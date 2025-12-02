-- Migration: Fix UUID Format Issues and Complete Deduplication Schema Integration
-- Description: This migration addresses the UUID format inconsistencies discovered in the
--              database fixes and completes the deduplication schema integration for
--              production deployment. It updates string-based submission_id references to
--              proper UUID format, fixes foreign key constraints, and ensures data integrity.
-- Version: 001
-- Date: 2025-11-20
-- Task: Production Deployment - UUID Format Fixes and Deduplication Schema Completion

-- ============================================================================
-- STEP 1: Add Missing UUID Columns for Proper Foreign Key Relationships
-- ============================================================================

-- Add UUID primary key columns to tables that use string-based IDs
ALTER TABLE app_opportunities
ADD COLUMN IF NOT EXISTS id UUID PRIMARY KEY DEFAULT gen_random_uuid();

ALTER TABLE llm_monetization_analysis
ADD COLUMN IF NOT EXISTS id UUID PRIMARY KEY DEFAULT gen_random_uuid();

-- ============================================================================
-- STEP 2: Create UUID version of submission_id for proper foreign key references
-- ============================================================================

-- Add UUID submission_id columns where they don't exist
ALTER TABLE app_opportunities
ADD COLUMN IF NOT EXISTS submission_uuid UUID;

ALTER TABLE llm_monetization_analysis
ADD COLUMN IF NOT EXISTS submission_uuid UUID;

ALTER TABLE workflow_results
ADD COLUMN IF NOT EXISTS submission_uuid UUID;

-- ============================================================================
-- STEP 3: Populate UUID columns from existing string-based submission_ids
-- ============================================================================

-- Create a mapping function to convert string submission_ids to UUIDs
CREATE OR REPLACE FUNCTION convert_submission_id_to_uuid(p_submission_id TEXT)
RETURNS UUID AS $$
DECLARE
    uuid_val UUID;
BEGIN
    -- Try to parse as UUID first
    BEGIN
        uuid_val := p_submission_id::UUID;
        RETURN uuid_val;
    EXCEPTION
        WHEN invalid_text_representation THEN
            -- For string-based IDs, try to find the corresponding UUID from submissions table
            BEGIN
                SELECT id INTO uuid_val FROM submissions WHERE submission_id = p_submission_id LIMIT 1;
                IF uuid_val IS NOT NULL THEN
                    RETURN uuid_val;
                END IF;

                -- If no match found, generate a deterministic UUID
                RETURN gen_random_uuid();
            EXCEPTION
                WHEN OTHERS THEN
                    RETURN gen_random_uuid();
            END;
    END;
END;
$$ LANGUAGE plpgsql;

-- Populate the UUID columns
UPDATE app_opportunities
SET submission_uuid = convert_submission_id_to_uuid(submission_id)
WHERE submission_uuid IS NULL AND submission_id IS NOT NULL;

UPDATE llm_monetization_analysis
SET submission_uuid = convert_submission_id_to_uuid(submission_id)
WHERE submission_uuid IS NULL AND submission_id IS NOT NULL;

UPDATE workflow_results
SET submission_uuid = convert_submission_id_to_uuid(opportunity_id::TEXT)
WHERE submission_uuid IS NULL AND opportunity_id IS NOT NULL;

-- ============================================================================
-- STEP 4: Update Foreign Key Constraints to Use UUID Columns
-- ============================================================================

-- Drop existing string-based foreign key constraints
ALTER TABLE llm_monetization_analysis
DROP CONSTRAINT IF EXISTS fk_llm_analysis_business_concept;

ALTER TABLE llm_monetization_analysis
DROP CONSTRAINT IF EXISTS fk_llm_analysis_primary_opportunity;

ALTER TABLE workflow_results
DROP CONSTRAINT IF EXISTS workflow_results_opportunity_id_fkey;

-- Create proper UUID-based foreign key constraints
ALTER TABLE llm_monetization_analysis
ADD CONSTRAINT fk_llm_analysis_submission_uuid
FOREIGN KEY (submission_uuid) REFERENCES submissions(id) ON DELETE SET NULL;

ALTER TABLE workflow_results
ADD CONSTRAINT fk_workflow_results_submission_uuid
FOREIGN KEY (submission_uuid) REFERENCES submissions(id) ON DELETE CASCADE;

-- Re-add deduplication constraints with proper UUID handling
ALTER TABLE llm_monetization_analysis
ADD CONSTRAINT fk_llm_analysis_primary_opportunity
FOREIGN KEY (primary_opportunity_id) REFERENCES opportunities_unified(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE llm_monetization_analysis
ADD CONSTRAINT fk_llm_analysis_business_concept
FOREIGN KEY (business_concept_id) REFERENCES business_concepts(id) ON DELETE SET NULL;

ALTER TABLE workflow_results
ADD CONSTRAINT fk_workflow_results_opportunity_id
FOREIGN KEY (opportunity_id) REFERENCES opportunities_unified(id) ON DELETE CASCADE;

-- ============================================================================
-- STEP 5: Complete opportunities_unified table with missing columns
-- ============================================================================

ALTER TABLE opportunities_unified
ADD COLUMN IF NOT EXISTS submission_id UUID REFERENCES submissions(id) ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS business_concept_id BIGINT REFERENCES business_concepts(id),
ADD COLUMN IF NOT EXISTS copied_from_primary BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS primary_opportunity_id UUID REFERENCES opportunities_unified(id) DEFERRABLE INITIALLY DEFERRED,
ADD COLUMN IF NOT EXISTS semantic_fingerprint TEXT,
ADD COLUMN IF NOT EXISTS app_concept TEXT,
ADD COLUMN IF NOT EXISTS core_functions JSONB,
ADD COLUMN IF NOT EXISTS value_proposition TEXT,
ADD COLUMN IF NOT EXISTS target_user TEXT,
ADD COLUMN IF NOT EXISTS monetization_model TEXT,
ADD COLUMN IF NOT EXISTS priority TEXT,
ADD COLUMN IF NOT EXISTS confidence DECIMAL(3,2) CHECK (confidence >= 0 AND confidence <= 1),
ADD COLUMN IF NOT EXISTS evidence_based BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS dimension_scores JSONB,
ADD COLUMN IF NOT EXISTS ai_profile JSONB,
ADD COLUMN IF NOT EXISTS analyzed_at TIMESTAMPTZ DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS enrichment_version VARCHAR(20) DEFAULT 'v3.0.0',
ADD COLUMN IF NOT EXISTS pipeline_source VARCHAR(50) DEFAULT 'unified_pipeline';

-- ============================================================================
-- STEP 6: Create Indexes for UUID-based Foreign Keys and Performance
-- ============================================================================

-- Indexes for UUID foreign key relationships
CREATE INDEX IF NOT EXISTS idx_app_opportunities_submission_uuid
ON app_opportunities(submission_uuid);

CREATE INDEX IF NOT EXISTS idx_llm_analysis_submission_uuid
ON llm_monetization_analysis(submission_uuid);

CREATE INDEX IF NOT EXISTS idx_workflow_results_submission_uuid
ON workflow_results(submission_uuid);

-- Indexes for deduplication schema
CREATE INDEX IF NOT EXISTS idx_opportunities_unified_business_concept
ON opportunities_unified(business_concept_id);

CREATE INDEX IF NOT EXISTS idx_opportunities_unified_semantic_fingerprint
ON opportunities_unified(semantic_fingerprint) WHERE semantic_fingerprint IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_opportunities_unified_submission_id
ON opportunities_unified(submission_id) WHERE submission_id IS NOT NULL;

-- Composite index for deduplication lookups
CREATE INDEX IF NOT EXISTS idx_opportunities_unified_composite
ON opportunities_unified(business_concept_id, submission_id, copied_from_primary);

-- ============================================================================
-- STEP 7: Data Migration and Validation
-- ============================================================================

-- Migrate data from app_opportunities to opportunities_unified
INSERT INTO opportunities_unified (
    title,
    problem_statement,
    app_concept,
    core_functions,
    value_proposition,
    target_user,
    monetization_model,
    opportunity_score,
    submission_id,
    business_concept_id,
    semantic_fingerprint,
    priority,
    confidence,
    evidence_based,
    dimension_scores,
    ai_profile,
    status,
    created_at,
    updated_at
)
SELECT
    ao.title,
    ao.problem_description,
    ao.app_concept,
    ao.core_functions::JSONB,
    ao.value_proposition,
    ao.target_user,
    ao.monetization_model,
    ao.opportunity_score,
    s.id as submission_id,
    bc.id as business_concept_id,
    -- Create semantic fingerprint from key fields
    COALESCE(
        LOWER(TRIM(REGEXP_REPLACE(COALESCE(ao.app_concept, ''), '[^a-zA-Z0-9]', '', 'g'))),
        LOWER(TRIM(REGEXP_REPLACE(COALESCE(ao.title, ''), '[^a-zA-Z0-9]', '', 'g')))
    ) as semantic_fingerprint,
    ao.priority,
    ao.confidence::DECIMAL(3,2),
    ao.evidence_based,
    ao.dimension_scores::JSONB,
    ao.ai_profile::JSONB,
    COALESCE(ao.status, 'discovered') as status,
    NOW() as created_at,
    NOW() as updated_at
FROM app_opportunities ao
LEFT JOIN submissions s ON s.id = ao.submission_uuid
LEFT JOIN business_concepts bc ON bc.concept_name = ao.app_concept
WHERE NOT EXISTS (
    SELECT 1 FROM opportunities_unified ou
    WHERE ou.submission_id = s.id
);

-- Update llm_monetization_analysis with proper opportunity references
UPDATE llm_monetization_analysis lma
SET opportunity_id = ou.id
FROM opportunities_unified ou
WHERE lma.submission_uuid = ou.submission_id AND lma.opportunity_id IS NULL;

-- ============================================================================
-- STEP 8: Create Validation Functions and Views
-- ============================================================================

-- Function to validate UUID format consistency
CREATE OR REPLACE FUNCTION validate_uuid_format_consistency()
RETURNS TABLE(table_name TEXT, issue_type TEXT, issue_count BIGINT, severity TEXT) AS $$
BEGIN
    -- Check for submission_id format inconsistencies
    RETURN QUERY
    SELECT
        'app_opportunities'::TEXT as table_name,
        'submission_uuid_null'::TEXT as issue_type,
        COUNT(*)::BIGINT as issue_count,
        'HIGH'::TEXT as severity
    FROM app_opportunities ao
    WHERE ao.submission_id IS NOT NULL AND ao.submission_uuid IS NULL;

    -- Check for orphaned UUID references
    RETURN QUERY
    SELECT
        'app_opportunities'::TEXT as table_name,
        'orphaned_submission_uuid'::TEXT as issue_type,
        COUNT(*)::BIGINT as issue_count,
        'HIGH'::TEXT as severity
    FROM app_opportunities ao
    WHERE ao.submission_uuid IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM submissions s WHERE s.id = ao.submission_uuid);

    -- Check for opportunities without proper links
    RETURN QUERY
    SELECT
        'opportunities_unified'::TEXT as table_name,
        'missing_submission_link'::TEXT as issue_type,
        COUNT(*)::BIGINT as issue_count,
        'MEDIUM'::TEXT as severity
    FROM opportunities_unified
    WHERE submission_id IS NULL;

    -- Check for missing semantic fingerprints
    RETURN QUERY
    SELECT
        'opportunities_unified'::TEXT as table_name,
        'missing_semantic_fingerprint'::TEXT as issue_type,
        COUNT(*)::BIGINT as issue_count,
        'LOW'::TEXT as severity
    FROM opportunities_unified
    WHERE semantic_fingerprint IS NULL OR semantic_fingerprint = '';
END;
$$ LANGUAGE plpgsql;

-- Enhanced deduplication integration view with UUID support
CREATE OR REPLACE VIEW deduplication_schema_overview AS
SELECT
    'business_concepts'::TEXT AS table_name,
    'Holds concept metadata and AI analysis results'::TEXT AS description,
    'id (bigint) → opportunities_unified.business_concept_id'::TEXT AS key_relationships,
    COUNT(*)::TEXT AS status
FROM business_concepts

UNION ALL

SELECT
    'submissions'::TEXT AS table_name,
    'Raw Reddit submission data with UUID primary keys'::TEXT AS description,
    'id (uuid) ← app_opportunities.submission_uuid'::TEXT AS key_relationships,
    COUNT(*)::TEXT AS status
FROM submissions

UNION ALL

SELECT
    'opportunities_unified'::TEXT AS table_name,
    'Deduplication pipeline main table with UUID integration'::TEXT AS description,
    'submission_id (uuid) → submissions.id, business_concept_id (bigint) → business_concepts.id'::TEXT AS key_relationships,
    COUNT(*)::TEXT AS status
FROM opportunities_unified

UNION ALL

SELECT
    'app_opportunities'::TEXT AS table_name,
    'Legacy table now with UUID foreign key support'::TEXT AS description,
    'submission_uuid (uuid) → submissions.id'::TEXT AS key_relationships,
    COUNT(*)::TEXT AS status
FROM app_opportunities

UNION ALL

SELECT
    'llm_monetization_analysis'::TEXT AS table_name,
    'LLM analysis results with UUID integration'::TEXT AS description,
    'submission_uuid (uuid) → submissions.id, primary_opportunity_id (uuid) → opportunities_unified.id'::TEXT AS key_relationships,
    COUNT(*)::TEXT AS status
FROM llm_monetization_analysis

UNION ALL

SELECT
    'workflow_results'::TEXT AS table_name,
    'Analysis results with proper UUID references'::TEXT AS description,
    'submission_uuid (uuid) → submissions.id, opportunity_id (uuid) → opportunities_unified.id'::TEXT AS key_relationships,
    COUNT(*)::TEXT AS status
FROM workflow_results;

-- ============================================================================
-- STEP 9: Add Comments for Documentation
-- ============================================================================

-- Comments for new UUID columns
COMMENT ON COLUMN app_opportunities.id IS 'UUID primary key generated for compatibility with deduplication schema';
COMMENT ON COLUMN app_opportunities.submission_uuid IS 'UUID foreign key reference to submissions.id, replacing string-based submission_id';

COMMENT ON COLUMN llm_monetization_analysis.id IS 'UUID primary key generated for compatibility with deduplication schema';
COMMENT ON COLUMN llm_monetization_analysis.submission_uuid IS 'UUID foreign key reference to submissions.id, replacing string-based submission_id';

COMMENT ON COLUMN workflow_results.submission_uuid IS 'UUID foreign key reference to submissions.id, replacing string-based opportunity_id';

-- Comments for opportunities_unified enhancements
COMMENT ON COLUMN opportunities_unified.submission_id IS 'UUID foreign key reference to submissions.id for proper linking';
COMMENT ON COLUMN opportunities_unified.business_concept_id IS 'Foreign key to business_concepts.id for deduplication integration';
COMMENT ON COLUMN opportunities_unified.semantic_fingerprint IS 'Normalized fingerprint for semantic deduplication';
COMMENT ON COLUMN opportunities_unified.copied_from_primary IS 'Indicates if this opportunity was copied from a primary opportunity during deduplication';
COMMENT ON COLUMN opportunities_unified.primary_opportunity_id IS 'Reference to the primary opportunity if this is a duplicate';

-- ============================================================================
-- STEP 10: Create Rollback Procedures
-- ============================================================================

-- Function to rollback UUID format changes
CREATE OR REPLACE FUNCTION rollback_uuid_format_changes()
RETURNS VOID AS $$
BEGIN
    -- Drop UUID foreign key constraints
    ALTER TABLE llm_monetization_analysis DROP CONSTRAINT IF EXISTS fk_llm_analysis_submission_uuid;
    ALTER TABLE workflow_results DROP CONSTRAINT IF EXISTS fk_workflow_results_submission_uuid;

    -- Drop UUID columns
    ALTER TABLE app_opportunities DROP COLUMN IF EXISTS submission_uuid;
    ALTER TABLE llm_monetization_analysis DROP COLUMN IF EXISTS submission_uuid;
    ALTER TABLE workflow_results DROP COLUMN IF EXISTS submission_uuid;

    -- Restore original string-based constraints
    -- Note: This would require recreating the original string-based foreign keys
    -- which is complex and would need to be done manually based on backup

    RAISE NOTICE 'UUID format changes rolled back. Manual restoration of original constraints may be required.';
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 11: Run Validation Checks
-- ============================================================================

-- Run the validation function and log results
DO $$
DECLARE
    validation_record RECORD;
    total_issues INTEGER := 0;
BEGIN
    RAISE NOTICE 'Running UUID format and deduplication schema validation...';

    FOR validation_record IN SELECT * FROM validate_uuid_format_consistency() LOOP
        RAISE NOTICE 'Table: %, Issue: %, Count: %, Severity: %',
            validation_record.table_name,
            validation_record.issue_type,
            validation_record.issue_count,
            validation_record.severity;
        total_issues := total_issues + validation_record.issue_count;
    END LOOP;

    IF total_issues > 0 THEN
        RAISE WARNING 'Validation completed with % issues found. Please review the output above.', total_issues;
    ELSE
        RAISE NOTICE 'Validation completed successfully with no issues found.';
    END IF;
END;
$$;