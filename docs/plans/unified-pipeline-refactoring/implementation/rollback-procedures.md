# Rollback Procedures

Consolidated rollback procedures for all phases.

---

## General Rollback Strategy

1. **Identify Issue**: Determine what went wrong
2. **Assess Impact**: How critical is the issue?
3. **Execute Rollback**: Follow phase-specific procedure
4. **Validate**: Confirm system restored
5. **Document**: Record issue and resolution

---

## Phase-Specific Rollbacks

### Phase 1-3: Low Risk (Foundation, Agents, Utilities)

**Issue**: New modules causing import errors

**Rollback**:
```bash
# Remove new modules
rm -rf core/pipeline/ core/fetchers/ core/enrichment/
rm -rf core/agents/ core/quality_filters/
rm tests/test_*_new.py

# Verify old system works
pytest tests/ -v
```

**Recovery Time**: < 5 minutes

---

### Phase 4-5: Medium Risk (Fetchers, Deduplication)

**Issue**: Data fetching broken or deduplication failing

**Rollback**:
```bash
# Restore original monolith logic
git checkout HEAD -- scripts/core/batch_opportunity_scoring.py
git checkout HEAD -- scripts/dlt/dlt_trust_pipeline.py

# Remove extracted modules
rm -rf core/fetchers/database_fetcher.py
rm -rf core/deduplication/

# Verify functionality
python scripts/core/batch_opportunity_scoring.py --limit 10
```

**Recovery Time**: 10-15 minutes

---

### Phase 6: High Risk (AI Enrichment Services)

**Issue**: AI analysis producing incorrect results or failing

**Rollback**:
```bash
# Stop using enrichment services
rm -rf core/enrichment/

# Restore direct AI agent calls in monoliths
git checkout HEAD -- scripts/core/batch_opportunity_scoring.py

# Verify AI analysis works
python scripts/testing/test_ai_services.py
```

**Recovery Time**: 15-20 minutes

**Critical**: If in production, this requires immediate action

---

### Phase 7: High Risk (Storage Layer)

**Issue**: Data not being stored or duplicates created

**Rollback**:
```bash
# Stop unified storage
rm -rf core/storage/

# Restore database from backup
pg_restore -d reddit_harbor backup_$(date +%Y%m%d).sql

# Restore original DLT loading logic
git checkout HEAD -- scripts/

# Verify data integrity
SELECT submission_id, COUNT(*) 
FROM opportunities_unified 
GROUP BY submission_id 
HAVING COUNT(*) > 1;
```

**Recovery Time**: 30-60 minutes (database restore)

**Critical**: Always backup before Phase 7

---

### Phase 8: Critical (Unified Orchestrator)

**Issue**: Orchestrator not working correctly

**Rollback**:
```bash
# Remove orchestrator
rm -rf core/pipeline/orchestrator.py

# Switch back to monoliths
# (No code changes needed if monoliths still present)

# Run monolithic pipelines
python scripts/core/batch_opportunity_scoring.py
python scripts/dlt/dlt_trust_pipeline.py

# Verify both work
python scripts/testing/verify_monoliths.py
```

**Recovery Time**: 5-10 minutes

---

### Phase 9-10: Medium Risk (API, SDK)

**Issue**: API not responding or SDK broken

**Rollback**:
```bash
# Stop API
docker-compose down

# Remove API code
rm -rf api/
rm -rf sdk/

# Direct Python access still works
python scripts/unified/run_unified_pipeline.py
```

**Recovery Time**: < 5 minutes

**Impact**: Only affects web/external access, core pipeline unaffected

---

### Phase 11: CRITICAL (Production Migration)

**Issue**: Production failures after cutover

**IMMEDIATE ROLLBACK** (<5 minutes):

```bash
# 1. Stop unified pipeline
docker-compose -f docker-compose.prod.yml down
killall -9 run_unified_pipeline.py

# 2. Restore monolithic scripts
cp scripts/archive/monoliths_YYYYMMDD/*.py scripts/core/

# 3. Restore cron jobs
crontab -e
# 0 2 * * * python scripts/core/batch_opportunity_scoring.py

# 4. Restart old pipelines
python scripts/core/batch_opportunity_scoring.py --limit 100 &

# 5. Verify functionality
tail -f logs/batch_opportunity_scoring.log

# 6. Confirm database writes
SELECT COUNT(*) FROM opportunities_unified 
WHERE created_at > NOW() - INTERVAL '1 hour';

# 7. Notify team
echo "PRODUCTION ROLLED BACK: $(date)" | mail -s "URGENT" team@company.com
```

**Recovery Time**: < 5 minutes

**Post-Rollback**:
- Document what failed
- Create incident report
- Plan remediation
- Schedule retry

---

## Rollback Decision Matrix

| Severity | Action | Approval Required |
|----------|--------|-------------------|
| **P0 - Critical** | Immediate rollback | Notify stakeholders |
| **P1 - High** | Rollback within 1 hour | Tech lead approval |
| **P2 - Medium** | Rollback within 24 hours | Team discussion |
| **P3 - Low** | Fix forward | No rollback needed |

---

## Rollback Checklist

Before executing rollback:
- [ ] Issue clearly identified
- [ ] Impact assessed
- [ ] Backup verified (for data-related issues)
- [ ] Rollback procedure reviewed
- [ ] Team notified
- [ ] Approval obtained (if required)

After rollback:
- [ ] System functionality verified
- [ ] No data loss confirmed
- [ ] Incident documented
- [ ] Root cause identified
- [ ] Remediation plan created
- [ ] Stakeholders updated

---

## Emergency Contacts

**During Rollback**:
- Tech Lead: [contact]
- DevOps: [contact]
- On-Call Engineer: [contact]

**Escalation Path**:
1. Team Lead
2. Engineering Manager
3. CTO

---

## Prevention

**Best Practices**:
- Always test in staging first
- Use blue-green deployments
- Maintain database backups
- Keep monoliths available during migration
- Have rollback plan ready BEFORE deployment
- Practice rollback procedures

**Remember**: A good rollback is fast, documented, and validated.
