#!/usr/bin/env python3
"""
Pipeline-v2 Trust Validator - Complete 6-Dimensional Trust Scoring System

Extracted from scripts/dlt/dlt_trust_pipeline.py and core/trust/ to provide a clean,
dedicated trust validation system for the pipeline-v2 architecture.

This module implements the comprehensive trust validation algorithm with:
- 6-dimensional scoring: Activity, Engagement, Trend, Validity, Quality, AI Confidence
- Badge system: GOLD, SILVER, BRONZE, BADGE + secondary badges
- TrustIndicators dataclass with 20+ trust fields
- Database integration patterns for app_opportunities table
- Configuration constants and thresholds

NEW STRATEGY IMPLEMENTATION:
- Uses OpportunityAnalyzer wrapper from ..analysis (relative import)
- Direct core imports for MonetizationAgnoAnalyzer and EnhancedLLMProfiler
- Maintains interface compatibility with existing TrustLayerValidator

Author: Extracted from original RedditHarbor trust system
Version: Pipeline-v2 compatible
"""

import logging
import time
from datetime import datetime, UTC
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path for core imports
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# NEW STRATEGY: Import from analysis wrapper using relative import
try:
    from ..analysis import OpportunityAnalyzer
    OPPORTUNITY_ANALYZER_AVAILABLE = True
except ImportError:
    OPPORTUNITY_ANALYZER_AVAILABLE = False
    OpportunityAnalyzer = None

# Direct core imports for other agents (as per new strategy)
try:
    from core.agents.monetization.agno_analyzer import MonetizationAgnoAnalyzer
    MONETIZATION_ANALYZER_AVAILABLE = True
except ImportError:
    MONETIZATION_ANALYZER_AVAILABLE = False
    MonetizationAgnoAnalyzer = None

try:
    from core.agents.profiler.enhanced_profiler import EnhancedLLMProfiler
    PROFILER_AVAILABLE = True
except ImportError:
    PROFILER_AVAILABLE = False
    EnhancedLLMProfiler = None

# Core imports for trust validation
try:
    from core.collection import PROBLEM_KEYWORDS
    from core.activity_validation import calculate_activity_score
    CORE_DEPENDENCIES_AVAILABLE = True
except ImportError:
    CORE_DEPENDENCIES_AVAILABLE = False
    PROBLEM_KEYWORDS = [
        'problem', 'issue', 'help', 'recommendation', 'suggest', 'advice',
        'looking for', 'need', 'want', 'best', 'good', 'better', 'alternative'
    ]

    def calculate_activity_score(subreddit, time_filter="day"):
        """Fallback activity score calculation."""
        return 25.0  # Default moderate activity

# Configure logging
logger = logging.getLogger(__name__)


class TrustLevel(Enum):
    """Trust level enumeration."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class TrustBadge(Enum):
    """Trust badge enumeration."""
    GOLD = "GOLD"
    SILVER = "SILVER"
    BRONZE = "BRONZE"
    BASIC = "BASIC"


class EngagementLevel(Enum):
    """Engagement level enumeration."""
    MINIMAL = "MINIMAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class ProblemValidity(Enum):
    """Problem validity enumeration."""
    INVALID = "INVALID"
    UNCLEAR = "UNCLEAR"
    POTENTIAL = "POTENTIAL"
    VALID = "VALID"


class DiscussionQuality(Enum):
    """Discussion quality enumeration."""
    POOR = "POOR"
    FAIR = "FAIR"
    GOOD = "GOOD"
    EXCELLENT = "EXCELLENT"


class AIConfidenceLevel(Enum):
    """AI confidence level enumeration."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


@dataclass
class TrustWeights:
    """Trust scoring weights configuration."""
    subreddit_activity: float = 0.25
    post_engagement: float = 0.20
    trend_velocity: float = 0.15
    problem_validity: float = 0.15
    discussion_quality: float = 0.15
    ai_confidence: float = 0.10

    def __post_init__(self):
        """Validate weights sum to 1.0."""
        total = sum([
            self.subreddit_activity, self.post_engagement, self.trend_velocity,
            self.problem_validity, self.discussion_quality, self.ai_confidence
        ])
        if abs(total - 1.0) > 0.01:
            logger.warning(f"Trust weights sum to {total:.3f}, should be 1.0")

    # Trust score thresholds
    TRUST_THRESHOLDS = {
        "very_high": 85.0,
        "high": 70.0,
        "medium": 50.0,
        "low": 0.0
    }

    # Default weights
    DEFAULT_WEIGHTS = {
        "subreddit_activity": 0.25,
        "post_engagement": 0.20,
        "trend_velocity": 0.15,
        "problem_validity": 0.15,
        "discussion_quality": 0.15,
        "ai_confidence": 0.10
    }


@dataclass
class TrustValidationConfig:
    """Trust validation configuration constants."""
    # Activity thresholds
    DEFAULT_ACTIVITY_THRESHOLD: float = 25.0

    # Badge thresholds
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

    # Quality constraints
    MAX_CORE_FUNCTIONS: int = 3
    MIN_PROBLEM_DESCRIPTION_LENGTH: int = 20
    MIN_APP_CONCEPT_LENGTH: int = 20


@dataclass
class TrustIndicators:
    """Comprehensive trust indicators dataclass with 20+ trust fields."""

    # 6-dimensional scoring components
    subreddit_activity_score: float = 0.0
    post_engagement_score: float = 0.0
    trend_velocity_score: float = 0.0
    problem_validity_score: float = 0.0
    discussion_quality_score: float = 0.0
    ai_analysis_confidence: float = 0.0

    # Overall trust metrics
    overall_trust_score: float = 0.0
    trust_level: TrustLevel = TrustLevel.LOW
    trust_badges: List[str] = field(default_factory=list)
    confidence_score: float = 0.0

    # Additional scoring fields for compatibility
    activity_score: float = 0.0
    trust_score: float = 0.0
    engagement_level: str = EngagementLevel.MINIMAL.value
    trend_velocity: float = 0.0
    problem_validity: str = ProblemValidity.INVALID.value
    discussion_quality: str = DiscussionQuality.POOR.value
    ai_confidence_level: str = AIConfidenceLevel.LOW.value

    # Community health metrics
    community_health_score: float = 0.0

    # Validation metadata
    validation_timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    validation_method: str = "comprehensive_trust_layer"

    # Constraint indicators
    activity_constraints_met: bool = False
    quality_constraints_met: bool = False

    # Additional metadata for database integration
    subreddit: str = ""
    submission_id: str = ""

    def get_confidence_score(self) -> float:
        """Get confidence score for backward compatibility."""
        return self.confidence_score

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'subreddit_activity_score': self.subreddit_activity_score,
            'post_engagement_score': self.post_engagement_score,
            'trend_velocity_score': self.trend_velocity_score,
            'problem_validity_score': self.problem_validity_score,
            'discussion_quality_score': self.discussion_quality_score,
            'ai_analysis_confidence': self.ai_analysis_confidence,
            'overall_trust_score': self.overall_trust_score,
            'trust_level': self.trust_level.value,
            'trust_badges': self.trust_badges,
            'confidence_score': self.confidence_score,
            'activity_score': self.activity_score,
            'trust_score': self.trust_score,
            'engagement_level': self.engagement_level,
            'trend_velocity': self.trend_velocity,
            'problem_validity': self.problem_validity,
            'discussion_quality': self.discussion_quality,
            'ai_confidence_level': self.ai_confidence_level,
            'community_health_score': self.community_health_score,
            'validation_timestamp': self.validation_timestamp,
            'validation_method': self.validation_method,
            'activity_constraints_met': self.activity_constraints_met,
            'quality_constraints_met': self.quality_constraints_met,
            'subreddit': self.subreddit,
            'submission_id': self.submission_id
        }


class TrustValidator:
    """
    Main trust validation class implementing 6-dimensional trust scoring.

    Extracted from scripts/dlt/dlt_trust_pipeline.py trust validation logic
    and enhanced with the new strategy using ..analysis wrappers.

    Features:
    - 6-dimensional trust scoring algorithm
    - Badge assignment system
    - Database integration patterns
    - Backward compatibility with TrustLayerValidator
    """

    def __init__(
        self,
        activity_threshold: float = TrustValidationConfig.DEFAULT_ACTIVITY_THRESHOLD,
        weights: Optional[TrustWeights] = None,
        enable_ai_analysis: bool = True
    ):
        """
        Initialize trust validator.

        Args:
            activity_threshold: Minimum activity score for validation (default: 25.0)
            weights: Custom trust scoring weights
            enable_ai_analysis: Whether to use AI analysis components
        """
        self.activity_threshold = activity_threshold
        self.weights = weights or TrustWeights()
        self.enable_ai_analysis = enable_ai_analysis

        # Initialize AI agents if available and enabled
        self.opportunity_analyzer = None
        self.monetization_analyzer = None
        self.profiler = None

        if enable_ai_analysis:
            self._initialize_ai_agents()

        # Validation history for audit trail
        self.validation_history: List[TrustIndicators] = []

        logger.info(f"TrustValidator initialized with activity_threshold={activity_threshold}")

        if not CORE_DEPENDENCIES_AVAILABLE:
            logger.warning("Core dependencies not available, using fallback implementations")

    def _initialize_ai_agents(self):
        """Initialize AI agents using new strategy."""
        try:
            # NEW STRATEGY: Use OpportunityAnalyzer from ..analysis
            if OPPORTUNITY_ANALYZER_AVAILABLE:
                self.opportunity_analyzer = OpportunityAnalyzer()
                logger.info("OpportunityAnalyzer initialized from ..analysis")
            else:
                logger.warning("OpportunityAnalyzer not available from ..analysis")

            # Direct core imports for other agents
            if MONETIZATION_ANALYZER_AVAILABLE:
                self.monetization_analyzer = MonetizationAgnoAnalyzer()
                logger.info("MonetizationAgnoAnalyzer initialized from core.agents.monetization")
            else:
                logger.warning("MonetizationAgnoAnalyzer not available from core.agents.monetization")

            if PROFILER_AVAILABLE:
                self.profiler = EnhancedLLMProfiler()
                logger.info("EnhancedLLMProfiler initialized from core.agents.profiler")
            else:
                logger.warning("EnhancedLLMProfiler not available from core.agents.profiler")

        except Exception as e:
            logger.error(f"Failed to initialize AI agents: {e}")
            self.enable_ai_analysis = False

    def validate_opportunity_trust(
        self,
        submission_data: Dict[str, Any],
        ai_analysis: Dict[str, Any]
    ) -> TrustIndicators:
        """
        Validate trust for a single opportunity using 6-dimensional scoring.

        This is the main validation method that implements the complete trust
        scoring algorithm extracted from the original DLT trust pipeline.

        Args:
            submission_data: Reddit submission data with fields:
                - submission_id: Unique identifier
                - title: Post title
                - text: Post content
                - subreddit: Subreddit name
                - upvotes: Upvote count
                - comments_count: Comment count
                - created_utc: Creation timestamp
                - permalink: Reddit URL
            ai_analysis: AI analysis results containing:
                - final_score: Overall opportunity score
                - core_functions: List of app functions
                - problem_description: Problem description
                - app_concept: Application concept

        Returns:
            TrustIndicators: Comprehensive trust validation results
        """
        start_time = time.time()
        logger.info(f"Starting trust validation for submission: {submission_data.get('submission_id', 'unknown')}")

        # Initialize trust indicators
        indicators = TrustIndicators(
            subreddit=submission_data.get('subreddit', ''),
            submission_id=submission_data.get('submission_id', ''),
            validation_timestamp=datetime.now(UTC).isoformat(),
            validation_method="comprehensive_trust_layer_pipeline_v2"
        )

        try:
            # 1. Activity validation - subreddit activity score
            indicators.subreddit_activity_score = self._validate_subreddit_activity(submission_data)
            indicators.activity_constraints_met = indicators.subreddit_activity_score >= self.activity_threshold
            indicators.activity_score = indicators.subreddit_activity_score

            # 2. Post engagement validation
            indicators.post_engagement_score = self._validate_post_engagement(submission_data)
            indicators.engagement_level = self._determine_engagement_level(indicators.post_engagement_score)

            # 3. Trend velocity calculation
            indicators.trend_velocity_score = self._calculate_trend_velocity(submission_data)
            indicators.trend_velocity = indicators.trend_velocity_score

            # 4. Problem validity assessment
            indicators.problem_validity_score = self._validate_problem_validity(submission_data, ai_analysis)
            indicators.problem_validity = self._determine_problem_validity(indicators.problem_validity_score)

            # 5. Discussion quality evaluation
            indicators.discussion_quality_score = self._validate_discussion_quality(submission_data)
            indicators.discussion_quality = self._determine_discussion_quality(indicators.discussion_quality_score)

            # 6. AI confidence assessment
            indicators.ai_analysis_confidence = self._validate_ai_confidence(ai_analysis)
            indicators.ai_confidence_level = self._determine_ai_confidence_level(indicators.ai_analysis_confidence)

            # 7. Quality constraints check
            indicators.quality_constraints_met = self._check_quality_constraints(ai_analysis)

            # 8. Calculate overall trust score (6-dimensional weighted sum)
            indicators.overall_trust_score = self._calculate_overall_trust_score(indicators)
            indicators.trust_level = self._determine_trust_level(indicators.overall_trust_score)

            # 9. Generate trust badges
            indicators.trust_badges = self._generate_trust_badges(indicators)

            # 10. Set compatibility fields
            indicators.trust_score = indicators.overall_trust_score
            indicators.confidence_score = self._calculate_confidence_score(indicators)

            # 11. Add to validation history
            self.validation_history.append(indicators)

            processing_time = (time.time() - start_time) * 1000
            logger.info(
                f"✅ Trust validation completed: {indicators.trust_level.value} trust "
                f"(score: {indicators.overall_trust_score:.1f}) "
                f"in {processing_time:.1f}ms"
            )

            return indicators

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            error_msg = f"Trust validation failed for {submission_data.get('submission_id', 'unknown')}: {e}"
            logger.error(error_msg)

            # Return minimal trust indicators on error
            indicators.overall_trust_score = 10.0
            indicators.trust_level = TrustLevel.LOW
            indicators.trust_badges = ["BASIC"]
            indicators.validation_method = "comprehensive_trust_layer_error"

            return indicators

    def _validate_subreddit_activity(self, submission_data: Dict[str, Any]) -> float:
        """Validate subreddit activity using Reddit API or fallback."""
        try:
            if not CORE_DEPENDENCIES_AVAILABLE:
                logger.warning("Core dependencies not available, using fallback activity score")
                return 30.0  # Moderate fallback activity

            # Use existing activity validation from core
            import praw
            from config.settings import REDDIT_PUBLIC, REDDIT_SECRET, REDDIT_USER_AGENT

            reddit = praw.Reddit(
                client_id=REDDIT_PUBLIC,
                client_secret=REDDIT_SECRET,
                user_agent=REDDIT_USER_AGENT
            )

            subreddit_name = submission_data.get('subreddit', '')
            if not subreddit_name:
                return 0.0

            subreddit = reddit.subreddit(subreddit_name)

            # Use existing activity validation
            activity_score = calculate_activity_score(subreddit, time_filter="day")

            # Normalize to 0-100 scale for trust scoring
            normalized_score = min(100.0, activity_score * 2)

            return round(normalized_score, 2)

        except Exception as e:
            logger.warning(f"Error validating subreddit activity: {e}")
            return 25.0  # Default moderate activity

    def _validate_post_engagement(self, submission_data: Dict[str, Any]) -> float:
        """Validate post engagement metrics using log scaling."""
        try:
            upvotes = submission_data.get('upvotes', 0) or submission_data.get('score', 0)
            comments = submission_data.get('comments_count', 0) or submission_data.get('num_comments', 0)

            # Handle negative values
            upvotes = max(0, upvotes)
            comments = max(0, comments)

            # Calculate engagement score using log scaling
            # Upvotes: log scale (0-100+ points)
            if upvotes <= 0:
                upvote_score = 0
            elif upvotes <= 10:
                upvote_score = upvotes * 10
            elif upvotes <= 100:
                upvote_score = 100 + (upvotes - 10) * 5
            else:
                upvote_score = 100 + (upvotes - 100) * 2

            # Comments: linear scale (0-100 points)
            comment_score = min(100, comments)

            # Combined engagement score (70% upvotes, 30% comments)
            engagement_score = (upvote_score * 0.7) + (comment_score * 0.3)

            return round(engagement_score, 2)

        except Exception as e:
            logger.warning(f"Error validating post engagement: {e}")
            return 0.0

    def _calculate_trend_velocity(self, submission_data: Dict[str, Any]) -> float:
        """Calculate trend velocity based on post timing and engagement patterns."""
        try:
            if not submission_data.get('created_utc'):
                return 0.0

            created_utc = float(submission_data['created_utc'])
            upvotes = submission_data.get('upvotes', 0) or submission_data.get('score', 0)
            comments = submission_data.get('comments_count', 0) or submission_data.get('num_comments', 0)

            total_engagement = max(0, upvotes) + max(0, comments)

            # Calculate time since post creation
            created_time = datetime.fromtimestamp(created_utc, tz=UTC)
            time_diff = datetime.now(UTC) - created_time
            hours_old = time_diff.total_seconds() / 3600

            # Trend velocity based on engagement rate over time
            if hours_old <= 1:
                # Very recent (1 hour): high velocity potential
                velocity_score = min(100, total_engagement * 10)
            elif hours_old <= 24:
                # Recent (1 day): good velocity
                velocity_score = min(100, total_engagement * 5)
            elif hours_old <= 168:  # 1 week
                velocity_score = min(100, total_engagement * 2)
            else:
                # Older posts: lower velocity but stable
                velocity_score = min(100, total_engagement)

            # Apply time decay for very old posts
            if hours_old > 168:  # More than 1 week
                decay_factor = max(0.1, 1.0 - (hours_old - 168) / 720)  # Decay over 1 month
                velocity_score *= decay_factor

            return round(velocity_score, 2)

        except Exception as e:
            logger.warning(f"Error calculating trend velocity: {e}")
            return 0.0

    def _validate_problem_validity(self, submission_data: Dict[str, Any], ai_analysis: Dict[str, Any]) -> float:
        """Validate problem validity using AI analysis and content analysis."""
        try:
            if not ai_analysis:
                return 0.0

            # Check AI analysis completeness
            problem_desc = ai_analysis.get('problem_description', '') or ai_analysis.get('market需求评估', '')
            app_concept = ai_analysis.get('app_concept', '')

            if not problem_desc or len(problem_desc.strip()) < TrustValidationConfig.MIN_PROBLEM_DESCRIPTION_LENGTH:
                return 0.0

            if not app_concept or len(app_concept.strip()) < TrustValidationConfig.MIN_APP_CONCEPT_LENGTH:
                return 0.0

            # Check for problem keywords in original text
            text = submission_data.get('text', '') or submission_data.get('content', '')

            problem_keywords_found = len([kw for kw in PROBLEM_KEYWORDS if kw in text.lower()])

            # Calculate problem validity score
            keyword_score = min(100, problem_keywords_found * 20)
            length_score = min(100, len(problem_desc) / 2)

            validity_score = (keyword_score * 0.6) + (length_score * 0.4)

            return round(validity_score, 2)

        except Exception as e:
            logger.warning(f"Error validating problem validity: {e}")
            return 0.0

    def _validate_discussion_quality(self, submission_data: Dict[str, Any]) -> float:
        """Validate discussion quality based on comment patterns."""
        try:
            comments_count = submission_data.get('comments_count', 0) or submission_data.get('num_comments', 0)
            comments_count = max(0, comments_count)

            if comments_count == 0:
                return 0.0
            elif comments_count <= 5:
                return comments_count * 20  # Linear for small discussions
            elif comments_count <= 50:
                return 100 + (comments_count - 5) * 2  # Bonus for medium discussions
            else:
                return 100  # Max score for large discussions

        except Exception as e:
            logger.warning(f"Error validating discussion quality: {e}")
            return 0.0

    def _validate_ai_confidence(self, ai_analysis: Dict[str, Any]) -> float:
        """Validate AI analysis confidence."""
        try:
            if not ai_analysis:
                return 0.0

            final_score = ai_analysis.get('final_score', 0) or ai_analysis.get('opportunity_score', 0)
            final_score = max(0, min(100, final_score))  # Clamp to 0-100

            # Check AI score range and consistency
            if final_score >= 70:
                return 90.0  # High confidence
            elif final_score >= 50:
                return 70.0  # Medium confidence
            elif final_score >= 30:
                return 50.0  # Low confidence
            else:
                return 30.0  # Very low confidence

        except Exception as e:
            logger.warning(f"Error validating AI confidence: {e}")
            return 0.0

    def _check_quality_constraints(self, ai_analysis: Dict[str, Any]) -> bool:
        """Check if quality constraints are met."""
        try:
            if not ai_analysis:
                return False

            # Check function count constraint
            core_functions = ai_analysis.get('core_functions', [])
            if not isinstance(core_functions, list) or len(core_functions) > TrustValidationConfig.MAX_CORE_FUNCTIONS:
                return False

            # Check for complete app concept
            app_concept = ai_analysis.get('app_concept', '')
            if not app_concept or len(app_concept.strip()) < TrustValidationConfig.MIN_APP_CONCEPT_LENGTH:
                return False

            # Check for problem description
            problem_desc = ai_analysis.get('problem_description', '') or ai_analysis.get('market需求评估', '')
            if not problem_desc or len(problem_desc.strip()) < TrustValidationConfig.MIN_PROBLEM_DESCRIPTION_LENGTH:
                return False

            return True

        except Exception as e:
            logger.warning(f"Error checking quality constraints: {e}")
            return False

    def _calculate_overall_trust_score(self, indicators: TrustIndicators) -> float:
        """Calculate overall trust score from 6-dimensional components."""
        try:
            overall_score = (
                indicators.subreddit_activity_score * self.weights.subreddit_activity +
                indicators.post_engagement_score * self.weights.post_engagement +
                indicators.trend_velocity_score * self.weights.trend_velocity +
                indicators.problem_validity_score * self.weights.problem_validity +
                indicators.discussion_quality_score * self.weights.discussion_quality +
                indicators.ai_analysis_confidence * self.weights.ai_confidence
            )

            return round(overall_score, 2)

        except Exception as e:
            logger.error(f"Error calculating overall trust score: {e}")
            return 10.0

    def _determine_trust_level(self, trust_score: float) -> TrustLevel:
        """Determine trust level based on trust score."""
        thresholds = TrustWeights.TRUST_THRESHOLDS

        if trust_score >= thresholds["very_high"]:
            return TrustLevel.VERY_HIGH
        elif trust_score >= thresholds["high"]:
            return TrustLevel.HIGH
        elif trust_score >= thresholds["medium"]:
            return TrustLevel.MEDIUM
        else:
            return TrustLevel.LOW

    def _determine_engagement_level(self, engagement_score: float) -> str:
        """Determine engagement level based on score."""
        if engagement_score >= 80:
            return EngagementLevel.VERY_HIGH.value
        elif engagement_score >= 60:
            return EngagementLevel.HIGH.value
        elif engagement_score >= 40:
            return EngagementLevel.MEDIUM.value
        elif engagement_score >= 20:
            return EngagementLevel.LOW.value
        else:
            return EngagementLevel.MINIMAL.value

    def _determine_problem_validity(self, validity_score: float) -> str:
        """Determine problem validity based on score."""
        if validity_score >= 80:
            return ProblemValidity.VALID.value
        elif validity_score >= 60:
            return ProblemValidity.POTENTIAL.value
        elif validity_score >= 40:
            return ProblemValidity.UNCLEAR.value
        else:
            return ProblemValidity.INVALID.value

    def _determine_discussion_quality(self, quality_score: float) -> str:
        """Determine discussion quality based on score."""
        if quality_score >= 80:
            return DiscussionQuality.EXCELLENT.value
        elif quality_score >= 60:
            return DiscussionQuality.GOOD.value
        elif quality_score >= 40:
            return DiscussionQuality.FAIR.value
        else:
            return DiscussionQuality.POOR.value

    def _determine_ai_confidence_level(self, confidence_score: float) -> str:
        """Determine AI confidence level based on score."""
        if confidence_score >= 80:
            return AIConfidenceLevel.VERY_HIGH.value
        elif confidence_score >= 60:
            return AIConfidenceLevel.HIGH.value
        elif confidence_score >= 40:
            return AIConfidenceLevel.MEDIUM.value
        else:
            return AIConfidenceLevel.LOW.value

    def _generate_trust_badges(self, indicators: TrustIndicators) -> List[str]:
        """Generate trust badges based on validation results."""
        badges = []

        # Activity badge
        if indicators.activity_constraints_met:
            activity_thresholds = TrustValidationConfig.ACTIVITY_BADGE_THRESHOLDS
            if indicators.subreddit_activity_score >= activity_thresholds.get("highly_active", 80):
                badges.append("🔥 Highly Active Community")
            elif indicators.subreddit_activity_score >= activity_thresholds.get("active", 60):
                badges.append("✅ Active Community")

        # Engagement badge
        engagement_thresholds = TrustValidationConfig.ENGAGEMENT_BADGE_THRESHOLDS
        if indicators.post_engagement_score >= engagement_thresholds.get("high", 70):
            badges.append("📈 High Engagement")
        elif indicators.post_engagement_score >= engagement_thresholds.get("good", 40):
            badges.append("📊 Good Engagement")

        # Trend badge
        trend_thresholds = TrustValidationConfig.TREND_BADGE_THRESHOLDS
        if indicators.trend_velocity_score >= trend_thresholds.get("trending", 80):
            badges.append("🚀 Trending Topic")
        elif indicators.trend_velocity_score >= trend_thresholds.get("emerging", 50):
            badges.append("📈 Emerging Trend")

        # Quality badge
        if indicators.quality_constraints_met:
            badges.append("✅ Quality Verified")

        # AI confidence badge
        confidence_thresholds = TrustValidationConfig.AI_CONFIDENCE_THRESHOLDS
        if indicators.ai_analysis_confidence >= confidence_thresholds.get("high", 70):
            badges.append("🤖 High AI Confidence")
        elif indicators.ai_analysis_confidence >= confidence_thresholds.get("medium", 50):
            badges.append("🤖 AI Verified")

        # Overall trust badge
        if indicators.trust_level == TrustLevel.VERY_HIGH:
            badges.append("🏆 Premium Quality")
        elif indicators.trust_level == TrustLevel.HIGH:
            badges.append("🌟 High Trust")
        elif indicators.trust_level == TrustLevel.MEDIUM:
            badges.append("🟡 Moderate Trust")
        else:
            badges.append("⚠️ Basic Validation")

        # Add primary trust badge at the beginning
        if indicators.overall_trust_score >= 85:
            badges.insert(0, TrustBadge.GOLD.value)
        elif indicators.overall_trust_score >= 70:
            badges.insert(0, TrustBadge.SILVER.value)
        elif indicators.overall_trust_score >= 50:
            badges.insert(0, TrustBadge.BRONZE.value)
        else:
            badges.insert(0, TrustBadge.BASIC.value)

        return badges

    def _calculate_confidence_score(self, indicators: TrustIndicators) -> float:
        """Calculate overall confidence score from validation results."""
        try:
            # Weight components for confidence calculation
            components = [
                indicators.subreddit_activity_score * 0.2,
                indicators.problem_validity_score * 0.3,
                indicators.discussion_quality_score * 0.2,
                indicators.ai_analysis_confidence * 0.3
            ]

            confidence_score = sum(components)

            # Apply constraint penalties
            if not indicators.quality_constraints_met:
                confidence_score *= 0.8  # 20% penalty

            if not indicators.activity_constraints_met:
                confidence_score *= 0.9  # 10% penalty

            return round(confidence_score, 2)

        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.0

    def get_validation_history(self, limit: int = 100) -> List[TrustIndicators]:
        """Get validation history for audit trail."""
        return self.validation_history[-limit:]

    def clear_validation_history(self):
        """Clear validation history (use with caution)."""
        self.validation_history.clear()
        logger.info("Trust validation history cleared")

    def get_validator_stats(self) -> Dict[str, Any]:
        """Get validator statistics."""
        history = self.validation_history
        total_validations = len(history)

        if total_validations == 0:
            return {
                "total_validations": 0,
                "average_trust_score": 0.0,
                "trust_distribution": {},
                "activity_threshold": self.activity_threshold,
                "ai_analysis_enabled": self.enable_ai_analysis
            }

        # Calculate statistics
        avg_trust_score = sum(ind.overall_trust_score for ind in history) / total_validations

        trust_distribution = {}
        for level in TrustLevel:
            count = sum(1 for ind in history if ind.trust_level == level)
            trust_distribution[level.value] = count

        return {
            "total_validations": total_validations,
            "average_trust_score": round(avg_trust_score, 2),
            "trust_distribution": trust_distribution,
            "activity_threshold": self.activity_threshold,
            "ai_analysis_enabled": self.enable_ai_analysis,
            "agents_available": {
                "opportunity_analyzer": OPPORTUNITY_ANALYZER_AVAILABLE,
                "monetization_analyzer": MONETIZATION_ANALYZER_AVAILABLE,
                "profiler": PROFILER_AVAILABLE
            }
        }


# Convenience functions for easy integration
def create_trust_validator(
    activity_threshold: float = TrustValidationConfig.DEFAULT_ACTIVITY_THRESHOLD,
    enable_ai_analysis: bool = True
) -> TrustValidator:
    """
    Create a trust validator instance with default configuration.

    Args:
        activity_threshold: Minimum activity score for validation
        enable_ai_analysis: Whether to enable AI analysis components

    Returns:
        TrustValidator: Configured trust validator instance
    """
    return TrustValidator(
        activity_threshold=activity_threshold,
        enable_ai_analysis=enable_ai_analysis
    )


def validate_opportunity_trust(
    submission_data: Dict[str, Any],
    ai_analysis: Dict[str, Any],
    activity_threshold: float = TrustValidationConfig.DEFAULT_ACTIVITY_THRESHOLD
) -> TrustIndicators:
    """
    Validate trust for a single opportunity using default validator.

    This is a convenience function that creates a validator and performs
    validation in one call. Useful for simple use cases.

    Args:
        submission_data: Reddit submission data
        ai_analysis: AI analysis results
        activity_threshold: Minimum activity score for validation

    Returns:
        TrustIndicators: Comprehensive trust validation results
    """
    validator = create_trust_validator(activity_threshold=activity_threshold)
    return validator.validate_opportunity_trust(submission_data, ai_analysis)


# Backward compatibility alias for existing code
TrustLayerValidator = TrustValidator


# Export key classes and functions
__all__ = [
    "TrustValidator",
    "TrustIndicators",
    "TrustLevel",
    "TrustBadge",
    "TrustWeights",
    "TrustValidationConfig",
    "EngagementLevel",
    "ProblemValidity",
    "DiscussionQuality",
    "AIConfidenceLevel",
    "create_trust_validator",
    "validate_opportunity_trust",
    "TrustLayerValidator"  # Backward compatibility
]