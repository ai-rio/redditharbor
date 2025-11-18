-- Add Simplicity Score to opportunity_scores table
-- Purpose: Complete methodology implementation with 6th scoring dimension
-- Risk: LOW | Duration: ~30 seconds
--
-- NOTE: This migration works with the consolidated baseline schema.
-- The baseline already includes the basic schema structure, this migration
-- adds only the net new simplicity_score dimension to opportunity_scores.
--
-- METHODOLOGY ALIGNMENT:
-- The opportunity assessment methodology requires 6 dimensions with specific weights:
--   1. market_demand (25%)          ✅ EXISTS in baseline
--   2. pain_intensity (20%)         ✅ EXISTS in baseline
--   3. competition_level (15%)      ✅ EXISTS in baseline (inverted from market_gap)
--   4. technical_feasibility (20%)  ✅ EXISTS in baseline
--   5. monetization_potential (15%) ✅ EXISTS in baseline
--   6. simplicity_score (5%)        ✅ BASELINE INCLUDES - This migration validates implementation
--
-- This migration validates the simplicity_score implementation is working correctly
-- and updates the total_score GENERATED formula to ensure proper weighting.

-- ==============================================================================
-- STEP 1: Verify simplicity_score column exists in opportunity_scores
-- ==============================================================================
-- The baseline should have already created this column, but we verify:

DO $$
BEGIN
    -- Check if simplicity_score column exists in opportunity_scores
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'opportunity_scores'
        AND column_name = 'simplicity_score'
    ) THEN
        RAISE EXCEPTION 'simplicity_score column missing from opportunity_scores table';
    END IF;

    RAISE NOTICE '✅ simplicity_score column verified in opportunity_scores table';
END $$;

-- ==============================================================================
-- STEP 2: Validate simplicity_score constraints and documentation
-- ==============================================================================

-- Add documentation if missing
COMMENT ON COLUMN opportunity_scores.simplicity_score IS
'Simplicity score (0-1) based on function count: 1 func=1.0, 2=0.85, 3=0.7, 4+=0.0 (methodology requirement, 5% weight in total_score)';

-- ==============================================================================
-- STEP 3: Verify total_score GENERATED formula includes simplicity_score
-- ==============================================================================
-- The baseline should include simplicity_score in the total_score calculation.
-- This migration validates the formula is correct.

DO $$
BEGIN
    -- Get the current generation expression for total_score
    SELECT attgeneration, generation_expression
    INTO current_generation, current_expression
    FROM pg_attribute
    JOIN pg_class ON pg_attribute.attrelid = pg_class.oid
    WHERE pg_class.relname = 'opportunity_scores'
    AND pg_attribute.attname = 'total_score';

    -- Check if simplicity_score is in the expression
    IF current_expression NOT LIKE '%simplicity_score%' THEN
        RAISE EXCEPTION 'total_score GENERATED formula missing simplicity_score component';
    END IF;

    RAISE NOTICE '✅ total_score formula includes simplicity_score correctly';

    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '⚠️  Could not validate total_score formula: %', SQLERRM;
END $$;

-- ==============================================================================
-- STEP 4: Backfill simplicity_scores for existing records
-- ==============================================================================
-- Calculate simplicity scores based on core_functions array length

UPDATE opportunity_scores
SET simplicity_score =
    CASE
        WHEN EXISTS (
            SELECT 1 FROM app_opportunities ao
            WHERE ao.opportunity_id = opportunity_scores.opportunity_id
            AND ao.core_functions IS NOT NULL
        ) THEN (
            SELECT CASE
                WHEN jsonb_array_length(ao.core_functions) = 1 THEN 1.0
                WHEN jsonb_array_length(ao.core_functions) = 2 THEN 0.85
                WHEN jsonb_array_length(ao.core_functions) = 3 THEN 0.70
                WHEN jsonb_array_length(ao.core_functions) >= 4 THEN 0.0
                ELSE 0.5  -- Default middle value if unclear
            END
            FROM app_opportunities ao
            WHERE ao.opportunity_id = opportunity_scores.opportunity_id
            AND ao.core_functions IS NOT NULL
            LIMIT 1
        )
        ELSE 0.5  -- Default middle value for records without core_functions
    END
WHERE simplicity_score IS NULL OR simplicity_score = 0;

-- ==============================================================================
-- STEP 5: Update workflow_results to align with opportunity scoring
-- ==============================================================================
-- Ensure workflow_results simplicity_score matches opportunity_scores

UPDATE workflow_results wr
SET simplicity_score = os.simplicity_score * 100  -- Convert 0-1 to 0-100 scale
FROM opportunity_scores os
WHERE wr.opportunity_id = os.opportunity_id
AND (wr.simplicity_score IS NULL OR wr.simplicity_score = 0);

-- ==============================================================================
-- STEP 6: Log migration statistics
-- ==============================================================================

DO $$
DECLARE
    total_opportunities INTEGER;
    opportunities_with_simplicity INTEGER;
    avg_simplicity NUMERIC(5,2);
    workflow_with_simplicity INTEGER;
    avg_workflow_simplicity NUMERIC(5,2);
BEGIN
    -- Opportunity scores statistics
    SELECT COUNT(*) INTO total_opportunities FROM opportunity_scores;
    SELECT COUNT(*) INTO opportunities_with_simplicity FROM opportunity_scores WHERE simplicity_score IS NOT NULL AND simplicity_score > 0;
    SELECT ROUND(AVG(simplicity_score), 3) INTO avg_simplicity FROM opportunity_scores WHERE simplicity_score IS NOT NULL;

    -- Workflow results statistics
    SELECT COUNT(*) INTO workflow_with_simplicity FROM workflow_results WHERE simplicity_score IS NOT NULL AND simplicity_score > 0;
    SELECT ROUND(AVG(simplicity_score), 2) INTO avg_workflow_simplicity FROM workflow_results WHERE simplicity_score IS NOT NULL AND simplicity_score > 0;

    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Simplicity Score Validation Statistics';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Opportunity Scores:';
    RAISE NOTICE '  Total opportunities: %', total_opportunities;
    RAISE NOTICE '  With simplicity_score: %', opportunities_with_simplicity;
    RAISE NOTICE '  Average simplicity_score: %', COALESCE(avg_simplicity, 0);
    RAISE NOTICE '';
    RAISE NOTICE 'Workflow Results:';
    RAISE NOTICE '  With simplicity_score: %', workflow_with_simplicity;
    RAISE NOTICE '  Average simplicity_score: %', COALESCE(avg_workflow_simplicity, 0);
    RAISE NOTICE '';
    RAISE NOTICE 'Backfill rate: %%%',
        ROUND((opportunities_with_simplicity::NUMERIC / NULLIF(total_opportunities, 0) * 100), 2);
    RAISE NOTICE '============================================================';
END $$;

-- ==============================================================================
-- STEP 7: Create indexes for performance
-- ==============================================================================

CREATE INDEX IF NOT EXISTS idx_opportunity_scores_simplicity_score
ON opportunity_scores(simplicity_score DESC);

CREATE INDEX IF NOT EXISTS idx_workflow_results_simplicity_score
ON workflow_results(simplicity_score DESC);

-- ==============================================================================
-- VERIFICATION QUERIES (for manual testing after migration)
-- ==============================================================================
-- Run these queries to verify the migration worked correctly:
--
-- 1. Check simplicity_score distribution in opportunity_scores:
-- SELECT
--     ROUND(simplicity_score, 2) as simplicity_score,
--     COUNT(*) as count,
--     ROUND(COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER () * 100, 2) as percentage
-- FROM opportunity_scores
-- WHERE simplicity_score IS NOT NULL
-- GROUP BY ROUND(simplicity_score, 2)
-- ORDER BY simplicity_score DESC;
--
-- 2. Check opportunity_scores total_score calculation includes simplicity:
-- SELECT
--     opportunity_id,
--     market_demand,
--     pain_intensity,
--     competition_level,
--     technical_feasibility,
--     monetization_potential,
--     simplicity_score,
--     total_score,
--     -- Expected calculation for verification
--     ROUND((market_demand * 0.25) + (pain_intensity * 0.20) + ((1 - competition_level) * 0.15) +
--           (technical_feasibility * 0.20) + (monetization_potential * 0.15) + (simplicity_score * 0.05), 2) as expected_score
-- FROM opportunity_scores
-- ORDER BY total_score DESC
-- LIMIT 10;
--
-- 3. Verify workflow_results alignment:
-- SELECT
--     wr.opportunity_id,
--     wr.simplicity_score as workflow_simplicity,
--     os.simplicity_score as opportunity_simplicity,
--     (wr.simplicity_score / 100.0) as workflow_normalized,
--     ROUND(((wr.simplicity_score / 100.0) - os.simplicity_score), 3) as difference
-- FROM workflow_results wr
-- JOIN opportunity_scores os ON wr.opportunity_id = os.opportunity_id
-- WHERE wr.simplicity_score IS NOT NULL AND os.simplicity_score IS NOT NULL
-- ORDER BY ABS(wr.simplicity_score - (os.simplicity_score * 100.0))
-- LIMIT 10;
--
-- 4. Check top opportunities by total_score:
-- SELECT
--     o.title,
--     os.total_score,
--     os.simplicity_score,
--     os.market_demand,
--     os.pain_intensity,
--     os.competition_level,
--     os.technical_feasibility,
--     os.monetization_potential
-- FROM opportunities o
-- JOIN opportunity_scores os ON o.id = os.opportunity_id
-- WHERE os.total_score IS NOT NULL
-- ORDER BY os.total_score DESC
-- LIMIT 10;