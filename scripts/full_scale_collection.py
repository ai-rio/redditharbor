#!/usr/bin/env python3
"""
Full-Scale RedditHarbor Data Collection
Collects from all 73 target subreddits across 6 market segments
"""

import sys
from pathlib import Path
import logging
from datetime import datetime

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redditharbor.login import reddit, supabase
from redditharbor.dock.pipeline import collect
from config.settings import (
    REDDIT_PUBLIC, REDDIT_SECRET, REDDIT_USER_AGENT,
    SUPABASE_URL, SUPABASE_KEY, DB_CONFIG
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('error_log/full_scale_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Target subreddits by market segment
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

logger.info(f"🎯 Starting Full-Scale Collection from {len(ALL_SUBREDDITS)} subreddits")
logger.info(f"📊 Market segments: {list(TARGET_SUBREDDITS.keys())}")

def main():
    try:
        # Create clients
        logger.info("🔑 Creating Reddit and Supabase clients...")
        reddit_client = reddit(
            public_key=REDDIT_PUBLIC,
            secret_key=REDDIT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
        supabase_client = supabase(
            url=SUPABASE_URL,
            private_key=SUPABASE_KEY
        )

        # Create pipeline
        logger.info("🔄 Initializing RedditHarbor pipeline...")
        pipeline = collect(
            reddit_client=reddit_client,
            supabase_client=supabase_client,
            db_config=DB_CONFIG
        )

        # Collection parameters
        sort_types = ["hot", "top", "new"]
        limit_per_sort = 50  # 50 posts per sort type
        mask_pii = False

        logger.info(f"📝 Collection parameters:")
        logger.info(f"   - Subreddits: {len(ALL_SUBREDDITS)}")
        logger.info(f"   - Sort types: {sort_types}")
        logger.info(f"   - Limit per sort: {limit_per_sort}")
        logger.info(f"   - Total expected: ~{len(ALL_SUBREDDITS) * len(sort_types) * limit_per_sort} submissions")

        # Collect from each market segment
        total_submissions = 0
        total_redditors = 0

        for segment_name, subreddits in TARGET_SUBREDDITS.items():
            logger.info(f"\n{'='*80}")
            logger.info(f"📈 Collecting from {segment_name.upper()} segment ({len(subreddits)} subreddits)")
            logger.info(f"{'='*80}")

            segment_submissions = 0
            segment_redditors = 0

            for subreddit in subreddits:
                logger.info(f"\n🔍 Processing r/{subreddit}...")

                try:
                    # Step 1: Collect submissions (posts)
                    logger.info(f"   📝 Collecting submissions...")
                    result = pipeline.subreddit_submission(
                        subreddits=[subreddit],
                        sort_types=sort_types,
                        limit=limit_per_sort,
                        mask_pii=mask_pii
                    )

                    if result:
                        subs_count, users_count = result
                        segment_submissions += subs_count
                        segment_redditors += users_count
                        total_submissions += subs_count
                        total_redditors += users_count
                        logger.info(f"      ✅ {subs_count} submissions, {users_count} users")
                    else:
                        logger.warning(f"      ⚠️  No submissions collected")

                    # Step 2: Collect comments (CRITICAL for AI insights!)
                    logger.info(f"   💬 Collecting comments...")
                    comment_limit = 20  # Collect comments from top 20 posts per subreddit
                    try:
                        pipeline.subreddit_comment(
                            subreddits=[subreddit],
                            sort_types=sort_types,
                            limit=comment_limit,
                            level=1,  # Only top-level comments (faster)
                            mask_pii=mask_pii
                        )
                        logger.info(f"      ✅ Comments collected from top {comment_limit} posts")
                    except Exception as comment_e:
                        logger.warning(f"      ⚠️  Comment collection failed: {str(comment_e)}")

                except Exception as e:
                    logger.error(f"   ❌ r/{subreddit}: Error - {str(e)}")

            logger.info(f"\n✅ {segment_name} segment complete:")
            logger.info(f"   📊 Submissions: {segment_submissions}")
            logger.info(f"   👥 Redditors: {segment_redditors}")

        # Final summary
        logger.info(f"\n{'='*80}")
        logger.info(f"🎉 FULL-SCALE COLLECTION COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"📊 Total Submissions: {total_submissions}")
        logger.info(f"👥 Total Redditors: {total_redditors}")
        logger.info(f"🏆 Success! Data collected from {len(ALL_SUBREDDITS)} subreddits")

        # Verify in database
        logger.info(f"\n🔍 Verifying database...")
        subs_result = supabase_client.table('submissions').select('count', count='exact').execute()
        comments_result = supabase_client.table('comments').select('count', count='exact').execute()
        redditors_result = supabase_client.table('redditors').select('count', count='exact').execute()

        logger.info(f"✅ Database verified:")
        logger.info(f"   📝 Submissions: {subs_result.count}")
        logger.info(f"   💬 Comments: {comments_result.count}")
        logger.info(f"   👥 Redditors: {redditors_result.count}")

        # Verify comment coverage
        if comments_result.count > 0:
            avg_comments = comments_result.count / subs_result.count if subs_result.count > 0 else 0
            logger.info(f"   📊 Avg comments per submission: {avg_comments:.1f}")
            logger.info(f"   ✅ Comments successfully collected!")
        else:
            logger.warning(f"   ⚠️  No comments found in database!")

        return True

    except Exception as e:
        logger.error(f"❌ Collection failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
