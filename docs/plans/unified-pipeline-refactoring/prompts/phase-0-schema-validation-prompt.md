# Local AI Agent Testing Instructions - Phase 0: Schema Validation

## Context

Phase 0 of the deduplication integration has been completed and pushed to branch `claude/review-pipeline-handover-018wChYNQXVLhN6HdDn3omBV`. Your task is to validate the database schema prerequisites locally before implementing deduplication logic.

## What Was Done

A remote AI agent created a schema validation script to verify that all required database tables and columns exist for deduplication integration:

- ✅ Created schema validation script: `scripts/testing/validate_deduplication_schema.py`
- ✅ Validates 4 critical tables: `opportunities_unified`, `business_concepts`, `llm_monetization_analysis`, `workflow_results`
- ✅ Checks 14 required columns across these tables
- ✅ Provides clear error messages if schema is incomplete
- ✅ **1 file created, ~140 lines of code**
- ✅ **Zero existing code modified (ZERO RISK)**

## Your Task

### Step 1: Pull the Changes

```bash
git fetch origin
git checkout claude/review-pipeline-handover-018wChYNQXVLhN6HdDn3omBV
git pull
```

### Step 2: Start Supabase (if not already running)

```bash
# Start local Supabase instance
supabase start

# Verify it's running
supabase status
```

**Expected Output:**
```
API URL: http://127.0.0.1:54321
DB URL: postgresql://postgres:postgres@127.0.0.1:54322/postgres
Studio URL: http://127.0.0.1:54323
```

### Step 3: Run Schema Validation

```bash
# Run the schema validation script
python scripts/testing/validate_deduplication_schema.py
```

**Expected Result (SUCCESS CASE):**
```
🔍 Validating deduplication schema...
   Database: http://127.0.0.1:54321

  ✅ opportunities_unified: 2 columns validated
  ✅ business_concepts: 3 columns validated
  ✅ llm_monetization_analysis: 6 columns validated
  ✅ workflow_results: 4 columns validated

================================================================================
VALIDATION SUMMARY
================================================================================
✅ Schema validation passed - deduplication can proceed

Tables validated:
  • opportunities_unified: 2 columns
  • business_concepts: 3 columns
  • llm_monetization_analysis: 6 columns
  • workflow_results: 4 columns

Next steps:
  1. Proceed with Phase 1: Integrate Deduplication Classes
  2. Run Phase 0 local AI test
```

**Expected Result (FAILURE CASE):**
```
🔍 Validating deduplication schema...
   Database: http://127.0.0.1:54321

  ✅ opportunities_unified: 2 columns validated
  ❌ business_concepts: FAILED - relation "business_concepts" does not exist
  ❌ llm_monetization_analysis: FAILED - column "copied_from_primary" does not exist

================================================================================
VALIDATION SUMMARY
================================================================================
❌ Schema validation FAILED

Missing/invalid tables:
  • business_concepts
    Required columns: id, has_agno_analysis, has_profiler_analysis
    Error: relation "business_concepts" does not exist
  • llm_monetization_analysis
    Required columns: business_concept_id, copied_from_primary, ...
    Error: column "copied_from_primary" does not exist

Action required:
  1. Run database migrations: supabase db push
  2. Check migrations/002_add_comprehensive_enrichment_fields.sql
  3. Re-run this validation script
```

### Step 4: Fix Schema Issues (if validation fails)

If schema validation fails, run the migrations:

```bash
# Apply all pending migrations
supabase db push

# Re-run validation
python scripts/testing/validate_deduplication_schema.py
```

### Step 5: Verify Required Columns

You can manually verify key tables exist:

```bash
# Check opportunities_unified
supabase db query "SELECT submission_id, business_concept_id FROM opportunities_unified LIMIT 1;"

# Check business_concepts
supabase db query "SELECT id, has_agno_analysis, has_profiler_analysis FROM business_concepts LIMIT 1;"

# Check llm_monetization_analysis
supabase db query "SELECT business_concept_id, copied_from_primary, willingness_to_pay_score FROM llm_monetization_analysis LIMIT 1;"

# Check workflow_results
supabase db query "SELECT opportunity_id, copied_from_primary, app_name, core_functions FROM workflow_results LIMIT 1;"
```

## What to Report Back

Please report:

1. ✅ **Pass/Fail**: Did schema validation pass?
2. 📊 **Tables Validated**: How many tables passed validation? (Should be 4/4)
3. 📊 **Columns Validated**: Total columns validated? (Should be ~15)
4. ⚠️ **Missing Schema**: Any tables or columns missing?
5. 🔧 **Fixes Applied**: Did you need to run migrations?
6. 📝 **Database Stats**: Any existing data in these tables?

## If Validation Fails

If schema validation fails, provide:

1. **Full error output** from the validation script
2. **Migration status**: Output from `supabase migration list`
3. **Table list**: Output from `supabase db query "\dt"`
4. **Supabase version**: Output from `supabase --version`

## Critical Tables for Deduplication

The deduplication integration depends on these tables:

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `opportunities_unified` | Links submissions to business concepts | `submission_id`, `business_concept_id` |
| `business_concepts` | Tracks which concepts have been analyzed | `has_agno_analysis`, `has_profiler_analysis` |
| `llm_monetization_analysis` | Stores Agno monetization analysis | `copied_from_primary`, `willingness_to_pay_score` |
| `workflow_results` | Stores Profiler app analysis | `copied_from_primary`, `app_name`, `core_functions` |

## Success Criteria

✅ All 4 tables exist
✅ All required columns exist in each table
✅ Validation script exits with code 0
✅ No errors or warnings in output

## Next Steps After Validation

Once you confirm schema validation passes:

**Phase 1: Integrate Deduplication Classes** (Ready to implement)
- Add deduplication check to orchestrator
- Implement copy logic with evidence chaining
- Add batch query optimization
- Timeline: 4-6 hours

---

**Phase 0 Status**: ✅ COMPLETE (awaiting local validation)
**Risk Level**: 🟢 ZERO (no code changes, only validation)
**Expected Cost Savings**: $3,528-$6,300/year (70% deduplication rate)
**Branch**: `claude/review-pipeline-handover-018wChYNQXVLhN6HdDn3omBV`
