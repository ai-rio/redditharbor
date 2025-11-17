# Schema Consolidation Plan

## Executive Summary

This plan outlines the strategy for consolidating 20 migration files (3,156 lines) into a streamlined, maintainable baseline migration that accurately represents the working schema captured in `schema_dumps/dlt_trust_pipeline_success_schema_20251117_194348.sql`.

**Goal**: Create a single baseline migration that can replace the first 19 migrations while preserving data integrity and system functionality.

**Estimated Effort**: 8-12 hours (dev + testing + validation)

**Risk Level**: MEDIUM (requires careful testing, but working schema provides safety net)

---

## Current State Assessment

### Migration Landscape
- **Total Migrations**: 20 files
- **Total Lines**: 3,156 lines
- **Date Range**: 2025-11-04 to 2025-11-14 (10 days)
- **Schemas Affected**: public, public_staging (DLT)
- **Tables Created**: 20 core tables + DLT metadata + views

### Key Challenges
1. **Migration Sprawl**: 20 files for a 10-day development cycle indicates high churn
2. **Fragmented Features**: Trust layer spans 3 migrations, cost tracking spans 4 migrations
3. **DLT Dependency**: Schema relies on DLT-created tables not tracked in migrations
4. **Schema Drift**: Working schema may differ from migration history due to DLT interference
5. **Testing Overhead**: 20 migrations require 20 test runs for full validation

---

## Consolidation Strategy

### Option A: Full Consolidation (Recommended)
**Approach**: Replace migrations 1-19 with single baseline, keep migration 20 as incremental

#### Structure
```
supabase/migrations/
├── 00000000000000_baseline_schema.sql          # NEW: Consolidated baseline
├── 20251114232013_add_simplicity_score.sql     # KEEP: Latest incremental change
└── archived/                                    # MOVE: Original 20 migrations
    ├── 20251104190002_market_validation.sql
    ├── 20251104190003_competitive_analysis.sql
    └── ... (18 more files)
```

#### Baseline Migration Contents
1. **Core Reddit Tables**: subreddits, redditors, submissions, comments
2. **Opportunity Tables**: opportunities, opportunity_scores, score_components
3. **Validation Tables**: market_validations, competitive_landscape, feature_gaps, cross_platform_verification
4. **Monetization Tables**: monetization_patterns, user_willingness_to_pay, technical_assessments
5. **Workflow Tables**: workflow_results, app_opportunities
6. **Analytics Tables**: problem_metrics, customer_leads
7. **All Indexes**: Consolidated from migration 4 + individual migrations
8. **All Constraints**: CHECK, FK, UNIQUE constraints
9. **All Views**: migration_validation_report, top_opportunities, problem_metrics_summary, etc.
10. **All Functions**: calculate_trending_score(), update_problem_metrics(), etc.
11. **All Comments**: Table and column documentation

**Advantages**:
- Single source of truth for schema
- Fast fresh database setup (1 migration vs 20)
- Eliminates migration order dependencies
- Simplifies testing and rollback
- Easier onboarding for new developers

**Disadvantages**:
- Requires thorough testing
- Existing databases need migration path
- Loses granular history (mitigated by archiving)

---

### Option B: Logical Grouping
**Approach**: Consolidate into 5 logical migration groups

#### Structure
```
supabase/migrations/
├── 20251104000001_core_reddit_schema.sql           # Subreddits, redditors, submissions, comments
├── 20251104000002_opportunity_analysis.sql         # Opportunities + scoring + validation
├── 20251104000003_monetization_technical.sql       # Monetization + technical + competitive
├── 20251104000004_workflow_trust_analytics.sql     # Workflow + trust layer + analytics
├── 20251114232013_add_simplicity_score.sql         # Keep latest incremental
└── archived/                                        # Original 20 migrations
```

**Advantages**:
- Preserves logical architecture boundaries
- Easier to understand evolution
- More conservative approach

**Disadvantages**:
- Still requires 5 migration tests vs 1
- Doesn't fully solve migration sprawl
- Retains some complexity

---

### Option C: Hybrid Approach (Best for Production)
**Approach**: Baseline + incremental for last 30 days

#### Structure
```
supabase/migrations/
├── 20251104000000_baseline_schema.sql              # Migrations 1-17 (up to 2025-11-13)
├── 20251114200000_add_customer_leads.sql           # Keep recent changes
├── 20251114200001_add_llm_monetization.sql         # Keep recent changes
├── 20251114232013_add_simplicity_score.sql         # Keep recent changes
└── archived/                                        # Migrations 1-17
```

**Advantages**:
- Balances consolidation with recency
- Preserves recent incremental changes
- Easier to review recent work
- Lower risk (recent migrations tested in production)

**Disadvantages**:
- Arbitrary 30-day cutoff
- Still 4 migrations (vs ideal 1)

---

## Recommended Approach: Option A (Full Consolidation)

### Rationale
1. **Fresh Start**: Project is early stage (10 days of migrations)
2. **Working Schema**: Complete schema dump provides safety net
3. **DLT Integration**: DLT manages own tables; baseline won't interfere
4. **Developer Experience**: New team members can spin up DB in 1 migration
5. **Testing Efficiency**: 1 baseline + incremental migrations easier to validate

---

## Implementation Plan

### Phase 1: Preparation (1-2 hours)

#### 1.1 Backup Current State
```bash
# Dump working schema
pg_dump -s postgresql://postgres:postgres@127.0.0.1:54322/postgres \
  > schema_dumps/pre_consolidation_backup_$(date +%Y%m%d_%H%M%S).sql

# Backup migration files
cp -r supabase/migrations supabase/migrations_backup_$(date +%Y%m%d_%H%M%S)
```

#### 1.2 Archive Existing Migrations
```bash
mkdir -p supabase/migrations/archived
mv supabase/migrations/202511*.sql supabase/migrations/archived/
```

#### 1.3 Extract Working Schema Sections
Create script to extract from `dlt_trust_pipeline_success_schema_20251117_194348.sql`:
- Table definitions (public schema only)
- Index definitions
- Constraint definitions
- View definitions
- Function definitions
- Comment statements

---

### Phase 2: Baseline Creation (3-4 hours)

#### 2.1 Create Baseline Migration File
**File**: `supabase/migrations/00000000000000_baseline_schema.sql`

**Structure**:
```sql
-- ============================================================================
-- RedditHarbor Baseline Schema
-- Created: 2025-11-17
-- Consolidates: Migrations 1-19 (2025-11-04 to 2025-11-14)
-- Source: schema_dumps/dlt_trust_pipeline_success_schema_20251117_194348.sql
-- ============================================================================

-- ============================================================================
-- PART 1: CORE REDDIT TABLES
-- ============================================================================

-- Subreddits
CREATE TABLE IF NOT EXISTS subreddits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    ... -- Full column definitions
);

-- Redditors
-- Submissions
-- Comments

-- ============================================================================
-- PART 2: OPPORTUNITY ANALYSIS TABLES
-- ============================================================================

-- Opportunities
-- Opportunity Scores
-- Score Components

-- ============================================================================
-- PART 3: VALIDATION & COMPETITIVE TABLES
-- ============================================================================

-- Market Validations
-- Competitive Landscape
-- Feature Gaps
-- Cross-Platform Verification

-- ============================================================================
-- PART 4: MONETIZATION & TECHNICAL TABLES
-- ============================================================================

-- Monetization Patterns
-- User Willingness to Pay
-- Technical Assessments

-- ============================================================================
-- PART 5: WORKFLOW & ANALYTICS TABLES
-- ============================================================================

-- Workflow Results
-- App Opportunities
-- Problem Metrics
-- Customer Leads

-- ============================================================================
-- PART 6: INDEXES
-- ============================================================================

-- Foreign key indexes
-- Scoring indexes
-- Timestamp indexes
-- Composite indexes

-- ============================================================================
-- PART 7: VIEWS
-- ============================================================================

-- Migration validation report
-- Top opportunities
-- Problem metrics summary
-- Trending problems
-- High engagement problems
-- LLM cost summary
-- LLM usage by day
-- LLM error analysis
-- LLM performance metrics

-- ============================================================================
-- PART 8: FUNCTIONS
-- ============================================================================

-- calculate_trending_score()
-- update_problem_metrics()
-- calculate_token_cost()
-- update_opportunity_costs()
-- get_cost_breakdown()

-- ============================================================================
-- PART 9: COMMENTS & DOCUMENTATION
-- ============================================================================

-- Table comments
-- Column comments
```

#### 2.2 Exclude DLT-Managed Tables
**Do NOT include in baseline**:
- `_dlt_loads`
- `_dlt_pipeline_state`
- `_dlt_version`
- `_migrations_log` (handled separately)
- `app_opportunities__core_functions` (DLT child table)
- All `public_staging.*` tables (DLT staging)

**Rationale**: DLT creates these tables automatically; including them causes conflicts

#### 2.3 Extract Column Definitions
For each table, extract from working schema:
1. Column names, types, defaults
2. NOT NULL constraints
3. CHECK constraints
4. UNIQUE constraints
5. Generated columns (opportunity_scores.total_score, workflow_results.opportunity_assessment_score)

#### 2.4 Extract Relationship Definitions
For each FK, extract:
1. Foreign table and column
2. ON DELETE action (CASCADE, SET NULL, RESTRICT)
3. ON UPDATE action (if specified)

---

### Phase 3: Incremental Migration Handling (1 hour)

#### 3.1 Restore Latest Incremental Migration
```bash
cp supabase/migrations/archived/20251114232013_add_simplicity_score_and_assessment.sql \
   supabase/migrations/20251114232013_add_simplicity_score.sql
```

#### 3.2 Modify Incremental Migration
Update to work with baseline:
- Remove redundant column additions already in baseline
- Keep only NET NEW changes (simplicity_score + opportunity_assessment_score)
- Update comments to reference baseline

---

### Phase 4: Testing & Validation (2-3 hours)

#### 4.1 Fresh Database Test
```bash
# Stop Supabase
supabase stop

# Reset database
supabase db reset

# Start Supabase (will run migrations)
supabase start

# Verify schema
psql postgresql://postgres:postgres@127.0.0.1:54322/postgres \
  -c "\dt public.*"
```

#### 4.2 Schema Comparison
```bash
# Dump new schema
pg_dump -s postgresql://postgres:postgres@127.0.0.1:54322/postgres \
  > schema_dumps/post_consolidation_$(date +%Y%m%d_%H%M%S).sql

# Compare schemas
diff -u \
  schema_dumps/dlt_trust_pipeline_success_schema_20251117_194348.sql \
  schema_dumps/post_consolidation_*.sql
```

**Expected Differences**:
- DLT tables (created by DLT, not migrations)
- Timestamp differences in default values
- Order of definitions (cosmetic)

**Unacceptable Differences**:
- Missing tables
- Missing columns
- Incorrect column types
- Missing constraints
- Missing indexes

#### 4.3 Functional Testing
Run application test suite:
```bash
pytest tests/ -v
```

Test critical workflows:
1. Reddit data collection
2. Opportunity creation
3. Scoring calculations
4. Trust validation
5. Cost tracking

#### 4.4 Data Migration Test (If Existing Data)
If consolidating production database:
1. Export data from all tables
2. Apply baseline migration to fresh DB
3. Import data
4. Verify data integrity
5. Run application tests

---

### Phase 5: Documentation & Cleanup (1-2 hours)

#### 5.1 Update Migration README
Create `supabase/migrations/README.md`:
```markdown
# RedditHarbor Database Migrations

## Current Structure
- `00000000000000_baseline_schema.sql`: Complete schema baseline
- `20251114232013_add_simplicity_score.sql`: Simplicity scoring addition

## Archived Migrations
Original 20 incremental migrations moved to `archived/` subdirectory.

## Development Workflow
1. Fresh setup: `supabase db reset` (runs all migrations)
2. New migration: `supabase migration new <name>`
3. Apply: `supabase db push`

## Schema Documentation
See `/docs/schema-consolidation/` for:
- ERD diagram
- Migration history analysis
- Consolidation rationale
```

#### 5.2 Update Project Documentation
Update main README.md:
- Reference consolidated schema
- Update setup instructions
- Link to schema documentation

#### 5.3 Archive Original Migrations
Create `supabase/migrations/archived/README.md`:
```markdown
# Archived Migrations

These migrations were consolidated into `00000000000000_baseline_schema.sql`
on 2025-11-17.

Preserved for historical reference and audit trail.

## Original Migration Timeline
[Table from migration-analysis.md]

## Consolidation Rationale
See `/docs/schema-consolidation/consolidation-plan.md`
```

---

## Rollback Plan

### If Consolidation Fails

#### Option 1: Restore Backup
```bash
# Restore migration files
rm -rf supabase/migrations
mv supabase/migrations_backup_* supabase/migrations

# Reset database
supabase db reset
```

#### Option 2: Keep Baseline, Add Fixes
```bash
# Keep baseline migration
# Create fix migration for identified issues
supabase migration new fix_baseline_schema

# Apply fix
supabase db push
```

---

## Success Criteria

### Migration Must Pass
- [ ] Fresh database setup with `supabase db reset`
- [ ] All tables created with correct schemas
- [ ] All indexes created
- [ ] All FK constraints established
- [ ] All views functional
- [ ] All functions defined and working

### Schema Must Match
- [ ] Table count matches working schema (20 core tables)
- [ ] Column count matches for each table
- [ ] Data types match exactly
- [ ] Constraints match (CHECK, FK, UNIQUE, NOT NULL)
- [ ] Indexes match
- [ ] Generated columns work correctly

### Application Must Function
- [ ] Reddit data collection pipeline works
- [ ] Opportunity scoring calculates correctly
- [ ] Trust validation stores data
- [ ] Cost tracking updates
- [ ] All views return data
- [ ] All functions execute without errors

### Tests Must Pass
- [ ] Unit tests pass: `pytest tests/`
- [ ] Integration tests pass
- [ ] Schema validation tests pass
- [ ] No regressions in existing functionality

---

## Migration Script Template

```bash
#!/bin/bash
# consolidate_migrations.sh
# Automates schema consolidation process

set -e  # Exit on error

echo "=== RedditHarbor Migration Consolidation ==="
echo ""

# Step 1: Backup
echo "Step 1: Creating backups..."
BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump -s postgresql://postgres:postgres@127.0.0.1:54322/postgres \
  > schema_dumps/pre_consolidation_backup_${BACKUP_TIMESTAMP}.sql
cp -r supabase/migrations supabase/migrations_backup_${BACKUP_TIMESTAMP}
echo "✓ Backups created"

# Step 2: Archive
echo "Step 2: Archiving original migrations..."
mkdir -p supabase/migrations/archived
mv supabase/migrations/202511*.sql supabase/migrations/archived/
echo "✓ Migrations archived"

# Step 3: Create baseline
echo "Step 3: Creating baseline migration..."
# (Run Python/SQL script to generate baseline from schema dump)
python scripts/generate_baseline_migration.py \
  --input schema_dumps/dlt_trust_pipeline_success_schema_20251117_194348.sql \
  --output supabase/migrations/00000000000000_baseline_schema.sql
echo "✓ Baseline created"

# Step 4: Restore incremental
echo "Step 4: Restoring latest incremental migration..."
cp supabase/migrations/archived/20251114232013_add_simplicity_score_and_assessment.sql \
   supabase/migrations/20251114232013_add_simplicity_score.sql
echo "✓ Incremental restored"

# Step 5: Test
echo "Step 5: Testing migrations..."
supabase db reset
echo "✓ Migrations applied"

# Step 6: Validate
echo "Step 6: Validating schema..."
pg_dump -s postgresql://postgres:postgres@127.0.0.1:54322/postgres \
  > schema_dumps/post_consolidation_${BACKUP_TIMESTAMP}.sql
echo "✓ Schema dumped for comparison"

echo ""
echo "=== Consolidation Complete ==="
echo "Review schema dumps for differences:"
echo "  - Pre:  schema_dumps/pre_consolidation_backup_${BACKUP_TIMESTAMP}.sql"
echo "  - Post: schema_dumps/post_consolidation_${BACKUP_TIMESTAMP}.sql"
echo ""
echo "Run tests: pytest tests/ -v"
```

---

## Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| Phase 1: Preparation | 1-2 hours | Backup, archive, extract schema |
| Phase 2: Baseline Creation | 3-4 hours | Create baseline migration |
| Phase 3: Incremental Handling | 1 hour | Restore/modify latest migration |
| Phase 4: Testing & Validation | 2-3 hours | Fresh DB test, schema comparison, functional tests |
| Phase 5: Documentation | 1-2 hours | README updates, documentation |
| **Total** | **8-12 hours** | **Full consolidation** |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Schema drift | MEDIUM | HIGH | Use working schema dump as source of truth |
| DLT conflicts | HIGH | MEDIUM | Exclude DLT tables from baseline |
| Data loss | LOW | HIGH | Backup before consolidation |
| Application breakage | LOW | HIGH | Comprehensive testing before deployment |
| Migration ordering | LOW | MEDIUM | Use timestamp prefix 00000000000000 |
| Rollback difficulty | LOW | MEDIUM | Keep backups, document rollback procedure |

---

## Future Recommendations

### Migration Hygiene
1. **One Concern Per Migration**: Avoid multi-purpose migrations
2. **Descriptive Names**: Use clear, searchable migration names
3. **Idempotent SQL**: Always use IF NOT EXISTS, IF EXISTS for safety
4. **Rollback Scripts**: Include rollback procedure in migration comments
5. **Testing**: Test migrations on fresh DB before merging

### Schema Evolution
1. **Baseline Refresh**: Consolidate every 50-100 migrations or quarterly
2. **Breaking Changes**: Use separate schema versions for major changes
3. **DLT Isolation**: Keep DLT tables in separate schema if possible
4. **Documentation**: Update ERD and schema docs with each migration

### Automation
1. **Schema Diff Tool**: Automate schema comparison
2. **Migration Testing**: CI/CD pipeline for migration validation
3. **Schema Versioning**: Track schema version in database
4. **Baseline Generator**: Script to generate baseline from working schema

---

## Related Documentation

- [ERD Diagram](./erd.md) - Complete entity relationship diagram
- [Migration Analysis](./migration-analysis.md) - Historical schema evolution
- [README](./README.md) - Schema consolidation overview

---

## Appendix: Baseline Migration Extraction Script

```python
#!/usr/bin/env python3
"""
Generate baseline migration from working schema dump.

Usage:
    python scripts/generate_baseline_migration.py \
        --input schema_dumps/dlt_trust_pipeline_success_schema_20251117_194348.sql \
        --output supabase/migrations/00000000000000_baseline_schema.sql
"""

import re
import argparse
from pathlib import Path

def extract_public_schema(sql_dump: str) -> str:
    """Extract only public schema objects, excluding DLT tables."""

    # Tables to exclude (DLT-managed)
    exclude_tables = [
        '_dlt_loads',
        '_dlt_pipeline_state',
        '_dlt_version',
        '_migrations_log',
        'app_opportunities__core_functions',
    ]

    # Extract sections
    tables = extract_tables(sql_dump, exclude_tables)
    indexes = extract_indexes(sql_dump, exclude_tables)
    constraints = extract_constraints(sql_dump, exclude_tables)
    views = extract_views(sql_dump)
    functions = extract_functions(sql_dump)
    comments = extract_comments(sql_dump, exclude_tables)

    # Build baseline migration
    baseline = f"""-- ============================================================================
-- RedditHarbor Baseline Schema
-- Created: {datetime.now().strftime('%Y-%m-%d')}
-- Consolidates: Migrations 1-19 (2025-11-04 to 2025-11-14)
-- Source: schema_dumps/dlt_trust_pipeline_success_schema_20251117_194348.sql
--
-- EXCLUDED FROM BASELINE (DLT-managed):
{chr(10).join(f'--   - {table}' for table in exclude_tables)}
-- ============================================================================

{tables}

{indexes}

{constraints}

{views}

{functions}

{comments}
"""

    return baseline

# Implementation of extraction functions...
# (See full script in /scripts/generate_baseline_migration.py)
```

---

## Sign-off

**Created By**: Schema Consolidation Team
**Date**: 2025-11-17
**Approved By**: _[Pending]_
**Status**: DRAFT - Awaiting Review

---
