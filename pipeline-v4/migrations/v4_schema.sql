-- Pipeline V4 Database Schema
-- Simplified opportunities table without Agno fields
-- Migration script for PostgreSQL

-- Drop existing table if it exists (for clean migration)
DROP TABLE IF EXISTS opportunities CASCADE;

-- Create the simplified opportunities table
CREATE TABLE opportunities (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Reddit identifiers
    submission_id TEXT UNIQUE NOT NULL,
    subreddit TEXT NOT NULL,
    title TEXT NOT NULL,

    -- Core scores (0-100)
    wtp_score DECIMAL(5,2) NOT NULL,
    final_score DECIMAL(5,2) NOT NULL,
    confidence_score DECIMAL(5,2) NOT NULL,

    -- Analysis data (JSONB for flexibility)
    core_functions JSONB DEFAULT '[]'::jsonb,
    pricing_strategy JSONB DEFAULT '{}'::jsonb,
    pain_points JSONB DEFAULT '[]'::jsonb,

    -- Metadata
    target_segment TEXT,
    trust_level TEXT DEFAULT 'MEDIUM',

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes for common queries
    CONSTRAINT valid_scores CHECK (
        wtp_score >= 0 AND wtp_score <= 100 AND
        final_score >= 0 AND final_score <= 100 AND
        confidence_score >= 0 AND confidence_score <= 100
    ),
    CONSTRAINT valid_trust_level CHECK (
        trust_level IN ('LOW', 'MEDIUM', 'HIGH')
    )
);

-- Create GIN indexes for JSONB columns for efficient querying
CREATE INDEX idx_opportunities_core_functions_gin
    ON opportunities USING GIN (core_functions);

CREATE INDEX idx_opportunities_pricing_strategy_gin
    ON opportunities USING GIN (pricing_strategy);

CREATE INDEX idx_opportunities_pain_points_gin
    ON opportunities USING GIN (pain_points);

-- Indexes for performance
CREATE INDEX idx_opportunities_subreddit
    ON opportunities(subreddit);

CREATE INDEX idx_opportunities_final_score
    ON opportunities(final_score DESC);

CREATE INDEX idx_opportunities_wtp_score
    ON opportunities(wtp_score DESC);

CREATE INDEX idx_opportunities_created_at
    ON opportunities(created_at DESC);

-- Composite index for common query patterns
CREATE INDEX idx_opportunities_subreddit_score
    ON opportunities(subreddit, final_score DESC);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at on row updates
CREATE TRIGGER update_opportunities_updated_at
    BEFORE UPDATE ON opportunities
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create a unique index on submission_id for ON CONFLICT support
-- This supports upsert operations in postgres_loader.py
CREATE UNIQUE INDEX IF NOT EXISTS idx_opportunities_submission_id
    ON opportunities(submission_id);

-- Add comments for documentation
COMMENT ON TABLE opportunities IS 'Pipeline V4: Simplified opportunity analysis results without Agno integration';
COMMENT ON COLUMN opportunities.submission_id IS 'Reddit submission identifier (UUID or URL)';
COMMENT ON COLUMN opportunities.wtp_score IS 'Willingness-to-pay score (0-100)';
COMMENT ON COLUMN opportunities.final_score IS 'Final opportunity score (0-100)';
COMMENT ON COLUMN opportunities.confidence_score IS 'Analysis confidence score (0-100)';
COMMENT ON COLUMN opportunities.core_functions IS 'JSON array of identified core functions';
COMMENT ON COLUMN opportunities.pricing_strategy IS 'JSON object describing pricing strategy';
COMMENT ON COLUMN opportunities.pain_points IS 'JSON array of identified pain points';
COMMENT ON COLUMN opportunities.trust_level IS 'Trust level: LOW, MEDIUM, or HIGH';

-- Create a view for high-scoring opportunities
CREATE OR REPLACE VIEW high_value_opportunities AS
SELECT
    id,
    submission_id,
    subreddit,
    title,
    wtp_score,
    final_score,
    confidence_score,
    target_segment,
    trust_level,
    created_at
FROM opportunities
WHERE final_score >= 75
ORDER BY final_score DESC;

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL ON opportunities TO reddit_app;
-- GRANT SELECT ON opportunities TO reddit_readonly;
-- GRANT ALL ON high_value_opportunities TO reddit_app;
-- GRANT SELECT ON high_value_opportunities TO reddit_readonly;
