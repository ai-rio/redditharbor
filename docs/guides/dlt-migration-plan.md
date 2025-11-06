# DLT Migration Plan: From Manual Collection to Automated Pipelines

## Executive Summary

This document outlines a **3-week phased migration** from RedditHarbor's current manual data collection approach to a DLT-powered automated pipeline system. The migration minimizes risk through parallel testing and gradual traffic cutover.

**Timeline:** 3 weeks
**Risk Level:** Low (parallel testing validates functionality)
**Expected ROI:** 80-95% API call reduction, 70% code reduction, production-ready deployment

---

## Pre-Migration Checklist

### Week 0: Preparation (Before Migration Starts)

- [ ] **Backup existing database**
  ```bash
  # Create Supabase backup
  supabase db dump -f backup_pre_dlt_$(date +%Y%m%d).sql

  # Archive current scripts
  mkdir -p archive/pre-dlt-migration-$(date +%Y%m%d)
  cp -r scripts/ archive/pre-dlt-migration-$(date +%Y%m%d)/
  ```

- [ ] **Document current performance baselines**
  ```bash
  # Run baseline collection
  python scripts/collect_problem_posts.py --subreddits opensource --limit 100

  # Record metrics:
  # - API calls made: _____
  # - Execution time: _____
  # - Rows inserted: _____
  # - Errors encountered: _____
  ```

- [ ] **Verify environment setup**
  ```bash
  # Check Python version (3.9+)
  python --version

  # Verify Supabase running
  supabase status

  # Test Reddit API credentials
  python -c "import praw; print('✓ Reddit API working')"
  ```

- [ ] **Review DLT documentation**
  - Read: `docs/guides/dlt-integration-guide.md`
  - Read: `docs/architecture/dlt-pipeline-architecture.md`
  - Bookmark: https://dlthub.com/docs

- [ ] **Communicate migration plan to team**
  - Share timeline and milestones
  - Identify stakeholders for testing
  - Schedule daily standups during migration

---

## Migration Timeline

### Week 1: Setup, Testing, and Validation

#### Day 1: DLT Installation and Configuration

**Goal:** Install DLT and create basic configuration

**Tasks:**
1. Install DLT with Supabase support
   ```bash
   # Add to requirements.txt
   echo "dlt[supabase]>=1.0.0" >> requirements.txt

   # Install with UV
   uv pip install -r requirements.txt

   # Verify installation
   python -c "import dlt; print(f'✓ DLT {dlt.__version__} installed')"
   ```

2. Create DLT configuration file
   ```bash
   # Create config/dlt_settings.py (see implementation guide)
   touch config/dlt_settings.py
   ```

3. Configure Supabase destination
   ```bash
   # Test Supabase connection
   python -c "
   import dlt
   p = dlt.pipeline(destination='supabase', dataset_name='test')
   print('✓ Supabase connection working')
   "
   ```

**Deliverables:**
- ✓ DLT installed and verified
- ✓ `config/dlt_settings.py` created
- ✓ Supabase connection tested

**Time Estimate:** 2-3 hours

---

#### Day 2: Simple Test Pipeline

**Goal:** Create and run first DLT pipeline with sample data

**Tasks:**
1. Create test pipeline script
   ```bash
   # Create scripts/test_dlt_pipeline.py
   # (See implementation guide for code)
   ```

2. Run test with 10 posts
   ```bash
   python scripts/test_dlt_pipeline.py
   ```

3. Verify data in Supabase Studio
   ```bash
   # Open Supabase Studio
   # http://127.0.0.1:54323
   # Verify table: submissions
   # Check row count: 10
   ```

4. Inspect DLT metadata
   ```bash
   python -c "
   import dlt
   p = dlt.pipeline('reddit_harbor_collection', destination='supabase')
   print(p.state)
   print(p.schema.tables)
   "
   ```

**Success Criteria:**
- ✓ 10 Reddit posts loaded successfully
- ✓ Schema auto-created in Supabase
- ✓ DLT metadata tables present (_dlt_loads, _dlt_version)
- ✓ No errors in execution

**Time Estimate:** 3-4 hours

---

#### Day 3: Incremental Loading Test

**Goal:** Validate incremental loading reduces API calls

**Tasks:**
1. Create incremental test script
   ```bash
   # Create scripts/test_incremental_loading.py
   ```

2. Run first load (full refresh)
   ```bash
   python scripts/test_incremental_loading.py --full-refresh
   # Expected: 100 posts loaded
   ```

3. Run second load (incremental)
   ```bash
   python scripts/test_incremental_loading.py
   # Expected: 0-10 posts loaded (only new since last run)
   ```

4. Measure API call reduction
   ```bash
   # Calculate reduction:
   # First run API calls: 100
   # Second run API calls: 5
   # Reduction: 95%
   ```

**Success Criteria:**
- ✓ First run loads 100 posts
- ✓ Second run loads <10 posts
- ✓ API call reduction: 80%+
- ✓ Incremental state tracked correctly

**Time Estimate:** 4-5 hours

---

#### Day 4: Problem-First Collection with DLT

**Goal:** Migrate problem detection logic to DLT pipeline

**Tasks:**
1. Create `core/dlt_collection.py` with problem-first filtering
   ```bash
   # Implement PROBLEM_KEYWORDS filtering
   # Add DLT source configuration
   # Apply incremental hints
   ```

2. Test with single subreddit
   ```bash
   python -c "
   from core.dlt_collection import collect_problem_posts
   collect_problem_posts(['opensource'], limit=50)
   "
   ```

3. Validate problem posts only
   ```bash
   # Query Supabase to verify filtering worked
   # Check: all posts contain problem keywords
   ```

4. Compare with manual collection
   ```bash
   # Run old script: scripts/collect_problem_posts.py
   # Run new script: core/dlt_collection.py
   # Compare row counts and data quality
   ```

**Success Criteria:**
- ✓ DLT collection matches manual collection (row count ±5%)
- ✓ Problem keyword filtering works
- ✓ Incremental loading functional
- ✓ Execution time comparable or faster

**Time Estimate:** 6-8 hours

---

#### Day 5: Parallel Testing - 1 Subreddit

**Goal:** Run old and new pipelines side-by-side for validation

**Tasks:**
1. Set up parallel test script
   ```bash
   # Create scripts/parallel_test.py
   # Runs both old and new collection
   # Compares results
   ```

2. Run parallel test
   ```bash
   python scripts/parallel_test.py --subreddit opensource --limit 100
   ```

3. Compare results
   ```bash
   # Metrics to compare:
   # - Row count difference
   # - Execution time
   # - API calls made
   # - Error rates
   # - Data quality (spot check 10 posts)
   ```

4. Document discrepancies
   ```bash
   # Create test report
   # Note any differences
   # Investigate root causes
   ```

**Success Criteria:**
- ✓ Row counts within 5% difference
- ✓ Data quality equivalent
- ✓ DLT execution time ≤ manual collection
- ✓ No critical errors in DLT pipeline

**Time Estimate:** 4-5 hours

---

### Week 2: Migration and Gradual Cutover

#### Day 6-7: AI Insights Integration

**Goal:** Chain DLT collection with AI opportunity generation

**Tasks:**
1. Create `scripts/dlt_opportunity_pipeline.py`
   ```python
   # Implement end-to-end pipeline:
   # Reddit Collection (DLT) → AI Analysis → Insights Storage (DLT)
   ```

2. Test AI integration
   ```bash
   python scripts/dlt_opportunity_pipeline.py --subreddits opensource --limit 50
   ```

3. Verify insights storage
   ```bash
   # Check opportunity_analysis table
   # Validate merge (no duplicates)
   # Confirm AI success rate (80%+)
   ```

4. Measure end-to-end performance
   ```bash
   # Time full pipeline
   # Compare with manual approach
   # Expected: 20-30% faster
   ```

**Success Criteria:**
- ✓ AI insights generated for new posts
- ✓ Merge write prevents duplicates
- ✓ Success rate 80%+
- ✓ End-to-end pipeline under 5 minutes (50 posts)

**Time Estimate:** 8-10 hours

---

#### Day 8: Traffic Cutover - 10% (1 Subreddit)

**Goal:** Start routing real traffic to DLT pipeline

**Tasks:**
1. Choose low-risk subreddit for cutover
   ```bash
   # Suggested: r/opensource (lower traffic)
   # Keep other subreddits on manual collection
   ```

2. Update production scheduler
   ```bash
   # If using cron:
   # Comment out manual collection for r/opensource
   # Add DLT collection for r/opensource
   ```

3. Monitor for 24 hours
   ```bash
   # Check logs every 4 hours
   # Verify data loading correctly
   # Watch for errors
   ```

4. Create rollback plan
   ```bash
   # Document steps to revert to manual collection
   # Keep manual scripts ready
   ```

**Success Criteria:**
- ✓ 24 hours of stable operation
- ✓ No data loss or corruption
- ✓ Error rate <5%
- ✓ Incremental loading working

**Time Estimate:** 2-3 hours (plus monitoring)

---

#### Day 9-10: Traffic Cutover - 50% (3 Subreddits)

**Goal:** Increase DLT traffic to 50%

**Tasks:**
1. Add 2 more subreddits to DLT
   ```bash
   # Add: r/SideProject, r/productivity
   # Keep manual: r/freelance, r/personalfinance
   ```

2. Monitor increased load
   ```bash
   # Check resource usage
   # Verify API rate limits not exceeded
   # Watch for performance degradation
   ```

3. Validate data consistency
   ```bash
   # Compare DLT vs manual collection
   # Spot check 20 random posts
   # Verify schema consistency
   ```

4. Adjust configuration if needed
   ```bash
   # Tune batch sizes
   # Adjust incremental frequency
   # Optimize schema settings
   ```

**Success Criteria:**
- ✓ 48 hours of stable operation
- ✓ 3 subreddits loading correctly
- ✓ Error rate <5%
- ✓ Resource usage acceptable

**Time Estimate:** 3-4 hours (plus monitoring)

---

#### Day 11-12: Traffic Cutover - 100% (All Subreddits)

**Goal:** Complete migration to DLT for all subreddits

**Tasks:**
1. Migrate remaining subreddits
   ```bash
   # Add: r/freelance, r/personalfinance
   # Disable all manual collection scripts
   ```

2. Run full-scale test
   ```bash
   # Collect from all 5 subreddits
   # Verify each loads successfully
   # Check total execution time
   ```

3. Monitor for 72 hours
   ```bash
   # Daily checks of:
   # - Data loading
   # - Error logs
   # - Resource usage
   # - API rate limits
   ```

4. Optimize performance
   ```bash
   # Profile slow queries
   # Adjust batch sizes
   # Fine-tune incremental settings
   ```

**Success Criteria:**
- ✓ 72 hours of stable operation
- ✓ All subreddits loading correctly
- ✓ Error rate <5%
- ✓ API call reduction 80%+
- ✓ Execution time meets SLA

**Time Estimate:** 4-5 hours (plus monitoring)

---

### Week 3: Production Deployment and Cleanup

#### Day 13-14: Airflow Integration

**Goal:** Deploy DLT pipeline to Airflow for scheduled execution

**Tasks:**
1. Create Airflow DAG
   ```bash
   # Create .airflow/dags/reddit_opportunity_dag.py
   # Configure schedule: daily at 2 AM UTC
   # Add error notifications
   ```

2. Test DAG locally
   ```bash
   # Start Airflow
   airflow standalone

   # Trigger DAG manually
   airflow dags trigger reddit_opportunity_pipeline

   # Monitor execution
   airflow dags list-runs -d reddit_opportunity_pipeline
   ```

3. Deploy to production
   ```bash
   # Copy DAG to production Airflow
   # Verify environment variables set
   # Enable DAG
   ```

4. Set up monitoring
   ```bash
   # Configure email alerts
   # Add Slack notifications (optional)
   # Set up Datadog metrics (optional)
   ```

**Success Criteria:**
- ✓ DAG runs successfully on schedule
- ✓ Error notifications working
- ✓ Execution time within SLA
- ✓ Monitoring dashboards configured

**Time Estimate:** 6-8 hours

---

#### Day 15: Script Cleanup and Archival

**Goal:** Archive old scripts and clean up codebase

**Tasks:**
1. Archive legacy collection scripts
   ```bash
   # Create archive directory
   mkdir -p archive/legacy-collection-$(date +%Y%m%d)

   # Move old scripts
   mv scripts/collect_problem_posts.py archive/legacy-collection-*/
   mv scripts/filter_problems.py archive/legacy-collection-*/
   mv scripts/fix_comment_linkage.py archive/legacy-collection-*/

   # Keep for 90 days, then delete
   ```

2. Update import paths
   ```bash
   # Search for old script imports
   rg "scripts.collect_problem_posts" --files-with-matches

   # Update to new DLT imports
   # from core.dlt_collection import collect_problem_posts
   ```

3. Run linting
   ```bash
   ruff check . && ruff format .
   ```

4. Update .gitignore
   ```bash
   # Add DLT cache directories
   echo ".dlt/" >> .gitignore
   echo "_dlt_cache/" >> .gitignore
   ```

**Deliverables:**
- ✓ Old scripts archived
- ✓ Import paths updated
- ✓ Code linted and formatted
- ✓ .gitignore updated

**Time Estimate:** 2-3 hours

---

#### Day 16-17: Documentation Updates

**Goal:** Update all documentation to reflect DLT architecture

**Tasks:**
1. Update README.md
   ```bash
   # Add DLT section
   # Update architecture diagram
   # Update setup instructions
   ```

2. Update docs/README.md
   ```bash
   # Revise data collection section
   # Add DLT pipeline overview
   # Update API references
   ```

3. Create team training materials
   ```bash
   # docs/guides/dlt-team-training.md
   # Include:
   # - DLT basics
   # - Running pipelines
   # - Troubleshooting guide
   # - Common issues and solutions
   ```

4. Update memory files
   ```bash
   # Update memory_project_overview.md
   # Update memory_active_work.md
   # Document DLT as primary collection method
   ```

**Deliverables:**
- ✓ README.md updated
- ✓ docs/README.md revised
- ✓ Team training materials created
- ✓ Memory files updated

**Time Estimate:** 6-8 hours

---

#### Day 18: Performance Benchmarking

**Goal:** Document performance improvements and ROI

**Tasks:**
1. Run comprehensive benchmarks
   ```bash
   python scripts/benchmark_dlt_performance.py
   ```

2. Create performance report
   ```bash
   # docs/reports/dlt-migration-performance-report.md
   # Include:
   # - API call reduction (%)
   # - Execution time improvement (%)
   # - Code reduction (lines)
   # - Error rate comparison
   # - Resource usage comparison
   ```

3. Calculate cost savings
   ```bash
   # Estimate:
   # - API call cost reduction
   # - Developer time savings (maintenance)
   # - Infrastructure cost changes
   ```

4. Share results with team
   ```bash
   # Present findings in team meeting
   # Highlight key improvements
   # Discuss lessons learned
   ```

**Deliverables:**
- ✓ Benchmark results documented
- ✓ Performance report created
- ✓ Cost savings calculated
- ✓ Results shared with team

**Time Estimate:** 4-5 hours

---

#### Day 19-21: Stabilization and Optimization

**Goal:** Monitor production, fix issues, optimize performance

**Tasks:**
1. Monitor production metrics
   ```bash
   # Daily checks for 3 days:
   # - Error rates
   # - Execution times
   # - Data quality
   # - API rate limits
   ```

2. Address any issues
   ```bash
   # Fix bugs discovered in production
   # Adjust configuration as needed
   # Optimize slow queries
   ```

3. Collect user feedback
   ```bash
   # Survey team on DLT experience
   # Identify pain points
   # Document feature requests
   ```

4. Create improvement roadmap
   ```bash
   # docs/roadmap/dlt-future-improvements.md
   # Plan next optimizations:
   # - Add more subreddits
   # - Increase collection frequency
   # - Add real-time streaming
   ```

**Deliverables:**
- ✓ Production stable for 72 hours
- ✓ Issues resolved
- ✓ User feedback collected
- ✓ Improvement roadmap created

**Time Estimate:** 8-10 hours (spread over 3 days)

---

## Rollback Plan

### When to Rollback

Trigger rollback if any of the following occur:

- ❌ Data loss or corruption detected
- ❌ Error rate >20% for 6+ hours
- ❌ Critical production incident
- ❌ API rate limits consistently exceeded
- ❌ Execution time SLA missed repeatedly

### Rollback Procedure

```bash
# Step 1: Disable DLT pipeline
# Stop Airflow DAG
airflow dags pause reddit_opportunity_pipeline

# Step 2: Restore legacy scripts from archive
cp -r archive/legacy-collection-*/scripts/* scripts/

# Step 3: Re-enable manual collection
# Update cron/scheduler to use old scripts

# Step 4: Verify rollback
python scripts/collect_problem_posts.py --subreddits opensource --limit 10

# Step 5: Investigate root cause
# Review DLT logs
# Identify issue
# Create fix plan

# Step 6: Re-attempt migration (after fix)
# Follow migration plan again with fixes applied
```

---

## Risk Assessment

### High-Risk Areas

| Risk | Impact | Probability | Mitigation |
|------|--------|------------|------------|
| Data loss during migration | High | Low | Parallel testing, backups |
| Incremental loading bugs | Medium | Medium | Extensive testing, monitoring |
| API rate limit exceeded | Medium | Low | Gradual cutover, rate limiting |
| Schema conflicts | Medium | Low | Schema evolution testing |
| Team knowledge gap | Low | Medium | Training materials, documentation |

### Mitigation Strategies

1. **Parallel Testing (Week 1)** - Validate DLT matches manual collection
2. **Gradual Cutover (Week 2)** - 10% → 50% → 100% traffic shift
3. **Comprehensive Monitoring** - Real-time alerting for issues
4. **Rollback Plan** - Quick revert to manual collection if needed
5. **Team Training** - Ensure team understands DLT workflows

---

## Success Metrics

### Key Performance Indicators (KPIs)

| Metric | Baseline (Manual) | Target (DLT) | Actual (Post-Migration) |
|--------|------------------|--------------|------------------------|
| API Calls (incremental) | 1000 | <200 | _____ |
| Execution Time | 45s | <40s | _____ |
| Code Lines (collection) | 150 | <50 | _____ |
| Error Rate | 8% | <5% | _____ |
| Schema Updates (manual) | Weekly | Automatic | _____ |
| Incremental State Tracking | None | Automatic | _____ |
| Production Deployment | Manual | Airflow | _____ |

### Success Criteria

Migration is successful if:

- ✓ API call reduction ≥80%
- ✓ Error rate <5%
- ✓ Code reduction ≥60%
- ✓ Zero data loss
- ✓ Production deployment functional
- ✓ Team trained and confident

---

## Post-Migration Review

### Week 4: Retrospective

**Schedule:** End of Week 3
**Participants:** Full team
**Duration:** 1 hour

**Agenda:**
1. Review migration timeline (what went well, what didn't)
2. Discuss performance improvements
3. Share lessons learned
4. Identify remaining issues
5. Plan next optimizations

**Deliverables:**
- Retrospective notes document
- Action items for improvements
- Updated best practices guide

---

## Appendix: Quick Reference Commands

### DLT Troubleshooting

```bash
# Check pipeline state
python -c "import dlt; p = dlt.pipeline('reddit_harbor_collection', destination='supabase'); print(p.state)"

# Reset incremental state (if corrupted)
python -c "import dlt; p = dlt.pipeline('reddit_harbor_collection', destination='supabase'); p.drop_state()"

# View schema
python -c "import dlt; p = dlt.pipeline('reddit_harbor_collection', destination='supabase'); print(p.schema.tables)"

# Inspect last run
python -c "import dlt; p = dlt.pipeline('reddit_harbor_collection', destination='supabase'); print(p.last_trace)"
```

### Supabase Verification

```bash
# Check row counts
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres \
  -c "SELECT COUNT(*) FROM submissions;"

# Verify incremental loading
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres \
  -c "SELECT MAX(created_utc) FROM submissions;"

# Check for duplicates
psql -h 127.0.0.1 -p 54322 -U postgres -d postgres \
  -c "SELECT id, COUNT(*) FROM submissions GROUP BY id HAVING COUNT(*) > 1;"
```

### Performance Monitoring

```bash
# Monitor API calls
grep "API request" logs/*.log | wc -l

# Check execution time
python -c "import dlt; p = dlt.pipeline('reddit_harbor_collection', destination='supabase'); print(f'Last run: {p.last_trace.duration}s')"

# View error logs
tail -f logs/dlt_pipeline.log | grep ERROR
```

---

## Contact and Support

**Migration Lead:** [Your Name]
**Email:** [your-email@domain.com]
**Slack:** #redditharbor-dlt-migration

**Daily Standup:** 9:00 AM (during migration weeks)
**Escalation Path:** Lead → Team Manager → CTO

---

*Migration Plan Version: 1.0*
*Last Updated: 2025-01-06*
*Next Review: Weekly during migration*
