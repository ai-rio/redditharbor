"""Configuration for pytest in pipeline-v3.

This file ensures proper Python path configuration for all test imports
and provides common fixtures for the test suite.
"""

import os
import sys
from pathlib import Path

import pytest

# CRITICAL: Set up Python path BEFORE any imports to avoid conflicts
# The order is crucial: pipeline-v3 must be FIRST to avoid conflicts with other models

pipeline_root = Path(__file__).parent.parent.absolute()  # Go up to pipeline-v3 root

# Remove any existing references to avoid conflicts with project models
original_path = sys.path[:]
sys.path = [p for p in sys.path if not any([
    'models' in p and ('core' in p or 'trust' in p),
    'redditharbor-core-functions-fix' in p and p != str(pipeline_root)
])]

# Add pipeline-v3 root at the very beginning
sys.path.insert(0, str(pipeline_root))

# Ensure we still have the virtual environment paths
venv_paths = [p for p in original_path if '.venv' in p or 'site-packages' in p]
for p in venv_paths:
    if p not in sys.path:
        sys.path.append(p)

# Only add parent root if needed for specific cross-imports (avoid conflicts)
parent_root = pipeline_root.parent.absolute()
# Commenting this out to prevent conflicts with other models in the parent project
# if str(parent_root) not in sys.path:
#     sys.path.append(str(parent_root))

# Set environment variables for testing
os.environ.setdefault('PYTHONPATH', str(pipeline_root))

def pytest_configure(config):
    """Called after command line options have been parsed."""
    print("\n=== Pipeline v3 Test Configuration ===")
    print(f"Pipeline root: {pipeline_root}")
    print(f"Parent root: {parent_root}")
    print(f"Working directory: {Path.cwd()}")

    # Show python path (first few entries)
    print(f"Python path (first 5): {sys.path[:5]}")

    # Verify model imports work
    try:
        import models
        print(f"✓ Models module: {models.__file__}")
        print(f"✓ Available models: {models.__all__}")

        # Test that all required models can be imported
        for model_name in ['AnalysisResult', 'AppIdea', 'MarketMetrics', 'RedditSubmission']:
            model = getattr(models, model_name, None)
            if model:
                print(f"  ✓ {model_name}: {model}")
            else:
                print(f"  ✗ {model_name}: NOT FOUND")

    except ImportError as e:
        print(f"✗ Failed to import models: {e}")
        print(f"✗ sys.path: {sys.path}")

def pytest_collection_modifyitems(config, items):
    """Called after collection has been performed."""
    print("\n=== Test Collection Summary ===")
    print(f"Total tests collected: {len(items)}")

    # Group tests by module for better organization
    modules = {}
    for item in items:
        module = item.module.__name__
        if module not in modules:
            modules[module] = []
        modules[module].append(item.name)

    for module, test_names in sorted(modules.items()):
        print(f"  {module}: {len(test_names)} tests")

def pytest_report_header(config):
    """Called when generating test report header."""
    return f"Pipeline v3 Python Path: {sys.path[0]}"

# Common test fixtures
@pytest.fixture
def sample_reddit_submission():
    """Sample Reddit submission for testing."""
    from models import RedditSubmission
    return RedditSubmission(
        id="test123",
        title="Test Submission",
        content="This is a test submission content",
        author="test_user",
        subreddit="test_subreddit",
        score=100,
        num_comments=25,
        created_at="2024-01-01T00:00:00Z",
        url="https://reddit.com/r/test/test123",
        metadata={"test": True}
    )

@pytest.fixture
def sample_app_idea():
    """Sample app idea for testing."""
    from models import AppIdea
    return AppIdea(
        title="Test App",
        description="A test application idea",
        target_audience="developers",
        problem_solved="Testing issues",
        unique_value="Test value proposition",
        market_potential="high",
        development_complexity="medium",
        estimated_timeline="3 months"
    )
