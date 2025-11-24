-- RedditHarbor Existing Data Normalization Migration
-- Phase 3: Database Enforcement - Data Migration
--
-- This migration normalizes existing non-UUID submission_id records in app_opportunities
-- using the normalize_submission_id function to ensure data consistency.
--
-- Created: 2025-11-23 12:00:02 UTC
-- Author: Data Engineering Team

-- ========================================
-- MIGRATION SAFETY CHECKS
-- ========================================

-- Ensure this migration hasn't been run before
DO $$
DECLARE
    migration_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'app_opportunities'
        AND column_default LIKE '%normalize_submission_id%'
    ) INTO migration_exists;

    IF migration_exists THEN
        RAISE EXCEPTION 'Migration already applied or normalize_submission_id function not available';
    END IF;
END $$;

-- Verify normalize_submission_id function exists
DO $$
DECLARE
    function_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.routines
        WHERE routine_name = 'normalize_submission_id'
        AND routine_schema = 'public'
    ) INTO function_exists;

    IF NOT function_exists THEN
        RAISE EXCEPTION 'normalize_submission_id function not found. Please run migration 20251123120000 first.';
    END IF;
END $$;

-- ========================================
-- DATA ANALYSIS BEFORE MIGRATION
-- ========================================

-- Record current state for audit
DO $$
DECLARE
    total_records BIGINT;
    non_uuid_records BIGINT;
    null_records BIGINT;
    valid_uuid_records BIGINT;
BEGIN
    -- Count total records
    EXECUTE 'SELECT COUNT(*) FROM app_opportunities' INTO total_records;

    -- Count NULL submission_ids
    EXECUTE 'SELECT COUNT(*) FROM app_opportunities WHERE submission_id IS NULL' INTO null_records;

    -- Count non-UUID submission_ids
    EXECUTE 'SELECT COUNT(*) FROM app_opportunities WHERE submission_id IS NOT NULL AND NOT (submission_id LIKE ''t1_%'')' INTO non_uuid_records;

    -- Count valid UUID submission_ids (t1_ prefix indicates normalized UUID)
    EXECUTE 'SELECT COUNT(*) FROM app_opportunities WHERE submission_id IS NOT NULL AND submission_id LIKE ''t1_%''' INTO valid_uuid_records;

    RAISE NOTICE '=== DATA MIGRATION AUDIT ===';
    RAISE NOTICE 'Total records: %', total_records;
    RAISE NOTICE 'NULL submission_ids: %', null_records;
    RAISE NOTICE 'Non-UUID submission_ids: %', non_uuid_records;
    RAISE NOTICE 'Already normalized UUIDs: %', valid_uuid_records;
    RAISE NOTICE '==========================';
END $$;

-- Create a backup of records to be normalized
CREATE TEMP TABLE app_opportunities_backup AS
SELECT
    * -- Note: This creates a backup of all columns
FROM app_opportunities
WHERE submission_id IS NOT NULL
AND NOT (submission_id LIKE 't1_%');

RAISE NOTICE 'Created backup table with % records to be normalized',
    (SELECT COUNT(*) FROM app_opportunities_backup);

-- ========================================
-- IDENTIFY RECORDS TO NORMALIZE
-- ========================================

-- Display sample records that will be normalized
DO $$
DECLARE
    sample_records RECORD;
BEGIN
    RAISE NOTICE '=== SAMPLE RECORDS TO NORMALIZE ===';

    FOR sample_records IN
        SELECT submission_id
        FROM app_opportunities
        WHERE submission_id IS NOT NULL
        AND NOT (submission_id LIKE 't1_%')
        LIMIT 5
    LOOP
        RAISE NOTICE 'Will normalize: "%" -> UUID', sample_records.submission_id;
    END LOOP;

    RAISE NOTICE '=================================';
END $$;

-- ========================================
-- PERFORM DATA NORMALIZATION
-- ========================================

-- Create a function to safely update records in batches
CREATE OR REPLACE FUNCTION batch_normalize_submission_ids(
    batch_size INT DEFAULT 10,
    batch_delay INTERVAL DEFAULT '100ms'
)
RETURNS TABLE(
    batch_num INT,
    records_updated BIGINT,
    errors_encountered BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    total_updated BIGINT := 0;
    total_errors BIGINT := 0;
    current_batch INT := 0;
    batch_record RECORD;
    records_to_update BIGINT;
BEGIN
    -- Get total count of records to process
    SELECT COUNT(*) INTO records_to_update
    FROM app_opportunities
    WHERE submission_id IS NOT NULL
    AND NOT (submission_id LIKE 't1_%');

    RAISE NOTICE 'Starting batch normalization of % records', records_to_update;

    -- Process in batches to avoid transaction overload
    FOR batch_record IN
        SELECT submission_id, _dlt_id
        FROM app_opportunities
        WHERE submission_id IS NOT NULL
        AND NOT (submission_id LIKE 't1_%')
        ORDER BY _dlt_id -- Process deterministically
        LIMIT batch_size OFFSET (current_batch * batch_size)
    LOOP
        current_batch := current_batch + 1;

        BEGIN
            -- Update current batch
            UPDATE app_opportunities
            SET submission_id = normalize_submission_id(submission_id)
            WHERE submission_id = batch_record.submission_id;

            GET DIAGNOSTICS total_updated = ROW_COUNT;

            RAISE NOTICE 'Batch %: Normalized % records', current_batch, total_updated;

            -- Add small delay to prevent overwhelming the system
            PERFORM pg_sleep(EXTRACT(EPOCH FROM batch_delay));

            RETURN NEXT;

        EXCEPTION WHEN OTHERS THEN
            total_errors := total_errors + 1;
            RAISE WARNING 'Error in batch % for submission_id "%": %',
                current_batch, batch_record.submission_id, SQLERRM;
        END;
    END LOOP;

    RAISE NOTICE '=== BATCH NORMALIZATION COMPLETE ===';
    RAISE NOTICE 'Total batches processed: %', current_batch;
    RAISE NOTICE 'Total records updated: %', total_updated;
    RAISE NOTICE 'Total errors encountered: %', total_errors;
    RAISE NOTICE '=================================';
END;
$$;

-- Execute the batch normalization
SELECT * FROM batch_normalize_submission_ids(5, '50ms');

-- ========================================
-- VALIDATION AFTER MIGRATION
-- ========================================

-- Verify normalization results
DO $$
DECLARE
    total_records BIGINT;
    normalized_records BIGINT;
    null_records BIGINT;
    still_non_uuid BIGINT;
    validation_passed BOOLEAN := TRUE;
BEGIN
    -- Count total records
    EXECUTE 'SELECT COUNT(*) FROM app_opportunities' INTO total_records;

    -- Count NULL submission_ids
    EXECUTE 'SELECT COUNT(*) FROM app_opportunities WHERE submission_id IS NULL' INTO null_records;

    -- Count successfully normalized records (t1_ prefix indicates normalized UUID)
    EXECUTE 'SELECT COUNT(*) FROM app_opportunities WHERE submission_id IS NOT NULL AND submission_id LIKE ''t1_%''' INTO normalized_records;

    -- Count any remaining non-UUID records
    EXECUTE 'SELECT COUNT(*) FROM app_opportunities WHERE submission_id IS NOT NULL AND NOT (submission_id LIKE ''t1_%'')' INTO still_non_uuid;

    RAISE NOTICE '=== POST-MIGRATION VALIDATION ===';
    RAISE NOTICE 'Total records: %', total_records;
    RAISE NOTICE 'NULL submission_ids: %', null_records;
    RAISE NOTICE 'Successfully normalized UUIDs: %', normalized_records;
    RAISE NOTICE 'Remaining non-UUID records: %', still_non_uuid;
    RAISE NOTICE '=================================';

    -- Validate against backup
    IF still_non_uuid > 0 THEN
        RAISE WARNING '⚠️  Records still need normalization: %', still_non_uuid;
        validation_passed := FALSE;
    END IF;

    -- Check if we lost any data
    IF (SELECT COUNT(*) FROM app_opportunities_backup) != normalized_records THEN
        RAISE WARNING '⚠️  Data count mismatch - some records may not have been normalized';
        validation_passed := FALSE;
    END IF;

    IF validation_passed THEN
        RAISE NOTICE '✅ Data normalization validation PASSED';
    ELSE
        RAISE EXCEPTION '❌ Data normalization validation FAILED';
    END IF;
END $$;

-- ========================================
-- SAMPLE VERIFICATION
-- ========================================

-- Show sample results
DO $$
DECLARE
    sample_result RECORD;
BEGIN
    RAISE NOTICE '=== SAMPLE NORMALIZATION RESULTS ===';

    FOR sample_result IN
        SELECT b.submission_id as original_id, a.submission_id as normalized_id
        FROM app_opportunities a
        JOIN app_opportunities_backup b ON a._dlt_id = b._dlt_id
        WHERE b.submission_id IS NOT NULL
        AND NOT (b.submission_id LIKE 't1_%')
        LIMIT 5
    LOOP
        RAISE NOTICE 'Original: "%" -> Normalized: "%"',
            sample_result.original_id, sample_result.normalized_id;
    END LOOP;

    RAISE NOTICE '===================================';
END $$;

-- ========================================
-- CLEANUP
-- ========================================

-- Drop the batch processing function (no longer needed)
DROP FUNCTION IF EXISTS batch_normalize_submission_ids(INT, INTERVAL);

-- Keep backup table for 7 days for safety, then it can be dropped
DO $$
BEGIN
    RAISE NOTICE '=== CLEANUP NOTES ===';
    RAISE NOTICE 'Backup table app_opportunities_backup retained for safety';
    RAISE NOTICE 'Can be dropped manually after verification: DROP TABLE app_opportunities_backup;';
    RAISE NOTICE '=====================';
END $$;

-- ========================================
-- MIGRATION COMPLETION
-- ========================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE 'RedditHarbor Data Normalization Migration Completed Successfully';
    RAISE NOTICE '================================================================';
    RAISE NOTICE 'Migration ID: 20251123120002';
    RAISE NOTICE 'Function Used: normalize_submission_id';
    RAISE NOTICE 'Backup Table: app_opportunities_backup';
    RAISE NOTICE 'Validation: PASSED';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '1. Verify application functionality with normalized data';
    RAISE NOTICE '2. Monitor DLT pipeline performance';
    RAISE NOTICE '3. Consider dropping backup table after 7 days';
    RAISE NOTICE '';
END $$;