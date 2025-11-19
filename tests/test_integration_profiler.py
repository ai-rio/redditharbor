#!/usr/bin/env python3
"""
Integration test for AI Profiler skip logic in batch_opportunity_scoring.py

This test validates that the AI Profiler deduplication integration works correctly:
- Checks should_run_profiler_analysis function is called before AI profiling
- Validates copy_profiler_from_primary is called when analysis should be skipped
- Ensures update_concept_profiler_stats is called when fresh profiling is performed
- Tests both skip and fresh profiling scenarios
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the functions to test
from scripts.core.batch_opportunity_scoring import (
    should_run_profiler_analysis,
    copy_profiler_from_primary,
    update_concept_profiler_stats,
    process_batch
)


class TestProfilerIntegration:
    """Test AI Profiler deduplication integration in process_batch function."""

    @pytest.fixture
    def mock_submission(self):
        """Create a mock submission for testing."""
        return {
            "id": "test-submission-id",
            "submission_id": "test-submission-id",
            "title": "Test Submission for AI Profiler Integration",
            "text": "This is a test submission to validate the AI profiler deduplication integration logic.",
            "subreddit": "testsubreddit",
            "score": 100,
            "num_comments": 25,
            "sentiment_score": 0.8,
            "monetization_potential": 75.0,
        }

    @pytest.fixture
    def mock_agent(self):
        """Create a mock opportunity analyzer agent."""
        mock_agent = MagicMock()
        mock_agent.analyze_opportunity.return_value = {
            "final_score": 85.0,
            "monetization_potential": 75.0,
            "market_size": "Large",
            "innovation_level": "High",
            "competition_level": "Low",
            "implementation_complexity": "Medium",
            "time_to_market": "6-12 months",
            "confidence_score": 0.85,
            "reasoning": "Test reasoning for high-scoring opportunity"
        }
        return mock_agent

    @pytest.fixture
    def mock_llm_profiler(self):
        """Create a mock LLM profiler."""
        mock_profiler = MagicMock()
        mock_profiler.generate_app_profile_with_evidence.return_value = {
            "app_concept": "Test App Concept",
            "target_user": "B2C",
            "problem_description": "Test problem description",
            "solution_approach": "Test solution approach",
            "core_features": ["Feature 1", "Feature 2"],
            "monetization_model": "freemium",
            "cost_tracking": {
                "total_cost_usd": 0.002,
                "total_tokens": 150
            }
        }
        return mock_profiler

    @pytest.fixture
    def mock_supabase(self):
        """Create a mock Supabase client."""
        return MagicMock()

    def test_should_run_profiler_analysis_called_before_profiling(
        self, mock_submission, mock_agent, mock_llm_profiler, mock_supabase
    ):
        """Test that should_run_profiler_analysis is called before AI profiling."""

        # Mock the deduplication function to return False (fresh profiling needed)
        with patch('scripts.core.batch_opportunity_scoring.should_run_profiler_analysis') as mock_should_run:
            mock_should_run.return_value = (False, None)

            # Mock format_submission_for_agent to avoid import issues
            with patch('scripts.core.batch_opportunity_scoring.format_submission_for_agent') as mock_format:
                mock_format.return_value = {
                    "id": "test-submission-id",
                    "title": "Test Submission",
                    "text": "Test text",
                    "subreddit": "testsubreddit",
                    "engagement": 125,
                    "comments": 25,
                    "sentiment_score": 0.8,
                    "db_id": "test-submission-id",
                }

                # Call process_batch with high-scoring submission
                analysis_results, _, _, _ = process_batch(
                    submissions=[mock_submission],
                    agent=mock_agent,
                    batch_number=1,
                    llm_profiler=mock_llm_profiler,
                    ai_profile_threshold=40.0,
                    supabase=mock_supabase
                )

                # Verify should_run_profiler_analysis was called
                mock_should_run.assert_called_once_with(mock_submission, mock_supabase)

                # Verify fresh profiling was performed (since should_run_profiler returned False)
                mock_llm_profiler.generate_app_profile_with_evidence.assert_called_once()

    def test_copy_profiler_from_primary_called_when_skip_profiling(
        self, mock_submission, mock_agent, mock_llm_profiler, mock_supabase
    ):
        """Test that copy_profiler_from_primary is called when profiling should be skipped."""

        # Mock the deduplication function to return True (skip profiling)
        with patch('scripts.core.batch_opportunity_scoring.should_run_profiler_analysis') as mock_should_run:
            mock_should_run.return_value = (True, "test-concept-id")

            # Mock the copy function
            with patch('scripts.core.batch_opportunity_scoring.copy_profiler_from_primary') as mock_copy:
                mock_copy.return_value = {
                    "app_concept": "Copied App Concept",
                    "target_user": "B2C",
                    "problem_description": "Copied problem description",
                    "solution_approach": "Copied solution approach",
                    "core_features": ["Copied Feature 1", "Copied Feature 2"],
                    "monetization_model": "freemium",
                }

            # Mock format_submission_for_agent to avoid import issues
            with patch('scripts.core.batch_opportunity_scoring.format_submission_for_agent') as mock_format:
                mock_format.return_value = {
                    "id": "test-submission-id",
                    "title": "Test Submission",
                    "text": "Test text",
                    "subreddit": "testsubreddit",
                    "engagement": 125,
                    "comments": 25,
                    "sentiment_score": 0.8,
                    "db_id": "test-submission-id",
                }

                # Call process_batch with high-scoring submission
                analysis_results, _, _, _ = process_batch(
                    submissions=[mock_submission],
                    agent=mock_agent,
                    batch_number=1,
                    llm_profiler=mock_llm_profiler,
                    ai_profile_threshold=40.0,
                    supabase=mock_supabase
                )

                # Verify should_run_profiler_analysis was called
                mock_should_run.assert_called_once_with(mock_submission, mock_supabase)

                # Verify copy_profiler_from_primary was called
                mock_copy.assert_called_once_with(mock_submission, "test-concept-id", mock_supabase)

                # Verify fresh profiling was NOT performed
                mock_llm_profiler.generate_app_profile_with_evidence.assert_not_called()

    def test_update_concept_profiler_stats_called_after_fresh_profiling(
        self, mock_submission, mock_agent, mock_llm_profiler, mock_supabase
    ):
        """Test that update_concept_profiler_stats is called after fresh profiling."""

        # Mock the deduplication function to return False (fresh profiling needed)
        with patch('scripts.core.batch_opportunity_scoring.should_run_profiler_analysis') as mock_should_run:
            mock_should_run.return_value = (False, None)

            # Mock the stats update function
            with patch('scripts.core.batch_opportunity_scoring.update_concept_profiler_stats') as mock_update_stats:

                # Mock format_submission_for_agent to avoid import issues
                with patch('scripts.core.batch_opportunity_scoring.format_submission_for_agent') as mock_format:
                    mock_format.return_value = {
                        "id": "test-submission-id",
                        "title": "Test Submission",
                        "text": "Test text",
                        "subreddit": "testsubreddit",
                        "engagement": 125,
                        "comments": 25,
                        "sentiment_score": 0.8,
                        "db_id": "test-submission-id",
                    }

                    # Call process_batch with high-scoring submission
                    analysis_results, _, _, _ = process_batch(
                        submissions=[mock_submission],
                        agent=mock_agent,
                        batch_number=1,
                        llm_profiler=mock_llm_profiler,
                        ai_profile_threshold=40.0,
                        supabase=mock_supabase
                    )

                    # Verify should_run_profiler_analysis was called
                    mock_should_run.assert_called_once_with(mock_submission, mock_supabase)

                    # Verify fresh profiling was performed
                    mock_llm_profiler.generate_app_profile_with_evidence.assert_called_once()

                    # Verify update_concept_profiler_stats was called
                    mock_update_stats.assert_called_once()

    def test_fallback_fresh_profiling_when_copy_fails(
        self, mock_submission, mock_agent, mock_llm_profiler, mock_supabase
    ):
        """Test that fresh profiling is used as fallback when copy operation fails."""

        # Mock the deduplication function to return True (skip profiling initially)
        with patch('scripts.core.batch_opportunity_scoring.should_run_profiler_analysis') as mock_should_run:
            mock_should_run.return_value = (True, "test-concept-id")

            # Mock the copy function to return None (failure)
            with patch('scripts.core.batch_opportunity_scoring.copy_profiler_from_primary') as mock_copy:
                mock_copy.return_value = None

            # Mock format_submission_for_agent to avoid import issues
            with patch('scripts.core.batch_opportunity_scoring.format_submission_for_agent') as mock_format:
                mock_format.return_value = {
                    "id": "test-submission-id",
                    "title": "Test Submission",
                    "text": "Test text",
                    "subreddit": "testsubreddit",
                    "engagement": 125,
                    "comments": 25,
                    "sentiment_score": 0.8,
                    "db_id": "test-submission-id",
                }

                # Call process_batch with high-scoring submission
                analysis_results, _, _, _ = process_batch(
                    submissions=[mock_submission],
                    agent=mock_agent,
                    batch_number=1,
                    llm_profiler=mock_llm_profiler,
                    ai_profile_threshold=40.0,
                    supabase=mock_supabase
                )

                # Verify should_run_profiler_analysis was called
                mock_should_run.assert_called_once_with(mock_submission, mock_supabase)

                # Verify copy_profiler_from_primary was called
                mock_copy.assert_called_once_with(mock_submission, "test-concept-id", mock_supabase)

                # Verify fresh profiling was performed as fallback
                mock_llm_profiler.generate_app_profile_with_evidence.assert_called_once()

    def test_no_profiling_below_threshold(
        self, mock_submission, mock_agent, mock_llm_profiler, mock_supabase
    ):
        """Test that no profiling occurs when score is below threshold."""

        # Create agent that returns low score
        low_score_agent = MagicMock()
        low_score_agent.analyze_opportunity.return_value = {
            "final_score": 25.0,  # Below threshold of 40.0
            "monetization_potential": 30.0,
            "market_size": "Small",
            "innovation_level": "Low",
            "competition_level": "High",
            "implementation_complexity": "High",
            "time_to_market": "12+ months",
            "confidence_score": 0.6,
            "reasoning": "Test reasoning for low-scoring opportunity"
        }

        # Mock the deduplication function
        with patch('scripts.core.batch_opportunity_scoring.should_run_profiler_analysis') as mock_should_run:

            # Mock format_submission_for_agent to avoid import issues
            with patch('scripts.core.batch_opportunity_scoring.format_submission_for_agent') as mock_format:
                mock_format.return_value = {
                    "id": "test-submission-id",
                    "title": "Test Submission",
                    "text": "Test text",
                    "subreddit": "testsubreddit",
                    "engagement": 125,
                    "comments": 25,
                    "sentiment_score": 0.8,
                    "db_id": "test-submission-id",
                }

                # Call process_batch with low-scoring submission
                analysis_results, _, _, _ = process_batch(
                    submissions=[mock_submission],
                    agent=low_score_agent,
                    batch_number=1,
                    llm_profiler=mock_llm_profiler,
                    ai_profile_threshold=40.0,
                    supabase=mock_supabase
                )

                # Verify should_run_profiler_analysis was NOT called
                mock_should_run.assert_not_called()

                # Verify no profiling was performed
                mock_llm_profiler.generate_app_profile_with_evidence.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])