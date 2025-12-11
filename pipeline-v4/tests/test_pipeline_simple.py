#!/usr/bin/env python3
"""
Simple test of the Pipeline data structures without external dependencies
"""

import logging
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.reddit import RedditSubmission
from models.analysis import AnalysisResult, AppIdea, MarketMetrics
from core.pipeline import PipelineResults
from datetime import datetime, UTC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_pipeline_results():
    """Test PipelineResults dataclass"""
    try:
        results = PipelineResults(
            total_time=120.5,
            submissions_fetched=10,
            analyses_completed=8,
            analyses_saved=7,
            analyses_skipped=2,
            errors=1
        )

        logger.info(f"✓ PipelineResults created:")
        logger.info(f"  Time: {results.total_time}s")
        logger.info(f"  Fetched: {results.submissions_fetched}")
        logger.info(f"  Analyzed: {results.analyses_completed}")
        logger.info(f"  Saved: {results.analyses_saved}")
        logger.info(f"  Skipped: {results.analyses_skipped}")
        logger.info(f"  Errors: {results.errors}")
        return True
    except Exception as e:
        logger.error(f"✗ PipelineResults test failed: {e}")
        return False

def test_mock_submission():
    """Test creating a mock Reddit submission"""
    try:
        submission = RedditSubmission(
            id="test123",
            title="Looking for a tool to automate my expense reports",
            text="I spend hours every month creating expense reports for my team. There must be a better way to automate this process with receipts and accounting integration.",
            author="user123",
            upvotes=45,
            downvotes=0,
            score=45,
            comments_count=23,
            subreddit="productivity",
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/productivity/abc123"
        )

        logger.info(f"✓ Mock submission created:")
        logger.info(f"  ID: {submission.id}")
        logger.info(f"  Title: {submission.title}")
        logger.info(f"  Score: {submission.score}")
        logger.info(f"  Comments: {submission.comments_count}")
        return True
    except Exception as e:
        logger.error(f"✗ Mock submission test failed: {e}")
        return False

def test_mock_analysis():
    """Test creating a mock analysis result"""
    try:
        app_idea = AppIdea(
            title="Expense Report Automator",
            app_concept="An automated expense reporting tool that processes receipts and integrates with accounting systems.",
            problem_statement="Manual expense report creation is time-consuming and error-prone.",
            core_functions=["Receipt scanning", "Automated categorization", "Accounting integration"],
            target_audience="Small business owners and finance teams"
        )

        market_metrics = MarketMetrics(
            market_demand=85.0,
            pain_intensity=90.0,
            monetization_potential=80.0,
            competition_level=60.0,
            technical_feasibility=75.0
        )

        analysis = AnalysisResult(
            submission_id="test123",
            subreddit="productivity",
            title="Looking for expense automation tool",
            app_idea=app_idea,
            market_metrics=market_metrics,
            final_score=82.5,
            wtp_score=80.0,
            confidence_score=85.0,
            trust_level="HIGH",
            content_quality_score=90.0,
            is_spam=False,
            spam_indicators=[],
            analyzed_at=datetime.now(UTC)
        )

        logger.info(f"✓ Mock analysis created:")
        logger.info(f"  Final Score: {analysis.final_score}")
        logger.info(f"  WTP Score: {analysis.wtp_score}")
        logger.info(f"  Trust Level: {analysis.trust_level}")
        logger.info(f"  App Idea: {analysis.app_idea.title}")
        return True
    except Exception as e:
        logger.error(f"✗ Mock analysis test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Testing Pipeline V4 Data Structures")
    logger.info("=" * 50)

    tests = [
        ("PipelineResults", test_pipeline_results),
        ("RedditSubmission", test_mock_submission),
        ("AnalysisResult", test_mock_analysis),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        logger.info(f"\nRunning: {test_name}")
        if test_func():
            passed += 1
        logger.info("-" * 30)

    logger.info(f"\nTest Results: {passed}/{total} passed")

    if passed == total:
        logger.info("✓ All tests passed!")
        return 0
    else:
        logger.error("✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())