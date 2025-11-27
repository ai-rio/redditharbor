#!/usr/bin/env python3
"""
Minimal pytest test without dependency mocking
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from storage.sqlalchemy_loader import SQLAlchemyLoader
import logging
import time
from datetime import datetime, UTC

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestMinimalPytest:
    """Minimal pytest test without mocking dependencies"""

    def test_no_data_corruption_pytest(self):
        """Test data corruption with pytest environment"""
        print("\n=== PYTEST NO DATA CORRUPTION TEST ===")

        # Create loader
        loader = SQLAlchemyLoader('postgresql://postgres:postgres@127.0.0.1:54322/postgres')

        # Generate test data with specific values (exact copy from failing test)
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

        # Load data
        result = loader.load_opportunities(
            opportunities=test_data,
            write_disposition="merge"
        )

        # Verify success (same assertion as failing test)
        assert result.success is True, "Load must succeed"

        # Verify data integrity by querying database directly (exact copy from failing test)
        with loader.get_session() as session:
            from sqlalchemy import text

            # Query the record we just inserted (exact query from failing test)
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

            # This is the assertion that's failing in pytest
            assert query_result is not None, "Record should be found in database"

            # Verify specific fields weren't corrupted (same assertions as failing test)
            assert query_result.title == 'Corruption Test Title', "Title should match"
            assert query_result.subreddit == 'corruption_test', "Subreddit should match"
            assert query_result.reddit_score == 42, "Upvotes should match"
            assert 'ABC123XYZ' in query_result.problem_description, "Text should contain marker"
            assert query_result.trust_score == 87.5, "Trust score should match"
            assert query_result.opportunity_score == 92.3, "Opportunity score should match"
            assert query_result.trust_level == 'HIGH', "Trust level should match"

        print("✅ Pytest no data corruption test: PASSED")

    def test_duplicate_handling_pytest(self):
        """Test duplicate handling with pytest environment"""
        print("\n=== PYTEST DUPLICATE HANDLING TEST ===")

        # Create loader
        loader = SQLAlchemyLoader('postgresql://postgres:postgres@127.0.0.1:54322/postgres')

        # Create test data with specific ID (exact copy from failing test)
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

        # Same assertions as failing test
        assert first_result.success is True, "First load should succeed"
        assert first_result.records_inserted == 1, "First load should insert 1 record"

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

        # Same assertions as failing test
        assert second_result.success is True, "Second load should succeed"
        assert second_result.records_inserted == 0, "Second load should insert 0 records"
        assert second_result.records_updated == 1, "Second load should update 1 record"

        # Verify data was updated, not duplicated (exact copy from failing test)
        with loader.get_session() as session:
            from sqlalchemy import text

            # Check total records for this submission ID
            count_result = session.execute(
                text("SELECT COUNT(*) FROM app_opportunities WHERE submission_id = :submission_id"),
                {"submission_id": submission_id}
            ).scalar()

            # This is the assertion that's failing in pytest
            assert count_result == 1, "Should have exactly 1 record, not duplicates"

            # Verify data was updated
            updated_record = session.execute(
                text("SELECT title, reddit_score, problem_description, trust_score FROM app_opportunities WHERE submission_id = :submission_id"),
                {"submission_id": submission_id}
            ).fetchone()

            assert updated_record.title == 'Updated Title', "Title should be updated"
            assert updated_record.reddit_score == 200, "Upvotes should be updated"
            assert 'Updated text' in updated_record.problem_description, "Text should be updated"
            assert updated_record.trust_score == 90.0, "Trust score should be updated"

        print("✅ Pytest duplicate handling test: PASSED")

    def test_verification_step_effectiveness_pytest(self):
        """Test verification step effectiveness with pytest environment"""
        print("\n=== PYTEST VERIFICATION STEP EFFECTIVENESS TEST ===")

        # Create loader
        loader = SQLAlchemyLoader('postgresql://postgres:postgres@127.0.0.1:54322/postgres')

        # Load valid data (exact copy from failing test)
        timestamp = int(time.time() * 1000000)
        valid_data = [{
            'submission_id': f'verification_test_{timestamp}',
            'title': 'Verification Test',
            'subreddit': 'verification_test',
            'upvotes': 50,
            'text': 'Testing verification step',
            'trust_score': 85.0,
            'processed_at': datetime.now(UTC).isoformat()
        }]

        result = loader.load_opportunities(
            opportunities=valid_data,
            write_disposition="merge"
        )

        # Verify success and that verification step ran (same as failing test)
        assert result.success is True, "Valid data load should succeed"
        assert result.records_inserted == 1, "Should insert 1 record"

        # Double-check by querying database directly (same as failing test)
        with loader.get_session() as session:
            from sqlalchemy import text

            count_result = session.execute(
                text("SELECT COUNT(*) FROM app_opportunities WHERE submission_id = :submission_id"),
                {"submission_id": f"verification_test_{timestamp}"}
            ).scalar()

            # This is the assertion that's failing in pytest
            assert count_result == 1, "Verification should confirm data was actually persisted"

        print("✅ Pytest verification step effectiveness test: PASSED")


if __name__ == "__main__":
    print("This file should be run with pytest: pytest test_minimal_pytest.py -xvs")