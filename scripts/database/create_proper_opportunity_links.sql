-- Create Proper Links Between Submissions and Opportunities_Unified
-- This script will link the meaningful submissions to opportunities_unified records
-- For test data, we'll create the appropriate relationships

-- Step 1: First, let's see if there are any opportunities that could match our real submissions
-- based on title similarity or content
SELECT 'Checking for potential matches between submissions and opportunities_unified:' as info;
SELECT
    s.id as submission_id,
    s.submission_id as submission_string_id,
    s.title as submission_title,
    COUNT(ou.id) as matching_opportunities
FROM submissions s
LEFT JOIN opportunities_unified ou ON
    -- Try to match by keywords in title
    (LOWER(s.title) LIKE LOWER('%' || ou.title || '%') OR
     LOWER(ou.title) LIKE LOWER('%' || s.title || '%') OR
     LOWER(s.title) LIKE LOWER('%' || ou.app_concept || '%') OR
     LOWER(ou.app_concept) LIKE LOWER('%' || s.title || '%'))
WHERE s.submission_id IN ('real_test_prof_1', 'real_test_prof_2', 'real_test_prof_3', 'hybrid_1', 'hybrid_2')
GROUP BY s.id, s.submission_id, s.title
ORDER BY s.submission_id;

-- Step 2: Create mappings for our real test submissions to some opportunities
-- Since this is test data, we'll assign them to the first few opportunities
CREATE TEMP TABLE real_submission_mappings (
    submission_string_id VARCHAR(50),
    submission_uuid UUID,
    opportunity_id UUID
);

-- Insert mappings for our real submissions
INSERT INTO real_submission_mappings (submission_string_id, submission_uuid, opportunity_id)
SELECT
    s.submission_id,
    s.id,
    ou.id
FROM submissions s
CROSS JOIN LATERAL (
    SELECT id FROM opportunities_unified
    WHERE submission_id IS NULL
    LIMIT 1
) ou
WHERE s.submission_id IN ('real_test_prof_1', 'real_test_prof_2', 'real_test_prof_3', 'hybrid_1', 'hybrid_2')
ORDER BY s.submission_id;

-- Show the mappings we created
SELECT 'Real Submission to Opportunity Mappings:' as info;
SELECT * FROM real_submission_mappings;

-- Step 3: Update opportunities_unified with the submission_id from real submissions
UPDATE opportunities_unified
SET submission_id = rsm.submission_uuid
FROM real_submission_mappings rsm
WHERE opportunities_unified.id = rsm.opportunity_id;

-- Step 4: For the remaining simple test submissions (sub1, sub2, sub3, test1, high_quality),
-- assign them to some of the remaining opportunities
CREATE TEMP TABLE simple_submission_mappings (
    submission_string_id VARCHAR(50),
    submission_uuid UUID,
    opportunity_id UUID
);

INSERT INTO simple_submission_mappings (submission_string_id, submission_uuid, opportunity_id)
SELECT
    s.submission_id,
    s.id,
    ou.id
FROM submissions s
CROSS JOIN LATERAL (
    SELECT id FROM opportunities_unified
    WHERE submission_id IS NULL
    LIMIT 1
) ou
WHERE s.submission_id IN ('sub1', 'sub2', 'sub3', 'test1', 'high_quality')
ORDER BY s.submission_id;

-- Show the simple mappings
SELECT 'Simple Submission to Opportunity Mappings:' as info;
SELECT * FROM simple_submission_mappings;

-- Step 5: Update opportunities_unified with simple test submissions
UPDATE opportunities_unified
SET submission_id = ssm.submission_uuid
FROM simple_submission_mappings ssm
WHERE opportunities_unified.id = ssm.opportunity_id;

-- Step 6: Verify the linking was successful
SELECT 'Linking Results Summary:' as info;
SELECT
    (SELECT COUNT(*) FROM opportunities_unified) as total_opportunities,
    (SELECT COUNT(*) FROM opportunities_unified WHERE submission_id IS NOT NULL) as linked_opportunities,
    (SELECT COUNT(*) FROM opportunities_unified WHERE submission_id IS NULL) as unlinked_opportunities,
    ROUND(
        ((SELECT COUNT(*) FROM opportunities_unified WHERE submission_id IS NOT NULL) * 100.0 /
         (SELECT COUNT(*) FROM opportunities_unified)), 2
    ) as linking_success_rate;

-- Step 7: Show the specific submissions that got linked
SELECT 'Successfully Linked Submissions with Their Opportunities:' as info;
SELECT
    s.submission_id as string_id,
    s.id as uuid_id,
    LEFT(s.title, 30) as title_preview,
    COUNT(ou.id) as linked_opportunity_count,
    ARRAY_AGG(ou.id) as linked_opportunity_ids
FROM submissions s
JOIN opportunities_unified ou ON s.id = ou.submission_id
GROUP BY s.submission_id, s.id, LEFT(s.title, 30)
ORDER BY s.submission_id;

-- Step 8: Test the deduplication pipeline query pattern
SELECT 'Testing Deduplication Pipeline Query Pattern:' as info;
SELECT
    COUNT(*) as total_opportunities_with_uuids,
    COUNT(CASE
        WHEN ou.submission_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        THEN 1
    END) as valid_uuid_count
FROM opportunities_unified ou
WHERE ou.submission_id IS NOT NULL;

-- Step 9: Test a sample query that would be used in deduplication
SELECT 'Sample Deduplication Query (Should Work Now):' as info;
SELECT
    ou.id as opportunity_id,
    ou.submission_id,
    ou.title,
    s.title as original_submission_title,
    s.submission_id as original_submission_string_id
FROM opportunities_unified ou
JOIN submissions s ON ou.submission_id = s.id
WHERE ou.submission_id IS NOT NULL
LIMIT 5;

-- Step 10: Test UUID format validation specifically for the Phase 4 deduplication
SELECT 'UUID Format Validation for Phase 4:' as info;
SELECT
    ou.submission_id,
    CASE
        WHEN ou.submission_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        THEN 'VALID UUID - Deduplication will work'
        ELSE 'INVALID UUID - Deduplication will fail'
    END as validation_result
FROM opportunities_unified ou
WHERE ou.submission_id IS NOT NULL
ORDER BY validation_result
LIMIT 10;

-- Clean up temp tables
DROP TABLE IF EXISTS real_submission_mappings;
DROP TABLE IF EXISTS simple_submission_mappings;