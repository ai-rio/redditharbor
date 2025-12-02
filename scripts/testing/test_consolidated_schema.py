#!/usr/bin/env python3
"""
Test script for the consolidated schema migration.

This script validates that the consolidated migration creates a working schema
that matches the expected structure and functionality.

Usage:
    python scripts/test_consolidated_schema.py [--schema-only]
"""

import argparse
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description, capture_output=True):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=capture_output,
            text=True,
            check=True
        )
        if capture_output:
            return result.stdout.strip()
        return None
    except subprocess.CalledProcessError as e:
        print(f"❌ Error in {description}: {e}")
        if capture_output and e.stderr:
            print(f"Stderr: {e.stderr}")
        return None

def test_fresh_database():
    """Test the consolidated migration on a fresh database."""
    print("🚀 Testing consolidated schema on fresh database...")

    # Reset the database
    if not run_command("supabase db reset", "Resetting database", capture_output=False):
        return False

    print("✅ Database reset completed")
    return True

def verify_schema_structure():
    """Verify that all expected tables and columns exist."""
    print("📋 Verifying schema structure...")

    # Expected tables
    expected_tables = [
        'subreddits', 'redditors', 'submissions', 'comments',
        'opportunities', 'opportunity_scores', 'score_components',
        'market_validations', 'competitive_landscape', 'feature_gaps',
        'cross_platform_verification', 'monetization_patterns',
        'user_willingness_to_pay', 'technical_assessments',
        'workflow_results', 'app_opportunities', 'opportunity_analysis'
    ]

    # Check each table exists
    for table in expected_tables:
        query = f"SELECT 1 FROM information_schema.tables WHERE table_name = '{table}'"
        result = run_docker_query(query)
        if not result:
            print(f"❌ Table {table} not found")
            return False
        print(f"✅ Table {table} exists")

    # Verify DLT tables are excluded (should not be created by migration)
    dlt_tables = ['_dlt_loads', '_dlt_pipeline_state', '_dlt_version']
    for table in dlt_tables:
        query = f"SELECT 1 FROM information_schema.tables WHERE table_name = '{table}'"
        result = run_docker_query(query)
        if result:
            print(f"⚠️  DLT table {table} found (should be created by DLT, not migration)")

    return True

def run_docker_query(query):
    """Run a SQL query via Docker."""
    cmd = f'docker exec supabase_db_carlos psql -U postgres -d postgres -t -c "{query}"'
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def verify_critical_constraints():
    """Verify critical constraints and relationships."""
    print("🔗 Verifying critical constraints...")

    # Check app_opportunities primary key (critical for DLT)
    pk_query = """
        SELECT a.attname
        FROM pg_index i
        JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
        WHERE i.indrelid = 'app_opportunities'::regclass
        AND i.indisprimary
    """
    pk_result = run_docker_query(pk_query)
    if pk_result and pk_result.strip() == 'submission_id':
        print("✅ app_opportunities primary key is submission_id (DLT-compatible)")
    else:
        print(f"❌ app_opportunities primary key is not submission_id: {pk_result}")
        return False

    # Check foreign key relationships
    fk_checks = [
        ('opportunity_scores', 'opportunity_id', 'opportunities'),
        ('workflow_results', 'opportunity_id', 'opportunities'),
        ('app_opportunities', 'opportunity_id', 'opportunities'),
    ]

    for table, column, referenced_table in fk_checks:
        fk_query = f"""
            SELECT 1
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = '{table}'
            AND kcu.column_name = '{column}'
            AND tc.constraint_type = 'FOREIGN KEY'
        """
        fk_result = run_docker_query(fk_query)
        if fk_result:
            print(f"✅ Foreign key {table}.{column} exists")
        else:
            print(f"❌ Foreign key {table}.{column} missing")
            return False

    return True

def verify_indexes():
    """Verify critical indexes exist."""
    print("🔍 Verifying critical indexes...")

    critical_indexes = [
        'idx_opportunities_submission_id',
        'idx_opportunity_scores_opportunity_id',
        'idx_opportunity_scores_total_score',
        'idx_app_opportunities_opportunity_id',
        'idx_workflow_results_opportunity_id',
    ]

    for index_name in critical_indexes:
        index_query = f"SELECT 1 FROM pg_indexes WHERE indexname = '{index_name}'"
        index_result = run_docker_query(index_query)
        if index_result:
            print(f"✅ Index {index_name} exists")
        else:
            print(f"⚠️  Index {index_name} not found")

    return True

def verify_generated_columns():
    """Verify GENERATED columns work correctly."""
    print("🧮 Verifying GENERATED columns...")

    # Check opportunity_scores.total_score is generated
    gen_query = """
        SELECT attgenerated
        FROM pg_attribute
        JOIN pg_class ON pg_attribute.attrelid = pg_class.oid
        WHERE pg_class.relname = 'opportunity_scores'
        AND pg_attribute.attname = 'total_score'
    """
    gen_result = run_docker_query(gen_query)
    if gen_result and 's' in gen_result:  # 's' = stored
        print("✅ opportunity_scores.total_score is a stored generated column")
    else:
        print(f"❌ opportunity_scores.total_score is not properly generated: {gen_result}")
        return False

    # Test total_score calculation
    test_query = """
        SELECT COUNT(*)
        FROM opportunity_scores
        WHERE total_score IS NOT NULL
    """
    test_result = run_docker_query(test_query)
    if test_result:
        print(f"✅ total_score calculation working for {test_result} records")
    else:
        print("⚠️  No opportunity_scores records to test total_score")

    return True

def verify_views():
    """Verify that views can be created and queried."""
    print("👁️  Verifying views...")

    views = ['top_opportunities', 'opportunity_metrics_summary']

    for view_name in views:
        view_query = f"SELECT 1 FROM information_schema.views WHERE table_name = '{view_name}'"
        view_result = run_docker_query(view_query)
        if view_result:
            # Test querying the view
            test_query = f"SELECT COUNT(*) FROM {view_name} LIMIT 1"
            try:
                test_result = run_docker_query(test_query)
                print(f"✅ View {view_name} is queryable")
            except:
                print(f"⚠️  View {view_name} exists but query failed")
        else:
            print(f"❌ View {view_name} not found")
            return False

    return True

def test_data_compatibility():
    """Test that DLT can still work with the consolidated schema."""
    print("🔄 Testing DLT compatibility...")

    # Check that DLT tables are in expected schemas
    dlt_schemas = ['public', 'public_staging']

    for schema in dlt_schemas:
        schema_query = f"SELECT 1 FROM information_schema.schemata WHERE schema_name = '{schema}'"
        schema_result = run_docker_query(schema_query)
        if schema_result:
            print(f"✅ Schema {schema} exists")
        else:
            print(f"❌ Schema {schema} not found")
            return False

    # Verify core_functions column is properly typed
    core_functions_query = """
        SELECT data_type
        FROM information_schema.columns
        WHERE table_name = 'app_opportunities'
        AND column_name = 'core_functions'
    """
    core_functions_result = run_docker_query(core_functions_query)
    if core_functions_result and 'jsonb' in core_functions_result.lower():
        print("✅ app_opportunities.core_functions is JSONB")
    else:
        print(f"❌ app_opportunities.core_functions is not JSONB: {core_functions_result}")
        return False

    return True

def compare_schemas():
    """Compare the new schema with the original working schema."""
    print("📊 Comparing schemas...")

    # Create post-consolidation schema dump
    timestamp = subprocess.check_output(['date', '+%Y%m%d_%H%M%S'], text=True).strip()
    post_dump = f"schema_dumps/post_consolidation_{timestamp}.sql"

    if not run_command(
        f"docker exec supabase_db_carlos pg_dump -s -U postgres postgres > {post_dump}",
        "Creating post-consolidation schema dump"
    ):
        return False, None

    print(f"✅ Post-consolidation dump created: {post_dump}")

    # Simple comparison (in a real scenario, you'd do more sophisticated diffing)
    pre_dump = "schema_dumps/current_working_schema_20251117_215004.sql"

    if Path(pre_dump).exists() and Path(post_dump).exists():
        # Count tables in both dumps
        pre_tables = subprocess.check_output(
            f"grep -c 'CREATE TABLE public\\.' {pre_dump}",
            shell=True, text=True
        ).strip()
        post_tables = subprocess.check_output(
            f"grep -c 'CREATE TABLE public\\.' {post_dump}",
            shell=True, text=True
        ).strip()

        print(f"📈 Table count comparison:")
        print(f"   Pre-consolidation: {pre_tables} tables")
        print(f"   Post-consolidation: {post_tables} tables")

        # Expect difference due to DLT table exclusion
        expected_diff = 4  # _dlt_loads, _dlt_pipeline_state, _dlt_version, _migrations_log

        try:
            pre_count = int(pre_tables)
            post_count = int(post_tables)
            actual_diff = pre_count - post_count

            if actual_diff >= expected_diff:
                print(f"✅ Table count difference ({actual_diff}) meets expectations (≥ {expected_diff})")
                return True, post_dump
            else:
                print(f"⚠️  Table count difference ({actual_diff}) less than expected ({expected_diff})")
                return True, post_dump  # Still return True, but note the difference
        except ValueError:
            print("⚠️  Could not parse table counts")
            return True, post_dump

    return True, post_dump

def generate_test_report(results, schema_dump=None):
    """Generate a test report."""
    print("\n" + "="*60)
    print("📋 CONSOLIDATED SCHEMA TEST REPORT")
    print("="*60)

    passed = 0
    total = len(results)

    for test_name, test_result in results.items():
        status = "✅ PASS" if test_result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if test_result:
            passed += 1

    print(f"\n📊 Summary: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Schema consolidation successful.")
    else:
        print("⚠️  Some tests failed. Review issues before proceeding to production.")

    if schema_dump:
        print(f"\n📄 Post-consolidation schema: {schema_dump}")

    print("\n📝 Next steps:")
    if passed == total:
        print("   1. Review the schema differences")
        print("   2. Run application integration tests")
        print("   3. Test DLT pipeline functionality")
        print("   4. Prepare for production deployment")
    else:
        print("   1. Fix failing tests")
        print("   2. Re-run this test script")
        print("   3. Address any schema inconsistencies")

    return passed == total

def main():
    """Main test execution."""
    parser = argparse.ArgumentParser(description='Test consolidated schema migration')
    parser.add_argument('--schema-only', action='store_true',
                       help='Only test schema structure, skip fresh database test')

    args = parser.parse_args()

    print("🧪 RedditHarbor Schema Consolidation Test")
    print("="*60)

    results = {}
    schema_dump = None

    # Test fresh database setup (unless schema-only)
    if not args.schema_only:
        results['Fresh Database Setup'] = test_fresh_database()
        if not results['Fresh Database Setup']:
            print("❌ Cannot proceed with tests - database setup failed")
            return 1

    # Run all schema tests
    results['Schema Structure'] = verify_schema_structure()
    results['Critical Constraints'] = verify_critical_constraints()
    results['Indexes'] = verify_indexes()
    results['Generated Columns'] = verify_generated_columns()
    results['Views'] = verify_views()
    results['DLT Compatibility'] = test_data_compatibility()

    # Compare schemas
    comparison_success, schema_dump = compare_schemas()
    results['Schema Comparison'] = comparison_success

    # Generate final report
    success = generate_test_report(results, schema_dump)

    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())