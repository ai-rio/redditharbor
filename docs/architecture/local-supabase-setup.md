# Local Supabase Development Setup

## Overview

This project uses a **local Supabase environment** for development. This document explains how it differs from cloud Supabase and how to work with it.

## Local vs Cloud Differences

### 1. Migrations

**Cloud Supabase:**
```bash
supabase db push  # Deploy to cloud
```

**Local Supabase:**
```bash
supabase start                # Start local instance
supabase migration up         # Apply pending migrations
supabase migration list       # See all migrations
```

### 2. Database URLs

**Cloud:** `https://xxxxx.supabase.co`

**Local:**
```
API URL:      http://127.0.0.1:54321
Studio URL:   http://127.0.0.1:54323
Direct DB:    postgresql://postgres:postgres@127.0.0.1:54322/postgres
```

### 3. Migration File Naming

**Requirement:** Supabase migrations must use timestamp format

**Format:** `YYYYMMDD_description.sql`

**Example:**
```
20251107_create_opportunity_scores_table.sql
20251107_create_market_demand_function.sql
```

**How to generate timestamp:**
```bash
date +%Y%m%d  # Returns: 20251107
```

### 4. Environment Variables

Local Supabase sets these automatically in `.env.local`:

```bash
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_KEY=<your-anon-key>
```

No need to manually configure URLs for local development.

## Daily Workflow

### Start Development Session

```bash
# 1. Start Supabase (runs in background)
supabase start

# 2. Apply any pending migrations
supabase migration up

# 3. Verify database is running
psql postgresql://postgres:postgres@127.0.0.1:54322/postgres -c "SELECT 1;"
```

### Create a New Migration

```bash
# 1. Get current timestamp
TIMESTAMP=$(date +%Y%m%d)

# 2. Create migration file
touch "supabase/migrations/${TIMESTAMP}_your_migration_name.sql"

# 3. Add SQL code to the file

# 4. Apply migration
supabase migration up

# 5. Verify in Supabase Studio: http://127.0.0.1:54323
```

### Access Database

**Option 1: Supabase Studio (Web UI)**
```
http://127.0.0.1:54323
- Tables view
- SQL Editor
- Data browser
```

**Option 2: Command Line (psql)**
```bash
psql postgresql://postgres:postgres@127.0.0.1:54322/postgres

# Then run SQL commands:
\dt                 # List tables
SELECT * FROM submissions LIMIT 1;
```

**Option 3: Python Script**
```python
from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
response = supabase.table("submissions").select("*").limit(1).execute()
```

## Common Tasks

### Verify Supabase is Running

```bash
# Check if service is running
supabase status

# Expected output:
# API: http://127.0.0.1:54321
# Studio: http://127.0.0.1:54323
# [✓] All systems operational
```

### Check Migration Status

```bash
supabase migration list

# Shows:
# 20251104190000_core_reddit_data_tables.sql (applied)
# 20251104190001_opportunity_management.sql (applied)
# etc.
```

### Reset Local Database (⚠️ destructive)

```bash
# Remove all data and reset to initial state
supabase db reset

# This will:
# 1. Drop all tables
# 2. Reapply all migrations
# 3. Reset sequences
```

### Stop Supabase

```bash
supabase stop
```

## Troubleshooting

### Port Already in Use

If you see "port 54321 already in use":

```bash
# Kill any existing Supabase process
pkill -f "supabase"

# Start fresh
supabase start
```

### Migration Fails to Apply

```bash
# Check migration syntax
supabase migration list

# If syntax error:
# 1. Fix the SQL in the migration file
# 2. Run: supabase db reset (if you haven't pushed)
# 3. Re-apply: supabase migration up
```

### Can't Connect from Python

Verify `.env.local` has correct settings:

```bash
cat .env.local | grep SUPABASE

# Should see:
# SUPABASE_URL=http://127.0.0.1:54321
# SUPABASE_KEY=<key>
```

If missing, run:
```bash
supabase start
```

This auto-generates `.env.local`.

## Key Files

- **Migrations:** `supabase/migrations/` - All SQL schema changes
- **Config:** `supabase/config.toml` - Local Supabase configuration
- **Environment:** `.env.local` - Auto-generated local settings (git-ignored)

## Related Documentation

- [Opportunity Scoring System](./opportunity-scoring-system.md) - Schema for scoring
- [Implementation Plan](../plans/2025-11-07-db-scoring-implementation.md) - Step-by-step setup
- Supabase Docs: https://supabase.com/docs/guides/local-development
