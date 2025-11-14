#!/usr/bin/env python3
"""
Apply the cost tracking fix directly using the Supabase Python client
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from supabase import create_client
    import dotenv

    # Load environment variables
    dotenv.load_dotenv()

    # Get Supabase credentials
    url = os.getenv('SUPABASE_URL', 'http://127.0.0.1:54321')
    key = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU')

    # Create Supabase client
    supabase = create_client(url, key)

    # Read the SQL fix
    fix_sql_path = project_root / 'supabase' / 'migrations' / '20251114005544_fix_cost_tracking_functions.sql'

    with open(fix_sql_path, 'r') as f:
        sql_content = f.read()

    print("Applying cost tracking fix...")
    print(f"SQL file: {fix_sql_path}")

    # Split SQL into individual statements (simple split on semicolons)
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and not stmt.strip().startswith('--')]

    # Execute statements
    for i, statement in enumerate(statements, 1):
        if statement:
            print(f"\nExecuting statement {i}:")
            print(f"Type: {statement.split()[0] if statement.split() else 'Unknown'}")

            try:
                # Try to execute via Supabase RPC
                result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                print(f"✓ Success")
            except Exception as e:
                print(f"✗ Error: {e}")
                print(f"Statement was: {statement[:100]}...")

    print("\nCost tracking fix application completed!")

    # Test the fixed function
    print("\nTesting the fixed get_cost_summary() function...")
    try:
        result = supabase.rpc('get_cost_summary').execute()
        print("✓ get_cost_summary() function works!")
        print(f"Result: {result.data}")
    except Exception as e:
        print(f"✗ get_cost_summary() test failed: {e}")

    # Test the simple view
    print("\nTesting cost_summary_simple view...")
    try:
        result = supabase.table('cost_summary_simple').select('*').limit(1).execute()
        print("✓ cost_summary_simple view works!")
        print(f"Result: {result.data}")
    except Exception as e:
        print(f"✗ cost_summary_simple view test failed: {e}")

except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Please install required packages: pip install supabase python-dotenv")
    sys.exit(1)
except Exception as e:
    print(f"Error applying fix: {e}")
    sys.exit(1)