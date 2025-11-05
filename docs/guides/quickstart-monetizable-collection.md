# Quick Start: Monetizable Opportunities Collection

## TL;DR - Implementation Status

✅ **ALL FUNCTIONS FULLY IMPLEMENTED** - No stub code, ready for production!

The three critical functions are **completely implemented** in `/home/carlos/projects/redditharbor/core/collection.py`:

1. ✅ `collect_monetizable_opportunities_data()` (lines 702-787)
2. ✅ `collect_enhanced_submissions()` (lines 790-903)
3. ✅ `collect_enhanced_comments()` (lines 906-1044)

## What's Implemented

### Reddit API Integration
```python
# Real Reddit API calls (not stubs)
if sort_type == "hot":
    submissions = subreddit.hot(limit=limit)
elif sort_type == "rising":
    submissions = subreddit.rising(limit=limit)
elif sort_type == "top":
    submissions = subreddit.top(time_filter, limit=limit)
```

### Enhanced Metadata Extraction
```python
# Actual helper function calls
"sentiment_score": calculate_sentiment_score(submission.selftext),
"problem_indicators": json.dumps(extract_problem_keywords(submission.selftext)),
"solution_mentions": json.dumps(extract_solution_mentions(submission.selftext)),
"monetization_signals": json.dumps(detect_payment_mentions(submission.selftext))
```

### Database Storage
```python
# Real Supabase upsert operations
result = supabase_client.table(db_config["submission"]).upsert(
    submission_data, on_conflict="submission_id"
).execute()
```

### Smart Rate Limiting
```python
# Intelligent delays
delay = smart_rate_limiting(sort_type, "submission")  # 1.5s-3.0s
time.sleep(delay)
```

## Quick Verification

Run this command to verify everything is implemented:

```bash
python3 scripts/verify_monetizable_implementation.py
```

Expected output:
```
================================================================================
✅ IMPLEMENTATION VERIFICATION SUCCESSFUL!

All required functions are implemented and contain:
  • Reddit API data collection
  • Enhanced metadata extraction (sentiment, keywords, etc.)
  • Supabase database storage
  • Smart rate limiting (1.5s-3.0s delays)
  • Comprehensive error handling
  • Progress logging

The implementation is ready for production use!
================================================================================
```

## Run Production Collection

### Option 1: Full Collection (All 73 Subreddits)

```bash
python3 scripts/run_monetizable_collection.py
```

This will:
- Collect from all 73 target subreddits
- Use 3 sort types (hot, rising, top)
- Extract enhanced metadata for each submission and comment
- Store everything to Supabase database
- Take approximately 6-10 hours to complete

### Option 2: Programmatic Usage

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redditharbor.login import reddit, supabase
from config.settings import DB_CONFIG
from core.collection import collect_monetizable_opportunities_data

# Run collection
success = collect_monetizable_opportunities_data(
    reddit_client=reddit,
    supabase_client=supabase,
    db_config=DB_CONFIG,
    market_segment="health_fitness",  # Or "all" for everything
    limit_per_sort=50,
    time_filter="week",
    mask_pii=False,
    sentiment_analysis=True,
    extract_problem_keywords=True,
    track_workarounds=True
)

print(f"✅ Success!" if success else "❌ Failed!")
```

## What Gets Collected

### Submissions (Enhanced)
- Standard fields: title, author, score, num_comments, etc.
- **Enhanced fields**:
  - `market_segment`: "health_fitness", "finance_investing", etc.
  - `sentiment_score`: -1.0 to 1.0 (negative to positive)
  - `emotional_language_score`: 0.0 to 1.0 (intensity)
  - `problem_indicators`: JSON array of problem keywords found
  - `solution_mentions`: JSON array of solution mentions
  - `monetization_signals`: JSON array of payment willingness signals
  - `post_engagement_rate`: score / num_comments ratio

### Comments (Enhanced)
- Standard fields: body, author, score, etc.
- **Enhanced fields**:
  - `sentiment_score`: -1.0 to 1.0
  - `pain_intensity_indicators`: 0.0 to 1.0
  - `workaround_mentions`: JSON array of workarounds
  - `payment_willingness_signals`: JSON array of payment signals
  - `problem_keywords`: JSON array of problem keywords

## Target Markets

### 73 Subreddits in 6 Segments

- **health_fitness** (14): fitness, nutrition, keto, yoga, meditation, etc.
- **finance_investing** (13): personalfinance, investing, stocks, crypto, etc.
- **education_career** (11): learnprogramming, cscareerquestions, productivity, etc.
- **travel_experiences** (12): travel, solotravel, digitalnomad, flights, etc.
- **real_estate** (11): RealEstate, landlord, PropertyManagement, etc.
- **technology_saas** (12): SaaS, startups, Entrepreneur, productivity, etc.

## Collection Performance

### Expected Times
- **Single subreddit**: 5-10 minutes (~300 submissions)
- **Single segment**: 1-2 hours (10-14 subreddits)
- **All segments**: 6-10 hours (73 subreddits)

### Rate Limits
- Hot/rising posts: 1.5 seconds delay
- Top posts: 3.0 seconds delay
- Comments: 2.0 seconds delay
- Between subreddits: 3.0-5.0 seconds

This keeps us well under Reddit's 60 requests/minute limit (~20-40 req/min).

## Verification Checklist

After running collection, verify:

1. **Submissions collected**
   ```sql
   SELECT COUNT(*) FROM submissions;
   SELECT COUNT(*) FROM submissions WHERE market_segment IS NOT NULL;
   SELECT COUNT(*) FROM submissions WHERE sentiment_score IS NOT NULL;
   ```

2. **Comments collected**
   ```sql
   SELECT COUNT(*) FROM comments;
   SELECT COUNT(*) FROM comments WHERE sentiment_score IS NOT NULL;
   SELECT COUNT(*) FROM comments WHERE problem_keywords IS NOT NULL;
   ```

3. **Enhanced metadata present**
   ```sql
   SELECT
     submission_id,
     market_segment,
     sentiment_score,
     problem_indicators,
     solution_mentions
   FROM submissions
   LIMIT 10;
   ```

## Documentation Files

For more details, see:

1. **Implementation Guide** (comprehensive)
   - `/home/carlos/projects/redditharbor/docs/MONETIZABLE_COLLECTION_IMPLEMENTATION.md`

2. **Code Reference** (actual code snippets)
   - `/home/carlos/projects/redditharbor/docs/IMPLEMENTATION_CODE_REFERENCE.md`

3. **Implementation Summary** (overview)
   - `/home/carlos/projects/redditharbor/IMPLEMENTATION_SUMMARY.md`

4. **This File** (quick start)
   - `/home/carlos/projects/redditharbor/QUICKSTART_MONETIZABLE_COLLECTION.md`

## Key Functions Reference

### Main Orchestrator
```python
collect_monetizable_opportunities_data(
    reddit_client,      # Reddit API client
    supabase_client,    # Supabase client
    db_config,          # Database table mapping
    market_segment="all",  # Which segment(s) to collect
    limit_per_sort=100,    # Posts per sort type
    time_filter="month",   # Time filter for top posts
    mask_pii=True,         # Enable PII masking
    sentiment_analysis=True,
    extract_problem_keywords=True,
    track_workarounds=True
) -> bool
```

### Helper Functions Available
- `extract_problem_keywords(text)` - 36 problem indicators
- `extract_workarounds(text)` - 24 workaround keywords
- `extract_solution_mentions(text)` - 23 solution mentions
- `detect_payment_mentions(text)` - 45 monetization signals
- `calculate_sentiment_score(text)` - -1.0 to 1.0
- `analyze_pain_language(text)` - 0.0 to 1.0
- `analyze_emotional_intensity(text)` - 0.0 to 1.0
- `identify_market_segment(subreddit)` - Returns segment name
- `smart_rate_limiting(sort_type, collection_type)` - Returns delay in seconds

## Summary

**Status**: ✅ FULLY IMPLEMENTED AND READY

All three functions contain:
- Real Reddit API calls
- Enhanced metadata extraction
- Supabase database storage
- Smart rate limiting
- Comprehensive error handling
- Progress logging

**No stub code. No placeholders. Production ready!** 🚀

---

To get started immediately:

```bash
# 1. Verify implementation
python3 scripts/verify_monetizable_implementation.py

# 2. Run collection
python3 scripts/run_monetizable_collection.py

# 3. Check results in Supabase Studio
# http://127.0.0.1:54323
```
