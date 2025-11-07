# RedditHarbor - Simple Workflow Guide

## Overview

This guide provides a streamlined 2-step workflow for collecting Reddit data and extracting monetizable app opportunities.

**Time commitment:** 10-15 minutes per week

## Prerequisites

- ✅ Docker running (for Supabase database)
- ✅ Python environment with uv/venv
- ✅ Reddit API credentials configured

## The 2-Step Workflow

### Step 1: Analyze Existing Data (5 minutes)

Your database already has 937 Reddit submissions. Run the analysis script to identify opportunities:

```bash
python scripts/analyze_real_database_data.py
```

**What it does:**
- Fetches submissions from your Supabase database
- Analyzes for pain points, solution seeking, and monetization signals
- Calculates opportunity scores (signal score × engagement multiplier)
- Outputs results to `generated/real_reddit_opportunity_analysis.json`

**Output:**
- Top 20 opportunities by score
- Subreddit rankings
- Business ideas extracted from discussions
- Market segment insights

### Step 2: View Insights Dashboard (1 minute)

Open the interactive dashboard to explore opportunities:

```bash
marimo run marimo_notebooks/simple_opportunity_dashboard.py
```

**What you'll see:**
1. **Problem Trends** - Top 10 problems by pain intensity
2. **App Ideas** - Business opportunities with monetization signals
3. **Subreddit Insights** - Which communities to monitor

**Interactive features:**
- Minimum score filter (adjust threshold)
- Subreddit filter (focus on specific communities)
- Sortable tables
- Visual charts with Plotly

## Optional: Collect Fresh Data

If you want to collect new Reddit data:

```bash
python scripts/collect_real_reddit_data.py
```

**Note:** You already have 937 submissions in your database. Only run this if you want fresh data from recent discussions.

## Understanding the Metrics

### Opportunity Score

Calculated from signals in Reddit posts/comments:

- **Pain Points** (weight: 4) - Frustration keywords like "terrible", "broken", "doesn't work"
- **Solution Seeking** (weight: 3) - Requests like "looking for", "recommendation", "alternative"
- **Monetization Signals** (weight: 5) - Payment indicators like "willing to pay", "subscription", "worth it"
- **App Keywords** (weight: 2) - Mentions of "app", "tool", "software", "platform"

**Formula:** `Opportunity Score = Signal Score × Engagement Multiplier`

Where:
- `Signal Score = (pain×4) + (solution×3) + (monetization×5) + (app×2)`
- `Engagement Multiplier = 1 + (upvotes/200) + (comments/100)`

### Priority Levels

- **HIGH PRIORITY** (score ≥ 100): Immediate development consideration
- **MEDIUM-HIGH** (50-99): Strong candidate with refinement
- **MEDIUM** (25-49): Viable but requires more validation
- **LOW** (10-24): Monitor for future development
- **NOT RECOMMENDED** (<10): Don't pursue currently

## What to Look For

### 1. High Pain + High Engagement
Problems that many people discuss with frustration = strong demand signal

### 2. Multiple Monetization Mentions
Users discussing pricing, subscriptions, willingness to pay = clear revenue path

### 3. Cross-Subreddit Patterns
Same problem appearing in multiple communities = broader market opportunity

### 4. Solution Gaps
Complaints about existing tools + feature requests = competitive advantage opportunities

## Weekly Routine (15 minutes)

**Monday morning:**
1. Run analysis script (5 min)
2. Open dashboard (1 min)
3. Review high-priority opportunities (5 min)
4. Note 1-2 ideas worth validating (2 min)
5. Add to your research backlog (2 min)

**Monthly review:**
- Collect fresh Reddit data
- Track trending problems over time
- Identify emerging vs. declining opportunities

## Files You Need to Know

### Active Files (Use These)

- `scripts/analyze_real_database_data.py` - Main analysis script
- `marimo_notebooks/simple_opportunity_dashboard.py` - Visualization dashboard
- `generated/real_reddit_opportunity_analysis.json` - Analysis output

### Configuration

- `config/settings.py` - Reddit API keys, Supabase connection
- `.env` - Environment variables (credentials)

### Documentation

- `docs/monetizable-app-research-methodology.md` - Full methodology (reference)
- `WORKFLOW.md` - This guide

### Archive (Ignore These for Now)

The `scripts/` directory has 30+ files. Most are experiments or alternatives. For the simple workflow, you only need `analyze_real_database_data.py`.

Consider moving others to `scripts/_archive/` to reduce clutter.

## Troubleshooting

### "No analysis data found"

**Problem:** Dashboard shows this message
**Solution:** Run `python scripts/analyze_real_database_data.py` first

### "No submissions found in database"

**Problem:** Analysis script can't find data
**Solution:**
1. Check Docker is running: `docker ps`
2. Check Supabase is accessible: `curl http://127.0.0.1:54321`
3. Collect data: `python scripts/collect_real_reddit_data.py`

### "Database connection failed"

**Problem:** Can't connect to Supabase
**Solution:**
1. Start Supabase: `supabase start`
2. Check connection URL in `config/settings.py`
3. Verify credentials in `.env`

### Empty visualizations in dashboard

**Problem:** Dashboard loads but shows no data
**Solution:** Lower the "Minimum Opportunity Score" filter (default: 25)

## Advanced: Customizing the Analysis

### Change scoring weights

Edit `scripts/analyze_real_database_data.py`, line 130-133:

```python
pain_weight = 4          # Increase for pain-focused opportunities
solution_weight = 3      # Increase for solution-seeking patterns
monetization_weight = 5  # Increase for revenue-focused opportunities
app_weight = 2           # Increase for digital/software opportunities
```

### Add custom keywords

Edit `analyze_opportunity_signals()` function, line 89-116:

```python
opportunity_keywords = {
    "pain_points": [...],       # Add frustration keywords
    "solution_seeking": [...],  # Add help-seeking keywords
    "monetization_signals": [...], # Add payment keywords
    "app_keywords": [...]       # Add tech product keywords
}
```

### Target different subreddits

Edit `scripts/collect_real_reddit_data.py`, line 39-48 to change target communities.

## Next Steps

1. **Run the workflow** - Try it once to see the insights
2. **Validate opportunities** - Pick 1-2 high-scoring ideas and research them further
3. **Set up weekly routine** - Schedule 15 min every Monday
4. **Refine over time** - Adjust keywords and weights based on what works

## Support

- Check `docs/README.md` for comprehensive documentation
- Review `generated/real_reddit_opportunity_analysis.json` for raw data
- Adjust filters in dashboard to explore different opportunity types

---

**Remember:** The goal is actionable insights, not perfect analysis. Start simple, iterate based on what you discover.
