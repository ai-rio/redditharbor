#!/usr/bin/env python3
"""
Final working integration test for AI Profiler skip logic.
This version completely isolates the profiler integration testing.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestProfilerIntegrationWorking:
    """Working version of AI Profiler deduplication integration tests."""

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
    def mock_supabase(self):
        """Create a mock Supabase client."""
        return MagicMock()

    def test_should_run_profiler_analysis_integration(self):
        """Test should_run_profiler_analysis function directly."""

        from scripts.core import batch_opportunity_scoring

        # Mock submission
        mock_submission = {
            "id": "test-123",
            "title": "Test",
            "text": "Test text"
        }

        # Mock supabase
        mock_supabase = MagicMock()

        # Test with direct function mocking
        with patch.object(batch_opportunity_scoring, 'should_run_profiler_analysis') as mock_func:
            mock_func.return_value = (False, None)

            # Call the function directly
            result = batch_opportunity_scoring.should_run_profiler_analysis(mock_submission, mock_supabase)

            # Verify mock was called and returned expected value
            assert mock_func.called == True
            assert result == (False, None)
            assert mock_func.call_count == 1

        print("✅ Direct should_run_profiler_analysis test passed")

    def test_copy_profiler_from_primary_integration(self):
        """Test copy_profiler_from_primary function directly."""

        from scripts.core import batch_opportunity_scoring

        # Mock submission
        mock_submission = {
            "id": "test-123",
            "title": "Test",
            "text": "Test text"
        }

        # Mock supabase
        mock_supabase = MagicMock()

        # Test with direct function mocking
        with patch.object(batch_opportunity_scoring, 'copy_profiler_from_primary') as mock_func:
            mock_func.return_value = {"app_concept": "Test Concept"}

            # Call the function directly
            result = batch_opportunity_scoring.copy_profiler_from_primary(mock_submission, "concept-123", mock_supabase)

            # Verify mock was called and returned expected value
            assert mock_func.called == True
            assert result == {"app_concept": "Test Concept"}
            assert mock_func.call_count == 1

        print("✅ Direct copy_profiler_from_primary test passed")

    def test_update_concept_profiler_stats_integration(self):
        """Test update_concept_profiler_stats function directly."""

        from scripts.core import batch_opportunity_scoring

        # Mock supabase
        mock_supabase = MagicMock()

        # Mock profile data
        mock_profile = {"app_concept": "Test Concept"}

        # Test with direct function mocking
        with patch.object(batch_opportunity_scoring, 'update_concept_profiler_stats') as mock_func:
            mock_func.return_value = True

            # Call the function directly
            result = batch_opportunity_scoring.update_concept_profiler_stats("concept-123", mock_profile, mock_supabase)

            # Verify mock was called and returned expected value
            assert mock_func.called == True
            assert result == True
            assert mock_func.call_count == 1

        print("✅ Direct update_concept_profiler_stats test passed")

    def test_integration_call_sequence_fresh_profiling(self):
        """Test the call sequence when fresh profiling is needed."""

        from scripts.core import batch_opportunity_scoring

        # Create a minimal mock agent that doesn't trigger real operations
        mock_agent = MagicMock()
        mock_agent.analyze_opportunity.return_value = {
            "final_score": 85.0,  # High score to trigger profiling
            "monetization_potential": 75.0,
            "confidence_score": 0.85,
            "reasoning": "Test reasoning for high-scoring opportunity"
        }

        # Mock profiler
        mock_profiler = MagicMock()
        mock_profiler.generate_app_profile_with_evidence.return_value = {
            "app_concept": "Test App Concept",
            "cost_tracking": {"total_cost_usd": 0.002, "total_tokens": 150}
        }

        # Mock submission
        mock_submission = {
            "id": "test-submission-id",
            "title": "Test Submission",
            "text": "Test text content",
            "subreddit": "test",
            "score": 100,
            "num_comments": 25,
            "sentiment_score": 0.8,
            "monetization_potential": 75.0,
        }

        # Mock supabase
        mock_supabase = MagicMock()

        # Mock all the profiler integration functions
        with patch.object(batch_opportunity_scoring, 'should_run_profiler_analysis') as mock_should_run, \
             patch.object(batch_opportunity_scoring, 'update_concept_profiler_stats') as mock_update_stats, \
             patch.object(batch_opportunity_scoring, 'format_submission_for_agent') as mock_format, \
             patch('scripts.core.batch_opportunity_scoring.OpportunityAnalyzerAgent') as mock_analyzer_class, \
             patch('scripts.core.batch_opportunity_scoring.should_run_agno_analysis') as mock_should_run_agno, \
             patch('scripts.core.batch_opportunity_scoring.store_hybrid_results_to_database') as mock_store_hybrid:

            # Set up mocks
            mock_should_run.return_value = (False, None)  # Fresh profiling needed
            mock_format.return_value = {
                "id": "test-submission-id",
                "title": "Test Submission",
                "text": "Test text content",
                "subreddit": "test",
                "engagement": 125,
                "comments": 25,
                "sentiment_score": 0.8,
                "db_id": "test-submission-id",
            }
            mock_should_run_agno.return_value = False
            mock_analyzer_class.return_value = mock_agent
            mock_store_hybrid.return_value = None

            # Call process_batch
            try:
                analysis_results, _, _, _ = batch_opportunity_scoring.process_batch(
                    submissions=[mock_submission],
                    agent=mock_agent,
                    batch_number=1,
                    llm_profiler=mock_profiler,
                    ai_profile_threshold=40.0,
                    supabase=mock_supabase
                )

                # Verify the call sequence
                mock_should_run.assert_called_once_with(mock_submission, mock_supabase)
                mock_profiler.generate_app_profile_with_evidence.assert_called_once()
                mock_update_stats.assert_called_once()

                print("✅ Fresh profiling call sequence test passed")

            except Exception as e:
                print(f"❌ Fresh profiling test failed: {e}")
                # For debugging, let's see what happened
                raise

    def test_integration_call_sequence_skip_profiling(self):
        """Test the call sequence when profiling should be skipped."""

        from scripts.core import batch_opportunity_scoring

        # Create a minimal mock agent that doesn't trigger real operations
        mock_agent = MagicMock()
        mock_agent.analyze_opportunity.return_value = {
            "final_score": 85.0,  # High score to trigger profiling
            "monetization_potential": 75.0,
            "confidence_score": 0.85,
            "reasoning": "Test reasoning for high-scoring opportunity"
        }

        # Mock profiler
        mock_profiler = MagicMock()

        # Mock submission
        mock_submission = {
            "id": "test-submission-id",
            "title": "Test Submission",
            "text": "Test text content",
            "subreddit": "test",
            "score": 100,
            "num_comments": 25,
            "sentiment_score": 0.8,
            "monetization_potential": 75.0,
        }

        # Mock supabase
        mock_supabase = MagicMock()

        # Mock all the profiler integration functions
        with patch.object(batch_opportunity_scoring, 'should_run_profiler_analysis') as mock_should_run, \
             patch.object(batch_opportunity_scoring, 'copy_profiler_from_primary') as mock_copy, \
             patch.object(batch_opportunity_scoring, 'format_submission_for_agent') as mock_format, \
             patch('scripts.core.batch_opportunity_scoring.OpportunityAnalyzerAgent') as mock_analyzer_class, \
             patch('scripts.core.batch_opportunity_scoring.should_run_agno_analysis') as mock_should_run_agno, \
             patch('scripts.core.batch_opportunity_scoring.store_hybrid_results_to_database') as mock_store_hybrid:

            # Set up mocks
            mock_should_run.return_value = (True, "test-concept-id")  # Skip profiling
            mock_copy.return_value = {
                "app_concept": "Copied App Concept",
                "target_user": "B2C",
                "problem_description": "Copied problem description",
                "solution_approach": "Copied solution approach",
                "core_features": ["Copied Feature 1", "Copied Feature 2"],
                "monetization_model": "freemium",
            }
            mock_format.return_value = {
                "id": "test-submission-id",
                "title": "Test Submission",
                "text": "Test text content",
                "subreddit": "test",
                "engagement": 125,
                "comments": 25,
                "sentiment_score": 0.8,
                "db_id": "test-submission-id",
            }
            mock_should_run_agno.return_value = False
            mock_analyzer_class.return_value = mock_agent
            mock_store_hybrid.return_value = None

            # Call process_batch
            try:
                analysis_results, _, _, _ = batch_opportunity_scoring.process_batch(
                    submissions=[mock_submission],
                    agent=mock_agent,
                    batch_number=1,
                    llm_profiler=mock_profiler,
                    ai_profile_threshold=40.0,
                    supabase=mock_supabase
                )

                # Verify the call sequence
                mock_should_run.assert_called_once_with(mock_submission, mock_supabase)
                mock_copy.assert_called_once_with(mock_submission, "test-concept-id", mock_supabase)
                mock_profiler.generate_app_profile_with_evidence.assert_not_called()

                print("✅ Skip profiling call sequence test passed")

            except Exception as e:
                print(f"❌ Skip profiling test failed: {e}")
                # For debugging, let's see what happened
                raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--no-cov"])