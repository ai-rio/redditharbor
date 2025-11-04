"""
RedditHarbor Core Collection Module

Handles the main data collection functionality for RedditHarbor with comprehensive comment collection.
"""

import logging
import time
import random
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import traceback

logger = logging.getLogger(__name__)


def collect_data(
    reddit_client,
    supabase_client,
    db_config: dict[str, str],
    subreddits: list[str],
    limit: int = 100,
    sort_types: list[str] | None = None,
    mask_pii: bool = True,
) -> bool:
    """
    Collect Reddit data and store it in Supabase database.

    Args:
        reddit_client: Reddit API client
        supabase_client: Supabase database client
        db_config: Database table configuration
        subreddits: List of subreddits to collect from
        limit: Maximum number of posts to collect per subreddit
        sort_types: Sort types to use ("hot", "new", "top", etc.)
        mask_pii: Whether to mask personally identifiable information

    Returns:
        bool: True if collection successful, False otherwise
    """
    if sort_types is None:
        sort_types = ["hot"]

    try:
        logger.info(f"🔍 Starting comprehensive data collection from {len(subreddits)} subreddits")

        # Collect submissions
        submissions_success = collect_submissions(
            reddit_client, supabase_client, db_config, subreddits, limit, sort_types, mask_pii
        )

        # CRITICAL: Collect comments for all submissions
        comments_success = collect_comments_for_submissions(
            reddit_client, supabase_client, db_config, subreddits, mask_pii
        )

        return submissions_success and comments_success

    except Exception as e:
        logger.error(f"❌ Data collection failed: {e!s}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False


def collect_submissions(
    reddit_client,
    supabase_client,
    db_config: dict[str, str],
    subreddits: list[str],
    limit: int,
    sort_types: list[str],
    mask_pii: bool,
) -> bool:
    """Collect submissions from specified subreddits"""
    try:
        logger.info(f"📝 Collecting submissions from {len(subreddits)} subreddits")

        total_submissions = 0
        successful_subreddits = 0

        for subreddit_name in subreddits:
            try:
                logger.info(f"  📖 Processing r/{subreddit_name}")
                subreddit = reddit_client.subreddit(subreddit_name)

                subreddit_submissions = 0
                for sort_type in sort_types:
                    try:
                        if sort_type == "hot":
                            submissions = subreddit.hot(limit=limit)
                        elif sort_type == "new":
                            submissions = subreddit.new(limit=limit)
                        elif sort_type == "top":
                            submissions = subreddit.top(limit=limit)
                        elif sort_type == "rising":
                            submissions = subreddit.rising(limit=limit)
                        else:
                            submissions = subreddit.hot(limit=limit)

                        for submission in submissions:
                            try:
                                # Store submission data
                                submission_data = {
                                    "submission_id": submission.id,
                                    "title": submission.title,
                                    "author": str(submission.author) if submission.author else "[deleted]",
                                    "subreddit": subreddit_name,
                                    "score": submission.score,
                                    "num_comments": submission.num_comments,
                                    "created_utc": datetime.fromtimestamp(submission.created_utc).isoformat(),
                                    "url": submission.url,
                                    "selftext": submission.selftext[:1000] if submission.selftext else "",
                                    "permalink": submission.permalink,
                                    "over_18": submission.over_18,
                                    "collection_timestamp": datetime.utcnow().isoformat()
                                }

                                # Apply PII masking if enabled
                                if mask_pii:
                                    submission_data = apply_pii_masking(submission_data)

                                # Store in Supabase
                                result = supabase_client.table(db_config["submission"]).upsert(
                                    submission_data, on_conflict="submission_id"
                                ).execute()

                                if result.data:
                                    subreddit_submissions += 1

                            except Exception as e:
                                logger.warning(f"    ⚠️ Failed to store submission {submission.id}: {e}")
                                continue

                        # Rate limiting
                        time.sleep(2)

                    except Exception as e:
                        logger.warning(f"  ⚠️ Failed to fetch {sort_type} posts from r/{subreddit_name}: {e}")
                        continue

                total_submissions += subreddit_submissions
                successful_subreddits += 1
                logger.info(f"  ✅ Collected {subreddit_submissions} submissions from r/{subreddit_name}")

                # Rate limiting between subreddits
                time.sleep(3)

            except Exception as e:
                logger.error(f"  ❌ Failed to process r/{subreddit_name}: {e}")
                continue

        logger.info(f"✅ Submission collection complete: {total_submissions} submissions from {successful_subreddits}/{len(subreddits)} subreddits")
        return True

    except Exception as e:
        logger.error(f"❌ Submission collection failed: {e}")
        return False


def collect_comments_for_submissions(
    reddit_client,
    supabase_client,
    db_config: dict[str, str],
    target_subreddits: list[str],
    mask_pii: bool,
    max_comments_per_submission: int = 50,
    max_age_hours: int = 72,  # Only process submissions from last 72 hours
) -> bool:
    """
    CRITICAL FUNCTION: Collect comments for existing submissions

    This is the key function to solve the 0 comments issue.
    It processes existing submissions and collects their comments.
    """
    try:
        logger.info(f"💬 CRITICAL: Starting comment collection for existing submissions")
        logger.info(f"🎯 Target subreddits: {len(target_subreddits)}")
        logger.info(f"⏰ Processing submissions from last {max_age_hours} hours")

        # Get recent submissions that need comments
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

        total_comments_collected = 0
        processed_submissions = 0

        for subreddit_name in target_subreddits:
            try:
                logger.info(f"  💬 Processing comments for r/{subreddit_name}")

                # Get recent submissions from this subreddit that have comments
                submissions_query = supabase_client.table(db_config["submission"]).select(
                    "submission_id,title,num_comments,created_utc"
                ).eq("subreddit", subreddit_name).gte("created_utc", cutoff_time.isoformat()).gt("num_comments", 0).limit(50)

                submissions_result = submissions_query.execute()

                if not submissions_result.data:
                    logger.info(f"    ℹ️ No recent submissions with comments found for r/{subreddit_name}")
                    continue

                logger.info(f"    📄 Found {len(submissions_result.data)} submissions with comments")

                subreddit_comments = 0

                for submission_data in submissions_result.data:
                    try:
                        submission_id = submission_data["submission_id"]
                        expected_comments = submission_data["num_comments"]

                        logger.info(f"      💬 Processing submission {submission_id} (expected {expected_comments} comments)")

                        # Check if comments already exist for this submission
                        existing_comments_query = supabase_client.table(db_config["comment"]).select(
                            "comment_id"
                        ).eq("submission_id", submission_id).limit(1)

                        existing_comments_result = existing_comments_query.execute()

                        if existing_comments_result.data:
                            logger.info(f"        ℹ️ Comments already exist for submission {submission_id}")
                            processed_submissions += 1
                            continue

                        # Get the submission from Reddit
                        submission = reddit_client.submission(submission_id)

                        # Replace more_comments to get all comments
                        submission.comments.replace_more(limit=None)

                        comment_count = 0
                        for comment in submission.comments.list():
                            try:
                                if comment_count >= max_comments_per_submission:
                                    break

                                # Skip if comment is deleted or removed
                                if comment.author is None or comment.body in ["[deleted]", "[removed]"]:
                                    continue

                                # Store comment data
                                comment_data = {
                                    "comment_id": comment.id,
                                    "submission_id": submission_id,
                                    "author": str(comment.author) if comment.author else "[deleted]",
                                    "body": comment.body[:2000],  # Limit comment length
                                    "score": comment.score,
                                    "created_utc": datetime.fromtimestamp(comment.created_utc).isoformat(),
                                    "subreddit": subreddit_name,
                                    "parent_id": comment.parent_id,
                                    "depth": getattr(comment, 'depth', 0),
                                    "collection_timestamp": datetime.utcnow().isoformat()
                                }

                                # Apply PII masking if enabled
                                if mask_pii:
                                    comment_data = apply_pii_masking(comment_data)

                                # Store in Supabase
                                result = supabase_client.table(db_config["comment"]).upsert(
                                    comment_data, on_conflict="comment_id"
                                ).execute()

                                if result.data:
                                    comment_count += 1
                                    subreddit_comments += 1
                                    total_comments_collected += 1

                            except Exception as e:
                                logger.warning(f"        ⚠️ Failed to store comment {comment.id}: {e}")
                                continue

                        logger.info(f"        ✅ Collected {comment_count} comments for submission {submission_id}")
                        processed_submissions += 1

                        # Rate limiting between submissions
                        time.sleep(1)

                    except Exception as e:
                        logger.warning(f"      ⚠️ Failed to process submission {submission_id}: {e}")
                        continue

                logger.info(f"    ✅ Collected {subreddit_comments} comments from r/{subreddit_name}")

                # Rate limiting between subreddits
                time.sleep(5)

            except Exception as e:
                logger.error(f"  ❌ Failed to process comments for r/{subreddit_name}: {e}")
                continue

        logger.info(f"🎉 CRITICAL COMMENT COLLECTION COMPLETED!")
        logger.info(f"✅ Total comments collected: {total_comments_collected}")
        logger.info(f"✅ Submissions processed: {processed_submissions}")

        return total_comments_collected > 0

    except Exception as e:
        logger.error(f"❌ Comment collection failed: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False


def collect_standalone_comments(
    reddit_client,
    supabase_client,
    db_config: dict[str, str],
    subreddits: list[str],
    limit: int = 1000,
    mask_pii: bool = True,
) -> bool:
    """
    Collect standalone comments from subreddits (alternative approach)
    """
    try:
        logger.info(f"💬 Collecting standalone comments from {len(subreddits)} subreddits")

        total_comments = 0

        for subreddit_name in subreddits:
            try:
                subreddit = reddit_client.subreddit(subreddit_name)

                # Get comments from hot posts
                for submission in subreddit.hot(limit=50):
                    try:
                        if submission.num_comments == 0:
                            continue

                        submission.comments.replace_more(limit=0)

                        for comment in submission.comments[:10]:  # Limit to top 10 comments per post
                            try:
                                if comment.author and comment.body not in ["[deleted]", "[removed]"]:
                                    comment_data = {
                                        "comment_id": comment.id,
                                        "submission_id": submission.id,
                                        "author": str(comment.author),
                                        "body": comment.body[:2000],
                                        "score": comment.score,
                                        "created_utc": datetime.fromtimestamp(comment.created_utc).isoformat(),
                                        "subreddit": subreddit_name,
                                        "parent_id": comment.parent_id,
                                        "collection_timestamp": datetime.utcnow().isoformat()
                                    }

                                    if mask_pii:
                                        comment_data = apply_pii_masking(comment_data)

                                    result = supabase_client.table(db_config["comment"]).upsert(
                                        comment_data, on_conflict="comment_id"
                                    ).execute()

                                    if result.data:
                                        total_comments += 1

                            except Exception as e:
                                logger.warning(f"    ⚠️ Failed to process comment: {e}")
                                continue

                    except Exception as e:
                        logger.warning(f"  ⚠️ Failed to process submission {submission.id}: {e}")
                        continue

                logger.info(f"  ✅ Processed comments for r/{subreddit_name}")
                time.sleep(3)

            except Exception as e:
                logger.error(f"  ❌ Failed to process r/{subreddit_name}: {e}")
                continue

        logger.info(f"✅ Standalone comment collection complete: {total_comments} comments")
        return True

    except Exception as e:
        logger.error(f"❌ Standalone comment collection failed: {e}")
        return False


def apply_pii_masking(data: dict[str, Any]) -> dict[str, Any]:
    """Apply PII masking to collected data (placeholder implementation)"""
    try:
        # For now, return data unchanged as ENABLE_PII_ANONYMIZATION is False
        # In a full implementation, this would use spaCy for PII detection and masking
        return data
    except Exception as e:
        logger.warning(f"⚠️ PII masking failed: {e}")
        return data


def get_collection_status(reddit_client, supabase_client, db_config: dict[str, str]) -> dict[str, Any]:
    """
    Get the current status of data collection.
    """
    try:
        # Get actual counts from database
        submissions_count = len(supabase_client.table(db_config["submission"]).select("submission_id").execute().data or [])
        comments_count = len(supabase_client.table(db_config["comment"]).select("comment_id").execute().data or [])
        redditors_count = len(supabase_client.table(db_config["user"]).select("user_id").execute().data or [])

        return {
            "status": "active",
            "last_collection": datetime.utcnow().isoformat(),
            "total_posts_collected": submissions_count,
            "total_comments_collected": comments_count,
            "total_redditors_collected": redditors_count,
            "collection_summary": f"{submissions_count} submissions, {comments_count} comments, {redditors_count} redditors"
        }
    except Exception as e:
        logger.error(f"❌ Failed to get collection status: {e}")
        return {
            "status": "error",
            "last_collection": None,
            "total_posts_collected": 0,
            "total_comments_collected": 0,
            "total_redditors_collected": 0,
            "error": str(e)
        }


def emergency_comment_collection(
    reddit_client,
    supabase_client,
    db_config: dict[str, str],
    target_subreddits: list[str] = None,
) -> bool:
    """
    EMERGENCY FUNCTION: Aggressive comment collection to fix the 0 comments crisis
    """
    if target_subreddits is None:
        target_subreddits = [
            "personalfinance", "investing", "fitness", "learnprogramming",
            "technology", "SaaS", "entrepreneur", "selfimprovement"
        ]

    try:
        logger.info(f"🚨 EMERGENCY COMMENT COLLECTION ACTIVATED")
        logger.info(f"🎯 Target: Collect comments for existing 937 submissions")

        # Use multiple strategies for maximum comment collection

        # Strategy 1: Process recent submissions with high comment counts
        success1 = collect_comments_for_submissions(
            reddit_client, supabase_client, db_config, target_subreddits,
            mask_pii=False, max_comments_per_submission=100, max_age_hours=168  # 7 days
        )

        # Strategy 2: Standalone comment collection
        success2 = collect_standalone_comments(
            reddit_client, supabase_client, db_config, target_subreddits,
            limit=2000, mask_pii=False
        )

        logger.info(f"🎯 EMERGENCY COLLECTION COMPLETE")
        return success1 or success2

    except Exception as e:
        logger.error(f"❌ Emergency comment collection failed: {e}")
        return False