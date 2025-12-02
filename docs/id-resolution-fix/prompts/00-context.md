# ID Resolution Fix - Problem Context

**Date**: 2025-11-23
**Status**: Critical - Blocking Test 02 Small Batch
**Priority**: P0

---

## The Problem

Pipeline reports success but database verification fails with 0% field coverage. Data appears to be stored but cannot be found.

## Root Cause

Three incompatible ID systems coexist without enforcement:

| Location | Field | Format | Example |
|----------|-------|--------|---------|
| `submissions.id` | Primary Key | UUID | `e7763e41-d7bf-4bf1-a004-decff9f0f0c5` |
| `submissions.submission_id` | Legacy field | UUID (copy of id) | `e7763e41-d7bf-4bf1-a004-decff9f0f0c5` |
| `submissions.reddit_id` | Reddit API ID | String | `hybrid_1`, `1fp7k8t` |
| `app_opportunities.submission_id` | DLT-managed | Raw string | `hybrid_1` |

## Evidence

### Database State (verified 2025-11-23)

```sql
-- submissions table shows:
id                                   | submission_id                        | reddit_id
e7763e41-d7bf-4bf1-a004-decff9f0f0c5 | e7763e41-d7bf-4bf1-a004-decff9f0f0c5 | hybrid_1

-- app_opportunities table shows:
submission_id | app_name  | opportunity_score
hybrid_1      | TimeSync  | NULL
hybrid_2      | StudySync | NULL
```

### FK Constraints (verified 2025-11-23)

```sql
-- Only these FK constraints exist:
opportunities         | submission_id | submissions | id
opportunities_unified | submission_id | submissions | id

-- app_opportunities has NO FK constraint to submissions
```

### The Disconnect

1. Pipeline stores `hybrid_1` in `app_opportunities.submission_id`
2. Verifier queries `submissions WHERE submission_id = 'hybrid_1'`
3. No match because `submissions.submission_id` contains UUID, not `hybrid_1`
4. `hybrid_1` is in `submissions.reddit_id`, not `submission_id`

## Files Involved

### Storage Layer
- `core/storage/enhanced_hybrid_store.py` - Main storage, has `_fix_submission_id_formats()` that doesn't work correctly
- `core/storage/hybrid_store.py` - Parent class
- `core/storage/dlt_loader.py` - DLT pipeline that creates its own schema

### Verification Layer
- `scripts/testing/integration/utils/database_verifier.py` - SQLAlchemy verifier that queries wrong fields

### Schema
- `supabase/migrations/` - Multiple migrations with inconsistent ID handling

## Success Criteria

After fix:
1. `app_opportunities.submission_id` contains UUID that matches `submissions.id`
2. Database verifier finds records using the correct ID
3. Test 02 passes with >90% field coverage
4. FK constraint enforced between `app_opportunities` and `submissions`

## Constraints

- Must not break existing data
- Must not require full database migration
- Must be backwards compatible with DLT pipeline
- Changes must be testable incrementally

---

## Workflow

This fix is broken into 6 steps. Each step has:
- A prompt for the AI agent
- A report template to fill
- Validation criteria before proceeding

**Steps:**
1. **Audit** - Map all ID usage in codebase
2. **Design** - Design canonical resolver (no code)
3. **Implement** - Create the resolver module
4. **Integrate** - Wire resolver into storage/verifier
5. **Enforce** - Add DB triggers
6. **Validate** - Run tests, confirm fix

Proceed to `01-audit.md` to begin.
