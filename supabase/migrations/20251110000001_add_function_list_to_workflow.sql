-- Phase 2: Add function_list Column to workflow_results
-- Part of function-count bias fix migration plan
-- Risk: LOW | Duration: ~3 hours
-- Purpose: Unify function data representation between workflow_results and app_opportunities

-- Step 1: Add function_list column to workflow_results
ALTER TABLE workflow_results
ADD COLUMN IF NOT EXISTS function_list JSONB DEFAULT NULL;

-- Step 2: Add comment for documentation
COMMENT ON COLUMN workflow_results.function_list IS 'Array of core function names (Phase 2: function-count bias fix)';

-- Step 3: Create GIN index for efficient JSONB queries
CREATE INDEX IF NOT EXISTS idx_workflow_results_function_list
ON workflow_results USING gin(function_list);

-- Step 4: Backfill function_list from app_opportunities where possible
-- Note: Currently workflow_results.opportunity_id and app_opportunities.submission_id
-- use different formats, so backfill will happen naturally as new data flows through
-- the DLT pipeline. This UPDATE is commented out for now.
--
-- Future enhancement: Add submission_id to workflow_results or opportunity_id to app_opportunities
-- to enable historical data backfill.
--
-- UPDATE workflow_results wr
-- SET function_list = ao.core_functions
-- FROM app_opportunities ao
-- WHERE wr.opportunity_id = ao.submission_id
--   AND wr.function_list IS NULL
--   AND ao.core_functions IS NOT NULL;

-- Step 5: Log backfill statistics
DO $$
DECLARE
    total_count INTEGER;
    backfilled_count INTEGER;
    null_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_count FROM workflow_results;
    SELECT COUNT(*) INTO backfilled_count FROM workflow_results WHERE function_list IS NOT NULL;
    SELECT COUNT(*) INTO null_count FROM workflow_results WHERE function_list IS NULL;

    RAISE NOTICE 'Phase 2 Migration Statistics:';
    RAISE NOTICE '  Total workflow_results: %', total_count;
    RAISE NOTICE '  With function_list: %', backfilled_count;
    RAISE NOTICE '  Still NULL: %', null_count;
    RAISE NOTICE '  Backfill rate: %%%', ROUND((backfilled_count::NUMERIC / NULLIF(total_count, 0) * 100), 2);
END $$;

-- Verification query (commented out, run manually if needed)
-- SELECT
--     COUNT(*) as total,
--     COUNT(function_list) as with_functions,
--     COUNT(*) FILTER (WHERE function_list IS NULL) as still_null,
--     ROUND(COUNT(function_list)::NUMERIC / COUNT(*) * 100, 2) as backfill_percentage
-- FROM workflow_results;
