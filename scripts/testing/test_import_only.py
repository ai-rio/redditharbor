#!/usr/bin/env python3
"""
Test import only to verify the fix is structurally correct.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    # Test basic imports
    print("Testing imports...")

    # Import settings
    import config.settings as settings
    print("✓ Settings imported")

    # Import supabase
    from supabase import create_client
    print("✓ Supabase client imported")

    # Create a client to test connectivity
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    print("✓ Supabase client created")

    # Test basic query
    result = client.table("submissions").select("count", count="exact").execute()
    count = result.count if hasattr(result, 'count') else 'unknown'
    print(f"✓ Connected to database, submissions table has ~{count} rows")

    print("\n✅ IMPORT AND CONNECTIVITY TEST PASSED")
    print("The basic infrastructure is working")

except Exception as e:
    print(f"❌ Import/connectivity test failed: {e}")
    import traceback
    traceback.print_exc()