-- Add DLT metadata columns to app_opportunities table
-- Required for DLT merge disposition and deduplication

ALTER TABLE app_opportunities
ADD COLUMN IF NOT EXISTS _dlt_load_id text,
ADD COLUMN IF NOT EXISTS _dlt_id text;

-- Set default values for existing rows
UPDATE app_opportunities
SET _dlt_load_id = 'manual_' || id::text,
    _dlt_id = id::text
WHERE _dlt_load_id IS NULL;

-- Add comment
COMMENT ON COLUMN app_opportunities._dlt_load_id IS 'DLT load batch identifier for tracking data lineage';
COMMENT ON COLUMN app_opportunities._dlt_id IS 'DLT unique row identifier for deduplication';
