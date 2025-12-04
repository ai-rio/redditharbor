# Agno Integration Coverage Requirements

**Document Status**: Implementation Standard
**Version**: 1.0
**Created**: 2025-12-03
**Component**: Pipeline v3 - Agno Multi-Agent Integration

---

## Table of Contents

1. [Coverage Philosophy](#1-coverage-philosophy)
2. [Component-Level Requirements](#2-component-level-requirements)
3. [Critical Path Coverage (100%)](#3-critical-path-coverage-100)
4. [High-Value Coverage (90%)](#4-high-value-coverage-90)
5. [Standard Coverage (80%)](#5-standard-coverage-80)
6. [Minimal Coverage (50%)](#6-minimal-coverage-50)
7. [Coverage Measurement](#7-coverage-measurement)
8. [Quality Gates](#8-quality-gates)
9. [Coverage Exemptions](#9-coverage-exemptions)

---

## 1. Coverage Philosophy

### 1.1 Risk-Based Coverage Targets

Coverage targets are set based on **business risk** and **technical complexity**, not arbitrary percentages.

**Guiding Principles:**
- **100% coverage for financial calculations** - Billing errors are unacceptable
- **100% coverage for data transformations** - Schema violations break downstream systems
- **90% coverage for high-value integrations** - Core business logic must be reliable
- **80% coverage for standard components** - Balance quality with velocity
- **50% coverage for exploratory code** - Smoke tests prevent major regressions

### 1.2 Coverage is NOT Quality

**Coverage measures test execution, not test quality.**

```python
# ❌ 100% coverage, 0% value
def test_synthesis_exists():
    """This test achieves coverage but validates nothing"""
    synthesizer = AgnoSynthesizer()
    result = synthesizer.calculate_market_demand(80.0, 60.0)
    assert result is not None  # Useless assertion

# ✅ 100% coverage, high value
def test_synthesis_weighted_average():
    """This test validates business logic"""
    synthesizer = AgnoSynthesizer()
    result = synthesizer.calculate_market_demand(80.0, 60.0)

    # Validates actual business rule
    expected = (80.0 * 0.6) + (60.0 * 0.4)  # 72.0
    assert result == expected
```

**Focus on meaningful assertions:**
- ✅ Validate outputs match business rules
- ✅ Test edge cases and boundary conditions
- ✅ Verify error handling and recovery
- ❌ Don't test framework code (Pydantic, SQLAlchemy internals)
- ❌ Don't chase coverage percentage for its own sake

### 1.3 Mutation Testing for Quality

**Coverage tells you what's executed, mutation testing tells you what's actually validated.**

```bash
# Install mutation testing framework
pip install mutmut

# Run mutation tests on synthesis logic
mutmut run --paths-to-mutate=pipeline-v3/transform/agno_synthesis.py

# Example: mutmut changes `*` to `+` in calculation
# If tests still pass, your tests are weak
```

---

## 2. Component-Level Requirements

### 2.1 Coverage Matrix

| Component | Target | Rationale | Priority |
|-----------|--------|-----------|----------|
| **Multi-Agent Synthesis Logic** | 100% | Financial accuracy critical | P0 |
| **Cost Tracking & Calculation** | 100% | Billing errors unacceptable | P0 |
| **Pipeline Format Conversion** | 100% | Data integrity for downstream | P0 |
| **Simplicity Processor** | 100% | Business rule enforcement | P0 |
| **Database Migrations** | 100% | Schema changes must be reversible | P0 |
| **Pydantic Data Models** | 100% | API contract validation | P0 |
| **AgnoOpportunityAnalyzer** | 90% | Main integration point | P1 |
| **AnalyzerFactory** | 90% | Critical dependency injection | P1 |
| **Market Research Agent** | 90% | High business value | P1 |
| **Agent Implementations** | 80% | Prompt engineering requires flexibility | P2 |
| **Jina API Integration** | 80% | External service, use VCR.py | P2 |
| **AgentOps Tracking** | 80% | Observability, not business logic | P2 |
| **Configuration Loading** | 80% | Simple validation logic | P2 |
| **Agent Instructions** | 50% | Iterative prompt tuning | P3 |
| **Logging Utilities** | 50% | Simple wrappers | P3 |
| **CLI Entry Points** | 50% | Smoke tests sufficient | P3 |

### 2.2 Priority Definitions

**P0 (Critical)**: Must have 100% coverage before merge
- Blocks production deployment if uncovered
- Requires manual review for coverage exemptions
- Breaking changes require regression test updates

**P1 (High)**: Should have 90%+ coverage before merge
- Warnings generated for coverage below threshold
- Can merge with justification and follow-up ticket
- Focus on critical paths, edge cases optional

**P2 (Standard)**: Target 80% coverage over time
- Best effort during development
- Coverage gaps acceptable with risk assessment
- Focus on happy path and common errors

**P3 (Low)**: Minimal coverage (50%) for smoke tests
- Prevent major regressions only
- Extensive testing wastes time on exploratory code
- Increase coverage if code stabilizes

---

## 3. Critical Path Coverage (100%)

### 3.1 Multi-Agent Synthesis Logic

**File**: `pipeline-v3/transform/agno_synthesis.py`

**Why 100%**: Financial calculations must be exact. Incorrect consensus scoring leads to bad opportunity prioritization and wasted resources.

**Required Test Coverage:**

```python
# ✅ REQUIRED: All calculation branches
def test_market_demand_calculation():
    """Market demand = WTP (60%) + Segment (40%)"""
    assert calculate_market_demand(80.0, 60.0) == 72.0

def test_market_demand_with_subreddit_multiplier():
    """High purchasing power subreddits get 2x multiplier"""
    result = calculate_market_demand(80.0, 60.0, subreddit="entrepreneur")
    assert result == min((72.0 * 2.0), 100.0)

def test_market_demand_caps_at_100():
    """Market demand never exceeds 100"""
    result = calculate_market_demand(100.0, 100.0, subreddit="entrepreneur")
    assert result == 100.0

# ✅ REQUIRED: All edge cases
def test_pain_intensity_zero_scores():
    """Zero scores should return zero pain intensity"""
    assert calculate_pain_intensity(0.0, 0.0, 0.0) == 0.0

def test_pain_intensity_max_scores():
    """Max scores should return weighted max"""
    result = calculate_pain_intensity(100.0, 100.0, 100.0)
    assert result == 100.0

# ✅ REQUIRED: Consensus confidence
def test_consensus_confidence_perfect_agreement():
    """Perfect agreement = 100% confidence"""
    scores = {"wtp": 80.0, "segment": 80.0, "price": 80.0, "behavior": 80.0}
    assert calculate_consensus_confidence(scores) == 100.0

def test_consensus_confidence_high_disagreement():
    """High variance = low confidence"""
    scores = {"wtp": 90.0, "segment": 30.0, "price": 95.0, "behavior": 25.0}
    assert calculate_consensus_confidence(scores) < 50.0
```

**Coverage Verification:**
```bash
pytest tests/transform/test_agno_synthesis.py \
  --cov=pipeline-v3/transform/agno_synthesis.py \
  --cov-report=term-missing \
  --cov-fail-under=100
```

### 3.2 Cost Tracking & Calculation

**File**: `pipeline-v3/monitoring/cost_tracking.py`

**Why 100%**: Billing accuracy is critical. Underestimating costs leads to budget overruns, overestimating loses business.

**Required Test Coverage:**

```python
# ✅ REQUIRED: All cost models
def test_cost_calculation_openai():
    """OpenAI pricing: $0.002/1K input, $0.006/1K output"""
    cost = calculate_cost(tokens_in=1000, tokens_out=500, model="gpt-4o-mini")
    expected = (1000 * 0.002 / 1000) + (500 * 0.006 / 1000)
    assert cost == expected

def test_cost_calculation_anthropic():
    """Claude Haiku: $0.0008/1K input, $0.004/1K output"""
    cost = calculate_cost(tokens_in=1000, tokens_out=500, model="claude-haiku-4.5")
    expected = (1000 * 0.0008 / 1000) + (500 * 0.004 / 1000)
    assert cost == expected

def test_cost_calculation_unknown_model():
    """Unknown model should raise ValueError"""
    with pytest.raises(ValueError, match="Unknown model"):
        calculate_cost(tokens_in=1000, tokens_out=500, model="fake-model")

# ✅ REQUIRED: Aggregation logic
def test_batch_cost_aggregation():
    """Batch cost = sum of individual costs"""
    tracker = CostTracker()

    for _ in range(10):
        tracker.record_call(tokens_in=500, tokens_out=200, model="claude-haiku-4.5")

    single_cost = (500 * 0.0008 / 1000) + (200 * 0.004 / 1000)
    assert tracker.total_cost == single_cost * 10

# ✅ REQUIRED: Per-agent breakdown
def test_per_agent_cost_tracking():
    """Track individual agent costs separately"""
    tracker = CostTracker()

    tracker.record_agent_call("WTP Analyst", tokens_in=500, model="claude-haiku-4.5")
    tracker.record_agent_call("Segment Analyst", tokens_in=600, model="claude-haiku-4.5")

    wtp_cost = tracker.get_agent_cost("WTP Analyst")
    segment_cost = tracker.get_agent_cost("Segment Analyst")

    assert segment_cost > wtp_cost  # More tokens = higher cost
```

### 3.3 Pipeline Format Conversion

**File**: `pipeline-v3/transform/format_converter.py`

**Why 100%**: Incorrect conversions break downstream systems. Database schema violations cause pipeline failures.

**Required Test Coverage:**

```python
# ✅ REQUIRED: All field mappings
def test_converts_agno_synthesis_to_analysis_result():
    """AgnoSynthesis → AnalysisResult preserves all fields"""
    synthesis = AgnoSynthesis(
        market_demand=85.0,
        pain_intensity=78.0,
        monetization_potential=72.0,
        confidence_score=90.0
    )
    submission = RedditSubmission(id="sub_123")

    result = convert_to_analysis_result(synthesis, submission)

    assert result.submission_id == "sub_123"
    assert result.market_metrics.market_demand == 85.0
    assert result.market_metrics.pain_intensity == 78.0
    assert result.confidence_score == 90.0

# ✅ REQUIRED: Simplicity enforcement
def test_enforces_max_3_core_functions():
    """Simplicity processor limits to 3 functions"""
    synthesis = AgnoSynthesis(
        core_functions=["Fn1", "Fn2", "Fn3", "Fn4", "Fn5"]
    )

    result = convert_to_analysis_result(synthesis)

    assert len(result.app_idea.core_functions) == 3
    # Should keep highest-priority functions
    assert result.app_idea.core_functions == ["Fn1", "Fn2", "Fn3"]

# ✅ REQUIRED: Trust level assignment
def test_assigns_trust_level_high():
    """Confidence >80% = HIGH trust"""
    synthesis = AgnoSynthesis(confidence_score=85.0)
    result = convert_to_analysis_result(synthesis)
    assert result.trust_level == "HIGH"

def test_assigns_trust_level_medium():
    """Confidence 60-80% = MEDIUM trust"""
    synthesis = AgnoSynthesis(confidence_score=70.0)
    result = convert_to_analysis_result(synthesis)
    assert result.trust_level == "MEDIUM"

def test_assigns_trust_level_low():
    """Confidence <60% = LOW trust"""
    synthesis = AgnoSynthesis(confidence_score=50.0)
    result = convert_to_analysis_result(synthesis)
    assert result.trust_level == "LOW"

# ✅ REQUIRED: Final score calculation
def test_calculates_final_score():
    """Final score = market (40%) + pain (30%) + monetization (30%)"""
    synthesis = AgnoSynthesis(
        market_demand=80.0,
        pain_intensity=70.0,
        monetization_potential=60.0
    )

    result = convert_to_analysis_result(synthesis)

    expected = (80.0 * 0.4) + (70.0 * 0.3) + (60.0 * 0.3)
    assert result.final_score == expected
```

### 3.4 Database Migrations

**File**: `pipeline-v3/migrations/add_agno_columns.sql`

**Why 100%**: Failed migrations corrupt production data. Rollbacks must be tested.

**Required Test Coverage:**

```python
# ✅ REQUIRED: Forward migration
def test_migration_adds_agno_columns(db_connection):
    """Forward migration adds all Agno columns"""
    run_migration("add_agno_columns", direction="up")

    inspector = inspect(db_connection)
    columns = [c["name"] for c in inspector.get_columns("opportunities")]

    # All Agno columns present
    assert "agno_wtp_score" in columns
    assert "agno_segment_confidence" in columns
    assert "agno_price_potential" in columns
    assert "agno_behavior_score" in columns
    assert "agno_consensus_confidence" in columns

    # All Jina columns present
    assert "jina_validation_score" in columns
    assert "jina_data_quality_score" in columns
    assert "jina_competitor_count" in columns

# ✅ REQUIRED: Backward migration
def test_migration_rollback_removes_columns(db_connection):
    """Rollback removes all Agno columns without data loss"""
    # Add data
    run_migration("add_agno_columns", direction="up")
    db_connection.execute(
        "INSERT INTO opportunities (id, submission_id, agno_wtp_score) "
        "VALUES ('opp_1', 'sub_1', 85.0)"
    )

    # Rollback
    run_migration("add_agno_columns", direction="down")

    # Columns removed
    inspector = inspect(db_connection)
    columns = [c["name"] for c in inspector.get_columns("opportunities")]
    assert "agno_wtp_score" not in columns

    # Base data preserved
    row = db_connection.execute("SELECT * FROM opportunities WHERE id = 'opp_1'").fetchone()
    assert row["submission_id"] == "sub_1"

# ✅ REQUIRED: Idempotency
def test_migration_idempotent(db_connection):
    """Running migration twice doesn't fail"""
    run_migration("add_agno_columns", direction="up")

    # Should not fail
    run_migration("add_agno_columns", direction="up")
```

---

## 4. High-Value Coverage (90%)

### 4.1 AgnoOpportunityAnalyzer

**File**: `pipeline-v3/transform/agno_analyzer.py`

**Why 90%**: Main integration point. Errors here cascade to all components.

**Coverage Focus:**
- ✅ Team initialization (5 agents)
- ✅ Sequential orchestration mode
- ✅ Parallel orchestration mode
- ✅ Error handling and fallbacks
- ✅ Cost tracking integration
- ⚠️ Internal state management (can skip)

```bash
pytest tests/transform/test_agno_analyzer.py \
  --cov=pipeline-v3/transform/agno_analyzer.py \
  --cov-report=term-missing \
  --cov-fail-under=90
```

### 4.2 AnalyzerFactory

**File**: `pipeline-v3/transform/analyzer_factory.py`

**Why 90%**: Dependency injection errors break entire pipeline.

**Coverage Focus:**
- ✅ All analyzer types ("simple", "litellm", "agno", "hybrid")
- ✅ Configuration injection
- ✅ Environment variable handling
- ⚠️ Private helper methods (can skip if trivial)

### 4.3 Market Research Agent

**File**: `pipeline-v3/agents/market_research_agent.py`

**Why 90%**: High business value. Real market data enrichment is key differentiator.

**Coverage Focus:**
- ✅ Jina API integration
- ✅ Competitor discovery
- ✅ Pricing extraction
- ✅ Market size validation
- ✅ Evidence aggregation
- ⚠️ Prompt engineering (test outputs, not prompts)

```python
# ✅ REQUIRED: High-value paths
@pytest.mark.vcr()
def test_market_research_finds_competitors():
    """MarketResearchAgent finds >=3 competitors"""
    agent = MarketResearchAgent(model="claude-haiku-4.5")
    result = agent.run({"app_concept": "Project management tool"})

    assert len(result["competitor_pricing"]) >= 3
    assert result["validation_score"] > 0

# ⚠️ OPTIONAL: Edge cases
def test_market_research_handles_no_competitors():
    """Agent gracefully handles zero competitors found"""
    agent = MarketResearchAgent(model="test-model")
    # Mock Jina API returning empty results
    with patch.object(JinaClient, "search_web", return_value=[]):
        result = agent.run({"app_concept": "Obscure niche tool"})

    assert result["competitor_pricing"] == []
    assert result["validation_score"] == 0
    # Optional test - nice to have but not critical
```

---

## 5. Standard Coverage (80%)

### 5.1 Agent Implementations

**Files**: `pipeline-v3/agents/*.py`

**Why 80%**: Prompt engineering requires iteration. Test outputs, not prompts.

**Coverage Focus:**
- ✅ Output format validation (Pydantic models)
- ✅ Score ranges (0-100)
- ✅ Required fields present
- ⚠️ Prompt quality (manual validation)

```python
# ✅ REQUIRED: Output contract
def test_wtp_agent_returns_valid_output():
    """WTP Agent returns valid WTPAnalysis"""
    agent = WTPAgent(model="test-model")
    result = agent.run(test_input)

    # Validate Pydantic model
    analysis = WTPAnalysis(**result)
    assert isinstance(analysis, WTPAnalysis)
    assert 0 <= analysis.wtp_score <= 100

# ⚠️ OPTIONAL: Prompt quality
def test_wtp_agent_prompt_quality():
    """WTP Agent uses correct prompt template"""
    agent = WTPAgent(model="test-model")
    # Don't test this - prompts change frequently
```

### 5.2 Jina API Integration

**File**: `pipeline-v3/integrations/jina_client.py`

**Why 80%**: External service. Use VCR.py for recording, don't test Jina's API.

**Coverage Focus:**
- ✅ Search query construction
- ✅ URL extraction
- ✅ Error handling (timeouts, rate limits)
- ⚠️ Jina API internals (don't test)

### 5.3 Configuration Loading

**File**: `pipeline-v3/config/settings.py`

**Why 80%**: Simple validation logic. Focus on environment variable handling.

**Coverage Focus:**
- ✅ Environment variable loading
- ✅ Default fallbacks
- ✅ Validation errors
- ⚠️ Getter methods (trivial)

---

## 6. Minimal Coverage (50%)

### 6.1 Agent Instructions

**Files**: `pipeline-v3/agents/instructions/*.txt`

**Why 50%**: Iterative prompt tuning. Only test integration points.

**Coverage Focus:**
- ✅ Smoke test: Agent runs without errors
- ⚠️ Prompt quality: Manual validation only

### 6.2 CLI Entry Points

**File**: `pipeline-v3/cli.py`

**Why 50%**: Simple wrappers. Smoke tests prevent regressions.

**Coverage Focus:**
- ✅ Main entry point runs
- ✅ Help text displayed
- ⚠️ Argument parsing (framework code)

---

## 7. Coverage Measurement

### 7.1 Running Coverage Reports

```bash
# ========================================
# COMPONENT-LEVEL COVERAGE
# ========================================

# Critical path (100% required)
pytest tests/transform/test_agno_synthesis.py \
  --cov=pipeline-v3/transform/agno_synthesis.py \
  --cov-fail-under=100

# High-value (90% required)
pytest tests/transform/test_agno_analyzer.py \
  --cov=pipeline-v3/transform/agno_analyzer.py \
  --cov-fail-under=90

# Standard (80% required)
pytest tests/agents/ \
  --cov=pipeline-v3/agents \
  --cov-fail-under=80


# ========================================
# OVERALL COVERAGE
# ========================================

# Generate HTML report
pytest tests/ \
  --cov=pipeline-v3 \
  --cov-report=html \
  --cov-report=term-missing

# Open in browser
open htmlcov/index.html


# ========================================
# COVERAGE DIFF (CI/CD)
# ========================================

# Compare coverage against main branch
coverage xml
diff-cover coverage.xml --compare-branch=main --fail-under=80
```

### 7.2 Coverage Report Interpretation

```bash
$ pytest tests/ --cov=pipeline-v3 --cov-report=term-missing

Name                                      Stmts   Miss  Cover   Missing
-----------------------------------------------------------------------
pipeline-v3/transform/agno_synthesis.py      45      0   100%
pipeline-v3/monitoring/cost_tracking.py      32      0   100%
pipeline-v3/transform/format_converter.py    28      0   100%
pipeline-v3/transform/agno_analyzer.py       67      7    90%   102-108
pipeline-v3/agents/market_research.py        54      5    91%   201-205
pipeline-v3/agents/wtp_agent.py              42      8    81%   67-74
pipeline-v3/config/settings.py               23      5    78%   89-93
-----------------------------------------------------------------------
TOTAL                                       291     25    91%
```

**What to Focus On:**
- ✅ `agno_synthesis.py`: 100% (meets critical path requirement)
- ✅ `cost_tracking.py`: 100% (meets critical path requirement)
- ✅ `agno_analyzer.py`: 90% (meets high-value requirement)
- ⚠️ `settings.py`: 78% (below 80% standard - investigate)

### 7.3 Investigating Coverage Gaps

```bash
# Show missing lines
pytest tests/ --cov=pipeline-v3/config/settings.py --cov-report=term-missing

# Missing lines: 89-93
# Code review shows:
#   - Line 89-91: Debug logging (exempt)
#   - Line 92-93: Environment-specific fallback (should test)

# Add test for missing coverage
def test_settings_environment_fallback():
    """Settings use fallback when env var missing"""
    with patch.dict(os.environ, {}, clear=True):
        settings = load_settings()
        assert settings.model_name == "anthropic/claude-haiku-4.5"  # Default
```

---

## 8. Quality Gates

### 8.1 Pre-Merge Quality Gates

**All pull requests must pass:**

```yaml
# .github/workflows/quality-gate.yml

name: Quality Gate
on: [pull_request]

jobs:
  coverage-gate:
    runs-on: ubuntu-latest
    steps:
      - name: Run tests with coverage
        run: pytest tests/ --cov=pipeline-v3 --cov-report=xml

      - name: Check critical path coverage (100%)
        run: |
          pytest tests/transform/test_agno_synthesis.py \
            --cov=pipeline-v3/transform/agno_synthesis.py \
            --cov-fail-under=100

      - name: Check overall coverage (80%)
        run: |
          pytest tests/ \
            --cov=pipeline-v3 \
            --cov-fail-under=80

      - name: Coverage diff vs main
        run: |
          diff-cover coverage.xml --compare-branch=main --fail-under=80
```

### 8.2 Coverage Exemption Process

**To exempt code from coverage requirements:**

1. Add `# pragma: no cover` comment
2. Document reason in pull request
3. Get approval from two reviewers

```python
# Example: Exempt debug code
def _debug_print_agent_state(self):  # pragma: no cover
    """Debug utility - not covered in tests"""
    print(f"Agent state: {self.state}")
```

**Valid exemption reasons:**
- ✅ Debug/logging code
- ✅ Platform-specific code (Windows-only, Linux-only)
- ✅ Deprecation warnings
- ❌ "Too hard to test" (fix the design instead)
- ❌ "We'll add tests later" (no, add now)

---

## 9. Coverage Exemptions

### 9.1 Configuration in .coveragerc

```ini
# .coveragerc

[report]
exclude_lines =
    # Standard exemptions
    pragma: no cover
    def __repr__
    def __str__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
    @overload

    # Project-specific exemptions
    # Debug/logging only
    logger.debug
    logger.trace

    # Platform-specific
    if sys.platform == "win32":
    if os.name == "nt":

    # Deprecation warnings
    warnings.warn.*DeprecationWarning
```

### 9.2 When to Exempt Code

**Exempt these patterns:**

```python
# ✅ EXEMPT: Type checking imports
if TYPE_CHECKING:
    from typing import Protocol  # pragma: no cover

# ✅ EXEMPT: Abstract methods
@abstractmethod
def run(self, input_data: dict) -> dict:  # pragma: no cover
    """Subclasses must implement"""
    pass

# ✅ EXEMPT: Unreachable error cases
def parse_score(score: str) -> float:
    try:
        return float(score)
    except ValueError:
        # Should never happen due to upstream validation
        raise AssertionError("Invalid score passed validation")  # pragma: no cover

# ✅ EXEMPT: Platform-specific code
if sys.platform == "win32":  # pragma: no cover
    # Windows-specific database connection
    connection_string = f"Driver={{SQL Server}};Server={host};Database={db}"

# ✅ EXEMPT: Debug logging
def _log_agent_details(self, agent_name: str):  # pragma: no cover
    """Debug logging - not covered in tests"""
    if os.getenv("DEBUG_AGENTS"):
        logger.debug(f"Agent {agent_name} state: {self._get_state()}")
```

**Don't exempt these:**

```python
# ❌ NO EXEMPTION: Business logic
def calculate_final_score(self, metrics: dict) -> float:
    # This must be tested!
    return (metrics["market"] * 0.4) + (metrics["pain"] * 0.3)

# ❌ NO EXEMPTION: Error handling
try:
    result = self.team.run(input_data)
except Exception as e:
    # Must test error recovery!
    logger.error(f"Team execution failed: {e}")
    return fallback_result()

# ❌ NO EXEMPTION: "Too hard to test"
def complex_agent_orchestration(self):
    # If it's too hard to test, refactor it!
    # Don't exempt it
    ...
```

---

## Summary

### Coverage Requirements by Priority

| Priority | Components | Target | Gate |
|----------|-----------|--------|------|
| **P0** | Synthesis, Cost, Format, Migrations | 100% | Blocks merge |
| **P1** | Analyzer, Factory, Market Research | 90% | Warning |
| **P2** | Agents, Jina, Config | 80% | Best effort |
| **P3** | Instructions, CLI, Logging | 50% | Smoke tests |

### Key Principles

1. **Risk-based targets**: Higher coverage for financial calculations, data transformations
2. **Quality over quantity**: Meaningful assertions, not coverage theater
3. **Mutation testing**: Validate test quality, not just execution
4. **Exemptions require justification**: No blanket `# pragma: no cover`
5. **Coverage is a guide, not a goal**: 80% with good tests > 100% with weak tests

### Commands Reference

```bash
# Check critical path (100%)
pytest tests/transform/test_agno_synthesis.py \
  --cov=pipeline-v3/transform/agno_synthesis.py \
  --cov-fail-under=100

# Check overall (80%)
pytest tests/ --cov=pipeline-v3 --cov-fail-under=80

# Generate HTML report
pytest tests/ --cov=pipeline-v3 --cov-report=html

# Coverage diff vs main
diff-cover coverage.xml --compare-branch=main --fail-under=80
```

---

**Related Documentation:**
- `/home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3/docs/agno-integration/testing/testing-strategy.md`
- `/home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3/docs/AGNO_INTEGRATION_ARCHITECTURE.md` (Section 10.3)
- `/home/carlos/projects/redditharbor-core-functions-fix/CLAUDE.md` (Testing Standards rules)
