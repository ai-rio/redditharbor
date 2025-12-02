"""Opportunity Analysis enrichment service.

This module provides a wrapper for OpportunityAnalyzerAgent with the unified
enrichment service interface. Analyzes Reddit submissions using 5-dimensional
scoring methodology to identify app opportunities.

Key Features:
- Wraps OpportunityAnalyzerAgent for unified interface
- 5-dimensional scoring: market demand, pain intensity, monetization, market gap, technical feasibility
- Generates core function suggestions
- No deduplication (runs on all submissions)
- Tracks statistics (analyzed, errors)
- Handles errors gracefully
"""

import logging
from typing import Any, Optional

from core.agents.interactive.opportunity_analyzer import OpportunityAnalyzerAgent
from core.enrichment.base_service import BaseEnrichmentService

logger = logging.getLogger(__name__)


class OpportunityService(BaseEnrichmentService):
    """
    Wrapper for OpportunityAnalyzerAgent with unified interface.

    Provides opportunity analysis using 5-dimensional scoring methodology.
    No deduplication logic - runs on all submissions as opportunities are
    unique per submission.

    Attributes:
        analyzer: OpportunityAnalyzerAgent instance

    Examples:
        >>> from core.agents.interactive.opportunity_analyzer import OpportunityAnalyzerAgent
        >>>
        >>> analyzer = OpportunityAnalyzerAgent()
        >>> service = OpportunityService(analyzer)
        >>>
        >>> submission = {
        ...     'submission_id': 'abc123',
        ...     'title': 'Need better budgeting app',
        ...     'text': 'Current apps are too expensive and complicated',
        ...     'subreddit': 'personalfinance',
        ...     'upvotes': 245,
        ...     'num_comments': 87
        ... }
        >>> analysis = service.enrich(submission)
        >>> assert 'final_score' in analysis
        >>> assert 'dimension_scores' in analysis
    """

    def __init__(
        self,
        analyzer: OpportunityAnalyzerAgent,
        config: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize OpportunityService.

        Args:
            analyzer: OpportunityAnalyzerAgent instance for opportunity analysis
            config: Optional configuration dictionary (reserved for future use)
        """
        super().__init__(config)
        self.analyzer = analyzer

    def enrich(self, submission: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze opportunity using 5-dimensional scoring.

        Evaluates market demand, pain intensity, monetization potential,
        market gap, and technical feasibility. Generates core function
        suggestions and overall priority score.

        Args:
            submission: Submission data dictionary with fields:
                - submission_id: Unique identifier
                - title: Submission title
                - text: Submission content
                - subreddit: Subreddit name
                - upvotes: Number of upvotes (optional)
                - num_comments: Number of comments (optional)
                - comments: List of comment texts (optional)

        Returns:
            dict: Opportunity analysis with fields:
                - opportunity_id: Submission ID
                - title: Truncated title
                - subreddit: Subreddit name
                - dimension_scores: Dict with 5 dimension scores
                - final_score: Weighted overall score (0-100)
                - priority: Priority level string
                - weights: Dimension weight configuration
                - core_functions: List of 1-3 suggested functions
                - function_count: Number of core functions
                - timestamp: Analysis timestamp
                Or empty dict if error occurs

        Examples:
            >>> submission = {
            ...     'submission_id': 'test1',
            ...     'title': 'Looking for project management tool',
            ...     'text': 'Frustrated with current tools, too complex',
            ...     'subreddit': 'startups',
            ...     'upvotes': 100,
            ...     'num_comments': 50
            ... }
            >>> analysis = service.enrich(submission)
            >>> assert analysis['final_score'] > 0
            >>> assert len(analysis['core_functions']) in [1, 2, 3]
        """
        if not self.validate_input(submission):
            self.logger.error(
                f"Invalid submission: missing required fields for "
                f"{submission.get('submission_id', submission.get('id', 'unknown'))}"
            )
            self.stats["errors"] += 1
            return {}

        try:
            # Format submission data for analyzer
            analyzer_input = self._format_analyzer_input(submission)

            # Run opportunity analysis (no deduplication)
            result = self.analyzer.analyze_opportunity(analyzer_input)

            if result and "final_score" in result:
                self.stats["analyzed"] += 1
                self.logger.info(
                    f"Analyzed opportunity for {submission.get('submission_id', submission.get('id', 'unknown'))}: "
                    f"score={result.get('final_score', 0)}, "
                    f"priority={result.get('priority', 'unknown')}"
                )
                return result
            else:
                self.stats["errors"] += 1
                self.logger.warning(
                    f"Analyzer returned invalid result for {submission.get('submission_id', submission.get('id', 'unknown'))}"
                )
                return {}

        except Exception as e:
            self.logger.error(
                f"Opportunity analysis error for {submission.get('submission_id', submission.get('id', 'unknown'))}: {e}",
                exc_info=True,
            )
            self.stats["errors"] += 1
            return {}

    def _format_analyzer_input(self, submission: dict[str, Any]) -> dict[str, Any]:
        """
        Format submission data for OpportunityAnalyzerAgent.

        Transforms enrichment service input format to analyzer's expected format.

        Args:
            submission: Submission data from enrichment pipeline

        Returns:
            dict: Formatted data for analyzer with fields:
                - id: submission_id
                - title: title
                - text: text or content
                - subreddit: subreddit
                - engagement: dict with upvotes, num_comments
                - comments: list of comment texts
        """
        # Extract text (support both 'text' and 'content' fields)
        text = submission.get("text", "") or submission.get("content", "")

        # Format engagement data
        engagement = {
            "upvotes": submission.get("upvotes", 0),
            "num_comments": submission.get("num_comments", 0),
        }

        # Extract comments if available
        comments = submission.get("comments", [])
        if not isinstance(comments, list):
            comments = []

        return {
            "id": submission.get("submission_id", submission.get("id")),
            "title": submission["title"],
            "text": text,
            "subreddit": submission["subreddit"],
            "engagement": engagement,
            "comments": comments,
        }

    def validate_input(self, submission: dict[str, Any]) -> bool:
        """
        Validate submission has required fields for opportunity analysis.

        Args:
            submission: Submission data dictionary

        Returns:
            bool: True if valid, False otherwise
        """
        # Base validation (submission_id, title, subreddit)
        if not super().validate_input(submission):
            return False

        # Opportunity analysis needs either text or content field
        has_content = bool(submission.get("text") or submission.get("content"))

        if not has_content:
            self.logger.warning(
                f"Submission {submission.get('submission_id')} missing text/content"
            )
            return False

        return True

    def get_service_name(self) -> str:
        """
        Return service name for logging.

        Returns:
            str: Service name "OpportunityService"
        """
        return "OpportunityService"
