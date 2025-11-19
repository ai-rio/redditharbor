"""
Trust Validation System - Configuration Constants

This module provides centralized constants for trust validation system
to prevent hard-coded references and enable safe schema consolidation.

Usage:
    from core.trust.config import TrustTables, TrustColumns, TrustLevel

    # Use constants instead of hard-coded strings
    table.select(TrustColumns.TRUST_SCORE, TrustColumns.TRUST_BADGE)
"""

from enum import Enum


class TrustTables:
    """Database table names for trust validation."""
    SUBMISSIONS = "submissions"
    APP_OPPORTUNITIES = "app_opportunities"
    TRUST_VALIDATIONS = "trust_validations"
    WORKFLOW_RESULTS = "workflow_results"
    PUBLIC_STAGING_APP_OPPORTUNITIES = "public_staging.app_opportunities"


class TrustColumns:
    """Column names for trust validation data."""

    # Core trust indicators
    TRUST_SCORE = "trust_score"
    TRUST_BADGE = "trust_badge"
    TRUST_LEVEL = "trust_level"

    # Activity and engagement
    ACTIVITY_SCORE = "activity_score"
    ENGAGEMENT_LEVEL = "engagement_level"
    TREND_VELOCITY = "trend_velocity"

    # Quality indicators
    PROBLEM_VALIDITY = "problem_validity"
    DISCUSSION_QUALITY = "discussion_quality"
    AI_CONFIDENCE_LEVEL = "ai_confidence_level"

    # Validation metadata
    CONFIDENCE_SCORE = "confidence_score"
    VALIDATION_TIMESTAMP = "trust_validation_timestamp"
    VALIDATION_METHOD = "trust_validation_method"

    # Additional trust metadata
    QUALITY_CONSTRAINTS_MET = "quality_constraints_met"
    ACTIVITY_CONSTRAINTS_MET = "activity_constraints_met"
    SUBREDDIT_ACTIVITY_SCORE = "subreddit_activity_score"
    POST_ENGAGEMENT_SCORE = "post_engagement_score"
    COMMUNITY_HEALTH_SCORE = "community_health_score"
    TREND_VELOCITY_SCORE = "trend_velocity_score"
    PROBLEM_VALIDITY_SCORE = "problem_validity_score"
    DISCUSSION_QUALITY_SCORE = "discussion_quality_score"
    AI_ANALYSIS_CONFIDENCE = "ai_analysis_confidence"
    OVERALL_TRUST_SCORE = "overall_trust_score"
    TRUST_BADGES = "trust_badges"

    # Cost tracking columns (related to trust)
    LLM_MODEL_USED = "llm_model_used"
    LLM_PROVIDER = "llm_provider"
    COST_TRACKING_ENABLED = "cost_tracking_enabled"

    # Primary key columns for DLT operations
    SUBMISSION_ID = "submission_id"
    OPPORTUNITY_ID = "opportunity_id"
    ID = "id"


class TrustLevel(str, Enum):
    """Trust level enumeration matching database values."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    UNKNOWN = "unknown"


class TrustBadge(str, Enum):
    """Trust badge enumeration matching database values."""
    GOLD = "GOLD"
    SILVER = "SILVER"
    BRONZE = "BRONZE"
    BASIC = "BASIC"
    NO_BADGE = "NO-BADGE"


class EngagementLevel(str, Enum):
    """Engagement level enumeration."""
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    MINIMAL = "MINIMAL"


class ProblemValidity(str, Enum):
    """Problem validity enumeration."""
    VALID = "VALID"
    POTENTIAL = "POTENTIAL"
    UNCLEAR = "UNCLEAR"
    INVALID = "INVALID"


class DiscussionQuality(str, Enum):
    """Discussion quality enumeration."""
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"


class AIConfidenceLevel(str, Enum):
    """AI confidence level enumeration."""
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TrustWeights:
    """Trust calculation weights for scoring."""

    # Default weights (must sum to 1.0)
    DEFAULT_WEIGHTS = {
        "subreddit_activity": 0.25,      # 25% - community engagement
        "post_engagement": 0.20,        # 20% - post interaction
        "trend_velocity": 0.15,         # 15% - emerging vs established
        "problem_validity": 0.15,       # 15% - AI confidence
        "discussion_quality": 0.15,     # 15% - comment quality
        "ai_confidence": 0.10           # 10% - analysis quality
    }

    # Weight bounds for validation
    MIN_WEIGHT = 0.05
    MAX_WEIGHT = 0.50
    TOTAL_WEIGHT = 1.0

    # Trust score thresholds
    TRUST_THRESHOLDS = {
        "very_high": 85.0,
        "high": 70.0,
        "medium": 50.0,
        "low": 0.0
    }


class TrustValidationConfig:
    """Configuration for trust validation system."""

    # Default thresholds
    DEFAULT_ACTIVITY_THRESHOLD = 25.0
    DEFAULT_QUALITY_THRESHOLD = 0.7

    # Validation constraints
    MAX_CORE_FUNCTIONS = 3
    MIN_PROBLEM_DESCRIPTION_LENGTH = 20
    MIN_APP_CONCEPT_LENGTH = 20

    # Badge generation thresholds
    ACTIVITY_BADGE_THRESHOLDS = {
        "highly_active": 80.0,
        "active": 60.0
    }

    ENGAGEMENT_BADGE_THRESHOLDS = {
        "high": 70.0,
        "good": 40.0
    }

    TREND_BADGE_THRESHOLDS = {
        "trending": 80.0,
        "emerging": 50.0
    }

    AI_CONFIDENCE_THRESHOLDS = {
        "high": 70.0,
        "medium": 50.0
    }


class TrustBadgeConfig:
    """Configuration for trust badge generation."""

    # Badge generation thresholds (matching TrustValidationConfig but as a class)
    activity_thresholds = {
        "highly_active": 80.0,
        "active": 60.0
    }

    engagement_thresholds = {
        "high": 70.0,
        "good": 40.0
    }

    trend_thresholds = {
        "trending": 80.0,
        "emerging": 50.0
    }

    ai_confidence_thresholds = {
        "high": 70.0,
        "medium": 50.0
    }


# Column groups for common operations
CORE_TRUST_COLUMNS = [
    TrustColumns.TRUST_SCORE,
    TrustColumns.TRUST_BADGE,
    TrustColumns.TRUST_LEVEL,
    TrustColumns.ACTIVITY_SCORE
]

ENGAGEMENT_COLUMNS = [
    TrustColumns.ACTIVITY_SCORE,
    TrustColumns.ENGAGEMENT_LEVEL,
    TrustColumns.TREND_VELOCITY,
    TrustColumns.POST_ENGAGEMENT_SCORE
]

QUALITY_COLUMNS = [
    TrustColumns.PROBLEM_VALIDITY,
    TrustColumns.DISCUSSION_QUALITY,
    TrustColumns.AI_CONFIDENCE_LEVEL,
    TrustColumns.QUALITY_CONSTRAINTS_MET
]

METADATA_COLUMNS = [
    TrustColumns.VALIDATION_TIMESTAMP,
    TrustColumns.VALIDATION_METHOD,
    TrustColumns.CONFIDENCE_SCORE
]

ALL_TRUST_COLUMNS = (
    CORE_TRUST_COLUMNS +
    ENGAGEMENT_COLUMNS +
    QUALITY_COLUMNS +
    METADATA_COLUMNS
)