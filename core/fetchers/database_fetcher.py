"""Database fetcher for retrieving submissions from Supabase.

This module provides a DatabaseFetcher class for fetching Reddit submissions
from the submissions table in Supabase. Extracted from
scripts/core/batch_opportunity_scoring.py to enable code reuse across pipeline
components.
"""

from typing import Any, Iterator

from core.fetchers.base_fetcher import BaseFetcher
from core.fetchers.formatters import format_submission_for_agent


class DatabaseFetcher(BaseFetcher):
    """
    Fetch submissions from Supabase submissions table.

    Provides efficient batch fetching with pagination, content-based deduplication,
    and standardized data formatting. Implements BaseFetcher interface for
    compatibility with unified pipeline architecture.

    Attributes:
        client: Initialized Supabase client
        config: Configuration dictionary with optional settings:
            - batch_size: Number of records per batch (default: 1000)
            - deduplicate: Enable content-based deduplication (default: True)
            - table_name: Database table name (default: "submissions")
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
                - table_name: Table to query (default: "submissions")
                - use_orm: Use SQLAlchemy ORM instead of REST queries (default: False)
                - id_field: Field to use as primary identifier (default: "id")
        """
        super().__init__(config)
        self.client = client
        self.batch_size = self.config.get("batch_size", 1000)
        self.deduplicate = self.config.get("deduplicate", True)
        self.table_name = self.config.get("table_name", "submissions")
        self.use_orm = self.config.get("use_orm", False)
        self.id_field = self.config.get("id_field", "id")

    def fetch(self, limit: int | None = None, **kwargs) -> Iterator[dict[str, Any]]:
        """
        Fetch submissions from database.

        Retrieves submissions from database table with optional limit.
        Supports both REST (Supabase) and ORM (SQLAlchemy) modes.
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
            if self.use_orm:
                # Use SQLAlchemy ORM mode
                yield from self._fetch_orm(limit)
            else:
                # Use original REST mode
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
            # Build column list based on table name for backward compatibility
            if self.table_name == "submissions":
                # New schema: id (UUID), reddit_id, content, score, num_comments
                columns = "id, reddit_id, title, content, score, num_comments, created_at, url"
            else:
                # Legacy schema: submission_id, subreddit, reddit_score, selftext
                columns = (
                    "submission_id, title, content, subreddit, reddit_score, "
                    "num_comments, trust_score, trust_level, created_utc, author, selftext"
                )

            query = (
                self.client.table(self.table_name)
                .select(columns)
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
                # Build column list based on table name for backward compatibility
                if self.table_name == "submissions":
                    # New schema: id (UUID), reddit_id, content, score, num_comments
                    columns = "id, reddit_id, title, content, score, num_comments, created_at, url"
                else:
                    # Legacy schema: submission_id, subreddit, reddit_score, selftext
                    columns = (
                        "submission_id, title, content, subreddit, reddit_score, "
                        "num_comments, trust_score, trust_level, created_utc, author, selftext"
                    )

                # Build query with pagination
                query = (
                    self.client.table(self.table_name)
                    .select(columns)
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

    def _fetch_orm(self, limit: int | None = None) -> Iterator[dict[str, Any]]:
        """
        Fetch submissions using SQLAlchemy ORM.

        Retrieves submissions using the configured ORM model instead of
        hardcoded REST queries. This allows for dynamic schema introspection
        and proper field mapping.

        Args:
            limit: Maximum number of submissions to fetch. None = fetch all.

        Yields:
            dict: Formatted submission data in standardized format

        Raises:
            Exception: If ORM query fails
        """
        try:
            # Import ORM components only when needed
            from core.db import get_db_session, Submission
            from sqlalchemy import select

            with get_db_session() as session:
                # Build query
                if self.table_name == "submissions":
                    stmt = select(Submission)

                    # Apply limit if specified
                    if limit:
                        stmt = stmt.limit(limit)

                    # Execute query
                    result = session.execute(stmt)
                    submissions = result.scalars().all()

                    # Convert ORM objects to dictionaries and format
                    for submission in submissions:
                        # Skip None submissions (possible NULL records)
                        if submission is None:
                            continue

                        submission_dict = submission.to_dict()

                        # Convert UUID objects to strings for JSON compatibility
                        for key, value in submission_dict.items():
                            if hasattr(value, 'hex'):  # UUID object
                                submission_dict[key] = str(value)

                        # Use configured id field for validation
                        if self.validate_submission_orm(submission_dict):
                            self.stats["fetched"] += 1
                            # In ORM mode, don't use legacy fields to test dynamic schema handling
                            yield format_submission_for_agent(submission_dict, use_legacy_fields=False)
                        else:
                            self.stats["filtered"] += 1
                else:
                    # For other tables, fall back to original method or raise error
                    raise ValueError(f"ORM mode not supported for table: {self.table_name}")

        except Exception as e:
            self.stats["errors"] += 1
            raise Exception(f"ORM fetch failed: {e}") from e

    def validate_submission_orm(self, submission: dict[str, Any]) -> bool:
        """
        Validate submission has required fields for ORM records.

        Args:
            submission: Submission data from ORM

        Returns:
            bool: True if valid, False otherwise
        """
        # Use configured id field instead of hardcoded submission_id
        # NOTE: Database has subreddit_id (UUID), not subreddit (string)
        # subreddit_id can be None in our current data, so don't require it
        required_fields = [self.id_field, "title"]
        return all(
            field in submission and submission[field] for field in required_fields
        )

    def validate_submission(self, submission: dict[str, Any]) -> bool:
        """
        Validate submission has required fields for database records.

        Checks for essential fields needed for AI analysis and processing.
        Overrides base class to provide database-specific validation.
        Supports both legacy (submission_id, subreddit) and new (id, reddit_id) schemas.

        Args:
            submission: Submission data from database

        Returns:
            bool: True if valid, False otherwise
        """
        # Must have title
        if "title" not in submission or not submission["title"]:
            return False

        # Check for ID field - support both legacy and new schemas
        has_id = (
            ("submission_id" in submission and submission["submission_id"]) or
            ("id" in submission and submission["id"]) or
            ("reddit_id" in submission and submission["reddit_id"])
        )

        if not has_id:
            return False

        # For legacy schema, require subreddit field
        # For new schema, subreddit_id is optional
        if "submission_id" in submission:
            # Legacy schema validation
            return "subreddit" in submission and submission["subreddit"]

        # New schema validation - just needs id and title
        return True
