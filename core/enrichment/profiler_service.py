"""AI Profiler enrichment service with deduplication.

This module provides a wrapper for EnhancedLLMProfiler with integrated
deduplication logic from Phase 5. Prevents redundant AI profiler analyses
on semantically similar submissions to preserve cost savings.

Key Features:
- Wraps EnhancedLLMProfiler for unified interface
- Integrates ProfilerSkipLogic for deduplication
- Copies profiles from primary submissions
- Tracks statistics (analyzed, skipped, copied, errors)
- Handles errors gracefully
"""

import logging
from typing import Any, Optional

from core.agents.profiler import EnhancedLLMProfiler
from core.deduplication.profiler_skip_logic import ProfilerSkipLogic
from core.enrichment.base_service import BaseEnrichmentService

logger = logging.getLogger(__name__)


class ProfilerService(BaseEnrichmentService):
    """
    Wrapper for EnhancedLLMProfiler with deduplication.

    Provides AI profiler enrichment with integrated skip logic to prevent
    redundant analyses. Copies profiles from primary submissions when
    duplicates are detected.

    Attributes:
        profiler: EnhancedLLMProfiler instance
        skip_logic: ProfilerSkipLogic instance for deduplication
        enable_dedup: Whether deduplication is enabled

    Examples:
        >>> from supabase import create_client
        >>> from core.agents.profiler import EnhancedLLMProfiler
        >>> from core.deduplication.profiler_skip_logic import ProfilerSkipLogic
        >>>
        >>> client = create_client(url, key)
        >>> profiler = EnhancedLLMProfiler()
        >>> skip_logic = ProfilerSkipLogic(client)
        >>> service = ProfilerService(profiler, skip_logic)
        >>>
        >>> submission = {
        ...     'submission_id': 'abc123',
        ...     'title': 'Need fitness tracker',
        ...     'text': 'Looking for app to track workouts',
        ...     'subreddit': 'fitness',
        ...     'score': 50
        ... }
        >>> profile = service.enrich(submission)
        >>> assert 'app_name' in profile
    """

    def __init__(
        self,
        profiler: EnhancedLLMProfiler,
        skip_logic: ProfilerSkipLogic,
        config: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize ProfilerService.

        Args:
            profiler: EnhancedLLMProfiler instance for AI analysis
            skip_logic: ProfilerSkipLogic instance for deduplication
            config: Optional configuration with settings:
                - enable_deduplication: Enable/disable dedup (default: True)
                - include_agno_evidence: Use Agno analysis as evidence
        """
        super().__init__(config)
        self.profiler = profiler
        self.skip_logic = skip_logic
        self.enable_dedup = self.config.get("enable_deduplication", True)

    def enrich(self, submission: dict[str, Any]) -> dict[str, Any]:
        """
        Generate AI profile with deduplication.

        Checks if analysis should be skipped based on business concept.
        If skipped, attempts to copy from primary submission. Otherwise
        generates fresh profile using EnhancedLLMProfiler.

        Args:
            submission: Submission data dictionary with fields:
                - submission_id: Unique identifier
                - title: Submission title
                - text: Submission content
                - subreddit: Subreddit name
                - score: Opportunity score (optional, default: 50)
                - business_concept_id: Optional concept ID for dedup
                - agno_analysis: Optional Agno analysis for evidence

        Returns:
            dict: AI profile with fields:
                - app_name: Generated app name
                - core_functions: List of core features
                - value_proposition: Value prop description
                - problem_description: Problem being solved
                - target_user: Target user persona
                - monetization_model: Monetization approach
                - final_score: Overall score
                - market_demand, pain_intensity, etc.
                Or empty dict if error/skip occurs

        Examples:
            >>> submission = {
            ...     'submission_id': 'test1',
            ...     'title': 'Need project management tool',
            ...     'text': 'Struggling with team coordination',
            ...     'subreddit': 'startups',
            ...     'score': 75
            ... }
            >>> profile = service.enrich(submission)
            >>> assert 'app_name' in profile
            >>> assert service.stats['analyzed'] == 1
        """
        if not self.validate_input(submission):
            self.logger.error(
                f"Invalid submission: missing required fields for "
                f"{submission.get('submission_id', submission.get('id', 'unknown'))}"
            )
            self.stats["errors"] += 1
            return {}

        try:
            business_concept_id = submission.get("business_concept_id")

            # Check if should skip due to deduplication
            if self.enable_dedup and business_concept_id:
                should_run, reason = self.skip_logic.should_run_profiler_analysis(
                    submission, business_concept_id
                )

                if not should_run:
                    self.logger.info(
                        f"Skipping profiler for {submission.get('submission_id', submission.get('id', 'unknown'))}: {reason}"
                    )

                    # Try to copy from primary submission
                    primary_id = self._get_primary_submission_id(business_concept_id)
                    if primary_id:
                        copied = self.skip_logic.copy_profiler_analysis(
                            primary_id, submission.get("submission_id", submission.get("id", "unknown")), business_concept_id
                        )
                        if copied:
                            self.stats["copied"] += 1
                            self.logger.info(
                                f"Copied profile from {primary_id} to "
                                f"{submission.get('submission_id', submission.get('id', 'unknown'))}"
                            )
                            return copied

                    # Couldn't copy, mark as skipped
                    self.stats["skipped"] += 1
                    return {}

            # Run fresh analysis
            profile = self._generate_profile(submission)

            if profile:
                self.stats["analyzed"] += 1
                self.logger.info(
                    f"Generated profile for {submission.get('submission_id', submission.get('id', 'unknown'))}: "
                    f"{profile.get('app_name', 'unknown')}"
                )

                # Update business concept if applicable
                if business_concept_id:
                    self.skip_logic.update_concept_profiler_stats(
                        business_concept_id, profile
                    )

                return profile
            else:
                self.stats["errors"] += 1
                return {}

        except Exception as e:
            self.logger.error(
                f"Profiler error for {submission.get('submission_id', 'unknown')}: {e}",
                exc_info=True,
            )
            self.stats["errors"] += 1
            return {}

    def _generate_profile(self, submission: dict[str, Any]) -> dict[str, Any]:
        """
        Generate fresh AI profile using EnhancedLLMProfiler.

        Args:
            submission: Submission data dictionary

        Returns:
            dict: Generated profile or empty dict if generation fails
        """
        try:
            # Extract fields for profiler
            text = submission.get("text", "") or submission.get("content", "")
            title = submission.get("title", "")
            subreddit = submission.get("subreddit", "")
            score = submission.get("score", 50)  # Default to 50 if not provided
            agno_analysis = submission.get("agno_analysis")

            # Generate profile
            profile = self.profiler.generate_app_profile(
                text=text,
                title=title,
                subreddit=subreddit,
                score=score,
                agno_analysis=agno_analysis,
            )

            # Add metadata
            submission_id = submission.get("submission_id", submission.get("id", "unknown"))
            profile["submission_id"] = submission_id
            profile["opportunity_id"] = f"opp_{submission_id}"

            return profile

        except Exception as e:
            self.logger.error(f"Error generating profile: {e}", exc_info=True)
            return {}

    def _get_primary_submission_id(
        self, business_concept_id: int
    ) -> Optional[str]:
        """
        Get primary submission ID for a business concept.

        Args:
            business_concept_id: Business concept ID

        Returns:
            str: Primary submission ID or None if not found
        """
        try:
            concept = self.skip_logic.concept_manager.get_concept_by_id(
                business_concept_id
            )
            if concept:
                return concept.get("primary_submission_id")
            return None
        except Exception as e:
            self.logger.error(
                f"Error getting primary submission ID for concept {business_concept_id}: {e}"
            )
            return None

    def get_service_name(self) -> str:
        """
        Return service name for logging.

        Returns:
            str: Service name "ProfilerService"
        """
        return "ProfilerService"

    def validate_input(self, submission: dict[str, Any]) -> bool:
        """
        Validate submission has required fields for profiler.

        Args:
            submission: Submission data dictionary

        Returns:
            bool: True if valid, False otherwise
        """
        # Base validation
        if not super().validate_input(submission):
            return False

        # Profiler needs either text or content field
        has_content = bool(
            submission.get("text") or submission.get("content")
        )

        if not has_content:
            self.logger.warning(
                f"Submission {submission.get('submission_id')} missing text/content"
            )
            return False

        return True
