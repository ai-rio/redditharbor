#!/usr/bin/env .venv/bin/python
"""
RedditHarbor Research: Skill Acquisition Pain Points
Research Question: What are the most common struggles people face when learning new skills?
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from redditharbor.dock.pipeline import collect
    from redditharbor.login import reddit, supabase

    from config.settings import *
except ImportError as e:
    print(f"Error: Could not import dependencies: {e}")
    sys.exit(1)

def research_skill_acquisition_pain_points():
    """Research skill acquisition pain points and learning struggles"""
    print("🎓 Research: Skill Acquisition Pain Points")
    print("=" * 50)

    # Initialize pipeline
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

    # Target subreddits focused on skill learning struggles
    skill_learning_subreddits = [
        "learnprogramming",
        "language_learning",
        "learnmath",
        "learnpython",
        "learnart",
        "ADHD_Programmers",
        "datascience",
        "webdev",
        "coding",
        "gamedev",
        "musictheory",
        "drawing"
    ]

    print(f"📊 Collecting data from {len(skill_learning_subreddits)} skill learning subreddits...")

    # Focus on recent learning struggles and questions
    sort_types = ["hot", "new"]  # Recent problems and popular discussions
    limit = 120  # Larger sample to capture different skill types

    # Collect submissions
    pipeline.subreddit_submission(
        subreddits=skill_learning_subreddits,
        sort_types=sort_types,
        limit=limit,
        mask_pii=ENABLE_PII_ANONYMIZATION
    )

    # Collect comments for detailed learning process insights
    print("📝 Collecting comment data for learning challenge analysis...")
    pipeline.subreddit_comment(
        subreddits=skill_learning_subreddits,
        limit=600,  # More comments for qualitative analysis
        mask_pii=ENABLE_PII_ANONYMIZATION
    )

    print("✅ Skill acquisition pain points research complete!")
    print("📈 Analyze patterns in Supabase Studio: http://127.0.0.1:54323")
    print("🔍 Look for recurring themes: motivation, resources, progress tracking, methods")

if __name__ == "__main__":
    research_skill_acquisition_pain_points()
