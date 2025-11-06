# RedditHarbor Main Dashboard Guide

## Overview

The unified marimo dashboard for discovering AI-powered app development opportunities from Reddit data.

## Running the Dashboard

```bash
# Start dashboard
marimo run marimo_notebooks/main_dashboard.py --port 8895

# Access at http://localhost:8895
```

## Features

### Two-Tier Display

**Confirmed Opportunities**
- 20 opportunities with full AI analysis
- App concept, core functions, growth justification
- Ready for evaluation

**High-Scoring Candidates**
- Submissions scoring ≥70 without AI analysis yet
- Can trigger AI analysis on demand

### View Modes

**All Mode (Default)**
- Card-based list of all opportunities
- Sorted by score (highest first)
- Filter by priority tier

**By Sector Mode**
- Table view for side-by-side comparison
- Select sector from dropdown
- Shows sector statistics

### AI Insights Panel

- Displays when opportunity is selected
- Shows full AI analysis
- Fixed position (no scrolling)

### Processing Controls

- Analyze Top 50 (~5 min, $0.005)
- Analyze All High Priority (~1 hr, $0.61)
- Custom count option

## Usage Tips

1. Start with "All" mode to see best opportunities globally
2. Use priority filters to focus on High (85+) opportunities
3. Switch to "By Sector" to compare similar opportunities
4. Click opportunity to view full AI insights
5. Use processing controls to analyze more submissions

## Troubleshooting

**No data showing:**
- Check Supabase: `supabase status`
- Verify data exists in Supabase Studio
- Run batch scoring: `python scripts/batch_opportunity_scoring.py`

**Database connection failed:**
- Ensure Supabase is running on port 54322
- Check credentials in config

**Processing fails:**
- Verify OPENROUTER_API_KEY is set
- Check script exists: `scripts/generate_opportunity_insights_openrouter.py`
