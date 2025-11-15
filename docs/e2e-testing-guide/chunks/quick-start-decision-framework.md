# Quick Start Guide & Decision Framework

**Enhanced Semantic Chunk 2**
**RedditHarbor E2E Guide - Agent-Enhanced Processing**
**Generated:** 2025-11-12 07:41:21

## 🎯 Chunk Overview

- **Semantic Theme:** quick_start
- **Complexity Level:** medium
- **Content Focus:** Quick Start Guide & Decision Framework
- **Agent Integration:** 2 agents
- **Doit Tasks:** 2 tasks

## 🤖 Agent Integration

### Opportunity_Analyzer Agent
- **File:** `agent_tools/opportunity_analyzer_agent.py`
- **Functions:** __init__, _calculate_final_score, _get_priority, analyze_opportunity, _calculate_market_demand, _calculate_pain_intensity, _calculate_monetization_potential, _calculate_market_gap, _calculate_technical_feasibility, _generate_core_functions, batch_analyze_opportunities, get_top_opportunities, generate_validation_report, track_business_metrics, continuous_analysis, main
- **Complexity:** high

### Task_Automation Agent
- **File:** `N/A`
- **Functions:** 
- **Complexity:** N/A

## 🔧 Doit Integration

- `doit e2e_test`
- `doit collect_reddit_data`

---

## 📖 Content
---

## 🤖 Agent Integration

This section is enhanced with RedditHarbor agent integration:

**Primary Agents:** opportunity_analyzer, task_automation
**Integration Points:** scoring_validation, constraint_checking, quality_assessment
**Data Dependencies:** submissions, workflow_results

## Quick Start Guide: Choose Your Path

RedditHarbor now offers **two powerful approaches** for Reddit data collection and opportunity analysis. Choose based on your goals:

### 🎯 Quick Decision Matrix

| Your Goal | Recommended Path | Why |
|-----------|------------------|-----|
| **Quick validation** | **Traditional AI** (5 min) | Simple setup, immediate results |
| **Production system** | **DLT Activity** (10 min) | 60% API savings, automatic quality filtering |
| **Maximum insights** | **Hybrid approach** (15 min) | Quality data + AI analysis |
| **Research project** | **DLT Activity** (10 min) | Scalable, production-ready features |

### Path A: Traditional AI Profiling (5-Minute Test)

**Best for**: Quick validation, small-scale testing, beginners

```bash
cd /home/carlos/projects/redditharbor

# 1. Start Supabase (if not running)
supabase start

# 2. Run traditional E2E test with AI profiling
source .venv/bin/activate && python  scripts/e2e_test_small_batch.py

# 3. Run batch scoring with threshold 40 (recommended for production)
SCORE_THRESHOLD=40.0 source .venv/bin/activate && python  scripts/batch_opportunity_scoring.py

# 4. Check results
source .venv/bin/activate && python  -c "
from supabase import create_client
supabase = create_client('http://127.0.0.1:54321', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU')
result = supabase.table('app_opportunities').select('*').execute()
print(f'AI Profiles (40+): {len(result.data)}')
for row in result.data:
    print(f\"  Score: {row['opportunity_score']:.1f} - {row['app_concept'][:60]}...\")
"

# 5. Start dashboard (optional)
marimo run marimo_notebooks/opportunity_dashboard_fixed.py --host 127.0.0.1 --port 8081
```

**Expected Output:**
- 3 test submissions created
- 1 AI profile generated (score >= 30)
- Data visible in Supabase Studio: http://127.0.0.1:54323
- Dashboard shows opportunities (if running)

### Path B: DLT Activity Validation (10-Minute Test) ⭐ RECOMMENDED

**Best for**: Production systems, large-scale research, cost efficiency

```bash
cd /home/carlos/projects/redditharbor

# 1. Source virtual environment and verify DLT setup
source .venv/bin/activate
python -c "import dlt, praw; print('✅ DLT dependencies available')"

# 2. Start Supabase (if not running)
supabase start

# 3. Quick DLT dry-run validation (no data collection)
python scripts/run_dlt_activity_collection.py --subreddits "python,MachineLearning" --dry-run --min-activity 50

# 4. Small-scale DLT collection (10-20 high-quality posts)
python scripts/run_dlt_activity_collection.py --segment "technology_saas" --min-activity 60 --limit 15

# 5. Run AI profiling on DLT-collected data
SCORE_THRESHOLD=40.0 source .venv/bin/activate && python  scripts/batch_opportunity_scoring.py

# 6. Check DLT-enhanced results
source .venv/bin/activate && python  -c "
from supabase import create_client
supabase = create_client('http://127.0.0.1:54321', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU')


---

## ✅ Agent Validation

**Doit Tasks:** e2e_test, collect_reddit_data
**Expected Agent Behavior:** Automated validation and enhancement
**Quality Assurance:** Multi-agent cross-validation
