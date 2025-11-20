# Phase 8: Full Pipeline Integration Testing

This directory contains the integration testing framework for validating the unified OpportunityPipeline produces functionally equivalent AI-enriched profiles as the monolithic scripts.

## Overview

**Goal**: Prove unified pipeline = monolith (95%+ field match rate on 30+ enrichment fields)

**Exit Criteria**: All 9 tests passing → Proceed to Phase 9 (FastAPI Backend Development)

## Directory Structure

```
scripts/testing/integration/
├── README.md                       # This file
├── config/                         # Test configurations
│   ├── test_config.py             # Configuration loader
│   ├── submissions_single.json    # 1 submission (Test 01)
│   ├── submissions_small_batch.json  # 5 submissions (Test 02)
│   ├── submissions_monolith_comparison.json  # 10 (Test 03)
│   ├── submissions_medium_batch.json  # 50 (Test 04)
│   ├── submissions_large_batch.json  # 200 (Test 05)
│   └── service_config.json        # Service enable/disable flags
├── tests/                          # Test scripts
│   ├── test_01_single_submission.py
│   ├── test_02_small_batch.py
│   ├── test_03_monolith_equivalence.py  # ⭐ CRITICAL
│   ├── test_04_medium_scale.py
│   ├── test_05_large_scale.py
│   ├── test_06_error_recovery.py
│   ├── test_07_storage_validation.py
│   ├── test_08_cost_monitoring.py
│   └── test_09_observability.py
├── utils/                          # Utilities
│   ├── metrics.py                 # Metrics collection
│   ├── reporting.py               # Report generation
│   ├── comparison.py              # Field comparison (Test 03)
│   ├── monolith_runner.py        # Monolith baseline helper
│   └── observability.py          # AgentOps/LiteLLM/Agno helpers
├── results/                        # Test run results (timestamped)
│   ├── test_01_single_submission/
│   ├── test_02_small_batch/
│   └── ...
├── monolith_baseline/             # Real monolith results
│   └── generate_baseline.sh
└── observability/                 # AgentOps/LiteLLM/Agno traces
    ├── agentops_traces/
    ├── litellm_logs/
    └── agno_traces/
```

## Quick Start

### Prerequisites

1. **Environment Setup**:
   ```bash
   # Ensure Supabase is running
   supabase status

   # Verify environment variables (.env.local)
   # Required: SUPABASE_URL, SUPABASE_KEY, OPENROUTER_API_KEY, JINA_API_KEY
   # Optional: AGENTOPS_API_KEY (for observability)
   ```

2. **Database Setup**:
   ```bash
   # Ensure submissions table has test data
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM submission;"
   ```

### Running Tests

**Test 01: Single Submission Validation**
```bash
python scripts/testing/integration/tests/test_01_single_submission.py
```

**Test 02: Small Batch (5 Submissions)**
```bash
python scripts/testing/integration/tests/test_02_small_batch.py
```

**Test 03: Monolith Equivalence ⭐ CRITICAL**
```bash
# Generate monolith baseline first
./scripts/testing/integration/monolith_baseline/generate_baseline.sh

# Run equivalence test
python scripts/testing/integration/tests/test_03_monolith_equivalence.py
```

**Other Tests**: Follow same pattern

### Viewing Results

Results are saved to `results/test_XX_name/run_YYYY-MM-DD_HH-MM-SS.json`

```bash
# View latest Test 01 results
cat results/test_01_single_submission/run_*.json | tail -1 | jq .

# List all Test 01 runs
ls -lt results/test_01_single_submission/
```

## Test Suite

| Test | Goal | Duration | Prerequisites |
|------|------|----------|---------------|
| 01 | Single submission validation | 30min | None |
| 02 | Small batch consistency | 1h | Test 01 PASSED |
| 03 | **Monolith equivalence** ⭐ | 6-8h | Test 02 PASSED |
| 04 | Medium scale (50) | 3-4h | **Test 03 PASSED** |
| 05 | Large scale (200) | 4-5h | Test 04 PASSED |
| 06 | Error recovery | 3-4h | Test 05 PASSED |
| 07 | Storage validation | 2-3h | Test 05 PASSED |
| 08 | Cost monitoring | 2-3h | Test 05 PASSED |
| 09 | Observability | 3-4h | Test 08 PASSED |

**Total Duration**: 30-38 hours (1-2 weeks)

## Success Criteria

### Per-Test Criteria

See individual test scripts or `docs/plans/unified-pipeline-refactoring/HANDOVER-PHASE-8-TESTING.md`

### Overall Phase 8 Criteria

- [ ] All 9 tests PASSED
- [ ] Test 03 achieved 95%+ field match rate (critical gate)
- [ ] All success criteria met
- [ ] Comprehensive testing reports generated

**THEN**: Proceed to Phase 9 (FastAPI Backend Development)

## Observability

All tests integrate with observability tools:

- **AgentOps**: Tracks all AI agent executions
  - Sessions: `observability/agentops_traces/`
  - Metrics: cost, latency, errors

- **LiteLLM**: Unified LLM cost tracking
  - Logs: `observability/litellm_logs/`
  - Metrics: cost by provider, tokens used

- **Agno**: Multi-agent monetization tracing
  - Traces: `observability/agno_traces/`
  - Metrics: agent contributions, deduplication rate

## Configuration

### Service Configuration

Edit `config/service_config.json` to:
- Enable/disable individual services
- Adjust thresholds
- Configure observability
- Set cost budgets

### Submission Selection

Edit submission config files to:
- Select specific submissions for testing
- Define selection criteria
- Document submission quality levels

## Troubleshooting

**Test fails with "No submissions found"**:
- Update `config/submissions_*.json` with real submission IDs from database
- Or use `--submission-id` argument

**Service initialization fails**:
- Check API keys in `.env.local`
- Verify service dependencies installed
- Check `config/service_config.json`

**Cost exceeds budget**:
- Review `service_config.json` cost settings
- Check observability logs for unexpected AI calls
- Consider disabling expensive services for testing

**AgentOps/LiteLLM not working**:
- Verify API keys set
- Check `config/service_config.json` observability settings
- Review observability exports in `observability/`

## Documentation

- **Testing Framework**: `docs/plans/unified-pipeline-refactoring/PHASE-8-FULL-PIPELINE-TESTING-FRAMEWORK.md`
- **Progress Tracking**: `docs/plans/unified-pipeline-refactoring/HANDOVER-PHASE-8-TESTING.md`
- **Test Prompts**: `docs/plans/unified-pipeline-refactoring/prompts/integration-testing/`
- **Test Reports**: `docs/plans/unified-pipeline-refactoring/local-ai-report/integration-testing/`

## Contributing

When adding new tests:
1. Follow naming convention: `test_XX_descriptive_name.py`
2. Create corresponding config file if needed
3. Add testing prompt to `docs/plans/.../prompts/integration-testing/`
4. Update `HANDOVER-PHASE-8-TESTING.md` with test details
5. Document success criteria clearly

---

**Last Updated**: 2025-11-20
**Status**: Test 01 Implementation Complete, Ready for Testing
