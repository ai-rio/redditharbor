# Agent Specifications Reference

## Overview

This document provides complete specifications for all Agno agents integrated into Pipeline v3, including their instructions, prompts, output schemas, subreddit multipliers, and scoring formulas.

**Version**: 1.0
**Last Updated**: 2025-12-03
**Related**: [AGNO_INTEGRATION_ARCHITECTURE.md](../../AGNO_INTEGRATION_ARCHITECTURE.md)

---

## Agent Roster

Pipeline v3 integrates **5 specialized agents** for multi-dimensional opportunity analysis:

1. **WillingnessToPayAgent** - Payment sentiment and budget signal analysis
2. **MarketSegmentAgent** - B2B/B2C classification and market sizing
3. **PricePointAgent** - Revenue modeling and pricing strategy
4. **PaymentBehaviorAgent** - Purchase patterns and friction analysis
5. **MarketResearchAgent** - Real-world market data validation (Jina API)

---

## 1. WillingnessToPayAgent

### Purpose

Analyzes Reddit submissions for willingness to pay signals, including sentiment toward payment solutions, budget indicators, urgency signals, and market demand.

### Agent Configuration

```python
@agent(name="WTP Analyst")
class WillingnessToPayAgent(Agent):
    name = "Willingness to Pay Analyst"
    role = "Analyze user willingness to pay"
    model = OpenAIChat(
        model="anthropic/claude-haiku-4.5",
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )
```

### Agent Instructions

```text
Analyze Reddit submission for monetization signals:

1. Payment Sentiment: Positive/Neutral/Negative
   - Positive: "I'd pay for this", "worth the money", "shut up and take my money"
   - Neutral: No payment mentions, passive interest
   - Negative: "should be free", "not worth paying for", "overpriced"

2. WTP Score: 0-100 based on urgency, pain, mentions
   - 0-20: Low willingness, strong price resistance
   - 21-40: Limited willingness, budget-conscious
   - 41-60: Moderate willingness, conditional interest
   - 61-80: High willingness, clear budget signals
   - 81-100: Very high willingness, urgent need, budget mentioned

3. Budget Signals: Explicit prices, budget ranges, value expectations
   - Extract specific price mentions: "$10/month", "under $50"
   - Identify budget ranges: "budget-friendly", "enterprise pricing"
   - Capture value expectations: "worth 2x competitors", "10x cheaper"

4. Market Demand: Problem frequency, audience size, unmet needs
   - Assess how often the problem occurs: daily, weekly, monthly
   - Estimate audience size: personal, team, organization, industry
   - Identify unmet needs: "no good solution exists", "all tools are lacking"

Output JSON format:
{
    "wtp_score": float,              // 0-100
    "payment_sentiment": str,        // "positive" | "neutral" | "negative"
    "budget_signals": List[str],     // Extracted budget mentions
    "market_demand_score": float,    // 0-100
    "reasoning": str                 // Explanation of analysis
}
```

### Output Schema

```python
class WTPAnalysis(BaseModel):
    """Willingness to Pay Agent output"""

    wtp_score: float = Field(
        ge=0, le=100,
        description="Willingness to pay score (0-100)"
    )
    payment_sentiment: Literal["positive", "neutral", "negative"] = Field(
        description="Overall sentiment toward payment"
    )
    budget_signals: List[str] = Field(
        default_factory=list,
        description="Extracted budget mentions and price references"
    )
    market_demand_score: float = Field(
        ge=0, le=100,
        description="Market demand intensity score (0-100)"
    )
    pain_score: float = Field(
        ge=0, le=100,
        description="Pain point intensity score (0-100)"
    )
    urgency_score: float = Field(
        ge=0, le=100,
        description="User urgency score (0-100)"
    )
    reasoning: str = Field(
        description="Detailed explanation of WTP analysis"
    )
```

### Scoring Formula

```python
# WTP Score Calculation
wtp_score = (
    pain_score * 0.4 +           # Pain intensity: 40%
    urgency_score * 0.3 +        # Urgency signals: 30%
    sentiment_score * 0.3        # Payment sentiment: 30%
)

# Sentiment Score Mapping
sentiment_scores = {
    "positive": 100,
    "neutral": 50,
    "negative": 0
}
```

---

## 2. MarketSegmentAgent

### Purpose

Classifies opportunities as B2B vs B2C, estimates audience size, identifies target industries, and assesses purchasing power.

### Agent Configuration

```python
@agent(name="Market Segment")
class MarketSegmentAgent(Agent):
    name = "Market Segment Analyst"
    role = "Classify B2B vs B2C and estimate market size"
    model = OpenAIChat(
        model="anthropic/claude-haiku-4.5",
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )
```

### Agent Instructions

```text
Classify the opportunity as B2B (Business-to-Business) or B2C (Business-to-Consumer):

1. Market Segment Classification:
   - B2B: Tools for businesses, teams, organizations, professionals
   - B2C: Consumer products, personal use, individual users
   - Hybrid: Both business and consumer applications

2. Target Audience Analysis:
   - Identify primary user persona
   - Estimate audience size: niche, medium, broad, mass market
   - Determine user sophistication level: beginner, intermediate, expert

3. Industry Context:
   - Specify target industry/vertical
   - Assess industry purchasing power: low, medium, high, very high
   - Identify competitive landscape density

4. Purchasing Power Multipliers:
   Apply industry-specific multipliers based on typical budgets:
   - Enterprise SaaS: 2.5x
   - SMB Tools: 1.8x
   - Developer Tools: 1.5x
   - Consumer Apps: 1.0x
   - Hobbyist Tools: 0.8x

Output JSON format:
{
    "segment_type": str,              // "B2B" | "B2C" | "Hybrid"
    "target_audience": str,           // Description of primary users
    "audience_size_score": float,     // 0-100
    "industry_vertical": str,         // Primary industry/category
    "purchasing_power": str,          // "low" | "medium" | "high" | "very_high"
    "purchasing_power_multiplier": float,  // 0.5-3.0
    "confidence": float,              // 0-100
    "reasoning": str
}
```

### Output Schema

```python
class SegmentAnalysis(BaseModel):
    """Market Segment Agent output"""

    segment_type: Literal["B2B", "B2C", "Hybrid"] = Field(
        description="Market segment classification"
    )
    target_audience: str = Field(
        description="Primary target user persona"
    )
    audience_size_score: float = Field(
        ge=0, le=100,
        description="Estimated addressable audience size (0-100)"
    )
    industry_vertical: str = Field(
        description="Primary industry or vertical market"
    )
    purchasing_power: Literal["low", "medium", "high", "very_high"] = Field(
        description="Target market purchasing power level"
    )
    purchasing_power_multiplier: float = Field(
        ge=0.5, le=3.0,
        description="Industry-specific revenue multiplier"
    )
    confidence: float = Field(
        ge=0, le=100,
        description="Classification confidence score"
    )
    reasoning: str = Field(
        description="Explanation of segment classification"
    )
```

### Purchasing Power Multipliers

```python
# Industry-specific purchasing power multipliers
PURCHASING_POWER_MULTIPLIERS = {
    # B2B Segments
    "enterprise_saas": 2.5,
    "fintech": 2.3,
    "healthcare_tech": 2.2,
    "smb_tools": 1.8,
    "marketing_tools": 1.7,
    "developer_tools": 1.5,

    # B2C Segments
    "consumer_apps": 1.0,
    "gaming": 0.9,
    "hobbyist_tools": 0.8,
    "education": 0.7,

    # Hybrid
    "productivity": 1.4,
    "design_tools": 1.3
}
```

---

## 3. PricePointAgent

### Purpose

Models potential revenue, recommends pricing strategies, estimates customer lifetime value, and assesses pricing psychology.

### Agent Configuration

```python
@agent(name="Price Point")
class PricePointAgent(Agent):
    name = "Price Point Analyst"
    role = "Model revenue potential and pricing strategy"
    model = OpenAIChat(
        model="anthropic/claude-haiku-4.5",
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )
```

### Agent Instructions

```text
Analyze revenue potential and recommend pricing strategy:

1. Pricing Model Recommendation:
   - Subscription: Recurring monthly/annual revenue (SaaS)
   - Freemium: Free tier + paid upgrade path
   - One-time: Single purchase with optional add-ons
   - Usage-based: Pay-per-use or consumption pricing
   - Tiered: Multiple price points for different features

2. Price Point Estimation:
   - Recommend specific price ranges based on:
     * Value delivered vs problem cost
     * Competitive pricing benchmarks
     * Target market purchasing power
     * Feature complexity and differentiation
   - Provide low, medium, high price scenarios

3. Revenue Modeling:
   - Calculate potential revenue per customer
   - Estimate customer lifetime value (LTV)
   - Assess revenue scalability potential
   - Consider conversion rate expectations

4. Pricing Psychology:
   - Anchor pricing: Reference points for value perception
   - Tiering strategy: Good-better-best positioning
   - Price elasticity: Sensitivity to price changes
   - Psychological thresholds: $10, $50, $100, $500, $1000

Output JSON format:
{
    "pricing_model": str,           // Recommended model
    "price_points": {
        "low": float,               // Minimum viable price
        "medium": float,            // Target price point
        "high": float               // Premium price ceiling
    },
    "revenue_potential": float,     // 0-100 score
    "ltv_estimate": float,          // Estimated LTV in USD
    "pricing_strategy": str,        // Strategic recommendation
    "urgency_score": float,         // 0-100
    "reasoning": str
}
```

### Output Schema

```python
class PriceAnalysis(BaseModel):
    """Price Point Agent output"""

    pricing_model: Literal[
        "subscription",
        "freemium",
        "one_time",
        "usage_based",
        "tiered"
    ] = Field(description="Recommended pricing model")

    price_points: Dict[str, float] = Field(
        description="Low/medium/high price scenarios"
    )

    revenue_potential: float = Field(
        ge=0, le=100,
        description="Revenue potential score (0-100)"
    )

    ltv_estimate: float = Field(
        ge=0,
        description="Estimated customer lifetime value (USD)"
    )

    pricing_strategy: str = Field(
        description="Strategic pricing recommendation"
    )

    urgency_score: float = Field(
        ge=0, le=100,
        description="Revenue urgency/opportunity score"
    )

    reasoning: str = Field(
        description="Pricing analysis explanation"
    )
```

### Revenue Scoring Formula

```python
# Revenue Potential Score Calculation
revenue_potential = (
    ltv_estimate_normalized * 0.4 +    # LTV potential: 40%
    pricing_model_score * 0.3 +         # Model suitability: 30%
    market_fit_score * 0.3              # Price-market fit: 30%
)

# Pricing Model Scores (based on scalability)
pricing_model_scores = {
    "subscription": 100,    # Highest recurring revenue
    "usage_based": 90,      # Scalable with usage
    "tiered": 85,           # Multiple revenue streams
    "freemium": 70,         # Conversion dependency
    "one_time": 50          # Lower LTV potential
}
```

---

## 4. PaymentBehaviorAgent

### Purpose

Analyzes user purchase patterns, identifies friction points in the payment journey, assesses payment readiness, and recommends behavioral optimizations.

### Agent Configuration

```python
@agent(name="Payment Behavior")
class PaymentBehaviorAgent(Agent):
    name = "Payment Behavior Analyst"
    role = "Analyze purchase patterns and payment friction"
    model = OpenAIChat(
        model="anthropic/claude-haiku-4.5",
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )
```

### Agent Instructions

```text
Analyze user payment behavior and purchase readiness:

1. Purchase Pattern Analysis:
   - Buying trigger: What motivates purchase decision?
   - Decision timeline: Immediate, short-term, long-term consideration
   - Purchase journey: Discovery → Research → Comparison → Purchase
   - Payment preferences: Credit card, invoice, trial-first, etc.

2. Friction Point Identification:
   - Identify barriers to purchase:
     * Complexity: "too complicated to set up"
     * Trust: "not sure if it works", "need social proof"
     * Budget: "need approval", "waiting for budget cycle"
     * Integration: "worried about compatibility"
   - Assess friction severity: low, medium, high

3. Payment Readiness Score:
   - 0-20: Not ready, major blockers present
   - 21-40: Low readiness, significant friction
   - 41-60: Moderate readiness, some concerns
   - 61-80: High readiness, minor friction
   - 81-100: Very high readiness, ready to purchase

4. Behavioral Optimization:
   - Recommend friction reduction strategies
   - Suggest conversion optimization tactics
   - Identify trust-building requirements

Output JSON format:
{
    "payment_readiness": float,       // 0-100
    "friction_score": float,          // 0-100 (inverse: low friction = high score)
    "purchase_triggers": List[str],   // Key buying motivations
    "friction_points": List[str],     // Identified barriers
    "decision_timeline": str,         // "immediate" | "short_term" | "long_term"
    "optimization_recommendations": List[str],
    "reasoning": str
}
```

### Output Schema

```python
class BehaviorAnalysis(BaseModel):
    """Payment Behavior Agent output"""

    payment_readiness: float = Field(
        ge=0, le=100,
        description="Purchase readiness score (0-100)"
    )

    friction_score: float = Field(
        ge=0, le=100,
        description="Friction score (0=high friction, 100=low friction)"
    )

    purchase_triggers: List[str] = Field(
        default_factory=list,
        description="Key motivations for purchase"
    )

    friction_points: List[str] = Field(
        default_factory=list,
        description="Identified barriers to purchase"
    )

    decision_timeline: Literal["immediate", "short_term", "long_term"] = Field(
        description="Expected purchase decision timeline"
    )

    optimization_recommendations: List[str] = Field(
        default_factory=list,
        description="Strategies to reduce friction"
    )

    reasoning: str = Field(
        description="Behavioral analysis explanation"
    )
```

### Friction Scoring Formula

```python
# Friction Score Calculation (inverse: lower friction = higher score)
friction_score = 100 - (
    complexity_penalty * 0.3 +       # Complexity barriers: 30%
    trust_penalty * 0.3 +            # Trust/credibility issues: 30%
    budget_penalty * 0.2 +           # Budget constraints: 20%
    integration_penalty * 0.2        # Technical integration: 20%
)

# Penalty Ranges
penalty_levels = {
    "low": 10,      # Minor friction
    "medium": 40,   # Moderate friction
    "high": 70      # Major friction
}
```

---

## 5. MarketResearchAgent

### Purpose

Performs real-world market validation using Jina Reader API to gather competitive pricing, market size data, and product launch benchmarks from actual web sources.

### Agent Configuration

```python
@agent(name="Market Research Analyst")
class MarketResearchAgent(Agent):
    name = "Market Research Analyst"
    role = "Validate opportunities with real market data"
    model = OpenAIChat(
        model="anthropic/claude-haiku-4.5",
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )

    # Inject MarketDataValidator tool
    market_validator: MarketDataValidator = MarketDataValidator(
        enable_mcp_experimental=True
    )
```

### Agent Instructions

```text
You are an expert market researcher using real-world data sources.

Use the MarketDataValidator tool to:

1. Search for competitors using Jina web search
   - Query examples:
     * "[app concept] pricing"
     * "[target market] tools pricing comparison"
     * "[problem space] SaaS solutions"
   - Retrieve top 5-10 competitor URLs

2. Extract pricing data from competitor websites
   - Use Jina Reader API to fetch pricing pages
   - Extract structured data:
     * Pricing tiers (Free, Pro, Enterprise, etc.)
     * Pricing models (monthly, annual, per-seat, usage-based)
     * Feature comparisons across tiers
     * Target markets (SMB, Enterprise, etc.)
   - Confidence score based on data clarity

3. Find market size data from industry reports
   - Query for market research reports:
     * "TAM SAM SOM [industry] market size"
     * "[vertical] market growth rate CAGR"
     * "Statista Grand View Research [industry]"
   - Extract:
     * TAM (Total Addressable Market)
     * SAM (Serviceable Addressable Market)
     * Growth rate (CAGR)
     * Report source and date

4. Identify similar product launches for benchmarking
   - Search Product Hunt, Hacker News, tech blogs
   - Extract launch metrics:
     * Product name and category
     * Launch platform (Product Hunt, etc.)
     * Upvotes/traction metrics
     * Funding/user numbers if available

Return structured evidence:
{
    "competitor_pricing": List[CompetitorPricing],
    "market_size": MarketSizeData,
    "similar_launches": List[ProductLaunchData],
    "validation_score": float (0-100),
    "data_quality_score": float (0-100),
    "reasoning": str,
    "evidence_urls": List[str]
}

IMPORTANT:
- All data must come from real sources via Jina API
- Do NOT hallucinate market data - only use extracted information
- If data cannot be found, report low confidence scores
- Include source URLs for all extracted data
```

### Output Schema

```python
class MarketResearchAnalysis(BaseModel):
    """Market Research Agent output"""

    competitor_pricing: List[CompetitorPricing] = Field(
        default_factory=list,
        description="Pricing data from competitor analysis"
    )

    market_size: Optional[MarketSizeData] = Field(
        default=None,
        description="Market size data from industry reports"
    )

    similar_launches: List[ProductLaunchData] = Field(
        default_factory=list,
        description="Benchmark data from similar product launches"
    )

    validation_score: float = Field(
        ge=0, le=100,
        description="Market validation score based on evidence"
    )

    data_quality_score: float = Field(
        ge=0, le=100,
        description="Data quality and source credibility score"
    )

    reasoning: str = Field(
        description="Evidence-based market validation reasoning"
    )

    search_queries_used: List[str] = Field(
        default_factory=list,
        description="Jina search queries executed"
    )

    evidence_urls: List[str] = Field(
        default_factory=list,
        description="URLs of data sources"
    )

    jina_cost: float = Field(
        ge=0,
        description="Total Jina API cost (USD)"
    )


class CompetitorPricing(BaseModel):
    """Competitor pricing data structure"""

    company: str
    pricing_model: Literal["subscription", "freemium", "one_time", "usage_based", "tiered"]
    tiers: List[PricingTier]
    target: Literal["SMB", "Enterprise", "Consumer", "Developer"]
    url: str
    confidence: float = Field(ge=0, le=100)


class PricingTier(BaseModel):
    """Pricing tier details"""

    name: str  # e.g., "Free", "Pro", "Enterprise"
    price: Optional[float]  # Monthly price in USD
    billing_cycle: Optional[str]  # "monthly", "annual"
    features: List[str]


class MarketSizeData(BaseModel):
    """Market size information"""

    tam_value: Optional[str]  # e.g., "$50B"
    sam_value: Optional[str]
    growth_rate: Optional[str]  # e.g., "15% CAGR"
    source_name: str
    source_url: str
    report_date: Optional[str]


class ProductLaunchData(BaseModel):
    """Product launch benchmark data"""

    product: str
    platform: str  # "Product Hunt", "Hacker News", etc.
    upvotes: Optional[int]
    url: str
    launch_date: Optional[str]
```

### Validation Scoring Formula

```python
# Market Validation Score Calculation
validation_score = (
    competitor_evidence_score * 0.4 +    # Competitor data: 40%
    market_size_evidence_score * 0.3 +   # Market size data: 30%
    launch_benchmark_score * 0.3         # Launch benchmarks: 30%
)

# Evidence Quality Scoring
competitor_evidence_score = min(100, (
    len(competitor_pricing) * 20  # 5 competitors = 100 points
))

market_size_evidence_score = (
    100 if market_size.tam_value else 0
)

launch_benchmark_score = min(100, (
    len(similar_launches) * 33  # 3 launches = 100 points
))

# Data Quality Score
data_quality_score = (
    source_credibility * 0.5 +    # Source reputation: 50%
    data_completeness * 0.3 +     # Data completeness: 30%
    data_freshness * 0.2          # Report recency: 20%
)
```

---

## Subreddit Multipliers

### Purpose

Adjust opportunity scores based on subreddit purchasing power and audience quality.

### Multiplier Table

```python
SUBREDDIT_MULTIPLIERS = {
    # High Purchasing Power (Enterprise, B2B)
    "saas": 2.5,
    "b2bsales": 2.3,
    "entrepreneur": 2.2,
    "startups": 2.1,
    "smallbusiness": 1.9,

    # Medium-High (Professional, Developer)
    "webdev": 1.7,
    "programming": 1.6,
    "devops": 1.7,
    "sysadmin": 1.6,
    "datascience": 1.8,

    # Medium (Productivity, Tools)
    "productivity": 1.5,
    "notion": 1.4,
    "excel": 1.3,
    "googlesheets": 1.3,

    # Medium-Low (Consumer, Hobbyist)
    "lifehacks": 1.2,
    "software": 1.2,
    "apps": 1.1,

    # Low (General Interest)
    "technology": 1.0,
    "askreddit": 0.8,
    "lifeprotips": 0.9,

    # Default
    "default": 1.0
}
```

### Application Formula

```python
# Apply multiplier to market demand score
adjusted_market_demand = (
    base_market_demand * subreddit_multiplier
)

# Multiplier selection
def get_subreddit_multiplier(subreddit_name: str) -> float:
    """Get multiplier for subreddit, defaulting to 1.0"""
    return SUBREDDIT_MULTIPLIERS.get(
        subreddit_name.lower(),
        SUBREDDIT_MULTIPLIERS["default"]
    )
```

---

## Multi-Agent Consensus Synthesis

### Consensus Scoring Formulas

```python
# Market Demand Consensus
market_demand = (
    wtp_analysis.market_demand_score * 0.6 +
    segment_analysis.audience_size_score * 0.4
)

# Pain Intensity Consensus
pain_intensity = (
    wtp_analysis.pain_score * 0.5 +
    behavior_analysis.friction_score * 0.3 +
    price_analysis.urgency_score * 0.2
)

# Monetization Potential Consensus
monetization_potential = statistics.mean([
    wtp_analysis.wtp_score,
    price_analysis.revenue_potential,
    behavior_analysis.payment_readiness
])

# Final Score (Weighted Average)
final_score = (
    market_demand * 0.4 +
    pain_intensity * 0.3 +
    monetization_potential * 0.3
) * subreddit_multiplier

# Confidence Score
confidence_score = statistics.mean([
    wtp_analysis.confidence if hasattr(wtp_analysis, 'confidence') else 70,
    segment_analysis.confidence,
    100 - abs(agent_variance)  # Lower variance = higher confidence
])

# Agent Variance Calculation
agent_variance = statistics.stdev([
    wtp_analysis.wtp_score,
    segment_analysis.audience_size_score,
    price_analysis.revenue_potential,
    behavior_analysis.payment_readiness
])
```

### Trust Level Assignment

```python
def calculate_trust_level(confidence_score: float) -> str:
    """Assign trust level based on confidence score"""

    if confidence_score >= 80:
        return "high"
    elif confidence_score >= 60:
        return "medium"
    elif confidence_score >= 40:
        return "low"
    else:
        return "very_low"
```

---

## Usage Example

### Complete Analysis Flow

```python
from pipeline_v3.transform.agno_analyzer import AgnoOpportunityAnalyzer
from pipeline_v3.extract.models import RedditSubmission

# Initialize analyzer
analyzer = AgnoOpportunityAnalyzer(
    model="anthropic/claude-haiku-4.5",
    enable_agentops=True
)

# Analyze submission
submission = RedditSubmission(
    id="abc123",
    title="Need a tool to automate invoicing",
    text="Our small business manually creates 100+ invoices monthly...",
    subreddit="smallbusiness"
)

result = analyzer.analyze_submission(submission)

# Access agent-specific results
print(f"WTP Score: {result.agno_wtp_score}")
print(f"Segment: {result.agno_segment_type}")
print(f"Revenue Potential: {result.agno_price_potential}")
print(f"Payment Readiness: {result.agno_behavior_score}")
print(f"Market Validation: {result.jina_validation_score}")
print(f"Final Score: {result.final_score}")
print(f"Confidence: {result.confidence_score}")
print(f"Trust Level: {result.trust_level}")
```

---

## Performance Metrics

### Expected Agent Performance

| Agent | Avg Latency | Cost per Run | Success Rate |
|-------|------------|--------------|--------------|
| WillingnessToPayAgent | 2-3s | $0.0008 | >95% |
| MarketSegmentAgent | 2-3s | $0.0008 | >95% |
| PricePointAgent | 2-3s | $0.0008 | >95% |
| PaymentBehaviorAgent | 2-3s | $0.0008 | >95% |
| MarketResearchAgent | 15-30s | $0.005-0.01 | >90% |

### Total Analysis Performance

- **Sequential Mode**: 25-40s per submission
- **Parallel Mode**: 15-30s per submission
- **Total Cost**: $0.004-0.014 per submission
- **Consensus Accuracy**: 85%+ improvement over single LLM

---

## References

- **Architecture Document**: [AGNO_INTEGRATION_ARCHITECTURE.md](../../AGNO_INTEGRATION_ARCHITECTURE.md)
- **Data Models**: [data-models.md](./data-models.md)
- **API Compatibility**: [api-compatibility.md](./api-compatibility.md)
- **Legacy Implementation**: `/agent_tools/monetization_agno_analyzer.py`
- **Jina Integration**: `/docs/integrations/jina/`

---

**Document Version**: 1.0
**Author**: RedditHarbor Engineering Team
**Status**: Reference Documentation
