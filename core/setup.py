#!/usr/bin/env python3
"""
RedditHarbor Setup Script for Multi-Project Supabase Environment
"""

import os

# Try to import with fallback for migration
try:
    from redditharbor.dock.pipeline import collect
    from redditharbor.login import reddit, supabase

    from config.settings import *
except ImportError as e:
    print(f"Warning: Could not import dependencies: {e}")
    # Define fallbacks if needed
    reddit = None
    supabase = None
    collect = None

    # Try to import config directly if settings module doesn't work
    try:
        import sys

        config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
        sys.path.insert(0, config_dir)
        import settings as redditharbor_config

        # Import all config variables
        for key in dir(redditharbor_config):
            if not key.startswith("_"):
                globals()[key] = getattr(redditharbor_config, key)
    except ImportError:
        print("Warning: Could not import configuration")
        # Define minimal defaults
        REDDIT_PUBLIC = ""
        REDDIT_SECRET = ""
        REDDIT_USER_AGENT = ""
        SUPABASE_URL = ""
        SUPABASE_KEY = ""
        DB_CONFIG = {}


def setup_redditharbor():
    """
    Initialize RedditHarbor with your local Supabase instance
    """
    print("🚀 Setting up RedditHarbor...")

    # Check if credentials are set
    if (
        REDDIT_PUBLIC == "<your-reddit-public-key>"
        or REDDIT_SECRET == "<your-reddit-secret-key>"
    ):
        print("❌ Reddit API credentials not configured!")
        print("Please edit redditharbor_config.py with your Reddit API credentials.")
        print("Get them from: https://www.reddit.com/prefs/apps")
        return False

    if REDDIT_USER_AGENT == "<institution:project-name (u/reddit-username)>":
        print("❌ User agent not configured!")
        print("Please edit redditharbor_config.py with a proper user agent.")
        return False

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

        # Initialize collection pipeline
        print("🔧 Initializing collection pipeline...")
        pipeline = collect(
            reddit_client=reddit_client,
            supabase_client=supabase_client,
            db_config=DB_CONFIG,
        )

        print("✅ RedditHarbor setup complete!")
        return pipeline

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False


def test_collection(pipeline, test_mode=True):
    """
    Test data collection with small sample
    """
    if not pipeline:
        print("❌ Pipeline not initialized. Run setup_redditharbor() first.")
        return

    print(f"🧪 Testing collection with {DEFAULT_SUBREDDITS[:2]} subreddits...")

    try:
        # Small test collection
        pipeline.subreddit_submission(
            subreddits=DEFAULT_SUBREDDITS[:2],  # Use only first 2 subreddits for test
            sort_types=["hot"],  # Only hot posts for test
            limit=3,  # Only 3 posts for test
            mask_pii=ENABLE_PII_ANONYMIZATION,
        )

        print("✅ Test collection successful!")
        print("📊 Data has been saved to your local Supabase instance.")
        print("🌐 View your data at: http://127.0.0.1:54323")

    except Exception as e:
        print(f"❌ Test collection failed: {e}")


def run_sample_collection(pipeline):
    """
    Run a sample collection for demonstration
    """
    if not pipeline:
        print("❌ Pipeline not initialized. Run setup_redditharbor() first.")
        return

    print(f"📊 Starting sample collection from {DEFAULT_SUBREDDITS}...")

    try:
        # Collect submissions
        pipeline.subreddit_submission(
            subreddits=DEFAULT_SUBREDDITS,
            sort_types=DEFAULT_SORT_TYPES,
            limit=DEFAULT_LIMIT,
            mask_pii=ENABLE_PII_ANONYMIZATION,
        )

        # Collect comments
        pipeline.subreddit_comment(
            subreddits=DEFAULT_SUBREDDITS,
            limit=200,  # More comments than submissions
            mask_pii=ENABLE_PII_ANONYMIZATION,
        )

        print("✅ Sample collection complete!")
        print(
            "📈 Data has been saved to the 'redditharbor' schema in your local Supabase."
        )

    except Exception as e:
        print(f"❌ Sample collection failed: {e}")


if __name__ == "__main__":
    print("🪛 RedditHarbor Multi-Project Setup")
    print("=" * 40)

    # Setup
    pipeline = setup_redditharbor()

    if pipeline:
        # Test with small sample first
        test_collection(pipeline)

        # Ask if user wants to run full sample
        response = input("\n📥 Run full sample collection? (y/n): ")
        if response.lower() == "y":
            run_sample_collection(pipeline)

    print("\n📋 Next Steps:")
    print("1. Configure your Reddit API credentials in redditharbor_config.py")
    print("2. Customize subreddits and collection parameters")
    print("3. Access your data at http://127.0.0.1:54323")
    print("4. Use the redditharbor schema for all your Reddit data analysis")
