"""
Trust Validation System - Data Models

Type-safe data models for trust validation with comprehensive validation
and serialization support. These models abstract the database schema
and enable safe schema consolidation.

Usage:
    from core.trust.models import TrustIndicators, TrustValidationRequest

    # Create type-safe trust indicators
    indicators = TrustIndicators(
        trust_score=85.5,
        trust_level=TrustLevel.HIGH,
        trust_badges=[TrustBadge.GOLD, TrustBadge.HIGH_ENGAGEMENT]
    )
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from core.trust.config import (
    AIConfidenceLevel,
    DiscussionQuality,
    EngagementLevel,
    ProblemValidity,
    TrustLevel,
    TrustValidationConfig,
    TrustWeights,
)


@dataclass
class TrustIndicators:
    """Comprehensive trust indicators for opportunity validation."""

    # Core trust metrics
    trust_score: float = 0.0
    trust_level: TrustLevel = TrustLevel.LOW
    trust_badges: list[str] = field(default_factory=list)

    # Activity indicators
    activity_score: float = 0.0
    engagement_level: str = EngagementLevel.MINIMAL.value
    trend_velocity: float = 0.0

    # Quality indicators
    problem_validity: str = ProblemValidity.UNCLEAR.value
    discussion_quality: str = DiscussionQuality.FAIR.value
    ai_confidence_level: str = AIConfidenceLevel.LOW.value

    # Validation metadata
    validation_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    validation_method: str = "trust_validation_service"
    confidence_score: float = 0.0

    # Constraint indicators
    quality_constraints_met: bool = False
    activity_constraints_met: bool = False

    # Detailed scoring components
    subreddit_activity_score: float = 0.0
    post_engagement_score: float = 0.0
    community_health_score: float = 0.0
    trend_velocity_score: float = 0.0
    problem_validity_score: float = 0.0
    discussion_quality_score: float = 0.0
    ai_analysis_confidence: float = 0.0
    overall_trust_score: float = 0.0

    def __post_init__(self):
        """Validate trust indicators after initialization."""
        self._validate_trust_score()
        self._validate_confidence_scores()
        self._validate_enums()

    def _validate_trust_score(self):
        """Validate trust score range."""
        if not (0.0 <= self.trust_score <= 100.0):
            raise ValueError(f"Trust score must be between 0-100, got {self.trust_score}")

    def _validate_confidence_scores(self):
        """Validate confidence score ranges."""
        scores = [
            self.confidence_score,
            self.subreddit_activity_score,
            self.post_engagement_score,
            self.community_health_score,
            self.trend_velocity_score,
            self.problem_validity_score,
            self.discussion_quality_score,
            self.ai_analysis_confidence,
            self.overall_trust_score
        ]

        for i, score in enumerate(scores):
            if not (0.0 <= score <= 100.0):
                raise ValueError(f"Confidence score {i} must be between 0-100, got {score}")

    def _validate_enums(self):
        """Validate enum values."""
        if isinstance(self.trust_level, str):
            try:
                self.trust_level = TrustLevel(self.trust_level.lower())
            except ValueError:
                self.trust_level = TrustLevel.LOW

        if isinstance(self.engagement_level, str):
            if self.engagement_level not in [e.value for e in EngagementLevel]:
                self.engagement_level = EngagementLevel.MINIMAL.value

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with snake_case keys."""
        return {
            "trust_score": self.trust_score,
            "trust_level": self.trust_level.value,
            "trust_badges": self.trust_badges,
            "activity_score": self.activity_score,
            "engagement_level": self.engagement_level,
            "trend_velocity": self.trend_velocity,
            "problem_validity": self.problem_validity,
            "discussion_quality": self.discussion_quality,
            "ai_confidence_level": self.ai_confidence_level,
            "validation_timestamp": self.validation_timestamp,
            "validation_method": self.validation_method,
            "confidence_score": self.confidence_score,
            "quality_constraints_met": self.quality_constraints_met,
            "activity_constraints_met": self.activity_constraints_met,
            "subreddit_activity_score": self.subreddit_activity_score,
            "post_engagement_score": self.post_engagement_score,
            "community_health_score": self.community_health_score,
            "trend_velocity_score": self.trend_velocity_score,
            "problem_validity_score": self.problem_validity_score,
            "discussion_quality_score": self.discussion_quality_score,
            "ai_analysis_confidence": self.ai_analysis_confidence,
            "overall_trust_score": self.overall_trust_score
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrustIndicators":
        """Create from dictionary, handling type conversion."""
        # Convert string enums to enum objects
        trust_level = data.get("trust_level", "low")
        if isinstance(trust_level, str):
            trust_level = TrustLevel(trust_level.lower())

        engagement_level = data.get("engagement_level", "minimal")
        if isinstance(engagement_level, str) and engagement_level not in [e.value for e in EngagementLevel]:
            engagement_level = EngagementLevel.MINIMAL.value

        return cls(
            trust_score=float(data.get("trust_score", 0.0)),
            trust_level=trust_level,
            trust_badges=data.get("trust_badges", []),
            activity_score=float(data.get("activity_score", 0.0)),
            engagement_level=engagement_level,
            trend_velocity=float(data.get("trend_velocity", 0.0)),
            problem_validity=data.get("problem_validity", ProblemValidity.UNCLEAR.value),
            discussion_quality=data.get("discussion_quality", DiscussionQuality.FAIR.value),
            ai_confidence_level=data.get("ai_confidence_level", AIConfidenceLevel.LOW.value),
            validation_timestamp=data.get("validation_timestamp", datetime.utcnow().isoformat()),
            validation_method=data.get("validation_method", "trust_validation_service"),
            confidence_score=float(data.get("confidence_score", 0.0)),
            quality_constraints_met=bool(data.get("quality_constraints_met", False)),
            activity_constraints_met=bool(data.get("activity_constraints_met", False)),
            subreddit_activity_score=float(data.get("subreddit_activity_score", 0.0)),
            post_engagement_score=float(data.get("post_engagement_score", 0.0)),
            community_health_score=float(data.get("community_health_score", 0.0)),
            trend_velocity_score=float(data.get("trend_velocity_score", 0.0)),
            problem_validity_score=float(data.get("problem_validity_score", 0.0)),
            discussion_quality_score=float(data.get("discussion_quality_score", 0.0)),
            ai_analysis_confidence=float(data.get("ai_analysis_confidence", 0.0)),
            overall_trust_score=float(data.get("overall_trust_score", 0.0))
        )


@dataclass
class TrustValidationRequest:
    """Request for trust validation."""

    # Required data
    submission_id: str
    subreddit: str
    upvotes: int
    comments_count: int
    created_utc: float | str
    text: str | None = None
    title: str | None = None

    # AI analysis data
    ai_analysis: dict[str, Any] | None = None

    # Optional configuration overrides
    activity_threshold: float | None = None
    trust_weights: dict[str, float] | None = None

    def __post_init__(self):
        """Validate request after initialization."""
        if not self.submission_id:
            raise ValueError("submission_id is required")
        if not self.subreddit:
            raise ValueError("subreddit is required")
        if self.upvotes < 0:
            raise ValueError("upvotes cannot be negative")
        if self.comments_count < 0:
            raise ValueError("comments_count cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "submission_id": self.submission_id,
            "subreddit": self.subreddit,
            "upvotes": self.upvotes,
            "comments_count": self.comments_count,
            "created_utc": self.created_utc,
            "text": self.text,
            "title": self.title,
            "ai_analysis": self.ai_analysis,
            "activity_threshold": self.activity_threshold,
            "trust_weights": self.trust_weights
        }


@dataclass
class TrustValidationResult:
    """Result of trust validation with metadata."""

    # Core results
    indicators: TrustIndicators
    success: bool = True
    error_message: str | None = None

    # Processing metadata
    processing_time_ms: float | None = None
    validation_version: str = "1.0"

    # Source data tracking
    source_submission_id: str = ""
    source_table: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "indicators": self.indicators.to_dict(),
            "success": self.success,
            "error_message": self.error_message,
            "processing_time_ms": self.processing_time_ms,
            "validation_version": self.validation_version,
            "source_submission_id": self.source_submission_id,
            "source_table": self.source_table
        }


@dataclass
class TrustScoreWeights:
    """Configurable weights for trust score calculation."""

    subreddit_activity: float = TrustWeights.DEFAULT_WEIGHTS["subreddit_activity"]
    post_engagement: float = TrustWeights.DEFAULT_WEIGHTS["post_engagement"]
    trend_velocity: float = TrustWeights.DEFAULT_WEIGHTS["trend_velocity"]
    problem_validity: float = TrustWeights.DEFAULT_WEIGHTS["problem_validity"]
    discussion_quality: float = TrustWeights.DEFAULT_WEIGHTS["discussion_quality"]
    ai_confidence: float = TrustWeights.DEFAULT_WEIGHTS["ai_confidence"]

    def __post_init__(self):
        """Validate weights after initialization."""
        self._validate_weights()

    def _validate_weights(self):
        """Validate weight constraints."""
        total = sum([
            self.subreddit_activity,
            self.post_engagement,
            self.trend_velocity,
            self.problem_validity,
            self.discussion_quality,
            self.ai_confidence
        ])

        # Allow small floating point tolerance
        if abs(total - TrustWeights.TOTAL_WEIGHT) > 0.01:
            raise ValueError(f"Weights must sum to {TrustWeights.TOTAL_WEIGHT}, got {total}")

        weights = [
            self.subreddit_activity,
            self.post_engagement,
            self.trend_velocity,
            self.problem_validity,
            self.discussion_quality,
            self.ai_confidence
        ]

        for weight in weights:
            if not (TrustWeights.MIN_WEIGHT <= weight <= TrustWeights.MAX_WEIGHT):
                raise ValueError(f"Each weight must be between {TrustWeights.MIN_WEIGHT}-{TrustWeights.MAX_WEIGHT}, got {weight}")

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return {
            "subreddit_activity": self.subreddit_activity,
            "post_engagement": self.post_engagement,
            "trend_velocity": self.trend_velocity,
            "problem_validity": self.problem_validity,
            "discussion_quality": self.discussion_quality,
            "ai_confidence": self.ai_confidence
        }

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "TrustScoreWeights":
        """Create from dictionary."""
        return cls(
            subreddit_activity=data.get("subreddit_activity", TrustWeights.DEFAULT_WEIGHTS["subreddit_activity"]),
            post_engagement=data.get("post_engagement", TrustWeights.DEFAULT_WEIGHTS["post_engagement"]),
            trend_velocity=data.get("trend_velocity", TrustWeights.DEFAULT_WEIGHTS["trend_velocity"]),
            problem_validity=data.get("problem_validity", TrustWeights.DEFAULT_WEIGHTS["problem_validity"]),
            discussion_quality=data.get("discussion_quality", TrustWeights.DEFAULT_WEIGHTS["discussion_quality"]),
            ai_confidence=data.get("ai_confidence", TrustWeights.DEFAULT_WEIGHTS["ai_confidence"])
        )


@dataclass
class TrustBadgeConfigModel:
    """Data model for trust badge configuration."""

    activity_thresholds: dict[str, float] = field(default_factory=lambda: TrustValidationConfig.ACTIVITY_BADGE_THRESHOLDS.copy())
    engagement_thresholds: dict[str, float] = field(default_factory=lambda: TrustValidationConfig.ENGAGEMENT_BADGE_THRESHOLDS.copy())
    trend_thresholds: dict[str, float] = field(default_factory=lambda: TrustValidationConfig.TREND_BADGE_THRESHOLDS.copy())
    ai_confidence_thresholds: dict[str, float] = field(default_factory=lambda: TrustValidationConfig.AI_CONFIDENCE_THRESHOLDS.copy())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "activity_thresholds": self.activity_thresholds,
            "engagement_thresholds": self.engagement_thresholds,
            "trend_thresholds": self.trend_thresholds,
            "ai_confidence_thresholds": self.ai_confidence_thresholds
        }


# Type aliases for better readability
TrustData = dict[str, Any]
TrustColumnMap = dict[str, str]
TrustTableMapping = dict[str, dict[str, str]]
