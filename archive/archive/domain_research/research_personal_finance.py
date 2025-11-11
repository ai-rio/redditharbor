#!/usr/bin/env .venv/bin/python
"""
RedditHarbor Research: Personal Finance Daily Struggles
Research Question: What are the most common, recurring personal finance problems people face daily?
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

def research_personal_finance_struggles():
    """Research personal finance daily struggles and recurring problems"""
    print("💰 Research: Personal Finance Daily Struggles")
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

    # Target subreddits focused on daily personal finance struggles
    personal_finance_subreddits = [
        "personalfinance",
        "poverty",
        "debtfree",
        "FinancialPlanning",
        "StudentLoans",
        "frugal",
        "budget",
        "RealPersonalFinance"
    ]

    print(f"📊 Collecting data from {len(personal_finance_subreddits)} personal finance subreddits...")

    # Focus on recent discussions and common problems
    sort_types = ["hot", "new"]  # Recent and trending issues
    limit = 100  # Larger sample for pattern analysis

    # Collect submissions
    pipeline.subreddit_submission(
        subreddits=personal_finance_subreddits,
        sort_types=sort_types,
        limit=limit,
        mask_pii=ENABLE_PII_ANONYMIZATION
    )

    # Also collect comments for deeper insight into specific problems
    print("📝 Collecting comment data for detailed problem analysis...")
    pipeline.subreddit_comment(
        subreddits=personal_finance_subreddits,
        limit=500,  # More comments for qualitative analysis
        mask_pii=ENABLE_PII_ANONYMIZATION
    )

    print("✅ Personal finance struggles research complete!")
    print("📈 Analyze patterns in Supabase Studio: http://127.0.0.1:54323")
    print("🔍 Look for recurring themes: budgeting, debt, saving, daily money decisions")

if __name__ == "__main__":
    research_personal_finance_struggles()
