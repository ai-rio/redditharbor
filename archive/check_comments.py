#!/usr/bin/env python3
"""Check which submissions have comments"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redditharbor.login import supabase

from config.settings import SUPABASE_KEY, SUPABASE_URL

client = supabase(url=SUPABASE_URL, private_key=SUPABASE_KEY)

print("=" * 80)
print("CHECKING SUBMISSIONS FOR COMMENTS")
print("=" * 80)

# Get a sample of submissions from commercial subreddits
result = client.table('submissions').select('id, title, subreddit').neq('subreddit', 'Fitness').limit(20).execute()

submissions_with_comments = []

for row in result.data:
    sub_id = row['id']

    # Count comments
    comment_result = client.table('comments').select('id', count='exact').eq('submission_id', sub_id).execute()

    if hasattr(comment_result, 'count') and comment_result.count > 0:
        submissions_with_comments.append({
            'id': sub_id,
            'title': row['title'],
            'subreddit': row['subreddit'],
            'count': comment_result.count
        })

print(f"\nFound {len(submissions_with_comments)} submissions with comments out of {len(result.data)} checked:\n")

for sub in sorted(submissions_with_comments, key=lambda x: x['count'], reverse=True)[:10]:
    print(f"{sub['count']:3} comments - r/{sub['subreddit']:15}")
    print(f"   {sub['title'][:70]}")
    print()

if len(submissions_with_comments) == 0:
    print("NO submissions with comments found!")
    print("\nThis confirms the issue: problem posts don't have comments,")
    print("so the scoring algorithm can't extract evidence.")
