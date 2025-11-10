-- ============================================================================
-- Verification Query: Confirm Comment-Submission Linking
-- ============================================================================
-- This query verifies that the DLT pipeline bug has been fixed and comments
-- are now properly linked to their parent submissions.
-- ============================================================================

-- ============================================================================
-- 1. SUMMARY: Comment Linking Statistics
-- ============================================================================
SELECT
    'SUMMARY' as report_section,
    COUNT(*) as total_comments,
    COUNT(submission_id) as linked_to_submission,
    COUNT(*) - COUNT(submission_id) as orphaned,
    ROUND(
        (COUNT(submission_id)::decimal / COUNT(*)::decimal) * 100,
        2
    ) as link_success_rate_percent
FROM public.comments;

-- ============================================================================
-- 2. DETAIL: Comments by Submission
-- ============================================================================
SELECT
    'DETAIL_BY_SUBMISSION' as report_section,
    s.id as submission_uuid,
    s.submission_id as reddit_id,
    s.title,
    s.subreddit,
    COUNT(c.comment_id) as comment_count
FROM public.submissions s
LEFT JOIN public.comments c ON s.id = c.submission_id
GROUP BY s.id, s.submission_id, s.title, s.subreddit
HAVING COUNT(c.comment_id) > 0
ORDER BY comment_count DESC
LIMIT 20;

-- ============================================================================
-- 3. SAMPLE: Verify Individual Comment Links
-- ============================================================================
SELECT
    'SAMPLE_COMMENTS' as report_section,
    c.comment_id,
    c.link_id,
    s.submission_id as reddit_submission_id,
    s.id as submission_uuid,
    s.title as submission_title,
    s.subreddit,
    c.body,
    c.upvotes,
    c.created_at
FROM public.comments c
JOIN public.submissions s ON c.submission_id = s.id
ORDER BY c.created_at DESC
LIMIT 15;

-- ============================================================================
-- 4. PROBLEM: Check for Still-Orphaned Comments
-- ============================================================================
SELECT
    'ORPHANED_COMMENTS' as report_section,
    c.comment_id,
    c.link_id,
    c.body,
    c.parent_id,
    c.created_at
FROM public.comments c
WHERE c.submission_id IS NULL
  AND c.link_id IS NOT NULL
ORDER BY c.created_at DESC
LIMIT 20;

-- ============================================================================
-- 5. CREDIBILITY METRICS: Verify Metrics Can Now Work
-- ============================================================================
-- This simulates the credibility metrics query that depends on comment links
SELECT
    'CREDIBILITY_METRICS' as report_section,
    s.id as submission_uuid,
    s.submission_id as reddit_id,
    s.title,
    s.subreddit,
    s.upvotes,
    COUNT(c.comment_id) as total_comments,
    SUM(c.upvotes) as total_comment_upvotes,
    ROUND(AVG(c.upvotes)::decimal, 2) as avg_comment_upvotes,
    -- This is a simple credibility metric example
    CASE
        WHEN COUNT(c.comment_id) = 0 THEN 0
        ELSE
            ROUND(
                (s.upvotes + SUM(c.upvotes))::decimal /
                (1 + COUNT(c.comment_id))::decimal,
                2
            )
    END as credibility_score
FROM public.submissions s
LEFT JOIN public.comments c ON s.id = c.submission_id
WHERE s.submission_id IS NOT NULL
GROUP BY s.id, s.submission_id, s.title, s.subreddit, s.upvotes
HAVING COUNT(c.comment_id) > 0
ORDER BY credibility_score DESC
LIMIT 10;

-- ============================================================================
-- 6. FINAL SUMMARY
-- ============================================================================
DO $$
DECLARE
    total_comms integer;
    linked_comms integer;
    orph_comms integer;
    link_rate numeric;
BEGIN
    SELECT
        COUNT(*),
        COUNT(submission_id),
        COUNT(*) - COUNT(submission_id),
        ROUND((COUNT(submission_id)::decimal / COUNT(*)::decimal) * 100, 2)
    INTO total_comms, linked_comms, orph_comms, link_rate
    FROM public.comments;

    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'VERIFICATION REPORT: Comment Linking';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Total Comments: %', total_comms;
    RAISE NOTICE 'Successfully Linked: %', linked_comms;
    RAISE NOTICE 'Still Orphaned: %', orph_comms;
    RAISE NOTICE 'Link Success Rate: %%%', link_rate;
    RAISE NOTICE '';

    IF link_rate >= 95 THEN
        RAISE NOTICE '✓ SUCCESS: Comment linking is working correctly!';
        RAISE NOTICE '  The DLT pipeline bug has been fixed.';
        RAISE NOTICE '  Credibility metrics can now function properly.';
    ELSIF link_rate >= 80 THEN
        RAISE NOTICE '~ PARTIAL: Most comments are linked but some remain orphaned.';
        RAISE NOTICE '  This may be acceptable if orphaned comments are from';
        RAISE NOTICE '  submissions not in the database.';
    ELSE
        RAISE NOTICE '✗ FAILED: Most comments are still orphaned.';
        RAISE NOTICE '  The DLT pipeline bug is NOT fixed.';
        RAISE NOTICE '  Credibility metrics will NOT work correctly.';
    END IF;

    RAISE NOTICE '========================================';
END $$;
