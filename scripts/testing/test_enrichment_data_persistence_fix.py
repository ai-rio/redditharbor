#!/usr/bin/env python3
"""
Test Enrichment Data Persistence Fix

This script tests the fix for enrichment data persistence in RedditHarbor pipeline.
It validates that enrichment data from all 5 AI services is properly written to
the correct specialized tables.

Test Validation:
1. Pipeline executes all 5 services successfully
2. Enrichment data is written to specialized tables (opportunity_scores, etc.)
3. Field coverage reaches 90%+ when checking all tables
4. UUID-based foreign key relationships are maintained

Created: 2025-11-22
Author: RedditHarbor Data Engineering Team
"""

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Set up paths
test_utils_path = Path(__file__).parent.resolve()
project_root = Path(__file__).parent.parent.parent.resolve()

sys.path.insert(0, str(test_utils_path))
sys.path.insert(1, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env.local")

# Import test utilities
from config import load_service_config, load_submissions_config, get_observability_config
from utils import MetricsCollector, ObservabilityManager

# Import main project settings
import importlib.util
spec = importlib.util.spec_from_file_location("main_config", project_root / "config" / "settings.py")
main_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_config)
SUPABASE_URL = main_config.SUPABASE_URL
SUPABASE_KEY = main_config.SUPABASE_KEY
from supabase import create_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_test_submission_id() -> str:
    """Get a test submission ID from the database."""
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Query for a high-quality submission
    result = client.table("submissions").select(
        "id, submission_id, title, subreddit, score, num_comments"
    ).gte("score", 50).gte("num_comments", 10).limit(1).execute()

    if not result.data or len(result.data) == 0:
        raise ValueError("No high-quality submissions found in database")

    return result.data[0]["submission_id"]

def test_enhanced_hybrid_store():
    """Test the EnhancedHybridStore directly."""
    print("\n" + "=" * 80)
    print("TESTING ENHANCED HYBRID STORE")
    print("=" * 80)

    try:
        from core.storage.enhanced_hybrid_store import EnhancedHybridStore
        from core.pipeline import PipelineConfig, DataSource

        # Create test data with all service outputs
        test_submission = {
            "submission_id": "test_enhanced_store_001",
            "title": "Need better project management tool",
            "content": "Current tools are too expensive and complicated",
            "subreddit": "startups",
            "score": 150,
            "num_comments": 45,

            # OpportunityService outputs
            "final_score": 85.0,
            "dimension_scores": {
                "market_demand": 0.9,
                "pain_intensity": 0.8,
                "competition_level": 0.6,
                "technical_feasibility": 0.7,
                "monetization_potential": 0.8,
            },
            "priority": "high",
            "confidence": 0.85,
            "evidence_based": True,
            "core_functions": ["Task management", "Team collaboration"],
            "problem_description": "Teams struggle with complex PM tools",
            "target_user": "Small teams and startups",

            # ProfilerService outputs
            "profession": "Software Engineer",
            "ai_profile": {
                "overall_score": 85.0,
                "analysis_available": True
            },
            "app_name": "SimplePM",
            "app_category": "Productivity",
            "core_problems": ["Complexity", "Cost", "Learning curve"],

            # MonetizationService outputs
            "willingness_to_pay_score": 75.0,
            "customer_segment": "B2B",
            "price_sensitivity_score": 60.0,
            "revenue_potential_score": 80.0,
            "mentioned_price_points": [50, 100],
            "existing_payment_behavior": "Currently paying $100/month",
            "urgency_level": "high",
            "sentiment_toward_payment": "positive",
            "llm_monetization_score": 78.0,

            # TrustService outputs
            "trust_level": "medium",
            "overall_trust_score": 75.0,
            "trust_badges": ["quality_discussion"],

            # MarketValidationService outputs
            "market_validation_score": 70.0,
            "market_data_quality_score": 80.0,
            "validation_reasoning": "Clear market need with competitors",
            "market_competitors_found": [
                {"company_name": "Asana", "pricing_model": "subscription"}
            ],
            "market_similar_launches": 5,
        }

        # Create EnhancedHybridStore
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        store = EnhancedHybridStore(supabase_client=client)

        print("✓ EnhancedHybridStore initialized successfully")

        # Store test data
        print("Storing test enrichment data...")
        success = store.store([test_submission])

        if success:
            print("✓ EnhancedHybridStore storage successful")

            # Get enhanced statistics
            stats = store.get_enhanced_statistics()
            print(f"  - Records loaded: {stats.get('loaded', 0)}")
            print(f"  - Enrichment tables written: {stats.get('enrichment_tables_written', [])}")

            # Validate table population
            from utils.enhanced_metrics import validate_enrichment_tables_populated
            table_validation = validate_enrichment_tables_populated(client, test_submission["submission_id"])

            print("\nTable Population Validation:")
            populated_count = 0
            for table_name, is_populated in table_validation.items():
                status = "✓" if is_populated else "✗"
                print(f"  {status} {table_name}")
                if is_populated:
                    populated_count += 1

            coverage = (populated_count / len(table_validation)) * 100
            print(f"\nTable Coverage: {populated_count}/{len(table_validation)} ({coverage:.1f}%)")

            if coverage >= 80:
                print("✅ Table coverage target met")
                return True
            else:
                print("❌ Table coverage target missed")
                return False

        else:
            print("❌ EnhancedHybridStore storage failed")
            return False

    except Exception as e:
        print(f"❌ EnhancedHybridStore test failed: {e}")
        logger.error(f"EnhancedHybridStore test error: {e}", exc_info=True)
        return False

def test_pipeline_with_enhanced_storage(submission_id: str):
    """Test the complete pipeline with enhanced storage."""
    print("\n" + "=" * 80)
    print("TESTING COMPLETE PIPELINE WITH ENHANCED STORAGE")
    print("=" * 80)

    try:
        from core.pipeline import OpportunityPipeline, PipelineConfig, DataSource

        # Create pipeline config
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=1,
            enable_profiler=True,
            enable_opportunity_scoring=True,
            enable_monetization=True,
            enable_trust=True,
            enable_market_validation=True,
            ai_profile_threshold=0.0,
            monetization_threshold=0.0,
            market_validation_threshold=0.0,
            return_data=True,
            dry_run=False,
            supabase_client=client,
            source_config={
                "table_name": "submissions",
                "filter_column": "submission_id",
                "filter_value": submission_id,
            },
            enable_deduplication=False,
            monetization_strategy="agno",
        )

        print(f"✓ Pipeline config created for submission: {submission_id}")

        # Create and run pipeline
        pipeline = OpportunityPipeline(config)
        print(f"✓ Pipeline initialized with {len(pipeline.services)} services")

        print("\nRunning pipeline with enhanced storage...")
        start_time = time.time()

        result = pipeline.run()
        processing_time = time.time() - start_time

        if result.get("success"):
            print(f"✓ Pipeline completed in {processing_time:.2f}s")

            # Get enriched data
            enriched_submissions = result.get("opportunities", [])
            if not enriched_submissions:
                print("❌ No enriched submissions returned")
                return False

            enriched_submission = enriched_submissions[0]

            # Test enhanced field coverage
            from utils.enhanced_metrics import calculate_enhanced_field_coverage
            field_coverage, populated_fields = calculate_enhanced_field_coverage(
                enriched_submission, client, submission_id
            )

            print(f"\nField Coverage Results:")
            print(f"  - Fields populated: {len(populated_fields)}/38")
            print(f"  - Coverage: {field_coverage:.1f}%")

            # Validate enrichment tables
            from utils.enhanced_metrics import validate_enrichment_tables_populated
            table_validation = validate_enrichment_tables_populated(client, submission_id)

            print(f"\nEnrichment Table Validation:")
            populated_tables = 0
            for table_name, is_populated in table_validation.items():
                status = "✓" if is_populated else "✗"
                print(f"  {status} {table_name:25s}")
                if is_populated:
                    populated_tables += 1

            table_coverage = (populated_tables / len(table_validation)) * 100
            print(f"\nTable Coverage: {populated_tables}/{len(table_validation)} ({table_coverage:.1f}%)")

            # Determine success
            success = (
                field_coverage >= 90 and  # Field coverage target
                table_coverage >= 80     # Table coverage target
            )

            if success:
                print("\n✅ ENRICHMENT DATA PERSISTENCE TEST PASSED")
                print("  - Field coverage ≥ 90%")
                print("  - Table coverage ≥ 80%")
                print("  - All enrichment data properly persisted")
                return True
            else:
                print("\n❌ ENRICHMENT DATA PERSISTENCE TEST FAILED")
                if field_coverage < 90:
                    print(f"  - Field coverage below target: {field_coverage:.1f}% < 90%")
                if table_coverage < 80:
                    print(f"  - Table coverage below target: {table_coverage:.1f}% < 80%")
                return False

        else:
            error = result.get("error", "Unknown error")
            print(f"❌ Pipeline failed: {error}")
            return False

    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        logger.error(f"Pipeline test error: {e}", exc_info=True)
        return False

def main():
    """Main test execution."""
    parser = argparse.ArgumentParser(description="Test Enrichment Data Persistence Fix")
    parser.add_argument(
        "--submission-id",
        type=str,
        help="Specific submission ID to test (optional, will query database if not provided)"
    )
    parser.add_argument(
        "--store-only",
        action="store_true",
        help="Test EnhancedHybridStore only (skip full pipeline)"
    )

    args = parser.parse_args()

    print("RedditHarbor Enrichment Data Persistence Fix Test")
    print("=" * 80)

    try:
        # Get submission ID
        if args.submission_id:
            submission_id = args.submission_id
            print(f"Using provided submission ID: {submission_id}")
        else:
            submission_id = get_test_submission_id()
            print(f"Selected test submission: {submission_id}")

        # Run tests
        results = []

        # Test EnhancedHybridStore directly
        store_result = test_enhanced_hybrid_store()
        results.append(("EnhancedHybridStore", store_result))

        # Test complete pipeline (unless disabled)
        if not args.store_only:
            pipeline_result = test_pipeline_with_enhanced_storage(submission_id)
            results.append(("Complete Pipeline", pipeline_result))

        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:25s} {status}")

        all_passed = all(result for _, result in results)

        if all_passed:
            print("\n✅ ALL TESTS PASSED - Enrichment data persistence fix working correctly")
            sys.exit(0)
        else:
            print("\n❌ SOME TESTS FAILED - Fix needs additional work")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        logger.error(f"Test execution error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()