#!/usr/bin/env python3
"""
Full migration consolidation test with fresh database setup.

This script performs a complete test of the consolidated migration process,
including database reset, migration execution, and validation.
"""

import subprocess
import sys
import time
from pathlib import Path

def run_command(cmd, description, max_retries=3):
    """Run a command with retries and proper error handling."""
    for attempt in range(max_retries):
        try:
            print(f"🔧 {description}...")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            print(f"✅ {description} completed")
            return result.stdout.strip() if result.stdout else None
        except subprocess.CalledProcessError as e:
            if attempt < max_retries - 1:
                print(f"⚠️  {description} failed (attempt {attempt + 1}/{max_retries}): {e}")
                if e.stderr:
                    print(f"   Error: {e.stderr}")
                time.sleep(2)
                continue
            else:
                print(f"❌ {description} failed after {max_retries} attempts: {e}")
                if e.stderr:
                    print(f"   Error: {e.stderr}")
                return None

def stop_supabase():
    """Stop Supabase services."""
    print("🛑 Stopping Supabase services...")
    try:
        subprocess.run("supabase stop", shell=True, check=True, capture_output=True)
        print("✅ Supabase stopped")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Could not stop Supabase: {e}")
        return False

def reset_database():
    """Reset database to clean state."""
    print("🔄 Resetting database to clean state...")

    # Stop services
    stop_supabase()

    # Start services (this will also reset the database)
    if not run_command("supabase start", "Starting Supabase services"):
        return False

    # Wait for services to be ready
    print("⏳ Waiting for database to be ready...")
    time.sleep(10)

    # Test database connection
    connection_test = run_command(
        "docker exec supabase_db_carlos psql -U postgres -d postgres -c 'SELECT 1'",
        "Testing database connection"
    )

    return connection_test is not None

def run_migrations():
    """Run the consolidated migrations."""
    print("🚀 Running consolidated migrations...")

    # List current migration files
    migrations_dir = Path("supabase/migrations")
    migration_files = sorted(migrations_dir.glob("*.sql"))

    print(f"📄 Found {len(migration_files)} migration files:")
    for migration in migration_files:
        print(f"   - {migration.name}")

    # Run db reset to apply all migrations
    if not run_command("supabase db reset", "Applying migrations with db reset", max_retries=5):
        return False

    print("✅ All migrations applied successfully")
    return True

def verify_migration_results():
    """Verify that migrations created the expected schema."""
    print("🔍 Verifying migration results...")

    verification_queries = [
        ("subreddits table exists", """
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_name = 'subreddits' AND table_schema = 'public'
        """),
        ("opportunity_scores table exists", """
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_name = 'opportunity_scores' AND table_schema = 'public'
        """),
        ("app_opportunities view exists", """
            SELECT COUNT(*) FROM information_schema.views
            WHERE table_name = 'app_opportunities' AND table_schema = 'public'
        """),
        ("top_opportunities view exists", """
            SELECT COUNT(*) FROM information_schema.views
            WHERE table_name = 'top_opportunities' AND table_schema = 'public'
        """),
        ("opportunity_scores total_score is generated", """
            SELECT COUNT(*) FROM pg_attribute
            WHERE attrelid = 'opportunity_scores'::regclass
            AND attname = 'total_score'
            AND attgenerated = 's'
        """),
    ]

    results = {}
    for description, query in verification_queries:
        try:
            cmd = f'docker exec supabase_db_carlos psql -U postgres -d postgres -t -c "{query}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            count = int(result.stdout.strip()) if result.stdout.strip() else 0
            results[description] = count > 0
            status = "✅" if count > 0 else "❌"
            print(f"   {status} {description}: {count}")
        except Exception as e:
            results[description] = False
            print(f"   ❌ {description}: Error - {e}")

    return results

def test_dlt_compatibility():
    """Test DLT compatibility aspects."""
    print("🔄 Testing DLT compatibility...")

    dlt_tests = [
        ("public_staging schema exists", """
            SELECT COUNT(*) FROM information_schema.schemata
            WHERE schema_name = 'public_staging'
        """),
        ("public_staging.app_opportunities exists", """
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_name = 'app_opportunities' AND table_schema = 'public_staging'
        """),
    ]

    results = {}
    for description, query in dlt_tests:
        try:
            cmd = f'docker exec supabase_db_carlos psql -U postgres -d postgres -t -c "{query}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            count = int(result.stdout.strip()) if result.stdout.strip() else 0
            results[description] = count > 0
            status = "✅" if count > 0 else "❌"
            print(f"   {status} {description}: {count}")
        except Exception as e:
            results[description] = False
            print(f"   ❌ {description}: Error - {e}")

    return results

def create_test_data():
    """Create some test data to verify the schema works."""
    print("📝 Creating test data...")

    test_sql = """
    -- Insert test subreddit
    INSERT INTO subreddits (name, title, description, subscribers)
    VALUES ('testsub', 'Test Subreddit', 'A test subreddit', 1000)
    ON CONFLICT (name) DO NOTHING;

    -- Insert test redditor
    INSERT INTO redditors (username, karma)
    VALUES ('testuser', 500)
    ON CONFLICT (username) DO NOTHING;

    -- Insert test submission
    INSERT INTO submissions (reddit_id, redditor_id, subreddit_id, title, content)
    VALUES ('test123',
            (SELECT id FROM redditors WHERE username = 'testuser'),
            (SELECT id FROM subreddits WHERE name = 'testsub'),
            'Test Submission',
            'This is a test submission content')
    ON CONFLICT (reddit_id) DO NOTHING;
    """

    try:
        cmd = f'docker exec supabase_db_carlos psql -U postgres -d postgres -c "{test_sql}"'
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        print("✅ Test data created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create test data: {e}")
        return False

def generate_report(migration_results, dlt_results, test_data_success):
    """Generate final test report."""
    print("\n" + "="*60)
    print("📋 MIGRATION CONSOLIDATION TEST REPORT")
    print("="*60)

    all_results = {
        **migration_results,
        **dlt_results,
        "Test data creation": test_data_success
    }

    passed = sum(1 for result in all_results.values() if result)
    total = len(all_results)

    for test_name, test_result in all_results.items():
        status = "✅ PASS" if test_result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\n📊 Summary: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Migration consolidation successful.")
        print("\n📝 Next steps:")
        print("   1. Test application functionality")
        print("   2. Test DLT pipeline integration")
        print("   3. Verify all 7 production pipelines work")
        print("   4. Prepare for production deployment")
        return True
    else:
        print("⚠️  Some tests failed. Review issues before proceeding.")
        print("\n📝 Next steps:")
        print("   1. Fix failing tests")
        print("   2. Re-run this consolidation test")
        print("   3. Address schema inconsistencies")
        return False

def main():
    """Main test execution."""
    print("🧪 RedditHarbor Migration Consolidation Test")
    print("="*60)

    # Step 1: Reset database to clean state
    if not reset_database():
        print("❌ Database reset failed. Cannot proceed.")
        return 1

    # Step 2: Run migrations
    if not run_migrations():
        print("❌ Migration execution failed. Cannot proceed.")
        return 1

    # Step 3: Verify migration results
    migration_results = verify_migration_results()

    # Step 4: Test DLT compatibility
    dlt_results = test_dlt_compatibility()

    # Step 5: Create test data
    test_data_success = create_test_data()

    # Step 6: Generate report
    success = generate_report(migration_results, dlt_results, test_data_success)

    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())