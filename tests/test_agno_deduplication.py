#!/usr/bin/env python3
"""
Tests for Agno Analysis Deduplication Functions
Task 2: Agno Analysis Deduplication Functions - Steps 1-7

This test file follows TDD approach - tests are written first to validate
the Agno deduplication functions before implementation.
"""

import logging
import os
import sys
import time
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from config.settings import SUPABASE_KEY, SUPABASE_URL
    from scripts.core.batch_opportunity_scoring import (
        should_run_agno_analysis,
        copy_agno_from_primary,
        update_concept_agno_stats,
    )
except ImportError as e:
    # Handle import errors gracefully for CI/testing environments
    should_run_agno_analysis = None
    copy_agno_from_primary = None
    update_concept_agno_stats = None
    SUPABASE_URL = None
    SUPABASE_KEY = None
    logging.warning(f"Could not import Agno deduplication functions: {e}")

# Set up logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestAgnoDeduplicationFunctions:
    """Test cases for Agno Analysis Deduplication Functions"""

    @pytest.fixture
    def mock_supabase(self):
        """Create a mock Supabase client for testing"""
        mock_client = Mock()
        return mock_client

    @pytest.fixture
    def sample_submission(self):
        """Create sample submission data for testing"""
        return {
            "submission_id": "test_abc123",
            "id": "test_abc123",
            "title": "Looking for feedback on my food delivery app idea",
            "problem_description": "I want to create an app that connects local restaurants with customers for food delivery",
            "subreddit": "startups",
            "reddit_score": 45,
            "num_comments": 23,
            "trust_score": 75,
            "trust_badge": "Trusted",
            "activity_score": 80,
        }

    @pytest.fixture
    def sample_primary_opportunity(self):
        """Create sample primary opportunity data for testing"""
        return {
            "id": "primary_uuid_123",
            "submission_id": "primary_abc123",
            "title": "Food delivery app concept",
            "app_concept": "App idea: Food delivery service for local restaurants",
            "business_concept_id": 42,
            "llm_monetization_score": 85.5,
            "willingness_to_pay_score": 75.0,
            "customer_segment": "B2C",
            "payment_sentiment": "Positive",
            "urgency_level": "High",
            "confidence": 0.85,
            "reasoning": "Strong market demand for food delivery services",
            "model_used": "openai/gpt-4o-mini",
        }

    def test_should_run_agno_analysis_missing_functions(self):
        """Test that should_run_agno_analysis function exists and can be imported"""
        if should_run_agno_analysis is None:
            pytest.skip("should_run_agno_analysis function not implemented yet")

        # Verify function signature
        import inspect
        sig = inspect.signature(should_run_agno_analysis)
        expected_params = ['submission', 'supabase']
        actual_params = list(sig.parameters.keys())

        assert actual_params == expected_params, f"Function signature mismatch. Expected: {expected_params}, Got: {actual_params}"

    def test_copy_agno_from_primary_missing_functions(self):
        """Test that copy_agno_from_primary function exists and can be imported"""
        if copy_agno_from_primary is None:
            pytest.skip("copy_agno_from_primary function not implemented yet")

        # Verify function signature
        import inspect
        sig = inspect.signature(copy_agno_from_primary)
        expected_params = ['submission', 'concept_id', 'supabase']
        actual_params = list(sig.parameters.keys())

        assert actual_params == expected_params, f"Function signature mismatch. Expected: {expected_params}, Got: {actual_params}"

    def test_update_concept_agno_stats_missing_functions(self):
        """Test that update_concept_agno_stats function exists and can be imported"""
        if update_concept_agno_stats is None:
            pytest.skip("update_concept_agno_stats function not implemented yet")

        # Verify function signature
        import inspect
        sig = inspect.signature(update_concept_agno_stats)
        expected_params = ['concept_id', 'agno_result', 'supabase']
        actual_params = list(sig.parameters.keys())

        assert actual_params == expected_params, f"Function signature mismatch. Expected: {expected_params}, Got: {actual_params}"

    def test_should_run_agno_analysis_with_unique_submission(self, mock_supabase, sample_submission):
        """Test should_run_agno_analysis returns True for unique submission (no duplicate)"""
        if should_run_agno_analysis is None:
            pytest.skip("should_run_agno_analysis function not implemented yet")

        # Mock database responses for unique submission
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        # Call the function
        result, concept_id = should_run_agno_analysis(sample_submission, mock_supabase)

        # Should return True for unique submission (no existing Agno analysis)
        assert result is True
        assert concept_id is None  # No concept_id for unique submission

    def test_should_run_agno_analysis_with_duplicate_no_agno(self, mock_supabase, sample_submission):
        """Test should_run_agno_analysis returns True for duplicate without existing Agno analysis"""
        if should_run_agno_analysis is None:
            pytest.skip("should_run_agno_analysis function not implemented yet")

        # Mock database responses for duplicate without Agno analysis
        # First call: check opportunities_unified table (find business_concept_id)
        # Second call: check business_concepts table (check has_agno_analysis)
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            Mock(data=[{"business_concept_id": 42}]),  # opportunities_unified response
            Mock(data=[{"id": 42, "has_agno_analysis": False}])  # business_concepts response
        ]

        # Call the function
        result, concept_id = should_run_agno_analysis(sample_submission, mock_supabase)

        # Should return True for duplicate without Agno analysis
        assert result is True
        assert concept_id == "42"  # Should return the concept_id as string

    def test_should_run_agno_analysis_with_duplicate_with_agno(self, mock_supabase, sample_submission):
        """Test should_run_agno_analysis returns False for duplicate with existing Agno analysis"""
        if should_run_agno_analysis is None:
            pytest.skip("should_run_agno_analysis function not implemented yet")

        # Mock database responses for duplicate with Agno analysis
        # First call: check opportunities_unified table (find business_concept_id)
        # Second call: check business_concepts table (check has_agno_analysis)
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            Mock(data=[{"business_concept_id": 42}]),  # opportunities_unified response
            Mock(data=[{"id": 42, "has_agno_analysis": True}])  # business_concepts response
        ]

        # Call the function
        result, concept_id = should_run_agno_analysis(sample_submission, mock_supabase)

        # Should return False for duplicate with existing Agno analysis
        assert result is False
        assert concept_id == "42"  # Should still return the concept_id as string

    def test_should_run_agno_analysis_handles_database_errors(self, mock_supabase, sample_submission):
        """Test should_run_agno_analysis handles database errors gracefully"""
        if should_run_agno_analysis is None:
            pytest.skip("should_run_agno_analysis function not implemented yet")

        # Mock database error
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("Database error")

        # Call the function
        result, concept_id = should_run_agno_analysis(sample_submission, mock_supabase)

        # Should handle error gracefully - default to running analysis
        assert result is True
        assert concept_id is None

    def test_copy_agno_from_primary_success(self, mock_supabase, sample_submission, sample_primary_opportunity):
        """Test copy_agno_from_primary successfully copies Agno analysis from primary opportunity"""
        if copy_agno_from_primary is None:
            pytest.skip("copy_agno_from_primary function not implemented yet")

        # Mock database query to find primary opportunity with Agno analysis
        # The function calls: table().select().eq().eq().execute()
        mock_response = Mock()
        mock_response.data = [sample_primary_opportunity]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response

        # Call the function
        result = copy_agno_from_primary(sample_submission, 42, mock_supabase)

        # Verify the result structure
        assert isinstance(result, dict)

        # Should contain all required Agno analysis fields
        expected_fields = [
            "llm_monetization_score",
            "willingness_to_pay_score",
            "customer_segment",
            "payment_sentiment",
            "urgency_level",
            "confidence",
            "reasoning",
            "model_used",
            "opportunity_id",  # Should be formatted for current submission
            "submission_id",  # Should be current submission's ID
        ]

        for field in expected_fields:
            assert field in result, f"Missing field: {field}"

        # Verify opportunity_id is correctly formatted for current submission
        assert result["opportunity_id"] == f"opp_{sample_submission['submission_id']}"
        assert result["submission_id"] == sample_submission["submission_id"]

        # Verify analysis data is copied from primary opportunity
        assert result["llm_monetization_score"] == sample_primary_opportunity["llm_monetization_score"]
        assert result["willingness_to_pay_score"] == sample_primary_opportunity["willingness_to_pay_score"]
        assert result["customer_segment"] == sample_primary_opportunity["customer_segment"]

    def test_copy_agno_from_primary_no_primary_found(self, mock_supabase, sample_submission):
        """Test copy_agno_from_primary handles case when no primary opportunity is found"""
        if copy_agno_from_primary is None:
            pytest.skip("copy_agno_from_primary function not implemented yet")

        # Mock empty response (no primary opportunity found)
        mock_response = Mock()
        mock_response.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        # Call the function
        result = copy_agno_from_primary(sample_submission, 42, mock_supabase)

        # Should return empty dict when no primary found
        assert result == {}

    def test_copy_agno_from_primary_handles_database_errors(self, mock_supabase, sample_submission):
        """Test copy_agno_from_primary handles database errors gracefully"""
        if copy_agno_from_primary is None:
            pytest.skip("copy_agno_from_primary function not implemented yet")

        # Mock database error
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("Database error")

        # Call the function
        result = copy_agno_from_primary(sample_submission, 42, mock_supabase)

        # Should return empty dict on error
        assert result == {}

    def test_update_concept_agno_stats_success(self, mock_supabase):
        """Test update_concept_agno_stats successfully updates concept with Agno analysis metadata"""
        if update_concept_agno_stats is None:
            pytest.skip("update_concept_agno_stats function not implemented yet")

        # Sample Agno result
        agno_result = {
            "willingness_to_pay_score": 75.0,
            "llm_monetization_score": 85.5,
            "customer_segment": "B2C",
            "confidence": 0.85,
        }

        # Mock successful database update
        mock_supabase.rpc.return_value.execute.return_value = Mock(data=[{"update_agno_analysis_tracking": True}])

        # Call the function
        update_concept_agno_stats("42", agno_result, mock_supabase)

        # Verify the RPC call was made with correct parameters
        mock_supabase.rpc.assert_called_once_with("update_agno_analysis_tracking", {
            "p_concept_id": 42,
            "p_has_analysis": True,
            "p_wtp_score": 75.0
        })

    def test_update_concept_agno_stats_missing_wtp_score(self, mock_supabase):
        """Test update_concept_agno_stats handles case when WTP score is missing"""
        if update_concept_agno_stats is None:
            pytest.skip("update_concept_agno_stats function not implemented yet")

        # Sample Agno result without WTP score
        agno_result = {
            "llm_monetization_score": 85.5,
            "customer_segment": "B2C",
            "confidence": 0.85,
        }

        # Mock successful database update
        mock_supabase.rpc.return_value.execute.return_value = Mock(data=[{"update_agno_analysis_tracking": True}])

        # Call the function
        update_concept_agno_stats("42", agno_result, mock_supabase)

        # Verify the RPC call was made with None WTP score
        mock_supabase.rpc.assert_called_once_with("update_agno_analysis_tracking", {
            "p_concept_id": 42,
            "p_has_analysis": True,
            "p_wtp_score": None
        })

    def test_update_concept_agno_stats_handles_database_errors(self, mock_supabase):
        """Test update_concept_agno_stats handles database errors gracefully"""
        if update_concept_agno_stats is None:
            pytest.skip("update_concept_agno_stats function not implemented yet")

        # Sample Agno result
        agno_result = {
            "willingness_to_pay_score": 75.0,
            "llm_monetization_score": 85.5,
        }

        # Mock database error
        mock_supabase.rpc.return_value.execute.side_effect = Exception("Database error")

        # Should not raise exception - function should handle errors gracefully
        try:
            update_concept_agno_stats("42", agno_result, mock_supabase)
        except Exception:
            pytest.fail("update_concept_agno_stats should handle database errors gracefully")

    def test_integration_workflow_duplicate_with_existing_agno(self, mock_supabase, sample_submission):
        """Test complete workflow for duplicate opportunity with existing Agno analysis"""
        if should_run_agno_analysis is None or copy_agno_from_primary is None:
            pytest.skip("Agno deduplication functions not implemented yet")

        # Mock database responses
        # First call: check opportunities_unified table (find business_concept_id)
        # Second call: check business_concepts table (check has_agno_analysis)
        mock_calls = [
            Mock(data=[{"business_concept_id": 42}]),  # opportunities_unified response
            Mock(data=[{"id": 42, "has_agno_analysis": True}])  # business_concepts response
        ]

        # Reset and setup the mock
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = mock_calls

        # Step 1: Check if should run Agno analysis
        should_run, concept_id = should_run_agno_analysis(sample_submission, mock_supabase)

        assert should_run is False
        assert concept_id == "42"

        # Step 2: Since should_run is False, we should copy from primary
        # Mock primary opportunity query
        primary_opp = {
            "id": "primary_uuid",
            "llm_monetization_score": 85.5,
            "willingness_to_pay_score": 75.0,
            "customer_segment": "B2C",
            "confidence": 0.85,
        }
        # Reset mock to setup new response for copy function
        mock_supabase.reset_mock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(data=[primary_opp])

        copied_analysis = copy_agno_from_primary(sample_submission, concept_id, mock_supabase)

        # Should get valid copied analysis
        assert copied_analysis != {}
        assert copied_analysis["llm_monetization_score"] == 85.5
        assert copied_analysis["opportunity_id"] == f"opp_{sample_submission['submission_id']}"

    def test_integration_workflow_duplicate_without_existing_agno(self, mock_supabase, sample_submission):
        """Test complete workflow for duplicate opportunity without existing Agno analysis"""
        if should_run_agno_analysis is None or update_concept_agno_stats is None:
            pytest.skip("Agno deduplication functions not implemented yet")

        # Mock database responses for duplicate without Agno
        # First call: check opportunities_unified table (find business_concept_id)
        # Second call: check business_concepts table (check has_agno_analysis)
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            Mock(data=[{"business_concept_id": 42}]),  # opportunities_unified response
            Mock(data=[{"id": 42, "has_agno_analysis": False}])  # business_concepts response
        ]
        mock_supabase.rpc.return_value.execute.return_value = Mock(data=[{"update_agno_analysis_tracking": True}])

        # Step 1: Check if should run Agno analysis
        should_run, concept_id = should_run_agno_analysis(sample_submission, mock_supabase)

        assert should_run is True
        assert concept_id == "42"

        # Step 2: Since should_run is True, we would run new analysis
        # Simulate new Agno analysis result
        new_agno_result = {
            "llm_monetization_score": 90.0,
            "willingness_to_pay_score": 80.0,
            "customer_segment": "B2C",
            "confidence": 0.90,
        }

        # Step 3: Update concept stats with new analysis
        update_concept_agno_stats(concept_id, new_agno_result, mock_supabase)

        # Verify the update was called
        mock_supabase.rpc.assert_called_with("update_agno_analysis_tracking", {
            "p_concept_id": 42,
            "p_has_analysis": True,
            "p_wtp_score": 80.0
        })


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])