-- Migration 1: Core Reddit Data Tables
-- Created: 2025-11-04 19:00:00
-- Description: Creates core Reddit data collection tables and extends existing tables
-- Tables: subreddits (new), redditors (extend), submissions (extend), comments (extend)

-- ============================================================================
-- Subreddits Table (NEW)
-- ============================================================================
-- Purpose: Target communities for data collection
CREATE TABLE IF NOT EXISTS subreddits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    subscriber_count INTEGER DEFAULT 0,
    category VARCHAR(100),
    target_market_segment VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_scraped_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,

    CONSTRAINT idx_subreddits_name UNIQUE (name)
);

COMMENT ON TABLE subreddits IS 'Target subreddits for monetizable app research';
COMMENT ON COLUMN subreddits.target_market_segment IS 'e.g., Health & Fitness, Finance & Investing, Education & Career';
COMMENT ON COLUMN subreddits.is_active IS 'Whether subreddit is currently being monitored';

-- ============================================================================
-- Extend Redditors Table (EXISTING TABLE - ADD COLUMNS)
-- ============================================================================
-- Check if columns exist before adding
DO $$
BEGIN
    -- Add anonymized_id column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'redditors' AND column_name = 'anonymized_id') THEN
        ALTER TABLE redditors ADD COLUMN anonymized_id TEXT;
    END IF;

    -- Add flair_type column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'redditors' AND column_name = 'flair_type') THEN
        ALTER TABLE redditors ADD COLUMN flair_type VARCHAR(100);
    END IF;
END $$;

COMMENT ON COLUMN redditors.is_anonymous IS 'Whether user data has been anonymized per PII requirements';
COMMENT ON COLUMN redditors.anonymized_id IS 'Hashed/anonymized user identifier for privacy compliance';

-- ============================================================================
-- Extend Submissions Table (EXISTING TABLE - ADD COLUMNS)
-- ============================================================================
DO $$
BEGIN
    -- Add post_type column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'submissions' AND column_name = 'post_type') THEN
        ALTER TABLE submissions ADD COLUMN post_type VARCHAR(50) DEFAULT 'text';
    END IF;

    -- Add problem_keywords column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'submissions' AND column_name = 'problem_keywords') THEN
        ALTER TABLE submissions ADD COLUMN problem_keywords TEXT;
    END IF;

    -- Add solution_mentions column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'submissions' AND column_name = 'solution_mentions') THEN
        ALTER TABLE submissions ADD COLUMN solution_mentions TEXT;
    END IF;

    -- Add awards_count column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'submissions' AND column_name = 'awards_count') THEN
        ALTER TABLE submissions ADD COLUMN awards_count INTEGER DEFAULT 0;
    END IF;

    -- Add is_spoiler column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'submissions' AND column_name = 'is_spoiler') THEN
        ALTER TABLE submissions ADD COLUMN is_spoiler BOOLEAN DEFAULT false;
    END IF;
END $$;

COMMENT ON COLUMN submissions.problem_keywords IS 'JSON or comma-separated keywords identifying pain points';
COMMENT ON COLUMN submissions.solution_mentions IS 'Current tools or workarounds mentioned by users';

-- ============================================================================
-- Extend Comments Table (EXISTING TABLE - ADD COLUMNS)
-- ============================================================================
DO $$
BEGIN
    -- Add workaround_mentions column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'comments' AND column_name = 'workaround_mentions') THEN
        ALTER TABLE comments ADD COLUMN workaround_mentions TEXT;
    END IF;

    -- Add comment_depth column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'comments' AND column_name = 'comment_depth') THEN
        ALTER TABLE comments ADD COLUMN comment_depth INTEGER DEFAULT 0;
    END IF;
END $$;

COMMENT ON COLUMN comments.workaround_mentions IS 'DIY solutions or workarounds mentioned by users';
COMMENT ON COLUMN comments.comment_depth IS 'Depth in reply tree (0 for top-level comments)';

-- ============================================================================
-- Basic Indexes for Core Tables (Performance Critical)
-- ============================================================================

-- Subreddits indexes
CREATE INDEX IF NOT EXISTS idx_subreddits_active ON subreddits(is_active);
CREATE INDEX IF NOT EXISTS idx_subreddits_subscriber_count ON subreddits(subscriber_count DESC);
CREATE INDEX IF NOT EXISTS idx_subreddits_category ON subreddits(category);
CREATE INDEX IF NOT EXISTS idx_subreddits_market_segment ON subreddits(target_market_segment);

-- Redditors indexes
CREATE INDEX IF NOT EXISTS idx_redditors_anonymous ON redditors(is_anonymous);
CREATE INDEX IF NOT EXISTS idx_redditors_flair ON redditors(flair_type);

-- Submissions indexes (already exist in most cases, but adding these specific ones)
CREATE INDEX IF NOT EXISTS idx_submissions_post_type ON submissions(post_type);
CREATE INDEX IF NOT EXISTS idx_submissions_awards ON submissions(awards_count DESC);
CREATE INDEX IF NOT EXISTS idx_submissions_spoiler ON submissions(is_spoiler);

-- Comments indexes
CREATE INDEX IF NOT EXISTS idx_comments_workarounds_gin ON comments USING gin(to_tsvector('english', workaround_mentions));

-- Migration completed successfully
INSERT INTO _migrations_log (migration_name, applied_at) VALUES ('20251104190000_core_reddit_data_tables', NOW()) ON CONFLICT DO NOTHING;
