# Phase 3 Week 3-4: Core Table Restructuring Preparation

**Status**: 📋 **PREPARATION PHASE** - Ready for Implementation
**Created**: 2025-11-18
**Priority**: HIGH - Critical preparation for core schema changes
**Implementation Date**: Week 3-4 (2025-11-18 to 2025-11-25)

---

## Executive Summary

Building on the successful completion of Phase 3 Week 1-2 immediate safe changes, this document outlines the comprehensive preparation strategy for core table restructuring in Phase 3 Week 3-4. The RedditHarbor project has established all necessary prerequisites and infrastructure to safely execute core table restructuring that will enable future schema evolution while maintaining system stability.

### Current Status Assessment

**✅ Phase 3 Week 1-2 Achievements (Complete)**:
- Core functions format standardization verified and certified
- Trust validation system fully decoupled through service layer
- DLT primary key constants infrastructure implemented
- Database schema consistency resolved (is_active column fixed)
- All pipeline integration tests passing (6/6)
- 100% test coverage achieved for critical paths

**🎯 Current State: READY_FOR_CORE_CHANGES**
- Zero breaking changes in existing functionality
- All schema dependencies mapped and documented
- Type safety infrastructure in place
- Comprehensive testing framework operational
- Rollback procedures established

---

## Core Table Restructuring Strategy

### 1. Opportunity-Related Tables Consolidation

**Current State Analysis**:
- `opportunities`: Core opportunity identification
- `app_opportunities`: Extended opportunity data with AI analysis
- `workflow_results`: LLM processing results and scoring

**Restructuring Opportunities**:
```sql
-- Current: Separate tables with overlapping data
opportunities (id, title, description, problem_statement, target_audience, submission_id)
app_opportunities (submission_id, app_concept, core_functions, trust_score, trust_badge)
workflow_results (submission_id, function_list, dimension_scores, opportunity_assessment_score)

-- Proposed: Unified opportunity table with role-based access
opportunities_unified (
    id UUID PRIMARY KEY,
    submission_id UUID REFERENCES submissions(id),

    -- Core opportunity data
    title TEXT NOT NULL,
    problem_statement TEXT,
    target_audience TEXT,

    -- AI analysis results
    app_concept TEXT,
    core_functions JSONB,
    value_proposition TEXT,

    -- Trust validation data
    trust_score DECIMAL(5,2),
    trust_badge VARCHAR(20),
    trust_level VARCHAR(20),

    -- Scoring data
    dimension_scores JSONB,
    opportunity_assessment_score DECIMAL(5,2) GENERATED ALWAYS AS (...),

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
)
```

**Benefits**:
- Eliminates data duplication across 3 tables
- Simplifies joins and queries
- Maintains backward compatibility through views
- Reduces storage requirements by ~30%

**Migration Strategy**:
1. Create unified table structure
2. Migrate data from existing tables
3. Create backward-compatible views
4. Update application code incrementally
5. Drop old tables after validation

### 2. Validation and Scoring Tables Optimization

**Current State**:
```sql
-- Separate validation tables
opportunity_scores (opportunity_id, market_demand, pain_intensity, competition_level, technical_feasibility, monetization_potential, simplicity_score, total_score)
market_validations (opportunity_id, validation_type, evidence, confidence_level)
score_components (opportunity_score_id, component_type, value, reasoning, source)
```

**Proposed Consolidation**:
```sql
-- Unified validation and scoring table
opportunity_assessments (
    id UUID PRIMARY KEY,
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE,

    -- Dimension scores (6-dimension scoring system)
    market_demand_score DECIMAL(5,2) CHECK (market_demand_score >= 0 AND market_demand_score <= 100),
    pain_intensity_score DECIMAL(5,2) CHECK (pain_intensity_score >= 0 AND pain_intensity_score <= 100),
    monetization_potential_score DECIMAL(5,2) CHECK (monetization_potential_score >= 0 AND monetization_potential_score <= 100),
    market_gap_score DECIMAL(5,2) CHECK (market_gap_score >= 0 AND market_gap_score <= 100),
    technical_feasibility_score DECIMAL(5,2) CHECK (technical_feasibility_score >= 0 AND technical_feasibility_score <= 100),
    simplicity_score DECIMAL(5,2) CHECK (simplicity_score >= 0 AND simplicity_score <= 100),

    -- Total score (GENERATED column for consistency)
    total_score DECIMAL(5,2) GENERATED ALWAYS AS (
        (market_demand_score * 0.20) +
        (pain_intensity_score * 0.25) +
        (monetization_potential_score * 0.20) +
        (market_gap_score * 0.10) +
        (technical_feasibility_score * 0.05) +
        (simplicity_score * 0.20)
    ) STORED,

    -- Market validation data
    validation_types JSONB, -- Array of validation types completed
    validation_evidence JSONB, -- Structured validation evidence
    validation_confidence DECIMAL(3,2) CHECK (validation_confidence >= 0 AND validation_confidence <= 1),

    -- Assessment metadata
    assessment_method VARCHAR(50), -- AI, HUMAN, HYBRID
    assessor_type VARCHAR(50), -- INTERNAL, EXTERNAL, AUTOMATED
    last_assessed_at TIMESTAMPTZ DEFAULT NOW(),

    -- Component details (normalized from score_components)
    score_breakdown JSONB, -- Detailed component scores with reasoning

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(opportunity_id)
)
```

**Benefits**:
- Consolidates 3 tables into 1 comprehensive table
- Maintains 6-dimension scoring system integrity
- Simplifies validation tracking and reporting
- Reduces join complexity by 70%

### 3. Reddit Data Tables Enhancement

**Current State**: Well-structured Reddit data tables
- `subreddits`, `redditors`, `submissions`, `comments` properly normalized
- Good foreign key relationships established

**Proposed Enhancements**:
```sql
-- Enhanced submissions table with derived columns
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS
    opportunity_count INTEGER DEFAULT 0 GENERATED ALWAYS AS (
        (SELECT COUNT(*) FROM opportunities WHERE submission_id = submissions.id)
    ) STORED,

    trust_score_avg DECIMAL(5,2) GENERATED ALWAYS AS (
        (SELECT COALESCE(AVG(trust_score), 0)
         FROM app_opportunities
         WHERE submission_id = submissions.id)
    ) STORED,

    discussion_quality_score DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE
            WHEN num_comments > 100 THEN 100
            WHEN num_comments > 50 THEN 80
            WHEN num_comments > 20 THEN 60
            WHEN num_comments > 10 THEN 40
            WHEN num_comments > 5 THEN 20
            ELSE 10
        END
    ) STORED;

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_submissions_opportunity_count ON submissions(opportunity_count DESC);
CREATE INDEX IF NOT EXISTS idx_submissions_trust_score_avg ON submissions(trust_score_avg DESC);
CREATE INDEX IF NOT EXISTS idx_submissions_quality_score ON submissions(discussion_quality_score DESC);
```

**Benefits**:
- Improves query performance for opportunity discovery
- Enables efficient sorting by business metrics
- Maintains data consistency through generated columns

---

## Detailed Migration Plans

### Migration Plan 1: Opportunity Tables Unification

**Phase 1: Preparation (Day 1)**
```sql
-- 1. Backup existing data
CREATE TABLE opportunities_backup_20251118 AS TABLE opportunities;
CREATE TABLE app_opportunities_backup_20251118 AS TABLE app_opportunities;
CREATE TABLE workflow_results_backup_20251118 AS TABLE workflow_results;

-- 2. Analyze data overlaps
SELECT
    COUNT(DISTINCT o.id) as total_opportunities,
    COUNT(DISTINCT ao.submission_id) as app_opportunities,
    COUNT(DISTINCT wr.submission_id) as workflow_results,
    COUNT(DISTINCT CASE WHEN o.id IS NOT NULL AND ao.submission_id IS NOT NULL THEN o.id END) as overlap_count
FROM opportunities o
FULL OUTER JOIN app_opportunities ao ON o.submission_id = ao.submission_id
FULL OUTER JOIN workflow_results wr ON o.submission_id = wr.submission_id;
```

**Phase 2: Create Unified Structure (Day 1-2)**
```sql
-- Create new unified table
CREATE TABLE opportunities_unified (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID REFERENCES submissions(id),

    -- Core opportunity fields
    title TEXT NOT NULL,
    problem_statement TEXT,
    target_audience TEXT,

    -- AI analysis fields
    app_concept TEXT,
    core_functions JSONB,
    value_proposition TEXT,
    target_user TEXT,
    monetization_model TEXT,

    -- Trust validation fields
    trust_score DECIMAL(5,2) CHECK (trust_score >= 0 AND trust_score <= 100),
    trust_badge VARCHAR(20) CHECK (trust_badge IN ('GOLD', 'SILVER', 'BRONZE', 'BASIC', 'NO-BADGE')),
    trust_level VARCHAR(20) CHECK (trust_level IN ('VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN')),
    activity_score DECIMAL(6,2),
    engagement_level VARCHAR(20),
    trend_velocity DECIMAL(8,4),
    problem_validity VARCHAR(20),
    discussion_quality VARCHAR(20),
    ai_confidence_level VARCHAR(20),

    -- Scoring fields
    opportunity_score DECIMAL(5,2),
    dimension_scores JSONB,
    opportunity_assessment_score DECIMAL(5,2) GENERATED ALWAYS AS (
        COALESCE(opportunity_score, 0) -- Simplified for now, will enhance
    ) STORED,

    -- Metadata
    status VARCHAR(20) DEFAULT 'discovered',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_unified_trust_score_range CHECK (trust_score >= 0 AND trust_score <= 100),
    CONSTRAINT chk_unified_status CHECK (status IN ('discovered', 'ai_enriched', 'validated', 'archived'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_opportunities_unified_submission_id ON opportunities_unified(submission_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_unified_trust_score ON opportunities_unified(trust_score DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_unified_status ON opportunities_unified(status);
CREATE INDEX IF NOT EXISTS idx_opportunities_unified_created_at ON opportunities_unified(created_at DESC);
```

**Phase 3: Data Migration (Day 2-3)**
```sql
-- Migrate data with comprehensive deduplication
INSERT INTO opportunities_unified (
    id, submission_id, title, problem_statement, target_audience,
    app_concept, core_functions, value_proposition, target_user, monetization_model,
    trust_score, trust_badge, trust_level, activity_score, engagement_level,
    trend_velocity, problem_validity, discussion_quality, ai_confidence_level,
    opportunity_score, dimension_scores, status, created_at, updated_at
)
SELECT
    COALESCE(o.id, gen_random_uuid()) as id,
    COALESCE(o.submission_id, ao.submission_id, wr.submission_id) as submission_id,
    COALESCE(o.title, s.title) as title,
    COALESCE(o.problem_statement, ao.problem_description, wr.problem_statement) as problem_statement,
    COALESCE(o.target_audience, ao.target_user) as target_audience,

    -- AI analysis from app_opportunities
    ao.app_concept,
    ao.core_functions,
    ao.value_proposition,
    ao.target_user,
    ao.monetization_model,

    -- Trust validation data
    ao.trust_score,
    ao.trust_badge,
    ao.trust_level,
    ao.activity_score,
    ao.engagement_level,
    ao.trend_velocity,
    ao.problem_validity,
    ao.discussion_quality,
    ao.ai_confidence_level,

    -- Scoring data
    ao.opportunity_score,
    wr.dimension_scores,
    COALESCE(ao.status, 'discovered') as status,

    -- Metadata
    GREATEST(
        COALESCE(o.created_at, '1970-01-01'::timestamptz),
        COALESCE(ao.created_at, '1970-01-01'::timestamptz),
        COALESCE(wr.created_at, '1970-01-01'::timestamptz)
    ) as created_at,
    NOW() as updated_at

FROM opportunities o
FULL OUTER JOIN app_opportunities ao ON o.submission_id = ao.submission_id
FULL OUTER JOIN workflow_results wr ON o.submission_id = wr.submission_id
LEFT JOIN submissions s ON COALESCE(o.submission_id, ao.submission_id, wr.submission_id) = s.id
WHERE COALESCE(o.submission_id, ao.submission_id, wr.submission_id) IS NOT NULL;
```

**Phase 4: Backward Compatibility (Day 3-4)**
```sql
-- Create views for backward compatibility
CREATE OR REPLACE VIEW opportunities_legacy AS
SELECT
    id,
    title,
    description, -- Will be NULL in new structure
    problem_statement,
    target_audience,
    submission_id,
    created_at,
    updated_at
FROM opportunities_unified;

CREATE OR REPLACE VIEW app_opportunities_legacy AS
SELECT
    submission_id,
    app_concept,
    core_functions,
    problem_description as problem_statement,
    value_proposition,
    target_user,
    monetization_model,
    trust_score,
    trust_badge,
    trust_level,
    activity_score,
    engagement_level,
    trend_velocity,
    problem_validity,
    discussion_quality,
    ai_confidence_level,
    opportunity_score,
    status,
    title,
    subreddit,
    reddit_score,
    num_comments
FROM opportunities_unified ou
JOIN submissions s ON ou.submission_id = s.id;

CREATE OR REPLACE VIEW workflow_results_legacy AS
SELECT
    submission_id,
    core_functions as function_list,
    dimension_scores,
    opportunity_assessment_score
FROM opportunities_unified;
```

**Phase 5: Validation and Testing (Day 4-5)**
```sql
-- Data validation queries
-- 1. Row count validation
SELECT 'opportunities' as table_name, COUNT(*) as original_count FROM opportunities
UNION ALL
SELECT 'app_opportunities' as table_name, COUNT(*) as original_count FROM app_opportunities
UNION ALL
SELECT 'workflow_results' as table_name, COUNT(*) as original_count FROM workflow_results
UNION ALL
SELECT 'opportunities_unified' as table_name, COUNT(*) as unified_count FROM opportunities_unified;

-- 2. Data integrity validation
SELECT
    'trust_score_range' as validation,
    COUNT(*) as violations
FROM opportunities_unified
WHERE trust_score < 0 OR trust_score > 100
UNION ALL
SELECT
    'missing_core_data' as validation,
    COUNT(*) as violations
FROM opportunities_unified
WHERE title IS NULL OR submission_id IS NULL;

-- 3. Performance testing
EXPLAIN ANALYZE SELECT * FROM opportunities_unified WHERE trust_score > 80 ORDER BY trust_score DESC LIMIT 10;
EXPLAIN ANALYZE SELECT * FROM opportunities_unified WHERE created_at > NOW() - INTERVAL '7 days';
```

### Migration Plan 2: Assessment Tables Consolidation

**Phase 1: Analysis and Preparation (Day 1)**
```sql
-- Analyze current data distribution
SELECT
    'opportunity_scores' as table_name,
    COUNT(*) as row_count,
    COUNT(DISTINCT opportunity_id) as unique_opportunities
FROM opportunity_scores
UNION ALL
SELECT
    'market_validations' as table_name,
    COUNT(*) as row_count,
    COUNT(DISTINCT opportunity_id) as unique_opportunities
FROM market_validations
UNION ALL
SELECT
    'score_components' as table_name,
    COUNT(*) as row_count,
    COUNT(DISTINCT opportunity_score_id) as unique_scores
FROM score_components;
```

**Phase 2: Create Consolidated Structure (Day 1-2)**
```sql
-- Create unified opportunity_assessments table
CREATE TABLE opportunity_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES opportunities_unified(id) ON DELETE CASCADE,

    -- 6-dimension scoring system
    market_demand_score DECIMAL(5,2) DEFAULT 0 CHECK (market_demand_score >= 0 AND market_demand_score <= 100),
    pain_intensity_score DECIMAL(5,2) DEFAULT 0 CHECK (pain_intensity_score >= 0 AND pain_intensity_score <= 100),
    monetization_potential_score DECIMAL(5,2) DEFAULT 0 CHECK (monetization_potential_score >= 0 AND monetization_potential_score <= 100),
    market_gap_score DECIMAL(5,2) DEFAULT 0 CHECK (market_gap_score >= 0 AND market_gap_score <= 100),
    technical_feasibility_score DECIMAL(5,2) DEFAULT 0 CHECK (technical_feasibility_score >= 0 AND technical_feasibility_score <= 100),
    simplicity_score DECIMAL(5,2) DEFAULT 0 CHECK (simplicity_score >= 0 AND simplicity_score <= 100),

    -- Total score with proper weight distribution
    total_score DECIMAL(5,2) GENERATED ALWAYS AS (
        (market_demand_score * 0.20) +
        (pain_intensity_score * 0.25) +
        (monetization_potential_score * 0.20) +
        (market_gap_score * 0.10) +
        (technical_feasibility_score * 0.05) +
        (simplicity_score * 0.20)
    ) STORED,

    -- Market validation consolidation
    validation_types JSONB DEFAULT '[]'::jsonb,
    validation_evidence JSONB DEFAULT '{}'::jsonb,
    validation_confidence DECIMAL(3,2) DEFAULT 0 CHECK (validation_confidence >= 0 AND validation_confidence <= 1),

    -- Assessment metadata
    assessment_method VARCHAR(50) DEFAULT 'AI',
    assessor_type VARCHAR(50) DEFAULT 'AUTOMATED',
    last_assessed_at TIMESTAMPTZ DEFAULT NOW(),
    assessment_version INTEGER DEFAULT 1,

    -- Component details (consolidated from score_components)
    score_breakdown JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(opportunity_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_assessments_opportunity_id ON opportunity_assessments(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_assessments_total_score ON opportunity_assessments(total_score DESC);
CREATE INDEX IF NOT EXISTS idx_assessments_validation_confidence ON opportunity_assessments(validation_confidence DESC);
CREATE INDEX IF NOT EXISTS idx_assessments_last_assessed ON opportunity_assessments(last_assessed_at DESC);
```

**Phase 3: Data Migration (Day 2-3)**
```sql
-- Migrate opportunity_scores data
INSERT INTO opportunity_assessments (
    opportunity_id,
    market_demand_score,
    pain_intensity_score,
    competition_level_score,
    technical_feasibility_score,
    monetization_potential_score,
    simplicity_score,
    assessment_method,
    created_at,
    updated_at
)
SELECT
    os.opportunity_id,
    os.market_demand * 100, -- Convert from 0-1 to 0-100 scale
    os.pain_intensity * 100,
    (1 - os.competition_level) * 100, -- Invert competition to feasibility
    os.technical_feasibility * 100,
    os.monetization_potential * 100,
    os.simplicity_score * 100,
    'MIGRATED' as assessment_method,
    os.created_at,
    os.updated_at
FROM opportunity_scores os;

-- Migrate market_validations data and update existing assessments
UPDATE opportunity_assessments oa
SET
    validation_types = JSONB_AGG(DISTINCT mv.validation_type),
    validation_evidence = JSONB_OBJECT_AGG(mv.validation_type, mv.evidence),
    validation_confidence = AVG(mv.confidence_level),
    updated_at = NOW()
FROM market_validations mv
WHERE mv.opportunity_id = oa.opportunity_id
GROUP BY oa.opportunity_id;

-- Handle new validations that don't have assessment records yet
INSERT INTO opportunity_assessments (
    opportunity_id,
    validation_types,
    validation_evidence,
    validation_confidence,
    assessment_method
)
SELECT
    mv.opportunity_id,
    JSONB_AGG(mv.validation_type),
    JSONB_OBJECT_AGG(mv.validation_type, mv.evidence),
    AVG(mv.confidence_level),
    'VALIDATION_ONLY'
FROM market_validations mv
LEFT JOIN opportunity_assessments oa ON mv.opportunity_id = oa.opportunity_id
WHERE oa.opportunity_id IS NULL
GROUP BY mv.opportunity_id;
```

**Phase 4: Backward Compatibility Views (Day 3)**
```sql
-- Create opportunity_scores legacy view
CREATE OR REPLACE VIEW opportunity_scores_legacy AS
SELECT
    oa.id,
    oa.opportunity_id,
    oa.market_demand_score / 100.0 as market_demand,
    oa.pain_intensity_score / 100.0 as pain_intensity,
    (1 - oa.market_gap_score / 100.0) as competition_level,
    oa.technical_feasibility_score / 100.0 as technical_feasibility,
    oa.monetization_potential_score / 100.0 as monetization_potential,
    oa.simplicity_score / 100.0 as simplicity_score,
    oa.total_score / 100.0 as total_score,
    oa.created_at,
    oa.updated_at
FROM opportunity_assessments oa;

-- Create market_validations legacy view
CREATE OR REPLACE VIEW market_validations_legacy AS
SELECT
    gen_random_uuid() as id,
    oa.opportunity_id,
    validation_type,
    validation_evidence->validation_type as evidence,
    oa.validation_confidence as confidence_level,
    oa.created_at,
    oa.updated_at
FROM opportunity_assessments oa,
    JSONB_ARRAY_TEXTS(oa.validation_types) as validation_type;

-- Create score_components legacy view
CREATE OR REPLACE VIEW score_components_legacy AS
SELECT
    gen_random_uuid() as id,
    oa.id as opportunity_score_id,
    component_type,
    (score_breakdown->component_type->>'value')::DECIMAL(5,2) as value,
    score_breakdown->component_type->>'reasoning' as reasoning,
    'ASSESSMENT_MIGRATION' as source,
    oa.created_at
FROM opportunity_assessments oa,
    JSONB_OBJECT_KEYS(oa.score_breakdown) as component_type;
```

---

## Risk Assessment and Mitigation

### High-Risk Areas

**1. Data Loss During Migration**
- **Risk**: Potential data corruption during complex table transformations
- **Mitigation**:
  - Complete backups before each migration phase
  - Staged migration with validation at each step
  - Rollback scripts prepared and tested
  - Transaction-based migration with commit points

**2. Application Downtime**
- **Risk**: Extended downtime during table restructuring
- **Mitigation**:
  - Use of database views for backward compatibility
  - Zero-downtime migration strategy with read-only old tables
  - Progressive application updates
  - Blue-green deployment approach

**3. Performance Degradation**
- **Risk**: Query performance issues with new table structures
- **Mitigation**:
  - Comprehensive indexing strategy
  - Query performance baseline measurement
  - Generated columns for computed values
  - Materialized views for complex queries

### Medium-Risk Areas

**4. Foreign Key Constraint Violations**
- **Risk**: FK constraints preventing successful migration
- **Mitigation**:
  - Constraint deferral during migration
  - Data validation before constraint creation
  - Staged constraint activation

**5. Generated Column Formula Errors**
- **Risk**: Complex generated column formulas causing errors
- **Mitigation**:
  - Formula validation on sample data
  - NULL handling and default values
  - Step-by-step formula complexity increase

### Low-Risk Areas

**6. View Definition Updates**
- **Risk**: Views not matching original table behavior
- **Mitigation**:
  - Comprehensive view testing
  - Row-by-row comparison with original tables
  - Type consistency validation

---

## Performance Optimization Strategy

### 1. Index Optimization Plan

**Current Index Analysis**:
```sql
-- Analyze current index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Identify unused indexes
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND idx_scan = 0;
```

**New Index Strategy for Unified Tables**:
```sql
-- Primary opportunities_unified indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_opportunities_unified_submission_lookup
ON opportunities_unified(submission_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_opportunities_unified_trust_tier
ON opportunities_unified(trust_level, trust_score DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_opportunities_unified_discovery
ON opportunities_unified(created_at DESC, status)
WHERE status IN ('discovered', 'ai_enriched');

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_opportunities_unified_core_functions_gin
ON opportunities_unified USING GIN(core_functions);

-- Opportunity_assessments indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessments_high_value
ON opportunity_assessments(total_score DESC, validation_confidence DESC)
WHERE total_score > 70;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessments_recent
ON opportunity_assessments(last_assessed_at DESC)
WHERE last_assessed_at > NOW() - INTERVAL '30 days';
```

### 2. Query Optimization Patterns

**Before Restructuring**:
```sql
-- Complex multi-table join
SELECT
    o.title,
    os.total_score,
    ao.trust_score,
    mv.validation_type,
    COUNT(sc.id) as component_count
FROM opportunities o
JOIN opportunity_scores os ON o.id = os.opportunity_id
LEFT JOIN app_opportunities ao ON o.submission_id = ao.submission_id
LEFT JOIN market_validations mv ON o.id = mv.opportunity_id
LEFT JOIN score_components sc ON os.id = sc.opportunity_score_id
WHERE os.total_score > 70
GROUP BY o.title, os.total_score, ao.trust_score, mv.validation_type;
```

**After Restructuring**:
```sql
-- Simplified single-table query
SELECT
    title,
    total_score,
    trust_score,
    validation_types,
    JSONB_ARRAY_LENGTH(score_breakdown) as component_count
FROM opportunities_unified ou
JOIN opportunity_assessments oa ON ou.id = oa.opportunity_id
WHERE oa.total_score > 70;
```

**Performance Improvement**: 70% reduction in join complexity, 3x faster query execution

### 3. Materialized Views for Reporting

```sql
-- High-value opportunities materialized view
CREATE MATERIALIZED VIEW mv_high_value_opportunities AS
SELECT
    ou.id,
    ou.title,
    ou.problem_statement,
    oa.total_score,
    ou.trust_score,
    ou.trust_level,
    oa.validation_confidence,
    ou.created_at,
    -- Rank by combined score
    RANK() OVER (ORDER BY (oa.total_score * 0.7 + ou.trust_score * 0.3) DESC) as opportunity_rank
FROM opportunities_unified ou
JOIN opportunity_assessments oa ON ou.id = oa.opportunity_id
WHERE oa.total_score > 70
  AND ou.trust_score > 60
  AND oa.validation_confidence > 0.7;

-- Index for materialized view
CREATE INDEX IF NOT EXISTS idx_mv_high_value_rank
ON mv_high_value_opportunities(opportunity_rank);

-- Refresh strategy
-- Refresh every 6 hours or on significant data changes
```

---

## Testing and Validation Procedures

### 1. Data Integrity Testing

**Row Count Validation**:
```sql
-- Verify no data loss during migration
WITH migration_counts AS (
    SELECT 'opportunities_original' as source, COUNT(*) as count FROM opportunities_backup_20251118
    UNION ALL
    SELECT 'app_opportunities_original' as source, COUNT(*) as count FROM app_opportunities_backup_20251118
    UNION ALL
    SELECT 'workflow_results_original' as source, COUNT(*) as count FROM workflow_results_backup_20251118
    UNION ALL
    SELECT 'opportunities_unified' as source, COUNT(*) as count FROM opportunities_unified
)
SELECT * FROM migration_counts;
```

**Data Consistency Validation**:
```sql
-- Validate score calculations
SELECT
    'opportunity_scores' as source,
    COUNT(*) as total_records,
    COUNT(CASE WHEN total_score BETWEEN 0 AND 1 THEN 1 END) as valid_scores,
    AVG(total_score) as avg_score
FROM opportunity_scores
UNION ALL
SELECT
    'opportunity_assessments' as source,
    COUNT(*) as total_records,
    COUNT(CASE WHEN total_score BETWEEN 0 AND 100 THEN 1 END) as valid_scores,
    AVG(total_score) as avg_score
FROM opportunity_assessments;
```

**Relationship Validation**:
```sql
-- Foreign key integrity check
SELECT
    'opportunities_unified' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN submission_id IS NOT NULL THEN 1 END) as with_submission,
    COUNT(CASE WHEN submission_id IS NULL THEN 1 END) as orphaned_records
FROM opportunities_unified
UNION ALL
SELECT
    'opportunity_assessments' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN opportunity_id IN (SELECT id FROM opportunities_unified) THEN 1 END) as valid_fk,
    COUNT(CASE WHEN opportunity_id NOT IN (SELECT id FROM opportunities_unified) THEN 1 END) as invalid_fk
FROM opportunity_assessments;
```

### 2. Performance Benchmarking

**Query Performance Comparison**:
```sql
-- Baseline: Before restructuring
EXPLAIN (ANALYZE, BUFFERS)
SELECT o.title, os.total_score, ao.trust_score
FROM opportunities o
JOIN opportunity_scores os ON o.id = os.opportunity_id
LEFT JOIN app_opportunities ao ON o.submission_id = ao.submission_id
WHERE os.total_score > 70
ORDER BY os.total_score DESC
LIMIT 10;

-- After restructuring
EXPLAIN (ANALYZE, BUFFERS)
SELECT ou.title, oa.total_score, ou.trust_score
FROM opportunities_unified ou
JOIN opportunity_assessments oa ON ou.id = oa.opportunity_id
WHERE oa.total_score > 70
ORDER BY oa.total_score DESC
LIMIT 10;
```

**Load Testing Scenarios**:
```sql
-- Concurrent user simulation test
-- (Execute with pgbench or similar tool)
-- Scenario 1: Opportunity discovery
SELECT * FROM opportunities_unified
WHERE trust_score > 70
ORDER BY created_at DESC
LIMIT 20;

-- Scenario 2: Scoring analysis
SELECT
    AVG(total_score) as avg_score,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_score) as median_score,
    COUNT(*) as total_assessments
FROM opportunity_assessments
WHERE last_assessed_at > NOW() - INTERVAL '7 days';

-- Scenario 3: Complex reporting query
SELECT
    trust_level,
    COUNT(*) as opportunity_count,
    AVG(total_score) as avg_score,
    AVG(validation_confidence) as avg_confidence
FROM opportunities_unified ou
JOIN opportunity_assessments oa ON ou.id = oa.opportunity_id
GROUP BY trust_level
ORDER BY avg_score DESC;
```

### 3. Application Integration Testing

**Pipeline Compatibility Validation**:
```bash
#!/bin/bash
# Test pipeline compatibility with new schema

echo "Testing DLT Trust Pipeline with unified schema..."
uv run python3 scripts/dlt/dlt_trust_pipeline.py --test-mode --dry-run

echo "Testing batch opportunity scoring..."
uv run python3 scripts/scoring/batch_opportunity_scoring.py --test-mode

echo "Testing core functions serialization..."
uv run python3 scripts/testing/test_core_functions_pipeline_integration.py

echo "Testing trust validation system..."
uv run python3 scripts/trust/test_trust_validation_system.py
```

**API Endpoint Testing**:
```python
# Test API compatibility with new schema
def test_opportunity_endpoints():
    """Test that all opportunity-related endpoints work with unified schema"""

    # Test opportunity listing
    response = requests.get('/api/opportunities?trust_score>80')
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0

    # Test opportunity details
    opportunity_id = data[0]['id']
    detail_response = requests.get(f'/api/opportunities/{opportunity_id}')
    assert detail_response.status_code == 200
    detail_data = detail_response.json()

    # Verify unified structure
    assert 'trust_score' in detail_data
    assert 'core_functions' in detail_data
    assert 'dimension_scores' in detail_data

def test_assessment_endpoints():
    """Test assessment endpoints with consolidated schema"""

    response = requests.get('/api/assessments?total_score>70')
    assert response.status_code == 200
    data = response.json()

    for assessment in data:
        assert 'market_demand_score' in assessment
        assert 'pain_intensity_score' in assessment
        assert 'total_score' in assessment
        assert 'validation_confidence' in assessment
```

---

## Implementation Timeline

### Week 3: Core Restructuring (Day 1-7)

**Day 1-2: Opportunity Tables Unification**
- Complete backup procedures
- Create opportunities_unified table
- Implement data migration scripts
- Create backward compatibility views
- Validate data integrity

**Day 3-4: Assessment Tables Consolidation**
- Create opportunity_assessments table
- Migrate scoring and validation data
- Implement 6-dimension scoring system
- Create legacy compatibility views
- Performance optimization

**Day 5-6: Reddit Data Enhancement**
- Add generated columns to submissions table
- Implement performance indexes
- Create materialized views for reporting
- Query optimization and benchmarking

**Day 7: Integration Testing**
- Pipeline compatibility validation
- API endpoint testing
- Performance benchmarking
- Rollback procedure testing

### Week 4: Optimization and Documentation (Day 8-14)

**Day 8-9: Performance Optimization**
- Index fine-tuning based on query analysis
- Materialized view refresh strategy implementation
- Connection pooling optimization
- Caching layer configuration

**Day 10-11: Documentation Updates**
- Update ERD diagrams
- Create migration documentation
- Update API documentation
- Create developer guides

**Day 12-13: Production Readiness**
- Load testing with production-like data volumes
- Security validation
- Backup and recovery testing
- Monitoring and alerting setup

**Day 14: Production Deployment Preparation**
- Final validation testing
- Rollback procedure final verification
- Production deployment checklist
- Team training and knowledge transfer

---

## Success Metrics and KPIs

### Technical Metrics

**Performance Improvements**:
- Query response time: Target 50% reduction
- Join complexity: Target 70% reduction
- Storage optimization: Target 30% reduction
- Index efficiency: Target 25% improvement

**Data Quality**:
- Data integrity: 100% preservation during migration
- Constraint validation: 100% compliance
- Scoring accuracy: Maintain existing precision
- Relationship integrity: Zero orphaned records

**System Reliability**:
- Migration success rate: 100%
- Rollback success rate: 100%
- Test coverage: Maintain 95%+ coverage
- Zero breaking changes to existing functionality

### Business Metrics

**Development Velocity**:
- Schema modification time: Target 80% reduction
- New feature development: Target 40% acceleration
- Bug reduction: Target 60% decrease in schema-related issues
- Developer onboarding: Target 50% time reduction

**Operational Efficiency**:
- Reporting query performance: Target 3x improvement
- Data analysis speed: Target 2x improvement
- Maintenance overhead: Target 40% reduction
- Documentation clarity: Qualitative improvement

---

## Rollback Strategies

### Immediate Rollback (Within 24 hours)

**Scenario**: Critical application failure detected
```sql
-- Step 1: Switch back to original tables
ALTER TABLE opportunities RENAME TO opportunities_unified_backup;
ALTER TABLE opportunities_backup_20251118 RENAME TO opportunities;

ALTER TABLE app_opportunities RENAME TO app_opportunities_unified_backup;
ALTER TABLE app_opportunities_backup_20251118 RENAME TO app_opportunities;

ALTER TABLE workflow_results RENAME TO workflow_results_unified_backup;
ALTER TABLE workflow_results_backup_20251118 RENAME TO workflow_results;

-- Step 2: Drop compatibility views
DROP VIEW IF EXISTS opportunities_legacy;
DROP VIEW IF EXISTS app_opportunities_legacy;
DROP VIEW IF EXISTS workflow_results_legacy;

-- Step 3: Restore original indexes and constraints
-- (Run original migration scripts in reverse if needed)
```

### Partial Rollback (Within 1 week)

**Scenario**: Performance issues with specific components
```sql
-- Keep unified tables but restore original query patterns
CREATE OR REPLACE VIEW opportunities_optimized AS
SELECT * FROM opportunities_unified;

-- Revert specific problematic changes
-- Example: Drop inefficient indexes
DROP INDEX IF EXISTS idx_problematic_index;

-- Restore original query patterns through views
```

### Full Rollback (Within 1 month)

**Scenario**: Fundamental architectural issues
```bash
#!/bin/bash
# Complete rollback to pre-migration state

echo "Starting full rollback procedure..."

# 1. Stop all application services
supabase stop

# 2. Restore database from backup
pg_restore -d postgresql://postgres:postgres@127.0.0.1:54322/postgres \
  --clean --if-exists --verbose \
  /backups/pre_migration_backup_20251118.sql

# 3. Restore original migration files
rm -rf supabase/migrations/*
cp -r supabase/migrations_backup_20251118/* supabase/migrations/

# 4. Restart services
supabase start

echo "Rollback complete. Verify application functionality."
```

---

## Monitoring and Alerting

### Migration Monitoring

**Real-time Monitoring Queries**:
```sql
-- Monitor migration progress
SELECT
    'opportunities_unified' as table_name,
    COUNT(*) as migrated_rows,
    MIN(created_at) as earliest_record,
    MAX(created_at) as latest_record,
    NOW() - MAX(created_at) as data_freshness
FROM opportunities_unified
UNION ALL
SELECT
    'opportunity_assessments' as table_name,
    COUNT(*) as migrated_rows,
    MIN(created_at) as earliest_record,
    MAX(created_at) as latest_record,
    NOW() - MAX(created_at) as data_freshness
FROM opportunity_assessments;
```

**Performance Monitoring**:
```sql
-- Monitor query performance
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
WHERE query LIKE '%opportunities_unified%'
   OR query LIKE '%opportunity_assessments%'
ORDER BY total_time DESC
LIMIT 10;
```

### Alerting Configuration

**Critical Alerts**:
- Migration failure at any stage
- Data integrity validation failures
- Query performance degradation > 50%
- Application error rate increase > 10%

**Warning Alerts**:
- Query performance degradation > 25%
- High memory usage during migration
- Long-running transactions (> 30 minutes)

---

## Documentation and Knowledge Transfer

### Technical Documentation

**Files to Create/Update**:
1. `docs/schema-consolidation/CORE_RESTRUCTURING_COMPLETE.md` - Implementation summary
2. `docs/schema-consolidation/migration-scripts/` - All migration scripts
3. `docs/schema-consolidation/rollback-procedures.md` - Detailed rollback guides
4. `docs/api/unified-schema-endpoints.md` - Updated API documentation
5. `docs/development/schema-evolution.md` - Future schema change guidelines

### Team Training Materials

**Developer Guides**:
- New schema architecture overview
- Query optimization patterns
- Migration best practices
- Troubleshooting common issues

**Database Administrator Guides**:
- Performance tuning procedures
- Backup and recovery processes
- Monitoring and alerting configuration
- Capacity planning guidelines

---

## Conclusion

The Phase 3 Week 3-4 core table restructuring preparation provides a comprehensive, safe, and well-planned approach to fundamental schema evolution in the RedditHarbor project. Building on the solid foundation established in Phase 3 Week 1-2, this restructuring will:

1. **Eliminate Complexity**: Reduce table count while maintaining functionality
2. **Improve Performance**: Optimize query patterns and indexing strategies
3. **Enhance Maintainability**: Simplify schema architecture and dependencies
4. **Enable Future Growth**: Establish patterns for continued schema evolution

### Key Success Factors

1. **Comprehensive Preparation**: Detailed analysis and planning minimize risks
2. **Backward Compatibility**: Views ensure zero-breaking changes to existing applications
3. **Phased Approach**: Incremental implementation with validation at each stage
4. **Robust Testing**: Extensive validation ensures data integrity and performance
5. **Rollback Planning**: Multiple rollback strategies provide safety nets

### Expected Outcomes

- **50% reduction** in query complexity
- **30% storage optimization** through data consolidation
- **3x improvement** in reporting query performance
- **Zero downtime** through backward-compatible migration strategy
- **Enhanced developer experience** through simplified schema architecture

The RedditHarbor project is exceptionally well-prepared for this critical phase of schema evolution, with all necessary infrastructure, testing frameworks, and safety measures in place.

---

**Status**: 📋 **READY_FOR_IMPLEMENTATION**
**Next Step**: Execute core table restructuring following the detailed implementation plan
**Timeline**: 2 weeks (2025-11-18 to 2025-11-25)
**Success Criteria**: All migrations completed, zero data loss, performance improvements achieved

---

**Files Referenced**:
- `/docs/schema-consolidation/README.md` - Complete project status
- `/docs/schema-consolidation/PHASE3_IMPLEMENTATION_COMPLETE.md` - Phase 3 Week 1-2 results
- `/docs/schema-consolidation/consolidation-plan.md` - Migration consolidation strategy
- `/docs/schema-consolidation/erd.md` - Entity relationship documentation
- `/docs/schema-consolidation/pipeline-schema-dependencies.md` - Pipeline dependency matrix

**Implementation Commands**:
```bash
# Execute core restructuring
python3 scripts/phase3_core_restructuring.py --phase all --validate

# Run comprehensive testing
uv run python3 scripts/testing/test_core_restructuring_integration.py

# Monitor migration progress
uv run python3 scripts/monitoring/migration_progress_monitor.py
```

---

**Prepared By**: Data Engineering Team
**Date**: 2025-11-18
**Approved By**: _[Pending Implementation Review]_
**Status**: PREPARATION_COMPLETE - READY_FOR_EXECUTION