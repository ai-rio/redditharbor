#!/usr/bin/env python3
"""
RedditHarbor Monetizable App Research - Complete Data Collection
Collects data from all 73 target subreddits across 6 market segments
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('error_log/monetizable_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_collection():
    """Execute complete data collection for monetizable app research"""

    logger.info("=" * 80)
    logger.info("🚀 REDDITHARBOR MONETIZABLE APP RESEARCH DATA COLLECTION")
    logger.info("=" * 80)
    logger.info("")

    try:
        # Import RedditHarbor components
        from redditharbor.login import reddit, supabase

        from config.settings import DB_CONFIG
        from core.collection import (
            ALL_TARGET_SUBREDDITS,
            TARGET_SUBREDDITS,
            collect_monetizable_opportunities_data,
        )

        # Verify connections
        logger.info("🔍 Verifying connections...")

        # Test Reddit
        try:
            test_sub = reddit.subreddit("personalfinance")
            next(test_sub.hot(limit=1))
            logger.info("✅ Reddit API: Connected")
        except Exception as e:
            logger.error(f"❌ Reddit API: Failed - {e}")
            return False

        # Test Supabase
        try:
            supabase.table('submissions').select('count').limit(1).execute()
            logger.info("✅ Supabase: Connected")
        except Exception as e:
            logger.error(f"❌ Supabase: Failed - {e}")
            return False

        logger.info("")
        logger.info("📊 COLLECTION PLAN:")
        logger.info("=" * 80)

        total_subreddits = len(ALL_TARGET_SUBREDDITS)
        logger.info(f"Total target subreddits: {total_subreddits}")
        logger.info("Market segments:")

        for segment, subreddits in TARGET_SUBREDDITS.items():
            segment_name = segment.replace('_', ' & ').title()
            logger.info(f"  🎯 {segment_name}: {len(subreddits)} subreddits")

        logger.info("")
        logger.info("Collection settings:")
        logger.info("  - Posts per sort type: 100")
        logger.info("  - Sort types: hot, rising, top")
        logger.info("  - Time filter: month")
        logger.info("  - PII anonymization: DISABLED (for testing)")
        logger.info("")
        logger.info("=" * 80)
        logger.info("")

        # Start collection
        logger.info("🔄 Starting data collection...")
        logger.info("")

        success = collect_monetizable_opportunities_data(
            reddit_client=reddit,
            supabase_client=supabase,
            db_config=DB_CONFIG,
            market_segment="all",  # Collect from ALL segments
            limit_per_sort=100,
            time_filter="month",
            mask_pii=False,  # Disabled for testing
            sentiment_analysis=True,
            extract_problem_keywords=True,
            track_workarounds=True
        )

        if success:
            logger.info("")
            logger.info("=" * 80)
            logger.info("✅ DATA COLLECTION COMPLETED SUCCESSFULLY!")
            logger.info("=" * 80)
            logger.info("")
            logger.info("📈 Next steps:")
            logger.info("  1. Check collected data in Supabase Studio")
            logger.info("  2. Run opportunity scoring algorithm")
            logger.info("  3. Identify top opportunities (score 70+)")
            logger.info("  4. Validate simplicity constraint (1-3 core functions)")
            logger.info("  5. Build Marimo dashboard for visualization")
            logger.info("")
            logger.info("🎯 Access Supabase Studio:")
            logger.info("  http://127.0.0.1:54323")
            logger.info("")
            return True
        else:
            logger.error("")
            logger.error("=" * 80)
            logger.error("❌ DATA COLLECTION FAILED")
            logger.error("=" * 80)
            logger.error("")
            return False

    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("Make sure RedditHarbor is properly installed")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    try:
        success = run_collection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("🛑 Collection interrupted by user")
        sys.exit(1)
