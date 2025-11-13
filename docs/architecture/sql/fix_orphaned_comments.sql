-- ============================================================================
-- Fix Orphaned Comments - Link Existing Comments to Submissions
-- ============================================================================
-- This script fixes the 8,779 comments that have NULL submission_id
-- by linking them to their parent submissions via link_id
--
-- Background: The DLT collection pipeline was collecting comments but not
-- populating the submission_id foreign key, making them orphaned.
--
-- Fix Strategy:
-- 1. Populate link_id field for comments that have it NULL
-- 2. Update submission_id (UUID) by joining link_id to submissions.submission_id
-- ============================================================================

-- Step 1: Check the current state
-- Shows how many comments are orphaned
SELECT
    'BEFORE' as status,
    COUNT(*) as total_comments,
    COUNT(submission_id) as with_submission_id,
    COUNT(*) - COUNT(submission_id) as orphaned_comments,
    COUNT(link_id) as with_link_id,
    COUNT(*) - COUNT(link_id) as missing_link_id
FROM public.comments
UNION ALL
SELECT
    'AFTER' as status,
    COUNT(*) as total_comments,
    COUNT(submission_id) as with_submission_id,
    COUNT(*) - COUNT(submission_id) as orphaned_comments,
    COUNT(link_id) as with_link_id,
    COUNT(*) - COUNT(link_id) as missing_link_id
FROM public.comments
WHERE 1=0;  -- This will be replaced by the actual AFTER query

-- Step 2: Backfill link_id for comments that have submission_id populated
-- If submission_id is populated with Reddit ID, use that to populate link_id
UPDATE public.comments
SET link_id = submission_id
WHERE link_id IS NULL
  AND submission_id IS NOT NULL
  AND submission_id ~ '^[a-zA-Z0-9]+$';  -- Basic validation it's a Reddit ID

-- Step 3: The main fix - link comments to submissions
-- This links comments.submission_id (UUID) to submissions.id (UUID)
-- by joining on: comments.link_id = submissions.submission_id
UPDATE public.comments
SET submission_id = s.id
FROM public.submissions s
WHERE public.comments.link_id = s.submission_id
  AND public.comments.submission_id IS NULL
  AND s.submission_id IS NOT NULL;

-- Get the count of updated rows
DO $$
DECLARE
    updated_count integer;
BEGIN
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Linked % comments to their parent submissions', updated_count;
END $$;

-- Step 4: Handle edge cases - try to extract link_id from parent_id
-- Some comments might have parent_id like "t3_1opmkio" where 1opmkio is the submission ID
UPDATE public.comments
SET link_id = CASE
    WHEN parent_id ~ '^t3_[a-zA-Z0-9]+$' THEN
        SUBSTRING(parent_id FROM 4)  -- Remove "t3_" prefix
    ELSE
        link_id  -- Keep existing value
END
WHERE (link_id IS NULL OR link_id = '')
  AND parent_id ~ '^t3_[a-zA-Z0-9]+$';

-- Step 5: Final backfill after extracting from parent_id
UPDATE public.comments
SET submission_id = s.id
FROM public.submissions s
WHERE public.comments.link_id = s.submission_id
  AND public.comments.submission_id IS NULL
  AND s.submission_id IS NOT NULL;

-- Step 6: Verify the fix worked
-- Check how many comments are now linked
SELECT
    'AFTER FIX' as status,
    COUNT(*) as total_comments,
    COUNT(submission_id) as with_submission_id,
    COUNT(*) - COUNT(submission_id) as still_orphaned,
    ROUND(
        (COUNT(submission_id)::decimal / COUNT(*)::decimal) * 100,
        2
    ) as linked_percentage
FROM public.comments;

-- Step 7: Show sample of linked comments for verification
-- This helps verify the fix worked correctly
SELECT
    c.comment_id,
    c.link_id,
    s.submission_id as reddit_submission_id,
    s.id as submission_uuid,
    s.title,
    s.subreddit
FROM public.comments c
JOIN public.submissions s ON c.submission_id = s.id
WHERE c.submission_id IS NOT NULL
ORDER BY c.created_at DESC
LIMIT 10;

-- Step 8: Optional - Create a view to monitor comment linking status
CREATE OR REPLACE VIEW comment_linking_status AS
SELECT
    'All Comments' as category,
    COUNT(*) as total_count,
    COUNT(submission_id) as linked_count,
    COUNT(*) - COUNT(submission_id) as orphaned_count,
    ROUND(
        (COUNT(submission_id)::decimal / NULLIF(COUNT(*), 0)) * 100,
        2
    ) as linked_percentage
FROM public.comments
UNION ALL
SELECT
    'With Link ID' as category,
    COUNT(*) as total_count,
    COUNT(submission_id) as linked_count,
    COUNT(*) - COUNT(submission_id) as orphaned_count,
    ROUND(
        (COUNT(submission_id)::decimal / NULLIF(COUNT(*), 0)) * 100,
        2
    ) as linked_percentage
FROM public.comments
WHERE link_id IS NOT NULL;

-- Step 9: Success message
DO $$
DECLARE
    total_comments integer;
    linked_comments integer;
    orphaned_count integer;
BEGIN
    SELECT COUNT(*), COUNT(submission_id), COUNT(*) - COUNT(submission_id)
    INTO total_comments, linked_comments, orphaned_count
    FROM public.comments;

    RAISE NOTICE '';
    RAISE NOTICE '=== COMMENT LINKING FIX COMPLETE ===';
    RAISE NOTICE 'Total Comments: %', total_comments;
    RAISE NOTICE 'Successfully Linked: % (%.2f%%)',
        linked_comments,
        (linked_comments::decimal / total_comments::decimal * 100);
    RAISE NOTICE 'Still Orphaned: % (%.2f%%)',
        orphaned_count,
        (orphaned_count::decimal / total_comments::decimal * 100);

    IF orphaned_count = 0 THEN
        RAISE NOTICE 'SUCCESS: All comments are now linked to submissions!';
    ELSE
        RAISE NOTICE 'WARNING: % comments could not be linked.', orphaned_count;
        RAISE NOTICE 'These may be from submissions not in the database.';
    END IF;
END $$;

-- ============================================================================
-- USAGE INSTRUCTIONS
-- ============================================================================
-- 1. Start Supabase: supabase start
-- 2. Run this script: psql "postgresql://postgres:postgres@127.0.0.1:54322/postgres" -f fix_orphaned_comments.sql
-- 3. Verify in Supabase Studio or run verification queries above
-- ============================================================================

-- To undo this fix (if needed):
-- WARNING: This will set submission_id to NULL for all comments
-- UPDATE public.comments SET submission_id = NULL WHERE submission_id IS NOT NULL;
