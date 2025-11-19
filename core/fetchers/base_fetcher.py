"""Abstract base class for data fetchers."""
from abc import ABC, abstractmethod
from typing import Any, Iterator, Optional


class BaseFetcher(ABC):
    """
    Abstract base class for data fetchers.

    Provides common interface for fetching submissions from different sources
    (database, Reddit API, etc.) with standardized data format and statistics tracking.

    Attributes:
        config: Configuration dictionary for fetcher-specific settings
        stats: Dictionary tracking fetching statistics (fetched, filtered, errors)
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """
        Initialize the fetcher with optional configuration.

        Args:
            config: Configuration dictionary with fetcher-specific settings
        """
        self.config = config or {}
        self.stats = {"fetched": 0, "filtered": 0, "errors": 0}

    @abstractmethod
    def fetch(self, limit: int, **kwargs) -> Iterator[dict[str, Any]]:
        """
        Fetch submissions from data source.

        Args:
            limit: Maximum number of submissions to fetch
            **kwargs: Additional source-specific parameters

        Yields:
            dict: Submission data in standardized format

        Raises:
            Exception: If fetching fails
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """
        Return human-readable source name.

        Returns:
            str: Source identifier (e.g., "Database (submissions)", "Reddit API")
        """
        pass

    def validate_submission(self, submission: dict[str, Any]) -> bool:
        """
        Validate submission has required fields.

        Checks that submission contains minimum required fields for processing.
        Can be overridden by subclasses for source-specific validation.

        Args:
            submission: Submission data to validate

        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ["submission_id", "title", "subreddit"]
        return all(field in submission and submission[field] for field in required_fields)

    def get_statistics(self) -> dict[str, int]:
        """
        Return fetching statistics.

        Returns:
            dict: Copy of statistics dictionary with keys:
                - fetched: Number of successfully fetched submissions
                - filtered: Number of submissions filtered out
                - errors: Number of errors encountered

        Examples:
            >>> fetcher = DatabaseFetcher(client)
            >>> submissions = list(fetcher.fetch(limit=100))
            >>> stats = fetcher.get_statistics()
            >>> print(f"Fetched: {stats['fetched']}, Errors: {stats['errors']}")
        """
        return self.stats.copy()

    def reset_statistics(self) -> None:
        """
        Reset fetching statistics to zero.

        Useful when reusing a fetcher instance for multiple fetch operations.
        """
        self.stats = {"fetched": 0, "filtered": 0, "errors": 0}

