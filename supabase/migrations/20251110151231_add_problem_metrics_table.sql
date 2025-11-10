-- ============================================================================
-- Problem Metrics Table for Reddit Validation Signals
-- Migration: 20251110151231_add_problem_metrics_table.sql
-- Created: 2025-11-10
-- Description: Add credibility layer tracking for opportunity validation
--
-- PURPOSE:
-- This table aggregates Reddit engagement metrics to provide transparent
-- validation data showing real-world problem signals. It sits on top of the
-- existing opportunity scoring system to show users concrete evidence of
-- demand, discussion patterns, and community engagement.
--
-- KEY METRICS:
-- - Engagement depth (comment count, upvotes)
-- - Spread/reach (subreddit diversity)
-- - Momentum (trending score - percent change in activity)
-- - Intent signals (willingness to pay mentions)
-- - Temporal patterns (first seen, last seen, recency)
-- ============================================================================

-- ============================================================================
-- PART 1: CREATE PROBLEM_METRICS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS problem_metrics (
    -- Primary identifier - references the submission that defines this problem
    problem_id UUID PRIMARY KEY,

    -- Engagement metrics
    comment_count INTEGER NOT NULL DEFAULT 0,
    total_upvotes INTEGER NOT NULL DEFAULT 0,

    -- Reach metrics
    subreddit_spread INTEGER NOT NULL DEFAULT 0,

    -- Momentum metrics
    trending_score FLOAT NOT NULL DEFAULT 0.0,

    -- Intent signals
    intent_signal_count INTEGER NOT NULL DEFAULT 0,

    -- Temporal tracking
    first_seen TIMESTAMP WITH TIME ZONE NOT NULL,
    last_seen TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Foreign key constraint
    CONSTRAINT fk_problem_metrics_submission
        FOREIGN KEY (problem_id)
        REFERENCES submissions(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    -- Data integrity constraints
    CONSTRAINT chk_comment_count_non_negative
        CHECK (comment_count >= 0),

    CONSTRAINT chk_total_upvotes_non_negative
        CHECK (total_upvotes >= 0),

    CONSTRAINT chk_subreddit_spread_non_negative
        CHECK (subreddit_spread >= 0),

    CONSTRAINT chk_intent_signal_count_non_negative
        CHECK (intent_signal_count >= 0),

    CONSTRAINT chk_temporal_order
        CHECK (last_seen >= first_seen)
);

-- ============================================================================
-- PART 2: CREATE INDEXES FOR PERFORMANCE
-- ============================================================================

-- Index for sorting by trending score (descending - hottest problems first)
CREATE INDEX IF NOT EXISTS idx_problem_metrics_trending_score
    ON problem_metrics(trending_score DESC);

-- Index for sorting by comment count (descending - most discussed problems)
CREATE INDEX IF NOT EXISTS idx_problem_metrics_comment_count
    ON problem_metrics(comment_count DESC);

-- Index for sorting by total upvotes (descending - most validated problems)
CREATE INDEX IF NOT EXISTS idx_problem_metrics_total_upvotes
    ON problem_metrics(total_upvotes DESC);

-- Index for sorting by subreddit spread (descending - widest reach)
CREATE INDEX IF NOT EXISTS idx_problem_metrics_subreddit_spread
    ON problem_metrics(subreddit_spread DESC);

-- Index for sorting by intent signals (descending - strongest monetization potential)
CREATE INDEX IF NOT EXISTS idx_problem_metrics_intent_signal_count
    ON problem_metrics(intent_signal_count DESC);

-- Index for temporal queries (most recent activity)
CREATE INDEX IF NOT EXISTS idx_problem_metrics_last_seen
    ON problem_metrics(last_seen DESC);

-- Composite index for filtering active + trending problems
CREATE INDEX IF NOT EXISTS idx_problem_metrics_active_trending
    ON problem_metrics(last_seen DESC, trending_score DESC)
    WHERE trending_score > 0;

-- ============================================================================
-- PART 3: ADD COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE problem_metrics IS
'Aggregated Reddit validation signals for opportunity credibility tracking. Provides transparent metrics showing real-world problem validation through engagement, reach, and intent signals.';

COMMENT ON COLUMN problem_metrics.problem_id IS
'UUID reference to the submission that defines this problem/opportunity';

COMMENT ON COLUMN problem_metrics.comment_count IS
'Total number of comments discussing this problem across all threads';

COMMENT ON COLUMN problem_metrics.total_upvotes IS
'Aggregated upvote count showing community validation of the problem';

COMMENT ON COLUMN problem_metrics.subreddit_spread IS
'Number of unique subreddits where this problem has been mentioned (indicates breadth of concern)';

COMMENT ON COLUMN problem_metrics.trending_score IS
'Percent change in activity over time (positive = gaining momentum, negative = declining interest)';

COMMENT ON COLUMN problem_metrics.intent_signal_count IS
'Count of comments expressing willingness to pay or strong desire for solution (monetization validation)';

COMMENT ON COLUMN problem_metrics.first_seen IS
'Timestamp of earliest mention of this problem on Reddit';

COMMENT ON COLUMN problem_metrics.last_seen IS
'Timestamp of most recent discussion of this problem';

COMMENT ON COLUMN problem_metrics.updated_at IS
'Timestamp when these metrics were last calculated/refreshed';

-- ============================================================================
-- PART 4: CREATE HELPER FUNCTIONS
-- ============================================================================

-- Function to calculate trending score based on recent activity
CREATE OR REPLACE FUNCTION calculate_trending_score(
    p_problem_id UUID,
    p_lookback_days INTEGER DEFAULT 7
) RETURNS FLOAT AS $$
DECLARE
    recent_activity INTEGER;
    baseline_activity INTEGER;
    trending_pct FLOAT;
BEGIN
    -- Count activity in last N days
    SELECT COUNT(*)
    INTO recent_activity
    FROM comments
    WHERE submission_id = p_problem_id
      AND created_at >= NOW() - (p_lookback_days || ' days')::INTERVAL;

    -- Count activity in previous N days (baseline)
    SELECT COUNT(*)
    INTO baseline_activity
    FROM comments
    WHERE submission_id = p_problem_id
      AND created_at >= NOW() - (p_lookback_days * 2 || ' days')::INTERVAL
      AND created_at < NOW() - (p_lookback_days || ' days')::INTERVAL;

    -- Calculate percentage change (avoid division by zero)
    IF baseline_activity = 0 THEN
        IF recent_activity > 0 THEN
            RETURN 100.0; -- 100% increase from zero baseline
        ELSE
            RETURN 0.0; -- No activity in either period
        END IF;
    ELSE
        trending_pct := ((recent_activity - baseline_activity)::FLOAT / baseline_activity::FLOAT) * 100.0;
        RETURN trending_pct;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_trending_score IS
'Calculate trending score as percent change in comment activity. Compares recent period (default 7 days) to previous equivalent period.';

-- Function to refresh metrics for a specific problem
CREATE OR REPLACE FUNCTION refresh_problem_metrics(p_problem_id UUID)
RETURNS VOID AS $$
DECLARE
    v_comment_count INTEGER;
    v_subreddit_spread INTEGER;
    v_total_upvotes INTEGER;
    v_trending_score FLOAT;
    v_intent_signal_count INTEGER;
    v_first_seen TIMESTAMP WITH TIME ZONE;
    v_last_seen TIMESTAMP WITH TIME ZONE;
BEGIN
    -- Calculate comment count
    SELECT COUNT(*)
    INTO v_comment_count
    FROM comments
    WHERE submission_id = p_problem_id;

    -- Calculate subreddit spread
    SELECT COUNT(DISTINCT subreddit)
    INTO v_subreddit_spread
    FROM comments
    WHERE submission_id = p_problem_id;

    -- Calculate total upvotes (from submission + sum of comment scores)
    SELECT
        COALESCE((SELECT CAST(score->>'value' AS INTEGER) FROM submissions WHERE id = p_problem_id), 0) +
        COALESCE(SUM(CAST(score->>'value' AS INTEGER)), 0)
    INTO v_total_upvotes
    FROM comments
    WHERE submission_id = p_problem_id;

    -- Calculate trending score
    SELECT calculate_trending_score(p_problem_id)
    INTO v_trending_score;

    -- Calculate intent signal count (simple keyword detection)
    -- Look for phrases indicating willingness to pay or strong need
    SELECT COUNT(*)
    INTO v_intent_signal_count
    FROM comments
    WHERE submission_id = p_problem_id
      AND (
          body ILIKE '%would pay%' OR
          body ILIKE '%willing to pay%' OR
          body ILIKE '%take my money%' OR
          body ILIKE '%shut up and take%' OR
          body ILIKE '%need this%' OR
          body ILIKE '%desperately need%'
      );

    -- Get temporal boundaries
    SELECT
        MIN(created_at),
        MAX(created_at)
    INTO v_first_seen, v_last_seen
    FROM (
        SELECT created_at FROM submissions WHERE id = p_problem_id
        UNION ALL
        SELECT created_at FROM comments WHERE submission_id = p_problem_id
    ) combined;

    -- Upsert metrics
    INSERT INTO problem_metrics (
        problem_id,
        comment_count,
        subreddit_spread,
        total_upvotes,
        trending_score,
        intent_signal_count,
        first_seen,
        last_seen,
        updated_at
    ) VALUES (
        p_problem_id,
        v_comment_count,
        v_subreddit_spread,
        v_total_upvotes,
        v_trending_score,
        v_intent_signal_count,
        v_first_seen,
        v_last_seen,
        NOW()
    )
    ON CONFLICT (problem_id) DO UPDATE SET
        comment_count = EXCLUDED.comment_count,
        subreddit_spread = EXCLUDED.subreddit_spread,
        total_upvotes = EXCLUDED.total_upvotes,
        trending_score = EXCLUDED.trending_score,
        intent_signal_count = EXCLUDED.intent_signal_count,
        first_seen = EXCLUDED.first_seen,
        last_seen = EXCLUDED.last_seen,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_problem_metrics IS
'Recalculate and update all metrics for a specific problem_id. Safe to call repeatedly (upserts data).';

-- ============================================================================
-- PART 5: CREATE CONVENIENCE VIEWS
-- ============================================================================

-- View for top trending problems with validation signals
CREATE OR REPLACE VIEW v_trending_problems AS
SELECT
    pm.problem_id,
    s.title AS problem_title,
    s.text AS problem_description,
    s.subreddit AS source_subreddit,
    pm.comment_count,
    pm.subreddit_spread,
    pm.total_upvotes,
    pm.trending_score,
    pm.intent_signal_count,
    pm.first_seen,
    pm.last_seen,
    pm.updated_at,
    -- Calculate days since first seen
    EXTRACT(DAY FROM (NOW() - pm.first_seen))::INTEGER AS days_active,
    -- Calculate recency score (0-100, higher = more recent)
    CASE
        WHEN pm.last_seen >= NOW() - INTERVAL '1 day' THEN 100
        WHEN pm.last_seen >= NOW() - INTERVAL '7 days' THEN 75
        WHEN pm.last_seen >= NOW() - INTERVAL '30 days' THEN 50
        WHEN pm.last_seen >= NOW() - INTERVAL '90 days' THEN 25
        ELSE 0
    END AS recency_score
FROM problem_metrics pm
INNER JOIN submissions s ON pm.problem_id = s.id
WHERE pm.trending_score > 0
  AND pm.last_seen >= NOW() - INTERVAL '90 days'
ORDER BY pm.trending_score DESC;

COMMENT ON VIEW v_trending_problems IS
'Top trending problems sorted by momentum, filtered to active problems (last 90 days)';

-- View for highly validated problems (strong engagement signals)
CREATE OR REPLACE VIEW v_validated_problems AS
SELECT
    pm.problem_id,
    s.title AS problem_title,
    s.text AS problem_description,
    s.subreddit AS source_subreddit,
    pm.comment_count,
    pm.subreddit_spread,
    pm.total_upvotes,
    pm.trending_score,
    pm.intent_signal_count,
    pm.first_seen,
    pm.last_seen,
    -- Calculate validation score (weighted composite)
    (
        (pm.comment_count * 0.3) +
        (pm.subreddit_spread * 10 * 0.2) +
        (pm.total_upvotes * 0.1 * 0.3) +
        (pm.intent_signal_count * 5 * 0.2)
    ) AS validation_score
FROM problem_metrics pm
INNER JOIN submissions s ON pm.problem_id = s.id
WHERE pm.comment_count >= 5
   OR pm.subreddit_spread >= 2
   OR pm.intent_signal_count >= 1
ORDER BY validation_score DESC;

COMMENT ON VIEW v_validated_problems IS
'Problems with strong validation signals sorted by composite score (engagement + reach + intent)';

-- ============================================================================
-- PART 5B: HELPER FUNCTION FOR DASHBOARD
-- ============================================================================

-- Function to get opportunities with metrics joined for dashboard display
CREATE OR REPLACE FUNCTION get_opportunities_with_metrics()
RETURNS TABLE (
    submission_id UUID,
    opportunity_score FLOAT,
    problem_description TEXT,
    app_concept TEXT,
    core_functions JSONB,
    target_user TEXT,
    monetization_model TEXT,
    subreddit TEXT,
    title TEXT,
    comment_count INTEGER,
    trending_score FLOAT,
    subreddit_spread INTEGER,
    intent_signal_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ao.submission_id,
        ao.opportunity_score,
        ao.problem_description,
        ao.app_concept,
        ao.core_functions,
        ao.target_user,
        ao.monetization_model,
        ao.subreddit,
        ao.title,
        COALESCE(pm.comment_count, 0)::INTEGER,
        COALESCE(pm.trending_score, 0)::FLOAT,
        COALESCE(pm.subreddit_spread, 0)::INTEGER,
        COALESCE(pm.intent_signal_count, 0)::INTEGER
    FROM app_opportunities ao
    LEFT JOIN problem_metrics pm ON ao.submission_id = pm.problem_id
    WHERE ao.opportunity_score >= 25.0
    ORDER BY ao.opportunity_score DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_opportunities_with_metrics IS
'Fetch opportunities with credibility metrics for dashboard display. Joins app_opportunities with problem_metrics for comprehensive view.';

-- ============================================================================
-- PART 6: DATA GOVERNANCE
-- ============================================================================

-- Row Level Security (RLS) - enable for production
-- ALTER TABLE problem_metrics ENABLE ROW LEVEL SECURITY;

-- Example policy (adjust based on your auth setup)
-- CREATE POLICY "Enable read access for all users" ON problem_metrics
--     FOR SELECT USING (true);

-- ============================================================================
-- MIGRATION COMPLETED SUCCESSFULLY
-- ============================================================================

-- Verify migration with these queries:
-- SELECT COUNT(*) FROM problem_metrics;
-- SELECT * FROM v_trending_problems LIMIT 10;
-- SELECT * FROM v_validated_problems LIMIT 10;

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

-- Example 1: Refresh metrics for a specific problem
-- SELECT refresh_problem_metrics('your-submission-uuid-here');

-- Example 2: Bulk refresh for all submissions with comments
-- DO $$
-- DECLARE
--     submission_record RECORD;
-- BEGIN
--     FOR submission_record IN
--         SELECT DISTINCT submission_id
--         FROM comments
--         WHERE submission_id IS NOT NULL
--     LOOP
--         PERFORM refresh_problem_metrics(submission_record.submission_id);
--     END LOOP;
-- END $$;

-- Example 3: Find problems with strong monetization intent
-- SELECT * FROM problem_metrics
-- WHERE intent_signal_count >= 3
-- ORDER BY intent_signal_count DESC, total_upvotes DESC;

-- Example 4: Find rapidly growing problems
-- SELECT * FROM v_trending_problems
-- WHERE trending_score > 50
-- ORDER BY trending_score DESC;
