"""
Trust Validation System - Package Initialization

This package provides a comprehensive, decoupled trust validation system
for RedditHarbor opportunities. It implements the Service Layer Pattern,
Repository Pattern, and Observer Pattern to enable safe schema consolidation.

Key Components:
- TrustValidationService: Main business logic for trust validation
- TrustRepository: Abstract data access layer with multiple table support
- TrustIndicators: Type-safe data models with validation
- TrustConfig: Centralized constants and configuration

Usage:
    from core.trust import TrustValidationService, TrustRepositoryFactory
    from core.trust.models import TrustValidationRequest, TrustIndicators
    from core.trust.config import TrustLevel, TrustBadge

    # Create service
    repository = TrustRepositoryFactory.create_repository(supabase_client)
    service = TrustValidationService(repository)

    # Validate opportunity
    request = TrustValidationRequest(
        submission_id="abc123",
        subreddit="productivity",
        upvotes=150,
        comments_count=25,
        created_utc=1700000000,
        text="I need help with task management..."
    )

    result = service.validate_opportunity_trust(request)
    indicators = result.indicators

    print(f"Trust Level: {indicators.trust_level}")
    print(f"Trust Score: {indicators.trust_score}")
    print(f"Trust Badges: {indicators.trust_badges}")
"""

from core.trust.config import (
    ALL_TRUST_COLUMNS,
    CORE_TRUST_COLUMNS,
    ENGAGEMENT_COLUMNS,
    METADATA_COLUMNS,
    QUALITY_COLUMNS,
    AIConfidenceLevel,
    DiscussionQuality,
    EngagementLevel,
    ProblemValidity,
    TrustBadge,
    TrustColumns,
    TrustLevel,
    TrustTables,
    TrustValidationConfig,
    TrustWeights,
)
from core.trust.models import (
    TrustBadgeConfigModel,
    TrustColumnMap,
    TrustData,
    TrustIndicators,
    TrustScoreWeights,
    TrustTableMapping,
    TrustValidationRequest,
    TrustValidationResult,
)
from core.trust.repository import (
    MultiTableTrustRepository,
    StagingTrustRepository,
    SupabaseTrustRepository,
    TrustRepositoryFactory,
    TrustRepositoryInterface,
    repository_error_handler,
)
from core.trust.validation import TrustValidationService

__version__ = "1.0.0"
__author__ = "RedditHarbor Development Team"

# Export main classes for easy access
__all__ = [
    # Configuration
    "TrustTables",
    "TrustColumns",
    "TrustLevel",
    "TrustBadge",
    "EngagementLevel",
    "ProblemValidity",
    "DiscussionQuality",
    "AIConfidenceLevel",
    "TrustWeights",
    "TrustValidationConfig",
    "CORE_TRUST_COLUMNS",
    "ENGAGEMENT_COLUMNS",
    "QUALITY_COLUMNS",
    "METADATA_COLUMNS",
    "ALL_TRUST_COLUMNS",

    # Models
    "TrustIndicators",
    "TrustValidationRequest",
    "TrustValidationResult",
    "TrustScoreWeights",
    "TrustBadgeConfigModel",
    "TrustData",
    "TrustColumnMap",
    "TrustTableMapping",

    # Repository
    "TrustRepositoryInterface",
    "SupabaseTrustRepository",
    "StagingTrustRepository",
    "TrustRepositoryFactory",
    "MultiTableTrustRepository",
    "repository_error_handler",

    # Service
    "TrustValidationService"
]


# Package metadata
class TrustValidationSystemInfo:
    """Information about the trust validation system."""

    NAME = "RedditHarbor Trust Validation System"
    VERSION = __version__
    DESCRIPTION = "Comprehensive trust validation for opportunity discovery"
    AUTHOR = __author__

    # Feature flags
    SUPPORTS_BATCH_VALIDATION = True
    SUPPORTS_MULTI_TABLE_REPOSITORY = True
    SUPPORTS_CUSTOM_WEIGHTS = True
    SUPPORTS_AUDIT_TRAIL = True
    SUPPORTS_CACHING = False  # Future enhancement

    # Configuration
    DEFAULT_ACTIVITY_THRESHOLD = TrustValidationConfig.DEFAULT_ACTIVITY_THRESHOLD
    DEFAULT_WEIGHTS = TrustWeights.DEFAULT_WEIGHTS
    MAX_CORE_FUNCTIONS = TrustValidationConfig.MAX_CORE_FUNCTIONS

    @classmethod
    def get_system_info(cls) -> dict:
        """Get comprehensive system information."""
        return {
            "name": cls.NAME,
            "version": cls.VERSION,
            "description": cls.DESCRIPTION,
            "author": cls.AUTHOR,
            "features": {
                "supports_batch_validation": cls.SUPPORTS_BATCH_VALIDATION,
                "supports_multi_table_repository": cls.SUPPORTS_MULTI_TABLE_REPOSITORY,
                "supports_custom_weights": cls.SUPPORTS_CUSTOM_WEIGHTS,
                "supports_audit_trail": cls.SUPPORTS_AUDIT_TRAIL,
                "supports_caching": cls.SUPPORTS_CACHING
            },
            "configuration": {
                "default_activity_threshold": cls.DEFAULT_ACTIVITY_THRESHOLD,
                "default_weights": cls.DEFAULT_WEIGHTS,
                "max_core_functions": cls.MAX_CORE_FUNCTIONS
            },
            "supported_tables": [
                TrustTables.APP_OPPORTUNITIES,
                TrustTables.SUBMISSIONS,
                TrustTables.PUBLIC_STAGING_APP_OPPORTUNITIES
            ],
            "trust_levels": [level.value for level in TrustLevel],
            "trust_badges": [badge.value for badge in TrustBadge]
        }


# Convenience factory functions
def create_trust_service(supabase_client, **kwargs) -> TrustValidationService:
    """
    Create a fully configured trust validation service.

    Args:
        supabase_client: Supabase client instance
        **kwargs: Additional configuration options

    Returns:
        Configured TrustValidationService instance
    """
    repository = TrustRepositoryFactory.create_repository(supabase_client)
    return TrustValidationService(repository, **kwargs)


def create_multi_table_trust_service(supabase_client, **kwargs) -> TrustValidationService:
    """
    Create a trust validation service with multi-table repository support.

    Args:
        supabase_client: Supabase client instance
        **kwargs: Additional configuration options

    Returns:
        TrustValidationService with MultiTableTrustRepository
    """
    repository = TrustRepositoryFactory.create_multi_table_repository(supabase_client)
    return TrustValidationService(repository, **kwargs)


def validate_trust_compatibility() -> dict:
    """
    Validate trust validation system compatibility.

    Returns:
        Dictionary with compatibility check results
    """
    try:
        # Test imports
        from core.trust.models import TrustIndicators
        from core.trust.repository import TrustRepositoryInterface
        from core.trust.validation import TrustValidationService

        # Test basic functionality
        indicators = TrustIndicators()
        assert hasattr(indicators, 'trust_score')
        assert hasattr(indicators, 'trust_level')

        return {
            "compatible": True,
            "version": __version__,
            "tests_passed": [
                "model_imports",
                "repository_imports",
                "service_imports",
                "basic_model_creation"
            ],
            "errors": []
        }

    except Exception as e:
        return {
            "compatible": False,
            "version": __version__,
            "tests_passed": [],
            "errors": [str(e)]
        }


# Package-level logging setup
import logging

# Create logger for trust validation system
logger = logging.getLogger(__name__)

# Set default level if not configured
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Log package initialization
logger.info(f"Trust Validation System v{__version__} initialized")
logger.debug(f"Available components: {len(__all__)}")
