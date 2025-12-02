-- Migration 7: Indexes for Performance Optimization
-- Created: 2025-11-04 19:00:06
-- Description: Creates all performance indexes, full-text search GIN indexes, and foreign key indexes
-- Focus: Optimized for large Reddit datasets and analytical queries

-- ============================================================================
-- Foreign Key Indexes for JOIN Performance
-- ============================================================================

-- Submissions foreign key indexes
CREATE INDEX IF NOT EXISTS idx_submissions_subreddit_fkey ON submissions(subreddit_id);
CREATE INDEX IF NOT EXISTS idx_submissions_redditor_fkey ON submissions(redditor_id);

-- Comments foreign key indexes
CREATE INDEX IF NOT EXISTS idx_comments_submission_fkey ON comments(submission_id);
CREATE INDEX IF NOT EXISTS idx_comments_redditor_fkey ON comments(redditor_id);
CREATE INDEX IF NOT EXISTS idx_comments_parent_fkey ON comments(parent_comment_id);

-- Opportunities foreign key indexes
CREATE INDEX IF NOT EXISTS idx_opportunities_submission_fkey ON opportunities(identified_from_submission_id);

-- All opportunity_id foreign key indexes (for JOIN performance)
CREATE INDEX IF NOT EXISTS idx_opportunity_scores_opportunity_fkey ON opportunity_scores(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_score_components_opportunity_fkey ON score_components(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_market_validations_opportunity_fkey ON market_validations(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_cross_platform_opportunity_fkey ON cross_platform_verification(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_competitive_landscape_opportunity_fkey ON competitive_landscape(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_feature_gaps_opportunity_fkey ON feature_gaps(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_monetization_patterns_opportunity_fkey ON monetization_patterns(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_user_willingness_opportunity_fkey ON user_willingness_to_pay(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_technical_assessments_opportunity_fkey ON technical_assessments(opportunity_id);

-- User willingness to pay source comment index
CREATE INDEX IF NOT EXISTS idx_user_willingness_source_comment ON user_willingness_to_pay(source_comment_id);

-- ============================================================================
-- Temporal Performance Indexes (Time-Series Queries)
-- ============================================================================

-- Submissions temporal indexes
CREATE INDEX IF NOT EXISTS idx_submissions_created_at_desc ON submissions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_submissions_sentiment_idx ON submissions(sentiment_score);

-- Comments temporal indexes
CREATE INDEX IF NOT EXISTS idx_comments_created_at_desc ON comments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_comments_depth_idx ON comments(comment_depth);

-- Opportunities temporal indexes
CREATE INDEX IF NOT EXISTS idx_opportunities_last_reviewed ON opportunities(last_reviewed_at DESC);

-- ============================================================================
-- Full-Text Search GIN Indexes
-- ============================================================================

-- Submissions full-text search
CREATE INDEX IF NOT EXISTS idx_submissions_problem_keywords_gin ON submissions USING gin(to_tsvector('english', problem_keywords));
CREATE INDEX IF NOT EXISTS idx_submissions_solution_mentions_gin ON submissions USING gin(to_tsvector('english', solution_mentions));

-- Score components evidence search
CREATE INDEX IF NOT EXISTS idx_score_components_evidence_gin_full ON score_components USING gin(to_tsvector('english', evidence_text));

-- Market validations notes search
CREATE INDEX IF NOT EXISTS idx_market_validations_notes_gin ON market_validations USING gin(to_tsvector('english', notes));

-- Competitive landscape text search
CREATE INDEX IF NOT EXISTS idx_competitive_market_position_gin ON competitive_landscape USING gin(to_tsvector('english', market_position));
CREATE INDEX IF NOT EXISTS idx_competitive_strengths_gin_full ON competitive_landscape USING gin(to_tsvector('english', strengths));
CREATE INDEX IF NOT EXISTS idx_competitive_weaknesses_gin_full ON competitive_landscape USING gin(to_tsvector('english', weaknesses));

-- Feature gaps evidence search
CREATE INDEX IF NOT EXISTS idx_feature_gaps_user_evidence_gin ON feature_gaps USING gin(to_tsvector('english', user_evidence));

-- Monetization patterns evidence search
CREATE INDEX IF NOT EXISTS idx_monetization_pricing_evidence_gin ON monetization_patterns USING gin(to_tsvector('english', pricing_evidence));

-- User willingness context search
CREATE INDEX IF NOT EXISTS idx_willingness_context_gin_full ON user_willingness_to_pay USING gin(to_tsvector('english', user_context));

-- Technical assessments text search
CREATE INDEX IF NOT EXISTS idx_technical_api_requirements_gin ON technical_assessments USING gin(to_tsvector('english', api_integrations_required));
CREATE INDEX IF NOT EXISTS idx_technical_regulatory_gin ON technical_assessments USING gin(to_tsvector('english', regulatory_considerations));
CREATE INDEX IF NOT EXISTS idx_technical_resources_gin ON technical_assessments USING gin(to_tsvector('english', resource_requirements));
CREATE INDEX IF NOT EXISTS idx_technical_risk_factors_gin_full ON technical_assessments USING gin(to_tsvector('english', risk_factors));
CREATE INDEX IF NOT EXISTS idx_technical_notes_gin ON technical_assessments USING gin(to_tsvector('english', technical_notes));

-- ============================================================================
-- Composite Indexes for Analytical Queries
-- ============================================================================

-- Top opportunities by score and market segment

-- Opportunity status and simplicity constraint (for filtering)

-- Comments by submission and depth (for thread analysis)
CREATE INDEX IF NOT EXISTS idx_comments_submission_depth ON comments(submission_id, comment_depth, created_at DESC);

-- Feature gaps by priority and request count
CREATE INDEX IF NOT EXISTS idx_feature_gaps_priority_requests ON feature_gaps(priority_level, user_requests_count DESC)
    INCLUDE (existing_solution, missing_feature);

-- Monetization patterns by model type and revenue
CREATE INDEX IF NOT EXISTS idx_monetization_type_revenue ON monetization_patterns(model_type, revenue_estimate DESC)
    INCLUDE (price_range_min, price_range_max);

-- ============================================================================
-- Specialized Search Indexes
-- ============================================================================

-- Submissions by engagement (upvotes/comments ratio)
CREATE INDEX IF NOT EXISTS idx_submissions_engagement_ratio ON submissions(upvotes DESC, comments_count DESC);

-- Score components by metric and confidence
CREATE INDEX IF NOT EXISTS idx_score_components_metric_confidence ON score_components(metric_name, confidence_level DESC)
    INCLUDE (metric_value, calculated_at);

-- Market validations by type and confidence
CREATE INDEX IF NOT EXISTS idx_market_validations_type_confidence ON market_validations(validation_type, confidence_score DESC)
    INCLUDE (validation_result, validation_date);

-- Cross-platform by platform and status
CREATE INDEX IF NOT EXISTS idx_cross_platform_platform_status ON cross_platform_verification(platform_name, validation_status, confidence_score DESC);

-- Competitive landscape by market share and verification
CREATE INDEX IF NOT EXISTS idx_competitive_market_share_verification ON competitive_landscape(market_share_estimate DESC, verification_status);

-- Technical assessments by complexity and feasibility
CREATE INDEX IF NOT EXISTS idx_technical_complexity_feasibility ON technical_assessments(development_complexity, feasibility_score DESC)
    INCLUDE (estimated_timeline, assessed_at);

-- ============================================================================
-- Unique Constraints for Data Integrity
-- ============================================================================

-- Ensure unique competitor per opportunity
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'competitive_landscape') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'competitive_landscape_opportunity_competitor_unique') THEN
            ALTER TABLE competitive_landscape ADD CONSTRAINT competitive_landscape_opportunity_competitor_unique
                UNIQUE (opportunity_id, competitor_name);
        END IF;
    END IF;

    -- Ensure unique score version per opportunity
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'opportunity_scores') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'opportunity_scores_opportunity_version_unique') THEN
            ALTER TABLE opportunity_scores ADD CONSTRAINT opportunity_scores_opportunity_version_unique
                UNIQUE (opportunity_id, score_version);
        END IF;
    END IF;

    -- Ensure unique metric per opportunity
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'score_components') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'score_components_opportunity_metric_unique') THEN
            ALTER TABLE score_components ADD CONSTRAINT score_components_opportunity_metric_unique
                UNIQUE (opportunity_id, metric_name, calculated_at);
        END IF;
    END IF;

    -- Ensure unique platform verification per opportunity
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'cross_platform_verification') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'cross_platform_opportunity_platform_unique') THEN
            ALTER TABLE cross_platform_verification ADD CONSTRAINT cross_platform_opportunity_platform_unique
                UNIQUE (opportunity_id, platform_name);
        END IF;
    END IF;
END $$;

-- Migration completed
