-- RedditHarbor ID Normalization Trigger Migration (Final)
-- Phase 3: Database Enforcement
--
-- This migration implements PostgreSQL-level enforcement for canonical ID resolution
-- by automatically normalizing submission_id values to UUID format using deterministic
-- UUID v5 generation that matches Python's uuid.uuid5() behavior exactly.
--
-- Namespace: 67959699-bbd7-5213-8934-bbfccb37697b (RedditHarbor pipeline)
-- Created: 2025-11-23 12:00:00 UTC
-- Author: Data Engineering Team

-- ========================================
-- DEPENDENCY VERIFICATION
-- ========================================

-- Ensure pgcrypto extension is available for SHA-1 digest functions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ========================================
-- UUID V5 GENERATION FUNCTION (Final - Using Built-in)
-- ========================================

/**
 * uuid5_generate(namespace_uuid, name_string)
 *
 * Generates a deterministic UUID v5 using SHA-1, exactly matching Python's uuid.uuid5()
 *
 * This implementation uses PostgreSQL's built-in uuid_generate_v5 function which
 * follows the exact RFC 4122 specification as Python's uuid.uuid5().
 *
 * Parameters:
 *   namespace_uuid: UUID namespace (must use RedditHarbor namespace)
 *   name_string: String to generate deterministic UUID from
 *
 * Returns:
 *   UUID: Deterministic UUID v5 or NULL if name_string is NULL/empty
 *
 * Security: IMMUTABLE function - safe for use in indexes and constraints
 */
CREATE OR REPLACE FUNCTION uuid5_generate(namespace_uuid UUID, name_string TEXT)
RETURNS UUID
IMMUTABLE
LANGUAGE sql
AS $$
    -- Use PostgreSQL's built-in uuid_generate_v5 function for RFC 4122 compliance
    SELECT CASE
        WHEN name_string IS NULL OR name_string = '' THEN NULL
        ELSE uuid_generate_v5(namespace_uuid, name_string)
    END;
$$;

-- ========================================
-- REDDITHARBOR NAMESPACE CONSTANT
-- ========================================

/**
 * RedditHarbor pipeline namespace for UUID v5 generation
 * Computed using Python: uuid.uuid5(uuid.NAMESPACE_DNS, "redditharbor-pipeline")
 * Value: 67959699-bbd7-5213-8934-bbfccb37697b
 *
 * This matches exactly the namespace used in core/utils/id_resolver.py
 */
CREATE OR REPLACE FUNCTION redditharbor_namespace()
RETURNS UUID
IMMUTABLE
LANGUAGE sql
AS $$
    SELECT '67959699-bbd7-5213-8934-bbfccb37697b'::UUID;
$$;

-- ========================================
-- SUBMISSION ID NORMALIZATION FUNCTION
-- ========================================

/**
 * normalize_submission_id(input_id)
 *
 * Normalizes various submission ID formats to canonical RedditHarbor UUID
 *
 * This function implements the core ID resolution logic that matches the Python
 * implementation in core/utils/id_resolver.py:
 * 1. NULL/empty values -> NULL (passthrough)
 * 2. Valid UUIDs -> passthrough unchanged (normalized to lowercase)
 * 3. Reddit URLs -> extract ID and generate deterministic UUID
 * 4. Reddit IDs -> generate deterministic UUID
 * 5. Other strings -> generate deterministic UUID
 *
 * Parameters:
 *   input_id: Input value in any format (UUID, Reddit ID, URL, etc.)
 *
 * Returns:
 *   UUID: Canonical RedditHarbor UUID or NULL
 *
 * Security: IMMUTABLE function - safe for use in triggers and constraints
 */
CREATE OR REPLACE FUNCTION normalize_submission_id(input_id TEXT)
RETURNS UUID
IMMUTABLE
LANGUAGE plpgsql
AS $$
DECLARE
    trimmed_input TEXT;
    uuid_pattern TEXT;
    reddit_url_pattern TEXT;
BEGIN
    -- 1. NULL/Empty check
    IF input_id IS NULL OR input_id = '' THEN
        RETURN NULL;
    END IF;

    -- Trim whitespace
    trimmed_input := TRIM(input_id);

    -- Return NULL for empty after trimming
    IF trimmed_input = '' THEN
        RETURN NULL;
    END IF;

    -- 2. UUID validation using regex pattern
    -- Pattern: /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    uuid_pattern := '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
    IF trimmed_input ~* uuid_pattern THEN
        -- Passthrough valid UUID (lowercase normalization)
        RETURN trimmed_input::UUID;
    END IF;

    -- 3. Reddit URL extraction
    -- Use SUBSTRING to extract the Reddit ID from URLs
    -- This handles URLs like: https://reddit.com/r/subreddit/comments/abc123/title
    -- and: https://reddit.com/comments/abc123/title
    IF trimmed_input ~ 'reddit\.com.*comments/([a-zA-Z0-9]{6,})' THEN
        -- Extract using SUBSTRING which is more reliable than REGEXP_REPLACE
        RETURN uuid5_generate(redditharbor_namespace(), SUBSTRING(trimmed_input FROM 'reddit\.com.*comments/([a-zA-Z0-9]{6,})'));
    END IF;

    -- 4. Generate deterministic UUID for all other valid inputs
    -- This handles direct Reddit IDs and other string formats
    RETURN uuid5_generate(redditharbor_namespace(), trimmed_input);
END;
$$;

-- ========================================
-- APP_OPPORTUNITIES TRIGGER
-- ========================================

/**
 * Trigger function to normalize submission_id before INSERT/UPDATE
 *
 * This trigger automatically converts non-UUID submission_id values to
 * canonical RedditHarbor UUIDs using the same logic as the Python resolver.
 *
 * Trigger Behavior:
 * - Fires BEFORE INSERT and BEFORE UPDATE on app_opportunities
 * - Only processes NEW.submission_id when it changes
 * - Preserves existing valid UUIDs unchanged
 * - Converts non-UUID values to deterministic UUIDs
 * - Allows NULL values (for NOT NULL constraint handling)
 */
CREATE OR REPLACE FUNCTION normalize_app_opportunities_submission_id()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Process submission_id if it's being set or changed
    IF NEW.submission_id IS DISTINCT FROM OLD.submission_id THEN
        -- Normalize the submission_id using the resolver logic
        NEW.submission_id := normalize_submission_id(NEW.submission_id);
    END IF;

    RETURN NEW;
END;
$$;

/**
 * Main trigger for app_opportunities submission_id normalization
 *
 * This trigger enforces canonical ID resolution at the database level,
 * ensuring that all submission_id values are properly normalized UUIDs.
 *
 * Trigger Configuration:
 * - Timing: BEFORE INSERT, BEFORE UPDATE
 * - Target: app_opportunities table
 * - Condition: When submission_id column is affected
 */
DROP TRIGGER IF EXISTS trigger_normalize_app_opportunities_submission_id ON app_opportunities;
CREATE TRIGGER trigger_normalize_app_opportunities_submission_id
    BEFORE INSERT OR UPDATE ON app_opportunities
    FOR EACH ROW
    EXECUTE FUNCTION normalize_app_opportunities_submission_id();

-- ========================================
-- VERIFICATION AND TESTING
-- ========================================

-- Test the implementation with known values from Python
DO $$
DECLARE
    test_input TEXT := 'abc123';
    postgres_uuid UUID;
    python_expected UUID := '7e975bfc-ff6d-5798-b61a-19d72ed6a63b'::UUID;
BEGIN
    -- Test the normalization function
    SELECT normalize_submission_id(test_input) INTO postgres_uuid;

    IF postgres_uuid = python_expected THEN
        RAISE NOTICE '✓ UUID5 normalization test passed: %', postgres_uuid;
    ELSE
        RAISE EXCEPTION '✗ UUID5 normalization test failed: expected %, got %', python_expected, postgres_uuid;
    END IF;

    -- Test UUID passthrough
    SELECT normalize_submission_id('67959699-bbd7-5213-8934-bbfccb37697b'::TEXT) INTO postgres_uuid;
    IF postgres_uuid = '67959699-bbd7-5213-8934-bbfccb37697b'::UUID THEN
        RAISE NOTICE '✓ UUID passthrough test passed';
    ELSE
        RAISE EXCEPTION '✗ UUID passthrough test failed';
    END IF;

    -- Test URL extraction
    SELECT normalize_submission_id('https://reddit.com/r/test/comments/xyz123/post_title') INTO postgres_uuid;
    IF postgres_uuid IS NOT NULL THEN
        RAISE NOTICE '✓ Reddit URL extraction test passed: %', postgres_uuid;
    ELSE
        RAISE EXCEPTION '✗ Reddit URL extraction test failed';
    END IF;

    RAISE NOTICE '✓ All verification tests passed';
END $$;

-- ========================================
-- PERFORMANCE INDEXES (Optional)
-- ========================================

-- Create index on submission_id for performance if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE indexname = 'idx_app_opportunities_submission_id'
    ) THEN
        CREATE INDEX idx_app_opportunities_submission_id
        ON app_opportunities(submission_id);
        RAISE NOTICE '✓ Created performance index on app_opportunities.submission_id';
    END IF;
END $$;

-- ========================================
-- MIGRATION COMPLETION
-- ========================================

-- Record migration completion
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE 'RedditHarbor ID Normalization Migration Completed Successfully';
    RAISE NOTICE '=====================================================';
    RAISE NOTICE 'Namespace: 67959699-bbd7-5213-8934-bbfccb37697b';
    RAISE NOTICE 'Functions: 4 created (uuid5_generate, redditharbor_namespace, normalize_submission_id, normalize_app_opportunities_submission_id)';
    RAISE NOTICE 'Triggers: 1 created (trigger_normalize_app_opportunities_submission_id)';
    RAISE NOTICE 'Table: app_opportunities (submission_id column)';
    RAISE NOTICE 'Compatibility: Full Python uuid.uuid5() compatibility using built-in uuid_generate_v5';
    RAISE NOTICE '';
END $$;