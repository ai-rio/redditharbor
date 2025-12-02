# RedditHarbor Database Schema Dumps

Last Updated: 2025-11-13 11:48:46

## Available Dump Files

### Current Schema (Production Ready)
- **updated_schema_with_trust_layer_20251112_160214.sql** (83,121 bytes, 2025-11-12 16:02)
  - Complete database schema including trust layer integration
  - Contains all tables: submissions, comments, redditors, app_opportunities
  - Includes trust validation columns: trust_level, trust_score, trust_badge, activity_score
  - Includes performance indexes for trust layer queries

### Pre-Cleanup Snapshot (November 13, 2025)
- **pre_cleanup_schema_20251113_114846.sql** (2.3K)
  - app_opportunities_trust table schema before data cleanup
- **pre_cleanup_table_details_20251113_114846.txt** (3.8K)
  - Detailed table structure with column descriptions
- **pre_cleanup_data_stats_20251113_114846.txt** (138 bytes)
  - Statistical snapshot of old data (47.8% scoring 70+, n=23)
- **PRE_CLEANUP_SNAPSHOT_20251113.md**
  - Complete documentation of database state before cleanup
  - Explains why old data was discarded (mixed code versions, test data contamination)
  - Related to production readiness audit findings

## Trust Layer Schema Features

### Enhanced app_opportunities Table
- `trust_level` - VERY_HIGH/HIGH/MEDIUM/LOW/UNKNOWN
- `trust_score` - 0-100 numeric score with validation
- `trust_badge` - GOLD/SILVER/BRONZE/BASIC/NO-BADGE
- `activity_score` - Subreddit activity scoring
- `engagement_level` - VERY_HIGH/HIGH/MEDIUM/LOW/MINIMAL
- `trend_velocity` - Trend velocity analysis
- `problem_validity` - VALID/POTENTIAL/UNCLEAR/INVALID
- `discussion_quality` - EXCELLENT/GOOD/FAIR/POOR
- `ai_confidence_level` - VERY_HIGH/HIGH/MEDIUM/LOW
- `trust_factors` - JSONB for additional trust data
- `trust_updated_at` - Last trust validation timestamp

## Usage

```bash
# Restore complete schema with trust layer
docker exec -i supabase_db_carlos psql -U postgres -d postgres < updated_schema_with_trust_layer_20251112_160214.sql

# Alternative: Using supabase CLI
supabase db reset --local
# Then apply: supabase db push --local
```
