#!/bin/bash
# ============================================================================
# Main Pipeline Characterization Test Runner
# Phase 5: TDD RED Phase Characterization Tests
# ============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test configuration
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$TEST_DIR")"
PIPELINE_DIR="$PROJECT_ROOT"
CHARACTERIZATION_TEST="$TEST_DIR/test_main_pipeline_characterization.py"
VALIDATION_TEST="$TEST_DIR/test_characterization_validation.py"

# Print header
echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║  Phase 5: Main Pipeline Integration Characterization Tests    ║${NC}"
echo -e "${PURPLE}║  TDD RED Phase - Comprehensive main.py characterization       ║${NC}"
echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"

echo -e "${BLUE}Project Root:${NC} $PROJECT_ROOT"
echo -e "${BLUE}Pipeline Directory:${NC} $PIPELINE_DIR"
echo -e "${BLUE}Tests Directory:${NC} $TEST_DIR"
echo -e "${BLUE}Characterization Test:${NC} $CHARACTERIZATION_TEST"

# Function to print colored status
print_status() {
    local status=$1
    local message=$2

    case $status in
        "PASS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "FAIL")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "WARN")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
        "HEADER")
            echo -e "${PURPLE}🔬 $message${NC}"
            ;;
    esac
}

# Function to check if test files exist
check_test_files() {
    print_status "HEADER" "Checking Test Files..."

    if [ ! -f "$CHARACTERIZATION_TEST" ]; then
        print_status "FAIL" "Characterization test not found: $CHARACTERIZATION_TEST"
        exit 1
    else
        print_status "PASS" "Characterization test found"
    fi

    if [ ! -f "$VALIDATION_TEST" ]; then
        print_status "FAIL" "Validation test not found: $VALIDATION_TEST"
        exit 1
    else
        print_status "PASS" "Validation test found"
    fi

    # Check for required modules
    print_status "INFO" "Checking required pipeline modules..."

    local modules=(
        "filters/quality.py"
        "deduplication/concept_tracker.py"
        "analysis/__init__.py"
        "trust/validator.py"
    )

    for module in "${modules[@]}"; do
        if [ ! -f "$PIPELINE_DIR/$module" ]; then
            print_status "FAIL" "Required module not found: $module"
            exit 1
        else
            print_status "PASS" "Module found: $module"
        fi
    done
}

# Function to run validation tests
run_validation_tests() {
    print_status "HEADER" "Running Validation Tests..."

    cd "$PIPELINE_DIR"

    if python3 "$VALIDATION_TEST"; then
        print_status "PASS" "All validation tests passed"
        return 0
    else
        print_status "FAIL" "Validation tests failed"
        return 1
    fi
}

# Function to test import strategy
test_import_strategy() {
    print_status "HEADER" "Testing Phase 4 Import Strategy..."

    cd "$PIPELINE_DIR"

    # Test individual imports
    local import_test_result=0

    # Test quality filters
    if python3 -c "
import sys
sys.path.insert(0, '.')
sys.path.insert(0, '..')
from filters.quality import should_analyze_with_ai, filter_submissions_batch
print('✅ Quality filters import successful')
    " 2>/dev/null; then
        print_status "PASS" "Quality filters import successful"
    else
        print_status "FAIL" "Quality filters import failed"
        import_test_result=1
    fi

    # Test deduplication
    if python3 -c "
import sys
sys.path.insert(0, '.')
sys.path.insert(0, '..')
from deduplication.concept_tracker import should_run_agno_analysis, should_run_profiler_analysis
print('✅ Deduplication import successful')
    " 2>/dev/null; then
        print_status "PASS" "Deduplication import successful"
    else
        print_status "FAIL" "Deduplication import failed"
        import_test_result=1
    fi

    # Test analysis wrapper
    if python3 -c "
import sys
sys.path.insert(0, '.')
sys.path.insert(0, '..')
from analysis import OpportunityAnalyzer
print('✅ Analysis wrapper import successful')
    " 2>/dev/null; then
        print_status "PASS" "Analysis wrapper import successful"
    else
        print_status "FAIL" "Analysis wrapper import failed"
        import_test_result=1
    fi

    # Test trust validator
    if python3 -c "
import sys
sys.path.insert(0, '.')
sys.path.insert(0, '..')
from trust.validator import TrustValidator
validator = TrustValidator(enable_ai_analysis=False)
print('✅ Trust validator import successful')
    " 2>/dev/null; then
        print_status "PASS" "Trust validator import successful"
    else
        print_status "FAIL" "Trust validator import failed"
        import_test_result=1
    fi

    return $import_test_result
}

# Function to test pipeline functionality
test_pipeline_functionality() {
    print_status "HEADER" "Testing Pipeline Functionality..."

    cd "$PIPELINE_DIR"

    # Test quality filtering
    if python3 -c "
import sys
import time
sys.path.insert(0, '.')
sys.path.insert(0, '..')
from filters.quality import should_analyze_with_ai, filter_submissions_batch

test_post = {
    'upvotes': 25,
    'num_comments': 12,
    'title': 'Problem with expensive workflow tool',
    'text': 'Looking for better alternative',
    'created_utc': time.time()
}

# Test individual filtering
should_analyze, score, reason = should_analyze_with_ai(test_post)
assert isinstance(should_analyze, bool)
assert isinstance(score, float)
assert isinstance(reason, str)
print('✅ Individual quality filtering works')

# Test batch filtering
passed, filtered = filter_submissions_batch([test_post])
assert len(passed) + len(filtered) == 1
print('✅ Batch quality filtering works')
    " 2>/dev/null; then
        print_status "PASS" "Quality filtering functionality works"
    else
        print_status "FAIL" "Quality filtering functionality failed"
        return 1
    fi

    # Test trust validation
    if python3 -c "
import sys
sys.path.insert(0, '.')
sys.path.insert(0, '..')
from trust.validator import TrustValidator

validator = TrustValidator(enable_ai_analysis=False)

submission_data = {
    'submission_id': 'test123',
    'title': 'Test submission',
    'subreddit': 'test',
    'upvotes': 10,
    'num_comments': 5,
    'created_utc': 1234567890
}

ai_analysis = {
    'final_score': 75.0,
    'core_functions': ['task_management'],
    'app_concept': 'Test app',
    'problem_description': 'Test problem'
}

trust_indicators = validator.validate_opportunity_trust(submission_data, ai_analysis)
assert hasattr(trust_indicators, 'overall_trust_score')
assert hasattr(trust_indicators, 'trust_level')
print('✅ Trust validation functionality works')
    " 2>/dev/null; then
        print_status "PASS" "Trust validation functionality works"
    else
        print_status "FAIL" "Trust validation functionality failed"
        return 1
    fi

    return 0
}

# Function to characterize test expectations
characterize_expectations() {
    print_status "HEADER" "Characterizing Test Expectations..."

    echo -e "${CYAN}📋 Pipeline Step Expectations:${NC}"
    echo "  Step 1: Reddit submission fetching (praw library)"
    echo "  Step 2: Pre-AI quality filtering (60% reduction in AI calls)"
    echo "  Step 3: Deduplication checking (70% cost reduction)"
    echo "  Step 4: AI analysis (mixed import strategy)"
    echo "  Step 5: Trust validation (6-dimensional scoring)"
    echo "  Step 6: DLT database loading (merge disposition)"

    echo -e "${CYAN}🎯 CLI Interface Expectations:${NC}"
    echo "  --limit: Maximum submissions to process (default: 10)"
    echo "  --subreddits: List of subreddits to fetch from"
    echo "  --score-threshold: Minimum trust score (default: 40.0)"
    echo "  --test-mode: Enable test mode with relaxed validation"

    echo -e "${CYAN}💰 Cost Savings Expectations:${NC}"
    echo "  Quality filtering: \$3,528/year at 10K posts/month"
    echo "  Deduplication: \$0.07 per duplicate submission"
    echo "  Total expected savings: ~\$4,200/year"

    echo -e "${CYAN}🚀 Performance Expectations:${NC}"
    echo "  Throughput: 5 submissions/minute (excluding AI time)"
    echo "  Batch processing: 10-50 submissions per batch"
    echo "  Memory usage: < 500MB for typical workload"

    print_status "PASS" "All expectations characterized"
}

# Function to display TDD RED phase summary
display_tdd_summary() {
    echo -e "\n${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                    TDD RED PHASE SUMMARY                       ║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"

    echo -e "${RED}🔴 CURRENT STATUS: TDD RED PHASE${NC}"
    echo -e "Characterization tests written and validated"
    echo -e "main.py implementation NOT yet started"
    echo -e "Tests expected to FAIL until main.py is implemented"

    echo -e "\n${GREEN}✅ NEXT STEPS:${NC}"
    echo -e "1. Implement main.py based on test specifications"
    echo -e "2. Tests will transition from RED to GREEN"
    echo -e "3. Refactor and optimize implementation"

    echo -e "\n${BLUE}📝 IMPLEMENTATION GUIDE:${NC}"
    echo -e "- Follow import strategy: pipeline_v2.* + core.agents.*"
    echo -e "- Implement 6-step pipeline flow"
    echo -e "- Add CLI argument parsing"
    echo -e "- Include comprehensive error handling"
    echo -e "- Add DLT database integration"

    echo -e "\n${YELLOW}⚠️  IMPORTANT NOTES:${NC}"
    echo -e "- Tests use NEW Phase 4 import strategy"
    echo -e "- Cost savings: \$4,200/year at 10K posts/month"
    echo -e "- Trust validation: 6-dimensional scoring"
    echo -e "- DLT merge disposition for database operations"
}

# Main execution
main() {
    local overall_result=0

    # Run all test phases
    check_test_files || exit 1
    run_validation_tests || overall_result=1
    test_import_strategy || overall_result=1
    test_pipeline_functionality || overall_result=1
    characterize_expectations

    # Display summary
    display_tdd_summary

    if [ $overall_result -eq 0 ]; then
        echo -e "\n${GREEN}🎉 ALL CHARACTERIZATION TESTS VALIDATED!${NC}"
        echo -e "${GREEN}🔴 READY FOR TDD RED PHASE: main.py implementation${NC}"
        exit 0
    else
        echo -e "\n${RED}❌ CHARACTERIZATION VALIDATION FAILED!${NC}"
        echo -e "${RED}🔧 Fix issues before implementing main.py${NC}"
        exit 1
    fi
}

# Run main function
main "$@"