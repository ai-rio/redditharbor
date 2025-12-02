-- LLM Monetization Analysis Tracking Table (Option A Enhancement)
-- Tracks which opportunities received LLM monetization analysis
-- Allows A/B testing: keyword-based scoring vs LLM-based scoring

-- ============================================================================
-- LLM MONETIZATION ANALYSIS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS llm_monetization_analysis (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  opportunity_id VARCHAR(255) NOT NULL,
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
  analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Comparison
  score_delta DECIMAL(6,2), -- llm_score - keyword_score (for A/B testing)

  CONSTRAINT unique_opportunity_analysis UNIQUE(opportunity_id)
);

-- Indexes for performance
CREATE INDEX idx_llm_analysis_opportunity ON llm_monetization_analysis(opportunity_id);
CREATE INDEX idx_llm_analysis_submission ON llm_monetization_analysis(submission_id);
CREATE INDEX idx_llm_analysis_segment ON llm_monetization_analysis(customer_segment);
CREATE INDEX idx_llm_analysis_llm_score ON llm_monetization_analysis(llm_monetization_score DESC);
CREATE INDEX idx_llm_analysis_score_delta ON llm_monetization_analysis(score_delta DESC);
CREATE INDEX idx_llm_analysis_analyzed_at ON llm_monetization_analysis(analyzed_at DESC);

-- ============================================================================
-- USEFUL VIEWS
-- ============================================================================

-- Monetization Scoring Comparison (LLM vs Keyword)
CREATE OR REPLACE VIEW monetization_scoring_comparison AS
SELECT
  opportunity_id,
  keyword_monetization_score,
  llm_monetization_score,
  score_delta,
  customer_segment,
  payment_sentiment,
  urgency_level,
  confidence,
  CASE
    WHEN ABS(score_delta) <= 10 THEN 'Similar'
    WHEN score_delta > 10 THEN 'LLM Higher'
    WHEN score_delta < -10 THEN 'Keyword Higher'
  END as score_comparison,
  analyzed_at
FROM llm_monetization_analysis
ORDER BY ABS(score_delta) DESC;

-- High Monetization Opportunities (LLM-validated)
CREATE OR REPLACE VIEW high_monetization_opportunities AS
SELECT
  lma.opportunity_id,
  lma.llm_monetization_score,
  lma.customer_segment,
  lma.willingness_to_pay_score,
  lma.payment_sentiment,
  lma.urgency_level,
  lma.mentioned_price_points,
  lma.confidence,
  lma.analyzed_at
FROM llm_monetization_analysis lma
WHERE
  lma.llm_monetization_score >= 70
  AND lma.confidence >= 0.6
  AND lma.customer_segment IN ('B2B', 'Mixed')
ORDER BY lma.llm_monetization_score DESC;

-- LLM Analysis Cost Tracking
CREATE OR REPLACE VIEW llm_analysis_cost_stats AS
SELECT
  DATE_TRUNC('day', analyzed_at) as date,
  COUNT(*) as analyses_performed,
  SUM(cost_usd) as total_cost_usd,
  AVG(cost_usd) as avg_cost_per_analysis,
  SUM(tokens_used) as total_tokens,
  AVG(latency_ms) as avg_latency_ms,
  model_used
FROM llm_monetization_analysis
WHERE analyzed_at IS NOT NULL
GROUP BY DATE_TRUNC('day', analyzed_at), model_used
ORDER BY date DESC;

-- B2B vs B2C Segment Performance
CREATE OR REPLACE VIEW segment_performance AS
SELECT
  customer_segment,
  COUNT(*) as opportunity_count,
  AVG(llm_monetization_score) as avg_llm_score,
  AVG(keyword_monetization_score) as avg_keyword_score,
  AVG(willingness_to_pay_score) as avg_wtp_score,
  AVG(revenue_potential_score) as avg_revenue_potential,
  COUNT(CASE WHEN payment_sentiment = 'Positive' THEN 1 END) as positive_sentiment_count,
  COUNT(CASE WHEN urgency_level IN ('High', 'Critical') THEN 1 END) as high_urgency_count
FROM llm_monetization_analysis
GROUP BY customer_segment
ORDER BY avg_llm_score DESC;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE llm_monetization_analysis IS 'LLM-powered monetization analysis results for Option A enhancement';
COMMENT ON COLUMN llm_monetization_analysis.opportunity_id IS 'Links to workflow_results.opportunity_id';
COMMENT ON COLUMN llm_monetization_analysis.score_delta IS 'Difference between LLM and keyword scores (for A/B testing)';
COMMENT ON COLUMN llm_monetization_analysis.customer_segment IS 'B2B (35% weight), B2C (15% weight), Mixed (25% weight)';
COMMENT ON COLUMN llm_monetization_analysis.payment_friction_indicators IS 'Extracted friction signals (subscription_fatigue, price_objection, etc.)';
COMMENT ON COLUMN llm_monetization_analysis.subreddit_multiplier IS 'Purchasing power multiplier (r/entrepreneur=1.5x, r/frugal=0.6x)';

-- ============================================================================
-- SAMPLE QUERY EXAMPLES
-- ============================================================================

-- Find opportunities where LLM scored significantly different from keywords
-- SELECT * FROM monetization_scoring_comparison
-- WHERE ABS(score_delta) > 20
-- ORDER BY ABS(score_delta) DESC
-- LIMIT 20;

-- Calculate ROI: Cost vs Value of LLM analysis
-- SELECT
--   COUNT(*) as total_analyses,
--   SUM(cost_usd) as total_cost,
--   COUNT(CASE WHEN llm_monetization_score >= 70 THEN 1 END) as high_quality_opps,
--   SUM(cost_usd) / NULLIF(COUNT(CASE WHEN llm_monetization_score >= 70 THEN 1 END), 0) as cost_per_quality_opp
-- FROM llm_monetization_analysis;

-- Find false positives caught by LLM (keyword high, LLM low)
-- SELECT * FROM monetization_scoring_comparison
-- WHERE keyword_monetization_score >= 70
--   AND llm_monetization_score < 50
-- ORDER BY (keyword_monetization_score - llm_monetization_score) DESC;

-- Get B2B opportunities with high revenue potential
-- SELECT * FROM high_monetization_opportunities
-- WHERE customer_segment = 'B2B'
--   AND revenue_potential_score >= 75
-- ORDER BY llm_monetization_score DESC;
