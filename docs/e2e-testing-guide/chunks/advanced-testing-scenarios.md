# Advanced Testing Scenarios & Integration

**Enhanced Semantic Chunk 6**
**RedditHarbor E2E Guide - Agent-Enhanced Processing**
**Generated:** 2025-11-12 07:41:21

## 🎯 Chunk Overview

- **Semantic Theme:** advanced_scenarios
- **Complexity Level:** high
- **Content Focus:** Advanced Testing Scenarios & Integration
- **Agent Integration:** 3 agents
- **Doit Tasks:** 2 tasks

## 🤖 Agent Integration

### Opportunity_Analyzer Agent
- **File:** `agent_tools/opportunity_analyzer_agent.py`
- **Functions:** __init__, _calculate_final_score, _get_priority, analyze_opportunity, _calculate_market_demand, _calculate_pain_intensity, _calculate_monetization_potential, _calculate_market_gap, _calculate_technical_feasibility, _generate_core_functions, batch_analyze_opportunities, get_top_opportunities, generate_validation_report, track_business_metrics, continuous_analysis, main
- **Complexity:** high

### Llm_Profiler Agent
- **File:** `agent_tools/llm_profiler.py`
- **Functions:** __init__, generate_app_profile, _build_prompt, _call_llm, _parse_response
- **Complexity:** medium

### Dlt_Collection Agent
- **File:** `core/dlt_collection.py`
- **Functions:** get_reddit_client, contains_problem_keywords, transform_submission_to_schema, collect_problem_posts, transform_comment_to_schema, collect_post_comments, create_dlt_pipeline, load_to_supabase, submission_resource, main
- **Complexity:** medium

## 🔧 Doit Integration

- `doit e2e_test`
- `doit full_scale_collection`

---

## 📖 Content
---

## 🤖 Agent Integration

This section is enhanced with RedditHarbor agent integration:

**Primary Agents:** opportunity_analyzer, llm_profiler, dlt_collection
**Integration Points:** scoring_validation, constraint_checking, quality_assessment, activity_scoring, data_validation, performance_monitoring, profile_generation, market_analysis, concept_validation
**Data Dependencies:** all_tables, performance_metrics

## Advanced Testing Scenarios

### Scenario 1: Custom Subreddit Focus

Test a specific niche:

```bash
# Create custom collection script
cat > scripts/test_niche_collection.py << 'EOF'
#!/usr/bin/env source .venv/bin/activate && python 
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

source .venv/bin/activate && python  scripts/test_niche_collection.py
```

### Scenario 2: A/B Test Score Thresholds

Compare results with different thresholds:

```bash
# Run with threshold 30
SCORE_THRESHOLD=30.0 source .venv/bin/activate && python  scripts/batch_opportunity_scoring.py

# Save results
source .venv/bin/activate && python  -c "
from supabase import create_client
supabase = create_client('http://127.0.0.1:54321', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU')
result = supabase.table('app_opportunities').select('*').gte('opportunity_score', 30).execute()
with open('threshold_30_results.txt', 'w') as f:
    f.write(f'Count: {len(result.data)}\\n')
    for row in result.data:
        f.write(f\"{row['opportunity_score']:.1f} - {row['app_concept'][:60]}\\n\")
"

# Run with threshold 40
SCORE_THRESHOLD=40.0 source .venv/bin/activate && python  scripts/batch_opportunity_scoring.py

# Compare results
diff threshold_30_results.txt threshold_40_results.txt
```

### Scenario 3: Dimension Score Analysis

Identify which dimensions drive high scores:

```bash
source .venv/bin/activate && python  -c "
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


---

## ✅ Agent Validation

**Doit Tasks:** e2e_test, full_scale_collection
**Expected Agent Behavior:** Automated validation and enhancement
**Quality Assurance:** Multi-agent cross-validation
