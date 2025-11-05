-- Migration 6: Constraints & Triggers
-- Created: 2025-11-04 19:00:05
-- Description: Adds constraints, CHECK constraints, foreign keys, and critical trigger
-- Focus: Simplicity constraint enforcement (4+ functions = auto disqualification)

-- Create migrations log table if it doesn't exist
CREATE TABLE IF NOT EXISTS _migrations_log (
    migration_name VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Add Remaining CHECK Constraints for Extended Tables
-- ============================================================================

-- Redditors constraints
DO $$
BEGIN
    -- Add karma constraint if redditors table exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'redditors') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints WHERE constraint_name = 'chk_redditors_karma_non_negative') THEN
            ALTER TABLE redditors ADD CONSTRAINT chk_redditors_karma_non_negative CHECK (karma_score >= 0);
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints WHERE constraint_name = 'chk_redditors_age_non_negative') THEN
            ALTER TABLE redditors ADD CONSTRAINT chk_redditors_age_non_negative CHECK (account_age_days >= 0);
        END IF;
    END IF;
END $$;

-- Submissions constraints
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'submissions') THEN
        -- Add upvotes constraint
        IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints WHERE constraint_name = 'chk_submissions_upvotes_non_negative') THEN
            ALTER TABLE submissions ADD CONSTRAINT chk_submissions_upvotes_non_negative CHECK (upvotes >= 0);
        END IF;

        -- Add downvotes constraint
        IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints WHERE constraint_name = 'chk_submissions_downvotes_non_negative') THEN
            ALTER TABLE submissions ADD CONSTRAINT chk_submissions_downvotes_non_negative CHECK (downvotes >= 0);
        END IF;

        -- Add comments_count constraint
        IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints WHERE constraint_name = 'chk_submissions_comments_non_negative') THEN
            ALTER TABLE submissions ADD CONSTRAINT chk_submissions_comments_non_negative CHECK (comments_count >= 0);
        END IF;

        -- Add sentiment_score constraint
        IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints WHERE constraint_name = 'chk_submissions_sentiment_range') THEN
            ALTER TABLE submissions ADD CONSTRAINT chk_submissions_sentiment_range CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0);
        END IF;
    END IF;
END $$;

-- Comments constraints
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'comments') THEN
        -- Add upvotes constraint
        IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints WHERE constraint_name = 'chk_comments_upvotes_non_negative') THEN
            ALTER TABLE comments ADD CONSTRAINT chk_comments_upvotes_non_negative CHECK (upvotes >= 0);
        END IF;

        -- Add depth constraint
        IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints WHERE constraint_name = 'chk_comments_depth_valid') THEN
            ALTER TABLE comments ADD CONSTRAINT chk_comments_depth_valid CHECK (comment_depth >= 0);
        END IF;

        -- Add sentiment constraint
        IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints WHERE constraint_name = 'chk_comments_sentiment_range') THEN
            ALTER TABLE comments ADD CONSTRAINT chk_comments_sentiment_range CHECK (sentiment_score >= -1.0 AND sentiment_score <= 1.0);
        END IF;
    END IF;
END $$;

-- ============================================================================
-- CRITICAL: Simplicity Constraint Enforcement Trigger
-- ============================================================================
-- This trigger automatically disqualifies any opportunity with 4+ core functions
-- This is the core enforcement mechanism for the 1-3 function constraint

CREATE OR REPLACE FUNCTION enforce_simplicity_constraint()
RETURNS TRIGGER AS $$
BEGIN
    -- Automatically disqualify apps with 4+ core functions
    IF NEW.core_function_count >= 4 THEN
        NEW.simplicity_constraint_met = false;
        NEW.status = 'disqualified';
    ELSIF NEW.core_function_count <= 3 THEN
        NEW.simplicity_constraint_met = true;
        -- Set status to 'valid' if it was previously disqualified and now meets constraint
        IF NEW.status = 'disqualified' THEN
            NEW.status = 'identified';
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on opportunities table
DROP TRIGGER IF EXISTS trigger_enforce_simplicity ON opportunities;

CREATE TRIGGER trigger_enforce_simplicity
    BEFORE INSERT OR UPDATE ON opportunities
    FOR EACH ROW
    EXECUTE FUNCTION enforce_simplicity_constraint();

COMMENT ON FUNCTION enforce_simplicity_constraint() IS 'Automatically disqualifies opportunities with 4+ core functions';

-- ============================================================================
-- Additional Constraint Enforcement for Score Validation
-- ============================================================================

-- Ensure simplicity score reflects function count accurately
CREATE OR REPLACE FUNCTION calculate_simplicity_score()
RETURNS TRIGGER AS $$
BEGIN
    -- Set simplicity score based on function count
    IF NEW.core_function_count = 1 THEN
        NEW.simplicity_score = 100;
    ELSIF NEW.core_function_count = 2 THEN
        NEW.simplicity_score = 85;
    ELSIF NEW.core_function_count = 3 THEN
        NEW.simplicity_score = 70;
    ELSIF NEW.core_function_count >= 4 THEN
        NEW.simplicity_score = 0;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_calculate_simplicity ON opportunity_scores;

CREATE TRIGGER trigger_calculate_simplicity
    BEFORE INSERT OR UPDATE ON opportunity_scores
    FOR EACH ROW
    EXECUTE FUNCTION calculate_simplicity_score();

COMMENT ON FUNCTION calculate_simplicity_score() IS 'Sets simplicity score: 1 func=100, 2=85, 3=70, 4+=0';

-- Foreign keys already created in Migration 1

-- Migration completed successfully
INSERT INTO _migrations_log (migration_name, applied_at) VALUES ('20251104190005_constraints_triggers', NOW()) ON CONFLICT DO NOTHING;


-- All foreign keys were created in Migration 1