#!/usr/bin/env python3
"""
IMMEDIATE COMMENT COLLECTION FIX
CRITICAL PRIORITY: Fix the 0 comments issue for 937 submissions
TIME SENSITIVE: Must start immediately to enable opportunity analysis
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Execute immediate comment collection fix"""

    print("\n" + "="*80)
    print("🚨 IMMEDIATE COMMENT COLLECTION FIX - CRITICAL PRIORITY")
    print("="*80)
    print("⚠️ CRITICAL ISSUE: 937 submissions collected, 0 comments collected")
    print("🎯 MISSION: Enable comprehensive comment collection for opportunity analysis")
    print("💬 Comments are ESSENTIAL for:")
    print("   • Understanding user pain points in detail")
    print("   • Identifying solution-seeking behavior")
    print("   • Detecting monetization signals")
    print("   • Validating opportunity scores")
    print("="*80)

    try:
        logger.info("🚀 Starting immediate comment collection fix")

        # Import core components
        from core.collection import emergency_comment_collection, get_collection_status
        from core.setup import setup_redditharbor
        from config.settings import DB_CONFIG, DEFAULT_SUBREDDITS

        logger.info("✅ Components imported successfully")

        # Setup RedditHarbor pipeline
        logger.info("🔧 Setting up RedditHarbor pipeline...")
        pipeline = setup_redditharbor()

        if not pipeline:
            logger.error("❌ Failed to setup RedditHarbor pipeline")
            return False

        logger.info("✅ RedditHarbor pipeline setup complete")

        # Get current status before collection
        logger.info("📊 Getting current collection status...")
        try:
            status_before = get_collection_status(
                pipeline.reddit_client,
                pipeline.supabase_client,
                DB_CONFIG
            )
            logger.info(f"📈 Before: {status_before.get('collection_summary', 'Unknown')}")
        except Exception as e:
            logger.warning(f"⚠️ Could not get before status: {e}")

        # Execute emergency comment collection
        logger.info("🚨 EXECUTING EMERGENCY COMMENT COLLECTION")
        start_time = time.time()

        success = emergency_comment_collection(
            reddit_client=pipeline.reddit_client,
            supabase_client=pipeline.supabase_client,
            db_config=DB_CONFIG,
            target_subreddits=DEFAULT_SUBREDDITS[:8]  # Focus on top 8 subreddits for immediate impact
        )

        collection_time = time.time() - start_time

        logger.info(f"🎯 Emergency collection completed in {collection_time:.2f} seconds")

        # Get status after collection
        logger.info("📊 Getting post-collection status...")
        time.sleep(3)  # Allow database to settle

        try:
            status_after = get_collection_status(
                pipeline.reddit_client,
                pipeline.supabase_client,
                DB_CONFIG
            )
            logger.info(f"📈 After: {status_after.get('collection_summary', 'Unknown')}")
        except Exception as e:
            logger.warning(f"⚠️ Could not get after status: {e}")

        # Report results
        if success:
            print("\n🎉 COMMENT COLLECTION FIX SUCCESSFUL!")
            print("✅ Comments have been collected and are ready for analysis")
            print("📊 Opportunity dashboards can now access comprehensive comment data")
            print("💬 Deep analysis of user pain points and solution-seeking is now possible")
        else:
            print("\n⚠️ Comment collection completed with limited success")
            print("🔧 Additional collection methods may be needed")

        print(f"\n⏱️ Collection completed in {collection_time:.2f} seconds")
        print("🌐 View collected data at: http://127.0.0.1:54323")

        return success

    except KeyboardInterrupt:
        logger.info("🛑 Comment collection interrupted by user")
        return False

    except Exception as e:
        logger.error(f"❌ Immediate comment fix failed: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

def verify_comment_collection():
    """Verify that comments were actually collected"""
    logger.info("🔍 Verifying comment collection results...")

    try:
        from core.setup import setup_redditharbor
        from config.settings import DB_CONFIG

        pipeline = setup_redditharbor()
        if not pipeline:
            logger.error("❌ Could not setup pipeline for verification")
            return False

        # Check comment count in database
        try:
            comments_result = pipeline.supabase_client.table(DB_CONFIG["comment"]).select("comment_id").execute()
            comment_count = len(comments_result.data) if comments_result.data else 0

            logger.info(f"💬 Total comments in database: {comment_count}")

            if comment_count > 0:
                logger.info("✅ Comment collection verification SUCCESSFUL!")

                # Get sample comments for analysis
                sample_comments = pipeline.supabase_client.table(DB_CONFIG["comment"]).select("*").limit(5).execute()

                if sample_comments.data:
                    logger.info("📄 Sample comments collected:")
                    for comment in sample_comments.data:
                        logger.info(f"  • r/{comment.get('subreddit', 'unknown')}: {comment.get('body', '')[:100]}...")

                return True
            else:
                logger.error("❌ No comments found - collection failed")
                return False

        except Exception as e:
            logger.error(f"❌ Database query failed: {e}")
            return False

    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    print(f"🕐 Starting immediate comment fix at {datetime.now().isoformat()}")

    # Execute the fix
    success = main()

    if success:
        print("\n🔍 Verifying collection results...")
        time.sleep(5)  # Allow time for data to settle
        verification_success = verify_comment_collection()

        if verification_success:
            print("\n🎉 CRITICAL ISSUE RESOLVED!")
            print("💬 Comments have been successfully collected for opportunity analysis")
            print("🚀 Opportunity dashboards and analysis tools can now function properly")
        else:
            print("\n⚠️ Collection completed but verification shows issues")
            print("🔧 Manual verification may be required")
    else:
        print("\n❌ Comment collection fix failed")
        print("🔧 Check logs for details and try alternative collection methods")

    print(f"\n🕐 Fix execution completed at {datetime.now().isoformat()}")