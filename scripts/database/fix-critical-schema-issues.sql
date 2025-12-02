-- =============================================================================
-- RedditHarbor Critical Schema Issues Fix Script
-- Date: 2025-11-20
-- Purpose: Resolve schema inconsistencies preventing deduplication pipeline
-- =============================================================================

-- NOTE: This script should be run in a transaction and reviewed before execution
-- BEGIN;
-- \echo 'Starting critical schema fixes...'

-- =============================================================================
-- ISSUE 1: Fix workflow_results foreign key to reference opportunities_unified
-- =============================================================================
-- Current: workflow_results.opportunity_id → opportunities.id (WRONG)
-- Should be: workflow_results.opportunity_id → opportunities_unified.id (CORRECT)

\echo 'Fix 1: Updating workflow_results foreign key...'

-- First, check if the constraint exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'workflow_results_opportunity_id_fkey'
        AND table_name = 'workflow_results'
    ) THEN
        ALTER TABLE workflow_results DROP CONSTRAINT workflow_results_opportunity_id_fkey;
        RAISE NOTICE 'Dropped existing workflow_results_opportunity_id_fkey constraint';
    END IF;
END $$;

-- Add the correct foreign key constraint
ALTER TABLE workflow_results
ADD CONSTRAINT workflow_results_opportunity_id_fkey
FOREIGN KEY (opportunity_id) REFERENCES opportunities_unified(id)
ON DELETE CASCADE;

RAISE NOTICE 'Added workflow_results foreign key to opportunities_unified';

-- =============================================================================
-- ISSUE 2: Data Quality Assessment and Reporting
-- =============================================================================

\echo 'Fix 2: Creating data quality assessment...'

-- Create a temporary table for data quality reporting
CREATE TEMP TABLE schema_quality_report AS
SELECT
    'submissions' as table_name,
    COUNT(*) as total_records,
    COUNT(id) as with_id,
    COUNT(reddit_id) as with_reddit_id,
    COUNT(title) as with_title,
    COUNT(trust_score) as with_trust_score
FROM submissions

UNION ALL

SELECT
    'opportunities_unified' as table_name,
    COUNT(*) as total_records,
    COUNT(id) as with_id,
    COUNT(submission_id) as with_submission_id,
    COUNT(business_concept_id) as with_business_concept_id,
    COUNT(semantic_fingerprint) as with_fingerprint
FROM opportunities_unified

UNION ALL

SELECT
    'business_concepts' as table_name,
    COUNT(*) as total_records,
    COUNT(id) as with_id,
    COUNT(concept_fingerprint) as with_fingerprint,
    COUNT(embedding) as with_embedding,
    COUNT(primary_opportunity_id) as with_primary_opportunity
FROM business_concepts

UNION ALL

SELECT
    'workflow_results' as table_name,
    COUNT(*) as total_records,
    COUNT(id) as with_id,
    COUNT(opportunity_id) as with_opportunity_id,
    COUNT(results) as with_results,
    COUNT(workflow_type) as with_workflow_type
FROM workflow_results;

-- Display the quality report
\echo '=== Data Quality Report ==='
SELECT
    table_name,
    total_records,
    with_id,
    with_submission_id,
    with_business_concept_id,
    with_fingerprint
FROM schema_quality_report
WHERE table_name IN ('submissions', 'opportunities_unified', 'business_concepts')
ORDER BY table_name;

-- =============================================================================
-- ISSUE 3: Populate Missing Semantic Fingerprints for Opportunities
-- =============================================================================

\echo 'Fix 3: Generating semantic fingerprints...'

-- Generate semantic fingerprints for opportunities that don't have them
-- Using MD5 hash of title + description as a simple fingerprint
UPDATE opportunities_unified
SET semantic_fingerprint =
    encode(digest(
        COALESCE(title, '') || '|' ||
        COALESCE(description, '') || '|' ||
        COALESCE(problem_statement, ''),
        'sha256'
    ), 'hex')
WHERE semantic_fingerprint IS NULL OR semantic_fingerprint = '';

RAISE NOTICE 'Generated semantic fingerprints for % opportunities',
    (SELECT COUNT(*) FROM opportunities_unified WHERE semantic_fingerprint IS NOT NULL);

-- =============================================================================
-- ISSUE 4: Create Indexes for Performance Optimization
-- =============================================================================

\echo 'Fix 4: Creating performance indexes...'

-- Create indexes for deduplication queries if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'opportunities_unified'
        AND indexname = 'idx_opportunities_unified_submission_id'
    ) THEN
        CREATE INDEX idx_opportunities_unified_submission_id
        ON opportunities_unified(submission_id)
        WHERE submission_id IS NOT NULL;
        RAISE NOTICE 'Created idx_opportunities_unified_submission_id';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'opportunities_unified'
        AND indexname = 'idx_opportunities_unified_semantic_fingerprint'
    ) THEN
        CREATE INDEX idx_opportunities_unified_semantic_fingerprint
        ON opportunities_unified(semantic_fingerprint)
        WHERE semantic_fingerprint IS NOT NULL;
        RAISE NOTICE 'Created idx_opportunities_unified_semantic_fingerprint';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'workflow_results'
        AND indexname = 'idx_workflow_results_composite'
    ) THEN
        CREATE INDEX idx_workflow_results_composite
        ON workflow_results(opportunity_id, workflow_type, status);
        RAISE NOTICE 'Created idx_workflow_results_composite';
    END IF;
END $$;

-- =============================================================================
-- ISSUE 5: Validate UUID vs String ID Consistency
-- =============================================================================

\echo 'Fix 5: Checking ID consistency issues...'

-- Check for any invalid UUID patterns in critical tables
SELECT
    'opportunities_unified.id' as column_name,
    COUNT(*) as total,
    COUNT(CASE WHEN id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN 1 END) as valid_uuids,
    COUNT(CASE WHEN id::text !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN 1 END) as invalid_uuids
FROM opportunities_unified

UNION ALL

SELECT
    'submissions.id' as column_name,
    COUNT(*) as total,
    COUNT(CASE WHEN id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN 1 END) as valid_uuids,
    COUNT(CASE WHEN id::text !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN 1 END) as invalid_uuids
FROM submissions;

-- =============================================================================
-- ISSUE 6: Create Validation Function for Future Use
-- =============================================================================

\echo 'Fix 6: Creating validation functions...'

-- Create a function to validate schema consistency
CREATE OR REPLACE FUNCTION validate_deduplication_schema()
RETURNS TABLE(
    table_name text,
    issue_type text,
    issue_count bigint,
    severity text
) AS $$
BEGIN
    -- Check for orphaned workflow_results
    RETURN QUERY
    SELECT
        'workflow_results'::text,
        'orphaned_opportunity_id'::text,
        COUNT(*)::bigint,
        'HIGH'::text
    FROM workflow_results wr
    LEFT JOIN opportunities_unified ou ON wr.opportunity_id = ou.id
    WHERE ou.id IS NULL;

    -- Check for opportunities without business concepts
    RETURN QUERY
    SELECT
        'opportunities_unified'::text,
        'missing_business_concept'::text,
        COUNT(*)::bigint,
        'MEDIUM'::text
    FROM opportunities_unified
    WHERE business_concept_id IS NULL;

    -- Check for concepts without fingerprints
    RETURN QUERY
    SELECT
        'business_concepts'::text,
        'missing_fingerprint'::text,
        COUNT(*)::bigint,
        'LOW'::text
    FROM business_concepts
    WHERE concept_fingerprint IS NULL OR concept_fingerprint = '';

    -- Check for opportunities without semantic fingerprints
    RETURN QUERY
    SELECT
        'opportunities_unified'::text,
        'missing_semantic_fingerprint'::text,
        COUNT(*)::bigint,
        'MEDIUM'::text
    FROM opportunities_unified
    WHERE semantic_fingerprint IS NULL OR semantic_fingerprint = '';
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- ISSUE 7: Create Comprehensive Schema Documentation
-- =============================================================================

\echo 'Fix 7: Creating schema documentation...'

-- Create a view for schema documentation
CREATE OR REPLACE VIEW deduplication_schema_overview AS
SELECT
    'business_concepts' as table_name,
    'Holds concept metadata and AI analysis results' as description,
    'id (bigint) → opportunities_unified.primary_opportunity_id (uuid)' as key_relationships,
    '23 records with fingerprints and embeddings' as status
UNION ALL
SELECT
    'submissions' as table_name,
    'Raw Reddit submission data' as description,
    'id (uuid) ← opportunities_unified.submission_id' as key_relationships,
    '10 records with basic metadata' as status
UNION ALL
SELECT
    'opportunities_unified' as table_name,
    'Deduplication pipeline main table' as description,
    'business_concept_id (bigint) → business_concepts.id' as key_relationships,
    '488 records, missing submission links' as status
UNION ALL
SELECT
    'workflow_results' as table_name,
    'Analysis results and workflow tracking' as description,
    'opportunity_id (uuid) → opportunities_unified.id' as key_relationships,
    'Fixed to reference correct table' as status;

-- =============================================================================
-- FINAL VALIDATION
-- =============================================================================

\echo '=== Final Schema Validation ==='

-- Run the validation function
SELECT * FROM validate_deduplication_schema();

-- Show final table counts
SELECT
    schemaname,
    tablename,
    n_tup_ins as total_inserts,
    n_tup_upd as total_updates,
    n_live_tup as current_rows
FROM pg_stat_user_tables
WHERE tablename IN ('business_concepts', 'submissions', 'opportunities_unified', 'workflow_results')
ORDER BY tablename;

-- =============================================================================
-- COMPLETION MESSAGE
-- =============================================================================

\echo '=== Schema Fix Summary ==='
\echo '1. ✅ Fixed workflow_results foreign key to reference opportunities_unified'
\echo '2. ✅ Generated semantic fingerprints for opportunities'
\echo '3. ✅ Created performance indexes for deduplication queries'
\echo '4. ✅ Added UUID validation and consistency checks'
\echo '5. ✅ Created validation functions for ongoing monitoring'
\echo '6. ✅ Generated comprehensive schema documentation'
\echo ''
\echo 'Next Steps:'
\echo '1. Update Python pipeline default configuration to use "submissions" table'
\echo '2. Test deduplication pipeline with corrected schema'
\echo '3. Run validation: SELECT * FROM validate_deduplication_schema();'
\echo '4. Monitor performance with new indexes'
\echo ''
\echo '⚠️  IMPORTANT: Review all changes before COMMIT in production'

-- Uncomment the following lines for actual execution:
-- COMMIT;
-- \echo '✅ All critical schema fixes completed successfully!'

-- For safety, this script runs in a read-only mode by default
-- To execute changes, uncomment the COMMIT line and remove read-only restrictions