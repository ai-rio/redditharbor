# Python Script Organization Best Practices

<div style="text-align: center; margin: 20px 0;">
  <h2 style="color: #FF6B35;">Structuring Python Projects</h2>
  <p style="color: #004E89;">Best practices for organizing Python scripts and projects</p>
</div>

## 📋 Overview

This guide summarizes the best practices for organizing Python scripts and projects, based on authoritative sources including the Python Guide, Real Python, and Dagster's Python engineering resources. These practices will help you create maintainable, scalable, and collaborative-friendly Python projects.

---

## 🎯 Why Organization Matters

### Benefits of Proper Organization

1. **Simplified Development** - Focus on one module at a time
2. **Better Maintainability** - Easier to update and modify code
3. **Enhanced Reusability** - Modules can be reused across projects
4. **Reduced Duplication** - Share functionality without copying code
5. **Namespace Management** - Avoid naming conflicts between modules
6. **Team Collaboration** - Multiple developers can work simultaneously
7. **Testing Efficiency** - Easier to test isolated components

---

## 📁 Recommended Project Structures

### 1. Basic Single Script

For simple projects with one main script:

```
project-name/
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
├── script_name.py
└── tests.py
```

**When to use:**
- Simple utility scripts
- Personal projects
- Proof of concepts
- Educational exercises

### 2. Installable Single Package

For projects that can be distributed:

```
project-name/
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
├── setup.py
├── project_name/
│   ├── __init__.py
│   ├── main.py
│   └── helpers.py
└── tests/
    ├── main_tests.py
    └── helpers_tests.py
```

**When to use:**
- Distributable packages
- Libraries for others to use
- Medium-sized applications
- Open source projects

### 3. Application with Internal Packages

For complex applications with multiple components:

```
project-name/
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
├── setup.py
├── bin/
│   └── executable_script
├── docs/
├── project_name/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── database.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── helpers.py
│   └── modules/
│       ├── __init__.py
│       ├── module1.py
│       └── module2.py
├── data/
├── tests/
│   ├── test_core/
│   ├── test_utils/
│   └── test_modules/
└── assets/
```

**When to use:**
- Large applications
- Multi-component systems
- Team development projects
- Enterprise applications

---

## 🏗️ 9 Essential Best Practices

### 1. **Organize Your Code**

Create separate folders for different project parts:

```python
# Recommended directory structure
project/
├── src/              # Source code
├── tests/            # Test files
├── docs/             # Documentation
├── data/             # Data files
├── config/           # Configuration files
└── scripts/          # Utility scripts
```

### 2. **Use Consistent Naming**

Follow Python naming conventions:

```python
# ✅ GOOD
import module_name
from package import function_name
from module import ClassName

# ❌ BAD
import Module-Name
from package import FunctionName
```

**File Naming:**
- Use `kebab-case` for documentation: `user-guide.md`
- Use `snake_case` for Python modules: `user_auth.py`
- Use `PascalCase` for classes: `UserAuthenticator`

### 3. **Use Version Control**

Even for solo projects, use Git:

```bash
# Initialize repository
git init
git add .
git commit -m "Initial commit"

# Remote setup
git remote add origin <repository-url>
git push -u origin main
```

**Essential files for Git:**
```bash
# .gitignore
__pycache__/
*.pyc
.env
venv/
.venv/
*.egg-info/
dist/
```

### 4. **Use Package Managers**

Manage dependencies properly:

```bash
# Modern approach (recommended)
pip install -r requirements.txt

# Alternative: pipenv
pipenv install
pipenv install requests

# Alternative: poetry
poetry add requests
poetry install
```

**requirements.txt example:**
```
requests==2.31.0
pandas>=2.0.0
numpy>=1.24.0
python-dotenv>=1.0.0
```

### 5. **Create Virtual Environments**

Isolate project dependencies:

```bash
# Create virtual environment
python -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 6. **Comment Your Code**

Write clear, useful documentation:

```python
def extract_data(source_db: str, table_name: str) -> pd.DataFrame:
    """
    Extract data from a database table.

    Args:
        source_db: Path to the source database
        table_name: Name of the table to extract

    Returns:
        DataFrame containing the extracted data

    Raises:
        DatabaseConnectionError: If connection fails
    """
    # Implementation here
    pass
```

### 7. **Test, Test, Test**

Implement comprehensive testing:

```python
# tests/test_data_extraction.py
import unittest
import pandas as pd
from src.data_extraction import extract_data

class TestDataExtraction(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_database.db"
        self.test_table = "test_table"

    def test_extract_data_success(self):
        """Test successful data extraction."""
        result = extract_data(self.test_db, self.test_table)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertFalse(result.empty)

    def test_extract_data_missing_table(self):
        """Test extraction with missing table."""
        with self.assertRaises(ValueError):
            extract_data(self.test_db, "nonexistent_table")

if __name__ == "__main__":
    unittest.main()
```

### 8. **Lint and Style**

Maintain code quality with automated tools:

```bash
# Install linting tools
pip install black flake8 isort mypy

# Format code
black src/ tests/

# Check style
flake8 src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/
```

**pyproject.toml configuration:**
```toml
[tool.black]
line-length = 88
target-version = ['py38']

[tool.isort]
profile = "black"
multi_line_output = 3

[tool.flake8]
max-line-length = 88
extend-ignore = ["E203", "W503"]
```

### 9. **Package to Share**

Make your code distributable:

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="your-package-name",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "pandas>=2.0.0"
    ],
    python_requires=">=3.8",
    author="Your Name",
    author_email="your.email@example.com",
    description="A brief description of your package",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/your-package",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
```

---

## 🗂️ File Organization Patterns

### Module Organization

```python
# Good module structure
src/
├── __init__.py
├── config.py          # Configuration and constants
├── database.py        # Database operations
├── data_extraction.py # Data extraction logic
├── data_transformation.py # Data transformation
├── data_loading.py    # Data loading
└── utils.py           # Utility functions
```

### Import Best Practices

```python
# ✅ GOOD - Grouped and ordered
import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np

from local_module import local_function
from .local_module import another_function

# ❌ BAD - Unordered and mixed
import sys
import pandas as pd
from local_module import local_function
import os
from .local_module import another_function
import numpy as np
```

### Configuration Management

```python
# config.py
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseConfig:
    host: str
    port: int
    database: str
    username: str
    password: str

    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        return cls(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME'),
            username=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )

@dataclass
class AppConfig:
    database: DatabaseConfig
    log_level: str = 'INFO'
    max_retries: int = 3

    @classmethod
    def load(cls, config_file: Optional[Path] = None) -> 'AppConfig':
        database_config = DatabaseConfig.from_env()
        return cls(database=database_config)
```

---

## 🧪 Testing Structure

### Test Organization

```
tests/
├── __init__.py
├── conftest.py          # Pytest configuration and fixtures
├── test_data_extraction.py
├── test_data_transformation.py
├── test_data_loading.py
├── fixtures/            # Test data and fixtures
│   ├── sample_data.csv
│   └── test_database.db
└── integration/         # Integration tests
    ├── test_end_to_end.py
    └── test_api_integration.py
```

### Fixtures and Setup

```python
# tests/conftest.py
import pytest
import pandas as pd
from pathlib import Path

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['Alice', 'Bob', 'Charlie'],
        'value': [10.5, 20.3, 15.7]
    })

@pytest.fixture
def temp_database(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.db"
    # Create test database
    yield db_path
    # Cleanup happens automatically
```

---

## 📚 Documentation Standards

### README.md Structure

```markdown
# Project Name

Short description of what the project does.

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

```bash
git clone <repository-url>
cd project-name
pip install -r requirements.txt
```

## Usage

```python
from project_name import main_function

result = main_function("parameter")
print(result)
```

## Testing

```bash
python -m pytest tests/
```

## Contributing

Guidelines for contributing.

## License

This project is licensed under the MIT License.
```

### Code Documentation

```python
def complex_function(param1: str, param2: int, *, optional_param: bool = False) -> dict:
    """
    Perform a complex operation with the given parameters.

    This function demonstrates proper docstring formatting according to
    PEP 257. It includes detailed descriptions, type hints, and examples.

    Args:
        param1: Description of the first parameter
        param2: Description of the second parameter
        optional_param: Description of optional parameter

    Returns:
        A dictionary containing the operation results

    Raises:
        ValueError: If param1 is empty or param2 is negative
        TypeError: If parameters are of incorrect type

    Example:
        >>> result = complex_function("hello", 42, optional_param=True)
        >>> print(result['status'])
        'success'
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
    if param2 < 0:
        raise ValueError("param2 cannot be negative")

    # Implementation here
    return {"status": "success", "input": f"{param1}_{param2}"}
```

---

## 🔧 Development Workflow

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3.8

  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

### GitHub Actions CI/CD

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Lint with flake8
      run: |
        flake8 src tests

    - name: Type check with mypy
      run: |
        mypy src

    - name: Test with pytest
      run: |
        pytest tests/ --cov=src --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
```

---

## 🎯 Applying to RedditHarbor

### Current Structure Analysis

The RedditHarbor project follows many of these best practices:

✅ **Strengths:**
- Virtual environment usage
- Clear separation of concerns
- Proper documentation
- Configuration management
- Comprehensive testing

🔧 **Areas for Improvement:**
- Add pre-commit hooks
- Implement CI/CD pipeline
- Enhance type hints
- Add integration tests
- Improve error handling

### Recommended Enhancements

1. **Add Type Hints:**
```python
from typing import Dict, List, Optional, Union
import pandas as pd

def collect_subreddit_data(
    subreddit: str,
    limit: int,
    sort_by: str = "hot"
) -> List[Dict[str, Union[str, int]]]:
    """Collect subreddit data with proper type hints."""
    pass
```

2. **Improve Configuration:**
```python
# Enhanced config.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class RedditConfig:
    client_id: str
    client_secret: str
    user_agent: str
    rate_limit: int = 60

    @classmethod
    def from_env(cls) -> 'RedditConfig':
        import os
        from dotenv import load_dotenv
        load_dotenv()

        return cls(
            client_id=os.getenv('REDDIT_CLIENT_ID', ''),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET', ''),
            user_agent=os.getenv('REDDIT_USER_AGENT', 'RedditHarbor/1.0')
        )
```

---

## 📖 Additional Resources

### Documentation References

- [Python Guide: Structuring Your Project](https://docs.python-guide.org/writing/structure/)
- [Real Python: Application Layouts](https://realpython.com/python-application-layouts/)
- [Dagster: Python Project Best Practices](https://dagster.io/blog/python-project-best-practices/)

### Tools and Libraries

- **Code Formatting:** [Black](https://black.readthedocs.io/), [isort](https://isort.readthedocs.io/)
- **Linting:** [Flake8](https://flake8.pycqa.org/), [Ruff](https://github.com/charliermarsh/ruff)
- **Type Checking:** [MyPy](https://mypy.readthedocs.io/)
- **Testing:** [pytest](https://pytest.org/), [unittest](https://docs.python.org/3/library/unittest.html)
- **Documentation:** [Sphinx](https://www.sphinx-doc.org/), [MkDocs](https://www.mkdocs.org/)

---

<div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 2px solid #F5F5F5;">
  <p style="color: #666; font-size: 0.9em;">
    Following these best practices will help you create maintainable, scalable, and collaborative Python projects! 🚀
  </p>
</div>