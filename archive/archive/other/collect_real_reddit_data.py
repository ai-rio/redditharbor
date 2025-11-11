#!/usr/bin/env python3
"""
RedditHarbor Simple Data Collection Script
Collects REAL Reddit data from finance and health subreddits for opportunity analysis
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('error_log/simple_data_collection.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def collect_reddit_data_simple():
    """
    Simplified Reddit data collection that focuses on getting REAL data
    """
    logger.info("🚀 Starting Simple Reddit Data Collection for Opportunity Analysis")

    # Target subreddits for opportunity analysis
    target_subreddits = {
        "Finance & Investing": [
            "personalfinance", "investing", "stocks", "Bogleheads", "financialindependence",
            "CryptoCurrency", "tax", "Accounting", "RealEstateInvesting", "FinancialCareers"
        ],
        "Health & Fitness": [
            "fitness", "loseit", "bodyweightfitness", "nutrition", "keto", "running",
            "cycling", "yoga", "meditation", "mentalhealth", "fitness30plus", "homegym"
        ]
    }

    # Keywords that indicate monetizable opportunities
    opportunity_keywords = {
        "pain_points": [
            "frustrated", "annoying", "terrible", "hate", "worst", "useless", "broken",
            "doesn't work", "problem", "issue", "bug", "crash", "slow", "expensive",
            "difficult", "complicated", "confusing", "waste of time", "disappointed"
        ],
        "solution_seeking": [
            "recommendation", "suggestion", "best", "looking for", "need help",
            "any alternatives", "what do you use", "how to", "tutorial", "guide",
            "alternative", "replacement", "better than", "is there a way"
        ],
        "monetization_signals": [
            "willing to pay", "subscription", "premium", "pro version", "paid", "cost",
            "price", "affordable", "worth it", "investment", "budget", "cheap",
            "expensive", "free trial", "upgrade", "paid version"
        ]
    }

    try:
        # Try to use RedditHarbor if available
        logger.info("🔍 Attempting RedditHarbor imports...")
        from redditharbor.dock.pipeline import collect
        from redditharbor.login import reddit, supabase
        logger.info("✅ RedditHarbor imports successful")

        # Check Reddit connection
        if reddit:
            logger.info("🔍 Testing Reddit API connection...")
            try:
                # Test with a simple subreddit fetch
                test_subreddit = reddit.subreddit("personalfinance")
                test_post = next(test_subreddit.hot(limit=1))
                logger.info(f"✅ Reddit API connection successful! Found post: {test_post.title}")
                reddit_connected = True
            except Exception as e:
                logger.error(f"❌ Reddit API connection failed: {e}")
                reddit_connected = False
        else:
            logger.error("❌ Reddit client not initialized")
            reddit_connected = False

        # Check Supabase connection
        if supabase and reddit_connected:
            logger.info("🔍 Testing Supabase connection...")
            try:
                # Test with a simple query
                response = supabase.table('submission').select('count').execute()
                logger.info("✅ Supabase connection successful!")
                supabase_connected = True
            except Exception as e:
                logger.error(f"❌ Supabase connection failed: {e}")
                supabase_connected = False
        else:
            supabase_connected = False

        if reddit_connected and supabase_connected:
            logger.info("🎯 Starting REAL data collection from target subreddits...")

            # Collect data from each category
            results = {}
            for category, subreddits in target_subreddits.items():
                logger.info(f"📊 Collecting from {category}: {subreddits}")

                try:
                    # Use RedditHarbor collect function with our target subreddits
                    collect(
                        subreddits=subreddits,
                        sort_types=["hot", "top", "new"],
                        limit=200,  # Conservative limit for testing
                        mask_pii=False,  # Disabled for now to avoid spaCy issues
                        ignore_existing=False  # Get fresh data
                    )

                    results[category] = {
                        "status": "success",
                        "subreddits": subreddits,
                        "timestamp": datetime.now().isoformat()
                    }

                    logger.info(f"✅ Completed collection for {category}")

                except Exception as e:
                    logger.error(f"❌ Failed to collect from {category}: {e}")
                    results[category] = {
                        "status": "failed",
                        "error": str(e),
                        "subreddits": subreddits,
                        "timestamp": datetime.now().isoformat()
                    }

            # Save collection results
            results_path = Path("generated") / "simple_collection_results.json"
            results_path.parent.mkdir(exist_ok=True)

            with open(results_path, 'w') as f:
                json.dump({
                    "collection_summary": results,
                    "opportunity_keywords": opportunity_keywords,
                    "collection_metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "method": "RedditHarbor Simple Collection",
                        "pi_anonymization": False
                    }
                }, f, indent=2)

            logger.info(f"📄 Collection results saved to: {results_path}")
            return True

        else:
            logger.error("❌ Cannot proceed with data collection due to connection issues")
            return False

    except ImportError as e:
        logger.error(f"❌ Could not import RedditHarbor: {e}")
        logger.info("🔄 Falling back to manual data analysis approach...")
        # Fallback: Process existing HTML logs for insights
        return process_existing_html_logs()

    except Exception as e:
        import traceback
        logger.error(f"❌ Data collection failed: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

def process_existing_html_logs():
    """
    Process existing HTML logs from error_log directory for opportunity insights
    """
    logger.info("🔄 Processing existing HTML logs for opportunity insights...")

    error_log_dir = Path("error_log")
    html_files = list(error_log_dir.glob("*.html"))

    if not html_files:
        logger.warning("❌ No HTML logs found to process")
        return False

    logger.info(f"📁 Found {len(html_files)} HTML logs to process")

    opportunity_insights = {
        "processed_files": len(html_files),
        "insights": [],
        "pain_points": [],
        "solution_requests": [],
        "monetization_mentions": []
    }

    # Simple keyword-based analysis
    pain_keywords = ["problem", "issue", "broken", "frustrated", "difficult", "confusing"]
    solution_keywords = ["looking for", "recommendation", "alternative", "help", "how to"]
    monetization_keywords = ["pay", "cost", "price", "premium", "subscription"]

    for html_file in html_files[:10]:  # Process first 10 files for testing
        try:
            with open(html_file, encoding='utf-8') as f:
                content = f.read().lower()

                # Extract subreddit info and content from HTML
                if "subreddit:" in content:
                    lines = content.split('\n')
                    for line in lines:
                        if "subreddit:" in line:
                            subreddit = line.split("subreddit:")[1].strip()
                            break

                    # Count keyword occurrences
                    pain_count = sum(content.count(keyword) for keyword in pain_keywords)
                    solution_count = sum(content.count(keyword) for keyword in solution_keywords)
                    monetization_count = sum(content.count(keyword) for keyword in monetization_keywords)

                    if pain_count > 0 or solution_count > 0 or monetization_count > 0:
                        insight = {
                            "file": html_file.name,
                            "subreddit": subreddit,
                            "pain_indicators": pain_count,
                            "solution_requests": solution_count,
                            "monetization_signals": monetization_count,
                            "total_opportunity_signals": pain_count + solution_count + monetization_count
                        }
                        opportunity_insights["insights"].append(insight)

                        if pain_count > 0:
                            opportunity_insights["pain_points"].append(insight)
                        if solution_count > 0:
                            opportunity_insights["solution_requests"].append(insight)
                        if monetization_count > 0:
                            opportunity_insights["monetization_mentions"].append(insight)

        except Exception as e:
            logger.error(f"❌ Error processing {html_file}: {e}")

    # Save insights
    insights_path = Path("generated") / "existing_data_insights.json"
    insights_path.parent.mkdir(exist_ok=True)

    with open(insights_path, 'w') as f:
        json.dump({
            "analysis_summary": opportunity_insights,
            "analysis_metadata": {
                "timestamp": datetime.now().isoformat(),
                "method": "HTML Log Processing",
                "files_analyzed": len(html_files)
            }
        }, f, indent=2)

    logger.info(f"📄 Existing data insights saved to: {insights_path}")

    # Print summary
    print("\n" + "="*60)
    print("🎯 EXISTING DATA OPPORTUNITY ANALYSIS SUMMARY")
    print("="*60)
    print(f"Files Processed: {opportunity_insights['processed_files']}")
    print(f"Total Insights Found: {len(opportunity_insights['insights'])}")
    print(f"Pain Points Identified: {len(opportunity_insights['pain_points'])}")
    print(f"Solution Requests: {len(opportunity_insights['solution_requests'])}")
    print(f"Monetization Mentions: {len(opportunity_insights['monetization_mentions'])}")

    if opportunity_insights["insights"]:
        print("\n🔥 TOP OPPORTUNITIES (by signal count):")
        sorted_insights = sorted(opportunity_insights["insights"],
                               key=lambda x: x['total_opportunity_signals'], reverse=True)
        for insight in sorted_insights[:5]:
            print(f"• r/{insight['subreddit']}: {insight['total_opportunity_signals']} signals "
                  f"(Pain: {insight['pain_indicators']}, Solutions: {insight['solution_requests']}, "
                  f"Monetization: {insight['monetization_signals']})")

    print("="*60)

    return True

def main():
    """
    Main execution function
    """
    try:
        logger.info("🎯 Starting Reddit Data Collection for Opportunity Analysis")

        success = collect_reddit_data_simple()

        if success:
            logger.info("✅ Data collection completed successfully!")
            print("\n🎉 DATA COLLECTION COMPLETED!")
            print("📊 Check generated/ directory for results and insights")
        else:
            logger.error("❌ Data collection failed")
            print("\n❌ Data collection failed. Check logs for details.")

    except KeyboardInterrupt:
        logger.info("🛑 Data collection interrupted by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
