#!/usr/bin/env python3
"""
Simplified integration test for AI Profiler skip logic.
This version fixes the mocking issues and provides faster execution.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestProfilerIntegrationFixed:
    """Fixed version of AI Profiler deduplication integration tests."""

    @pytest.fixture
    def mock_submission(self):
        """Create a mock submission for testing."""
        return {
            "id": "test-submission-id",
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

    def test_fresh_profiling_scenario(
        self, mock_submission, mock_agent, mock_llm_profiler, mock_supabase
    ):
        """Test scenario where fresh profiling should be performed."""

        # Import the module locally to avoid import issues
        from scripts.core import batch_opportunity_scoring

        # Mock the deduplication function to return False (fresh profiling needed)
        with patch.object(batch_opportunity_scoring, 'should_run_profiler_analysis') as mock_should_run:
            mock_should_run.return_value = (False, None)

            # Mock the stats update function
            with patch.object(batch_opportunity_scoring, 'update_concept_profiler_stats') as mock_update_stats:

                # Mock format_submission_for_agent
                with patch.object(batch_opportunity_scoring, 'format_submission_for_agent') as mock_format:
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
                    analysis_results, _, _, _ = batch_opportunity_scoring.process_batch(
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

                    # Verify update_concept_profiler_stats was called
                    mock_update_stats.assert_called_once()

    def test_skip_profiling_scenario(
        self, mock_submission, mock_agent, mock_llm_profiler, mock_supabase
    ):
        """Test scenario where profiling should be skipped and copied."""

        # Import the module locally to avoid import issues
        from scripts.core import batch_opportunity_scoring

        # Mock the deduplication function to return True (skip profiling)
        with patch.object(batch_opportunity_scoring, 'should_run_profiler_analysis') as mock_should_run:
            mock_should_run.return_value = (True, "test-concept-id")

            # Mock the copy function
            with patch.object(batch_opportunity_scoring, 'copy_profiler_from_primary') as mock_copy:
                mock_copy.return_value = {
                    "app_concept": "Copied App Concept",
                    "target_user": "B2C",
                    "problem_description": "Copied problem description",
                    "solution_approach": "Copied solution approach",
                    "core_features": ["Copied Feature 1", "Copied Feature 2"],
                    "monetization_model": "freemium",
                }

                # Mock format_submission_for_agent
                with patch.object(batch_opportunity_scoring, 'format_submission_for_agent') as mock_format:
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
                    analysis_results, _, _, _ = batch_opportunity_scoring.process_batch(
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

    def test_fallback_fresh_profiling_when_copy_fails(
        self, mock_submission, mock_agent, mock_llm_profiler, mock_supabase
    ):
        """Test that fresh profiling is used as fallback when copy operation fails."""

        # Import the module locally to avoid import issues
        from scripts.core import batch_opportunity_scoring

        # Mock the deduplication function to return True (skip profiling initially)
        with patch.object(batch_opportunity_scoring, 'should_run_profiler_analysis') as mock_should_run:
            mock_should_run.return_value = (True, "test-concept-id")

            # Mock the copy function to return None (failure)
            with patch.object(batch_opportunity_scoring, 'copy_profiler_from_primary') as mock_copy:
                mock_copy.return_value = None

                # Mock the stats update function
                with patch.object(batch_opportunity_scoring, 'update_concept_profiler_stats') as mock_update_stats:

                    # Mock format_submission_for_agent
                    with patch.object(batch_opportunity_scoring, 'format_submission_for_agent') as mock_format:
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
                        analysis_results, _, _, _ = batch_opportunity_scoring.process_batch(
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

                    # Verify update_concept_profiler_stats was called for fresh profiling
                    mock_update_stats.assert_called_once()

    def test_no_profiling_below_threshold(
        self, mock_submission, mock_llm_profiler, mock_supabase
    ):
        """Test that no profiling occurs when score is below threshold."""

        # Import the module locally to avoid import issues
        from scripts.core import batch_opportunity_scoring

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
        with patch.object(batch_opportunity_scoring, 'should_run_profiler_analysis') as mock_should_run:

            # Mock format_submission_for_agent
            with patch.object(batch_opportunity_scoring, 'format_submission_for_agent') as mock_format:
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
                analysis_results, _, _, _ = batch_opportunity_scoring.process_batch(
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

    def test_mock_verification(self):
        """Test that our mocking approach works correctly."""

        # Import the module locally
        from scripts.core import batch_opportunity_scoring

        # Test direct function mocking
        with patch.object(batch_opportunity_scoring, 'should_run_profiler_analysis') as mock_func:
            mock_func.return_value = (True, "test-id")

            # Call the function directly
            result = batch_opportunity_scoring.should_run_profiler_analysis({"id": "test"}, MagicMock())

            # Verify mock was called and returned expected value
            assert mock_func.called == True
            assert result == (True, "test-id")
            assert mock_func.call_count == 1

        print("✅ Mock verification passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--no-cov"])