# DLT Module Extension Quick Reference

**Purpose:** Fast lookup guide for implementing DLT extensions to unblock Phase 1 scripts
**Document Location:** docs/architecture/dlt-module-analysis.md (full analysis)

---

## At a Glance

| Component | Status | Priority | Effort |
|-----------|--------|----------|--------|
| core/dlt_collection.py (6 existing functions) | ✅ Ready | - | - |
| Extension 1.1: collect_post_comments() | ❌ Missing | 🔴 CRITICAL | 3-4 hrs |
| Extension 1.2: enrich_posts_with_sector() | ❌ Missing | 🟡 HIGH | 2 hrs |
| Extension 1.3: load_opportunity_insights() | ❌ Missing | 🟡 MEDIUM | 2 hrs |
| Extension 1.4: Cursor tracking | ❌ Missing | 🟡 MEDIUM | 2 hrs |

---

## 6 Existing Functions in core/dlt_collection.py

### Quick Function Reference

1. **get_reddit_client()** → praw.Reddit
   - Initializes Reddit API client from .env

2. **contains_problem_keywords(text, min_keywords=1)** → bool
   - Filters by problem keywords (33 keywords from core.collection)

3. **collect_problem_posts(subreddits, limit=50, sort_type="new", test_mode=False)** → List[Dict]
   - Main collection function
   - Returns: 12 fields per post (id, title, selftext, author, created_utc, subreddit, score, url, num_comments, problem_keywords_found, problem_keyword_count)

4. **create_dlt_pipeline()** → dlt.Pipeline
   - Creates Supabase/PostgreSQL destination pipeline
   - Credentials from .dlt/secrets.toml

5. **load_to_supabase(problem_posts, write_mode="merge")** → bool
   - Loads posts to "submissions" table
   - Merge write disposition prevents duplicates
   - Primary key: "id"

6. **main()** - CLI entry point
   - Arguments: --subreddits, --limit, --sort, --test

---

## Phase 1 Scripts Blocking Status

### Script 1: batch_opportunity_scoring.py
- **Current State:** Reads from Supabase, scores with AI, saves to opportunity_analysis
- **Blocker:** ❌ NONE (uses direct Supabase client)
- **DLT Need:** Optional Extension 1.3 (insights DLT writer)
- **Can Start:** ✅ YES (right now if not using DLT for insights)

### Script 2: final_system_test.py
- **Current State:** Validates end-to-end pipeline with synthetic data
- **Blocker:** ❌ NONE
- **DLT Need:** None (uses test data)
- **Can Start:** ✅ YES (right now)

### Script 3: collect_commercial_data.py
- **Current State:** Imports from redditharbor.dock.pipeline (EXTERNAL)
- **Blocker:** 🔴 CRITICAL - redditharbor.dock.pipeline NOT in project
- **DLT Need:** Extension 1.1 (comment collection)
- **Can Start:** ❌ NO - needs Extension 1.1 first

---

## Extension Implementation Map

### Extension 1.1: collect_post_comments() (CRITICAL)

**Location:** Add to core/dlt_collection.py after collect_problem_posts()

**Signature:**
```python
def collect_post_comments(
    reddit_client: praw.Reddit,
    submission_ids: List[str],
    limit: int = 20,
    test_mode: bool = False
) -> List[Dict[str, Any]]:
    """Collect comments from specified submissions."""
```

**Effort:** 3-4 hours
**Blocks:** collect_commercial_data.py, full_scale_collection.py, all Phase 2+

**Implementation Checklist:**
- [ ] Handle nested comment structure
- [ ] Skip deleted/removed comments
- [ ] Extract: id, submission_id, author, body, score, created_utc, subreddit
- [ ] Apply problem keyword filtering
- [ ] Test with 5-10 submissions
- [ ] Error handling for API failures

**Return Format:**
```python
[{
    "id": "comment_id",
    "submission_id": "parent_submission_id",
    "author": "username",
    "body": "comment text",
    "score": 42,
    "created_utc": 1704067200,
    "subreddit": "subreddit_name",
    "has_problem_keywords": bool,
    "problem_keywords_found": [list]
}]
```

---

### Extension 1.2: enrich_posts_with_sector() (HIGH)

**Location:** Add to core/dlt_collection.py after collect_problem_posts()

**Signature:**
```python
def enrich_posts_with_sector(
    posts: List[Dict[str, Any]],
    sector_mapping: Dict[str, str] = None
) -> List[Dict[str, Any]]:
    """Add sector classification to posts."""
```

**Effort:** 2 hours
**Blocks:** batch_opportunity_scoring.py (needs sector for analysis)

**Implementation Checklist:**
- [ ] Import SECTOR_MAPPING from batch_opportunity_scoring.py (87 subreddits)
- [ ] Add "sector" field to each post
- [ ] Handle unmapped subreddits (default to "Other")
- [ ] Validate all subreddits have mappings
- [ ] Test with sample data

**Sector Mapping Categories (87 total):**
- Health & Fitness (14)
- Finance & Investing (18)
- Education & Career (11)
- Travel & Experiences (12)
- Real Estate (11)
- Technology & SaaS (12)
- Other (unmapped)

---

### Extension 1.3: load_opportunity_insights() (MEDIUM - Optional)

**Location:** Add to core/dlt_collection.py after load_to_supabase()

**Signature:**
```python
def load_opportunity_insights(
    insights: List[Dict[str, Any]],
    write_mode: str = "merge"
) -> bool:
    """Load AI-generated opportunity insights to DLT."""
```

**Effort:** 2 hours
**Blocks:** None (optional for Phase 1)

**Implementation:**
- [ ] Create opportunity_analysis table schema
- [ ] DLT loader with merge disposition
- [ ] Primary key: submission_id (unique per analysis)
- [ ] Support incremental re-analysis

**Table Schema:**
```python
{
    "submission_id": str,  # PK
    "opportunity_score": float,
    "dimensions": {
        "problem_severity": float,
        "market_size": float,
        "payment_willingness": float,
        "competitive_intensity": float,
        "technical_feasibility": float
    },
    "recommendation": str,
    "analyzed_at": int,
    "ai_model": str
}
```

---

### Extension 1.4: Cursor State Tracking (MEDIUM - Incremental)

**Location:** Modify main() in core/dlt_collection.py

**Effort:** 2 hours
**Impact:** Enables resumable collection (useful for large datasets)

**Implementation:**
- [ ] Add --resume flag to CLI
- [ ] Load last_created_utc from state file
- [ ] Filter posts >= last_created_utc
- [ ] Save state after successful load
- [ ] Test resume functionality

**State File Format:**
```json
{
    "reddit_harbor_problem_collection": {
        "opensource": {
            "last_created_utc": 1704067200,
            "last_run": "2025-11-07T12:00:00Z"
        },
        "SideProject": { ... }
    }
}
```

---

## Migration Path Summary

### Immediate Actions (Today)
1. ✅ Extension 1.1: Implement collect_post_comments() (3-4 hrs)
2. ✅ Migrate collect_commercial_data.py (1 hr)
3. ✅ Test with real Reddit data (1 hr)

### Following Day
4. ✅ Extension 1.2: Implement enrich_posts_with_sector() (2 hrs)
5. ✅ Adapt batch_opportunity_scoring.py (1 hr)
6. ✅ Test sector mapping (1 hr)

### Optional Phase 1
7. Extension 1.3: load_opportunity_insights() (2 hrs)
8. Test full pipeline (1 hr)

### Timeline
- **Phase 1 Unblock:** 1-2 days (Extensions 1.1 only)
- **Full Phase 1:** 2-3 days (Extensions 1.1 + 1.2)
- **Phase 2+:** 1 week additional (Extensions 1.3 + 1.4 + scaling)

---

## Dependency Resolution Quick Guide

### Problem 1: redditharbor.dock.pipeline (EXTERNAL)
**Solution:** Implement locally in core/dlt_collection.py
- Extension 1.1 replaces subreddit_comment() calls
- collect_problem_posts() already replaces subreddit_submission() calls
- No external dependency needed

### Problem 2: analyze_real_database_data (ARCHIVED)
**Solution:** Extract to core/opportunity_analyzer.py (Phase 2+)
- Not needed for Phase 1
- Only referenced in automated_opportunity_collector.py
- Keep archived until Phase 2 starts

### Problem 3: core.collection functions (PARTIAL)
**Solution:** Import constants, adapt function signatures
- Use: PROBLEM_KEYWORDS, MONETIZATION_KEYWORDS, etc. ✅
- Replace: collect_data() with core.dlt_collection.py functions ✅
- Status: No blocker, just refactoring

---

## Success Criteria for Phase 1

### By End of Day 1
- [x] Extension 1.1 implemented (collect_post_comments)
- [x] collect_commercial_data.py migrated
- [x] All Phase 1 scripts using core.dlt_collection.py

### By End of Day 2
- [x] Extension 1.2 implemented (sector mapping)
- [x] batch_opportunity_scoring.py adapted
- [x] End-to-end test with real data

### Testing Validation
```bash
# Test comment collection
python -c "from core.dlt_collection import collect_post_comments; 
           print(collect_post_comments(reddit, ['test_id'], test_mode=True))"

# Test sector enrichment  
python -c "from core.dlt_collection import enrich_posts_with_sector;
           posts = [{'subreddit': 'personalfinance'}]
           result = enrich_posts_with_sector(posts)
           print(result[0]['sector'])"

# Test migration
python scripts/collect_commercial_data.py --limit 5 --test
```

---

## File References

**Core Module:** `/home/carlos/projects/redditharbor/core/dlt_collection.py` (368 lines)

**Related Scripts:**
- `/home/carlos/projects/redditharbor/scripts/batch_opportunity_scoring.py` (Line 46: SECTOR_MAPPING)
- `/home/carlos/projects/redditharbor/scripts/collect_commercial_data.py` (Line 14: BLOCKING IMPORT)
- `/home/carlos/projects/redditharbor/scripts/full_scale_collection.py` (Line 17: BLOCKING IMPORT)

**Configuration:**
- `/home/carlos/projects/redditharbor/config/dlt_settings.py`
- `/home/carlos/projects/redditharbor/.dlt/secrets.toml` (not in source)

**Full Analysis:** `/home/carlos/projects/redditharbor/docs/architecture/dlt-module-analysis.md`

---

**Last Updated:** 2025-11-07
**Status:** Ready for implementation
**Next:** Implement Extension 1.1
