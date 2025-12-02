# DLT to SQLAlchemy Migration - Execution Guide

**Status**: Ready for execution
**Framework**: Phase-based enforcement with specialized agents
**Progress Tracker**: `PROGRESS.md`

---

## Overview

This migration uses **4 phase-specific slash commands** that enforce:
- ✅ Sequential phase execution (can't skip phases)
- ✅ Specialized agent delegation per phase
- ✅ Workspace cleanliness (no orphan files)
- ✅ Documentation references for all agents
- ✅ Success criteria validation
- ✅ Automatic cleanup and archival

---

## Phase Architecture

| Phase | Command | Agent | Duration | Dependencies |
|-------|---------|-------|----------|--------------|
| **Phase 1: Foundation** | `/phase1-foundation` | test-engineer | 1-2 days | None |
| **Phase 2: Implementation** | `/phase2-implementation` | backend-architect | 3-5 days | Phase 1 complete |
| **Phase 3: Validation** | `/phase3-validation` | test-engineer | 2-3 days | Phase 2 complete |
| **Phase 4: Migration** | `/phase4-migration` | data-engineer | 1-2 days | Phase 3 complete |

**Total Estimated Duration**: 7-12 days

---

## How to Execute

### Step 1: Start Phase 1

```bash
# In Claude Code, run:
/phase1-foundation
```

**What happens**:
1. Pre-flight checks run (validates environment, checks for orphans)
2. If checks pass, spawns **test-engineer** agent with full context package
3. Agent executes Phase 1 deliverables:
   - Characterization tests documenting DLT behavior
   - SQLAlchemy foundation setup
   - Phase 1 validation report
4. Main Claude validates deliverables
5. Updates `PROGRESS.md` to mark Phase 1 complete
6. Archives workspace and cleans up

**Success Indicators**:
- ✅ `tests/test_dlt_characterization.py` exists
- ✅ `storage/sqlalchemy_loader.py` foundation created
- ✅ DLT silent failure documented with evidence
- ✅ SQLAlchemy connects successfully
- ✅ Phase 1 status in PROGRESS.md: "✅ COMPLETE"

**If Phase 1 Fails**:
- Review error logs
- Fix blockers
- Clean up workspace: `rm -rf pipeline-v2/phase1-workspace`
- Re-run `/phase1-foundation`

---

### Step 2: Start Phase 2 (Only After Phase 1 Complete)

```bash
# In Claude Code, run:
/phase2-implementation
```

**What happens**:
1. Pre-flight checks verify Phase 1 is complete
2. If Phase 1 incomplete, command **blocks** and tells you to run Phase 1 first
3. If Phase 1 complete, spawns **backend-architect** agent
4. Agent builds complete SQLAlchemy implementation:
   - Full SQLAlchemy loader with transaction control
   - DLT compatibility adapter
   - Comprehensive test suite
5. Main Claude validates all tests pass
6. Updates PROGRESS.md, archives workspace

**Success Indicators**:
- ✅ `storage/sqlalchemy_loader.py` - Complete implementation
- ✅ `storage/dlt_compatibility_adapter.py` - Adapter created
- ✅ `tests/test_sqlalchemy_loader.py` - All tests passing (100%)
- ✅ Explicit transaction control working
- ✅ Phase 2 status: "✅ COMPLETE"

**If Phase 2 Fails**:
- Review test failures
- May need to revisit Phase 1 foundation
- Clean workspace and retry
- Rollback option available

---

### Step 3: Start Phase 3 (Only After Phase 2 Complete)

```bash
# In Claude Code, run:
/phase3-validation
```

**What happens**:
1. Pre-flight checks verify Phase 2 is complete
2. Spawns **test-engineer** agent for validation
3. Agent performs:
   - Parallel testing (DLT vs SQLAlchemy comparison)
   - Performance benchmarking
   - Data integrity validation
   - Silent failure elimination confirmation
4. Main Claude validates all benchmarks met
5. Updates PROGRESS.md, archives results

**Success Indicators**:
- ✅ `tests/test_migration_parallel.py` - All tests passing
- ✅ Performance meets targets (< 1s, < 5s, < 30s for small/med/large batches)
- ✅ No data loss or corruption
- ✅ Silent failures eliminated (confirmed with evidence)
- ✅ Phase 3 status: "✅ COMPLETE"

**If Phase 3 Fails**:
- Performance issues: Profile and optimize
- Test failures: May indicate Phase 2 issues
- Rollback to Phase 2 if needed

---

### Step 4: Start Phase 4 (Only After Phase 3 Complete)

```bash
# In Claude Code, run:
/phase4-migration
```

**What happens**:
1. Pre-flight checks verify Phase 3 is complete
2. Spawns **data-engineer** agent for production migration
3. Agent executes:
   - Full database backup (multiple formats)
   - Migration script creation
   - Configuration updates (switch to SQLAlchemy)
   - Post-migration validation
4. Main Claude validates migration success
5. Updates PROGRESS.md to "✅ MIGRATION COMPLETE"

**Success Indicators**:
- ✅ Full database backup created and verified
- ✅ `scripts/migrate_to_sqlalchemy.py` - Migration script ready
- ✅ Configuration updated to use SQLAlchemy
- ✅ All post-migration tests passing
- ✅ No data loss
- ✅ Rollback capability validated
- ✅ Phase 4 status: "✅ COMPLETE"

**If Phase 4 Fails**:
- **IMMEDIATELY ROLLBACK**: `python scripts/migrate_to_sqlalchemy.py --rollback`
- Or restore from backup
- Document failure
- Fix issues and retry

---

## Progress Tracking

### Check Current Status

```bash
# View progress tracker
cat pipeline-v2/docs/dlt-to-sqlalchemy-migration/PROGRESS.md
```

### Progress Indicators

**Phase Status Meanings**:
- ❌ **NOT STARTED** - Phase hasn't begun
- ⏳ **READY** - Previous phase complete, ready to start
- 🔒 **BLOCKED** - Previous phase incomplete, cannot start
- ✅ **COMPLETE** - Phase finished and validated

---

## Enforcement Mechanisms

### What Prevents Mistakes

1. **Phase Gate Blocking**:
   - Can't run Phase 2 until Phase 1 complete
   - Can't run Phase 3 until Phase 2 complete
   - Can't run Phase 4 until Phase 3 complete

2. **Workspace Cleanliness**:
   - Each phase checks for orphan files before starting
   - Fails if `pipeline-v2/` root has orphans
   - Workspace automatically cleaned up after phase completion

3. **Documentation References**:
   - Every agent gets hardcoded doc references
   - Agents can't skip reading required context
   - All docs verified to exist before agent spawn

4. **Success Criteria Validation**:
   - Main Claude validates deliverables after agent completes
   - Tests must pass before phase marked complete
   - Manual validation steps documented

5. **Automatic Archival**:
   - Phase workspaces deleted after completion
   - Artifacts archived to `reports/phase<N>/`
   - Prevents workspace clutter

---

## Agent Responsibilities

### Phase 1: test-engineer
- Write characterization tests for DLT behavior
- Document DLT silent failures with evidence
- Set up SQLAlchemy foundation (connection only)
- Create Phase 1 validation report

### Phase 2: backend-architect
- Build complete SQLAlchemy loader implementation
- Implement explicit transaction control
- Create DLT compatibility adapter
- Write comprehensive test suite

### Phase 3: test-engineer
- Run parallel validation tests (DLT vs SQLAlchemy)
- Perform performance benchmarking
- Validate data integrity
- Confirm silent failure elimination

### Phase 4: data-engineer
- Create full database backup
- Build migration script with rollback capability
- Update configuration to use SQLAlchemy
- Perform post-migration validation

---

## Workspace Management

### Phase Workspaces (Temporary)

Each phase creates a disposable workspace:

```
pipeline-v2/phase1-workspace/  # Created by Phase 1, deleted after completion
pipeline-v2/phase2-workspace/  # Created by Phase 2, deleted after completion
pipeline-v2/phase3-workspace/  # Created by Phase 3, deleted after completion
pipeline-v2/phase4-workspace/  # Created by Phase 4, deleted after completion
```

**Rules**:
- Only ONE workspace exists at a time
- Workspace deleted after phase completion
- Useful artifacts archived to `reports/phase<N>/`
- NO files outside workspace during execution

### Permanent Artifacts

All deliverables and reports archived here:

```
pipeline-v2/docs/dlt-to-sqlalchemy-migration/
├── PROGRESS.md                           # Progress tracker (updated by phases)
├── reports/
│   ├── phase1/
│   │   ├── validation-report.md          # Phase 1 findings
│   │   └── logs/                         # Archived logs
│   ├── phase2/
│   │   ├── implementation-report.md      # Phase 2 implementation details
│   │   └── logs/
│   ├── phase3/
│   │   ├── validation-report.md          # Phase 3 validation results
│   │   ├── benchmarks/                   # Performance benchmarks
│   │   └── comparison_results/           # DLT vs SQLAlchemy comparison
│   └── phase4/
│       ├── migration-report.md           # Phase 4 migration completion
│       └── migration_logs/               # Migration execution logs
└── backups/                              # Phase 4 database backups (permanent)
```

---

## Troubleshooting

### Common Issues

#### "Phase X blocked - previous phase incomplete"
**Solution**: Complete the previous phase first
```bash
# Check what phase you're on
cat pipeline-v2/docs/dlt-to-sqlalchemy-migration/PROGRESS.md

# Run the required phase
/phaseX-<name>
```

#### "Orphan files found in pipeline-v2/"
**Solution**: Clean up orphan files
```bash
# Find orphans
find pipeline-v2/ -maxdepth 1 -type f \( -name "*.py" -o -name "*.log" \) ! -name "README.md" ! -name "__init__.py" ! -name "main.py"

# Move to appropriate location or delete
```

#### "Workspace already exists"
**Solution**: Previous phase didn't clean up properly
```bash
# Remove old workspace
rm -rf pipeline-v2/phase*-workspace/

# Re-run phase
```

#### "Tests failing in Phase X"
**Solution**: Debug test failures
```bash
# Run tests with verbose output
pytest pipeline-v2/tests/test_sqlalchemy_loader.py -v -s

# Check logs for details
# Fix issues and re-run phase
```

#### "Agent not completing deliverables"
**Solution**: Agent may need guidance
- Check if agent is blocked on a decision
- Review agent's questions or errors
- Provide clarification if needed
- Agent will update when unblocked

---

## Rollback Procedures

### Phase 1-3 Rollback (Pre-Migration)
**Safe**: No production changes yet

```bash
# Delete phase deliverables
rm -rf pipeline-v2/tests/test_dlt_characterization.py
rm -rf pipeline-v2/storage/sqlalchemy_loader.py
rm -rf pipeline-v2/storage/dlt_compatibility_adapter.py
rm -rf pipeline-v2/tests/test_sqlalchemy_loader.py
rm -rf pipeline-v2/tests/test_migration_parallel.py

# Clean up reports
rm -rf pipeline-v2/docs/dlt-to-sqlalchemy-migration/reports/

# Reset PROGRESS.md to initial state
```

### Phase 4 Rollback (Post-Migration)
**Critical**: Production configuration changed

```bash
# Option 1: Use rollback script
python pipeline-v2/scripts/migrate_to_sqlalchemy.py --rollback

# Option 2: Manual rollback from backup
PGPASSWORD=postgres psql -h 127.0.0.1 -p 54322 -U postgres -d postgres \
  -f pipeline-v2/docs/dlt-to-sqlalchemy-migration/backups/full_backup_*.sql

# Verify rollback successful
pytest pipeline-v2/tests/test_dlt_loader.py -v
```

---

## Success Criteria Summary

### Phase 1 Success
- [ ] DLT silent failures documented with evidence
- [ ] SQLAlchemy foundation connects and validates
- [ ] ID resolution system integrated
- [ ] Test infrastructure in place

### Phase 2 Success
- [ ] SQLAlchemy loader implements all required features
- [ ] DLT compatibility adapter maintains existing interfaces
- [ ] Comprehensive test suite passes (100%)
- [ ] Transaction control working explicitly

### Phase 3 Success
- [ ] Parallel tests confirm data consistency
- [ ] Performance comparable or better than DLT
- [ ] Error handling significantly improved
- [ ] No silent failures detected

### Phase 4 Success
- [ ] Migration completed without data loss
- [ ] All existing functionality preserved
- [ ] Performance acceptable in production
- [ ] Monitoring shows reliable operation

---

## Final Migration Checklist

Before declaring migration complete:

- [ ] All 4 phases marked "✅ COMPLETE" in PROGRESS.md
- [ ] All tests passing (characterization, unit, parallel)
- [ ] Performance benchmarks met
- [ ] No silent failures detected
- [ ] Full database backup created and verified
- [ ] Configuration updated to use SQLAlchemy
- [ ] Post-migration validation passed
- [ ] Rollback procedures tested and documented
- [ ] No orphan files in pipeline-v2/ root
- [ ] All workspaces cleaned up
- [ ] Migration report completed

---

## Getting Started

**Ready to begin?**

1. Review this execution guide
2. Check PROGRESS.md current status
3. Run: `/phase1-foundation`
4. Follow agent progress
5. Validate deliverables
6. Move to next phase

**Questions or issues?**
- Review phase-specific documentation in `docs/dlt-to-sqlalchemy-migration/`
- Check PROGRESS.md for current status
- Review agent output for guidance
- Rollback if needed and retry

---

**Let's eliminate those silent failures! 🚀**
