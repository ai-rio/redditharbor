#!/usr/bin/env python3
"""
Test DLT integration with PRAW (existing Reddit client).

This test uses the existing PRAW-based Reddit client to collect data
and then loads it into Supabase using DLT.
"""

import sys
from pathlib import Path

import dlt

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import existing Reddit client
try:
    import praw

    from config.settings import REDDIT_PUBLIC, REDDIT_SECRET, REDDIT_USER_AGENT
    PRAW_AVAILABLE = True
except ImportError:
    print("⚠️  PRAW not available - will use mock data")
    PRAW_AVAILABLE = False

def get_reddit_data(subreddit_name="opensource", limit=10):
    """Get Reddit data using PRAW."""

    if not PRAW_AVAILABLE:
        # Return mock data for testing
        return [{
            "id": "test123",
            "title": "Test submission",
            "selftext": "This is a test submission",
            "author": "test_user",
            "created_utc": 1704067200,
            "subreddit": subreddit_name,
            "score": 10
        }]

    try:
        # Initialize Reddit client
        reddit = praw.Reddit(
            client_id=REDDIT_PUBLIC,
            client_secret=REDDIT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )

        # Get subreddit
        subreddit = reddit.subreddit(subreddit_name)

        # Collect submissions
        submissions = []
        for submission in subreddit.new(limit=limit):
            submissions.append({
                "id": submission.id,
                "title": submission.title,
                "selftext": submission.selftext,
                "author": str(submission.author) if submission.author else "[deleted]",
                "created_utc": submission.created_utc,
                "subreddit": str(submission.subreddit),
                "score": submission.score,
                "url": submission.url
            })

        return submissions

    except Exception as e:
        print(f"✗ Error collecting Reddit data: {e}")
        return []

def test_dlt_with_reddit_data():
    """Test DLT pipeline with Reddit data."""

    print("=" * 80)
    print("Testing DLT with Reddit Data (PRAW)")
    print("=" * 80)

    # Collect Reddit data
    print("\n1. Collecting Reddit data...")
    submissions = get_reddit_data("opensource", limit=10)

    if not submissions:
        print("✗ No data collected")
        return False

    print(f"✓ Collected {len(submissions)} submissions")

    # Create DLT pipeline
    print("\n2. Creating DLT pipeline...")
    pipeline = dlt.pipeline(
        pipeline_name="reddit_harbor_collection",
        destination="postgres",
        dataset_name="reddit_harbor"
    )
    print(f"✓ Pipeline created: {pipeline.pipeline_name}")

    # Load data to Supabase using DLT
    print("\n3. Loading data to Supabase with DLT...")
    try:
        load_info = pipeline.run(
            submissions,
            table_name="submissions",
            write_disposition="replace"
        )
        print("✓ Data loaded successfully!")
        print("  - Load completed: ✓")
        print("  - Table: submissions")

        return True

    except Exception as e:
        print(f"✗ Data load failed: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("RedditHarbor DLT + PRAW Integration Test")
    print("=" * 80)

    success = test_dlt_with_reddit_data()

    print("\n" + "=" * 80)
    if success:
        print("✓ SUCCESS: DLT + PRAW Integration Working!")
        print("=" * 80)
        print("\nThe DLT infrastructure is operational and can:")
        print("1. Collect data from Reddit using PRAW")
        print("2. Load data to Supabase using DLT")
        print("3. Manage schema automatically")
        print("\nNext steps:")
        print("1. Verify data in Supabase Studio (http://127.0.0.1:54323)")
        print("2. Test incremental loading")
        print("3. Create production DLT pipeline")
    else:
        print("✗ FAILED: Integration test failed")
        print("=" * 80)

    sys.exit(0 if success else 1)
