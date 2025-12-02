# SQLAlchemy Schema Analysis Report

## Database Schema Investigation Results

### Critical Schema Mismatch Identified

The Phase 2 SQLAlchemy implementation is failing due to **major field mapping mismatches** between what the loader expects and what actually exists in the database.

### Actual Database Schema

**Table**: `app_opportunities` (34 columns)

**Key Findings**:
1. **DLT-specific columns exist**: `_dlt_load_id`, `_dlt_id` (both NOT NULL)
2. **Missing columns in loader**: Several expected columns don't exist
3. **Column name differences**: Some columns exist with different names
4. **Data type differences**: Some columns have different types than expected

### Schema Mismatch Details

| Expected by Loader | Actual in Database | Issue Type |
|-------------------|-------------------|------------|
| `text` | **DOES NOT EXIST** | Missing column |
| `upvotes` | `reddit_score` (bigint) | Wrong name |
| `comments_count` | **DOES NOT EXIST** | Missing column |
| `score` | **DOES NOT EXIST** | Missing column |
| `created_utc` | **DOES NOT EXIST** | Missing column |
| `quality_score` | **DOES NOT EXIST** | Missing column |
| `processed_at` | `analyzed_at` (timestamptz) | Wrong name |
| `pipeline_version` | `pipeline_source` (varchar) | Wrong name |

### Available Database Columns

**Core Identity Fields**:
- `submission_id` (varchar, NOT NULL) - Primary identifier
- `title` (varchar) - Reddit post title
- `subreddit` (varchar) - Reddit subreddit name
- `reddit_score` (bigint) - Reddit score (was `upvotes`)

**Opportunity Analysis Fields**:
- `problem_description` (varchar) - Problem statement
- `app_concept` (varchar) - App concept description
- `core_functions` (varchar) - Core app functions
- `opportunity_score` (double precision) - Opportunity score
- `monetization_score` (numeric) - Monetization potential

**Trust and Quality Fields**:
- `trust_score` (double precision) - Trust score
- `trust_level` (varchar) - Trust level
- `trust_badges` (jsonb) - Trust badges array
- `confidence` (numeric) - Confidence score

**Metadata Fields**:
- `analyzed_at` (timestamptz) - Analysis timestamp
- `pipeline_source` (varchar) - Pipeline identifier
- `enrichment_version` (varchar) - Processing version

**Required DLT Fields**:
- `_dlt_load_id` (varchar, NOT NULL) - DLT load identifier
- `_dlt_id` (varchar, NOT NULL) - DLT record identifier

### Critical Constraints

1. **NOT NULL Constraints**: `_dlt_load_id` and `_dlt_id` must be populated
2. **Data Types**: Numeric vs double precision differences
3. **JSON Fields**: `trust_badges`, `core_problems`, `dimension_scores`, `ai_profile` are JSONB

## Required Schema Alignment Strategy

### Phase 1: Field Mapping Corrections

Fix the `prepare_opportunity_data()` method to properly map incoming Reddit data to existing database columns:

```python
# MAPPING CORRECTIONS NEEDED:
'text' -> 'problem_description' (main Reddit post content)
'upvotes' -> 'reddit_score'
'comments_count' -> OMIT (no corresponding column)
'score' -> OMIT (no corresponding column)
'created_utc' -> OMIT (no corresponding column)
'quality_score' -> 'opportunity_score' (or calculate from available fields)
'processed_at' -> 'analyzed_at'
'pipeline_version' -> 'pipeline_source'
```

### Phase 2: SQL Statement Updates

Update all INSERT/UPDATE SQL statements to use correct column names and omit non-existent columns.

### Phase 3: Data Validation

Ensure all required fields are populated before database operations, especially DLT-specific NOT NULL fields.

## Business Impact

This schema mismatch is causing **silent data loss** because:
1. SQLAlchemy loader attempts to insert into non-existent columns
2. SQL errors are caught but not properly handled
3. LoadResult.success may return True even when data fails to persist
4. Business loses valuable Reddit opportunity data

## Immediate Actions Required

1. **Fix field mappings** in `prepare_opportunity_data()`
2. **Update SQL statements** to use actual column names
3. **Add comprehensive error handling** for schema mismatches
4. **Implement verification** to ensure data actually persists
5. **Test with actual Reddit data** to verify end-to-end functionality

## Success Criteria

- [ ] SQLAlchemy loader successfully loads test data without SQL errors
- [ ] All Reddit opportunity data fields are properly mapped to database columns
- [ ] LoadResult.success accurately reflects database state
- [ ] No silent failures - all errors are properly caught and reported
- [ ] Verification step confirms data persistence

---

**Generated**: 2025-11-27
**Priority**: CRITICAL - Blocking all Reddit data collection
**Impact**: Business cannot proceed with monetizable app idea database