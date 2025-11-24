# Pre-Test Validation Scripts

This directory contains validation scripts to ensure the database is ready for Phase 8 integration testing.

---

## Quick Validation: ID Format Check

**Purpose**: Verify all submission IDs are clean UUIDs (clean-break implementation working)

**Usage**:

```bash
# Option 1: Using Python script
source .venv/bin/activate
export SUPABASE_KEY="your-service-role-key"
python scripts/testing/validate_ids.py

# Option 2: Using bash (requires Docker)
bash /tmp/validate_id_formats.sh

# Option 3: Direct SQL query
docker exec supabase_db_redditharbor-core-functions-fix psql -U postgres -d postgres -c "
SELECT
    CASE
        WHEN id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        THEN 'UUID'
        ELSE 'RAW_ID'
    END as format_type,
    COUNT(*) as count
FROM submissions
GROUP BY format_type;
"
```

**Expected Output** (Success):
```
================================================================================
PRE-TEST VALIDATION: Clean-Break ID Format Check
================================================================================

🔗 Connecting to Supabase: http://127.0.0.1:54330
✅ Connected successfully

🔍 Validating submission ID formats...
   Total submissions: 150
   Clean UUIDs: 150
   Non-UUID formats: 0

✅ ID FORMAT VALIDATION PASSED

All submission IDs are clean UUIDs!
Database is ready for Phase 8 integration testing.

================================================================================
```

**Expected Output** (Failure):
```
❌ VALIDATION FAILED

Found submissions with non-UUID format:
   1. ID: abc123
      Title: Example post about...
   2. ID: t3_xyz789
      Title: Another example...

Fix: Ensure clean-break ID normalization is working
See: docs/clean-break-implementation/00-problem-statement.md
```

---

## What This Validates

### Clean-Break Implementation Status

The validation checks that the **Pre-DLT ID Normalization** is working:

```
Reddit API (raw ID "abc123")
       ↓
core/utils/id_resolver.py → resolve_submission_id()
       ↓
core/dlt/collection.py → transform_submission_to_schema()
       ↓
PostgreSQL submissions table (UUID format)
```

**If validation passes**: All submission IDs were normalized to UUIDs before storage

**If validation fails**: Some IDs bypassed normalization (clean-break not working)

---

## When to Run This

### Before Starting Phase 8 Tests

Run this validation **before Test 01** to ensure database foundation is clean:

```bash
# 1. Validate ID formats
python scripts/testing/validate_ids.py

# 2. If passed, proceed with testing
python scripts/testing/integration/tests/test_01_single_submission.py
```

### After Database Reset

Run this after `supabase db reset` to verify migrations applied correctly:

```bash
# Reset database
supabase db reset

# Validate clean state
python scripts/testing/validate_ids.py

# Should show: 0 submissions (clean slate)
```

### After Data Collection

Run this after collecting Reddit data to verify normalization:

```bash
# Collect data
python scripts/collection/collect_reddit_data.py

# Validate IDs normalized
python scripts/testing/validate_ids.py

# Should show: All UUIDs
```

---

## Comprehensive Validation (Advanced)

For full pre-test validation including table existence and field validation:

```bash
source .venv/bin/activate
export SUPABASE_URL="http://127.0.0.1:54330"
export SUPABASE_KEY="your-service-role-key"
python scripts/testing/integration/utils/validation.py
```

This runs:
1. ✅ ID format validation (clean-break check)
2. ✅ Required tables exist (submissions, app_opportunities, opportunities_unified)
3. ✅ Minimum data availability (at least 5 submissions with score >= 20)
4. ✅ Required fields present (id, title, selftext, score, num_comments)

**Note**: This validation may fail if app_opportunities table doesn't exist yet (created during tests).

---

## Troubleshooting

### "No submissions found in database"

**Meaning**: Database is empty (clean slate)

**Action**:
- If expecting data: Run data collection first
- If testing clean slate: This is normal after `supabase db reset`

### "Non-UUID formats found"

**Meaning**: Clean-break implementation not working correctly

**Actions**:
1. Check `core/utils/id_resolver.py` exists and working
2. Check `core/dlt/collection.py` uses `resolve_submission_id()`
3. Review clean-break tests: `pytest tests/test_dlt_id_normalization.py`
4. Check problem statement: `docs/clean-break-implementation/00-problem-statement.md`

### "Could not connect to Supabase"

**Meaning**: Supabase not running or wrong credentials

**Actions**:
1. Check Supabase running: `supabase status`
2. Verify SUPABASE_KEY: `echo $SUPABASE_KEY`
3. Start Supabase: `supabase start`

---

## Integration with Test Framework

Add this to the beginning of Test 01 prompt:

```bash
# Pre-Test Validation Step
echo "Step 0: Validating database state..."
python scripts/testing/validate_ids.py

if [ $? -ne 0 ]; then
    echo "❌ Pre-test validation failed. Fix issues before proceeding."
    exit 1
fi

echo "✅ Database validated. Proceeding with Test 01..."
```

---

## References

- **Clean-Break Problem Statement**: `docs/clean-break-implementation/00-problem-statement.md`
- **ID Resolver Implementation**: `core/utils/id_resolver.py`
- **DLT Collection Transforms**: `core/dlt/collection.py`
- **ID Normalization Tests**: `tests/test_dlt_id_normalization.py`
- **Phase 8 Test Framework**: `docs/plans/unified-pipeline-refactoring/testing/phase-8-full-pipeline-testing-framework.md`

---

**Created**: 2025-11-24
**Purpose**: Unblock Phase 8 testing by verifying clean-break implementation
**Status**: Production ready ✅
