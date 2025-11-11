#!/usr/bin/env .venv/bin/python
"""
RedditHarbor Research: Budget Travel Constraints
Research Question: What are the most common budget-related frustrations and challenges travelers face?
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

def research_budget_travel_constraints():
    """Research budget travel constraints and frustrations"""
    print("✈️ Research: Budget Travel Constraints")
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

    # Target subreddits focused on budget travel
    budget_travel_subreddits = [
        "solotravel",
        "backpacking",
        "travel",
        "Flights",
        "TravelHacks",
        "Shoestring",
        "budgettravel",
        "nomads",
        "digitalnomad",
        "hostels",
        "couchsurfing"
    ]

    print(f"📊 Collecting data from {len(budget_travel_subreddits)} budget travel subreddits...")

    # Focus on recent budget travel discussions and frustrations
    sort_types = ["hot", "new"]  # Recent budget concerns and popular money-saving tips
    limit = 100  # Good sample across different travel types

    # Collect submissions
    pipeline.subreddit_submission(
        subreddits=budget_travel_subreddits,
        sort_types=sort_types,
        limit=limit,
        mask_pii=ENABLE_PII_ANONYMIZATION
    )

    # Collect comments for detailed budget challenge insights
    print("📝 Collecting comment data for budget constraint analysis...")
    pipeline.subreddit_comment(
        subreddits=budget_travel_subreddits,
        limit=500,  # More comments for detailed frustration insights
        mask_pii=ENABLE_PII_ANONYMIZATION
    )

    print("✅ Budget travel constraints research complete!")
    print("📈 Analyze patterns in Supabase Studio: http://127.0.0.1:54323")
    print("🔍 Look for recurring themes: hidden costs, booking issues, money-saving strategies")

if __name__ == "__main__":
    research_budget_travel_constraints()
