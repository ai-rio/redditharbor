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
                self.logger.info(
                    f"Validated trust for {submission['submission_id']}: "
                    f"level={result.indicators.trust_level.value}, "
                    f"score={result.indicators.overall_trust_score}"
                )

                # Convert indicators to dict
                validation = asdict(result.indicators)

                # Convert TrustLevel enum to string if needed
                if hasattr(validation.get("trust_level"), "value"):
                    validation["trust_level"] = validation["trust_level"].value

                # Add metadata
                validation["submission_id"] = submission["submission_id"]

                return validation
            else:
                self.stats["errors"] += 1
                self.logger.warning(
                    f"Validation returned unsuccessful result for {submission['submission_id']}"
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

        # Get optional overrides from config
        activity_threshold = self.config.get("activity_threshold")
        trust_weights = self.config.get("trust_weights")

        return TrustValidationRequest(
            submission_id=submission["submission_id"],
            subreddit=submission["subreddit"],
            upvotes=submission.get("upvotes", 0),
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
        # Base validation (submission_id, title, subreddit)
        if not super().validate_input(submission):
            return False

        # Trust validation needs upvotes and created_utc
        required_fields = ["upvotes", "created_utc"]

        for field in required_fields:
            if field not in submission:
                self.logger.warning(
                    f"Submission {submission.get('submission_id')} missing {field}"
                )
                return False

        return True

    def get_service_name(self) -> str:
        """
        Return service name for logging.

        Returns:
            str: Service name "TrustService"
        """
        return "TrustService"
