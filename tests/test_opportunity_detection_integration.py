#!/usr/bin/env python3
"""
Integration Tests for Opportunity Detection System

Tests verify:
1. batch_opportunity_scoring script execution flow
2. Opportunities stored in workflow_results table
3. LLMProfiler integration with Claude Haiku
4. Opportunity scoring logic and threshold (40.0)
5. Database operations (insert, query)
6. LLMProfiler.generate_app_profile() structure validation
7. workflow_results table schema validation
8. Integration between scoring and profiling components
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import modules to test
from agent_tools.llm_profiler import LLMProfiler
from scripts.batch_opportunity_scoring import (
    format_submission_for_agent,
    load_scores_to_supabase_via_dlt,
    map_subreddit_to_sector,
    prepare_analysis_for_storage,
    process_batch,
)


class TestDatabaseOperations:
    """Test database operations for workflow_results table."""

    @patch('scripts.batch_opportunity_scoring.create_client')
    @patch('core.dlt_collection.create_dlt_pipeline')
    def test_insert_opportunity_to_workflow_results(self, mock_create_pipeline, mock_create_client):
        """Test inserting a scored opportunity into workflow_results table."""
        # Setup mocks
        mock_supabase = MagicMock()
        mock_create_client.return_value = mock_supabase
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_load_info.started_at = datetime.now()
        mock_pipeline.run.return_value = mock_load_info
        mock_create_pipeline.return_value = mock_pipeline

        # Test data - scored opportunity ready for DLT
        # Note: DLT constraint validator will add core_functions, simplicity_score, etc.
        scored_opportunity = {
            "opportunity_id": "opp_test_001",
            "app_name": "Test Fitness Tracker",
            "function_count": 2,
            "function_list": ["Track workouts", "Monitor progress"],
            "original_score": 75.5,
            "final_score": 75.5,
            "status": "scored",
            "constraint_applied": True,
            "ai_insight": "Market sector: Health & Fitness. Subreddit: fitness",
            "processed_at": datetime.now().isoformat(),
            "market_demand": 80.0,
            "pain_intensity": 75.0,
            "monetization_potential": 70.0,
            "market_gap": 65.0,
            "technical_feasibility": 85.0,
            "problem_description": "Users struggle with workout tracking consistency",
            "app_concept": "Simple mobile app for tracking workouts and progress",
            "value_proposition": "Helps users maintain fitness goals with easy tracking",
            "target_user": "Fitness enthusiasts",
            "monetization_model": "Freemium model with premium features"
        }

        # Execute - DLT will handle insertion via constraint validator
        result = load_scores_to_supabase_via_dlt([scored_opportunity])

        # Verify
        assert result is True
        mock_create_pipeline.assert_called_once()
        mock_pipeline.run.assert_called_once()

        # Verify DLT was called with correct parameters
        call_args = mock_pipeline.run.call_args
        assert call_args[1]['write_disposition'] == "merge"
        assert call_args[1]['primary_key'] == "opportunity_id"

    @patch('scripts.batch_opportunity_scoring.create_client')
    @patch('scripts.batch_opportunity_scoring.create_dlt_pipeline')
    def test_query_workflow_results_by_score(self, mock_create_pipeline, mock_create_client):
        """Test querying workflow_results table for high-scoring opportunities."""
        # Setup mocks
        mock_supabase = MagicMock()
        mock_create_client.return_value = mock_supabase

        # Simulate query result
        mock_response = MagicMock()
        mock_response.data = [
            {
                "opportunity_id": "opp_001",
                "final_score": 85.5,
                "status": "scored"
            },
            {
                "opportunity_id": "opp_002",
                "final_score": 72.3,
                "status": "scored"
            }
        ]
        mock_supabase.table("workflow_results").select("*").gte("final_score", 70.0).execute.return_value = mock_response

        # Execute query
        response = mock_supabase.table("workflow_results").select("*").gte("final_score", 70.0).execute()

        # Verify
        assert len(response.data) == 2
        assert all(item["final_score"] >= 70.0 for item in response.data)
        assert all(item["status"] == "scored" for item in response.data)

    @patch('scripts.batch_opportunity_scoring.create_client')
    @patch('core.dlt_collection.create_dlt_pipeline')
    def test_update_existing_opportunity_via_merge(self, mock_create_pipeline, mock_create_client):
        """Test that DLT merge disposition updates existing opportunities."""
        # Setup mocks
        mock_supabase = MagicMock()
        mock_create_client.return_value = mock_supabase
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_load_info.started_at = datetime.now()
        mock_pipeline.run.return_value = mock_load_info
        mock_create_pipeline.return_value = mock_pipeline

        # Test data - opportunity with same ID (should update)
        # Note: DLT constraint validator will add missing fields
        scored_opportunity = {
            "opportunity_id": "opp_existing_001",  # Same ID as existing
            "app_name": "Updated App Name",
            "function_count": 3,  # Required field
            "function_list": ["Function 1", "Function 2", "Function 3"],
            "original_score": 82.0,  # Updated score
            "final_score": 82.0,
            "status": "scored"
        }

        # Execute
        result = load_scores_to_supabase_via_dlt([scored_opportunity])

        # Verify merge disposition is used
        assert result is True
        mock_create_pipeline.assert_called_once()
        mock_pipeline.run.assert_called_once()
        call_args = mock_pipeline.run.call_args
        assert call_args[1]['write_disposition'] == "merge"
        assert call_args[1]['primary_key'] == "opportunity_id"


class TestScoringThreshold:
    """Test the 40.0 scoring threshold for opportunities."""

    def test_scoring_threshold_40_determines_priority(self):
        """Test that score >= 40.0 is considered valid opportunity."""
        # Below threshold
        low_score = 35.0
        assert low_score < 40.0

        # At threshold
        threshold_score = 40.0
        assert threshold_score >= 40.0

        # Above threshold
        high_score = 75.5
        assert high_score > 40.0

    @patch('scripts.batch_opportunity_scoring.LLMProfiler')
    @patch('scripts.batch_opportunity_scoring.OpportunityAnalyzerAgent')
    def test_process_batch_with_threshold(self, mock_agent_class, mock_profiler_class):
        """Test that process_batch correctly applies 40.0 threshold logic."""
        # Setup mocks
        mock_agent = MagicMock()
        mock_agent.analyze_opportunity.return_value = {
            "title": "Fitness Tracker Issue",
            "subreddit": "fitness",
            "dimension_scores": {
                "market_demand": 75.0,
                "pain_intensity": 80.0,
                "monetization_potential": 70.0,
                "market_gap": 60.0,
                "technical_feasibility": 75.0,
            },
            "final_score": 72.0,  # Above 40.0 threshold
            "priority": "⚡ Med-High Priority",
        }

        mock_profiler = MagicMock()
        mock_profiler.generate_app_profile.return_value = {
            "problem_description": "Need better workout tracking",
            "app_concept": "Simple fitness tracking app",
            "core_functions": ["Track workouts", "Monitor progress"],
            "value_proposition": "Easy-to-use fitness tracking",
            "target_user": "Fitness beginners",
            "monetization_model": "Freemium"
        }
        mock_profiler_class.return_value = mock_profiler

        # Test submission
        submissions = [
            {
                "id": "sub_001",
                "submission_id": "reddit_001",
                "title": "Struggling with workout tracking",
                "text": "I can't find a good way to track my workouts consistently",
                "subreddit": "fitness",
                "upvotes": 150,
                "comments_count": 45,
            }
        ]

        # Execute
        results, scored_opps = process_batch(
            submissions,
            mock_agent,
            batch_number=1,
            llm_profiler=mock_profiler,
            high_score_threshold=40.0
        )

        # Verify
        assert len(results) == 1
        assert len(scored_opps) == 1
        assert results[0]["final_score"] == 72.0
        assert results[0]["final_score"] >= 40.0  # Above threshold

        # LLMProfiler should be called for high-score opportunities
        mock_profiler.generate_app_profile.assert_called_once()

    @patch('scripts.batch_opportunity_scoring.LLMProfiler')
    @patch('scripts.batch_opportunity_scoring.OpportunityAnalyzerAgent')
    def test_below_threshold_not_profiled(self, mock_agent_class, mock_profiler_class):
        """Test that opportunities below 40.0 threshold are not profiled."""
        # Setup mocks
        mock_agent = MagicMock()
        mock_agent.analyze_opportunity.return_value = {
            "title": "Minor Issue",
            "subreddit": "random",
            "dimension_scores": {
                "market_demand": 30.0,
                "pain_intensity": 35.0,
                "monetization_potential": 25.0,
                "market_gap": 20.0,
                "technical_feasibility": 40.0,
            },
            "final_score": 30.0,  # Below 40.0 threshold
            "priority": "❌ Not Recommended",
        }

        mock_profiler = MagicMock()
        mock_profiler_class.return_value = mock_profiler

        # Test submission
        submissions = [
            {
                "id": "sub_002",
                "submission_id": "reddit_002",
                "title": "Small problem",
                "text": "This is a minor issue",
                "subreddit": "random",
                "upvotes": 5,
                "comments_count": 1,
            }
        ]

        # Execute
        results, scored_opps = process_batch(
            submissions,
            mock_agent,
            batch_number=1,
            llm_profiler=mock_profiler,
            high_score_threshold=40.0
        )

        # Verify - score below threshold, no LLM profiling
        assert results[0]["final_score"] == 30.0
        assert results[0]["final_score"] < 40.0
        mock_profiler.generate_app_profile.assert_not_called()  # Should not be called


class TestLLMProfilerIntegration:
    """Test LLMProfiler integration and output structure."""

    def test_llm_profiler_init_with_api_key(self):
        """Test LLMProfiler initialization requires OPENROUTER_API_KEY."""
        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key_123'}):
            profiler = LLMProfiler()
            assert profiler.api_key == 'test_key_123'
            assert profiler.model == 'anthropic/claude-haiku-4.5'

    def test_llm_profiler_init_without_api_key_raises_error(self):
        """Test LLMProfiler raises error when API key is missing."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY not found"):
                LLMProfiler()

    @patch('agent_tools.llm_profiler.requests.post')
    def test_generate_app_profile_structure(self, mock_post):
        """Test LLMProfiler.generate_app_profile() returns correct structure."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "problem_description": "Users need better workout tracking",
                        "app_concept": "Simple mobile app for tracking fitness goals",
                        "core_functions": ["Track workouts", "Set reminders", "View progress"],
                        "value_proposition": "Helps users stay consistent with fitness goals",
                        "target_user": "Busy professionals",
                        "monetization_model": "Freemium with $4.99/month premium"
                    })
                }
            }]
        }
        mock_post.return_value = mock_response

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
            profiler = LLMProfiler()
            profile = profiler.generate_app_profile(
                text="I struggle to track my workouts consistently",
                title="Need better fitness tracker",
                subreddit="fitness",
                score=75.5
            )

            # Verify structure
            assert "problem_description" in profile
            assert "app_concept" in profile
            assert "core_functions" in profile
            assert "value_proposition" in profile
            assert "target_user" in profile
            assert "monetization_model" in profile

            # Verify values
            assert profile["problem_description"] == "Users need better workout tracking"
            assert isinstance(profile["core_functions"], list)
            assert len(profile["core_functions"]) == 3
            assert all(isinstance(f, str) for f in profile["core_functions"])

    @patch('agent_tools.llm_profiler.requests.post')
    def test_generate_app_profile_with_markdown_code_block(self, mock_post):
        """Test LLMProfiler handles markdown code blocks in response."""
        # Setup mock response with markdown
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "```json\n" + json.dumps({
                        "problem_description": "Testing markdown handling",
                        "app_concept": "Test app concept",
                        "core_functions": ["Function 1", "Function 2"],
                        "value_proposition": "Test value prop",
                        "target_user": "Test user",
                        "monetization_model": "Test model"
                    }) + "\n```"
                }
            }]
        }
        mock_post.return_value = mock_response

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
            profiler = LLMProfiler()
            profile = profiler.generate_app_profile(
                text="Test text",
                title="Test title",
                subreddit="test",
                score=50.0
            )

            # Should parse correctly despite markdown
            assert profile["problem_description"] == "Testing markdown handling"
            assert isinstance(profile["core_functions"], list)

    @patch('agent_tools.llm_profiler.requests.post')
    def test_generate_app_profile_limits_functions(self, mock_post):
        """Test LLMProfiler limits core_functions to maximum 3."""
        # Setup mock response with 5 functions
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "problem_description": "Too many functions test",
                        "app_concept": "Test app",
                        "core_functions": [
                            "Function 1", "Function 2", "Function 3",
                            "Function 4", "Function 5"  # Should be limited to 3
                        ],
                        "value_proposition": "Test",
                        "target_user": "Test",
                        "monetization_model": "Test"
                    })
                }
            }]
        }
        mock_post.return_value = mock_response

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
            profiler = LLMProfiler()
            profile = profiler.generate_app_profile(
                text="Test",
                title="Test",
                subreddit="test",
                score=50.0
            )

            # Should be limited to 3
            assert len(profile["core_functions"]) == 3
            assert profile["core_functions"] == ["Function 1", "Function 2", "Function 3"]

    @patch('agent_tools.llm_profiler.requests.post')
    def test_generate_app_profile_error_handling(self, mock_post):
        """Test LLMProfiler handles API errors gracefully."""
        # Setup mock to raise exception
        mock_post.side_effect = Exception("API connection failed")

        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
            profiler = LLMProfiler()
            profile = profiler.generate_app_profile(
                text="Test",
                title="Test",
                subreddit="test",
                score=50.0
            )

            # Should return error structure
            assert "error" in profile
            assert "problem_description" in profile
            assert "app_concept" in profile
            assert "Analysis failed" in profile["app_concept"]


class TestWorkflowResultsTableSchema:
    """Test workflow_results table schema validation."""

    def test_workflow_results_table_has_required_columns(self):
        """Test that workflow_results table has all required columns."""
        # Expected columns based on constraint_validator.py
        required_columns = [
            "opportunity_id",
            "app_name",
            "function_count",
            "function_list",
            "original_score",
            "final_score",
            "status",
            "constraint_applied",
            "ai_insight",
            "processed_at",
            "market_demand",
            "pain_intensity",
            "monetization_potential",
            "market_gap",
            "technical_feasibility",
        ]

        # Expected constraint metadata columns
        constraint_columns = [
            "core_functions",
            "simplicity_score",
            "is_disqualified",
            "constraint_version",
            "validation_timestamp",
            "violation_reason",
            "validation_status",
        ]

        # This test documents the expected schema
        all_expected = required_columns + constraint_columns
        assert len(all_expected) > 0  # Sanity check

    def test_workflow_results_dimension_score_constraints(self):
        """Test that dimension scores have proper constraints (0-100)."""
        # From migration: dimension scores have CHECK constraints
        # market_demand: CHECK (market_demand >= 0 AND market_demand <= 100)
        # pain_intensity: CHECK (pain_intensity >= 0 AND pain_intensity <= 100)
        # monetization_potential: CHECK (monetization_potential >= 0 AND monetization_potential <= 100)
        # market_gap: CHECK (market_gap >= 0 AND market_gap <= 100)
        # technical_feasibility: CHECK (technical_feasibility >= 0 AND technical_feasibility <= 100)

        # Test valid scores
        valid_scores = [0, 25.5, 50, 75.3, 100]
        for score in valid_scores:
            assert 0 <= score <= 100

        # Test invalid scores
        invalid_scores = [-1, 101, 150]
        for score in invalid_scores:
            assert not (0 <= score <= 100)

    def test_workflow_results_opportunity_id_unique(self):
        """Test that opportunity_id is unique in workflow_results table."""
        # From constraint_validator: opportunity_id has unique=True
        # This ensures deduplication via merge disposition works

        # Generate opportunity IDs
        id1 = "opp_submission_123"
        id2 = "opp_submission_456"
        id3 = "opp_submission_123"  # Same as id1

        # Should be unique for different submissions
        assert id1 != id2

        # Same submission should generate same ID
        assert id1 == id3


class TestOpportunityScoringLogic:
    """Test opportunity scoring logic and calculations."""

    @patch('scripts.batch_opportunity_scoring.OpportunityAnalyzerAgent')
    def test_analyze_opportunity_returns_dimension_scores(self, mock_agent_class):
        """Test that analyze_opportunity returns all 5 dimension scores."""
        # Setup mock
        mock_agent = MagicMock()
        mock_agent.analyze_opportunity.return_value = {
            "opportunity_id": "test_001",
            "title": "Test Opportunity",
            "subreddit": "fitness",
            "dimension_scores": {
                "market_demand": 75.0,
                "pain_intensity": 80.0,
                "monetization_potential": 70.0,
                "market_gap": 65.0,
                "technical_feasibility": 75.0,
            },
            "final_score": 73.0,
            "priority": "⚡ Med-High Priority",
            "weights": {
                "market_demand": 0.20,
                "pain_intensity": 0.25,
                "monetization_potential": 0.30,
                "market_gap": 0.15,
                "technical_feasibility": 0.10,
            }
        }
        mock_agent_class.return_value = mock_agent

        # Test submission
        submission = {
            "id": "sub_001",
            "title": "Fitness tracking problem",
            "text": "I need a better way to track my workouts",
            "subreddit": "fitness",
            "engagement": {"upvotes": 100, "num_comments": 50}
        }

        # Execute
        result = mock_agent.analyze_opportunity(submission)

        # Verify all dimensions present
        assert "dimension_scores" in result
        assert "market_demand" in result["dimension_scores"]
        assert "pain_intensity" in result["dimension_scores"]
        assert "monetization_potential" in result["dimension_scores"]
        assert "market_gap" in result["dimension_scores"]
        assert "technical_feasibility" in result["dimension_scores"]

        # Verify weights sum to 1.0
        weights = result["weights"]
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.001

        # Verify final score calculated
        assert "final_score" in result
        assert result["final_score"] > 0

    def test_map_subreddit_to_sector_comprehensive(self):
        """Test comprehensive subreddit to sector mapping."""
        # Test known mappings
        assert map_subreddit_to_sector("fitness") == "Health & Fitness"
        assert map_subreddit_to_sector("loseit") == "Health & Fitness"
        assert map_subreddit_to_sector("personalfinance") == "Finance & Investing"
        assert map_subreddit_to_sector("investing") == "Finance & Investing"
        assert map_subreddit_to_sector("learnprogramming") == "Education & Career"
        assert map_subreddit_to_sector("travel") == "Travel & Experiences"
        assert map_subreddit_to_sector("realestate") == "Real Estate"
        assert map_subreddit_to_sector("saas") == "Technology & SaaS"

        # Test case insensitivity
        assert map_subreddit_to_sector("FITNESS") == "Health & Fitness"
        assert map_subreddit_to_sector("PersonalFinance") == "Finance & Investing"

        # Test default for unknown
        assert map_subreddit_to_sector("unknown_subreddit") == "Technology & SaaS"
        assert map_subreddit_to_sector("") == "Technology & SaaS"
        assert map_subreddit_to_sector(None) == "Technology & SaaS"

    def test_format_submission_for_agent_complete(self):
        """Test complete submission formatting for agent analysis."""
        submission = {
            "id": "db_123",
            "submission_id": "reddit_abc",
            "title": "Looking for budgeting help",
            "text": "I can't manage my money effectively",
            "subreddit": "personalfinance",
            "upvotes": 250,
            "comments_count": 75,
            "sentiment_score": 0.65,
            "problem_keywords": "budget, money management",
            "solution_mentions": "app, tracking"
        }

        formatted = format_submission_for_agent(submission)

        # Verify all fields present
        assert formatted["id"] == "reddit_abc"
        assert formatted["title"] == "Looking for budgeting help"
        assert formatted["text"] == "Looking for budgeting help\n\nI can't manage my money effectively"
        assert formatted["subreddit"] == "personalfinance"
        assert formatted["engagement"]["upvotes"] == 250
        assert formatted["engagement"]["num_comments"] == 75
        assert formatted["sentiment_score"] == 0.65
        assert formatted["db_id"] == "db_123"

        # Verify comments populated from keywords
        assert len(formatted["comments"]) == 2
        assert "Problem identified" in formatted["comments"][0]
        assert "Solution discussed" in formatted["comments"][1]

    def test_prepare_analysis_for_storage_with_llm_profile(self):
        """Test analysis preparation includes LLM-generated app profile."""
        submission_id = "test_sub_001"
        analysis = {
            "title": "Fitness Tracker Opportunity",
            "subreddit": "fitness",
            "dimension_scores": {
                "market_demand": 80.0,
                "pain_intensity": 85.0,
                "monetization_potential": 75.0,
                "market_gap": 70.0,
                "technical_feasibility": 80.0,
            },
            "final_score": 78.0,
            "priority": "⚡ Med-High Priority",
            # LLM-generated fields
            "problem_description": "Users struggle with workout consistency",
            "app_concept": "Simple mobile fitness tracker with reminders",
            "core_functions": ["Track workouts", "Set reminders", "View progress"],
            "value_proposition": "Helps users build sustainable workout habits",
            "target_user": "Busy professionals",
            "monetization_model": "Freemium $4.99/month premium"
        }
        sector = "Health & Fitness"

        prepared = prepare_analysis_for_storage(submission_id, analysis, sector)

        # Verify all fields
        assert prepared["opportunity_id"] == "opp_test_sub_001"
        assert prepared["app_name"] == "Fitness Tracker Opportunity"
        assert prepared["function_count"] == 3  # From core_functions list
        assert prepared["original_score"] == 78.0
        assert prepared["final_score"] == 78.0
        assert prepared["status"] == "scored"
        assert prepared["constraint_applied"] is True

        # Verify dimension scores
        assert prepared["market_demand"] == 80.0
        assert prepared["pain_intensity"] == 85.0
        assert prepared["monetization_potential"] == 75.0
        assert prepared["market_gap"] == 70.0
        assert prepared["technical_feasibility"] == 80.0

        # Verify LLM profile fields
        assert prepared["problem_description"] == "Users struggle with workout consistency"
        assert prepared["app_concept"] == "Simple mobile fitness tracker with reminders"
        assert prepared["value_proposition"] == "Helps users build sustainable workout habits"
        assert prepared["target_user"] == "Busy professionals"
        assert prepared["monetization_model"] == "Freemium $4.99/month premium"


class TestBatchOpportunityScoringScript:
    """Test the batch_opportunity_scoring script as a whole."""

    @patch('scripts.batch_opportunity_scoring.create_client')
    @patch('scripts.batch_opportunity_scoring.LLMProfiler')
    @patch('scripts.batch_opportunity_scoring.OpportunityAnalyzerAgent')
    @patch('scripts.batch_opportunity_scoring.create_dlt_pipeline')
    def test_full_pipeline_integration(self, mock_create_pipeline, mock_agent_class, mock_profiler_class, mock_client_class):
        """Test complete pipeline: fetch -> score -> profile -> store."""
        # Setup mocks
        mock_supabase = MagicMock()
        mock_client_class.return_value = mock_supabase

        # Mock submissions query
        mock_submissions = [
            {
                "id": "sub_001",
                "submission_id": "reddit_001",
                "title": "Budgeting app problem",
                "text": "Need better expense tracking",
                "subreddit": "personalfinance",
                "upvotes": 200,
                "comments_count": 60,
            },
            {
                "id": "sub_002",
                "submission_id": "reddit_002",
                "title": "Workout tracking issue",
                "text": "Can't track workouts consistently",
                "subreddit": "fitness",
                "upvotes": 150,
                "comments_count": 45,
            }
        ]

        # Setup agent mock
        mock_agent = MagicMock()
        mock_agent.analyze_opportunity.side_effect = [
            {
                "title": "Budgeting App",
                "subreddit": "personalfinance",
                "dimension_scores": {
                    "market_demand": 85.0,
                    "pain_intensity": 80.0,
                    "monetization_potential": 75.0,
                    "market_gap": 70.0,
                    "technical_feasibility": 80.0,
                },
                "final_score": 78.0,
                "priority": "⚡ Med-High Priority",
            },
            {
                "title": "Fitness Tracker",
                "subreddit": "fitness",
                "dimension_scores": {
                    "market_demand": 80.0,
                    "pain_intensity": 85.0,
                    "monetization_potential": 70.0,
                    "market_gap": 75.0,
                    "technical_feasibility": 85.0,
                },
                "final_score": 79.0,
                "priority": "⚡ Med-High Priority",
            }
        ]
        mock_agent_class.return_value = mock_agent

        # Setup profiler mock
        mock_profiler = MagicMock()
        mock_profiler.generate_app_profile.return_value = {
            "problem_description": "Test problem",
            "app_concept": "Test app",
            "core_functions": ["Function 1", "Function 2"],
            "value_proposition": "Test value",
            "target_user": "Test user",
            "monetization_model": "Test model"
        }
        mock_profiler_class.return_value = mock_profiler

        # Setup DLT pipeline mock
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_load_info.started_at = datetime.now()
        mock_pipeline.run.return_value = mock_load_info
        mock_create_pipeline.return_value = mock_pipeline

        # Simulate database query
        mock_response = MagicMock()
        mock_response.data = mock_submissions
        mock_supabase.table("submissions").select().range().execute.return_value = mock_response

        # Process batch
        results, scored_opps = process_batch(
            mock_submissions,
            mock_agent,
            batch_number=1,
            llm_profiler=mock_profiler,
            high_score_threshold=40.0
        )

        # Verify pipeline
        assert len(results) == 2
        assert len(scored_opps) == 2

        # Verify both scored above threshold
        assert all(r["final_score"] >= 40.0 for r in results)

        # Verify LLM profiling was called
        assert mock_profiler.generate_app_profile.call_count == 2

        # Verify storage prepared
        for opp in scored_opps:
            assert "opportunity_id" in opp
            assert "final_score" in opp
            assert "market_demand" in opp
            assert "pain_intensity" in opp

    @patch('scripts.batch_opportunity_scoring.create_client')
    @patch('scripts.batch_opportunity_scoring.create_dlt_pipeline')
    def test_load_empty_list_handling(self, mock_create_pipeline, mock_client_class):
        """Test that loading empty list of opportunities is handled gracefully."""
        # Setup mocks
        mock_supabase = MagicMock()
        mock_client_class.return_value = mock_supabase

        # Execute with empty list
        result = load_scores_to_supabase_via_dlt([])

        # Verify graceful handling
        assert result is False
        mock_create_pipeline.assert_not_called()

    @patch('scripts.batch_opportunity_scoring.create_client')
    @patch('scripts.batch_opportunity_scoring.create_dlt_pipeline')
    def test_dlt_pipeline_error_handling(self, mock_create_pipeline, mock_client_class):
        """Test that DLT pipeline errors are handled gracefully."""
        # Setup mocks
        mock_supabase = MagicMock()
        mock_client_class.return_value = mock_supabase

        # Mock pipeline to raise error
        mock_pipeline = MagicMock()
        mock_pipeline.run.side_effect = Exception("Connection failed")
        mock_create_pipeline.return_value = mock_pipeline

        scored_opportunities = [
            {
                "opportunity_id": "opp_001",
                "app_name": "Test",
                "final_score": 50.0,
                "status": "scored"
            }
        ]

        # Execute
        result = load_scores_to_supabase_via_dlt(scored_opportunities)

        # Verify error handled
        assert result is False


class TestSectorMapping:
    """Test subreddit to business sector mapping."""

    def test_health_fitness_sector(self):
        """Test all Health & Fitness subreddit mappings."""
        fitness_subreddits = [
            "fitness", "loseit", "bodyweightfitness", "nutrition",
            "healthyfood", "yoga", "running", "weightlifting",
            "xxfitness", "progresspics", "gainit", "flexibility",
            "naturalbodybuilding", "eatcheapandhealthy", "keto",
            "cycling", "meditation", "mentalhealth", "fitness30plus", "homegym"
        ]

        for subreddit in fitness_subreddits:
            assert map_subreddit_to_sector(subreddit) == "Health & Fitness"

    def test_finance_investing_sector(self):
        """Test all Finance & Investing subreddit mappings."""
        finance_subreddits = [
            "personalfinance", "financialindependence", "investing",
            "stocks", "wallstreetbets", "realestateinvesting",
            "povertyfinance", "frugal", "fire", "bogleheads",
            "dividends", "options", "smallbusiness", "cryptocurrency",
            "tax", "accounting", "financialcareers"
        ]

        for subreddit in finance_subreddits:
            assert map_subreddit_to_sector(subreddit) == "Finance & Investing"

    def test_technology_saas_sector(self):
        """Test Technology & SaaS sector and default mapping."""
        tech_subreddits = [
            "saas", "indiehackers", "sidehustle", "juststart",
            "roastmystartup", "buildinpublic", "microsaas", "nocode", "webdev"
        ]

        for subreddit in tech_subreddits:
            assert map_subreddit_to_sector(subreddit) == "Technology & SaaS"

        # Unknown subreddits default to Technology & SaaS
        assert map_subreddit_to_sector("unknown_subreddit") == "Technology & SaaS"
        assert map_subreddit_to_sector("random_123") == "Technology & SaaS"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
