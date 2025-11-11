#!/usr/bin/env python3
"""
Quick test: Collect from just 3 subreddits to verify pipeline works
Fast validation before running full 73-subreddit collection
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
    print("QUICK COLLECTION TEST (3 subreddits)")
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

    # Test with 3 subreddits only (fast!)
    test_subreddits = ["fitness", "personalfinance", "investing"]
    sort_types = ["hot", "top"]
    limit_per_sort = 20  # 20 posts per sort type
    mask_pii = False

    print(f"\n📝 Testing with subreddits: {test_subreddits}")
    print(f"   Sort types: {sort_types}")
    print(f"   Limit per sort: {limit_per_sort}")
    print(f"   Expected: ~{len(test_subreddits) * len(sort_types) * limit_per_sort} submissions")
    print(f"   Comments from top {limit_per_sort} posts per sort")

    total_submissions = 0
    total_comments = 0
    total_redditors = 0

    for subreddit in test_subreddits:
        print(f"\n{'='*60}")
        print(f"📈 Processing r/{subreddit}")
        print(f"{'='*60}")

        try:
            # Step 1: Collect submissions
            print("\n   📝 Collecting submissions...")
            result = pipeline.subreddit_submission(
                subreddits=[subreddit],
                sort_types=sort_types,
                limit=limit_per_sort,
                mask_pii=mask_pii
            )

            # Step 2: Collect comments
            print("\n   💬 Collecting comments...")
            pipeline.subreddit_comment(
                subreddits=[subreddit],
                sort_types=sort_types,
                limit=limit_per_sort,
                level=1,  # Top-level comments only
                mask_pii=mask_pii
            )
            print(f"      ✅ Completed r/{subreddit}")

        except Exception as e:
            print(f"      ❌ Error with r/{subreddit}: {e}")
            continue

    # Final summary
    print("\n" + "=" * 80)
    print("QUICK TEST COMPLETE")
    print("=" * 80)

    # Verify in database
    subs_result = supabase_client.table('submissions').select('count', count='exact').execute()
    comments_result = supabase_client.table('comments').select('count', count='exact').execute()
    redditors_result = supabase_client.table('redditors').select('count', count='exact').execute()

    print("\n📊 Final Database State:")
    print(f"   📝 Submissions: {subs_result.count}")
    print(f"   💬 Comments: {comments_result.count}")
    print(f"   👥 Redditors: {redditors_result.count}")

    if comments_result.count > 0:
        avg_comments = comments_result.count / subs_result.count if subs_result.count > 0 else 0
        print(f"   📊 Avg comments per submission: {avg_comments:.1f}")
        print("\n✅ SUCCESS! Ready to run full-scale collection")
        print("✅ Ready to test AI insights script")
        return True
    else:
        print("\n❌ FAILED! No comments collected")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
