import marimo

__generated_with = "0.10.14"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import altair as alt
    from supabase import create_client
    import os
    return alt, create_client, mo, os, pd


@app.cell
def _(create_client, os):
    # Database connection
    supabase_url = os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")
    supabase_key = os.getenv("SUPABASE_KEY")
    supabase = create_client(supabase_url, supabase_key)
    return supabase, supabase_key, supabase_url


@app.cell
def _(mo):
    mo.md("# 🎯 Top Opportunity Contenders Dashboard")
    return


@app.cell
def _(mo):
    mo.md("## Filters")
    return


@app.cell
def _(mo):
    # UI Controls
    sector_filter = mo.ui.dropdown(
        options=["All", "Health & Fitness", "Technology", "Finance & Money", "Education", "Productivity", "Entertainment"],
        value="All",
        label="Sector:"
    )
    return (sector_filter,)


@app.cell
def _(mo):
    min_score_slider = mo.ui.slider(0, 100, value=15, label="Minimum Score:", show_value=True)
    return (min_score_slider,)


@app.cell
def _(mo):
    top_n_slider = mo.ui.slider(5, 50, value=20, step=5, label="Top N Results:", show_value=True)
    return (top_n_slider,)


@app.cell
def _(min_score_slider, mo, sector_filter, top_n_slider):
    mo.hstack([sector_filter, min_score_slider, top_n_slider], justify="start", gap=2)
    return


@app.cell
def _(min_score_slider, pd, sector_filter, supabase, top_n_slider):
    # Fetch opportunity_analysis data
    query = supabase.table("opportunity_analysis").select("*")

    if sector_filter.value != "All":
        query = query.eq("sector", sector_filter.value)

    query = query.gte("final_score", min_score_slider.value)
    query = query.order("final_score", desc=True).limit(top_n_slider.value)

    opp_response = query.execute()
    opp_df = pd.DataFrame(opp_response.data)

    # Fetch matching submissions
    if len(opp_df) > 0:
        submission_ids = opp_df['submission_id'].tolist()
        sub_query = supabase.table("submissions").select(
            "id, content, problem_keywords, solution_mentions, upvotes, comments_count"
        ).in_("id", submission_ids)
        sub_response = sub_query.execute()
        sub_df = pd.DataFrame(sub_response.data)

        # Merge dataframes
        df = opp_df.merge(sub_df, left_on='submission_id', right_on='id', how='left', suffixes=('', '_sub'))
    else:
        df = opp_df

    return df, opp_df, opp_response, query


@app.cell
def _(df, mo):
    mo.md(f"### 📊 Found {len(df)} opportunities")
    return


@app.cell
def _(mo):
    mo.md("## 🎯 Top 5 Opportunity Details")
    return


@app.cell
def _(df, mo):
    # Generate detailed opportunity cards for top 5
    cards = []
    top_5_opps = df.head(5) if len(df) >= 5 else df

    for idx, opp_row in top_5_opps.iterrows():
        # Extract key info
        title = opp_row.get('title', 'N/A')
        score = opp_row.get('final_score', 0)
        sector = opp_row.get('sector', 'N/A')
        content = opp_row.get('content', '')[:500]  # First 500 chars
        problem_kw = opp_row.get('problem_keywords', 'N/A')
        solution = opp_row.get('solution_mentions', 'N/A')
        upvotes = opp_row.get('upvotes', 0)
        comments = opp_row.get('comments_count', 0)

        # Extract AI insights
        app_concept = opp_row.get('app_concept', 'N/A')
        core_functions = opp_row.get('core_functions', [])
        growth_justification = opp_row.get('growth_justification', 'N/A')

        # Format core functions as list
        if core_functions and isinstance(core_functions, list):
            functions_list = '\n'.join([f"- {func}" for func in core_functions[:3]])
        else:
            functions_list = "- N/A"

        # Build card content
        card_md = f"""
---

### #{idx+1}: {title}

**Score:** {score:.1f}/100 | **Sector:** {sector} | 👍 {upvotes} | 💬 {comments}

**Problem Keywords:** {problem_kw}

**Solution Mentions:** {solution}

---

### 💡 AI-Generated Insights

**App Concept:** {app_concept}

**Core Functions:**
{functions_list}

**Growth Justification:**
{growth_justification}

---

**Key Metrics:**
- Market Demand: {opp_row.get('market_demand', 0):.1f}/100
- Pain Intensity: {opp_row.get('pain_intensity', 0):.1f}/100
- Monetization: {opp_row.get('monetization_potential', 0):.1f}/100
- Simplicity: {opp_row.get('simplicity_score', 0):.1f}/100

**Content Preview:**
{content}...
"""
        cards.append(mo.md(card_md))

    mo.vstack(cards) if cards else mo.md("No opportunities found")
    return cards, top_5_opps


@app.cell
def _(df, mo):
    # Display dataframe with key columns including AI insights
    display_df = df[[
        "title", "sector", "final_score", "app_concept",
        "market_demand", "pain_intensity", "monetization_potential", "priority"
    ]] if len(df) > 0 else df

    mo.ui.table(display_df, selection=None)
    return (display_df,)


@app.cell
def _(mo):
    mo.md("## 📈 Score Distribution")
    return


@app.cell
def _(alt, df):
    # Score distribution chart
    score_chart = alt.Chart(df).mark_bar().encode(
        x=alt.X("final_score:Q", bin=alt.Bin(step=5), title="Final Score"),
        y=alt.Y("count()", title="Count"),
        color=alt.Color("sector:N", title="Sector")
    ).properties(width=600, height=300)

    score_chart
    return (score_chart,)


@app.cell
def _(mo):
    mo.md("## 🎯 Top Opportunities by Sector")
    return


@app.cell
def _(alt, df):
    # Sector comparison
    sector_chart = alt.Chart(df).mark_bar().encode(
        y=alt.Y("sector:N", title="Sector", sort="-x"),
        x=alt.X("mean(final_score):Q", title="Average Score"),
        color=alt.Color("sector:N", legend=None)
    ).properties(width=600, height=300)

    sector_chart
    return (sector_chart,)


@app.cell
def _(mo):
    mo.md("## 🔍 Dimension Breakdown (Top 10)")
    return


@app.cell
def _(alt, df, pd):
    # Dimension radar/breakdown for top 10
    top_10_dims = df.head(10) if len(df) >= 10 else df

    dimensions = ["market_demand", "pain_intensity", "monetization_potential",
                  "market_gap", "technical_feasibility", "simplicity_score"]

    dimension_data = []
    for _, dim_row in top_10_dims.iterrows():
        for dim in dimensions:
            dimension_data.append({
                "title": dim_row["title"][:40] + "...",
                "dimension": dim.replace("_", " ").title(),
                "score": dim_row[dim]
            })

    dim_df = pd.DataFrame(dimension_data)

    dimension_chart = alt.Chart(dim_df).mark_bar().encode(
        x=alt.X("score:Q", title="Score", scale=alt.Scale(domain=[0, 100])),
        y=alt.Y("dimension:N", title="Dimension"),
        color=alt.Color("dimension:N", legend=None),
        row=alt.Row("title:N", title="Opportunity")
    ).properties(width=500, height=80)

    dimension_chart
    return dim_df, dimension_chart, dimension_data, dimensions, top_10_dims


@app.cell
def _(mo):
    mo.md("## 📋 Export Data")
    return


@app.cell
def _(df, mo):
    # Export button
    csv_data = df.to_csv(index=False)

    mo.download(
        data=csv_data.encode(),
        filename="top_opportunities.csv",
        label="Download CSV"
    )
    return (csv_data,)


if __name__ == "__main__":
    app.run()
