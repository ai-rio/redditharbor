-- Fix Cost Tracking Functions with Improved Error Handling
-- Migration to resolve SQL syntax errors and provide working alternatives
-- Created: 2025-11-14

-- First, let's drop and recreate the function with better error handling
DROP FUNCTION IF EXISTS get_cost_summary(date, date) CASCADE;

-- Recreate get_cost_summary function with improved syntax and error handling
CREATE OR REPLACE FUNCTION get_cost_summary(
    p_start_date date DEFAULT (CURRENT_DATE - INTERVAL '30 days'),
    p_end_date date DEFAULT CURRENT_DATE
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
) AS $$
BEGIN
    -- Validate input dates
    IF p_start_date > p_end_date THEN
        RAISE EXCEPTION 'Start date must be before or equal to end date';
    END IF;

    RETURN QUERY
    WITH date_range_data AS (
        SELECT
            COUNT(*) as total_count,
            COUNT(CASE WHEN cost_tracking_enabled = true THEN 1 END) as cost_enabled_count,
            COALESCE(SUM(CASE WHEN cost_tracking_enabled = true THEN llm_total_cost_usd ELSE 0 END), 0) as total_cost,
            COALESCE(AVG(CASE WHEN cost_tracking_enabled = true THEN llm_total_cost_usd END), 0) as avg_cost,
            COALESCE(SUM(CASE WHEN cost_tracking_enabled = true THEN llm_total_tokens ELSE 0 END), 0) as total_tokens,
            COALESCE(AVG(CASE WHEN cost_tracking_enabled = true THEN llm_total_tokens END), 0) as avg_tokens,
            COUNT(DISTINCT CASE WHEN cost_tracking_enabled = true AND llm_model_used IS NOT NULL THEN llm_model_used END) as distinct_models
        FROM workflow_results
        WHERE processed_at >= p_start_date AND processed_at <= p_end_date
    ),
    daily_costs AS (
        SELECT
            DATE(llm_timestamp) as cost_date,
            SUM(llm_total_cost_usd) as daily_cost
        FROM workflow_results
        WHERE cost_tracking_enabled = true
            AND llm_timestamp >= p_start_date
            AND llm_timestamp <= p_end_date
            AND llm_total_cost_usd > 0
        GROUP BY DATE(llm_timestamp)
    )
    SELECT
        d.total_count::bigint,
        d.cost_enabled_count::bigint,
        ROUND(d.total_cost::numeric, 6),
        ROUND(d.avg_cost::numeric, 6),
        d.total_tokens::bigint,
        ROUND(d.avg_tokens::numeric, 2),
        d.distinct_models::integer,
        ROUND((SELECT COALESCE(AVG(daily_cost), 0) FROM daily_costs)::numeric, 6),
        ROUND((SELECT COALESCE(MAX(daily_cost), 0) FROM daily_costs)::numeric, 6)
    FROM date_range_data d;
END;
$$ LANGUAGE plpgsql;

-- Create a simpler view-based alternative that doesn't require function calls
CREATE OR REPLACE VIEW cost_summary_simple AS
WITH daily_stats AS (
    SELECT
        DATE(llm_timestamp) as cost_date,
        COUNT(*) as daily_requests,
        SUM(llm_total_cost_usd) as daily_cost,
        SUM(llm_total_tokens) as daily_tokens,
        COUNT(DISTINCT llm_model_used) as daily_models
    FROM workflow_results
    WHERE cost_tracking_enabled = true
        AND llm_timestamp >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY DATE(llm_timestamp)
),
cumulative_stats AS (
    SELECT
        COUNT(*) as total_requests,
        COUNT(CASE WHEN cost_tracking_enabled = true THEN 1 END) as cost_enabled_requests,
        COALESCE(SUM(llm_total_cost_usd), 0) as total_cost,
        COALESCE(SUM(llm_total_tokens), 0) as total_tokens,
        COUNT(DISTINCT llm_model_used) as distinct_models,
        COALESCE(AVG(llm_total_cost_usd), 0) as avg_cost_per_request,
        COALESCE(AVG(llm_total_tokens), 0) as avg_tokens_per_request
    FROM workflow_results
    WHERE processed_at >= CURRENT_DATE - INTERVAL '30 days'
        AND processed_at <= CURRENT_DATE
)
SELECT
    c.total_requests,
    c.cost_enabled_requests,
    ROUND(c.total_cost::numeric, 6) as total_cost_usd,
    ROUND(c.avg_cost_per_request::numeric, 6) as avg_cost_per_request,
    c.total_tokens,
    ROUND(c.avg_tokens_per_request::numeric, 2) as avg_tokens_per_request,
    c.distinct_models,
    ROUND((SELECT COALESCE(AVG(daily_cost), 0) FROM daily_stats)::numeric, 6) as daily_avg_cost,
    ROUND((SELECT COALESCE(MAX(daily_cost), 0) FROM daily_stats)::numeric, 6) as peak_daily_cost,
    (SELECT COUNT(*) FROM daily_stats) as active_days
FROM cumulative_stats c;

-- Create a function for flexible date range cost analysis
CREATE OR REPLACE FUNCTION analyze_costs_by_date_range(
    p_start_date date DEFAULT (CURRENT_DATE - INTERVAL '30 days'),
    p_end_date date DEFAULT CURRENT_DATE,
    p_group_by text DEFAULT 'day' -- 'day', 'week', 'month'
)
RETURNS TABLE(
    period_start date,
    period_end date,
    total_requests bigint,
    total_cost_usd numeric,
    avg_cost_per_request numeric,
    total_tokens bigint,
    avg_tokens_per_request numeric,
    unique_models integer
) AS $$
BEGIN
    -- Validate group_by parameter
    IF p_group_by NOT IN ('day', 'week', 'month') THEN
        RAISE EXCEPTION 'group_by must be one of: day, week, month';
    END IF;

    RETURN QUERY
    SELECT
        CASE
            WHEN p_group_by = 'day' THEN DATE_TRUNC('day', DATE(llm_timestamp))::date
            WHEN p_group_by = 'week' THEN DATE_TRUNC('week', DATE(llm_timestamp))::date
            WHEN p_group_by = 'month' THEN DATE_TRUNC('month', DATE(llm_timestamp))::date
        END as period_start,
        CASE
            WHEN p_group_by = 'day' THEN DATE_TRUNC('day', DATE(llm_timestamp))::date + INTERVAL '1 day' - INTERVAL '1 second'
            WHEN p_group_by = 'week' THEN DATE_TRUNC('week', DATE(llm_timestamp))::date + INTERVAL '1 week' - INTERVAL '1 second'
            WHEN p_group_by = 'month' THEN DATE_TRUNC('month', DATE(llm_timestamp))::date + INTERVAL '1 month' - INTERVAL '1 second'
        END::date as period_end,
        COUNT(*)::bigint,
        ROUND(SUM(llm_total_cost_usd)::numeric, 6),
        ROUND(AVG(llm_total_cost_usd)::numeric, 6),
        SUM(llm_total_tokens)::bigint,
        ROUND(AVG(llm_total_tokens)::numeric, 2),
        COUNT(DISTINCT llm_model_used)::integer
    FROM workflow_results
    WHERE cost_tracking_enabled = true
        AND llm_timestamp >= p_start_date
        AND llm_timestamp <= p_end_date
        AND llm_total_cost_usd > 0
    GROUP BY
        CASE
            WHEN p_group_by = 'day' THEN DATE_TRUNC('day', DATE(llm_timestamp))
            WHEN p_group_by = 'week' THEN DATE_TRUNC('week', DATE(llm_timestamp))
            WHEN p_group_by = 'month' THEN DATE_TRUNC('month', DATE(llm_timestamp))
        END
    ORDER BY period_start;
END;
$$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON FUNCTION get_cost_summary(date, date) IS 'Returns comprehensive cost summary for specified date range with improved error handling';
COMMENT ON VIEW cost_summary_simple IS 'Simple cost summary view without function calls - good for quick analytics';
COMMENT ON FUNCTION analyze_costs_by_date_range(date, date, text) IS 'Flexible cost analysis by day/week/month with customizable date ranges';

-- Grant permissions
GRANT SELECT ON cost_summary_simple TO anon, authenticated;
GRANT EXECUTE ON FUNCTION get_cost_summary(date, date) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION analyze_costs_by_date_range(date, date, text) TO anon, authenticated;