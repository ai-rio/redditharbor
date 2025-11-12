-- Add Trust Layer Columns to app_opportunities Table
-- Migration for comprehensive trust validation and credibility indicators
-- Created: 2025-11-12

-- Trust level and score columns
ALTER TABLE app_opportunities
ADD COLUMN IF NOT EXISTS trust_level TEXT CHECK (trust_level IN ('VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN'));

ALTER TABLE app_opportunities
ADD COLUMN IF NOT EXISTS trust_score DECIMAL(5,2) DEFAULT 0.0 CHECK (trust_score >= 0 AND trust_score <= 100);

ALTER TABLE app_opportunities
ADD COLUMN IF NOT EXISTS trust_badge TEXT CHECK (trust_badge IN ('GOLD', 'SILVER', 'BRONZE', 'BASIC', 'NO-BADGE'));

-- Activity and engagement columns
ALTER TABLE app_opportunities
ADD COLUMN IF NOT EXISTS activity_score DECIMAL(6,2) DEFAULT 0.0 CHECK (activity_score >= 0);

ALTER TABLE app_opportunities
ADD COLUMN IF NOT EXISTS engagement_level TEXT CHECK (engagement_level IN ('VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW', 'MINIMAL'));

ALTER TABLE app_opportunities
ADD COLUMN IF NOT EXISTS trend_velocity DECIMAL(8,4) DEFAULT 0.0;

-- Validation indicator columns
ALTER TABLE app_opportunities
ADD COLUMN IF NOT EXISTS problem_validity TEXT CHECK (problem_validity IN ('VALID', 'POTENTIAL', 'UNCLEAR', 'INVALID'));

ALTER TABLE app_opportunities
ADD COLUMN IF NOT EXISTS discussion_quality TEXT CHECK (discussion_quality IN ('EXCELLENT', 'GOOD', 'FAIR', 'POOR'));

ALTER TABLE app_opportunities
ADD COLUMN IF NOT EXISTS ai_confidence_level TEXT CHECK (ai_confidence_level IN ('VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW'));

-- Additional data and timestamps
ALTER TABLE app_opportunities
ADD COLUMN IF NOT EXISTS trust_factors JSONB DEFAULT '{}';

ALTER TABLE app_opportunities
ADD COLUMN IF NOT EXISTS trust_updated_at TIMESTAMPTZ;

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_app_opportunities_trust_level ON app_opportunities(trust_level);
CREATE INDEX IF NOT EXISTS idx_app_opportunities_trust_score ON app_opportunities(trust_score);
CREATE INDEX IF NOT EXISTS idx_app_opportunities_trust_badge ON app_opportunities(trust_badge);
CREATE INDEX IF NOT EXISTS idx_app_opportunities_activity_score ON app_opportunities(activity_score);
CREATE INDEX IF NOT EXISTS idx_app_opportunities_engagement_level ON app_opportunities(engagement_level);
CREATE INDEX IF NOT EXISTS idx_app_opportunities_trust_updated_at ON app_opportunities(trust_updated_at);

-- Add composite index for common queries
CREATE INDEX IF NOT EXISTS idx_app_opportunities_trust_composite ON app_opportunities(trust_level, trust_score, activity_score);