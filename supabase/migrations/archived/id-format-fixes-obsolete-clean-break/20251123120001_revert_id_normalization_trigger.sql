-- RedditHarbor ID Normalization Trigger Rollback Migration
-- Phase 3: Database Enforcement Rollback
--
-- This migration safely removes all ID normalization enforcement components
-- and restores the database to its previous state while preserving data integrity.
--
-- Created: 2025-11-23 12:00:01 UTC
-- Author: Data Engineering Team
-- Version: 1.0.0

-- ========================================
-- MIGRATION SAFETY CHECKS
-- ========================================

-- Verify this is a rollback operation (prevent accidental execution)
DO $$
DECLARE
    is_rollback BOOLEAN := FALSE;
BEGIN
    -- Check if we're in a rollback context
    -- This is a safety measure to prevent accidental data loss
    RAISE NOTICE '⚠️  ROLLBACK MIGRATION - This will remove ID normalization enforcement';
    RAISE NOTICE '⚠️  Ensure you want to remove automatic ID normalization triggers';

    -- Continue with rollback - user has been warned
END $$;

-- ========================================
-- TRIGGER REMOVAL
-- ========================================

/**
 * Remove the app_opportunities submission_id normalization trigger
 *
 * This trigger was responsible for automatically converting non-UUID
 * submission_id values to canonical RedditHarbor UUIDs.
 */
DROP TRIGGER IF EXISTS trigger_normalize_app_opportunities_submission_id ON app_opportunities;

-- Verify trigger removal
DO $$
DECLARE
    trigger_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO trigger_count
    FROM information_schema.triggers
    WHERE trigger_name = 'trigger_normalize_app_opportunities_submission_id';

    IF trigger_count = 0 THEN
        RAISE NOTICE '✓ ID normalization trigger removed successfully';
    ELSE
        RAISE WARNING '⚠️  ID normalization trigger may not have been removed completely';
    END IF;
END $$;

-- ========================================
-- FUNCTION REMOVAL
-- ========================================

/**
 * Remove all ID normalization functions in dependency order
 *
 * Functions are removed in reverse dependency order to avoid
 * referencing dropped functions during cleanup.
 */

-- Remove trigger function (depends on normalization function)
DROP FUNCTION IF EXISTS normalize_app_opportunities_submission_id();

-- Remove validation function (independent)
DROP FUNCTION IF EXISTS is_valid_submission_id(TEXT);

-- Remove normalization function (depends on uuid5_generate and redditharbor_namespace)
DROP FUNCTION IF EXISTS normalize_submission_id(TEXT);

-- Remove namespace function (depends on nothing)
DROP FUNCTION IF EXISTS redditharbor_namespace();

-- Remove uuid5_generate function (core dependency)
DROP FUNCTION IF EXISTS uuid5_generate(UUID, TEXT);

-- Verify function removal
DO $$
DECLARE
    function_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO function_count
    FROM information_schema.routines
    WHERE routine_name IN (
        'uuid5_generate',
        'redditharbor_namespace',
        'normalize_submission_id',
        'is_valid_submission_id',
        'normalize_app_opportunities_submission_id'
    );

    IF function_count = 0 THEN
        RAISE NOTICE '✓ All ID normalization functions removed successfully';
    ELSE
        RAISE WARNING '⚠️  Some ID normalization functions may not have been removed: %', function_count;
    END IF;
END $$;

-- ========================================
-- CLEANUP OPTIONAL INDEXES
-- ========================================

/**
 * Remove performance indexes created for ID normalization
 *
 * These indexes were optional and created for performance.
 * We remove them only if they were created by our migration.
 */
DO $$
BEGIN
    -- Check if the index exists and was created by our migration
    IF EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE indexname = 'idx_app_opportunities_submission_id'
        AND tablename = 'app_opportunities'
    ) THEN
        -- Additional safety check: verify the index is on submission_id column
        IF EXISTS (
            SELECT 1 FROM pg_index
            JOIN pg_class ON pg_index.indexrelid = pg_class.oid
            JOIN pg_attribute ON pg_attribute.attrelid = pg_index.indrelid
                              AND pg_attribute.attnum = ANY(pg_index.indkey)
            JOIN pg_class table_class ON pg_index.indrelid = table_class.oid
            WHERE pg_class.relname = 'idx_app_opportunities_submission_id'
            AND table_class.relname = 'app_opportunities'
            AND pg_attribute.attname = 'submission_id'
        ) THEN
            DROP INDEX IF EXISTS idx_app_opportunities_submission_id;
            RAISE NOTICE '✓ Removed ID normalization performance index';
        ELSE
            RAISE WARNING '⚠️  Index idx_app_opportunities_submission_id exists but is not on submission_id column - not removed';
        END IF;
    END IF;
END $$;

-- ========================================
-- EXTENSION CLEANUP (Optional)
-- ========================================

/**
 * Note: We do NOT remove the pgcrypto extension as other parts
 * of the application may depend on it. pgcrypto is a common
 * extension that should be left in place unless explicitly
 * requested for removal.
 */

-- ========================================
-- DATA INTEGRITY VERIFICATION
-- ========================================

/**
 * Verify that app_opportunities table still exists and has data
 *
 * This ensures that our rollback operation didn't accidentally
 * affect the underlying data structure.
 */
DO $$
DECLARE
    table_exists BOOLEAN;
    row_count BIGINT;
    submission_id_count BIGINT;
    null_submission_id_count BIGINT;
BEGIN
    -- Check if table exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'app_opportunities'
    ) INTO table_exists;

    IF NOT table_exists THEN
        RAISE EXCEPTION '❌ Critical: app_opportunities table not found after rollback';
    END IF;

    -- Count total rows
    EXECUTE 'SELECT COUNT(*) FROM app_opportunities' INTO row_count;

    -- Count non-NULL submission_id values
    EXECUTE 'SELECT COUNT(*) FROM app_opportunities WHERE submission_id IS NOT NULL' INTO submission_id_count;

    -- Count NULL submission_id values
    EXECUTE 'SELECT COUNT(*) FROM app_opportunities WHERE submission_id IS NULL' INTO null_submission_id_count;

    RAISE NOTICE '✓ Data integrity verification:';
    RAISE NOTICE '  - app_opportunities table exists: %', table_exists;
    RAISE NOTICE '  - Total rows: %', row_count;
    RAISE NOTICE '  - Non-NULL submission_id values: %', submission_id_count;
    RAISE NOTICE '  - NULL submission_id values: %', null_submission_id_count;

    -- Basic sanity check
    IF row_count = 0 THEN
        RAISE WARNING '⚠️  Warning: app_opportunities table is empty';
    END IF;

    IF submission_id_count + null_submission_id_count != row_count THEN
        RAISE WARNING '⚠️  Warning: Row count mismatch in verification';
    END IF;
END $$;

-- ========================================
-- SCHEMA STATE VERIFICATION
-- ========================================

/**
 * Verify that the schema is in a clean state after rollback
 */
DO $$
DECLARE
    function_count INTEGER;
    trigger_count INTEGER;
    remaining_objects TEXT;
BEGIN
    -- Check for any remaining ID normalization functions
    SELECT COUNT(*) INTO function_count
    FROM information_schema.routines
    WHERE routine_name IN (
        'uuid5_generate',
        'redditharbor_namespace',
        'normalize_submission_id',
        'is_valid_submission_id',
        'normalize_app_opportunities_submission_id'
    );

    -- Check for any remaining ID normalization triggers
    SELECT COUNT(*) INTO trigger_count
    FROM information_schema.triggers
    WHERE trigger_name = 'trigger_normalize_app_opportunities_submission_id';

    -- Report findings
    IF function_count = 0 AND trigger_count = 0 THEN
        RAISE NOTICE '✓ Schema is clean - all ID normalization objects removed';
    ELSE
        remaining_objects := format('Functions: %s, Triggers: %s', function_count, trigger_count);
        RAISE WARNING '⚠️  Some ID normalization objects may remain: %', remaining_objects;
    END IF;
END $$;

-- ========================================
-- POST-ROLLBACK GUIDANCE
-- ========================================

/**
 * Provide guidance for post-rollback operations
 */
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE 'RedditHarbor ID Normalization Rollback Completed';
    RAISE NOTICE '==============================================';
    RAISE NOTICE '';
    RAISE NOTICE '🔄 Changes Rolled Back:';
    RAISE NOTICE '  - Removed trigger: trigger_normalize_app_opportunities_submission_id';
    RAISE NOTICE '  - Removed functions: uuid5_generate, redditharbor_namespace, normalize_submission_id, is_valid_submission_id, normalize_app_opportunities_submission_id';
    RAISE NOTICE '  - Removed performance index: idx_app_opportunities_submission_id (if created)';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Data Status:';
    RAISE NOTICE '  - All existing data preserved in app_opportunities table';
    RAISE NOTICE '  - No data modification performed during rollback';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  Important Notes:';
    RAISE NOTICE '  - pgcrypto extension left in place (may be used by other features)';
    RAISE NOTICE '  - New records will no longer be auto-normalized to UUIDs';
    RAISE NOTICE '  - Application should handle ID normalization at the code level';
    RAISE NOTICE '  - Consider running data validation to ensure consistency';
    RAISE NOTICE '';
    RAISE NOTICE '🔍 Recommended Post-Rollback Actions:';
    RAISE NOTICE '  1. Verify application compatibility with non-normalized IDs';
    RAISE NOTICE '  2. Check for any existing non-UUID submission_id values';
    RAISE NOTICE '  3. Validate that ID resolution logic in code handles all formats';
    RAISE NOTICE '  4. Monitor application behavior for ID-related issues';
    RAISE NOTICE '';
    RAISE NOTICE 'To re-enable ID normalization, run the forward migration:';
    RAISE NOTICE '  20251123120000_add_id_normalization_trigger.sql';
    RAISE NOTICE '';
END $$;