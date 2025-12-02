#!/usr/bin/env python3
"""
RedditHarbor LLM-Based Monetization Analyzer (Option A Enhancement)

Uses DSPy for intelligent, context-aware monetization potential analysis.
Fixes false positives from naive keyword matching in opportunity_analyzer_agent.py.

Key Improvements:
- Sentiment-aware analysis (understands "NOT willing to pay")
- B2B/B2C differentiation with proper weighting (B2B 35%, B2C 15%)
- Price point extraction from discussions
- Subreddit purchasing power context multipliers
- Existing payment behavior detection
- Payment friction indicator extraction

Integration: Stage 2.5 between keyword scoring and AI profile generation
Cost: ~$0.01 per analysis with gpt-4o-mini
"""

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import dspy

# Add project root to path FIRST (before config imports)
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import centralized configuration
try:
    from config import settings
    # Configure OpenRouter for DSPy (it expects OpenAI-compatible API)
    if settings.OPENROUTER_API_KEY:
        os.environ["OPENAI_API_KEY"] = settings.OPENROUTER_API_KEY
        os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
except ImportError:
    # Fallback for standalone usage
    if os.getenv("OPENROUTER_API_KEY"):
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY")
        os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"


# =============================================================================
# DSPY SIGNATURES - Define what we want the LLM to analyze
# =============================================================================

class WillingnessToPayAnalysis(dspy.Signature):
    """Analyze user willingness to pay with sentiment awareness"""

    text = dspy.InputField(desc="Reddit post text to analyze")
    subreddit = dspy.InputField(desc="Subreddit context")

    sentiment = dspy.OutputField(desc="Positive, Neutral, or Negative")
    willingness_score = dspy.OutputField(desc="0-100 score of willingness to pay")
    evidence = dspy.OutputField(desc="Key phrases that support the score")
    reasoning = dspy.OutputField(desc="Why this score was assigned")


class MarketSegmentClassification(dspy.Signature):
    """Classify B2B vs B2C market segment"""

    text = dspy.InputField(desc="Reddit post text")
    subreddit = dspy.InputField(desc="Subreddit context")

    segment = dspy.OutputField(desc="B2B, B2C, Mixed, or Unknown")
    confidence = dspy.OutputField(desc="0-1 confidence in classification")
    indicators = dspy.OutputField(desc="Signals that indicate this segment")
    segment_score = dspy.OutputField(desc="0-100 score for segment quality")


class PricePointExtraction(dspy.Signature):
    """Extract mentioned price points and budget signals"""

    text = dspy.InputField(desc="Reddit post text")

    price_points = dspy.OutputField(desc="List of mentioned prices with context")
    budget_ceiling = dspy.OutputField(desc="Maximum budget mentioned or inferred")
    pricing_model = dspy.OutputField(desc="Subscription, one-time, freemium, etc.")


class PaymentBehaviorAnalysis(dspy.Signature):
    """Analyze existing payment behavior and switching willingness"""

    text = dspy.InputField(desc="Reddit post text")

    current_spending = dspy.OutputField(desc="What they currently pay for")
    switching_willingness = dspy.OutputField(desc="High, Medium, Low, or Unknown")
    spending_evidence = dspy.OutputField(desc="Evidence of current spending")
    behavior_score = dspy.OutputField(desc="0-100 score based on payment behavior")


# =============================================================================
# DSPY MODULES - Chain of Thought reasoning
# =============================================================================

class WillingnessToPayAnalyzer(dspy.Module):
    """Analyzes willingness to pay with sentiment awareness"""

    def __init__(self):
        super().__init__()
        self.analyze = dspy.ChainOfThought(WillingnessToPayAnalysis)

    def forward(self, text: str, subreddit: str):
        return self.analyze(text=text, subreddit=subreddit)


class MarketSegmentClassifier(dspy.Module):
    """Classifies B2B vs B2C market segment"""

    def __init__(self):
        super().__init__()
        self.classify = dspy.ChainOfThought(MarketSegmentClassification)

    def forward(self, text: str, subreddit: str):
        return self.classify(text=text, subreddit=subreddit)


class PricePointExtractor(dspy.Module):
    """Extracts price points and budget signals"""

    def __init__(self):
        super().__init__()
        self.extract = dspy.ChainOfThought(PricePointExtraction)

    def forward(self, text: str):
        return self.extract(text=text)


class PaymentBehaviorAnalyzer(dspy.Module):
    """Analyzes payment behavior and switching signals"""

    def __init__(self):
        super().__init__()
        self.analyze = dspy.ChainOfThought(PaymentBehaviorAnalysis)

    def forward(self, text: str):
        return self.analyze(text=text)


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


class MonetizationLLMAnalyzer:
    """
    LLM-powered monetization analyzer using DSPy

    Fixes issues with keyword-based scoring:
    - Understands "NOT willing to pay" correctly
    - Differentiates B2B from B2C properly
    - Extracts actual price points mentioned
    - Considers subreddit purchasing power context
    - Detects existing payment behavior
    """

    def __init__(self, model: str = None):
        """
        Initialize analyzer with DSPy and centralized configuration.

        Args:
            model: Optional model override. If not provided, uses priority:
                   1. Explicit model parameter
                   2. MONETIZATION_LLM_MODEL from settings
                   3. OPENROUTER_MODEL from settings
                   4. Default: anthropic/claude-haiku-4.5
        """
        # Determine model using centralized config with proper priority
        if model is None:
            try:
                # Use centralized settings (loads .env.local then .env)
                from config import settings
                model = settings.MONETIZATION_LLM_MODEL
            except (ImportError, AttributeError):
                # Fallback to environment variables directly
                model = (
                    os.getenv("MONETIZATION_LLM_MODEL") or
                    os.getenv("OPENROUTER_MODEL") or
                    "anthropic/claude-haiku-4.5"
                )

        # DSPy expects OpenAI-compatible format when using OpenRouter
        # OpenRouter routes based on model string (e.g., anthropic/claude-haiku-4.5)
        # We prefix with "openai/" for DSPy compatibility
        if not model.startswith("openai/"):
            model = f"openai/{model}"

        # Store model for reference
        self.model = model

        # Configure DSPy with connection pool management
        # Note: DSPy uses httpx internally, which we'll configure below
        self.lm = dspy.LM(model=model)
        dspy.configure(lm=self.lm)

        # Initialize analyzers
        self.wtp_analyzer = WillingnessToPayAnalyzer()
        self.segment_classifier = MarketSegmentClassifier()
        self.price_extractor = PricePointExtractor()
        self.behavior_analyzer = PaymentBehaviorAnalyzer()

    def analyze(
        self,
        text: str,
        subreddit: str,
        keyword_monetization_score: float = None
    ) -> MonetizationAnalysis:
        """
        Analyze monetization potential with LLM

        Args:
            text: Reddit post text
            subreddit: Subreddit name
            keyword_monetization_score: Optional baseline score from keyword analysis

        Returns:
            MonetizationAnalysis with LLM-enhanced scores
        """
        # Run all analyzers
        wtp_result = self.wtp_analyzer(text=text, subreddit=subreddit)
        segment_result = self.segment_classifier(text=text, subreddit=subreddit)
        price_result = self.price_extractor(text=text)
        behavior_result = self.behavior_analyzer(text=text)

        # Extract scores
        wtp_score = self._parse_score(wtp_result.willingness_score)
        segment_score = self._parse_score(segment_result.segment_score)
        behavior_score = self._parse_score(behavior_result.behavior_score)

        # Price sensitivity (inverse of willingness - high prices mentioned = lower sensitivity)
        price_sensitivity = 100 - (wtp_score * 0.5)  # Inverse relationship

        # Revenue potential based on segment and scores
        segment_type = segment_result.segment
        if segment_type == "B2B":
            revenue_potential = segment_score * 0.35 + wtp_score * 0.35 + behavior_score * 0.30
        elif segment_type == "B2C":
            revenue_potential = segment_score * 0.15 + wtp_score * 0.50 + behavior_score * 0.35
        elif segment_type == "Mixed":
            revenue_potential = segment_score * 0.25 + wtp_score * 0.40 + behavior_score * 0.35
        else:  # Unknown
            revenue_potential = wtp_score * 0.50 + behavior_score * 0.50

        # Apply subreddit multiplier
        subreddit_mult = get_subreddit_multiplier(subreddit)

        # Calculate composite LLM monetization score
        llm_score = (
            wtp_score * 0.35 +
            segment_score * 0.25 +
            revenue_potential * 0.25 +
            behavior_score * 0.15
        ) * subreddit_mult

        # Cap at 100
        llm_score = min(100, llm_score)

        # Extract payment friction indicators
        friction_indicators = self._extract_friction_indicators(text)

        # Determine urgency from text
        urgency = self._determine_urgency(text, wtp_result.evidence)

        # Build result
        return MonetizationAnalysis(
            willingness_to_pay_score=wtp_score,
            market_segment_score=segment_score,
            price_sensitivity_score=price_sensitivity,
            revenue_potential_score=revenue_potential,
            customer_segment=segment_type,
            mentioned_price_points=self._parse_price_points(price_result.price_points),
            existing_payment_behavior=behavior_result.current_spending,
            urgency_level=urgency,
            sentiment_toward_payment=wtp_result.sentiment,
            payment_friction_indicators=friction_indicators,
            llm_monetization_score=llm_score,
            confidence=float(segment_result.confidence) if segment_result.confidence else 0.7,
            reasoning=f"WTP: {wtp_result.reasoning} | Segment: {segment_result.indicators}",
            subreddit_multiplier=subreddit_mult
        )

    def _parse_score(self, score_str: str) -> float:
        """Parse score string to float (0-100)"""
        try:
            # Handle various formats: "85", "85.5", "85/100"
            score_str = str(score_str).strip()
            if "/" in score_str:
                score_str = score_str.split("/")[0]
            score = float(score_str)
            return max(0, min(100, score))
        except:
            return 50.0  # Default to middle if parsing fails

    def _parse_price_points(self, price_str: str) -> list[str]:
        """Parse price points string into list"""
        try:
            # Try to parse as JSON list
            if price_str.startswith("["):
                return json.loads(price_str)
            # Otherwise split by common delimiters
            return [p.strip() for p in price_str.split(",") if p.strip()]
        except:
            return [price_str] if price_str else []

    def _extract_friction_indicators(self, text: str) -> list[str]:
        """Extract payment friction signals from text"""
        text_lower = text.lower()
        friction = []

        # Price objections
        if any(phrase in text_lower for phrase in ["too expensive", "overpriced", "can't afford", "too costly"]):
            friction.append("price_objection")

        # Budget constraints
        if any(phrase in text_lower for phrase in ["tight budget", "limited budget", "no budget", "budget constraint"]):
            friction.append("budget_constraint")

        # Subscription fatigue
        if any(phrase in text_lower for phrase in ["another subscription", "subscription fatigue", "too many subscriptions"]):
            friction.append("subscription_fatigue")

        # Free alternative preference
        if any(phrase in text_lower for phrase in ["free alternative", "free version", "open source", "free option"]):
            friction.append("free_alternative_preference")

        # Switching cost concern
        if any(phrase in text_lower for phrase in ["switching cost", "migration", "too hard to switch", "locked in"]):
            friction.append("switching_cost_concern")

        return friction if friction else ["none_detected"]

    def _determine_urgency(self, text: str, evidence: str) -> str:
        """Determine urgency level from text and evidence"""
        text_lower = text.lower()
        evidence_lower = evidence.lower() if evidence else ""
        combined = f"{text_lower} {evidence_lower}"

        # Critical urgency
        if any(phrase in combined for phrase in ["urgent", "asap", "immediately", "emergency", "critical"]):
            return "Critical"

        # High urgency
        if any(phrase in combined for phrase in ["soon", "this week", "this month", "end of quarter", "deadline"]):
            return "High"

        # Medium urgency
        if any(phrase in combined for phrase in ["looking for", "need", "searching", "considering"]):
            return "Medium"

        # Low urgency
        return "Low"


# =============================================================================
# TESTING & DEMO
# =============================================================================

def demo_analyzer():
    """Demo the monetization analyzer with example posts"""

    print("\n" + "="*80)
    print("MONETIZATION LLM ANALYZER DEMO")
    print("="*80 + "\n")

    # Example posts
    examples = [
        {
            "text": "We're paying $300/month for Asana and it's too expensive. Team of 12. Looking for alternatives under $150/month. Budget is approved, need to decide by Q1.",
            "subreddit": "projectmanagement",
            "expected": "High WTP, B2B segment, budget approved"
        },
        {
            "text": "I'm NOT willing to pay for another subscription app. Too many already. Looking for free alternatives to MyFitnessPal.",
            "subreddit": "fitness",
            "expected": "Low WTP, B2C segment, subscription fatigue"
        },
        {
            "text": "Our company needs a CRM solution. Currently using spreadsheets. Budget of around $5k-10k for the right tool. Need proposals ASAP.",
            "subreddit": "business",
            "expected": "Very high WTP, B2B segment, high urgency"
        }
    ]

    try:
        analyzer = MonetizationLLMAnalyzer()

        for i, example in enumerate(examples, 1):
            print(f"\n{'='*80}")
            print(f"EXAMPLE {i}: {example['subreddit']}")
            print(f"{'='*80}")
            print(f"\nText: {example['text'][:100]}...")
            print(f"\nExpected: {example['expected']}")

            result = analyzer.analyze(
                text=example["text"],
                subreddit=example["subreddit"]
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

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nNote: This requires DSPy and an OpenRouter API key in .env")
        print("To test locally: Set OPENROUTER_API_KEY in your .env file")


if __name__ == "__main__":
    demo_analyzer()
