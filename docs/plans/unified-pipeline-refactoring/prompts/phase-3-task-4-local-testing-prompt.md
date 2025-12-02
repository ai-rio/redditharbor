# Phase 3 Task 4: Trust Score Converters - Local Testing Prompt

**Branch**: `claude/pull-the-chan-01VHHaDftgWXe82ENhr3nauq`
**Commit**: `3bbba37` (or later)
**Task**: Extract trust score conversion utilities from dlt_trust_pipeline
**Date**: 2025-11-19

---

## Context

This task extracted trust score conversion functions from `scripts/dlt/dlt_trust_pipeline.py` lines 423-471 into a reusable utility module.

**Extracted Functions:**
1. `get_engagement_level()` - Convert engagement scores to levels
2. `get_problem_validity()` - Convert problem validity scores to levels
3. `get_discussion_quality()` - Convert discussion quality scores to levels
4. `get_ai_confidence_level()` - Convert AI confidence scores to levels
5. `convert_all_trust_scores()` - Batch conversion utility

**Original Location**: `scripts/dlt/dlt_trust_pipeline.py` lines 423-471
**New Location**: `core/enrichment/trust_converters.py`

---

## Testing Instructions

### Step 1: Pull Latest Changes

```bash
git checkout claude/pull-the-chan-01VHHaDftgWXe82ENhr3nauq
git pull origin claude/pull-the-chan-01VHHaDftgWXe82ENhr3nauq
```

### Step 2: Verify File Creation

```bash
ls -lh core/enrichment/trust_converters.py
ls -lh tests/test_trust_converters.py
```

**Expected**: Both files exist (~10 KB and ~22 KB)

### Step 3: Test Module Imports

```bash
python3 << 'EOF'
from core.enrichment.trust_converters import (
    get_engagement_level,
    get_problem_validity,
    get_discussion_quality,
    get_ai_confidence_level,
    convert_all_trust_scores
)

print("✅ All 5 functions imported successfully")
EOF
```

### Step 4: Test Individual Converters

```bash
python3 << 'EOF'
from core.enrichment.trust_converters import (
    get_engagement_level,
    get_problem_validity,
    get_discussion_quality,
    get_ai_confidence_level
)

# Test engagement levels
assert get_engagement_level(85.0) == "VERY_HIGH"
assert get_engagement_level(70.0) == "HIGH"
assert get_engagement_level(50.0) == "MEDIUM"
assert get_engagement_level(30.0) == "LOW"
assert get_engagement_level(10.0) == "MINIMAL"

# Test problem validity
assert get_problem_validity(85.0) == "VALID"
assert get_problem_validity(70.0) == "POTENTIAL"
assert get_problem_validity(50.0) == "UNCLEAR"
assert get_problem_validity(30.0) == "INVALID"

# Test discussion quality
assert get_discussion_quality(85.0) == "EXCELLENT"
assert get_discussion_quality(70.0) == "GOOD"
assert get_discussion_quality(50.0) == "FAIR"
assert get_discussion_quality(30.0) == "POOR"

# Test AI confidence
assert get_ai_confidence_level(85.0) == "VERY_HIGH"
assert get_ai_confidence_level(70.0) == "HIGH"
assert get_ai_confidence_level(50.0) == "MEDIUM"
assert get_ai_confidence_level(30.0) == "LOW"

print("✅ All converters work correctly")
EOF
```

### Step 5: Test Batch Conversion

```bash
python3 << 'EOF'
from core.enrichment.trust_converters import convert_all_trust_scores

# Test complete data
trust_data = {
    'engagement_score': 85.0,
    'problem_validity_score': 70.0,
    'discussion_quality_score': 55.0,
    'ai_confidence_score': 90.0
}

result = convert_all_trust_scores(trust_data)

# Check categorical levels added
assert result['engagement_level'] == 'VERY_HIGH'
assert result['problem_validity'] == 'POTENTIAL'
assert result['discussion_quality'] == 'FAIR'
assert result['ai_confidence'] == 'VERY_HIGH'

# Check original scores preserved
assert result['engagement_score'] == 85.0
assert result['problem_validity_score'] == 70.0
assert result['discussion_quality_score'] == 55.0
assert result['ai_confidence_score'] == 90.0

print("✅ Batch conversion works correctly")
print("   Original scores preserved: ✓")
print("   Categorical levels added: ✓")
EOF
```

### Step 6: Run Full Test Suite

```bash
uv run pytest tests/test_trust_converters.py -v
```

**Expected**: 40/40 tests pass

### Step 7: Check Test Coverage

```bash
uv run pytest tests/test_trust_converters.py \
  --cov=core.enrichment.trust_converters --cov-report=term-missing
```

**Expected Coverage**: 46/46 statements (100%)

### Step 8: Verify Original Monolith

```bash
python3 << 'EOF'
with open('scripts/dlt/dlt_trust_pipeline.py', 'r') as f:
    content = f.read()

# Check functions still exist
assert 'def get_engagement_level(' in content
assert 'def get_problem_validity(' in content
assert 'def get_discussion_quality(' in content
assert 'def get_ai_confidence_level(' in content

# Find line number
lines = content.split('\n')
for i, line in enumerate(lines, 1):
    if 'def get_engagement_level(' in line:
        print(f"✅ Original functions still at line {i}")
        break

print("✅ Backward compatibility maintained")
EOF
```

---

## Success Criteria

1. ✅ **File Creation**: Both files exist
2. ✅ **Module Imports**: All 5 functions import successfully
3. ✅ **Individual Converters**: All 4 score converters work correctly
4. ✅ **Batch Conversion**: convert_all_trust_scores() works correctly
5. ✅ **Test Suite**: 40/40 tests pass
6. ✅ **Coverage**: 100% (46/46 statements)
7. ✅ **Original Monolith**: Functions preserved at line 423

---

## Report Template

Save to: `docs/plans/unified-pipeline-refactoring/local-ai-report/phase-3-task-4-testing-report.md`

```markdown
# Phase 3 Task 4 Testing Report - Trust Score Converters

**Date**: [DATE]
**Commit**: [HASH]
**Tester**: [NAME]

## Executive Summary
[PASS/FAIL] - Phase 3 Task 4 extraction of trust score converters...

## Test Results

### ✅/❌ Module Creation
- trust_converters.py: [STATUS]
- test_trust_converters.py: [STATUS]

### ✅/❌ Functionality Tests
- get_engagement_level(): [STATUS]
- get_problem_validity(): [STATUS]
- get_discussion_quality(): [STATUS]
- get_ai_confidence_level(): [STATUS]
- convert_all_trust_scores(): [STATUS]

### ✅/❌ Test Suite
- Total: [N/40]
- Coverage: [N/46] ([X]%)

## Issues Found
[List any issues]

## Recommendation
**[PASS/FAIL]** - Phase 3 COMPLETE: [YES/NO]
```

---

**Ready for Local AI Testing** 🤖

This is the FINAL task of Phase 3. Once validated, Phase 3 (Extract Utilities) will be complete!
