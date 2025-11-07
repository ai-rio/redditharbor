-- Create opportunity_scores table for database-driven scoring
-- This table stores calculated scores for each submission based on Reddit engagement metrics
-- Scores are calculated deterministically using SQL functions

CREATE TABLE IF NOT EXISTS opportunity_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  submission_id UUID NOT NULL UNIQUE REFERENCES submissions(id) ON DELETE CASCADE,

  -- Individual component scores (0-10 scale)
  market_demand FLOAT CHECK (market_demand >= 0 AND market_demand <= 10),
  pain_intensity FLOAT CHECK (pain_intensity >= 0 AND pain_intensity <= 10),
  monetization_potential FLOAT CHECK (monetization_potential >= 0 AND monetization_potential <= 10),
  simplicity_score FLOAT CHECK (simplicity_score >= 0 AND simplicity_score <= 10),

  -- Composite score (0-100 scale)
  -- Formula: (market_demand * 0.35) + (pain_intensity * 0.30) + (monetization_potential * 0.20) + (simplicity_score * 0.15) * 10
  composite_score FLOAT CHECK (composite_score >= 0 AND composite_score <= 100),

  -- Metadata
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  calculation_version INT DEFAULT 1 COMMENT 'Version of scoring algorithm used'
);

-- Create index on submission_id for fast lookups
CREATE INDEX idx_opportunity_scores_submission_id ON opportunity_scores(submission_id);

-- Create index on composite_score for sorting/filtering
CREATE INDEX idx_opportunity_scores_composite_score ON opportunity_scores(composite_score DESC);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_opportunity_scores_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_opportunity_scores_timestamp
BEFORE UPDATE ON opportunity_scores
FOR EACH ROW
EXECUTE FUNCTION update_opportunity_scores_timestamp();

-- Add RLS (Row Level Security) policies if auth is enabled
ALTER TABLE opportunity_scores ENABLE ROW LEVEL SECURITY;

-- Policy: Allow anyone to read scores (public research data)
CREATE POLICY "Allow public read access to opportunity scores"
  ON opportunity_scores FOR SELECT
  USING (true);

-- Policy: Only service role can insert/update/delete
CREATE POLICY "Allow service role to modify opportunity scores"
  ON opportunity_scores FOR INSERT
  WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Allow service role to update opportunity scores"
  ON opportunity_scores FOR UPDATE
  USING (auth.role() = 'service_role');
