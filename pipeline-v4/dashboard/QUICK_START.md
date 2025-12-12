# Dashboard Quick Start Guide

Get up and running with the RedditHarbor Dashboard in 5 minutes.

## Installation

```bash
# 1. Navigate to pipeline-v4 directory
cd /path/to/redditharbor-core-functions-fix/pipeline-v4

# 2. Install dependencies (if not already installed)
pip install streamlit pandas

# Or with uv
uv pip install streamlit pandas

# 3. Verify database connection
python database.py
```

## Running the Dashboard

### Method 1: Quick Start Script (Recommended)

```bash
./run_dashboard.sh
```

This script will:
- Check dependencies
- Test database connection
- Launch the dashboard
- Display the access URL

### Method 2: Direct Streamlit Command

```bash
streamlit run dashboard/app.py
```

### Method 3: Python Module

```bash
python -m streamlit run dashboard/app.py
```

## First Time Setup

1. **Configure Database:**
   - Ensure `.env` or `.env.local` has `DATABASE_URL` set
   - Example: `DATABASE_URL=postgresql://user:pass@localhost:5432/db`

2. **Verify Data:**
   ```bash
   python -c "from database import get_db_session; from models.analysis import Opportunity; from sqlmodel import select, func; session = next(get_db_session()); print(f'Found {session.exec(select(func.count(Opportunity.id))).one()} opportunities')"
   ```

3. **Launch Dashboard:**
   ```bash
   ./run_dashboard.sh
   ```

4. **Access Dashboard:**
   - Open browser to `http://localhost:8501`
   - Use sidebar to navigate between pages

## Quick Tour

### Home Page
- Shows quick stats and quarterly progress
- Displays total opportunities and high-scoring count
- Progress bar for 50 opportunity target

### Overview Page
- Browse all opportunities in a table
- Use filters in sidebar:
  - Score range (default: 70-100)
  - Subreddit selection
  - Function count (1-3 compliance)
  - Date range (optional)
- Sort by score, WTP, date, or subreddit
- Export to CSV or JSON

### Detailed View Page
- Select an opportunity from dropdown
- View complete details in tabs:
  - App Idea (title, concept, functions, audience)
  - Metrics (market demand, pain intensity, etc.)
  - Analysis (source info, quality, spam check)
  - Pain Points (all identified pains)
  - Raw Data (full JSON with export)

### Comparison Page
- Select 2-3 opportunities to compare
- Side-by-side layout
- Highlights differences
- Shows compliance status
- Provides recommendation
- Export comparison as CSV/JSON

## Common Tasks

### Find High-Scoring Opportunities
1. Go to Overview page
2. Ensure "Minimum Score" is set to 70+
3. Sort by "Final Score" descending
4. Review top results

### Check Function Compliance
1. Go to Overview page
2. Look at "Function Compliance" metric
3. Filter by "Core Functions Count" (1, 2, 3)
4. Review "Functions" column in table

### Compare Top 3 Opportunities
1. Go to Comparison page
2. Select 3 highest-scoring opportunities
3. Review side-by-side details
4. Check recommendation at bottom
5. Export comparison if needed

### Export Data
1. Go to Overview page
2. Apply desired filters
3. Scroll to "Export Data" section
4. Click "Download as CSV" or "Download as JSON"

### View Opportunity Details
1. Note the opportunity ID from Overview table
2. Go to Detailed View page
3. Select the opportunity from dropdown
4. Explore tabs for complete information

## Troubleshooting

### "No opportunities found"
- Check database connection
- Verify opportunities table has data
- Adjust filters (lower minimum score)

### "Error loading dashboard data"
- Verify DATABASE_URL in .env
- Test connection: `python database.py`
- Check PostgreSQL is running

### Dashboard won't start
- Verify streamlit installed: `pip list | grep streamlit`
- Check port 8501 is available: `lsof -i :8501`
- Try alternative port: `streamlit run dashboard/app.py --server.port 8502`

### Import errors
- Ensure running from pipeline-v4 directory
- Check Python path includes project root
- Reinstall dependencies: `pip install -r requirements.txt`

## Keyboard Shortcuts

- `Ctrl+C` - Stop dashboard (in terminal)
- `R` - Rerun dashboard (in browser)
- `C` - Clear cache (in browser menu)
- `?` - Show keyboard shortcuts (in browser)

## Tips

1. **Performance:** Use high-scoring filter (70+) for faster loading
2. **Comparison:** Compare opportunities with similar scores for better insights
3. **Export:** Export filtered results before changing filters
4. **Navigation:** Use browser back button to return to previous page state
5. **Refresh:** Dashboard auto-refreshes when code changes (development mode)

## Next Steps

- Read full [README.md](README.md) for detailed documentation
- Explore all three pages to understand available features
- Customize filters to match your research criteria
- Export data for further analysis in other tools

## Support

For more help:
- Check [README.md](README.md) for detailed documentation
- Review `models/analysis.py` for data schema
- Check `database.py` for connection details
- Review Streamlit logs in terminal for errors

## Version

Quick Start Guide Version: 1.0.0
Dashboard Version: 1.0.0
Last Updated: 2025-12-12
