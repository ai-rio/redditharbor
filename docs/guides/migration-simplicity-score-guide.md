# Migration Guide: Simplicity Score & Opportunity Assessment

**Migration ID:** 20251114232013
**Status:** Ready for Review
**Risk Level:** LOW
**Estimated Time:** 30 seconds

## Quick Summary

This migration adds the missing 6th dimension (`simplicity_score`) to the opportunity assessment methodology and creates a consolidated `opportunity_assessment_score` that properly weights all 6 dimensions.

## Pre-Migration Checklist

- [ ] Review migration SQL file
- [ ] Review verification queries
- [ ] Backup database (if in production)
- [ ] Ensure Supabase is running: `supabase start`
- [ ] Check current schema: See `/home/carlos/projects/redditharbor/schema_dumps/current_complete_schema_20251114_230311.sql`

## Migration Files

All files are located in `/home/carlos/projects/redditharbor/supabase/migrations/`:

1. **20251114232013_add_simplicity_score_and_assessment.sql** - Main migration
2. **VERIFY_20251114232013_add_simplicity_score_and_assessment.sql** - Verification queries
3. **ROLLBACK_20251114232013_add_simplicity_score_and_assessment.sql** - Rollback script
4. **README_20251114232013.md** - Detailed documentation

## Apply Migration

### Step 1: Review the Migration

```bash
# View the migration file
cat /home/carlos/projects/redditharbor/supabase/migrations/20251114232013_add_simplicity_score_and_assessment.sql
```

### Step 2: Apply Using Supabase CLI (Recommended)

```bash
cd /home/carlos/projects/redditharbor
supabase db push
```

**Expected Output:**
```
Applying migration 20251114232013_add_simplicity_score_and_assessment...
Migration applied successfully
```

### Step 3: Verify the Migration

```bash
psql postgresql://postgres:postgres@127.0.0.1:54322/postgres \
  -f /home/carlos/projects/redditharbor/supabase/migrations/VERIFY_20251114232013_add_simplicity_score_and_assessment.sql
```

### Step 4: Check Results

Run quick validation queries:

```sql
-- 1. Check both columns exist
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'workflow_results'
  AND column_name IN ('simplicity_score', 'opportunity_assessment_score');

-- 2. Check data backfilled correctly
SELECT
  COUNT(*) as total,
  COUNT(simplicity_score) as with_simplicity,
  COUNT(opportunity_assessment_score) as with_assessment,
  ROUND(AVG(opportunity_assessment_score), 2) as avg_score
FROM workflow_results;

-- 3. View top opportunities
SELECT
  app_name,
  opportunity_assessment_score,
  simplicity_score,
  market_demand,
  pain_intensity
FROM workflow_results
WHERE opportunity_assessment_score IS NOT NULL
ORDER BY opportunity_assessment_score DESC
LIMIT 5;
```

## Expected Changes

### Schema Changes

**New Column 1: `simplicity_score`**
```sql
simplicity_score NUMERIC(5,2)
  CHECK (simplicity_score >= 0 AND simplicity_score <= 100)
```

**New Column 2: `opportunity_assessment_score`**
```sql
opportunity_assessment_score NUMERIC(5,2)
  GENERATED ALWAYS AS (
    COALESCE(market_demand, 0) * 0.20 +
    COALESCE(pain_intensity, 0) * 0.25 +
    COALESCE(monetization_potential, 0) * 0.20 +
    COALESCE(market_gap, 0) * 0.10 +
    COALESCE(technical_feasibility, 0) * 0.05 +
    COALESCE(simplicity_score, 0) * 0.20
  ) STORED
```

**New Index:**
```sql
CREATE INDEX idx_workflow_results_opportunity_assessment_score
  ON workflow_results(opportunity_assessment_score DESC);
```

### Data Changes

All existing `workflow_results` records will be backfilled:

- **simplicity_score** populated based on `function_count`/`core_functions`
- **opportunity_assessment_score** computed automatically from all 6 dimensions

## Validation Criteria

✅ **Migration Successful If:**

1. Both columns exist with correct types (`NUMERIC(5,2)`)
2. `opportunity_assessment_score` is a computed/generated column
3. `simplicity_score` has CHECK constraint (0-100 range)
4. Index `idx_workflow_results_opportunity_assessment_score` exists
5. All existing records have `simplicity_score` values (unless function_count was NULL)
6. All existing records have `opportunity_assessment_score` values
7. Assessment scores are within 0-100 range
8. Formula verification passes (manual calculation matches computed value)

❌ **Migration Failed If:**

1. Columns missing or wrong type
2. Constraints missing
3. Index missing
4. Backfill incomplete (many NULL values)
5. Scores out of range (< 0 or > 100)
6. Formula mismatch

## Troubleshooting

### Issue: Migration Fails with "column already exists"

**Solution:** The existing `simplicity_score` has wrong type. The migration handles this by dropping and recreating it.

```sql
-- Manual fix if needed
ALTER TABLE workflow_results DROP COLUMN IF EXISTS simplicity_score CASCADE;
-- Then re-run migration
```

### Issue: Backfill Incomplete (many NULL values)

**Diagnosis:**
```sql
SELECT
  COUNT(*) FILTER (WHERE function_count IS NULL AND core_functions IS NULL) as no_func_data,
  COUNT(*) FILTER (WHERE simplicity_score IS NULL) as null_simplicity
FROM workflow_results;
```

**Explanation:** If records have NULL for both `function_count` and `core_functions`, the backfill will set `simplicity_score = 0.0` (safe default).

### Issue: Assessment Score Seems Wrong

**Validation:**
```sql
SELECT
  app_name,
  opportunity_assessment_score,
  -- Manual calculation
  ROUND(
    COALESCE(market_demand, 0) * 0.20 +
    COALESCE(pain_intensity, 0) * 0.25 +
    COALESCE(monetization_potential, 0) * 0.20 +
    COALESCE(market_gap, 0) * 0.10 +
    COALESCE(technical_feasibility, 0) * 0.05 +
    COALESCE(simplicity_score, 0) * 0.20,
    2
  ) as expected_score,
  ABS(opportunity_assessment_score - (
    COALESCE(market_demand, 0) * 0.20 +
    COALESCE(pain_intensity, 0) * 0.25 +
    COALESCE(monetization_potential, 0) * 0.20 +
    COALESCE(market_gap, 0) * 0.10 +
    COALESCE(technical_feasibility, 0) * 0.05 +
    COALESCE(simplicity_score, 0) * 0.20
  )) as difference
FROM workflow_results
WHERE opportunity_assessment_score IS NOT NULL
LIMIT 10;
```

If `difference > 0.01`, there may be an issue with the computed column formula.

## Rollback Instructions

**WARNING:** Rollback will permanently delete data. Backup first!

```bash
# Create backup
pg_dump -U postgres -h 127.0.0.1 -p 54322 postgres > backup_before_rollback.sql

# Apply rollback
psql postgresql://postgres:postgres@127.0.0.1:54322/postgres \
  -f /home/carlos/projects/redditharbor/supabase/migrations/ROLLBACK_20251114232013_add_simplicity_score_and_assessment.sql

# Verify rollback
psql postgresql://postgres:postgres@127.0.0.1:54322/postgres -c "
  SELECT column_name
  FROM information_schema.columns
  WHERE table_name = 'workflow_results'
    AND column_name IN ('simplicity_score', 'opportunity_assessment_score');
"
```

## Post-Migration Tasks

After successful migration:

### 1. Update Application Code

**Python Example:**
```python
# workflows/opportunities/llm_profiler.py

def calculate_simplicity_score(function_count: int) -> float:
    """Calculate simplicity score based on function count."""
    if function_count == 1:
        return 100.0
    elif function_count == 2:
        return 85.0
    elif function_count == 3:
        return 70.0
    else:
        return 0.0

# When inserting records, include simplicity_score
record = {
    'opportunity_id': opp_id,
    'app_name': app_name,
    'function_count': func_count,
    'simplicity_score': calculate_simplicity_score(func_count),  # NEW
    'market_demand': scores['market_demand'],
    'pain_intensity': scores['pain_intensity'],
    # ... other dimensions
    # opportunity_assessment_score computed automatically
}
```

### 2. Update Queries to Use New Score

**Old Way:**
```python
# Query using legacy final_score
top_opportunities = supabase.table('workflow_results') \
    .select('*') \
    .order('final_score', desc=True) \
    .limit(10) \
    .execute()
```

**New Way (Recommended):**
```python
# Query using new opportunity_assessment_score
top_opportunities = supabase.table('workflow_results') \
    .select('*') \
    .order('opportunity_assessment_score', desc=True) \
    .limit(10) \
    .execute()
```

### 3. Update Dashboards and Reports

Add all 6 dimensions to reporting:

```python
# Example: Generate opportunity report
def generate_opportunity_report(opportunity_id: str):
    result = supabase.table('workflow_results') \
        .select('*') \
        .eq('opportunity_id', opportunity_id) \
        .single() \
        .execute()

    report = {
        'app_name': result.data['app_name'],
        'overall_score': result.data['opportunity_assessment_score'],
        'dimensions': {
            'market_demand': result.data['market_demand'],          # 20%
            'pain_intensity': result.data['pain_intensity'],        # 25%
            'monetization': result.data['monetization_potential'],  # 20%
            'market_gap': result.data['market_gap'],                # 10%
            'technical_feasibility': result.data['technical_feasibility'], # 5%
            'simplicity': result.data['simplicity_score']           # 20% NEW
        }
    }
    return report
```

### 4. Update Documentation

- [ ] Update API documentation to include new columns
- [ ] Update methodology documentation with complete 6-dimension formula
- [ ] Update data dictionary with column descriptions
- [ ] Add migration to changelog

## Reference: Complete Methodology Formula

```
Opportunity Assessment Score =
  (market_demand × 20%) +           // Discussion volume, engagement, trends
  (pain_intensity × 25%) +          // Sentiment, emotion, workarounds
  (monetization_potential × 20%) +  // Willingness to pay, revenue signals
  (market_gap × 10%) +              // Competition, solution inadequacy
  (technical_feasibility × 5%) +    // Development complexity
  (simplicity_score × 20%)          // Function count simplicity

Where simplicity_score is:
  1 function  → 100.0 (single-purpose)
  2 functions → 85.0  (focused)
  3 functions → 70.0  (moderate)
  4+ functions → 0.0  (complex, disqualified)

All scores range from 0-100
Total weights: 100%
```

## Support

If you encounter issues:

1. **Check migration logs** in the Supabase output
2. **Run verification script** for detailed diagnostics
3. **Review schema dumps** in `/home/carlos/projects/redditharbor/schema_dumps/`
4. **Check application logs** for any errors after migration
5. **Consult README** at `/home/carlos/projects/redditharbor/supabase/migrations/README_20251114232013.md`

## Related Files

- Migration SQL: `/home/carlos/projects/redditharbor/supabase/migrations/20251114232013_add_simplicity_score_and_assessment.sql`
- Verification: `/home/carlos/projects/redditharbor/supabase/migrations/VERIFY_20251114232013_add_simplicity_score_and_assessment.sql`
- Rollback: `/home/carlos/projects/redditharbor/supabase/migrations/ROLLBACK_20251114232013_add_simplicity_score_and_assessment.sql`
- Documentation: `/home/carlos/projects/redditharbor/supabase/migrations/README_20251114232013.md`
- Current Schema: `/home/carlos/projects/redditharbor/schema_dumps/current_complete_schema_20251114_230311.sql`
