#!/bin/bash
# RedditHarbor Phase 5 Traffic Switching Script
# ============================================
#
# This script manages traffic switching between stable and canary deployments
# using Istio VirtualService or simple service-based routing.

set -euo pipefail

# Configuration defaults
NAMESPACE=${NAMESPACE:-production}
TRAFFIC_PERCENT=${TRAFFIC_PERCENT:-0}
MODE=${MODE:-split}  # split, all-stable, all-canary
DRY_RUN=${DRY_RUN:-false}
VERIFY=${VERIFY:-true}
GRACEFUL=${GRACEFUL:-true}
WAIT_TIME=${WAIT_TIME:-10}  # seconds between checks

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
RedditHarbor Phase 5 Traffic Switching

Usage: $0 [OPTIONS] MODE TRAFFIC_PERCENT

MODES:
    split        Split traffic between stable and canary
    all-stable   Route 100% traffic to stable
    all-canary   Route 100% traffic to canary

TRAFFIC_PERCENT:
    For 'split' mode: Percentage of traffic to route to canary (0-100)

OPTIONS:
    -n, --namespace NAMESPACE    Target namespace (default: production)
    --dry-run                    Show what would be done without executing
    --no-verify                  Skip traffic verification
    --no-graceful               Make immediate traffic switch
    --wait-time SECONDS         Time between verification checks (default: 10)
    -h, --help                  Show this help message

EXAMPLES:
    # Route 20% traffic to canary
    $0 split 20

    # Route all traffic to stable (rollback)
    $0 all-stable

    # Route all traffic to canary (full promotion)
    $0 all-canary

    # Show what would change without executing
    $0 --dry-run split 50

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --no-verify)
                VERIFY=false
                shift
                ;;
            --no-graceful)
                GRACEFUL=false
                shift
                ;;
            --wait-time)
                WAIT_TIME="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            split|all-stable|all-canary)
                MODE="$1"
                shift
                ;;
            *)
                if [[ "$MODE" == "split" ]] && [[ -z "$TRAFFIC_PERCENT" ]]; then
                    TRAFFIC_PERCENT="$1"
                    shift
                else
                    error "Unknown option or invalid argument: $1"
                fi
                ;;
        esac
    done

    # Validate arguments
    if [[ -z "$MODE" ]]; then
        error "MODE is required. Use --help for usage information."
    fi

    if [[ "$MODE" == "split" ]]; then
        if [[ -z "$TRAFFIC_PERCENT" ]]; then
            error "TRAFFIC_PERCENT is required for split mode"
        fi
        if [[ ! "$TRAFFIC_PERCENT" =~ ^[0-9]+$ ]] || [[ "$TRAFFIC_PERCENT" -lt 0 ]] || [[ "$TRAFFIC_PERCENT" -gt 100 ]]; then
            error "Traffic percentage must be between 0 and 100"
        fi
    fi

    # Set traffic percentages based on mode
    case "$MODE" in
        all-stable)
            STABLE_PERCENT=100
            CANARY_PERCENT=0
            ;;
        all-canary)
            STABLE_PERCENT=0
            CANARY_PERCENT=100
            ;;
        split)
            STABLE_PERCENT=$((100 - TRAFFIC_PERCENT))
            CANARY_PERCENT=$TRAFFIC_PERCENT
            ;;
    esac
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed"
    fi

    # Check kubectl connectivity
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster"
    fi

    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        error "Namespace '$NAMESPACE' does not exist"
    fi

    # Check if deployments exist
    if ! kubectl get deployment redditharbor-agno -n "$NAMESPACE" &> /dev/null; then
        error "Stable deployment 'redditharbor-agno' not found"
    fi

    # Check if canary exists (unless we're routing all to stable)
    if [[ "$MODE" != "all-stable" ]] && ! kubectl get deployment redditharbor-agno-canary -n "$NAMESPACE" &> /dev/null; then
        error "Canary deployment 'redditharbor-agno-canary' not found"
    fi

    # Check routing method
    if kubectl get crd virtualservices.networking.istio.io &> /dev/null; then
        ROUTING_METHOD="istio"
        log "Using Istio for traffic routing"
    else
        ROUTING_METHOD="service"
        log "Using service-based traffic routing"
    fi

    success "Prerequisites check passed"
}

# Get current traffic distribution
get_current_traffic() {
    if [[ "$ROUTING_METHOD" == "istio" ]]; then
        # Get current weights from VirtualService
        if kubectl get virtualservice redditharbor-agno -n "$NAMESPACE" &> /dev/null; then
            STABLE_CURRENT=$(kubectl get virtualservice redditharbor-agno -n "$NAMESPACE" -o jsonpath='{.spec.http[1].route[0].weight}')
            CANARY_CURRENT=$(kubectl get virtualservice redditharbor-agno -n "$NAMESPACE" -o jsonpath='{.spec.http[1].route[1].weight}')
        else
            STABLE_CURRENT=100
            CANARY_CURRENT=0
        fi
    else
        # Service-based routing doesn't support gradual traffic splitting
        if kubectl get svc redditharbor-agno-test -n "$NAMESPACE" &> /dev/null; then
            STABLE_CURRENT=0
            CANARY_CURRENT=100
        else
            STABLE_CURRENT=100
            CANARY_CURRENT=0
        fi
    fi

    echo "Current traffic distribution: Stable=${STABLE_CURRENT:-100}%, Canary=${CANARY_CURRENT:-0}%"
}

# Switch traffic using Istio
switch_istio_traffic() {
    log "Switching Istio traffic distribution: Stable=${STABLE_PERCENT}%, Canary=${CANARY_PERCENT}%"

    cat > /tmp/virtual-service.yaml << EOF
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: redditharbor-agno
  namespace: $NAMESPACE
spec:
  hosts:
  - redditharbor-agno
  http:
  - match:
    - headers:
        x-canary:
          exact: "true"
    route:
    - destination:
        host: redditharbor-agno
        subset: canary
      weight: 100
  - route:
    - destination:
        host: redditharbor-agno
        subset: stable
      weight: $STABLE_PERCENT
    - destination:
        host: redditharbor-agno
        subset: canary
      weight: $CANARY_PERCENT
EOF

    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY RUN] Would apply Istio VirtualService with traffic weights"
        cat /tmp/virtual-service.yaml
        return 0
    fi

    # Apply graceful transition if enabled
    if [[ "$GRACEFUL" == "true" ]] && [[ "$STABLE_CURRENT" != "$STABLE_PERCENT" ]]; then
        log "Performing graceful traffic transition..."

        # Calculate transition steps
        STEPS=10
        STABLE_DIFF=$((STABLE_PERCENT - STABLE_CURRENT))
        CANARY_DIFF=$((CANARY_PERCENT - CANARY_CURRENT))

        for i in $(seq 1 $STEPS); do
            STEP_STABLE=$((STABLE_CURRENT + (STABLE_DIFF * i / STEPS)))
            STEP_CANARY=$((CANARY_CURRENT + (CANARY_DIFF * i / STEPS)))

            log "Transition step $i/$STEPS: Stable=${STEP_STABLE}%, Canary=${STEP_CANARY}%"

            # Update VirtualService
            cat > /tmp/transition-vs.yaml << EOF
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: redditharbor-agno
  namespace: $NAMESPACE
spec:
  hosts:
  - redditharbor-agno
  http:
  - match:
    - headers:
        x-canary:
          exact: "true"
    route:
    - destination:
        host: redditharbor-agno
        subset: canary
      weight: 100
  - route:
    - destination:
        host: redditharbor-agno
        subset: stable
      weight: $STEP_STABLE
    - destination:
        host: redditharbor-agno
        subset: canary
      weight: $STEP_CANARY
EOF

            kubectl apply -f /tmp/transition-vs.yaml
            sleep "$WAIT_TIME"

            # Verify traffic after each step
            if [[ "$VERIFY" == "true" ]]; then
                verify_traffic_switch
            fi
        done
    else
        # Immediate switch
        kubectl apply -f /tmp/virtual-service.yaml
    fi

    success "Istio traffic routing updated"
}

# Switch traffic using services
switch_service_traffic() {
    log "Switching service-based traffic..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY RUN] Would switch service-based traffic"
        if [[ "$MODE" == "all-canary" ]]; then
            log "[DRY RUN] Would point main service to canary pods"
        elif [[ "$MODE" == "all-stable" ]]; then
            log "[DRY RUN] Would point main service to stable pods"
        fi
        return 0
    fi

    # Service-based routing is all-or-nothing
    if [[ "$MODE" == "all-canary" ]]; then
        # Patch main service to select canary pods
        kubectl patch service redditharbor-agno -n "$NAMESPACE" -p \
            '{"spec":{"selector":{"track":"canary"}}}'
        log "Main service now points to canary pods"
    elif [[ "$MODE" == "all-stable" ]]; then
        # Patch main service to select stable pods
        kubectl patch service redditharbor-agno -n "$NAMESPACE" -p \
            '{"spec":{"selector":{"track":"stable"}}}'
        log "Main service now points to stable pods"
    else
        warn "Service-based routing does not support gradual traffic splitting"
        warn "Use external load balancer or Istio for traffic splitting"
    fi

    success "Service-based traffic updated"
}

# Verify traffic switch
verify_traffic_switch() {
    if [[ "$VERIFY" != "true" ]] || [[ "$DRY_RUN" == "true" ]]; then
        return 0
    fi

    log "Verifying traffic distribution..."

    # Wait a moment for changes to take effect
    sleep "$WAIT_TIME"

    # Test traffic distribution
    TOTAL_REQUESTS=50
    CANARY_REQUESTS=0
    STABLE_REQUESTS=0

    for i in $(seq 1 $TOTAL_REQUESTS); do
        # Send test request
        RESPONSE=$(curl -s -o /dev/null -w "%{http_code},%{remote_addr}" \
            http://redditharbor-agno."$NAMESPACE".svc.cluster.local/health)

        HTTP_CODE="${RESPONSE%%,*}"
        POD_IP="${RESPONSE##*,}"

        # Check if request went to canary or stable
        if kubectl get pod -n "$NAMESPACE" -o wide | grep "$POD_IP" | grep -q "canary"; then
            CANARY_REQUESTS=$((CANARY_REQUESTS + 1))
        else
            STABLE_REQUESTS=$((STABLE_REQUESTS + 1))
        fi
    done

    # Calculate percentages
    ACTUAL_CANARY_PERCENT=$((CANARY_REQUESTS * 100 / TOTAL_REQUESTS))
    ACTUAL_STABLE_PERCENT=$((STABLE_REQUESTS * 100 / TOTAL_REQUESTS))

    log "Traffic verification results:"
    log "  Expected: Canary=${CANARY_PERCENT}%, Stable=${STABLE_PERCENT}%"
    log "  Actual:   Canary=${ACTUAL_CANARY_PERCENT}%, Stable=${ACTUAL_STABLE_PERCENT}%"
    log "  Requests: Canary=${CANARY_REQUESTS}, Stable=${STABLE_REQUESTS}"

    # Check if results are within acceptable range
    TOLERANCE=10
    STABLE_DIFF=$((ACTUAL_STABLE_PERCENT - STABLE_PERCENT))
    STABLE_DIFF_ABS=${STABLE_DIFF#-}

    if [[ $STABLE_DIFF_ABS -gt $TOLERANCE ]]; then
        warn "Traffic distribution is outside tolerance (+/-${TOLERANCE}%)"
        warn "This might be normal during graceful transitions"
    else
        success "Traffic distribution verified"
    fi
}

# Display traffic status
show_traffic_status() {
    log "=== Traffic Status ==="
    echo "Namespace: $NAMESPACE"
    echo "Routing Method: $ROUTING_METHOD"
    echo "Mode: $MODE"
    echo ""

    get_current_traffic
    echo ""

    if [[ "$ROUTING_METHOD" == "istio" ]]; then
        echo "VirtualService:"
        kubectl get virtualservice redditharbor-agno -n "$NAMESPACE" -o yaml | \
            grep -A 10 "route:" | grep -E "weight:|destination:" | \
            sed 's/^/  /'
    else
        echo "Service Selectors:"
        echo "  Main Service:"
        kubectl get service redditharbor-agno -n "$NAMESPACE" -o jsonpath='{.spec.selector}' | \
            jq -r 'to_entries[] | "    \(.key): \(.value)"'
        echo ""
        echo "  Test Service (if exists):"
        if kubectl get service redditharbor-agno-test -n "$NAMESPACE" &> /dev/null; then
            kubectl get service redditharbor-agno-test -n "$NAMESPACE" -o jsonpath='{.spec.selector}' | \
                jq -r 'to_entries[] | "    \(.key): \(.value)"'
        else
            echo "    Not found"
        fi
    fi

    echo ""
    echo "Deployment Status:"
    echo "  Stable:"
    kubectl get deployment redditharbor-agno -n "$NAMESPACE" -o jsonpath='  Ready: {.status.readyReplicas}/{.spec.replicas}\n'
    if kubectl get deployment redditharbor-agno-canary -n "$NAMESPACE" &> /dev/null; then
        echo "  Canary:"
        kubectl get deployment redditharbor-agno-canary -n "$NAMESPACE" -o jsonpath='  Ready: {.status.readyReplicas}/{.spec.replicas}\n'
    else
        echo "  Canary: Not deployed"
    fi
}

# Main execution
main() {
    log "Starting RedditHarbor Phase 5 Traffic Switch..."

    # Parse arguments
    parse_args "$@"

    # Run checks and switch
    check_prerequisites

    # Get current state before switching
    get_current_traffic
    CURRENT_STABLE="$STABLE_CURRENT"
    CURRENT_CANARY="$CANARY_CURRENT"

    # Perform traffic switch
    case "$ROUTING_METHOD" in
        istio)
            switch_istio_traffic
            ;;
        service)
            switch_service_traffic
            ;;
    esac

    # Verify the switch
    verify_traffic_switch

    # Show final status
    show_traffic_status

    # Log the change
    if [[ "$DRY_RUN" != "true" ]]; then
        log "Traffic switch completed:"
        log "  Before: Stable=${CURRENT_STABLE:-100}%, Canary=${CURRENT_CANARY:-0}%"
        log "  After:  Stable=${STABLE_PERCENT}%, Canary=${CANARY_PERCENT}%"

        # Create audit log entry
        AUDIT_ENTRY="{
            \"timestamp\": \"$(date -u +'%Y-%m-%dT%H:%M:%SZ')\",
            \"namespace\": \"$NAMESPACE\",
            \"mode\": \"$MODE\",
            \"before\": {\"stable\": ${CURRENT_STABLE:-100}, \"canary\": ${CURRENT_CANARY:-0}},
            \"after\": {\"stable\": $STABLE_PERCENT, \"canary\": $CANARY_PERCENT},
            \"user\": \"$(whoami)\",
            \"command\": \"$0 $*\"
        }"

        echo "$AUDIT_ENTRY" >> /var/log/redditharbor-traffic-switches.log
    fi

    success "Traffic switching completed successfully!"
}

# Execute main function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi