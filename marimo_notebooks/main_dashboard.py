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
    import subprocess

    import marimo as mo
    import pandas as pd
    from sqlalchemy import create_engine, text
    return create_engine, mo, pd, text, subprocess


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
    return (COLORS,)


@app.cell
def database_config():
    """Database connection configuration"""

    DB_CONFIG = {
        'host': '127.0.0.1',
        'port': 54322,
        'database': 'postgres',
        'user': 'postgres',
        'password': 'postgres'
    }
    return (DB_CONFIG,)


@app.cell
def database_connection(DB_CONFIG, create_engine, mo, text):
    """Create database connection with error handling"""

    def get_db_engine():
        """Create SQLAlchemy engine for database"""
        try:
            conn_str = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
            engine = create_engine(conn_str)
            return engine
        except Exception as e:
            raise ConnectionError(f"Failed to connect to database: {e}")

    # Test connection
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        connection_status = mo.md("✅ **Database:** Connected")
    except Exception as e:
        connection_status = mo.md(f"⚠️ **Database:** Connection failed - {e}")
    return connection_status, get_db_engine


@app.cell
def display_connection_status(connection_status):
    """Display database connection status"""
    connection_status
    return


@app.cell
def dashboard_header(COLORS, mo):
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
    return (header,)


@app.cell
def display_header(header):
    """Display dashboard header"""
    header
    return


@app.cell
def load_confirmed_opportunities(get_db_engine, pd):
    """Query opportunities with AI insights"""

    def fetch_confirmed():
        query = """
            SELECT
                id, title, sector, final_score,
                app_concept, core_functions, growth_justification,
                simplicity_score, subreddit
            FROM opportunity_analysis
            WHERE app_concept IS NOT NULL
            ORDER BY final_score DESC
        """

        try:
            engine = get_db_engine()
            df = pd.read_sql(query, engine)
            return df
        except Exception as e:
            print(f"Error loading confirmed opportunities: {e}")
            return pd.DataFrame()

    confirmed_df = fetch_confirmed()
    return (confirmed_df,)


@app.cell
def load_candidates(get_db_engine, pd):
    """Query high-scoring submissions without AI analysis"""

    def fetch_candidates():
        query = """
            SELECT
                id, title, sector, final_score,
                subreddit
            FROM opportunity_analysis
            WHERE app_concept IS NULL
            AND final_score >= 70
            ORDER BY final_score DESC
            LIMIT 50
        """

        try:
            engine = get_db_engine()
            df = pd.read_sql(query, engine)
            return df
        except Exception as e:
            print(f"Error loading candidates: {e}")
            return pd.DataFrame()

    candidates_df = fetch_candidates()
    return (candidates_df,)


@app.cell
def data_summary(candidates_df, confirmed_df, mo):
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
    return (summary,)


@app.cell
def display_summary(summary):
    """Display data summary"""
    summary
    return


@app.cell
def view_mode_control(mo):
    """Toggle between All and By Sector views"""

    view_mode = mo.ui.radio(
        options=["All", "By Sector"],
        value="All",
        label="**View Mode:**"
    )
    return (view_mode,)


@app.cell
def priority_filter_control(mo):
    """Filter by priority tiers"""

    priority_options = {
        "high": "🔥 High Priority (85+)",
        "med-high": "⚡ Med-High Priority (70-84)",
        "medium": "📊 Medium Priority (55-69)"
    }

    priority_filter = mo.ui.multiselect(
        options=priority_options,
        value=list(priority_options.keys()),  # All selected by default
        label="**Priority Tiers:**"
    )
    return (priority_filter,)


@app.cell
def sector_dropdown_control(confirmed_df, mo):
    """Sector selection dropdown"""

    # Get unique sectors from data
    sectors = ["All"] + sorted(confirmed_df['sector'].unique().tolist()) if len(confirmed_df) > 0 else ["All"]

    sector_dropdown = mo.ui.dropdown(
        options=sectors,
        value="All",
        label="**Sector:**"
    )
    return (sector_dropdown,)


@app.cell
def filter_panel(mo, priority_filter, sector_dropdown, view_mode):
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
    return (filters,)


@app.cell
def display_filters(filters):
    """Display filter controls"""
    filters
    return


@app.cell
def opportunity_selection_state(mo):
    """Track which opportunity is currently selected"""

    selected_opportunity_id = mo.ui.number(
        value=None,
        label="Selected Opportunity ID (internal)"
    )

    return (selected_opportunity_id,)


@app.cell
def apply_filters_to_data(
    confirmed_df,
    pd,
    priority_filter,
    sector_dropdown,
    view_mode,
):
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
        mask = pd.Series(False, index=filtered_df.index)
        for tier in priority_selected:
            if tier in priority_ranges:
                low, high = priority_ranges[tier]
                mask |= (filtered_df['final_score'] >= low) & (filtered_df['final_score'] <= high)

        filtered_df = filtered_df[mask]

    # Apply sector filter (only in "By Sector" mode)
    if view_mode.value == "By Sector" and sector_dropdown.value != "All":
        filtered_df = filtered_df[filtered_df['sector'] == sector_dropdown.value]
    return (filtered_df,)


@app.cell
def calculate_sector_stats(
    candidates_df,
    filtered_df,
    sector_dropdown,
    view_mode,
):
    """Calculate statistics for sector view"""

    if view_mode.value == "By Sector" and sector_dropdown.value != "All":
        _sector_name = sector_dropdown.value

        # Stats for confirmed opportunities
        _confirmed_count = len(filtered_df)
        _avg_score = filtered_df['final_score'].mean() if _confirmed_count > 0 else 0
        _score_range = (
            filtered_df['final_score'].min(),
            filtered_df['final_score'].max()
        ) if _confirmed_count > 0 else (0, 0)

        # Count candidates in this sector
        _sector_candidates = len(candidates_df[candidates_df['sector'] == _sector_name]) if len(candidates_df) > 0 else 0

        stats = {
            'sector': _sector_name,
            'confirmed_count': _confirmed_count,
            'candidates_count': _sector_candidates,
            'avg_score': _avg_score,
            'score_range': _score_range
        }
    else:
        stats = None
    return (stats,)


@app.cell
def sector_stats_display(mo, stats):
    """Show sector overview stats in By Sector mode"""

    if stats:
        stats_display = mo.md(f"""
        ### 📊 {stats['sector']} Overview

        - **{stats['confirmed_count']}** Confirmed Opportunities
        - **{stats['candidates_count']}** High-Scoring Candidates
        - **Average Score:** {stats['avg_score']:.1f}
        - **Score Range:** {stats['score_range'][0]:.0f} - {stats['score_range'][1]:.0f}
        """)
    else:
        stats_display = mo.md("")
    return (stats_display,)


@app.cell
def ai_insights_panel(mo, selected_opportunity_id, confirmed_df, COLORS):
    """Display AI insights for selected opportunity"""

    # Find selected opportunity in dataframe
    if selected_opportunity_id.value and len(confirmed_df) > 0:
        _opp = confirmed_df[confirmed_df['id'] == selected_opportunity_id.value]

        if len(_opp) > 0:
            _row = _opp.iloc[0]

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

                <h3 style="color: {COLORS['text']};\">{_row['title']}</h3>

                <div style="margin-bottom: 1rem; color: {COLORS['secondary']};\">
                    <strong>Score:</strong> {_row['final_score']:.0f} |
                    <strong>Sector:</strong> {_row['sector']}
                </div>

                <h4 style="color: {COLORS['secondary']};\">📱 App Concept</h4>
                <p style="line-height: 1.6;\">{_row['app_concept']}</p>

                <h4 style="color: {COLORS['secondary']};\">⚙️ Core Functions</h4>
                <pre style="background: {COLORS['light']}; padding: 1rem; border-radius: 4px; white-space: pre-wrap;\">{_row['core_functions']}</pre>

                <h4 style="color: {COLORS['secondary']};\">📈 Growth Justification</h4>
                <p style="line-height: 1.6;\">{_row['growth_justification']}</p>

                <div style="
                    background: {COLORS['accent']};
                    color: {COLORS['text']};
                    padding: 0.75rem;
                    border-radius: 4px;
                    margin-top: 1rem;
                    font-weight: 600;
                \">
                    🎯 Simplicity Score: {_row['simplicity_score']:.0f}/100
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
        \">
            <h2>💡 AI Insights</h2>
            <p style="color: {COLORS['secondary']};\">
                Select an opportunity from the list<br/>
                to view detailed AI analysis.
            </p>
        </div>
        """)

    return (panel,)


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
    return (badge_for_score,)


@app.cell
def create_opportunity_card(COLORS, badge_for_score, selected_opportunity_id):
    """Generate HTML for a single opportunity card with selection handling"""

    def render_card(row, index):
        emoji, color, priority = badge_for_score(row['final_score'])

        # Check if this card is selected
        _is_selected = selected_opportunity_id.value == row['id']
        _border_color = COLORS['primary'] if _is_selected else COLORS['light']
        _border_width = "3px" if _is_selected else "2px"
        _bg_color = "#f9f9f9" if _is_selected else "white"

        card_html = f"""
        <div class="opportunity-card" data-id="{row['id']}" style="
            border: {_border_width} solid {_border_color};
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            cursor: pointer;
            transition: all 0.2s;
            background: {_bg_color};
        ">
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
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const card = document.querySelector('[data-id="{row['id']}"]');
            if (card) {{
                card.addEventListener('click', function(e) {{
                    // Find the number input for selected_opportunity_id and update it
                    const numberInput = document.querySelector('input[type="number"]');
                    if (numberInput) {{
                        numberInput.value = {row['id']};
                        numberInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                }});
            }}
        }});
        </script>
        """

        return card_html
    return (render_card,)


@app.cell
def display_confirmed_opportunities(filtered_df, render_card, mo):
    """Show confirmed opportunities in card view with selection tracking"""

    if len(filtered_df) == 0:
        confirmed_display = mo.md("""
        ### ✅ Confirmed Opportunities

        📭 No opportunities match your filters.
        Try adjusting the priority tier or sector selection.
        """)
    else:
        cards_html = "### ✅ Confirmed Opportunities\n\n"

        for _idx, _row in filtered_df.iterrows():
            cards_html += render_card(_row, _idx)

        confirmed_display = mo.Html(cards_html)
    return (confirmed_display,)


@app.cell
def display_candidates_section(COLORS, candidates_df, mo):
    """Show high-scoring candidates awaiting AI analysis"""

    if len(candidates_df) == 0:
        candidates_display = mo.md("")
    else:
        candidates_html = f"""
        <div style="margin-top: 2rem;">
            <h3>🔍 High-Scoring Candidates</h3>
            <p style="color: {COLORS['secondary']};">
                These submissions scored ≥70 but haven't been analyzed by AI yet.
            </p>
        """

        for _idx, _row in candidates_df.head(10).iterrows():
            candidates_html += f"""
            <div style="
                border: 1px dashed {COLORS['light']};
                border-radius: 6px;
                padding: 0.75rem;
                margin-bottom: 0.5rem;
                background: {COLORS['light']};
            ">
                <div style="font-weight: 600; margin-bottom: 0.25rem;">
                    {_row['title'][:80]}...
                </div>
                <div style="font-size: 0.85rem; color: {COLORS['secondary']};">
                    Score: {_row['final_score']:.0f} | {_row['sector']} | r/{_row['subreddit']}
                </div>
            </div>
            """

        candidates_html += "</div>"
        candidates_display = mo.Html(candidates_html)
    return (candidates_display,)


@app.cell
def create_table_view(badge_for_score, filtered_df, mo, pd, view_mode, selected_opportunity_id):
    """Display opportunities in table format for sector comparison"""

    if view_mode.value != "By Sector" or len(filtered_df) == 0:
        table_display = mo.md("")
    else:
        # Prepare table data
        table_data = []
        _row_to_id = {}  # Mapping of row index to opportunity ID

        for _idx, _row in filtered_df.iterrows():
            emoji, color, priority = badge_for_score(_row['final_score'])

            # Truncate app concept for table display
            concept_brief = _row['app_concept'][:60] + "..." if pd.notna(_row['app_concept']) and len(str(_row['app_concept'])) > 60 else _row['app_concept']

            # Extract function count from core_functions
            functions_text = str(_row['core_functions']) if pd.notna(_row['core_functions']) else ""
            function_count = functions_text.count('\n') + 1 if functions_text else 0

            table_data.append({
                'Rank': f"#{_idx + 1}",
                'Title': _row['title'][:50] + "..." if len(_row['title']) > 50 else _row['title'],
                'Score': f"{emoji} {_row['final_score']:.0f}",
                'App Concept': concept_brief,
                'Functions': function_count,
                'Priority': priority
            })
            # Store mapping of data index to opportunity ID
            _row_to_id[len(table_data) - 1] = _row['id']

        # Convert to DataFrame for marimo table
        table_df = pd.DataFrame(table_data)

        table_widget = mo.ui.table(
            table_df,
            selection="single",
            label="**Sector Opportunities Comparison**"
        )

        # Update selected opportunity when table row is selected
        if table_widget.value is not None and len(table_widget.value) > 0:
            _selected_row_idx = table_widget.value[0]
            if _selected_row_idx in _row_to_id:
                selected_opportunity_id.set_value(_row_to_id[_selected_row_idx])

        table_display = table_widget

    return (table_display,)


@app.cell
def main_content_display(confirmed_display, table_display, view_mode):
    """Show either card view or table view based on mode"""

    if view_mode.value == "All":
        content = confirmed_display  # Card view
    else:
        content = table_display  # Table view
    return (content,)


@app.cell
def dashboard_layout(mo, content, panel):
    """Combine main content and AI panel in two-column layout"""

    layout = mo.hstack(
        [
            mo.vstack([content], justify="start", gap=1),
            mo.vstack([panel], justify="start", gap=1),
        ],
        widths=[7, 3],
        gap=2,
    )

    return (layout,)


@app.cell
def display_dashboard_layout(layout):
    """Display the complete dashboard layout"""
    layout
    return


@app.cell
def processing_status(mo, confirmed_df, candidates_df):
    """Display AI processing status"""

    _confirmed_count = len(confirmed_df)
    _total_submissions = 6127  # From database
    _awaiting = _total_submissions - _confirmed_count

    # Mock last run time (would come from database in production)
    _last_run = "2 hours ago"

    status = mo.md(f"""
    ## 🤖 AI Processing Controls

    ### 📊 Processing Status

    - **{_confirmed_count}** opportunities analyzed (AI insights complete)
    - **{_awaiting:,}** submissions awaiting analysis
    - **Last run:** {_last_run}
    """)

    return (status,)


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
            return "⏱️ Analysis timed out after 10 minutes"
        except Exception as e:
            return f"❌ Error: {e}"

    return (trigger_analysis,)


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

    return (buttons, btn_top_50, btn_all_high, btn_custom, custom_count)


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
        result_display = mo.md("""
        💡 **Tip:** Start with top 50 to discover new opportunities quickly.
        Costs are estimates based on Claude Haiku 4.5.
        """)

    return (result_display,)


@app.cell
def display_processing_status(processing_status):
    """Display processing status"""
    processing_status
    return


@app.cell
def display_processing_controls(buttons):
    """Display processing buttons"""
    buttons
    return


@app.cell
def display_processing_result(processing_result_display):
    """Display processing result"""
    processing_result_display
    return


if __name__ == "__main__":
    app.run()
