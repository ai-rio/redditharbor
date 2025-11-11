#!/usr/bin/env python3
"""Fix comment-submission linkage for commercial data"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redditharbor.login import supabase

from config.settings import SUPABASE_KEY, SUPABASE_URL

client = supabase(url=SUPABASE_URL, private_key=SUPABASE_KEY)

print("=" * 80)
print("FIXING COMMENT-SUBMISSION LINKAGE")
print("=" * 80)

# First, let's see what we have
result = client.table('comments').select('id', count='exact').is_('submission_id', None).execute()
unlinked = result.count
print(f"\nUnlinked comments: {unlinked}")

result = client.table('comments').select('id', count='exact').neq('submission_id', None).execute()
linked = result.count
print(f"Linked comments: {linked}")

# Get a sample to see the pattern
result = client.table('comments').select('link_id').is_('submission_id', None).limit(5).execute()
print("\nSample unlinked comment link_ids:")
for row in result.data:
    print(f"  {row['link_id']}")

result = client.table('submissions').select('submission_id').limit(5).execute()
print("\nSample submission submission_ids:")
for row in result.data:
    print(f"  {row['submission_id']}")

# Try to match and update
print("\nAttempting to match link_id to submission_id...")

# This is a complex update - we need to do it carefully
# For now, let's just show what would happen
print("\nThis requires a SQL UPDATE with JOIN...")
print("Skipping automated fix - manual intervention needed.")
print("\nExpected SQL:")
print("""
UPDATE comments
SET submission_id = s.id
FROM submissions s
WHERE comments.link_id = s.submission_id
  AND comments.submission_id IS NULL;
""")
