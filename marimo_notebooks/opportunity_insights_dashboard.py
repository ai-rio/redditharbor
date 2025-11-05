import marimo

__generated_with = "0.17.6"
app = marimo.App(app_title="RedditHarbor - Opportunity Insights")


@app.cell
def _():
    """Setup and database connection"""
    import sys
    from pathlib import Path
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from datetime import datetime

    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    from marimo_notebooks.utils import DatabaseConnector

    db = DatabaseConnector()
    db_connected = db.test_connection()

    return mo, pd, px, go, Path, project_root, db, db_connected, datetime


@app.cell
def _(mo, db_connected):
    """Header"""
    status = "✅ Connected" if db_connected else "❌ Not Connected"
    mo.md(f"""
    # 🎯 RedditHarbor - Opportunity Insights Dashboard

    **Your comprehensive decision-making tool for finding monetizable app opportunities**

    Status: {status}
    """)
    return status,


@app.cell
def _(db, db_connected, pd):
    """Load ALL submissions from database"""
    submissions_df = pd.DataFrame()

    if db_connected:
        query = """
        SELECT
            submission_id, title, text as selftext, subreddit,
            score, num_comments, created_at, permalink as url
        FROM submission
        ORDER BY created_at DESC
        """
        submissions_df = db.execute_query(query)

    return submissions_df, query


@app.cell
def _(submissions_df, pd):
    """Process and analyze ALL submissions"""
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

        # Analyze text for signals
        def count_signals(text):
            if pd.isna(text):
                return 0, 0, 0
            text = str(text).lower()

            pain = sum(text.count(w) for w in ['problem', 'issue', 'broken', 'frustrated', 'terrible', 'hate', 'worst', 'annoying'])
            solution = sum(text.count(w) for w in ['looking for', 'recommend', 'alternative', 'how to', 'help', 'suggest', 'need'])
            money = sum(text.count(w) for w in ['pay', 'price', 'subscription', 'premium', 'cost', 'worth it', 'willing to pay'])

            return pain, solution, money

        # Apply analysis
        signals = analyzed_df.apply(
            lambda row: count_signals(str(row['title']) + ' ' + str(row['selftext'])),
            axis=1
        )

        analyzed_df['pain_score'] = signals.apply(lambda x: x[0])
        analyzed_df['solution_score'] = signals.apply(lambda x: x[1])
        analyzed_df['monetization_score'] = signals.apply(lambda x: x[2])

        # Calculate opportunity score (pain*4 + solution*3 + monetization*5)
        analyzed_df['opportunity_score'] = (
            analyzed_df['pain_score'] * 4 +
            analyzed_df['solution_score'] * 3 +
            analyzed_df['monetization_score'] * 5
        )

        # Engagement multiplier
        analyzed_df['engagement'] = 1 + (analyzed_df['score_int'] / 200) + (analyzed_df['comments_int'] / 100)
        analyzed_df['final_score'] = analyzed_df['opportunity_score'] * analyzed_df['engagement']

        # Priority classification
        def classify_priority(score):
            if score >= 100:
                return "🔥 CRITICAL"
            elif score >= 50:
                return "⚡ HIGH"
            elif score >= 25:
                return "💡 MEDIUM"
            elif score >= 10:
                return "📌 LOW"
            else:
                return "❌ SKIP"

        analyzed_df['priority'] = analyzed_df['final_score'].apply(classify_priority)

    return analyzed_df,


@app.cell
def _(mo, analyzed_df, db_connected):
    """Executive Summary"""
    summary_content = mo.md("Loading...")

    if db_connected and not analyzed_df.empty:
        total = len(analyzed_df)
        critical = len(analyzed_df[analyzed_df['final_score'] >= 100])
        high = len(analyzed_df[analyzed_df['final_score'] >= 50])
        with_signals_count = len(analyzed_df[analyzed_df['opportunity_score'] > 0])
        avg_score = analyzed_df['final_score'].mean()

        summary_content = mo.md(f"""
        ## 📊 Executive Summary

        | Metric | Value |
        |--------|-------|
        | **Total Posts Analyzed** | {total:,} |
        | **With Opportunity Signals** | {with_signals_count:,} ({with_signals_count/total*100:.1f}%) |
        | **Critical Priority (≥100)** | {critical} |
        | **High Priority (≥50)** | {high} |
        | **Average Opportunity Score** | {avg_score:.1f} |
        """)

    summary_content
    return summary_content,


@app.cell
def _(mo, analyzed_df, px):
    """Top 20 Opportunities"""
    mo.md("## 🏆 Top 20 Opportunities - Ready to Build")

    top20_viz = mo.md("No data")
    top20_table = mo.md("")

    if not analyzed_df.empty:
        # Get top 20 by final score
        top_opportunities = analyzed_df.nlargest(20, 'final_score')

        if not top_opportunities.empty:
            # Create visualization
            top_opportunities_display = top_opportunities.copy()
            top_opportunities_display['title_short'] = top_opportunities_display['title'].str[:60] + '...'

            top20_chart = px.bar(
                top_opportunities_display,
                x='final_score',
                y='title_short',
                orientation='h',
                color='priority',
                title="Top 20 Opportunities by Final Score",
                labels={'final_score': 'Opportunity Score', 'title_short': 'Discussion'},
                color_discrete_map={
                    '🔥 CRITICAL': '#FF0000',
                    '⚡ HIGH': '#FF6B35',
                    '💡 MEDIUM': '#F7B801',
                    '📌 LOW': '#4A90E2'
                }
            )
            top20_chart.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
            top20_viz = top20_chart

            # Create detailed table
            top20_df = top_opportunities[[
                'priority', 'title', 'subreddit', 'pain_score', 'solution_score',
                'monetization_score', 'score_int', 'final_score'
            ]].copy()
            top20_df.columns = [
                'Priority', 'Discussion', 'Subreddit', 'Pain', 'Solution',
                'Money', 'Upvotes', 'Final Score'
            ]
            top20_table = mo.ui.dataframe(top20_df, page_size=20)

    top20_viz
    top20_table

    return top20_viz, top20_table, top_opportunities


@app.cell
def _(mo, analyzed_df, px):
    """Problem Category Breakdown"""
    mo.md("## 📈 Problem Category Distribution")

    category_viz = mo.md("No data")

    if not analyzed_df.empty:
        # Filter posts with signals
        with_signals = analyzed_df[analyzed_df['opportunity_score'] > 0]

        if not with_signals.empty:
            # Calculate category totals
            category_data = pd.DataFrame({
                'Category': ['Pain Points', 'Solution Seeking', 'Monetization Signals'],
                'Total Signals': [
                    with_signals['pain_score'].sum(),
                    with_signals['solution_score'].sum(),
                    with_signals['monetization_score'].sum()
                ],
                'Avg per Post': [
                    with_signals['pain_score'].mean(),
                    with_signals['solution_score'].mean(),
                    with_signals['monetization_score'].mean()
                ]
            })

            category_chart = px.bar(
                category_data,
                x='Category',
                y='Total Signals',
                title="Signal Distribution Across All Posts",
                color='Category',
                color_discrete_map={
                    'Pain Points': '#FF6B35',
                    'Solution Seeking': '#4A90E2',
                    'Monetization Signals': '#00C853'
                }
            )
            category_chart.update_layout(height=400, showlegend=False)
            category_viz = category_chart

    category_viz

    return category_viz, category_data


@app.cell
def _(mo, analyzed_df, px):
    """Subreddit Gold Mines"""
    mo.md("## 💎 Subreddit Gold Mines - Best Communities")

    subreddit_viz = mo.md("No data")
    subreddit_table = mo.md("")

    if not analyzed_df.empty:
        # Group by subreddit
        subreddit_stats = analyzed_df.groupby('subreddit').agg({
            'final_score': ['mean', 'sum', 'count'],
            'pain_score': 'sum',
            'monetization_score': 'sum',
            'opportunity_score': 'mean'
        }).reset_index()

        subreddit_stats.columns = [
            'Subreddit', 'Avg Score', 'Total Score', 'Post Count',
            'Total Pain', 'Total Money', 'Avg Opportunity'
        ]

        # Filter and sort
        subreddit_stats = subreddit_stats[subreddit_stats['Post Count'] >= 5]  # Min 5 posts
        subreddit_stats = subreddit_stats.sort_values('Avg Score', ascending=False).head(15)

        if not subreddit_stats.empty:
            subreddit_chart = px.scatter(
                subreddit_stats,
                x='Post Count',
                y='Avg Score',
                size='Total Money',
                color='Total Pain',
                hover_name='Subreddit',
                title="Top 15 Subreddits by Opportunity Density",
                labels={
                    'Post Count': 'Number of Posts',
                    'Avg Score': 'Average Opportunity Score',
                    'Total Money': 'Monetization Signals',
                    'Total Pain': 'Pain Signals'
                },
                color_continuous_scale='Reds'
            )
            subreddit_chart.update_layout(height=500)
            subreddit_viz = subreddit_chart

            # Table
            subreddit_display = subreddit_stats[['Subreddit', 'Avg Score', 'Post Count', 'Total Pain', 'Total Money']].copy()
            subreddit_table = mo.ui.dataframe(subreddit_display, page_size=15)

    subreddit_viz
    subreddit_table

    return subreddit_viz, subreddit_table, subreddit_stats


@app.cell
def _(mo, analyzed_df):
    """App Ideas Extraction"""
    mo.md("## 💡 Specific App Ideas - Extracted from Discussions")

    app_ideas_content = mo.md("No high-value app ideas found")

    if not analyzed_df.empty:
        # Get high-score opportunities with monetization signals
        app_ideas = analyzed_df[
            (analyzed_df['final_score'] >= 50) &
            (analyzed_df['monetization_score'] > 0)
        ].nlargest(10, 'final_score')

        if not app_ideas.empty:
            # Format as actionable app ideas
            ideas_list = []
            for idx, row in app_ideas.iterrows():
                ideas_list.append(f"""
### {row['priority']} - Score: {row['final_score']:.1f}
**Problem:** {row['title']}
**Community:** r/{row['subreddit']}
**Signals:** Pain={row['pain_score']}, Solution={row['solution_score']}, Money={row['monetization_score']}
**Engagement:** {row['score_int']} upvotes, {row['comments_int']} comments
                """)

            app_ideas_content = mo.md("\n".join(ideas_list))

    app_ideas_content

    return app_ideas_content, app_ideas


@app.cell
def _(mo, analyzed_df, px):
    """Score Distribution"""
    mo.md("## 📊 Opportunity Score Distribution")

    distribution_viz = mo.md("No data")

    if not analyzed_df.empty:
        # Create histogram
        dist_chart = px.histogram(
            analyzed_df[analyzed_df['final_score'] > 0],
            x='final_score',
            nbins=50,
            title="Distribution of Opportunity Scores",
            labels={'final_score': 'Opportunity Score', 'count': 'Number of Posts'},
            color_discrete_sequence=['#4A90E2']
        )
        dist_chart.update_layout(height=400)

        # Add vertical lines for priority thresholds
        dist_chart.add_vline(x=100, line_dash="dash", line_color="red", annotation_text="Critical")
        dist_chart.add_vline(x=50, line_dash="dash", line_color="orange", annotation_text="High")
        dist_chart.add_vline(x=25, line_dash="dash", line_color="yellow", annotation_text="Medium")

        distribution_viz = dist_chart

    distribution_viz

    return distribution_viz, dist_chart


@app.cell
def _(mo, db, db_connected):
    """Footer with Database Stats"""
    footer_content = mo.md("Database not connected")

    if db_connected:
        stats = db.execute_query("SELECT COUNT(*) as total, COUNT(DISTINCT subreddit) as subs FROM submission")

        if not stats.empty:
            total_posts = int(stats.iloc[0]['total'])
            total_subs = int(stats.iloc[0]['subs'])

            footer_content = mo.md(f"""
            ---

            ## 🔍 How to Use This Dashboard

            1. **Check Executive Summary** - Get overview of opportunity landscape
            2. **Review Top 20 Opportunities** - Focus on Critical and High priority items
            3. **Explore Subreddit Gold Mines** - Identify best communities to monitor
            4. **Read Specific App Ideas** - Get actionable business opportunities
            5. **Analyze Score Distribution** - Understand opportunity density

            ## 📊 Database Info

            - **Total Posts:** {total_posts:,}
            - **Unique Subreddits:** {total_subs}
            - **Connection:** Supabase (Local)

            ## 🎯 Next Steps

            1. Pick 2-3 Critical priority opportunities
            2. Validate demand in target subreddits
            3. Research existing solutions (if any)
            4. Start building MVP

            ---

            **Methodology:** Pain×4 + Solution×3 + Monetization×5, multiplied by engagement factor
            """)

    footer_content

    return footer_content,


if __name__ == "__main__":
    app.run()
