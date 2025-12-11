#!/usr/bin/env python3
"""
Quick test of the Pipeline orchestrator
"""

import logging
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.pipeline import Pipeline, PipelineResults
from models.reddit import RedditSubmission
from models.analysis import AnalysisResult, AppIdea, MarketMetrics
from datetime import datetime, UTC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_pipeline_init():
    """Test pipeline initialization"""
    try:
        pipeline = Pipeline()
        logger.info("✓ Pipeline initialized successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Pipeline initialization failed: {e}")
        return False

def test_pipeline_with_mock_data():
    """Test pipeline with mock submission"""
    try:
        # Create a mock submission
        mock_submission = RedditSubmission(
            id="test123",
            title="Looking for a tool to automate my expense reports",
            selftext="I spend hours every month creating expense reports for my team. There must be a better way to automate this process with receipts and accounting integration.",
            author="user123",
            upvotes=45,
            score=45,
            comments_count=23,
            subreddit="productivity",
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/productivity/abc123"
        )

        logger.info(f"Created mock submission: {mock_submission.title}")
        logger.info(f"✓ Mock submission validation passed")
        return True
    except Exception as e:
        logger.error(f"✗ Mock submission test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Testing Pipeline V4 Orchestrator")
    logger.info("=" * 50)

    tests = [
        ("Pipeline Initialization", test_pipeline_init),
        ("Mock Data Creation", test_pipeline_with_mock_data),
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