-- ============================================================================
-- MARKET VALIDATION PERSISTENCY MIGRATION
-- RedditHarbor Jina Reader API Integration
--
-- Migration: 001_add_market_validation_fields.sql
-- Purpose: Add Jina Reader API specific columns for market validation persistency
-- Date: 2025-11-16
-- ============================================================================

-- Step 1: Add market validation columns to app_opportunities table
-- These provide quick access to key validation metrics without joins

ALTER TABLE app_opportunities
ADD COLUMN market_validation_score NUMERIC(5,2) CHECK (market_validation_score >= 0 AND market_validation_score <= 100),
ADD COLUMN market_data_quality_score NUMERIC(5,2) CHECK (market_data_quality_score >= 0 AND market_data_quality_score <= 100),
ADD COLUMN market_validation_reasoning TEXT,
ADD COLUMN market_competitors_found JSONB,
ADD COLUMN market_size_tam VARCHAR(50),
ADD COLUMN market_size_sam VARCHAR(50),
ADD COLUMN market_size_growth VARCHAR(20),
ADD COLUMN market_similar_launches INTEGER DEFAULT 0,
ADD COLUMN market_validation_cost_usd NUMERIC(10,6) DEFAULT 0,
ADD COLUMN market_validation_timestamp TIMESTAMPTZ;

-- Step 2: Enhance existing market_validations table with Jina-specific fields

ALTER TABLE market_validations
ADD COLUMN market_validation_score NUMERIC(5,2) CHECK (market_validation_score >= 0 AND market_validation_score <= 100),
ADD COLUMN market_data_quality_score NUMERIC(5,2) CHECK (market_data_quality_score >= 0 AND market_data_quality_score <= 100),
ADD COLUMN market_validation_reasoning TEXT,
ADD COLUMN market_competitors_found JSONB,
ADD COLUMN market_size_tam VARCHAR(50),
ADD COLUMN market_size_sam VARCHAR(50),
ADD COLUMN market_size_growth VARCHAR(20),
ADD COLUMN market_similar_launches INTEGER DEFAULT 0,
ADD COLUMN market_validation_cost_usd NUMERIC(10,6) DEFAULT 0,
ADD COLUMN search_queries_used JSONB,
ADD COLUMN urls_fetched JSONB,
ADD COLUMN extraction_stats JSONB,
ADD COLUMN jina_api_calls_count INTEGER DEFAULT 0,
ADD COLUMN jina_cache_hit_rate NUMERIC(5,4) DEFAULT 0;

-- Step 3: Create performance indexes for efficient querying

-- Indexes for app_opportunities table
CREATE INDEX idx_app_opportunities_market_validation_score ON app_opportunities(market_validation_score DESC) WHERE market_validation_score IS NOT NULL;
CREATE INDEX idx_app_opportunities_market_data_quality ON app_opportunities(market_data_quality_score DESC) WHERE market_data_quality_score IS NOT NULL;
CREATE INDEX idx_app_opportunities_market_cost ON app_opportunities(market_validation_cost_usd DESC) WHERE market_validation_cost_usd > 0;
CREATE INDEX idx_app_opportunities_market_timestamp ON app_opportunities(market_validation_timestamp DESC) WHERE market_validation_timestamp IS NOT NULL;

-- Indexes for market_validations table
CREATE INDEX idx_market_validations_score ON market_validations(market_validation_score DESC) WHERE market_validation_score IS NOT NULL;
CREATE INDEX idx_market_validations_quality ON market_validations(market_data_quality_score DESC) WHERE market_data_quality_score IS NOT NULL;
CREATE INDEX idx_market_validations_cost ON market_validations(market_validation_cost_usd DESC) WHERE market_validation_cost_usd > 0;
CREATE INDEX idx_market_validations_jina_calls ON market_validations(jina_api_calls_count DESC) WHERE jina_api_calls_count > 0;

-- JSONB indexes for efficient querying of nested data
CREATE INDEX idx_app_opportunities_competitors ON app_opportunities USING GIN(market_competitors_found) WHERE market_competitors_found IS NOT NULL;
CREATE INDEX idx_market_validations_competitors ON market_validations USING GIN(market_competitors_found) WHERE market_competitors_found IS NOT NULL;
CREATE INDEX idx_market_validations_search_queries ON market_validations USING GIN(search_queries_used) WHERE search_queries_used IS NOT NULL;
CREATE INDEX idx_market_validations_urls_fetched ON market_validations USING GIN(urls_fetched) WHERE urls_fetched IS NOT NULL;
CREATE INDEX idx_market_validations_extraction_stats ON market_validations USING GIN(extraction_stats) WHERE extraction_stats IS NOT NULL;

-- Step 4: Add table and column comments for documentation

COMMENT ON COLUMN app_opportunities.market_validation_score IS 'Overall market validation score (0-100) from Jina Reader API analysis';
COMMENT ON COLUMN app_opportunities.market_data_quality_score IS 'Data quality score (0-100) for market validation evidence';
COMMENT ON COLUMN app_opportunities.market_validation_reasoning IS 'LLM-generated reasoning for market validation score';
COMMENT ON COLUMN app_opportunities.market_competitors_found IS 'JSON array of competitor data extracted by Jina API';
COMMENT ON COLUMN app_opportunities.market_size_tam IS 'Total Addressable Market (e.g., "$50B")';
COMMENT ON COLUMN app_opportunities.market_size_sam IS 'Serviceable Addressable Market (e.g., "$10B")';
COMMENT ON COLUMN app_opportunities.market_size_growth IS 'Market growth rate (e.g., "15% CAGR")';
COMMENT ON COLUMN app_opportunities.market_similar_launches IS 'Number of similar product launches found';
COMMENT ON COLUMN app_opportunities.market_validation_cost_usd IS 'Total cost in USD for market validation (Jina API + LLM)';
COMMENT ON COLUMN app_opportunities.market_validation_timestamp IS 'Timestamp when market validation was performed';

COMMENT ON COLUMN market_validations.market_validation_score IS 'Overall market validation score (0-100) from Jina Reader API analysis';
COMMENT ON COLUMN market_validations.market_data_quality_score IS 'Data quality score (0-100) for market validation evidence';
COMMENT ON COLUMN market_validations.market_validation_reasoning IS 'LLM-generated reasoning for market validation score';
COMMENT ON COLUMN market_validations.market_competitors_found IS 'JSON array of competitor data extracted by Jina API';
COMMENT ON COLUMN market_validations.market_size_tam IS 'Total Addressable Market (e.g., "$50B")';
COMMENT ON COLUMN market_validations.market_size_sam IS 'Serviceable Addressable Market (e.g., "$10B")';
COMMENT ON COLUMN market_validations.market_size_growth IS 'Market growth rate (e.g., "15% CAGR")';
COMMENT ON COLUMN market_validations.market_similar_launches IS 'Number of similar product launches found';
COMMENT ON COLUMN market_validations.market_validation_cost_usd IS 'Total cost in USD for market validation (Jina API + LLM)';
COMMENT ON COLUMN market_validations.search_queries_used IS 'JSON array of search queries sent to Jina API';
COMMENT ON COLUMN market_validations.urls_fetched IS 'JSON array of URLs successfully fetched by Jina Reader';
COMMENT ON COLUMN market_validations.extraction_stats IS 'JSON object with success/failure metrics for data extraction';
COMMENT ON COLUMN market_validations.jina_api_calls_count IS 'Total number of Jina API calls made during validation';
COMMENT ON COLUMN market_validations.jina_cache_hit_rate IS 'Cache efficiency rate (0-1) for Jina API calls';

-- Step 5: Create a view for market validation analytics

CREATE OR REPLACE VIEW market_validation_analytics AS
SELECT
    ao.id,
    ao.submission_id,
    ao.problem_description,
    ao.app_concept,
    ao.target_user,
    ao.opportunity_score,
    ao.market_validation_score,
    ao.market_data_quality_score,
    ao.market_size_tam,
    ao.market_size_growth,
    ao.market_similar_launches,
    ao.market_validation_cost_usd,
    ao.market_validation_timestamp,
    ao.status,
    mv.validation_type,
    mv.validation_source,
    mv.confidence_score,
    mv.market_competitors_found,
    CASE
        WHEN ao.market_validation_score >= 70 THEN 'HIGH'
        WHEN ao.market_validation_score >= 40 THEN 'MEDIUM'
        WHEN ao.market_validation_score IS NOT NULL THEN 'LOW'
        ELSE 'NOT_VALIDATED'
    END as validation_tier,
    CASE
        WHEN ao.market_data_quality_score >= 70 THEN 'HIGH'
        WHEN ao.market_data_quality_score >= 40 THEN 'MEDIUM'
        WHEN ao.market_data_quality_score IS NOT NULL THEN 'LOW'
        ELSE 'NOT_VALIDATED'
    END as data_quality_tier,
    -- ROI calculation: validation score per dollar spent
    CASE
        WHEN ao.market_validation_cost_usd > 0
        THEN ROUND(ao.market_validation_score::numeric / ao.market_validation_cost_usd, 2)
        ELSE NULL
    END as validation_roi_score
FROM app_opportunities ao
LEFT JOIN market_validations mv ON ao.id = mv.opportunity_id
WHERE ao.market_validation_timestamp IS NOT NULL OR mv.validation_date IS NOT NULL;

COMMENT ON VIEW market_validation_analytics IS 'Analytics view for market validation performance and ROI metrics';

-- Step 6: Record migration completion

INSERT INTO _migrations_log (migration_name, applied_at)
VALUES ('001_add_market_validation_fields.sql', CURRENT_TIMESTAMP);

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
--
-- This migration successfully adds:
-- ✅ Market validation columns to app_opportunities (quick access)
-- ✅ Jina-specific enhancements to market_validations (detailed storage)
-- ✅ Performance indexes for efficient querying
-- ✅ JSONB indexes for nested data structures
-- ✅ Analytics view for business intelligence
-- ✅ Proper constraints and data validation
-- ✅ Comprehensive documentation
--
-- Schema now supports comprehensive market validation persistency as recommended
-- in MARKET_VALIDATION_PERSISTENCY_ANALYSIS_20251116.md (Option 1)