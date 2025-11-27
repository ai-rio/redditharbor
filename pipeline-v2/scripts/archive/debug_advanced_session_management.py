#!/usr/bin/env python3
"""
Advanced Debug Script for test_no_data_corruption Session Management Issue

This script isolates the exact problem with pytest vs standalone execution:
The issue is in SQLAlchemy session context manager exception handling.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, '/home/carlos/projects/redditharbor-core-functions-fix/.venv/lib/python3.12/site-packages')

import logging
import time
from datetime import datetime, UTC
from contextlib import contextmanager
from typing import Iterator

# Import the loader
from storage.sqlalchemy_loader import SQLAlchemyLoader
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@contextmanager
def manual_session_management(loader):
    """
    Manual session management without automatic rollback on assertion failures
    This mimics what SHOULD happen in the test
    """
    session = loader._session_factory()
    try:
        yield session
        session.commit()
    except AssertionError as e:
        # CRITICAL: Don't rollback on assertion failures - commit first to preserve data
        logger.info(f"Assertion failed but committing to preserve debug data: {e}")
        session.commit()
        raise  # Re-raise the original assertion
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()

def debug_pytest_session_behavior():
    """
    Debug the exact pytest session management behavior that causes the issue
    """
    print("=== DEBUGGING PYTEST SESSION BEHAVIOR ===")

    # Create loader
    loader = SQLAlchemyLoader('postgresql://postgres:postgres@127.0.0.1:54322/postgres')

    # Generate test data
    timestamp = int(time.time() * 1000000)
    test_data = [
        {
            'submission_id': f'debug_session_{timestamp}',
            'title': 'Debug Session Test',
            'subreddit': 'debug_session',
            'upvotes': 100,
            'text': 'Debug session test marker: XYZ789',
            'trust_score': 88.0,
            'opportunity_score': 93.0,
            'trust_level': 'HIGH',
            'trust_badges': ['DEBUG', 'SESSION'],
            'processed_at': '2024-11-27T15:00:00Z',
            'pipeline_version': 'debug_session_v1.0'
        }
    ]

    print(f"Test data: {test_data}")

    # Step 1: Load data successfully
    print("\n=== STEP 1: LOADING DATA ===")
    result = loader.load_opportunities(
        opportunities=test_data,
        write_disposition="merge"
    )

    print(f"Load result: success={result.success}, inserted={result.records_inserted}")
    assert result.success is True, "Load must succeed"

    # Step 2: Query using built-in session manager (like in pytest)
    print("\n=== STEP 2: QUERYING WITH BUILT-IN SESSION MANAGER ===")
    try:
        with loader.get_session() as session:
            query_result = session.execute(
                text("""
                    SELECT title, subreddit, reddit_score, problem_description,
                           trust_score, opportunity_score, trust_level,
                           trust_badges, pipeline_source
                    FROM app_opportunities
                    WHERE submission_id = :submission_id
                """),
                {"submission_id": f"debug_session_{timestamp}"}
            ).fetchone()

            print(f"Query result (built-in): {query_result}")

            # This assertion will cause the session to rollback
            assert query_result is not None, "Record should be found in database"
            print("✅ Built-in session query succeeded")

    except Exception as e:
        print(f"❌ Built-in session query failed: {e}")
        print(f"Exception type: {type(e)}")

        # Step 3: Check if data still exists after rollback
        print("\n=== STEP 3: CHECKING DATA AFTER ROLLBACK ===")
        with manual_session_management(loader) as session:
            count_result = session.execute(
                text("SELECT COUNT(*) FROM app_opportunities WHERE submission_id = :submission_id"),
                {"submission_id": f"debug_session_{timestamp}"}
            ).scalar()

            print(f"Record count after built-in session failure: {count_result}")
            if count_result == 0:
                print("❌ DATA WAS ROLLED BACK - This is the pytest issue!")
                return False
            else:
                print("✅ Data still exists")
                return True

def debug_manual_session_behavior():
    """
    Debug manual session management without automatic rollback
    """
    print("\n\n=== DEBUGGING MANUAL SESSION BEHAVIOR ===")

    # Create loader
    loader = SQLAlchemyLoader('postgresql://postgres:postgres@127.0.0.1:54322/postgres')

    # Generate test data
    timestamp = int(time.time() * 1000000)
    test_data = [
        {
            'submission_id': f'debug_manual_{timestamp}',
            'title': 'Debug Manual Test',
            'subreddit': 'debug_manual',
            'upvotes': 200,
            'text': 'Debug manual test marker: ABC456',
            'trust_score': 91.0,
            'opportunity_score': 95.0,
            'trust_level': 'HIGH',
            'trust_badges': ['DEBUG', 'MANUAL'],
            'processed_at': '2024-11-27T15:30:00Z',
            'pipeline_version': 'debug_manual_v1.0'
        }
    ]

    # Load data
    print("\n=== LOADING DATA ===")
    result = loader.load_opportunities(
        opportunities=test_data,
        write_disposition="merge"
    )

    print(f"Load result: success={result.success}, inserted={result.records_inserted}")
    assert result.success is True, "Load must succeed"

    # Query using manual session management
    print("\n=== QUERYING WITH MANUAL SESSION MANAGEMENT ===")
    try:
        with manual_session_management(loader) as session:
            query_result = session.execute(
                text("""
                    SELECT title, subreddit, reddit_score, problem_description,
                           trust_score, opportunity_score, trust_level,
                           trust_badges, pipeline_source
                    FROM app_opportunities
                    WHERE submission_id = :submission_id
                """),
                {"submission_id": f"debug_manual_{timestamp}"}
            ).fetchone()

            print(f"Query result (manual): {query_result}")

            assert query_result is not None, "Record should be found in database"
            print("✅ Manual session query succeeded")
            return True

    except Exception as e:
        print(f"❌ Manual session query failed: {e}")
        return False

def debug_isolated_transactions():
    """
    Debug completely isolated transactions to understand transaction boundaries
    """
    print("\n\n=== DEBUGGING ISOLATED TRANSACTIONS ===")

    # Create loader
    loader = SQLAlchemyLoader('postgresql://postgres:postgres@127.0.0.1:54322/postgres')

    # Generate test data
    timestamp = int(time.time() * 1000000)
    test_data = [
        {
            'submission_id': f'debug_isolated_{timestamp}',
            'title': 'Debug Isolated Test',
            'subreddit': 'debug_isolated',
            'upvotes': 300,
            'text': 'Debug isolated test marker: DEF123',
            'trust_score': 94.0,
            'opportunity_score': 97.0,
            'trust_level': 'HIGH',
            'trust_badges': ['DEBUG', 'ISOLATED'],
            'processed_at': '2024-11-27T16:00:00Z',
            'pipeline_version': 'debug_isolated_v1.0'
        }
    ]

    # Load data
    print("\n=== LOADING DATA ===")
    result = loader.load_opportunities(
        opportunities=test_data,
        write_disposition="merge"
    )

    print(f"Load result: success={result.success}, inserted={result.records_inserted}")

    # Check data immediately with a new connection
    print("\n=== CHECKING DATA WITH NEW CONNECTION ===")
    with loader._engine.connect() as conn:
        query_result = conn.execute(
            text("""
                SELECT title, subreddit, reddit_score, problem_description
                FROM app_opportunities
                WHERE submission_id = :submission_id
            """),
            {"submission_id": f"debug_isolated_{timestamp}"}
        ).fetchone()

        print(f"Query result (new connection): {query_result}")

        if query_result is None:
            print("❌ No data found with new connection")
            return False
        else:
            print("✅ Data found with new connection")

            # Now try with session context manager
            print("\n=== CHECKING DATA WITH SESSION CONTEXT MANAGER ===")
            try:
                with loader.get_session() as session:
                    session_result = session.execute(
                        text("""
                            SELECT title, subreddit, reddit_score, problem_description
                            FROM app_opportunities
                            WHERE submission_id = :submission_id
                        """),
                        {"submission_id": f"debug_isolated_{timestamp}"}
                    ).fetchone()

                    print(f"Query result (session): {session_result}")

                    if session_result is None:
                        print("❌ No data found with session")
                        return False
                    else:
                        print("✅ Data found with session")
                        return True

            except Exception as e:
                print(f"❌ Session query failed: {e}")
                return False

if __name__ == "__main__":
    print("🔍 Advanced debugging of SQLAlchemy session management in pytest")

    # Test 1: Pytest session behavior
    pytest_ok = debug_pytest_session_behavior()

    # Test 2: Manual session behavior
    manual_ok = debug_manual_session_behavior()

    # Test 3: Isolated transactions
    isolated_ok = debug_isolated_transactions()

    print("\n" + "="*80)
    print("📊 DEBUG RESULTS SUMMARY")
    print("="*80)
    print(f"Pytest session behavior:     {'PASSED' if pytest_ok else 'FAILED'}")
    print(f"Manual session behavior:     {'PASSED' if manual_ok else 'FAILED'}")
    print(f"Isolated transactions:       {'PASSED' if isolated_ok else 'FAILED'}")

    if not pytest_ok and (manual_ok or isolated_ok):
        print("\n🎯 ISSUE IDENTIFIED:")
        print("The problem is in the get_session() context manager exception handling.")
        print("When an assertion fails inside the session context, it triggers a rollback.")
        print("This rolls back the entire transaction, including the data that was loaded.")
        print("\n💡 SOLUTION:")
        print("1. Separate data loading and data verification into different transactions")
        print("2. Or modify session context manager to not rollback on assertion failures")
        print("3. Or use raw connections instead of sessions for verification")
    elif pytest_ok and manual_ok and isolated_ok:
        print("\n✅ All session management approaches work correctly")
        print("The issue may be intermittent or test-specific")
    else:
        print("\n❌ Deeper SQLAlchemy loader issue - all approaches failing")