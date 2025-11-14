-- Fix Cost Tracking Views and Functions
-- Migration to repair broken cost analytics functionality
-- Created: 2025-11-13

-- Drop existing broken views and functions to recreate them correctly
DROP VIEW IF EXISTS cost_tracking_summary CASCADE;
DROP VIEW IF EXISTS cost_tracking_daily_trends CASCADE;
DROP VIEW IF EXISTS cost_tracking_model_comparison CASCADE;
DROP FUNCTION IF EXISTS get_model_cost_comparison(integer) CASCADE;
DROP FUNCTION IF EXISTS get_cost_summary(date, date) CASCADE;
DROP FUNCTION IF EXISTS calculate_cost_forecast(integer) CASCADE;

-- Recreate cost_tracking_summary view
CREATE OR REPLACE VIEW cost_tracking_summary AS
SELECT
    CURRENT_DATE as analysis_date,
    llm_model_used,
    llm_provider,
    COUNT(*) as opportunities_processed,
    ROUND(SUM(llm_total_cost_usd)::numeric, 6) as total_cost_usd,
    ROUND(AVG(llm_total_cost_usd)::numeric, 6) as avg_cost_per_opportunity,
    SUM(llm_total_tokens) as total_tokens,
    ROUND(AVG(llm_total_tokens)::numeric, 2) as avg_tokens_per_opportunity,
    ROUND(AVG(llm_latency_seconds)::numeric, 3) as avg_latency_seconds
FROM workflow_results
WHERE cost_tracking_enabled = true
    AND llm_model_used IS NOT NULL
GROUP BY llm_model_used, llm_provider;

-- Create cost_tracking_daily_trends view
CREATE OR REPLACE VIEW cost_tracking_daily_trends AS
SELECT
    DATE(llm_timestamp) as trend_date,
    llm_model_used,
    llm_provider,
    COUNT(*) as daily_requests,
    ROUND(SUM(llm_total_cost_usd)::numeric, 6) as daily_cost_usd,
    ROUND(AVG(llm_total_cost_usd)::numeric, 6) as avg_cost_per_request,
    SUM(llm_total_tokens) as daily_tokens,
    ROUND(AVG(llm_total_tokens)::numeric, 2) as avg_tokens_per_request,
    ROUND(AVG(llm_latency_seconds)::numeric, 3) as avg_latency_seconds,
    MIN(llm_total_cost_usd) as min_cost_usd,
    MAX(llm_total_cost_usd) as max_cost_usd
FROM workflow_results
WHERE cost_tracking_enabled = true
    AND llm_model_used IS NOT NULL
    AND llm_timestamp IS NOT NULL
GROUP BY DATE(llm_timestamp), llm_model_used, llm_provider
ORDER BY trend_date DESC, daily_cost_usd DESC;

-- Create cost_tracking_model_comparison view
CREATE OR REPLACE VIEW cost_tracking_model_comparison AS
SELECT
    llm_model_used,
    llm_provider,
    COUNT(*) as total_requests,
    ROUND(SUM(llm_total_cost_usd)::numeric, 6) as total_cost_usd,
    ROUND(AVG(llm_total_cost_usd)::numeric, 6) as avg_cost_per_request,
    SUM(llm_total_tokens) as total_tokens,
    ROUND(AVG(llm_total_tokens)::numeric, 2) as avg_tokens_per_request,
    ROUND((SUM(llm_total_cost_usd) / NULLIF(SUM(llm_total_tokens), 0)) * 1000, 6) as cost_per_1k_tokens,
    ROUND(AVG(llm_latency_seconds)::numeric, 3) as avg_latency_seconds,
    ROUND(AVG(final_score)::numeric, 2) as avg_score,
    MIN(llm_timestamp) as first_used,
    MAX(llm_timestamp) as last_used
FROM workflow_results
WHERE cost_tracking_enabled = true
    AND llm_model_used IS NOT NULL
GROUP BY llm_model_used, llm_provider
ORDER BY total_cost_usd DESC;

-- Create the missing cost_tracking_budget_monitor view
CREATE OR REPLACE VIEW cost_tracking_budget_monitor AS
WITH daily_costs AS (
    SELECT
        DATE(llm_timestamp) as cost_date,
        COUNT(*) as daily_requests,
        ROUND(SUM(llm_total_cost_usd)::numeric, 6) as daily_total_cost,
        SUM(llm_total_tokens) as daily_tokens,
        COUNT(DISTINCT llm_model_used) as models_used
    FROM workflow_results
    WHERE cost_tracking_enabled = true
        AND llm_timestamp IS NOT NULL
        AND llm_timestamp >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY DATE(llm_timestamp)
),
running_totals AS (
    SELECT
        cost_date,
        daily_requests,
        daily_total_cost,
        daily_tokens,
        models_used,
        SUM(daily_total_cost) OVER (ORDER BY cost_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as running_total_cost,
        SUM(daily_tokens) OVER (ORDER BY cost_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as running_total_tokens,
        LAG(daily_total_cost, 1) OVER (ORDER BY cost_date) as previous_day_cost,
        CASE
            WHEN LAG(daily_total_cost, 1) OVER (ORDER BY cost_date) IS NULL THEN 0
            ELSE ROUND(((daily_total_cost - LAG(daily_total_cost, 1) OVER (ORDER BY cost_date)) /
                       NULLIF(LAG(daily_total_cost, 1) OVER (ORDER BY cost_date), 0)) * 100, 2)
        END as cost_change_percentage
    FROM daily_costs
)
SELECT
    cost_date as monitoring_date,
    daily_requests,
    daily_total_cost,
    running_total_cost,
    daily_tokens,
    running_total_tokens,
    models_used,
    previous_day_cost,
    cost_change_percentage,
    CASE
        WHEN daily_total_cost > 10.0 THEN 'HIGH_USAGE'
        WHEN daily_total_cost > 5.0 THEN 'MEDIUM_USAGE'
        WHEN daily_total_cost > 0.0 THEN 'LOW_USAGE'
        ELSE 'NO_USAGE'
    END as usage_alert_level,
    CASE
        WHEN cost_change_percentage > 50 THEN 'SPIKING'
        WHEN cost_change_percentage > 20 THEN 'RISING'
        WHEN cost_change_percentage < -20 THEN 'FALLING'
        ELSE 'STABLE'
    END as cost_trend
FROM running_totals
ORDER BY cost_date DESC;

-- Recreate get_model_cost_comparison function with correct return types
CREATE OR REPLACE FUNCTION get_model_cost_comparison(days_back integer DEFAULT 30)
RETURNS TABLE(
    model_name text,
    provider text,
    request_count bigint,
    total_cost_usd numeric,
    avg_cost_per_request numeric,
    total_tokens bigint,
    avg_tokens_per_request numeric,
    cost_per_1k_tokens numeric,
    avg_latency_seconds numeric,
    avg_score numeric,
    usage_percentage numeric
) LANGUAGE plpgsql AS $$
DECLARE
    total_requests BIGINT;
BEGIN
    -- Get total requests for percentage calculation
    SELECT COUNT(*) INTO total_requests
    FROM workflow_results
    WHERE cost_tracking_enabled = true
        AND llm_timestamp >= CURRENT_DATE - INTERVAL '1 day' * days_back;

    RETURN QUERY
    SELECT
        llm_model_used::text,
        llm_provider::text,
        COUNT(*)::bigint,
        ROUND(SUM(llm_total_cost_usd)::numeric, 6),
        ROUND(AVG(llm_total_cost_usd)::numeric, 6),
        SUM(llm_total_tokens)::bigint,
        ROUND(AVG(llm_total_tokens)::numeric, 2),
        ROUND((SUM(llm_total_cost_usd) / NULLIF(SUM(llm_total_tokens), 0)) * 1000, 6),
        ROUND(AVG(llm_latency_seconds)::numeric, 3),
        ROUND(AVG(final_score)::numeric, 2),
        ROUND((COUNT(*)::DECIMAL / NULLIF(total_requests, 0)) * 100, 2)
    FROM workflow_results
    WHERE cost_tracking_enabled = true
        AND llm_model_used IS NOT NULL
        AND llm_timestamp >= CURRENT_DATE - INTERVAL '1 day' * days_back
    GROUP BY llm_model_used, llm_provider
    ORDER BY total_cost_usd DESC;
END;
$$;

-- Recreate get_cost_summary function
CREATE OR REPLACE FUNCTION get_cost_summary(
    start_date date DEFAULT (CURRENT_DATE - INTERVAL '30 days'),
    end_date date DEFAULT CURRENT_DATE
)
RETURNS TABLE(
    total_opportunities bigint,
    opportunities_with_costs bigint,
    total_cost_usd numeric,
    avg_cost_per_opportunity numeric,
    total_tokens bigint,
    avg_tokens_per_opportunity numeric,
    models_used integer,
    daily_avg_cost numeric,
    peak_daily_cost numeric
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*) FROM workflow_results WHERE processed_at >= start_date AND processed_at <= end_date)::bigint,
        (SELECT COUNT(*) FROM workflow_results WHERE cost_tracking_enabled = true AND processed_at >= start_date AND processed_at <= end_date)::bigint,
        COALESCE((SELECT ROUND(SUM(llm_total_cost_usd)::numeric, 6) FROM workflow_results WHERE cost_tracking_enabled = true AND processed_at >= start_date AND processed_at <= end_date), 0),
        COALESCE((SELECT ROUND(AVG(llm_total_cost_usd)::numeric, 6) FROM workflow_results WHERE cost_tracking_enabled = true AND processed_at >= start_date AND processed_at <= end_date), 0),
        COALESCE((SELECT SUM(llm_total_tokens) FROM workflow_results WHERE cost_tracking_enabled = true AND processed_at >= start_date AND processed_at <= end_date), 0)::bigint,
        COALESCE((SELECT ROUND(AVG(llm_total_tokens)::numeric, 2) FROM workflow_results WHERE cost_tracking_enabled = true AND processed_at >= start_date AND processed_at <= end_date), 0),
        (SELECT COUNT(DISTINCT llm_model_used) FROM workflow_results WHERE cost_tracking_enabled = true AND processed_at >= start_date AND processed_at <= end_date AND llm_model_used IS NOT NULL)::integer,
        COALESCE((SELECT ROUND(AVG(daily_cost)::numeric, 6) FROM (
            SELECT DATE(llm_timestamp) as dt, SUM(llm_total_cost_usd) as daily_cost
            FROM workflow_results
            WHERE cost_tracking_enabled = true
                AND llm_timestamp >= start_date
                AND llm_timestamp <= end_date
            GROUP BY DATE(llm_timestamp)
        ) daily_costs), 0),
        COALESCE((SELECT ROUND(MAX(daily_cost)::numeric, 6) FROM (
            SELECT DATE(llm_timestamp) as dt, SUM(llm_total_cost_usd) as daily_cost
            FROM workflow_results
            WHERE cost_tracking_enabled = true
                AND llm_timestamp >= start_date
                AND llm_timestamp <= end_date
            GROUP BY DATE(llm_timestamp)
        ) daily_costs), 0);
END;
$$;

-- Recreate calculate_cost_forecast function
CREATE OR REPLACE FUNCTION calculate_cost_forecast(forecast_days integer DEFAULT 7)
RETURNS TABLE(
    forecast_date date,
    predicted_cost_usd numeric,
    confidence_level text,
    trend_direction text
) LANGUAGE plpgsql AS $$
DECLARE
    avg_daily_cost numeric;
    cost_variance numeric;
    trend_slope numeric;
BEGIN
    -- Calculate recent average and variance
    SELECT AVG(daily_cost), STDDEV(daily_cost) INTO avg_daily_cost, cost_variance
    FROM (
        SELECT DATE(llm_timestamp) as dt, SUM(llm_total_cost_usd) as daily_cost
        FROM workflow_results
        WHERE cost_tracking_enabled = true
            AND llm_timestamp >= CURRENT_DATE - INTERVAL '14 days'
        GROUP BY DATE(llm_timestamp)
    ) recent_costs;

    -- Simple trend calculation
    SELECT
        CORR(EXTRACT(EPOCH FROM dt), daily_cost) INTO trend_slope
    FROM (
        SELECT DATE(llm_timestamp) as dt, SUM(llm_total_cost_usd) as daily_cost
        FROM workflow_results
        WHERE cost_tracking_enabled = true
            AND llm_timestamp >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY DATE(llm_timestamp)
    ) recent_trend;

    RETURN QUERY
    SELECT
        CURRENT_DATE + generate_series,
        ROUND(avg_daily_cost * (1 + (trend_slope * 0.1 * generate_series))::numeric, 6),
        CASE
            WHEN cost_variance > avg_daily_cost * 0.5 THEN 'LOW'
            WHEN cost_variance > avg_daily_cost * 0.2 THEN 'MEDIUM'
            ELSE 'HIGH'
        END,
        CASE
            WHEN trend_slope > 0.1 THEN 'INCREASING'
            WHEN trend_slope < -0.1 THEN 'DECREASING'
            ELSE 'STABLE'
        END
    FROM generate_series(1, forecast_days);
END;
$$;

-- Add comments for documentation
COMMENT ON VIEW cost_tracking_budget_monitor IS 'Monitors daily cost usage with alerts and trends for budget management';
COMMENT ON FUNCTION get_model_cost_comparison(integer) IS 'Returns cost comparison data for different LLM models over specified period';
COMMENT ON FUNCTION get_cost_summary(date, date) IS 'Returns summary statistics for cost tracking within specified date range';
COMMENT ON FUNCTION calculate_cost_forecast(integer) IS 'Predicts future costs based on historical usage patterns';