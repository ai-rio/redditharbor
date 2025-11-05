# RedditHarbor 🚀

**A comprehensive Reddit data collection and research platform with organized, AI-agent friendly architecture.**

<div align="center">

![RedditHarbor Logo](https://img.shields.io/badge/RedditHarbor-v0.3-FF6B35?style=for-the-badge&logo=reddit)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-MIT-004E89?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Production%20Ready-F7B801?style=for-the-badge)

</div>

---

## 📋 Table of Contents

- [🎯 Overview](#-overview)
- [✨ Features](#-features)
- [🏗️ Architecture](#️-architecture)
- [🚀 Quick Start](#-quick-start)
- [🔧 Configuration](#-configuration)
- [📊 Research Capabilities](#-research-capabilities)
- [🛠️ Development](#️-development)
- [📚 Documentation](#-documentation)
- [🔒 Security](#-security)
- [🤝 Contributing](#-contributing)

---

## 🎯 Overview

RedditHarbor is a **reorganized, production-ready** Reddit data collection platform that transforms Reddit discussions into research-ready datasets. Built with **AI-agent compatibility** in mind, it features a clean, modular architecture that makes both human and automated research workflows intuitive.

### 🔥 What's New in v0.3

- **✨ Reorganized package structure** for better maintainability
- **🤖 AI-agent ready** architecture with clear boundaries
- **🔧 Improved configuration management** with fallback mechanisms
- **📋 Built-in code quality tools** (Ruff integration)
- **🎯 Enhanced research templates** for common use cases

---

## ✨ Features

### 🏗️ Clean Architecture
```
redditharbor/
├── config/           # 📋 Configuration management
├── core/             # 🔧 Core functionality
├── scripts/          # 📊 Research scripts & demos
├── tests/            # 🧪 Test suite
└── docs/             # 📚 Documentation
```

### 🎯 Research Capabilities
- **6 pre-built research templates** for common analysis patterns
- **Custom research workflows** with flexible parameters
- **Real-time data collection** from Reddit API
- **PII anonymization** for research compliance
- **Multi-subreddit support** with customizable filters

### 🛡️ Production Ready
- **Error handling & fallbacks** at every level
- **Privacy-first design** with PII protection
- **Database integration** with Supabase
- **Code quality monitoring** with Ruff
- **Comprehensive testing** suite

---

## 🏗️ Architecture

RedditHarbor follows **clean architecture principles** with clear separation of concerns:

### 📦 Package Structure

| Package | Purpose | Key Components |
|---------|---------|-----------------|
| **config/** | Configuration Management | API keys, database settings, research parameters |
| **core/** | Core Functionality | Reddit connections, data collection, setup utilities |
| **scripts/** | Research Workflows | Research templates, demos, certification tools |
| **tests/** | Quality Assurance | Integration tests, debug tools, functionality checks |

### 🔗 Data Flow

```
Reddit API → Core Collection → Supabase Database → Research Analysis
     ↓              ↓                ↓                 ↓
  Config        Validation      Storage          Insights
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** installed
- **uv** package manager (recommended)
- **Reddit API credentials** (Reddit app)
- **Supabase instance** (local or cloud)

### 1️⃣ Setup Environment

```bash
# Clone and navigate
cd /home/carlos/projects/redditharbor

# Set up uv virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

### 2️⃣ Configure API Credentials

Edit `config/settings.py` with your credentials:

```python
# Reddit API Configuration
REDDIT_PUBLIC = "your-reddit-public-key"
REDDIT_SECRET = "your-reddit-secret-key"
REDDIT_USER_AGENT = "your-project-name (u/your-username)"

# Supabase Configuration
SUPABASE_URL = "your-supabase-url"
SUPABASE_KEY = "your-supabase-service-role-key"
```

### 3️⃣ Test the Setup

```bash
# Run structure demo
PYTHONPATH=. python scripts/demo_simple.py

# Run quick connectivity test
PYTHONPATH=. python -m tests.test_quick
```

### 4️⃣ Start Research!

```python
# Import organized modules
from config import settings as config
from core.setup import setup_redditharbor
from scripts.research import run_research_project

# Initialize connections
reddit, supabase = setup_redditharbor()

# Run programming trends research
run_research_project(
    'programming_trends',
    subreddits=['python', 'MachineLearning'],
    limit=100
)
```

---

## 🔧 Configuration

### 📋 Core Settings

Located in `config/settings.py`:

```python
# Research Configuration
DEFAULT_SUBREDDITS = ["python", "MachineLearning", "datascience", "learnprogramming"]
DEFAULT_LIMIT = 100
DEFAULT_SORT_TYPES = ["hot", "top", "new"]

# Privacy Settings
ENABLE_PII_ANONYMIZATION = True  # Recommended for research

# Database Configuration
DB_CONFIG = {
    "user": "redditor",
    "submission": "submission",
    "comment": "comment"
}
```

### 🎛️ Custom Research Parameters

```python
# Custom research workflow
from scripts.research import custom_research_project

custom_params = {
    "subreddits": ["python", "reactjs", "javascript"],
    "keywords": ["hooks", "state", "component"],
    "sort_type": "hot",
    "limit": 200,
    "time_filter": "week"
}

custom_research_project(
    name="react_hooks_analysis",
    description="Analyze React hooks discussions",
    **custom_params
)
```

---

## 📊 Research Capabilities

### 🔬 Available Research Templates

| Template | Description | Use Case |
|---------|-------------|---------|
| **programming_trends** | Programming language discussions | Trend analysis |
| **tech_industry_sentiment** | Tech company sentiment analysis | Market research |
| **learning_community** | Learning behavior analysis | Educational research |
| **ai_ml_monitoring** | AI/ML trend monitoring | Technology research |
| **startup_ecosystem** | Startup discussion analysis | Entrepreneurship research |
| **viral_content_analysis** | Cross-community viral patterns | Content research |

### 🎯 Research Workflow Examples

#### Basic Data Collection
```python
from core.collection import collect_data

# Collect from specific subreddits
collect_data(
    reddit_client=reddit,
    supabase_client=supabase,
    subreddits=["python", "MachineLearning"],
    limit=50,
    sort_types=["hot"],
    mask_pii=True
)
```

#### Custom Analysis
```python
from scripts.research import generate_research_report

# Generate comprehensive report
generate_research_report(
    title="Python Framework Analysis",
    description="Analysis of Python web framework discussions",
    output_format="markdown"
)
```

---

## 🛠️ Development

### 🔧 Code Quality

RedditHarbor includes **Ruff** for code quality management:

```bash
# Run our linting script
./lint.sh

# Or use Ruff directly
source .venv/bin/activate
ruff check .           # Find issues
ruff check . --fix      # Auto-fix issues
ruff format .           # Format code
```

### 🧪 Testing

```bash
# Run all tests
PYTHONPATH=. python -m tests.test_full

# Run specific tests
PYTHONPATH=. python -m tests.test_quick      # Quick collection
PYTHONPATH=. python -m tests.test_debug      # Debug issues
PYTHONPATH=. python -m tests.test_setup      # Setup verification
```

### 📁 Project Structure

```
redditharbor/
├── config/                     # 📋 Configuration
│   ├── __init__.py            # Package initialization
│   └── settings.py            # Core configuration settings
├── core/                      # 🔧 Core functionality
│   ├── __init__.py            # Core package exports
│   ├── setup.py               # Reddit/Supabase setup utilities
│   ├── collection.py          # Data collection functions
│   └── templates.py           # Research project templates
├── scripts/                   # 📊 Research workflows
│   ├── __init__.py            # Scripts package exports
│   ├── research.py            # Research project implementations
│   ├── demo.py                # Demo and examples
│   └── certification.py        # Data collection certification
├── tests/                     # 🧪 Test suite
│   ├── __init__.py            # Tests package exports
│   ├── test_debug.py          # Debug utilities
│   ├── test_quick.py          # Quick functionality tests
│   ├── test_full.py           # Comprehensive tests
│   └── test_setup.py          # Setup verification
├── docs/                      # 📚 Documentation
│   ├── api/                   # API documentation
│   ├── architecture/          # System architecture
│   ├── guides/                # User guides
│   └── contributing/          # Contributing guidelines
├── config.py                  # ⚙️ Backward compatibility config wrapper
├── requirements.txt           # 📦 Python dependencies
├── ruff.toml                  # 🔍 Code quality configuration
├── lint.sh                    # 🔧 Linting script
├── marimo_notebooks/          # 📊 Marimo dashboard notebooks
└── README.md                  # 📖 This file
```

---

## 📚 Documentation

### 🎯 Essential Guides

- **[docs/guides/quickstart.md](./docs/guides/quickstart.md)** - Quick reference for common operations
- **[docs/guides/research-guide.md](./docs/guides/research-guide.md)** - Complete research workflow guide
- **[docs/guides/setup-guide-root.md](./docs/guides/setup-guide-root.md)** - Detailed setup instructions
- **[docs/guides/integration-complete.md](./docs/guides/integration-complete.md)** - Marimo integration documentation

### 🔧 Technical Documentation

- **[docs/api/README.md](./docs/api/README.md)** - Complete API reference
- **[docs/architecture/README.md](./docs/architecture/README.md)** - System architecture overview
- **[docs/guides/research-types.md](./docs/guides/research-types.md)** - Research capabilities

### 🤝 Development

- **[docs/contributing/README.md](./docs/contributing/README.md)** - Contributing guidelines
- **[docs/guides/security-guide.md](./docs/guides/security-guide.md)** - Security best practices

---

## 🔒 Security

### 🛡️ Privacy Protection

- **✅ PII Anonymization** enabled by default
- **🔐 Local credential storage** (never in version control)
- **🚫 No personal data in logs**
- **🔒 Schema isolation** in dedicated database

### 🔐 API Key Management

```python
# Credentials are loaded from config/settings.py
# Never commit real API keys to version control
REDDIT_PUBLIC = "your-public-key"
REDDIT_SECRET = "your-secret-key"
SUPABASE_KEY = "your-service-role-key"
```

### 🛠️ Security Best Practices

- Use **read-only Reddit API** access
- Enable **PII anonymization** for all research
- **Rotate API keys** regularly
- **Monitor database access** logs

---

## 🎯 Use Cases

### 📚 Academic Research
- **Social media analysis** studies
- **Community behavior** research
- **Trend analysis** projects
- **Natural language processing** datasets

### 🏢 Business Intelligence
- **Competitor analysis** monitoring
- **Customer sentiment** tracking
- **Market research** automation
- **Brand monitoring** systems

### 🔬 Data Science
- **Machine learning** training data
- **Text analysis** pipelines
- **Network analysis** studies
- **Time series** forecasting

---

## 🤝 Contributing

We welcome contributions! Please see our [contributing guidelines](./docs/contributing/README.md) for details.

### 🔧 Development Setup

```bash
# Fork and clone
git clone https://github.com/your-username/redditharbor.git
cd redditharbor

# Setup development environment
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
uv pip install ruff  # Development dependency

# Run tests
PYTHONPATH=. python -m tests.test_full

# Check code quality
./lint.sh
```

### 📝 Contribution Process

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes with tests
4. **Run** `./lint.sh` to check code quality
5. **Commit** your changes (`git commit -m 'Add amazing feature'`)
6. **Push** to the branch (`git push origin feature/amazing-feature`)
7. **Open** a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Reddit API** for data access
- **Supabase** for database infrastructure
- **Ruff** for code quality management
- **PRAW** for Python Reddit API wrapper
- **spaCy** for natural language processing

---

## 📞 Support

- **📚 Documentation**: See [docs/](./docs/) directory
- **🐛 Issues**: [GitHub Issues](https://github.com/your-username/redditharbor/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/your-username/redditharbor/discussions)
- **📧 Email**: support@redditharbor.dev

---

<div align="center">

**Made with ❤️ by the RedditHarbor team**

![Built with CueTimer Colors](https://img.shields.io/badge/Style-CueTimer-FF6B35?style=flat-square)

</div>