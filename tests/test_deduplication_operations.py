#!/usr/bin/env python3
"""
Tests for SimpleDeduplicator database operations methods
Task 3: Database operations for semantic deduplication

This test file follows TDD approach - tests are written first, then implementation.
"""

import logging
import os

# Import the module under test
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from core.deduplication import SimpleDeduplicator
except ImportError:
    # Handle the case where the import path might be different
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
    from deduplication import SimpleDeduplicator

# Set up logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestSimpleDeduplicatorDatabaseOperations:
    """Test database operations methods of SimpleDeduplicator class"""

    @pytest.fixture
    def mock_supabase_client(self):
        """Create a mock Supabase client for testing"""
        mock_client = Mock()
        return mock_client

    @pytest.fixture
    def deduplicator(self, mock_supabase_client):
        """Create SimpleDeduplicator instance with mocked Supabase client"""
        with patch(
            "core.deduplication.create_client", return_value=mock_supabase_client
        ):
            return SimpleDeduplicator("test_url", "test_key")

    def test_find_existing_concept_success(self, deduplicator, mock_supabase_client):
        """Test successful find_existing_concept operation"""
        # Arrange
        fingerprint = "test_fingerprint_123"
        expected_data = {
            "id": 1,
            "concept_name": "Test Concept",
            "concept_fingerprint": fingerprint,
            "submission_count": 5,
            "created_at": "2024-01-01T00:00:00Z",
        }

        # Mock Supabase response
        mock_response = Mock()
        mock_response.data = [expected_data]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        # Act
        result = deduplicator.find_existing_concept(fingerprint)

        # Assert
        assert result == expected_data
        mock_supabase_client.table.assert_called_once_with("business_concepts")
        mock_supabase_client.table.return_value.select.assert_called_once_with("*")
        mock_supabase_client.table.return_value.select.return_value.eq.assert_called_once_with(
            "concept_fingerprint", fingerprint
        )

    def test_find_existing_concept_not_found(self, deduplicator, mock_supabase_client):
        """Test find_existing_concept when no concept exists"""
        # Arrange
        fingerprint = "nonexistent_fingerprint"

        # Mock empty response
        mock_response = Mock()
        mock_response.data = []
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        # Act
        result = deduplicator.find_existing_concept(fingerprint)

        # Assert
        assert result is None

    def test_find_existing_concept_database_error(
        self, deduplicator, mock_supabase_client
    ):
        """Test find_existing_concept handles database errors gracefully"""
        # Arrange
        fingerprint = "test_fingerprint"

        # Mock database error
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception(
            "Database error"
        )

        # Act
        result = deduplicator.find_existing_concept(fingerprint)

        # Assert
        assert result is None

    def test_create_business_concept_success(self, deduplicator, mock_supabase_client):
        """Test successful create_business_concept operation"""
        # Arrange
        concept_name = "New Business Concept"
        fingerprint = "new_fingerprint_456"
        opportunity_id = "opp_123"
        expected_id = 42

        # Mock the table calls using side_effect to handle different calls
        mock_exist_response = Mock()
        mock_exist_response.data = [{"id": opportunity_id}]  # Opportunity exists

        mock_insert_response = Mock()
        mock_insert_response.data = [{"id": expected_id}]

        # Create a sequence of mock responses for different table operations
        def table_side_effect(table_name):
            mock_table = Mock()
            if table_name == "opportunities_unified":
                # For opportunity existence check
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_exist_response
            elif table_name == "business_concepts":
                # For concept creation
                mock_table.insert.return_value.execute.return_value = mock_insert_response
            return mock_table

        mock_supabase_client.table.side_effect = table_side_effect

        # Act
        result = deduplicator.create_business_concept(
            concept_name, fingerprint, opportunity_id
        )

        # Assert
        assert result == expected_id
        # Should be called twice - once for opportunity check, once for insert
        assert mock_supabase_client.table.call_count == 2

    def test_create_business_concept_error(self, deduplicator, mock_supabase_client):
        """Test create_business_concept handles errors gracefully"""
        # Arrange
        concept_name = "Error Concept"
        fingerprint = "error_fingerprint"
        opportunity_id = "opp_error"

        # Mock database error
        mock_supabase_client.table.return_value.insert.return_value.execute.side_effect = Exception(
            "Insert failed"
        )

        # Act
        result = deduplicator.create_business_concept(
            concept_name, fingerprint, opportunity_id
        )

        # Assert
        assert result is None

    def test_update_concept_stats_success(self, deduplicator, mock_supabase_client):
        """Test successful update_concept_stats operation"""
        # Arrange
        concept_id = 123

        # Mock successful update response
        mock_response = Mock()
        mock_response.data = [{"id": concept_id}]
        mock_supabase_client.rpc.return_value.execute.return_value = mock_response

        # Act
        deduplicator.update_concept_stats(concept_id)

        # Assert
        mock_supabase_client.rpc.assert_called_once_with(
            "increment_concept_count", {"concept_id": concept_id}
        )

    def test_update_concept_stats_error(self, deduplicator, mock_supabase_client):
        """Test update_concept_stats handles errors gracefully"""
        # Arrange
        concept_id = 456

        # Mock RPC error
        mock_supabase_client.rpc.return_value.execute.side_effect = Exception(
            "RPC failed"
        )

        # Act & Assert - Should not raise exception
        deduplicator.update_concept_stats(concept_id)

    def test_mark_as_duplicate_success(self, deduplicator, mock_supabase_client):
        """Test successful mark_as_duplicate operation"""
        # Arrange
        opportunity_id = "opp_duplicate"
        concept_id = 789
        primary_opportunity_id = "opp_primary"

        # Mock opportunity existence check for _ensure_opportunity_exists
        def table_side_effect(table_name):
            mock_table = Mock()
            if table_name == "opportunities_unified":
                # For opportunity existence check
                mock_exist_response = Mock()
                mock_exist_response.data = [{"id": opportunity_id}]
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_exist_response
            return mock_table

        mock_supabase_client.table.side_effect = table_side_effect

        # Mock successful RPC response
        mock_response = Mock()
        mock_response.data = True  # RPC returns True, not a list
        mock_supabase_client.rpc.return_value.execute.return_value = mock_response

        # Act
        result = deduplicator.mark_as_duplicate(
            opportunity_id, concept_id, primary_opportunity_id
        )

        # Assert
        assert result is True
        mock_supabase_client.rpc.assert_called_once_with(
            "mark_opportunity_duplicate", {
                "p_opportunity_id": opportunity_id,
                "p_concept_id": concept_id,
                "p_primary_opportunity_id": primary_opportunity_id
            }
        )

    def test_mark_as_duplicate_error(self, deduplicator, mock_supabase_client):
        """Test mark_as_duplicate handles errors gracefully"""
        # Arrange
        opportunity_id = "opp_error"
        concept_id = 999
        primary_opportunity_id = "opp_primary_error"

        # Mock database error
        mock_supabase_client.rpc.return_value.execute.side_effect = Exception(
            "Update failed"
        )

        # Act
        result = deduplicator.mark_as_duplicate(
            opportunity_id, concept_id, primary_opportunity_id
        )

        # Assert
        assert result is False

    def test_mark_as_unique_success(self, deduplicator, mock_supabase_client):
        """Test successful mark_as_unique operation"""
        # Arrange
        opportunity_id = "opp_unique"
        concept_id = 321

        # Mock opportunity existence check for _ensure_opportunity_exists
        def table_side_effect(table_name):
            mock_table = Mock()
            if table_name == "opportunities_unified":
                # For opportunity existence check
                mock_exist_response = Mock()
                mock_exist_response.data = [{"id": opportunity_id}]
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_exist_response
            return mock_table

        mock_supabase_client.table.side_effect = table_side_effect

        # Mock successful RPC response
        mock_response = Mock()
        mock_response.data = True  # RPC returns True, not a list
        mock_supabase_client.rpc.return_value.execute.return_value = mock_response

        # Act
        result = deduplicator.mark_as_unique(opportunity_id, concept_id)

        # Assert
        assert result is True
        mock_supabase_client.rpc.assert_called_once_with(
            "mark_opportunity_unique", {
                "p_opportunity_id": opportunity_id,
                "p_concept_id": concept_id
            }
        )

    def test_mark_as_unique_error(self, deduplicator, mock_supabase_client):
        """Test mark_as_unique handles errors gracefully"""
        # Arrange
        opportunity_id = "opp_unique_error"
        concept_id = 654

        # Mock opportunity existence check for _ensure_opportunity_exists
        def table_side_effect(table_name):
            mock_table = Mock()
            if table_name == "opportunities_unified":
                # For opportunity existence check
                mock_exist_response = Mock()
                mock_exist_response.data = [{"id": opportunity_id}]
                mock_table.select.return_value.eq.return_value.execute.return_value = mock_exist_response
            return mock_table

        mock_supabase_client.table.side_effect = table_side_effect

        # Mock database error
        mock_supabase_client.rpc.return_value.execute.side_effect = Exception(
            "Update failed"
        )

        # Act
        result = deduplicator.mark_as_unique(opportunity_id, concept_id)

        # Assert
        assert result is False

    def test_fingerprint_generation_still_works(self, deduplicator):
        """Test that existing fingerprint generation functionality still works after adding database operations"""
        # Test the existing functionality from Task 2
        concept1 = "App idea: Food delivery service"
        concept2 = "app idea: food delivery service"  # Different case, spacing
        concept3 = "web app: Food delivery service"  # Different prefix

        fingerprint1 = deduplicator.generate_fingerprint(concept1)
        fingerprint2 = deduplicator.generate_fingerprint(concept2)
        fingerprint3 = deduplicator.generate_fingerprint(concept3)

        # Concepts 1 and 2 should have same fingerprint after normalization
        assert fingerprint1 == fingerprint2
        # Concept 3 should have different fingerprint (different core concept)
        assert fingerprint1 != fingerprint3

        # All fingerprints should be valid SHA256 hex strings (64 characters)
        assert len(fingerprint1) == 64
        assert all(c in "0123456789abcdef" for c in fingerprint1)


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
