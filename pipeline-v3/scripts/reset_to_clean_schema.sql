-- RedditHarbor Pipeline-v3 Clean Schema Reset
-- Drops all legacy tables and creates ONE clean schema
-- WARNING: This destroys all existing data

-- Drop legacy tables
DROP TABLE IF EXISTS app_opportunities CASCADE;
DROP TABLE IF EXISTS opportunities CASCADE;

-- Create clean opportunities table from pipeline-v3 models
CREATE TABLE opportunities (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source Reddit data
    submission_id VARCHAR(10) NOT NULL UNIQUE,
    reddit_title VARCHAR(300) NOT NULL,
    reddit_url VARCHAR(500) NOT NULL,
    subreddit VARCHAR(100) NOT NULL,
    reddit_author VARCHAR(100),
    reddit_upvotes INTEGER NOT NULL DEFAULT 0,
    reddit_comments_count INTEGER NOT NULL DEFAULT 0,
    reddit_created_at TIMESTAMP NOT NULL,

    -- App idea analysis (8 MANDATORY FIELDS mapped correctly)
    app_title VARCHAR(200) NOT NULL,              -- Maps to app_name
    app_concept TEXT NOT NULL,                     -- Maps to app_concept
    problem_statement TEXT NOT NULL,               -- Maps to problem_description
    target_audience TEXT NOT NULL,                 -- Maps to target_user
    core_functions JSONB NOT NULL,                 -- Maps to core_functions (as JSON!)

    -- Market metrics
    market_demand FLOAT NOT NULL,
    pain_intensity FLOAT NOT NULL,
    monetization_potential FLOAT NOT NULL,         -- Maps to monetization_model score
    competition_level FLOAT NOT NULL,
    technical_feasibility FLOAT NOT NULL,

    -- Overall scoring
    final_score FLOAT NOT NULL,                    -- Maps to opportunity_score
    confidence_score FLOAT NOT NULL,
    trust_level VARCHAR(10) NOT NULL CHECK (trust_level IN ('LOW', 'MEDIUM', 'HIGH')),

    -- AI Quality Assessment
    content_quality_score FLOAT NOT NULL DEFAULT 50.0,
    is_spam BOOLEAN NOT NULL DEFAULT FALSE,
    spam_indicators JSONB,

    -- Semantic search
    embedding JSONB,

    -- Metadata
    analyzed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Status flags
    is_duplicate BOOLEAN NOT NULL DEFAULT FALSE,
    duplicate_of_id UUID REFERENCES opportunities(id)
);

-- Create indexes for performance
CREATE INDEX idx_opportunities_submission_id ON opportunities(submission_id);
CREATE INDEX idx_opportunities_subreddit ON opportunities(subreddit);
CREATE INDEX idx_opportunities_final_score ON opportunities(final_score);
CREATE INDEX idx_opportunities_trust_level ON opportunities(trust_level);
CREATE INDEX idx_opportunities_final_score_trust ON opportunities(final_score, trust_level);
CREATE INDEX idx_opportunities_subreddit_created ON opportunities(subreddit, reddit_created_at);
CREATE INDEX idx_opportunities_analyzed_created ON opportunities(analyzed_at, created_at);
CREATE INDEX idx_opportunities_is_spam ON opportunities(is_spam);
CREATE INDEX idx_opportunities_quality_score ON opportunities(content_quality_score);
CREATE INDEX idx_opportunities_quality_spam ON opportunities(content_quality_score, is_spam);

-- GIN index for JSONB columns
CREATE INDEX idx_opportunities_core_functions ON opportunities USING GIN (core_functions);
CREATE INDEX idx_opportunities_spam_indicators ON opportunities USING GIN (spam_indicators);

-- Verify the schema
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'opportunities'
ORDER BY ordinal_position;

-- Show count (should be 0)
SELECT COUNT(*) as total_opportunities FROM opportunities;
