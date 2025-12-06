-- SQL script to verify agent-level metrics tracking
-- Use this to check that all 5 agents are tracking metrics properly

-- Check recent metrics for all agents
SELECT
    agent_name,
    COUNT(*) as execution_count,
    MAX(created_at) as last_execution,
    MIN(created_at) as first_execution,
    AVG(duration_seconds) as avg_duration_seconds
FROM pipeline_metrics
WHERE created_at >= NOW() - INTERVAL '24 hours'
  AND phase = 'transform'
  AND agent_name IS NOT NULL
GROUP BY agent_name
ORDER BY agent_name;

-- Expected result should show:
-- wtp, segment, price, payment, market

-- Check for NULL agent_name records (should be 0)
SELECT
    COUNT(*) as null_agent_name_count
FROM pipeline_metrics
WHERE created_at >= NOW() - INTERVAL '24 hours'
  AND phase = 'transform'
  AND agent_name IS NULL;

-- Check for unique agent names in last 24 hours
SELECT
    COUNT(DISTINCT agent_name) as unique_agent_count,
    array_agg(DISTINCT agent_name ORDER BY agent_name) as agent_names
FROM pipeline_metrics
WHERE created_at >= NOW() - INTERVAL '24 hours'
  AND phase = 'transform'
  AND agent_name IS NOT NULL;

-- Expected result should show:
-- unique_agent_count = 5
-- agent_names = {market, payment, price, segment, wtp}

-- Verify all expected agents are present
WITH expected_agents AS (
    SELECT unnest(ARRAY['wtp', 'segment', 'price', 'payment', 'market']) as agent_name
),
actual_agents AS (
    SELECT DISTINCT agent_name
    FROM pipeline_metrics
    WHERE created_at >= NOW() - INTERVAL '24 hours'
      AND phase = 'transform'
      AND agent_name IS NOT NULL
)
SELECT
    e.agent_name as expected_agent,
    CASE WHEN a.agent_name IS NOT NULL THEN 'FOUND' ELSE 'MISSING' END as status
FROM expected_agents e
LEFT JOIN actual_agents a ON e.agent_name = a.agent_name
ORDER BY e.agent_name;