#!/usr/bin/env python3
"""
Final test using the pipeline methods directly
"""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redditharbor.dock.pipeline import collect
from redditharbor.login import reddit, supabase
from config.settings import REDDIT_PUBLIC, REDDIT_SECRET, REDDIT_USER_AGENT, SUPABASE_URL, SUPABASE_KEY, DB_CONFIG

# Create clients
reddit_client = reddit(public_key=REDDIT_PUBLIC, secret_key=REDDIT_SECRET, user_agent=REDDIT_USER_AGENT)
supabase_client = supabase(url=SUPABASE_URL, private_key=SUPABASE_KEY)

# Create pipeline
pipeline = collect(reddit_client=reddit_client, supabase_client=supabase_client, db_config=DB_CONFIG)

print("=" * 80)
print("🚀 TESTING REDDITHARBOR PIPELINE")
print("=" * 80)
print()

# Test with one subreddit
print("📝 Collecting submissions from r/personalfinance...")
try:
    pipeline.subreddit_submission(
        subreddits=["personalfinance"],
        sort_types=["hot"],
        limit=5,
        mask_pii=False
    )
    print("✅ Submissions collected")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("💬 Collecting comments...")
try:
    pipeline.subreddit_comment(
        subreddits=["personalfinance"],
        limit=10,
        mask_pii=False
    )
    print("✅ Comments collected")
except Exception as e:
    print(f"❌ Error: {e}")

# Check results
print()
print("🔍 Checking database...")
try:
    subs_result = supabase_client.table('submissions').select('count').execute()
    comments_result = supabase_client.table('comments').select('count').execute()

    print(f"Total submissions: {len(subs_result.data) if subs_result.data else 0}")
    print(f"Total comments: {len(comments_result.data) if comments_result.data else 0}")

    # Get actual count
    if subs_result.data:
        count = subs_result.data[0]['count'] if 'count' in subs_result.data[0] else 'N/A'
        print(f"Submissions count: {count}")
    if comments_result.data:
        count = comments_result.data[0]['count'] if 'count' in comments_result.data[0] else 'N/A'
        print(f"Comments count: {count}")

except Exception as e:
    print(f"Error checking database: {e}")

print()
print("=" * 80)
print("✅ TEST COMPLETE")
print("=" * 80)
