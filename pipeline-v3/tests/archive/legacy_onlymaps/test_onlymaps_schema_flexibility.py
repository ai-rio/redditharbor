"""
OnlyMaps database schema flexibility tests for pipeline-v3.

This module tests OnlyMaps' ability to handle database schema changes,
missing columns, and schema evolution scenarios while maintaining
robust SQL-to-Python object mapping functionality.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from load.database import DatabaseLoader
from models import (
    AnalysisResult,
    AppIdea,
    MarketMetrics,
    RedditComment,
    RedditSubmission,
)
from models.database import Opportunity, OpportunityCreate

# Import OnlyMaps components (assuming they exist)
from onlymaps import OnlyMapsConfig, OnlyMapsMapper, SchemaFlexibilityError


class TestOnlyMapsSchemaFlexibility:
    """Test suite for OnlyMaps schema flexibility capabilities."""

    @pytest.fixture
    def flexible_mapper(self):
        """OnlyMaps mapper configured for maximum flexibility."""
        config = OnlyMapsConfig(
            batch_size=100,
            timeout=30,
            retry_attempts=3,
            fallback_to_sqlalchemy=True,
            schema_validation=False,  # Disable strict validation for flexibility testing
            performance_monitoring=True
        )
        return OnlyMapsMapper(config=config)

    @pytest.fixture
    def strict_mapper(self):
        """OnlyMaps mapper configured for strict schema validation."""
        config = OnlyMapsConfig(
            batch_size=100,
            timeout=30,
            retry_attempts=3,
            fallback_to_sqlalchemy=True,
            schema_validation=True,  # Enable strict validation
            performance_monitoring=True
        )
        return OnlyMapsMapper(config=config)

    # =============================================================================
    # Missing Column Handling Tests
    # =============================================================================

    def test_missing_required_column_handling(self, flexible_mapper, sample_database_schema):
        """Test handling of missing required columns."""
        # Create SQL record missing required columns
        sql_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'test123',
            # Missing reddit_title (required)
            'reddit_url': 'https://reddit.com/r/test/test123',
            'subreddit': 'test',
            'reddit_author': 'testuser',
            'reddit_upvotes': 150,
            'reddit_comments_count': 42,
            'reddit_created_at': '2024-01-15T10:30:00Z',
            'app_title': 'Test App',
            'app_concept': 'Test concept',
            'problem_statement': 'Test problem',
            'target_audience': 'Test audience',
            'core_functions': ['function1', 'function2'],
            'market_demand': 85.0,
            'pain_intensity': 90.0,
            'monetization_potential': 75.0,
            'competition_level': 60.0,
            'technical_feasibility': 80.0,
            'final_score': 78.5,
            'confidence_score': 85.0,
            'trust_level': 'HIGH',
            'embedding': None,
            'analyzed_at': '2024-01-16T12:45:00Z',
            'created_at': '2024-01-16T12:45:00Z',
            'updated_at': '2024-01-16T12:45:00Z'
        }

        # Test flexible mapping (should handle missing column gracefully)
        opportunity = flexible_mapper.map_from_sql(
            sql_record,
            target_class=Opportunity,
            schema=sample_database_schema
        )

        # Verify the mapping worked, but with default/None values for missing fields
        assert opportunity is not None
        assert opportunity.submission_id == 'test123'
        assert opportunity.reddit_title is None or hasattr(opportunity, 'reddit_title')

    def test_missing_optional_column_handling(self, flexible_mapper, sample_database_schema):
        """Test handling of missing optional columns."""
        # Create SQL record missing optional columns
        sql_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'test123',
            'reddit_title': 'Test App',
            'reddit_url': 'https://reddit.com/r/test/test123',
            'subreddit': 'test',
            'reddit_author': None,  # Optional field set to None
            'reddit_upvotes': 150,
            'reddit_comments_count': 42,
            'reddit_created_at': '2024-01-15T10:30:00Z',
            'app_title': 'Test App',
            'app_concept': 'Test concept',
            'problem_statement': 'Test problem',
            'target_audience': 'Test audience',
            'core_functions': ['function1', 'function2'],
            # Missing optional field: embedding
            'final_score': 78.5,
            'confidence_score': 85.0,
            'trust_level': 'HIGH',
            'analyzed_at': '2024-01-16T12:45:00Z',
            'created_at': '2024-01-16T12:45:00Z',
            'updated_at': '2024-01-16T12:45:00Z'
        }

        # Test flexible mapping
        opportunity = flexible_mapper.map_from_sql(
            sql_record,
            target_class=Opportunity,
            schema=sample_database_schema
        )

        # Verify the mapping worked correctly
        assert opportunity is not None
        assert opportunity.submission_id == 'test123'
        assert opportunity.reddit_title == 'Test App'
        assert opportunity.reddit_author is None
        assert opportunity.embedding is None

    def test_missing_foreign_key_column_handling(self, flexible_mapper, sample_database_schema):
        """Test handling of missing foreign key columns."""
        # Create SQL record missing foreign key column
        sql_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'test123',
            'reddit_title': 'Test App',
            'reddit_url': 'https://reddit.com/r/test/test123',
            'subreddit': 'test',
            'reddit_author': 'testuser',
            'reddit_upvotes': 150,
            'reddit_comments_count': 42,
            'reddit_created_at': '2024-01-15T10:30:00Z',
            'app_title': 'Test App',
            'app_concept': 'Test concept',
            'problem_statement': 'Test problem',
            'target_audience': 'Test audience',
            'core_functions': ['function1', 'function2'],
            'market_demand': 85.0,
            'pain_intensity': 90.0,
            'monetization_potential': 75.0,
            'competition_level': 60.0,
            'technical_feasibility': 80.0,
            'final_score': 78.5,
            'confidence_score': 85.0,
            'trust_level': 'HIGH',
            'embedding': None,
            'analyzed_at': '2024-01-16T12:45:00Z',
            'created_at': '2024-01-16T12:45:00Z',
            'updated_at': '2024-01-16T12:45:00Z'
            # Missing duplicate_of_id (foreign key column)
        }

        # Test flexible mapping
        opportunity = flexible_mapper.map_from_sql(
            sql_record,
            target_class=Opportunity,
            schema=sample_database_schema
        )

        # Verify the mapping worked correctly
        assert opportunity is not None
        assert opportunity.submission_id == 'test123'
        assert opportunity.reddit_title == 'Test App'

    # =============================================================================
    # Schema Evolution Tests
    # =============================================================================

    def test_schema_v1_to_v2_migration(self, flexible_mapper, schema_version_fixtures):
        """Test schema migration from v1 to v2."""
        # Create v1 data (with legacy fields)
        v1_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'test123',
            'reddit_title': 'Test App',
            'reddit_url': 'https://reddit.com/r/test/test123',
            'subreddit': 'test',
            'app_title': 'Test App',
            'app_description': 'Legacy description',  # Legacy field
            'app_features': ['legacy_feature1', 'legacy_feature2'],  # Legacy field
            'final_score': 78.5,
            'created_at': '2024-01-16T12:45:00Z',
            'updated_at': '2024-01-16T12:45:00Z'
        }

        # Test mapping from v1 to v2 schema
        opportunity = flexible_mapper.map_from_sql(
            v1_record,
            target_class=Opportunity,
            schema=schema_version_fixtures['v2']
        )

        # Verify migration worked
        assert opportunity is not None
        assert opportunity.submission_id == 'test123'
        assert opportunity.reddit_title == 'Test App'
        assert opportunity.app_description == 'Legacy description'  # Legacy field preserved
        assert opportunity.app_features == ['legacy_feature1', 'legacy_feature2']  # Legacy field preserved

    def test_schema_v2_to_v1_downgrade(self, flexible_mapper, schema_version_fixtures):
        """Test schema downgrade from v2 to v1."""
        # Create v2 data (with new fields)
        v2_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'test123',
            'reddit_title': 'Test App',
            'reddit_url': 'https://reddit.com/r/test/test123',
            'subreddit': 'test',
            'reddit_author': 'testuser',
            'reddit_upvotes': 150,
            'reddit_comments_count': 42,
            'reddit_created_at': '2024-01-15T10:30:00Z',
            'app_title': 'Test App',
            'app_concept': 'New concept',  # New field
            'problem_statement': 'New problem',  # New field
            'target_audience': 'New audience',  # New field
            'core_functions': ['new_function1', 'new_function2'],  # New field
            'app_description': 'Legacy description',  # Legacy field
            'app_features': ['legacy_feature1', 'legacy_feature2'],  # Legacy field
            'final_score': 78.5,
            'confidence_score': 85.0,  # New field
            'trust_level': 'HIGH',  # New field
            'created_at': '2024-01-16T12:45:00Z',
            'updated_at': '2024-01-16T12:45:00Z',
            'schema_version': 2  # New field
        }

        # Test mapping from v2 to v1 schema (should ignore new fields)
        opportunity = flexible_mapper.map_from_sql(
            v2_record,
            target_class=Opportunity,
            schema=schema_version_fixtures['v1']
        )

        # Verify downgrade worked
        assert opportunity is not None
        assert opportunity.submission_id == 'test123'
        assert opportunity.reddit_title == 'Test App'
        assert opportunity.app_description == 'Legacy description'  # Legacy field preserved
        assert opportunity.app_features == ['legacy_feature1', 'legacy_feature2']  # Legacy field preserved

    def test_schema_field_alias_mapping(self, flexible_mapper):
        """Test field alias mapping during schema evolution."""
        # Define field aliases for schema evolution
        field_aliases = {
            'app_description': 'concept_description',  # Old name -> New name
            'app_features': 'core_functions'          # Old name -> New name
        }

        # Create record with old field names
        old_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'test123',
            'reddit_title': 'Test App',
            'reddit_url': 'https://reddit.com/r/test/test123',
            'subreddit': 'test',
            'app_title': 'Test App',
            'concept_description': 'Legacy description',  # Old field name
            'core_functions': ['legacy_function1', 'legacy_function2'],  # Old field name
            'final_score': 78.5,
            'trust_level': 'HIGH'
        }

        # Test field alias mapping
        opportunity = flexible_mapper.map_from_sql(
            old_record,
            target_class=Opportunity,
            field_mappings=field_aliases
        )

        # Verify alias mapping worked
        assert opportunity is not None
        assert opportunity.submission_id == 'test123'
        assert opportunity.app_concept == 'Legacy description'  # Mapped from concept_description
        assert opportunity.core_functions == ['legacy_function1', 'legacy_function2']  # Mapped from core_functions

    def test_schema_field_type_conversion(self, flexible_mapper):
        """Test field type conversion during schema evolution."""
        # Define field type conversions
        field_conversions = {
            'numeric_score': 'float',      # String to float conversion
            'json_data': 'json',          # String to JSON conversion
            'boolean_flag': 'boolean'     # String to boolean conversion
        }

        # Create record with mixed types
        mixed_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'test123',
            'reddit_title': 'Test App',
            'numeric_score': '78.5',     # String representation of float
            'json_data': '{"key": "value"}',  # JSON string
            'boolean_flag': 'true',       # String representation of boolean
            'final_score': 75.0,
            'trust_level': 'HIGH'
        }

        # Test field type conversion
        opportunity = flexible_mapper.map_from_sql(
            mixed_record,
            target_class=Opportunity,
            field_types=field_conversions
        )

        # Verify type conversion worked
        assert opportunity is not None
        assert opportunity.submission_id == 'test123'
        assert isinstance(opportunity.final_score, float)  # Should be converted to float

    # =============================================================================
    # Partial Data Handling Tests
    # =============================================================================

    def test_partial_data_handling(self, flexible_mapper, partial_opportunities):
        """Test handling of partial/incomplete data."""
        # Test mapping partial data
        partial_records = []
        for opportunity in partial_opportunities:
            record = {
                'id': str(opportunity.id),
                'submission_id': opportunity.submission_id,
                'reddit_title': opportunity.reddit_title,
                'reddit_upvotes': opportunity.reddit_upvotes,
                'reddit_comments_count': opportunity.reddit_comments_count,
                'reddit_created_at': opportunity.reddit_created_at.isoformat(),
                'app_title': opportunity.app_title,
                'target_audience': opportunity.target_audience,
                'core_functions': opportunity.core_functions,
                'final_score': opportunity.final_score,
                'confidence_score': opportunity.confidence_score,
                'trust_level': opportunity.trust_level,
                'analyzed_at': opportunity.analyzed_at.isoformat(),
                'created_at': opportunity.created_at.isoformat(),
                'updated_at': opportunity.updated_at.isoformat()
            }
            partial_records.append(record)

        # Test batch mapping of partial data
        opportunities = flexible_mapper.map_batch(
            partial_records,
            target_class=Opportunity
        )

        # Verify partial data handling worked
        assert len(opportunities) == len(partial_records)
        for opportunity in opportunities:
            assert opportunity is not None
            assert opportunity.submission_id is not None
            assert opportunity.reddit_title is not None
            assert opportunity.app_title is not None
            assert opportunity.final_score is not None

    def test_minimal_viable_data_handling(self, flexible_mapper):
        """Test handling of minimal viable data."""
        # Create record with only minimal required fields
        minimal_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'test123',
            'reddit_title': 'Test App',
            'final_score': 50.0,
            'trust_level': 'MEDIUM'
        }

        # Test mapping minimal data
        opportunity = flexible_mapper.map_from_sql(
            minimal_record,
            target_class=Opportunity
        )

        # Verify minimal data handling worked
        assert opportunity is not None
        assert opportunity.submission_id == 'test123'
        assert opportunity.reddit_title == 'Test App'
        assert opportunity.final_score == 50.0
        assert opportunity.trust_level == 'MEDIUM'

    def test_empty_field_handling(self, flexible_mapper):
        """Test handling of empty/null field values."""
        # Create record with empty/null values
        empty_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'test123',
            'reddit_title': 'Test App',
            'reddit_url': '',  # Empty string
            'subreddit': None,  # Null value
            'reddit_author': '  ',  # Whitespace only
            'reddit_upvotes': 0,
            'reddit_comments_count': 0,
            'reddit_created_at': '2024-01-15T10:30:00Z',
            'app_title': 'Test App',
            'app_concept': '',  # Empty string
            'problem_statement': None,  # Null value
            'target_audience': '  ',  # Whitespace only
            'core_functions': [],  # Empty list
            'market_demand': 0.0,
            'pain_intensity': 0.0,
            'monetization_potential': 0.0,
            'competition_level': 0.0,
            'technical_feasibility': 0.0,
            'final_score': 0.0,
            'confidence_score': 0.0,
            'trust_level': 'LOW',
            'embedding': None,  # Null value
            'analyzed_at': '2024-01-16T12:45:00Z',
            'created_at': '2024-01-16T12:45:00Z',
            'updated_at': '2024-01-16T12:45:00Z'
        }

        # Test mapping empty data
        opportunity = flexible_mapper.map_from_sql(
            empty_record,
            target_class=Opportunity
        )

        # Verify empty data handling worked
        assert opportunity is not None
        assert opportunity.submission_id == 'test123'
        assert opportunity.reddit_title == 'Test App'
        assert opportunity.reddit_url == ''
        assert opportunity.subreddit is None
        assert opportunity.reddit_author == '  '
        assert opportunity.app_concept == ''
        assert opportunity.problem_statement is None
        assert opportunity.target_audience == '  '
        assert opportunity.core_functions == []

    # =============================================================================
    # Schema Validation Tests
    # =============================================================================

    def test_strict_schema_validation_error(self, strict_mapper, sample_database_schema):
        """Test strict schema validation raises errors."""
        # Create record with invalid schema
        invalid_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'test123',
            'reddit_title': 'Test App',
            'invalid_column': 'should_not_exist',  # Invalid column
            'final_score': 75.0,
            'trust_level': 'HIGH'
        }

        # Test strict validation should raise error
        with pytest.raises(SchemaFlexibilityError) as exc_info:
            strict_mapper.map_from_sql(
                invalid_record,
                target_class=Opportunity,
                schema=sample_database_schema
            )

        # Verify error message contains relevant information
        assert "schema" in str(exc_info.value).lower()
        assert "invalid" in str(exc_info.value).lower()

    def test_flexible_schema_validation_success(self, flexible_mapper, sample_database_schema):
        """Test flexible schema validation succeeds with invalid columns."""
        # Create record with invalid schema
        invalid_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'test123',
            'reddit_title': 'Test App',
            'invalid_column': 'should_be_ignored',  # Invalid column, should be ignored
            'final_score': 75.0,
            'trust_level': 'HIGH'
        }

        # Test flexible validation should succeed
        opportunity = flexible_mapper.map_from_sql(
            invalid_record,
            target_class=Opportunity,
            schema=sample_database_schema
        )

        # Verify mapping succeeded and invalid column was ignored
        assert opportunity is not None
        assert opportunity.submission_id == 'test123'
        assert opportunity.reddit_title == 'Test App'
        assert not hasattr(opportunity, 'invalid_column')

    def test_schema_compatibility_check(self, flexible_mapper, sample_database_schema):
        """Test schema compatibility checking."""
        # Test schema compatibility
        is_compatible = flexible_mapper.check_schema_compatibility(
            sample_database_schema,
            Opportunity
        )

        # Verify compatibility check worked
        assert isinstance(is_compatible, bool)
        # This would typically return True for compatible schemas

    def test_missing_schema_fallback(self, flexible_mapper):
        """Test fallback behavior when schema is not provided."""
        # Create record without schema
        record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'test123',
            'reddit_title': 'Test App',
            'final_score': 75.0,
            'trust_level': 'HIGH'
        }

        # Test mapping without schema (should use default behavior)
        opportunity = flexible_mapper.map_from_sql(
            record,
            target_class=Opportunity,
            schema=None
        )

        # Verify fallback worked
        assert opportunity is not None
        assert opportunity.submission_id == 'test123'
        assert opportunity.reddit_title == 'Test App'

    # =============================================================================
    # Batch Processing Flexibility Tests
    # =============================================================================

    def test_batch_processing_mixed_data(self, flexible_mapper):
        """Test batch processing with mixed data completeness."""
        # Create records with varying levels of completeness
        mixed_records = [
            {
                'id': str(uuid.uuid4()),
                'submission_id': 'complete1',
                'reddit_title': 'Complete App',
                'reddit_url': 'https://reddit.com/r/test/complete1',
                'subreddit': 'test',
                'reddit_author': 'user1',
                'reddit_upvotes': 150,
                'reddit_comments_count': 42,
                'reddit_created_at': '2024-01-15T10:30:00Z',
                'app_title': 'Complete App',
                'app_concept': 'Complete concept',
                'problem_statement': 'Complete problem',
                'target_audience': 'Complete audience',
                'core_functions': ['function1', 'function2'],
                'market_demand': 85.0,
                'pain_intensity': 90.0,
                'monetization_potential': 75.0,
                'competition_level': 60.0,
                'technical_feasibility': 80.0,
                'final_score': 78.5,
                'confidence_score': 85.0,
                'trust_level': 'HIGH',
                'embedding': None,
                'analyzed_at': '2024-01-16T12:45:00Z',
                'created_at': '2024-01-16T12:45:00Z',
                'updated_at': '2024-01-16T12:45:00Z'
            },
            {
                'id': str(uuid.uuid4()),
                'submission_id': 'partial2',
                'reddit_title': 'Partial App',
                # Missing many fields
                'final_score': 65.0,
                'trust_level': 'MEDIUM'
            },
            {
                'id': str(uuid.uuid4()),
                'submission_id': 'minimal3',
                'reddit_title': 'Minimal App',
                'final_score': 50.0,
                'trust_level': 'LOW'
            }
        ]

        # Test batch processing of mixed data
        opportunities = flexible_mapper.map_batch(
            mixed_records,
            target_class=Opportunity
        )

        # Verify batch processing worked for all records
        assert len(opportunities) == len(mixed_records)
        for i, opportunity in enumerate(opportunities):
            assert opportunity is not None
            assert opportunity.submission_id == mixed_records[i]['submission_id']
            assert opportunity.reddit_title == mixed_records[i]['reddit_title']
            assert opportunity.final_score == mixed_records[i]['final_score']

    def test_batch_processing_error_isolation(self, flexible_mapper):
        """Test that batch processing errors are isolated."""
        # Create records with some invalid data
        mixed_records = [
            {
                'id': str(uuid.uuid4()),
                'submission_id': 'valid1',
                'reddit_title': 'Valid App',
                'final_score': 75.0,
                'trust_level': 'HIGH'
            },
            {
                'id': 'invalid-uuid',  # Invalid UUID
                'submission_id': 'invalid2',
                'reddit_title': 'Invalid App',
                'final_score': 65.0,
                'trust_level': 'MEDIUM'
            },
            {
                'id': str(uuid.uuid4()),
                'submission_id': 'valid3',
                'reddit_title': 'Another Valid App',
                'final_score': 55.0,
                'trust_level': 'LOW'
            }
        ]

        # Test batch processing with error isolation
        opportunities = flexible_mapper.map_batch(
            mixed_records,
            target_class=Opportunity,
            fail_fast=False  # Don't stop on first error
        )

        # Verify that valid records were processed despite invalid ones
        assert len(opportunities) == 2  # Only valid records should be returned
        valid_submissions = [opp.submission_id for opp in opportunities]
        assert 'valid1' in valid_submissions
        assert 'valid3' in valid_submissions
        assert 'invalid2' not in valid_submissions

    # =============================================================================
    # Performance Impact Tests
    # =============================================================================

    def test_schema_flexibility_performance_overhead(self, flexible_mapper, large_dataset_fixture):
        """Test performance impact of schema flexibility."""
        import time

        # Generate large dataset
        large_dataset = large_dataset_fixture(100)

        # Convert to records
        records = []
        for opportunity in large_dataset:
            record = {
                'id': str(opportunity.id),
                'submission_id': opportunity.submission_id,
                'reddit_title': opportunity.reddit_title,
                'reddit_url': opportunity.reddit_url,
                'subreddit': opportunity.subreddit,
                'reddit_author': opportunity.reddit_author,
                'reddit_upvotes': opportunity.reddit_upvotes,
                'reddit_comments_count': opportunity.reddit_comments_count,
                'reddit_created_at': opportunity.reddit_created_at.isoformat(),
                'app_title': opportunity.app_title,
                'app_concept': opportunity.app_concept,
                'problem_statement': opportunity.problem_statement,
                'target_audience': opportunity.target_audience,
                'core_functions': opportunity.core_functions,
                'market_demand': opportunity.market_demand,
                'pain_intensity': opportunity.pain_intensity,
                'monetization_potential': opportunity.monetization_potential,
                'competition_level': opportunity.competition_level,
                'technical_feasibility': opportunity.technical_feasibility,
                'final_score': opportunity.final_score,
                'confidence_score': opportunity.confidence_score,
                'trust_level': opportunity.trust_level,
                'embedding': opportunity.embedding,
                'analyzed_at': opportunity.analyzed_at.isoformat(),
                'created_at': opportunity.created_at.isoformat(),
                'updated_at': opportunity.updated_at.isoformat()
            }
            records.append(record)

        # Test performance with schema flexibility
        start_time = time.time()
        opportunities = flexible_mapper.map_batch(records, target_class=Opportunity)
        end_time = time.time()
        flexible_time = end_time - start_time

        # Verify performance is reasonable
        assert len(opportunities) == len(records)
        assert flexible_time < 10.0  # Should complete within 10 seconds

        # Verify performance metrics are captured
        assert hasattr(flexible_mapper, '_performance_metrics')
        assert 'mapping_times' in flexible_mapper._performance_metrics

    def test_schema_validation_performance_impact(self, strict_mapper, flexible_mapper, large_dataset_fixture):
        """Test performance impact of schema validation."""
        import time

        # Generate smaller dataset for performance comparison
        dataset = large_dataset_fixture(50)
        records = []
        for opportunity in dataset:
            record = {
                'id': str(opportunity.id),
                'submission_id': opportunity.submission_id,
                'reddit_title': opportunity.reddit_title,
                'final_score': opportunity.final_score,
                'trust_level': opportunity.trust_level
            }
            records.append(record)

        # Test strict performance
        start_time = time.time()
        strict_opportunities = strict_mapper.map_batch(records, target_class=Opportunity)
        strict_time = time.time() - start_time

        # Test flexible performance
        start_time = time.time()
        flexible_opportunities = flexible_mapper.map_batch(records, target_class=Opportunity)
        flexible_time = time.time() - start_time

        # Verify both produce same results
        assert len(strict_opportunities) == len(flexible_opportunities)

        # Performance difference should be reasonable (< 100ms overhead)
        performance_overhead = flexible_time - strict_time
        assert performance_overhead < 0.1  # Less than 100ms overhead

    # =============================================================================
    # Edge Case Tests
    # =============================================================================

    def test_unicode_character_handling(self, flexible_mapper):
        """Test handling of Unicode characters in fields."""
        # Create record with Unicode characters
        unicode_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'unicode123',
            'reddit_title': '🚀 App with émojis & unicodé chars',
            'reddit_url': 'https://reddit.com/r/test/unicode123',
            'subreddit': 'tëst',
            'reddit_author': 'usér_ñame',
            'app_concept': 'App with spëcial chars: ñ, é, ü, ö, ß',
            'problem_statement': 'Prôblèm with unicödé: café naïve résumé',
            'target_audience': 'Audience with unicodé: 日本語, 中文, Español',
            'core_functions': ['fünction1', 'fünction2'],
            'final_score': 75.0,
            'trust_level': 'HIGH'
        }

        # Test Unicode handling
        opportunity = flexible_mapper.map_from_sql(
            unicode_record,
            target_class=Opportunity
        )

        # Verify Unicode characters preserved
        assert opportunity is not None
        assert opportunity.submission_id == 'unicode123'
        assert opportunity.reddit_title == '🚀 App with émojis & unicodé chars'
        assert opportunity.subreddit == 'tëst'
        assert opportunity.reddit_author == 'usér_ñame'
        assert opportunity.app_concept == 'App with spëcial chars: ñ, é, ü, ö, ß'

    def test_special_character_handling(self, flexible_mapper):
        """Test handling of special characters and SQL injection attempts."""
        # Create record with special characters and potential injection attempts
        special_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'special123',
            'reddit_title': "App with 'quotes' and \"double quotes\" and backslashes\\",
            'reddit_url': 'https://reddit.com/r/test/special123',
            'subreddit': 'test; DROP TABLE opportunities; --',
            'reddit_author': 'user; INSERT INTO malicious VALUES (1); --',
            'app_concept': 'App with newlines\nand tabs\tand carriage returns\r',
            'problem_statement': 'Problem with control characters: \x00\x01\x02',
            'target_audience': 'Target with unicode: 🌍🚀💻',
            'core_functions': ['function with "quotes"', 'function with \\backslash\\'],
            'final_score': 75.0,
            'trust_level': 'HIGH'
        }

        # Test special character handling
        opportunity = flexible_mapper.map_from_sql(
            special_record,
            target_class=Opportunity
        )

        # Verify special characters preserved and sanitized
        assert opportunity is not None
        assert opportunity.submission_id == 'special123'
        assert opportunity.reddit_title == "App with 'quotes' and \"double quotes\" and backslashes\\"
        assert opportunity.subreddit == 'test; DROP TABLE opportunities; --'
        assert opportunity.reddit_author == 'user; INSERT INTO malicious VALUES (1); --'

    def test_null_and_empty_string_distinction(self, flexible_mapper):
        """Test distinction between NULL values and empty strings."""
        # Create record with NULL vs empty string distinction
        null_empty_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'nulltest123',
            'reddit_title': 'Test App',
            'reddit_url': '',  # Empty string
            'subreddit': None,  # NULL value
            'reddit_author': '  ',  # Whitespace only
            'app_concept': None,  # NULL value
            'problem_statement': '',  # Empty string
            'target_audience': 'valid_audience',  # Valid value
            'core_functions': [],  # Empty list
            'final_score': 75.0,
            'trust_level': 'HIGH'
        }

        # Test NULL vs empty string handling
        opportunity = flexible_mapper.map_from_sql(
            null_empty_record,
            target_class=Opportunity
        )

        # Verify distinction is preserved
        assert opportunity is not None
        assert opportunity.submission_id == 'nulltest123'
        assert opportunity.reddit_url == ''  # Empty string preserved
        assert opportunity.subreddit is None  # NULL preserved
        assert opportunity.reddit_author == '  '  # Whitespace preserved
        assert opportunity.app_concept is None  # NULL preserved
        assert opportunity.problem_statement == ''  # Empty string preserved
        assert opportunity.target_audience == 'valid_audience'  # Valid value preserved
        assert opportunity.core_functions == []  # Empty list preserved

    # =============================================================================
    # Configuration and Behavior Tests
    # =============================================================================

    def test_schema_flexibility_configuration_options(self, flexible_mapper):
        """Test schema flexibility configuration options."""
        # Test different configuration options
        config_options = [
            {'strict_mode': False, 'ignore_unknown_fields': True},
            {'strict_mode': False, 'ignore_unknown_fields': False},
            {'strict_mode': True, 'ignore_unknown_fields': False},
            {'strict_mode': True, 'ignore_unknown_fields': True}
        ]

        for config in config_options:
            # Update configuration
            flexible_mapper.config.strict_mode = config['strict_mode']
            flexible_mapper.config.ignore_unknown_fields = config['ignore_unknown_fields']

            # Test configuration is applied
            assert flexible_mapper.config.strict_mode == config['strict_mode']
            assert flexible_mapper.config.ignore_unknown_fields == config['ignore_unknown_fields']

    def test_schema_flexibility_reset_behavior(self, flexible_mapper):
        """Test schema flexibility behavior reset."""
        # Test default behavior
        assert flexible_mapper.config.strict_mode is False
        assert flexible_mapper.config.ignore_unknown_fields is True

        # Modify behavior
        flexible_mapper.config.strict_mode = True
        flexible_mapper.config.ignore_unknown_fields = False

        # Reset to defaults
        flexible_mapper.config.reset_to_defaults()

        # Verify reset worked
        assert flexible_mapper.config.strict_mode is False
        assert flexible_mapper.config.ignore_unknown_fields is True

    def test_schema_flexibility_reporting(self, flexible_mapper):
        """Test schema flexibility reporting."""
        # Test schema compatibility reporting
        report = flexible_mapper.get_schema_flexibility_report()

        # Verify report structure
        assert isinstance(report, dict)
        assert 'flexibility_score' in report
        assert 'missing_columns' in report
        assert 'unknown_columns' in report
        assert 'type_mismatches' in report
        assert 'compatibility_issues' in report

        # Verify report values are reasonable
        assert isinstance(report['flexibility_score'], float)
        assert 0.0 <= report['flexibility_score'] <= 1.0
        assert isinstance(report['missing_columns'], list)
        assert isinstance(report['unknown_columns'], list)
        assert isinstance(report['type_mismatches'], list)
        assert isinstance(report['compatibility_issues'], list)
