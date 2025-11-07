# DLT Migration Rollback Plan

## Overview

This document provides procedures for quickly rolling back from DLT pipeline to manual collection in case of issues during traffic cutover.

## When to Rollback

**Trigger rollback immediately if any of the following occur:**

- ❌ Data loss or corruption detected
- ❌ Error rate >20% for 6+ hours
- ❌ Critical production incident
- ❌ API rate limits consistently exceeded
- ❌ Execution time SLA missed repeatedly
- ❌ Duplicate data detected in database
- ❌ DLT pipeline fails to load data

## Rollback Procedure

### Step 1: Immediate Action (30 seconds)

**Command:**
```bash
python scripts/dlt_traffic_cuttover.py --action rollback
```

**What it does:**
- Disables DLT pipeline
- Enables manual collection (100%)
- Updates configuration to manual_only phase
- Logs rollback timestamp

### Step 2: Verify Rollback (1 minute)

**Check status:**
```bash
python scripts/check_cutover_status.py
```

**Expected output:**
```
Current Phase: manual_only
DLT Enabled: ✗
Manual Enabled: ✓
```

### Step 3: Re-enable Manual Collection (2 minutes)

**If using cron/scheduler, re-enable manual jobs:**

```bash
# Example: Uncomment manual collection in crontab
crontab -e

# Or update scheduler configuration
# (Specific steps depend on your scheduler)
```

### Step 4: Verify Manual Collection (5 minutes)

**Test manual collection:**
```bash
source .venv/bin/activate
python -c "
from core.collection import collect_data
from config.settings import REDDIT_PUBLIC, REDDIT_SECRET, REDDIT_USER_AGENT
import praw

reddit = praw.Reddit(
    client_id=REDDIT_PUBLIC,
    client_secret=REDDIT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

success = collect_data(
    reddit_client=reddit,
    supabase_client=None,  # Use test mode
    db_config={},
    subreddits=['opensource'],
    limit=10
)
print(f'Manual collection: {\"✓ SUCCESS\" if success else \"✗ FAILED\"}')"
```

**Expected:** Manual collection working

### Step 5: Check Data Integrity (10 minutes)

**Verify no data loss:**

```bash
# Check Supabase for latest submissions
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c "
SELECT
    COUNT(*) as total_submissions,
    MAX(created_utc) as latest_submission
FROM submissions
WHERE created_utc > NOW() - INTERVAL '1 hour';"

# Check opportunity_analysis table
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c "
SELECT
    COUNT(*) as total_opportunities,
    COUNT(CASE WHEN scored_at > NOW() - INTERVAL '1 hour' THEN 1 END) as recent
FROM opportunity_analysis;"
```

**Expected:**
- Recent submissions present
- No gaps in data
- Opportunity analysis continuing

### Step 6: Investigate Root Cause (30+ minutes)

**Check DLT logs:**
```bash
# View DLT traffic cutover logs
tail -f error_log/dlt_traffic_cuttover.log

# Check DLT pipeline logs
find . -name "*.log" -type f | grep dlt
```

**Common issues:**
1. **Database connection timeout** → Check Supabase status
2. **API rate limit exceeded** → Reduce collection frequency
3. **Schema mismatch** → Review table structure
4. **Memory/resource issues** → Check system resources

### Step 7: Create Fix Plan

**Document findings:**
```bash
# Create incident report
cat > incident_report_$(date +%Y%m%d_%H%M%S).md << EOF
# DLT Rollback Incident Report

## Timeline
- Rollback triggered: $(date)
- Rollback completed: $(date)
- Total downtime: X minutes

## Root Cause
[Describe what went wrong]

## Impact
- Data loss: Yes/No
- Affected subreddits: [list]
- Users affected: [estimate]

## Resolution
- Action taken: Rolled back to manual collection
- Next steps: [plan to fix and retry]

## Prevention
- [How to prevent this in future]
EOF
```

## Re-attempt Migration (After Fix)

### 1. Fix the Issue
- Apply code fixes
- Update configuration
- Test in isolation

### 2. Start Over at 10% Cutover
```bash
# Re-setup 10% cutover
python scripts/dlt_traffic_cuttover.py --phase 10% --action setup

# Monitor closely
python scripts/dlt_traffic_cuttover.py --phase 10% --action monitor
```

### 3. Validate Before Next Phase
Ensure 10% cutover runs successfully for 24 hours before moving to 50%.

## Rollback Script (One-liner)

For emergency use, here's a one-liner rollback:

```bash
cd /home/carlos/projects/redditharbor && \
python -c "
import json
from datetime import datetime
config = {
    'current_phase': 'manual_only',
    'dlt_enabled': False,
    'manual_enabled': True,
    'rollback_timestamp': datetime.now().isoformat()
}
with open('config/traffic_cutover_config.json', 'w') as f:
    json.dump(config, f, indent=2)
print('✓ Rollback complete - DLT disabled, manual collection enabled')
" && \
python scripts/check_cutover_status.py
```

## Contact Information

**Escalation Path:**
1. **On-call Engineer** (immediate)
2. **Team Lead** (if unresolved after 1 hour)
3. **CTO** (if data loss/critical incident)

**Resources:**
- DLT Documentation: https://dlthub.com/docs
- Supabase Status: https://status.supabase.com
- Project Slack: #redditharbor-dlt-migration

## Rollback Success Criteria

Rollback is successful when:
- ✓ Manual collection resumes normally
- ✓ No data loss detected
- ✓ Error rate returns to normal (<5%)
- ✓ System performance restored
- ✓ All queues/jobs processing

---

**Last Updated:** 2025-11-07
**Version:** 1.0
