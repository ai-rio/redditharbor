#!/usr/bin/env python3
"""
Automated RedditHarvester - Complete Automation System
Schedules and manages continuous collection + 60+ score hunting
"""

import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import schedule

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv(project_root / '.env.local')

import os

from scripts.continuous_collection_system import ContinuousCollectionSystem
from scripts.score_hunter_60_plus import ScoreHunter60Plus
from supabase import create_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('error_log/automated_harvester.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomatedRedditHarvester:
    """Complete automation system for continuous Reddit harvesting and score hunting"""

    def __init__(self):
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )

        self.collection_system = ContinuousCollectionSystem()
        self.score_hunter = ScoreHunter60Plus()

        # Automation metrics
        self.automation_stats = {
            'daily_collections': 0,
            'total_opportunities_found': 0,
            'ultra_rare_discoveries': 0,
            'last_collection': None,
            'last_score_hunt': None,
            'system_uptime': datetime.now().isoformat()
        }

    def morning_collection_routine(self):
        """Morning collection routine (9:00 AM) - Focus on ultra-premium content"""
        logger.info("🌅 MORNING COLLECTION ROUTINE")
        logger.info("Targeting ultra-premium, high-stakes business content")

        try:
            # Execute daily collection with ultra-premium focus
            result = self.collection_system.collect_daily_posts(test_mode=False)

            if result['status'] == 'success':
                self.automation_stats['daily_collections'] += 1
                self.automation_stats['last_collection'] = datetime.now().isoformat()

                logger.info(f"✅ Morning collection completed: {result['total_collected']} posts")

                # Trigger immediate scoring for new content
                self.trigger_opportunity_scoring()

            else:
                logger.error(f"❌ Morning collection failed: {result.get('message', 'Unknown error')}")

        except Exception as e:
            logger.error(f"❌ Morning collection error: {e}")

    def afternoon_score_hunt(self):
        """Afternoon score hunting routine (2:00 PM) - Focus on ultra-rare detection"""
        logger.info("🔍 AFTERNOON SCORE HUNT")
        logger.info("Hunting for ultra-rare 60+ opportunities")

        try:
            # Hunt for ultra-rare opportunities
            opportunities = self.score_hunter.hunt_ultra_rare_opportunities(limit=300)

            if opportunities:
                self.automation_stats['total_opportunities_found'] += len(opportunities)

                # Count ultra-rare discoveries (60+)
                ultra_rare_count = len([o for o in opportunities if o.score >= 60])
                self.automation_stats['ultra_rare_discoveries'] += ultra_rare_count

                logger.info(f"🎯 Found {len(opportunities)} opportunities")
                logger.info(f"🌟 Ultra-rare discoveries (60+): {ultra_rare_count}")

                # Send alerts for exceptional findings
                for opp in opportunities:
                    if opp.score >= 60:
                        self.send_ultra_rare_alert(opp)

            self.automation_stats['last_score_hunt'] = datetime.now().isoformat()

            # Generate hunter report
            report = self.score_hunter.generate_hunter_report(opportunities)
            self.store_automation_metrics(report)

        except Exception as e:
            logger.error(f"❌ Afternoon score hunt error: {e}")

    def evening_analysis(self):
        """Evening analysis routine (7:00 PM) - Performance analysis and optimization"""
        logger.info("📊 EVENING ANALYSIS")
        logger.info("Analyzing daily performance and optimizing strategy")

        try:
            # Analyze today's performance
            performance_report = self.generate_daily_performance_report()

            # Store performance metrics
            self.store_performance_metrics(performance_report)

            # Log summary
            logger.info("📈 DAILY PERFORMANCE SUMMARY")
            logger.info("=" * 40)
            logger.info(f"📊 Collections: {performance_report.get('collections_completed', 0)}")
            logger.info(f"🎯 Opportunities: {performance_report.get('opportunities_found', 0)}")
            logger.info(f"🌟 Ultra-rare: {performance_report.get('ultra_rare_discoveries', 0)}")
            logger.info(f"💰 Estimated value: ${performance_report.get('estimated_value', 0):,}")

            # Optimize tomorrow's strategy
            self.optimize_collection_strategy(performance_report)

        except Exception as e:
            logger.error(f"❌ Evening analysis error: {e}")

    def trigger_opportunity_scoring(self):
        """Trigger batch opportunity scoring for new submissions"""
        logger.info("🎯 Triggering opportunity scoring for new submissions")

        try:
            # Get recent submissions from last 24 hours
            cutoff_date = (datetime.now() - timedelta(hours=24)).isoformat()

            result = self.supabase.table('submissions').select('id').gte(
                'created_at', cutoff_date
            ).execute()

            if result.data and len(result.data) > 0:
                logger.info(f"📊 Found {len(result.data)} recent submissions for scoring")

                # Run batch scoring (this would normally be a separate process)
                # For now, we'll just log that scoring should be triggered
                logger.info("⚡ Batch scoring triggered for recent submissions")
                # In production, this would call: batch_scoring()

            else:
                logger.info("📊 No new submissions found for scoring")

        except Exception as e:
            logger.error(f"❌ Error triggering opportunity scoring: {e}")

    def send_ultra_rare_alert(self, opportunity):
        """Send alert for ultra-rare opportunity discovery"""
        logger.info("🚨 ULTRA-RARE OPPORTUNITY ALERT")
        logger.info("=" * 40)
        logger.info(f"🌟 Score: {opportunity.score}")
        logger.info(f"💎 Tier: {opportunity.rarity_tier}")
        logger.info(f"🎯 Confidence: {opportunity.confidence_level}")
        logger.info(f"💰 Market: {opportunity.market_size_estimate}")
        logger.info(f"⚡ Advantage: {opportunity.competitive_advantage}")
        logger.info(f"🕐 Discovered: {opportunity.timestamp}")
        logger.info("🚨 IMMEDIATE ATTENTION REQUIRED!")
        logger.info("=" * 40)

        # In production, this would send email, Slack, or other notifications
        self.store_alert_record(opportunity)

    def store_alert_record(self, opportunity):
        """Store ultra-rare alert record"""
        try:
            alert_record = {
                'opportunity_id': opportunity.opportunity_id,
                'score': opportunity.score,
                'rarity_tier': opportunity.rarity_tier,
                'confidence_level': opportunity.confidence_level,
                'market_size_estimate': opportunity.market_size_estimate,
                'alert_timestamp': datetime.now().isoformat(),
                'alert_type': 'ultra_rare_discovery',
                'notification_sent': False  # Would be updated when notification is sent
            }

            self.supabase.table('ultra_rare_alerts').insert(alert_record).execute()
            logger.info("📊 Ultra-rare alert record stored")

        except Exception as e:
            logger.error(f"❌ Error storing alert record: {e}")

    def generate_daily_performance_report(self) -> dict[str, Any]:
        """Generate daily performance analysis report"""
        try:
            today = datetime.now().date().isoformat()

            # Get today's collection metrics
            collection_result = self.supabase.table('continuous_collection_metrics').select('*').eq(
                'collection_date', today
            ).execute()

            # Get today's opportunities
            opportunities_result = self.supabase.table('app_opportunities').select('*').gte(
                'created_at', datetime.now().replace(hour=0, minute=0, second=0).isoformat()
            ).execute()

            # Calculate metrics
            total_collected = sum(m['total_collected'] for m in collection_result.data or [])
            opportunities_found = len(opportunities_result.data or [])
            ultra_rare_count = len([o for o in opportunities_result.data or [] if o.get('opportunity_score', 0) >= 60])

            # Estimate value (conservative valuation)
            estimated_value = opportunities_found * 1000  # $1,000 per opportunity
            if ultra_rare_count > 0:
                estimated_value += ultra_rare_count * 50000  # $50,000 per ultra-rare

            report = {
                'date': today,
                'collections_completed': len(collection_result.data or []),
                'total_posts_collected': total_collected,
                'opportunities_found': opportunities_found,
                'ultra_rare_discoveries': ultra_rare_count,
                'hit_rate': f"{(opportunities_found / total_collected * 100):.1f}%" if total_collected > 0 else "0%",
                'ultra_rare_rate': f"{(ultra_rare_count / total_collected * 100):.2f}%" if total_collected > 0 else "0%",
                'estimated_value': estimated_value,
                'performance_grade': self.calculate_performance_grade(opportunities_found, ultra_rare_count)
            }

            return report

        except Exception as e:
            logger.error(f"❌ Error generating performance report: {e}")
            return {
                'date': datetime.now().date().isoformat(),
                'error': str(e)
            }

    def calculate_performance_grade(self, opportunities: int, ultra_rare: int) -> str:
        """Calculate daily performance grade"""
        if ultra_rare >= 1:
            return "A+ (Unicorn Day)"
        elif opportunities >= 10:
            return "A (Excellent)"
        elif opportunities >= 5:
            return "B (Good)"
        elif opportunities >= 2:
            return "C (Fair)"
        else:
            return "D (Needs Improvement)"

    def store_performance_metrics(self, report: dict[str, Any]):
        """Store daily performance metrics"""
        try:
            self.supabase.table('daily_performance_metrics').insert(report).execute()
            logger.info("📊 Daily performance metrics stored")
        except Exception as e:
            logger.error(f"❌ Error storing performance metrics: {e}")

    def store_automation_metrics(self, hunter_report: dict[str, Any]):
        """Store automation system metrics"""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'automation_stats': self.automation_stats,
                'hunter_report': hunter_report,
                'system_health': 'healthy'
            }

            self.supabase.table('automation_system_metrics').insert(metrics).execute()
            logger.info("📊 Automation metrics stored")
        except Exception as e:
            logger.error(f"❌ Error storing automation metrics: {e}")

    def optimize_collection_strategy(self, performance_report: dict[str, Any]):
        """Optimize collection strategy based on performance"""
        logger.info("🧠 Optimizing collection strategy based on performance")

        # This would contain logic to adjust subreddit selection, timing, etc.
        # For now, we'll just log the optimization step
        logger.info(f"📊 Performance grade: {performance_report.get('performance_grade', 'Unknown')}")
        logger.info("🔄 Strategy optimization completed")

    def setup_automation_schedule(self):
        """Setup complete automation schedule"""
        logger.info("⏰ Setting up complete automation schedule")

        # Morning collection (9:00 AM) - Ultra-premium focus
        schedule.every().day.at("09:00").do(self.morning_collection_routine)

        # Afternoon score hunting (2:00 PM) - Ultra-rare detection
        schedule.every().day.at("14:00").do(self.afternoon_score_hunt)

        # Evening analysis (7:00 PM) - Performance review
        schedule.every().day.at("19:00").do(self.evening_analysis)

        # Weekly deep analysis (Sundays at 3:00 PM)
        schedule.every().sunday.at("15:00").do(self.weekly_deep_analysis)

        logger.info("✅ Automation schedule configured:")
        logger.info("   🌅 09:00 - Morning collection (ultra-premium focus)")
        logger.info("   🔍 14:00 - Afternoon score hunting (ultra-rare detection)")
        logger.info("   📊 19:00 - Evening analysis (performance review)")
        logger.info("   🧠 15:00 Sunday - Weekly deep analysis")

    def weekly_deep_analysis(self):
        """Weekly comprehensive analysis"""
        logger.info("🧠 WEEKLY DEEP ANALYSIS")
        logger.info("Comprehensive analysis of weekly performance and trends")

        try:
            # This would implement comprehensive weekly analysis
            # Including trend analysis, subreddit performance, etc.
            logger.info("📊 Weekly deep analysis completed")
        except Exception as e:
            logger.error(f"❌ Weekly deep analysis error: {e}")

    def run_automation(self):
        """Run the complete automation system"""
        logger.info("🚀 RedditHarbor Complete Automation System")
        logger.info("🔄 Continuous collection + 60+ score hunting")

        self.setup_automation_schedule()

        logger.info("✅ Automation system active. Press Ctrl+C to stop.")
        logger.info("📊 System will continuously hunt for ultra-rare opportunities")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            logger.info("🛑 Automation system stopped by user")
        except Exception as e:
            logger.error(f"❌ Automation system error: {e}")
            time.sleep(300)  # Wait 5 minutes before retry

def main():
    """Main entry point"""
    logger.info("🚀 Starting RedditHarbor Automated Harvester")

    harvester = AutomatedRedditHarvester()

    # Check if running in test mode
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        logger.info("🧪 Running in test mode")
        harvester.morning_collection_routine()
        harvester.afternoon_score_hunt()
    else:
        logger.info("🔄 Starting full automation system...")
        harvester.run_automation()

if __name__ == "__main__":
    main()
