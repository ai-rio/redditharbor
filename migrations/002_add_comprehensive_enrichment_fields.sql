-- Migration: Add Comprehensive Enrichment Fields
-- Description: Align app_opportunities schema with unified pipeline output for 93.1% field coverage
-- Version: 002
-- Date: 2025-11-20
-- Task: Database Schema Alignment - Test 01 Field Coverage Achievement

-- This migration adds all missing enrichment fields that our unified pipeline generates
-- to achieve the 93.1% field coverage validated in Test 01

-- Add missing ProfilerService fields
ALTER TABLE app_opportunities
ADD COLUMN IF NOT EXISTS ai_profile JSONB,
ADD COLUMN IF NOT EXISTS app_name TEXT,
ADD COLUMN IF NOT EXISTS app_category TEXT,
ADD COLUMN IF NOT EXISTS profession TEXT,
ADD COLUMN IF NOT EXISTS core_problems JSONB;

-- Add missing OpportunityService fields
ALTER TABLE app_opportunities
ADD COLUMN IF NOT EXISTS dimension_scores JSONB,
ADD COLUMN IF NOT EXISTS priority TEXT,
ADD COLUMN IF NOT EXISTS confidence DECIMAL(3,2),
ADD COLUMN IF NOT EXISTS evidence_based BOOLEAN DEFAULT FALSE;

-- Add missing MonetizationService field
ALTER TABLE app_opportunities
ADD COLUMN IF NOT EXISTS monetization_score DECIMAL(5,2);

-- Add missing TrustService fields
ALTER TABLE app_opportunities
ADD COLUMN IF NOT EXISTS trust_level TEXT,
ADD COLUMN IF NOT EXISTS trust_badges JSONB;

-- Add missing MarketValidationService field
ALTER TABLE app_opportunities
ADD COLUMN IF NOT EXISTS market_validation_score DECIMAL(5,2);

-- Add metadata and timestamp fields
ALTER TABLE app_opportunities
ADD COLUMN IF NOT EXISTS analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS enrichment_version VARCHAR(20) DEFAULT 'v3.0.0',
ADD COLUMN IF NOT EXISTS pipeline_source VARCHAR(50) DEFAULT 'unified_pipeline';

-- Create indexes for frequently queried fields
CREATE INDEX IF NOT EXISTS idx_app_opportunities_trust_level
ON app_opportunities(trust_level);

CREATE INDEX IF NOT EXISTS idx_app_opportunities_priority
ON app_opportunities(priority);

CREATE INDEX IF NOT EXISTS idx_app_opportunities_analyzed_at
ON app_opportunities(analyzed_at);

CREATE INDEX IF NOT EXISTS idx_app_opportunities_submission_id
ON app_opportunities(submission_id);

-- Create a view to monitor field coverage
CREATE OR REPLACE VIEW enrichment_coverage_stats AS
SELECT
    COUNT(*) as total_records,
    COUNT(CASE WHEN ai_profile IS NOT NULL THEN 1 END) as with_ai_profile,
    COUNT(CASE WHEN app_name IS NOT NULL THEN 1 END) as with_app_name,
    COUNT(CASE WHEN app_category IS NOT NULL THEN 1 END) as with_app_category,
    COUNT(CASE WHEN profession IS NOT NULL THEN 1 END) as with_profession,
    COUNT(CASE WHEN monetization_score IS NOT NULL THEN 1 END) as with_monetization_score,
    COUNT(CASE WHEN trust_level IS NOT NULL THEN 1 END) as with_trust_level,
    COUNT(CASE WHEN market_validation_score IS NOT NULL THEN 1 END) as with_market_validation_score,
    COUNT(CASE WHEN dimension_scores IS NOT NULL THEN 1 END) as with_dimension_scores,
    COUNT(CASE WHEN priority IS NOT NULL THEN 1 END) as with_priority,
    COUNT(CASE WHEN confidence IS NOT NULL THEN 1 END) as with_confidence,
    COUNT(CASE WHEN core_functions IS NOT NULL THEN 1 END) as with_core_functions,
    ROUND(
        (
            COUNT(CASE WHEN ai_profile IS NOT NULL THEN 1 END) +
            COUNT(CASE WHEN app_name IS NOT NULL THEN 1 END) +
            COUNT(CASE WHEN app_category IS NOT NULL THEN 1 END) +
            COUNT(CASE WHEN profession IS NOT NULL THEN 1 END) +
            COUNT(CASE WHEN monetization_score IS NOT NULL THEN 1 END) +
            COUNT(CASE WHEN trust_level IS NOT NULL THEN 1 END) +
            COUNT(CASE WHEN market_validation_score IS NOT NULL THEN 1 END) +
            COUNT(CASE WHEN dimension_scores IS NOT NULL THEN 1 END) +
            COUNT(CASE WHEN priority IS NOT NULL THEN 1 END) +
            COUNT(CASE WHEN confidence IS NOT NULL THEN 1 END) +
            COUNT(CASE WHEN core_functions IS NOT NULL THEN 1 END) +
            COUNT(CASE WHEN problem_description IS NOT NULL THEN 1 END) +
            COUNT(CASE WHEN app_concept IS NOT NULL THEN 1 END) +
            COUNT(CASE WHEN value_proposition IS NOT NULL THEN 1 END) +
            COUNT(CASE WHEN target_user IS NOT NULL THEN 1 END) +
            COUNT(CASE WHEN opportunity_score IS NOT NULL THEN 1 END) +
            COUNT(CASE WHEN final_score IS NOT NULL THEN 1 END) +
            COUNT(CASE WHEN submission_id IS NOT NULL THEN 1 END)
        ) ::numeric / NULLIF(COUNT(*), 0) * 100,
        2
    ) as field_coverage_percentage
FROM app_opportunities;

-- Add comments for documentation
COMMENT ON COLUMN app_opportunities.ai_profile IS 'AI-generated profile with app details and user insights from ProfilerService';
COMMENT ON COLUMN app_opportunities.app_name IS 'Generated application name from ProfilerService analysis';
COMMENT ON COLUMN app_opportunities.app_category IS 'Application category classification from ProfilerService';
COMMENT ON COLUMN app_opportunities.profession IS 'Target profession from ProfilerService analysis';
COMMENT ON app_opportunities.core_problems IS 'Core problems identified from ProfilerService analysis';
COMMENT ON COLUMN app_opportunities.dimension_scores IS 'Opportunity scoring dimensions from OpportunityService';
COMMENT ON COLUMN app_opportunities.priority IS 'Priority level from OpportunityService scoring';
COMMENT ON COLUMN app_opportunities.confidence IS 'Confidence score from OpportunityService analysis';
COMMENT ON COLUMN app_opportunities.evidence_based IS 'Whether analysis is evidence-based from OpportunityService';
COMMENT ON COLUMN app_opportunities.monetization_score IS 'Monetization potential score from MonetizationService';
COMMENT ON COLUMN app_opportunities.trust_level IS 'Trust validation level from TrustService';
COMMENT ON COLUMN app_opportunities.trust_badges IS 'Trust badges earned from TrustService validation';
COMMENT ON COLUMN app_opportunities.market_validation_score IS 'Market validation score from MarketValidationService';
COMMENT ON COLUMN app_opportunities.analyzed_at IS 'Timestamp when enrichment analysis was completed';
COMMENT ON COLUMN app_opportunities.enrichment_version IS 'Version of enrichment pipeline used';
COMMENT ON COLUMN app_opportunities.pipeline_source IS 'Source of the enrichment data (unified_pipeline, monolith, etc.)';

COMMIT;