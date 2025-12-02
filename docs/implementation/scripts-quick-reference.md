# RedditHarbor Scripts Quick Reference

**Last Updated:** November 7, 2025 (Post-DLT Integration)

---

## Production Scripts (Active)

All production scripts are in: `/home/carlos/projects/redditharbor/scripts/`

### Data Collection

```bash
# Commercial subreddit data collection
python scripts/collect_commercial_data.py

# Full-scale data collection
python scripts/full_scale_collection.py

# Automated opportunity collection (scheduled)
python scripts/automated_opportunity_collector.py
```

### Analysis & Insights

```bash
# Batch opportunity scoring
python scripts/batch_opportunity_scoring.py

# Generate AI-powered insights
python scripts/generate_opportunity_insights_openrouter.py
```

### Testing & Validation

```bash
# Comprehensive system test
python scripts/final_system_test.py
```

---

## Archived Scripts (Reference Only)

All archived scripts are in: `/home/carlos/projects/redditharbor/archive/archive/`

### Reactivating Archived Scripts

```bash
# General pattern
cp /home/carlos/projects/redditharbor/archive/archive/[category]/[script_name] /home/carlos/projects/redditharbor/scripts/

# Examples
cp archive/archive/test_infrastructure/test_dlt_pipeline.py scripts/
cp archive/archive/utilities/check_database_schema.py scripts/
```

### Archive Categories

| Category | Count | Purpose |
|----------|-------|---------|
| test_infrastructure | 6 | DLT integration testing |
| utilities | 4 | Development tools |
| pipeline_management | 3 | Cutover orchestration |
| research | 3 | Legacy research framework |
| old_versions | 7 | Superseded implementations |
| hung_stuck | 5 | Performance issues |
| duplicate_tests | 7 | Redundant tests |
| fix_scripts | 3 | Resolved issues |
| demos | 3 | Examples |
| domain_research | 4 | Research examples |
| data_analysis | 6 | Old analysis |
| agent_sdk | 2 | SDK demos |
| dashboard_ui | 2 | UI components |
| other | 6 | Miscellaneous |

---

## Production Pipeline Flow

```
1. automated_opportunity_collector.py
   ↓
2. collect_commercial_data.py / full_scale_collection.py
   ↓
3. DLT Pipeline → Supabase
   ↓
4. batch_opportunity_scoring.py
   ↓
5. generate_opportunity_insights_openrouter.py
   ↓
6. Insights & Reports
```

---

## Common Tasks

### Run Full Pipeline
```bash
# Automated (scheduled)
python scripts/automated_opportunity_collector.py

# Manual
python scripts/collect_commercial_data.py
python scripts/batch_opportunity_scoring.py
python scripts/generate_opportunity_insights_openrouter.py
```

### Validate System
```bash
python scripts/final_system_test.py
```

### Check Database
```bash
# View in Supabase Studio
open http://127.0.0.1:54323

# Or use archived utility (if needed)
cp archive/archive/utilities/check_database_schema.py scripts/
python scripts/check_database_schema.py
```

---

## File Locations

| Item | Location |
|------|----------|
| Production scripts | `/home/carlos/projects/redditharbor/scripts/` |
| Archive | `/home/carlos/projects/redditharbor/archive/archive/` |
| Documentation | `/home/carlos/projects/redditharbor/docs/` |
| Error logs | `/home/carlos/projects/redditharbor/error_log/` |
| Configuration | `/home/carlos/projects/redditharbor/config/` |

---

## Documentation

| Document | Purpose |
|----------|---------|
| SCRIPTS_ORGANIZATION_SUMMARY.md | Complete organization details |
| archive/README.md | Archive overview |
| archive/archive/*/README.md | Category-specific details |
| SCRIPTS_QUICK_REFERENCE.md | This file (quick reference) |

---

## Support

**Questions?**
1. Check SCRIPTS_ORGANIZATION_SUMMARY.md for detailed information
2. Review category-specific READMEs in archive/archive/
3. Reference this quick guide for common tasks

**Need archived script?**
1. Find it in archive/archive/[category]/
2. Review its README for context
3. Copy to scripts/ if needed
4. Consider if production scripts meet your needs first

---

**Organization Date:** November 7, 2025
**DLT Integration:** 100% Complete
**Production Scripts:** 6 active
**Archived Scripts:** 72 total (19 from this cleanup)
