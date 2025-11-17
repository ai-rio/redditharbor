-- Add Simplicity Score (6th Dimension) and Opportunity Assessment Score
-- Purpose: Complete methodology implementation with all 6 scoring dimensions
-- Risk: LOW | Duration: ~30 seconds
--
-- METHODOLOGY ALIGNMENT:
-- The opportunity assessment methodology requires 6 dimensions with specific weights:
--   1. market_demand (20%)          ✅ EXISTS
--   2. pain_intensity (25%)         ✅ EXISTS
--   3. monetization_potential (20%) ✅ EXISTS
--   4. market_gap (10%)             ✅ EXISTS
--   5. technical_feasibility (5%)   ✅ EXISTS
--   6. simplicity_score (20%)       ❌ MISSING - THIS MIGRATION
--
-- This migration adds the missing simplicity_score dimension and creates a computed
-- opportunity_assessment_score that consolidates all 6 dimensions with proper weights.

-- ==============================================================================
-- STEP 1: Drop existing simplicity_score column (if exists with wrong type)
-- ==============================================================================
-- Current schema shows simplicity_score as DOUBLE PRECISION, but methodology
-- requires NUMERIC(5,2) for consistency with other dimensions (0-100 range)

ALTER TABLE workflow_results
DROP COLUMN IF EXISTS simplicity_score;

-- ==============================================================================
-- STEP 2: Add simplicity_score with correct type and constraints
-- ==============================================================================
-- Simplicity score is based on function count:
--   - 1 function  = 100.0 (single-purpose, ultra-simple)
--   - 2 functions = 85.0  (focused, but not single-purpose)
--   - 3 functions = 70.0  (moderate complexity)
--   - 4+ functions = 0.0  (high complexity, disqualified)

ALTER TABLE workflow_results
ADD COLUMN simplicity_score NUMERIC(5,2)
CONSTRAINT workflow_results_simplicity_score_check
CHECK (simplicity_score >= 0 AND simplicity_score <= 100);

-- Add documentation
COMMENT ON COLUMN workflow_results.simplicity_score IS
'Simplicity score (0-100) based on function count: 1 func=100, 2=85, 3=70, 4+=0 (methodology requirement, 20% weight)';

-- ==============================================================================
-- STEP 3: Backfill simplicity_score from existing function_count data
-- ==============================================================================
-- Use function_list if available (new data), fallback to function_count (legacy)

UPDATE workflow_results
SET simplicity_score = CASE
    -- Prefer function_list (jsonb array length) over function_count for newer records
    WHEN function_list IS NOT NULL THEN
        CASE
            WHEN jsonb_array_length(function_list) = 1 THEN 100.0
            WHEN jsonb_array_length(function_list) = 2 THEN 85.0
            WHEN jsonb_array_length(function_list) = 3 THEN 70.0
            WHEN jsonb_array_length(function_list) >= 4 THEN 0.0
            ELSE 0.0
        END
    -- Fallback to function_count for older records
    WHEN function_count IS NOT NULL THEN
        CASE
            WHEN function_count = 1 THEN 100.0
            WHEN function_count = 2 THEN 85.0
            WHEN function_count = 3 THEN 70.0
            WHEN function_count >= 4 THEN 0.0
            ELSE 0.0
        END
    -- If both are NULL, set to 0.0 (safest default for scoring)
    ELSE 0.0
END
WHERE simplicity_score IS NULL;

-- ==============================================================================
-- STEP 4: Add opportunity_assessment_score as computed column
-- ==============================================================================
-- This consolidates all 6 dimensions into a single weighted score (0-100)
-- Formula per methodology:
--   market_demand * 0.20 +
--   pain_intensity * 0.25 +
--   monetization_potential * 0.20 +
--   market_gap * 0.10 +
--   technical_feasibility * 0.05 +
--   simplicity_score * 0.20
--
-- Total weights: 0.20 + 0.25 + 0.20 + 0.10 + 0.05 + 0.20 = 1.00 ✓

ALTER TABLE workflow_results
ADD COLUMN opportunity_assessment_score NUMERIC(5,2)
GENERATED ALWAYS AS (
    COALESCE(market_demand, 0) * 0.20 +
    COALESCE(pain_intensity, 0) * 0.25 +
    COALESCE(monetization_potential, 0) * 0.20 +
    COALESCE(market_gap, 0) * 0.10 +
    COALESCE(technical_feasibility, 0) * 0.05 +
    COALESCE(simplicity_score, 0) * 0.20
) STORED;

-- Add documentation
COMMENT ON COLUMN workflow_results.opportunity_assessment_score IS
'Total opportunity score (0-100) following methodology weights: market_demand(20%) + pain_intensity(25%) + monetization_potential(20%) + market_gap(10%) + technical_feasibility(5%) + simplicity_score(20%)';

-- ==============================================================================
-- STEP 5: Create index for efficient sorting/filtering by assessment score
-- ==============================================================================

CREATE INDEX IF NOT EXISTS idx_workflow_results_opportunity_assessment_score
ON workflow_results(opportunity_assessment_score DESC);

-- ==============================================================================
-- STEP 6: Log migration statistics
-- ==============================================================================

DO $$
DECLARE
    total_count INTEGER;
    with_simplicity INTEGER;
    with_assessment INTEGER;
    null_simplicity INTEGER;
    avg_assessment NUMERIC(5,2);
    max_assessment NUMERIC(5,2);
    min_assessment NUMERIC(5,2);
BEGIN
    SELECT COUNT(*) INTO total_count FROM workflow_results;
    SELECT COUNT(*) INTO with_simplicity FROM workflow_results WHERE simplicity_score IS NOT NULL;
    SELECT COUNT(*) INTO with_assessment FROM workflow_results WHERE opportunity_assessment_score IS NOT NULL;
    SELECT COUNT(*) INTO null_simplicity FROM workflow_results WHERE simplicity_score IS NULL;

    SELECT
        ROUND(AVG(opportunity_assessment_score), 2),
        ROUND(MAX(opportunity_assessment_score), 2),
        ROUND(MIN(opportunity_assessment_score), 2)
    INTO avg_assessment, max_assessment, min_assessment
    FROM workflow_results
    WHERE opportunity_assessment_score IS NOT NULL;

    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Simplicity Score & Assessment Migration Statistics';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Total workflow_results records: %', total_count;
    RAISE NOTICE 'Records with simplicity_score: %', with_simplicity;
    RAISE NOTICE 'Records with NULL simplicity_score: %', null_simplicity;
    RAISE NOTICE 'Records with opportunity_assessment_score: %', with_assessment;
    RAISE NOTICE '';
    RAISE NOTICE 'Opportunity Assessment Score Statistics:';
    RAISE NOTICE '  Average: %', COALESCE(avg_assessment, 0);
    RAISE NOTICE '  Maximum: %', COALESCE(max_assessment, 0);
    RAISE NOTICE '  Minimum: %', COALESCE(min_assessment, 0);
    RAISE NOTICE '';
    RAISE NOTICE 'Backfill rate: %%%',
        ROUND((with_simplicity::NUMERIC / NULLIF(total_count, 0) * 100), 2);
    RAISE NOTICE '============================================================';
END $$;

-- ==============================================================================
-- VERIFICATION QUERIES (for manual testing after migration)
-- ==============================================================================
-- Run these queries to verify the migration worked correctly:
--
-- 1. Check simplicity_score distribution:
-- SELECT
--     simplicity_score,
--     COUNT(*) as record_count,
--     ROUND(COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER () * 100, 2) as percentage
-- FROM workflow_results
-- WHERE simplicity_score IS NOT NULL
-- GROUP BY simplicity_score
-- ORDER BY simplicity_score DESC;
--
-- 2. Check opportunity_assessment_score range and distribution:
-- SELECT
--     MIN(opportunity_assessment_score) as min_score,
--     MAX(opportunity_assessment_score) as max_score,
--     ROUND(AVG(opportunity_assessment_score), 2) as avg_score,
--     ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY opportunity_assessment_score), 2) as median_score,
--     ROUND(STDDEV(opportunity_assessment_score), 2) as std_dev
-- FROM workflow_results
-- WHERE opportunity_assessment_score IS NOT NULL;
--
-- 3. Compare function_count vs simplicity_score (validation):
-- SELECT
--     COALESCE(jsonb_array_length(function_list), function_count) as func_count,
--     simplicity_score,
--     COUNT(*) as record_count
-- FROM workflow_results
-- GROUP BY COALESCE(jsonb_array_length(function_list), function_count), simplicity_score
-- ORDER BY func_count;
--
-- 4. Top 10 opportunities by new assessment score:
-- SELECT
--     app_name,
--     opportunity_id,
--     simplicity_score,
--     opportunity_assessment_score,
--     final_score as legacy_score,
--     market_demand,
--     pain_intensity,
--     monetization_potential,
--     market_gap,
--     technical_feasibility,
--     processed_at
-- FROM workflow_results
-- WHERE opportunity_assessment_score IS NOT NULL
-- ORDER BY opportunity_assessment_score DESC
-- LIMIT 10;
--
-- 5. Check for any NULL values that shouldn't be NULL:
-- SELECT
--     COUNT(*) FILTER (WHERE market_demand IS NULL) as null_market_demand,
--     COUNT(*) FILTER (WHERE pain_intensity IS NULL) as null_pain_intensity,
--     COUNT(*) FILTER (WHERE monetization_potential IS NULL) as null_monetization,
--     COUNT(*) FILTER (WHERE market_gap IS NULL) as null_market_gap,
--     COUNT(*) FILTER (WHERE technical_feasibility IS NULL) as null_technical,
--     COUNT(*) FILTER (WHERE simplicity_score IS NULL) as null_simplicity,
--     COUNT(*) FILTER (WHERE opportunity_assessment_score IS NULL) as null_assessment
-- FROM workflow_results;
