-- ============================================================================
-- RedditHarbor Baseline Schema
-- Created: 2025-11-17
-- Consolidates: Migrations 1-19 (2025-11-04 to 2025-11-14)
-- Source: Current working schema dump
--
-- EXCLUDED FROM BASELINE (DLT-managed):
--   - _dlt_loads, _dlt_pipeline_state, _dlt_version (created by DLT runtime)
--   - _migrations_log (managed by migration system)
--   - All public_staging schema tables (DLT staging area)
-- ============================================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- PART 1: CORE REDDIT TABLES
-- ============================================================================

-- Subreddits table
CREATE TABLE IF NOT EXISTS subreddits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    title TEXT,
    description TEXT,
    subscribers INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Redditors table
CREATE TABLE IF NOT EXISTS redditors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) NOT NULL UNIQUE,
    karma INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Submissions table
CREATE TABLE IF NOT EXISTS submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reddit_id VARCHAR(20) NOT NULL UNIQUE,
    redditor_id UUID REFERENCES redditors(id),
    subreddit_id UUID REFERENCES subreddits(id),
    title TEXT NOT NULL,
    content TEXT,
    url TEXT,
    score INTEGER DEFAULT 0,
    num_comments INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Comments table
CREATE TABLE IF NOT EXISTS comments (
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    submission_id UUID,
    redditor_id UUID,
    parent_comment_id UUID,
    content TEXT NOT NULL,
    content_raw TEXT,
    upvotes INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    sentiment_score NUMERIC(5,4),
    workaround_mentions TEXT,
    comment_depth INTEGER DEFAULT 0,
    link_id VARCHAR(255),
    comment_id VARCHAR(255),
    body TEXT,
    subreddit VARCHAR(255),
    parent_id VARCHAR(255),
    score JSONB,
    edited BOOLEAN DEFAULT false,
    removed VARCHAR(50),
    CONSTRAINT chk_comments_depth_valid CHECK ((comment_depth >= 0)),
    CONSTRAINT chk_comments_sentiment_range CHECK (((sentiment_score >= '-1.0'::numeric) AND (sentiment_score <= 1.0))),
    CONSTRAINT chk_comments_upvotes_non_negative CHECK ((upvotes >= 0))
);

-- ============================================================================
-- PART 2: OPPORTUNITY ANALYSIS TABLES
-- ============================================================================

-- Opportunities table
CREATE TABLE IF NOT EXISTS opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    problem_statement TEXT,
    target_audience TEXT,
    submission_id UUID REFERENCES submissions(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Opportunity scores table
CREATE TABLE IF NOT EXISTS opportunity_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    market_demand DECIMAL(3,2) DEFAULT 0.00 CHECK (market_demand >= 0 AND market_demand <= 1),
    pain_intensity DECIMAL(3,2) DEFAULT 0.00 CHECK (pain_intensity >= 0 AND pain_intensity <= 1),
    competition_level DECIMAL(3,2) DEFAULT 0.00 CHECK (competition_level >= 0 AND competition_level <= 1),
    technical_feasibility DECIMAL(3,2) DEFAULT 0.00 CHECK (technical_feasibility >= 0 AND technical_feasibility <= 1),
    monetization_potential DECIMAL(3,2) DEFAULT 0.00 CHECK (monetization_potential >= 0 AND monetization_potential <= 1),
    simplicity_score DECIMAL(3,2) DEFAULT 0.00 CHECK (simplicity_score >= 0 AND simplicity_score <= 1),
    total_score DECIMAL(5,2) GENERATED ALWAYS AS (
        (market_demand * 0.25) +
        (pain_intensity * 0.20) +
        ((1 - competition_level) * 0.15) +
        (technical_feasibility * 0.20) +
        (monetization_potential * 0.15) +
        (simplicity_score * 0.05)
    ) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(opportunity_id)
);

-- Score components table
CREATE TABLE IF NOT EXISTS score_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_score_id UUID REFERENCES opportunity_scores(id) ON DELETE CASCADE,
    component_type VARCHAR(50) NOT NULL,
    value DECIMAL(5,2) NOT NULL,
    reasoning TEXT,
    source VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- PART 3: VALIDATION & COMPETITIVE TABLES
-- ============================================================================

-- Market validations table
CREATE TABLE IF NOT EXISTS market_validations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    validation_type VARCHAR(50) NOT NULL,
    evidence JSONB,
    confidence_level DECIMAL(3,2) DEFAULT 0.00 CHECK (confidence_level >= 0 AND confidence_level <= 1),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Competitive landscape table
CREATE TABLE IF NOT EXISTS competitive_landscape (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    competitor_name VARCHAR(255) NOT NULL,
    competitor_features JSONB,
    competitive_analysis TEXT,
    market_share DECIMAL(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feature gaps table
CREATE TABLE IF NOT EXISTS feature_gaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    gap_description TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    market_impact DECIMAL(3,2) DEFAULT 0.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cross platform verification table
CREATE TABLE IF NOT EXISTS cross_platform_verification (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    verification_status VARCHAR(20) DEFAULT 'pending',
    verification_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- PART 4: MONETIZATION & TECHNICAL TABLES
-- ============================================================================

-- Monetization patterns table
CREATE TABLE IF NOT EXISTS monetization_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    pattern_type VARCHAR(50) NOT NULL,
    revenue_model TEXT,
    target_pricing DECIMAL(10,2),
    market_size DECIMAL(12,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User willingness to pay table
CREATE TABLE IF NOT EXISTS user_willingness_to_pay (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    price_point DECIMAL(10,2) NOT NULL,
    willingness_percentage DECIMAL(5,2) DEFAULT 0.00,
    user_segment VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Technical assessments table
CREATE TABLE IF NOT EXISTS technical_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    complexity_level VARCHAR(20) DEFAULT 'medium',
    technical_requirements JSONB,
    development_timeframe VARCHAR(50),
    resource_requirements JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- PART 5: WORKFLOW & ANALYTICS TABLES
-- ============================================================================

-- Workflow results table
CREATE TABLE IF NOT EXISTS workflow_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID REFERENCES opportunities(id),
    workflow_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    results JSONB,
    market_demand_score DECIMAL(3,2) DEFAULT 0.00 CHECK (market_demand_score >= 0 AND market_demand_score <= 1),
    pain_intensity_score DECIMAL(3,2) DEFAULT 0.00 CHECK (pain_intensity_score >= 0 AND pain_intensity_score <= 1),
    competition_level_score DECIMAL(3,2) DEFAULT 0.00 CHECK (competition_level_score >= 0 AND competition_level_score <= 1),
    technical_feasibility_score DECIMAL(3,2) DEFAULT 0.00 CHECK (technical_feasibility_score >= 0 AND technical_feasibility_score <= 1),
    monetization_potential_score DECIMAL(3,2) DEFAULT 0.00 CHECK (monetization_potential_score >= 0 AND monetization_potential_score <= 1),
    opportunity_assessment_score DECIMAL(3,2) DEFAULT 0.00 CHECK (opportunity_assessment_score >= 0 AND opportunity_assessment_score <= 1),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Opportunity analysis table (for detailed problem characteristics)
CREATE TABLE IF NOT EXISTS opportunity_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    problem_category VARCHAR(100),
    problem_frequency VARCHAR(50),
    user_impact_level VARCHAR(20),
    market_size DECIMAL(12,2),
    growth_potential DECIMAL(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- PART 6: INDEXES FOR PERFORMANCE
-- ============================================================================

-- Foreign key indexes
CREATE INDEX IF NOT EXISTS idx_submissions_redditor_id ON submissions(redditor_id);
CREATE INDEX IF NOT EXISTS idx_submissions_subreddit_id ON submissions(subreddit_id);
CREATE INDEX IF NOT EXISTS idx_comments_redditor_id ON comments(redditor_id);
CREATE INDEX IF NOT EXISTS idx_comments_submission_id ON comments(submission_id);
CREATE INDEX IF NOT EXISTS idx_comments_parent_comment_id ON comments(parent_comment_id);

-- Opportunity indexes
CREATE INDEX IF NOT EXISTS idx_opportunities_submission_id ON opportunities(submission_id);
CREATE INDEX IF NOT EXISTS idx_opportunity_scores_opportunity_id ON opportunity_scores(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_opportunity_scores_total_score ON opportunity_scores(total_score);

-- Workflow indexes
CREATE INDEX IF NOT EXISTS idx_workflow_results_opportunity_id ON workflow_results(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_workflow_results_status ON workflow_results(status);
CREATE INDEX IF NOT EXISTS idx_workflow_results_workflow_type ON workflow_results(workflow_type);

-- Opportunity analysis indexes
CREATE INDEX IF NOT EXISTS idx_opportunity_analysis_opportunity_id ON opportunity_analysis(opportunity_id);

-- Timestamp indexes for analytics
CREATE INDEX IF NOT EXISTS idx_opportunities_created_at ON opportunities(created_at);
CREATE INDEX IF NOT EXISTS idx_workflow_results_created_at ON workflow_results(created_at);

-- ============================================================================
-- PART 7: ANALYTICS VIEWS
-- ============================================================================

-- Top opportunities view
CREATE OR REPLACE VIEW top_opportunities AS
SELECT
    o.id,
    o.title,
    o.description,
    os.total_score,
    os.market_demand,
    os.pain_intensity,
    os.competition_level,
    os.technical_feasibility,
    os.monetization_potential,
    os.simplicity_score,
    o.created_at
FROM opportunities o
JOIN opportunity_scores os ON o.id = os.opportunity_id
WHERE os.total_score >= 0.6
ORDER BY os.total_score DESC;

-- Opportunity metrics summary view
CREATE OR REPLACE VIEW opportunity_metrics_summary AS
SELECT
    COUNT(*) as total_opportunities,
    AVG(os.total_score) as avg_total_score,
    AVG(os.market_demand) as avg_market_demand,
    AVG(os.pain_intensity) as avg_pain_intensity,
    AVG(os.competition_level) as avg_competition_level,
    AVG(os.technical_feasibility) as avg_technical_feasibility,
    AVG(os.monetization_potential) as avg_monetization_potential,
    AVG(os.simplicity_score) as avg_simplicity_score,
    COUNT(CASE WHEN os.total_score >= 0.8 THEN 1 END) as high_score_opportunities,
    COUNT(CASE WHEN os.total_score >= 0.6 AND os.total_score < 0.8 THEN 1 END) as medium_score_opportunities,
    COUNT(CASE WHEN os.total_score < 0.6 THEN 1 END) as low_score_opportunities
FROM opportunities o
JOIN opportunity_scores os ON o.id = os.opportunity_id;

-- ============================================================================
-- PART 8: UTILITY FUNCTIONS
-- ============================================================================

-- Function to calculate trending score
CREATE OR REPLACE FUNCTION calculate_trending_score(
    score DECIMAL,
    engagement_rate DECIMAL,
    recency_factor DECIMAL
) RETURNS DECIMAL AS $$
BEGIN
    RETURN (score * 0.6) + (engagement_rate * 0.3) + (recency_factor * 0.1);
END;
$$ LANGUAGE plpgsql;

-- Function to update opportunity metrics
CREATE OR REPLACE FUNCTION update_opportunity_metrics() RETURNS TRIGGER AS $$
BEGIN
    -- Update modified timestamp
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PART 9: TABLE AND COLUMN COMMENTS
-- ============================================================================

-- Table comments
COMMENT ON TABLE subreddits IS 'Reddit communities/subreddits data';
COMMENT ON TABLE redditors IS 'Reddit user profiles';
COMMENT ON TABLE submissions IS 'Reddit posts and submissions';
COMMENT ON TABLE comments IS 'Reddit comments and replies';
COMMENT ON TABLE opportunities IS 'Business opportunities identified from Reddit discussions';
COMMENT ON TABLE opportunity_scores IS 'Scoring metrics for opportunity evaluation';
COMMENT ON TABLE score_components IS 'Individual components contributing to opportunity scores';
COMMENT ON TABLE market_validations IS 'Market validation evidence and analysis';
COMMENT ON TABLE competitive_landscape IS 'Competitive analysis for opportunities';
COMMENT ON TABLE feature_gaps IS 'Identified gaps in current solutions';
COMMENT ON TABLE cross_platform_verification IS 'Cross-platform verification of opportunities';
COMMENT ON TABLE monetization_patterns IS 'Monetization strategies and revenue models';
COMMENT ON TABLE user_willingness_to_pay IS 'User pricing sensitivity analysis';
COMMENT ON TABLE technical_assessments IS 'Technical feasibility and complexity analysis';
COMMENT ON TABLE workflow_results IS 'Results from automated workflow analysis';
COMMENT ON TABLE opportunity_analysis IS 'Detailed analysis of problem characteristics and market potential';

-- ============================================================================
-- PART 10: TRIGGERS FOR AUTOMATIC UPDATES
-- ============================================================================

-- Auto-update triggers for timestamp fields
CREATE TRIGGER update_subreddits_timestamp
    BEFORE UPDATE ON subreddits
    FOR EACH ROW
    EXECUTE FUNCTION update_opportunity_metrics();

CREATE TRIGGER update_redditors_timestamp
    BEFORE UPDATE ON redditors
    FOR EACH ROW
    EXECUTE FUNCTION update_opportunity_metrics();

CREATE TRIGGER update_submissions_timestamp
    BEFORE UPDATE ON submissions
    FOR EACH ROW
    EXECUTE FUNCTION update_opportunity_metrics();

CREATE TRIGGER update_comments_timestamp
    BEFORE UPDATE ON comments
    FOR EACH ROW
    EXECUTE FUNCTION update_opportunity_metrics();

CREATE TRIGGER update_opportunities_timestamp
    BEFORE UPDATE ON opportunities
    FOR EACH ROW
    EXECUTE FUNCTION update_opportunity_metrics();

CREATE TRIGGER update_market_validations_timestamp
    BEFORE UPDATE ON market_validations
    FOR EACH ROW
    EXECUTE FUNCTION update_opportunity_metrics();

CREATE TRIGGER update_competitive_landscape_timestamp
    BEFORE UPDATE ON competitive_landscape
    FOR EACH ROW
    EXECUTE FUNCTION update_opportunity_metrics();

CREATE TRIGGER update_feature_gaps_timestamp
    BEFORE UPDATE ON feature_gaps
    FOR EACH ROW
    EXECUTE FUNCTION update_opportunity_metrics();

CREATE TRIGGER update_cross_platform_verification_timestamp
    BEFORE UPDATE ON cross_platform_verification
    FOR EACH ROW
    EXECUTE FUNCTION update_opportunity_metrics();

CREATE TRIGGER update_monetization_patterns_timestamp
    BEFORE UPDATE ON monetization_patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_opportunity_metrics();

CREATE TRIGGER update_technical_assessments_timestamp
    BEFORE UPDATE ON technical_assessments
    FOR EACH ROW
    EXECUTE FUNCTION update_opportunity_metrics();

CREATE TRIGGER update_workflow_results_timestamp
    BEFORE UPDATE ON workflow_results
    FOR EACH ROW
    EXECUTE FUNCTION update_opportunity_metrics();

CREATE TRIGGER update_opportunity_analysis_timestamp
    BEFORE UPDATE ON opportunity_analysis
    FOR EACH ROW
    EXECUTE FUNCTION update_opportunity_metrics();

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- This baseline migration consolidates 20 previous migrations into a single
-- comprehensive schema definition. It preserves:
-- 1. All table structures and relationships
-- 2. Critical indexes for performance
-- 3. Views for analytics and reporting
-- 4. Functions for business logic
-- 5. Triggers for automatic timestamp updates
-- 6. DLT compatibility (app_opportunities will be created by DLT in public_staging)
--
-- Excluded from baseline (DLT-managed):
-- - _dlt_loads, _dlt_pipeline_state, _dlt_version (created by DLT runtime)
-- - _migrations_log (managed by migration system)
-- - All public_staging schema tables (DLT staging area)
--
-- Key design decisions:
-- - Baseline creates core schema without DLT-managed tables
-- - DLT will create app_opportunities in public_staging schema
-- - Views and indexes optimized for analytics performance
-- - Preserves all business logic and constraints
-- - Maintains backward compatibility with existing code