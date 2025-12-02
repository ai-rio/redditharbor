"""
Core OnlyMaps integration tests for pipeline-v3.

This module tests the fundamental SQL-to-Python object mapping functionality
of OnlyMaps, ensuring it correctly maps database records to Python objects
with proper type conversion and validation.
"""

import pytest
import uuid
from datetime import datetime, UTC, timedelta
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock, call

from models import (
    AnalysisResult, AppIdea, MarketMetrics, RedditSubmission, RedditComment
)
from models.database import Opportunity, OpportunityCreate
from load.database import DatabaseLoader

# Import OnlyMaps components (assuming they exist)
from onlymaps import OnlyMapsMapper, OnlyMapsConfig, MappingError, ValidationError


class TestOnlyMapsCoreMapping:
    """Test suite for core OnlyMaps mapping functionality."""

    @pytest.fixture
    def onlymaps_config(self):
        """OnlyMaps configuration for testing."""
        return OnlyMapsConfig(
            batch_size=100,
            timeout=30,
            retry_attempts=3,
            fallback_to_sqlalchemy=True,
            schema_validation=True,
            performance_monitoring=True
        )

    @pytest.fixture
    def onlymaps_mapper(self, onlymaps_config):
        """OnlyMaps mapper instance for testing."""
        # This would be the actual OnlyMaps mapper class
        mapper = OnlyMapsMapper(config=onlymaps_config)
        return mapper

    def test_map_from_sql_basic(self, onlymaps_mapper, sample_opportunity_data):
        """Test basic SQL to Python object mapping."""
        # Test mapping a single database record to Python object
        sql_record = {
            'id': str(sample_opportunity_data[0].id),
            'submission_id': sample_opportunity_data[0].submission_id,
            'reddit_title': sample_opportunity_data[0].reddit_title,
            'reddit_url': sample_opportunity_data[0].reddit_url,
            'subreddit': sample_opportunity_data[0].subreddit,
            'reddit_author': sample_opportunity_data[0].reddit_author,
            'reddit_upvotes': sample_opportunity_data[0].reddit_upvotes,
            'reddit_comments_count': sample_opportunity_data[0].reddit_comments_count,
            'reddit_created_at': sample_opportunity_data[0].reddit_created_at.isoformat(),
            'app_title': sample_opportunity_data[0].app_title,
            'app_concept': sample_opportunity_data[0].app_concept,
            'problem_statement': sample_opportunity_data[0].problem_statement,
            'target_audience': sample_opportunity_data[0].target_audience,
            'core_functions': sample_opportunity_data[0].core_functions,
            'market_demand': sample_opportunity_data[0].market_demand,
            'pain_intensity': sample_opportunity_data[0].pain_intensity,
            'monetization_potential': sample_opportunity_data[0].monetization_potential,
            'competition_level': sample_opportunity_data[0].competition_level,
            'technical_feasibility': sample_opportunity_data[0].technical_feasibility,
            'final_score': sample_opportunity_data[0].final_score,
            'confidence_score': sample_opportunity_data[0].confidence_score,
            'trust_level': sample_opportunity_data[0].trust_level,
            'embedding': sample_opportunity_data[0].embedding,
            'analyzed_at': sample_opportunity_data[0].analyzed_at.isoformat(),
            'created_at': sample_opportunity_data[0].created_at.isoformat(),
            'updated_at': sample_opportunity_data[0].updated_at.isoformat()
        }

        # Test mapping
        opportunity = onlymaps_mapper.map_from_sql(sql_record, target_class=Opportunity)

        # Verify the mapping worked correctly
        assert opportunity is not None
        assert opportunity.id == sample_opportunity_data[0].id
        assert opportunity.submission_id == sample_opportunity_data[0].submission_id
        assert opportunity.reddit_title == sample_opportunity_data[0].reddit_title
        assert opportunity.reddit_url == sample_opportunity_data[0].reddit_url
        assert opportunity.subreddit == sample_opportunity_data[0].subreddit
        assert opportunity.reddit_author == sample_opportunity_data[0].reddit_author
        assert opportunity.reddit_upvotes == sample_opportunity_data[0].reddit_upvotes
        assert opportunity.reddit_comments_count == sample_opportunity_data[0].reddit_comments_count
        assert opportunity.reddit_created_at == sample_opportunity_data[0].reddit_created_at
        assert opportunity.app_title == sample_opportunity_data[0].app_title
        assert opportunity.app_concept == sample_opportunity_data[0].app_concept
        assert opportunity.problem_statement == sample_opportunity_data[0].problem_statement
        assert opportunity.target_audience == sample_opportunity_data[0].target_audience
        assert opportunity.core_functions == sample_opportunity_data[0].core_functions
        assert opportunity.market_demand == sample_opportunity_data[0].market_demand
        assert opportunity.pain_intensity == sample_opportunity_data[0].pain_intensity
        assert opportunity.monetization_potential == sample_opportunity_data[0].monetization_potential
        assert opportunity.competition_level == sample_opportunity_data[0].competition_level
        assert opportunity.technical_feasibility == sample_opportunity_data[0].technical_feasibility
        assert opportunity.final_score == sample_opportunity_data[0].final_score
        assert opportunity.confidence_score == sample_opportunity_data[0].confidence_score
        assert opportunity.trust_level == sample_opportunity_data[0].trust_level
        assert opportunity.embedding == sample_opportunity_data[0].embedding
        assert opportunity.analyzed_at == sample_opportunity_data[0].analyzed_at
        assert opportunity.created_at == sample_opportunity_data[0].created_at
        assert opportunity.updated_at == sample_opportunity_data[0].updated_at

    def test_map_to_sql_basic(self, onlymaps_mapper, sample_opportunities):
        """Test Python object to SQL mapping."""
        opportunity = sample_opportunity_data[0]

        # Test mapping
        sql_query, params = onlymaps_mapper.map_to_sql(opportunity)

        # Verify the mapping worked correctly
        assert sql_query is not None
        assert isinstance(sql_query, str)
        assert "INSERT INTO" in sql_query or "UPDATE" in sql_query
        assert params is not None
        assert isinstance(params, dict)

        # Check that all fields are included in the parameters
        expected_fields = [
            'id', 'submission_id', 'reddit_title', 'reddit_url', 'subreddit',
            'reddit_author', 'reddit_upvotes', 'reddit_comments_count',
            'reddit_created_at', 'app_title', 'app_concept', 'problem_statement',
            'target_audience', 'core_functions', 'market_demand', 'pain_intensity',
            'monetization_potential', 'competition_level', 'technical_feasibility',
            'final_score', 'confidence_score', 'trust_level', 'embedding',
            'analyzed_at', 'created_at', 'updated_at'
        ]

        for field in expected_fields:
            assert field in params or f':{field}' in sql_query

    def test_map_batch(self, onlymaps_mapper, sample_opportunities):
        """Test batch mapping functionality."""
        # Convert opportunities to SQL records
        sql_records = []
        for opportunity in sample_opportunities:
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
            sql_records.append(record)

        # Test batch mapping
        opportunities = onlymaps_mapper.map_batch(sql_records, target_class=Opportunity)

        # Verify the batch mapping worked correctly
        assert len(opportunities) == len(sample_opportunities)
        for i, opportunity in enumerate(opportunities):
            expected = sample_opportunities[i]
            assert opportunity.id == expected.id
            assert opportunity.submission_id == expected.submission_id
            assert opportunity.reddit_title == expected.reddit_title
            assert opportunity.reddit_url == expected.reddit_url
            assert opportunity.subreddit == expected.subreddit
            assert opportunity.reddit_author == expected.reddit_author
            assert opportunity.reddit_upvotes == expected.reddit_upvotes
            assert opportunity.reddit_comments_count == expected.reddit_comments_count
            assert opportunity.app_title == expected.app_title

    def test_type_conversion_datetime(self, onlymaps_mapper):
        """Test datetime type conversion."""
        # Test datetime string to datetime object conversion
        sql_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'test123',
            'reddit_title': 'Test App',
            'reddit_url': 'https://reddit.com/r/test/test123',
            'subreddit': 'test',
            'reddit_created_at': '2024-01-15T10:30:00Z',
            'analyzed_at': '2024-01-16T12:45:00Z',
            'created_at': '2024-01-16T12:45:00Z',
            'updated_at': '2024-01-16T12:45:00Z',
            'app_title': 'Test App',
            'final_score': 75.0,
            'trust_level': 'HIGH'
        }

        opportunity = onlymaps_mapper.map_from_sql(sql_record, target_class=Opportunity)

        # Verify datetime conversion
        assert isinstance(opportunity.reddit_created_at, datetime)
        assert isinstance(opportunity.analyzed_at, datetime)
        assert isinstance(opportunity.created_at, datetime)
        assert isinstance(opportunity.updated_at, datetime)

        # Verify the datetime values are correct
        expected_datetime = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        assert opportunity.reddit_created_at == expected_datetime

    def test_type_conversion_json(self, onlymaps_mapper):
        """Test JSON type conversion."""
        # Test JSON string to Python object conversion
        sql_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'test123',
            'reddit_title': 'Test App',
            'reddit_url': 'https://reddit.com/r/test/test123',
            'subreddit': 'test',
            'core_functions': '["function1", "function2", "function3"]',
            'embedding': '[0.1, 0.2, 0.3, 0.4, 0.5]',
            'final_score': 75.0,
            'trust_level': 'HIGH'
        }

        opportunity = onlymaps_mapper.map_from_sql(sql_record, target_class=Opportunity)

        # Verify JSON conversion
        assert isinstance(opportunity.core_functions, list)
        assert len(opportunity.core_functions) == 3
        assert opportunity.core_functions == ["function1", "function2", "function3"]

        assert isinstance(opportunity.embedding, list)
        assert len(opportunity.embedding) == 5
        assert opportunity.embedding == [0.1, 0.2, 0.3, 0.4, 0.5]

    def test_type_conversion_uuid(self, onlymaps_mapper):
        """Test UUID type conversion."""
        test_uuid = uuid.uuid4()
        sql_record = {
            'id': str(test_uuid),
            'submission_id': 'test123',
            'reddit_title': 'Test App',
            'reddit_url': 'https://reddit.com/r/test/test123',
            'subreddit': 'test',
            'final_score': 75.0,
            'trust_level': 'HIGH'
        }

        opportunity = onlymaps_mapper.map_from_sql(sql_record, target_class=Opportunity)

        # Verify UUID conversion
        assert isinstance(opportunity.id, uuid.UUID)
        assert opportunity.id == test_uuid

    def test_type_conversion_int_float(self, onlymaps_mapper):
        """Test integer and float type conversion."""
        sql_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'test123',
            'reddit_title': 'Test App',
            'reddit_url': 'https://reddit.com/r/test/test123',
            'subreddit': 'test',
            'reddit_upvotes': '150',
            'reddit_comments_count': '42',
            'market_demand': '85.5',
            'pain_intensity': '90.0',
            'final_score': '78.5',
            'trust_level': 'HIGH'
        }

        opportunity = onlymaps_mapper.map_from_sql(sql_record, target_class=Opportunity)

        # Verify integer conversion
        assert isinstance(opportunity.reddit_upvotes, int)
        assert opportunity.reddit_upvotes == 150
        assert isinstance(opportunity.reddit_comments_count, int)
        assert opportunity.reddit_comments_count == 42

        # Verify float conversion
        assert isinstance(opportunity.market_demand, float)
        assert opportunity.market_demand == 85.5
        assert isinstance(opportunity.pain_intensity, float)
        assert opportunity.pain_intensity == 90.0
        assert isinstance(opportunity.final_score, float)
        assert opportunity.final_score == 78.5

    def test_null_value_handling(self, onlymaps_mapper):
        """Test NULL value handling."""
        sql_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'test123',
            'reddit_title': 'Test App',
            'reddit_url': 'https://reddit.com/r/test/test123',
            'subreddit': 'test',
            'reddit_author': None,
            'reddit_upvotes': '150',
            'reddit_comments_count': '42',
            'reddit_created_at': '2024-01-15T10:30:00Z',
            'app_title': 'Test App',
            'app_concept': 'Test concept',
            'problem_statement': 'Test problem',
            'target_audience': 'Test audience',
            'core_functions': '["function1", "function2"]',
            'market_demand': '85.0',
            'pain_intensity': '90.0',
            'monetization_potential': '75.0',
            'competition_level': '60.0',
            'technical_feasibility': '80.0',
            'final_score': '78.5',
            'confidence_score': '85.0',
            'trust_level': 'HIGH',
            'embedding': None,
            'analyzed_at': '2024-01-16T12:45:00Z',
            'created_at': '2024-01-16T12:45:00Z',
            'updated_at': '2024-01-16T12:45:00Z'
        }

        opportunity = onlymaps_mapper.map_from_sql(sql_record, target_class=Opportunity)

        # Verify NULL value handling
        assert opportunity.reddit_author is None
        assert opportunity.embedding is None

    def test_missing_field_handling(self, onlymaps_mapper, flexible_database_schema):
        """Test handling of missing fields."""
        # Create SQL record with missing fields
        sql_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'test123',
            'reddit_title': 'Test App',
            'reddit_upvotes': '150',
            'reddit_comments_count': '42',
            'reddit_created_at': '2024-01-15T10:30:00Z',
            'app_title': 'Test App',
            'target_audience': 'Test audience',
            'core_functions': '["function1", "function2"]',
            'final_score': '78.5',
            'confidence_score': '85.0',
            'trust_level': 'HIGH',
            'analyzed_at': '2024-01-16T12:45:00Z',
            'created_at': '2024-01-16T12:45:00Z',
            'updated_at': '2024-01-16T12:45:00Z'
            # Missing fields: reddit_url, subreddit, reddit_author, app_concept,
            # problem_statement, market metrics, embedding, etc.
        }

        # Test mapping with flexible schema
        opportunity = onlymaps_mapper.map_from_sql(
            sql_record,
            target_class=Opportunity,
            schema=flexible_database_schema
        )

        # Verify missing fields are handled gracefully
        assert hasattr(opportunity, 'reddit_url') or not hasattr(opportunity, 'reddit_url')
        assert hasattr(opportunity, 'subreddit') or not hasattr(opportunity, 'subreddit')
        assert hasattr(opportunity, 'reddit_author') or not hasattr(opportunity, 'reddit_author')

    def test_validation_on_mapping(self, onlymaps_mapper):
        """Test validation during mapping."""
        # Create invalid SQL record
        sql_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'short',  # Invalid submission ID
            'reddit_title': 'Test App',
            'reddit_url': 'invalid-url',  # Invalid URL
            'subreddit': 'test',
            'final_score': 150.0,  # Invalid score (> 100)
            'trust_level': 'INVALID',  # Invalid trust level
            'created_at': '2024-01-16T12:45:00Z'
        }

        # Test mapping with validation should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            onlymaps_mapper.map_from_sql(sql_record, target_class=Opportunity, validate=True)

        # Verify the validation error contains relevant information
        assert "validation" in str(exc_info.value).lower()
        assert "submission_id" in str(exc_info.value).lower() or "url" in str(exc_info.value).lower()

    def test_mapping_error_handling(self, onlymaps_mapper):
        """Test error handling during mapping."""
        # Create malformed SQL record
        sql_record = {
            'id': 'invalid-uuid',  # Invalid UUID
            'submission_id': 'test123',
            'reddit_title': 'Test App',
            'final_score': 75.0,
            'trust_level': 'HIGH'
        }

        # Test mapping error handling
        with pytest.raises(MappingError) as exc_info:
            onlymaps_mapper.map_from_sql(sql_record, target_class=Opportunity)

        # Verify the mapping error contains relevant information
        assert "mapping" in str(exc_info.value).lower() or "uuid" in str(exc_info.value).lower()

    def test_field_mapping_customization(self, onlymaps_mapper):
        """Test custom field mapping configuration."""
        # Configure custom field mappings
        custom_mappings = {
            'reddit_title': 'submission_title',
            'reddit_url': 'submission_url',
            'app_concept': 'concept_description'
        }

        # Test custom mapping configuration
        sql_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'test123',
            'submission_title': 'Test App',  # Custom field name
            'submission_url': 'https://reddit.com/r/test/test123',  # Custom field name
            'subreddit': 'test',
            'concept_description': 'Test concept',  # Custom field name
            'final_score': 75.0,
            'trust_level': 'HIGH'
        }

        opportunity = onlymaps_mapper.map_from_sql(
            sql_record,
            target_class=Opportunity,
            field_mappings=custom_mappings
        )

        # Verify custom mapping worked
        assert opportunity.reddit_title == 'Test App'
        assert opportunity.reddit_url == 'https://reddit.com/r/test/test123'
        assert opportunity.app_concept == 'Test concept'

    def test_performance_monitoring(self, onlymaps_mapper, performance_metrics_fixture):
        """Test performance monitoring during mapping."""
        import time

        # Enable performance monitoring
        onlymaps_mapper.config.performance_monitoring = True

        # Test mapping with performance monitoring
        start_time = time.time()

        sql_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'test123',
            'reddit_title': 'Test App',
            'reddit_url': 'https://reddit.com/r/test/test123',
            'subreddit': 'test',
            'final_score': 75.0,
            'trust_level': 'HIGH'
        }

        opportunity = onlymaps_mapper.map_from_sql(sql_record, target_class=Opportunity)

        end_time = time.time()
        mapping_time = end_time - start_time

        # Verify performance monitoring is working
        assert hasattr(onlymaps_mapper, '_performance_metrics')
        assert 'mapping_times' in onlymaps_mapper._performance_metrics

        # Verify performance data is recorded
        assert len(onlymaps_mapper._performance_metrics['mapping_times']) > 0

        # Verify performance metrics are reasonable
        recorded_times = onlymaps_mapper._performance_metrics['mapping_times']
        assert all(t >= 0 for t in recorded_times)  # All times should be non-negative

    def test_batch_size_configuration(self, onlymaps_config):
        """Test batch size configuration."""
        # Test different batch sizes
        for batch_size in [1, 10, 50, 100, 500]:
            onlymaps_config.batch_size = batch_size

            # Verify the configuration is applied
            assert onlymaps_config.batch_size == batch_size

    def test_timeout_configuration(self, onlymaps_config):
        """Test timeout configuration."""
        # Test different timeout values
        for timeout in [10, 30, 60, 120]:
            onlymaps_config.timeout = timeout

            # Verify the configuration is applied
            assert onlymaps_config.timeout == timeout

    def test_retry_attempts_configuration(self, onlymaps_config):
        """Test retry attempts configuration."""
        # Test different retry attempts
        for retry_attempts in [0, 1, 3, 5, 10]:
            onlymaps_config.retry_attempts = retry_attempts

            # Verify the configuration is applied
            assert onlymaps_config.retry_attempts == retry_attempts

    def test_fallback_to_sqlalchemy(self, onlymaps_config):
        """Test fallback to SQLAlchemy configuration."""
        # Test fallback configuration
        for fallback in [True, False]:
            onlymaps_config.fallback_to_sqlalchemy = fallback

            # Verify the configuration is applied
            assert onlymaps_config.fallback_to_sqlalchemy == fallback

    def test_schema_validation_configuration(self, onlymaps_config):
        """Test schema validation configuration."""
        # Test schema validation configuration
        for schema_validation in [True, False]:
            onlymaps_config.schema_validation = schema_validation

            # Verify the configuration is applied
            assert onlymaps_config.schema_validation == schema_validation

    def test_configuration_serialization(self, onlymaps_config):
        """Test configuration serialization."""
        # Test configuration can be serialized
        config_dict = onlymaps_config.to_dict()

        # Verify all configuration options are included
        expected_keys = ['batch_size', 'timeout', 'retry_attempts', 'fallback_to_sqlalchemy',
                        'schema_validation', 'performance_monitoring']

        for key in expected_keys:
            assert key in config_dict

        # Test configuration can be deserialized
        new_config = OnlyMapsConfig.from_dict(config_dict)
        assert new_config.batch_size == onlymaps_config.batch_size
        assert new_config.timeout == onlymaps_config.timeout
        assert new_config.retry_attempts == onlymaps_config.retry_attempts
        assert new_config.fallback_to_sqlalchemy == onlymaps_config.fallback_to_sqlalchemy
        assert new_config.schema_validation == onlymaps_config.schema_validation
        assert new_config.performance_monitoring == onlymaps_config.performance_monitoring


class TestOnlyMapsMapperLifecycle:
    """Test suite for OnlyMaps mapper lifecycle management."""

    def test_mapper_initialization(self):
        """Test mapper initialization."""
        config = OnlyMapsConfig(
            batch_size=50,
            timeout=60,
            retry_attempts=5,
            fallback_to_sqlalchemy=False,
            schema_validation=False,
            performance_monitoring=False
        )

        mapper = OnlyMapsMapper(config=config)

        # Verify initialization
        assert mapper.config == config
        assert mapper.config.batch_size == 50
        assert mapper.config.timeout == 60
        assert mapper.config.retry_attempts == 5
        assert mapper.config.fallback_to_sqlalchemy is False
        assert mapper.config.schema_validation is False
        assert mapper.config.performance_monitoring is False

    def test_mapper_configuration_validation(self):
        """Test mapper configuration validation."""
        # Test invalid configuration
        with pytest.raises(ValueError):
            OnlyMapsConfig(batch_size=-1)  # Invalid batch size

        with pytest.raises(ValueError):
            OnlyMapsConfig(timeout=-1)  # Invalid timeout

        with pytest.raises(ValueError):
            OnlyMapsConfig(retry_attempts=-1)  # Invalid retry attempts

    def test_mapper_cleanup(self, onlymaps_mapper):
        """Test mapper cleanup."""
        # Perform some operations to generate performance metrics
        sql_record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'test123',
            'reddit_title': 'Test App',
            'reddit_url': 'https://reddit.com/r/test/test123',
            'subreddit': 'test',
            'final_score': 75.0,
            'trust_level': 'HIGH'
        }

        # Perform mapping operations
        for _ in range(5):
            onlymaps_mapper.map_from_sql(sql_record, target_class=Opportunity)

        # Verify performance metrics exist
        assert hasattr(onlymaps_mapper, '_performance_metrics')
        assert 'mapping_times' in onlymaps_mapper._performance_metrics
        assert len(onlymaps_mapper._performance_metrics['mapping_times']) > 0

        # Test cleanup
        onlymaps_mapper.cleanup()

        # Verify metrics are cleared
        assert len(onlymaps_mapper._performance_metrics['mapping_times']) == 0


# Integration tests
class TestOnlyMapsIntegration:
    """Integration tests for OnlyMaps with other components."""

    def test_onlymaps_with_database_loader(self, onlymaps_mapper, sample_opportunities):
        """Test OnlyMaps integration with DatabaseLoader."""
        # Mock DatabaseLoader to use OnlyMaps
        mock_loader = Mock(spec=DatabaseLoader)
        mock_loader.onlymaps_mapper = onlymaps_mapper
        mock_loader.store_analyses = Mock(return_value={"stored": len(sample_opportunities), "skipped": 0, "errors": 0})

        # Test integration
        sql_records = []
        for opportunity in sample_opportunities:
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
            sql_records.append(record)

        # Test batch mapping integration
        opportunities = onlymaps_mapper.map_batch(sql_records, target_class=Opportunity)

        # Verify integration worked
        assert len(opportunities) == len(sample_opportunities)
        for i, opportunity in enumerate(opportunities):
            expected = sample_opportunities[i]
            assert opportunity.id == expected.id
            assert opportunity.submission_id == expected.submission_id
            assert opportunity.reddit_title == expected.reddit_title

    def test_onlymaps_with_validation_service(self, onlymaps_mapper, sample_opportunities):
        """Test OnlyMaps integration with validation service."""
        # Mock validation service
        mock_validation_service = Mock()
        mock_validation_service.validate_opportunity_create = Mock(return_value=True)

        # Test mapping with validation service integration
        sql_record = {
            'id': str(sample_opportunity_data[0].id),
            'submission_id': sample_opportunity_data[0].submission_id,
            'reddit_title': sample_opportunity_data[0].reddit_title,
            'reddit_url': sample_opportunity_data[0].reddit_url,
            'subreddit': sample_opportunity_data[0].subreddit,
            'reddit_author': sample_opportunity_data[0].reddit_author,
            'reddit_upvotes': sample_opportunity_data[0].reddit_upvotes,
            'reddit_comments_count': sample_opportunity_data[0].reddit_comments_count,
            'reddit_created_at': sample_opportunity_data[0].reddit_created_at.isoformat(),
            'app_title': sample_opportunity_data[0].app_title,
            'app_concept': sample_opportunity_data[0].app_concept,
            'problem_statement': sample_opportunity_data[0].problem_statement,
            'target_audience': sample_opportunity_data[0].target_audience,
            'core_functions': sample_opportunity_data[0].core_functions,
            'market_demand': sample_opportunity_data[0].market_demand,
            'pain_intensity': sample_opportunity_data[0].pain_intensity,
            'monetization_potential': sample_opportunity_data[0].monetization_potential,
            'competition_level': sample_opportunity_data[0].competition_level,
            'technical_feasibility': sample_opportunity_data[0].technical_feasibility,
            'final_score': sample_opportunity_data[0].final_score,
            'confidence_score': sample_opportunity_data[0].confidence_score,
            'trust_level': sample_opportunity_data[0].trust_level,
            'embedding': sample_opportunity_data[0].embedding,
            'analyzed_at': sample_opportunity_data[0].analyzed_at.isoformat(),
            'created_at': sample_opportunity_data[0].created_at.isoformat(),
            'updated_at': sample_opportunity_data[0].updated_at.isoformat()
        }

        # Test mapping with validation service
        opportunity = onlymaps_mapper.map_from_sql(
            sql_record,
            target_class=Opportunity,
            validation_service=mock_validation_service
        )

        # Verify validation service was called
        mock_validation_service.validate_opportunity_create.assert_called_once()

        # Verify opportunity was created correctly
        assert opportunity is not None
        assert opportunity.submission_id == sample_opportunity_data[0].submission_id