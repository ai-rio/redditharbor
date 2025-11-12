#!/usr/bin/env python3
"""
Continuous RedditHarbor Collection System
Automated daily harvesting with intelligent subreddit rotation and quality control
"""

import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import schedule

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv(project_root / '.env.local')

import os

from core.dlt_collection import collect_problem_posts
from scripts.full_scale_collection import load_submissions_to_supabase
from supabase import create_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('error_log/continuous_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ContinuousCollectionSystem:
    """Automated continuous collection system with intelligent subreddit rotation"""

    def __init__(self):
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )

        # Performance tracking for subreddit rotation
        self.subreddit_performance = {}
        self.collection_history = []

        # Collection strategy tiers
        self.daily_rotation_tiers = {
            'ultra_premium': [
                'venturecapital', 'financialindependence', 'realestateinvesting',
                'investing', 'startups', 'Entrepreneur'
            ],
            'premium_business': [
                'SaaS', 'smallbusiness', 'consulting', 'freelance',
                'sales', 'marketing'
            ],
            'tech_development': [
                'programming', 'webdev', 'devops', 'datascience',
                'MachineLearning', 'cybersecurity'
            ],
            'health_wellness': [
                'fitness', 'nutrition', 'mentalhealth', 'health',
                'Productivity'
            ]
        }

    def get_high_performance_subreddits(self, limit: int = 10) -> list[str]:
        """Analyze historical performance to select high-performing subreddits"""
        try:
            # Query recent high-scoring opportunities
            result = self.supabase.table('app_opportunities').select(
                'subreddit, opportunity_score'
            ).gte('opportunity_score', 45.0).order('created_at', desc=True).limit(100).execute()

            # Calculate performance metrics
            subreddit_scores = {}
            for opportunity in result.data or []:
                subreddit = opportunity.get('subreddit', 'unknown')
                score = opportunity.get('opportunity_score', 0)

                if subreddit not in subreddit_scores:
                    subreddit_scores[subreddit] = []
                subreddit_scores[subreddit].append(score)

            # Calculate average scores and sort
            avg_scores = {}
            for subreddit, scores in subreddit_scores.items():
                if len(scores) >= 2:  # Need at least 2 data points
                    avg_scores[subreddit] = sum(scores) / len(scores)

            # Return top performing subreddits
            sorted_subreddits = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)
            return [subreddit for subreddit, _ in sorted_subreddits[:limit]]

        except Exception as e:
            logger.error(f"Error analyzing subreddit performance: {e}")
            # Fallback to default ultra-premium list
            return self.daily_rotation_tiers['ultra_premium'][:limit]

    def adaptive_subreddit_selection(self, daily_target: int = 20) -> dict[str, int]:
        """Intelligently select subreddits based on performance and diversity"""

        # Get high performers (40% of collection)
        high_performers = self.get_high_performance_subreddits(limit=8)
        high_performer_allocation = int(daily_target * 0.4)

        # Allocate based on performance
        allocation = {}
        for i, subreddit in enumerate(high_performers):
            # Give more allocation to better performers
            weight = (len(high_performers) - i) / sum(range(1, len(high_performers) + 1))
            allocation[subreddit] = max(10, int(high_performer_allocation * weight))

        # Fill remaining with rotation tiers (60% of collection)
        remaining_allocation = daily_target - sum(allocation.values())

        # Rotate through tiers daily
        today = datetime.now().weekday()
        tier_key = list(self.daily_rotation_tiers.keys())[today % len(self.daily_rotation_tiers)]
        rotation_subreddits = self.daily_rotation_tiers[tier_key]

        per_subreddit = max(5, remaining_allocation // len(rotation_subreddits))
        for subreddit in rotation_subreddits:
            if subreddit not in allocation:  # Avoid duplicates
                allocation[subreddit] = per_subreddit

        logger.info(f"📊 Adaptive subreddit selection for {daily_target} posts:")
        for subreddit, count in allocation.items():
            logger.info(f"   r/{subreddit}: {count} posts")

        return allocation

    def collect_daily_posts(self, test_mode: bool = False) -> dict[str, Any]:
        """Main daily collection function"""
        logger.info("🌅 Starting Daily Continuous Collection")
        logger.info(f"📅 Collection date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Get intelligent subreddit allocation
        subreddit_allocation = self.adaptive_subreddit_selection(daily_target=50)

        all_posts = []
        collection_stats = {}

        for subreddit_name, target_count in subreddit_allocation.items():
            logger.info(f"🎯 Collecting from r/{subreddit_name} (target: {target_count})")

            try:
                posts = collect_problem_posts(
                    subreddits=[subreddit_name],
                    limit=target_count,
                    sort_type="top",  # Focus on high-engagement content
                    test_mode=test_mode
                )

                if posts:
                    # Add continuous collection metadata
                    for post in posts:
                        post['continuous_collection_metadata'] = {
                            'collection_type': 'daily_continuous',
                            'collection_date': datetime.now().isoformat(),
                            'target_subreddit': subreddit_name,
                            'allocation_reason': 'adaptive_performance_based',
                            'daily_target': target_count
                        }

                    all_posts.extend(posts)
                    collection_stats[subreddit_name] = {
                        'target': target_count,
                        'collected': len(posts),
                        'success_rate': len(posts) / target_count
                    }
                    logger.info(f"✅ Collected {len(posts)} posts from r/{subreddit_name}")
                else:
                    logger.warning(f"⚠️  No posts collected from r/{subreddit_name}")
                    collection_stats[subreddit_name] = {
                        'target': target_count,
                        'collected': 0,
                        'success_rate': 0.0
                    }

                # Be respectful to Reddit API
                time.sleep(2)

            except Exception as e:
                logger.error(f"❌ Error collecting from r/{subreddit_name}: {e}")
                collection_stats[subreddit_name] = {
                    'target': target_count,
                    'collected': 0,
                    'success_rate': 0.0,
                    'error': str(e)
                }
                continue

        # Load to database
        logger.info(f"📤 Loading {len(all_posts)} posts to Supabase...")

        try:
            load_submissions_to_supabase(all_posts)
            logger.info("✅ Successfully loaded daily collection to database")
        except Exception as e:
            logger.error(f"❌ Error loading to database: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'stats': collection_stats
            }

        # Generate daily report
        total_target = sum(s['target'] for s in collection_stats.values())
        total_collected = sum(s['collected'] for s in collection_stats.values())
        overall_success_rate = total_collected / total_target if total_target > 0 else 0

        daily_report = {
            'collection_date': datetime.now().isoformat(),
            'status': 'success',
            'total_target': total_target,
            'total_collected': total_collected,
            'overall_success_rate': overall_success_rate,
            'subreddit_stats': collection_stats,
            'subreddit_count': len(collection_stats),
            'avg_posts_per_subreddit': total_collected / len(collection_stats) if collection_stats else 0
        }

        # Store collection metrics
        try:
            self.supabase.table('continuous_collection_metrics').insert(daily_report).execute()
            logger.info("📊 Daily collection metrics stored")
        except Exception as e:
            logger.warning(f"⚠️  Could not store collection metrics: {e}")

        # Log summary
        logger.info("\n📊 DAILY COLLECTION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"📈 Target posts: {total_target}")
        logger.info(f"✅ Collected: {total_collected}")
        logger.info(f"📊 Success rate: {overall_success_rate:.1%}")
        logger.info(f"🎯 Subreddits: {len(collection_stats)}")
        logger.info(f"📈 Avg per subreddit: {daily_report['avg_posts_per_subreddit']:.1f}")

        return daily_report

    def setup_daily_schedule(self):
        """Setup automatic daily collection schedule"""
        logger.info("⏰ Setting up daily collection schedule")

        # Schedule collection for optimal Reddit engagement times
        # 9:00 AM EST (when Reddit activity peaks)
        schedule.every().day.at("09:00").do(self.collect_daily_posts)

        # Optional: Secondary collection at 2:00 PM EST for additional coverage
        # schedule.every().day.at("14:00").do(self.collect_daily_posts, test_mode=True)

        logger.info("✅ Daily collection scheduled for 09:00 AM EST")
        logger.info("🔄 System will run continuously. Press Ctrl+C to stop.")

    def run_scheduler(self):
        """Run the continuous collection scheduler"""
        self.setup_daily_schedule()

        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("🛑 Continuous collection stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes before retry

def main():
    """Main entry point for continuous collection system"""
    logger.info("🚀 RedditHarbor Continuous Collection System")
    logger.info("📊 Automated daily harvesting with intelligent subreddit rotation")

    system = ContinuousCollectionSystem()

    # Check if running as script or imported
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        logger.info("🧪 Running in test mode (single collection)")
        result = system.collect_daily_posts(test_mode=True)
        logger.info(f"📊 Test result: {result}")
    else:
        logger.info("🔄 Starting continuous collection scheduler...")
        system.run_scheduler()

if __name__ == "__main__":
    main()
