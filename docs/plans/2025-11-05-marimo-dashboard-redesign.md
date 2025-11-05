# Marimo Dashboard Redesign - Design Document

**Date:** 2025-11-05
**Status:** ✅ Design Validated, Ready for Implementation
**Feature Branch:** feature/marimo-dashboard-enhancement
**Document Type:** Technical Design

---

## Executive Summary

This document outlines the design for a unified marimo dashboard that consolidates 9+ existing dashboards into a single, reactive opportunity analysis interface. The dashboard enables users to discover AI-powered app development opportunities from Reddit data across 6 market sectors.

### Primary User Goal
**"What are the absolute best opportunities across all sectors that I should build?"**

### Key Design Decisions
- Single-page reactive architecture (no tabs, no separate files)
- Two-tier display: Confirmed opportunities + High-scoring candidates
- Dedicated AI insights panel for comparison
- Simple AI processing triggers (no over-engineering)
- Delete all legacy dashboards (clean slate)

---

## Background & Context

### Current State Problems

**Dashboard Chaos:**
- 9+ marimo dashboards exist with overlapping functionality
- No single source of truth
- Unclear which dashboard to use

**Data Model Clarification:**
- 6,127 Reddit submissions (raw data)
- 20 identified opportunities (AI-analyzed)
- Opportunities only exist after AI processing

**Documentation Gap:**
- Existing methodology docs don't match user's vision
- No clear specification for sector comparison
- Missing wireframes/mockups

### User Requirements

Based on brainstorming session:
1. Show best opportunities globally (not sector-first)
2. Allow sector-level comparison within chosen sector
3. AI insights in dedicated panel (not inline)
4. Simple tier-based filtering (High/Med-High/Med)
5. Avoid over-engineering (no real-time progress, no job queues)

---

## Architecture

### High-Level Design

**Type:** Single-page reactive marimo notebook
**File:** `/marimo_notebooks/main_dashboard.py`
**Estimated Size:** ~500-700 lines
**Tech Stack:** marimo + pandas + altair + psycopg2 (all already installed)

### Reactive Cell Structure

```python
# 1. Setup & Configuration (~50 lines)
#    - Imports (marimo, pandas, altair, psycopg2)
#    - Database connection setup
#    - CueTimer brand colors (#FF6B35, #004E89, #F7B801)

# 2. Data Loading (~80 lines)
#    - Query confirmed opportunities (app_concept IS NOT NULL)
#    - Query high-scoring candidates (score >= 70, no AI insights)
#    - Return pandas DataFrames

# 3. Filter Controls (~60 lines)
#    - View mode: All vs By Sector
#    - Priority tier: High (85+), Med-High (70-84), Medium (55-69)
#    - Sector dropdown: 6 sectors

# 4. Filtered Data (~40 lines)
#    - Apply filters reactively
#    - Calculate sector stats (when in sector view)

# 5. Main Display (~120 lines)
#    - Card view (All mode)
#    - Table view (By Sector mode)
#    - Click handling for selection

# 6. AI Insights Panel (~80 lines)
#    - Empty state: "Select an opportunity..."
#    - Populated: app_concept, core_functions, growth_justification
#    - Fixed position (right side)

# 7. Processing Controls (~70 lines)
#    - Status display (20 analyzed, 6,107 awaiting)
#    - Trigger buttons (Top 50, All High Priority, Custom)
#    - Simple subprocess call to existing script
```

### Data Flow

**On Load:**
1. Connect to Supabase (postgres://postgres:postgres@127.0.0.1:54322/postgres)
2. Query `opportunity_analysis` table for both tiers
3. Load into pandas DataFrames (fast, small dataset)
4. Display default view: All opportunities, sorted by score DESC

**On Interaction:**
- User changes filter → Marimo auto-recomputes → UI updates
- User selects opportunity → AI panel updates reactively
- User clicks "Analyze" → Script runs → Data refreshes

---

## User Interface Design

### Page Layout

```
┌────────────────────────────────────────────────────────────┐
│  🎯 RedditHarbor - Opportunity Analysis Dashboard          │
│  📊 20 Opportunities Found | 6,127 Submissions Analyzed    │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  [Filters & Controls Panel]                                │
│  ┌──────────────────────────────────────────────────┐     │
│  │ View: ⦿ All  ○ By Sector                        │     │
│  │ Priority: [High 85+] [Med-High 70-84] [Med 55-69]│     │
│  │ Sector: [All ▼] (shown when By Sector selected) │     │
│  └──────────────────────────────────────────────────┘     │
│                                                             │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  [Main Content: 70% width]   │  [AI Insights Panel: 30%]  │
│                               │                             │
│  ✅ Confirmed Opportunities   │  💡 AI Insights            │
│  ┌─────────────────────┐     │  ┌──────────────────────┐ │
│  │ #1: [Title]         │ ◄───┼──┤ Select an opportunity│ │
│  │ Score: 85           │     │  │ to view AI insights  │ │
│  │ Sector: Tech & SaaS │     │  └──────────────────────┘ │
│  │ [Select]            │     │                            │
│  └─────────────────────┘     │  (When opportunity         │
│                               │   is selected:)            │
│  ┌─────────────────────┐     │  - App Concept            │
│  │ #2: [Title]         │     │  - Core Functions (1-3)   │
│  │ Score: 82           │     │  - Growth Justification   │
│  └─────────────────────┘     │  - Simplicity Score       │
│                               │                            │
│  🔍 High-Scoring Candidates   │                            │
│  ┌─────────────────────┐     │                            │
│  │ [Title] - Score: 78 │     │                            │
│  │ [Analyze This]      │     │                            │
│  └─────────────────────┘     │                            │
│                               │                            │
├────────────────────────────────────────────────────────────┤
│  🤖 AI Processing Controls                                 │
│  📊 Status: 20 analyzed | 6,107 awaiting                  │
│  [Analyze Top 50] [Analyze All High Priority] [Custom]   │
└────────────────────────────────────────────────────────────┘
```

### View Modes

#### Mode 1: All Opportunities (Default)

**Display:** Card-based list showing all opportunities across sectors
**Sorting:** By final_score DESC
**Selection:** Click card to view AI insights in right panel

**Card Content:**
- Title (from submission)
- Score (color-coded by tier)
- Sector badge
- Priority indicator (🔥 High, ⚡ Med-High, 📊 Medium)

#### Mode 2: By Sector

**Display:** Table format for side-by-side comparison within sector
**Trigger:** User toggles "By Sector" and selects sector from dropdown

**Sector Overview Stats:**
- Number of confirmed opportunities
- Number of high-scoring candidates
- Average score
- Score range

**Comparison Table Columns:**
- Rank
- Title
- Score
- App Concept (brief)
- Core Functions (count)

**Click row → AI insights panel shows full details**

### Two-Tier Display

#### Tier 1: ✅ Confirmed Opportunities

**Query:**
```sql
SELECT id, title, sector, final_score,
       app_concept, core_functions, growth_justification,
       simplicity_score, subreddit, created_at
FROM opportunity_analysis
WHERE app_concept IS NOT NULL
ORDER BY final_score DESC
```

**Display:**
- Full details available
- Can view AI insights immediately
- Ready for evaluation

#### Tier 2: 🔍 High-Scoring Candidates

**Query:**
```sql
SELECT id, title, sector, final_score,
       subreddit, created_at
FROM opportunity_analysis
WHERE app_concept IS NULL
AND final_score >= 70
ORDER BY final_score DESC
LIMIT 50
```

**Display:**
- Basic info only (no AI insights yet)
- "Analyze This" button to trigger AI processing
- Shows potential but unconfirmed opportunities

### AI Insights Panel

**Location:** Right side (30% width), fixed position
**Purpose:** Compare opportunities without scrolling

**Empty State:**
```
💡 AI Insights

Select an opportunity from the list
to view detailed AI analysis.
```

**Populated State:**
```
💡 AI Insights

[Opportunity Title]
Score: 85 | Sector: Technology & SaaS

📱 App Concept
[Full app_concept text from database]

⚙️ Core Functions (2)
[core_functions text - must be 1-3 functions]

📈 Growth Justification
[growth_justification text]

🎯 Simplicity Score: 85/100
```

### Priority Tier Filters

**High Priority (85-100):** 🔥
- Immediate development consideration
- Color: `#FF6B35` (CueTimer Orange)

**Medium-High Priority (70-84):** ⚡
- Next quarter planning
- Color: `#F7B801` (Golden Yellow)

**Medium Priority (55-69):** 📊
- Research phase
- Color: `#004E89` (Deep Blue)

**Implementation:**
```python
priority_filter = mo.ui.multiselect({
    "high": "High Priority (85+)",
    "med-high": "Med-High Priority (70-84)",
    "medium": "Medium Priority (55-69)"
})
```

---

## AI Processing Integration

### Simple Trigger Design

**Philosophy:** No over-engineering, use existing scripts

**Processing Controls UI:**

```
🤖 AI Processing Controls

📊 Processing Status:
• 20 opportunities analyzed (AI insights complete)
• 6,107 submissions awaiting analysis
• Last run: 2 hours ago

⚡ Quick Actions:
┌─────────────────────────────────────────────────┐
│ [Analyze Top 50 by Score]  (~5 min, $0.005)    │
│ [Analyze All High Priority] (~1 hr, $0.61)     │
│ [Custom: Enter count ▼]                         │
└─────────────────────────────────────────────────┘

💡 Tip: Start with top 50 to discover new opportunities
    quickly. Costs are estimates based on Claude Haiku.
```

### Implementation Strategy

**What happens when user clicks "Analyze Top 50":**

```python
def trigger_ai_analysis(count: int):
    """Simple subprocess call to existing script"""
    import subprocess

    # Show progress message
    mo.md(f"🔄 Analyzing top {count} submissions...")

    # Run existing script
    result = subprocess.run(
        ["python", "scripts/generate_opportunity_insights_openrouter.py",
         "--limit", str(count)],
        capture_output=True
    )

    # Refresh data (Marimo handles reactivity)
    return mo.md(f"✅ Analysis complete! {count} processed.")
```

**Deliberately NOT implementing:**
- ❌ Real-time progress bars (websocket complexity)
- ❌ Background job queue (infrastructure overhead)
- ❌ Data collection triggers (out of scope)
- ❌ Job scheduling (use cron if needed)

---

## Database Integration

### Connection Setup

```python
import psycopg2

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 54322,
    'database': 'postgres',
    'user': 'postgres',
    'password': 'postgres'
}

def get_db_connection():
    """Create database connection with error handling"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        raise ConnectionError(f"Failed to connect to database: {e}")
```

### Query Functions

**Load Confirmed Opportunities:**
```python
def load_confirmed_opportunities():
    """Query opportunities with AI insights"""
    query = """
        SELECT
            id, title, sector, final_score,
            app_concept, core_functions, growth_justification,
            simplicity_score, subreddit, created_at
        FROM opportunity_analysis
        WHERE app_concept IS NOT NULL
        ORDER BY final_score DESC
    """
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
```

**Load High-Scoring Candidates:**
```python
def load_candidates():
    """Query high-scoring submissions without AI analysis"""
    query = """
        SELECT
            id, title, sector, final_score,
            subreddit, created_at
        FROM opportunity_analysis
        WHERE app_concept IS NULL
        AND final_score >= 70
        ORDER BY final_score DESC
        LIMIT 50
    """
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
```

---

## Error Handling

### Database Connection Failure

```python
try:
    confirmed_df = load_confirmed_opportunities()
    candidates_df = load_candidates()
except ConnectionError as e:
    mo.md("""
    ⚠️ **Database Connection Failed**

    Cannot connect to Supabase. Please check:
    - Is Supabase running? (`supabase status`)
    - Is database accessible on port 54322?

    Error: {e}
    """)
    confirmed_df = pd.DataFrame()  # Empty state
    candidates_df = pd.DataFrame()
```

### No Opportunities Found

```python
if len(confirmed_df) == 0:
    mo.md("""
    📭 **No AI-Analyzed Opportunities Yet**

    No opportunities have been analyzed by AI.
    Use the processing controls below to analyze submissions.

    Current status: {len(candidates_df)} high-scoring candidates available
    """)
```

### AI Processing Failure

```python
try:
    result = trigger_ai_analysis(count)
    mo.md(f"✅ Analysis complete! {count} opportunities processed.")
except Exception as e:
    mo.md(f"""
    ❌ **Analysis Failed**

    Could not process submissions. Error: {e}

    Please check:
    - OPENROUTER_API_KEY is configured
    - Script exists: scripts/generate_opportunity_insights_openrouter.py
    """)
```

---

## Dashboard Cleanup Strategy

### Current Dashboard Inventory

**To be deleted (9 dashboards):**
1. `marimo_notebooks/db_dashboard.py`
2. `marimo_notebooks/top_contenders_dashboard.py`
3. `marimo_notebooks/live_dashboard.py`
4. `marimo_notebooks/simple_opportunity_dashboard.py`
5. `marimo_notebooks/opportunity_insights_dashboard.py`
6. `marimo_notebooks/opportunity_dashboard_reactive.py`
7. `marimo_notebooks/redditharbor_marimo_dashboard.py`
8. `marimo_notebooks/opportunity_analysis_dashboard.py`
9. `simple_redditharbor_dashboard.py` (root file)

**To be created:**
- `marimo_notebooks/main_dashboard.py` (single unified dashboard)

### Cleanup Commands

```bash
# Delete old dashboards
rm marimo_notebooks/db_dashboard.py
rm marimo_notebooks/top_contenders_dashboard.py
rm marimo_notebooks/live_dashboard.py
rm marimo_notebooks/simple_opportunity_dashboard.py
rm marimo_notebooks/opportunity_insights_dashboard.py
rm marimo_notebooks/opportunity_dashboard_reactive.py
rm marimo_notebooks/redditharbor_marimo_dashboard.py
rm marimo_notebooks/opportunity_analysis_dashboard.py
rm simple_redditharbor_dashboard.py

# Verify cleanup
ls marimo_notebooks/*.py
# Should only show: main_dashboard.py
```

---

## Implementation Checklist

### Phase 1: Setup & Data Loading
- [ ] Create `/marimo_notebooks/main_dashboard.py`
- [ ] Set up imports (marimo, pandas, psycopg2, altair)
- [ ] Define CueTimer brand colors
- [ ] Implement database connection
- [ ] Create query functions for both tiers
- [ ] Test data loading with current database

### Phase 2: Basic UI Structure
- [ ] Create header with stats
- [ ] Implement filter controls (view mode, priority, sector)
- [ ] Build card view for "All" mode
- [ ] Build table view for "By Sector" mode
- [ ] Add empty states for no data

### Phase 3: AI Insights Panel
- [ ] Create dedicated panel layout (30% width)
- [ ] Implement empty state
- [ ] Connect to opportunity selection
- [ ] Display app_concept, core_functions, growth_justification
- [ ] Test reactive updates

### Phase 4: Processing Controls
- [ ] Add status display section
- [ ] Create trigger buttons (Top 50, All, Custom)
- [ ] Implement subprocess call to existing script
- [ ] Add progress/completion messages
- [ ] Test AI processing integration

### Phase 5: Testing & Refinement
- [ ] Test all filter combinations
- [ ] Verify reactive behavior
- [ ] Check error handling paths
- [ ] Validate sector comparison view
- [ ] Ensure AI panel updates correctly

### Phase 6: Cleanup
- [ ] Delete all 9 old dashboards
- [ ] Update documentation references
- [ ] Update README with new dashboard location
- [ ] Test dashboard runs: `marimo run marimo_notebooks/main_dashboard.py`

---

## Success Criteria

### Functional Requirements
✅ Single unified dashboard accessible at `/marimo_notebooks/main_dashboard.py`
✅ Shows confirmed opportunities with AI insights
✅ Shows high-scoring candidates awaiting analysis
✅ Dedicated AI insights panel updates reactively
✅ Priority tier filtering works correctly
✅ Sector comparison view displays table format
✅ AI processing triggers work via subprocess
✅ All 9 legacy dashboards deleted

### Performance Requirements
✅ Page loads in < 2 seconds with 20 opportunities
✅ Filter updates feel instant (< 100ms)
✅ AI panel updates without lag
✅ Handles up to 100 opportunities without slowdown

### User Experience Requirements
✅ Clear visual hierarchy (confirmed vs candidates)
✅ Intuitive navigation between view modes
✅ AI insights easily readable and comparable
✅ Processing status clearly communicated
✅ Error states provide actionable guidance

---

## Next Steps

1. **Create Implementation Plan**: Use `superpowers:writing-plans` to create detailed step-by-step tasks
2. **Set Up Isolated Workspace**: Use `superpowers:using-git-worktrees` if needed
3. **Begin Implementation**: Start with Phase 1 (Setup & Data Loading)
4. **Iterative Development**: Complete each phase, test, then move to next
5. **Code Review**: Use `superpowers:requesting-code-review` after implementation

---

## References

- [Marimo Documentation](/.claude/skills/marimo/references/)
- [Methodology](docs/methodology/monetizable_app_research_methodology.md)
- [Integration Complete Memory](memory: redditharbor_marimo_integration_complete)
- [Dashboard Assessment](docs/guides/opportunity-dashboard-assessment.md)

---

**Document Status:** ✅ Design Complete & Validated
**Next Action:** Create implementation plan with detailed tasks
**Estimated Implementation Time:** 8-12 hours
**Risk Level:** Low (using existing dependencies, clear requirements)
