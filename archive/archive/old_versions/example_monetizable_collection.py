#!/usr/bin/env python3
"""
Example script demonstrating monetizable app research collection

This script shows how to use the new collection capabilities for identifying
monetizable app opportunities from Reddit discussions.
"""

import logging
import sys

# Add project root to path
sys.path.insert(0, '/home/carlos/projects/redditharbor')

from core.collection import (
    TARGET_SUBREDDITS,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_full_collection():
    """
    Example 1: Collect data from all market segments
    """
    logger.info("=" * 80)
    logger.info("📚 Example 1: Full Market Collection")
    logger.info("=" * 80)

    # Mock clients (replace with real clients in production)
    reddit_client = None
    supabase_client = None
    db_config = {
        "submission": "submissions",
        "comment": "comments"
    }

    logger.info("\nThis would collect from all 6 market segments:")
    for segment, subreddits in TARGET_SUBREDDITS.items():
        logger.info(f"  🎯 {segment}: {len(subreddits)} subreddits")

    # Example usage:
    # success = collect_monetizable_opportunities_data(
    #     reddit_client=reddit_client,
    #     supabase_client=supabase_client,
    #     db_config=db_config,
    #     market_segment="all",  # or specific segment
    #     limit_per_sort=100,
    #     time_filter="month",
    #     mask_pii=True
    # )

    logger.info("\n✅ Example 1: Complete")


def example_segment_specific_collection():
    """
    Example 2: Collect from a specific market segment
    """
    logger.info("=" * 80)
    logger.info("📚 Example 2: Segment-Specific Collection")
    logger.info("=" * 80)

    logger.info("\nExample: Health & Fitness segment")
    logger.info(f"Target subreddits: {TARGET_SUBREDDITS['health_fitness']}")

    logger.info("\nUse case: Focused research on health/fitness app opportunities")
    logger.info("Benefits:")
    logger.info("  - Deeper analysis within one vertical")
    logger.info("  - Better understanding of specific user pain points")
    logger.info("  - More targeted monetization opportunities")

    # Example usage:
    # reddit_client = create_reddit_client()
    # supabase_client = create_supabase_client()
    #
    # success = collect_monetizable_opportunities_data(
    #     reddit_client=reddit_client,
    #     supabase_client=supabase_client,
    #     db_config=db_config,
    #     market_segment="health_fitness",
    #     limit_per_sort=150,
    #     time_filter="week",
    #     mask_pii=True,
    #     sentiment_analysis=True,
    #     extract_problem_keywords=True,
    #     track_workarounds=True
    # )

    logger.info("\n✅ Example 2: Complete")


def example_opportunity_scoring():
    """
    Example 3: Collect data specifically for opportunity scoring
    """
    logger.info("=" * 80)
    logger.info("📚 Example 3: Opportunity Scoring Collection")
    logger.info("=" * 80)

    # Custom keywords for specific opportunity research
    custom_problem_keywords = [
        "expense tracking", "budget", "receipt", "receipts", "expense report",
        "income tracking", "money management", "financial planning"
    ]

    custom_monetization_keywords = [
        "subscription", "premium", "pay", "price", "cost", "monthly", "yearly",
        "freemium", "one-time", "paid features"
    ]

    logger.info("\nCustom problem keywords for expense tracking research:")
    for keyword in custom_problem_keywords:
        logger.info(f"  - {keyword}")

    logger.info("\nCustom monetization keywords:")
    for keyword in custom_monetization_keywords[:10]:
        logger.info(f"  - {keyword}")

    # Example usage:
    # reddit_client = create_reddit_client()
    # supabase_client = create_supabase_client()
    # target_subreddits = ["personalfinance", "leanfire", "financialindependence"]
    #
    # success = collect_for_opportunity_scoring(
    #     reddit_client=reddit_client,
    #     supabase_client=supabase_client,
    #     db_config=db_config,
    #     subreddits=target_subreddits,
    #     problem_keywords=custom_problem_keywords,
    #     monetization_keywords=custom_monetization_keywords,
    #     limit=200
    # )

    logger.info("\nThis data would be used for 6-dimension scoring:")
    logger.info("  1. Market Demand Score (20%)")
    logger.info("  2. Pain Intensity Score (25%)")
    logger.info("  3. Monetization Potential Score (20%)")
    logger.info("  4. Market Gap Analysis Score (10%)")
    logger.info("  5. Technical Feasibility Score (5%)")
    logger.info("  6. Simplicity Score (20%) - MANDATORY: 1-3 core functions only")

    logger.info("\n✅ Example 3: Complete")


def example_enhanced_data_fields():
    """
    Example 4: Show enhanced data fields collected
    """
    logger.info("=" * 80)
    logger.info("📚 Example 4: Enhanced Data Fields")
    logger.info("=" * 80)

    logger.info("\n📝 Enhanced Submission Fields:")
    logger.info("  - market_segment: Category (health_fitness, finance_investing, etc.)")
    logger.info("  - sort_type: hot, rising, or top")
    logger.info("  - time_filter: day, week, month")
    logger.info("  - post_engagement_rate: score / comments ratio")
    logger.info("  - emotional_language_score: 0.0 to 1.0 intensity")
    logger.info("  - sentiment_score: -1.0 to 1.0 sentiment")
    logger.info("  - problem_indicators: JSON array of problem keywords")
    logger.info("  - solution_mentions: JSON array of current solutions")
    logger.info("  - monetization_signals: JSON array of payment mentions")

    logger.info("\n💬 Enhanced Comment Fields:")
    logger.info("  - sentiment_score: -1.0 to 1.0")
    logger.info("  - pain_intensity_indicators: 0.0 to 1.0")
    logger.info("  - engagement_score: Comment upvotes")
    logger.info("  - workaround_mentions: JSON array of DIY/workaround keywords")
    logger.info("  - payment_willingness_signals: JSON array of payment indicators")
    logger.info("  - problem_keywords: JSON array of problem indicators")

    logger.info("\n✅ Example 4: Complete")


def example_rate_limiting():
    """
    Example 5: Smart rate limiting
    """
    logger.info("=" * 80)
    logger.info("📚 Example 5: Smart Rate Limiting")
    logger.info("=" * 80)

    from core.collection import smart_rate_limiting

    logger.info("\nRate limiting by sort type:")
    logger.info(f"  - Hot posts:     {smart_rate_limiting('hot', 'submission')}s delay")
    logger.info(f"  - Rising posts:  {smart_rate_limiting('rising', 'submission')}s delay")
    logger.info(f"  - Top posts:     {smart_rate_limiting('top', 'submission')}s delay")
    logger.info(f"  - Comments:      {smart_rate_limiting('n/a', 'comment')}s delay")

    logger.info("\nWhy smart rate limiting?")
    logger.info("  - Hot/Rising: Faster (1.5s) - current trending content")
    logger.info("  - Top: Slower (3.0s) - historical data with filters")
    logger.info("  - Comments: Moderate (2.0s) - balance collection speed with API respect")

    logger.info("\n✅ Example 5: Complete")


def example_simplicity_constraint():
    """
    Example 6: Simplicity constraint enforcement
    """
    logger.info("=" * 80)
    logger.info("📚 Example 6: Simplicity Constraint (CRITICAL)")
    logger.info("=" * 80)

    logger.info("\n🎯 MANDATORY CONSTRAINT: 1-3 Core Functions Only")
    logger.info("\nWhy this matters:")
    logger.info("  - 1-3 function apps: 4-10 weeks to MVP")
    logger.info("  - 4+ function apps: 16-24 weeks to MVP")
    logger.info("  - Simpler = Faster = Cheaper = More Attempts")
    logger.info("  - Higher success rate with focused solutions")

    logger.info("\n✅ Examples of ACCEPTED apps (1-3 functions):")
    logger.info("  ✓ Habit tracker (1 function): Track habit streaks")
    logger.info("  ✓ Calorie counter (1 function): Track calories only")
    logger.info("  ✓ Focus timer (2 functions): Pomodoro + break reminders")
    logger.info("  ✓ Invoice generator (2 functions): Create + send invoices")
    logger.info("  ✓ Expense tracker (3 functions): Entry + categorization + summaries")

    logger.info("\n❌ Examples of REJECTED apps (4+ functions):")
    logger.info("  ✗ All-in-one health app: Exercise + Nutrition + Sleep + Photos")
    logger.info("  ✗ Business manager: Time + Invoicing + Projects + Expenses + Taxes")

    logger.info("\n💡 Scoring system enforces this:")
    logger.info("  - 1 core function = 100 simplicity points")
    logger.info("  - 2 core functions = 85 simplicity points")
    logger.info("  - 3 core functions = 70 simplicity points")
    logger.info("  - 4+ core functions = 0 points (AUTO DISQUALIFIED)")

    logger.info("\n✅ Example 6: Complete")


def main():
    """Run all examples"""
    logger.info("\n" + "=" * 80)
    logger.info("🎓 MONETIZABLE APP RESEARCH COLLECTION - EXAMPLES")
    logger.info("=" * 80)
    logger.info("\nThis script demonstrates how to use the new monetizable app")
    logger.info("research collection capabilities in RedditHarbor.\n")

    try:
        example_full_collection()
        example_segment_specific_collection()
        example_opportunity_scoring()
        example_enhanced_data_fields()
        example_rate_limiting()
        example_simplicity_constraint()

        logger.info("\n" + "=" * 80)
        logger.info("🎉 ALL EXAMPLES COMPLETED")
        logger.info("=" * 80)

        logger.info("\n📖 Next Steps:")
        logger.info("  1. Set up Reddit API credentials in config/settings.py")
        logger.info("  2. Set up Supabase connection")
        logger.info("  3. Run collection for your target market segment")
        logger.info("  4. Analyze collected data for opportunities")
        logger.info("  5. Score opportunities using 6-dimension framework")
        logger.info("  6. Validate top opportunities across platforms")
        logger.info("  7. Build simple (1-3 function) MVPs only!")

        logger.info("\n🔗 Related Files:")
        logger.info("  - /home/carlos/projects/redditharbor/core/collection.py - Collection module")
        logger.info("  - /home/carlos/projects/redditharbor/docs/monetizable_app_research_methodology.md - Full methodology")
        logger.info("  - /home/carlos/projects/redditharbor/docs/monetizable_app_research_erd.md - Database schema")
        logger.info("  - /home/carlos/projects/redditharbor/tests/test_monetizable_collection.py - Tests")

        return True

    except Exception as e:
        logger.error(f"❌ Error running examples: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
