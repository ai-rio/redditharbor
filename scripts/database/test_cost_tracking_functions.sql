-- Test and validate cost tracking functions
-- Run this script to check if all functions work correctly

-- First, check if the function exists and its definition
SELECT
    routine_name,
    routine_type,
    data_type,
    external_language
FROM information_schema.routines
WHERE routine_name = 'get_cost_summary'
    AND routine_schema = 'public';

-- Check the function arguments
SELECT
    parameter_name,
    parameter_mode,
    data_type,
    ordinal_position
FROM information_schema.parameters
WHERE specific_name = 'get_cost_summary'
ORDER BY ordinal_position;

-- Test basic view functionality
SELECT * FROM cost_tracking_summary LIMIT 5;

-- Test the daily trends view
SELECT * FROM cost_tracking_daily_trends LIMIT 5;

-- Test the model comparison view
SELECT * FROM cost_tracking_model_comparison LIMIT 5;

-- Test calling the function with default parameters
SELECT * FROM get_cost_summary();

-- Test calling the function with explicit date parameters
SELECT * FROM get_cost_summary(
    CURRENT_DATE - INTERVAL '30 days',
    CURRENT_DATE
);

-- Test the function with a specific date range
SELECT * FROM get_cost_summary(
    '2025-11-01'::date,
    '2025-11-13'::date
);

-- Test the model comparison function
SELECT * FROM get_model_cost_comparison(7);

-- Test the forecast function
SELECT * FROM calculate_cost_forecast(3);

-- Check if there are any sample cost tracking records
SELECT
    COUNT(*) as total_records,
    COUNT(CASE WHEN cost_tracking_enabled = true THEN 1 END) as cost_tracking_records,
    COUNT(CASE WHEN llm_total_cost_usd > 0 THEN 1 END) as records_with_costs,
    MIN(llm_timestamp) as earliest_llm_call,
    MAX(llm_timestamp) as latest_llm_call,
    COUNT(DISTINCT llm_model_used) as unique_models
FROM workflow_results;

-- Sample of cost tracking records
SELECT
    id,
    workflow_name,
    app_name,
    llm_model_used,
    llm_provider,
    llm_total_cost_usd,
    llm_total_tokens,
    llm_timestamp,
    cost_tracking_enabled
FROM workflow_results
WHERE cost_tracking_enabled = true
    AND llm_total_cost_usd > 0
ORDER BY llm_timestamp DESC
LIMIT 10;