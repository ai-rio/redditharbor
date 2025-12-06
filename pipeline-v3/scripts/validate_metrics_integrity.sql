-- Metrics Collection Integrity Validation SQL Script
-- Purpose: Comprehensive validation of pipeline_metrics data integrity
-- Usage: psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -f validate_metrics_integrity.sql

-- Set up output format
\pset format wrapped
\pset linestyle ascii
\pset border 2
\pset null '[NULL]'

-- Create validation results temp table
DROP TABLE IF EXISTS validation_results;
CREATE TEMP TABLE validation_results (
    test_name TEXT,
    status TEXT,
    score NUMERIC,
    details JSONB
);

-- =====================================================
-- 1. Data Completeness Check
-- =====================================================
DO $$
DECLARE
    total_records INTEGER;
    null_counts JSONB;
    invalid_counts JSONB;
    completeness_score NUMERIC;
BEGIN
    -- Check if table exists
    IF NOT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'pipeline_metrics'
    ) THEN
        INSERT INTO validation_results VALUES (
            'data_completeness',
            'FAIL',
            0,
            '{"error": "Table pipeline_metrics does not exist"}'::jsonb
        );
        RETURN;
    END IF;

    -- Get null counts
    SELECT jsonb_build_object(
        'total_records', COUNT(*),
        'null_opportunity_id', COUNT(CASE WHEN opportunity_id IS NULL THEN 1 END),
        'null_agent_name', COUNT(CASE WHEN agent_name IS NULL THEN 1 END),
        'null_phase', COUNT(CASE WHEN phase IS NULL THEN 1 END),
        'null_success', COUNT(CASE WHEN success IS NULL THEN 1 END),
        'null_duration', COUNT(CASE WHEN duration_seconds IS NULL THEN 1 END),
        'null_cost', COUNT(CASE WHEN api_cost_usd IS NULL THEN 1 END)
    ) INTO null_counts
    FROM pipeline_metrics
    WHERE created_at >= NOW() - INTERVAL '24 hour';

    -- Get invalid value counts
    SELECT jsonb_build_object(
        'negative_duration', COUNT(CASE WHEN duration_seconds < 0 THEN 1 END),
        'zero_duration', COUNT(CASE WHEN duration_seconds = 0 THEN 1 END),
        'negative_cost', COUNT(CASE WHEN api_cost_usd < 0 THEN 1 END)
    ) INTO invalid_counts
    FROM pipeline_metrics
    WHERE created_at >= NOW() - INTERVAL '24 hour';

    -- Calculate completeness score
    total_records := (null_counts->>'total_records')::INTEGER;

    IF total_records = 0 THEN
        completeness_score := 100; -- No data is technically complete
    ELSE
        completeness_score := 100 - (
            ((null_counts->>'null_opportunity_id')::INTEGER +
             (null_counts->>'null_agent_name')::INTEGER +
             (null_counts->>'null_phase')::INTEGER +
             (null_counts->>'null_success')::INTEGER +
             (null_counts->>'null_duration')::INTEGER +
             (invalid_counts->>'negative_duration')::INTEGER +
             (invalid_counts->>'negative_cost')::INTEGER) * 100.0 / total_records
        );
    END IF;

    INSERT INTO validation_results VALUES (
        'data_completeness',
        CASE WHEN completeness_score >= 95 THEN 'PASS' ELSE 'FAIL' END,
        completeness_score,
        jsonb_build_object('null_counts', null_counts, 'invalid_counts', invalid_counts)
    );
END $$;

-- =====================================================
-- 2. Data Consistency Verification
-- =====================================================
DO $$
DECLARE
    format_validation JSONB;
    agent_coverage JSONB;
    phase_coverage JSONB;
    consistency_score NUMERIC;
BEGIN
    -- Validate opportunity_id format
    SELECT jsonb_build_object(
        'total_records', COUNT(*),
        'valid_format', COUNT(CASE WHEN opportunity_id ~ '^opp-[0-9]+$' THEN 1 END),
        'invalid_format', COUNT(CASE WHEN opportunity_id IS NOT NULL AND opportunity_id !~ '^opp-[0-9]+$' THEN 1 END)
    ) INTO format_validation
    FROM pipeline_metrics
    WHERE created_at >= NOW() - INTERVAL '24 hour';

    -- Check agent coverage
    WITH expected_agents AS (
        SELECT unnest(ARRAY['wtp', 'segment', 'price', 'payment', 'market', 'consensus', 'all',
                             'reddit_client', 'database_loader', 'agno_analyzer']) as agent
    ),
    actual_agents AS (
        SELECT DISTINCT agent_name
        FROM pipeline_metrics
        WHERE created_at >= NOW() - INTERVAL '24 hour'
        AND agent_name IS NOT NULL
    )
    SELECT jsonb_build_object(
        'expected', (SELECT COUNT(*) FROM expected_agents),
        'found', (SELECT COUNT(*) FROM actual_agents),
        'missing', (SELECT string_agg(e.agent, ', ') FROM expected_agents e
                    LEFT JOIN actual_agents a ON e.agent = a.agent_name
                    WHERE a.agent_name IS NULL),
        'coverage_pct', (SELECT COUNT(*) * 100.0 / (SELECT COUNT(*) FROM expected_agents)
                        FROM actual_agents WHERE agent_name IN (SELECT agent FROM expected_agents))
    ) INTO agent_coverage;

    -- Check phase coverage
    WITH expected_phases AS (
        SELECT unnest(ARRAY['extract', 'transform', 'load', 'end_to_end']) as phase
    ),
    actual_phases AS (
        SELECT DISTINCT phase
        FROM pipeline_metrics
        WHERE created_at >= NOW() - INTERVAL '24 hour'
        AND phase IS NOT NULL
    )
    SELECT jsonb_build_object(
        'expected', (SELECT COUNT(*) FROM expected_phases),
        'found', (SELECT COUNT(*) FROM actual_phases),
        'missing', (SELECT string_agg(e.phase, ', ') FROM expected_phases e
                    LEFT JOIN actual_phases a ON e.phase = a.phase
                    WHERE a.phase IS NULL),
        'coverage_pct', (SELECT COUNT(*) * 100.0 / (SELECT COUNT(*) FROM expected_phases)
                        FROM actual_phases WHERE phase IN (SELECT phase FROM expected_phases))
    ) INTO phase_coverage;

    -- Calculate consistency score
    consistency_score := (
        ((format_validation->>'valid_format')::NUMERIC / NULLIF((format_validation->>'total_records')::NUMERIC, 0) * 100) +
        (agent_coverage->>'coverage_pct')::NUMERIC +
        (phase_coverage->>'coverage_pct')::NUMERIC
    ) / 3;

    INSERT INTO validation_results VALUES (
        'data_consistency',
        CASE WHEN consistency_score >= 90 THEN 'PASS' ELSE 'FAIL' END,
        consistency_score,
        jsonb_build_object(
            'opportunity_format', format_validation,
            'agent_coverage', agent_coverage,
            'phase_coverage', phase_coverage
        )
    );
END $$;

-- =====================================================
-- 3. Relationship Integrity Check
-- =====================================================
DO $$
DECLARE
    opportunity_tracking JSONB;
    orphaned_records JSONB;
    integrity_score NUMERIC;
BEGIN
    -- Check opportunity pipeline completeness
    WITH opportunity_phases AS (
        SELECT
            opportunity_id,
            COUNT(DISTINCT phase) as phases_covered,
            COUNT(*) as total_executions
        FROM pipeline_metrics
        WHERE created_at >= NOW() - INTERVAL '24 hour'
        AND opportunity_id IS NOT NULL
        GROUP BY opportunity_id
    ),
    completeness_stats AS (
        SELECT
            COUNT(*) as total_opportunities,
            COUNT(CASE WHEN phases_covered >= 3 THEN 1 END) as complete_tracking,
            COUNT(CASE WHEN phases_covered < 3 THEN 1 END) as partial_tracking
        FROM opportunity_phases
    )
    SELECT jsonb_build_object(
        'total_opportunities', total_opportunities,
        'complete_tracking', complete_tracking,
        'partial_tracking', partial_tracking,
        'completeness_pct', CASE WHEN total_opportunities > 0
                                THEN complete_tracking * 100.0 / total_opportunities
                                ELSE 100 END
    ) INTO opportunity_tracking
    FROM completeness_stats;

    -- Check for orphaned records
    SELECT jsonb_build_object(
        'total_orphaned', COUNT(*),
        'orphaned_by_phase', (
            SELECT jsonb_agg(jsonb_build_object(phase, count))
            FROM (
                SELECT phase, COUNT(*) as count
                FROM pipeline_metrics
                WHERE created_at >= NOW() - INTERVAL '24 hour'
                AND opportunity_id IS NULL
                GROUP BY phase
            ) orphan_counts
        )
    ) INTO orphaned_records
    FROM pipeline_metrics
    WHERE created_at >= NOW() - INTERVAL '24 hour'
    AND opportunity_id IS NULL;

    -- Calculate integrity score
    integrity_score := (opportunity_tracking->>'completeness_pct')::NUMERIC -
                       ((orphaned_records->>'total_orphaned')::INTEGER * 2.0);

    INSERT INTO validation_results VALUES (
        'relationship_integrity',
        CASE WHEN integrity_score >= 80 THEN 'PASS' ELSE 'FAIL' END,
        GREATEST(0, LEAST(100, integrity_score)),
        jsonb_build_object(
            'opportunity_tracking', opportunity_tracking,
            'orphaned_records', orphaned_records
        )
    );
END $$;

-- =====================================================
-- 4. Performance Metrics Validation
-- =====================================================
DO $$
DECLARE
    time_window JSONB;
    duration_analysis JSONB;
    cost_analysis JSONB;
    performance_score NUMERIC;
    issues TEXT[];
BEGIN
    -- Time window analysis
    SELECT jsonb_build_object(
        'first_execution', MIN(created_at),
        'last_execution', MAX(created_at),
        'total_seconds', EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at))),
        'opportunities_processed', COUNT(DISTINCT opportunity_id),
        'total_executions', COUNT(*)
    ) INTO time_window
    FROM pipeline_metrics
    WHERE created_at >= NOW() - INTERVAL '24 hour';

    -- Duration analysis
    WITH duration_stats AS (
        SELECT
            phase,
            agent_name,
            AVG(duration_seconds) as avg_duration,
            MAX(duration_seconds) as max_duration
        FROM pipeline_metrics
        WHERE created_at >= NOW() - INTERVAL '24 hour'
        AND duration_seconds > 0
        GROUP BY phase, agent_name
    )
    SELECT jsonb_build_object(
        'executions_analyzed', COUNT(*),
        'slow_executions', (
            SELECT jsonb_agg(jsonb_build_object(
                'phase_agent', phase || '/' || agent_name,
                'max_duration', max_duration
            ))
            FROM duration_stats
            WHERE max_duration > 300
        )
    ) INTO duration_analysis
    FROM duration_stats;

    -- Cost analysis
    SELECT jsonb_build_object(
        'total_cost', COALESCE(SUM(api_cost_usd), 0),
        'avg_cost_per_execution', CASE WHEN COUNT(*) > 0 THEN COALESCE(AVG(api_cost_usd), 0) ELSE 0 END,
        'non_zero_costs', COUNT(CASE WHEN api_cost_usd > 0 THEN 1 END),
        'total_records', COUNT(*),
        'cost_per_opportunity', CASE WHEN COUNT(DISTINCT opportunity_id) > 0
                                   THEN COALESCE(SUM(api_cost_usd), 0) / COUNT(DISTINCT opportunity_id)
                                   ELSE 0 END
    ) INTO cost_analysis
    FROM pipeline_metrics
    WHERE created_at >= NOW() - INTERVAL '24 hour';

    -- Calculate performance score
    performance_score := 100;

    -- Deduct for issues
    IF (duration_analysis->>'executions_analyzed')::INTEGER > 0 AND
       jsonb_array_length(duration_analysis->'slow_executions') > 0 THEN
        performance_score := performance_score - 10;
    END IF;

    IF (cost_analysis->>'total_cost')::NUMERIC > 10.0 THEN
        performance_score := performance_score - 10;
    END IF;

    INSERT INTO validation_results VALUES (
        'performance_metrics',
        CASE WHEN performance_score >= 80 THEN 'PASS' ELSE 'WARN' END,
        performance_score,
        jsonb_build_object(
            'time_window', time_window,
            'duration_analysis', duration_analysis,
            'cost_analysis', cost_analysis
        )
    );
END $$;

-- =====================================================
-- Generate Validation Report
-- =====================================================

-- Overall validation summary
\echo ''
\echo '========================================================'
\echo 'PIPELINE METRICS INTEGRITY VALIDATION REPORT'
\echo '========================================================'
\echo ''

-- Overall score
SELECT
    ROUND(AVG(score), 2) as overall_quality_score,
    CASE
        WHEN AVG(score) >= 95 THEN 'EXCELLENT'
        WHEN AVG(score) >= 85 THEN 'GOOD'
        WHEN AVG(score) >= 70 THEN 'ACCEPTABLE'
        ELSE 'NEEDS IMPROVEMENT'
    END as rating
FROM validation_results
WHERE status NOT IN ('ERROR');

\echo ''

-- Detailed results
\echo 'VALIDATION TEST RESULTS:'
\echo '------------------------'
SELECT
    test_name,
    status,
    score,
    CASE
        WHEN status = 'PASS' THEN '✓ All checks passed'
        WHEN status = 'WARN' THEN '⚠ Minor issues detected'
        WHEN status = 'FAIL' THEN '✗ Critical issues found'
        WHEN status = 'ERROR' THEN '❌ Test execution error'
    END as summary
FROM validation_results
ORDER BY
    CASE status
        WHEN 'ERROR' THEN 1
        WHEN 'FAIL' THEN 2
        WHEN 'WARN' THEN 3
        WHEN 'PASS' THEN 4
    END,
    test_name;

-- Detailed analysis section
\echo ''
\echo 'DETAILED ANALYSIS:'
\echo '=================='

-- Data completeness details
\echo ''
\echo '1. DATA COMPLETENESS:'
SELECT
    'Total Records' as metric,
    (details->'null_counts'->>'total_records') as value
FROM validation_results
WHERE test_name = 'data_completeness'
UNION ALL
SELECT
    'NULL opportunity_id' as metric,
    (details->'null_counts'->>'null_opportunity_id') as value
FROM validation_results
WHERE test_name = 'data_completeness'
UNION ALL
SELECT
    'Invalid durations' as metric,
    (details->'invalid_counts'->>'negative_duration') as value
FROM validation_results
WHERE test_name = 'data_completeness';

-- Data consistency details
\echo ''
\echo '2. DATA CONSISTENCY:'
SELECT
    'Valid opportunity_id format %' as metric,
    ROUND((details->'opportunity_format'->>'valid_format')::NUMERIC * 100 /
          NULLIF((details->'opportunity_format'->>'total_records')::NUMERIC, 0), 2) as value
FROM validation_results
WHERE test_name = 'data_consistency'
UNION ALL
SELECT
    'Agent coverage %' as metric,
    (details->'agent_coverage'->>'coverage_pct') as value
FROM validation_results
WHERE test_name = 'data_consistency'
UNION ALL
SELECT
    'Missing agents' as metric,
    COALESCE(details->'agent_coverage'->>'missing', 'None') as value
FROM validation_results
WHERE test_name = 'data_consistency';

-- Relationship integrity details
\echo ''
\echo '3. RELATIONSHIP INTEGRITY:'
SELECT
    'Opportunities tracked' as metric,
    (details->'opportunity_tracking'->>'total_opportunities') as value
FROM validation_results
WHERE test_name = 'relationship_integrity'
UNION ALL
SELECT
    'Complete tracking %' as metric,
    (details->'opportunity_tracking'->>'completeness_pct') as value
FROM validation_results
WHERE test_name = 'relationship_integrity'
UNION ALL
SELECT
    'Orphaned records' as metric,
    (details->'orphaned_records'->>'total_orphaned') as value
FROM validation_results
WHERE test_name = 'relationship_integrity';

-- Performance metrics details
\echo ''
\echo '4. PERFORMANCE METRICS:'
SELECT
    'Total cost (USD)' as metric,
    '$' || ROUND((details->'cost_analysis'->>'total_cost')::NUMERIC, 6) as value
FROM validation_results
WHERE test_name = 'performance_metrics'
UNION ALL
SELECT
    'Avg cost per opportunity' as metric,
    '$' || ROUND((details->'cost_analysis'->>'cost_per_opportunity')::NUMERIC, 6) as value
FROM validation_results
WHERE test_name = 'performance_metrics'
UNION ALL
SELECT
    'Opportunities processed' as metric,
    (details->'time_window'->>'opportunities_processed') as value
FROM validation_results
WHERE test_name = 'performance_metrics';

-- Recommendations
\echo ''
\echo 'RECOMMENDATIONS:'
\echo '================'
\echo ''

-- Generate specific recommendations based on results
DO $$
BEGIN
    -- Check for missing table
    IF EXISTS (SELECT 1 FROM validation_results WHERE test_name = 'data_completeness' AND status = 'FAIL') THEN
        \echo '• CRITICAL: pipeline_metrics table does not exist'
        \echo '  Action: Run migration script - add_metrics_tracking_migration.sql'
    END IF;

    -- Check for NULL values
    IF EXISTS (SELECT 1 FROM validation_results WHERE test_name = 'data_completeness' AND score < 100) THEN
        \echo '• Data completeness issues detected'
        \echo '  Action: Review metric recording logic to ensure all fields populated'
    END IF;

    -- Check for format issues
    IF EXISTS (SELECT 1 FROM validation_results WHERE test_name = 'data_consistency' AND score < 100) THEN
        \echo '• Data consistency issues detected'
        \echo '  Action: Standardize opportunity_id format and agent names'
    END IF;

    -- Check for orphaned records
    IF EXISTS (SELECT 1 FROM validation_results WHERE test_name = 'relationship_integrity' AND score < 100) THEN
        \echo '• Orphaned metrics records found'
        \echo '  Action: Ensure all metrics are associated with an opportunity_id'
    END IF;

    -- Check for performance issues
    IF EXISTS (SELECT 1 FROM validation_results WHERE test_name = 'performance_metrics' AND status = 'WARN') THEN
        \echo '• Performance issues detected'
        \echo '  Action: Investigate slow executions and high API costs'
    END IF;

    -- If all passed
    IF NOT EXISTS (SELECT 1 FROM validation_results WHERE status IN ('FAIL', 'WARN', 'ERROR')) THEN
        \echo '• All validations passed - metrics collection is healthy'
        \echo '  Action: Continue monitoring with scheduled validation checks'
    END IF;
END $$;

\echo ''
\echo '========================================================'
\echo 'END OF VALIDATION REPORT'
\echo '========================================================'
\echo ''

-- Clean up
DROP TABLE validation_results;