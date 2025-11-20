"""Market validation enrichment service.

This module provides a wrapper for MarketDataValidator with the unified
enrichment service interface. Validates market opportunities using real
market data including competitor pricing, market size, and launch metrics.

Key Features:
- Wraps MarketDataValidator for unified interface
- Evidence-based validation with citations
- No deduplication (runs on all submissions)
- Tracks statistics (analyzed, errors)
- Handles errors gracefully
"""

import logging
from typing import Any, Optional

from core.agents.market_validation import MarketDataValidator
from core.enrichment.base_service import BaseEnrichmentService

logger = logging.getLogger(__name__)


class MarketValidationService(BaseEnrichmentService):
    """
    Wrapper for MarketDataValidator with unified interface.

    Provides market validation using real market data including competitor
    pricing analysis, market size estimation, and similar product launches.
    No deduplication logic - market validation runs on all submissions.

    Attributes:
        validator: MarketDataValidator instance

    Examples:
        >>> from core.agents.market_validation import MarketDataValidator
        >>>
        >>> validator = MarketDataValidator()
        >>> service = MarketValidationService(validator)
        >>>
        >>> submission = {
        ...     'submission_id': 'abc123',
        ...     'title': 'Need better budgeting app',
        ...     'selftext': 'Current apps too expensive',
        ...     'subreddit': 'personalfinance',
        ...     'problem_description': 'Expensive budgeting tools'
        ... }
        >>> validation = service.enrich(submission)
        >>> assert 'market_validation_score' in validation
        >>> assert 'market_data_quality' in validation
    """

    def __init__(
        self,
        validator: MarketDataValidator,
        config: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize MarketValidationService.

        Args:
            validator: MarketDataValidator instance for market validation
            config: Optional configuration dictionary with settings:
                - max_searches: Maximum web searches (default: 3)
        """
        super().__init__(config)
        self.validator = validator

    def enrich(self, submission: dict[str, Any]) -> dict[str, Any]:
        """
        Validate market opportunity using real market data.

        Analyzes market validation evidence including competitor pricing,
        market size data, similar product launches, and industry benchmarks.
        Uses web search and LLM extraction for evidence collection.

        Args:
            submission: Submission data dictionary with fields:
                - submission_id: Unique identifier
                - title: Submission title
                - selftext: Submission content (or text)
                - subreddit: Subreddit name (used as target market)
                - problem_description: Problem being solved (from opportunity analysis)

        Returns:
            dict: Market validation with fields:
                - market_validation_score: Overall validation score (0-100)
                - market_data_quality: Data quality score (0-100)
                - competitor_count: Number of competitors found
                - market_size_estimate: Market size description (if available)
                - similar_launches_count: Number of similar launches found
                - validation_reasoning: Human-readable reasoning
                - evidence_urls: List of source URLs used
                - total_cost: LLM cost for extraction
                Or empty dict if error occurs or validation skipped

        Examples:
            >>> submission = {
            ...     'submission_id': 'test1',
            ...     'title': 'Looking for project management tool',
            ...     'selftext': 'Frustrated with current tools',
            ...     'subreddit': 'startups',
            ...     'problem_description': 'Complex project management'
            ... }
            >>> validation = service.enrich(submission)
            >>> assert validation['market_validation_score'] >= 0
            >>> assert 'evidence_urls' in validation
        """
        if not self.validate_input(submission):
            self.logger.error(
                f"Invalid submission: missing required fields for "
                f"{submission.get('submission_id', 'unknown')}"
            )
            self.stats["errors"] += 1
            return {}

        try:
            # Extract required fields from submission
            submission_id = submission.get("submission_id", "unknown")

            # Get problem description from opportunity analysis or fallback to title
            problem_description = submission.get("problem_description")
            if not problem_description:
                # If no problem_description, use title + selftext
                title = submission.get("title", "")
                selftext = submission.get("selftext") or submission.get("text", "")
                problem_description = f"{title} {selftext}".strip()

                if not problem_description:
                    self.logger.warning(
                        f"No problem description for {submission_id}, skipping market validation"
                    )
                    self.stats["skipped"] += 1
                    return {}

            # Extract app concept (use title as concept)
            app_concept = submission.get("title", "App concept")

            # Use subreddit as target market indicator
            target_market = submission.get("subreddit", "General")

            # Get max searches from config
            max_searches = self.config.get("max_searches", 3)

            self.logger.info(
                f"Running market validation for {submission_id}: {app_concept[:50]}"
            )

            # Call validator with correct method
            evidence = self.validator.validate_opportunity(
                app_concept=app_concept,
                target_market=target_market,
                problem_description=problem_description,
                max_searches=max_searches
            )

            self.stats["analyzed"] += 1

            # Format result for storage
            result = {
                "market_validation_score": evidence.validation_score,
                "market_data_quality": evidence.data_quality_score,
                "competitor_count": len(evidence.competitor_pricing),
                "market_size_estimate": None,
                "similar_launches_count": len(evidence.similar_launches),
                "validation_reasoning": evidence.reasoning,
                "evidence_urls": evidence.urls_fetched,
                "total_cost": evidence.total_cost,
            }

            # Add market size if available
            if evidence.market_size:
                market_size_parts = []
                if evidence.market_size.tam_value:
                    market_size_parts.append(f"TAM: {evidence.market_size.tam_value}")
                if evidence.market_size.sam_value:
                    market_size_parts.append(f"SAM: {evidence.market_size.sam_value}")
                if evidence.market_size.growth_rate:
                    market_size_parts.append(f"Growth: {evidence.market_size.growth_rate}")

                if market_size_parts:
                    result["market_size_estimate"] = ", ".join(market_size_parts)

            self.logger.info(
                f"Market validation complete for {submission_id}: "
                f"Score={result['market_validation_score']:.1f}, "
                f"Quality={result['market_data_quality']:.1f}, "
                f"Competitors={result['competitor_count']}"
            )

            return result

        except Exception as e:
            self.logger.error(
                f"Market validation failed for {submission.get('submission_id', 'unknown')}: {e}",
                exc_info=True
            )
            self.stats["errors"] += 1
            return {}

    def get_service_name(self) -> str:
        """
        Return service name for logging and monitoring.

        Returns:
            str: Human-readable service name

        Examples:
            >>> service = MarketValidationService(validator)
            >>> assert service.get_service_name() == "MarketValidationService"
        """
        return "MarketValidationService"
