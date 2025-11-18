# RedditHarbor Schema Consolidation

## Overview

This directory contains comprehensive documentation of the RedditHarbor database schema consolidation effort, including the complete Entity Relationship Diagram (ERD), migration history analysis, and consolidation strategy.

**Date**: 2025-11-17
**Working Schema**: `schema_dumps/dlt_trust_pipeline_success_schema_20251117_194348.sql`
**Migration Count**: 20 files, 3,156 lines
**Schema Version**: 1.0 (post-simplicity-score)

---

## ⚠️ CRITICAL WARNINGS - READ BEFORE ANY SCHEMA CHANGES

### Schema Consolidation Prerequisites

**DO NOT proceed with schema consolidation until**:
- [ ] All 3 new documentation files have been reviewed: `pipeline-schema-dependencies.md`, `jsonb-schema-versions.md`, `hardcoded-references-analysis.md`
- [ ] All 7 production pipelines have been tested and validated
- [ ] All 145+ hard-coded column references have been documented
- [ ] All JSONB schemas have been versioned
- [ ] The `core_functions` format inconsistency has been resolved
- [ ] All DLT primary key dependencies have been identified
- [ ] Trust validation system dependencies have been mapped
- [ ] Market validation persistence patterns have been documented

### Critical Issues Identified

**1. core_functions Format Inconsistency** (CRITICAL)
- **Problem**: 3 different serialization formats for same column
- **Impact**: Data inconsistency, query failures, parsing errors
- **Files**: `dlt_trust_pipeline.py` (Python list), `dlt_app_opportunities.py` (JSON string), `batch_opportunity_scoring.py` (CSV string)
- **Action**: MUST standardize before consolidation (see `jsonb-schema-versions.md` Section 1)

**2. DLT Merge Disposition Dependencies** (CRITICAL)
- **Problem**: Hard-coded primary key strings in 4 DLT resources
- **Impact**: Renaming primary keys breaks DLT merge logic, creates duplicates
- **Columns**: `submission_id`, `opportunity_id`
- **Action**: Refactor to constants before any renames (see `hardcoded-references-analysis.md` Part 3)

**3. Trust Validation System Coupling** (HIGH)
- **Problem**: 12 trust columns tightly coupled across 3 tables
- **Impact**: Breaking any trust column stops trust validation pipeline
- **Action**: Document all dependencies before changes (see `pipeline-schema-dependencies.md` Pipeline 3)

**4. GENERATED Column Dependencies** (HIGH)
- **Problem**: `opportunity_assessment_score` formula references dimension score columns
- **Impact**: Renaming dimension scores breaks GENERATED column
- **Action**: Update formula in migration if renaming (see `pipeline-schema-dependencies.md` Pipeline 2)

---

## Documentation Structure

### [erd.md](./erd.md)
**Complete Entity Relationship Diagram**

Comprehensive Mermaid ERD showing all tables, columns, relationships, and constraints in the working schema. Includes:
- Reddit data domain (submissions, comments, redditors, subreddits)
- Opportunity analysis domain (opportunities, scoring, validation)
- DLT pipeline domain (staging, metadata, child tables)
- Complete foreign key relationships
- Scoring methodology (6-dimension weighted system)
- Data quality constraints and indexes

**Use this for**:
- Understanding schema architecture
- Planning new features requiring database changes
- Onboarding new developers
- Troubleshooting relationship issues

### [migration-analysis.md](./migration-analysis.md)
**Historical Migration Evolution**

Detailed analysis of all 20 migration files, organized chronologically by phase:
1. Foundation (market validation, competitive analysis, monetization)
2. Schema consolidation (DLT merge, data migration)
3. DLT integration (pipeline metadata, staging tables)
4. Credibility & trust layers (validation signals, trust scoring)
5. Cost tracking & analytics (LLM monitoring, customer leads)
6. Methodology alignment (6th dimension, simplicity scoring)

**Use this for**:
- Understanding why the schema evolved this way
- Identifying migration drift and schema inconsistencies
- Planning future migrations
- Auditing schema changes

### [consolidation-plan.md](./consolidation-plan.md)
**Migration Consolidation Strategy**

Step-by-step plan for consolidating 20 migration files into a streamlined baseline migration. Includes:
- Three consolidation options (full, logical grouping, hybrid)
- Implementation plan with 5 phases
- Testing and validation procedures
- Rollback plan
- Success criteria
- Risk assessment
- Timeline and effort estimates (8-12 hours)

**Use this for**:
- Executing schema consolidation
- Creating baseline migrations for fresh deployments
- Reducing migration overhead
- Improving developer experience

### [pipeline-schema-dependencies.md](./pipeline-schema-dependencies.md) ⚠️ CRITICAL
**Complete Pipeline Dependency Matrix**

Comprehensive analysis of all 7 production pipelines and their database dependencies. Includes:
- Table-by-table dependency analysis with line-level code references
- Hard-coded column name inventory (145+ references)
- DLT merge disposition dependencies (4 primary keys)
- Trust validation system integration (12 columns)
- Market validation persistence patterns
- JSONB column dependencies
- Breaking change risk assessment for each dependency
- Safe refactoring recommendations

**Use this for**:
- REQUIRED before any schema changes
- Understanding pipeline data flow
- Identifying breaking changes
- Planning column renames
- Refactoring hard-coded references

### [jsonb-schema-versions.md](./jsonb-schema-versions.md) ⚠️ HIGH PRIORITY
**JSONB Column Schema Documentation**

Version-controlled documentation for all 7 JSONB columns. Includes:
- JSON structure specifications with types
- Required vs optional fields
- Backward compatibility rules
- Code locations that parse each JSONB column
- Schema evolution best practices
- Migration strategies for structure changes
- **CRITICAL**: Documents `core_functions` format inconsistency (3 different formats!)

**Use this for**:
- REQUIRED before modifying JSONB structures
- Adding version fields to JSONB columns
- Understanding parsing dependencies
- Planning data migrations
- Debugging JSONB parsing errors

### [hardcoded-references-analysis.md](./hardcoded-references-analysis.md) ⚠️ HIGH PRIORITY
**Hard-Coded Reference Inventory & Refactoring Guide**

Complete inventory of all hard-coded schema references with refactoring recommendations. Includes:
- 145+ hard-coded column name references with line numbers
- 8 SQL queries with string column names
- 4 DLT primary key strings
- 30+ JSONB field access patterns
- Schema constants module design
- Query builder utilities
- DLT configuration centralization
- 5-phase refactoring timeline

**Use this for**:
- REQUIRED before schema consolidation
- Planning code refactoring
- Removing hard-coded strings
- Standardizing column access
- Creating query builders
- Testing schema changes

---

## Quick Start

### View the Schema
```bash
# Start Supabase
supabase start

# Access Supabase Studio
open http://127.0.0.1:54323

# Or use SQL directly
psql postgresql://postgres:postgres@127.0.0.1:54322/postgres
```

### Generate Fresh Schema Dump
```bash
# Dump full schema (all schemas)
pg_dump -s postgresql://postgres:postgres@127.0.0.1:54322/postgres \
  > schema_dumps/full_schema_$(date +%Y%m%d_%H%M%S).sql

# Dump public schema only
pg_dump -s -n public postgresql://postgres:postgres@127.0.0.1:54322/postgres \
  > schema_dumps/public_schema_$(date +%Y%m%d_%H%M%S).sql
```

### Compare Schemas
```bash
# Compare two schema dumps
diff -u schema_dumps/schema1.sql schema_dumps/schema2.sql

# Ignore timestamps and cosmetic differences
diff -u schema_dumps/schema1.sql schema_dumps/schema2.sql | \
  grep -v "^---" | grep -v "^+++" | grep -v "Dump completed on"
```

### Visualize ERD
1. Open [erd.md](./erd.md)
2. Copy Mermaid diagram code
3. Paste into [Mermaid Live Editor](https://mermaid.live)
4. Export as PNG/SVG for presentations

---

## Schema Statistics

### Core Tables (Public Schema)
| Category | Tables | Description |
|----------|--------|-------------|
| Reddit Data | 4 | subreddits, redditors, submissions, comments |
| Opportunities | 3 | opportunities, opportunity_scores, score_components |
| Validation | 4 | market_validations, competitive_landscape, feature_gaps, cross_platform_verification |
| Monetization | 3 | monetization_patterns, user_willingness_to_pay, technical_assessments |
| Workflows | 4 | workflow_results, app_opportunities, problem_metrics, customer_leads |
| DLT Metadata | 3 | _dlt_loads, _dlt_pipeline_state, _dlt_version |
| **Total** | **21** | **Core application tables** |

### Relationships
- **Foreign Keys**: 16 relationships
- **Self-referencing**: 1 (comments.parent_comment_id → comments.id)
- **Cascading Deletes**: 14 FK constraints
- **SET NULL Deletes**: 2 FK constraints (opportunities, user_willingness_to_pay)

### Data Quality
- **CHECK Constraints**: 35+ (score ranges, enums, value validation)
- **NOT NULL Constraints**: 40+ required fields
- **UNIQUE Constraints**: 2 (subreddits.name, redditors.username)
- **Generated Columns**: 2 (opportunity_scores.total_score, workflow_results.opportunity_assessment_score)

### Performance
- **Indexes**: 50+ indexes
  - Foreign key indexes (16)
  - Scoring indexes (6)
  - Timestamp indexes (8)
  - Composite indexes (4)
  - Full-text search indexes (0 - future enhancement)

---

## Schema Architecture

### Layered Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Application Layer                   │
│  (Python/Airflow DAGs, LLM Agents, API Endpoints)   │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│              Workflow & Analytics Layer              │
│  (workflow_results, app_opportunities, metrics)      │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│            Opportunity Analysis Layer                │
│  (opportunities, scores, validations, monetization)  │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                Reddit Data Layer                     │
│  (subreddits, submissions, comments, redditors)      │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                  DLT Pipeline Layer                  │
│  (public_staging.*, _dlt_*, incremental loads)       │
└─────────────────────────────────────────────────────┘
```

### Data Flow

```
1. Reddit API → DLT Pipeline → public_staging.app_opportunities
2. DLT → Normalization → public.submissions, public.comments
3. Submissions → Opportunity Detection → public.opportunities
4. Opportunities → LLM Profiling → public.workflow_results
5. Workflow Results → Scoring → public.opportunity_scores
6. Opportunities → Validation → market_validations, competitive_landscape, etc.
7. Opportunities → Monetization Analysis → monetization_patterns
8. Validated Opportunities → Customer Leads → customer_leads
```

---

## Scoring Methodology

### 6-Dimension Opportunity Scoring

The schema implements a comprehensive 6-dimension scoring system with specific weights optimized for app opportunity validation:

| Dimension | Weight | Range | Source Table | Description |
|-----------|--------|-------|--------------|-------------|
| **Market Demand** | 20% | 0-100 | opportunity_scores | Discussion volume + engagement rate + trend velocity + audience size |
| **Pain Intensity** | 25% | 0-100 | opportunity_scores | User frustration signals + emotional language + problem urgency |
| **Monetization Potential** | 20% | 0-100 | opportunity_scores | Willingness to pay + revenue estimates + pricing validation |
| **Market Gap** | 10% | 0-100 | opportunity_scores | Unmet needs + competitive gaps + feature requests |
| **Technical Feasibility** | 5% | 0-100 | opportunity_scores | Build complexity + resource requirements + API availability |
| **Simplicity Score** | 20% | 0-100 | opportunity_scores | Function count penalty: 1 func=100, 2=85, 3=70, 4+=0 |

### Total Score Calculation

**Formula**:
```sql
total_score =
  (market_demand * 0.20) +
  (pain_intensity * 0.25) +
  (monetization_potential * 0.20) +
  (market_gap * 0.10) +
  (technical_feasibility * 0.05) +
  (simplicity_score * 0.20)
```

**Implementation**: Stored as GENERATED ALWAYS column in both:
- `opportunity_scores.total_score`
- `workflow_results.opportunity_assessment_score`

**Weights Total**: 1.00 (100%)

**Range**: 0-100 (higher is better)

**Disqualification Rule**: Apps with 4+ core functions automatically receive simplicity_score = 0, which caps total_score at 80.

---

## Trust Validation System

### Trust Indicators
The schema includes a comprehensive trust validation layer for opportunities:

| Column | Type | Values | Purpose |
|--------|------|--------|---------|
| trust_level | TEXT | VERY_HIGH, HIGH, MEDIUM, LOW, UNKNOWN | Overall trust tier |
| trust_score | DECIMAL(5,2) | 0-100 | Quantitative trust metric |
| trust_badge | TEXT | GOLD, SILVER, BRONZE, BASIC, NO-BADGE | Visual trust indicator |
| activity_score | DECIMAL(6,2) | 0+ | Community engagement metric |
| engagement_level | TEXT | VERY_HIGH, HIGH, MEDIUM, LOW, MINIMAL | Discussion quality tier |
| trend_velocity | DECIMAL(8,4) | -∞ to +∞ | Momentum indicator |
| problem_validity | TEXT | VALID, POTENTIAL, UNCLEAR, INVALID | Problem assessment |
| discussion_quality | TEXT | EXCELLENT, GOOD, FAIR, POOR | Conversation quality |
| ai_confidence_level | TEXT | VERY_HIGH, HIGH, MEDIUM, LOW | AI analysis confidence |

### Trust Data Sources
- Reddit engagement metrics (upvotes, comments, awards)
- Temporal patterns (first seen, last seen, trending score)
- Cross-platform validation (Twitter, LinkedIn, Product Hunt)
- Market validation results
- Competitive landscape analysis

---

## DLT Pipeline Integration

### Staging Schema: `public_staging`

DLT (Data Load Tool) uses a staging pattern for incremental loads:

| Table | Purpose | DLT Columns |
|-------|---------|-------------|
| `app_opportunities` | Staged opportunity data | _dlt_load_id, _dlt_id |
| `app_opportunities__core_functions` | Array flattening (child table) | _dlt_root_id, _dlt_parent_id, _dlt_list_idx |

### DLT Metadata Tables

| Table | Purpose |
|-------|---------|
| `_dlt_loads` | Track ETL batch status and schema versions |
| `_dlt_pipeline_state` | Store pipeline state snapshots for incremental processing |
| `_dlt_version` | Track schema version evolution |

### Child Table Pattern

Tables with `__` suffix (e.g., `app_opportunities__core_functions`) represent **DLT child tables** for array/nested data:
- `_dlt_root_id`: Links to parent record
- `_dlt_parent_id`: Immediate parent in nested structure
- `_dlt_list_idx`: Preserves array order (0-based index)
- `value`: Array element value

**Example**:
```json
// Source data
{
  "submission_id": "abc123",
  "core_functions": ["Track expenses", "Set budgets", "Generate reports"]
}

// Flattened to child table
app_opportunities__core_functions:
  _dlt_root_id | value                  | _dlt_list_idx
  abc123       | "Track expenses"       | 0
  abc123       | "Set budgets"          | 1
  abc123       | "Generate reports"     | 2
```

---

## Migration History

### Timeline

| Date | Migration Count | Phase | Focus |
|------|-----------------|-------|-------|
| 2025-11-04 | 4 | Foundation | Market validation, competitive analysis, indexes |
| 2025-11-08 to 2025-11-09 | 3 | Consolidation | Schema merge, DLT integration |
| 2025-11-10 to 2025-11-12 | 4 | Trust Layer | Credibility metrics, trust validation |
| 2025-11-13 to 2025-11-14 | 6 | Analytics | Cost tracking, customer leads, monetization |
| 2025-11-14 | 1 | Methodology | 6th dimension (simplicity score) |
| **Total** | **20** | **10 days** | **Complete schema** |

### Key Milestones

1. **2025-11-04**: Initial schema (Reddit data + validation tables)
2. **2025-11-08**: Major consolidation (DLT merge, data migration)
3. **2025-11-10**: Credibility layer (problem metrics, trust indicators)
4. **2025-11-13**: Cost tracking (LLM monitoring, analytics)
5. **2025-11-14**: Methodology completion (6-dimension scoring)

---

## Common Queries

### Top Opportunities by Score
```sql
SELECT
  o.id,
  o.app_name,
  o.problem_statement,
  os.total_score,
  os.market_demand_score,
  os.pain_intensity_score,
  os.simplicity_score
FROM opportunities o
JOIN opportunity_scores os ON o.id = os.opportunity_id
WHERE os.total_score > 70
ORDER BY os.total_score DESC
LIMIT 10;
```

### Opportunities with High Trust
```sql
SELECT
  ao.app_name,
  ao.trust_level,
  ao.trust_score,
  ao.trust_badge,
  ao.opportunity_score
FROM app_opportunities ao
WHERE ao.trust_level IN ('VERY_HIGH', 'HIGH')
  AND ao.trust_score > 80
ORDER BY ao.trust_score DESC;
```

### Trending Problems
```sql
SELECT
  s.title,
  pm.comment_count,
  pm.total_upvotes,
  pm.trending_score,
  pm.subreddit_spread,
  pm.last_seen
FROM problem_metrics pm
JOIN submissions s ON pm.problem_id = s.id
WHERE pm.trending_score > 0.5
ORDER BY pm.trending_score DESC
LIMIT 20;
```

### LLM Cost Summary
```sql
SELECT
  llm_model_used,
  llm_provider,
  COUNT(*) AS analysis_count,
  SUM(llm_prompt_tokens) AS total_prompt_tokens,
  SUM(llm_completion_tokens) AS total_completion_tokens,
  SUM(llm_total_cost) AS total_cost,
  AVG(llm_latency_ms) AS avg_latency_ms
FROM app_opportunities
WHERE llm_model_used IS NOT NULL
GROUP BY llm_model_used, llm_provider
ORDER BY total_cost DESC;
```

### Market Validation Coverage
```sql
SELECT
  o.app_name,
  COUNT(DISTINCT mv.validation_type) AS validation_types,
  COUNT(DISTINCT cpv.platform_name) AS platforms_verified,
  AVG(mv.confidence_score) AS avg_validation_confidence
FROM opportunities o
LEFT JOIN market_validations mv ON o.id = mv.opportunity_id
LEFT JOIN cross_platform_verification cpv ON o.id = cpv.opportunity_id
GROUP BY o.id, o.app_name
HAVING COUNT(DISTINCT mv.validation_type) > 2
ORDER BY validation_types DESC;
```

---

## Future Enhancements

### Planned Improvements
1. **Full-Text Search**: Add GIN indexes for title/content search
2. **Partitioning**: Partition submissions/comments by created_at (monthly)
3. **Materialized Views**: Pre-compute trending_problems for performance
4. **Audit Log**: Track all changes to opportunities table
5. **Schema Versioning**: Add version column to track schema evolution

### Data Quality
1. **Data Validation Functions**: Automated validation of score ranges
2. **Orphan Detection**: Identify orphaned records missing FKs
3. **Duplicate Detection**: Find duplicate submissions/opportunities
4. **PII Scanning**: Automated PII detection and anonymization

### Performance
1. **Query Optimization**: Analyze slow queries with EXPLAIN
2. **Index Tuning**: Review unused indexes, add missing indexes
3. **Connection Pooling**: Optimize database connection management
4. **Caching Layer**: Add Redis for frequently accessed data

---

## Troubleshooting

### Schema Drift
**Problem**: Working schema differs from migrations
**Solution**:
1. Generate fresh schema dump
2. Compare with migration-generated schema
3. Create fix migration for drift
4. Consider baseline consolidation

### Migration Failures
**Problem**: Migration fails to apply
**Solution**:
1. Check Supabase logs: `supabase status`
2. Review migration SQL for syntax errors
3. Verify dependencies (tables/columns referenced)
4. Test migration on fresh DB: `supabase db reset`

### DLT Conflicts
**Problem**: DLT recreates tables from migrations
**Solution**:
1. Exclude DLT tables from migrations
2. Use DLT schema versioning
3. Separate staging schema from production schema

### Performance Issues
**Problem**: Slow queries on large datasets
**Solution**:
1. Run EXPLAIN ANALYZE on slow queries
2. Check for missing indexes
3. Consider partitioning large tables
4. Review materialized view refresh strategy

---

## Resources

### Internal Documentation
- [ERD Diagram](./erd.md)
- [Migration Analysis](./migration-analysis.md)
- [Consolidation Plan](./consolidation-plan.md)

### External Resources
- [Supabase Documentation](https://supabase.com/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [DLT Documentation](https://dlthub.com/docs)
- [Mermaid ERD Syntax](https://mermaid.js.org/syntax/entityRelationshipDiagram.html)

### Tools
- [Supabase Studio](http://127.0.0.1:54323) - Local database UI
- [pgAdmin](https://www.pgadmin.org/) - PostgreSQL administration
- [Mermaid Live Editor](https://mermaid.live) - ERD visualization
- [DB Diagram](https://dbdiagram.io/) - Alternative ERD tool

---

## Changelog

### 2025-11-17
- Initial schema consolidation documentation
- Created comprehensive ERD diagram
- Completed migration analysis
- Drafted consolidation plan

### [session-progress-2025-11-17.md](./session-progress-2025-11-17.md)
**Schema Consolidation Session Progress**

Session log documenting the complete schema consolidation process including analysis, planning, and execution phases for RedditHarbor database schema optimization.

**Use this for**:
- Understanding consolidation timeline and progress
- Session reference for similar projects
- Progress tracking methodology

---

## Additional Test Results & Analysis

### [baseline_test_results.md](./baseline_test_results.md)
**Core Functions Format Testing Results**

Comprehensive test results documenting the core_functions serialization format inconsistency issue and validation of the fix implementation across different pipeline components.

**Use this for**:
- Understanding core_functions format problems
- Validating fix implementation
- Reference for format standardization testing

### [core-functions-fix-certification.md](./core-functions-fix-certification.md)
**Core Functions Fix Implementation Certification**

Complete certification documentation for the core_functions format fix, including testing procedures, validation results, and production readiness assessment.

**Use this for**:
- Production deployment certification
- Fix validation procedures
- Quality assurance documentation

### [core-functions-fix-summary.md](./core-functions-fix-summary.md)
**Core Functions Fix Implementation Summary**

Executive summary of the core_functions format fix implementation, including problem analysis, solution approach, and impact assessment on the RedditHarbor pipeline.

**Use this for**:
- Quick overview of fix implementation
- Executive summary for stakeholders
- Impact assessment documentation

---

## Contributing

### Adding New Tables
1. Create migration: `supabase migration new add_new_table`
2. Update ERD diagram in `erd.md`
3. Update migration analysis in `migration-analysis.md`
4. Run tests: `pytest tests/`
5. Commit migration + documentation together

### Modifying Existing Tables
1. Create migration: `supabase migration new modify_table_name`
2. Update ERD diagram if relationships change
3. Test on fresh DB: `supabase db reset`
4. Update common queries if needed
5. Document breaking changes in CHANGELOG.md

### Schema Consolidation
Follow the [consolidation-plan.md](./consolidation-plan.md) for periodic baseline refreshes.

---

## License

This documentation is part of the RedditHarbor project.
See [LICENSE](../../LICENSE) for details.

---

**Last Updated**: 2025-11-17
**Maintained By**: RedditHarbor Development Team
**Questions**: See project README or create GitHub issue
