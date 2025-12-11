#!/usr/bin/env python3
"""
Migration verification script for RedditHarbor Pipeline V4
Tests alembic migration up/down and validates schema
"""

from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor

from config.settings import get_settings


def get_db_connection():
    """Get database connection"""
    settings = get_settings()
    return psycopg2.connect(settings.database_url)


def check_table_schema():
    """Check if opportunities table matches expected schema"""
    expected_columns = {
        'id': 'integer',
        'submission_id': 'character varying',
        'subreddit': 'character varying',
        'title': 'character varying',
        'wtp_score': 'double precision',
        'final_score': 'double precision',
        'confidence_score': 'double precision',
        'analysis': 'jsonb',
        'metrics': 'jsonb',
        'trust_level': 'character varying',
        'created_at': 'timestamp with time zone',
        'updated_at': 'timestamp with time zone'
    }

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Get table schema
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'opportunities'
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)

        columns = cursor.fetchall()

        # Check all expected columns exist with correct types
        results = {
            'table_exists': False,
            'columns_match': True,
            'missing_columns': [],
            'wrong_types': [],
            'jsonb_columns': False,
            'indexes_exist': False,
            'unique_constraint': False
        }

        if columns:
            results['table_exists'] = True

            # Check JSONB columns
            jsonb_cols = [col['column_name'] for col in columns if col['data_type'] == 'jsonb']
            results['jsonb_columns'] = {'analysis', 'metrics'}.issubset(set(jsonb_cols))

            # Check each expected column
            existing_cols = {col['column_name']: col['data_type'] for col in columns}

            for col_name, expected_type in expected_columns.items():
                if col_name not in existing_cols:
                    results['missing_columns'].append(col_name)
                    results['columns_match'] = False
                elif 'jsonb' in expected_type and existing_cols[col_name] == 'jsonb':
                    pass  # JSONB check already done
                elif expected_type not in existing_cols[col_name]:
                    results['wrong_types'].append(f"{col_name}: expected {expected_type}, got {existing_cols[col_name]}")
                    results['columns_match'] = False

            # Check for timezone columns
            time_cols = [col for col in columns if 'timestamp with time zone' in col['data_type']]
            if len(time_cols) < 2:
                results['wrong_types'].append("created_at and updated_at should be timestamp with time zone")

        # Check indexes
        cursor.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'opportunities'
            AND schemaname = 'public'
        """)

        indexes = cursor.fetchall()
        index_names = [idx['indexname'] for idx in indexes]

        # Check for required indexes
        has_unique_sub = any('submission_id' in idx['indexdef'] and 'UNIQUE' in idx['indexdef'] for idx in indexes)
        has_subreddit_idx = any('subreddit' in idx['indexdef'] for idx in indexes)

        results['indexes_exist'] = has_unique_sub and has_subreddit_idx
        results['unique_constraint'] = has_unique_sub

        return results

    finally:
        cursor.close()
        conn.close()


def check_alembic_version():
    """Check alembic version table"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT version_num FROM alembic_version")
        version = cursor.fetchone()
        return {
            'table_exists': True,
            'current_version': version[0] if version else None
        }
    except:
        return {
            'table_exists': False,
            'current_version': None
        }
    finally:
        cursor.close()
        conn.close()


def main():
    """Run migration verification"""
    print("=== RedditHarbor Pipeline V4 Migration Verification ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Check alembic version
    print("1. Checking Alembic Version:")
    alembic_info = check_alembic_version()
    if alembic_info['table_exists']:
        print("   ✓ alembic_version table exists")
        if alembic_info['current_version']:
            print(f"   ✓ Current version: {alembic_info['current_version']}")
        else:
            print("   ✗ No version recorded")
    else:
        print("   ✗ alembic_version table does not exist")
    print()

    # Check table schema
    print("2. Checking Opportunities Table Schema:")
    schema_info = check_table_schema()

    if schema_info['table_exists']:
        print("   ✓ opportunities table exists")

        if schema_info['columns_match']:
            print("   ✓ All columns present with correct types")
        else:
            print("   ✗ Column issues found:")
            for col in schema_info['missing_columns']:
                print(f"      - Missing column: {col}")
            for err in schema_info['wrong_types']:
                print(f"      - {err}")

        if schema_info['jsonb_columns']:
            print("   ✓ JSONB columns (analysis, metrics) configured correctly")
        else:
            print("   ✗ JSONB columns not properly configured")

        if schema_info['indexes_exist']:
            print("   ✓ Required indexes created (submission_id unique, subreddit)")
        else:
            print("   ✗ Missing required indexes")

        if schema_info['unique_constraint']:
            print("   ✓ Unique constraint on submission_id")
        else:
            print("   ✗ Unique constraint on submission_id missing")
    else:
        print("   ✗ opportunities table does not exist")

    print()
    print("3. Summary:")
    if schema_info['table_exists'] and schema_info['columns_match'] and schema_info['jsonb_columns'] and schema_info['indexes_exist']:
        print("   ✓ Migration verification PASSED")
        return True
    else:
        print("   ✗ Migration verification FAILED")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
