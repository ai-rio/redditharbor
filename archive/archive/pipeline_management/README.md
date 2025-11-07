# Pipeline Management Scripts

This directory contains scripts that managed the DLT integration and traffic cutover process. These scripts orchestrated the transition from legacy data collection to the DLT-based pipeline.

## Scripts

### dlt_opportunity_pipeline.py
- **Purpose:** DLT-based opportunity discovery pipeline
- **Status:** Archived after integration into production collectors
- **Reason:** Functionality merged into `automated_opportunity_collector.py`
- **Context:** Prototype for DLT opportunity detection, now production-ready

### dlt_traffic_cuttover.py
- **Purpose:** Manages traffic cutover from 0% → 50% → 100% DLT
- **Status:** Archived after 100% cutover completion
- **Reason:** Cutover complete (Week 2 Day 12), no longer needed
- **Context:** Orchestrated gradual migration with dual-write validation

### run_monetizable_collection.py
- **Purpose:** Collection orchestrator for monetizable opportunities
- **Status:** Archived - replaced by automated collector
- **Reason:** Superseded by `automated_opportunity_collector.py` with enhanced features
- **Context:** Earlier implementation without automated scheduling

## Migration Timeline

**Week 2 Days 11-12 (Nov 7, 2025):**
- ✅ DLT traffic cutover: 0% → 50% → 100%
- ✅ Dual-write validation successful
- ✅ Legacy pipeline decommissioned
- ✅ Full production on DLT infrastructure

## Production Replacement

| Archived Script | Production Replacement |
|----------------|----------------------|
| `dlt_opportunity_pipeline.py` | `automated_opportunity_collector.py` |
| `dlt_traffic_cuttover.py` | No longer needed (cutover complete) |
| `run_monetizable_collection.py` | `automated_opportunity_collector.py` |

## Architecture Notes

These scripts demonstrate:
- **Gradual cutover pattern:** 0% → 50% → 100% with validation
- **Dual-write strategy:** Running both pipelines during transition
- **Pipeline orchestration:** Coordinating multiple data collection processes
- **Integration testing:** Validating new infrastructure before full cutover

## Usage

Archived because migration is complete. Preserved for:
- Reference for future migrations
- Understanding cutover strategy
- Historical record of DLT integration

To reactivate for reference:
```bash
cp /home/carlos/projects/redditharbor/archive/archive/pipeline_management/[script_name] /home/carlos/projects/redditharbor/scripts/
```
