"""
RedditHarbor DLT Source with Activity Validation Integration

This module provides a DLT (Data Load Tool) source for Reddit data collection
with integrated activity validation functionality. It combines PRAW (Python Reddit
API Wrapper) with the activity validation module to provide intelligent,
activity-aware Reddit data collection.

Main Components:
- reddit_activity_aware: Main DLT source with activity validation
- active_subreddits: Resource for validated active subreddits
- validated_comments: Resource for comments with activity validation
- activity_trends: Resource for tracking subreddit activity trends

Usage:
    import dlt
    from core.dlt_reddit_source import reddit_activity_aware

    # Initialize Reddit client
    reddit = praw.Reddit(...)

    # Create DLT pipeline
    pipeline = dlt.pipeline(
        pipeline_name="reddit_activity_pipeline",
        destination="postgres",
        dataset_name="reddit_data"
    )

    # Load data with activity validation
    data = reddit_activity_aware(
        reddit_client=reddit,
        subreddits=["python", "learnprogramming"],
        time_filter="day",
        min_activity_score=50.0
    )

    # Run pipeline
    info = pipeline.run(data)
"""

import logging
import time
from collections.abc import Generator
from typing import Any

import dlt
import pendulum
import praw

# Import activity validation functions
from core.activity_validation import (
    calculate_activity_score,
    calculate_trending_score,
    collect_activity_metrics,
    get_active_subreddits,
)
from core.dlt import PK_DISPLAY_NAME, PK_ID

# Configure logging
logger = logging.getLogger(__name__)


def quick_opportunity_score(submission_title: str, subreddit: str, submission_score: int) -> float:
    """
    Quick AI scoring function for pre-filtering submissions before database storage.
    Uses simple heuristics to estimate opportunity viability.

    Args:
        submission_title: Reddit submission title
        subreddit: Subreddit name
        submission_score: Reddit submission score

    Returns:
        Quick opportunity score (0-100)
    """
    try:
        score = 0.0

        # Base score from submission engagement
        if submission_score > 1000:
            score += 15
        elif submission_score > 100:
            score += 10
        elif submission_score > 10:
            score += 5

        # Subreddit quality bonus
        high_value_subreddits = {
            'entrepreneur', 'startups', 'smallbusiness', 'business',
            'productivity', 'selfimprovement', 'personalfinance', 'investing',
            'technology', 'programming', 'software', 'SaaS'
        }
        if subreddit.lower() in high_value_subreddits:
            score += 10

        # Title analysis for opportunity signals
        opportunity_keywords = [
            'looking for', 'need help', 'recommendation', 'what do you use',
            'best way to', 'how can i', 'problem with', 'struggling with',
            'anyone know', 'suggestion needed', 'advice needed', 'help me find'
        ]

        title_lower = submission_title.lower()
        keyword_matches = sum(1 for keyword in opportunity_keywords if keyword in title_lower)
        score += min(keyword_matches * 3, 15)  # Max 15 points from keywords

        # Length and quality signals
        if 20 <= len(submission_title) <= 200:
            score += 5  # Good title length
        if '?' in submission_title:
            score += 5  # Question format often indicates needs

        # Technical/problem-solving indicators
        tech_keywords = ['api', 'integration', 'automation', 'tool', 'software', 'app', 'platform']
        tech_matches = sum(1 for keyword in tech_keywords if keyword in title_lower)
        score += min(tech_matches * 2, 10)

        return min(score, 100.0)

    except Exception as e:
        logger.warning(f"Error in quick scoring for '{submission_title}': {e}")
        return 20.0  # Conservative default score


def filter_high_potential_submissions(data_stream, min_score: float = 30.0):
    """
    Filter submissions by quick opportunity score before database storage.

    Args:
        data_stream: Stream of submission/comment data
        min_score: Minimum quick score required to pass through filter

    Yields:
        Only submissions meeting the minimum score threshold
    """
    filtered_count = 0
    total_count = 0

    for item in data_stream:
        total_count += 1

        # Extract relevant fields for scoring
        title = item.get('submission_title', '') or item.get('title', '')
        subreddit = item.get('subreddit', '')
        score = item.get('submission_score', 0) or item.get('score', 0)

        # Calculate quick opportunity score
        quick_score = quick_opportunity_score(title, subreddit, score)

        # Only yield items meeting threshold
        if quick_score >= min_score:
            item['quick_opportunity_score'] = quick_score
            yield item
            filtered_count += 1

    logger.info(f"DLT Pre-filter: {filtered_count}/{total_count} items passed threshold ({min_score:.1f}+)")
    logger.info(f"Database reduction: {((total_count - filtered_count) / total_count * 100):.1f}% less storage")


@dlt.source(
    name="reddit_activity_aware",
    max_table_nesting=0,
)
def reddit_activity_aware(
    reddit_client: praw.Reddit,
    subreddits: list[str],
    time_filter: str = "day",
    min_activity_score: float = 50.0,
    min_opportunity_score: float = 30.0,
) -> Any:
    """
    Main DLT source for Reddit data collection with activity validation and pre-filtering.

    Args:
        reddit_client: PRAW Reddit client instance
        subreddits: List of subreddit names to collect from
        time_filter: Time period for activity analysis (hour, day, week, month, year, all)
        min_activity_score: Minimum activity score threshold (0-100)
        min_opportunity_score: Minimum quick opportunity score for pre-filtering (0-100)

    Returns:
        DLT source with configured resources and pre-filtering applied
    """
    logger.info(
        f"Creating reddit_activity_aware source for {len(subreddits)} subreddits "
        f"with min_activity_score={min_activity_score}, time_filter={time_filter}, "
        f"min_opportunity_score={min_opportunity_score}"
    )

    return [
        active_subreddits(reddit_client, subreddits, time_filter, min_activity_score),
        validated_comments(reddit_client, subreddits, time_filter, min_activity_score, min_opportunity_score),
        activity_trends(reddit_client, subreddits, time_filter, min_activity_score),
    ]


@dlt.resource(
    name="active_subreddits",
    write_disposition="merge",
    primary_key=PK_DISPLAY_NAME,
    columns={
        "display_name": {"data_type": "text", "nullable": False},
        "subscribers": {"data_type": "bigint", "nullable": True},
        "public_description": {"data_type": "text", "nullable": True},
        "activity_score": {"data_type": "decimal", "nullable": False},
        "trending_score": {"data_type": "decimal", "nullable": False},
        "comments_24h": {"data_type": "bigint", "nullable": False},
        "posts_24h": {"data_type": "bigint", "nullable": False},
        "avg_engagement_rate": {"data_type": "decimal", "nullable": False},
        "time_filter": {"data_type": "text", "nullable": False},
        "collection_timestamp": {"data_type": "timestamp", "nullable": False},
        "subscriber_base_score": {"data_type": "decimal", "nullable": False},
        "active_users_score": {"data_type": "decimal", "nullable": False},
        "quality_signals": {"data_type": "json", "nullable": True},
        "trending_velocity": {"data_type": "decimal", "nullable": False},
        "activity_density": {"data_type": "decimal", "nullable": False},
        "is_restricted": {"data_type": "bool", "nullable": True},
        "is_nsfw": {"data_type": "bool", "nullable": True},
        "subreddit_type": {"data_type": "text", "nullable": True},
    },
)
def active_subreddits(
    reddit_client: praw.Reddit,
    subreddits: list[str],
    time_filter: str = "day",
    min_activity_score: float = 50.0,
) -> Generator[dict[str, Any], None, None]:
    """
    DLT resource for collecting active subreddits with validation.

    Args:
        reddit_client: PRAW Reddit client instance
        subreddits: List of subreddit names to validate and collect
        time_filter: Time period for activity analysis
        min_activity_score: Minimum activity score threshold

    Yields:
        Dict containing subreddit data with activity metrics
    """
    logger.info(
        f"Starting active_subreddits resource collection for {len(subreddits)} subreddits"
    )

    # Get active subreddits using activity validation
    active_subs = get_active_subreddits(
        reddit_client, subreddits, time_filter, min_activity_score
    )

    collection_timestamp = pendulum.now()

    for subreddit in active_subs:
        try:
            # Collect detailed activity metrics
            metrics = collect_activity_metrics(subreddit, time_filter)

            # Calculate trending score
            trending_score = calculate_trending_score(metrics)

            # Extract subreddit metadata safely
            subscribers = getattr(subreddit, "subscribers", None) or 0
            public_description = getattr(subreddit, "public_description", "") or ""
            is_restricted = getattr(subreddit, "over18", False) or getattr(
                subreddit, "restricted", False
            )
            is_nsfw = getattr(subreddit, "over18", False)
            subreddit_type = getattr(subreddit, "subreddit_type", "public")

            # Yield subreddit data with activity metrics
            yield {
                "display_name": subreddit.display_name,
                "subscribers": subscribers,
                "public_description": public_description,
                "activity_score": calculate_activity_score(subreddit, time_filter),
                "trending_score": trending_score,
                "comments_24h": metrics.comments_24h,
                "posts_24h": metrics.posts_24h,
                "avg_engagement_rate": metrics.avg_engagement_rate,
                "time_filter": time_filter,
                "collection_timestamp": collection_timestamp.to_iso8601_string(),
                "subscriber_base_score": metrics.subscriber_base_score,
                "active_users_score": metrics.active_users_score,
                "quality_signals": metrics.quality_signals,
                "trending_velocity": metrics.trending_velocity,
                "activity_density": metrics.activity_density,
                "is_restricted": is_restricted,
                "is_nsfw": is_nsfw,
                "subreddit_type": subreddit_type,
            }

            # Rate limiting between subreddit processing
            time.sleep(1)

        except Exception as e:
            logger.warning(f"Error processing subreddit {subreddit.display_name}: {e}")
            continue

    logger.info("Completed active_subreddits resource collection")


@dlt.resource(
    name="validated_comments",
    write_disposition="merge",
    primary_key=PK_ID,
    columns={
        "id": {"data_type": "text", "nullable": False},
        "subreddit": {"data_type": "text", "nullable": False},
        "author": {"data_type": "text", "nullable": True},
        "body": {"data_type": "text", "nullable": True},
        "score": {"data_type": "bigint", "nullable": False},
        "created_utc": {"data_type": "timestamp", "nullable": False},
        "permalink": {"data_type": "text", "nullable": True},
        "subreddit_activity_score": {"data_type": "decimal", "nullable": False},
        "subreddit_trending_score": {"data_type": "decimal", "nullable": False},
        "body_length": {"data_type": "bigint", "nullable": False},
        "is_edited": {"data_type": "bool", "nullable": False},
        "stickied": {"data_type": "bool", "nullable": False},
        "parent_id": {"data_type": "text", "nullable": True},
        "submission_id": {"data_type": "text", "nullable": True},
        "submission_title": {"data_type": "text", "nullable": True},
        "submission_score": {"data_type": "bigint", "nullable": False},
        "quick_opportunity_score": {"data_type": "decimal", "nullable": True},
        "time_filter": {"data_type": "text", "nullable": False},
        "collection_timestamp": {"data_type": "timestamp", "nullable": False},
    },
)
def validated_comments(
    reddit_client: praw.Reddit,
    subreddits: list[str],
    time_filter: str = "day",
    min_activity_score: float = 50.0,
    min_opportunity_score: float = 30.0,
    comments_per_post: int = 10,
    created_after: pendulum.DateTime | None = None,
    min_comment_length: int = 10,
    min_score: int = 1,
) -> Generator[dict[str, Any], None, None]:
    """
    DLT resource for collecting validated comments with activity awareness and pre-filtering.

    Args:
        reddit_client: PRAW Reddit client instance
        subreddits: List of subreddit names to collect from
        time_filter: Time period for activity analysis
        min_activity_score: Minimum activity score threshold
        min_opportunity_score: Minimum opportunity score for pre-filtering (0-100)
        comments_per_post: Maximum number of comments to collect per post
        created_after: Optional incremental loading cursor
        min_comment_length: Minimum comment length filter
        min_score: Minimum comment score filter

    Yields:
        Dict containing comment data with validation metadata and quick opportunity score
    """
    logger.info(
        f"Starting validated_comments resource collection for {len(subreddits)} subreddits"
    )

    # Get active subreddits first
    active_subs = get_active_subreddits(
        reddit_client, subreddits, time_filter, min_activity_score
    )

    collection_timestamp = pendulum.now()

    for subreddit in active_subs:
        try:
            # Calculate subreddit activity metrics
            activity_score = calculate_activity_score(subreddit, time_filter)
            metrics = collect_activity_metrics(subreddit, time_filter)
            trending_score = calculate_trending_score(metrics)

            logger.info(
                f"Collecting comments from r/{subreddit.display_name} "
                f"(activity_score: {activity_score:.2f})"
            )

            # Get top posts within time filter
            for submission in subreddit.top(time_filter=time_filter, limit=20):
                try:
                    # Check incremental loading cursor
                    if created_after:
                        submission_time = pendulum.from_timestamp(
                            submission.created_utc
                        )
                        if submission_time <= created_after:
                            continue

                    # Collect comments from this submission
                    submission.comments.replace_more(limit=0)
                    comment_count = 0

                    for comment in submission.comments.list():
                        if comment_count >= comments_per_post:
                            break

                        # Apply quality filters
                        if (
                            hasattr(comment, "body")
                            and comment.body
                            and len(comment.body) >= min_comment_length
                            and comment.score >= min_score
                        ):
                            # Calculate quick opportunity score for pre-filtering
                            quick_score = quick_opportunity_score(
                                submission.title,
                                subreddit.display_name,
                                submission.score
                            )

                            # Only yield if opportunity score meets threshold
                            if quick_score >= min_opportunity_score:
                                yield {
                                    "id": comment.id,
                                    "subreddit": subreddit.display_name,
                                    "author": (
                                        str(comment.author)
                                        if comment.author
                                        else "[deleted]"
                                    ),
                                    "body": comment.body,
                                    "score": comment.score,
                                    "created_utc": pendulum.from_timestamp(
                                        comment.created_utc
                                    ).to_iso8601_string(),
                                    "permalink": getattr(comment, "permalink", ""),
                                    "subreddit_activity_score": activity_score,
                                    "subreddit_trending_score": trending_score,
                                    "body_length": len(comment.body) if comment.body else 0,
                                    "is_edited": getattr(comment, "edited", False),
                                    "stickied": getattr(comment, "stickied", False),
                                    "parent_id": getattr(comment, "parent_id", ""),
                                    "submission_id": submission.id,
                                    "submission_title": submission.title,
                                    "submission_score": submission.score,
                                    "quick_opportunity_score": quick_score,
                                    "time_filter": time_filter,
                                    "collection_timestamp": collection_timestamp.to_iso8601_string(),
                                }
                                comment_count += 1

                except Exception as e:
                    logger.warning(
                        f"Error processing submission {submission.id} in r/{subreddit.display_name}: {e}"
                    )
                    continue

            # Rate limiting between subreddit processing
            time.sleep(2)

        except Exception as e:
            logger.warning(f"Error processing subreddit {subreddit.display_name}: {e}")
            continue

    logger.info("Completed validated_comments resource collection")


@dlt.resource(
    name="activity_trends",
    write_disposition="merge",
    primary_key=PK_DISPLAY_NAME,
    columns={
        "subreddit_name": {"data_type": "text", "nullable": False},
        "time_filter": {"data_type": "text", "nullable": False},
        "activity_score": {"data_type": "decimal", "nullable": False},
        "trending_score": {"data_type": "decimal", "nullable": False},
        "comments_24h": {"data_type": "bigint", "nullable": False},
        "posts_24h": {"data_type": "bigint", "nullable": False},
        "avg_engagement_rate": {"data_type": "decimal", "nullable": False},
        "subscriber_count": {"data_type": "bigint", "nullable": True},
        "trending_velocity": {"data_type": "decimal", "nullable": False},
        "activity_density": {"data_type": "decimal", "nullable": False},
        "quality_score": {"data_type": "decimal", "nullable": False},
        "trend_direction": {"data_type": "text", "nullable": False},
        "collection_timestamp": {"data_type": "timestamp", "nullable": False},
        "analysis_date": {"data_type": "date", "nullable": False},
    },
)
def activity_trends(
    reddit_client: praw.Reddit,
    subreddits: list[str],
    time_filter: str = "day",
    min_activity_score: float = 50.0,
) -> Generator[dict[str, Any], None, None]:
    """
    DLT resource for tracking subreddit activity trends over time.

    Args:
        reddit_client: PRAW Reddit client instance
        subreddits: List of subreddit names to track trends for
        time_filter: Time period for activity analysis
        min_activity_score: Minimum activity score threshold

    Yields:
        Dict containing activity trend data
    """
    logger.info(
        f"Starting activity_trends resource collection for {len(subreddits)} subreddits"
    )

    # Get active subreddits
    active_subs = get_active_subreddits(
        reddit_client, subreddits, time_filter, min_activity_score
    )

    collection_timestamp = pendulum.now()
    analysis_date = collection_timestamp.date()

    for subreddit in active_subs:
        try:
            # Collect comprehensive activity metrics
            metrics = collect_activity_metrics(subreddit, time_filter)
            activity_score = calculate_activity_score(subreddit, time_filter)
            trending_score = calculate_trending_score(metrics)

            # Determine trend direction
            if metrics.trending_velocity > 50:
                trend_direction = "rising"
            elif metrics.trending_velocity > 10:
                trend_direction = "increasing"
            elif metrics.trending_velocity > -10:
                trend_direction = "stable"
            elif metrics.trending_velocity > -50:
                trend_direction = "decreasing"
            else:
                trend_direction = "falling"

            # Calculate quality score based on various factors
            quality_score = min(
                100,
                (metrics.quality_signals.get("avg_post_score", 0) / 10)
                + (metrics.avg_engagement_rate * 5)
                + (metrics.activity_density * 100),
            )

            # Yield trend data
            yield {
                "subreddit_name": subreddit.display_name,
                "time_filter": time_filter,
                "activity_score": activity_score,
                "trending_score": trending_score,
                "comments_24h": metrics.comments_24h,
                "posts_24h": metrics.posts_24h,
                "avg_engagement_rate": metrics.avg_engagement_rate,
                "subscriber_count": getattr(subreddit, "subscribers", 0),
                "trending_velocity": metrics.trending_velocity,
                "activity_density": metrics.activity_density,
                "quality_score": quality_score,
                "trend_direction": trend_direction,
                "collection_timestamp": collection_timestamp.to_iso8601_string(),
                "analysis_date": analysis_date.isoformat(),
            }

            # Rate limiting between subreddit processing
            time.sleep(1)

        except Exception as e:
            logger.warning(f"Error processing trends for {subreddit.display_name}: {e}")
            continue

    logger.info("Completed activity_trends resource collection")


# Utility functions for DLT pipeline integration
def create_reddit_pipeline(
    pipeline_name: str = "reddit_activity_pipeline",
    destination: str = "postgres",
    dataset_name: str = "reddit_data",
    **kwargs,
) -> dlt.Pipeline:
    """
    Create a DLT pipeline for Reddit data collection.

    Args:
        pipeline_name: Name of the DLT pipeline
        destination: DLT destination (postgres, bigquery, etc.)
        dataset_name: Dataset name for the destination
        **kwargs: Additional pipeline arguments

    Returns:
        Configured DLT pipeline instance
    """
    logger.info(f"Creating DLT pipeline: {pipeline_name}")

    pipeline = dlt.pipeline(
        pipeline_name=pipeline_name,
        destination=destination,
        dataset_name=dataset_name,
        **kwargs,
    )

    return pipeline


def run_reddit_collection(
    reddit_client: praw.Reddit,
    subreddits: list[str],
    time_filter: str = "day",
    min_activity_score: float = 50.0,
    pipeline_name: str = "reddit_activity_pipeline",
    **pipeline_kwargs,
) -> dict[str, Any]:
    """
    Run a complete Reddit data collection pipeline.

    Args:
        reddit_client: PRAW Reddit client instance
        subreddits: List of subreddit names to collect from
        time_filter: Time period for activity analysis
        min_activity_score: Minimum activity score threshold
        pipeline_name: Name of the DLT pipeline
        pipeline_kwargs: Additional pipeline arguments

    Returns:
        Pipeline execution information
    """
    logger.info(f"Starting Reddit collection pipeline for {len(subreddits)} subreddits")

    # Create pipeline
    pipeline = create_reddit_pipeline(pipeline_name=pipeline_name, **pipeline_kwargs)

    # Create data source
    data = reddit_activity_aware(
        reddit_client=reddit_client,
        subreddits=subreddits,
        time_filter=time_filter,
        min_activity_score=min_activity_score,
    )

    # Run pipeline
    info = pipeline.run(data)

    logger.info(f"Reddit collection pipeline completed: {info}")

    return info


# Example usage function
def example_usage():
    """
    Example usage of the DLT Reddit source with activity validation.
    """
    try:
        # Initialize Reddit client
        from config.settings import REDDIT_PUBLIC, REDDIT_SECRET, REDDIT_USER_AGENT

        reddit = praw.Reddit(
            client_id=REDDIT_PUBLIC,
            client_secret=REDDIT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )

        # Test subreddits
        test_subreddits = ["python", "learnprogramming", "technology"]

        print("🔍 Testing DLT Reddit source with activity validation...")

        # Create data source
        data = reddit_activity_aware(
            reddit_client=reddit,
            subreddits=test_subreddits,
            time_filter="day",
            min_activity_score=30.0,
        )

        print(f"✅ Created DLT source with {len(data)} resources")

        # You can now run this with a DLT pipeline
        # pipeline = create_reddit_pipeline()
        # info = pipeline.run(data)

        print("🎉 DLT Reddit source ready for pipeline execution!")

    except Exception as e:
        logger.error(f"Example usage failed: {e}")


if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    example_usage()
