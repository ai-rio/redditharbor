<!--
🤖 AI-RULEZ :: GENERATED FILE — DO NOT EDIT DIRECTLY
Project: RedditHarbor
Generated: 2025-11-03 18:07:53
Source of truth: ai-rulez.yaml
Target file: GEMINI.md
Content summary: rules=21, sections=4, agents=0

UPDATE WORKFLOW
1. Modify ai-rulez.yaml
2. Run `ai-rulez generate` to refresh generated files
3. Commit regenerated outputs together with the config changes

AI ASSISTANT SAFEGUARDS
- Treat ai-rulez.yaml as the canonical configuration
- Never overwrite GEMINI.md manually; regenerate instead
- Surface changes as patches to ai-rulez.yaml (include doc/test updates)

Need help? /capability-plan or https://github.com/Goldziher/ai-rulez
-->

# RedditHarbor

RedditHarbor is a comprehensive Reddit data collection and research platform built with Python that transforms Reddit discussions into research-ready datasets through automated collection and analysis tools with AI-agent friendly architecture and multiple research templates.

Version: 1.0.0

## Governance

- Source of truth: ai-rulez.yaml
- Generated output: GEMINI.md
- Update workflow:
  1. Edit the source configuration above.
  2. Run ai-rulez generate to refresh generated files.
  3. Commit the regenerated files alongside the configuration change.
- AI assistants must propose edits to the source configuration, not this file.

## Rules

### Code Quality
**Priority:** medium

Use ruff for linting and formatting. Run lint.sh before commits. Follow Python PEP 8 style guidelines. Use type hints for all function parameters and returns.

### Documentation Standards
**Priority:** medium

Include comprehensive docstrings for all public functions. Use triple-quoted strings with Args:, Returns:, and Raises: sections. Document configuration constants with inline comments explaining their purpose.

### Documentation Structure
**Priority:** medium

Organize documentation in docs/ with subdirectories: api/ for API docs, guides/ for tutorials, architecture/ for design decisions, contributing/ for contribution guidelines, assets/ for images and diagrams. Use CueTimer brand colors (#FF6B35, #004E89, #F7B801) consistently in documentation.

### Import Structure
**Priority:** medium

Use star imports (*) only in config/__init__.py, core/setup.py, scripts/, and tests/ directories as per ruff.toml exceptions. Standard Python imports elsewhere. Always add project root to sys.path for scripts.

### Modular Architecture
**Priority:** medium

Keep core/ modules focused and single-purpose. Use clear separation between collection logic, templates, and configuration. Import paths should be relative and explicit.

### Module Architecture Boundaries
**Priority:** medium

Respect the clean architecture: core/ for essential functionality, config/ for settings, scripts/ for research workflows, and tests/ for test suites. Import restrictions: scripts may import from core, but core modules should not import from scripts.

### Testing with Fallbacks
**Priority:** medium

Write tests with ImportError fallbacks for dependencies. Test Reddit API connectivity with simple subreddit queries. Test Supabase with count queries. Validate configuration loading with fallback defaults.

### UV Dependency Management
**Priority:** medium

Use UV for Python package management (uv.lock present). All dependencies must be declared in requirements.txt. When adding new Reddit-related packages, verify compatibility with the existing data collection pipeline.

### Documentation and Research Templates
**Priority:** low

Document all research templates in core/templates.py. Update docs/guides/ when adding new research capabilities. Maintain JSON structure for research briefs and findings.

### Error Handling
**Priority:** high

Implement comprehensive error handling in core/collection.py. Log errors to error_log/ directory with descriptive filenames. Always validate API responses from Reddit.

### Error Handling and Logging
**Priority:** high

Use try-except blocks for all external API calls (Reddit, Supabase). Include proper logging with structured messages using logger.info(), logger.error(). Return boolean success status from core functions like collect_data().

### File Organization Standards
**Priority:** high

Maintain clean root directory. Use analysis/ for research and license analysis files, generated/ for AI-produced content, docs/ for documentation. Follow kebab-case naming for all files except README.md, CHANGELOG.md, LICENSE. Keep core/ for essential functionality, config/ for settings, scripts/ for workflows, tests/ for test suites.

### PII Anonymization
**Priority:** high

Always respect ENABLE_PII_ANONYMIZATION setting. When enabled, use spaCy en_core_web_lg model for PII detection and anonymization. Handle PII masking at the collection pipeline level before data storage.

### Reddit Data Collection Error Handling
**Priority:** high

All Reddit API calls in core/collection.py must include rate limiting handling and proper error recovery. Use try-except blocks with specific Reddit API exceptions and implement exponential backoff for failed requests.

### Security and Privacy Handling
**Priority:** high

All Reddit user data must be processed through PII anonymization. Never store raw user identifiers in the database. Use the established error_log/ pattern for handling collection failures without exposing sensitive data.

### Template Configuration Management
**Priority:** high

Use config/settings.py for all configuration values. Never hardcode credentials or API keys. Follow the fallback mechanism pattern established in the config module for environment variables.

### Testing Standards
**Priority:** high

Run pytest for all new functionality. Use tests/ directory for unit tests, integration tests for core modules, and test scripts/ with sample data. Maintain test coverage above 80%.

### Configuration Management
**Priority:** critical

Store all configuration in config/settings.py using REDDIT_PUBLIC, REDDIT_SECRET, SUPABASE_URL, SUPABASE_KEY constants. Never hardcode credentials in other files. Use DB_CONFIG for database table mappings.

### Data Privacy and PII
**Priority:** critical

Anonymize all Reddit user data before storage. Use PII detection and removal tools. Store only research-relevant data in compliance with Reddit's ToS and privacy regulations.

### Pytest Testing Standards
**Priority:** critical

Write unit tests for all functions in core/ and scripts/ modules. Use pytest for testing (configured in project). Test files must be in tests/ directory with test_ prefix. Aim for 80% coverage on Reddit data collection logic.

### Ruff Code Quality
**Priority:** critical

Always run 'ruff check .' and 'ruff format .' before commits. Use the lint.sh script for comprehensive checks. Follow the ruff.toml configuration which allows star imports in config/ and scripts/ directories.

## Sections

### Core Architecture
**Priority:** medium

## RedditHarbor Core Architecture

### Module Structure
- **core/**: Essential functionality and business logic
  - `collection.py`: Reddit API data collection with error handling
  - `templates.py`: Research template definitions and configurations
  - `setup.py`: Project initialization and environment setup
- **config/**: Configuration management and settings
  - `settings.py`: Environment variables and database configuration
  - `__init__.py`: Configuration exports and constants
- **scripts/**: Research workflow execution scripts
- **tests/**: Unit and integration tests

### Data Flow
1. Reddit API → Collection Pipeline (core/collection.py)
2. PII Anonymization → Privacy Compliance Layer
3. Data Validation → Supabase Storage
4. Research Templates → Analysis Workflows

### Key Components
- Rate limiting and error recovery for Reddit API
- Configurable PII anonymization using spaCy
- Template-based research workflows
- Comprehensive logging and error tracking
- Modular testing with dependency fallbacks

### Database Schema
**Priority:** medium

## RedditHarbor Database Schema

### Core Tables
- **redditor**: Reddit user profiles and metadata
- **submission**: Posts and submissions data
- **comment**: Comments and replies hierarchy

### Access Methods
- Supabase Studio: http://127.0.0.1:54323
- REST API: http://127.0.0.1:54321/rest/v1/
- Direct SQL: `postgresql://postgres:postgres@127.0.0.1:54322/postgres`

### Development Workflow
**Priority:** high

## RedditHarbor Development Workflow

### Environment Setup
1. Clone the repository and navigate to the project root
2. Install dependencies using UV: `uv sync`
3. Set up environment variables in `.env` file
4. Start Supabase locally: `supabase start`
5. Run database migrations: `supabase db push`

### Code Quality Workflow
1. Make changes to core modules or scripts
2. Run linting: `./lint.sh` or `ruff check . && ruff format .`
3. Run tests: `pytest tests/`
4. Verify functionality with test scripts in `scripts/`
5. Commit changes with descriptive messages

### Research Data Collection
1. Configure Reddit API credentials in config/settings.py
2. Select research template from core/templates.py
3. Run collection script: `python scripts/collect_research_data.py`
4. Monitor progress in error_log/ directory
5. Analyze results in Supabase Studio

### Reddit API Setup
**Priority:** high

## Reddit API Configuration
1. Create Reddit App at https://www.reddit.com/prefs/apps
2. Select 'script' app type
3. Record client_id and client_secret
4. Add redirect URI: http://localhost:8080
5. Store credentials securely in .env file

## MCP Servers

### ai-rulez
AI-Rulez MCP server for configuration management
- Transport: stdio
- Command: npx
- Args: -y, ai-rulez@latest, mcp
