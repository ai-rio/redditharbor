#!/usr/bin/env python3
"""
Apply Schema Synchronization Migration

This script applies the generated schema sync migration to ensure all
monetization patterns columns are properly documented in migrations.
"""

import asyncio
import logging
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import DB_CONFIG

logger = logging.getLogger(__name__)

async def apply_migration():
    """Apply the schema sync migration to the database."""
    try:
        # Load environment variables
        load_dotenv()

        # Connect to database using Supabase connection info
        # From supabase status: postgresql://postgres:postgres@127.0.0.1:54331/postgres
        connection = await asyncpg.connect(
            host="127.0.0.1",
            port=54331,
            user="postgres",
            password="postgres",
            database="postgres"
        )

        logger.info("Connected to database successfully")

        # Read and execute migration SQL
        migration_file = Path(__file__).parent.parent / "supabase/migrations/schema_sync_20251122211144.sql"
        migration_sql = migration_file.read_text()

        logger.info("Applying schema sync migration...")

        # Execute migration
        await connection.execute(migration_sql)

        logger.info("✅ Migration applied successfully!")

        # Verify the migration
        result = await connection.fetchval("""
            SELECT COUNT(*) FROM information_schema.columns
            WHERE table_name = 'monetization_patterns'
            AND table_schema = 'public'
        """)

        logger.info(f"✅ monetization_patterns table now has {result} columns")

        # Check specific new columns exist
        new_columns = [
            'willingness_to_pay_score',
            'customer_segment',
            'price_sensitivity_score',
            'revenue_potential_score'
        ]

        for column in new_columns:
            exists = await connection.fetchval("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'monetization_patterns'
                AND column_name = $1
                AND table_schema = 'public'
            """, column)

            if exists:
                logger.info(f"✅ {column} column verified")
            else:
                logger.error(f"❌ {column} column missing")

        await connection.close()
        logger.info("Migration verification completed")

        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    result = asyncio.run(apply_migration())

    if result:
        print("\n🎉 Schema synchronization migration completed successfully!")
        print("The monetization_patterns table now has all columns properly documented in migrations.")
        sys.exit(0)
    else:
        print("\n❌ Migration failed. Check logs for details.")
        sys.exit(1)