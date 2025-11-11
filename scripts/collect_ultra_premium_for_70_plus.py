#!/usr/bin/env python3
"""
Ultra-Premium Reddit Data Collection for 70+ Score Opportunities

Strategy: Target ultra-premium subreddits with VC-level, high-stakes pain
where users demonstrate proven willingness to pay for solutions.

Based on E2E testing guide, 70+ scores require:
- Ultra-high stakes decisions (6-7 figure investments)
- Proven willingness to pay ($100-500/month solutions)
- Professional/B2B contexts with measurable ROI
- Complex problems with significant business impact

Collection Strategy:
1. Ultra-premium subreddits (venturecapital, financialindependence, etc.)
2. High-engagement posts (top posts = stronger pain signals)
3. Volume: 1000+ posts for statistical significance
4. Focus on professional domains with business impact
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv(project_root / '.env.local')

from core.dlt_collection import collect_problem_posts
from scripts.full_scale_collection import load_submissions_to_supabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('error_log/ultra_premium_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ultra-premium subreddits with VC-level, high-stakes pain
ULTRA_PREMIUM_SUBREDDITS = {
    "venturecapital": {
        "description": "VC-level investment decisions, fund management pain",
        "monetization": "Ultra-high ($100-500/month)",
        "stakes": "Multi-million dollar investment decisions",
        "limit": 200
    },
    "financialindependence": {
        "description": "High net worth individuals, retirement planning",
        "monetization": "High ($49-199/month)",
        "stakes": "7-8 figure portfolio decisions",
        "limit": 200
    },
    "realestateinvesting": {
        "description": "Real estate investors, property acquisition",
        "monetization": "High ($29-99/month)",
        "stakes": "Multi-million property investments",
        "limit": 200
    },
    "investing": {
        "description": "Investment strategy and portfolio management",
        "monetization": "Medium-High ($19-79/month)",
        "stakes": "Significant investment capital",
        "limit": 200
    },
    "startups": {
        "description": "Startup founders, business scaling challenges",
        "monetization": "High ($29-99/month)",
        "stakes": "Company valuation and funding",
        "limit": 200
    }
}

# Additional premium subreddits for expanded reach
PREMIUM_SUBREDDITS = {
    "SaaS": {
        "description": "SaaS business owners, recurring revenue",
        "monetization": "High ($29-99/month)",
        "stakes": "Business revenue and growth",
        "limit": 150
    },
    "smallbusiness": {
        "description": "Small business owners, operational efficiency",
        "monetization": "Medium-High ($19-79/month)",
        "stakes": "Business profitability",
        "limit": 150
    },
    "Entrepreneur": {
        "description": "Business scaling and strategy challenges",
        "monetization": "High ($29-99/month)",
        "stakes": "Business growth and valuation",
        "limit": 150
    },
    "consulting": {
        "description": "Consultants, client management and scaling",
        "monetization": "Medium-High ($29-79/month)",
        "stakes": "Revenue optimization",
        "limit": 100
    },
    "freelance": {
        "description": "Freelancers, income optimization and scaling",
        "monetization": "Medium ($19-49/month)",
        "stakes": "Income stability and growth",
        "limit": 100
    }
}

def collect_from_subreddit(subreddit_name, config, sort_type="top"):
    """Collect posts from a specific subreddit with configuration."""
    logger.info(f"🎯 Collecting from r/{subreddit_name}...")
    logger.info(f"   Description: {config['description']}")
    logger.info(f"   Monetization: {config['monetization']}")
    logger.info(f"   Stakes: {config['stakes']}")
    logger.info(f"   Target posts: {config['limit']}")

    try:
        posts = collect_problem_posts(
            subreddits=[subreddit_name],
            limit=config['limit'],
            sort_type=sort_type,
            test_mode=False
        )

        if posts:
            # Add metadata to posts for analysis
            for post in posts:
                post['collection_metadata'] = {
                    'subreddit_category': 'ultra_premium' if subreddit_name in ULTRA_PREMIUM_SUBREDDITS else 'premium',
                    'expected_monetization': config['monetization'],
                    'stakes_level': config['stakes'],
                    'collection_date': datetime.now().isoformat()
                }

            logger.info(f"✅ Collected {len(posts)} posts from r/{subreddit_name}")
            return posts
        else:
            logger.warning(f"⚠️  No posts collected from r/{subreddit_name}")
            return []

    except Exception as e:
        logger.error(f"❌ Error collecting from r/{subreddit_name}: {e}")
        return []

def main():
    """Main collection function for ultra-premium data gathering."""
    logger.info("🚀 Starting Ultra-Premium Reddit Data Collection for 70+ Opportunities")
    logger.info("📊 Target: 1000+ posts from ultra-premium subreddits")
    logger.info("🎯 Goal: Find 70+ score opportunities (unicorn apps)")

    all_posts = []
    collection_summary = {}

    # Phase 1: Ultra-premium subreddits (highest priority)
    logger.info("\n📍 Phase 1: Ultra-Premium Subreddits (VC-level)")
    logger.info("=" * 60)

    for subreddit_name, config in ULTRA_PREMIUM_SUBREDDITS.items():
        posts = collect_from_subreddit(subreddit_name, config, sort_type="top")
        if posts:
            all_posts.extend(posts)
            collection_summary[subreddit_name] = {
                'collected': len(posts),
                'category': 'ultra_premium',
                'monetization': config['monetization']
            }

    # Phase 2: Premium subreddits (expansion)
    logger.info("\n📍 Phase 2: Premium Subreddits (High-value)")
    logger.info("=" * 60)

    for subreddit_name, config in PREMIUM_SUBREDDITS.items():
        posts = collect_from_subreddit(subreddit_name, config, sort_type="top")
        if posts:
            all_posts.extend(posts)
            collection_summary[subreddit_name] = {
                'collected': len(posts),
                'category': 'premium',
                'monetization': config['monetization']
            }

    # Load to database
    logger.info(f"\n📤 Loading {len(all_posts)} posts to Supabase...")

    try:
        load_submissions_to_supabase(all_posts)
        logger.info("✅ Successfully loaded all posts to database")
    except Exception as e:
        logger.error(f"❌ Error loading to database: {e}")
        return

    # Collection summary
    logger.info("\n📊 Collection Summary")
    logger.info("=" * 60)
    total_collected = sum(summary['collected'] for summary in collection_summary.values())
    ultra_premium_count = sum(1 for summary in collection_summary.values() if summary['category'] == 'ultra_premium')
    premium_count = sum(1 for summary in collection_summary.values() if summary['category'] == 'premium')

    logger.info(f"📈 Total posts collected: {total_collected}")
    logger.info(f"🏆 Ultra-premium subreddits: {ultra_premium_count}")
    logger.info(f"⭐ Premium subreddits: {premium_count}")

    logger.info("\n🎯 Detailed Breakdown:")
    for subreddit, summary in collection_summary.items():
        logger.info(f"   r/{subreddit}: {summary['collected']} posts ({summary['category']}) - {summary['monetization']}")

    # Next steps
    logger.info("\n🚀 Next Steps for 70+ Opportunity Detection:")
    logger.info("1. Run batch scoring: python scripts/batch_opportunity_scoring.py")
    logger.info("2. Monitor for high scores (70+): Check dashboard and database")
    logger.info("3. Expected: 0-5 opportunities at 70+ (extremely rare but valuable)")
    logger.info("4. Cost estimate: ~$500-1000 in LLM profiling")
    logger.info("5. Time estimate: 60-90 minutes for full processing")

    logger.info(f"\n✅ Ultra-premium collection completed at {datetime.now().isoformat()}")
    logger.info("🎯 Ready for 70+ opportunity detection!")

if __name__ == "__main__":
    main()
