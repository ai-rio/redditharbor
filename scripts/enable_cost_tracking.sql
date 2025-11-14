-- Enable Cost Tracking Script
-- This script helps enable cost tracking for existing workflow_results records
-- and provides sample queries for monitoring cost analytics

-- 1. Enable cost tracking for all existing records (optional)
-- Uncomment the line below if you want to enable tracking for all existing records
-- UPDATE workflow_results SET cost_tracking_enabled = true WHERE cost_tracking_enabled = false;

-- 2. Enable cost tracking for specific records (example)
-- UPDATE workflow_results
-- SET cost_tracking_enabled = true
-- WHERE opportunity_id IN ('specific-opportunity-ids');

-- 3. Check current status of cost tracking
SELECT
    'Cost Tracking Status Report' as report_title,
    COUNT(*) as total_records,
    COUNT(CASE WHEN cost_tracking_enabled = true THEN 1 END) as cost_tracking_enabled,
    COUNT(CASE WHEN cost_tracking_enabled = false THEN 1 END) as cost_tracking_disabled,
    ROUND((COUNT(CASE WHEN cost_tracking_enabled = true THEN 1 END) * 100.0 / COUNT(*)), 2) as percentage_enabled
FROM workflow_results;

-- 4. Check records with LLM data but no cost tracking enabled
SELECT
    'Records with LLM data but tracking disabled' as issue_title,
    COUNT(*) as affected_records
FROM workflow_results
WHERE llm_model_used IS NOT NULL
    AND cost_tracking_enabled = false;

-- 5. Quick cost overview (last 7 days)
SELECT
    'Last 7 Days Cost Overview' as overview_title,
    COUNT(*) as total_requests,
    COUNT(CASE WHEN cost_tracking_enabled = true THEN 1 END) as tracked_requests,
    COALESCE(SUM(llm_total_cost_usd), 0) as total_cost_usd,
    COALESCE(SUM(llm_total_tokens), 0) as total_tokens,
    COALESCE(AVG(llm_latency_seconds), 0) as avg_latency_seconds
FROM workflow_results
WHERE llm_timestamp >= CURRENT_DATE - INTERVAL '7 days';

-- 6. Model usage summary (last 30 days)
SELECT
    'Model Usage Summary (30 days)' as summary_title,
    llm_model_used,
    llm_provider,
    COUNT(*) as usage_count,
    COALESCE(SUM(llm_total_cost_usd), 0) as total_cost_usd,
    COALESCE(AVG(llm_total_cost_usd), 0) as avg_cost_usd,
    COALESCE(SUM(llm_total_tokens), 0) as total_tokens
FROM workflow_results
WHERE cost_tracking_enabled = true
    AND llm_timestamp >= CURRENT_DATE - INTERVAL '30 days'
    AND llm_model_used IS NOT NULL
GROUP BY llm_model_used, llm_provider
ORDER BY total_cost_usd DESC;