"""
Base test classes providing common functionality for Agno analyzer tests
"""

import pytest
from typing import Dict, Any, Optional
from unittest.mock import Mock, MagicMock
from dataclasses import asdict
import json

# Import the analyzer - handle import errors gracefully
try:
    from core.agents.monetization.agno_analyzer import (
        MonetizationAgnoAnalyzer,
        MonetizationAnalysis
    )
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import Agno analyzer: {e}")
    IMPORTS_AVAILABLE = False


class BaseAgnoTest:
    """Base class for all Agno analyzer tests"""

    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client"""
        return Mock()

    @pytest.fixture
    def mock_agentops(self):
        """Mock AgentOps client"""
        return Mock()

    @pytest.fixture
    def mock_openrouter(self):
        """Mock OpenRouter API"""
        return Mock()

    @pytest.fixture
    def base_analyzer(self, mock_openrouter, mock_agentops):
        """Base analyzer instance with mocked dependencies"""
        if not IMPORTS_AVAILABLE:
            pytest.skip("Agno analyzer not available")

        return MonetizationAgnoAnalyzer(
            model="anthropic/claude-haiku-4.5",
            agentops_api_key="test_key"
        )

    @pytest.fixture
    def sample_analysis_result(self):
        """Sample MonetizationAnalysis result for testing"""
        return MonetizationAnalysis(
            willingness_to_pay_score=75.0,
            market_segment_score=80.0,
            price_sensitivity_score=60.0,
            revenue_potential_score=78.5,
            customer_segment="B2B",
            mentioned_price_points=["$500/month", "$1000/year"],
            existing_payment_behavior="$200/month on Salesforce",
            urgency_level="High",
            sentiment_toward_payment="Positive",
            payment_friction_indicators=["none_detected"],
            llm_monetization_score=82.5,
            confidence=0.85,
            reasoning="Strong B2B signals with clear budget",
            subreddit_multiplier=1.3
        )

    def assert_monetization_analysis_valid(self, analysis):
        """Assert that a MonetizationAnalysis object is valid"""
        assert isinstance(analysis, MonetizationAnalysis)
        assert 0 <= analysis.willingness_to_pay_score <= 100
        assert 0 <= analysis.market_segment_score <= 100
        assert 0 <= analysis.price_sensitivity_score <= 100
        assert 0 <= analysis.revenue_potential_score <= 100
        assert 0 <= analysis.llm_monetization_score <= 100
        assert 0 <= analysis.confidence <= 1
        assert isinstance(analysis.customer_segment, str)
        assert isinstance(analysis.mentioned_price_points, list)
        assert isinstance(analysis.payment_friction_indicators, list)

    def assert_analyzer_initialized(self, analyzer):
        """Assert analyzer is properly initialized"""
        assert analyzer.model is not None
        assert analyzer.agentops_enabled is not None
        assert analyzer.wtp_agent is not None
        assert analyzer.segment_agent is not None
        assert analyzer.price_agent is not None
        assert analyzer.behavior_agent is not None
        assert analyzer.team is not None


class MockAgentResponse:
    """Helper class for creating mock agent responses"""

    @staticmethod
    def create_wtp_response(score: int, sentiment: str, evidence: list = None, reasoning: str = "Test reasoning") -> Dict[str, Any]:
        return {
            "sentiment_toward_payment": sentiment,
            "willingness_to_pay_score": score,
            "evidence": evidence or ["test evidence"],
            "reasoning": reasoning
        }

    @staticmethod
    def create_segment_response(segment: str, confidence: float, indicators: list = None) -> Dict[str, Any]:
        return {
            "customer_segment": segment,
            "confidence": confidence,
            "indicators": indicators or ["test indicator"],
            "segment_score": int(confidence * 100)
        }

    @staticmethod
    def create_price_response(prices: list, budget_ceiling: str = "$500/month") -> Dict[str, Any]:
        price_points = [
            {"price": price, "context": "test context"}
            for price in prices
        ]
        return {
            "mentioned_price_points": price_points,
            "budget_ceiling": budget_ceiling,
            "pricing_model": "Subscription"
        }

    @staticmethod
    def create_behavior_response(spending: str, willingness: str = "High") -> Dict[str, Any]:
        return {
            "current_spending": spending,
            "switching_willingness": willingness,
            "spending_evidence": ["test evidence"],
            "behavior_score": 75
        }

    @staticmethod
    def create_combined_agent_response(wtp: Dict, segment: Dict, price: Dict, behavior: Dict) -> str:
        """Create a combined response string from multiple agents"""
        response_parts = [
            f"WTP Analysis: {json.dumps(wtp)}",
            f"Market Segment: {json.dumps(segment)}",
            f"Price Analysis: {json.dumps(price)}",
            f"Payment Behavior: {json.dumps(behavior)}"
        ]
        return "\n\n".join(response_parts)


class ResponseTestHelper:
    """Helper class for testing response parsing and field mapping"""

    def test_field_mapping_scenarios(self):
        """Test field mapping scenarios"""
        scenarios = [
            # Original field names
            {
                "input": {
                    "sentiment": "Positive",
                    "willingness_score": 85,
                    "segment": "B2B",
                    "price_points": ["$100/month"],
                    "current_spending": "$200/month"
                },
                "expected": {
                    "sentiment_toward_payment": "Positive",
                    "willingness_to_pay_score": 85,
                    "customer_segment": "B2B",
                    "mentioned_price_points": ["$100/month"],
                    "current_spending": "$200/month"
                }
            },
            # Alternative field names
            {
                "input": {
                    "payment_sentiment": "Negative",
                    "wtp_score": 25,
                    "business_type": "B2C",
                    "prices": ["$50/year"],
                    "existing_spending": "$100/month"
                },
                "expected": {
                    "sentiment_toward_payment": "Negative",
                    "willingness_to_pay_score": 25,
                    "customer_segment": "B2C",
                    "mentioned_price_points": ["$50/year"],
                    "current_spending": "$100/month"
                }
            }
        ]
        return scenarios

    def test_json_extraction_scenarios(self):
        """Test JSON extraction scenarios"""
        scenarios = [
            # Valid JSON
            {
                "input": '{"sentiment": "Positive", "score": 85}',
                "should_parse": True
            },
            # Malformed JSON
            {
                "input": '{"sentiment": "Positive", "score": 85',  # Missing closing brace
                "should_parse": False
            },
            # JSON with surrounding text
            {
                "input": 'Analysis result: {"sentiment": "Positive", "score": 85}',
                "should_parse": True
            },
            # No JSON
            {
                "input": 'This is plain text with no JSON',
                "should_parse": False
            }
        ]
        return scenarios

    def test_consensus_calculation_scenarios(self):
        """Test consensus calculation scenarios"""
        scenarios = [
            # High agreement
            {
                "agent_responses": [
                    {"willingness_to_pay_score": 80},
                    {"willingness_to_pay_score": 85},
                    {"willingness_to_pay_score": 82}
                ],
                "expected_confidence": 0.85,
                "expected_agreement": "high"
            },
            # Medium agreement
            {
                "agent_responses": [
                    {"willingness_to_pay_score": 70},
                    {"willingness_to_pay_score": 85},
                    {"willingness_to_pay_score": 90}
                ],
                "expected_confidence": 0.75,
                "expected_agreement": "medium"
            },
            # Low agreement
            {
                "agent_responses": [
                    {"willingness_to_pay_score": 50},
                    {"willingness_to_pay_score": 80},
                    {"willingness_to_pay_score": 95}
                ],
                "expected_confidence": 0.65,
                "expected_agreement": "low"
            }
        ]
        return scenarios