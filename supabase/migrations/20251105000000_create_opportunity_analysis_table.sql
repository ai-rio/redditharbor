-- Migration: Opportunity Analysis Table
-- Created: 2025-11-05 00:00:00
-- Description: Creates opportunity_analysis table for storing 6-dimensional opportunity scores
-- Purpose: Store scoring results for Reddit submissions across 6 key dimensions with final weighted scores
-- Expected records: ~6,127 submissions from research collection

-- ============================================================================
-- Opportunity Analysis Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS opportunity_analysis (
    id BIGSERIAL PRIMARY KEY,
    submission_id TEXT NOT NULL,
    opportunity_id TEXT UNIQUE NOT NULL,
    title TEXT,
    subreddit TEXT,
    sector TEXT,

    -- 6 Scoring Dimensions (0-100 scale)
    market_demand NUMERIC(5,2) CHECK (market_demand >= 0 AND market_demand <= 100),
    pain_intensity NUMERIC(5,2) CHECK (pain_intensity >= 0 AND pain_intensity <= 100),
    monetization_potential NUMERIC(5,2) CHECK (monetization_potential >= 0 AND monetization_potential <= 100),
    market_gap NUMERIC(5,2) CHECK (market_gap >= 0 AND market_gap <= 100),
    technical_feasibility NUMERIC(5,2) CHECK (technical_feasibility >= 0 AND technical_feasibility <= 100),
    simplicity_score NUMERIC(5,2) CHECK (simplicity_score >= 0 AND simplicity_score <= 100),

    -- Final Weighted Score
    final_score NUMERIC(5,2) CHECK (final_score >= 0 AND final_score <= 100),

    -- Priority Classification
    priority TEXT CHECK (priority IN (
        '🔥 High Priority',
        '⚡ Med-High Priority',
        '📊 Medium Priority',
        '📋 Low Priority',
        '❌ Not Recommended'
    )),

    scored_at TIMESTAMPTZ DEFAULT NOW(),

    -- Foreign Key Constraint
    CONSTRAINT fk_opportunity_analysis_submission
        FOREIGN KEY (submission_id)
        REFERENCES submissions(id)
        ON DELETE CASCADE
);

-- ============================================================================
-- Table Comments
-- ============================================================================
COMMENT ON TABLE opportunity_analysis IS 'Opportunity scoring results for Reddit submissions across 6 dimensions';
COMMENT ON COLUMN opportunity_analysis.submission_id IS 'Reference to submissions.id (TEXT)';
COMMENT ON COLUMN opportunity_analysis.opportunity_id IS 'Unique opportunity identifier in format: opp_[submission_id]';
COMMENT ON COLUMN opportunity_analysis.sector IS 'Market sector: Health & Fitness, Finance & Investing, Education & Career, Travel & Experiences, Real Estate, Technology & SaaS';
COMMENT ON COLUMN opportunity_analysis.market_demand IS 'Score 0-100: Community engagement, discussion volume, search trends';
COMMENT ON COLUMN opportunity_analysis.pain_intensity IS 'Score 0-100: Emotional language, urgency, desperation levels';
COMMENT ON COLUMN opportunity_analysis.monetization_potential IS 'Score 0-100: Willingness to pay, budget mentions, subscription readiness';
COMMENT ON COLUMN opportunity_analysis.market_gap IS 'Score 0-100: Unmet needs, competitor weaknesses, missing features';
COMMENT ON COLUMN opportunity_analysis.technical_feasibility IS 'Score 0-100: Implementation complexity, API availability, development time';
COMMENT ON COLUMN opportunity_analysis.simplicity_score IS 'Score 0-100: Core function count (1-3 functions max), feature creep risk';
COMMENT ON COLUMN opportunity_analysis.final_score IS 'Weighted average: Market(20%) + Pain(25%) + Monetization(20%) + Gap(10%) + Tech(5%) + Simplicity(20%)';
COMMENT ON COLUMN opportunity_analysis.priority IS 'Priority classification based on final_score: 80+=High, 65-79=Med-High, 50-64=Medium, 30-49=Low, <30=Not Recommended';

-- ============================================================================
-- Performance Indexes
-- ============================================================================

-- Primary lookup indexes
CREATE INDEX idx_opportunity_analysis_submission ON opportunity_analysis(submission_id);
CREATE INDEX idx_opportunity_analysis_opportunity_id ON opportunity_analysis(opportunity_id);

-- Filtering and sorting indexes
CREATE INDEX idx_opportunity_analysis_sector ON opportunity_analysis(sector);
CREATE INDEX idx_opportunity_analysis_final_score ON opportunity_analysis(final_score DESC);
CREATE INDEX idx_opportunity_analysis_priority ON opportunity_analysis(priority);
CREATE INDEX idx_opportunity_analysis_scored_at ON opportunity_analysis(scored_at DESC);

-- Composite index for sector-based queries
CREATE INDEX idx_opportunity_analysis_sector_score ON opportunity_analysis(sector, final_score DESC);

-- Individual dimension scores (for filtering by specific criteria)
CREATE INDEX idx_opportunity_analysis_market_demand ON opportunity_analysis(market_demand DESC);
CREATE INDEX idx_opportunity_analysis_pain_intensity ON opportunity_analysis(pain_intensity DESC);
CREATE INDEX idx_opportunity_analysis_monetization ON opportunity_analysis(monetization_potential DESC);
CREATE INDEX idx_opportunity_analysis_simplicity ON opportunity_analysis(simplicity_score DESC);

-- Subreddit-based analysis
CREATE INDEX idx_opportunity_analysis_subreddit ON opportunity_analysis(subreddit);
CREATE INDEX idx_opportunity_analysis_subreddit_score ON opportunity_analysis(subreddit, final_score DESC);

-- ============================================================================
-- Data Quality Triggers (Optional - for future enhancements)
-- ============================================================================

-- Function to validate scoring logic
CREATE OR REPLACE FUNCTION validate_opportunity_score()
RETURNS TRIGGER AS $$
BEGIN
    -- Ensure opportunity_id follows format: opp_[submission_id]
    IF NEW.opportunity_id NOT LIKE 'opp_%' THEN
        RAISE EXCEPTION 'opportunity_id must start with opp_ prefix';
    END IF;

    -- Validate that all dimension scores exist if final_score exists
    IF NEW.final_score IS NOT NULL THEN
        IF NEW.market_demand IS NULL OR
           NEW.pain_intensity IS NULL OR
           NEW.monetization_potential IS NULL OR
           NEW.market_gap IS NULL OR
           NEW.technical_feasibility IS NULL OR
           NEW.simplicity_score IS NULL THEN
            RAISE EXCEPTION 'All dimension scores must be present when final_score is set';
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to table
CREATE TRIGGER trigger_validate_opportunity_score
    BEFORE INSERT OR UPDATE ON opportunity_analysis
    FOR EACH ROW
    EXECUTE FUNCTION validate_opportunity_score();

-- ============================================================================
-- Sample Query Examples (for documentation)
-- ============================================================================

-- Example 1: Get top 10 high-priority opportunities
-- SELECT * FROM opportunity_analysis
-- WHERE priority = '🔥 High Priority'
-- ORDER BY final_score DESC LIMIT 10;

-- Example 2: Get opportunities by sector
-- SELECT sector, COUNT(*), AVG(final_score) as avg_score
-- FROM opportunity_analysis
-- GROUP BY sector
-- ORDER BY avg_score DESC;

-- Example 3: Find opportunities with high monetization but low technical feasibility
-- SELECT title, subreddit, monetization_potential, technical_feasibility, final_score
-- FROM opportunity_analysis
-- WHERE monetization_potential > 80 AND technical_feasibility < 50
-- ORDER BY final_score DESC;

-- Migration completed successfully
