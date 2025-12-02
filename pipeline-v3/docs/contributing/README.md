# Contributing to RedditHarbor Pipeline v3

<div align="center">

**Contributing Guidelines and Development Standards**

*Building clean Reddit data processing together*

</div>

## 📋 Table of Contents

- [🚀 Getting Started](#-getting-started)
- [🔧 Development Setup](#-development-setup)
- [📝 Code Standards](#-code-standards)
- [🧪 Testing Requirements](#-testing-requirements)
- [📚 Documentation Standards](#-documentation-standards)
- [🔄 Pull Request Process](#-pull-request-process)
- [🏷️ Issue Reporting](#️-issue-reporting)

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- UV package manager
- Git
- Supabase local instance
- Reddit API credentials

### Development Workflow
1. Fork the repository
2. Create feature branch
3. Make changes with proper testing
4. Submit pull request with clear description

---

## 🔧 Development Setup

### 1. Clone and Setup
```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/redditharbor-core-functions-fix.git
cd redditharbor-core-functions-fix/pipeline-v3

# Install dependencies
uv sync

# Set up pre-commit hooks
uv run pre-commit install
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 3. Development Services
```bash
# Start Supabase locally
supabase start

# Run database migrations
python -m pipeline_v3.scripts.init_database

# Verify setup
python -m pipeline_v3.scripts.check_schema
```

### 4. Development Commands
```bash
# Run pipeline in development mode
python -m pipeline_v3.main --subreddit productivity --limit 10 --debug

# Run tests
pytest tests/

# Lint and format
ruff check .
ruff format .
```

---

## 📝 Code Standards

### Style Guide
- **Language**: Python 3.9+
- **Formatter**: Ruff (Black-compatible)
- **Type Checking**: MyPy compatible annotations
- **Documentation**: Comprehensive docstrings

### Code Quality Tools
```bash
# Lint code
ruff check .

# Format code
ruff format .

# Type checking (if using mypy)
mypy pipeline_v3/

# Import sorting (handled by ruff)
ruff check --select I
```

### Code Structure
```
pipeline_v3/
├── extract/           # Data extraction layer
├── transform/         # Data transformation layer
├── load/             # Data loading layer
├── models/           # Pydantic models
├── config/           # Configuration management
└── scripts/          # Utility scripts
```

### Naming Conventions
- **Files**: kebab-case (e.g., `reddit-client.py`)
- **Classes**: PascalCase (e.g., `RedditExtractor`)
- **Functions**: snake_case (e.g., `extract_posts`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRIES`)

### Type Annotations
```python
from typing import List, Optional, Dict, Any

def extract_posts(
    subreddit: str,
    limit: int = 100,
    time_filter: str = "week"
) -> List[RedditPost]:
    """Extract posts from subreddit with rate limiting."""
    pass
```

### Docstring Format
```python
def analyze_content(
    content: str,
    analysis_type: str = "opportunity_detection"
) -> LLMAnalysisResult:
    """
    Analyze Reddit content for business opportunities.

    Args:
        content: Reddit post or comment content
        analysis_type: Type of analysis to perform

    Returns:
        Structured analysis result with confidence scores

    Raises:
        ValidationError: If content format is invalid
        APIError: If LLM API call fails
    """
    pass
```

---

## 🧪 Testing Requirements

### Test Structure
```
tests/
├── unit/             # Unit tests for individual components
├── integration/      # Integration tests for API connections
├── fixtures/         # Test data and fixtures
└── conftest.py       # Test configuration and fixtures
```

### Running Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=pipeline_v3 tests/

# Run specific test file
pytest tests/test_extract/test_reddit_client.py

# Run with verbose output
pytest -v tests/

# Run tests for specific module
pytest tests/ -k "test_extract"
```

### Test Requirements
- **Coverage**: Minimum 80% for new code
- **Unit Tests**: For all functions and classes
- **Integration Tests**: For external API connections
- **Mock Tests**: For external dependencies

### Example Test
```python
import pytest
from pipeline_v3.extract.reddit_client import RedditExtractor
from pipeline_v3.models import RedditPost

class TestRedditExtractor:
    """Test cases for Reddit data extraction."""

    @pytest.fixture
    def extractor(self):
        return RedditExtractor(
            client_id="test_id",
            client_secret="test_secret",
            user_agent="test_agent"
        )

    def test_extract_posts_success(self, extractor, mock_reddit):
        """Test successful post extraction."""
        posts = list(extractor.extract_posts("test_subreddit", limit=5))
        assert len(posts) <= 5
        assert all(isinstance(post, RedditPost) for post in posts)

    def test_rate_limiting(self, extractor, mock_reddit):
        """Test that rate limiting is enforced."""
        # Implementation test
        pass
```

### Mock Testing
```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_reddit():
    with patch('praw.Reddit') as mock:
        yield mock

def test_with_mock(mock_reddit):
    mock_reddit.return_value.subreddit.return_value.hot.return_value = [
        Mock(id="1", title="Test Post")
    ]
    # Test implementation
```

---

## 📚 Documentation Standards

### Documentation Files
- **User Guides**: Step-by-step tutorials in `docs/guides/`
- **API Documentation**: Interface documentation in `docs/api/`
- **Architecture**: System design in `docs/architecture/`
- **Implementation**: Technical details in `docs/implementation/`

### Documentation Style
- **Headers**: Use semantic HTML headers (`<h2>`, `<h3>`, etc.)
- **Code Blocks**: Specify language for syntax highlighting
- **Links**: Use relative links for internal documentation
- **Images**: Include alt text and descriptive captions

### Code Documentation
```python
class PipelineV3:
    """
    Main ELT pipeline orchestrator.

    This class coordinates the extract, transform, and load phases
    of the Reddit data processing pipeline with full type safety.

    Example:
        >>> pipeline = PipelineV3()
        >>> result = await pipeline.run_pipeline("productivity", limit=100)
        >>> print(f"Processed {result.opportunities_created} opportunities")
    """

    def __init__(self):
        """Initialize pipeline with configuration and clients."""
        pass
```

### README Updates
- Update relevant sections for new features
- Add new examples and use cases
- Update dependency requirements
- Include breaking changes notice

---

## 🔄 Pull Request Process

### 1. Branch Naming
```bash
# Feature branches
feature/new-extraction-method
feature/llm-analysis-improvements

# Bug fix branches
fix/rate-limiting-issue
fix/validation-error-handling

# Documentation branches
docs/api-documentation-update
```

### 2. Commit Messages
```
type(scope): description

feat(extract): add rate limiting for Reddit API
fix(transform): handle empty content validation
docs(readme): update setup instructions
test(load): add integration test for database
```

### 3. Pull Request Template
```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Coverage requirements met

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Breaking changes documented
```

### 4. Review Process
1. **Self-Review**: Review your own changes
2. **Automated Checks**: Ensure CI/CD passes
3. **Peer Review**: Request review from team members
4. **Merge**: Merge after approval

### 5. Merge Requirements
- **Approval**: At least one review approval
- **CI/CD**: All automated checks pass
- **Documentation**: Relevant docs updated
- **Tests**: New code has test coverage

---

## 🏷️ Issue Reporting

### Bug Reports
Use the bug report template:
```markdown
**Bug Description**
Clear description of the issue

**Steps to Reproduce**
1. Run command...
2. Input data...
3. Error occurs...

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., Ubuntu 20.04]
- Python: [e.g., 3.9.7]
- Dependencies: [version numbers]
```

### Feature Requests
Use the feature request template:
```markdown
**Feature Description**
Clear description of desired feature

**Problem Statement**
What problem this solves

**Proposed Solution**
How the feature should work

**Alternatives Considered**
Other approaches evaluated

**Additional Context**
Any relevant information
```

### Questions
- Use GitHub Discussions for questions
- Check existing documentation first
- Include relevant error messages
- Describe what you've tried

---

## 🎯 Contribution Areas

### High Priority Areas
- **Error Handling**: Improve error recovery mechanisms
- **Performance**: Optimize batch processing
- **Testing**: Add comprehensive test coverage
- **Documentation**: Fill documentation gaps

### Medium Priority Areas
- **Monitoring**: Add observability features
- **Configuration**: Improve configuration management
- **CLI Tools**: Enhance command-line interface
- **Docker**: Containerization support

### Community Guidelines
- **Be Respectful**: Maintain professional communication
- **Be Helpful**: Support other contributors
- **Be Constructive**: Focus on technical solutions
- **Be Inclusive**: Welcome contributors of all backgrounds

---

## 📞 Getting Help

### Resources
- **Documentation**: `/docs/` directory
- **Code Examples**: Check existing implementation
- **Tests**: See test files for usage examples
- **Issues**: Search existing GitHub issues

### Contact
- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Code Reviews**: Request help in pull requests

---

<div align="center">

**🤝 Thank you for contributing to RedditHarbor Pipeline v3!**

**Your contributions help make Reddit data processing better for everyone.**

</div>