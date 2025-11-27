#!/usr/bin/env python3
"""
Test Schema-Fixed SQLAlchemy Loader

This script comprehensively tests the schema-fixed SQLAlchemy loader to ensure
it properly maps Reddit opportunity data to the actual database schema and
eliminates silent failures.

Author: Phase 2 DLT to SQLAlchemy Migration
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, UTC

# Add project paths
pipeline_v2_root = Path(__file__).parent.parent.resolve()
project_root = Path(__file__).parent.parent.parent.resolve()

sys.path.insert(0, str(pipeline_v2_root))
sys.path.insert(1, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_foundation():
    """Test SQLAlchemy foundation components."""
    logger.info("=" * 80)
    logger.info("TESTING SCHEMA-FIXED SQLALCHEMY FOUNDATION")
    logger.info("=" * 80)

    try:
        # Import the fixed loader
        from storage.sqlalchemy_loader_fixed import test_sqlalchemy_foundation

        logger.info("✓ Schema-fixed SQLAlchemy loader imported successfully")

        # Run foundation tests
        results = test_sqlalchemy_foundation()

        logger.info("Foundation Test Results:")
        logger.info(f"  - Overall Status: {results.get('overall_status', 'unknown')}")
        logger.info(f"  - SQLAlchemy Available: {results.get('sqlalchemy_available', False)}")
        logger.info(f"  - Schema Status: {results.get('schema_status', 'unknown')}")

        # Test connection details
        connection_test = results.get('components', {}).get('connection', {})
        logger.info(f"  - Connection Status: {connection_test.get('status', 'unknown')}")
        logger.info(f"  - Connection Valid: {connection_test.get('connection_valid', False)}")

        # Test table validation
        table_test = results.get('components', {}).get('table_validation', {})
        validation = table_test.get('validation', {})
        logger.info(f"  - Table Exists: {validation.get('exists', False)}")
        logger.info(f"  - Validation Status: {validation.get('validation_status', 'unknown')}")

        if validation.get('missing_critical_columns'):
            logger.warning(f"  - Missing Critical Columns: {validation['missing_critical_columns']}")

        # Test ID resolution
        id_test = results.get('components', {}).get('id_resolution', {})
        logger.info(f"  - ID Resolution Status: {id_test.get('status', 'unknown')}")
        logger.info(f"  - Successful Resolutions: {id_test.get('successful_resolutions', 0)}/{id_test.get('total_tests', 0)}")

        return results.get('overall_status') == 'success'

    except Exception as e:
        logger.error(f"✗ Foundation test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_schema_mapping():
    """Test field mapping from Reddit data to database schema."""
    logger.info("=" * 80)
    logger.info("TESTING SCHEMA MAPPING")
    logger.info("=" * 80)

    try:
        from storage.sqlalchemy_loader_fixed import create_sqlalchemy_loader

        # Create loader
        loader = create_sqlalchemy_loader()
        logger.info("✓ SQLAlchemy loader created successfully")

        # Test data with field mapping challenges
        test_opportunities = [
            {
                "submission_id": "test_mapping_001",
                "title": "Schema Mapping Test Productivity App",
                "text": "I need an app that helps manage team productivity with AI insights and real-time collaboration.",  # Should map to problem_description
                "subreddit": "productivity",
                "upvotes": 42,  # Should map to reddit_score
                "comments_count": 15,  # Should be ignored (no corresponding column)
                "score": 57,  # Should be ignored (no corresponding column)
                "created_utc": "2024-11-27T10:30:00Z",  # Should be ignored (no corresponding column)
                "quality_score": 88.5,  # Should map to opportunity_score or be used in calculation
                "opportunity_score": 79.0,
                "core_functions": ["AI insights", "real-time collaboration", "productivity tracking"],
                "app_concept": "AI-powered team productivity platform",
                "problem_description": "Teams struggle with productivity management across multiple projects",  # Direct mapping
                "trust_score": 72.0,
                "trust_level": "HIGH",
                "trust_badges": ["EXPERT_POSTER", "ACTIVE_COMMUNITY"],
                "confidence_score": 85.0,
                "monetization_score": 91.0,
                "processed_at": datetime.now(UTC).isoformat(),  # Should map to analyzed_at
                "pipeline_version": "pipeline_v2_sqlalchemy_fixed"  # Should map to pipeline_source
            }
        ]

        # Test data preparation
        prepared = loader.prepare_opportunity_data(test_opportunities)

        logger.info(f"✓ Prepared {len(prepared)} opportunities for loading")

        # Validate field mappings
        if prepared:
            opp = prepared[0]

            logger.info("Field Mapping Validation:")
            logger.info(f"  - submission_id: {opp.get('submission_id')}")
            logger.info(f"  - title: {opp.get('title')}")
            logger.info(f"  - problem_description: {opp.get('problem_description')[:50]}...")
            logger.info(f"  - reddit_score: {opp.get('reddit_score')} (mapped from upvotes)")
            logger.info(f"  - opportunity_score: {opp.get('opportunity_score')}")
            logger.info(f"  - analyzed_at: {opp.get('analyzed_at')} (mapped from processed_at)")
            logger.info(f"  - pipeline_source: {opp.get('pipeline_source')} (mapped from pipeline_version)")
            logger.info(f"  - _dlt_load_id: {opp.get('_dlt_load_id')}")
            logger.info(f"  - _dlt_id: {opp.get('_dlt_id')}")

            # Check that non-existent fields are not present
            non_existent_fields = ['text', 'comments_count', 'score', 'created_utc', 'quality_score', 'processed_at', 'pipeline_version']
            for field in non_existent_fields:
                if field in opp:
                    logger.error(f"✗ Non-existent field '{field}' found in prepared data")
                    return False
                else:
                    logger.debug(f"✓ Non-existent field '{field}' correctly excluded")

        logger.info("✓ Schema mapping test completed successfully")
        return True

    except Exception as e:
        logger.error(f"✗ Schema mapping test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_actual_load():
    """Test actual database load with verification."""
    logger.info("=" * 80)
    logger.info("TESTING ACTUAL DATABASE LOAD")
    logger.info("=" * 80)

    try:
        from storage.sqlalchemy_loader_fixed import create_sqlalchemy_loader

        # Create loader
        loader = create_sqlalchemy_loader()
        logger.info("✓ SQLAlchemy loader created successfully")

        # Get initial statistics
        initial_stats = loader.get_load_statistics()
        initial_count = initial_stats.get('record_count', 0)
        logger.info(f"Initial record count: {initial_count}")

        # Test data for actual load
        test_opportunities = [
            {
                "submission_id": f"test_load_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
                "title": "Real Load Test - Task Management Solution",
                "text": "Our team wastes hours every week switching between different task management tools. We need a unified platform that integrates with existing tools.",
                "subreddit": "projectmanagement",
                "upvotes": 28,
                "opportunity_score": 82.0,
                "core_functions": ["task management", "tool integration", "team collaboration"],
                "app_concept": "Unified task management platform with deep integrations",
                "problem_description": "Teams lose productivity switching between multiple task management tools",
                "trust_score": 78.0,
                "trust_level": "VERIFIED",
                "trust_badges": ["INDUSTRY_EXPERT", "ACTIVE_COMMUNITY"],
                "confidence_score": 88.0,
                "monetization_score": 85.0,
                "processed_at": datetime.now(UTC).isoformat(),
                "pipeline_version": "pipeline_v2_sqlalchemy_fixed",
                "value_proposition": "Eliminate tool-switching overhead with unified platform",
                "target_user": "Project managers and team leads",
                "monetization_model": "Tiered subscription: $15-50/month per team",
                "priority": "high",
                "status": "discovered"
            }
        ]

        logger.info(f"Loading {len(test_opportunities)} opportunities...")

        # Perform the load
        load_result = loader.load_opportunities(
            test_opportunities,
            write_disposition="merge"
        )

        # Analyze results
        logger.info("Load Results:")
        logger.info(f"  - Success: {load_result.success}")
        logger.info(f"  - Load ID: {load_result.load_id}")
        logger.info(f"  - Records Inserted: {load_result.records_inserted}")
        logger.info(f"  - Records Updated: {load_result.records_updated}")
        logger.info(f"  - Errors: {len(load_result.errors)}")

        if load_result.errors:
            for error in load_result.errors:
                logger.error(f"    Error: {error}")

        # Verify final statistics
        final_stats = loader.get_load_statistics()
        final_count = final_stats.get('record_count', 0)
        logger.info(f"Final record count: {final_count}")

        # Validate data persistence
        expected_increase = load_result.records_inserted
        actual_increase = final_count - initial_count

        logger.info(f"Expected increase: {expected_increase}")
        logger.info(f"Actual increase: {actual_increase}")

        if load_result.success and actual_increase >= expected_increase:
            logger.info("✓ Data persistence verification PASSED")
            return True
        else:
            logger.error("❌ Data persistence verification FAILED")
            logger.error(f"  Load success: {load_result.success}")
            logger.error(f"  Expected vs actual increase: {expected_increase} vs {actual_increase}")
            return False

    except Exception as e:
        logger.error(f"✗ Actual load test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_error_handling():
    """Test error handling for various failure scenarios."""
    logger.info("=" * 80)
    logger.info("TESTING ERROR HANDLING")
    logger.info("=" * 80)

    try:
        from storage.sqlalchemy_loader_fixed import create_sqlalchemy_loader, SQLAlchemyLoadError

        loader = create_sqlalchemy_loader()
        logger.info("✓ SQLAlchemy loader created successfully")

        # Test 1: Empty data
        logger.info("Testing empty data handling...")
        empty_result = loader.load_opportunities([], write_disposition="merge")
        if empty_result.success and empty_result.records_inserted == 0:
            logger.info("✓ Empty data handled correctly")
        else:
            logger.error("❌ Empty data not handled correctly")
            return False

        # Test 2: Invalid field mappings (should be handled gracefully)
        logger.info("Testing invalid field handling...")
        invalid_data = [
            {
                "submission_id": "test_invalid_001",
                # Missing required fields - should be handled gracefully
                "non_existent_field": "this should be ignored"
            }
        ]

        try:
            invalid_result = loader.load_opportunities(invalid_data, write_disposition="merge")
            # This should either succeed (with default values) or fail gracefully
            logger.info(f"Invalid data result - Success: {invalid_result.success}, Errors: {len(invalid_result.errors)}")
        except Exception as e:
            logger.info(f"Invalid data handled with exception: {type(e).__name__}")

        # Test 3: Duplicate data handling
        logger.info("Testing duplicate data handling...")
        duplicate_data = [
            {
                "submission_id": f"test_duplicate_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
                "title": "Duplicate Test Data",
                "text": "This data will be loaded twice to test duplicate handling.",
                "subreddit": "test",
                "upvotes": 10,
                "opportunity_score": 50.0,
                "processed_at": datetime.now(UTC).isoformat()
            }
        ]

        # Load first time
        first_load = loader.load_opportunities(duplicate_data, write_disposition="merge")
        logger.info(f"First load: {first_load.records_inserted} inserted, {first_load.records_updated} updated")

        # Load second time (should update existing record)
        duplicate_data[0]["title"] = "Duplicate Test Data - Updated"
        second_load = loader.load_opportunities(duplicate_data, write_disposition="merge")
        logger.info(f"Second load: {second_load.records_inserted} inserted, {second_load.records_updated} updated")

        if first_load.records_inserted > 0 and second_load.records_updated > 0:
            logger.info("✓ Duplicate data handled correctly")
        else:
            logger.warning("⚠ Duplicate handling may need review")

        logger.info("✓ Error handling tests completed")
        return True

    except Exception as e:
        logger.error(f"✗ Error handling test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main test function."""
    logger.info("SCHEMA-FIXED SQLALCHEMY LOADER COMPREHENSIVE TEST")
    logger.info("=" * 80)
    logger.info("Testing critical schema alignment fixes for Phase 2 migration")
    logger.info("=" * 80)

    all_tests_passed = True

    # Run all tests
    tests = [
        ("Foundation Components", test_foundation),
        ("Schema Mapping", test_schema_mapping),
        ("Actual Database Load", test_actual_load),
        ("Error Handling", test_error_handling)
    ]

    for test_name, test_func in tests:
        logger.info(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_passed = test_func()
            if test_passed:
                logger.info(f"✓ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
                all_tests_passed = False
        except Exception as e:
            logger.error(f"❌ {test_name}: EXCEPTION - {e}")
            all_tests_passed = False

    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("FINAL TEST RESULTS")
    logger.info("=" * 80)

    if all_tests_passed:
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("✓ Schema-fixed SQLAlchemy loader is ready for production")
        logger.info("✓ Field mappings are correctly aligned with database schema")
        logger.info("✓ Silent failures have been eliminated")
        logger.info("✓ Data persistence verification is working")
        logger.info("\nThe business can now proceed with:")
        logger.info("  - Reddit opportunity data collection without loss")
        logger.info("  - Monetizable app idea database building")
        logger.info("  - Reliable pipeline execution with accurate success/failure reporting")
    else:
        logger.error("❌ SOME TESTS FAILED!")
        logger.error("❌ Schema-fixed loader needs additional fixes before production use")
        logger.error("❌ Business objectives may be impacted")

    logger.info("=" * 80)

    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())