-- Fix Schema Compatibility for Trust Pipeline
-- Migration to resolve confidence_score vs ai_confidence_level conflict
-- Created: 2025-11-12

-- Step 1: Add confidence_score column if it doesn't exist (for compatibility)
-- This will be a numeric column (0-100) for backward compatibility
ALTER TABLE app_opportunities
ADD COLUMN IF NOT EXISTS confidence_score DECIMAL(5,2) DEFAULT 0.0
CHECK (confidence_score >= 0 AND confidence_score <= 100);

-- Step 2: Create a function to convert ai_confidence_level to numeric score
CREATE OR REPLACE FUNCTION convert_ai_confidence_to_score(confidence_level TEXT)
RETURNS DECIMAL(5,2) AS $$
BEGIN
    CASE confidence_level
        WHEN 'VERY_HIGH' THEN RETURN 90.0;
        WHEN 'HIGH' THEN RETURN 75.0;
        WHEN 'MEDIUM' THEN RETURN 50.0;
        WHEN 'LOW' THEN RETURN 25.0;
        ELSE RETURN 0.0;
    END CASE;
END;
$$ LANGUAGE plpgsql;

-- Step 3: Create a trigger to automatically maintain confidence_score based on ai_confidence_level
CREATE OR REPLACE FUNCTION update_confidence_score_trigger()
RETURNS TRIGGER AS $$
BEGIN
    -- Only update if ai_confidence_level has changed
    IF TG_OP = 'UPDATE' AND OLD.ai_confidence_level IS DISTINCT FROM NEW.ai_confidence_level THEN
        NEW.confidence_score := convert_ai_confidence_to_score(NEW.ai_confidence_level);
    END IF;

    -- For new records
    IF TG_OP = 'INSERT' AND NEW.ai_confidence_level IS NOT NULL THEN
        NEW.confidence_score := convert_ai_confidence_to_score(NEW.ai_confidence_level);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 4: Apply trigger to app_opportunities table
DROP TRIGGER IF EXISTS trigger_update_confidence_score ON app_opportunities;
CREATE TRIGGER trigger_update_confidence_score
    BEFORE INSERT OR UPDATE ON app_opportunities
    FOR EACH ROW EXECUTE FUNCTION update_confidence_score_trigger();

-- Step 5: Update existing records to have proper confidence_score values
UPDATE app_opportunities
SET confidence_score = convert_ai_confidence_to_score(ai_confidence_level)
WHERE ai_confidence_level IS NOT NULL AND (confidence_score = 0.0 OR confidence_score IS NULL);

-- Step 6: Create a composite index for better query performance
CREATE INDEX IF NOT EXISTS idx_app_opportunities_ai_confidence_composite
ON app_opportunities(ai_confidence_level, confidence_score);

-- Step 7: Add constraint to ensure ai_confidence_level values are valid
ALTER TABLE app_opportunities
ADD CONSTRAINT app_opportunities_ai_confidence_level_check_valid
CHECK (
    ai_confidence_level IS NULL OR
    ai_confidence_level IN ('VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW')
);

COMMIT;

-- Documentation
COMMENT ON COLUMN app_opportunities.confidence_score IS 'Numeric confidence score (0-100) automatically derived from ai_confidence_level for backward compatibility';
COMMENT ON FUNCTION convert_ai_confidence_to_score IS 'Convert string AI confidence levels to numeric scores';
COMMENT ON FUNCTION update_confidence_score_trigger IS 'Trigger function to maintain confidence_score consistency';