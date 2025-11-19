# Unified Pipeline Refactoring - Complete Checklist

Track progress across all 11 phases with this comprehensive checklist.

**Status Legend**:
- [ ] Not Started
- [x] Completed
- [~] In Progress
- [!] Blocked

---

## Phase 1: Foundation & Setup

### Task 1: Create Core Module Structure
- [ ] Create `core/pipeline/` directory
- [ ] Create `core/fetchers/` directory
- [ ] Create `core/enrichment/` directory
- [ ] Create `core/storage/` directory
- [ ] Create `core/quality_filters/` directory
- [ ] All `__init__.py` files created

### Task 2: Create Abstract Base Classes
- [ ] `BaseFetcher` interface defined
- [ ] `PipelineConfig` class created
- [ ] ServiceType enum created
- [ ] All base classes importable

### Task 3: Set Up Testing Infrastructure
- [ ] `conftest.py` with shared fixtures
- [ ] `test_base_fetcher.py` created and passing
- [ ] `test_pipeline_config.py` created and passing
- [ ] Coverage reporting configured

### Task 4: Document Baseline Metrics
- [ ] Baseline metrics document created
- [ ] Performance metrics captured
- [ ] Cost metrics documented
- [ ] Target metrics defined

### Task 5: Update Documentation
- [ ] CLAUDE.md updated with new structure
- [ ] Module READMEs created
- [ ] Refactoring plan referenced

### Validation
- [ ] All directories created
- [ ] Tests passing
- [ ] Baseline documented
- [ ] Existing system unaffected

---

## Phase 2: Agent Tools Restructuring

### Task 1: Create core/agents/ Structure
- [ ] Create `core/agents/profiler/`
- [ ] Create `core/agents/monetization/`
- [ ] Create `core/agents/market_validation/`
- [ ] Create `core/agents/search/`
- [ ] Create `core/agents/interactive/`

### Task 2: Restructure Profiler Module
- [ ] Files moved to `core/agents/profiler/`
- [ ] enhanced_profiler.py <20KB
- [ ] Imports working
- [ ] Tests passing

### Task 3: Restructure Market Validation Module
- [ ] 70KB file split into 3 files
- [ ] Each file <30KB
- [ ] All functionality preserved
- [ ] Tests passing

### Task 4: Restructure Monetization Module
- [ ] 63KB file split appropriately
- [ ] Files moved to `core/agents/monetization/`
- [ ] Tests passing

### Task 5: Consolidate Search Clients
- [ ] All Jina clients moved
- [ ] Factory pattern implemented
- [ ] Tests passing

### Task 6: Move Remaining Modules
- [ ] Interactive analyzer moved
- [ ] Agno validation converter moved
- [ ] No files remain in `agent_tools/`

### Task 7: Update All Imports
- [ ] All imports updated across codebase
- [ ] No references to `agent_tools` remain
- [ ] All files parse correctly

### Task 8: Update Documentation
- [ ] CLAUDE.md updated
- [ ] Deprecation notice in `agent_tools/`
- [ ] New README in `core/agents/`

### Validation
- [ ] All files moved
- [ ] No files >30KB
- [ ] All imports working
- [ ] All tests passing

---

## Phase 3: Extract Utilities

### Task 1: Extract Sector Mapping
- [ ] `core/utils/sector_mapping.py` created
- [ ] Tests created
- [ ] 100% coverage
- [ ] Used in monolith

### Task 2: Extract Formatters
- [ ] `core/fetchers/formatters.py` created
- [ ] Tests created
- [ ] 100% coverage
- [ ] Used in monolith

### Task 3: Extract Quality Filters
- [ ] `core/quality_filters/quality_scorer.py` created
- [ ] `core/quality_filters/pre_filter.py` created
- [ ] Tests created
- [ ] 100% coverage

### Task 4: Extract Trust Converters
- [ ] `core/enrichment/trust_converters.py` created
- [ ] Tests created
- [ ] 100% coverage

### Validation
- [ ] All utilities extracted
- [ ] 100% test coverage
- [ ] Both monoliths functional
- [ ] Side-by-side operation confirmed

---

## Phase 4: Extract Data Fetching Layer

### Task 1: Create BaseFetcher Interface
- [ ] `base_fetcher.py` enhanced
- [ ] Additional methods added
- [ ] Interface complete

### Task 2: Extract DatabaseFetcher
- [ ] `database_fetcher.py` created
- [ ] Tests created
- [ ] Used in batch pipeline

### Task 3: Extract RedditAPIFetcher
- [ ] `reddit_api_fetcher.py` created
- [ ] Tests created
- [ ] Used in DLT pipeline

### Task 4: Create Tests
- [ ] DatabaseFetcher tests passing
- [ ] RedditAPIFetcher tests passing
- [ ] Coverage >90%

### Validation
- [ ] Both fetchers return identical format
- [ ] Both monoliths using new fetchers
- [ ] All tests passing
- [ ] Deduplication integration preserved

---

## Phase 5: Extract Deduplication System

### Task 1: Extract Business Concept Manager
- [ ] `concept_manager.py` created
- [ ] Tests created
- [ ] Integrated with pipelines

### Task 2: Extract Agno Skip Logic
- [ ] `agno_skip_logic.py` created
- [ ] Tests created
- [ ] Statistics tracking working

### Task 3: Extract Profiler Skip Logic
- [ ] `profiler_skip_logic.py` created
- [ ] Tests created
- [ ] Copy logic working

### Task 4: Extract Statistics Updater
- [ ] `stats_updater.py` created
- [ ] Cost tracking accurate
- [ ] Savings validated

### Validation
- [ ] All deduplication extracted
- [ ] $3,528/year savings preserved
- [ ] Skip logic working both sources
- [ ] Business concepts unified

---

## Phase 6: Extract AI Enrichment Services

### Task 1: Create Base Service Interface
- [ ] `base_service.py` created
- [ ] Abstract methods defined
- [ ] Statistics tracking included

### Task 2: Create ProfilerService
- [ ] `profiler_service.py` created
- [ ] Deduplication integrated
- [ ] Tests passing

### Task 3: Create Other Services
- [ ] `opportunity_service.py` created
- [ ] `monetization_service.py` created
- [ ] `trust_service.py` created
- [ ] `market_validation_service.py` created

### Task 4: Integration Testing
- [ ] All services tested with real data
- [ ] Deduplication working
- [ ] Performance validated

### Task 5: Side-by-Side Validation
- [ ] 100 submissions compared
- [ ] Results identical to monoliths
- [ ] No discrepancies found

### Validation
- [ ] All 5 services created
- [ ] Deduplication working
- [ ] Identical results to monoliths
- [ ] Performance within 10%

---

## Phase 7: Extract Storage Layer

### Task 1: Create Unified DLT Loader
- [ ] `dlt_loader.py` created
- [ ] Generic load() method working
- [ ] Schema evolution supported

### Task 2: Create Storage Services
- [ ] `opportunity_store.py` created
- [ ] `profile_store.py` created
- [ ] `hybrid_store.py` created

### Task 3: Schema Migration Testing
- [ ] Add column test passing
- [ ] Merge disposition test passing
- [ ] No duplicates created

### Validation
- [ ] Unified DLT loading working
- [ ] No duplicate records
- [ ] Schema evolution working
- [ ] All tables populated correctly

---

## Phase 8: Create Unified Orchestrator

### Task 1: Create OpportunityPipeline Class
- [ ] `orchestrator.py` created
- [ ] All services integrated
- [ ] Configuration working

### Task 2: Service Container
- [ ] `factory.py` created
- [ ] Dependency injection working
- [ ] Services initialized correctly

### Task 3: Side-by-Side Validation
- [ ] 100 submissions compared
- [ ] Results byte-for-byte identical
- [ ] Validation script passing

### Validation
- [ ] OpportunityPipeline replaces monoliths
- [ ] Identical results validated
- [ ] All service combinations work
- [ ] Performance within 5%

---

## Phase 9: Build FastAPI Backend

### Task 1: Create FastAPI Application
- [ ] `api/main.py` created
- [ ] All endpoints implemented
- [ ] CORS configured

### Task 2: Add Authentication & Rate Limiting
- [ ] API key auth working
- [ ] Rate limiting configured
- [ ] Validation working

### Task 3: API Documentation
- [ ] OpenAPI spec complete
- [ ] Swagger UI accessible
- [ ] Examples provided

### Task 4: Docker Deployment
- [ ] Dockerfile created
- [ ] docker-compose.yml configured
- [ ] Containers running

### Validation
- [ ] All endpoints tested
- [ ] Authentication working
- [ ] Rate limiting functional
- [ ] Documentation complete

---

## Phase 10: Create TypeScript SDK

### Task 1: Generate TypeScript Types
- [ ] `sdk/types/api.ts` created
- [ ] All request types defined
- [ ] All response types defined

### Task 2: Create API Client
- [ ] `reddit-harbor-client.ts` created
- [ ] All endpoints wrapped
- [ ] Type safety validated

### Task 3: Create Integration Examples
- [ ] Next.js integration guide created
- [ ] API route example provided
- [ ] Server component example provided
- [ ] Client component example provided

### Task 4: Package for Distribution
- [ ] `package.json` created
- [ ] TypeScript build working
- [ ] README complete

### Validation
- [ ] TypeScript types accurate
- [ ] Client implements all endpoints
- [ ] Test Next.js project works
- [ ] Documentation complete

---

## Phase 11: Production Migration

### Task 1: Pre-Production Validation
- [ ] Complete test suite passing (>90% coverage)
- [ ] Side-by-side comparison 100% match
- [ ] Performance benchmarks met
- [ ] Load testing passed
- [ ] Cost validation confirmed

### Task 2: Production Deployment
- [ ] Blue-green deployment complete
- [ ] Parallel operation (24 hours) successful
- [ ] Monitoring and alerting active
- [ ] Gradual traffic shift completed
- [ ] Zero errors during cutover

### Task 3: Switch Over
- [ ] Final validation passed
- [ ] Database backed up
- [ ] Cron jobs updated
- [ ] Old monoliths stopped
- [ ] 2-hour monitoring complete

### Task 4: Decommission Monoliths
- [ ] Archive directory created
- [ ] Scripts moved to archive
- [ ] Archive README created
- [ ] Documentation references updated
- [ ] Git committed

### Task 5: Post-Migration Validation
- [ ] Day 1 validation passed
- [ ] Day 3 validation passed
- [ ] Week 1 validation passed
- [ ] All success metrics achieved

### Task 6: Team Training
- [ ] Architecture overview session complete
- [ ] Development workflow session complete
- [ ] Operations session complete
- [ ] API usage session complete
- [ ] Documentation handoff complete

### Final Validation
- [ ] Production stable for 1 week
- [ ] All success metrics achieved:
  - [ ] Code reduction: 3,574 lines
  - [ ] Processing time: ≤7.0s
  - [ ] Throughput: ≥500/hr
  - [ ] Error rate: ≤1%
  - [ ] Cost savings: $3,528/year preserved
  - [ ] Test coverage: >90%

### Final Sign-Off
- [ ] Technical Lead approval
- [ ] Product Owner approval
- [ ] Engineering Manager approval
- [ ] Stakeholder confirmation

---

## Overall Progress

**Phase Completion**:
- [ ] Phase 1: Foundation & Setup
- [ ] Phase 2: Agent Tools Restructuring
- [ ] Phase 3: Extract Utilities
- [ ] Phase 4: Extract Data Fetching Layer
- [ ] Phase 5: Extract Deduplication System
- [ ] Phase 6: Extract AI Enrichment Services
- [ ] Phase 7: Extract Storage Layer
- [ ] Phase 8: Create Unified Orchestrator
- [ ] Phase 9: Build FastAPI Backend
- [ ] Phase 10: Create TypeScript SDK
- [ ] Phase 11: Production Migration

**Milestones**:
- [ ] Foundation Complete (Phases 1-3)
- [ ] Core Extraction Complete (Phases 4-5)
- [ ] Services Complete (Phases 6-7)
- [ ] Orchestration Complete (Phase 8)
- [ ] API Layer Complete (Phases 9-10)
- [ ] Production Cutover Complete (Phase 11)

**Final Status**: ⏸️ NOT STARTED

---

**Last Updated**: 2025-11-19
**Document Version**: 2.0.0

[← Back to Master Plan](../README.md)
