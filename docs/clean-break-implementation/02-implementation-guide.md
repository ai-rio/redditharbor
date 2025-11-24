# Implementation Guide: Clean Break ID Normalization

**Document Version**: 1.0
**Last Updated**: 2025-11-24
**Status**: Template (Implementation Details to be Filled)

---

## Overview

This guide provides step-by-step instructions for implementing the Clean Break approach to ID normalization in RedditHarbor. The goal is to ensure all submission IDs are normalized to UUID format **before** entering the DLT pipeline.

---

## Prerequisites

### Technical Requirements

- [ ] Python 3.11+
- [ ] Access to development PostgreSQL/Supabase instance
- [ ] DLT library installed (`pip install dlt`)
- [ ] Project dependencies installed (`uv sync`)

### Knowledge Requirements

- [ ] Understanding of [00-problem-statement.md](./00-problem-statement.md)
- [ ] Familiarity with DLT pipeline concepts
- [ ] Basic understanding of UUID v5 generation

### Repository State

Before starting, ensure:

```bash
# Clean working directory
git status
# Should be on feature branch, not main

# Tests passing
pytest tests/test_id_resolver.py -v
# All tests should pass

# Database accessible
python -c "from config.settings import DATABASE_URL; print('DB configured')"
```

---

## Step-by-Step Implementation

### Phase 1: Understand the ID Resolver

The ID resolver is already implemented at `core/utils/id_resolver.py`.

**Key Components**:

```python
# Namespace for deterministic UUID generation
REDDITHARBOR_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "redditharbor-pipeline")

# Main entry point
def resolve_submission_id(
    input_value: str | dict[str, Any] | None,
    *,
    require_db_existence: bool = False,
    fallback_to_generated: bool = True,
    supabase_client: Any = None,
) -> ResolutionResult | None:
    """Resolve various ID formats to canonical UUID."""
```

**Supported Input Formats**:

| Input Format | Example | Behavior |
|--------------|---------|----------|
| UUID | `550e8400-e29b-...` | Passthrough (normalized to lowercase) |
| Reddit ID | `abc123` | Generate UUID v5 |
| Reddit URL | `reddit.com/r/.../comments/abc123` | Extract ID, generate UUID v5 |
| Dictionary | `{"submission_id": "abc123"}` | Extract from key, generate UUID v5 |
| None/Empty | `None`, `""` | Return None |

**Output Structure**:

```python
@dataclass
class ResolutionResult:
    uuid: str | None          # The resolved UUID
    source: str | None        # "passthrough", "generated", or "database"
    original_input: str       # What was passed in
    error: str | None         # Error message if failed
    metadata: dict            # Additional context
```

---

### Phase 2: Integration Points

Identify all locations where submission IDs enter the system:

```
[TODO: Complete audit of code paths]

1. core/dlt/collection.py
   - transform_submission_to_schema()
   - collect_problem_posts()
   Status: [ ] Audited [ ] Modified [ ] Tested

2. core/fetchers/reddit_api_fetcher.py
   - fetch_submission()
   - fetch_submissions_batch()
   Status: [ ] Audited [ ] Modified [ ] Tested

3. core/enrichment/opportunity_service.py
   - enrich_opportunity()
   - create_opportunity_from_submission()
   Status: [ ] Audited [ ] Modified [ ] Tested

4. [Additional paths to be identified]
   Status: [ ] Audited [ ] Modified [ ] Tested
```

---

### Phase 3: Modify DLT Transform Functions

**Location**: `core/dlt/collection.py`

**Current Implementation** (lines ~113-151):

```python
def transform_submission_to_schema(submission_data: dict[str, Any]) -> dict[str, Any]:
    """Transform Reddit API submission data to match Supabase schema."""
    from datetime import datetime

    selftext = submission_data.get("selftext", "")
    # ... existing transformation logic ...

    transformed = {
        "submission_id": submission_data.get("id"),  # <-- Currently raw ID
        # ... other fields ...
    }
    return {k: v for k, v in transformed.items() if v is not None}
```

**Required Change**:

```python
def transform_submission_to_schema(submission_data: dict[str, Any]) -> dict[str, Any]:
    """Transform Reddit API submission data to match Supabase schema."""
    from datetime import datetime
    from core.utils.id_resolver import resolve_submission_id

    selftext = submission_data.get("selftext", "")
    # ... existing transformation logic ...

    # Normalize submission_id to UUID format
    raw_id = submission_data.get("id")
    resolution = resolve_submission_id(raw_id)
    normalized_id = resolution.uuid if resolution else None

    transformed = {
        "submission_id": normalized_id,  # <-- Now normalized UUID
        "reddit_id": raw_id,             # <-- Preserve original for reference
        # ... other fields ...
    }
    return {k: v for k, v in transformed.items() if v is not None}
```

**Verification**:

```python
# Test the transformation
from core.dlt.collection import transform_submission_to_schema

test_data = {"id": "abc123", "title": "Test", "selftext": "Content"}
result = transform_submission_to_schema(test_data)

assert result["submission_id"] is not None
assert "-" in result["submission_id"]  # UUID format
assert result["reddit_id"] == "abc123"  # Original preserved
```

---

### Phase 4: Update Query Functions

All functions that query by submission_id must normalize the query parameter:

**Pattern**:

```python
# Before
def get_opportunity(submission_id: str):
    return db.query("SELECT * FROM app_opportunities WHERE submission_id = %s",
                    [submission_id])

# After
def get_opportunity(submission_id: str):
    from core.utils.id_resolver import resolve_submission_id

    resolution = resolve_submission_id(submission_id)
    if not resolution or not resolution.uuid:
        return None

    return db.query("SELECT * FROM app_opportunities WHERE submission_id = %s",
                    [resolution.uuid])
```

**Locations to Update**:

```
[TODO: Complete list of query functions]

1. core/storage/opportunity_store.py
   - get_by_submission_id()
   - exists()
   Status: [ ] Modified [ ] Tested

2. core/fetchers/database_fetcher.py
   - fetch_submission()
   Status: [ ] Modified [ ] Tested

3. [Additional locations]
   Status: [ ] Modified [ ] Tested
```

---

### Phase 5: Database Safety Net (Optional)

Add a PostgreSQL trigger as a safety net for any IDs that bypass application normalization:

**Migration File**: `supabase/migrations/YYYYMMDDHHMMSS_add_id_normalization_trigger.sql`

```sql
-- Create normalization function
CREATE OR REPLACE FUNCTION normalize_submission_id(input_text TEXT)
RETURNS UUID
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    redditharbor_namespace UUID := uuid_generate_v5(
        uuid_ns_dns(),
        'redditharbor-pipeline'
    );
BEGIN
    -- If already a valid UUID, return as-is
    IF input_text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN
        RETURN input_text::UUID;
    END IF;

    -- Generate deterministic UUID from input
    RETURN uuid_generate_v5(redditharbor_namespace, input_text);
END;
$$;

-- Create trigger function
CREATE OR REPLACE FUNCTION normalize_submission_id_trigger()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.submission_id := normalize_submission_id(NEW.submission_id)::TEXT;
    RETURN NEW;
END;
$$;

-- Apply to relevant tables
CREATE TRIGGER normalize_submission_id_on_insert
    BEFORE INSERT ON app_opportunities
    FOR EACH ROW
    EXECUTE FUNCTION normalize_submission_id_trigger();

CREATE TRIGGER normalize_submission_id_on_update
    BEFORE UPDATE OF submission_id ON app_opportunities
    FOR EACH ROW
    WHEN (OLD.submission_id IS DISTINCT FROM NEW.submission_id)
    EXECUTE FUNCTION normalize_submission_id_trigger();
```

---

### Phase 6: Verification Steps

#### Unit Tests

```bash
# Run ID resolver tests
pytest tests/test_id_resolver.py -v

# Expected: All tests pass
```

#### Integration Tests

```bash
# Run DLT integration tests
pytest tests/test_dlt_integration.py -v -k "submission_id"

# Expected: All tests pass
```

#### Database Verification

```sql
-- Check for any non-UUID format IDs
SELECT COUNT(*) as non_uuid_count
FROM app_opportunities
WHERE submission_id !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';

-- Expected: 0
```

#### End-to-End Test

```python
# Test complete flow
from core.dlt.collection import collect_problem_posts, load_to_supabase
from core.storage.opportunity_store import get_by_submission_id

# 1. Collect with test mode
posts = collect_problem_posts(["test_subreddit"], limit=1, test_mode=True)
assert len(posts) > 0

# 2. Verify ID format
submission_id = posts[0]["submission_id"]
assert "-" in submission_id  # UUID format

# 3. Load to database
success = load_to_supabase(posts)
assert success

# 4. Query with original Reddit ID should find record
original_id = "test_0_0"  # From test data
result = get_by_submission_id(original_id)
assert result is not None  # Found via normalized query
```

---

## Rollback Procedure

If issues are discovered after deployment:

### Step 1: Revert Code Changes

```bash
git revert HEAD  # Revert the implementation commit
```

### Step 2: Remove Database Trigger (if installed)

```sql
DROP TRIGGER IF EXISTS normalize_submission_id_on_insert ON app_opportunities;
DROP TRIGGER IF EXISTS normalize_submission_id_on_update ON app_opportunities;
DROP FUNCTION IF EXISTS normalize_submission_id_trigger();
DROP FUNCTION IF EXISTS normalize_submission_id(TEXT);
```

### Step 3: Verify Rollback

```bash
pytest tests/test_dlt_integration.py -v
# Tests should pass (may have known failures from before fix)
```

---

## Troubleshooting

### Issue: Tests fail after implementation

**Symptom**: Tests that were passing now fail with ID mismatch errors

**Cause**: Test fixtures using old ID format

**Solution**: Update test fixtures to expect UUID format:

```python
# Before
expected_id = "abc123"

# After
from core.utils.id_resolver import resolve_submission_id
expected_id = resolve_submission_id("abc123").uuid
```

---

### Issue: Existing data not found after migration

**Symptom**: Records exist in database but queries return None

**Cause**: Existing data has old format, queries use new format

**Solution**: Run data migration to normalize existing IDs:

```sql
UPDATE app_opportunities
SET submission_id = normalize_submission_id(submission_id)::TEXT
WHERE submission_id !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
```

---

### Issue: Foreign key violations after normalization

**Symptom**: Updates fail with FK constraint errors

**Cause**: Related tables have old ID format

**Solution**: Normalize all related tables in order:

```sql
-- 1. Disable FK checks temporarily (careful!)
-- 2. Normalize parent table (submissions)
-- 3. Normalize child tables (comments, opportunities)
-- 4. Re-enable FK checks
```

---

### Issue: UUID mismatch between Python and PostgreSQL

**Symptom**: Python generates different UUID than PostgreSQL trigger

**Cause**: Namespace UUIDs not identical

**Solution**: Verify namespace matches:

```python
# Python
import uuid
NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "redditharbor-pipeline")
print(NAMESPACE)  # Should match PostgreSQL
```

```sql
-- PostgreSQL
SELECT uuid_generate_v5(uuid_ns_dns(), 'redditharbor-pipeline');
-- Should match Python output
```

---

## Checklist

### Pre-Implementation

- [ ] Read problem statement document
- [ ] Run existing tests (baseline)
- [ ] Create feature branch
- [ ] Back up development database

### Implementation

- [ ] Audit all ID entry points
- [ ] Modify transform functions
- [ ] Update query functions
- [ ] Add database trigger (optional)
- [ ] Update test fixtures

### Verification

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Database shows 0 non-UUID IDs
- [ ] E2E test successful

### Post-Implementation

- [ ] Document any deviations from guide
- [ ] Update this guide with learnings
- [ ] Create PR for review

---

## Related Documents

- [00-problem-statement.md](./00-problem-statement.md) - Why we need this
- [README.md](./README.md) - Overview and quick start
- [ID Resolver Source](../../core/utils/id_resolver.py) - Implementation reference

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-24 | - | Initial template |
