#!/usr/bin/env python3
"""
Simple test collection from one subreddit
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("🔍 TEST: Simple Collection from r/personalfinance")
print("=" * 80)
print()

try:
    from redditharbor.login import reddit, supabase

    from config.settings import (
        DB_CONFIG,
        REDDIT_PUBLIC,
        REDDIT_SECRET,
        REDDIT_USER_AGENT,
        SUPABASE_KEY,
        SUPABASE_URL,
    )
    from core.collection import collect_monetizable_opportunities_data

    print("✅ All imports successful")
    print()

    # Create Reddit client
    print("🔍 Creating Reddit client...")
    reddit_client = reddit(
        public_key=REDDIT_PUBLIC,
        secret_key=REDDIT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
    print("✅ Reddit client created")
    print()

    # Test Reddit connection
    print("🔍 Testing Reddit connection...")
    test_sub = reddit_client.subreddit("personalfinance")
    test_post = next(test_sub.hot(limit=1))
    print(f"✅ Reddit API working - found post: {test_post.title[:50]}...")
    print()

    # Create Supabase client
    print("🔍 Creating Supabase client...")
    supabase_client = supabase(
        url=SUPABASE_URL,
        private_key=SUPABASE_KEY
    )
    print("✅ Supabase client created")
    print()

    # Test Supabase connection
    print("🔍 Testing Supabase connection...")
    result = supabase_client.table('submissions').select('count').limit(1).execute()
    print("✅ Supabase connected - table accessible")
    print()

    # Try collection from one subreddit
    print("🔄 Starting test collection from r/personalfinance...")
    success = collect_monetizable_opportunities_data(
        reddit_client=reddit_client,
        supabase_client=supabase_client,
        db_config=DB_CONFIG,
        market_segment="all",  # Use all since TARGET_SUBREDDITS is used internally
        limit_per_sort=5,  # Very small limit for testing
        time_filter="week",
        mask_pii=False,
        sentiment_analysis=True,
        extract_problem_keywords=True,
        track_workarounds=True
    )

    if success:
        print()
        print("=" * 80)
        print("✅ TEST COLLECTION SUCCESSFUL!")
        print("=" * 80)
    else:
        print()
        print("=" * 80)
        print("❌ TEST COLLECTION FAILED")
        print("=" * 80)

except Exception as e:
    print()
    print("=" * 80)
    print(f"❌ ERROR: {e}")
    print("=" * 80)
    import traceback
    traceback.print_exc()
    sys.exit(1)
