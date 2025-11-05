import marimo

__generated_with = "0.17.6"
app = marimo.App(app_title="RedditHarbor Live Analysis")


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
    status = "✅ Database Connected" if db_connected else "❌ Database Not Connected"

    header = mo.md(f"""
    # 🎯 RedditHarbor - Live Analysis

    **Real-time opportunity analysis from your Supabase database**

    {status}
    """)
    header
    return header, status


@app.cell
def _(mo):
    """Filters"""
    result_limit = mo.ui.slider(
        start=10,
        stop=100,
        value=50,
        step=10,
        label="Number of Results",
        show_value=True
    )

    min_upvotes = mo.ui.slider(
        start=0,
        stop=100,
        value=5,
        step=5,
        label="Minimum Upvotes",
        show_value=True
    )

    mo.md("## 🎛️ Filters")
    filters = mo.hstack([result_limit, min_upvotes], gap="2rem")
    filters

    return result_limit, min_upvotes, filters


@app.cell
def _(db, db_connected, result_limit, pd):
    """Load submissions from database"""
    submissions_df = pd.DataFrame()

    if db_connected:
        query = f"""
        SELECT
            submission_id, title, text as selftext, subreddit,
            score, num_comments, created_at, permalink as url
        FROM submission
        ORDER BY created_at DESC
        LIMIT {result_limit.value}
        """
        submissions_df = db.execute_query(query)

    return submissions_df, query


@app.cell
def _(submissions_df, pd, min_upvotes):
    """Process and analyze submissions"""
    analyzed_df = pd.DataFrame()

    if not submissions_df.empty:
        # Extract scores from JSONB
        def get_score(score_data):
            if pd.isna(score_data):
                return 0
            if isinstance(score_data, dict):
                values = list(score_data.values())
                return int(values[-1]) if values else 0
            return int(score_data)

        def get_comments(comments_data):
            if pd.isna(comments_data):
                return 0
            if isinstance(comments_data, dict):
                values = list(comments_data.values())
                return int(values[-1]) if values else 0
            return int(comments_data)

        analyzed_df = submissions_df.copy()
        analyzed_df['score_int'] = analyzed_df['score'].apply(get_score)
        analyzed_df['comments_int'] = analyzed_df['num_comments'].apply(get_comments)

        # Filter by upvotes
        analyzed_df = analyzed_df[analyzed_df['score_int'] >= min_upvotes.value]

        # Analyze text for signals
        def count_signals(text):
            if pd.isna(text):
                return 0, 0, 0
            text = str(text).lower()

            pain = sum(text.count(w) for w in ['problem', 'issue', 'broken', 'frustrated', 'terrible', 'hate'])
            solution = sum(text.count(w) for w in ['looking for', 'recommend', 'alternative', 'how to', 'help'])
            money = sum(text.count(w) for w in ['pay', 'price', 'subscription', 'premium', 'cost'])

            return pain, solution, money

        # Apply analysis
        signals = analyzed_df.apply(
            lambda row: count_signals(str(row['title']) + ' ' + str(row['selftext'])),
            axis=1
        )

        analyzed_df['pain_score'] = signals.apply(lambda x: x[0])
        analyzed_df['solution_score'] = signals.apply(lambda x: x[1])
        analyzed_df['monetization_score'] = signals.apply(lambda x: x[2])

        # Calculate opportunity score
        analyzed_df['opportunity_score'] = (
            analyzed_df['pain_score'] * 4 +
            analyzed_df['solution_score'] * 3 +
            analyzed_df['monetization_score'] * 5
        )

        # Engagement multiplier
        analyzed_df['engagement'] = 1 + (analyzed_df['score_int'] / 200) + (analyzed_df['comments_int'] / 100)
        analyzed_df['final_score'] = analyzed_df['opportunity_score'] * analyzed_df['engagement']

    return analyzed_df,


@app.cell
def _(mo, analyzed_df, db_connected):
    """Summary stats"""
    summary = mo.md("Loading...")

    if db_connected and not analyzed_df.empty:
        total = len(analyzed_df)
        high_opp = len(analyzed_df[analyzed_df['final_score'] >= 50])

        summary = mo.md(f"""
        ## 📊 Summary

        - **Posts Loaded**: {total}
        - **High Opportunity** (≥50 score): {high_opp}
        - **Source**: Supabase Database
        """)

    summary
    return summary,


@app.cell
def _(mo, analyzed_df, px):
    """Top problems visualization"""
    mo.md("## 🔥 Top Problems by Pain Score")

    viz1 = mo.md("No data")
    table1 = mo.md("")

    if not analyzed_df.empty:
        top_problems = analyzed_df.nlargest(10, 'pain_score')

        if not top_problems.empty:
            top_problems_display = top_problems.copy()
            top_problems_display['title_short'] = top_problems_display['title'].str[:50] + '...'

            problems_chart = px.bar(
                top_problems_display,
                x='pain_score',
                y='title_short',
                orientation='h',
                title="Top 10 Problems",
                labels={'pain_score': 'Pain Signals', 'title_short': 'Post'},
                color='final_score',
                color_continuous_scale='Reds'
            )
            problems_chart.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
            viz1 = problems_chart

            problems_display_df = top_problems[['title', 'subreddit', 'pain_score', 'score_int', 'final_score']].copy()
            problems_display_df.columns = ['Title', 'Subreddit', 'Pain Score', 'Upvotes', 'Opportunity Score']
            table1 = mo.ui.dataframe(problems_display_df, page_size=10)

    viz1
    table1

    return viz1, table1


@app.cell
def _(mo, analyzed_df, px):
    """Monetization opportunities"""
    mo.md("## 💰 Monetization Opportunities")

    viz2 = mo.md("No monetization signals found")
    table2 = mo.md("")

    if not analyzed_df.empty:
        money_opps = analyzed_df[analyzed_df['monetization_score'] > 0].nlargest(10, 'final_score')

        if not money_opps.empty:
            monetization_chart = px.scatter(
                money_opps,
                x='monetization_score',
                y='final_score',
                size='score_int',
                color='subreddit',
                hover_data=['title'],
                title="Monetization Signals vs Opportunity Score"
            )
            monetization_chart.update_layout(height=350)
            viz2 = monetization_chart

            money_display_df = money_opps[['title', 'subreddit', 'monetization_score', 'final_score']].copy()
            money_display_df.columns = ['Title', 'Subreddit', 'Monetization Signals', 'Opportunity Score']
            table2 = mo.ui.dataframe(money_display_df, page_size=10)

    viz2
    table2

    return viz2, table2


@app.cell
def _(mo, analyzed_df, px):
    """Subreddit analysis"""
    mo.md("## 📊 Subreddit Analysis")

    viz3 = mo.md("No data")
    table3 = mo.md("")

    if not analyzed_df.empty:
        subreddit_stats = analyzed_df.groupby('subreddit').agg({
            'final_score': 'mean',
            'pain_score': 'sum',
            'monetization_score': 'sum',
            'title': 'count'
        }).reset_index()

        subreddit_stats.columns = ['Subreddit', 'Avg Score', 'Total Pain', 'Total Money', 'Post Count']
        subreddit_stats = subreddit_stats.sort_values('Avg Score', ascending=False).head(10)

        if not subreddit_stats.empty:
            subreddit_chart = px.bar(
                subreddit_stats,
                x='Avg Score',
                y='Subreddit',
                orientation='h',
                color='Total Money',
                title="Top Subreddits by Opportunity",
                color_continuous_scale='Greens'
            )
            subreddit_chart.update_layout(height=350, yaxis={'categoryorder': 'total ascending'})
            viz3 = subreddit_chart
            table3 = mo.ui.dataframe(subreddit_stats, page_size=10)

    viz3
    table3

    return viz3, table3


@app.cell
def _(mo, db, db_connected):
    """Footer"""
    footer_content = mo.md("Database not connected")

    if db_connected:
        stats = db.execute_query("SELECT COUNT(*) as total, COUNT(DISTINCT subreddit) as subs FROM submission")

        if not stats.empty:
            total_posts = int(stats.iloc[0]['total'])
            total_subs = int(stats.iloc[0]['subs'])

            footer_content = mo.md(f"""
            ---

            ## 📈 Database Stats

            - **Total Posts**: {total_posts:,}
            - **Unique Subreddits**: {total_subs}

            ## 🔄 Next Steps

            1. Adjust filters above to explore different segments
            2. Collect more data: `uv run python scripts/collect_real_reddit_data.py`
            3. Refresh dashboard to see updates
            """)

    footer_content
    return footer_content,


if __name__ == "__main__":
    app.run()
