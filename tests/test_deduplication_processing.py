"""
Test suite for process_opportunity method - Task 4 Implementation.
Following TDD: Write failing test first, then implementation.

Tests cover:
- process_opportunity() method complete workflow
- Validation of required fields
- Fingerprint generation and duplicate detection
- Creation of new business concepts
- Marking opportunities as duplicate/unique
- Comprehensive error handling
"""

from unittest.mock import Mock, patch

import pytest

# Import the module we're going to extend
try:
    from core.deduplication import SimpleDeduplicator
except ImportError:
    SimpleDeduplicator = None


class TestProcessOpportunity:
    """Test process_opportunity method."""

    def test_process_opportunity_success_unique(self):
        """Test successful processing of a unique opportunity."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        # Mock Supabase client and methods
        with patch("core.deduplication.create_client") as mock_create_client:
            mock_client = Mock()
            mock_create_client.return_value = mock_client

            # Mock find_existing_concept to return None (unique concept)
            with patch.object(SimpleDeduplicator, "find_existing_concept") as mock_find:
                mock_find.return_value = None

                # Mock create_business_concept to return new concept ID
                with patch.object(
                    SimpleDeduplicator, "create_business_concept"
                ) as mock_create:
                    mock_create.return_value = 123

                    # Mock mark_as_unique to return True
                    with patch.object(
                        SimpleDeduplicator, "mark_as_unique"
                    ) as mock_mark_unique:
                        mock_mark_unique.return_value = True

                        deduplicator = SimpleDeduplicator("test_url", "test_key")

                        opportunity = {
                            "id": "opp_123",
                            "app_concept": "Fitness tracking app for workouts",
                        }

                        result = deduplicator.process_opportunity(opportunity)

                        # Verify the result structure
                        assert result["success"] is True
                        assert result["is_duplicate"] is False
                        assert result["concept_id"] == 123
                        assert result["opportunity_id"] is not None  # UUID gets converted
                        assert result["fingerprint"] is not None
                        assert len(result["fingerprint"]) == 64
                        assert (
                            result["normalized_concept"]
                            == "fitness tracking app for workouts"
                        )
                        assert (
                            result["message"]
                            == "Processed unique opportunity successfully"
                        )

                        # Verify method calls
                        mock_find.assert_called_once()
                        mock_create.assert_called_once_with(
                            "fitness tracking app for workouts",
                            result["fingerprint"],
                            result["opportunity_id"],  # Use converted UUID
                        )
                        mock_mark_unique.assert_called_once_with(result["opportunity_id"], 123)

    def test_process_opportunity_success_duplicate(self):
        """Test successful processing of a duplicate opportunity."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch("core.deduplication.create_client") as mock_create_client:
            mock_client = Mock()
            mock_create_client.return_value = mock_client

            # Mock find_existing_concept to return existing concept
            existing_concept = {
                "id": 456,
                "concept_name": "fitness tracking app for workouts",
                "concept_fingerprint": "abcd1234...",  # Updated field name
                "submission_count": 3,  # Updated field name
                "created_at": "2024-01-01T00:00:00Z",
                "primary_opportunity_id": "opp_123",  # Updated field name
            }
            with patch.object(SimpleDeduplicator, "find_existing_concept") as mock_find:
                mock_find.return_value = existing_concept

                # Mock update_concept_stats and mark_as_duplicate
                with patch.object(
                    SimpleDeduplicator, "update_concept_stats"
                ) as mock_update_stats:
                    with patch.object(
                        SimpleDeduplicator, "mark_as_duplicate"
                    ) as mock_mark_duplicate:
                        mock_mark_duplicate.return_value = True

                        deduplicator = SimpleDeduplicator("test_url", "test_key")

                        opportunity = {
                            "id": "opp_456",
                            "app_concept": "Fitness Tracking App for Workouts",  # Same concept, different formatting
                        }

                        result = deduplicator.process_opportunity(opportunity)

                        # Verify the result structure
                        assert result["success"] is True
                        assert result["is_duplicate"] is True
                        assert result["concept_id"] == 456
                        assert result["opportunity_id"] is not None  # UUID gets converted
                        assert result["fingerprint"] is not None
                        assert (
                            result["normalized_concept"]
                            == "fitness tracking app for workouts"
                        )
                        assert (
                            result["message"]
                            == "Processed duplicate opportunity successfully"
                        )

                        # Verify method calls
                        mock_find.assert_called_once()
                        mock_update_stats.assert_called_once_with(456)
                        mock_mark_duplicate.assert_called_once_with(
                            result["opportunity_id"], 456, "opp_123"
                        )  # primary_opportunity_id from existing concept

    def test_process_opportunity_missing_required_fields(self):
        """Test handling of missing required fields."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch("core.deduplication.create_client"):
            deduplicator = SimpleDeduplicator("test_url", "test_key")

            # Test missing 'id' field
            opportunity_missing_id = {"app_concept": "Fitness tracking app"}

            result = deduplicator.process_opportunity(opportunity_missing_id)
            assert result["success"] is False
            assert result["error"] == "Missing required field: id"
            assert result["opportunity_id"] is None

            # Test missing 'app_concept' field
            opportunity_missing_concept = {"id": "opp_123"}

            result = deduplicator.process_opportunity(opportunity_missing_concept)
            assert result["success"] is False
            assert result["error"] == "Missing required field: app_concept"
            assert result["opportunity_id"] is not None  # UUID gets converted

            # Test empty values
            opportunity_empty_values = {"id": "", "app_concept": "   "}

            result = deduplicator.process_opportunity(opportunity_empty_values)
            assert result["success"] is False
            assert "Missing required field" in result["error"]

    def test_process_opportunity_empty_concept_after_normalization(self):
        """Test handling of concepts that become empty after normalization."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch("core.deduplication.create_client"):
            deduplicator = SimpleDeduplicator("test_url", "test_key")

            opportunity = {
                "id": "opp_123",
                "app_concept": "   ",  # Only whitespace
            }

            result = deduplicator.process_opportunity(opportunity)
            assert result["success"] is False
            assert result["error"] == "Concept becomes empty after normalization"
            assert result["opportunity_id"] is not None  # UUID gets converted

    def test_process_opportunity_database_errors(self):
        """Test handling of database operation errors."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch("core.deduplication.create_client"):
            deduplicator = SimpleDeduplicator("test_url", "test_key")

            # Mock find_existing_concept to raise exception
            with patch.object(SimpleDeduplicator, "find_existing_concept") as mock_find:
                mock_find.side_effect = Exception("Database connection failed")

                opportunity = {"id": "opp_123", "app_concept": "Fitness tracking app"}

                result = deduplicator.process_opportunity(opportunity)
                assert result["success"] is False
                assert "Database connection failed" in result["error"]
                assert result["opportunity_id"] is not None  # UUID gets converted

    def test_process_opportunity_create_concept_failure(self):
        """Test handling when creating new business concept fails."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch("core.deduplication.create_client"):
            deduplicator = SimpleDeduplicator("test_url", "test_key")

            # Mock find_existing_concept to return None (unique)
            with patch.object(SimpleDeduplicator, "find_existing_concept") as mock_find:
                mock_find.return_value = None

                # Mock create_business_concept to return None (failure)
                with patch.object(
                    SimpleDeduplicator, "create_business_concept"
                ) as mock_create:
                    mock_create.return_value = None

                    opportunity = {
                        "id": "opp_123",
                        "app_concept": "Fitness tracking app",
                    }

                    result = deduplicator.process_opportunity(opportunity)
                    assert result["success"] is False
                    assert "Failed to create business concept" in result["error"]
                    assert result["opportunity_id"] is not None  # UUID gets converted

    def test_process_opportunity_mark_unique_failure(self):
        """Test handling when marking as unique fails."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch("core.deduplication.create_client"):
            deduplicator = SimpleDeduplicator("test_url", "test_key")

            # Mock find_existing_concept to return None (unique)
            with patch.object(SimpleDeduplicator, "find_existing_concept") as mock_find:
                mock_find.return_value = None

                # Mock create_business_concept to succeed
                with patch.object(
                    SimpleDeduplicator, "create_business_concept"
                ) as mock_create:
                    mock_create.return_value = 123

                    # Mock mark_as_unique to return False (failure)
                    with patch.object(
                        SimpleDeduplicator, "mark_as_unique"
                    ) as mock_mark_unique:
                        mock_mark_unique.return_value = False

                        opportunity = {
                            "id": "opp_123",
                            "app_concept": "Fitness tracking app",
                        }

                        result = deduplicator.process_opportunity(opportunity)
                        assert result["success"] is False
                        assert "Failed to mark opportunity as unique" in result["error"]
                        assert result["opportunity_id"] is not None  # UUID gets converted

    def test_process_opportunity_mark_duplicate_failure(self):
        """Test handling when marking as duplicate fails."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch("core.deduplication.create_client"):
            deduplicator = SimpleDeduplicator("test_url", "test_key")

            # Mock find_existing_concept to return existing concept
            existing_concept = {
                "id": 456,
                "concept_name": "fitness tracking app",
                "concept_fingerprint": "abcd1234...",
            }
            with patch.object(SimpleDeduplicator, "find_existing_concept") as mock_find:
                mock_find.return_value = existing_concept

                # Mock update_concept_stats to succeed
                with patch.object(SimpleDeduplicator, "update_concept_stats"):
                    # Mock mark_as_duplicate to return False (failure)
                    with patch.object(
                        SimpleDeduplicator, "mark_as_duplicate"
                    ) as mock_mark_duplicate:
                        mock_mark_duplicate.return_value = False

                        opportunity = {
                            "id": "opp_456",
                            "app_concept": "fitness tracking app",
                        }

                        result = deduplicator.process_opportunity(opportunity)
                        assert result["success"] is False
                        assert (
                            "Failed to mark opportunity as duplicate" in result["error"]
                        )
                        assert result["opportunity_id"] is not None  # UUID gets converted

    def test_process_opportunity_comprehensive_result_structure(self):
        """Test that result contains all expected fields."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch("core.deduplication.create_client"):
            deduplicator = SimpleDeduplicator("test_url", "test_key")

            # Mock find_existing_concept to return None for unique processing
            with patch.object(SimpleDeduplicator, "find_existing_concept") as mock_find:
                mock_find.return_value = None

                # Mock all subsequent operations to succeed
                with patch.object(
                    SimpleDeduplicator, "create_business_concept"
                ) as mock_create:
                    mock_create.return_value = 123
                    with patch.object(
                        SimpleDeduplicator, "mark_as_unique"
                    ) as mock_mark_unique:
                        mock_mark_unique.return_value = True

                        opportunity = {
                            "id": "opp_123",
                            "app_concept": "Fitness tracking app",
                        }

                        result = deduplicator.process_opportunity(opportunity)

                        # Verify all expected fields are present
                        expected_fields = [
                            "success",
                            "is_duplicate",
                            "concept_id",
                            "opportunity_id",
                            "fingerprint",
                            "normalized_concept",
                            "message",
                            "processing_time",
                        ]
                        for field in expected_fields:
                            assert field in result, f"Missing field: {field}"

                        # Verify field types and constraints
                        assert isinstance(result["success"], bool)
                        assert isinstance(result["is_duplicate"], bool)
                        assert isinstance(result["concept_id"], int)
                        assert isinstance(result["opportunity_id"], str)
                        assert isinstance(result["fingerprint"], str)
                        assert isinstance(result["normalized_concept"], str)
                        assert isinstance(result["message"], str)
                        assert isinstance(result["processing_time"], float)
                        assert result["processing_time"] >= 0

    def test_process_opportunity_performance_logging(self):
        """Test that processing time is logged and reasonable."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch("core.deduplication.create_client"):
            deduplicator = SimpleDeduplicator("test_url", "test_key")

            with patch.object(SimpleDeduplicator, "find_existing_concept") as mock_find:
                mock_find.return_value = None
                with patch.object(
                    SimpleDeduplicator, "create_business_concept"
                ) as mock_create:
                    mock_create.return_value = 123
                    with patch.object(
                        SimpleDeduplicator, "mark_as_unique"
                    ) as mock_mark_unique:
                        mock_mark_unique.return_value = True

                        opportunity = {
                            "id": "opp_123",
                            "app_concept": "Fitness tracking app",
                        }

                        result = deduplicator.process_opportunity(opportunity)

                        # Processing should be fast (less than 1 second for mock operations)
                        assert result["processing_time"] < 1.0
                        assert result["processing_time"] > 0


class TestProcessOpportunityIntegration:
    """Integration tests for process_opportunity with real workflow."""

    def test_process_opportunity_realistic_concept_variations(self):
        """Test processing with realistic concept variations from Reddit."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch("core.deduplication.create_client"):
            deduplicator = SimpleDeduplicator("test_url", "test_key")

            # Test various realistic Reddit app concept formats
            test_cases = [
                {
                    "input": {
                        "id": "opp_1",
                        "app_concept": "  App IDEA:   FitnessFAQ   for  Tracking   Workouts  ",
                    },
                    "expected_normalized": "idea: fitnessfaq for tracking workouts",
                },
                {
                    "input": {
                        "id": "opp_2",
                        "app_concept": "Mobile App: Meal Prepper Pro",
                    },
                    "expected_normalized": "app: meal prepper pro",
                },
                {
                    "input": {
                        "id": "opp_3",
                        "app_concept": "Web app for meditation guide",
                    },
                    "expected_normalized": "app for meditation guide",
                },
            ]

            for case in test_cases:
                with patch.object(
                    SimpleDeduplicator, "find_existing_concept"
                ) as mock_find:
                    mock_find.return_value = None
                    with patch.object(
                        SimpleDeduplicator, "create_business_concept"
                    ) as mock_create:
                        mock_create.return_value = 100 + int(
                            case["input"]["id"].split("_")[1]
                        )
                        with patch.object(
                            SimpleDeduplicator, "mark_as_unique"
                        ) as mock_mark_unique:
                            mock_mark_unique.return_value = True

                            result = deduplicator.process_opportunity(case["input"])

                            assert result["success"] is True
                            assert (
                                result["normalized_concept"]
                                == case["expected_normalized"]
                            )
                            assert result["is_duplicate"] is False
