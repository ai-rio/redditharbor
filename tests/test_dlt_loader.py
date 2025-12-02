"""Tests for DLTLoader unified loading infrastructure.

This test suite ensures comprehensive coverage of the DLTLoader module,
testing initialization, loading operations, statistics tracking, and error handling.

Note: These tests use real DLT and database connections for integration testing.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from typing import List, Dict, Any

from core.storage.dlt_loader import DLTLoader, LoadStatistics


# ===========================
# Fixtures - Test Data
# ===========================


@pytest.fixture
def sample_opportunities():
    """Sample opportunity data for testing."""
    return [
        {
            "submission_id": "test001",
            "title": "Need better project management tool",
            "problem_description": "Current tools too complex",
            "app_concept": "Simple PM platform",
            "core_functions": ["Task tracking", "Team collaboration"],
            "final_score": 78.5,
        },
        {
            "submission_id": "test002",
            "title": "Looking for budget tracking app",
            "problem_description": "Existing apps lack automation",
            "app_concept": "Smart budget tracker",
            "core_functions": ["Expense tracking", "Budget alerts"],
            "final_score": 72.0,
        },
        {
            "submission_id": "test003",
            "title": "Need fitness tracking solution",
            "problem_description": "Current apps don't sync devices",
            "app_concept": "Universal fitness hub",
            "core_functions": ["Device sync", "Progress tracking"],
            "final_score": 65.3,
        },
    ]


@pytest.fixture
def sample_submissions():
    """Sample Reddit submissions for testing."""
    return [
        {
            "submission_id": "sub001",
            "title": "Test submission 1",
            "subreddit": "startups",
            "upvotes": 150,
            "created_utc": 1700000000,
        },
        {
            "submission_id": "sub002",
            "title": "Test submission 2",
            "subreddit": "SaaS",
            "upvotes": 200,
            "created_utc": 1700000100,
        },
    ]


# ===========================
# Initialization Tests
# ===========================


def test_init_with_defaults():
    """Test DLTLoader initialization with default configuration."""
    loader = DLTLoader()

    assert loader.destination == "postgres"
    assert loader.dataset_name == "public"
    assert loader.connection_string == "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
    assert isinstance(loader.stats, LoadStatistics)
    assert loader.stats.loaded == 0
    assert loader.stats.failed == 0
    assert len(loader._pipeline_cache) == 0


def test_init_with_custom_destination():
    """Test initialization with custom destination."""
    loader = DLTLoader(destination="duckdb", dataset_name="test_dataset")

    assert loader.destination == "duckdb"
    assert loader.dataset_name == "test_dataset"


def test_init_with_custom_connection_string():
    """Test initialization with custom connection string."""
    custom_conn = "postgresql://user:pass@localhost:5432/testdb"
    loader = DLTLoader(connection_string=custom_conn)

    assert loader.connection_string == custom_conn


def test_stats_initialized_to_zero():
    """Test that statistics are initialized to zero."""
    loader = DLTLoader()

    assert loader.stats.loaded == 0
    assert loader.stats.failed == 0
    assert loader.stats.skipped == 0
    assert loader.stats.total_attempted == 0
    assert len(loader.stats.errors) == 0


# ===========================
# LoadStatistics Tests
# ===========================


def test_load_statistics_add_success():
    """Test LoadStatistics success tracking."""
    stats = LoadStatistics()

    stats.add_success(5)

    assert stats.loaded == 5
    assert stats.total_attempted == 5
    assert stats.failed == 0


def test_load_statistics_add_failure():
    """Test LoadStatistics failure tracking."""
    stats = LoadStatistics()

    stats.add_failure(3, error="Test error")

    assert stats.failed == 3
    assert stats.total_attempted == 3
    assert stats.loaded == 0
    assert len(stats.errors) == 1
    assert stats.errors[0] == "Test error"


def test_load_statistics_add_skip():
    """Test LoadStatistics skip tracking."""
    stats = LoadStatistics()

    stats.add_skip(2)

    assert stats.skipped == 2
    assert stats.total_attempted == 0  # Skips don't count as attempted


def test_load_statistics_get_summary():
    """Test LoadStatistics summary generation."""
    stats = LoadStatistics()

    stats.add_success(10)
    stats.add_failure(2)
    stats.add_skip(5)

    summary = stats.get_summary()

    assert summary["loaded"] == 10
    assert summary["failed"] == 2
    assert summary["skipped"] == 5
    assert summary["total_attempted"] == 12
    assert summary["success_rate"] == 10 / 12
    assert summary["error_count"] == 0


def test_load_statistics_success_rate_zero_attempts():
    """Test success rate calculation with zero attempts."""
    stats = LoadStatistics()

    summary = stats.get_summary()

    assert summary["success_rate"] == 0.0


def test_load_statistics_reset():
    """Test LoadStatistics reset functionality."""
    stats = LoadStatistics()

    stats.add_success(5)
    stats.add_failure(2, error="Error")
    stats.reset()

    assert stats.loaded == 0
    assert stats.failed == 0
    assert stats.skipped == 0
    assert stats.total_attempted == 0
    assert len(stats.errors) == 0


# ===========================
# load() Method Tests
# ===========================


@patch("core.storage.dlt_loader.dlt.pipeline")
def test_load_basic_success(mock_pipeline_func, sample_opportunities):
    """Test basic load operation success."""
    # Mock pipeline
    mock_pipeline = MagicMock()
    mock_load_info = MagicMock()
    mock_load_info.started_at = "2025-01-15T10:00:00"
    mock_pipeline.run.return_value = mock_load_info
    mock_pipeline_func.return_value = mock_pipeline

    loader = DLTLoader()
    success = loader.load(
        data=sample_opportunities,
        table_name="app_opportunities",
        write_disposition="merge",
        primary_key="submission_id",
    )

    assert success is True
    assert loader.stats.loaded == 3
    assert loader.stats.failed == 0
    mock_pipeline.run.assert_called_once()


@patch("core.storage.dlt_loader.dlt.pipeline")
def test_load_with_merge_disposition(mock_pipeline_func, sample_opportunities):
    """Test load with merge disposition."""
    mock_pipeline = MagicMock()
    mock_pipeline.run.return_value = MagicMock(started_at="2025-01-15")
    mock_pipeline_func.return_value = mock_pipeline

    loader = DLTLoader()
    success = loader.load(
        data=sample_opportunities,
        table_name="test_table",
        write_disposition="merge",
        primary_key="submission_id",
    )

    assert success is True
    # Verify merge disposition was passed
    call_args = mock_pipeline.run.call_args
    assert call_args[1]["write_disposition"] == "merge"
    assert call_args[1]["primary_key"] == "submission_id"


@patch("core.storage.dlt_loader.dlt.pipeline")
def test_load_with_replace_disposition(mock_pipeline_func, sample_submissions):
    """Test load with replace disposition."""
    mock_pipeline = MagicMock()
    mock_pipeline.run.return_value = MagicMock(started_at="2025-01-15")
    mock_pipeline_func.return_value = mock_pipeline

    loader = DLTLoader()
    success = loader.load(
        data=sample_submissions,
        table_name="submissions",
        write_disposition="replace",
    )

    assert success is True
    call_args = mock_pipeline.run.call_args
    assert call_args[1]["write_disposition"] == "replace"


@patch("core.storage.dlt_loader.dlt.pipeline")
def test_load_with_append_disposition(mock_pipeline_func, sample_submissions):
    """Test load with append disposition."""
    mock_pipeline = MagicMock()
    mock_pipeline.run.return_value = MagicMock(started_at="2025-01-15")
    mock_pipeline_func.return_value = mock_pipeline

    loader = DLTLoader()
    success = loader.load(
        data=sample_submissions,
        table_name="submissions",
        write_disposition="append",
    )

    assert success is True
    call_args = mock_pipeline.run.call_args
    assert call_args[1]["write_disposition"] == "append"


def test_load_with_empty_data():
    """Test load with empty data list."""
    loader = DLTLoader()
    success = loader.load(
        data=[],
        table_name="test_table",
        write_disposition="merge",
        primary_key="id",
    )

    assert success is False
    assert loader.stats.loaded == 0


def test_load_merge_without_primary_key(sample_opportunities):
    """Test load with merge disposition but no primary key raises error."""
    loader = DLTLoader()

    with pytest.raises(ValueError, match="primary_key required for merge"):
        loader.load(
            data=sample_opportunities,
            table_name="test_table",
            write_disposition="merge",
        )


@patch("core.storage.dlt_loader.dlt.pipeline")
def test_load_with_dlt_error(mock_pipeline_func, sample_opportunities):
    """Test load handling DLT errors gracefully."""
    mock_pipeline = MagicMock()
    mock_pipeline.run.side_effect = Exception("DLT connection error")
    mock_pipeline_func.return_value = mock_pipeline

    loader = DLTLoader()
    success = loader.load(
        data=sample_opportunities,
        table_name="test_table",
        write_disposition="merge",
        primary_key="submission_id",
    )

    assert success is False
    assert loader.stats.failed == 3
    assert loader.stats.loaded == 0
    assert len(loader.stats.errors) == 1
    assert "DLT connection error" in loader.stats.errors[0]


@patch("core.storage.dlt_loader.dlt.pipeline")
def test_load_updates_statistics_correctly(mock_pipeline_func, sample_opportunities):
    """Test that load updates statistics correctly."""
    mock_pipeline = MagicMock()
    mock_pipeline.run.return_value = MagicMock(started_at="2025-01-15")
    mock_pipeline_func.return_value = mock_pipeline

    loader = DLTLoader()

    # First load
    loader.load(sample_opportunities, "table1", "merge", "submission_id")
    assert loader.stats.loaded == 3

    # Second load
    loader.load(sample_opportunities[:2], "table2", "merge", "submission_id")
    assert loader.stats.loaded == 5
    assert loader.stats.total_attempted == 5


# ===========================
# load_batch() Tests
# ===========================


@patch("core.storage.dlt_loader.dlt.pipeline")
def test_load_batch_success(mock_pipeline_func, sample_opportunities):
    """Test batch loading with default batch size."""
    mock_pipeline = MagicMock()
    mock_pipeline.run.return_value = MagicMock(started_at="2025-01-15")
    mock_pipeline_func.return_value = mock_pipeline

    loader = DLTLoader()
    results = loader.load_batch(
        data=sample_opportunities,
        table_name="test_table",
        primary_key="submission_id",
        batch_size=2,
    )

    assert results["total_records"] == 3
    assert results["batches"] == 2  # 3 records / batch_size 2 = 2 batches
    assert results["successful_batches"] == 2
    assert results["failed_batches"] == 0
    assert results["success_rate"] == 1.0


@patch("core.storage.dlt_loader.dlt.pipeline")
def test_load_batch_with_failures(mock_pipeline_func, sample_opportunities):
    """Test batch loading with some failures."""
    mock_pipeline = MagicMock()
    # First batch succeeds, second fails
    mock_pipeline.run.side_effect = [
        MagicMock(started_at="2025-01-15"),
        Exception("Batch 2 failed"),
    ]
    mock_pipeline_func.return_value = mock_pipeline

    loader = DLTLoader()
    results = loader.load_batch(
        data=sample_opportunities,
        table_name="test_table",
        primary_key="submission_id",
        batch_size=2,
    )

    assert results["successful_batches"] == 1
    assert results["failed_batches"] == 1
    assert results["success_rate"] == 0.5


def test_load_batch_with_empty_data():
    """Test batch loading with empty data."""
    loader = DLTLoader()
    results = loader.load_batch(
        data=[],
        table_name="test_table",
        primary_key="id",
        batch_size=10,
    )

    assert results["total_records"] == 0
    assert results["batches"] == 0
    assert results["success_rate"] == 0.0


@patch("core.storage.dlt_loader.dlt.pipeline")
def test_load_batch_small_batch_size(mock_pipeline_func, sample_opportunities):
    """Test batch loading with batch size of 1."""
    mock_pipeline = MagicMock()
    mock_pipeline.run.return_value = MagicMock(started_at="2025-01-15")
    mock_pipeline_func.return_value = mock_pipeline

    loader = DLTLoader()
    results = loader.load_batch(
        data=sample_opportunities,
        table_name="test_table",
        primary_key="submission_id",
        batch_size=1,
    )

    assert results["batches"] == 3  # 3 records, batch_size 1 = 3 batches
    assert mock_pipeline.run.call_count == 3


# ===========================
# Pipeline Caching Tests
# ===========================


@patch("core.storage.dlt_loader.dlt.pipeline")
def test_pipeline_caching(mock_pipeline_func, sample_opportunities):
    """Test that pipelines are cached and reused."""
    mock_pipeline = MagicMock()
    mock_pipeline.run.return_value = MagicMock(started_at="2025-01-15")
    mock_pipeline_func.return_value = mock_pipeline

    loader = DLTLoader()

    # First load
    loader.load(sample_opportunities, "table1", "merge", "submission_id")

    # Second load with same table (should reuse pipeline)
    loader.load(sample_opportunities, "table1", "merge", "submission_id")

    # Pipeline should be created only once
    assert mock_pipeline_func.call_count == 1


@patch("core.storage.dlt_loader.dlt.pipeline")
def test_pipeline_cache_different_tables(mock_pipeline_func, sample_opportunities):
    """Test that different tables get different pipelines."""
    mock_pipeline = MagicMock()
    mock_pipeline.run.return_value = MagicMock(started_at="2025-01-15")
    mock_pipeline_func.return_value = mock_pipeline

    loader = DLTLoader()

    loader.load(sample_opportunities, "table1", "merge", "submission_id")
    loader.load(sample_opportunities, "table2", "merge", "submission_id")

    # Two different pipelines should be created
    assert mock_pipeline_func.call_count == 2


def test_clear_pipeline_cache():
    """Test clearing pipeline cache."""
    loader = DLTLoader()

    # Add to cache manually
    loader._pipeline_cache["test_pipeline"] = MagicMock()
    assert len(loader._pipeline_cache) == 1

    loader.clear_pipeline_cache()

    assert len(loader._pipeline_cache) == 0


# ===========================
# Statistics Methods Tests
# ===========================


@patch("core.storage.dlt_loader.dlt.pipeline")
def test_get_statistics(mock_pipeline_func, sample_opportunities):
    """Test get_statistics returns correct data."""
    mock_pipeline = MagicMock()
    mock_pipeline.run.return_value = MagicMock(started_at="2025-01-15")
    mock_pipeline_func.return_value = mock_pipeline

    loader = DLTLoader()

    loader.load(sample_opportunities, "test_table", "merge", "submission_id")

    stats = loader.get_statistics()

    assert stats["loaded"] == 3
    assert stats["failed"] == 0
    assert stats["total_attempted"] == 3
    assert stats["success_rate"] == 1.0


def test_reset_statistics():
    """Test reset_statistics clears counters."""
    loader = DLTLoader()

    # Manually set some stats
    loader.stats.loaded = 10
    loader.stats.failed = 2
    loader.stats.errors.append("Test error")

    loader.reset_statistics()

    assert loader.stats.loaded == 0
    assert loader.stats.failed == 0
    assert loader.stats.skipped == 0
    assert len(loader.stats.errors) == 0


# ===========================
# Integration Tests
# ===========================


@patch("core.storage.dlt_loader.dlt.pipeline")
def test_full_workflow_merge_disposition(mock_pipeline_func, sample_opportunities):
    """Test complete workflow with merge disposition."""
    mock_pipeline = MagicMock()
    mock_pipeline.run.return_value = MagicMock(started_at="2025-01-15")
    mock_pipeline_func.return_value = mock_pipeline

    loader = DLTLoader(dataset_name="test_dataset")

    # Load initial data
    success1 = loader.load(
        data=sample_opportunities,
        table_name="opportunities",
        write_disposition="merge",
        primary_key="submission_id",
    )

    # Load duplicate (should merge)
    success2 = loader.load(
        data=sample_opportunities[:1],  # First record again
        table_name="opportunities",
        write_disposition="merge",
        primary_key="submission_id",
    )

    assert success1 is True
    assert success2 is True
    assert loader.stats.loaded == 4  # 3 + 1
    assert loader.stats.failed == 0


@patch("core.storage.dlt_loader.dlt.pipeline")
def test_multiple_table_loads(mock_pipeline_func, sample_opportunities, sample_submissions):
    """Test loading to multiple tables."""
    mock_pipeline = MagicMock()
    mock_pipeline.run.return_value = MagicMock(started_at="2025-01-15")
    mock_pipeline_func.return_value = mock_pipeline

    loader = DLTLoader()

    # Load to first table
    loader.load(sample_opportunities, "opportunities", "merge", "submission_id")

    # Load to second table
    loader.load(sample_submissions, "submissions", "merge", "submission_id")

    assert loader.stats.loaded == 5  # 3 + 2
    assert len(loader._pipeline_cache) == 2


# ===========================
# Edge Cases
# ===========================


def test_load_with_single_record():
    """Test loading a single record."""
    loader = DLTLoader()
    data = [{"id": "test1", "value": "data"}]

    # Mock pipeline
    with patch("core.storage.dlt_loader.dlt.pipeline") as mock_pipeline_func:
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = MagicMock(started_at="2025-01-15")
        mock_pipeline_func.return_value = mock_pipeline

        success = loader.load(data, "test_table", "merge", "id")

        assert success is True
        assert loader.stats.loaded == 1


@patch("core.storage.dlt_loader.dlt.pipeline")
def test_load_with_large_dataset(mock_pipeline_func):
    """Test loading large dataset."""
    mock_pipeline = MagicMock()
    mock_pipeline.run.return_value = MagicMock(started_at="2025-01-15")
    mock_pipeline_func.return_value = mock_pipeline

    loader = DLTLoader()
    large_data = [{"id": f"test{i}", "value": f"data{i}"} for i in range(1000)]

    success = loader.load(large_data, "large_table", "merge", "id")

    assert success is True
    assert loader.stats.loaded == 1000


@patch("core.storage.dlt_loader.dlt.pipeline")
def test_load_with_custom_pipeline_name(mock_pipeline_func, sample_opportunities):
    """Test load with custom pipeline name."""
    mock_pipeline = MagicMock()
    mock_pipeline.run.return_value = MagicMock(started_at="2025-01-15")
    mock_pipeline_func.return_value = mock_pipeline

    loader = DLTLoader()
    success = loader.load(
        data=sample_opportunities,
        table_name="test_table",
        write_disposition="merge",
        primary_key="submission_id",
        pipeline_name="custom_pipeline_name",
    )

    assert success is True
    # Verify custom pipeline name was used
    mock_pipeline_func.assert_called_once()
    assert "custom_pipeline_name" in loader._pipeline_cache


# ===========================
# JSONB Column Type Hints Tests
# ===========================


def test_create_resource_with_columns():
    """Test creating a DLT resource with explicit column type hints."""
    loader = DLTLoader()

    # Sample JSONB column configuration (from the working implementation)
    columns = {
        "submission_id": {"data_type": "text", "nullable": False},
        "problem_description": {"data_type": "text"},
        "ai_profile": {"data_type": "json"},
        "core_problems": {"data_type": "json"},
        "dimension_scores": {"data_type": "json"},
        "trust_badges": {"data_type": "json"},
    }

    data = [{"submission_id": "test001", "ai_profile": {"test": "data"}}]

    # Create resource with column hints
    resource = loader._create_resource_with_columns(
        data=data,
        table_name="app_opportunities",
        columns=columns,
        write_disposition="merge",
        primary_key="submission_id"
    )

    # Verify resource is callable
    assert callable(resource)

    # Verify resource yields correct data
    records = list(resource())
    assert len(records) == 1
    assert records[0]["submission_id"] == "test001"
    assert records[0]["ai_profile"]["test"] == "data"


@patch("core.storage.dlt_loader.dlt.pipeline")
def test_load_with_jsonb_columns(mock_pipeline_func, sample_opportunities):
    """Test load operation with JSONB column type hints."""
    mock_pipeline = MagicMock()
    mock_pipeline.run.return_value = MagicMock(started_at="2025-01-15T10:00:00")
    mock_pipeline_func.return_value = mock_pipeline

    loader = DLTLoader()

    # JSONB column type hints configuration
    columns = {
        "submission_id": {"data_type": "text", "nullable": False},
        "problem_description": {"data_type": "text"},
        "ai_profile": {"data_type": "json"},
        "core_problems": {"data_type": "json"},
        "dimension_scores": {"data_type": "json"},
        "trust_badges": {"data_type": "json"},
    }

    # Add JSON fields to test data
    test_data = sample_opportunities.copy()
    for record in test_data:
        record.update({
            "ai_profile": {"analysis": "test profile"},
            "core_problems": ["problem1", "problem2"],
            "dimension_scores": {"market": 0.8, "technical": 0.7},
            "trust_badges": {"verified": True, "score": 85}
        })

    success = loader.load(
        data=test_data,
        table_name="app_opportunities",
        write_disposition="merge",
        primary_key="submission_id",
        columns=columns,  # CRITICAL: JSONB type hints
    )

    assert success is True
    assert loader.stats.loaded == 3
    assert loader.stats.failed == 0

    # Verify pipeline was called with a resource (not raw data)
    mock_pipeline.run.assert_called_once()
    call_args = mock_pipeline.run.call_args
    # First argument should be a resource (callable), not data directly
    resource_arg = call_args[0][0]
    assert callable(resource_arg), "Should be called with a DLT resource, not raw data"


@patch("core.storage.dlt_loader.dlt.pipeline")
def test_load_without_columns_fallback(mock_pipeline_func, sample_opportunities):
    """Test that load without columns falls back to raw data loading."""
    mock_pipeline = MagicMock()
    mock_pipeline.run.return_value = MagicMock(started_at="2025-01-15")
    mock_pipeline_func.return_value = mock_pipeline

    loader = DLTLoader()
    success = loader.load(
        data=sample_opportunities,
        table_name="app_opportunities",
        write_disposition="merge",
        primary_key="submission_id",
        columns=None,  # No column hints - should use fallback
    )

    assert success is True
    assert loader.stats.loaded == 3

    # Verify pipeline was called with raw data (not a resource)
    mock_pipeline.run.assert_called_once()
    call_args = mock_pipeline.run.call_args
    # First argument should be raw data, not a resource
    data_arg = call_args[0][0]
    assert data_arg == sample_opportunities
    assert not callable(data_arg), "Should be raw data, not a resource"


@patch("core.storage.dlt_loader.dlt.pipeline")
def test_load_with_empty_columns_fallback(mock_pipeline_func, sample_opportunities):
    """Test that empty columns dict falls back to raw data loading."""
    mock_pipeline = MagicMock()
    mock_pipeline.run.return_value = MagicMock(started_at="2025-01-15")
    mock_pipeline_func.return_value = mock_pipeline

    loader = DLTLoader()
    success = loader.load(
        data=sample_opportunities,
        table_name="app_opportunities",
        write_disposition="merge",
        primary_key="submission_id",
        columns={},  # Empty columns - should use fallback
    )

    assert success is True
    assert loader.stats.loaded == 3

    # Verify pipeline was called with raw data
    mock_pipeline.run.assert_called_once()
    call_args = mock_pipeline.run.call_args
    data_arg = call_args[0][0]
    assert data_arg == sample_opportunities
