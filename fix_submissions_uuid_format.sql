-- Comprehensive Fix for Submissions UUID Format Issue
-- This script resolves the UUID format mismatch between submissions and opportunities_unified tables
--
-- Issue:
-- - submissions.submission_id is character varying (string) with test values like "high_quality", "sub1", etc.
-- - opportunities_unified.submission_id is UUID and references submissions.id (UUID)
-- - Deduplication pipeline expects UUID format but gets strings

-- Step 1: Create temporary mapping table
CREATE TEMP TABLE submission_uuid_mappings (
    old_string_submission_id VARCHAR(255) PRIMARY KEY,
    correct_uuid_id UUID
);

-- Step 2: Map all string submission_ids to their corresponding UUID id from submissions table
INSERT INTO submission_uuid_mappings (old_string_submission_id, correct_uuid_id)
SELECT
    s.submission_id,
    s.id
FROM submissions s
WHERE s.submission_id IS NOT NULL
GROUP BY s.submission_id, s.id;

-- Show the mappings we created
SELECT 'Submission UUID Mappings:' as info;
SELECT old_string_submission_id, correct_uuid_id
FROM submission_uuid_mappings
ORDER BY old_string_submission_id;

-- Step 3: Check current state of opportunities_unified
SELECT 'Current opportunities_unified records before fix:' as info;
SELECT
    COUNT(*) as total_records,
    COUNT(submission_id) as records_with_submission_id,
    COUNT(CASE WHEN submission_id IS NOT NULL THEN 1 END) as non_null_submission_ids
FROM opportunities_unified;

-- Step 4: The core issue is that opportunities_unified might have string submission_ids
-- Let's check if there are any invalid UUIDs in submission_id column
SELECT 'Checking for invalid UUID formats in opportunities_unified.submission_id:' as info;
SELECT
    COUNT(*) as total_records,
    COUNT(CASE WHEN submission_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN 1 END) as valid_uuids,
    COUNT(CASE WHEN submission_id::text !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' AND submission_id IS NOT NULL THEN 1 END) as invalid_uuids
FROM opportunities_unified;

-- Step 5: Check if we need to create or update opportunities_unified records
-- The issue might be that opportunities_unified doesn't have the right submission_id references
SELECT 'Checking if opportunities_unified has records linked to our test submissions:' as info;
SELECT
    COUNT(*) as matching_records
FROM opportunities_unified ou
JOIN submissions s ON ou.submission_id = s.id
WHERE s.submission_id IN ('high_quality', 'sub1', 'sub2', 'sub3', 'test1', 'hybrid_1', 'hybrid_2', 'real_test_prof_1', 'real_test_prof_2', 'real_test_prof_3');

-- Step 6: If there are opportunities_unified records with submission_id issues, fix them
-- This would handle cases where submission_id was incorrectly stored as string instead of UUID
DO $$
BEGIN
    -- Check if there are any invalid UUIDs that need fixing
    IF EXISTS (
        SELECT 1 FROM opportunities_unified
        WHERE submission_id IS NOT NULL
        AND submission_id::text !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    ) THEN
        -- Fix invalid UUIDs by mapping them to proper submission UUIDs
        UPDATE opportunities_unified
        SET submission_id = mappings.correct_uuid_id
        FROM submission_uuid_mappings mappings
        WHERE opportunities_unified.submission_id::text = mappings.old_string_submission_id;

        RAISE NOTICE 'Fixed invalid UUID formats in opportunities_unified.submission_id';
    END IF;
END $$;

-- Step 7: If opportunities_unified is missing submission_id references for our test data,
-- we might need to create those relationships or check if they exist properly
SELECT 'Checking existing relationships between submissions and opportunities_unified:' as info;
SELECT
    s.submission_id as string_id,
    s.id as uuid_id,
    COUNT(ou.id) as opportunity_count
FROM submissions s
LEFT JOIN opportunities_unified ou ON s.id = ou.submission_id
WHERE s.submission_id IN ('high_quality', 'sub1', 'sub2', 'sub3', 'test1', 'hybrid_1', 'hybrid_2', 'real_test_prof_1', 'real_test_prof_2', 'real_test_prof_3')
GROUP BY s.submission_id, s.id
ORDER BY s.submission_id;

-- Step 8: Verification - Check if there are any remaining invalid UUID formats
SELECT 'Final verification - checking for remaining invalid UUIDs:' as info;
SELECT
    COUNT(*) as remaining_issues
FROM opportunities_unified
WHERE submission_id IS NOT NULL
AND submission_id::text !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';

-- Step 9: Test UUID format validation (this should work after the fix)
SELECT 'Testing UUID format validation:' as info;
SELECT
    submission_id,
    CASE
        WHEN submission_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN 'Valid UUID'
        WHEN submission_id IS NULL THEN 'NULL'
        ELSE 'Invalid UUID'
    END as uuid_status
FROM opportunities_unified
WHERE submission_id IS NOT NULL
LIMIT 5;

-- Step 10: Summary of the fix
SELECT 'Summary:' as info;
SELECT
    (SELECT COUNT(*) FROM submissions) as total_submissions,
    (SELECT COUNT(*) FROM submissions WHERE submission_id IN ('high_quality', 'sub1', 'sub2', 'sub3', 'test1', 'hybrid_1', 'hybrid_2', 'real_test_prof_1', 'real_test_prof_2', 'real_test_prof_3')) as test_submissions,
    (SELECT COUNT(*) FROM opportunities_unified) as total_opportunities_unified,
    (SELECT COUNT(*) FROM opportunities_unified WHERE submission_id IS NOT NULL) as opportunities_with_submission_id;

-- Clean up
DROP TABLE IF EXISTS submission_uuid_mappings;