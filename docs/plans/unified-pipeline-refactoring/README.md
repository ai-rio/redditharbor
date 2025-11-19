# Unified Pipeline Refactoring - Master Plan

**Version**: 2.0
**Status**: 🟡 In Planning
**Created**: 2025-11-19
**Timeline**: 11 weeks (8-10 weeks core migration + 1 week production)
**Last Updated**: 2025-11-19

---

## 📋 Executive Summary

This directory contains the **complete, executable plan** for refactoring RedditHarbor's two competing monolithic pipelines into a unified, modular architecture that enables Next.js integration while preserving critical functionality and cost savings.

### The Problem
- **3,574 lines of duplicate code** across `batch_opportunity_scoring.py` (2,830 lines) and `dlt_trust_pipeline.py` (774 lines)
- **Competing architectures** preventing unified API exposure
- **Inconsistent feature coverage** (trust validation missing from batch, deduplication missing from API pipeline)
- **Impossible to expose as Next.js endpoints** due to monolithic structure

### The Solution
Unified modular architecture with:
- ✅ Single source of truth for each responsibility
- ✅ Configurable data sources (database OR Reddit API)
- ✅ Clean module boundaries for Next.js integration
- ✅ Preserved $3,528/year deduplication savings
- ✅ Zero-downtime migration approach

### Business Impact
- **ROI**: 124% return on investment ($205K cost → $253K annual benefit)
- **Payback Period**: 9.7 months
- **Code Reduction**: 3,574 lines eliminated
- **Development Velocity**: 50% faster on new features
- **Maintenance Savings**: 60% reduction in bug fix time

---

## 📁 Documentation Structure

```
docs/plans/unified-pipeline-refactoring/
├── README.md                          # ← You are here
├── PHASES.md                          # Quick reference table of all phases
├── phases/                            # 11 detailed phase execution plans
│   ├── phase-01-foundation.md
│   ├── phase-02-agent-restructuring.md
│   ├── phase-03-extract-utilities.md
│   ├── phase-04-extract-fetchers.md
│   ├── phase-05-extract-deduplication.md
│   ├── phase-06-extract-enrichment.md
│   ├── phase-07-extract-storage.md
│   ├── phase-08-orchestrator.md
│   ├── phase-09-fastapi-backend.md
│   ├── phase-10-nextjs-integration.md
│   └── phase-11-production-migration.md
├── implementation/                    # Deep-dive technical guides
│   ├── agent-restructuring-detailed.md
│   ├── api-specification.md
│   ├── testing-strategy.md
│   └── rollback-procedures.md
├── checklists/                        # Executable task checklists
│   ├── phase-01-checklist.md
│   ├── phase-02-checklist.md
│   └── ... (one per phase)
└── execution-logs/                    # Progress tracking (agent writes here)
    ├── phase-01-execution.md
    ├── phase-02-execution.md
    └── ... (created during execution)
```

---

## 🎯 Phase Overview & Progress

| Phase | Name | Timeline | Risk | Status | Checklist | Execution Log |
|-------|------|----------|------|--------|-----------|---------------|
| **1** | Foundation & Setup | Week 1 (Days 1-2) | 🟢 LOW | ⏸️ NOT STARTED | [Checklist](checklists/phase-01-checklist.md) | [Log](execution-logs/phase-01-execution.md) |
| **2** | Agent Tools Restructuring | Week 1-2 (Days 3-5) | 🟡 MEDIUM | ⏸️ NOT STARTED | [Checklist](checklists/phase-02-checklist.md) | [Log](execution-logs/phase-02-execution.md) |
| **3** | Extract Utilities | Week 2 (Days 6-10) | 🟢 LOW | ⏸️ NOT STARTED | [Checklist](checklists/phase-03-checklist.md) | [Log](execution-logs/phase-03-execution.md) |
| **4** | Extract Data Fetching | Week 3 | 🟡 MEDIUM | ⏸️ NOT STARTED | [Checklist](checklists/phase-04-checklist.md) | [Log](execution-logs/phase-04-execution.md) |
| **5** | Extract Deduplication | Week 4 | 🟡 MEDIUM | ⏸️ NOT STARTED | [Checklist](checklists/phase-05-checklist.md) | [Log](execution-logs/phase-05-execution.md) |
| **6** | Extract AI Enrichment | Week 5-6 | 🔴 HIGH | ⏸️ NOT STARTED | [Checklist](checklists/phase-06-checklist.md) | [Log](execution-logs/phase-06-execution.md) |
| **7** | Extract Storage Layer | Week 7 | 🔴 HIGH | ⏸️ NOT STARTED | [Checklist](checklists/phase-07-checklist.md) | [Log](execution-logs/phase-07-execution.md) |
| **8** | Create Unified Orchestrator | Week 8 | 🔴 HIGH | ⏸️ NOT STARTED | [Checklist](checklists/phase-08-checklist.md) | [Log](execution-logs/phase-08-execution.md) |
| **9** | Build FastAPI Backend | Week 9 | 🟡 MEDIUM | ⏸️ NOT STARTED | [Checklist](checklists/phase-09-checklist.md) | [Log](execution-logs/phase-09-execution.md) |
| **10** | Next.js Integration | Week 10 | 🟡 MEDIUM | ⏸️ NOT STARTED | [Checklist](checklists/phase-10-checklist.md) | [Log](execution-logs/phase-10-execution.md) |
| **11** | Production Migration | Week 11 | 🔴 HIGH | ⏸️ NOT STARTED | [Checklist](checklists/phase-11-checklist.md) | [Log](execution-logs/phase-11-execution.md) |

**Legend**:
- ⏸️ NOT STARTED
- 🏗️ IN PROGRESS
- ✅ COMPLETED
- ⚠️ BLOCKED
- ❌ FAILED

---

## 🚀 Quick Start

### For Human Developers

**Starting Phase 1:**
1. Read [Phase 1: Foundation](phases/phase-01-foundation.md)
2. Review [Phase 1 Checklist](checklists/phase-01-checklist.md)
3. Execute tasks sequentially
4. Log progress in [execution-logs/phase-01-execution.md](execution-logs/phase-01-execution.md)
5. Mark checklist items complete as you go
6. Update status in this README when phase completes

**Daily Workflow:**
```bash
# 1. Check current phase
cat docs/plans/unified-pipeline-refactoring/PHASES.md

# 2. Read phase details
cat docs/plans/unified-pipeline-refactoring/phases/phase-0X-name.md

# 3. Open checklist
cat docs/plans/unified-pipeline-refactoring/checklists/phase-0X-checklist.md

# 4. Execute tasks, update log
echo "## $(date): Starting Task 1" >> docs/plans/unified-pipeline-refactoring/execution-logs/phase-0X-execution.md

# 5. Run validation
pytest tests/ -v
```

### For AI Agents

**Sequential Execution:**
```markdown
1. Load: docs/plans/unified-pipeline-refactoring/phases/phase-01-foundation.md
2. Read: Context, Objectives, Tasks sections
3. Execute: Each task sequentially, validating after each
4. Log: Write progress to execution-logs/phase-01-execution.md
5. Validate: Complete Full Validation Checklist
6. Mark: Update checklist items as completed
7. Transition: Read "Next Phase" section, load next phase file
8. Repeat: Until all phases complete
```

**Parallel Execution (if supported):**
- Low-risk phases (1, 3) can run in parallel with planning phases
- High-risk phases (6, 7, 8) must run sequentially with full validation
- See individual phase files for parallelization guidance

---

## 📖 How to Use This Documentation

### Phase Files (`phases/phase-XX-name.md`)

Each phase file is **self-contained** and includes:
- **Context**: What was completed previously, current state
- **Objectives**: Clear goals and success criteria
- **Tasks**: Step-by-step executable tasks with validation
- **Validation Checklist**: Comprehensive validation requirements
- **Rollback Procedure**: Emergency recovery steps
- **Next Phase**: Link to continue

**Format**: ~500-1500 lines per file (LLM-friendly)

### Implementation Files (`implementation/`)

Deep-dive technical references:
- **agent-restructuring-detailed.md**: Complete guide for restructuring `agent_tools/` → `core/agents/`
- **api-specification.md**: Full FastAPI endpoint specifications
- **testing-strategy.md**: Testing approach, frameworks, coverage targets
- **rollback-procedures.md**: Consolidated emergency procedures

**Use Case**: Reference during execution for detailed technical guidance

### Checklist Files (`checklists/phase-XX-checklist.md`)

Pure task lists extracted from phase files:
- No explanatory text, just checkboxes
- Grouped by task category
- Easy to track completion
- Can be converted to GitHub Issues

**Use Case**: Daily progress tracking, standup updates

### Execution Logs (`execution-logs/phase-XX-execution.md`)

Agent-written progress logs:
- Timestamped entries
- Task completion notes
- Issues encountered
- Validation results
- Performance metrics

**Use Case**: Historical record, debugging, audit trail

---

## 🎨 Target Architecture

### Final Module Structure

```
core/
├── agents/                      # AI service implementations (NEW)
│   ├── profiler/               # EnhancedLLMProfiler
│   ├── monetization/           # MonetizationAgnoAnalyzer
│   ├── market_validation/      # MarketDataValidator
│   ├── search/                 # Jina clients
│   └── interactive/            # Interactive tools
├── pipeline/                    # Unified orchestration (NEW)
│   ├── orchestrator.py         # OpportunityPipeline class
│   ├── config.py              # Configuration management
│   └── factory.py             # Dependency injection
├── fetchers/                    # Data acquisition (NEW)
│   ├── base_fetcher.py        # Abstract interface
│   ├── database_fetcher.py    # Supabase implementation
│   ├── reddit_api_fetcher.py  # Reddit API implementation
│   └── formatters.py          # Data formatting
├── deduplication/               # Semantic deduplication (REFACTORED)
│   ├── concept_manager.py     # Business concepts
│   ├── agno_skip_logic.py     # Monetization deduplication
│   ├── profiler_skip_logic.py # AI profiling deduplication
│   └── stats_updater.py       # Statistics tracking
├── enrichment/                  # AI analysis services (NEW)
│   ├── profiler_service.py    # Profiler wrapper
│   ├── opportunity_service.py # Opportunity scoring wrapper
│   ├── monetization_service.py# Monetization wrapper
│   ├── trust_service.py       # Trust validation wrapper
│   └── market_validation_service.py # Market validation wrapper
├── storage/                     # Data persistence (NEW)
│   ├── dlt_loader.py          # Unified DLT loading
│   ├── opportunity_store.py   # Opportunity storage
│   └── profile_store.py       # AI profile storage
├── quality_filters/             # Pre-AI filtering (NEW)
│   ├── quality_scorer.py      # Quality scoring
│   └── pre_filter.py          # Pre-filter logic
└── utils/                       # Utilities (EXISTING)
    ├── core_functions_serialization.py
    └── logging.py
```

### Decommissioned Monoliths

```
scripts/archive/monoliths_20251119/  # Archived after Phase 11
├── batch_opportunity_scoring.py     # Database pipeline (2,830 lines)
└── dlt_trust_pipeline.py            # Reddit API pipeline (774 lines)
```

---

## ⚠️ Risk Management

### High-Risk Phases
- **Phase 6** (AI Enrichment): Changes to AI service integration
- **Phase 7** (Storage): Database operations and DLT loading
- **Phase 8** (Orchestrator): Integrates all components
- **Phase 11** (Production): Final cutover

### Mitigation Strategies
1. **Side-by-Side Execution**: Run new code alongside monoliths
2. **Feature Flags**: Enable/disable new features without deployment
3. **Rollback Procedures**: Every phase has emergency rollback steps
4. **Comprehensive Validation**: 90%+ test coverage requirement
5. **Progressive Rollout**: Database → API → Production cutover

### Decision Gates
Each high-risk phase requires:
- ✅ All tests passing (unit + integration)
- ✅ Performance within 10% of baseline
- ✅ Security scan clean
- ✅ Stakeholder sign-off

---

## 📊 Success Metrics

### Code Quality
- **Code Duplication**: <5% (currently ~60% between pipelines)
- **Test Coverage**: >90% (target: 95%)
- **File Size**: <500 lines per module (currently up to 2,830 lines)
- **Cyclomatic Complexity**: <10 per function

### Performance
- **Processing Time**: ≤7.0 seconds per submission (baseline: 8.5s)
- **Throughput**: ≥500 submissions/hour (baseline: 423/hr)
- **Memory Usage**: ≤400MB (baseline: 512MB)
- **Error Rate**: ≤1% (baseline: 2%)

### Business Metrics
- **Cost Savings**: Preserve $3,528/year from deduplication
- **Development Velocity**: 50% faster feature development
- **Maintenance Reduction**: 60% fewer bug fixes
- **Time to Market**: Enable Next.js web app development

---

## 🔗 Related Documentation

### Original Planning Documents (Historical)
- [Complete Unified Refactoring Guide](../../architecture/complete-unified-refactoring-guide.md) - Original comprehensive guide
- [Unified Pipeline Refactoring Plan](../../architecture/unified-pipeline-refactoring-plan.md) - Technical deep-dive
- [Next.js API Integration Guide](../../implementation/nextjs-api-integration-guide.md) - API specifications
- [Unified Pipeline Migration Strategy](../unified-pipeline-migration-strategy.md) - Original 10-phase plan

**Note**: The documents above have been consolidated and reorganized into this executable plan. Use this directory as the single source of truth.

### Architecture Documentation
- [Architecture Overview](../../architecture/README.md) - Current system architecture
- [Clean Pipeline Architecture](../../architecture/clean-pipeline-architecture.md) - Target architecture design
- [DLT Schema Documentation](../../architecture/dlt-schema-staging-root-cause-analysis.md) - DLT implementation details

### Implementation Guides
- [Testing README](../../testing/README.md) - Testing strategy and framework
- [Schema Consolidation](../../schema-consolidation/README.md) - Database schema documentation

---

## 🤝 Contributing

### For Team Members

**Before Starting Work:**
1. Check current phase status in this README
2. Read the phase file completely
3. Understand dependencies and risks
4. Review the checklist

**During Execution:**
1. Update execution log with progress
2. Mark checklist items as you complete them
3. Run validation tests frequently
4. Commit after each major task

**After Phase Completion:**
1. Complete full validation checklist
2. Update phase status in this README
3. Write phase completion summary in execution log
4. Notify team and get sign-off for high-risk phases

### For AI Agents

**Execution Protocol:**
1. Read phase file from `phases/phase-XX-name.md`
2. Parse Tasks section, execute sequentially
3. After each task, run validation steps
4. Write progress to `execution-logs/phase-XX-execution.md`
5. On failure, execute Rollback Procedure
6. On success, load next phase and continue

**Logging Format:**
```markdown
## [TIMESTAMP] Phase X - Task Y

**Status**: IN PROGRESS / COMPLETED / FAILED
**Duration**: X minutes

### Actions Taken
- Step 1 completed
- Step 2 completed
- Validation passed

### Results
- Files created: [list]
- Tests passing: X/Y
- Performance: Xms

### Issues Encountered
- [List any issues]

### Next Steps
- [What's next]
```

---

## 📞 Support & Questions

### Getting Help
1. **Phase-Specific Questions**: See individual phase files
2. **Technical Questions**: See implementation detail files
3. **Architecture Questions**: See related architecture docs
4. **Rollback Help**: See `implementation/rollback-procedures.md`

### Escalation
- **Blocking Issue**: Document in execution log, flag in standup
- **Risk Identified**: Update risk register, notify stakeholders
- **Schedule Delay**: Re-plan subsequent phases, update timeline

---

## 📝 Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 2.0 | 2025-11-19 | Complete restructure into executable plan format | AI-assisted |
| 1.0 | 2025-11-19 | Initial comprehensive documentation | AI-generated |

---

## ✅ Sign-Off

### Planning Approval
- [ ] Technical Lead
- [ ] Product Owner
- [ ] Engineering Manager
- [ ] DevOps Lead

### Phase Completion Sign-Offs
- [ ] Phase 1: Foundation
- [ ] Phase 2: Agent Restructuring
- [ ] Phase 3: Extract Utilities
- [ ] Phase 4: Extract Fetching
- [ ] Phase 5: Extract Deduplication
- [ ] Phase 6: Extract Enrichment
- [ ] Phase 7: Extract Storage
- [ ] Phase 8: Unified Orchestrator
- [ ] Phase 9: FastAPI Backend
- [ ] Phase 10: Next.js Integration
- [ ] Phase 11: Production Migration

### Final Project Sign-Off
- [ ] All phases completed
- [ ] All success metrics achieved
- [ ] Production stable for 1 week
- [ ] Documentation complete
- [ ] Knowledge transfer complete

---

**Last Updated**: 2025-11-19
**Status**: 🟡 Planning Phase
**Next Milestone**: Begin Phase 1 - Foundation & Setup
