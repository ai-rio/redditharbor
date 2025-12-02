#!/usr/bin/env python3
"""
Test Script: EnhancedHybridStore Fix Validation

This script validates that the EnhancedHybridStore fix works correctly.

The original issue was:
1. FK constraint violations - random UUIDs were generated that didn't exist in the
   `opportunities` table
2. Silent error handling - errors were caught but not propagated
3. Wrong success logic - returned `total_count > 0` instead of `success_count > 0`

The fix ensures:
1. `_get_or_create_opportunity_id()` returns None when it fails (not a random UUID)
2. FK violations are logged with `[FK_VIOLATION]` prefix
3. Success is based on `success_count > 0` (actual inserts, not attempts)

Test Coverage:
1. Verifies records are created in the `opportunities` table
2. Verifies records are created in all 4 enrichment tables:
   - opportunity_scores
   - monetization_patterns
   - market_validations
   - competitive_landscape
3. Verifies proper error handling and logging

Created: 2025-11-22
"""

import json
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_base_submission_record(supabase_client, submission_id: str) -> bool:
    """Create a base submission record in the submissions table (FK requirement).

    The opportunities table has a FK constraint to submissions table, so we need
    to create a submission record first before we can create an opportunity.
    """
    try:
        # Note: reddit_id is VARCHAR(20), so use a short ID
        # submission_id is the UUID we'll use for FK
        short_reddit_id = f"test_{submission_id[:8]}"  # e.g., "test_aca32db4"

        # Generate a unique DLT load ID for this test
        import time
        dlt_load_id = f"test_{time.time()}"

        # IMPORTANT: The opportunities.submission_id FK references submissions.id (the PK)
        # NOT submissions.submission_id. So we need to set id = submission_id so the FK works.
        submission_record = {
            "id": submission_id,  # Set id explicitly so opportunities FK will work
            "submission_id": submission_id,
            "reddit_id": short_reddit_id,  # Required NOT NULL field, VARCHAR(20)
            "title": "Test Submission for EnhancedHybridStore Fix Validation",
            "selftext": "This is test content to validate the EnhancedHybridStore fix works correctly.",
            "subreddit": "test_subreddit",
            "author": "test_author",
            "_dlt_load_id": dlt_load_id,  # Required NOT NULL field
            "_dlt_id": f"test_{submission_id[:16]}",  # Required NOT NULL field
        }
        response = supabase_client.table("submissions").insert(submission_record).execute()
        if response.data:
            logger.info(f"Created base submission record: {submission_id}")
            return True
        else:
            logger.error(f"Failed to create base submission record: {response}")
            return False
    except Exception as e:
        # Check if it's a duplicate key error (already exists)
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            logger.info(f"Base submission record already exists: {submission_id}")
            return True
        logger.error(f"Error creating base submission record: {e}")
        return False


def create_test_submission(submission_id: str) -> dict:
    """Create a test submission with all required enrichment fields."""
    return {
        # Core identifiers - use proper UUID format
        "submission_id": submission_id,
        "title": "Test Submission for EnhancedHybridStore Fix Validation",
        "content": "This is test content to validate the EnhancedHybridStore fix works correctly.",
        "subreddit": "test_subreddit",
        # Required for HybridStore to create opportunity entry
        "problem_description": "Users need a way to test storage functionality",
        "app_concept": "A test application for validation purposes",
        "target_user": "Developers testing the system",
        # Opportunity scoring data - triggers opportunity_scores mapping
        "final_score": 75.0,
        "opportunity_score": 75.0,
        "dimension_scores": {
            "market_demand": 0.7,
            "pain_intensity": 0.8,
            "competition_level": 0.5,
            "technical_feasibility": 0.9,
            "monetization_potential": 0.75,
            "simplicity_score": 0.6,
        },
        # Monetization data - triggers monetization_patterns mapping
        "willingness_to_pay_score": 80.0,
        "monetization_model": "subscription",
        "llm_monetization_score": 72.0,
        # Market validation data - triggers market_validations mapping
        "market_validation_score": 70.0,
        "market_data_quality_score": 65.0,
        "market_validation_reasoning": "Test validation reasoning",
        # Competitors data - triggers competitive_landscape mapping
        "market_competitors_found": [
            {
                "company_name": "TestCompetitor1",
                "features": {"feature1": "value1", "feature2": "value2"},
                "analysis": "Competitor analysis for testing",
                "market_share": 0.25,
            },
            {
                "company_name": "TestCompetitor2",
                "features": {"feature1": "value1"},
                "analysis": "Second competitor analysis",
                "market_share": 0.15,
            },
        ],
    }


def cleanup_test_data(supabase_client, submission_id: str, opportunity_id: str = None):
    """Clean up test data from all tables."""
    logger.info(f"Cleaning up test data for submission_id={submission_id}")

    tables_cleaned = []

    try:
        # First, get the opportunity_id if we don't have it
        if opportunity_id is None:
            try:
                response = (
                    supabase_client.table("opportunities")
                    .select("id")
                    .eq("submission_id", submission_id)
                    .execute()
                )
                if response.data and len(response.data) > 0:
                    opportunity_id = response.data[0]["id"]
                    logger.info(f"Found opportunity_id={opportunity_id} for cleanup")
            except Exception as e:
                logger.debug(f"Could not find opportunity_id: {e}")

        # Clean enrichment tables first (they have FK to opportunities)
        if opportunity_id:
            for table in [
                "opportunity_scores",
                "monetization_patterns",
                "market_validations",
                "competitive_landscape",
            ]:
                try:
                    response = (
                        supabase_client.table(table)
                        .delete()
                        .eq("opportunity_id", opportunity_id)
                        .execute()
                    )
                    deleted_count = len(response.data) if response.data else 0
                    if deleted_count > 0:
                        tables_cleaned.append(f"{table}: {deleted_count}")
                        logger.info(f"Cleaned {table}: {deleted_count} records deleted")
                except Exception as e:
                    logger.debug(f"Could not clean {table}: {e}")

        # Clean opportunities table
        try:
            response = (
                supabase_client.table("opportunities")
                .delete()
                .eq("submission_id", submission_id)
                .execute()
            )
            deleted_count = len(response.data) if response.data else 0
            if deleted_count > 0:
                tables_cleaned.append(f"opportunities: {deleted_count}")
                logger.info(f"Cleaned opportunities: {deleted_count} records deleted")
        except Exception as e:
            logger.debug(f"Could not clean opportunities: {e}")

        # Clean app_opportunities table
        try:
            response = (
                supabase_client.table("app_opportunities")
                .delete()
                .eq("submission_id", submission_id)
                .execute()
            )
            deleted_count = len(response.data) if response.data else 0
            if deleted_count > 0:
                tables_cleaned.append(f"app_opportunities: {deleted_count}")
                logger.info(f"Cleaned app_opportunities: {deleted_count} records deleted")
        except Exception as e:
            logger.debug(f"Could not clean app_opportunities: {e}")

        # Clean submissions table
        try:
            response = (
                supabase_client.table("submissions")
                .delete()
                .eq("submission_id", submission_id)
                .execute()
            )
            deleted_count = len(response.data) if response.data else 0
            if deleted_count > 0:
                tables_cleaned.append(f"submissions: {deleted_count}")
                logger.info(f"Cleaned submissions: {deleted_count} records deleted")
        except Exception as e:
            logger.debug(f"Could not clean submissions: {e}")

        if tables_cleaned:
            logger.info(f"Cleanup complete: {tables_cleaned}")
        else:
            logger.info("Cleanup complete: No records found to delete")

    except Exception as e:
        logger.warning(f"Cleanup encountered issues: {e}")


def run_tests():
    """Run all tests for the EnhancedHybridStore fix."""
    # Initialize Supabase client
    logger.info(f"Connecting to Supabase at {SUPABASE_URL}")
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Generate a proper UUID for test submission_id
    # This avoids the UUID conversion issues
    test_submission_id = str(uuid.uuid4())
    logger.info(f"Test submission ID: {test_submission_id}")

    # Track test results
    test_results = {
        "passed": 0,
        "failed": 0,
        "details": [],
    }

    opportunity_id = None

    try:
        # Import EnhancedHybridStore
        from core.storage.enhanced_hybrid_store import EnhancedHybridStore

        # =========================================================================
        # TEST 1: Test _get_or_create_opportunity_id directly
        # =========================================================================
        logger.info("\n" + "=" * 70)
        logger.info("TEST 1: Test _get_or_create_opportunity_id directly")
        logger.info("=" * 70)

        # Clean up any existing test data first
        cleanup_test_data(supabase_client, test_submission_id)

        # Create base submission record (FK requirement for opportunities table)
        if not create_base_submission_record(supabase_client, test_submission_id):
            raise Exception("Failed to create base submission record - cannot continue tests")

        # Create test submission data
        test_submission = create_test_submission(test_submission_id)
        logger.info(f"Created test submission with ID: {test_submission_id}")

        # Initialize EnhancedHybridStore with Supabase client
        enhanced_store = EnhancedHybridStore(supabase_client=supabase_client)
        logger.info("EnhancedHybridStore initialized")

        # Test _get_or_create_opportunity_id - this should create an opportunity
        opportunity_id = enhanced_store._get_or_create_opportunity_id(test_submission)

        if opportunity_id is not None:
            logger.info(f"[PASS] TEST 1: _get_or_create_opportunity_id returned: {opportunity_id}")
            test_results["passed"] += 1
            test_results["details"].append({
                "test": "TEST 1: _get_or_create_opportunity_id",
                "status": "PASS",
                "details": f"Created opportunity_id={opportunity_id}",
            })
        else:
            logger.error("[FAIL] TEST 1: _get_or_create_opportunity_id returned None")
            test_results["failed"] += 1
            test_results["details"].append({
                "test": "TEST 1: _get_or_create_opportunity_id",
                "status": "FAIL",
                "details": "Returned None instead of opportunity_id",
            })
            raise Exception("Cannot continue tests without opportunity_id")

        # =========================================================================
        # TEST 2: Verify opportunity was created in database
        # =========================================================================
        logger.info("\n" + "=" * 70)
        logger.info("TEST 2: Verify opportunity was created in database")
        logger.info("=" * 70)

        response = (
            supabase_client.table("opportunities")
            .select("*")
            .eq("id", opportunity_id)
            .execute()
        )

        if response.data and len(response.data) > 0:
            record = response.data[0]
            logger.info(f"[PASS] TEST 2: Opportunity record found in database")
            logger.info(f"  - id: {record.get('id')}")
            logger.info(f"  - submission_id: {record.get('submission_id')}")
            logger.info(f"  - title: {record.get('title')[:50] if record.get('title') else 'None'}...")
            test_results["passed"] += 1
            test_results["details"].append({
                "test": "TEST 2: Opportunity in database",
                "status": "PASS",
                "details": f"Found record with id={opportunity_id}",
            })
        else:
            logger.error("[FAIL] TEST 2: Opportunity not found in database")
            test_results["failed"] += 1
            test_results["details"].append({
                "test": "TEST 2: Opportunity in database",
                "status": "FAIL",
                "details": "No record found",
            })

        # =========================================================================
        # TEST 3: Test _store_to_enrichment_tables directly
        # =========================================================================
        logger.info("\n" + "=" * 70)
        logger.info("TEST 3: Test _store_to_enrichment_tables directly")
        logger.info("=" * 70)

        # Call _store_to_enrichment_tables directly
        enrichment_result = enhanced_store._store_to_enrichment_tables([test_submission])
        logger.info(f"_store_to_enrichment_tables returned: {enrichment_result}")

        if enrichment_result:
            logger.info("[PASS] TEST 3: _store_to_enrichment_tables returned True")
            test_results["passed"] += 1
            test_results["details"].append({
                "test": "TEST 3: _store_to_enrichment_tables",
                "status": "PASS",
                "details": "Returned True indicating successful storage",
            })
        else:
            logger.error("[FAIL] TEST 3: _store_to_enrichment_tables returned False")
            test_results["failed"] += 1
            test_results["details"].append({
                "test": "TEST 3: _store_to_enrichment_tables",
                "status": "FAIL",
                "details": "Returned False",
            })

        # =========================================================================
        # TEST 4: Verify opportunity_scores table
        # =========================================================================
        logger.info("\n" + "=" * 70)
        logger.info("TEST 4: Verify opportunity_scores table")
        logger.info("=" * 70)

        response = (
            supabase_client.table("opportunity_scores")
            .select("*")
            .eq("opportunity_id", opportunity_id)
            .execute()
        )

        if response.data and len(response.data) > 0:
            record = response.data[0]
            logger.info(f"[PASS] TEST 4: opportunity_scores has {len(response.data)} record(s)")
            logger.info(f"  - market_demand: {record.get('market_demand')}")
            logger.info(f"  - pain_intensity: {record.get('pain_intensity')}")
            logger.info(f"  - competition_level: {record.get('competition_level')}")
            logger.info(f"  - technical_feasibility: {record.get('technical_feasibility')}")
            logger.info(f"  - monetization_potential: {record.get('monetization_potential')}")
            logger.info(f"  - simplicity_score: {record.get('simplicity_score')}")
            test_results["passed"] += 1
            test_results["details"].append({
                "test": "TEST 4: opportunity_scores table",
                "status": "PASS",
                "details": "Record found with all dimension scores",
            })
        else:
            logger.error("[FAIL] TEST 4: opportunity_scores table is empty")
            test_results["failed"] += 1
            test_results["details"].append({
                "test": "TEST 4: opportunity_scores table",
                "status": "FAIL",
                "details": "No record found",
            })

        # =========================================================================
        # TEST 5: Verify monetization_patterns table
        # =========================================================================
        logger.info("\n" + "=" * 70)
        logger.info("TEST 5: Verify monetization_patterns table")
        logger.info("=" * 70)

        response = (
            supabase_client.table("monetization_patterns")
            .select("*")
            .eq("opportunity_id", opportunity_id)
            .execute()
        )

        if response.data and len(response.data) > 0:
            record = response.data[0]
            logger.info(f"[PASS] TEST 5: monetization_patterns has {len(response.data)} record(s)")
            logger.info(f"  - pattern_type: {record.get('pattern_type')}")
            logger.info(f"  - revenue_model: {record.get('revenue_model')}")
            test_results["passed"] += 1
            test_results["details"].append({
                "test": "TEST 5: monetization_patterns table",
                "status": "PASS",
                "details": f"Record found with revenue_model={record.get('revenue_model')}",
            })
        else:
            logger.error("[FAIL] TEST 5: monetization_patterns table is empty")
            test_results["failed"] += 1
            test_results["details"].append({
                "test": "TEST 5: monetization_patterns table",
                "status": "FAIL",
                "details": "No record found",
            })

        # =========================================================================
        # TEST 6: Verify market_validations table
        # =========================================================================
        logger.info("\n" + "=" * 70)
        logger.info("TEST 6: Verify market_validations table")
        logger.info("=" * 70)

        response = (
            supabase_client.table("market_validations")
            .select("*")
            .eq("opportunity_id", opportunity_id)
            .execute()
        )

        if response.data and len(response.data) > 0:
            record = response.data[0]
            logger.info(f"[PASS] TEST 6: market_validations has {len(response.data)} record(s)")
            logger.info(f"  - validation_type: {record.get('validation_type')}")
            logger.info(f"  - confidence_level: {record.get('confidence_level')}")
            evidence = record.get('evidence')
            if evidence:
                evidence_preview = str(evidence)[:100] if isinstance(evidence, (str, dict)) else str(evidence)[:100]
                logger.info(f"  - evidence: {evidence_preview}...")
            test_results["passed"] += 1
            test_results["details"].append({
                "test": "TEST 6: market_validations table",
                "status": "PASS",
                "details": f"Record found with confidence_level={record.get('confidence_level')}",
            })
        else:
            logger.error("[FAIL] TEST 6: market_validations table is empty")
            test_results["failed"] += 1
            test_results["details"].append({
                "test": "TEST 6: market_validations table",
                "status": "FAIL",
                "details": "No record found",
            })

        # =========================================================================
        # TEST 7: Verify competitive_landscape table
        # =========================================================================
        logger.info("\n" + "=" * 70)
        logger.info("TEST 7: Verify competitive_landscape table")
        logger.info("=" * 70)

        response = (
            supabase_client.table("competitive_landscape")
            .select("*")
            .eq("opportunity_id", opportunity_id)
            .execute()
        )

        if response.data and len(response.data) > 0:
            logger.info(f"[PASS] TEST 7: competitive_landscape has {len(response.data)} record(s)")
            for i, record in enumerate(response.data):
                logger.info(f"  - Competitor {i + 1}: {record.get('competitor_name')}")
            test_results["passed"] += 1
            test_results["details"].append({
                "test": "TEST 7: competitive_landscape table",
                "status": "PASS",
                "details": f"Found {len(response.data)} competitor records",
            })
        else:
            logger.error("[FAIL] TEST 7: competitive_landscape table is empty")
            test_results["failed"] += 1
            test_results["details"].append({
                "test": "TEST 7: competitive_landscape table",
                "status": "FAIL",
                "details": "No records found",
            })

        # =========================================================================
        # TEST 8: Verify _get_or_create_opportunity_id returns None on failure
        # =========================================================================
        logger.info("\n" + "=" * 70)
        logger.info("TEST 8: Verify _get_or_create_opportunity_id returns None on failure")
        logger.info("=" * 70)

        # Test with empty submission_id
        result = enhanced_store._get_or_create_opportunity_id({})
        if result is None:
            logger.info("[PASS] TEST 8: _get_or_create_opportunity_id returns None for empty submission")
            test_results["passed"] += 1
            test_results["details"].append({
                "test": "TEST 8: Error handling for empty submission",
                "status": "PASS",
                "details": "Returns None for empty submission_id",
            })
        else:
            logger.error(f"[FAIL] TEST 8: Expected None, got {result}")
            test_results["failed"] += 1
            test_results["details"].append({
                "test": "TEST 8: Error handling for empty submission",
                "status": "FAIL",
                "details": f"Expected None, got {result}",
            })

        # =========================================================================
        # TEST 9: Verify enhanced statistics include enrichment data
        # =========================================================================
        logger.info("\n" + "=" * 70)
        logger.info("TEST 9: Verify enhanced statistics")
        logger.info("=" * 70)

        stats = enhanced_store.get_enhanced_statistics()
        logger.info(f"Enhanced statistics: {json.dumps(stats, indent=2, default=str)}")

        if "enhancement_version" in stats:
            logger.info("[PASS] TEST 9: Enhanced statistics include enrichment info")
            test_results["passed"] += 1
            test_results["details"].append({
                "test": "TEST 9: Enhanced statistics",
                "status": "PASS",
                "details": f"enhancement_version={stats.get('enhancement_version')}",
            })
        else:
            logger.error("[FAIL] TEST 9: Enhanced statistics missing enrichment info")
            test_results["failed"] += 1
            test_results["details"].append({
                "test": "TEST 9: Enhanced statistics",
                "status": "FAIL",
                "details": "Missing enhancement_version in stats",
            })

        # =========================================================================
        # TEST 10: Verify idempotency - calling again should find existing opportunity
        # =========================================================================
        logger.info("\n" + "=" * 70)
        logger.info("TEST 10: Verify idempotency - should find existing opportunity")
        logger.info("=" * 70)

        # Call _get_or_create_opportunity_id again with same submission
        second_opportunity_id = enhanced_store._get_or_create_opportunity_id(test_submission)

        if second_opportunity_id == opportunity_id:
            logger.info(f"[PASS] TEST 10: Idempotency verified - returned same opportunity_id")
            test_results["passed"] += 1
            test_results["details"].append({
                "test": "TEST 10: Idempotency",
                "status": "PASS",
                "details": f"Same opportunity_id={opportunity_id} returned on second call",
            })
        else:
            logger.error(f"[FAIL] TEST 10: Different opportunity_id returned: {second_opportunity_id} vs {opportunity_id}")
            test_results["failed"] += 1
            test_results["details"].append({
                "test": "TEST 10: Idempotency",
                "status": "FAIL",
                "details": f"Got {second_opportunity_id} instead of {opportunity_id}",
            })

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        test_results["failed"] += 1
        test_results["details"].append({
            "test": "Test Execution",
            "status": "ERROR",
            "details": str(e),
        })

    finally:
        # Cleanup test data
        logger.info("\n" + "=" * 70)
        logger.info("CLEANUP: Removing test data")
        logger.info("=" * 70)
        cleanup_test_data(supabase_client, test_submission_id, opportunity_id)

    # =========================================================================
    # SUMMARY
    # =========================================================================
    logger.info("\n" + "=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Passed: {test_results['passed']}")
    logger.info(f"Failed: {test_results['failed']}")
    logger.info(f"Total:  {test_results['passed'] + test_results['failed']}")
    logger.info("")

    for detail in test_results["details"]:
        status_icon = "[PASS]" if detail["status"] == "PASS" else "[FAIL]"
        logger.info(f"{status_icon} {detail['test']}: {detail['details']}")

    # Overall result
    if test_results["failed"] == 0:
        logger.info("\n[SUCCESS] All tests passed! The EnhancedHybridStore fix is working correctly.")
        return True
    else:
        logger.error(f"\n[FAILURE] {test_results['failed']} test(s) failed. Please review the fix.")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
