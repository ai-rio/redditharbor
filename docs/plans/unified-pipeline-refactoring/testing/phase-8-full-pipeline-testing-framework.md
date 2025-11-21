# Phase 8: Full Pipeline Testing Framework

**Date**: 2025-11-20
**Status**: Planning
**Target**: Prove unified OpportunityPipeline produces identical AI-enriched profiles as monolith, ready for production

---

## Executive Summary

### Testing Target

**PRIMARY GOAL**: Validate unified OpportunityPipeline produces **functionally equivalent** AI-enriched profiles as monolith scripts before building FastAPI backend (Phase 9).

**SUCCESS DEFINITION**:
- ✅ **Functional Equivalence**: 95%+ field match rate vs monolith (30+ enrichment fields)
- ✅ **Production Readiness**: 95%+ success rate at scale (200 submissions)
- ✅ **Performance Acceptable**: Processing time within 20% of monolith
- ✅ **Budget Sustainable**: Average cost < $0.15 per submission
- ✅ **Storage Validated**: DLT merge disposition working correctly
- ✅ **Observability Working**: AgentOps, LiteLLM tracking all AI service calls

**WHEN COMPLETE**: All success criteria met → Proceed to Phase 9 (FastAPI Backend)

---

## Naming Conventions

### Directory Structure Naming

```
scripts/testing/integration/                     # Integration testing suite
├── README.md                                    # Suite overview
│
├── config/
│   ├── test_config.py                          # Centralized test configuration
│   ├── submissions_single.json                 # 1 high-quality submission
│   ├── submissions_small_batch.json            # 5 varied submissions
│   ├── submissions_monolith_comparison.json    # 10 for monolith comparison
│   ├── submissions_medium_batch.json           # 50 for scale testing
│   ├── submissions_large_batch.json            # 200 for stress testing
│   └── service_config.json                     # Service enable/disable flags
│
├── tests/
│   ├── test_01_single_submission.py            # Single submission validation
│   ├── test_02_small_batch.py                  # 5 submissions, all services
│   ├── test_03_monolith_equivalence.py         # Compare vs real monolith (10)
│   ├── test_04_medium_scale.py                 # 50 submissions
│   ├── test_05_large_scale.py                  # 200 submissions (stress)
│   ├── test_06_error_recovery.py               # Service failure scenarios
│   ├── test_07_storage_validation.py           # DLT storage integration
│   ├── test_08_cost_monitoring.py              # Cost tracking and budgets
│   └── test_09_observability.py                # AgentOps/LiteLLM validation
│
├── utils/
│   ├── comparison.py                           # Field-by-field comparison logic
│   ├── metrics.py                              # Metrics collection
│   ├── reporting.py                            # JSON/console report generation
│   ├── monolith_runner.py                      # Helper to run real monolith
│   └── observability.py                        # AgentOps/LiteLLM helpers
│
├── results/
│   ├── test_01_single_submission/
│   │   ├── run_2025-11-20_10-30-00.json
│   │   └── run_2025-11-20_14-45-00.json
│   ├── test_02_small_batch/
│   ├── test_03_monolith_equivalence/
│   │   ├── unified_results_2025-11-20.json
│   │   ├── monolith_results_2025-11-20.json
│   │   └── comparison_report_2025-11-20.json
│   └── ...
│
├── monolith_baseline/
│   ├── generate_baseline.sh                    # Script to run monolith and store results
│   └── results/
│       └── monolith_enrichment_2025-11-20.json
│
└── observability/
    ├── agentops_traces/                        # AgentOps session exports
    ├── litellm_logs/                           # LiteLLM cost tracking logs
    └── agno_traces/                            # Agno agent execution traces
```

### Documentation Naming

```
docs/plans/unified-pipeline-refactoring/
│
├── PHASE-8-FULL-PIPELINE-TESTING-FRAMEWORK.md  # This document (overview)
│
├── prompts/
│   └── integration-testing/
│       ├── test-01-single-submission-prompt.md
│       ├── test-02-small-batch-prompt.md
│       ├── test-03-monolith-equivalence-prompt.md
│       ├── test-04-medium-scale-prompt.md
│       ├── test-05-large-scale-prompt.md
│       ├── test-06-error-recovery-prompt.md
│       ├── test-07-storage-validation-prompt.md
│       ├── test-08-cost-monitoring-prompt.md
│       └── test-09-observability-prompt.md
│
└── local-ai-report/
    └── integration-testing/
        ├── test-01-single-submission-report.md
        ├── test-02-small-batch-report.md
        ├── test-03-monolith-equivalence-report.md
        ├── test-04-medium-scale-report.md
        ├── test-05-large-scale-report.md
        ├── test-06-error-recovery-report.md
        ├── test-07-storage-validation-report.md
        ├── test-08-cost-monitoring-report.md
        └── test-09-observability-report.md
```

### File Naming Convention Rules

1. **Test Scripts**: `test_{number}_{descriptive_name}.py`
   - `test_01_` = Single submission validation
   - `test_02_` = Small batch (5)
   - `test_03_` = Monolith equivalence (critical comparison)
   - `test_04_` = Medium scale (50)
   - `test_05_` = Large scale (200)
   - `test_06_` = Error recovery
   - `test_07_` = Storage validation
   - `test_08_` = Cost monitoring
   - `test_09_` = Observability validation

2. **Config Files**: `{entity}_{size/type}.json`
   - `submissions_single.json` = 1 submission
   - `submissions_small_batch.json` = 5 submissions
   - `submissions_monolith_comparison.json` = 10 submissions
   - `submissions_medium_batch.json` = 50 submissions
   - `submissions_large_batch.json` = 200 submissions

3. **Results**: `run_{ISO_timestamp}.json`
   - `run_2025-11-20_10-30-00.json` = Timestamped run
   - Stored in test-specific subdirectories

4. **Prompts**: `test-{number}-{name}-prompt.md`
   - Matches test script naming
   - Easy to find corresponding prompt for each test

5. **Reports**: `test-{number}-{name}-report.md`
   - Matches test script and prompt naming
   - Clear traceability

---

## Clear Path Forward

### Testing Roadmap (Sequential Execution)

```
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 8: FULL PIPELINE INTEGRATION TESTING                         │
│  Target: Prove unified pipeline = monolith (functionally)           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TEST 01: Single Submission Validation                              │
│  Goal: Prove all AI services execute and populate enrichment fields │
│  Command: test_01_single_submission.py --submission-id sub_001      │
│  Duration: 30 mins (including fixes)                                │
│  Success: All 30+ fields populated, no crashes                      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TEST 02: Small Batch (5 Submissions)                               │
│  Goal: Prove consistency across multiple submissions                │
│  Command: test_02_small_batch.py                                    │
│  Duration: 1 hour                                                   │
│  Success: 5/5 processed, 100% field coverage, cost < $1             │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TEST 03: Monolith Equivalence (10 Submissions) ⭐ CRITICAL          │
│  Goal: Prove unified pipeline = monolith (field-by-field)           │
│  Steps:                                                              │
│    1. Run real monolith scripts on 10 submissions                   │
│    2. Store monolith results in baseline                            │
│    3. Run unified pipeline on same 10 submissions                   │
│    4. Compare 30+ fields with tolerances                            │
│  Duration: 3-4 hours                                                │
│  Success: 95%+ field match rate                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TEST 04: Medium Scale (50 Submissions)                             │
│  Goal: Validate production batch size performance                   │
│  Command: test_04_medium_scale.py                                   │
│  Duration: 2-3 hours                                                │
│  Success: 48+/50 (96%+), performance within 20% of monolith         │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TEST 05: Large Scale (200 Submissions) - Stress Test               │
│  Goal: Prove production readiness at scale                          │
│  Command: test_05_large_scale.py                                    │
│  Duration: 8-10 hours                                               │
│  Success: 190+/200 (95%+), no memory leaks, cost < $30              │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TEST 06: Error Recovery                                            │
│  Goal: Validate graceful degradation                                │
│  Command: test_06_error_recovery.py                                 │
│  Duration: 2 hours                                                  │
│  Success: Pipeline continues despite service failures               │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TEST 07: Storage Validation                                        │
│  Goal: Validate DLT storage layer integration                       │
│  Command: test_07_storage_validation.py                             │
│  Duration: 1 hour                                                   │
│  Success: DLT merge disposition working, no duplicates              │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TEST 08: Cost Monitoring                                           │
│  Goal: Validate budget sustainability                               │
│  Command: test_08_cost_monitoring.py                                │
│  Duration: 1 hour                                                   │
│  Success: Average cost < $0.15/submission                           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TEST 09: Observability Validation                                  │
│  Goal: Validate AgentOps/LiteLLM tracking                           │
│  Command: test_09_observability.py                                  │
│  Duration: 2 hours                                                  │
│  Success: All AI calls tracked, traces exportable                   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  🎯 PHASE 8 COMPLETE: UNIFIED PIPELINE VALIDATED                    │
│  ✅ Functional equivalence proven                                    │
│  ✅ Production readiness validated                                   │
│  ✅ Observability working                                            │
│  → PROCEED TO PHASE 9: FASTAPI BACKEND                              │
└─────────────────────────────────────────────────────────────────────┘
```

### Total Estimated Timeline

**Aggressive**: 1 week (if no major issues)
**Conservative**: 2 weeks (with expected debugging/fixes)

---

## Observability Integration Strategy

### Tools to Integrate

1. **AgentOps** - AI agent observability and monitoring
2. **LiteLLM** - Unified LLM interface with cost tracking
3. **Agno** - Multi-agent monetization analysis framework

### Where Each Tool Fits

#### 1. AgentOps Integration

**Purpose**: Track all AI agent executions, costs, latency, errors

**Integration Points**:
- **ProfilerService** (`core/enrichment/profiler_service.py`)
  - Track EnhancedLLMProfiler calls
  - Monitor Claude Haiku API latency
  - Track profiling costs

- **MonetizationService** (`core/enrichment/monetization_service.py`)
  - Track Agno multi-agent team executions
  - Monitor individual agent traces
  - Track monetization analysis costs ($0.10 per call)

- **MarketValidationService** (`core/enrichment/market_validation_service.py`)
  - Track MarketDataValidator calls
  - Monitor Jina AI API calls
  - Track web scraping operations

**Implementation**:
```python
# core/enrichment/profiler_service.py
import agentops

class ProfilerService(BaseEnrichmentService):
    def __init__(self, config):
        super().__init__(config)
        # Initialize AgentOps session
        self.agentops_client = agentops.Client(api_key=os.getenv("AGENTOPS_API_KEY"))
        self.session = self.agentops_client.start_session(
            tags=["profiler", "enrichment"]
        )

    def enrich(self, submission):
        # Track enrichment operation
        with self.agentops_client.create_agent(
            name="EnhancedLLMProfiler",
            agent_id=f"profiler_{submission['submission_id']}"
        ) as agent:
            # Execute profiling
            result = self.profiler.generate_profile(...)

            # Record metrics
            agent.record(
                event_type="llm_call",
                model="claude-3-haiku",
                cost=0.005,
                latency=2.5,
                result=result
            )
```

**Testing**: Test 09 validates AgentOps integration
- Verify sessions created for each test run
- Verify all AI calls tracked
- Verify cost/latency metrics captured
- Verify traces exportable for analysis

#### 2. LiteLLM Integration

**Purpose**: Unified LLM interface with automatic cost tracking across providers

**Integration Points**:
- **ProfilerService**: Route Claude calls through LiteLLM
- **MonetizationService**: Route OpenAI/Anthropic calls through LiteLLM
- **All AI Services**: Centralized cost tracking

**Implementation**:
```python
# core/enrichment/profiler_service.py
import litellm

class ProfilerService(BaseEnrichmentService):
    def enrich(self, submission):
        # Use LiteLLM for unified interface
        response = litellm.completion(
            model="claude-3-haiku-20240307",
            messages=[{"role": "user", "content": prompt}],
            api_base=os.getenv("OPENROUTER_BASE_URL"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
            # LiteLLM automatically tracks cost
        )

        # Get cost from LiteLLM
        cost = litellm.completion_cost(
            completion_response=response,
            model="claude-3-haiku-20240307"
        )

        self.stats["total_cost"] += cost
```

**Benefits**:
- Automatic cost calculation across all providers
- Unified error handling
- Automatic retries with exponential backoff
- Rate limit handling
- Cost analytics and reporting

**Testing**: Test 08 validates LiteLLM cost tracking
- Verify costs calculated correctly for each provider
- Verify total costs match expected budget
- Verify cost breakdown by service
- Export cost reports for analysis

#### 3. Agno Integration

**Purpose**: Multi-agent monetization analysis (already integrated)

**Current Integration**:
- `core/agents/monetization/factory.py` - Creates Agno analyzer
- `core/enrichment/monetization_service.py` - Uses Agno for analysis
- Agno runs multi-agent team:
  - WillingnessToPayAgent
  - PriceSensitivityAgent
  - RevenueOpportunityAgent
  - CustomerSegmentAgent

**What to Test**:
- Verify Agno agents execute correctly through unified pipeline
- Track Agno execution costs (~$0.10 per analysis)
- Monitor Agno agent traces
- Validate deduplication logic (70% cost savings)

**Testing**: Test 09 validates Agno integration
- Verify multi-agent team executes
- Verify all 4 agents contribute
- Verify deduplication working (copied vs fresh analysis)
- Track Agno-specific costs separately

---

## Test Configuration Management

### Service Configuration

**File**: `scripts/testing/integration/config/service_config.json`

```json
{
  "services": {
    "profiler": {
      "enabled": true,
      "config": {
        "model": "claude-3-haiku-20240307",
        "provider": "openrouter",
        "temperature": 0.7,
        "max_tokens": 1000
      },
      "observability": {
        "agentops_enabled": true,
        "litellm_enabled": true
      }
    },
    "opportunity": {
      "enabled": true,
      "config": {
        "scoring_method": "five_dimensional"
      },
      "observability": {
        "agentops_enabled": false,
        "litellm_enabled": false
      }
    },
    "monetization": {
      "enabled": true,
      "config": {
        "use_agno": true,
        "model": "openai/gpt-4o-mini",
        "deduplication_enabled": true
      },
      "observability": {
        "agentops_enabled": true,
        "litellm_enabled": true,
        "agno_tracing_enabled": true
      }
    },
    "trust": {
      "enabled": true,
      "config": {
        "validation_method": "six_dimensional"
      },
      "observability": {
        "agentops_enabled": false,
        "litellm_enabled": false
      }
    },
    "market_validation": {
      "enabled": true,
      "config": {
        "jina_api_key": "${JINA_API_KEY}",
        "max_searches": 3
      },
      "observability": {
        "agentops_enabled": true,
        "litellm_enabled": true
      }
    }
  },
  "storage": {
    "dlt_enabled": true,
    "merge_disposition": true,
    "table_name": "app_opportunities"
  },
  "observability": {
    "agentops": {
      "enabled": true,
      "api_key": "${AGENTOPS_API_KEY}",
      "export_traces": true,
      "export_path": "scripts/testing/integration/observability/agentops_traces"
    },
    "litellm": {
      "enabled": true,
      "log_level": "INFO",
      "export_logs": true,
      "export_path": "scripts/testing/integration/observability/litellm_logs"
    },
    "agno": {
      "enabled": true,
      "export_traces": true,
      "export_path": "scripts/testing/integration/observability/agno_traces"
    }
  }
}
```

### Test Submission Selection

**File**: `scripts/testing/integration/config/submissions_single.json`

```json
{
  "description": "Single high-quality submission for initial validation",
  "selection_criteria": {
    "reddit_score": ">= 50",
    "num_comments": ">= 10",
    "text_length": ">= 200",
    "problem_keywords": ">= 3"
  },
  "submissions": [
    {
      "submission_id": "abc123xyz",
      "title": "I hate manually tracking expenses across multiple bank accounts",
      "subreddit": "productivity",
      "reddit_score": 127,
      "num_comments": 43,
      "reason": "High quality, clear problem, active discussion, good for all services"
    }
  ]
}
```

**File**: `scripts/testing/integration/config/submissions_small_batch.json`

```json
{
  "description": "5 varied submissions for small batch testing",
  "selection_criteria": "Mixed quality levels to test all scenarios",
  "submissions": [
    {
      "submission_id": "high_001",
      "quality": "high",
      "reason": "High quality, all services should execute"
    },
    {
      "submission_id": "medium_001",
      "quality": "medium",
      "reason": "Medium quality, some services may skip"
    },
    {
      "submission_id": "low_001",
      "quality": "low",
      "reason": "Low quality, tests graceful degradation"
    },
    {
      "submission_id": "edge_long_text",
      "quality": "edge_case",
      "reason": "Very long text (>5000 chars), tests text handling"
    },
    {
      "submission_id": "edge_minimal",
      "quality": "edge_case",
      "reason": "Minimal data, tests required field validation"
    }
  ]
}
```

---

## Success Criteria (Detailed)

### Test 01: Single Submission Validation

**Must Pass**:
- ✅ All 5 services execute successfully
- ✅ All 30+ enrichment fields populated
- ✅ Processing time: 15-30 seconds
- ✅ Cost: $0.10-$0.20
- ✅ No unhandled exceptions
- ✅ Data stored in database

**Should Pass**:
- ✅ AgentOps session created
- ✅ LiteLLM costs tracked
- ✅ Agno traces exportable

### Test 02: Small Batch (5 Submissions)

**Must Pass**:
- ✅ 5/5 submissions processed
- ✅ Success rate: 100%
- ✅ Average field coverage: 90%+
- ✅ Total cost: $0.50-$1.00
- ✅ No crashes

**Should Pass**:
- ✅ Performance: 3-5 submissions/minute
- ✅ Memory: < 1GB peak

### Test 03: Monolith Equivalence ⭐ CRITICAL

**Must Pass**:
- ✅ **Field match rate: 95%+** (30+ fields compared)
- ✅ Numeric fields within tolerance:
  - opportunity_score: ±1.0
  - final_score: ±1.0
  - monetization_score: ±2.0
  - trust_score: ±2.0
  - market_validation_score: ±5.0
- ✅ Array fields match (order-independent):
  - core_functions
  - monetization_methods
  - trust_badges
- ✅ Exact match fields:
  - priority (HIGH/MEDIUM/LOW)
  - trust_level (GOLD/SILVER/BRONZE/BASIC)
  - profession

**Should Pass**:
- ✅ Performance within 20% of monolith
- ✅ Cost within 10% of monolith

**This is the GATE to Phase 9** - If this fails, we iterate until it passes.

### Test 04-05: Scale Testing

**Must Pass**:
- ✅ Medium (50): 48+/50 success rate (96%+)
- ✅ Large (200): 190+/200 success rate (95%+)
- ✅ Performance: 3-5 submissions/minute
- ✅ Memory: < 2GB peak
- ✅ No memory leaks

**Should Pass**:
- ✅ Cost averages < $0.15/submission
- ✅ Error rate < 5%

### Test 06: Error Recovery

**Must Pass**:
- ✅ Pipeline continues despite individual service failures
- ✅ Failed services logged clearly
- ✅ Partial enrichment stored
- ✅ Statistics track failures correctly

### Test 07: Storage Validation

**Must Pass**:
- ✅ DLT pipeline stores data correctly
- ✅ Merge disposition prevents duplicates
- ✅ Schema compatibility verified
- ✅ All fields stored with correct data types

### Test 08: Cost Monitoring

**Must Pass**:
- ✅ Average cost/submission: < $0.15
- ✅ Projected monthly cost (10K): < $1000
- ✅ Cost breakdown by service available
- ✅ Deduplication savings tracked

### Test 09: Observability

**Must Pass**:
- ✅ AgentOps sessions created for each run
- ✅ All AI calls tracked in AgentOps
- ✅ LiteLLM costs calculated correctly
- ✅ Agno traces exportable
- ✅ Traces include: model, cost, latency, errors

---

## Exit Criteria for Phase 8

Phase 8 is **COMPLETE** when:

1. ✅ **Tests 01-03 PASS** (proof of concept + monolith equivalence)
2. ✅ **Test 03 achieves 95%+ field match rate** (critical gate)
3. ✅ **Tests 04-05 PASS** (scale testing)
4. ✅ **Tests 06-09 PASS** (error recovery, storage, cost, observability)
5. ✅ **All success criteria met**
6. ✅ **Comprehensive testing report generated**

**THEN**: Proceed to Phase 9 (FastAPI Backend Development)

**IF ANY TEST FAILS**: Iterate, fix, re-test until all pass.

---

## Next Steps

1. **Confirm approach** with user
2. **Create Test 01** (single submission validation)
   - Script: `test_01_single_submission.py`
   - Config: `submissions_single.json`
   - Prompt: `test-01-single-submission-prompt.md`
3. **Submit to local AI** for testing
4. **Review results**, iterate if needed
5. **Proceed to Test 02-09** sequentially

**Estimated Total Duration**: 1-2 weeks
**Target Date**: Phase 8 complete by early December 2025
