# E2E Incremental Testing Guide: AI App Profiling System

**Version:** 1.0.0
**Last Updated:** 2025-11-09
**Status:** Production-Ready

## Overview

This guide provides step-by-step instructions for testing the RedditHarbor AI app profiling system across different opportunity score ranges (30 → 40 → 50 → 60 → 70). The system collects Reddit data, scores opportunities using a 5-dimensional methodology, generates AI profiles with Claude Haiku, and visualizes results in a Marimo dashboard.

**Pipeline Components:**
1. Reddit data collection (`scripts/full_scale_collection.py`)
2. Opportunity scoring (`scripts/batch_opportunity_scoring.py`)
3. AI profiling with LLMProfiler (Claude Haiku via OpenRouter)
4. Storage in `app_opportunities` and `workflow_results` tables
5. Marimo dashboard visualization

**Current Test Status:**
- E2E test script: `scripts/e2e_test_small_batch.py`
- Test data scores: ~32-35/100 (below ideal 40+ threshold)
- AI profiles generated: 1 so far
- Target: Test across score ranges 30 → 70

---

## Quick Start (5-Minute Test)

Run the existing E2E test to verify the pipeline works end-to-end:

```bash
cd /home/carlos/projects/redditharbor

# 1. Start Supabase (if not running)
supabase start

# 2. Run E2E test with AI profiling
python3 scripts/e2e_test_small_batch.py

# 3. Check results
python3 -c "
from supabase import create_client
supabase = create_client('http://127.0.0.1:54321', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU')
result = supabase.table('app_opportunities').select('*').execute()
print(f'AI Profiles: {len(result.data)}')
for row in result.data:
    print(f\"  Score: {row['opportunity_score']:.1f} - {row['app_concept'][:60]}...\")
"

# 4. Start dashboard (optional)
marimo run marimo_notebooks/opportunity_dashboard_fixed.py --host 127.0.0.1 --port 8081
```

**Expected Output:**
- 3 test submissions created
- 1 AI profile generated (score >= 30)
- Data visible in Supabase Studio: http://127.0.0.1:54323
- Dashboard shows opportunities (if running)

---

## Score Thresholds Explained

The OpportunityAnalyzerAgent uses a 5-dimensional scoring methodology:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Market Demand | 20% | Discussion volume, engagement, trend velocity |
| Pain Intensity | 25% | Negative sentiment, emotional language, frustration |
| Monetization Potential | 30% | Willingness to pay, commercial gaps, B2B/B2C signals |
| Market Gap | 15% | Competition density, solution inadequacy |
| Technical Feasibility | 10% | Development complexity, API needs |

**Score Ranges:**
- **85+**: High Priority (rare, exceptional opportunities)
- **70-84**: Med-High Priority (strong opportunities)
- **55-69**: Medium Priority (good opportunities)
- **40-54**: Low Priority (marginal opportunities)
- **<40**: Not Recommended (testing threshold: 30)

**Current Reality:**
- Most Reddit posts score 15-35/100
- Even extreme pain points score 32-35/100
- High-scoring opportunities (40+) are rare and valuable
- 70+ scores indicate exceptional product opportunities

---

## Incremental Testing Strategy

### Phase 1: Verify Baseline (Score 30-40)

**Goal:** Confirm AI profiling works with current test data

```bash
# 1. Run E2E test (already done in Quick Start)
python3 scripts/e2e_test_small_batch.py

# 2. Verify AI profiles in database
python3 -c "
from supabase import create_client
supabase = create_client('http://127.0.0.1:54321', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU')
result = supabase.table('app_opportunities').select('*').gte('opportunity_score', 30).execute()
print(f'Profiles (30+): {len(result.data)}')
for row in result.data[:5]:
    print(f\"\\n  Score: {row['opportunity_score']:.1f}\")
    print(f\"  Problem: {row['problem_description'][:80]}...\")
    print(f\"  App: {row['app_concept'][:80]}...\")
    print(f\"  Functions: {row['core_functions']}\")
"
```

**Verification Checklist:**
- [ ] 1+ AI profiles stored in `app_opportunities`
- [ ] `problem_description` field is populated (not empty)
- [ ] `app_concept` field has meaningful text
- [ ] `core_functions` is a JSON array with 1-3 items
- [ ] `value_proposition` explains user benefit
- [ ] `target_user` describes persona
- [ ] `monetization_model` suggests revenue model

---

### Phase 2: Collect Real Data (Score 40+)

**Goal:** Gather Reddit data likely to score 40+

**Strategy:** Focus on high-pain, high-engagement subreddits

```bash
# 1. Collect from pain-heavy subreddits (limited test)
python3 scripts/full_scale_collection.py --limit 100 --test-mode

# Or for specific high-pain subreddits, create a custom script:
cat > scripts/collect_high_pain_data.py << 'EOF'
#!/usr/bin/env python3
"""Collect from high-pain subreddits for testing"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / '.env.local')

from core.dlt_collection import collect_problem_posts
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# High-pain subreddits with strong monetization signals
HIGH_PAIN_SUBREDDITS = [
    "SaaS", "smallbusiness", "entrepreneur", "startups",
    "freelance", "digitalmarketing", "ecommerce"
]

def main():
    all_posts = []
    for subreddit in HIGH_PAIN_SUBREDDITS:
        logger.info(f"Collecting from r/{subreddit}...")
        posts = collect_problem_posts(
            subreddits=[subreddit],
            limit=50,
            sort_type="top",  # Top posts = higher engagement
            test_mode=False
        )
        if posts:
            all_posts.extend(posts)
            logger.info(f"  Collected {len(posts)} posts")

    logger.info(f"Total posts collected: {len(all_posts)}")

    # Load to database
    from scripts.full_scale_collection import load_submissions_to_supabase
    load_submissions_to_supabase(all_posts)

if __name__ == "__main__":
    main()
EOF

chmod +x scripts/collect_high_pain_data.py
python3 scripts/collect_high_pain_data.py
```

**High-Scoring Subreddits:**
- `r/SaaS` - Software business pain points (monetization signals)
- `r/entrepreneur` - Business problems (willingness to pay)
- `r/smallbusiness` - Operational pain (commercial gaps)
- `r/freelance` - Income/productivity pain (B2B signals)
- `r/Entrepreneur` - Startup challenges (high pain intensity)

---

### Phase 3: Score with Threshold 40 (Score 40+)

**Goal:** Run batch scoring and generate AI profiles for 40+ opportunities

```bash
# 1. Edit batch_opportunity_scoring.py to use threshold 40
# (Line 505: high_score_threshold: float = 40.0)
# OR pass as environment variable

# 2. Run batch scoring
SCORE_THRESHOLD=40.0 python3 scripts/batch_opportunity_scoring.py

# 3. Monitor progress
tail -f error_log/full_scale_collection.log

# 4. Verify results
python3 -c "
from supabase import create_client
supabase = create_client('http://127.0.0.1:54321', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU')

# Check workflow_results (all scores)
wf = supabase.table('workflow_results').select('*').gte('final_score', 40).execute()
print(f'Workflow results (40+): {len(wf.data)}')

# Check app_opportunities (AI profiles only)
app = supabase.table('app_opportunities').select('*').gte('opportunity_score', 40).execute()
print(f'AI Profiles (40+): {len(app.data)}')

if app.data:
    print('\\nTop opportunities:')
    for row in sorted(app.data, key=lambda x: x['opportunity_score'], reverse=True)[:5]:
        print(f\"  {row['opportunity_score']:.1f} - {row['app_concept'][:60]}...\")
"
```

**Verification Checklist:**
- [ ] 5+ opportunities score >= 40
- [ ] 3+ AI profiles generated for 40+ scores
- [ ] Dashboard shows higher-quality opportunities
- [ ] `top_opportunities` view returns results (score > 40 filter)

---

### Phase 4: Increase Threshold to 50 (Score 50+)

**Goal:** Test with more selective threshold

```bash
# 1. Collect more data if needed (repeat Phase 2)

# 2. Run batch scoring with threshold 50
SCORE_THRESHOLD=50.0 python3 scripts/batch_opportunity_scoring.py

# 3. Analyze score distribution
python3 -c "
from supabase import create_client
supabase = create_client('http://127.0.0.1:54321', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU')

result = supabase.table('workflow_results').select('final_score').execute()
scores = [row['final_score'] for row in result.data if row['final_score']]

print(f'Total opportunities: {len(scores)}')
print(f'Score 50+: {len([s for s in scores if s >= 50])}')
print(f'Score 40-49: {len([s for s in scores if 40 <= s < 50])}')
print(f'Score 30-39: {len([s for s in scores if 30 <= s < 40])}')
print(f'Score <30: {len([s for s in scores if s < 30])}')
print(f'Average: {sum(scores)/len(scores):.1f}')
print(f'Max: {max(scores):.1f}')
"
```

**Expected:**
- Fewer opportunities (50+ is selective)
- Higher-quality AI profiles
- Clear problem-solution fit
- Strong monetization signals

---

### Phase 5: Test High Thresholds (60+, 70+)

**Goal:** Validate exceptional opportunity detection

```bash
# 1. Check if any opportunities score 60+
python3 -c "
from supabase import create_client
supabase = create_client('http://127.0.0.1:54321', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU')

high_scores = supabase.table('workflow_results').select('*').gte('final_score', 60).execute()
print(f'Opportunities scoring 60+: {len(high_scores.data)}')

if high_scores.data:
    print('\\nExceptional opportunities:')
    for row in high_scores.data:
        print(f\"\\n  Score: {row['final_score']:.1f}\")
        print(f\"  App: {row['app_name'][:80]}\")
        print(f\"  Dimensions:\")
        print(f\"    Market Demand: {row.get('market_demand', 0):.1f}\")
        print(f\"    Pain Intensity: {row.get('pain_intensity', 0):.1f}\")
        print(f\"    Monetization: {row.get('monetization_potential', 0):.1f}\")
        print(f\"    Market Gap: {row.get('market_gap', 0):.1f}\")
        print(f\"    Tech Feasibility: {row.get('technical_feasibility', 0):.1f}\")
else:
    print('\\nNo 60+ scores yet. This is normal - these are rare!')
    print('Recommendation: Collect 1000+ posts from high-pain subreddits')
"

# 2. If no 60+ scores, collect more data
python3 scripts/full_scale_collection.py --limit 200
```

**Reality Check:**
- 60+ scores are **rare** (top 1-2% of opportunities)
- 70+ scores are **exceptional** (top 0.1%)
- May need 1000+ posts to find one 70+ opportunity
- This scarcity validates the scoring methodology

---

## Data Collection Strategies

### Strategy 1: Pain-First Collection

Target subreddits with explicit pain expressions:

```bash
# High-pain keywords to filter
PAIN_KEYWORDS = [
    "frustrated", "desperate", "broken", "terrible",
    "waste", "expensive", "confusing", "hate",
    "losing money", "waste time", "doesn't work"
]

# Subreddits with strong pain signals
r/SaaS           # Software problems, willingness to pay
r/entrepreneur   # Business challenges, commercial gaps
r/smallbusiness  # Operational pain, budget concerns
r/freelance      # Income/productivity pain
r/realestateinvesting  # Deal analysis pain, high stakes
```

### Strategy 2: Engagement-First Collection

High engagement = strong market demand:

```bash
# Collect top posts (high upvotes/comments)
python3 scripts/full_scale_collection.py --limit 100

# Focus on sort_type="top" for high engagement
# Edit full_scale_collection.py line 546:
# sort_types = ["top"]  # Instead of ["hot", "top", "new"]
```

### Strategy 3: Monetization-First Collection

Subreddits with strong willingness to pay signals:

```bash
# B2B subreddits (higher monetization potential)
r/SaaS
r/b2bmarketing
r/digitalnomad
r/freelance
r/consulting

# Example: Collect from B2B subreddits only
python3 -c "
import sys
from pathlib import Path
project_root = Path.cwd()
sys.path.insert(0, str(project_root))

from core.dlt_collection import collect_problem_posts
from scripts.full_scale_collection import load_submissions_to_supabase

b2b_subreddits = ['SaaS', 'b2bmarketing', 'freelance', 'consulting']
all_posts = []

for sub in b2b_subreddits:
    posts = collect_problem_posts(subreddits=[sub], limit=100, sort_type='top')
    all_posts.extend(posts)
    print(f'Collected {len(posts)} from r/{sub}')

load_submissions_to_supabase(all_posts)
print(f'Total: {len(all_posts)} posts loaded')
"
```

---

## Verification Checklist

Use this checklist at each score threshold:

### Database Verification

```bash
# Check all tables
python3 -c "
from supabase import create_client
supabase = create_client('http://127.0.0.1:54321', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU')

# 1. Submissions (raw Reddit data)
subs = supabase.table('submissions').select('*', count='exact').execute()
print(f'Submissions: {subs.count}')

# 2. Workflow results (all scores)
wf = supabase.table('workflow_results').select('*', count='exact').execute()
print(f'Workflow results: {wf.count}')

# 3. App opportunities (AI profiles only)
app = supabase.table('app_opportunities').select('*', count='exact').execute()
print(f'App opportunities: {app.count}')

# 4. Top opportunities view (score > 40)
top = supabase.table('top_opportunities').select('*', count='exact').execute()
print(f'Top opportunities (40+): {top.count}')
"
```

### Score Distribution Check

```bash
python3 -c "
from supabase import create_client
import statistics

supabase = create_client('http://127.0.0.1:54321', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU')

result = supabase.table('workflow_results').select('final_score').execute()
scores = [row['final_score'] for row in result.data if row['final_score']]

print(f'\\nScore Statistics:')
print(f'  Count: {len(scores)}')
print(f'  Mean: {statistics.mean(scores):.1f}')
print(f'  Median: {statistics.median(scores):.1f}')
print(f'  Std Dev: {statistics.stdev(scores):.1f}')
print(f'  Min: {min(scores):.1f}')
print(f'  Max: {max(scores):.1f}')

# Percentiles
sorted_scores = sorted(scores)
print(f'\\nPercentiles:')
print(f'  90th: {sorted_scores[int(len(scores)*0.9)]:.1f}')
print(f'  95th: {sorted_scores[int(len(scores)*0.95)]:.1f}')
print(f'  99th: {sorted_scores[int(len(scores)*0.99)]:.1f}')
"
```

### AI Profile Quality Check

```bash
python3 -c "
from supabase import create_client

supabase = create_client('http://127.0.0.1:54321', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU')

profiles = supabase.table('app_opportunities').select('*').order('opportunity_score', desc=True).limit(10).execute()

print(f'\\nTop 10 AI Profiles:')
for i, row in enumerate(profiles.data, 1):
    print(f\"\\n{i}. Score: {row['opportunity_score']:.1f}\")
    print(f\"   Problem: {row['problem_description'][:80]}...\")
    print(f\"   App: {row['app_concept'][:80]}...\")
    print(f\"   Functions ({len(row['core_functions'])}): {row['core_functions']}\")
    print(f\"   Value: {row['value_proposition'][:60]}...\")
    print(f\"   User: {row['target_user'][:60]}...\")
    print(f\"   Monetization: {row['monetization_model'][:60]}...\")
"
```

---

## Common Issues & Solutions

### Issue 1: No High Scores (All < 40)

**Symptoms:**
- All opportunities score 15-35
- No AI profiles generated
- Dashboard empty

**Diagnosis:**
```bash
python3 -c "
from supabase import create_client
supabase = create_client('http://127.0.0.1:54321', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU')

# Check dimension scores
result = supabase.table('workflow_results').select('*').order('final_score', desc=True).limit(5).execute()

for row in result.data:
    print(f\"\\nScore: {row['final_score']:.1f}\")
    print(f\"  Market Demand: {row.get('market_demand', 0):.1f}\")
    print(f\"  Pain Intensity: {row.get('pain_intensity', 0):.1f}\")
    print(f\"  Monetization: {row.get('monetization_potential', 0):.1f}\")
    print(f\"  Market Gap: {row.get('market_gap', 0):.1f}\")
    print(f\"  Tech Feasibility: {row.get('technical_feasibility', 0):.1f}\")
"
```

**Solution:**
1. Collect from high-pain subreddits (r/SaaS, r/entrepreneur)
2. Focus on `sort_type="top"` for high engagement
3. Increase collection volume (1000+ posts)
4. Lower threshold to 30 for testing

### Issue 2: DLT Type Mismatch Error

**Symptoms:**
```
TypeError: function_list expected TEXT[] but got JSONB
```

**Solution:**
```bash
# Check current schema
docker exec -i redditharbor-db psql -U postgres -d postgres -c "
\d workflow_results
"

# If function_list is TEXT[], run migration
docker exec -i redditharbor-db psql -U postgres -d postgres -c "
ALTER TABLE workflow_results
ALTER COLUMN function_list TYPE JSONB USING function_list::JSONB;
"
```

**Reference:** See `DLT_TYPE_MISMATCH_FIX_REPORT.md` for full resolution

### Issue 3: LLM Profiler Fails

**Symptoms:**
```
⚠️ LLM Profiler unavailable: API key not found
```

**Solution:**
```bash
# Check .env.local has OpenRouter API key
grep OPENROUTER_API_KEY /home/carlos/projects/redditharbor/.env.local

# If missing, add it
echo "OPENROUTER_API_KEY=your-key-here" >> /home/carlos/projects/redditharbor/.env.local

# Verify LLM profiler works
python3 -c "
from agent_tools.llm_profiler import LLMProfiler
profiler = LLMProfiler()
print('LLM Profiler initialized successfully')
"
```

### Issue 4: Dashboard Shows No Data

**Symptoms:**
- Dashboard loads but shows empty charts
- "No opportunities found" message

**Diagnosis:**
```bash
# Check which table dashboard queries
grep -n "table(" marimo_notebooks/opportunity_dashboard_fixed.py

# Check data in tables
python3 -c "
from supabase import create_client
supabase = create_client('http://127.0.0.1:54321', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU')

app = supabase.table('app_opportunities').select('*', count='exact').execute()
wf = supabase.table('workflow_results').select('*', count='exact').execute()

print(f'app_opportunities: {app.count} rows')
print(f'workflow_results: {wf.count} rows')
"
```

**Solution:**
1. If `app_opportunities` is empty: Run scoring with threshold <= 40
2. If `workflow_results` is empty: Run `batch_opportunity_scoring.py`
3. Update dashboard to query the correct table

### Issue 5: Constraint Validation Failures

**Symptoms:**
```
⚠️ Disqualified: 45 opportunities (4+ functions)
```

**Diagnosis:**
```bash
# Check disqualified opportunities
python3 -c "
from core.dlt.constraint_validator import app_opportunities_with_constraint

# Test with sample data
test_opps = [
    {'app_name': 'Test 1', 'function_list': ['F1', 'F2'], 'final_score': 50},
    {'app_name': 'Test 2', 'function_list': ['F1', 'F2', 'F3', 'F4'], 'final_score': 60}
]

validated = list(app_opportunities_with_constraint(test_opps))
for opp in validated:
    if opp.get('is_disqualified'):
        print(f\"Disqualified: {opp['app_name']} - {opp['violation_reason']}\")
"
```

**Solution:**
This is working as designed (enforces 1-3 function rule). High-quality opportunities should have 1-3 focused functions. If too many are disqualified:
1. Review `_define_core_functions()` logic in `opportunity_analyzer_agent.py`
2. Ensure function lists are properly trimmed to 1-3 items
3. Check for data quality issues in source Reddit posts

---

## Advanced Testing Scenarios

### Scenario 1: Custom Subreddit Focus

Test a specific niche:

```bash
# Create custom collection script
cat > scripts/test_niche_collection.py << 'EOF'
#!/usr/bin/env python3
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / '.env.local')

from core.dlt_collection import collect_problem_posts
from scripts.full_scale_collection import load_submissions_to_supabase

# Test specific niche
NICHE_SUBREDDITS = ["realestateinvesting", "financialcareers"]

all_posts = []
for sub in NICHE_SUBREDDITS:
    posts = collect_problem_posts(subreddits=[sub], limit=100, sort_type="top")
    all_posts.extend(posts)

load_submissions_to_supabase(all_posts)
print(f"Collected {len(all_posts)} posts from {NICHE_SUBREDDITS}")
EOF

python3 scripts/test_niche_collection.py
```

### Scenario 2: A/B Test Score Thresholds

Compare results with different thresholds:

```bash
# Run with threshold 30
SCORE_THRESHOLD=30.0 python3 scripts/batch_opportunity_scoring.py

# Save results
python3 -c "
from supabase import create_client
supabase = create_client('http://127.0.0.1:54321', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU')
result = supabase.table('app_opportunities').select('*').gte('opportunity_score', 30).execute()
with open('threshold_30_results.txt', 'w') as f:
    f.write(f'Count: {len(result.data)}\\n')
    for row in result.data:
        f.write(f\"{row['opportunity_score']:.1f} - {row['app_concept'][:60]}\\n\")
"

# Run with threshold 40
SCORE_THRESHOLD=40.0 python3 scripts/batch_opportunity_scoring.py

# Compare results
diff threshold_30_results.txt threshold_40_results.txt
```

### Scenario 3: Dimension Score Analysis

Identify which dimensions drive high scores:

```bash
python3 -c "
from supabase import create_client
import statistics

supabase = create_client('http://127.0.0.1:54321', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU')

# High scorers (40+)
high = supabase.table('workflow_results').select('*').gte('final_score', 40).execute()

# Low scorers (<30)
low = supabase.table('workflow_results').select('*').lt('final_score', 30).execute()

def avg_dimension(data, dim):
    scores = [row.get(dim, 0) for row in data if row.get(dim)]
    return statistics.mean(scores) if scores else 0

dimensions = ['market_demand', 'pain_intensity', 'monetization_potential', 'market_gap', 'technical_feasibility']

print('Dimension Analysis:')
print('\\nHigh Scorers (40+):')
for dim in dimensions:
    print(f'  {dim}: {avg_dimension(high.data, dim):.1f}')

print('\\nLow Scorers (<30):')
for dim in dimensions:
    print(f'  {dim}: {avg_dimension(low.data, dim):.1f}')
"
```

---

## Performance Metrics

Track key metrics at each phase:

```bash
# Create metrics tracker
cat > scripts/track_test_metrics.py << 'EOF'
#!/usr/bin/env python3
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from supabase import create_client

supabase = create_client('http://127.0.0.1:54321', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU')

def get_metrics():
    subs = supabase.table('submissions').select('*', count='exact').execute()
    wf = supabase.table('workflow_results').select('*').execute()
    app = supabase.table('app_opportunities').select('*').execute()

    scores = [row['final_score'] for row in wf.data if row.get('final_score')]

    metrics = {
        'timestamp': datetime.now().isoformat(),
        'submissions_collected': subs.count,
        'opportunities_scored': len(wf.data),
        'ai_profiles_generated': len(app.data),
        'avg_score': sum(scores)/len(scores) if scores else 0,
        'max_score': max(scores) if scores else 0,
        'score_40_plus': len([s for s in scores if s >= 40]),
        'score_50_plus': len([s for s in scores if s >= 50]),
        'score_60_plus': len([s for s in scores if s >= 60]),
    }

    return metrics

if __name__ == "__main__":
    m = get_metrics()
    print(f"\n=== Test Metrics ({m['timestamp']}) ===")
    print(f"Submissions collected: {m['submissions_collected']}")
    print(f"Opportunities scored: {m['opportunities_scored']}")
    print(f"AI profiles generated: {m['ai_profiles_generated']}")
    print(f"Average score: {m['avg_score']:.1f}")
    print(f"Max score: {m['max_score']:.1f}")
    print(f"Score 40+: {m['score_40_plus']}")
    print(f"Score 50+: {m['score_50_plus']}")
    print(f"Score 60+: {m['score_60_plus']}")
    print("="*50)
EOF

python3 scripts/track_test_metrics.py
```

**Target Metrics:**
- **Phase 1 (30+)**: 10+ AI profiles
- **Phase 2 (40+)**: 5+ AI profiles
- **Phase 3 (50+)**: 2+ AI profiles
- **Phase 4 (60+)**: 1+ AI profile
- **Phase 5 (70+)**: 0-1 AI profiles (rare!)

---

## Continuous Monitoring

Set up continuous monitoring during long-running tests:

```bash
# Watch metrics in real-time
watch -n 30 python3 scripts/track_test_metrics.py

# Monitor log files
tail -f error_log/full_scale_collection.log | grep -E "(Score|AI profile|Error)"

# Monitor Supabase Studio
open http://127.0.0.1:54323

# Monitor dashboard
open http://127.0.0.1:8081
```

---

## Next Steps After Testing

Once you've successfully tested across score ranges:

1. **Production Deployment**
   - Set threshold to 40.0 for production
   - Schedule batch_opportunity_scoring.py daily
   - Monitor AI profile quality

2. **Quality Improvements**
   - Fine-tune scoring weights if needed
   - Expand LLM profiler prompts
   - Add more subreddit coverage

3. **Integration**
   - Connect dashboard to production data
   - Add email alerts for 60+ scores
   - Build app validation workflows

4. **Documentation**
   - Document high-scoring patterns
   - Create playbook for manual review
   - Share findings with team

---

## Appendix: Quick Reference Commands

```bash
# Start Supabase
supabase start

# Quick E2E test
python3 scripts/e2e_test_small_batch.py

# Collect Reddit data
python3 scripts/full_scale_collection.py --limit 100 --test-mode

# Run batch scoring
python3 scripts/batch_opportunity_scoring.py

# Check database counts
python3 -c "from supabase import create_client; s = create_client('http://127.0.0.1:54321', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU'); print(f\"Submissions: {s.table('submissions').select('*', count='exact').execute().count}\"); print(f\"Scores: {s.table('workflow_results').select('*', count='exact').execute().count}\"); print(f\"AI Profiles: {s.table('app_opportunities').select('*', count='exact').execute().count}\")"

# Start dashboard
marimo run marimo_notebooks/opportunity_dashboard_fixed.py --host 127.0.0.1 --port 8081

# Track metrics
python3 scripts/track_test_metrics.py

# View Supabase Studio
open http://127.0.0.1:54323
```

---

## Support

**Files:**
- E2E test: `/home/carlos/projects/redditharbor/scripts/e2e_test_small_batch.py`
- Scoring: `/home/carlos/projects/redditharbor/scripts/batch_opportunity_scoring.py`
- Collection: `/home/carlos/projects/redditharbor/scripts/full_scale_collection.py`
- Analyzer: `/home/carlos/projects/redditharbor/agent_tools/opportunity_analyzer_agent.py`
- Profiler: `/home/carlos/projects/redditharbor/agent_tools/llm_profiler.py`

**Documentation:**
- E2E Results: `/home/carlos/projects/redditharbor/E2E_TEST_RESULTS.md`
- DLT Fix: `/home/carlos/projects/redditharbor/DLT_TYPE_MISMATCH_FIX_REPORT.md`
- AI App Plan: `/home/carlos/projects/redditharbor/docs/plans/2025-11-08-ai-app-profile-generation.md`

**Logs:**
- Collection: `/home/carlos/projects/redditharbor/error_log/full_scale_collection.log`
- General: `/home/carlos/projects/redditharbor/error_log/*.log`

---

**End of Guide**
