# Migration Analysis: RedditHarbor Schema Evolution

## Overview

This document analyzes the 20 migration files (3,156 total lines) that evolved the RedditHarbor schema from initial setup to the current working state captured in `schema_dumps/dlt_trust_pipeline_success_schema_20251117_194348.sql`.

**Analysis Date**: 2025-11-17
**Working Schema**: `dlt_trust_pipeline_success_schema_20251117_194348.sql`
**Migration Count**: 20 SQL files
**Total Migration Lines**: 3,156 lines

---

## Migration Timeline

### Phase 1: Foundation (2025-11-04)
**Focus**: Core validation and analysis infrastructure

#### 1. `20251104190002_market_validation.sql` (3,773 bytes)
**Purpose**: Market validation and cross-platform verification
**Tables Created**:
- `market_validations`: Primary validation metrics for opportunities
  - Columns: validation_type, validation_source, confidence_score, status, evidence_url
  - Constraints: confidence_score range check (0.0-1.0)
  - FK: opportunity_id → opportunities(id) ON DELETE CASCADE
- `cross_platform_verification`: Multi-platform validation (Twitter, LinkedIn, Product Hunt, etc.)
  - Columns: platform_name, validation_status, data_points, confidence_score
  - Constraints: confidence_score range check (0.0-1.0)
  - FK: opportunity_id → opportunities(id) ON DELETE CASCADE

**Impact**: Established external validation layer for opportunities

#### 2. `20251104190003_competitive_analysis.sql` (3,870 bytes)
**Purpose**: Competitive landscape analysis
**Tables Created**:
- `competitive_landscape`: Market competition tracking
  - Columns: competitor_name, market_position, pricing_model, strengths, weaknesses, market_share_estimate
  - Constraints: market_share 0-100%, user_count >= 0
  - FK: opportunity_id → opportunities(id) ON DELETE CASCADE
- `feature_gaps`: Missing features in existing solutions
  - Columns: existing_solution, missing_feature, user_requests_count, priority_level, user_evidence
  - Constraints: priority_level enum (low, medium, high, critical)
  - FK: opportunity_id → opportunities(id) ON DELETE CASCADE

**Impact**: Added competitive intelligence capabilities

#### 3. `20251104190004_monetization_technical.sql` (6,247 bytes)
**Purpose**: Monetization models and technical feasibility
**Tables Created**:
- `monetization_patterns`: Revenue model tracking
  - Columns: model_type, price_range_min/max, revenue_estimate, market_segment, potential_users
  - Constraints: price/revenue >= 0, price_max >= price_min
  - FK: opportunity_id → opportunities(id) ON DELETE CASCADE
- `user_willingness_to_pay`: Payment intent signals from users
  - Columns: payment_mention_text, price_point, user_segment, confidence_score
  - FK: opportunity_id → opportunities(id), source_comment_id → comments(id) ON DELETE SET NULL
- `technical_assessments`: Feasibility analysis
  - Columns: api_integrations_required, development_complexity, estimated_timeline, feasibility_score
  - Constraints: complexity enum (low, medium, high, very_high), feasibility_score 0-100
  - FK: opportunity_id → opportunities(id) ON DELETE CASCADE

**Impact**: Enabled revenue forecasting and build complexity analysis

#### 4. `20251104190006_indexes_performance.sql` (10,176 bytes)
**Purpose**: Performance optimization via strategic indexing
**Indexes Created**: 40+ indexes across all tables
- Foreign key indexes for join performance
- Scoring/filtering indexes (opportunity_scores.total_score DESC)
- Timestamp indexes for temporal queries
- Composite indexes for common query patterns

**Impact**: Significant query performance improvements

---

### Phase 2: Schema Consolidation (2025-11-08 to 2025-11-09)
**Focus**: Data integrity and architecture cleanup

#### 5. `20251108000000_consolidate_schema_safe.sql` (17,097 bytes)
**Purpose**: Major schema consolidation addressing critical issues
**Critical Issues Fixed**:
1. NULL foreign keys in submissions (subreddit_id, redditor_id)
2. NULL foreign keys in comments (submission_id, redditor_id)
3. Duplicate columns from mixed DLT/schema sources
4. Missing columns that code expects
5. Data integrity and backwards compatibility

**Changes**:
- **Redditors Table**: Added redditor_id, is_gold, is_mod, trophy, karma, name, removed
- **Submissions Table**: Added submission_id, archived, removed, attachment, poll, flair, awards, score, upvote_ratio, num_comments, edited, text, subreddit, permalink
- **Comments Table**: Added link_id, comment_id, body, subreddit, parent_id, score, edited, removed
- **Opportunities Table**: Added opportunity_id, app_name, business_category, source_subreddit
- **Backfill Logic**: Migrated data from DLT tables to normalized schema
- **Indexes**: Added string ID lookups for Reddit API identifiers

**Impact**: Unified schema from disparate sources (DLT + manual migrations)

#### 6. `20251108000001_workflow_results_table.sql` (778 bytes)
**Purpose**: Track AI workflow processing
**Table Created**: `workflow_results`
- Columns: opportunity_id, app_name, function_count, original_score, final_score, status, constraint_applied, ai_insight
- Purpose: Store AI-driven opportunity processing results

**Impact**: Separated AI processing layer from core opportunity data

#### 7. `20251108000002_add_dimension_scores_to_workflow.sql` (1,906 bytes)
**Purpose**: Add multi-dimensional scoring to workflow_results
**Columns Added**:
- market_demand (0-100)
- pain_intensity (0-100)
- monetization_potential (0-100)
- market_gap (0-100)
- technical_feasibility (0-100)

**Constraints**: All scores 0-100 range checks

**Impact**: Aligned workflow_results with opportunity_scores methodology (5 of 6 dimensions)

---

### Phase 3: DLT Integration (2025-11-09)
**Focus**: DLT pipeline integration for automated data loading

#### 8. `20251109000001_create_app_opportunities_table.sql` (2,335 bytes)
**Purpose**: Store LLM-generated app ideas
**Table Created**: `app_opportunities` (public schema)
- Columns: submission_id, problem_description, app_concept, core_functions (jsonb), value_proposition, target_user, monetization_model, opportunity_score
- Status: discovered, validated, built, rejected
- Indexes: score, submission_id, status, created_at, subreddit

**View Created**: `top_opportunities` (score > 40 only)

**Impact**: Separate storage for AI-analyzed opportunities from workflows

#### 9. `20251109000002_add_dlt_columns_to_app_opportunities.sql` (601 bytes)
**Purpose**: Add DLT tracking metadata
**Columns Added**:
- _dlt_load_id (varchar)
- _dlt_id (varchar)

**Impact**: Enabled DLT pipeline integration for incremental loads

---

### Phase 4: Credibility & Trust Layers (2025-11-10 to 2025-11-12)
**Focus**: Trust validation and credibility indicators

#### 10. `20251110000001_add_function_list_to_workflow.sql` (2,813 bytes)
**Purpose**: Track individual core functions for transparency
**Column Added**: function_list (jsonb) to workflow_results
- Stores array of core function names
- Enables function-count bias detection and fixes

**Impact**: Improved transparency in simplicity scoring

#### 11. `20251110151231_add_problem_metrics_table.sql` (16,067 bytes)
**Purpose**: Credibility layer for opportunity validation
**Table Created**: `problem_metrics`
- Engagement: comment_count, total_upvotes
- Reach: subreddit_spread
- Momentum: trending_score
- Intent: intent_signal_count
- Temporal: first_seen, last_seen, updated_at
- FK: problem_id → submissions(id) ON DELETE CASCADE

**Views Created**:
- `problem_metrics_summary`: Aggregated engagement stats
- `trending_problems`: Hot problems sorted by trending_score
- `high_engagement_problems`: Most discussed problems

**Functions Created**:
- `calculate_trending_score()`: Compute momentum metric
- `update_problem_metrics()`: Aggregate metrics from submissions/comments

**Impact**: Added transparent validation signals for opportunities

#### 12. `20251111000001_add_llm_profiler_columns.sql` (1,963 bytes)
**Purpose**: Track LLM profiling metadata
**Columns Added to app_opportunities**:
- llm_model_used (varchar)
- llm_prompt_tokens (integer)
- llm_completion_tokens (integer)
- llm_total_cost (decimal)
- llm_profiling_timestamp (timestamptz)

**Impact**: Cost tracking and model transparency for AI processing

#### 13. `20251112000001_add_trust_layer_columns.sql` (2,551 bytes)
**Purpose**: Comprehensive trust validation layer
**Columns Added to app_opportunities**:
- **Trust Indicators**: trust_level (enum), trust_score (0-100), trust_badge (GOLD/SILVER/BRONZE/BASIC)
- **Engagement**: activity_score, engagement_level (enum), trend_velocity
- **Validation**: problem_validity (enum), discussion_quality (enum), ai_confidence_level (enum)
- **Metadata**: trust_factors (jsonb), trust_updated_at

**Indexes Created**: 6 indexes + 1 composite index for trust queries

**Impact**: Multi-dimensional trust assessment for opportunities

#### 14. `20251112000002_fix_trust_schema_compatibility.sql` (3,034 bytes)
**Purpose**: Fix trust column compatibility with DLT pipeline
**Changes**:
- Renamed trust_factors → trust_validation_data
- Added trust_validation_timestamp (double precision for Unix epoch)
- Added trust_validation_method (varchar)
- Added confidence_score (decimal 0-100)

**Impact**: Resolved DLT schema conflicts for trust data

---

### Phase 5: Cost Tracking & Analytics (2025-11-13 to 2025-11-14)
**Focus**: LLM cost monitoring and customer lead generation

#### 15. `20251113000001_add_cost_tracking_columns.sql` (3,478 bytes)
**Purpose**: Enhanced cost tracking for AI operations
**Columns Added**:
- llm_provider (varchar): 'openrouter', 'anthropic', 'openai'
- llm_latency_ms (integer): Response time tracking
- llm_error_count (integer): Failure tracking
- llm_retry_count (integer): Retry tracking

**Impact**: Comprehensive AI operation monitoring

#### 16. `20251113000002_fix_cost_tracking_views.sql` (11,570 bytes)
**Purpose**: Analytics views for cost analysis
**Views Created**:
- `llm_cost_summary`: Total costs by model/provider
- `llm_usage_by_day`: Daily usage trends
- `llm_error_analysis`: Error rates and patterns
- `llm_performance_metrics`: Latency and throughput

**Impact**: Cost visibility and optimization insights

#### 17. `20251114005544_fix_cost_tracking_functions.sql` (7,450 bytes)
**Purpose**: Automated cost calculation functions
**Functions Created**:
- `calculate_token_cost()`: Compute cost from tokens and model
- `update_opportunity_costs()`: Batch cost recalculation
- `get_cost_breakdown()`: Detailed cost analysis

**Impact**: Automated cost management

#### 18. `20251114200000_add_customer_leads_table.sql` (8,219 bytes)
**Purpose**: Track potential customers from Reddit discussions
**Table Created**: `customer_leads`
- Columns: submission_id, redditor_id, lead_score, pain_points, willingness_to_pay_signals, contact_feasibility, lead_status
- FK: submission_id → submissions(id), redditor_id → redditors(id)
- Constraints: lead_score 0-100, lead_status enum

**Impact**: Customer development and validation pipeline

#### 19. `20251114200001_add_llm_monetization_analysis.sql` (6,903 bytes)
**Purpose**: LLM-driven monetization insights
**Columns Added to monetization_patterns**:
- llm_analysis_text (text): AI-generated insights
- llm_confidence_score (decimal 0-1)
- llm_model_used (varchar)
- llm_analyzed_at (timestamptz)

**Impact**: AI-augmented revenue analysis

---

### Phase 6: Methodology Alignment (2025-11-14)
**Focus**: Complete 6-dimension scoring methodology

#### 20. `20251114232013_add_simplicity_score_and_assessment.sql` (9,726 bytes)
**Purpose**: Complete 6-dimension scoring system
**Critical Addition**: Missing 6th dimension - simplicity_score

**Methodology Weights**:
1. market_demand: 20%
2. pain_intensity: 25%
3. monetization_potential: 20%
4. market_gap: 10%
5. technical_feasibility: 5%
6. **simplicity_score: 20%** ← ADDED

**Changes to workflow_results**:
- Added simplicity_score (numeric 5,2, range 0-100)
- Backfilled from function_count: 1 func=100, 2=85, 3=70, 4+=0
- Added opportunity_assessment_score (GENERATED ALWAYS column)
- Formula: Sum of (dimension * weight) for all 6 dimensions

**Index Created**: idx_workflow_results_opportunity_assessment_score

**Impact**: Completed methodology alignment, single source of truth for opportunity scoring

---

## Schema Drift Analysis

### Missing from Working Schema vs Migrations

Based on comparison between `schema_dumps/dlt_trust_pipeline_success_schema_20251117_194348.sql` and migration files:

#### 1. Tables in Schema but NOT in Migrations
These tables were created outside the migration system (likely by DLT or Supabase):
- `_dlt_loads` (DLT metadata)
- `_dlt_pipeline_state` (DLT metadata)
- `_dlt_version` (DLT metadata)
- `_migrations_log` (manual tracking, not Supabase migrations)
- `app_opportunities__core_functions` (DLT child table for array flattening)
- All `public_staging.*` tables (DLT staging schema)
- All `auth.*` tables (Supabase authentication)
- All `_realtime.*` tables (Supabase realtime)
- All `realtime.*` tables (Supabase realtime partitions)
- All `storage.*` tables (Supabase storage, if present)

**Risk**: LOW - These are managed by external systems (Supabase, DLT)

#### 2. Columns in Schema but NOT in Migrations
Analysis shows migrations successfully captured all application columns. Any drift is from:
- DLT-managed columns (`_dlt_*` prefixes)
- Supabase system columns (auth, realtime schemas)

**Risk**: LOW - External system management

#### 3. Duplicate Column Definitions
Migration `20251108000000_consolidate_schema_safe.sql` explicitly addressed duplicates from DLT/schema merge. Current schema shows clean column definitions.

**Risk**: RESOLVED

---

## Migration Quality Assessment

### Strengths
1. **Comprehensive Comments**: All migrations include purpose, table descriptions, column comments
2. **Safety Measures**: Use of IF NOT EXISTS, ADD COLUMN IF NOT EXISTS for idempotency
3. **Data Integrity**: Extensive CHECK constraints for score ranges, enums, relationships
4. **Performance**: Strategic indexing throughout evolution
5. **Backfill Logic**: Migration 5 includes data migration from DLT to normalized schema
6. **Documentation**: Inline verification queries and rollback procedures

### Weaknesses
1. **Migration Count**: 20 files for relatively small schema (high overhead)
2. **Overlapping Concerns**: Some migrations modify same tables multiple times
3. **Trust Layer Fragmentation**: Trust columns added across 3 separate migrations (11, 13, 14)
4. **Cost Tracking Fragmentation**: Cost columns added across 3 migrations (12, 15, 16, 17)
5. **No Baseline**: No single "create all tables" migration at start
6. **DLT Dependency**: Schema relies on DLT-created tables not in migration system

---

## Migration Dependencies

### Hard Dependencies (FK Constraints)
```
opportunities → submissions (identified_from_submission_id)
submissions → subreddits (subreddit_id)
submissions → redditors (redditor_id)
comments → submissions (submission_id)
comments → redditors (redditor_id)
comments → comments (parent_comment_id)

opportunity_scores → opportunities (opportunity_id)
score_components → opportunities (opportunity_id)
market_validations → opportunities (opportunity_id)
competitive_landscape → opportunities (opportunity_id)
feature_gaps → opportunities (opportunity_id)
cross_platform_verification → opportunities (opportunity_id)
monetization_patterns → opportunities (opportunity_id)
technical_assessments → opportunities (opportunity_id)
user_willingness_to_pay → opportunities (opportunity_id)
user_willingness_to_pay → comments (source_comment_id)

problem_metrics → submissions (problem_id)
customer_leads → submissions (submission_id)
customer_leads → redditors (redditor_id)
```

### Soft Dependencies (Application Logic)
- `workflow_results` references opportunities via string `opportunity_id` (not FK)
- `app_opportunities` references submissions via string `submission_id` (not FK)
- DLT child tables reference parent via `_dlt_root_id` (DLT-managed)

---

## Recommendations

See [consolidation-plan.md](./consolidation-plan.md) for detailed consolidation strategy.

### Immediate Actions
1. **Verify working schema matches migrations**: Run migration verification queries
2. **Document DLT table dependencies**: Map DLT tables to application usage
3. **Test migration rollback**: Ensure migrations are reversible

### Future Improvements
1. **Consolidate migrations**: Reduce 20 files to 3-5 logical groupings
2. **Baseline migration**: Create single "initial schema" migration
3. **Separate DLT schema**: Isolate DLT tables from application schema
4. **Migration testing**: Add automated migration validation

---

## Migration File Summary Table

| # | File | Date | Size | Tables | Purpose |
|---|------|------|------|--------|---------|
| 1 | 20251104190002_market_validation.sql | 2025-11-04 | 3.7KB | 2 | Market validation tables |
| 2 | 20251104190003_competitive_analysis.sql | 2025-11-04 | 3.9KB | 2 | Competitive analysis |
| 3 | 20251104190004_monetization_technical.sql | 2025-11-04 | 6.2KB | 3 | Monetization & technical |
| 4 | 20251104190006_indexes_performance.sql | 2025-11-04 | 10KB | 0 | Performance indexes |
| 5 | 20251108000000_consolidate_schema_safe.sql | 2025-11-08 | 17KB | 0 | Schema consolidation |
| 6 | 20251108000001_workflow_results_table.sql | 2025-11-08 | 778B | 1 | Workflow tracking |
| 7 | 20251108000002_add_dimension_scores_to_workflow.sql | 2025-11-08 | 1.9KB | 0 | Dimension scores |
| 8 | 20251109000001_create_app_opportunities_table.sql | 2025-11-09 | 2.3KB | 1 | App opportunities |
| 9 | 20251109000002_add_dlt_columns_to_app_opportunities.sql | 2025-11-09 | 601B | 0 | DLT metadata |
| 10 | 20251110000001_add_function_list_to_workflow.sql | 2025-11-10 | 2.8KB | 0 | Function tracking |
| 11 | 20251110151231_add_problem_metrics_table.sql | 2025-11-10 | 16KB | 1 | Problem metrics |
| 12 | 20251111000001_add_llm_profiler_columns.sql | 2025-11-11 | 2.0KB | 0 | LLM cost tracking |
| 13 | 20251112000001_add_trust_layer_columns.sql | 2025-11-12 | 2.6KB | 0 | Trust validation |
| 14 | 20251112000002_fix_trust_schema_compatibility.sql | 2025-11-12 | 3.0KB | 0 | Trust schema fixes |
| 15 | 20251113000001_add_cost_tracking_columns.sql | 2025-11-13 | 3.5KB | 0 | Enhanced cost tracking |
| 16 | 20251113000002_fix_cost_tracking_views.sql | 2025-11-13 | 12KB | 0 | Cost analytics views |
| 17 | 20251114005544_fix_cost_tracking_functions.sql | 2025-11-14 | 7.5KB | 0 | Cost functions |
| 18 | 20251114200000_add_customer_leads_table.sql | 2025-11-14 | 8.2KB | 1 | Customer leads |
| 19 | 20251114200001_add_llm_monetization_analysis.sql | 2025-11-14 | 6.9KB | 0 | LLM monetization |
| 20 | 20251114232013_add_simplicity_score_and_assessment.sql | 2025-11-14 | 9.7KB | 0 | Methodology completion |

**Total**: 20 files, ~108KB, 3,156 lines

---

## Related Documentation

- [ERD Diagram](./erd.md) - Complete entity relationship diagram
- [Consolidation Plan](./consolidation-plan.md) - Migration consolidation strategy
- [README](./README.md) - Schema consolidation overview
