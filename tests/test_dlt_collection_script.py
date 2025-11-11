"""
Test suite for the Enhanced DLT Collection Script.

This module provides comprehensive tests for the run_dlt_activity_collection.py script,
including Reddit client initialization, DLT pipeline creation, main collection function,
and command-line interface functionality.
"""

import sys
from unittest.mock import Mock, patch

import pytest

# Add project root to path for imports
sys.path.insert(0, '/home/carlos/projects/redditharbor')

from scripts.run_dlt_activity_collection import (
    apply_quality_filters,
    create_dlt_pipeline,
    get_reddit_client,
    get_target_subreddits,
    main,
    run_dlt_collection,
    show_pipeline_statistics,
)


class TestRedditClient:
    """Test cases for Reddit client initialization."""

    @patch('scripts.run_dlt_activity_collection.praw.Reddit')
    @patch('scripts.run_dlt_activity_collection.REDDIT_PUBLIC', 'test_public')
    @patch('scripts.run_dlt_activity_collection.REDDIT_SECRET', 'test_secret')
    @patch('scripts.run_dlt_activity_collection.REDDIT_USER_AGENT', 'test_agent')
    def test_get_reddit_client_success(self, mock_reddit_class):
        """Test successful Reddit client initialization."""
        # Mock Reddit instance
        mock_reddit = Mock()
        mock_reddit_class.return_value = mock_reddit

        # Mock test subreddit
        mock_subreddit = Mock()
        mock_subreddit.subscribers = 1000000
        mock_reddit.subreddit.return_value = mock_subreddit

        client = get_reddit_client()

        # Verify Reddit client was initialized with correct parameters
        mock_reddit_class.assert_called_once_with(
            client_id='test_public',
            client_secret='test_secret',
            user_agent='test_agent',
            read_only=True
        )

        # Verify test query was executed
        mock_reddit.subreddit.assert_called_once_with('python')

        assert client == mock_reddit

    @patch('scripts.run_dlt_activity_collection.praw.Reddit')
    def test_get_reddit_client_failure(self, mock_reddit_class):
        """Test Reddit client initialization failure."""
        mock_reddit_class.side_effect = Exception("Authentication failed")

        with pytest.raises(Exception, match="Authentication failed"):
            get_reddit_client()


class TestDLTPipeline:
    """Test cases for DLT pipeline creation."""

    @patch('scripts.run_dlt_activity_collection.dlt.pipeline')
    def test_create_dlt_pipeline_success(self, mock_dlt_pipeline):
        """Test successful DLT pipeline creation."""
        # Mock pipeline instance
        mock_pipeline = Mock()
        mock_dlt_pipeline.return_value = mock_pipeline

        pipeline = create_dlt_pipeline("test_pipeline", "test_dataset")

        # Verify pipeline was created with correct parameters (credentials not passed to pipeline creation)
        mock_dlt_pipeline.assert_called_once_with(
            pipeline_name="test_pipeline",
            destination="postgres",
            dataset_name="test_dataset"
        )

        assert pipeline == mock_pipeline

    @patch('scripts.run_dlt_activity_collection.dlt.pipeline')
    def test_create_dlt_pipeline_failure(self, mock_dlt_pipeline):
        """Test DLT pipeline creation failure."""
        mock_dlt_pipeline.side_effect = Exception("Pipeline creation failed")

        with pytest.raises(Exception, match="Pipeline creation failed"):
            create_dlt_pipeline()


class TestTargetSubreddits:
    """Test cases for target subreddit selection."""

    @patch('scripts.run_dlt_activity_collection.ALL_TARGET_SUBREDDITS', ['python', 'learnprogramming'])
    @patch('scripts.run_dlt_activity_collection.TARGET_SUBREDDITS', {
        'technology': ['python', 'programming'],
        'health': ['fitness', 'nutrition']
    })
    def test_get_target_subreddits_custom(self):
        """Test custom subreddit list."""
        subreddits = get_target_subreddits(custom_subreddits="python,technology,webdev")
        assert subreddits == ['python', 'technology', 'webdev']

    @patch('scripts.run_dlt_activity_collection.ALL_TARGET_SUBREDDITS', ['python', 'learnprogramming'])
    @patch('scripts.run_dlt_activity_collection.TARGET_SUBREDDITS', {
        'technology': ['python', 'programming'],
        'health': ['fitness', 'nutrition']
    })
    def test_get_target_subreddits_segment_all(self):
        """Test 'all' segment selection."""
        subreddits = get_target_subreddits(segment="all")
        assert subreddits == ['python', 'learnprogramming']

    @patch('scripts.run_dlt_activity_collection.ALL_TARGET_SUBREDDITS', ['python', 'learnprogramming'])
    @patch('scripts.run_dlt_activity_collection.TARGET_SUBREDDITS', {
        'technology': ['python', 'programming'],
        'health': ['fitness', 'nutrition']
    })
    def test_get_target_subreddits_segment_specific(self):
        """Test specific segment selection."""
        subreddits = get_target_subreddits(segment="technology")
        assert subreddits == ['python', 'programming']

    @patch('scripts.run_dlt_activity_collection.ALL_TARGET_SUBREDDITS', ['python', 'learnprogramming'])
    @patch('scripts.run_dlt_activity_collection.TARGET_SUBREDDITS', {
        'technology': ['python', 'programming'],
        'health': ['fitness', 'nutrition']
    })
    def test_get_target_subreddits_segment_invalid(self):
        """Test invalid segment selection."""
        with pytest.raises(ValueError, match="Unknown segment: invalid"):
            get_target_subreddits(segment="invalid")

    def test_get_target_subreddits_default(self):
        """Test default subreddit selection."""
        subreddits = get_target_subreddits()
        assert subreddits == ["python", "learnprogramming", "technology", "SaaS"]


class TestQualityFilters:
    """Test cases for quality filter application."""

    def test_apply_quality_filters(self):
        """Test quality filter application."""
        mock_source = Mock()

        filtered_source = apply_quality_filters(
            mock_source,
            min_activity_score=75.0,
            min_comment_length=20,
            min_score=5,
            comments_per_post=15
        )

        # Quality filters are applied at the resource level
        # This function mainly passes through the source with logging
        assert filtered_source == mock_source


class TestPipelineStatistics:
    """Test cases for pipeline statistics display."""

    def test_show_pipeline_statistics_success(self):
        """Test successful statistics display."""
        mock_pipeline = Mock()
        mock_trace = Mock()
        mock_resource = Mock()
        mock_resource.counts = {"items": 100, "rows": 95}
        mock_resource.duration = 1500.5
        mock_trace.resources = {"test_resource": mock_resource}
        mock_pipeline.last_trace = mock_trace

        # This function mainly logs statistics
        # We'll just verify it doesn't raise an exception
        show_pipeline_statistics(mock_pipeline, 100.0)

    def test_show_pipeline_statistics_no_trace(self):
        """Test statistics display with no trace available."""
        mock_pipeline = Mock()
        mock_pipeline.last_trace = None

        # Should not raise an exception even without trace
        show_pipeline_statistics(mock_pipeline, 100.0)

    def test_show_pipeline_statistics_trace_error(self):
        """Test statistics display with trace access error."""
        mock_pipeline = Mock()
        mock_pipeline.last_trace = Mock()

        # Simulate attribute access error
        mock_pipeline.last_trace.resources = Mock(side_effect=Exception("Access error"))

        # Should handle the error gracefully
        show_pipeline_statistics(mock_pipeline, 100.0)


class TestMainCollection:
    """Test cases for the main collection function."""

    @patch('scripts.run_dlt_activity_collection.show_pipeline_statistics')
    @patch('scripts.run_dlt_activity_collection.apply_quality_filters')
    @patch('scripts.run_dlt_activity_collection.reddit_activity_aware')
    @patch('scripts.run_dlt_activity_collection.create_dlt_pipeline')
    @patch('scripts.run_dlt_activity_collection.get_reddit_client')
    def test_run_dlt_collection_dry_run(self, mock_get_client, mock_create_pipeline,
                                       mock_source, mock_filters, mock_stats):
        """Test collection in dry run mode."""
        # Mock dependencies
        mock_reddit = Mock()
        mock_get_client.return_value = mock_reddit

        mock_pipeline = Mock()
        mock_create_pipeline.return_value = mock_pipeline

        mock_data = [Mock(), Mock()]
        mock_data[0].name = "resource1"
        mock_data[1].name = "resource2"
        mock_source.return_value = mock_data
        mock_filters.return_value = mock_data

        # Test dry run
        results = run_dlt_collection(
            subreddits=["python", "learnprogramming"],
            dry_run=True
        )

        # Verify results
        assert results["success"] is True
        assert results["dry_run"] is True
        assert results["subreddits_count"] == 2
        assert results["resources_count"] == 2

        # Verify dependencies were called
        mock_get_client.assert_called_once()
        mock_create_pipeline.assert_called_once()
        mock_source.assert_called_once()
        mock_filters.assert_called_once()

    @patch('scripts.run_dlt_activity_collection.get_reddit_client')
    @patch('scripts.run_dlt_activity_collection.create_dlt_pipeline')
    @patch('scripts.run_dlt_activity_collection.reddit_activity_aware')
    @patch('scripts.run_dlt_activity_collection.apply_quality_filters')
    @patch('scripts.run_dlt_activity_collection.show_pipeline_statistics')
    def test_run_dlt_collection_execution(self, mock_stats, mock_filters, mock_source,
                                         mock_create_pipeline, mock_get_client):
        """Test collection execution (not dry run)."""
        # Mock dependencies
        mock_reddit = Mock()
        mock_get_client.return_value = mock_reddit

        mock_pipeline = Mock()
        mock_create_pipeline.return_value = mock_pipeline

        mock_data = [Mock(), Mock()]
        mock_source.return_value = mock_data
        mock_filters.return_value = mock_data

        mock_load_info = Mock()
        mock_load_info.load_id = "test_load_123"
        mock_pipeline.run.return_value = mock_load_info

        # Mock DLT_SUPABASE_CONFIG
        with patch('scripts.run_dlt_activity_collection.DLT_SUPABASE_CONFIG', {'test': 'credentials'}):
            # Test execution
            results = run_dlt_collection(
                subreddits=["python", "learnprogramming"],
                dry_run=False,
                pipeline_name="test_pipeline"
            )

        # Verify results
        assert results["success"] is True
        assert results["dry_run"] is False
        assert results["pipeline_name"] == "test_pipeline"
        assert results["load_id"] == "test_load_123"
        assert results["subreddits_count"] == 2

        # Verify pipeline was run with credentials
        mock_pipeline.run.assert_called_once_with(mock_data, credentials={'test': 'credentials'})

    @patch('scripts.run_dlt_activity_collection.get_reddit_client')
    def test_run_dlt_collection_failure(self, mock_get_client):
        """Test collection failure handling."""
        mock_get_client.side_effect = Exception("Reddit client failed")

        results = run_dlt_collection(
            subreddits=["python"],
            dry_run=False
        )

        # Verify failure handling
        assert results["success"] is False
        assert "Reddit client failed" in results["error"]


class TestCommandLineInterface:
    """Test cases for command-line interface."""

    @patch('scripts.run_dlt_activity_collection.run_dlt_collection')
    @patch('scripts.run_dlt_activity_collection.get_target_subreddits')
    @patch('scripts.run_dlt_activity_collection.sys.exit')
    def test_main_dry_run_success(self, mock_exit, mock_get_subreddits, mock_run_collection):
        """Test successful dry run via CLI."""
        # Mock dependencies
        mock_get_subreddits.return_value = ["python", "learnprogramming"]
        mock_run_collection.return_value = {
            "success": True,
            "dry_run": True,
            "subreddits_count": 2,
            "resources_count": 3,
            "duration": 1.5
        }

        # Mock command line arguments
        test_args = [
            "script_name",
            "--subreddits", "python,learnprogramming",
            "--dry-run"
        ]

        with patch('sys.argv', test_args):
            main()

        # Verify success path
        mock_run_collection.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch('scripts.run_dlt_activity_collection.run_dlt_collection')
    @patch('scripts.run_dlt_activity_collection.get_target_subreddits')
    @patch('scripts.run_dlt_activity_collection.sys.exit')
    def test_main_execution_success(self, mock_exit, mock_get_subreddits, mock_run_collection):
        """Test successful execution via CLI."""
        # Mock dependencies
        mock_get_subreddits.return_value = ["python", "learnprogramming"]
        mock_run_collection.return_value = {
            "success": True,
            "dry_run": False,
            "pipeline_name": "test_pipeline",
            "load_id": "test_load_123",
            "subreddits_count": 2,
            "duration": 10.5
        }

        # Mock command line arguments
        test_args = [
            "script_name",
            "--subreddits", "python,learnprogramming",
            "--time-filter", "week",
            "--min-activity", "75"
        ]

        with patch('sys.argv', test_args):
            main()

        # Verify success path
        mock_run_collection.assert_called_once_with(
            subreddits=["python", "learnprogramming"],
            time_filter="week",
            min_activity_score=75.0,
            dry_run=False,
            pipeline_name="reddit_harbor_activity_collection"
        )
        mock_exit.assert_called_once_with(0)

    @patch('scripts.run_dlt_activity_collection.run_dlt_collection')
    @patch('scripts.run_dlt_activity_collection.get_target_subreddits')
    @patch('scripts.run_dlt_activity_collection.sys.exit')
    def test_main_collection_failure(self, mock_exit, mock_get_subreddits, mock_run_collection):
        """Test collection failure via CLI."""
        # Mock dependencies
        mock_get_subreddits.return_value = ["python"]
        mock_run_collection.return_value = {
            "success": False,
            "error": "Reddit API error"
        }

        # Mock command line arguments
        test_args = ["script_name", "--subreddits", "python"]

        with patch('sys.argv', test_args):
            main()

        # Verify failure handling
        mock_exit.assert_called_once_with(1)

    @patch('scripts.run_dlt_activity_collection.sys.exit')
    def test_main_keyboard_interrupt(self, mock_exit):
        """Test keyboard interrupt handling."""
        # Mock command line arguments
        test_args = ["script_name", "--subreddits", "python"]

        with patch('sys.argv', test_args), \
             patch('scripts.run_dlt_activity_collection.get_target_subreddits', side_effect=KeyboardInterrupt()):
            main()

        # Verify interrupt handling
        mock_exit.assert_called_once_with(130)

    @patch('scripts.run_dlt_activity_collection.sys.exit')
    def test_main_unexpected_error(self, mock_exit):
        """Test unexpected error handling."""
        # Mock command line arguments
        test_args = ["script_name", "--subreddits", "python"]

        with patch('sys.argv', test_args), \
             patch('scripts.run_dlt_activity_collection.get_target_subreddits', side_effect=Exception("Unexpected error")):
            main()

        # Verify error handling
        mock_exit.assert_called_once_with(1)


class TestIntegrationScenarios:
    """Integration test scenarios for the script."""

    @patch('scripts.run_dlt_activity_collection.run_dlt_collection')
    @patch('scripts.run_dlt_activity_collection.get_target_subreddits')
    def test_segment_all_scenario(self, mock_get_subreddits, mock_run_collection):
        """Test --all flag scenario."""
        mock_get_subreddits.return_value = ["python", "learnprogramming", "tech"]
        mock_run_collection.return_value = {"success": True, "dry_run": True}

        test_args = [
            "script_name",
            "--all",
            "--time-filter", "week",
            "--dry-run"
        ]

        with patch('sys.argv', test_args), \
             patch('scripts.run_dlt_activity_collection.sys.exit') as mock_exit:
            main()

        # Verify correct parameters were passed
        mock_get_subreddits.assert_called_once_with(segment="all")
        mock_run_collection.assert_called_once_with(
            subreddits=["python", "learnprogramming", "tech"],
            time_filter="week",
            min_activity_score=50.0,
            dry_run=True,
            pipeline_name="reddit_harbor_activity_collection"
        )

    @patch('scripts.run_dlt_activity_collection.run_dlt_collection')
    @patch('scripts.run_dlt_activity_collection.get_target_subreddits')
    def test_custom_pipeline_scenario(self, mock_get_subreddits, mock_run_collection):
        """Test custom pipeline name scenario."""
        mock_get_subreddits.return_value = ["python"]
        mock_run_collection.return_value = {"success": True, "dry_run": False}

        test_args = [
            "script_name",
            "--segment", "technology_saas",  # Fixed segment name
            "--pipeline", "custom_pipeline_2025",
            "--min-activity", "80"
        ]

        with patch('sys.argv', test_args), \
             patch('scripts.run_dlt_activity_collection.sys.exit') as mock_exit:
            main()

        # Verify custom pipeline name was used
        mock_run_collection.assert_called_once_with(
            subreddits=["python"],
            time_filter="day",
            min_activity_score=80.0,
            dry_run=False,
            pipeline_name="custom_pipeline_2025"
        )


# Pytest configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
