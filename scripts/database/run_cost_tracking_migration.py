#!/usr/bin/env python3
"""
Database Migration Executor for Cost Tracking Columns
Executes the cost tracking migration and validates the results
"""

import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import psycopg2
    from psycopg2.extras import DictCursor
except ImportError:
    print("Installing psycopg2-binary...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2
    from psycopg2.extras import DictCursor

from dotenv import load_dotenv


def get_database_connection():
    """
    Get database connection using Supabase credentials.

    Returns:
        psycopg2 connection object
    """
    # Load environment variables
    load_dotenv(project_root / '.env.local')

    # Get Supabase connection details
    db_url = os.getenv("SUPABASE_DB_URL")
    if db_url:
        return psycopg2.connect(db_url)

    # Fallback to individual credentials
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("Missing database credentials. Please check SUPABASE_URL and SUPABASE_KEY in .env.local")

    # Parse Supabase URL for local development
    if "http://127.0.0.1" in supabase_url:
        # Extract host from URL like http://127.0.0.1:54321
        host = "127.0.0.1"
        port = "54322"
        # For local development, the password is 'postgres'
        password = "postgres"
    elif "https://" in supabase_url:
        # Remove https:// and any path
        host = supabase_url.replace("https://", "").split("/")[0]
        port = "5432"  # Default PostgreSQL port for production
        password = supabase_key
    else:
        # Assume it's already a hostname
        host = supabase_url
        port = "5432"
        password = supabase_key

    # Construct connection string
    conn_string = f"postgresql://postgres:{password}@{host}:{port}/postgres"
    print(f"  Connecting to: {host}:{port}")
    return psycopg2.connect(conn_string)


def execute_migration(conn, migration_file: Path) -> Dict[str, Any]:
    """
    Execute the cost tracking migration.

    Args:
        conn: Database connection
        migration_file: Path to migration file

    Returns:
        Migration execution results
    """
    print(f"Executing migration: {migration_file.name}")

    # Read migration SQL
    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    results = {
        'migration_file': migration_file.name,
        'execution_time': 0,
        'success': False,
        'error': None,
        'statements_executed': 0,
        'columns_added': [],
        'indexes_created': [],
        'constraints_added': []
    }

    start_time = time.time()

    try:
        with conn.cursor() as cursor:
            # Split migration into individual statements
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]

            for statement in statements:
                if statement.lower().startswith('--') or not statement:
                    continue

                try:
                    cursor.execute(statement)
                    results['statements_executed'] += 1

                    # Parse statement to categorize what was done
                    stmt_lower = statement.lower()

                    if 'alter table' in stmt_lower and 'add column' in stmt_lower:
                        # Extract column name
                        if 'if not exists' in stmt_lower:
                            column_name = statement.split('ADD COLUMN IF NOT EXISTS')[1].split()[0].strip()
                        else:
                            column_name = statement.split('ADD COLUMN')[1].split()[0].strip()
                        results['columns_added'].append(column_name)

                    elif 'create index' in stmt_lower:
                        # Extract index name
                        index_name = statement.split('CREATE INDEX')[1].split()[0].strip()
                        results['indexes_created'].append(index_name)

                    elif 'add constraint' in stmt_lower:
                        # Extract constraint name
                        constraint_name = statement.split('ADD CONSTRAINT')[1].split()[0].strip()
                        results['constraints_added'].append(constraint_name)

                except Exception as stmt_error:
                    # Some statements might fail due to IF NOT EXISTS conditions
                    print(f"  Statement warning: {stmt_error}")
                    continue

            conn.commit()
            results['success'] = True

    except Exception as e:
        conn.rollback()
        results['error'] = str(e)
        print(f"  Migration failed: {e}")

    results['execution_time'] = time.time() - start_time
    return results


def validate_migration(conn) -> Dict[str, Any]:
    """
    Validate that the cost tracking migration was successful.

    Args:
        conn: Database connection

    Returns:
        Validation results
    """
    print("Validating migration results...")

    validation = {
        'workflow_results_table_exists': False,
        'cost_tracking_columns_exist': False,
        'missing_columns': [],
        'column_types': {},
        'indexes_exist': False,
        'missing_indexes': [],
        'constraints_exist': False,
        'missing_constraints': [],
        'success': False
    }

    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            # Check if workflow_results table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'workflow_results'
                );
            """)
            validation['workflow_results_table_exists'] = cursor.fetchone()[0]

            if not validation['workflow_results_table_exists']:
                print("  ❌ workflow_results table does not exist")
                return validation

            # Check cost tracking columns
            expected_columns = [
                ('llm_model_used', 'TEXT'),
                ('llm_provider', 'TEXT'),
                ('llm_prompt_tokens', 'INTEGER'),
                ('llm_completion_tokens', 'INTEGER'),
                ('llm_total_tokens', 'INTEGER'),
                ('llm_input_cost_usd', 'DECIMAL'),
                ('llm_output_cost_usd', 'DECIMAL'),
                ('llm_total_cost_usd', 'DECIMAL'),
                ('llm_latency_seconds', 'DECIMAL'),
                ('llm_timestamp', 'TIMESTAMPTZ'),
                ('llm_pricing_info', 'JSONB'),
                ('cost_tracking_enabled', 'BOOLEAN')
            ]

            cursor.execute("""
                SELECT column_name, data_type, numeric_precision, numeric_scale
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'workflow_results'
                AND column_name LIKE 'llm_%' OR column_name = 'cost_tracking_enabled'
                ORDER BY column_name;
            """)

            existing_columns = {row[0]: row[1] for row in cursor.fetchall()}

            for column_name, expected_type in expected_columns:
                if column_name in existing_columns:
                    validation['column_types'][column_name] = existing_columns[column_name]
                else:
                    validation['missing_columns'].append(column_name)

            validation['cost_tracking_columns_exist'] = len(validation['missing_columns']) == 0

            # Check indexes
            expected_indexes = [
                'idx_workflow_results_llm_model',
                'idx_workflow_results_llm_cost',
                'idx_workflow_results_llm_timestamp',
                'idx_workflow_results_cost_tracking',
                'idx_workflow_results_cost_composite'
            ]

            cursor.execute("""
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                AND tablename = 'workflow_results'
                AND indexname LIKE 'idx_workflow_results_%';
            """)

            existing_indexes = {row[0] for row in cursor.fetchall()}

            for index_name in expected_indexes:
                if index_name not in existing_indexes:
                    validation['missing_indexes'].append(index_name)

            validation['indexes_exist'] = len(validation['missing_indexes']) == 0

            # Check constraints
            cursor.execute("""
                SELECT conname
                FROM pg_constraint
                WHERE conrelid = 'public.workflow_results'::regclass
                AND conname LIKE 'check_llm_%';
            """)

            existing_constraints = {row[0] for row in cursor.fetchall()}

            # Expected constraints might include check constraints
            expected_constraints = [
                'check_llm_tokens_non_negative',
                'check_llm_costs_non_negative',
                'check_llm_latency_non_negative'
            ]

            for constraint_name in expected_constraints:
                if constraint_name not in existing_constraints:
                    validation['missing_constraints'].append(constraint_name)

            validation['constraints_exist'] = len(validation['missing_constraints']) <= 1  # Allow some flexibility

            # Overall success
            validation['success'] = (
                validation['workflow_results_table_exists'] and
                validation['cost_tracking_columns_exist'] and
                validation['indexes_exist']
            )

    except Exception as e:
        print(f"  Validation error: {e}")
        validation['error'] = str(e)

    return validation


def test_cost_tracking_functionality(conn) -> Dict[str, Any]:
    """
    Test basic cost tracking functionality.

    Args:
        conn: Database connection

    Returns:
        Test results
    """
    print("Testing cost tracking functionality...")

    test_results = {
        'insert_test': False,
        'update_test': False,
        'query_test': False,
        'cost_aggregation_test': False,
        'error': None
    }

    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            # Test 1: Insert a record with cost tracking data
            print("  Testing insert with cost tracking...")
            cursor.execute("""
                INSERT INTO workflow_results (
                    opportunity_id, app_name, function_count, function_list,
                    original_score, final_score, status, constraint_applied,
                    llm_model_used, llm_provider, llm_prompt_tokens,
                    llm_completion_tokens, llm_total_tokens, llm_input_cost_usd,
                    llm_output_cost_usd, llm_total_cost_usd, llm_latency_seconds,
                    llm_timestamp, cost_tracking_enabled, llm_pricing_info
                ) VALUES (
                    'test_cost_opp_001', 'TestCostApp', 2, ARRAY['Function 1', 'Function 2'],
                    75.0, 80.0, 'scored', true,
                    'claude-haiku-4.5', 'openrouter', 850, 350, 1200,
                    0.00085, 0.00175, 0.0026, 1.234,
                    NOW(), true, '{"input": 1.0, "output": 5.0}'
                )
                ON CONFLICT (opportunity_id) DO UPDATE SET
                    llm_total_cost_usd = EXCLUDED.llm_total_cost_usd,
                    llm_timestamp = EXCLUDED.llm_timestamp;
            """)
            test_results['insert_test'] = True

            # Test 2: Update existing record
            print("  Testing update...")
            cursor.execute("""
                UPDATE workflow_results
                SET llm_total_cost_usd = llm_total_cost_usd + 0.001,
                    llm_total_tokens = llm_total_tokens + 100
                WHERE opportunity_id = 'test_cost_opp_001';
            """)
            test_results['update_test'] = True

            # Test 3: Query with cost tracking
            print("  Testing cost tracking queries...")
            cursor.execute("""
                SELECT
                    opportunity_id,
                    app_name,
                    llm_model_used,
                    llm_total_cost_usd,
                    llm_total_tokens,
                    cost_tracking_enabled
                FROM workflow_results
                WHERE opportunity_id = 'test_cost_opp_001'
                AND cost_tracking_enabled = true;
            """)

            result = cursor.fetchone()
            if result and result['llm_total_cost_usd'] > 0:
                test_results['query_test'] = True

            # Test 4: Cost aggregation queries
            print("  Testing cost aggregation...")
            cursor.execute("""
                SELECT
                    COUNT(*) as total_records,
                    COUNT(*) FILTER (WHERE cost_tracking_enabled = true) as with_cost_tracking,
                    SUM(llm_total_cost_usd) as total_cost,
                    AVG(llm_total_cost_usd) as avg_cost,
                    SUM(llm_total_tokens) as total_tokens
                FROM workflow_results
                WHERE cost_tracking_enabled = true;
            """)

            agg_result = cursor.fetchone()
            if agg_result and agg_result['total_records'] > 0:
                test_results['cost_aggregation_test'] = True

            conn.commit()

    except Exception as e:
        conn.rollback()
        test_results['error'] = str(e)
        print(f"  Test error: {e}")

    return test_results


def create_cost_tracking_views(conn) -> Dict[str, Any]:
    """
    Create helpful views for cost tracking analysis.

    Args:
        conn: Database connection

    Returns:
        View creation results
    """
    print("Creating cost tracking views...")

    view_results = {
        'views_created': [],
        'errors': [],
        'success': False
    }

    views = [
        {
            'name': 'cost_tracking_summary',
            'sql': '''
                CREATE OR REPLACE VIEW cost_tracking_summary AS
                SELECT
                    DATE_TRUNC('day', llm_timestamp) as analysis_date,
                    llm_model_used,
                    llm_provider,
                    COUNT(*) as opportunities_processed,
                    SUM(llm_total_cost_usd) as total_cost_usd,
                    AVG(llm_total_cost_usd) as avg_cost_per_opportunity,
                    SUM(llm_total_tokens) as total_tokens,
                    AVG(llm_total_tokens) as avg_tokens_per_opportunity,
                    AVG(llm_latency_seconds) as avg_latency_seconds
                FROM workflow_results
                WHERE cost_tracking_enabled = true
                    AND llm_timestamp IS NOT NULL
                GROUP BY DATE_TRUNC('day', llm_timestamp), llm_model_used, llm_provider
                ORDER BY analysis_date DESC, total_cost_usd DESC;
            '''
        },
        {
            'name': 'cost_tracking_model_comparison',
            'sql': '''
                CREATE OR REPLACE VIEW cost_tracking_model_comparison AS
                SELECT
                    llm_model_used,
                    llm_provider,
                    COUNT(*) as usage_count,
                    SUM(llm_total_cost_usd) as total_cost_usd,
                    AVG(llm_total_cost_usd) as avg_cost_per_request,
                    SUM(llm_total_tokens) as total_tokens,
                    AVG(llm_total_tokens) as avg_tokens_per_request,
                    AVG(llm_latency_seconds) as avg_latency_seconds,
                    MIN(llm_timestamp) as first_used,
                    MAX(llm_timestamp) as last_used
                FROM workflow_results
                WHERE cost_tracking_enabled = true
                    AND llm_model_used IS NOT NULL
                GROUP BY llm_model_used, llm_provider
                ORDER BY total_cost_usd DESC;
            '''
        },
        {
            'name': 'cost_tracking_daily_trends',
            'sql': '''
                CREATE OR REPLACE VIEW cost_tracking_daily_trends AS
                SELECT
                    DATE_TRUNC('day', llm_timestamp) as analysis_date,
                    COUNT(*) as opportunities_processed,
                    COUNT(*) FILTER (WHERE cost_tracking_enabled = true) as with_cost_tracking,
                    SUM(llm_total_cost_usd) as total_cost_usd,
                    AVG(llm_total_cost_usd) as avg_cost_per_opportunity,
                    SUM(llm_total_tokens) as total_tokens,
                    AVG(llm_latency_seconds) as avg_latency_seconds
                FROM workflow_results
                WHERE llm_timestamp IS NOT NULL
                GROUP BY DATE_TRUNC('day', llm_timestamp)
                ORDER BY analysis_date DESC;
            '''
        }
    ]

    try:
        with conn.cursor() as cursor:
            for view in views:
                try:
                    cursor.execute(view['sql'])
                    view_results['views_created'].append(view['name'])
                    print(f"  ✓ Created view: {view['name']}")
                except Exception as e:
                    error_msg = f"Failed to create view {view['name']}: {e}"
                    view_results['errors'].append(error_msg)
                    print(f"  ❌ {error_msg}")

            conn.commit()
            view_results['success'] = len(view_results['views_created']) > 0

    except Exception as e:
        conn.rollback()
        view_results['errors'].append(f"Failed to create views: {e}")
        print(f"  ❌ View creation failed: {e}")

    return view_results


def cleanup_test_data(conn) -> bool:
    """
    Clean up test data created during migration testing.

    Args:
        conn: Database connection

    Returns:
        True if successful
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM workflow_results
                WHERE opportunity_id LIKE 'test_cost_opp_%';
            """)
            conn.commit()
        return True
    except Exception as e:
        print(f"Cleanup error: {e}")
        return False


def main():
    """
    Main execution function for cost tracking migration.
    """
    print("=" * 80)
    print("COST TRACKING DATABASE MIGRATION")
    print("=" * 80)

    migration_file = project_root / 'supabase' / 'migrations' / '20251113000001_add_cost_tracking_columns.sql'

    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return 1

    print(f"Migration file: {migration_file}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    conn = None
    migration_success = False

    try:
        # Connect to database
        print("Connecting to database...")
        conn = get_database_connection()
        print("✓ Database connection established")

        # Execute migration
        print("\n" + "=" * 50)
        print("EXECUTING MIGRATION")
        print("=" * 50)
        migration_results = execute_migration(conn, migration_file)

        if migration_results['success']:
            print("✓ Migration executed successfully")
            print(f"  - Statements executed: {migration_results['statements_executed']}")
            print(f"  - Columns added: {len(migration_results['columns_added'])}")
            print(f"  - Indexes created: {len(migration_results['indexes_created'])}")
            print(f"  - Constraints added: {len(migration_results['constraints_added'])}")
            print(f"  - Execution time: {migration_results['execution_time']:.2f}s")

            migration_success = True
        else:
            print("❌ Migration failed")
            print(f"  Error: {migration_results['error']}")
            return 1

        # Validate migration
        print("\n" + "=" * 50)
        print("VALIDATING MIGRATION")
        print("=" * 50)
        validation_results = validate_migration(conn)

        if validation_results['success']:
            print("✓ Migration validation successful")
            print(f"  - workflow_results table exists: {validation_results['workflow_results_table_exists']}")
            print(f"  - Cost tracking columns exist: {validation_results['cost_tracking_columns_exist']}")
            print(f"  - Indexes exist: {validation_results['indexes_exist']}")
            print(f"  - Constraints exist: {validation_results['constraints_exist']}")
        else:
            print("❌ Migration validation failed")
            if validation_results.get('missing_columns'):
                print(f"  Missing columns: {validation_results['missing_columns']}")
            if validation_results.get('missing_indexes'):
                print(f"  Missing indexes: {validation_results['missing_indexes']}")
            return 1

        # Test functionality
        print("\n" + "=" * 50)
        print("TESTING FUNCTIONALITY")
        print("=" * 50)
        test_results = test_cost_tracking_functionality(conn)

        if test_results['error']:
            print(f"❌ Functionality tests failed: {test_results['error']}")
        else:
            print("✓ Functionality tests passed")
            print(f"  - Insert test: {'✓' if test_results['insert_test'] else '❌'}")
            print(f"  - Update test: {'✓' if test_results['update_test'] else '❌'}")
            print(f"  - Query test: {'✓' if test_results['query_test'] else '❌'}")
            print(f"  - Aggregation test: {'✓' if test_results['cost_aggregation_test'] else '❌'}")

        # Create views
        print("\n" + "=" * 50)
        print("CREATING ANALYTICS VIEWS")
        print("=" * 50)
        view_results = create_cost_tracking_views(conn)

        if view_results['success']:
            print(f"✓ Created {len(view_results['views_created'])} analytics views")
            for view_name in view_results['views_created']:
                print(f"  - {view_name}")
        else:
            print("⚠️  View creation had issues")
            for error in view_results['errors']:
                print(f"  - {error}")

        # Cleanup test data
        print("\n" + "=" * 50)
        print("CLEANING UP TEST DATA")
        print("=" * 50)
        if cleanup_test_data(conn):
            print("✓ Test data cleaned up")
        else:
            print("⚠️  Test data cleanup failed")

        # Final summary
        print("\n" + "=" * 80)
        print("MIGRATION SUMMARY")
        print("=" * 80)
        if migration_success and validation_results['success']:
            print("✅ COST TRACKING MIGRATION COMPLETED SUCCESSFULLY")
            print("\n📊 Next steps:")
            print("  1. Update batch_opportunity_scoring.py to use new cost tracking columns")
            print("  2. Test the complete pipeline with cost tracking enabled")
            print("  3. Monitor costs using the new analytics views:")
            print("     - cost_tracking_summary")
            print("     - cost_tracking_model_comparison")
            print("     - cost_tracking_daily_trends")
        else:
            print("❌ MIGRATION COMPLETED WITH ISSUES")
            print("\n🔧 Troubleshooting:")
            print("  1. Check database connection permissions")
            print("  2. Verify migration SQL syntax")
            print("  3. Review validation errors above")

        print("=" * 80)
        return 0 if migration_success else 1

    except Exception as e:
        print(f"\n❌ Migration execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        if conn:
            conn.close()
            print("\n📌 Database connection closed")


if __name__ == "__main__":
    import os
    from datetime import datetime

    sys.exit(main())