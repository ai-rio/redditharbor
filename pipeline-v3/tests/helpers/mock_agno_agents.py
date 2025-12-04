"""
Mock implementations of Agno agents for testing
"""

from unittest.mock import Mock
from typing import Dict, Any, Optional
import json
import asyncio


class MockWTPAgent:
    """Mock Willingness to Pay Agent"""

    def __init__(self, response_data: Optional[Dict[str, Any]] = None):
        self.response_data = response_data or {
            "sentiment_toward_payment": "Positive",
            "willingness_to_pay_score": 75,
            "evidence": ["test evidence"],
            "reasoning": "Test reasoning for WTP"
        }

    def run(self, prompt: str) -> str:
        """Mock run method"""
        # Simulate processing delay
        asyncio.sleep(0.01)
        return json.dumps(self.response_data)

    async def run_async(self, prompt: str) -> Dict[str, Any]:
        """Mock async run method"""
        await asyncio.sleep(0.01)
        return self.response_data


class MockSegmentAgent:
    """Mock Market Segment Agent"""

    def __init__(self, response_data: Optional[Dict[str, Any]] = None):
        self.response_data = response_data or {
            "customer_segment": "B2B",
            "confidence": 0.8,
            "indicators": ["business", "team"],
            "segment_score": 80
        }

    def run(self, prompt: str) -> str:
        """Mock run method"""
        asyncio.sleep(0.01)
        return json.dumps(self.response_data)

    async def run_async(self, prompt: str) -> Dict[str, Any]:
        """Mock async run method"""
        await asyncio.sleep(0.01)
        return self.response_data


class MockPriceAgent:
    """Mock Price Point Agent"""

    def __init__(self, response_data: Optional[Dict[str, Any]] = None):
        self.response_data = response_data or {
            "mentioned_price_points": [
                {"price": "$100/month", "context": "budget"}
            ],
            "budget_ceiling": "$150/month",
            "pricing_model": "Subscription"
        }

    def run(self, prompt: str) -> str:
        """Mock run method"""
        asyncio.sleep(0.01)
        return json.dumps(self.response_data)

    async def run_async(self, prompt: str) -> Dict[str, Any]:
        """Mock async run method"""
        await asyncio.sleep(0.01)
        return self.response_data


class MockBehaviorAgent:
    """Mock Payment Behavior Agent"""

    def __init__(self, response_data: Optional[Dict[str, Any]] = None):
        self.response_data = response_data or {
            "current_spending": "$200/month on Salesforce",
            "switching_willingness": "Medium",
            "spending_evidence": ["current pain points"],
            "behavior_score": 65
        }

    def run(self, prompt: str) -> str:
        """Mock run method"""
        asyncio.sleep(0.01)
        return json.dumps(self.response_data)

    async def run_async(self, prompt: str) -> Dict[str, Any]:
        """Mock async run method"""
        await asyncio.sleep(0.01)
        return self.response_data


class MockAgnoTeam:
    """Mock Agno Team for coordinated testing"""

    def __init__(self, agents: Optional[Dict[str, Mock]] = None):
        self.agents = agents or {
            "wtp": MockWTPAgent(),
            "segment": MockSegmentAgent(),
            "price": MockPriceAgent(),
            "behavior": MockBehaviorAgent()
        }
        self.execution_history = []

    def run_agent(self, agent_name: str, prompt: str) -> str:
        """Run a specific mock agent"""
        if agent_name in self.agents:
            start_time = asyncio.get_event_loop().time()
            response = self.agents[agent_name].run(prompt)
            end_time = asyncio.get_event_loop().time()

            self.execution_history.append({
                "agent": agent_name,
                "prompt": prompt[:100] + "...",  # Truncate for storage
                "response": response,
                "duration": end_time - start_time,
                "timestamp": start_time
            })
            return response
        raise ValueError(f"Unknown agent: {agent_name}")

    def run_all_agents(self, prompt: str) -> Dict[str, str]:
        """Run all agents and return responses"""
        responses = {}
        for agent_name in self.agents:
            responses[agent_name] = self.run_agent(agent_name, prompt)
        return responses

    def set_agent_response(self, agent_name: str, response_data: Dict[str, Any]):
        """Set custom response for an agent"""
        if agent_name == "wtp":
            self.agents["wtp"] = MockWTPAgent(response_data)
        elif agent_name == "segment":
            self.agents["segment"] = MockSegmentAgent(response_data)
        elif agent_name == "price":
            self.agents["price"] = MockPriceAgent(response_data)
        elif agent_name == "behavior":
            self.agents["behavior"] = MockBehaviorAgent(response_data)
        else:
            raise ValueError(f"Unknown agent: {agent_name}")

    def get_execution_history(self) -> list:
        """Get execution history for verification"""
        return self.execution_history.copy()

    def clear_history(self):
        """Clear execution history"""
        self.execution_history = []


class MockAgnoAnalyzer:
    """Mock version of MonetizationAgnoAnalyzer for testing"""

    def __init__(self, model: str = "test_model"):
        self.model = model
        self.team = MockAgnoTeam()
        self.agentops_enabled = False
        self.session_id = "test_session"

    def analyze(self, text: str, subreddit: str, keyword_monetization_score: float = None):
        """Mock analyze method"""
        # Create analysis prompt
        prompt = f"Analyze this text: {text} from subreddit: {subreddit}"

        # Run all agents
        responses = self.team.run_all_agents(prompt)

        # Parse responses (simplified)
        analysis_data = self._parse_responses(responses)

        # Return mock analysis
        from dataclasses import dataclass
        from datetime import datetime

        @dataclass
        class MockAnalysis:
            willingness_to_pay_score: float
            market_segment_score: float
            price_sensitivity_score: float
            revenue_potential_score: float
            customer_segment: str
            mentioned_price_points: list
            existing_payment_behavior: str
            urgency_level: str
            sentiment_toward_payment: str
            payment_friction_indicators: list
            llm_monetization_score: float
            confidence: float
            reasoning: str
            subreddit_multiplier: float

        return MockAnalysis(
            willingness_to_pay_score=analysis_data.get("willingness_to_pay_score", 75.0),
            market_segment_score=85.0,
            price_sensitivity_score=60.0,
            revenue_potential_score=78.5,
            customer_segment=analysis_data.get("customer_segment", "B2B"),
            mentioned_price_points=analysis_data.get("mentioned_price_points", []),
            existing_payment_behavior="$200/month",
            urgency_level="Medium",
            sentiment_toward_payment=analysis_data.get("sentiment_toward_payment", "Neutral"),
            payment_friction_indicators=["none_detected"],
            llm_monetization_score=82.5,
            confidence=0.85,
            reasoning="Mock analysis result",
            subreddit_multiplier=1.0
        )

    async def analyze_stream(self, text: str, subreddit: str, keyword_monetization_score: float = None):
        """Mock streaming analyze method"""
        import json
        from datetime import datetime

        # Mock streaming chunks
        chunks = [
            {
                "step": "initiation",
                "message": "Starting multi-agent analysis",
                "timestamp": datetime.now().isoformat(),
            },
            {
                "step": "willingness_analysis",
                "result": {"willingness_to_pay_score": 75},
                "timestamp": datetime.now().isoformat(),
            },
            {
                "step": "final_analysis",
                "result": {"llm_monetization_score": 82.5},
                "timestamp": datetime.now().isoformat(),
            }
        ]

        for chunk in chunks:
            yield json.dumps(chunk)

    def _parse_responses(self, responses: Dict[str, str]) -> Dict[str, Any]:
        """Parse agent responses (simplified)"""
        parsed = {}
        for agent_name, response in responses.items():
            try:
                # Extract JSON from response
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    data = json.loads(json_str)
                    parsed.update(data)
            except json.JSONDecodeError:
                # Handle non-JSON responses
                if agent_name == "wtp":
                    parsed["willingness_to_pay_score"] = 75
                    parsed["sentiment_toward_payment"] = "Neutral"
                elif agent_name == "segment":
                    parsed["customer_segment"] = "Unknown"
        return parsed


class ErrorSimulator:
    """Helper class for simulating various error scenarios"""

    @staticmethod
    def create_timeout_agent():
        """Create an agent that simulates timeout"""
        class TimeoutAgent(Mock):
            def run(self, prompt: str):
                import asyncio
                asyncio.sleep(2)  # Simulate timeout
                return "timeout_response"

        return TimeoutAgent()

    @staticmethod
    def create_error_agent(error_type: str = "json_parse_error"):
        """Create an agent that simulates errors"""
        class ErrorAgent(Mock):
            def run(self, prompt: str):
                if error_type == "json_parse_error":
                    return "{ invalid json"
                elif error_type == "network_error":
                    raise Exception("Network connection failed")
                elif error_type == "empty_response":
                    return ""
                else:
                    return "normal_response"

        return ErrorAgent()

    @staticmethod
    def create_inconsistent_agent():
        """Create an agent with inconsistent responses"""
        class InconsistentAgent(Mock):
            def __init__(self):
                self.call_count = 0

            def run(self, prompt: str):
                self.call_count += 1
                if self.call_count % 3 == 0:
                    return '{"score": 10, "sentiment": "Negative"}'  # Very different response
                else:
                    return '{"score": 80, "sentiment": "Positive"}'

        return InconsistentAgent()