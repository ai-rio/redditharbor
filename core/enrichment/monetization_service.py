"""Monetization analysis enrichment service with deduplication.

This module provides a wrapper for MonetizationAgnoAnalyzer with integrated
deduplication logic from Phase 5. Prevents redundant monetization analyses
on semantically similar submissions to preserve cost savings ($1,764/year).

Key Features:
- Wraps MonetizationAgnoAnalyzer for unified interface
- Integrates AgnoSkipLogic for deduplication
- Copies analyses from primary submissions
- Tracks statistics (analyzed, skipped, copied, errors)
- Handles errors gracefully
"""

import logging
from dataclasses import asdict
from typing import Any, Optional

from core.agents.monetization.agno_analyzer import MonetizationAgnoAnalyzer
from core.deduplication.agno_skip_logic import AgnoSkipLogic
from core.enrichment.base_service import BaseEnrichmentService

logger = logging.getLogger(__name__)


class MonetizationService(BaseEnrichmentService):
    """
    Wrapper for MonetizationAgnoAnalyzer with deduplication.

    Provides monetization analysis with integrated skip logic to prevent
    redundant analyses. Copies analyses from primary submissions when
    duplicates are detected, preserving $1,764/year in cost savings.

    Attributes:
        analyzer: MonetizationAgnoAnalyzer instance
        skip_logic: AgnoSkipLogic instance for deduplication
        enable_dedup: Whether deduplication is enabled

    Examples:
        >>> from supabase import create_client
        >>> from core.agents.monetization.agno_analyzer import MonetizationAgnoAnalyzer
        >>> from core.deduplication.agno_skip_logic import AgnoSkipLogic
        >>>
        >>> client = create_client(url, key)
        >>> analyzer = MonetizationAgnoAnalyzer()
        >>> skip_logic = AgnoSkipLogic(client)
        >>> service = MonetizationService(analyzer, skip_logic)
        >>>
        >>> submission = {
        ...     'submission_id': 'abc123',
        ...     'title': 'Need budgeting app',
        ...     'text': 'Willing to pay for better solution',
        ...     'subreddit': 'personalfinance'
        ... }
        >>> analysis = service.enrich(submission)
        >>> assert 'willingness_to_pay_score' in analysis
    """

    def __init__(
        self,
        analyzer: MonetizationAgnoAnalyzer,
        skip_logic: AgnoSkipLogic,
        config: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize MonetizationService.

        Args:
            analyzer: MonetizationAgnoAnalyzer instance for monetization analysis
            skip_logic: AgnoSkipLogic instance for deduplication
            config: Optional configuration with settings:
                - enable_deduplication: Enable/disable dedup (default: True)
                - keyword_monetization_score: Optional baseline score
        """
        super().__init__(config)
        self.analyzer = analyzer
        self.skip_logic = skip_logic
        self.enable_dedup = self.config.get("enable_deduplication", True)

    def enrich(self, submission: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze monetization potential with deduplication.

        Checks if analysis should be skipped based on business concept.
        If skipped, attempts to copy from primary submission. Otherwise
        generates fresh analysis using MonetizationAgnoAnalyzer.

        Args:
            submission: Submission data dictionary with fields:
                - submission_id: Unique identifier
                - title: Submission title
                - text: Submission content
                - subreddit: Subreddit name
                - business_concept_id: Optional concept ID for dedup
                - keyword_monetization_score: Optional baseline score

        Returns:
            dict: Monetization analysis with fields:
                - willingness_to_pay_score: WTP score (0-100)
                - market_segment_score: Market segment score (0-100)
                - price_sensitivity_score: Price sensitivity (0-100)
                - revenue_potential_score: Revenue potential (0-100)
                - customer_segment: B2B, B2C, Mixed, Unknown
                - mentioned_price_points: List of mentioned prices
                - existing_payment_behavior: Current spending patterns
                - urgency_level: Critical, High, Medium, Low
                - sentiment_toward_payment: Positive, Neutral, Negative
                - payment_friction_indicators: List of friction points
                - llm_monetization_score: Overall score (0-100)
                - confidence: Analysis confidence (0-1)
                - reasoning: Analysis reasoning
                - subreddit_multiplier: Subreddit context multiplier
                Or empty dict if error/skip occurs

        Examples:
            >>> submission = {
            ...     'submission_id': 'test1',
            ...     'title': 'Looking for project management tool',
            ...     'text': 'Would pay $50/month for better solution',
            ...     'subreddit': 'startups'
            ... }
            >>> analysis = service.enrich(submission)
            >>> assert 'llm_monetization_score' in analysis
            >>> assert service.stats['analyzed'] == 1
        """
        if not self.validate_input(submission):
            self.logger.error(
                f"Invalid submission: missing required fields for "
                f"{submission.get('submission_id', 'unknown')}"
            )
            self.stats["errors"] += 1
            return {}

        try:
            business_concept_id = submission.get("business_concept_id")

            # Check if should skip due to deduplication
            if self.enable_dedup and business_concept_id:
                should_run, reason = self.skip_logic.should_run_agno_analysis(
                    submission, business_concept_id
                )

                if not should_run:
                    self.logger.info(
                        f"Skipping Agno for {submission.get('submission_id', submission.get('id', 'unknown'))}: {reason}"
                    )

                    # Try to copy from primary submission
                    primary_id = self._get_primary_submission_id(business_concept_id)
                    if primary_id:
                        copied = self.skip_logic.copy_agno_analysis(
                            primary_id, submission.get("submission_id", submission.get("id", "unknown")), business_concept_id
                        )
                        if copied:
                            self.stats["copied"] += 1
                            self.logger.info(
                                f"Copied Agno analysis from {primary_id} to "
                                f"{submission.get('submission_id', submission.get('id', 'unknown'))}"
                            )
                            return copied

                    # Couldn't copy, mark as skipped
                    self.stats["skipped"] += 1
                    return {}

            # Run fresh analysis
            analysis = self._generate_analysis(submission)

            if analysis:
                self.stats["analyzed"] += 1
                self.logger.info(
                    f"Generated Agno analysis for {submission.get('submission_id', submission.get('id', 'unknown'))}: "
                    f"score={analysis.get('llm_monetization_score', 0)}, "
                    f"segment={analysis.get('customer_segment', 'unknown')}"
                )

                # Update business concept if applicable
                if business_concept_id:
                    self.skip_logic.update_concept_agno_stats(
                        business_concept_id, analysis
                    )

                return analysis
            else:
                self.stats["errors"] += 1
                return {}

        except Exception as e:
            self.logger.error(
                f"Monetization analysis error for {submission.get('submission_id', 'unknown')}: {e}",
                exc_info=True,
            )
            self.stats["errors"] += 1
            return {}

    def _generate_analysis(self, submission: dict[str, Any]) -> dict[str, Any]:
        """
        Generate fresh monetization analysis using MonetizationAgnoAnalyzer.

        Args:
            submission: Submission data dictionary

        Returns:
            dict: Generated analysis or empty dict if generation fails
        """
        try:
            # Extract fields for analyzer
            text = submission.get("text", "") or submission.get("content", "")
            subreddit = submission.get("subreddit", "")
            keyword_score = submission.get("keyword_monetization_score")

            # Generate analysis (returns MonetizationAnalysis dataclass)
            result = self.analyzer.analyze(
                text=text,
                subreddit=subreddit,
                keyword_monetization_score=keyword_score,
            )

            # Convert dataclass to dict
            analysis = asdict(result)

            # Add metadata
            analysis["submission_id"] = submission.get("submission_id", submission.get("id", "unknown"))
            analysis["business_concept_id"] = submission.get("business_concept_id")

            return analysis

        except Exception as e:
            self.logger.error(f"Error generating analysis: {e}", exc_info=True)
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
            str: Service name "MonetizationService"
        """
        return "MonetizationService"

    def validate_input(self, submission: dict[str, Any]) -> bool:
        """
        Validate submission has required fields for monetization analysis.

        Args:
            submission: Submission data dictionary

        Returns:
            bool: True if valid, False otherwise
        """
        # Base validation
        if not super().validate_input(submission):
            return False

        # Monetization analysis needs either text or content field
        has_content = bool(
            submission.get("text") or submission.get("content")
        )

        if not has_content:
            self.logger.warning(
                f"Submission {submission.get('submission_id')} missing text/content"
            )
            return False

        return True
