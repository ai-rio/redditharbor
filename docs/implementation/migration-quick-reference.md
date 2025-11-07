# DLT Migration Quick Reference

## At a Glance

**6 Scripts Analyzed → 3 Phases → Clear Migration Path**

---

## Phase 1: Foundation (EASY - Start Here)
### Scripts: 3 | Timeline: 1-2 days | Risk: LOW

| Script | Scale | Type | Key Feature | Ready |
|--------|-------|------|-------------|-------|
| batch_opportunity_scoring.py | N/A | Transform | No collection, pure DB processing | ✅ NOW |
| final_system_test.py | Synthetic | Validation | No API calls, test data | ✅ NOW |
| collect_commercial_data.py | 5 subs | Collection | Smallest real collection | ✅ NOW |

**Goal:** Validate DLT → Supabase pipeline works

---

## Phase 2: Scale (MEDIUM - Next)
### Scripts: 2 | Timeline: 4-6 days | Risk: MEDIUM

| Script | Scale | Type | Key Feature | Blocker |
|--------|-------|------|-------------|---------|
| full_scale_collection.py | 47 subs | Collection | Multi-segment, comments | Clarify pipeline abstraction |
| automated_opportunity_collector.py | 35 subs | Collection | Scheduled, batch delays | Locate analyze_real_database_data |

**Goal:** Collection at scale with error recovery

---

## Phase 3: Complex (HARD - Last)
### Scripts: 1 | Timeline: 1-2 weeks | Risk: HIGH

| Script | Scale | Type | Key Feature | Blocker |
|--------|-------|------|-------------|---------|
| run_monetizable_collection.py | 73 subs | Collection | Keywords, sentiment, workarounds | Analyze core.collection function |

**Goal:** Complete pipeline with all transformations

---

## Key Patterns (What We Found)

### 1. Abstraction Inconsistency
```
full_scale_collection.py        → Direct PRAW
collect_commercial_data.py      → RedditHarbor.dock.pipeline (undefined)
run_monetizable_collection.py   → core.collection module
```
**Action:** Standardize on direct PRAW OR clarify RedditHarbor.dock.pipeline

---

### 2. No Duplicate Prevention
**All scripts lack it.** DLT's `merge` mode with `primary_key="id"` solves this.

---

### 3. Rate Limiting Varies
| Script | Approach |
|--------|----------|
| automated_opportunity_collector | Explicit 30s delays |
| run_monetizable_collection | Exponential backoff |
| Others | Implicit in PRAW |

---

### 4. Error Recovery ∝ Scale
- 5 subs: Print statements
- 35-47 subs: File logging + batch recovery
- 73 subs: Structured logging + segment recovery

---

### 5. Transformation is Separate
```
Collect → Store → Transform → Analyze
 PRAW   Supabase  Batch Scoring  Reporting
```
DLT handles first 2 steps; transformations remain post-load.

---

## Blocking Dependencies

### MUST RESOLVE (High Risk)
1. **redditharbor.dock.pipeline** - Used by 2 scripts, not found
   - Decision: Clarify if exists or use direct PRAW

2. **analyze_real_database_data** - Used by 1 script, not found
   - Decision: Locate or refactor analyzer integration

3. **core.collection.collect_monetizable_opportunities_data()** - Complex function
   - Decision: Analyze before Phase 3 migration

### SHOULD HANDLE (Medium Risk)
4. **PII Anonymization** - Currently disabled (mask_pii=False)
5. **Agent Integration** - OpportunityAnalyzerAgent dependency

---

## Success Metrics

### Phase 1 ✓
- 5 subs collected without errors
- 250+ submissions stored
- 5000+ comments stored  
- No duplicates on re-run

### Phase 2 ✓
- 47 subs collected without errors
- 7000+ submissions + 10000+ comments
- All 3 tables populated (submissions, comments, redditors)
- Completes in < 30 minutes

### Phase 3 ✓
- 73 subs collected
- 22000+ submissions
- Keywords populated
- Sentiment scores calculated
- End-to-end validation passes

---

## Migration Decision Tree

```
Start Phase 1?
├─ YES → Proceed with batch_opportunity_scoring.py
│  └─ Validate transformation pipeline
│  └─ Then final_system_test.py
│  └─ Then collect_commercial_data.py (5 subs)
│
└─ NO → Resolve blockers first
   ├─ Clarify redditharbor.dock.pipeline
   ├─ Locate analyze_real_database_data
   └─ Analyze core.collection module
```

---

## Technical Architecture Notes

### DLT Setup Required
```python
# .dlt/secrets.toml
[reddit_harbor_problem_collection.destination.postgres]
host = "localhost"
port = 54322
database = "postgres"
username = "postgres"
password = "postgres"
```

### Resource Pattern (Model)
```python
@dlt.resource
def reddit_submissions(subreddit: str, limit: int = 50):
    reddit = get_reddit_client()
    for submission in reddit.subreddit(subreddit).new(limit=limit):
        yield {
            "id": submission.id,
            "title": submission.title,
            # ... other fields
        }
```

### Pipeline Pattern
```python
pipeline = dlt.pipeline(
    "reddit_collection",
    destination="postgres",
    dataset_name="reddit_harbor"
)

pipeline.run(
    reddit_submissions("subreddit_name"),
    write_disposition="merge",
    primary_key="id"
)
```

---

## Files Generated

### Detailed Analysis
📄 `/home/carlos/projects/redditharbor/analysis/dlt_migration_task1_analysis.md`
- 741 lines, 28 KB
- Complete script profiles
- Dependency graph
- Detailed migration specs

### Executive Summary
📄 `/home/carlos/projects/redditharbor/dlt-task1-summary.md`
- 343 lines, 12 KB
- Key findings
- Phase breakdown
- Immediate next steps

### Quick Reference (this file)
📄 `/home/carlos/projects/redditharbor/migration-quick-reference.md`
- Visual overview
- Decision trees
- Quick lookup tables

---

## Immediate Actions

### This Week
- [ ] Clarify redditharbor.dock.pipeline existence
- [ ] Locate analyze_real_database_data module
- [ ] Review migration order with team
- [ ] Confirm technical decisions (1, 2, 3 above)

### Next Week
- [ ] Start Phase 1 with batch_opportunity_scoring.py
- [ ] Set up DLT pipeline infrastructure
- [ ] Create unit tests for DLT resources
- [ ] Begin final_system_test.py migration

### Then
- [ ] Phase 1 complete → validation
- [ ] Phase 2 with full_scale_collection.py
- [ ] Phase 3 with run_monetizable_collection.py

---

## Contact for Clarification

Refer to:
- Detailed analysis: `/home/carlos/projects/redditharbor/analysis/dlt_migration_task1_analysis.md`
- Summary: `/home/carlos/projects/redditharbor/dlt-task1-summary.md`
- This guide: `/home/carlos/projects/redditharbor/migration-quick-reference.md`

---

**Task 1 Status:** ✅ COMPLETE  
**Analysis Date:** 2025-11-07  
**Branch:** feature/dlt-integration  
**Confidence:** HIGH
