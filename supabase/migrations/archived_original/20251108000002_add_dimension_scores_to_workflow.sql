-- Add 5 dimension score columns to workflow_results
ALTER TABLE workflow_results
ADD COLUMN IF NOT EXISTS market_demand DECIMAL(5,2)
    CHECK (market_demand >= 0 AND market_demand <= 100),
ADD COLUMN IF NOT EXISTS pain_intensity DECIMAL(5,2)
    CHECK (pain_intensity >= 0 AND pain_intensity <= 100),
ADD COLUMN IF NOT EXISTS monetization_potential DECIMAL(5,2)
    CHECK (monetization_potential >= 0 AND monetization_potential <= 100),
ADD COLUMN IF NOT EXISTS market_gap DECIMAL(5,2)
    CHECK (market_gap >= 0 AND market_gap <= 100),
ADD COLUMN IF NOT EXISTS technical_feasibility DECIMAL(5,2)
    CHECK (technical_feasibility >= 0 AND technical_feasibility <= 100);

-- Add indexes for dimension-based queries
CREATE INDEX IF NOT EXISTS idx_workflow_results_market_demand
    ON workflow_results(market_demand DESC);
CREATE INDEX IF NOT EXISTS idx_workflow_results_pain_intensity
    ON workflow_results(pain_intensity DESC);
CREATE INDEX IF NOT EXISTS idx_workflow_results_monetization
    ON workflow_results(monetization_potential DESC);

-- Add documentation
COMMENT ON COLUMN workflow_results.market_demand IS
    'Market demand score (0-100): Discussion volume + engagement rate + trend velocity + audience size';
COMMENT ON COLUMN workflow_results.pain_intensity IS
    'Pain intensity score (0-100): Negative sentiment + emotional language + repetition + workaround complexity';
COMMENT ON COLUMN workflow_results.monetization_potential IS
    'Monetization potential score (0-100): Willingness to pay + commercial gaps + B2B/B2C signals + revenue model hints';
COMMENT ON COLUMN workflow_results.market_gap IS
    'Market gap score (0-100): Competition density + solution inadequacy + innovation opportunities';
COMMENT ON COLUMN workflow_results.technical_feasibility IS
    'Technical feasibility score (0-100): Development complexity + API integration needs + implementation simplicity';
