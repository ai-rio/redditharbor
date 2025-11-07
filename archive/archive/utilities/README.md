# Utility Scripts

This directory contains utility scripts for monitoring, verification, and status checking that were used during development and cutover phases.

## Scripts

### check_cutover_status.py
- **Purpose:** Monitors DLT traffic cutover percentage (0% → 50% → 100%)
- **Status:** Archived after 100% cutover completion
- **Reason:** Cutover complete on Week 2 Day 12, monitoring no longer needed
- **Context:** Used during gradual migration from legacy to DLT pipeline

### check_database_schema.py
- **Purpose:** Validates database schema and table structures
- **Status:** Archived after schema stabilization
- **Reason:** Schema now stable and validated, functionality available via Supabase Studio
- **Alternative:** Use `supabase db diff` for schema checking

### verify_monetizable_implementation.py
- **Purpose:** Verifies monetizable opportunity detection implementation
- **Status:** Archived after implementation validation
- **Reason:** Implementation validated and production-ready, verification complete
- **Context:** Used during development of opportunity scoring pipeline

### monitor_collection.sh
- **Purpose:** Shell script for monitoring data collection processes
- **Status:** Archived - replaced by integrated monitoring
- **Reason:** Monitoring now handled by production scripts with built-in logging
- **Alternative:** Use `final_system_test.py` for comprehensive testing

## Usage

These scripts provided development and transition support. They are archived because:
1. **Cutover complete:** No longer transitioning between systems
2. **Schema stable:** Database structure finalized and documented
3. **Implementation validated:** All production features tested and verified
4. **Better alternatives:** Production scripts include superior monitoring

For similar needs:
- **Schema validation:** Use Supabase Studio or `supabase db diff`
- **Collection monitoring:** Check logs in `error_log/` directory
- **System testing:** Use `final_system_test.py`

To reactivate for reference:
```bash
cp /home/carlos/projects/redditharbor/archive/archive/utilities/[script_name] /home/carlos/projects/redditharbor/scripts/
```
