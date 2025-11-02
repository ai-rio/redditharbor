#!/usr/bin/env .venv/bin/python
"""
Quick test to collect a small sample of Reddit data
"""

from redditharbor.dock.pipeline import collect
from redditharbor.login import reddit, supabase
from redditharbor_config import *


def test_small_collection():
    """Collect a very small sample to verify everything works"""
    print("🧪 Running small collection test...")

    try:
        # Initialize clients
        reddit_client = reddit(
            public_key=REDDIT_PUBLIC,
            secret_key=REDDIT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )

        supabase_client = supabase(
            url=SUPABASE_URL,
            private_key=SUPABASE_KEY
        )

        pipeline = collect(
            reddit_client=reddit_client,
            supabase_client=supabase_client,
            db_config=DB_CONFIG
        )

        # Collect just 2 posts from r/python
        print("📥 Collecting 2 hot posts from r/python...")
        pipeline.subreddit_submission(
            subreddits=["python"],
            sort_types=["hot"],
            limit=2,
            mask_pii=ENABLE_PII_ANONYMIZATION
        )

        print("✅ Collection successful!")
        print("📊 Check your data at: http://127.0.0.1:54323")
        print("🔍 Go to Table Editor -> Select 'redditor', 'submission', or 'comment' tables")

        return True

    except Exception as e:
        print(f"❌ Collection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_small_collection()

    if success:
        print("\n🎉 RedditHarbor is fully configured and working!")
        print("📈 You can now:")
        print("   • Use redditharbor_project_templates.py for predefined collections")
        print("   • Create custom collection scripts")
        print("   • View data in Supabase Studio")
    else:
        print("\n❌ Something went wrong. Check the error above.")
