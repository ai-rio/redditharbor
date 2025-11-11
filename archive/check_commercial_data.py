#!/usr/bin/env python3
"""Check commercial data in database"""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redditharbor.login import supabase

from config.settings import SUPABASE_KEY, SUPABASE_URL

# Initialize Supabase
client = supabase(url=SUPABASE_URL, private_key=SUPABASE_KEY)

# Check submissions by subreddit
print("=" * 80)
print("SUBMISSIONS BY SUBREDDIT")
print("=" * 80)

result = client.table('submissions').select('subreddit').execute()
subreddits = {}
for row in result.data:
    sub = row['subreddit']
    subreddits[sub] = subreddits.get(sub, 0) + 1

for sub, count in sorted(subreddits.items(), key=lambda x: x[1], reverse=True):
    print(f"  {sub:25} {count:4} posts")

# Check top smallbusiness opportunities
print("\n" + "=" * 80)
print("TOP SMALLBUSINESS OPPORTUNITIES")
print("=" * 80)

result = client.table('opportunity_analysis').select('submission_id, score, title, text').eq('subreddit', 'smallbusiness').order('score', desc=True).limit(3).execute()

for i, row in enumerate(result.data, 1):
    print(f"\n{i}. Score: {row['score']}")
    print(f"   Title: {row['title'][:80]}...")
    if row['text']:
        print(f"   Text:  {row['text'][:100]}...")

print("\n" + "=" * 80)
print("CHECK COMPLETE")
print("=" * 80)
