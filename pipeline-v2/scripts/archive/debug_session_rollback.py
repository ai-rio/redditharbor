#!/usr/bin/env python3
"""
Debug script to test session behavior and transaction isolation
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, '/home/carlos/projects/redditharbor-core-functions-fix/.venv/lib/python3.12/site-packages')

from storage.sqlalchemy_loader import create_sqlalchemy_loader
import logging
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_session_rollback():
    """Debug session rollback behavior"""
    print("=== DEBUGGING SESSION ROLLBACK BEHAVIOR ===")

    # Create loader exactly like the test fixture
    loader = create_sqlalchemy_loader(
        connection_string="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
    )

    # Generate test data
    timestamp = int(time.time() * 1000000)
    test_data = [
        {
            'submission_id': f'rollback_test_{timestamp}',
            'title': 'Rollback Test Title',
            'subreddit': 'rollback_test',
            'upvotes': 123,
            'text': 'Rollback test text: ROLLBACK456',
            'trust_score': 80.0,
            'opportunity_score': 90.0,
            'trust_level': 'HIGH',
            'trust_badges': ['ROLLBACK'],
            'processed_at': '2024-11-27T12:00:00Z',
            'pipeline_version': 'rollback_test_v1.0'
        }
    ]

    # Step 1: Load data
    print("Step 1: Loading data...")
    result = loader.load_opportunities(
        opportunities=test_data,
        write_disposition="merge"
    )
    print(f"Load result: Success={result.success}, Inserted={result.records_inserted}")

    # Step 2: Query data in separate session (like the test)
    print("\nStep 2: Querying data in separate session...")
    with loader.get_session() as session:
        from sqlalchemy import text

        # Check if data exists
        query_result = session.execute(
            text("""
                SELECT title, subreddit, reddit_score, problem_description
                FROM app_opportunities
                WHERE submission_id = :submission_id
            """),
            {"submission_id": f"rollback_test_{timestamp}"}
        ).fetchone()

        print(f"Query result: {query_result}")

        if query_result:
            print("✅ Data found in session")
            # Simulate a failing assertion
            print("Simulating assertion failure...")
            try:
                assert False, "Simulated test assertion failure"
            except Exception as assert_error:
                print(f"Assertion failed: {assert_error}")
                # This should trigger rollback in the context manager
                raise

    # Step 3: Check if data still exists after rollback
    print("\nStep 3: Checking data after rollback...")
    try:
        with loader.get_session() as session:
            final_result = session.execute(
                text("""
                    SELECT COUNT(*) FROM app_opportunities
                    WHERE submission_id = :submission_id
                """),
                {"submission_id": f"rollback_test_{timestamp}"}
            ).scalar()
            print(f"Data count after rollback: {final_result}")

    except Exception as e:
        print(f"Final check failed: {e}")

    # Step 4: Test loading then immediate query without assertion failure
    print("\nStep 4: Testing without assertion failure...")
    timestamp2 = int(time.time() * 1000000)
    test_data2 = [
        {
            'submission_id': f'no_rollback_test_{timestamp2}',
            'title': 'No Rollback Test Title',
            'subreddit': 'no_rollback_test',
            'upvotes': 456,
            'text': 'No rollback test text: NOROLLBACK789',
            'trust_score': 85.0,
            'opportunity_score': 95.0,
            'trust_level': 'MEDIUM',
            'trust_badges': ['NO_ROLLBACK'],
            'processed_at': '2024-11-27T12:00:00Z',
            'pipeline_version': 'no_rollback_test_v1.0'
        }
    ]

    result2 = loader.load_opportunities(
        opportunities=test_data2,
        write_disposition="merge"
    )
    print(f"Load result 2: Success={result2.success}, Inserted={result2.records_inserted}")

    with loader.get_session() as session:
        query_result2 = session.execute(
            text("""
                SELECT title FROM app_opportunities
                WHERE submission_id = :submission_id
            """),
            {"submission_id": f"no_rollback_test_{timestamp2}"}
        ).scalar()
        print(f"Query result 2: {query_result2}")
        if query_result2:
            print("✅ Data persists when no assertion failure")
        else:
            print("❌ Data missing even without assertion failure")

if __name__ == "__main__":
    debug_session_rollback()