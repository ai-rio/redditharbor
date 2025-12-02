"""
Test suite for UUID format fixes and deduplication schema migration.

This test suite validates the UUID format fixes and ensures the deduplication
schema integration works correctly after migration deployment.
"""

import pytest
import asyncio
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

# Add project root to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from scripts.testing.validate_uuid_migration import UUIDMigrationValidator
from config.settings import get_database_config


class TestUUIDMigrationValidator:
    """Test cases for UUID Migration Validator."""

    @pytest.fixture
    def validator(self):
        """Create validator instance for testing."""
        return UUIDMigrationValidator(fix_issues=False, dry_run=True)

    @pytest.fixture
    def mock_connection(self):
        """Create mock database connection."""
        conn = AsyncMock()
        return conn

    @pytest.mark.asyncio
    async def test_check_uuid_foreign_key_consistency(self, validator, mock_connection):
        """Test UUID foreign key consistency checking."""
        # Mock database responses
        mock_connection.fetchrow.side_effect = [
            # app_opportunities result
            MagicMock(total_records=100, missing_uuid=5, has_uuid=95, orphaned_uuid=2),
            # llm_monetization_analysis result
            MagicMock(total_records=50, missing_uuid=3, has_uuid=47, orphaned_uuid=1),
            # workflow_results result
            MagicMock(total_records=25, missing_uuid=1, has_uuid=24, orphaned_uuid=0)
        ]

        result = await validator.check_uuid_foreign_key_consistency(mock_connection)

        # Verify results
        assert 'app_opportunities' in result
        assert 'llm_monetization_analysis' in result
        assert 'workflow_results' in result

        assert result['app_opportunities']['total_records'] == 100
        assert result['app_opportunities']['missing_uuid'] == 5
        assert result['app_opportunities']['has_uuid'] == 95
        assert result['app_opportunities']['orphaned_uuid'] == 2

        # Verify proper queries were called
        assert mock_connection.fetchrow.call_count == 3

    @pytest.mark.asyncio
    async def test_check_deduplication_schema_integration(self, validator, mock_connection):
        """Test deduplication schema integration checking."""
        # Mock database responses
        mock_connection.fetchrow.side_effect = [
            # opportunities_unified_structure result
            MagicMock(total_records=200, has_submission_link=150, has_business_concept=180,
                     has_fingerprint=120, copied_records=25),
            # foreign_key_relationships result
            MagicMock(total_opportunities=200, orphaned_opportunities=10, orphaned_business_concepts=5),
            # semantic_fingerprints result
            MagicMock(total_with_fingerprints=120, avg_fingerprint_length=45.5, unique_fingerprints=115)
        ]

        result = await validator.check_deduplication_schema_integration(mock_connection)

        # Verify results
        assert 'opportunities_unified_structure' in result
        assert 'foreign_key_relationships' in result
        assert 'semantic_fingerprints' in result

        assert result['opportunities_unified_structure']['total_records'] == 200
        assert result['foreign_key_relationships']['orphaned_opportunities'] == 10
        assert result['semantic_fingerprints']['unique_fingerprints'] == 115

        assert mock_connection.fetchrow.call_count == 3

    @pytest.mark.asyncio
    async def test_check_constraint_validation(self, validator, mock_connection):
        """Test constraint validation checking."""
        # Mock database responses
        mock_connection.fetch.side_effect = [
            # Foreign key violations
            [
                MagicMock(constraint_name='app_opportunities_submission_uuid', violations=0),
                MagicMock(constraint_name='llm_analysis_submission_uuid', violations=1),
                MagicMock(constraint_name='workflow_results_opportunity_id', violations=0)
            ],
            # Data quality violations
            [
                MagicMock(check_name='opportunities_unified_trust_score', violations=2),
                MagicMock(check_name='opportunities_unified_confidence', violations=0)
            ]
        ]

        result = await validator.check_constraint_validation(mock_connection)

        # Verify results
        assert 'foreign_key_violations' in result
        assert 'data_quality_violations' in result

        assert len(result['foreign_key_violations']) == 3
        assert len(result['data_quality_violations']) == 2

        # Check specific violation counts
        fk_violations = {v['constraint_name']: v['violations'] for v in result['foreign_key_violations']}
        assert fk_violations['llm_analysis_submission_uuid'] == 1
        assert fk_violations['app_opportunities_submission_uuid'] == 0

        assert mock_connection.fetch.call_count == 2

    @pytest.mark.asyncio
    async def test_fix_missing_uuids_dry_run(self, validator, mock_connection):
        """Test fixing missing UUIDs in dry run mode."""
        validator.fix_issues = True  # Enable fixing but keep dry_run=True

        result = await validator.fix_missing_uuids(mock_connection)

        # Should return 0 for dry run
        assert result == 0

        # Should not have executed any UPDATE queries
        assert mock_connection.execute.call_count == 0

    @pytest.mark.asyncio
    async def test_fix_missing_uuids_with_fixes(self, validator, mock_connection):
        """Test fixing missing UUIDs with actual fixes."""
        validator.fix_issues = True
        validator.dry_run = False  # Enable actual fixes

        # Mock UPDATE execution results
        mock_connection.execute.side_effect = [
            "UPDATE 5",  # app_opportunities fixed
            "UPDATE 3"   # llm_monetization_analysis fixed
        ]

        result = await validator.fix_missing_uuids(mock_connection)

        # Should return total fixed count
        assert result == 8

        # Should have executed UPDATE queries
        assert mock_connection.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_check_performance_impact(self, validator, mock_connection):
        """Test performance impact checking."""
        # Mock performance query results
        mock_connection.fetchrow.side_effect = [
            # opportunities_by_business_concept result
            {
                'QUERY PLAN': [{
                    'Execution Time': 150.5
                }]
            },
            # app_opportunities_by_submission_uuid (needs UUID parameter)
            None,  # First call to get sample UUID
            # Second call for actual performance test
            {
                'QUERY PLAN': [{
                    'Execution Time': 25.3
                }]
            }
        ]

        # Mock the UUID parameter fetch
        mock_connection.fetchval.return_value = '550e8400-e29b-41d4-a716-446655440000'

        result = await validator.check_performance_impact(mock_connection)

        # Verify results
        assert 'opportunities_by_business_concept' in result
        assert 'app_opportunities_by_submission_uuid' in result

        assert result['opportunities_by_business_concept']['execution_time_ms'] == 150.5
        assert result['opportunities_by_business_concept']['status'] == 'good'
        assert result['app_opportunities_by_submission_uuid']['execution_time_ms'] == 25.3
        assert result['app_opportunities_by_submission_uuid']['status'] == 'good'

    def test_generate_recommendations_no_issues(self, validator):
        """Test recommendation generation with no issues."""
        validator.validation_results = {
            'checks': {
                'uuid_consistency': {
                    'app_opportunities': {'missing_uuid': 0, 'orphaned_uuid': 0},
                    'llm_monetization_analysis': {'missing_uuid': 0, 'orphaned_uuid': 0}
                },
                'deduplication_schema': {
                    'foreign_key_relationships': {'orphaned_opportunities': 0}
                },
                'constraint_validation': {
                    'foreign_key_violations': [],
                    'data_quality_violations': []
                },
                'performance_impact': {
                    'test_query': {'status': 'good'}
                }
            }
        }

        recommendations = validator._generate_recommendations()

        assert len(recommendations) == 1
        assert "No issues detected" in recommendations[0]

    def test_generate_recommendations_with_issues(self, validator):
        """Test recommendation generation with various issues."""
        validator.validation_results = {
            'checks': {
                'uuid_consistency': {
                    'app_opportunities': {'missing_uuid': 5, 'orphaned_uuid': 2}
                },
                'deduplication_schema': {
                    'foreign_key_relationships': {'orphaned_opportunities': 3}
                },
                'constraint_validation': {
                    'foreign_key_violations': [
                        {'constraint_name': 'test_constraint', 'violations': 1}
                    ]
                },
                'performance_impact': {
                    'slow_query': {'status': 'needs_review', 'execution_time_ms': 1500}
                }
            }
        }

        recommendations = validator._generate_recommendations()

        # Should have multiple recommendations
        assert len(recommendations) >= 4

        # Check for specific recommendation types
        rec_text = ' '.join(recommendations)
        assert 'missing UUID columns' in rec_text
        assert 'orphaned UUID references' in rec_text
        assert 'missing submission links' in rec_text
        assert 'slow performance' in rec_text
        assert 'Foreign key constraint' in rec_text

    @pytest.mark.asyncio
    async def test_run_validation_complete(self, validator, mock_connection):
        """Test complete validation run."""
        # Mock all the check methods
        validator.check_uuid_foreign_key_consistency = AsyncMock(return_value={'test': 'data'})
        validator.check_deduplication_schema_integration = AsyncMock(return_value={'test': 'data'})
        validator.check_constraint_validation = AsyncMock(return_value={'test': 'data'})
        validator.check_performance_impact = AsyncMock(return_value={'test': 'data'})
        validator.fix_missing_uuids = AsyncMock(return_value=0)

        # Mock the connection
        with patch.object(validator, 'get_async_connection', return_value=mock_connection):
            result = await validator.run_validation()

        # Verify structure
        assert 'timestamp' in result
        assert 'checks' in result
        assert 'summary' in result
        assert 'recommendations' in result

        # Verify methods were called
        validator.check_uuid_foreign_key_consistency.assert_called_once_with(mock_connection)
        validator.check_deduplication_schema_integration.assert_called_once_with(mock_connection)
        validator.check_constraint_validation.assert_called_once_with(mock_connection)
        validator.check_performance_impact.assert_called_once_with(mock_connection)
        validator.fix_missing_uuids.assert_called_once_with(mock_connection)

    def test_save_results(self, validator):
        """Test saving validation results to file."""
        validator.validation_results = {
            'timestamp': '2025-11-20T10:00:00',
            'checks': {},
            'summary': {'total_issues': 0, 'validation_success': True},
            'recommendations': ['Test recommendation']
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('pathlib.Path.mkdir'):
                with patch('builtins.open', create=True) as mock_open:
                    mock_file = MagicMock()
                    mock_open.return_value.__enter__.return_value = mock_file

                    filename = validator.save_results()

                    # Verify file was opened for writing
                    mock_open.assert_called_once()
                    mock_file.write.assert_called_once()

                    # Verify filename format
                    assert filename.startswith('logs/uuid_migration_validation_')
                    assert filename.endswith('.json')


class TestUUIDMigrationIntegration:
    """Integration tests for UUID migration."""

    @pytest.mark.asyncio
    async def test_database_connection(self):
        """Test database connection works with current configuration."""
        # This test requires actual database connection, so we'll mock it
        with patch('scripts.testing.validate_uuid_migration.asyncpg.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn

            validator = UUIDMigrationValidator()
            conn = await validator.get_async_connection()

            assert conn == mock_conn
            mock_connect.assert_called_once()

    def test_validator_initialization(self):
        """Test validator initialization with different parameters."""
        # Test default initialization
        validator1 = UUIDMigrationValidator()
        assert validator1.fix_issues is False
        assert validator1.dry_run is False

        # Test with fix issues enabled
        validator2 = UUIDMigrationValidator(fix_issues=True)
        assert validator2.fix_issues is True
        assert validator2.dry_run is False

        # Test with dry run enabled
        validator3 = UUIDMigrationValidator(dry_run=True)
        assert validator3.fix_issues is False
        assert validator3.dry_run is True

        # Test with both enabled
        validator4 = UUIDMigrationValidator(fix_issues=True, dry_run=True)
        assert validator4.fix_issues is True
        assert validator4.dry_run is True

    @pytest.mark.asyncio
    async def test_validation_with_no_data(self):
        """Test validation behavior with empty database."""
        validator = UUIDMigrationValidator(dry_run=True)
        mock_conn = AsyncMock()

        # Mock empty results
        mock_conn.fetchrow.return_value = MagicMock(total_records=0, missing_uuid=0, has_uuid=0, orphaned_uuid=0)
        mock_conn.fetch.return_value = []

        with patch.object(validator, 'get_async_connection', return_value=mock_conn):
            result = await validator.run_validation()

        assert result['summary']['validation_success'] is True
        assert result['summary']['total_issues'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])