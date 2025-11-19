"""
Test suite for migrate_existing_opportunities.py script.

This test suite follows TDD approach by testing the migration script functionality
before implementation. Tests cover:
- Script initialization and configuration
- Processing opportunities without business_concept_id
- Progress tracking and statistics
- Error handling and logging
- Result saving to JSON file
"""

import json
import os
import tempfile
import unittest.mock as mock
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the script we're testing
import sys
sys.path.append(str(Path(__file__).parent.parent))
from scripts.deduplication.migrate_existing_opportunities import (
    MigrationScript,
    main,
    parse_arguments
)


class TestMigrationScript:
    """Test the MigrationScript class functionality."""

    def test_init_with_valid_config(self):
        """Test script initialization with valid configuration."""
        with patch('scripts.deduplication.migrate_existing_opportunities.SimpleDeduplicator') as mock_dedup:
            with patch('scripts.deduplication.migrate_existing_opportunities.create_client') as mock_client:
                # Setup mock client
                mock_supabase = MagicMock()
                mock_client.return_value = mock_supabase

                # Initialize script
                script = MigrationScript(
                    supabase_url="http://test-url",
                    supabase_key="test-key"
                )

                # Verify initialization
                assert script.supabase_url == "http://test-url"
                assert script.supabase_key == "test-key"
                assert script.deduplicator is not None
                assert script.statistics == {
                    'total_processed': 0,
                    'unique_concepts': 0,
                    'duplicates_found': 0,
                    'errors': 0
                }

    def test_init_with_missing_deduplicator(self):
        """Test script initialization when SimpleDeduplicator is not available."""
        with patch('scripts.deduplication.migrate_existing_opportunities.SimpleDeduplicator', side_effect=ImportError("No module named 'supabase'")):
            with pytest.raises(ImportError, match="supabase package is required"):
                MigrationScript(
                    supabase_url="http://test-url",
                    supabase_key="test-key"
                )

    def test_fetch_opportunities_without_concept_id(self):
        """Test fetching opportunities without business_concept_id."""
        with patch('scripts.deduplication.migrate_existing_opportunities.SimpleDeduplicator') as mock_dedup:
            with patch('scripts.deduplication.migrate_existing_opportunities.create_client') as mock_client:
                # Setup mock client and response
                mock_supabase = MagicMock()
                mock_client.return_value = mock_supabase

                # Mock opportunities data
                mock_opportunities = [
                    {
                        'id': 'opp1',
                        'app_concept': 'app idea: social media for pets',
                        'title': 'Pet Social Network',
                        'subreddit': 'pets'
                    },
                    {
                        'id': 'opp2',
                        'app_concept': 'mobile app: find local dog walkers',
                        'title': 'Dog Walker Finder',
                        'subreddit': 'dogs'
                    }
                ]

                mock_supabase.table.return_value.select.return_value.is_.return_value.execute.return_value.data = mock_opportunities

                # Initialize script and fetch opportunities
                script = MigrationScript(
                    supabase_url="http://test-url",
                    supabase_key="test-key"
                )

                opportunities = script.fetch_opportunities_without_concept_id()

                # Verify results
                assert len(opportunities) == 2
                assert opportunities[0]['id'] == 'opp1'
                assert opportunities[1]['app_concept'] == 'mobile app: find local dog walkers'

                # Verify Supabase was called correctly
                mock_supabase.table.assert_called_once_with('opportunities_unified')
                mock_supabase.table.return_value.select.assert_called_once_with('id, app_concept, title')
                mock_supabase.table.return_value.select.return_value.is_.assert_called_once_with('business_concept_id', 'null')

    def test_fetch_opportunities_with_api_error(self):
        """Test handling API errors when fetching opportunities."""
        with patch('scripts.deduplication.migrate_existing_opportunities.SimpleDeduplicator') as mock_dedup:
            with patch('scripts.deduplication.migrate_existing_opportunities.create_client') as mock_client:
                # Setup mock client with error
                mock_supabase = MagicMock()
                mock_client.return_value = mock_supabase
                mock_supabase.table.return_value.select.return_value.is_.return_value.execute.side_effect = Exception("Database connection failed")

                script = MigrationScript(
                    supabase_url="http://test-url",
                    supabase_key="test-key"
                )

                opportunities = script.fetch_opportunities_without_concept_id()

                # Should return empty list on error
                assert opportunities == []

    def test_process_opportunities_success(self):
        """Test successful processing of opportunities."""
        with patch('scripts.deduplication.migrate_existing_opportunities.SimpleDeduplicator') as mock_dedup:
            with patch('scripts.deduplication.migrate_existing_opportunities.create_client') as mock_client:
                # Setup mock client
                mock_supabase = MagicMock()
                mock_client.return_value = mock_supabase

                # Setup mock deduplicator
                mock_dedup_instance = MagicMock()
                mock_dedup.return_value = mock_dedup_instance

                # Mock deduplication results
                mock_dedup_instance.process_opportunity.side_effect = [
                    {
                        'success': True,
                        'is_duplicate': False,
                        'concept_id': 1,
                        'opportunity_id': 'opp1',
                        'fingerprint': 'abc123',
                        'normalized_concept': 'social media for pets',
                        'message': 'Processed unique opportunity successfully',
                        'processing_time': 0.05
                    },
                    {
                        'success': True,
                        'is_duplicate': True,
                        'concept_id': 1,
                        'opportunity_id': 'opp2',
                        'fingerprint': 'abc123',
                        'normalized_concept': 'social media for pets',
                        'message': 'Processed duplicate opportunity successfully',
                        'processing_time': 0.03
                    }
                ]

                # Mock opportunities
                opportunities = [
                    {'id': 'opp1', 'app_concept': 'app idea: social media for pets'},
                    {'id': 'opp2', 'app_concept': 'app for pets social media'}
                ]

                script = MigrationScript(
                    supabase_url="http://test-url",
                    supabase_key="test-key"
                )

                # Process opportunities
                with patch('builtins.print') as mock_print:  # Capture progress prints
                    results = script.process_opportunities(opportunities)

                # Verify results
                assert len(results) == 2
                assert results[0]['success'] is True
                assert results[0]['is_duplicate'] is False
                assert results[1]['success'] is True
                assert results[1]['is_duplicate'] is True

                # Verify statistics
                assert script.statistics['total_processed'] == 2
                assert script.statistics['unique_concepts'] == 1
                assert script.statistics['duplicates_found'] == 1
                assert script.statistics['errors'] == 0

                # Verify progress was printed
                assert mock_print.call_count >= 2  # Should print progress for each opportunity

    def test_process_opportunities_with_errors(self):
        """Test processing opportunities with some errors."""
        with patch('scripts.deduplication.migrate_existing_opportunities.SimpleDeduplicator') as mock_dedup:
            with patch('scripts.deduplication.migrate_existing_opportunities.create_client') as mock_client:
                # Setup mock client
                mock_supabase = MagicMock()
                mock_client.return_value = mock_supabase

                # Setup mock deduplicator with mixed results
                mock_dedup_instance = MagicMock()
                mock_dedup.return_value = mock_dedup_instance

                mock_dedup_instance.process_opportunity.side_effect = [
                    {
                        'success': True,
                        'is_duplicate': False,
                        'concept_id': 1,
                        'opportunity_id': 'opp1',
                        'message': 'Success'
                    },
                    {
                        'success': False,
                        'error': 'Missing app_concept field',
                        'opportunity_id': 'opp2',
                        'message': 'Processing failed: missing app concept'
                    },
                    Exception("Unexpected error")
                ]

                opportunities = [
                    {'id': 'opp1', 'app_concept': 'good idea'},
                    {'id': 'opp2'},  # Missing app_concept
                    {'id': 'opp3', 'app_concept': 'bad luck'}
                ]

                script = MigrationScript(
                    supabase_url="http://test-url",
                    supabase_key="test-key"
                )

                # Process opportunities
                with patch('builtins.print'):
                    results = script.process_opportunities(opportunities)

                # Verify results
                assert len(results) == 3
                assert results[0]['success'] is True
                assert results[1]['success'] is False
                assert results[2]['success'] is False

                # Verify statistics
                assert script.statistics['total_processed'] == 3
                assert script.statistics['unique_concepts'] == 1
                assert script.statistics['duplicates_found'] == 0
                assert script.statistics['errors'] == 2

    def test_save_results_to_json(self):
        """Test saving results to JSON file."""
        with patch('scripts.deduplication.migrate_existing_opportunities.SimpleDeduplicator') as mock_dedup:
            with patch('scripts.deduplication.migrate_existing_opportunities.create_client') as mock_client:
                # Setup mock client
                mock_supabase = MagicMock()
                mock_client.return_value = mock_supabase

                script = MigrationScript(
                    supabase_url="http://test-url",
                    supabase_key="test-key"
                )

                # Mock results
                results = [
                    {
                        'success': True,
                        'opportunity_id': 'opp1',
                        'concept_id': 1,
                        'is_duplicate': False
                    },
                    {
                        'success': False,
                        'opportunity_id': 'opp2',
                        'error': 'Processing failed'
                    }
                ]

                script.statistics = {
                    'total_processed': 2,
                    'unique_concepts': 1,
                    'duplicates_found': 0,
                    'errors': 1
                }

                # Save to temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                    temp_path = temp_file.name

                try:
                    script.save_results_to_json(results, temp_path)

                    # Verify file was created and contains correct data
                    assert os.path.exists(temp_path)

                    with open(temp_path, 'r') as f:
                        saved_data = json.load(f)

                    assert saved_data['statistics'] == script.statistics
                    assert len(saved_data['results']) == 2
                    assert saved_data['results'][0]['success'] is True
                    assert saved_data['results'][1]['success'] is False
                    assert 'timestamp' in saved_data

                finally:
                    # Clean up
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)

    def test_save_results_with_file_error(self):
        """Test handling file save errors."""
        with patch('scripts.deduplication.migrate_existing_opportunities.SimpleDeduplicator') as mock_dedup:
            with patch('scripts.deduplication.migrate_existing_opportunities.create_client') as mock_client:
                # Setup mock client
                mock_supabase = MagicMock()
                mock_client.return_value = mock_supabase

                script = MigrationScript(
                    supabase_url="http://test-url",
                    supabase_key="test-key"
                )

                # Mock json.dump to raise an exception
                with patch('json.dump', side_effect=IOError("Permission denied")):
                    with patch('builtins.print') as mock_print:
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                            temp_path = temp_file.name

                        try:
                            script.save_results_to_json([], temp_path)
                        finally:
                            # Clean up
                            if os.path.exists(temp_path):
                                os.unlink(temp_path)

                    # Should print error message but not raise exception
                    print_calls = [str(call) for call in mock_print.call_args_list]
                    assert any("Error saving results to JSON file" in call for call in print_calls)

    def test_progress_updates(self):
        """Test that progress updates are printed every 100 records."""
        with patch('scripts.deduplication.migrate_existing_opportunities.SimpleDeduplicator') as mock_dedup:
            with patch('scripts.deduplication.migrate_existing_opportunities.create_client') as mock_client:
                # Setup mock client
                mock_supabase = MagicMock()
                mock_client.return_value = mock_supabase

                # Setup mock deduplicator
                mock_dedup_instance = MagicMock()
                mock_dedup.return_value = mock_dedup_instance

                # Mock successful processing
                mock_dedup_instance.process_opportunity.return_value = {
                    'success': True,
                    'is_duplicate': False,
                    'concept_id': 1,
                    'opportunity_id': 'opp1',
                    'message': 'Success'
                }

                # Create 205 opportunities
                opportunities = [
                    {'id': f'opp{i}', 'app_concept': f'idea {i}'}
                    for i in range(205)
                ]

                script = MigrationScript(
                    supabase_url="http://test-url",
                    supabase_key="test-key"
                )

                with patch('builtins.print') as mock_print:
                    script.process_opportunities(opportunities, batch_size=100)

                # Should print progress at 100, 200 records
                progress_calls = [
                    call for call in mock_print.call_args_list
                    if 'Progress:' in str(call) and '/' in str(call)
                ]

                # Should have progress updates at 100 and 200
                assert len(progress_calls) >= 2
                # Check that progress calls contain the expected numbers
                progress_text = ' '.join(str(call) for call in progress_calls)
                assert '100/205' in progress_text
                assert '200/205' in progress_text


class TestArgumentParsing:
    """Test command line argument parsing."""

    def test_parse_arguments_default_values(self):
        """Test parsing arguments with default values."""
        with patch('sys.argv', ['migrate_existing_opportunities.py']):
            args = parse_arguments()

            assert args.output_file == 'migration_results.json'
            assert args.batch_size == 100
            assert args.dry_run is False
            assert args.verbose is False

    def test_parse_arguments_custom_values(self):
        """Test parsing arguments with custom values."""
        with patch('sys.argv', [
            'migrate_existing_opportunities.py',
            '--output-file', 'custom_results.json',
            '--batch-size', '50',
            '--dry-run',
            '--verbose'
        ]):
            args = parse_arguments()

            assert args.output_file == 'custom_results.json'
            assert args.batch_size == 50
            assert args.dry_run is True
            assert args.verbose is True


class TestMainFunction:
    """Test the main function integration."""

    def test_main_successful_execution(self):
        """Test main function with successful execution."""
        with patch('scripts.deduplication.migrate_existing_opportunities.MigrationScript') as mock_script_class:
            with patch('scripts.deduplication.migrate_existing_opportunities.parse_arguments') as mock_parse:
                with patch('scripts.deduplication.migrate_existing_opportunities.SUPABASE_URL', 'http://test-url'):
                    with patch('scripts.deduplication.migrate_existing_opportunities.SUPABASE_KEY', 'test-key'):
                        # Setup mocks
                        mock_args = MagicMock()
                        mock_args.output_file = 'test_results.json'
                        mock_args.batch_size = 100
                        mock_args.verbose = False
                        mock_parse.return_value = mock_args

                    # Setup mock script instance
                    mock_script = MagicMock()
                    mock_script_class.return_value = mock_script
                    mock_script.fetch_opportunities_without_concept_id.return_value = [
                        {'id': 'opp1', 'app_concept': 'test idea'}
                    ]
                    mock_script.process_opportunities.return_value = [{'success': True}]

                    # Run main
                    with patch('builtins.print'):
                        main()

                    # Verify script was called correctly
                    mock_script_class.assert_called_once_with(
                        supabase_url='http://test-url',
                        supabase_key='test-key'
                    )
                    mock_script.fetch_opportunities_without_concept_id.assert_called_once()
                    mock_script.process_opportunities.assert_called_once()
                    mock_script.save_results_to_json.assert_called_once()

    def test_main_missing_config(self):
        """Test main function with missing configuration."""
        with patch('scripts.deduplication.migrate_existing_opportunities.SUPABASE_URL', None):
            with patch('sys.argv', ['migrate_existing_opportunities.py']):
                with patch('builtins.print') as mock_print:
                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    assert exc_info.value.code == 1
                    mock_print.assert_any_call("Error: SUPABASE_URL not found in environment variables")

    def test_main_no_opportunities(self):
        """Test main function when no opportunities need migration."""
        with patch('scripts.deduplication.migrate_existing_opportunities.MigrationScript') as mock_script_class:
            with patch('scripts.deduplication.migrate_existing_opportunities.parse_arguments') as mock_parse:
                with patch('scripts.deduplication.migrate_existing_opportunities.SUPABASE_URL', 'http://test-url'):
                    with patch('scripts.deduplication.migrate_existing_opportunities.SUPABASE_KEY', 'test-key'):
                        # Setup mocks
                        mock_args = MagicMock()
                        mock_args.verbose = False
                        mock_parse.return_value = mock_args

                        # Setup mock script with no opportunities
                        mock_script = MagicMock()
                        mock_script_class.return_value = mock_script
                        mock_script.fetch_opportunities_without_concept_id.return_value = []

                        with patch('builtins.print') as mock_print:
                            main()

                        # Should print message about no opportunities
                        mock_print.assert_any_call("No opportunities found without business_concept_id")

                        # Should not call process_opportunities or save_results
                        mock_script.process_opportunities.assert_not_called()
                        mock_script.save_results_to_json.assert_not_called()