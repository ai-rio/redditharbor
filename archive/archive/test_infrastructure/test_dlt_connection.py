#!/usr/bin/env python3
"""
Test DLT connection to Supabase/PostgreSQL database.
"""

import sys
from pathlib import Path

import dlt

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_supabase_connection():
    """Test connection to Supabase database."""

    print("=" * 80)
    print("Testing DLT Supabase Connection")
    print("=" * 80)

    try:
        # Create pipeline
        pipeline = dlt.pipeline(
            pipeline_name="reddit_harbor_collection",
            destination="postgres",
            dataset_name="reddit_harbor"
        )

        print("\n✓ Pipeline created successfully")
        print(f"  Name: {pipeline.pipeline_name}")
        print(f"  Destination: {pipeline.destination}")

        # Test destination client initialization
        destination_client = pipeline.destination_client()
        print("\n✓ Destination client initialized")
        print(f"  Client type: {type(destination_client).__name__}")

        # Test database connection by trying to create the client
        with pipeline.destination_client() as client:
            # Just having the client means connection parameters are valid
            print("\n✓ Database connection successful")
            print(f"  Client ready: {client is not None}")

        return True

    except Exception as e:
        print(f"\n✗ Connection test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_supabase_connection()

    print("\n" + "=" * 80)
    if success:
        print("✓ SUCCESS: DLT can connect to Supabase/PostgreSQL")
        print("=" * 80)
        print("\nDLT infrastructure is properly configured!")
        print("\nNext steps:")
        print("1. Configure Reddit API credentials")
        print("2. Get OAuth access token")
        print("3. Run full data collection pipeline")
    else:
        print("✗ FAILED: Could not connect to database")
        print("=" * 80)
        print("\nPlease check:")
        print("1. Supabase is running (supabase start)")
        print("2. Credentials in .dlt/secrets.toml are correct")
        print("3. Database is accessible at 127.0.0.1:54322")

    sys.exit(0 if success else 1)
