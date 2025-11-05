#!/usr/bin/env python3
"""
Fresh test with brand new client initialization
"""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redditharbor.login import reddit, supabase
from config.settings import REDDIT_PUBLIC, REDDIT_SECRET, REDDIT_USER_AGENT, SUPABASE_URL, SUPABASE_KEY, DB_CONFIG

# Create fresh clients (force new connection)
reddit_client = reddit(public_key=REDDIT_PUBLIC, secret_key=REDDIT_SECRET, user_agent=REDDIT_USER_AGENT)
supabase_client = supabase(url=SUPABASE_URL, private_key=SUPABASE_KEY)

print("=" * 80)
print("🚀 FRESH TEST WITH NEW CLIENT CONNECTIONS")
print("=" * 80)
print()

# Test with minimal data
print("📝 Testing single submission from r/personalfinance...")
try:
    from redditharbor.dock.pipeline import collect
    pipeline = collect(reddit_client=reddit_client, supabase_client=supabase_client, db_config=DB_CONFIG)

    # Use the direct method
    pipeline.subreddit_submission(
        subreddits=["personalfinance"],
        sort_types=["hot"],
        limit=1,  # Just 1 submission
        mask_pii=False
    )
    print("✅ Submission collected successfully!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("✅ TEST COMPLETE")
print("=" * 80)
