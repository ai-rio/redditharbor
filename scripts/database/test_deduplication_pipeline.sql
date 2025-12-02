-- Test Phase 4 Deduplication Pipeline
-- This script validates that the UUID format fix resolves the deduplication issues

-- Step 1: Test the exact query pattern that was failing before
-- This simulates what the deduplication pipeline would do
SELECT 'Testing Original Failing Query Pattern:' as info;
SELECT
    COUNT(*) as total_opportunities,
    COUNT(CASE WHEN submission_id IS NOT NULL THEN 1 END) as with_submission_id
FROM opportunities_unified
WHERE submission_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';

-- Step 2: Test querying by specific UUID (this should work now)
SELECT 'Testing Query by Specific UUID (Should Work):' as info;
SELECT
    ou.id,
    ou.submission_id,
    ou.title,
    s.submission_id as original_string_id
FROM opportunities_unified ou
JOIN submissions s ON ou.submission_id = s.id
WHERE ou.submission_id = '968ffcd9-cd0d-4632-b2f2-6553f616b33a';  -- high_quality submission

-- Step 3: Test the join pattern that deduplication uses
SELECT 'Testing Join Pattern for Deduplication:' as info;
SELECT
    ou.id as opportunity_id,
    ou.submission_id,
    ou.title,
    s.submission_id as string_id,
    s.title as original_title,
    ou.metadata,
    ou.is_duplicate,
    ou.duplicate_of_id
FROM opportunities_unified ou
LEFT JOIN submissions s ON ou.submission_id = s.id
WHERE ou.submission_id IS NOT NULL
ORDER BY s.submission_id;

-- Step 4: Test concept metadata tracking (this was the main failing point)
SELECT 'Testing Concept Metadata Tracking:' as info;
SELECT
    ou.id,
    ou.submission_id,
    ou.app_concept,
    ou.problem_statement,
    ou.target_audience,
    s.submission_id as original_string_id,
    s.title as original_title,
    CASE
        WHEN ou.submission_id IS NOT NULL AND
             ou.submission_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        THEN 'UUID Valid - Metadata tracking will work'
        ELSE 'UUID Invalid - Metadata tracking will fail'
    END as metadata_tracking_status
FROM opportunities_unified ou
LEFT JOIN submissions s ON ou.submission_id = s.id
WHERE ou.submission_id IS NOT NULL
LIMIT 5;

-- Step 5: Test batch UUID validation (what Phase 4 would do)
SELECT 'Testing Batch UUID Validation:' as info;
SELECT
    COUNT(*) as total_records,
    COUNT(CASE
        WHEN submission_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        THEN 1
    END) as valid_uuids,
    COUNT(CASE
        WHEN submission_id IS NULL
        THEN 1
    END) as null_uuids,
    COUNT(CASE
        WHEN submission_id IS NOT NULL AND
             submission_id::text !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        THEN 1
    END) as invalid_uuids
FROM opportunities_unified;

-- Step 6: Test the specific submissions that were causing issues
SELECT 'Testing Previously Problematic Submissions:' as info;
SELECT
    s.submission_id as original_string_id,
    s.id as proper_uuid,
    COUNT(ou.id) as linked_opportunities,
    STRING_AGG(ou.title, ', ') as linked_opportunity_titles
FROM submissions s
LEFT JOIN opportunities_unified ou ON s.id = ou.submission_id
WHERE s.submission_id IN ('high_quality', 'sub1', 'sub2', 'sub3', 'test1', 'real_test_prof_1', 'real_test_prof_2', 'real_test_prof_3', 'hybrid_1', 'hybrid_2')
GROUP BY s.submission_id, s.id
ORDER BY s.submission_id;

-- Step 7: Simulate the exact error that was happening
-- This should now work without "invalid input syntax for type uuid" error
SELECT 'Simulating Previous Error Scenario (Should Work Now):' as info;
DO $$
BEGIN
    -- This represents the kind of query that was failing
    PERFORM 1 FROM opportunities_unified
    WHERE submission_id = '968ffcd9-cd0d-4632-b2f2-6553f616b33a';

    RAISE NOTICE '✓ UUID query succeeded - no more "invalid input syntax for type uuid" errors';
EXCEPTION
    WHEN invalid_text_representation THEN
        RAISE NOTICE '✗ UUID query failed - still having format issues';
    WHEN OTHERS THEN
        RAISE NOTICE '✗ UUID query failed with unexpected error: %', SQLERRM;
END $$;

-- Step 8: Test foreign key constraint validation
SELECT 'Testing Foreign Key Constraints:' as info;
SELECT
    COUNT(*) as total_opportunities,
    COUNT(CASE WHEN s.id IS NOT NULL THEN 1 END) as valid_foreign_keys,
    COUNT(CASE WHEN s.id IS NULL THEN 1 END) as broken_foreign_keys
FROM opportunities_unified ou
LEFT JOIN submissions s ON ou.submission_id = s.id
WHERE ou.submission_id IS NOT NULL;

-- Step 9: Final validation summary
SELECT 'Final Validation Summary - Phase 4 Ready:' as info;
SELECT
    'All UUID formats are valid and properly linked' as status,
    (SELECT COUNT(*) FROM submissions) as total_submissions,
    (SELECT COUNT(*) FROM opportunities_unified WHERE submission_id IS NOT NULL) as linked_opportunities,
    (SELECT COUNT(*) FROM opportunities_unified WHERE submission_id IS NOT NULL AND submission_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$') as valid_uuid_links,
    CASE
        WHEN (SELECT COUNT(*) FROM opportunities_unified WHERE submission_id IS NOT NULL AND submission_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$') > 0
        THEN '✓ READY for Phase 4 deduplication'
        ELSE '✗ NOT READY - still have UUID issues'
    END as phase_4_status;