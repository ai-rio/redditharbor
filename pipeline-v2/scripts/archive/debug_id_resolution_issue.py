#!/usr/bin/env python3
"""
Debug script to verify the ID resolution issue in test_no_data_corruption

The issue: ID resolution converts submission_id to UUID, but test queries original ID
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, '/home/carlos/projects/redditharbor-core-functions-fix/.venv/lib/python3.12/site-packages')

import logging
import time
from datetime import datetime, UTC

# Import the loader
from storage.sqlalchemy_loader import SQLAlchemyLoader
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_id_resolution_mapping():
    """
    Debug the ID resolution mapping to understand the conversion issue
    """
    print("=== DEBUGGING ID RESOLUTION MAPPING ===")

    # Create loader
    loader = SQLAlchemyLoader('postgresql://postgres:postgres@127.0.0.1:54322/postgres')

    # Generate test data
    timestamp = int(time.time() * 1000000)
    original_submission_id = f'debug_id_resolution_{timestamp}'
    test_data = [
        {
            'submission_id': original_submission_id,
            'title': 'ID Resolution Debug Test',
            'subreddit': 'id_resolution_debug',
            'upvotes': 999,
            'text': 'ID resolution debug marker: ID_RESOLUTION_DEBUG_123',
            'trust_score': 99.0,
            'opportunity_score': 99.0,
            'trust_level': 'HIGH',
            'trust_badges': ['ID', 'RESOLUTION', 'DEBUG'],
            'processed_at': '2024-11-27T16:00:00Z',
            'pipeline_version': 'id_resolution_debug_v1.0'
        }
    ]

    print(f"Original submission_id: {original_submission_id}")
    print(f"Test data: {test_data}")

    # Step 1: Load data and capture ID resolution
    print("\n=== STEP 1: LOADING DATA WITH ID RESOLUTION TRACKING ===")

    # Import ID resolver to track the mapping
    try:
        from core.utils.id_resolver import resolve_submission_id
        ID_RESOLVER_AVAILABLE = True
    except ImportError:
        print("❌ ID resolver not available")
        return False

    # Manually resolve the ID to see what it becomes
    if ID_RESOLVER_AVAILABLE:
        resolved = resolve_submission_id(original_submission_id)
        print(f"Resolved submission_id: {resolved.uuid if resolved else 'None'}")
        print(f"Resolution source: {resolved.source if resolved else 'None'}")
        resolved_uuid = resolved.uuid if resolved else original_submission_id
    else:
        resolved_uuid = original_submission_id

    # Load data
    result = loader.load_opportunities(
        opportunities=test_data,
        write_disposition="merge"
    )

    print(f"Load result: success={result.success}, inserted={result.records_inserted}")
    assert result.success is True, "Load must succeed"

    # Step 2: Check what was actually stored
    print("\n=== STEP 2: CHECKING STORED DATA ===")
    with loader.get_session() as session:
        # Query by original ID (should fail)
        original_result = session.execute(
            text("SELECT title, subreddit FROM app_opportunities WHERE submission_id = :submission_id"),
            {"submission_id": original_submission_id}
        ).fetchone()

        print(f"Query by original ID ({original_submission_id}): {original_result}")

        # Query by resolved UUID (should succeed)
        resolved_result = session.execute(
            text("SELECT title, subreddit FROM app_opportunities WHERE submission_id = :submission_id"),
            {"submission_id": resolved_uuid}
        ).fetchone()

        print(f"Query by resolved UUID ({resolved_uuid}): {resolved_result}")

        if original_result is None and resolved_result is not None:
            print("✅ ISSUE CONFIRMED: Data is stored under UUID, not original ID")
            print(f"   Original ID: {original_submission_id}")
            print(f"   Stored as UUID: {resolved_uuid}")
            print(f"   Found record: {resolved_result.title}")
            return True
        elif original_result is not None:
            print("✅ Data found under original ID - no ID resolution issue")
            return False
        else:
            print("❌ Data not found anywhere")
            return False

def test_fixed_verification_approach():
    """
    Test a fixed verification approach that accounts for ID resolution
    """
    print("\n\n=== TESTING FIXED VERIFICATION APPROACH ===")

    # Create loader
    loader = SQLAlchemyLoader('postgresql://postgres:postgres@127.0.0.1:54322/postgres')

    # Generate test data
    timestamp = int(time.time() * 1000000)
    original_submission_id = f'debug_fixed_verification_{timestamp}'
    test_data = [
        {
            'submission_id': original_submission_id,
            'title': 'Fixed Verification Test',
            'subreddit': 'fixed_verification',
            'upvotes': 777,
            'text': 'Fixed verification debug marker: FIXED_VERIFICATION_456',
            'trust_score': 88.5,
            'opportunity_score': 92.5,
            'trust_level': 'HIGH',
            'trust_badges': ['FIXED', 'VERIFICATION'],
            'processed_at': '2024-11-27T16:30:00Z',
            'pipeline_version': 'fixed_verification_v1.0'
        }
    ]

    print(f"Original submission_id: {original_submission_id}")

    # Resolve ID first
    try:
        from core.utils.id_resolver import resolve_submission_id
        ID_RESOLVER_AVAILABLE = True
        resolved = resolve_submission_id(original_submission_id)
        resolved_uuid = resolved.uuid if resolved else original_submission_id
        print(f"Resolved submission_id to: {resolved_uuid}")
    except ImportError:
        ID_RESOLVER_AVAILABLE = False
        resolved_uuid = original_submission_id
        print("Using original submission_id (no resolver)")

    # Load data
    result = loader.load_opportunities(
        opportunities=test_data,
        write_disposition="merge"
    )

    print(f"Load result: success={result.success}, inserted={result.records_inserted}")
    assert result.success is True, "Load must succeed"

    # Step 3: Verify using the CORRECT submission_id (resolved UUID)
    print("\n=== STEP 3: VERIFYING WITH CORRECT SUBMISSION_ID ===")
    try:
        with loader.get_session() as session:
            # Query using the resolved UUID (the key insight!)
            query_result = session.execute(
                text("""
                    SELECT title, subreddit, reddit_score, problem_description,
                           trust_score, opportunity_score, trust_level,
                           trust_badges, pipeline_source
                    FROM app_opportunities
                    WHERE submission_id = :submission_id
                """),
                {"submission_id": resolved_uuid}  # Use resolved UUID, not original
            ).fetchone()

            print(f"Query result (correct ID): {query_result}")

            assert query_result is not None, f"Record should be found in database with resolved ID {resolved_uuid}"
            print("✅ Record found with resolved UUID")

            # Verify specific fields
            assert query_result.title == 'Fixed Verification Test', f"Title should match, got: {query_result.title}"
            assert query_result.subreddit == 'fixed_verification', f"Subreddit should match, got: {query_result.subreddit}"
            assert query_result.reddit_score == 777, f"Reddit score should match, got: {query_result.reddit_score}"
            assert 'FIXED_VERIFICATION_456' in query_result.problem_description, f"Text should contain marker, got: {query_result.problem_description}"
            assert query_result.trust_score == 88.5, f"Trust score should match, got: {query_result.trust_score}"
            assert query_result.opportunity_score == 92.5, f"Opportunity score should match, got: {query_result.opportunity_score}"
            assert query_result.trust_level == 'HIGH', f"Trust level should match, got: {query_result.trust_level}"

            print("✅ All data corruption checks passed")
            return True

    except Exception as e:
        print(f"❌ Fixed verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Debugging ID resolution issue in test_no_data_corruption")

    # Test 1: Confirm ID resolution issue
    id_issue_confirmed = debug_id_resolution_mapping()

    # Test 2: Test fixed verification approach
    fixed_approach_works = test_fixed_verification_approach()

    print("\n" + "="*80)
    print("📊 ID RESOLUTION DEBUG RESULTS")
    print("="*80)
    print(f"ID resolution issue confirmed: {'YES' if id_issue_confirmed else 'NO'}")
    print(f"Fixed verification approach: {'WORKS' if fixed_approach_works else 'FAILED'}")

    if id_issue_confirmed and fixed_approach_works:
        print("\n🎯 ROOT CAUSE IDENTIFIED:")
        print("The test_no_data_corruption failure is caused by ID resolution!")
        print("")
        print("📋 WHAT HAPPENS:")
        print("1. Test data uses original submission_id (e.g., 'corruption_test_123456789')")
        print("2. ID resolver converts it to UUID (e.g., '5db16ee6-6fdf-5846-ac0e-d68687d3219b')")
        print("3. Data is stored in database under the UUID")
        print("4. Test queries for the original submission_id")
        print("5. Query returns None because original ID doesn't exist in database")
        print("6. Assertion fails, causing test failure")
        print("")
        print("💡 SOLUTION:")
        print("Option 1: Query using the resolved UUID instead of original submission_id")
        print("Option 2: Store both original ID and resolved UUID for verification")
        print("Option 3: Disable ID resolution in tests to preserve original IDs")
        print("")
        print("🔧 IMMEDIATE FIX:")
        print("Modify test to resolve submission_id before querying database")
    else:
        print("\n❌ ID resolution is not the issue or fix didn't work")