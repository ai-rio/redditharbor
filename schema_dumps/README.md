# RedditHarbor Database Schema Dumps

Generated: 2025-11-11 13:05:10

## Available Dump Files

- **migrations_schema_20251111_130509.sql** (19,317 bytes, 2025-11-11 13:05)
- **schema_only_20251111_130509.sql** (229,590 bytes, 2025-11-11 13:05)
- **schema_only_20251111_130510.sql** (229,590 bytes, 2025-11-11 13:05)

## Usage

```bash
# Restore schema only
psql -h localhost -p 54322 -U postgres -d postgres < schema_only_YYYYMMDD_HHMMSS.sql

# Restore roles first
psql -h localhost -p 54322 -U postgres -d postgres < roles_dump_YYYYMMDD_HHMMSS.sql
```
