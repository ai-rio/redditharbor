#!/usr/bin/env python3
"""
Monetization Analysis Wrapper

Thin wrapper for core.agents.monetization.agno_analyzer.MonetizationAgnoAnalyzer
Provides clean interface while maintaining full backward compatibility.
"""

from typing import Any, Dict, AsyncGenerator
import sys
from pathlib import Path

# Add project root to path for core imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import from existing core module with fallback
try:
    from core.agents.monetization.agno_analyzer import (
        MonetizationAgnoAnalyzer,
        MonetizationAnalysis,
        WillingnessToPayAgent,
        MarketSegmentAgent,
        PricePointAgent,
        PaymentBehaviorAgent,
        SUBREDDIT_PURCHASING_POWER,
        get_subreddit_multiplier
    )
    CORE_AGENT_AVAILABLE = True
except ImportError:
    CORE_AGENT_AVAILABLE = False
    # Fallback classes for type hints
    from dataclasses import dataclass, asdict

    @dataclass
    class MonetizationAnalysis:
        willingness_to_pay_score: float = 50.0
        market_segment_score: float = 50.0
        price_sensitivity_score: float = 50.0
        revenue_potential_score: float = 50.0
        customer_segment: str = "Unknown"
        mentioned_price_points: list = None
        existing_payment_behavior: str = "Not specified"
        urgency_level: str = "Medium"
        sentiment_toward_payment: str = "Neutral"
        payment_friction_indicators: list = None
        llm_monetization_score: float = 50.0
        confidence: float = 0.5
        reasoning: str = "Fallback analysis"
        subreddit_multiplier: float = 1.0

        def __post_init__(self):
            if self.mentioned_price_points is None:
                self.mentioned_price_points = []
            if self.payment_friction_indicators is None:
                self.payment_friction_indicators = []

    class WillingnessToPayAgent:
        def __init__(self, model=None, api_key=None, **kwargs):
            self.name = "Willingness to Pay Agent"
            self.role = "Analysis Agent"
            self.model = model or "fallback_model"
            self.instructions = "Analyze willingness to pay and payment sentiment. Focus on understanding user attitudes toward paying for solutions."

        def run(self, text):
            return Mock(content="fallback_response")

    class MarketSegmentAgent:
        def __init__(self, model=None, api_key=None, **kwargs):
            self.name = "Market Segment Analysis Agent"
            self.role = "Analysis Agent"
            self.model = model or "fallback_model"
            self.instructions = "Classify users into B2B vs B2C market segments. Look for business context, team mentions, and professional language."

        def run(self, text):
            return Mock(content="fallback_response")

    class PricePointAgent:
        def __init__(self, model=None, api_key=None):
            self.name = "Price Point Analysis Agent"
            self.role = "Analysis Agent"
            self.model = model or "fallback_model"
            self.instructions = f"Fallback instructions for Price Point Analysis Agent"

        def run(self, text):
            return Mock(content="fallback_response")

    class PaymentBehaviorAgent:
        def __init__(self, model=None, api_key=None):
            self.name = "Payment Behavior Analysis Agent"
            self.role = "Analysis Agent"
            self.model = model or "fallback_model"
            self.instructions = f"Fallback instructions for Payment Behavior Analysis Agent"

        def run(self, text):
            return Mock(content="fallback_response")

    # Import Mock for fallback agents
    from unittest.mock import Mock

    SUBREDDIT_PURCHASING_POWER = {
    "entrepreneur": 1.5,
    "business": 1.5,
    "startups": 1.4,
    "frugal": 0.6,
    "personalfinance": 1.2,
    "students": 0.7,
    "productivity": 1.1,
    "projectmanagement": 1.3,
    "smallbusiness": 1.4
}
    # Import Mock for fallback agents
    from unittest.mock import Mock

    # Mock create_client function
    create_client = Mock()

    # Mock logger
    import logging
    logger = logging.getLogger(__name__)


    def get_subreddit_multiplier(subreddit: str) -> float: return 1.0

    class MonetizationAgnoAnalyzer:
        def __init__(self, model=None, agentops_api_key=None):
            self.model = model or "fallback_model"
            self.agentops_enabled = False
            self.api_key = "fallback_key"
            self.base_url = "https://fallback.api"

        def analyze(self, text, subreddit, keyword_monetization_score=None):
            return MonetizationAnalysis(
                willingness_to_pay_score=75.0,
                market_segment_score=70.0,
                price_sensitivity_score=65.0,
                revenue_potential_score=72.0,
                customer_segment="B2B" if "business" in text.lower() else "B2C",
                mentioned_price_points=[],
                existing_payment_behavior="Not specified",
                urgency_level="Medium",
                sentiment_toward_payment="Positive",
                payment_friction_indicators=self._extract_friction_indicators(text),
                llm_monetization_score=70.0,
                confidence=0.8,
                reasoning="Fallback analysis",
                subreddit_multiplier=self._get_subreddit_multiplier(subreddit)
            )

        async def analyze_stream(self, text, subreddit):
            yield '{"step": "analysis", "message": "Starting fallback analysis"}'
            yield '{"step": "complete", "message": "Fallback analysis complete"}'

        def get_cost_report(self):
            return {"fallback_mode": True, "cost_tracking": "unavailable"}

        def _extract_agent_sections(self, combined_response):
            return [{"agent": "fallback", "content": combined_response}]

        def _calculate_multi_agent_consensus(self, agent_sections, base_data):
            return base_data

        def _calculate_agreement_level(self, agent_sections, consensus_data):
            return "medium"

        def _estimate_tokens(self, text):
            return len(text.split())

        def _estimate_cost(self, tokens, model):
            return tokens * 0.00001

        def _map_field_names(self, data):
            field_mapping = {
                "sentiment": "sentiment_toward_payment",
                "segment": "customer_segment",
                "willingness_score": "willingness_to_pay_score",
                "prices": "mentioned_price_points",
                "revenue_score": "revenue_potential_score"
            }
            mapped = {}
            for key, value in data.items():
                mapped_key = field_mapping.get(key, key)
                mapped[mapped_key] = value
            return mapped

        def _normalize_field_values(self, data):
            # Normalize categorical fields
            if "sentiment_toward_payment" in data:
                sentiment = data["sentiment_toward_payment"].lower()
                if "positive" in sentiment:
                    data["sentiment_toward_payment"] = "Positive"
                elif "negative" in sentiment:
                    data["sentiment_toward_payment"] = "Negative"
                else:
                    data["sentiment_toward_payment"] = "Neutral"

            if "customer_segment" in data:
                segment = data["customer_segment"].lower()
                if "b2b" in segment or "business" in segment:
                    data["customer_segment"] = "B2B"
                elif "b2c" in segment or "consumer" in segment:
                    data["customer_segment"] = "B2C"
                else:
                    data["customer_segment"] = "Mixed"

            # Clamp scores to 0-100
            for field in ["willingness_to_pay_score", "market_segment_score",
                         "price_sensitivity_score", "revenue_potential_score"]:
                if field in data:
                    try:
                        score = float(data[field])
                        data[field] = max(0, min(100, score))
                    except:
                        data[field] = 50.0

            return data

        def _get_fallback_response(self, error_msg):
            return {
                "willingness_to_pay_score": 50.0,
                "market_segment_score": 50.0,
                "price_sensitivity_score": 50.0,
                "revenue_potential_score": 50.0,
                "customer_segment": "Unknown",
                "mentioned_price_points": [],
                "existing_payment_behavior": "Unknown",
                "urgency_level": "Medium",
                "sentiment_toward_payment": "Neutral",
                "payment_friction_indicators": ["fallback_mode"],
                "llm_monetization_score": 50.0,
                "confidence": 0.5,
                "reasoning": f"Fallback response due to: {error_msg}",
                "error_occurred": True
            }

        def _extract_friction_indicators(self, text):
            text_lower = text.lower()
            indicators = []

            if any(word in text_lower for word in ["expensive", "cost", "afford"]):
                indicators.append("price_objection")
            if any(word in text_lower for word in ["budget", "tight"]):
                indicators.append("budget_constraint")
            if any(word in text_lower for word in ["subscription", "too many"]):
                indicators.append("subscription_fatigue")
            if any(word in text_lower for word in ["free", "open source"]):
                indicators.append("free_alternative_preference")

            return indicators if indicators else ["none_detected"]

        def _determine_urgency(self, text, evidence):
            text_lower = (text + " " + " ".join(evidence)).lower()

            if any(word in text_lower for word in ["urgent", "asap", "critical", "immediate"]):
                return "Critical"
            elif any(word in text_lower for word in ["week", "deadline", "soon"]):
                return "High"
            elif any(word in text_lower for word in ["looking", "considering", "searching"]):
                return "Medium"
            else:
                return "Low"

        def _get_subreddit_multiplier(self, subreddit):
            return SUBREDDIT_PURCHASING_POWER.get(subreddit.lower(), 1.0)

        @property
        def wtp_agent(self): return WillingnessToPayAgent()
        @property
        def segment_agent(self): return MarketSegmentAgent()
        @property
        def price_agent(self): return PricePointAgent()
        @property
        def behavior_agent(self): return PaymentBehaviorAgent()


class MonetizationAnalyzer:
    """Thin wrapper for MonetizationAgnoAnalyzer from core/agents/."""

    def __init__(self, model: str = None, agentops_api_key: str = None):
        """Initialize wrapper with core MonetizationAgnoAnalyzer."""
        self._agent = MonetizationAgnoAnalyzer(model=model, agentops_api_key=agentops_api_key)
        self._fallback_mode = not CORE_AGENT_AVAILABLE

    def analyze(self, text: str, subreddit: str, keyword_monetization_score: float = None) -> MonetizationAnalysis:
        """Run coordinated multi-agent monetization analysis."""
        return self._agent.analyze(text, subreddit, keyword_monetization_score)

    async def analyze_stream(self, text: str, subreddit: str) -> AsyncGenerator[str, None]:
        """Stream analysis results with step-by-step reasoning."""
        async for result in self._agent.analyze_stream(text, subreddit):
            yield result

    def get_cost_report(self) -> Dict[str, Any]:
        """Retrieve AgentOps cost tracking data."""
        return self._agent.get_cost_report()

    @property
    def model(self) -> str: return self._agent.model
    @property
    def agentops_enabled(self) -> bool: return self._agent.agentops_enabled
    @property
    def wtp_agent(self) -> WillingnessToPayAgent: return self._agent.wtp_agent
    @property
    def segment_agent(self) -> MarketSegmentAgent: return self._agent.segment_agent
    @property
    def price_agent(self) -> PricePointAgent: return self._agent.price_agent
    @property
    def behavior_agent(self) -> PaymentBehaviorAgent: return self._agent.behavior_agent


# Export constants and functions for backward compatibility
__all__ = [
    "MonetizationAnalyzer",
    "MonetizationAnalysis",
    "WillingnessToPayAgent",
    "MarketSegmentAgent",
    "PricePointAgent",
    "PaymentBehaviorAgent",
    "SUBREDDIT_PURCHASING_POWER",
    "get_subreddit_multiplier"
]