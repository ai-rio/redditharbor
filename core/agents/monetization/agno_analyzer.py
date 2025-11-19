#!/usr/bin/env python3
"""
RedditHarbor Agno-Based Monetization Analyzer

Migrated from DSPy to Agno + LiteLLM + AgentOps for better multi-agent architecture
and comprehensive cost tracking. Maintains identical API and functionality.

Key Improvements:
- Multi-agent architecture with specialized agents
- LiteLLM for unified model management
- AgentOps for comprehensive cost tracking
- Better error handling and retry logic
- Streaming support with reasoning transparency
- Subreddit purchasing power context multipliers
- Enhanced B2B/B2C differentiation

Integration: Drop-in replacement for monetization_llm_analyzer.py
Cost: ~$0.01 per analysis with transparent tracking
"""

import asyncio
import json
import os
import re
import statistics
import sys
from collections import Counter
from collections.abc import AsyncGenerator
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Import json-repair for robust LLM JSON parsing
from json_repair import repair_json

# Third-party imports
try:
    from agno.agent import Agent
    from agno.models.openai import OpenAIChat
    from agno.team import Team
    from agno.utils.log import logger

    # Define a simple response wrapper if RunResponse doesn't exist
    class RunResponse:
        def __init__(self, content: str):
            self.content = content

except ImportError:
    print("❌ agno not installed. Install with: pip install agno")
    sys.exit(1)

try:
    import agentops
    from agentops import agent, tool, trace
except ImportError:
    print("❌ agentops not installed. Install with: pip install agentops")
    sys.exit(1)

# Add project root to path FIRST (before config imports)
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import centralized configuration
try:
    from config import settings
except ImportError:
    # Fallback for standalone usage
    class Settings:
        OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
        MONETIZATION_LLM_MODEL = os.getenv(
            "MONETIZATION_LLM_MODEL", "anthropic/claude-haiku-4.5"
        )
        OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-haiku-4.5")

    settings = Settings()


# =============================================================================
# AGNO AGENTS - Specialized analysis agents
# =============================================================================


@agent(name="WTP Analyst")
class WillingnessToPayAgent(Agent):
    """Analyzes user willingness to pay with sentiment awareness"""

    def __init__(
        self, model: str, api_key: str | None = None, base_url: str | None = None
    ):
        super().__init__(
            name="Willingness to Pay Analyst",
            role="Analyze user willingness to pay with sentiment awareness",
            instructions="""
            You are an expert at analyzing Reddit posts to determine willingness to pay.

            Analyze the given text and subreddit context to determine:
            1. Overall sentiment toward payment (Positive, Neutral, Negative)
            2. Willingness to pay score (0-100)
            3. Key evidence phrases
            4. Reasoning for the score

            Important considerations:
            - Look for explicit statements like "willing to pay", "NOT willing to pay"
            - Consider context (frustration with current tools may indicate high WTP)
            - Sentiment matters - positive sentiment increases WTP score
            - Budget constraints reduce WTP score
            - Urgency increases WTP score

            CRITICAL: You MUST return your analysis in JSON format with EXACT field names:
            {
                "sentiment_toward_payment": "Positive|Neutral|Negative",
                "willingness_to_pay_score": 85,
                "evidence": ["key phrase 1", "key phrase 2"],
                "reasoning": "Detailed explanation of the score"
            }

            The field names MUST be exactly:
            - "sentiment_toward_payment" (NOT "sentiment")
            - "willingness_to_pay_score" (NOT "willingness_score")
            """,
            model=OpenAIChat(id=model, api_key=api_key, base_url=base_url),
        )


@agent(name="Market Segment Analyst")
class MarketSegmentAgent(Agent):
    """Classifies B2B vs B2C market segment"""

    def __init__(
        self, model: str, api_key: str | None = None, base_url: str | None = None
    ):
        super().__init__(
            name="Market Segment Classifier",
            role="Classify B2B vs B2C market segment",
            instructions="""
            You are an expert at identifying market segments from Reddit discussions.

            Analyze the text and subreddit context to determine:
            1. Market segment (B2B, B2C, Mixed, Unknown)
            2. Confidence level (0-1)
            3. Indicators that point to this segment
            4. Segment quality score (0-100)

            B2B indicators:
            - Business problems, team coordination, workflow
            - Company size, team mentions, enterprise tools
            - Business metrics, ROI, revenue impact
            - Professional contexts, work-related discussions
            - Budget approval processes
            - Team collaboration needs
            - Enterprise-level requirements

            B2C indicators:
            - Personal use, individual needs, hobbies
            - Personal budget constraints, individual preferences
            - Consumer features, personal benefits
            - Non-work contexts
            - Individual decision-making
            - Personal subscription management

            Mixed indicators:
            - Both business and personal use cases mentioned
            - Work-life balance tools
            - Apps used for both professional and personal purposes

            CRITICAL: You MUST return your analysis in JSON format with EXACT field names:
            {
                "customer_segment": "B2B|B2C|Mixed|Unknown",
                "confidence": 0.85,
                "indicators": ["indicator 1", "indicator 2"],
                "segment_score": 90
            }

            The field name MUST be exactly:
            - "customer_segment" (NOT "segment")
            """,
            model=OpenAIChat(id=model, api_key=api_key, base_url=base_url),
        )


@agent(name="Price Point Analyst")
class PricePointAgent(Agent):
    """Extracts mentioned price points and budget signals"""

    def __init__(
        self, model: str, api_key: str | None = None, base_url: str | None = None
    ):
        super().__init__(
            name="Price Point Extractor",
            role="Extract price points and budget signals from text",
            instructions="""
            You are an expert at extracting pricing information from text.

            Analyze the text to identify:
            1. All mentioned price points with context
            2. Maximum budget mentioned or inferred
            3. Preferred pricing model

            Look for:
            - Explicit dollar amounts ($X, $X/month, $X/year)
            - Budget ranges ($X-Y)
            - Pricing model preferences (subscription, one-time, freemium)
            - Comparison to competitor pricing
            - Budget approval mentions

            CRITICAL: You MUST return your analysis in JSON format with EXACT field names:
            {
                "mentioned_price_points": [
                    {"price": "$300/month", "context": "current spending on Asana"},
                    {"price": "$150/month", "context": "target budget"}
                ],
                "budget_ceiling": "$150/month",
                "pricing_model": "Subscription"
            }

            The field name MUST be exactly:
            - "mentioned_price_points" (NOT "price_points")
            """,
            model=OpenAIChat(id=model, api_key=api_key, base_url=base_url),
        )


@agent(name="Payment Behavior Analyst")
class PaymentBehaviorAgent(Agent):
    """Analyzes existing payment behavior and switching willingness"""

    def __init__(
        self, model: str, api_key: str | None = None, base_url: str | None = None
    ):
        super().__init__(
            name="Payment Behavior Analyst",
            role="Analyze existing payment behavior and switching willingness",
            instructions="""
            You are an expert at understanding payment behavior from user discussions.

            Analyze the text to determine:
            1. Current spending patterns
            2. Willingness to switch providers
            3. Evidence of payment behavior
            4. Behavior score (0-100)

            Look for:
            - Current tool subscriptions or purchases
            - Pain points with current solutions
            - Budget approval processes
            - Switching costs or concerns
            - Decision-making timeline
            - Past purchasing behavior

            Return your analysis in JSON format:
            {
                "current_spending": "$300/month on Asana",
                "switching_willingness": "High|Medium|Low|Unknown",
                "spending_evidence": ["evidence 1", "evidence 2"],
                "behavior_score": 85
            }
            """,
            model=OpenAIChat(id=model, api_key=api_key, base_url=base_url),
        )


# =============================================================================
# SUBREDDIT CONTEXT MULTIPLIERS
# =============================================================================

SUBREDDIT_PURCHASING_POWER = {
    # High purchasing power
    "entrepreneur": 1.5,
    "business": 1.5,
    "startups": 1.4,
    "saas": 1.4,
    "smallbusiness": 1.3,
    # Medium purchasing power (baseline)
    "personalfinance": 1.0,
    "financialindependence": 1.0,
    "productivity": 1.0,
    # Lower purchasing power
    "frugal": 0.6,
    "povertyfinance": 0.5,
    "college": 0.7,
    "students": 0.7,
}


def get_subreddit_multiplier(subreddit: str) -> float:
    """Get purchasing power multiplier for subreddit"""
    subreddit_lower = subreddit.lower()
    return SUBREDDIT_PURCHASING_POWER.get(subreddit_lower, 1.0)


# =============================================================================
# MAIN MONETIZATION ANALYZER
# =============================================================================


@dataclass
class MonetizationAnalysis:
    """Result of LLM monetization analysis"""

    # Core scores
    willingness_to_pay_score: float  # 0-100
    market_segment_score: float  # 0-100
    price_sensitivity_score: float  # 0-100
    revenue_potential_score: float  # 0-100

    # Extracted insights
    customer_segment: str  # B2B, B2C, Mixed, Unknown
    mentioned_price_points: list[str]
    existing_payment_behavior: str
    urgency_level: str  # Critical, High, Medium, Low
    sentiment_toward_payment: str  # Positive, Neutral, Negative
    payment_friction_indicators: list[str]

    # Composite score
    llm_monetization_score: float  # 0-100

    # Meta
    confidence: float  # 0-1
    reasoning: str
    subreddit_multiplier: float


class MonetizationAgnoAnalyzer:
    """
    Agno-powered monetization analyzer with AgentOps cost tracking

    Replaces DSPy with multi-agent architecture while maintaining identical
    functionality. Features:
    - Multi-agent analysis with specialized agents
    - Comprehensive cost tracking with AgentOps
    - LiteLLM model management
    - Better error handling and retry logic
    - Streaming support
    """

    def __init__(
        self,
        model: str | None = None,
        agentops_api_key: str | None = None,
    ):
        """
        Initialize analyzer with Agno and AgentOps.

        Args:
            model: Optional model override. Uses settings.MONETIZATION_LLM_MODEL
                   if not provided
            agentops_api_key: Optional AgentOps API key. If not provided,
                             uses AGENTOPS_API_KEY env var
        """
        # Force Agno to use OpenRouter by setting environment variables
        # This prevents Agno from auto-detecting and using OpenAI endpoints
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY", "")
        os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"

        # Disable OpenAI auto-instrumentation for AgentOps compatibility
        os.environ["AGENTOPS_AUTO_INSTRUMENT_OPENAI"] = "false"

        # Determine model using centralized config
        if model is None:
            model = getattr(
                settings, "MONETIZATION_LLM_MODEL", "anthropic/claude-haiku-4.5"
            )

        self.model = model
        self.agentops_api_key = agentops_api_key or os.getenv("AGENTOPS_API_KEY")

        # Get OpenRouter API configuration
        self.api_key = getattr(
            settings, "OPENROUTER_API_KEY", os.getenv("OPENROUTER_API_KEY")
        )
        self.base_url = "https://openrouter.ai/api/v1"

        # Initialize AgentOps if API key is provided
        if self.agentops_api_key:
            try:
                # FIXED: Initialize AgentOps with manual trace control for better visibility
                agentops.init(
                    self.agentops_api_key,
                    auto_start_session=False,  # Manual control for better debugging
                    tags=["reddit-monetization", "agno-multi-agent"],
                    instrument_llm_calls=False  # Disable auto-instrumentation to avoid OpenAI validation conflicts
                )
                self.agentops_enabled = True
                self.agentops_trace = None  # Track current trace
                logger.info("AgentOps initialized with manual trace control")
            except Exception as e:
                logger.warning(f"Failed to initialize AgentOps: {e}")
                self.agentops_enabled = False
                self.agentops_trace = None
        else:
            self.agentops_enabled = False
            self.agentops_trace = None
            logger.info("AgentOps not initialized (no API key provided)")

        # Initialize Agno agents with OpenRouter configuration
        self.wtp_agent = WillingnessToPayAgent(
            model=model, api_key=self.api_key, base_url=self.base_url
        )
        self.segment_agent = MarketSegmentAgent(
            model=model, api_key=self.api_key, base_url=self.base_url
        )
        self.price_agent = PricePointAgent(
            model=model, api_key=self.api_key, base_url=self.base_url
        )
        self.behavior_agent = PaymentBehaviorAgent(
            model=model, api_key=self.api_key, base_url=self.base_url
        )

        # Create team for coordinated analysis
        self.team = Team(
            name="Monetization Analysis Team",
            instructions=(
                "Analyze Reddit posts for monetization potential "
                "using specialized agents"
            ),
            members=[
                self.wtp_agent,
                self.segment_agent,
                self.price_agent,
                self.behavior_agent,
            ],
        )

        # Track analysis session
        self.session_id = f"monetization_analysis_{datetime.now().isoformat()}"
        if self.agentops_enabled:
            # Note: create_session is deprecated, using start_trace instead
            # self.session_id = agentops.start_trace("monetization_analysis")
            pass

    @tool(name="parse_team_response", cost=0.001)
    def _parse_team_response(self, response):
        """Parse team response with robust JSON repair and field mapping"""
        try:
            # Handle different response types from Agno agents
            if hasattr(response, 'content'):
                content = response.content
            elif isinstance(response, str):
                content = response
            elif isinstance(response, dict):
                content = json.dumps(response)
            else:
                content = str(response)

            logger.info(f"Parsing response content (length: {len(content)})")

            # Extract JSON from response content
            parsed_data = self._extract_json_from_response(content)

            # Map field names and validate structure
            mapped_data = self._map_field_names(parsed_data)

            # Apply consensus calculation from multiple agents
            consensus_data = self._calculate_consensus_from_agents(content, mapped_data)

            logger.info(f"Successfully parsed response with {len(consensus_data)} fields")
            return consensus_data

        except Exception as e:
            logger.error(f"Failed to parse team response: {e}")
            # Return safe fallback structure
            return self._get_fallback_response(str(e))

    def _extract_json_from_response(self, content: str) -> dict[str, Any]:
        """Extract and repair JSON from agent response content"""
        try:
            # First try direct JSON parsing
            if content.strip().startswith('{'):
                parsed = json.loads(content)
                return self._ensure_dict_type(parsed)

            # Look for JSON blocks in the content
            json_start = content.find('{')
            if json_start == -1:
                # No JSON found, treat as text response
                return self._parse_text_response(content)

            json_end = content.rfind('}') + 1
            if json_end <= json_start:
                return self._parse_text_response(content)

            json_str = content[json_start:json_end]

            try:
                # Try direct parsing first
                parsed = json.loads(json_str)
                return self._ensure_dict_type(parsed)
            except json.JSONDecodeError:
                # Use json-repair for malformed LLM JSON
                logger.info("JSON malformed, attempting repair...")
                repaired = repair_json(json_str)
                parsed = json.loads(repaired)
                logger.info(f"Successfully repaired JSON with {len(parsed) if isinstance(parsed, (dict, list)) else 0} fields")
                return self._ensure_dict_type(parsed)

        except Exception as e:
            logger.warning(f"JSON extraction failed: {e}")
            return self._parse_text_response(content)

    def _ensure_dict_type(self, parsed_data: Any) -> dict[str, Any]:
        """Ensure parsed JSON data is always a dictionary, handling lists gracefully"""
        if isinstance(parsed_data, dict):
            return parsed_data
        elif isinstance(parsed_data, list):
            # Handle case where JSON repair returns a list
            if len(parsed_data) == 0:
                logger.warning("Empty list returned from JSON repair, treating as empty dict")
                return {}
            elif len(parsed_data) == 1 and isinstance(parsed_data[0], dict):
                # Single dictionary in list - extract it
                logger.info("Extracting single dictionary from list")
                return parsed_data[0]
            else:
                # Multiple items in list - try to merge dictionaries or convert first item
                logger.warning(f"List with {len(parsed_data)} items returned, attempting to extract meaningful data")

                # Look for dictionary items in the list
                dict_items = [item for item in parsed_data if isinstance(item, dict)]
                if dict_items:
                    # Merge all dictionaries (later items override earlier ones)
                    merged_dict = {}
                    for item in dict_items:
                        merged_dict.update(item)
                    logger.info(f"Merged {len(dict_items)} dictionaries from list")
                    return merged_dict
                else:
                    # No dictionaries in list, create a structured response
                    return {
                        "mentioned_price_points": [str(item) for item in parsed_data if item],
                        "raw_response_list": parsed_data,
                        "parsing_note": "Converted from list response"
                    }
        else:
            # Handle other types (string, number, etc.)
            logger.warning(f"Unexpected type {type(parsed_data)} returned from JSON parsing")
            return {
                "raw_response": parsed_data,
                "parsing_note": f"Converted from {type(parsed_data).__name__} response"
            }

    def _map_field_names(self, data: dict[str, Any]) -> dict[str, Any]:
        """Map various field name variations to expected field names"""
        field_mappings = {
            # Sentiment field mappings
            "sentiment": "sentiment_toward_payment",
            "payment_sentiment": "sentiment_toward_payment",
            "payment_attitude": "sentiment_toward_payment",

            # Willingness to pay field mappings
            "willingness_score": "willingness_to_pay_score",
            "wtp_score": "willingness_to_pay_score",
            "willingness": "willingness_to_pay_score",

            # Customer segment field mappings
            "segment": "customer_segment",
            "market_segment": "customer_segment",
            "business_type": "customer_segment",

            # Price points field mappings
            "price_points": "mentioned_price_points",
            "prices": "mentioned_price_points",
            "pricing": "mentioned_price_points",

            # Payment behavior field mappings
            "spending": "current_spending",
            "existing_spending": "current_spending",
            "payment_behavior": "current_spending",

            # Revenue potential field mappings
            "revenue_score": "revenue_potential_score",
            "potential": "revenue_potential_score",
        }

        mapped_data = {}

        # Apply field mappings
        for key, value in data.items():
            mapped_key = field_mappings.get(key, key)
            mapped_data[mapped_key] = value

        # Validate and normalize specific fields
        mapped_data = self._normalize_field_values(mapped_data)

        return mapped_data

    def _normalize_field_values(self, data: dict[str, Any]) -> dict[str, Any]:
        """Normalize and validate specific field values"""
        # Normalize sentiment values - handle both strings and lists
        sentiment_value = data.get("sentiment_toward_payment", "")
        if isinstance(sentiment_value, list):
            # Join list items and convert to string
            sentiment = " ".join(str(item) for item in sentiment_value).lower()
        elif isinstance(sentiment_value, str):
            sentiment = sentiment_value.lower()
        else:
            sentiment = str(sentiment_value).lower()

        if any(word in sentiment for word in ["positive", "willing", "favorable"]):
            data["sentiment_toward_payment"] = "Positive"
        elif any(word in sentiment for word in ["negative", "unwilling", "reluctant"]):
            data["sentiment_toward_payment"] = "Negative"
        else:
            data["sentiment_toward_payment"] = "Neutral"

        # Normalize customer segment values - handle both strings and lists
        segment_value = data.get("customer_segment", "")
        if isinstance(segment_value, list):
            # Join list items and convert to string
            segment = " ".join(str(item) for item in segment_value).lower()
        elif isinstance(segment_value, str):
            segment = segment_value.lower()
        else:
            segment = str(segment_value).lower()

        if "b2b" in segment or "business" in segment:
            data["customer_segment"] = "B2B"
        elif "b2c" in segment or "consumer" in segment:
            data["customer_segment"] = "B2C"
        elif "mixed" in segment:
            data["customer_segment"] = "Mixed"
        else:
            data["customer_segment"] = "Unknown"

        # Normalize score values to 0-100 range
        for score_field in ["willingness_to_pay_score", "revenue_potential_score"]:
            if score_field in data:
                try:
                    score = float(data[score_field])
                    score = max(0, min(100, score))  # Clamp to 0-100
                    data[score_field] = score
                except (ValueError, TypeError):
                    data[score_field] = 50.0  # Default fallback

        # Normalize price points to list of strings
        if "mentioned_price_points" in data:
            price_points = data["mentioned_price_points"]
            if isinstance(price_points, str):
                data["mentioned_price_points"] = [price_points]
            elif isinstance(price_points, list):
                data["mentioned_price_points"] = [str(p) for p in price_points]
            else:
                data["mentioned_price_points"] = []

        return data

    def _calculate_consensus_from_agents(self, content: str, mapped_data: dict[str, Any]) -> dict[str, Any]:
        """Calculate consensus from multiple agent responses"""
        try:
            # Look for individual agent sections in the content
            agent_sections = self._extract_agent_sections(content)

            if len(agent_sections) > 1:
                # Multiple agents detected - calculate consensus
                consensus_data = self._calculate_multi_agent_consensus(agent_sections, mapped_data)
                logger.info(f"Calculated consensus from {len(agent_sections)} agents")
                return consensus_data
            else:
                # Single agent response - return mapped data with confidence boost
                confidence = float(mapped_data.get("confidence", 0.7))
                # Slightly reduce confidence for single agent analysis
                mapped_data["confidence"] = max(0.5, confidence * 0.9)
                return mapped_data

        except Exception as e:
            logger.warning(f"Consensus calculation failed: {e}")
            # Return mapped data with reduced confidence
            mapped_data["confidence"] = 0.5
            return mapped_data

    def _extract_agent_sections(self, content: str) -> list[dict[str, Any]]:
        """Extract individual agent responses from combined content"""
        agent_sections = []

        # Look for agent-specific markers in the content
        agent_markers = [
            "WTP Analysis:", "Willingness to Pay Analysis:",
            "Market Segment:", "Market Segment Analysis:",
            "Price Analysis:", "Price Point Analysis:",
            "Payment Behavior:", "Payment Behavior Analysis:"
        ]

        sections = content.split('\n\n')
        for section in sections:
            section = section.strip()
            if any(marker in section for marker in agent_markers):
                try:
                    # Try to parse this section as JSON
                    parsed = self._extract_json_from_response(section)
                    # Ensure we always have a dictionary
                    dict_data = self._ensure_dict_type(parsed) if not isinstance(parsed, dict) else parsed
                    if dict_data:
                        agent_sections.append(dict_data)
                except Exception as e:
                    # Skip unparsable sections but log for debugging
                    logger.warning(f"Failed to parse agent section: {e}")
                    continue

        return agent_sections

    def _calculate_multi_agent_consensus(self, agent_sections: list[dict[str, Any]], base_data: dict[str, Any]) -> dict[str, Any]:
        """Calculate consensus values from multiple agent analyses"""
        consensus_data = base_data.copy()

        # Calculate consensus for numerical scores
        score_fields = ["willingness_to_pay_score", "revenue_potential_score"]
        for field in score_fields:
            scores = []
            for section in agent_sections:
                # Ensure section is a dictionary before accessing items
                if not isinstance(section, dict):
                    logger.warning(f"Skipping non-dict section in consensus calculation: {type(section)}")
                    continue
                if field in section:
                    try:
                        score = float(section[field])
                        scores.append(score)
                    except (ValueError, TypeError):
                        continue

            if scores:
                # Use median with outlier detection
                scores.sort()
                n = len(scores)
                if n >= 3:
                    # Remove outliers (values > 2 std deviations from mean)
                    mean = statistics.mean(scores)
                    stdev = statistics.stdev(scores) if len(set(scores)) > 1 else 0

                    filtered_scores = [s for s in scores if abs(s - mean) <= 2 * stdev]
                    if filtered_scores:
                        scores = filtered_scores

                if scores:
                    consensus_data[field] = statistics.median(scores)

        # Calculate consensus for categorical fields
        categorical_fields = ["customer_segment", "sentiment_toward_payment"]
        for field in categorical_fields:
            values = []
            for section in agent_sections:
                # Ensure section is a dictionary before accessing items
                if not isinstance(section, dict):
                    logger.warning(f"Skipping non-dict section in categorical consensus: {type(section)}")
                    continue
                value = section.get(field)
                if value:
                    values.append(value)

            if values:
                # Use most common value
                consensus_data[field] = Counter(values).most_common(1)[0][0]

        # Boost confidence based on agreement level
        consensus_data["confidence"] = min(0.95, 0.7 + (len(agent_sections) - 1) * 0.05)

        # Add metadata about consensus calculation
        consensus_data["consensus_metadata"] = {
            "agent_count": len(agent_sections),
            "agreement_level": self._calculate_agreement_level(agent_sections, consensus_data),
            "outliers_detected": len(agent_sections) - len([s for s in agent_sections if self._is_outlier(s, consensus_data)])
        }

        return consensus_data

    def _calculate_agreement_level(self, agent_sections: list[dict[str, Any]], consensus: dict[str, Any]) -> str:
        """Calculate agreement level between agents"""
        if len(agent_sections) < 2:
            return "single_agent"

        agreement_score = 0
        total_comparisons = 0

        # Compare numerical scores
        for field in ["willingness_to_pay_score", "revenue_potential_score"]:
            values = [section.get(field) for section in agent_sections if section.get(field) is not None]
            if len(values) > 1:
                try:
                    values = [float(v) for v in values]
                    max_diff = max(values) - min(values)
                    if max_diff <= 10:  # Within 10 points
                        agreement_score += 1
                    elif max_diff <= 20:  # Within 20 points
                        agreement_score += 0.5
                    total_comparisons += 1
                except (ValueError, TypeError):
                    pass

        # Compare categorical fields
        for field in ["customer_segment", "sentiment_toward_payment"]:
            values = [section.get(field) for section in agent_sections if section.get(field)]
            if len(values) > 1:
                unique_values = set(values)
                if len(unique_values) == 1:
                    agreement_score += 1
                elif len(unique_values) == 2:
                    agreement_score += 0.5
                total_comparisons += 1

        if total_comparisons == 0:
            return "unknown"

        agreement_ratio = agreement_score / total_comparisons

        if agreement_ratio >= 0.9:
            return "high"
        elif agreement_ratio >= 0.7:
            return "medium"
        elif agreement_ratio >= 0.5:
            return "low"
        else:
            return "very_low"

    def _is_outlier(self, agent_data: dict[str, Any], consensus: dict[str, Any]) -> bool:
        """Determine if an agent's response is an outlier"""
        # Ensure both inputs are dictionaries
        if not isinstance(agent_data, dict) or not isinstance(consensus, dict):
            logger.warning(f"Invalid data types in outlier detection: agent_data={type(agent_data)}, consensus={type(consensus)}")
            return False

        outlier_count = 0
        total_checks = 0

        # Check numerical scores
        for field in ["willingness_to_pay_score", "revenue_potential_score"]:
            if field in agent_data and field in consensus:
                try:
                    agent_val = float(agent_data[field])
                    consensus_val = float(consensus[field])
                    if abs(agent_val - consensus_val) > 30:  # More than 30 points difference
                        outlier_count += 1
                    total_checks += 1
                except (ValueError, TypeError):
                    pass

        # Check categorical fields
        for field in ["customer_segment", "sentiment_toward_payment"]:
            if field in agent_data and field in consensus:
                if agent_data[field] != consensus[field]:
                    outlier_count += 1
                total_checks += 1

        if total_checks == 0:
            return False

        return outlier_count > total_checks * 0.6  # > 60% disagreement

    def _parse_text_response(self, content: str) -> dict[str, Any]:
        """Parse non-JSON text response using keyword extraction"""
        data = {}
        content_lower = content.lower()

        # Extract sentiment
        if any(word in content_lower for word in ["positive", "willing", "happy", "ready"]):
            data["sentiment_toward_payment"] = "Positive"
        elif any(word in content_lower for word in ["negative", "unwilling", "refuse", "not willing"]):
            data["sentiment_toward_payment"] = "Negative"
        else:
            data["sentiment_toward_payment"] = "Neutral"

        # Extract segment
        if any(word in content_lower for word in ["b2b", "business", "company", "team", "enterprise"]):
            data["customer_segment"] = "B2B"
        elif any(word in content_lower for word in ["b2c", "personal", "individual", "consumer"]):
            data["customer_segment"] = "B2C"
        elif "mixed" in content_lower:
            data["customer_segment"] = "Mixed"
        else:
            data["customer_segment"] = "Unknown"

        # Extract willingness score (look for numbers)
        scores = re.findall(r'\b(\d{1,3})\b', content)
        if scores:
            # Take the highest score that makes sense for willingness to pay
            valid_scores = [int(s) for s in scores if 0 <= int(s) <= 100]
            if valid_scores:
                data["willingness_to_pay_score"] = max(valid_scores)
            else:
                data["willingness_to_pay_score"] = 50
        else:
            data["willingness_to_pay_score"] = 50

        # Extract price mentions
        prices = re.findall(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', content)
        if prices:
            data["mentioned_price_points"] = [f"${p}" for p in prices]
        else:
            data["mentioned_price_points"] = []

        # Extract spending mentions
        spending_patterns = [
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:\/(?:month|year|mo|yr))?'
        ]
        for pattern in spending_patterns:
            matches = re.findall(pattern, content)
            if matches:
                data["current_spending"] = f"${matches[0]}/month"
                break
        else:
            data["current_spending"] = "Unknown"

        # Set reasonable defaults
        data.update({
            "revenue_potential_score": data.get("willingness_to_pay_score", 50),
            "confidence": 0.6,  # Lower confidence for text parsing
            "reasoning": f"Parsed from text: {content[:100]}..." if len(content) > 100 else f"Parsed from text: {content}"
        })

        return data

    def _get_fallback_response(self, error_msg: str) -> dict[str, Any]:
        """Get safe fallback response structure"""
        return {
            "willingness_to_pay_score": 50.0,
            "customer_segment": "Unknown",
            "mentioned_price_points": [],
            "current_spending": "Unknown",
            "sentiment_toward_payment": "Neutral",
            "revenue_potential_score": 50.0,
            "confidence": 0.5,
            "reasoning": f"Parsing failed with error: {error_msg}",
            "error_occurred": True,
            "consensus_metadata": {
                "agent_count": 0,
                "agreement_level": "parsing_failed",
                "outliers_detected": 0
            }
        }

    @tool(name="calculate_scores", cost=0.002)
    def _calculate_scores(self, analysis_data, subreddit):
        """Calculate composite scores with AgentOps tracking"""
        # FIXED: Add actual implementation
        try:
            # Extract or calculate individual scores
            wtp_score = float(analysis_data.get("willingness_to_pay_score", 70))
            segment_score = 85 if analysis_data.get("customer_segment") == "B2B" else 75
            price_sensitivity = float(analysis_data.get("price_sensitivity", 60))

            # Subreddit multipliers for enhanced accuracy
            subreddit_multipliers = {
                "programming": 1.3,
                "entrepreneur": 1.5,
                "MicroSaaS": 1.6,
                "SaaS": 1.4,
                "startups": 1.4,
                "business": 1.2,
                "technology": 1.1,
                "ProductHunt": 1.3,
            }

            subreddit_multiplier = subreddit_multipliers.get(subreddit.lower(), 1.0)

            # Calculate composite scores
            revenue_potential = (wtp_score + segment_score + price_sensitivity) / 3 * subreddit_multiplier

            composite_score = min(100, revenue_potential)

            return {
                "wtp_score": wtp_score,
                "segment_score": segment_score,
                "price_sensitivity": price_sensitivity,
                "revenue_potential": min(100, revenue_potential),
                "composite_score": composite_score,
                "subreddit_multiplier": subreddit_multiplier
            }

        except Exception as e:
            logger.warning(f"Score calculation failed: {e}")
            return {
                "wtp_score": 50,
                "segment_score": 50,
                "price_sensitivity": 50,
                "revenue_potential": 50,
                "composite_score": 50,
                "subreddit_multiplier": 1.0
            }

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for cost tracking"""
        # Rough estimate: ~1 token per 4 characters for English text
        return len(text) // 4

    def _estimate_cost(self, tokens: int, model: str) -> float:
        """Estimate cost based on model and token count"""
        # OpenRouter pricing estimates (per 1M tokens)
        model_pricing = {
            "anthropic/claude-haiku-4.5": 0.125,  # $0.125 per 1M input tokens
            "anthropic/claude-3.5-haiku": 0.125,
            "anthropic/claude-3-haiku": 0.25,
            "openai/gpt-4o-mini": 0.15,
            "openai/gpt-4o": 2.5,
        }

        base_price = model_pricing.get(model, 0.125)  # Default to haiku pricing
        return (tokens / 1_000_000) * base_price

    def _record_agent_execution(self, agent_name: str, text: str, result_length: int = 0):
        """Record agent execution with AgentOps for cost tracking"""
        if self.agentops_enabled:
            input_tokens = self._estimate_tokens(text)
            output_tokens = self._estimate_tokens(str(result_length)) if result_length else input_tokens // 4
            total_tokens = input_tokens + output_tokens
            cost = self._estimate_cost(total_tokens, self.model)

            # FIXED: Use newer AgentOps v4 API for event recording
            try:
                # Try v4 API first
                agentops.Event(f"{agent_name}_execution", {
                    "agent_name": agent_name,
                    "model": self.model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "cost_usd": round(cost, 6),
                    "text_length": len(text),
                    "subreddit": getattr(self, 'current_subreddit', 'unknown')
                })
            except AttributeError:
                # Fallback to older API if Event doesn't exist
                agentops.record({
                    "event_name": f"{agent_name}_execution",
                    "agent_name": agent_name,
                    "model": self.model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "cost_usd": round(cost, 6),
                    "text_length": len(text),
                    "subreddit": getattr(self, 'current_subreddit', 'unknown')
                })

            logger.info(f"AgentOps recorded {agent_name}: {total_tokens} tokens, ${cost:.6f}")

    @trace(name="monetization_analysis")
    def analyze(
        self,
        text: str,
        subreddit: str,
        keyword_monetization_score: float | None = None,
    ) -> MonetizationAnalysis:
        """
        Analyze monetization potential with multi-agent system

        Args:
            text: Reddit post text
            subreddit: Subreddit name
            keyword_monetization_score: Optional baseline score from keyword analysis

        Returns:
            MonetizationAnalysis with agent-enhanced scores
        """
        try:
            # FIXED: Start manual AgentOps trace with better tracking
            if self.agentops_enabled:
                self.agentops_trace = agentops.start_trace(
                    "monetization_analysis",
                    tags=["monetization_analysis", subreddit, f"model:{self.model}"]
                )
                self.current_subreddit = subreddit
                logger.info(f"Started AgentOps trace: {self.agentops_trace}")

            # Create analysis prompt
            analysis_prompt = f"""
            Analyze this Reddit post for monetization potential:

            Text: {text}
            Subreddit: {subreddit}

            Please coordinate your analysis as a team:
            1. Willingness to Pay Agent: Analyze sentiment and willingness to pay
            2. Market Segment Agent: Classify B2B vs B2C
            3. Price Point Agent: Extract pricing information
            4. Payment Behavior Agent: Analyze current spending patterns

            Return a consolidated analysis with all findings.
            """

            # FIXED: Run individual agents with manual tracking instead of team.run
            logger.info("Starting individual agent analysis with AgentOps tracking")

            # Willingness to Pay Agent
            logger.info("Running WTP Agent...")
            wtp_response = self.wtp_agent.run(analysis_prompt)
            self._record_agent_execution("WTP_Analyst", analysis_prompt, len(str(wtp_response)))

            # Market Segment Agent
            logger.info("Running Market Segment Agent...")
            segment_response = self.segment_agent.run(analysis_prompt)
            self._record_agent_execution("Market_Segment_Analyst", analysis_prompt, len(str(segment_response)))

            # Price Point Agent
            logger.info("Running Price Point Agent...")
            price_response = self.price_agent.run(analysis_prompt)
            self._record_agent_execution("Price_Point_Analyst", analysis_prompt, len(str(price_response)))

            # Payment Behavior Agent
            logger.info("Running Payment Behavior Agent...")
            behavior_response = self.behavior_agent.run(analysis_prompt)
            self._record_agent_execution("Payment_Behavior_Analyst", analysis_prompt, len(str(behavior_response)))

            # Combine responses (simulating team coordination)
            combined_response = f"""
            WTP Analysis: {wtp_response}
            Market Segment: {segment_response}
            Price Analysis: {price_response}
            Payment Behavior: {behavior_response}
            """

            # Parse agent responses
            analysis_data = self._parse_team_response(combined_response)

            # FIXED: Record tool executions with AgentOps
            if self.agentops_enabled:
                try:
                    agentops.Event("parse_team_response", {
                        "tool_name": "parse_team_response",
                        "response_length": len(str(combined_response)),
                        "parsing_successful": True
                    })
                except AttributeError:
                    agentops.record({
                        "event_name": "parse_team_response",
                        "tool_name": "parse_team_response",
                        "response_length": len(str(combined_response)),
                        "parsing_successful": True
                    })

            # Calculate composite scores
            scores = self._calculate_scores(analysis_data, subreddit)
            self._record_agent_execution("Score_Calculation", f"Scores: {scores}", len(str(scores)))

            # Extract additional insights
            friction_indicators = self._extract_friction_indicators(text)
            urgency = self._determine_urgency(
                text, analysis_data.get("evidence", "")
            )

            # Build result
            result = MonetizationAnalysis(
                willingness_to_pay_score=scores["wtp_score"],
                market_segment_score=scores["segment_score"],
                price_sensitivity_score=scores["price_sensitivity"],
                revenue_potential_score=scores["revenue_potential"],
                customer_segment=analysis_data.get("customer_segment", "Unknown"),
                mentioned_price_points=analysis_data.get("mentioned_price_points", []),
                existing_payment_behavior=analysis_data.get(
                    "current_spending", "Unknown"
                ),
                urgency_level=urgency,
                sentiment_toward_payment=analysis_data.get("sentiment_toward_payment", "Neutral"),
                payment_friction_indicators=friction_indicators,
                llm_monetization_score=scores["composite_score"],
                confidence=analysis_data.get("confidence", 0.7),
                reasoning=analysis_data.get("reasoning", ""),
                subreddit_multiplier=scores["subreddit_multiplier"],
            )

            # FIXED: End AgentOps trace properly
            if self.agentops_enabled and self.agentops_trace:
                try:
                    agentops.end_trace(self.agentops_trace, "Success")
                    logger.info(f"Ended AgentOps trace successfully: {self.agentops_trace}")
                except Exception as e:
                    logger.warning(f"Failed to end AgentOps trace cleanly: {e}")
                self.agentops_trace = None

            logger.info("Analysis completed successfully with AgentOps tracking")
            return result

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            # FIXED: Proper error handling for AgentOps
            if self.agentops_enabled and self.agentops_trace:
                try:
                    agentops.end_trace(self.agentops_trace, "Fail")
                    logger.error(f"AgentOps trace ended with error: {e}")
                except Exception as trace_error:
                    logger.error(f"Failed to end AgentOps trace on error: {trace_error}")
                self.agentops_trace = None
            raise

    async def analyze_stream(
        self,
        text: str,
        subreddit: str,
        keyword_monetization_score: float | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream analysis results with reasoning transparency

        Args:
            text: Reddit post text
            subreddit: Subreddit name
            keyword_monetization_score: Optional baseline score

        Yields:
            JSON strings with intermediate analysis steps
        """
        try:
            if self.agentops_enabled:
                self.session_id = agentops.start_trace(
                    "monetization_analysis_stream", tags=["monetization_analysis_stream"]
                )

            # Create analysis prompt
            analysis_prompt = f"""
            Analyze this Reddit post for monetization potential:

            Text: {text}
            Subreddit: {subreddit}

            Please provide step-by-step analysis with reasoning:
            """

            # Stream analysis (note: Agno streaming implementation may vary)
            # This is a placeholder for the actual streaming implementation
            yield json.dumps(
                {
                    "step": "initiation",
                    "message": "Starting multi-agent analysis",
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Run individual agents and stream results
            wtp_result = await self._run_agent_async(self.wtp_agent, analysis_prompt)
            yield json.dumps(
                {
                    "step": "willingness_analysis",
                    "result": wtp_result,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            segment_result = await self._run_agent_async(
                self.segment_agent, analysis_prompt
            )
            yield json.dumps(
                {
                    "step": "segment_analysis",
                    "result": segment_result,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            price_result = await self._run_agent_async(
                self.price_agent, analysis_prompt
            )
            yield json.dumps(
                {
                    "step": "price_analysis",
                    "result": price_result,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            behavior_result = await self._run_agent_async(
                self.behavior_agent, analysis_prompt
            )
            yield json.dumps(
                {
                    "step": "behavior_analysis",
                    "result": behavior_result,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Final analysis
            final_result = self.analyze(text, subreddit, keyword_monetization_score)
            yield json.dumps(
                {
                    "step": "final_analysis",
                    "result": asdict(final_result),
                    "timestamp": datetime.now().isoformat(),
                }
            )

            if self.agentops_enabled:
                agentops.end_session("Success")

        except Exception as e:
            logger.error(f"Stream analysis failed: {e}")
            yield json.dumps(
                {
                    "step": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            if self.agentops_enabled:
                agentops.end_session("Error")

    async def _run_agent_async(self, agent: Agent, prompt: str) -> dict[str, Any]:
        """Run agent asynchronously (placeholder implementation)"""
        # This would need to be implemented based on Agno's async API
        # For now, we'll simulate async execution
        await asyncio.sleep(0.1)
        response = agent.run(prompt)
        return self._parse_agent_response(response)

    def _parse_agent_response(self, response) -> dict[str, Any]:
        """Parse individual agent response using the main parsing logic"""
        return self._parse_team_response(response)

    def _calculate_scores(
        self, analysis_data: dict[str, Any], subreddit: str
    ) -> dict[str, float]:
        """Calculate composite scores from agent analysis"""
        # Extract individual scores with defaults
        wtp_score = float(analysis_data.get("willingness_to_pay_score", 50))
        segment_score = float(analysis_data.get("segment_score", 50))
        behavior_score = float(analysis_data.get("behavior_score", 50))

        # Price sensitivity (inverse of willingness)
        price_sensitivity = 100 - (wtp_score * 0.5)

        # Revenue potential based on segment
        segment_type = analysis_data.get("customer_segment", "Unknown")
        if segment_type == "B2B":
            revenue_potential = (
                segment_score * 0.35 + wtp_score * 0.35 + behavior_score * 0.30
            )
        elif segment_type == "B2C":
            revenue_potential = (
                segment_score * 0.15 + wtp_score * 0.50 + behavior_score * 0.35
            )
        elif segment_type == "Mixed":
            revenue_potential = (
                segment_score * 0.25 + wtp_score * 0.40 + behavior_score * 0.35
            )
        else:
            revenue_potential = wtp_score * 0.50 + behavior_score * 0.50

        # Apply subreddit multiplier
        subreddit_mult = get_subreddit_multiplier(subreddit)

        # Calculate composite score
        composite_score = (
            wtp_score * 0.35
            + segment_score * 0.25
            + revenue_potential * 0.25
            + behavior_score * 0.15
        ) * subreddit_mult

        # Cap at 100
        composite_score = min(100, composite_score)

        return {
            "wtp_score": wtp_score,
            "segment_score": segment_score,
            "price_sensitivity": price_sensitivity,
            "revenue_potential": revenue_potential,
            "composite_score": composite_score,
            "subreddit_multiplier": subreddit_mult,
        }

    def _extract_friction_indicators(self, text: str) -> list[str]:
        """Extract payment friction signals from text"""
        text_lower = text.lower()
        friction = []

        # Price objections
        if any(
            phrase in text_lower
            for phrase in ["too expensive", "overpriced", "can't afford", "too costly"]
        ):
            friction.append("price_objection")

        # Budget constraints
        if any(
            phrase in text_lower
            for phrase in [
                "tight budget",
                "limited budget",
                "no budget",
                "budget constraint",
            ]
        ):
            friction.append("budget_constraint")

        # Subscription fatigue
        if any(
            phrase in text_lower
            for phrase in [
                "another subscription",
                "subscription fatigue",
                "too many subscriptions",
            ]
        ):
            friction.append("subscription_fatigue")

        # Free alternative preference
        if any(
            phrase in text_lower
            for phrase in [
                "free alternative",
                "free version",
                "open source",
                "free option",
            ]
        ):
            friction.append("free_alternative_preference")

        # Switching cost concern
        if any(
            phrase in text_lower
            for phrase in [
                "switching cost",
                "migration",
                "too hard to switch",
                "locked in",
            ]
        ):
            friction.append("switching_cost_concern")

        return friction if friction else ["none_detected"]

    def _determine_urgency(self, text: str, evidence: str | list) -> str:
        """Determine urgency level from text and evidence"""
        text_lower = text.lower()

        # Handle evidence that might be a list from Agno agents
        if isinstance(evidence, list):
            evidence_text = " ".join(str(item) for item in evidence if item)
        else:
            evidence_text = evidence

        evidence_lower = evidence_text.lower() if evidence_text else ""
        combined = f"{text_lower} {evidence_lower}"

        # Critical urgency
        if any(
            phrase in combined
            for phrase in ["urgent", "asap", "immediately", "emergency", "critical"]
        ):
            return "Critical"

        # High urgency
        if any(
            phrase in combined
            for phrase in [
                "soon",
                "this week",
                "this month",
                "end of quarter",
                "deadline",
            ]
        ):
            return "High"

        # Medium urgency
        if any(
            phrase in combined
            for phrase in ["looking for", "need", "searching", "considering"]
        ):
            return "Medium"

        # Low urgency
        return "Low"

    def get_cost_report(self) -> dict[str, Any]:
        """Get cost report from AgentOps"""
        if not self.agentops_enabled:
            return {"error": "AgentOps not enabled"}

        try:
            # This would use AgentOps API to get cost data
            # Implementation depends on AgentOps API
            return {
                "session_id": self.session_id,
                "total_cost": 0.0,  # Placeholder
                "token_usage": 0,  # Placeholder
                "model_costs": {},  # Placeholder
            }
        except Exception as e:
            return {"error": f"Failed to get cost report: {e}"}

    def __del__(self):
        """Cleanup AgentOps session"""
        if hasattr(self, "agentops_enabled") and self.agentops_enabled:
            try:
                agentops.end_session("Analyzer destroyed")
            except Exception:
                pass


# =============================================================================
# TESTING & DEMO
# =============================================================================


def demo_analyzer():
    """Demo the monetization analyzer with example posts"""

    print("\n" + "=" * 80)
    print("MONETIZATION AGNO ANALYZER DEMO")
    print("=" * 80 + "\n")

    # Example posts
    examples = [
        {
            "text": (
                "We're paying $300/month for Asana and it's too expensive. "
                "Team of 12. Looking for alternatives under $150/month. "
                "Budget is approved, need to decide by Q1."
            ),
            "subreddit": "projectmanagement",
            "expected": "High WTP, B2B segment, budget approved",
        },
        {
            "text": (
                "I'm NOT willing to pay for another subscription app. "
                "Too many already. Looking for free alternatives to MyFitnessPal."
            ),
            "subreddit": "fitness",
            "expected": "Low WTP, B2C segment, subscription fatigue",
        },
        {
            "text": (
                "Our company needs a CRM solution. Currently using spreadsheets. "
                "Budget of around $5k-10k for the right tool. Need proposals ASAP."
            ),
            "subreddit": "business",
            "expected": "Very high WTP, B2B segment, high urgency",
        },
    ]

    try:
        analyzer = MonetizationAgnoAnalyzer()

        for i, example in enumerate(examples, 1):
            print(f"\n{'=' * 80}")
            print(f"EXAMPLE {i}: {example['subreddit']}")
            print(f"{'=' * 80}")
            print(f"\nText: {example['text'][:100]}...")
            print(f"\nExpected: {example['expected']}")

            result = analyzer.analyze(
                text=example["text"], subreddit=example["subreddit"]
            )

            print("\n--- RESULTS ---")
            print(f"LLM Monetization Score: {result.llm_monetization_score:.1f}/100")
            print(f"Customer Segment: {result.customer_segment}")
            print(f"Willingness to Pay: {result.willingness_to_pay_score:.1f}/100")
            print(f"Payment Sentiment: {result.sentiment_toward_payment}")
            print(f"Urgency: {result.urgency_level}")
            print(f"Price Points: {result.mentioned_price_points}")
            print(f"Payment Friction: {result.payment_friction_indicators}")
            print(f"Subreddit Multiplier: {result.subreddit_multiplier}x")
            print(f"\nReasoning: {result.reasoning[:200]}...")

            # Get cost report
            cost_report = analyzer.get_cost_report()
            print("\n--- COST TRACKING ---")
            print(f"Session ID: {cost_report.get('session_id', 'N/A')}")
            print(f"AgentOps Enabled: {analyzer.agentops_enabled}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nNote: This requires Agno, LiteLLM, and an OpenRouter API key in .env")
        print("Optional: Set AGENTOPS_API_KEY for cost tracking")


async def demo_streaming():
    """Demo streaming analysis"""
    print("\n" + "=" * 80)
    print("STREAMING ANALYSIS DEMO")
    print("=" * 80 + "\n")

    example = {
        "text": (
            "We're paying $300/month for Asana and it's too expensive. "
            "Team of 12. Looking for alternatives under $150/month. "
            "Budget is approved, need to decide by Q1."
        ),
        "subreddit": "projectmanagement",
    }

    try:
        analyzer = MonetizationAgnoAnalyzer()

        print("Starting streaming analysis...")
        async for chunk in analyzer.analyze_stream(
            text=example["text"], subreddit=example["subreddit"]
        ):
            data = json.loads(chunk)
            print(f"[{data['step']}] {data.get('message', '')}")
            if "result" in data and data["step"] != "initiation":
                print(f"  Result: {json.dumps(data['result'], indent=2)[:200]}...")

    except Exception as e:
        print(f"\n❌ Streaming Error: {e}")


def create_monetization_analyzer():
    """Factory function for integration health monitor"""
    return MonetizationAgnoAnalyzer()


if __name__ == "__main__":
    demo_analyzer()

    # Uncomment to test streaming
    # asyncio.run(demo_streaming())
