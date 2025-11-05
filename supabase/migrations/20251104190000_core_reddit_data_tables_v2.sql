-- Migration 1: Core Reddit Data Tables (REVISED)
-- Created: 2025-11-04 19:00:00 (Revised)
-- Description: Creates NEW Reddit data collection tables following ERD schema
-- Note: Existing tables (redditor, submission, comment) kept as-is
-- Tables: subreddits (NEW), redditors_new (NEW), submissions_new (NEW), comments_new (NEW)

-- ============================================================================
-- Subreddits Table (NEW - follows ERD)
-- ============================================================================
CREATE TABLE IF NOT EXISTS subreddits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    subscriber_count INTEGER DEFAULT 0,
    category VARCHAR(100),
    target_market_segment VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_scraped_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_subreddits_name ON subreddits(name);
CREATE INDEX IF NOT EXISTS idx_subreddits_active ON subreddits(is_active);
CREATE INDEX IF NOT EXISTS idx_subreddits_subscriber_count ON subreddits(subscriber_count DESC);
CREATE INDEX IF NOT EXISTS idx_subreddits_category ON subreddits(category);
CREATE INDEX IF NOT EXISTS idx_subreddits_market_segment ON subreddits(target_market_segment);

COMMENT ON TABLE subreddits IS 'Target subreddits for monetizable app research';
COMMENT ON COLUMN subreddits.target_market_segment IS 'e.g., Health & Fitness, Finance & Investing, Education & Career';
COMMENT ON COLUMN subreddits.is_active IS 'Whether subreddit is currently being monitored';

-- ============================================================================
-- Redditors Table (NEW - follows ERD)
-- ============================================================================
CREATE TABLE IF NOT EXISTS redditors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    karma_score INTEGER DEFAULT 0,
    account_age_days INTEGER DEFAULT 0,
    flair_type VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_anonymous BOOLEAN DEFAULT false,
    anonymized_id TEXT,

    CONSTRAINT chk_redditors_karma_non_negative CHECK (karma_score >= 0),
    CONSTRAINT chk_redditors_age_non_negative CHECK (account_age_days >= 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_redditors_username ON redditors(username);
CREATE INDEX IF NOT EXISTS idx_redditors_karma ON redditors(karma_score DESC);
CREATE INDEX IF NOT EXISTS idx_redditors_account_age ON redditors(account_age_days DESC);
CREATE INDEX IF NOT EXISTS idx_redditors_anonymous ON redditors(is_anonymous);
CREATE INDEX IF NOT EXISTS idx_redditors_flair ON redditors(flair_type);

COMMENT ON TABLE redditors IS 'Anonymized Reddit user profiles and metadata';
COMMENT ON COLUMN redditors.is_anonymous IS 'Whether user data has been anonymized per PII requirements';
COMMENT ON COLUMN redditors.anonymized_id IS 'Hashed/anonymized user identifier for privacy compliance';

-- ============================================================================
-- Submissions Table (NEW - follows ERD)
-- ============================================================================
CREATE TABLE IF NOT EXISTS submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subreddit_id UUID REFERENCES subreddits(id) ON DELETE CASCADE,
    redditor_id UUID REFERENCES redditors(id) ON DELETE CASCADE,
    title VARCHAR(300) NOT NULL,
    content TEXT,
    content_raw TEXT,
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    awards_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    post_type VARCHAR(50) DEFAULT 'text',
    sentiment_score DECIMAL(5,4),
    problem_keywords TEXT,
    solution_mentions TEXT,
    url TEXT,
    is_nsfw BOOLEAN DEFAULT false,
    is_spoiler BOOLEAN DEFAULT false,

    CONSTRAINT chk_submissions_upvotes_non_negative CHECK (upvotes >= 0),
    CONSTRAINT chk_submissions_downvotes_non_negative CHECK (downvotes >= 0),
    CONSTRAINT chk_submissions_comments_non_negative CHECK (comments_count >= 0),
    CONSTRAINT chk_submissions_sentiment_range CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0)
);

CREATE INDEX IF NOT EXISTS idx_submissions_subreddit ON submissions(subreddit_id);
CREATE INDEX IF NOT EXISTS idx_submissions_redditor ON submissions(redditor_id);
CREATE INDEX IF NOT EXISTS idx_submissions_created_at ON submissions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_submissions_upvotes ON submissions(upvotes DESC);
CREATE INDEX IF NOT EXISTS idx_submissions_sentiment ON submissions(sentiment_score);
CREATE INDEX IF NOT EXISTS idx_submissions_post_type ON submissions(post_type);
CREATE INDEX IF NOT EXISTS idx_submissions_awards ON submissions(awards_count DESC);
CREATE INDEX IF NOT EXISTS idx_submissions_spoiler ON submissions(is_spoiler);
CREATE INDEX IF NOT EXISTS idx_submissions_keywords ON submissions USING gin(to_tsvector('english', problem_keywords));
CREATE INDEX IF NOT EXISTS idx_submissions_solution_gin ON submissions USING gin(to_tsvector('english', solution_mentions));

COMMENT ON TABLE submissions IS 'Reddit posts and submissions analyzed for opportunities';
COMMENT ON COLUMN submissions.problem_keywords IS 'JSON or comma-separated keywords identifying pain points';
COMMENT ON COLUMN submissions.solution_mentions IS 'Current tools or workarounds mentioned by users';

-- ============================================================================
-- Comments Table (NEW - follows ERD)
-- ============================================================================
CREATE TABLE IF NOT EXISTS comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID REFERENCES submissions(id) ON DELETE CASCADE,
    redditor_id UUID REFERENCES redditors(id) ON DELETE CASCADE,
    parent_comment_id UUID REFERENCES comments(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    content_raw TEXT,
    upvotes INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sentiment_score DECIMAL(5,4),
    workaround_mentions TEXT,
    comment_depth INTEGER DEFAULT 0,

    CONSTRAINT chk_comments_upvotes_non_negative CHECK (upvotes >= 0),
    CONSTRAINT chk_comments_depth_valid CHECK (comment_depth >= 0),
    CONSTRAINT chk_comments_sentiment_range CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0)
);

CREATE INDEX IF NOT EXISTS idx_comments_submission ON comments(submission_id);
CREATE INDEX IF NOT EXISTS idx_comments_redditor ON comments(redditor_id);
CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(parent_comment_id);
CREATE INDEX IF NOT EXISTS idx_comments_created_at ON comments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_comments_depth ON comments(comment_depth);
CREATE INDEX IF NOT EXISTS idx_comments_workarounds ON comments USING gin(to_tsvector('english', workaround_mentions));

COMMENT ON TABLE comments IS 'Reddit comments including replies and discussion threads';
COMMENT ON COLUMN comments.parent_comment_id IS 'Self-reference for building comment hierarchy';
COMMENT ON COLUMN comments.comment_depth IS 'Depth in reply tree (0 for top-level comments)';
COMMENT ON COLUMN comments.workaround_mentions IS 'DIY solutions or workarounds mentioned by users';
