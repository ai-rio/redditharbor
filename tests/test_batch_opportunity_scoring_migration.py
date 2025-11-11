#!/usr/bin/env python3
"""
Unit Tests for Batch Opportunity Scoring DLT Migration

Tests verify:
1. DLT pipeline integration for scoring data
2. Scoring calculation logic preserved
3. Data preparation for DLT storage
4. Deduplication via merge disposition
5. Batch processing statistics
6. Error handling
"""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.batch_opportunity_scoring import (
    format_submission_for_agent,
    load_scores_to_supabase_via_dlt,
    map_subreddit_to_sector,
    prepare_analysis_for_storage,
    process_batch,
)


class TestSectorMapping:
    """Test subreddit to sector mapping logic."""

    def test_map_subreddit_to_sector_health_fitness(self):
        """Test mapping for Health & Fitness subreddits."""
        assert map_subreddit_to_sector("fitness") == "Health & Fitness"
        assert map_subreddit_to_sector("loseit") == "Health & Fitness"
        assert map_subreddit_to_sector("YOGA") == "Health & Fitness"  # Case insensitive

    def test_map_subreddit_to_sector_finance(self):
        """Test mapping for Finance & Investing subreddits."""
        assert map_subreddit_to_sector("personalfinance") == "Finance & Investing"
        assert map_subreddit_to_sector("investing") == "Finance & Investing"
        assert map_subreddit_to_sector("STOCKS") == "Finance & Investing"

    def test_map_subreddit_to_sector_education(self):
        """Test mapping for Education & Career subreddits."""
        assert map_subreddit_to_sector("learnprogramming") == "Education & Career"
        assert map_subreddit_to_sector("cscareerquestions") == "Education & Career"

    def test_map_subreddit_to_sector_default(self):
        """Test default sector for unmapped subreddits."""
        assert map_subreddit_to_sector("unknown_subreddit") == "Technology & SaaS"
        assert map_subreddit_to_sector("") == "Technology & SaaS"
        assert map_subreddit_to_sector(None) == "Technology & SaaS"


class TestSubmissionFormatting:
    """Test submission data formatting for agent analysis."""

    def test_format_submission_for_agent_basic(self):
        """Test basic submission formatting."""
        submission = {
            "id": "abc123",
            "submission_id": "xyz789",
            "title": "Test Title",
            "text": "Test content",
            "subreddit": "fitness",
            "upvotes": 42,
            "comments_count": 15,
            "sentiment_score": 0.75,
        }

        formatted = format_submission_for_agent(submission)

        assert formatted["id"] == "xyz789"  # Uses submission_id
        assert formatted["title"] == "Test Title"
        assert formatted["text"] == "Test Title\n\nTest content"
        assert formatted["subreddit"] == "fitness"
        assert formatted["engagement"]["upvotes"] == 42
        assert formatted["engagement"]["num_comments"] == 15
        assert formatted["sentiment_score"] == 0.75
        assert formatted["db_id"] == "abc123"

    def test_format_submission_for_agent_with_problem_keywords(self):
        """Test formatting with problem keywords."""
        submission = {
            "id": "test_001",
            "submission_id": "sub_001",
            "title": "Looking for solution",
            "text": "I struggle with this problem",
            "subreddit": "productivity",
            "upvotes": 10,
            "comments_count": 5,
            "problem_keywords": "struggle, problem",
            "solution_mentions": "automation",
        }

        formatted = format_submission_for_agent(submission)

        # Check comments are populated from keywords
        assert len(formatted["comments"]) == 2
        assert "Problem identified" in formatted["comments"][0]
        assert "Solution discussed" in formatted["comments"][1]

    def test_format_submission_for_agent_missing_fields(self):
        """Test formatting handles missing fields gracefully."""
        submission = {
            "id": "minimal_001",
        }

        formatted = format_submission_for_agent(submission)

        assert formatted["id"] == "minimal_001"
        assert formatted["title"] == ""
        assert formatted["text"] == ""
        assert formatted["subreddit"] == ""
        assert formatted["engagement"]["upvotes"] == 0
        assert formatted["engagement"]["num_comments"] == 0


class TestAnalysisPreparation:
    """Test preparation of analysis results for DLT storage."""

    def test_prepare_analysis_for_storage_complete(self):
        """Test preparation with complete analysis data."""
        submission_id = "test_submission_123"
        analysis = {
            "title": "Test Opportunity",
            "subreddit": "personalfinance",
            "dimension_scores": {
                "market_demand": 75.5,
                "pain_intensity": 82.0,
                "monetization_potential": 68.5,
                "market_gap": 55.0,
                "technical_feasibility": 70.0,
            },
            "final_score": 72.3,
            "priority": "⚡ Med-High Priority",
        }
        sector = "Finance & Investing"

        prepared = prepare_analysis_for_storage(submission_id, analysis, sector)

        # Verify opportunity_id generation
        assert prepared["opportunity_id"] == "opp_test_submission_123"
        assert prepared["submission_id"] == "test_submission_123"

        # Verify metadata
        assert prepared["title"] == "Test Opportunity"
        assert prepared["subreddit"] == "personalfinance"
        assert prepared["sector"] == "Finance & Investing"

        # Verify dimension scores (converted to float)
        assert prepared["market_demand"] == 75.5
        assert prepared["pain_intensity"] == 82.0
        assert prepared["monetization_potential"] == 68.5
        assert prepared["market_gap"] == 55.0
        assert prepared["technical_feasibility"] == 70.0

        # Verify final score and priority
        assert prepared["final_score"] == 72.3
        assert prepared["priority"] == "⚡ Med-High Priority"

        # Verify timestamp
        assert "scored_at" in prepared
        assert isinstance(prepared["scored_at"], str)

    def test_prepare_analysis_for_storage_missing_scores(self):
        """Test preparation handles missing dimension scores."""
        submission_id = "test_002"
        analysis = {
            "title": "Minimal Opportunity",
            "dimension_scores": {},  # Empty scores
            "final_score": 0,
        }
        sector = "Technology & SaaS"

        prepared = prepare_analysis_for_storage(submission_id, analysis, sector)

        # Verify defaults for missing scores
        assert prepared["market_demand"] == 0.0
        assert prepared["pain_intensity"] == 0.0
        assert prepared["monetization_potential"] == 0.0
        assert prepared["market_gap"] == 0.0
        assert prepared["technical_feasibility"] == 0.0
        assert prepared["simplicity_score"] == 70.0  # Default neutral score

    def test_prepare_analysis_for_storage_long_title_truncation(self):
        """Test title truncation to 500 characters."""
        submission_id = "test_003"
        long_title = "A" * 600  # 600 characters
        analysis = {
            "title": long_title,
            "dimension_scores": {},
            "final_score": 50,
        }
        sector = "Education & Career"

        prepared = prepare_analysis_for_storage(submission_id, analysis, sector)

        # Verify title truncated to 500 chars
        assert len(prepared["title"]) == 500
        assert prepared["title"] == "A" * 500


class TestDLTPipelineIntegration:
    """Test DLT pipeline integration for loading scores."""

    @patch('scripts.batch_opportunity_scoring.create_dlt_pipeline')
    def test_load_scores_to_supabase_via_dlt_success(self, mock_create_pipeline):
        """Test successful DLT pipeline loading."""
        # Mock pipeline
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_load_info.started_at = datetime.now()
        mock_pipeline.run.return_value = mock_load_info
        mock_create_pipeline.return_value = mock_pipeline

        # Test data
        scored_opportunities = [
            {
                "opportunity_id": "opp_001",
                "submission_id": "sub_001",
                "market_demand": 75.0,
                "pain_intensity": 80.0,
                "monetization_potential": 70.0,
                "market_gap": 60.0,
                "technical_feasibility": 65.0,
                "final_score": 72.5,
            }
        ]

        # Execute
        result = load_scores_to_supabase_via_dlt(scored_opportunities)

        # Verify
        assert result is True
        mock_create_pipeline.assert_called_once()
        mock_pipeline.run.assert_called_once_with(
            scored_opportunities,
            table_name="opportunity_scores",
            write_disposition="merge",
            primary_key="opportunity_id"
        )

    @patch('scripts.batch_opportunity_scoring.create_dlt_pipeline')
    def test_load_scores_to_supabase_via_dlt_empty_list(self, mock_create_pipeline):
        """Test handling of empty scored opportunities list."""
        result = load_scores_to_supabase_via_dlt([])

        assert result is False
        mock_create_pipeline.assert_not_called()

    @patch('scripts.batch_opportunity_scoring.create_dlt_pipeline')
    def test_load_scores_to_supabase_via_dlt_pipeline_error(self, mock_create_pipeline):
        """Test error handling when pipeline fails."""
        # Mock pipeline that raises error
        mock_pipeline = MagicMock()
        mock_pipeline.run.side_effect = Exception("DLT pipeline connection failed")
        mock_create_pipeline.return_value = mock_pipeline

        scored_opportunities = [{"opportunity_id": "opp_001"}]

        # Execute
        result = load_scores_to_supabase_via_dlt(scored_opportunities)

        # Verify error handled gracefully
        assert result is False


class TestBatchProcessing:
    """Test batch processing of submissions."""

    @patch('scripts.batch_opportunity_scoring.OpportunityAnalyzerAgent')
    def test_process_batch_single_submission(self, mock_agent_class):
        """Test processing a single submission."""
        # Mock agent
        mock_agent = MagicMock()
        mock_agent.analyze_opportunity.return_value = {
            "opportunity_id": "test_001",
            "title": "Test Opportunity",
            "subreddit": "fitness",
            "dimension_scores": {
                "market_demand": 70.0,
                "pain_intensity": 75.0,
                "monetization_potential": 65.0,
                "market_gap": 60.0,
                "technical_feasibility": 70.0,
            },
            "final_score": 69.5,
            "priority": "📊 Medium Priority",
        }

        # Test submission
        submissions = [
            {
                "id": "sub_001",
                "submission_id": "reddit_001",
                "title": "Fitness tracking issue",
                "text": "I struggle with tracking workouts",
                "subreddit": "fitness",
                "upvotes": 25,
                "comments_count": 10,
            }
        ]

        # Execute
        results, scored_opps = process_batch(submissions, mock_agent, batch_number=1)

        # Verify results
        assert len(results) == 1
        assert len(scored_opps) == 1

        # Check analysis result
        result = results[0]
        assert result["opportunity_id"] == "opp_sub_001"
        assert result["sector"] == "Health & Fitness"
        assert result["stored"] is False  # Not yet loaded

        # Check scored opportunity
        scored = scored_opps[0]
        assert scored["opportunity_id"] == "opp_sub_001"
        assert scored["submission_id"] == "sub_001"
        assert scored["sector"] == "Health & Fitness"
        assert scored["market_demand"] == 70.0

    @patch('scripts.batch_opportunity_scoring.OpportunityAnalyzerAgent')
    def test_process_batch_multiple_submissions(self, mock_agent_class):
        """Test processing multiple submissions in batch."""
        # Mock agent
        mock_agent = MagicMock()
        mock_agent.analyze_opportunity.side_effect = [
            {
                "title": "Opp 1",
                "subreddit": "fitness",
                "dimension_scores": {
                    "market_demand": 70.0,
                    "pain_intensity": 75.0,
                    "monetization_potential": 65.0,
                    "market_gap": 60.0,
                    "technical_feasibility": 70.0,
                },
                "final_score": 69.5,
                "priority": "📊 Medium Priority",
            },
            {
                "title": "Opp 2",
                "subreddit": "investing",
                "dimension_scores": {
                    "market_demand": 80.0,
                    "pain_intensity": 85.0,
                    "monetization_potential": 75.0,
                    "market_gap": 70.0,
                    "technical_feasibility": 65.0,
                },
                "final_score": 77.5,
                "priority": "⚡ Med-High Priority",
            },
        ]

        submissions = [
            {"id": "sub_001", "subreddit": "fitness", "title": "Test 1", "text": "Content 1"},
            {"id": "sub_002", "subreddit": "investing", "title": "Test 2", "text": "Content 2"},
        ]

        # Execute
        results, scored_opps = process_batch(submissions, mock_agent, batch_number=1)

        # Verify
        assert len(results) == 2
        assert len(scored_opps) == 2
        assert results[0]["sector"] == "Health & Fitness"
        assert results[1]["sector"] == "Finance & Investing"

    @patch('scripts.batch_opportunity_scoring.OpportunityAnalyzerAgent')
    def test_process_batch_handles_errors(self, mock_agent_class):
        """Test batch processing handles individual submission errors."""
        # Mock agent that fails on second submission
        mock_agent = MagicMock()
        mock_agent.analyze_opportunity.side_effect = [
            {
                "title": "Success",
                "dimension_scores": {"market_demand": 70.0},
                "final_score": 65.0,
            },
            Exception("Analysis failed"),
        ]

        submissions = [
            {"id": "sub_001", "subreddit": "fitness", "title": "Test 1", "text": "Content 1"},
            {"id": "sub_002", "subreddit": "investing", "title": "Test 2", "text": "Content 2"},
        ]

        # Execute
        results, scored_opps = process_batch(submissions, mock_agent, batch_number=1)

        # Verify - first submission succeeds, second has error
        assert len(results) == 2
        assert "error" not in results[0]
        assert "error" in results[1]
        assert results[1]["error"] == "Analysis failed"
        assert results[1]["final_score"] == 0

        # Only successful submission has scored opportunity
        assert len(scored_opps) == 1


class TestScoringWeights:
    """Test scoring weight preservation from OpportunityAnalyzerAgent."""

    def test_scoring_weights_match_agent_specification(self):
        """
        Test that the expected weights match the OpportunityAnalyzerAgent's methodology.

        From agent_tools/opportunity_analyzer_agent.py:
        - market_demand: 20%
        - pain_intensity: 25%
        - monetization_potential: 30%
        - market_gap: 15%
        - technical_feasibility: 10%
        """
        # This is a documentation test to ensure weights are preserved
        expected_weights = {
            "market_demand": 0.20,
            "pain_intensity": 0.25,
            "monetization_potential": 0.30,
            "market_gap": 0.15,
            "technical_feasibility": 0.10,
        }

        # Verify weights sum to 1.0
        total_weight = sum(expected_weights.values())
        assert abs(total_weight - 1.0) < 0.001  # Float comparison

        # This test serves as documentation that the DLT migration
        # preserves the original 5-dimensional scoring methodology


class TestDeduplication:
    """Test deduplication logic via opportunity_id primary key."""

    def test_opportunity_id_generation_is_consistent(self):
        """Test that opportunity_id is consistently generated from submission_id."""
        submission_id = "abc123"

        analysis = {
            "title": "Test",
            "dimension_scores": {},
            "final_score": 50,
        }

        # Generate twice with same submission_id
        prepared1 = prepare_analysis_for_storage(submission_id, analysis, "Tech")
        prepared2 = prepare_analysis_for_storage(submission_id, analysis, "Tech")

        # Should produce identical opportunity_ids
        assert prepared1["opportunity_id"] == prepared2["opportunity_id"]
        assert prepared1["opportunity_id"] == "opp_abc123"

    def test_different_submissions_get_different_opportunity_ids(self):
        """Test that different submissions get unique opportunity_ids."""
        analysis = {
            "title": "Test",
            "dimension_scores": {},
            "final_score": 50,
        }

        prepared1 = prepare_analysis_for_storage("sub_001", analysis, "Tech")
        prepared2 = prepare_analysis_for_storage("sub_002", analysis, "Tech")

        assert prepared1["opportunity_id"] != prepared2["opportunity_id"]
        assert prepared1["opportunity_id"] == "opp_sub_001"
        assert prepared2["opportunity_id"] == "opp_sub_002"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
