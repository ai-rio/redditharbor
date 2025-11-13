#!/bin/bash
#
# Enhanced Chunks Test Execution Script
#
# Follows the RedditHarbor E2E Guide - Agent-Enhanced Processing
# Based on enhanced chunks documentation (chunks 1-3)
#
# Test Modes:
#   --quick: 5-minute validation (3 posts, basic checks)
#   --production: 10-minute test (10 posts, full pipeline)
#   --comprehensive: 15-minute deep analysis (25 posts, extensive validation)
#
# Usage:
#   ./run_enhanced_chunks_test.sh [--quick] [--production] [--comprehensive]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/home/carlos/projects/redditharbor"
TEST_DIR="$PROJECT_ROOT/tests/enhanced_chunks_validation"
LOG_DIR="$TEST_DIR/logs"

# Create log directory
mkdir -p "$LOG_DIR"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if Supabase is running
check_supabase() {
    print_status "Checking Supabase status..."

    if ! supabase status > /dev/null 2>&1; then
        print_status "Starting Supabase..."
        cd "$PROJECT_ROOT"
        supabase start
        print_success "Supabase started successfully"
    else
        print_success "Supabase is already running"
    fi
}

# Function to activate virtual environment
activate_venv() {
    print_status "Activating virtual environment..."
    cd "$PROJECT_ROOT"

    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        print_success "Virtual environment activated"
    else
        print_error "Virtual environment not found at .venv/bin/activate"
        exit 1
    fi
}

# Function to validate dependencies
validate_dependencies() {
    print_status "Validating Python dependencies..."

    python -c "
import sys
try:
    import dlt
    import praw
    from agent_tools.llm_profiler import LLMProfiler
    from core.trust_layer import TrustLayerValidator
    print('✅ All dependencies available')
except ImportError as e:
    print(f'❌ Missing dependency: {e}')
    sys.exit(1)
"

    if [ $? -eq 0 ]; then
        print_success "Dependencies validated"
    else
        print_error "Dependency validation failed"
        exit 1
    fi
}

# Function to run quick test
run_quick_test() {
    print_status "Running QUICK Enhanced Chunks Test (5-minute validation)..."

    cd "$PROJECT_ROOT"
    python "$TEST_DIR/comprehensive_test_runner.py" \
        --limit 3 \
        --score-threshold 40.0 \
        --test-mode \
        --output "$LOG_DIR/quick_test_results_$(date +%Y%m%d_%H%M%S).json"

    if [ $? -eq 0 ]; then
        print_success "Quick test completed successfully"
        return 0
    else
        print_error "Quick test failed"
        return 1
    fi
}

# Function to run production test
run_production_test() {
    print_status "Running PRODUCTION Enhanced Chunks Test (10-minute full pipeline)..."

    cd "$PROJECT_ROOT"
    python "$TEST_DIR/comprehensive_test_runner.py" \
        --limit 10 \
        --score-threshold 40.0 \
        --output "$LOG_DIR/production_test_results_$(date +%Y%m%d_%H%M%S).json"

    if [ $? -eq 0 ]; then
        print_success "Production test completed successfully"
        return 0
    else
        print_error "Production test failed"
        return 1
    fi
}

# Function to run comprehensive test
run_comprehensive_test() {
    print_status "Running COMPREHENSIVE Enhanced Chunks Test (15-minute deep analysis)..."

    cd "$PROJECT_ROOT"
    python "$TEST_DIR/comprehensive_test_runner.py" \
        --limit 25 \
        --score-threshold 40.0 \
        --output "$LOG_DIR/comprehensive_test_results_$(date +%Y%m%d_%H%M%S).json"

    if [ $? -eq 0 ]; then
        print_success "Comprehensive test completed successfully"
        return 0
    else
        print_error "Comprehensive test failed"
        return 1
    fi
}

# Function to verify database contents
verify_database() {
    print_status "Verifying database contents..."

    python -c "
from supabase import create_client
import json

# Connect to Supabase
supabase = create_client(
    'http://127.0.0.1:54321',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU'
)

# Check app_opportunities
opportunities = supabase.table('app_opportunities').select('*').execute()
print(f'AI Profiles in database: {len(opportunities.data)}')

if opportunities.data:
    print('Sample profiles:')
    for i, profile in enumerate(opportunities.data[:3]):
        score = profile.get('opportunity_score', 0)
        concept = profile.get('app_concept', 'N/A')[:50]
        trust_level = profile.get('trust_level', 'N/A')
        print(f'  {i+1}. Score: {score:.1f}, Trust: {trust_level}, Concept: {concept}...')
else:
    print('No AI profiles found in database')
"

    if [ $? -eq 0 ]; then
        print_success "Database verification completed"
    else
        print_warning "Database verification had issues"
    fi
}

# Function to show test results summary
show_results_summary() {
    print_status "Test Results Summary"

    # Find the most recent test results file
    latest_results=$(ls -t "$LOG_DIR"/test_run_*.log 2>/dev/null | head -1)

    if [ -n "$latest_results" ]; then
        echo "Most recent test log: $latest_results"

        # Extract key metrics from the log
        if grep -q "COMPLIANCE:" "$latest_results"; then
            compliance_line=$(grep "COMPLIANCE:" "$latest_results" | tail -1)
            echo "$compliance_line"
        fi

        if grep -q "Posts Collected:" "$latest_results"; then
            posts_collected=$(grep "Posts Collected:" "$latest_results" | tail -1 | awk '{print $3}')
            echo "Posts Collected: $posts_collected"
        fi

        if grep -q "Pass Rate:" "$latest_results"; then
            pass_rate=$(grep "Pass Rate:" "$latest_results" | tail -1 | awk '{print $3}')
            echo "Pass Rate: $pass_rate"
        fi
    fi

    # Check for JSON results
    latest_json=$(ls -t "$LOG_DIR"/*_test_results_*.json 2>/dev/null | head -1)
    if [ -n "$latest_json" ]; then
        echo "Detailed results: $latest_json"
    fi
}

# Function to display help
show_help() {
    echo "Enhanced Chunks Test Execution Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  --quick         Run 5-minute validation (3 posts, basic checks)"
    echo "  --production    Run 10-minute test (10 posts, full pipeline)"
    echo "  --comprehensive Run 15-minute deep analysis (25 posts, extensive validation)"
    echo "  --help          Show this help message"
    echo ""
    echo "This script follows the RedditHarbor E2E Guide with Agent-Enhanced Processing"
    echo "Based on enhanced chunks documentation (chunks 1-3)"
}

# Main execution logic
main() {
    echo "🚀 Enhanced Chunks Test Execution"
    echo "================================="
    echo ""

    # Parse command line arguments
    case "${1:-}" in
        --quick)
            test_mode="quick"
            ;;
        --production)
            test_mode="production"
            ;;
        --comprehensive)
            test_mode="comprehensive"
            ;;
        --help)
            show_help
            exit 0
            ;;
        "")
            test_mode="production"  # Default to production test
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac

    print_status "Running $test_mode Enhanced Chunks test"
    echo ""

    # Pre-test setup
    check_supabase
    activate_venv
    validate_dependencies

    echo ""
    print_status "Starting Enhanced Chunks validation..."
    echo ""

    # Run the appropriate test
    start_time=$(date +%s)

    case $test_mode in
        quick)
            if run_quick_test; then
                test_success=true
            else
                test_success=false
            fi
            ;;
        production)
            if run_production_test; then
                test_success=true
            else
                test_success=false
            fi
            ;;
        comprehensive)
            if run_comprehensive_test; then
                test_success=true
            else
                test_success=false
            fi
            ;;
    esac

    end_time=$(date +%s)
    duration=$((end_time - start_time))

    echo ""
    print_status "Test completed in ${duration} seconds"

    # Post-test verification
    if [ "$test_success" = true ]; then
        verify_database
        show_results_summary

        echo ""
        print_success "Enhanced Chunks test completed successfully! 🎉"

        # Show next steps
        echo ""
        print_status "Next Steps:"
        echo "  1. Review detailed logs in: $LOG_DIR/"
        echo "  2. Check Supabase Studio: http://127.0.0.1:54323"
        echo "  3. View test results JSON files for detailed metrics"
        echo "  4. Start dashboard: marimo run marimo_notebooks/opportunity_dashboard_fixed.py"
    else
        print_error "Enhanced Chunks test failed! ❌"
        echo ""
        print_status "Troubleshooting:"
        echo "  1. Check logs in: $LOG_DIR/"
        echo "  2. Verify Supabase is running: supabase status"
        echo "  3. Check Reddit API credentials"
        echo "  4. Review error messages in test output"
    fi

    exit 0
}

# Run main function
main "$@"