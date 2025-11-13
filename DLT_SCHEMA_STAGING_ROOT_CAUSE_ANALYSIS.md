# DLT Schema Staging Root Cause Analysis

## Problem Summary

**Issue**: Trust scores calculated by `dlt_trust_pipeline.py` are being written to `public_staging.app_opportunities_trust` instead of `public.app_opportunities_trust`, causing the batch enrichment script to see NULL values for trust indicators.

**Impact**:
- Trust scores (63.6, 88.8, etc.) are calculated correctly but not accessible
- Batch enrichment script (`batch_opportunity_scoring.py`) expects data in `public` schema
- Trust preservation logic (lines 505-545) cannot read trust indicators
- Two-phase AI enrichment pipeline is broken

## Root Cause

DLT (Data Load Tool) uses a **staging schema pattern** by default for Postgres destinations. When you configure:

```python
pipeline = dlt.pipeline(
    pipeline_name="reddit_harbor_trust_opportunities",
    destination=dlt.destinations.postgres("postgresql://postgres:postgres@127.0.0.1:54322/postgres"),
    dataset_name="public"
)
```

DLT automatically creates a **staging schema** with the naming pattern: `{dataset_name}_staging`

**Key Configuration Parameter**:
```python
PostgresClientConfiguration(
    ...
    staging_dataset_name_layout: str = '%s_staging',  # DEFAULT VALUE
    ...
)
```

This means:
- `dataset_name="public"` → creates schema `public_staging`
- Tables are written to `public_staging.app_opportunities_trust`
- Your application queries `public.app_opportunities_trust` → NULL values

## Evidence from DLT Pipeline State

From `/home/carlos/.dlt/pipelines/reddit_harbor_trust_opportunities/state.json`:

```json
{
    "pipeline_name": "reddit_harbor_trust_opportunities",
    "default_schema_name": "reddit_harbor_trust_opportunities",
    "schema_names": ["reddit_harbor_trust_opportunities"],
    "dataset_name": "public",  // <- Requested schema
    "destination_type": "dlt.destinations.postgres"
}
```

From DLT schema file, the table is correctly defined but will be created in staging:
```json
{
  "name": "reddit_harbor_trust_opportunities",
  "tables": {
    "app_opportunities_trust": {
      "columns": {
        "trust_score": {"data_type": "double", "nullable": true},
        "trust_badge": {"data_type": "text", "nullable": true},
        // ... other trust fields
      },
      "write_disposition": "merge",
      "primary_key": "submission_id"
    }
  }
}
```

## Why DLT Uses Staging Schemas

DLT's staging pattern is designed for:

1. **Atomic Loads**: Stage data first, then move to production
2. **Data Validation**: Validate data in staging before promoting
3. **Rollback Safety**: Keep production schema stable during loads
4. **Schema Evolution**: Test schema changes in staging first

## Solutions

### Solution 1: Disable Staging Pattern (RECOMMENDED)

Modify `scripts/dlt/dlt_trust_pipeline.py` line 532-536:

**Current Code**:
```python
trust_pipeline = dlt.pipeline(
    pipeline_name="reddit_harbor_trust_opportunities",
    destination=dlt.destinations.postgres("postgresql://postgres:postgres@127.0.0.1:54322/postgres"),
    dataset_name="public"
)
```

**Fixed Code**:
```python
# Configure Postgres destination without staging pattern
from dlt.destinations import postgres

postgres_config = {
    "credentials": "postgresql://postgres:postgres@127.0.0.1:54322/postgres",
    "staging_dataset_name_layout": None,  # Disable staging schema
    # OR use: "staging_dataset_name_layout": "%s"  # No suffix
}

trust_pipeline = dlt.pipeline(
    pipeline_name="reddit_harbor_trust_opportunities",
    destination=postgres(**postgres_config),
    dataset_name="public"
)
```

### Solution 2: Use Schema-Qualified Table Names

Modify DLT resource to explicitly specify the schema:

```python
@dlt.resource(
    name="app_opportunities_trust",
    write_disposition="merge",
    primary_key="submission_id",
    table_name="public.app_opportunities_trust"  # Fully qualified name
)
def app_opportunities_trust_resource(profiles_data):
    # ... existing code
```

**Note**: This may not work as DLT typically handles schema-table separation.

### Solution 3: Update Batch Script to Query Staging Schema

Modify `scripts/core/batch_opportunity_scoring.py` line 505:

**Current**:
```python
existing = supabase.table("app_opportunities_trust").select(...).execute()
```

**Fixed**:
```python
# Query staging schema instead
existing = supabase.schema("public_staging").table("app_opportunities_trust").select(...).execute()
```

**Downside**: Not a clean solution; staging should be temporary.

### Solution 4: Create Migration After DLT Load

Add post-load hook to copy data from staging to public:

```python
def migrate_staging_to_public(pipeline):
    """Migrate data from staging to public schema after DLT load"""
    import psycopg2
    conn = psycopg2.connect("postgresql://postgres:postgres@127.0.0.1:54322/postgres")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO public.app_opportunities_trust
        SELECT * FROM public_staging.app_opportunities_trust
        ON CONFLICT (submission_id) DO UPDATE SET
            trust_score = EXCLUDED.trust_score,
            trust_badge = EXCLUDED.trust_badge,
            activity_score = EXCLUDED.activity_score,
            -- ... all trust fields
    """)

    conn.commit()
    conn.close()

# After pipeline.run()
migrate_staging_to_public(trust_pipeline)
```

## Recommended Fix

**Solution 1** is the cleanest approach. Here's the complete fix:

### File: `/home/carlos/projects/redditharbor/scripts/dlt/dlt_trust_pipeline.py`

**Changes Required**:

1. **Import the postgres destination properly** (line ~35):
```python
from dlt.destinations import postgres
```

2. **Update the pipeline creation function** (lines 532-536):

```python
# OLD CODE (REMOVE):
trust_pipeline = dlt.pipeline(
    pipeline_name="reddit_harbor_trust_opportunities",
    destination=dlt.destinations.postgres("postgresql://postgres:postgres@127.0.0.1:54322/postgres"),
    dataset_name="public"
)

# NEW CODE (ADD):
# Configure Postgres destination to write directly to public schema (no staging)
postgres_destination = postgres(
    credentials="postgresql://postgres:postgres@127.0.0.1:54322/postgres",
    staging_dataset_name_layout=None  # Disable staging schema pattern
)

trust_pipeline = dlt.pipeline(
    pipeline_name="reddit_harbor_trust_opportunities",
    destination=postgres_destination,
    dataset_name="public"
)
```

### Same Fix for `batch_opportunity_scoring.py`

Apply the same fix to `/home/carlos/projects/redditharbor/scripts/core/batch_opportunity_scoring.py` around line 562 where it creates the DLT pipeline.

## Cache Cleanup Commands

After making changes, clear DLT cache:

```bash
# Remove pipeline cache to force schema recreation
rm -rf ~/.dlt/pipelines/reddit_harbor_trust_opportunities/

# OR clear all DLT caches
rm -rf ~/.dlt/pipelines/
```

## Verification Steps

After applying the fix:

1. **Run the trust pipeline**:
```bash
cd /home/carlos/projects/redditharbor
python scripts/dlt/dlt_trust_pipeline.py --limit 5
```

2. **Verify table creation**:
```sql
-- Check schemas
SELECT schema_name FROM information_schema.schemata
WHERE schema_name IN ('public', 'public_staging');

-- Verify data in public schema
SELECT submission_id, trust_score, trust_badge
FROM public.app_opportunities_trust
LIMIT 5;

-- Ensure no staging schema was created
SELECT tablename FROM pg_tables
WHERE schemaname = 'public_staging';
```

3. **Run batch enrichment**:
```bash
python scripts/core/batch_opportunity_scoring.py --limit 5
```

4. **Verify trust preservation**:
```sql
-- Check that trust scores are preserved after batch enrichment
SELECT submission_id, trust_score, trust_badge,
       app_concept, problem_description
FROM public.app_opportunities_trust
WHERE trust_score IS NOT NULL
LIMIT 10;
```

## DLT Best Practices

For RedditHarbor's use case:

1. **Disable staging for direct writes**: Your pipeline writes directly to production
2. **Use merge disposition**: Already implemented correctly with `write_disposition="merge"`
3. **Set primary keys**: Already using `primary_key="submission_id"`
4. **Schema version control**: Consider adding schema version tracking

## Additional Considerations

### If You Want to Keep Staging Pattern

If staging is desired for data quality validation:

1. Keep staging enabled
2. Add post-load validation step
3. Promote data from staging to public only after validation
4. Use DLT's `replace_strategy='staging-optimized'`

Example:
```python
postgres_destination = postgres(
    credentials="postgresql://postgres:postgres@127.0.0.1:54322/postgres",
    replace_strategy="staging-optimized",  # Use staging efficiently
    staging_dataset_name_layout="%s_staging"
)
```

Then add promotion logic:
```python
# After successful validation
promote_staging_to_production()
```

## Summary

**Root Cause**: DLT's default `staging_dataset_name_layout='%s_staging'` creates a staging schema

**Fix**: Set `staging_dataset_name_layout=None` in postgres destination configuration

**Files to Update**:
1. `/home/carlos/projects/redditharbor/scripts/dlt/dlt_trust_pipeline.py` (line 532-536)
2. `/home/carlos/projects/redditharbor/scripts/core/batch_opportunity_scoring.py` (line ~562)

**Cache Cleanup**: `rm -rf ~/.dlt/pipelines/reddit_harbor_trust_opportunities/`

**Verification**: Query `public.app_opportunities_trust` and verify trust scores are visible
