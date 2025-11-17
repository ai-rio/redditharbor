#!/usr/bin/env python3
"""Execute the SQL to fix comment-submission linkage"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import psycopg2

# Connect to Supabase PostgreSQL directly
# Use the connection URL from environment or .env
SUPABASE_DB_URL = os.environ.get('SUPABASE_DB_URL')
if not SUPABASE_DB_URL:
    # Default local Supabase URL
    SUPABASE_DB_URL = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

conn = psycopg2.connect(SUPABASE_DB_URL)
cur = conn.cursor()

print("=" * 80)
print("FIXING COMMENT-SUBMISSION LINKAGE")
print("=" * 80)

# Check before
cur.execute("SELECT COUNT(*) FROM comments WHERE submission_id IS NULL")
before = cur.fetchone()[0]
print(f"\nUnlinked comments BEFORE: {before}")

# Execute the update
print("\nExecuting UPDATE...")
update_sql = """
UPDATE comments
SET submission_id = s.id
FROM submissions s
WHERE comments.link_id = s.submission_id
  AND comments.submission_id IS NULL;
"""

cur.execute(update_sql)
rows_updated = cur.rowcount
print(f"Rows updated: {rows_updated}")

# Check after
cur.execute("SELECT COUNT(*) FROM comments WHERE submission_id IS NULL")
after = cur.fetchone()[0]
print(f"Unlinked comments AFTER: {after}")

# Commit
conn.commit()
print("\n✅ Changes committed!")

# Verify
cur.execute("SELECT COUNT(*) FROM comments")
total = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM comments WHERE submission_id IS NOT NULL")
linked = cur.fetchone()[0]
print(f"\nTotal comments: {total}")
print(f"Linked comments: {linked}")
print(f"Success rate: {linked/total*100:.1f}%")

cur.close()
conn.close()
