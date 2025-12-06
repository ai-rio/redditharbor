# Pipeline v3 Live Test Execution Guide

**Complete AI-Executable Instructions for Live Testing**

**Date:** 2025-12-05
**Version:** 1.0
**Audience:** AI Agents, Developers, QA Engineers

---

## 📋 Table of Contents

1. [Pre-Flight Checklist](#pre-flight-checklist)
2. [Environment Setup](#environment-setup)
3. [Metrics Integration (Step-by-Step)](#metrics-integration-step-by-step)
4. [Phase 1: Smoke Test](#phase-1-smoke-test-100-opportunities)
5. [Phase 2: Quality Validation](#phase-2-quality-validation-500-opportunities)
6. [Phase 3: Performance Validation](#phase-3-performance-validation-1000-opportunities)
7. [Manual Review Procedures](#manual-review-procedures)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Rollback Procedures](#rollback-procedures)

---

## 🔍 Pre-Flight Checklist

**Run these checks BEFORE starting live testing:**

### 1. Database Verification

```bash
# Check if Supabase is running
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c "SELECT 1;"
# Expected: Should return "1" without errors
# Password: postgres

# Check if opportunities table exists
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c "\dt opportunities"
# Expected: Should show table structure

# Check current opportunity count
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c "SELECT COUNT(*) FROM opportunities;"
# Note this number - you'll compare it after testing
```

**If database checks fail:**
```bash
# Start Supabase
cd /home/carlos/projects/redditharbor-core-functions-fix
supabase start

# Wait 30 seconds, then retry checks
```

---

### 2. Python Environment Verification

```bash
# Verify UV environment
cd /home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3
uv --version
# Expected: uv 0.x.x or higher

# Activate virtual environment
source .venv/bin/activate

# Check required packages
python -c "import psycopg2; print('psycopg2: OK')"
python -c "import flask; print('flask: OK')"
python -c "from config import get_settings; print('config: OK')"
```

**If package checks fail:**
```bash
# Install missing dependencies
uv pip install psycopg2-binary flask

# Retry checks
```

---

### 3. Pipeline Configuration Verification

```bash
# Check DATABASE_URL is set correctly
python -c "from config import get_settings; s = get_settings(); print(f'DB: {s.database_url}')"
# Expected: postgresql://postgres:postgres@127.0.0.1:54322/postgres

# Check Reddit credentials exist
python -c "from config import get_settings; s = get_settings(); print(f'Reddit: {bool(s.reddit_client_id)}')"
# Expected: Reddit: True

# Check OpenRouter key exists
python -c "from config import get_settings; s = get_settings(); print(f'OpenRouter: {bool(s.openrouter_api_key)}')"
# Expected: OpenRouter: True
```

**If configuration checks fail:**
- Check `.env.local` file exists
- Verify all required environment variables are set
- See [Troubleshooting: Missing Configuration](#missing-configuration)

---

### 4. Disk Space Verification

```bash
# Check available disk space
df -h /home/carlos/projects/redditharbor-core-functions-fix
# Expected: At least 5GB free

# Check logs directory exists
mkdir -p /home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3/logs
mkdir -p /home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3/reports
```

---

### ✅ Pre-Flight Checklist Summary

- [ ] Database connection successful (port 54322)
- [ ] Opportunities table exists
- [ ] Python environment activated
- [ ] psycopg2 and flask installed
- [ ] Configuration loaded successfully
- [ ] Reddit and OpenRouter credentials present
- [ ] At least 5GB disk space available
- [ ] Logs and reports directories created

**⚠️ DO NOT PROCEED until all checks pass!**

---

## 🔧 Environment Setup

### Install Required Dependencies

```bash
cd /home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3

# Activate virtual environment
source .venv/bin/activate

# Install metrics collection dependencies
uv pip install psycopg2-binary flask

# Verify installation
python -c "import psycopg2, flask; print('Dependencies installed successfully')"
```

---

## 🔌 Metrics Integration (Step-by-Step)

### Step 1: Apply Database Migration

```bash
cd /home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3

# Make migration script executable (if not already)
chmod +x scripts/apply_metrics_migration.sh

# Apply migration
./scripts/apply_metrics_migration.sh

# Expected output:
# ✓ Database connection successful
# ✓ pipeline_metrics table created successfully
# ✓ Created 5 indexes
# ✓ Created 3 views
```

**Verify migration:**
```bash
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c "\d pipeline_metrics"
# Should show table structure with 10 columns

psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c "\dv"
# Should show 3 views: pipeline_phase_summary, agent_performance_summary, cost_analysis
```

---

### Step 2: Add Metrics Collection to Agno Analyzer

**File:** `pipeline-v3/transform/agno_analyzer.py`

**Location:** Add import at top of file (around line 10)

```python
# Add this import after existing imports
from monitoring.metrics_collector import track_execution, get_collector
```

**Location:** Modify `AgnoOpportunityAnalyzer.analyze()` method (around line 250)

**Find this code:**
```python
async def analyze(
    self,
    submission: RedditSubmission,
    embedding_strategy: Optional[EmbeddingStrategy] = None
) -> AnalysisResult:
    """Analyze Reddit submission using multi-agent consensus"""
```

**Replace with:**
```python
async def analyze(
    self,
    submission: RedditSubmission,
    embedding_strategy: Optional[EmbeddingStrategy] = None
) -> AnalysisResult:
    """Analyze Reddit submission using multi-agent consensus"""

    opportunity_id = f"opp-{submission.id}"
    collector = get_collector()

    # Track entire analysis
    with collector.track("transform", agent_name="all", opportunity_id=opportunity_id) as ctx:
        # Original method code continues here...
        # (Keep all existing code)

        # At the end, before return statement, add:
        ctx["api_cost_usd"] = getattr(result, 'total_cost', 0.0)
        ctx["metadata"] = {
            "agents_executed": len(self.agents),
            "consensus_score": result.final_score
        }

        return result
```

---

### Step 3: Add Metrics Collection to Individual Agents

**File:** `pipeline-v3/transform/agno_agents.py`

**For each agent class (WillingnessToPayAgent, MarketSegmentAgent, etc.):**

**Find the `analyze()` method:**
```python
async def analyze(self, submission: RedditSubmission) -> AgentAnalysis:
    # Agent logic here
```

**Wrap with metrics tracking:**
```python
async def analyze(self, submission: RedditSubmission) -> AgentAnalysis:
    from monitoring.metrics_collector import get_collector

    opportunity_id = f"opp-{submission.id}"
    collector = get_collector()

    # Agent name: 'wtp', 'segment', 'price', 'payment', or 'market'
    agent_name = "wtp"  # Change per agent: wtp, segment, price, payment, market

    with collector.track("transform", agent_name=agent_name, opportunity_id=opportunity_id) as ctx:
        # Original agent analysis code
        result = await self._perform_analysis(submission)

        # Track cost if available
        if hasattr(result, 'cost'):
            ctx["api_cost_usd"] = result.cost

        ctx["metadata"] = {
            "agent_type": agent_name,
            "confidence": getattr(result, 'confidence', 0.0)
        }

        return result
```

**Repeat for all 5 agents:**
- WillingnessToPayAgent → `agent_name = "wtp"`
- MarketSegmentAgent → `agent_name = "segment"`
- PricePointAgent → `agent_name = "price"`
- PaymentBehaviorAgent → `agent_name = "payment"`
- MarketResearchAgent → `agent_name = "market"`

---

### Step 4: Add Metrics Collection to Pipeline Orchestrator

**File:** `pipeline-v3/orchestration/pipeline_orchestrator.py`

**Location:** In the `process_batch()` method (around line 150)

**Add import at top:**
```python
from monitoring.metrics_collector import get_collector
```

**Wrap the extract-transform-load flow:**
```python
async def process_batch(self, submissions: List[dict]) -> List[dict]:
    """Process batch of submissions through pipeline"""

    collector = get_collector()
    results = []

    for submission in submissions:
        opportunity_id = f"opp-{submission['id']}"

        # Track end-to-end pipeline
        with collector.track("end_to_end", opportunity_id=opportunity_id):

            # Extract phase
            with collector.track("extract", opportunity_id=opportunity_id):
                reddit_submission = self._extract(submission)

            # Transform phase (already tracked in agno_analyzer.py)
            analysis_result = await self.analyzer.analyze(reddit_submission)

            # Load phase
            with collector.track("load", opportunity_id=opportunity_id):
                stored = self._load(analysis_result)

            results.append(stored)

    return results
```

---

### Step 5: Verify Metrics Integration

**Create test script:** `pipeline-v3/scripts/test_metrics_integration.py`

```python
#!/usr/bin/env python3
"""Test metrics integration"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from monitoring.metrics_collector import MetricsCollector
import time

def test_metrics():
    """Test metrics collection"""
    print("Testing metrics integration...")

    collector = MetricsCollector()

    # Test manual recording
    collector.record_metric(
        phase="test",
        duration_seconds=1.5,
        success=True,
        agent_name="test_agent",
        opportunity_id="test-001",
        api_cost_usd=0.001,
        metadata={"test": True}
    )

    # Test context manager
    with collector.track("test", "test_agent", "test-002") as ctx:
        time.sleep(0.1)
        ctx["api_cost_usd"] = 0.002

    print("✓ Metrics integration working")

    collector.close()

if __name__ == "__main__":
    test_metrics()
```

**Run test:**
```bash
python scripts/test_metrics_integration.py
# Expected: ✓ Metrics integration working

# Verify data in database
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c "SELECT * FROM pipeline_metrics WHERE phase='test';"
# Should show 2 test records
```

---

### Step 6: Clean Test Data

```bash
# Remove test metrics
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c "DELETE FROM pipeline_metrics WHERE phase='test';"
```

---

### ✅ Metrics Integration Checklist

- [ ] Database migration applied successfully
- [ ] pipeline_metrics table exists with 3 views
- [ ] monitoring/metrics_collector.py imported in agno_analyzer.py
- [ ] AgnoOpportunityAnalyzer.analyze() wrapped with metrics tracking
- [ ] All 5 agents (wtp, segment, price, payment, market) have metrics tracking
- [ ] Pipeline orchestrator tracks extract/load phases
- [ ] Test script executed successfully
- [ ] Test data cleaned from database

**⚠️ Metrics integration complete! Ready for Phase 1.**

---

## 🧪 Phase 1: Smoke Test (100 Opportunities)

**Duration:** 2-3 hours
**Goal:** Verify all systems operational

### Step 1: Prepare for Test

```bash
cd /home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3

# Record baseline
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c \
  "SELECT COUNT(*) as baseline FROM opportunities;" > /tmp/baseline_count.txt

cat /tmp/baseline_count.txt
# Note this number

# Clear old logs
rm -f logs/*.log

# Create test timestamp
date > /tmp/test_start_time.txt
```

---

### Step 2: Execute Smoke Test

```bash
# Run pipeline (100 submissions)
uv run python main.py \
  --limit 100 \
  --subreddits SaaS,Entrepreneur,productivity

# Monitor progress in another terminal
tail -f logs/pipeline.log
```

**Expected output:**
```
INFO - Starting pipeline with 100 submissions
INFO - Extract: Processing r/SaaS...
INFO - Transform: Analyzing submission xyz...
INFO - Load: Stored opportunity opp-xyz
...
INFO - Completed 100/100 submissions
INFO - Total duration: X minutes
```

**⚠️ If errors occur, see [Troubleshooting](#troubleshooting-guide)**

---

### Step 3: Validate Smoke Test

```bash
# Run validator
python scripts/validate_smoke_test.py

# Expected output:
# ✓ Found 100 opportunities (>= 100)
# ✓ All 8 mandatory fields populated
# ✓ Error rate: 0.00% (<= 5.00%)
# ✓ Processing time: X.XX minutes (<= 10)
#
# 🎉 SMOKE TEST PASSED - Proceed to Phase 2
```

**Exit code interpretation:**
- `0` = PASS (proceed to Phase 2)
- `1` = FAIL (fix issues before proceeding)

---

### Step 4: Review Results

```bash
# Check opportunities created
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c \
  "SELECT COUNT(*) FROM opportunities WHERE created_at >= NOW() - INTERVAL '1 hour';"

# Check metrics collected
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c \
  "SELECT * FROM pipeline_phase_summary;"

# View sample opportunities
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c \
  "SELECT app_title, final_score FROM opportunities ORDER BY created_at DESC LIMIT 10;"
```

---

### ✅ Phase 1 Success Criteria

- [ ] 100 opportunities created in database
- [ ] All 8 mandatory fields populated (no NULLs)
- [ ] Error rate <5%
- [ ] Processing time <10 minutes
- [ ] Smoke test validator returns exit code 0
- [ ] Metrics collected in pipeline_metrics table

**If all criteria met:** ✅ Proceed to Phase 2
**If any criteria failed:** ❌ See [Troubleshooting](#troubleshooting-guide)

---

## 📊 Phase 2: Quality Validation (500 Opportunities)

**Duration:** 1 day
**Goal:** Validate Tier 1 Business Value KPIs

### Step 1: Prepare for Test

```bash
# Record start time
date > /tmp/phase2_start_time.txt

# Clear Phase 1 logs
mv logs/pipeline.log logs/pipeline_phase1.log
```

---

### Step 2: Execute Quality Test

```bash
# Run pipeline (500 submissions)
uv run python main.py \
  --limit 500 \
  --subreddits SaaS,Entrepreneur,productivity,smallbusiness,startups

# Monitor in separate terminal
tail -f logs/pipeline.log
```

**Expected duration:** 30-60 minutes for 500 submissions

---

### Step 3: Generate Quality Report

```bash
# Generate report
python scripts/generate_quality_report.py --lookback-hours 24

# Expected output:
# 🎯 TIER 1 BUSINESS VALUE KPIs
# ✓ high_score_rate: PASS
# ✓ function_compliance: PASS
#
# 📊 QUALITY ANALYSIS
# Function Distribution: ...
# Score Distribution: ...
#
# 🎉 QUALITY VALIDATION PASSED - Proceed to Phase 3
```

**Files generated:**
- `reports/quality_report_YYYYMMDD_HHMMSS.json` - Full report
- `reports/top_opportunities_YYYYMMDD_HHMMSS.csv` - Top 50 for manual review

---

### Step 4: Manual Review (Top 50 Opportunities)

**Open CSV file:**
```bash
# Find latest CSV
ls -lt reports/top_opportunities_*.csv | head -1

# Open in spreadsheet or view in terminal
cat reports/top_opportunities_YYYYMMDD_HHMMSS.csv | column -t -s, | less
```

**Manual Review Checklist for Each Opportunity:**

Create file: `reports/manual_review_phase2.md`

```markdown
# Phase 2 Manual Review

**Date:** YYYY-MM-DD
**Reviewer:** [Your Name/AI Agent ID]
**Sample Size:** 50 opportunities (final_score >= 70)

## Review Criteria

For each opportunity, validate:

1. **Problem Clarity** (1-5 scale)
   - Is the problem clearly articulated?
   - Can you understand the user pain point?
   - Rating: __/5

2. **Target Audience** (1-5 scale)
   - Is the target audience well-defined?
   - Can you identify who would use this?
   - Rating: __/5

3. **Monetization Viability** (1-5 scale)
   - Is the monetization path realistic?
   - Would users actually pay for this?
   - Rating: __/5

4. **Market Evidence** (Yes/No)
   - Does the opportunity include market validation?
   - Are there supporting URLs or data?
   - Answer: __

5. **Function Simplicity** (Pass/Fail)
   - Does it have 1-3 functions only?
   - Are functions focused and clear?
   - Answer: __

6. **Overall Viability** (Pass/Fail)
   - Would you greenlight this opportunity?
   - Is it worth pursuing?
   - Answer: __

## Review Summary

| Opportunity ID | Problem | Audience | Monetization | Evidence | Functions | Overall | Notes |
|----------------|---------|----------|--------------|----------|-----------|---------|-------|
| opp-001        | 4/5     | 5/5      | 4/5          | Yes      | Pass      | PASS    | Great idea |
| opp-002        | 3/5     | 3/5      | 2/5          | No       | Pass      | FAIL    | Weak monetization |
| ...            | ...     | ...      | ...          | ...      | ...       | ...     | ... |

## Statistics

- **Total Reviewed:** 50
- **Passed:** __ (Target: ≥35, 70%)
- **Failed:** __
- **Pass Rate:** __%

## Recommendation

- [ ] PASS: ≥70% of top opportunities are viable → Proceed to Phase 3
- [ ] FAIL: <70% viable → Review scoring algorithm
```

**Complete manual review:**
```bash
# Edit the review file
nano reports/manual_review_phase2.md

# Fill in ratings for all 50 opportunities
# Calculate statistics
# Make recommendation
```

---

### Step 5: Analyze Quality Results

```bash
# View quality report
cat reports/quality_report_YYYYMMDD_HHMMSS.json | python -m json.tool

# Check Tier 1 KPIs
cat reports/quality_report_YYYYMMDD_HHMMSS.json | python -m json.tool | grep -A5 "tier1_kpis"
```

---

### ✅ Phase 2 Success Criteria

**Tier 1 KPIs (MUST PASS):**
- [ ] High-Score Rate: ≥25% opportunities with score 70+ (Target: 30%)
- [ ] Function Compliance: 100% compliance with 1-3 function rule
- [ ] Market Validation: ≥85% Jina API success (Target: 90%)

**Manual Review:**
- [ ] ≥70% of top 50 opportunities rated as viable
- [ ] Manual review documented in `reports/manual_review_phase2.md`

**If all criteria met:** ✅ Proceed to Phase 3
**If any Tier 1 KPI failed:** ❌ Fix issues, see [Troubleshooting](#tier-1-kpi-failures)

---

## ⚡ Phase 3: Performance Validation (1000 Opportunities)

**Duration:** 2-3 days
**Goal:** Validate Tier 2 Performance KPIs

### Step 1: Prepare for Test

```bash
# Record start time
date > /tmp/phase3_start_time.txt

# Archive Phase 2 logs
mv logs/pipeline.log logs/pipeline_phase2.log

# Start monitoring dashboard (separate terminal)
python scripts/kpi_dashboard.py &
echo $! > /tmp/dashboard_pid.txt

# Access dashboard: http://localhost:5000
```

---

### Step 2: Execute Performance Test

```bash
# Run pipeline (1000 submissions at production pace)
uv run python main.py \
  --limit 1000 \
  --subreddits SaaS,Entrepreneur,productivity,smallbusiness,startups,SideProject

# Monitor dashboard in browser: http://localhost:5000

# Monitor logs
tail -f logs/pipeline.log
```

**Expected duration:** 1-3 hours for 1000 submissions

**Real-time monitoring:**
- Watch dashboard for live KPI updates
- Monitor cost accumulation
- Track latency percentiles
- Observe throughput metrics

---

### Step 3: Generate Performance Report

```bash
# Generate report
python scripts/generate_performance_report.py --lookback-hours 48

# Expected output:
# ⚡ TIER 2 PERFORMANCE KPIs
# ✓ cost_per_opportunity: PASS
# ✓ latency: PASS
# ✓ throughput: PASS
#
# 🤖 AGENT PERFORMANCE
# wtp        | 1.23s | $0.0012 | 99.5% success
# segment    | 0.98s | $0.0008 | 99.8% success
# ...
#
# 🎉 PERFORMANCE VALIDATION PASSED - Ready for production decision
```

**Files generated:**
- `reports/performance_report_YYYYMMDD_HHMMSS.json`

---

### Step 4: Analyze Performance Results

```bash
# View detailed agent performance
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c \
  "SELECT * FROM agent_performance_summary ORDER BY total_cost_usd DESC;"

# View cost analysis by day
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c \
  "SELECT * FROM cost_analysis ORDER BY date DESC LIMIT 7;"

# Check latency distribution
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c \
  "SELECT
     PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration_seconds) as p50,
     PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_seconds) as p95,
     PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_seconds) as p99
   FROM pipeline_metrics
   WHERE phase='transform' AND success=true;"
```

---

### Step 5: Stop Monitoring Dashboard

```bash
# Stop dashboard
kill $(cat /tmp/dashboard_pid.txt)
rm /tmp/dashboard_pid.txt
```

---

### ✅ Phase 3 Success Criteria

**Tier 2 KPIs (SHOULD PASS):**
- [ ] Cost Per Opportunity: <$0.06 (Target: <$0.05, 60% reduction)
- [ ] Analysis Latency P95: <7 seconds (Target: <5 seconds)
- [ ] Throughput: ≥800 opportunities/day (Target: 1000+/day)
- [ ] Agent Consensus Rate: ≥55% (Target: ≥60%)

**Performance Analysis:**
- [ ] No single agent has >10% failure rate
- [ ] Cost distribution is balanced across agents
- [ ] Latency is consistent (P99 < 2x P95)

**If all criteria met:** ✅ Proceed to Production Decision
**If 1-2 Tier 2 KPIs failed:** ⚠️ CONDITIONAL GO (can optimize post-launch)
**If 3+ Tier 2 KPIs failed:** ❌ Optimize before production

---

## 🎯 Production Readiness Decision

### Step 1: Aggregate All Results

```bash
# Run decision engine
python scripts/production_readiness_decision.py

# Expected output:
# ========================================
# AGGREGATING LIVE TEST RESULTS
# ========================================
#
# Phase 1: Smoke Test - Infrastructure validation
# Phase 2: Quality Validation - X/Y KPIs passed
# Phase 3: Performance Validation - X/Y KPIs passed
#
# ========================================
# FINAL DECISION: ✅ GO - Production Ready
# Confidence: 100%
# ========================================
#
# RECOMMENDATIONS:
# 1. All KPIs passed - system ready for production
# 2. Deploy with full monitoring enabled
# ...
```

**Exit code interpretation:**
- `0` = ✅ GO (Production Ready)
- `1` = ⚠️ CONDITIONAL GO (Needs Optimization)
- `2` = ❌ NO-GO (Major Issues)
- `3` = 🛑 STOP (Complete Failure)

---

### Step 2: Review Decision Report

```bash
# View decision report
cat reports/production_readiness_YYYYMMDD_HHMMSS.json | python -m json.tool

# Check decision details
cat reports/production_readiness_YYYYMMDD_HHMMSS.json | python -m json.tool | grep -A10 "decision"
```

---

### Step 3: Take Action Based on Decision

#### ✅ GO - Production Ready (Exit 0)

**Actions:**
1. Deploy to production with full monitoring
2. Set up AgentOps dashboards
3. Create production runbook
4. Schedule weekly quality reviews (first month)
5. Configure alerts for KPI degradation

**Deployment command:**
```bash
# Follow production deployment runbook
# See: docs/agno-integration/implementation/phase-5-production-testing.md
```

---

#### ⚠️ CONDITIONAL GO (Exit 1)

**Actions:**
1. Deploy with conservative rate limits
2. Monitor closely for 2 weeks
3. Create optimization roadmap (2-4 weeks)
4. Document which Tier 2 KPIs failed
5. Performance improvements can be done post-launch

**Deployment command:**
```bash
# Deploy with rate limiting
uv run python main.py --rate-limit 10 --monitor-mode strict
```

---

#### ❌ NO-GO (Exit 2)

**Actions:**
1. Fix critical Tier 1 KPI failures
2. Root cause analysis required
3. Re-run Phase 2 validation after fixes
4. Consider architecture adjustments
5. DO NOT deploy until all Tier 1 KPIs pass

**Fix and re-test:**
```bash
# Identify failures
cat reports/production_readiness_YYYYMMDD_HHMMSS.json | python -m json.tool | grep "FAIL"

# Fix issues
# See [Troubleshooting: Tier 1 KPI Failures]

# Re-run Phase 2
python scripts/generate_quality_report.py
python scripts/production_readiness_decision.py
```

---

#### 🛑 STOP (Exit 3)

**Actions:**
1. Comprehensive post-mortem required
2. Evaluate if multi-agent approach is viable
3. Consider alternative architectures
4. DO NOT proceed to production
5. Schedule architecture review meeting

**Post-mortem:**
```bash
# Document all failures
cat reports/production_readiness_YYYYMMDD_HHMMSS.json > postmortem/failures_YYYYMMDD.json

# Analyze root causes
# Create architecture redesign proposal
```

---

## 📝 Manual Review Procedures

### Manual Review Template

Use this template for Phase 2 manual review:

```markdown
# Opportunity Manual Review Form

**Opportunity ID:** opp-XXXXX
**Reviewer:** [Name/ID]
**Date:** YYYY-MM-DD

## 1. Problem Clarity (1-5)

**Question:** Is the problem clearly articulated?

- [ ] 5 - Crystal clear, well-defined problem
- [ ] 4 - Clear problem with minor ambiguity
- [ ] 3 - Somewhat clear, needs clarification
- [ ] 2 - Vague problem statement
- [ ] 1 - Unclear or missing problem

**Rating:** __/5

**Notes:** _______________

---

## 2. Target Audience (1-5)

**Question:** Is the target audience well-defined?

- [ ] 5 - Specific demographic/psychographic profile
- [ ] 4 - Clear audience with minor gaps
- [ ] 3 - General audience description
- [ ] 2 - Vague audience
- [ ] 1 - No defined audience

**Rating:** __/5

**Notes:** _______________

---

## 3. Monetization Viability (1-5)

**Question:** Is the monetization path realistic?

- [ ] 5 - Proven model, clear willingness to pay
- [ ] 4 - Realistic model with minor risks
- [ ] 3 - Possible but uncertain
- [ ] 2 - Weak monetization strategy
- [ ] 1 - No clear path to revenue

**Rating:** __/5

**Notes:** _______________

---

## 4. Market Evidence (Yes/No)

**Question:** Is there supporting market data?

- [ ] Yes - URLs, data, validation present
- [ ] No - No market evidence

**Evidence URLs:** _______________

---

## 5. Function Simplicity (Pass/Fail)

**Question:** Does it have 1-3 focused functions?

- [ ] PASS - 1-3 functions, clearly focused
- [ ] FAIL - 4+ functions OR unfocused

**Function Count:** __
**Functions:**
1. _______________
2. _______________
3. _______________

---

## 6. Overall Viability (Pass/Fail)

**Question:** Would you greenlight this opportunity?

- [ ] PASS - Worth pursuing
- [ ] FAIL - Not viable

**Final Decision:** ______

**Confidence (1-5):** __/5

**Summary Notes:**
_______________
_______________

---

## Red Flags Checklist

- [ ] Over-engineered solution
- [ ] No clear target market
- [ ] Unrealistic pricing
- [ ] Too similar to existing products
- [ ] Requires significant user behavior change
- [ ] Long time-to-value

**Red Flags Found:** ______

---

## Recommendations

**If PASS:**
- Priority: High / Medium / Low
- Suggested next steps: _______________

**If FAIL:**
- Reason for rejection: _______________
- Could be salvaged if: _______________
```

---

### Batch Review Process

**For 50 opportunities:**

1. **Prepare workspace:**
```bash
mkdir -p reports/manual_reviews
cd reports/manual_reviews
```

2. **Create review log:**
```bash
cat > review_log_YYYYMMDD.csv << 'EOF'
id,problem_rating,audience_rating,monetization_rating,market_evidence,function_compliance,overall_viability,confidence,notes
EOF
```

3. **Review each opportunity:**
   - Open CSV file with opportunities
   - For each row, fill out manual review form
   - Record results in review_log CSV

4. **Calculate statistics:**
```bash
# Count passes/fails
awk -F',' 'NR>1 {if($7=="PASS") pass++; else fail++} END {print "Pass:"pass" Fail:"fail" Rate:"(pass/(pass+fail)*100)"%"}' review_log_YYYYMMDD.csv
```

5. **Document findings:**
```bash
# Create summary
cat > manual_review_summary_YYYYMMDD.md << 'EOF'
# Manual Review Summary

**Date:** YYYY-MM-DD
**Total Reviewed:** 50
**Pass Rate:** XX%

## Key Findings
- ...

## Recommendations
- ...
EOF
```

---

## 🔧 Troubleshooting Guide

### Common Issues and Solutions

#### Database Connection Failed

**Symptom:**
```
Error: could not connect to server: Connection refused
```

**Solution:**
```bash
# Check if Supabase is running
docker ps | grep supabase

# Start Supabase if not running
cd /home/carlos/projects/redditharbor-core-functions-fix
supabase start

# Wait 30 seconds
sleep 30

# Verify connection
psql -h 127.0.0.1 -p 54322 -U postgres -c "SELECT 1;"
```

---

#### Migration Failed

**Symptom:**
```
Error: relation "pipeline_metrics" already exists
```

**Solution:**
```bash
# Check if table exists
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c "\dt pipeline_metrics"

# If exists, drop and recreate
./scripts/apply_metrics_migration.sh
# Answer "y" when prompted to drop existing table
```

---

#### Missing Configuration

**Symptom:**
```
Error: REDDIT_CLIENT_ID not set
```

**Solution:**
```bash
# Check .env.local exists
ls -la /home/carlos/projects/redditharbor-core-functions-fix/.env.local

# If missing, create from template
cp .env.example .env.local

# Edit with required values
nano .env.local

# Verify
python -c "from config import get_settings; s = get_settings(); print('OK' if s.reddit_client_id else 'FAIL')"
```

---

#### No Opportunities Created

**Symptom:**
```
Pipeline completed but opportunity count = 0
```

**Solution:**
```bash
# Check pipeline logs
tail -100 logs/pipeline.log | grep -i error

# Check if Reddit API is accessible
python -c "import praw; r = praw.Reddit(...); print(r.subreddit('test').display_name)"

# Check if LLM is accessible
python -c "from transform import get_analyzer; a = get_analyzer(); print('OK')"

# Run in debug mode
uv run python main.py --limit 1 --debug
```

---

#### High Error Rate (>5%)

**Symptom:**
```
✗ Error rate: 8.50% (> 5.00%)
```

**Solution:**
```bash
# Check error messages
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c \
  "SELECT agent_name, error_message, COUNT(*)
   FROM pipeline_metrics
   WHERE success=false
   GROUP BY agent_name, error_message
   ORDER BY COUNT(*) DESC
   LIMIT 10;"

# Common causes:
# - API rate limiting → Add delays between requests
# - Timeout errors → Increase timeout settings
# - Invalid responses → Check LLM output parsing
```

---

#### Function Compliance Failures

**Symptom:**
```
✗ function_compliance: FAIL
Violations: 25 apps with 4+ functions
```

**Solution:**
```bash
# Check SimplicitiyProcessor logic
grep -n "function_count" pipeline-v3/transform/simplicity_processor.py

# Verify score-driven reduction is active
python -c "from transform.simplicity_processor import SimplicitiyProcessor; print(SimplicitiyProcessor.__doc__)"

# Review violating opportunities
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c \
  "SELECT id, app_title, jsonb_array_length(core_functions) as func_count, final_score
   FROM opportunities
   WHERE jsonb_array_length(core_functions) > 3
   LIMIT 10;"

# Fix: Update SimplicitiyProcessor to enforce 3-function max
# See: transform/simplicity_processor.py
```

---

#### Low High-Score Rate (<25%)

**Symptom:**
```
✗ high_score_rate: FAIL
Rate: 18.5% (< 25% threshold)
```

**Solution:**
```bash
# Analyze score distribution
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c \
  "SELECT
     MIN(final_score) as min,
     AVG(final_score) as avg,
     MAX(final_score) as max,
     PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY final_score) as median
   FROM opportunities
   WHERE created_at >= NOW() - INTERVAL '24 hours';"

# Common causes:
# - Scoring weights need adjustment
# - Quality filter too aggressive
# - Subreddit selection (low-quality sources)

# Fix: Adjust scoring weights in transform/agno_synthesis.py
# Or: Use higher-quality subreddits
```

---

#### Dashboard Not Loading

**Symptom:**
```
Browser shows "Connection refused" at localhost:5000
```

**Solution:**
```bash
# Check if dashboard is running
ps aux | grep kpi_dashboard

# If not running, start it
python scripts/kpi_dashboard.py &

# Check port is available
lsof -i :5000

# If port in use, kill process
kill $(lsof -t -i:5000)

# Restart dashboard
python scripts/kpi_dashboard.py &

# Access: http://localhost:5000
```

---

### Tier 1 KPI Failures

#### High-Score Rate < 25%

**Root Causes:**
1. Scoring algorithm too conservative
2. Low-quality source subreddits
3. Market validation failing frequently

**Solutions:**
1. Review and adjust scoring weights
2. Select higher-quality subreddits (r/SaaS, r/Entrepreneur)
3. Check Jina API success rate

---

#### Function Compliance < 100%

**Root Causes:**
1. SimplicitiyProcessor not enforcing limit
2. Score-driven reduction not working
3. LLM generating 4+ functions

**Solutions:**
1. Verify SimplicitiyProcessor logic
2. Check score thresholds (70/60 for 3/2 functions)
3. Add hard constraint in validator

---

#### Market Validation < 85%

**Root Causes:**
1. Jina API rate limiting
2. Network connectivity issues
3. Invalid search queries

**Solutions:**
1. Implement request throttling
2. Check network connection
3. Review query formatting logic

---

## 🔄 Rollback Procedures

### Rollback Database Migration

**If metrics migration causes issues:**

```bash
# Connect to database
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres

# Drop metrics table and views
DROP TABLE IF EXISTS pipeline_metrics CASCADE;
DROP VIEW IF EXISTS pipeline_phase_summary;
DROP VIEW IF EXISTS agent_performance_summary;
DROP VIEW IF EXISTS cost_analysis;

# Exit
\q

# Verify rollback
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c "\dt pipeline_metrics"
# Expected: "Did not find any relation named 'pipeline_metrics'"
```

---

### Rollback Code Changes

**If metrics integration causes pipeline failures:**

```bash
# Backup current state
cd /home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3
git stash save "Metrics integration backup"

# List files modified
git diff HEAD --name-only

# Restore original files
git checkout HEAD -- transform/agno_analyzer.py
git checkout HEAD -- transform/agno_agents.py
git checkout HEAD -- orchestration/pipeline_orchestrator.py

# Verify pipeline works
uv run python main.py --limit 5 --test-mode
```

---

### Restore Backup Data

**If test data corrupts production opportunities:**

```bash
# Check if backup exists
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c "\dt *backup*"

# Restore from backup (if exists)
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c \
  "INSERT INTO opportunities SELECT * FROM app_opportunities_backup_20251127_154500
   ON CONFLICT DO NOTHING;"

# Verify restoration
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c "SELECT COUNT(*) FROM opportunities;"
```

---

### Emergency Stop

**If pipeline is consuming excessive resources:**

```bash
# Find pipeline process
ps aux | grep "python main.py"

# Kill process
kill -9 <PID>

# Stop dashboard
kill $(cat /tmp/dashboard_pid.txt 2>/dev/null)

# Check database connections
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c \
  "SELECT pid, query FROM pg_stat_activity WHERE datname='postgres';"

# Kill hanging connections if needed
# (Replace <PID> with actual process ID)
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c "SELECT pg_terminate_backend(<PID>);"
```

---

## 📚 Additional Resources

### Related Documentation

- [Live Test Implementation Summary](LIVE_TEST_IMPLEMENTATION_SUMMARY.md)
- [Agno Integration README](agno-integration/README.md)
- [Phase 5 Production Testing](agno-integration/implementation/phase-5-production-testing.md)
- [Database Schema Documentation](agno-integration/implementation/phase-4-database-schema.md)

### Memory Recall

```python
# Recall live test plan from memory
from mcp__memorygraph import recall_memories

recall_memories(query="Pipeline v3 live test KPI")
# Returns: KPI framework, test plan, metrics schema, baseline strategy
```

### Script Reference

| Script | Purpose | Exit Codes |
|--------|---------|------------|
| `validate_smoke_test.py` | Phase 1 validation | 0=PASS, 1=FAIL |
| `generate_quality_report.py` | Phase 2 analysis | 0=PASS, 1=FAIL |
| `generate_performance_report.py` | Phase 3 analysis | 0=PASS, 1=FAIL |
| `production_readiness_decision.py` | Final decision | 0=GO, 1=CONDITIONAL, 2=NO-GO, 3=STOP |
| `kpi_dashboard.py` | Real-time monitoring | N/A (runs as server) |

---

## ✅ Final Checklist

Before executing live tests, verify:

- [ ] All pre-flight checks passed
- [ ] Database migration applied successfully
- [ ] Metrics integration tested and verified
- [ ] Python dependencies installed
- [ ] Configuration validated
- [ ] Disk space available (≥5GB)
- [ ] Logs and reports directories created
- [ ] Backup procedures documented
- [ ] Rollback procedures tested
- [ ] This execution guide reviewed completely

**⚠️ Only proceed if ALL items are checked!**

---

**Document Version:** 1.0
**Last Updated:** 2025-12-05
**Maintainer:** RedditHarbor Engineering Team
**Status:** Production Ready

---

**AI Execution Note:** This guide is designed to be executed autonomously by AI agents. Each step includes expected outputs, error handling, and rollback procedures. Follow sequentially and do not skip steps.
