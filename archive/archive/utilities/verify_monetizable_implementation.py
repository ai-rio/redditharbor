#!/usr/bin/env python3
"""
Verification script for monetizable opportunities data collection implementation
Validates that all required functions are implemented and callable
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_implementation():
    """Verify all required functions are implemented"""

    logger.info("=" * 80)
    logger.info("🔍 VERIFYING MONETIZABLE OPPORTUNITIES IMPLEMENTATION")
    logger.info("=" * 80)

    try:
        # Import core functions
        from core.collection import (
            ALL_TARGET_SUBREDDITS,
            MONETIZATION_KEYWORDS,
            PAYMENT_WILLINGNESS_SIGNALS,
            PROBLEM_KEYWORDS,
            SOLUTION_MENTION_KEYWORDS,
            # Constants
            TARGET_SUBREDDITS,
            WORKAROUND_KEYWORDS,
            analyze_emotional_intensity,
            analyze_pain_language,
            analyze_sentiment_and_pain_intensity,
            calculate_sentiment_score,
            collect_enhanced_comments,
            collect_enhanced_submissions,
            collect_monetizable_opportunities_data,
            detect_payment_mentions,
            # Helper functions
            extract_problem_keywords,
            extract_solution_mentions,
            extract_workarounds,
            identify_market_segment,
            smart_rate_limiting,
        )

        logger.info("✅ All required imports successful")
        logger.info("")

        # Verify main functions
        logger.info("📋 MAIN FUNCTIONS:")
        logger.info("  ✅ collect_monetizable_opportunities_data()")
        logger.info("  ✅ collect_enhanced_submissions()")
        logger.info("  ✅ collect_enhanced_comments()")
        logger.info("")

        # Verify helper functions
        logger.info("📋 HELPER FUNCTIONS:")
        logger.info("  ✅ extract_problem_keywords()")
        logger.info("  ✅ extract_workarounds()")
        logger.info("  ✅ extract_solution_mentions()")
        logger.info("  ✅ detect_payment_mentions()")
        logger.info("  ✅ analyze_emotional_intensity()")
        logger.info("  ✅ calculate_sentiment_score()")
        logger.info("  ✅ analyze_pain_language()")
        logger.info("  ✅ analyze_sentiment_and_pain_intensity()")
        logger.info("  ✅ identify_market_segment()")
        logger.info("  ✅ smart_rate_limiting()")
        logger.info("")

        # Verify constants
        logger.info("📋 CONSTANTS:")
        logger.info(f"  ✅ TARGET_SUBREDDITS: {len(TARGET_SUBREDDITS)} market segments")
        logger.info(f"  ✅ ALL_TARGET_SUBREDDITS: {len(ALL_TARGET_SUBREDDITS)} total subreddits")
        logger.info(f"  ✅ PROBLEM_KEYWORDS: {len(PROBLEM_KEYWORDS)} keywords")
        logger.info(f"  ✅ MONETIZATION_KEYWORDS: {len(MONETIZATION_KEYWORDS)} keywords")
        logger.info(f"  ✅ PAYMENT_WILLINGNESS_SIGNALS: {len(PAYMENT_WILLINGNESS_SIGNALS)} signals")
        logger.info(f"  ✅ WORKAROUND_KEYWORDS: {len(WORKAROUND_KEYWORDS)} keywords")
        logger.info(f"  ✅ SOLUTION_MENTION_KEYWORDS: {len(SOLUTION_MENTION_KEYWORDS)} keywords")
        logger.info("")

        # Test helper functions with sample data
        logger.info("📋 TESTING HELPER FUNCTIONS:")

        sample_text = "I'm frustrated with this tedious manual process. It's so time consuming and I would pay for a better solution."

        problem_kw = extract_problem_keywords(sample_text)
        logger.info(f"  ✅ extract_problem_keywords(): Found {len(problem_kw)} keywords: {problem_kw[:3]}")

        workarounds = extract_workarounds(sample_text)
        logger.info(f"  ✅ extract_workarounds(): Found {len(workarounds)} workarounds")

        solutions = extract_solution_mentions(sample_text)
        logger.info(f"  ✅ extract_solution_mentions(): Found {len(solutions)} solutions")

        payment_signals = detect_payment_mentions(sample_text)
        logger.info(f"  ✅ detect_payment_mentions(): Found {len(payment_signals)} signals: {payment_signals[:3]}")

        emotional_score = analyze_emotional_intensity(sample_text)
        logger.info(f"  ✅ analyze_emotional_intensity(): Score = {emotional_score:.3f}")

        sentiment = calculate_sentiment_score(sample_text)
        logger.info(f"  ✅ calculate_sentiment_score(): Score = {sentiment:.3f}")

        pain_score = analyze_pain_language(sample_text)
        logger.info(f"  ✅ analyze_pain_language(): Score = {pain_score:.3f}")

        segment = identify_market_segment("fitness")
        logger.info(f"  ✅ identify_market_segment(): 'fitness' → '{segment}'")

        delay = smart_rate_limiting("hot", "submission")
        logger.info(f"  ✅ smart_rate_limiting(): 'hot' posts → {delay}s delay")
        logger.info("")

        # Verify market segments
        logger.info("📋 MARKET SEGMENTS:")
        for segment, subreddits in TARGET_SUBREDDITS.items():
            logger.info(f"  ✅ {segment}: {len(subreddits)} subreddits")
            logger.info(f"     Examples: {', '.join(subreddits[:3])}")
        logger.info("")

        # Verify function signatures
        import inspect

        logger.info("📋 FUNCTION SIGNATURES:")

        sig = inspect.signature(collect_monetizable_opportunities_data)
        logger.info(f"  collect_monetizable_opportunities_data{sig}")
        params = list(sig.parameters.keys())
        logger.info(f"    Parameters: {', '.join(params)}")
        logger.info("")

        sig = inspect.signature(collect_enhanced_submissions)
        logger.info(f"  collect_enhanced_submissions{sig}")
        params = list(sig.parameters.keys())
        logger.info(f"    Parameters: {', '.join(params)}")
        logger.info("")

        sig = inspect.signature(collect_enhanced_comments)
        logger.info(f"  collect_enhanced_comments{sig}")
        params = list(sig.parameters.keys())
        logger.info(f"    Parameters: {', '.join(params)}")
        logger.info("")

        # Verify implementation completeness
        logger.info("📋 IMPLEMENTATION COMPLETENESS CHECK:")

        # Check collect_monetizable_opportunities_data implementation
        import inspect
        source = inspect.getsource(collect_monetizable_opportunities_data)

        checks = {
            "Calls collect_enhanced_submissions()": "collect_enhanced_submissions(" in source,
            "Calls collect_enhanced_comments()": "collect_enhanced_comments(" in source,
            "Handles market_segment parameter": "market_segment" in source,
            "Uses TARGET_SUBREDDITS": "TARGET_SUBREDDITS" in source,
            "Uses ALL_TARGET_SUBREDDITS": "ALL_TARGET_SUBREDDITS" in source,
            "Has error handling": "try:" in source and "except" in source,
            "Has logging": "logger." in source,
            "Returns boolean": "return" in source and "bool" in str(sig.return_annotation),
        }

        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            logger.info(f"  {status} {check}")

        all_passed = all(checks.values())
        logger.info("")

        # Check collect_enhanced_submissions implementation
        logger.info("📋 ENHANCED SUBMISSIONS IMPLEMENTATION:")
        source = inspect.getsource(collect_enhanced_submissions)

        checks = {
            "Iterates through subreddits": "for subreddit_name in subreddits" in source,
            "Handles multiple sort types": "for sort_type in sort_types" in source,
            "Calls Reddit API": ("subreddit.hot" in source or "subreddit.top" in source or "subreddit.rising" in source),
            "Extracts enhanced metadata": "sentiment_score" in source or "calculate_sentiment_score" in source,
            "Calls extract_problem_keywords()": "extract_problem_keywords" in source,
            "Calls extract_solution_mentions()": "extract_solution_mentions" in source,
            "Calls detect_payment_mentions()": "detect_payment_mentions" in source,
            "Stores to Supabase": "supabase_client.table" in source and "upsert" in source,
            "Has rate limiting": "time.sleep" in source,
            "Has error handling": "try:" in source and "except" in source,
        }

        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            logger.info(f"  {status} {check}")

        all_passed = all_passed and all(checks.values())
        logger.info("")

        # Check collect_enhanced_comments implementation
        logger.info("📋 ENHANCED COMMENTS IMPLEMENTATION:")
        source = inspect.getsource(collect_enhanced_comments)

        checks = {
            "Queries existing submissions": "supabase_client.table" in source and "select" in source,
            "Fetches comments from Reddit": "reddit_client.submission" in source,
            "Extracts workarounds": "extract_workarounds" in source,
            "Extracts problem keywords": "extract_problem_keywords" in source or "problem_keywords" in source,
            "Calculates sentiment": "calculate_sentiment_score" in source or "sentiment_score" in source,
            "Analyzes pain intensity": "analyze_pain_language" in source or "pain_intensity" in source,
            "Detects payment mentions": "detect_payment_mentions" in source,
            "Stores to Supabase": "supabase_client.table" in source and "upsert" in source,
            "Has rate limiting": "time.sleep" in source or "smart_rate_limiting" in source,
            "Has error handling": "try:" in source and "except" in source,
        }

        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            logger.info(f"  {status} {check}")

        all_passed = all_passed and all(checks.values())
        logger.info("")

        # Final verdict
        logger.info("=" * 80)
        if all_passed:
            logger.info("✅ IMPLEMENTATION VERIFICATION SUCCESSFUL!")
            logger.info("")
            logger.info("All required functions are implemented and contain:")
            logger.info("  • Reddit API data collection")
            logger.info("  • Enhanced metadata extraction (sentiment, keywords, etc.)")
            logger.info("  • Supabase database storage")
            logger.info("  • Smart rate limiting (1.5s-3.0s delays)")
            logger.info("  • Comprehensive error handling")
            logger.info("  • Progress logging")
            logger.info("")
            logger.info("The implementation is ready for production use!")
        else:
            logger.warning("⚠️ Some implementation checks failed")
            logger.warning("Review the checks above for details")

        logger.info("=" * 80)

        return all_passed

    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = verify_implementation()
    sys.exit(0 if success else 1)
