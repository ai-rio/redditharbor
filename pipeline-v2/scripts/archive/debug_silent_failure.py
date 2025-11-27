#!/usr/bin/env python3
"""
Debug script to reproduce silent failure issue
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, '/home/carlos/projects/redditharbor-core-functions-fix/.venv/lib/python3.12/site-packages')

from storage.sqlalchemy_loader import SQLAlchemyLoader
import logging
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_silent_failure():
    """Debug the silent failure pattern"""
    print("=== DEBUGGING SILENT FAILURE PATTERN ===")

    # Create loader
    loader = SQLAlchemyLoader('postgresql://postgres:postgres@127.0.0.1:54322/postgres')
    print(f"Loader created: {loader}")

    # Test connection
    connection_ok = loader.validate_connection()
    print(f"Database connection: {connection_ok}")

    # Create test data (same as failing test)
    timestamp = int(time.time() * 1000000)
    test_data = [
        {
            'submission_id': f'debug_test_{timestamp}',
            'title': 'Debug Test Title',
            'subreddit': 'debug_test',
            'upvotes': 42,
            'text': 'Specific text for debugging: DEBUG123',
            'trust_score': 87.5,
            'opportunity_score': 92.3,
            'trust_level': 'HIGH',
            'trust_badges': ['BADGE1', 'BADGE2'],
            'processed_at': '2024-11-27T12:00:00Z',
            'pipeline_version': 'debug_test_v1.0'
        }
    ]

    print(f"Test data: {test_data}")

    # Load data
    print("Loading data...")
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

    # Now verify data actually exists
    print("\n=== VERIFYING DATA PERSISTENCE ===")
    try:
        with loader.get_session() as session:
            from sqlalchemy import text

            # Query for the record
            query_result = session.execute(
                text("""
                    SELECT submission_id, title, subreddit
                    FROM app_opportunities
                    WHERE submission_id = :submission_id
                """),
                {"submission_id": f"debug_test_{timestamp}"}
            ).fetchone()

            if query_result:
                print(f"✅ Data found: {query_result}")
            else:
                print("❌ NO DATA FOUND - This is the silent failure!")

    except Exception as e:
        print(f"❌ Query failed: {e}")

if __name__ == "__main__":
    debug_silent_failure()