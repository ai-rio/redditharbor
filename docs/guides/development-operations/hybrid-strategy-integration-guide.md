# RedditHarbor Hybrid Strategy Integration Guide

Complete guide for implementing both **Option A** (enhanced monetization scoring) and **Option B** (customer lead generation) in your existing pipeline.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Database Setup](#database-setup)
4. [Option A Integration](#option-a-integration)
5. [Option B Integration](#option-b-integration)
6. [Hybrid Implementation](#hybrid-implementation)
7. [Testing](#testing)
8. [Cost Estimates](#cost-estimates)
9. [Monitoring](#monitoring)

---

## 🎯 Overview

### What Was Built

**Option A: Enhanced Monetization Scoring**
- `agent_tools/monetization_llm_analyzer.py` - DSPy-powered LLM analyzer
- Fixes false positives from keyword matching
- Proper B2B/B2C weighting (B2B 35%, B2C 15%)
- Price extraction, sentiment analysis, subreddit context

**Option B: Customer Lead Generation**
- `core/lead_extractor.py` - Regex-based lead extraction
- Extracts: Reddit username, budget, competitor, team size, urgency
- Simple extraction (no complex AI needed)
- 10-100x bigger revenue opportunity ($499-4999/mo vs $29-99/mo)

### Key Insight

**You're already collecting all the data needed for both options!**

Your existing pipeline collects:
```json
{
  "author": "startup_cto_42",  // THE LEAD (Option B)
  "text": "Paying $360/month for Asana...",  // Budget + competitor
  "subreddit": "projectmanagement"
}
```

You just need to:
- **Option A**: Run LLM analysis on text
- **Option B**: Extract lead-specific fields

**Same data. Same pipeline. Different extraction.**

---

## 🏗️ Architecture

### Current Pipeline (Simplified)

```
1. collect_problem_posts()               (DLT collection)
2. OpportunityAnalyzerAgent.analyze()     (Keyword 5D scoring)
3. EnhancedLLMProfiler.generate()         (AI profiles for ≥40)
4. DLT load → workflow_results            (Merge disposition)
```

### Enhanced Pipeline (Hybrid Strategy)

```
1. collect_problem_posts()               (DLT collection)
2. OpportunityAnalyzerAgent.analyze()     (Keyword 5D scoring)
   │
   ├─→ 2a. Extract leads (Option B)          ← NEW
   │      └→ Load to customer_leads table
   │
   └─→ 2b. LLM monetization (Option A)       ← NEW
          └→ Load to llm_monetization_analysis table

3. EnhancedLLMProfiler.generate()         (AI profiles for ≥40)
4. DLT load → workflow_results            (Merge disposition)
```

**Key Points:**
- ✅ Non-breaking: Existing pipeline continues to work
- ✅ Parallel: Options A and B run independently
- ✅ Selective: Only run on high-scoring opportunities (cost control)
- ✅ DLT-compatible: Uses same merge disposition pattern

---

## 💾 Database Setup

### Step 1: Run Migrations

```bash
# Option B: Customer leads table
psql $DATABASE_URL -f supabase/migrations/20251114200000_add_customer_leads_table.sql

# Option A: LLM monetization tracking
psql $DATABASE_URL -f supabase/migrations/20251114200001_add_llm_monetization_analysis.sql
```

### Step 2: Verify Tables Created

```sql
-- Check Option B tables
SELECT * FROM customer_leads LIMIT 1;
SELECT * FROM customer_companies LIMIT 1;

-- Check Option A table
SELECT * FROM llm_monetization_analysis LIMIT 1;

-- Check views
SELECT * FROM hot_leads LIMIT 5;
SELECT * FROM high_monetization_opportunities LIMIT 5;
```

---

## 🔧 Option A Integration

### Enhanced Monetization Scoring with LLM

**When to use:** After keyword scoring, before AI profile generation
**Cost:** ~$0.01 per analysis with gpt-4o-mini
**Filters:** Only run on opportunities with score ≥ 60 (cost control)

### Integration Point 1: `batch_opportunity_scoring.py`

Add after line ~650 (after `agent.analyze_opportunity()`):

```python
from agent_tools.monetization_llm_analyzer import MonetizationLLMAnalyzer

# Initialize analyzer (do this once, outside the loop)
llm_analyzer = MonetizationLLMAnalyzer(model="openai/gpt-4o-mini")

# In your processing loop, after keyword analysis:
analysis = agent.analyze_opportunity(formatted)
final_score = analysis.get("final_score", 0)
keyword_mon_score = analysis.get("monetization_potential", 0)

# NEW: Run LLM analysis on mid-high scorers
if final_score >= 60:  # Cost control threshold
    try:
        llm_result = llm_analyzer.analyze(
            text=formatted["text"],
            subreddit=formatted["subreddit"],
            keyword_monetization_score=keyword_mon_score
        )

        # Update monetization score with LLM result
        analysis["monetization_potential"] = llm_result.llm_monetization_score
        analysis["customer_segment"] = llm_result.customer_segment
        analysis["llm_analysis"] = {
            "willingness_to_pay": llm_result.willingness_to_pay_score,
            "payment_sentiment": llm_result.sentiment_toward_payment,
            "price_points": llm_result.mentioned_price_points,
            "urgency": llm_result.urgency_level,
            "confidence": llm_result.confidence
        }

        # Store LLM analysis separately for tracking
        llm_analysis_record = {
            "opportunity_id": analysis["opportunity_id"],
            "submission_id": formatted["id"],
            "llm_monetization_score": llm_result.llm_monetization_score,
            "keyword_monetization_score": keyword_mon_score,
            "customer_segment": llm_result.customer_segment,
            "willingness_to_pay_score": llm_result.willingness_to_pay_score,
            "price_sensitivity_score": llm_result.price_sensitivity_score,
            "revenue_potential_score": llm_result.revenue_potential_score,
            "payment_sentiment": llm_result.sentiment_toward_payment,
            "urgency_level": llm_result.urgency_level,
            "existing_payment_behavior": llm_result.existing_payment_behavior,
            "mentioned_price_points": llm_result.mentioned_price_points,
            "payment_friction_indicators": llm_result.payment_friction_indicators,
            "confidence": llm_result.confidence,
            "reasoning": llm_result.reasoning,
            "subreddit_multiplier": llm_result.subreddit_multiplier,
            "model_used": "openai/gpt-4o-mini",
            "score_delta": llm_result.llm_monetization_score - keyword_mon_score
        }

        # Load to database via DLT (add to your pipeline resources)
        # Or insert directly if not using DLT for this table

    except Exception as e:
        logger.warning(f"LLM analysis failed for {analysis['opportunity_id']}: {e}")
        # Continue with keyword score
```

### Configuration

Add to `.env`:
```bash
# Option A: LLM Monetization Analyzer
MONETIZATION_LLM_ENABLED=true
MONETIZATION_LLM_THRESHOLD=60.0  # Only analyze opportunities ≥ 60
MONETIZATION_LLM_MODEL=openai/gpt-4o-mini
```

---

## 👥 Option B Integration

### Customer Lead Extraction

**When to use:** After scoring, in parallel with Option A
**Cost:** $0 (regex-based, no API calls)
**Filters:** Only extract from opportunities with score ≥ 60

### Integration Point 1: `batch_opportunity_scoring.py`

Add in the same location as Option A:

```python
from core.lead_extractor import LeadExtractor, convert_to_database_record

# Initialize extractor (do this once, outside the loop)
lead_extractor = LeadExtractor()

# In your processing loop, after keyword analysis:
analysis = agent.analyze_opportunity(formatted)
final_score = analysis.get("final_score", 0)

# NEW: Extract lead data
if final_score >= 60:  # Quality threshold
    try:
        # Convert submission to post format
        post = {
            "id": formatted["id"],
            "author": formatted.get("author", "unknown"),
            "title": formatted["title"],
            "selftext": formatted["text"],
            "subreddit": formatted["subreddit"],
            "created_utc": formatted.get("created_utc")
        }

        # Extract lead signals
        lead = lead_extractor.extract_from_reddit_post(
            post=post,
            opportunity_score=final_score
        )

        # Convert to database record
        lead_record = convert_to_database_record(lead)

        # Load to customer_leads table via DLT
        # Or insert directly

        # Optional: Send Slack alert for hot leads
        if lead.urgency_level in ['high', 'critical'] and lead.lead_score >= 75:
            from core.lead_extractor import format_lead_for_slack
            slack_msg = format_lead_for_slack(lead)
            # Send to Slack webhook

    except Exception as e:
        logger.warning(f"Lead extraction failed for {formatted['id']}: {e}")
```

### Configuration

Add to `.env`:
```bash
# Option B: Lead Extraction
LEAD_EXTRACTION_ENABLED=true
LEAD_EXTRACTION_THRESHOLD=60.0
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

## 🚀 Hybrid Implementation

### Run Both in Parallel

```python
from agent_tools.monetization_llm_analyzer import MonetizationLLMAnalyzer
from core.lead_extractor import LeadExtractor, convert_to_database_record

# Initialize once
llm_analyzer = MonetizationLLMAnalyzer()
lead_extractor = LeadExtractor()

# In processing loop
analysis = agent.analyze_opportunity(formatted)
final_score = analysis.get("final_score", 0)

if final_score >= 60:
    # Run BOTH in parallel
    results = {}

    # Option A: LLM monetization
    try:
        llm_result = llm_analyzer.analyze(
            text=formatted["text"],
            subreddit=formatted["subreddit"]
        )
        results['llm_analysis'] = llm_result
    except Exception as e:
        logger.warning(f"LLM analysis failed: {e}")

    # Option B: Lead extraction
    try:
        post = {
            "id": formatted["id"],
            "author": formatted.get("author", "unknown"),
            "title": formatted["title"],
            "selftext": formatted["text"],
            "subreddit": formatted["subreddit"],
            "created_utc": formatted.get("created_utc")
        }
        lead = lead_extractor.extract_from_reddit_post(post, final_score)
        results['lead'] = lead
    except Exception as e:
        logger.warning(f"Lead extraction failed: {e}")

    # Store both results
    # ... (database insertion code)
```

---

## 🧪 Testing

### Test Option A (LLM Analyzer)

```bash
# Set OpenAI API key
export OPENAI_API_KEY=your_key_here

# Run demo
python agent_tools/monetization_llm_analyzer.py
```

Expected output:
```
EXAMPLE 1: projectmanagement
LLM Monetization Score: 85.2/100
Customer Segment: B2B
Willingness to Pay: 90.0/100
Payment Sentiment: Positive
Urgency: High
Price Points: ['$360/month', 'under $200/month']
```

### Test Option B (Lead Extractor)

```bash
# No API key needed
python core/lead_extractor.py
```

Expected output:
```
🔥 HIGH URGENCY LEAD - Posted 2024-01-15 16:02
Reddit: u/startup_cto_42
Currently Using: Asana
Budget: ✅ $360/month (approved)
Team Size: 12 users
Stage: 💰 Ready To Buy
Lead Score: 85/100
```

### Test Hybrid Demo

```bash
python scripts/demo_hybrid_strategy.py
```

---

## 💰 Cost Estimates

### Option A: LLM Monetization Analyzer

**Model:** `gpt-4o-mini` (cost-efficient)
- Input: ~500 tokens per post
- Output: ~200 tokens per analysis
- Cost: ~$0.01 per analysis

**Monthly estimates:**
- 100 opps/day @ threshold 60: ~$0.20-0.30/day = **$6-9/month**
- 1000 opps/day @ threshold 70: ~$2-3/day = **$60-90/month**

### Option B: Lead Extraction

**Cost:** $0 (regex-based, no API calls)

### Hybrid Strategy

**Total monthly cost:** $6-90/month depending on volume

---

## 📊 Monitoring

### Option A Monitoring

```sql
-- LLM vs Keyword score comparison
SELECT * FROM monetization_scoring_comparison
WHERE ABS(score_delta) > 20
ORDER BY ABS(score_delta) DESC
LIMIT 20;

-- Cost tracking
SELECT * FROM llm_analysis_cost_stats
ORDER BY date DESC;

-- B2B vs B2C performance
SELECT * FROM segment_performance;
```

### Option B Monitoring

```sql
-- Hot leads (ready to contact)
SELECT * FROM hot_leads
LIMIT 20;

-- Leads by competitor
SELECT * FROM leads_by_competitor;

-- Lead funnel metrics
SELECT * FROM lead_funnel_metrics
ORDER BY date DESC
LIMIT 30;
```

---

## 🎯 Launch Strategy

### Week 1-2: Implementation
- ✅ Run migrations
- ✅ Add integration code to pipeline
- ✅ Test with sample data
- ✅ Verify database writes

### Week 3-4: Validation

**Option A Validation:**
- Compare LLM scores vs keyword scores
- Identify false positives caught by LLM
- Calculate ROI (cost per quality opportunity)

**Option B Validation:**
- Call 5-10 SaaS founders with lead examples
- Script: "Do your sales reps check Reddit for competitor complaints?"
- Goal: 3+ say "Yes, I'd pay for that"

### Week 5-6: Launch

**If Option A validates:** Launch Founders Edition at $49-99/mo
**If Option B validates:** Launch Growth Edition at $499-4999/mo
**If BOTH validate:** Launch both tiers!

---

## ❓ FAQ

**Q: Can I run Option A without Option B?**
A: Yes! They're completely independent.

**Q: Do I need to change my existing pipeline?**
A: Minimal changes - just add the new analyzers after scoring.

**Q: What if LLM analysis fails?**
A: Falls back to keyword score. Non-blocking.

**Q: How do I disable one option?**
A: Set `MONETIZATION_LLM_ENABLED=false` or `LEAD_EXTRACTION_ENABLED=false` in `.env`

**Q: Can I test without API keys?**
A: Option B works without API keys. Option A requires OpenAI key.

---

## 📚 Additional Resources

- `agent_tools/monetization_llm_analyzer.py` - Implementation
- `core/lead_extractor.py` - Implementation
- `scripts/demo_hybrid_strategy.py` - Demo script
- Lost session chunks: `docs/claude-code-ai/chunks/` - Full context

---

## 🆘 Support

If you encounter issues:
1. Check logs for error messages
2. Verify environment variables are set
3. Test components individually first
4. Check database migrations ran successfully

---

*Generated for RedditHarbor Hybrid Strategy Implementation*
