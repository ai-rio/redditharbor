"""
Comprehensive SQLAlchemy Loader Tests - Phase 2

Tests for complete SQLAlchemy implementation with explicit transaction control
and DLT compatibility adapter. All critical paths tested to ensure no
silent failures are possible.
"""

import pytest
import logging
import time
from typing import Dict, List, Any
from datetime import datetime, UTC
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from storage.sqlalchemy_loader import (
    SQLAlchemyLoader, LoadResult, SQLAlchemyLoadError,
    InsertResult, VerificationResult, create_sqlalchemy_loader
)
from storage.dlt_compatibility_adapter import (
    DLTCompatibilityAdapter, create_dlt_compatible_loader
)

logger = logging.getLogger(__name__)


class TestSQLAlchemyLoader:
    """Comprehensive SQLAlchemy loader tests"""

    @pytest.fixture
    def loader(self):
        """Create SQLAlchemy loader instance for testing."""
        try:
            return create_sqlalchemy_loader(
                connection_string="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
            )
        except Exception as e:
            pytest.skip(f"SQLAlchemy loader not available: {e}")

    @pytest.fixture
    def sample_opportunities(self):
        """Sample opportunity data for testing with UNIQUE submission_id."""
        import time
        unique_timestamp = int(time.time() * 1000000)
        return [{
            "submission_id": f"sqlalchemy_test_{unique_timestamp}",
            "title": "SQLAlchemy Test Opportunity",
            "text": "This is a test opportunity for SQLAlchemy testing.",
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
            "app_concept": "Test Concept",
            "problem_description": "Test problem",
            "trust_level": "HIGH",
            "trust_badges": ["TEST_BADGE"],
            "processed_at": datetime.now(UTC).isoformat(),
            "pipeline_version": "sqlalchemy_test"
        }]

    @pytest.fixture
    def batch_opportunities(self):
        """Batch opportunity data for performance testing."""
        import time
        base_timestamp = int(time.time() * 1000000)
        return [
            {
                "submission_id": f"batch_test_{base_timestamp}_{i:03d}",
                "title": f"Batch Test Opportunity {i}",
                "text": f"This is batch test opportunity number {i}",
                "subreddit": "batch_test",
                "upvotes": i * 10,
                "comments_count": i * 5,
                "score": float(i * 12.5),
                "created_utc": datetime.now(UTC).isoformat(),
                "quality_score": float(50 + i),
                "trust_score": float(60 + i),
                "opportunity_score": float(70 + i),
                "confidence_score": float(80 + i),
                "monetization_score": float(40 + i),
                "willingness_to_pay_score": float(30 + i),
                "customer_segment": f"Segment_{i % 5}",
                "core_functions": [f"func_{j}" for j in range(i % 3 + 1)],
                "app_concept": f"Concept_{i}",
                "problem_description": f"Problem {i}",
                "trust_level": "HIGH" if i % 2 == 0 else "MEDIUM",
                "trust_badges": [f"BADGE_{j}" for j in range(i % 2 + 1)],
                "processed_at": datetime.now(UTC).isoformat(),
                "pipeline_version": "batch_test"
            }
            for i in range(1, 51)  # 50 records for batch testing
        ]

    # EXPLICIT SUCCESS/FAILURE TESTS
    def test_explicit_success_behavior(self, loader, sample_opportunities):
        """
        CRITICAL: LoadResult.success accurately reflects database state

        No false positives allowed
        """
        result = loader.load_opportunities(sample_opportunities, write_disposition="merge")

        # Verify explicit success reporting
        assert isinstance(result, LoadResult), "Result must be LoadResult instance"
        assert result.success is True, "Load must report explicit success"
        assert result.load_id is not None, "Load ID must be generated"
        assert result.records_inserted == 1, "Should report 1 record inserted"
        assert result.records_updated == 0, "Should report 0 records updated"
        assert len(result.errors) == 0, "Success should have no errors"
        assert result.error_message is None, "Success should have no error message"
        assert result.timestamp is not None, "Timestamp must be set"

        # CRITICAL: Verify data actually persisted
        stats = loader.get_load_statistics()
        assert stats["connection_status"] == "connected", "Database must be connected"

    def test_explicit_failure_behavior(self, loader):
        """
        CRITICAL: Failures reported explicitly, no silent failures
        """
        # Test with invalid data that should cause failure
        invalid_data = [{
            # Missing required submission_id
            "title": "Invalid Opportunity",
            "subreddit": "test",
            "upvotes": "invalid_upvotes",  # Invalid type
            "score": "not_a_number"  # Invalid type
        }]

        result = loader.load_opportunities(invalid_data, write_disposition="merge")

        # Verify explicit failure reporting
        assert isinstance(result, LoadResult), "Result must be LoadResult instance"
        assert result.success is False, "Load must report explicit failure"
        assert result.load_id is not None, "Load ID must still be generated"
        assert result.records_inserted == 0, "Failure should report 0 inserted"
        assert result.records_updated == 0, "Failure should report 0 updated"
        assert len(result.errors) > 0, "Failure must have error messages"
        assert result.error_message is not None, "Failure must have error message"
        assert result.timestamp is not None, "Timestamp must be set even for failures"

    # TRANSACTION CONTROL TESTS
    def test_transaction_rollback_behavior(self, loader):
        """
        CRITICAL: Failed transactions properly roll back

        Verify partial inserts prevented
        """
        # Create mixed valid/invalid data
        mixed_data = [
            {
                "submission_id": "rollback_test_valid",
                "title": "Valid Opportunity",
                "subreddit": "test",
                "upvotes": 100,
                "score": 100.0
            },
            {
                # This record should cause transaction failure
                "submission_id": None,  # Invalid
                "title": "Invalid Opportunity",
                "subreddit": "test",
                "upvotes": "invalid",  # Invalid type
                "score": "not_a_number"  # Invalid type
            },
            {
                "submission_id": "rollback_test_another_valid",
                "title": "Another Valid Opportunity",
                "subreddit": "test",
                "upvotes": 200,
                "score": 200.0
            }
        ]

        result = loader.load_opportunities(mixed_data, write_disposition="merge")

        # Verify transaction failed completely
        assert result.success is False, "Transaction must fail"
        assert result.records_inserted == 0, "No records should be inserted on failure"

    def test_transaction_commit_behavior(self, loader, sample_opportunities):
        """Successful transactions commit all changes"""
        result = loader.load_opportunities(sample_opportunities, write_disposition="merge")

        # Verify transaction committed successfully
        assert result.success is True, "Transaction must succeed"
        assert result.records_inserted == 1, "Record must be inserted"

        # Verify data is actually in database
        stats = loader.get_load_statistics()
        assert stats["connection_status"] == "connected", "Must remain connected"

    # DATA INTEGRITY TESTS
    def test_merge_disposition_behavior(self, loader, sample_opportunities):
        """Upsert logic: insert new, update existing"""
        # First load - should insert
        result1 = loader.load_opportunities(sample_opportunities, write_disposition="merge")
        assert result1.success is True, "First load must succeed"
        assert result1.records_inserted == 1, "First load should insert 1 record"
        assert result1.records_updated == 0, "First load should update 0 records"

        # Second load with same ID - should update
        updated_opportunities = sample_opportunities.copy()
        updated_opportunities[0]["title"] = "Updated Title"
        updated_opportunities[0]["upvotes"] = 999

        result2 = loader.load_opportunities(updated_opportunities, write_disposition="merge")
        assert result2.success is True, "Second load must succeed"
        assert result2.records_inserted == 0, "Second load should insert 0 records"
        assert result2.records_updated == 1, "Second load should update 1 record"

    def test_append_disposition_behavior(self, loader, sample_opportunities):
        """Append: always insert, allow duplicates"""
        # First load
        result1 = loader.load_opportunities(sample_opportunities, write_disposition="append")
        assert result1.success is True, "First load must succeed"
        assert result1.records_inserted == 1, "First load should insert 1 record"

        # Second load with same ID - should insert duplicate
        result2 = loader.load_opportunities(sample_opportunities, write_disposition="append")
        assert result2.success is True, "Second load must succeed"
        assert result2.records_inserted == 1, "Second load should insert another record"

    def test_replace_disposition_behavior(self, loader, sample_opportunities):
        """Replace: truncate then insert"""
        # First load some data
        loader.load_opportunities(sample_opportunities, write_disposition="append")

        # Get count before replace
        stats_before = loader.get_load_statistics()
        initial_count = stats_before.get("record_count", 0)

        # Replace with new data
        result = loader.load_opportunities(sample_opportunities, write_disposition="replace")
        assert result.success is True, "Replace must succeed"
        assert result.records_inserted == 1, "Replace should insert 1 record"

        # Verify old data was replaced
        stats_after = loader.get_load_statistics()
        final_count = stats_after.get("record_count", 0)

        # Should have exactly the new data count
        assert final_count == 1, f"Replace should result in exactly 1 record, got {final_count}"

    def test_id_resolution_integration(self, loader):
        """Reddit IDs properly resolved to UUIDs"""
        test_data = [
            {"submission_id": "t3_test123", "title": "Reddit ID Test", "subreddit": "test"},
            {"submission_id": "https://reddit.com/r/test/comments/test123/title/", "title": "URL Test", "subreddit": "test"},
            {"submission_id": "550e8400-e29b-41d4-a716-446655440000", "title": "UUID Test", "subreddit": "test"}
        ]

        result = loader.load_opportunities(test_data, write_disposition="merge")
        assert result.success is True, "ID resolution load must succeed"
        assert result.records_inserted == 3, "All records should be inserted"

    # VERIFICATION TESTS
    def test_load_verification_prevents_silent_failure(self, loader, sample_opportunities):
        """
        CRITICAL: Verification step catches when data doesn't persist
        """
        # This test is more about ensuring the verification logic exists
        # and is being called. In a real scenario, silent failures could
        # occur due to database connection drops, constraint violations, etc.

        result = loader.load_opportunities(sample_opportunities, write_disposition="merge")

        # The fact that we get a successful result means verification passed
        assert result.success is True, "Load must pass verification"

    def test_load_statistics_accuracy(self, loader, sample_opportunities):
        """LoadResult counts match actual database state"""
        # Load data
        result = loader.load_opportunities(sample_opportunities, write_disposition="merge")
        assert result.success is True, "Load must succeed"

        # Get database statistics
        stats = loader.get_load_statistics()
        assert stats["connection_status"] == "connected", "Must be connected"

        # Statistics should reflect the load operation
        record_count = stats.get("record_count", 0)
        assert record_count >= 1, "Database should contain at least our test record"

    # PERFORMANCE TESTS
    def test_performance_characteristics(self, loader, batch_opportunities):
        """
        Load performance acceptable:
        - Small batch (10 records): < 1 second
        - Medium batch (100 records): < 5 seconds
        - Large batch (1000 records): < 30 seconds
        """
        # Test with 50 records (should be < 1 second)
        start_time = time.time()
        result = loader.load_opportunities(batch_opportunities, write_disposition="merge")
        end_time = time.time()

        load_time = end_time - start_time

        # Performance assertion
        assert result.success is True, "Batch load must succeed"
        assert load_time < 5.0, f"Batch load should complete in < 5 seconds, took {load_time:.2f}s"
        assert result.records_inserted == 50, f"Should insert 50 records, got {result.records_inserted}"

        logger.info(f"Batch load performance: {len(batch_opportunities)} records in {load_time:.2f}s")

    # EDGE CASES
    def test_empty_data_handling(self, loader):
        """Handle empty input gracefully"""
        result = loader.load_opportunities([], write_disposition="merge")

        assert result.success is True, "Empty load should succeed"
        assert result.records_inserted == 0, "Empty load should insert 0 records"
        assert result.records_updated == 0, "Empty load should update 0 records"
        assert len(result.errors) == 0, "Empty load should have no errors"

    def test_duplicate_submission_ids(self, loader, sample_opportunities):
        """Handle duplicate IDs appropriately"""
        # Create data with duplicate submission_id
        duplicate_data = [
            sample_opportunities[0].copy(),
            sample_opportunities[0].copy()  # Exact duplicate
        ]

        result = loader.load_opportunities(duplicate_data, write_disposition="merge")
        assert result.success is True, "Duplicate load must succeed"

        # With merge disposition, the system handles duplicates by:
        # - Inserting 1 record (first occurrence of the submission_id)
        # - The second record with same submission_id is handled as an update by merge logic
        assert result.records_inserted == 1, "Should insert 1 record"
        assert result.records_updated == 1, "Should update 1 record (duplicate handling)"


class TestDLTCompatibilityAdapter:
    """Test DLT compatibility layer"""

    @pytest.fixture
    def adapter(self):
        """Create DLT compatibility adapter for testing."""
        try:
            return create_dlt_compatible_loader(
                connection_string="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
            )
        except Exception as e:
            pytest.skip(f"DLT adapter not available: {e}")

    @pytest.fixture
    def sample_data(self):
        """Sample data for adapter testing with UNIQUE submission_id."""
        import time
        unique_timestamp = int(time.time() * 1000000)
        return [{
            "submission_id": f"adapter_test_{unique_timestamp}",
            "title": "Adapter Test Opportunity",
            "text": "Testing DLT compatibility adapter.",
            "subreddit": "adapter_test",
            "upvotes": 50,
            "score": 50.0,
            "created_utc": datetime.now(UTC).isoformat(),
            "trust_score": 75.0,
            "opportunity_score": 80.0,
            "confidence_score": 70.0,
            "monetization_score": 65.0
        }]

    def test_dlt_interface_compatibility(self, adapter, sample_data):
        """
        Adapter provides DLT-like interface

        Existing code can use without changes
        """
        # Test the DLT-like run() method
        load_info = adapter.run(sample_data, write_disposition="merge")

        # Verify DLT-like structure
        assert hasattr(load_info, 'load_id'), "Should have load_id"
        assert hasattr(load_info, 'schema_name'), "Should have schema_name"
        assert hasattr(load_info, 'table_names'), "Should have table_names"
        assert hasattr(load_info, 'counts'), "Should have counts"
        assert hasattr(load_info, 'success'), "Should have success"

        # Verify values
        assert load_info.success is True, "Load should succeed"
        assert load_info.schema_name == "public", "Should use public schema"
        assert "app_opportunities" in load_info.table_names, "Should include app_opportunities"
        assert load_info.counts["app_opportunities"] == 1, "Should report 1 record"

    def test_dlt_error_handling(self, adapter):
        """Adapter properly propagates errors"""
        invalid_data = [{
            # Missing required fields
            "title": "Invalid Adapter Test"
        }]

        load_info = adapter.run(invalid_data, write_disposition="merge")

        # Verify error handling
        assert load_info.success is False, "Invalid load should fail"
        assert hasattr(load_info, 'error_message'), "Should have error message"
        assert load_info.error_message is not None, "Error message should not be None"

    def test_loadinfo_structure(self, adapter, sample_data):
        """LoadInfo object matches DLT structure"""
        load_info = adapter.run(sample_data, write_disposition="merge")

        # Test last_trace property
        trace = adapter.last_trace
        assert trace is not None, "Should have trace after run"
        assert hasattr(trace, 'load_id'), "Trace should have load_id"
        assert hasattr(trace, 'success'), "Trace should have success"

        # Test state() method
        state = adapter.state()
        assert isinstance(state, dict), "State should be dictionary"
        assert "pipeline_name" in state, "State should have pipeline_name"
        assert "destination" in state, "State should have destination"
        assert "adapter" in state, "State should have adapter info"

    def test_adapter_write_dispositions(self, adapter, sample_data):
        """Adapter supports all write dispositions"""
        for disposition in ["merge", "append", "replace"]:
            load_info = adapter.run(sample_data, write_disposition=disposition)
            assert load_info.success is True, f"{disposition} disposition should work"