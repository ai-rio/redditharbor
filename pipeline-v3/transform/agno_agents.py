"""
Specialized agents for Agno multi-agent analysis
"""

from typing import Dict, Any
import json
import logging
from monitoring.metrics_collector import get_collector

logger = logging.getLogger(__name__)


class Agent:
    """Base class for specialized agents"""

    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.name = self.__class__.__name__
        self.metrics = get_collector()

    def run(self, input_data: str) -> str:
        """Run the agent analysis"""
        # Extract opportunity_id from input if possible
        try:
            input_dict = json.loads(input_data) if isinstance(input_data, str) else input_data
            opportunity_id = input_dict.get('opportunity_id', 'unknown')
        except:
            opportunity_id = 'unknown'

        # Get agent short name for metrics
        agent_name = self._get_agent_name()

        # Track execution with metrics
        with self.metrics.track("transform", agent_name=agent_name, opportunity_id=opportunity_id) as context:
            # Get mock response (for now)
            result = self._get_mock_response()

            # Add metadata to context
            context["metadata"] = {
                "agent_name": self.name,
                "model": self.model,
                "input_length": len(str(input_data))
            }

            return json.dumps(result)

    def _get_agent_name(self) -> str:
        """Get short agent name for metrics tracking"""
        name_map = {
            "WillingnessToPayAgent": "wtp",
            "MarketSegmentAgent": "segment",
            "PricePointAgent": "price",
            "PaymentBehaviorAgent": "payment",
            "MarketResearchAgent": "market"
        }
        return name_map.get(self.__class__.__name__, self.__class__.__name__.lower())

    def _get_mock_response(self) -> Dict[str, Any]:
        """Get mock response for testing"""
        return {}


class WillingnessToPayAgent(Agent):
    """Analyzes willingness to pay indicators"""

    def __init__(self, model: str, api_key: str, base_url: str):
        super().__init__(model, api_key, base_url)
        self.name = "Willingness to Pay Analyst"
        self.instructions = "Analyze wtp_score and payment sentiment"

    def _get_mock_response(self) -> Dict[str, Any]:
        return {
            "wtp_score": 75,
            "market_demand_score": 80,
            "sentiment": "Positive",
            "evidence": ["explicit_price_mention", "budget_discussion"]
        }


class MarketSegmentAgent(Agent):
    """Analyzes market segment characteristics"""

    def __init__(self, model: str, api_key: str, base_url: str):
        super().__init__(model, api_key, base_url)
        self.name = "Market Segment Analyst"
        self.instructions = "Analyze segment_type and customer_profile"

    def _get_mock_response(self) -> Dict[str, Any]:
        return {
            "segment_type": "B2B",
            "market_demand_score": 70,
            "customer_profile": "Small Business",
            "indicators": ["business_context", "team_mention"]
        }


class PricePointAgent(Agent):
    """Analyzes price point sensitivity"""

    def __init__(self, model: str, api_key: str, base_url: str):
        super().__init__(model, api_key, base_url)
        self.name = "Price Point Analyst"
        self.instructions = "Analyze price_point and budget_ceiling"

    def _get_mock_response(self) -> Dict[str, Any]:
        return {
            "price_point": 100,
            "monetization_score": 70,
            "budget_ceiling": 150,
            "pricing_model": "Subscription"
        }


class PaymentBehaviorAgent(Agent):
    """Analyzes payment behavior patterns"""

    def __init__(self, model: str, api_key: str, base_url: str):
        super().__init__(model, api_key, base_url)
        self.name = "Payment Behavior Analyst"
        self.instructions = "Analyze purchase_pattern and spending_behavior"

    def _get_mock_response(self) -> Dict[str, Any]:
        return {
            "behavior_score": 90,
            "pain_intensity_score": 70,
            "purchase_pattern": "Subscription",
            "current_spending": "Moderate"
        }