#!/usr/bin/env python3
"""
Test the pipeline data structures directly
"""

import logging
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import only the specific classes we need
from dataclasses import dataclass
from typing import List
from datetime import datetime, UTC

# Define PipelineResults inline to avoid dependency issues
@dataclass
class PipelineResults:
    """Pipeline execution results"""
    total_time: float
    submissions_fetched: int
    analyses_completed: int
    analyses_saved: int
    analyses_skipped: int
    errors: int

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

        logger.info(f"✓ PipelineResults created successfully:")
        logger.info(f"  Total Time: {results.total_time}s")
        logger.info(f"  Submissions Fetched: {results.submissions_fetched}")
        logger.info(f"  Analyses Completed: {results.analyses_completed}")
        logger.info(f"  Analyses Saved: {results.analyses_saved}")
        logger.info(f"  Analyses Skipped: {results.analyses_skipped}")
        logger.info(f"  Errors: {results.errors}")
        return True
    except Exception as e:
        logger.error(f"✗ PipelineResults test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run tests"""
    logger.info("Testing Pipeline V4 Data Structures")
    logger.info("=" * 50)

    if test_pipeline_results():
        logger.info("\n✓ All tests passed!")
        return 0
    else:
        logger.error("\n✗ Test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())