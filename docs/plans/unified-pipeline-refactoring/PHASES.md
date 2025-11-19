# Unified Pipeline Refactoring - Phase Quick Reference

**Quick navigation and overview of all 11 phases**

---

## Phase Summary Table

| # | Phase Name | Week | Days | Risk | Duration | Key Deliverables | Dependencies |
|---|------------|------|------|------|----------|------------------|--------------|
| **1** | [Foundation & Setup](phases/phase-01-foundation.md) | 1 | 1-2 | 🟢 | 2 days | Module structure, testing infrastructure | None |
| **2** | [Agent Tools Restructuring](phases/phase-02-agent-restructuring.md) | 1-2 | 3-5 | 🟡 | 3 days | `core/agents/` modules, 70KB files split | Phase 1 |
| **3** | [Extract Utilities](phases/phase-03-extract-utilities.md) | 2 | 6-10 | 🟢 | 5 days | Standalone utilities, formatters | Phase 2 |
| **4** | [Extract Data Fetching](phases/phase-04-extract-fetchers.md) | 3 | - | 🟡 | 5 days | `core/fetchers/` with DB + API sources | Phase 3 |
| **5** | [Extract Deduplication](phases/phase-05-extract-deduplication.md) | 4 | - | 🟡 | 5 days | `core/deduplication/` modules | Phase 4 |
| **6** | [Extract AI Enrichment](phases/phase-06-extract-enrichment.md) | 5-6 | - | 🔴 | 8 days | All AI service wrappers in `core/enrichment/` | Phase 5 |
| **7** | [Extract Storage Layer](phases/phase-07-extract-storage.md) | 7 | - | 🔴 | 5 days | Unified DLT loader, storage services | Phase 6 |
| **8** | [Create Unified Orchestrator](phases/phase-08-orchestrator.md) | 8 | - | 🔴 | 5 days | `OpportunityPipeline` class, side-by-side validation | Phase 7 |
| **9** | [Build FastAPI Backend](phases/phase-09-fastapi-backend.md) | 9 | - | 🟡 | 5 days | Complete API with all endpoints | Phase 8 |
| **10** | [Next.js Integration](phases/phase-10-nextjs-integration.md) | 10 | - | 🟡 | 5 days | Next.js API routes, frontend components | Phase 9 |
| **11** | [Production Migration](phases/phase-11-production-migration.md) | 11 | - | 🔴 | 3 days | Production cutover, monolith decommission | Phase 10 |

**Total Duration**: 8-11 weeks (51 days + 10 days buffer)

---

## Phase Details

### Phase 1: Foundation & Setup 🟢 LOW RISK
**Week 1, Days 1-2 (2 days)**

**What**: Create complete modular directory structure and testing infrastructure

**Key Tasks**:
- Create all new directories under `core/`
- Add `__init__.py` files with proper exports
- Establish abstract base classes
- Set up comprehensive test suites
- Configure CI/CD pipeline checks

**Deliverables**:
- ✅ Complete modular directory structure
- ✅ Test infrastructure with CI/CD integration
- ✅ Baseline performance metrics

**Why Critical**: Foundation for all subsequent work

**Read More**: [phases/phase-01-foundation.md](phases/phase-01-foundation.md)

---

### Phase 2: Agent Tools Restructuring 🟡 MEDIUM RISK
**Week 1-2, Days 3-5 (3 days)**

**What**: Restructure `agent_tools/` → `core/agents/` and break up 70KB+ files

**Key Tasks**:
- Move profiler files (37KB) → `core/agents/profiler/`
- Split market validation (70KB) → `core/agents/market_validation/`
- Split monetization (63KB) → `core/agents/monetization/`
- Consolidate Jina clients → `core/agents/search/`
- Update all imports across codebase

**Deliverables**:
- ✅ All files moved to `core/agents/`
- ✅ No files >30KB
- ✅ All imports updated
- ✅ All tests passing

**Why Critical**: Establishes clean import patterns for entire project, AI services are core dependencies

**Read More**: [phases/phase-02-agent-restructuring.md](phases/phase-02-agent-restructuring.md)

---

### Phase 3: Extract Utilities 🟢 LOW RISK
**Week 2, Days 6-10 (5 days)**

**What**: Extract standalone utility functions with no side effects

**Key Tasks**:
- Extract `map_subreddit_to_sector()` → `core/utils/sector_mapping.py`
- Extract `format_submission_for_agent()` → `core/fetchers/formatters.py`
- Extract quality scoring → `core/quality_filters/quality_scorer.py`
- Extract pre-filter logic → `core/quality_filters/pre_filter.py`
- Extract trust score converters → `core/enrichment/trust_service.py`

**Deliverables**:
- ✅ All utilities extracted and tested
- ✅ 100% test coverage for extracted functions
- ✅ Side-by-side operation with monoliths

**Why Critical**: Immediate reusability, easy to test, zero dependencies

**Read More**: [phases/phase-03-extract-utilities.md](phases/phase-03-extract-utilities.md)

---

### Phase 4: Extract Data Fetching Layer 🟡 MEDIUM RISK
**Week 3 (5 days)**

**What**: Create abstract fetcher interface with database and Reddit API implementations

**Key Tasks**:
- Create `BaseFetcher` abstract class
- Extract `DatabaseFetcher` from batch pipeline (130+ lines)
- Extract `RedditAPIFetcher` from DLT pipeline (35+ lines)
- Update both monoliths to use new fetchers
- Integration test both data sources

**Deliverables**:
- ✅ `core/fetchers/base_fetcher.py` - Abstract interface
- ✅ `core/fetchers/database_fetcher.py` - Supabase implementation
- ✅ `core/fetchers/reddit_api_fetcher.py` - Reddit API implementation
- ✅ Both fetchers return identical data structures

**Why Critical**: Single interface for both data sources, core data acquisition logic

**Read More**: [phases/phase-04-extract-fetchers.md](phases/phase-04-extract-fetchers.md)

---

### Phase 5: Extract Deduplication System 🟡 MEDIUM RISK
**Week 4 (5 days)**

**What**: Extract semantic deduplication logic that saves $3,528/year

**Key Tasks**:
- Extract Agno skip logic (should_run + copy + stats)
- Extract Profiler skip logic (should_run + copy + stats)
- Create `BusinessConceptManager` for unified concept operations
- Test deduplication with real data

**Deliverables**:
- ✅ `core/deduplication/agno_skip_logic.py`
- ✅ `core/deduplication/profiler_skip_logic.py`
- ✅ `core/deduplication/concept_manager.py`
- ✅ Deduplication savings preserved ($3,528/year)

**Why Critical**: Preserves cost savings, enables deduplication for both pipelines

**Read More**: [phases/phase-05-extract-deduplication.md](phases/phase-05-extract-deduplication.md)

---

### Phase 6: Extract AI Enrichment Services 🔴 HIGH RISK
**Week 5-6 (8 days)**

**What**: Create service wrappers for all AI components with deduplication integration

**Key Tasks**:
- Create `ProfilerService` (EnhancedLLMProfiler + profiler skip)
- Create `OpportunityService` (OpportunityAnalyzerAgent)
- Create `MonetizationService` (MonetizationAgnoAnalyzer + Agno skip)
- Create `TrustService` (TrustLayerValidator)
- Create `MarketValidationService` (MarketDataValidator)
- Comprehensive integration testing

**Deliverables**:
- ✅ All AI services with deduplication integration
- ✅ Service-level configuration and error handling
- ✅ Performance within 10% of original
- ✅ All tests passing

**Why Critical**: Touches all AI components, high complexity, critical path

**Read More**: [phases/phase-06-extract-enrichment.md](phases/phase-06-extract-enrichment.md)

---

### Phase 7: Extract Storage Layer 🔴 HIGH RISK
**Week 7 (5 days)**

**What**: Create unified DLT loading logic for all storage operations

**Key Tasks**:
- Create `DLTLoader` with generic `load()` method
- Extract opportunity store logic
- Extract profile store logic
- Extract hybrid store logic
- Schema migration testing

**Deliverables**:
- ✅ Unified DLT loading infrastructure
- ✅ Individual storage services
- ✅ No duplicate records
- ✅ Schema evolution supported

**Why Critical**: Data persistence layer, high risk of data integrity issues

**Read More**: [phases/phase-07-extract-storage.md](phases/phase-07-extract-storage.md)

---

### Phase 8: Create Unified Orchestrator 🔴 HIGH RISK
**Week 8 (5 days)**

**What**: Single `OpportunityPipeline` class replacing both monoliths

**Key Tasks**:
- Implement `OpportunityPipeline` class
- Wire up all services with dependency injection
- Create `ServiceContainer` for service management
- Side-by-side testing with both monoliths
- Compare results byte-for-byte

**Deliverables**:
- ✅ `core/pipeline/orchestrator.py` - Unified pipeline
- ✅ Identical results to both monoliths
- ✅ All functionality preserved
- ✅ Performance within 5% of original

**Why Critical**: Integrates all components, final validation before API exposure

**Read More**: [phases/phase-08-orchestrator.md](phases/phase-08-orchestrator.md)

---

### Phase 9: Build FastAPI Backend 🟡 MEDIUM RISK
**Week 9 (5 days)**

**What**: Expose all services as REST API endpoints

**Key Tasks**:
- Create FastAPI application with 20+ endpoints
- Implement request validation (Pydantic models)
- Add JWT authentication and role-based access
- Add rate limiting and request validation
- API documentation (OpenAPI/Swagger)

**Deliverables**:
- ✅ FastAPI backend with all endpoints
- ✅ Authentication and validation layer
- ✅ API documentation complete
- ✅ Load testing passes

**Why Critical**: Enables Next.js integration, new component

**Read More**: [phases/phase-09-fastapi-backend.md](phases/phase-09-fastapi-backend.md)

---

### Phase 10: Next.js Integration 🟡 MEDIUM RISK
**Week 10 (5 days)**

**What**: Connect Next.js frontend to FastAPI backend

**Key Tasks**:
- Create Next.js API routes (proxies to FastAPI)
- Build TypeScript API client
- Implement WebSocket hooks for real-time updates
- Create UI components for pipeline management
- End-to-end integration testing

**Deliverables**:
- ✅ Next.js API routes functional
- ✅ Frontend components complete
- ✅ Real-time updates working
- ✅ User acceptance testing passed

**Why Critical**: Final user-facing integration, enables web application

**Read More**: [phases/phase-10-nextjs-integration.md](phases/phase-10-nextjs-integration.md)

---

### Phase 11: Production Migration 🔴 HIGH RISK
**Week 11 (3 days)**

**What**: Deploy unified pipeline, decommission monoliths

**Key Tasks**:
- Deploy unified pipeline to production
- Switch monitoring to new system
- Move monoliths to `scripts/archive/`
- Update documentation and references
- Post-migration validation (1 week monitoring)

**Deliverables**:
- ✅ Production cutover completed
- ✅ Monoliths archived and documented
- ✅ All success metrics validated
- ✅ Stakeholder sign-off received

**Why Critical**: Final cutover, production stability at risk

**Read More**: [phases/phase-11-production-migration.md](phases/phase-11-production-migration.md)

---

## Risk Heat Map

```
    Week 1    Week 2    Week 3    Week 4    Week 5-6  Week 7    Week 8    Week 9    Week 10   Week 11
┌─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬─────────┐
│ Phase 1 │ Phase 3 │ Phase 4 │ Phase 5 │ Phase 6 │ Phase 7 │ Phase 8 │ Phase 9 │ Phase10 │ Phase11 │
│   🟢    │   🟢    │   🟡    │   🟡    │   🔴    │   🔴    │   🔴    │   🟡    │   🟡    │   🔴    │
│  LOW    │  LOW    │ MEDIUM  │ MEDIUM  │  HIGH   │  HIGH   │  HIGH   │ MEDIUM  │ MEDIUM  │  HIGH   │
└─────────┴─────────┴─────────┴─────────┴─────────┴─────────┴─────────┴─────────┴─────────┴─────────┘
│ Phase 2 │
│   🟡    │
│ MEDIUM  │
└─────────┘
```

**High-Risk Phases**: 6, 7, 8, 11 (require stakeholder sign-off)

---

## Dependencies Graph

```
Phase 1 (Foundation)
    │
    └──> Phase 2 (Agent Restructuring)
            │
            └──> Phase 3 (Utilities)
                    │
                    └──> Phase 4 (Fetchers)
                            │
                            └──> Phase 5 (Deduplication)
                                    │
                                    └──> Phase 6 (Enrichment) ← Critical Path
                                            │
                                            └──> Phase 7 (Storage)
                                                    │
                                                    └──> Phase 8 (Orchestrator)
                                                            │
                                                            ├──> Phase 9 (API)
                                                            │       │
                                                            │       └──> Phase 10 (Next.js)
                                                            │               │
                                                            └───────────────┴──> Phase 11 (Production)
```

**Critical Path**: Phases 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 (all sequential)

**Possible Parallelization**:
- Phase 9 (API) can start while Phase 10 (Next.js) planning happens
- Documentation can be written in parallel throughout

---

## Quick Commands

```bash
# View specific phase
cat docs/plans/unified-pipeline-refactoring/phases/phase-01-foundation.md

# Check phase checklist
cat docs/plans/unified-pipeline-refactoring/checklists/phase-01-checklist.md

# View execution log
cat docs/plans/unified-pipeline-refactoring/execution-logs/phase-01-execution.md

# Check overall status
cat docs/plans/unified-pipeline-refactoring/README.md

# Search across all phases
grep -r "task name" docs/plans/unified-pipeline-refactoring/phases/
```

---

## Success Criteria Summary

**Code Quality**:
- ✅ 3,574 lines duplicate code eliminated
- ✅ No files >500 lines
- ✅ Test coverage >90%

**Performance**:
- ✅ Processing time ≤7.0s (baseline: 8.5s)
- ✅ Throughput ≥500/hr (baseline: 423/hr)
- ✅ Memory usage ≤400MB (baseline: 512MB)

**Business**:
- ✅ $3,528/year cost savings preserved
- ✅ 50% faster development velocity
- ✅ Next.js integration enabled

---

**Last Updated**: 2025-11-19
**Version**: 2.0
**Status**: Planning Phase

[← Back to Master Plan](README.md)
