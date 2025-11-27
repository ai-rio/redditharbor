#!/usr/bin/env python3
"""
Fixed version of test_no_data_corruption that accounts for ID resolution

CRITICAL FIX: The original test was failing because ID resolution converts
submission_id to UUID, but the test was querying for the original ID.
"""

import pytest
import logging
import time
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, UTC
from types import SimpleNamespace
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import both implementations for comparison
from storage.sqlalchemy_loader import (
    SQLAlchemyLoader, LoadResult, create_sqlalchemy_loader
)

# Import ID resolver to handle submission_id resolution
try:
    from core.utils.id_resolver import resolve_submission_id, ResolutionResult
    ID_RESOLVER_AVAILABLE = True
except ImportError:
    ID_RESOLVER_AVAILABLE = False
    ResolutionResult = None

logger = logging.getLogger(__name__)


class TestDataIntegrityFixed:
    """Fixed version of TestDataIntegrity that handles ID resolution correctly"""

    @pytest.fixture
    def sqlalchemy_loader(self):
        """Create SQLAlchemy loader for integrity testing."""
        try:
            return create_sqlalchemy_loader(
                connection_string="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
            )
        except Exception as e:
            pytest.skip(f"SQLAlchemy loader not available: {e}")

    def resolve_submission_id_for_test(self, original_id: str) -> str:
        """
        Helper function to resolve submission_id for testing

        Args:
            original_id: Original submission_id from test data

        Returns:
            Resolved UUID (or original ID if resolver unavailable)
        """
        if ID_RESOLVER_AVAILABLE:
            try:
                resolved = resolve_submission_id(original_id)
                return resolved.uuid if resolved else original_id
            except Exception as e:
                logger.warning(f"ID resolution failed for {original_id}: {e}")
                return original_id
        else:
            return original_id

    def test_no_data_corruption_fixed(self, sqlalchemy_loader):
        """
        FIXED VERSION: Verify data integrity preserved during load operations

        CRITICAL FIX: Query using resolved UUID, not original submission_id
        """
        logger.info("=== NO DATA CORRUPTION INTEGRITY TEST (FIXED) ===")

        # Generate test data with specific values
        timestamp = int(time.time() * 1000000)
        original_submission_id = f'corruption_test_{timestamp}'
        test_data = [
            {
                'submission_id': original_submission_id,
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

        print(f"Original submission_id: {original_submission_id}")

        # CRITICAL FIX: Resolve submission_id before loading to know what to query
        resolved_submission_id = self.resolve_submission_id_for_test(original_submission_id)
        print(f"Resolved submission_id: {resolved_submission_id}")

        # Load data
        result = sqlalchemy_loader.load_opportunities(
            opportunities=test_data,
            write_disposition="merge"
        )

        # Verify success
        assert result.success is True, "Load must succeed"
        assert result.records_inserted == 1, "Should insert 1 record"
        print(f"✅ Load succeeded: inserted={result.records_inserted}")

        # CRITICAL FIX: Query using resolved UUID, not original ID
        with sqlalchemy_loader.get_session() as session:
            from sqlalchemy import text

            print("=== DATA VERIFICATION ===")
            print(f"Querying for resolved submission_id: {resolved_submission_id}")

            # Query the record using the RESOLVED UUID (the fix!)
            query_result = session.execute(
                text("""
                    SELECT title, subreddit, reddit_score, problem_description,
                           trust_score, opportunity_score, trust_level,
                           trust_badges, pipeline_source
                    FROM app_opportunities
                    WHERE submission_id = :submission_id
                """),
                {"submission_id": resolved_submission_id}  # CRITICAL FIX: Use resolved UUID
            ).fetchone()

            print(f"Query result: {query_result}")

            assert query_result is not None, f"Record should be found in database with resolved ID {resolved_submission_id}"
            print("✅ Record found in database")

            # Verify specific fields weren't corrupted
            assert query_result.title == 'Corruption Test Title', f"Title should match, got: {query_result.title}"
            assert query_result.subreddit == 'corruption_test', f"Subreddit should match, got: {query_result.subreddit}"
            assert query_result.reddit_score == 42, f"Reddit score should match, got: {query_result.reddit_score}"
            assert 'ABC123XYZ' in query_result.problem_description, f"Text should contain marker, got: {query_result.problem_description}"
            assert query_result.trust_score == 87.5, f"Trust score should match, got: {query_result.trust_score}"
            assert query_result.opportunity_score == 92.3, f"Opportunity score should match, got: {query_result.opportunity_score}"
            assert query_result.trust_level == 'HIGH', f"Trust level should match, got: {query_result.trust_level}"

            print("✅ All data corruption checks passed")

        logger.info("✅ No data corruption integrity test (FIXED) PASSED")

    def test_duplicate_handling_fixed(self, sqlalchemy_loader):
        """
        FIXED VERSION: Verify duplicate handling with merge disposition

        CRITICAL FIX: Query using resolved UUID, not original submission_id
        """
        logger.info("=== DUPLICATE HANDLING TEST (FIXED) ===")

        # Create test data with specific ID
        timestamp = int(time.time() * 1000000)
        original_submission_id = f"duplicate_test_{timestamp}"

        # First load
        first_data = [{
            'submission_id': original_submission_id,
            'title': 'Original Title',
            'subreddit': 'duplicate_test',
            'upvotes': 100,
            'text': 'Original text',
            'trust_score': 80.0,
            'processed_at': datetime.now(UTC).isoformat()
        }]

        first_result = sqlalchemy_loader.load_opportunities(
            opportunities=first_data,
            write_disposition="merge"
        )
        assert first_result.success is True, "First load should succeed"
        assert first_result.records_inserted == 1, "First load should insert 1 record"
        print("✅ First load succeeded")

        # Second load with same ID (should update)
        second_data = [{
            'submission_id': original_submission_id,  # Same ID
            'title': 'Updated Title',  # Different title
            'subreddit': 'duplicate_test',
            'upvotes': 200,  # Different upvotes
            'text': 'Updated text',  # Different text
            'trust_score': 90.0,  # Different score
            'processed_at': datetime.now(UTC).isoformat()
        }]

        second_result = sqlalchemy_loader.load_opportunities(
            opportunities=second_data,
            write_disposition="merge"
        )
        assert second_result.success is True, "Second load should succeed"
        assert second_result.records_inserted == 0, "Second load should insert 0 records"
        assert second_result.records_updated == 1, "Second load should update 1 record"
        print("✅ Second load succeeded")

        # CRITICAL FIX: Verify data was updated, not duplicated using resolved UUID
        resolved_submission_id = self.resolve_submission_id_for_test(original_submission_id)

        with sqlalchemy_loader.get_session() as session:
            from sqlalchemy import text

            print("=== DUPLICATE VERIFICATION ===")
            print(f"Checking for resolved submission_id: {resolved_submission_id}")

            # Check total records for this resolved submission ID
            count_result = session.execute(
                text("SELECT COUNT(*) FROM app_opportunities WHERE submission_id = :submission_id"),
                {"submission_id": resolved_submission_id}
            ).scalar()

            print(f"Record count for {resolved_submission_id}: {count_result}")
            assert count_result == 1, "Should have exactly 1 record, not duplicates"
            print("✅ No duplicates found")

            # Verify data was updated
            updated_record = session.execute(
                text("SELECT title, reddit_score, problem_description, trust_score FROM app_opportunities WHERE submission_id = :submission_id"),
                {"submission_id": resolved_submission_id}
            ).fetchone()

            print(f"Updated record: {updated_record}")
            assert updated_record.title == 'Updated Title', "Title should be updated"
            assert updated_record.reddit_score == 200, "Reddit score should be updated"
            assert 'Updated text' in updated_record.problem_description, "Text should be updated"
            assert updated_record.trust_score == 90.0, "Trust score should be updated"

            print("✅ Update verification passed")

        logger.info("✅ Duplicate handling test (FIXED) PASSED")

    def test_verification_step_effectiveness_fixed(self, sqlalchemy_loader):
        """
        FIXED VERSION: Verify that verification step catches silent failures

        CRITICAL FIX: Query using resolved UUID, not original submission_id
        """
        logger.info("=== VERIFICATION STEP EFFECTIVENESS TEST (FIXED) ===")

        # Load valid data
        timestamp = int(time.time() * 1000000)
        original_submission_id = f'verification_test_{timestamp}'
        test_data = [{
            'submission_id': original_submission_id,
            'title': 'Verification Test',
            'subreddit': 'verification_test',
            'upvotes': 50,
            'text': 'Testing verification step',
            'trust_score': 85.0,
            'processed_at': datetime.now(UTC).isoformat()
        }]

        result = sqlalchemy_loader.load_opportunities(
            opportunities=test_data,
            write_disposition="merge"
        )

        # Verify success and that verification step ran
        assert result.success is True, "Valid data load should succeed"
        assert result.records_inserted == 1, "Should insert 1 record"

        # CRITICAL FIX: Double-check using resolved UUID
        resolved_submission_id = self.resolve_submission_id_for_test(original_submission_id)

        with sqlalchemy_loader.get_session() as session:
            from sqlalchemy import text

            count_result = session.execute(
                text("SELECT COUNT(*) FROM app_opportunities WHERE submission_id = :submission_id"),
                {"submission_id": resolved_submission_id}
            ).scalar()

            assert count_result == 1, f"Verification should confirm data was actually persisted (found {count_result} records)"

        print("✅ Verification step confirmed data persistence")
        logger.info("✅ Verification step effectiveness test (FIXED) PASSED")


def main():
    """
    Run the fixed tests standalone to verify they work
    """
    print("🔧 Testing fixed version of data integrity tests")

    # Create loader
    try:
        loader = create_sqlalchemy_loader(
            connection_string="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
        )
        print("✅ SQLAlchemy loader created")
    except Exception as e:
        print(f"❌ Failed to create loader: {e}")
        return False

    # Create test instance
    test_instance = TestDataIntegrityFixed()

    # Test 1: No data corruption
    try:
        test_instance.test_no_data_corruption_fixed(loader)
        print("✅ No data corruption test PASSED")
    except Exception as e:
        print(f"❌ No data corruption test FAILED: {e}")
        return False

    # Test 2: Duplicate handling
    try:
        test_instance.test_duplicate_handling_fixed(loader)
        print("✅ Duplicate handling test PASSED")
    except Exception as e:
        print(f"❌ Duplicate handling test FAILED: {e}")
        return False

    # Test 3: Verification effectiveness
    try:
        test_instance.test_verification_step_effectiveness_fixed(loader)
        print("✅ Verification effectiveness test PASSED")
    except Exception as e:
        print(f"❌ Verification effectiveness test FAILED: {e}")
        return False

    print("\n🎉 ALL FIXED TESTS PASSED!")
    print("\n📋 SUMMARY OF THE FIX:")
    print("The root cause was ID resolution converting submission_id to UUID.")
    print("Fixed tests now:")
    print("1. Resolve submission_id before loading data")
    print("2. Query using resolved UUID instead of original ID")
    print("3. All data verification works correctly")

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)