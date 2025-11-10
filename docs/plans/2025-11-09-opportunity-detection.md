# Opportunity Detection System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Connect the existing LLMProfiler to the Supabase database to create a continuous app opportunity discovery engine that transforms Reddit posts into validated app ideas.

**Architecture:**
1. **Phase 1 (Validation):** 50-line proof of concept script to test if LLM output is useful
2. **Phase 2 (MVP):** Production-ready pipeline with database storage, scoring, and filtering
3. **Phase 3 (Optional):** Full automation with scheduled collection, dashboard, and advanced analytics

**Tech Stack:** Python, Supabase, Claude Haiku via OpenRouter, pytest, Marimo

---

## Phase 1: Validation Script (50 lines)

### Task 1: Create 50-line Validation Script

**Files:**
- Create: `scripts/test_opportunity_detection.py`

**Step 1: Write the validation script**

```python
#!/usr/bin/env python3
"""50-line proof of concept: Connect LLMProfiler to Supabase"""

import os
from agent_tools.llm_profiler import LLMProfiler
from supabase import create_client

# Initialize clients
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)
profiler = LLMProfiler()

# Get 10 submissions with content
result = supabase.table('submission').select('*').limit(10).execute()

print("\n" + "="*80)
print("TESTING: LLMProfiler → Supabase Integration")
print("="*80)

count = 0
for sub in result.data:
    if not sub.get('selftext'):
        continue

    count += 1
    if count > 5:  # Limit to 5 for testing
        break

    # Generate profile
    profile = profiler.generate_app_profile(
        text=sub['selftext'],
        title=sub['title'],
        subreddit=sub['subreddit'],
        score=float(sub.get('score', 0))
    )

    # Print results
    print(f"\n[{count}] {sub['title'][:60]}...")
    print(f"    Problem: {profile.get('problem_description', 'N/A')}")
    print(f"    App Idea: {profile.get('app_concept', 'N/A')[:80]}...")
    print(f"    Value Prop: {profile.get('value_proposition', 'N/A')[:80]}...")

print("\n" + "="*80)
print("VALIDATION COMPLETE: Check if output is useful")
print("="*80)
```

**Step 2: Run the validation script**

Run: `python scripts/test_opportunity_detection.py`
Expected: Successfully connects to Supabase, fetches submissions, generates 5 profiles

**Step 3: Review output quality**

Check: Are the generated app ideas actually useful? If yes → proceed to Phase 2. If no → stop and improve LLM prompts.

**Step 4: Commit**

```bash
git add scripts/test_opportunity_detection.py
git commit -m "feat: add 50-line validation script for LLMProfiler integration"
```

---

## Phase 2: Production MVP (300 lines)

### Task 2: Create app_opportunities Database Table

**Files:**
- Create: `supabase/migrations/YYYYMMDDHHMMSS_create_app_opportunities_table.sql`

**Step 1: Write the migration**

```sql
-- Create app_opportunities table for storing LLM-generated app ideas

CREATE TABLE IF NOT EXISTS app_opportunities (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id uuid REFERENCES submission(id) ON DELETE CASCADE,

    -- LLM-generated profile fields (from LLMProfiler)
    problem_description text NOT NULL,
    app_concept text NOT NULL,
    core_functions jsonb NOT NULL,  -- Array of 1-3 strings
    value_proposition text NOT NULL,
    target_user text NOT NULL,
    monetization_model text NOT NULL,

    -- Opportunity scoring (calculated post-generation)
    opportunity_score numeric(5,2) DEFAULT 0.0,  -- 0-100 scale
    market_size_estimate text,
    competition_level text,
    implementation_difficulty text,

    -- Metadata
    template_type text,  -- Which template/filter found this
    created_at timestamptz DEFAULT now(),
    analyzed_at timestamptz DEFAULT now(),

    -- Status tracking
    status text DEFAULT 'discovered' CHECK (status IN ('discovered', 'validated', 'built', 'rejected')),
    notes text
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_app_opportunities_score ON app_opportunities(opportunity_score DESC);
CREATE INDEX IF NOT EXISTS idx_app_opportunities_submission ON app_opportunities(submission_id);
CREATE INDEX IF NOT EXISTS idx_app_opportunities_status ON app_opportunities(status);
CREATE INDEX IF NOT EXISTS idx_app_opportunities_created ON app_opportunities(created_at DESC);

-- Create view for top opportunities
CREATE OR REPLACE VIEW top_opportunities AS
SELECT
    ao.*,
    s.title,
    s.subreddit,
    s.score as reddit_score,
    s.num_comments
FROM app_opportunities ao
JOIN submission s ON ao.submission_id = s.id
WHERE ao.opportunity_score > 60
ORDER BY ao.opportunity_score DESC, ao.created_at DESC;
```

**Step 2: Apply the migration**

Run: `supabase db push`
Expected: Table created successfully with indexes and view

**Step 3: Verify table creation**

Run SQL in Supabase Studio:
```sql
SELECT * FROM top_opportunities LIMIT 5;
```
Expected: Empty result (table exists but no data yet)

**Step 4: Commit**

```bash
git add supabase/migrations/YYYYMMDDHHMMSS_create_app_opportunities_table.sql
git commit -m "feat: add app_opportunities table and top_opportunities view"
```

### Task 3: Create OpportunityAnalyzer Class

**Files:**
- Create: `agent_tools/opportunity_analyzer.py`

**Step 1: Write the test**

```python
import pytest
from agent_tools.opportunity_analyzer import OpportunityAnalyzer

def test_opportunity_analyzer_init():
    """Test OpportunityAnalyzer initialization"""
    analyzer = OpportunityAnalyzer()
    assert analyzer is not None
    assert hasattr(analyzer, 'analyze_opportunity')
    assert hasattr(analyzer, '_calculate_score')

def test_calculate_score_high_engagement():
    """Test scoring for high engagement submission"""
    analyzer = OpportunityAnalyzer()
    score = analyzer._calculate_score(
        reddit_engagement=150,
        num_comments=75,
        problem_clarity="Clear problem with specific pain points",
        solution_feasibility="Simple to implement, well-defined scope"
    )
    assert score > 60
    assert score <= 100

def test_calculate_score_low_engagement():
    """Test scoring for low engagement submission"""
    analyzer = OpportunityAnalyzer()
    score = analyzer._calculate_score(
        reddit_engagement=5,
        num_comments=2,
        problem_clarity="Vague problem statement",
        solution_feasibility="Complex, unclear requirements"
    )
    assert score < 50
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent_tools/test_opportunity_analyzer.py -v`
Expected: FAIL (module doesn't exist yet)

**Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
"""OpportunityAnalyzer - Enhanced LLMProfiler with scoring and validation"""

from typing import Any
from agent_tools.llm_profiler import LLMProfiler


class OpportunityAnalyzer(LLMProfiler):
    """Enhanced profiler with scoring, validation, and market analysis"""

    def analyze_opportunity(self, submission: dict) -> dict[str, Any]:
        """
        Analyze submission and generate scored opportunity profile.

        Args:
            submission: Dict with submission fields (id, title, selftext, subreddit, score, num_comments)

        Returns:
            Dict with app profile + opportunity_score
        """
        # 1. Generate base profile (existing LLMProfiler)
        profile = self.generate_app_profile(
            text=submission.get('selftext', ''),
            title=submission.get('title', ''),
            subreddit=submission.get('subreddit', ''),
            score=float(submission.get('score', 0))
        )

        # 2. Add opportunity scoring
        profile['opportunity_score'] = self._calculate_score(
            reddit_engagement=float(submission.get('score', 0)),
            num_comments=int(submission.get('num_comments', 0)),
            problem_clarity=profile.get('problem_description', ''),
            solution_feasibility=str(profile.get('core_functions', ''))
        )

        return profile

    def _calculate_score(
        self,
        reddit_engagement: float,
        num_comments: int,
        problem_clarity: str,
        solution_feasibility: str
    ) -> float:
        """
        Calculate multi-factor opportunity score (0-100).

        Scoring breakdown:
        - Engagement (0-30): Based on reddit score
        - Comments (0-20): Based on discussion volume
        - Clarity (0-30): Based on problem description quality
        - Feasibility (0-20): Based on solution complexity
        """
        score = 0.0

        # Reddit engagement scoring (0-30 points)
        if reddit_engagement > 100:
            score += 30
        elif reddit_engagement > 50:
            score += 20
        elif reddit_engagement > 10:
            score += 10

        # Comments scoring (0-20 points)
        if num_comments > 50:
            score += 20
        elif num_comments > 20:
            score += 10
        elif num_comments > 5:
            score += 5

        # Problem clarity scoring (0-30 points) - heuristic based on keywords
        clarity_keywords = ['frustrated', 'annoying', 'terrible', 'struggle', 'problem', 'issue']
        clarity_matches = sum(1 for keyword in clarity_keywords if keyword in problem_clarity.lower())
        score += min(clarity_matches * 5, 30)

        # Solution feasibility scoring (0-20 points) - heuristic
        feasible_keywords = ['simple', 'easy', 'basic', 'straightforward']
        feasible_matches = sum(1 for keyword in feasible_keywords if keyword in solution_feasibility.lower())
        score += min(feasible_matches * 5, 20)

        return min(score, 100.0)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/agent_tools/test_opportunity_analyzer.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/agent_tools/test_opportunity_analyzer.py agent_tools/opportunity_analyzer.py
git commit -m "feat: add OpportunityAnalyzer with scoring logic"
```

### Task 4: Create OpportunityPipeline Class

**Files:**
- Create: `scripts/opportunity_pipeline.py`

**Step 1: Write the test**

```python
import pytest
from unittest.mock import Mock, patch
from scripts.opportunity_pipeline import OpportunityPipeline

def test_pipeline_init():
    """Test pipeline initialization"""
    pipeline = OpportunityPipeline()
    assert pipeline is not None
    assert hasattr(pipeline, 'run_pipeline')

@patch('scripts.opportunity_pipeline.create_client')
def test_filter_pain_points(mock_client):
    """Test pain point filtering"""
    pipeline = OpportunityPipeline()

    test_submissions = [
        {'id': 1, 'title': 'I am frustrated with budgeting apps', 'selftext': 'They are terrible'},
        {'id': 2, 'title': 'Great weather today', 'selftext': 'Nice and sunny'},
        {'id': 3, 'title': 'No good solution for meal planning', 'selftext': 'Wish there was an app'}
    ]

    filtered = pipeline._filter_pain_points(test_submissions)
    assert len(filtered) == 2  # First and third submissions
    assert filtered[0]['id'] == 1
    assert filtered[2]['id'] == 3
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/scripts/test_opportunity_pipeline.py -v`
Expected: FAIL (module doesn't exist yet)

**Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
"""Opportunity Pipeline - Automated opportunity discovery and analysis"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent_tools.opportunity_analyzer import OpportunityAnalyzer
from supabase import create_client


class OpportunityPipeline:
    """Automated opportunity discovery and analysis pipeline"""

    def __init__(self):
        """Initialize pipeline with Supabase client and analyzer"""
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
        self.analyzer = OpportunityAnalyzer()

    def run_pipeline(self, batch_size: int = 50) -> Dict[str, Any]:
        """
        Run the full opportunity discovery pipeline.

        Args:
            batch_size: Number of submissions to process

        Returns:
            Dict with processing results
        """
        results = {
            'processed': 0,
            'opportunities_found': 0,
            'errors': 0
        }

        # 1. Get unanalyzed submissions (that haven't been processed yet)
        submissions = self._get_unanalyzed_submissions(batch_size)

        # 2. Filter for pain points
        pain_points = self._filter_pain_points(submissions)

        # 3. Analyze each submission
        for submission in pain_points:
            try:
                # Generate opportunity profile
                opportunity = self.analyzer.analyze_opportunity(submission)

                # Store if score > threshold
                if opportunity.get('opportunity_score', 0) > 60:
                    self._store_opportunity(opportunity, submission['id'])
                    results['opportunities_found'] += 1

                # Mark as analyzed (for tracking)
                self._mark_analyzed(submission['id'])
                results['processed'] += 1

            except Exception as e:
                results['errors'] += 1
                self._log_error(submission['id'], str(e))

        return results

    def _get_unanalyzed_submissions(self, batch_size: int) -> List[Dict[str, Any]]:
        """Get submissions that haven't been analyzed yet"""
        # This is a simplified approach - in production you'd track analyzed submissions
        result = self.supabase.table('submission').select('*').limit(batch_size).execute()
        return result.data

    def _filter_pain_points(self, submissions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter submissions for pain point indicators"""
        pain_keywords = [
            "frustrated", "annoying", "terrible", "wish there was",
            "no good solution", "struggling with", "hate that",
            "why doesn't", "can't find", "looking for"
        ]

        filtered = []
        for sub in submissions:
            # Combine title and text for analysis
            text = f"{sub.get('title', '')} {sub.get('selftext', '')}".lower()

            # Check for pain keywords
            if any(keyword in text for keyword in pain_keywords):
                filtered.append(sub)

        return filtered

    def _store_opportunity(self, opportunity: Dict[str, Any], submission_id: str):
        """Store opportunity in database"""
        self.supabase.table('app_opportunities').insert({
            'submission_id': submission_id,
            'problem_description': opportunity.get('problem_description'),
            'app_concept': opportunity.get('app_concept'),
            'core_functions': opportunity.get('core_functions'),
            'value_proposition': opportunity.get('value_proposition'),
            'target_user': opportunity.get('target_user'),
            'monetization_model': opportunity.get('monetization_model'),
            'opportunity_score': opportunity.get('opportunity_score', 0),
            'status': 'discovered'
        }).execute()

    def _mark_analyzed(self, submission_id: str):
        """Mark submission as analyzed (placeholder for future tracking)"""
        pass  # In production, add column to submission table

    def _log_error(self, submission_id: str, error: str):
        """Log error to error_log directory"""
        import logging
        from datetime import datetime

        error_dir = Path('error_log')
        error_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        error_file = error_dir / f'opportunity_pipeline_{timestamp}.log'

        logging.basicConfig(filename=error_file, level=logging.ERROR)
        logging.error(f"Submission {submission_id}: {error}")


if __name__ == "__main__":
    # Example usage
    pipeline = OpportunityPipeline()
    results = pipeline.run_pipeline(batch_size=50)

    print("\n" + "="*80)
    print("OPPORTUNITY PIPELINE RESULTS")
    print("="*80)
    print(f"Processed: {results['processed']} submissions")
    print(f"Opportunities found: {results['opportunities_found']} (score > 60)")
    print(f"Errors: {results['errors']}")
    print("="*80 + "\n")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/scripts/test_opportunity_pipeline.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/scripts/test_opportunity_pipeline.py scripts/opportunity_pipeline.py
git commit -m "feat: add OpportunityPipeline for automated analysis"
```

### Task 5: Test the Complete MVP

**Files:**
- Modify: `scripts/test_opportunity_detection.py` (update to test MVP)

**Step 1: Write integration test**

```python
#!/usr/bin/env python3
"""Test the complete MVP: LLMProfiler → Database pipeline"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.opportunity_pipeline import OpportunityPipeline

# Initialize pipeline
pipeline = OpportunityPipeline()

print("\n" + "="*80)
print("MVP TEST: Running OpportunityPipeline on 25 submissions")
print("="*80)

# Run pipeline
results = pipeline.run_pipeline(batch_size=25)

print(f"\nResults:")
print(f"  - Processed: {results['processed']} submissions")
print(f"  - Opportunities found: {results['opportunities_found']}")
print(f"  - Errors: {results['errors']}")

# Check top opportunities in database
from supabase import create_client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

top_result = supabase.table('top_opportunities').select('*').limit(5).execute()

print(f"\nTop {len(top_result.data)} Opportunities:")
print("-" * 80)

for idx, opp in enumerate(top_result.data, 1):
    print(f"\n{idx}. Score: {opp.get('opportunity_score', 0):.1f} | r/{opp.get('subreddit', 'unknown')}")
    print(f"   Problem: {opp.get('problem_description', 'N/A')[:100]}...")
    print(f"   App Idea: {opp.get('app_concept', 'N/A')[:100]}...")

print("\n" + "="*80)
print("MVP TEST COMPLETE")
print("="*80)
```

**Step 2: Run the MVP test**

Run: `python scripts/test_opportunity_detection.py`
Expected: Processes 25 submissions, finds 5-15 opportunities, displays top 5

**Step 3: Commit**

```bash
git add scripts/test_opportunity_detection.py
git commit -m "test: add MVP integration test for opportunity pipeline"
```

---

## Phase 3: Full System (Optional - 1000 lines)

### Task 6: Create Marimo Dashboard

**Files:**
- Create: `marimo_notebooks/opportunity_dashboard.py`

**Step 1: Write dashboard**

```python
#!/usr/bin/env python3
"""Marimo Dashboard for App Opportunities"""

import marimo as mo
import os
from supabase import create_client

# Initialize Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Fetch top opportunities
def get_top_opportunities(limit: int = 20):
    result = supabase.table('top_opportunities').select('*').limit(limit).execute()
    return result.data

# Main dashboard
app = mo.App(title="RedditHarbor - App Opportunity Dashboard")

@app.cell
def header():
    return mo.md("# 🎯 App Opportunity Discovery Dashboard")

@app.cell
def controls():
    return mo.ui.slider(
        label="Minimum Score Threshold",
        start=0,
        stop=100,
        value=60,
        step=5
    )

@app.cell
def opportunities_table(threshold):
    data = get_top_opportunities(50)
    filtered = [opp for opp in data if opp.get('opportunity_score', 0) >= threshold]

    if not filtered:
        return mo.md("No opportunities found with the current threshold.")

    table_data = []
    for opp in filtered:
        table_data.append({
            'Score': f"{opp.get('opportunity_score', 0):.1f}",
            'Subreddit': f"r/{opp.get('subreddit', 'unknown')}",
            'Problem': opp.get('problem_description', 'N/A')[:80] + "...",
            'App Concept': opp.get('app_concept', 'N/A')[:80] + "...",
            'Value Prop': opp.get('value_proposition', 'N/A')[:80] + "..."
        })

    return mo.ui.table(table_data, label=f"Top {len(filtered)} Opportunities (Score ≥ {threshold})")

@app.cell
def summary_stats():
    data = get_top_opportunities(100)
    total = len(data)
    avg_score = sum(opp.get('opportunity_score', 0) for opp in data) / total if total > 0 else 0

    return mo.md(f"""
    ### Summary Statistics

    - **Total Opportunities:** {total}
    - **Average Score:** {avg_score:.1f}
    - **High-Score (≥80):** {len([o for o in data if o.get('opportunity_score', 0) >= 80])}
    """)

if __name__ == "__main__":
    app.run()
```

**Step 2: Run the dashboard**

Run: `marimo run marimo_notebooks/opportunity_dashboard.py`
Expected: Dashboard loads in browser showing opportunities

**Step 3: Commit**

```bash
git add marimo_notebooks/opportunity_dashboard.py
git commit -m "feat: add Marimo dashboard for opportunity exploration"
```

### Task 7: Create Tests for Full System

**Files:**
- Create: `tests/integration/test_full_pipeline.py`

**Step 1: Write integration test**

```python
import pytest
import os
from scripts.opportunity_pipeline import OpportunityPipeline
from supabase import create_client


@pytest.mark.integration
def test_full_pipeline_integration():
    """Test complete pipeline from submission to stored opportunity"""
    pipeline = OpportunityPipeline()
    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_KEY')
    )

    # Run pipeline on small batch
    results = pipeline.run_pipeline(batch_size=10)

    # Verify results structure
    assert 'processed' in results
    assert 'opportunities_found' in results
    assert 'errors' in results
    assert results['processed'] >= 0
    assert results['opportunities_found'] >= 0
    assert results['errors'] >= 0

    # Verify opportunities were stored
    if results['opportunities_found'] > 0:
        stored = supabase.table('app_opportunities').select('*').limit(1).execute()
        assert len(stored.data) > 0

        # Verify required fields
        opportunity = stored.data[0]
        required_fields = [
            'problem_description', 'app_concept', 'core_functions',
            'value_proposition', 'target_user', 'monetization_model',
            'opportunity_score'
        ]
        for field in required_fields:
            assert field in opportunity
```

**Step 2: Run integration test**

Run: `pytest tests/integration/test_full_pipeline.py::test_full_pipeline_integration -v -m integration`
Expected: PASS (or skip if no test data)

**Step 3: Commit**

```bash
git add tests/integration/test_full_pipeline.py
git commit -m "test: add integration test for full pipeline"
```

---

## Summary

**Completion Criteria:**

- [ ] Phase 1 (Validation) complete: 50-line script runs and produces useful output
- [ ] Phase 2 (MVP) complete: Database table, OpportunityAnalyzer, Pipeline all working
- [ ] Tests passing: Unit tests and integration tests verify functionality
- [ ] Manual testing: Pipeline successfully processes submissions and stores opportunities
- [ ] Quality check: Generated app ideas are actually useful (not generic)

**Total Estimated Lines:** 400-600 (significantly less than initial estimate)
**Estimated Time:** 1-2 days for MVP

**Next Steps After MVP:**
- Automate with cron or Supabase Edge Functions
- Add market analysis and competition checking
- Add email digest of top opportunities
- Build production dashboard with filtering and search
