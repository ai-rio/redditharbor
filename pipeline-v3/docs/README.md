# RedditHarbor Pipeline v3 Documentation

<div align="center">

**Clean ELT Architecture for Reddit Data Collection and Research**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](../LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](../requirements.txt)
[![Documentation](https://img.shields.io/badge/docs-wip-yellow.svg)](./documentation-debt-analysis.md)

---

*Transforming Reddit discussions into monetizable app opportunities through clean ELT pipeline with full type safety*

</div>

## 📚 Table of Contents

- [🚀 Quick Start](#-quick-start)
- [📖 Documentation Structure](#-documentation-structure)
- [🔧 Implementation Guides](#-implementation-guides)
- [🏗️ Architecture & Design](#️-architecture--design)
- [🧩 Components & Systems](#-components--systems)
- [🎯 Guides & Tutorials](#-guides--tutorials)
- [📊 Implementation Phases](#-implementation-phases)
- [🤝 Contributing](#-contributing)

---

## 🚀 Quick Start

New to RedditHarbor Pipeline v3? Start here:

- **[Getting Started Guide](./guides/elt-pipeline-setup.md)** - Complete ELT pipeline setup and configuration
- **[ELT Architecture Overview](./architecture/elt-architecture-design.md)** - Clean Extract → Transform → Load pattern
- **[Implementation Guide](./implementation/elt-pipeline-implementation.md)** - Technical implementation details

---

## 📖 Documentation Structure

This documentation is organized into logical sections to help you find information quickly:

### Directory Overview

```
docs/
├── README.md                           # This file - navigation hub
├── api/                                # External API integrations
│   └── README.md                       # API documentation and interfaces
├── architecture/                       # System design and architecture decisions
│   ├── elt-architecture-design.md     # Clean ELT architecture overview
│   ├── filtering-architecture.md      # Dual filtering system architecture
│   ├── onlymaps-test-architecture.md  # OnlyMaps testing framework design
│   ├── v2-to-v3-migration.md          # Migration guide from v2
│   └── adr/                           # Architecture Decision Records
├── components/                         # Pipeline components documentation
│   └── README.md                       # Extract, Transform, Load layers
├── config/                             # Configuration management
│   └── README.md                       # Environment setup and API config
├── contributing/                       # Development contribution guidelines
│   └── README.md                       # Code standards and workflows
├── guides/                             # User guides and tutorials
│   └── elt-pipeline-setup.md          # Complete setup guide
├── implementation/                     # Implementation details and technical guides
│   ├── elt-pipeline-implementation.md # Full implementation guide
│   ├── IMPLEMENTATION_SUMMARY.md      # Complete implementation overview
│   ├── VALIDATION_REFACTOR_PLAN.md    # Validation system refactoring strategy
│   ├── README_ONLYMAPS_TESTS.md       # OnlyMaps testing framework
│   ├── ai-content-quality-scoring.md  # AI content quality assessment
│   ├── documentation-debt-analysis.md # Documentation gaps analysis
│   ├── pydantic-completeness-testing.md # Pydantic validation framework
│   ├── real-api-integration.md        # Real API integration details
│   └── elt-pipeline-implementation.md # ELT pipeline implementation
├── assets/                             # Visual resources and documentation assets
│   └── README.md                       # Images, diagrams, and examples
├── plans/                              # Development plans and roadmaps
├── prompts/                            # AI prompt templates and configurations
├── research/                           # Research notes and findings (NEW)
├── technical-debt/                     # Technical debt analysis and tracking
├── technical-debt-register.md          # Technical debt tracking
└── documentation-debt-analysis.md      # Documentation gap analysis
```

---

## 🔧 Implementation Guides

**Core Implementation Documentation:**

- **[ELT Pipeline Implementation Guide](./implementation/elt-pipeline-implementation.md)**
  - Complete Extract → Transform → Load pipeline
  - Pydantic model integration and type safety
  - Real API integration setup
  - Testing strategies and performance optimization

**New Implementation Documentation:**

- **[Implementation Summary](./implementation/IMPLEMENTATION_SUMMARY.md)** - Complete implementation overview and achievements
- **[Validation Refactor Plan](./implementation/VALIDATION_REFACTOR_PLAN.md)** - Detailed validation system refactoring strategy
- **[OnlyMaps Test Architecture](./implementation/README_ONLYMAPS_TESTS.md)** - Comprehensive OnlyMaps testing framework
- **[AI Content Quality Scoring](./implementation/ai-content-quality-scoring.md)** - AI-powered content quality assessment system
- **[Documentation Debt Analysis](./implementation/documentation-debt-analysis.md)** - Current documentation gaps and improvement plan
- **[Pydantic Completeness Testing](./implementation/pydantic-completeness-testing.md)** - Comprehensive Pydantic model validation framework

**API and Configuration:**

- **[API Documentation](./api/README.md)** - External service integrations
- **[Configuration Guide](./config/README.md)** - Environment setup and management

---

## 🏗️ Architecture & Design

**System Architecture and Design Decisions:**

- **[ELT Architecture Design](./architecture/elt-architecture-design.md)**
  - Clean ELT pattern vs v2 complexity
  - Type safety with Pydantic throughout
  - Performance optimization strategies

- **[Architecture Decision Records](./architecture/adr/README.md)**
  - Repository pattern implementation (ADR-001)
  - Quality validation system design (ADR-002)
  - Vector embedding strategy (ADR-003)

### 📊 ELT Architecture Diagrams

<div align="center">

```mermaid
graph LR
    subgraph 1. Extraction
        A[Reddit API] -->|Raw JSON| B{PRAW Client};
    end

    subgraph 2. Staging Layer
        B -->|Cleaned Text| C[Staging Area];
        C -.->|Deduplication| C;
        note[Resilience Checkpoint]
    end

    subgraph 3. Transformation Engine
        C -->|Batch Input| D[LLM Agent];
        D -->|Validation| E{Pydantic + Instructor};
        E -- Schema Enforced --> F((Structured Object));
    end

    subgraph 4. Supabase Storage
        F --> G{SQLAlchemy ORM};
        G -->|Transactional Write| H[(PostgreSQL)];
        G -->|Vector Write| I[(pgvector)];
    end

    style A fill:#FF4500,stroke:#333,stroke-width:2px
    style C fill:#E0E0E0,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
    style E fill:#0077B6,stroke:#333,stroke-width:2px,color:white
    style H fill:#3ECF8E,stroke:#333,stroke-width:2px,color:white
    style I fill:#3ECF8E,stroke:#333,stroke-width:2px,color:white
```

*Pipeline v3 Clean ELT Architecture with Staging Layer*

</div>

---

## 🧩 Pipeline Components

**Core Pipeline Components and Systems:**

### ELT Pipeline Layers
- **[Component Documentation](./components/README.md)** - Complete overview of all pipeline components
  - Extract Layer - Reddit API and LLM data extraction
  - Transform Layer - Pydantic validation and data transformation
  - Load Layer - Database storage with SQLAlchemy

### Core Systems
- **Pydantic Models** - Type-safe data validation throughout pipeline (see `models/` directory)
- **Configuration Management** - Environment-based configuration (see setup guide)
- **Error Handling & Logging** - Comprehensive error management (see implementation guide)

*Detailed component architecture and implementation available in the [Component Documentation](./components/README.md)*

---

## 🎯 Guides & Tutorials

**Step-by-Step Guides and Tutorials:**

- **[ELT Pipeline Setup Guide](./guides/elt-pipeline-setup.md)**
  - Complete pipeline initialization
  - API credential configuration
  - Database setup and migration
  - Troubleshooting and diagnostics

---

## 📊 Implementation Phases

### Phase Status Overview

| Phase | Status | Completion | Tests | Environment |
|-------|--------|------------|-------|-------------|
| **Phase 1** | ✅ Complete | Factory Pattern Integration | 16/16 passing | `.venv` required |
| **Phase 2** | ⚠️ Needs Re-verification | Validation System Enhancement | 15/16 claimed* | `.venv` required |
| **Phase 3** | ✅ **COMPLETE** | **Jina Market Research Integration** | **49/49 passing** | **`.venv` required** |

*Phase 2 test results need re-verification with correct environment

### 🔧 Environment Requirements

**CRITICAL:** All testing and development MUST use the pipeline-v3 local virtual environment:

```bash
# CORRECT - Use local pipeline-v3 environment
cd /home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3
source .venv/bin/activate  # ✅ REQUIRED

# WRONG - Do NOT use parent directory environment
source ../.venv/bin/activate  # ❌ WILL CAUSE TEST FAILURES
```

**Why This Matters:**
- Phase 3 audit discrepancies were caused by using wrong virtual environment
- Local `.venv` contains Phase 3-specific dependencies not in parent environment
- All test claims validated only with correct environment activation

### Phase 3: Jina Market Research Integration ✅ COMPLETE

**Status: PRODUCTION READY** - All requirements verified with corrected audit

#### ✅ Verified Results (Using Correct Environment)
```bash
# Verify Phase 3 completion
source .venv/bin/activate
python -m pytest tests/transform/test_market_research_agent_tdd.py tests/transform/test_jina_client.py -v

# Expected: 49 passed, 0 failed (100% success rate)
# TDD Tests: 36/36 passing ✅
# Jina Client Tests: 13/13 passing ✅
```

#### 🎯 Phase 3 Deliverables Completed
- **✅ Jina Client Architecture** - Web search, content extraction, LLM-powered analysis
- **✅ Advanced Caching Layer** - Redis with memory fallback and TTL management
- **✅ Market Research Agent** - Competitor analysis, market sizing, launch tracking
- **✅ Validation Evidence System** - Pydantic models with quality scoring
- **✅ Production Infrastructure** - PrometheusMetrics, HealthCheckEndpoint, monitoring
- **✅ Comprehensive Testing** - 100% test success rate with TDD methodology

#### 📊 Production Readiness
- **✅ Monitoring:** Prometheus integration with comprehensive metrics
- **✅ Health Checks:** `/health`, `/ready`, `/live` endpoints operational
- **✅ Cost Tracking:** Detailed API usage monitoring and budget controls
- **✅ Error Handling:** Circuit breakers, rate limiting, resilient architecture
- **✅ Documentation:** Complete API documentation and operational guides

#### 🔍 QA Verification
- **✅ QA Checkpoint Report:** All claims verified as accurate
- **✅ Audit Correction:** Previous audit errors identified and corrected
- **✅ Test Environment:** Clear requirements documented to prevent discrepancies
- **✅ Production Deployment:** Ready for immediate deployment

*Note: Additional guides (Type Safety, Performance Optimization) are planned but not yet implemented*

---

## 🤝 Contributing

We welcome contributions to RedditHarbor Pipeline v3!

### Code Quality Standards

- **Ruff Linting**: Run `ruff check . && ruff format .` before commits
- **Testing**: Add comprehensive tests for new features (pytest)
- **Type Safety**: Use type hints and Pydantic models throughout
- **Documentation**: Update relevant documentation for new features

### Pre-Development Environment Verification

**MANDATORY:** Before any development or testing, verify your environment:

```bash
# 1. Verify correct directory
pwd
# Must be: /home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3

# 2. Activate correct virtual environment
source .venv/bin/activate
# NOT: source ../.venv/bin/activate

# 3. Verify environment activation
echo $VIRTUAL_ENV
# Must include: pipeline-v3/.venv

# 4. Verify Python and pytest
python --version  # Should be Python 3.12.3
python -m pytest --version  # Should show pytest version

# 5. Test environment with single test
python -m pytest tests/transform/test_market_research_agent_tdd.py::TestMarketResearchAgentTDD::TestValidationScoreCalculation::test_high_validation_score_with_all_evidence -v
```

**If tests fail, check environment first - DO NOT assume code issues.**

### Quick Contribution Checklist

- [ ] **Environment Verified:** Used `.venv` not `../.venv`
- [ ] Follow RedditHarbor code quality standards (ruff required)
- [ ] Add comprehensive tests for new features (pytest)
- [ ] Update relevant documentation
- [ ] Ensure all CI checks pass with correct environment
- [ ] Submit pull request with clear description

**Environment Verification Required:** All contributions must use pipeline-v3 local environment to prevent false test failures.

*Note: Detailed contributing guidelines are planned but not yet implemented*

---

## 🔍 Additional Resources

### Related Documentation

- **[Main Project README](../README.md)** - Overall project information
- **[Technical Debt Register](./technical-debt-register.md)** - Active development tracking
- **[Documentation Debt Analysis](./implementation/documentation-debt-analysis.md)** - Documentation gap analysis

### External Resources

- **[Reddit API Documentation](https://www.reddit.com/dev/api/)** - Official Reddit API documentation
- **[Supabase Documentation](https://supabase.com/docs)** - Database and storage platform docs
- **[Pydantic Documentation](https://pydantic-docs.helpmanual.io/)** - Data validation library docs
- **[SQLAlchemy Documentation](https://docs.sqlalchemy.org/)** - Python ORM framework docs

---

## 📞 Support & Contact

Need help or have questions?

- 📧 **Documentation Issues**: Create an issue in the repository
- 💬 **General Questions**: Check our discussions section
- 🐛 **Bug Reports**: Submit detailed bug reports with reproduction steps
- 🚀 **Feature Requests**: Submit feature requests with use case details

---

<div align="center">

**Built with ❤️ by the RedditHarbor Team**

*Pipeline v3: Clean ELT Architecture with Full Type Safety*

*Last updated: November 2025*

[![CueTimer Brand](https://img.shields.io/badge/Powered%20By-CueTimer-FF6B35.svg)](https://cuetimer.com)

</div>