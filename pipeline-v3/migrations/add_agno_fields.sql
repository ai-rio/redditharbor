-- Migration: Add Agno multi-agent analysis fields to opportunities table
-- Version: 001_add_agno_fields.sql
-- Date: 2024-12-06

-- Add Agno agent analysis fields to opportunities table
-- These fields store results from the 5 specialized Agno agents:
-- 1. Willingness to Pay Agent
-- 2. Market Segment Agent
-- 3. Price Point Agent
-- 4. Payment Behavior Agent
-- 5. Market Research Agent

ALTER TABLE opportunities
ADD COLUMN IF NOT EXISTS agno_wtp_score FLOAT NULL COMMENT 'Agno willingness-to-pay agent score (0-100)',
ADD COLUMN IF NOT EXISTS agno_segment_confidence FLOAT NULL COMMENT 'Agno market segment confidence score (0-100)',
ADD COLUMN IF NOT EXISTS agno_price_potential FLOAT NULL COMMENT 'Agno price potential score (0-100)',
ADD COLUMN IF NOT EXISTS agno_behavior_score FLOAT NULL COMMENT 'Agno payment behavior score (0-100)',
ADD COLUMN IF NOT EXISTS agno_consensus_confidence FLOAT NULL COMMENT 'Agno agent consensus confidence (0-100)',
ADD COLUMN IF NOT EXISTS agno_segment_type VARCHAR(50) NULL COMMENT 'Agno identified market segment type',
ADD COLUMN IF NOT EXISTS agno_agents_count INTEGER NULL COMMENT 'Number of Agno agents that participated',
ADD COLUMN IF NOT EXISTS agno_analysis_cost_usd FLOAT NULL COMMENT 'Cost of Agno analysis in USD',
ADD COLUMN IF NOT EXISTS agno_agent_metadata JSON NULL COMMENT 'Metadata about Agno agent responses',
ADD COLUMN IF NOT EXISTS agno_validation_status VARCHAR(50) NULL COMMENT 'Agno market validation status';

-- Create indexes for frequently queried Agno fields
CREATE INDEX IF NOT EXISTS idx_opportunities_agno_wtp_score ON opportunities(agno_wtp_score) WHERE agno_wtp_score IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_opportunities_agno_validation_status ON opportunities(agno_validation_status) WHERE agno_validation_status IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_opportunities_agno_segment_type ON opportunities(agno_segment_type) WHERE agno_segment_type IS NOT NULL;

-- Create composite index for Agno analysis quality
CREATE INDEX IF NOT EXISTS idx_opportunities_agno_quality ON opportunities(agno_wtp_score, agno_consensus_confidence)
WHERE agno_wtp_score IS NOT NULL AND agno_consensus_confidence IS NOT NULL;

-- Add comments to document the Agno integration
COMMENT ON COLUMN opportunities.agno_wtp_score IS 'Score from Willingness-to-Pay agent analyzing user readiness to pay';
COMMENT ON COLUMN opportunities.agno_segment_confidence IS 'Confidence score from Market Segment agent for target audience identification';
COMMENT ON COLUMN opportunities.agno_price_potential IS 'Pricing potential score from Price Point agent';
COMMENT ON COLUMN opportunities.agno_behavior_score IS 'Payment behavior score from Payment Behavior agent';
COMMENT ON COLUMN opportunities.agno_consensus_confidence IS 'Consensus confidence calculated from all agent agreement';
COMMENT ON COLUMN opportunities.agno_segment_type IS 'Market segment classification (e.g., SMB, Enterprise, Consumer)';
COMMENT ON COLUMN opportunities.agno_agents_count IS 'Number of agents that successfully completed analysis';
COMMENT ON COLUMN opportunities.agno_analysis_cost_usd IS 'Total cost in USD for running Agno analysis';
COMMENT ON COLUMN opportunities.agno_agent_metadata IS 'Structured metadata about agent responses and reasoning';
COMMENT ON COLUMN opportunities.agno_validation_status IS 'Market research validation status (validated, pending, failed)';

-- Grant permissions if needed (uncomment if using specific user permissions)
-- GRANT SELECT, UPDATE ON TABLE opportunities TO reddit_user;
-- GRANT USAGE ON SEQUENCE opportunities_id_seq TO reddit_user;