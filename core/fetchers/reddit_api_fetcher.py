"""Reddit API fetcher for retrieving submissions via PRAW.

This module provides a RedditAPIFetcher class for fetching Reddit submissions
from the Reddit API using PRAW. Extracted from core/dlt_collection.py and
scripts/dlt/dlt_trust_pipeline.py to enable code reuse across pipeline components.
"""

import os
from pathlib import Path
from typing import Any, Iterator

import praw

from core.fetchers.base_fetcher import BaseFetcher
from core.quality_filters.thresholds import PROBLEM_KEYWORDS


class RedditAPIFetcher(BaseFetcher):
    """
    Fetch submissions from Reddit API using PRAW.

    Provides problem-keyword filtering, configurable sorting, and standardized
    data formatting. Implements BaseFetcher interface for compatibility with
    unified pipeline architecture.

    Attributes:
        client: Initialized PRAW Reddit client
        config: Configuration dictionary with optional settings:
            - sort_type: Sort method for fetching ('new', 'hot', 'top', 'rising')
            - filter_keywords: Enable problem keyword filtering (default: True)
            - min_keywords: Minimum problem keywords required (default: 1)
        stats: Fetching statistics (fetched, filtered, errors)

    Examples:
        >>> import praw
        >>> reddit = praw.Reddit(client_id=..., client_secret=..., user_agent=...)
        >>> fetcher = RedditAPIFetcher(reddit, config={'sort_type': 'hot'})
        >>> for submission in fetcher.fetch(limit=50, subreddit='SaaS'):
        ...     print(f"Processing: {submission['title']}")
        >>> stats = fetcher.get_statistics()
        >>> print(f"Fetched {stats['fetched']}, Filtered {stats['filtered']}")
    """

    def __init__(self, client: praw.Reddit | None = None, config: dict[str, Any] | None = None):
        """
        Initialize Reddit API fetcher.

        Args:
            client: Initialized PRAW Reddit client. If None, creates client from env vars.
            config: Optional configuration dictionary with settings:
                - sort_type: Sort method ('new', 'hot', 'top', 'rising') (default: 'new')
                - filter_keywords: Enable keyword filtering (default: True)
                - min_keywords: Minimum problem keywords (default: 1)
        """
        super().__init__(config)
        self.client = client or self._create_client()
        self.sort_type = self.config.get("sort_type", "new")
        self.filter_keywords = self.config.get("filter_keywords", True)
        self.min_keywords = self.config.get("min_keywords", 1)

    def _create_client(self) -> praw.Reddit:
        """
        Create PRAW Reddit client from environment variables.

        Reads REDDIT_PUBLIC, REDDIT_SECRET, and REDDIT_USER_AGENT from .env file
        or environment variables.

        Returns:
            praw.Reddit: Initialized Reddit client

        Raises:
            ValueError: If required credentials are missing
        """
        # Try to load from .env file if exists
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / ".env"

        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        key, val = line.split("=", 1)
                        if key not in os.environ:  # Don't override existing env vars
                            os.environ[key] = val

        reddit_public = os.getenv("REDDIT_PUBLIC")
        reddit_secret = os.getenv("REDDIT_SECRET")
        reddit_user_agent = os.getenv("REDDIT_USER_AGENT")

        if not all([reddit_public, reddit_secret, reddit_user_agent]):
            raise ValueError(
                "Missing Reddit API credentials. Set REDDIT_PUBLIC, REDDIT_SECRET, "
                "and REDDIT_USER_AGENT environment variables."
            )

        return praw.Reddit(
            client_id=reddit_public,
            client_secret=reddit_secret,
            user_agent=reddit_user_agent,
        )

    def fetch(
        self, limit: int, subreddit: str | None = None, subreddits: list[str] | None = None, **kwargs
    ) -> Iterator[dict[str, Any]]:
        """
        Fetch submissions from Reddit API.

        Retrieves submissions from specified subreddit(s) with optional
        problem keyword filtering and configurable sorting.

        Args:
            limit: Maximum number of submissions to fetch per subreddit
            subreddit: Single subreddit name (e.g., 'SaaS')
            subreddits: List of subreddit names (alternative to single subreddit)
            **kwargs: Additional parameters (reserved for future use)

        Yields:
            dict: Formatted submission data in standardized format

        Raises:
            ValueError: If neither subreddit nor subreddits is provided
            Exception: If Reddit API call fails

        Examples:
            >>> # Fetch from single subreddit
            >>> for sub in fetcher.fetch(limit=50, subreddit='SaaS'):
            ...     process(sub)
            >>> # Fetch from multiple subreddits
            >>> for sub in fetcher.fetch(limit=25, subreddits=['SaaS', 'startups']):
            ...     process(sub)
        """
        # Validate input
        if not subreddit and not subreddits:
            raise ValueError("Must provide either 'subreddit' or 'subreddits' parameter")

        # Convert single subreddit to list
        target_subreddits = [subreddit] if subreddit else subreddits

        try:
            for sub_name in target_subreddits:
                yield from self._fetch_from_subreddit(sub_name, limit)

        except Exception as e:
            self.stats["errors"] += 1
            raise Exception(f"Reddit API fetch failed: {e}") from e

    def _fetch_from_subreddit(self, subreddit_name: str, limit: int) -> Iterator[dict[str, Any]]:
        """
        Fetch submissions from a single subreddit.

        Args:
            subreddit_name: Name of subreddit (without 'r/')
            limit: Maximum number of submissions to fetch

        Yields:
            dict: Formatted submission data

        Raises:
            Exception: If subreddit access fails
        """
        try:
            subreddit = self.client.subreddit(subreddit_name)

            # Get submissions based on sort type
            if self.sort_type == "new":
                submissions = subreddit.new(limit=limit)
            elif self.sort_type == "hot":
                submissions = subreddit.hot(limit=limit)
            elif self.sort_type == "top":
                submissions = subreddit.top(limit=limit)
            elif self.sort_type == "rising":
                submissions = subreddit.rising(limit=limit)
            else:
                # Default to 'new' if unknown sort type
                submissions = subreddit.new(limit=limit)

            for submission in submissions:
                # Apply problem keyword filtering if enabled
                if self.filter_keywords:
                    full_text = f"{submission.title} {submission.selftext}"
                    if not self._contains_problem_keywords(full_text):
                        self.stats["filtered"] += 1
                        continue

                # Format submission
                formatted = self._format_submission(submission, subreddit_name)

                # Validate
                if self.validate_submission(formatted):
                    self.stats["fetched"] += 1
                    yield formatted
                else:
                    self.stats["filtered"] += 1

        except Exception as e:
            self.stats["errors"] += 1
            raise Exception(f"Error fetching from r/{subreddit_name}: {e}") from e

    def _contains_problem_keywords(self, text: str) -> bool:
        """
        Check if text contains minimum required problem keywords.

        Args:
            text: Text to check (title + selftext)

        Returns:
            bool: True if text contains >= min_keywords problem keywords
        """
        if not text:
            return False

        text_lower = text.lower()
        found_count = sum(1 for keyword in PROBLEM_KEYWORDS if keyword in text_lower)
        return found_count >= self.min_keywords

    def _format_submission(self, submission: praw.models.Submission, subreddit_name: str) -> dict[str, Any]:
        """
        Format PRAW submission to standardized format.

        Transforms Reddit API submission object to the standardized format
        used across the pipeline, matching the database schema.

        Args:
            submission: PRAW submission object
            subreddit_name: Name of subreddit

        Returns:
            dict: Formatted submission data
        """
        from datetime import datetime

        # Get ISO datetime string for created_at
        created_at = datetime.fromtimestamp(submission.created_utc).isoformat()

        return {
            "submission_id": submission.id,
            "title": submission.title,
            "text": submission.selftext,
            "content": submission.selftext,  # Alias for compatibility
            "subreddit": subreddit_name,
            "upvotes": submission.score,
            "reddit_score": submission.score,  # Alias for compatibility
            "num_comments": submission.num_comments,
            "comments_count": submission.num_comments,  # Alias for compatibility
            "url": submission.url,
            "created_at": created_at,
            "created_utc": submission.created_utc,  # Keep Unix timestamp too
        }

    def get_source_name(self) -> str:
        """
        Return human-readable source name.

        Returns:
            str: Source identifier for logging and monitoring
        """
        return f"Reddit API ({self.sort_type})"

    def validate_submission(self, submission: dict[str, Any]) -> bool:
        """
        Validate submission has required fields for Reddit API data.

        Checks for essential fields needed for AI analysis and processing.
        Overrides base class to provide Reddit-specific validation.

        Args:
            submission: Submission data from Reddit API

        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ["submission_id", "title", "subreddit"]
        return all(
            field in submission and submission[field] for field in required_fields
        )
