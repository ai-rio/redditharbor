#!/bin/bash
# RedditHarbor Phase 5 Deployment Verification Script
# =====================================================
#
# This script verifies that a Phase 5 deployment is healthy and ready for production.
# It performs comprehensive checks including health endpoints, external APIs,
# database connectivity, and performance validation.

set -euo pipefail

# Configuration defaults
NAMESPACE=${NAMESPACE:-production}
TIMEOUT=${TIMEOUT:-300}
PERFORMANCE_TEST=${PERFORMANCE_TEST:-true}
VERBOSE=${VERBOSE:-false}
FAIL_ON_WARNINGS=${FAIL_ON_WARNINGS:-false}
OUTPUT_FORMAT=${OUTPUT_FORMAT:-table}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
PASSED_TESTS=0
FAILED_TESTS=0
WARNING_TESTS=0

# Logging functions
log() {
    if [[ "$VERBOSE" == "true" ]] || [[ "${1^^}" == "ERROR" ]] || [[ "${1^^}" == "FAIL" ]]; then
        echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $2"
    fi
}

pass() {
    echo -e "${GREEN}✓ PASS${NC} $1"
    ((PASSED_TESTS++))
}

fail() {
    echo -e "${RED}✗ FAIL${NC} $1"
    ((FAILED_TESTS++))
}

warn() {
    echo -e "${YELLOW}⚠ WARN${NC} $1"
    if [[ "$FAIL_ON_WARNINGS" == "true" ]]; then
        ((FAILED_TESTS++))
    else
        ((WARNING_TESTS++))
    fi
}

# Test result summary
show_summary() {
    local total=$((PASSED_TESTS + FAILED_TESTS + WARNING_TESTS))
    local status="SUCCESS"

    if [[ $FAILED_TESTS -gt 0 ]]; then
        status="FAILED"
    elif [[ $WARNING_TESTS -gt 0 ]] && [[ "$FAIL_ON_WARNINGS" == "true" ]]; then
        status="FAILED"
    elif [[ $WARNING_TESTS -gt 0 ]]; then
        status="WARNING"
    fi

    echo ""
    echo "=== Verification Summary ==="
    echo "Total Tests: $total"
    echo "Passed: $PASSED_TESTS"
    echo "Failed: $FAILED_TESTS"
    echo "Warnings: $WARNING_TESTS"
    echo "Status: $status"
    echo ""

    if [[ "$status" == "FAILED" ]]; then
        echo -e "${RED}Deployment verification FAILED!${NC}"
        exit 1
    elif [[ "$status" == "WARNING" ]]; then
        echo -e "${YELLOW}Deployment verification completed with WARNINGS${NC}"
        exit 0
    else
        echo -e "${GREEN}Deployment verification SUCCESSFUL!${NC}"
        exit 0
    fi
}

# Test 1: Check if deployment exists
test_deployment_exists() {
    log "INFO" "Checking if RedditHarbor deployment exists..."

    if kubectl get deployment redditharbor-agno -n "$NAMESPACE" &> /dev/null; then
        pass "Deployment 'redditharbor-agno' exists in namespace '$NAMESPACE'"

        # Check replica count
        REPLICAS=$(kubectl get deployment redditharbor-agno -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
        READY=$(kubectl get deployment redditharbor-agno -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')

        log "INFO" "Replicas: $READY/$REPLICAS ready"

        if [[ "$READY" -eq "$REPLICAS" ]] && [[ "$READY" -gt 0 ]]; then
            pass "All replicas are ready"
        else
            fail "Not all replicas are ready ($READY/$REPLICAS)"
        fi
    else
        fail "Deployment 'redditharbor-agno' not found in namespace '$NAMESPACE'"
    fi
}

# Test 2: Check pod health
test_pod_health() {
    log "INFO" "Checking pod health status..."

    # Get pods with their status
    kubectl get pods -n "$NAMESPACE" -l app=redditharbor-agno -o wide

    # Check for non-running pods
    NON_RUNNING=$(kubectl get pods -n "$NAMESPACE" -l app=redditharbor-agno \
        --field-selector=status.phase!=Running --no-headers | wc -l)

    if [[ "$NON_RUNNING" -eq 0 ]]; then
        pass "All pods are running"
    else
        fail "$NON_RUNNING pods are not running"
    fi

    # Check for failing pods
    FAILING=$(kubectl get pods -n "$NAMESPACE" -l app=redditharbor-agno \
        -o jsonpath='{range .items[*]}{.status.phase}{"\n"}{end}' | grep -c -E "(Failed|CrashLoopBackOff|Error)" || true)

    if [[ "$FAILING" -eq 0 ]]; then
        pass "No pods are in failed state"
    else
        fail "$FAILING pods are in failed state"
    fi

    # Check restart counts
    RESTARTS=$(kubectl get pods -n "$NAMESPACE" -l app=redditharbor-agno \
        -o jsonpath='{range .items[*]}{sum(.status.containerStatuses[*].restartCount)}{"\n"}{end}' | paste -sd+ - | bc || echo "0")

    if [[ "$RESTARTS" -lt 5 ]]; then
        pass "Pod restart count is low ($RESTARTS)"
    elif [[ "$RESTARTS" -lt 10 ]]; then
        warn "Pod restart count is moderate ($RESTARTS)"
    else
        fail "Pod restart count is high ($RESTARTS)"
    fi
}

# Test 3: Check service endpoints
test_service_endpoints() {
    log "INFO" "Checking service endpoints..."

    # Check if service exists
    if kubectl get service redditharbor-agno -n "$NAMESPACE" &> /dev/null; then
        pass "Service 'redditharbor-agno' exists"

        # Get service endpoints
        ENDPOINTS=$(kubectl get endpoints redditharbor-agno -n "$NAMESPACE" -o jsonpath='{.subsets[*].addresses[*].ip}' | wc -w)

        if [[ "$ENDPOINTS" -gt 0 ]]; then
            pass "Service has $ENDPOINTS ready endpoints"
        else
            fail "Service has no ready endpoints"
        fi
    else
        fail "Service 'redditharbor-agno' not found"
    fi
}

# Test 4: Check basic health endpoint
test_health_endpoint() {
    log "INFO" "Testing basic health endpoint..."

    # Get service URL
    SERVICE_URL="http://redditharbor-agno.$NAMESPACE.svc.cluster.local/health"

    # Test health endpoint
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$SERVICE_URL" || echo "000")

    if [[ "$HTTP_CODE" == "200" ]]; then
        pass "Health endpoint responds with HTTP 200"

        # Get response body
        RESPONSE=$(curl -s --max-time 10 "$SERVICE_URL")

        # Check required fields
        if echo "$RESPONSE" | jq -e '.status' &> /dev/null; then
            pass "Health response includes status field"
        else
            warn "Health response missing status field"
        fi

        if echo "$RESPONSE" | jq -e '.timestamp' &> /dev/null; then
            pass "Health response includes timestamp"
        else
            warn "Health response missing timestamp"
        fi
    else
        fail "Health endpoint failed with HTTP $HTTP_CODE"
    fi
}

# Test 5: Check detailed health endpoint
test_detailed_health() {
    log "INFO" "Testing detailed health endpoint..."

    SERVICE_URL="http://redditharbor-agno.$NAMESPACE.svc.cluster.local/health/detailed"

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "$SERVICE_URL" || echo "000")

    if [[ "$HTTP_CODE" == "200" ]]; then
        pass "Detailed health endpoint responds with HTTP 200"

        # Parse response
        RESPONSE=$(curl -s --max-time 15 "$SERVICE_URL")

        # Check overall status
        OVERALL_STATUS=$(echo "$RESPONSE" | jq -r '.status // "unknown"')

        if [[ "$OVERALL_STATUS" == "healthy" ]]; then
            pass "Overall health status is healthy"
        elif [[ "$OVERALL_STATUS" == "degraded" ]]; then
            warn "Overall health status is degraded"
            echo "$RESPONSE" | jq -r '.issues[]' | sed 's/^/  - /'
        else
            fail "Overall health status is $OVERALL_STATUS"
        fi

        # Check individual component statuses
        if echo "$RESPONSE" | jq -e '.checks.database' &> /dev/null; then
            DB_STATUS=$(echo "$RESPONSE" | jq -r '.checks.database.status // "unknown"')
            if [[ "$DB_STATUS" == "healthy" ]]; then
                pass "Database health check passed"
            else
                fail "Database health check failed: $DB_STATUS"
            fi
        fi

        if echo "$RESPONSE" | jq -e '.checks.external_apis' &> /dev/null; then
            COHERE_STATUS=$(echo "$RESPONSE" | jq -r '.checks.external_apis.cohere.status // "unknown"')
            if [[ "$COHERE_STATUS" == "healthy" ]]; then
                pass "Cohere API health check passed"
            elif [[ "$COHERE_STATUS" == "degraded" ]]; then
                warn "Cohere API health check degraded"
            else
                fail "Cohere API health check failed"
            fi
        fi
    else
        fail "Detailed health endpoint failed with HTTP $HTTP_CODE"
    fi
}

# Test 6: Check metrics endpoint
test_metrics_endpoint() {
    log "INFO" "Testing metrics endpoint..."

    SERVICE_URL="http://redditharbor-agno.$NAMESPACE.svc.cluster.local/metrics"

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$SERVICE_URL" || echo "000")

    if [[ "$HTTP_CODE" == "200" ]]; then
        pass "Metrics endpoint responds with HTTP 200"

        # Check for required metrics
        METRICS=$(curl -s --max-time 10 "$SERVICE_URL")

        if echo "$METRICS" | grep -q "reddit_harbor_submissions_total"; then
            pass "Submissions metric found"
        else
            warn "Submissions metric not found"
        fi

        if echo "$METRICS" | grep -q "reddit_harbor_request_duration_seconds"; then
            pass "Latency metric found"
        else
            warn "Latency metric not found"
        fi

        if echo "$METRICS" | grep -q "reddit_harbor_errors_total"; then
            pass "Error metric found"
        else
            warn "Error metric not found"
        fi
    else
        fail "Metrics endpoint failed with HTTP $HTTP_CODE"
    fi
}

# Test 7: Check database connectivity
test_database_connectivity() {
    log "INFO" "Testing database connectivity..."

    # Get database URL from secret
    DB_URL=$(kubectl get secret reddit-harbor-secrets -n "$NAMESPACE" \
        -o jsonpath='{.data.DATABASE_URL}' | base64 -d 2>/dev/null || echo "")

    if [[ -z "$DB_URL" ]]; then
        fail "Database URL not found in secrets"
        return
    fi

    # Test basic connectivity
    if psql "$DB_URL" -c "SELECT 1;" &> /dev/null; then
        pass "Database connection successful"

        # Test query performance
        START_TIME=$(date +%s.%N)
        psql "$DB_URL" -c "SELECT COUNT(*) FROM opportunities WHERE created_at > NOW() - INTERVAL '1 hour';" &> /dev/null
        END_TIME=$(date +%s.%N)
        QUERY_TIME=$(echo "$END_TIME - $START_TIME" | bc)

        if (( $(echo "$QUERY_TIME < 1.0" | bc -l) )); then
            pass "Database query performance is good (${QUERY_TIME}s)"
        elif (( $(echo "$QUERY_TIME < 2.0" | bc -l) )); then
            warn "Database query performance is moderate (${QUERY_TIME}s)"
        else
            fail "Database query performance is poor (${QUERY_TIME}s)"
        fi

        # Check connection count
        CONN_COUNT=$(psql "$DB_URL" -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database();" 2>/dev/null | xargs)

        if [[ "$CONN_COUNT" -lt 50 ]]; then
            pass "Database connection count is reasonable ($CONN_COUNT)"
        elif [[ "$CONN_COUNT" -lt 80 ]]; then
            warn "Database connection count is high ($CONN_COUNT)"
        else
            fail "Database connection count is very high ($CONN_COUNT)"
        fi
    else
        fail "Database connection failed"
    fi
}

# Test 8: Check external API connectivity
test_external_api_connectivity() {
    log "INFO" "Testing external API connectivity..."

    # Get API keys from secrets
    COHERE_KEY=$(kubectl get secret reddit-harbor-secrets -n "$NAMESPACE" \
        -o jsonpath='{.data.COHERE_API_KEY}' | base64 -d 2>/dev/null || echo "")
    OPENROUTER_KEY=$(kubectl get secret reddit-harbor-secrets -n "$NAMESPACE" \
        -o jsonpath='{.data.OPENROUTER_API_KEY}' | base64 -d 2>/dev/null || echo "")

    # Test Cohere API
    if [[ -n "$COHERE_KEY" ]]; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
            -X POST "https://api.cohere.ai/v1/embed" \
            -H "Authorization: Bearer $COHERE_KEY" \
            -H "Content-Type: application/json" \
            -d '{"texts": ["test"], "model": "embed-english-v3.0", "input_type": "search_document"}' || echo "000")

        if [[ "$HTTP_CODE" == "200" ]]; then
            pass "Cohere API connectivity verified"
        elif [[ "$HTTP_CODE" == "429" ]]; then
            warn "Cohere API rate limited but reachable"
        else
            fail "Cohere API failed with HTTP $HTTP_CODE"
        fi
    else
        fail "Cohere API key not configured"
    fi

    # Test OpenRouter API
    if [[ -n "$OPENROUTER_KEY" ]]; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
            -X POST "https://openrouter.ai/api/v1/chat/completions" \
            -H "Authorization: Bearer $OPENROUTER_KEY" \
            -H "Content-Type: application/json" \
            -d '{"model": "anthropic/claude-haiku", "messages": [{"role": "user", "content": "test"}]}' || echo "000")

        if [[ "$HTTP_CODE" == "200" ]]; then
            pass "OpenRouter API connectivity verified"
        elif [[ "$HTTP_CODE" == "429" ]]; then
            warn "OpenRouter API rate limited but reachable"
        else
            fail "OpenRouter API failed with HTTP $HTTP_CODE"
        fi
    else
        fail "OpenRouter API key not configured"
    fi
}

# Test 9: Performance validation
test_performance() {
    if [[ "$PERFORMANCE_TEST" != "true" ]]; then
        log "INFO" "Skipping performance test"
        return
    fi

    log "INFO" "Running performance validation..."

    SERVICE_URL="http://redditharbor-agno.$NAMESPACE.svc.cluster.local/health"

    # Run multiple concurrent requests
    TEMP_FILE=$(mktemp)
    pids=()

    # Start 10 concurrent requests
    for i in {1..10}; do
        (
            START_TIME=$(date +%s.%N)
            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$SERVICE_URL" || echo "000")
            END_TIME=$(date +%s.%N)
            LATENCY=$(echo "$END_TIME - $START_TIME" | bc)
            echo "$HTTP_CODE,$LATENCY" >> "$TEMP_FILE"
        ) &
        pids+=($!)
    done

    # Wait for all requests
    for pid in "${pids[@]}"; do
        wait "$pid"
    done

    # Analyze results
    TOTAL_REQUESTS=0
    SUCCESS_REQUESTS=0
    TOTAL_LATENCY=0
    MAX_LATENCY=0

    while IFS=',' read -r http_code latency; do
        ((TOTAL_REQUESTS++))
        TOTAL_LATENCY=$(echo "$TOTAL_LATENCY + $latency" | bc)

        if (( $(echo "$latency > $MAX_LATENCY" | bc -l) )); then
            MAX_LATENCY=$latency
        fi

        if [[ "$http_code" == "200" ]]; then
            ((SUCCESS_REQUESTS++))
        fi
    done < "$TEMP_FILE"

    rm -f "$TEMP_FILE"

    # Calculate metrics
    SUCCESS_RATE=$(echo "scale=2; $SUCCESS_REQUESTS * 100 / $TOTAL_REQUESTS" | bc)
    AVG_LATENCY=$(echo "scale=2; $TOTAL_LATENCY / $TOTAL_REQUESTS" | bc)

    log "INFO" "Performance: $SUCCESS_REQUESTS/$TOTAL_REQUESTS successful (${SUCCESS_RATE}%)"
    log "INFO" "Average latency: ${AVG_LATENCY}s, Max: ${MAX_LATENCY}s"

    # Evaluate results
    if [[ "$SUCCESS_RATE" == "100.00" ]]; then
        pass "All requests successful (100%)"
    elif (( $(echo "$SUCCESS_RATE >= 95.00" | bc -l) )); then
        warn "High success rate but some failures (${SUCCESS_RATE}%)"
    else
        fail "Low success rate (${SUCCESS_RATE}%)"
    fi

    if (( $(echo "$AVG_LATENCY < 1.0" | bc -l) )); then
        pass "Average latency is good (${AVG_LATENCY}s)"
    elif (( $(echo "$AVG_LATENCY < 2.0" | bc -l) )); then
        warn "Average latency is moderate (${AVG_LATENCY}s)"
    else
        fail "Average latency is poor (${AVG_LATENCY}s)"
    fi

    if (( $(echo "$MAX_LATENCY < 5.0" | bc -l) )); then
        pass "Maximum latency is acceptable (${MAX_LATENCY}s)"
    elif (( $(echo "$MAX_LATENCY < 10.0" | bc -l) )); then
        warn "Maximum latency is high (${MAX_LATENCY}s)"
    else
        fail "Maximum latency is too high (${MAX_LATENCY}s)"
    fi
}

# Test 10: Resource usage check
test_resource_usage() {
    log "INFO" "Checking resource usage..."

    # Get pod resource usage (requires metrics-server)
    if kubectl top pods -n "$NAMESPACE" -l app=redditharbor-agno &> /dev/null; then
        # Check CPU usage
        AVG_CPU=$(kubectl top pods -n "$NAMESPACE" -l app=redditharbor-agno \
            --no-headers | awk '{sum+=$2} END {print sum/NR}' | sed 's/m//')

        if (( $(echo "$AVG_CPU < 500" | bc -l) )); then
            pass "Average CPU usage is low (${AVG_CPU}m)"
        elif (( $(echo "$AVG_CPU < 1000" | bc -l) )); then
            warn "Average CPU usage is moderate (${AVG_CPU}m)"
        else
            warn "Average CPU usage is high (${AVG_CPU}m)"
        fi

        # Check memory usage
        AVG_MEMORY=$(kubectl top pods -n "$NAMESPACE" -l app=redditharbor-agno \
            --no-headers | awk '{sum+=$3} END {print sum/NR}' | sed 's/Mi//')

        if (( $(echo "$AVG_MEMORY < 1000" | bc -l) )); then
            pass "Average memory usage is low (${AVG_MEMORY}Mi)"
        elif (( $(echo "$AVG_MEMORY < 2000" | bc -l) )); then
            warn "Average memory usage is moderate (${AVG_MEMORY}Mi)"
        else
            warn "Average memory usage is high (${AVG_MEMORY}Mi)"
        fi
    else
        warn "Metrics server not available - cannot check resource usage"
    fi

    # Check pod limits
    PODS=$(kubectl get pods -n "$NAMESPACE" -l app=redditharbor-agno -o name)

    for pod in $PODSS; do
        pod_name=${pod#pod/}

        # Check for OOMKilled events
        OOM_COUNT=$(kubectl describe pod "$pod_name" -n "$NAMESPACE" | grep -c "OOMKilled" || true)

        if [[ "$OOM_COUNT" -eq 0 ]]; then
            pass "Pod $pod_name has no OOM kills"
        else
            fail "Pod $pod_name has $OOM_COUNT OOM kills"
        fi
    done
}

# Main verification function
run_verification() {
    echo "RedditHarbor Phase 5 Deployment Verification"
    echo "=========================================="
    echo "Namespace: $NAMESPACE"
    echo "Timeout: ${TIMEOUT}s"
    echo ""

    # Run all tests
    test_deployment_exists
    test_pod_health
    test_service_endpoints
    test_health_endpoint
    test_detailed_health
    test_metrics_endpoint
    test_database_connectivity
    test_external_api_connectivity
    test_performance
    test_resource_usage

    # Show summary
    show_summary
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --no-performance)
            PERFORMANCE_TEST=false
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --fail-on-warnings)
            FAIL_ON_WARNINGS=true
            shift
            ;;
        -f|--format)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        -h|--help)
            cat << EOF
RedditHarbor Phase 5 Deployment Verification

Usage: $0 [OPTIONS]

OPTIONS:
    -n, --namespace NAMESPACE     Target namespace (default: production)
    -t, --timeout SECONDS         Test timeout (default: 300)
    --no-performance             Skip performance tests
    -v, --verbose                Show verbose output
    --fail-on-warnings           Treat warnings as failures
    -f, --format FORMAT          Output format (table/json)
    -h, --help                   Show this help message

EXAMPLES:
    # Basic verification
    $0

    # Verify staging namespace
    $0 -n staging

    # Verbose output with fail-on-warnings
    $0 -v --fail-on-warnings

    # Quick verification without performance tests
    $0 --no-performance

EOF
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run verification
run_verification