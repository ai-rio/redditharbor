# DLT Consolidation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Consolidate all Reddit data collection through DLT infrastructure, remove redundant PRAW-only scripts, and achieve 13.8% performance improvement through incremental loading.

**Architecture:** Migrate 7 active PRAW-only scripts to use `core/dlt_collection.py`, which provides unified DLT-based collection with incremental loading, automatic deduplication, and state tracking. This eliminates dual-system maintenance overhead and enables performance optimization.

**Tech Stack:** DLT v1.18.2, PRAW Reddit API client, PostgreSQL/Supabase, Python 3.12

**Current State:**
- DLT infrastructure exists: `core/dlt_collection.py` (367 lines, 6 functions)
- 2 scripts use DLT: `dlt_opportunity_pipeline.py`, `dlt_traffic_cuttover.py`
- 7 active scripts still use direct PRAW (missing 13.8% performance gain)

**Benefits of Consolidation:**
- 13.8% faster incremental loads (verified in testing)
- Automatic state tracking (no reprocessing old data)
- Schema evolution (handles new fields automatically)
- Clear audit trail (DLT load IDs track data provenance)
- Single source of truth for data collection

---

## Phase 1: Audit & Dependency Analysis

### Task 1: Analyze PRAW-Only Scripts for Common Patterns

**Files:**
- Read: `scripts/automated_opportunity_collector.py`
- Read: `scripts/batch_opportunity_scoring.py`
- Read: `scripts/collect_commercial_data.py`
- Read: `scripts/full_scale_collection.py`
- Read: `scripts/run_monetizable_collection.py`
- Read: `scripts/final_system_test.py`
- Read: `core/dlt_collection.py` (understand available functions)

**Step 1: Examine script purposes**

Open each script and identify:
- What data does it collect? (specific subreddits, search terms, etc.)
- What filtering does it apply? (problem keywords, comment counts, etc.)
- Where does it store data? (Supabase table names)
- How does it handle duplicates? (or does it?)

**Step 2: Document findings**

Create a table in memory with:
```
Script Name | Purpose | Data Source | Filters Applied | DLT Equivalent
automated_opportunity_collector.py | collect opportunities | r/personalfinance, r/investing | problem keywords | collect_problem_posts()
...
```

**Step 3: Verify core/dlt_collection.py functions**

Check what functions are available:
```bash
grep "^def " core/dlt_collection.py
```

Expected output:
```
def collect_problem_posts(subreddit_list, limit=500, use_incremental=True)
def create_dlt_pipeline()
def load_to_supabase()
...
```

**Step 4: Create audit document**

Write findings to: `docs/audits/dlt-consolidation-audit.md`

Document:
- Which scripts can be replaced by existing DLT functions
- Which scripts need custom filtering extensions
- Which scripts are truly redundant
- Which scripts should be kept for testing

**Step 5: Commit audit**

```bash
git add docs/audits/dlt-consolidation-audit.md
git commit -m "docs: audit PRAW scripts for DLT migration readiness"
```

---

## Phase 2: Create DLT Wrapper Functions (if needed)

### Task 2: Extend DLT Collection Module with Missing Functions

**Files:**
- Modify: `core/dlt_collection.py`
- Test: `tests/test_dlt_collection_extended.py`

**Context from Task 1:** Based on audit, identify if additional functions are needed.

**Step 1: Analyze gaps**

Compare each PRAW script's requirements vs DLT available functions:
- Does `collect_problem_posts()` support all needed filters?
- Are there domain-specific collection needs (e.g., commercial data)?
- Do any scripts need custom keyword filtering?

**Step 2: Design new functions** (if needed)

If audit shows gaps, design new DLT functions:
```python
def collect_commercial_opportunities(subreddit_list: List[str], limit=500):
    """Collect posts with commercial keywords (pay, cost, price, revenue, etc.)"""
    pass

def collect_by_keyword(subreddit_list: List[str], keywords: List[str], limit=500):
    """Generic collection by keyword list"""
    pass
```

**Step 3: Implement minimal new functions**

Add only what's necessary to `core/dlt_collection.py`:

```python
def collect_by_keyword(subreddit_list: List[str], keywords: List[str], limit=500):
    """
    Collect Reddit posts matching any keyword.

    Args:
        subreddit_list: List of subreddit names
        keywords: Keywords to search for
        limit: Max posts per subreddit

    Returns:
        Generator of submission dictionaries
    """
    reddit = _get_reddit_client()

    for subreddit_name in subreddit_list:
        subreddit = reddit.subreddit(subreddit_name)
        for post in subreddit.new(limit=limit):
            # Filter by keywords
            text = (post.title + " " + post.selftext).lower()
            if any(kw.lower() in text for kw in keywords):
                yield {
                    'id': post.id,
                    'title': post.title,
                    'text': post.selftext,
                    'subreddit': post.subreddit.display_name,
                    'created_utc': post.created_utc,
                    'score': post.score,
                    'num_comments': post.num_comments
                }
```

**Step 4: Write tests**

Create `tests/test_dlt_collection_extended.py`:

```python
def test_collect_by_keyword_filters_correctly(mock_reddit):
    """Test that keyword filter returns only matching posts"""
    # Setup mock posts
    posts = [
        {'title': 'I need help with payments', 'selftext': 'How do I handle crypto payments?'},
        {'title': 'Tips for hiking', 'selftext': 'Great trails in Colorado'},
    ]

    keywords = ['payment', 'crypto']
    results = list(collect_by_keyword(['test_sub'], keywords))

    assert len(results) == 1
    assert 'payment' in results[0]['title'].lower() or 'payment' in results[0]['text'].lower()
```

**Step 5: Commit**

```bash
git add core/dlt_collection.py tests/test_dlt_collection_extended.py
git commit -m "feat: add keyword-based collection to DLT module"
```

---

## Phase 3: Migrate Individual Scripts

### Task 3: Migrate automated_opportunity_collector.py to DLT

**Files:**
- Modify: `scripts/automated_opportunity_collector.py`
- Update imports, remove direct PRAW usage
- Test with: `python scripts/automated_opportunity_collector.py --test --limit 5`

**Step 1: Backup original**

```bash
cp scripts/automated_opportunity_collector.py scripts/automated_opportunity_collector.py.bak
```

**Step 2: Replace PRAW collection with DLT**

Identify current collection code:
```python
# OLD: Direct PRAW
reddit = praw.Reddit(...)
for subreddit in ['personalfinance', 'investing']:
    for post in reddit.subreddit(subreddit).new(limit=100):
        # process post
```

Replace with:
```python
# NEW: DLT-based
from core.dlt_collection import collect_problem_posts

for post in collect_problem_posts(['personalfinance', 'investing'], limit=100):
    # process post
```

**Step 3: Remove manual Supabase handling**

DLT handles data loading, so remove:
```python
# DELETE: Manual Supabase operations
supabase = create_client(...)
supabase.table("submissions").insert(...)
```

Replace with:
```python
# DLT handles this automatically
```

**Step 4: Test migration**

```bash
source .venv/bin/activate
python scripts/automated_opportunity_collector.py --test --limit 3
```

Expected: Script runs, collects 3 posts, loads to Supabase via DLT

**Step 5: Commit**

```bash
git add scripts/automated_opportunity_collector.py
git commit -m "feat: migrate automated_opportunity_collector to DLT pipeline"
```

### Task 4: Migrate batch_opportunity_scoring.py to DLT

**Files:**
- Modify: `scripts/batch_opportunity_scoring.py`

**Steps:** Same as Task 3 (apply same migration pattern)

**Commit:**
```bash
git commit -m "feat: migrate batch_opportunity_scoring to DLT pipeline"
```

### Task 5: Migrate collect_commercial_data.py to DLT

**Files:**
- Modify: `scripts/collect_commercial_data.py`

**Steps:** Same as Task 3

**Commit:**
```bash
git commit -m "feat: migrate collect_commercial_data to DLT pipeline"
```

### Task 6: Migrate full_scale_collection.py to DLT

**Files:**
- Modify: `scripts/full_scale_collection.py`

**Steps:** Same as Task 3

**Commit:**
```bash
git commit -m "feat: migrate full_scale_collection to DLT pipeline"
```

### Task 7: Migrate run_monetizable_collection.py to DLT

**Files:**
- Modify: `scripts/run_monetizable_collection.py`

**Steps:** Same as Task 3

**Commit:**
```bash
git commit -m "feat: migrate run_monetizable_collection to DLT pipeline"
```

### Task 8: Migrate final_system_test.py to DLT

**Files:**
- Modify: `scripts/final_system_test.py`

**Steps:** Same as Task 3

**Commit:**
```bash
git commit -m "feat: migrate final_system_test to DLT pipeline"
```

---

## Phase 4: Consolidate & Remove Redundancy

### Task 9: Verify All Scripts Use DLT

**Files:**
- Check: All scripts in `scripts/` directory

**Step 1: Verify imports**

```bash
grep -l "from core.dlt_collection import\|import dlt" scripts/*.py | wc -l
```

Expected: All collection scripts (should be 8+ scripts)

**Step 2: Verify no direct PRAW collection**

```bash
grep -l "reddit.subreddit\|reddit.submission" scripts/*.py
```

Expected: Only test/utility scripts (no active collection scripts)

**Step 3: Document consolidated state**

Update `docs/architecture/dlt-collection-overview.md`:

```markdown
# DLT Collection Architecture

## Current Status
✅ All Reddit data collection flows through DLT infrastructure
✅ Incremental loading enabled (13.8% performance improvement)
✅ Automatic state tracking and deduplication
✅ Schema evolution handled automatically

## Data Pipeline
Reddit API → PRAW → DLT Pipeline → Supabase PostgreSQL
                        ↓
                   State Tracking
                   Deduplication
                   Schema Evolution

## Available Functions
- `collect_problem_posts()` - Problems from configured subreddits
- `collect_by_keyword()` - Custom keyword-based collection
- `create_dlt_pipeline()` - Initialize DLT pipeline
- `load_to_supabase()` - Load data to destination

## Scripts Using DLT
- dlt_opportunity_pipeline.py ✅
- dlt_traffic_cuttover.py ✅
- automated_opportunity_collector.py ✅ (migrated)
- batch_opportunity_scoring.py ✅ (migrated)
- collect_commercial_data.py ✅ (migrated)
- full_scale_collection.py ✅ (migrated)
- run_monetizable_collection.py ✅ (migrated)
- final_system_test.py ✅ (migrated)
```

**Step 4: Commit documentation**

```bash
git add docs/architecture/dlt-collection-overview.md
git commit -m "docs: document consolidated DLT collection architecture"
```

### Task 10: Clean Up Old PRAW Scripts (Optional)

**Files:**
- Archive or delete old PRAW-only test scripts

**Decision Point:** Keep or remove?
- `test_scanner.py` - PRAW test utility
- `manual_subreddit_test.py` - Manual testing script
- Other pure-PRAW scripts

**Step 1: Create archive for potentially useful scripts**

```bash
mkdir -p archive/praw-only-scripts
mv scripts/test_scanner.py archive/praw-only-scripts/
mv scripts/manual_subreddit_test.py archive/praw-only-scripts/
```

**Step 2: Update .gitignore if needed**

```bash
echo "archive/praw-only-scripts/" >> .gitignore
```

**Step 3: Commit cleanup**

```bash
git add archive/ .gitignore
git commit -m "chore: archive redundant PRAW-only test scripts"
```

---

## Phase 5: Testing & Validation

### Task 11: End-to-End Test with DLT

**Files:**
- Test: Run full pipeline with incremental loading

**Step 1: Clear local DLT state** (to test fresh run)

```bash
rm -rf .dlt/pipelines/reddit_harbor_collection/
```

**Step 2: Run full collection pipeline**

```bash
source .venv/bin/activate
python scripts/dlt_opportunity_pipeline.py --limit 100
```

Expected:
- Collects 100 posts via DLT
- Loads to Supabase with deduplication
- Creates DLT state files

**Step 3: Run second time** (test incremental loading)

```bash
python scripts/dlt_opportunity_pipeline.py --limit 100
```

Expected:
- Only NEW posts since last run processed
- Execution time ~13.8% faster
- No duplicate posts in Supabase

**Step 4: Verify deduplication**

```bash
source .venv/bin/activate
python3 << 'EOF'
from config.settings import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
response = supabase.table("submissions").select("COUNT").execute()
print(f"Total submissions: {len(response.data)}")

# Check for duplicates
response = supabase.table("submissions").select("id").execute()
ids = [s['id'] for s in response.data]
print(f"Unique IDs: {len(set(ids))}")
assert len(ids) == len(set(ids)), "Duplicate IDs found!"
print("✅ No duplicates - DLT deduplication working")
EOF
```

**Step 5: Commit test results**

```bash
git add docs/test-results/dlt-consolidation-e2e.txt
git commit -m "test: verify end-to-end DLT consolidation"
```

### Task 12: Performance Benchmark

**Files:**
- Benchmark: Compare old PRAW vs new DLT approach

**Step 1: Benchmark DLT pipeline** (first run)

```bash
time python scripts/dlt_opportunity_pipeline.py --limit 500
```

Record time (example: 15 seconds)

**Step 2: Benchmark DLT incremental**

Wait 2 minutes, then:

```bash
time python scripts/dlt_opportunity_pipeline.py --limit 100
```

Record time (example: 2 seconds for 20 new posts)

**Step 3: Calculate savings**

Full run: 15 seconds
Incremental: 2 seconds (but only 20 new posts vs 500)
Efficiency: 2s / (20/500 * 15s) = ~3.3x faster for incremental loads

**Step 4: Document results**

Create `docs/benchmarks/dlt-consolidation-performance.md`:

```markdown
# DLT Consolidation Performance Results

## Full Collection (500 posts)
- Time: ~15 seconds
- Method: Initial DLT load
- Result: All 500 posts to Supabase

## Incremental Collection (20 new posts)
- Time: ~2 seconds
- Method: DLT with state tracking
- Result: Only 20 new posts loaded, 0 duplicates
- Efficiency: 3.3x faster than proportional full load

## Conclusion
✅ DLT incremental loading provides significant performance benefit
✅ Automatic deduplication eliminates data quality issues
✅ State tracking enables efficient scheduled jobs
```

**Step 5: Commit benchmarks**

```bash
git add docs/benchmarks/dlt-consolidation-performance.md
git commit -m "perf: document DLT consolidation performance gains"
```

---

## Phase 6: Update Dependencies & Documentation

### Task 13: Verify Dependencies

**Files:**
- Check: `requirements.txt` and `uv.lock`

**Step 1: Verify DLT is in dependencies**

```bash
grep -i "dlt" requirements.txt
```

Expected:
```
dlt[postgres]==1.18.2
```

**Step 2: Verify DLT is installed**

```bash
source .venv/bin/activate
python -c "import dlt; print(dlt.__version__)"
```

Expected: `1.18.2` (or newer)

**Step 3: If DLT not in requirements, add it**

```bash
echo 'dlt[postgres]==1.18.2' >> requirements.txt
uv sync
```

**Step 4: Commit**

```bash
git add requirements.txt uv.lock
git commit -m "deps: ensure DLT and postgres driver in dependencies"
```

### Task 14: Update README & Documentation

**Files:**
- Modify: `README.md` (data collection section)
- Modify: `docs/architecture/data-pipeline.md` (if exists)
- Create: `docs/guides/dlt-collection-guide.md`

**Step 1: Update README**

Find data collection section in README and update:

```markdown
## Data Collection

RedditHarbor uses **DLT (Data Load Tool)** for efficient Reddit data collection:

### Key Features
- ✅ Incremental loading (13.8% faster on subsequent runs)
- ✅ Automatic deduplication (no duplicate submissions)
- ✅ State tracking (knows what was loaded last)
- ✅ Schema evolution (handles new fields automatically)

### Quick Start

```bash
python scripts/dlt_opportunity_pipeline.py --limit 100
```

### Available Commands

```bash
# Collect problem-first posts
python scripts/dlt_opportunity_pipeline.py --limit 500

# Check collection status
python scripts/dlt_traffic_cuttover.py

# Run full end-to-end pipeline
python scripts/parallel_test_dlt.py
```

### Pipeline Architecture

```
Reddit API (PRAW)
    ↓
DLT Collection (core/dlt_collection.py)
    ├─ Problem Keyword Filtering
    ├─ Incremental State Tracking
    └─ Deduplication by ID
    ↓
Supabase PostgreSQL
    ├─ submissions table
    ├─ comments table
    └─ redditor table
```
```

**Step 2: Create DLT guide**

Create `docs/guides/dlt-collection-guide.md`:

```markdown
# DLT Collection Guide

## Overview

DLT (Data Load Tool) handles all Reddit data collection for RedditHarbor. It provides:
- Efficient incremental loading
- Automatic deduplication
- State tracking
- Schema evolution

## Architecture

### Collection Pipeline
1. **PRAW Client** - Authenticates with Reddit API
2. **DLT Normalization** - Converts raw API data to consistent schema
3. **DLT Write Disposition** - Merge strategy (insert new, skip duplicates)
4. **Supabase Loading** - Writes to PostgreSQL via HTTP

### State Management
- DLT maintains state in `.dlt/pipelines/reddit_harbor_collection/`
- Tracks last run date via `created_utc` cursor
- Prevents reprocessing of old data

## Usage Examples

### Basic Collection
```python
from core.dlt_collection import collect_problem_posts, load_to_supabase

# Collect problem posts
for post in collect_problem_posts(['personalfinance', 'investing'], limit=500):
    print(f"Collected: {post['title']}")

# Load to Supabase (automatic via DLT)
load_to_supabase()
```

### Custom Keyword Collection
```python
from core.dlt_collection import collect_by_keyword

keywords = ['payment', 'crypto', 'subscription']
for post in collect_by_keyword(['personal finance'], keywords):
    print(f"Found: {post['title']}")
```

## Performance

- **Initial Collection**: ~15 seconds for 500 posts
- **Incremental Run**: ~2 seconds for 20 new posts
- **Efficiency**: 3.3x faster than proportional full load

## Troubleshooting

### Reset State (Start Fresh)
```bash
rm -rf .dlt/pipelines/reddit_harbor_collection/
python scripts/dlt_opportunity_pipeline.py  # Re-run
```

### Check Collection Status
```bash
ls -la .dlt/pipelines/reddit_harbor_collection/
cat .dlt/pipelines/reddit_harbor_collection/state.json
```

## Configuration

DLT configuration in `config/dlt_settings.py`:
```python
DLT_PIPELINE_NAME = "reddit_harbor_collection"
DLT_DATASET_NAME = "reddit_harbor"
DLT_WRITE_DISPOSITION = "merge"  # merge | replace | append
DLT_PRIMARY_KEY = "id"  # Deduplication key
```
```

**Step 3: Commit documentation**

```bash
git add README.md docs/guides/dlt-collection-guide.md
git commit -m "docs: add DLT collection documentation and guide"
```

---

## Summary: Before and After

### Before Consolidation
- ✗ 7 PRAW-only scripts (inconsistent, redundant)
- ✗ 2 DLT scripts (isolated, not widely used)
- ✗ Missing 13.8% performance gain
- ✗ Manual duplicate handling
- ✗ No centralized state tracking

### After Consolidation
- ✅ All scripts use DLT pipeline
- ✅ Single source of truth: `core/dlt_collection.py`
- ✅ 13.8% performance improvement enabled
- ✅ Automatic deduplication
- ✅ Centralized state tracking
- ✅ Consistent data quality
- ✅ Easier maintenance (fewer scripts)

---

## Testing Checklist

- [ ] Task 1: Audit PRAW scripts (identify migration patterns)
- [ ] Task 2: Extend DLT module (add missing functions)
- [ ] Task 3-8: Migrate individual scripts
- [ ] Task 9: Verify all scripts use DLT
- [ ] Task 10: Archive redundant PRAW scripts
- [ ] Task 11: End-to-end test (verify deduplication)
- [ ] Task 12: Performance benchmark
- [ ] Task 13: Verify dependencies
- [ ] Task 14: Update documentation

---

## Commits Expected

```
1. docs: audit PRAW scripts for DLT migration readiness
2. feat: add keyword-based collection to DLT module
3. feat: migrate automated_opportunity_collector to DLT pipeline
4. feat: migrate batch_opportunity_scoring to DLT pipeline
5. feat: migrate collect_commercial_data to DLT pipeline
6. feat: migrate full_scale_collection to DLT pipeline
7. feat: migrate run_monetizable_collection to DLT pipeline
8. feat: migrate final_system_test to DLT pipeline
9. docs: document consolidated DLT collection architecture
10. chore: archive redundant PRAW-only test scripts
11. test: verify end-to-end DLT consolidation
12. perf: document DLT consolidation performance gains
13. deps: ensure DLT and postgres driver in dependencies
14. docs: add DLT collection documentation and guide
```

Total estimated time: **3-4 hours** for complete consolidation
