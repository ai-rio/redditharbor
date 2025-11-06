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
- **[Component Guide](./components/README.md)** - Detailed component documentation
- **[User Guides](./guides/README.md)** - Step-by-step tutorials and how-to guides
- **[Architecture](./architecture/README.md)** - System design and architecture decisions

### Setup & Verification

- **[Setup Guide](./guides/setup-guide.md)** - Complete multi-project setup instructions
- **[Setup Checklist](./guides/setup-checklist.md)** - Verification checklist for complete setup
- **[Verification Report](./guides/verification-report.md)** - Manual verification and certification report
- **[Security Guide](./guides/security-guide.md)** - Comprehensive security and privacy protection

### Development Documentation

- **[Contributing Guide](./contributing/README.md)** - How to contribute to RedditHarbor
- **[Project Setup](./guides/setup-guide.md)** - Development environment setup
- **[Testing Guide](./guides/testing.md)** - Testing procedures and best practices *(Coming Soon)*

### Implementation & Research

- **[Implementation Success](./implementation/IMPLEMENTATION_SUCCESS.md)** - AI insight generation implementation details
- **[Active Work Notes](./research/active-work-notes.md)** - Active development work log
- **[Project Overview](./research/project-overview.md)** - Project overview and history
- **[Requirements](./architecture/requirements.txt)** - Project dependencies

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

1. **Read the [Setup Guide](./guides/setup-guide.md)** - Complete setup instructions
2. **Check the [Setup Checklist](./guides/setup-checklist.md)** - Verify your setup
3. **Review the [Verification Report](./guides/verification-report.md)** - System certification details
4. **Explore [Research Types](./guides/research-types.md)** - Available research capabilities

### For Developers

1. **Check the [API Reference](./api/README.md)** - Detailed function documentation
2. **Review [Component Documentation](./components/README.md)** - Component details
3. **Read [Architecture Guide](./architecture/README.md)** - System design
4. **Follow [Contributing Guidelines](./contributing/README.md)** - How to contribute

### For Researchers

1. **Start with [Research Types Guide](./guides/research-types.md)** - Research methodologies
2. **Review [Security Guide](./guides/security-guide.md)** - Privacy and ethics
3. **Check [Setup Guide](./guides/setup-guide.md)** - Multi-project setup
4. **Verify with [Setup Checklist](./guides/setup-checklist.md)** - Ensure completeness

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
    Explore all research possibilities in our comprehensive <a href="./guides/research-types.md" style="color: #004E89;">Research Types Guide</a>
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
    <a href="./guides/verification-report.md" style="color: #004E89;">View detailed verification report →</a>
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
  <span style="color: #1A1A1A;">Check our <a href="./guides/setup-checklist.md" style="color: #004E89;">Setup Checklist</a> or <a href="./contributing/README.md" style="color: #004E89;">Contact Us</a></span>
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