# Hybrid Strategy E2E Testing Guide

**Enhanced Testing Chunk - Production Integration**
**RedditHarbor E2E Guide - Hybrid Strategy Validation**
**Generated:** 2025-11-15

## 🎯 Chunk Overview

- **Semantic Theme:** hybrid_strategy_testing
- **Complexity Level:** advanced
- **Content Focus:** LLM Monetization + Lead Extraction E2E Testing
- **Testing Path:** Implementation → Production
- **Time Commitment:** 30-45 minutes

## 📋 What is the Hybrid Strategy?

The **Hybrid Strategy** combines two powerful approaches to maximize value from Reddit opportunity data:

### **Option A: LLM-Enhanced Monetization Scoring**
- Uses DSPy-powered LLM analysis for intelligent monetization assessment
- Fixes false positives (understands "NOT willing to pay")
- B2B/B2C differentiation with proper weighting
- Subreddit purchasing power multipliers
- Cost: ~$0.01 per analysis (GPT-4o-mini) or ~$0.002 (Claude Haiku 4.5)

### **Option B: Customer Lead Extraction**
- Zero-cost regex-based lead extraction
- Extracts: Reddit username, budget signals, competitor mentions, team size, urgency
- Buying intent stage classification (awareness → evaluation → ready_to_buy)
- Slack alerts for hot leads (score ≥ 75 + high/critical urgency)
- 10-100x bigger revenue opportunity than Option A

### **Why Hybrid?**
Run both strategies in parallel on high-scoring opportunities (≥60):
- **App ideas** for productization (Option A)
- **Sales leads** for B2B outreach (Option B)
- Same data collection, double the value extraction

---

## 🧪 E2E Testing Strategy

### **Testing Objectives**

1. **Functional Validation**
   - LLM analyzer correctly processes Reddit posts
   - Lead extractor identifies budget signals, competitors, urgency
   - Both results stored to database via DLT
   - Slack alerts fire for hot leads

2. **Performance Validation**
   - LLM API latency and cost tracking
   - Database write performance (DLT merge disposition)
   - End-to-end processing time (collection → analysis → storage)

3. **Quality Validation**
   - LLM scoring accuracy vs keyword baseline
   - Lead extraction precision (no false positives)
   - Database integrity (no duplicates, proper schema)

---

## 🚀 Quick Start E2E Test (15 minutes)

### **Step 1: Environment Setup**

```bash
cd /home/user/redditharbor

# Ensure dependencies installed
uv sync

# Configure environment (copy from .env.example)
cat >> .env.local <<EOF
# Hybrid Strategy Configuration
MONETIZATION_LLM_ENABLED=true
MONETIZATION_LLM_THRESHOLD=60.0
OPENROUTER_API_KEY=your_actual_key_here

LEAD_EXTRACTION_ENABLED=true
LEAD_EXTRACTION_THRESHOLD=60.0
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
EOF
```

### **Step 2: Database Migration**

```bash
# Run hybrid strategy migrations
psql $DATABASE_URL -f supabase/migrations/20251114200000_add_customer_leads_table.sql
psql $DATABASE_URL -f supabase/migrations/20251114200001_add_llm_monetization_analysis.sql

# Verify tables created
psql $DATABASE_URL -c "\dt customer_*"
psql $DATABASE_URL -c "\dt llm_*"
```

### **Step 3: Run Test Script**

```bash
# Test with high-score examples
python scripts/testing/test_hybrid_strategy_with_high_scores.py

# Expected output:
# ✅ LLM monetization analysis: 5-10 analyses
# ✅ Lead extraction: 5-10 leads with budget/competitor data
# ✅ Database writes: All records via DLT merge
# ✅ Slack alerts: 2-3 hot leads (if configured)
```

### **Step 4: Verify Results**

```bash
# Check lead extraction results
psql $DATABASE_URL -c "
  SELECT reddit_username, competitor_mentioned, budget_mentioned, lead_score
  FROM customer_leads
  ORDER BY lead_score DESC
  LIMIT 10;
"

# Check LLM monetization results
psql $DATABASE_URL -c "
  SELECT opportunity_id, llm_monetization_score, keyword_monetization_score, score_delta
  FROM llm_monetization_analysis
  ORDER BY ABS(score_delta) DESC
  LIMIT 10;
"

# Run monitoring dashboard
python scripts/analysis/monitor_hybrid_strategy.py
```

---

## 🔬 Advanced Testing Scenarios

### **Scenario 1: Full Pipeline Integration Test**

Test the complete workflow from collection to storage:

```bash
# Phase 1: Collect Reddit data (DLT)
python scripts/dlt/dlt_trust_pipeline.py --limit 10

# Phase 2: Run batch scoring with hybrid strategy
python scripts/core/batch_opportunity_scoring.py

# Phase 3: Verify hybrid results
python scripts/analysis/monitor_hybrid_strategy.py
```

**Expected Results:**
- Posts with score ≥ 60: ~5-10 per run
- LLM analyses: Same count as posts ≥ 60
- Lead extractions: Same count as posts ≥ 60
- Database records: All stored via DLT merge (no duplicates)
- Cost: ~$0.05-0.10 per batch (10 analyses × $0.01)

### **Scenario 2: Cost Optimization Testing**

Compare different LLM providers:

```bash
# Test 1: OpenAI GPT-4o-mini (baseline)
export MONETIZATION_LLM_MODEL="openai/gpt-4o-mini"
python scripts/testing/test_hybrid_strategy_with_high_scores.py

# Test 2: Claude Haiku 4.5 via OpenRouter (cheaper)
export MONETIZATION_LLM_MODEL="anthropic/claude-3-5-haiku-20241022"
python scripts/testing/test_hybrid_strategy_with_high_scores.py

# Compare costs in monitoring dashboard
python scripts/analysis/monitor_hybrid_strategy.py
```

**Expected Savings:**
- GPT-4o-mini: ~$0.01 per analysis
- Claude Haiku 4.5: ~$0.002 per analysis (5x cheaper)
- Monthly cost (1000 analyses): $10 vs $2

### **Scenario 3: Lead Quality Validation**

Test lead extraction precision:

```bash
# Run test with known high-quality leads
python scripts/testing/test_hybrid_strategy_with_high_scores.py

# Verify lead quality
psql $DATABASE_URL -c "
  SELECT
    reddit_username,
    budget_mentioned,
    competitor_mentioned,
    buying_intent_stage,
    urgency_level,
    lead_score
  FROM customer_leads
  WHERE lead_score >= 70
  ORDER BY lead_score DESC;
"
```

**Quality Metrics:**
- Budget detection accuracy: >90%
- Competitor identification: >80%
- Buying intent classification: >85%
- False positive rate: <5%

### **Scenario 4: Slack Alert Testing**

Validate hot lead alerting:

```bash
# Configure Slack webhook
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Enable lead extraction
export LEAD_EXTRACTION_ENABLED=true

# Run pipeline
python scripts/core/batch_opportunity_scoring.py

# Check Slack channel for alerts
# Expected: Alerts for leads with:
#   - Lead score >= 75
#   - Urgency: high or critical
```

### **Scenario 5: Performance Benchmarking**

Measure end-to-end performance:

```bash
# Run with performance tracking
time python scripts/core/batch_opportunity_scoring.py > batch_output.log

# Analyze performance
grep "LLM analysis time" batch_output.log
grep "Lead extraction time" batch_output.log
grep "Database write time" batch_output.log

# Expected timings:
# - LLM analysis: 1-3 seconds per opportunity
# - Lead extraction: <100ms per opportunity
# - Database writes: <500ms total (DLT batching)
```

---

## 📊 Testing Validation Metrics

### **Functional Metrics**

| Component | Test | Success Criteria |
|-----------|------|------------------|
| **LLM Analyzer** | Process 10 posts | 100% success rate |
| **Lead Extractor** | Extract from 10 posts | ≥80% budget detection |
| **DLT Storage** | Write to database | Zero duplicates, 100% integrity |
| **Slack Alerts** | Hot lead notification | Alerts fire within 5 seconds |

### **Performance Metrics**

| Metric | Target | Measurement |
|--------|--------|-------------|
| **LLM Latency** | <3 sec/analysis | OpenRouter API response time |
| **Extraction Speed** | <100ms/post | Regex processing time |
| **Database Write** | <500ms batch | DLT merge write time |
| **End-to-End** | <5 min/batch | Collection → storage |

### **Quality Metrics**

| Quality Check | Target | Validation Method |
|---------------|--------|-------------------|
| **LLM Accuracy** | ±10 points from baseline | Score delta analysis |
| **Lead Precision** | >90% budget detection | Manual verification |
| **Schema Integrity** | 100% valid records | Database constraints |
| **Cost Efficiency** | <$0.01/analysis | Cost tracking queries |

---

## 🔍 Troubleshooting Common Issues

### **Issue 1: LLM API Failures**

**Symptoms:**
- `OpenAI API error: 401 Unauthorized`
- `Module 'dspy' not found`

**Solutions:**
```bash
# Check API key
echo $OPENROUTER_API_KEY  # Should not be empty

# Verify dspy installed
python -c "import dspy; print(dspy.__version__)"

# Reinstall if needed
uv sync --reinstall
```

### **Issue 2: Database Migration Errors**

**Symptoms:**
- `relation "customer_leads" already exists`
- Foreign key constraint violations

**Solutions:**
```bash
# Check existing tables
psql $DATABASE_URL -c "\dt customer_*"

# Drop and recreate if needed (CAUTION: loses data)
psql $DATABASE_URL -c "DROP TABLE IF EXISTS customer_leads CASCADE;"
psql $DATABASE_URL -f supabase/migrations/20251114200000_add_customer_leads_table.sql
```

### **Issue 3: Slack Alerts Not Firing**

**Symptoms:**
- No Slack notifications for hot leads

**Solutions:**
```bash
# Verify webhook URL
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test from RedditHarbor"}'

# Check lead scores
psql $DATABASE_URL -c "SELECT COUNT(*) FROM customer_leads WHERE lead_score >= 75 AND urgency_level IN ('high', 'critical');"

# Verify configuration
echo $LEAD_EXTRACTION_ENABLED  # Should be "true"
```

### **Issue 4: DLT Deduplication Not Working**

**Symptoms:**
- Duplicate records in database
- `unique constraint violation` errors

**Solutions:**
```bash
# Check DLT configuration in batch_opportunity_scoring.py
grep -A 5 "@dlt.resource.*write_disposition" scripts/core/batch_opportunity_scoring.py

# Should see: write_disposition="merge"
# Verify primary merge keys are set correctly

# Clean duplicates manually (if needed)
psql $DATABASE_URL -c "
  DELETE FROM customer_leads a USING customer_leads b
  WHERE a.id > b.id AND a.reddit_post_id = b.reddit_post_id;
"
```

---

## 📈 Production Deployment Checklist

### **Pre-Deployment**

- [ ] All E2E tests passing (100% success rate)
- [ ] Database migrations applied successfully
- [ ] Environment variables configured (.env.local)
- [ ] API keys validated (OpenRouter/OpenAI)
- [ ] Slack webhook tested (if using alerts)
- [ ] Cost limits configured ($100/month recommended)

### **Deployment**

- [ ] Dependencies installed (`uv sync`)
- [ ] Database backup created
- [ ] Monitoring dashboard accessible
- [ ] Error alerting configured
- [ ] Performance benchmarks documented

### **Post-Deployment**

- [ ] Monitor first 24 hours (check logs, costs, errors)
- [ ] Validate lead quality (manual spot-check)
- [ ] Verify Slack alerts working
- [ ] Review cost tracking (should be <$10/day)
- [ ] Check database growth (disk space)

---

## 🤖 Agent Integration

### **Hybrid Strategy Testing Agent**

Located at: `docs/e2e-testing-guide/agents/hybrid-strategy-testing-agent.py`

**Functions:**
- `test_llm_monetization()` - Validate LLM analyzer
- `test_lead_extraction()` - Validate lead extractor
- `test_database_integration()` - Validate DLT storage
- `test_slack_alerts()` - Validate notification system
- `generate_test_report()` - Comprehensive test results
- `monitor_costs()` - Track LLM API costs
- `validate_quality()` - Check lead precision

**Usage:**
```python
from docs.e2e_testing_guide.agents.hybrid_strategy_testing_agent import HybridStrategyTestAgent

agent = HybridStrategyTestAgent()
report = agent.run_full_test_suite()
print(report.summary())
```

---

## 🔗 Integration with RedditHarbor

### **Related Documentation**

- **[Hybrid Strategy Integration Guide](../../guides/development-operations/hybrid-strategy-integration-guide.md)** - Complete implementation guide
- **[Option B Workflow Integration](../../guides/development-operations/option-b-workflow-integration.md)** - Lead extraction workflow
- **[DLT Activity Validation](./dlt-activity-validation-system.md)** - DLT testing fundamentals
- **[Advanced Testing Scenarios](./advanced-testing-scenarios.md)** - Performance benchmarking

### **CLI Integration**

```bash
# Run hybrid strategy tests
doit test_hybrid_strategy
doit monitor_hybrid_costs
doit validate_leads

# Production monitoring
doit monitor_hybrid_dashboard
```

### **Workflow Integration**

The hybrid strategy integrates seamlessly with existing workflows:

```bash
# Before (traditional workflow)
python scripts/dlt/dlt_trust_pipeline.py
python scripts/core/batch_opportunity_scoring.py

# After (hybrid strategy enabled)
# Same commands, just set environment variables:
export MONETIZATION_LLM_ENABLED=true
export LEAD_EXTRACTION_ENABLED=true

python scripts/dlt/dlt_trust_pipeline.py
python scripts/core/batch_opportunity_scoring.py
# Now extracts BOTH app ideas AND sales leads!
```

---

## 💰 Cost Analysis & ROI

### **Expected Costs (Monthly)**

Based on 1000 opportunities analyzed per month:

| Component | Unit Cost | Volume | Monthly Cost |
|-----------|-----------|--------|--------------|
| **LLM Analysis (GPT-4o-mini)** | $0.01 | 1000 | $10 |
| **LLM Analysis (Claude Haiku)** | $0.002 | 1000 | $2 |
| **Lead Extraction** | $0 | 1000 | $0 |
| **Slack Alerts** | $0 | ~50 alerts | $0 |
| **Database Storage** | ~$0.001/GB | <1GB | $0 |

**Total Monthly Cost:** $2-10 (depending on LLM choice)

### **Expected Revenue Potential**

**Option A (App Ideas):**
- SaaS pricing: $29-99/mo
- At 100 customers: $3-10k MRR

**Option B (Sales Leads):**
- B2B SaaS pricing: $499-4999/mo
- At 100 customers: $50-500k MRR

**ROI:** 10-100x Option A, 500-50,000x Option B

---

## ✅ Testing Checklist

### **Functional Testing**
- [ ] LLM analyzer processes posts correctly
- [ ] Lead extractor identifies budget signals
- [ ] Lead extractor identifies competitors
- [ ] Lead extractor classifies buying intent
- [ ] DLT writes to customer_leads table
- [ ] DLT writes to llm_monetization_analysis table
- [ ] Slack alerts fire for hot leads
- [ ] No duplicate records in database

### **Performance Testing**
- [ ] LLM latency <3 seconds per analysis
- [ ] Lead extraction <100ms per post
- [ ] Database writes <500ms per batch
- [ ] End-to-end pipeline <5 minutes

### **Quality Testing**
- [ ] LLM scoring within ±10 points of baseline
- [ ] Budget detection accuracy >90%
- [ ] Competitor identification >80%
- [ ] Buying intent classification >85%
- [ ] False positive rate <5%

### **Production Readiness**
- [ ] All migrations applied
- [ ] Environment variables configured
- [ ] API keys validated
- [ ] Error handling tested
- [ ] Monitoring dashboard working
- [ ] Cost tracking enabled

---

## 🎯 Next Steps

1. **Complete Quick Start Test** - Run 15-minute validation
2. **Review Test Results** - Check monitoring dashboard
3. **Tune Configuration** - Adjust thresholds based on results
4. **Deploy to Production** - Follow deployment checklist
5. **Monitor & Iterate** - Track costs, quality, and ROI

---

**Testing Validation:** This chunk covers comprehensive E2E testing for the RedditHarbor Hybrid Strategy, validated through real-world implementation and production deployment.

**Last Updated:** 2025-11-15
**Complexity Level:** Advanced
**Time Commitment:** 30-45 minutes
**Prerequisites:** DLT Activity Validation, System Architecture Overview
