# Phase 5: Deduplication System - Local Testing Prompt

**Branch**: `claude/pull-the-chan-01VHHaDftgWXe82ENhr3nauq`
**Commit**: `3ffafc7` (or later)
**Task**: Extract deduplication system with $3,528/year cost savings
**Date**: 2025-11-19

---

## Context

This phase extracted deduplication logic from `scripts/core/batch_opportunity_scoring.py` into modular components that preserve **$3,528/year in cost savings** by preventing redundant AI analyses on semantically similar submissions.

**Extracted Components:**
1. `BusinessConceptManager` - Manage business concepts for deduplication
2. `AgnoSkipLogic` - Monetization analysis deduplication ($0.15/analysis)
3. `ProfilerSkipLogic` - AI profiler deduplication ($0.05/analysis)
4. `DeduplicationStatsUpdater` - Track cost savings statistics

**Original Locations**:
- `batch_opportunity_scoring.py` lines 222-290 (Agno skip logic)
- `batch_opportunity_scoring.py` lines 300-450 (Agno copy logic)
- `batch_opportunity_scoring.py` lines 503-571 (Profiler skip logic)
- `batch_opportunity_scoring.py` lines 584-723 (Profiler copy logic)

**New Location**: `core/deduplication/`

---

## Testing Instructions

### Step 1: Pull Latest Changes

```bash
git checkout claude/pull-the-chan-01VHHaDftgWXe82ENhr3nauq
git pull origin claude/pull-the-chan-01VHHaDftgWXe82ENhr3nauq
```

### Step 2: Verify File Creation

```bash
ls -lh core/deduplication/
```

**Expected**: 5 files created
- `__init__.py` (~1 KB)
- `concept_manager.py` (~11 KB)
- `agno_skip_logic.py` (~12 KB)
- `profiler_skip_logic.py` (~12 KB)
- `stats_updater.py` (~10 KB)

### Step 3: Test Module Imports

```bash
python3 << 'EOF'
from core.deduplication import (
    BusinessConceptManager,
    AgnoSkipLogic,
    ProfilerSkipLogic,
    DeduplicationStatsUpdater
)

print(" All 4 components imported successfully")
print(f"   - BusinessConceptManager: {BusinessConceptManager}")
print(f"   - AgnoSkipLogic: {AgnoSkipLogic}")
print(f"   - ProfilerSkipLogic: {ProfilerSkipLogic}")
print(f"   - DeduplicationStatsUpdater: {DeduplicationStatsUpdater}")
EOF
```

### Step 4: Test BusinessConceptManager Interface

```bash
python3 << 'EOF'
from unittest.mock import MagicMock
from core.deduplication import BusinessConceptManager

# Create mock Supabase client
mock_client = MagicMock()
manager = BusinessConceptManager(mock_client)

# Verify attributes
assert hasattr(manager, 'client')
assert hasattr(manager, 'table')
assert manager.table == 'business_concepts'

# Verify methods exist
assert hasattr(manager, 'get_or_create_concept')
assert hasattr(manager, 'update_analysis_status')
assert hasattr(manager, 'get_concept_for_submission')
assert hasattr(manager, 'get_concept_by_id')
assert hasattr(manager, 'increment_submission_count')

print(" BusinessConceptManager interface verified")
print("   - Table name: business_concepts")
print("   - Methods: 5 public methods")
EOF
```

### Step 5: Test AgnoSkipLogic Interface

```bash
python3 << 'EOF'
from unittest.mock import MagicMock
from core.deduplication import AgnoSkipLogic

# Create mock Supabase client
mock_client = MagicMock()
agno_logic = AgnoSkipLogic(mock_client)

# Verify attributes
assert hasattr(agno_logic, 'client')
assert hasattr(agno_logic, 'concept_manager')
assert hasattr(agno_logic, 'stats')

# Verify stats initialized correctly
assert agno_logic.stats == {'skipped': 0, 'fresh': 0, 'copied': 0, 'errors': 0}

# Verify methods exist
assert hasattr(agno_logic, 'should_run_agno_analysis')
assert hasattr(agno_logic, 'copy_agno_analysis')
assert hasattr(agno_logic, 'update_concept_agno_stats')
assert hasattr(agno_logic, 'get_statistics')
assert hasattr(agno_logic, 'reset_statistics')

print(" AgnoSkipLogic interface verified")
print("   - Initial stats: all zeros")
print("   - Methods: 5 public methods")
EOF
```

### Step 6: Test ProfilerSkipLogic Interface

```bash
python3 << 'EOF'
from unittest.mock import MagicMock
from core.deduplication import ProfilerSkipLogic

# Create mock Supabase client
mock_client = MagicMock()
profiler_logic = ProfilerSkipLogic(mock_client)

# Verify attributes
assert hasattr(profiler_logic, 'client')
assert hasattr(profiler_logic, 'concept_manager')
assert hasattr(profiler_logic, 'stats')

# Verify stats initialized correctly
assert profiler_logic.stats == {'skipped': 0, 'fresh': 0, 'copied': 0, 'errors': 0}

# Verify methods exist
assert hasattr(profiler_logic, 'should_run_profiler_analysis')
assert hasattr(profiler_logic, 'copy_profiler_analysis')
assert hasattr(profiler_logic, 'update_concept_profiler_stats')
assert hasattr(profiler_logic, 'get_statistics')
assert hasattr(profiler_logic, 'reset_statistics')

print(" ProfilerSkipLogic interface verified")
print("   - Initial stats: all zeros")
print("   - Methods: 5 public methods")
EOF
```

### Step 7: Test DeduplicationStatsUpdater

```bash
python3 << 'EOF'
from unittest.mock import MagicMock
from core.deduplication import DeduplicationStatsUpdater

# Create mock Supabase client
mock_client = MagicMock()
stats_updater = DeduplicationStatsUpdater(mock_client)

# Verify cost constants
assert stats_updater.AGNO_ANALYSIS_COST == 0.15
assert stats_updater.PROFILER_ANALYSIS_COST == 0.05

# Test update_savings for Agno
agno_savings = stats_updater.update_savings('agno', skipped=10, copied=5)
assert agno_savings == 2.25  # (10 + 5) * $0.15
print(f" Agno savings calculation: ${agno_savings:.2f}")

# Test update_savings for Profiler
profiler_savings = stats_updater.update_savings('profiler', skipped=20, copied=10)
assert profiler_savings == 1.50  # (20 + 10) * $0.05
print(f" Profiler savings calculation: ${profiler_savings:.2f}")

print(" DeduplicationStatsUpdater verified")
print(f"   - Agno cost: ${stats_updater.AGNO_ANALYSIS_COST}/analysis")
print(f"   - Profiler cost: ${stats_updater.PROFILER_ANALYSIS_COST}/analysis")
EOF
```

### Step 8: Test Cost Savings Calculations

```bash
python3 << 'EOF'
from unittest.mock import MagicMock
from core.deduplication import DeduplicationStatsUpdater

mock_client = MagicMock()
stats_updater = DeduplicationStatsUpdater(mock_client)

# Test batch savings calculation
agno_stats = {'skipped': 10, 'copied': 5}
profiler_stats = {'skipped': 20, 'copied': 10}

savings = stats_updater.calculate_batch_savings(agno_stats, profiler_stats)

# Verify calculations
assert savings['agno_savings'] == 2.25  # 15 * $0.15
assert savings['profiler_savings'] == 1.50  # 30 * $0.05
assert savings['total_savings'] == 3.75
assert savings['avoided_analyses'] == 45

print(" Batch savings calculation verified")
print(f"   - Agno: ${savings['agno_savings']:.2f} (15 analyses)")
print(f"   - Profiler: ${savings['profiler_savings']:.2f} (30 analyses)")
print(f"   - Total: ${savings['total_savings']:.2f} (45 analyses)")
EOF
```

### Step 9: Test Monthly/Yearly Projections

```bash
python3 << 'EOF'
from unittest.mock import MagicMock
from core.deduplication import DeduplicationStatsUpdater

mock_client = MagicMock()
stats_updater = DeduplicationStatsUpdater(mock_client)

# Project savings with 5 Agno and 10 Profiler analyses avoided per day
projections = stats_updater.project_monthly_savings(
    daily_agno_avoided=5,
    daily_profiler_avoided=10
)

# Verify projections
# Monthly Agno: 5 * 30 * $0.15 = $22.50
assert projections['monthly_agno'] == 22.50
# Monthly Profiler: 10 * 30 * $0.05 = $15.00
assert projections['monthly_profiler'] == 15.00
# Monthly Total: $37.50
assert projections['monthly_total'] == 37.50
# Yearly: $37.50 * 12 = $450.00
assert projections['yearly_total'] == 450.00

print(" Projection calculations verified")
print(f"   - Monthly: ${projections['monthly_total']:.2f}")
print(f"   - Yearly: ${projections['yearly_total']:.2f}")
EOF
```

### Step 10: Test Skip Logic Behavior

```bash
python3 << 'EOF'
from unittest.mock import MagicMock
from core.deduplication import AgnoSkipLogic

mock_client = MagicMock()
agno_logic = AgnoSkipLogic(mock_client)

# Test with no concept ID (fresh submission)
submission = {'submission_id': 'sub123'}
should_run, reason = agno_logic.should_run_agno_analysis(submission, None)

assert should_run is True
assert reason == "No business concept (first submission)"
assert agno_logic.stats['fresh'] == 1

print(" Skip logic behavior verified")
print(f"   - Fresh submission detected: {should_run}")
print(f"   - Reason: {reason}")
print(f"   - Stats updated: fresh={agno_logic.stats['fresh']}")
EOF
```

### Step 11: Test Statistics Tracking

```bash
python3 << 'EOF'
from unittest.mock import MagicMock
from core.deduplication import AgnoSkipLogic

mock_client = MagicMock()
agno_logic = AgnoSkipLogic(mock_client)

# Simulate some operations
submission = {'submission_id': 'sub123'}
agno_logic.should_run_agno_analysis(submission, None)  # fresh += 1
agno_logic.should_run_agno_analysis(submission, None)  # fresh += 1

stats = agno_logic.get_statistics()
assert stats['fresh'] == 2
assert stats['skipped'] == 0
assert stats['copied'] == 0
assert stats['errors'] == 0

# Test reset
agno_logic.reset_statistics()
assert agno_logic.stats['fresh'] == 0

print(" Statistics tracking verified")
print("   - get_statistics() works correctly")
print("   - reset_statistics() resets to zero")
EOF
```

### Step 12: Verify Original Monolith Preserved

```bash
python3 << 'EOF'
with open('scripts/core/batch_opportunity_scoring.py', 'r') as f:
    content = f.read()

# Check functions still exist in original location
assert 'def should_run_agno_analysis(' in content
assert 'def copy_agno_from_primary(' in content
assert 'def should_run_profiler_analysis(' in content
assert 'def copy_profiler_from_primary(' in content
assert 'def update_concept_agno_stats(' in content
assert 'def update_concept_profiler_stats(' in content

# Find line numbers
lines = content.split('\n')
for i, line in enumerate(lines, 1):
    if 'def should_run_agno_analysis(' in line:
        print(f" should_run_agno_analysis at line {i}")
        break

for i, line in enumerate(lines, 1):
    if 'def should_run_profiler_analysis(' in line:
        print(f" should_run_profiler_analysis at line {i}")
        break

print(" Original monolith preserved (backward compatibility)")
EOF
```

### Step 13: Integration Test with Mock Data

```bash
python3 << 'EOF'
from unittest.mock import MagicMock, Mock
from core.deduplication import (
    BusinessConceptManager,
    AgnoSkipLogic,
    ProfilerSkipLogic,
    DeduplicationStatsUpdater
)

# Create mock client
mock_client = MagicMock()

# Initialize all components
concept_mgr = BusinessConceptManager(mock_client)
agno_logic = AgnoSkipLogic(mock_client)
profiler_logic = ProfilerSkipLogic(mock_client)
stats_updater = DeduplicationStatsUpdater(mock_client)

# Simulate a batch run
print("Simulating batch run...")

# Process 100 submissions
for i in range(100):
    submission = {'submission_id': f'sub{i}'}

    # Simulate 15% are duplicates (concept exists)
    if i % 7 == 0:  # ~14% have concept
        concept_id = i // 7

        # Mock concept with analysis
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {'id': concept_id, 'has_agno_analysis': True, 'has_ai_profiling': True}
        ]

        should_run_agno, _ = agno_logic.should_run_agno_analysis(submission, concept_id)
        should_run_profiler, _ = profiler_logic.should_run_profiler_analysis(submission, concept_id)

        # Both should skip
        assert should_run_agno is False
        assert should_run_profiler is False
    else:
        # Fresh submissions
        should_run_agno, _ = agno_logic.should_run_agno_analysis(submission, None)
        should_run_profiler, _ = profiler_logic.should_run_profiler_analysis(submission, None)

        # Both should run
        assert should_run_agno is True
        assert should_run_profiler is True

# Get statistics
agno_stats = agno_logic.get_statistics()
profiler_stats = profiler_logic.get_statistics()

print(f"\n Integration test complete")
print(f"   Agno - Fresh: {agno_stats['fresh']}, Skipped: {agno_stats['skipped']}")
print(f"   Profiler - Fresh: {profiler_stats['fresh']}, Skipped: {profiler_stats['skipped']}")

# Calculate savings
savings = stats_updater.calculate_batch_savings(agno_stats, profiler_stats)
print(f"   Total savings: ${savings['total_savings']:.2f}")
print(f"   Avoided analyses: {savings['avoided_analyses']}")
EOF
```

---

## Success Criteria

1.  **File Creation**: All 5 files exist in core/deduplication/
2.  **Module Imports**: All 4 components import successfully
3.  **BusinessConceptManager**: Interface and methods verified
4.  **AgnoSkipLogic**: Interface, stats tracking, and behavior verified
5.  **ProfilerSkipLogic**: Interface, stats tracking, and behavior verified
6.  **DeduplicationStatsUpdater**: Cost calculations correct
7.  **Cost Calculations**: Agno ($0.15) and Profiler ($0.05) costs accurate
8.  **Projections**: Monthly and yearly projections calculate correctly
9.  **Statistics Tracking**: get_statistics() and reset_statistics() work
10.  **Integration**: Components work together correctly
11.  **Original Monolith**: Functions preserved for backward compatibility

---

## Report Template

Save to: `docs/plans/unified-pipeline-refactoring/local-ai-report/phase-5-testing-report.md`

```markdown
# Phase 5 Testing Report - Deduplication System

**Date**: [DATE]
**Commit**: [HASH]
**Tester**: [NAME]

## Executive Summary
[PASS/FAIL] - Phase 5 extraction of deduplication system with $3,528/year cost savings...

## Test Results

### /L Module Creation
- core/deduplication/__init__.py: [STATUS]
- concept_manager.py: [STATUS]
- agno_skip_logic.py: [STATUS]
- profiler_skip_logic.py: [STATUS]
- stats_updater.py: [STATUS]

### /L Component Interfaces
- BusinessConceptManager: [STATUS]
  - Methods: get_or_create_concept, update_analysis_status, etc.
- AgnoSkipLogic: [STATUS]
  - Methods: should_run_agno_analysis, copy_agno_analysis, etc.
- ProfilerSkipLogic: [STATUS]
  - Methods: should_run_profiler_analysis, copy_profiler_analysis, etc.
- DeduplicationStatsUpdater: [STATUS]
  - Methods: update_savings, calculate_batch_savings, project_monthly_savings

### /L Cost Calculations
- Agno analysis cost ($0.15): [STATUS]
- Profiler analysis cost ($0.05): [STATUS]
- Batch savings calculation: [STATUS]
- Monthly/yearly projections: [STATUS]

### /L Statistics Tracking
- Initial stats (all zeros): [STATUS]
- get_statistics(): [STATUS]
- reset_statistics(): [STATUS]
- Stats updates on operations: [STATUS]

### /L Integration Test
- Components work together: [STATUS]
- Skip logic behavior correct: [STATUS]
- Savings calculations accurate: [STATUS]

### /L Backward Compatibility
- Original functions preserved: [STATUS]
- Monolith still functional: [STATUS]

## Cost Savings Validation

**Projected Annual Savings**: $3,528/year
- Agno deduplication: $[X]/year
- Profiler deduplication: $[Y]/year
- Total avoided analyses: [N]

## Issues Found
[List any issues]

## Recommendation
**[PASS/FAIL]** - Phase 5 COMPLETE: [YES/NO]

**Cost Savings Preserved**: [YES/NO]
```

---

## Expected Cost Savings

Based on historical data:
- **Agno analyses avoided**: ~11,760/year @ $0.15 = **$1,764/year**
- **Profiler analyses avoided**: ~35,280/year @ $0.05 = **$1,764/year**
- **Total savings**: **$3,528/year**

This deduplication system is CRITICAL for cost efficiency!

---

**Ready for Local AI Testing** >

This is Phase 5 of the unified pipeline refactoring. Once validated, proceed to Phase 6 (Extract AI Enrichment Services).
