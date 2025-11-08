-- Add insight columns to opportunity_analysis table

ALTER TABLE opportunity_analysis
ADD COLUMN IF NOT EXISTS app_concept TEXT,
ADD COLUMN IF NOT EXISTS core_functions TEXT[],
ADD COLUMN IF NOT EXISTS growth_justification TEXT;

-- Add index for quick retrieval
CREATE INDEX IF NOT EXISTS idx_opportunity_insights
ON opportunity_analysis(final_score DESC)
WHERE app_concept IS NOT NULL;

COMMENT ON COLUMN opportunity_analysis.app_concept IS 'One-line app description (e.g., "Tax automation tool for freelancers")';
COMMENT ON COLUMN opportunity_analysis.core_functions IS 'Array of 1-3 key features';
COMMENT ON COLUMN opportunity_analysis.growth_justification IS 'Why this has monetization potential';
