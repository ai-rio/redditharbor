# Trust Schema Investigation Report
**Date**: 2025-11-13
**Issue**: Trust indicators potentially being written to wrong schema
**Status**: CODE ANALYSIS COMPLETE (Database offline)

## Executive Summary

Based on code analysis of the DLT pipeline and batch scoring scripts, the **architecture is correctly configured** to write trust indicators to the `public` schema in the `app_opportunities_trust` table. However, the database was offline during investigation, preventing runtime verification.

## Investigation Findings

### 1. Schema Configuration Analysis

#### DLT Trust Pipeline (`scripts/dlt/dlt_trust_pipeline.py`)

**Line 532-536**: DLT pipeline configuration
```python
trust_pipeline = dlt.pipeline(
    pipeline_name="reddit_harbor_trust_opportunities",
    destination=dlt.destinations.postgres("postgresql://postgres:postgres@127.0.0.1:54322/postgres"),
    dataset_name="public"  # ✓ CORRECT: Writing to public schema
)
```

**Finding**: The DLT trust pipeline is explicitly configured to write to the `public` schema (not `public_staging` or any other schema).

#### Table Name Configuration

**Line 540**: Table name specification
```python
info = trust_pipeline.run(
    app_opportunities_trust_resource(dlt_profiles),
    table_name="app_opportunities_trust"  # ✓ CORRECT: Target table name
)
```

**Finding**: Trust data is being written to `public.app_opportunities_trust`.

### 2. Batch Scoring Script Analysis

#### Data Source (`scripts/core/batch_opportunity_scoring.py`)

**Line 192-195**: Fetching opportunities with trust indicators
```python
query = supabase_client.table("app_opportunities_trust").select(
    "submission_id, title, problem_description, subreddit, reddit_score, "
    "num_comments, trust_score, trust_badge, activity_score"
).range(offset, offset + batch_size - 1)
```

**Finding**: The batch scoring script is correctly reading from `app_opportunities_trust`, including trust indicator fields:
- `trust_score`
- `trust_badge`
- `activity_score`

### 3. Trust Indicator Fields Mapping

#### Fields Written by DLT Trust Pipeline (Line 496-509)

```python
# Trust Layer fields (comprehensive)
'trust_level': post.get('trust_level', 'UNKNOWN'),
'trust_score': post.get('trust_score', 0),
'trust_badge': post.get('trust_badge', 'NO-BADGE'),
'activity_score': post.get('activity_score', 0),
'confidence_score': post.get('confidence_score', 0),
'engagement_level': post.get('engagement_level', 'UNKNOWN'),
'trend_velocity': post.get('trend_velocity', 0),
'problem_validity': post.get('problem_validity', 'UNKNOWN'),
'discussion_quality': post.get('discussion_quality', 'UNKNOWN'),
'ai_confidence_level': post.get('ai_confidence_level', 'LOW'),
'trust_validation_timestamp': post.get('trust_validation_timestamp'),
'trust_validation_method': post.get('trust_validation_method', 'comprehensive_trust_layer')
```

**Finding**: The DLT pipeline writes comprehensive trust indicators to `app_opportunities_trust`.

#### Fields Read by Batch Scoring Script (Line 192-195, 237-240)

```python
"submission_id, title, problem_description, subreddit, reddit_score, "
"num_comments, trust_score, trust_badge, activity_score"
```

**Finding**: The batch scoring script reads the key trust indicators.

### 4. Schema Inventory (From Code Analysis)

Based on DLT configuration files and pipeline code:

#### Schemas in Use

1. **`public`** (Line 535 in dlt_trust_pipeline.py)
   - Primary schema for application tables
   - Target for DLT trust pipeline
   - Contains: `app_opportunities_trust`

2. **`_dlt`** (Line 165 in .dlt/config.toml)
   - DLT metadata schema
   - Contains: `_dlt_loads`, `_dlt_version`, `_dlt_pipeline_state`

3. **`reddit_harbor`** (Line 61 in core/dlt_collection.py)
   - Dataset for Reddit collection pipeline
   - Separate from trust pipeline

#### No Evidence of `public_staging` Schema

**Finding**: No configuration or code references a `public_staging` schema in the trust pipeline flow.

### 5. Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ DLT Trust Pipeline (dlt_trust_pipeline.py)                     │
│                                                                 │
│ 1. Collect Posts → 2. AI Analysis → 3. Trust Validation        │
│         ↓                                                       │
│ 4. Load to Supabase (DLT)                                      │
│    - dataset_name: "public"                                     │
│    - table_name: "app_opportunities_trust"                      │
│    - write_disposition: "merge"                                 │
│    - primary_key: "submission_id"                               │
└─────────────────────────────────────────────────────────────────┘
                         ↓
         ┌───────────────────────────────┐
         │ public.app_opportunities_trust │
         │                                │
         │ Fields:                        │
         │ - submission_id (PK)           │
         │ - trust_score                  │
         │ - trust_badge                  │
         │ - activity_score               │
         │ - trust_level                  │
         │ - engagement_level             │
         │ - ... (12 trust fields)        │
         └───────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Batch Opportunity Scoring (batch_opportunity_scoring.py)       │
│                                                                 │
│ 1. Fetch from app_opportunities_trust (includes trust data)    │
│ 2. AI Enrichment (LLM profiler)                                │
│ 3. Store to workflow_results (DLT)                             │
└─────────────────────────────────────────────────────────────────┘
```

### 6. Potential Issues (Hypothetical)

Since the database was offline, we cannot verify runtime behavior. However, based on code analysis, potential issues could include:

#### Issue A: Trust Validation Not Running
**Symptom**: Trust fields are NULL in `app_opportunities_trust`
**Cause**: Trust validation step (Line 683-686 in dlt_trust_pipeline.py) failing silently
**Evidence Needed**: Check if `apply_trust_validation()` is executing successfully

#### Issue B: Schema Migration
**Symptom**: Old data in different schema, new data in `public`
**Cause**: Previous pipeline version used different schema
**Evidence Needed**: Check for tables like `public_staging.app_opportunities_trust`

#### Issue C: DLT Write Failure
**Symptom**: Pipeline completes but no data in table
**Cause**: DLT load failing silently (Line 538-542)
**Evidence Needed**: Check DLT logs in `_dlt_loads` table

## Database Verification Checklist

When database is online, run these queries:

### 1. Check Schema Inventory
```sql
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
ORDER BY schema_name;
```

### 2. Find All app_opportunities Tables
```sql
SELECT table_schema, table_name,
       (SELECT COUNT(*) FROM information_schema.columns
        WHERE table_schema = t.table_schema
        AND table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_name LIKE '%app_opportunities%'
ORDER BY table_schema, table_name;
```

### 3. Check Trust Indicator Data Quality
```sql
SELECT
    COUNT(*) as total_rows,
    COUNT(trust_score) as has_trust_score,
    COUNT(trust_badge) as has_trust_badge,
    COUNT(activity_score) as has_activity_score,
    COUNT(trust_level) as has_trust_level,
    ROUND(COUNT(trust_score)::numeric / COUNT(*)::numeric * 100, 2) as trust_coverage_pct
FROM public.app_opportunities_trust;
```

### 4. Sample Trust Data
```sql
SELECT
    submission_id,
    title,
    trust_score,
    trust_badge,
    activity_score,
    trust_level,
    trust_validation_timestamp
FROM public.app_opportunities_trust
ORDER BY trust_validation_timestamp DESC NULLS LAST
LIMIT 10;
```

### 5. Check DLT Load History
```sql
SELECT
    load_id,
    schema_name,
    status,
    inserted_at
FROM _dlt.loads
WHERE schema_name LIKE '%app_opportunities_trust%'
ORDER BY inserted_at DESC
LIMIT 10;
```

## Recommendations

### Option A: Code is Correct (Most Likely)
**If**: Database verification shows trust indicators ARE populated in `public.app_opportunities_trust`
**Action**: No changes needed
**Rationale**: Code analysis shows correct schema configuration

### Option B: Trust Validation Failing
**If**: Table exists but trust fields are NULL
**Action**:
1. Add error logging to `apply_trust_validation()` (Line 301-400 in dlt_trust_pipeline.py)
2. Add validation checks before DLT load (Line 453-557)
3. Implement retry logic for failed trust validations

**Code Change Example**:
```python
# In apply_trust_validation() function
try:
    trust_indicators = trust_validator.validate_opportunity_trust(...)
    validated_post.update({...})
except Exception as e:
    logger.error(f"Trust validation failed for {post.get('submission_id')}: {e}")
    # Use default trust values
    validated_post.update({
        'trust_level': 'UNKNOWN',
        'trust_score': 0,
        'trust_badge': 'NO-BADGE',
        ...
    })
```

### Option C: Schema Migration Needed
**If**: Old data exists in `public_staging.app_opportunities_trust`
**Action**: Migrate data from staging to public
**SQL Migration**:
```sql
INSERT INTO public.app_opportunities_trust
SELECT * FROM public_staging.app_opportunities_trust
ON CONFLICT (submission_id) DO UPDATE SET
    trust_score = EXCLUDED.trust_score,
    trust_badge = EXCLUDED.trust_badge,
    activity_score = EXCLUDED.activity_score,
    trust_level = EXCLUDED.trust_level,
    updated_at = NOW();
```

### Option D: DLT Configuration Issue
**If**: DLT is writing to wrong schema despite configuration
**Action**:
1. Check DLT runtime environment variables
2. Verify DLT credentials in `.dlt/secrets.toml`
3. Add explicit schema to table name: `public.app_opportunities_trust`

**Code Change**:
```python
# Line 540 in dlt_trust_pipeline.py
info = trust_pipeline.run(
    app_opportunities_trust_resource(dlt_profiles),
    table_name="public.app_opportunities_trust"  # Explicit schema
)
```

## Testing Plan

Once database is online:

### Test 1: End-to-End Pipeline Test
```bash
# Run trust pipeline with small dataset
python3 scripts/dlt/dlt_trust_pipeline.py --limit 5 --test-mode

# Verify data landed in public.app_opportunities_trust
# Check that trust indicators are populated
```

### Test 2: Batch Scoring Test
```bash
# Run batch scoring on trust-validated opportunities
python3 scripts/core/batch_opportunity_scoring.py

# Verify it reads trust indicators correctly
# Check workflow_results has enriched data
```

### Test 3: Trust Indicator Validation
```python
# Query sample and verify trust indicators
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
result = supabase.table('app_opportunities_trust')\
    .select('submission_id, trust_score, trust_badge, activity_score')\
    .not_.is_('trust_score', 'null')\
    .limit(10)\
    .execute()

print(f"Found {len(result.data)} opportunities with trust scores")
for opp in result.data:
    print(f"  {opp['submission_id']}: score={opp['trust_score']}, badge={opp['trust_badge']}")
```

## Conclusion

**Code Analysis Result**: The DLT pipeline and batch scoring script are correctly configured to use the `public.app_opportunities_trust` table. There is no evidence of a `public_staging` schema in the trust pipeline flow.

**Next Steps**:
1. **Start Supabase database** to verify runtime behavior
2. **Run database verification queries** from checklist above
3. **Execute test plan** to confirm end-to-end flow
4. **Implement recommendations** based on test results

**Confidence Level**: HIGH that code is correctly configured
**Risk Level**: LOW - worst case is missing trust indicators (not data loss)
**Priority**: MEDIUM - affects data quality but not system stability

---

**Investigation Tools Created**:
- `/home/carlos/projects/redditharbor/scripts/investigate_schemas.py` (requires supabase package)
- `/home/carlos/projects/redditharbor/scripts/investigate_trust_schema.py` (requires supabase package)
- `/home/carlos/projects/redditharbor/scripts/check_db_direct.py` (HTTP API, no dependencies)

**Usage** (when database is online):
```bash
# HTTP API approach (no dependencies)
python3 scripts/check_db_direct.py

# Or query directly with curl
curl "http://127.0.0.1:54321/rest/v1/app_opportunities_trust?select=trust_score,trust_badge&limit=5" \
  -H "apikey: $SUPABASE_KEY"
```
