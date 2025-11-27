#!/usr/bin/env python3
"""
Test Reddit API fetch in isolation
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def test_reddit_fetch():
    """Test basic Reddit API fetch"""
    print("🧪 Testing Reddit API Fetch in Isolation")
    print("=" * 60)

    try:
        # Import Reddit
        import praw
        print("✅ praw imported successfully")

        # Load credentials
        from config.settings import REDDIT_PUBLIC, REDDIT_SECRET
        print("✅ Credentials loaded")

        # Create Reddit instance
        reddit = praw.Reddit(
            client_id=REDDIT_PUBLIC,
            client_secret=REDDIT_SECRET,
            user_agent="RedditHarbor/1.0 (Testing)"
        )
        print("✅ Reddit instance created")

        # Test fetch from productivity subreddit
        print("\n📡 Fetching 3 submissions from r/productivity...")
        subreddit = reddit.subreddit("productivity")

        submissions = list(subreddit.hot(limit=3))
        print(f"✅ Fetched {len(submissions)} submissions")

        # Display results
        print("\n📋 Submissions:")
        for i, sub in enumerate(submissions, 1):
            print(f"{i}. {sub.title[:60]}...")
            print(f"   Score: {sub.score}, Comments: {sub.num_comments}")
            print(f"   Author: {sub.author}, Subreddit: {sub.subreddit}")

        print("\n🎉 REDDIT API FETCH TEST PASSED")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ REDDIT API FETCH TEST FAILED")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import time
    start = time.time()
    success = test_reddit_fetch()
    elapsed = time.time() - start

    print(f"\n⏱️  Test completed in {elapsed:.2f} seconds")
    sys.exit(0 if success else 1)
