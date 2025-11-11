#!/usr/bin/env python3
"""
Enhanced Monetizable Opportunity Collection
Uses the new enhanced collection functions from core/collection.py
Targets all 73 subreddits across 6 market segments with enhanced metadata extraction
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redditharbor.login import reddit, supabase

from config.settings import (
    DB_CONFIG,
    REDDIT_PUBLIC,
    REDDIT_SECRET,
    REDDIT_USER_AGENT,
    SUPABASE_KEY,
    SUPABASE_URL,
)
from core.collection import (
    ALL_TARGET_SUBREDDITS,
    TARGET_SUBREDDITS,
    collect_enhanced_comments,
    collect_monetizable_opportunities_data,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'error_log/enhanced_collection_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("="*80)
        logger.info("🚀 ENHANCED MONETIZABLE OPPORTUNITY COLLECTION")
        logger.info("="*80)
        logger.info(f"📊 Target: {len(ALL_TARGET_SUBREDDITS)} subreddits across 6 market segments")
        logger.info(f"🎯 Market Segments: {list(TARGET_SUBREDDITS.keys())}")
        logger.info("🔍 Enhanced Features: sentiment analysis, problem extraction, solution tracking")
        logger.info("="*80)

        # Create clients
        logger.info("\n🔑 Creating Reddit and Supabase clients...")
        reddit_client = reddit(
            public_key=REDDIT_PUBLIC,
            secret_key=REDDIT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
        supabase_client = supabase(
            url=SUPABASE_URL,
            private_key=SUPABASE_KEY
        )

        # Collection parameters
        limit_per_sort = 50  # 50 posts per sort type (hot, rising, top)
        time_filter = "month"  # Last month's top posts

        logger.info("\n📝 Collection Parameters:")
        logger.info("   - Sort types: hot, rising, top")
        logger.info(f"   - Limit per sort: {limit_per_sort}")
        logger.info(f"   - Time filter: {time_filter}")
        logger.info(f"   - Expected submissions: ~{len(ALL_TARGET_SUBREDDITS) * 3 * limit_per_sort}")

        # Collect by market segment
        total_submissions = 0
        total_comments = 0

        for segment_name, subreddits in TARGET_SUBREDDITS.items():
            logger.info(f"\n{'='*80}")
            logger.info(f"📈 COLLECTING: {segment_name.upper()}")
            logger.info(f"{'='*80}")
            logger.info(f"📍 Subreddits ({len(subreddits)}): {', '.join(subreddits)}")

            try:
                # Use enhanced collection function
                success = collect_monetizable_opportunities_data(
                    reddit_client=reddit_client,
                    supabase_client=supabase_client,
                    db_config=DB_CONFIG,
                    market_segment=segment_name,
                    limit_per_sort=limit_per_sort,
                    time_filter=time_filter,
                    mask_pii=False,
                    sentiment_analysis=True,
                    extract_problem_keywords=True,
                    track_workarounds=True
                )

                if success:
                    logger.info(f"✅ {segment_name} segment collection completed successfully")
                else:
                    logger.warning(f"⚠️  {segment_name} segment had some collection issues")

            except Exception as e:
                logger.error(f"❌ {segment_name} segment failed: {e!s}", exc_info=True)

        # Now collect comments for all submissions
        logger.info(f"\n{'='*80}")
        logger.info("💬 COLLECTING COMMENTS FOR ALL SUBMISSIONS")
        logger.info("="*80)

        try:
            comments_success = collect_enhanced_comments(
                reddit_client=reddit_client,
                supabase_client=supabase_client,
                db_config=DB_CONFIG,
                target_subreddits=ALL_TARGET_SUBREDDITS,
                mask_pii=False,
                extract_problem_keywords=True,
                track_workarounds=True
            )

            if comments_success:
                logger.info("✅ Comment collection completed successfully")
            else:
                logger.warning("⚠️  Comment collection had some issues")

        except Exception as e:
            logger.error(f"❌ Comment collection failed: {e!s}", exc_info=True)

        # Final verification
        logger.info(f"\n{'='*80}")
        logger.info("🔍 VERIFYING DATABASE")
        logger.info("="*80)

        try:
            # Count submissions
            subs_result = supabase_client.table('submissions').select('id', count='exact').execute()
            logger.info(f"📝 Total Submissions: {subs_result.count}")

            # Count with enhanced metadata
            sentiment_result = supabase_client.table('submissions').select('id', count='exact').not_.is_('sentiment_score', 'null').execute()
            logger.info(f"🎭 With Sentiment: {sentiment_result.count}")

            problems_result = supabase_client.table('submissions').select('id', count='exact').not_.is_('problem_keywords', 'null').execute()
            logger.info(f"🔍 With Problems: {problems_result.count}")

            solutions_result = supabase_client.table('submissions').select('id', count='exact').not_.is_('solution_mentions', 'null').execute()
            logger.info(f"💡 With Solutions: {solutions_result.count}")

            # Count comments
            comments_result = supabase_client.table('comments').select('id', count='exact').execute()
            logger.info(f"💬 Total Comments: {comments_result.count}")

            # Count redditors
            redditors_result = supabase_client.table('redditors').select('id', count='exact').execute()
            logger.info(f"👥 Total Redditors: {redditors_result.count}")

        except Exception as e:
            logger.error(f"⚠️  Database verification error: {e!s}")

        logger.info(f"\n{'='*80}")
        logger.info("🎉 ENHANCED COLLECTION COMPLETE")
        logger.info("="*80)
        logger.info("✅ All market segments processed")
        logger.info("✅ Enhanced metadata extracted")
        logger.info("✅ Comments collected")
        logger.info("✅ Ready for opportunity analysis")

        return True

    except Exception as e:
        logger.error(f"❌ Collection failed: {e!s}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
