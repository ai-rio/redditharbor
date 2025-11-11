#!/usr/bin/env python3
"""
Improved Migration Runner for RedditHarbor Monetizable App Research Schema
Properly handles DO blocks and dollar-quoted strings
"""

import re
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

def extract_sql_statements(sql_content):
    """
    Extract SQL statements, handling:
    - DO blocks with dollar-quoted strings
    - Regular statements separated by semicolons
    - Multi-line statements
    """
    statements = []

    # Handle DO blocks - match from DO $$ to END;
    do_pattern = r'DO\s*\$\$[\s\S]*?END;'
    do_matches = list(re.finditer(do_pattern, sql_content, re.MULTILINE))

    # Extract DO blocks
    for match in do_matches:
        statements.append(match.group(0).strip())

    # Remove DO blocks from content
    remaining = re.sub(do_pattern, '', sql_content, flags=re.MULTILINE)

    # Split remaining content by semicolons
    current_statement = []
    in_string = False
    string_char = None

    for line in remaining.split('\n'):
        stripped = line.strip()

        # Skip pure comment lines and migration log inserts
        if stripped.startswith('--') or 'INSERT INTO _migrations_log' in line:
            continue

        current_statement.append(line)

        # Check if line ends with semicolon (not inside a string)
        if not in_string and stripped.endswith(';'):
            stmt = '\n'.join(current_statement).strip()
            if stmt and not stmt.isspace():
                statements.append(stmt)
            current_statement = []

        # Track string state
        for char in ['"', "'"]:
            if stripped.count(char) % 2 == 1:
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None

    return [s for s in statements if s.strip()]

def apply_migration(sql_file_path):
    """Apply a single migration file"""
    try:
        with open(sql_file_path) as f:
            sql = f.read()

        # Extract statements
        statements = extract_sql_statements(sql)

        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cur = conn.cursor()

        # Execute each statement
        executed_count = 0
        skipped_count = 0

        for statement in statements:
            if statement.strip():
                try:
                    cur.execute(statement)
                    executed_count += 1
                    print(f"  ✓ Statement {executed_count}")
                except Exception as e:
                    error_msg = str(e).lower()
                    # Check for benign errors
                    if ('already exists' in error_msg or
                        'duplicate' in error_msg or
                        'does not exist' in error_msg or
                        'undefined_table' in error_msg):
                        skipped_count += 1
                        print(f"  ⚠ Skipped: {str(e)[:100]}")
                    else:
                        print("  ✗ Error executing statement:")
                        print(f"     {str(e)[:200]}")
                        print(f"\n     Statement preview: {statement[:200]}...")
                        raise

        conn.commit()
        cur.close()
        conn.close()

        total = executed_count + skipped_count
        if total > 0:
            print(f"✓ Migration complete ({executed_count} executed, {skipped_count} skipped)")
        else:
            print("✓ Migration complete (no statements to execute)")

        return True

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        if 'conn' in locals():
            try:
                conn.rollback()
                conn.close()
            except:
                pass
        return False

def verify_schema():
    """Verify the final schema after all migrations"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Get all tables
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cur.fetchall()]

        print("\n" + "=" * 70)
        print("Schema Verification")
        print("=" * 70)
        print(f"Total tables: {len(tables)}")
        print("\nTables created:")
        for table in tables:
            print(f"  ✓ {table}")

        # Check for key tables
        key_tables = [
            'subreddits', 'opportunities', 'opportunity_scores',
            'market_validations', 'competitive_landscape', 'monetization_patterns'
        ]

        missing = [t for t in key_tables if t not in tables]
        if missing:
            print(f"\n⚠ Missing key tables: {missing}")
        else:
            print("\n✓ All key tables present")

        # Check for constraints
        cur.execute("""
            SELECT constraint_name
            FROM information_schema.check_constraints
            WHERE constraint_schema = 'public'
        """)
        constraints = [row[0] for row in cur.fetchall()]

        print(f"\nConstraints: {len(constraints)}")
        simplicity_constraints = [c for c in constraints if 'simplicity' in c.lower() or 'function_count' in c.lower()]
        if simplicity_constraints:
            print(f"✓ Simplicity constraints: {len(simplicity_constraints)}")
            for c in simplicity_constraints:
                print(f"  - {c}")

        # Check for triggers
        cur.execute("""
            SELECT trigger_name
            FROM information_schema.triggers
            WHERE trigger_schema = 'public'
        """)
        triggers = [row[0] for row in cur.fetchall()]

        print(f"\nTriggers: {len(triggers)}")
        if triggers:
            for t in triggers:
                print(f"  - {t}")

        cur.close()
        conn.close()

        return len(missing) == 0

    except Exception as e:
        print(f"Schema verification failed: {e}")
        return False

def test_simplicity_constraint():
    """Test the simplicity constraint trigger"""
    print("\n" + "=" * 70)
    print("Testing Simplicity Constraint")
    print("=" * 70)

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Create a test opportunity with 2 functions (should pass)
        cur.execute("""
            INSERT INTO opportunities (problem_statement, core_function_count)
            VALUES ('Test with 2 functions', 2)
            RETURNING id, core_function_count, simplicity_constraint_met, status
        """)
        result = cur.fetchone()
        print("\nTest 1 - 2 Functions:")
        print(f"  Core Functions: {result[1]}")
        print(f"  Constraint Met: {result[2]}")
        print(f"  Status: {result[3]}")
        print("  ✓ PASS" if result[2] and result[3] != 'disqualified' else "  ✗ FAIL")

        # Test with 4 functions (should auto-disqualify)
        cur.execute("""
            INSERT INTO opportunities (problem_statement, core_function_count)
            VALUES ('Test with 4 functions', 4)
            RETURNING id, core_function_count, simplicity_constraint_met, status
        """)
        result = cur.fetchone()
        print("\nTest 2 - 4 Functions (Auto-Disqualify):")
        print(f"  Core Functions: {result[1]}")
        print(f"  Constraint Met: {result[2]}")
        print(f"  Status: {result[3]}")
        print("  ✓ PASS" if not result[2] and result[3] == 'disqualified' else "  ✗ FAIL")

        # Clean up test data
        cur.execute("DELETE FROM opportunities WHERE problem_statement LIKE 'Test with%'")
        conn.commit()

        cur.close()
        conn.close()

        return True

    except Exception as e:
        print(f"Constraint test failed: {e}")
        return False

def main():
    """Apply all migrations in order"""
    migrations_dir = Path(__file__).parent

    # Get all migration files and sort them
    migration_files = sorted([
        f for f in migrations_dir.glob('*.sql')
        if not f.name.startswith('apply_migrations')
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

    print("\n" + "=" * 70)
    print(f"Migration Summary: {success_count} succeeded, {fail_count} failed")

    if fail_count == 0:
        print("✓ All migrations applied successfully!")
        # Run verification
        if verify_schema():
            print("\n" + "=" * 70)
            print("Running constraint tests...")
            test_simplicity_constraint()
        return 0
    else:
        print(f"⚠️  {fail_count} migration(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
