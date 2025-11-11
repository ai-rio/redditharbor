#!/usr/bin/env python3
"""
Test using the redditharbor pipeline directly
"""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redditharbor.dock.pipeline import collect
from redditharbor.login import reddit, supabase

from config.settings import (
    REDDIT_PUBLIC,
    REDDIT_SECRET,
    REDDIT_USER_AGENT,
    SUPABASE_KEY,
    SUPABASE_URL,
)

# Create clients
reddit_client = reddit(public_key=REDDIT_PUBLIC, secret_key=REDDIT_SECRET, user_agent=REDDIT_USER_AGENT)
supabase_client = supabase(url=SUPABASE_URL, private_key=SUPABASE_KEY)

print("Testing redditharbor pipeline directly...")
print("Target subreddits: personalfinance, investing, fitness")
print()

# Use the pipeline
try:
    result = collect(
        subreddits=["personalfinance", "investing", "fitness"],
        sort_types=["hot", "rising"],
        limit=10,
        mask_pii=False
    )

    print(f"Pipeline result: {result}")

    # Check data
    if result:
        print("\nChecking database...")
        subs_result = supabase_client.table('submissions').select('count').execute()
        comments_result = supabase_client.table('comments').select('count').execute()

        print(f"Submissions: {subs_result.data}")
        print(f"Comments: {comments_result.data}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
