# Cost Tracking Analytics Guide

This document provides comprehensive information about the cost tracking analytics system for monitoring AI enrichment costs in RedditHarbor.

## Overview

The cost tracking system allows you to monitor and analyze the costs associated with LLM operations used for AI profile enrichment. The system tracks token usage, costs per model, latency metrics, and provides budget monitoring capabilities.

## Database Schema

### Cost Tracking Columns

The `workflow_results` table includes the following cost tracking columns:

| Column | Type | Description |
|--------|------|-------------|
| `llm_model_used` | TEXT | LLM model used for AI profile generation (e.g., claude-haiku-4.5, gpt-4o-mini) |
| `llm_provider` | TEXT | LLM provider (openrouter, openai, anthropic, etc.) |
| `llm_prompt_tokens` | INTEGER | Number of input tokens sent to LLM |
| `llm_completion_tokens` | INTEGER | Number of output tokens received from LLM |
| `llm_total_tokens` | INTEGER | Total tokens used in LLM transaction |
| `llm_input_cost_usd` | DECIMAL(10,8) | Cost for input tokens in USD |
| `llm_output_cost_usd` | DECIMAL(10,8) | Cost for output tokens in USD |
| `llm_total_cost_usd` | DECIMAL(10,8) | Total cost for LLM transaction in USD |
| `llm_latency_seconds` | DECIMAL(8,3) | LLM response time in seconds |
| `llm_timestamp` | TIMESTAMPTZ | Timestamp when LLM call was made |
| `llm_pricing_info` | JSONB | JSON with pricing details (cost per 1M tokens, etc.) |
| `cost_tracking_enabled` | BOOLEAN | Flag indicating if cost tracking is enabled for this record |

## Views and Functions

### 1. cost_tracking_summary

Provides a summary view of cost tracking data grouped by model and provider.

**Usage:**
```sql
SELECT * FROM cost_tracking_summary;
```

**Columns:**
- `analysis_date`: Current timestamp when the view was queried
- `llm_model_used`: The LLM model name
- `llm_provider`: The LLM provider
- `opportunities_processed`: Number of opportunities processed with this model
- `total_cost_usd`: Total cost in USD for this model
- `avg_cost_per_opportunity`: Average cost per opportunity
- `total_tokens`: Total tokens used
- `avg_tokens_per_opportunity`: Average tokens per opportunity
- `avg_latency_seconds`: Average response time in seconds

### 2. cost_tracking_daily_trends

Shows daily cost trends and metrics for each model.

**Usage:**
```sql
SELECT * FROM cost_tracking_daily_trends
WHERE trend_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY trend_date DESC, daily_cost_usd DESC;
```

**Columns:**
- `trend_date`: Date of the cost data
- `llm_model_used`: The LLM model name
- `llm_provider`: The LLM provider
- `daily_requests`: Number of requests made on that day
- `daily_cost_usd`: Total cost for that day
- `avg_cost_per_request`: Average cost per request
- `daily_tokens`: Total tokens used that day
- `avg_tokens_per_request`: Average tokens per request
- `avg_latency_seconds`: Average response time
- `min_cost_usd`: Minimum cost for a request that day
- `max_cost_usd`: Maximum cost for a request that day

### 3. cost_tracking_model_comparison

Provides a comparative view of all models used.

**Usage:**
```sql
SELECT * FROM cost_tracking_model_comparison;
```

**Columns:**
- `llm_model_used`: The LLM model name
- `llm_provider`: The LLM provider
- `total_requests`: Total number of requests
- `total_cost_usd`: Total cost in USD
- `avg_cost_per_request`: Average cost per request
- `total_tokens`: Total tokens used
- `avg_tokens_per_request`: Average tokens per request
- `cost_per_1k_tokens`: Cost per 1000 tokens
- `avg_latency_seconds`: Average response time
- `avg_score`: Average score from the model responses
- `first_used`: First time this model was used
- `last_used`: Last time this model was used

### 4. cost_tracking_budget_monitor

Monitors daily cost usage with alerts and trends for budget management.

**Usage:**
```sql
SELECT * FROM cost_tracking_budget_monitor;
```

**Columns:**
- `monitoring_date`: Date being monitored
- `daily_requests`: Number of requests on that date
- `daily_total_cost`: Total cost for that date
- `running_total_cost`: Running total cost over time
- `daily_tokens`: Total tokens used that date
- `running_total_tokens`: Running total tokens over time
- `models_used`: Number of different models used
- `previous_day_cost`: Cost from the previous day
- `cost_change_percentage`: Percentage change from previous day
- `usage_alert_level`: Alert level (NO_USAGE, LOW_USAGE, MEDIUM_USAGE, HIGH_USAGE)
- `cost_trend`: Trend direction (STABLE, RISING, FALLING, SPIKING)

### 5. get_model_cost_comparison(days_back)

Returns cost comparison data for different LLM models over a specified period.

**Usage:**
```sql
-- Default 30 days
SELECT * FROM get_model_cost_comparison();

-- Custom period
SELECT * FROM get_model_cost_comparison(7);
```

**Parameters:**
- `days_back`: Number of days to look back (default: 30)

**Returns:**
- `model_name`: LLM model name
- `provider`: LLM provider
- `request_count`: Number of requests
- `total_cost_usd`: Total cost in USD
- `avg_cost_per_request`: Average cost per request
- `total_tokens`: Total tokens used
- `avg_tokens_per_request`: Average tokens per request
- `cost_per_1k_tokens`: Cost per 1000 tokens
- `avg_latency_seconds`: Average response time
- `avg_score`: Average score from model responses
- `usage_percentage`: Percentage of total usage

### 6. get_cost_summary(start_date, end_date)

Returns summary statistics for cost tracking within a specified date range.

**Usage:**
```sql
-- Default 30-day period
SELECT * FROM get_cost_summary();

-- Custom date range
SELECT * FROM get_cost_summary('2025-11-01'::date, '2025-11-13'::date);
```

**Parameters:**
- `start_date`: Start date for analysis (default: 30 days ago)
- `end_date`: End date for analysis (default: today)

**Returns:**
- `total_opportunities`: Total opportunities in period
- `opportunities_with_costs`: Opportunities with cost tracking enabled
- `total_cost_usd`: Total cost in USD
- `avg_cost_per_opportunity`: Average cost per opportunity
- `total_tokens`: Total tokens used
- `avg_tokens_per_opportunity`: Average tokens per opportunity
- `models_used`: Number of different models used
- `daily_avg_cost`: Average daily cost
- `peak_daily_cost`: Peak daily cost

### 7. calculate_cost_forecast(forecast_days)

Predicts future costs based on historical usage patterns.

**Usage:**
```sql
-- Default 7-day forecast
SELECT * FROM calculate_cost_forecast();

-- Custom forecast period
SELECT * FROM calculate_cost_forecast(14);
```

**Parameters:**
- `forecast_days`: Number of days to forecast (default: 7)

**Returns:**
- `forecast_date`: Date of the forecast
- `predicted_cost_usd`: Predicted cost for that date
- `confidence_level`: Confidence level (LOW, MEDIUM, HIGH)
- `trend_direction`: Trend direction (STABLE, INCREASING, DECREASING)

## Common Queries

### 1. Get Today's Cost Summary
```sql
SELECT
    COUNT(*) as requests_today,
    SUM(llm_total_cost_usd) as total_cost_today,
    SUM(llm_total_tokens) as total_tokens_today,
    AVG(llm_latency_seconds) as avg_latency_today
FROM workflow_results
WHERE cost_tracking_enabled = true
    AND DATE(llm_timestamp) = CURRENT_DATE;
```

### 2. Compare Model Performance
```sql
SELECT * FROM get_model_cost_comparison(7)
ORDER BY avg_cost_per_request;
```

### 3. Check Budget Status
```sql
SELECT
    monitoring_date,
    daily_total_cost,
    usage_alert_level,
    cost_trend,
    cost_change_percentage
FROM cost_tracking_budget_monitor
WHERE monitoring_date >= CURRENT_DATE - INTERVAL '7 days';
```

### 4. Find Most Expensive Models
```sql
SELECT
    llm_model_used,
    llm_provider,
    COUNT(*) as usage_count,
    ROUND(AVG(llm_total_cost_usd), 6) as avg_cost,
    ROUND(AVG(llm_total_tokens), 2) as avg_tokens
FROM workflow_results
WHERE cost_tracking_enabled = true
    AND llm_timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY llm_model_used, llm_provider
ORDER BY avg_cost DESC;
```

### 5. Monitor Token Usage Trends
```sql
SELECT
    DATE(llm_timestamp) as usage_date,
    SUM(llm_prompt_tokens) as total_prompt_tokens,
    SUM(llm_completion_tokens) as total_completion_tokens,
    SUM(llm_total_cost_usd) as daily_cost
FROM workflow_results
WHERE cost_tracking_enabled = true
    AND llm_timestamp >= CURRENT_DATE - INTERVAL '14 days'
GROUP BY DATE(llm_timestamp)
ORDER BY usage_date DESC;
```

## Budget Alert Levels

The `cost_tracking_budget_monitor` view provides automated budget alerts:

- **NO_USAGE**: No usage detected ($0)
- **LOW_USAGE**: Minimal usage (>$0 to $5)
- **MEDIUM_USAGE**: Moderate usage (>$5 to $10)
- **HIGH_USAGE**: High usage (>$10)

## Cost Trend Indicators

- **STABLE**: Costs are relatively stable (-20% to +20% change)
- **RISING**: Costs are increasing (+20% to +50% change)
- **FALLING**: Costs are decreasing (> -20% change)
- **SPIKING**: Costs are rapidly increasing (> +50% change)

## Setup and Configuration

### Enable Cost Tracking

To enable cost tracking for new records, set `cost_tracking_enabled = true` when processing workflow results:

```python
# Example: Enable cost tracking in your code
workflow_result = {
    # ... other fields ...
    'cost_tracking_enabled': True,
    'llm_model_used': 'claude-haiku-4.5',
    'llm_provider': 'openrouter',
    'llm_prompt_tokens': prompt_tokens,
    'llm_completion_tokens': completion_tokens,
    'llm_total_tokens': total_tokens,
    'llm_input_cost_usd': input_cost,
    'llm_output_cost_usd': output_cost,
    'llm_total_cost_usd': total_cost,
    'llm_latency_seconds': latency,
    'llm_timestamp': datetime.utcnow()
}
```

### Update Existing Records

To enable cost tracking for existing records:

```sql
UPDATE workflow_results
SET cost_tracking_enabled = true
WHERE opportunity_id IN ('list', 'of', 'opportunity_ids');
```

## Monitoring and Maintenance

### Regular Checks

Run these queries regularly to monitor your cost tracking:

1. **Daily Cost Check**: Run `SELECT * FROM cost_tracking_budget_monitor WHERE monitoring_date = CURRENT_DATE;`

2. **Weekly Model Comparison**: Run `SELECT * FROM get_model_cost_comparison(7);`

3. **Monthly Summary**: Run `SELECT * FROM get_cost_summary();`

### Performance Considerations

- The cost tracking views are optimized with appropriate indexes
- Queries should include date ranges for better performance
- Consider archiving old data if the table grows very large

## Troubleshooting

### Common Issues

1. **Empty Results**: Ensure `cost_tracking_enabled = true` for the records you want to analyze
2. **Missing Timestamps**: Check that `llm_timestamp` is populated for cost tracking
3. **NULL Costs**: Verify that cost calculations are being performed before saving records

### Data Validation

Use this query to check data integrity:

```sql
SELECT
    COUNT(*) as total_records,
    COUNT(CASE WHEN cost_tracking_enabled THEN 1 END) as cost_enabled,
    COUNT(CASE WHEN llm_timestamp IS NOT NULL THEN 1 END) as has_timestamp,
    COUNT(CASE WHEN llm_total_cost_usd > 0 THEN 1 END) as has_cost
FROM workflow_results;
```

## API Access

You can access these views and functions through Supabase's REST API:

```bash
# Example: Get cost summary via REST API
curl -X POST 'http://127.0.0.1:54321/rest/v1/rpc/get_cost_summary' \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-11-01", "end_date": "2025-11-13"}'
```

Replace `YOUR_ANON_KEY` with your actual Supabase anonymous key.