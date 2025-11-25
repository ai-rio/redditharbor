# Test 02: Small Batch Scale Validation Prompt

**Date**: 2025-11-24
**Priority**: HIGH - Validate DLT pipeline fixes enable data collection scaling
**Duration**: 30-60 minutes
**Target**: Confirm DLT pipeline can collect and store Reddit data without primary key errors

---

## Executive Summary

### Primary Objective

Validate that the DLT pipeline primary key configuration fixes resolve the production blocker that was preventing data collection scaling. This test confirms the pipeline can successfully process and store Reddit submissions without attempting to insert into the non-existent `submission_id` column.

### Success Definition

- ✅ **Pipeline Stability**: 5/5 submissions processed without fatal DLT errors
- ✅ **Storage Success**: Data successfully stored in `app_opportunities` table using correct `id` primary key
- ✅ **Error Resolution**: No more "column submission_id does not exist" errors
- ✅ **Scalability Confirmation**: Pipeline ready for larger batch processing
- ✅ **Performance**: Processing completes within 30 minutes

---

## Pre-Test Validation Checklist

### Environment Requirements

Before executing this test, verify the following prerequisites:

1. **✅ DLT Fixes Applied**:
   - `core/dlt/constants.py` updated to use `PK_ID` for `app_opportunities`
   - `core/dlt/app_opportunities.py` updated with correct primary key
   - All primary key configurations point to `id` column (not `submission_id`)

2. **✅ Database Status**:
   - Supabase running locally: `supabase status` shows all services active
   - Database schema has `app_opportunities` table with `id` as primary key
   - Connection configured: `SUPABASE_URL` and `SUPABASE_KEY` environment variables set

3. **✅ Python Environment**:
   - Virtual environment activated: `source .venv/bin/activate`
   - Dependencies installed: `uv sync` completed successfully
   - Current working directory: project root

4. **✅ Reddit API Configuration**:
   - Reddit API credentials configured in environment
   - API rate limits understood and respected
   - Test data selection criteria defined

### Critical Validation Commands

Execute these commands to verify environment readiness:

```bash
# Verify Supabase is running
supabase status

# Verify database connection
psql postgresql://postgres:postgres@127.0.0.1:54322/postgres -c "SELECT COUNT(*) FROM app_opportunities;"

# Verify DLT configuration
python -c "
from core.dlt import PK_ID, DLT_RESOURCE_PK_MAP
print(f'PK_ID: {PK_ID}')
print(f'app_opportunities PK: {DLT_RESOURCE_PK_MAP.get(\"app_opportunities\", \"NOT FOUND\")}')
"
```

---

## Test Execution Plan

### Phase 1: Data Selection (10 minutes)

**Objective**: Select 5 diverse Reddit submissions for testing.

**Selection Strategy**:
- Query existing database for submissions with `score >= 20`
- Choose varied subreddits and post types
- Ensure submissions have sufficient content for enrichment

**Selection Query**:
```sql
SELECT id, title, score, num_comments, subreddit, selftext
FROM submissions
WHERE score >= 20
LIMIT 5;
```

**If no existing data**: Use Reddit API to collect 5 new submissions:
- Target subreddits: productivity, entrepreneurship, software, technology, business
- Minimum score threshold: 20
- Content requirement: > 100 characters

### Phase 2: Pipeline Execution (20-40 minutes)

**Objective**: Run the unified pipeline on selected submissions.

**Execution Steps**:

1. **Initialize Pipeline**:
```bash
cd /home/carlos/projects/redditharbor-core-functions-fix
source .venv/bin/activate
```

2. **Run Data Collection**:
```python
# Execute DLT pipeline
python -c "
import asyncio
from core.dlt.collection import main

async def run_test():
    try:
        print('Starting DLT pipeline execution...')
        result = await main()
        print(f'Pipeline completed: {result}')
    except Exception as e:
        print(f'Pipeline error: {e}')
        raise

asyncio.run(run_test())
"
```

3. **Monitor Progress**:
- Watch for DLT processing logs
- Monitor database insert operations
- Track any error messages or warnings

### Phase 3: Results Validation (10 minutes)

**Objective**: Verify successful processing and storage.

**Validation Queries**:

1. **Check Processing Count**:
```sql
SELECT COUNT(*) as processed_count
FROM app_opportunities
WHERE created_at >= NOW() - INTERVAL '1 hour';
```

2. **Verify Primary Key Usage**:
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'app_opportunities'
AND column_name = 'id';
```

3. **Check for Errors**:
```sql
-- Verify no new errors in recent operations
SELECT COUNT(*) as error_count
FROM app_opportunities
WHERE processing_status = 'ERROR';
```

---

## Success Criteria Validation

### Primary Success Metrics

1. **✅ Processing Success Rate**: 5/5 submissions processed (100% success)

2. **✅ Storage Verification**: All processed data stored in `app_opportunities` table

3. **✅ Primary Key Validation**: Data stored using `id` column (not `submission_id`)

4. **✅ Error-Free Execution**: No "column submission_id does not exist" errors

5. **✅ Performance**: Total execution time < 30 minutes

### Secondary Success Indicators

- **Consistent Data Quality**: All required fields populated correctly
- **DLT Logs Clean**: No schema mismatch warnings in DLT logs
- **Memory Usage**: Stable memory consumption during processing
- **API Rate Limiting**: Reddit API calls respect rate limits

---

## Error Handling and Troubleshooting

### Common Issues and Solutions

#### Issue 1: DLT Schema Errors
**Symptoms**: "Column submission_id does not exist" or similar schema errors
**Root Cause**: DLT configuration still referencing old primary key
**Solution**: Verify all DLT configuration files use `PK_ID` instead of `PK_SUBMISSION_ID`

#### Issue 2: Database Connection Failures
**Symptoms**: Connection refused, authentication errors
**Root Cause**: Supabase not running or incorrect credentials
**Solution**:
```bash
supabase start
export SUPABASE_URL=http://127.0.0.1:54330
export SUPABASE_KEY=your-service-role-key
```

#### Issue 3: Reddit API Rate Limiting
**Symptoms**: HTTP 429 errors, request throttling
**Root Cause**: Too many API calls in short time period
**Solution**: Implement delays between API calls, respect rate limits

#### Issue 4: Python Environment Issues
**Symptoms**: Import errors, missing dependencies
**Root Cause**: Virtual environment not activated or incomplete installation
**Solution**:
```bash
source .venv/bin/activate
uv sync
```

### Escalation Procedures

1. **Critical Failures**: Stop execution and document error conditions
2. **Partial Success**: Record which submissions failed and why
3. **Performance Issues**: Document execution times and bottlenecks

---

## Partner AI Instructions

### Required Deliverables

Create a comprehensive test report at:
`docs/plans/unified-pipeline-refactoring/testing/local-ai-report/test-02-small-batch-scale-validation-report.md`

### Report Structure (Following Existing Pattern)

```markdown
# Test 02: Small Batch Scale Validation Report

**Date**: [execution date]
**Status**: [SUCCESS/PARTIAL/FAILURE]
**Duration**: [total execution time]

## Executive Summary
[Brief overview of test results and key findings]

## Test Execution
### Environment Setup
[Details about environment validation and prerequisites]
### Data Selection
[Information about submissions selected for testing]
### Pipeline Execution
[Step-by-step execution details and observations]
### Results Validation
[Database query results and storage verification]

## Key Results
### Success Metrics
[Quantitative results with specific numbers]
### Error Analysis
[Any errors encountered and their resolution]
### Performance Metrics
[Timing data and resource usage]

## Conclusion
[Summary of whether the DLT pipeline fixes enable scaling]
## Recommendations
[Any follow-up actions or additional testing needed]
```

### Critical Information to Include

1. **Execution Environment**:
   - Exact commands run
   - Environment variable values
   - Database status at test start

2. **Processing Results**:
   - Number of submissions processed
   - Success/failure counts
   - Processing time per submission

3. **Database Validation**:
   - SQL queries executed
   - Results of validation checks
   - Record counts before/after

4. **Error Documentation**:
   - Any errors encountered (full error messages)
   - Troubleshooting steps taken
   - Resolution status

5. **Performance Metrics**:
   - Total execution time
   - Memory usage observations
   - API call rates

### Reporting Requirements

- **Honest Assessment**: Report actual results, not expected results
- **Detailed Logs**: Include relevant log outputs and error messages
- **Quantitative Data**: Use specific numbers and measurements
- **Visual Evidence**: Include console output screenshots where helpful
- **Clear Conclusion**: State definitively whether scaling is now possible

---

## Expected Outcome

### Success Scenario
If this test passes, it confirms that:
- The DLT pipeline primary key fixes are working correctly
- Data collection scaling is now unblocked
- The production blocker has been resolved
- Larger scale testing can proceed with confidence

### Failure Scenario
If this test fails, it indicates:
- Additional DLT configuration fixes are needed
- Further investigation into pipeline architecture required
- Production scaling remains blocked
- Root cause analysis and additional fixes required

---

## Timeline and Resources

**Estimated Total Time**: 30-60 minutes
**API Costs**: Minimal (Reddit API usage only)
**Resource Requirements**: Standard development environment
**Dependencies**: DLT fixes, Supabase, Reddit API access

---

**Ready for execution when all prerequisites are validated and environment is confirmed ready.**