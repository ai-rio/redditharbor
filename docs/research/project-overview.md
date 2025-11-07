# RedditHarbor - Project Overview

## What It Is
Reddit data collection and research platform that identifies monetizable app opportunities from Reddit discussions using AI analysis.

## Tech Stack
- **Database**: Supabase (local dev: port 54321, SQL: port 54322, Studio: port 54323)
- **Language**: Python
- **AI**: OpenRouter (anthropic/claude-haiku-4.5) for opportunity analysis
- **Collection**: Reddit API with PII anonymization

## Core Database Tables
```
redditor    - Reddit user profiles
submission  - Posts and submissions
comment     - Comments and replies hierarchy
opportunity_analysis - AI-scored opportunities
```

## Essential Commands
```bash
# Start Docker services (Supabase)
sudo dockerd > /dev/null 2>&1 &

# Run scripts
source .venv/bin/activate && python scripts/test_commercial_insights.py
source .venv/bin/activate && python scripts/generate_opportunity_insights_openrouter.py --mode database --limit 5

# Code quality
ruff check . && ruff format .
```

## AI Insight Generation
- **Script**: `scripts/generate_opportunity_insights_openrouter.py`
- **Purpose**: Analyze Reddit posts to identify 1-3 function app opportunities
- **Output**: `app_concept`, `core_functions`, `growth_justification`
- **Approach**: Problem-First (identify problem → validate → design app)

## Current Data Status
- 15 redditors, 285 submissions
- Active subreddits: r/Python, r/technology, r/programming, r/startups, r/smallbusiness, r/SaaS
- 0 valid AI insights generated (expected - data lacks real user problems)

## SOLUTION IMPLEMENTED (Problem-First Approach)
**Files Modified:**
- `scripts/generate_opportunity_insights_openrouter.py` - Updated to problem-first prompt
- Lowered monetization threshold to 5 (from 25)
- Enhanced validation to handle problem-first format
- Added rejection reason handling

**What Was Fixed:**
1. ❌ Old: "App-First" approach (force posts into apps)
2. ✅ New: "Problem-First" approach (find problems → design apps)
3. ❌ Old: 0% success rate (too strict)
4. ✅ New: AI correctly rejects non-problems
5. ❌ Old: Comments query bug (content → body)
6. ✅ Fixed: All database queries work correctly

**How It Works Now:**
1. Read Reddit post
2. Identify underlying problem
3. Validate problem is real and painful
4. Design simplest 1-3 function app
5. Cite Reddit evidence
6. Reject if not a real solvable problem

## Key Files
- `/docs/README.md` - Comprehensive documentation
- `/docs/methodology/monetizable-app-research-methodology.md` - Full methodology
- `scripts/generate_opportunity_insights_openrouter.py` - AI generation script (UPDATED)
- `config/settings.py` - Configuration
