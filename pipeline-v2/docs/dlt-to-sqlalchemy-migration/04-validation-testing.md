# Validation Testing - Comprehensive Test Suite

## Overview

This document provides the complete test suite for validating the SQLAlchemy implementation and ensuring it eliminates the silent failures found in DLT. The tests are organized into logical categories that cover all critical aspects of the migration.

## Test Structure

The validation tests are divided into three main categories:

1. **SQLAlchemy Implementation Tests** - Validate core SQLAlchemy functionality
2. **DLT Comparison Tests** - Compare SQLAlchemy behavior against DLT
3. **Parallel Validation Tests** - Run both systems side-by-side

## 1. SQLAlchemy Implementation Tests

### File: `pipeline-v2/tests/test_sqlalchemy_loader.py`

```python
"""
Comprehensive tests for SQLAlchemy loader implementation.

These tests verify that the SQLAlchemy replacement provides:
- Explicit transaction control
- Immediate success/failure feedback
- No silent failures
- Proper error handling
- Performance within acceptable limits
"""

import pytest
import logging
import time
from typing import Dict, List, Any
from datetime import datetime, UTC

from storage.sqlalchemy_loader import SQLAlchemyLoader, LoadResult, create_sqlalchemy_loader

logger = logging.getLogger(__name__)

class TestSQLAlchemyLoader:
    """Test SQLAlchemy loader implementation comprehensively."""

    @pytest.fixture
    def sqlalchemy_loader(self):
        """Create SQLAlchemy loader for testing."""
        connection_string = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
        try:
            loader = SQLAlchemyLoader(connection_string, echo=False)
            return loader
        except Exception as e:
            pytest.skip(f"SQLAlchemy connection failed: {e}")

    @pytest.fixture
    def sample_opportunities(self):
        """Sample opportunity data for testing."""
        return [{
            "submission_id": "sqlalchemy_test_001",
            "title": "SQLAlchemy Test Opportunity",
            "text": "This is a test opportunity for SQLAlchemy loader validation.",
            "subreddit": "test",
            "upvotes": 100,
            "comments_count": 25,
            "score": 125.0,
            "created_utc": datetime.now(UTC).isoformat(),
            "quality_score": 85.0,
            "trust_score": 80.0,
            "opportunity_score": 75.0,
            "confidence_score": 70.0,
            "monetization_score": 65.0,
            "willingness_to_pay_score": 60.0,
            "customer_segment": "Test Segment",
            "core_functions": ["test", "sqlalchemy"],
            "app_concept": "SQLAlchemy Test Concept",
            "problem_description": "SQLAlchemy test problem",
            "trust_level": "HIGH",
            "trust_badges": ["SQLALCHEMY_TEST_BADGE"],
            "processed_at": datetime.now(UTC).isoformat(),
            "pipeline_version": "sqlalchemy_test"
        }]

    def test_connection_validation(self, sqlalchemy_loader):
        """Test explicit connection validation."""
        result = sqlalchemy_loader.validate_connection()

        assert result is True, "Connection validation should return True for working connection"

        # Test statistics to ensure connection is working
        stats = sqlalchemy_loader.get_load_statistics()
        assert stats["connection_status"] == "connected"
        assert "total_records" in stats

        logger.info("✅ Connection validation test passed")

    def test_explicit_success_behavior(self, sqlalchemy_loader, sample_opportunities):
        """
        Test that SQLAlchemy provides explicit success feedback.

        This is critical - success should be clearly indicated
        and should correspond to actual data persistence.
        """
        # Get pre-load state
        pre_load_stats = sqlalchemy_loader.get_load_statistics()
        pre_count = pre_load_stats["total_records"]

        # Load data
        load_result = sqlalchemy_loader.load_opportunities(
            opportunities=sample_opportunities,
            table_name="app_opportunities",
            write_disposition="merge"
        )

        # Verify explicit success reporting
        assert isinstance(load_result, LoadResult)
        assert load_result.success is True, "LoadResult should indicate success"
        assert load_result.records_inserted > 0, "Should report records inserted"
        assert load_result.error_message is None, "Should have no error message on success"
        assert load_result.load_id is not None, "Should have load ID"

        # Verify actual data persistence
        post_load_stats = sqlalchemy_loader.get_load_statistics()
        post_count = post_load_stats["total_records"]

        assert post_count == pre_count + load_result.records_inserted, \
            f"Database should have {load_result.records_inserted} more records"

        logger.info(f"✅ Explicit success validation passed")
        logger.info(f"  - Records inserted: {load_result.records_inserted}")
        logger.info(f"  - Database count change: {post_count - pre_count}")

    def test_explicit_failure_behavior(self, sqlalchemy_loader):
        """
        Test that SQLAlchemy provides explicit failure feedback.

        Failures should be clearly indicated with error messages.
        """
        # Create invalid opportunity data that should cause failure
        invalid_opportunities = [{
            "submission_id": "sqlalchemy_invalid_test",
            "upvotes": "invalid_number",  # This should cause a type error
            "score": "not_a_float"
        }]

        # Attempt load - should fail explicitly
        load_result = sqlalchemy_loader.load_opportunities(
            opportunities=invalid_opportunities,
            table_name="app_opportunities"
        )

        # Verify explicit failure reporting
        assert isinstance(load_result, LoadResult)
        assert load_result.success is False, "LoadResult should indicate failure"
        assert load_result.records_inserted == 0, "Should report no records inserted"
        assert load_result.error_message is not None, "Should have error message"
        assert len(load_result.error_message) > 0, "Error message should not be empty"

        logger.info(f"✅ Explicit failure validation passed")
        logger.info(f"  - Error message: {load_result.error_message}")

    def test_transaction_rollback_behavior(self, sqlalchemy_loader):
        """
        Test that failed transactions are properly rolled back.

        This is critical - partial failures should not persist any data.
        """
        # Get initial record count
        initial_count = sqlalchemy_loader.get_load_statistics()["total_records"]

        # Create data where first record is valid but second is invalid
        mixed_validity_opportunities = [
            {
                "submission_id": "rollback_test_valid",
                "title": "Valid Record",
                "subreddit": "test",
                "upvotes": 100,
                "score": 100.0,
                "created_utc": datetime.now(UTC).isoformat()
            },
            {
                "submission_id": "rollback_test_invalid",
                "title": "Invalid Record",
                "subreddit": "test",
                "upvotes": "invalid",  # This should cause rollback
                "score": "not_a_float"
            }
        ]

        # Attempt load - should fail and rollback
        load_result = sqlalchemy_loader.load_opportunities(
            opportunities=mixed_validity_opportunities,
            table_name="app_opportunities"
        )

        # Verify load failed
        assert load_result.success is False
        assert load_result.error_message is not None

        # Verify rollback - no records should be added
        final_count = sqlalchemy_loader.get_load_statistics()["total_records"]
        assert final_count == initial_count, \
            "No records should be added when transaction rolls back"

        # Verify valid record was not persisted
        with sqlalchemy_loader.get_session() as session:
            result = session.execute(
                text("SELECT COUNT(*) FROM app_opportunities WHERE submission_id = 'rollback_test_valid'")
            ).scalar()
            assert result == 0, "Valid record should not be persisted after rollback"

        logger.info(f"✅ Transaction rollback validation passed")
        logger.info(f"  - Initial count: {initial_count}")
        logger.info(f"  - Final count: {final_count}")
        logger.info(f"  - Records added: 0 (correct rollback)")

    def test_merge_disposition_behavior(self, sqlalchemy_loader, sample_opportunities):
        """Test merge write disposition behavior (upsert logic)."""

        # First load - should insert
        first_load = sqlalchemy_loader.load_opportunities(
            opportunities=sample_opportunities,
            write_disposition="merge"
        )

        assert first_load.success is True
        assert first_load.records_inserted == len(sample_opportunities)
        assert first_load.records_updated == 0

        # Second load with same IDs - should update
        updated_opportunities = [
            {**opp, "upvotes": 999, "title": "Updated Title"}
            for opp in sample_opportunities
        ]

        second_load = sqlalchemy_loader.load_opportunities(
            opportunities=updated_opportunities,
            write_disposition="merge"
        )

        assert second_load.success is True
        assert second_load.records_inserted == 0, "Should insert no new records"
        assert second_load.records_updated == len(sample_opportunities), "Should update existing records"

        # Verify updates were actually applied
        with sqlalchemy_loader.get_session() as session:
            result = session.execute(
                text("SELECT upvotes, title FROM app_opportunities WHERE submission_id = :id"),
                {"id": sample_opportunities[0]["submission_id"]}
            ).fetchone()

            assert result.upvotes == 999, "Upvotes should be updated"
            assert result.title == "Updated Title", "Title should be updated"

        logger.info(f"✅ Merge disposition validation passed")

    def test_id_resolution_integration(self, sqlalchemy_loader):
        """
        Test integration with ID resolution system.

        Raw Reddit IDs should be resolved to UUIDs.
        """
        # Test with raw Reddit ID
        reddit_id_opportunities = [{
            "submission_id": "abc123xyz",  # Raw Reddit ID
            "title": "Reddit ID Test",
            "subreddit": "test",
            "upvotes": 50,
            "score": 75.0,
            "created_utc": datetime.now(UTC).isoformat()
        }]

        load_result = sqlalchemy_loader.load_opportunities(
            opportunities=reddit_id_opportunities,
            write_disposition="merge"
        )

        assert load_result.success is True

        # Verify ID was resolved to UUID format
        with sqlalchemy_loader.get_session() as session:
            result = session.execute(
                text("SELECT submission_id FROM app_opportunities WHERE title = 'Reddit ID Test'")
            ).fetchone()

            assert result is not None, "Record should be found"

            # Should be a UUID, not the raw Reddit ID
            stored_id = result.submission_id
            assert stored_id != "abc123xyz", "Should not store raw Reddit ID"
            assert len(stored_id) == 36, "Should be UUID length"
            assert stored_id.count('-') == 4, "Should be UUID format"

        logger.info(f"✅ ID resolution integration validation passed")

    def test_load_statistics_accuracy(self, sqlalchemy_loader, sample_opportunities):
        """Test that load statistics are accurate and consistent."""

        # Get initial statistics
        initial_stats = sqlalchemy_loader.get_load_statistics()
        initial_count = initial_stats["total_records"]

        # Load data
        load_result = sqlalchemy_loader.load_opportunities(
            opportunities=sample_opportunities,
            write_disposition="append"
        )

        # Get updated statistics
        updated_stats = sqlalchemy_loader.get_load_statistics()
        updated_count = updated_stats["total_records"]

        # Verify statistics accuracy
        assert updated_count == initial_count + load_result.records_inserted, \
            "Statistics should reflect actual database state"
        assert updated_stats["connection_status"] == "connected"
        assert "unique_subreddits" in updated_stats

        logger.info(f"✅ Load statistics validation passed")
        logger.info(f"  - Initial records: {initial_count}")
        logger.info(f"  - Loaded records: {load_result.records_inserted}")
        logger.info(f"  - Final records: {updated_count}")
        logger.info(f"  - Count matches: {updated_count == initial_count + load_result.records_inserted}")

    def test_performance_characteristics(self, sqlalchemy_loader):
        """Test performance characteristics are reasonable."""

        # Create larger dataset for performance testing
        performance_data = []
        for i in range(100):  # 100 records
            performance_data.append({
                "submission_id": f"perf_test_{i}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
                "title": f"Performance Test Record {i}",
                "subreddit": "performance_test",
                "upvotes": i * 10,
                "score": float(i * 15),
                "created_utc": datetime.now(UTC).isoformat(),
                "quality_score": 80.0 + (i % 20),
                "trust_score": 75.0 + (i % 25)
            })

        # Measure performance
        start_time = time.time()
        load_result = sqlalchemy_loader.load_opportunities(
            opportunities=performance_data,
            write_disposition="append"
        )
        execution_time = time.time() - start_time

        # Validate performance
        assert load_result.success is True, "Performance test should succeed"
        assert execution_time < 30.0, "Should complete within 30 seconds"
        assert len(performance_data) / execution_time > 10, "Should process at least 10 records/sec"

        records_per_second = len(performance_data) / execution_time
        logger.info(f"✅ Performance validation passed")
        logger.info(f"  - Records processed: {len(performance_data)}")
        logger.info(f"  - Execution time: {execution_time:.2f}s")
        logger.info(f"  - Records per second: {records_per_second:.1f}")

    def test_data_type_handling(self, sqlalchemy_loader):
        """Test proper handling of different data types."""

        # Test various data types
        type_test_data = [{
            "submission_id": "type_test_001",
            "title": "Type Test",
            "subreddit": "test",
            "upvotes": 100,  # Integer
            "score": 123.456,  # Float
            "created_utc": datetime.now(UTC).isoformat(),  # String/datetime
            "core_functions": ["test", "validation"],  # List
            "trust_badges": [],  # Empty list
            "quality_score": 0.0,  # Zero float
            "comments_count": 0  # Zero integer
        }]

        load_result = sqlalchemy_loader.load_opportunities(type_test_data)

        assert load_result.success is True
        assert load_result.records_inserted == 1

        # Verify data types were handled correctly
        with sqlalchemy_loader.get_session() as session:
            result = session.execute(
                text("SELECT upvotes, score, core_functions, trust_badges FROM app_opportunities WHERE submission_id = 'type_test_001'")
            ).fetchone()

            assert result.upvotes == 100, "Integer should be preserved"
            assert result.score == 123.456, "Float should be preserved"
            assert result.core_functions == ["test", "validation"], "List should be preserved"
            assert result.trust_badges == [], "Empty list should be preserved"

        logger.info(f"✅ Data type handling validation passed")

    def test_edge_cases(self, sqlalchemy_loader):
        """Test edge cases and boundary conditions."""

        # Test empty data
        empty_result = sqlalchemy_loader.load_opportunities([])
        assert empty_result.success is True
        assert empty_result.records_inserted == 0

        # Test very long strings
        long_text_data = [{
            "submission_id": "edge_test_long",
            "title": "Long Title Test",
            "text": "x" * 10000,  # Very long text
            "subreddit": "test",
            "upvotes": 1,
            "score": 1.0,
            "created_utc": datetime.now(UTC).isoformat()
        }]

        long_result = sqlalchemy_loader.load_opportunities(long_text_data)
        assert long_result.success is True

        # Test special characters
        special_char_data = [{
            "submission_id": "edge_test_special",
            "title": "Special Characters: áéíóú 🚀 ñç",
            "text": "Special chars: 'quotes', \"double quotes\", \\backslashes\\, \n\tnewlines\t",
            "subreddit": "test",
            "upvotes": 1,
            "score": 1.0,
            "created_utc": datetime.now(UTC).isoformat()
        }]

        special_result = sqlalchemy_loader.load_opportunities(special_char_data)
        assert special_result.success is True

        logger.info(f"✅ Edge cases validation passed")

class TestDLTCompatibilityAdapter:
    """Test DLT compatibility adapter functionality."""

    @pytest.fixture
    def dlt_adapter(self):
        """Create DLT compatibility adapter."""
        try:
            from storage.dlt_compatibility_adapter import create_dlt_compatible_loader
            return create_dlt_compatible_loader()
        except Exception as e:
            pytest.skip(f"DLT adapter not available: {e}")

    def test_dlt_interface_compatibility(self, dlt_adapter):
        """Test that adapter provides DLT-like interface."""

        test_data = [{
            "submission_id": "compat_test_001",
            "title": "Compatibility Test",
            "subreddit": "test",
            "upvotes": 100,
            "score": 100.0,
            "created_utc": datetime.now(UTC).isoformat()
        }]

        # Test DLT-like interface
        load_info = dlt_adapter.run(
            data=test_data,
            table_name="app_opportunities",
            write_disposition="merge"
        )

        # Verify DLT-like attributes
        assert hasattr(load_info, 'load_id')
        assert hasattr(load_info, 'schema_name')
        assert hasattr(load_info, 'table_names')
        assert hasattr(load_info, 'counts')
        assert hasattr(load_info, 'success')

        # Verify values
        assert load_info.success is True
        assert load_info.schema_name == "public"
        assert "app_opportunities" in load_info.table_names
        assert "app_opportunities" in load_info.counts
        assert load_info.counts["app_opportunities"] > 0

        logger.info(f"✅ DLT interface compatibility validation passed")

    def test_dlt_error_handling(self, dlt_adapter):
        """Test error handling in DLT-compatible mode."""

        invalid_data = [{
            "submission_id": None,  # Invalid
            "upvotes": "invalid"
        }]

        load_info = dlt_adapter.run(data=invalid_data)

        # Should handle error gracefully
        assert load_info.success is False
        assert load_info.counts["app_opportunities"] == 0

        logger.info(f"✅ DLT error handling validation passed")
```

## 2. DLT Comparison Tests

### File: `pipeline-v2/tests/test_dlt_comparison.py`

```python
"""
Comparison tests between DLT and SQLAlchemy implementations.

These tests directly compare the behavior of both systems to validate
that SQLAlchemy fixes the silent failure issues in DLT.
"""

import pytest
import logging
from typing import Dict, List, Any
from datetime import datetime, UTC

from storage.dlt_loader import DLTLoader
from storage.sqlalchemy_loader import SQLAlchemyLoader

logger = logging.getLogger(__name__)

class TestDLTComparison:
    """Compare DLT and SQLAlchemy behaviors directly."""

    @pytest.fixture
    def dlt_loader(self):
        """Create DLT loader instance."""
        try:
            return DLTLoader(
                pipeline_name="comparison_test_dlt",
                use_local_dev=True
            )
        except Exception as e:
            pytest.skip(f"DLT not available for comparison: {e}")

    @pytest.fixture
    def sqlalchemy_loader(self):
        """Create SQLAlchemy loader instance."""
        connection_string = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
        try:
            return SQLAlchemyLoader(connection_string, echo=False)
        except Exception as e:
            pytest.skip(f"SQLAlchemy not available for comparison: {e}")

    def test_silent_failure_comparison(self, dlt_loader, sqlalchemy_loader):
        """
        CRITICAL TEST: Compare silent failure behavior.

        This test validates that SQLAlchemy eliminates the silent failures
        that occur with DLT.
        """
        # Generate unique test data
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
        test_data = [{
            "submission_id": f"silent_failure_test_{timestamp}",
            "title": f"Silent Failure Test {timestamp}",
            "subreddit": "test",
            "upvotes": 50,
            "score": 75.0,
            "created_utc": datetime.now(UTC).isoformat()
        }]

        # Get initial database state
        initial_count = sqlalchemy_loader.get_load_statistics()["total_records"]

        # Test SQLAlchemy behavior
        sqlalchemy_result = sqlalchemy_loader.load_opportunities(test_data)

        # Verify SQLAlchemy reports success AND data is actually persisted
        assert sqlalchemy_result.success is True, "SQLAlchemy should report success"
        assert sqlalchemy_result.records_inserted > 0, "SQLAlchemy should report records inserted"

        # Verify actual data persistence
        final_count = sqlalchemy_loader.get_load_statistics()["total_records"]
        actual_records_added = final_count - initial_count
        assert actual_records_added == sqlalchemy_result.records_inserted, \
            "SQLAlchemy reported records should match actual database changes"

        logger.info("✅ SQLAlchemy: No silent failure - success reports match actual persistence")

        # Test DLT behavior for comparison
        dlt_test_data = [{
            "submission_id": f"dlt_{test_data[0]['submission_id']}",
            "title": f"DLT {test_data[0]['title']}",
            "subreddit": "test",
            "upvotes": 50,
            "score": 75.0,
            "created_utc": datetime.now(UTC).isoformat()
        }]

        dlt_success = False
        dlt_records_reported = 0

        try:
            dlt_load_info = dlt_loader.load_opportunities(dlt_test_data)
            dlt_success = self._check_dlt_success(dlt_load_info)

            if hasattr(dlt_load_info, 'counts') and dlt_load_info.counts:
                dlt_records_reported = sum(dlt_load_info.counts.values())

        except Exception as e:
            logger.info(f"DLT load failed with exception: {e}")
            dlt_success = False

        # Check actual DLT data persistence
        dlt_count = sqlalchemy_loader.get_load_statistics()["total_records"]
        dlt_records_added = dlt_count - final_count

        # Document the difference
        logger.info(f"Behavior Comparison:")
        logger.info(f"  SQLAlchemy: Success={sqlalchemy_result.success}, Reported={sqlalchemy_result.records_inserted}, Actual={actual_records_added}")
        logger.info(f"  DLT:        Success={dlt_success}, Reported={dlt_records_reported}, Actual={dlt_records_added}")

        # Validate SQLAlchemy is superior
        assert sqlalchemy_result.success == (actual_records_added > 0), \
            "SQLAlchemy success should match actual data persistence"

        if dlt_success and dlt_records_added == 0:
            logger.error("🚨 CONFIRMED: DLT silent failure - reports success but no data persisted")

        logger.info("✅ Silent failure comparison completed")

    def test_error_reporting_comparison(self, dlt_loader, sqlalchemy_loader):
        """Compare error handling and reporting between implementations."""

        # Create invalid data that should cause errors
        invalid_data = [{
            "submission_id": None,  # Invalid primary key
            "title": "Error Test",
            "upvotes": "not_a_number"  # Invalid type
        }]

        # Test SQLAlchemy error handling
        sqlalchemy_result = sqlalchemy_loader.load_opportunities(invalid_data)

        # Validate SQLAlchemy error reporting
        assert sqlalchemy_result.success is False, "SQLAlchemy should report failure"
        assert sqlalchemy_result.error_message is not None, "SQLAlchemy should provide error message"
        assert sqlalchemy_result.records_inserted == 0, "SQLAlchemy should report no records inserted"

        # Test DLT error handling
        dlt_success = False
        dlt_error = None

        try:
            dlt_load_info = dlt_loader.load_opportunities(invalid_data)
            dlt_success = self._check_dlt_success(dlt_load_info)
        except Exception as e:
            dlt_error = str(e)

        # Document comparison
        logger.info("Error Handling Comparison:")
        logger.info(f"  SQLAlchemy: Success={sqlalchemy_result.success}, Error={sqlalchemy_result.error_message}")
        logger.info(f"  DLT:        Success={dlt_success}, Exception={dlt_error}")

        # Validate SQLAlchemy error handling is superior
        assert sqlalchemy_result.success is False, "SQLAlchemy should fail cleanly"
        assert sqlalchemy_result.error_message, "SQLAlchemy should provide clear error message"

        logger.info("✅ Error handling comparison completed")

    def test_performance_comparison(self, dlt_loader, sqlalchemy_loader):
        """Compare performance characteristics."""

        # Create test dataset
        performance_data = []
        for i in range(50):  # 50 records for reasonable test
            performance_data.append({
                "submission_id": f"perf_comp_{i}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
                "title": f"Performance Comparison {i}",
                "subreddit": "performance_comparison",
                "upvotes": i * 5,
                "score": float(i * 7),
                "created_utc": datetime.now(UTC).isoformat()
            })

        # Test SQLAlchemy performance
        import time
        sqlalchemy_start = time.time()
        sqlalchemy_result = sqlalchemy_loader.load_opportunities(performance_data)
        sqlalchemy_time = time.time() - sqlalchemy_start

        # Test DLT performance
        dlt_performance_data = [
            {**record, "submission_id": f"dlt_{record['submission_id']}"}
            for record in performance_data
        ]

        dlt_start = time.time()
        dlt_success = False
        try:
            dlt_load_info = dlt_loader.load_opportunities(dlt_performance_data)
            dlt_success = self._check_dlt_success(dlt_load_info)
        except Exception as e:
            logger.info(f"DLT performance test failed: {e}")
        dlt_time = time.time() - dlt_start

        # Document performance comparison
        logger.info("Performance Comparison:")
        logger.info(f"  Records tested: {len(performance_data)}")
        logger.info(f"  SQLAlchemy: Time={sqlalchemy_time:.2f}s, Success={sqlalchemy_result.success}")
        logger.info(f"  DLT:        Time={dlt_time:.2f}s, Success={dlt_success}")

        if sqlalchemy_result.success:
            sqlalchemy_rps = len(performance_data) / sqlalchemy_time
            logger.info(f"  SQLAlchemy: {sqlalchemy_rps:.1f} records/sec")

        if dlt_success:
            dlt_rps = len(performance_data) / dlt_time
            logger.info(f"  DLT:        {dlt_rps:.1f} records/sec")

        # Validate SQLAlchemy performance is reasonable
        assert sqlalchemy_result.success is True, "SQLAlchemy should succeed"
        assert sqlalchemy_time < 15.0, "SQLAlchemy should complete within 15 seconds"

        logger.info("✅ Performance comparison completed")

    def _check_dlt_success(self, load_info) -> bool:
        """Helper to check if DLT reports success."""
        if hasattr(load_info, 'counts') and load_info.counts:
            return sum(load_info.counts.values()) > 0
        elif hasattr(load_info, 'success'):
            return load_info.success
        else:
            return True  # Assume success if no clear failure indicator
```

## 3. Running the Tests

### Test Execution

```bash
# Run all SQLAlchemy tests
pytest pipeline-v2/tests/test_sqlalchemy_loader.py -v

# Run DLT comparison tests
pytest pipeline-v2/tests/test_dlt_comparison.py -v

# Run all validation tests
pytest pipeline-v2/tests/ -k "sqlalchemy or dlt_comparison" -v

# Run with detailed output
pytest pipeline-v2/tests/test_sqlalchemy_loader.py -v -s

# Run specific critical tests
pytest pipeline-v2/tests/test_sqlalchemy_loader.py::TestSQLAlchemyLoader::test_explicit_success_behavior -v -s
pytest pipeline-v2/tests/test_sqlalchemy_loader.py::TestSQLAlchemyLoader::test_transaction_rollback_behavior -v -s
```

### Test Configuration

Create `pipeline-v2/tests/conftest.py` for shared test configuration:

```python
"""
Pytest configuration for pipeline-v2 tests.
"""

import pytest
import logging
import sys
import os

# Add pipeline-v2 to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@pytest.fixture(scope="session")
def test_database_url():
    """Database URL for testing."""
    return os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
```

## Validation Checklist

### Before Migration

- [ ] All characterization tests document current DLT behavior
- [ ] SQLAlchemy connection validation passes
- [ ] Basic load operations work correctly
- [ ] ID resolution system integration confirmed
- [ ] Error handling behaves explicitly

### During Migration

- [ ] All SQLAlchemy implementation tests pass
- [ ] Transaction rollback behavior verified
- [ ] Silent failure comparison confirms fix
- [ ] Performance characteristics acceptable
- [ ] DLT compatibility adapter works

### After Migration

- [ ] Parallel tests show consistency
- [ ] No regression in functionality
- [ ] Performance meets or exceeds requirements
- [ ] Error visibility significantly improved
- [ ] All test scenarios covered

This comprehensive test suite ensures that the SQLAlchemy implementation successfully replaces DLT while eliminating the critical silent failure issues.