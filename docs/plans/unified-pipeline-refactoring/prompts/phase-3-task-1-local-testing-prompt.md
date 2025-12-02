# Phase 3 Task 1 Local AI Testing Prompt

**Phase**: 3 - Extract Utilities
**Task**: Task 1 - Sector Mapping Utility
**Date**: 2025-11-19
**Branch**: `claude/pull-the-chan-01VHHaDftgWXe82ENhr3nauq`
**Commit**: `c2fbb2a`
**Status**: Ready for local validation

---

## Context

Phase 3 Task 1 extracted the subreddit-to-sector mapping utility from the monolithic `batch_opportunity_scoring.py` script into a reusable module.

**What Was Extracted**:
- **Source**: `scripts/core/batch_opportunity_scoring.py` (lines 117-219)
- **Target**: `core/utils/sector_mapping.py` (new file, 169 lines)
- **Tests**: `tests/test_sector_mapping.py` (new file, 188 lines)

**What Changed**:
- ✅ Extracted `SUBREDDIT_SECTOR_MAP` dictionary (89 mappings)
- ✅ Extracted `map_subreddit_to_sector()` function
- ✅ Added 3 new utility functions
- ✅ Created comprehensive test suite (20+ tests)

---

## Your Task

Validate that the sector mapping utility works correctly by:

1. Testing that the utility module can be imported
2. Verifying all utility functions work as expected
3. Running the test suite
4. Checking test coverage
5. Verifying the original monolith still has the function (not yet removed)
6. Reporting any issues found

---

## Step-by-Step Testing Instructions

### Step 1: Pull Latest Changes

```bash
git fetch origin
git checkout claude/pull-the-chan-01VHHaDftgWXe82ENhr3nauq
git pull
```

**Expected**: Successfully pulled commit `c2fbb2a` or later

---

### Step 2: Verify New Files Exist

```bash
# Check that sector_mapping.py was created
ls -la core/utils/sector_mapping.py

# Check that test file was created
ls -la tests/test_sector_mapping.py
```

**Expected Output**:
```
-rw-r--r-- 1 ... 5.2K ... core/utils/sector_mapping.py
-rw-r--r-- 1 ... 6.1K ... tests/test_sector_mapping.py
```

---

### Step 3: Test Module Imports

**Test 1: Import the module**

```bash
python -c "from core.utils.sector_mapping import map_subreddit_to_sector; print('✅ sector_mapping module imports successfully')"
```

**Expected**: `✅ sector_mapping module imports successfully`

**Test 2: Import all functions**

```bash
python -c "
from core.utils.sector_mapping import (
    map_subreddit_to_sector,
    get_all_sectors,
    get_subreddits_by_sector,
    get_sector_stats,
    SUBREDDIT_SECTOR_MAP
)
print('✅ All functions and data structures import successfully')
"
```

**Expected**: `✅ All functions and data structures import successfully`

---

### Step 4: Test Basic Functionality

**Test 1: map_subreddit_to_sector() works**

```bash
python -c "
from core.utils.sector_mapping import map_subreddit_to_sector

# Test known subreddits
assert map_subreddit_to_sector('fitness') == 'Health & Fitness'
assert map_subreddit_to_sector('saas') == 'Technology & SaaS'
assert map_subreddit_to_sector('personalfinance') == 'Finance & Investing'

# Test unknown subreddit
assert map_subreddit_to_sector('unknown') == 'Technology & SaaS'

# Test empty/None
assert map_subreddit_to_sector('') == 'Technology & SaaS'
assert map_subreddit_to_sector(None) == 'Technology & SaaS'

# Test case insensitive
assert map_subreddit_to_sector('FITNESS') == 'Health & Fitness'
assert map_subreddit_to_sector('SaaS') == 'Technology & SaaS'

print('✅ map_subreddit_to_sector() works correctly')
"
```

**Expected**: `✅ map_subreddit_to_sector() works correctly`

**Test 2: get_all_sectors() works**

```bash
python -c "
from core.utils.sector_mapping import get_all_sectors

sectors = get_all_sectors()

# Check expected sectors exist
assert 'Technology & SaaS' in sectors
assert 'Health & Fitness' in sectors
assert 'Finance & Investing' in sectors
assert 'Education & Career' in sectors
assert 'Travel & Experiences' in sectors
assert 'Real Estate' in sectors

# Check it's sorted
assert sectors == sorted(sectors)

print(f'✅ get_all_sectors() returns {len(sectors)} unique sectors')
"
```

**Expected**: `✅ get_all_sectors() returns 6 unique sectors`

**Test 3: get_subreddits_by_sector() works**

```bash
python -c "
from core.utils.sector_mapping import get_subreddits_by_sector

# Test Technology & SaaS
tech_subs = get_subreddits_by_sector('Technology & SaaS')
assert 'saas' in tech_subs
assert 'indiehackers' in tech_subs
assert len(tech_subs) == 9

# Test Health & Fitness
fitness_subs = get_subreddits_by_sector('Health & Fitness')
assert 'fitness' in fitness_subs
assert 'yoga' in fitness_subs
assert len(fitness_subs) == 20

# Test non-existent sector
empty = get_subreddits_by_sector('NonExistent')
assert empty == []

print('✅ get_subreddits_by_sector() works correctly')
"
```

**Expected**: `✅ get_subreddits_by_sector() works correctly`

**Test 4: get_sector_stats() works**

```bash
python -c "
from core.utils.sector_mapping import get_sector_stats

stats = get_sector_stats()

# Check all sectors represented
assert 'Technology & SaaS' in stats
assert 'Health & Fitness' in stats

# Check counts are correct
assert stats['Health & Fitness'] == 20
assert stats['Finance & Investing'] == 17
assert stats['Technology & SaaS'] == 9

# Check total count
assert sum(stats.values()) == 89

print('✅ get_sector_stats() works correctly')
print(f'   Total subreddits: {sum(stats.values())}')
"
```

**Expected**:
```
✅ get_sector_stats() works correctly
   Total subreddits: 89
```

---

### Step 5: Run Test Suite

**Run all tests**:

```bash
pytest tests/test_sector_mapping.py -v
```

**Expected Output** (summary):
```
tests/test_sector_mapping.py::test_map_known_subreddit_saas PASSED
tests/test_sector_mapping.py::test_map_known_subreddit_fitness PASSED
tests/test_sector_mapping.py::test_map_known_subreddit_finance PASSED
... (more tests)
======================== XX passed in X.XXs ========================
```

**Expected**: All tests should PASS (20+ tests)

---

### Step 6: Check Test Coverage

**Run with coverage**:

```bash
pytest tests/test_sector_mapping.py --cov=core.utils.sector_mapping --cov-report=term
```

**Expected Output**:
```
Name                             Stmts   Miss  Cover
----------------------------------------------------
core/utils/sector_mapping.py       XX      0   100%
----------------------------------------------------
TOTAL                              XX      0   100%
```

**Expected**: 100% code coverage

---

### Step 7: Verify Data Integrity

**Check mapping count**:

```bash
python -c "
from core.utils.sector_mapping import SUBREDDIT_SECTOR_MAP

print(f'Total subreddit mappings: {len(SUBREDDIT_SECTOR_MAP)}')

# Check for duplicates
subreddits = list(SUBREDDIT_SECTOR_MAP.keys())
assert len(subreddits) == len(set(subreddits)), 'Duplicate subreddits found!'

# Check all values are non-empty
for subreddit, sector in SUBREDDIT_SECTOR_MAP.items():
    assert sector, f'Empty sector for {subreddit}'
    assert len(sector) > 0, f'Empty sector name for {subreddit}'

print('✅ All 89 mappings are valid and unique')
"
```

**Expected**: `✅ All 89 mappings are valid and unique`

---

### Step 8: Verify Original Monolith Still Works

**Important**: The original function in the monolith should still exist (not yet removed).

```bash
# Check that the original function still exists in the monolith
grep -n "def map_subreddit_to_sector" scripts/core/batch_opportunity_scoring.py
```

**Expected Output**:
```
205:def map_subreddit_to_sector(subreddit: str) -> str:
```

**Expected**: Function should still exist at line 205 (or nearby)

**Note**: In a later task, we'll update the monolith to use the extracted version.

---

## Expected Test Summary

After completing all steps, you should have:

✅ **File Creation**: 2 new files created
✅ **Module Import**: sector_mapping module imports successfully
✅ **Function Imports**: All 4 functions import successfully
✅ **map_subreddit_to_sector()**: Works correctly (case-insensitive, defaults)
✅ **get_all_sectors()**: Returns 6 sectors, sorted
✅ **get_subreddits_by_sector()**: Returns correct subreddit lists
✅ **get_sector_stats()**: Returns correct statistics
✅ **Test Suite**: All tests pass (20+ tests)
✅ **Test Coverage**: 100% coverage
✅ **Data Integrity**: 89 valid, unique mappings
✅ **Monolith Intact**: Original function still exists

**Total Test Categories**: 10

---

## What to Report Back

Please create a report at:
```
docs/plans/unified-pipeline-refactoring/local-ai-report/phase-3-task-1-testing-report.md
```

### Report Structure

```markdown
# Phase 3 Task 1 Testing Report - Sector Mapping Utility

**Date**: [current date]
**Branch**: claude/pull-the-chan-01VHHaDftgWXe82ENhr3nauq
**Commit**: [actual commit hash]
**Tester**: Local AI Agent

## Executive Summary

[PASS/FAIL status with brief explanation]

## Test Results

### File Creation
- [ ] core/utils/sector_mapping.py exists: [PASS/FAIL]
- [ ] tests/test_sector_mapping.py exists: [PASS/FAIL]

### Module Import Tests
- [ ] sector_mapping module imports: [PASS/FAIL]
- [ ] All functions import: [PASS/FAIL]

### Functionality Tests
- [ ] map_subreddit_to_sector() works: [PASS/FAIL]
- [ ] get_all_sectors() works: [PASS/FAIL]
- [ ] get_subreddits_by_sector() works: [PASS/FAIL]
- [ ] get_sector_stats() works: [PASS/FAIL]

### Test Suite
- [ ] All unit tests pass: [PASS/FAIL]
- [ ] Number of tests: [XX tests]
- [ ] Test coverage: [XX%]

### Data Integrity
- [ ] 89 mappings verified: [PASS/FAIL]
- [ ] No duplicates: [PASS/FAIL]
- [ ] All sectors valid: [PASS/FAIL]

### Backward Compatibility
- [ ] Original monolith function still exists: [PASS/FAIL]

## Issues Found

[List any issues encountered, or write "None" if all tests passed]

## Test Output

[Include relevant test output, especially any failures]

## Recommendations

[Your recommendation: PASS (proceed to Task 2) or FAIL (needs fixes)]
```

---

## Common Issues and Solutions

### Issue 1: ImportError - Module not found

**Symptom**: `ModuleNotFoundError: No module named 'core.utils.sector_mapping'`

**Cause**: Project root not in Python path

**Solution**:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
python -c "from core.utils.sector_mapping import map_subreddit_to_sector"
```

### Issue 2: pytest not found

**Symptom**: `/usr/bin/python: No module named pytest`

**Cause**: pytest not installed in environment

**Solution**:
```bash
pip install pytest pytest-cov
# or
uv pip install pytest pytest-cov
```

### Issue 3: Test failures

**Symptom**: Some tests fail

**Cause**: Potential data inconsistencies

**Solution**: Report the specific test failures - this needs fixing.

---

## Success Criteria

Phase 3 Task 1 is considered **PASSED** if:

1. ✅ Both new files exist and are readable
2. ✅ Module and all functions import successfully
3. ✅ All 4 utility functions work correctly
4. ✅ All unit tests pass (20+ tests)
5. ✅ Test coverage is 100%
6. ✅ 89 mappings are valid and unique
7. ✅ Original monolith function still exists

---

## After Testing

Once you've completed testing and generated your report:

1. Commit your report to the repo
2. Notify the team of results
3. If all tests pass, Task 1 is validated
4. If tests fail, work with remote team to fix issues
5. Ready to proceed to Task 2 (submission formatters)

---

**Testing Priority**: 🟡 MEDIUM - Pure utility function, low risk

**Estimated Testing Time**: 5-10 minutes

**Phase 3 Progress**: Task 1 of 4 (25% complete)

**Last Updated**: 2025-11-19
