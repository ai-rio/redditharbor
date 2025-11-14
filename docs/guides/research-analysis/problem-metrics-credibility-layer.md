# Problem Metrics & Credibility Layer Implementation

**Status:** ✅ Complete
**Date:** 2025-11-10
**Purpose:** Add transparent Reddit validation signals to opportunities for credibility

---

## Overview

The problem metrics credibility layer adds **raw Reddit engagement data** to opportunity opportunities, providing transparent proof of market demand rather than relying solely on the AI scoring algorithm.

### What Gets Added

For each opportunity, users now see:
- **Comment Count:** Total discussions of this problem
- **Trending Score:** % change in recent activity (momentum)
- **Subreddit Spread:** Number of communities where problem appears (breadth)
- **Intent Signals:** Comments expressing willingness to pay (monetization validation)

**Example Display:**
```
Score: 28.0 | Comments: 247 | Trending: +8% | Spread: 4 communities | Intent Signals: 12
```

This shifts from: **"Here's a score"** → to **"Here's proof from Reddit"**

---

## Architecture

### New Database Components

| Component | Type | Purpose |
|-----------|------|---------|
| `problem_metrics` | Table | Stores aggregated engagement data per submission |
| `refresh_problem_metrics()` | Function | Calculates and updates metrics for a submission |
| `get_opportunities_with_metrics()` | Function | Dashboard query joining opportunities with metrics |
| `v_trending_problems` | View | Top trending problems by momentum |
| `v_validated_problems` | View | Problems with strong engagement signals |

### Data Flow

```
submissions + comments
    ↓
refresh_problem_metrics()
    ↓
problem_metrics table
    ↓
get_opportunities_with_metrics()
    ↓
Dashboards display metrics alongside scores
```

---

## Deployment Steps

### 1. Apply Database Migration

**First time setup (required):**

```bash
# Option A: Using the initialization script (recommended)
python scripts/initialize_problem_metrics.py

# Option B: Manual psql
psql -h <host> -U <user> -d <database> \
  -f supabase/migrations/20251110151231_add_problem_metrics_table.sql
```

**What it creates:**
- `problem_metrics` table with 7 indexes
- `refresh_problem_metrics()` function
- `get_opportunities_with_metrics()` function (for dashboards)
- 2 convenience views (`v_trending_problems`, `v_validated_problems`)

### 2. Refresh Metrics for Existing Data

**Using the script (recommended):**

```bash
python scripts/initialize_problem_metrics.py
```

**Using SQL directly:**

```sql
-- Refresh metrics for all submissions
DO $$
DECLARE
    submission_record RECORD;
BEGIN
    FOR submission_record IN
        SELECT DISTINCT id FROM submissions
    LOOP
        PERFORM refresh_problem_metrics(submission_record.id);
    END LOOP;
END $$;
```

### 3. Update Batch Scoring Script

✅ **Already updated** - metrics are automatically refreshed after batch processing.

The `batch_opportunity_scoring.py` now includes:
```python
# Line 871-873: Automatic metrics refresh
submission_ids = [sub.get("id") for sub in submissions if sub.get("id")]
refresh_problem_metrics(supabase, submission_ids)
```

### 4. Update Dashboards

✅ **Already updated** - all 3 dashboards now support metrics:

| Dashboard | Status | Metrics Shown |
|-----------|--------|---------------|
| `opportunity_dashboard_fixed.py` | ✅ Updated | Comments, Trending, Spread, Intent Signals |
| `opportunity_dashboard_reactive.py` | ✅ Updated | Comments, Trending |
| `ultra_rare_dashboard.py` | ✅ Updated | Fallback to app_opportunities if metrics unavailable |

All dashboards have graceful fallback if `problem_metrics` table doesn't exist yet.

---

## Code Changes Summary

### Modified Files

#### 1. `scripts/batch_opportunity_scoring.py`

Added `refresh_problem_metrics()` function (line 711-750):
```python
def refresh_problem_metrics(supabase, submission_ids: List[str]) -> None:
    """Refresh problem metrics for given submissions."""
    # Calls stored procedure for each submission
    # Has error handling - failures don't block scoring
```

Called after DLT loading (line 871-873):
```python
submission_ids = [sub.get("id") for sub in submissions if sub.get("id")]
refresh_problem_metrics(supabase, submission_ids)
```

#### 2. `marimo_notebooks/opportunity_dashboard_fixed.py`

Updated data fetch (line 51-68):
```python
# Try to get opportunities with metrics
try:
    result = supabase.rpc('get_opportunities_with_metrics', {}).execute()
    data = result.data if result.data else []
except:
    # Fallback to app_opportunities only
    ...
```

Updated display (line 103-110):
```python
if opp_data.get('comment_count') is not None:
    row.update({
        'Comments': opp_data.get('comment_count', 0),
        'Trending': f"{opp_data.get('trending_score', 0):.0f}%",
        'Spread': f"{opp_data.get('subreddit_spread', 0)} communities",
        'Intent Signals': opp_data.get('intent_signal_count', 0),
    })
```

#### 3. `marimo_notebooks/opportunity_dashboard_reactive.py`

Same changes as `opportunity_dashboard_fixed.py`

#### 4. `marimo_notebooks/ultra_rare_dashboard.py`

Updated high-score opportunity fetch with metrics support and fallback

#### 5. `supabase/migrations/20251110151231_add_problem_metrics_table.sql`

New migration (401 lines) that creates:
- `problem_metrics` table
- Helper functions
- Views
- Indexes

### New Files

#### 1. `scripts/initialize_problem_metrics.py`

Standalone initialization script that:
- Applies the migration
- Verifies all components
- Refreshes metrics for all existing submissions
- Provides deployment feedback

---

## Usage After Deployment

### Automatic Metrics Refresh

Metrics are **automatically refreshed** after each batch scoring run:

```bash
python scripts/batch_opportunity_scoring.py
# ... scoring runs ...
# ✓ Problem metrics refreshed for 115 submissions
```

### Manual Metrics Refresh

Refresh metrics for a specific submission:

```sql
SELECT refresh_problem_metrics('submission-uuid');
```

### Dashboard Queries

Get opportunities with metrics:

```sql
SELECT * FROM get_opportunities_with_metrics() LIMIT 10;
```

Get trending problems:

```sql
SELECT * FROM v_trending_problems LIMIT 10;
```

Get validated problems:

```sql
SELECT * FROM v_validated_problems LIMIT 10;
```

---

## Performance Considerations

### Table Indexes

The migration creates **7 indexes** optimized for dashboard queries:

```sql
-- Sorting/filtering by key metrics
idx_problem_metrics_trending_score      -- For trending sort
idx_problem_metrics_comment_count        -- For engagement sort
idx_problem_metrics_total_upvotes        -- For upvote sort
idx_problem_metrics_subreddit_spread     -- For reach sort
idx_problem_metrics_intent_signal_count  -- For monetization sort
idx_problem_metrics_last_seen            -- For recency
idx_problem_metrics_active_trending      -- Composite for filtering
```

### Calculated Fields in Views

The views calculate on-the-fly:
- `days_active` - Days since first mention
- `recency_score` - 0-100 score based on last activity
- `validation_score` - Weighted composite of all signals

All calculations are efficient (no N+1 queries).

---

## Rollback Plan

If needed to revert:

```sql
-- Drop all new components (safe)
DROP VIEW IF EXISTS v_validated_problems CASCADE;
DROP VIEW IF EXISTS v_trending_problems CASCADE;
DROP FUNCTION IF EXISTS get_opportunities_with_metrics() CASCADE;
DROP FUNCTION IF EXISTS refresh_problem_metrics(UUID) CASCADE;
DROP TABLE IF EXISTS problem_metrics CASCADE;

-- Data in app_opportunities remains untouched
-- Dashboards will gracefully fallback to app_opportunities only
```

---

## Expected Behavior

### Before Metrics Refresh

```
Opportunity: "Procrastination Intervention App"
Score: 28.0
[No credibility data - waiting for refresh]
```

### After Metrics Refresh

```
Opportunity: "Procrastination Intervention App"
Score: 28.0
Comments: 247
Trending: +8%
Spread: 4 communities
Intent Signals: 12
[Raw Reddit proof of demand]
```

### Dashboard Experience

1. **Main Dashboard** (≥25.0)
   - Shows full credibility metrics
   - 115+ opportunities with natural function distribution

2. **Reactive Dashboard** (≥25.0)
   - Compact view with key metrics
   - Shows Comments and Trending columns

3. **Ultra-Rare Dashboard** (≥60.0)
   - For high-score opportunities
   - Metrics shown when available

---

## Testing

### Verify Installation

```bash
# Run the initialization script
python scripts/initialize_problem_metrics.py

# Expected output:
# ✓ Migration applied successfully!
# ✓ problem_metrics table exists
# ✓ refresh_problem_metrics() function exists
# ✓ get_opportunities_with_metrics() function exists
# ✓ Metrics refresh complete!
```

### Query Test

```sql
-- Check metrics exist
SELECT COUNT(*) FROM problem_metrics;

-- View a sample
SELECT problem_id, comment_count, trending_score, intent_signal_count
FROM problem_metrics LIMIT 5;

-- Test dashboard query
SELECT * FROM get_opportunities_with_metrics() LIMIT 3;
```

### Dashboard Test

```bash
# Start each dashboard
marimo run marimo_notebooks/opportunity_dashboard_fixed.py
marimo run marimo_notebooks/opportunity_dashboard_reactive.py
marimo run marimo_notebooks/ultra_rare_dashboard.py

# Look for metrics columns in tables
```

---

## Monitoring

### Metrics Staleness

Monitor when metrics were last updated:

```sql
SELECT
    problem_id,
    EXTRACT(HOUR FROM (NOW() - updated_at)) AS hours_since_refresh,
    comment_count,
    trending_score
FROM problem_metrics
WHERE updated_at < NOW() - INTERVAL '24 hours'
ORDER BY updated_at ASC;
```

### Refresh Success Rate

```sql
SELECT
    DATE(updated_at) AS refresh_date,
    COUNT(*) AS total_refreshed,
    COUNT(CASE WHEN comment_count > 0 THEN 1 END) AS with_engagement
FROM problem_metrics
GROUP BY DATE(updated_at)
ORDER BY refresh_date DESC;
```

---

## FAQ

**Q: Do I need to manually refresh metrics?**
A: No. The batch scorer does it automatically. Use manual refresh only for testing or specific submissions.

**Q: What if the metrics table doesn't exist?**
A: Dashboards gracefully fallback to app_opportunities only. Metrics are optional, not required.

**Q: How long does refresh take?**
A: ~0.1 seconds per submission. 1000 submissions ≈ 100 seconds.

**Q: Can I refresh just changed opportunities?**
A: Yes: `SELECT refresh_problem_metrics('submission-id');`

**Q: What if a submission has no comments?**
A: Metrics are set to 0. The dashboard still displays the opportunity with its score.

**Q: Does this affect the 5D scoring algorithm?**
A: No. Metrics are display-only. Scoring is unchanged. They're complementary data layers.

---

## Next Steps

1. ✅ **Deploy migration** - Run `initialize_problem_metrics.py`
2. ✅ **Refresh metrics** - Script handles this automatically
3. ✅ **Run batch scoring** - Metrics refresh happens automatically
4. ✅ **View dashboards** - Metrics now displayed alongside scores
5. 📊 **Monitor trend** - Track trending/intent signals over time

---

**Questions?** See code references in migration or dashboard files.

Generated: 2025-11-10
