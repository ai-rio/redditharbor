# Test 02: Small Batch (5 Submissions) Validation - Local AI Testing Prompt

**Date**: 2025-11-23
**Test**: Test 02 - Small Batch Validation
**File**: `scripts/testing/integration/tests/test_02_small_batch.py`
**Purpose**: Validate unified OpportunityPipeline consistency across multiple varied submissions

---

## Pre-Testing Checklist

Before running the test, verify the following:

- [ ] **Supabase Running**: `supabase status` shows all services running
- [ ] **Database Has Varied Data**: `psql $DATABASE_URL -c "SELECT COUNT(*) FROM submission WHERE reddit_score >= 20;"` returns >= 5
- [ ] **Test 01 Status**: Test 01 PASSED with >= 90% field coverage
- [ ] **Environment Variables Set** (`.env.local`):
  - [ ] `SUPABASE_URL`
  - [ ] `SUPABASE_KEY`
  - [ ] `OPENROUTER_API_KEY` (for ProfilerService)
  - [ ] `JINA_API_KEY` (for MarketValidationService)
  - [ ] `AGENTOPS_API_KEY` (optional, for observability)
- [ ] **Small Batch Config Ready**: `submissions_small_batch.json` has 5 varied submissions
- [ ] **Virtual Environment Activated**: `which python` shows project venv
- [ ] **Dependencies Installed**: All core dependencies available
- [ ] **API Credits Available**: Sufficient OpenRouter/Jina credits for 5 submissions (~$0.50-$1.00 total)

---

## Test Overview

### Goal
Prove that the unified OpportunityPipeline processes multiple submissions consistently, handling varied quality levels and edge cases while maintaining field coverage and performance.

### Submissions to Test

The test uses 5 varied submissions from `submissions_small_batch.json`:

1. **high_001** (High Quality)
   - High score, good engagement, sufficient text
   - Expected: All services execute successfully
   - Field coverage: 90%+

2. **medium_001** (Medium Quality)
   - Moderate score, some engagement, limited text
   - Expected: Most services execute, some may skip
   - Field coverage: 70-90%

3. **low_001** (Low Quality)
   - Low score, minimal engagement, very limited text
   - Expected: Graceful degradation, basic services only
   - Field coverage: 50-70%

4. **edge_long_text** (Edge Case)
   - Very long text (>5000 characters)
   - Expected: Services handle long text, possible timeouts
   - Field coverage: 80%+

5. **edge_minimal** (Edge Case)
   - Minimal required data, tests validation
   - Expected: Required field validation only
   - Field coverage: 40-60%

### Services to Validate
1. **ProfilerService**: AI profiling using Claude Haiku via OpenRouter (~$0.025 total)
2. **OpportunityService**: 5-dimensional opportunity scoring (rule-based, no cost)
3. **MonetizationService**: DISABLED due to credit constraints
4. **TrustService**: 6-dimensional trust validation (rule-based, no cost)
5. **MarketValidationService**: Real market data validation using Jina AI (~$0.25 total)

### Success Criteria
- [ ] All 5 submissions processed (100% completion rate)
- [ ] Average field coverage >= 90% across high/medium quality submissions
- [ ] Processing time: 5-15 minutes total (1-3 minutes per submission)
- [ ] Total cost: $0.50-$1.00
- [ ] Consistent behavior across similar quality submissions
- [ ] Graceful handling of edge cases
- [ ] No unhandled exceptions or crashes
- [ ] Data stored in database correctly for all submissions
- [ ] Memory usage < 1GB peak

---

## Test Execution

### Step 1: Verify Small Batch Configuration (5 minutes)

**Task**: Ensure submissions_small_batch.json has proper varied submissions

```bash
# Navigate to project root
cd /home/user/redditharbor

# Check submissions configuration
cat scripts/testing/integration/config/submissions_small_batch.json | jq '.submissions | length'
cat scripts/testing/integration/config/submissions_small_batch.json | jq '.submissions[] | {id: .submission_id, title: .title, score: .reddit_score, comments: .num_comments, text_length: .text_length}'
```

**Expected Output**: 5 submissions with varied characteristics

If configuration is missing or incomplete:
```bash
# Update submissions_small_batch.json with actual submission IDs
nano scripts/testing/integration/config/submissions_small_batch.json

# Query database for suitable submissions of different quality levels
# High quality:
psql $DATABASE_URL -c "SELECT submission_id, title, subreddit, reddit_score, num_comments, LENGTH(selftext) as text_length FROM submission WHERE reddit_score >= 100 AND num_comments >= 20 AND LENGTH(selftext) >= 300 ORDER BY reddit_score DESC LIMIT 1;"

# Medium quality:
psql $DATABASE_URL -c "SELECT submission_id, title, subreddit, reddit_score, num_comments, LENGTH(selftext) as text_length FROM submission WHERE reddit_score BETWEEN 30 AND 99 AND num_comments BETWEEN 5 AND 19 AND LENGTH(selftext) BETWEEN 100 AND 299 ORDER BY reddit_score DESC LIMIT 1;"

# Low quality:
psql $DATABASE_URL -c "SELECT submission_id, title, subreddit, reddit_score, num_comments, LENGTH(selftext) as text_length FROM submission WHERE reddit_score < 30 AND num_comments < 5 AND LENGTH(selftext) < 100 ORDER BY reddit_score DESC LIMIT 1;"

# Edge case - long text:
psql $DATABASE_URL -c "SELECT submission_id, title, subreddit, reddit_score, num_comments, LENGTH(selftext) as text_length FROM submission WHERE LENGTH(selftext) > 3000 ORDER BY LENGTH(selftext) DESC LIMIT 1;"

# Edge case - minimal:
psql $DATABASE_URL -c "SELECT submission_id, title, subreddit, reddit_score, num_comments, LENGTH(selftext) as text_length FROM submission WHERE selftext IS NOT NULL AND LENGTH(selftext) < 50 ORDER BY LENGTH(selftext) ASC LIMIT 1;"
```

### Step 2: Verify Service Configuration (5 minutes)

**Task**: Ensure appropriate services are enabled for batch testing

```bash
# Check service_config.json
cat scripts/testing/integration/config/service_config.json | jq '.services | to_entries | map({service: .key, enabled: .value.enabled})'
```

**Expected Configuration**:
- profiler: enabled (true)
- opportunity: enabled (true)
- monetization: disabled (false) - to save credits
- trust: enabled (true)
- market_validation: enabled (true)

If configuration needs adjustment, edit `config/service_config.json` and set `enabled` appropriately.

### Step 3: Run Test 02 (5-15 minutes)

**Task**: Execute the small batch test

```bash
# Run test with verbose logging
python scripts/testing/integration/tests/test_02_small_batch.py --verbose
```

**Monitor Output** for:
- Batch initialization success
- Individual submission processing status
- Service execution patterns
- Field coverage per submission
- Cost accumulation
- Memory usage indicators
- Batch-level statistics

**Expected Output** (sample):
```
================================================================================
TEST 02: SMALL BATCH VALIDATION
================================================================================

Goal: Validate consistency across 5 varied submissions (high, medium, low, edge cases)

Submissions to test:
  1. high_001 - High quality (all services expected)
  2. medium_001 - Medium quality (most services expected)
  3. low_001 - Low quality (graceful degradation)
  4. edge_long_text - Edge case (long text handling)
  5. edge_minimal - Edge case (minimal data validation)

Services enabled:
  1. ProfilerService (AI profiling via Claude Haiku)
  2. OpportunityService (5-dimensional scoring)
  3. TrustService (6-dimensional trust validation)
  4. MarketValidationService (Real market data via Jina AI)

Initializing batch processing...
  - Data Source: DATABASE
  - Batch Size: 5 submissions
  - Services Enabled: 4

✓ Batch initialized successfully
  - Services loaded: 4
  - Memory usage: 125 MB

Processing batch...
--------------------------------------------------------------------------------
Processing submission 1/5: high_001...
  ✓ ProfilerService executed (0.8s, $0.0050)
  ✓ OpportunityService executed (0.2s, $0.0000)
  ✓ TrustService executed (0.3s, $0.0000)
  ✓ MarketValidationService executed (2.1s, $0.0500)
  ✓ Field coverage: 92.3% (28/30 fields)

Processing submission 2/5: medium_001...
  ✓ ProfilerService executed (0.6s, $0.0050)
  ✓ OpportunityService executed (0.2s, $0.0000)
  ✓ TrustService executed (0.2s, $0.0000)
  ✓ MarketValidationService executed (1.8s, $0.0500)
  ✓ Field coverage: 85.7% (24/28 fields)

Processing submission 3/5: low_001...
  ✓ ProfilerService skipped (insufficient quality)
  ✓ OpportunityService executed (0.2s, $0.0000)
  ✓ TrustService executed (0.2s, $0.0000)
  ✓ MarketValidationService skipped (insufficient opportunity score)
  ✓ Field coverage: 63.3% (19/30 fields)

Processing submission 4/5: edge_long_text...
  ✓ ProfilerService executed (1.2s, $0.0050)
  ✓ OpportunityService executed (0.3s, $0.0000)
  ✓ TrustService executed (0.4s, $0.0000)
  ✓ MarketValidationService executed (2.5s, $0.0500)
  ✓ Field coverage: 88.9% (32/36 fields)

Processing submission 5/5: edge_minimal...
  ✓ ProfilerService skipped (insufficient text)
  ✓ OpportunityService executed (0.1s, $0.0000)
  ✓ TrustService executed (0.1s, $0.0000)
  ✓ MarketValidationService skipped (insufficient opportunity score)
  ✓ Field coverage: 46.7% (14/30 fields)
--------------------------------------------------------------------------------

✓ Batch completed in 8.7s

Analyzing batch results...

Batch Execution Results:
================================================================================
Submission           Status     Services    Coverage   Cost     Time
high_001            SUCCESS    4/4         92.3%      $0.0550  3.4s
medium_001          SUCCESS    4/4         85.7%      $0.0550  2.8s
low_001             SUCCESS    2/4         63.3%      $0.0000  0.4s
edge_long_text      SUCCESS    4/4         88.9%      $0.0550  4.4s
edge_minimal        SUCCESS    2/4         46.7%      $0.0000  0.2s
--------------------------------------------------------------------------------
Batch Summary:
  - Total Submissions: 5/5 (100%)
  - Total Services Executed: 16/20 (80%)
  - Avg Field Coverage: 75.4%
  - High/Medium Coverage: 89.0%
  - Total Cost: $0.1650
  - Total Time: 11.2s
  - Avg Time/Submission: 2.2s
  - Peak Memory: 145 MB

[Battery metrics console report...]

✓ Results saved to: scripts/testing/integration/results/test_02_small_batch/run_2025-11-23_14-30-00.json

================================================================================
✅ TEST 02 PASSED - Small batch validation successful
================================================================================
```

### Step 4: Verify Results (5 minutes)

**Task**: Check batch results and database consistency

**1. Check JSON Report**:
```bash
# Find latest result file
LATEST_RESULT=$(ls -t scripts/testing/integration/results/test_02_small_batch/run_*.json | head -1)

# View batch summary
cat $LATEST_RESULT | jq '{
  total_submissions: .total_submissions,
  success_rate: .success_rate,
  avg_field_coverage: .avg_field_coverage,
  high_medium_coverage: .high_medium_field_coverage,
  total_cost: .total_cost,
  total_time: .total_time,
  services_executed: .total_services_executed,
  peak_memory_mb: .peak_memory_mb
}'

# View per-submission results
cat $LATEST_RESULT | jq '.submissions[] | {id: .submission_id, coverage: .field_coverage, services: .services_succeeded, cost: .total_cost}'
```

**Expected**:
- `total_submissions`: 5
- `success_rate`: 100
- `avg_field_coverage`: 70-80% (overall)
- `high_medium_coverage`: >= 85% (for high/medium quality)
- `total_cost`: 0.50-1.00
- `total_time`: 300-900 seconds (5-15 minutes)

**2. Check Database**:
```bash
# Verify all submissions were stored
psql $DATABASE_URL -c "SELECT submission_id, opportunity_score, final_score, profession, trust_level, market_validation_score FROM app_opportunities WHERE submission_id IN ('high_001', 'medium_001', 'low_001', 'edge_long_text', 'edge_minimal') ORDER BY opportunity_score DESC;"

# Check field coverage patterns
psql $DATABASE_URL -c "SELECT
  COUNT(*) as total_enriched,
  AVG(CASE WHEN profession IS NOT NULL THEN 1 ELSE 0 END) * 100 as profession_coverage,
  AVG(CASE WHEN ai_profile IS NOT NULL THEN 1 ELSE 0 END) * 100 as ai_profile_coverage,
  AVG(CASE WHEN trust_level IS NOT NULL THEN 1 ELSE 0 END) * 100 as trust_coverage,
  AVG(CASE WHEN market_validation_score IS NOT NULL THEN 1 ELSE 0 END) * 100 as market_coverage
FROM app_opportunities
WHERE submission_id IN ('high_001', 'medium_001', 'low_001', 'edge_long_text', 'edge_minimal');"
```

**Expected**: All 5 submissions present with varying levels of enrichment based on quality

**3. Check Observability** (if enabled):
```bash
# Check AgentOps traces for batch patterns
ls -lt scripts/testing/integration/observability/agentops_traces/ | head -10

# Check LiteLLM logs for cost tracking
ls -lt scripts/testing/integration/observability/litellm_logs/ | head -5
cat scripts/testing/integration/observability/litellm_logs/*.log | jq '.total_cost'

# Check memory/performance logs
ls -lt scripts/testing/integration/observability/performance_logs/
```

**Expected**: Trace files and logs showing batch processing patterns and costs

---

## Issues to Watch For

### Issue 1: Inconsistent Submissions Quality
**Symptom**: All submissions show similar field coverage or execution patterns

**Possible Causes**:
- All submissions selected have similar quality levels
- Service thresholds too strict/lenient
- Configuration error in submission selection

**Resolution**:
1. Verify submission variety in config: Check reddit_score, num_comments, text_length
2. Adjust service thresholds if all submissions trigger same behavior
3. Manually select submissions with clear quality differences
4. Use `--submission-ids` argument to specify diverse submissions

### Issue 2: Edge Cases Cause Failures
**Symptom**: Test fails on long text or minimal submissions

**Possible Causes**:
- Text truncation or buffer overflow
- Timeout issues with long processing
- Validation errors on minimal data

**Resolution**:
1. Check verbose logs for specific error messages
2. For long text: Verify timeout settings and memory usage
3. For minimal: Check required field validation logic
4. Consider adjusting edge case thresholds in service config
5. Add protective measures in service implementations

### Issue 3: Cost Exceeds Budget (>$1.00)
**Symptom**: Total cost > $1.00 for 5 submissions

**Possible Causes**:
- Services not using deduplication properly
- Too many API calls per submission
- MonetizationService accidentally enabled

**Resolution**:
1. Verify MonetizationService is disabled in config
2. Check MarketValidationService `max_searches` setting
3. Review cost breakdown in JSON report
4. Implement cost limiting or warnings in test
5. Use API call deduplication where possible

### Issue 4: Memory Usage Too High (>1GB)
**Symptom**: Memory usage grows linearly with batch size

**Possible Causes**:
- Data not being released between submissions
- Large text submissions held in memory
- Observability data accumulation

**Resolution**:
1. Monitor memory usage per submission
2. Implement proper cleanup between submissions
3. Check for memory leaks in pipeline code
4. Limit concurrent processing or add memory limits
5. Optimize data structures for batch processing

### Issue 5: Processing Too Slow (>15 minutes)
**Symptom**: Batch takes >15 minutes for 5 submissions

**Possible Causes**:
- Sequential processing instead of concurrent
- API rate limiting or timeouts
- Complex processing on large text

**Resolution**:
1. Check if services can run in parallel
2. Optimize API call patterns and caching
3. Reduce MarketValidationService search count
4. Add progress indicators and timeout handling
5. Consider processing smaller batches or using faster models

### Issue 6: Inconsistent Data Storage
**Symptom**: Some submissions not saved to database or incomplete data

**Possible Causes**:
- Database connection issues during batch
- Partial failures not properly handled
- Storage service overwhelmed

**Resolution**:
1. Check database logs for connection issues
2. Verify error handling doesn't skip storage
3. Implement transaction handling for batch operations
4. Add retry logic for database operations
5. Validate data integrity after batch completion

---

## Reporting Results

### Create Testing Report

Create: `docs/plans/unified-pipeline-refactoring/local-ai-report/integration-testing/test-02-small-batch-report.md`

**Template**:

```markdown
# Test 02: Small Batch Validation - Testing Report

**Date**: YYYY-MM-DD HH:MM
**Tester**: Local AI Agent
**Status**: [SUCCESS/PARTIAL/FAILED]

## Summary

- Test Duration: Xm Ys
- Total Submissions: 5/5
- Submissions Processed: 5/5 (100%)
- Services Enabled: 4/4 (Profiler, Opportunity, Trust, Market Validation)
- Overall Success Rate: 100%
- Average Field Coverage: XX.X%
- High/Medium Quality Coverage: XX.X%
- Total Cost: $X.XXXX
- Peak Memory: XXX MB
- Overall Status: [PASSED/FAILED]

## Test Configuration

### Submissions Tested

| ID | Quality | Title | Score | Comments | Text Length | Expected Services |
|----|---------|-------|-------|----------|-------------|-------------------|
| high_001 | High | [title] | XXX | XX | XXX | All 4 services |
| medium_001 | Medium | [title] | XX | X | XXX | 3-4 services |
| low_001 | Low | [title] | X | X | XX | 2 services basic |
| edge_long_text | Edge | [title] | XX | XX | XXXX+ | Handle long text |
| edge_minimal | Edge | [title] | X | X | X | Validation only |

### Services Configuration

| Service | Enabled | Expected Cost | Notes |
|---------|---------|---------------|-------|
| ProfilerService | YES | $0.025 | Claude Haiku for high/medium |
| OpportunityService | YES | $0.000 | Rule-based, all submissions |
| MonetizationService | NO | $0.000 | Disabled to save credits |
| TrustService | YES | $0.000 | Rule-based, all submissions |
| MarketValidationService | YES | $0.250 | Jina AI for high/medium only |

## Test Execution

### Batch Processing
- Initialization: [SUCCESS/FAILED]
- Batch Size: 5 submissions
- Processing Mode: [Sequential/Parallel]
- Total Processing Time: XX.Xs
- Average Time/Submission: X.Xs
- Peak Memory Usage: XXX MB

### Submission Results

| Submission | Status | Services Executed | Field Coverage | Cost | Time | Notes |
|------------|--------|-------------------|----------------|------|------|-------|
| high_001 | SUCCESS | 4/4 | XX.X% | $0.0550 | X.Xs | All services ran |
| medium_001 | SUCCESS | 4/4 | XX.X% | $0.0550 | X.Xs | Most services ran |
| low_001 | SUCCESS | 2/4 | XX.X% | $0.0000 | X.Xs | Basic services only |
| edge_long_text | SUCCESS | 4/4 | XX.X% | $0.0550 | X.Xs | Long text handled |
| edge_minimal | SUCCESS | 2/4 | XX.X% | $0.0000 | X.Xs | Validation passed |

### Service Performance

| Service | Total Executions | Success Rate | Total Cost | Avg Time | Notes |
|---------|------------------|--------------|------------|----------|-------|
| ProfilerService | 3 | 100% | $0.0150 | X.Xs | High/medium/long_text |
| OpportunityService | 5 | 100% | $0.0000 | X.Xs | All submissions |
| TrustService | 5 | 100% | $0.0000 | X.Xs | All submissions |
| MarketValidationService | 3 | 100% | $0.1500 | X.Xs | High/medium/long_text |

## Consistency Analysis

### Quality-Based Behavior
- **High Quality** (high_001): All services executed, high coverage
- **Medium Quality** (medium_001): Most services executed, good coverage
- **Low Quality** (low_001): Basic services only, lower coverage
- **Consistency Score**: [Score how well quality-based filtering worked]

### Edge Case Handling
- **Long Text** (edge_long_text): [How it was handled]
- **Minimal Data** (edge_minimal): [How validation worked]
- **Edge Case Score**: [Score how well edge cases were handled]

### Field Coverage Patterns
- **AI Profile Fields**: Populated for X/5 submissions
- **Trust Fields**: Populated for X/5 submissions
- **Market Fields**: Populated for X/5 submissions
- **Core Fields**: Populated for X/5 submissions

## Performance Analysis

### Batch Efficiency
- **Throughput**: X.X submissions/minute
- **Cost Efficiency**: $X.XXXX per submission
- **Memory Efficiency**: X.X MB/submission peak
- **Service Overhead**: X% of total time

### Resource Usage
- **Peak Memory**: XXX MB (limit: 1GB)
- **Memory Growth Pattern**: [Linear/Stable]
- **API Call Patterns**: [Efficient/Needs optimization]
- **Cost Distribution**: [Services breakdown]

## Issues Found

### Issue 1: [Title]
- **Description**: [What went wrong]
- **Location**: [File:line or service name]
- **Severity**: [Critical/High/Medium/Low]
- **Affected Submissions**: [List affected submissions]
- **Resolution**: [How it was fixed]
- **Commit**: [commit hash if code was fixed]

[Repeat for each issue]

## Observability Analysis

### AgentOps Tracing
- Sessions Created: [Number]
- Service Traces: [Complete/Incomplete]
- Cost Tracking: [Accurate/Needs improvement]
- Performance Insights: [Key findings]

### LiteLLM Logging
- Total API Calls: [Number]
- Total Tokens Used: [Number]
- Cost Tracking: [Matches expected]
- Error Rates: [Percentage]

### Database Operations
- Records Stored: [Number]
- Storage Success Rate: [Percentage]
- Storage Time: [Average per submission]
- Data Integrity: [Verified/Issues found]

## Success Criteria Evaluation

- [ ] All 5 submissions processed: [YES/NO] (5/5)
- [ ] Average field coverage >= 90%: [YES/NO] (XX.X% overall, XX.X% high/medium)
- [ ] Processing time 5-15 minutes: [YES/NO] (XX.X minutes)
- [ ] Cost $0.50-$1.00: [YES/NO] ($X.XXXX)
- [ ] Consistent quality-based behavior: [YES/NO]
- [ ] Graceful edge case handling: [YES/NO]
- [ ] Memory usage < 1GB: [YES/NO] (XXX MB)
- [ ] No unhandled exceptions: [YES/NO]
- [ ] Data stored for all submissions: [YES/NO]
- [ ] Observability working: [YES/NO]

## Overall Result

✅ **TEST PASSED** - All success criteria met

[or]

❌ **TEST FAILED** - [Reason for failure]

## Batch Processing Insights

### Quality Score Effectiveness
- High quality submissions: [All services ran as expected]
- Medium quality submissions: [Appropriate service filtering]
- Low quality submissions: [Graceful degradation worked]
- **Recommendation**: [Threshold adjustments if needed]

### Edge Case Robustness
- Long text handling: [Performance and success]
- Minimal data validation: [Error prevention]
- **Recommendation**: [Edge case handling improvements]

### Scalability Indicators
- Linear processing time: [Yes/No]
- Memory stability: [Yes/No]
- Cost predictability: [Yes/No]
- **Recommendation**: [Scale to larger batches]

## Recommendations

1. [Recommendation 1 - e.g., Adjust quality thresholds for better filtering]
2. [Recommendation 2 - e.g., Optimize long text processing]
3. [Recommendation 3 - e.g., Implement batch parallelization]
4. [Recommendation 4 - e.g., Add more comprehensive edge case tests]

## Next Steps

- [ ] Proceed to Test 03 (Error Handling)
- [ ] [Any fixes needed before proceeding]
- [ ] [Performance optimizations if needed]
- [ ] [Scale considerations for larger batches]

---

**Testing Complete**: YYYY-MM-DD HH:MM
```

### Exit Criteria for Test 02

Test 02 is **COMPLETE** when:

1. ✅ Test script executes without crashes
2. ✅ All 5 submissions processed successfully (100% completion)
3. ✅ Average field coverage >= 90% for high/medium quality submissions
4. ✅ Cost within budget ($0.50-$1.00)
5. ✅ Processing time 5-15 minutes
6. ✅ Memory usage < 1GB peak
7. ✅ Consistent quality-based behavior demonstrated
8. ✅ Edge cases handled gracefully
9. ✅ Data stored for all submissions
10. ✅ Testing report created
11. ✅ No critical issues outstanding

**THEN**: Mark Test 02 as PASSED in HANDOVER-PHASE-8-TESTING.md and proceed to Test 03

---

## Notes for Local AI

### Batch Testing Philosophy

1. **Consistency over Speed**: Focus on consistent behavior across submissions
2. **Quality-Based Validation**: Verify services adapt to submission quality
3. **Edge Case Robustness**: Test system boundaries and error conditions
4. **Resource Efficiency**: Monitor memory, cost, and time at scale
5. **Data Integrity**: Ensure all processed data is stored correctly

### Expected Timeline

- Setup and Configuration: 15 minutes
- Test Execution: 5-15 minutes (depending on API performance)
- Result Analysis: 10 minutes
- Issue Resolution: 0-60 minutes (if issues found)
- Reporting: 15-20 minutes

**Total**: 45 minutes - 2 hours

### Batch-Specific Success Indicators

You've succeeded when:
- Quality-based service filtering works consistently
- Edge cases don't crash the system
- Resource usage scales linearly (no exponential growth)
- Cost and time remain predictable
- All submissions complete with appropriate enrichment levels

### When to Ask for Help

- If batch processing fails repeatedly for multiple submissions
- If edge cases cause systemic failures
- If cost exceeds budget significantly (>20% over)
- If memory usage grows exponentially
- If quality-based filtering doesn't work as expected

Good luck with batch testing! 🚀