#!/usr/bin/env python3
"""
Test pytest session isolation issues without mocking dependencies
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, '/home/carlos/projects/redditharbor-core-functions-fix/.venv/lib/python3.12/site-packages')

# Import pytest without mocked dependencies
import pytest

# Test isolation by creating loaders in different test scopes
from storage.sqlalchemy_loader import SQLAlchemyLoader
import logging
import time
from datetime import datetime, UTC

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestPytestIsolation:
    """Test pytest isolation issues"""

    def test_session_isolation_single_test(self):
        """Test with session created and used in same test"""
        print("\n=== SINGLE TEST SESSION ISOLATION ===")

        # Create loader and test data
        loader = SQLAlchemyLoader('postgresql://postgres:postgres@127.0.0.1:54322/postgres')

        timestamp = int(time.time() * 1000000)
        test_data = [{
            'submission_id': f'single_test_{timestamp}',
            'title': 'Single Test',
            'subreddit': 'test',
            'upvotes': 42,
            'text': 'Test text',
            'trust_score': 80.0,
            'processed_at': datetime.now(UTC).isoformat()
        }]

        # Load data
        result = loader.load_opportunities(
            opportunities=test_data,
            write_disposition="merge"
        )

        # Verify success
        assert result.success is True
        assert result.records_inserted == 1

        # Verify data persistence
        with loader.get_session() as session:
            from sqlalchemy import text

            count = session.execute(
                text("SELECT COUNT(*) FROM app_opportunities WHERE submission_id = :submission_id"),
                {"submission_id": f"single_test_{timestamp}"}
            ).scalar()

            assert count == 1, f"Expected 1 record, found {count}"

        print("✅ Single test session isolation: PASSED")

    def test_cross_test_data_isolation(self):
        """Test that data from previous tests doesn't interfere"""
        print("\n=== CROSS TEST DATA ISOLATION ===")

        # Create a NEW loader instance
        loader = SQLAlchemyLoader('postgresql://postgres:postgres@127.0.0.1:54322/postgres')

        timestamp = int(time.time() * 1000000)
        test_data = [{
            'submission_id': f'cross_test_{timestamp}',
            'title': 'Cross Test',
            'subreddit': 'test',
            'upvotes': 84,
            'text': 'Cross test text',
            'trust_score': 90.0,
            'processed_at': datetime.now(UTC).isoformat()
        }]

        # Load data
        result = loader.load_opportunities(
            opportunities=test_data,
            write_disposition="merge"
        )

        # Verify success
        assert result.success is True
        assert result.records_inserted == 1

        # Verify our data exists
        with loader.get_session() as session:
            from sqlalchemy import text

            count = session.execute(
                text("SELECT COUNT(*) FROM app_opportunities WHERE submission_id = :submission_id"),
                {"submission_id": f"cross_test_{timestamp}"}
            ).scalar()

            assert count == 1, f"Expected 1 record, found {count}"

        print("✅ Cross test data isolation: PASSED")

    @pytest.fixture(scope="function")
    def loader_fixture(self):
        """Function-scoped loader fixture"""
        return SQLAlchemyLoader('postgresql://postgres:postgres@127.0.0.1:54322/postgres')

    def test_fixture_session_isolation(self, loader_fixture):
        """Test using function-scoped fixture"""
        print("\n=== FIXTURE SESSION ISOLATION ===")

        timestamp = int(time.time() * 1000000)
        test_data = [{
            'submission_id': f'fixture_test_{timestamp}',
            'title': 'Fixture Test',
            'subreddit': 'test',
            'upvotes': 126,
            'text': 'Fixture test text',
            'trust_score': 95.0,
            'processed_at': datetime.now(UTC).isoformat()
        }]

        # Load data using fixture
        result = loader_fixture.load_opportunities(
            opportunities=test_data,
            write_disposition="merge"
        )

        # Verify success
        assert result.success is True
        assert result.records_inserted == 1

        # Verify data persistence
        with loader_fixture.get_session() as session:
            from sqlalchemy import text

            count = session.execute(
                text("SELECT COUNT(*) FROM app_opportunities WHERE submission_id = :submission_id"),
                {"submission_id": f"fixture_test_{timestamp}"}
            ).scalar()

            assert count == 1, f"Expected 1 record, found {count}"

        print("✅ Fixture session isolation: PASSED")

    def test_transaction_rollback_behavior(self):
        """Test transaction rollback in pytest environment"""
        print("\n=== TRANSACTION ROLLBACK BEHAVIOR ===")

        # Test with data that should cause failure
        loader = SQLAlchemyLoader('postgresql://postgres:postgres@127.0.0.1:54322/postgres')

        # Create data that will fail validation
        invalid_data = [{
            'submission_id': None,  # This should cause failure
            'title': 'Invalid Test',
            'subreddit': 'test',
            'upvotes': 10
        }]

        # Attempt load with invalid data
        result = loader.load_opportunities(
            opportunities=invalid_data,
            write_disposition="merge"
        )

        # Should fail
        assert result.success is False
        assert result.records_inserted == 0
        assert result.error_message is not None

        print(f"✅ Transaction rollback test: {result.error_message}")

    def test_concurrent_session_behavior(self):
        """Test behavior with multiple sessions"""
        print("\n=== CONCURRENT SESSION BEHAVIOR ===")

        # Create two loaders
        loader1 = SQLAlchemyLoader('postgresql://postgres:postgres@127.0.0.1:54322/postgres')
        loader2 = SQLAlchemyLoader('postgresql://postgres:postgres@127.0.0.1:54322/postgres')

        timestamp = int(time.time() * 1000000)

        # Data for loader1
        data1 = [{
            'submission_id': f'concurrent1_{timestamp}',
            'title': 'Concurrent Test 1',
            'subreddit': 'test',
            'upvotes': 100,
            'processed_at': datetime.now(UTC).isoformat()
        }]

        # Data for loader2
        data2 = [{
            'submission_id': f'concurrent2_{timestamp}',
            'title': 'Concurrent Test 2',
            'subreddit': 'test',
            'upvotes': 200,
            'processed_at': datetime.now(UTC).isoformat()
        }]

        # Load with both loaders
        result1 = loader1.load_opportunities(opportunities=data1, write_disposition="merge")
        result2 = loader2.load_opportunities(opportunities=data2, write_disposition="merge")

        # Both should succeed
        assert result1.success is True and result2.success is True
        assert result1.records_inserted == 1 and result2.records_inserted == 1

        # Verify both records exist
        with loader1.get_session() as session:
            from sqlalchemy import text

            count1 = session.execute(
                text("SELECT COUNT(*) FROM app_opportunities WHERE submission_id = :submission_id"),
                {"submission_id": f"concurrent1_{timestamp}"}
            ).scalar()

            count2 = session.execute(
                text("SELECT COUNT(*) FROM app_opportunities WHERE submission_id = :submission_id"),
                {"submission_id": f"concurrent2_{timestamp}"}
            ).scalar()

            assert count1 == 1 and count2 == 1

        print("✅ Concurrent session behavior: PASSED")


if __name__ == "__main__":
    # Run tests directly without pytest
    print("Running isolation tests directly...")

    test_instance = TestPytestIsolation()

    try:
        test_instance.test_session_isolation_single_test()
        test_instance.test_cross_test_data_isolation()
        test_instance.test_transaction_rollback_behavior()
        test_instance.test_concurrent_session_behavior()

        print("\n✅ All isolation tests passed when run directly")
        print("🔍 This confirms the issue is with pytest environment/mocking")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()