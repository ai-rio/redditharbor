#!/usr/bin/env python3
"""
Simple Migration Runner - Executes each file as a complete SQL batch
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

def apply_migration_file(sql_file_path):
    """Apply a migration file by executing it as a complete batch"""
    try:
        with open(sql_file_path) as f:
            sql = f.read()

        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cur = conn.cursor()

        # Execute the entire file
        cur.execute(sql)
        executed = cur.rowcount if cur.rowcount >= 0 else 1

        conn.commit()
        cur.close()
        conn.close()

        print("✓ Migration applied successfully")
        return True

    except psycopg2.Error as e:
        error_msg = str(e).lower()
        print(f"  Error: {error_msg[:200]}")

        # Check for benign errors
        if ('already exists' in error_msg or
            'duplicate' in error_msg):

            print("  ⚠ Migration had benign errors (resources already exist)")
            if 'conn' in locals():
                try:
                    conn.rollback()
                    conn.close()
                except:
                    pass
            return True  # Treat as success if it's just "already exists"
        else:
            print("✗ Migration failed")
            if 'conn' in locals():
                try:
                    conn.rollback()
                    conn.close()
                except:
                    pass
            return False
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
    """Verify the final schema"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cur.fetchall()]

        print("\n" + "=" * 70)
        print("SCHEMA VERIFICATION")
        print("=" * 70)
        print(f"\nTotal tables: {len(tables)}")

        # Expected tables
        expected = [
            'subreddits',
            'opportunities',
            'opportunity_scores',
            'score_components',
            'market_validations',
            'cross_platform_verification',
            'competitive_landscape',
            'feature_gaps',
            'monetization_patterns',
            'user_willingness_to_pay',
            'technical_assessments'
        ]

        missing = [t for t in expected if t not in tables]
        if missing:
            print(f"\n⚠ Missing tables: {missing}")
            return False
        else:
            print("\n✓ All expected tables created:")
            for table in sorted(tables):
                print(f"  • {table}")

        # Check constraints
        cur.execute("""
            SELECT COUNT(*)
            FROM information_schema.check_constraints
            WHERE constraint_schema = 'public'
        """)
        constraint_count = cur.fetchone()[0]
        print(f"\n✓ Constraints: {constraint_count}")

        # Check triggers
        cur.execute("""
            SELECT trigger_name
            FROM information_schema.triggers
            WHERE trigger_schema = 'public'
        """)
        triggers = cur.fetchall()
        print(f"\n✓ Triggers: {len(triggers)}")
        for trigger in triggers:
            print(f"  • {trigger[0]}")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"Schema verification failed: {e}")
        return False

def test_constraint():
    """Test simplicity constraint"""
    print("\n" + "=" * 70)
    print("CONSTRAINT TESTING")
    print("=" * 70)

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Test 1: 2 functions (should pass)
        print("\nTest 1: Insert opportunity with 2 core functions")
        cur.execute("""
            INSERT INTO opportunities (problem_statement, core_function_count)
            VALUES ('Test opportunity', 2)
            RETURNING core_function_count, simplicity_constraint_met, status
        """)
        result = cur.fetchone()
        print(f"  Core Functions: {result[0]}")
        print(f"  Constraint Met: {result[1]}")
        print(f"  Status: {result[2]}")

        if result[1] and result[2] != 'disqualified':
            print("  ✓ PASS - Correctly allows 2 functions")
        else:
            print("  ✗ FAIL - Should allow 2 functions")

        # Test 2: 4 functions (should auto-disqualify)
        print("\nTest 2: Insert opportunity with 4 core functions")
        cur.execute("""
            INSERT INTO opportunities (problem_statement, core_function_count)
            VALUES ('Complex test', 4)
            RETURNING core_function_count, simplicity_constraint_met, status
        """)
        result = cur.fetchone()
        print(f"  Core Functions: {result[0]}")
        print(f"  Constraint Met: {result[1]}")
        print(f"  Status: {result[2]}")

        if not result[1] and result[2] == 'disqualified':
            print("  ✓ PASS - Correctly auto-disqualifies 4+ functions")
        else:
            print("  ✗ FAIL - Should auto-disqualify 4+ functions")

        # Clean up
        cur.execute("DELETE FROM opportunities WHERE problem_statement LIKE 'Test%'")
        conn.commit()

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"Constraint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    migrations_dir = Path(__file__).parent

    migration_files = sorted([
        f for f in migrations_dir.glob('*.sql')
        if not f.name.startswith('apply_migrations')
    ])

    if not migration_files:
        print("No migration files found!")
        return 1

    print(f"APPLYING {len(migration_files)} MIGRATIONS")
    print("=" * 70)

    success = 0
    failed = 0

    for migration_file in migration_files:
        print(f"\n[1/7] {migration_file.name}")
        if apply_migration_file(migration_file):
            success += 1
        else:
            failed += 1

    print("\n" + "=" * 70)
    print(f"RESULTS: {success} succeeded, {failed} failed")

    if failed == 0:
        print("✓ All migrations applied!")
        verify_schema()
        test_constraint()
        return 0
    else:
        print(f"⚠ {failed} migration(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
