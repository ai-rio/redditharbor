"""
RedditHarbor Activity Validation Module

This module provides comprehensive activity scoring and validation for Reddit subreddits
using PRAW (Python Reddit API Wrapper). It implements multi-factor scoring to assess
subreddit activity levels and identify active communities for research purposes.

Main Functions:
- calculate_activity_score(): Multi-factor activity scoring with weighted components
- collect_activity_metrics(): Detailed metrics collection from Reddit API
- calculate_trending_score(): Trending analysis based on activity patterns
- get_active_subreddits(): Filter subreddits by minimum activity thresholds

Usage:
    from core.activity_validation import (
        calculate_activity_score,
        collect_activity_metrics,
        calculate_trending_score,
        get_active_subreddits
    )

    # Initialize Reddit client
    reddit = praw.Reddit(...)

    # Calculate activity score for a subreddit
    score = calculate_activity_score(subreddit, time_filter="day")
"""

import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

import praw

# Configure logging
logger = logging.getLogger(__name__)


class TimeFilter(Enum):
    """Time filter options for Reddit API calls."""

    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    ALL = "all"


@dataclass
class ActivityMetrics:
    """Data class for storing activity metrics."""

    recent_comments_count: int = 0
    post_engagement_score: float = 0.0
    subscriber_base_score: float = 0.0
    active_users_score: float = 0.0
    comments_24h: int = 0
    posts_24h: int = 0
    avg_engagement_rate: float = 0.0
    quality_signals: dict[str, float] = None
    trending_velocity: float = 0.0
    activity_density: float = 0.0

    def __post_init__(self):
        if self.quality_signals is None:
            self.quality_signals = {}


def calculate_activity_score(
    subreddit: praw.models.Subreddit, time_filter: str = "day"
) -> float:
    """
    Calculate multi-factor activity score for a subreddit.

    Scoring weights:
    - Recent comments: 40%
    - Post engagement: 30%
    - Subscriber base: 20%
    - Active users: 10%

    Args:
        subreddit: PRAW Subreddit object
        time_filter: Time period for analysis (hour, day, week, month, year, all)

    Returns:
        Activity score between 0-100

    Raises:
        Exception: If Reddit API calls fail
    """
    # Handle None subreddit
    if subreddit is None:
        logger.warning("Subreddit is None")
        return 0.0

    # Handle invalid subreddit
    if not hasattr(subreddit, "display_name"):
        logger.warning("Invalid subreddit object")
        return 0.0

    logger.info(
        f"Calculating activity score for r/{subreddit.display_name} "
        f"with time_filter={time_filter}"
    )

    try:
        # Collect detailed metrics
        metrics = collect_activity_metrics(subreddit, time_filter)

        # Calculate weighted components
        # Recent comments score (40% weight)
        comments_score = min(
            100, metrics.recent_comments_count / 10
        )  # Normalize to 0-100
        comments_weight = 0.40

        # Post engagement score (30% weight)
        engagement_score = min(100, metrics.post_engagement_score)
        engagement_weight = 0.30

        # Subscriber base score (20% weight) - logarithmic scaling
        subscriber_score = min(100, min(90, metrics.subscriber_base_score))
        subscriber_weight = 0.20

        # Active users score (10% weight)
        active_users_score = min(100, metrics.active_users_score)
        active_users_weight = 0.10

        # Calculate weighted average
        activity_score = (
            comments_score * comments_weight
            + engagement_score * engagement_weight
            + subscriber_score * subscriber_weight
            + active_users_score * active_users_weight
        )

        logger.info(
            f"Activity score for r/{subreddit.display_name}: {activity_score:.2f}"
        )
        logger.debug(
            f"Components: comments={comments_score:.1f}, engagement={engagement_score:.1f}, "
            f"subscribers={subscriber_score:.1f}, active_users={active_users_score:.1f}"
        )

        return round(activity_score, 2)

    except Exception as e:
        logger.error(
            f"Error calculating activity score for r/{subreddit.display_name}: {e}"
        )
        return 0.0


def collect_activity_metrics(
    subreddit: praw.models.Subreddit, time_filter: str = "day"
) -> ActivityMetrics:
    """
    Collect detailed activity metrics from Reddit API.

    Args:
        subreddit: PRAW Subreddit object
        time_filter: Time period for analysis

    Returns:
        ActivityMetrics object with all collected metrics
    """
    # Handle None subreddit
    if subreddit is None:
        logger.warning("Subreddit is None")
        return ActivityMetrics()

    # Handle invalid subreddit
    if not hasattr(subreddit, "display_name"):
        logger.warning("Invalid subreddit object")
        return ActivityMetrics()

    logger.info(f"Collecting activity metrics for r/{subreddit.display_name}")

    metrics = ActivityMetrics()

    try:
        # Collect recent comments (40% weight component)
        metrics.recent_comments_count = get_recent_comments_count(
            subreddit, time_filter
        )

        # Collect post engagement metrics (30% weight component)
        metrics.comments_24h, metrics.posts_24h, metrics.post_engagement_score = (
            get_post_engagement_metrics(subreddit, time_filter)
        )

        # Collect subscriber base metrics (20% weight component)
        metrics.subscriber_base_score = calculate_subscriber_score(subreddit)

        # Collect active users metrics (10% weight component)
        metrics.active_users_score = estimate_active_users_score(
            subreddit, metrics.comments_24h
        )

        # Calculate derived metrics
        metrics.avg_engagement_rate = calculate_average_engagement_rate(
            metrics.comments_24h, metrics.posts_24h
        )

        # Collect quality signals
        metrics.quality_signals = collect_quality_signals(subreddit, time_filter)

        # Calculate trending velocity
        metrics.trending_velocity = calculate_trending_velocity(metrics)

        # Calculate activity density
        metrics.activity_density = calculate_activity_density(metrics)

        logger.info(
            f"Metrics collected for r/{subreddit.display_name}: "
            f"comments={metrics.recent_comments_count}, "
            f"engagement={metrics.post_engagement_score:.1f}, "
            f"subscribers={metrics.subscriber_base_score:.1f}"
        )

        return metrics

    except Exception as e:
        logger.error(
            f"Error collecting activity metrics for r/{subreddit.display_name}: {e}"
        )
        return metrics


def get_recent_comments_count(
    subreddit: praw.models.Subreddit, time_filter: str, limit: int = 100
) -> int:
    """
    Get count of recent comments within the specified time filter.

    Args:
        subreddit: PRAW Subreddit object
        time_filter: Time period for analysis
        limit: Maximum number of comments to fetch

    Returns:
        Number of recent comments
    """
    try:
        comments_count = 0

        # Get recent comments from subreddit
        for comment in subreddit.comments(limit=limit):
            # Check if comment is within time filter
            if is_within_time_filter(comment.created_utc, time_filter):
                comments_count += 1
            else:
                break  # Comments are ordered by recency

        logger.debug(
            f"Found {comments_count} recent comments for r/{subreddit.display_name}"
        )
        return comments_count

    except Exception as e:
        logger.warning(
            f"Error getting recent comments for r/{subreddit.display_name}: {e}"
        )
        return 0


def get_post_engagement_metrics(
    subreddit: praw.models.Subreddit, time_filter: str, limit: int = 50
) -> tuple[int, int, float]:
    """
    Get post engagement metrics including comments per post and overall engagement score.

    Args:
        subreddit: PRAW Subreddit object
        time_filter: Time period for analysis
        limit: Maximum number of posts to analyze

    Returns:
        Tuple of (total_comments_24h, total_posts_24h, engagement_score)
    """
    try:
        total_comments = 0
        total_posts = 0
        total_score = 0
        posts_analyzed = 0

        # Get top posts within time filter
        for submission in subreddit.top(time_filter=time_filter, limit=limit):
            if is_within_time_filter(submission.created_utc, time_filter):
                total_posts += 1
                total_comments += submission.num_comments
                total_score += submission.score
                posts_analyzed += 1
            else:
                break

        # Calculate engagement score based on comments and upvotes
        if posts_analyzed > 0:
            avg_comments_per_post = total_comments / posts_analyzed
            avg_score_per_post = total_score / posts_analyzed

            # Engagement score: combination of comments and upvotes
            engagement_score = min(
                100, (avg_comments_per_post * 2) + (avg_score_per_post * 0.1)
            )
        else:
            avg_comments_per_post = 0
            avg_score_per_post = 0
            engagement_score = 0

        logger.debug(
            f"Engagement metrics for r/{subreddit.display_name}: "
            f"posts={total_posts}, comments={total_comments}, score={engagement_score:.1f}"
        )

        return total_comments, total_posts, engagement_score

    except Exception as e:
        logger.warning(
            f"Error getting post engagement metrics for r/{subreddit.display_name}: {e}"
        )
        return 0, 0, 0.0


def calculate_subscriber_score(subreddit: praw.models.Subreddit) -> float:
    """
    Calculate subscriber base score using logarithmic scaling.

    Args:
        subreddit: PRAW Subreddit object

    Returns:
        Subscriber score between 0-100
    """
    try:
        if not hasattr(subreddit, "subscribers") or subreddit.subscribers is None:
            return 0.0

        subscriber_count = subreddit.subscribers

        # Logarithmic scaling: very large subreddits don't get exponentially higher scores
        if subscriber_count <= 0:
            return 0.0
        elif subscriber_count < 100:
            # Small subreddits (1-99)
            return (subscriber_count / 100) * 30
        elif subscriber_count < 1000:
            # Medium subreddits (100-999)
            return 30 + ((subscriber_count - 100) / 900) * 30
        elif subscriber_count < 10000:
            # Large subreddits (1000-9999)
            return 60 + ((subscriber_count - 1000) / 9000) * 20
        elif subscriber_count < 100000:
            # Very large subreddits (10000-99999)
            return 80 + ((subscriber_count - 10000) / 90000) * 15
        else:
            # Massive subreddits (100000+)
            return min(95, 95 + (subscriber_count / 1000000))

    except Exception as e:
        logger.warning(
            f"Error calculating subscriber score for r/{subreddit.display_name}: {e}"
        )
        return 0.0


def estimate_active_users_score(
    subreddit: praw.models.Subreddit, recent_comments: int
) -> float:
    """
    Estimate active users score based on comment activity and subreddit size.

    Args:
        subreddit: PRAW Subreddit object
        recent_comments: Number of recent comments in time period

    Returns:
        Active users score between 0-100
    """
    try:
        if not hasattr(subreddit, "subscribers") or subreddit.subscribers is None:
            return min(100, recent_comments * 2)  # Basic fallback

        subscriber_count = subreddit.subscribers

        # Estimate active users as a function of comments and subscriber base
        if subscriber_count <= 0:
            active_users_estimate = recent_comments
        else:
            # Active users estimate: comments + some factor based on lurkers
            active_users_estimate = recent_comments * 1.5

        # Calculate activity ratio
        activity_ratio = active_users_estimate / max(1, subscriber_count)

        # Score based on activity ratio
        if activity_ratio >= 0.1:  # 10%+ active
            return 100
        elif activity_ratio >= 0.05:  # 5-10% active
            return 80
        elif activity_ratio >= 0.01:  # 1-5% active
            return 60
        elif activity_ratio >= 0.005:  # 0.5-1% active
            return 40
        elif activity_ratio >= 0.001:  # 0.1-0.5% active
            return 20
        else:
            return 10  # Less than 0.1% active

    except Exception as e:
        logger.warning(
            f"Error estimating active users score for r/{subreddit.display_name}: {e}"
        )
        return 0.0


def calculate_average_engagement_rate(comments: int, posts: int) -> float:
    """
    Calculate average engagement rate (comments per post).

    Args:
        comments: Total number of comments
        posts: Total number of posts

    Returns:
        Average engagement rate (comments per post)
    """
    try:
        if posts <= 0:
            return 0.0
        return comments / posts
    except Exception as e:
        logger.warning(f"Error calculating engagement rate: {e}")
        return 0.0


def collect_quality_signals(
    subreddit: praw.models.Subreddit, time_filter: str, limit: int = 20
) -> dict[str, float]:
    """
    Collect quality signals from posts and comments.

    Args:
        subreddit: PRAW Subreddit object
        time_filter: Time period for analysis
        limit: Number of posts to analyze

    Returns:
        Dictionary of quality signals
    """
    quality_signals = {}

    try:
        total_score = 0
        total_comments = 0
        posts_analyzed = 0

        # Analyze recent posts for quality signals
        for submission in subreddit.top(time_filter=time_filter, limit=limit):
            total_score += submission.score
            total_comments += submission.num_comments
            posts_analyzed += 1

        if posts_analyzed > 0:
            quality_signals["avg_post_score"] = total_score / posts_analyzed
            quality_signals["avg_comments_per_post"] = total_comments / posts_analyzed
            quality_signals["post_velocity"] = total_comments / max(1, posts_analyzed)
        else:
            quality_signals["avg_post_score"] = 0.0
            quality_signals["avg_comments_per_post"] = 0.0
            quality_signals["post_velocity"] = 0.0

        logger.debug(
            f"Quality signals for r/{subreddit.display_name}: {quality_signals}"
        )

    except Exception as e:
        logger.warning(
            f"Error collecting quality signals for r/{subreddit.display_name}: {e}"
        )
        quality_signals = {
            "avg_post_score": 0.0,
            "avg_comments_per_post": 0.0,
            "post_velocity": 0.0,
        }

    return quality_signals


def calculate_trending_velocity(metrics: ActivityMetrics) -> float:
    """
    Calculate trending velocity based on activity patterns.

    Args:
        metrics: ActivityMetrics object

    Returns:
        Trending velocity score (positive = trending up, negative = trending down)
    """
    try:
        # Simple trending calculation based on comment velocity and engagement
        base_velocity = metrics.comments_24h + (
            metrics.posts_24h * 5
        )  # Posts weighted more

        # Adjust by engagement rate
        engagement_multiplier = max(0.1, metrics.avg_engagement_rate / 10)

        trending_velocity = base_velocity * engagement_multiplier

        logger.debug(f"Trending velocity: {trending_velocity:.2f}")
        return trending_velocity

    except Exception as e:
        logger.warning(f"Error calculating trending velocity: {e}")
        return 0.0


def calculate_activity_density(metrics: ActivityMetrics) -> float:
    """
    Calculate activity density (quality vs quantity balance).

    Args:
        metrics: ActivityMetrics object

    Returns:
        Activity density score between 0-1
    """
    try:
        # Balance between engagement rate and subscriber base
        if metrics.comments_24h + metrics.posts_24h == 0:
            return 0.0

        density = metrics.avg_engagement_rate / max(
            1, metrics.comments_24h + metrics.posts_24h
        )

        return min(1.0, density)

    except Exception as e:
        logger.warning(f"Error calculating activity density: {e}")
        return 0.0


def calculate_trending_score(metrics: ActivityMetrics) -> float:
    """
    Calculate trending score based on comprehensive activity metrics.

    Args:
        metrics: ActivityMetrics object with all activity data

    Returns:
        Trending score between 0-100
    """
    try:
        # Base score from velocity
        base_trending = min(100, metrics.trending_velocity / 10)

        # Quality adjustment
        quality_multiplier = 1.0
        if metrics.quality_signals.get("avg_post_score", 0) > 100:
            quality_multiplier = 1.2
        elif metrics.quality_signals.get("avg_post_score", 0) > 50:
            quality_multiplier = 1.1

        # Activity density bonus
        density_bonus = metrics.activity_density * 20

        # Final trending score
        trending_score = min(100, (base_trending * quality_multiplier) + density_bonus)

        logger.debug(
            f"Trending score: {trending_score:.2f} (base: {base_trending:.2f}, "
            f"quality: {quality_multiplier:.2f}, density: {density_bonus:.2f})"
        )

        return round(trending_score, 2)

    except Exception as e:
        logger.error(f"Error calculating trending score: {e}")
        return 0.0


def get_active_subreddits(
    reddit_client: praw.Reddit,
    candidate_subreddits: list[str],
    time_filter: str = "day",
    min_activity_score: float = 50.0,
) -> list[praw.models.Subreddit]:
    """
    Filter and return active subreddits from a list of candidates.

    Args:
        reddit_client: PRAW Reddit client instance
        candidate_subreddits: List of subreddit names to check
        time_filter: Time period for activity analysis
        min_activity_score: Minimum activity score threshold (0-100)

    Returns:
        List of PRAW Subreddit objects that meet the activity threshold
    """
    logger.info(
        f"Filtering {len(candidate_subreddits)} candidate subreddits with min_score={min_activity_score}"
    )

    active_subreddits = []
    failed_subreddits = []

    for subreddit_name in candidate_subreddits:
        try:
            # Get subreddit object
            subreddit = reddit_client.subreddit(subreddit_name)

            # Validate subreddit exists and is accessible
            if not validate_subreddit_accessible(subreddit):
                logger.warning(f"Subreddit r/{subreddit_name} is not accessible")
                failed_subreddits.append(subreddit_name)
                continue

            # Calculate activity score
            activity_score = calculate_activity_score(subreddit, time_filter)

            # Check if meets threshold
            if activity_score >= min_activity_score:
                logger.info(
                    f"✅ r/{subreddit_name}: ACTIVE (score: {activity_score:.2f})"
                )
                active_subreddits.append(subreddit)
            else:
                logger.debug(
                    f"❌ r/{subreddit_name}: Inactive (score: {activity_score:.2f} < {min_activity_score})"
                )

            # Rate limiting between requests
            time.sleep(1)

        except Exception as e:
            logger.warning(f"Error processing subreddit r/{subreddit_name}: {e}")
            failed_subreddits.append(subreddit_name)
            continue

    logger.info(
        f"Found {len(active_subreddits)} active subreddits out of {len(candidate_subreddits)} candidates"
    )
    if failed_subreddits:
        logger.warning(
            f"Failed to process {len(failed_subreddits)} subreddits: {failed_subreddits}"
        )

    return active_subreddits


def validate_subreddit_accessible(subreddit: praw.models.Subreddit) -> bool:
    """
    Validate that a subreddit is accessible and not banned/private.

    Args:
        subreddit: PRAW Subreddit object

    Returns:
        True if subreddit is accessible, False otherwise
    """
    try:
        # Try to access basic subreddit properties
        display_name = getattr(subreddit, "display_name", None)
        if not display_name:
            return False

        subscribers = getattr(subreddit, "subscribers", 0)

        # Check if subreddit is public
        if hasattr(subreddit, "subreddit_type"):
            return subreddit.subreddit_type == "public"

        # Fallback: assume accessible if we got display name and subscribers
        return True

    except Exception as e:
        logger.debug(f"Subreddit validation failed for r/{getattr(subreddit, 'display_name', 'unknown')}: {e}")
        return False


def is_within_time_filter(created_utc: float, time_filter: str) -> bool:
    """
    Check if a timestamp is within the specified time filter.

    Args:
        created_utc: Unix timestamp
        time_filter: Time filter string (hour, day, week, month, year, all)

    Returns:
        True if timestamp is within the time filter
    """
    if time_filter == "all":
        return True

    try:
        # Convert to datetime
        created_time = datetime.fromtimestamp(created_utc, tz=UTC)
        current_time = datetime.now(UTC)

        # Calculate time difference
        time_diff = current_time - created_time

        # Check against filter
        if time_filter == "hour":
            return time_diff.total_seconds() <= 3600  # 1 hour
        elif time_filter == "day":
            return time_diff.total_seconds() <= 86400  # 24 hours
        elif time_filter == "week":
            return time_diff.total_seconds() <= 604800  # 7 days
        elif time_filter == "month":
            return time_diff.total_seconds() <= 2592000  # 30 days
        elif time_filter == "year":
            return time_diff.total_seconds() <= 31536000  # 365 days
        else:
            logger.warning(f"Unknown time filter: {time_filter}")
            return True

    except Exception as e:
        logger.warning(f"Error checking time filter: {e}")
        return True


# Example usage and testing function
def example_usage():
    """
    Example usage of activity validation functions.
    """
    try:
        # Initialize Reddit client (example - credentials should be in environment)
        from config.settings import REDDIT_PUBLIC, REDDIT_SECRET, REDDIT_USER_AGENT

        reddit = praw.Reddit(
            client_id=REDDIT_PUBLIC,
            client_secret=REDDIT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )

        # Test with a few subreddits
        test_subreddits = ["python", "learnprogramming", "technology"]
        time_filter = "day"

        print("🔍 Testing activity validation...")

        # Get active subreddits
        active_subs = get_active_subreddits(
            reddit, test_subreddits, time_filter, min_activity_score=30
        )

        for subreddit in active_subs:
            # Get detailed metrics
            metrics = collect_activity_metrics(subreddit, time_filter)

            # Calculate scores
            activity_score = calculate_activity_score(subreddit, time_filter)
            trending_score = calculate_trending_score(metrics)

            print(f"\n📊 r/{subreddit.display_name}")
            print(f"   Activity Score: {activity_score}/100")
            print(f"   Trending Score: {trending_score}/100")
            print(f"   Comments (24h): {metrics.comments_24h}")
            print(f"   Posts (24h): {metrics.posts_24h}")
            print(f"   Engagement Rate: {metrics.avg_engagement_rate:.2f}")
            print(f"   Subscriber Base: {subreddit.subscribers:,}")

    except Exception as e:
        logger.error(f"Example usage failed: {e}")


if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    example_usage()
