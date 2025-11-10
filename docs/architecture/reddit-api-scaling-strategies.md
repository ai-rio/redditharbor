# Reddit API Scaling Strategies for Data Collection

**Goal:** Scale from 594 to 1000+ posts to test threshold 70+  
**Date:** 2025-11-09

---

## Current State Analysis

**Problem:** Only 594 submissions after scale-up attempt
- 7 subreddits × 200 limit = 1,400 potential posts
- Actual collected: 473 new posts (34% of potential)
- Problem filter rate: ~10-20% (most posts don't contain problem keywords)

**Root Cause:** Reddit API returns maximum 100 posts per listing request, but we were only requesting 200-300 posts per subreddit with high filter rate

---

## Reddit API Capabilities (From PRAW Documentation)

### 1. Listing Types Available
```python
subreddit.new(limit=100)      # Most recent posts
subreddit.hot(limit=100)      # Popular posts
subreddit.top(time_filter)    # Top posts with time filters
subreddit.rising(limit=100)   # Posts gaining traction
subreddit.gilded(limit=100)   # Posts with gold awards
```

### 2. Time Filters for Top Posts
- `hour` - Top posts from last hour
- `day` - Top posts from last day
- `week` - Top posts from last week
- `month` - Top posts from last month
- `year` - Top posts from last year
- `all` - Top posts of all time

### 3. Post Limits
- **Default:** 100 posts per listing
- **Maximum:** Can set `limit=None` to get all available
- **Pagination:** Automatic with ListingGenerator

### 4. Search Capabilities
```python
# Search for problem-related posts
subreddit.search("frustrated OR struggling OR wish there was", limit=100)

# Search with time filters
subreddit.search("problem", time_filter="week", limit=100)
```

### 5. Multi-Subreddit Queries
```python
# Query multiple subreddits at once
reddit.subreddit("startups+entrepreneur+SaaS").top(limit=100)
```

---

## Scaling Strategies (In Order of Recommendation)

### Strategy 1: Increase Limits Per Subreddit ⭐ RECOMMENDED

**Current:** 200-300 posts per subreddit  
**New:** 500-1000 posts per subreddit

```python
# Instead of this
collect_problem_posts(
    subreddits=["startups", "entrepreneur"],
    limit=200,
    sort_type="top"
)

# Do this
collect_problem_posts(
    subreddits=["startups", "entrepreneur"],
    limit=1000,  # Increased 5x
    sort_type="top"
)
```

**Expected Results:**
- 7 subreddits × 1000 = 7,000 potential posts
- 20% filter rate = ~1,400 problem posts
- **Target: ACHIEVED** ✅

---

### Strategy 2: Expand Subreddit List

**Current:** 7 subreddits  
**New:** 20-30 subreddits

```python
ULTRA_PREMIUM_SUBREDDITS = [
    # Original 7
    "venturecapital", "financialindependence", "startups",
    "investing", "realestateinvesting", "business", "SaaS",
    
    # Additional 15
    "smallbusiness", "b2bmarketing", "entrepreneur",
    "freelance", "consulting", "digitalmarketing",
    "ecommerce", "webdev", "socialmedia",
    "projectmanagement", "productivity", "contractors",
    "accounting", "marketing", "sales"
]
```

**Expected Results:**
- 22 subreddits × 500 = 11,000 potential posts
- 20% filter rate = ~2,200 problem posts
- **Target: EXCEEDED** 🚀

---

### Strategy 3: Multiple Sort Types Per Subreddit

**Current:** One sort type (e.g., only "top")  
**New:** Multiple sort types per subreddit

```python
# For each subreddit, collect:
posts = []
posts += collect_problem_posts([sub], limit=100, sort_type="new")
posts += collect_problem_posts([sub], limit=100, sort_type="hot")
posts += collect_problem_posts([sub], limit=100, sort_type="top", time_filter="day")
posts += collect_problem_posts([sub], limit=100, sort_type="top", time_filter="week")
posts += collect_problem_posts([sub], limit=100, sort_type="top", time_filter="month")
posts += collect_problem_posts([sub], limit=100, sort_type="top", time_filter="year")
posts += collect_problem_posts([sub], limit=100, sort_type="rising")
```

**Expected Results:**
- 7 sort types × 100 posts × 7 subreddits = 4,900 potential posts
- 20% filter rate = ~980 problem posts
- **Target: ACHIEVED** ✅

---

### Strategy 4: Use `limit=None`

**Current:** `limit=200` (fixed number)  
**New:** `limit=None` (all available)

```python
# Get ALL top posts (not just first 100)
collect_problem_posts(
    subreddits=["startups"],
    limit=None,  # Get all available
    sort_type="top"
)
```

**Expected Results:**
- Varies by subreddit (could be 1000-10000+ posts)
- **Target: EXCEEDED** 🚀

**Caveat:** May hit rate limits on large subreddits

---

### Strategy 5: Search-Based Collection

**Current:** Collect all posts, then filter by keywords  
**New:** Search for problem keywords directly

```python
# Search for problem-related posts
problem_queries = [
    "frustrated OR struggling OR annoying",
    "wish there was OR looking for OR need tool",
    "hard OR difficult OR time consuming",
    "problem OR issue OR pain point"
]

for query in problem_queries:
    posts += collect_problem_posts(
        subreddits=[subreddit],
        limit=100,
        sort_type="search",
        search_query=query  # Would need to add this parameter
    )
```

**Expected Results:**
- More targeted collection (higher problem filter rate)
- **Target: EFFICIENT** ⚡

---

### Strategy 6: Time-Series Collection

**Current:** Snapshot collection  
**New:** Collect top posts from different time periods

```python
# For each subreddit, get top posts from different periods
time_filters = ["day", "week", "month", "year", "all"]

for time_filter in time_filters:
    posts += collect_problem_posts(
        subreddits=[subreddit],
        limit=200,
        sort_type="top",
        time_filter=time_filter
    )
```

**Expected Results:**
- 5 time periods × 200 posts × 7 subreddits = 7,000 potential posts
- **Target: EXCEEDED** 🚀

---

## Implementation Scripts Created

### Script 1: Simple Scale-Up
**File:** `scripts/collect_1000_plus_simple_scale.py`

```bash
# 22 subreddits × 1000 limit = 22,000 potential posts
# Expected: 2,000-4,000 problem posts
python3 scripts/collect_1000_plus_simple_scale.py
```

**Strategy:**
- ✅ Increase limits: 200 → 1000 per subreddit
- ✅ Expand subreddits: 7 → 22
- ✅ Use "top" sort type for quality
- ⚠️  Single sort type only

---

### Script 2: Massive Scale
**File:** `scripts/collect_massive_scale_for_70_plus.py`

```bash
# Multiple sort types × 20 subreddits
# Expected: 10,000-15,000 problem posts
python3 scripts/collect_massive_scale_for_70_plus.py
```

**Strategy:**
- ✅ Multiple sort types: new, hot, top[time filters], rising
- ✅ Time-filtered top posts: day, week, month, year, all
- ✅ 20+ ultra-premium subreddits
- ✅ 500+ limit per sort type
- ⚠️  More complex, may hit rate limits

---

### Script 3: Enhanced Collection Function
**File:** `scripts/collect_enhanced_multi_sort.py` (not created yet)

**Strategy:**
- ✅ Modify `collect_problem_posts()` to support:
  - `time_filter` parameter
  - `search_query` parameter
  - Multiple sort types in one call
- ✅ More efficient API usage
- ⚠️  Requires code changes to core function

---

## Rate Limits & Best Practices

### Reddit API Rate Limits
- **60 requests per minute** for authenticated apps
- **100 requests per minute** for some endpoints
- **Pagination:** Maximum 1000 items per query

### Best Practices for Scale

1. **Use Multiple Sort Types**
   ```python
   # Good: Distribute requests across sort types
   new_posts = subreddit.new(limit=100)
   top_week = subreddit.top(time_filter="week", limit=100)
   ```

2. **Batch Subreddit Requests**
   ```python
   # Good: Query multiple subreddits at once
   reddit.subreddit("startups+entrepreneur").top(limit=100)
   ```

3. **Respect Rate Limits**
   ```python
   # Add delays for large collections
   import time
   time.sleep(1)  # 1 second between requests
   ```

4. **Use Search for Targeted Collection**
   ```python
   # More efficient than filtering after collection
   results = subreddit.search("frustrated OR struggling", limit=100)
   ```

5. **Handle Errors Gracefully**
   ```python
   try:
       posts = collect_problem_posts([subreddit], limit=1000)
   except praw.exceptions.RedditAPIException as e:
       print(f"Rate limited: {e}")
       time.sleep(60)  # Wait 1 minute
   ```

---

## Recommendation for Threshold 70+ Testing

### Option A: Quick Scale (Recommended for Testing)
```bash
# Simple, fast, uses existing code
python3 scripts/collect_1000_plus_simple_scale.py
```
- **Expected:** 1,000-2,000 posts
- **Time:** 10-20 minutes
- **Success Probability:** High for finding 60+ scores

### Option B: Massive Scale (For Research)
```bash
# Comprehensive, maximum data
python3 scripts/collect_massive_scale_for_70_plus.py
```
- **Expected:** 5,000-10,000 posts
- **Time:** 30-60 minutes
- **Success Probability:** Very high for finding 70+ scores

### Option C: Hybrid Approach
```python
# 1. Run simple scale first
python3 scripts/collect_1000_plus_simple_scale.py

# 2. If no 70+ scores, run massive scale
python3 scripts/collect_massive_scale_for_70_plus.py
```

---

## Expected Outcomes

### With 1,000 Posts
- 40+ scores: ~20 opportunities (2%)
- 50+ scores: ~5 opportunities (0.5%)
- 60+ scores: ~1 opportunity (0.1%)
- **70+ scores:** Unlikely (0.01% or less)

### With 5,000 Posts
- 40+ scores: ~100 opportunities (2%)
- 50+ scores: ~25 opportunities (0.5%)
- 60+ scores: ~5 opportunities (0.1%)
- **70+ scores:** Possible (1-2 opportunities, 0.02%)

### With 10,000 Posts
- 40+ scores: ~200 opportunities (2%)
- 50+ scores: ~50 opportunities (0.5%)
- 60+ scores: ~10 opportunities (0.1%)
- **70+ scores:** Likely (2-5 opportunities, 0.02-0.05%)

---

## Conclusion

**For Threshold 70+ Testing:**
1. **Start with Simple Scale** (`scripts/collect_1000_plus_simple_scale.py`)
2. **If needed, use Massive Scale** (`scripts/collect_massive_scale_for_70_plus.py`)
3. **Expected:** Need 5,000-10,000 posts to find 70+ scores

**Key Insight:** The issue isn't the scoring methodology - 47.2 is likely the practical ceiling for Reddit data. To find 70+ scores, we need to scale to 10,000+ posts or explore non-Reddit data sources.

---

**Files Created:**
- `scripts/collect_1000_plus_simple_scale.py` - Quick scale to 1000+ posts
- `scripts/collect_massive_scale_for_70_plus.py` - Massive scale to 10,000+ posts
- `REDDIT_API_SCALING_STRATEGIES.md` - This document

**Next Steps:**
1. Run simple scale script
2. Test with threshold 70
3. If no results, run massive scale
4. Consider non-Reddit data sources for 70+ testing
