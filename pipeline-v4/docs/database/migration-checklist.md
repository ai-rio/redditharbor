# Migration Checklist for Developers

> <span style="color: #FF6B35;">**CueTimer**</span> Pipeline V4 Migration Checklist
> <span style="color: #004E89;">Version:</span> 1.0
> <span style="color: #F7B801;">Last Updated:</span> 2025-12-10

---

## Pre-Migration Checklist

### 📋 Planning Phase

- [ ] **Understand the Change**
  - [ ] What columns/tables are being added/removed/modified?
  - [ ] Will data be lost during rollback?
  - [ ] Is the change backwards compatible?
  - [ ] Will this require application downtime?

- [ ] **Review with Team**
  - [ ] PR created for model changes
  - [ ] Code reviewed by at least one senior developer
  - [ ] Migration plan discussed in team meeting
  - [ ] Impact on other services assessed

- [ ] **Check Dependencies**
  - [ ] No other migrations in progress
  - [ ] Application code compatible with both old and new schema
  - [ ] Related tests updated
  - [ ] Documentation updated

### 🔧 Technical Preparation

- [ ] **Model Review**
  - [ ] Field types are appropriate for data
  - [ ] Default values specified where needed
  - [ ] Indexes added for query performance
  - [ ] Constraints properly defined

- [ ] **Database Considerations**
  - [ ] Estimated data volume for new columns
  - [ ] Index size calculated
  - [ ] Query performance impact assessed
  - [ ] Lock duration estimated

---

## Migration Creation Checklist

### 📝 Generate Migration

- [ ] **Environment Setup**
  - [ ] On correct branch
  - [ ] Virtual environment activated
  - [ ] Database connection working
  - [ ] Alembic initialized

- [ ] **Generate Migration**
  ```bash
  alembic revision --autogenerate -m "Clear, descriptive message"
  ```

- [ ] **Migration Naming**
  - [ ] Uses snake_case
  - [ ] Starts with action verb (add, remove, update)
  - [ ] Describes what changed
  - [ ] Examples:
    - `add_priority_field_to_opportunities`
    - `remove_unused_legacy_columns`
    - `update_score_constraints_range`

### 👀 Review Generated Migration

- [ ] **File Structure**
  - [ ] Revision ID correct
  - [ ] Down revision correct
  - [ ] Create date present
  - [ ] Imports complete

- [ ] **Upgrade Function Review**
  - [ ] All expected operations present
  - [ ] Operations in correct order
  - [ ] No unexpected operations
  - [ ] JSON columns use JSONB for PostgreSQL

- [ ] **Downgrade Function Review**
  - [ ] All operations reversed
  - [ ] In reverse order of upgrade
  - [ ] Will rollback cleanly
  - [ ] Data loss documented if any

- [ ] **Specific Checks**
  ```python
  # ✅ GOOD - JSONB for PostgreSQL
  sa.Column(
      "data",
      sa.JSON().with_variant(sa.dialects.postgresql.JSONB, "postgresql"),
      nullable=False
  )

  # ❌ BAD - Missing PostgreSQL optimization
  sa.Column("data", sa.JSON(), nullable=False)

  # ✅ GOOD - Server default for timestamps
  created_at = sa.Column(
      sa.DateTime(timezone=True),
      server_default=sa.text("now()"),
      nullable=False
  )

  # ✅ GOOD - Unique constraint
  op.create_index(
      op.f("ix_table_field"),
      "table",
      ["field"],
      unique=True
  )
  ```

---

## Testing Checklist

### 🧪 Local Testing

- [ ] **Database Setup**
  - [ ] Test database created
  - [ ] Clean state (no tables)
  - [ ] Current migrations applied
  - [ ] Test data loaded (if needed)

- [ ] **Upgrade Test**
  ```bash
  # Apply migration
  alembic upgrade head

  # Verify schema
  psql -c "\d table_name"

  # Verify indexes
  psql -c "\di table_name"

  # Verify constraints
  psql -c "\d+ table_name"
  ```

- [ ] **Downgrade Test**
  ```bash
  # Rollback migration
  alembic downgrade -1

  # Verify old schema restored
  psql -c "\d table_name"

  # Check no orphaned objects
  psql -c "SELECT indexname FROM pg_indexes WHERE tablename = 'table_name'"
  ```

- [ ] **Application Test**
  - [ ] Application starts with new schema
  - [ ] All tests pass
  - [ ] No database errors in logs
  - [ ] Performance acceptable

### 🚀 Staging Testing

- [ ] **Full Dataset Test**
  - [ ] Migration run on staging database
  - [ ] Full data volume processed
  - [ ] Performance measured
  - [ ] Lock duration acceptable

- [ ] **Application Integration**
  - [ ] Staging app updated
  - [ ] End-to-end tests pass
  - [ ] No runtime errors
  - [ ] API responses correct

- [ ] **Rollback Test**
  - [ ] Rollback tested on staging
  - [ ] Application works after rollback
  - [ ] Data integrity maintained
  - [ ] No orphaned data

---

## Pre-Deployment Checklist

### ✅ Final Verification

- [ ] **Code Quality**
  - [ ] Migration file linted with ruff
  - [ ] All PR approvals received
  - [ ] Tests passing in CI/CD
  - [ ] Documentation updated

- [ ] **Production Preparation**
  - [ ] Backup strategy confirmed
  - [ ] Maintenance window scheduled (if needed)
  - [ ] Team notified of deployment
  - [ ] Monitoring alerts configured

- [ ] **Rollback Plan**
  - [ ] Rollback commands documented
  - [ ] Rollback tested on staging
  - [ ] Data restoration plan ready
  - [ ] Communication plan prepared

### 📊 Production Readiness

- [ ] **Schema Validation**
  ```bash
  # Compare staging and production schemas
  pg_dump --schema-only -h staging-db | diff - <(pg_dump --schema-only -h prod-db)
  ```

- [ ] **Performance Baseline**
  - [ ] Current query times recorded
  - [ ] Expected impact documented
  - [ ] Performance alerts configured
  - [ ] Success criteria defined

- [ ] **Safety Checks**
  - [ ] No other deployments in progress
  - [ ] Database load below threshold
  - [ ] Enough disk space for migration
  - [ ] Team availability during deployment

---

## Deployment Checklist

### 🚀 Deployment Process

- [ ] **Pre-Deployment**
  - [ ] Put up maintenance mode (if needed)
  - [ ] Stop application (if needed)
  - [ ] Create database backup
  - [ ] Notify team of deployment start

- [ ] **Migration Execution**
  ```bash
  # Check current state
  alembic current

  # Run migration
  alembic upgrade head

  # Verify completion
  alembic current
  psql -c "\d table_name"
  ```

- [ ] **Post-Deployment**
  - [ ] Verify new schema
  - [ ] Check application health
  - [ ] Run smoke tests
  - [ ] Monitor error rates
  - [ ] Remove maintenance mode
  - [ ] Notify team of completion

### 🔍 Monitoring

- [ ] **Immediate Monitoring (First 30 mins)**
  - [ ] Error rate below threshold
  - [ ] Response time acceptable
  - [ ] Database connections normal
  - [ ] No timeout errors

- [ ] **Extended Monitoring (First 24 hours)**
  - [ ] Daily job completion
  - [ ] Query performance stable
  - [ ] No memory leaks
  - [ ] Backup jobs successful

---

## Post-Migration Checklist

### ✅ Validation

- [ ] **Data Integrity**
  - [ ] Row counts match expectations
  - [ ] No duplicate data
  - [ ] Referential integrity maintained
  - [ ] Data quality checks pass

- [ ] **Performance Validation**
  - [ ] Query times within acceptable range
  - [ ] Indexes being used effectively
  - [ ] No full table scans
  - [ ] Database load normal

- [ ] **Application Health**
  - [ ] All features working
  - [ ] No new errors in logs
  - [ ] User feedback positive
  - [ ] Metrics within normal ranges

### 📚 Documentation Updates

- [ ] **Update Documentation**
  - [ ] Schema documentation updated
  - [ ] Migration guide updated
  - [ ] API documentation updated
  - [ ] Architecture diagrams updated

- [ ] **Team Communication**
  - [ ] Migration summary sent
  - [ ] Lessons learned documented
  - [ ] Best practices updated
  - [ ] Knowledge base updated

### 🧹 Cleanup

- [ ] **Code Cleanup**
  - [ ] Remove temporary scripts
  - [ ] Clean up test data
  - [ ] Archive old migration files
  - [ ] Update TODO comments

- [ ] **Environment Cleanup**
  - [ ] Remove staging test data
  - [ ] Clean up temporary files
  - [ ] Reset test environments
  - [ ] Archive logs

---

## Emergency Checklist

### 🚨 If Migration Fails

1. **Stop immediately**
   ```bash
   # Cancel running migration
   # Don't force kill - may leave locks

   # Check what's running
   psql -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
   ```

2. **Assess impact**
   - [ ] Check error logs
   - [ ] Verify application status
   - [ ] Identify failure point
   - [ ] Document what happened

3. **Decide action**
   - [ ] Can we continue? (Retry)
   - [ ] Need to rollback?
   - [ ] Can we work around it?
   - [ ] Who needs to be notified?

4. **Execute plan**
   - [ ] Follow rollback procedure if needed
   - [ ] Update team on status
   - [ ] Document resolution
   - [ ] Schedule follow-up

### 📋 Post-Mortem

If migration fails:
- [ ] Timeline of events created
- [ ] Root cause identified
- [ ] Impact assessed
- [ ] Prevention measures defined
- [ ] Process improvements documented
- [ ] Team debrief scheduled

---

## Common Pitfalls to Avoid

### ⚠️ Known Issues

1. **JSON vs JSONB**
   - Always check for JSONB in PostgreSQL
   - Autogenerate may miss this

2. **Missing Server Defaults**
   - Check timestamp fields have `server_default=sa.text("now()")`
   - Autogenerate doesn't always detect these

3. **Large Table Modifications**
   - May require special handling
   - Consider multi-step migrations
   - Test on realistic data volumes

4. **Enum Changes**
   - PostgreSQL doesn't support removing enum values
   - Plan enum changes carefully

5. **Lock Duration**
   - Some operations lock tables
   - Estimate impact before deployment
   - Consider maintenance window

### 💡 Pro Tips

1. **Always test rollback** - Never assume it works
2. **Use descriptive messages** - Future you will thank you
3. **Keep migrations small** - One change per migration
4. **Document data loss** - Be explicit about what's lost
5. **Review with peers** - Fresh eyes catch mistakes

---

## Quick Reference

### Commands
```bash
# Create migration
alembic revision --autogenerate -m "message"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Check status
alembic current
alembic history
```

### File Locations
- Migrations: `alembic/versions/`
- Configuration: `alembic.ini`
- Environment: `alembic/env.py`

### Contacts
- DBA Team: dba@company.com
- On-call Engineer: +1-555-0123
- Emergency Channel: #pipeline-emergency

---

**Remember:** When in doubt, ask! It's better to delay a migration than to cause production issues.

**Last Updated:** 2025-12-10
**Version:** 1.0
**Maintainer:** Pipeline V4 Team