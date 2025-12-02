# Phase 3 Task 2: Submission Formatters - Local Testing Prompt

**Branch**: `claude/pull-the-chan-01VHHaDftgWXe82ENhr3nauq`
**Commit**: `d027a97`
**Task**: Extract submission formatting utilities from monolithic pipeline
**Date**: 2025-11-19

---

## Context

This task extracted submission formatting functions from `scripts/core/batch_opportunity_scoring.py` into a reusable utility module `core/fetchers/formatters.py`.

**Extracted Functions:**
1. `format_submission_for_agent()` - Main formatting function for AI agent consumption
2. `format_batch_submissions()` - Batch processing utility
3. `extract_problem_statement()` - Problem extraction with 500-char truncation
4. `validate_submission_completeness()` - Field validation for required data

**Original Location**: `scripts/core/batch_opportunity_scoring.py` line 956
**New Location**: `core/fetchers/formatters.py`

---

## Testing Instructions

### Step 1: Pull Latest Changes

```bash
git checkout claude/pull-the-chan-01VHHaDftgWXe82ENhr3nauq
git pull origin claude/pull-the-chan-01VHHaDftgWXe82ENhr3nauq
```

**Expected Output**: Successfully pulled commit `d027a97` or later

---

### Step 2: Verify File Creation

```bash
ls -lh core/fetchers/formatters.py
ls -lh tests/test_formatters.py
```

**Expected Output**:
- `core/fetchers/formatters.py` exists (~6.5 KB)
- `tests/test_formatters.py` exists (~21 KB)

---

### Step 3: Test Module Import

```bash
python3 << 'EOF'
# Test basic import
from core.fetchers.formatters import (
    format_submission_for_agent,
    format_batch_submissions,
    extract_problem_statement,
    validate_submission_completeness
)

print("✅ All functions imported successfully")
print(f"✅ format_submission_for_agent: {format_submission_for_agent.__name__}")
print(f"✅ format_batch_submissions: {format_batch_submissions.__name__}")
print(f"✅ extract_problem_statement: {extract_problem_statement.__name__}")
print(f"✅ validate_submission_completeness: {validate_submission_completeness.__name__}")
EOF
```

**Expected Output**: All 4 functions import successfully with their correct names

---

### Step 4: Test Basic Functionality

#### Test 1: format_submission_for_agent()

```bash
python3 << 'EOF'
from core.fetchers.formatters import format_submission_for_agent

# Test complete submission
submission = {
    'submission_id': 'test123',
    'title': 'Need fitness app',
    'problem_description': 'Looking for workout tracker',
    'subreddit': 'fitness',
    'reddit_score': 42,
    'num_comments': 15,
    'trust_score': 85.5,
    'trust_badge': 'Verified'
}

formatted = format_submission_for_agent(submission)

# Verify all fields present
assert formatted['id'] == 'test123', "ID mismatch"
assert formatted['title'] == 'Need fitness app', "Title mismatch"
assert 'Need fitness app' in formatted['text'], "Text missing title"
assert 'Looking for workout tracker' in formatted['text'], "Text missing description"
assert formatted['subreddit'] == 'fitness', "Subreddit mismatch"
assert formatted['engagement']['upvotes'] == 42, "Upvotes mismatch"
assert formatted['engagement']['num_comments'] == 15, "Comments mismatch"
assert len(formatted['comments']) == 2, "Trust metadata missing"
assert 'Trust Score: 85.5' in formatted['comments'], "Trust score not in comments"

print("✅ format_submission_for_agent() works correctly")
EOF
```

**Expected Output**: All assertions pass, function formats submissions correctly

#### Test 2: format_batch_submissions()

```bash
python3 << 'EOF'
from core.fetchers.formatters import format_batch_submissions

submissions = [
    {'submission_id': '1', 'title': 'First', 'subreddit': 'test'},
    {'submission_id': '2', 'title': 'Second', 'subreddit': 'test'}
]

formatted = format_batch_submissions(submissions)

assert len(formatted) == 2, "Wrong number of results"
assert formatted[0]['id'] == '1', "First ID wrong"
assert formatted[1]['id'] == '2', "Second ID wrong"
assert all('text' in s for s in formatted), "Missing text field"

print("✅ format_batch_submissions() works correctly")
EOF
```

**Expected Output**: Batch formatting processes multiple submissions correctly

#### Test 3: extract_problem_statement()

```bash
python3 << 'EOF'
from core.fetchers.formatters import extract_problem_statement

# Test with description
submission1 = {
    'title': 'Need app',
    'problem_description': 'For tracking tasks'
}
problem1 = extract_problem_statement(submission1)
assert 'Need app' in problem1, "Title missing"
assert 'For tracking tasks' in problem1, "Description missing"

# Test truncation
submission2 = {
    'title': 'Test',
    'problem_description': 'x' * 1000
}
problem2 = extract_problem_statement(submission2)
assert problem2.endswith('...'), "Long content not truncated"
assert len(problem2) <= 510, "Truncation failed"  # title + \n\n + 500 + ...

# Test title only
submission3 = {'title': 'Just title'}
problem3 = extract_problem_statement(submission3)
assert problem3 == 'Just title', "Title-only extraction failed"

print("✅ extract_problem_statement() works correctly")
EOF
```

**Expected Output**: Problem extraction and truncation work as expected

#### Test 4: validate_submission_completeness()

```bash
python3 << 'EOF'
from core.fetchers.formatters import validate_submission_completeness

# Test valid submission
valid = {
    'submission_id': 'test123',
    'title': 'Need app',
    'subreddit': 'test'
}
is_valid, missing = validate_submission_completeness(valid)
assert is_valid is True, "Valid submission marked invalid"
assert len(missing) == 0, "False positive missing fields"

# Test invalid submission
invalid = {'submission_id': 'test123'}
is_valid, missing = validate_submission_completeness(invalid)
assert is_valid is False, "Invalid submission marked valid"
assert 'title' in missing, "Missing title not detected"
assert 'subreddit' in missing, "Missing subreddit not detected"

# Test empty strings
empty = {'submission_id': '', 'title': '  ', 'subreddit': None}
is_valid, missing = validate_submission_completeness(empty)
assert is_valid is False, "Empty values not caught"
assert len(missing) == 3, "Not all empty fields detected"

print("✅ validate_submission_completeness() works correctly")
EOF
```

**Expected Output**: Validation correctly identifies required fields and empty values

---

### Step 5: Run Full Test Suite

```bash
uv run pytest tests/test_formatters.py -v
```

**Expected Output**:
- All 39 tests pass
- 0 failures
- Test time: ~3-5 seconds

---

### Step 6: Check Test Coverage

```bash
uv run pytest tests/test_formatters.py --cov=core.fetchers.formatters --cov-report=term-missing
```

**Expected Output**:
```
core/fetchers/formatters.py        32      0   100%
```

**Coverage Requirements**:
- ✅ 100% statement coverage (32/32 statements)
- ✅ All functions covered
- ✅ All edge cases tested

---

### Step 7: Verify Data Integrity

Verify the extracted function matches the original:

```bash
python3 << 'EOF'
import inspect
from core.fetchers.formatters import format_submission_for_agent

# Check function signature
sig = inspect.signature(format_submission_for_agent)
params = list(sig.parameters.keys())

assert 'submission' in params, "Function signature changed"
assert len(params) == 1, "Extra parameters added"

# Verify return type annotation
assert sig.return_annotation == dict[str, any] or str(sig.return_annotation) == "dict[str, typing.Any]", "Return type annotation missing or incorrect"

# Check docstring
doc = format_submission_for_agent.__doc__
assert doc is not None, "Missing docstring"
assert 'Format an opportunity' in doc, "Docstring content mismatch"

print("✅ Function signature and documentation intact")
print(f"✅ Parameters: {params}")
print(f"✅ Return type: {sig.return_annotation}")
EOF
```

**Expected Output**: Function signature matches original specification

---

### Step 8: Verify Original Monolith Still Works

```bash
python3 << 'EOF'
import sys
sys.path.insert(0, 'scripts/core')

# Check that original function still exists in monolith
with open('scripts/core/batch_opportunity_scoring.py', 'r') as f:
    content = f.read()

assert 'def format_submission_for_agent(' in content, "Original function removed prematurely"
assert content.count('def format_submission_for_agent(') == 1, "Function duplicated or removed"

# Find line number
lines = content.split('\n')
func_line = None
for i, line in enumerate(lines, 1):
    if 'def format_submission_for_agent(' in line:
        func_line = i
        break

print(f"✅ Original function still present at line {func_line}")
print("✅ Backward compatibility maintained")
EOF
```

**Expected Output**: Original function still exists in monolith at line 956

---

## Success Criteria

Your testing is successful if:

1. ✅ **File Creation**: Both `core/fetchers/formatters.py` and `tests/test_formatters.py` exist
2. ✅ **Module Import**: All 4 functions import without errors
3. ✅ **Functionality**: All 4 functions work as expected with test data
4. ✅ **Test Suite**: 39/39 tests pass
5. ✅ **Coverage**: 100% coverage (32/32 statements, 0 missed)
6. ✅ **Data Integrity**: 4 functions extracted correctly
7. ✅ **Function Signatures**: All signatures and docstrings intact
8. ✅ **Original Monolith**: Original function preserved at line 956

---

## Report Template

Create your report at:
`docs/plans/unified-pipeline-refactoring/local-ai-report/phase-3-task-2-testing-report.md`

```markdown
# Phase 3 Task 2 Testing Report - Submission Formatters

**Date**: [DATE]
**Branch**: claude/pull-the-chan-01VHHaDftgWXe82ENhr3nauq
**Commit**: [COMMIT_HASH]
**Tester**: [YOUR_NAME]

## Executive Summary
[PASS/FAIL] - Phase 3 Task 2 extraction of submission formatters...

## Test Results

### ✅/❌ File Creation (Step 2)
- core/fetchers/formatters.py: [STATUS] ([SIZE])
- tests/test_formatters.py: [STATUS] ([SIZE])

### ✅/❌ Module Import (Step 3)
- Basic module import: [STATUS]
- All 4 functions import: [STATUS]

### ✅/❌ Basic Functionality (Step 4)
- format_submission_for_agent(): [STATUS]
- format_batch_submissions(): [STATUS]
- extract_problem_statement(): [STATUS]
- validate_submission_completeness(): [STATUS]

### ✅/❌ Test Suite (Step 5)
- Total Tests: [N/39]
- Result: [PASSED/FAILED]

### ✅/❌ Test Coverage (Step 6)
- Module: core/fetchers/formatters.py
- Coverage: [N]% ([STATEMENTS] statements, [MISSED] missed)

### ✅/❌ Data Integrity (Step 7)
- Total Functions: [N/4]
- Function signatures: [STATUS]
- Docstrings: [STATUS]

### ✅/❌ Original Monolith (Step 8)
- Function Location: Line [N]
- Function Preserved: [YES/NO]

## Issues Found
[List any issues discovered during testing]

## Final Assessment
**RECOMMENDATION: [PASS/FAIL]** ✅/❌

[Detailed explanation of results]

**Ready to proceed to Phase 3 Task 3**: [YES/NO]
```

---

## Troubleshooting

### Issue: Import errors
**Solution**: Ensure you're in the project root and Python path includes the project

### Issue: Tests fail with missing dependencies
**Solution**: Run `uv sync` to install all dependencies

### Issue: Coverage below 100%
**Solution**: Review the coverage report to identify untested code paths

### Issue: Original function not found
**Solution**: Check you're on the correct branch and have pulled latest changes

---

**Ready for Local AI Testing** 🤖

Once testing is complete, report results and proceed to Phase 3 Task 3: Quality Filters Extraction.

---

**Document Version**: 1.0
**Last Updated**: 2025-11-19
**Phase**: 3 - Extract Utilities
**Task**: 2 of 4
