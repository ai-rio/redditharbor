#!/usr/bin/env python3
"""
RedditHarbor Opportunity Dashboard - Reactive Version

Displays AI-generated app opportunities from Reddit.
"""

import marimo

__generated_with = "0.17.6"
app = marimo.App()


@app.cell
def __():
    import os

    import marimo as mo

    from supabase import create_client
    return mo, create_client, os


@app.cell
def __(create_client, os):
    supabase = create_client(
        os.getenv('SUPABASE_URL', 'http://127.0.0.1:54321'),
        os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU')
    )
    return supabase,


@app.cell
def __(mo):
    mo.md("# 🎯 RedditHarbor - App Opportunity Discovery")
    return


@app.cell
def __(mo):
    mo.md("""
    ## AI-Powered App Ideas from Reddit

    This dashboard displays app development opportunities identified through:
    1. Reddit data collection from high-signal subreddits
    2. AI analysis using Claude Haiku via OpenRouter
    3. Multi-dimensional scoring (Market, Pain, Monetization, Feasibility, Simplicity)

    **Showing opportunities with score >= 40.0 (Methodology-Compliant 1-3 Function Apps)**
    """)
    return


@app.cell
def __(supabase):
    # Fetch AI-generated opportunities with credibility metrics
    try:
        result = supabase.rpc(
            'get_opportunities_with_metrics',
            {}
        ).execute()
        opportunities = result.data if result.data else []
    except:
        # Fallback: fetch from app_opportunities only
        result = supabase.table('app_opportunities').select(
            'submission_id, opportunity_score, problem_description, app_concept, core_functions, target_user, monetization_model, subreddit, title'
        ).gte('opportunity_score', 40.0).order('opportunity_score', desc=True).execute()
        opportunities = result.data if result.data else []

    return opportunities, result


@app.cell
def __(mo, opportunities):
    if not opportunities:
        no_data_msg = mo.md("### No opportunities found with score >= 25.0")
        no_data_msg
    else:
        # Build table data with optional credibility metrics
        table_data = []
        for table_opp in opportunities:
            table_functions = table_opp.get('core_functions', [])
            if isinstance(table_functions, str):
                try:
                    table_functions = eval(table_functions)
                except:
                    table_functions = [str(table_functions)]

            # Format functions as readable list
            if isinstance(table_functions, list) and table_functions:
                functions_text = "\n".join([f"• {func}" for func in table_functions])
                functions_count = f"{len(table_functions)} functions"
            else:
                functions_text = str(table_functions)
                functions_count = "1 function"

            row = {
                'Score': f"{table_opp.get('opportunity_score', 0):.1f}",
                'Functions': functions_count,
                'Subreddit': table_opp.get('subreddit', 'N/A') or 'N/A',
                'Problem': table_opp.get('problem_description', 'N/A'),
                'App Concept': table_opp.get('app_concept', 'N/A'),
            }

            # Add credibility metrics if available
            if table_opp.get('comment_count') is not None:
                row.update({
                    'Comments': table_opp.get('comment_count', 0),
                    'Trending': f"{table_opp.get('trending_score', 0):.0f}%",
                })

            row.update({
                'Core Functions': functions_text,
                'Target User': table_opp.get('target_user', 'N/A'),
                'Monetization': table_opp.get('monetization_model', 'N/A')
            })

            table_data.append(row)

        opportunities_table = mo.ui.table(table_data, label=f"Top {len(table_data)} AI-Generated Opportunities (with Credibility)")
        opportunities_table
    return table_opp, table_data


@app.cell
def __(mo, opportunities):
    total = len(opportunities)
    avg_score = sum(o.get('opportunity_score', 0) for o in opportunities) / total if total > 0 else 0
    high_score = len([o for o in opportunities if o.get('opportunity_score', 0) >= 45])

    # Calculate function distribution
    one_func = 0
    two_func = 0
    three_func = 0

    for summary_opp in opportunities:
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

    - **Total AI Profiles (≥40):** {total}
    - **Average Score:** {avg_score:.1f}
    - **High-Score (≥45):** {high_score}
    - **Function Distribution:** {one_func} function | {two_func} functions | {three_func} functions
    - **Cost per Profile:** ~$0.001 (Claude Haiku via OpenRouter)
    - **Methodology:** 1-2 function apps prioritized with simplicity scoring
    """)
    return avg_score, high_score, one_func, summary_md, three_func, total, two_func


@app.cell
def __(mo):
    mo.md("---")
    mo.md("*Generated by RedditHarbor - AI-Powered App Discovery*")
    return


if __name__ == "__main__":
    app.run()
