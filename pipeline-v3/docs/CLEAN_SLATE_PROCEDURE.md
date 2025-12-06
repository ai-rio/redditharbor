# Clean Slate Procedure - RedditHarbor Pipeline v3 Live Test

## Purpose

The clean slate procedure is performed before live testing to establish a clear baseline with zero existing opportunities. This eliminates data contamination from previous test runs and ensures accurate performance measurement and KPI calculation.

Starting from zero opportunities provides:
- Unambiguous baseline measurements
- Accurate KPI tracking without legacy data interference
- Reproducible test results
- Clean metrics collection from the first processed record

## Benefits of Clean Slate Testing

1. **Clear Baseline Measurement**: Every metric starts from 0, making it easy to track and validate pipeline performance

2. **Accurate KPI Calculation**:
   - No interference from previous test data
   - Precise measurement of processing rates
   - Reliable cost tracking per opportunity
   - Trustworthy agent performance metrics

3. **Reproducible Test Results**:
   - Identical starting conditions for each test run
   - Consistent benchmark comparisons
   - Reliable performance regression detection

4. **Clean Metrics Collection**:
   - No mixed or legacy data in metrics tables
   - Fresh start for all monitoring views
   - Accurate timing measurements from timestamp 0

## Procedure

The clean slate procedure was performed on **2025-12-05** with the following steps:

### 1. Database Backup Creation

```bash
# Create timestamped backup before clean slate
pg_dump -h 127.0.0.1 -p 54322 -U postgres -d postgres \
    > backup_before_live_test_20251205_000000.dump
```

### 2. Truncate Opportunities Table

```bash
# Remove all existing opportunities
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres \
    -c "TRUNCATE opportunities CASCADE;"
```

### 3. Truncate Pipeline Metrics (if exists)

```bash
# Clear any existing metrics
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres \
    -c "TRUNCATE pipeline_metrics CASCADE;"
```

### 4. Verify Zero Counts

```bash
# Check opportunity count
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres \
    -c "SELECT COUNT(*) FROM opportunities;"

# Expected: 0

# Check metrics table
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres \
    -c "SELECT COUNT(*) FROM pipeline_metrics;"

# Expected: 0
```

### 5. Apply Metrics Migration

```bash
# Ensure metrics tracking is properly set up
./pipeline-v3/scripts/apply_metrics_migration.sh
```

### 6. Verify Clean State

```bash
# Verify all tables are clean and ready
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c "
SELECT
    'opportunities' as table_name, COUNT(*) as record_count
FROM opportunities
UNION ALL
SELECT
    'pipeline_metrics' as table_name, COUNT(*) as record_count
FROM pipeline_metrics;
"
```

## Validation Commands

After clean slate procedure, validate the system is ready:

### Database State Validation

```bash
# Verify clean state
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres << 'SQL'
-- Check table counts
DO $$
DECLARE
    opp_count INTEGER;
    metrics_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO opp_count FROM opportunities;
    SELECT COUNT(*) INTO metrics_count FROM pipeline_metrics;

    IF opp_count <> 0 THEN
        RAISE EXCEPTION 'Opportunities table not clean: % records', opp_count;
    END IF;

    IF metrics_count <> 0 THEN
        RAISE EXCEPTION 'Pipeline metrics table not clean: % records', metrics_count;
    END IF;

    RAISE NOTICE '✓ Database is in clean state';
END $$;
SQL
```

### Metrics Views Verification

```bash
# Verify metrics views return empty results
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c "
SELECT * FROM pipeline_phase_summary;
SELECT * FROM agent_performance_summary;
SELECT * FROM cost_analysis;"
```

## Rollback Procedure

If you need to restore the previous state:

### Restore from Backup

```bash
# Stop any running pipeline processes first
# Then restore the backup
pg_restore -h 127.0.0.1 -p 54322 -U postgres -d postgres \
    --clean --if-exists \
    backup_before_live_test_20251205_000000.dump
```

### Verify Restoration

```bash
# Check if data was restored correctly
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres \
    -c "SELECT COUNT(*) FROM opportunities;"
```

## Post-Clean Slate Testing

With a clean slate, the following tests provide accurate baseline measurements:

### Test 1: Single Opportunity Processing

```bash
cd /home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3
python main.py --limit 1 --subreddits test
```

### Test 2: Small Batch Processing

```bash
cd /home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3
python main.py --limit 10 --subreddits productivity,entrepreneur
```

### Test 3: Metrics Collection Validation

```bash
# After processing any opportunities, verify metrics
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c "
SELECT
    phase_name,
    COUNT(*) as records,
    AVG(duration_ms) as avg_duration_ms,
    SUM(CASE WHEN success THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as success_rate
FROM pipeline_phase_summary
GROUP BY phase_name;"
```

## Key Considerations

1. **Performance Impact**: Starting from 0 means the first batch may show slightly different performance characteristics than steady-state processing

2. **Agent Learning**: Some agents might benefit from a warm-up period; consider this when analyzing initial results

3. **Database Statistics**: Run `ANALYZE` after the first significant data load to update optimizer statistics

4. **Monitoring**: With clean metrics, all alerts and thresholds will be based on current performance, not historical averages

## Timestamp

**Clean Slate Performed**: 2025-12-05 00:00:00 UTC

This procedure ensures that all live testing begins with a pristine state, providing the most accurate and reliable measurements of pipeline performance.