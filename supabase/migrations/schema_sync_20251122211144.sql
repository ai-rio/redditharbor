-- Schema Synchronization Migration
-- Generated: 2025-11-22T21:11:44.112263
-- Purpose: Fix schema drift detected by validation script
-- Issue: monetization_patterns table has columns in database but not in migrations

-- ============================================================================
-- STEP 1: Add Missing Monetization Enrichment Columns to monetization_patterns
-- ============================================================================

-- These columns were added manually to achieve 96.9% field coverage
-- They need to be properly documented in migrations for reproducibility

ALTER TABLE monetization_patterns
ADD COLUMN IF NOT EXISTS willingness_to_pay_score DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS customer_segment TEXT,
ADD COLUMN IF NOT EXISTS price_sensitivity_score DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS revenue_potential_score DOUBLE PRECISION;

-- ============================================================================
-- STEP 2: Add Comments for Documentation
-- ============================================================================

COMMENT ON COLUMN monetization_patterns.willingness_to_pay_score IS
'Willingness-to-pay score (0-100) indicating how likely users are to pay for this solution';

COMMENT ON COLUMN monetization_patterns.customer_segment IS
'Customer segment: B2B, B2C, Mixed, or other market categorization';

COMMENT ON COLUMN monetization_patterns.price_sensitivity_score IS
'Price sensitivity score (0-100) indicating how sensitive users are to pricing changes';

COMMENT ON COLUMN monetization_patterns.revenue_potential_score IS
'Revenue potential score (0-100) indicating the overall revenue opportunity';

-- ============================================================================
-- STEP 3: Create Indexes for Performance
-- ============================================================================

-- Indexes for the new columns to support efficient querying
CREATE INDEX IF NOT EXISTS idx_monetization_patterns_wtp_score
ON monetization_patterns(willingness_to_pay_score DESC)
WHERE willingness_to_pay_score IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_monetization_patterns_customer_segment
ON monetization_patterns(customer_segment)
WHERE customer_segment IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_monetization_patterns_revenue_potential
ON monetization_patterns(revenue_potential_score DESC)
WHERE revenue_potential_score IS NOT NULL;

-- ============================================================================
-- STEP 4: Validate Migration
-- ============================================================================

DO $$
DECLARE
    column_count INTEGER;
    expected_columns INTEGER := 12; -- Total expected columns after migration
BEGIN
    -- Count columns in monetization_patterns table
    SELECT COUNT(*) INTO column_count
    FROM information_schema.columns
    WHERE table_name = 'monetization_patterns'
    AND table_schema = 'public';

    RAISE NOTICE '✅ Monetization patterns migration validation:';
    RAISE NOTICE '  Current column count: %', column_count;
    RAISE NOTICE '  Expected column count: %', expected_columns;
    RAISE NOTICE '  Migration status: %',
        CASE WHEN column_count >= expected_columns THEN 'SUCCESS' ELSE 'INCOMPLETE' END;

    -- Verify specific columns exist
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'monetization_patterns'
               AND column_name = 'willingness_to_pay_score') THEN
        RAISE NOTICE '  ✅ willingness_to_pay_score column verified';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'monetization_patterns'
               AND column_name = 'customer_segment') THEN
        RAISE NOTICE '  ✅ customer_segment column verified';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'monetization_patterns'
               AND column_name = 'price_sensitivity_score') THEN
        RAISE NOTICE '  ✅ price_sensitivity_score column verified';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'monetization_patterns'
               AND column_name = 'revenue_potential_score') THEN
        RAISE NOTICE '  ✅ revenue_potential_score column verified';
    END IF;
END $$;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
