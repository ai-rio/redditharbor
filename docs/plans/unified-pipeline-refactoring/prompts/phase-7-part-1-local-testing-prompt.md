# Phase 7 Part 1: DLT Loader Foundation - Local Testing Prompt

**Branch**: `claude/review-pipeline-handover-01Jm26EM3B94UGjpV5xR3bxc`
**Commit**: [latest commit]
**Task**: Extract DLT loading logic into unified DLTLoader class
**Date**: 2025-11-19

---

## Context

This phase creates the foundation of the storage layer by extracting scattered DLT loading logic into a unified `DLTLoader` class. This replaces ~200 lines of duplicated DLT code in monolithic scripts.

**Phase 7 Part 1 Created:**
1. ✅ **DLTLoader class** - Unified DLT loading infrastructure (464 lines)
2. ✅ **LoadStatistics** - Statistics tracking for loads
3. ✅ **Comprehensive tests** - 40+ tests covering all functionality

**Key Features:**
- Unified interface for all DLT loading operations
- Automatic merge disposition handling (prevents duplicates)
- Statistics tracking (loaded, failed, skipped records)
- Error handling with detailed logging
- Pipeline caching for performance
- Batch loading support

**Files Created:**
- `core/storage/dlt_loader.py` (464 lines)
- `core/storage/__init__.py` (module exports)
- `tests/test_dlt_loader.py` (600+ lines, 40+ tests)

**Risk Level**: 🔴 HIGH (data integrity risk - DLT loads to database)

---

## Testing Instructions

### Step 1: Pull Latest Changes

```bash
git checkout claude/review-pipeline-handover-01Jm26EM3B94UGjpV5xR3bxc
git pull origin claude/review-pipeline-handover-01Jm26EM3B94UGjpV5xR3bxc
```

### Step 2: Verify Phase 7 Part 1 Files

```bash
# Check DLTLoader implementation
ls -lh core/storage/dlt_loader.py

# Check tests
ls -lh tests/test_dlt_loader.py

# Check module exports
cat core/storage/__init__.py
```

**Expected Output**:
```
core/storage/dlt_loader.py     (~18 KB) - DLTLoader + LoadStatistics
tests/test_dlt_loader.py       (~24 KB) - 40+ comprehensive tests
core/storage/__init__.py       (~400 bytes) - Module exports
```

### Step 3: Test Module Imports

```bash
python3 << 'EOF'
from core.storage import DLTLoader, LoadStatistics

print("✓ Imports successful")
print(f"  - DLTLoader: {DLTLoader}")
print(f"  - LoadStatistics: {LoadStatistics}")

# Test instantiation
loader = DLTLoader()
print(f"✓ DLTLoader instantiated")
print(f"  - Destination: {loader.destination}")
print(f"  - Dataset: {loader.dataset_name}")
print(f"  - Connection: {loader.connection_string}")

EOF
```

**Expected Output**:
```
✓ Imports successful
  - DLTLoader: <class 'core.storage.dlt_loader.DLTLoader'>
  - LoadStatistics: <class 'core.storage.dlt_loader.LoadStatistics'>
✓ DLTLoader instantiated
  - Destination: postgres
  - Dataset: public
  - Connection: postgresql://postgres:postgres@127.0.0.1:54322/postgres
```

---

## Test Execution

### Step 4: Run DLTLoader Unit Tests

```bash
uv run pytest tests/test_dlt_loader.py -v --tb=short
```

**Expected Output**: All tests should pass (40+ tests)

**Test Categories**:
1. **Initialization Tests** (4 tests)
   - Default configuration
   - Custom destination and dataset
   - Custom connection string
   - Statistics initialization

2. **LoadStatistics Tests** (7 tests)
   - Success tracking
   - Failure tracking
   - Skip tracking
   - Summary generation
   - Success rate calculation
   - Reset functionality

3. **load() Method Tests** (9 tests)
   - Basic success
   - Merge disposition
   - Replace disposition
   - Append disposition
   - Empty data handling
   - Missing primary key error
   - DLT error handling
   - Statistics updates

4. **load_batch() Tests** (4 tests)
   - Batch loading success
   - Batch loading with failures
   - Empty data
   - Small batch sizes

5. **Pipeline Caching Tests** (3 tests)
   - Pipeline reuse
   - Different tables get different pipelines
   - Cache clearing

6. **Statistics Methods Tests** (2 tests)
   - get_statistics()
   - reset_statistics()

7. **Integration Tests** (2 tests)
   - Full workflow with merge
   - Multiple table loads

8. **Edge Cases** (4 tests)
   - Single record
   - Large dataset
   - Custom pipeline names

**Success Criteria**: All 40+ tests PASS

### Step 5: Test DLTLoader with Real Database (CRITICAL)

⚠️ **IMPORTANT**: This tests actual DLT loading to the database!

```bash
python3 << 'EOF'
from core.storage import DLTLoader
from core.dlt import PK_SUBMISSION_ID
import time

print("=" * 80)
print("TESTING DLTLOADER WITH REAL DATABASE")
print("=" * 80)

# Initialize loader
loader = DLTLoader(dataset_name="public")

# Create test data
test_opportunities = [
    {
        "submission_id": f"dlt_test_{int(time.time())}_{i}",
        "title": f"Test Opportunity {i}",
        "problem_description": "Testing DLTLoader",
        "app_concept": "Test App",
        "core_functions": '["Feature 1", "Feature 2"]',
        "final_score": 75.0 + i,
    }
    for i in range(5)
]

print(f"\n📊 Test Data: {len(test_opportunities)} records")
print(f"  Sample: {test_opportunities[0]['submission_id']}")

# Test 1: Load with merge disposition
print("\n--- Test 1: Merge Load ---")
success = loader.load(
    data=test_opportunities,
    table_name="app_opportunities",
    write_disposition="merge",
    primary_key=PK_SUBMISSION_ID
)

print(f"  Success: {success}")
print(f"  Statistics: {loader.get_statistics()}")

assert success is True, "Load should succeed"
assert loader.stats.loaded == 5, "Should load 5 records"

# Test 2: Load duplicate (should merge, not duplicate)
print("\n--- Test 2: Duplicate Load (Merge Test) ---")
duplicate = [test_opportunities[0]]  # Load first record again

success2 = loader.load(
    data=duplicate,
    table_name="app_opportunities",
    write_disposition="merge",
    primary_key=PK_SUBMISSION_ID
)

print(f"  Success: {success2}")
print(f"  Statistics: {loader.get_statistics()}")

assert success2 is True, "Duplicate load should succeed"
assert loader.stats.loaded == 6, "Should track 6 total loads"

# Test 3: Batch loading
print("\n--- Test 3: Batch Load ---")
loader.reset_statistics()

batch_results = loader.load_batch(
    data=test_opportunities,
    table_name="app_opportunities",
    primary_key=PK_SUBMISSION_ID,
    batch_size=2
)

print(f"  Total Records: {batch_results['total_records']}")
print(f"  Batches: {batch_results['batches']}")
print(f"  Success Rate: {batch_results['success_rate'] * 100:.1f}%")

assert batch_results['successful_batches'] == batch_results['batches'], "All batches should succeed"

# Test 4: Statistics accuracy
print("\n--- Test 4: Statistics Tracking ---")
stats = loader.get_statistics()
print(f"  Loaded: {stats['loaded']}")
print(f"  Failed: {stats['failed']}")
print(f"  Success Rate: {stats['success_rate'] * 100:.1f}%")

assert stats['success_rate'] == 1.0, "Success rate should be 100%"

print("\n" + "=" * 80)
print("✓ ALL REAL DATABASE TESTS PASSED")
print("=" * 80)

EOF
```

**Expected Output**:
```
================================================================================
TESTING DLTLOADER WITH REAL DATABASE
================================================================================

📊 Test Data: 5 records
  Sample: dlt_test_1700000000_0

--- Test 1: Merge Load ---
  Success: True
  Statistics: {'loaded': 5, 'failed': 0, ...}

--- Test 2: Duplicate Load (Merge Test) ---
  Success: True
  Statistics: {'loaded': 6, 'failed': 0, ...}

--- Test 3: Batch Load ---
  Total Records: 5
  Batches: 3
  Success Rate: 100.0%

--- Test 4: Statistics Tracking ---
  Loaded: 5
  Failed: 0
  Success Rate: 100.0%

================================================================================
✓ ALL REAL DATABASE TESTS PASSED
================================================================================
```

**Success Criteria**:
- All database loads succeed
- Merge disposition prevents duplicates (check database)
- Batch loading works correctly
- Statistics accurately track operations

### Step 6: Verify No Duplicates in Database

```bash
python3 << 'EOF'
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Check for duplicates in app_opportunities
result = client.rpc(
    "exec_sql",
    {"query": """
        SELECT submission_id, COUNT(*) as count
        FROM app_opportunities
        WHERE submission_id LIKE 'dlt_test_%'
        GROUP BY submission_id
        HAVING COUNT(*) > 1
    """}
).execute()

if result.data:
    print(f"❌ DUPLICATES FOUND: {len(result.data)} duplicate records")
    for dup in result.data:
        print(f"  - {dup['submission_id']}: {dup['count']} copies")
else:
    print("✓ No duplicates found - Merge disposition working correctly")

EOF
```

**Expected Output**:
```
✓ No duplicates found - Merge disposition working correctly
```

### Step 7: Test Pipeline Caching

```bash
python3 << 'EOF'
from core.storage import DLTLoader

loader = DLTLoader()

# Check initial cache state
print(f"Initial cache size: {len(loader._pipeline_cache)}")

# Load to table1 (creates pipeline)
loader.load(
    data=[{"id": "test1"}],
    table_name="test_cache_1",
    write_disposition="append"
)
print(f"After load 1: {len(loader._pipeline_cache)} pipeline(s)")

# Load to same table (should reuse pipeline)
loader.load(
    data=[{"id": "test2"}],
    table_name="test_cache_1",
    write_disposition="append"
)
print(f"After load 2 (same table): {len(loader._pipeline_cache)} pipeline(s)")

# Load to different table (creates new pipeline)
loader.load(
    data=[{"id": "test3"}],
    table_name="test_cache_2",
    write_disposition="append"
)
print(f"After load 3 (new table): {len(loader._pipeline_cache)} pipeline(s)")

# Clear cache
loader.clear_pipeline_cache()
print(f"After clear: {len(loader._pipeline_cache)} pipeline(s)")

assert len(loader._pipeline_cache) == 0, "Cache should be empty after clear"

print("\n✓ Pipeline caching working correctly")

EOF
```

**Expected Output**:
```
Initial cache size: 0
After load 1: 1 pipeline(s)
After load 2 (same table): 1 pipeline(s)
After load 3 (new table): 2 pipeline(s)
After clear: 0 pipeline(s)

✓ Pipeline caching working correctly
```

### Step 8: Test Error Handling

```bash
python3 << 'EOF'
from core.storage import DLTLoader

loader = DLTLoader()

# Test 1: Empty data
print("Test 1: Empty data")
success = loader.load([], "test_table", "merge", "id")
print(f"  Result: {success}")
assert success is False, "Should return False for empty data"

# Test 2: Merge without primary key
print("\nTest 2: Merge without primary key")
try:
    loader.load([{"id": "test"}], "test_table", "merge")
    print("  ❌ Should have raised ValueError")
except ValueError as e:
    print(f"  ✓ Correctly raised ValueError: {e}")

# Test 3: Statistics after errors
print("\nTest 3: Statistics after empty data")
stats = loader.get_statistics()
print(f"  Failed: {stats['failed']}")
print(f"  Loaded: {stats['loaded']}")

print("\n✓ Error handling working correctly")

EOF
```

**Expected Output**:
```
Test 1: Empty data
  Result: False

Test 2: Merge without primary key
  ✓ Correctly raised ValueError: primary_key required for merge

Test 3: Statistics after empty data
  Failed: 0
  Loaded: 0

✓ Error handling working correctly
```

### Step 9: Integration with Existing DLT Constants

```bash
python3 << 'EOF'
from core.storage import DLTLoader
from core.dlt import (
    PK_SUBMISSION_ID,
    PK_OPPORTUNITY_ID,
    PK_COMMENT_ID,
    submission_resource_config,
    opportunity_resource_config
)

loader = DLTLoader()

print("Testing DLT Constants Integration")
print("=" * 60)

# Test with different primary keys
test_data = [
    (PK_SUBMISSION_ID, [{"submission_id": "test1", "title": "Test"}]),
    (PK_OPPORTUNITY_ID, [{"opportunity_id": "opp1", "score": 75}]),
    (PK_COMMENT_ID, [{"comment_id": "com1", "text": "Comment"}]),
]

for pk_constant, data in test_data:
    table_name = f"test_{pk_constant}"
    success = loader.load(
        data=data,
        table_name=table_name,
        write_disposition="merge",
        primary_key=pk_constant
    )
    print(f"✓ {pk_constant}: {success}")

print("\n✓ All DLT constants working correctly")

EOF
```

**Expected Output**:
```
Testing DLT Constants Integration
============================================================
✓ submission_id: True
✓ opportunity_id: True
✓ comment_id: True

✓ All DLT constants working correctly
```

### Step 10: Performance Validation

```bash
python3 << 'EOF'
from core.storage import DLTLoader
import time

loader = DLTLoader()

# Create larger dataset
large_dataset = [
    {
        "submission_id": f"perf_test_{i}",
        "title": f"Test {i}",
        "final_score": 75.0 + (i % 20),
    }
    for i in range(100)
]

print("Performance Test: Loading 100 records")
print("=" * 60)

start = time.time()
success = loader.load(
    data=large_dataset,
    table_name="app_opportunities",
    write_disposition="merge",
    primary_key="submission_id"
)
duration = time.time() - start

print(f"  Duration: {duration:.2f} seconds")
print(f"  Success: {success}")
print(f"  Records/sec: {len(large_dataset) / duration:.1f}")

# Performance criteria: < 5 seconds for 100 records (from Phase 7 spec)
assert duration < 5.0, f"Should complete in < 5s, took {duration:.2f}s"
assert success is True, "Should succeed"

print("\n✓ Performance within acceptable limits (< 5s for 100 records)")

EOF
```

**Expected Output**:
```
Performance Test: Loading 100 records
============================================================
  Duration: 2.34 seconds
  Success: True
  Records/sec: 42.7

✓ Performance within acceptable limits (< 5s for 100 records)
```

**Success Criteria**: Load 100 records in < 5 seconds

---

## Validation Checklist

### Implementation Validation
- [ ] DLTLoader class created with all methods
- [ ] LoadStatistics class created
- [ ] Module exports configured (`__init__.py`)
- [ ] All 40+ tests pass
- [ ] Code follows existing DLT patterns

### Functionality Validation
- [ ] Basic load() works with merge disposition
- [ ] load() works with replace disposition
- [ ] load() works with append disposition
- [ ] load_batch() splits data correctly
- [ ] Pipeline caching works (reuses pipelines)
- [ ] Statistics tracking accurate

### Data Integrity Validation (CRITICAL)
- [ ] Merge disposition prevents duplicates
- [ ] No duplicate records in database after test
- [ ] Primary key enforcement working
- [ ] Error handling prevents data loss

### Performance Validation
- [ ] 100 records load in < 5 seconds
- [ ] Pipeline caching improves performance
- [ ] Batch loading more efficient than individual loads

### Integration Validation
- [ ] Works with core.dlt constants (PK_SUBMISSION_ID, etc.)
- [ ] Compatible with existing DLT resource configs
- [ ] Logs appropriately (INFO for success, ERROR for failures)

---

## Troubleshooting

### Issue: Tests fail with DLT import errors

**Cause**: DLT not installed or version mismatch

**Solution**:
```bash
uv pip install dlt
# or
pip install dlt
```

### Issue: Database connection errors

**Cause**: Supabase not running or wrong connection string

**Solution**:
```bash
# Check Supabase status
supabase status

# Start if not running
supabase start

# Verify connection string matches
python3 -c "from core.storage import DLTLoader; print(DLTLoader().connection_string)"
```

### Issue: Duplicate records found

**Cause**: Merge disposition not working correctly

**Investigation**:
1. Check primary key is set correctly
2. Verify write_disposition="merge"
3. Check DLT version (should be latest)
4. Review DLT logs for merge behavior

### Issue: Performance too slow

**Cause**: Database load, network latency, or inefficient batching

**Investigation**:
1. Check database CPU/memory usage
2. Test with smaller datasets first
3. Try different batch sizes
4. Check network latency to database

---

## Reporting Results

### Test Summary Format

```
PHASE 7 PART 1 TESTING REPORT

Branch: claude/review-pipeline-handover-01Jm26EM3B94UGjpV5xR3bxc
Commit: [commit hash]
Date: [test date]
Tester: [your name/local AI]

RESULTS:

Unit Tests:
- Total Tests: 40+
- Passed: [X]
- Failed: [Y]
- Status: [PASS/FAIL]

Real Database Tests:
- Load Success: [PASS/FAIL]
- Merge Deduplication: [PASS/FAIL]
- Batch Loading: [PASS/FAIL]
- Statistics Accuracy: [PASS/FAIL]

Data Integrity:
- Duplicates Found: [YES/NO]
- Records Loaded: [X]
- Merge Working: [YES/NO]

Performance:
- 100 Records Load Time: [X.XX] seconds
- Status: [PASS/FAIL if < 5s]

Integration:
- DLT Constants: [PASS/FAIL]
- Pipeline Caching: [PASS/FAIL]
- Error Handling: [PASS/FAIL]

ISSUES FOUND:
[List any failures, errors, or unexpected behavior]

FIXES APPLIED:
[List any fixes made during testing]

DATA INTEGRITY STATUS:
- No duplicate records: [YES/NO]
- All loads successful: [YES/NO]
- Statistics accurate: [YES/NO]

NEXT STEPS:
[Recommendations for Phase 7 Part 2 or additional work needed]
```

### Save Report To:
`docs/plans/unified-pipeline-refactoring/local-ai-report/phase-7-part-1-testing-report.md`

---

## Success Criteria

### Phase 7 Part 1 Complete When:
1. ✅ **All unit tests pass** (40+ tests)
2. ✅ **Real database loads work** (merge, replace, append)
3. ✅ **No duplicate records** in database after merge tests
4. ✅ **Performance acceptable** (< 5s for 100 records)
5. ✅ **Statistics tracking accurate**
6. ✅ **Pipeline caching working**
7. ✅ **Error handling comprehensive**
8. ✅ **Integration with DLT constants successful**

### Known Limitations:
- **load_with_resource()** tested with mocks (real resource testing in Part 2)
- **Schema evolution** tested conceptually (full testing in Part 3)
- **Storage services** not created yet (Part 2 task)

---

## Next Phase

After Phase 7 Part 1 completion and local AI testing report:

→ **Phase 7 Part 2: Storage Services**
- Create OpportunityStore
- Create ProfileStore
- Create HybridStore
- Integration with enrichment services

---

**End of Testing Prompt**

*Generated: 2025-11-19*
*Phase: 7 Part 1 - DLT Loader Foundation*
*Status: Code complete, awaiting local AI execution*
