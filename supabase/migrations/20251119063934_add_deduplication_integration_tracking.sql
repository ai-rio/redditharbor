-- Migration: Add Deduplication Integration Tracking Columns
-- Description: Add tracking columns for Agno/AI profile analysis, ProfilerService analysis, and deduplication integration
-- Version: 001
-- Date: 2025-11-20 (Updated)
-- Task: Deduplication Integration Project - Task 1: Database Schema Updates
-- Changes: Added missing has_profiler_analysis and workflow_results deduplication columns

-- ============================================================================
-- STEP 1: Add Agno Analysis Tracking Columns to business_concepts table
-- ============================================================================

ALTER TABLE business_concepts
ADD COLUMN IF NOT EXISTS has_agno_analysis BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS agno_analysis_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_agno_analysis_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS agno_avg_wtp_score DECIMAL(5,2) CHECK (agno_avg_wtp_score >= 0 AND agno_avg_wtp_score <= 100),
ADD COLUMN IF NOT EXISTS has_ai_profile BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS ai_profile_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_ai_profile_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS has_profiler_analysis BOOLEAN DEFAULT FALSE;

-- ============================================================================
-- STEP 2: Create llm_monetization_analysis table (if not exists)
-- ============================================================================

CREATE TABLE IF NOT EXISTS llm_monetization_analysis (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  opportunity_id UUID NOT NULL,
  submission_id TEXT,

  -- LLM Analysis Results
  llm_monetization_score DECIMAL(5,2) CHECK (llm_monetization_score >= 0 AND llm_monetization_score <= 100),
  keyword_monetization_score DECIMAL(5,2) CHECK (keyword_monetization_score >= 0 AND keyword_monetization_score <= 100),

  -- Customer Insights
  customer_segment VARCHAR(20), -- B2B, B2C, Mixed, Unknown
  willingness_to_pay_score DECIMAL(5,2),
  price_sensitivity_score DECIMAL(5,2),
  revenue_potential_score DECIMAL(5,2),

  -- Sentiment & Behavior
  payment_sentiment VARCHAR(20), -- Positive, Neutral, Negative
  urgency_level VARCHAR(20), -- Low, Medium, High, Critical
  existing_payment_behavior TEXT,

  -- Extracted Data
  mentioned_price_points JSONB, -- Array of price points found
  payment_friction_indicators JSONB, -- Array of friction signals

  -- Meta
  confidence DECIMAL(3,2) CHECK (confidence >= 0 AND confidence <= 1),
  reasoning TEXT,
  subreddit_multiplier DECIMAL(3,2),

  -- LLM Execution Details
  model_used VARCHAR(100), -- e.g., "openai/gpt-4o-mini"
  tokens_used INTEGER,
  cost_usd DECIMAL(10,6),
  latency_ms INTEGER,
  analyzed_at TIMESTAMPTZ DEFAULT NOW(),

  -- Comparison
  score_delta DECIMAL(6,2), -- llm_score - keyword_score (for A/B testing)

  CONSTRAINT unique_opportunity_analysis UNIQUE(opportunity_id)
);

-- ============================================================================
-- STEP 3: Add Deduplication Tracking Columns to llm_monetization_analysis table
-- ============================================================================

ALTER TABLE llm_monetization_analysis
ADD COLUMN IF NOT EXISTS copied_from_primary BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS primary_opportunity_id UUID REFERENCES opportunities_unified(id) DEFERRABLE INITIALLY DEFERRED,
ADD COLUMN IF NOT EXISTS business_concept_id BIGINT REFERENCES business_concepts(id);

-- ============================================================================
-- STEP 4: Add Deduplication Tracking Columns to opportunities_unified table
-- ============================================================================

ALTER TABLE opportunities_unified
ADD COLUMN IF NOT EXISTS copied_from_primary BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS primary_opportunity_id UUID REFERENCES opportunities_unified(id) DEFERRABLE INITIALLY DEFERRED;

-- ============================================================================
-- STEP 5: Add Deduplication Tracking Columns to workflow_results table
-- ============================================================================

ALTER TABLE workflow_results
ADD COLUMN IF NOT EXISTS copied_from_primary BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS app_name TEXT,
ADD COLUMN IF NOT EXISTS core_functions TEXT;

-- ============================================================================
-- STEP 6: Create Indexes for Fast Lookups
-- ============================================================================

-- Indexes for business_concepts Agno/AI profile tracking
CREATE INDEX IF NOT EXISTS idx_business_concepts_agno_analysis
ON business_concepts(has_agno_analysis, last_agno_analysis_at DESC);

CREATE INDEX IF NOT EXISTS idx_business_concepts_ai_profile
ON business_concepts(has_ai_profile, last_ai_profile_at DESC);

CREATE INDEX IF NOT EXISTS idx_business_concepts_wtp_score
ON business_concepts(agno_avg_wtp_score DESC)
WHERE agno_avg_wtp_score IS NOT NULL;

-- Indexes for llm_monetization_analysis deduplication tracking
CREATE INDEX IF NOT EXISTS idx_llm_analysis_deduplication
ON llm_monetization_analysis(copied_from_primary, primary_opportunity_id);

CREATE INDEX IF NOT EXISTS idx_llm_analysis_business_concept
ON llm_monetization_analysis(business_concept_id);

-- Indexes for opportunities_unified deduplication tracking
CREATE INDEX IF NOT EXISTS idx_opportunities_unified_deduplication
ON opportunities_unified(copied_from_primary, primary_opportunity_id);

-- Additional useful indexes for llm_monetization_analysis
CREATE INDEX IF NOT EXISTS idx_llm_analysis_opportunity ON llm_monetization_analysis(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_llm_analysis_submission ON llm_monetization_analysis(submission_id);
CREATE INDEX IF NOT EXISTS idx_llm_analysis_segment ON llm_monetization_analysis(customer_segment);
CREATE INDEX IF NOT EXISTS idx_llm_analysis_llm_score ON llm_monetization_analysis(llm_monetization_score DESC);
CREATE INDEX IF NOT EXISTS idx_llm_analysis_score_delta ON llm_monetization_analysis(score_delta DESC);
CREATE INDEX IF NOT EXISTS idx_llm_analysis_analyzed_at ON llm_monetization_analysis(analyzed_at DESC);

-- Indexes for workflow_results deduplication tracking
CREATE INDEX IF NOT EXISTS idx_workflow_results_deduplication ON workflow_results(copied_from_primary);
CREATE INDEX IF NOT EXISTS idx_workflow_results_app_name ON workflow_results(app_name);

-- ============================================================================
-- STEP 7: Create Constraints and Triggers
-- ============================================================================

-- Note: Foreign key constraints are already added in the ALTER TABLE statements above
-- They are marked as DEFERRABLE INITIALLY DEFERRED to handle circular dependencies

-- ============================================================================
-- STEP 8: Create Utility Views
-- ============================================================================

-- View for Agno analysis statistics
CREATE OR REPLACE VIEW agno_analysis_stats AS
SELECT
  COUNT(*) as total_concepts,
  COUNT(CASE WHEN has_agno_analysis THEN 1 END) as concepts_with_agno,
  COUNT(CASE WHEN has_ai_profile THEN 1 END) as concepts_with_ai_profile,
  COUNT(CASE WHEN has_agno_analysis AND has_ai_profile THEN 1 END) as concepts_with_both,
  ROUND(
    COUNT(CASE WHEN has_agno_analysis THEN 1 END)::numeric /
    NULLIF(COUNT(*), 0) * 100,
    2
  ) as agno_adoption_rate_percent,
  ROUND(
    COUNT(CASE WHEN has_ai_profile THEN 1 END)::numeric /
    NULLIF(COUNT(*), 0) * 100,
    2
  ) as ai_profile_adoption_rate_percent,
  AVG(agno_avg_wtp_score) as avg_wtp_score,
  MAX(last_agno_analysis_at) as latest_agno_analysis,
  MAX(last_ai_profile_at) as latest_ai_profile
FROM business_concepts;

-- View for deduplication integration statistics
CREATE OR REPLACE VIEW deduplication_integration_stats AS
SELECT
  'business_concepts' as table_name,
  COUNT(*) as total_records,
  COUNT(CASE WHEN has_agno_analysis THEN 1 END) as agno_analyzed,
  COUNT(CASE WHEN has_ai_profile THEN 1 END) as ai_profile_analyzed,
  0 as copied_records,
  COUNT(CASE WHEN primary_opportunity_id IS NOT NULL THEN 1 END) as has_primary_reference
FROM business_concepts
WHERE 1=1

UNION ALL

SELECT
  'llm_monetization_analysis' as table_name,
  COUNT(*) as total_records,
  0 as agno_analyzed,
  0 as ai_profile_analyzed,
  COUNT(CASE WHEN copied_from_primary THEN 1 END) as copied_records,
  COUNT(CASE WHEN primary_opportunity_id IS NOT NULL THEN 1 END) as has_primary_reference
FROM llm_monetization_analysis

UNION ALL

SELECT
  'opportunities_unified' as table_name,
  COUNT(*) as total_records,
  0 as agno_analyzed,
  0 as ai_profile_analyzed,
  COUNT(CASE WHEN copied_from_primary THEN 1 END) as copied_records,
  COUNT(CASE WHEN primary_opportunity_id IS NOT NULL THEN 1 END) as has_primary_reference
FROM opportunities_unified

UNION ALL

SELECT
  'workflow_results' as table_name,
  COUNT(*) as total_records,
  0 as agno_analyzed,
  0 as ai_profile_analyzed,
  COUNT(CASE WHEN copied_from_primary THEN 1 END) as copied_records,
  0 as has_primary_reference
FROM workflow_results;

-- ============================================================================
-- STEP 9: Add Comments for Documentation
-- ============================================================================

-- Comments for business_concepts table
COMMENT ON COLUMN business_concepts.has_agno_analysis IS 'Indicates if this concept has been processed by Agno AI agent';
COMMENT ON COLUMN business_concepts.agno_analysis_count IS 'Number of times Agno analysis has been performed on this concept';
COMMENT ON COLUMN business_concepts.last_agno_analysis_at IS 'Timestamp of the most recent Agno analysis';
COMMENT ON COLUMN business_concepts.agno_avg_wtp_score IS 'Average willingness-to-pay score from Agno analyses (0-100)';
COMMENT ON COLUMN business_concepts.has_ai_profile IS 'Indicates if this concept has an AI-generated profile';
COMMENT ON COLUMN business_concepts.ai_profile_count IS 'Number of AI profiles generated for this concept';
COMMENT ON COLUMN business_concepts.last_ai_profile_at IS 'Timestamp of the most recent AI profile generation';
COMMENT ON COLUMN business_concepts.has_profiler_analysis IS 'Indicates if this concept has been processed by ProfilerService analysis';

-- Comments for llm_monetization_analysis table
COMMENT ON TABLE llm_monetization_analysis IS 'LLM-powered monetization analysis results for opportunities';
COMMENT ON COLUMN llm_monetization_analysis.copied_from_primary IS 'Indicates if this analysis was copied from a primary opportunity';
COMMENT ON COLUMN llm_monetization_analysis.primary_opportunity_id IS 'Reference to the primary opportunity if this was copied';
COMMENT ON COLUMN llm_monetization_analysis.business_concept_id IS 'Foreign key to business_concepts for deduplication integration';

-- Comments for opportunities_unified table
COMMENT ON COLUMN opportunities_unified.copied_from_primary IS 'Indicates if this opportunity was copied from a primary opportunity';
COMMENT ON COLUMN opportunities_unified.primary_opportunity_id IS 'Reference to the primary opportunity if this is a duplicate';

-- Comments for workflow_results table
COMMENT ON COLUMN workflow_results.copied_from_primary IS 'Indicates if this workflow result was copied from a primary opportunity';
COMMENT ON COLUMN workflow_results.app_name IS 'Application name stored for deduplication tracking';
COMMENT ON COLUMN workflow_results.core_functions IS 'Core functions description stored for deduplication tracking';

-- ============================================================================
-- STEP 10: Create Helper Functions
-- ============================================================================

-- Function to update Agno analysis tracking
CREATE OR REPLACE FUNCTION update_agno_analysis_tracking(
  p_concept_id BIGINT,
  p_has_analysis BOOLEAN DEFAULT TRUE,
  p_wtp_score DECIMAL(5,2) DEFAULT NULL
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE business_concepts
  SET
    has_agno_analysis = p_has_analysis,
    agno_analysis_count = CASE WHEN p_has_analysis THEN agno_analysis_count + 1 ELSE agno_analysis_count END,
    last_agno_analysis_at = CASE WHEN p_has_analysis THEN NOW() ELSE last_agno_analysis_at END,
    agno_avg_wtp_score = CASE
      WHEN p_has_analysis AND p_wtp_score IS NOT NULL THEN
        (COALESCE(agno_avg_wtp_score * agno_analysis_count, 0) + p_wtp_score) / (agno_analysis_count + 1)
      ELSE agno_avg_wtp_score
    END
  WHERE id = p_concept_id;

  RETURN FOUND;
END;
$$;

-- Function to update AI profile tracking
CREATE OR REPLACE FUNCTION update_ai_profile_tracking(
  p_concept_id BIGINT,
  p_has_profile BOOLEAN DEFAULT TRUE
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE business_concepts
  SET
    has_ai_profile = p_has_profile,
    ai_profile_count = CASE WHEN p_has_profile THEN ai_profile_count + 1 ELSE ai_profile_count END,
    last_ai_profile_at = CASE WHEN p_has_profile THEN NOW() ELSE last_ai_profile_at END
  WHERE id = p_concept_id;

  RETURN FOUND;
END;
$$;