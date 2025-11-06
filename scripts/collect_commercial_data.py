#!/usr/bin/env python3
"""
Collect data from top 5 monetizable subreddits
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redditharbor.login import reddit, supabase
from redditharbor.dock.pipeline import collect
from config.settings import (
    REDDIT_PUBLIC, REDDIT_SECRET, REDDIT_USER_AGENT,
    SUPABASE_URL, SUPABASE_KEY, DB_CONFIG
)

def main():
    print("=" * 80)
    print("COLLECTING HIGH-VALUE COMMERCIAL DATA")
    print("=" * 80)
    print()

    # Top 5 subreddits from manual test
    TOP_SUBREDDITS = [
        "smallbusiness",
        "startups",
        "SaaS",
        "entrepreneur",
        "indiehackers"
    ]

    print(f"Target subreddits: {', '.join(TOP_SUBREDDITS)}")
    print()

    # Create clients
    print("Creating Reddit and Supabase clients...")
    reddit_client = reddit(
        public_key=REDDIT_PUBLIC,
        secret_key=REDDIT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
    supabase_client = supabase(
        url=SUPABASE_URL,
        private_key=SUPABASE_KEY
    )

    # Create pipeline
    print("Initializing RedditHarbor pipeline...")
    pipeline = collect(
        reddit_client=reddit_client,
        supabase_client=supabase_client,
        db_config=DB_CONFIG
    )

    # Collection parameters
    sort_types = ["hot"]
    limit = 50  # Posts per subreddit
    comment_limit = 20     # Comments per post
    mask_pii = False

    print(f"Collection parameters:")
    print(f"  - Submissions per subreddit: {limit}")
    print(f"  - Comments per submission: {comment_limit}")
    print(f"  - Sort types: {', '.join(sort_types)}")
    print()

    for subreddit in TOP_SUBREDDITS:
        print(f"\n📥 Collecting from r/{subreddit}...")
        print("-" * 60)

        # Collect submissions
        print("  📝 Collecting submissions...")
        pipeline.subreddit_submission(
            subreddits=[subreddit],
            sort_types=sort_types,
            limit=limit
        )

        # Collect comments
        print("  💬 Collecting comments...")
        pipeline.subreddit_comment(
            subreddits=[subreddit],
            sort_types=sort_types,
            limit=comment_limit
        )

        print(f"✅ r/{subreddit} complete")

    print("\n" + "=" * 80)
    print("COLLECTION COMPLETE!")
    print("=" * 80)
    print("\nNext step: Test AI insights with commercial data")
    print()

if __name__ == "__main__":
    main()
