-- Phase 4 UUID Format Fixes
-- This script fixes invalid UUID format errors in test data

-- Step 1: Create mapping table for test submission IDs to proper UUIDs
CREATE TEMP TABLE test_submission_uuid_mappings (
    old_submission_id VARCHAR(255),
    new_submission_id UUID PRIMARY KEY
);

-- Insert mappings for problematic test submission IDs
INSERT INTO test_submission_uuid_mappings (old_submission_id, new_submission_id) VALUES
('real_test_prof_1', '08f7631e-f7ae-5bc7-b688-a2e4824d67e3'),
('real_test_prof_2', '9be2d52d-565c-5908-a371-99f6e5e6a229'),
('real_test_prof_3', '3dcc503d-c487-5aab-9d75-cd2479cadd42'),
('high_quality', '7a878720-ec88-553a-bc9c-3b51b785148f');

-- Step 2: Show current problematic records before fix
SELECT 'Current problematic app_opportunities records:' as info;
SELECT submission_id, COUNT(*) as count
FROM app_opportunities
WHERE submission_id IN (SELECT old_submission_id FROM test_submission_uuid_mappings)
GROUP BY submission_id;

-- Step 3: Update app_opportunities table with proper UUIDs
UPDATE app_opportunities
SET submission_id = new_uuid.new_submission_id
FROM test_submission_uuid_mappings new_uuid
WHERE app_opportunities.submission_id = new_uuid.old_submission_id;

-- Step 4: Verify the fix
SELECT 'Updated app_opportunities records:' as info;
SELECT submission_id, COUNT(*) as count
FROM app_opportunities
WHERE submission_id IN (SELECT new_submission_id FROM test_submission_uuid_mappings)
GROUP BY submission_id;

-- Step 5: Check for any other tables that might reference the old string IDs
-- Note: We need to check opportunities table (which has UUID submission_id)
-- but it might not have records referencing these test IDs

-- Step 6: Check if we need to create placeholder submissions for these UUIDs
SELECT 'Checking if submission entries exist for new UUIDs:' as info;
SELECT s.id, s.submission_id
FROM submissions s
WHERE s.id IN (SELECT new_submission_id FROM test_submission_uuid_mappings)
OR s.submission_id IN (SELECT old_submission_id FROM test_submission_uuid_mappings);

-- If the submissions don't exist, we may need to create them
-- This would be needed if there are foreign key constraints

-- Step 7: Show final verification
SELECT 'Final verification - no more string-based test submission IDs should exist:' as info;
SELECT COUNT(*) as remaining_string_issues
FROM app_opportunities
WHERE submission_id::text LIKE '%real_test_prof_%'
   OR submission_id::text LIKE '%high_quality%';

SELECT 'All test submission UUID mappings:' as info;
SELECT old_submission_id, new_submission_id
FROM test_submission_uuid_mappings
ORDER BY old_submission_id;