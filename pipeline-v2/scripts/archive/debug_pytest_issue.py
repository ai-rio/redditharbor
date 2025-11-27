#!/usr/bin/env python3
"""
Debug script to investigate pytest vs standalone execution differences
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

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_no_data_corruption_debug():
    """
    Reproduce the test_no_data_corruption test exactly
    """
    print("=== DEBUGGING NO DATA CORRUPTION TEST ===")

    # Create loader (same as pytest fixture)
    loader = SQLAlchemyLoader('postgresql://postgres:postgres@127.0.0.1:54322/postgres')
    print(f"✅ Loader created: {loader}")

    # Test connection
    connection_ok = loader.validate_connection()
    print(f"✅ Database connection: {connection_ok}")

    # Generate test data with specific values (exact copy from test)
    timestamp = int(time.time() * 1000000)
    test_data = [
        {
            'submission_id': f'corruption_test_{timestamp}',
            'title': 'Corruption Test Title',
            'subreddit': 'corruption_test',
            'upvotes': 42,
            'text': 'Specific text for corruption detection: ABC123XYZ',
            'trust_score': 87.5,
            'opportunity_score': 92.3,
            'trust_level': 'HIGH',
            'trust_badges': ['BADGE1', 'BADGE2'],
            'processed_at': '2024-11-27T12:00:00Z',
            'pipeline_version': 'corruption_test_v1.0'
        }
    ]

    print(f"✅ Test data generated: {test_data}")

    # Load data (exact copy from test)
    result = loader.load_opportunities(
        opportunities=test_data,
        write_disposition="merge"
    )

    print(f"=== LOAD RESULT ===")
    print(f"Success: {result.success}")
    print(f"Records inserted: {result.records_inserted}")
    print(f"Records updated: {result.records_updated}")
    print(f"Error message: {result.error_message}")
    print(f"Load ID: {result.load_id}")

    # Verify success (same assertion as test)
    assert result.success is True, "Load must succeed"
    print("✅ Load success assertion passed")

    # Verify data integrity by querying database directly (exact copy from test)
    with loader.get_session() as session:
        from sqlalchemy import text

        print("=== DATABASE VERIFICATION ===")

        # Query the record we just inserted (exact query from test)
        query_result = session.execute(
            text("""
                SELECT title, subreddit, reddit_score, problem_description,
                       trust_score, opportunity_score, trust_level,
                       trust_badges, pipeline_source
                FROM app_opportunities
                WHERE submission_id = :submission_id
            """),
            {"submission_id": f"corruption_test_{timestamp}"}
        ).fetchone()

        print(f"Query result: {query_result}")

        if query_result is None:
            print("❌ RECORD NOT FOUND - This is the pytest failure!")
            return False

        # Verify specific fields weren't corrupted (same assertions as test)
        try:
            assert query_result.title == 'Corruption Test Title', f"Title should match, got: {query_result.title}"
            assert query_result.subreddit == 'corruption_test', f"Subreddit should match, got: {query_result.subreddit}"
            assert query_result.reddit_score == 42, f"Upvotes should match, got: {query_result.reddit_score}"
            assert 'ABC123XYZ' in query_result.problem_description, f"Text should contain marker, got: {query_result.problem_description}"
            assert query_result.trust_score == 87.5, f"Trust score should match, got: {query_result.trust_score}"
            assert query_result.opportunity_score == 92.3, f"Opportunity score should match, got: {query_result.opportunity_score}"
            assert query_result.trust_level == 'HIGH', f"Trust level should match, got: {query_result.trust_level}"

            print("✅ All data corruption checks passed")
            return True

        except AssertionError as e:
            print(f"❌ Data corruption check failed: {e}")
            return False

def test_duplicate_handling_debug():
    """
    Reproduce the test_duplicate_handling test exactly
    """
    print("\n\n=== DEBUGGING DUPLICATE HANDLING TEST ===")

    # Create loader
    loader = SQLAlchemyLoader('postgresql://postgres:postgres@127.0.0.1:54322/postgres')

    # Create test data with specific ID (exact copy from test)
    timestamp = int(time.time() * 1000000)
    submission_id = f"duplicate_test_{timestamp}"

    # First load
    first_data = [{
        'submission_id': submission_id,
        'title': 'Original Title',
        'subreddit': 'duplicate_test',
        'upvotes': 100,
        'text': 'Original text',
        'trust_score': 80.0,
        'processed_at': datetime.now(UTC).isoformat()
    }]

    first_result = loader.load_opportunities(
        opportunities=first_data,
        write_disposition="merge"
    )

    print(f"First load result: success={first_result.success}, inserted={first_result.records_inserted}")
    assert first_result.success is True, "First load should succeed"
    assert first_result.records_inserted == 1, "First load should insert 1 record"
    print("✅ First load assertions passed")

    # Second load with same ID (should update)
    second_data = [{
        'submission_id': submission_id,  # Same ID
        'title': 'Updated Title',  # Different title
        'subreddit': 'duplicate_test',
        'upvotes': 200,  # Different upvotes
        'text': 'Updated text',  # Different text
        'trust_score': 90.0,  # Different score
        'processed_at': datetime.now(UTC).isoformat()
    }]

    second_result = loader.load_opportunities(
        opportunities=second_data,
        write_disposition="merge"
    )

    print(f"Second load result: success={second_result.success}, inserted={second_result.records_inserted}, updated={second_result.records_updated}")
    assert second_result.success is True, "Second load should succeed"
    assert second_result.records_inserted == 0, "Second load should insert 0 records"
    assert second_result.records_updated == 1, "Second load should update 1 record"
    print("✅ Second load assertions passed")

    # Verify data was updated, not duplicated (exact copy from test)
    with loader.get_session() as session:
        from sqlalchemy import text

        print("=== DUPLICATE VERIFICATION ===")

        # Check total records for this submission ID
        count_result = session.execute(
            text("SELECT COUNT(*) FROM app_opportunities WHERE submission_id = :submission_id"),
            {"submission_id": submission_id}
        ).scalar()

        print(f"Record count for {submission_id}: {count_result}")
        assert count_result == 1, "Should have exactly 1 record, not duplicates"
        print("✅ No duplicates assertion passed")

        # Verify data was updated
        updated_record = session.execute(
            text("SELECT title, reddit_score, problem_description, trust_score FROM app_opportunities WHERE submission_id = :submission_id"),
            {"submission_id": submission_id}
        ).fetchone()

        print(f"Updated record: {updated_record}")
        assert updated_record.title == 'Updated Title', "Title should be updated"
        assert updated_record.reddit_score == 200, "Upvotes should be updated"
        assert 'Updated text' in updated_record.problem_description, "Text should be updated"
        assert updated_record.trust_score == 90.0, "Trust score should be updated"
        print("✅ Update verification passed")

        return True

if __name__ == "__main__":
    print("Testing to understand pytest vs standalone differences...")

    # Run corruption test
    corruption_ok = test_no_data_corruption_debug()

    # Run duplicate test
    duplicate_ok = test_duplicate_handling_debug()

    print("\n=== SUMMARY ===")
    print(f"No data corruption test: {'PASSED' if corruption_ok else 'FAILED'}")
    print(f"Duplicate handling test: {'PASSED' if duplicate_ok else 'FAILED'}")

    if corruption_ok and duplicate_ok:
        print("\n✅ All tests passed in standalone execution")
        print("🔍 The issue is likely in pytest environment isolation (transactions/sessions)")
    else:
        print("\n❌ Tests failed even in standalone execution")
        print("🔍 The issue is in the SQLAlchemy loader itself")