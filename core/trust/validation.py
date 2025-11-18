"""
Trust Validation System - Service Layer

Main trust validation service that provides comprehensive trust analysis
for RedditHarbor opportunities. This service implements the business logic
and coordinates between different trust validation components.

Usage:
    from core.trust.validation import TrustValidationService
    from core.trust.repository import TrustRepositoryFactory

    repository = TrustRepositoryFactory.create_repository(supabase_client)
    service = TrustValidationService(repository)

    result = service.validate_opportunity_trust(request)
"""

import logging
import time
from datetime import UTC, datetime
from typing import Any

from core.trust.config import (
    AIConfidenceLevel,
    DiscussionQuality,
    EngagementLevel,
    ProblemValidity,
    TrustBadge,
    TrustBadgeConfig,
    TrustLevel,
    TrustValidationConfig,
    TrustWeights,
)
from core.trust.models import TrustBadgeConfigModel as BadgeConfig
from core.trust.models import (
    TrustIndicators,
    TrustScoreWeights,
    TrustValidationRequest,
    TrustValidationResult,
)
from core.trust.repository import TrustRepositoryInterface

logger = logging.getLogger(__name__)


class TrustValidationService:
    """Main trust validation service."""

    def __init__(
        self,
        repository: TrustRepositoryInterface,
        weights: TrustScoreWeights | None = None,
        badge_config: TrustBadgeConfig | None = None,
        activity_threshold: float = TrustValidationConfig.DEFAULT_ACTIVITY_THRESHOLD
    ):
        """Initialize trust validation service."""
        self.repository = repository
        self.weights = weights or TrustScoreWeights()
        self.badge_config = badge_config or BadgeConfig()
        self.activity_threshold = activity_threshold

        # Validation history for audit trail
        self.validation_history: list[TrustValidationResult] = []

    def validate_opportunity_trust(self, request: TrustValidationRequest) -> TrustValidationResult:
        """
        Validate trust for a single opportunity.

        Args:
            request: Trust validation request with submission data and AI analysis

        Returns:
            TrustValidationResult with indicators and metadata
        """
        start_time = time.time()
        logger.info(f"Starting trust validation for submission: {request.submission_id}")

        try:
            # Initialize trust indicators
            indicators = TrustIndicators(
                validation_timestamp=datetime.now(UTC).isoformat(),
                validation_method="comprehensive_trust_layer"
            )

            # Apply configuration overrides
            activity_threshold = request.activity_threshold or self.activity_threshold
            weights = TrustScoreWeights.from_dict(request.trust_weights) if request.trust_weights else self.weights

            # 1. Activity validation
            activity_score = self._validate_subreddit_activity(request)
            indicators.subreddit_activity_score = activity_score
            indicators.activity_constraints_met = activity_score >= activity_threshold
            indicators.activity_score = activity_score

            # 2. Post engagement validation
            engagement_score = self._validate_post_engagement(request)
            indicators.post_engagement_score = engagement_score

            # 3. Trend analysis
            trend_score = self._calculate_trend_velocity(request)
            indicators.trend_velocity_score = trend_score
            indicators.trend_velocity = trend_score

            # 4. Problem validation
            problem_score = self._validate_problem_validity(request)
            indicators.problem_validity_score = problem_score

            # 5. Discussion quality
            discussion_score = self._validate_discussion_quality(request)
            indicators.discussion_quality_score = discussion_score

            # 6. AI confidence
            ai_confidence = self._validate_ai_confidence(request)
            indicators.ai_analysis_confidence = ai_confidence

            # 7. Quality constraints check
            indicators.quality_constraints_met = self._check_quality_constraints(request)

            # 8. Calculate overall trust score
            indicators.overall_trust_score = self._calculate_overall_trust_score(indicators, weights)
            indicators.trust_level = self._determine_trust_level(indicators.overall_trust_score)
            indicators.trust_badges = self._generate_trust_badges(indicators, self.badge_config)
            indicators.confidence_score = self._calculate_confidence_score(indicators)

            # Set final trust score for compatibility
            indicators.trust_score = indicators.overall_trust_score
            indicators.engagement_level = self._determine_engagement_level(indicators.post_engagement_score)
            indicators.problem_validity = self._determine_problem_validity(indicators.problem_validity_score)
            indicators.discussion_quality = self._determine_discussion_quality(indicators.discussion_quality_score)
            indicators.ai_confidence_level = self._determine_ai_confidence_level(indicators.ai_analysis_confidence)

            processing_time = (time.time() - start_time) * 1000

            # Create result
            result = TrustValidationResult(
                indicators=indicators,
                success=True,
                processing_time_ms=processing_time,
                validation_version="1.0",
                source_submission_id=request.submission_id,
                source_table="service_layer"
            )

            # Add to history
            self.validation_history.append(result)

            logger.info(
                f"✅ Trust validation completed: {indicators.trust_level.value} trust "
                f"(score: {indicators.overall_trust_score:.1f}) "
                f"in {processing_time:.1f}ms"
            )

            return result

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            error_msg = f"Trust validation failed for {request.submission_id}: {e}"
            logger.error(error_msg)

            # Return minimal trust indicators on error
            indicators = TrustIndicators(
                overall_trust_score=10.0,
                trust_level=TrustLevel.LOW,
                trust_badges=["basic_validation"],
                validation_timestamp=datetime.now(UTC).isoformat(),
                validation_method="comprehensive_trust_layer_error"
            )

            result = TrustValidationResult(
                indicators=indicators,
                success=False,
                error_message=error_msg,
                processing_time_ms=processing_time,
                validation_version="1.0",
                source_submission_id=request.submission_id,
                source_table="service_layer"
            )

            self.validation_history.append(result)
            return result

    def validate_batch_opportunities_trust(self, requests: list[TrustValidationRequest]) -> list[TrustValidationResult]:
        """
        Validate trust for multiple opportunities.

        Args:
            requests: List of trust validation requests

        Returns:
            List of trust validation results
        """
        logger.info(f"Starting batch trust validation for {len(requests)} opportunities")
        results = []

        for i, request in enumerate(requests):
            try:
                result = self.validate_opportunity_trust(request)
                results.append(result)

                # Log progress every 10 requests
                if (i + 1) % 10 == 0:
                    logger.info(f"  Progress: {i + 1}/{len(requests)} processed")

            except Exception as e:
                logger.error(f"Error in batch validation for request {i}: {e}")
                # Add error result
                error_result = TrustValidationResult(
                    indicators=TrustIndicators(
                        overall_trust_score=0.0,
                        trust_level=TrustLevel.LOW,
                        trust_badges=["error"],
                        validation_timestamp=datetime.now(UTC).isoformat()
                    ),
                    success=False,
                    error_message=str(e),
                    processing_time_ms=0.0,
                    source_submission_id=request.submission_id,
                    source_table="batch_validation"
                )
                results.append(error_result)

        success_count = sum(1 for r in results if r.success)
        logger.info(f"✅ Batch validation completed: {success_count}/{len(results)} successful")

        return results

    def save_trust_indicators(self, submission_id: str, indicators: TrustIndicators) -> bool:
        """Save trust indicators to repository."""
        return self.repository.save_trust_indicators(submission_id, indicators)

    def get_trust_indicators(self, submission_id: str) -> TrustIndicators | None:
        """Get trust indicators from repository."""
        return self.repository.get_trust_indicators(submission_id)

    def _validate_subreddit_activity(self, request: TrustValidationRequest) -> float:
        """Validate subreddit activity using Reddit API."""
        try:
            # Import here to avoid circular dependencies
            import praw

            from config.settings import REDDIT_PUBLIC, REDDIT_SECRET, REDDIT_USER_AGENT

            reddit = praw.Reddit(
                client_id=REDDIT_PUBLIC,
                client_secret=REDDIT_SECRET,
                user_agent=REDDIT_USER_AGENT
            )

            subreddit = reddit.subreddit(request.subreddit)

            # Use existing activity validation
            from core.activity_validation import calculate_activity_score
            activity_score = calculate_activity_score(subreddit, time_filter="day")

            # Normalize to 0-100 scale for trust scoring
            normalized_score = min(100.0, activity_score * 2)  # Scale up for better trust scoring

            return round(normalized_score, 2)

        except Exception as e:
            logger.warning(f"Error validating subreddit activity for {request.submission_id}: {e}")
            return 0.0

    def _validate_post_engagement(self, request: TrustValidationRequest) -> float:
        """Validate post engagement metrics."""
        try:
            upvotes = request.upvotes or 0
            comments = request.comments_count or 0

            # Calculate engagement score
            # Upvotes: log scale (0-100 points)
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
            logger.warning(f"Error validating post engagement for {request.submission_id}: {e}")
            return 0.0

    def _calculate_trend_velocity(self, request: TrustValidationRequest) -> float:
        """Calculate trend velocity based on post timing and engagement patterns."""
        try:
            if not request.created_utc:
                return 0.0

            created_utc = float(request.created_utc)
            total_engagement = request.upvotes + request.comments_count

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
            logger.warning(f"Error calculating trend velocity for {request.submission_id}: {e}")
            return 0.0

    def _validate_problem_validity(self, request: TrustValidationRequest) -> float:
        """Validate problem validity using AI analysis."""
        try:
            if not request.ai_analysis:
                return 0.0

            ai_analysis = request.ai_analysis

            # Check AI analysis completeness
            problem_desc = ai_analysis.get('problem_description', '')
            app_concept = ai_analysis.get('app_concept', '')

            if not problem_desc or len(problem_desc.strip()) < TrustValidationConfig.MIN_PROBLEM_DESCRIPTION_LENGTH:
                return 0.0

            if not app_concept or len(app_concept.strip()) < TrustValidationConfig.MIN_APP_CONCEPT_LENGTH:
                return 0.0

            # Check for problem keywords in original text
            text = request.text or ''
            from core.collection import PROBLEM_KEYWORDS

            problem_keywords_found = len([kw for kw in PROBLEM_KEYWORDS if kw in text.lower()])

            # Calculate problem validity score
            keyword_score = min(100, problem_keywords_found * 20)
            length_score = min(100, len(problem_desc) / 2)

            validity_score = (keyword_score * 0.6) + (length_score * 0.4)

            return round(validity_score, 2)

        except Exception as e:
            logger.warning(f"Error validating problem validity for {request.submission_id}: {e}")
            return 0.0

    def _validate_discussion_quality(self, request: TrustValidationRequest) -> float:
        """Validate discussion quality based on comment patterns."""
        try:
            comments_count = request.comments_count or 0

            if comments_count == 0:
                return 0.0
            elif comments_count <= 5:
                return comments_count * 20  # Linear for small discussions
            elif comments_count <= 50:
                return 100 + (comments_count - 5) * 2  # Bonus for medium discussions
            else:
                return 100  # Max score for large discussions

        except Exception as e:
            logger.warning(f"Error validating discussion quality for {request.submission_id}: {e}")
            return 0.0

    def _validate_ai_confidence(self, request: TrustValidationRequest) -> float:
        """Validate AI analysis confidence."""
        try:
            if not request.ai_analysis:
                return 0.0

            final_score = request.ai_analysis.get('final_score', 0)

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
            logger.warning(f"Error validating AI confidence for {request.submission_id}: {e}")
            return 0.0

    def _check_quality_constraints(self, request: TrustValidationRequest) -> bool:
        """Check if quality constraints are met."""
        try:
            if not request.ai_analysis:
                return False

            ai_analysis = request.ai_analysis

            # Check function count constraint
            core_functions = ai_analysis.get('core_functions', [])
            if not isinstance(core_functions, list) or len(core_functions) > TrustValidationConfig.MAX_CORE_FUNCTIONS:
                return False

            # Check for complete app concept
            app_concept = ai_analysis.get('app_concept', '')
            if not app_concept or len(app_concept.strip()) < TrustValidationConfig.MIN_APP_CONCEPT_LENGTH:
                return False

            # Check for problem description
            problem_desc = ai_analysis.get('problem_description', '')
            if not problem_desc or len(problem_desc.strip()) < TrustValidationConfig.MIN_PROBLEM_DESCRIPTION_LENGTH:
                return False

            return True

        except Exception as e:
            logger.warning(f"Error checking quality constraints for {request.submission_id}: {e}")
            return False

    def _calculate_overall_trust_score(self, indicators: TrustIndicators, weights: TrustScoreWeights) -> float:
        """Calculate overall trust score from individual indicators."""
        try:
            overall_score = (
                indicators.subreddit_activity_score * weights.subreddit_activity +
                indicators.post_engagement_score * weights.post_engagement +
                indicators.trend_velocity_score * weights.trend_velocity +
                indicators.problem_validity_score * weights.problem_validity +
                indicators.discussion_quality_score * weights.discussion_quality +
                indicators.ai_analysis_confidence * weights.ai_confidence
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

    def _generate_trust_badges(self, indicators: TrustIndicators, badge_config: BadgeConfig) -> list[str]:
        """Generate trust badges based on validation results."""
        badges = []

        # Activity badge
        if indicators.activity_constraints_met:
            activity_thresholds = badge_config.activity_thresholds
            if indicators.subreddit_activity_score >= activity_thresholds.get("highly_active", 80):
                badges.append("🔥 Highly Active Community")
            elif indicators.subreddit_activity_score >= activity_thresholds.get("active", 60):
                badges.append("✅ Active Community")
            else:
                badges.append("⚠️ Low Activity")

        # Engagement badge
        engagement_thresholds = badge_config.engagement_thresholds
        if indicators.post_engagement_score >= engagement_thresholds.get("high", 70):
            badges.append("📈 High Engagement")
        elif indicators.post_engagement_score >= engagement_thresholds.get("good", 40):
            badges.append("📊 Good Engagement")

        # Trend badge
        trend_thresholds = badge_config.trend_thresholds
        if indicators.trend_velocity_score >= trend_thresholds.get("trending", 80):
            badges.append("🚀 Trending Topic")
        elif indicators.trend_velocity_score >= trend_thresholds.get("emerging", 50):
            badges.append("📈 Emerging Trend")

        # Quality badge
        if indicators.quality_constraints_met:
            badges.append("✅ Quality Verified")

        # AI confidence badge
        confidence_thresholds = badge_config.ai_confidence_thresholds
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

        # Add primary trust badge
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

    def get_validation_history(self, limit: int = 100) -> list[TrustValidationResult]:
        """Get validation history for audit trail."""
        return self.validation_history[-limit:]

    def clear_validation_history(self):
        """Clear validation history (use with caution)."""
        self.validation_history.clear()
        logger.info("Trust validation history cleared")

    def get_service_stats(self) -> dict[str, Any]:
        """Get service statistics."""
        history = self.validation_history
        total_validations = len(history)
        successful_validations = sum(1 for r in history if r.success)
        failed_validations = total_validations - successful_validations

        avg_processing_time = 0.0
        if history:
            processing_times = [r.processing_time_ms for r in history if r.processing_time_ms]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0.0

        return {
            "total_validations": total_validations,
            "successful_validations": successful_validations,
            "failed_validations": failed_validations,
            "success_rate": successful_validations / total_validations if total_validations > 0 else 0.0,
            "average_processing_time_ms": round(avg_processing_time, 2),
            "validation_version": "1.0",
            "activity_threshold": self.activity_threshold,
            "weights": self.weights.to_dict()
        }
