"""Base class for AI enrichment services.

This module provides the abstract base class for all AI enrichment services
in the unified pipeline. Each service wraps an AI component (profiler,
opportunity analyzer, monetization analyzer, etc.) and integrates deduplication
logic to preserve cost savings.

Key Features:
- Abstract interface for enrichment services
- Built-in statistics tracking
- Input validation
- Standardized error handling
- Deduplication integration hooks
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseEnrichmentService(ABC):
    """
    Abstract base class for AI enrichment services.

    All enrichment services must extend this class and implement the abstract
    methods. Provides common functionality for statistics tracking, input
    validation, and error handling.

    Attributes:
        config: Configuration dictionary for service-specific settings
        stats: Statistics tracking dict (analyzed, skipped, copied, errors)
        logger: Logger instance for the service

    Examples:
        >>> class MyService(BaseEnrichmentService):
        ...     def enrich(self, submission):
        ...         if not self.validate_input(submission):
        ...             self.stats['errors'] += 1
        ...             return {}
        ...         # Perform analysis
        ...         self.stats['analyzed'] += 1
        ...         return {'result': 'analysis'}
        ...
        ...     def get_service_name(self):
        ...         return "MyService"
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """
        Initialize enrichment service.

        Args:
            config: Optional configuration dictionary with service-specific
                settings (e.g., enable_deduplication, batch_size, etc.)
        """
        self.config = config or {}
        self.stats = {"analyzed": 0, "skipped": 0, "copied": 0, "errors": 0}
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def enrich(self, submission: dict[str, Any]) -> dict[str, Any]:
        """
        Enrich submission with AI analysis.

        This is the main method that performs the enrichment. Must be
        implemented by all subclasses.

        Args:
            submission: Submission data dictionary with required fields:
                - submission_id: Unique submission identifier
                - title: Submission title
                - subreddit: Subreddit name
                - business_concept_id: Optional concept ID for deduplication

        Returns:
            dict: Analysis results in service-specific format, or empty dict
                if analysis fails or is skipped

        Examples:
            >>> service = MyService()
            >>> result = service.enrich({
            ...     'submission_id': 'abc123',
            ...     'title': 'Need a better tool',
            ...     'subreddit': 'SaaS'
            ... })
            >>> assert 'result' in result
        """
        pass

    @abstractmethod
    def get_service_name(self) -> str:
        """
        Return service name for logging and monitoring.

        Returns:
            str: Human-readable service name (e.g., "ProfilerService",
                "MonetizationService")

        Examples:
            >>> service = MyService()
            >>> assert service.get_service_name() == "MyService"
        """
        pass

    def validate_input(self, submission: dict[str, Any]) -> bool:
        """
        Validate submission has required fields.

        Checks that the submission dictionary contains all minimum required
        fields for processing. Can be overridden by subclasses for additional
        validation.

        Args:
            submission: Submission data dictionary

        Returns:
            bool: True if valid, False otherwise

        Examples:
            >>> service = MyService()
            >>> valid = service.validate_input({
            ...     'submission_id': 'abc123',
            ...     'title': 'Test',
            ...     'subreddit': 'test'
            ... })
            >>> assert valid is True
            >>>
            >>> invalid = service.validate_input({'title': 'Test'})
            >>> assert invalid is False
        """
        required = ["title", "subreddit"]
        # Accept either submission_id or id field
        has_id = submission.get("submission_id")
        has_alt_id = submission.get("id")
        return (has_id or has_alt_id) and all(field in submission and submission[field] for field in required)

    def get_statistics(self) -> dict[str, int]:
        """
        Return service statistics.

        Provides statistics on service operations including analyses performed,
        skipped due to deduplication, copied from primary, and errors.

        Returns:
            dict: Copy of statistics dictionary with keys:
                - analyzed: Number of fresh analyses performed
                - skipped: Number of analyses skipped (deduplication)
                - copied: Number of analyses copied from primary
                - errors: Number of errors encountered

        Examples:
            >>> service = MyService()
            >>> service.enrich({'submission_id': 'test', 'title': 'Test', 'subreddit': 'test'})
            >>> stats = service.get_statistics()
            >>> assert 'analyzed' in stats
            >>> assert 'skipped' in stats
            >>> assert 'copied' in stats
            >>> assert 'errors' in stats
        """
        return self.stats.copy()

    def reset_statistics(self) -> None:
        """
        Reset service statistics to zero.

        Useful when reusing service instance for multiple batch runs.

        Examples:
            >>> service = MyService()
            >>> service.stats['analyzed'] = 10
            >>> service.reset_statistics()
            >>> assert service.stats['analyzed'] == 0
        """
        self.stats = {"analyzed": 0, "skipped": 0, "copied": 0, "errors": 0}

    def log_statistics(self) -> None:
        """
        Log current statistics.

        Provides a convenient way to log service performance metrics.

        Examples:
            >>> service = MyService()
            >>> service.enrich({'submission_id': 'test', 'title': 'Test', 'subreddit': 'test'})
            >>> service.log_statistics()
            # Logs: "MyService Statistics - Analyzed: 1, Skipped: 0, Copied: 0, Errors: 0"
        """
        self.logger.info(
            f"{self.get_service_name()} Statistics - "
            f"Analyzed: {self.stats['analyzed']}, "
            f"Skipped: {self.stats['skipped']}, "
            f"Copied: {self.stats['copied']}, "
            f"Errors: {self.stats['errors']}"
        )
