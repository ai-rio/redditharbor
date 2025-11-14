# Option B Workflow Integration
**How to add Lead Extraction to your existing 2-script workflow**

---

## 📋 Current Workflow (Option A Only)

Your current workflow is beautifully simple:

```bash
# Step 1: Collect Reddit data + analyze + trust validation
python scripts/dlt/dlt_trust_pipeline.py --limit 10

# Step 2: Score opportunities + generate AI profiles
python scripts/core/batch_opportunity_scoring.py
```

**Result:** App idea profiles in `app_opportunities` and `workflow_results` tables

---

## 🚀 Enhanced Workflow (Option A + B Hybrid)

### **Option 1: Single Integrated Script (RECOMMENDED)**

Add lead extraction directly into `dlt_trust_pipeline.py`:

```bash
# Same command, now extracts BOTH app ideas AND sales leads
python scripts/dlt/dlt_trust_pipeline.py --limit 10 --enable-leads

# Then score as before
python scripts/core/batch_opportunity_scoring.py
```

**Result:**
- App idea profiles in `app_opportunities` ✓
- **Sales leads in `customer_leads`** ← NEW!

---

### **Option 2: Separate Lead Extraction Script (More Control)**

Keep your existing workflow, add optional lead extraction:

```bash
# Step 1: Existing pipeline (unchanged)
python scripts/dlt/dlt_trust_pipeline.py --limit 10

# Step 2: Existing scoring (unchanged)
python scripts/core/batch_opportunity_scoring.py

# Step 3: NEW - Extract leads (optional)
python scripts/core/extract_leads.py --threshold 60
```

**Result:**
- App ideas via existing flow ✓
- **Sales leads via new script** ← NEW!

---

## 💡 Integration Code Examples

### **Approach 1: Add to dlt_trust_pipeline.py (Minimal Changes)**

Add **~10 lines** to your existing `dlt_trust_pipeline.py`:

```python
# At the top, add import
from core.lead_extractor import LeadExtractor, convert_to_database_record

# In main(), after line 696, add:
LEAD_EXTRACTION_ENABLED = os.getenv("LEAD_EXTRACTION_ENABLED", "false").lower() == "true"
LEAD_THRESHOLD = float(os.getenv("LEAD_EXTRACTION_THRESHOLD", "60.0"))

# After Step 2 (analyze_opportunities_with_ai), add:
if LEAD_EXTRACTION_ENABLED:
    leads = extract_leads_from_posts(analyzed_posts, LEAD_THRESHOLD)
    load_leads_to_database(leads)
```

**New function to add (copy-paste):**

```python
def extract_leads_from_posts(posts: list[dict], threshold: float = 60.0) -> list[dict]:
    """
    Extract sales leads from analyzed posts

    Args:
        posts: Posts with AI analysis scores
        threshold: Minimum score to extract leads

    Returns:
        List of lead records for database
    """
    print("\n" + "=" * 80)
    print("OPTION B: LEAD EXTRACTION")
    print(f"Extracting leads from posts with score >= {threshold}")
    print("=" * 80)

    extractor = LeadExtractor()
    leads = []

    for post in posts:
        final_score = post.get('final_score', 0)

        if final_score >= threshold:
            try:
                # Convert to lead format
                lead_post = {
                    'id': post.get('id'),
                    'author': post.get('author', 'unknown'),
                    'title': post.get('title', ''),
                    'selftext': post.get('text', ''),
                    'subreddit': post.get('subreddit', ''),
                    'created_utc': post.get('created_utc')
                }

                # Extract lead signals
                lead = extractor.extract_from_reddit_post(lead_post, final_score)
                lead_record = convert_to_database_record(lead)
                leads.append(lead_record)

                print(f"  ✓ Lead: u/{lead.reddit_username} | Score: {final_score:.0f} | Stage: {lead.buying_intent_stage}")

            except Exception as e:
                print(f"  ⚠️  Lead extraction failed for {post.get('id')}: {e}")

    print(f"\n✓ Extracted {len(leads)} sales leads")
    return leads


def load_leads_to_database(leads: list[dict]):
    """
    Load leads to customer_leads table using DLT

    Args:
        leads: Lead records to load
    """
    if not leads:
        print("  No leads to load")
        return

    print(f"\n📊 Loading {len(leads)} leads to database...")

    try:
        import dlt

        # Create DLT pipeline
        pipeline = dlt.pipeline(
            pipeline_name="reddit_harbor_leads",
            destination="postgres",
            dataset_name="reddit_harbor"
        )

        # Define resource with merge disposition (prevent duplicates)
        @dlt.resource(
            name="customer_leads",
            write_disposition="merge",
            primary_key="reddit_post_id"
        )
        def leads_resource():
            yield leads

        # Load to database
        load_info = pipeline.run(leads_resource())

        print(f"✓ Loaded {len(leads)} leads to customer_leads table")
        print(f"  Pipeline: {load_info.pipeline.pipeline_name}")

    except Exception as e:
        print(f"❌ Lead loading failed: {e}")
        import traceback
        traceback.print_exc()
```

**That's it! Just add these 2 functions and enable with env var.**

---

### **Approach 2: Standalone Lead Extraction Script**

Create `scripts/core/extract_leads.py`:

```python
#!/usr/bin/env python3
"""
Extract sales leads from workflow_results
Reads opportunities that were already scored and extracts lead data
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.lead_extractor import LeadExtractor, convert_to_database_record
from config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client
import dlt

def main():
    # Connect to database
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Fetch high-scoring opportunities
    threshold = 60.0
    print(f"Fetching opportunities with score >= {threshold}...")

    response = supabase.table('workflow_results')\
        .select('*')\
        .gte('final_score', threshold)\
        .execute()

    opportunities = response.data
    print(f"Found {len(opportunities)} opportunities")

    # Extract leads
    extractor = LeadExtractor()
    leads = []

    for opp in opportunities:
        # Convert to post format
        post = {
            'id': opp.get('submission_id'),
            'author': 'unknown',  # Need to fetch from submissions table
            'title': opp.get('problem_description', ''),
            'selftext': '',
            'subreddit': opp.get('subreddit', ''),
            'created_utc': None
        }

        lead = extractor.extract_from_reddit_post(post, opp['final_score'])
        leads.append(convert_to_database_record(lead))

    # Load to database
    pipeline = dlt.pipeline(
        pipeline_name="reddit_harbor_leads",
        destination="postgres",
        dataset_name="reddit_harbor"
    )

    @dlt.resource(name="customer_leads", write_disposition="merge", primary_key="reddit_post_id")
    def leads_resource():
        yield leads

    pipeline.run(leads_resource())
    print(f"✓ Loaded {len(leads)} leads to customer_leads table")

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
python scripts/core/extract_leads.py
```

---

## 🎯 Recommended Approach

### **For Your Use Case: Approach 1 (Integrated)**

**Why:**
- ✅ Minimal code changes (~50 lines total)
- ✅ No extra script to run
- ✅ Same DLT pattern you're already using
- ✅ Enable/disable with env var
- ✅ Runs in parallel with existing flow

**Steps:**

1. **Add the 2 functions above to `dlt_trust_pipeline.py`**

2. **Add 3 lines to `main()` function:**
```python
# After line 713 (after analyze_opportunities_with_ai)
if os.getenv("LEAD_EXTRACTION_ENABLED", "false").lower() == "true":
    leads = extract_leads_from_posts(analyzed_posts, args.score_threshold)
    load_leads_to_database(leads)
```

3. **Enable with environment variable:**
```bash
# Add to .env.local
LEAD_EXTRACTION_ENABLED=true
LEAD_EXTRACTION_THRESHOLD=60.0
```

4. **Run as before:**
```bash
python scripts/dlt/dlt_trust_pipeline.py --limit 10
```

**That's it! Now you get BOTH app ideas AND sales leads from one command.**

---

## 📊 Workflow Comparison

### **Before (Option A Only):**
```
dlt_trust_pipeline.py
  ├─ Collect Reddit posts
  ├─ Analyze with AI
  ├─ Trust validation
  └─ Store app_opportunities ✓

batch_opportunity_scoring.py
  ├─ Score opportunities
  └─ Generate AI profiles ✓
```

### **After (Option A + B Hybrid):**
```
dlt_trust_pipeline.py
  ├─ Collect Reddit posts
  ├─ Analyze with AI
  ├─ Trust validation
  ├─ Store app_opportunities ✓
  └─ Extract & store customer_leads ✓ ← NEW (if enabled)

batch_opportunity_scoring.py
  ├─ Score opportunities
  └─ Generate AI profiles ✓
```

**Impact:** +50 lines of code, same workflow!

---

## 🔧 Configuration

### **Environment Variables (.env.local)**

```bash
# Option A: Enhanced monetization (optional)
MONETIZATION_LLM_ENABLED=false  # Set to true when ready
MONETIZATION_LLM_THRESHOLD=60.0
OPENAI_API_KEY=sk-...  # Required for Option A

# Option B: Lead extraction (recommended)
LEAD_EXTRACTION_ENABLED=true  # Enable lead extraction
LEAD_EXTRACTION_THRESHOLD=60.0  # Only extract from high scorers

# Slack alerts for hot leads (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK
```

---

## 🧪 Testing

### **Test Lead Extraction Without Changing Production:**

```bash
# 1. Test with demo data
python core/lead_extractor.py

# 2. Test integrated flow on dev database
export DATABASE_URL=$DEV_DATABASE_URL
export LEAD_EXTRACTION_ENABLED=true
python scripts/dlt/dlt_trust_pipeline.py --limit 5 --test-mode

# 3. Check results
psql $DEV_DATABASE_URL -c "SELECT * FROM customer_leads LIMIT 5;"
```

---

## 💡 Best Practices

### **Start Simple:**

1. **Week 1:** Enable lead extraction, observe data
```bash
LEAD_EXTRACTION_ENABLED=true
```

2. **Week 2:** Add Slack alerts for hot leads
```bash
SLACK_WEBHOOK_URL=your_webhook
```

3. **Week 3:** Lower threshold to get more leads
```bash
LEAD_EXTRACTION_THRESHOLD=50.0
```

4. **Week 4:** Validate with 5-10 SaaS founder calls

### **Gradual Rollout:**

```bash
# Start conservative (high threshold)
LEAD_EXTRACTION_THRESHOLD=70.0  # Only top leads

# After validation, expand
LEAD_EXTRACTION_THRESHOLD=60.0  # More leads

# Production volume
LEAD_EXTRACTION_THRESHOLD=50.0  # Full pipeline
```

---

## 📈 Expected Results

### **Volume Estimates:**

With `--limit 10` per subreddit (3 subreddits = 30 posts):
- Posts collected: ~30
- Posts passing trust validation: ~15-20
- Posts with score >= 60: ~5-10
- **Sales leads extracted: ~5-10 per run**

**Daily run:** 10-20 leads/day
**Weekly run:** 50-100 leads/week

---

## ❓ FAQ

**Q: Will this slow down my pipeline?**
A: No! Lead extraction is pure regex (no API calls), adds <1 second per 10 posts.

**Q: Can I disable it later?**
A: Yes! Set `LEAD_EXTRACTION_ENABLED=false` in .env.local

**Q: Does it change my app idea flow?**
A: No! App ideas continue flowing to same tables. Leads go to separate `customer_leads` table.

**Q: Do I need OpenAI API key?**
A: Not for Option B (lead extraction). Only needed for Option A (LLM monetization).

**Q: Can I run just lead extraction?**
A: Yes! Use Approach 2 (standalone script) to extract from existing `workflow_results`.

---

## 🚀 Quick Start (Copy-Paste Ready)

### **30-Second Integration:**

1. **Download integration code:**
```bash
# Already in your repo at:
# core/lead_extractor.py (already committed)
```

2. **Add to .env.local:**
```bash
echo "LEAD_EXTRACTION_ENABLED=true" >> .env.local
echo "LEAD_EXTRACTION_THRESHOLD=60.0" >> .env.local
```

3. **Copy-paste the 2 functions** from "Approach 1" above into `dlt_trust_pipeline.py`

4. **Run your existing workflow:**
```bash
python scripts/dlt/dlt_trust_pipeline.py --limit 10
```

5. **Check results:**
```bash
psql $DATABASE_URL -c "SELECT reddit_username, competitor_mentioned, budget_mentioned, lead_score FROM customer_leads ORDER BY lead_score DESC LIMIT 10;"
```

**Done! You're now extracting sales leads. 🎉**

---

*Need help? See full integration guide: `docs/guides/hybrid-strategy-integration-guide.md`*
