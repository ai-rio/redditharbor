#!/usr/bin/env python3
"""
Tests for AI Profiler Deduplication Functions

This module tests the AI profiler deduplication functionality that ensures
semantic consistency of core_functions arrays across duplicate submissions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict, List
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import functions to test
from scripts.core.batch_opportunity_scoring import (
    should_run_profiler_analysis,
    copy_profiler_from_primary,
    update_concept_profiler_stats
)


class TestShouldRunProfilerAnalysis:
    """Test cases for should_run_profiler_analysis function."""

    @patch('scripts.core.batch_opportunity_scoring.create_client')
    def test_should_run_profiler_unique_submission(self, mock_create_client):
        """Test that unique submissions should run profiler analysis."""
        # Setup mock Supabase client
        mock_supabase = Mock()
        mock_create_client.return_value = mock_supabase

        # Mock response for opportunities_unified table (no business_concept_id)
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"submission_id": "test123"}]
        )

        # Test submission
        submission = {
            "submission_id": "test123",
            "title": "Test submission"
        }

        # Execute function
        should_run, concept_id = should_run_profiler_analysis(submission, mock_supabase)

        # Assertions
        assert should_run is True
        assert concept_id is None

    @patch('scripts.core.batch_opportunity_scoring.create_client')
    def test_should_run_profiler_duplicate_with_existing_profile(self, mock_create_client):
        """Test that duplicates with existing AI profiles should skip profiling."""
        # Setup mock Supabase client
        mock_supabase = Mock()
        mock_create_client.return_value = mock_supabase

        # Mock response for opportunities_unified table (has business_concept_id)
        opportunities_response = Mock()
        opportunities_response.data = [{"business_concept_id": "456"}]

        # Mock response for business_concepts table (has_ai_profiling=True)
        concept_response = Mock()
        concept_response.data = [{"has_ai_profiling": True}]

        # Set up the mock to return different responses for different calls
        mock_execute = Mock()
        mock_execute.side_effect = [
            opportunities_response,  # First call (opportunities_unified)
            concept_response         # Second call (business_concepts)
        ]

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute = mock_execute

        # Test submission
        submission = {
            "submission_id": "test123",
            "title": "Test submission"
        }

        # Execute function
        should_run, concept_id = should_run_profiler_analysis(submission, mock_supabase)

        # Assertions
        assert should_run is False
        assert concept_id == "456"

    @patch('scripts.core.batch_opportunity_scoring.create_client')
    def test_should_run_profiler_duplicate_without_existing_profile(self, mock_create_client):
        """Test that duplicates without existing AI profiles should run profiling."""
        # Setup mock Supabase client
        mock_supabase = Mock()
        mock_create_client.return_value = mock_supabase

        # Mock response for opportunities_unified table (has business_concept_id)
        opportunities_response = Mock()
        opportunities_response.data = [{"business_concept_id": "456"}]

        # Mock response for business_concepts table (has_ai_profiling=False)
        concept_response = Mock()
        concept_response.data = [{"has_ai_profiling": False}]

        # Set up the mock to return different responses for different calls
        mock_execute = Mock()
        mock_execute.side_effect = [
            opportunities_response,  # First call (opportunities_unified)
            concept_response         # Second call (business_concepts)
        ]

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute = mock_execute

        # Test submission
        submission = {
            "submission_id": "test123",
            "title": "Test submission"
        }

        # Execute function
        should_run, concept_id = should_run_profiler_analysis(submission, mock_supabase)

        # Assertions
        assert should_run is True
        assert concept_id == "456"

    @patch('scripts.core.batch_opportunity_scoring.create_client')
    def test_should_run_profiler_missing_submission_id(self, mock_create_client):
        """Test handling of submissions missing submission_id."""
        # Setup mock Supabase client
        mock_supabase = Mock()
        mock_create_client.return_value = mock_supabase

        # Test submission without submission_id
        submission = {
            "title": "Test submission",
            "id": "fallback_id"
        }

        # Execute function
        should_run, concept_id = should_run_profiler_analysis(submission, mock_supabase)

        # Assertions - should default to running analysis
        assert should_run is True
        assert concept_id is None

    @patch('scripts.core.batch_opportunity_scoring.create_client')
    def test_should_run_profiler_database_error(self, mock_create_client):
        """Test handling of database errors during deduplication check."""
        # Setup mock Supabase client
        mock_supabase = Mock()
        mock_create_client.return_value = mock_supabase

        # Mock database error
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("Database error")

        # Test submission
        submission = {
            "submission_id": "test123",
            "title": "Test submission"
        }

        # Execute function
        should_run, concept_id = should_run_profiler_analysis(submission, mock_supabase)

        # Assertions - should default to running analysis on error
        assert should_run is True
        assert concept_id is None


class TestCopyProfilerFromPrimary:
    """Test cases for copy_profiler_from_primary function."""

    @patch('scripts.core.batch_opportunity_scoring.create_client')
    def test_copy_profiler_success(self, mock_create_client):
        """Test successful copying of AI profile from primary opportunity."""
        # Setup mock Supabase client
        mock_supabase = Mock()
        mock_create_client.return_value = mock_supabase

        # Mock primary AI profile data
        primary_profile = {
            "opportunity_id": "opp_primary123",
            "submission_id": "primary123",
            "app_name": "Test App",
            "core_functions": "['Function 1', 'Function 2', 'Function 3']",
            "value_proposition": "Test value proposition",
            "problem_description": "Test problem",
            "app_concept": "Test concept",
            "target_user": "Test user",
            "monetization_model": "Test monetization",
            "final_score": 75.0,
            "monetization_potential": 80.0,
            "market_demand": 70.0,
            "pain_intensity": 85.0,
            "market_gap": 60.0,
            "technical_feasibility": 90.0
        }

        # Mock database response
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(
            data=[primary_profile]
        )

        # Test data
        submission = {
            "submission_id": "duplicate456",
            "id": "duplicate456"
        }
        concept_id = "concept789"

        # Execute function
        result = copy_profiler_from_primary(submission, concept_id, mock_supabase)

        # Assertions
        assert result is not None
        assert result["app_name"] == "Test App"
        assert result["core_functions"] == "['Function 1', 'Function 2', 'Function 3']"
        assert result["value_proposition"] == "Test value proposition"
        assert result["copied_from_primary"] is True
        assert result["primary_opportunity_id"] == "opp_primary123"
        assert result["business_concept_id"] == concept_id
        assert "copy_timestamp" in result

    @patch('scripts.core.batch_opportunity_scoring.create_client')
    def test_copy_profiler_no_primary_found(self, mock_create_client):
        """Test handling when no primary AI profile is found."""
        # Setup mock Supabase client
        mock_supabase = Mock()
        mock_create_client.return_value = mock_supabase

        # Mock empty database response
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(
            data=[]
        )

        # Test data
        submission = {
            "submission_id": "duplicate456",
            "id": "duplicate456"
        }
        concept_id = "concept789"

        # Execute function
        result = copy_profiler_from_primary(submission, concept_id, mock_supabase)

        # Assertions
        assert result == {}

    @patch('scripts.core.batch_opportunity_scoring.create_client')
    def test_copy_profiler_database_error(self, mock_create_client):
        """Test handling of database errors during profile copying."""
        # Setup mock Supabase client
        mock_supabase = Mock()
        mock_create_client.return_value = mock_supabase

        # Mock database error
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("Database error")

        # Test data
        submission = {
            "submission_id": "duplicate456",
            "id": "duplicate456"
        }
        concept_id = "concept789"

        # Execute function
        result = copy_profiler_from_primary(submission, concept_id, mock_supabase)

        # Assertions
        assert result == {}

    @patch('scripts.core.batch_opportunity_scoring.create_client')
    def test_copy_profiler_handles_mock_objects(self, mock_create_client):
        """Test handling of Mock objects in database responses (for testing)."""
        # Setup mock Supabase client
        mock_supabase = Mock()
        mock_create_client.return_value = mock_supabase

        # Mock response that simulates Mock object behavior
        mock_data = Mock()
        mock_data.__iter__ = Mock(return_value=iter([{
            "app_name": "Test App",
            "core_functions": "['Function 1', 'Function 2']",
            "value_proposition": "Test value",
            "opportunity_id": "opp_primary"
        }]))

        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(
            data=mock_data
        )

        # Test data
        submission = {"submission_id": "test123", "id": "test123"}
        concept_id = "concept456"

        # Execute function - should handle Mock objects gracefully
        result = copy_profiler_from_primary(submission, concept_id, mock_supabase)

        # Assertions
        assert result is not None
        assert "app_name" in result
        assert "core_functions" in result

    @patch('scripts.core.batch_opportunity_scoring.create_client')
    def test_copy_profiler_multiple_primary_profiles(self, mock_create_client):
        """Test handling when multiple primary profiles exist (should pick most recent)."""
        # Setup mock Supabase client
        mock_supabase = Mock()
        mock_create_client.return_value = mock_supabase

        # Mock multiple AI profiles with different timestamps
        profiles = [
            {
                "opportunity_id": "opp_older",
                "app_name": "Older App",
                "core_functions": "['Function 1']",
                "value_proposition": "Older value",
                "processed_at": "2025-01-01T00:00:00Z"
            },
            {
                "opportunity_id": "opp_newer",
                "app_name": "Newer App",
                "core_functions": "['Function 1', 'Function 2']",
                "value_proposition": "Newer value",
                "processed_at": "2025-01-02T00:00:00Z"
            }
        ]

        profile_response = Mock()
        profile_response.data = profiles

        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = profile_response

        # Test data
        submission = {"submission_id": "test123", "id": "test123"}
        concept_id = "concept456"

        # Execute function
        result = copy_profiler_from_primary(submission, concept_id, mock_supabase)

        # Assertions - should pick the most recent profile (based on processed_at)
        assert result is not None
        assert result["app_name"] == "Newer App"
        assert result["primary_opportunity_id"] == "opp_newer"


class TestUpdateConceptProfilerStats:
    """Test cases for update_concept_profiler_stats function."""

    @patch('scripts.core.batch_opportunity_scoring.create_client')
    def test_update_concept_profiler_stats_success(self, mock_create_client):
        """Test successful update of concept profiler statistics."""
        # Setup mock Supabase client
        mock_supabase = Mock()
        mock_create_client.return_value = mock_supabase

        # Mock successful RPC response
        mock_supabase.rpc.return_value.execute.return_value = Mock(
            data=[{"update_profiler_analysis_tracking": True}]
        )

        # Test data - use integer concept_id
        concept_id = 123
        ai_profile = {
            "final_score": 75.0,
            "app_name": "Test App",
            "core_functions": "['Function 1', 'Function 2']"
        }

        # Execute function
        update_concept_profiler_stats(concept_id, ai_profile, mock_supabase)

        # Verify RPC call was made correctly
        mock_supabase.rpc.assert_called_once_with("update_profiler_analysis_tracking", {
            "p_concept_id": int(concept_id),
            "p_has_analysis": True,
            "p_profiler_score": 75.0
        })

    @patch('scripts.core.batch_opportunity_scoring.create_client')
    def test_update_concept_profiler_stats_missing_score(self, mock_create_client):
        """Test handling when AI profile missing final_score."""
        # Setup mock Supabase client
        mock_supabase = Mock()
        mock_create_client.return_value = mock_supabase

        # Mock successful RPC response
        mock_supabase.rpc.return_value.execute.return_value = Mock(
            data=[{"update_profiler_analysis_tracking": True}]
        )

        # Test data without final_score - use integer concept_id
        concept_id = 123
        ai_profile = {
            "app_name": "Test App",
            "core_functions": "['Function 1', 'Function 2']"
        }

        # Execute function
        update_concept_profiler_stats(concept_id, ai_profile, mock_supabase)

        # Verify RPC call was made with None score
        mock_supabase.rpc.assert_called_once_with("update_profiler_analysis_tracking", {
            "p_concept_id": int(concept_id),
            "p_has_analysis": True,
            "p_profiler_score": None
        })

    @patch('scripts.core.batch_opportunity_scoring.create_client')
    def test_update_concept_profiler_stats_rpc_failure(self, mock_create_client):
        """Test handling when RPC call returns failure."""
        # Setup mock Supabase client
        mock_supabase = Mock()
        mock_create_client.return_value = mock_supabase

        # Mock failed RPC response
        mock_supabase.rpc.return_value.execute.return_value = Mock(
            data=[{"update_profiler_analysis_tracking": False}]
        )

        # Test data - use integer concept_id
        concept_id = 123
        ai_profile = {"final_score": 75.0}

        # Execute function - should not raise exception
        update_concept_profiler_stats(concept_id, ai_profile, mock_supabase)

        # Verify RPC call was made
        mock_supabase.rpc.assert_called_once()

    @patch('scripts.core.batch_opportunity_scoring.create_client')
    def test_update_concept_profiler_stats_database_error(self, mock_create_client):
        """Test handling of database errors during stats update."""
        # Setup mock Supabase client
        mock_supabase = Mock()
        mock_create_client.return_value = mock_supabase

        # Mock database error
        mock_supabase.rpc.return_value.execute.side_effect = Exception("Database error")

        # Test data - use integer concept_id
        concept_id = 123
        ai_profile = {"final_score": 75.0}

        # Execute function - should not raise exception
        update_concept_profiler_stats(concept_id, ai_profile, mock_supabase)

        # Verify RPC call was attempted
        mock_supabase.rpc.assert_called_once()

    @patch('scripts.core.batch_opportunity_scoring.create_client')
    def test_update_concept_profiler_stats_no_response_data(self, mock_create_client):
        """Test handling when RPC response has no data."""
        # Setup mock Supabase client
        mock_supabase = Mock()
        mock_create_client.return_value = mock_supabase

        # Mock empty RPC response
        mock_supabase.rpc.return_value.execute.return_value = Mock(data=None)

        # Test data - use integer concept_id
        concept_id = 123
        ai_profile = {"final_score": 75.0}

        # Execute function - should not raise exception
        update_concept_profiler_stats(concept_id, ai_profile, mock_supabase)

        # Verify RPC call was made
        mock_supabase.rpc.assert_called_once()


class TestIntegration:
    """Integration tests for profiler deduplication functions."""

    @patch('scripts.core.batch_opportunity_scoring.create_client')
    def test_deduplication_workflow(self, mock_create_client):
        """Test complete deduplication workflow."""
        # Setup mock Supabase client
        mock_supabase = Mock()
        mock_create_client.return_value = mock_supabase

        # Setup scenario: duplicate submission with existing profile
        # Step 1: should_run_profiler_analysis returns False (skip analysis)
        opportunities_response = Mock()
        concept_response = Mock()

        opportunities_response.data = [{"business_concept_id": "456"}]
        concept_response.data = [{"has_ai_profiling": True}]

        mock_execute = Mock()
        mock_execute.side_effect = [
            opportunities_response,  # opportunities_unified lookup
            concept_response         # business_concepts lookup
        ]

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute = mock_execute

        submission = {"submission_id": "duplicate123", "title": "Duplicate"}

        # Step 1: Check if should run analysis
        should_run, concept_id = should_run_profiler_analysis(submission, mock_supabase)

        assert should_run is False
        assert concept_id == "456"

        # Step 2: Copy profile from primary
        primary_profile = {
            "app_name": "Test App",
            "core_functions": "['Function 1', 'Function 2']",
            "value_proposition": "Test value",
            "final_score": 75.0
        }

        profile_response = Mock()
        profile_response.data = [primary_profile]

        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = profile_response

        copied_profile = copy_profiler_from_primary(submission, concept_id, mock_supabase)

        assert copied_profile is not None
        assert copied_profile["app_name"] == "Test App"
        assert copied_profile["copied_from_primary"] is True

        # Step 3: Update concept stats - use integer concept_id for this function
        rpc_response = Mock()
        rpc_response.data = [{"update_profiler_analysis_tracking": True}]

        mock_supabase.rpc.return_value.execute.return_value = rpc_response

        update_concept_profiler_stats(456, copied_profile, mock_supabase)

        mock_supabase.rpc.assert_called_with("update_profiler_analysis_tracking", {
            "p_concept_id": 456,
            "p_has_analysis": True,
            "p_profiler_score": 75.0
        })


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])