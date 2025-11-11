#!/usr/bin/env python3
"""
Migration Runner for RedditHarbor Monetizable App Research Schema
Applies all migration files in order to the Supabase database
"""

import sys
from pathlib import Path

import psycopg2

# Database connection parameters
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 54322,
    'database': 'postgres',
    'user': 'postgres',
    'password': 'postgres'
}

def apply_migration(sql_file_path):
    """Apply a single migration file"""
    try:
        with open(sql_file_path) as f:
            sql = f.read()

        # Split SQL into individual statements
        # Remove comment lines and split on semicolons
        statements = []
        current_statement = []

        for line in sql.split('\n'):
            # Skip pure comment lines and migration log inserts
            if line.strip().startswith('--') or 'INSERT INTO _migrations_log' in line:
                continue

            current_statement.append(line)

            # Split on semicolons, but not inside dollar-quoted strings
            if line.strip().endswith(';') and not line.strip().startswith("'"):
                stmt = '\n'.join(current_statement).strip()
                if stmt and not stmt.isspace():
                    statements.append(stmt)
                current_statement = []

        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cur = conn.cursor()

        # Execute each statement
        executed_count = 0
        for statement in statements:
            if statement.strip():
                try:
                    cur.execute(statement)
                    executed_count += 1
                    print(f"  ✓ Executed statement {executed_count}")
                except Exception as e:
                    # Check if it's a "already exists" error or similar benign error
                    if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                        print(f"  ⚠ Skipped (already exists): {str(e)[:80]}")
                    else:
                        print(f"  ✗ Error: {str(e)[:200]}")
                        raise

        conn.commit()
        cur.close()
        conn.close()

        print(f"✓ Migration applied successfully ({executed_count} statements)")
        return True

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def main():
    """Apply all migrations in order"""
    migrations_dir = Path(__file__).parent

    # Get all migration files and sort them
    migration_files = sorted([
        f for f in migrations_dir.glob('*.sql')
        if f.name != 'apply_migrations.py'
    ])

    if not migration_files:
        print("No migration files found!")
        return 1

    print(f"Found {len(migration_files)} migration files")
    print("=" * 70)

    success_count = 0
    fail_count = 0

    for migration_file in migration_files:
        print(f"\nApplying: {migration_file.name}")
        print("-" * 70)

        if apply_migration(migration_file):
            success_count += 1
        else:
            fail_count += 1
            print(f"\n⚠️  Failed to apply {migration_file.name}")
            # Continue with next migration even if one fails

    print("\n" + "=" * 70)
    print(f"Migration Summary: {success_count} succeeded, {fail_count} failed")

    if fail_count == 0:
        print("✓ All migrations applied successfully!")
        return 0
    else:
        print(f"⚠️  {fail_count} migration(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
