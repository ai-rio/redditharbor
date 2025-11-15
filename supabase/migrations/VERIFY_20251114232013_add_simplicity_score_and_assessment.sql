-- VERIFICATION QUERIES: Simplicity Score & Assessment Migration
-- Purpose: Comprehensive validation of migration 20251114232013
-- Usage: Run these queries after applying the migration to verify correctness

-- ==============================================================================
-- 1. SCHEMA VERIFICATION: Check columns exist with correct types
-- ==============================================================================

SELECT
    column_name,
    data_type,
    character_maximum_length,
    numeric_precision,
    numeric_scale,
    is_nullable,
    column_default,
    generation_expression IS NOT NULL as is_computed
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'workflow_results'
  AND column_name IN ('simplicity_score', 'opportunity_assessment_score')
ORDER BY column_name;

-- Expected output:
-- simplicity_score: NUMERIC(5,2), nullable=YES, is_computed=false
-- opportunity_assessment_score: NUMERIC(5,2), nullable=YES, is_computed=true

-- ==============================================================================
-- 2. CONSTRAINT VERIFICATION: Check simplicity_score constraint exists
-- ==============================================================================

SELECT
    con.conname as constraint_name,
    pg_get_constraintdef(con.oid) as constraint_definition
FROM pg_constraint con
JOIN pg_class rel ON rel.oid = con.conrelid
JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
WHERE nsp.nspname = 'public'
  AND rel.relname = 'workflow_results'
  AND con.conname LIKE '%simplicity_score%';

-- Expected: workflow_results_simplicity_score_check with CHECK (simplicity_score >= 0 AND simplicity_score <= 100)

-- ==============================================================================
-- 3. INDEX VERIFICATION: Check assessment score index exists
-- ==============================================================================

SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename = 'workflow_results'
  AND indexname = 'idx_workflow_results_opportunity_assessment_score';

-- Expected: idx_workflow_results_opportunity_assessment_score with DESC ordering

-- ==============================================================================
-- 4. DATA DISTRIBUTION: Check simplicity_score values match function counts
-- ==============================================================================

SELECT
    COALESCE(jsonb_array_length(function_list), function_count) as func_count,
    simplicity_score,
    COUNT(*) as record_count,
    ROUND(COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER () * 100, 2) as percentage
FROM workflow_results
WHERE simplicity_score IS NOT NULL
GROUP BY COALESCE(jsonb_array_length(function_list), function_count), simplicity_score
ORDER BY func_count;

-- Expected mappings:
-- func_count=1 → simplicity_score=100.0
-- func_count=2 → simplicity_score=85.0
-- func_count=3 → simplicity_score=70.0
-- func_count>=4 → simplicity_score=0.0

-- ==============================================================================
-- 5. BACKFILL COMPLETENESS: Check for NULL values
-- ==============================================================================

SELECT
    COUNT(*) as total_records,
    COUNT(simplicity_score) as with_simplicity_score,
    COUNT(*) - COUNT(simplicity_score) as null_simplicity_score,
    COUNT(opportunity_assessment_score) as with_assessment_score,
    COUNT(*) - COUNT(opportunity_assessment_score) as null_assessment_score,
    ROUND(COUNT(simplicity_score)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 2) as simplicity_backfill_pct,
    ROUND(COUNT(opportunity_assessment_score)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 2) as assessment_backfill_pct
FROM workflow_results;

-- Expected: High backfill percentages (>95%) for both columns

-- ==============================================================================
-- 6. ASSESSMENT SCORE CALCULATION: Verify formula correctness
-- ==============================================================================

SELECT
    app_name,
    opportunity_id,
    market_demand,
    pain_intensity,
    monetization_potential,
    market_gap,
    technical_feasibility,
    simplicity_score,
    opportunity_assessment_score as computed_score,
    -- Manual calculation for verification
    ROUND(
        COALESCE(market_demand, 0) * 0.20 +
        COALESCE(pain_intensity, 0) * 0.25 +
        COALESCE(monetization_potential, 0) * 0.20 +
        COALESCE(market_gap, 0) * 0.10 +
        COALESCE(technical_feasibility, 0) * 0.05 +
        COALESCE(simplicity_score, 0) * 0.20,
        2
    ) as manual_calculation,
    -- Check if they match
    CASE
        WHEN ABS(opportunity_assessment_score - (
            COALESCE(market_demand, 0) * 0.20 +
            COALESCE(pain_intensity, 0) * 0.25 +
            COALESCE(monetization_potential, 0) * 0.20 +
            COALESCE(market_gap, 0) * 0.10 +
            COALESCE(technical_feasibility, 0) * 0.05 +
            COALESCE(simplicity_score, 0) * 0.20
        )) < 0.01 THEN 'PASS'
        ELSE 'FAIL'
    END as verification_status
FROM workflow_results
WHERE opportunity_assessment_score IS NOT NULL
LIMIT 20;

-- Expected: All records should have verification_status='PASS'

-- ==============================================================================
-- 7. SCORE RANGE VALIDATION: Check assessment score is within 0-100
-- ==============================================================================

SELECT
    MIN(opportunity_assessment_score) as min_score,
    MAX(opportunity_assessment_score) as max_score,
    ROUND(AVG(opportunity_assessment_score), 2) as avg_score,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY opportunity_assessment_score), 2) as q1,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY opportunity_assessment_score), 2) as median,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY opportunity_assessment_score), 2) as q3,
    ROUND(STDDEV(opportunity_assessment_score), 2) as std_dev,
    COUNT(*) FILTER (WHERE opportunity_assessment_score < 0) as below_min,
    COUNT(*) FILTER (WHERE opportunity_assessment_score > 100) as above_max
FROM workflow_results
WHERE opportunity_assessment_score IS NOT NULL;

-- Expected: min_score >= 0, max_score <= 100, below_min = 0, above_max = 0

-- ==============================================================================
-- 8. TOP OPPORTUNITIES: Show highest-scoring opportunities
-- ==============================================================================

SELECT
    app_name,
    opportunity_id,
    opportunity_assessment_score,
    simplicity_score,
    market_demand,
    pain_intensity,
    monetization_potential,
    market_gap,
    technical_feasibility,
    final_score as legacy_score,
    COALESCE(jsonb_array_length(function_list), function_count) as func_count,
    processed_at
FROM workflow_results
WHERE opportunity_assessment_score IS NOT NULL
ORDER BY opportunity_assessment_score DESC
LIMIT 10;

-- Review: Check if high-scoring opportunities make sense based on dimension values

-- ==============================================================================
-- 9. DIMENSION COMPLETENESS: Check for missing dimension values
-- ==============================================================================

SELECT
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE market_demand IS NULL) as null_market_demand,
    COUNT(*) FILTER (WHERE pain_intensity IS NULL) as null_pain_intensity,
    COUNT(*) FILTER (WHERE monetization_potential IS NULL) as null_monetization,
    COUNT(*) FILTER (WHERE market_gap IS NULL) as null_market_gap,
    COUNT(*) FILTER (WHERE technical_feasibility IS NULL) as null_technical,
    COUNT(*) FILTER (WHERE simplicity_score IS NULL) as null_simplicity,
    -- Calculate completeness percentage
    ROUND(COUNT(*) FILTER (
        WHERE market_demand IS NOT NULL
          AND pain_intensity IS NOT NULL
          AND monetization_potential IS NOT NULL
          AND market_gap IS NOT NULL
          AND technical_feasibility IS NOT NULL
          AND simplicity_score IS NOT NULL
    )::NUMERIC / NULLIF(COUNT(*), 0) * 100, 2) as complete_records_pct
FROM workflow_results;

-- Expected: High complete_records_pct (ideally >90%)

-- ==============================================================================
-- 10. ASSESSMENT VS LEGACY SCORE: Compare new vs old scoring
-- ==============================================================================

SELECT
    ROUND(AVG(opportunity_assessment_score), 2) as avg_new_score,
    ROUND(AVG(final_score), 2) as avg_legacy_score,
    ROUND(AVG(opportunity_assessment_score - final_score), 2) as avg_difference,
    ROUND(CORR(opportunity_assessment_score, final_score), 3) as correlation,
    COUNT(*) FILTER (WHERE opportunity_assessment_score > final_score) as new_score_higher,
    COUNT(*) FILTER (WHERE opportunity_assessment_score < final_score) as legacy_score_higher,
    COUNT(*) FILTER (WHERE ABS(opportunity_assessment_score - final_score) < 5) as similar_scores
FROM workflow_results
WHERE opportunity_assessment_score IS NOT NULL
  AND final_score IS NOT NULL;

-- Review: Understand how new methodology compares to legacy scoring

-- ==============================================================================
-- 11. SIMPLICITY SCORE IMPACT: Analyze contribution of simplicity dimension
-- ==============================================================================

SELECT
    ROUND(simplicity_score, 0) as simplicity_bucket,
    COUNT(*) as record_count,
    ROUND(AVG(opportunity_assessment_score), 2) as avg_assessment_score,
    ROUND(AVG(simplicity_score * 0.20), 2) as avg_simplicity_contribution,
    ROUND(AVG(
        COALESCE(market_demand, 0) * 0.20 +
        COALESCE(pain_intensity, 0) * 0.25 +
        COALESCE(monetization_potential, 0) * 0.20 +
        COALESCE(market_gap, 0) * 0.10 +
        COALESCE(technical_feasibility, 0) * 0.05
    ), 2) as avg_other_dimensions_contribution
FROM workflow_results
WHERE simplicity_score IS NOT NULL
  AND opportunity_assessment_score IS NOT NULL
GROUP BY ROUND(simplicity_score, 0)
ORDER BY simplicity_bucket DESC;

-- Review: Understand how simplicity_score affects overall assessment

-- ==============================================================================
-- 12. COMMENTS VERIFICATION: Check documentation exists
-- ==============================================================================

SELECT
    cols.column_name,
    pg_catalog.col_description(c.oid, cols.ordinal_position::int) as column_comment
FROM information_schema.columns cols
JOIN pg_catalog.pg_class c ON c.relname = cols.table_name
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
WHERE cols.table_schema = 'public'
  AND cols.table_name = 'workflow_results'
  AND cols.column_name IN ('simplicity_score', 'opportunity_assessment_score')
ORDER BY cols.column_name;

-- Expected: Both columns should have descriptive comments

-- ==============================================================================
-- VERIFICATION SUMMARY
-- ==============================================================================

DO $$
DECLARE
    total_records INTEGER;
    records_with_simplicity INTEGER;
    records_with_assessment INTEGER;
    schema_check_passed BOOLEAN;
    constraint_check_passed BOOLEAN;
    index_check_passed BOOLEAN;
BEGIN
    -- Count records
    SELECT COUNT(*) INTO total_records FROM workflow_results;
    SELECT COUNT(*) INTO records_with_simplicity FROM workflow_results WHERE simplicity_score IS NOT NULL;
    SELECT COUNT(*) INTO records_with_assessment FROM workflow_results WHERE opportunity_assessment_score IS NOT NULL;

    -- Check schema
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'workflow_results'
          AND column_name = 'simplicity_score'
          AND data_type = 'numeric'
    ) INTO schema_check_passed;

    -- Check constraint
    SELECT EXISTS (
        SELECT 1 FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        WHERE rel.relname = 'workflow_results'
          AND con.conname LIKE '%simplicity_score%'
    ) INTO constraint_check_passed;

    -- Check index
    SELECT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'workflow_results'
          AND indexname = 'idx_workflow_results_opportunity_assessment_score'
    ) INTO index_check_passed;

    RAISE NOTICE '============================================================';
    RAISE NOTICE 'MIGRATION VERIFICATION SUMMARY';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Schema Check: %', CASE WHEN schema_check_passed THEN 'PASS' ELSE 'FAIL' END;
    RAISE NOTICE 'Constraint Check: %', CASE WHEN constraint_check_passed THEN 'PASS' ELSE 'FAIL' END;
    RAISE NOTICE 'Index Check: %', CASE WHEN index_check_passed THEN 'PASS' ELSE 'FAIL' END;
    RAISE NOTICE '';
    RAISE NOTICE 'Data Statistics:';
    RAISE NOTICE '  Total records: %', total_records;
    RAISE NOTICE '  With simplicity_score: % (%%%)',
        records_with_simplicity,
        ROUND(records_with_simplicity::NUMERIC / NULLIF(total_records, 0) * 100, 2);
    RAISE NOTICE '  With assessment_score: % (%%%)',
        records_with_assessment,
        ROUND(records_with_assessment::NUMERIC / NULLIF(total_records, 0) * 100, 2);
    RAISE NOTICE '';
    RAISE NOTICE 'Overall Status: %',
        CASE
            WHEN schema_check_passed AND constraint_check_passed AND index_check_passed
                AND records_with_simplicity > 0 AND records_with_assessment > 0
            THEN 'SUCCESS - Migration completed successfully'
            ELSE 'WARNING - Please review verification queries above'
        END;
    RAISE NOTICE '============================================================';
END $$;
