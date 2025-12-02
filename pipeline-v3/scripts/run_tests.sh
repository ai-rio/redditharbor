#!/bin/bash

# Pipeline v3 Test Runner
# This script runs all pipeline-v3 tests with proper PYTHONPATH configuration

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../" && pwd)"

echo "=== Pipeline v3 Test Suite ==="
echo "Pipeline directory: $SCRIPT_DIR"
echo "Project root: $PROJECT_ROOT"
echo ""

# Count total test files
TEST_FILES=$(find "$SCRIPT_DIR/tests" -name "test_*.py" -type f | wc -l)
echo "Found $TEST_FILES test files"
echo ""

# Run all tests with pytest
cd "$PROJECT_ROOT"
PYTHONPATH="$SCRIPT_DIR" /home/carlos/projects/redditharbor-core-functions-fix/.venv/bin/python3 -m pytest $(find "$SCRIPT_DIR/tests" -name "test_*.py" -type f) --no-cov "$@"

echo ""
echo "=== Test Summary ==="
echo "All tests completed!"