# Phase 7 Part 3: Integration & Validation - Local Testing Prompt

**Branch**: `claude/review-pipeline-handover-01Jm26EM3B94UGjpV5xR3bxc`
**Commit**: [latest commit]
**Task**: Validate storage layer with schema migration and integration tests
**Date**: 2025-11-19

---

## Context

This phase validates the storage layer with schema evolution tests and enrichment pipeline integration tests. Parts 1 and 2 have been thoroughly tested with real database, so Part 3 focuses on validation and integration scenarios.

**Phase 7 Part 3 Created:**
1. ✅ **Schema Migration Tests** - Validates DLT schema evolution
2. ✅ **Integration Tests** - Validates storage works with enrichment pipeline

**Files Created:**
- `tests/test_schema_migration.py` (~400 lines, 9 tests)
- `tests/test_storage_integration.py` (~400 lines, 11 tests)

**Risk Level**: 🟢 LOW (validation tests with mocks)

---

## Testing Instructions

### Step 1: Pull Latest Changes

```bash
git checkout claude/review-pipeline-handover-01Jm26EM3B94UGjpV5xR3bxc
git pull origin claude/review-pipeline-handover-01Jm26EM3B94UGjpV5xR3bxc
```

### Step 2: Verify Phase 7 Part 3 Files

```bash
ls -lh tests/test_schema_migration.py
ls -lh tests/test_storage_integration.py
```

**Expected Output**:
```
tests/test_schema_migration.py      (~15 KB) - 9 schema evolution tests
tests/test_storage_integration.py   (~16 KB) - 11 integration tests
```

### Step 3: Run Schema Migration Tests

```bash
uv run pytest tests/test_schema_migration.py -v --tb=short
```

**Expected Output**: All 9 tests should pass

**Test Categories**:
1. **Schema Evolution** (4 tests)
   - Add column to existing schema
   - Merge disposition prevents duplicates
   - Schema backward compatibility
   - Multiple schema versions coexist

2. **Data Integrity** (3 tests)
   - Concurrent writes no data loss
   - Batch operation atomicity
   - Invalid data filtered before storage

3. **Performance** (2 tests)
   - Batch size optimization
   - Statistics overhead minimal

**Success Criteria**: All 9 tests PASS

### Step 4: Run Integration Tests

```bash
uv run pytest tests/test_storage_integration.py -v --tb=short
```

**Expected Output**: All 11 tests should pass

**Test Categories**:
1. **Enrichment Pipeline Integration** (4 tests)
   - Opportunity enrichment to storage
   - Trust validation to storage
   - Full pipeline enrichment to storage
   - Batch enrichment storage

2. **Multi-Service Coordination** (2 tests)
   - Shared loader across services
   - Sequential enrichment stages

3. **Error Handling** (2 tests)
   - Partial enrichment failure recovery
   - Enrichment service timeout handling

4. **End-to-End Data Flow** (1 test)
   - Complete enrichment pipeline

**Success Criteria**: All 11 tests PASS

### Step 5: Run All Storage Tests Together

```bash
uv run pytest tests/test_dlt_loader.py tests/test_storage_services.py tests/test_schema_migration.py tests/test_storage_integration.py -v --tb=short
```

**Expected Output**: All tests should pass

**Total Test Count**:
- DLTLoader tests: 32 tests (from Part 1)
- Storage services tests: 34 tests (from Part 2)
- Schema migration tests: 9 tests (Part 3)
- Integration tests: 11 tests (Part 3)
- **Total**: 86 tests

**Success Criteria**: All 86 tests PASS

### Step 6: Verify Test Coverage

```bash
uv run pytest tests/test_dlt_loader.py tests/test_storage_services.py tests/test_schema_migration.py tests/test_storage_integration.py --cov=core.storage --cov-report=term-missing
```

**Expected Coverage**: > 85%

---

## Validation Checklist

### Implementation Validation
- [ ] Schema migration tests created (9 tests)
- [ ] Integration tests created (11 tests)
- [ ] All new tests pass
- [ ] No regressions in existing tests

### Schema Evolution Validation
- [ ] Add column tests pass
- [ ] Merge disposition prevents duplicates
- [ ] Backward compatibility works
- [ ] Multiple schema versions coexist

### Integration Validation
- [ ] Storage works with enrichment pipeline pattern
- [ ] Shared DLTLoader works across services
- [ ] Sequential enrichment stages work
- [ ] Error handling comprehensive

### Quality Validation
- [ ] Test coverage maintained > 85%
- [ ] All 86 tests pass
- [ ] No test failures or warnings
- [ ] Code quality maintained

---

## Success Criteria

### Phase 7 Part 3 Complete When:
1. ✅ **All 9 schema migration tests pass**
2. ✅ **All 11 integration tests pass**
3. ✅ **No regressions** in Parts 1 & 2 tests
4. ✅ **Total test count: 86 tests** (32 + 34 + 9 + 11)
5. ✅ **Test coverage > 85%**

---

## Troubleshooting

### Issue: Import errors

**Solution**:
```bash
# Verify Python path
python3 -c "import sys; print(sys.path)"

# Test imports
python3 -c "from core.storage import DLTLoader, OpportunityStore, ProfileStore, HybridStore; print('OK')"
```

### Issue: Tests fail with mock errors

**Investigation**:
1. Check mock setup in test files
2. Verify DLT module mocking correct
3. Review test assertions

---

## Reporting Results

### Test Summary Format

```
PHASE 7 PART 3 TESTING REPORT

Branch: claude/review-pipeline-handover-01Jm26EM3B94UGjpV5xR3bxc
Commit: [commit hash]
Date: [test date]
Tester: [local AI]

RESULTS:

Schema Migration Tests:
- Total Tests: 9
- Passed: [X]
- Failed: [Y]
- Status: [PASS/FAIL]

Integration Tests:
- Total Tests: 11
- Passed: [X]
- Failed: [Y]
- Status: [PASS/FAIL]

Combined Test Suite:
- Total Tests: 86 (32 + 34 + 9 + 11)
- Passed: [X]
- Failed: [Y]
- Coverage: [X]%
- Status: [PASS/FAIL]

ISSUES FOUND:
[List any issues]

FIXES APPLIED:
[List any fixes]

PHASE 7 STATUS:
- Part 1: [COMPLETE]
- Part 2: [COMPLETE]
- Part 3: [COMPLETE/PENDING]

NEXT STEPS:
[Phase 8 or additional work needed]
```

### Save Report To:
`docs/plans/unified-pipeline-refactoring/local-ai-report/phase-7-part-3-testing-report.md`

---

## Phase 7 Complete

After Part 3 testing succeeds:

**Phase 7 Achievement**: Complete storage layer extraction
- ✅ Part 1: DLT Loader Foundation (32 tests)
- ✅ Part 2: Storage Services (34 tests)
- ✅ Part 3: Integration & Validation (20 tests)
- ✅ **Total**: 86 comprehensive tests
- ✅ **Production Ready**: Robust, tested, documented

**Next Phase**: Phase 8 - Create Unified Orchestrator

---

**End of Testing Prompt**

*Generated: 2025-11-19*
*Phase: 7 Part 3 - Integration & Validation*
*Status: Code complete, awaiting local AI execution*
