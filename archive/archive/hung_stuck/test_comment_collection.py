#!/usr/bin/env python3
"""
Quick test to verify comment collection works
Only processes 1 subreddit to validate the fix
"""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redditharbor.dock.pipeline import collect
from redditharbor.login import reddit, supabase

from config.settings import (
    DB_CONFIG,
    REDDIT_PUBLIC,
    REDDIT_SECRET,
    REDDIT_USER_AGENT,
    SUPABASE_KEY,
    SUPABASE_URL,
)


def main():
    print("=" * 80)
    print("TESTING COMMENT COLLECTION")
    print("=" * 80)

    # Create clients
    print("\n🔑 Creating Reddit and Supabase clients...")
    reddit_client = reddit(
        public_key=REDDIT_PUBLIC,
        secret_key=REDDIT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
    supabase_client = supabase(
        url=SUPABASE_URL,
        private_key=SUPABASE_KEY
    )

    # Create pipeline
    print("🔄 Initializing pipeline...")
    pipeline = collect(
        reddit_client=reddit_client,
        supabase_client=supabase_client,
        db_config=DB_CONFIG
    )

    # Test with just 1 subreddit (fast!)
    test_subreddit = "fitness"
    print(f"\n📝 Testing with r/{test_subreddit}...")

    # Check existing counts
    print("\n📊 BEFORE collection:")
    subs_before = supabase_client.table('submissions').select('count', count='exact').execute()
    comments_before = supabase_client.table('comments').select('count', count='exact').execute()

    print(f"   Submissions: {subs_before.count}")
    print(f"   Comments: {comments_before.count}")

    # Collect comments (from top 10 posts)
    print(f"\n💬 Collecting comments from r/{test_subreddit}...")
    try:
        pipeline.subreddit_comment(
            subreddits=[test_subreddit],
            sort_types=["hot", "top"],
            limit=10,  # Only top 10 posts
            level=1,  # Top-level comments only
            mask_pii=False
        )
        print("   ✅ Comment collection complete")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    # Check new counts
    print("\n📊 AFTER collection:")
    subs_after = supabase_client.table('submissions').select('count', count='exact').execute()
    comments_after = supabase_client.table('comments').select('count', count='exact').execute()

    print(f"   Submissions: {subs_after.count}")
    print(f"   Comments: {comments_after.count}")

    new_comments = comments_after.count - comments_before.count
    print(f"\n🎉 SUCCESS! Collected {new_comments} new comments")

    if new_comments > 0:
        print("   ✅ Comment collection is working!")
        print("   ✅ AI insights script should now work properly")
        return True
    else:
        print("   ⚠️  No new comments collected")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
