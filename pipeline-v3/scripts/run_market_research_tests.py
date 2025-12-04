#!/usr/bin/env python3
"""
Test runner script for MarketResearchAgent tests
"""

import sys
import os
from pathlib import Path

# Add pipeline-v3 to Python path
pipeline_root = Path(__file__).parent
sys.path.insert(0, str(pipeline_root))

# Add project root to Python path
project_root = pipeline_root.parent
sys.path.insert(0, str(project_root))

# Set environment variables for testing
os.environ["TESTING"] = "true"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

# Import pytest and run
import pytest

if __name__ == "__main__":
    # Default test files
    test_files = [
        "tests/transform/test_market_research_agent_tdd.py",
        "tests/transform/test_market_research_agent_vcr.py",
        "tests/transform/test_market_research_performance.py",
        "tests/transform/test_agno_market_research_integration_fixed.py"
    ]

    # Get command line arguments
    args = sys.argv[1:]

    # If no args, run all tests with verbose output
    if not args:
        args = ["-v", "--tb=short"] + test_files
    elif not any(arg.endswith(".py") for arg in args):
        # If markers or options provided but no files, add our test files
        args.extend(test_files)

    # Run pytest
    sys.exit(pytest.main(args))