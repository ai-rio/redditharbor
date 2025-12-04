# Agno Integration Testing Strategy

**Document Status**: Implementation Guide
**Version**: 1.0
**Created**: 2025-12-03
**Component**: Pipeline v3 - Agno Multi-Agent Integration

---

## Table of Contents

1. [Testing Philosophy](#1-testing-philosophy)
2. [TDD Applicability Matrix](#2-tdd-applicability-matrix)
3. [Phase-by-Phase Testing Approach](#3-phase-by-phase-testing-approach)
4. [Coverage Targets by Component](#4-coverage-targets-by-component)
5. [Testing Workflow Examples](#5-testing-workflow-examples)
6. [Unit Testing Strategy](#6-unit-testing-strategy)
7. [Integration Testing Strategy](#7-integration-testing-strategy)
8. [Testing Tools and Infrastructure](#8-testing-tools-and-infrastructure)
9. [Continuous Testing Workflow](#9-continuous-testing-workflow)

---

## 1. Testing Philosophy

### 1.1 Guiding Principles

**Pragmatic Test-Driven Development (TDD)**
- Apply TDD where it provides maximum value: complex business logic and data transformations
- Use test-after for exploratory work: external API integrations and agent behavior tuning
- Balance coverage with velocity: target 80% overall, 100% for critical paths

**Risk-Based Testing**
- **High Risk**: Multi-agent consensus logic, cost tracking, data persistence
- **Medium Risk**: Agent orchestration, API integrations, format conversions
- **Low Risk**: Simple getters, configuration loading, logging

**Integration-First for AI Systems**
- AI agent behavior is emergent and non-deterministic
- Integration tests validate actual agent interactions
- Unit tests focus on deterministic helper functions

### 1.2 Testing Anti-Patterns to Avoid

**Don't Mock What You Don't Own**
- ❌ Mocking external LLM APIs (OpenAI, Anthropic, OpenRouter)
- ✅ Use VCR.py for recording real API interactions
- ✅ Create fixture responses for repeatable tests

**Don't Test Implementation Details**
- ❌ Testing internal agent state transitions
- ✅ Test observable outputs and side effects
- ✅ Validate data contracts (Pydantic models)

**Don't Aim for 100% Coverage Everywhere**
- ❌ Writing tests for simple property accessors
- ✅ Focus on business-critical logic paths
- ✅ Use coverage gaps to guide risk assessment

---

## 2. TDD Applicability Matrix

### 2.1 When to Use TDD (Test-First)

| Component | TDD Approach | Rationale |
|-----------|-------------|-----------|
| **Multi-Agent Synthesis Logic** | ✅ **REQUIRED** | Complex scoring algorithms with deterministic math |
| **Pipeline Format Conversion** | ✅ **REQUIRED** | Data transformation logic must preserve structure |
| **Cost Calculation** | ✅ **REQUIRED** | Financial accuracy is critical, bugs are expensive |
| **Simplicity Processor** | ✅ **REQUIRED** | Business rule enforcement (3-function limit) |
| **Pydantic Model Validation** | ✅ **REQUIRED** | Data contracts define API boundaries |
| **Database Persistence** | ✅ **REQUIRED** | Schema migrations must be bidirectional |
| **Consensus Scoring Weights** | ✅ **RECOMMENDED** | Math-heavy logic benefits from TDD |
| **Trust Level Assignment** | ✅ **RECOMMENDED** | Business logic with clear rules |
| **Subreddit Multipliers** | ✅ **RECOMMENDED** | Domain-specific scoring rules |

**TDD Workflow for These Components:**
```python
# 1. Write failing test first
def test_consensus_synthesis_calculates_market_demand():
    """Market demand = WTP score (60%) + Segment score (40%)"""
    # Arrange
    wtp_score = 80.0
    segment_score = 60.0

    # Act
    result = synthesize_market_demand(wtp_score, segment_score)

    # Assert
    expected = (80.0 * 0.6) + (60.0 * 0.4)  # 72.0
    assert result == expected

# 2. Implement minimal code to pass
def synthesize_market_demand(wtp_score: float, segment_score: float) -> float:
    return (wtp_score * 0.6) + (segment_score * 0.4)

# 3. Refactor with confidence
```

### 2.2 When NOT to Use TDD (Test-After)

| Component | Testing Approach | Rationale |
|-----------|-----------------|-----------|
| **LLM Agent Prompts** | ❌ **NO TDD** | Emergent behavior requires experimentation |
| **Agno Team Orchestration** | ❌ **NO TDD** | Sequential vs parallel mode needs profiling |
| **Agent Instructions** | ❌ **NO TDD** | Iterative prompt engineering |
| **Jina API Integration** | ❌ **NO TDD** | External service behavior exploration |
| **Market Research Queries** | ❌ **NO TDD** | Search quality requires manual validation |
| **OpenRouter Model Selection** | ❌ **NO TDD** | Performance testing guides decisions |
| **AgentOps Event Tracking** | ❌ **NO TDD** | Observability patterns emerge from usage |
| **Caching Strategies** | ❌ **NO TDD** | Cache hit rates discovered through profiling |

**Test-After Workflow for These Components:**
```python
# 1. Implement experimental version
@agent(name="Market Research Analyst")
class MarketResearchAgent(Agent):
    def __init__(self, model: str):
        super().__init__(
            name="Market Research Analyst",
            role="Validate opportunities with real market data",
            instructions="""
            Search for competitor pricing data using Jina API.
            Extract structured pricing tiers, models, and target markets.
            Return evidence with source URLs.
            """  # ← Requires iteration to tune
        )

# 2. Run manual tests with real data
result = agent.run({"app_concept": "Project management tool"})
print(result)  # Does it find relevant competitors?

# 3. Write regression tests after validation
def test_market_research_agent_returns_structured_evidence():
    """Regression: Agent must return ValidationEvidence format"""
    result = agent.run(test_input)

    assert "competitor_pricing" in result
    assert "validation_score" in result
    assert 0 <= result["validation_score"] <= 100
```

### 2.3 Hybrid TDD Approach

**Use TDD + Test-After for Integration Points:**

```python
# TDD for data contract
def test_market_research_agent_output_converts_to_validation_evidence():
    """Agent output must convert to ValidationEvidence Pydantic model"""
    raw_output = {
        "competitor_pricing": [...],
        "market_size": {...},
        "validation_score": 85.0
    }

    # This test drives Pydantic model design (TDD)
    evidence = ValidationEvidence(**raw_output)
    assert isinstance(evidence, ValidationEvidence)
    assert evidence.validation_score == 85.0

# Test-after for agent behavior
def test_market_research_agent_real_competitor_search():
    """Integration: Agent finds real competitors for project management"""
    agent = MarketResearchAgent(model="anthropic/claude-haiku-4.5")

    # Run real search (test-after, validates actual behavior)
    result = agent.run({
        "app_concept": "Project management tool for remote teams",
        "target_market": "B2B SaaS"
    })

    # Regression assertions (prevent quality degradation)
    assert len(result["competitor_pricing"]) >= 3
    assert any("Asana" in p["company"] for p in result["competitor_pricing"])
```

---

## 3. Phase-by-Phase Testing Approach

### Phase 1: Core Agno Integration

**Goal**: Validate multi-agent analysis produces correct Pipeline v3 outputs

#### Testing Priorities

1. **Unit Tests for Synthesis Logic (TDD Required)**
   - Consensus scoring calculations
   - Weighted averaging algorithms
   - Confidence threshold enforcement

2. **Integration Tests for Agent Orchestration (Test-After)**
   - 4-agent team coordination
   - Sequential vs parallel mode validation
   - Error handling and fallbacks

3. **Contract Tests for Format Conversion (TDD Required)**
   - AgnoSynthesis → AnalysisResult transformation
   - Pydantic model validation
   - Core functions enforcement (max 3)

#### Example Test Suite

```python
# tests/transform/test_agno_analyzer.py

# ========================================
# UNIT TESTS (TDD - Write First)
# ========================================

def test_synthesize_market_demand_weighted_average():
    """Market demand = WTP (60%) + Segment (40%)"""
    synthesis = AgnoSynthesis(
        wtp_score=80.0,
        segment_audience_size=60.0
    )

    result = synthesis.calculate_market_demand()

    assert result == (80.0 * 0.6) + (60.0 * 0.4)  # 72.0


def test_synthesize_pain_intensity_multi_factor():
    """Pain = WTP (50%) + Behavior (30%) + Price (20%)"""
    synthesis = AgnoSynthesis(
        wtp_pain_score=90.0,
        behavior_friction_score=70.0,
        price_urgency_score=60.0
    )

    result = synthesis.calculate_pain_intensity()

    expected = (90.0 * 0.5) + (70.0 * 0.3) + (60.0 * 0.2)
    assert result == expected


def test_convert_to_pipeline_format_preserves_submission_id():
    """AnalysisResult must maintain submission linkage"""
    submission = RedditSubmission(id="sub_123")
    synthesis = create_test_synthesis()

    result = converter.convert_to_pipeline_format(synthesis, submission)

    assert result.submission_id == "sub_123"


def test_convert_enforces_max_3_core_functions():
    """Simplicity processor must limit to 3 functions"""
    synthesis = AgnoSynthesis(
        core_functions=["Fn1", "Fn2", "Fn3", "Fn4", "Fn5"]  # Too many
    )

    result = converter.convert_to_pipeline_format(synthesis)

    assert len(result.app_idea.core_functions) == 3


# ========================================
# INTEGRATION TESTS (Test-After)
# ========================================

@pytest.mark.integration
def test_agno_analyzer_full_workflow():
    """Integration: Complete analysis workflow with real agents"""
    analyzer = AgnoOpportunityAnalyzer(
        model="anthropic/claude-haiku-4.5",
        enable_agentops=False  # Disable for testing
    )
    submission = load_test_submission("productivity_tool.json")

    result = analyzer.analyze_submission(submission)

    # Validate output contract
    assert isinstance(result, AnalysisResult)
    assert result.final_score >= 0 and result.final_score <= 100
    assert result.confidence_score >= 0 and result.confidence_score <= 100

    # Validate business rules
    assert len(result.app_idea.core_functions) <= 3
    assert result.trust_level in ["LOW", "MEDIUM", "HIGH"]


@pytest.mark.integration
def test_agno_team_parallel_execution():
    """Integration: Parallel agent mode completes successfully"""
    analyzer = AgnoOpportunityAnalyzer(orchestration_mode="parallel")
    submission = create_test_submission()

    start_time = time.time()
    result = analyzer.analyze_submission(submission)
    duration = time.time() - start_time

    # Parallel should be faster than sequential
    assert duration < 5.0  # Target: <5s for parallel mode
    assert isinstance(result, AnalysisResult)
```

### Phase 2: Factory Integration

**Goal**: Ensure analyzer factory supports Agno with backward compatibility

#### Testing Priorities

1. **Unit Tests for Factory Creation (TDD)**
   - Factory instantiates correct analyzer type
   - Configuration passed to analyzer
   - Environment variable handling

2. **Integration Tests for Analyzer Switching (Test-After)**
   - Factory supports all analyzer types
   - No breaking changes to existing code
   - Graceful fallback handling

```python
# tests/transform/test_analyzer_factory.py

def test_factory_creates_agno_analyzer():
    """Factory returns AgnoOpportunityAnalyzer for 'agno' type"""
    factory = AgnoAnalyzerFactory()

    analyzer = factory.create_analyzer()

    assert isinstance(analyzer, AgnoOpportunityAnalyzer)
    assert len(analyzer.team.agents) == 5  # 4 core + 1 market research


def test_factory_backward_compatibility_litellm():
    """Existing 'litellm' factory still works"""
    factory = ProductionAnalyzerFactory()

    analyzer = factory.create_analyzer()

    assert isinstance(analyzer, LiteLLMAnalyzer)
    # No breaking changes


@pytest.mark.integration
def test_get_analyzer_all_types():
    """Integration: get_analyzer() supports all types"""
    types = ["simple", "litellm", "agno", "hybrid"]

    for analyzer_type in types:
        analyzer = get_analyzer(analyzer_type)
        assert analyzer is not None

        # All analyzers share common interface
        assert hasattr(analyzer, "analyze_submission")
        assert hasattr(analyzer, "analyze_batch_with_costs")
```

### Phase 3: Jina Market Research Integration

**Goal**: Validate real market data enrichment with Jina API

#### Testing Priorities

1. **Unit Tests for Data Models (TDD)**
   - ValidationEvidence Pydantic model
   - CompetitorPricing structure
   - MarketSizeData format

2. **Integration Tests with VCR.py (Test-After)**
   - Record real Jina API responses
   - Test search query construction
   - Test URL extraction logic

3. **Contract Tests for LLM Extraction (TDD)**
   - Pricing data extraction schema
   - Market size parsing rules
   - Confidence scoring thresholds

```python
# tests/agents/test_market_research_agent.py

# ========================================
# UNIT TESTS (TDD - Pydantic Models)
# ========================================

def test_validation_evidence_model_required_fields():
    """ValidationEvidence requires competitor_pricing and scores"""
    with pytest.raises(ValidationError):
        ValidationEvidence(
            # Missing required fields
            competitor_pricing=[],
            validation_score=None  # Should fail
        )


def test_competitor_pricing_model_structure():
    """CompetitorPricing has all required fields"""
    pricing = CompetitorPricing(
        company="Asana",
        pricing_model="subscription",
        tiers=["Free", "Premium", "Business"],
        target_market="B2B",
        source_url="https://asana.com/pricing",
        confidence=0.95
    )

    assert pricing.company == "Asana"
    assert "subscription" in pricing.pricing_model


# ========================================
# INTEGRATION TESTS (VCR.py for API Mocking)
# ========================================

@pytest.mark.vcr()  # Records HTTP interactions
def test_market_research_agent_real_competitor_search():
    """Integration: Agent searches for project management competitors"""
    agent = MarketResearchAgent(
        model="anthropic/claude-haiku-4.5",
        market_validator=MarketDataValidator()
    )

    result = agent.run({
        "app_concept": "Project management tool",
        "target_market": "B2B SaaS"
    })

    # VCR replays recorded Jina responses
    assert len(result["competitor_pricing"]) >= 3
    assert result["validation_score"] > 0
    assert len(result["evidence_urls"]) > 0


@pytest.mark.vcr()
def test_jina_api_pricing_extraction():
    """Integration: Jina extracts pricing from competitor page"""
    jina_client = JinaHybridClient()

    response = jina_client.read_url("https://asana.com/pricing")

    # LLM extracts structured data
    pricing = extract_pricing_with_llm(response.content)

    assert pricing.company == "Asana"
    assert len(pricing.tiers) >= 3
    assert pricing.confidence >= 0.8
```

### Phase 4: Database Persistence

**Goal**: Ensure Agno results persist correctly with new schema columns

#### Testing Priorities

1. **Migration Tests (TDD)**
   - Forward migration adds columns
   - Backward migration removes columns
   - Data integrity preserved

2. **ORM Tests (TDD)**
   - SQLAlchemy models updated
   - Pydantic → ORM mapping correct
   - Query performance acceptable

```python
# tests/database/test_agno_schema_migration.py

def test_migration_adds_agno_columns():
    """Forward migration adds Agno-specific columns"""
    # Run migration
    run_migration("add_agno_columns")

    # Verify columns exist
    inspector = inspect(engine)
    columns = [c["name"] for c in inspector.get_columns("opportunities")]

    assert "agno_wtp_score" in columns
    assert "agno_segment_confidence" in columns
    assert "agno_consensus_confidence" in columns


def test_agno_result_persists_to_database():
    """Integration: AnalysisResult with Agno data saves correctly"""
    result = AnalysisResult(
        submission_id="sub_123",
        app_idea=AppIdea(...),
        final_score=85.0,
        agno_wtp_score=90.0,  # New field
        agno_consensus_confidence=0.92  # New field
    )

    # Save to database
    save_result(result)

    # Retrieve and verify
    retrieved = db.query(Opportunity).filter_by(submission_id="sub_123").first()
    assert retrieved.agno_wtp_score == 90.0
    assert retrieved.agno_consensus_confidence == 0.92
```

### Phase 5: Production Testing & Optimization

**Goal**: Validate production readiness with A/B comparison

#### Testing Priorities

1. **Performance Tests (Test-After)**
   - Latency benchmarks
   - Throughput measurements
   - Resource utilization

2. **Quality Comparison Tests (Test-After)**
   - Agno vs LiteLLM accuracy
   - False positive rates
   - Market intelligence depth

```python
# tests/performance/test_agno_benchmarks.py

@pytest.mark.benchmark
def test_agno_analyzer_latency_p95(benchmark):
    """Benchmark: Agno analysis completes in <5s (P95)"""
    analyzer = AgnoOpportunityAnalyzer(orchestration_mode="parallel")
    submission = create_test_submission()

    result = benchmark(analyzer.analyze_submission, submission)

    # Target: P95 latency <5s for parallel mode
    assert benchmark.stats["mean"] < 5.0


@pytest.mark.benchmark
def test_agno_batch_throughput(benchmark):
    """Benchmark: Process 100 submissions/hour"""
    analyzer = AgnoOpportunityAnalyzer()
    submissions = create_test_batch(100)

    start = time.time()
    results = analyzer.analyze_batch(submissions)
    duration = time.time() - start

    throughput = len(submissions) / (duration / 3600)  # per hour
    assert throughput >= 100  # Target: 100+ submissions/hour


@pytest.mark.comparison
def test_agno_vs_litellm_quality():
    """Comparison: Agno reduces false positives by 60%"""
    # Load ground truth dataset (manually validated opportunities)
    ground_truth = load_ground_truth_dataset()

    # Run both analyzers
    agno_results = run_analyzer("agno", ground_truth)
    litellm_results = run_analyzer("litellm", ground_truth)

    # Calculate false positive rates
    agno_fp_rate = calculate_false_positive_rate(agno_results, ground_truth)
    litellm_fp_rate = calculate_false_positive_rate(litellm_results, ground_truth)

    # Agno should reduce false positives
    improvement = (litellm_fp_rate - agno_fp_rate) / litellm_fp_rate
    assert improvement >= 0.60  # Target: 60% reduction
```

---

## 4. Coverage Targets by Component

### 4.1 Critical Path Coverage: 100%

**Components requiring complete coverage:**

| Component | Target | Rationale |
|-----------|--------|-----------|
| Multi-Agent Synthesis Logic | 100% | Financial calculations, no errors tolerated |
| Cost Tracking & Calculation | 100% | Budget accuracy critical |
| Pipeline Format Conversion | 100% | Data integrity for downstream consumers |
| Simplicity Processor | 100% | Business rule enforcement |
| Database Migrations | 100% | Schema changes must be reversible |

**How to Measure:**
```bash
# Run coverage for critical components only
pytest \
  --cov=pipeline-v3/transform/agno_synthesis.py \
  --cov=pipeline-v3/monitoring/cost_tracking.py \
  --cov=pipeline-v3/transform/format_converter.py \
  --cov-report=html \
  --cov-fail-under=100
```

### 4.2 High-Value Coverage: 90%+

**Components requiring high coverage:**

| Component | Target | Rationale |
|-----------|--------|-----------|
| AgnoOpportunityAnalyzer | 90% | Main integration point |
| AnalyzerFactory | 90% | Critical dependency injection |
| Pydantic Models | 90% | Data contract validation |
| Market Research Agent | 90% | High business value |

### 4.3 Standard Coverage: 80%+

**Components with standard coverage:**

| Component | Target | Rationale |
|-----------|--------|-----------|
| Agent Implementations | 80% | Prompt engineering requires flexibility |
| Jina API Integration | 80% | External service, use VCR.py |
| AgentOps Tracking | 80% | Observability, not business logic |
| Configuration Loading | 80% | Simple validation logic |

### 4.4 Minimal Coverage: 50%+

**Components with lower coverage needs:**

| Component | Target | Rationale |
|-----------|--------|-----------|
| Agent Instructions | 50% | Iterative prompt tuning |
| Logging Utilities | 50% | Simple wrappers |
| CLI Entry Points | 50% | Smoke tests sufficient |

### 4.5 Coverage Exclusions

**Don't measure coverage for:**
- `__repr__` and `__str__` methods
- Type stubs and protocol definitions
- Deprecation warnings
- Debug logging statements

**Configure in `.coveragerc`:**
```ini
[run]
omit =
    */tests/*
    */migrations/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    def __str__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
```

---

## 5. Testing Workflow Examples

### 5.1 TDD Workflow: Multi-Agent Synthesis

**Step 1: Write failing test**
```python
def test_consensus_confidence_calculation():
    """Confidence = standard deviation of agent scores (inverted)"""
    # Arrange
    agent_scores = {
        "wtp": 85.0,
        "segment": 82.0,
        "price": 88.0,
        "behavior": 84.0
    }

    # Act
    confidence = calculate_consensus_confidence(agent_scores)

    # Assert
    # Low stddev = high confidence
    # stddev ≈ 2.38 → confidence ≈ 97.6%
    assert 95.0 <= confidence <= 100.0
```

**Step 2: Run test (should fail)**
```bash
$ pytest tests/transform/test_agno_synthesis.py::test_consensus_confidence_calculation

FAILED - NameError: name 'calculate_consensus_confidence' is not defined
```

**Step 3: Implement minimal solution**
```python
import statistics

def calculate_consensus_confidence(agent_scores: dict) -> float:
    """
    Calculate consensus confidence from agent score variance

    Low variance (high agreement) = high confidence
    High variance (disagreement) = low confidence
    """
    scores = list(agent_scores.values())
    stddev = statistics.stdev(scores)

    # Convert stddev to confidence percentage
    # stddev range [0, 50] → confidence range [100, 0]
    confidence = max(0, 100 - (stddev * 2))

    return confidence
```

**Step 4: Verify test passes**
```bash
$ pytest tests/transform/test_agno_synthesis.py::test_consensus_confidence_calculation

PASSED ✓
```

**Step 5: Add edge case tests**
```python
def test_consensus_confidence_perfect_agreement():
    """Perfect agreement (no variance) = 100% confidence"""
    agent_scores = {"wtp": 80.0, "segment": 80.0, "price": 80.0, "behavior": 80.0}

    confidence = calculate_consensus_confidence(agent_scores)

    assert confidence == 100.0


def test_consensus_confidence_high_disagreement():
    """High disagreement (high variance) = low confidence"""
    agent_scores = {"wtp": 90.0, "segment": 30.0, "price": 95.0, "behavior": 20.0}

    confidence = calculate_consensus_confidence(agent_scores)

    assert confidence < 50.0  # Low confidence due to disagreement
```

### 5.2 Test-After Workflow: Market Research Agent

**Step 1: Implement exploratory version**
```python
@agent(name="Market Research Analyst")
class MarketResearchAgent(Agent):
    def __init__(self, model: str):
        super().__init__(
            name="Market Research Analyst",
            role="Validate opportunities with real market data",
            instructions="""
            You are a market research expert using Jina API.

            Search for competitor pricing data for the given app concept.
            Extract structured pricing tiers, models, and target markets.

            Return JSON with competitor_pricing list and validation_score.
            """
        )
        self.jina_client = JinaHybridClient()
```

**Step 2: Run manual tests**
```python
# Manual testing script
agent = MarketResearchAgent(model="anthropic/claude-haiku-4.5")

result = agent.run({
    "app_concept": "Project management tool for remote teams",
    "target_market": "B2B SaaS"
})

print(json.dumps(result, indent=2))
```

**Step 3: Validate output structure**
```json
{
  "competitor_pricing": [
    {
      "company": "Asana",
      "pricing_model": "subscription",
      "tiers": ["Free", "Premium", "Business"],
      "target_market": "B2B"
    }
  ],
  "validation_score": 85.0
}
```

**Step 4: Write regression tests**
```python
@pytest.mark.vcr()  # Record real API interaction
def test_market_research_agent_finds_competitors():
    """Regression: Agent finds at least 3 competitors"""
    agent = MarketResearchAgent(model="anthropic/claude-haiku-4.5")

    result = agent.run({
        "app_concept": "Project management tool",
        "target_market": "B2B SaaS"
    })

    # Regression assertions
    assert len(result["competitor_pricing"]) >= 3
    assert result["validation_score"] > 0

    # Data quality checks
    for competitor in result["competitor_pricing"]:
        assert "company" in competitor
        assert "pricing_model" in competitor
        assert competitor["confidence"] >= 0.5
```

**Step 5: Add contract tests**
```python
def test_market_research_output_converts_to_pydantic():
    """Contract: Agent output must map to ValidationEvidence"""
    # Load recorded VCR response
    agent = MarketResearchAgent(model="test-model")
    result = agent.run(test_input)

    # Pydantic validation (TDD for data contract)
    evidence = ValidationEvidence(**result)

    assert isinstance(evidence, ValidationEvidence)
    assert len(evidence.competitor_pricing) > 0
```

---

## 6. Unit Testing Strategy

### 6.1 Test Organization

```
tests/
├── transform/
│   ├── test_agno_analyzer.py          # AgnoOpportunityAnalyzer tests
│   ├── test_agno_synthesis.py         # Consensus logic tests
│   ├── test_format_converter.py       # Pipeline format conversion
│   └── test_analyzer_factory.py       # Factory pattern tests
│
├── agents/
│   ├── test_wtp_agent.py              # WTP Agent unit tests
│   ├── test_segment_agent.py          # Market Segment Agent tests
│   ├── test_price_agent.py            # Price Point Agent tests
│   ├── test_behavior_agent.py         # Payment Behavior Agent tests
│   └── test_market_research_agent.py  # Market Research Agent tests
│
├── monitoring/
│   ├── test_cost_tracking.py          # Cost calculation tests
│   └── test_agno_metrics.py           # Agno-specific metrics
│
└── database/
    ├── test_agno_schema.py             # Schema migration tests
    └── test_agno_persistence.py        # ORM persistence tests
```

### 6.2 Unit Test Examples

#### Multi-Agent Synthesis Tests

```python
# tests/transform/test_agno_synthesis.py

class TestMarketDemandSynthesis:
    """Test market demand calculation from multiple agents"""

    def test_market_demand_weighted_average(self):
        """Market demand = WTP (60%) + Segment (40%)"""
        synthesizer = AgnoSynthesizer()

        result = synthesizer.calculate_market_demand(
            wtp_score=80.0,
            segment_score=60.0
        )

        expected = (80.0 * 0.6) + (60.0 * 0.4)  # 72.0
        assert result == expected

    def test_market_demand_applies_subreddit_multiplier(self):
        """High purchasing power subreddits get 2x multiplier"""
        synthesizer = AgnoSynthesizer()

        # /r/entrepreneur has 2.0x multiplier
        result = synthesizer.calculate_market_demand(
            wtp_score=80.0,
            segment_score=60.0,
            subreddit="entrepreneur"
        )

        base = (80.0 * 0.6) + (60.0 * 0.4)  # 72.0
        expected = base * 2.0  # 144.0 (capped at 100)
        assert result == min(expected, 100.0)

    def test_market_demand_caps_at_100(self):
        """Market demand never exceeds 100"""
        synthesizer = AgnoSynthesizer()

        result = synthesizer.calculate_market_demand(
            wtp_score=100.0,
            segment_score=100.0,
            subreddit="entrepreneur"  # 2x multiplier
        )

        assert result == 100.0


class TestPainIntensitySynthesis:
    """Test pain intensity calculation from multiple factors"""

    def test_pain_intensity_multi_factor_weighted(self):
        """Pain = WTP (50%) + Behavior (30%) + Price (20%)"""
        synthesizer = AgnoSynthesizer()

        result = synthesizer.calculate_pain_intensity(
            wtp_pain_score=90.0,
            behavior_friction_score=70.0,
            price_urgency_score=60.0
        )

        expected = (90.0 * 0.5) + (70.0 * 0.3) + (60.0 * 0.2)
        assert result == expected


class TestConsensuConfidence:
    """Test consensus confidence from agent agreement"""

    def test_consensus_perfect_agreement(self):
        """Perfect agreement = 100% confidence"""
        agent_scores = {
            "wtp": 80.0,
            "segment": 80.0,
            "price": 80.0,
            "behavior": 80.0
        }

        confidence = calculate_consensus_confidence(agent_scores)

        assert confidence == 100.0

    def test_consensus_high_variance_low_confidence(self):
        """High variance = low confidence"""
        agent_scores = {
            "wtp": 90.0,
            "segment": 30.0,
            "price": 95.0,
            "behavior": 25.0
        }

        confidence = calculate_consensus_confidence(agent_scores)

        assert confidence < 50.0
```

#### Format Conversion Tests

```python
# tests/transform/test_format_converter.py

class TestAgnoToAnalysisResultConversion:
    """Test conversion from Agno synthesis to Pipeline v3 format"""

    def test_preserves_submission_id(self):
        """AnalysisResult maintains submission linkage"""
        submission = RedditSubmission(id="sub_123")
        synthesis = create_test_synthesis()

        result = convert_to_analysis_result(synthesis, submission)

        assert result.submission_id == "sub_123"

    def test_enforces_max_3_core_functions(self):
        """Simplicity processor limits to 3 functions"""
        synthesis = AgnoSynthesis(
            core_functions=["Fn1", "Fn2", "Fn3", "Fn4", "Fn5"]
        )

        result = convert_to_analysis_result(synthesis)

        assert len(result.app_idea.core_functions) == 3

    def test_calculates_final_score_from_metrics(self):
        """Final score = market (40%) + pain (30%) + monetization (30%)"""
        synthesis = AgnoSynthesis(
            market_demand=80.0,
            pain_intensity=70.0,
            monetization_potential=60.0
        )

        result = convert_to_analysis_result(synthesis)

        expected = (80.0 * 0.4) + (70.0 * 0.3) + (60.0 * 0.3)
        assert result.final_score == expected

    def test_assigns_trust_level_based_on_confidence(self):
        """Trust level: HIGH (>80%), MEDIUM (60-80%), LOW (<60%)"""
        # High confidence
        synthesis_high = AgnoSynthesis(confidence_score=85.0)
        result_high = convert_to_analysis_result(synthesis_high)
        assert result_high.trust_level == "HIGH"

        # Medium confidence
        synthesis_med = AgnoSynthesis(confidence_score=70.0)
        result_med = convert_to_analysis_result(synthesis_med)
        assert result_med.trust_level == "MEDIUM"

        # Low confidence
        synthesis_low = AgnoSynthesis(confidence_score=50.0)
        result_low = convert_to_analysis_result(synthesis_low)
        assert result_low.trust_level == "LOW"
```

#### Cost Tracking Tests

```python
# tests/monitoring/test_cost_tracking.py

class TestCostCalculation:
    """Test LLM cost calculation for Agno agents"""

    def test_calculates_per_agent_costs(self):
        """Track individual agent costs separately"""
        tracker = CostTracker()

        tracker.record_agent_call(
            agent="WTP Analyst",
            tokens_in=500,
            tokens_out=200,
            model="anthropic/claude-haiku-4.5"
        )

        cost = tracker.get_agent_cost("WTP Analyst")

        # Claude Haiku: $0.0008/1K input, $0.004/1K output
        expected = (500 * 0.0008 / 1000) + (200 * 0.004 / 1000)
        assert cost == expected

    def test_aggregates_total_analysis_cost(self):
        """Total cost = sum of all agent costs"""
        tracker = CostTracker()

        # Simulate 4 agent calls
        for agent in ["WTP", "Segment", "Price", "Behavior"]:
            tracker.record_agent_call(
                agent=agent,
                tokens_in=500,
                tokens_out=200,
                model="anthropic/claude-haiku-4.5"
            )

        total = tracker.get_total_cost()

        # 4 agents × cost per agent
        single_cost = (500 * 0.0008 / 1000) + (200 * 0.004 / 1000)
        expected = single_cost * 4
        assert total == expected

    def test_batch_cost_summary(self):
        """Batch analysis provides cost summary"""
        tracker = CostTracker()

        # Analyze 10 submissions
        for _ in range(10):
            tracker.record_analysis(
                agents_used=4,
                tokens_per_agent=700,
                model="anthropic/claude-haiku-4.5"
            )

        summary = tracker.get_summary()

        assert summary.num_analyses == 10
        assert summary.total_agents_called == 40
        assert summary.avg_cost_per_analysis > 0
```

---

## 7. Integration Testing Strategy

### 7.1 Integration Test Scope

**What to Test:**
- Full agent orchestration workflows
- External API integrations (Jina, LLMs)
- Database persistence end-to-end
- Factory pattern analyzer switching
- AgentOps event tracking

**What NOT to Test in Integration:**
- Individual function logic (unit tests)
- Pydantic model validation (unit tests)
- Math calculations (unit tests)

### 7.2 Integration Test Examples

#### Full Pipeline Integration

```python
# tests/integration/test_agno_pipeline.py

@pytest.mark.integration
class TestAgnoPipelineIntegration:
    """Test complete Agno analysis pipeline"""

    def test_end_to_end_analysis_workflow(self):
        """Integration: Extract → Agno Analysis → Load"""
        # Arrange
        analyzer = get_analyzer("agno")
        submission = RedditSubmission(
            id="sub_123",
            title="I need a productivity tool",
            text="Looking for something to manage tasks...",
            subreddit="productivity"
        )

        # Act
        result = analyzer.analyze_submission(submission)

        # Assert: Valid analysis result
        assert isinstance(result, AnalysisResult)
        assert result.submission_id == "sub_123"
        assert result.final_score >= 0

        # Assert: Agno-specific data populated
        assert result.agno_wtp_score is not None
        assert result.agno_consensus_confidence is not None

        # Assert: Simplicity enforced
        assert len(result.app_idea.core_functions) <= 3

    def test_database_persistence(self, db_session):
        """Integration: AnalysisResult saves to database"""
        # Arrange
        analyzer = get_analyzer("agno")
        submission = create_test_submission()

        # Act: Analyze and save
        result = analyzer.analyze_submission(submission)
        save_analysis_result(result, db_session)
        db_session.commit()

        # Assert: Retrieve from database
        retrieved = db_session.query(Opportunity).filter_by(
            submission_id=submission.id
        ).first()

        assert retrieved is not None
        assert retrieved.final_score == result.final_score
        assert retrieved.agno_wtp_score == result.agno_wtp_score

    def test_agentops_tracking_enabled(self):
        """Integration: AgentOps events tracked"""
        # Arrange
        analyzer = get_analyzer("agno", enable_agentops=True)
        submission = create_test_submission()

        # Act
        with patch("agentops.record") as mock_record:
            result = analyzer.analyze_submission(submission)

        # Assert: AgentOps events fired
        assert mock_record.call_count >= 4  # One per agent

        # Verify event types
        calls = [call[0][0] for call in mock_record.call_args_list]
        assert any("WTP" in str(call) for call in calls)
```

#### Factory Integration Tests

```python
# tests/integration/test_analyzer_factory_integration.py

@pytest.mark.integration
class TestAnalyzerFactoryIntegration:
    """Test analyzer factory creates functional analyzers"""

    def test_all_analyzer_types_work(self):
        """Integration: All factory types produce working analyzers"""
        types = ["simple", "litellm", "agno", "hybrid"]
        submission = create_test_submission()

        for analyzer_type in types:
            analyzer = get_analyzer(analyzer_type)

            # Should complete without errors
            result = analyzer.analyze_submission(submission)

            assert isinstance(result, AnalysisResult)
            assert result.final_score >= 0

    def test_factory_respects_configuration(self):
        """Integration: Factory uses environment configuration"""
        # Arrange: Set custom model
        with patch.dict(os.environ, {"MONETIZATION_LLM_MODEL": "custom-model"}):
            factory = AgnoAnalyzerFactory()
            analyzer = factory.create_analyzer()

        # Assert: Analyzer uses configured model
        assert analyzer.model == "custom-model"

    def test_hybrid_fallback_mechanism(self):
        """Integration: Hybrid analyzer falls back to LiteLLM on error"""
        analyzer = get_analyzer("hybrid")
        submission = create_test_submission()

        # Simulate Agno failure
        with patch.object(AgnoOpportunityAnalyzer, "analyze_submission", side_effect=Exception("Agno failed")):
            result = analyzer.analyze_submission(submission)

        # Should still return result via LiteLLM fallback
        assert isinstance(result, AnalysisResult)
```

#### Jina API Integration Tests (with VCR.py)

```python
# tests/integration/test_jina_integration.py

@pytest.mark.integration
@pytest.mark.vcr()
class TestJinaMarketResearchIntegration:
    """Test Jina API integration with VCR recording"""

    def test_market_research_finds_competitors(self):
        """Integration: MarketResearchAgent finds real competitors"""
        agent = MarketResearchAgent(
            model="anthropic/claude-haiku-4.5",
            market_validator=MarketDataValidator()
        )

        result = agent.run({
            "app_concept": "Project management tool for remote teams",
            "target_market": "B2B SaaS"
        })

        # VCR replays recorded Jina API calls
        assert len(result["competitor_pricing"]) >= 3
        assert any("Asana" in p["company"] for p in result["competitor_pricing"])
        assert result["validation_score"] > 0

    def test_jina_search_constructs_relevant_queries(self):
        """Integration: Jina search uses app concept in queries"""
        agent = MarketResearchAgent(model="test-model")

        result = agent.run({
            "app_concept": "Email automation tool",
            "target_market": "SMB"
        })

        # Check search queries used
        queries = result["search_queries_used"]
        assert any("email automation" in q.lower() for q in queries)
        assert any("pricing" in q.lower() for q in queries)

    def test_jina_extraction_produces_structured_data(self):
        """Integration: Jina extraction returns valid Pydantic models"""
        jina_client = JinaHybridClient()

        # VCR: Replay recorded extraction
        response = jina_client.read_url("https://asana.com/pricing")

        # LLM extraction
        pricing = extract_pricing_with_llm(response.content)

        # Pydantic validation
        assert isinstance(pricing, CompetitorPricing)
        assert pricing.company == "Asana"
        assert len(pricing.tiers) >= 3
        assert pricing.confidence >= 0.8
```

### 7.3 VCR.py Configuration for API Recording

```python
# tests/conftest.py

import pytest
import vcr

@pytest.fixture(scope="module")
def vcr_config():
    """Configure VCR for recording API interactions"""
    return {
        "filter_headers": ["authorization", "x-api-key"],  # Redact sensitive headers
        "record_mode": "once",  # Record once, then replay
        "match_on": ["uri", "method", "body"],
        "cassette_library_dir": "tests/fixtures/vcr_cassettes"
    }

@pytest.fixture
def vcr_cassette(request, vcr_config):
    """Provide VCR cassette for test"""
    with vcr.VCR(**vcr_config).use_cassette(f"{request.node.name}.yaml"):
        yield
```

**Usage in tests:**
```python
@pytest.mark.vcr()  # Automatically uses vcr_cassette fixture
def test_jina_api_call():
    # First run: Records real API call to cassette
    # Subsequent runs: Replays from cassette (no real API call)
    result = jina_client.search_web("competitor pricing")
    assert len(result) > 0
```

---

## 8. Testing Tools and Infrastructure

### 8.1 Testing Dependencies

```toml
# pyproject.toml or requirements-test.txt

[tool.poetry.group.test.dependencies]
pytest = "^8.0.0"
pytest-cov = "^5.0.0"
pytest-vcr = "^1.0.2"          # Record HTTP interactions
pytest-benchmark = "^4.0.0"     # Performance benchmarking
pytest-xdist = "^3.5.0"         # Parallel test execution
pytest-timeout = "^2.2.0"       # Timeout protection
pytest-mock = "^3.12.0"         # Mocking utilities
hypothesis = "^6.96.0"          # Property-based testing
faker = "^22.0.0"               # Test data generation
freezegun = "^1.4.0"            # Time mocking
vcr-py = "^6.0.0"               # HTTP recording library
```

### 8.2 Pytest Configuration

```ini
# pytest.ini

[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Markers
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (external APIs, database)
    vcr: Tests using VCR for HTTP recording
    benchmark: Performance benchmark tests
    comparison: A/B comparison tests (Agno vs LiteLLM)
    slow: Slow-running tests (>5s)

# Coverage
addopts =
    --strict-markers
    --tb=short
    --cov=pipeline-v3
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    -ra
    --maxfail=3

# Timeouts
timeout = 300
timeout_method = thread

# Parallel execution
#-n auto  # Uncomment for parallel execution
```

### 8.3 Coverage Configuration

```.coveragerc
# .coveragerc

[run]
source = pipeline-v3
omit =
    */tests/*
    */migrations/*
    */__pycache__/*
    */venv/*
    */site-packages/*

[report]
precision = 2
exclude_lines =
    pragma: no cover
    def __repr__
    def __str__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
    @overload

[html]
directory = htmlcov
```

### 8.4 Test Data Fixtures

```python
# tests/fixtures/reddit_submissions.py

@pytest.fixture
def sample_submission():
    """Sample Reddit submission for testing"""
    return RedditSubmission(
        id="sub_123",
        title="I need a productivity tool for remote teams",
        text="""
        I'm looking for something that helps manage tasks,
        track time, and collaborate with my remote team.
        Budget is around $50/month. Any recommendations?
        """,
        subreddit="productivity",
        author="test_user",
        created_utc=datetime(2025, 12, 1),
        score=42,
        num_comments=15
    )

@pytest.fixture
def batch_submissions():
    """Batch of test submissions"""
    return [
        create_test_submission(subreddit="entrepreneur", score=100),
        create_test_submission(subreddit="SaaS", score=75),
        create_test_submission(subreddit="productivity", score=50),
    ]

@pytest.fixture
def agno_synthesis_result():
    """Sample Agno synthesis result"""
    return AgnoSynthesis(
        market_demand=85.0,
        pain_intensity=78.0,
        monetization_potential=72.0,
        confidence_score=90.0,
        agent_details={
            "wtp": {"wtp_score": 85.0, "pain_score": 80.0},
            "segment": {"audience_size_score": 85.0},
            "price": {"revenue_potential": 70.0},
            "behavior": {"payment_readiness": 75.0}
        }
    )
```

---

## 9. Continuous Testing Workflow

### 9.1 Pre-Commit Testing

```bash
# .git/hooks/pre-commit

#!/bin/bash
# Run fast unit tests before commit

echo "Running unit tests..."
pytest tests/ -m "unit" --tb=short -q

if [ $? -ne 0 ]; then
    echo "❌ Unit tests failed. Commit aborted."
    exit 1
fi

echo "✅ Unit tests passed."
```

### 9.2 CI/CD Testing Pipeline

```yaml
# .github/workflows/test.yml

name: Test Suite

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run unit tests
        run: pytest tests/ -m "unit" --cov --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4

      - name: Start services
        run: docker-compose up -d postgres

      - name: Run integration tests
        run: pytest tests/ -m "integration" --vcr-record=none

      - name: Stop services
        run: docker-compose down

  benchmark-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4

      - name: Run benchmarks
        run: |
          pytest tests/ -m "benchmark" --benchmark-only \
            --benchmark-json=output.json

      - name: Compare benchmarks
        run: python scripts/compare_benchmarks.py
```

### 9.3 Daily Testing Schedule

```bash
# crontab -e

# Run full test suite daily at 2 AM
0 2 * * * cd /app && pytest tests/ --cov --cov-report=html

# Run A/B comparison tests weekly (Sundays at 3 AM)
0 3 * * 0 cd /app && pytest tests/ -m "comparison" --report=weekly_comparison.html
```

### 9.4 Testing Commands Reference

```bash
# ========================================
# FAST TESTS (Development)
# ========================================

# Run unit tests only (fast)
pytest tests/ -m "unit" -v

# Run specific test file
pytest tests/transform/test_agno_analyzer.py -v

# Run specific test function
pytest tests/transform/test_agno_analyzer.py::test_analyze_submission -v

# Run tests matching pattern
pytest tests/ -k "synthesis" -v


# ========================================
# COVERAGE TESTS (Quality Gate)
# ========================================

# Run with coverage report
pytest tests/ --cov=pipeline-v3 --cov-report=html

# Coverage for specific module
pytest tests/transform/ --cov=pipeline-v3/transform --cov-report=term-missing

# Fail if coverage below threshold
pytest tests/ --cov --cov-fail-under=80


# ========================================
# INTEGRATION TESTS (CI/CD)
# ========================================

# Run integration tests only
pytest tests/ -m "integration" -v

# Run with VCR recording (first time)
pytest tests/ -m "vcr" --vcr-record=all

# Run with VCR replay (subsequent runs)
pytest tests/ -m "vcr" --vcr-record=none


# ========================================
# PERFORMANCE TESTS (Benchmarking)
# ========================================

# Run benchmark tests
pytest tests/ -m "benchmark" --benchmark-only

# Compare benchmarks
pytest tests/ --benchmark-compare --benchmark-autosave


# ========================================
# COMPARISON TESTS (Quality Validation)
# ========================================

# Run A/B comparison (Agno vs LiteLLM)
pytest tests/ -m "comparison" --report=comparison_report.html

# Run slow tests (full dataset)
pytest tests/ -m "slow" --timeout=600


# ========================================
# PARALLEL EXECUTION (Speed)
# ========================================

# Run tests in parallel (4 workers)
pytest tests/ -n 4 -v

# Auto-detect worker count
pytest tests/ -n auto -v
```

---

## Summary

This testing strategy provides:

1. **Clear TDD guidance**: Know when to write tests first (synthesis logic, cost tracking) vs test-after (agent prompts, API integrations)

2. **Comprehensive coverage targets**: 100% for critical paths, 90% for high-value components, 80% overall

3. **Phase-by-phase approach**: Testing strategy aligned with implementation phases

4. **Practical examples**: Real test code for synthesis logic, format conversion, API integration

5. **Modern tooling**: VCR.py for API mocking, pytest-benchmark for performance, hypothesis for property-based testing

6. **CI/CD integration**: Pre-commit hooks, GitHub Actions workflows, daily test schedules

**Key Takeaway**: Apply TDD where it provides value (deterministic logic, data transformations), use test-after for exploratory work (agent prompts, API integrations), and always write regression tests after validation.

---

**Related Documentation:**
- `/home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3/docs/agno-integration/testing/coverage-requirements.md`
- `/home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3/docs/AGNO_INTEGRATION_ARCHITECTURE.md` (Section 7)
- `/home/carlos/projects/redditharbor-core-functions-fix/CLAUDE.md` (Testing Standards rules)
