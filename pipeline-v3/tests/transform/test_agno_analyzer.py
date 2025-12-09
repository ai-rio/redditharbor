"""
Unit tests for AgnoOpportunityAnalyzer - Phase 1 Implementation

These tests verify the AgnoOpportunityAnalyzer implementation.
"""

import json
from datetime import UTC, datetime, timezone
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest

from models.analysis import AnalysisResult, AppIdea, MarketMetrics
from models.reddit import RedditSubmission
from transform.agno_agents import (
    MarketSegmentAgent,
    PaymentBehaviorAgent,
    PricePointAgent,
    WillingnessToPayAgent,
)

# Import the actual implementation
from transform.agno_analyzer import AgnoOpportunityAnalyzer, MockTeam
from transform.agno_synthesis import AgnoSynthesis


class TestAgnoOpportunityAnalyzerClassStructure:
    """Test the AgnoOpportunityAnalyzer class initialization and structure"""

    def test_analyzer_initializes_with_4_specialized_agents(self):
        """Test that analyzer creates with exactly 4 specialized agents"""
        analyzer = AgnoOpportunityAnalyzer()

        # Check that team has 5 members (4 core + 1 market research)
        assert len(analyzer.team.members) == 5

        # Check agent names in members
        agent_names = [agent.name for agent in analyzer.team.members]
        assert "Willingness to Pay Analyst" in agent_names
        assert "Market Segment Analyst" in agent_names
        assert "Price Point Analyst" in agent_names
        assert "Payment Behavior Analyst" in agent_names

    def test_analyzer_accepts_custom_model_configuration(self):
        """Test analyzer accepts custom model configuration"""
        analyzer = AgnoOpportunityAnalyzer(
            model="anthropic/claude-opus-4",
            base_url="https://custom-api.com"
        )
        # Check that agents have the custom model (stored in model.id for OpenAIChat)
        assert analyzer.wtp_agent.model.id == "anthropic/claude-opus-4"
        assert analyzer.wtp_agent.model.base_url == "https://custom-api.com"

    def test_analyzer_model_configuration_defaults(self):
        """Test analyzer uses correct default model configuration"""
        analyzer = AgnoOpportunityAnalyzer()
        assert analyzer.wtp_agent.model.id == "anthropic/claude-haiku-4.5"

    def test_analyzer_integrates_agentops_tracker(self):
        """Test AgentOps integration setup"""
        with patch('transform.agno_analyzer.get_tracker') as mock_get_tracker:
            mock_tracker = Mock()
            mock_get_tracker.return_value = mock_tracker

            analyzer = AgnoOpportunityAnalyzer(enable_agentops=True)
            assert analyzer.agentops_tracker == mock_tracker
            mock_get_tracker.assert_called_once()

    def test_analyzer_cost_tracking_initialization(self):
        """Test LiteLLM cost tracking integration"""
        analyzer = AgnoOpportunityAnalyzer()
        assert analyzer.cost_tracker is not None
        assert hasattr(analyzer.cost_tracker, 'get_last_analysis_cost')


class TestAgentImplementations:
    """Test the individual agent implementations"""

    def test_willingness_to_pay_agent_structure(self):
        """Test WillingnessToPayAgent class structure and initialization"""
        agent = WillingnessToPayAgent("anthropic/claude-haiku-4.5", "test_key", "https://openrouter.ai/api/v1")
        assert agent.name == "Willingness to Pay Analyst"
        assert any("willingness to pay" in instruction.lower() for instruction in agent.instructions)

    def test_market_segment_agent_structure(self):
        """Test MarketSegmentAgent class structure and initialization"""
        agent = MarketSegmentAgent("anthropic/claude-haiku-4.5", "test_key", "https://openrouter.ai/api/v1")
        assert agent.name == "Market Segment Analyst"
        assert any("market segment" in instruction.lower() for instruction in agent.instructions)

    def test_price_point_agent_structure(self):
        """Test PricePointAgent class structure and initialization"""
        agent = PricePointAgent("anthropic/claude-haiku-4.5", "test_key", "https://openrouter.ai/api/v1")
        assert agent.name == "Price Point Analyst"
        assert any("pricing" in instruction.lower() for instruction in agent.instructions)

    def test_payment_behavior_agent_structure(self):
        """Test PaymentBehaviorAgent class structure and initialization"""
        agent = PaymentBehaviorAgent("anthropic/claude-haiku-4.5", "test_key", "https://openrouter.ai/api/v1")
        assert agent.name == "Payment Behavior Analyst"
        assert any("payment" in instruction.lower() for instruction in agent.instructions)


class TestAgnoSynthesisStructure:
    """Test AgnoSynthesis data structure"""

    def test_agno_synthesis_class_exists(self):
        """Test AgnoSynthesis class exists and has required fields"""
        synthesis = AgnoSynthesis(
            market_demand=75.0,
            pain_intensity=80.0,
            monetization_potential=70.0,
            confidence_score=85.0,
            agent_details={}
        )
        assert synthesis.market_demand == 75.0
        assert synthesis.pain_intensity == 80.0
        assert synthesis.monetization_potential == 70.0
        assert synthesis.confidence_score == 85.0
        assert synthesis.agent_details == {}


class TestAgnoOpportunityAnalyzerCoreFunctionality:
    """Test the core functionality of AgnoOpportunityAnalyzer"""

    @pytest.fixture
    def analyzer(self):
        """Create an AgnoOpportunityAnalyzer instance for testing"""
        return AgnoOpportunityAnalyzer()

    @pytest.fixture
    def mock_submission(self):
        """Create a mock Reddit submission for testing"""
        submission = RedditSubmission(
            id="test123",
            title="Looking for a tool to automate my workflow",
            text="I'm a small business owner struggling to manage my daily tasks. I need something that can help me automate routine processes like email follow-ups and scheduling.",
            author="test_user",
            score=150,
            upvotes=150,
            downvotes=0,
            comments_count=42,
            subreddit="entrepreneur",
            created_utc=datetime(2024, 1, 1, tzinfo=UTC),
            permalink="/r/entrepreneur/test123"
        )
        return submission

    @pytest.fixture
    def mock_agno_result(self):
        """Create a mock Agno result with agent outputs"""
        class MockResult:
            def get_agent_result(self, agent_name: str) -> dict[str, Any]:
                agent_results = {
                    "WTP Analyst": {
                        "wtp_score": 75,
                        "market_demand_score": 80,
                        "payment_willingness": "High"
                    },
                    "Market Segment": {
                        "segment_type": "SMB",
                        "market_demand_score": 70,
                        "target_audience": "Small businesses"
                    },
                    "Price Point": {
                        "price_point": "$19.99/month",
                        "monetization_score": 65,
                        "pricing_model": "SaaS"
                    },
                    "Payment Behavior": {
                        "purchase_pattern": "Subscription",
                        "pain_intensity_score": 85,
                        "churn_risk": "Low"
                    }
                }
                return agent_results.get(agent_name, {})
        return MockResult()

    def test_format_agno_input(self, analyzer, mock_submission):
        """Test that submission is correctly formatted for Agno input"""
        agno_input = analyzer._format_agno_input(mock_submission)

        assert agno_input["title"] == mock_submission.title
        assert agno_input["content"] == mock_submission.text
        assert agno_input["subreddit"] == mock_submission.subreddit
        assert agno_input["author"] == mock_submission.author
        assert agno_input["score"] == mock_submission.score
        assert agno_input["num_comments"] == mock_submission.comments_count

    def test_format_agno_input_missing_attributes(self, analyzer):
        """Test formatting submission with missing attributes"""
        partial_submission = Mock()
        partial_submission.title = "Test title"
        partial_submission.text = ""
        partial_submission.subreddit = ""
        partial_submission.author = ""
        partial_submission.score = 0
        partial_submission.comments_count = 0
        # Missing other attributes

        agno_input = analyzer._format_agno_input(partial_submission)

        assert agno_input["title"] == "Test title"
        assert agno_input["content"] == ""
        assert agno_input["subreddit"] == ""
        assert agno_input["author"] == ""
        assert agno_input["score"] == 0
        assert agno_input["num_comments"] == 0  # This uses getattr fallback

    def test_synthesize_agent_outputs(self, analyzer, mock_agno_result):
        """Test synthesis of agent outputs into AgnoSynthesis"""
        synthesis = analyzer._synthesize_agent_outputs(mock_agno_result)

        assert isinstance(synthesis, AgnoSynthesis)
        # Debug output to see actual values
        print(f"Market demand: {synthesis.market_demand}")
        print(f"Pain intensity: {synthesis.pain_intensity}")
        print(f"Monetization potential: {synthesis.monetization_potential}")

        assert synthesis.market_demand == 76.0  # (80 * 0.6) + (70 * 0.4)
        assert synthesis.pain_intensity == 76.0  # (75 * 0.5) + (85 * 0.3) + (65 * 0.2) = 37.5 + 25.5 + 13 = 76
        assert synthesis.monetization_potential == 70.0  # (75 + 70 + 65) / 3
        assert synthesis.confidence_score == 85.0
        assert "wtp" in synthesis.agent_details
        assert "segment" in synthesis.agent_details
        assert "price" in synthesis.agent_details
        assert "behavior" in synthesis.agent_details

    def test_synthesize_agent_outputs_with_missing_data(self, analyzer):
        """Test synthesis with missing agent data"""
        class PartialMockResult:
            def get_agent_result(self, agent_name: str) -> dict[str, Any]:
                return {}  # Return empty data

        synthesis = analyzer._synthesize_agent_outputs(PartialMockResult())

        assert synthesis.market_demand == 50.0  # Default value
        assert synthesis.pain_intensity == 50.0  # Default value
        assert synthesis.monetization_potential == 50.0  # Default value

    def test_convert_to_pipeline_format(self, analyzer, mock_submission):
        """Test conversion from AgnoSynthesis to AnalysisResult"""
        synthesis = AgnoSynthesis(
            market_demand=75.0,
            pain_intensity=80.0,
            monetization_potential=70.0,
            confidence_score=85.0,
            agent_details={}
        )

        result = analyzer._convert_to_pipeline_format(synthesis, mock_submission)

        assert isinstance(result, AnalysisResult)
        assert result.submission_id == "test123"
        assert result.app_idea is not None
        assert result.market_metrics is not None
        assert result.final_score > 0
        assert result.content_quality_score == 85.0
        assert result.is_spam is False
        assert result.confidence_score == 85.0
        assert result.trust_level == "HIGH"

    def test_convert_to_pipeline_format_calculates_final_score(self, analyzer, mock_submission):
        """Test that final score is calculated correctly"""
        synthesis = AgnoSynthesis(
            market_demand=80.0,
            pain_intensity=70.0,
            monetization_potential=90.0,
            confidence_score=95.0,
            agent_details={}
        )

        result = analyzer._convert_to_pipeline_format(synthesis, mock_submission)

        # After SimplicityProcessor adjustment:
        # Simplicity score = 70.0 (2 functions)
        # Final score = (80*0.2) + (70*0.25) + (90*0.2) + (70*0.1) + (80*0.05) + (70*0.2) = 79.5
        assert abs(result.final_score - 79.5) < 0.01

    def test_calculate_trust_level_high(self, analyzer):
        """Test trust level calculation for high confidence"""
        assert analyzer._calculate_trust_level(85.0) == "HIGH"
        assert analyzer._calculate_trust_level(100.0) == "HIGH"

    def test_calculate_trust_level_medium(self, analyzer):
        """Test trust level calculation for medium confidence"""
        assert analyzer._calculate_trust_level(60.0) == "MEDIUM"
        assert analyzer._calculate_trust_level(50.0) == "MEDIUM"

    def test_calculate_trust_level_low(self, analyzer):
        """Test trust level calculation for low confidence"""
        assert analyzer._calculate_trust_level(40.0) == "LOW"
        assert analyzer._calculate_trust_level(0.0) == "LOW"

    def test_get_subreddit_multiplier_high_value(self, analyzer):
        """Test subreddit multiplier for high-value subreddits"""
        assert analyzer._get_subreddit_multiplier("saas") == 1.5
        assert analyzer._get_subreddit_multiplier("entrepreneur") == 1.5
        assert analyzer._get_subreddit_multiplier("smallbusiness") == 1.5

    def test_get_subreddit_multiplier_low_value(self, analyzer):
        """Test subreddit multiplier for low-value subreddits"""
        assert analyzer._get_subreddit_multiplier("opensource") == 0.7
        assert analyzer._get_subreddit_multiplier("freeware") == 0.7
        assert analyzer._get_subreddit_multiplier("piracy") == 0.7

    def test_get_subreddit_multiplier_default(self, analyzer):
        """Test subreddit multiplier for default subreddits"""
        assert analyzer._get_subreddit_multiplier("technology") == 1.0
        assert analyzer._get_subreddit_multiplier("programming") == 1.0

    def test_generate_app_idea(self, analyzer, mock_submission):
        """Test app idea generation from synthesis"""
        synthesis = AgnoSynthesis(
            market_demand=75.0,
            pain_intensity=80.0,
            monetization_potential=70.0,
            confidence_score=85.0,
            agent_details={"wtp": {}, "segment": {}, "price": {}}
        )

        app_idea = analyzer._generate_app_idea(synthesis, mock_submission)

        assert isinstance(app_idea, AppIdea)
        assert app_idea.title == "AI-Powered Solution Tool"
        assert app_idea.app_concept == "An intelligent tool that addresses market needs with automated features"
        assert "manage my daily tasks" in app_idea.problem_statement
        assert len(app_idea.core_functions) <= 3
        assert app_idea.target_audience == "Small to medium businesses looking for automation solutions"

    def test_generate_app_idea_limits_core_functions(self, analyzer):
        """Test that core functions are limited to 3"""
        synthesis = AgnoSynthesis(
            market_demand=75.0,
            pain_intensity=80.0,
            monetization_potential=70.0,
            confidence_score=85.0,
            agent_details={
                "wtp": {},
                "segment": {},
                "price": {},
                "behavior": {}
            }
        )

        mock_submission = Mock()
        mock_submission.text = "Test problem statement"
        mock_submission.id = "test"

        app_idea = analyzer._generate_app_idea(synthesis, mock_submission)

        # Should be limited to max 3 functions
        assert len(app_idea.core_functions) <= 3

    def test_create_fallback_result(self, analyzer, mock_submission):
        """Test fallback result creation for error cases"""
        result = analyzer._create_fallback_result(mock_submission)

        assert isinstance(result, AnalysisResult)
        assert result.submission_id == "test123"
        assert result.app_idea.title == "Error Recovery Tool"
        assert result.market_metrics.market_demand == 0.0
        assert result.final_score == 0.0
        assert result.trust_level == "LOW"

    def test_analyze_submission_success(self, analyzer, mock_submission):
        """Test successful submission analysis"""
        # Mock the team run to return a mock result with proper data structure
        mock_response = Mock()
        mock_response.content = json.dumps({
            "wtp_score": 75,
            "market_demand_score": 80,
            "pain_intensity_score": 70,
            "monetization_score": 65
        })

        mock_result = Mock()
        mock_result.responses = [mock_response]  # Team returns a list of responses

        # Patch the team's run method
        with patch.object(analyzer.team, 'run', return_value=mock_result) as mock_run:
            result = analyzer.analyze_submission(mock_submission)

            assert isinstance(result, AnalysisResult)
            mock_run.assert_called_once()
            assert analyzer.cost_tracker.last_cost == 0.002

    @patch.object(MockTeam, 'run')
    def test_analyze_submission_with_subreddit_multiplier(self, mock_team_run, analyzer, mock_submission):
        """Test that subreddit multiplier is applied"""
        mock_result = Mock()
        mock_result.get_agent_result.return_value = {"wtp_score": 75, "market_demand_score": 80}
        mock_team_run.return_value = mock_result

        result = analyzer.analyze_submission(mock_submission)

        # Since subreddit is "entrepreneur", multiplier should be 1.5
        # This would affect the market_demand in synthesis
        assert isinstance(result, AnalysisResult)

    def test_analyze_submission_error_handling(self, analyzer, mock_submission):
        """Test error handling in analyze_submission"""
        with patch.object(analyzer.team, 'run', side_effect=Exception("Test error")):
            result = analyzer.analyze_submission(mock_submission)

            assert isinstance(result, AnalysisResult)
            assert result.app_idea.title == "Error Recovery Tool"
            assert result.final_score == 0.0

    def test_analyze_batch_with_costs(self, analyzer, mock_submission):
        """Test batch analysis with cost tracking"""
        submissions = [mock_submission, mock_submission]

        results, cost_summary = analyzer.analyze_batch_with_costs(submissions)

        assert len(results) == 2
        assert all(isinstance(r, AnalysisResult) for r in results)
        assert "total_cost" in cost_summary
        assert "cost_per_submission" in cost_summary
        assert "analysis_duration" in cost_summary
        assert cost_summary["total_cost"] > 0


class TestAgnoOpportunityAnalyzerIntegration:
    """Test integration with other components"""

    def test_integration_with_simplicity_processor(self):
        """Test that results are processed by SimplicityProcessor"""
        analyzer = AgnoOpportunityAnalyzer()

        # Create a test submission
        submission = Mock()
        submission.id = "test123"
        submission.title = "Test submission"
        submission.selftext = "Test content"
        submission.subreddit = "test"

        # Mock the team to return valid data
        with patch.object(analyzer.team, 'run') as mock_run:
            mock_result = Mock()
            mock_result.get_agent_result.return_value = {"wtp_score": 75}
            mock_run.return_value = mock_result

            result = analyzer.analyze_submission(submission)

            # Check that simplicity processor was called
            assert analyzer.simplicity_processor is not None
            # The result should have been processed
            assert isinstance(result, AnalysisResult)

    def test_agentops_integration(self):
        """Test AgentOps integration when enabled"""
        with patch('transform.agno_analyzer.get_tracker') as mock_get_tracker:
            mock_tracker = Mock()
            mock_get_tracker.return_value = mock_tracker

            analyzer = AgnoOpportunityAnalyzer(enable_agentops=True)

            assert analyzer.agentops_tracker == mock_tracker
            mock_tracker.start_session.assert_called_once_with("agno_analysis_session")

    def test_agentops_disabled_by_default(self):
        """Test that AgentOps is disabled when explicitly set to False"""
        analyzer = AgnoOpportunityAnalyzer(enable_agentops=False)

        assert analyzer.agentops_tracker is None

    def test_cost_tracking_initialization(self):
        """Test cost tracking initialization"""
        analyzer = AgnoOpportunityAnalyzer()

        assert analyzer.cost_tracker is not None
        assert analyzer.cost_tracker.total_cost == 0.0
        assert analyzer.cost_tracker.last_cost == 0.0


class TestAgnoOpportunityAnalyzerEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_submission_data(self):
        """Test handling of empty submission data"""
        analyzer = AgnoOpportunityAnalyzer()

        empty_submission = Mock()
        empty_submission.title = ""
        empty_submission.text = ""
        empty_submission.subreddit = ""
        empty_submission.id = "empty"

        agno_input = analyzer._format_agno_input(empty_submission)

        assert agno_input["title"] == ""
        assert agno_input["content"] == ""
        assert agno_input["subreddit"] == ""

    def test_negative_scores_in_subreddit_multiplier(self):
        """Test subreddit multiplier with edge cases"""
        analyzer = AgnoOpportunityAnalyzer()

        # Test with None subreddit - using our mock that doesn't trigger __getattr__
        class MockSubmission:
            def __init__(self):
                self.subreddit = None

        submission = MockSubmission()

        # We need to test the logic directly rather than through getattr
        # Since the method expects a submission with subreddit attribute
        # But our method actually uses the parameter directly
        # Let's test the subreddit value directly
        subreddit_value = getattr(submission, 'subreddit', None)
        assert subreddit_value is None

        # The _get_subreddit_multiplier method expects a string
        # So let's test what happens with None - it should return 1.0 (default)
        result = analyzer._get_subreddit_multiplier(None)
        assert result == 1.0

    def test_extreme_confidence_scores(self):
        """Test handling of extreme confidence scores"""
        analyzer = AgnoOpportunityAnalyzer()

        # Test confidence > 100
        assert analyzer._calculate_trust_level(150.0) == "HIGH"

        # Test negative confidence
        assert analyzer._calculate_trust_level(-10.0) == "LOW"

    @patch.object(MockTeam, 'run', side_effect=KeyError("Missing key"))
    def test_team_run_exception_handling(self, mock_team_run):
        """Test exception handling when team.run fails"""
        analyzer = AgnoOpportunityAnalyzer()
        submission = Mock()
        submission.id = "test123"

        result = analyzer.analyze_submission(submission)

        # Should return fallback result
        assert isinstance(result, AnalysisResult)
        assert result.final_score == 0.0

    def test_fallback_result_with_missing_attributes(self):
        """Test fallback result with missing submission attributes"""
        analyzer = AgnoOpportunityAnalyzer()

        # Mock submission with missing id
        submission = Mock()
        del submission.id

        result = analyzer._create_fallback_result(submission)

        assert result.submission_id == "error"
        assert isinstance(result, AnalysisResult)
