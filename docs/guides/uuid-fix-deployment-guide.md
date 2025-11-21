# UUID Format Fixes and Deduplication Schema Deployment Guide

## Overview

This guide covers the deployment of the UUID format fixes and complete deduplication schema integration for RedditHarbor production deployment. These changes resolve critical data integrity issues discovered during the core functions fixes and ensure proper foreign key relationships across the database schema.

## Migration Files

### Primary Migration
- **File**: `supabase/migrations/20251120000000_fix_uuid_format_and_deduplication_schema.sql`
- **Purpose**: Fix UUID format inconsistencies and complete deduplication schema integration
- **Dependencies**: All previous migrations up to `20251119063934_add_deduplication_integration_tracking.sql`

## Prerequisites

### 1. Environment Setup
- Source Python environment: `source .venv/bin/activate`
- Verify Supabase CLI is installed and configured
- Ensure local database is running: `supabase start`

### 2. Backup Requirements
- Create full database backup before running migrations
- Backup existing migration files
- Document current schema state

```bash
# Create backup directory
mkdir -p backups/pre-deployment/$(date +%Y%m%d_%H%M%S)

# Export schema
supabase db dump --data-only -f backups/pre-deployment/$(date +%Y%m%d_%H%M%S)/data_dump.sql

# Export schema structure
supabase db dump --schema-only -f backups/pre-deployment/$(date +%Y%m%d_%H%M%S)/schema_dump.sql
```

## Key Changes Summary

### 1. UUID Format Fixes

#### Before Migration Issues:
- `app_opportunities.submission_id` (TEXT) inconsistent with `submissions.id` (UUID)
- Broken foreign key relationships due to type mismatches
- Missing primary keys in several tables

#### After Migration Improvements:
- Added `submission_uuid` (UUID) columns to tables needing UUID foreign keys
- Created proper UUID-based foreign key constraints
- Added primary key columns where missing
- Implemented UUID conversion functions for data migration

### 2. Deduplication Schema Completion

#### Added to `opportunities_unified` table:
- `submission_id` (UUID) - Proper foreign key to submissions
- `business_concept_id` (BIGINT) - Link to business concepts
- `semantic_fingerprint` (TEXT) - For semantic deduplication
- `copied_from_primary` (BOOLEAN) - Deduplication tracking
- `primary_opportunity_id` (UUID) - Self-referencing for duplicates
- Analysis result columns (app_concept, core_functions, etc.)
- Metadata columns (analyzed_at, enrichment_version, etc.)

### 3. Foreign Key Constraint Updates

#### Updated Constraints:
- `app_opportunities.submission_uuid` → `submissions.id`
- `llm_monetization_analysis.submission_uuid` → `submissions.id`
- `workflow_results.opportunity_id` → `opportunities_unified.id`
- `llm_monetization_analysis.primary_opportunity_id` → `opportunities_unified.id`

## Deployment Steps

### Step 1: Pre-Deployment Validation

```bash
# Activate environment
source .venv/bin/activate

# Check current migration status
supabase db diff

# Run validation on current state
python -c "
import asyncio
from core.enrichment.base_service import BaseEnrichmentService
# Add your validation code here
print('Running pre-deployment validation...')
"
```

### Step 2: Apply Migration

```bash
# Apply the primary migration
supabase db push

# Monitor for any errors
supabase db diff  # Should show minimal changes after push
```

### Step 3: Post-Deployment Validation

```bash
# Run the validation function included in the migration
psql $DATABASE_URL -c "SELECT * FROM validate_uuid_format_consistency();"

# Check the deduplication overview view
psql $DATABASE_URL -c "SELECT * FROM deduplication_schema_overview;"

# Verify data integrity
python -c "
import asyncio
from scripts.migration.phase3_core_restructuring import CoreRestructuringManager
async def validate():
    manager = CoreRestructuringManager(dry_run=True)
    return await manager.validate_only()
asyncio.run(validate())
"
```

### Step 4: Application Testing

```bash
# Test core functionality
python scripts/test_opportunity_pipeline.py --test-uuid-fixes

# Test deduplication functionality
python scripts/test_deduplication_integration.py --validate-relationships

# Run full integration tests
pytest tests/test_uuid_migration.py -v
```

## Rollback Procedures

### Emergency Rollback

If critical issues are discovered:

```bash
# Quick rollback (if migration was just applied)
supabase db reset  # This will reset to the last migration

# OR use the rollback function (if partial application)
psql $DATABASE_URL -c "SELECT rollback_uuid_format_changes();"

# Restore from backup if needed
psql $DATABASE_URL < backups/pre-deployment/TIMESTAMP/data_dump.sql
```

### Manual Rollback Steps

1. **Stop all application services**
2. **Restore database from backup**
3. **Verify application functionality**
4. **Investigate migration failure causes**

## Validation Checklist

### Pre-Deployment
- [ ] Database backup created and verified
- [ ] Migration files reviewed and approved
- [ ] Environment variables configured
- [ ] Application services stopped

### Post-Deployment
- [ ] Migration applied successfully
- [ ] No validation errors in `validate_uuid_format_consistency()`
- [ ] All foreign key constraints valid
- [ ] Data integrity maintained
- [ ] Application tests passing
- [ ] Performance acceptable

### Functional Testing
- [ ] Opportunity creation pipeline working
- [ ] Deduplication logic functioning
- [ ] LLM analysis pipeline operational
- [ ] UI applications loading correctly
- [ ] API endpoints responding properly

## Monitoring and Performance

### Key Metrics to Monitor

1. **Database Performance**
   - Query execution times
   - Index usage statistics
   - Connection pool utilization

2. **Application Performance**
   - API response times
   - Error rates
   - Memory usage

3. **Data Integrity**
   - Foreign key constraint violations
   - Orphaned record counts
   - UUID format consistency

### Monitoring Commands

```sql
-- Check query performance
EXPLAIN ANALYZE SELECT * FROM opportunities_unified WHERE business_concept_id IS NOT NULL;

-- Monitor index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
WHERE schemaname = 'public' ORDER BY idx_scan DESC;

-- Check constraint violations
SELECT * FROM validate_uuid_format_consistency() WHERE issue_count > 0;
```

## Troubleshooting

### Common Issues

#### 1. Migration Fails Due to Constraint Violations
```sql
-- Identify problematic records
SELECT submission_id, COUNT(*)
FROM app_opportunities
WHERE submission_uuid IS NULL
GROUP BY submission_id;

-- Fix manually if needed
UPDATE app_opportunities
SET submission_uuid = gen_random_uuid()
WHERE submission_uuid IS NULL;
```

#### 2. Performance Issues After Migration
```sql
-- Check if indexes are being used
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM opportunities_unified
WHERE business_concept_id = 123;

-- Rebuild indexes if necessary
REINDEX INDEX CONCURRENTLY idx_opportunities_unified_business_concept;
```

#### 3. Data Consistency Issues
```sql
-- Check for orphaned records
SELECT 'opportunities_unified' as table_name, COUNT(*) as orphaned_count
FROM opportunities_unified ou
LEFT JOIN submissions s ON ou.submission_id = s.id
WHERE s.id IS NULL;
```

## Support Contacts

- **Database Administrator**: [Contact Information]
- **Application Developer**: [Contact Information]
- **DevOps Engineer**: [Contact Information]

## Appendices

### A. Schema Changes Summary

| Table | New Columns | Modified Columns | New Constraints |
|-------|-------------|------------------|-----------------|
| app_opportunities | id, submission_uuid | None | fk_submission_uuid |
| llm_monetization_analysis | id, submission_uuid | None | fk_submission_uuid, fk_primary_opportunity |
| workflow_results | submission_uuid | None | fk_submission_uuid |
| opportunities_unified | Multiple deduplication columns | None | Various deduplication constraints |

### B. Migration Dependencies

The UUID fixes migration depends on:
- Base schema (`00000000000000_baseline_schema.sql`)
- Deduplication schema (`20251119005848_add_deduplication_schema.sql`)
- Integration tracking (`20251119063934_add_deduplication_integration_tracking.sql`)

### C. Security Considerations

- All foreign key constraints use `ON DELETE SET NULL` or `ON DELETE CASCADE` appropriately
- UUID generation uses PostgreSQL's `gen_random_uuid()` for security
- No sensitive data is exposed in new columns or indexes
- Migration includes proper transaction handling

---

**Version**: 1.0
**Last Updated**: 2025-11-20
**Next Review**: 2025-11-27