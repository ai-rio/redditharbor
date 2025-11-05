import marimo

__generated_with = "0.17.6"
app = marimo.App(app_title="RedditHarbor DB Dashboard")


@app.cell
def _():
    """Setup"""
    import sys
    from pathlib import Path
    import marimo as mo
    import pandas as pd
    import plotly.express as px

    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    from marimo_notebooks.utils import DatabaseConnector

    db = DatabaseConnector()
    db_connected = db.test_connection()

    return mo, pd, px, db, db_connected, project_root


@app.cell
def _(mo, db_connected):
    """Header"""
    status = "✅ Connected" if db_connected else "❌ Not Connected"
    mo.md(f"""
    # RedditHarbor - Database Dashboard

    **Status:** {status}
    """)
    return status,


@app.cell
def _(mo):
    """Filters"""
    limit_slider = mo.ui.slider(10, 100, value=50, label="Results", show_value=True)
    limit_slider
    return limit_slider,


@app.cell
def _(db, db_connected, limit_slider, pd):
    """Load data"""
    if db_connected:
        query = f"SELECT title, subreddit, score, num_comments, selftext FROM submission LIMIT {limit_slider.value}"
        df = db.execute_query(query)
    else:
        df = pd.DataFrame()

    return df, query


@app.cell
def _(mo, df):
    """Show data"""
    mo.md(f"## Data ({len(df)} rows)")

    if not df.empty:
        mo.ui.dataframe(df.head(20))
    else:
        mo.md("No data")
    return


if __name__ == "__main__":
    app.run()
