-- =============================================================================
-- RedditHarbor Schema Fixes - Clean Version
-- Date: 2025-11-20
-- Purpose: Apply critical schema fixes for deduplication pipeline
-- =============================================================================

-- Fix 1: Drop and recreate workflow_results foreign key
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'workflow_results_opportunity_id_fkey'
        AND table_name = 'workflow_results'
    ) THEN
        ALTER TABLE workflow_results DROP CONSTRAINT workflow_results_opportunity_id_fkey;
    END IF;
END $$;

-- Add correct foreign key constraint
ALTER TABLE workflow_results
ADD CONSTRAINT workflow_results_opportunity_id_fkey
FOREIGN KEY (opportunity_id) REFERENCES opportunities_unified(id)
ON DELETE CASCADE;

-- Fix 2: Generate semantic fingerprints for opportunities
UPDATE opportunities_unified
SET semantic_fingerprint =
    encode(digest(
        COALESCE(title, '') || '|' ||
        COALESCE(description, '') || '|' ||
        COALESCE(problem_statement, ''),
        'sha256'
    ), 'hex')
WHERE semantic_fingerprint IS NULL OR semantic_fingerprint = '';

-- Fix 3: Create performance indexes
CREATE INDEX IF NOT EXISTS idx_opportunities_unified_submission_id
ON opportunities_unified(submission_id)
WHERE submission_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_opportunities_unified_semantic_fingerprint
ON opportunities_unified(semantic_fingerprint)
WHERE semantic_fingerprint IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_workflow_results_composite
ON workflow_results(opportunity_id, workflow_type, status);

-- Fix 4: Update table statistics (optional)
ANALYZE business_concepts;
ANALYZE submissions;
ANALYZE opportunities_unified;
ANALYZE workflow_results;

-- Fix 5: Simple validation query
SELECT
    'business_concepts' as table_name, COUNT(*) as record_count FROM business_concepts
UNION ALL
SELECT 'submissions', COUNT(*) FROM submissions
UNION ALL
SELECT 'opportunities_unified', COUNT(*) FROM opportunities_unified
UNION ALL
SELECT 'workflow_results', COUNT(*) FROM workflow_results;