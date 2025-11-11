import marimo as mo

app = marimo.App()

@app.cell
def hello():
    mo.md("# 🚀 RedditHarbor Marimo Demo")
    mo.md("Welcome to the RedditHarbor interactive dashboard demo!")

@app.cell
def interactive_controls():
    subreddit = mo.ui.dropdown(
        options=['python', 'technology', 'programming', 'startups'],
        value='python',
        label='Select Subreddit'
    )

    metric = mo.ui.radio(
        options=['posts', 'comments', 'engagement'],
        value='posts',
        label='Show Metric'
    )

    return subreddit, metric

@app.cell
def show_selections(subreddit, metric):
    mo.md(f"### Selected: r/{subreddit.value} - {metric.value}")

    if subreddit.value == 'python':
        mo.md("🐍 **Python Community Stats:**")
        mo.md("- 15.2M members")
        mo.md("- 2.3K online now")
        mo.md("- Hot: Python 3.12 features")
    elif subreddit.value == 'technology':
        mo.md("💻 **Technology Community Stats:**")
        mo.md("- 14.8M members")
        mo.md("- 3.1K online now")
        mo.md("- Hot: AI breakthrough news")
    elif subreddit.value == 'programming':
        mo.md("⌨️ **Programming Community Stats:**")
        mo.md("- 4.2M members")
        mo.md("- 890 online now")
        mo.md("- Hot: Best practices 2024")
    else:
        mo.md("🚀 **Startups Community Stats:**")
        mo.md("- 2.1M members")
        mo.md("- 450 online now")
        mo.md("- Hot: YC new batch")

@app.cell
def interactive_chart():
    import altair as alt
    import pandas as pd

    data = pd.DataFrame({
        'metric': ['Posts', 'Comments', 'Engagement', 'Activity'],
        'value': [1200, 3400, 890, 560],
        'change': [+12, +8, +15, -3]
    })

    chart = alt.Chart(data).mark_bar().encode(
        x='metric:N',
        y='value:Q',
        color=alt.condition(
            alt.datum.change > 0,
            alt.value('#FF6B35'),  # CueTimer orange
            alt.value('#004E89')   # CueTimer blue
        ),
        tooltip=['metric', 'value', 'change']
    ).properties(
        title='RedditHarbor Community Metrics',
        width=600,
        height=400
    )

    mo.altair(chart)

if __name__ == "__main__":
    app.run()
