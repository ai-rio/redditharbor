# Trust Schema Quick Fix Guide
**Created**: 2025-11-13
**For**: Resolving trust indicator schema issues

## Quick Diagnosis (30 seconds)

Once database is online, run:

```bash
# Start Supabase (if not running)
supabase start

# Quick check
python3 scripts/check_db_direct.py
```

## Problem Scenarios & Solutions

### Scenario 1: Trust indicators are NULL
**Symptom**: `app_opportunities_trust` table has data but `trust_score`, `trust_badge`, `activity_score` are NULL

**Root Cause**: Trust validation step failing or not running

**Solution**:
```bash
# Re-run trust pipeline with verbose logging
python3 scripts/dlt/dlt_trust_pipeline.py --limit 10

# Check for errors in trust validation step (Step 3)
# Look for "✅ Trust Level: ..." messages
```

**Code Fix** (if trust validation is failing):
Edit `/home/carlos/projects/redditharbor/scripts/dlt/dlt_trust_pipeline.py`, line 391-393:

```python
except Exception as e:
    print(f"    ❌ Error: {e}")
    import traceback
    traceback.print_exc()  # Add this line for debugging
    continue
```

### Scenario 2: Wrong schema (public_staging vs public)
**Symptom**: Data exists in `public_staging.app_opportunities_trust` but not in `public.app_opportunities_trust`

**Root Cause**: DLT writing to staging schema instead of public

**Quick Fix - Migrate Data**:
```sql
-- Connect to database
-- Run this migration to copy data from staging to public

INSERT INTO public.app_opportunities_trust
SELECT * FROM public_staging.app_opportunities_trust
ON CONFLICT (submission_id) DO UPDATE SET
    trust_score = EXCLUDED.trust_score,
    trust_badge = EXCLUDED.trust_badge,
    activity_score = EXCLUDED.activity_score,
    trust_level = EXCLUDED.trust_level,
    engagement_level = EXCLUDED.engagement_level,
    trend_velocity = EXCLUDED.trend_velocity,
    problem_validity = EXCLUDED.problem_validity,
    discussion_quality = EXCLUDED.discussion_quality,
    ai_confidence_level = EXCLUDED.ai_confidence_level,
    trust_validation_timestamp = EXCLUDED.trust_validation_timestamp,
    trust_validation_method = EXCLUDED.trust_validation_method;
```

**Permanent Fix - Update DLT Config**:
Edit `/home/carlos/projects/redditharbor/scripts/dlt/dlt_trust_pipeline.py`, line 535:

```python
dataset_name="public"  # Already correct - verify this line exists
```

If it says `"public_staging"` or anything else, change it to `"public"`.

### Scenario 3: Table doesn't exist
**Symptom**: Error accessing `app_opportunities_trust` table

**Root Cause**: DLT pipeline never ran or table creation failed

**Solution**:
```bash
# Run DLT trust pipeline to create table and populate data
python3 scripts/dlt/dlt_trust_pipeline.py --limit 5 --test-mode
```

**Manual Table Creation** (if DLT fails):
```sql
CREATE TABLE IF NOT EXISTS public.app_opportunities_trust (
    submission_id TEXT PRIMARY KEY,
    problem_description TEXT,
    app_concept TEXT,
    core_functions TEXT,
    value_proposition TEXT,
    target_user TEXT,
    monetization_model TEXT,
    opportunity_score FLOAT,
    title TEXT,
    subreddit TEXT,
    reddit_score INTEGER,
    num_comments INTEGER,
    status TEXT,

    -- Trust layer fields
    trust_level TEXT,
    trust_score FLOAT,
    trust_badge TEXT,
    activity_score FLOAT,
    confidence_score FLOAT,
    engagement_level TEXT,
    trend_velocity FLOAT,
    problem_validity TEXT,
    discussion_quality TEXT,
    ai_confidence_level TEXT,
    trust_validation_timestamp TIMESTAMP,
    trust_validation_method TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Scenario 4: Batch script can't read trust indicators
**Symptom**: `batch_opportunity_scoring.py` runs but doesn't see trust indicators

**Root Cause**: Column name mismatch or query error

**Diagnosis**:
```python
# Quick Python check
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Check what columns exist
result = supabase.table('app_opportunities_trust').select('*').limit(1).execute()
print("Columns:", list(result.data[0].keys()) if result.data else "No data")

# Check for trust columns specifically
result = supabase.table('app_opportunities_trust')\
    .select('submission_id, trust_score, trust_badge, activity_score')\
    .limit(5)\
    .execute()
print(f"Found {len(result.data)} rows with trust data")
```

**Fix** (if column names are wrong):
Edit `/home/carlos/projects/redditharbor/scripts/core/batch_opportunity_scoring.py`, line 192-195:

Update the column names in the SELECT query to match actual table schema.

## Verification Commands

### Check table exists and has data
```bash
curl "http://127.0.0.1:54321/rest/v1/app_opportunities_trust?select=*&limit=0" \
  -H "apikey: $SUPABASE_KEY" \
  -H "Prefer: count=exact" -I | grep "Content-Range"
```

### Check trust indicators are populated
```bash
curl "http://127.0.0.1:54321/rest/v1/app_opportunities_trust?select=trust_score,trust_badge,activity_score&limit=5" \
  -H "apikey: $SUPABASE_KEY"
```

### Check for NULL trust values
```bash
curl "http://127.0.0.1:54321/rest/v1/app_opportunities_trust?select=submission_id,trust_score,trust_badge&trust_score=is.null&limit=10" \
  -H "apikey: $SUPABASE_KEY"
```

## Decision Tree

```
Is Supabase running?
├─ NO  → Run: supabase start
└─ YES → Does app_opportunities_trust table exist?
         ├─ NO  → Run: python3 scripts/dlt/dlt_trust_pipeline.py
         └─ YES → Does table have data?
                  ├─ NO  → Run: python3 scripts/dlt/dlt_trust_pipeline.py
                  └─ YES → Are trust indicators populated?
                           ├─ NO  → SCENARIO 1 (trust validation failing)
                           └─ YES → Check if data is in wrong schema
                                    ├─ Data in public_staging → SCENARIO 2
                                    └─ Data in public → ✅ ALL GOOD
```

## Expected Behavior

When everything is working correctly:

1. **DLT Trust Pipeline** runs successfully:
   ```
   ✓ Collection completed
   ✓ AI Analysis completed
   ✓ Trust Validation completed
   ✓ DLT Load completed
   ```

2. **Trust indicators** are populated:
   ```sql
   SELECT COUNT(*) FROM app_opportunities_trust WHERE trust_score IS NOT NULL;
   -- Should return > 0
   ```

3. **Batch scoring** reads trust data:
   ```
   Fetching all opportunities from app_opportunities_trust...
   Successfully fetched N opportunities
   ```

## Files Involved

| File | Purpose | Key Lines |
|------|---------|-----------|
| `scripts/dlt/dlt_trust_pipeline.py` | Write trust indicators | Line 535 (dataset_name), Line 496-509 (trust fields) |
| `scripts/core/batch_opportunity_scoring.py` | Read trust indicators | Line 192-195 (query), Line 237-240 (fetch) |
| `core/trust_layer.py` | Generate trust indicators | Trust validation logic |
| `.dlt/config.toml` | DLT configuration | Line 26 (dataset_name) |

## Contact for Help

If none of these solutions work:

1. Check full investigation report: `/home/carlos/projects/redditharbor/docs/architecture/TRUST_SCHEMA_INVESTIGATION_REPORT_2025-11-13.md`
2. Run diagnostic script: `python3 scripts/check_db_direct.py`
3. Check DLT logs: Query `_dlt.loads` table
4. Enable debug logging in DLT trust pipeline (add `--debug` flag if available)

## Summary of Code Analysis Findings

**✅ CORRECT Configuration**:
- DLT pipeline writes to `public` schema
- DLT pipeline writes to `app_opportunities_trust` table
- Batch scoring reads from `app_opportunities_trust` table
- Trust indicator fields are correctly mapped

**❓ NEEDS VERIFICATION** (when database is online):
- Are trust indicators actually populated?
- Is there duplicate data in staging schema?
- Is trust validation step succeeding?

**⚡ QUICK WIN**: If trust indicators are NULL, just re-run the trust pipeline:
```bash
python3 scripts/dlt/dlt_trust_pipeline.py --subreddits SideProject --limit 10
```
