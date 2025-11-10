# Function-Count Bias: One-Page Executive Summary

**Problem:** 95%+ of stored app opportunities list exactly 2 core functions.
**Root Cause:** NOT validator bias—**LLM prompt bias** cascading through pipeline fragmentation.
**Severity:** Medium (design fragility, not data loss)

---

## The Issue Explained

### Current Pipeline
```
Submission → Opportunity Scorer (returns: no functions)
           ↓ (if score ≥ 40)
           → LLM Profiler (prompt prefers 2; returns: ["F1", "F2"])
           ↓
           → Constraint Validator (counts: 2)
           ↓
           → workflow_results table (stores: core_functions = 2 as INTEGER)
           → app_opportunities table (stores: core_functions = ["F1", "F2"] as JSON)
                                                                    ↑ Dashboards read this
```

### Why 95% Are 2-Function Apps
1. **LLM Prompt** (llm_profiler.py:99–102):
   - "2 function apps get 85 simplicity points (GOOD)"
   - Temperature=0.3 → deterministic
   - **Intentional design, working as intended**

2. **Data Flow Fragmentation:**
   - `workflow_results.core_functions` = **INTEGER count** (2)
   - `app_opportunities.core_functions` = **JSON array** (["F1", "F2"])
   - Constraint validator writes integers; LLM profiler returns arrays
   - Two tables, two types, two sources of truth = **fragile architecture**

3. **No Post-Profiling Revalidation:**
   - Count is set once, never rechecked
   - If LLM response parsing breaks, count silently becomes 1 (placeholder)

---

## The Real Problem (Not Data, Design)

| Component | Finding | Issue |
|-----------|---------|-------|
| **LLM Prompt** | Prefers 2 functions | ✓ Intentional, correct |
| **Constraint Validator** | Counts correctly | ✓ Works as designed |
| **Schema Fragmentation** | Two tables, two types | ✗ **REAL ISSUE** |
| **Missing Validation** | No post-profiling check | ✗ **REAL ISSUE** |
| **NULL Handling** | Allows empty function_list | ✗ **REAL ISSUE** |

---

## Why This Matters

**Fragility Risks:**
1. Dashboard code is brittle (works with `app_opportunities.function_list` but fails if schema drifts)
2. If constraint validator changes, `workflow_results` breaks
3. Data audit trail split across two tables (hard to debug)
4. New engineers may not realize arrays and counts are in different tables

---

## The Fix (Phased, Zero Data Loss)

### Phase 1: Guardrails (2 hours) ← START HERE
**Where:** `core/dlt/constraint_validator.py` + `scripts/batch_opportunity_scoring.py`

**What:**
- Add `_validate_function_consistency()` to catch count/array mismatches
- Add pre-flight assertions in batch processor
- If count ≠ len(array), auto-correct and warn

**Why:** Catches bugs early, prevents bad data downstream

### Phase 2: Schema Unification (3 hours)
**Where:** `supabase/migrations/`, constraint_validator

**What:**
- Add `function_list` column to `workflow_results`
- Backfill from `app_opportunities`
- Add CHECK constraint: `core_functions = ARRAY_LENGTH(function_list, 1)`

**Why:** Single source of truth per table, prevents drifting counts

### Phase 3: Dashboard Update (3 hours)
**Where:** 3 marimo notebooks

**What:**
- Update queries to explicitly read `function_list` from correct table
- Handle both JSON array and string fallbacks

**Why:** Explicit is better than implicit; prevents future breaks

### Phase 4: Consolidation (Optional, next release)
**Where:** Create unified `app_opportunities_v2`

**What:**
- Merge `workflow_results` + `app_opportunities` into one table
- Single source of truth, eliminates fragmentation

**Why:** Simpler architecture, easier to debug

---

## Acceptance Test

```python
def test_function_count_healthy():
    """Verify no systemic bias (allowing LLM's intentional 2-preference)."""
    opportunities = load_all_opportunities()
    counts = [len(o.get("function_list", [])) for o in opportunities]

    # Must pass
    assert len(counts) >= 100, "Need ≥100 samples"
    assert all(1 <= c <= 3 for c in counts), "All must be 1-3 functions"
    assert None not in counts, "No NULLs"

    # Check for severe bias (>80% = bad; >60% = LLM bias, acceptable)
    from collections import Counter
    dist = Counter(counts)
    pct_2 = (dist.get(2, 0) / len(counts)) * 100

    if pct_2 > 80:
        print(f"⚠️  {pct_2:.1f}% are 2-function (possible bug)")
        assert False, "Suspicious distribution"
    else:
        print(f"✓ {pct_2:.1f}% are 2-function (LLM bias, acceptable)")
```

---

## Key Findings

### Your Premise (Partially Correct)
❌ "Profiler agent decides function counts" — Not quite.
✅ "Data arrives at wrong tables with mismatched types" — Exactly.
✅ "LLM bias cascades unchecked" — Correct.

### Actual Root Cause
**Schema fragmentation + architectural decision split** (not a profiler bug).

---

## Deliverables

1. **Diagnosis:** ✅ `/docs/diagnosis-function-count-bias.md` (detailed analysis)
2. **Migration Plan:** ✅ `/docs/function-count-migration-plan.md` (phased fix + SQL)
3. **Summary:** ✅ This document

---

## Next Steps

1. **Review** the detailed diagnosis for code paths and table column details
2. **Choose a phase:** Phase 1 (guardrails) has lowest risk; start immediately
3. **Test locally** using provided test cases before production deployment
4. **Monitor** with acceptance test after each phase

**No code executed.** Proposals only. Ready for review and approval.

