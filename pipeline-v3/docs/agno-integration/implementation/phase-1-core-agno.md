# Phase 1: Core Agno Integration - Implementation Guide

## Front Matter

**Status**: In Progress
**Phase**: 1 of 5
**Timeline**: Week 1 (2 days)
**Priority**: Critical

### Deliverables Checklist

- [ ] `AgnoOpportunityAnalyzer` class implementation
- [ ] WillingnessToPayAgent implementation
- [ ] MarketSegmentAgent implementation
- [ ] PricePointAgent implementation
- [ ] PaymentBehaviorAgent implementation
- [ ] Multi-agent synthesis logic
- [ ] Pipeline v3 format conversion
- [ ] Unit tests with >80% coverage
- [ ] Integration with SimplicityProcessor
- [ ] AgentOps tracking integration

### Related Documents

- **Parent Architecture**: `/pipeline-v3/docs/AGNO_INTEGRATION_ARCHITECTURE.md`
- **Testing Strategy**: Section 7.1 (this document)
- **Phase 2 Guide**: `/pipeline-v3/docs/agno-integration/implementation/phase-2-factory.md`
- **Legacy Reference**: `/agent_tools/monetization_agno_analyzer.py`

---

## 1. Phase 1 Overview

### Objective

Implement the core Agno multi-agent analyzer for Pipeline v3, providing multi-dimensional market intelligence through specialized agent coordination while maintaining full API compatibility with existing OpportunityAnalyzer.

### Scope

**In Scope:**
- Create `AgnoOpportunityAnalyzer` class with Pipeline v3 API compatibility
- Adapt 4 specialized agents from legacy implementation
- Implement multi-agent consensus synthesis logic
- Add Pipeline v3 format conversion (AnalysisResult output)
- Integrate with SimplicityProcessor (3-function enforcement)
- Write comprehensive unit tests (>80% coverage)
- AgentOps monitoring integration

**Out of Scope:**
- Factory pattern integration (Phase 2)
- Jina market research integration (Phase 3)
- Database schema extensions (Phase 4)
- Production deployment (Phase 5)

### Success Criteria

1. **Functional**: `AgnoOpportunityAnalyzer.analyze_submission()` returns valid `AnalysisResult`
2. **Quality**: All agent outputs synthesize into consensus scores
3. **Compatibility**: Maintains Pipeline v3 OpportunityAnalyzer API
4. **Testing**: >80% test coverage with passing unit tests
5. **Performance**: Analysis completes in <10s (sequential mode)
6. **Cost**: Per-submission cost <$0.005

---

## 2. Component Design

### 2.1 AgnoOpportunityAnalyzer

**File**: `pipeline-v3/transform/agno_analyzer.py`

#### Class Structure

```python
class AgnoOpportunityAnalyzer:
    """
    Multi-agent opportunity analyzer using Agno framework

    Maintains Pipeline v3 API compatibility while providing
    multi-dimensional market intelligence through specialized agents.
    """

    def __init__(
        self,
        model: str = "anthropic/claude-haiku-4.5",
        api_key: str = None,
        base_url: str = "https://openrouter.ai/api/v1",
        enable_agentops: bool = True,
        embedding_strategy: EmbeddingStrategy = None
    ):
        """Initialize Agno analyzer with Pipeline v3 compatibility"""

        # Agno Team Setup
        self.team = Team(
            name="OpportunityAnalysisTeam",
            agents=[
                WillingnessToPayAgent(model, api_key, base_url),
                MarketSegmentAgent(model, api_key, base_url),
                PricePointAgent(model, api_key, base_url),
                PaymentBehaviorAgent(model, api_key, base_url)
            ],
            mode="sequential"  # Or "parallel" for faster execution
        )

        # Pipeline v3 Integration
        self.embedding_strategy = embedding_strategy or EmbeddingStrategy(
            FakeEmbeddingProvider()
        )
        self.simplicity_processor = SimplicityProcessor()

        # AgentOps Integration (reuse existing monitoring)
        self.agentops_tracker = get_tracker() if enable_agentops else None

        # Cost Tracking (LiteLLM compatible)
        self.cost_tracker = CostTracking()

    def analyze_submission(self, submission: RedditSubmission) -> AnalysisResult:
        """
        Analyze submission using multi-agent team

        Compatible with Pipeline v3 OpportunityAnalyzer API
        """

        # 1. Prepare Agno input format
        agno_input = self._format_agno_input(submission)

        # 2. Run Agno team analysis
        agno_result = self.team.run(agno_input)

        # 3. Synthesize multi-agent results
        synthesis = self._synthesize_agent_outputs(agno_result)

        # 4. Convert to Pipeline v3 format
        analysis_result = self._convert_to_pipeline_format(
            synthesis, submission
        )

        # 5. Apply simplicity processor (3-function enforcement)
        processed = self.simplicity_processor.process_analysis(analysis_result)

        # 6. Generate embedding
        processed.embedding = self.embedding_strategy.generate_embedding(
            processed
        )

        return processed

    def analyze_batch_with_costs(
        self,
        submissions: List[RedditSubmission]
    ) -> Tuple[List[AnalysisResult], CostSummary]:
        """Batch analysis with comprehensive cost tracking"""
        # Implementation maintains LiteLLM cost tracking compatibility
        pass
```

#### Key Methods

**`_format_agno_input(submission: RedditSubmission) -> dict`**
- Converts RedditSubmission to Agno team input format
- Extracts title, text, subreddit, metadata
- Prepares context for each specialized agent

**`_synthesize_agent_outputs(agno_result: AgnoTeamResult) -> AgnoSynthesis`**
- Combines outputs from 4 specialized agents
- Applies consensus rules (weighted averages)
- Calculates confidence scores
- Returns unified synthesis object

**`_convert_to_pipeline_format(synthesis: AgnoSynthesis, submission: RedditSubmission) -> AnalysisResult`**
- Converts Agno synthesis to Pipeline v3 AnalysisResult
- Maintains Pydantic validation compatibility
- Generates AppIdea and MarketMetrics
- Applies trust level assignment

---

### 2.2 Agent Implementations

**File**: `pipeline-v3/transform/agno_agents.py`

Adapt from: `agent_tools/monetization_agno_analyzer.py`

#### A. WillingnessToPayAgent

```python
@agent(name="WTP Analyst")
class WillingnessToPayAgent(Agent):
    """
    Analyzes Reddit submission for willingness to pay signals

    Adapted for Pipeline v3 opportunity analysis:
    - Sentiment toward payment solutions
    - Budget signals and price mentions
    - Urgency and pain point intensity
    - Market demand indicators
    """

    def __init__(self, model: str, api_key: str, base_url: str):
        super().__init__(
            name="Willingness to Pay Analyst",
            role="Analyze user willingness to pay",
            instructions="""
            Analyze Reddit submission for monetization signals:

            1. Payment Sentiment: Positive/Neutral/Negative
            2. WTP Score: 0-100 based on urgency, pain, mentions
            3. Budget Signals: Explicit prices, budget ranges, value expectations
            4. Market Demand: Problem frequency, audience size, unmet needs

            Output JSON format:
            {
                "wtp_score": float,
                "payment_sentiment": str,
                "budget_signals": List[str],
                "market_demand_score": float,
                "reasoning": str
            }
            """,
            model=OpenAIChat(model=model, api_key=api_key, base_url=base_url)
        )
```

**Output Schema:**
```python
{
    "wtp_score": float,              # 0-100
    "payment_sentiment": str,        # "positive", "neutral", "negative"
    "budget_signals": List[str],     # ["$50/mo mentioned", "willing to pay for X"]
    "market_demand_score": float,    # 0-100
    "pain_score": float,             # 0-100 (urgency × intensity)
    "reasoning": str                 # Detailed analysis explanation
}
```

#### B. MarketSegmentAgent

```python
@agent(name="Market Segment")
class MarketSegmentAgent(Agent):
    """
    Classifies market segment and identifies target audience

    Analysis dimensions:
    - B2B vs B2C classification
    - Industry verticals and niches
    - Audience size estimation
    - Purchasing power multipliers
    """

    def __init__(self, model: str, api_key: str, base_url: str):
        super().__init__(
            name="Market Segment Analyst",
            role="Classify market segment and target audience",
            instructions="""
            Classify the opportunity's market segment:

            1. Segment Type: B2B, B2C, B2B2C, or Hybrid
            2. Industry Vertical: SaaS, E-commerce, Healthcare, etc.
            3. Target Audience: Demographics, psychographics, size
            4. Purchasing Power: Budget ranges, decision-making authority

            Output JSON format:
            {
                "segment_type": str,
                "industry_vertical": str,
                "target_audience": str,
                "audience_size_score": float,
                "purchasing_power_multiplier": float,
                "reasoning": str
            }
            """,
            model=OpenAIChat(model=model, api_key=api_key, base_url=base_url)
        )
```

**Output Schema:**
```python
{
    "segment_type": str,                      # "B2B", "B2C", "B2B2C", "Hybrid"
    "segment_confidence": float,              # 0-100
    "industry_vertical": str,                 # "SaaS", "E-commerce", etc.
    "target_audience": str,                   # Description
    "audience_size_score": float,             # 0-100
    "purchasing_power_multiplier": float,     # 0.5-2.0
    "reasoning": str
}
```

#### C. PricePointAgent

```python
@agent(name="Price Point")
class PricePointAgent(Agent):
    """
    Analyzes pricing strategy and revenue potential

    Analysis dimensions:
    - Optimal price point estimation
    - Pricing model recommendation (subscription/freemium/one-time)
    - Revenue potential scoring
    - Competitive pricing context
    """

    def __init__(self, model: str, api_key: str, base_url: str):
        super().__init__(
            name="Price Point Analyst",
            role="Analyze pricing strategy and revenue potential",
            instructions="""
            Analyze pricing and revenue potential:

            1. Price Point: Estimated optimal price ($X/mo, $Y one-time)
            2. Pricing Model: Subscription, Freemium, One-time, Tiered
            3. Revenue Potential: Score based on price × market × WTP
            4. Urgency Score: How quickly users would pay

            Output JSON format:
            {
                "price_point_low": float,
                "price_point_high": float,
                "pricing_model": str,
                "revenue_potential": float,
                "urgency_score": float,
                "reasoning": str
            }
            """,
            model=OpenAIChat(model=model, api_key=api_key, base_url=base_url)
        )
```

**Output Schema:**
```python
{
    "price_point_low": float,        # Minimum viable price
    "price_point_high": float,       # Maximum market price
    "pricing_model": str,            # "subscription", "freemium", "one-time", "tiered"
    "revenue_potential": float,      # 0-100
    "urgency_score": float,          # 0-100
    "reasoning": str
}
```

#### D. PaymentBehaviorAgent

```python
@agent(name="Payment Behavior")
class PaymentBehaviorAgent(Agent):
    """
    Analyzes payment behavior patterns and friction points

    Analysis dimensions:
    - Purchase pattern identification
    - Payment friction assessment
    - Payment readiness scoring
    - Behavioral monetization insights
    """

    def __init__(self, model: str, api_key: str, base_url: str):
        super().__init__(
            name="Payment Behavior Analyst",
            role="Analyze payment behavior and friction",
            instructions="""
            Analyze payment behavior patterns:

            1. Purchase Pattern: Impulse, Considered, Enterprise
            2. Friction Score: Barriers to payment (0=high friction, 100=low)
            3. Payment Readiness: How ready users are to pay now
            4. Behavior Insights: Patterns, triggers, objections

            Output JSON format:
            {
                "purchase_pattern": str,
                "friction_score": float,
                "payment_readiness": float,
                "behavior_insights": List[str],
                "reasoning": str
            }
            """,
            model=OpenAIChat(model=model, api_key=api_key, base_url=base_url)
        )
```

**Output Schema:**
```python
{
    "purchase_pattern": str,           # "impulse", "considered", "enterprise"
    "friction_score": float,           # 0-100 (higher = less friction)
    "payment_readiness": float,        # 0-100
    "behavior_insights": List[str],    # ["price-sensitive", "feature-driven", etc.]
    "reasoning": str
}
```

---

### 2.3 Multi-Agent Synthesis Logic

**File**: `pipeline-v3/transform/agno_synthesis.py`

#### Synthesis Algorithm

```python
def _synthesize_agent_outputs(
    self,
    agno_result: AgnoTeamResult
) -> AgnoSynthesis:
    """
    Combine outputs from 4 specialized agents into unified analysis

    Consensus Rules:
    - Market Demand: Average of WTP.market_demand and Segment.audience_size
    - Pain Intensity: WTP.pain_score × PaymentBehavior.friction_score
    - Monetization Potential: Consensus of WTP, Price, and PaymentBehavior
    - Final Score: Weighted average with confidence thresholds
    """

    # Extract agent-specific results
    wtp_analysis = agno_result.get_agent_result("WTP Analyst")
    segment_analysis = agno_result.get_agent_result("Market Segment")
    price_analysis = agno_result.get_agent_result("Price Point")
    behavior_analysis = agno_result.get_agent_result("Payment Behavior")

    # Calculate consensus scores
    market_demand = (
        wtp_analysis["market_demand_score"] * 0.6 +
        segment_analysis["audience_size_score"] * 0.4
    )

    pain_intensity = (
        wtp_analysis["pain_score"] * 0.5 +
        behavior_analysis["friction_score"] * 0.3 +
        price_analysis["urgency_score"] * 0.2
    )

    monetization_potential = statistics.mean([
        wtp_analysis["wtp_score"],
        price_analysis["revenue_potential"],
        behavior_analysis["payment_readiness"]
    ])

    # Apply subreddit multipliers (from legacy Agno implementation)
    multiplier = self._get_subreddit_multiplier(submission.subreddit)

    return AgnoSynthesis(
        market_demand=market_demand * multiplier,
        pain_intensity=pain_intensity,
        monetization_potential=monetization_potential,
        confidence_score=self._calculate_consensus_confidence(agno_result),
        agent_details={
            "wtp": wtp_analysis,
            "segment": segment_analysis,
            "price": price_analysis,
            "behavior": behavior_analysis
        }
    )
```

#### Consensus Weights

```python
# Market Demand Calculation
market_demand = (
    wtp_analysis["market_demand_score"] * 0.6 +  # WTP market signals
    segment_analysis["audience_size_score"] * 0.4  # Segment size
)

# Pain Intensity Calculation
pain_intensity = (
    wtp_analysis["pain_score"] * 0.5 +           # User pain severity
    behavior_analysis["friction_score"] * 0.3 +   # Payment barriers
    price_analysis["urgency_score"] * 0.2         # Solution urgency
)

# Monetization Potential Calculation
monetization_potential = mean([
    wtp_analysis["wtp_score"],                    # Willingness to pay
    price_analysis["revenue_potential"],          # Revenue modeling
    behavior_analysis["payment_readiness"]        # Purchase readiness
])
```

#### Subreddit Multipliers

```python
def _get_subreddit_multiplier(self, subreddit: str) -> float:
    """
    Apply purchasing power multipliers based on subreddit

    Based on legacy Agno implementation data
    """
    multipliers = {
        # High purchasing power (B2B, Enterprise)
        "entrepreneur": 1.8,
        "startups": 1.7,
        "smallbusiness": 1.6,
        "saas": 1.5,

        # Medium purchasing power (Prosumer)
        "productivity": 1.3,
        "webdev": 1.2,
        "digitalnomad": 1.2,

        # Standard purchasing power
        "technology": 1.0,
        "software": 1.0,

        # Lower purchasing power (Consumer)
        "freesoftware": 0.8,
        "opensource": 0.7
    }

    return multipliers.get(subreddit.lower(), 1.0)
```

---

### 2.4 Pipeline v3 Format Conversion

**File**: `pipeline-v3/transform/agno_analyzer.py`

```python
def _convert_to_pipeline_format(
    self,
    synthesis: AgnoSynthesis,
    submission: RedditSubmission
) -> AnalysisResult:
    """
    Convert Agno multi-agent synthesis to Pipeline v3 AnalysisResult

    Maintains Pydantic validation and database schema compatibility
    """

    # Generate AppIdea from multi-agent insights
    app_idea = AppIdea(
        title=self._generate_title_from_agents(synthesis),
        app_concept=self._generate_concept_from_agents(synthesis),
        problem_statement=synthesis.agent_details["wtp"]["problem_description"],
        target_audience=synthesis.agent_details["segment"]["target_audience"],
        core_functions=self._extract_core_functions(synthesis)  # Max 3!
    )

    # Build MarketMetrics from consensus scores
    market_metrics = MarketMetrics(
        market_demand=synthesis.market_demand,
        pain_intensity=synthesis.pain_intensity,
        monetization_potential=synthesis.monetization_potential
    )

    # Calculate final score (weighted consensus)
    final_score = (
        synthesis.market_demand * 0.4 +
        synthesis.pain_intensity * 0.3 +
        synthesis.monetization_potential * 0.3
    )

    return AnalysisResult(
        submission_id=submission.id,
        app_idea=app_idea,
        market_metrics=market_metrics,
        final_score=final_score,
        confidence_score=synthesis.confidence_score,
        trust_level=self._calculate_trust_level(synthesis.confidence_score),
        llm_reasoning=self._format_multi_agent_reasoning(synthesis),
        embedding=None,  # Generated later
        created_at=datetime.utcnow()
    )
```

#### Helper Methods

**`_extract_core_functions(synthesis: AgnoSynthesis) -> List[str]`**
```python
def _extract_core_functions(self, synthesis: AgnoSynthesis) -> List[str]:
    """
    Extract top 3 core functions from multi-agent analysis

    Enforces SimplicityProcessor requirement
    """
    # Combine insights from all agents
    all_features = []

    # WTP insights → pain point solutions
    if "features" in synthesis.agent_details["wtp"]:
        all_features.extend(synthesis.agent_details["wtp"]["features"])

    # Segment insights → audience needs
    if "key_features" in synthesis.agent_details["segment"]:
        all_features.extend(synthesis.agent_details["segment"]["key_features"])

    # Price insights → value drivers
    if "value_drivers" in synthesis.agent_details["price"]:
        all_features.extend(synthesis.agent_details["price"]["value_drivers"])

    # Rank by importance and return top 3
    ranked_features = self._rank_features_by_importance(all_features)
    return ranked_features[:3]
```

**`_format_multi_agent_reasoning(synthesis: AgnoSynthesis) -> str`**
```python
def _format_multi_agent_reasoning(self, synthesis: AgnoSynthesis) -> str:
    """
    Format multi-agent reasoning into unified explanation

    Combines individual agent reasoning into cohesive narrative
    """
    return f"""
    Multi-Agent Analysis Summary:

    Willingness to Pay (Score: {synthesis.agent_details['wtp']['wtp_score']:.1f}):
    {synthesis.agent_details['wtp']['reasoning']}

    Market Segment ({synthesis.agent_details['segment']['segment_type']}):
    {synthesis.agent_details['segment']['reasoning']}

    Price Point (${synthesis.agent_details['price']['price_point_low']}-${synthesis.agent_details['price']['price_point_high']}):
    {synthesis.agent_details['price']['reasoning']}

    Payment Behavior ({synthesis.agent_details['behavior']['purchase_pattern']}):
    {synthesis.agent_details['behavior']['reasoning']}

    Consensus Score: {synthesis.confidence_score:.1f}%
    Final Assessment: {self._generate_final_assessment(synthesis)}
    """
```

---

## 3. Testing Requirements

### 3.1 Unit Tests

**File**: `tests/transform/test_agno_analyzer.py`

#### Test Coverage Areas

1. **Initialization Tests**
```python
def test_agno_analyzer_initialization():
    """Test Agno analyzer creates with 4 agents"""
    analyzer = AgnoOpportunityAnalyzer()
    assert len(analyzer.team.agents) == 4
    assert analyzer.team.has_agent("WTP Analyst")
    assert analyzer.team.has_agent("Market Segment")
    assert analyzer.team.has_agent("Price Point")
    assert analyzer.team.has_agent("Payment Behavior")

def test_agno_analyzer_with_custom_model():
    """Test analyzer accepts custom model configuration"""
    analyzer = AgnoOpportunityAnalyzer(
        model="anthropic/claude-opus-4",
        base_url="https://custom-api.com"
    )
    assert analyzer.team.agents[0].model.model == "anthropic/claude-opus-4"
```

2. **Analysis Tests**
```python
def test_analyze_submission_returns_valid_result():
    """Test analysis returns Pipeline v3 AnalysisResult"""
    analyzer = AgnoOpportunityAnalyzer()
    submission = create_test_submission()

    result = analyzer.analyze_submission(submission)

    assert isinstance(result, AnalysisResult)
    assert result.final_score >= 0 and result.final_score <= 100
    assert len(result.app_idea.core_functions) <= 3
    assert result.confidence_score > 0

def test_analyze_submission_with_high_quality_post():
    """Test analysis produces high scores for quality opportunities"""
    analyzer = AgnoOpportunityAnalyzer()
    submission = create_high_quality_submission()

    result = analyzer.analyze_submission(submission)

    assert result.final_score > 60
    assert result.trust_level in ["GOOD", "EXCELLENT"]
    assert result.market_metrics.market_demand > 50
```

3. **Synthesis Tests**
```python
def test_multi_agent_consensus_synthesis():
    """Test consensus logic combines agent outputs correctly"""
    analyzer = AgnoOpportunityAnalyzer()

    # Mock agent results
    mock_agno_result = create_mock_agno_result({
        "WTP Analyst": {"wtp_score": 80, "market_demand_score": 75},
        "Market Segment": {"audience_size_score": 70},
        "Price Point": {"revenue_potential": 85},
        "Payment Behavior": {"payment_readiness": 90}
    })

    synthesis = analyzer._synthesize_agent_outputs(mock_agno_result)

    assert synthesis.market_demand > 0
    assert synthesis.pain_intensity > 0
    assert synthesis.monetization_potential > 0
    assert synthesis.confidence_score > 0

def test_consensus_weights_calculation():
    """Test weighted averaging of agent scores"""
    # Test market demand = WTP * 0.6 + Segment * 0.4
    # Test pain intensity calculation
    # Test monetization potential averaging
    pass
```

4. **Format Conversion Tests**
```python
def test_pipeline_format_conversion():
    """Test Agno synthesis converts to Pipeline v3 format"""
    analyzer = AgnoOpportunityAnalyzer()
    synthesis = create_mock_synthesis()
    submission = create_test_submission()

    result = analyzer._convert_to_pipeline_format(synthesis, submission)

    assert isinstance(result.app_idea, AppIdea)
    assert isinstance(result.market_metrics, MarketMetrics)
    assert result.submission_id == submission.id
    assert result.llm_reasoning is not None

def test_core_functions_extraction():
    """Test core functions limited to 3"""
    analyzer = AgnoOpportunityAnalyzer()
    synthesis = create_synthesis_with_many_features()

    core_functions = analyzer._extract_core_functions(synthesis)

    assert len(core_functions) <= 3
    assert all(isinstance(f, str) for f in core_functions)
```

5. **Cost Tracking Tests**
```python
def test_agno_cost_tracking():
    """Test cost tracking integrates with LiteLLM"""
    analyzer = AgnoOpportunityAnalyzer()
    submissions = [create_test_submission() for _ in range(5)]

    results, cost_summary = analyzer.analyze_batch_with_costs(submissions)

    assert cost_summary.total_cost > 0
    assert len(cost_summary.agent_breakdown) == 4
    assert cost_summary.cost_per_submission > 0

def test_cost_per_submission_under_threshold():
    """Test cost per submission stays under $0.005"""
    analyzer = AgnoOpportunityAnalyzer()
    submission = create_test_submission()

    result = analyzer.analyze_submission(submission)
    cost = analyzer.cost_tracker.get_last_analysis_cost()

    assert cost < 0.005
```

6. **Error Handling Tests**
```python
def test_handles_agent_failure_gracefully():
    """Test analyzer handles individual agent failures"""
    # Test graceful degradation when one agent fails
    # Test fallback to partial consensus
    # Test error logging
    pass

def test_handles_invalid_submission_data():
    """Test analyzer validates input data"""
    # Test empty submission
    # Test missing required fields
    # Test invalid data types
    pass
```

### 3.2 Integration Tests

**File**: `tests/integration/test_agno_pipeline_integration.py`

```python
def test_agno_analyzer_in_full_pipeline():
    """Test Agno analyzer works in complete pipeline"""
    # Extract → Agno Analysis → Load workflow
    # Verify database storage
    # Check AgentOps tracking
    pass

def test_simplicity_processor_integration():
    """Test Agno results processed by SimplicityProcessor"""
    analyzer = AgnoOpportunityAnalyzer()
    submission = create_test_submission()

    result = analyzer.analyze_submission(submission)

    # Verify SimplicityProcessor applied
    assert len(result.app_idea.core_functions) <= 3
    assert result.app_idea.title is not None
    assert result.app_idea.app_concept is not None

def test_agentops_tracking_integration():
    """Test AgentOps tracks Agno analysis"""
    analyzer = AgnoOpportunityAnalyzer(enable_agentops=True)
    submission = create_test_submission()

    result = analyzer.analyze_submission(submission)

    # Verify AgentOps session created
    # Verify agent events logged
    # Verify cost tracked
    pass

def test_embedding_strategy_integration():
    """Test embedding generation works with Agno results"""
    embedding_strategy = EmbeddingStrategy(FakeEmbeddingProvider())
    analyzer = AgnoOpportunityAnalyzer(embedding_strategy=embedding_strategy)
    submission = create_test_submission()

    result = analyzer.analyze_submission(submission)

    assert result.embedding is not None
    assert len(result.embedding) > 0
```

### 3.3 Test Coverage Goals

**Target**: >80% coverage

```
pipeline-v3/transform/agno_analyzer.py       85%
pipeline-v3/transform/agno_agents.py         80%
pipeline-v3/transform/agno_synthesis.py      90%
```

**Key Areas to Cover:**
- All agent initialization paths
- All synthesis calculation branches
- All format conversion methods
- Error handling scenarios
- Cost tracking accuracy
- AgentOps integration points

---

## 4. Implementation Tasks

### Task Breakdown

**Total Estimated Time**: 2 days

#### Day 1: Core Implementation
- [ ] **Task 1.1**: Create `agno_analyzer.py` skeleton (1 hour)
- [ ] **Task 1.2**: Implement `AgnoOpportunityAnalyzer.__init__()` (1 hour)
- [ ] **Task 1.3**: Port 4 agents from legacy to `agno_agents.py` (3 hours)
- [ ] **Task 1.4**: Implement `analyze_submission()` method (2 hours)
- [ ] **Task 1.5**: Add basic error handling and logging (1 hour)

#### Day 2: Synthesis & Testing
- [ ] **Task 2.1**: Implement `_synthesize_agent_outputs()` (2 hours)
- [ ] **Task 2.2**: Implement `_convert_to_pipeline_format()` (2 hours)
- [ ] **Task 2.3**: Write unit tests for all components (3 hours)
- [ ] **Task 2.4**: Integration testing with SimplicityProcessor (1 hour)

### Dependencies

**External Dependencies:**
- `agno` framework (already in project)
- `openai` SDK for OpenAIChat model
- `instructor` for Pydantic validation
- `litellm` for cost tracking

**Internal Dependencies:**
- `pipeline-v3/transform/simplicity_processor.py`
- `pipeline-v3/monitoring/agentops_tracker.py`
- `pipeline-v3/models/analysis_result.py`
- `pipeline-v3/models/reddit_submission.py`

---

## 5. Validation Checklist

### Functional Validation

- [ ] `AgnoOpportunityAnalyzer` initializes with 4 agents
- [ ] `analyze_submission()` returns valid `AnalysisResult`
- [ ] All agent outputs synthesize into consensus scores
- [ ] Core functions limited to 3 (SimplicityProcessor)
- [ ] Embeddings generated correctly
- [ ] Cost tracking works for batch analysis

### Quality Validation

- [ ] Multi-agent consensus produces higher quality than single LLM
- [ ] Confidence scores accurately reflect agent agreement
- [ ] Trust levels assigned correctly (POOR/FAIR/GOOD/EXCELLENT)
- [ ] Reasoning text combines all agent insights

### Compatibility Validation

- [ ] Maintains Pipeline v3 OpportunityAnalyzer API
- [ ] Returns same AnalysisResult structure
- [ ] Works with existing EmbeddingStrategy
- [ ] Integrates with SimplicityProcessor
- [ ] Tracks costs via LiteLLM CostTracking

### Performance Validation

- [ ] Single analysis completes in <10s (sequential mode)
- [ ] Cost per submission <$0.005
- [ ] Memory usage reasonable for batch processing
- [ ] Error rate <5%

---

## 6. Next Steps

### Immediate Actions (Post Phase 1)

1. **Code Review**: Team review of implementation
2. **Performance Testing**: Benchmark against single LLM analyzer
3. **Documentation**: Update API docs with Agno examples
4. **Handoff to Phase 2**: Prepare for factory integration

### Phase 2 Preparation

- Review `analyzer_factory.py` for integration points
- Plan configuration management for Agno mode
- Design factory switching mechanism
- Prepare integration tests for factory pattern

---

## Appendix: Code Examples

### Example Usage

```python
from transform.agno_analyzer import AgnoOpportunityAnalyzer
from models.reddit_submission import RedditSubmission

# Initialize analyzer
analyzer = AgnoOpportunityAnalyzer(
    model="anthropic/claude-haiku-4.5",
    enable_agentops=True
)

# Analyze single submission
submission = RedditSubmission(
    id="abc123",
    title="Need a tool to manage project tasks",
    selftext="My team struggles with task tracking...",
    subreddit="productivity"
)

result = analyzer.analyze_submission(submission)

print(f"Final Score: {result.final_score:.1f}")
print(f"Trust Level: {result.trust_level}")
print(f"Market Demand: {result.market_metrics.market_demand:.1f}")
print(f"Core Functions: {result.app_idea.core_functions}")
```

### Example Test

```python
import pytest
from transform.agno_analyzer import AgnoOpportunityAnalyzer
from tests.fixtures import create_test_submission

def test_agno_analyzer_produces_valid_results():
    """Test Agno analyzer end-to-end"""
    # Arrange
    analyzer = AgnoOpportunityAnalyzer()
    submission = create_test_submission()

    # Act
    result = analyzer.analyze_submission(submission)

    # Assert
    assert result.final_score > 0
    assert len(result.app_idea.core_functions) <= 3
    assert result.confidence_score > 0
    assert result.trust_level in ["POOR", "FAIR", "GOOD", "EXCELLENT"]
```

---

**Document Version**: 1.0
**Created**: 2025-12-03
**Phase**: 1 of 5
**Status**: Ready for Implementation
