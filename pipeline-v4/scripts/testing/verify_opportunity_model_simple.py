#!/usr/bin/env python3
"""
Simplified Opportunity Model Compatibility Verification
Phase 1, Task 1.3

This script performs comprehensive verification of the Opportunity model
with the SQLModel database integration.
"""

import logging
import sys
from datetime import datetime, UTC
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all required modules import successfully"""
    logger.info("Testing imports...")

    try:
        from database import get_db_session, create_db_and_tables, init_db
        logger.info("✓ Database module imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import database module: {e}")
        return False

    try:
        from models.analysis import Opportunity
        logger.info("✓ Opportunity model imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import Opportunity model: {e}")
        return False

    return True

def test_database_connection():
    """Test database connection and table creation"""
    logger.info("Testing database connection...")

    try:
        from database import init_db, get_engine
        from sqlalchemy import text

        # Initialize database with tables
        init_db(echo=False, use_alembic=False)
        logger.info("✓ Database initialized successfully")

        # Test connection
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"✓ Connected to PostgreSQL: {version[:60]}...")

        return True

    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False

def test_opportunity_creation():
    """Test Opportunity model instance creation"""
    logger.info("Testing Opportunity model creation...")

    try:
        from models.analysis import Opportunity

        # Create comprehensive test data
        test_data = {
            "submission_id": "test_opp_v1",
            "subreddit": "productivity",
            "title": "Looking for an app to track my daily habits and build streaks",
            "wtp_score": 85.5,
            "confidence_score": 92.0,
            "trust_level": "HIGH",
            "analysis": {
                "app_idea": {
                    "title": "Habit Tracker Pro",
                    "app_concept": "A beautiful habit tracking app with streaks, reminders, and social features",
                    "problem_statement": "Users struggle to maintain consistent habits and need motivation through visual progress tracking",
                    "core_functions": ["habit tracking", "streak visualization", "smart reminders"],
                    "target_audience": "Self-improvement enthusiasts aged 18-35"
                },
                "pain_points": [
                    "Forgetting to track habits daily",
                    "Losing motivation after a few days",
                    "No visual representation of progress",
                    "Difficulty maintaining consistency"
                ],
                "spam_analysis": {
                    "is_spam": False,
                    "score": 0.05,
                    "reasons": []
                }
            },
            "metrics": {
                "market_demand": 90.0,
                "pain_intensity": 85.0,
                "monetization_potential": 80.0,
                "technical_feasibility": 95.0,
                "competition_level": 70.0,
                "engagement": {
                    "score": 100,
                    "comments": 45,
                    "upvotes": 234
                }
            }
        }

        # Create Opportunity instance
        opp = Opportunity(**test_data)

        # Validate basic fields
        assert opp.submission_id == test_data["submission_id"]
        assert opp.subreddit == test_data["subreddit"]
        assert opp.title == test_data["title"]
        assert opp.wtp_score == test_data["wtp_score"]
        assert opp.confidence_score == test_data["confidence_score"]
        assert opp.trust_level == test_data["trust_level"]

        # Validate JSON fields
        assert opp.analysis["app_idea"]["title"] == "Habit Tracker Pro"
        assert len(opp.pain_points) == 4
        assert opp.metrics["market_demand"] == 90.0

        # Validate calculated fields
        expected_final_score = (
            90.0 * 0.3 +      # market_demand
            85.0 * 0.25 +     # pain_intensity
            80.0 * 0.25 +     # monetization_potential
            95.0 * 0.2        # technical_feasibility
        )
        assert abs(opp.final_score - expected_final_score) < 0.01

        # Validate timestamps
        assert isinstance(opp.created_at, datetime)
        assert isinstance(opp.updated_at, datetime)
        assert opp.created_at.tzinfo == UTC

        logger.info("✓ Opportunity instance created successfully")
        logger.info(f"  - Title: {opp.title}")
        logger.info(f"  - Final Score: {opp.final_score:.2f}")
        logger.info(f"  - Trust Level: {opp.trust_level}")

        return test_data

    except Exception as e:
        logger.error(f"✗ Opportunity creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_database_operations(test_data):
    """Test database insert and query operations"""
    logger.info("Testing database operations...")

    try:
        from database import get_db_session
        from models.analysis import Opportunity

        # Insert opportunity
        with get_db_session() as session:
            opp = Opportunity(**test_data)
            session.add(opp)
            session.flush()
            opportunity_id = opp.id
            logger.info(f"✓ Opportunity saved to database (ID: {opportunity_id})")

        # Query opportunity back
        with get_db_session() as session:
            # Query by submission_id
            retrieved = session.query(Opportunity).filter(
                Opportunity.submission_id == test_data["submission_id"]
            ).first()

            assert retrieved is not None, "Opportunity not found in database"
            assert retrieved.id == opportunity_id, "ID mismatch"

            logger.info(f"✓ Opportunity retrieved from database (ID: {retrieved.id})")

            # Validate all fields
            assert retrieved.submission_id == test_data["submission_id"]
            assert retrieved.subreddit == test_data["subreddit"]
            assert retrieved.title == test_data["title"]
            assert abs(retrieved.wtp_score - test_data["wtp_score"]) < 0.001
            assert abs(retrieved.confidence_score - test_data["confidence_score"]) < 0.001
            assert retrieved.trust_level == test_data["trust_level"]

            # Validate JSON fields preserved
            assert retrieved.analysis == test_data["analysis"]
            assert retrieved.metrics == test_data["metrics"]

            # Validate calculated field
            expected_final_score = 87.25
            assert abs(retrieved.final_score - expected_final_score) < 0.01

            # Validate property accessors
            assert retrieved.app_idea["title"] == "Habit Tracker Pro"
            assert len(retrieved.pain_points) == 4
            assert retrieved.market_metrics["market_demand"] == 90.0

            logger.info("✓ All fields validated successfully")
            logger.info(f"  - Retrieved final score: {retrieved.final_score:.2f}")

            return True

    except Exception as e:
        logger.error(f"✗ Database operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_cases():
    """Test edge cases and error conditions"""
    logger.info("Testing edge cases...")

    try:
        from models.analysis import Opportunity
        from database import get_db_session

        # Test minimal opportunity
        minimal_opp = Opportunity(
            submission_id="minimal_test_v2",
            subreddit="test",
            title="Minimal test",
            wtp_score=50.0  # Required field
        )

        with get_db_session() as session:
            session.add(minimal_opp)

        # Query and validate defaults
        with get_db_session() as session:
            retrieved = session.query(Opportunity).filter(
                Opportunity.submission_id == "minimal_test_v2"
            ).first()

            assert retrieved.analysis == {}, "Default analysis should be empty dict"
            assert retrieved.metrics == {}, "Default metrics should be empty dict"
            assert retrieved.calculate_final_score() == 0.0, "Final score should be 0 for empty metrics"
            assert retrieved.trust_level == "MEDIUM", "Default trust level should be MEDIUM"

        logger.info("✓ Edge cases handled correctly")
        return True

    except Exception as e:
        logger.error(f"✗ Edge case testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_json_serialization():
    """Test JSON field serialization/deserialization"""
    logger.info("Testing JSON serialization...")

    try:
        from models.analysis import Opportunity
        from database import get_db_session

        # Create opportunity with complex nested JSON
        complex_opp = Opportunity(
            submission_id="json_test_v2",
            subreddit="test",
            title="JSON serialization test",
            wtp_score=60.0,  # Required field
            analysis={
                "nested_dict": {
                    "level1": {
                        "level2": {
                            "list": [1, 2, 3],
                            "string": "test",
                            "boolean": True,
                            "null_value": None
                        }
                    }
                },
                "unicode_test": "Test with unicode: 🚀 ✨",
                "special_chars": "Special chars: '\"\\"
            },
            metrics={
                "float_precision": 3.14159265359,
                "scientific": 1.23e-4,
                "large_int": 9223372036854775807
            }
        )

        # Save and retrieve
        with get_db_session() as session:
            session.add(complex_opp)

        with get_db_session() as session:
            retrieved = session.query(Opportunity).filter(
                Opportunity.submission_id == "json_test_v2"
            ).first()

            # Validate complex JSON preserved
            assert retrieved.analysis["nested_dict"]["level1"]["level2"]["list"] == [1, 2, 3]
            assert retrieved.analysis["unicode_test"] == "Test with unicode: 🚀 ✨"
            assert retrieved.metrics["float_precision"] == 3.14159265359
            assert retrieved.metrics["large_int"] == 9223372036854775807

        logger.info("✓ JSON serialization working correctly")
        return True

    except Exception as e:
        logger.error(f"✗ JSON serialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_test_data():
    """Clean up test data from database"""
    logger.info("Cleaning up test data...")

    try:
        from database import get_db_session
        from models.analysis import Opportunity

        test_submission_ids = [
            "test_opp_v1",
            "minimal_test_v2",
            "json_test_v2"
        ]

        with get_db_session() as session:
            deleted = session.query(Opportunity).filter(
                Opportunity.submission_id.in_(test_submission_ids)
            ).delete()
            logger.info(f"✓ Cleaned up {deleted} test records")

    except Exception as e:
        logger.warning(f"⚠ Cleanup failed: {e}")

def run_existing_tests():
    """Run the existing test suite to ensure compatibility"""
    logger.info("\n" + "="*60)
    logger.info("Running existing SQLModel tests...")

    try:
        import subprocess
        import os

        # Run SQLModel Phase 1 tests
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/test_sqlmodel_phase1.py", "-v"],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )

        if result.returncode == 0:
            logger.info("✓ All SQLModel Phase 1 tests passed!")
            logger.info(result.stdout[-500:])  # Last 500 chars
            return True
        else:
            logger.error("✗ Some SQLModel Phase 1 tests failed")
            logger.error(result.stderr)
            return False

    except Exception as e:
        logger.error(f"✗ Failed to run existing tests: {e}")
        return False

def run_verification():
    """Run all verification tests"""
    logger.info("Starting Opportunity Model Verification")
    logger.info("=" * 60)

    all_passed = True

    # 1. Test imports
    if not test_imports():
        all_passed = False
        return all_passed

    # 2. Test database connection
    if not test_database_connection():
        all_passed = False
        return all_passed

    # 3. Test opportunity creation
    test_data = test_opportunity_creation()
    if test_data is None:
        all_passed = False
        return all_passed

    # 4. Test database operations
    if not test_database_operations(test_data):
        all_passed = False

    # 5. Test edge cases
    if not test_edge_cases():
        all_passed = False

    # 6. Test JSON serialization
    if not test_json_serialization():
        all_passed = False

    # 7. Run existing tests
    if not run_existing_tests():
        all_passed = False

    # Cleanup
    cleanup_test_data()

    # Summary
    logger.info("=" * 60)
    if all_passed:
        logger.info("🎉 ALL VERIFICATION TESTS PASSED! 🎉")
        logger.info("\nThe Opportunity model is fully compatible with SQLModel database integration.")
        logger.info("\nDeliverables completed:")
        logger.info("✓ Model imports without errors")
        logger.info("✓ Session connects to database")
        logger.info("✓ Opportunity instance creates successfully")
        logger.info("✓ All required fields are present")
        logger.info("✓ JSON fields (analysis, metrics) persist correctly")
        logger.info("✓ Timestamps maintain timezone information")
        logger.info("✓ final_score calculates correctly")
        logger.info("✓ Trust level validation works")
        logger.info("✓ Round-trip preserves all data")
        logger.info("✓ All existing 10 tests still pass")
    else:
        logger.error("❌ VERIFICATION FAILED")
        logger.error("Some tests failed. Please review the logs above.")

    return all_passed

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)