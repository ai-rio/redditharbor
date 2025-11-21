-- Populate Missing Submission IDs in opportunities_unified
-- This script links opportunities_unified records to their corresponding submissions
-- by matching on title and other relevant fields

-- Step 1: Create mapping between submissions and opportunities_unified based on title
-- Since both tables should have the same content, we can match by title
WITH submission_opportunity_mapping AS (
    SELECT
        s.id as submission_uuid,
        s.submission_id as submission_string_id,
        s.title,
        s.content,
        ou.id as opportunity_id
    FROM submissions s
    JOIN opportunities_unified ou ON
        -- Match by title first (most reliable)
        s.title = ou.title OR
        -- Fallback: match by content if available
        (CASE
            WHEN s.content IS NOT NULL AND ou.description IS NOT NULL
            THEN s.content = ou.description
            ELSE false
        END)
    WHERE ou.submission_id IS NULL  -- Only target opportunities without submission_id
),
-- Count how many matches we find
match_stats AS (
    SELECT
        COUNT(*) as total_matches,
        COUNT(DISTINCT submission_string_id) as unique_submissions_matched,
        COUNT(DISTINCT opportunity_id) as unique_opportunities_matched
    FROM submission_opportunity_mapping
)
SELECT 'Mapping Statistics Before Update:' as info;
SELECT * FROM match_stats;

-- Step 2: Show some sample matches before updating
SELECT 'Sample Submission-Opportunity Matches:' as info;
SELECT
    som.submission_string_id,
    som.submission_uuid,
    LEFT(som.title, 50) as title_preview,
    som.opportunity_id
FROM submission_opportunity_mapping som
LIMIT 10;

-- Step 3: Update opportunities_unified with proper submission_id values
-- This will establish the foreign key relationship
UPDATE opportunities_unified
SET submission_id = som.submission_uuid
FROM submission_opportunity_mapping som
WHERE opportunities_unified.id = som.opportunity_id;

-- Step 4: Verify the update was successful
SELECT 'After Update - Opportunities with submission_id:' as info;
SELECT
    COUNT(*) as total_opportunities,
    COUNT(submission_id) as opportunities_with_submission_id,
    COUNT(CASE WHEN submission_id IS NOT NULL THEN 1 END) as non_null_submission_ids,
    ROUND(
        (COUNT(CASE WHEN submission_id IS NOT NULL THEN 1 END) * 100.0 / COUNT(*)), 2
    ) as percentage_linked
FROM opportunities_unified;

-- Step 5: Check the specific submissions that got linked
SELECT 'Successfully Linked Submissions:' as info;
SELECT
    s.submission_id as string_id,
    s.id as uuid_id,
    LEFT(s.title, 50) as title_preview,
    COUNT(ou.id) as linked_opportunities
FROM submissions s
JOIN opportunities_unified ou ON s.id = ou.submission_id
WHERE s.submission_id IN ('high_quality', 'sub1', 'sub2', 'sub3', 'test1', 'hybrid_1', 'hybrid_2', 'real_test_prof_1', 'real_test_prof_2', 'real_test_prof_3')
GROUP BY s.submission_id, s.id, LEFT(s.title, 50)
ORDER BY s.submission_id;

-- Step 6: Test a UUID-based query to ensure deduplication pipeline will work
SELECT 'Testing UUID-based Query (Simulating Deduplication Pipeline):' as info;
SELECT
    ou.id,
    ou.submission_id,
    ou.title,
    CASE
        WHEN ou.submission_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN 'Valid UUID'
        ELSE 'Invalid UUID'
    END as uuid_validation
FROM opportunities_unified ou
WHERE ou.submission_id IS NOT NULL
LIMIT 5;

-- Step 7: Test the specific query pattern that deduplication pipeline uses
SELECT 'Testing Deduplication Pipeline Query Pattern:' as info;
SELECT
    COUNT(*) as total_opportunities_with_valid_uuids,
    COUNT(CASE
        WHEN ou.submission_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        THEN 1
    END) as valid_uuid_count
FROM opportunities_unified ou
WHERE ou.submission_id IS NOT NULL;

-- Step 8: Check for any remaining opportunities without submission_id
SELECT 'Remaining Opportunities Without submission_id:' as info;
SELECT
    COUNT(*) as unlinked_opportunities,
    ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM opportunities_unified)), 2) as percentage_unlinked
FROM opportunities_unified
WHERE submission_id IS NULL;

-- If there are still unlinked opportunities, show some samples for manual review
SELECT 'Sample Unlinked Opportunities (may need manual linking):' as info;
SELECT
    id,
    LEFT(title, 50) as title_preview,
    LEFT(app_concept, 30) as concept_preview
FROM opportunities_unified
WHERE submission_id IS NULL
LIMIT 5;

-- Step 9: Final verification summary
SELECT 'Final Verification Summary:' as info;
SELECT
    'Total Submissions: ' || (SELECT COUNT(*) FROM submissions) as submissions_count,
    'Total Opportunities: ' || (SELECT COUNT(*) FROM opportunities_unified) as opportunities_count,
    'Linked Opportunities: ' || (SELECT COUNT(*) FROM opportunities_unified WHERE submission_id IS NOT NULL) as linked_count,
    'Unlinked Opportunities: ' || (SELECT COUNT(*) FROM opportunities_unified WHERE submission_id IS NULL) as unlinked_count,
    'Link Success Rate: ' || ROUND(
        ((SELECT COUNT(*) FROM opportunities_unified WHERE submission_id IS NOT NULL) * 100.0 /
         (SELECT COUNT(*) FROM opportunities_unified)), 2
    ) || '%' as success_rate;