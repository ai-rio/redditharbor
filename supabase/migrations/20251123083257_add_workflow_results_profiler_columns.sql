-- Migration: Add Profiler Deduplication Columns to workflow_results
-- Description: Add missing columns required by ProfilerSkipLogic for copy_profiler_analysis
-- Version: 001
-- Date: 2025-11-23
-- Task: Fix workflow_results.business_concept_id schema issue
-- Root Cause: Python code queries columns that don't exist in the table schema

-- ============================================================================
-- STEP 1: Add Business Concept ID for Deduplication
-- ============================================================================

-- This is the primary column causing the error:
-- "column workflow_results.business_concept_id does not exist"
ALTER TABLE workflow_results
ADD COLUMN IF NOT EXISTS business_concept_id BIGINT REFERENCES business_concepts(id);

-- ============================================================================
-- STEP 2: Add Submission Tracking Column
-- ============================================================================

-- submission_id is needed for insert/update operations in profiler_skip_logic.py
ALTER TABLE workflow_results
ADD COLUMN IF NOT EXISTS submission_id TEXT;

-- ============================================================================
-- STEP 3: Add AI Profile Fields
-- ============================================================================

-- These fields store the AI profiler analysis results for deduplication
ALTER TABLE workflow_results
ADD COLUMN IF NOT EXISTS value_proposition TEXT,
ADD COLUMN IF NOT EXISTS problem_description TEXT,
ADD COLUMN IF NOT EXISTS app_concept TEXT,
ADD COLUMN IF NOT EXISTS target_user TEXT,
ADD COLUMN IF NOT EXISTS monetization_model TEXT;

-- ============================================================================
-- STEP 4: Add Scoring Fields
-- ============================================================================

-- Scoring metrics from AI profiler analysis
ALTER TABLE workflow_results
ADD COLUMN IF NOT EXISTS final_score DECIMAL(5,2) CHECK (final_score >= 0 AND final_score <= 100),
ADD COLUMN IF NOT EXISTS market_demand DECIMAL(3,2) CHECK (market_demand >= 0 AND market_demand <= 1),
ADD COLUMN IF NOT EXISTS pain_intensity DECIMAL(3,2) CHECK (pain_intensity >= 0 AND pain_intensity <= 1),
ADD COLUMN IF NOT EXISTS monetization_potential DECIMAL(3,2) CHECK (monetization_potential >= 0 AND monetization_potential <= 1),
ADD COLUMN IF NOT EXISTS market_gap DECIMAL(3,2) CHECK (market_gap >= 0 AND market_gap <= 1),
ADD COLUMN IF NOT EXISTS technical_feasibility DECIMAL(3,2) CHECK (technical_feasibility >= 0 AND technical_feasibility <= 1);

-- ============================================================================
-- STEP 5: Add Deduplication Tracking Fields
-- ============================================================================

-- Track when profile was copied from primary opportunity
ALTER TABLE workflow_results
ADD COLUMN IF NOT EXISTS primary_opportunity_id UUID,
ADD COLUMN IF NOT EXISTS copy_timestamp TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ DEFAULT NOW();

-- ============================================================================
-- STEP 6: Create Indexes for Fast Lookups
-- ============================================================================

-- Index for deduplication queries (most important - directly fixes the error)
CREATE INDEX IF NOT EXISTS idx_workflow_results_business_concept_id
ON workflow_results(business_concept_id);

-- Index for finding primary profiles (not copies)
CREATE INDEX IF NOT EXISTS idx_workflow_results_primary_lookup
ON workflow_results(business_concept_id, copied_from_primary)
WHERE copied_from_primary = FALSE;

-- Index for submission lookup
CREATE INDEX IF NOT EXISTS idx_workflow_results_submission_id
ON workflow_results(submission_id)
WHERE submission_id IS NOT NULL;

-- Index for processed_at for ordering
CREATE INDEX IF NOT EXISTS idx_workflow_results_processed_at
ON workflow_results(processed_at DESC)
WHERE processed_at IS NOT NULL;

-- ============================================================================
-- STEP 7: Add Foreign Key Constraint for business_concept_id
-- ============================================================================

-- Note: The REFERENCES in the ALTER TABLE above creates the FK constraint
-- but we add an explicit name for documentation
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_workflow_results_business_concept'
        AND table_name = 'workflow_results'
    ) THEN
        ALTER TABLE workflow_results
        ADD CONSTRAINT fk_workflow_results_business_concept
        FOREIGN KEY (business_concept_id) REFERENCES business_concepts(id)
        ON DELETE SET NULL;
    END IF;
END $$;

-- ============================================================================
-- STEP 8: Add Comments for Documentation
-- ============================================================================

COMMENT ON COLUMN workflow_results.business_concept_id IS 'Foreign key to business_concepts for deduplication integration - enables copying AI profiles across duplicate submissions';
COMMENT ON COLUMN workflow_results.submission_id IS 'String-based submission ID for AI profiler workflow tracking';
COMMENT ON COLUMN workflow_results.value_proposition IS 'AI-generated value proposition from profiler analysis';
COMMENT ON COLUMN workflow_results.problem_description IS 'AI-generated problem description from profiler analysis';
COMMENT ON COLUMN workflow_results.app_concept IS 'AI-generated app concept from profiler analysis';
COMMENT ON COLUMN workflow_results.target_user IS 'AI-identified target user segment';
COMMENT ON COLUMN workflow_results.monetization_model IS 'AI-suggested monetization model';
COMMENT ON COLUMN workflow_results.final_score IS 'Overall opportunity score from AI profiler (0-100)';
COMMENT ON COLUMN workflow_results.market_demand IS 'Market demand score from AI profiler (0-1)';
COMMENT ON COLUMN workflow_results.pain_intensity IS 'Pain intensity score from AI profiler (0-1)';
COMMENT ON COLUMN workflow_results.monetization_potential IS 'Monetization potential score from AI profiler (0-1)';
COMMENT ON COLUMN workflow_results.market_gap IS 'Market gap score from AI profiler (0-1)';
COMMENT ON COLUMN workflow_results.technical_feasibility IS 'Technical feasibility score from AI profiler (0-1)';
COMMENT ON COLUMN workflow_results.primary_opportunity_id IS 'Reference to the primary opportunity if this was copied during deduplication';
COMMENT ON COLUMN workflow_results.copy_timestamp IS 'Timestamp when the profile was copied from primary';
COMMENT ON COLUMN workflow_results.processed_at IS 'Timestamp when the workflow result was processed';

-- ============================================================================
-- STEP 9: Validate Migration
-- ============================================================================

DO $$
DECLARE
    column_exists BOOLEAN;
    issue_count INTEGER := 0;
BEGIN
    RAISE NOTICE 'Validating workflow_results profiler columns migration...';

    -- Check business_concept_id column (the primary fix)
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'workflow_results'
        AND column_name = 'business_concept_id'
    ) INTO column_exists;

    IF column_exists THEN
        RAISE NOTICE '  [OK] business_concept_id column verified';
    ELSE
        RAISE WARNING '  [FAIL] business_concept_id column missing';
        issue_count := issue_count + 1;
    END IF;

    -- Check submission_id column
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'workflow_results'
        AND column_name = 'submission_id'
    ) INTO column_exists;

    IF column_exists THEN
        RAISE NOTICE '  [OK] submission_id column verified';
    ELSE
        RAISE WARNING '  [FAIL] submission_id column missing';
        issue_count := issue_count + 1;
    END IF;

    -- Check copied_from_primary column (from previous migration)
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'workflow_results'
        AND column_name = 'copied_from_primary'
    ) INTO column_exists;

    IF column_exists THEN
        RAISE NOTICE '  [OK] copied_from_primary column verified';
    ELSE
        RAISE WARNING '  [FAIL] copied_from_primary column missing';
        issue_count := issue_count + 1;
    END IF;

    -- Summary
    IF issue_count = 0 THEN
        RAISE NOTICE 'Migration validation PASSED - workflow_results ready for ProfilerSkipLogic';
    ELSE
        RAISE WARNING 'Migration validation FAILED with % issues', issue_count;
    END IF;
END $$;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
--
-- This migration adds the columns required by core/deduplication/profiler_skip_logic.py
-- for the copy_profiler_analysis() method to work correctly.
--
-- Key changes:
-- 1. Added business_concept_id - primary column that was causing the error
-- 2. Added submission_id - needed for insert operations
-- 3. Added AI profile fields (value_proposition, app_concept, etc.)
-- 4. Added scoring fields (final_score, market_demand, etc.)
-- 5. Added deduplication tracking fields (primary_opportunity_id, copy_timestamp)
-- 6. Created indexes for efficient lookups
--
-- After applying this migration, the following query will work:
--   client.table("workflow_results")
--       .select("*")
--       .eq("business_concept_id", concept_id)
--       .eq("copied_from_primary", False)
--       .execute()
