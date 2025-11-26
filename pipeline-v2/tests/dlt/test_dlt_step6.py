#!/usr/bin/env python3
"""
Standalone Test Script for RedditHarbor Pipeline v2 - Step 6: DLT Loading to Supabase

This script directly tests the DLT loading component (Step 6 of the pipeline)
without going through the full pipeline initialization.

Tests:
1. DLT configuration loading from .dlt/secrets.toml
2. Connection to Supabase PostgreSQL database
3. Sample data loading to app_opportunities table with merge disposition

Author: Standalone DLT Test
Version: 1.0
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List

# Add pipeline-v2 to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_sample_opportunity_data() -> List[Dict[str, Any]]:
    """
    Create sample opportunity data for testing DLT loading.

    Returns:
        List of opportunity records matching app_opportunities table schema
    """
    sample_data = [
        {
            "submission_id": "test_opportunity_001",
            "title": "Looking for a productivity app that helps track daily habits",
            "text": "I need an app that can help me build better habits and track my progress throughout the day.",
            "subreddit": "productivity",
            "upvotes": 145,
            "comments_count": 23,
            "score": 145.0,
            "created_utc": "2024-11-26T10:00:00Z",
            "permalink": "https://reddit.com/r/productivity/comments/test001",

            # Quality and analysis fields
            "quality_score": 85.5,
            "filter_reason": None,
            "opportunity_score": 78.2,
            "core_functions": ["habit_tracking", "progress_monitoring", "daily_planning"],
            "app_concept": "Habit Forge - Daily habit builder with progress visualization",
            "problem_description": "User needs systematic approach to habit formation with tracking",

            # Trust validation fields
            "trust_score": 75.8,
            "trust_level": "high",
            "trust_badges": ["verified_user", "active_member"],
            "confidence_score": 0.82,

            # Monetization analysis fields
            "monetization_score": 65.4,
            "willingness_to_pay_score": 70.1,
            "customer_segment": "productivity_enthusiasts",

            # Processing metadata
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "pipeline_version": "pipeline_v2_test"
        },
        {
            "submission_id": "test_opportunity_002",
            "title": "Need a budget app that automatically categorizes expenses",
            "text": "I'm looking for an app that can connect to my bank account and automatically sort my spending into categories.",
            "subreddit": "personalfinance",
            "upvotes": 289,
            "comments_count": 67,
            "score": 289.0,
            "created_utc": "2024-11-26T12:30:00Z",
            "permalink": "https://reddit.com/r/personalfinance/comments/test002",

            # Quality and analysis fields
            "quality_score": 92.3,
            "filter_reason": None,
            "opportunity_score": 88.7,
            "core_functions": ["expense_tracking", "bank_integration", "auto_categorization", "budget_planning"],
            "app_concept": "Smart Budget - AI-powered expense categorization and financial insights",
            "problem_description": "Manual expense tracking is time-consuming and error-prone",

            # Trust validation fields
            "trust_score": 89.4,
            "trust_level": "very_high",
            "trust_badges": ["trusted_member", "financial_contributor"],
            "confidence_score": 0.91,

            # Monetization analysis fields
            "monetization_score": 85.2,
            "willingness_to_pay_score": 88.9,
            "customer_segment": "finance_professionals",

            # Processing metadata
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "pipeline_version": "pipeline_v2_test"
        }
    ]

    logger.info(f"✓ Created {len(sample_data)} sample opportunity records")
    return sample_data

def test_dlt_import_and_configuration():
    """
    Test DLT import and configuration loading from .dlt/secrets.toml

    Returns:
        Tuple of (success: bool, loader_instance: DLTLoader or None, error: str or None)
    """
    try:
        logger.info("=== Testing DLT Import and Configuration ===")

        # Import DLT loader
        logger.info("1. Importing DLT loader...")
        try:
            from storage.dlt_loader import DLTLoader, create_dlt_loader
            logger.info("✓ DLT loader imported successfully")
        except ImportError as e:
            error_msg = f"Failed to import DLT loader: {e}"
            logger.error(f"✗ {error_msg}")
            return False, None, error_msg

        # Check DLT availability
        logger.info("2. Checking DLT library availability...")
        try:
            import dlt
            dlt_version = getattr(dlt, '__version__', 'unknown')
            logger.info(f"✓ DLT library available (version: {dlt_version})")
        except ImportError as e:
            error_msg = f"DLT library not available: {e}"
            logger.error(f"✗ {error_msg}")
            return False, None, error_msg

        # Create DLT loader instance
        logger.info("3. Creating DLT loader instance...")
        try:
            # Use the exact path mentioned in the context
            loader = create_dlt_loader(
                pipeline_name="test_dlt_step6_pipeline",
                secrets_path="/home/carlos/projects/redditharbor-core-functions-fix/pipeline-v2/.dlt/secrets.toml",
                use_local_dev=False  # Use actual configured credentials
            )
            logger.info("✓ DLT loader instance created successfully")
            return True, loader, None

        except Exception as e:
            error_msg = f"Failed to create DLT loader: {e}"
            logger.error(f"✗ {error_msg}")
            return False, None, error_msg

    except Exception as e:
        error_msg = f"Unexpected error during DLT import: {e}"
        logger.error(f"✗ {error_msg}")
        return False, None, error_msg

def test_dlt_connection(loader) -> bool:
    """
    Test DLT connection to Supabase.

    Args:
        loader: DLT loader instance

    Returns:
        True if connection test passes, False otherwise
    """
    try:
        logger.info("=== Testing DLT Connection to Supabase ===")

        # Test configuration validation
        logger.info("1. Validating DLT configuration...")
        if hasattr(loader, '_validate_configuration'):
            loader._validate_configuration()
            logger.info("✓ DLT configuration validation passed")

        # Test connection by creating pipeline
        logger.info("2. Testing connection via pipeline creation...")
        pipeline = loader.create_pipeline(
            destination="postgres",
            dataset_name="app_opportunities"
        )

        if pipeline:
            logger.info("✓ DLT pipeline created successfully - connection test passed")
            return True
        else:
            logger.error("✗ Failed to create DLT pipeline")
            return False

    except Exception as e:
        logger.error(f"✗ DLT connection test failed: {e}")
        return False

def test_dlt_data_loading(loader, sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Test DLT data loading to app_opportunities table.

    Args:
        loader: DLT loader instance
        sample_data: Sample opportunity data to load

    Returns:
        Dictionary with test results and statistics
    """
    try:
        logger.info("=== Testing DLT Data Loading ===")

        # Load sample data
        logger.info(f"1. Loading {len(sample_data)} opportunity records...")

        load_info = loader.load_opportunities(
            opportunities=sample_data,
            table_name="app_opportunities",
            primary_key="submission_id",
            write_disposition="merge"
        )

        # Extract load statistics
        stats = loader.get_load_statistics(load_info)

        logger.info("✓ DLT data loading completed successfully")
        logger.info(f"  - Load ID: {stats.get('load_id', 'unknown')}")
        logger.info(f"  - Records processed: {stats.get('total_records', 0)}")
        logger.info(f"  - Table: app_opportunities")
        logger.info(f"  - Write disposition: merge")
        logger.info(f"  - Primary key: submission_id")

        return {
            "success": True,
            "load_statistics": stats,
            "load_info": load_info
        }

    except Exception as e:
        error_msg = f"DLT data loading test failed: {e}"
        logger.error(f"✗ {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "load_statistics": None,
            "load_info": None
        }

def main():
    """
    Main test function that orchestrates all DLT Step 6 tests.
    """
    logger.info("=" * 60)
    logger.info("RedditHarbor Pipeline v2 - Step 6 DLT Loading Test")
    logger.info("=" * 60)

    test_results = {
        "dlt_import": {"success": False, "error": None},
        "dlt_connection": {"success": False},
        "dlt_loading": {"success": False, "error": None, "stats": None},
        "overall_success": False
    }

    try:
        # Step 1: Test DLT import and configuration
        logger.info("\n" + "=" * 40)
        logger.info("STEP 1: DLT Import and Configuration Test")
        logger.info("=" * 40)

        import_success, loader, import_error = test_dlt_import_and_configuration()
        test_results["dlt_import"]["success"] = import_success
        test_results["dlt_import"]["error"] = import_error

        if not import_success:
            logger.error("❌ DLT import/configuration failed. Cannot proceed with connection/loading tests.")
            print_test_results(test_results)
            return False

        # Step 2: Test DLT connection to Supabase
        logger.info("\n" + "=" * 40)
        logger.info("STEP 2: DLT Connection Test")
        logger.info("=" * 40)

        connection_success = test_dlt_connection(loader)
        test_results["dlt_connection"]["success"] = connection_success

        if not connection_success:
            logger.error("❌ DLT connection test failed. Cannot proceed with data loading test.")
            print_test_results(test_results)
            return False

        # Step 3: Test DLT data loading
        logger.info("\n" + "=" * 40)
        logger.info("STEP 3: DLT Data Loading Test")
        logger.info("=" * 40)

        sample_data = create_sample_opportunity_data()
        loading_results = test_dlt_data_loading(loader, sample_data)

        test_results["dlt_loading"]["success"] = loading_results["success"]
        test_results["dlt_loading"]["error"] = loading_results.get("error")
        test_results["dlt_loading"]["stats"] = loading_results.get("load_statistics")

        # Overall success determination
        test_results["overall_success"] = all([
            test_results["dlt_import"]["success"],
            test_results["dlt_connection"]["success"],
            test_results["dlt_loading"]["success"]
        ])

        # Print final results
        print_test_results(test_results)
        return test_results["overall_success"]

    except Exception as e:
        logger.error(f"❌ Unexpected error in main test execution: {e}")
        test_results["overall_success"] = False
        test_results["error"] = str(e)
        print_test_results(test_results)
        return False

def print_test_results(results: Dict[str, Any]):
    """
    Print formatted test results summary.

    Args:
        results: Test results dictionary
    """
    logger.info("\n" + "=" * 60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 60)

    # DLT Import/Configuration
    import_result = "✅ PASS" if results["dlt_import"]["success"] else "❌ FAIL"
    logger.info(f"DLT Import & Configuration: {import_result}")
    if not results["dlt_import"]["success"] and results["dlt_import"]["error"]:
        logger.info(f"  Error: {results['dlt_import']['error']}")

    # DLT Connection
    connection_result = "✅ PASS" if results["dlt_connection"]["success"] else "❌ FAIL"
    logger.info(f"DLT Connection to Supabase: {connection_result}")

    # DLT Data Loading
    loading_result = "✅ PASS" if results["dlt_loading"]["success"] else "❌ FAIL"
    logger.info(f"DLT Data Loading: {loading_result}")
    if results["dlt_loading"]["success"] and results["dlt_loading"]["stats"]:
        stats = results["dlt_loading"]["stats"]
        logger.info(f"  Records loaded: {stats.get('total_records', 0)}")
        logger.info(f"  Load ID: {stats.get('load_id', 'unknown')}")
    elif not results["dlt_loading"]["success"] and results["dlt_loading"]["error"]:
        logger.info(f"  Error: {results['dlt_loading']['error']}")

    # Overall Result
    logger.info("-" * 60)
    overall_result = "🎉 SUCCESS" if results["overall_success"] else "⚠️  FAILURE"
    logger.info(f"OVERALL STEP 6 TEST: {overall_result}")

    if results["overall_success"]:
        logger.info("\n✅ Step 6 (DLT Loading to Supabase) is ready!")
        logger.info("🚀 Your DLT configuration is working correctly.")
    else:
        logger.info("\n❌ Step 6 (DLT Loading to Supabase) needs attention.")
        logger.info("🔧 Check the errors above and fix configuration issues.")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)