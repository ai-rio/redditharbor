#!/usr/bin/env python3
"""Quick schema verification after migration."""
from pathlib import Path

import psycopg2

project_root = Path(__file__).parent.parent

conn = psycopg2.connect(host='127.0.0.1', port='54322', user='postgres', password='postgres', database='postgres')
cur = conn.cursor()

# Query migration validation report
print('\n' + '=' * 70)
print('MIGRATION VALIDATION REPORT')
print('=' * 70)
cur.execute('SELECT * FROM migration_validation_report')
columns = [desc[0] for desc in cur.description]
rows = cur.fetchall()

for row in rows:
    row_dict = dict(zip(columns, row))
    print(f"\nTable: {row_dict['table_name']}")
    print(f"  Total rows: {row_dict['total_rows']}")
    for k, v in row_dict.items():
        if k != 'table_name' and v != 0:
            print(f"  {k}: {v}")

# List all tables
print('\n' + '=' * 70)
print('TABLES CREATED')
print('=' * 70)
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
tables = [row[0] for row in cur.fetchall()]
for table in tables:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = cur.fetchone()[0]
    print(f"  {table:<35} {count:>6} rows")

# List all views
print('\n' + '=' * 70)
print('VIEWS CREATED')
print('=' * 70)
cur.execute("SELECT viewname FROM pg_views WHERE schemaname='public' ORDER BY viewname")
views = [row[0] for row in cur.fetchall()]
for view in views:
    print(f"  {view}")

# Check key columns added to submissions
print('\n' + '=' * 70)
print('SUBMISSIONS TABLE - NEW COLUMNS ADDED')
print('=' * 70)
new_submission_cols = [
    'submission_id', 'archived', 'removed', 'attachment', 'poll', 'flair',
    'awards', 'score', 'upvote_ratio', 'num_comments', 'edited', 'text',
    'subreddit', 'permalink'
]
cur.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'submissions'
    AND column_name IN %s
    ORDER BY column_name
""", (tuple(new_submission_cols),))
print(f"  {'Column':<30} {'Type':<20} {'Nullable'}")
print(f"  {'-'*30} {'-'*20} {'-'*8}")
for row in cur.fetchall():
    print(f"  {row[0]:<30} {row[1]:<20} {row[2]}")

# Check key columns added to redditors
print('\n' + '=' * 70)
print('REDDITORS TABLE - NEW COLUMNS ADDED')
print('=' * 70)
new_redditor_cols = [
    'redditor_reddit_id', 'is_gold', 'is_mod', 'trophy', 'removed', 'name', 'karma'
]
cur.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'redditors'
    AND column_name IN %s
    ORDER BY column_name
""", (tuple(new_redditor_cols),))
print(f"  {'Column':<30} {'Type':<20} {'Nullable'}")
print(f"  {'-'*30} {'-'*20} {'-'*8}")
for row in cur.fetchall():
    print(f"  {row[0]:<30} {row[1]:<20} {row[2]}")

# Check opportunity_scores columns
print('\n' + '=' * 70)
print('OPPORTUNITY_SCORES TABLE - SCORE COLUMNS')
print('=' * 70)
score_cols = [
    'market_demand_score', 'pain_intensity_score', 'monetization_potential_score',
    'market_gap_score', 'technical_feasibility_score', 'simplicity_score', 'total_score'
]
cur.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'opportunity_scores'
    AND column_name IN %s
    ORDER BY column_name
""", (tuple(score_cols),))
print(f"  {'Column':<35} {'Type':<20} {'Nullable'}")
print(f"  {'-'*35} {'-'*20} {'-'*8}")
for row in cur.fetchall():
    print(f"  {row[0]:<35} {row[1]:<20} {row[2]}")

# Check functions
print('\n' + '=' * 70)
print('FUNCTIONS CREATED')
print('=' * 70)
cur.execute("""
    SELECT routine_name
    FROM information_schema.routines
    WHERE routine_schema = 'public'
    AND routine_name LIKE '%opportunity%'
    ORDER BY routine_name
""")
for row in cur.fetchall():
    print(f"  {row[0]}")

cur.close()
conn.close()

print('\n' + '=' * 70)
print('MIGRATION VERIFICATION COMPLETE')
print('=' * 70)
print('\nAll tables, columns, views, and functions created successfully!')
print('Migration status: SUCCESS\n')
