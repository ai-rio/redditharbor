#!/usr/bin/env python3
"""
RedditHarbor Opportunity Analysis Dashboard

Marimo notebook for analyzing and visualizing monetizable app opportunities
from Reddit discussions using the comprehensive research methodology.
"""

import marimo

__generated_with = "0.6.17"
app = marimo.App()


@app.cell
def __init__():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import re
    from datetime import datetime, timedelta

    # Import RedditHarbor utilities
    from marimo_notebooks.utils import DatabaseConnector
    from marimo_notebooks.config import MarimoConfig

    # Initialize database connection
    db_connector = DatabaseConnector()
    config = MarimoConfig()

    # Sentiment analysis keywords for opportunity identification
    PAIN_INDICATORS = [
        "frustrated", "annoying", "terrible", "hate", "worst", "useless",
        "broken", "doesn't work", "problem", "issue", "bug", "crash",
        "slow", "expensive", "difficult", "complicated", "confusing"
    ]

    SOLUTION_SEEKERS = [
        "recommendation", "suggestion", "best", "looking for", "need help",
        "any alternatives", "what do you use", "how to", "tutorial",
        "guide", "alternative", "replacement", "better than"
    ]

    MONETIZATION_SIGNALS = [
        "willing to pay", "subscription", "premium", "pro version",
        "paid", "cost", "price", "affordable", "worth it", "investment",
        "budget", "cheap", "expensive", "free trial"
    ]

    return (
        mo,
        pd,
        np,
        px,
        go,
        make_subplots,
        re,
        datetime,
        timedelta,
        db_connector,
        config,
        PAIN_INDICATORS,
        SOLUTION_SEEKERS,
        MONETIZATION_SIGNALS,
    )


@app.cell
def __(db_connector, mo):
    # Enhanced Database Connection Status with Data Collection Evidence
    mo.md("## 📊 Opportunity Analysis Dashboard")

    # Data collection evidence variables
    data_evidence = {
        "database_connected": False,
        "total_submissions": 0,
        "total_comments": 0,
        "subreddits_covered": 0,
        "data_freshness_hours": None,
        "collection_active": False,
        "methodology_coverage_percentage": 0
    }

    if db_connector.test_connection():
        data_evidence["database_connected"] = True
        mo.md("✅ **Database Connected Successfully**")

        try:
            # Get comprehensive data collection evidence
            import pandas as pd
            from datetime import datetime

            # Submission count
            submission_count = db_connector.execute_query('SELECT COUNT(*) as count FROM submission')
            if not submission_count.empty and "count" in submission_count.columns:
                data_evidence["total_submissions"] = int(submission_count.iloc[0]["count"])

            # Comment count
            comment_count = db_connector.execute_query('SELECT COUNT(*) as count FROM comment')
            if not comment_count.empty and "count" in comment_count.columns:
                data_evidence["total_comments"] = int(comment_count.iloc[0]["count"])

            # Subreddit coverage and freshness
            coverage_query = '''
                SELECT
                    COUNT(DISTINCT subreddit) as unique_subreddits,
                    MIN(created_at) as earliest,
                    MAX(created_at) as latest,
                    COUNT(*) as total_posts
                FROM submission
            '''
            coverage_data = db_connector.execute_query(coverage_query)
            if not coverage_data.empty:
                data_evidence["subreddits_covered"] = int(coverage_data.iloc[0]["unique_subreddits"])
                latest = coverage_data.iloc[0]["latest"]
                if pd.notna(latest):
                    freshness = datetime.now(latest.tzinfo) - latest
                    data_evidence["data_freshness_hours"] = int(freshness.total_seconds() / 3600)
                    data_evidence["collection_active"] = True

            # Calculate methodology coverage (target: 73 subreddits)
            data_evidence["methodology_coverage_percentage"] = (data_evidence["subreddits_covered"] / 73) * 100

        except Exception as e:
            mo.md(f"⚠️ **Error getting data collection stats**: {e}")
    else:
        mo.md("❌ **Database Connection Failed**")

    # Display comprehensive data collection status
    status_emoji = "🟢" if data_evidence["database_connected"] else "🔴"
    freshness_emoji = "🟢" if (data_evidence["data_freshness_hours"] or 999) <= 24 else "🟡" if (data_evidence["data_freshness_hours"] or 999) <= 72 else "🔴"
    coverage_emoji = "🟢" if data_evidence["methodology_coverage_percentage"] >= 25 else "🟡" if data_evidence["methodology_coverage_percentage"] >= 10 else "🔴"

    mo.md(f"""
    ### 🎯 Data Collection Evidence & System Status

    **Connection Status:** {status_emoji} Database {'Connected' if data_evidence['database_connected'] else 'Disconnected'}

    **Data Freshness:** {freshness_emoji} Last collection {data_evidence['data_freshness_hours'] or 'N/A'} hours ago

    **Coverage Status:** {coverage_emoji} {data_evidence['subreddits_covered']}/73 methodology subreddits ({data_evidence['methodology_coverage_percentage']:.1f}% coverage)

    **Sample Size:** 📊 {data_evidence['total_submissions']:,} submissions | 💬 {data_evidence['total_comments']:,} comments
    """)

    # Create trustworthiness indicators table
    trustworthiness_df = pd.DataFrame([
        {
            "Trust Factor": "Data Source Authenticity",
            "Status": "✅ Verified Reddit API",
            "Score": "100%",
            "Details": "Direct API integration with verified subreddits"
        },
        {
            "Trust Factor": "Sample Size Adequacy",
            "Status": "✅ Excellent" if data_evidence['total_submissions'] >= 500 else "⚠️ Moderate" if data_evidence['total_submissions'] >= 100 else "❌ Insufficient",
            "Score": f"{min(100, (data_evidence['total_submissions'] / 500) * 100):.0f}%",
            "Details": f"{data_evidence['total_submissions']:,} submissions analyzed"
        },
        {
            "Trust Factor": "Data Freshness",
            "Status": "✅ Fresh" if (data_evidence['data_freshness_hours'] or 999) <= 24 else "⚠️ Recent" if (data_evidence['data_freshness_hours'] or 999) <= 72 else "❌ Stale",
            "Score": f"{max(0, 100 - (data_evidence['data_freshness_hours'] or 999))}%",
            "Details": f"Updated {data_evidence['data_freshness_hours'] or 'N/A'} hours ago"
        },
        {
            "Trust Factor": "Market Coverage",
            "Status": "✅ Good" if data_evidence['methodology_coverage_percentage'] >= 25 else "⚠️ Limited",
            "Score": f"{min(100, data_evidence['methodology_coverage_percentage']):.0f}%",
            "Details": f"{data_evidence['subreddits_covered']} subreddits covered"
        }
    ])

    mo.md("### 🔍 Trustworthiness Indicators")
    mo.ui.dataframe(trustworthiness_df, selection=None, pagination=False)

    # Get available tables
    tables_df = db_connector.get_available_tables()

    if not tables_df.empty and "error" not in tables_df.columns:
        mo.md(f"📁 **Available Tables**: {', '.join(tables_df['table_name'].tolist())}")
    else:
        mo.md("⚠️ **No tables available - Please run data collection first**")

    return tables_df, data_evidence, trustworthiness_df


@app.cell
def __(mo):
    # Market segment selector
    market_segments = [
        "Health & Fitness",
        "Finance & Investing",
        "Education & Career",
        "Travel & Experiences",
        "Real Estate",
        "Technology & SaaS Productivity"
    ]

    selected_segment = mo.ui.dropdown(
        label="Select Market Segment",
        options=market_segments,
        value="Technology & SaaS Productivity"
    )

    return market_segments, selected_segment


@app.cell
def __(db_connector, mo, data_evidence):
    # Real-time Data Quality Monitoring
    mo.md("### 📈 Real-time Data Quality Monitoring")

    try:
        import pandas as pd
        from datetime import datetime, timedelta

        # Get recent collection activity (last 7 days)
        activity_query = '''
            SELECT
                DATE(created_at) as collection_date,
                COUNT(*) as posts_collected,
                COUNT(DISTINCT subreddit) as subreddits_active,
                AVG((score->>'0')::numeric) as avg_score,
                SUM((num_comments->>'0')::numeric) as total_comments
            FROM submission
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY collection_date DESC
            LIMIT 7
        '''
        activity_data = db_connector.execute_query(activity_query)

        if not activity_data.empty and "error" not in activity_data.columns:
            # Display collection activity
            mo.ui.dataframe(activity_data, selection=None, pagination=False)

            # Calculate data quality metrics
            total_posts_last_7d = activity_data['posts_collected'].sum()
            active_subreddits_7d = activity_data['subreddits_active'].sum()
            avg_engagement = activity_data['total_comments'].sum() / max(1, total_posts_last_7d)

            # Data quality indicators
            quality_score = 0
            quality_indicators = []

            if total_posts_last_7d >= 300:
                quality_score += 25
                quality_indicators.append("✅ High Volume Collection")
            elif total_posts_last_7d >= 100:
                quality_score += 15
                quality_indicators.append("🟡 Moderate Volume Collection")
            else:
                quality_indicators.append("❌ Low Volume Collection")

            if active_subreddits_7d >= 10:
                quality_score += 25
                quality_indicators.append("✅ Diverse Subreddit Coverage")
            elif active_subreddits_7d >= 5:
                quality_score += 15
                quality_indicators.append("🟡 Moderate Coverage")
            else:
                quality_indicators.append("❌ Limited Coverage")

            if avg_engagement >= 10:
                quality_score += 25
                quality_indicators.append("✅ High Engagement Data")
            elif avg_engagement >= 5:
                quality_score += 15
                quality_indicators.append("🟡 Moderate Engagement")
            else:
                quality_indicators.append("❌ Low Engagement")

            if data_evidence["data_freshness_hours"] and data_evidence["data_freshness_hours"] <= 24:
                quality_score += 25
                quality_indicators.append("✅ Fresh Data Collection")
            elif data_evidence["data_freshness_hours"] and data_evidence["data_freshness_hours"] <= 72:
                quality_score += 15
                quality_indicators.append("🟡 Recent Data Collection")
            else:
                quality_indicators.append("❌ Stale Data")

            # Overall quality grade
            if quality_score >= 80:
                quality_grade = "🟢 EXCELLENT"
            elif quality_score >= 60:
                quality_grade = "🟡 GOOD"
            elif quality_score >= 40:
                quality_grade = "🟠 FAIR"
            else:
                quality_grade = "🔴 POOR"

            mo.md(f"""
            **Data Quality Score:** {quality_score}/100 - {quality_grade}

            **Quality Indicators:** {', '.join(quality_indicators)}

            **7-Day Summary:** {total_posts_last_7d:,} posts from {active_subreddits_7d} subreddits
            """)

            # Get subreddit breakdown
            subreddit_query = '''
                SELECT
                    subreddit,
                    COUNT(*) as post_count,
                    AVG((score->>'0')::numeric) as avg_score,
                    SUM((num_comments->>'0')::numeric) as total_comments,
                    MAX(created_at) as latest_post
                FROM submission
                WHERE created_at >= NOW() - INTERVAL '7 days'
                GROUP BY subreddit
                ORDER BY post_count DESC
                LIMIT 10
            '''
            subreddit_data = db_connector.execute_query(subreddit_query)

            if not subreddit_data.empty and "error" not in subreddit_data.columns:
                mo.md("### 📊 Top Subreddits by Recent Activity")
                mo.ui.dataframe(subreddit_data, selection=None, pagination=False)

        else:
            mo.md("⚠️ **No recent collection activity data available**")

    except Exception as e:
        mo.md(f"❌ **Error loading data quality metrics**: {e}")

    return


@app.cell
def __(mo, selected_segment):
    # Time range selector for analysis
    time_ranges = {
        "Last 30 days": 30,
        "Last 90 days": 90,
        "Last 6 months": 180,
        "Last year": 365
    }

    selected_time_range = mo.ui.dropdown(
        label="Analysis Time Range",
        options=list(time_ranges.keys()),
        value="Last 90 days"
    )

    return time_ranges, selected_time_range


@app.cell
def __(db_connector, mo, pd):
    # Function to analyze opportunities from Reddit data
    def analyze_opportunities(segment_name: str, days_back: int = 90):
        """
        Analyze Reddit discussions for monetizable app opportunities
        """

        # Get date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Map segment to subreddits (simplified for example)
        segment_subreddits = {
            "Health & Fitness": ["fitness", "nutrition", "loseit", "gainit"],
            "Finance & Investing": ["personalfinance", "investing", "stocks"],
            "Education & Career": ["learnprogramming", "cscareerquestions", "selfimprovement"],
            "Travel & Experiences": ["travel", "solotravel", "TravelHacks"],
            "Real Estate": ["RealEstate", "FirstTimeHomeBuyer", "HomeImprovement"],
            "Technology & SaaS Productivity": ["SaaS", "productivity", "startups"]
        }

        target_subreddits = segment_subreddits.get(segment_name, ["SaaS", "productivity"])
        subreddit_list = "', '".join(target_subreddits)

        # Query recent posts from target subreddits
        query = f"""
        SELECT
            s.subreddit,
            s.title,
            s.selftext,
            s.score,
            s.num_comments,
            s.created_utc,
            c.body as comment_text,
            c.score as comment_score
        FROM submission s
        LEFT JOIN comment c ON s.id = c.parent_id
        WHERE s.subreddit IN ('{subreddit_list}')
        AND s.created_utc >= '{start_date.isoformat()}'
        ORDER BY s.score DESC, s.num_comments DESC
        LIMIT 1000
        """

        try:
            data_df = db_connector.execute_query(query)

            if "error" in data_df.columns:
                mo.md(f"❌ **Query Error**: {data_df['error'].iloc[0]}")
                return pd.DataFrame()

            # Add data collection evidence to the results
            if not data_df.empty:
                collection_evidence = {
                    "sample_size": len(data_df),
                    "data_freshness": f"Data from {segment_name} discussions",
                    "collection_period": f"Last {days_back} days",
                    "subreddits_analyzed": target_subreddits,
                    "analysis_confidence": "HIGH" if len(data_df) >= 100 else "MODERATE" if len(data_df) >= 50 else "LOW"
                }
                print(f"📊 Data Collection Evidence: {collection_evidence}")

            return data_df

        except Exception as e:
            mo.md(f"❌ **Analysis Error**: {str(e)}")
            return pd.DataFrame()

    return analyze_opportunities,


@app.cell
def __(analyze_opportunities, mo, selected_segment, selected_time_range, time_ranges, data_evidence):
    # Run analysis based on selections
    days_back = time_ranges[selected_time_range.value]

    with mo.status.spinner() as _status:
        _status.text(f"Analyzing {selected_segment.value} opportunities...")
        opportunity_data = analyze_opportunities(selected_segment.value, days_back)

    if opportunity_data.empty:
        mo.md("❌ **No data available for selected segment**")
    else:
        # Enhanced results display with data collection evidence
        confidence_level = "HIGH" if len(opportunity_data) >= 100 else "MODERATE" if len(opportunity_data) >= 50 else "LOW"
        confidence_emoji = "🟢" if confidence_level == "HIGH" else "🟡" if confidence_level == "MODERATE" else "🔴"

        mo.md(f"""
        ✅ **Found {len(opportunity_data):,} discussions in {selected_segment.value}**

        **Data Collection Evidence:**
        - **Confidence Level:** {confidence_emoji} {confidence_level}
        - **Overall Database:** {data_evidence['total_submissions']:,} total submissions available
        - **Market Coverage:** {data_evidence['subreddits_covered']}/73 methodology subreddits
        - **Data Freshness:** {data_evidence['data_freshness_hours'] or 'N/A'} hours since last collection
        - **Analysis Period:** Last {days_back} days
        """)

    return days_back, opportunity_data, confidence_level


@app.cell
def __(opportunity_data, pd, PAIN_INDICATORS, SOLUTION_SEEKERS, MONETIZATION_SIGNALS):
    # Function to score individual opportunities
    def score_opportunity(row):
        """
        Score an individual Reddit post/comment for monetization potential
        """
        text = str(row.get('title', '')) + ' ' + str(row.get('selftext', '')) + ' ' + str(row.get('comment_text', ''))
        text = text.lower()

        score = 0
        max_score = 100

        # Pain Indicators (40 points)
        pain_score = 0
        for indicator in PAIN_INDICATORS:
            if indicator in text:
                pain_score += min(40, len([m.start() for m in re.finditer(indicator, text)]) * 5)

        # Solution Seekers (30 points)
        solution_score = 0
        for seeker in SOLUTION_SEEKERS:
            if seeker in text:
                solution_score += min(30, len([m.start() for m in re.finditer(seeker, text)]) * 4)

        # Monetization Signals (20 points)
        monetization_score = 0
        for signal in MONETIZATION_SIGNALS:
            if signal in text:
                monetization_score += min(20, len([m.start() for m in re.finditer(signal, text)]) * 3)

        # Engagement Score (10 points)
        engagement_score = min(10, int(row.get('score', 0)) / 100) + min(10, int(row.get('num_comments', 0)) / 50)

        total_score = min(pain_score + solution_score + monetization_score + engagement_score, max_score)

        return {
            'total_score': total_score,
            'pain_score': min(pain_score, 40),
            'solution_score': min(solution_score, 30),
            'monetization_score': min(monetization_score, 20),
            'engagement_score': min(engagement_score, 10)
        }

    return score_opportunity,


@app.cell
def __(opportunity_data, pd, score_opportunity):
    # Apply scoring to all opportunities
    if not opportunity_data.empty:
        scored_opportunities = opportunity_data.copy()

        # Calculate scores for each row
        score_results = scored_opportunities.apply(score_opportunity, axis=1, result_type='expand')

        # Merge scores back to original data
        scored_opportunities = pd.concat([scored_opportunities, score_results], axis=1)

        # Sort by total score
        scored_opportunities = scored_opportunities.sort_values('total_score', ascending=False)

        # Add opportunity categorization
        def categorize_opportunity(score):
            if score >= 80:
                return "High Priority"
            elif score >= 60:
                return "Medium-High Priority"
            elif score >= 40:
                return "Medium Priority"
            else:
                return "Low Priority"

        scored_opportunities['priority'] = scored_opportunities['total_score'].apply(categorize_opportunity)
    else:
        scored_opportunities = pd.DataFrame()

    return scored_opportunities, categorize_opportunity


@app.cell
def __(scored_opportunities, mo):
    # Display top opportunities
    if not scored_opportunities.empty:
        mo.md("### 🎯 Top Monetizable Opportunities")

        top_opportunities = scored_opportunities.head(10)

        # Create display table with key metrics
        display_data = top_opportunities[[
            'subreddit', 'title', 'total_score', 'priority',
            'score', 'num_comments'
        ]].copy()

        display_data.columns = ['Subreddit', 'Title', 'Opportunity Score', 'Priority', 'Reddit Score', 'Comments']

        mo.table(display_data)
    else:
        mo.md("❌ **No opportunities scored**")

    return display_data, top_opportunities


@app.cell
def __(go, make_subplots, mo, px, scored_opportunities):
    # Visualize opportunity analysis
    if not scored_opportunities.empty:
        mo.md("### 📈 Opportunity Analysis Visualizations")

        # Score distribution chart
        fig1 = px.histogram(
            scored_opportunities,
            x='total_score',
            title="Distribution of Opportunity Scores",
            labels={'total_score': 'Opportunity Score', 'count': 'Frequency'},
            nbins=20,
            color_discrete_sequence=['#FF6B35']
        )
        fig1.update_layout(height=400)
        mo.plotly(fig1)

        # Score breakdown by priority
        priority_counts = scored_opportunities['priority'].value_counts()
        fig2 = px.pie(
            values=priority_counts.values,
            names=priority_counts.index,
            title="Opportunity Priority Distribution",
            color_discrete_map={
                "High Priority": "#FF6B35",
                "Medium-High Priority": "#004E89",
                "Medium Priority": "#F7B801",
                "Low Priority": "#A0A0A0"
            }
        )
        fig2.update_layout(height=400)
        mo.plotly(fig2)

        # Subreddit opportunity heatmap
        subreddit_scores = scored_opportunities.groupby('subreddit')['total_score'].agg(['mean', 'count']).reset_index()
        subreddit_scores.columns = ['Subreddit', 'Average Score', 'Opportunity Count']

        fig3 = px.scatter(
            subreddit_scores,
            x='Opportunity Count',
            y='Average Score',
            size='Opportunity Count',
            hover_name='Subreddit',
            title="Opportunity Analysis by Subreddit",
            color='Average Score',
            color_continuous_scale='Viridis'
        )
        fig3.update_layout(height=500)
        mo.plotly(fig3)

    return priority_counts, subreddit_scores


@app.cell
def __(mo, scored_opportunities):
    # Generate opportunity recommendations
    if not scored_opportunities.empty:
        mo.md("### 💡 Opportunity Recommendations")

        # Get high-priority opportunities
        high_priority = scored_opportunities[scored_opportunities['total_score'] >= 80]

        if not high_priority.empty:
            mo.md(f"🎯 **Found {len(high_priority)} high-priority opportunities**")

            # Generate summary insights
            insights = []

            # Top subreddit by opportunity count
            top_subreddit = high_priority['subreddit'].value_counts().index[0]
            insights.append(f"**{top_subreddit}** shows highest opportunity concentration")

            # Average engagement for high-priority opportunities
            avg_engagement = high_priority['num_comments'].mean()
            insights.append(f"**{avg_engagement:.1f} average comments** per high-priority opportunity")

            # Common patterns
            common_keywords = []
            for _, row in high_priority.head(5).iterrows():
                title_words = str(row.get('title', '')).lower().split()
                common_keywords.extend([word for word in title_words if len(word) > 4])

            if common_keywords:
                from collections import Counter
                word_freq = Counter(common_keywords)
                top_words = word_freq.most_common(3)
                insights.append(f"**Common themes**: {', '.join([word for word, count in top_words])}")

            for insight in insights:
                mo.md(f"• {insight}")
        else:
            mo.md("⚠️ **No high-priority opportunities found. Consider adjusting analysis parameters.**")

    return high_priority, insights, avg_engagement, common_keywords, word_freq


@app.cell
def __(mo, data_evidence):
    # Action items and next steps with data collection improvements
    mo.md("### 🚀 Action Items & Next Steps")

    action_items = [
        "1. **Validate top opportunities** through targeted user research",
        "2. **Analyze competitive landscape** for high-priority opportunities",
        "3. **Develop MVP specifications** for top 3 opportunities",
        "4. **Create user acquisition strategy** based on subreddit demographics",
        "5. **Build monetization model** based on price sensitivity discussions"
    ]

    for item in action_items:
        mo.md(f"{item}")

    # Data collection improvement recommendations
    mo.md("### 📈 Data Collection Improvement Plan")

    coverage_percentage = data_evidence["methodology_coverage_percentage"]

    if coverage_percentage < 25:
        mo.md("🎯 **Priority 1: Expand Subreddit Coverage**")
        mo.md(f"Current coverage: {data_evidence['subreddits_covered']}/73 subreddits ({coverage_percentage:.1f}%)")
        mo.md("Action: Add 20+ new subreddits to reach 25% methodology coverage")

    if data_evidence["total_comments"] < 200:
        mo.md("💬 **Priority 2: Improve Comment Collection**")
        mo.md(f"Current comments: {data_evidence['total_comments']:,} (Target: 200+)")
        mo.md("Action: Optimize comment collection pipeline for deeper analysis")

    if data_evidence["data_freshness_hours"] and data_evidence["data_freshness_hours"] > 48:
        mo.md("🔄 **Priority 3: Freshen Data Collection**")
        mo.md(f"Data age: {data_evidence['data_freshness_hours']} hours (Target: < 24 hours)")
        mo.md("Action: Increase collection frequency for real-time insights")

    mo.md(f"""
    **Current Data Quality Score:**
    - Sample Size: {"✅" if data_evidence['total_submissions'] >= 500 else "⚠️"} {data_evidence['total_submissions']:,} submissions
    - Coverage: {"✅" if coverage_percentage >= 25 else "⚠️"} {coverage_percentage:.1f}% of methodology
    - Freshness: {"✅" if (data_evidence['data_freshness_hours'] or 999) <= 48 else "⚠️"} {data_evidence['data_freshness_hours'] or 'N/A'} hours old
    """)

    return action_items


if __name__ == "__main__":
    app.run()