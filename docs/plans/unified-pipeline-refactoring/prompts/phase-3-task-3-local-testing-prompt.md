# Phase 3 Task 3: Quality Filters - Local Testing Prompt

**Branch**: `claude/pull-the-chan-01VHHaDftgWXe82ENhr3nauq`
**Commit**: `0e9dd78`
**Task**: Extract quality filtering and scoring utilities from dlt_trust_pipeline
**Date**: 2025-11-19

---

## Context

This task extracted quality filtering logic from `scripts/dlt/dlt_trust_pipeline.py` into a reusable quality filters system with 3 modules:

1. **thresholds.py** - Quality threshold constants
2. **quality_scorer.py** - Pre-AI quality scoring (2 functions)
3. **pre_filter.py** - Pre-AI filtering logic (3 functions)

**Original Location**: `scripts/dlt/dlt_trust_pipeline.py` lines 95-176
**New Location**: `core/quality_filters/`

---

## Testing Instructions

### Step 1: Pull Latest Changes

```bash
git checkout claude/pull-the-chan-01VHHaDftgWXe82ENhr3nauq
git pull origin claude/pull-the-chan-01VHHaDftgWXe82ENhr3nauq
```

### Step 2: Verify File Creation

```bash
ls -lh core/quality_filters/thresholds.py
ls -lh core/quality_filters/quality_scorer.py
ls -lh core/quality_filters/pre_filter.py
ls -lh tests/test_quality_scorer.py
ls -lh tests/test_pre_filter.py
```

**Expected**: All 5 files exist

### Step 3: Test Module Imports

```bash
python3 << 'EOF'
from core.quality_filters.thresholds import (
    MIN_ENGAGEMENT_SCORE, MIN_COMMENT_COUNT, 
    MIN_PROBLEM_KEYWORDS, MIN_QUALITY_SCORE,
    PROBLEM_KEYWORDS
)
from core.quality_filters.quality_scorer import (
    calculate_pre_ai_quality_score,
    get_quality_breakdown
)
from core.quality_filters.pre_filter import (
    should_analyze_with_ai,
    filter_submissions_batch,
    get_filter_stats
)

print("✅ All imports successful")
print(f"✅ {len(PROBLEM_KEYWORDS)} problem keywords loaded")
print(f"✅ MIN_QUALITY_SCORE: {MIN_QUALITY_SCORE}")
EOF
```

### Step 4: Test Quality Scoring

```bash
python3 << 'EOF'
import time
from core.quality_filters.quality_scorer import calculate_pre_ai_quality_score, get_quality_breakdown

# High quality post
post = {
    'upvotes': 50,
    'num_comments': 20,
    'title': 'I have a problem with my workflow',
    'text': 'It is frustrating and difficult',
    'created_utc': time.time()
}

score = calculate_pre_ai_quality_score(post)
breakdown = get_quality_breakdown(post)

assert score > 60.0, f"Expected high score, got {score}"
assert 'engagement_score' in breakdown
assert 'keyword_score' in breakdown
assert 'recency_score' in breakdown
assert 'total_score' in breakdown
assert 'problem_keyword_count' in breakdown
assert breakdown['total_score'] == score

print("✅ Quality scoring works correctly")
print(f"   Score: {score}")
print(f"   Breakdown: {breakdown}")
EOF
```

### Step 5: Test Pre-Filtering

```bash
python3 << 'EOF'
import time
from core.quality_filters.pre_filter import should_analyze_with_ai, filter_submissions_batch

# Test passing post
good_post = {
    'upvotes': 50,
    'num_comments': 20,
    'title': 'I have a problem',
    'text': 'Need help',
    'created_utc': time.time()
}

should_analyze, score, reason = should_analyze_with_ai(good_post)
assert should_analyze is True, "Good post should pass filter"
assert "Passed all quality filters" in reason

# Test failing post
bad_post = {
    'upvotes': 1,
    'num_comments': 0,
    'title': 'test',
    'text': '',
    'created_utc': time.time()
}

should_analyze, score, reason = should_analyze_with_ai(bad_post)
assert should_analyze is False, "Bad post should fail filter"

# Test batch filtering
posts = [good_post, bad_post]
passed, filtered = filter_submissions_batch(posts)

assert len(passed) >= 1
assert len(filtered) >= 1
assert all('quality_score' in p for p in passed)
assert all('filter_reason' in p for p in filtered)

print("✅ Pre-filtering works correctly")
print(f"   Passed: {len(passed)}, Filtered: {len(filtered)}")
EOF
```

### Step 6: Run Full Test Suite

```bash
uv run pytest tests/test_quality_scorer.py tests/test_pre_filter.py -v
```

**Expected**: 59/59 tests pass

### Step 7: Check Test Coverage

```bash
uv run pytest tests/test_quality_scorer.py tests/test_pre_filter.py \
  --cov=core.quality_filters --cov-report=term-missing
```

**Expected Coverage**:
- `quality_scorer.py`: 32/32 statements (100%)
- `pre_filter.py`: 39/39 statements (100%)
- `thresholds.py`: 6/6 statements (100%)

### Step 8: Verify Original Monolith

```bash
python3 << 'EOF'
with open('scripts/dlt/dlt_trust_pipeline.py', 'r') as f:
    content = f.read()

assert 'def calculate_pre_ai_quality_score(' in content
assert 'def should_analyze_with_ai(' in content

# Find line numbers
lines = content.split('\n')
for i, line in enumerate(lines, 1):
    if 'def calculate_pre_ai_quality_score(' in line:
        print(f"✅ Original function still at line {i}")
        break

print("✅ Backward compatibility maintained")
EOF
```

---

## Success Criteria

1. ✅ **File Creation**: All 5 files exist (3 modules + 2 test files)
2. ✅ **Module Imports**: All 7 functions import successfully
3. ✅ **Quality Scoring**: Scoring and breakdown functions work
4. ✅ **Pre-Filtering**: Filter decisions and batch processing work
5. ✅ **Test Suite**: 59/59 tests pass
6. ✅ **Coverage**: 100% (77/77 statements)
7. ✅ **Original Monolith**: Functions preserved at lines 101 & 137

---

## Report Template

Save to: `docs/plans/unified-pipeline-refactoring/local-ai-report/phase-3-task-3-testing-report.md`

```markdown
# Phase 3 Task 3 Testing Report - Quality Filters

**Date**: [DATE]
**Commit**: [HASH]
**Tester**: [NAME]

## Executive Summary
[PASS/FAIL] - Phase 3 Task 3 extraction of quality filters...

## Test Results

### ✅/❌ Module Creation
- thresholds.py: [STATUS]
- quality_scorer.py: [STATUS]
- pre_filter.py: [STATUS]

### ✅/❌ Test Suite (Step 6)
- Total: [N/59]
- Passed: [N]
- Failed: [N]

### ✅/❌ Coverage (Step 7)
- quality_scorer.py: [N/32] ([X]%)
- pre_filter.py: [N/39] ([X]%)
- thresholds.py: [N/6] ([X]%)

## Issues Found
[List any issues]

## Recommendation
**[PASS/FAIL]** - Ready for Phase 3 Task 4: [YES/NO]
```

---

**Ready for Local AI Testing** 🤖
