"""
Shared fixtures and configuration for Agno integration tests

Following TDD principles - these fixtures support RED-GREEN-REFACTOR workflow
"""

import pytest
from datetime import datetime, UTC
from uuid import uuid4
from typing import Dict, Any

from models.reddit import RedditSubmission
from models.analysis import AnalysisResult, AppIdea, MarketMetrics


@pytest.fixture
def sample_reddit_submission():
    """
    Create a high-quality Reddit submission for testing

    Represents a typical opportunity with clear pain points and monetization potential
    """
    return RedditSubmission(
        id=str(uuid4()),
        title="Need a tool to automate invoice generation for freelancers",
        text="""
        As a freelancer, I spend 10+ hours every month creating and sending invoices manually.
        The current tools are either too expensive ($50/mo) or lack features I need.

        Pain points:
        - Manual data entry from time tracking tools
        - Following up on late payments
        - Tax calculation and reporting
        - Client-specific invoice formats

        I'd pay $20-30/month for a tool that:
        - Auto-generates invoices from time tracking
        - Sends automated payment reminders
        - Integrates with accounting software

        Other freelancers in my network have the same problem.
        """,
        author="freelancer_dev",
        upvotes=245,
        downvotes=12,
        score=233,
        comments_count=87,
        subreddit="freelance",
        created_utc=datetime.now(UTC).replace(year=2024, month=11, day=15),
        permalink="/r/freelance/comments/test123/need_invoice_tool/",
        url=None,
        is_self=True,
        over_18=False
    )


@pytest.fixture
def low_quality_submission():
    """
    Create a low-quality Reddit submission for testing

    Represents spam or irrelevant content
    """
    return RedditSubmission(
        id=str(uuid4()),
        title="FREE MONEY!!! CLICK HERE NOW!!!",
        text="Make $1000/day working from home! Limited time offer! Act now!",
        author="spammer123",
        upvotes=2,
        downvotes=50,
        score=-48,
        comments_count=1,
        subreddit="spam",
        created_utc=datetime.now(UTC),
        permalink="/r/spam/comments/spam123/free_money/",
        url=None,
        is_self=True,
        over_18=False
    )


@pytest.fixture
def b2b_submission():
    """B2B opportunity submission"""
    return RedditSubmission(
        id=str(uuid4()),
        title="Enterprise API rate limiting solution needed",
        text="""
        Our SaaS company needs better API rate limiting for enterprise clients.
        Current solutions don't handle complex multi-tenant scenarios.
        Budget: $10k+ for the right solution.
        """,
        author="cto_saas",
        upvotes=156,
        downvotes=8,
        score=148,
        comments_count=42,
        subreddit="entrepreneur",
        created_utc=datetime.now(UTC),
        permalink="/r/entrepreneur/comments/b2b123/api_rate_limiting/",
        url=None,
        is_self=True,
        over_18=False
    )


@pytest.fixture
def b2c_submission():
    """B2C opportunity submission"""
    return RedditSubmission(
        id=str(uuid4()),
        title="App to help me remember to water my plants",
        text="""
        I keep killing my plants because I forget to water them.
        Would love a simple app with reminders and care tips.
        """,
        author="plant_lover",
        upvotes=89,
        downvotes=5,
        score=84,
        comments_count=34,
        subreddit="houseplants",
        created_utc=datetime.now(UTC),
        permalink="/r/houseplants/comments/b2c123/plant_water_reminder/",
        url=None,
        is_self=True,
        over_18=False
    )


@pytest.fixture
def mock_wtp_analysis():
    """Mock WillingnessToPayAgent output"""
    return {
        "wtp_score": 75.0,
        "payment_sentiment": "positive",
        "budget_signals": ["$20-30/month mentioned", "willing to pay for automation"],
        "market_demand_score": 80.0,
        "pain_score": 85.0,
        "urgency_score": 70.0,
        "reasoning": "Strong willingness to pay indicated by explicit budget mention and pain severity"
    }


@pytest.fixture
def mock_segment_analysis():
    """Mock MarketSegmentAgent output"""
    return {
        "segment_type": "B2B",
        "segment_confidence": 90.0,
        "industry_vertical": "Freelance Services",
        "target_audience": "Independent freelancers and consultants",
        "audience_size_score": 75.0,
        "purchasing_power_multiplier": 1.5,
        "reasoning": "Target audience is freelancers with demonstrated purchasing power"
    }


@pytest.fixture
def mock_price_analysis():
    """Mock PricePointAgent output"""
    return {
        "price_point_low": 19.99,
        "price_point_high": 49.99,
        "pricing_model": "subscription",
        "revenue_potential": 82.0,
        "urgency_score": 75.0,
        "reasoning": "Subscription model fits recurring need, price point validated by user budget signals"
    }


@pytest.fixture
def mock_behavior_analysis():
    """Mock PaymentBehaviorAgent output"""
    return {
        "purchase_pattern": "considered",
        "friction_score": 70.0,
        "payment_readiness": 68.0,
        "behavior_insights": ["price-sensitive", "feature-driven", "problem-aware"],
        "reasoning": "Users are aware of the problem and actively seeking solutions"
    }


@pytest.fixture
def mock_agno_team_result(
    mock_wtp_analysis,
    mock_segment_analysis,
    mock_price_analysis,
    mock_behavior_analysis
):
    """
    Mock complete Agno Team result with all agent outputs

    This fixture simulates the response from Agno Team after running all agents
    """
    class MockAgnoResult:
        def __init__(self, agent_results: Dict[str, Any]):
            self.agent_results = agent_results

        def get_agent_result(self, agent_name: str) -> Dict[str, Any]:
            """Get result from specific agent"""
            return self.agent_results.get(agent_name, {})

    return MockAgnoResult({
        "WTP Analyst": mock_wtp_analysis,
        "Market Segment": mock_segment_analysis,
        "Price Point": mock_price_analysis,
        "Payment Behavior": mock_behavior_analysis
    })


@pytest.fixture
def expected_analysis_result_schema():
    """
    Define expected AnalysisResult schema for validation

    Used to verify that AgnoOpportunityAnalyzer returns correct format
    """
    return {
        "required_fields": [
            "submission_id",
            "app_idea",
            "market_metrics",
            "final_score",
            "confidence_score",
            "trust_level",
            "llm_reasoning"
        ],
        "optional_fields": [
            "embedding",
            "embedding_metadata",
            "agno_wtp_score",
            "agno_segment_type",
            "agno_segment_confidence",
            "agno_price_potential",
            "agno_behavior_score",
            "agno_consensus_confidence"
        ],
        "score_ranges": {
            "final_score": (0.0, 100.0),
            "confidence_score": (0.0, 100.0),
            "market_demand": (0.0, 100.0),
            "pain_intensity": (0.0, 100.0),
            "monetization_potential": (0.0, 100.0)
        },
        "valid_trust_levels": ["POOR", "FAIR", "GOOD", "EXCELLENT"],
        "valid_segment_types": ["B2B", "B2C", "Hybrid"],
        "max_core_functions": 3
    }


@pytest.fixture
def subreddit_multipliers():
    """
    Subreddit purchasing power multipliers for testing

    Based on legacy Agno implementation
    """
    return {
        # High purchasing power (B2B, Enterprise)
        "entrepreneur": 1.8,
        "startups": 1.7,
        "smallbusiness": 1.6,
        "saas": 1.5,
        # Medium purchasing power (Prosumer)
        "freelance": 1.3,
        "productivity": 1.3,
        "webdev": 1.2,
        "digitalnomad": 1.2,
        # Standard purchasing power
        "technology": 1.0,
        "software": 1.0,
        # Lower purchasing power (Consumer)
        "houseplants": 0.9,
        "freesoftware": 0.8,
        "opensource": 0.7
    }


def assert_valid_analysis_result(analysis: AnalysisResult, schema: dict):
    """
    Helper function to validate AnalysisResult against expected schema

    Args:
        analysis: AnalysisResult to validate
        schema: Expected schema from expected_analysis_result_schema fixture
    """
    # Check required fields exist
    for field in schema["required_fields"]:
        assert hasattr(analysis, field), f"Missing required field: {field}"
        assert getattr(analysis, field) is not None, f"Required field is None: {field}"

    # Check score ranges
    for score_field, (min_val, max_val) in schema["score_ranges"].items():
        if hasattr(analysis, score_field):
            score = getattr(analysis, score_field)
            if score is not None:
                assert min_val <= score <= max_val, \
                    f"{score_field} out of range: {score} not in [{min_val}, {max_val}]"
        elif hasattr(analysis.market_metrics, score_field):
            score = getattr(analysis.market_metrics, score_field)
            if score is not None:
                assert min_val <= score <= max_val, \
                    f"{score_field} out of range: {score} not in [{min_val}, {max_val}]"

    # Check trust level
    if analysis.trust_level:
        assert analysis.trust_level in schema["valid_trust_levels"], \
            f"Invalid trust_level: {analysis.trust_level}"

    # Check core functions limit
    assert len(analysis.app_idea.core_functions) <= schema["max_core_functions"], \
        f"Too many core functions: {len(analysis.app_idea.core_functions)} > {schema['max_core_functions']}"

    # Check segment type if present
    if hasattr(analysis, "agno_segment_type") and analysis.agno_segment_type:
        assert analysis.agno_segment_type in schema["valid_segment_types"], \
            f"Invalid segment_type: {analysis.agno_segment_type}"
