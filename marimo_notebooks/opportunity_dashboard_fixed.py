#!/usr/bin/env python3
"""
RedditHarbor Opportunity Dashboard - FIXED

Interactive dashboard showing AI-powered app opportunities from Reddit data.
Fixed: Proper imports, correct table/column names, correct score threshold.
"""

import marimo

__generated_with = "0.17.6"
app = marimo.App()


@app.cell
def _():
    import os

    import marimo as mo

    from supabase import create_client

    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_KEY')
    )
    return mo, supabase


@app.cell
def _(mo):
    mo.md("""
    # 🎯 RedditHarbor - App Opportunity Discovery
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## AI-Powered App Ideas from Reddit

    This dashboard displays app development opportunities identified through:
    1. Reddit data collection from high-signal subreddits
    2. AI analysis using Claude Haiku via OpenRouter
    3. Multi-dimensional scoring (Market, Pain, Monetization, Feasibility, Simplicity)

    **Showing opportunities with score >= 25.0 (1-3 Function Apps per Methodology)**
    """)
    return


@app.cell
def _(supabase):
    # Fetch AI-generated opportunities from app_opportunities table with credibility metrics
    # First try to get data with metrics; if metrics table doesn't exist yet, get just opportunities
    try:
        result = supabase.rpc(
            'get_opportunities_with_metrics',
            {}
        ).execute()
        data = result.data if result.data else []
    except:
        # Fallback: fetch from app_opportunities only (metrics table not yet created)
        result = supabase.table('app_opportunities').select(
            'submission_id, opportunity_score, problem_description, app_concept, core_functions, target_user, monetization_model, subreddit, title'
        ).gte('opportunity_score', 25.0).order('opportunity_score', desc=True).execute()
        data = result.data if result.data else []

    return (data,)


@app.cell
def _(data, mo):
    # Convert to display format with credibility metrics
    if not data:
        table_output = mo.md("No opportunities found with score >= 25.0")
    else:
        display_data = []
        for opp_data in data:
            core_functions = opp_data.get('core_functions', [])
            if isinstance(core_functions, str):
                try:
                    core_functions = eval(core_functions)
                except:
                    core_functions = [str(core_functions)]

            # Format functions as a readable list
            if isinstance(core_functions, list) and core_functions:
                functions_text = "\n".join([f"• {func}" for func in core_functions])
                functions_count = f"{len(core_functions)} functions"
            else:
                functions_text = str(core_functions)
                functions_count = "1 function"

            # Build display row with metrics if available
            row = {
                'Score': f"{opp_data.get('opportunity_score', 0):.1f}",
                'Functions': functions_count,
                'Subreddit': opp_data.get('subreddit', 'N/A') or 'N/A',
                'Problem': opp_data.get('problem_description', 'N/A'),
                'App Concept': opp_data.get('app_concept', 'N/A'),
            }

            # Add credibility metrics if available
            if opp_data.get('comment_count') is not None:
                row.update({
                    'Comments': opp_data.get('comment_count', 0),
                    'Trending': f"{opp_data.get('trending_score', 0):.0f}%",
                    'Spread': f"{opp_data.get('subreddit_spread', 0)} communities",
                    'Intent Signals': opp_data.get('intent_signal_count', 0),
                })

            row.update({
                'Core Functions': functions_text,
                'Target User': opp_data.get('target_user', 'N/A'),
                'Monetization': opp_data.get('monetization_model', 'N/A')
            })

            display_data.append(row)

        table_output = mo.ui.table(display_data, label=f"Top {len(display_data)} AI-Generated Opportunities (with Credibility Signals)")

    table_output
    return


@app.cell
def _(data, mo):
    total = len(data)
    avg_score = sum(summary_opp.get('opportunity_score', 0) for summary_opp in data) / total if total > 0 else 0
    high_score_count = len([o for o in data if o.get('opportunity_score', 0) >= 30])

    # Calculate function distribution
    one_func = 0
    two_func = 0
    three_func = 0

    for summary_opp in data:
        summary_functions = summary_opp.get('core_functions', [])
        if isinstance(summary_functions, str):
            try:
                summary_functions = eval(summary_functions)
            except:
                summary_functions = [summary_functions]

        if len(summary_functions) == 1:
            one_func += 1
        elif len(summary_functions) == 2:
            two_func += 1
        elif len(summary_functions) == 3:
            three_func += 1

    summary_md = mo.md(f"""
    ## Summary

    - **Total AI Profiles (≥25):** {total}
    - **Average Score:** {avg_score:.1f}
    - **High-Score (≥30):** {high_score_count}
    - **Function Distribution:** {one_func} function | {two_func} functions | {three_func} functions
    - **Cost per Profile:** ~$0.001 (Claude Haiku via OpenRouter)
    - **Methodology:** 1-3 function apps (1=100pts, 2=85pts, 3=70pts) with unbiased LLM selection
    """)
    return summary_md


@app.cell
def _(mo):
    mo.md("---")
    mo.md("*Generated by RedditHarbor - AI-Powered App Discovery*")
    return


if __name__ == "__main__":
    app.run()
