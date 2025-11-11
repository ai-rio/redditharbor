#!/usr/bin/env .venv/bin/python
"""
RedditHarbor Research: Chronic Disease Daily Management
Research Question: What are the most common daily struggles people face managing chronic conditions?
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

def research_chronic_disease_management():
    """Research chronic disease daily management struggles"""
    print("🏥 Research: Chronic Disease Daily Management")
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

    # Target subreddits focused on chronic disease management
    chronic_disease_subreddits = [
        "diabetes",
        "ChronicPain",
        "ibs",
        "epilepsy",
        "fibromyalgia",
        "ChronicIllness",
        "MultipleSclerosis",
        "CrohnsDisease",
        "Lupus",
        "migraine",
        "asthma",
        "ADHD"
    ]

    print(f"📊 Collecting data from {len(chronic_disease_subreddits)} chronic disease subreddits...")

    # Focus on recent daily management discussions
    sort_types = ["hot", "new"]  # Recent struggles and popular management tips
    limit = 100  # Sufficient sample across different conditions

    # Collect submissions
    pipeline.subreddit_submission(
        subreddits=chronic_disease_subreddits,
        sort_types=sort_types,
        limit=limit,
        mask_pii=ENABLE_PII_ANONYMIZATION
    )

    # Collect comments for detailed daily routine insights
    print("📝 Collecting comment data for daily management challenge analysis...")
    pipeline.subreddit_comment(
        subreddits=chronic_disease_subreddits,
        limit=500,  # More comments for detailed management insights
        mask_pii=ENABLE_PII_ANONYMIZATION
    )

    print("✅ Chronic disease management research complete!")
    print("📈 Analyze patterns in Supabase Studio: http://127.0.0.1:54323")
    print("🔍 Look for recurring themes: medication, symptoms, tracking, daily routines")

if __name__ == "__main__":
    research_chronic_disease_management()
