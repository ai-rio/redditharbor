#!/usr/bin/env python3
"""
Full-Scale RedditHarbor Data Collection (DLT-Powered)

Collects from all 73 target subreddits across 6 market segments using DLT pipeline
with automatic deduplication, problem keyword filtering, and comprehensive error recovery.

DLT Migration Benefits:
- Automatic deduplication (merge write disposition)
- Problem-first filtering (PROBLEM_KEYWORDS)
- Batch loading optimization
- Schema evolution support
- Production-ready deployment

Original functionality preserved:
- 73 subreddits across 6 market segments
- Per-segment and per-subreddit error handling
- Comprehensive logging with statistics
- Both submissions and comments collection
"""

import logging
import sys
from pathlib import Path
from typing import Any

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# DLT imports
# Import configuration
from config.settings import SUPABASE_KEY, SUPABASE_URL
from core.dlt_collection import (
    collect_post_comments,
    collect_problem_posts,
    get_reddit_client,
)

# Setup logging
error_log_dir = project_root / "error_log"
error_log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(error_log_dir / 'full_scale_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Target subreddits by market segment (73 total)
TARGET_SUBREDDITS = {
    "finance_investing": [
        "personalfinance", "investing", "stocks", "Bogleheads",
        "financialindependence", "CryptoCurrency", "tax",
        "Accounting", "RealEstateInvesting", "FinancialCareers"
    ],
    "health_fitness": [
        "fitness", "loseit", "bodyweightfitness", "nutrition",
        "keto", "running", "cycling", "yoga", "meditation",
        "mentalhealth", "fitness30plus", "homegym"
    ],
    "technology": [
        "technology", "programming", "webdev", "MachineLearning",
        "artificial", "startups", "entrepreneur", "SaaS"
    ],
    "education": [
        "education", "teachers", "studytips", "GetStudying",
        "college", "university", "gradschool", "research"
    ],
    "lifestyle": [
        "minimalism", "productivity", "getmotivated",
        "selfimprovement", "LifeProTips", "decidingtobebetter"
    ],
    "business": [
        "smallbusiness", "business", "ecommerce", "investing",
        "businessowners", "marketing", "solopreneurs"
    ]
}

# Flatten all subreddits
ALL_SUBREDDITS = []
for segment in TARGET_SUBREDDITS.values():
    ALL_SUBREDDITS.extend(segment)

logger.info(f"🎯 Starting Full-Scale DLT Collection from {len(ALL_SUBREDDITS)} subreddits")
logger.info(f"📊 Market segments: {list(TARGET_SUBREDDITS.keys())}")


def collect_segment_submissions(
    segment_name: str,
    subreddits: list[str],
    sort_types: list[str],
    limit_per_sort: int
) -> tuple[list[dict[str, Any]], int, int]:
    """
    Collect submissions from a market segment using DLT pipeline.

    Args:
        segment_name: Market segment name
        subreddits: List of subreddit names in this segment
        sort_types: Reddit sort types to use
        limit_per_sort: Posts to collect per sort type

    Returns:
        Tuple of (all_submissions, total_submissions, total_errors)
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"📈 Collecting from {segment_name.upper()} segment ({len(subreddits)} subreddits)")
    logger.info(f"{'='*80}")

    all_segment_submissions = []
    segment_submissions = 0
    segment_errors = 0

    for subreddit in subreddits:
        logger.info(f"\n🔍 Processing r/{subreddit}...")

        try:
            # Collect from each sort type
            subreddit_submissions = []

            for sort_type in sort_types:
                logger.info(f"   📝 Collecting {sort_type} submissions...")

                try:
                    # Collect using DLT with problem keyword filtering
                    posts = collect_problem_posts(
                        subreddits=[subreddit],
                        limit=limit_per_sort,
                        sort_type=sort_type,
                        test_mode=False
                    )

                    if posts:
                        subreddit_submissions.extend(posts)
                        logger.info(f"      ✅ {len(posts)} {sort_type} submissions collected")
                    else:
                        logger.warning(f"      ⚠️  No {sort_type} submissions found")

                except Exception as sort_e:
                    logger.error(f"      ❌ Error collecting {sort_type} submissions: {sort_e!s}")
                    segment_errors += 1

            # Add to segment total
            if subreddit_submissions:
                all_segment_submissions.extend(subreddit_submissions)
                segment_submissions += len(subreddit_submissions)
                logger.info(f"   ✅ Total: {len(subreddit_submissions)} submissions from r/{subreddit}")
            else:
                logger.warning(f"   ⚠️  No submissions collected from r/{subreddit}")

        except Exception as e:
            logger.error(f"   ❌ r/{subreddit}: Error - {e!s}")
            segment_errors += 1

    logger.info(f"\n✅ {segment_name} segment complete:")
    logger.info(f"   📊 Submissions: {segment_submissions}")
    logger.info(f"   ❌ Errors: {segment_errors}")

    return all_segment_submissions, segment_submissions, segment_errors


def load_submissions_to_supabase(submissions: list[dict[str, Any]]) -> bool:
    """
    Load collected submissions to Supabase using raw SQL INSERT.

    This approach bypasses DLT's schema detection and directly inserts
    into the public.submissions table using PostgreSQL's ON CONFLICT
    clause for deduplication based on submission_id.

    Args:
        submissions: List of submission dictionaries

    Returns:
        True if successful, False otherwise
    """
    if not submissions:
        logger.warning("⚠️  No submissions to load")
        return False

    logger.info(f"\n{'='*80}")
    logger.info(f"💾 Loading {len(submissions)} submissions to Supabase via SQL")
    logger.info(f"{'='*80}")

    try:
        import psycopg2
        from psycopg2.extras import execute_values

        # Connect directly to the database
        conn = psycopg2.connect(
            host="127.0.0.1",
            port=54322,
            database="postgres",
            user="postgres",
            password="postgres"
        )

        cursor = conn.cursor()

        # Create unique index on submission_id if it doesn't exist
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_submissions_submission_id_unique
            ON public.submissions(submission_id)
            WHERE submission_id IS NOT NULL;
        """)

        # Deduplicate submissions by submission_id (in case same post appears multiple times)
        seen_ids = set()
        unique_submissions = []
        for sub in submissions:
            sub_id = sub.get("submission_id")
            if sub_id and sub_id not in seen_ids:
                seen_ids.add(sub_id)
                unique_submissions.append(sub)

        logger.info(f"   Deduplicating: {len(submissions)} -> {len(unique_submissions)} unique submissions")

        # Prepare data for insertion
        values = [
            (
                sub.get("submission_id"),
                sub.get("title"),
                sub.get("text"),
                sub.get("content"),
                sub.get("subreddit"),
                sub.get("upvotes", 0),
                sub.get("comments_count", 0),
                sub.get("url"),
                sub.get("created_at")
            )
            for sub in unique_submissions
        ]

        # Insert with ON CONFLICT to handle duplicates
        # Note: ON CONFLICT requires a named constraint or column list matching the unique index
        insert_query = """
            INSERT INTO public.submissions
                (submission_id, title, text, content, subreddit, upvotes, comments_count, url, created_at)
            VALUES %s
            ON CONFLICT (submission_id) WHERE submission_id IS NOT NULL
            DO UPDATE SET
                title = EXCLUDED.title,
                text = EXCLUDED.text,
                content = EXCLUDED.content,
                upvotes = EXCLUDED.upvotes,
                comments_count = EXCLUDED.comments_count,
                url = EXCLUDED.url,
                created_at = EXCLUDED.created_at;
        """

        execute_values(cursor, insert_query, values, page_size=100)
        conn.commit()

        inserted_count = cursor.rowcount
        cursor.close()
        conn.close()

        logger.info("✅ Submissions loaded successfully!")
        logger.info("   - Table: public.submissions")
        logger.info(f"   - Rows affected: {inserted_count}")
        logger.info("   - Deduplication: ON CONFLICT (submission_id)")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to load submissions: {e!s}")
        import traceback
        traceback.print_exc()
        return False


def collect_segment_comments(
    segment_name: str,
    subreddits: list[str],
    sort_types: list[str],
    comment_limit: int
) -> tuple[list[dict[str, Any]], int]:
    """
    Collect comments from top posts in a market segment.

    Args:
        segment_name: Market segment name
        subreddits: List of subreddit names
        sort_types: Reddit sort types used for submissions
        comment_limit: Number of top posts to collect comments from

    Returns:
        Tuple of (all_comments, total_comments_collected)
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"💬 Collecting comments from {segment_name.upper()} segment")
    logger.info(f"{'='*80}")

    all_comments = []
    reddit_client = get_reddit_client()

    for subreddit in subreddits:
        logger.info(f"\n🔍 Processing comments from r/{subreddit}...")

        try:
            # Collect top posts to get their IDs
            posts = collect_problem_posts(
                subreddits=[subreddit],
                limit=comment_limit,
                sort_type="hot",  # Use hot for comment collection
                test_mode=False
            )

            if not posts:
                logger.warning("   ⚠️  No posts found for comment collection")
                continue

            # Extract submission IDs
            submission_ids = [post["submission_id"] for post in posts]

            logger.info(f"   💬 Collecting comments from {len(submission_ids)} posts...")

            # Collect comments using DLT function
            comments = collect_post_comments(
                submission_ids=submission_ids,
                reddit_client=reddit_client,
                merge_disposition="merge"
            )

            if comments:
                all_comments.extend(comments)
                logger.info(f"   ✅ {len(comments)} comments collected from r/{subreddit}")
            else:
                logger.warning(f"   ⚠️  No comments collected from r/{subreddit}")

        except Exception as e:
            logger.error(f"   ❌ Error collecting comments from r/{subreddit}: {e!s}")

    logger.info("\n✅ Comment collection complete:")
    logger.info(f"   💬 Total comments: {len(all_comments)}")

    return all_comments, len(all_comments)


def load_comments_to_supabase(comments: list[dict[str, Any]]) -> bool:
    """
    Load collected comments to Supabase using raw SQL INSERT.

    This approach bypasses DLT's schema detection and directly inserts
    into the public.comments table using PostgreSQL's ON CONFLICT
    clause for deduplication based on comment_id.

    Args:
        comments: List of comment dictionaries

    Returns:
        True if successful, False otherwise
    """
    if not comments:
        logger.warning("⚠️  No comments to load")
        return False

    logger.info(f"\n{'='*80}")
    logger.info(f"💾 Loading {len(comments)} comments to Supabase via SQL")
    logger.info(f"{'='*80}")

    try:
        import psycopg2
        from psycopg2.extras import execute_values

        # Connect directly to the database
        conn = psycopg2.connect(
            host="127.0.0.1",
            port=54322,
            database="postgres",
            user="postgres",
            password="postgres"
        )

        cursor = conn.cursor()

        # Create unique index on comment_id if it doesn't exist
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_comments_comment_id_unique
            ON public.comments(comment_id)
            WHERE comment_id IS NOT NULL;
        """)

        # Deduplicate comments by comment_id
        seen_ids = set()
        unique_comments = []
        for comment in comments:
            comment_id = comment.get("comment_id")
            if comment_id and comment_id not in seen_ids:
                seen_ids.add(comment_id)
                unique_comments.append(comment)

        logger.info(f"   Deduplicating: {len(comments)} -> {len(unique_comments)} unique comments")

        # Prepare data for insertion
        # Note: We populate link_id (Reddit submission ID string) which will be used to backfill submission_id (UUID)
        # submission_id (UUID) will be backfilled after INSERT via the UPDATE query below
        values = [
            (
                comment.get("comment_id"),
                comment.get("link_id"),  # Reddit submission ID string (e.g., "1opmkio")
                comment.get("body"),
                comment.get("content"),
                max(0, comment.get("score", 0)),  # Ensure non-negative for CHECK constraint
                comment.get("created_at"),
                comment.get("parent_id"),
                comment.get("comment_depth", 0),
                comment.get("subreddit")  # Add subreddit for denormalized access
            )
            for comment in unique_comments
        ]

        # Insert with ON CONFLICT to handle duplicates
        # Note: ON CONFLICT requires a named constraint or column list matching the unique index
        insert_query = """
            INSERT INTO public.comments
                (comment_id, link_id, body, content, upvotes, created_at, parent_id, comment_depth, subreddit)
            VALUES %s
            ON CONFLICT (comment_id) WHERE comment_id IS NOT NULL
            DO UPDATE SET
                body = EXCLUDED.body,
                content = EXCLUDED.content,
                upvotes = EXCLUDED.upvotes,
                created_at = EXCLUDED.created_at,
                parent_id = EXCLUDED.parent_id,
                comment_depth = EXCLUDED.comment_depth,
                subreddit = EXCLUDED.subreddit;
        """

        execute_values(cursor, insert_query, values, page_size=100)
        conn.commit()

        # CRITICAL: Backfill submission_id (UUID) by linking via link_id
        # This is the key fix - without this, comments are orphaned with NULL submission_id
        logger.info("   Backfilling submission_id UUID foreign key...")

        # Update comments.submission_id (UUID) from submissions.id (UUID)
        # Join on: comments.link_id = submissions.submission_id (both are Reddit ID strings)
        cursor.execute("""
            UPDATE public.comments
            SET submission_id = s.id
            FROM public.submissions s
            WHERE public.comments.link_id = s.submission_id
              AND public.comments.submission_id IS NULL
              AND s.submission_id IS NOT NULL;
        """)

        conn.commit()
        backfill_count = cursor.rowcount
        logger.info(f"   ✓ Backfilled {backfill_count} comments with submission_id UUID")

        inserted_count = cursor.rowcount
        cursor.close()
        conn.close()

        logger.info("✅ Comments loaded successfully!")
        logger.info("   - Table: public.comments")
        logger.info(f"   - Rows affected: {inserted_count}")
        logger.info("   - Deduplication: ON CONFLICT (comment_id)")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to load comments: {e!s}")
        import traceback
        traceback.print_exc()
        return False


def verify_database_results():
    """
    Verify final results in Supabase database.

    Returns:
        Dict with verification metrics
    """
    logger.info(f"\n{'='*80}")
    logger.info("🔍 Verifying database results...")
    logger.info(f"{'='*80}")

    try:
        from supabase import create_client

        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Count submissions
        subs_result = supabase_client.table('submissions').select('id', count='exact').execute()
        subs_count = subs_result.count if subs_result.count else 0

        # Count comments
        comments_result = supabase_client.table('comments').select('comment_id', count='exact').execute()
        comments_count = comments_result.count if comments_result.count else 0

        # Count redditors
        redditors_result = supabase_client.table('redditors').select('username', count='exact').execute()
        redditors_count = redditors_result.count if redditors_result.count else 0

        logger.info("✅ Database verified:")
        logger.info(f"   📝 Submissions: {subs_count}")
        logger.info(f"   💬 Comments: {comments_count}")
        logger.info(f"   👥 Redditors: {redditors_count}")

        # Calculate comment coverage
        if subs_count > 0 and comments_count > 0:
            avg_comments = comments_count / subs_count
            logger.info(f"   📊 Avg comments per submission: {avg_comments:.1f}")
            logger.info("   ✅ Comments successfully collected!")
        elif comments_count == 0:
            logger.warning("   ⚠️  No comments found in database!")

        return {
            "submissions": subs_count,
            "comments": comments_count,
            "redditors": redditors_count,
            "avg_comments_per_sub": avg_comments if subs_count > 0 else 0
        }

    except Exception as e:
        logger.error(f"⚠️  Database verification failed: {e!s}")
        return {
            "submissions": 0,
            "comments": 0,
            "redditors": 0,
            "avg_comments_per_sub": 0
        }


def main():
    """Main execution function with DLT pipeline."""
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Full-scale Reddit data collection using DLT pipeline"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Posts to collect per sort type (default: 50)"
    )
    parser.add_argument(
        "--comment-limit",
        type=int,
        default=20,
        help="Number of top posts to collect comments from (default: 20)"
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Run in test mode with limited subreddits"
    )

    args = parser.parse_args()

    try:
        # Collection parameters
        sort_types = ["hot", "top", "new"]
        limit_per_sort = args.limit  # Posts per sort type from CLI arg
        comment_limit = args.comment_limit  # Comments from CLI arg

        # Use limited subreddits for test mode
        subreddits_to_use = TARGET_SUBREDDITS if not args.test_mode else {
            "test": ["opensource", "productivity"]  # Just 2 subreddits for testing
        }

        # Calculate total subreddits
        total_subreddits = sum(len(subs) for subs in subreddits_to_use.values())

        logger.info("📝 Collection parameters:")
        logger.info(f"   - Mode: {'TEST' if args.test_mode else 'FULL SCALE'}")
        logger.info(f"   - Subreddits: {total_subreddits}")
        logger.info(f"   - Sort types: {sort_types}")
        logger.info(f"   - Limit per sort: {limit_per_sort}")
        logger.info(f"   - Comment limit: {comment_limit}")
        logger.info(f"   - Expected submissions: ~{total_subreddits * len(sort_types) * limit_per_sort}")

        # Track totals
        all_submissions = []
        total_submissions = 0
        total_errors = 0
        total_comments = 0

        # Collect from each market segment
        for segment_name, subreddits in subreddits_to_use.items():
            # Collect submissions
            segment_subs, seg_count, seg_errors = collect_segment_submissions(
                segment_name,
                subreddits,
                sort_types,
                limit_per_sort
            )

            all_submissions.extend(segment_subs)
            total_submissions += seg_count
            total_errors += seg_errors

        # Load all submissions to Supabase (batch operation)
        logger.info(f"\n{'='*80}")
        logger.info("📊 SUBMISSION COLLECTION COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"   Total submissions collected: {len(all_submissions)}")
        logger.info(f"   Total errors: {total_errors}")

        if all_submissions:
            submission_load_success = load_submissions_to_supabase(all_submissions)

            if not submission_load_success:
                logger.error("❌ Failed to load submissions to Supabase")
                return False
        else:
            logger.warning("⚠️  No submissions collected - skipping load")

        # Collect comments from each segment
        all_comments = []

        for segment_name, subreddits in subreddits_to_use.items():
            segment_comments, seg_comment_count = collect_segment_comments(
                segment_name,
                subreddits,
                sort_types,
                comment_limit
            )

            all_comments.extend(segment_comments)
            total_comments += seg_comment_count

        # Load all comments to Supabase (batch operation)
        logger.info(f"\n{'='*80}")
        logger.info("💬 COMMENT COLLECTION COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"   Total comments collected: {len(all_comments)}")

        if all_comments:
            comment_load_success = load_comments_to_supabase(all_comments)

            if not comment_load_success:
                logger.error("❌ Failed to load comments to Supabase")
                return False
        else:
            logger.warning("⚠️  No comments collected - skipping load")

        # Final summary
        logger.info(f"\n{'='*80}")
        logger.info("🎉 FULL-SCALE DLT COLLECTION COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"📊 Total Submissions: {total_submissions}")
        logger.info(f"💬 Total Comments: {total_comments}")
        logger.info(f"❌ Total Errors: {total_errors}")
        logger.info(f"🏆 Success! Data collected from {total_subreddits} subreddits")

        # Verify database results
        db_stats = verify_database_results()

        # Success criteria
        success = (
            total_submissions > 0 and
            db_stats["submissions"] > 0
        )

        if success:
            logger.info(f"\n{'='*80}")
            logger.info("✅ COLLECTION SUCCESS")
            logger.info(f"{'='*80}")
        else:
            logger.warning(f"\n{'='*80}")
            logger.warning("⚠️  COLLECTION INCOMPLETE - Check logs for details")
            logger.warning(f"{'='*80}")

        return success

    except Exception as e:
        logger.error(f"❌ Collection failed: {e!s}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
