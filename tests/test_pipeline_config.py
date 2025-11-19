"""Tests for PipelineConfig."""
from core.pipeline.config import DataSource, PipelineConfig, ServiceType


def test_pipeline_config_defaults():
    """Test default configuration values."""
    config = PipelineConfig()

    assert config.data_source == DataSource.DATABASE
    assert config.limit == 100
    assert config.enable_profiler is True
    assert config.enable_deduplication is True
    assert config.parallel_processing is True
    assert config.batch_size == 10


def test_pipeline_config_custom():
    """Test custom configuration."""
    config = PipelineConfig(
        data_source=DataSource.REDDIT_API, limit=50, enable_monetization=False
    )

    assert config.data_source == DataSource.REDDIT_API
    assert config.limit == 50
    assert config.enable_monetization is False
    # Other fields should still have defaults
    assert config.enable_profiler is True


def test_data_source_enum():
    """Test DataSource enum values."""
    assert DataSource.DATABASE == "database"
    assert DataSource.REDDIT_API == "reddit"
    assert len(list(DataSource)) == 2


def test_service_types():
    """Test ServiceType enum."""
    assert ServiceType.PROFILER == "profiler"
    assert ServiceType.OPPORTUNITY == "opportunity"
    assert ServiceType.MONETIZATION == "monetization"
    assert ServiceType.TRUST == "trust"
    assert ServiceType.MARKET_VALIDATION == "market_validation"

    assert list(ServiceType) == [
        ServiceType.PROFILER,
        ServiceType.OPPORTUNITY,
        ServiceType.MONETIZATION,
        ServiceType.TRUST,
        ServiceType.MARKET_VALIDATION,
    ]


def test_pipeline_config_source_config_dict():
    """Test source_config dictionary field."""
    config = PipelineConfig()

    # Should default to empty dict
    assert config.source_config == {}

    # Should accept custom dict
    custom_config = PipelineConfig(source_config={"subreddit": "technology"})
    assert custom_config.source_config == {"subreddit": "technology"}


def test_pipeline_config_thresholds():
    """Test quality threshold configurations."""
    config = PipelineConfig()

    assert config.ai_profile_threshold == 40.0
    assert config.monetization_threshold == 60.0
    assert config.market_validation_threshold == 60.0
    assert config.deduplication_threshold == 0.8


def test_pipeline_config_performance_settings():
    """Test performance-related settings."""
    config = PipelineConfig()

    assert config.parallel_processing is True
    assert config.batch_size == 10
    assert config.max_workers == 4
