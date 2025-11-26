#!/usr/bin/env python3
"""
RED PHASE TEST VERIFICATION SCRIPT

This script verifies that all the failing tests for SQLAlchemy ORM integration
are failing for the correct reasons. This confirms we've successfully
implemented the RED phase of TDD for fixing the hardcoded schema issues.

Root Cause: DatabaseFetcher hardcoded for app_opportunities schema with
submission_id column, but submissions table uses UUID id column.
"""

import sys
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_import_failures():
    """Test that expected imports fail with correct errors."""
    print("🔥 TESTING IMPORT FAILURES (Expected)")
    print("=" * 50)

    # Test 1: core.db.models should fail
    try:
        from core.db.models import Submission
        print("❌ UNEXPECTED: core.db.models import succeeded (should fail)")
        return False
    except ModuleNotFoundError as e:
        print(f"✅ EXPECTED: core.db.models import failed: {e}")
    except ImportError as e:
        print(f"✅ EXPECTED: core.db.models import failed: {e}")

    # Test 2: core.db.session should fail
    try:
        from core.db.session import get_db_session
        print("❌ UNEXPECTED: core.db.session import succeeded (should fail)")
        return False
    except ModuleNotFoundError as e:
        print(f"✅ EXPECTED: core.db.session import failed: {e}")
    except ImportError as e:
        print(f"✅ EXPECTED: core.db.session import failed: {e}")

    print("\n✅ All import failures working as expected!\n")
    return True

def test_database_fetcher_issues():
    """Test that DatabaseFetcher has the hardcoded schema issues."""
    print("🚨 TESTING DATABASE FETCHER ISSUES")
    print("=" * 50)

    try:
        from core.fetchers.database_fetcher import DatabaseFetcher
        print("✅ DatabaseFetcher import successful")

        # Create instance
        mock_client = None
        fetcher = DatabaseFetcher(mock_client)

        # Check default table name
        if fetcher.table_name == "app_opportunities":
            print("🚨 CONFIRMED: Default table is app_opportunities (not submissions)")
        else:
            print(f"❌ UNEXPECTED: Default table is {fetcher.table_name}")
            return False

        # Check for hardcoded submission_id usage
        import inspect
        source = inspect.getsource(fetcher._fetch_limited)

        if 'submission_id' in source:
            print("🚨 CONFIRMED: Uses hardcoded 'submission_id' field")
        else:
            print("❌ UNEXPECTED: No 'submission_id' field found")
            return False

        if 'reddit_id' not in source:
            print("🚨 CONFIRMED: Missing 'reddit_id' field (should use this instead)")
        else:
            print("❌ UNEXPECTED: Found 'reddit_id' field (should be missing)")
            return False

        # Check for ORM support (should be missing)
        has_orm = hasattr(fetcher, 'use_orm')
        has_query = hasattr(fetcher, 'query_submissions')

        if not has_orm:
            print("✅ EXPECTED: No ORM support (use_orm missing)")
        else:
            print("❌ UNEXPECTED: Has ORM support (use_orm exists)")
            return False

        if not has_query:
            print("✅ EXPECTED: No ORM query methods (query_submissions missing)")
        else:
            print("❌ UNEXPECTED: Has ORM query methods (query_submissions exists)")
            return False

    except ImportError as e:
        print(f"❌ UNEXPECTED: DatabaseFetcher import failed: {e}")
        return False

    print("\n✅ All DatabaseFetcher issues confirmed!\n")
    return True

def test_pytest_collection_failure():
    """Test that pytest collection fails correctly."""
    print("🧪 TESTING PYTEST COLLECTION FAILURE")
    print("=" * 50)

    test_file = project_root / "tests" / "test_submissions_orm.py"
    if not test_file.exists():
        print("❌ UNEXPECTED: test_submissions_orm.py not found")
        return False

    print("✅ test_submissions_orm.py exists")

    # Try to collect tests (should fail due to import errors)
    try:
        import pytest
        print("✅ pytest import successful")

        # This will fail during collection due to import errors
        result = pytest.main([str(test_file), "--collect-only", "-q"])

        # pytest returns 1 or 2 for collection errors, which is expected
        if result in (1, 2):
            print("✅ EXPECTED: Pytest collection failed due to import errors")
        else:
            print(f"❌ UNEXPECTED: Pytest collection returned {result} (expected 1 or 2)")
            return False

    except ImportError:
        print("❌ UNEXPECTED: pytest import failed")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED: pytest collection error: {e}")
        return False

    print("\n✅ Pytest collection failure confirmed!\n")
    return True

def main():
    """Run all RED phase verification tests."""
    print("🔴 RED PHASE VERIFICATION")
    print("=" * 80)
    print("Verifying that SQLAlchemy ORM tests fail for the RIGHT reasons.")
    print("This confirms we're addressing the hardcoded schema issues properly.")
    print("=" * 80)
    print()

    success_count = 0
    total_tests = 3

    # Test import failures
    if test_import_failures():
        success_count += 1

    # Test DatabaseFetcher issues
    if test_database_fetcher_issues():
        success_count += 1

    # Test pytest collection failure
    if test_pytest_collection_failure():
        success_count += 1

    print("🎯 RED PHASE SUMMARY")
    print("=" * 50)
    print(f"Tests Verified: {success_count}/{total_tests}")

    if success_count == total_tests:
        print("✅ RED PHASE CONFIRMED!")
        print()
        print("🎯 READY FOR GREEN PHASE:")
        print("1. Create core/db/models.py with Submission SQLAlchemy model")
        print("2. Create core/db/session.py with database session management")
        print("3. Update DatabaseFetcher to use ORM instead of hardcoded queries")
        print("4. Fix schema mismatch: submission_id -> reddit_id, id -> UUID")
        print()
        print("🚧 ROOT CAUSE IDENTIFIED:")
        print("- DatabaseFetcher hardcoded for app_opportunities table")
        print("- Uses 'submission_id' field but submissions table has 'id' (UUID)")
        print("- Should use 'reddit_id' for Reddit submission IDs")
        print("- This is SAME issue that caused 5 days of DLT pain")
        return True
    else:
        print("❌ RED PHASE ISSUES FOUND!")
        print("Some tests passed unexpectedly - investigate setup.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)