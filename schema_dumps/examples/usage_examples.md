# RedditHarbor Schema Dumps - Usage Examples

This file provides practical examples of using the Supabase CLI-based utilities for common database operations.

## Quick Start Examples

### 1. Generate Current Schema Documentation
```bash
# Generate comprehensive schema documentation
python utils/schema_dump.py --mode all

# Check generated files
ls -la *20251118_*
```

### 2. Interactive Database Exploration
```bash
# Start interactive mode
python utils/db_query.py --interactive

# Example interactive session:
redditdb> \tables
redditdb> SELECT COUNT(*) FROM opportunities_unified;
redditdb> \schema opportunities_unified
redditdb> SELECT app_name, trust_level FROM opportunities_unified WHERE trust_level = 'VERY_HIGH' LIMIT 5;
redditdb> \json
redditdb> SELECT COUNT(*) as total FROM submissions;
redditdb> \exit
```

### 3. Schema Health Check
```bash
# Run complete validation
python utils/schema_validator.py

# Check specific issues
python utils/schema_validator.py --check foreign-keys
python utils/schema_validator.py --check data-quality
```

## Common Queries

### RedditHarbor Analysis Queries

```bash
# Count opportunities by trust level
python utils/db_query.py --query "
SELECT trust_level, COUNT(*) as count
FROM opportunities_unified
GROUP BY trust_level
ORDER BY count DESC" --save

# Top performing opportunities
python utils/db_query.py --query "
SELECT app_name, opportunity_score, trust_level, created_at
FROM opportunities_unified
WHERE opportunity_score > 70
ORDER BY opportunity_score DESC
LIMIT 10"

# Recent submissions with opportunities
python utils/db_query.py --query "
SELECT s.title, s.score, o.app_name, o.opportunity_score
FROM submissions s
JOIN opportunities_unified o ON s.id = o.submission_id
ORDER BY s.created_at DESC
LIMIT 5"

# Schema size analysis
python utils/db_query.py --query "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10"
```

### Validation and Quality Checks

```bash
# Check for data quality issues
python utils/schema_validator.py --check data-quality --save

# Foreign key consistency
python utils/schema_validator.py --check foreign-keys --save

# Index coverage analysis
python utils/schema_validator.py --check indexes --save
```

## Batch Operations

### Generate Daily Schema Reports

```bash
# Create a daily schema snapshot
python utils/schema_dump.py --mode all

# Save validation report
python utils/schema_validator.py --save

# Create opportunities summary
python utils/db_query.py --query "
SELECT
    COUNT(*) as total_opportunities,
    AVG(opportunity_score) as avg_score,
    MAX(opportunity_score) as max_score,
    COUNT(CASE WHEN trust_level = 'VERY_HIGH' THEN 1 END) as very_high_trust
FROM opportunities_unified
WHERE opportunity_score IS NOT NULL" --save
```

### Migration Planning

```bash
# Before making schema changes:
# 1. Create current snapshot
python utils/schema_dump.py --mode full

# 2. Validate current state
python utils/schema_validator.py --save

# 3. Check for potential issues
python utils/db_query.py --query "SELECT COUNT(*) FROM opportunities_unified WHERE submission_id IS NULL"

# After making changes:
# 4. Compare new state
python utils/schema_dump.py --mode full
# diff between old and new schema files
```

## File Management

### Archive Old Dumps
```bash
# Move old dumps to archive
mkdir -p archive/$(date +%Y-%m)
mv *202511* archive/$(date +%Y-%m)/

# Keep only latest dumps for quick access
ls -la schema_dumps/archive/$(date +%Y-%m)/
```

### Clean Up Generated Results
```bash
# Clean up old query results
find query_results/ -name "*.txt" -mtime +7 -delete
find query_results/ -name "*.json" -mtime +7 -delete

# Clean up old validation reports
find validation_results/ -name "*.md" -mtime +7 -delete
```

## Automation Examples

### Create a Schema Monitoring Script

```bash
# Create: scripts/monitor_schema.sh
#!/bin/bash

echo "=== RedditHarbor Schema Monitoring $(date) ==="

# Generate schema dump
echo "Generating schema dump..."
python utils/schema_dump.py --mode all

# Run validation
echo "Running schema validation..."
python utils/schema_validator.py --save

# Get current statistics
echo "Current database statistics:"
python utils/db_query.py --query "
SELECT
    (SELECT COUNT(*) FROM opportunities_unified) as opportunities,
    (SELECT COUNT(*) FROM submissions) as submissions,
    (SELECT COUNT(*) FROM redditors) as redditors,
    (SELECT COUNT(*) FROM comments) as comments
" --json

echo "=== Monitoring complete ==="
```

### Create a Weekly Report Script

```bash
# Create: scripts/weekly_report.py
#!/usr/bin/env python3

import json
from pathlib import Path
import subprocess
import sys
sys.path.append(str(Path(__file__).parent.parent / 'schema_dumps' / 'utils'))

from db_query import DatabaseQuerier

def generate_weekly_report():
    querier = DatabaseQuerier(Path(__file__).parent.parent)

    report = "# RedditHarbor Weekly Report\n\n"
    report += f"Generated: {datetime.now().isoformat()}\n\n"

    # Opportunity statistics
    opp_stats = querier.run_supabase_query("""
        SELECT
            COUNT(*) as total,
            AVG(opportunity_score) as avg_score,
            MAX(opportunity_score) as max_score
        FROM opportunities_unified
        WHERE opportunity_score IS NOT NULL
    """)[0]

    report += "## Opportunity Statistics\n\n"
    report += f"- Total Opportunities: {opp_stats['total']}\n"
    report += f"- Average Score: {round(opp_stats['avg_score'], 1)}\n"
    report += f"- Highest Score: {opp_stats['max_score']}\n\n"

    # Trust level breakdown
    trust_stats = querier.run_supabase_query("""
        SELECT trust_level, COUNT(*) as count
        FROM opportunities_unified
        WHERE trust_level IS NOT NULL
        GROUP BY trust_level
        ORDER BY count DESC
    """)

    report += "## Trust Level Distribution\n\n"
    for stat in trust_stats:
        report += f"- {stat['trust_level']}: {stat['count']}\n"

    print(report)

if __name__ == "__main__":
    generate_weekly_report()
```

## Troubleshooting

### Common Issues and Solutions

**Issue: Supabase CLI not found**
```bash
# Solution: Install Supabase CLI
npm install -g supabase
```

**Issue: Database connection failed**
```bash
# Solution: Check if Supabase is running
supabase status

# Start Supabase if not running
supabase start
```

**Issue: Permission denied on utility scripts**
```bash
# Solution: Make scripts executable
chmod +x schema_dumps/utils/*.py
```

**Issue: No results from queries**
```bash
# Solution: Check if tables exist and have data
python utils/db_query.py --query "SELECT COUNT(*) FROM opportunities_unified"
python utils/db_query.py --query "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
```

## Advanced Usage

### Custom Query Files

Create reusable query files in a `queries/` directory:

```bash
# Create: queries/high_value_opportunities.sql
SELECT
    app_name,
    opportunity_score,
    trust_level,
    problem_statement
FROM opportunities_unified
WHERE opportunity_score > 80
  AND trust_level IN ('VERY_HIGH', 'HIGH')
ORDER BY opportunity_score DESC
LIMIT 20;

# Run the query file
python utils/db_query.py --file queries/high_value_opportunities.sql --save
```

### JSON Output for API Integration

```bash
# Generate JSON output for API consumption
python utils/db_query.py --query "
SELECT app_name, opportunity_score, trust_level
FROM opportunities_unified
WHERE opportunity_score > 70
LIMIT 10
" --json --save

# The output can be parsed by other applications
```

These examples show the flexibility and power of the new Supabase CLI-based utilities while maintaining security and consistency.