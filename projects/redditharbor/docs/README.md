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

### Development Documentation

- **[Contributing Guide](./contributing/README.md)** - How to contribute to RedditHarbor
- **[Project Setup](./guides/project-setup.md)** - Development environment setup
- **[Testing Guide](./guides/testing.md)** - Testing procedures and best practices

### Resources

- **[Images & Diagrams](./assets/images/)** - Visual assets and diagrams
- **[Examples](./assets/examples/)** - Code examples and sample implementations
- **[Changelog](CHANGELOG.md)** - Version history and changes

---

## 🎯 Key Features

- **Privacy-Preserving**: Built-in privacy features for responsible data collection
- **Database Integration**: Seamless integration with PostgreSQL and SQLite
- **Flexible Collection**: Support for posts, comments, user data, and more
- **Analytics Ready**: Structured data storage optimized for analysis
- **Error Handling**: Robust error handling and retry mechanisms

---

## 🏗️ Architecture

<div style="background: #F5F5F5; padding: 15px; border-radius: 8px; border-left: 4px solid #FF6B35; margin: 20px 0;">
  <p style="margin: 0; color: #1A1A1A;">
    <strong>RedditHarbor</strong> follows a modular architecture with separate components for data collection, processing, storage, and analysis. See the <a href="./architecture/README.md" style="color: #004E89;">Architecture Documentation</a> for detailed design decisions.
  </p>
</div>

---

## 📖 Getting Started

1. **Read the [Quick Start Guide](./guides/quick-start.md)** - Get up and running in minutes
2. **Explore [Examples](./assets/examples/)** - See RedditHarbor in action
3. **Check the [API Reference](./api/README.md)** - Detailed function documentation
4. **Join our [Community](./contributing/README.md)** - Connect with other users

---

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guide](./contributing/README.md) to get started.

<div style="background: #F7B801; padding: 10px; border-radius: 6px; margin: 15px 0; text-align: center;">
  <strong style="color: #1A1A1A;">Questions? Need Help?</strong><br>
  <span style="color: #1A1A1A;">Check our <a href="./guides/troubleshooting.md" style="color: #004E89;">Troubleshooting Guide</a> or <a href="./contributing/README.md" style="color: #004E89;">Contact Us</a></span>
</div>

---

<div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 2px solid #F5F5F5;">
  <p style="color: #666; font-size: 0.9em;">
    Built with ❤️ using <span style="color: #FF6B35;">CueTimer</span> branding
  </p>
</div>