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


@app.cell
def database_config():
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


@app.cell
def view_mode_control(mo):
    """Toggle between All and By Sector views"""

    view_mode = mo.ui.radio(
        options=["All", "By Sector"],
        value="All",
        label="**View Mode:**"
    )

    return view_mode,


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


if __name__ == "__main__":
    app.run()
