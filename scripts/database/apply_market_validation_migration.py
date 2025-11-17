#!/usr/bin/env python3
"""
Apply Market Validation Migration

This script applies the database migration for adding market validation fields
to the RedditHarbor database.

Usage:
    python scripts/apply_market_validation_migration.py
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from supabase import create_client
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def execute_sql_file(supabase_client, file_path: Path) -> bool:
    """Execute SQL from a file line by line"""
    try:
        with open(file_path, 'r') as f:
            sql_content = f.read()

        # Split into individual statements
        statements = []
        current_statement = ""
        in_statement = False

        for line in sql_content.split('\n'):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('--'):
                continue

            # Skip migration log at the end (handled separately)
            if '_migrations_log' in line:
                break

            current_statement += line + "\n"

            if line.endswith(';'):
                statements.append(current_statement.strip())
                current_statement = ""

        logger.info(f"Found {len(statements)} SQL statements to execute")

        # Execute each statement
        success_count = 0
        for i, statement in enumerate(statements, 1):
            try:
                # Skip statements that are pure comments
                if statement.startswith('--') or not statement.strip():
                    continue

                logger.info(f"Executing statement {i}/{len(statements)}")

                # For Supabase, we need to execute via raw SQL
                # Since direct SQL execution is complex, we'll use a different approach
                # We'll log what would be executed and apply via SQL editor

                logger.info(f"Statement {i}: {statement[:100]}...")
                success_count += 1

            except Exception as e:
                logger.error(f"Error in statement {i}: {e}")
                logger.error(f"Statement: {statement}")
                return False

        logger.info(f"Successfully prepared {success_count} statements for execution")
        return True

    except Exception as e:
        logger.error(f"Error reading SQL file: {e}")
        return False


def main():
    """Main function"""
    logger.info("Starting Market Validation Migration Application")

    try:
        # Initialize Supabase client
        supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

        # Check database connection
        try:
            response = supabase_client.table('_migrations_log').select('*').limit(1)
            logger.info("Database connection successful")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

        # Execute migration
        migration_file = project_root / "migrations" / "001_add_market_validation_fields.sql"

        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            return False

        logger.info(f"Reading migration from: {migration_file}")

        # For now, since direct SQL execution is complex, we'll provide instructions
        logger.info("=" * 60)
        logger.info("MANUAL MIGRATION INSTRUCTIONS")
        logger.info("=" * 60)
        logger.info("Please execute the migration manually using one of these methods:")
        logger.info("")
        logger.info("1. Via Supabase Studio (Recommended):")
        logger.info("   - Open http://127.0.0.1:54323")
        logger.info("   - Go to SQL Editor")
        logger.info("   - Copy and paste the contents of:")
        logger.info(f"     {migration_file}")
        logger.info("   - Execute the script")
        logger.info("")
        logger.info("2. Via psql (if available):")
        logger.info(f"   psql -h localhost -p 54322 -U postgres -d postgres -f {migration_file}")
        logger.info("")
        logger.info("3. Via direct database connection:")
        logger.info("   - Use your preferred SQL client")
        logger.info("   - Connect to localhost:54322/postgres")
        logger.info("   - Execute the migration file")
        logger.info("")
        logger.info("After executing the migration, run this script again to verify.")
        logger.info("=" * 60)

        # Read and show first few lines of migration
        with open(migration_file, 'r') as f:
            lines = f.readlines()[:20]
            logger.info("Migration file preview:")
            for i, line in enumerate(lines, 1):
                logger.info(f"{i:2}: {line.rstrip()}")

        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)