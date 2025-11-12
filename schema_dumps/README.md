# RedditHarbor Database Schema Dumps

Generated: 2025-11-12 16:02:14

## Available Dump Files

- **updated_schema_with_trust_layer_20251112_160214.sql** (83,121 bytes, 2025-11-12 16:02)
  - Complete database schema including trust layer integration
  - Contains all tables: submissions, comments, redditors, app_opportunities
  - Includes trust validation columns: trust_level, trust_score, trust_badge, activity_score
  - Includes performance indexes for trust layer queries

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
