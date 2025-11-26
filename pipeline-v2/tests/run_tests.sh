#!/bin/bash
#
# Test Runner for Pipeline-v2 Quality Filter Migration
#
# Usage:
#   ./run_tests.sh                    # Run all tests
#   ./run_tests.sh baseline           # Run baseline tests only
#   ./run_tests.sh migration          # Run migration tests only
#   ./run_tests.sh cost-savings       # Run cost savings tests only
#   ./run_tests.sh fast               # Skip slow tests
#   ./run_tests.sh coverage           # Run with coverage report
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../../.." && pwd )"
TESTS_DIR="$SCRIPT_DIR"

# Ensure we're in project root
cd "$PROJECT_ROOT"

# Add project root to PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Pipeline-v2 Quality Filter Migration Test Suite            ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Project Root:${NC} $PROJECT_ROOT"
echo -e "${YELLOW}Tests Dir:${NC} $TESTS_DIR"
echo ""

# Function to run tests with specific marker
run_marker_tests() {
    local marker=$1
    local description=$2

    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Running: $description${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo ""

    pytest "$TESTS_DIR" -m "$marker" -v

    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ $description PASSED${NC}"
    else
        echo ""
        echo -e "${RED}✗ $description FAILED${NC}"
        return $exit_code
    fi
    echo ""
}

# Function to run specific test file
run_test_file() {
    local file=$1
    local description=$2

    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Running: $description${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo ""

    pytest "$TESTS_DIR/$file" -v

    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ $description PASSED${NC}"
    else
        echo ""
        echo -e "${RED}✗ $description FAILED${NC}"
        return $exit_code
    fi
    echo ""
}

# Parse command line arguments
COMMAND=${1:-all}

case $COMMAND in
    baseline)
        echo -e "${YELLOW}Mode: Baseline Tests Only${NC}"
        echo ""
        run_marker_tests "baseline" "Old System Baseline Tests"
        ;;

    migration)
        echo -e "${YELLOW}Mode: Migration Tests Only${NC}"
        echo ""
        run_marker_tests "migration" "Quality Filter Migration Tests"
        ;;

    cost-savings|cost)
        echo -e "${YELLOW}Mode: Cost Savings Tests Only${NC}"
        echo ""
        run_marker_tests "cost_savings" "Cost Savings Validation Tests"
        ;;

    fast)
        echo -e "${YELLOW}Mode: Fast Tests (skip slow tests)${NC}"
        echo ""
        pytest "$TESTS_DIR" -m "not slow" -v
        ;;

    coverage)
        echo -e "${YELLOW}Mode: All Tests with Coverage${NC}"
        echo ""
        pytest "$TESTS_DIR" \
            --cov=pipeline_v2.filters \
            --cov-report=html \
            --cov-report=term \
            -v

        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✓ Tests passed with coverage${NC}"
            echo -e "${YELLOW}Coverage report: htmlcov/index.html${NC}"
        fi
        ;;

    sequential)
        echo -e "${YELLOW}Mode: Sequential Test Execution${NC}"
        echo ""

        # Run tests in order
        run_test_file "test_old_system_baseline.py" "Old System Baseline"

        if [ $? -eq 0 ]; then
            run_test_file "test_quality_filter_migration.py" "Migration Validation"
        else
            echo -e "${RED}Baseline tests failed. Skipping migration tests.${NC}"
            exit 1
        fi

        if [ $? -eq 0 ]; then
            run_test_file "test_cost_savings_validation.py" "Cost Savings Validation"
        else
            echo -e "${RED}Migration tests failed. Skipping cost savings tests.${NC}"
            exit 1
        fi
        ;;

    verbose)
        echo -e "${YELLOW}Mode: Verbose Output (show print statements)${NC}"
        echo ""
        pytest "$TESTS_DIR" -v -s
        ;;

    all|*)
        echo -e "${YELLOW}Mode: All Tests${NC}"
        echo ""

        echo -e "${BLUE}Running complete test suite...${NC}"
        echo ""

        pytest "$TESTS_DIR" -v

        exit_code=$?

        echo ""
        echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
        if [ $exit_code -eq 0 ]; then
            echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
            echo ""
            echo -e "${GREEN}Migration Status: VALIDATED${NC}"
            echo -e "${GREEN}Production Ready: YES${NC}"
        else
            echo -e "${RED}✗ SOME TESTS FAILED${NC}"
            echo ""
            echo -e "${RED}Migration Status: NOT VALIDATED${NC}"
            echo -e "${RED}Production Ready: NO${NC}"
        fi
        echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
        echo ""

        exit $exit_code
        ;;
esac

# Final summary
exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✓ Test run completed successfully${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
else
    echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  ✗ Test run failed${NC}"
    echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
fi

exit $exit_code
