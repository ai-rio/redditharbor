-- Migration 2: Opportunity Management
-- Created: 2025-11-04 19:00:01
-- Description: Creates opportunity management tables for monetizable app research
-- Tables: opportunities, opportunity_scores, score_components

-- ============================================================================
-- Opportunities Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    problem_statement TEXT NOT NULL,
    identified_from_submission_id UUID REFERENCES submissions(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'identified',
    core_function_count INTEGER DEFAULT 0,
    simplicity_constraint_met BOOLEAN DEFAULT false,
    proposed_solution TEXT,
    target_audience TEXT,
    market_segment VARCHAR(100),
    last_reviewed_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT chk_opportunities_function_count CHECK (core_function_count >= 0),
    CONSTRAINT chk_opportunities_valid_function_count CHECK (
        (core_function_count <= 3) OR (core_function_count IS NULL)
    )
);

COMMENT ON TABLE opportunities IS 'Identified monetizable app development opportunities from Reddit';
COMMENT ON COLUMN opportunities.core_function_count IS 'Number of core functions (MAXIMUM 3 - 4+ auto disqualifies)';
COMMENT ON COLUMN opportunities.simplicity_constraint_met IS 'True only if 1-3 core functions (4+ = automatic disqualification)';

-- ============================================================================
-- Opportunity Scores Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS opportunity_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    market_demand_score INTEGER CHECK (market_demand_score >= 0 AND market_demand_score <= 100),
    pain_intensity_score INTEGER CHECK (pain_intensity_score >= 0 AND pain_intensity_score <= 100),
    monetization_potential_score INTEGER CHECK (monetization_potential_score >= 0 AND monetization_potential_score <= 100),
    market_gap_score INTEGER CHECK (market_gap_score >= 0 AND market_gap_score <= 100),
    technical_feasibility_score INTEGER CHECK (technical_feasibility_score >= 0 AND technical_feasibility_score <= 100),
    simplicity_score INTEGER CHECK (simplicity_score >= 0 AND simplicity_score <= 100),
    total_score DECIMAL(5,2) GENERATED ALWAYS AS (
        (market_demand_score * 0.20) +
        (pain_intensity_score * 0.25) +
        (monetization_potential_score * 0.20) +
        (market_gap_score * 0.10) +
        (technical_feasibility_score * 0.05) +
        (simplicity_score * 0.20)
    ) STORED,
    score_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    score_version VARCHAR(20) DEFAULT '1.0',
    scoring_notes TEXT
);

COMMENT ON TABLE opportunity_scores IS 'Multi-dimensional scoring for each opportunity';
COMMENT ON COLUMN opportunity_scores.total_score IS 'Weighted total: Market(20%) + Pain(25%) + Monetization(20%) + Gap(10%) + Tech(5%) + Simplicity(20%)';
COMMENT ON COLUMN opportunity_scores.simplicity_score IS '1 function=100, 2=85, 3=70, 4+=0 (automatic disqualification)';

-- ============================================================================
-- Score Components Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS score_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    evidence_text TEXT,
    confidence_level DECIMAL(5,4) CHECK (confidence_level >= 0.0 AND confidence_level <= 1.0),
    source_submission_ids TEXT,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_score_components_confidence CHECK (
        confidence_level >= 0.0 AND confidence_level <= 1.0
    )
);

COMMENT ON TABLE score_components IS 'Detailed breakdown of each scoring metric with evidence';
COMMENT ON COLUMN score_components.metric_name IS 'e.g., discussion_volume, emotional_language, willingness_to_pay';
COMMENT ON COLUMN score_components.evidence_text IS 'Text snippets or data points supporting the score';
COMMENT ON COLUMN score_components.source_submission_ids IS 'Comma-separated list of submission IDs used as evidence';

-- ============================================================================
-- Indexes for Opportunity Management
-- ============================================================================

-- Opportunities indexes
CREATE INDEX IF NOT EXISTS idx_opportunities_status ON opportunities(status);
CREATE INDEX IF NOT EXISTS idx_opportunities_market_segment ON opportunities(market_segment);
CREATE INDEX IF NOT EXISTS idx_opportunities_created_at ON opportunities(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_simplicity ON opportunities(simplicity_constraint_met);
CREATE INDEX IF NOT EXISTS idx_opportunities_function_count ON opportunities(core_function_count);
CREATE INDEX IF NOT EXISTS idx_opportunities_submission ON opportunities(identified_from_submission_id);

-- Opportunity Scores indexes
CREATE INDEX IF NOT EXISTS idx_opportunity_scores_opportunity ON opportunity_scores(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_opportunity_scores_total ON opportunity_scores(total_score DESC);
CREATE INDEX IF NOT EXISTS idx_opportunity_scores_date ON opportunity_scores(score_date DESC);

-- Score Components indexes
CREATE INDEX IF NOT EXISTS idx_score_components_opportunity ON score_components(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_score_components_metric ON score_components(metric_name);
CREATE INDEX IF NOT EXISTS idx_score_components_confidence ON score_components(confidence_level DESC);
CREATE INDEX IF NOT EXISTS idx_score_components_evidence_gin ON score_components USING gin(to_tsvector('english', evidence_text));

-- Migration completed
