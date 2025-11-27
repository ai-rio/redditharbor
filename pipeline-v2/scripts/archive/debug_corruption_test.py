#!/usr/bin/env python3
"""
Debug script for test_no_data_corruption failure
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

def debug_corruption_test():
    """Debug the corruption test failure"""
    print("=== DEBUGGING CORRUPTION TEST FAILURE ===")

    # Create loader
    loader = SQLAlchemyLoader('postgresql://postgres:postgres@127.0.0.1:54322/postgres')
    print(f"Loader created: {loader}")

    # Test connection
    connection_ok = loader.validate_connection()
    print(f"Database connection: {connection_ok}")

    # Generate test data with specific values (same as test)
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

    # Now verify data exactly like the test does
    print("\n=== VERIFYING DATA EXACTLY LIKE TEST ===")
    try:
        with loader.get_session() as session:
            from sqlalchemy import text

            # Query the record we just inserted
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

            if query_result:
                print(f"✅ Data found: {query_result}")
                print(f"Title: {query_result.title}")
                print(f"Subreddit: {query_result.subreddit}")
                print(f"Reddit score: {query_result.reddit_score}")
                print(f"Problem description: {query_result.problem_description}")
                print(f"Trust score: {query_result.trust_score}")
                print(f"Opportunity score: {query_result.opportunity_score}")
                print(f"Trust level: {query_result.trust_level}")
            else:
                print("❌ NO DATA FOUND - This is the test failure!")

                # Debug: Check if any records exist
                print("\n=== DEBUGGING: CHECK ALL RECORDS ===")
                all_records = session.execute(text("SELECT COUNT(*) FROM app_opportunities")).scalar()
                print(f"Total records in app_opportunities: {all_records}")

                # Check recent records
                recent_records = session.execute(
                    text("""
                        SELECT submission_id, title, created_at
                        FROM app_opportunities
                        ORDER BY created_at DESC
                        LIMIT 5
                    """)
                ).fetchall()
                print(f"Recent records: {recent_records}")

    except Exception as e:
        print(f"❌ Query failed: {e}")

if __name__ == "__main__":
    debug_corruption_test()