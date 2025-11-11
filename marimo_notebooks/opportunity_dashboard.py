"""
RedditHarbor Opportunity Dashboard

Interactive dashboard for exploring AI-powered app development opportunities
from Reddit data analysis. Displays opportunities with final scores >= 40.0
and provides filtering and analytics capabilities.
"""

import marimo

__generated_with = "0.17.6"
app = marimo.App(width="full")

# ============================================================================
# CELL 1: IMPORTS AND SETUP
# ============================================================================

@app.cell
def imports():
    import os
    import sys
    from datetime import datetime
    from pathlib import Path

    import marimo as mo
    import pandas as pd
    import psycopg2
    from sqlalchemy import create_engine, text

    # Add project root to path for config imports
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    return create_engine, mo, pd, text, datetime, os, psycopg2

# ============================================================================
# CELL 2: BRAND COLORS AND STYLING
# ============================================================================

@app.cell
def brand_colors():
    """CueTimer brand colors for consistent styling"""
    COLORS = {
        'primary': '#FF6B35',     # Vibrant Orange
        'secondary': '#004E89',   # Deep Blue
        'accent': '#F7B801',      # Golden Yellow
        'text': '#1A1A1A',        # Dark Gray
        'light': '#F5F5F5',       # Light Gray
        'white': '#FFFFFF',
        'success': '#28a745',     # Green
        'danger': '#dc3545',      # Red
        'info': '#17a2b8'         # Cyan
    }

    # CSS for custom styling
    custom_css = f"""
    <style>
    .dashboard-header {{
        background: linear-gradient(135deg, {COLORS['primary']}, {COLORS['secondary']});
        color: {COLORS['white']};
        padding: 2rem;
        border-radius: 8px;
        margin-bottom: 2rem;
    }}
    .stat-card {{
        background: {COLORS['white']};
        border-left: 4px solid {COLORS['primary']};
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }}
    .filter-panel {{
        background: {COLORS['light']};
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 2rem;
    }}
    </style>
    """

    return mo.html(custom_css), COLORS

# ============================================================================
# CELL 3: DATABASE CONFIGURATION
# ============================================================================

@app.cell
def database_config():
    """Database connection configuration from environment"""

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('.env')

    # Database configuration
    DB_CONFIG = {
        'host': '127.0.0.1',
        'port': 54322,
        'database': 'postgres',
        'user': 'postgres',
        'password': 'postgres'
    }

    # Create connection URL
    connection_url = (
        f"postgresql://{DB_CONFIG['user']}:"
        f"{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}:"
        f"{DB_CONFIG['port']}/"
        f"{DB_CONFIG['database']}"
    )

    return connection_url, DB_CONFIG

# ============================================================================
# CELL 4: DATA CONNECTION
# ============================================================================

@app.cell
def data_connection(connection_url, mo):
    """Connect to database and fetch opportunities data"""

    def fetch_opportunities(min_score: float = 40.0) -> pd.DataFrame:
        """Fetch opportunities from database with minimum score filter"""
        try:
            engine = create_engine(connection_url, pool_pre_ping=True)

            query = text("""
                SELECT
                    opportunity_id,
                    app_name,
                    final_score,
                    problem_description,
                    app_concept,
                    function_list,
                    target_user,
                    monetization_model,
                    pain_intensity,
                    monetization_potential,
                    market_gap,
                    technical_feasibility,
                    market_demand,
                    status,
                    processed_at
                FROM workflow_results
                WHERE final_score >= :min_score
                ORDER BY final_score DESC
            """)

            with engine.connect() as conn:
                result_df = pd.read_sql(query, conn, params={'min_score': min_score})

            return result_df

        except Exception as e:
            # Return error DataFrame if connection fails
            error_df = pd.DataFrame({
                'error': [f"Database connection failed: {e!s}"],
                'connection_url': [connection_url]
            })
            return error_df

    # Initial data load with default threshold
    opportunities_df = fetch_opportunities(40.0)

    # Check if we have data
    if 'error' in opportunities_df.columns:
        status_message = mo.md(f"❌ **Database Error:** {opportunities_df['error'].iloc[0]}")
    elif len(opportunities_df) == 0:
        status_message = mo.md("ℹ️ **No opportunities found** with score >= 40.0")
    else:
        status_message = mo.md(f"✅ **Loaded {len(opportunities_df)} opportunities** with final_score >= 40.0")

    return (fetch_opportunities, opportunities_df, status_message)

# ============================================================================
# CELL 5: INTERACTIVE FILTERS AND FILTERED DATA
# ============================================================================

@app.cell
def filters_and_data(fetch_opportunities, mo, pd):
    """Interactive filters and apply them to data"""

    # Minimum score filter
    min_score_slider = mo.ui.slider(
        start=0,
        stop=100,
        value=40,
        step=5,
        label="Minimum Score Threshold",
        show_value=True
    )

    # Status filter
    status_options = ["All", "APPROVED", "DISQUALIFIED"]
    status_filter = mo.ui.select(
        options=status_options,
        value="All",
        label="Status Filter"
    )

    # Score range display
    score_range = mo.ui.range(
        start=0,
        stop=100,
        value=[40, 100],
        step=5,
        label="Score Range",
        show_value=True
    )

    # Fetch and filter data based on minimum score
    filtered_df = fetch_opportunities(float(min_score_slider.value))

    # Apply additional filters
    if len(filtered_df) > 0 and 'error' not in filtered_df.columns:
        # Apply status filter
        if status_filter.value != "All":
            filtered_df = filtered_df[filtered_df['status'] == status_filter.value]

        # Apply score range filter
        range_min = score_range.value[0]
        range_max = score_range.value[1]
        filtered_df = filtered_df[
            (filtered_df['final_score'] >= range_min) &
            (filtered_df['final_score'] <= range_max)
        ]

    return (min_score_slider, status_filter, score_range, filtered_df)

# ============================================================================
# CELL 6: SUMMARY STATISTICS
# ============================================================================

@app.cell
def summary_stats(filtered_df, mo, COLORS):
    """Calculate and display summary statistics"""

    if 'error' in filtered_df.columns:
        stats_html = mo.html(f"""
        <div class="stat-card">
            <h3 style="color: {COLORS['danger']}">Database Connection Error</h3>
            <p>{filtered_df['error'].iloc[0]}</p>
        </div>
        """)
    elif len(filtered_df) == 0:
        stats_html = mo.html(f"""
        <div class="stat-card">
            <h3 style="color: {COLORS['info']}">No Data</h3>
            <p>No opportunities match the current filters.</p>
        </div>
        """)
    else:
        # Calculate statistics
        total_count = len(filtered_df)
        avg_score = filtered_df['final_score'].mean()
        median_score = filtered_df['final_score'].median()
        max_score = filtered_df['final_score'].max()
        score_min = filtered_df['final_score'].min()
        approved_count = len(filtered_df[filtered_df['status'] == 'APPROVED'])
        disqualified_count = len(filtered_df[filtered_df['status'] == 'DISQUALIFIED'])

        # Average scores by dimension
        avg_pain = filtered_df['pain_intensity'].mean() if 'pain_intensity' in filtered_df.columns else 0
        avg_monetization = filtered_df['monetization_potential'].mean() if 'monetization_potential' in filtered_df.columns else 0
        avg_market_gap = filtered_df['market_gap'].mean() if 'market_gap' in filtered_df.columns else 0
        avg_tech_feas = filtered_df['technical_feasibility'].mean() if 'technical_feasibility' in filtered_df.columns else 0

        stats_html = mo.html(f"""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem;">
            <div class="stat-card">
                <h3 style="margin: 0; color: {COLORS['secondary']}">Total Opportunities</h3>
                <p style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0; color: {COLORS['primary']}">{total_count}</p>
                <p style="margin: 0; color: #666;">APPROVED: {approved_count} | DISQUALIFIED: {disqualified_count}</p>
            </div>

            <div class="stat-card">
                <h3 style="margin: 0; color: {COLORS['secondary']}">Average Score</h3>
                <p style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0; color: {COLORS['primary']}">{avg_score:.1f}</p>
                <p style="margin: 0; color: #666;">Range: {score_min:.1f} - {max_score:.1f}</p>
            </div>

            <div class="stat-card">
                <h3 style="margin: 0; color: {COLORS['secondary']}">Median Score</h3>
                <p style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0; color: {COLORS['primary']}">{median_score:.1f}</p>
                <p style="margin: 0; color: #666;">Middle value</p>
            </div>

            <div class="stat-card">
                <h3 style="margin: 0; color: {COLORS['secondary']}">Dimension Averages</h3>
                <p style="margin: 0.5rem 0;">Pain: <strong>{avg_pain:.1f}</strong></p>
                <p style="margin: 0.5rem 0;">Monetization: <strong>{avg_monetization:.1f}</strong></p>
                <p style="margin: 0.5rem 0;">Market Gap: <strong>{avg_market_gap:.1f}</strong></p>
                <p style="margin: 0;">Tech Feasibility: <strong>{avg_tech_feas:.1f}</strong></p>
            </div>
        </div>
        """)

    return (stats_html,)

# ============================================================================
# CELL 7: OPPORTUNITY TABLE
# ============================================================================

@app.cell
def opportunity_table(filtered_df, mo, COLORS):
    """Display opportunities in an interactive table"""

    if 'error' in filtered_df.columns:
        table_output = mo.md(f"❌ **Error:** {filtered_df['error'].iloc[0]}")
    elif len(filtered_df) == 0:
        table_output = mo.md("ℹ️ No opportunities match the current filters.")
    else:
        # Create a display-friendly version of the DataFrame
        display_df = filtered_df.copy()

        # Format function_list for display
        if 'function_list' in display_df.columns:
            display_df['function_list'] = display_df['function_list'].apply(
                lambda x: str(x)[:100] + "..." if isinstance(x, str) and len(str(x)) > 100 else str(x)
            )

        # Truncate long text fields
        if 'problem_description' in display_df.columns:
            display_df['problem_description'] = display_df['problem_description'].apply(
                lambda x: str(x)[:150] + "..." if isinstance(x, str) and len(str(x)) > 150 else str(x)
            )

        if 'app_concept' in display_df.columns:
            display_df['app_concept'] = display_df['app_concept'].apply(
                lambda x: str(x)[:150] + "..." if isinstance(x, str) and len(str(x)) > 150 else str(x)
            )

        # Select columns for display
        columns_to_show = [
            'opportunity_id',
            'app_name',
            'final_score',
            'status',
            'problem_description',
            'app_concept',
            'function_list',
            'target_user',
            'monetization_model'
        ]

        # Filter to only existing columns
        available_columns = [col for col in columns_to_show if col in display_df.columns]
        display_df = display_df[available_columns]

        # Create table with custom styling
        table = mo.ui.table(
            display_df,
            label="Opportunity Explorer",
            selection="multi",
            show_download=True,
            pagination=True,
            page_size=10
        )

        table_output = table

    return (table_output,)

# ============================================================================
# CELL 8: DETAILED OPPORTUNITY VIEW
# ============================================================================

@app.cell
def detailed_view(opportunity_table, filtered_df, mo, COLORS):
    """Show detailed view of selected opportunity"""

    # Get selected row
    selected_rows = opportunity_table.value

    if not selected_rows or len(selected_rows) == 0:
        detail_view = mo.md("👆 **Select an opportunity** from the table above to view details.")
    else:
        # Get the first selected opportunity
        selected_idx = selected_rows[0]
        opportunity = filtered_df.iloc[selected_idx]

        # Create detailed view
        detail_html = f"""
        <div style="background: {COLORS['white']}; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h2 style="color: {COLORS['secondary']}; margin-top: 0;">{opportunity.get('app_name', 'N/A')}</h2>

            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 2rem; margin-bottom: 2rem;">
                <div>
                    <h3 style="color: {COLORS['primary']}; border-bottom: 2px solid {COLORS['primary']}; padding-bottom: 0.5rem;">Basic Info</h3>
                    <p><strong>Opportunity ID:</strong> {opportunity.get('opportunity_id', 'N/A')}</p>
                    <p><strong>Final Score:</strong> <span style="color: {COLORS['primary']}; font-size: 1.5rem; font-weight: bold;">{opportunity.get('final_score', 'N/A')}</span></p>
                    <p><strong>Status:</strong> {opportunity.get('status', 'N/A')}</p>
                    <p><strong>Processed:</strong> {opportunity.get('processed_at', 'N/A')}</p>
                </div>

                <div>
                    <h3 style="color: {COLORS['primary']}; border-bottom: 2px solid {COLORS['primary']}; padding-bottom: 0.5rem;">Scores</h3>
                    <p><strong>Pain Intensity:</strong> {opportunity.get('pain_intensity', 'N/A')}</p>
                    <p><strong>Monetization:</strong> {opportunity.get('monetization_potential', 'N/A')}</p>
                    <p><strong>Market Gap:</strong> {opportunity.get('market_gap', 'N/A')}</p>
                    <p><strong>Technical Feasibility:</strong> {opportunity.get('technical_feasibility', 'N/A')}</p>
                    <p><strong>Market Demand:</strong> {opportunity.get('market_demand', 'N/A')}</p>
                </div>
            </div>

            <div style="margin-bottom: 2rem;">
                <h3 style="color: {COLORS['primary']}; border-bottom: 2px solid {COLORS['primary']}; padding-bottom: 0.5rem;">Problem Description</h3>
                <p style="line-height: 1.6;">{opportunity.get('problem_description', 'N/A')}</p>
            </div>

            <div style="margin-bottom: 2rem;">
                <h3 style="color: {COLORS['primary']}; border-bottom: 2px solid {COLORS['primary']}; padding-bottom: 0.5rem;">App Concept</h3>
                <p style="line-height: 1.6;">{opportunity.get('app_concept', 'N/A')}</p>
            </div>

            <div style="margin-bottom: 2rem;">
                <h3 style="color: {COLORS['primary']}; border-bottom: 2px solid {COLORS['primary']}; padding-bottom: 0.5rem;">Core Functions</h3>
                <p style="line-height: 1.6;">{opportunity.get('function_list', 'N/A')}</p>
            </div>

            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 2rem;">
                <div>
                    <h3 style="color: {COLORS['primary']}; border-bottom: 2px solid {COLORS['primary']}; padding-bottom: 0.5rem;">Target User</h3>
                    <p style="line-height: 1.6;">{opportunity.get('target_user', 'N/A')}</p>
                </div>

                <div>
                    <h3 style="color: {COLORS['primary']}; border-bottom: 2px solid {COLORS['primary']}; padding-bottom: 0.5rem;">Monetization Model</h3>
                    <p style="line-height: 1.6;">{opportunity.get('monetization_model', 'N/A')}</p>
                </div>
            </div>
        </div>
        """

        detail_view = mo.html(detail_html)

    return (detail_view,)

# ============================================================================
# CELL 9: DASHBOARD LAYOUT
# ============================================================================

@app.cell
def dashboard(custom_css, mo, status_message, min_score_slider, status_filter, score_range, summary_stats, opportunity_table, detailed_view):
    """Main dashboard layout"""

    dashboard_layout = mo.vstack([
        mo.html(custom_css),

        # Header
        mo.html("""
        <div class="dashboard-header">
            <h1 style="margin: 0; font-size: 2.5rem;">🎯 RedditHarbor Opportunity Explorer</h1>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem;">Discover AI-powered app development opportunities from Reddit data</p>
        </div>
        """),

        # Status message
        status_message,

        # Filters
        mo.html('<div class="filter-panel">'),
        mo.md("### 🔍 Filters"),
        mo.hstack([
            min_score_slider,
            status_filter,
        ], gap=2),
        score_range,
        mo.html('</div>'),

        # Summary statistics
        mo.md("### 📊 Summary Statistics"),
        summary_stats,

        # Opportunity table
        mo.md("### 💡 Opportunities"),
        opportunity_table,

        # Detailed view
        mo.md("### 📋 Opportunity Details"),
        detailed_view,
    ])

    return (dashboard_layout,)
