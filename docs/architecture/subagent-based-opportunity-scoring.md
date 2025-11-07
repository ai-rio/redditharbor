# Subagent-Based Opportunity Scoring Architecture

**Status:** Planning
**Date:** 2025-11-05
**Decision:** Use specialized subagents for opportunity scoring pipeline implementation

## Context

RedditHarbor has collected 6,127 enhanced submissions across 68 subreddits with sentiment analysis, problem keywords, and solution mentions. We need to process this data to identify clear app opportunity contenders across sectors using the 6-dimensional scoring methodology.

## Decision

Implement a **multi-phase subagent-based architecture** where specialized agents handle different aspects of the opportunity scoring pipeline, avoiding context window flooding and leveraging expertise.

## Architecture Overview

```
┌───────────────────────────────────────────────────────┐
│ Phase 1: Database Infrastructure                      │
│ Subagent: supabase-toolkit:data-engineer              │
│ ├─ Create opportunity_analysis table                  │
│ ├─ Add indexes for query performance                  │
│ └─ Run Supabase migration                             │
└───────────────────────────────────────────────────────┘
                        ↓
┌───────────────────────────────────────────────────────┐
│ Phase 2: Batch Scoring Script                         │
│ Subagent: python-pro                                  │
│ ├─ Build batch_opportunity_scoring.py                 │
│ ├─ Integrate OpportunityAnalyzerAgent                 │
│ ├─ Process 6,127 submissions in batches               │
│ └─ Store scored results in Supabase                   │
└───────────────────────────────────────────────────────┘
                        ↓
┌───────────────────────────────────────────────────────┐
│ Phase 3: Interactive Dashboard                        │
│ Subagent: marimo-specialist                           │
│ ├─ Create top_contenders_dashboard.py                 │
│ ├─ Build reactive UI (filters, sliders)               │
│ ├─ Query opportunity_analysis table                   │
│ └─ Visualize top contenders by sector                 │
└───────────────────────────────────────────────────────┘
                        ↓
┌───────────────────────────────────────────────────────┐
│ Phase 4: Analytics & Insights                         │
│ Subagent: data-scientist / data-analyst               │
│ ├─ Statistical validation of scores                   │
│ ├─ Sector correlation analysis                        │
│ └─ Generate insights and export reports               │
└───────────────────────────────────────────────────────┘
```

## Technology Stack Alignment

| Component | Technology | Subagent |
|-----------|------------|----------|
| **Database** | Supabase PostgreSQL | supabase-toolkit:data-engineer |
| **Scoring Logic** | Python, pandas | python-pro |
| **Dashboard** | Marimo, altair | marimo-specialist |
| **Analytics** | Python, scipy/numpy | data-scientist |

## Subagent Responsibilities

### Phase 1: Database Infrastructure (data-engineer)

**Responsibilities:**
- Design `opportunity_analysis` table schema
- Define dimension score columns (market_demand, pain_intensity, etc.)
- Create indexes for efficient querying
- Write Supabase migration file
- Apply migration to database

**Deliverables:**
- `supabase/migrations/XXXXXX_opportunity_scoring_tables.sql`
- Table with proper constraints and indexes
- Documentation of schema design

**Estimated Time:** 10-15 minutes

---

### Phase 2: Batch Scoring Script (python-pro)

**Responsibilities:**
- Create `scripts/batch_opportunity_scoring.py`
- Integrate with existing `OpportunityAnalyzerAgent` (`agent_tools/opportunity_analyzer_agent.py`)
- Implement batch processing (100 submissions per batch)
- Add progress tracking and logging
- Handle errors gracefully
- Store results in Supabase `opportunity_analysis` table

**Deliverables:**
- `scripts/batch_opportunity_scoring.py`
- Type hints and docstrings
- Error handling and logging
- Progress reporting

**Estimated Time:** 15-20 minutes

**Key Integration Points:**
```python
from agent_tools.opportunity_analyzer_agent import OpportunityAnalyzerAgent
from config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client

agent = OpportunityAnalyzerAgent()
results = agent.batch_analyze_opportunities(submissions)
```

---

### Phase 3: Interactive Dashboard (marimo-specialist)

**Responsibilities:**
- Create `marimo_notebooks/top_contenders_dashboard.py`
- Build reactive UI components:
  - Sector filter dropdown (6 sectors)
  - Score range sliders (0-100)
  - Top N selector (10, 20, 50, 100)
  - Simplicity score validator (1-3 functions)
- Query `opportunity_analysis` table
- Create visualizations:
  - Score distribution by sector
  - Top opportunities table
  - Dimension breakdown charts
  - Priority distribution

**Deliverables:**
- `marimo_notebooks/top_contenders_dashboard.py`
- Reactive marimo cells following patterns
- Altair/plotly visualizations
- Export functionality (JSON/CSV)

**Estimated Time:** 20-25 minutes

**Critical Pattern:**
```python
@app.cell
def _(mo):
    sector_selector = mo.ui.dropdown(
        options=["Health & Fitness", "Finance & Investing", ...]
    )
    return sector_selector,
```

---

### Phase 4: Analytics & Insights (data-scientist)

**Responsibilities:**
- Statistical validation of scoring methodology
- Correlation analysis (sentiment vs monetization)
- Sector comparison analysis
- Identify scoring patterns and anomalies
- Generate insights report
- Export top contenders by sector

**Deliverables:**
- Statistical validation report
- Correlation matrices
- Sector insights summary
- Top 20 contenders per sector (JSON/CSV)

**Estimated Time:** 15-20 minutes

## Data Flow

```
Supabase (submissions table)
    ↓ [6,127 submissions with metadata]
OpportunityAnalyzerAgent
    ↓ [5-dimension scoring]
Supabase (opportunity_analysis table)
    ↓ [Scored opportunities]
Marimo Dashboard
    ↓ [Interactive filtering/visualization]
Top Contenders Report
```

## Scoring Dimensions (6-Dimensional)

1. **Market Demand** (20%) - Engagement metrics, discussion volume
2. **Pain Intensity** (25%) - Sentiment score, problem keywords
3. **Monetization Potential** (20%) - Payment willingness signals
4. **Market Gap Analysis** (10%) - Competition density, inadequacy
5. **Technical Feasibility** (5%) - Development complexity
6. **Simplicity Score** (20%) - CRITICAL: 1-3 core functions max

### Simplicity Constraint
- 1 core function = 100 points
- 2 core functions = 85 points
- 3 core functions = 70 points
- 4+ core functions = DISQUALIFIED (0 points)

## Execution Strategy

### Parallel Execution (Phase 1 & 2)
- Launch **data-engineer** and **python-pro** simultaneously
- data-engineer creates table schema
- python-pro builds scoring script (can use mock data for testing)
- Once table exists, python-pro script can write to it

### Sequential Execution (Phase 3 & 4)
- **marimo-specialist** requires completed Phase 2 (scored data in DB)
- **data-scientist** requires completed Phase 2 for analysis

## Expected Outputs

### 1. Database Table
```sql
CREATE TABLE opportunity_analysis (
    id BIGSERIAL PRIMARY KEY,
    submission_id TEXT NOT NULL,
    opportunity_id TEXT UNIQUE NOT NULL,
    title TEXT,
    subreddit TEXT,
    sector TEXT,
    market_demand NUMERIC(5,2),
    pain_intensity NUMERIC(5,2),
    monetization_potential NUMERIC(5,2),
    market_gap NUMERIC(5,2),
    technical_feasibility NUMERIC(5,2),
    simplicity_score NUMERIC(5,2),
    final_score NUMERIC(5,2),
    priority TEXT,
    scored_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (submission_id) REFERENCES submission(submission_id)
);
```

### 2. Batch Scoring Results
- 6,127 opportunities scored
- Results stored in `opportunity_analysis` table
- Processing time: ~15-20 minutes
- Success rate: > 99%

### 3. Dashboard Interface
- Real-time sector filtering
- Interactive score range selection
- Top N selector (configurable)
- Export functionality

### 4. Analytics Report
- Top 20 opportunities per sector (120 total)
- Statistical validation of methodology
- Correlation insights
- Recommended priorities

## Rationale

### Why Subagents?

1. **Context Window Management** - Prevents flooding main context with implementation details
2. **Expertise Specialization** - Each subagent is expert in their domain
3. **Parallel Execution** - Phase 1 & 2 can run simultaneously
4. **Clean Separation** - Database, logic, UI, analytics cleanly separated
5. **Maintainability** - Each component can be updated independently

### Why This Technology Stack?

1. **Python** - Existing codebase language, rich data science ecosystem
2. **Supabase** - Already integrated, PostgreSQL power
3. **Marimo** - Reactive notebooks, proven in project
4. **OpportunityAnalyzerAgent** - Already built and tested

### Alternative Approaches Considered

1. **Single Monolithic Script** - ❌ Too complex, hard to maintain
2. **Agent SDK for Scoring** - ❌ Expensive, slow for 6K+ items
3. **Manual SQL Analysis** - ❌ Not scalable, no UI
4. **External ML Service** - ❌ Overkill, unnecessary complexity

## Success Metrics

- ✅ All 6,127 submissions scored
- ✅ Processing time < 30 minutes
- ✅ Dashboard loads in < 3 seconds
- ✅ Top 20 contenders per sector identified
- ✅ Statistical validation confirms methodology
- ✅ Simplicity constraint enforced

## Next Steps

1. Launch Phase 1 & 2 subagents in parallel
2. Monitor progress and resolve blockers
3. Launch Phase 3 once data is scored
4. Launch Phase 4 for insights generation
5. Review and iterate on results

## References

- [Monetizable App Research Methodology](../methodology/monetizable-app-research-methodology.md)
- [OpportunityAnalyzerAgent](../../agent_tools/opportunity_analyzer_agent.py)
- [Marimo Integration Complete](../../.serena/memories/redditharbor_marimo_integration_complete.md)
- [Enhanced Collection Results](../implementation/monetizable-collection-implementation.md)
