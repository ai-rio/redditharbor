# DLT to SQLAlchemy Migration - Quick Reference

## 🎯 Quick Start

```bash
# Check current status
cat pipeline-v2/docs/dlt-to-sqlalchemy-migration/PROGRESS.md

# Run next phase
/phase1-foundation   # Start here if not started
/phase2-implementation
/phase3-validation
/phase4-migration
```

---

## 📊 Phase Overview

| Phase | Command | Agent | Duration | Status Check |
|-------|---------|-------|----------|--------------|
| 1 | `/phase1-foundation` | test-engineer | 1-2 days | DLT silent failure documented |
| 2 | `/phase2-implementation` | backend-architect | 3-5 days | All tests passing |
| 3 | `/phase3-validation` | test-engineer | 2-3 days | Performance meets targets |
| 4 | `/phase4-migration` | data-engineer | 1-2 days | Migration successful |

---

## ✅ Success Criteria

### Phase 1
- ✅ DLT silent failures documented
- ✅ SQLAlchemy foundation working
- ✅ Tests exist (can fail)

### Phase 2
- ✅ Complete implementation
- ✅ 100% tests passing
- ✅ Transaction control explicit

### Phase 3
- ✅ Data consistency validated
- ✅ Performance benchmarks met
- ✅ Silent failures eliminated

### Phase 4
- ✅ Backup created
- ✅ Migration successful
- ✅ No data loss

---

## 🔍 Key Files

### Progress & Reports
```
docs/dlt-to-sqlalchemy-migration/
├── PROGRESS.md              ← Check status here
├── EXECUTION-GUIDE.md       ← Full execution guide
└── reports/
    ├── phase1/
    ├── phase2/
    ├── phase3/
    └── phase4/
```

### Deliverables
```
pipeline-v2/
├── tests/
│   ├── test_dlt_characterization.py   (Phase 1)
│   ├── test_sqlalchemy_loader.py      (Phase 2)
│   └── test_migration_parallel.py     (Phase 3)
├── storage/
│   ├── sqlalchemy_loader.py           (Phase 1 & 2)
│   └── dlt_compatibility_adapter.py   (Phase 2)
└── scripts/
    └── migrate_to_sqlalchemy.py       (Phase 4)
```

---

## 🚨 Common Issues

### "Phase blocked"
→ Complete previous phase first

### "Orphan files found"
→ Clean up: `find pipeline-v2/ -maxdepth 1 -type f`

### "Tests failing"
→ Debug: `pytest -v -s [test_file]`

### "Workspace exists"
→ Remove: `rm -rf pipeline-v2/phase*-workspace/`

---

## 🔄 Rollback

### Pre-Migration (Phase 1-3)
```bash
# Safe - just delete files
rm -rf pipeline-v2/tests/test_dlt_characterization.py
rm -rf pipeline-v2/storage/sqlalchemy_loader.py
# etc...
```

### Post-Migration (Phase 4)
```bash
# Use rollback script
python scripts/migrate_to_sqlalchemy.py --rollback

# Or restore backup
PGPASSWORD=postgres psql -h 127.0.0.1 -p 54322 -U postgres -d postgres \
  -f docs/dlt-to-sqlalchemy-migration/backups/full_backup_*.sql
```

---

## 📝 Validation Commands

### Phase 1
```bash
pytest tests/test_dlt_characterization.py -v
python -c "from storage.sqlalchemy_loader import SQLAlchemyLoader; ..."
```

### Phase 2
```bash
pytest tests/test_sqlalchemy_loader.py -v
```

### Phase 3
```bash
pytest tests/test_migration_parallel.py -v
```

### Phase 4
```bash
python scripts/migrate_to_sqlalchemy.py --dry-run
python scripts/migrate_to_sqlalchemy.py --execute
```

---

## 🎯 Current Status Query

```bash
# Full status
cat docs/dlt-to-sqlalchemy-migration/PROGRESS.md

# Quick check
grep "Status:" docs/dlt-to-sqlalchemy-migration/PROGRESS.md

# Check specific phase
grep "Phase 1" docs/dlt-to-sqlalchemy-migration/PROGRESS.md
```

---

## 🚀 Execution Flow

```
Start → Check PROGRESS.md → Run /phase1-foundation
  ↓
Phase 1 Complete? → Run /phase2-implementation
  ↓
Phase 2 Complete? → Run /phase3-validation
  ↓
Phase 3 Complete? → Run /phase4-migration
  ↓
Phase 4 Complete? → MIGRATION SUCCESS! 🎉
```

---

## 💡 Tips

1. **Always check PROGRESS.md first**
2. **One phase at a time** (no skipping)
3. **Validate deliverables** after each phase
4. **Keep workspaces clean** (auto-cleaned after phase)
5. **Backup before Phase 4** (automatic)
6. **Test rollback** before executing migration

---

## 📞 Need Help?

- **Execution Guide**: `docs/dlt-to-sqlalchemy-migration/EXECUTION-GUIDE.md`
- **Phase Details**: `docs/dlt-to-sqlalchemy-migration/01-tdd-phases-overview.md`
- **Progress Status**: `docs/dlt-to-sqlalchemy-migration/PROGRESS.md`
- **Rollback Plan**: `docs/dlt-to-sqlalchemy-migration/06-rollback-plan.md`
