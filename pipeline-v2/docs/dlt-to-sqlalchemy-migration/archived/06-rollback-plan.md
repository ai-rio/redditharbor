# Rollback Plan - Safe Migration Procedures

## Overview

This document provides comprehensive rollback procedures for the DLT to SQLAlchemy migration. The rollback plan ensures we can safely revert to the previous DLT implementation if issues arise during or after migration.

## Rollback Triggers

### Immediate Rollback Required

🚨 **Critical Issues** (Rollback within 1 hour):

- **Data Loss or Corruption**: Any unexpected data modification or loss
- **Complete System Failure**: Pipeline stops processing entirely
- **Performance Collapse**: > 5x performance degradation
- **Silent Failures Reappear**: DLT-like behavior returning in SQLAlchemy

### Scheduled Rollback Recommended

⚠️ **Significant Issues** (Rollback within 24 hours):

- **Consistent Error Patterns**: Regular failures in data processing
- **Performance Degradation**: 2-5x slower than DLT baseline
- **Integration Failures**: Breaks in downstream systems
- **Resource Exhaustion**: Memory/CPU usage unsustainable

### Monitor and Evaluate

ℹ️ **Minor Issues** (Assess within 72 hours):

- **Occasional Timeouts**: < 1% of operations
- **Slight Performance Impact**: < 2x slower than baseline
- **Non-Critical Errors**: Error handling edge cases
- **Log Anomalies**: Unexpected but non-blocking log messages

## Pre-Rollback Validation

### Step 1: Issue Assessment

```bash
#!/bin/bash
# Issue assessment script

echo "🔍 Assessing rollback necessity..."

# 1. Check data integrity
echo "1. Checking data integrity..."
python -c "
from storage.sqlalchemy_loader import create_sqlalchemy_loader
loader = create_sqlalchemy_loader()
stats = loader.get_load_statistics()
print('Current record count:', stats['total_records'])
"

# 2. Check recent errors
echo "2. Checking recent errors..."
if [ -f "error_log/latest_errors.log" ]; then
    echo "Recent errors (last 10 lines):"
    tail -10 error_log/latest_errors.log
fi

# 3. Check performance metrics
echo "3. Checking performance metrics..."
if command -v pg_top &> /dev/null; then
    echo "Database connection count:"
    psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c "SELECT count(*) FROM pg_stat_activity;"
fi

echo "✅ Assessment completed"
```

### Step 2: Data Backup Verification

```bash
#!/bin/bash
# Verify backup integrity

echo "🔒 Verifying backup integrity..."

BACKUP_FILE="backup_before_migration_*.sql"
LATEST_BACKUP=$(ls -t $BACKUP_FILE | head -1)

echo "Latest backup: $LATEST_BACKUP"

# Check backup file integrity
if [ -f "$LATEST_BACKUP" ]; then
    echo "✅ Backup file exists"
    echo "File size: $(du -h $LATEST_BACKUP | cut -f1)"

    # Test backup can be read
    if pg_restore --list "$LATEST_BACKUP" > /dev/null 2>&1; then
        echo "✅ Backup file is readable"
    else
        echo "❌ Backup file is corrupted"
        exit 1
    fi
else
    echo "❌ No backup file found"
    exit 1
fi
```

## Rollback Procedures

### Level 1: Configuration Rollback (Minutes)

#### 1.1 Revert to DLT Configuration

```bash
#!/bin/bash
# Configuration rollback script

echo "🔄 Rolling back configuration to DLT..."

# 1. Restore DLT configuration files
if [ -f "config/dlt_config.yaml.backup" ]; then
    cp config/dlt_config.yaml.backup config/dlt_config.yaml
    echo "✅ DLT configuration restored"
fi

if [ -f ".dlt/secrets.toml.backup" ]; then
    cp .dlt/secrets.toml.backup .dlt/secrets.toml
    echo "✅ DLT secrets restored"
fi

# 2. Update main configuration to use DLT
# (This depends on your specific configuration setup)
python -c "
# Update configuration to use DLT loader
# Implementation depends on your config system
print('Configuration updated to use DLT')
"

echo "✅ Configuration rollback completed"
```

#### 1.2 Restart Services

```bash
#!/bin/bash
# Service restart script

echo "🔄 Restarting services with DLT configuration..."

# Stop current services
if command -v systemctl &> /dev/null; then
    sudo systemctl stop redditharbor-pipeline || echo "Service not running or not managed by systemctl"
fi

# Stop any running processes
pkill -f "pipeline" || echo "No pipeline processes found"

# Start services with DLT
if command -v systemctl &> /dev/null; then
    sudo systemctl start redditharbor-pipeline || echo "Manual service start required"
fi

echo "✅ Services restarted with DLT"
```

#### 1.3 Validate DLT Functionality

```bash
#!/bin/bash
# DLT functionality validation

echo "✅ Validating DLT functionality..."

python -c "
try:
    from storage.dlt_loader import DLTLoader
    loader = DLTLoader(pipeline_name='rollback_test', use_local_dev=True)
    print('✅ DLT loader created successfully')

    # Test connection
    if loader.validate_connection():
        print('✅ DLT connection validated')
    else:
        print('❌ DLT connection failed')
        exit(1)

except Exception as e:
    print(f'❌ DLT validation failed: {e}')
    exit(1)
"

echo "✅ DLT functionality validated"
```

### Level 2: Data Rollback (Hours)

#### 2.1 Database Restoration

```bash
#!/bin/bash
# Database restoration script

echo "🔄 Restoring database from backup..."

LATEST_BACKUP=$(ls -t backup_before_migration_*.sql | head -1)
RESTORE_DB="postgres_restore_$(date +%Y%m%d_%H%M%S)"

echo "Restoring from: $LATEST_BACKUP"
echo "To database: $RESTORE_DB"

# Create new database for restoration
createdb -h 127.0.0.1 -p 54322 -U postgres "$RESTORE_DB"

# Restore backup
if pg_restore -h 127.0.0.1 -p 54322 -U postgres -d "$RESTORE_DB" --verbose --clean "$LATEST_BACKUP"; then
    echo "✅ Database restored successfully"
    echo "Restored database: $RESTORE_DB"
else
    echo "❌ Database restoration failed"
    dropdb -h 127.0.0.1 -p 54322 -U postgres "$RESTORE_DB"
    exit 1
fi
```

#### 2.2 Data Validation

```bash
#!/bin/bash
# Post-restoration data validation

echo "✅ Validating restored data..."

python -c "
from sqlalchemy import create_engine, text
import os

# Connect to restored database
conn_str = 'postgresql://postgres:postgres@127.0.0.1:54322/postgres_restore_*'
engine = create_engine(conn_str)

with engine.connect() as conn:
    # Check table exists
    table_check = conn.execute(text(\"\"\"
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'app_opportunities'
        )
    \"\"\")).scalar()

    if table_check:
        print('✅ app_opportunities table exists')

        # Check record count
        count = conn.execute(text('SELECT COUNT(*) FROM app_opportunities')).scalar()
        print(f'✅ Record count: {count}')

        # Check data sample
        sample = conn.execute(text('SELECT * FROM app_opportunities LIMIT 5')).fetchall()
        print(f'✅ Sample data accessible: {len(sample)} records')
    else:
        print('❌ app_opportunities table missing')
        exit(1)
"

echo "✅ Data validation completed"
```

#### 2.3 Switch to Restored Database

```bash
#!/bin/bash
# Switch production to restored database

echo "🔄 Switching to restored database..."

RESTORE_DB=$(psql -h 127.0.0.1 -p 54322 -U postgres -l | grep postgres_restore_ | awk '{print $1}' | head -1)
PROD_DB="postgres"

if [ -n "$RESTORE_DB" ]; then
    echo "Switching from $PROD_DB to $RESTORE_DB"

    # Backup current production database (in case)
    pg_dump -h 127.0.0.1 -p 54322 -U postgres "$PROD_DB" > "emergency_backup_$(date +%Y%m%d_%H%M%S).sql"

    # Drop current production database
    dropdb -h 127.0.0.1 -p 54322 -U postgres "$PROD_DB"

    # Rename restored database to production
    psql -h 127.0.0.1 -p 54322 -U postgres -c "ALTER DATABASE \"$RESTORE_DB\" RENAME TO \"$PROD_DB\""

    echo "✅ Database switch completed"
else
    echo "❌ No restored database found"
    exit 1
fi
```

### Level 3: Code Rollback (Days)

#### 3.1 Git Rollback

```bash
#!/bin/bash
# Code rollback script

echo "🔄 Rolling back code changes..."

# Find the commit before migration started
PRE_MIGRATION_COMMIT=$(git log --oneline --grep="DLT to SQLAlchemy" --reverse | head -1 | cut -d' ' -f1)

if [ -n "$PRE_MIGRATION_COMMIT" ]; then
    echo "Pre-migration commit: $PRE_MIGRATION_COMMIT"

    # Create rollback branch
    git checkout -b rollback-to-dlt "$PRE_MIGRATION_COMMIT"

    echo "✅ Code rolled back to: $PRE_MIGRATION_COMMIT"
else
    echo "❌ Could not find pre-migration commit"
    exit 1
fi
```

#### 3.2 Dependency Management

```bash
#!/bin/bash
# Dependency rollback

echo "🔄 Rolling back dependencies..."

# Restore original requirements
if [ -f "requirements.txt.backup" ]; then
    cp requirements.txt.backup requirements.txt
    echo "✅ Requirements restored"
fi

if [ -f "pyproject.toml.backup" ]; then
    cp pyproject.toml.backup pyproject.toml
    echo "✅ pyproject.toml restored"
fi

# Reinstall dependencies
if command -v uv &> /dev/null; then
    uv sync
else
    pip install -r requirements.txt
fi

echo "✅ Dependencies reinstalled"
```

## Rollback Validation

### Post-Rollback Testing

```bash
#!/bin/bash
# Comprehensive post-rollback validation

echo "✅ Running post-rollback validation..."

# 1. DLT functionality
echo "1. Testing DLT functionality..."
pytest pipeline-v2/tests/test_dlt_characterization.py -v

# 2. Pipeline integration
echo "2. Testing pipeline integration..."
python -c "
from storage.dlt_loader import DLTLoader
import logging

logging.basicConfig(level=logging.INFO)

# Test with sample data
loader = DLTLoader(pipeline_name='rollback_validation')
test_data = [{
    'submission_id': 'rollback_test_001',
    'title': 'Rollback Test',
    'subreddit': 'test',
    'upvotes': 10,
    'score': 10.0
}]

result = loader.load_opportunities(test_data)
print('✅ DLT pipeline test completed')
"

# 3. Data integrity
echo "3. Validating data integrity..."
python -c "
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:postgres@127.0.0.1:54322/postgres')
with engine.connect() as conn:
    count = conn.execute(text('SELECT COUNT(*) FROM app_opportunities')).scalar()
    print(f'✅ Total records: {count}')

    # Check recent data
    recent = conn.execute(text(\"\"\"
        SELECT COUNT(*) FROM app_opportunities
        WHERE created_utc > NOW() - INTERVAL '1 hour'
    \"\"\")).scalar()
    print(f'✅ Recent records: {recent}')
"

echo "✅ Post-rollback validation completed"
```

### Performance Baseline Verification

```bash
#!/bin/bash
# Performance verification after rollback

echo "⚡ Verifying performance baseline..."

# Test DLT performance
python -c "
import time
from storage.dlt_loader import DLTLoader

loader = DLTLoader(pipeline_name='perf_test')

# Create test dataset
test_data = []
for i in range(100):
    test_data.append({
        'submission_id': f'perf_rollback_{i}',
        'title': f'Performance Test {i}',
        'subreddit': 'perf_test',
        'upvotes': i,
        'score': float(i)
    })

# Measure performance
start_time = time.time()
result = loader.load_opportunities(test_data)
execution_time = time.time() - start_time

print(f'DLT Performance Test:')
print(f'  Records: {len(test_data)}')
print(f'  Time: {execution_time:.2f}s')
print(f'  Records/sec: {len(test_data) / execution_time:.1f}')

if execution_time < 30.0:
    print('✅ Performance within acceptable range')
else:
    print('⚠️ Performance degraded - investigate')
"
```

## Monitoring After Rollback

### Short-term Monitoring (First 24 hours)

```bash
#!/bin/bash
# Short-term monitoring script

echo "📊 Starting short-term post-rollback monitoring..."

# Monitor for 24 hours
END_TIME=$(($(date +%s) + 86400))

while [ $(date +%s) -lt $END_TIME ]; do
    echo "[$(date)] Checking system status..."

    # 1. Check error logs
    ERROR_COUNT=$(grep -c "ERROR" /var/log/redditharbor/pipeline.log 2>/dev/null || echo "0")
    if [ "$ERROR_COUNT" -gt 10 ]; then
        echo "⚠️ High error count: $ERROR_COUNT"
    fi

    # 2. Check database connectivity
    if python -c "
from storage.dlt_loader import DLTLoader
try:
    loader = DLTLoader(use_local_dev=True)
    loader.validate_connection()
except:
    exit(1)
" 2>/dev/null; then
        echo "✅ Database connection OK"
    else
        echo "❌ Database connection failed"
    fi

    # 3. Check processing queue
    QUEUE_SIZE=$(python -c "
from storage.dlt_loader import DLTLoader
try:
    loader = DLTLoader(use_local_dev=True)
    stats = loader.get_load_statistics()
    print(stats.get('queue_size', 0))
except:
    print(0)
" 2>/dev/null)

    if [ "$QUEUE_SIZE" -gt 1000 ]; then
        echo "⚠️ High queue size: $QUEUE_SIZE"
    fi

    sleep 300  # Check every 5 minutes
done

echo "✅ Short-term monitoring completed"
```

### Long-term Monitoring (First Week)

Create monitoring alerts for:

1. **Data Processing Failures**: Alert if success rate drops below 95%
2. **Performance Degradation**: Alert if processing time exceeds 2x baseline
3. **Error Rate Increases**: Alert if error rate increases by > 50%
4. **Resource Usage**: Alert if CPU/memory usage exceeds thresholds

## Rollback Documentation

### Incident Report Template

```
# DLT to SQLAlchemy Migration Rollback Report

## Rollback Information
- **Date**: [Date of rollback]
- **Time**: [Time of rollback]
- **Trigger**: [Reason for rollback]
- **Severity**: [Critical/High/Medium/Low]
- **Duration**: [Total rollback time]

## Issue Description
[Detailed description of the issue that triggered rollback]

## Rollback Actions Performed
1. [Action 1]
2. [Action 2]
3. [Action 3]

## Rollback Validation
- [ ] DLT functionality restored
- [ ] Data integrity verified
- [ ] Performance baseline confirmed
- [ ] Monitoring systems active

## Impact Assessment
- **Data Loss**: [None/Partial/Complete]
- **Service Downtime**: [Duration]
- **User Impact**: [Description]
- **Business Impact**: [Description]

## Root Cause Analysis
[Analysis of why the issue occurred]

## Prevention Measures
[Measures to prevent recurrence]

## Next Steps
[Plans for addressing the underlying issue]
```

## Success Criteria for Rollback

A rollback is considered successful when:

1. **DLT Functionality Restored**: All DLT operations working as before
2. **Data Integrity Confirmed**: No data loss or corruption
3. **Performance Baseline Met**: Performance equal to or better than pre-migration
4. **Monitoring Active**: All monitoring and alerting systems operational
5. **Documentation Complete**: Full incident report completed
6. **Stakeholder Notification**: All relevant parties informed

## Contact Information

### Emergency Contacts

- **Technical Lead**: [Name, Phone, Email]
- **Database Administrator**: [Name, Phone, Email]
- **DevOps Engineer**: [Name, Phone, Email]
- **Product Manager**: [Name, Phone, Email]

### Escalation Path

1. **Level 1**: Technical team (first hour)
2. **Level 2**: Engineering management (within 2 hours)
3. **Level 3**: Executive team (within 4 hours)

This rollback plan ensures we can safely and quickly revert to the DLT implementation if needed, minimizing risk to data integrity and system availability.