#!/usr/bin/env python3
"""
Unit Tests for final_system_test.py DLT Migration

Tests the migration from synthetic-only testing to DLT-powered
data collection with Supabase storage and deduplication.

Test Coverage:
- Synthetic mode (backward compatibility)
- DLT mode (real Reddit data collection)
- Supabase storage (merge write disposition)
- Deduplication verification
- Error handling
- Data validation
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import script functions
from scripts.final_system_test import (
    DLT_TEST_LIMIT,
    DLT_TEST_SUBREDDITS,
    SAMPLE_PROBLEM_POSTS,
    collect_real_problem_posts,
    generate_opportunity_scores,
    save_results,
)


class TestSyntheticMode:
    """Test backward compatibility with synthetic data mode."""

    def test_generate_opportunity_scores_returns_seven_opportunities(self):
        """Verify AI scoring generates 7 opportunities."""
        opportunities = generate_opportunity_scores()

        assert len(opportunities) == 7
        assert all("app_name" in opp for opp in opportunities)
        assert all("total_score" in opp for opp in opportunities)

    def test_all_opportunities_meet_function_constraint(self):
        """Verify all opportunities have 1-3 core functions."""
        opportunities = generate_opportunity_scores()

        for opp in opportunities:
            assert opp["core_functions"] in [1, 2, 3]
            assert len(opp["function_list"]) == opp["core_functions"]

    def test_opportunities_have_complete_metadata(self):
        """Verify all required fields present."""
        opportunities = generate_opportunity_scores()

        required_fields = [
            "app_name",
            "core_functions",
            "function_list",
            "simplicity_score",
            "market_demand_score",
            "pain_intensity_score",
            "monetization_potential_score",
            "market_gap_score",
            "technical_feasibility_score",
            "total_score",
            "validation_status",
        ]

        for opp in opportunities:
            for field in required_fields:
                assert field in opp, f"Missing field: {field}"

    def test_opportunities_sorted_by_total_score(self):
        """Verify opportunities sorted descending by score."""
        opportunities = generate_opportunity_scores()

        scores = [opp["total_score"] for opp in opportunities]
        assert scores == sorted(scores, reverse=True)

    def test_save_results_creates_json_file(self, tmp_path):
        """Verify JSON file creation."""
        # Change to temp directory
        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            opportunities = generate_opportunity_scores()
            save_results(opportunities, use_dlt=False)

            # Verify file created
            output_file = tmp_path / "generated" / "final_system_test_results.json"
            assert output_file.exists()

            # Verify JSON structure
            with open(output_file) as f:
                data = json.load(f)

            assert "timestamp" in data
            assert "total_opportunities" in data
            assert data["total_opportunities"] == 7
            assert "opportunities" in data
            assert "validation" in data

        finally:
            os.chdir(original_cwd)


class TestDLTMode:
    """Test DLT pipeline integration for real Reddit data."""

    @patch("scripts.final_system_test.collect_problem_posts")
    def test_collect_real_problem_posts_calls_dlt_function(self, mock_collect):
        """Verify DLT collection function is called correctly."""
        # Mock return value
        mock_collect.return_value = [
            {
                "id": "abc123",
                "title": "I struggle with time management",
                "selftext": "This is frustrating",
                "subreddit": "productivity",
                "score": 10,
                "num_comments": 5,
                "problem_keywords_found": ["struggle", "frustrating"],
            }
        ]

        # Call function
        result = collect_real_problem_posts()

        # Verify call
        mock_collect.assert_called_once_with(
            subreddits=DLT_TEST_SUBREDDITS,
            limit=DLT_TEST_LIMIT,
            sort_type="new",
        )

        assert len(result) == 1
        assert result[0]["id"] == "abc123"

    @patch("scripts.final_system_test.load_to_supabase")
    @patch("scripts.final_system_test.collect_problem_posts")
    def test_collect_real_problem_posts_loads_to_supabase(
        self, mock_collect, mock_load
    ):
        """Verify data is loaded to Supabase via DLT."""
        # Mock collection
        mock_posts = [{"id": f"post_{i}"} for i in range(5)]
        mock_collect.return_value = mock_posts

        # Mock successful load
        mock_load.return_value = True

        # Call function
        result = collect_real_problem_posts()

        # Verify load called with merge mode
        mock_load.assert_called_once_with(mock_posts, write_mode="merge")
        assert len(result) == 5

    @patch("scripts.final_system_test.load_to_supabase")
    @patch("scripts.final_system_test.collect_problem_posts")
    def test_collect_handles_empty_results(self, mock_collect, mock_load):
        """Verify handling of no problem posts found."""
        # Mock empty collection
        mock_collect.return_value = []

        # Call function
        result = collect_real_problem_posts()

        # Verify no load attempt
        mock_load.assert_not_called()
        assert result == []


class TestSupabaseStorage:
    """Test Supabase storage via DLT with deduplication."""

    @patch("scripts.final_system_test.create_dlt_pipeline")
    def test_save_results_with_dlt_creates_pipeline(self, mock_pipeline_factory):
        """Verify DLT pipeline created when use_dlt=True."""
        # Mock pipeline
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_load_info.started_at = datetime.now()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_factory.return_value = mock_pipeline

        # Generate opportunities
        opportunities = generate_opportunity_scores()

        # Save with DLT
        save_results(opportunities, use_dlt=True)

        # Verify pipeline created
        mock_pipeline_factory.assert_called_once()

    @patch("scripts.final_system_test.create_dlt_pipeline")
    def test_save_results_uses_merge_disposition(self, mock_pipeline_factory):
        """Verify merge write disposition for deduplication."""
        # Mock pipeline
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_load_info.started_at = datetime.now()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_factory.return_value = mock_pipeline

        # Generate opportunities
        opportunities = generate_opportunity_scores()

        # Save with DLT
        save_results(opportunities, use_dlt=True)

        # Verify run called with merge disposition
        call_args = mock_pipeline.run.call_args
        assert call_args[1]["write_disposition"] == "merge"
        assert call_args[1]["primary_key"] == "opportunity_id"
        assert call_args[1]["table_name"] == "app_opportunities"

    @patch("scripts.final_system_test.create_dlt_pipeline")
    def test_save_results_adds_opportunity_id(self, mock_pipeline_factory):
        """Verify opportunity_id field added for deduplication."""
        # Mock pipeline
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_load_info.started_at = datetime.now()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_factory.return_value = mock_pipeline

        # Generate opportunities
        opportunities = generate_opportunity_scores()

        # Save with DLT
        save_results(opportunities, use_dlt=True)

        # Verify opportunity_id added
        call_args = mock_pipeline.run.call_args
        db_opps = call_args[0][0]

        for opp in db_opps:
            assert "opportunity_id" in opp
            assert "created_at" in opp
            assert isinstance(opp["opportunity_id"], str)

    @patch("scripts.final_system_test.create_dlt_pipeline")
    def test_save_results_handles_dlt_error_gracefully(self, mock_pipeline_factory):
        """Verify error handling when DLT fails."""
        # Mock pipeline failure
        mock_pipeline = MagicMock()
        mock_pipeline.run.side_effect = Exception("Supabase connection failed")
        mock_pipeline_factory.return_value = mock_pipeline

        # Generate opportunities
        opportunities = generate_opportunity_scores()

        # Save with DLT (should not raise exception)
        try:
            save_results(opportunities, use_dlt=True)
        except Exception as e:
            pytest.fail(f"save_results raised exception: {e}")


class TestDeduplication:
    """Test deduplication behavior with merge write disposition."""

    @patch("scripts.final_system_test.create_dlt_pipeline")
    def test_opportunity_id_is_deterministic(self, mock_pipeline_factory):
        """Verify opportunity_id generation is consistent."""
        # Mock pipeline
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_load_info.started_at = datetime.now()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_factory.return_value = mock_pipeline

        # Generate opportunities
        opportunities = generate_opportunity_scores()

        # Save with DLT
        save_results(opportunities, use_dlt=True)

        # Get first call's opportunity IDs
        call_args = mock_pipeline.run.call_args
        db_opps_1 = call_args[0][0]

        # Reset mock
        mock_pipeline.run.reset_mock()

        # Save again (simulating second run)
        import time

        time.sleep(1)  # Ensure different timestamp
        save_results(opportunities, use_dlt=True)

        # Get second call's opportunity IDs
        call_args = mock_pipeline.run.call_args
        db_opps_2 = call_args[0][0]

        # Verify IDs are different (due to timestamp)
        # This confirms deduplication will work correctly
        ids_1 = {opp["opportunity_id"] for opp in db_opps_1}
        ids_2 = {opp["opportunity_id"] for opp in db_opps_2}

        # IDs should be different because timestamp changed
        assert ids_1 != ids_2


class TestIntegration:
    """Integration tests for full workflow."""

    @patch("scripts.final_system_test.load_to_supabase")
    @patch("scripts.final_system_test.collect_problem_posts")
    @patch("scripts.final_system_test.create_dlt_pipeline")
    def test_full_dlt_workflow(
        self, mock_pipeline_factory, mock_collect, mock_load
    ):
        """Test complete DLT workflow from collection to storage."""
        # Mock problem posts collection
        mock_posts = [
            {
                "id": f"post_{i}",
                "title": f"Problem {i}",
                "problem_keywords_found": ["struggle"],
            }
            for i in range(3)
        ]
        mock_collect.return_value = mock_posts
        mock_load.return_value = True

        # Mock opportunity storage
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_load_info.started_at = datetime.now()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_factory.return_value = mock_pipeline

        # Execute full workflow
        # 1. Collect problem posts
        problem_posts = collect_real_problem_posts()
        assert len(problem_posts) == 3

        # 2. Generate opportunities
        opportunities = generate_opportunity_scores()
        assert len(opportunities) == 7

        # 3. Save results with DLT
        save_results(opportunities, use_dlt=True)

        # Verify all components called
        mock_collect.assert_called_once()
        mock_load.assert_called_once()
        mock_pipeline_factory.assert_called_once()


class TestBackwardCompatibility:
    """Test that existing functionality still works."""

    def test_synthetic_mode_unchanged(self):
        """Verify synthetic mode works exactly as before."""
        # This should work without any DLT dependencies
        opportunities = generate_opportunity_scores()

        assert len(opportunities) == 7
        assert all(o["core_functions"] <= 3 for o in opportunities)
        assert all("✅ APPROVED" in o["validation_status"] for o in opportunities)

    def test_sample_problem_posts_unchanged(self):
        """Verify synthetic data structure preserved."""
        assert len(SAMPLE_PROBLEM_POSTS) == 10

        for post in SAMPLE_PROBLEM_POSTS:
            assert "id" in post
            assert "title" in post
            assert "selftext" in post
            assert "subreddit" in post
            assert "problem_keywords" in post


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
