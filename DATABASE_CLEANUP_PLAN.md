# Database Cleanup Plan

## Current Situation

The database is fragmented across multiple schemas and tables:

### Opportunity Data Distribution

| Table | Schema | Rows | Status |
|-------|--------|------|--------|
| `app_opportunities` | app_opportunities | 11 | Source of truth (mixed test/real) |
| `opportunities_unified` | public | 100 | Duplicate/aggregated |
| `opportunity_scores` | public | 100 | Derived data |
| `opportunities` | public | 0 | **Target - SQLModel table (EMPTY)** |
| `opportunities_legacy` | public | 3 | Legacy |
| `opportunity_analysis` | public | 0 | Empty |
| `app_opportunities` | app_opportunities_staging | 1 | Staging |
| `app_opportunities` | public_staging | 1 | Staging |
| Various helper tables | public/app_opportunities | Multiple | Support tables |

### Data Quality Analysis

- **Total in app_opportunities**: 11 opportunities
  - **Real data**: 2 (1p7drk6, 1p7hni7)
  - **Test data**: 9 (debug_, char_, test_, final_)

## Cleanup Strategy

### Phase 1: Backup & Validate
- [ ] Export all 11 opportunities from `app_opportunities.app_opportunities` to CSV
- [ ] Document the 2 real opportunities separately
- [ ] Validate data integrity

### Phase 2: Migration to SQLModel
The SQLModel `opportunities` table in `public` schema has this structure:
```
- id (int, auto-increment, PK)
- submission_id (varchar, unique)
- subreddit (varchar)
- title (varchar)
- wtp_score (float 0-100)
- final_score (float 0-100)
- confidence_score (float 0-100, default 75.0)
- analysis (JSON) - for storing app_concept, problem_description
- metrics (JSON) - for storing market metrics
- trust_level (varchar) - LOW/MEDIUM/HIGH
- created_at (timestamp)
- updated_at (timestamp)
```

Mapping from `app_opportunities`:
- submission_id → submission_id
- title → title
- subreddit → subreddit
- final_score → final_score (if available, else 0)
- trust_score → confidence_score (if available, else 75)
- trust_level → trust_level (if available, else 'MEDIUM')
- opportunity_score → wtp_score (if available, else willingness_to_pay_score)
- {app_concept, problem_description} → analysis (JSON)
- {opportunity_score, monetization_score, confidence_score} → metrics (JSON)

### Phase 3: Cleanup Duplicate/Legacy Tables
Delete in this order:
1. `public.app_opportunities__monetization_keywords`
2. `public.app_opportunities_backup_20251202`
3. `public.opportunities_legacy`
4. `public.opportunities_unified`
5. `public.opportunity_analysis`
6. `public.opportunity_scores`

### Phase 4: Drop Unused Schemas
- `app_opportunities` (and all tables within)
- `app_opportunities_staging` (and all tables within)
- `public_staging` (remove `app_opportunities` table)

### Phase 5: Code Updates
Update all pipeline code to:
- Import from `pipeline-v4/models/analysis.py` → `Opportunity` SQLModel
- Use `public.opportunities` table exclusively
- Remove all references to:
  - `app_opportunities` schema
  - DLT pipeline loaders for opportunities
  - Legacy ORM models

### Phase 6: Verification
- [ ] Confirm `public.opportunities` has all real data
- [ ] Run pytest on all affected modules
- [ ] Verify no broken imports
- [ ] Check Alembic migrations are clean

## Estimated Impact

- **Data Loss**: 9 test records (acceptable - they're test data)
- **Real Data Preserved**: 2 opportunities migrated to SQLModel
- **Schema Simplification**: From 15 opportunity-related tables to 1
- **Code Changes**: Update imports in pipeline modules

## Rollback Plan

- Keep backup of `app_opportunities` export before deletion
- Database backups automatically maintained by Supabase
- Can restore from backup if needed

## Timeline

1. Backup phase: 5 minutes
2. Migration: 10 minutes
3. Cleanup: 10 minutes
4. Code updates: 30 minutes
5. Testing: 20 minutes

**Total**: ~75 minutes
