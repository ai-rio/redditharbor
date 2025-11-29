#!/bin/bash

# Pipeline v3 Test Runner - Fixed Version
# This script runs all pipeline-v3 tests with proper configuration

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../" && pwd)"
VENV_PYTHON="/home/carlos/projects/redditharbor-core-functions-fix/.venv/bin/python3"

echo "=== Pipeline v3 Test Suite ==="
echo "Pipeline directory: $SCRIPT_DIR"
echo "Project root: $PROJECT_ROOT"
echo "Python executable: $VENV_PYTHON"
echo ""

# Check if we're in the right directory
if [[ ! -f "$SCRIPT_DIR/pyproject.toml" ]]; then
    echo "Error: pyproject.toml not found in $SCRIPT_DIR"
    exit 1
fi

# Run tests from within the pipeline-v3 directory to ensure proper import paths
cd "$SCRIPT_DIR"

echo "Running tests from: $(pwd)"
echo ""

# Try approach 1: Run from pipeline directory
cd "$SCRIPT_DIR"
echo "Method 1: Running tests from pipeline directory..."
if "$VENV_PYTHON" -m pytest tests/ --collect-only -q 2>/dev/null | grep -q "3 errors"; then
    echo "Method 1 failed due to import conflicts, trying Method 2..."

    # Method 2: Use the working explicit approach from project root
    cd "$PROJECT_ROOT"
    echo "Method 2: Running tests from project root with explicit paths..."

    # Separate problematic tests from working tests
    WORKING_TESTS=(
        "$SCRIPT_DIR/tests/test_models.py"
        "$SCRIPT_DIR/tests/test_config.py"
        "$SCRIPT_DIR/tests/test_extract.py"
        "$SCRIPT_DIR/tests/test_infrastructure.py"
        "$SCRIPT_DIR/tests/test_database_loader.py"
        "$SCRIPT_DIR/tests/test_extract_fixed.py"
        "$SCRIPT_DIR/tests/test_extract_comprehensive.py"
    )

    PROBLEMATIC_TESTS=(
        "$SCRIPT_DIR/tests/test_opportunity_analyzer.py"
        "$SCRIPT_DIR/tests/test_pipeline_integration.py"
        "$SCRIPT_DIR/tests/test_vector_similarity.py"
    )

    # Run working tests first
    echo "Running working tests..."
    PYTHONPATH="$SCRIPT_DIR" "$VENV_PYTHON" -m pytest "${WORKING_TESTS[@]}" -v "$@"
    WORKING_EXIT_CODE=$?

    echo ""
    echo "Running problematic tests with separate import path..."

    # Run problematic tests separately with more controlled environment
    cd "$PROJECT_ROOT"
    for test_file in "${PROBLEMATIC_TESTS[@]}"; do
        echo "Running $(basename "$test_file")..."
        PYTHONPATH="$SCRIPT_DIR" "$VENV_PYTHON" -m pytest "$test_file" -v "$@"
        EXIT_CODE=$?
        if [ $EXIT_CODE -ne 0 ]; then
            PROBLEMATIC_EXIT_CODE=$EXIT_CODE
        fi
    done

    # Combined exit code
    FINAL_EXIT_CODE=${PROBLEMATIC_EXIT_CODE:-$WORKING_EXIT_CODE}
else
    echo "Method 1 succeeded, running all tests..."
    "$VENV_PYTHON" -m pytest tests/ -v "$@"
    FINAL_EXIT_CODE=$?
fi

echo ""
echo "=== Test Summary ==="
echo "All tests completed!"

# Exit with appropriate code
exit ${FINAL_EXIT_CODE:-0}

# Alternative method if the above fails:
# Method 1: From project root with explicit PYTHONPATH
# cd "$PROJECT_ROOT" && PYTHONPATH="$SCRIPT_DIR" "$VENV_PYTHON" -m pytest "$SCRIPT_DIR/tests/" -v "$@"

# Method 2: Using specific test files (original approach)
# cd "$PROJECT_ROOT" && PYTHONPATH="$SCRIPT_DIR" "$VENV_PYTHON" -m pytest \
#     "$SCRIPT_DIR/tests/test_models.py" \
#     "$SCRIPT_DIR/tests/test_config.py" \
#     "$SCRIPT_DIR/tests/test_extract.py" \
#     "$SCRIPT_DIR/tests/test_infrastructure.py" \
#     "$SCRIPT_DIR/tests/test_database_loader.py" \
#     "$SCRIPT_DIR/tests/test_extract_fixed.py" \
#     "$SCRIPT_DIR/tests/test_extract_comprehensive.py" \
#     "$SCRIPT_DIR/tests/test_opportunity_analyzer.py" \
#     "$SCRIPT_DIR/tests/test_pipeline_integration.py" \
#     "$SCRIPT_DIR/tests/test_vector_similarity.py" \
#     -v "$@"