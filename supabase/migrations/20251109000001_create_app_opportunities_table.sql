-- Create app_opportunities table for storing LLM-generated app ideas
-- This table stores AI-analyzed opportunities separately from workflow_results

CREATE TABLE IF NOT EXISTS app_opportunities (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id text NOT NULL,  -- Reddit submission ID

    -- LLM-generated profile fields (from LLMProfiler)
    problem_description text NOT NULL,
    app_concept text NOT NULL,
    core_functions jsonb NOT NULL,  -- Array of 1-3 strings
    value_proposition text NOT NULL,
    target_user text NOT NULL,
    monetization_model text NOT NULL,

    -- Opportunity scoring (from OpportunityAnalyzerAgent)
    opportunity_score numeric(5,2) DEFAULT 0.0,  -- 0-100 scale

    -- Additional context
    title text,
    subreddit text,
    reddit_score integer,
    num_comments integer,

    -- Metadata
    created_at timestamptz DEFAULT now(),
    analyzed_at timestamptz DEFAULT now(),

    -- Status tracking
    status text DEFAULT 'discovered' CHECK (status IN ('discovered', 'validated', 'built', 'rejected')),
    notes text
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_app_opportunities_score ON app_opportunities(opportunity_score DESC);
CREATE INDEX IF NOT EXISTS idx_app_opportunities_submission ON app_opportunities(submission_id);
CREATE INDEX IF NOT EXISTS idx_app_opportunities_status ON app_opportunities(status);
CREATE INDEX IF NOT EXISTS idx_app_opportunities_created ON app_opportunities(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_app_opportunities_subreddit ON app_opportunities(subreddit);

-- Create view for top opportunities
CREATE OR REPLACE VIEW top_opportunities AS
SELECT
    id,
    submission_id,
    problem_description,
    app_concept,
    core_functions,
    value_proposition,
    target_user,
    monetization_model,
    opportunity_score,
    title,
    subreddit,
    reddit_score,
    num_comments,
    created_at,
    status
FROM app_opportunities
WHERE opportunity_score > 40  -- High-value opportunities only
ORDER BY opportunity_score DESC, created_at DESC;

-- Add comment for documentation
COMMENT ON TABLE app_opportunities IS 'LLM-generated app opportunities from Reddit posts analyzed by Claude Haiku';
COMMENT ON VIEW top_opportunities IS 'High-scoring opportunities (score > 40) ranked by score and recency';
