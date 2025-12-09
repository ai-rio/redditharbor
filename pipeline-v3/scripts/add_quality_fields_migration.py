#!/usr/bin/env python3
"""
Migration script to add AI quality tracking fields to opportunities table

This script adds the Phase 2+ quality assessment fields to the database:
- content_quality_score: AI-generated content quality score (0-100)
- is_spam: AI-identified spam flag
- spam_indicators: JSON list of spam detection reasons

Run with: uv run python scripts/add_quality_fields_migration.py
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from sqlalchemy import create_engine, text

    from config import get_settings
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're running this from the project root with: uv run python scripts/add_quality_fields_migration.py")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_migration():
    """Add quality tracking fields to opportunities table"""

    try:
        settings = get_settings()

        logger.info("Starting quality fields migration...")

        # Use the correct database URL (port 54322 instead of configured 54331)
        database_url = settings.database_url.replace(':54331/', ':54322/')
        logger.info(f"Database URL: {database_url.split('@')[0]}@...")  # Hide credentials

        engine = create_engine(database_url)

        # SQL migration with IF NOT EXISTS for safety
        migration_sql = """
        -- Add AI Quality Assessment fields to opportunities table

        -- Content quality score (0-100, AI-generated)
        ALTER TABLE opportunities
        ADD COLUMN IF NOT EXISTS content_quality_score FLOAT DEFAULT 50.0;

        -- Spam detection flag (AI-identified)
        ALTER TABLE opportunities
        ADD COLUMN IF NOT EXISTS is_spam BOOLEAN DEFAULT FALSE;

        -- Spam indicators list (JSON array of reasons)
        ALTER TABLE opportunities
        ADD COLUMN IF NOT EXISTS spam_indicators TEXT DEFAULT '[]';

        -- Create index for spam filtering (Phase 2+)
        CREATE INDEX IF NOT EXISTS idx_opportunities_is_spam
        ON opportunities(is_spam);

        -- Create index for quality scoring (Phase 2+)
        CREATE INDEX IF NOT EXISTS idx_opportunities_quality_score
        ON opportunities(content_quality_score);

        -- Create composite index for quality + spam filtering (Phase 2+)
        CREATE INDEX IF NOT EXISTS idx_opportunities_quality_spam
        ON opportunities(content_quality_score, is_spam);

        -- Add comments for documentation
        COMMENT ON COLUMN opportunities.content_quality_score IS 'AI-generated content quality score (0-100 scale)';
        COMMENT ON COLUMN opportunities.is_spam IS 'AI-identified spam flag from content analysis';
        COMMENT ON COLUMN opportunities.spam_indicators IS 'JSON array of spam detection reasons and indicators';
        """

        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            try:
                logger.info("Executing migration SQL...")

                # Run the migration
                conn.execute(text(migration_sql))

                # Verify the migration worked
                logger.info("Verifying migration...")
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'opportunities'
                    AND column_name IN ('content_quality_score', 'is_spam', 'spam_indicators')
                    ORDER BY column_name
                """))

                columns = result.fetchall()
                logger.info("Migration verification - new columns:")
                for col in columns:
                    logger.info(f"  ✓ {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")

                # Check indexes
                index_result = conn.execute(text("""
                    SELECT indexname
                    FROM pg_indexes
                    WHERE tablename = 'opportunities'
                    AND indexname LIKE 'idx_opportunities_%'
                    AND indexname IN ('idx_opportunities_is_spam', 'idx_opportunities_quality_score', 'idx_opportunities_quality_spam')
                    ORDER BY indexname
                """))

                indexes = index_result.fetchall()
                logger.info("Migration verification - new indexes:")
                for idx in indexes:
                    logger.info(f"  ✓ {idx[0]}")

                # Commit transaction
                trans.commit()
                logger.info("✅ Migration completed successfully!")

                # Provide migration statistics
                total_result = conn.execute(text("SELECT COUNT(*) as total_records FROM opportunities"))
                total_records = total_result.scalar()
                logger.info(f"📊 Migration affects {total_records} existing records")
                logger.info("   - All existing records will have default values:")
                logger.info("   • content_quality_score = 50.0 (neutral quality)")
                logger.info("   • is_spam = FALSE (not flagged as spam)")
                logger.info("   • spam_indicators = [] (empty list)")

            except Exception as e:
                logger.error(f"Migration failed: {e}")
                trans.rollback()
                raise

    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def verify_migration():
    """Verify the migration was successful by testing database operations"""

    try:
        settings = get_settings()

        # Use the correct database URL (port 54322 instead of configured 54331)
        database_url = settings.database_url.replace(':54331/', ':54322/')
        engine = create_engine(database_url)

        logger.info("Verifying migration with test operations...")

        with engine.connect() as conn:
            # Test that we can query the new fields
            test_sql = """
            SELECT
                COUNT(*) as total_records,
                COUNT(*) FILTER (WHERE is_spam = TRUE) as spam_count,
                AVG(content_quality_score) as avg_quality,
                COUNT(*) FILTER (WHERE spam_indicators IS NOT NULL AND spam_indicators != '[]') as has_indicators
            FROM opportunities
            """

            result = conn.execute(text(test_sql)).fetchone()

            if result:
                total, spam_count, avg_quality, has_indicators = result
                logger.info("✅ Migration verification successful:")
                logger.info(f"   • Total records: {total}")
                logger.info(f"   • Spam records: {spam_count}")
                if avg_quality is not None:
                    logger.info(f"   • Average quality: {avg_quality:.1f}")
                else:
                    logger.info("   • Average quality: N/A (no records)")
                logger.info(f"   • Records with indicators: {has_indicators}")

                # Test a sample query that would use the new indexes
                logger.info("Testing quality filtering query...")
                quality_test = conn.execute(text("""
                    SELECT content_quality_score, is_spam, title
                    FROM opportunities
                    WHERE content_quality_score >= 80
                    AND is_spam = FALSE
                    LIMIT 5
                """)).fetchall()

                logger.info(f"   • High-quality non-spam records (quality ≥80): {len(quality_test)}")

                return True
            else:
                logger.warning("⚠️  Could not verify migration - no data returned")
                return False

    except Exception as e:
        logger.error(f"Migration verification failed: {e}")
        return False

if __name__ == "__main__":
    try:
        run_migration()

        logger.info("\n" + "="*60)
        logger.info("🎯 Running post-migration verification...")
        logger.info("="*60)

        if verify_migration():
            logger.info("\n✅ All verifications passed! Database ready for Phase 2+ AI quality filtering.")
            logger.info("\n📋 Next steps:")
            logger.info("   1. Update application code to use new quality fields")
            logger.info("   2. Test AI quality scoring with real data")
            logger.info("   3. Monitor quality filtering statistics")
            logger.info("   4. Consider data retention policies for low-quality content")
        else:
            logger.error("\n❌ Migration verification failed! Please check the database.")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\n⚠️  Migration cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ Migration failed with error: {e}")
        sys.exit(1)
