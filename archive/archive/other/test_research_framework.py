#!/usr/bin/env .venv/bin/python
"""
Test RedditHarbor Research Framework
Verify the research system works without PII dependencies
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_research_framework():
    """Test the RedditHarbor research framework components"""
    print("🧪 RedditHarbor Research Framework Test")
    print("=" * 40)
    print("Testing core components without PII dependencies...")
    print()

    try:
        # Test 1: Configuration loading
        print("1️⃣ Testing configuration...")
        try:
            import config.settings as settings
            print("   ✅ Configuration loaded")
            print(f"   ✅ PII anonymization: {settings.ENABLE_PII_ANONYMIZATION}")
        except Exception as e:
            print(f"   ❌ Configuration failed: {e}")
            return False

        # Test 2: Reddit connection
        print("\n2️⃣ Testing Reddit API connection...")
        try:
            from redditharbor.login import reddit
            reddit_client = reddit(
                public_key=settings.REDDIT_PUBLIC,
                secret_key=settings.REDDIT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT
            )
            print("   ✅ Reddit API connected")
        except Exception as e:
            print(f"   ❌ Reddit connection failed: {e}")
            return False

        # Test 3: Supabase connection
        print("\n3️⃣ Testing Supabase connection...")
        try:
            from redditharbor.login import supabase
            supabase_client = supabase(
                url=settings.SUPABASE_URL,
                private_key=settings.SUPABASE_KEY
            )
            print("   ✅ Supabase connected")
        except Exception as e:
            print(f"   ❌ Supabase connection failed: {e}")
            return False

        # Test 4: Pipeline initialization
        print("\n4️⃣ Testing data pipeline...")
        try:
            from redditharbor.dock.pipeline import collect
            pipeline = collect(
                reddit_client=reddit_client,
                supabase_client=supabase_client,
                db_config=settings.DB_CONFIG
            )
            print("   ✅ Pipeline initialized")
        except Exception as e:
            print(f"   ❌ Pipeline initialization failed: {e}")
            return False

        # Test 5: Small data collection
        print("\n5️⃣ Testing small data collection...")
        try:
            # Test with a simple subreddit
            pipeline.subreddit_submission(
                subreddits=["python"],
                sort_types=["hot"],
                limit=2,  # Very small test
                mask_pii=settings.ENABLE_PII_ANONYMIZATION
            )
            print("   ✅ Small data collection test passed")
        except Exception as e:
            print(f"   ❌ Data collection failed: {e}")
            return False

        print("\n🎉 Research framework test PASSED!")
        print("✅ All core components working correctly")
        print("✅ Ready for full research deployment")
        print("\n📋 Next Steps:")
        print("   1. Install spaCy model: uv pip install en_core_web_lg")
        print("   2. Re-enable PII anonymization in config")
        print("   3. Run full research: python scripts/run_niche_research.py")

        return True

    except Exception as e:
        print(f"❌ Unexpected test failure: {e}")
        return False

if __name__ == "__main__":
    success = test_research_framework()
    sys.exit(0 if success else 1)
