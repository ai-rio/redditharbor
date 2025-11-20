-- Link All Remaining Submissions to Opportunities_Unified
-- This script ensures all 10 submissions get linked to distinct opportunity records

-- Step 1: Get all remaining unlinked submissions
CREATE TEMP TABLE remaining_submissions AS
SELECT
    s.id as submission_uuid,
    s.submission_id as submission_string_id,
    s.title
FROM submissions s
WHERE s.id NOT IN (
    SELECT DISTINCT submission_id
    FROM opportunities_unified
    WHERE submission_id IS NOT NULL
)
ORDER BY s.submission_id;

SELECT 'Remaining Unlinked Submissions:' as info;
SELECT * FROM remaining_submissions;

-- Step 2: Get remaining unlinked opportunities
CREATE TEMP TABLE remaining_opportunities AS
SELECT
    ou.id as opportunity_id,
    ou.title as opportunity_title
FROM opportunities_unified ou
WHERE ou.submission_id IS NULL
ORDER BY ou.id
LIMIT 10;  -- We only need 8 more for our remaining 8 submissions

SELECT 'Available Unlinked Opportunities:' as info;
SELECT COUNT(*) as available_opportunities
FROM remaining_opportunities;

-- Step 3: Create mappings for all remaining submissions
-- Using ROW_NUMBER() to ensure we get distinct opportunities
WITH numbered_submissions AS (
    SELECT
        rs.submission_uuid,
        rs.submission_string_id,
        rs.title,
        ROW_NUMBER() OVER (ORDER BY rs.submission_string_id) as submission_row
    FROM remaining_submissions rs
),
numbered_opportunities AS (
    SELECT
        ro.opportunity_id,
        ROW_NUMBER() OVER (ORDER BY ro.opportunity_id) as opportunity_row
    FROM remaining_opportunities ro
)
SELECT 'Creating Mappings for Remaining Submissions:' as info;
SELECT
    ns.submission_string_id,
    ns.submission_uuid,
    no.opportunity_id,
    ns.title as submission_title
FROM numbered_submissions ns
JOIN numbered_opportunities no ON ns.submission_row = no.opportunity_row
ORDER BY ns.submission_string_id;

-- Step 4: Update opportunities_unified with remaining submission mappings
UPDATE opportunities_unified
SET submission_id = numbered_submissions.submission_uuid
FROM (
    SELECT
        rs.submission_uuid,
        rs.submission_string_id,
        rs.title,
        ROW_NUMBER() OVER (ORDER BY rs.submission_string_id) as submission_row
    FROM remaining_submissions rs
) numbered_submissions
JOIN (
    SELECT
        ro.opportunity_id,
        ROW_NUMBER() OVER (ORDER BY ro.opportunity_id) as opportunity_row
    FROM remaining_opportunities ro
) numbered_opportunities ON numbered_submissions.submission_row = numbered_opportunities.opportunity_row
WHERE opportunities_unified.id = numbered_opportunities.opportunity_id;

-- Step 5: Verify all submissions are now linked
SELECT 'Final Linking Verification:' as info;
SELECT
    s.submission_id as string_id,
    s.id as uuid_id,
    LEFT(s.title, 40) as title_preview,
    COUNT(ou.id) as linked_opportunity_count
FROM submissions s
JOIN opportunities_unified ou ON s.id = ou.submission_id
GROUP BY s.submission_id, s.id, LEFT(s.title, 40)
ORDER BY s.submission_id;

-- Step 6: Complete verification summary
SELECT 'Complete Linking Summary:' as info;
SELECT
    (SELECT COUNT(*) FROM submissions) as total_submissions,
    (SELECT COUNT(*) FROM opportunities_unified) as total_opportunities,
    (SELECT COUNT(*) FROM opportunities_unified WHERE submission_id IS NOT NULL) as linked_opportunities,
    (SELECT COUNT(DISTINCT submission_id) FROM opportunities_unified WHERE submission_id IS NOT NULL) as unique_submissions_linked,
    ROUND(
        ((SELECT COUNT(*) FROM opportunities_unified WHERE submission_id IS NOT NULL) * 100.0 /
         (SELECT COUNT(*) FROM submissions)), 2
    ) as linking_coverage;

-- Step 7: Test all UUID formats are valid
SELECT 'Comprehensive UUID Format Validation:' as info;
SELECT
    COUNT(*) as total_linked_opportunities,
    COUNT(CASE
        WHEN ou.submission_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        THEN 1
        ELSE NULL
    END) as valid_uuids,
    COUNT(CASE
        WHEN ou.submission_id::text !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        THEN 1
        ELSE NULL
    END) as invalid_uuids
FROM opportunities_unified ou
WHERE ou.submission_id IS NOT NULL;

-- Step 8: Test a realistic deduplication query that will be used in Phase 4
SELECT 'Phase 4 Deduplication Query Test (Should Work Now):' as info;
SELECT
    ou.id as opportunity_id,
    ou.submission_id,
    ou.title as opportunity_title,
    s.title as original_title,
    s.submission_id as original_string_id,
    ou.metadata,
    ou.created_at,
    ou.updated_at
FROM opportunities_unified ou
JOIN submissions s ON ou.submission_id = s.id
WHERE ou.submission_id IS NOT NULL
  AND ou.submission_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
ORDER BY s.submission_id;

-- Step 9: Test specific UUID format validation that failed before
SELECT 'Specific UUID Format Test for Error Cases:' as info;
SELECT
    s.submission_id as original_string_id,
    s.id as proper_uuid,
    ou.id as opportunity_id,
    CASE
        WHEN s.id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        THEN 'Submission UUID is valid'
        ELSE 'Submission UUID is invalid'
    END as submission_uuid_validation,
    CASE
        WHEN ou.submission_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        THEN 'Opportunity submission_id is valid'
        ELSE 'Opportunity submission_id is invalid'
    END as opportunity_uuid_validation
FROM submissions s
JOIN opportunities_unified ou ON s.id = ou.submission_id
WHERE s.submission_id IN ('high_quality', 'sub1', 'sub2', 'sub3', 'test1')
ORDER BY s.submission_id;

-- Clean up
DROP TABLE IF EXISTS remaining_submissions;
DROP TABLE IF EXISTS remaining_opportunities;