-- Add LLM Cost Tracking Columns to workflow_results table
-- Migration for comprehensive cost tracking and budget management
-- Created: 2025-11-13

-- Cost tracking columns for LLM operations
ALTER TABLE workflow_results
ADD COLUMN IF NOT EXISTS llm_model_used TEXT,
ADD COLUMN IF NOT EXISTS llm_provider TEXT DEFAULT 'openrouter',
ADD COLUMN IF NOT EXISTS llm_prompt_tokens INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS llm_completion_tokens INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS llm_total_tokens INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS llm_input_cost_usd DECIMAL(10,8) DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS llm_output_cost_usd DECIMAL(10,8) DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS llm_total_cost_usd DECIMAL(10,8) DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS llm_latency_seconds DECIMAL(8,3) DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS llm_timestamp TIMESTAMPTZ;

-- Additional cost tracking metadata
ALTER TABLE workflow_results
ADD COLUMN IF NOT EXISTS llm_pricing_info JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS cost_tracking_enabled BOOLEAN DEFAULT false;

-- Create indexes for cost analysis queries
CREATE INDEX IF NOT EXISTS idx_workflow_results_llm_model ON workflow_results(llm_model_used);
CREATE INDEX IF NOT EXISTS idx_workflow_results_llm_cost ON workflow_results(llm_total_cost_usd DESC);
CREATE INDEX IF NOT EXISTS idx_workflow_results_llm_timestamp ON workflow_results(llm_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_workflow_results_cost_tracking ON workflow_results(cost_tracking_enabled);

-- Add composite index for cost analysis
CREATE INDEX IF NOT EXISTS idx_workflow_results_cost_composite ON workflow_results(llm_model_used, llm_total_cost_usd, llm_timestamp);

-- Add documentation comments
COMMENT ON COLUMN workflow_results.llm_model_used IS 'LLM model used for AI profile generation (e.g., claude-haiku-4.5, gpt-4o-mini)';
COMMENT ON COLUMN workflow_results.llm_provider IS 'LLM provider (openrouter, openai, anthropic, etc.)';
COMMENT ON COLUMN workflow_results.llm_prompt_tokens IS 'Number of input tokens sent to LLM';
COMMENT ON COLUMN workflow_results.llm_completion_tokens IS 'Number of output tokens received from LLM';
COMMENT ON COLUMN workflow_results.llm_total_tokens IS 'Total tokens used in LLM transaction';
COMMENT ON COLUMN workflow_results.llm_input_cost_usd IS 'Cost for input tokens in USD';
COMMENT ON COLUMN workflow_results.llm_output_cost_usd IS 'Cost for output tokens in USD';
COMMENT ON COLUMN workflow_results.llm_total_cost_usd IS 'Total cost for LLM transaction in USD';
COMMENT ON COLUMN workflow_results.llm_latency_seconds IS 'LLM response time in seconds';
COMMENT ON COLUMN workflow_results.llm_timestamp IS 'Timestamp when LLM call was made';
COMMENT ON COLUMN workflow_results.llm_pricing_info IS 'JSON with pricing details (cost per 1M tokens, etc.)';
COMMENT ON COLUMN workflow_results.cost_tracking_enabled IS 'Flag indicating if cost tracking is enabled for this record';

-- Add check constraints for data integrity
ALTER TABLE workflow_results
ADD CONSTRAINT IF NOT EXISTS check_llm_tokens_non_negative
    CHECK (llm_prompt_tokens >= 0 AND llm_completion_tokens >= 0 AND llm_total_tokens >= 0);

ALTER TABLE workflow_results
ADD CONSTRAINT IF NOT EXISTS check_llm_costs_non_negative
    CHECK (llm_input_cost_usd >= 0 AND llm_output_cost_usd >= 0 AND llm_total_cost_usd >= 0);

ALTER TABLE workflow_results
ADD CONSTRAINT IF NOT EXISTS check_llm_latency_non_negative
    CHECK (llm_latency_seconds >= 0);