"""
Specialized agents for Agno multi-agent analysis with real LLM integration
"""

from typing import Dict, Any, Optional, List, Type, Union
import json
import logging
from pydantic import BaseModel, Field
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from monitoring.metrics_collector import get_collector
from config import get_settings

logger = logging.getLogger(__name__)

# Get configuration
settings = get_settings()


# Pydantic models for structured outputs
class WillingnessToPayResult(BaseModel):
    """Structured output for willingness to pay analysis"""
    wtp_score: float = Field(..., ge=0, le=100, description="Willingness to pay score (0-100)")
    market_demand_score: float = Field(..., ge=0, le=100, description="Market demand score (0-100)")
    sentiment: str = Field(..., description="Overall payment sentiment")
    evidence: List[str] = Field(..., description="Evidence supporting the WTP assessment")
    reasoning: Optional[str] = Field(None, description="Reasoning behind the assessment")


class MarketSegmentResult(BaseModel):
    """Structured output for market segment analysis"""
    segment_type: str = Field(..., description="Market segment type (B2B, B2C, etc.)")
    market_demand_score: float = Field(..., ge=0, le=100, description="Market demand score (0-100)")
    customer_profile: str = Field(..., description="Customer profile description")
    target_audience: str = Field(..., description="Target audience description")
    indicators: List[str] = Field(..., description="Indicators supporting segment classification")
    reasoning: Optional[str] = Field(None, description="Reasoning behind the assessment")


class PricePointResult(BaseModel):
    """Structured output for price point analysis"""
    price_point: float = Field(..., ge=0, description="Estimated price point in USD")
    monetization_score: float = Field(..., ge=0, le=100, description="Monetization potential score (0-100)")
    budget_ceiling: Optional[float] = Field(None, ge=0, description="Customer budget ceiling")
    pricing_model: str = Field(..., description="Recommended pricing model")
    reasoning: Optional[str] = Field(None, description="Reasoning behind the assessment")


class PaymentBehaviorResult(BaseModel):
    """Structured output for payment behavior analysis"""
    behavior_score: float = Field(..., ge=0, le=100, description="Payment behavior score (0-100)")
    pain_intensity_score: float = Field(..., ge=0, le=100, description="Pain intensity score (0-100)")
    purchase_pattern: str = Field(..., description="Typical purchase pattern")
    current_spending: str = Field(..., description="Current spending level")
    reasoning: Optional[str] = Field(None, description="Reasoning behind the assessment")


class BaseAgent(Agent):
    """Base agent class with common functionality"""

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str,
        output_schema: Optional[Type[BaseModel]] = None,
        debug_mode: bool = False
    ):
        """
        Initialize base agent with OpenRouter configuration

        Args:
            model: Model name for the agent
            api_key: OpenRouter API key
            base_url: API base URL
            output_schema: Pydantic schema for structured output
            debug_mode: Enable debug logging
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

        # Initialize metrics collector
        self.metrics = get_collector()
        self.debug_mode = debug_mode

        # Initialize Agent with model and structured output
        super().__init__(
            model=self.openai_model,
            output_schema=output_schema,
            debug_mode=debug_mode,
            # Enable error handling
            retries=2,
            delay_between_retries=1,
            exponential_backoff=True
        )

    def run(self, input_data: Union[str, Dict[str, Any]]) -> str:
        """
        Run the agent analysis with proper error handling

        Args:
            input_data: Input data for analysis

        Returns:
            JSON string with analysis results
        """
        # Extract opportunity_id from input if possible
        try:
            input_dict = json.loads(input_data) if isinstance(input_data, str) else input_data
            opportunity_id = input_dict.get('opportunity_id', 'unknown')
        except:
            opportunity_id = 'unknown'

        # Get agent short name for metrics
        agent_name = self._get_agent_name()

        if self.debug_mode:
            logger.debug(f"Running {self.__class__.__name__} for opportunity {opportunity_id}")

        # Track execution with metrics
        with self.metrics.track("transform", agent_name=agent_name, opportunity_id=opportunity_id) as context:
            try:
                # Format input for the agent
                prompt = self._format_input(input_dict)

                # Run agent with structured output using the parent Agent.run method
                if hasattr(self, 'output_schema') and self.output_schema:
                    # Use the Agent's run method directly (not self.run to avoid recursion)
                    result = Agent.run(self, prompt, expected_output=self.output_schema.__doc__)
                    # Convert to dict for JSON serialization
                    if hasattr(result, 'model_dump'):
                        result_dict = result.model_dump()
                    else:
                        result_dict = result.dict() if hasattr(result, 'dict') else result
                else:
                    # Fallback to regular execution
                    response = Agent.run(self, prompt)
                    try:
                        result_dict = json.loads(response) if isinstance(response, str) else response
                    except json.JSONDecodeError:
                        result_dict = {"raw_response": str(response)}

                # Add metadata to context
                context["metadata"] = {
                    "agent_name": self.name,
                    "model": self.model,
                    "input_length": len(str(input_data)),
                    "has_structured_output": hasattr(self, 'output_schema') and self.output_schema is not None
                }

                if self.debug_mode:
                    logger.debug(f"Agent {agent_name} completed successfully")

                return json.dumps(result_dict, default=str)

            except Exception as e:
                logger.error(f"Error in {self.__class__.__name__}: {str(e)}")
                # Return error response
                error_response = {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "agent_name": self.name,
                    "opportunity_id": opportunity_id
                }

                # Update context with error
                context["metadata"] = {
                    "agent_name": self.name,
                    "model": self.model,
                    "opportunity_id": opportunity_id,
                    "has_error": True,
                    "error_message": str(e)
                }

                return json.dumps(error_response, default=str)

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

    def _format_input(self, input_data: Dict[str, Any]) -> str:
        """Format input data into a prompt for the agent"""
        # This should be overridden by subclasses
        return str(input_data)


class WillingnessToPayAgent(BaseAgent):
    """Analyzes willingness to pay indicators using real LLM"""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        debug_mode: bool = False
    ):
        """
        Initialize Willingness to Pay Agent

        Args:
            model: Model name (uses AGNO_MODEL from settings if None)
            api_key: API key (uses OPENROUTER_API_KEY from settings if None)
            base_url: Base URL (uses AGNO_BASE_URL from settings if None)
            debug_mode: Enable debug logging
        """
        # Use settings defaults if not provided
        self.model = model or settings.agno_model
        self.api_key = api_key or settings.openai_api_key
        self.base_url = base_url or settings.agno_base_url

        super().__init__(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            output_schema=WillingnessToPayResult,
            debug_mode=debug_mode
        )

        self.name = "Willingness to Pay Analyst"
        self.instructions = self._get_instructions()
        self.system_message = self._get_system_message()

    def _get_instructions(self) -> str:
        """Get agent instructions"""
        return """
        Analyze the provided opportunity for willingness to pay indicators. Look for:
        1. Explicit mentions of budget or pricing
        2. Pain points that suggest urgency
        3. Discussion of alternatives or existing solutions
        4. Indicators of decision-making authority

        Provide a structured analysis with scores from 0-100 and supporting evidence.
        """

    def _get_system_message(self) -> str:
        """Get system message for the agent"""
        return """
        You are a market research analyst specializing in assessing willingness to pay for products and services.
        Your analysis helps determine if users are likely to pay for a solution to their problem.
        Be thorough, evidence-based, and provide clear reasoning for your assessments.
        """

    def _format_input(self, input_data: Dict[str, Any]) -> str:
        """Format input data into a prompt for WTP analysis"""
        prompt = f"""
        Analyze this opportunity for willingness to pay indicators:

        Title: {input_data.get('title', '')}
        Content: {input_data.get('content', '')}
        Subreddit: {input_data.get('subreddit', '')}

        Focus on:
        1. Any mentions of budget, cost, or pricing
        2. Level of frustration with current solutions
        3. urgency indicators
        4. Commercial vs personal use context
        5. Decision-making authority indicators

        Provide specific evidence from the text to support your analysis.
        """
        return prompt


class MarketSegmentAgent(BaseAgent):
    """Analyzes market segment characteristics using real LLM"""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        debug_mode: bool = False
    ):
        """
        Initialize Market Segment Agent

        Args:
            model: Model name (uses AGNO_MODEL from settings if None)
            api_key: API key (uses OPENROUTER_API_KEY from settings if None)
            base_url: Base URL (uses AGNO_BASE_URL from settings if None)
            debug_mode: Enable debug logging
        """
        self.model = model or settings.agno_model
        self.api_key = api_key or settings.openai_api_key
        self.base_url = base_url or settings.agno_base_url

        super().__init__(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            output_schema=MarketSegmentResult,
            debug_mode=debug_mode
        )

        self.name = "Market Segment Analyst"
        self.instructions = self._get_instructions()
        self.system_message = self._get_system_message()

    def _get_instructions(self) -> str:
        """Get agent instructions"""
        return """
        Analyze the provided opportunity to identify the target market segment.
        Classify whether this is B2B or B2C, identify the customer profile,
        and determine the target audience characteristics.
        """

    def _get_system_message(self) -> str:
        """Get system message for the agent"""
        return """
        You are a market segmentation expert who identifies and classifies target markets.
        Your analysis helps understand who the potential customers are and how to reach them.
        Consider both explicit and implicit clues about the target audience.
        """

    def _format_input(self, input_data: Dict[str, Any]) -> str:
        """Format input data into a prompt for segment analysis"""
        prompt = f"""
        Analyze this opportunity to identify the market segment:

        Title: {input_data.get('title', '')}
        Content: {input_data.get('content', '')}
        Subreddit: {input_data.get('subreddit', '')}

        Determine:
        1. Is this B2B (business) or B2C (consumer)?
        2. What is the primary customer profile?
        3. Who is the target audience?
        4. What indicators support this classification?

        Consider the context, language, and specific needs mentioned.
        """
        return prompt


class PricePointAgent(BaseAgent):
    """Analyzes price point sensitivity using real LLM"""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        debug_mode: bool = False
    ):
        """
        Initialize Price Point Agent

        Args:
            model: Model name (uses AGNO_MODEL from settings if None)
            api_key: API key (uses OPENROUTER_API_KEY from settings if None)
            base_url: Base URL (uses AGNO_BASE_URL from settings if None)
            debug_mode: Enable debug logging
        """
        self.model = model or settings.agno_model
        self.api_key = api_key or settings.openai_api_key
        self.base_url = base_url or settings.agno_base_url

        super().__init__(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            output_schema=PricePointResult,
            debug_mode=debug_mode
        )

        self.name = "Price Point Analyst"
        self.instructions = self._get_instructions()
        self.system_message = self._get_system_message()

    def _get_instructions(self) -> str:
        """Get agent instructions"""
        return """
        Analyze the provided opportunity to determine appropriate pricing strategies.
        Estimate price points, identify budget constraints, and recommend pricing models.
        """

    def _get_system_message(self) -> str:
        """Get system message for the agent"""
        return """
        You are a pricing strategy expert who determines optimal price points for products and services.
        Your analysis considers the value proposition, customer budget constraints, and market positioning.
        Provide realistic pricing recommendations with clear justification.
        """

    def _format_input(self, input_data: Dict[str, Any]) -> str:
        """Format input data into a prompt for price analysis"""
        prompt = f"""
        Analyze this opportunity for pricing strategy:

        Title: {input_data.get('title', '')}
        Content: {input_data.get('content', '')}
        Subreddit: {input_data.get('subreddit', '')}

        Determine:
        1. What price point would be appropriate? (in USD)
        2. What is the customer's likely budget ceiling?
        3. What pricing model would work best? (subscription, one-time, freemium, etc.)
        4. How strong is the monetization potential?

        Look for explicit mentions of budget and implicit value indicators.
        """
        return prompt


class PaymentBehaviorAgent(BaseAgent):
    """Analyzes payment behavior patterns using real LLM"""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        debug_mode: bool = False
    ):
        """
        Initialize Payment Behavior Agent

        Args:
            model: Model name (uses AGNO_MODEL from settings if None)
            api_key: API key (uses OPENROUTER_API_KEY from settings if None)
            base_url: Base URL (uses AGNO_BASE_URL from settings if None)
            debug_mode: Enable debug logging
        """
        self.model = model or settings.agno_model
        self.api_key = api_key or settings.openai_api_key
        self.base_url = base_url or settings.agno_base_url

        super().__init__(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            output_schema=PaymentBehaviorResult,
            debug_mode=debug_mode
        )

        self.name = "Payment Behavior Analyst"
        self.instructions = self._get_instructions()
        self.system_message = self._get_system_message()

    def _get_instructions(self) -> str:
        """Get agent instructions"""
        return """
        Analyze the provided opportunity to understand payment behavior patterns.
        Assess pain intensity, spending habits, and likely purchase patterns.
        """

    def _get_system_message(self) -> str:
        """Get system message for the agent"""
        return """
        You are a consumer behavior expert specializing in payment and purchasing patterns.
        Your analysis helps predict how customers will behave when considering a purchase.
        Consider psychological factors, practical constraints, and past behaviors.
        """

    def _format_input(self, input_data: Dict[str, Any]) -> str:
        """Format input data into a prompt for behavior analysis"""
        prompt = f"""
        Analyze this opportunity for payment behavior patterns:

        Title: {input_data.get('title', '')}
        Content: {input_data.get('content', '')}
        Subreddit: {input_data.get('subreddit', '')}

        Assess:
        1. How intense is the pain point driving this need?
        2. What is the likely spending level on solutions?
        3. What purchase pattern would they follow? (impulse, research, subscription, etc.)
        4. How likely are they to actually pay for a solution?

        Look for evidence of past spending, decision-making patterns, and urgency.
        """
        return prompt


class MarketResearchAgent(BaseAgent):
    """Performs market research using external APIs for validation"""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        debug_mode: bool = False,
        validation_threshold: float = 70.0,
        max_competitors: int = 5,
        max_launches: int = 3,
        enable_cost_tracking: bool = True
    ):
        """
        Initialize Market Research Agent

        Args:
            model: Model name (uses AGNO_MODEL from settings if None)
            api_key: API key (uses OPENROUTER_API_KEY from settings if None)
            base_url: Base URL (uses AGNO_BASE_URL from settings if None)
            debug_mode: Enable debug logging
            validation_threshold: Threshold for validation
            max_competitors: Maximum competitors to research
            max_launches: Maximum launches to research
            enable_cost_tracking: Enable cost tracking
        """
        self.model = model or settings.agno_model
        self.api_key = api_key or settings.openai_api_key
        self.base_url = base_url or settings.agno_base_url
        self.validation_threshold = validation_threshold
        self.max_competitors = max_competitors
        self.max_launches = max_launches
        self.enable_cost_tracking = enable_cost_tracking

        super().__init__(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            debug_mode=debug_mode
        )

        self.name = "Market Research Analyst"
        self.instructions = self._get_instructions()
        self.system_message = self._get_system_message()

    def _get_instructions(self) -> str:
        """Get agent instructions"""
        return """
        Perform comprehensive market research for the opportunity.
        Validate market size, research competitors, and find similar product launches.
        """

    def _get_system_message(self) -> str:
        """Get system message for the agent"""
        return """
        You are a market research analyst using external data sources to validate opportunities.
        Your research provides real-world evidence about market viability and competitive landscape.
        Focus on finding concrete data points that support or challenge the opportunity.
        """

    def _format_input(self, input_data: Dict[str, Any]) -> str:
        """Format input data into a prompt for market research"""
        app_concept = input_data.get('app_concept', '')
        target_market = input_data.get('target_market', '')
        problem_description = input_data.get('problem_description', '')

        prompt = f"""
        Conduct market research for this opportunity:

        App Concept: {app_concept}
        Target Market: {target_market}
        Problem Description: {problem_description}

        Research:
        1. Market size and growth potential
        2. Competitor analysis and pricing
        3. Similar product launches and their performance
        4. Overall validation score (0-100)

        Provide a comprehensive validation of the market opportunity.
        """
        return prompt

    def run(self, input_data: Union[str, Dict[str, Any]]) -> str:
        """
        Override run method to handle mock implementation

        Args:
            input_data: Input data for market research

        Returns:
            JSON string with market research results
        """
        # Extract opportunity_id for tracking
        try:
            input_dict = json.loads(input_data) if isinstance(input_data, str) else input_data
            opportunity_id = input_dict.get('opportunity_id', 'unknown')
        except:
            opportunity_id = 'unknown'

        # Get agent short name for metrics
        agent_name = self._get_agent_name()

        # Track execution with metrics
        with self.metrics.track("transform", agent_name=agent_name, opportunity_id=opportunity_id) as context:
            if self.debug_mode:
                logger.debug(f"Running {self.__class__.__name__} for opportunity {opportunity_id}")

            # For now, return mock results similar to the original implementation
            # This can be enhanced later with real Jina API integration
            result = {
                "validation_score": 75,
                "competitor_pricing": [
                    {
                        "company": "CompetitorPro",
                        "pricing_model": "subscription",
                        "tiers": [{"name": "Basic", "price": "$9/mo"}],
                        "confidence": 85.0
                    }
                ],
                "market_size": {
                    "tam": "$45B",
                    "growth": "18% CAGR"
                },
                "similar_launches": [
                    {
                        "product": "SimilarApp",
                        "upvotes": 1250,
                        "platform": "Product Hunt"
                    }
                ]
            }

            # Add metadata to context
            context["metadata"] = {
                "agent_name": self.name,
                "model": self.model,
                "opportunity_id": opportunity_id,
                "is_mock": True
            }

            return json.dumps(result, default=str)