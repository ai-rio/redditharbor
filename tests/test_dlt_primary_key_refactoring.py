#!/usr/bin/env python3
"""
Test Suite for DLT Primary Key Refactoring

This test suite validates that the DLT primary key refactoring is working correctly
and ensures no breaking changes have been introduced. It tests the centralized
constants module and validates that all DLT resources use the correct primary keys.

Critical for Phase 3 schema consolidation - ensures merge dispositions remain
functional after removing hard-coded primary key dependencies.
"""

import pytest
from unittest.mock import patch, MagicMock
from typing import Any, Dict, List

# Import the centralized constants module
from core.dlt import (
    PK_SUBMISSION_ID,
    PK_OPPORTUNITY_ID,
    PK_COMMENT_ID,
    PK_DISPLAY_NAME,
    PK_ID,
    validate_primary_key,
    get_resource_primary_key,
    get_table_primary_key,
    migrate_legacy_primary_key,
    validate_merge_disposition_compatibility,
    submission_resource_config,
    opportunity_resource_config,
    PrimaryKeyType
)


class TestPrimaryKeyConstants:
    """Test the primary key constants module."""

    def test_all_constants_defined(self):
        """Test that all expected primary key constants are defined."""
        assert PK_SUBMISSION_ID == "submission_id"
        assert PK_OPPORTUNITY_ID == "opportunity_id"
        assert PK_COMMENT_ID == "comment_id"
        assert PK_DISPLAY_NAME == "display_name"
        assert PK_ID == "id"

    def test_constants_are_unique(self):
        """Test that all primary key constants have unique values."""
        pk_values = [PK_SUBMISSION_ID, PK_OPPORTUNITY_ID, PK_COMMENT_ID, PK_DISPLAY_NAME, PK_ID]
        assert len(pk_values) == len(set(pk_values)), "Primary key constants must be unique"

    def test_validate_primary_key_success(self):
        """Test successful primary key validation."""
        assert validate_primary_key(PK_SUBMISSION_ID)
        assert validate_primary_key(PK_OPPORTUNITY_ID)
        assert validate_primary_key(PK_COMMENT_ID)
        assert validate_primary_key(PK_DISPLAY_NAME)
        assert validate_primary_key(PK_ID)

    def test_validate_primary_key_with_expected_type(self):
        """Test primary key validation with expected type."""
        assert validate_primary_key(PK_SUBMISSION_ID, PrimaryKeyType.SUBMISSION_ID)
        assert validate_primary_key(PK_OPPORTUNITY_ID, PrimaryKeyType.OPPORTUNITY_ID)
        assert validate_primary_key(PK_COMMENT_ID, PrimaryKeyType.COMMENT_ID)
        assert validate_primary_key(PK_DISPLAY_NAME, PrimaryKeyType.DISPLAY_NAME)
        assert validate_primary_key(PK_ID, PrimaryKeyType.ID)

    def test_validate_primary_key_invalid_key(self):
        """Test validation with invalid primary key."""
        with pytest.raises(ValueError, match="Unrecognized primary key"):
            validate_primary_key("invalid_key")

    def test_validate_primary_key_type_mismatch(self):
        """Test validation with correct key but wrong expected type."""
        with pytest.raises(ValueError, match="Primary key mismatch"):
            validate_primary_key(PK_SUBMISSION_ID, PrimaryKeyType.OPPORTUNITY_ID)

    def test_get_resource_primary_key_success(self):
        """Test successful resource primary key lookup."""
        assert get_resource_primary_key("app_opportunities") == PK_SUBMISSION_ID
        assert get_resource_primary_key("opportunity_analysis") == PK_SUBMISSION_ID
        assert get_resource_primary_key("workflow_results_with_costs") == PK_OPPORTUNITY_ID
        assert get_resource_primary_key("active_subreddits") == PK_DISPLAY_NAME
        assert get_resource_primary_key("validated_comments") == PK_ID

    def test_get_resource_primary_key_invalid_resource(self):
        """Test resource primary key lookup with invalid resource name."""
        with pytest.raises(KeyError, match="Resource 'invalid_resource' not found"):
            get_resource_primary_key("invalid_resource")

    def test_get_table_primary_key_success(self):
        """Test successful table primary key lookup."""
        assert get_table_primary_key("submissions") == PK_SUBMISSION_ID
        assert get_table_primary_key("app_opportunities") == PK_SUBMISSION_ID
        assert get_table_primary_key("workflow_results") == PK_OPPORTUNITY_ID
        assert get_table_primary_key("active_subreddits") == PK_DISPLAY_NAME

    def test_get_table_primary_key_invalid_table(self):
        """Test table primary key lookup with invalid table name."""
        with pytest.raises(KeyError, match="Table 'invalid_table' not found"):
            get_table_primary_key("invalid_table")

    def test_migrate_legacy_primary_key_success(self):
        """Test successful legacy primary key migration."""
        assert migrate_legacy_primary_key("submission_id") == PK_SUBMISSION_ID
        assert migrate_legacy_primary_key("opportunity_id") == PK_OPPORTUNITY_ID
        assert migrate_legacy_primary_key("comment_id") == PK_COMMENT_ID
        assert migrate_legacy_primary_key("display_name") == PK_DISPLAY_NAME
        assert migrate_legacy_primary_key("id") == PK_ID

    def test_migrate_legacy_primary_key_invalid_legacy(self):
        """Test legacy primary key migration with invalid legacy key."""
        with pytest.raises(KeyError, match="Legacy primary key 'invalid_legacy' not recognized"):
            migrate_legacy_primary_key("invalid_legacy")

    def test_validate_merge_disposition_compatibility_merge_success(self):
        """Test successful merge disposition validation with primary key."""
        assert validate_merge_disposition_compatibility("merge", PK_SUBMISSION_ID)

    def test_validate_merge_disposition_compatibility_merge_missing_key(self):
        """Test merge disposition validation without primary key (should fail)."""
        with pytest.raises(ValueError, match="Merge disposition requires a primary key"):
            validate_merge_disposition_compatibility("merge", None)

    def test_validate_merge_disposition_compatibility_non_merge_success(self):
        """Test non-merge disposition validation."""
        assert validate_merge_disposition_compatibility("append", None)
        assert validate_merge_disposition_compatibility("replace", None)
        assert validate_merge_disposition_compatibility("append", PK_SUBMISSION_ID)

    def test_submission_resource_config_merge(self):
        """Test submission resource configuration for merge disposition."""
        config = submission_resource_config("merge")
        assert config["write_disposition"] == "merge"
        assert config["primary_key"] == PK_SUBMISSION_ID

    def test_submission_resource_config_append(self):
        """Test submission resource configuration for append disposition."""
        config = submission_resource_config("append")
        assert config["write_disposition"] == "append"
        assert config["primary_key"] is None

    def test_opportunity_resource_config_merge(self):
        """Test opportunity resource configuration for merge disposition."""
        config = opportunity_resource_config("merge")
        assert config["write_disposition"] == "merge"
        assert config["primary_key"] == PK_OPPORTUNITY_ID

    def test_opportunity_resource_config_append(self):
        """Test opportunity resource configuration for append disposition."""
        config = opportunity_resource_config("append")
        assert config["write_disposition"] == "append"
        assert config["primary_key"] is None


class TestDLTResourceIntegration:
    """Test integration with actual DLT resources."""

    @patch('core.dlt_app_opportunities.dlt')
    def test_app_opportunities_resource_uses_constant(self, mock_dlt):
        """Test that app_opportunities resource uses centralized constant."""
        # Import the module to trigger resource decorator
        from core.dlt_app_opportunities import app_opportunities_resource

        # Check that the resource was created with the correct primary key
        mock_dlt.resource.assert_called_once()
        call_kwargs = mock_dlt.resource.call_args[1]
        assert call_kwargs["primary_key"] == PK_SUBMISSION_ID
        assert call_kwargs["write_disposition"] == "merge"

    @patch('core.dlt_collection.dlt')
    def test_collection_pipeline_uses_constant(self, mock_dlt):
        """Test that collection pipeline uses centralized constant."""
        from core.dlt_collection import load_to_supabase

        # Mock pipeline and test data
        mock_pipeline = MagicMock()
        mock_dlt.pipeline.return_value = mock_pipeline
        mock_pipeline.run.return_value = MagicMock(started_at="2024-01-01")

        test_posts = [
            {"submission_id": "test123", "title": "Test Post", "text": "Test content"}
        ]

        # Test merge mode (should use primary key)
        with patch('core.dlt_collection.create_dlt_pipeline', return_value=mock_pipeline):
            result = load_to_supabase(test_posts, write_mode="merge")

            # Verify pipeline.run was called with correct primary key
            mock_pipeline.run.assert_called_once()
            call_args = mock_pipeline.run.call_args
            assert call_args[1]["primary_key"] == PK_SUBMISSION_ID

    @patch('core.dlt_cost_tracking.dlt')
    def test_cost_tracking_resource_uses_constant(self, mock_dlt):
        """Test that cost tracking resource uses centralized constant."""
        # Import the module to trigger resource decorator
        from core.dlt_cost_tracking import workflow_results_with_cost_tracking

        # Check that the resource was created with the correct primary key
        mock_dlt.resource.assert_called_once()
        call_kwargs = mock_dlt.resource.call_args[1]
        assert call_kwargs["primary_key"] == PK_OPPORTUNITY_ID
        assert call_kwargs["write_disposition"] == "merge"

    @patch('core.dlt_reddit_source.dlt')
    def test_reddit_source_resources_use_constants(self, mock_dlt):
        """Test that reddit source resources use centralized constants."""
        from core.dlt_reddit_source import (
            active_subreddits,
            validated_comments,
            activity_trends
        )

        # Should have 3 resource calls
        assert mock_dlt.resource.call_count == 3

        # Extract all call arguments
        call_args_list = [call[1] for call in mock_dlt.resource.call_args_list]

        # Check active_subreddits resource
        active_subreddits_config = next(
            config for config in call_args_list
            if config.get("name") == "active_subreddits"
        )
        assert active_subreddits_config["primary_key"] == PK_DISPLAY_NAME

        # Check validated_comments resource
        validated_comments_config = next(
            config for config in call_args_list
            if config.get("name") == "validated_comments"
        )
        assert validated_comments_config["primary_key"] == PK_ID

        # Check activity_trends resource
        activity_trends_config = next(
            config for config in call_args_list
            if config.get("name") == "activity_trends"
        )
        assert activity_trends_config["primary_key"] == PK_DISPLAY_NAME


class TestBackwardCompatibility:
    """Test backward compatibility and migration scenarios."""

    def test_legacy_hardcoded_keys_still_work(self):
        """Test that legacy hard-coded keys can be migrated to constants."""
        legacy_mappings = {
            "submission_id": PK_SUBMISSION_ID,
            "opportunity_id": PK_OPPORTUNITY_ID,
            "comment_id": PK_COMMENT_ID,
            "display_name": PK_DISPLAY_NAME,
            "id": PK_ID,
        }

        for legacy_key, expected_constant in legacy_mappings.items():
            migrated_key = migrate_legacy_primary_key(legacy_key)
            assert migrated_key == expected_constant
            assert migrated_key == legacy_key  # Should be identical for now

    def test_merge_disposition_warnings(self):
        """Test that appropriate warnings are generated for mismatched configurations."""
        import warnings

        # Capture warnings
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")

            # This should generate a warning
            validate_merge_disposition_compatibility("append", PK_SUBMISSION_ID)

            # Check that warning was generated
            assert len(warning_list) > 0
            assert any(
                "Primary key specified with write_disposition 'append'" in str(w.message)
                for w in warning_list
            )


class TestTypeSafety:
    """Test type safety and validation."""

    def test_primary_key_type_literals(self):
        """Test that type literals are working correctly."""
        from typing import get_args

        # These should not raise type errors in a type checker
        submission_pk: str = PK_SUBMISSION_ID
        opportunity_pk: str = PK_OPPORTUNITY_ID

        assert submission_pk == "submission_id"
        assert opportunity_pk == "opportunity_id"

    def test_resource_config_return_types(self):
        """Test that resource config functions return correct types."""
        merge_config = submission_resource_config("merge")
        append_config = submission_resource_config("append")

        assert isinstance(merge_config, dict)
        assert isinstance(append_config, dict)
        assert "write_disposition" in merge_config
        assert "primary_key" in merge_config
        assert "write_disposition" in append_config
        assert "primary_key" in append_config


class TestPerformanceAndMemory:
    """Test performance and memory efficiency."""

    def test_constants_import_performance(self):
        """Test that importing constants is performant."""
        import time
        import importlib

        # Time the import
        start_time = time.time()
        importlib.import_module('core.dlt')
        import_time = time.time() - start_time

        # Should be very fast (< 10ms)
        assert import_time < 0.01, f"Import took {import_time}s, expected < 0.01s"

    def test_validation_performance(self):
        """Test that validation functions are performant."""
        import time

        # Test validation performance with many calls
        iterations = 10000
        start_time = time.time()

        for _ in range(iterations):
            validate_primary_key(PK_SUBMISSION_ID)
            get_resource_primary_key("app_opportunities")
            get_table_primary_key("submissions")

        total_time = time.time() - start_time
        avg_time_per_call = total_time / (iterations * 3)

        # Should be very fast per call (< 0.1ms)
        assert avg_time_per_call < 0.0001, f"Average validation took {avg_time_per_call}s, expected < 0.0001s"


# Test data for integration tests
TEST_SUBMISSION_DATA = [
    {
        "submission_id": "test_sub_1",
        "title": "Test Submission 1",
        "text": "This is a test submission",
        "subreddit": "test",
        "score": 10,
        "created_utc": 1640995200,
    }
]

TEST_OPPORTUNITY_DATA = [
    {
        "opportunity_id": "test_opp_1",
        "submission_id": "test_sub_1",
        "app_name": "Test App",
        "final_score": 75.0,
        "status": "scored",
    }
]

TEST_COST_DATA = [
    {
        "opportunity_id": "test_opp_1",
        "cost_tracking": {
            "model_used": "claude-haiku-4.5",
            "total_tokens": 1000,
            "total_cost_usd": 0.002,
            "timestamp": "2024-01-01T00:00:00Z",
        }
    }
]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])