"""
Extended configuration for pytest in pipeline-v3 OnlyMaps integration tests.

This file provides comprehensive fixtures and mock strategies for testing OnlyMaps
SQL-to-Python object mapping integration with pipeline-v3.
"""

import asyncio
import json
import os
import tempfile
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from load.database import DatabaseLoader

# Import models for fixtures
from models import (
    AnalysisResult,
    AppIdea,
    MarketMetrics,
    RedditComment,
    RedditSubmission,
)
from models.database import Opportunity, OpportunityCreate

# =============================================================================
# Database Schema Fixtures
# =============================================================================

@pytest.fixture
def sample_database_schema():
    """Sample database schema definitions for testing."""
    return {
        "opportunities": {
            "columns": {
                "id": "UUID PRIMARY KEY",
                "submission_id": "VARCHAR(10) NOT NULL UNIQUE",
                "reddit_title": "VARCHAR(300) NOT NULL",
                "reddit_url": "VARCHAR(500) NOT NULL",
                "subreddit": "VARCHAR(100) NOT NULL",
                "reddit_author": "VARCHAR(100)",
                "reddit_upvotes": "INTEGER NOT NULL DEFAULT 0",
                "reddit_comments_count": "INTEGER NOT NULL DEFAULT 0",
                "reddit_created_at": "TIMESTAMP NOT NULL",
                "app_title": "VARCHAR(200) NOT NULL",
                "app_concept": "TEXT NOT NULL",
                "problem_statement": "TEXT NOT NULL",
                "target_audience": "TEXT NOT NULL",
                "core_functions": "JSON NOT NULL",
                "market_demand": "FLOAT NOT NULL",
                "pain_intensity": "FLOAT NOT NULL",
                "monetization_potential": "FLOAT NOT NULL",
                "competition_level": "FLOAT NOT NULL",
                "technical_feasibility": "FLOAT NOT NULL",
                "final_score": "FLOAT NOT NULL",
                "confidence_score": "FLOAT NOT NULL",
                "trust_level": "VARCHAR(10) NOT NULL",
                "embedding": "JSON",
                "analyzed_at": "TIMESTAMP NOT NULL",
                "created_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
                "updated_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
                "is_duplicate": "BOOLEAN NOT NULL DEFAULT FALSE",
                "duplicate_of_id": "UUID REFERENCES opportunities(id)"
            },
            "indexes": [
                "idx_opportunities_final_score_trust",
                "idx_opportunities_subreddit_created",
                "idx_opportunities_analyzed_created",
                "idx_opportunities_core_functions"
            ]
        }
    }


@pytest.fixture
def flexible_database_schema():
    """Database schema with optional/missing columns for testing flexibility."""
    return {
        "opportunities": {
            "columns": {
                "id": "UUID PRIMARY KEY",
                "submission_id": "VARCHAR(10) NOT NULL UNIQUE",
                "reddit_title": "VARCHAR(300) NOT NULL",
                # Missing reddit_url, subreddit, reddit_author - testing flexibility
                "reddit_upvotes": "INTEGER NOT NULL DEFAULT 0",
                "reddit_comments_count": "INTEGER NOT NULL DEFAULT 0",
                "reddit_created_at": "TIMESTAMP NOT NULL",
                "app_title": "VARCHAR(200) NOT NULL",
                # Missing app_concept, problem_statement - testing schema evolution
                "target_audience": "TEXT NOT NULL",
                "core_functions": "JSON NOT NULL",
                # Missing market metrics - testing partial data handling
                "final_score": "FLOAT NOT NULL",
                "confidence_score": "FLOAT NOT NULL",
                "trust_level": "VARCHAR(10) NOT NULL",
                # Missing embedding - testing optional field handling
                "analyzed_at": "TIMESTAMP NOT NULL",
                "created_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
                "updated_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
                "is_duplicate": "BOOLEAN NOT NULL DEFAULT FALSE"
                # Missing duplicate_of_id - testing foreign key flexibility
            },
            "indexes": [
                "idx_opportunities_final_score_trust"
                # Missing other indexes for testing partial index handling
            ]
        }
    }


@pytest.fixture
def evolving_database_schema():
    """Database schema representing schema evolution over time."""
    return {
        "opportunities": {
            "columns": {
                "id": "UUID PRIMARY KEY",
                "submission_id": "VARCHAR(10) NOT NULL UNIQUE",
                "reddit_title": "VARCHAR(300) NOT NULL",
                "reddit_url": "VARCHAR(500) NOT NULL",
                "subreddit": "VARCHAR(100) NOT NULL",
                "reddit_author": "VARCHAR(100)",
                "reddit_upvotes": "INTEGER NOT NULL DEFAULT 0",
                "reddit_comments_count": "INTEGER NOT NULL DEFAULT 0",
                "reddit_created_at": "TIMESTAMP NOT NULL",
                # Legacy fields (deprecated)
                "app_description": "TEXT",  # Deprecated - replaced by app_concept
                "app_features": "JSON",     # Deprecated - replaced by core_functions
                # New fields
                "app_concept": "TEXT NOT NULL",
                "problem_statement": "TEXT NOT NULL",
                "target_audience": "TEXT NOT NULL",
                "core_functions": "JSON NOT NULL",
                "market_demand": "FLOAT NOT NULL",
                "pain_intensity": "FLOAT NOT NULL",
                "monetization_potential": "FLOAT NOT NULL",
                "competition_level": "FLOAT NOT NULL",
                "technical_feasibility": "FLOAT NOT NULL",
                "final_score": "FLOAT NOT NULL",
                "confidence_score": "FLOAT NOT NULL",
                "trust_level": "VARCHAR(10) NOT NULL",
                "embedding": "JSON",
                "analyzed_at": "TIMESTAMP NOT NULL",
                "created_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
                "updated_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
                "is_duplicate": "BOOLEAN NOT NULL DEFAULT FALSE",
                "duplicate_of_id": "UUID REFERENCES opportunities(id)",
                # Version tracking
                "schema_version": "INTEGER NOT NULL DEFAULT 1"
            },
            "indexes": [
                "idx_opportunities_final_score_trust",
                "idx_opportunities_subreddit_created",
                "idx_opportunities_analyzed_created",
                "idx_opportunities_core_functions",
                "idx_opportunities_schema_version"
            ]
        }
    }


# =============================================================================
# Data Fixtures
# =============================================================================

@pytest.fixture
def sample_reddit_submissions():
    """Sample Reddit submissions for testing."""
    return [
        RedditSubmission(
            id="abc123",
            title="AI-Powered Task Management App Needed",
            text="I'm struggling to find a good task management app that uses AI to prioritize tasks automatically. Current apps are too manual and don't understand my work patterns well.",
            author="productivity_pro",
            upvotes=150,
            downvotes=5,
            score=145,
            comments_count=42,
            subreddit="productivity",
            created_utc=datetime.now(UTC).replace(year=2024, month=1, day=15),
            permalink="/r/productivity/comments/abc123/"
        ),
        RedditSubmission(
            id="def456",
            title="Blockchain-based Social Media Platform",
            text="We need a decentralized social media platform that actually respects user privacy and gives us control over our data. Current platforms are exploitative.",
            author="privacy_advocate",
            upvotes=89,
            downvotes=2,
            score=87,
            comments_count=15,
            subreddit="technology",
            created_utc=datetime.now(UTC).replace(year=2024, month=2, day=10),
            permalink="/r/technology/comments/def456/"
        ),
        RedditSubmission(
            id="ghi789",
            title="Sustainable Fashion Marketplace",
            text="Looking for a marketplace that focuses on sustainable and ethical clothing. Fast fashion is destroying our planet and we need better alternatives.",
            author="eco_shopper",
            upvotes=203,
            downvotes=8,
            score=195,
            comments_count=67,
            subreddit="sustainableliving",
            created_utc=datetime.now(UTC).replace(year=2024, month=3, day=5),
            permalink="/r/sustainableliving/comments/ghi789/"
        )
    ]


@pytest.fixture
def sample_analysis_results(sample_reddit_submissions):
    """Sample analysis results corresponding to Reddit submissions."""
    return [
        AnalysisResult(
            submission_id="abc123",
            analyzed_at=datetime.now(UTC),
            app_idea=AppIdea(
                title="TaskFlow AI",
                app_concept="AI-powered task management that learns from user behavior",
                problem_statement="Users struggle with manual task prioritization and workflow optimization",
                target_audience="Professionals and productivity enthusiasts",
                core_functions=["AI task prioritization", "automated workflow optimization", "cross-platform sync"]
            ),
            market_metrics=MarketMetrics(
                market_demand=85.0,
                pain_intensity=90.0,
                monetization_potential=75.0,
                competition_level=60.0,
                technical_feasibility=80.0
            ),
            final_score=78.5,
            content_quality_score=82.5,
            is_spam=False,
            spam_indicators=[],
            confidence_score=85.0,
            trust_level="HIGH"
        ),
        AnalysisResult(
            submission_id="def456",
            analyzed_at=datetime.now(UTC),
            app_idea=AppIdea(
                title="DecentSocial",
                app_concept="Decentralized social media platform with user-owned data",
                problem_statement="Centralized platforms exploit user data and lack transparency",
                target_audience="Privacy-conscious users and social media enthusiasts",
                core_functions=["decentralized identity", "encrypted messaging", "user-controlled data"]
            ),
            market_metrics=MarketMetrics(
                market_demand=72.0,
                pain_intensity=85.0,
                monetization_potential=68.0,
                competition_level=45.0,
                technical_feasibility=65.0
            ),
            final_score=73.2,
            content_quality_score=76.0,
            is_spam=False,
            spam_indicators=[],
            confidence_score=78.0,
            trust_level="HIGH"
        ),
        AnalysisResult(
            submission_id="ghi789",
            analyzed_at=datetime.now(UTC),
            app_idea=AppIdea(
                title="EcoStyle",
                app_concept="Marketplace for sustainable and ethical fashion",
                problem_statement="Fast fashion contributes to environmental destruction and unethical labor practices",
                target_audience="Environmentally conscious consumers and ethical shoppers",
                core_functions=["sustainable product discovery", "ethical brand verification", "carbon footprint tracking"]
            ),
            market_metrics=MarketMetrics(
                market_demand=88.0,
                pain_intensity=92.0,
                monetization_potential=82.0,
                competition_level=35.0,
                technical_feasibility=75.0
            ),
            final_score=84.4,
            content_quality_score=87.5,
            is_spam=False,
            spam_indicators=[],
            confidence_score=88.0,
            trust_level="HIGH"
        )
    ]


@pytest.fixture
def sample_opportunities(sample_analysis_results):
    """Sample opportunities corresponding to analysis results."""
    return [
        Opportunity(
            id=uuid.uuid4(),
            submission_id=result.submission_id,
            reddit_title=result.app_idea.title,
            reddit_url=f"https://reddit.com/r/productivity/{result.submission_id}",
            subreddit="productivity",
            reddit_author="productivity_pro",
            reddit_upvotes=150,
            reddit_comments_count=42,
            reddit_created_at=datetime.now(UTC).replace(year=2024, month=1, day=15),
            app_title=result.app_idea.title,
            app_concept=result.app_idea.app_concept,
            problem_statement=result.app_idea.problem_statement,
            target_audience=result.app_idea.target_audience,
            core_functions=result.app_idea.core_functions,
            market_demand=result.market_metrics.market_demand,
            pain_intensity=result.market_metrics.pain_intensity,
            monetization_potential=result.market_metrics.monetization_potential,
            competition_level=result.market_metrics.competition_level,
            technical_feasibility=result.market_metrics.technical_feasibility,
            final_score=result.final_score,
            confidence_score=result.confidence_score,
            trust_level=result.trust_level,
            embedding=None,
            analyzed_at=result.analyzed_at,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ) for result in sample_analysis_results
    ]


@pytest.fixture
def partial_opportunities():
    """Opportunities with missing data for testing schema flexibility."""
    return [
        Opportunity(
            id=uuid.uuid4(),
            submission_id="partial123",
            reddit_title="Partial App Concept",
            # Missing reddit_url, subreddit, reddit_author
            reddit_upvotes=50,
            reddit_comments_count=10,
            reddit_created_at=datetime.now(UTC).replace(year=2024, month=4, day=1),
            app_title="Partial App",
            # Missing app_concept, problem_statement
            target_audience="Limited audience",
            core_functions=["basic_function"],
            # Missing market metrics
            final_score=65.0,
            confidence_score=70.0,
            trust_level="MEDIUM",
            # Missing embedding
            analyzed_at=datetime.now(UTC),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    ]


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_database_connection():
    """Mock database connection for testing OnlyMaps mapping."""
    mock_conn = Mock()
    mock_cursor = Mock()

    # Mock basic cursor operations
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__ = Mock(return_value=mock_cursor)
    mock_cursor.__exit__ = Mock(return_value=None)

    # Mock fetch operations
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []
    mock_cursor.fetchmany.return_value = []

    # Mock execute operations
    mock_cursor.execute = Mock()
    mock_cursor.executemany = Mock()

    return mock_conn


@pytest.fixture
def mock_onlymaps_mapper():
    """Mock OnlyMaps mapper for testing."""
    mapper = Mock()

    # Mock mapping methods
    mapper.map_from_sql = Mock(return_value=Opportunity())
    mapper.map_to_sql = Mock(return_value=("INSERT INTO opportunities VALUES (...)", []))
    mapper.map_batch = Mock(return_value=[Opportunity()])
    mapper.validate_schema = Mock(return_value=True)
    mapper.get_missing_columns = Mock(return_value=[])
    mapper.get_column_types = Mock(return_value={})

    return mapper


@pytest.fixture
def mock_sqlalchemy_session():
    """Mock SQLAlchemy session for comparison testing."""
    session = Mock()
    session.query = Mock()
    session.add = Mock()
    session.add_all = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.close = Mock()

    # Mock query results
    mock_query = Mock()
    session.query.return_value = mock_query
    mock_query.all.return_value = []
    mock_query.filter_by.return_value = mock_query
    mock_query.first.return_value = None

    return session


@pytest.fixture
def async_mock_database_connection():
    """Mock async database connection for async testing."""
    mock_conn = AsyncMock()
    mock_cursor = AsyncMock()

    # Mock async cursor operations
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__aenter__ = AsyncMock(return_value=mock_cursor)
    mock_cursor.__aexit__ = AsyncMock(return_value=None)

    # Mock async fetch operations
    mock_cursor.fetchone = AsyncMock(return_value=None)
    mock_cursor.fetchall = AsyncMock(return_value=[])
    mock_cursor.fetchmany = AsyncMock(return_value=[])

    # Mock async execute operations
    mock_cursor.execute = AsyncMock()
    mock_cursor.executemany = AsyncMock()

    return mock_conn


@pytest.fixture
def mock_validation_service():
    """Mock validation service for testing OnlyMaps validation."""
    service = Mock()

    # Mock validation methods
    service.validate_opportunity_create = AsyncMock(return_value=True)
    service.validate_database_constraints = AsyncMock(return_value=True)
    service.validate_reddit_data = Mock(return_value=True)
    service.validate_schema_compatibility = Mock(return_value=True)

    return service


# =============================================================================
# Performance Testing Fixtures
# =============================================================================

@pytest.fixture
def large_dataset_fixture():
    """Large dataset fixture for performance testing."""
    def generate_large_dataset(size: int = 1000):
        """Generate large dataset of opportunities."""
        opportunities = []
        for i in range(size):
            opportunity = Opportunity(
                id=uuid.uuid4(),
                submission_id=f"test_{i}",
                reddit_title=f"Test App {i}",
                reddit_url=f"https://reddit.com/r/test/test_{i}",
                subreddit="test",
                reddit_author=f"user_{i}",
                reddit_upvotes=i % 1000,
                reddit_comments_count=i % 100,
                reddit_created_at=datetime.now(UTC) - timedelta(days=i),
                app_title=f"Test Application {i}",
                app_concept=f"Test concept {i}",
                problem_statement=f"Test problem {i}",
                target_audience=f"Test audience {i}",
                core_functions=[f"function_{i % 5}"],
                market_demand=float(i % 100),
                pain_intensity=float(i % 100),
                monetization_potential=float(i % 100),
                competition_level=float(i % 100),
                technical_feasibility=float(i % 100),
                final_score=float(i % 100),
                confidence_score=float(i % 100),
                trust_level=["HIGH", "MEDIUM", "LOW"][i % 3],
                embedding=None,
                analyzed_at=datetime.now(UTC) - timedelta(days=i),
                created_at=datetime.utcnow() - timedelta(days=i),
                updated_at=datetime.utcnow()
            )
            opportunities.append(opportunity)
        return opportunities

    return generate_large_dataset


@pytest.fixture
def performance_metrics_fixture():
    """Performance metrics fixture for benchmarking."""
    return {
        "mapping_times": [],
        "query_times": [],
        "memory_usage": [],
        "cpu_usage": [],
        "batch_sizes": [10, 50, 100, 500, 1000]
    }


# =============================================================================
# Schema Evolution Fixtures
# =============================================================================

@pytest.fixture
def schema_version_fixtures():
    """Schema version fixtures for testing schema evolution."""
    return {
        "v1": {
            "columns": {
                "id": "UUID PRIMARY KEY",
                "submission_id": "VARCHAR(10) NOT NULL UNIQUE",
                "reddit_title": "VARCHAR(300) NOT NULL",
                "reddit_url": "VARCHAR(500) NOT NULL",
                "subreddit": "VARCHAR(100) NOT NULL",
                "app_title": "VARCHAR(200) NOT NULL",
                "app_description": "TEXT",  # Legacy field
                "app_features": "JSON",     # Legacy field
                "final_score": "FLOAT NOT NULL",
                "created_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
                "updated_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"
            },
            "version": 1
        },
        "v2": {
            "columns": {
                "id": "UUID PRIMARY KEY",
                "submission_id": "VARCHAR(10) NOT NULL UNIQUE",
                "reddit_title": "VARCHAR(300) NOT NULL",
                "reddit_url": "VARCHAR(500) NOT NULL",
                "subreddit": "VARCHAR(100) NOT NULL",
                "reddit_author": "VARCHAR(100)",
                "reddit_upvotes": "INTEGER NOT NULL DEFAULT 0",
                "reddit_comments_count": "INTEGER NOT NULL DEFAULT 0",
                "reddit_created_at": "TIMESTAMP NOT NULL",
                "app_title": "VARCHAR(200) NOT NULL",
                "app_concept": "TEXT NOT NULL",     # New field
                "problem_statement": "TEXT NOT NULL",  # New field
                "target_audience": "TEXT NOT NULL",    # New field
                "core_functions": "JSON NOT NULL",    # New field
                "app_description": "TEXT",             # Legacy field
                "app_features": "JSON",               # Legacy field
                "final_score": "FLOAT NOT NULL",
                "confidence_score": "FLOAT NOT NULL",  # New field
                "trust_level": "VARCHAR(10) NOT NULL", # New field
                "created_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
                "updated_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
                "schema_version": "INTEGER NOT NULL DEFAULT 2"  # New field
            },
            "version": 2
        }
    }


# =============================================================================
# Test Helper Utilities
# =============================================================================

@pytest.fixture
def test_temp_directory():
    """Temporary directory for test file operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def test_database_url(test_temp_directory):
    """Test database URL for testing."""
    return f"sqlite:///{test_temp_directory}/test.db"


@pytest.fixture
def test_configuration():
    """Test configuration for OnlyMaps integration."""
    return {
        "onlymaps": {
            "enabled": True,
            "batch_size": 100,
            "timeout": 30,
            "retry_attempts": 3,
            "fallback_to_sqlalchemy": True,
            "schema_validation": True,
            "performance_monitoring": True
        },
        "database": {
            "url": "sqlite:///test.db",
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }


# =============================================================================
# Async Test Support
# =============================================================================

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_test_database():
    """Async test database fixture."""
    # This would set up an async database connection for testing
    mock_db = AsyncMock()
    mock_db.connect = AsyncMock(return_value=True)
    mock_db.disconnect = AsyncMock(return_value=True)
    mock_db.execute = AsyncMock(return_value=None)
    mock_db.fetch_all = AsyncMock(return_value=[])
    mock_db.fetch_one = AsyncMock(return_value=None)

    yield mock_db

    # Cleanup
    await mock_db.disconnect()


# =============================================================================
# Data Quality Test Fixtures
# =============================================================================

@pytest.fixture
def data_quality_test_cases():
    """Test cases for data quality validation."""
    return {
        "valid_data": {
            "submission_id": "valid123",
            "reddit_title": "Valid App Idea",
            "reddit_url": "https://reddit.com/r/test/valid123",
            "subreddit": "test",
            "app_title": "Valid App",
            "final_score": 75.0,
            "trust_level": "HIGH"
        },
        "invalid_submission_id": {
            "submission_id": "invalid",  # Too short
            "reddit_title": "Invalid App Idea",
            "reddit_url": "https://reddit.com/r/test/invalid",
            "subreddit": "test",
            "app_title": "Invalid App",
            "final_score": 75.0,
            "trust_level": "HIGH"
        },
        "invalid_trust_level": {
            "submission_id": "test123",
            "reddit_title": "Invalid Trust Level",
            "reddit_url": "https://reddit.com/r/test/test123",
            "subreddit": "test",
            "app_title": "Invalid App",
            "final_score": 75.0,
            "trust_level": "INVALID"  # Invalid trust level
        },
        "missing_required_fields": {
            # Missing submission_id, reddit_title, etc.
            "app_title": "Incomplete App",
            "final_score": 50.0
        }
    }


# =============================================================================
# Integration Test Fixtures
# =============================================================================

@pytest.fixture
def integration_test_pipeline():
    """Integration test pipeline fixture."""
    return {
        "extract": Mock(),
        "analyze": Mock(),
        "load": Mock(),
        "validate": Mock(),
        "monitor": Mock()
    }


# Alias for backward compatibility
@pytest.fixture
def sample_opportunity_data(sample_opportunities):
    """Alias for sample_opportunities for backward compatibility."""
    return sample_opportunities


@pytest.fixture
def legacy_interface_examples():
    """Legacy interface examples for backward compatibility testing."""
    return [
        {
            "type": "legacy_onlymaps_v1",
            "connect_method": "direct_connect",
            "query_method": "execute_query"
        },
        {
            "type": "legacy_onlymaps_v2",
            "connect_method": "with_connection",
            "query_method": "fetch_results"
        }
    ]


@pytest.fixture
def type_error_scenarios():
    """Type error scenarios for testing type safety."""
    return [
        {
            "name": "null_int_field",
            "data": {"score": None, "count": 10},
            "expected_error": "TypeError"
        },
        {
            "name": "invalid_enum_value",
            "data": {"trust_level": "INVALID_TRUST_LEVEL"},
            "expected_error": "ValidationError"
        },
        {
            "name": "missing_required_field",
            "data": {"title": "Test"},
            "expected_error": "ValidationError"
        },
        {
            "name": "invalid_json_field",
            "data": {"core_functions": "invalid_json"},
            "expected_error": "ValueError"
        }
    ]


@pytest.fixture
def validation_error_scenarios():
    """Validation error scenarios for testing validation."""
    return [
        {
            "name": "invalid_trust_level",
            "data": {"trust_level": "INVALID_LEVEL"},
            "expected_error": "ValidationError"
        },
        {
            "name": "invalid_score_range",
            "data": {"final_score": 150.0},
            "expected_error": "ValidationError"
        },
        {
            "name": "negative_score",
            "data": {"final_score": -10.0},
            "expected_error": "ValidationError"
        },
        {
            "name": "invalid_market_demand",
            "data": {"market_demand": -5.0},
            "expected_error": "ValidationError"
        }
    ]


@pytest.fixture
def migration_test_data():
    """Migration test data for backward compatibility testing."""
    return {
        "v1_to_v2": {
            "old_interface": {
                "connect": "direct_connect",
                "query": "execute_query",
                "map_results": "raw_to_object"
            },
            "new_interface": {
                "connect": "connect",
                "query": "fetch_one_or_none",
                "map_results": "map_to_model"
            },
            "migration_path": "adapter_pattern"
        },
        "v2_to_v3": {
            "old_interface": {
                "connection": "OnlyMapsConnection",
                "config": "OnlyMapsConfig",
                "mapper": "OnlyMapsMapper"
            },
            "new_interface": {
                "connection": "OnlyMapsConnection",
                "config": "OnlyMapsConfig",
                "mapper": "OnlyMapsMapper"
            },
            "migration_path": "direct_compatible"
        }
    }


@pytest.fixture
def mock_external_services():
    """Mock external services for integration testing."""
    return {
        "reddit_api": Mock(),
        "supabase_client": Mock(),
        "validation_service": Mock(),
        "monitoring_service": Mock(),
        "notification_service": Mock()
    }


# Cleanup function
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Auto-cleanup fixture for test data."""
    yield
    # Add any cleanup logic here if needed
    pass


# Markers for test organization
pytest.mark.onlymaps = pytest.mark.marker("onlymaps")
pytest.mark.schema_flexibility = pytest.mark.marker("schema_flexibility")
pytest.mark.performance = pytest.mark.marker("performance")
pytest.mark.type_safety = pytest.mark.marker("type_safety")
pytest.mark.async_patterns = pytest.mark.marker("async_patterns")
pytest.mark.compatibility = pytest.mark.marker("compatibility")
pytest.mark.integration = pytest.mark.marker("integration")
