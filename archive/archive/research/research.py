#!/usr/bin/env .venv/bin/python
"""
Ready-to-use Research Project Templates for RedditHarbor
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Try to import dependencies with fallback
try:
    from redditharbor.dock.pipeline import collect
    from redditharbor.login import reddit, supabase

    from config.settings import *
except ImportError as e:
    print(f"Warning: Could not import dependencies: {e}")
    # Define fallbacks
    reddit = None
    supabase = None
    collect = None

    # Try config fallback
    try:
        import redditharbor_config

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
        DEFAULT_SUBREDDITS = []
        DEFAULT_SORT_TYPES = []
        DEFAULT_LIMIT = 100
        ENABLE_PII_ANONYMIZATION = True


def initialize_pipeline():
    """Initialize the RedditHarbor pipeline"""
    reddit_client = reddit(
        public_key=REDDIT_PUBLIC, secret_key=REDDIT_SECRET, user_agent=REDDIT_USER_AGENT
    )

    supabase_client = supabase(url=SUPABASE_URL, private_key=SUPABASE_KEY)

    return collect(
        reddit_client=reddit_client,
        supabase_client=supabase_client,
        db_config=DB_CONFIG,
    )


# ==================== RESEARCH PROJECT TEMPLATES ====================


def project_1_programming_trends():
    """
    RESEARCH PROJECT 1: Programming Language Trends Analysis
    Research Question: Which programming languages are gaining/losing popularity?
    """
    print("🔬 Project 1: Programming Language Trends Analysis")
    print("=" * 50)

    pipeline = initialize_pipeline()

    programming_subreddits = [
        "python",
        "javascript",
        "java",
        "cpp",
        "rust",
        "golang",
        "typescript",
        "csharp",
        "php",
        "ruby",
    ]

    sort_types = ["hot", "top"]  # Hot for current trends, Top for all-time
    limit = 50  # Collect 50 posts from each sort type

    print(
        f"📊 Collecting data from {len(programming_subreddits)} programming subreddits..."
    )

    pipeline.subreddit_submission(
        subreddits=programming_subreddits,
        sort_types=sort_types,
        limit=limit,
        mask_pii=ENABLE_PII_ANONYMIZATION,
    )

    print("✅ Programming trends data collection complete!")
    print("📈 Analyze trends in Supabase Studio: http://127.0.0.1:54323")


def project_2_tech_industry_sentiment():
    """
    RESEARCH PROJECT 2: Tech Industry Sentiment Analysis
    Research Question: How do tech communities discuss major companies and products?
    """
    print("💼 Project 2: Tech Industry Sentiment Analysis")
    print("=" * 50)

    pipeline = initialize_pipeline()

    tech_subreddits = [
        "technology",
        "programming",
        "startups",
        "gadgets",
        "apple",
        "android",
        "windows",
        "linux",
        "Privacy",
    ]

    sort_types = ["hot", "new"]  # Recent discussions and trending topics
    limit = 30

    print("📊 Collecting tech industry sentiment data...")

    pipeline.subreddit_submission(
        subreddits=tech_subreddits,
        sort_types=sort_types,
        limit=limit,
        mask_pii=ENABLE_PII_ANONYMIZATION,
    )

    print("✅ Tech sentiment data collection complete!")
    print("💡 Analyze company mentions and sentiment patterns in Supabase")


def project_3_learning_community_analysis():
    """
    RESEARCH PROJECT 3: Learning Community Behavior Analysis
    Research Question: How do people seek help and share knowledge in learning communities?
    """
    print("🎓 Project 3: Learning Community Behavior Analysis")
    print("=" * 50)

    pipeline = initialize_pipeline()

    learning_subreddits = [
        "learnprogramming",
        "learnpython",
        "webdev",
        "datascience",
        "learnmath",
        "AskComputerScience",
        "ComputerScience",
        "coding",
    ]

    sort_types = ["hot", "new"]  # Recent questions and popular discussions
    limit = 40

    print("📊 Collecting learning community interaction data...")

    pipeline.subreddit_submission(
        subreddits=learning_subreddits,
        sort_types=sort_types,
        limit=limit,
        mask_pii=ENABLE_PII_ANONYMIZATION,
    )

    # Also collect comments for interaction analysis
    print("📝 Collecting comment data for interaction analysis...")
    pipeline.subreddit_comment(
        subreddits=learning_subreddits,
        limit=200,  # More comments for interaction analysis
        mask_pii=ENABLE_PII_ANONYMIZATION,
    )

    print("✅ Learning community data collection complete!")
    print("🔍 Analyze question patterns and response behaviors")


def project_4_ai_ml_monitoring():
    """
    RESEARCH PROJECT 4: AI/ML Discussion Monitoring
    Research Question: What are the trending topics in AI and machine learning communities?
    """
    print("🤖 Project 4: AI/ML Discussion Monitoring")
    print("=" * 50)

    pipeline = initialize_pipeline()

    ai_ml_subreddits = [
        "MachineLearning",
        "artificial",
        "deeplearning",
        "OpenAI",
        "ChatGPT",
        "singularity",
        "MLQuestions",
        "learnmachinelearning",
    ]

    sort_types = ["hot", "rising"]  # Focus on emerging and trending content
    limit = 60  # More data for trend analysis

    print("📊 Collecting AI/ML trending discussions...")

    pipeline.subreddit_submission(
        subreddits=ai_ml_subreddits,
        sort_types=sort_types,
        limit=limit,
        mask_pii=ENABLE_PII_ANONYMIZATION,
    )

    print("✅ AI/ML monitoring data collection complete!")
    print("📈 Track emerging AI topics and community concerns")


def project_5_startup_ecosystem():
    """
    RESEARCH PROJECT 5: Startup Ecosystem Analysis
    Research Question: What challenges and opportunities do entrepreneurs discuss?
    """
    print("🚀 Project 5: Startup Ecosystem Analysis")
    print("=" * 50)

    pipeline = initialize_pipeline()

    startup_subreddits = [
        "startups",
        "Entrepreneur",
        "SaaS",
        "smallbusiness",
        "SideProject",
        "IndieHackers",
        "freelance",
        "sysadmin",
    ]

    sort_types = ["hot", "top"]  # Popular and proven advice
    limit = 35

    print("📊 Collecting startup ecosystem insights...")

    pipeline.subreddit_submission(
        subreddits=startup_subreddits,
        sort_types=sort_types,
        limit=limit,
        mask_pii=ENABLE_PII_ANONYMIZATION,
    )

    print("✅ Startup ecosystem data collection complete!")
    print("💼 Analyze entrepreneur challenges and success factors")


def project_6_cross_community_viral_content():
    """
    RESEARCH PROJECT 6: Cross-Community Viral Content Analysis
    Research Question: What content spreads across multiple Reddit communities?
    """
    print("📈 Project 6: Cross-Community Viral Content Analysis")
    print("=" * 50)

    pipeline = initialize_pipeline()

    # Mix of different community types
    diverse_subreddits = [
        "programming",
        "gaming",
        "science",
        "technology",
        "AskReddit",
        "todayilearned",
        "interestingasfuck",
        "news",
        "videos",
        "pics",
    ]

    sort_types = ["hot", "top"]  # Focus on popular content
    limit = 25  # Smaller sample for focused analysis

    print("📊 Collecting diverse content for viral analysis...")

    pipeline.subreddit_submission(
        subreddits=diverse_subreddits,
        sort_types=sort_types,
        limit=limit,
        mask_pii=ENABLE_PII_ANONYMIZATION,
    )

    print("✅ Viral content data collection complete!")
    print("🔍 Analyze cross-community content patterns")


# ==================== INTERACTIVE RESEARCH PROJECT SELECTOR ====================


def run_research_project():
    """Interactive menu for selecting research projects"""

    print("🔬 RedditHarbor Research Projects")
    print("=" * 40)
    print("Available research projects:")
    print()
    print("1. 📊 Programming Language Trends Analysis")
    print("2. 💼 Tech Industry Sentiment Analysis")
    print("3. 🎓 Learning Community Behavior Analysis")
    print("4. 🤖 AI/ML Discussion Monitoring")
    print("5. 🚀 Startup Ecosystem Analysis")
    print("6. 📈 Cross-Community Viral Content Analysis")
    print("7. 🧪 Custom Research (Define your own)")
    print()

    try:
        choice = input("Select research project (1-7): ")

        if choice == "1":
            project_1_programming_trends()
        elif choice == "2":
            project_2_tech_industry_sentiment()
        elif choice == "3":
            project_3_learning_community_analysis()
        elif choice == "4":
            project_4_ai_ml_monitoring()
        elif choice == "5":
            project_5_startup_ecosystem()
        elif choice == "6":
            project_6_cross_community_viral_content()
        elif choice == "7":
            custom_research_project()
        else:
            print("❌ Invalid choice. Please select 1-7.")

    except KeyboardInterrupt:
        print("\n👋 Research session cancelled.")
    except Exception as e:
        print(f"❌ Error: {e}")


def custom_research_project():
    """Guide user through creating a custom research project"""

    print("🧪 Custom Research Project Setup")
    print("=" * 30)

    try:
        # Get research parameters from user
        subreddits_input = input("Enter subreddits (comma-separated): ")
        subreddits = [s.strip() for s in subreddits_input.split(",")]

        print("Sort types: hot, new, top, rising, controversial")
        sort_types_input = input("Enter sort types (comma-separated): ")
        sort_types = [s.strip() for s in sort_types_input.split(",")]

        limit = int(input("Number of posts per subreddit (suggest 20-100): "))

        pipeline = initialize_pipeline()

        print(
            f"\n📊 Collecting custom research data from {len(subreddits)} subreddits..."
        )

        pipeline.subreddit_submission(
            subreddits=subreddits,
            sort_types=sort_types,
            limit=limit,
            mask_pii=ENABLE_PII_ANONYMIZATION,
        )

        print("✅ Custom research data collection complete!")

    except Exception as e:
        print(f"❌ Error setting up custom project: {e}")


def generate_research_report():
    """Generate a summary report of collected data"""

    print("📋 Generating Research Data Report...")
    print("=" * 35)

    try:
        supabase_client = supabase(url=SUPABASE_URL, private_key=SUPABASE_KEY)

        # Get counts from each table
        redditor_result = (
            supabase_client.table("redditor").select("count", count="exact").execute()
        )
        submission_result = (
            supabase_client.table("submission").select("count", count="exact").execute()
        )
        comment_result = (
            supabase_client.table("comment").select("count", count="exact").execute()
        )

        print("📊 Dataset Summary:")
        print(f"   👥 Redditors: {redditor_result.count}")
        print(f"   📄 Submissions: {submission_result.count}")
        print(f"   💬 Comments: {comment_result.count}")

        # Get subreddit distribution
        submission_data = (
            supabase_client.table("submission").select("subreddit").execute()
        )
        subreddit_counts = {}
        for item in submission_data.data:
            subreddit_counts[item["subreddit"]] = (
                subreddit_counts.get(item["subreddit"], 0) + 1
            )

        print("\n🏷️  Subreddit Distribution:")
        for subreddit, count in sorted(
            subreddit_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]:
            print(f"   r/{subreddit}: {count} posts")

        # Get date range
        date_result = (
            supabase_client.table("submission")
            .select("created_at")
            .order("created_at", ascending=False)
            .limit(1)
            .execute()
        )
        if date_result.data:
            latest_date = date_result.data[0]["created_at"]
            print(f"\n📅 Latest data: {latest_date}")

        print("\n🔗 Access your data:")
        print("   Supabase Studio: http://127.0.0.1:54323")
        print("   Tables: redditor, submission, comment")

    except Exception as e:
        print(f"❌ Error generating report: {e}")


if __name__ == "__main__":
    print("🔬 RedditHarbor Research Platform")
    print("=" * 40)
    print("Choose an action:")
    print("1. Run research project")
    print("2. Generate data report")
    print("3. View research guide")

    action = input("Select action (1-3): ")

    if action == "1":
        run_research_project()
    elif action == "2":
        generate_research_report()
    elif action == "3":
        print("📚 Open research_types_guide.md for detailed research possibilities")
    else:
        print("❌ Invalid choice.")
