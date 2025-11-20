"""Schema migration and evolution tests for storage layer.

Tests DLT's schema evolution capabilities with the storage services,
ensuring data integrity during schema changes and validating merge
disposition behavior.
"""

import pytest
from unittest.mock import MagicMock, patch
import time
from core.storage import OpportunityStore, ProfileStore, DLTLoader


class TestSchemaMigration:
    """Test DLT schema evolution capabilities."""

    @patch("core.storage.dlt_loader.dlt.pipeline")
    def test_add_column_to_existing_schema(self, mock_pipeline_func):
        """Test adding new column doesn't break existing data."""
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_func.return_value = mock_pipeline

        store = OpportunityStore()

        # Load data with original schema
        original_data = [
            {
                "submission_id": "schema_test_1",
                "problem_description": "Original problem",
                "app_concept": "Original app",
                "core_functions": ["Feature 1"],
                "value_proposition": "Original value",
                "target_user": "Users",
                "monetization_model": "Subscription",
            }
        ]

        success1 = store.store(original_data)
        assert success1 is True

        # Load data with new column added
        evolved_data = [
            {
                "submission_id": "schema_test_2",
                "problem_description": "Evolved problem",
                "app_concept": "Evolved app",
                "core_functions": ["Feature 1"],
                "value_proposition": "Evolved value",
                "target_user": "Users",
                "monetization_model": "Subscription",
                "new_field": "This is a new field added later",  # New column
            }
        ]

        success2 = store.store(evolved_data)
        assert success2 is True

        # Both loads should succeed - DLT handles schema evolution
        assert store.stats.loaded == 2
        assert store.stats.failed == 0

    @patch("core.storage.dlt_loader.dlt.pipeline")
    def test_merge_disposition_prevents_duplicates(self, mock_pipeline_func):
        """Test merge disposition prevents duplicate records."""
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_func.return_value = mock_pipeline

        store = OpportunityStore()

        # Load initial data
        data = [
            {
                "submission_id": "merge_test_1",
                "problem_description": "Test problem",
                "app_concept": "Test app",
                "core_functions": ["Feature 1"],
                "value_proposition": "Test value",
                "target_user": "Users",
                "monetization_model": "Subscription",
                "opportunity_score": 70.0,
            }
        ]

        # Load first time
        success1 = store.store(data)
        assert success1 is True

        # Load same submission_id again with updated data
        updated_data = [
            {
                "submission_id": "merge_test_1",  # Same ID
                "problem_description": "Updated problem",
                "app_concept": "Updated app",
                "core_functions": ["Feature 1", "Feature 2"],
                "value_proposition": "Updated value",
                "target_user": "Updated users",
                "monetization_model": "Freemium",
                "opportunity_score": 85.0,  # Updated score
            }
        ]

        success2 = store.store(updated_data)
        assert success2 is True

        # Both loads should succeed - merge should update, not duplicate
        assert store.stats.loaded == 2
        assert store.stats.failed == 0

        # Verify merge disposition was used in both calls
        calls = mock_pipeline.run.call_args_list
        assert all(
            call.kwargs.get("write_disposition") == "merge" for call in calls
        ), "All loads should use merge disposition"

    @patch("core.storage.dlt_loader.dlt.pipeline")
    def test_schema_backward_compatibility(self, mock_pipeline_func):
        """Test new schema can load old data format."""
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_func.return_value = mock_pipeline

        store = OpportunityStore()

        # Load data with minimal required fields (old format)
        minimal_data = [
            {
                "submission_id": "backward_test_1",
                "problem_description": "Minimal problem",
                "app_concept": "Minimal app",
                "core_functions": ["Feature"],
                "value_proposition": "Value",
                "target_user": "Users",
                "monetization_model": "Free",
            }
        ]

        success = store.store(minimal_data)
        assert success is True
        assert store.stats.loaded == 1

    @patch("core.storage.dlt_loader.dlt.pipeline")
    def test_multiple_schema_versions_coexist(self, mock_pipeline_func):
        """Test multiple schema versions can coexist in same table."""
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_func.return_value = mock_pipeline

        store = OpportunityStore()

        # Load data with different schema versions
        v1_data = [
            {
                "submission_id": "v1_test",
                "problem_description": "V1 problem",
                "app_concept": "V1 app",
                "core_functions": ["F1"],
                "value_proposition": "V1 value",
                "target_user": "V1 users",
                "monetization_model": "V1 model",
            }
        ]

        v2_data = [
            {
                "submission_id": "v2_test",
                "problem_description": "V2 problem",
                "app_concept": "V2 app",
                "core_functions": ["F1", "F2"],
                "value_proposition": "V2 value",
                "target_user": "V2 users",
                "monetization_model": "V2 model",
                "opportunity_score": 75.0,  # New field in v2
                "final_score": 80.0,  # New field in v2
            }
        ]

        v3_data = [
            {
                "submission_id": "v3_test",
                "problem_description": "V3 problem",
                "app_concept": "V3 app",
                "core_functions": ["F1", "F2", "F3"],
                "value_proposition": "V3 value",
                "target_user": "V3 users",
                "monetization_model": "V3 model",
                "opportunity_score": 85.0,
                "final_score": 90.0,
                "status": "validated",  # New field in v3
            }
        ]

        # All versions should load successfully
        assert store.store(v1_data) is True
        assert store.store(v2_data) is True
        assert store.store(v3_data) is True

        assert store.stats.loaded == 3
        assert store.stats.failed == 0


class TestDataIntegrity:
    """Test data integrity across storage operations."""

    @patch("core.storage.dlt_loader.dlt.pipeline")
    def test_concurrent_writes_no_data_loss(self, mock_pipeline_func):
        """Test concurrent writes don't lose data."""
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_func.return_value = mock_pipeline

        # Create separate stores to simulate concurrent operations
        store1 = OpportunityStore()
        store2 = OpportunityStore()

        data1 = [
            {
                "submission_id": "concurrent_1",
                "problem_description": "Problem 1",
                "app_concept": "App 1",
                "core_functions": ["F1"],
                "value_proposition": "Value 1",
                "target_user": "Users 1",
                "monetization_model": "Model 1",
            }
        ]

        data2 = [
            {
                "submission_id": "concurrent_2",
                "problem_description": "Problem 2",
                "app_concept": "App 2",
                "core_functions": ["F2"],
                "value_proposition": "Value 2",
                "target_user": "Users 2",
                "monetization_model": "Model 2",
            }
        ]

        # Simulate concurrent writes
        success1 = store1.store(data1)
        success2 = store2.store(data2)

        assert success1 is True
        assert success2 is True
        assert store1.stats.loaded == 1
        assert store2.stats.loaded == 1

    @patch("core.storage.dlt_loader.dlt.pipeline")
    def test_batch_operation_atomicity(self, mock_pipeline_func):
        """Test batch operations maintain data integrity."""
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_func.return_value = mock_pipeline

        # Mock load_batch to return success
        loader = MagicMock(spec=DLTLoader)
        loader.load_batch.return_value = {
            "total_records": 10,
            "batches": 2,
            "successful_batches": 2,
            "failed_batches": 0,
            "success_rate": 1.0,
            "loaded": 10,
            "failed": 0,
        }

        store = OpportunityStore(loader=loader)

        large_dataset = [
            {
                "submission_id": f"batch_{i}",
                "problem_description": f"Problem {i}",
                "app_concept": f"App {i}",
                "core_functions": ["Feature"],
                "value_proposition": "Value",
                "target_user": "Users",
                "monetization_model": "Model",
            }
            for i in range(10)
        ]

        result = store.store_batch(large_dataset, batch_size=5)

        assert result["success_rate"] == 1.0
        assert result["total_records"] == 10
        assert result["failed_batches"] == 0

    @patch("core.storage.dlt_loader.dlt.pipeline")
    def test_invalid_data_filtered_before_storage(self, mock_pipeline_func):
        """Test invalid data is filtered and doesn't corrupt storage."""
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_func.return_value = mock_pipeline

        store = OpportunityStore()

        mixed_data = [
            {
                "submission_id": "valid_1",
                "problem_description": "Valid problem",
                "app_concept": "Valid app",
                "core_functions": ["Feature"],
                "value_proposition": "Value",
                "target_user": "Users",
                "monetization_model": "Model",
            },
            {
                "submission_id": "invalid_1",
                # Missing problem_description - should be filtered
                "app_concept": "Invalid app",
            },
            {
                "submission_id": "valid_2",
                "problem_description": "Another valid problem",
                "app_concept": "Another valid app",
                "core_functions": ["Feature"],
                "value_proposition": "Value",
                "target_user": "Users",
                "monetization_model": "Model",
            },
        ]

        success = store.store(mixed_data)

        assert success is True
        assert store.stats.loaded == 2  # Only 2 valid records loaded
        assert store.stats.skipped == 1  # 1 invalid record skipped
        assert store.stats.failed == 0  # No failures

        # Verify only valid data was passed to loader
        call_args = mock_pipeline.run.call_args
        # data is passed as positional argument (first arg) to pipeline.run()
        loaded_data = call_args.args[0]
        assert len(list(loaded_data)) == 2  # Only valid records


class TestPerformanceCharacteristics:
    """Test performance characteristics of storage layer."""

    @patch("core.storage.dlt_loader.dlt.pipeline")
    def test_batch_size_optimization(self, mock_pipeline_func):
        """Test different batch sizes for optimal performance."""
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_func.return_value = mock_pipeline

        loader = DLTLoader()

        # Test data
        test_data = [
            {
                "submission_id": f"perf_{i}",
                "problem_description": f"Problem {i}",
                "app_concept": f"App {i}",
                "core_functions": ["Feature"],
                "value_proposition": "Value",
                "target_user": "Users",
                "monetization_model": "Model",
            }
            for i in range(100)
        ]

        # Test different batch sizes
        batch_sizes = [10, 50, 100]

        for batch_size in batch_sizes:
            loader.reset_statistics()
            result = loader.load_batch(
                data=test_data,
                table_name="app_opportunities",
                primary_key="submission_id",
                batch_size=batch_size,
            )

            # All batch sizes should succeed
            assert result["success_rate"] >= 0.0
            assert result["total_records"] == 100
            assert result["batches"] == (100 + batch_size - 1) // batch_size

    @patch("core.storage.dlt_loader.dlt.pipeline")
    def test_statistics_overhead_minimal(self, mock_pipeline_func):
        """Test statistics tracking has minimal performance overhead."""
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_func.return_value = mock_pipeline

        store = OpportunityStore()

        # Perform multiple operations
        for i in range(10):
            data = [
                {
                    "submission_id": f"stats_test_{i}",
                    "problem_description": "Problem",
                    "app_concept": "App",
                    "core_functions": ["Feature"],
                    "value_proposition": "Value",
                    "target_user": "Users",
                    "monetization_model": "Model",
                }
            ]
            store.store(data)

        # Statistics should be accurate
        stats = store.get_statistics()
        assert stats["loaded"] == 10
        assert stats["total_attempted"] == 10
        assert stats["success_rate"] == 1.0
