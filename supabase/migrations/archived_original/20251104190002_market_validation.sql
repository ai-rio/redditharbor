-- Migration 3: Market Validation
-- Created: 2025-11-04 19:00:02
-- Description: Creates market validation tables for cross-platform verification
-- Tables: market_validations, cross_platform_verification

-- ============================================================================
-- Market Validations Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS market_validations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    validation_type VARCHAR(100) NOT NULL,
    validation_source VARCHAR(100) NOT NULL,
    validation_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    validation_result TEXT NOT NULL,
    confidence_score DECIMAL(5,4) CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    notes TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    evidence_url TEXT,

    CONSTRAINT chk_market_validations_confidence CHECK (
        confidence_score >= 0.0 AND confidence_score <= 1.0
    )
);

COMMENT ON TABLE market_validations IS 'Primary validation metrics for opportunities';
COMMENT ON COLUMN market_validations.validation_type IS 'e.g., problem_validation, market_validation, price_sensitivity';

-- ============================================================================
-- Cross-Platform Verification Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS cross_platform_verification (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    platform_name VARCHAR(100) NOT NULL,
    validation_status VARCHAR(50) DEFAULT 'pending',
    data_points_count INTEGER DEFAULT 0,
    data_points TEXT,
    verified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    confidence_score DECIMAL(5,4) CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    platform_notes TEXT,

    CONSTRAINT chk_cross_platform_data_points CHECK (data_points_count >= 0)
);

COMMENT ON TABLE cross_platform_verification IS 'Cross-platform verification (Twitter, LinkedIn, Product Hunt, etc.)';
COMMENT ON COLUMN cross_platform_verification.platform_name IS 'e.g., twitter, linkedin, product_hunt, app_store';

-- ============================================================================
-- Indexes for Market Validation
-- ============================================================================

-- Market Validations indexes
CREATE INDEX IF NOT EXISTS idx_market_validations_opportunity ON market_validations(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_market_validations_type ON market_validations(validation_type);
CREATE INDEX IF NOT EXISTS idx_market_validations_status ON market_validations(status);
CREATE INDEX IF NOT EXISTS idx_market_validations_confidence ON market_validations(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_market_validations_date ON market_validations(validation_date DESC);
CREATE INDEX IF NOT EXISTS idx_market_validations_source ON market_validations(validation_source);

-- Cross-Platform Verification indexes
CREATE INDEX IF NOT EXISTS idx_cross_platform_opportunity ON cross_platform_verification(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_cross_platform_name ON cross_platform_verification(platform_name);
CREATE INDEX IF NOT EXISTS idx_cross_platform_status ON cross_platform_verification(validation_status);
CREATE INDEX IF NOT EXISTS idx_cross_platform_confidence ON cross_platform_verification(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_cross_platform_data_points_gin ON cross_platform_verification USING gin(to_tsvector('english', data_points));

-- Migration completed
