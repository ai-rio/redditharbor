# Contributing to RedditHarbor

<div style="text-align: center; margin: 20px 0;">
  <h2 style="color: #FF6B35;">Join Our Community</h2>
  <p style="color: #004E89;">Help us build the best Reddit data collection toolkit</p>
</div>

## 🤝 Welcome!

Thank you for your interest in contributing to RedditHarbor! We welcome contributions from everyone, whether you're a seasoned developer or a beginner looking to get involved.

---

## 🚀 Quick Start for Contributors

### 1. Set Up Your Development Environment

```bash
# Fork the repository
git clone https://github.com/your-username/redditharbor.git
cd redditharbor

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt
pip install -e .
```

### 2. Make Your Changes

```bash
# Create a new branch
git checkout -b feature/your-feature-name

# Make your changes
# ... code changes ...

# Run tests
pytest tests/
```

### 3. Submit Your Contribution

```bash
# Commit your changes
git add .
git commit -m "feat: add your feature description"

# Push to your fork
git push origin feature/your-feature-name

# Create a pull request
```

---

## 📋 Ways to Contribute

### 🐛 Bug Reports

Found a bug? Please report it!

1. **Check existing issues** - Make sure it hasn't been reported
2. **Use our template** - Fill out the bug report template
3. **Provide details** - Include steps to reproduce, expected vs actual behavior
4. **Add logs** - Include any relevant error messages or logs

[📝 Report a Bug](https://github.com/your-org/redditharbor/issues/new?template=bug_report.md)

### 💡 Feature Requests

Have an idea for a new feature? We'd love to hear it!

1. **Check existing features** - Make sure it doesn't already exist
2. **Search issues** - See if someone else has suggested it
3. **Describe the use case** - Explain why this feature would be valuable
4. **Consider implementation** - If possible, suggest how it could be implemented

[💡 Suggest a Feature](https://github.com/your-org/redditharbor/issues/new?template=feature_request.md)

### 🔧 Code Contributions

We welcome code contributions in many areas:

#### Core Functionality
- **Data Collection** - New data sources, improved collection methods
- **Privacy Features** - Enhanced privacy protection, new anonymization techniques
- **Database Integration** - New database backends, optimization improvements
- **Performance** - Faster collection, better resource usage

#### Documentation
- **User Guides** - Tutorials, how-to guides, examples
- **API Documentation** - Function references, type annotations
- **Architecture Docs** - Design decisions, system documentation

#### Testing
- **Unit Tests** - Test individual components and functions
- **Integration Tests** - Test component interactions
- **Performance Tests** - Benchmark collection and processing

### 📝 Documentation

Help us improve our documentation:

- **Fix typos and grammar** - Even small improvements help!
- **Add examples** - Real-world usage examples
- **Write tutorials** - Step-by-step guides
- **Translate** - Help make RedditHarbor accessible to more people

### 🌐 Community

Join our community and help others:

- **Answer questions** - Help users on GitHub, Discord, or Reddit
- **Share your projects** - Show what you've built with RedditHarbor
- **Organize events** - Meetups, workshops, or hackathons
- **Mentor others** - Help new contributors get started

---

## 📏 Coding Standards

### Python Style Guide

We follow **PEP 8** with some additional conventions:

```python
# Good example
class RedditCollector:
    """Collect Reddit data with privacy features."""

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._session = None

    def collect_posts(self, subreddit: str, limit: int = 100) -> List[Dict]:
        """
        Collect posts from a subreddit.

        Args:
            subreddit: Name of the subreddit to collect from
            limit: Maximum number of posts to collect

        Returns:
            List of post data dictionaries

        Raises:
            APIError: If Reddit API request fails
            RateLimitError: If rate limit is exceeded
        """
        # Implementation here
        pass
```

#### Key Requirements

1. **Type Hints** - All functions must have type hints
2. **Docstrings** - All public functions and classes need docstrings
3. **Error Handling** - Proper exception handling throughout
4. **Testing** - All new features must include tests

### Code Quality Tools

We use these tools to maintain code quality:

```bash
# Linting
flake8 redditharbor/
black redditharbor/
isort redditharbor/

# Type checking
mypy redditharbor/

# Security
bandit -r redditharbor/

# Testing
pytest tests/ --cov=redditharbor
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_collector.py

# Run with coverage
pytest --cov=redditharbor

# Run integration tests
pytest tests/integration/
```

### Writing Tests

```python
import pytest
from unittest.mock import Mock, patch
from redditharbor import RedditCollector
from redditharbor.exceptions import APIError

class TestRedditCollector:
    def setup_method(self):
        """Set up test fixtures."""
        self.collector = RedditCollector(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )

    def test_init(self):
        """Test collector initialization."""
        assert self.collector.client_id == "test_client_id"
        assert self.collector.client_secret == "test_client_secret"

    @patch('redditharbor.collector.requests.get')
    def test_collect_posts_success(self, mock_get):
        """Test successful post collection."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {'data': {'children': []}}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test the method
        result = self.collector.collect_posts("test_subreddit")

        # Assertions
        assert isinstance(result, list)
        mock_get.assert_called_once()

    def test_collect_posts_invalid_subreddit(self):
        """Test error handling for invalid subreddit."""
        with pytest.raises(ValueError):
            self.collector.collect_posts("")
```

---

## 📝 Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Commit Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```bash
feat(collector): add rate limiting support

Implement rate limiting to respect Reddit API limits and prevent
temporary bans. This includes automatic backoff and retry logic.

Closes #123

fix(database): handle connection timeouts

Add proper error handling for database connection timeouts
and implement retry logic with exponential backoff.

docs(api): update authentication examples

Update the API documentation with new OAuth2 flow examples
and clarify credential requirements.

tests: add integration tests for privacy features

Add comprehensive integration tests to verify privacy
protection mechanisms are working correctly.
```

---

## 🔍 Code Review Process

### Review Checklist

When reviewing pull requests:

- [ ] **Functionality**: Does the code work as intended?
- [ ] **Tests**: Are there adequate tests? Do they pass?
- [ ] **Documentation**: Is the code well-documented?
- [ ] **Style**: Does it follow our style guidelines?
- [ ] **Security**: Are there any security concerns?
- [ ] **Performance**: Will this impact performance?
- [ ] **Breaking Changes**: Does this introduce breaking changes?

### Review Guidelines

1. **Be constructive** - Focus on improving the code
2. **Be thorough** - Check all aspects of the contribution
3. **Be respectful** - Remember that behind every PR is a person
4. **Ask questions** - If something isn't clear, ask for clarification

---

## 🎯 Areas Needing Help

### High Priority

- **🏃 Performance Optimization** - Improve collection speed and memory usage
- **🔐 Privacy Features** - Enhanced privacy protection and anonymization
- **📊 Analytics Integration** - Better support for data analysis workflows
- **🧪 Test Coverage** - Increase test coverage, especially for edge cases

### Medium Priority

- **📚 Documentation** - Improve user guides and API documentation
- **🔧 Plugin System** - Develop plugin architecture for extensibility
- **🌐 Internationalization** - Add support for multiple languages
- **📱 CLI Interface** - Command-line interface for easy usage

### Beginner Friendly

- **🐛 Bug Fixes** - Help fix reported issues
- **📝 Documentation** - Improve docs, fix typos, add examples
- **🧪 Tests** - Write tests for existing functionality
- **🔍 Issue Triage** - Help organize and label GitHub issues

---

## 🎉 Recognition

### Contributors Hall of Fame

We appreciate all contributions! Contributors are recognized in:

- **README.md** - Listed as contributors
- **Release Notes** - Mentioned in relevant releases
- **Community Spotlight** - Featured in blog posts and social media
- **Contributor Events** - Invited to special contributor events

### Types of Recognition

- **Code Contributors** - Pull requests merged
- **Issue Contributors** - Bug reports and feature requests
- **Documentation Contributors** - Documentation improvements
- **Community Contributors** - Helping other users

---

## 📞 Get in Touch

### Communication Channels

- **GitHub Issues** - Bug reports, feature requests, questions
- **GitHub Discussions** - General discussions, ideas, help
- **Discord** - Real-time chat with the community (invite link in README)
- **Email** - Private questions: contribute@redditharbor.org

### Response Times

- **Bug Reports**: 48 hours
- **Feature Requests**: 1 week
- **General Questions**: 72 hours
- **Pull Request Reviews**: 3-5 business days

---

## 📜 Code of Conduct

### Our Pledge

We are committed to making participation in our project a harassment-free experience for everyone, regardless of:

- Age, body size, disability, ethnicity, gender identity and expression
- Level of experience, education, socioeconomic status, nationality, personal appearance
- Race, religion, or sexual identity

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- Harassment, trolling, or offensive comments
- Personal attacks or political discussions
- Publishing private information without permission
- Any other conduct which could reasonably be considered inappropriate

### Enforcement

Project maintainers have the right and responsibility to remove, edit, or reject comments, commits, code, wiki edits, issues, and other contributions that are not aligned with this Code of Conduct.

---

## 🎯 Ready to Contribute?

<div style="background: #F7B801; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
  <h3 style="color: #1A1A1A; margin-top: 0;">🚀 Start Contributing Today!</h3>
  <p style="color: #1A1A1A; margin: 10px 0;">
    Check out our <a href="https://github.com/your-org/redditharbor/issues" style="color: #004E89; font-weight: bold;">good first issues</a> for beginner-friendly contributions.
  </p>
</div>

**Steps to get started:**

1. 🍴 **Fork** the repository
2. 🌿 **Clone** your fork locally
3. 🔧 **Set up** your development environment
4. 🐛 **Pick an issue** or create a new one
5. 💻 **Make your changes**
6. 🧪 **Test** your changes
7. 📤 **Submit** a pull request

---

<div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 2px solid #F5F5F5;">
  <p style="color: #666; font-size: 0.9em;">
    Thank you for contributing to RedditHarbor! Every contribution helps make this project better. 🙏
  </p>
</div>