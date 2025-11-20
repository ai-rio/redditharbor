# Test 01: Single Submission Validation - Local AI Testing Prompt

**Date**: 2025-11-20
**Test**: Test 01 - Single Submission Validation
**File**: `scripts/testing/integration/tests/test_01_single_submission.py`
**Purpose**: Validate unified OpportunityPipeline executes all AI services and populates enrichment fields

---

## Pre-Testing Checklist

Before running the test, verify the following:

- [ ] **Supabase Running**: `supabase status` shows all services running
- [ ] **Database Has Data**: `psql $DATABASE_URL -c "SELECT COUNT(*) FROM submission WHERE reddit_score >= 50 AND num_comments >= 10;"` returns > 0
- [ ] **Environment Variables Set** (`.env.local`):
  - [ ] `SUPABASE_URL`
  - [ ] `SUPABASE_KEY`
  - [ ] `OPENROUTER_API_KEY` (for ProfilerService and MonetizationService)
  - [ ] `JINA_API_KEY` (for MarketValidationService)
  - [ ] `AGENTOPS_API_KEY` (optional, for observability)
- [ ] **Virtual Environment Activated**: `which python` shows project venv
- [ ] **Dependencies Installed**: All core dependencies available

---

## Test Overview

### Goal
Prove that the unified OpportunityPipeline can successfully process a single high-quality submission through ALL AI services and populate all expected enrichment fields.

### Services to Validate
1. **ProfilerService**: AI profiling using Claude Haiku via OpenRouter (~$0.005/call)
2. **OpportunityService**: 5-dimensional opportunity scoring (rule-based, no cost)
3. **MonetizationService**: Agno multi-agent monetization analysis (~$0.10/call)
4. **TrustService**: 6-dimensional trust validation (rule-based, no cost)
5. **MarketValidationService**: Real market data validation using Jina AI (~$0.05/call)

### Success Criteria
- [ ] All 5 services execute successfully
- [ ] All 30+ enrichment fields populated (90%+ field coverage)
- [ ] Processing time: 15-30 seconds
- [ ] Total cost: $0.10-$0.20
- [ ] No unhandled exceptions
- [ ] Data stored in database correctly
- [ ] AgentOps session created (if enabled)
- [ ] LiteLLM costs tracked (if enabled)

---

## Test Execution

### Step 1: Select Test Submission (5 minutes)

**Task**: Find a high-quality submission from the database

```bash
# Navigate to project root
cd /home/user/redditharbor

# Query database for suitable submission
psql $DATABASE_URL -c "SELECT submission_id, title, subreddit, reddit_score, num_comments, LENGTH(selftext) as text_length FROM submission WHERE reddit_score >= 50 AND num_comments >= 10 AND selftext IS NOT NULL AND LENGTH(selftext) >= 200 ORDER BY reddit_score DESC LIMIT 5;"
```

**Expected Output**: List of 5 high-quality submissions

**Action**: Select the highest-scoring submission and note its `submission_id`

**Update Configuration**:
```bash
# Edit submissions_single.json
nano scripts/testing/integration/config/submissions_single.json

# Replace "REPLACE_WITH_ACTUAL_ID" with actual submission_id
# Also fill in title, subreddit, reddit_score, num_comments from query
```

### Step 2: Verify Service Configuration (5 minutes)

**Task**: Ensure all services are enabled in configuration

```bash
# Check service_config.json
cat scripts/testing/integration/config/service_config.json | jq '.services | to_entries | map({service: .key, enabled: .value.enabled})'
```

**Expected Output**: All 5 services should show `"enabled": true`

If any service is disabled, edit `config/service_config.json` and set `enabled: true`

### Step 3: Run Test 01 (10-15 minutes)

**Task**: Execute the test script

```bash
# Run test with verbose logging
python scripts/testing/integration/tests/test_01_single_submission.py --verbose
```

**Monitor Output** for:
- Pipeline initialization success
- Each service execution status
- Field coverage percentage
- Cost breakdown
- Success/failure indicators

**Expected Output** (sample):
```
================================================================================
TEST 01: SINGLE SUBMISSION VALIDATION
================================================================================

Goal: Validate all AI services execute and populate enrichment fields

Services to test:
  1. ProfilerService (AI profiling via Claude Haiku)
  2. OpportunityService (5-dimensional scoring)
  3. MonetizationService (Agno multi-agent analysis)
  4. TrustService (6-dimensional trust validation)
  5. MarketValidationService (Real market data via Jina AI)

Testing with submission: abc123xyz

Initializing unified OpportunityPipeline...
  - Data Source: DATABASE
  - Limit: 1 submission
  - All Services: ENABLED

✓ Pipeline initialized successfully
  - Services loaded: 5

Running pipeline...
--------------------------------------------------------------------------------
[Service execution logs...]
--------------------------------------------------------------------------------

✓ Pipeline completed in 22.5s

Analyzing results...

✓ Submission enriched successfully
  - Fields populated: 28/30+
  - Field coverage: 93.3%

Service Execution Results:
--------------------------------------------------------------------------------
profiler             ✓ SUCCESS      Cost: $0.0050
opportunity          ✓ SUCCESS      Cost: $0.0000
monetization         ✓ SUCCESS      Cost: $0.1000
trust                ✓ SUCCESS      Cost: $0.0000
market_validation    ✓ SUCCESS      Cost: $0.0500
--------------------------------------------------------------------------------
Total Estimated Cost: $0.1550

[Console report with detailed metrics...]

✓ Results saved to: scripts/testing/integration/results/test_01_single_submission/run_2025-11-20_10-30-00.json

================================================================================
✅ TEST 01 PASSED - Single submission validation successful
================================================================================
```

### Step 4: Verify Results (5 minutes)

**Task**: Check test results and database

**1. Check JSON Report**:
```bash
# Find latest result file
LATEST_RESULT=$(ls -t scripts/testing/integration/results/test_01_single_submission/run_*.json | head -1)

# View result
cat $LATEST_RESULT | jq '{
  success_rate: .success_rate,
  avg_field_coverage: .avg_field_coverage,
  total_cost: .total_cost,
  services: .service_success_rates
}'
```

**Expected**:
- `success_rate`: 100
- `avg_field_coverage`: >= 90
- `total_cost`: 0.10-0.20
- All services: 100% success rate

**2. Check Database**:
```bash
# Verify enriched data was stored
psql $DATABASE_URL -c "SELECT submission_id, opportunity_score, final_score, profession, trust_level, monetization_score, market_validation_score FROM app_opportunities WHERE submission_id = 'YOUR_SUBMISSION_ID' LIMIT 1;"
```

**Expected**: Row exists with populated enrichment fields

**3. Check Observability** (if enabled):
```bash
# Check AgentOps traces
ls -lt scripts/testing/integration/observability/agentops_traces/

# Check LiteLLM logs
ls -lt scripts/testing/integration/observability/litellm_logs/

# Check Agno traces
ls -lt scripts/testing/integration/observability/agno_traces/
```

**Expected**: Trace files created with timestamp matching test run

---

## Issues to Watch For

### Issue 1: Submission Selection Fails
**Symptom**: "No submissions found in database" or "No high-quality submissions"

**Possible Causes**:
- Database empty or has low-quality submissions
- Selection criteria too strict

**Resolution**:
1. Check database has submissions: `psql $DATABASE_URL -c "SELECT COUNT(*) FROM submission;"`
2. If empty, load test data or adjust criteria in query
3. Lower thresholds in selection criteria if needed
4. Use `--submission-id` argument to specify a known submission

### Issue 2: Service Initialization Fails
**Symptom**: "Failed to initialize pipeline" or service import errors

**Possible Causes**:
- Missing API keys
- Service dependencies not installed
- Import errors in service code

**Resolution**:
1. Verify API keys: `echo $OPENROUTER_API_KEY`, `echo $JINA_API_KEY`
2. Check imports: `python -c "from core.pipeline import OpportunityPipeline"`
3. Review error traceback for specific missing dependencies
4. Install missing dependencies: `pip install <missing_package>`

### Issue 3: Service Execution Fails
**Symptom**: Service shows "✗ FAILED" in results

**Possible Causes**:
- API timeout or rate limiting
- Invalid API key
- Service configuration error
- Input data quality issues

**Resolution**:
1. Check service-specific error in verbose logs
2. Verify API key is correct and has credits
3. Test API manually:
   ```bash
   # Test OpenRouter API
   curl https://openrouter.ai/api/v1/models -H "Authorization: Bearer $OPENROUTER_API_KEY"

   # Test Jina API
   curl "https://r.jina.ai/https://example.com" -H "Authorization: Bearer $JINA_API_KEY"
   ```
4. Review service config in `config/service_config.json`
5. Check submission has required fields for service

### Issue 4: Low Field Coverage (<90%)
**Symptom**: Field coverage 50-80%, some enrichment fields empty

**Possible Causes**:
- Services skipped due to thresholds
- Service execution partial failure
- Submission quality issues

**Resolution**:
1. Check which fields are missing in JSON report: `cat $LATEST_RESULT | jq '.fields_coverage_detail'`
2. Review service execution status
3. Lower thresholds in `config/service_config.json`
4. Check submission quality (has sufficient text, score, comments)

### Issue 5: Cost Exceeds Budget (>$0.20)
**Symptom**: Total cost > $0.20

**Possible Causes**:
- MonetizationService not using deduplication
- MarketValidationService made too many searches
- Multiple retries due to failures

**Resolution**:
1. Review cost breakdown in report
2. Check if deduplication is enabled in `config/service_config.json`
3. Review `max_searches` setting for MarketValidationService
4. Check observability logs for duplicate API calls

### Issue 6: Database Storage Fails
**Symptom**: Data not found in `app_opportunities` table after test

**Possible Causes**:
- DLT pipeline not configured
- Database permissions issue
- Storage service error

**Resolution**:
1. Check pipeline logs for storage errors
2. Verify `app_opportunities` table exists: `psql $DATABASE_URL -c "\dt app_opportunities;"`
3. Check DLT configuration in `config/service_config.json`
4. Review storage service logs

---

## Reporting Results

### Create Testing Report

Create: `docs/plans/unified-pipeline-refactoring/local-ai-report/integration-testing/test-01-single-submission-report.md`

**Template**:

```markdown
# Test 01: Single Submission Validation - Testing Report

**Date**: YYYY-MM-DD HH:MM
**Tester**: Local AI Agent
**Status**: [SUCCESS/PARTIAL/FAILED]

## Summary

- Test Duration: Xm Ys
- Submission ID: abc123xyz
- Services Executed: 5/5
- Services Succeeded: 5/5
- Field Coverage: XX.X%
- Total Cost: $X.XXXX
- Overall Status: [PASSED/FAILED]

## Test Execution

### Pre-Test Setup
- Database submissions available: X
- Selected submission: abc123xyz
  - Title: [submission title]
  - Subreddit: r/[subreddit]
  - Reddit Score: XX
  - Comments: XX
  - Text Length: XXX chars

### Pipeline Execution
- Initialization: [SUCCESS/FAILED]
- Processing Time: XX.Xs
- Services Loaded: 5

### Service Results

| Service | Status | Cost | Notes |
|---------|--------|------|-------|
| ProfilerService | SUCCESS | $0.0050 | Claude Haiku profile generated |
| OpportunityService | SUCCESS | $0.0000 | 5-dimension scoring complete |
| MonetizationService | SUCCESS | $0.1000 | Agno 4-agent analysis |
| TrustService | SUCCESS | $0.0000 | 6-dimension validation |
| MarketValidationService | SUCCESS | $0.0500 | Jina AI + 3 searches |

### Enrichment Results

**Field Coverage**: 28/30 fields (93.3%)

**Populated Fields**:
- opportunity_score: 72.5
- final_score: 68.3
- dimension_scores: {market: 75, monetization: 70, ...}
- priority: HIGH
- core_functions: ["expense_tracking", "bank_sync", ...]
- profession: "Financial Analyst"
- ai_profile: {...}
- monetization_score: 78.0
- trust_level: SILVER
- market_validation_score: 65.0
- [list all populated fields]

**Missing Fields** (if any):
- [list any fields that were not populated]

## Issues Found

### Issue 1: [Title]
- **Description**: [What went wrong]
- **Location**: [File:line or service name]
- **Severity**: [Critical/High/Medium/Low]
- **Resolution**: [How it was fixed]
- **Commit**: [commit hash if code was fixed]

[Repeat for each issue]

## Performance Analysis

- Processing Time: XX.Xs
- Avg Time per Submission: XX.Xs
- Throughput: X.X submissions/minute
- Peak Memory: XXX MB (if tracked)

## Cost Analysis

- Total Cost: $X.XXXX
- Cost per Submission: $X.XXXX
- Cost Breakdown:
  - ProfilerService: $0.0050
  - MonetizationService: $0.1000
  - MarketValidationService: $0.0500
  - Total: $0.1550

## Observability

- AgentOps Session: [Created/Not Available]
  - Session ID: [session_id]
  - Trace File: [path]

- LiteLLM Logs: [Created/Not Available]
  - Log File: [path]
  - Total Calls: X
  - Total Tokens: X

- Agno Traces: [Created/Not Available]
  - Trace File: [path]
  - Agents Executed: 4
  - Deduplication: [Yes/No]

## Success Criteria Evaluation

- [ ] All 5 services executed: [YES/NO]
- [ ] Field coverage >= 90%: [YES/NO] (XX.X%)
- [ ] Processing time 15-30s: [YES/NO] (XX.Xs)
- [ ] Cost $0.10-$0.20: [YES/NO] ($X.XXXX)
- [ ] No unhandled exceptions: [YES/NO]
- [ ] Data stored in database: [YES/NO]
- [ ] Observability working: [YES/NO]

## Overall Result

✅ **TEST PASSED** - All success criteria met

[or]

❌ **TEST FAILED** - [Reason for failure]

## Recommendations

1. [Recommendation 1]
2. [Recommendation 2]

## Next Steps

- [ ] Proceed to Test 02 (Small Batch)
- [ ] [Any other follow-up actions]

---

**Testing Complete**: YYYY-MM-DD HH:MM
```

### Exit Criteria for Test 01

Test 01 is **COMPLETE** when:

1. ✅ Test script executes without crashes
2. ✅ All 5 services execute successfully
3. ✅ Field coverage >= 90%
4. ✅ Cost within budget ($0.10-$0.20)
5. ✅ Data stored in database
6. ✅ Testing report created
7. ✅ No critical issues outstanding

**THEN**: Mark Test 01 as PASSED in HANDOVER-PHASE-8-TESTING.md and proceed to Test 02

---

## Notes for Local AI

### Testing Philosophy

1. **Run, Document, Fix**: Run test → Document results → Fix issues → Re-run
2. **No Skipping**: Do not skip steps or assume things work
3. **Evidence-Based**: Every claim in report must be backed by evidence (logs, database queries, files)
4. **Clear Communication**: Report issues clearly with reproduction steps

### Expected Timeline

- Setup: 10 minutes
- Test Execution: 10-30 minutes (depending on issues)
- Issue Resolution: 0-60 minutes (if issues found)
- Reporting: 10-15 minutes

**Total**: 30 minutes - 2 hours

### When to Ask for Help

- If API keys are missing and you cannot obtain them
- If fundamental architectural issues are found (not bugs, but design problems)
- If test consistently fails after multiple fix attempts

### Success Indicators

You've succeeded when:
- Test exits with code 0
- Report shows all green checkmarks
- Database has enriched submission
- No critical issues in report

Good luck with testing! 🚀
