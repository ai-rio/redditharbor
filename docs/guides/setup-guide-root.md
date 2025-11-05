# RedditHarbor - Environment Setup Guide

## Quick Start with Virtual Environment

### 1. Create and Activate Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate venv (Linux/macOS)
source venv/bin/activate

# Activate venv (Windows)
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Install python-dotenv for environment variable management
pip install python-dotenv

# Install additional dependencies for the marimo integration
pip install marimo pandas altair supabase tqdm requests
```

### 3. Configure Environment Variables

Edit `.env.local` in the project root with your credentials:

```bash
# Supabase Configuration (Local Development)
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_KEY=your_supabase_anon_key_here

# MiniMax API Configuration (for generating insights)
# Sign up at https://api.minimax.chat/
MINIMAX_API_KEY=your_minimax_api_key_here
MINIMAX_GROUP_ID=your_minimax_group_id_here
```

### 4. Start Supabase (if not already running)

```bash
# Check Supabase status
supabase status

# Start Supabase (if needed)
supabase start
```

### 5. Run the Scripts

```bash
# Generate insights for top opportunities
python scripts/generate_opportunity_insights.py

# Run batch opportunity scoring (process all submissions)
python scripts/batch_opportunity_scoring.py

# Test the setup
python scripts/test_batch_scoring.py
```

### 6. Launch Marimo Dashboard

```bash
# Start the dashboard
marimo run marimo_notebooks/top_contenders_dashboard.py --host 0.0.0.0 --port 8895

# Or with venv activated
marimo run marimo_notebooks/top_contenders_dashboard.py --port 8895
```

## What Each Script Does

### generate_opportunity_insights.py
- Fetches top 20 scored opportunities from database
- Uses MiniMax API to generate AI-powered insights
- Adds app concepts, core functions, and growth justification to each opportunity
- Updates the database with generated insights

### batch_opportunity_scoring.py
- Processes all 6,127 Reddit submissions
- Scores each using 6-dimensional methodology
- Stores results in `opportunity_analysis` table
- Takes ~18-20 minutes to complete

### top_contenders_dashboard.py
- Interactive web dashboard for exploring opportunities
- Filter by sector, score ranges, Top N
- Visualize score distributions and dimension breakdowns
- Export results as CSV/JSON

## Environment Variables Reference

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `SUPABASE_URL` | Supabase project URL | Yes | `http://127.0.0.1:54321` |
| `SUPABASE_KEY` | Supabase anonymous key | Yes | `eyJ...` |
| `MINIMAX_API_KEY` | MiniMax API key | Yes (for insights) | `eyJ...` |
| `MINIMAX_GROUP_ID` | MiniMax group ID | Yes (for insights) | `12345` |

## Troubleshooting

### python-dotenv not found
```bash
pip install python-dotenv
```

### Supabase connection error
1. Check Supabase is running: `supabase status`
2. Start if needed: `supabase start`
3. Verify credentials in `.env.local`

### MiniMax API errors
1. Verify API key and Group ID in `.env.local`
2. Check API limits at https://api.minimax.chat/
3. Ensure billing is set up

### Import errors
1. Ensure venv is activated: `source venv/bin/activate`
2. Install all dependencies: `pip install -r requirements.txt`
3. Check Python path includes project root

## File Structure

```
/home/carlos/projects/redditharbor/
├── .env.local              # Environment variables (git-ignored)
├── venv/                   # Virtual environment
├── scripts/
│   ├── generate_opportunity_insights.py
│   ├── batch_opportunity_scoring.py
│   └── test_batch_scoring.py
├── marimo_notebooks/
│   └── top_contenders_dashboard.py
├── supabase/
│   └── migrations/
│       ├── 20251105000000_create_opportunity_analysis_table.sql
│       └── 20251105010000_add_opportunity_insights.sql
└── docs/
    └── guides/
        ├── batch-opportunity-scoring-guide.md
        └── subagent-opportunity-scoring-guide.md
```

## Deactivate Virtual Environment

```bash
deactivate
```
