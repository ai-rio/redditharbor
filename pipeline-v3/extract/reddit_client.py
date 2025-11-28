"""
Reddit API client using PRAW for data extraction with proper error handling
"""

import logging
from datetime import datetime, UTC
from typing import List

import praw
from prawcore import ResponseException, NotFound, Forbidden

from config import get_settings
from models import RedditSubmission

logger = logging.getLogger(__name__)


class RedditClient:
    """
    Reddit API client wrapper using PRAW for safe data extraction
    """

    def __init__(self):
        """Initialize Reddit client with credentials from settings"""
        self.settings = get_settings()
        self._reddit = None

    @property
    def reddit(self) -> praw.Reddit:
        """Lazy initialization of Reddit client"""
        if self._reddit is None:
            try:
                self._reddit = praw.Reddit(
                    client_id=self.settings.reddit_client_id,
                    client_secret=self.settings.reddit_client_secret,
                    user_agent=self.settings.reddit_user_agent,
                    read_only=True  # We only need to read data
                )

                # Test authentication
                self._reddit.user.me()
                logger.info("✓ Reddit API authentication successful")

            except Exception as e:
                logger.error(f"Reddit API initialization failed: {e}")
                raise RuntimeError(f"Failed to initialize Reddit client: {e}")

        return self._reddit

    def fetch_submissions(
        self,
        subreddits: List[str],
        limit: int,
        sort_by: str = "hot",
        time_filter: str = "week"
    ) -> List[RedditSubmission]:
        """
        Fetch Reddit submissions from specified subreddits

        Args:
            subreddits: List of subreddit names to fetch from
            limit: Maximum number of submissions to fetch per subreddit
            sort_by: Sorting method ('hot', 'top', 'new')
            time_filter: Time filter for 'top' sort ('hour', 'day', 'week', 'month', 'year', 'all')

        Returns:
            List of validated RedditSubmission objects

        Raises:
            ValueError: If invalid parameters provided
            RuntimeError: If API calls fail
        """
        logger.info(f"Fetching submissions from {subreddits} (limit={limit}, sort={sort_by})")

        if not subreddits:
            raise ValueError("At least one subreddit must be specified")

        if limit <= 0:
            raise ValueError("Limit must be positive")

        valid_sort_methods = ["hot", "top", "new"]
        if sort_by not in valid_sort_methods:
            raise ValueError(f"sort_by must be one of {valid_sort_methods}")

        submissions = []
        total_fetched = 0
        errors = []

        for subreddit_name in subreddits:
            try:
                # Get subreddit object
                subreddit = self.reddit.subreddit(subreddit_name)

                # Choose sorting method
                if sort_by == "hot":
                    submission_iter = subreddit.hot(limit=limit)
                elif sort_by == "top":
                    submission_iter = subreddit.top(time_filter=time_filter, limit=limit)
                else:  # new
                    submission_iter = subreddit.new(limit=limit)

                # Process submissions
                subreddit_count = 0
                for submission in submission_iter:
                    if total_fetched >= limit * len(subreddits):
                        break

                    try:
                        # Convert to our model with validation
                        reddit_submission = self._convert_to_model(submission)
                        submissions.append(reddit_submission)
                        subreddit_count += 1
                        total_fetched += 1

                    except Exception as e:
                        logger.warning(f"Failed to process submission {submission.id}: {e}")
                        continue

                logger.info(f"✓ Fetched {subreddit_count} submissions from r/{subreddit_name}")

            except (NotFound, Forbidden) as e:
                error_msg = f"Subreddit r/{subreddit_name} not found or private"
                logger.error(error_msg)
                errors.append(error_msg)
                continue

            except ResponseException as e:
                error_msg = f"Reddit API error fetching from r/{subreddit_name}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue

            except Exception as e:
                error_msg = f"Unexpected error fetching from r/{subreddit_name}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue

        if not submissions and errors:
            raise RuntimeError(f"Failed to fetch any submissions. Errors: {errors}")

        logger.info(f"✓ Total submissions fetched: {len(submissions)}")
        if errors:
            logger.warning(f"Encountered {len(errors)} errors during fetch")

        return submissions

    def _convert_to_model(self, submission: praw.models.Submission) -> RedditSubmission:
        """
        Convert PRAW submission to our RedditSubmission model

        Args:
            submission: PRAW submission object

        Returns:
            Validated RedditSubmission object

        Raises:
            ValueError: If submission data is invalid
        """
        try:
            # Handle author safely
            author_name = str(submission.author) if submission.author else "[deleted]"

            # Create submission model
            reddit_submission = RedditSubmission(
                id=submission.id,
                title=submission.title,
                text=submission.selftext or "",
                author=author_name,
                upvotes=submission.ups,
                downvotes=getattr(submission, 'downs', 0),  # Not always available
                score=submission.score,
                comments_count=submission.num_comments,
                subreddit=submission.subreddit.display_name.lower(),
                created_utc=datetime.fromtimestamp(submission.created_utc, tz=UTC),
                permalink=f"https://reddit.com{submission.permalink}",
                url=getattr(submission, 'url', None),
                is_self=submission.is_self,
                over_18=submission.over_18
            )

            return reddit_submission

        except Exception as e:
            logger.error(f"Failed to convert submission {submission.id} to model: {e}")
            raise ValueError(f"Invalid submission data for {submission.id}: {e}")

    def test_connection(self) -> bool:
        """
        Test Reddit API connection and authentication

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # This will raise an exception if authentication fails
            self.reddit.user.me()
            logger.info("✓ Reddit API connection test successful")
            return True

        except Exception as e:
            logger.error(f"Reddit API connection test failed: {e}")
            return False

    def get_subreddit_info(self, subreddit_name: str) -> dict:
        """
        Get basic information about a subreddit

        Args:
            subreddit_name: Name of the subreddit

        Returns:
            Dictionary with subreddit information

        Raises:
            NotFound: If subreddit doesn't exist
            Forbidden: If subreddit is private
        """
        try:
            subreddit = self.reddit.subreddit(subreddit_name)

            return {
                "name": subreddit.display_name,
                "title": getattr(subreddit, 'title', 'No title'),
                "description": getattr(subreddit, 'public_description', 'No description'),
                "subscribers": getattr(subreddit, 'subscribers', 0),
                "active_users": getattr(subreddit, 'active_user_count', None),
                "created_utc": datetime.fromtimestamp(subreddit.created_utc, tz=UTC) if subreddit.created_utc else None,
                "over18": getattr(subreddit, 'over18', False),
                "is_restricted": getattr(subreddit, 'restricted', False),
            }

        except (NotFound, Forbidden) as e:
            logger.error(f"Subreddit r/{subreddit_name} not found or restricted: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get subreddit info for r/{subreddit_name}: {e}")
            raise