# Cost Tracking Queries - Working Examples

This document provides working cost tracking queries that resolve the SQL syntax error with `get_cost_summary()`.

## Quick Start - Working Queries

### 1. Simple Cost Summary (Recommended)
```sql
-- This view works without function calls
SELECT * FROM cost_summary_simple;
```

### 2. Fixed get_cost_summary() Function
```sql
-- Now works with proper date handling
SELECT * FROM get_cost_summary();

-- With explicit date range
SELECT * FROM get_cost_summary(
    CURRENT_DATE - INTERVAL '30 days',
    CURRENT_DATE
);

-- With specific dates
SELECT * FROM get_cost_summary('2025-11-01'::date, '2025-11-13'::date);
```

### 3. Flexible Date Range Analysis
```sql
-- Daily cost breakdown
SELECT * FROM analyze_costs_by_date_range(
    CURRENT_DATE - INTERVAL '7 days',
    CURRENT_DATE,
    'day'
);

-- Weekly cost breakdown
SELECT * FROM analyze_costs_by_date_range(
    CURRENT_DATE - INTERVAL '4 weeks',
    CURRENT_DATE,
    'week'
);

-- Monthly cost breakdown
SELECT * FROM analyze_costs_by_date_range(
    CURRENT_DATE - INTERVAL '3 months',
    CURRENT_DATE,
    'month'
);
```

## Direct SQL Queries (No Functions Required)

### Basic Cost Overview
```sql
-- Total costs and usage statistics
SELECT
    COUNT(*) as total_opportunities,
    COUNT(CASE WHEN cost_tracking_enabled = true THEN 1 END) as cost_enabled,
    COALESCE(SUM(CASE WHEN cost_tracking_enabled = true THEN llm_total_cost_usd ELSE 0 END), 0) as total_cost_usd,
    COALESCE(AVG(CASE WHEN cost_tracking_enabled = true THEN llm_total_cost_usd END), 0) as avg_cost_usd,
    COUNT(DISTINCT llm_model_used) as unique_models
FROM workflow_results
WHERE processed_at >= CURRENT_DATE - INTERVAL '30 days';
```

### Daily Cost Trends
```sql
-- Daily cost breakdown
SELECT
    DATE(llm_timestamp) as cost_date,
    COUNT(*) as daily_requests,
    ROUND(SUM(llm_total_cost_usd)::numeric, 6) as daily_cost_usd,
    ROUND(AVG(llm_total_cost_usd)::numeric, 6) as avg_cost_per_request,
    SUM(llm_total_tokens) as daily_tokens,
    STRING_AGG(DISTINCT llm_model_used, ', ') as models_used
FROM workflow_results
WHERE cost_tracking_enabled = true
    AND llm_timestamp >= CURRENT_DATE - INTERVAL '30 days'
    AND llm_total_cost_usd > 0
GROUP BY DATE(llm_timestamp)
ORDER BY cost_date DESC;
```

### Model Performance Comparison
```sql
-- Compare costs across different models
SELECT
    llm_model_used,
    llm_provider,
    COUNT(*) as total_requests,
    ROUND(SUM(llm_total_cost_usd)::numeric, 6) as total_cost_usd,
    ROUND(AVG(llm_total_cost_usd)::numeric, 6) as avg_cost_per_request,
    SUM(llm_total_tokens) as total_tokens,
    ROUND((SUM(llm_total_cost_usd) / NULLIF(SUM(llm_total_tokens), 0)) * 1000, 6) as cost_per_1k_tokens,
    ROUND(AVG(llm_latency_seconds)::numeric, 3) as avg_latency_seconds
FROM workflow_results
WHERE cost_tracking_enabled = true
    AND llm_model_used IS NOT NULL
    AND llm_timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY llm_model_used, llm_provider
ORDER BY total_cost_usd DESC;
```

### Cost Forecasting
```sql
-- Simple cost forecast based on recent trends
WITH recent_costs AS (
    SELECT
        DATE(llm_timestamp) as cost_date,
        SUM(llm_total_cost_usd) as daily_cost
    FROM workflow_results
    WHERE cost_tracking_enabled = true
        AND llm_timestamp >= CURRENT_DATE - INTERVAL '14 days'
        AND llm_total_cost_usd > 0
    GROUP BY DATE(llm_timestamp)
),
forecast AS (
    SELECT
        AVG(daily_cost) as avg_daily_cost,
        STDDEV(daily_cost) as cost_variance
    FROM recent_costs
)
SELECT
    CURRENT_DATE + generate_series as forecast_date,
    ROUND(f.avg_daily_cost * (1 + (generate_series * 0.02))::numeric, 6) as predicted_cost_usd,
    CASE
        WHEN f.cost_variance > f.avg_daily_cost * 0.5 THEN 'HIGH VARIANCE'
        WHEN f.cost_variance > f.avg_daily_cost * 0.2 THEN 'MEDIUM VARIANCE'
        ELSE 'LOW VARIANCE'
    END as confidence_level
FROM forecast f, generate_series(1, 7);
```

## Budget Monitoring Queries

### Daily Budget Alert
```sql
-- Check if daily costs exceed budget thresholds
WITH daily_costs AS (
    SELECT
        DATE(llm_timestamp) as cost_date,
        COUNT(*) as request_count,
        ROUND(SUM(llm_total_cost_usd)::numeric, 6) as total_cost
    FROM workflow_results
    WHERE cost_tracking_enabled = true
        AND llm_timestamp >= CURRENT_DATE - INTERVAL '7 days'
    GROUP BY DATE(llm_timestamp)
)
SELECT
    cost_date,
    request_count,
    total_cost,
    CASE
        WHEN total_cost > 10.0 THEN 'HIGH - BUDGET ALERT'
        WHEN total_cost > 5.0 THEN 'MEDIUM - MONITOR'
        WHEN total_cost > 0.0 THEN 'LOW - NORMAL'
        ELSE 'NO COST'
    END as alert_level,
    CASE
        WHEN LAG(total_cost) OVER (ORDER BY cost_date) IS NULL THEN 0
        ELSE ROUND(((total_cost - LAG(total_cost) OVER (ORDER BY cost_date)) /
                   NULLIF(LAG(total_cost) OVER (ORDER BY cost_date), 0)) * 100, 2)
    END as cost_change_pct
FROM daily_costs
ORDER BY cost_date DESC;
```

### Model Cost Efficiency
```sql
-- Find most cost-effective models
SELECT
    llm_model_used,
    llm_provider,
    COUNT(*) as total_requests,
    ROUND(SUM(llm_total_cost_usd)::numeric, 6) as total_cost_usd,
    ROUND(AVG(llm_total_cost_usd)::numeric, 6) as avg_cost_per_request,
    SUM(llm_total_tokens) as total_tokens,
    ROUND((SUM(llm_total_cost_usd) / NULLIF(SUM(llm_total_tokens), 0)) * 1000, 6) as cost_per_1k_tokens,
    ROUND(AVG(final_score)::numeric, 2) as avg_quality_score,
    ROUND((AVG(final_score) / NULLIF(AVG(llm_total_cost_usd), 0)), 2) as cost_efficiency_score
FROM workflow_results
WHERE cost_tracking_enabled = true
    AND llm_model_used IS NOT NULL
    AND final_score IS NOT NULL
    AND llm_timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY llm_model_used, llm_provider
HAVING COUNT(*) >= 10  -- Only include models with sufficient data
ORDER BY cost_efficiency_score DESC;
```

## Troubleshooting

### Check if Data Exists
```sql
-- Verify cost tracking data exists
SELECT
    COUNT(*) as total_records,
    COUNT(CASE WHEN cost_tracking_enabled = true THEN 1 END) as cost_tracking_enabled,
    COUNT(CASE WHEN llm_total_cost_usd > 0 THEN 1 END) as has_cost_data,
    COUNT(CASE WHEN llm_timestamp IS NOT NULL THEN 1 END) as has_timestamp,
    MIN(llm_timestamp) as earliest_cost,
    MAX(llm_timestamp) as latest_cost
FROM workflow_results;
```

### Validate Function Definitions
```sql
-- Check if functions exist and are properly defined
SELECT
    routine_name,
    routine_type,
    data_type,
    external_language
FROM information_schema.routines
WHERE routine_name IN ('get_cost_summary', 'analyze_costs_by_date_range')
    AND routine_schema = 'public';
```

## Running the Fix

To apply the fixes and ensure all functions work:

1. **Apply the SQL fixes:**
   ```sql
   -- Run this in your Supabase SQL editor
   -- Or use: supabase db push
   ```

2. **Test with simple queries first:**
   ```sql
   SELECT * FROM cost_summary_simple;
   ```

3. **Then test the fixed function:**
   ```sql
   SELECT * FROM get_cost_summary();
   ```

## Best Practices

1. **Use the view** `cost_summary_simple` for quick analytics
2. **Use the function** `get_cost_summary()` for custom date ranges
3. **Use `analyze_costs_by_date_range()`** for detailed time-based analysis
4. **Always check if cost tracking is enabled** in your queries
5. **Handle NULL values** with COALESCE for cleaner output

These queries should resolve the SQL syntax error and provide working alternatives for cost analytics.