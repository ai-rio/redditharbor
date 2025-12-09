"""
Unit tests for AgnoOpportunityAnalyzer - Phase 1 Implementation

These tests verify the AgnoOpportunityAnalyzer implementation.
"""

import sys
from pathlib import Path

# Add pipeline-v3 to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pipeline-v3"))

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Import the actual implementation
from transform.agno_analyzer import AgnoOpportunityAnalyzer
from transform.agno_agents import (
    WillingnessToPayAgent,
    MarketSegmentAgent,
    PricePointAgent,
    PaymentBehaviorAgent
)
from transform.agno_synthesis import AgnoSynthesis


class TestAgnoOpportunityAnalyzerClassStructure:
    """Test the AgnoOpportunityAnalyzer class initialization and structure"""

    def test_analyzer_initializes_with_4_specialized_agents(self):
        """Test that analyzer creates with exactly 4 specialized agents"""
        analyzer = AgnoOpportunityAnalyzer()

        # Check that team has 4 agents
        assert len(analyzer.team.agents) == 4
        assert analyzer.team.has_agent("WTP Analyst")
        assert analyzer.team.has_agent("Market Segment")
        assert analyzer.team.has_agent("Price Point")
        assert analyzer.team.has_agent("Payment Behavior")

    def test_analyzer_accepts_custom_model_configuration(self):
        """Test analyzer accepts custom model configuration"""
        analyzer = AgnoOpportunityAnalyzer(
            model="anthropic/claude-opus-4",
            base_url="https://custom-api.com"
        )
        # Check that agents have the custom model
        assert analyzer.wtp_agent.model == "anthropic/claude-opus-4"
        assert analyzer.wtp_agent.base_url == "https://custom-api.com"

    def test_analyzer_model_configuration_defaults(self):
        """Test analyzer uses correct default model configuration"""
        analyzer = AgnoOpportunityAnalyzer()
        assert analyzer.wtp_agent.model == "anthropic/claude-haiku-4.5"

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
        assert "wtp_score" in agent._get_mock_response()

    def test_market_segment_agent_structure(self):
        """Test MarketSegmentAgent class structure and initialization"""
        agent = MarketSegmentAgent("anthropic/claude-haiku-4.5", "test_key", "https://openrouter.ai/api/v1")
        assert agent.name == "Market Segment Analyst"
        assert "segment_type" in agent.instructions

    def test_price_point_agent_structure(self):
        """Test PricePointAgent class structure and initialization"""
        agent = PricePointAgent("anthropic/claude-haiku-4.5", "test_key", "https://openrouter.ai/api/v1")
        assert agent.name == "Price Point Analyst"
        assert "price_point" in agent.instructions

    def test_payment_behavior_agent_structure(self):
        """Test PaymentBehaviorAgent class structure and initialization"""
        agent = PaymentBehaviorAgent("anthropic/claude-haiku-4.5", "test_key", "https://openrouter.ai/api/v1")
        assert agent.name == "Payment Behavior Analyst"
        assert "purchase_pattern" in agent.instructions


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