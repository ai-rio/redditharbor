#!/usr/bin/env python3
"""
Quick test to verify environment variables are loaded correctly.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env.local
from dotenv import load_dotenv

load_dotenv(project_root / '.env.local')

# Check environment variables
def test_env():
    print("=" * 80)
    print("Environment Variable Test")
    print("=" * 80)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    minimax_api_key = os.getenv("MINIMAX_API_KEY")
    minimax_group_id = os.getenv("MINIMAX_GROUP_ID")

    print(f"\n✓ SUPABASE_URL: {supabase_url}")
    if supabase_url:
        print(f"  Length: {len(supabase_url)} chars")
    else:
        print("  ❌ NOT SET")

    print(f"\n✓ SUPABASE_KEY: {'*' * 20 if supabase_key else 'NOT SET'}")
    if supabase_key:
        print(f"  Length: {len(supabase_key)} chars")

    print(f"\n✓ MINIMAX_API_KEY: {'*' * 20 if minimax_api_key else 'NOT SET'}")
    if minimax_api_key != "your_minimax_api_key_here":
        print("  ✓ Looks like it's been configured!")
    else:
        print("  ⚠️  Using default placeholder - update .env.local")

    print(f"\n✓ MINIMAX_GROUP_ID: {minimax_group_id if minimax_group_id != 'your_minimax_group_id_here' else 'NOT SET'}")
    if minimax_group_id and minimax_group_id != "your_minimax_group_id_here":
        print("  ✓ Looks like it's been configured!")

    print("\n" + "=" * 80)

    # Test imports
    print("\nTesting imports...")
    try:
        import requests
        print("✓ requests imported")
    except ImportError:
        print("❌ requests not installed - run: pip install requests")

    try:
        from supabase import create_client
        print("✓ supabase imported")
    except ImportError:
        print("❌ supabase not installed - run: pip install supabase")

    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv imported")
    except ImportError:
        print("❌ python-dotenv not installed - run: pip install python-dotenv")

    print("\n" + "=" * 80)
    print("Test complete!")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    import os
    test_env()
