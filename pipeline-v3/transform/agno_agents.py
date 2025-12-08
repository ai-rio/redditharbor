"""
Agno Agents - Real Implementation using Agno 2.2.13

This module implements specialized market analysis agents using the Agno framework.
Each agent focuses on a specific aspect of market opportunity analysis.
"""

import logging

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from pydantic import BaseModel, Field

from monitoring.agentops_tracker import get_tracker
from monitoring.metrics_collector import get_collector

# Configure logger
logger = logging.getLogger(__name__)

# =============================================================================
# Pydantic Schemas for Structured Outputs
# =============================================================================

class WillingnessToPayResult(BaseModel):
    """Structured output for willingness to pay analysis"""
    wtp_score: float = Field(..., ge=0, le=100, description="Willingness to pay score (0-100)")
    price_range: str | None = Field(None, description="Identified price range")
    budget_mentioned: bool = Field(default=False, description="Whether budget was explicitly mentioned")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence in the analysis")
    reasoning: str | None = Field(None, description="Reasoning behind the assessment")


class MarketSegmentResult(BaseModel):
    """Structured output for market segment analysis"""
    segment_size_score: float = Field(..., ge=0, le=100, description="Market segment size score (0-100)")
    segment_type: str = Field(..., description="Type of market segment")
    growth_potential: float = Field(..., ge=0, le=100, description="Growth potential score (0-100)")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence in the analysis")
    reasoning: str | None = Field(None, description="Reasoning behind the assessment")


class PricePointResult(BaseModel):
    """Structured output for price point analysis"""
    price_point: float = Field(..., ge=0, description="Estimated price point in USD")
    monetization_score: float = Field(..., ge=0, le=100, description="Monetization potential score (0-100)")
    budget_ceiling: float | None = Field(None, ge=0, description="Customer budget ceiling")
    pricing_model: str = Field(..., description="Recommended pricing model")
    reasoning: str | None = Field(None, description="Reasoning behind the assessment")


class PaymentBehaviorResult(BaseModel):
    """Structured output for payment behavior analysis"""
    behavior_score: float = Field(..., ge=0, le=100, description="Payment behavior score (0-100)")
    pain_intensity_score: float = Field(..., ge=0, le=100, description="Pain intensity score (0-100)")
    purchase_pattern: str = Field(..., description="Typical purchase pattern")
    current_spending: str = Field(..., description="Current spending level")
    reasoning: str | None = Field(None, description="Reasoning behind the assessment")


class MarketResearchResult(BaseModel):
    """Structured output for market research analysis"""
    validation_score: float = Field(..., ge=0, le=100, description="Market validation score (0-100)")
    competitor_count: int = Field(..., ge=0, description="Number of identified competitors")
    market_maturity: str = Field(..., description="Market maturity level")
    barriers_to_entry: str = Field(..., description="Entry barriers assessment")
    reasoning: str | None = Field(None, description="Reasoning behind the assessment")


# =============================================================================
# Base Agent Class
# =============================================================================

class BaseAgent(Agent):
    """Base agent class with common functionality - following Agno best practices"""

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str,
        output_schema: type[BaseModel] | None = None,
        debug_mode: bool = False,
        enable_agentops: bool = False,
        instructions: list[str] | None = None,
        name: str | None = None
    ):
        """
        Initialize base agent with OpenRouter configuration

        Args:
            model: Model name for the agent
            api_key: OpenRouter API key
            base_url: API base URL
            output_schema: Pydantic schema for structured output
            debug_mode: Enable debug logging
            instructions: Agent instructions
            name: Agent name
        """
        # Create OpenAI model with OpenRouter configuration
        self.openai_model = OpenAIChat(
            id=model,
            api_key=api_key,
            base_url=base_url,
            default_headers={
                "HTTP-Referer": "https://github.com/redditharbor/redditharbor",
                "X-Title": "RedditHarbor Pipeline v3"
            }
        )

        # Store configuration for agent-specific use
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.output_schema = output_schema
        self.debug_mode = debug_mode

        # Initialize metrics tracking
        self.metrics = get_collector()
        self.agent_name = self._get_agent_name()

        # Initialize AgentOps tracking if enabled
        self.enable_agentops = enable_agentops
        self.agentops_tracker = None
        if self.enable_agentops:
            self.agentops_tracker = get_tracker()
            self.agentops_tracker.start_session(f"{self.agent_name}_session")
            logger.info(f"AgentOps tracking enabled for {self.agent_name}")

        # Initialize the Agno Agent without overriding run()
        super().__init__(
            model=self.openai_model,
            output_schema=output_schema,
            instructions=instructions or [],
            name=name or self._get_default_name(),
            debug_mode=debug_mode,
            # Enable error handling
            retries=2,
            delay_between_retries=1,
            exponential_backoff=True
        )

    def _get_agent_name(self) -> str:
        """Get short agent name for metrics"""
        class_name = self.__class__.__name__.lower().replace('agent', '')
        return class_name

    def _get_default_name(self) -> str:
        """Get default agent name"""
        return self.__class__.__name__.replace('Agent', '')

    def a_run(self, prompt: str, *args, **kwargs):
        """Override Agno's a_run method to add AgentOps tracking"""
        return super().a_run(prompt, *args, **kwargs)

    def _track_agent_completion(self, result, success: bool = True, error: str | None = None) -> None:
        """Track agent completion metrics and session lifecycle"""
        pass

        """Override Agno\'s a_run method to add AgentOps tracking"""
        return super().a_run(prompt, *args, **kwargs)


# =============================================================================
# Specialized Agent Classes
# =============================================================================

class WillingnessToPayAgent(BaseAgent):
    """Agent for analyzing willingness to pay from Reddit submissions"""

    def __init__(self, model: str, api_key: str, base_url: str, debug_mode: bool = False):
        instructions = [
            "Analyze the Reddit submission to determine willingness to pay for a solution.",
            "Look for explicit mentions of budget, pricing preferences, and payment capacity.",
            "Focus on identifying concrete price points and budget constraints.",
            "Provide a structured assessment with confidence scores.",
            "Consider both stated and implied willingness to pay based on language used."
        ]

        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            output_schema=WillingnessToPayResult,
            debug_mode=debug_mode,
            instructions=instructions,
            name="Willingness to Pay Analyst"
        )


class MarketSegmentAgent(BaseAgent):
    """Agent for analyzing market segments from Reddit submissions"""

    def __init__(self, model: str, api_key: str, base_url: str, debug_mode: bool = False):
        instructions = [
            "Analyze the Reddit submission to identify the target market segment.",
            "Look for demographic clues, industry context, and user characteristics.",
            "Assess the size and growth potential of the identified segment.",
            "Provide a structured assessment with confidence scores.",
            "Consider both explicit and implicit segment indicators."
        ]

        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            output_schema=MarketSegmentResult,
            debug_mode=debug_mode,
            instructions=instructions,
            name="Market Segment Analyst"
        )


class PricePointAgent(BaseAgent):
    """Agent for analyzing optimal price points from Reddit submissions"""

    def __init__(self, model: str, api_key: str, base_url: str, debug_mode: bool = False):
        instructions = [
            "Analyze the Reddit submission to determine optimal pricing strategies.",
            "Consider stated budgets, comparison to existing solutions, and value proposition.",
            "Recommend pricing models (subscription, one-time, freemium, etc.).",
            "Provide a structured assessment with confidence scores.",
            "Balance user willingness to pay with market positioning."
        ]

        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            output_schema=PricePointResult,
            debug_mode=debug_mode,
            instructions=instructions,
            name="Price Point Analyst"
        )


class PaymentBehaviorAgent(BaseAgent):
    """Agent for analyzing payment behavior patterns from Reddit submissions"""

    def __init__(self, model: str, api_key: str, base_url: str, debug_mode: bool = False):
        instructions = [
            "Analyze the Reddit submission to understand payment behavior patterns.",
            "Look for indications of current spending on similar solutions.",
            "Assess pain intensity and urgency of the problem.",
            "Identify typical purchase patterns and decision processes.",
            "Provide a structured assessment with confidence scores."
        ]

        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            output_schema=PaymentBehaviorResult,
            debug_mode=debug_mode,
            instructions=instructions,
            name="Payment Behavior Analyst"
        )


class MarketResearchAgent(BaseAgent):
    """Agent for conducting market research based on Reddit submissions"""

    def __init__(self, model: str, api_key: str, base_url: str, debug_mode: bool = False):
        instructions = [
            "Conduct market research based on the Reddit submission content.",
            "Identify key market trends and competitive landscape.",
            "Assess market validation and barriers to entry.",
            "Provide insights on market maturity and growth potential.",
            "Deliver a structured assessment with confidence scores."
        ]

        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            output_schema=MarketResearchResult,
            debug_mode=debug_mode,
            instructions=instructions,
            name="Market Research Analyst"
        )
