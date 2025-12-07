# RedditHarbor Repository Index

**Generated:** 2025-12-07
**Version:** 1.0.0
**Status:** Production Ready (Phase 4 Complete)

## 🏗️ Repository Overview

RedditHarbor is a comprehensive Reddit data collection and research platform built with Python that transforms Reddit discussions into research-ready datasets through automated collection and analysis tools with AI-agent friendly architecture and multiple research templates.

### 📊 Project Status
- **Phase 1:** ✅ Foundation & Core Infrastructure (COMPLETED)
- **Phase 2:** ✅ Data Collection & Processing (COMPLETED)
- **Phase 3:** ✅ AI Agent Wrappers (COMPLETED)
- **Phase 4:** ✅ Trust Validation System (COMPLETED)
- **Phase 5:** 🔄 Integration & Production Deployment (PLANNING)

## 📁 Directory Structure

```
redditharbor-core-functions-fix/
├── 📋 core/                          # Core functionality and business logic
│   ├── __init__.py                   # Core package exports
│   ├── setup.py                      # Reddit/Supabase setup utilities
│   ├── collection.py                 # Legacy collection (shim)
│   ├── templates.py                  # Legacy templates (shim)
│   ├── activity_validation.py        # Activity validation logic
│   ├── clients.py                    # HTTP client configuration
│   ├── cost_tracking_error_handler.py # Error handling for cost tracking
│   ├── dlt_reddit_source.py          # DLT Reddit data source
│   ├── dlt_collection.py             # DLT collection wrapper
│   ├── dlt_app_opportunities.py      # DLT opportunities processing
│   ├── dlt_cost_tracking.py          # DLT cost tracking
│   ├── http_client_config.py         # HTTP client configuration
│   ├── lead_extractor.py             # Lead extraction functionality
│   ├── pipeline_v3.py                # Pipeline v3 implementation
│   ├── pipeline_v3_simple.py         # Simplified pipeline v3
│   ├── verify_instrumentation.py     # Instrumentation verification
│   ├── 📂 agents/                    # AI agent frameworks
│   │   ├── __init__.py
│   │   ├── 📂 monetization/          # Monetization analysis agents
│   │   │   ├── __init__.py
│   │   │   ├── agno_analyzer.py      # Agno-based monetization analyzer
│   │   │   ├── factory.py            # Monetization agent factory
│   │   │   ├── llm_analyzer.py       # LLM-based analyzer
│   │   │   └── validation_converter.py # Validation converter
│   │   ├── 📂 market_validation/     # Market validation agents
│   │   │   ├── __init__.py
│   │   │   ├── integration.py        # Integration logic
│   │   │   ├── persistence.py        # Data persistence
│   │   │   └── validator.py          # Market validator
│   │   ├── 📂 interactive/           # Interactive analysis agents
│   │   │   ├── __init__.py
│   │   │   ├── analyzer.py           # Interactive analyzer
│   │   │   └── opportunity_analyzer.py # Opportunity analyzer
│   │   ├── 📂 profiler/              # Profiling agents
│   │   │   ├── __init__.py
│   │   │   ├── base_profiler.py      # Base profiler
│   │   │   └── enhanced_profiler.py  # Enhanced profiler
│   │   └── 📂 search/                # Search clients
│   │       ├── __init__.py
│   │       ├── hybrid_client.py      # Hybrid search client
│   │       ├── mcp_client.py         # MCP client
│   │       ├── mcp_client_simple.py  # Simplified MCP client
│   │       └── reader_client.py      # Reader client
│   ├── 📂 db/                        # Database models and session
│   │   ├── __init__.py
│   │   ├── base.py                   # Database base
│   │   ├── models.py                 # Database models
│   │   └── session.py                # Database session
│   ├── 📂 dlt/                       # DLT (Data Load Tool) components
│   │   ├── __init__.py
│   │   ├── app_opportunities.py      # App opportunities DLT
│   │   ├── collection.py             # DLT collection
│   │   ├── constraint_validator.py   # Constraint validation
│   │   ├── constants.py              # DLT constants
│   │   ├── cost_tracking.py          # Cost tracking DLT
│   │   ├── dataset_constraints.py    # Dataset constraints
│   │   ├── normalize_hooks.py        # Data normalization hooks
│   │   ├── reddit_source.py          # Reddit DLT source
│   │   ├── schemas/                  # DLT schemas
│   │   │   └── app_opportunities_schema.py
│   │   └── score_calculator.py       # Score calculation
│   ├── 📂 deduplication/             # Data deduplication
│   │   ├── __init__.py
│   │   ├── agno_skip_logic.py        # Agno skip logic
│   │   ├── concept_manager.py        # Concept management
│   │   ├── profiler_skip_logic.py    # Profiler skip logic
│   │   ├── simple_deduplicator.py    # Simple deduplicator
│   │   └── stats_updater.py          # Statistics updater
│   ├── 📂 enrichment/                # Data enrichment services
│   │   ├── __init__.py
│   │   ├── activity_validation.py    # Activity validation
│   │   ├── base_service.py           # Base enrichment service
│   │   ├── lead_extractor.py         # Lead extraction
│   │   ├── market_validation_service.py # Market validation
│   │   ├── monetization_service.py   # Monetization service
│   │   ├── opportunity_service.py    # Opportunity service
│   │   ├── profiler_service.py       # Profiler service
│   │   ├── trust_converters.py       # Trust data converters
│   │   ├── trust_service.py          # Trust scoring service
│   │   └── validation.py             # Data validation
│   ├── 📂 fetchers/                  # Data fetching components
│   │   ├── __init__.py
│   │   ├── base_fetcher.py           # Base fetcher
│   │   ├── collection.py             # Collection logic
│   │   ├── database_fetcher.py       # Database fetching
│   │   ├── formatters.py             # Data formatters
│   │   └── reddit_api_fetcher.py     # Reddit API fetching
│   ├── 📂 pipeline/                  # Pipeline orchestration
│   │   ├── __init__.py
│   │   ├── config.py                 # Pipeline configuration
│   │   ├── factory.py                # Pipeline factory
│   │   ├── orchestrator.py           # Pipeline orchestration
│   │   └── templates.py              # Pipeline templates
│   ├── 📂 quality_filters/           # Quality filtering
│   │   ├── __init__.py
│   │   ├── pre_filter.py             # Pre-filtering
│   │   ├── quality_scorer.py         # Quality scoring
│   │   └── thresholds.py             # Filter thresholds
│   ├── 📂 reddit/                    # Reddit-specific components
│   │   └── supabase_collection.py    # Reddit-Supabase collection
│   ├── 📂 reporting/                 # Reporting and metrics
│   │   ├── __init__.py
│   │   ├── metrics_calculator.py     # Metrics calculation
│   │   └── summary_generator.py      # Summary generation
│   ├── 📂 storage/                   # Data storage
│   │   ├── __init__.py
│   │   ├── dlt_loader.py             # DLT loading
│   │   ├── enhanced_hybrid_store.py  # Enhanced hybrid storage
│   │   ├── hybrid_store.py           # Hybrid storage
│   │   ├── opportunity_store.py      # Opportunity storage
│   │   └── profile_store.py          # Profile storage
│   ├── 📂 trust/                     # Trust validation system
│   │   ├── __init__.py
│   │   ├── config.py                 # Trust configuration
│   │   ├── legacy_layer.py           # Legacy trust layer
│   │   ├── models.py                 # Trust models
│   │   ├── repository.py             # Trust repository
│   │   └── validation.py             # Trust validation
│   └── 📂 utils/                     # Utility functions
│       ├── __init__.py
│       ├── core_functions_serialization.py # Core functions serialization
│       ├── cost_tracking_error_handler.py # Cost tracking error handler
│       └── http_client_config.py     # HTTP client configuration
├── ⚙️ config/                        # Configuration management
│   ├── __init__.py                   # Package initialization
│   ├── settings.py                   # Core configuration settings
│   ├── dlt_settings.py               # DLT-specific settings
│   └── dlt.toml                      # DLT configuration
├── 🔧 scripts/                       # Research workflows and tools
│   ├── README.md                     # Scripts documentation
│   ├── apply_migration.py            # Migration application
│   ├── check_db_columns.py           # Database column checking
│   ├── final_field_coverage_validation.py # Field validation
│   ├── organize_phase5_commits.sh    # Commit organization script
│   ├── validate_and_report.sh        # Validation and reporting
│   ├── validate_field_coverage.py    # Field coverage validation
│   ├── 📂 analysis/                  # Analysis scripts
│   ├── 📂 archive/                   # Archived scripts
│   ├── 📂 collection/                # Collection scripts
│   ├── 📂 core/                      # Core scripts
│   ├── 📂 database/                  # Database scripts
│   │   ├── generate_baseline_migration.py
│   │   └── check_backup_tables.py
│   ├── 📂 debugging/                 # Debugging tools
│   ├── 📂 deduplication/             # Deduplication scripts
│   ├── 📂 dlt/                       # DLT scripts
│   ├── 📂 migration/                 # Migration scripts
│   ├── 📂 monitoring/                # Monitoring scripts
│   │   ├── phase2_kpi_monitor.py
│   │   ├── migration_progress_monitor.py
│   │   └── advanced_migration_monitor.py
│   ├── 📂 reports/                   # Reporting scripts
│   ├── 📂 security/                  # Security scripts
│   ├── 📂 testing/                   # Testing framework
│   │   ├── produce_final_test_report.py
│   │   ├── 📂 integration/            # Integration testing
│   │   │   ├── 📂 results/           # Test results
│   │   │   └── 📂 observability/     # Test observability
│   │   └── 📂 utils/                 # Test utilities
│   └── 📂 trust/                     # Trust validation scripts
├── 🧪 tests/                         # Test suite
│   ├── __init__.py                   # Tests package exports
│   ├── conftest.py                   # Pytest configuration
│   ├── 📂 red_phase/                 # Red phase testing
│   ├── 📂 enhanced_chunks_validation/ # Enhanced validation
│   ├── 📂 marimo/                    # Marimo testing
│   ├── test_*.py                     # Individual test files
├── 📚 docs/                          # Documentation
│   ├── README.md                     # Documentation index
│   ├── 📂 api/                       # API documentation
│   ├── 📂 architecture/              # System architecture
│   ├── 📂 components/                # Component documentation
│   ├── 📂 contributing/              # Contributing guidelines
│   ├── 📂 guides/                    # User guides
│   ├── 📂 implementation/            # Implementation details
│   ├── 📂 integrations/              # Third-party integrations
│   └── 📂 assets/                    # Images and diagrams
├── 📊 analysis/                     # Analysis outputs
├── 🗄️ backups/                      # Data backups
├── 📈 logs/                          # Log files
├── 📊 reports/                       # Generated reports
├── 🗄️ schema_dumps/                  # Database schema dumps
│   └── update_with_docker.sh         # Schema update script
├── 🗄️ supabase/                     # Supabase configuration
│   └── config.toml                   # Supabase config
├── 📋 CLAUDE.md                      # AI assistant instructions
├── 📋 LICENSE                        # License file
├── 🐳 docker-compose.yml             # Docker configuration
├── 📋 README.md                      # Main documentation
├── 🔧 lint.sh                        # Code quality script
├── ⚙️ pyproject.toml                 # Project configuration
├── 🔍 ruff.toml                      # Code quality configuration
├── 📋 ai-rulez.yaml                  # AI rules configuration
└── 📋 requirements.txt              # Python dependencies
```

## 🚀 Entry Points

### Main Entry Points
- **`core/setup.py`** - Primary setup and initialization (`setup_redditharbor()`)
- **`pipeline_v3.py`** - Pipeline v3 implementation
- **`pipeline_v3_simple.py`** - Simplified pipeline v3
- **`verify_instrumentation.py`** - Instrumentation verification

### Configuration Entry Points
- **`config/settings.py`** - Main configuration with environment variables
- **`config/dlt_settings.py`** - DLT-specific configuration
- **`pyproject.toml`** - Project metadata and dependencies

### Script Entry Points
- **`scripts/apply_migration.py`** - Database migration
- **`scripts/produce_final_test_report.py`** - Test reporting
- **`lint.sh`** - Code quality and linting

## 🔧 Core Modules & APIs

### Data Collection
- **`core/dlt/collection.py`** - DLT-powered data collection
- **`core/fetchers/collection.py`** - Core collection logic
- **`core/dlt/reddit_source.py`** - Reddit data source for DLT

### AI Agent Framework
- **`core/agents/monetization/`** - Monetization analysis agents
- **`core/agents/profiler/`** - Profiling and analysis agents
- **`core/agents/search/`** - Search and retrieval agents

### Trust Validation
- **`core/trust/validation.py`** - Trust scoring algorithm
- **`core/trust/models.py`** - Trust data models
- **`core/enrichment/trust_service.py`** - Trust scoring service

### Data Processing
- **`core/deduplication/`** - Data deduplication logic
- **`core/enrichment/`** - Data enrichment services
- **`core/quality_filters/`** - Quality filtering and scoring

### Storage & Database
- **`core/db/models.py`** - Database models
- **`core/storage/`** - Data storage implementations
- **`core/dlt/`** - DLT pipeline components

## 📊 Key APIs & Public Functions

### Core Setup Functions
```python
from core.setup import setup_redditharbor
pipeline = setup_redditharbor()  # Initialize Reddit and Supabase connections
```

### Data Collection Functions
```python
from core.dlt.collection import collect_problem_posts
from core.dlt.collection import collect_post_comments
from core.fetchers.collection import collect_data
```

### Trust Validation Functions
```python
from core.trust.validation import validate_trust
from core.enrichment.trust_service import TrustService
```

### AI Agent Functions
```python
from core.agents.monetization.factory import MonetizationAgentFactory
from core.agents.profiler.enhanced_profiler import EnhancedProfiler
```

### Configuration Access
```python
from config.settings import REDDIT_PUBLIC, REDDIT_SECRET, SUPABASE_URL
from config.dlt_settings import DLT_CONFIG
```

## 🛠️ Development Tools & Scripts

### Code Quality
- **`lint.sh`** - Comprehensive linting with Ruff
- **`ruff.toml`** - Ruff configuration for code quality

### Testing
- **`tests/`** - Comprehensive test suite
- **`scripts/testing/`** - Testing framework and utilities
- **Integration Testing** - `scripts/testing/integration/`

### Database Management
- **`scripts/database/`** - Database utilities
- **`schema_dumps/`** - Database schema management
- **Migration Scripts** - `scripts/migration/`

### Monitoring & Reporting
- **`scripts/monitoring/`** - Performance monitoring
- **`scripts/reports/`** - Report generation
- **`logs/`** - Application logs

## 🔗 Dependencies & Integrations

### Core Dependencies
- **Reddit API**: `praw>=7.6.0`
- **Database**: `supabase>=1.0.0`, `sqlalchemy>=2.0.0`
- **Data Processing**: `pandas>=1.5.0`, `numpy>=1.21.0`
- **DLT Pipeline**: `dlt>=1.18.0`
- **AI Frameworks**: `agno>=0.1.0`, `dspy-ai>=2.5.0`

### AI & ML Integration
- **LLM Integration**: `litellm>=1.45.0`
- **Multi-Agent**: `agno>=0.1.0`
- **Cost Tracking**: `agentops>=0.2.0`
- **PII Protection**: `spacy>=3.4.0`

### Development Tools
- **Code Quality**: `ruff>=0.14.4`
- **Testing**: `pytest>=9.0.0`
- **Type Checking**: `mypy>=1.0.0`

## 🎯 Research Templates

### Pre-built Templates (via `core/pipeline/templates.py`)
1. **Academic Research** - Comprehensive data collection with privacy controls
2. **Market Research** - Sentiment analysis and trend monitoring
3. **Learning Community** - Educational behavior analysis
4. **AI/ML Monitoring** - Technology trend monitoring
5. **Startup Ecosystem** - Startup discussion analysis
6. **Viral Content Analysis** - Cross-community viral patterns

### Target Subreddit Segments
- **Health & Fitness**: fitness, nutrition, mentalhealth
- **Finance & Investing**: personalfinance, investing, stocks
- **Education & Career**: learnprogramming, cscareerquestions
- **Travel Experiences**: travel, digitalnomad, backpacking
- **Real Estate**: RealEstate, FirstTimeHomeBuyer
- **Technology & SaaS**: SaaS, startups, entrepreneurship

## 🔒 Security & Privacy

### PII Anonymization
- **Enabled by default** via `ENABLE_PII_ANONYMIZATION=True`
- **spaCy integration** for PII detection and removal
- **Configurable masking** for different use cases

### API Security
- **Environment-based credential management**
- **Local Supabase instance** for development
- **Read-only Reddit API access**
- **No hardcoded secrets** in source code

## 📈 Performance Features

### DLT Activity Validation
- **50-300% faster** than traditional collection methods
- **Multi-factor activity scoring** algorithm
- **Intelligent filtering** for high-value content
- **Incremental loading** with state management

### Trust Scoring System
- **6-dimensional analysis**: Activity, engagement, trends, validity, quality, confidence
- **Badge system**: GOLD, SILVER, BRONZE, BASIC
- **Real-time validation** with configurable thresholds

## 🚀 Deployment & Production

### Development Setup
```bash
# Clone and setup
git clone <repository>
cd redditharbor-core-functions-fix
uv venv && source .venv/bin/activate
uv sync

# Configure environment
cp .env.example .env.local
# Edit .env.local with credentials

# Run tests
PYTHONPATH=. python -m tests.test_quick

# Start collection
python scripts/run_dlt_activity_collection.py --segment "technology_saas"
```

### Production Considerations
- **Supabase Cloud** integration ready
- **Environment variable configuration**
- **Docker support** via docker-compose.yml
- **Monitoring and logging** built-in

## 📚 Documentation Structure

### User Documentation
- **`docs/guides/`** - User guides and tutorials
- **`docs/api/`** - API reference documentation
- **`README.md`** - Main project documentation

### Technical Documentation
- **`docs/architecture/`** - System architecture and design
- **`docs/implementation/`** - Implementation details
- **`docs/integrations/`** - Third-party integration docs

### Development Documentation
- **`docs/contributing/`** - Contribution guidelines
- **`CLAUDE.md`** - AI assistant instructions
- **Inline code documentation** with comprehensive docstrings

## 🎯 Use Cases & Applications

### Academic Research
- Social media analysis studies
- Community behavior research
- Natural language processing datasets
- Trend analysis projects

### Business Intelligence
- Competitor analysis monitoring
- Customer sentiment tracking
- Market research automation
- Brand monitoring systems

### Data Science & ML
- Machine learning training data
- Text analysis pipelines
- Network analysis studies
- Multi-agent research systems

---

**Repository Size**: 1000+ files across core modules, tests, documentation, and tools
**Test Coverage**: Comprehensive test suite with integration testing
**Code Quality**: Ruff-based linting with comprehensive configuration
**Production Status**: Phase 4 complete, Phase 5 planning in progress

*This index provides a comprehensive overview of the RedditHarbor repository structure, key components, and development workflows. For detailed documentation on specific components, refer to the respective documentation directories.*