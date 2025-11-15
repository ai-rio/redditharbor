#!/usr/bin/env python3
"""
Deployment script for trust schema compatibility fix

This script safely applies the schema changes and verifies the fix works.
"""

import os
import subprocess
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_command(cmd, description, cwd=project_root, capture_output=True):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=capture_output,
            text=True,
            cwd=cwd
        )
        if result.returncode == 0:
            print(f"   ✅ Success")
            if capture_output and result.stdout.strip():
                print(f"   📄 Output: {result.stdout.strip()[:200]}...")
            return True
        else:
            print(f"   ❌ Failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def check_supabase_running():
    """Check if Supabase is running"""
    print("🔍 Checking Supabase status...")
    try:
        result = subprocess.run(
            "supabase status",
            shell=True,
            capture_output=True,
            text=True,
            cwd=project_root
        )
        if result.returncode == 0 and "running" in result.stdout.lower():
            print("   ✅ Supabase is running")
            return True
        else:
            print("   ❌ Supabase is not running")
            return False
    except Exception as e:
        print(f"   ❌ Error checking Supabase: {e}")
        return False


def apply_schema_migration():
    """Apply the schema migration"""
    migration_file = project_root / "supabase/migrations/20251112000002_fix_trust_schema_compatibility.sql"

    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False

    print(f"📋 Applying schema migration: {migration_file.name}")

    # Use psql to apply the migration
    psql_cmd = f'psql "postgresql://postgres:postgres@127.0.0.1:54322/postgres" -f "{migration_file}"'

    return run_command(
        psql_cmd,
        "Applying schema migration via psql"
    )


def run_tests():
    """Run the compatibility test"""
    test_file = project_root / "scripts/test_trust_schema_fix.py"

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False

    print(f"🧪 Running compatibility tests...")

    # Run the test script
    test_cmd = f'python3 "{test_file}"'

    return run_command(
        test_cmd,
        "Running trust schema compatibility tests"
    )


def verify_database_state():
    """Verify the database is in the expected state"""
    print(f"🔍 Verifying database state...")

    # Check if the migration was applied correctly
    verify_sql = """
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_name = 'app_opportunities'
    AND table_schema = 'public'
    AND column_name IN ('confidence_score', 'ai_confidence_level')
    ORDER BY column_name;
    """

    psql_cmd = f'psql "postgresql://postgres:postgres@127.0.0.1:54322/postgres" -c "{verify_sql}"'

    return run_command(
        psql_cmd,
        "Verifying database column state",
        capture_output=False  # Show output for verification
    )


def create_backup():
    """Create a database backup before applying changes"""
    print(f"💾 Creating database backup...")

    timestamp = int(time.time())
    backup_file = project_root / f"db_dumps/pre_trust_schema_fix_backup_{timestamp}.sql"

    # Create backup directory if it doesn't exist
    backup_dir = backup_file.parent
    backup_dir.mkdir(exist_ok=True)

    # Use pg_dump to create backup
    dump_cmd = f'pg_dump "postgresql://postgres:postgres@127.0.0.1:54322/postgres" > "{backup_file}"'

    success = run_command(
        dump_cmd,
        f"Creating database backup to {backup_file.name}"
    )

    if success:
        print(f"   💾 Backup created: {backup_file}")
        return True
    else:
        print(f"   ❌ Failed to create backup")
        return False


def main():
    """Main deployment process"""
    print("🚀 Trust Schema Compatibility Fix Deployment")
    print("=" * 80)

    # Import time for timestamp generation
    import time

    try:
        # Step 1: Check prerequisites
        print(f"\n📋 Step 1: Checking prerequisites...")
        if not check_supabase_running():
            print("❌ Supabase is not running. Please start it with 'supabase start'")
            return False

        # Step 2: Create backup
        print(f"\n💾 Step 2: Creating database backup...")
        if not create_backup():
            print("⚠️  Warning: Failed to create backup, but continuing...")

        # Step 3: Apply schema migration
        print(f"\n📋 Step 3: Applying schema migration...")
        if not apply_schema_migration():
            print("❌ Schema migration failed")
            return False

        # Step 4: Verify database state
        print(f"\n🔍 Step 4: Verifying database state...")
        if not verify_database_state():
            print("⚠️  Warning: Could not verify database state, but continuing...")

        # Step 5: Run tests
        print(f"\n🧪 Step 5: Running compatibility tests...")
        if not run_tests():
            print("❌ Compatibility tests failed")
            return False

        # Success!
        print(f"\n🎉 DEPLOYMENT SUCCESSFUL!")
        print("=" * 80)
        print("✅ Schema compatibility fix has been applied successfully")
        print("✅ Database now supports both confidence_score (numeric) and ai_confidence_level (string)")
        print("✅ Trust pipeline should now work without schema conflicts")
        print("✅ All tests passed")

        print(f"\n📋 Next steps:")
        print("1. Run the trust pipeline to verify it works end-to-end")
        print("2. Monitor the database logs for any remaining issues")
        print("3. The trigger will automatically maintain confidence_score values")

        return True

    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)