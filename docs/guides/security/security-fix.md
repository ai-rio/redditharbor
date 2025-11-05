# Security Fix: Remove Hardcoded Credentials

**Severity:** CRITICAL  
**Date:** 2025-11-05  
**Status:** IN PROGRESS

## Issue Summary

Multiple files in the RedditHarbor codebase contain hardcoded API keys and credentials, violating security best practices and creating potential security vulnerabilities.

## Files Requiring Fix

### 1. `/scripts/generate_opportunity_insights.py`
**Problem:** Line 29 has hardcoded Supabase anon key as fallback
```python
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
```

**Fix:** Remove fallback value, require environment variable

### 2. `/config/settings.py`
**Problem:** Lines 5, 6, 11 have hardcoded Reddit and Supabase keys
```python
REDDIT_PUBLIC = "jEAmLlbzr0TvxbR1W0ziBQ"
REDDIT_SECRET = "g2r7vhtAB_kEmCeGcXXEM_KIzDh8iQ"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Fix:** Use environment variables

### 3. `/marimo_notebooks/top_contenders_dashboard.py`
**Problem:** Line has hardcoded Supabase anon key as fallback

**Fix:** Remove fallback value

### 4. Other affected files:
- `/scripts/analyze_real_database_data.py`
- `/marimo_notebooks/config.py`
- `/worktrees/feature-streamlit/config/settings.py`

## Solution

### Option A: Environment Variables Only
Remove all hardcoded fallbacks, require .env files

### Option B: Config Module Pattern
Create a config module that loads from .env and provides to other modules

## Recommendation

Follow the pattern already partially implemented in the codebase:
1. Use .env.local for local development
2. Load via python-dotenv
3. Provide sensible defaults that are clearly placeholders
4. Never use real credentials as fallbacks

## Next Steps

1. Fix scripts/generate_opportunity_insights.py
2. Fix config/settings.py
3. Fix marimo_notebooks/top_contenders_dashboard.py
4. Review and fix remaining files
5. Update documentation
