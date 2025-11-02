#!/usr/bin/env .venv/bin/python
"""
Quick Demo: Run a Small Research Project
"""

# Try to import dependencies with fallback
try:
    from redditharbor.dock.pipeline import collect
    from redditharbor.login import reddit, supabase
    from redditharbor_config import *
except ImportError as e:
    print(f"Warning: Could not import dependencies: {e}")
    # Define fallbacks for demo
    reddit = None
    supabase = None
    collect = None

    # Try config fallback
    try:
        from config import settings as config

        REDDIT_PUBLIC = config.REDDIT_PUBLIC
        REDDIT_SECRET = config.REDDIT_SECRET
        REDDIT_USER_AGENT = config.REDDIT_USER_AGENT
        SUPABASE_URL = config.SUPABASE_URL
        SUPABASE_KEY = config.SUPABASE_KEY
        DEFAULT_SUBREDDITS = config.DEFAULT_SUBREDDITS
        DEFAULT_LIMIT = config.DEFAULT_LIMIT
    except ImportError as e:
        print(f"Warning: Could not import configuration: {e}")
        import sys

        sys.exit(1)


def demo_tech_trends_research():
    """Demonstrate a mini research project on tech trends"""

    print("🔬 Demo Research: Tech Trends Analysis")
    print("=" * 40)
    print("Research Question: What are the current hot topics in tech subreddits?")
    print()

    try:
        # Initialize pipeline
        reddit_client = reddit(
            public_key=REDDIT_PUBLIC,
            secret_key=REDDIT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )

        supabase_client = supabase(url=SUPABASE_URL, private_key=SUPABASE_KEY)

        pipeline = collect(
            reddit_client=reddit_client,
            supabase_client=supabase_client,
            db_config=DB_CONFIG,
        )

        # Mini research: Collect from 3 tech subreddits
        tech_subreddits = ["technology", "programming", "startups"]

        print(f"📊 Collecting data from: {', '.join(tech_subreddits)}")
        print("🎯 Focus: Hot discussions (current trends)")
        print("📈 Sample size: 5 posts per subreddit")
        print()

        pipeline.subreddit_submission(
            subreddits=tech_subreddits,
            sort_types=["hot"],
            limit=5,
            mask_pii=False,  # Disable PII for demo
        )

        print("✅ Demo research data collection complete!")
        print()

        # Analyze the collected data
        print("📋 Research Results Summary:")

        # Get the collected submissions
        result = (
            supabase_client.table("submission")
            .select("submission_id, title, subreddit, score")
            .execute()
        )

        if result.data:
            print(f"   📄 Collected {len(result.data)} submissions")
            print()
            print("🔥 Current Hot Topics:")

            for i, post in enumerate(result.data, 1):
                score_display = (
                    f"[{post.get('score', {}).get('initial', 0)} points]"
                    if isinstance(post.get("score"), dict)
                    else "[Score: N/A]"
                )
                print(
                    f"   {i}. r/{post['subreddit']}: {post['title'][:60]}... {score_display}"
                )

        print()
        print("🎯 Research Insights Available:")
        print("   • Trending topics across tech communities")
        print("   • Cross-community discussion patterns")
        print("   • Popular themes and concerns")
        print("   • Engagement patterns (via scores)")

        print()
        print("🔗 Access full dataset:")
        print("   🌐 Supabase Studio: http://127.0.0.1:54323")
        print("   📊 Tables: redditharbor.submission")

        return True

    except Exception as e:
        print(f"❌ Demo research failed: {e}")
        return False


if __name__ == "__main__":
    demo_tech_trends_research()
