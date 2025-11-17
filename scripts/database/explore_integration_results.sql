-- RedditHarbor Integration Results Explorer
-- Generated: 2025-11-17
-- Purpose: Explore the results of the major integration effort (Agno, AgentOps, Jina)

-- =============================================================================
-- SECTION 1: DATA VOLUME & OVERVIEW
-- =============================================================================

-- Overall data status across all integration tables
SELECT
    'Total Submissions' as metric,
    COUNT(*) as count,
    'All Reddit posts collected' as description
FROM submissions
UNION ALL
SELECT
    'Total Comments',
    COUNT(*),
    'All Reddit comments collected'
FROM comments
UNION ALL
SELECT
    'Total Opportunities',
    COUNT(*),
    'App opportunities identified'
FROM app_opportunities
UNION ALL
SELECT
    'Trust Layer Records',
    COUNT(*),
    'Trust scoring completed'
FROM app_opportunities_trust
UNION ALL
SELECT
    'LLM Monetization Analysis',
    COUNT(*),
    'Monetization potential analyzed'
FROM llm_monetization_analysis;

-- =============================================================================
-- SECTION 2: TRUST LAYER ANALYSIS
-- =============================================================================

-- Trust score distribution
SELECT
    trust_score,
    COUNT(*) as frequency,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM app_opportunities_trust
WHERE trust_score IS NOT NULL
GROUP BY trust_score
ORDER BY trust_score DESC;

-- Trust badge distribution
SELECT
    trust_badge,
    COUNT(*) as count,
    ROUND(AVG(trust_score), 2) as avg_trust_score
FROM app_opportunities_trust
WHERE trust_badge IS NOT NULL
GROUP BY trust_badge
ORDER BY
    CASE trust_badge
        WHEN 'GOLD' THEN 1
        WHEN 'SILVER' THEN 2
        WHEN 'BRONZE' THEN 3
        WHEN 'BASIC' THEN 4
        ELSE 5
    END;

-- Engagement vs Trust correlation
SELECT
    engagement_level,
    COUNT(*) as count,
    ROUND(AVG(trust_score), 2) as avg_trust_score,
    ROUND(AVG(opportunity_score__v_double), 2) as avg_opportunity_score
FROM app_opportunities_trust
WHERE engagement_level IS NOT NULL
GROUP BY engagement_level
ORDER BY
    CASE engagement_level
        WHEN 'VERY_HIGH' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        WHEN 'LOW' THEN 4
        WHEN 'MINIMAL' THEN 5
    END;

-- =============================================================================
-- SECTION 3: OPPORTUNITY SCORING ANALYSIS
-- =============================================================================

-- Top scoring opportunities by subreddit
SELECT
    subreddit,
    COUNT(*) as opportunity_count,
    ROUND(AVG(opportunity_score__v_double), 2) as avg_score,
    MAX(opportunity_score__v_double) as max_score,
    ROUND(AVG(trust_score), 2) as avg_trust_score
FROM app_opportunities_trust
WHERE subreddit IS NOT NULL AND opportunity_score__v_double > 0
GROUP BY subreddit
HAVING COUNT(*) >= 2
ORDER BY avg_score DESC
LIMIT 10;

-- Problem validity distribution
SELECT
    problem_validity,
    COUNT(*) as count,
    ROUND(AVG(opportunity_score__v_double), 2) as avg_opportunity_score,
    ROUND(AVG(trust_score), 2) as avg_trust_score
FROM app_opportunities_trust
WHERE problem_validity IS NOT NULL
GROUP BY problem_validity
ORDER BY
    CASE problem_validity
        WHEN 'VALID' THEN 1
        WHEN 'POTENTIAL' THEN 2
        WHEN 'UNCLEAR' THEN 3
        WHEN 'INVALID' THEN 4
    END;

-- =============================================================================
-- SECTION 4: MARKET VALIDATION INTEGRATION (if available)
-- =============================================================================

-- Market validation overview
SELECT
    COUNT(*) as total_opportunities,
    COUNT(market_validation_score) as market_validated,
    ROUND(AVG(market_validation_score), 2) as avg_market_score,
    ROUND(AVG(market_data_quality_score), 2) as avg_data_quality,
    SUM(market_validation_cost_usd) as total_validation_cost
FROM app_opportunities;

-- Market size analysis
SELECT
    market_size_tam,
    COUNT(*) as count,
    ROUND(AVG(market_validation_score), 2) as avg_validation_score,
    ROUND(AVG(opportunity_score), 2) as avg_opportunity_score
FROM app_opportunities
WHERE market_size_tam IS NOT NULL
GROUP BY market_size_tam
ORDER BY count DESC;

-- =============================================================================
-- SECTION 5: INTEGRATION PERFORMANCE METRICS
-- =============================================================================

-- LLM Analysis performance (if data exists)
SELECT
    model_used,
    COUNT(*) as analysis_count,
    ROUND(AVG(llm_monetization_score), 2) as avg_score,
    ROUND(AVG(confidence), 2) as avg_confidence,
    SUM(cost_usd) as total_cost,
    ROUND(AVG(latency_ms), 0) as avg_latency_ms
FROM llm_monetization_analysis
GROUP BY model_used
ORDER BY analysis_count DESC;

-- Cost efficiency analysis
SELECT
    'Opportunity Discovery' as activity,
    COUNT(*) as count,
    COALESCE(SUM(cost_usd), 0) as total_cost_usd,
    CASE WHEN COUNT(*) > 0 THEN COALESCE(ROUND(SUM(cost_usd) / COUNT(*), 4), 0) ELSE 0 END as cost_per_opportunity
FROM app_opportunities
UNION ALL
SELECT
    'Trust Layer Analysis',
    COUNT(*),
    0, -- Trust layer doesn't track cost in current schema
    0
FROM app_opportunities_trust
UNION ALL
SELECT
    'LLM Monetization Analysis',
    COUNT(*),
    COALESCE(SUM(cost_usd), 0),
    CASE WHEN COUNT(*) > 0 THEN COALESCE(ROUND(SUM(cost_usd) / COUNT(*), 4), 0) ELSE 0 END
FROM llm_monetization_analysis;

-- =============================================================================
-- SECTION 6: INTEGRATION SUCCESS METRICS
-- =============================================================================

-- Integration pipeline success rates
SELECT
    stage,
    total_processed,
    successful,
    ROUND(successful * 100.0 / total_processed, 2) as success_rate
FROM (
    SELECT
        'Reddit Data Collection' as stage,
        COUNT(*) as total_processed,
        COUNT(CASE WHEN created_at IS NOT NULL THEN 1 END) as successful
    FROM submissions
    UNION ALL
    SELECT
        'Opportunity Identification',
        COUNT(*) as total_processed,
        COUNT(CASE WHEN opportunity_score__v_double > 0 THEN 1 END) as successful
    FROM app_opportunities_trust
    UNION ALL
    SELECT
        'Trust Scoring',
        COUNT(*) as total_processed,
        COUNT(CASE WHEN trust_score > 0 THEN 1 END) as successful
    FROM app_opportunities_trust
    WHERE trust_score IS NOT NULL
) pipeline_stats;

-- Cross-platform verification status
SELECT
    COUNT(*) as total_opportunities,
    COUNT(market_similar_launches) as with_competitor_analysis,
    COUNT(market_validation_timestamp) as with_timestamp_validation,
    ROUND(AVG(market_similar_launches), 1) as avg_similar_launches
FROM app_opportunities;

-- =============================================================================
-- SECTION 7: QUALITY ASSURANCE QUERIES
-- =============================================================================

-- Data quality checks
SELECT
    'Submissions with scores' as quality_metric,
    COUNT(*) as total,
    COUNT(CASE WHEN reddit_score > 0 THEN 1 END) as with_scores,
    ROUND(COUNT(CASE WHEN reddit_score > 0 THEN 1 END) * 100.0 / COUNT(*), 2) as completion_rate
FROM submissions
WHERE reddit_score IS NOT NULL
UNION ALL
SELECT
    'Opportunities with trust data',
    COUNT(*),
    COUNT(CASE WHEN trust_score IS NOT NULL THEN 1 END),
    ROUND(COUNT(CASE WHEN trust_score IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 2)
FROM app_opportunities_trust
UNION ALL
SELECT
    'Trust records with confidence',
    COUNT(*),
    COUNT(CASE WHEN confidence_score > 0 THEN 1 END),
    ROUND(COUNT(CASE WHEN confidence_score > 0 THEN 1 END) * 100.0 / COUNT(*), 2)
FROM app_opportunities_trust
WHERE confidence_score IS NOT NULL;

-- =============================================================================
-- SECTION 8: BUSINESS INSIGHTS
-- =============================================================================

-- High-value opportunity identification
SELECT
    'High Value' as segment,
    COUNT(*) as count,
    ROUND(AVG(opportunity_score__v_double), 2) as avg_score,
    ROUND(AVG(trust_score), 2) as avg_trust,
    STRING_AGG(DISTINCT subreddit, ', ') as top_subreddits
FROM app_opportunities_trust
WHERE opportunity_score__v_double >= 70 AND trust_score >= 70
UNION ALL
SELECT
    'Medium Value',
    COUNT(*),
    ROUND(AVG(opportunity_score__v_double), 2),
    ROUND(AVG(trust_score), 2),
    STRING_AGG(DISTINCT subreddit, ', ')
FROM app_opportunities_trust
WHERE opportunity_score__v_double BETWEEN 40 AND 69 AND trust_score BETWEEN 40 AND 69
UNION ALL
SELECT
    'Low Value',
    COUNT(*),
    ROUND(AVG(opportunity_score__v_double), 2),
    ROUND(AVG(trust_score), 2),
    STRING_AGG(DISTINCT subreddit, ', ')
FROM app_opportunities_trust
WHERE opportunity_score__v_double < 40 OR trust_score < 40;

-- =============================================================================
-- SECTION 9: INTEGRATION TIMELINE
-- =============================================================================

-- Analysis timeline (for recent activity)
SELECT
    DATE_TRUNC('day', created_at) as analysis_date,
    COUNT(*) as opportunities_analyzed
FROM app_opportunities
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY analysis_date DESC;

-- Trust validation recency
SELECT
    CASE
        WHEN trust_validation_timestamp > EXTRACT(EPOCH FROM NOW()) - 86400 THEN 'Last 24h'
        WHEN trust_validation_timestamp > EXTRACT(EPOCH FROM NOW()) - 604800 THEN 'Last 7d'
        WHEN trust_validation_timestamp > EXTRACT(EPOCH FROM NOW()) - 2592000 THEN 'Last 30d'
        ELSE 'Older'
    END as validation_period,
    COUNT(*) as count,
    ROUND(AVG(trust_score), 2) as avg_trust_score
FROM app_opportunities_trust
WHERE trust_validation_timestamp IS NOT NULL
GROUP BY
    CASE
        WHEN trust_validation_timestamp > EXTRACT(EPOCH FROM NOW()) - 86400 THEN 'Last 24h'
        WHEN trust_validation_timestamp > EXTRACT(EPOCH FROM NOW()) - 604800 THEN 'Last 7d'
        WHEN trust_validation_timestamp > EXTRACT(EPOCH FROM NOW()) - 2592000 THEN 'Last 30d'
        ELSE 'Older'
    END
ORDER BY
    CASE
        WHEN trust_validation_timestamp > EXTRACT(EPOCH FROM NOW()) - 86400 THEN 1
        WHEN trust_validation_timestamp > EXTRACT(EPOCH FROM NOW()) - 604800 THEN 2
        WHEN trust_validation_timestamp > EXTRACT(EPOCH FROM NOW()) - 2592000 THEN 3
        ELSE 4
    END;

-- =============================================================================
-- SECTION 10: RECOMMENDATIONS
-- =============================================================================

-- These queries provide insights for next steps:

-- 1. Identify high-trust, high-scoring opportunities for immediate follow-up
-- 2. Analyze subreddit performance patterns for focused collection
-- 3. Evaluate cost-effectiveness of LLM analysis pipeline
-- 4. Assess trust layer calibration accuracy
-- 5. Monitor data quality and completion rates

-- End of Integration Results Explorer