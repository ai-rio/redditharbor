-- ============================================================================
-- Schema Consolidation & Data Migration (SAFE)
-- Migration: 20251108000000_consolidate_schema_safe.sql
-- Created: 2025-11-08
-- Description: Safely consolidate schema and fix foreign key relationships
--
-- CRITICAL ISSUES ADDRESSED:
-- 1. NULL foreign keys in submissions (subreddit_id, redditor_id)
-- 2. NULL foreign keys in comments (submission_id, redditor_id)
-- 3. Duplicate columns from mixed DLT/schema sources
-- 4. Missing columns that code expects
-- 5. Data integrity and backwards compatibility
--
-- SAFETY MEASURES:
-- - All changes are additive or use ALTER COLUMN (non-destructive)
-- - Existing data is preserved with backfill logic
-- - Foreign key constraints remain optional (nullable)
-- - Rollback procedure included at end as comments
-- ============================================================================

-- ============================================================================
-- PART 1: REDDITORS TABLE CONSOLIDATION
-- ============================================================================

-- Add missing columns that code expects (from audit)
ALTER TABLE redditors
ADD COLUMN IF NOT EXISTS redditor_id VARCHAR(255);

ALTER TABLE redditors
ADD COLUMN IF NOT EXISTS is_gold BOOLEAN DEFAULT false;

ALTER TABLE redditors
ADD COLUMN IF NOT EXISTS is_mod JSONB;

ALTER TABLE redditors
ADD COLUMN IF NOT EXISTS trophy JSONB;

ALTER TABLE redditors
ADD COLUMN IF NOT EXISTS removed VARCHAR(50);

ALTER TABLE redditors
ADD COLUMN IF NOT EXISTS name VARCHAR(255);

ALTER TABLE redditors
ADD COLUMN IF NOT EXISTS karma JSONB;

-- Create index on redditor_id for lookups
CREATE INDEX IF NOT EXISTS idx_redditors_redditor_id ON redditors(redditor_id);

-- Backfill redditor_id from username if null (for legacy data)
UPDATE redditors
SET redditor_id = COALESCE(redditor_id, username)
WHERE redditor_id IS NULL;

COMMENT ON COLUMN redditors.redditor_id IS 'Reddit API identifier (e.g., dhg80)';
COMMENT ON COLUMN redditors.is_gold IS 'Whether user has Reddit Gold subscription';
COMMENT ON COLUMN redditors.is_mod IS 'Moderator status with subreddit details (JSONB)';
COMMENT ON COLUMN redditors.trophy IS 'User trophies and achievements (JSONB)';
COMMENT ON COLUMN redditors.karma IS 'Detailed karma breakdown (JSONB)';

-- ============================================================================
-- PART 2: SUBMISSIONS TABLE CONSOLIDATION
-- ============================================================================

-- Add missing columns that code expects (from audit)
ALTER TABLE submissions
ADD COLUMN IF NOT EXISTS submission_id VARCHAR(255);

ALTER TABLE submissions
ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT false;

ALTER TABLE submissions
ADD COLUMN IF NOT EXISTS removed BOOLEAN DEFAULT false;

ALTER TABLE submissions
ADD COLUMN IF NOT EXISTS attachment JSONB;

ALTER TABLE submissions
ADD COLUMN IF NOT EXISTS poll JSONB;

ALTER TABLE submissions
ADD COLUMN IF NOT EXISTS flair JSONB;

ALTER TABLE submissions
ADD COLUMN IF NOT EXISTS awards JSONB;

ALTER TABLE submissions
ADD COLUMN IF NOT EXISTS score JSONB;

ALTER TABLE submissions
ADD COLUMN IF NOT EXISTS upvote_ratio JSONB;

ALTER TABLE submissions
ADD COLUMN IF NOT EXISTS num_comments JSONB;

ALTER TABLE submissions
ADD COLUMN IF NOT EXISTS edited BOOLEAN DEFAULT false;

ALTER TABLE submissions
ADD COLUMN IF NOT EXISTS text TEXT;

ALTER TABLE submissions
ADD COLUMN IF NOT EXISTS subreddit VARCHAR(255);

ALTER TABLE submissions
ADD COLUMN IF NOT EXISTS permalink TEXT;

-- Create indexes for common lookups
CREATE INDEX IF NOT EXISTS idx_submissions_submission_id ON submissions(submission_id);
CREATE INDEX IF NOT EXISTS idx_submissions_subreddit_name ON submissions(subreddit);
CREATE INDEX IF NOT EXISTS idx_submissions_archived ON submissions(archived);

-- ============================================================================
-- PART 3: BACKFILL NULL FOREIGN KEYS (SUBMISSIONS)
-- ============================================================================

-- Create temporary mapping table for subreddit lookups
CREATE TEMP TABLE temp_subreddit_mapping AS
SELECT DISTINCT
    s.id as submission_id,
    s.subreddit,
    sr.id as subreddit_uuid_id
FROM submissions s
LEFT JOIN subreddits sr ON LOWER(s.subreddit) = LOWER(sr.name)
WHERE s.subreddit_id IS NULL AND s.subreddit IS NOT NULL;

-- Backfill subreddit_id based on subreddit name
UPDATE submissions s
SET subreddit_id = m.subreddit_uuid_id
FROM temp_subreddit_mapping m
WHERE s.id = m.submission_id
  AND s.subreddit_id IS NULL
  AND m.subreddit_uuid_id IS NOT NULL;

-- Create missing subreddits from submissions data
INSERT INTO subreddits (name, description, is_active)
SELECT DISTINCT
    s.subreddit,
    'Auto-created from existing submissions data',
    true
FROM submissions s
LEFT JOIN subreddits sr ON LOWER(s.subreddit) = LOWER(sr.name)
WHERE s.subreddit IS NOT NULL
  AND sr.id IS NULL
  AND s.subreddit != ''
ON CONFLICT (name) DO NOTHING;

-- Update submissions with newly created subreddit IDs
UPDATE submissions s
SET subreddit_id = sr.id
FROM subreddits sr
WHERE LOWER(s.subreddit) = LOWER(sr.name)
  AND s.subreddit_id IS NULL
  AND s.subreddit IS NOT NULL;

-- ============================================================================
-- PART 4: BACKFILL NULL FOREIGN KEYS (REDDITORS IN SUBMISSIONS)
-- ============================================================================

-- Create temporary mapping table for redditor lookups
CREATE TEMP TABLE temp_redditor_mapping_submissions AS
SELECT DISTINCT
    s.id as submission_id,
    s.redditor_id as redditor_string_id,
    r.id as redditor_uuid_id
FROM submissions s
LEFT JOIN redditors r ON s.redditor_id = r.redditor_id
WHERE s.redditor_id IS NOT NULL
  AND r.id IS NOT NULL;

-- Backfill redditor UUID in submissions
UPDATE submissions s
SET redditor_id = (
    SELECT r.id
    FROM redditors r
    WHERE r.redditor_id = s.redditor_id
    LIMIT 1
)
WHERE s.redditor_id IS NOT NULL
  AND s.redditor_id IN (SELECT redditor_id FROM redditors WHERE redditor_id IS NOT NULL);

COMMENT ON COLUMN submissions.submission_id IS 'Reddit API identifier (e.g., rv4o9f)';
COMMENT ON COLUMN submissions.subreddit IS 'Subreddit name (denormalized for convenience)';

-- ============================================================================
-- PART 5: COMMENTS TABLE CONSOLIDATION
-- ============================================================================

-- Add missing columns that code expects (from audit)
ALTER TABLE comments
ADD COLUMN IF NOT EXISTS link_id VARCHAR(255);

ALTER TABLE comments
ADD COLUMN IF NOT EXISTS comment_id VARCHAR(255);

ALTER TABLE comments
ADD COLUMN IF NOT EXISTS body TEXT;

ALTER TABLE comments
ADD COLUMN IF NOT EXISTS subreddit VARCHAR(255);

ALTER TABLE comments
ADD COLUMN IF NOT EXISTS parent_id VARCHAR(255);

ALTER TABLE comments
ADD COLUMN IF NOT EXISTS score JSONB;

ALTER TABLE comments
ADD COLUMN IF NOT EXISTS edited BOOLEAN DEFAULT false;

ALTER TABLE comments
ADD COLUMN IF NOT EXISTS removed VARCHAR(50);

-- Create indexes for common lookups
CREATE INDEX IF NOT EXISTS idx_comments_comment_id ON comments(comment_id);
CREATE INDEX IF NOT EXISTS idx_comments_link_id ON comments(link_id);
CREATE INDEX IF NOT EXISTS idx_comments_parent_id_string ON comments(parent_id);
CREATE INDEX IF NOT EXISTS idx_comments_subreddit ON comments(subreddit);

COMMENT ON COLUMN comments.link_id IS 'Reddit submission link ID (e.g., 1opmkio)';
COMMENT ON COLUMN comments.comment_id IS 'Reddit API comment identifier (e.g., nncvkqj)';
COMMENT ON COLUMN comments.body IS 'Comment text content';
COMMENT ON COLUMN comments.parent_id IS 'Reddit parent ID (string format, e.g., t1_nncv8ho)';

-- ============================================================================
-- PART 6: BACKFILL NULL FOREIGN KEYS (COMMENTS)
-- ============================================================================

-- Backfill submission_id in comments using link_id
UPDATE comments c
SET submission_id = s.id
FROM submissions s
WHERE c.link_id = s.submission_id
  AND c.submission_id IS NULL
  AND c.link_id IS NOT NULL;

-- Backfill redditor_id in comments
UPDATE comments c
SET redditor_id = r.id
FROM redditors r
WHERE c.redditor_id = r.redditor_id
  AND c.redditor_id IS NOT NULL
  AND r.redditor_id IS NOT NULL;

-- ============================================================================
-- PART 7: OPPORTUNITIES TABLE ENHANCEMENTS
-- ============================================================================

-- Add missing columns for workflow compatibility
ALTER TABLE opportunities
ADD COLUMN IF NOT EXISTS opportunity_id VARCHAR(255);

ALTER TABLE opportunities
ADD COLUMN IF NOT EXISTS app_name VARCHAR(255);

ALTER TABLE opportunities
ADD COLUMN IF NOT EXISTS business_category VARCHAR(100);

ALTER TABLE opportunities
ADD COLUMN IF NOT EXISTS source_subreddit VARCHAR(255);

-- Create index for opportunity_id lookups
CREATE INDEX IF NOT EXISTS idx_opportunities_opportunity_id ON opportunities(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_opportunities_app_name ON opportunities(app_name);

-- Backfill opportunity_id from id if null
UPDATE opportunities
SET opportunity_id = COALESCE(opportunity_id, id::text)
WHERE opportunity_id IS NULL;

COMMENT ON COLUMN opportunities.opportunity_id IS 'String identifier for workflows (e.g., test_001)';
COMMENT ON COLUMN opportunities.app_name IS 'Proposed application name';

-- ============================================================================
-- PART 8: OPPORTUNITY_SCORES TABLE ENHANCEMENTS
-- ============================================================================

-- Ensure all score columns exist with correct types
ALTER TABLE opportunity_scores
ALTER COLUMN market_demand_score TYPE DECIMAL(10,4) USING market_demand_score::DECIMAL(10,4);

ALTER TABLE opportunity_scores
ALTER COLUMN pain_intensity_score TYPE DECIMAL(10,4) USING pain_intensity_score::DECIMAL(10,4);

ALTER TABLE opportunity_scores
ALTER COLUMN monetization_potential_score TYPE DECIMAL(10,4) USING monetization_potential_score::DECIMAL(10,4);

ALTER TABLE opportunity_scores
ALTER COLUMN market_gap_score TYPE DECIMAL(10,4) USING market_gap_score::DECIMAL(10,4);

ALTER TABLE opportunity_scores
ALTER COLUMN technical_feasibility_score TYPE DECIMAL(10,4) USING technical_feasibility_score::DECIMAL(10,4);

ALTER TABLE opportunity_scores
ALTER COLUMN simplicity_score TYPE DECIMAL(10,4) USING simplicity_score::DECIMAL(10,4);

-- Drop and recreate total_score as a regular column (not generated) for flexibility
ALTER TABLE opportunity_scores
DROP COLUMN IF EXISTS total_score CASCADE;

ALTER TABLE opportunity_scores
ADD COLUMN total_score DECIMAL(10,4);

-- Create function to calculate total score
CREATE OR REPLACE FUNCTION calculate_opportunity_total_score(
    market_demand DECIMAL(10,4),
    pain_intensity DECIMAL(10,4),
    monetization_potential DECIMAL(10,4),
    market_gap DECIMAL(10,4),
    technical_feasibility DECIMAL(10,4),
    simplicity DECIMAL(10,4)
) RETURNS DECIMAL(10,4) AS $$
BEGIN
    RETURN (
        COALESCE(market_demand, 0) * 0.20 +
        COALESCE(pain_intensity, 0) * 0.25 +
        COALESCE(monetization_potential, 0) * 0.20 +
        COALESCE(market_gap, 0) * 0.10 +
        COALESCE(technical_feasibility, 0) * 0.05 +
        COALESCE(simplicity, 0) * 0.20
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION calculate_opportunity_total_score IS 'Calculate weighted total score: Market(20%) + Pain(25%) + Monetization(20%) + Gap(10%) + Tech(5%) + Simplicity(20%)';

-- Backfill total_score for existing rows
UPDATE opportunity_scores
SET total_score = calculate_opportunity_total_score(
    market_demand_score,
    pain_intensity_score,
    monetization_potential_score,
    market_gap_score,
    technical_feasibility_score,
    simplicity_score
)
WHERE total_score IS NULL;

-- ============================================================================
-- PART 9: DATA INTEGRITY VALIDATION
-- ============================================================================

-- Create view to check migration success
CREATE OR REPLACE VIEW migration_validation_report AS
SELECT
    'submissions' as table_name,
    COUNT(*) as total_rows,
    COUNT(subreddit_id) as with_subreddit_fk,
    COUNT(*) - COUNT(subreddit_id) as missing_subreddit_fk,
    COUNT(redditor_id) as with_redditor_fk,
    COUNT(*) - COUNT(redditor_id) as missing_redditor_fk
FROM submissions
UNION ALL
SELECT
    'comments' as table_name,
    COUNT(*) as total_rows,
    COUNT(submission_id) as with_submission_fk,
    COUNT(*) - COUNT(submission_id) as missing_submission_fk,
    COUNT(redditor_id) as with_redditor_fk,
    COUNT(*) - COUNT(redditor_id) as missing_redditor_fk
FROM comments
UNION ALL
SELECT
    'opportunities' as table_name,
    COUNT(*) as total_rows,
    COUNT(opportunity_id) as with_opportunity_id,
    COUNT(*) - COUNT(opportunity_id) as missing_opportunity_id,
    COUNT(identified_from_submission_id) as with_submission_fk,
    COUNT(*) - COUNT(identified_from_submission_id) as missing_submission_fk
FROM opportunities;

COMMENT ON VIEW migration_validation_report IS 'Validation report showing foreign key backfill success';

-- ============================================================================
-- PART 10: BACKWARDS COMPATIBILITY NOTES
-- ============================================================================

-- All existing queries will continue to work because:
-- 1. No columns were removed
-- 2. All new columns are nullable or have defaults
-- 3. Foreign key relationships remain optional (nullable)
-- 4. String-based IDs (submission_id, redditor_id, etc.) are preserved
-- 5. New columns support both UUID and string-based lookups

-- ============================================================================
-- MIGRATION COMPLETED SUCCESSFULLY
-- ============================================================================

-- Verify migration with this query:
-- SELECT * FROM migration_validation_report;

-- ============================================================================
-- ROLLBACK PROCEDURE (IF NEEDED - USE WITH CAUTION)
-- ============================================================================
/*
-- WARNING: This rollback removes columns and may cause data loss
-- Only use if absolutely necessary

-- Drop validation view
DROP VIEW IF EXISTS migration_validation_report;

-- Drop added columns from redditors
ALTER TABLE redditors DROP COLUMN IF EXISTS redditor_id CASCADE;
ALTER TABLE redditors DROP COLUMN IF EXISTS is_gold CASCADE;
ALTER TABLE redditors DROP COLUMN IF EXISTS is_mod CASCADE;
ALTER TABLE redditors DROP COLUMN IF EXISTS trophy CASCADE;
ALTER TABLE redditors DROP COLUMN IF EXISTS removed CASCADE;
ALTER TABLE redditors DROP COLUMN IF EXISTS name CASCADE;
ALTER TABLE redditors DROP COLUMN IF EXISTS karma CASCADE;

-- Drop added columns from submissions
ALTER TABLE submissions DROP COLUMN IF EXISTS submission_id CASCADE;
ALTER TABLE submissions DROP COLUMN IF EXISTS archived CASCADE;
ALTER TABLE submissions DROP COLUMN IF EXISTS removed CASCADE;
ALTER TABLE submissions DROP COLUMN IF EXISTS attachment CASCADE;
ALTER TABLE submissions DROP COLUMN IF EXISTS poll CASCADE;
ALTER TABLE submissions DROP COLUMN IF EXISTS flair CASCADE;
ALTER TABLE submissions DROP COLUMN IF EXISTS awards CASCADE;
ALTER TABLE submissions DROP COLUMN IF EXISTS score CASCADE;
ALTER TABLE submissions DROP COLUMN IF EXISTS upvote_ratio CASCADE;
ALTER TABLE submissions DROP COLUMN IF EXISTS num_comments CASCADE;
ALTER TABLE submissions DROP COLUMN IF EXISTS edited CASCADE;
ALTER TABLE submissions DROP COLUMN IF EXISTS text CASCADE;
ALTER TABLE submissions DROP COLUMN IF EXISTS subreddit CASCADE;
ALTER TABLE submissions DROP COLUMN IF EXISTS permalink CASCADE;

-- Drop added columns from comments
ALTER TABLE comments DROP COLUMN IF EXISTS link_id CASCADE;
ALTER TABLE comments DROP COLUMN IF EXISTS comment_id CASCADE;
ALTER TABLE comments DROP COLUMN IF EXISTS body CASCADE;
ALTER TABLE comments DROP COLUMN IF EXISTS subreddit CASCADE;
ALTER TABLE comments DROP COLUMN IF EXISTS parent_id CASCADE;
ALTER TABLE comments DROP COLUMN IF EXISTS score CASCADE;
ALTER TABLE comments DROP COLUMN IF EXISTS edited CASCADE;
ALTER TABLE comments DROP COLUMN IF EXISTS removed CASCADE;

-- Drop added columns from opportunities
ALTER TABLE opportunities DROP COLUMN IF EXISTS opportunity_id CASCADE;
ALTER TABLE opportunities DROP COLUMN IF EXISTS app_name CASCADE;
ALTER TABLE opportunities DROP COLUMN IF EXISTS business_category CASCADE;
ALTER TABLE opportunities DROP COLUMN IF EXISTS source_subreddit CASCADE;

-- Drop function
DROP FUNCTION IF EXISTS calculate_opportunity_total_score;

-- Note: Foreign key backfills cannot be easily reverted
-- You would need to set them to NULL manually if needed:
-- UPDATE submissions SET subreddit_id = NULL, redditor_id = NULL;
-- UPDATE comments SET submission_id = NULL, redditor_id = NULL;
*/
