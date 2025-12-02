# Phase 7 Part 2: Storage Services - Local Testing Prompt

**Branch**: `claude/review-pipeline-handover-01Jm26EM3B94UGjpV5xR3bxc`
**Commit**: [latest commit]
**Task**: Create storage service layer on top of DLTLoader foundation
**Date**: 2025-11-19

---

## Context

This phase creates three storage services on top of the DLTLoader foundation from Part 1:
- **OpportunityStore**: Manages app_opportunities table storage
- **ProfileStore**: Manages enriched submissions table storage
- **HybridStore**: Manages combined opportunity + profile storage

**Phase 7 Part 2 Created:**
1. ✅ **OpportunityStore** - Storage for AI-generated opportunity profiles
2. ✅ **ProfileStore** - Storage for enriched Reddit submissions
3. ✅ **HybridStore** - Storage for hybrid submissions (both pipelines)
4. ✅ **Comprehensive tests** - 55+ tests covering all three services

**Key Features:**
- High-level storage interface abstracting DLTLoader
- Automatic data validation and filtering
- Statistics tracking per service
- Batch processing support
- Integration with DLT constants

**Files Created:**
- `core/storage/opportunity_store.py` (~220 lines)
- `core/storage/profile_store.py` (~200 lines)
- `core/storage/hybrid_store.py` (~260 lines)
- `core/storage/__init__.py` (updated exports)
- `tests/test_storage_services.py` (~680 lines, 55 tests)

**Risk Level**: 🔴 HIGH (data integrity - storage to database)

---

## Testing Instructions

### Step 1: Pull Latest Changes

```bash
git checkout claude/review-pipeline-handover-01Jm26EM3B94UGjpV5xR3bxc
git pull origin claude/review-pipeline-handover-01Jm26EM3B94UGjpV5xR3bxc
```

### Step 2: Verify Phase 7 Part 2 Files

```bash
# Check storage services
ls -lh core/storage/*.py

# Check tests
ls -lh tests/test_storage_services.py
```

**Expected Output**:
```
core/storage/dlt_loader.py          (~18 KB) - DLTLoader from Part 1
core/storage/opportunity_store.py   (~6 KB) - OpportunityStore
core/storage/profile_store.py       (~5 KB) - ProfileStore
core/storage/hybrid_store.py        (~7 KB) - HybridStore
core/storage/__init__.py            (~800 bytes) - Module exports
tests/test_storage_services.py      (~22 KB) - 55 tests
```

### Step 3: Test Module Imports

```bash
python3 << 'EOF'
from core.storage import (
    DLTLoader,
    LoadStatistics,
    OpportunityStore,
    ProfileStore,
    HybridStore
)

print("✓ All imports successful")
print(f"  - DLTLoader: {DLTLoader}")
print(f"  - OpportunityStore: {OpportunityStore}")
print(f"  - ProfileStore: {ProfileStore}")
print(f"  - HybridStore: {HybridStore}")

# Test instantiation
opp_store = OpportunityStore()
profile_store = ProfileStore()
hybrid_store = HybridStore()

print("\n✓ All stores instantiated")
print(f"  - OpportunityStore table: {opp_store.table_name}")
print(f"  - ProfileStore table: {profile_store.table_name}")
print(f"  - HybridStore tables: {hybrid_store.opportunity_table}, {hybrid_store.profile_table}")

EOF
```

**Expected Output**:
```
✓ All imports successful
  - DLTLoader: <class 'core.storage.dlt_loader.DLTLoader'>
  - OpportunityStore: <class 'core.storage.opportunity_store.OpportunityStore'>
  - ProfileStore: <class 'core.storage.profile_store.ProfileStore'>
  - HybridStore: <class 'core.storage.hybrid_store.HybridStore'>

✓ All stores instantiated
  - OpportunityStore table: app_opportunities
  - ProfileStore table: submissions
  - HybridStore tables: app_opportunities, submissions
```

---

## Test Execution

### Step 4: Run Storage Services Unit Tests

```bash
uv run pytest tests/test_storage_services.py -v --tb=short
```

**Expected Output**: All tests should pass (55 tests)

**Test Categories**:
1. **OpportunityStore Tests** (13 tests)
   - Initialization (default, custom, no loader)
   - Successful storage
   - Empty data handling
   - Invalid data filtering
   - Partial data filtering
   - Load failure handling
   - Batch storage
   - Statistics tracking

2. **ProfileStore Tests** (8 tests)
   - Initialization (default, custom)
   - Successful storage
   - Empty data handling
   - Invalid data filtering
   - Batch storage
   - Load failure handling
   - Statistics tracking

3. **HybridStore Tests** (13 tests)
   - Initialization (default, custom)
   - Successful storage
   - Empty data handling
   - Invalid submission_id filtering
   - Data splitting (opportunity vs profile)
   - Partial failure handling
   - Complete failure handling
   - Batch storage
   - Profile-only submissions

4. **Integration Tests** (1 test)
   - All stores sharing same DLTLoader

**Success Criteria**: All 55 tests PASS

### Step 5: Test OpportunityStore with Real Database (CRITICAL)

⚠️ **IMPORTANT**: This tests actual storage to app_opportunities table!

```bash
python3 << 'EOF'
from core.storage import OpportunityStore
import time

print("=" * 80)
print("TESTING OPPORTUNITYSTORE WITH REAL DATABASE")
print("=" * 80)

# Initialize store
store = OpportunityStore()

# Create test opportunities
test_opportunities = [
    {
        "submission_id": f"store_test_opp_{int(time.time())}_{i}",
        "problem_description": f"Test problem {i}",
        "app_concept": f"Test app concept {i}",
        "core_functions": ["Feature 1", "Feature 2"],
        "value_proposition": "Test value prop",
        "target_user": "Test users",
        "monetization_model": "Subscription",
        "opportunity_score": 70.0 + i,
    }
    for i in range(3)
]

print(f"\n📊 Test Data: {len(test_opportunities)} opportunities")

# Test 1: Store opportunities
print("\n--- Test 1: Store Opportunities ---")
success = store.store(test_opportunities)
print(f"  Success: {success}")
print(f"  Statistics: {store.get_statistics()}")

assert success is True, "Store should succeed"
assert store.stats.loaded == 3, "Should load 3 opportunities"

# Test 2: Store duplicate (should merge, not duplicate)
print("\n--- Test 2: Duplicate Store (Merge Test) ---")
duplicate = [test_opportunities[0]]
success2 = store.store(duplicate)
print(f"  Success: {success2}")
print(f"  Statistics: {store.get_statistics()}")

assert success2 is True, "Duplicate store should succeed"

# Test 3: Batch storage
print("\n--- Test 3: Batch Store ---")
store.reset_statistics()
result = store.store_batch(test_opportunities, batch_size=2)
print(f"  Total Records: {result['total_records']}")
print(f"  Batches: {result['batches']}")
print(f"  Success Rate: {result['success_rate'] * 100:.1f}%")

assert result['successful_batches'] == result['batches'], "All batches should succeed"

print("\n" + "=" * 80)
print("✓ OPPORTUNITYSTORE TESTS PASSED")
print("=" * 80)

EOF
```

**Success Criteria**:
- All stores succeed
- No duplicate records created
- Statistics accurate

### Step 6: Test ProfileStore with Real Database (CRITICAL)

```bash
python3 << 'EOF'
from core.storage import ProfileStore
import time

print("=" * 80)
print("TESTING PROFILESTORE WITH REAL DATABASE")
print("=" * 80)

store = ProfileStore()

# Create test profiles
test_profiles = [
    {
        "submission_id": f"store_test_prof_{int(time.time())}_{i}",
        "title": f"Test submission {i}",
        "selftext": f"Test content {i}",
        "author": "test_user",
        "subreddit": "test",
        "trust_score": 80.0 + i,
        "opportunity_score": 75.0 + i,
    }
    for i in range(3)
]

print(f"\n📊 Test Data: {len(test_profiles)} profiles")

# Test 1: Store profiles
print("\n--- Test 1: Store Profiles ---")
success = store.store(test_profiles)
print(f"  Success: {success}")
print(f"  Statistics: {store.get_statistics()}")

assert success is True, "Store should succeed"
assert store.stats.loaded == 3, "Should load 3 profiles"

# Test 2: Batch storage
print("\n--- Test 2: Batch Store ---")
store.reset_statistics()
result = store.store_batch(test_profiles, batch_size=2)
print(f"  Batches: {result['batches']}")
print(f"  Success Rate: {result['success_rate'] * 100:.1f}%")

assert result['successful_batches'] == result['batches'], "All batches should succeed"

print("\n" + "=" * 80)
print("✓ PROFILESTORE TESTS PASSED")
print("=" * 80)

EOF
```

### Step 7: Test HybridStore with Real Database (CRITICAL)

```bash
python3 << 'EOF'
from core.storage import HybridStore
import time

print("=" * 80)
print("TESTING HYBRIDSTORE WITH REAL DATABASE")
print("=" * 80)

store = HybridStore()

# Create test hybrid submissions
test_hybrids = [
    {
        "submission_id": f"store_test_hybrid_{int(time.time())}_{i}",
        # Opportunity fields
        "problem_description": f"Test problem {i}",
        "app_concept": f"Test app {i}",
        "core_functions": ["Feature 1", "Feature 2"],
        "value_proposition": "Test value",
        "target_user": "Test users",
        "monetization_model": "Subscription",
        "opportunity_score": 70.0 + i,
        # Profile fields
        "title": f"Test submission {i}",
        "selftext": f"Test content {i}",
        "author": "test_user",
        "subreddit": "test",
        "trust_score": 80.0 + i,
    }
    for i in range(3)
]

print(f"\n📊 Test Data: {len(test_hybrids)} hybrid submissions")

# Test 1: Store hybrid submissions
print("\n--- Test 1: Store Hybrid Submissions ---")
success = store.store(test_hybrids)
print(f"  Success: {success}")
print(f"  Statistics: {store.get_statistics()}")

assert success is True, "Store should succeed"
assert store.stats.loaded == 3, "Should load 3 hybrid submissions"

# Test 2: Batch storage
print("\n--- Test 2: Batch Store ---")
store.reset_statistics()
result = store.store_batch(test_hybrids, batch_size=2)
print(f"  Batches: {result['batches']}")
print(f"  Success Rate: {result['success_rate'] * 100:.1f}%")

assert result['successful_batches'] == result['batches'], "All batches should succeed"

print("\n" + "=" * 80)
print("✓ HYBRIDSTORE TESTS PASSED")
print("=" * 80)

EOF
```

### Step 8: Verify No Duplicates in Database

```bash
python3 << 'EOF'
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("CHECKING FOR DUPLICATES")
print("=" * 80)

# Check app_opportunities
result_opp = client.rpc(
    "exec_sql",
    {"query": """
        SELECT submission_id, COUNT(*) as count
        FROM app_opportunities
        WHERE submission_id LIKE 'store_test_%'
        GROUP BY submission_id
        HAVING COUNT(*) > 1
    """}
).execute()

if result_opp.data:
    print(f"❌ DUPLICATES IN APP_OPPORTUNITIES: {len(result_opp.data)}")
else:
    print("✓ No duplicates in app_opportunities")

# Check submissions
result_sub = client.rpc(
    "exec_sql",
    {"query": """
        SELECT submission_id, COUNT(*) as count
        FROM submissions
        WHERE submission_id LIKE 'store_test_%'
        GROUP BY submission_id
        HAVING COUNT(*) > 1
    """}
).execute()

if result_sub.data:
    print(f"❌ DUPLICATES IN SUBMISSIONS: {len(result_sub.data)}")
else:
    print("✓ No duplicates in submissions")

print("=" * 80)

EOF
```

**Expected Output**:
```
✓ No duplicates in app_opportunities
✓ No duplicates in submissions
```

### Step 9: Integration Test with Enrichment Services

```bash
python3 << 'EOF'
from core.storage import OpportunityStore, ProfileStore, HybridStore, DLTLoader

print("=" * 80)
print("TESTING STORAGE SERVICES INTEGRATION")
print("=" * 80)

# Test: All stores can share same loader
shared_loader = DLTLoader()

opp_store = OpportunityStore(loader=shared_loader)
profile_store = ProfileStore(loader=shared_loader)
hybrid_store = HybridStore(loader=shared_loader)

print("✓ All stores share same DLTLoader")
print(f"  - OpportunityStore loader: {id(opp_store.loader)}")
print(f"  - ProfileStore loader: {id(profile_store.loader)}")
print(f"  - HybridStore loader: {id(hybrid_store.loader)}")

assert opp_store.loader == profile_store.loader == hybrid_store.loader

print("\n✓ Integration test passed")

EOF
```

### Step 10: Statistics Accuracy Test

```bash
python3 << 'EOF'
from core.storage import OpportunityStore

store = OpportunityStore()

# Test valid data
valid_data = [
    {
        "submission_id": "stat_test_1",
        "problem_description": "Test",
        "app_concept": "Test app",
        "core_functions": ["F1"],
        "value_proposition": "Value",
        "target_user": "Users",
        "monetization_model": "Subscription",
    }
]

# Test invalid data
invalid_data = [
    {"submission_id": "stat_test_2"},  # Missing problem_description
]

print("Testing statistics accuracy...")

# Store valid
store.store(valid_data)
print(f"After valid: loaded={store.stats.loaded}, skipped={store.stats.skipped}")

# Store invalid
store.store(invalid_data)
print(f"After invalid: loaded={store.stats.loaded}, skipped={store.stats.skipped}")

assert store.stats.loaded == 1, "Should have 1 loaded"
assert store.stats.skipped == 1, "Should have 1 skipped"

stats = store.get_statistics()
print(f"\nFinal stats: {stats}")

assert stats["success_rate"] == 1.0, "Success rate should be 100%"

print("\n✓ Statistics accuracy verified")

EOF
```

---

## Validation Checklist

### Implementation Validation
- [ ] OpportunityStore class created
- [ ] ProfileStore class created
- [ ] HybridStore class created
- [ ] Module exports updated
- [ ] All 55 tests pass

### Functionality Validation
- [ ] OpportunityStore stores to app_opportunities
- [ ] ProfileStore stores to submissions
- [ ] HybridStore stores to both tables
- [ ] Data validation and filtering works
- [ ] Batch processing works
- [ ] Statistics tracking accurate

### Data Integrity Validation (CRITICAL)
- [ ] No duplicate records in app_opportunities
- [ ] No duplicate records in submissions
- [ ] Merge disposition working correctly
- [ ] Invalid data properly filtered

### Integration Validation
- [ ] All stores can share same DLTLoader
- [ ] Compatible with DLT constants
- [ ] Works with existing database schema
- [ ] Appropriate logging

---

## Troubleshooting

### Issue: Import errors

**Solution**:
```bash
# Verify all files exist
ls core/storage/*.py

# Check Python path
python3 -c "import sys; print(sys.path)"
```

### Issue: Database connection errors

**Solution**:
```bash
# Verify Supabase running
supabase status

# Test connection
python3 -c "from core.storage import OpportunityStore; store = OpportunityStore(); print('OK')"
```

### Issue: Duplicate records found

**Investigation**:
1. Check merge disposition is set
2. Verify primary key configuration
3. Review DLT logs
4. Check data has submission_id

---

## Reporting Results

### Test Summary Format

```
PHASE 7 PART 2 TESTING REPORT

Branch: claude/review-pipeline-handover-01Jm26EM3B94UGjpV5xR3bxc
Commit: [commit hash]
Date: [test date]
Tester: [local AI]

RESULTS:

Unit Tests:
- Total Tests: 55
- Passed: [X]
- Failed: [Y]
- Status: [PASS/FAIL]

Real Database Tests:
- OpportunityStore: [PASS/FAIL]
- ProfileStore: [PASS/FAIL]
- HybridStore: [PASS/FAIL]

Data Integrity:
- Duplicates in app_opportunities: [YES/NO]
- Duplicates in submissions: [YES/NO]
- Merge Working: [YES/NO]

Integration:
- Shared Loader: [PASS/FAIL]
- Statistics Accuracy: [PASS/FAIL]

ISSUES FOUND:
[List any issues]

FIXES APPLIED:
[List any fixes]

NEXT STEPS:
[Phase 7 Part 3 or additional work needed]
```

### Save Report To:
`docs/plans/unified-pipeline-refactoring/local-ai-report/phase-7-part-2-testing-report.md`

---

## Success Criteria

### Phase 7 Part 2 Complete When:
1. ✅ **All unit tests pass** (55 tests)
2. ✅ **Real database storage works** for all three services
3. ✅ **No duplicate records** in database
4. ✅ **Statistics tracking accurate**
5. ✅ **Integration working** (shared loader)
6. ✅ **Data validation working** (invalid data filtered)

---

## Next Phase

After Phase 7 Part 2 completion:

→ **Phase 7 Part 3: Integration & Validation**
- Integration tests with enrichment services
- Schema migration validation
- Performance testing
- Production readiness validation

---

**End of Testing Prompt**

*Generated: 2025-11-19*
*Phase: 7 Part 2 - Storage Services*
*Status: Code complete, awaiting local AI execution*
