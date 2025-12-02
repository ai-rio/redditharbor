# Local AI Agent Testing Instructions - Phase 2: Trust Data Preservation

## Context

Phase 2 of the deduplication integration has been completed and pushed to branch `claude/review-pipeline-handover-018wChYNQXVLhN6HdDn3omBV`. Your task is to validate trust data preservation logic locally.

## What Was Done

A remote AI agent implemented trust data preservation to prevent trust score loss when AI enrichment updates are made:

- ✅ Added `_fetch_existing_trust_data()` batch fetch method to HybridStore
- ✅ Integrated trust data preservation into `store()` method
- ✅ Added supabase_client parameter to HybridStore
- ✅ Updated orchestrator to pass supabase_client to HybridStore
- ✅ Added trust field definitions to APP_OPPORTUNITIES_COLUMNS
- ✅ Implemented merge logic: new values override, otherwise preserve
- ✅ **2 files modified** (`hybrid_store.py` +90 lines, `orchestrator.py` +1 line)
- ✅ **1 test file created** (`test_trust_data_preservation.py`, ~500 lines)

## Trust Fields Preserved

The following trust fields are now preserved across AI updates:
1. `trust_score` (double) - Overall trust rating
2. `trust_badge` (text) - Trust badge type (verified, new, etc.)
3. `activity_score` (double) - User activity score
4. `trust_level` (text) - Trust tier (high, medium, low)
5. `trust_badges` (JSONB) - Detailed trust badges

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

### Step 3: Run Phase 2 Unit Tests

```bash
# Run the new trust preservation tests
pytest tests/test_trust_data_preservation.py -v

# Expected: ~20 tests should pass
```

**Expected Test Output:**
```
tests/test_trust_data_preservation.py::TestFetchExistingTrustData::test_fetch_with_existing_data PASSED
tests/test_trust_data_preservation.py::TestFetchExistingTrustData::test_fetch_with_no_existing_data PASSED
tests/test_trust_data_preservation.py::TestFetchExistingTrustData::test_fetch_without_supabase_client PASSED
tests/test_trust_data_preservation.py::TestFetchExistingTrustData::test_fetch_with_empty_submission_list PASSED
tests/test_trust_data_preservation.py::TestFetchExistingTrustData::test_fetch_with_database_error PASSED
tests/test_trust_data_preservation.py::TestFetchExistingTrustData::test_fetch_with_partial_data PASSED
tests/test_trust_data_preservation.py::TestTrustDataPreservation::test_preserve_trust_on_ai_update PASSED
tests/test_trust_data_preservation.py::TestTrustDataPreservation::test_new_trust_overrides_existing PASSED
tests/test_trust_data_preservation.py::TestTrustDataPreservation::test_no_trust_preservation_without_client PASSED
tests/test_trust_data_preservation.py::TestTrustDataPreservation::test_partial_trust_fields_preserved PASSED
tests/test_trust_data_preservation.py::TestTrustDataIntegration::test_full_pipeline_with_trust_preservation PASSED
tests/test_trust_data_preservation.py::TestTrustDataIntegration::test_statistics_tracking_with_trust_preservation PASSED
tests/test_trust_data_preservation.py::TestEdgeCases::test_empty_trust_data_dict PASSED
tests/test_trust_data_preservation.py::TestEdgeCases::test_store_with_no_submissions PASSED
tests/test_trust_data_preservation.py::TestEdgeCases::test_mixed_submission_ids PASSED

======================== 15 passed ========================
```

### Step 4: Run All Storage Tests

```bash
# Verify no regressions in existing storage tests
pytest tests/test_hybrid_store.py -v

# Should pass without errors
```

### Step 5: Test Code Quality

```bash
# Run linting on modified files
ruff check core/storage/hybrid_store.py core/pipeline/orchestrator.py tests/test_trust_data_preservation.py

# Run formatting check
ruff format --check core/storage/hybrid_store.py core/pipeline/orchestrator.py tests/test_trust_data_preservation.py
```

**Expected**: No linting errors, code properly formatted

### Step 6: Integration Test with Real Database (Optional)

```bash
# Create a simple integration test script
python -c "
from core.storage.hybrid_store import HybridStore
from config.settings import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create HybridStore with client
store = HybridStore(supabase_client=supabase)

# Test trust data fetch
trust_data = store._fetch_existing_trust_data(['test_sub_001'])
print(f'Trust data fetched: {len(trust_data)} records')

# Test submission with trust preservation
submissions = [{
    'submission_id': 'test_' + str(hash('test') % 10000),
    'problem_description': 'Test problem',
    'app_concept': 'Test app',
    'opportunity_score': 75.0,
    'trust_score': 85.5,  # New trust data
}]

result = store.store(submissions)
print(f'Store result: {result}')
"
```

**Expected Output:**
```
Trust data fetched: 0 records (or N if data exists)
Store result: True
```

## What to Report Back

Please report in `docs/plans/unified-pipeline-refactoring/local-ai-report/phase-2-trust-preservation-report.md`:

### Test Results
1. ✅ **Unit Tests**: Did all 15 trust preservation tests pass?
2. ✅ **Regression Tests**: Do existing hybrid_store tests still pass?
3. ✅ **Code Quality**: Any linting errors?
4. ✅ **Integration Test**: Does the store work with trust preservation?

### Trust Preservation Metrics
5. 📊 **Fetch Performance**: Was trust data batched correctly?
6. 📊 **Merge Logic**: Were new values preferred over existing?
7. 📊 **Preservation Logic**: Were existing values preserved when new missing?
8. 📊 **Field Coverage**: Were all 5 trust fields handled?

### Edge Cases
9. 🔄 **No Client**: Did store work without supabase_client?
10. 🔄 **Empty Data**: Did empty trust data dict work?
11. 🔄 **Partial Fields**: Were partial trust fields preserved correctly?

### Issues Found
12. ⚠️ **Test Failures**: Any tests failed? Provide error details
13. ⚠️ **Import Errors**: Any missing dependencies?
14. ⚠️ **Logic Errors**: Any unexpected behavior?

## If Tests Fail

If any tests fail, provide:
1. **Full test output** with error messages
2. **Stack traces** for failing tests
3. **Python version**: `python --version`
4. **Pytest version**: `pytest --version`
5. **Database state**: Any relevant data from Supabase

## Key Files Modified

Phase 2 changes:

- `core/storage/hybrid_store.py` - Trust preservation implementation
  - `__init__()` - Added supabase_client parameter
  - `_fetch_existing_trust_data()` - NEW: Batch fetch trust data
  - `store()` - Modified to preserve trust data
  - `APP_OPPORTUNITIES_COLUMNS` - Added trust field definitions

- `core/pipeline/orchestrator.py` - Orchestrator integration
  - `_store_results()` - Pass supabase_client to HybridStore

- `tests/test_trust_data_preservation.py` - Comprehensive test suite
  - TestFetchExistingTrustData (6 tests)
  - TestTrustDataPreservation (4 tests)
  - TestTrustDataIntegration (2 tests)
  - TestEdgeCases (3 tests)

## Architecture Changes

### Before Phase 2:
```
AI Enrichment → Store → Database
                  ↓
            TRUST DATA LOST ❌
```

### After Phase 2:
```
AI Enrichment → Pre-fetch Trust → Merge → Store → Database
                       ↓             ↓
                  Existing        New + Old
                  Trust Data      Combined ✅
```

## Critical Validation Points

1. **Batch Fetching**: Verify `_fetch_existing_trust_data()` uses single query
2. **Merge Logic**: Verify new values override existing when provided
3. **Preservation Logic**: Verify existing values used when new values missing
4. **Graceful Degradation**: Verify store works without supabase_client
5. **Field Coverage**: Verify all 5 trust fields preserved

## Success Criteria

✅ **Functional Requirements**:
- [ ] All 15 unit tests pass
- [ ] No regressions in existing tests
- [ ] Store works with and without client
- [ ] Trust data preserved correctly

✅ **Performance Requirements**:
- [ ] Single batch query for trust data
- [ ] No significant performance degradation
- [ ] Fast trust data merging (< 10ms)

✅ **Data Integrity Requirements**:
- [ ] New trust values override existing
- [ ] Existing trust values preserved when new missing
- [ ] No trust data corruption
- [ ] Proper NULL handling

## Next Steps After Validation

Once you confirm all tests pass:

**Phase 3: Concept Metadata Tracking** (Ready to implement)
- Update concept flags after enrichment
- Track has_agno_analysis and has_profiler_analysis
- Enable future deduplication runs
- Timeline: 2 hours

---

**Phase 2 Status**: ✅ COMPLETE (awaiting local validation)
**Risk Level**: 🟢 LOW (isolated to storage layer)
**Expected Impact**: Prevents trust data loss on AI updates
**Branch**: `claude/review-pipeline-handover-018wChYNQXVLhN6HdDn3omBV`
**Files Modified**: 2 files modified, 1 test file created, +600 lines total

## Trust Preservation Flow

```
Submission with AI enrichment:
{
  "submission_id": "sub_001",
  "problem_description": "NEW",  // ← AI enrichment
  "app_concept": "NEW",           // ← AI enrichment
  "trust_score": null             // ← NO trust data
}

↓ Pre-fetch existing trust data

Existing trust data from database:
{
  "submission_id": "sub_001",
  "trust_score": 85.5,            // ← Existing
  "trust_badge": "verified",      // ← Existing
  "activity_score": 72.3          // ← Existing
}

↓ Merge logic

Final stored data:
{
  "submission_id": "sub_001",
  "problem_description": "NEW",  // ← AI enrichment (updated)
  "app_concept": "NEW",           // ← AI enrichment (updated)
  "trust_score": 85.5,            // ← PRESERVED ✅
  "trust_badge": "verified",      // ← PRESERVED ✅
  "activity_score": 72.3          // ← PRESERVED ✅
}
```

## Common Issues and Solutions

### Issue 1: Trust data not preserved
**Symptom**: Tests fail with trust_score = None
**Solution**: Verify supabase_client is passed to HybridStore

### Issue 2: Database connection errors
**Symptom**: _fetch_existing_trust_data() raises exceptions
**Solution**: Verify Supabase is running and accessible

### Issue 3: Mock configuration errors
**Symptom**: Tests fail with MagicMock attribute errors
**Solution**: Check mock chain configuration in tests

### Issue 4: Linting errors
**Symptom**: ruff reports import or formatting issues
**Solution**: Run `ruff format .` to auto-fix formatting

---

**Report Status**: Awaiting local AI validation
**Implementation Completeness**: 100% (full implementation)
**Testing Coverage**: Comprehensive (15 tests, 4 test classes)
**Documentation**: Complete with examples and flow diagrams
