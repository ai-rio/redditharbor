-- ROLLBACK: Remove Simplicity Score and Opportunity Assessment Score
-- Purpose: Rollback migration 20251114232013 if needed
-- WARNING: This will permanently delete simplicity_score and opportunity_assessment_score columns
-- Make sure to backup data before running this rollback!

-- ==============================================================================
-- ROLLBACK STEP 1: Drop the computed opportunity_assessment_score column
-- ==============================================================================

ALTER TABLE workflow_results
DROP COLUMN IF EXISTS opportunity_assessment_score;

-- ==============================================================================
-- ROLLBACK STEP 2: Drop the index for assessment score
-- ==============================================================================

DROP INDEX IF EXISTS idx_workflow_results_opportunity_assessment_score;

-- ==============================================================================
-- ROLLBACK STEP 3: Drop the simplicity_score column
-- ==============================================================================

ALTER TABLE workflow_results
DROP COLUMN IF EXISTS simplicity_score;

-- ==============================================================================
-- ROLLBACK STEP 4: Restore old simplicity_score column (if needed)
-- ==============================================================================
-- If the old column existed as DOUBLE PRECISION, restore it
-- Note: This will NOT restore the old data, only the column structure

ALTER TABLE workflow_results
ADD COLUMN IF NOT EXISTS simplicity_score DOUBLE PRECISION;

-- ==============================================================================
-- ROLLBACK VERIFICATION
-- ==============================================================================

DO $$
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Rollback Complete: Simplicity Score & Assessment Migration';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Dropped columns:';
    RAISE NOTICE '  - opportunity_assessment_score (computed)';
    RAISE NOTICE '  - simplicity_score (NUMERIC)';
    RAISE NOTICE '';
    RAISE NOTICE 'Restored:';
    RAISE NOTICE '  - simplicity_score (DOUBLE PRECISION, empty)';
    RAISE NOTICE '';
    RAISE NOTICE 'WARNING: Old data in these columns has been permanently lost.';
    RAISE NOTICE '         Restore from backup if needed.';
    RAISE NOTICE '============================================================';
END $$;
