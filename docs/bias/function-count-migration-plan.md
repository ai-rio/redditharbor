# Function-Count Bias: Migration & Repair Plan
**Status:** Proposed (No execution)
**Complexity:** Medium | **Risk:** Low-Medium | **Duration:** 2–3 days

---

## Current State

**Data Issue:**
- `workflow_results.core_functions` = INTEGER (stores count only)
- `app_opportunities.core_functions` = JSON (stores array of function names)
- Dashboards read from `app_opportunities` (accidentally correct)
- Actual function list data is in `app_opportunities`, count in `workflow_results`

**Observation:**
- ~95% of app_opportunities have exactly 2 core functions
- Root: LLM prompt bias ("2 function apps get 85 simplicity points GOOD")
- NOT a validator bug—prompt is doing its job

---

## Recommended Approach: Option B + Option A (Phased)

### Phase 1: Immediate Guardrails (Week 1)
**Goal:** Stop data inconsistency from worsening; add early warning.

#### 1.1 Add Post-Profiling Validation
**File:** `core/dlt/constraint_validator.py`

```python
def _validate_function_consistency(opportunity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure function_count matches len(function_list).
    Auto-corrects minor mismatches, raises on structural errors.
    """
    function_list = opportunity.get("function_list", [])
    function_count = opportunity.get("core_functions", 0)

    # Type check
    if not isinstance(function_list, list):
        raise ValueError(
            f"function_list must be list, got {type(function_list).__name__}: {function_list}"
        )

    # Count mismatch
    actual_count = len(function_list)
    if actual_count != function_count:
        print(
            f"⚠️  MISMATCH in {opportunity.get('opportunity_id', 'unknown')}: "
            f"core_functions={function_count} but function_list={actual_count}"
        )
        opportunity["function_count"] = actual_count  # Auto-correct
        opportunity["core_functions"] = actual_count

    # Emptiness check
    if actual_count == 0:
        raise ValueError(f"Opportunity {opportunity.get('opportunity_id')} has empty function_list")

    return opportunity
```

**Integration:**
```python
@dlt.resource(...)
def app_opportunities_with_constraint(opportunities: List[Dict[str, Any]]):
    for opportunity in opportunities:
        core_functions = _extract_core_functions(opportunity)
        function_count = len(core_functions)

        # ... existing logic ...

        opportunity["core_functions"] = function_count
        opportunity["function_list"] = core_functions

        # NEW: Validate consistency before yielding
        opportunity = _validate_function_consistency(opportunity)

        yield opportunity
```

**Test:**
```bash
pytest tests/test_constraint_validator.py::test_function_consistency -v
```

---

#### 1.2 Add Schema Assertions to Batch Processor
**File:** `scripts/batch_opportunity_scoring.py`

```python
def load_scores_to_supabase_via_dlt(scored_opportunities: List[Dict[str, Any]]) -> bool:
    # NEW: Pre-flight checks
    if not scored_opportunities:
        print("⚠️  No scored opportunities to load")
        return False

    # Check: Every opportunity has function_list
    missing_functions = [
        o["opportunity_id"] for o in scored_opportunities
        if not o.get("function_list")
    ]
    if missing_functions:
        print(f"❌ ERROR: {len(missing_functions)} opportunities missing function_list:")
        for opp_id in missing_functions[:5]:
            print(f"  - {opp_id}")
        raise ValueError(f"Cannot load: {len(missing_functions)} missing function_list")

    # Check: function_count matches function_list length
    mismatches = [
        o for o in scored_opportunities
        if len(o.get("function_list", [])) != o.get("function_count")
    ]
    if mismatches:
        print(f"⚠️  WARNING: {len(mismatches)} opportunities have count/list mismatch")
        for opp in mismatches[:3]:
            print(f"  - {opp['opportunity_id']}: count={opp.get('function_count')}, "
                  f"actual={len(opp.get('function_list', []))}")

    # Continue loading (validator will auto-correct)
    ...
```

**Location:** Insert after line 395 in `batch_opportunity_scoring.py`

---

### Phase 2: Schema Migration (Week 2)
**Goal:** Unify function data representation.

#### 2.1 Add function_list Column to workflow_results
**File:** `supabase/migrations/20251111000001_add_function_list_to_workflow.sql`

```sql
-- Add function_list column to workflow_results
ALTER TABLE workflow_results
ADD COLUMN function_list JSONB DEFAULT NULL;

-- Index for future queries
CREATE INDEX idx_workflow_results_function_list ON workflow_results USING gin(function_list);

-- Backfill from app_opportunities where possible
UPDATE workflow_results wr
SET function_list = ao.function_list
FROM app_opportunities ao
WHERE wr.submission_id = ao.submission_id
  AND wr.function_list IS NULL;

-- Log backfill count
SELECT COUNT(*) as backfilled
FROM workflow_results
WHERE function_list IS NOT NULL;
```

**Execution:**
```bash
supabase db push  # Or manually in Supabase Studio
```

**Verify:**
```sql
SELECT COUNT(*) as total,
       COUNT(function_list) as with_functions,
       COUNT(*) FILTER (WHERE function_list IS NULL) as still_null
FROM workflow_results;
```

---

#### 2.2 Add Constraint Check (optional, phase 2b)
**File:** `supabase/migrations/20251111000002_add_function_check.sql`

```sql
-- Add CHECK constraint to enforce count = array length
ALTER TABLE workflow_results
ADD CONSTRAINT chk_function_count_matches_array
CHECK (
    (function_list IS NULL) OR
    (ARRAY_LENGTH(function_list, 1) = core_functions)
);
```

**Note:** This is optional and can be deferred to phase 3 (breaking change risk).

---

### Phase 3: Dashboard Update (Week 2–3)
**Goal:** Ensure dashboards read correct data type.

#### 3.1 Update Marimo Dashboards
**Files:**
- `marimo_notebooks/opportunity_dashboard_reactive.py`
- `marimo_notebooks/opportunity_dashboard_fixed.py`
- `marimo_notebooks/ultra_rare_dashboard.py`

**Change:** Query `function_list` from `app_opportunities` (as JSON array) instead of `core_functions` (INT count).

**Before:**
```python
core_functions = opp.get('core_functions', [])  # INT count
if isinstance(core_functions, str):
    core_functions = eval(core_functions)
functions_text = "\n".join([f"• {func}" for func in core_functions])
```

**After:**
```python
function_list = opp.get('function_list', [])  # JSON array
if isinstance(function_list, str):
    try:
        function_list = json.loads(function_list)
    except:
        function_list = [function_list]
functions_text = "\n".join([f"• {func}" for func in function_list])
```

**Query Update:**
```python
# Before
'submission_id, opportunity_score, problem_description, app_concept, core_functions, target_user'

# After
'submission_id, opportunity_score, problem_description, app_concept, function_list, target_user'
```

---

### Phase 4: Future Consolidation (Week 3+, Optional)
**Goal:** Single source of truth (Option A from diagnosis).

#### 4.1 Decide: Keep Both Tables or Consolidate
**Decision Tree:**
- **Keep both if:** Code is heavily dependent on two separate tables
- **Consolidate if:** Planning major refactor or preparing for production v2

**If consolidating, create migration:**
```sql
-- Create unified app_opportunities_v2
CREATE TABLE app_opportunities_v2 AS
SELECT
    ao.*,
    wr.function_count,
    wr.market_demand,
    wr.pain_intensity,
    wr.monetization_potential,
    wr.market_gap,
    wr.technical_feasibility,
    wr.simplicity_score
FROM app_opportunities ao
LEFT JOIN workflow_results wr ON wr.submission_id = ao.submission_id;

-- Archive old tables
ALTER TABLE app_opportunities RENAME TO app_opportunities_deprecated;
ALTER TABLE workflow_results RENAME TO workflow_results_deprecated;
ALTER TABLE app_opportunities_v2 RENAME TO app_opportunities;

-- Update all foreign keys and views
-- ...
```

**Risk:** High, deferred to v2.

---

## Data Repair (Non-Destructive)

### Current Data State
```sql
-- Audit current state
SELECT
    COUNT(*) as total_records,
    COUNT(DISTINCT CASE WHEN function_list IS NULL THEN 1 END) as missing_function_list,
    COUNT(DISTINCT CASE WHEN core_functions != ARRAY_LENGTH(function_list, 1) THEN 1 END) as mismatched_counts
FROM app_opportunities;
```

### Repair Approach: Version-Based
**Goal:** Preserve original data, add corrected versions.

```sql
-- Add version column to track corrections
ALTER TABLE app_opportunities
ADD COLUMN function_list_version INT DEFAULT 1;

-- Mark records as "repaired" after validation
UPDATE app_opportunities
SET function_list_version = 2
WHERE function_list IS NOT NULL
  AND ARRAY_LENGTH(function_list, 1) > 0;

-- Log all repairs
CREATE TABLE function_list_repairs (
    repair_id SERIAL PRIMARY KEY,
    opportunity_id TEXT,
    old_count INT,
    new_count INT,
    repaired_at TIMESTAMP DEFAULT NOW(),
    auto_corrected BOOLEAN DEFAULT FALSE
);
```

---

## Testing & Validation

### Unit Tests
**File:** `tests/test_constraint_validator.py` (new)

```python
import pytest
from core.dlt.constraint_validator import (
    _extract_core_functions,
    _validate_function_consistency,
    app_opportunities_with_constraint
)

def test_function_consistency_pass():
    """Valid: count matches array length."""
    opp = {
        "opportunity_id": "test_1",
        "function_list": ["Track", "Log"],
        "core_functions": 2
    }
    result = _validate_function_consistency(opp)
    assert result["core_functions"] == 2
    assert len(result["function_list"]) == 2

def test_function_consistency_auto_correct():
    """Mismatch: count corrected to match array."""
    opp = {
        "opportunity_id": "test_2",
        "function_list": ["Track"],
        "core_functions": 2  # Wrong
    }
    result = _validate_function_consistency(opp)
    assert result["core_functions"] == 1  # Auto-corrected
    assert len(result["function_list"]) == 1

def test_function_consistency_empty_fails():
    """Empty: raises error."""
    opp = {
        "opportunity_id": "test_3",
        "function_list": [],
        "core_functions": 0
    }
    with pytest.raises(ValueError):
        _validate_function_consistency(opp)

def test_constraint_validator_limits_to_3():
    """LLM limit: validator clips to 3 functions."""
    opp = {
        "opportunity_id": "test_4",
        "function_list": ["F1", "F2", "F3", "F4"],  # 4 functions
        "app_description": None
    }
    validated = list(app_opportunities_with_constraint([opp]))
    assert validated[0]["is_disqualified"] == True
    assert validated[0]["core_functions"] == 4

def test_distribution_not_spiked():
    """Distribution: no >80% concentration on single count."""
    # Generate test data with LLM bias
    test_opps = [
        {"opportunity_id": f"opp_{i}", "function_list": ["F1", "F2"]}
        for i in range(100)
    ]
    validated = list(app_opportunities_with_constraint(test_opps))
    counts = [v["core_functions"] for v in validated]

    from collections import Counter
    dist = Counter(counts)
    pct_2 = (dist[2] / len(counts)) * 100

    # Allow LLM bias up to 80%, fail if higher (indicates bug)
    assert pct_2 <= 80, f"Suspicious distribution: {pct_2}% are 2-function apps"
```

**Run:**
```bash
pytest tests/test_constraint_validator.py -v --tb=short
```

---

### Integration Test
**File:** `scripts/test_function_count_repair.py` (one-off)

```python
#!/usr/bin/env python3
"""
Integration test: Load sample opportunities, validate repairs, audit distribution.
Run this AFTER schema migration and before full deployment.
"""

import sys
import json
from pathlib import Path
from collections import Counter

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.dlt.constraint_validator import app_opportunities_with_constraint
from config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client

def test_function_count_distribution():
    """Verify distribution is healthy (not spiked at 2)."""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Fetch all opportunities
    response = supabase.table("app_opportunities").select(
        "opportunity_id, function_list, core_functions"
    ).execute()

    opportunities = response.data if response.data else []
    print(f"Testing {len(opportunities)} opportunities...")

    # Extract counts
    counts = []
    for opp in opportunities:
        fl = opp.get("function_list", [])
        if isinstance(fl, str):
            fl = json.loads(fl) if fl else []
        counts.append(len(fl))

    # Distribution
    dist = Counter(counts)
    print(f"\nFunction Count Distribution:")
    for count in sorted(dist.keys()):
        pct = (dist[count] / len(counts)) * 100
        bar = "█" * int(pct / 5)
        print(f"  {count} functions: {dist[count]:3d} ({pct:5.1f}%) {bar}")

    # Assertions
    assert len(counts) >= 100, f"Need ≥100 samples, got {len(counts)}"
    assert all(1 <= c <= 3 for c in counts), f"Found out-of-range: {set(counts)}"

    pct_2 = (dist.get(2, 0) / len(counts)) * 100
    if pct_2 > 80:
        print(f"\n⚠️  WARNING: {pct_2:.1f}% are 2-function apps (indicates LLM bias, not a bug)")
    else:
        print(f"\n✓ Distribution is healthy: {pct_2:.1f}% are 2-function apps")

    print("\n✅ Function count distribution test PASSED")
    return True

if __name__ == "__main__":
    try:
        test_function_count_distribution()
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        sys.exit(1)
```

**Run After Migration:**
```bash
python scripts/test_function_count_repair.py
```

---

## Rollback Plan

If issues arise:

1. **Revert migration (schema):**
   ```sql
   ALTER TABLE workflow_results DROP COLUMN function_list;
   DROP INDEX idx_workflow_results_function_list;
   ```

2. **Revert code changes:**
   ```bash
   git revert <commit-hash>
   ```

3. **Restore dashboards:**
   ```bash
   git checkout -- marimo_notebooks/
   ```

**Rollback is safe:** All changes are additive; no data is deleted.

---

## Success Criteria

- ✅ All opportunities have non-empty `function_list`
- ✅ `function_count` matches `len(function_list)` (or auto-corrected)
- ✅ No NULL values in `function_list` (post-migration)
- ✅ Distribution audit shows <80% concentration at 2 functions (or explicitly documents LLM bias)
- ✅ Dashboards render function lists correctly
- ✅ Validation warnings logged for all mismatches
- ✅ Zero opportunities with 0 or >3 functions in production table

---

## Effort Estimate

| Phase | Task | Effort | Risk |
|-------|------|--------|------|
| 1.1 | Add validation function | 1 hour | LOW |
| 1.2 | Add schema assertions | 1 hour | LOW |
| 2.1 | Write SQL migration | 2 hours | LOW |
| 2.2 | Add CHECK constraint | 1 hour | MEDIUM |
| 3.1 | Update dashboards (3 files) | 3 hours | LOW |
| 4.1 | Consolidation (optional) | 1–2 days | HIGH |
| Testing | Unit + integration tests | 2 hours | LOW |
| **Total** | **All phases** | **~12 hours** | **LOW-MEDIUM** |

---

## Decision Checkpoints

- [ ] Phase 1 approved? Deploy guardrails immediately.
- [ ] Phase 2 approved? Schedule schema migration window (low-traffic time).
- [ ] Phase 3 approved? Update dashboards in staging first.
- [ ] Phase 4 decision? Keep both tables or consolidate?

