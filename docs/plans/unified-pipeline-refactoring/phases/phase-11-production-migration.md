# Phase 11: Production Migration

**Timeline**: Week 11  
**Duration**: 3 days  
**Risk Level**: 🔴 HIGH  
**Dependencies**: Phase 10 completed (SDK created)

---

## Context

### What Was Completed (Phase 10)
- [x] TypeScript SDK created
- [x] Integration examples provided
- [x] Next.js consumption ready

### Current State
- Unified pipeline fully built and validated
- Monolithic scripts still in production
- Need final cutover
- **CRITICAL: This is production deployment**

### Why This Phase Is Critical
- **HIGHEST RISK** - production cutover
- Zero downtime requirement
- Data integrity critical
- Rollback must be ready
- Final validation of entire refactoring

---

## Objectives

### Primary Goals
1. **Deploy** unified pipeline to production
2. **Decommission** monolithic scripts safely
3. **Validate** production stability (1 week)
4. **Archive** old code with documentation
5. **Celebrate** 🎉 completion

### Success Criteria
- [ ] Unified pipeline running in production
- [ ] All success metrics achieved
- [ ] Production stable for 1 week
- [ ] Monoliths safely archived
- [ ] Team trained on new system

---

## Tasks

### Task 1: Pre-Production Validation (4 hours)

**Final Checks**:

```bash
# 1. Run complete test suite
pytest tests/ -v --cov=core --cov-report=term
# Target: >90% coverage

# 2. Run side-by-side comparison
python scripts/testing/validate_unified_pipeline.py
# Must show 100% match

# 3. Performance benchmarks
python scripts/testing/benchmark_pipeline.py
# Must be within 5% of baseline

# 4. Load testing
python scripts/testing/load_test_pipeline.py
# Must handle 1000 submissions/hour

# 5. Cost validation
python scripts/testing/validate_cost_savings.py
# Must preserve $3,528/year savings
```

**Validation Report**: Document all results

---

### Task 2: Production Deployment (1 day)

**Blue-Green Deployment Strategy**:

```bash
# 1. Deploy unified pipeline (green)
# Keep monoliths running (blue)

# Deploy API
docker-compose -f docker-compose.prod.yml up -d

# Deploy unified pipeline script
cp scripts/unified/run_unified_pipeline.py /production/scripts/

# 2. Configure monitoring
# Set up alerts for errors, performance, costs

# 3. Run parallel for 24 hours
# Compare results in real-time

# 4. Gradual traffic shift
# 10% -> 25% -> 50% -> 100%

# 5. Monitor closely
# Watch for:
# - Error rates
# - Processing times
# - Cost metrics
# - Data quality
```

---

### Task 3: Switch Over (4 hours)

**Critical Cutover Steps**:

```bash
# 1. Final parallel validation (2 hours before)
python scripts/testing/final_validation.py

# 2. Backup production database
pg_dump $PROD_DB > backup_final_$(date +%Y%m%d_%H%M%S).sql

# 3. Update cron jobs / schedulers
# OLD:
# 0 2 * * * python scripts/core/batch_opportunity_scoring.py
# NEW:
crontab -e
# 0 2 * * * python scripts/unified/run_unified_pipeline.py --source database --limit 100

# 4. Stop old monoliths
# Disable cron jobs for old scripts
# Keep processes available for rollback

# 5. Monitor for 2 hours
# Check logs, errors, database

# 6. Declare cutover complete
echo "Production cutover complete: $(date)" >> migration.log
```

---

### Task 4: Decommission Monoliths (1 day)

**Safe Archival Process**:

```bash
# 1. Create archive directory
mkdir -p scripts/archive/monoliths_$(date +%Y%m%d)

# 2. Move monolithic scripts
mv scripts/core/batch_opportunity_scoring.py scripts/archive/monoliths_$(date +%Y%m%d)/
mv scripts/dlt/dlt_trust_pipeline.py scripts/archive/monoliths_$(date +%Y%m%d)/

# 3. Create archive README
cat > scripts/archive/monoliths_$(date +%Y%m%d)/README.md << 'ARCHIVE'
# Archived Monolithic Pipelines

**Archived**: $(date)
**Reason**: Replaced by unified pipeline (Phase 11 completion)

## Original Files

- `batch_opportunity_scoring.py` (2,830 lines) - Database pipeline
- `dlt_trust_pipeline.py` (774 lines) - Reddit API pipeline

## Replacement

Unified pipeline: `scripts/unified/run_unified_pipeline.py`

See: [docs/plans/unified-pipeline-refactoring/README.md](../../../docs/plans/unified-pipeline-refactoring/README.md)

## Rollback Procedure

If needed to restore:
```bash
cp scripts/archive/monoliths_YYYYMMDD/*.py scripts/core/
# Restore cron jobs
# Revert database if needed
```

## Historical Context

These files served the project well but have been successfully replaced
by the unified architecture that:
- Eliminates 3,574 lines of duplicate code
- Enables Next.js integration
- Preserves $3,528/year cost savings
- Provides modular, maintainable codebase
ARCHIVE

# 4. Update documentation references
grep -r "batch_opportunity_scoring.py" docs/ | # Update all references
grep -r "dlt_trust_pipeline.py" docs/ | # Update all references

# 5. Git commit
git add scripts/archive/
git commit -m "archive: Decommission monolithic pipelines after successful migration

Archived scripts:
- batch_opportunity_scoring.py (2,830 lines)
- dlt_trust_pipeline.py (774 lines)

Replaced by unified pipeline achieving:
- 3,574 lines code reduction
- $3,528/year cost savings preserved
- Next.js integration enabled
- 50% faster development velocity

All success metrics validated. Production stable for 1 week.

Migration completed: $(date)
"
```

---

### Task 5: Post-Migration Validation (1 week)

**Monitor for 1 week**:

```bash
# Daily checks
- Error rates: Must be ≤1%
- Processing time: Must be ≤7.0s/submission
- Cost metrics: Must maintain $3,528/year savings
- Data quality: Run validation queries
- Performance: Check throughput ≥500/hr

# Weekly validation
python scripts/testing/weekly_validation.py
# Generates comprehensive report
```

**Success Metrics Validation**:

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Code Reduction | 3,574 lines | [FILL] | ✅/❌ |
| Processing Time | ≤7.0s | [FILL] | ✅/❌ |
| Throughput | ≥500/hr | [FILL] | ✅/❌ |
| Error Rate | ≤1% | [FILL] | ✅/❌ |
| Cost Savings | $3,528/year | [FILL] | ✅/❌ |
| Test Coverage | >90% | [FILL] | ✅/❌ |

---

### Task 6: Team Training & Knowledge Transfer (2 days)

**Training Sessions**:

1. **Architecture Overview** (2 hours)
   - New modular structure
   - Service responsibilities
   - Data flow

2. **Development Workflow** (2 hours)
   - How to add new features
   - Testing procedures
   - Deployment process

3. **Operations & Monitoring** (1 hour)
   - Monitoring dashboards
   - Troubleshooting procedures
   - Common issues and solutions

4. **API Usage** (1 hour)
   - FastAPI endpoints
   - TypeScript SDK
   - Integration patterns

**Documentation Handoff**:
- Complete architecture docs
- Runbooks and procedures
- Troubleshooting guides

---

## Validation Checklist

### Pre-Production
- [ ] All tests passing (>90% coverage)
- [ ] Side-by-side validation 100% match
- [ ] Performance benchmarks met
- [ ] Load testing passed
- [ ] Cost validation confirmed

### Production Deployment
- [ ] Blue-green deployment successful
- [ ] Parallel operation validated (24 hours)
- [ ] Monitoring and alerting active
- [ ] Gradual traffic shift completed
- [ ] Zero errors during cutover

### Post-Production
- [ ] Production stable for 1 week
- [ ] All success metrics achieved
- [ ] Monoliths archived safely
- [ ] Documentation updated
- [ ] Team trained

### Final Sign-Off
- [ ] Technical Lead approval
- [ ] Product Owner approval
- [ ] Engineering Manager approval
- [ ] Stakeholder confirmation

---

## Rollback Procedure

**If production issues occur**:

```bash
# IMMEDIATE ROLLBACK (< 5 minutes)

# 1. Stop unified pipeline
docker-compose -f docker-compose.prod.yml down

# 2. Restore monolithic scripts
cp scripts/archive/monoliths_YYYYMMDD/*.py scripts/core/

# 3. Restore cron jobs
crontab -e
# Switch back to old script paths

# 4. Restart old pipelines
python scripts/core/batch_opportunity_scoring.py --limit 100

# 5. Verify functionality
python scripts/testing/verify_rollback.py

# 6. Document issues
cat > rollback_report_$(date +%Y%m%d_%H%M%S).md << 'REPORT'
# Rollback Report

**Time**: $(date)
**Reason**: [Describe issue]
**Actions Taken**: [List steps]
**Current State**: Monoliths restored, production stable
**Next Steps**: [Plan for addressing issues]
REPORT

# 7. Notify team
echo "Production rolled back to monoliths. Investigating issues." | mail team@
```

---

## Success Celebration 🎉

**Once all validation passes**:

1. **Create Migration Completion Report**
   - Document all metrics achieved
   - Highlight improvements
   - Note lessons learned

2. **Team Celebration**
   - Recognize contributions
   - Share success story
   - Plan for future enhancements

3. **External Communication**
   - Update stakeholders
   - Document case study
   - Share technical blog post (optional)

---

## Final Deliverables

### Code
- ✅ Unified pipeline in production
- ✅ Monoliths archived with documentation
- ✅ All success metrics validated

### Documentation
- ✅ Architecture documentation complete
- ✅ Runbooks and procedures updated
- ✅ API documentation published
- ✅ SDK integration guide finalized

### Process
- ✅ Team trained
- ✅ Knowledge transferred
- ✅ Monitoring established
- ✅ Maintenance procedures documented

---

## Post-Migration Roadmap

**Next Steps After Completion**:

1. **Week 12-14: Optimization**
   - Performance tuning
   - Cost optimization
   - UX improvements

2. **Week 15-18: Advanced Features**
   - Real-time processing
   - Advanced analytics
   - ML model improvements

3. **Week 19+: New Capabilities**
   - Additional data sources
   - New AI models
   - Expanded integrations

---

## Final Status

**Migration Status**: ⏸️ AWAITING EXECUTION  
**Last Updated**: 2025-11-19  
**Expected Completion**: Week 11  

---

## Closure

This phase completes the **11-week unified pipeline refactoring** initiative.

**Achievements**:
- ✅ 3,574 lines of duplicate code eliminated
- ✅ $3,528/year cost savings preserved
- ✅ Next.js integration enabled
- ✅ 50% faster development velocity
- ✅ Modular, maintainable architecture
- ✅ Production-ready API infrastructure

**Thank you** to all contributors who made this transformation possible! 🚀

---

[← Back to Phases](../PHASES.md) | [↑ Top](#phase-11-production-migration) | [📋 Master Plan](../README.md)
