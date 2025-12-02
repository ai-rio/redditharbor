#!/bin/bash
"""
Run script wrapper for Test 02 Small Batch Validation

This script activates the Python virtual environment and runs Test 02
with the appropriate command line arguments.

Usage:
    ./run_test_02_small_batch.sh                    # Basic run
    ./run_test_02_small_batch.sh --monetization     # With monetization enabled
    ./run_test_02_small_batch.sh --update-config    # Update config with real IDs
    ./run_test_02_small_batch.sh --verbose          # Verbose output
"""

set -e  # Exit on error

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../" && pwd)"

echo "RedditHarbor Test 02: Small Batch Validation"
echo "============================================"
echo "Project Root: $PROJECT_ROOT"
echo "Test Script: $SCRIPT_DIR/tests/test_02_small_batch.py"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Activate virtual environment
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "Error: Virtual environment not found at .venv"
    echo "Please run: uv sync"
    exit 1
fi

# Run the test
echo "Running Test 02 Small Batch Validation..."
echo "Command: python scripts/testing/integration/tests/test_02_small_batch.py $@"
echo ""

python scripts/testing/integration/tests/test_02_small_batch.py "$@"

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "✅ Test 02 completed successfully"
else
    echo "❌ Test 02 failed with exit code $exit_code"
fi

exit $exit_code