#!/usr/bin/env python3
"""
Simple test script for RedditHarbor setup
"""

from redditharbor.dock.pipeline import collect
from redditharbor.login import reddit, supabase
from redditharbor_config import *


def test_basic_setup():
    """Test basic RedditHarbor functionality"""
    print("🧪 Testing RedditHarbor Setup...")

    try:
        # Initialize Reddit client
        print("📡 Connecting to Reddit API...")
        reddit_client = reddit(
            public_key=REDDIT_PUBLIC,
            secret_key=REDDIT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )

        # Initialize Supabase client
        print("🗄️ Connecting to local Supabase...")
        supabase_client = supabase(url=SUPABASE_URL, private_key=SUPABASE_KEY)

        # Test Reddit connection
        print("🔍 Testing Reddit API access...")
        test_subreddit = reddit_client.subreddit("python")
        hot_posts = list(test_subreddit.hot(limit=1))

        if hot_posts:
            print(
                f"✅ Successfully connected to Reddit! Found subreddit: r/{hot_posts[0].subreddit}"
            )

        # Test Supabase connection
        print("🔍 Testing Supabase connection...")
        supabase_client.table("redditor").select("count", count="exact").execute()
        print("✅ Successfully connected to Supabase!")

        # Initialize pipeline
        print("🔧 Initializing collection pipeline...")
        pipeline = collect(
            reddit_client=reddit_client,
            supabase_client=supabase_client,
            db_config=DB_CONFIG,
        )

        print("✅ All tests passed! RedditHarbor is ready to use.")
        return pipeline

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None


if __name__ == "__main__":
    pipeline = test_basic_setup()

    if pipeline:
        print("\n🎯 Ready to collect Reddit data!")
        print("📊 View your data at: http://127.0.0.1:54323")
        print("🔧 Use redditharbor_project_templates.py for predefined collections")
