-- Migration 5: Monetization & Technical Assessment
-- Created: 2025-11-04 19:00:04
-- Description: Creates monetization and technical feasibility tables
-- Tables: monetization_patterns, user_willingness_to_pay, technical_assessments

-- ============================================================================
-- Monetization Patterns Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS monetization_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    model_type VARCHAR(100) NOT NULL,
    price_range_min DECIMAL(10,2),
    price_range_max DECIMAL(10,2),
    revenue_estimate DECIMAL(12,2),
    validation_status VARCHAR(50) DEFAULT 'preliminary',
    market_segment VARCHAR(100),
    pricing_evidence TEXT,
    potential_users INTEGER,
    identified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_monetization_price_min CHECK (
        price_range_min IS NULL OR price_range_min >= 0
    ),
    CONSTRAINT chk_monetization_price_max CHECK (
        price_range_max IS NULL OR price_range_max >= 0
    ),
    CONSTRAINT chk_monetization_revenue CHECK (
        revenue_estimate IS NULL OR revenue_estimate >= 0
    ),
    CONSTRAINT chk_monetization_users CHECK (
        potential_users IS NULL OR potential_users >= 0
    ),
    CONSTRAINT chk_monetization_price_range CHECK (
        price_range_max IS NULL OR price_range_min IS NULL OR
        price_range_max >= price_range_min
    )
);

COMMENT ON TABLE monetization_patterns IS 'Identified monetization models and revenue estimates';
COMMENT ON COLUMN monetization_patterns.model_type IS 'e.g., subscription, one-time, freemium, marketplace, affiliate';

-- ============================================================================
-- User Willingness to Pay Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_willingness_to_pay (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    payment_mention_text TEXT NOT NULL,
    price_point DECIMAL(10,2),
    user_context TEXT,
    user_segment VARCHAR(100),
    confidence_score DECIMAL(5,4) CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    source_comment_id UUID REFERENCES comments(id) ON DELETE SET NULL,
    mentioned_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT chk_willingness_price CHECK (
        price_point IS NULL OR price_point >= 0
    )
);

COMMENT ON TABLE user_willingness_to_pay IS 'Direct user statements about payment willingness and price points';

-- ============================================================================
-- Technical Assessments Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS technical_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    api_integrations_required TEXT,
    regulatory_considerations TEXT,
    development_complexity VARCHAR(50),
    resource_requirements TEXT,
    estimated_timeline VARCHAR(100),
    feasibility_score INTEGER CHECK (feasibility_score >= 0 AND feasibility_score <= 100),
    technical_notes TEXT,
    risk_factors TEXT,
    assessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assessor VARCHAR(255),

    CONSTRAINT chk_technical_feasibility CHECK (
        feasibility_score >= 0 AND feasibility_score <= 100
    ),
    CONSTRAINT chk_technical_complexity CHECK (
        development_complexity IN ('low', 'medium', 'high', 'very_high')
    )
);

COMMENT ON TABLE technical_assessments IS 'Technical feasibility and development complexity assessment';

-- ============================================================================
-- Indexes for Monetization & Technical
-- ============================================================================

-- Monetization Patterns indexes
CREATE INDEX IF NOT EXISTS idx_monetization_opportunity ON monetization_patterns(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_monetization_type ON monetization_patterns(model_type);
CREATE INDEX IF NOT EXISTS idx_monetization_revenue ON monetization_patterns(revenue_estimate DESC);
CREATE INDEX IF NOT EXISTS idx_monetization_validation ON monetization_patterns(validation_status);
CREATE INDEX IF NOT EXISTS idx_monetization_market_segment ON monetization_patterns(market_segment);
CREATE INDEX IF NOT EXISTS idx_monetization_identified ON monetization_patterns(identified_at DESC);
CREATE INDEX IF NOT EXISTS idx_monetization_evidence_gin ON monetization_patterns USING gin(to_tsvector('english', pricing_evidence));

-- User Willingness to Pay indexes
CREATE INDEX IF NOT EXISTS idx_willingness_opportunity ON user_willingness_to_pay(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_willingness_price ON user_willingness_to_pay(price_point);
CREATE INDEX IF NOT EXISTS idx_willingness_segment ON user_willingness_to_pay(user_segment);
CREATE INDEX IF NOT EXISTS idx_willingness_confidence ON user_willingness_to_pay(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_willingness_mentioned ON user_willingness_to_pay(mentioned_at DESC);
CREATE INDEX IF NOT EXISTS idx_willingness_source ON user_willingness_to_pay(source_comment_id);
CREATE INDEX IF NOT EXISTS idx_willingness_context_gin ON user_willingness_to_pay USING gin(to_tsvector('english', user_context));

-- Technical Assessments indexes
CREATE INDEX IF NOT EXISTS idx_technical_opportunity ON technical_assessments(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_technical_complexity ON technical_assessments(development_complexity);
CREATE INDEX IF NOT EXISTS idx_technical_score ON technical_assessments(feasibility_score DESC);
CREATE INDEX IF NOT EXISTS idx_technical_assessed_at ON technical_assessments(assessed_at DESC);
CREATE INDEX IF NOT EXISTS idx_technical_assessor ON technical_assessments(assessor);
CREATE INDEX IF NOT EXISTS idx_technical_risks_gin ON technical_assessments USING gin(to_tsvector('english', risk_factors));

-- Migration completed
