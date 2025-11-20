"""Database fetcher for retrieving submissions from Supabase.

This module provides a DatabaseFetcher class for fetching Reddit submissions
from the app_opportunities table in Supabase. Extracted from
scripts/core/batch_opportunity_scoring.py to enable code reuse across pipeline
components.
"""

from typing import Any, Iterator

from core.fetchers.base_fetcher import BaseFetcher
from core.fetchers.formatters import format_submission_for_agent


class DatabaseFetcher(BaseFetcher):
    """
    Fetch submissions from Supabase app_opportunities table.

    Provides efficient batch fetching with pagination, content-based deduplication,
    and standardized data formatting. Implements BaseFetcher interface for
    compatibility with unified pipeline architecture.

    Attributes:
        client: Initialized Supabase client
        config: Configuration dictionary with optional settings:
            - batch_size: Number of records per batch (default: 1000)
            - deduplicate: Enable content-based deduplication (default: True)
            - table_name: Database table name (default: "app_opportunities")
        stats: Fetching statistics (fetched, filtered, errors)

    Examples:
        >>> from supabase import create_client
        >>> client = create_client(url, key)
        >>> fetcher = DatabaseFetcher(client, config={"batch_size": 500})
        >>> for submission in fetcher.fetch(limit=100):
        ...     print(f"Processing: {submission['title']}")
        >>> stats = fetcher.get_statistics()
        >>> print(f"Fetched {stats['fetched']}, Filtered {stats['filtered']}")
    """

    # Filler words to remove when creating title signatures for deduplication
    FILLER_WORDS = {
        "i",
        "my",
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "can",
        "must",
        "shall",
    }

    def __init__(self, client: Any, config: dict[str, Any] | None = None):
        """
        Initialize database fetcher with Supabase client.

        Args:
            client: Initialized Supabase client
            config: Optional configuration dictionary with settings:
                - batch_size: Records per batch (default: 1000)
                - deduplicate: Enable deduplication (default: True)
                - table_name: Table to query (default: "app_opportunities")
        """
        super().__init__(config)
        self.client = client
        self.batch_size = self.config.get("batch_size", 1000)
        self.deduplicate = self.config.get("deduplicate", True)
        self.table_name = self.config.get("table_name", "app_opportunities")

    def fetch(self, limit: int | None = None, **kwargs) -> Iterator[dict[str, Any]]:
        """
        Fetch submissions from database.

        Retrieves submissions from app_opportunities table with optional limit.
        Supports batch fetching, content-based deduplication, and automatic
        formatting for AI analysis.

        Args:
            limit: Maximum number of submissions to fetch. None = fetch all.
            **kwargs: Reserved for future use

        Yields:
            dict: Formatted submission data in standardized format

        Raises:
            Exception: If database query fails

        Examples:
            >>> fetcher = DatabaseFetcher(client)
            >>> # Fetch limited submissions
            >>> for sub in fetcher.fetch(limit=50):
            ...     process(sub)
            >>> # Fetch all submissions
            >>> all_subs = list(fetcher.fetch())
        """
        try:
            if limit:
                # Simple fetch for limited results
                yield from self._fetch_limited(limit)
            else:
                # Batch fetch with deduplication for unlimited results
                yield from self._fetch_all()

        except Exception as e:
            self.stats["errors"] += 1
            raise Exception(f"Database fetch failed: {e}") from e

    def _fetch_limited(self, limit: int) -> Iterator[dict[str, Any]]:
        """
        Fetch limited number of submissions without deduplication.

        Args:
            limit: Maximum number of submissions to fetch

        Yields:
            dict: Formatted submission data

        Raises:
            Exception: If query fails
        """
        try:
            query = (
                self.client.table(self.table_name)
                .select(
                    "submission_id, title, content, subreddit, reddit_score, "
                    "num_comments, trust_score, trust_level, created_utc, author, selftext"
                )
                .limit(limit)
            )

            response = query.execute()

            if not response.data:
                return

            for submission in response.data:
                if self.validate_submission(submission):
                    self.stats["fetched"] += 1
                    yield format_submission_for_agent(submission)
                else:
                    self.stats["filtered"] += 1

        except Exception as e:
            self.stats["errors"] += 1
            raise Exception(f"Limited fetch failed: {e}") from e

    def _fetch_all(self) -> Iterator[dict[str, Any]]:
        """
        Fetch all submissions in batches with content-based deduplication.

        Retrieves all submissions using pagination and applies title-based
        deduplication to remove cross-posted content.

        Yields:
            dict: Unique, formatted submission data

        Raises:
            Exception: If batch fetching fails
        """
        try:
            offset = 0
            seen_titles = set() if self.deduplicate else None
            total_fetched = 0
            total_filtered = 0

            while True:
                # Build query with pagination
                query = (
                    self.client.table(self.table_name)
                    .select(
                        "submission_id, title, content, subreddit, reddit_score, "
                        "num_comments, trust_score, trust_level, created_utc, author, selftext"
                    )
                    .range(offset, offset + self.batch_size - 1)
                )

                response = query.execute()

                if not response.data:
                    break  # No more submissions

                batch_count = 0
                for submission in response.data:
                    total_fetched += 1

                    # Validate submission
                    if not self.validate_submission(submission):
                        total_filtered += 1
                        continue

                    # Apply deduplication if enabled
                    if self.deduplicate:
                        if self._is_duplicate(submission, seen_titles):
                            total_filtered += 1
                            continue

                    batch_count += 1
                    self.stats["fetched"] += 1
                    yield format_submission_for_agent(submission)

                # If we got fewer than batch_size, we've reached the end
                if len(response.data) < self.batch_size:
                    break

                offset += self.batch_size

            # Update filtered count
            self.stats["filtered"] = total_filtered

        except Exception as e:
            self.stats["errors"] += 1
            raise Exception(f"Batch fetch failed: {e}") from e

    def _is_duplicate(
        self, submission: dict[str, Any], seen_titles: set[tuple[str, ...]]
    ) -> bool:
        """
        Check if submission is a duplicate based on title signature.

        Creates a normalized title signature by removing filler words and
        comparing with previously seen titles. This catches cross-posts
        which typically have identical titles.

        Args:
            submission: Submission data to check
            seen_titles: Set of previously seen title signatures

        Returns:
            bool: True if duplicate, False if unique
        """
        title = submission.get("title", "").strip().lower()

        # Create title signature from meaningful words only
        title_words = set(title.split())
        title_signature = tuple(sorted(title_words - self.FILLER_WORDS))

        if title_signature in seen_titles:
            return True

        seen_titles.add(title_signature)
        return False

    def get_source_name(self) -> str:
        """
        Return human-readable source name.

        Returns:
            str: Source identifier for logging and monitoring
        """
        return f"Database ({self.table_name})"

    def validate_submission(self, submission: dict[str, Any]) -> bool:
        """
        Validate submission has required fields for database records.

        Checks for essential fields needed for AI analysis and processing.
        Overrides base class to provide database-specific validation.

        Args:
            submission: Submission data from database

        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ["submission_id", "title", "subreddit"]
        return all(
            field in submission and submission[field] for field in required_fields
        )
