#!/usr/bin/env python3
"""
Automated RedditHarbor Opportunity Collector
Continuously collects fresh Reddit data and analyzes for monetizable app opportunities
"""

import sys
import os
from pathlib import Path
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import time

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('error_log/automated_collector.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def collect_fresh_reddit_data():
    """
    Collect fresh Reddit data from target subreddits
    """
    logger.info("🚀 Starting Fresh Reddit Data Collection")

    # Target subreddits for opportunity analysis
    finance_subreddits = [
        "personalfinance", "investing", "stocks", "Bogleheads", "financialindependence",
        "CryptoCurrency", "tax", "Accounting", "RealEstateInvesting", "FinancialCareers"
    ]

    health_fitness_subreddits = [
        "fitness", "loseit", "bodyweightfitness", "nutrition", "keto", "running",
        "cycling", "yoga", "meditation", "mentalhealth", "fitness30plus", "homegym"
    ]

    tech_saaS_subreddits = [
        "SaaS", "startups", "Entrepreneur", "SideProject", "productivity",
        "selfhosted", "apphookup", "iosapps", "androidapps", "software"
    ]

    # Additional opportunity-focused subreddits
    opportunity_subreddits = [
        "findareddit", "ProductHunt", "apps", "Shoestring", "digitalnomad",
        "workreform", "antiwork", "IWantToLearn"
    ]

    all_target_subreddits = (
        finance_subreddits + health_fitness_subreddits +
        tech_saaS_subreddits + opportunity_subreddits
    )

    logger.info(f"🎯 Targeting {len(all_target_subreddits)} subreddits for fresh data")

    try:
        # Try to use RedditHarbor for collection
        from redditharbor.login import reddit, supabase
        from redditharbor.dock.pipeline import collect

        logger.info("✅ RedditHarbor imports successful")

        # Check connections
        if reddit and supabase:
            logger.info("🔗 Reddit and Supabase connections available")

            # Collect data in batches to avoid rate limiting
            batch_size = 5
            for i in range(0, len(all_target_subreddits), batch_size):
                batch = all_target_subreddits[i:i + batch_size]
                logger.info(f"📊 Collecting from batch {i//batch_size + 1}: {batch}")

                try:
                    collect(
                        subreddits=batch,
                        sort_types=["hot", "top"],  # Focus on high-engagement content
                        limit=50,  # Conservative limit for reliability
                        mask_pii=False,  # Disabled for now to avoid spaCy issues
                        ignore_existing=False  # Get fresh data
                    )

                    logger.info(f"✅ Completed collection for batch {i//batch_size + 1}")

                    # Rate limiting delay between batches
                    time.sleep(30)  # 30 seconds between batches

                except Exception as e:
                    logger.error(f"❌ Failed to collect from batch {i//batch_size + 1}: {e}")
                    continue

            logger.info("🎉 Fresh Reddit data collection completed!")
            return True

        else:
            logger.error("❌ Reddit or Supabase connection not available")
            return False

    except ImportError as e:
        logger.error(f"❌ Could not import RedditHarbor: {e}")
        return False

    except Exception as e:
        logger.error(f"❌ Data collection failed: {e}")
        return False

def analyze_fresh_data():
    """
    Analyze freshly collected data for opportunities
    """
    logger.info("🔍 Analyzing Fresh Data for Opportunities")

    try:
        # Import the database analyzer
        from analyze_real_database_data import fetch_submissions, analyze_subreddit_opportunities, generate_opportunity_report

        # Get latest data
        submissions = fetch_submissions(limit=100)  # Latest 100 submissions
        comments = []  # Skip comments for now

        if not submissions:
            logger.warning("⚠️ No fresh submissions found for analysis")
            return False

        # Analyze opportunities
        logger.info("📊 Analyzing opportunity signals...")
        subreddit_analysis = analyze_subreddit_opportunities(submissions, comments)

        # Generate report
        report = generate_opportunity_report(subreddit_analysis)

        # Add collection timestamp
        report["collection_metadata"] = {
            "collection_time": datetime.now().isoformat(),
            "fresh_data_analyzed": len(submissions),
            "analysis_type": "automated_opportunity_detection"
        }

        # Save with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_path = Path("generated") / f"automated_opportunities_{timestamp}.json"
        results_path.parent.mkdir(exist_ok=True)

        with open(results_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"📄 Fresh analysis saved to: {results_path}")

        # Print summary of high-value opportunities
        high_priority = [opp for opp in report.get("top_opportunities", [])
                        if "HIGH" in opp.get("score_analysis", {}).get("priority", "")]

        if high_priority:
            print(f"\n🚀 NEW HIGH-PRIORITY OPPORTUNITIES FOUND: {len(high_priority)}")
            for i, opp in enumerate(high_priority[:5], 1):
                score = opp.get("score_analysis", {}).get("final_score", 0)
                title = opp.get("title", opp.get("content", ""))[:50]
                print(f"{i}. r/{opp.get('subreddit', 'unknown')} - Score: {score:.1f}")
                print(f"   {title}...")

        return True

    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        return False

def create_daily_opportunity_digest():
    """
    Create a daily digest of top opportunities
    """
    logger.info("📰 Creating Daily Opportunity Digest")

    try:
        # Analyze fresh data
        success = analyze_fresh_data()

        if success:
            # Create a summary file
            digest = {
                "digest_date": datetime.now().strftime("%Y-%m-%d"),
                "digest_time": datetime.now().isoformat(),
                "status": "opportunities_identified",
                "message": "Daily Reddit opportunity analysis completed successfully"
            }

            digest_path = Path("generated") / f"daily_digest_{datetime.now().strftime('%Y%m%d')}.json"
            with open(digest_path, 'w') as f:
                json.dump(digest, f, indent=2)

            logger.info(f"📰 Daily digest created: {digest_path}")
            return True

        return False

    except Exception as e:
        logger.error(f"❌ Daily digest creation failed: {e}")
        return False

def run_scheduled_collection():
    """
    Main function for scheduled Reddit data collection
    """
    logger.info("⏰ Starting Scheduled Reddit Opportunity Collection")

    try:
        # Step 1: Collect fresh data
        collection_success = collect_fresh_reddit_data()

        if collection_success:
            logger.info("✅ Data collection successful")

            # Step 2: Analyze the collected data
            analysis_success = analyze_fresh_data()

            if analysis_success:
                logger.info("✅ Analysis completed successfully")
                print("\n🎉 AUTOMATED COLLECTION CYCLE COMPLETED SUCCESSFULLY!")
                print("📊 Check generated/ directory for latest opportunity insights")
            else:
                logger.error("❌ Analysis failed")
        else:
            logger.error("❌ Data collection failed")

    except Exception as e:
        logger.error(f"❌ Scheduled collection failed: {e}")

def main():
    """
    Main execution function
    """
    print("\n" + "="*60)
    print("🤖 REDDITHARBOR AUTOMATED OPPORTUNITY COLLECTOR")
    print("="*60)
    print("This system will automatically:")
    print("• Collect fresh Reddit data from target subreddits")
    print("• Analyze for monetizable app opportunities")
    print("• Generate opportunity insights and reports")
    print("• Create daily opportunity digests")
    print("="*60)

    try:
        # Parse command line arguments
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()

            if command == "once":
                logger.info("🔄 Running single collection cycle")
                run_scheduled_collection()

            elif command == "schedule":
                logger.info("⏰ Simple scheduled collection mode")
                print("📅 Running collection every 6 hours (press Ctrl+C to stop)")

                # Simple scheduler
                while True:
                    run_scheduled_collection()
                    print("⏰ Next collection in 6 hours...")
                    time.sleep(6 * 60 * 60)  # 6 hours

            elif command == "daily":
                logger.info("📰 Creating daily opportunity digest")
                create_daily_opportunity_digest()

            else:
                print("❌ Unknown command. Use: once, schedule, or daily")
        else:
            # Default: run once
            logger.info("🔄 Running single collection cycle (default)")
            run_scheduled_collection()

    except KeyboardInterrupt:
        logger.info("🛑 Automated collection stopped by user")
    except Exception as e:
        logger.error(f"❌ Automated collector failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()