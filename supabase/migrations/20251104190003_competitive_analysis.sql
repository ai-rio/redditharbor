-- Migration 4: Competitive Analysis
-- Created: 2025-11-04 19:00:03
-- Description: Creates competitive analysis tables for market landscape
-- Tables: competitive_landscape, feature_gaps

-- ============================================================================
-- Competitive Landscape Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS competitive_landscape (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    competitor_name VARCHAR(255) NOT NULL,
    market_position TEXT,
    pricing_model VARCHAR(100),
    strengths TEXT,
    weaknesses TEXT,
    market_share_estimate DECIMAL(5,2),
    user_count_estimate INTEGER,
    verification_status VARCHAR(50) DEFAULT 'unverified',
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_competitive_market_share CHECK (
        market_share_estimate >= 0.0 AND market_share_estimate <= 100.0
    ),
    CONSTRAINT chk_competitive_users CHECK (
        user_count_estimate IS NULL OR user_count_estimate >= 0
    )
);

COMMENT ON TABLE competitive_landscape IS 'Analysis of existing solutions in the market';

-- ============================================================================
-- Feature Gaps Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS feature_gaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    existing_solution VARCHAR(255),
    missing_feature TEXT NOT NULL,
    user_requests_count INTEGER DEFAULT 0,
    priority_level VARCHAR(20) DEFAULT 'medium',
    user_evidence TEXT,
    identified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_feature_gaps_requests CHECK (user_requests_count >= 0),
    CONSTRAINT chk_feature_gaps_priority CHECK (
        priority_level IN ('low', 'medium', 'high', 'critical')
    )
);

COMMENT ON TABLE feature_gaps IS 'Missing features in existing solutions identified from user discussions';

-- ============================================================================
-- Indexes for Competitive Analysis
-- ============================================================================

-- Competitive Landscape indexes
CREATE INDEX IF NOT EXISTS idx_competitive_opportunity ON competitive_landscape(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_competitive_name ON competitive_landscape(competitor_name);
CREATE INDEX IF NOT EXISTS idx_competitive_market_share ON competitive_landscape(market_share_estimate DESC);
CREATE INDEX IF NOT EXISTS idx_competitive_verification ON competitive_landscape(verification_status);
CREATE INDEX IF NOT EXISTS idx_competitive_updated ON competitive_landscape(last_updated DESC);
CREATE INDEX IF NOT EXISTS idx_competitive_pricing ON competitive_landscape(pricing_model);
CREATE INDEX IF NOT EXISTS idx_competitive_strengths_gin ON competitive_landscape USING gin(to_tsvector('english', strengths));
CREATE INDEX IF NOT EXISTS idx_competitive_weaknesses_gin ON competitive_landscape USING gin(to_tsvector('english', weaknesses));

-- Feature Gaps indexes
CREATE INDEX IF NOT EXISTS idx_feature_gaps_opportunity ON feature_gaps(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_feature_gaps_solution ON feature_gaps(existing_solution);
CREATE INDEX IF NOT EXISTS idx_feature_gaps_priority ON feature_gaps(priority_level);
CREATE INDEX IF NOT EXISTS idx_feature_gaps_requests ON feature_gaps(user_requests_count DESC);
CREATE INDEX IF NOT EXISTS idx_feature_gaps_identified ON feature_gaps(identified_at DESC);
CREATE INDEX IF NOT EXISTS idx_feature_gaps_evidence_gin ON feature_gaps USING gin(to_tsvector('english', user_evidence));

-- Migration completed
