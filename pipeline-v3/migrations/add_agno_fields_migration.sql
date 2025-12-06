-- Migration script to add agno_* fields to opportunities table
-- These fields store detailed analysis from each Agno agent

-- Begin transaction
BEGIN;

-- Add agno_* columns to opportunities table
ALTER TABLE opportunities
ADD COLUMN IF NOT EXISTS agno_wtp_score FLOAT CHECK (agno_wtp_score >= 0.0 AND agno_wtp_score <= 100.0),
ADD COLUMN IF NOT EXISTS agno_segment_type VARCHAR(20) CHECK (agno_segment_type IN ('B2B', 'B2C', 'Hybrid')),
ADD COLUMN IF NOT EXISTS agno_segment_confidence FLOAT CHECK (agno_segment_confidence >= 0.0 AND agno_segment_confidence <= 100.0),
ADD COLUMN IF NOT EXISTS agno_price_potential FLOAT CHECK (agno_price_potential >= 0.0 AND agno_price_potential <= 100.0),
ADD COLUMN IF NOT EXISTS agno_behavior_score FLOAT CHECK (agno_behavior_score >= 0.0 AND agno_behavior_score <= 100.0),
ADD COLUMN IF NOT EXISTS agno_consensus_confidence FLOAT CHECK (agno_consensus_confidence >= 0.0 AND agno_consensus_confidence <= 100.0),
ADD COLUMN IF NOT EXISTS agno_agent_details JSONB;

-- Add indexes for the new fields for better query performance
CREATE INDEX IF NOT EXISTS idx_opportunities_agno_wtp_score ON opportunities(agno_wtp_score) WHERE agno_wtp_score IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_opportunities_agno_segment_type ON opportunities(agno_segment_type) WHERE agno_segment_type IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_opportunities_agno_price_potential ON opportunities(agno_price_potential) WHERE agno_price_potential IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_opportunities_agno_behavior_score ON opportunities(agno_behavior_score) WHERE agno_behavior_score IS NOT NULL;

-- Create GIN index on the JSONB agent details for efficient querying
CREATE INDEX IF NOT EXISTS idx_opportunities_agno_agent_details ON opportunities USING GIN(agno_agent_details) WHERE agno_agent_details IS NOT NULL;

-- Create a composite index for common agno field queries
CREATE INDEX IF NOT EXISTS idx_opportunities_agno_composite ON opportunities(agno_wtp_score, agno_price_potential)
WHERE agno_wtp_score IS NOT NULL AND agno_price_potential IS NOT NULL;

-- Add comments to document the new fields
COMMENT ON COLUMN opportunities.agno_wtp_score IS 'Willingness to pay score from Agno WTP agent (0-100)';
COMMENT ON COLUMN opportunities.agno_segment_type IS 'Market segment type from Agno Segment agent (B2B, B2C, Hybrid)';
COMMENT ON COLUMN opportunities.agno_segment_confidence IS 'Market segment confidence from Agno Segment agent (0-100)';
COMMENT ON COLUMN opportunities.agno_price_potential IS 'Price potential score from Agno Price agent (0-100)';
COMMENT ON COLUMN opportunities.agno_behavior_score IS 'Payment behavior score from Agno Behavior agent (0-100)';
COMMENT ON COLUMN opportunities.agno_consensus_confidence IS 'Consensus confidence across all Agno agents (0-100)';
COMMENT ON COLUMN opportunities.agno_agent_details IS 'Raw JSON output from all Agno agents for detailed analysis';

-- Commit the transaction
COMMIT;

-- Verify the columns were added
\d opportunities

-- Show the added indexes
\di+ idx_opportunities_agno_*