-- Workflow Results Table
-- Simple table to store processed workflow analysis results

CREATE TABLE IF NOT EXISTS workflow_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  opportunity_id VARCHAR(255) UNIQUE NOT NULL,
  app_name VARCHAR(255) NOT NULL,
  function_count INTEGER NOT NULL,
  function_list TEXT[] DEFAULT '{}',
  original_score FLOAT NOT NULL,
  final_score FLOAT NOT NULL,
  status VARCHAR(50) NOT NULL,
  constraint_applied BOOLEAN DEFAULT false,
  ai_insight TEXT,
  processed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_workflow_results_status ON workflow_results(status);
CREATE INDEX idx_workflow_results_final_score ON workflow_results(final_score DESC);
CREATE INDEX idx_workflow_results_processed_at ON workflow_results(processed_at DESC);
