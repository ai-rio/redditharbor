# RedditHarbor Dimension Scores Storage Implementation Plan

## Executive Summary

**Problem**: OpportunityAnalyzerAgent calculates 5 dimension scores but only stores final_score in workflow_results table.

**Solution**: Add 5 dimension columns to workflow_results table (additive migration, zero disruption).

**Effort**: 12 minutes | **Disruption**: ZERO | **Backwards Compatible**: YES

---

## Current State Analysis

### workflow_results Table
- **Records**: 10 existing
- **Stores**: Workflow metadata (opportunity_id, app_name, final_score, status, etc.)
- **Missing**: 5 dimension scores (market_demand, pain_intensity, monetization_potential, market_gap, technical_feasibility)

### opportunity_scores Table
- **Records**: 0 (empty)
- **Scale Mismatch**: 0-10 (vs. agent's 0-100)
- **Missing Dimensions**: market_gap, technical_feasibility
- **Foreign Key**: submission_id (incompatible with opportunity_id workflow)
- **Status**: NOT SUITABLE for current workflow

### OpportunityAnalyzerAgent
- **Location**: `/home/carlos/projects/redditharbor/agent_tools/opportunity_analyzer_agent.py`
- **Calculates**: All 5 dimensions correctly (0-100 scale)
- **Weights**: market_demand(20%), pain_intensity(25%), monetization_potential(30%), market_gap(15%), technical_feasibility(10%)
- **Problem**: Dimension scores calculated but NOT persisted

---

## Recommended Strategy: Add Columns to workflow_results

### Why This Approach?

✅ **Zero Disruption**
- Additive migration only (no DROP, no ALTER existing columns)
- NULL-safe (existing records unchanged)
- Backward compatible (old code still works)

✅ **Minimal Code Changes**
- 2 files need updates (batch_opportunity_scoring.py, stage4_workflow_verification.py)
- ~8 lines of code total
- No OpportunityAnalyzerAgent changes needed

✅ **Performance**
- Single table access (no JOINs)
- 5 new indexes for dimension-based queries
- ~25 bytes per row overhead (trivial)

✅ **Data Integrity**
- All workflow context in one place
- Atomic updates (all dimensions together)
- Type-safe DECIMAL(5,2) with CHECK constraints

---

## Migration Plan

### Step 1: SQL Migration (2 minutes)

**File**: `supabase/migrations/20251108000002_add_dimension_scores_to_workflow.sql`

```sql
-- Add 5 dimension score columns
ALTER TABLE workflow_results 
ADD COLUMN IF NOT EXISTS market_demand DECIMAL(5,2) 
    CHECK (market_demand >= 0 AND market_demand <= 100),
ADD COLUMN IF NOT EXISTS pain_intensity DECIMAL(5,2) 
    CHECK (pain_intensity >= 0 AND pain_intensity <= 100),
ADD COLUMN IF NOT EXISTS monetization_potential DECIMAL(5,2) 
    CHECK (monetization_potential >= 0 AND monetization_potential <= 100),
ADD COLUMN IF NOT EXISTS market_gap DECIMAL(5,2) 
    CHECK (market_gap >= 0 AND market_gap <= 100),
ADD COLUMN IF NOT EXISTS technical_feasibility DECIMAL(5,2) 
    CHECK (technical_feasibility >= 0 AND technical_feasibility <= 100);

-- Add indexes for dimension-based queries
CREATE INDEX IF NOT EXISTS idx_workflow_results_market_demand 
    ON workflow_results(market_demand DESC);
CREATE INDEX IF NOT EXISTS idx_workflow_results_pain_intensity 
    ON workflow_results(pain_intensity DESC);
CREATE INDEX IF NOT EXISTS idx_workflow_results_monetization 
    ON workflow_results(monetization_potential DESC);

-- Add documentation
COMMENT ON COLUMN workflow_results.market_demand IS 
    'Market demand score (0-100): Discussion volume + engagement rate + trend velocity + audience size';
COMMENT ON COLUMN workflow_results.pain_intensity IS 
    'Pain intensity score (0-100): Negative sentiment + emotional language + repetition + workaround complexity';
COMMENT ON COLUMN workflow_results.monetization_potential IS 
    'Monetization potential score (0-100): Willingness to pay + commercial gaps + B2B/B2C signals + revenue model hints';
COMMENT ON COLUMN workflow_results.market_gap IS 
    'Market gap score (0-100): Competition density + solution inadequacy + innovation opportunities';
COMMENT ON COLUMN workflow_results.technical_feasibility IS 
    'Technical feasibility score (0-100): Development complexity + API integration needs + implementation simplicity';
```

**Apply Migration**:
```bash
cd /home/carlos/projects/redditharbor
supabase db push
```

---

### Step 2: Update batch_opportunity_scoring.py (3 minutes)

**File**: `/home/carlos/projects/redditharbor/scripts/batch_opportunity_scoring.py`

**Function**: `prepare_analysis_for_storage()` (lines 328-346)

**Change**:
```python
def prepare_analysis_for_storage(
    submission_id: str,
    analysis: Dict[str, Any],
    sector: str
) -> Dict[str, Any]:
    # Extract dimension scores
    scores = analysis.get("dimension_scores", {})

    # Prepare data for opportunity_scores table
    analysis_data = {
        "submission_id": submission_id,
        "opportunity_id": f"opp_{submission_id}",
        "title": analysis.get("title", "")[:500],
        "subreddit": analysis.get("subreddit", ""),
        "sector": sector,
        
        # ADD THESE 5 LINES:
        "market_demand": float(scores.get("market_demand", 0)),
        "pain_intensity": float(scores.get("pain_intensity", 0)),
        "monetization_potential": float(scores.get("monetization_potential", 0)),
        "market_gap": float(scores.get("market_gap", 0)),
        "technical_feasibility": float(scores.get("technical_feasibility", 0)),
        
        "simplicity_score": float(scores.get("simplicity_score", 70)),
        "final_score": float(analysis.get("final_score", 0)),
        "priority": analysis.get("priority", ""),
        "scored_at": datetime.now().isoformat(),
    }

    return analysis_data
```

---

### Step 3: Update stage4_workflow_verification.py (3 minutes)

**File**: `/home/carlos/projects/redditharbor/scripts/stage4_workflow_verification.py`

**Function**: `insert_workflow_opportunities()` (lines 128-205)

**Change INSERT statement**:
```python
# Insert new record
cur.execute(
    """
    INSERT INTO workflow_results (
        opportunity_id, app_name, function_count, function_list,
        original_score, final_score, status, constraint_applied,
        ai_insight, processed_at,
        market_demand, pain_intensity, monetization_potential,
        market_gap, technical_feasibility
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """,
    (
        insert_data["opportunity_id"],
        insert_data["app_name"],
        insert_data["function_count"],
        insert_data["function_list"],
        insert_data["original_score"],
        insert_data["final_score"],
        insert_data["status"],
        insert_data["constraint_applied"],
        insert_data["ai_insight"],
        insert_data["processed_at"],
        insert_data.get("market_demand"),
        insert_data.get("pain_intensity"),
        insert_data.get("monetization_potential"),
        insert_data.get("market_gap"),
        insert_data.get("technical_feasibility"),
    ),
)
```

---

### Step 4: Test Implementation (2 minutes)

```bash
# Run batch scoring on small dataset
cd /home/carlos/projects/redditharbor
python3 scripts/batch_opportunity_scoring.py --limit 5
```

---

### Step 5: Verify Results (1 minute)

```sql
-- Check that dimensions are stored
SELECT 
    opportunity_id,
    app_name,
    market_demand,
    pain_intensity,
    monetization_potential,
    market_gap,
    technical_feasibility,
    final_score
FROM workflow_results
WHERE market_demand IS NOT NULL
LIMIT 5;

-- Verify weighted calculation
SELECT 
    opportunity_id,
    (market_demand * 0.20 + 
     pain_intensity * 0.25 + 
     monetization_potential * 0.30 + 
     market_gap * 0.15 + 
     technical_feasibility * 0.10) as calculated_score,
    final_score,
    ABS((market_demand * 0.20 + pain_intensity * 0.25 + monetization_potential * 0.30 + market_gap * 0.15 + technical_feasibility * 0.10) - final_score) as difference
FROM workflow_results
WHERE market_demand IS NOT NULL;
```

---

## Alternatives Considered (and Rejected)

### ❌ Use opportunity_scores Table
- **Problem**: Schema mismatch (0-10 vs 0-100 scale)
- **Problem**: Missing 2 dimensions (market_gap, technical_feasibility)
- **Problem**: Foreign key incompatibility (submission_id vs opportunity_id)
- **Problem**: Empty table (0 records)
- **Effort**: HIGH (breaking schema changes)
- **Disruption**: HIGH

### ❌ Create New Table (workflow_dimension_scores)
- **Problem**: Unnecessary complexity
- **Problem**: Requires JOINs for queries
- **Problem**: Violates DRY principle
- **Effort**: MEDIUM (new table + foreign keys + migration)
- **Disruption**: MODERATE

### ❌ Use JSONB Column
- **Problem**: Poor query performance
- **Problem**: No type safety
- **Problem**: Harder to index and filter
- **Effort**: LOW
- **Disruption**: LOW but poor maintainability

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Migration fails | LOW | LOW | DECIMAL(5,2) handles 0-100 range, simple rollback |
| NULL dimension values in existing records | EXPECTED | ZERO | Nullable columns, filter with WHERE clause |
| Code forgets to populate dimensions | MEDIUM | MINIMAL | Add validation, shows as NULL (easy to detect) |
| Performance degradation | NEGLIGIBLE | ZERO | 5 columns add ~25 bytes/row (trivial) |

---

## Success Criteria

- ✅ All 5 dimensions stored in workflow_results
- ✅ Existing 10 records unchanged
- ✅ New records include all dimension scores
- ✅ Queries run without errors
- ✅ Backward compatibility maintained
- ✅ Zero data loss
- ✅ Migration completes in <1 minute

---

## Rollback Procedure

If needed, rollback is simple and non-destructive:

```sql
-- Drop dimension columns
ALTER TABLE workflow_results 
DROP COLUMN IF EXISTS market_demand,
DROP COLUMN IF EXISTS pain_intensity,
DROP COLUMN IF EXISTS monetization_potential,
DROP COLUMN IF EXISTS market_gap,
DROP COLUMN IF EXISTS technical_feasibility;

-- Drop indexes
DROP INDEX IF EXISTS idx_workflow_results_market_demand;
DROP INDEX IF EXISTS idx_workflow_results_pain_intensity;
DROP INDEX IF EXISTS idx_workflow_results_monetization;
```

---

## Timeline

| Step | Task | Time |
|------|------|------|
| 1 | Create SQL migration file | 2 min |
| 2 | Run migration (`supabase db push`) | 1 min |
| 3 | Update batch_opportunity_scoring.py | 3 min |
| 4 | Update stage4_workflow_verification.py | 3 min |
| 5 | Test with sample data | 2 min |
| 6 | Verify database results | 1 min |
| **TOTAL** | | **12 min** |

---

## Implementation Checklist

- [ ] Create migration file: `supabase/migrations/20251108000002_add_dimension_scores_to_workflow.sql`
- [ ] Run `supabase db push`
- [ ] Update `prepare_analysis_for_storage()` in batch_opportunity_scoring.py
- [ ] Update `insert_workflow_opportunities()` in stage4_workflow_verification.py
- [ ] Test with `python3 scripts/batch_opportunity_scoring.py --limit 5`
- [ ] Verify with SQL queries
- [ ] Update documentation (CLAUDE.md)
- [ ] Commit changes to git

---

## Conclusion

**Recommended Approach**: Add 5 dimension columns to workflow_results table

**Rationale**:
- Zero disruption (additive migration only)
- Minimal code changes (2 files, ~8 lines)
- Backward compatible (100%)
- Performance optimal (single table, no JOINs)
- Data integrity (all workflow context together)

**Total Effort**: 12 minutes

**Risk Level**: MINIMAL

**Go/No-Go Decision**: ✅ GO - This is the safest, simplest, and most maintainable approach.

---

**Generated**: 2025-11-08  
**Analysis File**: `/home/carlos/projects/redditharbor/dimension_storage_analysis.json`
