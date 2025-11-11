# Contributing to RedditHarbor

<div align="center">

**RedditHarbor Contribution Guide**

![RedditHarbor Logo](https://img.shields.io/badge/RedditHarbor-Contributing-FF6B35?style=for-the-badge&logoColor=white)

*Join us in building the future of Reddit opportunity discovery*

</div>

---

## 🚀 Welcome, Contributors!

We're excited that you're interested in contributing to RedditHarbor! This guide will help you get started with contributing to our project, whether you're fixing bugs, adding new features, improving documentation, or sharing ideas.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contribution Guidelines](#contribution-guidelines)
- [Code Standards](#code-standards)
- [Documentation Standards](#documentation-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Community Guidelines](#community-guidelines)

## 🛠️ Getting Started

### Prerequisites
- **Python 3.8+** - Primary development language
- **UV Package Manager** - For dependency management
- **Git** - Version control
- **GitHub Account** - For pull requests and issues
- **Discord/Slack** - For community communication (optional)

### Quick Start
1. **Fork the Repository** - Create your own fork on GitHub
2. **Clone Your Fork** - `git clone https://github.com/YOUR_USERNAME/redditharbor.git`
3. **Set Up Development Environment** - See [Development Setup](#development-setup)
4. **Create a Feature Branch** - `git checkout -b feature/your-feature-name`
5. **Make Your Changes** - Code, test, and document your changes
6. **Submit a Pull Request** - Follow our [Pull Request Process](#pull-request-process)

## 🏗️ Development Setup

### Environment Setup
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/redditharbor.git
cd redditharbor

# Install dependencies using UV
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Set up pre-commit hooks
uv run pre-commit install

# Run initial setup
uv run python core/setup.py
```

### Development Workflow
```bash
# Create a new feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ... write code ...

# Run linting and formatting
./lint.sh
# or
ruff check . && ruff format .

# Run tests
pytest tests/

# Commit your changes
git add .
git commit -m "feat: add your feature description"

# Push to your fork
git push origin feature/your-feature-name
```

## 📝 Contribution Guidelines

### Types of Contributions
We welcome various types of contributions:

#### 🐛 Bug Fixes
- Report bugs using [GitHub Issues](https://github.com/YOUR_USERNAME/redditharbor/issues)
- Include reproduction steps, expected behavior, and actual behavior
- Provide system information and error logs when possible

#### ✨ New Features
- Propose new features using [GitHub Issues](https://github.com/YOUR_USERNAME/redditharbor/issues) with the "enhancement" label
- Include use cases, implementation suggestions, and potential impact
- Consider breaking changes and backwards compatibility

#### 📚 Documentation
- Improve existing documentation for clarity and accuracy
- Add examples and tutorials for common use cases
- Translate documentation into other languages
- Fix typos and grammatical errors

#### 🧪 Testing
- Add unit tests for new functionality
- Improve test coverage for existing code
- Add integration tests for complex workflows
- Fix failing tests and improve test reliability

### Before You Start
1. **Check Existing Issues** - Search for similar issues or pull requests
2. **Discuss Large Changes** - Open an issue for discussion before starting major work
3. **Understand the Codebase** - Read our [architecture documentation](../architecture/)
4. **Follow Standards** - Review our [code standards](#code-standards) and [documentation standards](#documentation-standards)

## 🎯 Code Standards

### Python Code Quality
We use **ruff** for linting and formatting:

```bash
# Install development dependencies
uv sync --dev

# Run linting
ruff check .

# Run formatting
ruff format .

# Run both together (our lint.sh script)
./lint.sh
```

### Code Style Guidelines
- **PEP 8 Compliance** - Follow Python style guidelines
- **Type Hints** - Include type hints for all function parameters and returns
- **Docstrings** - Use comprehensive docstrings with Args, Returns, and Raises sections
- **Imports** - Use explicit imports and organize them properly
- **Variable Names** - Use descriptive, kebab-case for files and snake_case for variables

### Example Code Structure
```python
"""
Reddit data collection module with comprehensive error handling.

This module provides functionality for collecting Reddit data with
rate limiting, error recovery, and data validation.
"""

from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

def collect_reddit_data(
    subreddits: List[str],
    time_filter: str = "week",
    min_score: int = 10
) -> Optional[Dict[str, any]]:
    """
    Collect Reddit data from specified subreddits.

    Args:
        subreddits: List of subreddit names to collect from
        time_filter: Time filter for posts (day, week, month, year)
        min_score: Minimum score threshold for posts

    Returns:
        Dictionary containing collected data or None if failed

    Raises:
        ValueError: If invalid parameters provided
        ConnectionError: If Reddit API connection fails
    """
    try:
        # Implementation here
        pass
    except Exception as e:
        logger.error(f"Error collecting Reddit data: {e}")
        raise
```

### Architectural Guidelines
- **Modular Design** - Keep modules focused and single-purpose
- **Clean Architecture** - Respect separation between core, config, and scripts
- **Error Handling** - Implement comprehensive error handling with proper logging
- **Performance** - Optimize for memory usage and processing speed
- **Security** - Follow security best practices, especially for API keys and user data

## 📖 Documentation Standards

### Documentation Structure
Follow our [documentation organization](../README.md) standards:

```
docs/
├── api/           # API documentation
├── architecture/  # System architecture
├── guides/        # User guides and tutorials
├── implementation/ # Implementation details
└── technical/     # Technical specifications
```

### Writing Documentation
- **Use Markdown** - All documentation should be in Markdown format
- **kebab-case Filenames** - Use kebab-case for all documentation files
- **CueTimer Branding** - Use brand colors (#FF6B35, #004E89, #F7B801)
- **Code Examples** - Include practical, tested code examples
- **Clear Structure** - Use clear headings, lists, and navigation

### README Template
```markdown
# Feature Name

<div align="center">

**Brief Description**

![RedditHarbor Logo](https://img.shields.io/badge/RedditHarbor-Feature-FF6B35?style=for-the-badge&logoColor=white)

*One-sentence description*

</div>

---

## Overview
Brief description of the feature and its purpose.

## Usage
```python
# Code example
```

## Configuration
Configuration options and settings.

## Related Documentation
Links to related documentation.
```

## 🧪 Testing Requirements

### Test Coverage
- **Minimum 80% Coverage** - Aim for high test coverage
- **Unit Tests** - Test individual functions and classes
- **Integration Tests** - Test component interactions
- **End-to-End Tests** - Test complete workflows

### Writing Tests
```python
import pytest
from unittest.mock import Mock, patch
from core.collection import collect_data

class TestRedditDataCollection:
    """Test Reddit data collection functionality."""

    def test_collect_data_success(self):
        """Test successful data collection."""
        # Arrange
        subreddits = ["test", "example"]

        # Act
        result = collect_data(subreddits)

        # Assert
        assert result is not None
        assert len(result) > 0

    def test_collect_data_with_invalid_subreddit(self):
        """Test data collection with invalid subreddit."""
        # Arrange
        subreddits = ["invalid_subreddit_name_that_does_not_exist"]

        # Act & Assert
        with pytest.raises(ValueError):
            collect_data(subreddits)
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov-report=html

# Run specific test file
pytest tests/test_collection.py

# Run with verbose output
pytest -v
```

## 🔄 Pull Request Process

### Before Submitting
1. **Fork and Clone** - Fork the repository and clone your fork
2. **Create Feature Branch** - Use descriptive branch names
3. **Make Changes** - Implement your feature or fix
4. **Test Thoroughly** - Run all tests and add new ones if needed
5. **Update Documentation** - Update relevant documentation
6. **Lint Code** - Run `./lint.sh` to ensure code quality

### Pull Request Template
```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] Added new tests for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project standards
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### Pull Request Review Process
1. **Automated Checks** - CI/CD runs tests and linting
2. **Code Review** - Maintainers review code for quality and standards
3. **Documentation Review** - Ensure documentation is complete and accurate
4. **Testing Review** - Verify test coverage and quality
5. **Approval** - Maintainer approval required for merge

## 👥 Community Guidelines

### Our Values
- **Inclusivity** - Welcome contributors from all backgrounds
- **Collaboration** - Work together to build great software
- **Respect** - Treat everyone with respect and professionalism
- **Learning** - Encourage learning and knowledge sharing
- **Quality** - Maintain high standards for code and documentation

### Communication
- **GitHub Issues** - For bug reports and feature requests
- **Pull Requests** - For code reviews and discussions
- **Discord/Slack** - For real-time discussions and help
- **Email** - For private or sensitive topics

### Getting Help
- **Read Documentation** - Check existing documentation first
- **Search Issues** - Look for similar issues or discussions
- **Ask Questions** - Don't hesitate to ask for clarification
- **Be Patient** - Maintainers will respond as soon as possible

## 🏆 Recognition

### Contributor Recognition
- **Contributor List** - All contributors are acknowledged in our README
- **Release Notes** - Significant contributions are mentioned in release notes
- **Community Spotlight** - Outstanding contributors are highlighted in our community
- **Swag** - Active contributors may receive RedditHarbor swag and stickers

### Ways to Contribute
- **Code** - Write features, fix bugs, improve performance
- **Documentation** - Write docs, tutorials, and examples
- **Testing** - Write tests, improve test coverage, report bugs
- **Design** - UI/UX design, graphics, and visual improvements
- **Community** - Help others, answer questions, share ideas
- **Translation** - Translate documentation and interface text

## 📞 Contact & Support

### Getting Help
- **GitHub Issues** - For bug reports and feature requests
- **Discord Community** - For real-time help and discussions
- **Email** - For private questions and security concerns
- **Documentation** - Check our comprehensive documentation first

### Reporting Security Issues
- **Private Disclosure** - Report security issues privately
- **Email**: security@redditharbor.com
- **Responsible Disclosure** - We'll work with you to address issues responsibly

---

<div align="center">

**Thank you for contributing to RedditHarbor!** 🎉

*Your contributions help make Reddit opportunity discovery accessible to everyone.*

**Last Updated**: November 11, 2025
**Maintained by**: RedditHarbor Community Team

</div>