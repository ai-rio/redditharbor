"""Pipeline configuration management."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class DataSource(str, Enum):
    """Supported data sources."""

    DATABASE = "database"
    REDDIT_API = "reddit"


class ServiceType(str, Enum):
    """Available AI services."""

    PROFILER = "profiler"
    OPPORTUNITY = "opportunity"
    MONETIZATION = "monetization"
    TRUST = "trust"
    MARKET_VALIDATION = "market_validation"


@dataclass
class PipelineConfig:
    """Configuration for OpportunityPipeline."""

    # Data source configuration
    data_source: DataSource = DataSource.DATABASE
    limit: int = 100

    # Service toggles
    enable_profiler: bool = True
    enable_opportunity_scoring: bool = True
    enable_monetization: bool = True
    enable_trust: bool = True
    enable_market_validation: bool = False

    # Performance settings
    parallel_processing: bool = True
    batch_size: int = 10
    max_workers: int = 4

    # Deduplication settings
    enable_deduplication: bool = True
    deduplication_threshold: float = 0.8

    # Quality thresholds
    ai_profile_threshold: float = 40.0
    monetization_threshold: float = 60.0
    market_validation_threshold: float = 60.0

    # Quality filter settings
    enable_quality_filter: bool = False
    min_score: int = 10
    min_comments: int = 5
    min_text_length: int = 100

    # Data return settings
    return_data: bool = True
    dry_run: bool = False

    # Monetization configuration
    monetization_strategy: str = "rule_based"
    monetization_config: Dict[str, Any] = field(default_factory=dict)

    # Client connections (optional)
    supabase_client: Optional[Any] = None
    reddit_client: Optional[Any] = None

    # Additional kwargs for data source
    source_config: Dict[str, Any] = field(default_factory=dict)
