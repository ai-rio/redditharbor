import marimo

__generated_with = "0.17.6"
app = marimo.App(app_title="RedditHarbor - Live Database Insights")


@app.cell
def _():
    """Setup and database connection"""
    import sys
    from pathlib import Path
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    from datetime import datetime

    # Add project root to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    # Import database connector
    from marimo_notebooks.utils import DatabaseConnector

    # Initialize database
    db = DatabaseConnector()
    db_status = "✅ Connected to Database" if db.test_connection() else "❌ Database Not Available"

    return mo, pd, px, Path, project_root, db, db_status, datetime


@app.cell
def _(mo, db_status):
    """Header"""
    mo.md(f"""
    # 🎯 RedditHarbor - Live Database Insights

    **Real-time analysis of Reddit discussions from your Supabase database**

    {db_status}
    """)


@app.cell
def _(mo):
    """Interactive filters"""
    # Minimum engagement filter
    min_engagement = mo.ui.slider(
        start=0,
        stop=100,
        value=5,
        step=5,
        label="Minimum Upvotes",
        show_value=True,
    )

    # Subreddit filter (will be populated from database)
    subreddit_filter = mo.ui.dropdown(
        options=["All"],
        value="All",
        label="Filter by Subreddit",
    )

    # Limit results
    result_limit = mo.ui.slider(
        start=10,
        stop=100,
        value=50,
        step=10,
        label="Number of Results",
        show_value=True,
    )

    mo.md("## 🎛️ Filters")
    filter_row = mo.hstack([min_engagement, result_limit, subreddit_filter], gap="2rem")
    filter_row

    return min_engagement, subreddit_filter, result_limit


@app.cell
def _(db, min_engagement, result_limit, subreddit_filter, pd):
    """Fetch and analyze data from database"""

    if not db.test_connection():
        submissions_df = pd.DataFrame()
        all_subreddits = ["All"]
    else:
        # Build query based on filters
        subreddit_condition = ""
        if subreddit_filter.value != "All":
            subreddit_condition = f"AND subreddit = '{subreddit_filter.value}'"

        # Fetch submissions from database
        query = f"""
        SELECT
            id,
            title,
            selftext,
            subreddit,
            score,
            num_comments,
            created_at,
            url
        FROM submission
        WHERE 1=1
        {subreddit_condition}
        ORDER BY created_at DESC
        LIMIT {result_limit.value}
        """

        submissions_df = db.execute_query(query)

        # Get all unique subreddits for filter
        subreddits_query = "SELECT DISTINCT subreddit FROM submission ORDER BY subreddit"
        subreddits_result = db.execute_query(subreddits_query)

        if not subreddits_result.empty and 'subreddit' in subreddits_result.columns:
            all_subreddits = ["All"] + subreddits_result['subreddit'].tolist()
        else:
            all_subreddits = ["All"]

        # Update subreddit filter options
        subreddit_filter.options = all_subreddits

        # Clean and process the data
        if not submissions_df.empty:
            # Handle JSONB score and num_comments fields
            def extract_score(score_data):
                if pd.isna(score_data):
                    return 0
                if isinstance(score_data, dict):
                    # Get the latest value from the dict
                    values = list(score_data.values())
                    return int(values[-1]) if values else 0
                return int(score_data)

            def extract_comments(comments_data):
                if pd.isna(comments_data):
                    return 0
                if isinstance(comments_data, dict):
                    values = list(comments_data.values())
                    return int(values[-1]) if values else 0
                return int(comments_data)

            submissions_df['score_int'] = submissions_df['score'].apply(extract_score)
            submissions_df['comments_int'] = submissions_df['num_comments'].apply(extract_comments)

            # Apply engagement filter
            submissions_df = submissions_df[submissions_df['score_int'] >= min_engagement.value]

            # Analyze for opportunity signals
            def analyze_text(text):
                if pd.isna(text):
                    return {'pain': 0, 'solution': 0, 'monetization': 0}
                text = str(text).lower()

                pain_words = ['frustrated', 'annoying', 'terrible', 'hate', 'worst', 'problem', 'issue', 'broken', "doesn't work"]
                solution_words = ['recommendation', 'looking for', 'need help', 'alternative', 'how to', 'suggest']
                money_words = ['pay', 'subscription', 'premium', 'cost', 'price', 'worth it', 'willing to pay']

                return {
                    'pain': sum(text.count(word) for word in pain_words),
                    'solution': sum(text.count(word) for word in solution_words),
                    'monetization': sum(text.count(word) for word in money_words)
                }

            submissions_df['signals'] = submissions_df.apply(
                lambda row: analyze_text(str(row['title']) + ' ' + str(row['selftext'])),
                axis=1
            )

            submissions_df['pain_score'] = submissions_df['signals'].apply(lambda x: x['pain'])
            submissions_df['solution_score'] = submissions_df['signals'].apply(lambda x: x['solution'])
            submissions_df['monetization_score'] = submissions_df['signals'].apply(lambda x: x['monetization'])

            # Calculate opportunity score: pain*4 + solution*3 + monetization*5
            submissions_df['opportunity_score'] = (
                submissions_df['pain_score'] * 4 +
                submissions_df['solution_score'] * 3 +
                submissions_df['monetization_score'] * 5
            )

            # Add engagement multiplier
            submissions_df['engagement_multiplier'] = 1 + (submissions_df['score_int'] / 200) + (submissions_df['comments_int'] / 100)
            submissions_df['final_score'] = submissions_df['opportunity_score'] * submissions_df['engagement_multiplier']

    return submissions_df, all_subreddits


@app.cell
def _(mo, submissions_df, db):
    """Database stats"""

    if not db.test_connection():
        mo.md("⚠️ **Database not connected** - Start Supabase with `supabase start`")
    else:
        total_count = len(submissions_df)
        high_opportunity = len(submissions_df[submissions_df['final_score'] >= 50]) if not submissions_df.empty else 0

        mo.md(f"""
        ## 📊 Live Data Summary

        - **Submissions Loaded**: {total_count}
        - **High Opportunity** (score ≥ 50): {high_opportunity}
        - **Data Source**: Supabase Database (Real-time)
        """)


@app.cell
def _(mo, submissions_df, px):
    """View 1: Top Problems by Pain Intensity"""

    mo.md("## 🔥 Top Problems - High Pain Points")

    if not submissions_df.empty:
        # Get top problems by pain score
        top_problems = submissions_df.nlargest(10, 'pain_score')[
            ['title', 'subreddit', 'pain_score', 'score_int', 'final_score']
        ].copy()

        top_problems['title_short'] = top_problems['title'].str[:60] + '...'

        # Bar chart
        problems_chart = px.bar(
            top_problems,
            x='pain_score',
            y='title_short',
            orientation='h',
            color='final_score',
            title="Top 10 Problems by Pain Intensity",
            labels={'pain_score': 'Pain Score', 'title_short': 'Title', 'final_score': 'Opportunity Score'},
            color_continuous_scale='Reds'
        )
        problems_chart.update_layout(height=500, yaxis={'categoryorder':'total ascending'})
        problems_chart

        # Data table
        mo.md("### 📋 Problem Details")
        display_problems = top_problems[['title', 'subreddit', 'pain_score', 'score_int', 'final_score']].copy()
        display_problems.columns = ['Title', 'Subreddit', 'Pain Score', 'Upvotes', 'Opportunity Score']
        problems_table = mo.ui.dataframe(display_problems, page_size=10)
        problems_table
    else:
        mo.md("*No data found. Adjust filters or check database connection.*")

    return problems_chart, problems_table


@app.cell
def _(mo, submissions_df, px):
    """View 2: Monetization Opportunities"""

    mo.md("## 💡 Monetization Opportunities")

    if not submissions_df.empty:
        # Filter for posts with monetization signals
        monetization_opps = submissions_df[submissions_df['monetization_score'] > 0].nlargest(15, 'final_score')

        if not monetization_opps.empty:
            # Scatter plot
            monetization_chart = px.scatter(
                monetization_opps,
                x='monetization_score',
                y='final_score',
                size='score_int',
                color='subreddit',
                hover_data=['title'],
                title="Monetization Signals vs Opportunity Score",
                labels={'monetization_score': 'Monetization Signals', 'final_score': 'Opportunity Score'}
            )
            monetization_chart.update_layout(height=400)
            monetization_chart

            # Data table
            mo.md("### 💰 Top Monetization Opportunities")
            display_money = monetization_opps[['title', 'subreddit', 'monetization_score', 'final_score']].copy()
            display_money.columns = ['Title', 'Subreddit', 'Monetization Signals', 'Opportunity Score']
            money_table = mo.ui.dataframe(display_money, page_size=10)
            money_table
        else:
            mo.md("*No posts found with monetization signals in current filter.*")
    else:
        mo.md("*No data available.*")

    return monetization_chart, money_table


@app.cell
def _(mo, submissions_df, px):
    """View 3: Subreddit Analysis"""

    mo.md("## 📊 Subreddit Opportunity Density")

    if not submissions_df.empty:
        # Group by subreddit
        subreddit_stats = submissions_df.groupby('subreddit').agg({
            'final_score': 'mean',
            'pain_score': 'sum',
            'monetization_score': 'sum',
            'title': 'count'
        }).reset_index()

        subreddit_stats.columns = ['Subreddit', 'Avg Opportunity Score', 'Total Pain Signals', 'Total Monetization', 'Post Count']
        subreddit_stats = subreddit_stats.sort_values('Avg Opportunity Score', ascending=False).head(10)

        # Bar chart
        subreddit_chart = px.bar(
            subreddit_stats,
            x='Avg Opportunity Score',
            y='Subreddit',
            orientation='h',
            color='Total Monetization',
            title="Top 10 Subreddits by Average Opportunity Score",
            color_continuous_scale='Greens'
        )
        subreddit_chart.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
        subreddit_chart

        # Data table
        mo.md("### 📈 Subreddit Comparison")
        subreddit_table = mo.ui.dataframe(subreddit_stats, page_size=10)
        subreddit_table
    else:
        mo.md("*No data available.*")

    return subreddit_chart, subreddit_table


@app.cell
def _(mo, db):
    """Footer and instructions"""

    if db.test_connection():
        # Get total stats from database
        stats_query = """
        SELECT
            COUNT(*) as total_submissions,
            COUNT(DISTINCT subreddit) as total_subreddits
        FROM submission
        """
        stats = db.execute_query(stats_query)

        if not stats.empty:
            total_subs = int(stats.iloc[0]['total_submissions'])
            total_subreddits = int(stats.iloc[0]['total_subreddits'])
        else:
            total_subs = 0
            total_subreddits = 0

        mo.md(f"""
        ---

        ## 📊 Database Statistics

        - **Total Submissions in Database**: {total_subs:,}
        - **Unique Subreddits**: {total_subreddits}
        - **Connection**: Supabase (Local Docker)

        ## 🔄 Refresh Data

        **Collect fresh Reddit data:**
        ```bash
        uv run python scripts/collect_real_reddit_data.py
        ```

        **Then refresh this dashboard** (it will automatically load new data)

        ## 💡 How It Works

        This dashboard connects **directly to your Supabase database** and analyzes submissions in real-time:

        1. **Pain Score**: Counts frustration words (frustrated, broken, problem, etc.)
        2. **Solution Score**: Counts help-seeking phrases (looking for, recommendation, etc.)
        3. **Monetization Score**: Counts payment signals (pay, subscription, premium, etc.)
        4. **Opportunity Score**: Weighted combination of all signals × engagement

        Adjust the filters above to explore different segments of your data.
        """)
    else:
        mo.md("""
        ---

        ## ⚠️ Database Not Connected

        Start your Supabase database:
        ```bash
        supabase start
        ```

        Then refresh this dashboard.
        """)


if __name__ == "__main__":
    app.run()
