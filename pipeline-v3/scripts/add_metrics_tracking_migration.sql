-- Migration: Add pipeline_metrics table for live test tracking
-- Created: 2025-12-05
-- Purpose: Track detailed metrics during Phase 1-3 live testing

-- Create pipeline_metrics table
CREATE TABLE IF NOT EXISTS pipeline_metrics (
    id SERIAL PRIMARY KEY,
    opportunity_id TEXT,
    phase TEXT CHECK (phase IN ('extract', 'transform', 'load', 'end_to_end')),
    agent_name TEXT CHECK (agent_name IN ('wtp', 'segment', 'price', 'payment', 'market', 'consensus', 'all')),
    duration_seconds FLOAT,
    api_cost_usd FLOAT,
    success BOOLEAN,
    error_message TEXT,
    metadata JSONB,  -- For additional context (model name, tokens, etc.)
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_opportunity_id ON pipeline_metrics(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_phase ON pipeline_metrics(phase);
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_agent_name ON pipeline_metrics(agent_name);
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_created_at ON pipeline_metrics(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pipeline_metrics_success ON pipeline_metrics(success);

-- Create view for quick phase summaries
CREATE OR REPLACE VIEW pipeline_phase_summary AS
SELECT
    phase,
    COUNT(*) as total_executions,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_executions,
    ROUND(AVG(duration_seconds)::numeric, 3) as avg_duration_seconds,
    ROUND(SUM(api_cost_usd)::numeric, 6) as total_cost_usd,
    ROUND(AVG(api_cost_usd)::numeric, 6) as avg_cost_usd,
    MAX(created_at) as last_execution
FROM pipeline_metrics
GROUP BY phase;

-- Create view for agent performance
CREATE OR REPLACE VIEW agent_performance_summary AS
SELECT
    agent_name,
    COUNT(*) as total_executions,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_executions,
    ROUND((SUM(CASE WHEN success THEN 1 ELSE 0 END)::float / COUNT(*)::float * 100)::numeric, 2) as success_rate_pct,
    ROUND(AVG(duration_seconds)::numeric, 3) as avg_duration_seconds,
    ROUND(SUM(api_cost_usd)::numeric, 6) as total_cost_usd,
    ROUND(AVG(api_cost_usd)::numeric, 6) as avg_cost_usd
FROM pipeline_metrics
WHERE agent_name IS NOT NULL
GROUP BY agent_name
ORDER BY total_cost_usd DESC;

-- Create view for cost analysis
CREATE OR REPLACE VIEW cost_analysis AS
SELECT
    DATE(created_at) as date,
    COUNT(DISTINCT opportunity_id) as opportunities_processed,
    ROUND(SUM(api_cost_usd)::numeric, 6) as total_cost_usd,
    ROUND(AVG(api_cost_usd)::numeric, 6) as avg_cost_per_metric,
    ROUND((SUM(api_cost_usd) / NULLIF(COUNT(DISTINCT opportunity_id), 0))::numeric, 6) as cost_per_opportunity
FROM pipeline_metrics
WHERE opportunity_id IS NOT NULL
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Grant permissions (adjust role as needed)
-- GRANT SELECT, INSERT ON pipeline_metrics TO your_app_role;
-- GRANT SELECT ON pipeline_phase_summary TO your_app_role;
-- GRANT SELECT ON agent_performance_summary TO your_app_role;
-- GRANT SELECT ON cost_analysis TO your_app_role;

-- Verification queries
COMMENT ON TABLE pipeline_metrics IS 'Tracks detailed execution metrics for Pipeline v3 live testing';
COMMENT ON COLUMN pipeline_metrics.phase IS 'Pipeline phase: extract, transform, load, or end_to_end';
COMMENT ON COLUMN pipeline_metrics.agent_name IS 'Agent name: wtp, segment, price, payment, market, consensus, or all';
COMMENT ON COLUMN pipeline_metrics.metadata IS 'Additional context: {model_name, tokens_used, jina_api_success, etc.}';

SELECT 'Pipeline metrics tracking migration completed successfully!' as status;
