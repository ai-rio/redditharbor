"""
TDD Tests for MarketResearchAgent Integration into AgnoOpportunityAnalyzer
Phase 3.5 Pipeline Integration

These tests follow the TDD methodology:
1. RED Phase: Tests are written first and initially fail
2. GREEN Phase: Minimal implementation is added to make tests pass
3. REFACTOR Phase: Implementation is cleaned up and improved

Key integration requirements:
- MarketResearchAgent should be added to MockTeam
- Conditional validation based on opportunity score (default threshold: 70.0)
- Market validation results incorporated into final analysis
- Synthesis logic includes market validation evidence
- Cost tracking includes market research costs
- Backward compatibility maintained
"""

import json
from datetime import UTC, datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from models.analysis import AnalysisResult, AppIdea, MarketMetrics
from models.reddit import RedditSubmission

# Import the components to integrate
from transform.agno_analyzer import AgnoOpportunityAnalyzer, MockCostTracker, MockTeam
from transform.agno_synthesis import AgnoSynthesis
from transform.market_research_agent import MarketResearchAgent


class TestMarketResearchAgentIntegrationRED:
    """
    RED Phase: Failing tests for MarketResearchAgent integration

    These tests define the expected behavior and will fail initially.
    They serve as a blueprint for the implementation.
    """

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing"""
        return AgnoOpportunityAnalyzer()

    @pytest.fixture
    def mock_submission(self):
        """Create a mock Reddit submission for testing"""
        return RedditSubmission(
            id="test123",
            title="Looking for workflow automation tool",
            text="I need a tool to automate my business processes and save time",
            author="business_owner",
            score=150,
            upvotes=150,
            downvotes=0,
            comments_count=42,
            subreddit="entrepreneur",
            created_utc=datetime(2024, 1, 1, tzinfo=UTC),
            permalink="/r/entrepreneur/test123"
        )

    def test_mock_team_includes_market_research_agent(self, analyzer):
        """
        RED Test: MockTeam should include MarketResearchAgent

        The team should have 5 agents total:
        - 4 original agents (WTP, Market Segment, Price Point, Payment Behavior)
        - 1 MarketResearchAgent

        This test will fail because the MockTeam currently only has 4 agents.
        """
        # Check that team has 5 agents (4 original + 1 MarketResearchAgent)
        assert len(analyzer.team.agents) == 5, f"Expected 5 agents, got {len(analyzer.team.agents)}"

        # Check that MarketResearchAgent is in the team
        assert analyzer.team.has_agent("Market Research"), "MarketResearchAgent should be in the team"

        # Check that original agents are still present
        assert analyzer.team.has_agent("WTP Analyst"), "Original agents should be preserved"
        assert analyzer.team.has_agent("Market Segment"), "Original agents should be preserved"
        assert analyzer.team.has_agent("Price Point"), "Original agents should be preserved"
        assert analyzer.team.has_agent("Payment Behavior"), "Original agents should be preserved"

    def test_market_research_agent_configured_with_threshold(self, analyzer):
        """
        RED Test: MarketResearchAgent should be configured with validation threshold

        The agent should use the default threshold of 70.0 unless custom configured.
        """
        # Get the MarketResearchAgent from the team
        market_research_agent = analyzer.team.agent_map["Market Research"]

        assert isinstance(market_research_agent, MarketResearchAgent), "Should be a MarketResearchAgent instance"
        assert market_research_agent.validation_threshold == 70.0, "Default threshold should be 70.0"

    def test_analyzer_accepts_custom_validation_threshold(self):
        """
        RED Test: Analyzer should accept custom validation threshold configuration

        Users should be able to configure the threshold at which market validation is triggered.
        """
        # This should fail because the analyzer doesn't currently accept validation_threshold parameter
        analyzer = AgnoOpportunityAnalyzer(validation_threshold=80.0)

        # Check that the MarketResearchAgent has the custom threshold
        market_research_agent = analyzer.team.agent_map["Market Research"]
        assert market_research_agent.validation_threshold == 80.0

    def test_conditional_market_validation_execution(self, analyzer, mock_submission):
        """
        RED Test: Market validation should only run when opportunity score exceeds threshold

        This test will fail because the current implementation doesn't check scores
        before running market validation.
        """
        # Mock the core agents to return a high score (above threshold)
        high_score_results = {
            "WTP Analyst": {"wtp_score": 85, "market_demand_score": 80},
            "Market Segment": {"segment_type": "SMB", "market_demand_score": 75},
            "Price Point": {"monetization_score": 80},
            "Payment Behavior": {"pain_intensity_score": 85}
        }

        # Mock the MarketResearchAgent
        with patch.object(analyzer.team.agent_map["Market Research"], 'run', new_callable=AsyncMock) as mock_market:
            mock_market.return_value = {
                "validation_score": 75.0,
                "competitor_pricing": [{"company": "TestCo", "pricing_model": "subscription"}],
                "reasoning": "Strong market validation found"
            }

            # Mock the other agents to return high scores
            with patch.object(analyzer.team, 'run') as mock_team_run:
                mock_result = Mock()
                mock_result.get_agent_result.side_effect = lambda name: high_score_results.get(name, {})
                mock_team_run.return_value = mock_result

                # Analyze submission
                result = analyzer.analyze_submission(mock_submission)

                # Market validation should have been called because score > 70.0
                mock_market.assert_called_once()

    def test_market_validation_skipped_below_threshold(self, analyzer, mock_submission):
        """
        RED Test: Market validation should be skipped when opportunity score is below threshold

        This test will fail because the current implementation doesn't implement
        conditional logic based on score thresholds.
        """
        # Mock the core agents to return a low score (below threshold)
        low_score_results = {
            "WTP Analyst": {"wtp_score": 40, "market_demand_score": 45},
            "Market Segment": {"segment_type": "Hobby", "market_demand_score": 35},
            "Price Point": {"monetization_score": 30},
            "Payment Behavior": {"pain_intensity_score": 25}
        }

        # Mock the MarketResearchAgent
        with patch.object(analyzer.team.agent_map["Market Research"], 'run', new_callable=AsyncMock) as mock_market:

            # Mock the other agents to return low scores
            with patch.object(analyzer.team, 'run') as mock_team_run:
                mock_result = Mock()
                mock_result.get_agent_result.side_effect = lambda name: low_score_results.get(name, {})
                mock_team_run.return_value = mock_result

                # Analyze submission
                result = analyzer.analyze_submission(mock_submission)

                # Market validation should NOT have been called because score < 70.0
                mock_market.assert_not_called()

    def test_market_validation_results_incorporated_into_synthesis(self, analyzer, mock_submission):
        """
        RED Test: Market validation results should be incorporated into the synthesis

        When market validation runs, its results should be included in the AgnoSynthesis
        and affect the final analysis.
        """
        # Mock market validation results
        market_validation_results = {
            "validation_score": 80.0,
            "data_quality_score": 75.0,
            "competitor_pricing": [
                {
                    "company": "CompetitorA",
                    "pricing_model": "subscription",
                    "tiers": [{"name": "Pro", "price": "$49/mo"}]
                }
            ],
            "market_size": {
                "tam": "$10B",
                "sam": "$1B",
                "growth": "15% CAGR"
            },
            "reasoning": "Strong market opportunity with validated demand"
        }

        # Mock the MarketResearchAgent
        with patch.object(analyzer.team.agent_map["Market Research"], 'run', new_callable=AsyncMock) as mock_market:
            mock_market.return_value = market_validation_results

            # Mock core agents to return high scores
            high_score_results = {
                "WTP Analyst": {"wtp_score": 80, "market_demand_score": 75},
                "Market Segment": {"segment_type": "SMB", "market_demand_score": 85},
                "Price Point": {"monetization_score": 70},
                "Payment Behavior": {"pain_intensity_score": 75}
            }

            with patch.object(analyzer.team, 'run') as mock_team_run:
                mock_result = Mock()
                mock_result.get_agent_result.side_effect = lambda name: high_score_results.get(name, {})
                mock_team_run.return_value = mock_result

                # Analyze submission
                result = analyzer.analyze_submission(mock_submission)

                # Check that market validation evidence is in the reasoning
                assert "market opportunity" in result.app_idea.app_concept.lower() or \
                       "competitor" in result.app_idea.app_concept.lower() or \
                       "validated" in result.app_idea.app_concept.lower(), \
                       "App concept should incorporate market validation evidence"

    def test_cost_tracking_includes_market_research_costs(self, analyzer, mock_submission):
        """
        RED Test: Cost tracking should include market research costs

        When market validation runs, its costs should be tracked and included
        in the total cost summary.
        """
        # Mock market validation with cost
        market_validation_results = {
            "validation_score": 75.0,
            "jina_cost": 0.005,  # $0.005 for market research
            "competitor_pricing": [],
            "reasoning": "Market validation completed"
        }

        # Mock the MarketResearchAgent
        with patch.object(analyzer.team.agent_map["Market Research"], 'run', new_callable=AsyncMock) as mock_market:
            mock_market.return_value = market_validation_results

            # Mock core agents to return high scores
            high_score_results = {
                "WTP Analyst": {"wtp_score": 80, "market_demand_score": 75},
                "Market Segment": {"segment_type": "SMB", "market_demand_score": 85},
                "Price Point": {"monetization_score": 70},
                "Payment Behavior": {"pain_intensity_score": 75}
            }

            with patch.object(analyzer.team, 'run') as mock_team_run:
                mock_result = Mock()
                mock_result.get_agent_result.side_effect = lambda name: high_score_results.get(name, {})
                mock_team_run.return_value = mock_result

                # Track initial cost
                initial_cost = analyzer.cost_tracker.total_cost

                # Analyze submission
                result = analyzer.analyze_submission(mock_submission)

                # Check that market research cost was added
                final_cost = analyzer.cost_tracker.total_cost
                assert final_cost > initial_cost, "Market research costs should be tracked"
                assert final_cost >= initial_cost + 0.005, "Expected market research cost of $0.005 to be included"

    def test_backward_compatibility_with_existing_tests(self, analyzer, mock_submission):
        """
        RED Test: Integration should maintain backward compatibility

        Existing tests should continue to pass without modification.
        The analyzer should work the same way when market validation is not triggered.
        """
        # Mock core agents to return low scores (below threshold to avoid market validation)
        low_score_results = {
            "WTP Analyst": {"wtp_score": 50, "market_demand_score": 55},
            "Market Segment": {"segment_type": "General", "market_demand_score": 45},
            "Price Point": {"monetization_score": 40},
            "Payment Behavior": {"pain_intensity_score": 35}
        }

        # Mock the team run (this should not trigger market validation)
        with patch.object(analyzer.team, 'run') as mock_team_run:
            mock_result = Mock()
            mock_result.get_agent_result.side_effect = lambda name: low_score_results.get(name, {})
            mock_team_run.return_value = mock_result

            # Analyze submission
            result = analyzer.analyze_submission(mock_submission)

            # Should still return a valid AnalysisResult
            assert isinstance(result, AnalysisResult)
            assert result.submission_id == "test123"
            assert result.app_idea is not None
            assert result.market_metrics is not None
            assert result.final_score > 0

    def test_synthesis_includes_market_validation_evidence(self, analyzer, mock_submission):
        """
        RED Test: Synthesis should include market validation evidence in reasoning

        When market validation runs successfully, the evidence should be
        incorporated into the final reasoning.
        """
        # Mock comprehensive market validation results
        market_validation_results = {
            "validation_score": 85.0,
            "competitor_pricing": [
                {
                    "company": "MarketLeader",
                    "pricing_model": "freemium",
                    "tiers": [{"name": "Pro", "price": "$29/mo"}]
                },
                {
                    "company": "EnterpriseTool",
                    "pricing_model": "enterprise",
                    "tiers": [{"name": "Business", "price": "Custom"}]
                }
            ],
            "market_size": {
                "tam": "$50B",
                "sam": "$5B",
                "growth": "20% CAGR",
                "source": "Industry Report 2024"
            },
            "similar_launches": [
                {
                    "product": "AutomationPro",
                    "platform": "Product Hunt",
                    "upvotes": 1500
                }
            ],
            "reasoning": "Validated market with 2 competitors, $50B TAM, and successful similar launches"
        }

        # Mock the MarketResearchAgent
        with patch.object(analyzer.team.agent_map["Market Research"], 'run', new_callable=AsyncMock) as mock_market:
            mock_market.return_value = market_validation_results

            # Mock core agents to return high scores
            high_score_results = {
                "WTP Analyst": {"wtp_score": 85, "market_demand_score": 80},
                "Market Segment": {"segment_type": "Enterprise", "market_demand_score": 85},
                "Price Point": {"monetization_score": 75},
                "Payment Behavior": {"pain_intensity_score": 80}
            }

            with patch.object(analyzer.team, 'run') as mock_team_run:
                mock_result = Mock()
                mock_result.get_agent_result.side_effect = lambda name: high_score_results.get(name, {})
                mock_team_run.return_value = mock_result

                # Analyze submission
                result = analyzer.analyze_submission(mock_submission)

                # Extract the multi-agent reasoning (this might be in different attributes)
                reasoning_text = ""
                if hasattr(result, 'app_idea') and result.app_idea:
                    reasoning_text += str(result.app_idea.app_concept) + " "
                if hasattr(result, 'market_metrics') and result.market_metrics:
                    reasoning_text += str(result.market_metrics) + " "

                # Check for market validation evidence in the reasoning
                evidence_found = any(evidence in reasoning_text.lower() for evidence in [
                    "competitor", "market size", "validation", "tam", "similar launch"
                ])

                assert evidence_found, f"Market validation evidence should be in reasoning. Got: {reasoning_text[:200]}"

    def test_market_research_agent_error_handling(self, analyzer, mock_submission):
        """
        RED Test: MarketResearchAgent errors should be handled gracefully

        If market validation fails, it should not break the entire analysis.
        """
        # Mock the MarketResearchAgent to raise an exception
        with patch.object(analyzer.team.agent_map["Market Research"], 'run', new_callable=AsyncMock) as mock_market:
            mock_market.side_effect = Exception("Market research service unavailable")

            # Mock core agents to return high scores
            with patch.object(analyzer.team, 'run') as mock_team_run:
                mock_result = Mock()
                mock_result.get_agent_result.return_value = {"wtp_score": 80}
                mock_team_run.return_value = mock_result

                # Analyze submission - should not raise an exception
                result = analyzer.analyze_submission(mock_submission)

                # Should still return a valid AnalysisResult
                assert isinstance(result, AnalysisResult)
                assert result.submission_id == "test123"
                assert result.app_idea is not None

    def test_analyzer_supports_market_research_configuration(self):
        """
        RED Test: Analyzer should support market research configuration options

        Users should be able to configure market research behavior.
        """
        # Test various configuration options
        analyzer_configured = AgnoOpportunityAnalyzer(
            validation_threshold=75.0,
            max_competitors=3,
            max_launches=2,
            enable_market_cost_tracking=True
        )

        # Check that the MarketResearchAgent was configured with these options
        market_agent = analyzer_configured.team.agent_map["Market Research"]
        assert market_agent.validation_threshold == 75.0
        assert market_agent.max_competitors == 3
        assert market_agent.max_launches == 2
        assert market_agent.enable_cost_tracking is True


class TestMarketResearchAgentIntegrationGREEN:
    """
    GREEN Phase: Tests that pass after minimal implementation

    These tests will pass once the basic integration is implemented.
    They represent the minimum viable functionality.
    """

    # This class will be populated after RED phase tests are implemented
    pass


class TestMarketResearchAgentIntegrationREFACTOR:
    """
    REFACTOR Phase: Tests for improved implementation

    These tests cover edge cases, performance, and code quality improvements.
    They ensure the implementation is robust and maintainable.
    """

    # This class will be populated after GREEN phase tests pass
    pass
