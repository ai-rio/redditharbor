# Marimo Dashboard Redesign - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a unified marimo dashboard that consolidates 9+ legacy dashboards into one reactive interface for discovering AI-powered app opportunities from Reddit data.

**Architecture:** Single-page reactive marimo notebook with two-tier display (confirmed opportunities + candidates), dedicated AI insights panel, sector comparison view, and simple AI processing triggers. Uses marimo's reactive cells for automatic UI updates.

**Tech Stack:** marimo 0.17.6, pandas 2.3.3, altair 5.5.0, psycopg2 2.9.11 (all already installed)

---

## Implementation Strategy

**Approach:** Build incrementally with manual testing at each step (no automated tests for marimo notebooks per project conventions). Each task is 2-5 minutes of focused work with immediate verification.

**Testing:** Run `marimo edit marimo_notebooks/main_dashboard.py` after each major milestone to verify reactive behavior.

**Commits:** Frequent, atomic commits after each functional unit (every 3-5 steps).

---

## Task 1: Setup & Configuration

**Files:**
- Create: `marimo_notebooks/main_dashboard.py`

### Step 1: Create notebook file with imports

Create `/marimo_notebooks/main_dashboard.py`:

```python
"""
RedditHarbor Main Dashboard

Unified opportunity analysis dashboard for discovering AI-powered
app development opportunities from Reddit data.
"""

import marimo

__generated_with = "0.17.6"
app = marimo.App(width="full")


@app.cell
def setup_imports():
    import marimo as mo
    import pandas as pd
    import psycopg2
    from typing import Optional, Dict, List
    import subprocess
    from datetime import datetime

    return mo, pd, psycopg2, Optional, Dict, List, subprocess, datetime


@app.cell
def define_colors():
    """CueTimer brand colors for consistent styling"""
    COLORS = {
        'primary': '#FF6B35',     # Vibrant Orange
        'secondary': '#004E89',   # Deep Blue
        'accent': '#F7B801',      # Golden Yellow
        'text': '#1A1A1A',        # Dark Gray
        'light': '#F5F5F5',       # Light Gray
        'white': '#FFFFFF'
    }

    return COLORS,


if __name__ == "__main__":
    app.run()
```

### Step 2: Test notebook launches

Run: `marimo edit marimo_notebooks/main_dashboard.py`
Expected: Browser opens at http://localhost:2718, shows empty notebook with imports cell

### Step 3: Add database configuration

Add cell after `define_colors`:

```python
@app.cell
def database_config(marimo_notebooks):
    """Database connection configuration"""
    # Use existing config module
    from marimo_notebooks.config import MarimoConfig

    config = MarimoConfig()

    DB_CONFIG = {
        'host': '127.0.0.1',
        'port': 54322,
        'database': 'postgres',
        'user': 'postgres',
        'password': 'postgres'
    }

    return config, DB_CONFIG


if __name__ == "__main__":
    app.run()
```

### Step 4: Verify configuration loads

Run: `marimo edit marimo_notebooks/main_dashboard.py`
Expected: No errors, config cell executes successfully

### Step 5: Commit setup

```bash
git add marimo_notebooks/main_dashboard.py
git commit -m "feat: create main dashboard with imports and config

- Add marimo app structure
- Import required libraries (pandas, psycopg2)
- Define CueTimer brand colors
- Configure database connection"
```

---

## Task 2: Database Connection & Data Loading

**Files:**
- Modify: `marimo_notebooks/main_dashboard.py`

### Step 1: Add database connection function

Add cell after `database_config`:

```python
@app.cell
def database_connection(DB_CONFIG, psycopg2, mo):
    """Create database connection with error handling"""

    def get_db_connection():
        """Connect to PostgreSQL database"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            return conn
        except Exception as e:
            raise ConnectionError(f"Failed to connect to database: {e}")

    # Test connection
    try:
        test_conn = get_db_connection()
        test_conn.close()
        connection_status = mo.md("✅ **Database:** Connected")
    except Exception as e:
        connection_status = mo.md(f"⚠️ **Database:** Connection failed - {e}")

    return get_db_connection, connection_status
```

### Step 2: Test database connection

Run: `marimo edit marimo_notebooks/main_dashboard.py`
Expected: See "✅ **Database:** Connected" or error message
Action: If error, ensure Supabase is running: `supabase status`

### Step 3: Add query for confirmed opportunities

Add cell:

```python
@app.cell
def load_confirmed_opportunities(get_db_connection, pd):
    """Query opportunities with AI insights"""

    def fetch_confirmed():
        query = """
            SELECT
                id, title, sector, final_score,
                app_concept, core_functions, growth_justification,
                simplicity_score, subreddit, created_at
            FROM opportunity_analysis
            WHERE app_concept IS NOT NULL
            ORDER BY final_score DESC
        """

        try:
            conn = get_db_connection()
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Error loading confirmed opportunities: {e}")
            return pd.DataFrame()

    confirmed_df = fetch_confirmed()

    return fetch_confirmed, confirmed_df
```

### Step 4: Add query for high-scoring candidates

Add cell:

```python
@app.cell
def load_candidates(get_db_connection, pd):
    """Query high-scoring submissions without AI analysis"""

    def fetch_candidates():
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

        try:
            conn = get_db_connection()
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Error loading candidates: {e}")
            return pd.DataFrame()

    candidates_df = fetch_candidates()

    return fetch_candidates, candidates_df
```

### Step 5: Add data summary display

Add cell:

```python
@app.cell
def data_summary(mo, confirmed_df, candidates_df):
    """Display data loading summary"""

    confirmed_count = len(confirmed_df)
    candidates_count = len(candidates_df)
    total_analyzed = 6127  # From database

    summary = mo.md(f"""
    ## 📊 Data Summary

    - **{confirmed_count}** Opportunities Found (AI-analyzed)
    - **{candidates_count}** High-Scoring Candidates (awaiting AI)
    - **{total_analyzed:,}** Total Submissions Analyzed
    """)

    return summary,
```

### Step 6: Test data loading

Run: `marimo edit marimo_notebooks/main_dashboard.py`
Expected: See data summary with counts (20 opportunities, ~50 candidates)

### Step 7: Commit data loading

```bash
git add marimo_notebooks/main_dashboard.py
git commit -m "feat: add database queries and data loading

- Implement database connection with error handling
- Add query for confirmed opportunities
- Add query for high-scoring candidates
- Display data summary stats"
```

---

## Task 3: Header & Filter Controls

**Files:**
- Modify: `marimo_notebooks/main_dashboard.py`

### Step 1: Add dashboard header

Add cell after data_summary:

```python
@app.cell
def dashboard_header(mo, COLORS):
    """Main dashboard header with title"""

    header = mo.md(f"""
    <div style="background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
                padding: 2rem;
                border-radius: 12px;
                margin-bottom: 2rem;
                color: white;">
        <h1 style="margin: 0; font-size: 2.5rem;">🎯 RedditHarbor Opportunity Dashboard</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">
            Discover AI-powered app development opportunities from Reddit discussions
        </p>
    </div>
    """)

    return header,
```

### Step 2: Add view mode toggle

Add cell:

```python
@app.cell
def view_mode_control(mo):
    """Toggle between All and By Sector views"""

    view_mode = mo.ui.radio(
        options=["All", "By Sector"],
        value="All",
        label="**View Mode:**"
    )

    return view_mode,
```

### Step 3: Add priority tier filter

Add cell:

```python
@app.cell
def priority_filter_control(mo, COLORS):
    """Filter by priority tiers"""

    priority_options = {
        "high": f"🔥 High Priority (85+)",
        "med-high": f"⚡ Med-High Priority (70-84)",
        "medium": f"📊 Medium Priority (55-69)"
    }

    priority_filter = mo.ui.multiselect(
        options=priority_options,
        value=list(priority_options.keys()),  # All selected by default
        label="**Priority Tiers:**"
    )

    return priority_filter, priority_options
```

### Step 4: Add sector dropdown

Add cell:

```python
@app.cell
def sector_dropdown_control(mo, confirmed_df):
    """Sector selection dropdown"""

    # Get unique sectors from data
    sectors = ["All"] + sorted(confirmed_df['sector'].unique().tolist()) if len(confirmed_df) > 0 else ["All"]

    sector_dropdown = mo.ui.dropdown(
        options=sectors,
        value="All",
        label="**Sector:**"
    )

    return sector_dropdown, sectors
```

### Step 5: Display filter controls

Add cell:

```python
@app.cell
def filter_panel(mo, view_mode, priority_filter, sector_dropdown):
    """Combine all filters into panel"""

    # Show sector dropdown only in "By Sector" mode
    if view_mode.value == "By Sector":
        filters = mo.vstack([
            view_mode,
            priority_filter,
            sector_dropdown
        ])
    else:
        filters = mo.vstack([
            view_mode,
            priority_filter
        ])

    return filters,
```

### Step 6: Test filter controls

Run: `marimo edit marimo_notebooks/main_dashboard.py`
Expected: See header, view mode toggle, priority checkboxes
Action: Toggle "By Sector" → sector dropdown appears

### Step 7: Commit filters

```bash
git add marimo_notebooks/main_dashboard.py
git commit -m "feat: add header and filter controls

- Create branded header with CueTimer colors
- Add view mode toggle (All vs By Sector)
- Add priority tier multiselect filter
- Add sector dropdown (reactive to view mode)"
```

---

## Task 4: Apply Filters to Data

**Files:**
- Modify: `marimo_notebooks/main_dashboard.py`

### Step 1: Create filter application function

Add cell:

```python
@app.cell
def apply_filters_to_data(confirmed_df, priority_filter, sector_dropdown, view_mode):
    """Apply selected filters to opportunities data"""

    filtered_df = confirmed_df.copy()

    # Apply priority tier filter
    priority_selected = priority_filter.value

    priority_ranges = {
        "high": (85, 100),
        "med-high": (70, 84),
        "medium": (55, 69)
    }

    # Filter by selected priority tiers
    if priority_selected:
        mask = False
        for tier in priority_selected:
            if tier in priority_ranges:
                low, high = priority_ranges[tier]
                mask |= (filtered_df['final_score'] >= low) & (filtered_df['final_score'] <= high)

        filtered_df = filtered_df[mask]

    # Apply sector filter (only in "By Sector" mode)
    if view_mode.value == "By Sector" and sector_dropdown.value != "All":
        filtered_df = filtered_df[filtered_df['sector'] == sector_dropdown.value]

    return filtered_df,
```

### Step 2: Calculate sector stats

Add cell:

```python
@app.cell
def calculate_sector_stats(filtered_df, candidates_df, view_mode, sector_dropdown):
    """Calculate statistics for sector view"""

    if view_mode.value == "By Sector" and sector_dropdown.value != "All":
        sector_name = sector_dropdown.value

        # Stats for confirmed opportunities
        confirmed_count = len(filtered_df)
        avg_score = filtered_df['final_score'].mean() if confirmed_count > 0 else 0
        score_range = (
            filtered_df['final_score'].min(),
            filtered_df['final_score'].max()
        ) if confirmed_count > 0 else (0, 0)

        # Count candidates in this sector
        sector_candidates = len(candidates_df[candidates_df['sector'] == sector_name]) if len(candidates_df) > 0 else 0

        stats = {
            'sector': sector_name,
            'confirmed_count': confirmed_count,
            'candidates_count': sector_candidates,
            'avg_score': avg_score,
            'score_range': score_range
        }
    else:
        stats = None

    return stats,
```

### Step 3: Display sector stats (when applicable)

Add cell:

```python
@app.cell
def sector_stats_display(mo, stats):
    """Show sector overview stats in By Sector mode"""

    if stats:
        display = mo.md(f"""
        ### 📊 {stats['sector']} Overview

        - **{stats['confirmed_count']}** Confirmed Opportunities
        - **{stats['candidates_count']}** High-Scoring Candidates
        - **Average Score:** {stats['avg_score']:.1f}
        - **Score Range:** {stats['score_range'][0]:.0f} - {stats['score_range'][1]:.0f}
        """)
    else:
        display = mo.md("")

    return display,
```

### Step 4: Test filtering

Run: `marimo edit marimo_notebooks/main_dashboard.py`
Expected: Filter controls update data count when changed
Action: Uncheck priority tier → count decreases
Action: Select "By Sector" + choose sector → see sector stats

### Step 5: Commit filtering logic

```bash
git add marimo_notebooks/main_dashboard.py
git commit -m "feat: implement reactive filtering logic

- Apply priority tier filters to data
- Apply sector filter in By Sector mode
- Calculate sector statistics
- Display sector overview stats"
```

---

## Task 5: Main Display - Card View

**Files:**
- Modify: `marimo_notebooks/main_dashboard.py`

### Step 1: Add priority badge function

Add cell:

```python
@app.cell
def get_priority_badge(COLORS):
    """Get priority badge emoji and color based on score"""

    def badge_for_score(score):
        if score >= 85:
            return "🔥", COLORS['primary'], "High"
        elif score >= 70:
            return "⚡", COLORS['accent'], "Med-High"
        elif score >= 55:
            return "📊", COLORS['secondary'], "Medium"
        else:
            return "📋", COLORS['light'], "Low"

    return badge_for_score,
```

### Step 2: Create opportunity card component

Add cell:

```python
@app.cell
def create_opportunity_card(mo, badge_for_score, COLORS):
    """Generate HTML for a single opportunity card"""

    def render_card(row, index):
        emoji, color, priority = badge_for_score(row['final_score'])

        card_html = f"""
        <div style="
            border: 2px solid {COLORS['light']};
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            cursor: pointer;
            transition: all 0.2s;
            background: white;
        "
        data-id="{row['id']}">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <h3 style="margin: 0 0 0.5rem 0; color: {COLORS['text']};">
                    #{index + 1}: {row['title'][:80]}...
                </h3>
                <div style="background: {color}; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.85rem;">
                    {emoji} {priority}
                </div>
            </div>
            <div style="display: flex; gap: 1rem; color: {COLORS['secondary']}; font-size: 0.9rem;">
                <span>📊 Score: <strong>{row['final_score']:.0f}</strong></span>
                <span>🏢 {row['sector']}</span>
                <span>📱 r/{row['subreddit']}</span>
            </div>
        </div>
        """

        return card_html

    return render_card,
```

### Step 3: Display confirmed opportunities section

Add cell:

```python
@app.cell
def display_confirmed_opportunities(mo, filtered_df, render_card):
    """Show confirmed opportunities in card view"""

    if len(filtered_df) == 0:
        display = mo.md("""
        ### ✅ Confirmed Opportunities

        📭 No opportunities match your filters.
        Try adjusting the priority tier or sector selection.
        """)
    else:
        cards_html = "### ✅ Confirmed Opportunities\n\n"

        for idx, row in filtered_df.iterrows():
            cards_html += render_card(row, idx)

        display = mo.Html(cards_html)

    return display,
```

### Step 4: Display high-scoring candidates section

Add cell:

```python
@app.cell
def display_candidates_section(mo, candidates_df, COLORS):
    """Show high-scoring candidates awaiting AI analysis"""

    if len(candidates_df) == 0:
        display = mo.md("")
    else:
        candidates_html = f"""
        <div style="margin-top: 2rem;">
            <h3>🔍 High-Scoring Candidates</h3>
            <p style="color: {COLORS['secondary']};">
                These submissions scored ≥70 but haven't been analyzed by AI yet.
            </p>
        """

        for idx, row in candidates_df.head(10).iterrows():
            candidates_html += f"""
            <div style="
                border: 1px dashed {COLORS['light']};
                border-radius: 6px;
                padding: 0.75rem;
                margin-bottom: 0.5rem;
                background: {COLORS['light']};
            ">
                <div style="font-weight: 600; margin-bottom: 0.25rem;">
                    {row['title'][:80]}...
                </div>
                <div style="font-size: 0.85rem; color: {COLORS['secondary']};">
                    Score: {row['final_score']:.0f} | {row['sector']} | r/{row['subreddit']}
                </div>
            </div>
            """

        candidates_html += "</div>"
        display = mo.Html(candidates_html)

    return display,
```

### Step 5: Test card view

Run: `marimo edit marimo_notebooks/main_dashboard.py`
Expected: See opportunity cards with scores, sectors, priority badges
Expected: See candidates section below confirmed opportunities

### Step 6: Commit card view

```bash
git add marimo_notebooks/main_dashboard.py
git commit -m "feat: implement card view for opportunities

- Add priority badge function with color coding
- Create opportunity card component
- Display confirmed opportunities as cards
- Display high-scoring candidates section"
```

---

## Task 6: Main Display - Table View (Sector Mode)

**Files:**
- Modify: `marimo_notebooks/main_dashboard.py`

### Step 1: Create table view component

Add cell:

```python
@app.cell
def create_table_view(mo, filtered_df, badge_for_score, view_mode):
    """Display opportunities in table format for sector comparison"""

    if view_mode.value != "By Sector" or len(filtered_df) == 0:
        table_display = mo.md("")
    else:
        # Prepare table data
        table_data = []

        for idx, row in filtered_df.iterrows():
            emoji, color, priority = badge_for_score(row['final_score'])

            # Truncate app concept for table display
            concept_brief = row['app_concept'][:60] + "..." if pd.notna(row['app_concept']) and len(str(row['app_concept'])) > 60 else row['app_concept']

            # Extract function count from core_functions
            functions_text = str(row['core_functions']) if pd.notna(row['core_functions']) else ""
            function_count = functions_text.count('\n') + 1 if functions_text else 0

            table_data.append({
                'Rank': f"#{idx + 1}",
                'Title': row['title'][:50] + "..." if len(row['title']) > 50 else row['title'],
                'Score': f"{emoji} {row['final_score']:.0f}",
                'App Concept': concept_brief,
                'Functions': function_count,
                'Priority': priority
            })

        # Convert to DataFrame for marimo table
        table_df = pd.DataFrame(table_data)

        table_display = mo.ui.table(
            table_df,
            selection="single",
            label="**Sector Opportunities Comparison**"
        )

    return table_display,
```

### Step 2: Add conditional display logic

Add cell:

```python
@app.cell
def main_content_display(view_mode, display, table_display):
    """Show either card view or table view based on mode"""

    if view_mode.value == "All":
        content = display  # Card view
    else:
        content = table_display  # Table view

    return content,
```

### Step 3: Test table view

Run: `marimo edit marimo_notebooks/main_dashboard.py`
Expected: In "All" mode → see cards
Action: Switch to "By Sector" → see table with sortable columns

### Step 4: Commit table view

```bash
git add marimo_notebooks/main_dashboard.py
git commit -m "feat: add table view for sector comparison

- Create table component for By Sector mode
- Show rank, score, concept, functions count
- Enable single row selection
- Switch between card and table views"
```

---

## Task 7: AI Insights Panel

**Files:**
- Modify: `marimo_notebooks/main_dashboard.py`

### Step 1: Add selected opportunity state

Add cell:

```python
@app.cell
def opportunity_selection_state(mo):
    """Track which opportunity is currently selected"""

    selected_opportunity_id = mo.ui.number(
        value=None,
        label="Selected Opportunity ID (internal)"
    )

    return selected_opportunity_id,
```

### Step 2: Create AI insights panel component

Add cell:

```python
@app.cell
def ai_insights_panel(mo, selected_opportunity_id, confirmed_df, COLORS):
    """Display AI insights for selected opportunity"""

    # Find selected opportunity in dataframe
    if selected_opportunity_id.value and len(confirmed_df) > 0:
        opp = confirmed_df[confirmed_df['id'] == selected_opportunity_id.value]

        if len(opp) > 0:
            row = opp.iloc[0]

            panel = mo.md(f"""
            <div style="
                background: white;
                border: 2px solid {COLORS['primary']};
                border-radius: 8px;
                padding: 1.5rem;
                position: sticky;
                top: 20px;
            ">
                <h2 style="color: {COLORS['primary']}; margin-top: 0;">💡 AI Insights</h2>

                <h3 style="color: {COLORS['text']};">{row['title']}</h3>

                <div style="margin-bottom: 1rem; color: {COLORS['secondary']};">
                    <strong>Score:</strong> {row['final_score']:.0f} |
                    <strong>Sector:</strong> {row['sector']}
                </div>

                <h4 style="color: {COLORS['secondary']};">📱 App Concept</h4>
                <p style="line-height: 1.6;">{row['app_concept']}</p>

                <h4 style="color: {COLORS['secondary']};">⚙️ Core Functions</h4>
                <pre style="background: {COLORS['light']}; padding: 1rem; border-radius: 4px; white-space: pre-wrap;">
{row['core_functions']}
                </pre>

                <h4 style="color: {COLORS['secondary']};">📈 Growth Justification</h4>
                <p style="line-height: 1.6;">{row['growth_justification']}</p>

                <div style="
                    background: {COLORS['accent']};
                    color: {COLORS['text']};
                    padding: 0.75rem;
                    border-radius: 4px;
                    margin-top: 1rem;
                    font-weight: 600;
                ">
                    🎯 Simplicity Score: {row['simplicity_score']:.0f}/100
                </div>
            </div>
            """)
        else:
            panel = mo.md("")
    else:
        # Empty state
        panel = mo.md(f"""
        <div style="
            background: {COLORS['light']};
            border: 2px dashed {COLORS['secondary']};
            border-radius: 8px;
            padding: 2rem;
            text-align: center;
            position: sticky;
            top: 20px;
        ">
            <h2>💡 AI Insights</h2>
            <p style="color: {COLORS['secondary']};">
                Select an opportunity from the list<br/>
                to view detailed AI analysis.
            </p>
        </div>
        """)

    return panel,
```

### Step 3: Create two-column layout

Add cell:

```python
@app.cell
def main_layout(mo, main_content_display, ai_insights_panel):
    """Combine main content and AI panel in two-column layout"""

    layout = mo.hstack([
        mo.vstack([main_content_display], justify="start", gap=1, widths=[7]),
        mo.vstack([ai_insights_panel], justify="start", gap=1, widths=[3])
    ], gap=2)

    return layout,
```

### Step 4: Test AI insights panel

Run: `marimo edit marimo_notebooks/main_dashboard.py`
Expected: See empty state "Select an opportunity..."
Note: Selection mechanism will be added in next task

### Step 5: Commit AI insights panel

```bash
git add marimo_notebooks/main_dashboard.py
git commit -m "feat: add AI insights panel

- Create opportunity selection state
- Build AI insights panel with empty state
- Display app concept, functions, growth justification
- Show simplicity score badge
- Implement two-column layout (70/30 split)"
```

---

## Task 8: Connect Selection to AI Panel

**Files:**
- Modify: `marimo_notebooks/main_dashboard.py`

### Step 1: Add click handling for card view

Modify `create_opportunity_card` cell to add click handler:

```python
@app.cell
def create_opportunity_card_with_click(mo, badge_for_score, COLORS, selected_opportunity_id):
    """Generate HTML for a single opportunity card with click handling"""

    def render_card_clickable(row, index):
        emoji, color, priority = badge_for_score(row['final_score'])

        is_selected = selected_opportunity_id.value == row['id']
        border_color = COLORS['primary'] if is_selected else COLORS['light']
        border_width = "3px" if is_selected else "2px"

        card = mo.Html(f"""
        <div style="
            border: {border_width} solid {border_color};
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            cursor: pointer;
            transition: all 0.2s;
            background: white;
        "
        onclick="document.getElementById('opp-{row['id']}').click()">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <h3 style="margin: 0 0 0.5rem 0; color: {COLORS['text']};">
                    #{index + 1}: {row['title'][:80]}...
                </h3>
                <div style="background: {color}; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.85rem;">
                    {emoji} {priority}
                </div>
            </div>
            <div style="display: flex; gap: 1rem; color: {COLORS['secondary']}; font-size: 0.9rem;">
                <span>📊 Score: <strong>{row['final_score']:.0f}</strong></span>
                <span>🏢 {row['sector']}</span>
                <span>📱 r/{row['subreddit']}</span>
            </div>
        </div>
        """)

        # Hidden button for marimo to track clicks
        button = mo.ui.button(
            value=row['id'],
            on_click=lambda v: selected_opportunity_id.set_value(v),
            label="",
            kind="neutral"
        )
        button._id = f"opp-{row['id']}"

        return mo.vstack([card, button])

    return render_card_clickable,
```

### Step 2: Update card display to use clickable cards

Modify `display_confirmed_opportunities` to use new clickable cards:

```python
@app.cell
def display_confirmed_opportunities_clickable(mo, filtered_df, render_card_clickable):
    """Show confirmed opportunities with click handling"""

    if len(filtered_df) == 0:
        display = mo.md("""
        ### ✅ Confirmed Opportunities

        📭 No opportunities match your filters.
        """)
    else:
        cards = [mo.md("### ✅ Confirmed Opportunities")]

        for idx, row in filtered_df.iterrows():
            cards.append(render_card_clickable(row, idx))

        display = mo.vstack(cards)

    return display,
```

### Step 3: Add table row selection handler

Modify `create_table_view` to handle row selection:

```python
@app.cell
def create_table_view_with_selection(mo, filtered_df, badge_for_score, view_mode, selected_opportunity_id, pd):
    """Display opportunities in table format with selection handling"""

    if view_mode.value != "By Sector" or len(filtered_df) == 0:
        table_display = mo.md("")
    else:
        # Build table (same as before)
        table_data = []

        for idx, row in filtered_df.iterrows():
            emoji, color, priority = badge_for_score(row['final_score'])

            concept_brief = row['app_concept'][:60] + "..." if pd.notna(row['app_concept']) and len(str(row['app_concept'])) > 60 else row['app_concept']
            functions_text = str(row['core_functions']) if pd.notna(row['core_functions']) else ""
            function_count = functions_text.count('\n') + 1 if functions_text else 0

            table_data.append({
                '_id': row['id'],  # Hidden ID column
                'Rank': f"#{idx + 1}",
                'Title': row['title'][:50] + "..." if len(row['title']) > 50 else row['title'],
                'Score': f"{emoji} {row['final_score']:.0f}",
                'App Concept': concept_brief,
                'Functions': function_count,
                'Priority': priority
            })

        table_df = pd.DataFrame(table_data)

        table_widget = mo.ui.table(
            table_df,
            selection="single",
            label="**Sector Opportunities Comparison**"
        )

        # Update selected opportunity when table row is clicked
        if table_widget.value and len(table_widget.value) > 0:
            selected_row_idx = table_widget.value[0]
            selected_opportunity_id.set_value(table_data[selected_row_idx]['_id'])

        table_display = table_widget

    return table_display,
```

### Step 4: Test selection interaction

Run: `marimo edit marimo_notebooks/main_dashboard.py`
Expected: Click opportunity card → AI panel updates
Expected: In table view, click row → AI panel updates

### Step 5: Commit selection mechanism

```bash
git add marimo_notebooks/main_dashboard.py
git commit -m "feat: connect selection to AI insights panel

- Add click handling to opportunity cards
- Highlight selected card with primary color border
- Handle table row selection
- Update AI panel reactively when opportunity selected"
```

---

## Task 9: AI Processing Controls

**Files:**
- Modify: `marimo_notebooks/main_dashboard.py`

### Step 1: Add processing status display

Add cell:

```python
@app.cell
def processing_status(mo, confirmed_df, candidates_df, datetime):
    """Display AI processing status"""

    confirmed_count = len(confirmed_df)
    total_submissions = 6127  # From database
    awaiting = total_submissions - confirmed_count

    # Mock last run time (would come from database in production)
    last_run = "2 hours ago"

    status = mo.md(f"""
    ## 🤖 AI Processing Controls

    ### 📊 Processing Status

    - **{confirmed_count}** opportunities analyzed (AI insights complete)
    - **{awaiting:,}** submissions awaiting analysis
    - **Last run:** {last_run}
    """)

    return status,
```

### Step 2: Create AI trigger function

Add cell:

```python
@app.cell
def ai_processing_trigger(subprocess):
    """Function to trigger AI analysis via subprocess"""

    def trigger_analysis(count: int):
        """Run AI analysis script for top N submissions"""
        try:
            result = subprocess.run(
                [
                    "python",
                    "scripts/generate_opportunity_insights_openrouter.py",
                    "--limit",
                    str(count)
                ],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            if result.returncode == 0:
                return f"✅ Analysis complete! Processed {count} submissions."
            else:
                return f"❌ Analysis failed: {result.stderr}"

        except subprocess.TimeoutExpired:
            return f"⏱️ Analysis timed out after 10 minutes"
        except Exception as e:
            return f"❌ Error: {e}"

    return trigger_analysis,
```

### Step 3: Add processing buttons

Add cell:

```python
@app.cell
def processing_buttons(mo, trigger_analysis):
    """Create buttons for AI processing actions"""

    # Top 50 button
    btn_top_50 = mo.ui.button(
        label="Analyze Top 50 by Score (~5 min, $0.005)",
        on_click=lambda: trigger_analysis(50),
        kind="success"
    )

    # All high priority button
    btn_all_high = mo.ui.button(
        label="Analyze All High Priority (~1 hr, $0.61)",
        on_click=lambda: trigger_analysis(1000),
        kind="warn"
    )

    # Custom count input
    custom_count = mo.ui.number(
        value=100,
        start=1,
        stop=1000,
        step=10,
        label="Custom count:"
    )

    btn_custom = mo.ui.button(
        label="Analyze Custom Count",
        on_click=lambda: trigger_analysis(custom_count.value),
        kind="neutral"
    )

    buttons = mo.vstack([
        mo.md("### ⚡ Quick Actions"),
        btn_top_50,
        btn_all_high,
        mo.hstack([custom_count, btn_custom])
    ])

    return buttons, btn_top_50, btn_all_high, btn_custom, custom_count
```

### Step 4: Display processing result

Add cell:

```python
@app.cell
def processing_result_display(mo, btn_top_50, btn_all_high, btn_custom, COLORS):
    """Show result of AI processing"""

    # Check which button was clicked
    if btn_top_50.value:
        result = btn_top_50.value
    elif btn_all_high.value:
        result = btn_all_high.value
    elif btn_custom.value:
        result = btn_custom.value
    else:
        result = None

    if result:
        if "✅" in result:
            result_display = mo.callout(result, kind="success")
        else:
            result_display = mo.callout(result, kind="danger")
    else:
        result_display = mo.md(f"""
        💡 **Tip:** Start with top 50 to discover new opportunities quickly.
        Costs are estimates based on Claude Haiku 4.5.
        """)

    return result_display,
```

### Step 5: Test processing controls

Run: `marimo edit marimo_notebooks/main_dashboard.py`
Expected: See processing status and buttons
Action: Click "Analyze Top 50" → See "🔄 Processing..." then result

Note: Script may fail if OPENROUTER_API_KEY not set - this is expected

### Step 6: Commit processing controls

```bash
git add marimo_notebooks/main_dashboard.py
git commit -m "feat: add AI processing controls

- Display processing status (analyzed vs awaiting)
- Create trigger function for AI script
- Add action buttons (Top 50, All, Custom)
- Show processing results with callouts
- Handle errors and timeouts gracefully"
```

---

## Task 10: Final Assembly & Testing

**Files:**
- Modify: `marimo_notebooks/main_dashboard.py`

### Step 1: Organize all cells into final layout

Add final assembly cell:

```python
@app.cell
def final_dashboard_layout(
    mo,
    header,
    connection_status,
    summary,
    filters,
    sector_stats_display,
    layout,
    display_candidates_section,
    processing_status,
    buttons,
    processing_result_display
):
    """Assemble complete dashboard layout"""

    complete_dashboard = mo.vstack([
        header,
        connection_status,
        summary,
        mo.md("---"),
        filters,
        sector_stats_display,
        mo.md("---"),
        layout,  # Main content + AI panel
        display_candidates_section,
        mo.md("---"),
        processing_status,
        buttons,
        processing_result_display
    ], gap=1)

    complete_dashboard
```

### Step 2: Test complete workflow

Run: `marimo edit marimo_notebooks/main_dashboard.py`

Test checklist:
- [ ] Dashboard loads without errors
- [ ] Database connection shows "✅ Connected"
- [ ] Data summary shows correct counts
- [ ] Filter controls are visible
- [ ] Changing filters updates opportunity list
- [ ] Clicking opportunity card updates AI panel
- [ ] "By Sector" mode shows table view
- [ ] Sector dropdown works
- [ ] Sector stats display correctly
- [ ] Candidates section shows up
- [ ] Processing controls are visible
- [ ] Layout looks clean (70/30 split)

### Step 3: Add error handling improvements

Add cell for comprehensive error handling:

```python
@app.cell
def error_boundary(mo, confirmed_df, candidates_df, COLORS):
    """Display helpful error states"""

    errors = []

    # Check database connection
    if len(confirmed_df) == 0 and len(candidates_df) == 0:
        errors.append(mo.callout("""
        ⚠️ **No Data Found**

        The opportunity_analysis table appears to be empty.

        **Next steps:**
        1. Check Supabase is running: `supabase status`
        2. Verify data was collected: Check Supabase Studio
        3. Run batch scoring: `python scripts/batch_opportunity_scoring.py`
        """, kind="warn"))

    # Check AI insights availability
    if len(confirmed_df) == 0:
        errors.append(mo.callout("""
        💡 **No AI Insights Yet**

        No opportunities have been analyzed by AI.

        **Action:** Use the processing controls below to analyze submissions.
        """, kind="info"))

    if errors:
        error_display = mo.vstack(errors)
    else:
        error_display = mo.md("")

    return error_display,
```

### Step 4: Fix any marimo reactivity issues

Common issues to check:
1. All cells that reference other cells list dependencies correctly
2. `mo.ui` elements are returned from their cells
3. `.value` is used to access UI element values
4. No circular dependencies between cells

### Step 5: Commit final assembly

```bash
git add marimo_notebooks/main_dashboard.py
git commit -m "feat: complete dashboard assembly and error handling

- Assemble all components into final layout
- Add comprehensive error boundary
- Improve empty state handling
- Verify reactive dependencies
- Ready for production use"
```

---

## Task 11: Cleanup Legacy Dashboards

**Files:**
- Delete: 9 old dashboard files

### Step 1: Verify new dashboard works

Run: `marimo run marimo_notebooks/main_dashboard.py --port 8895`
Expected: Dashboard runs without errors, accessible at http://localhost:8895

### Step 2: Delete old dashboard files

```bash
# Delete all legacy dashboards
rm marimo_notebooks/db_dashboard.py
rm marimo_notebooks/top_contenders_dashboard.py
rm marimo_notebooks/live_dashboard.py
rm marimo_notebooks/simple_opportunity_dashboard.py
rm marimo_notebooks/opportunity_insights_dashboard.py
rm marimo_notebooks/opportunity_dashboard_reactive.py
rm marimo_notebooks/redditharbor_marimo_dashboard.py
rm marimo_notebooks/opportunity_analysis_dashboard.py
rm simple_redditharbor_dashboard.py
```

### Step 3: Verify cleanup

Run: `ls marimo_notebooks/*.py`
Expected: Should show only:
- `__init__.py`
- `config.py`
- `main_dashboard.py`
- `redditharbor_demo.py` (keep for demos)

### Step 4: Update memory file

Update `redditharbor_marimo_integration_complete` memory:

```markdown
## Dashboard Consolidation Complete ✅

- **Old dashboards (9):** Deleted
- **New unified dashboard:** marimo_notebooks/main_dashboard.py
- **Run command:** `marimo run marimo_notebooks/main_dashboard.py --port 8895`

### Features
- Two-tier display (confirmed + candidates)
- Dedicated AI insights panel
- Sector comparison table view
- Priority tier filtering
- AI processing triggers
```

### Step 5: Commit cleanup

```bash
git add -A
git commit -m "refactor: consolidate 9 dashboards into unified main dashboard

Delete legacy dashboards:
- db_dashboard.py
- top_contenders_dashboard.py
- live_dashboard.py
- simple_opportunity_dashboard.py
- opportunity_insights_dashboard.py
- opportunity_dashboard_reactive.py
- redditharbor_marimo_dashboard.py
- opportunity_analysis_dashboard.py
- simple_redditharbor_dashboard.py (root)

Single source of truth: marimo_notebooks/main_dashboard.py

BREAKING CHANGE: Old dashboard files no longer available"
```

---

## Task 12: Documentation Updates

**Files:**
- Create: `docs/guides/marimo-main-dashboard.md`
- Modify: `README.md`

### Step 1: Create dashboard user guide

Create `docs/guides/marimo-main-dashboard.md`:

```markdown
# RedditHarbor Main Dashboard Guide

## Overview

The unified marimo dashboard for discovering AI-powered app development opportunities from Reddit data.

## Running the Dashboard

```bash
# Start dashboard
marimo run marimo_notebooks/main_dashboard.py --port 8895

# Access at http://localhost:8895
```

## Features

### Two-Tier Display

**✅ Confirmed Opportunities**
- 20 opportunities with full AI analysis
- App concept, core functions, growth justification
- Ready for evaluation

**🔍 High-Scoring Candidates**
- Submissions scoring ≥70 without AI analysis yet
- Can trigger AI analysis on demand

### View Modes

**All Mode (Default)**
- Card-based list of all opportunities
- Sorted by score (highest first)
- Filter by priority tier

**By Sector Mode**
- Table view for side-by-side comparison
- Select sector from dropdown
- Shows sector statistics

### AI Insights Panel

- Displays when opportunity is selected
- Shows full AI analysis
- Fixed position (no scrolling)

### Processing Controls

- Analyze Top 50 (~5 min, $0.005)
- Analyze All High Priority (~1 hr, $0.61)
- Custom count option

## Usage Tips

1. Start with "All" mode to see best opportunities globally
2. Use priority filters to focus on High (85+) opportunities
3. Switch to "By Sector" to compare similar opportunities
4. Click opportunity to view full AI insights
5. Use processing controls to analyze more submissions

## Troubleshooting

**No data showing:**
- Check Supabase: `supabase status`
- Verify data exists in Supabase Studio
- Run batch scoring: `python scripts/batch_opportunity_scoring.py`

**Database connection failed:**
- Ensure Supabase is running on port 54322
- Check credentials in config

**Processing fails:**
- Verify OPENROUTER_API_KEY is set
- Check script exists: `scripts/generate_opportunity_insights_openrouter.py`
```

### Step 2: Update main README

Add to `README.md` under "Usage" section:

```markdown
### Dashboard

View and analyze opportunities in the unified dashboard:

```bash
marimo run marimo_notebooks/main_dashboard.py --port 8895
```

Access at http://localhost:8895

Features:
- View AI-analyzed opportunities across 6 sectors
- Compare similar opportunities side-by-side
- Trigger AI analysis for high-scoring candidates
- Filter by priority tier and sector

See [Dashboard Guide](docs/guides/marimo-main-dashboard.md) for details.
```

### Step 3: Commit documentation

```bash
git add docs/guides/marimo-main-dashboard.md README.md
git commit -m "docs: add main dashboard user guide

- Create comprehensive dashboard guide
- Document features and usage
- Add troubleshooting section
- Update README with dashboard info"
```

---

## Task 13: Final Testing & Verification

**Files:**
- None (testing only)

### Step 1: Full workflow test

1. Start fresh: `marimo run marimo_notebooks/main_dashboard.py --port 8895`
2. Verify all sections load
3. Test filter interactions
4. Test selection → AI panel updates
5. Test sector mode
6. Verify processing controls display

### Step 2: Performance check

- Dashboard loads in < 2 seconds ✓
- Filter updates feel instant ✓
- No console errors ✓
- Layout is responsive ✓

### Step 3: Error state testing

Test these scenarios:
- Supabase not running → Shows connection error
- No opportunities → Shows empty state
- No candidates → Candidates section hidden
- Invalid filter selection → Handles gracefully

### Step 4: Create verification checklist

```bash
# Run this to verify everything works
echo "Verification Checklist:"
echo "[ ] Dashboard starts without errors"
echo "[ ] Database connects successfully"
echo "[ ] 20 opportunities display"
echo "[ ] Filters update data"
echo "[ ] Selection updates AI panel"
echo "[ ] Sector mode shows table"
echo "[ ] Processing controls work"
echo "[ ] Layout looks clean"
echo "[ ] No console errors"
echo "[ ] All legacy dashboards deleted"
```

### Step 5: Final commit

```bash
git add -A
git commit -m "test: verify complete dashboard functionality

All features tested and working:
- Data loading and display
- Reactive filtering
- Selection and AI panel updates
- Sector comparison view
- Processing controls
- Error handling

Dashboard ready for production use."
```

---

## Task 14: Merge to Develop

**Files:**
- None (git operations only)

### Step 1: Ensure all changes committed

```bash
git status
# Expected: nothing to commit, working tree clean
```

### Step 2: Push feature branch

```bash
git push origin feature/marimo-dashboard-enhancement
```

### Step 3: Use /finish command to merge

Run the `/finish` slash command to complete Git Flow workflow:

```bash
/finish
```

This will:
- Merge feature branch to develop
- Delete feature branch (optional)
- Push changes to remote

### Step 4: Verify merge

```bash
git checkout develop
git pull origin develop
git log --oneline -5
# Should see all commits from feature branch
```

### Step 5: Test on develop branch

```bash
# Verify dashboard works on develop
marimo run marimo_notebooks/main_dashboard.py --port 8895
# Expected: Dashboard runs successfully
```

---

## Success Criteria Checklist

### Functional Requirements
- [x] Single unified dashboard at `/marimo_notebooks/main_dashboard.py`
- [x] Shows confirmed opportunities with AI insights
- [x] Shows high-scoring candidates awaiting analysis
- [x] Dedicated AI insights panel updates reactively
- [x] Priority tier filtering works correctly
- [x] Sector comparison view displays table format
- [x] AI processing triggers work via subprocess
- [x] All 9 legacy dashboards deleted

### Performance Requirements
- [x] Page loads in < 2 seconds with 20 opportunities
- [x] Filter updates feel instant (< 100ms)
- [x] AI panel updates without lag
- [x] Handles up to 100 opportunities without slowdown

### User Experience Requirements
- [x] Clear visual hierarchy (confirmed vs candidates)
- [x] Intuitive navigation between view modes
- [x] AI insights easily readable and comparable
- [x] Processing status clearly communicated
- [x] Error states provide actionable guidance

---

## Plan Complete!

**Estimated total time:** 8-12 hours
**Tasks:** 14 major tasks, 70+ individual steps
**Commits:** ~15 atomic commits
**Risk level:** Low (using existing dependencies, clear requirements)

**Files created:**
- `marimo_notebooks/main_dashboard.py` (~600-700 lines)
- `docs/guides/marimo-main-dashboard.md`

**Files deleted:**
- 9 legacy dashboard files

**Next:** Use `/superpowers:executing-plans` or `/superpowers:subagent-driven-development` to implement this plan.
