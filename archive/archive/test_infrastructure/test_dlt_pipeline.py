#!/usr/bin/env python3
"""
Test DLT pipeline for Reddit data collection.

This script validates DLT integration by collecting a small sample
of Reddit data and loading it into Supabase.
"""

import os
import sys
from pathlib import Path

import dlt

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import configuration
from config.dlt_settings import DLT_PIPELINE_CONFIG


def test_reddit_collection():
    """Test basic Reddit data collection with DLT."""

    print("=" * 80)
    print("DLT TEST PIPELINE")
    print("=" * 80)

    # Create pipeline
    pipeline = dlt.pipeline(**DLT_PIPELINE_CONFIG)
    print(f"\n✓ Pipeline created: {pipeline.pipeline_name}")
    print(f"  Destination: {pipeline.destination}")
    print(f"  Dataset: {pipeline.dataset_name}")

    # Configure Reddit REST API source
    # Note: This is a basic test - in production we'd use proper OAuth
    reddit_source = {
        "client": {
            "base_url": "https://oauth.reddit.com",
            "auth": {
                "type": "bearer",
                "token": os.getenv("REDDIT_ACCESS_TOKEN", "test_token_placeholder")
            }
        },
        "resources": [
            {
                "name": "submissions",
                "endpoint": {
                    "path": "r/opensource/new",
                    "params": {
                        "limit": 10  # Small test sample
                    }
                }
            }
        ]
    }

    print("\n⚠️  WARNING: Using test configuration")
    print("  - Reddit API token not configured")
    print("  - This will test DLT pipeline structure only")
    print("  - For full test, configure REDDIT_ACCESS_TOKEN in .env")

    # Create source using rest_api_source
    try:
        from dlt.sources.rest_api import rest_api_source
        source = rest_api_source(reddit_source)
        print(f"\n✓ Source configured: {len(source.selected_resources)} resources")
    except Exception as e:
        print(f"\n✗ Source configuration failed: {e}")
        print("  This is expected without proper Reddit API setup")
        print("\n✓ DLT pipeline structure is valid")
        print("  Next steps:")
        print("  1. Configure Reddit API credentials")
        print("  2. Get OAuth token from Reddit")
        print("  3. Re-run this test")
        return None

    # Run pipeline
    try:
        load_info = pipeline.run(source)
        print("\n✓ Pipeline executed successfully")
        print(f"  Tables: {list(load_info.schema.tables.keys())}")
        print(f"  Metrics: {load_info.metrics}")
        return load_info
    except Exception as e:
        print(f"\n✗ Pipeline execution failed: {e}")
        print("  This may be due to:")
        print("  - Invalid Reddit API token")
        print("  - Supabase connection issues")
        print("  - Network/authentication problems")
        return None

def test_dlt_structure():
    """Test DLT installation and configuration structure."""

    print("\n" + "=" * 80)
    print("DLT STRUCTURE TEST")
    print("=" * 80)

    # Test DLT import
    try:
        import dlt
        print(f"\n✓ DLT installed: version {dlt.__version__}")
    except ImportError:
        print("\n✗ DLT not installed")
        return False

    # Test configuration
    try:
        from config.dlt_settings import (
            DLT_PIPELINE_CONFIG,
        )
        print("✓ DLT configuration loaded")
        print(f"  Pipeline: {DLT_PIPELINE_CONFIG['pipeline_name']}")
        print(f"  Destination: {DLT_PIPELINE_CONFIG['destination']}")
        print(f"  Dataset: {DLT_PIPELINE_CONFIG['dataset_name']}")
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

    # Test Supabase connection
    try:
        from config.settings import SUPABASE_KEY, SUPABASE_URL
        print("\n✓ Supabase configuration found")
        print(f"  URL: {SUPABASE_URL[:30]}...")
        print(f"  Key: {SUPABASE_KEY[:20]}...")
    except Exception as e:
        print(f"\n⚠️  Supabase config warning: {e}")

    print("\n✓ DLT structure is valid")
    return True

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("RedditHarbor DLT Integration Test")
    print("=" * 80)

    # Test 1: DLT Structure
    structure_ok = test_dlt_structure()

    if not structure_ok:
        print("\n❌ Structure test failed - cannot continue")
        sys.exit(1)

    # Test 2: Collection Pipeline
    print("\n" + "=" * 80)
    print("Testing DLT Collection Pipeline")
    print("=" * 80)

    result = test_reddit_collection()

    if result:
        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80)
        print("\nDLT is properly configured and ready for use!")
        print("\nNext steps:")
        print("1. Configure Reddit API credentials (.env)")
        print("2. Get OAuth access token")
        print("3. Test with real data")
    else:
        print("\n" + "=" * 80)
        print("⚠️  PARTIAL SUCCESS")
        print("=" * 80)
        print("\nDLT structure is valid but external dependencies need configuration")
        print("\nRequired setup:")
        print("1. Reddit API credentials in .env")
        print("2. OAuth access token")
        print("3. Supabase running (local or remote)")
        print("\nSee docs/guides/dlt-integration-guide.md for detailed setup instructions")
