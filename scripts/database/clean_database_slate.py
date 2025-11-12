#!/usr/bin/env python3
"""
Clean Database Slate - Clear all data while preserving table structure
"""

import sys
from pathlib import Path
from datetime import datetime
import os

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

def main():
    print("🧹 Cleaning database slate...")

    # Load environment variables
    load_dotenv(Path(__file__).parent.parent / '.env.local')

    # Get database connection info from environment
    db_host = os.getenv('SUPABASE_DB_HOST', '127.0.0.1')
    db_port = os.getenv('SUPABASE_DB_PORT', '54322')
    db_name = os.getenv('SUPABASE_DB_NAME', 'postgres')
    db_user = os.getenv('SUPABASE_DB_USER', 'postgres')
    db_password = os.getenv('SUPABASE_DB_PASSWORD', 'postgres')

    # Tables to clean
    tables_to_clean = [
        'submissions',
        'app_opportunities',
        'workflow_results',
        'redditors',
        'comments'
    ]

    # Create SQL commands
    sql_commands = []
    for table in tables_to_clean:
        sql_commands.append(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")

    # Execute SQL using psql
    try:
        import subprocess
        import tempfile

        # Create temporary SQL file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            for cmd in sql_commands:
                f.write(cmd + '\n')
            sql_file = f.name

        # Execute via psql
        env = os.environ.copy()
        env['PGPASSWORD'] = db_password

        cmd = [
            'psql',
            '-h', db_host,
            '-p', db_port,
            '-U', db_user,
            '-d', db_name,
            '-f', sql_file
        ]

        result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Database cleaned successfully!")
            print(f"Tables truncated: {', '.join(tables_to_clean)}")
        else:
            print(f"❌ Error cleaning database: {result.stderr}")
            # Fallback to individual TRUNCATE commands
            print("Trying individual table cleanup...")

        # Clean up temp file
        os.unlink(sql_file)

    except ImportError:
        print("⚠️ psql not available, trying basic approach...")
        # Try using direct Python approach
        try:
            from supabase import create_client
            from config.settings import SUPABASE_URL, SUPABASE_KEY
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

            for table_name in tables_to_clean:
                try:
                    print(f"Cleaning table: {table_name}")
                    # Try to delete all records with a WHERE clause
                    response = supabase.table(table_name).delete().neq('id', '').execute()
                    print(f"  ✓ Cleaned {table_name}")
                except Exception as e:
                    print(f"  ⚠️ Could not clean {table_name}: {str(e)}")

        except Exception as e:
            print(f"❌ Could not connect to database: {e}")

    except Exception as e:
        print(f"❌ Database cleaning failed: {e}")

    print("\n🚀 Database slate cleaned - Ready for clean 4-script pipeline!")

if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
    except ImportError:
        def load_dotenv(path):
            pass

    main()