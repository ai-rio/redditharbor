# Pre-Cleanup Database Snapshot
**Date:** November 13, 2025 11:48:46 UTC
**Purpose:** Document database state before cleanup for audit trail

## Context

This snapshot was taken before clearing the `app_opportunities_trust` table to establish a clean baseline for testing the updated OpportunityAnalyzerAgent scoring system.

### Audit Finding Summary
- **Production Readiness Claim:** "After Fix: 0% scoring 70+ (realistic)"
- **Database Reality:** 47.8% scoring 70+ (11/23 records)
- **Conclusion:** Old data from mixed code versions; not useful for comparison
- **Action:** Clean slate recommended

## Database State Summary

### Table: app_opportunities_trust
- **Total Records:** 23
- **Test Records:** 13 (56%)
- **Real Records:** 10 (44%)

### Score Distribution (OLD DATA - DISCARDED)
```
Score Range    | Count | Percentage
---------------|-------|------------
70+            |   11  |  47.8%
60-69          |    8  |  34.8%
40-49          |    4  |  17.4%
Below 40       |    0  |   0.0%
```

### Statistical Summary
- **Min Score:** 42
- **Max Score:** 78
- **Average Score:** 63.83
- **Std Deviation:** 11.31

### DLT Load History (6 batches)
```
Load Timestamp     | Records | Avg Score | Notes
-------------------|---------|-----------|-------
1763029704.805719  |    3    |   68.7    | Test data
1763030875.434589  |    1    |   68.0    |
1763031997.8378394 |    3    |   74.0    | Highest avg
1763033513.1314034 |    4    |   62.0    |
1763033561.7310271 |    2    |   67.0    |
1763041347.2332802 |   10    |   59.0    | Latest batch
```

**All loads from:** Nov 12-13, 2025 (within 24-48 hours)

## Why This Data Is Being Discarded

1. **Mixed Code Versions:** Unknown which batches used which analyzer (LLMProfiler vs OpportunityAnalyzerAgent)
2. **Test Data Contamination:** 56% test records make distribution unreliable
3. **Small Sample Size:** 23 records insufficient for statistical baseline
4. **Inconsistent Results:** Avg scores range 59.0-74.0 across batches without known cause
5. **No Clear Before/After:** Cannot definitively attribute scores to specific code versions

## Next Steps After Cleanup

1. ✅ Clear `app_opportunities_trust` table
2. ✅ Run fresh pipeline with CURRENT code (OpportunityAnalyzerAgent)
3. ✅ Collect 20-30 opportunities with documented configuration
4. ✅ Verify score distribution matches expectations (70+ ≤3%)
5. ✅ Update production readiness assessment based on NEW data

## Files Generated

1. `pre_cleanup_schema_20251113_114846.sql` - Table schema (DDL)
2. `pre_cleanup_table_details_20251113_114846.txt` - Detailed table structure
3. `pre_cleanup_data_stats_20251113_114846.txt` - Statistical summary
4. `PRE_CLEANUP_SNAPSHOT_20251113.md` - This document

## Related Documents

- **Audit Report:** `/home/carlos/projects/redditharbor/PRODUCTION_READINESS_AUDIT_REPORT_2025-11-13.md`
- **Statistical Analysis:** `docs/architecture/OPPORTUNITY_SCORING_STATISTICAL_AUDIT_2025-11-13.md`
- **Production Readiness Memory:** `production_readiness_analysis_2025_11_13` (marked INVALID)

---

**Snapshot Complete**
**Status:** Ready for cleanup and fresh testing
**Approved By:** User confirmed old data is discardable
