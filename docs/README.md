# RedditHarbor Documentation

<div style="text-align: center; margin: 20px 0;">
  <h1 style="color: #FF6B35;">RedditHarbor</h1>
  <p style="color: #004E89; font-size: 1.2em;">Reddit Data Collection & Analysis Toolkit</p>
</div>

## Overview

RedditHarbor is a comprehensive Python package for collecting, storing, and analyzing Reddit data with privacy-preserving features. This toolkit simplifies Reddit data collection workflows and provides robust database integration for research and analytics projects.

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd redditharbor

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```python
from redditharbor import RedditCollector

# Initialize collector
collector = RedditCollector(client_id="your_client_id",
                           client_secret="your_client_secret")

# Collect data from a subreddit
data = collector.collect_subreddit_posts("python", limit=100)

# Store to database
collector.store_to_database(data, database_url="your_db_url")
```

---

## 📚 Documentation Structure

### Core Documentation

- **[API Reference](./api/README.md)** - Complete API documentation and function reference
- **[Component Guide](./components/README.md)** - Reusable UI components and modular system architecture
  - **[Agents Overview](./components/agents-overview.md)** - Multi-agent system components and architecture
- **[User Guides](./guides/README.md)** - Step-by-step tutorials and comprehensive how-to guides
- **[Development & Operations](./guides/development-operations/README.md)** - Development workflows, testing, and deployment guides
- **[Architecture](./architecture/README.md)** - System design and architecture decisions
- **[Technical Specifications](./technical/README.md)** - System architecture, deployment guides, and technical specifications
- **[Testing Reports](./test-results/README.md)** - Comprehensive testing results, quality metrics, and validation reports
- **[Implementation](./implementation/README.md)** - Technical implementation and migration documentation
  - **[MCP Integration Fixes](./implementation/mcp-integration-fixes-summary.md)** - Model Context Protocol integration improvements and fixes

### Business & Strategy

- **[Business Strategy](./business/README.md)** - Strategic planning, monetization, and market positioning
- **[Planning & Roadmaps](./plans/README.md)** - Strategic plans, development roadmaps, and project timelines
- **[Bias Analysis](./bias/README.md)** - System bias detection, function count diagnosis, and optimization

### Resources & Examples

- **[Examples & Usage Patterns](./examples/README.md)** - Practical examples and implementation patterns
- **[Assets & Visual Resources](./assets/README.md)** - Diagrams, examples, and images for documentation

### Setup & Verification

- **[Getting Started Guides](./guides/getting-started/)** - Complete setup instructions and quick start guides
- **[Setup Checklist](./guides/getting-started/setup-checklist.md)** - Verification checklist for complete setup
- **[Verification Report](./guides/monitoring-quality/verification-report.md)** - Manual verification and certification report
- **[Security Guide](./guides/security-compliance/security-guide.md)** - Comprehensive security and privacy protection

### Development Documentation

- **[Development & Operations](./guides/development-operations/README.md)** - Development workflows, testing, and deployment
- **[Contributing Guide](./contributing/README.md)** - How to contribute to RedditHarbor
- **[Testing Procedures](./guides/development-operations/e2e-workflow-implementation-guide.md)** - End-to-end testing and validation

### External Integrations

- **[Integrations Overview](./integrations/README.md)** - Third-party service integration documentation
  - **[Agno Integration](./integrations/agno/)** - Multi-agent LLM framework for monetization analysis
  - **[AgentOps Integration](./integrations/agentops/)** - AI agent observability and cost tracking
  - **[Jina Integration](./integrations/jina/)** - Reader API for real market data validation
  - **[Gemini Integration](./integrations/gemini-integration.md)** - Google Gemini AI integration documentation

### DLT Integration & Pipeline

- **[DLT Integration Guides](./guides/integrations-tools/)** - Complete DLT integration and migration documentation
- **[DLT Consolidation Complete](./architecture/dlt-consolidation-complete.md)** - All 6 scripts migrated to DLT pipeline
- **[DLT Architecture](./architecture/dlt-consolidated-architecture.md)** - System design and data flow documentation

### Testing & Analysis Reports

- **[Testing Reports](./reports/)** - Comprehensive E2E and threshold testing reports
  - **[E2E Testing](./reports/e2e/)** - Complete end-to-end testing results and validation
  - **[Threshold Testing](./reports/threshold-testing/)** - Performance testing at various thresholds
- **[System Analysis](./analysis/)** - Performance analysis and system metrics
- **[System Logs](./logs/)** - Historical logs and debugging information
- **[JSON Reports & Data](./json/)** - Structured JSON reports and system data
  - **[Migration JSON](./json/migration/)** - Migration state snapshots and verification
  - **[Workflow JSON](./json/workflow/)** - Workflow execution and performance data
  - **[Analysis JSON](./json/analysis/)** - System analysis and diagnostic reports

### Implementation & Research

- **[Implementation Documentation](./implementation/)** - Complete implementation lifecycle documentation
- **[Bug Fixes & Critical Updates](./implementation/#-bug-fixes--critical-updates)** - Recent bug fixes and system improvements
- **[DLT Integration](./implementation/#-dlt-integration-documentation)** - Complete DLT pipeline implementation
- **[Migration Reports](./implementation/#-migration--workflow-documentation)** - Migration execution and workflow summaries
- **[Cost Tracking Documentation](./guides/cost-tracking/README.md)** - Complete cost tracking observability implementation
  - **[Deployment Guide](./guides/cost-tracking/deployment-guide.md)** - Setup and deployment instructions
  - **[Analytics Guide](./guides/cost-tracking/analytics-guide.md)** - Analytics and monitoring for cost tracking
  - **[SQL Queries](./guides/cost-tracking/sql-queries.md)** - SQL queries for cost analysis and reporting

### Archive & Historical Documentation

- **[Documentation Archive](./archive/README.md)** - Historical documentation and completed projects
  - **[Implementation Archive](./archive/old_versions/)** - Completed implementation phases and migration reports
  - **[Research Archive](./archive/research_notes/)** - Historical research documentation and findings
  - **[Agent Archive](./archive/agents/)** - AI agent specifications and configurations
  - **[Methodology Archive](./archive/methodology/)** - Previous research approaches and frameworks

### Resources

- **[Images & Diagrams](./assets/images/)** - Visual assets and diagrams
- **[Examples](./assets/examples/)** - Code examples and sample implementations
- **[Changelog](../CHANGELOG.md)** - Version history and changes *(Coming Soon)*
- **[Naming Conventions](./naming-conventions.md)** - File naming standards and conventions

---

## 🎯 Key Features

- **Privacy-Preserving**: Built-in privacy features for responsible data collection
- **Database Integration**: Seamless integration with PostgreSQL and SQLite
- **Flexible Collection**: Support for posts, comments, user data, and more
- **Analytics Ready**: Structured data storage optimized for analysis
- **Error Handling**: Robust error handling and retry mechanisms
- **Multi-Project Architecture**: Isolated schemas for different research projects

---

## 🏗️ Architecture

<div style="background: #F5F5F5; padding: 15px; border-radius: 8px; border-left: 4px solid #FF6B35; margin: 20px 0;">
  <p style="margin: 0; color: #1A1A1A;">
    <strong>RedditHarbor</strong> follows a modular architecture with separate components for data collection, processing, storage, and analysis. See the <a href="./architecture/README.md" style="color: #004E89;">Architecture Documentation</a> for detailed design decisions.
  </p>
</div>

### Core Components

- **RedditCollector**: Main data collection component
- **PrivacyProcessor**: Data anonymization and privacy protection
- **DatabaseManager**: Database operations and schema management
- **DataValidator**: Data quality validation and integrity checks
- **ExportManager**: Data export in multiple formats

---

## 📖 Getting Started

### For New Users

1. **Read the [Getting Started Guides](./guides/getting-started/)** - Complete setup instructions and quick starts
2. **Check the [Setup Checklist](./guides/getting-started/setup-checklist.md)** - Verify your setup
3. **Review the [Verification Report](./guides/monitoring-quality/verification-report.md)** - System certification details
4. **Explore [Research Types](./guides/research-analysis/research-types.md)** - Available research capabilities

### For Developers

1. **Check the [Development & Operations Guide](./guides/development-operations/README.md)** - Development workflows and testing
2. **Review the [API Reference](./api/README.md)** - Detailed function documentation
3. **Read [Architecture Guide](./architecture/README.md)** - System design
4. **Follow [Contributing Guidelines](./contributing/README.md)** - How to contribute

### For Researchers

1. **Start with [Research Types Guide](./guides/research-analysis/research-types.md)** - Research methodologies
2. **Review [Security Guide](./guides/security-compliance/security-guide.md)** - Privacy and ethics
3. **Check [Getting Started Guide](./guides/getting-started/setup-guide.md)** - Multi-project setup
4. **Verify with [Setup Checklist](./guides/getting-started/setup-checklist.md)** - Ensure completeness

---

## 🗄️ Database Schema

RedditHarbor uses a dedicated schema for data isolation:

```
redditharbor/
├── redditor (Reddit user data)
├── submission (Posts and submissions)
└── comment (Comments and replies)
```

### Access Methods

- **Supabase Studio**: http://127.0.0.1:54323
- **REST API**: http://127.0.0.1:54321/rest/v1/
- **Direct SQL**: `postgresql://postgres:postgres@127.0.0.1:54322/postgres`

---

## 🔒 Privacy & Security

RedditHarbor prioritizes user privacy and data security:

- **PII Anonymization**: Automatic detection and redaction of personally identifiable information
- **Schema Isolation**: Each project's data is isolated in dedicated schemas
- **Credential Protection**: Comprehensive .gitignore and security practices
- **IRB Compliance**: Built-in features for institutional review board compliance

<div style="background: #F7B801; padding: 10px; border-radius: 6px; margin: 15px 0; text-align: center;">
  <strong style="color: #1A1A1A;">🔒 Security First</strong><br>
  <span style="color: #1A1A1A;">See our <a href="./guides/security-guide.md" style="color: #004E89;">Security Guide</a> for comprehensive protection practices</span>
</div>

---

## 📊 Research Applications

RedditHarbor supports various research types:

### Academic Research
- Community behavior analysis
- Knowledge sharing dynamics
- Temporal trend studies
- Cross-community influence

### Market Research
- Product sentiment analysis
- Industry trend monitoring
- Brand perception tracking
- Competitor analysis

### Data Science & ML
- Engagement prediction models
- Content popularity forecasting
- User behavior classification
- Trend detection algorithms

### Social Science Research
- Online community formation
- Information diffusion patterns
- Cultural norm analysis
- Conflict resolution studies

<div style="background: #F5F5F5; padding: 15px; border-radius: 8px; margin: 20px 0;">
  <h4 style="color: #1A1A1A; margin-top: 0;">📚 Learn More</h4>
  <p style="margin: 0; color: #1A1A1A;">
    Explore all research possibilities in our comprehensive <a href="./guides/research-analysis/research-types.md" style="color: #004E89;">Research Types Guide</a>
  </p>
</div>

---

## 🛠️ Project Templates

RedditHarbor includes pre-configured project templates:

- **tech_research** - Academic research on programming communities
- **ai_ml_monitoring** - AI/ML trend monitoring and analysis
- **startup_analysis** - Startup ecosystem research
- **gaming_community** - Gaming community analysis

---

## 📈 System Status

<div style="background: #E8F5E8; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50; margin: 20px 0;">
  <h4 style="color: #1A1A1A; margin-top: 0;">✅ System Certified</h4>
  <ul style="color: #1A1A1A; margin: 0; padding-left: 20px;">
    <li><strong>Database Infrastructure:</strong> Verified and operational</li>
    <li><strong>Data Collection:</strong> 15 redditors, 17 submissions collected</li>
    <li><strong>Multi-subreddit:</strong> Data from r/Python, r/technology, r/programming, r/startups</li>
    <li><strong>Security:</strong> Comprehensive protection implemented</li>
  </ul>
  <p style="margin: 10px 0 0 0; color: #1A1A1A;">
    <a href="./guides/monitoring-quality/verification-report.md" style="color: #004E89;">View detailed verification report →</a>
  </p>
</div>

---

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guide](./contributing/README.md) to get started.

### Ways to Contribute

- **Code Contributions**: New features, bug fixes, performance improvements
- **Documentation**: Improve guides, fix typos, add examples
- **Testing**: Write tests, report bugs, suggest improvements
- **Community**: Help other users, share projects, provide feedback

<div style="background: #F7B801; padding: 10px; border-radius: 6px; margin: 15px 0; text-align: center;">
  <strong style="color: #1A1A1A;">Questions? Need Help?</strong><br>
  <span style="color: #1A1A1A;">Check our <a href="./guides/getting-started/setup-checklist.md" style="color: #004E89;">Setup Checklist</a> or <a href="./contributing/README.md" style="color: #004E89;">Contact Us</a></span>
</div>

---

## 📋 Documentation Standards

This documentation follows strict naming conventions:

- **Kebab-case**: All files use `kebab-case` naming
- **CueTimer Branding**: Consistent use of brand colors (#FF6B35, #004E89, #F7B801)
- **Cross-References**: Comprehensive linking between related topics
- **Visual Elements**: Structured layouts with clear navigation

<div style="background: #F5F5F5; padding: 15px; border-radius: 8px; margin: 20px 0;">
  <h4 style="color: #1A1A1A; margin-top: 0;">📝 Documentation Guidelines</h4>
  <p style="margin: 0; color: #1A1A1A;">
    See our <a href="./naming-conventions.md" style="color: #004E89;">Naming Conventions Guide</a> for detailed standards and best practices
  </p>
</div>

---

## 🔄 Version History

### Current Version
- **Multi-Project Architecture**: Complete setup with isolated schemas
- **Privacy Features**: Enhanced PII anonymization and protection
- **Research Templates**: Pre-configured project templates
- **System Certification**: Manual verification and certification completed

### Previous Versions
- Single-project setup
- Basic data collection
- Limited privacy features

---

<div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 2px solid #F5F5F5;">
  <p style="color: #666; font-size: 0.9em;">
    Built with ❤️ using <span style="color: #FF6B35;">CueTimer</span> branding •
    <a href="./naming-conventions.md" style="color: #004E89;">Documentation Standards</a> •
    <a href="./contributing/README.md" style="color: #004E89;">Contributing Guidelines</a>
  </p>
</div>