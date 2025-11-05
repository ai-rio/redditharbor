import marimo

__generated_with = "0.17.6"
app = marimo.App(app_title="RedditHarbor Research Dashboard")


@app.cell
def _():
    """Setup imports and configuration"""
    import sys
    from pathlib import Path
    import marimo as mo

    # Add project root to path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    has_db = False
    config = None
    db_connector = None

    try:
        from marimo_notebooks.config import MarimoConfig
        from marimo_notebooks.utils import DatabaseConnector

        config = MarimoConfig()
        db_connector = DatabaseConnector()
        has_db = True
    except Exception as e:
        pass  # Silently fail, use demo data

    return config, db_connector, has_db, mo, Path, sys


@app.cell
def _(mo):
    """Display header"""
    mo.md("# 📊 RedditHarbor Research Dashboard")
    return


@app.cell
def _(mo):
    """Create interactive UI components"""
    subreddit = mo.ui.dropdown(
        options=["python", "technology", "programming", "startups"],
        value="python",
        label="Select Subreddit",
    )

    data_type = mo.ui.dropdown(
        options=["submissions", "comments", "both"],
        value="submissions",
        label="Data Type",
    )

    date_range = mo.ui.date_range(label="Date Range (Optional)")

    limit = mo.ui.slider(start=10, stop=100, step=10, value=50, label="Result Limit")

    return subreddit, data_type, date_range, limit


@app.cell
def _(mo, subreddit, data_type, limit):
    """Display UI controls"""
    mo.md(f"""
    ## 🎛️ Controls

    {subreddit}

    {data_type}

    {limit}
    """)
    return


@app.cell
def _(subreddit, data_type, limit, config, db_connector, has_db, mo):
    """Load Reddit data from database or use demo data"""
    import pandas as pd
    import numpy as np

    def create_demo_data():
        """Create realistic demo data when database is not available"""
        num_items = limit.value
        timestamps = pd.date_range('2024-01-01', periods=num_items, freq='h')

        if subreddit.value == 'python':
            titles = [
                "Python 3.12 released with new pattern matching",
                "Django 5.0 brings major improvements",
                "Async Python best practices guide",
                "FastAPI vs Flask: Performance comparison",
                "Python type hints for better code quality",
                "Data visualization with Matplotlib and Seaborn",
                "Machine learning with scikit-learn tutorial",
                "Python web scraping with BeautifulSoup",
                "Testing strategies for Python applications",
                "Python packaging and distribution guide"
            ]
        elif subreddit.value == 'technology':
            titles = [
                "AI breakthrough changes everything we know",
                "Quantum computing reaches new milestone",
                "5G deployment accelerates globally",
                "Cybersecurity threats in 2024",
                "Cloud computing trends and predictions",
                "Blockchain beyond cryptocurrency",
                "IoT security vulnerabilities exposed",
                "Tech giants face antitrust challenges",
                "Autonomous vehicles hit the streets",
                "Renewable energy technology advances"
            ]
        elif subreddit.value == 'programming':
            titles = [
                "Clean code principles every developer should know",
                "Git advanced workflows for teams",
                "Microservices architecture patterns",
                "Kubernetes deployment strategies",
                "API design best practices",
                "Database optimization techniques",
                "Frontend frameworks comparison 2024",
                "DevOps culture transformation",
                "Code review checklist template",
                "Programming language selection guide"
            ]
        else:  # startups
            titles = [
                "YC announces new batch of startups",
                "Series B funding rounds this week",
                "Startup failure rates analyzed",
                "Unicorn valuations face reality check",
                "Remote work startup success stories",
                "SaaS metrics that matter most",
                "Founder-market fit evaluation",
                "Bootstrapping vs venture capital",
                "Startup pitch deck templates",
                "Exit strategies for tech startups"
            ]

        demo_data = pd.DataFrame({
            'id': range(1, num_items + 1),
            'title': np.random.choice(titles, num_items, replace=True),
            'score': np.random.randint(10, 1000, num_items),
            'num_comments': np.random.randint(1, 200, num_items),
            'created_utc': timestamps,
            'subreddit': subreddit.value
        })

        return demo_data

    if has_db and db_connector and db_connector.engine:
        try:
            # Check if tables exist first
            table_check = db_connector.execute_query("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public' AND tablename IN ('submission', 'comment')
            """)

            if "error" in table_check.columns or len(table_check) == 0:
                mo.md("📊 **Using demo data** (Database tables not found)")
                reddit_data = create_demo_data()
            else:
                # Build query based on selections
                if data_type.value == "submissions":
                    query = f"""
                    SELECT id, title, score, num_comments, created_utc, subreddit
                    FROM submission
                    WHERE subreddit = '{subreddit.value}'
                    ORDER BY created_utc DESC
                    LIMIT {limit.value}
                    """
                elif data_type.value == "comments":
                    query = f"""
                    SELECT id, body as title, score, created_utc, subreddit
                    FROM comment
                    WHERE subreddit = '{subreddit.value}'
                    ORDER BY created_utc DESC
                    LIMIT {limit.value}
                    """
                else:
                    query = f"""
                    SELECT id, title, score, num_comments, created_utc, subreddit
                    FROM submission
                    WHERE subreddit = '{subreddit.value}'
                    ORDER BY created_utc DESC
                    LIMIT {limit.value}
                    """

                reddit_data = db_connector.execute_query(query)

                if "error" in reddit_data.columns:
                    mo.md("⚠️ Database query failed, using demo data")
                    reddit_data = create_demo_data()
                else:
                    mo.md(f"✅ **Loaded {len(reddit_data)} real items** from r/{subreddit.value}")

        except Exception as e:
            mo.md(f"⚠️ **Error loading data:** {e}")
            reddit_data = create_demo_data()
    else:
        reddit_data = create_demo_data()
        mo.md("📊 **Using demo data** (No database connection)")

    return reddit_data, pd, np


@app.cell
def _(reddit_data, subreddit, mo):
    """Create interactive visualizations"""
    import altair as alt

    if len(reddit_data) == 0:
        display = mo.md("No data available for visualization")
    else:
        # Score distribution chart
        score_chart = (
            alt.Chart(reddit_data)
            .mark_bar()
            .encode(
                x=alt.X("score:Q", bin=True, title="Score Range"),
                y="count()",
                color=alt.value("#FF6B35"),
            )
            .properties(
                title=f"Score Distribution - r/{subreddit.value}",
                width=600,
                height=300,
            )
        )

        # Engagement scatter plot
        engagement_chart = (
            alt.Chart(reddit_data)
            .mark_circle(size=50)
            .encode(
                x=alt.X("score:Q", title="Score"),
                y=alt.Y("num_comments:Q", title="Comments"),
                color=alt.value("#004E89"),
                tooltip=["title", "score", "num_comments"],
            )
            .properties(
                title="Engagement Analysis: Score vs Comments",
                width=600,
                height=300,
            )
        )

        display = mo.vstack([
            mo.md(f"### 📊 Analytics - r/{subreddit.value}"),
            mo.md(f"**{len(reddit_data)} posts analyzed**"),
            score_chart,
            engagement_chart
        ])

    display
    return alt,


@app.cell
def _(reddit_data, mo):
    """Create interactive data table"""
    if len(reddit_data) == 0:
        table_display = mo.md("No data to display")
    else:
        display_data = reddit_data[["title", "score", "num_comments", "created_utc"]].copy()
        display_data["created_utc"] = display_data["created_utc"].dt.strftime(
            "%Y-%m-%d %H:%M"
        )
        display_data.columns = ["Title", "Score", "Comments", "Posted"]

        table_display = mo.vstack([
            mo.md("### 📋 Top Posts"),
            mo.ui.table(display_data.head(20), selection="multi", pagination=True)
        ])

    table_display
    return display_data,


@app.cell
def _(reddit_data, subreddit, mo):
    """Display summary statistics"""
    if len(reddit_data) == 0:
        stats_display = mo.md("No statistics available")
    else:
        avg_score = reddit_data["score"].mean()
        avg_comments = reddit_data["num_comments"].mean()
        total_score = reddit_data["score"].sum()
        total_comments = reddit_data["num_comments"].sum()

        stats_display = mo.md(f"""
        ### 📈 Summary Statistics

        **Community:** r/{subreddit.value}

        **Performance Metrics:**
        - **Average Score:** {avg_score:.1f}
        - **Average Comments:** {avg_comments:.1f}
        - **Total Score:** {total_score:,.0f}
        - **Total Comments:** {total_comments:,.0f}
        - **Posts Analyzed:** {len(reddit_data)}
        """)

    stats_display
    return


if __name__ == "__main__":
    app.run()
