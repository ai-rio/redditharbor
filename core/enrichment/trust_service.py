"""Trust validation enrichment service.

This module provides a wrapper for TrustValidationService with the unified
enrichment service interface. Validates Reddit submissions using comprehensive
trust indicators including activity, engagement, and content quality metrics.

Key Features:
- Wraps TrustValidationService for unified interface
- Multi-dimensional trust assessment
- No deduplication (validation runs on all submissions)
- Tracks statistics (analyzed, errors)
- Handles errors gracefully
"""

import logging
from dataclasses import asdict
from typing import Any, Optional

from core.enrichment.base_service import BaseEnrichmentService
from core.trust import TrustValidationService
from core.trust.models import TrustValidationRequest

logger = logging.getLogger(__name__)


class TrustService(BaseEnrichmentService):
    """
    Wrapper for TrustValidationService with unified interface.

    Provides trust validation using comprehensive trust indicators.
    No deduplication logic - trust validation runs on all submissions
    as trust assessment is time-sensitive and context-dependent.

    Attributes:
        validator: TrustValidationService instance

    Examples:
        >>> from supabase import create_client
        >>> from core.trust import TrustValidationService, TrustRepositoryFactory
        >>>
        >>> client = create_client(url, key)
        >>> repository = TrustRepositoryFactory.create_repository(client)
        >>> validator = TrustValidationService(repository)
        >>> service = TrustService(validator)
        >>>
        >>> submission = {
        ...     'submission_id': 'abc123',
        ...     'title': 'Need better tool',
        ...     'text': 'Looking for solution',
        ...     'subreddit': 'productivity',
        ...     'upvotes': 150,
        ...     'comments_count': 25,
        ...     'created_utc': 1700000000
        ... }
        >>> validation = service.enrich(submission)
        >>> assert 'trust_level' in validation
        >>> assert 'overall_trust_score' in validation
    """

    def __init__(
        self,
        validator: TrustValidationService,
        config: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize TrustService.

        Args:
            validator: TrustValidationService instance for trust validation
            config: Optional configuration dictionary with settings:
                - activity_threshold: Minimum activity score (default: 25.0)
                - trust_weights: Custom weights for trust calculation
        """
        super().__init__(config)
        self.validator = validator

    def enrich(self, submission: dict[str, Any]) -> dict[str, Any]:
        """
        Validate trust using comprehensive indicators.

        Evaluates submission trust using multiple dimensions including
        subreddit activity, post engagement, trend velocity, problem
        validity, discussion quality, and AI analysis confidence.

        Args:
            submission: Submission data dictionary with fields:
                - submission_id: Unique identifier
                - title: Submission title
                - text: Submission content
                - subreddit: Subreddit name
                - upvotes: Number of upvotes
                - comments_count: Number of comments (or num_comments)
                - created_utc: Submission timestamp
                - ai_analysis: Optional AI analysis results

        Returns:
            dict: Trust validation with fields:
                - subreddit_activity_score: Activity score (0-100)
                - post_engagement_score: Engagement score (0-100)
                - community_health_score: Community health (0-100)
                - trend_velocity_score: Trend velocity (0-100)
                - problem_validity_score: Problem validity (0-100)
                - discussion_quality_score: Discussion quality (0-100)
                - ai_analysis_confidence: AI confidence (0-100)
                - overall_trust_score: Overall trust score (0-100)
                - trust_level: Trust level (low, medium, high, very_high)
                - trust_badges: List of earned badges
                - activity_constraints_met: Activity threshold met
                - quality_constraints_met: Quality threshold met
                - validation_timestamp: ISO timestamp
                - validation_method: Validation method used
                Or empty dict if error occurs

        Examples:
            >>> submission = {
            ...     'submission_id': 'test1',
            ...     'title': 'Looking for project tool',
            ...     'text': 'Need better solution',
            ...     'subreddit': 'startups',
            ...     'upvotes': 200,
            ...     'comments_count': 30,
            ...     'created_utc': 1700000000
            ... }
            >>> validation = service.enrich(submission)
            >>> assert validation['trust_level'] in ['low', 'medium', 'high', 'very_high']
            >>> assert 0 <= validation['overall_trust_score'] <= 100
        """
        if not self.validate_input(submission):
            self.logger.error(
                f"Invalid submission: missing required fields for "
                f"{submission.get('submission_id', 'unknown')}"
            )
            self.stats["errors"] += 1
            return {}

        try:
            # Format validation request
            request = self._format_validation_request(submission)

            # Run trust validation (no deduplication)
            result = self.validator.validate_opportunity_trust(request)

            if result.success and result.indicators:
                self.stats["analyzed"] += 1
                submission_id = submission.get("id", submission.get("submission_id", "unknown"))
                self.logger.info(
                    f"Validated trust for {submission_id}: "
                    f"level={result.indicators.trust_level.value}, "
                    f"score={result.indicators.overall_trust_score}"
                )

                # Convert indicators to dict
                validation = asdict(result.indicators)

                # Convert TrustLevel enum to string if needed
                if hasattr(validation.get("trust_level"), "value"):
                    validation["trust_level"] = validation["trust_level"].value

                # Generate trust_badges based on trust scores
                validation["trust_badges"] = self._generate_trust_badges(validation)

                # Add metadata
                validation["submission_id"] = submission_id

                return validation
            else:
                self.stats["errors"] += 1
                self.logger.warning(
                    f"Validation returned unsuccessful result for {submission.get('submission_id', submission.get('id', 'unknown'))}"
                )
                return {}

        except Exception as e:
            self.logger.error(
                f"Trust validation error for {submission.get('submission_id', 'unknown')}: {e}",
                exc_info=True,
            )
            self.stats["errors"] += 1
            return {}

    def _format_validation_request(
        self, submission: dict[str, Any]
    ) -> TrustValidationRequest:
        """
        Format submission data for TrustValidationService.

        Args:
            submission: Submission data from enrichment pipeline

        Returns:
            TrustValidationRequest: Formatted request for validator
        """
        # Extract fields
        text = submission.get("text", "") or submission.get("content", "")
        title = submission.get("title", "")

        # Handle both 'comments_count' and 'num_comments' fields
        comments_count = submission.get("comments_count", 0) or submission.get(
            "num_comments", 0
        )

        # Handle upvotes from top level or engagement object
        upvotes = submission.get("upvotes", 0)
        if upvotes == 0 and "engagement" in submission:
            upvotes = submission["engagement"].get("upvotes", 0)

        # Get optional overrides from config
        activity_threshold = self.config.get("activity_threshold")
        trust_weights = self.config.get("trust_weights")

        return TrustValidationRequest(
            submission_id=submission.get("id", submission.get("submission_id", "unknown")),
            subreddit=submission["subreddit"],
            upvotes=upvotes,
            comments_count=comments_count,
            created_utc=submission.get("created_utc", 0),
            text=text,
            title=title,
            ai_analysis=submission.get("ai_analysis"),
            activity_threshold=activity_threshold,
            trust_weights=trust_weights,
        )

    def validate_input(self, submission: dict[str, Any]) -> bool:
        """
        Validate submission has required fields for trust validation.

        Args:
            submission: Submission data dictionary

        Returns:
            bool: True if valid, False otherwise
        """
        # Get submission ID for logging
        submission_id = submission.get("id", submission.get("submission_id", "unknown"))

        # Base validation (id, title, subreddit) - super() expects 'id' field
        if not super().validate_input(submission):
            return False

        # Trust validation needs upvotes and created_utc
        # Check for upvotes at top level or in engagement object
        upvotes = submission.get("upvotes")
        if upvotes is None and "engagement" in submission:
            upvotes = submission["engagement"].get("upvotes")

        if upvotes is None:
            self.logger.warning(
                f"Submission {submission_id} missing upvotes"
            )
            return False

        # Check created_utc
        if "created_utc" not in submission:
            self.logger.warning(
                f"Submission {submission_id} missing created_utc"
            )
            return False

        return True

    def _generate_trust_badges(self, validation: dict[str, Any]) -> list[str]:
        """
        Generate trust badges based on validation scores.

        Args:
            validation: Validation result dict with trust scores

        Returns:
            list: List of earned trust badges
        """
        badges = []

        overall_score = validation.get("overall_trust_score", 0)
        trust_level = validation.get("trust_level", "unknown")
        subreddit_activity = validation.get("subreddit_activity_score", 0)
        post_engagement = validation.get("post_engagement_score", 0)
        community_health = validation.get("community_health_score", 0)
        problem_validity = validation.get("problem_validity_score", 0)
        discussion_quality = validation.get("discussion_quality_score", 0)

        # Overall trust badges
        if overall_score >= 90:
            badges.append("platinum_trust")
        elif overall_score >= 80:
            badges.append("gold_trust")
        elif overall_score >= 70:
            badges.append("silver_trust")
        elif overall_score >= 60:
            badges.append("bronze_trust")

        # Trust level badges
        if trust_level == "very_high":
            badges.append("very_high_trust")
        elif trust_level == "high":
            badges.append("high_trust")
        elif trust_level == "medium":
            badges.append("medium_trust")

        # Activity badges
        if subreddit_activity >= 80:
            badges.append("active_community")
        if post_engagement >= 75:
            badges.append("high_engagement")
        if community_health >= 85:
            badges.append("healthy_discourse")

        # Quality badges
        if problem_validity >= 80:
            badges.append("valid_problem")
        if discussion_quality >= 75:
            badges.append("quality_discussion")

        # Special combination badges
        if (subreddit_activity >= 80 and post_engagement >= 75 and
            problem_validity >= 80 and overall_score >= 85):
            badges.append("premium_opportunity")

        if (post_engagement >= 90 and discussion_quality >= 85):
            badges.append("viral_potential")

        # Ensure no duplicates and return
        return sorted(list(set(badges)))

    def get_service_name(self) -> str:
        """
        Return service name for logging.

        Returns:
            str: Service name "TrustService"
        """
        return "TrustService"
