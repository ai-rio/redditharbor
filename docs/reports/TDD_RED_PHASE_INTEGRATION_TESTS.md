# TDD RED Phase - Database Pipeline Integration Tests

## Overview

This document describes the RED phase integration tests for the OpportunityPipeline database integration. These tests document the expected behavior and will FAIL due to known schema mismatches between the code expectations and database reality.

## Test File Location

- **Test File**: `/home/carlos/projects/redditharbor-core-functions-fix/tests/test_pipeline_database_integration.py`
- **Runner Script**: `/home/carlos/projects/redditharbor-core-functions-fix/run_integration_red_phase_tests.py`

## Current State (VALIDATED)

### What Works ✓
- 4 submissions stored in database (table: `submissions`)
- Data collection works: `core/reddit/supabase_collection.py`
- Supabase connection works

### What's Broken ✗
- `OpportunityPipeline` cannot read from database
- `DatabaseFetcher` expects wrong table and columns
- Processing fails due to schema/table mismatches

## Known Failures (from 8 background processes)

1. **Table mismatch**: Code expects `app_opportunities`, database has `submissions`
2. **Column mismatch**: Code expects `submission_id`, database has `id` and `reddit_id`
3. **Serialization error**: `ResolutionResult` object not JSON serializable

## Database Schema (Actual)

```sql
-- submissions table (actual schema in database)
CREATE TABLE submissions (
    id UUID PRIMARY KEY,              -- Database primary key
    reddit_id TEXT,                   -- Reddit's native submission ID (e.g., "t3_abc123")
    title TEXT NOT NULL,
    content TEXT,
    score INTEGER,
    num_comments INTEGER,
    subreddit_id UUID REFERENCES subreddits(id),
    redditor_id UUID REFERENCES redditors(id),
    url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Code Expectations (Wrong)

```python
# DatabaseFetcher (core/fetchers/database_fetcher.py)
# Line 99: Hardcoded table name
self.table_name = self.config.get("table_name", "app_opportunities")  # ❌ Wrong!

# Line 154-165: Hardcoded column names
query = (
    self.client.table(self.table_name)
    .select(
        "submission_id, title, content, subreddit, reddit_score, "  # ❌ Wrong!
        "num_comments, trust_score, trust_level, created_utc, author, selftext"
    )
    .limit(limit)
)
```

## Test Suite Structure

### 1. Basic Fetch Tests

**Test**: `test_pipeline_can_fetch_from_submissions_table`

Documents that pipeline should be able to:
- Configure DATABASE source
- Fetch submissions without enrichment
- Return correct count of fetched records

**Expected Failure**: DatabaseFetcher tries to query `app_opportunities` table with wrong columns.

### 2. Schema Validation Tests

**Test**: `test_pipeline_fetches_correct_schema_fields`

Documents that fetched submissions should have:
- `id` field (could be UUID or reddit_id)
- `title`, `text`, `subreddit` fields
- `engagement` dictionary with upvotes and comments

**Expected Failure**: Column name mismatches cause KeyError or missing fields.

### 3. Enrichment Tests

**Test**: `test_pipeline_with_minimal_enrichment`

Documents complete pipeline flow:
- Fetch from database
- Apply profiler enrichment
- Track statistics correctly

**Expected Failure**: Can't fetch due to schema mismatch, or ResolutionResult serialization fails.

### 4. Error Reporting Tests

**Test**: `test_pipeline_error_reporting`

Documents that pipeline should:
- Report errors with descriptive messages
- Track error counts in stats
- Mention schema issues in error messages

**Expected Failure**: May succeed in reporting errors, but should capture schema-related error messages.

### 5. Configuration Tests

**Test**: `test_database_fetcher_orm_mode`

Documents DatabaseFetcher ORM mode:
- Support `use_orm` config option
- Support `table_name` configuration
- Support `id_field` configuration
- Use dynamic schema introspection

**Expected Failure**: DatabaseFetcher doesn't support these config options yet.

## Running the Tests

### Quick Run
```bash
python run_integration_red_phase_tests.py
```

### Direct pytest
```bash
pytest tests/test_pipeline_database_integration.py -v --tb=short
```

### Run with print output
```bash
pytest tests/test_pipeline_database_integration.py -v --tb=short -s
```

## Expected Output (RED Phase)

```
================================ test session starts =================================
collected 5 items

tests/test_pipeline_database_integration.py::TestPipelineDatabaseIntegration::test_pipeline_can_fetch_from_submissions_table XFAIL
tests/test_pipeline_database_integration.py::TestPipelineDatabaseIntegration::test_pipeline_fetches_correct_schema_fields XFAIL
tests/test_pipeline_database_integration.py::TestPipelineDatabaseIntegration::test_pipeline_with_minimal_enrichment XFAIL
tests/test_pipeline_database_integration.py::TestPipelineDatabaseIntegration::test_pipeline_error_reporting XFAIL
tests/test_pipeline_database_integration.py::TestDatabaseFetcherConfiguration::test_database_fetcher_orm_mode XFAIL

========================= 5 xfailed in 2.34s =====================================
```

## Root Cause Analysis

The tests will fail due to these core issues:

### 1. Hardcoded Schema Assumptions
```python
# DatabaseFetcher line 154-165
.select("submission_id, title, content, subreddit, reddit_score, ...")
#        ^^^^^^^^^^^^^ - Doesn't exist!
#                                        ^^^^^^^ - Wrong name!
```

**Reality**: Database has `id` (UUID), `reddit_id` (text), `score` (not reddit_score)

### 2. Missing ORM Integration
```python
# DatabaseFetcher doesn't support:
config = {
    'use_orm': True,          # ❌ Not implemented
    'table_name': 'submissions',  # ✓ Supported but defaults to wrong table
    'id_field': 'id'          # ❌ Not implemented
}
```

### 3. Formatter Field Mapping
```python
# formatters.py expects these fields:
submission.get("submission_id")  # ❌ Doesn't exist in DB
submission.get("reddit_score")   # ❌ Should be "score"
submission.get("problem_description")  # ❌ Should be "content"
```

## Green Phase Requirements

To make these tests pass, we need:

1. **ORM Mode in DatabaseFetcher**
   - Add SQLAlchemy integration (`core/db/`)
   - Support dynamic schema introspection
   - Use ORM models instead of hardcoded REST queries

2. **Configurable Field Mapping**
   - Support `id_field` configuration
   - Support `table_name` configuration
   - Support `use_orm` mode flag

3. **Dynamic Formatter**
   - Detect available fields dynamically
   - Map database columns to expected schema
   - Handle both old and new schemas

4. **Pipeline Configuration**
   - Update `OpportunityPipeline._create_fetcher()` to pass correct config
   - Support ORM mode in pipeline config
   - Handle schema variations gracefully

## Test Dependencies

### Required Environment Variables
```bash
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_key
# OR
SUPABASE_KEY=your_supabase_key
```

### Required Test Data
The tests expect at least 4 submissions in the `submissions` table. This was already created by the collection script.

### Python Dependencies
- pytest
- supabase-py
- SQLAlchemy (for ORM mode - not yet implemented)

## Success Criteria

The RED phase is successful when:
1. ✓ All tests FAIL with expected errors
2. ✓ Error messages clearly indicate schema mismatches
3. ✓ Tests document the expected behavior clearly
4. ✓ Tests are well-organized and maintainable

## Next Steps (GREEN Phase)

After RED phase validation:

1. Implement SQLAlchemy ORM models (`core/db/models.py`)
2. Add ORM session management (`core/db/session.py`)
3. Update DatabaseFetcher to support ORM mode
4. Update formatters for dynamic field mapping
5. Run tests again to verify GREEN phase
6. Add integration with OpportunityPipeline

## Related Files

- **Integration Tests**: `tests/test_pipeline_database_integration.py`
- **ORM Tests**: `tests/test_submissions_orm.py` (existing RED phase tests)
- **Database Fetcher**: `core/fetchers/database_fetcher.py`
- **Formatters**: `core/fetchers/formatters.py`
- **Pipeline Orchestrator**: `core/pipeline/orchestrator.py`
- **Test Runner**: `run_integration_red_phase_tests.py`

## References

- TDD RED-GREEN-REFACTOR cycle
- SQLAlchemy ORM documentation
- Supabase Python client documentation
- RedditHarbor ORM Integration Plan: `REDDITHARBOR_ORM_INTEGRATION.md`
