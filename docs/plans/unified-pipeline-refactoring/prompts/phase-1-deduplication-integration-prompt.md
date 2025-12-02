# Local AI Agent Testing Instructions - Phase 1: Deduplication Integration

## Context

Phase 1 of the deduplication integration has been completed and pushed to branch `claude/review-pipeline-handover-018wChYNQXVLhN6HdDn3omBV`. Your task is to validate the deduplication logic integration locally.

## What Was Done

A remote AI agent integrated deduplication logic into the unified pipeline orchestrator to enable cost-saving analysis reuse:

- ✅ Added batch concept metadata fetching (2 queries vs N×3 queries)
- ✅ Implemented deduplication check before enrichment
- ✅ Created copy logic with evidence chaining (Agno → Profiler)
- ✅ Added deduplication statistics tracking (copied, dedup_rate, cost_saved)
- ✅ Updated enrichment loop with copy-or-analyze logic
- ✅ **1 file modified** (`core/pipeline/orchestrator.py`, +150 lines)
- ✅ **1 test file created** (`tests/test_pipeline_deduplication.py`, ~500 lines)
- ✅ **Expected cost savings**: $3,528-$6,300/year (70% deduplication rate)

## Your Task

### Step 1: Pull the Changes

```bash
git fetch origin
git checkout claude/review-pipeline-handover-018wChYNQXVLhN6HdDn3omBV
git pull
```

### Step 2: Verify Environment

```bash
# Ensure Python environment is active
source .venv/bin/activate

# Verify Supabase is running
supabase status

# Expected output: API URL, DB URL, Studio URL
```

### Step 3: Run Phase 1 Unit Tests

```bash
# Run the new deduplication tests
pytest tests/test_pipeline_deduplication.py -v

# Expected: ~20 tests should pass
```

**Expected Test Output:**
```
tests/test_pipeline_deduplication.py::TestBatchFetchConceptMetadata::test_batch_fetch_with_existing_concepts PASSED
tests/test_pipeline_deduplication.py::TestBatchFetchConceptMetadata::test_batch_fetch_with_no_concepts PASSED
tests/test_pipeline_deduplication.py::TestBatchFetchConceptMetadata::test_batch_fetch_without_supabase_client PASSED
tests/test_pipeline_deduplication.py::TestBatchFetchConceptMetadata::test_batch_fetch_with_database_error PASSED
tests/test_pipeline_deduplication.py::TestCopyExistingEnrichment::test_copy_both_services_success PASSED
tests/test_pipeline_deduplication.py::TestCopyExistingEnrichment::test_copy_agno_only PASSED
tests/test_pipeline_deduplication.py::TestCopyExistingEnrichment::test_copy_profiler_only PASSED
tests/test_pipeline_deduplication.py::TestCopyExistingEnrichment::test_copy_failure_returns_none PASSED
tests/test_pipeline_deduplication.py::TestDeduplicationStatistics::test_stats_include_copied_field PASSED
tests/test_pipeline_deduplication.py::TestDeduplicationStatistics::test_summary_includes_dedup_metrics PASSED
tests/test_pipeline_deduplication.py::TestDeduplicationStatistics::test_cost_savings_calculation PASSED
tests/test_pipeline_deduplication.py::TestDeduplicationStatistics::test_reset_statistics_includes_copied PASSED
tests/test_pipeline_deduplication.py::TestDeduplicationIntegration::test_pipeline_uses_deduplication PASSED
tests/test_pipeline_deduplication.py::TestDeduplicationIntegration::test_dedup_rate_calculation_edge_cases PASSED
tests/test_pipeline_deduplication.py::TestEvidenceChaining::test_agno_executes_before_profiler PASSED
tests/test_pipeline_deduplication.py::TestEvidenceChaining::test_evidence_extraction_from_agno PASSED

======================== 16 passed ========================
```

### Step 4: Run All Pipeline Tests

```bash
# Verify no regressions in existing pipeline tests
pytest tests/test_orchestrator.py -v

# Should pass without errors
```

### Step 5: Test Code Quality

```bash
# Run linting on modified files
ruff check core/pipeline/orchestrator.py tests/test_pipeline_deduplication.py

# Run formatting check
ruff format --check core/pipeline/orchestrator.py tests/test_pipeline_deduplication.py
```

**Expected**: No linting errors, code properly formatted

### Step 6: Integration Test with Real Database (Optional)

```bash
# Create a simple integration test script
python -c "
from core.pipeline import OpportunityPipeline, PipelineConfig, DataSource
from config.settings import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

config = PipelineConfig(
    data_source=DataSource.DATABASE,
    limit=5,
    enable_profiler=True,
    enable_monetization=True,
    supabase_client=supabase,
    dry_run=True
)

pipeline = OpportunityPipeline(config)
result = pipeline.run()

print(f'Fetched: {result[\"stats\"][\"fetched\"]}')
print(f'Analyzed: {result[\"stats\"][\"analyzed\"]}')
print(f'Copied: {result[\"stats\"][\"copied\"]}')
print(f'Dedup Rate: {result[\"summary\"][\"dedup_rate\"]}%')
print(f'Cost Saved: \${result[\"summary\"][\"cost_saved\"]}')
"
```

**Expected Output:**
```
Fetched: 5
Analyzed: X (depending on existing data)
Copied: Y (depending on existing data)
Dedup Rate: Z%
Cost Saved: $N.NN
```

## What to Report Back

Please report in `docs/plans/unified-pipeline-refactoring/local-ai-report/phase-1-deduplication-integration-report.md`:

### Test Results
1. ✅ **Unit Tests**: Did all 16 deduplication tests pass?
2. ✅ **Regression Tests**: Do existing orchestrator tests still pass?
3. ✅ **Code Quality**: Any linting errors?
4. ✅ **Integration Test**: Does the pipeline run without errors?

### Deduplication Metrics
5. 📊 **Batch Query Performance**: Were concept metadata queries batched correctly?
6. 📊 **Copy Statistics**: Were copied submissions tracked in stats?
7. 📊 **Cost Savings**: Was cost_saved calculated correctly?
8. 📊 **Dedup Rate**: Was deduplication rate calculated correctly?

### Evidence Chaining
9. 🔗 **Agno → Profiler Order**: Was execution order preserved?
10. 🔗 **Evidence Extraction**: Was Agno evidence extracted for Profiler?

### Issues Found
11. ⚠️ **Test Failures**: Any tests failed? Provide error details
12. ⚠️ **Import Errors**: Any missing dependencies?
13. ⚠️ **Logic Errors**: Any unexpected behavior?

## If Tests Fail

If any tests fail, provide:
1. **Full test output** with error messages
2. **Stack traces** for failing tests
3. **Python version**: `python --version`
4. **Pytest version**: `pytest --version`
5. **Database state**: Any relevant data from Supabase

## Key Files Modified

Phase 1 changes:

- `core/pipeline/orchestrator.py` - Deduplication integration
  - `_batch_fetch_concept_metadata()` - Batch query optimization
  - `_copy_existing_enrichment()` - Copy logic with evidence chaining
  - Updated enrichment loop with deduplication checks
  - Added deduplication statistics (copied, dedup_rate, cost_saved)

- `tests/test_pipeline_deduplication.py` - Comprehensive test suite
  - TestBatchFetchConceptMetadata (4 tests)
  - TestCopyExistingEnrichment (4 tests)
  - TestDeduplicationStatistics (4 tests)
  - TestDeduplicationIntegration (2 tests)
  - TestEvidenceChaining (2 tests)

## Architecture Changes

### Before Phase 1:
```
Fetch → Filter → Enrich (ALWAYS call AI) → Store
Cost: $0.075 per submission
```

### After Phase 1:
```
Fetch → Filter → Dedup Check → Copy OR Enrich → Store
                      ↓             ↓
                  Existing?    Fresh Analysis
                   ($0)         ($0.075)
```

## Critical Validation Points

1. **Batch Queries**: Verify that `_batch_fetch_concept_metadata` reduces queries from N×3 to 2
2. **Evidence Chaining**: Verify that Agno executes BEFORE Profiler in `_copy_existing_enrichment`
3. **Cost Tracking**: Verify that `cost_saved = copied × 0.075`
4. **Fallback Logic**: Verify that failed copy falls back to fresh analysis

## Success Criteria

✅ **Functional Requirements**:
- [ ] All 16 unit tests pass
- [ ] No regressions in existing tests
- [ ] Pipeline runs without errors
- [ ] Deduplication statistics tracked correctly

✅ **Performance Requirements**:
- [ ] Batch queries reduce database load
- [ ] Copy operations complete quickly (< 50ms)
- [ ] No significant performance degradation

✅ **Cost Requirements**:
- [ ] Cost savings calculated correctly
- [ ] Deduplication rate reported accurately
- [ ] Copy vs analyze distinction clear

## Next Steps After Validation

Once you confirm all tests pass:

**Phase 2: Trust Data Preservation** (Ready to implement)
- Pre-fetch existing trust data before updates
- Merge trust data with AI enrichment
- Prevent trust data loss on re-enrichment
- Timeline: 2-3 hours

---

**Phase 1 Status**: ✅ COMPLETE (awaiting local validation)
**Risk Level**: 🟡 MEDIUM (modifies core orchestrator logic)
**Expected Impact**: $3,528-$6,300/year cost savings
**Branch**: `claude/review-pipeline-handover-018wChYNQXVLhN6HdDn3omBV`
**Files Modified**: 1 file modified, 1 test file created, +650 lines total
