#!/usr/bin/env python3
"""
Test DLT Storage Direct Connection

This script tests the DLT storage functionality directly with mock data
to verify the port fix resolved the silent failure issue.
"""

import sys
import logging
from pathlib import Path

# Add project paths
pipeline_v2_root = Path(__file__).parent.resolve()
project_root = Path(__file__).parent.parent.resolve()

sys.path.insert(0, str(pipeline_v2_root))
sys.path.insert(1, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_dlt_connection():
    """Test DLT connection and storage with mock data."""
    try:
        # Import DLT storage module
        from storage import create_dlt_loader

        logger.info("✓ DLT storage module imported successfully")

        # Create DLT loader
        loader = create_dlt_loader(
            pipeline_name="test_connection_fix",
            use_local_dev=True
        )

        logger.info("✓ DLT loader created successfully")

        # Test connection validation
        connection_valid = loader.validate_connection()
        logger.info(f"✓ Connection validation: {connection_valid}")

        if not connection_valid:
            logger.error("✗ DLT connection validation failed")
            return False

        # Create mock opportunity data
        mock_opportunities = [
            {
                "submission_id": "test_dlt_fix_001",
                "title": "Test DLT Port Fix - Productivity App Idea",
                "text": "Looking for an app that helps track productivity across multiple projects with AI-powered insights and team collaboration features.",
                "subreddit": "productivity",
                "upvotes": 15,
                "comments_count": 8,
                "score": 23,
                "created_utc": "2024-11-26T21:45:00Z",
                "permalink": "https://reddit.com/r/productivity/comments/test_dlt_fix_001",
                "quality_score": 85.0,
                "opportunity_score": 75.0,
                "core_functions": ["productivity", "tracking", "collaboration"],
                "app_concept": "Multi-project productivity tracker with AI insights",
                "problem_description": "Users need better ways to track productivity across multiple projects and teams",
                "trust_score": 65.0,
                "trust_level": "MEDIUM",
                "trust_badges": ["ACTIVE_DISCUSSION", "QUALITY_CONTENT"],
                "confidence_score": 70.0,
                "monetization_score": 80.0,
                "willingness_to_pay_score": 75.0,
                "customer_segment": "Professionals and Team Leaders",
                "processed_at": "2025-11-26T21:45:00Z",
                "pipeline_version": "pipeline_v2"
            }
        ]

        logger.info(f"✓ Created {len(mock_opportunities)} mock opportunity records")

        # Test DLT load
        load_info = loader.load_opportunities(
            mock_opportunities,
            table_name="app_opportunities",
            write_disposition="merge",
            primary_key="submission_id"
        )

        logger.info("✓ DLT load completed successfully")

        # Extract and display load statistics
        stats = loader.get_load_statistics(load_info)
        logger.info("Load Statistics:")
        for key, value in stats.items():
            logger.info(f"  - {key}: {value}")

        return stats.get("total_records", 0) > 0

    except Exception as e:
        logger.error(f"✗ DLT test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main test function."""
    logger.info("=" * 80)
    logger.info("TESTING DLT STORAGE DIRECT CONNECTION")
    logger.info("=" * 80)

    success = test_dlt_connection()

    logger.info("=" * 80)
    if success:
        logger.info("✓ DLT STORAGE TEST PASSED - Port fix successful!")
        logger.info("✓ Data is now being stored correctly in the database")
    else:
        logger.error("✗ DLT STORAGE TEST FAILED - Issue persists")
        logger.error("✗ Check database connection and DLT configuration")
    logger.info("=" * 80)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())