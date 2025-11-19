"""Abstract base class for data fetchers."""
from abc import ABC, abstractmethod
from typing import Any, Iterator


class BaseFetcher(ABC):
    """Abstract base class for data fetchers."""

    @abstractmethod
    def fetch(self, limit: int, **kwargs) -> Iterator[dict[str, Any]]:
        """
        Fetch submissions from data source.

        Args:
            limit: Maximum number of submissions to fetch
            **kwargs: Additional source-specific parameters

        Yields:
            dict: Submission data in standardized format
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Return human-readable source name."""
        pass

    def validate_submission(self, submission: dict[str, Any]) -> bool:
        """
        Validate submission has required fields.

        Args:
            submission: Submission data to validate

        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ["submission_id", "title", "content", "subreddit"]
        return all(field in submission for field in required_fields)
