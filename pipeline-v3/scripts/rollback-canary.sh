#!/bin/bash
# RedditHarbor Phase 5 Canary Rollback Script
# ===========================================
#
# This script provides emergency rollback capabilities for canary deployments,
# including immediate traffic switching, resource cleanup, and status verification.

set -euo pipefail

# Configuration defaults
NAMESPACE=${NAMESPACE:-production}
FORCE=${FORCE:-false}
SKIP_CONFIRMATION=${SKIP_CONFIRMATION:-false}
BACKUP_RESOURCES=${BACKUP_RESOURCES:-true}
DRY_RUN=${DRY_RUN:-false}
CLEANUP_DELAY=${CLEANUP_DELAY:-30}  # seconds before cleanup
KEEP_MONITORING=${KEEP_MONITORING:-true}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
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

emergency() {
    echo -e "${MAGENTA}[EMERGENCY]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
RedditHarbor Phase 5 Canary Rollback

Usage: $0 [OPTIONS]

This script performs an emergency rollback of canary deployments,
routing all traffic back to the stable version.

OPTIONS:
    -n, --namespace NAMESPACE   Target namespace (default: production)
    -f, --force                 Force rollback without confirmation
    -s, --skip-confirmation    Skip interactive confirmation (use with caution)
    --no-backup                Skip resource backup before rollback
    --dry-run                  Show what would be done without executing
    --cleanup-delay SECONDS    Delay before cleaning up canary resources (default: 30)
    --no-monitoring            Don't keep monitoring after rollback
    -h, --help                 Show this help message

EMERGENCY MODE:
    For immediate emergency rollback, use:
    $0 --force --skip-confirmation

EXAMPLES:
    # Normal rollback with confirmation
    $0

    # Emergency rollback (immediate, no prompts)
    $0 --force --skip-confirmation

    # Dry run to see what would happen
    $0 --dry-run

    # Rollback with delayed cleanup
    $0 --cleanup-delay 300

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
            -f|--force)
                FORCE=true
                shift
                ;;
            -s|--skip-confirmation)
                SKIP_CONFIRMATION=true
                shift
                ;;
            --no-backup)
                BACKUP_RESOURCES=false
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --cleanup-delay)
                CLEANUP_DELAY="$2"
                shift 2
                ;;
            --no-monitoring)
                KEEP_MONITORING=false
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                error "Unknown option: $1. Use --help for usage information."
                ;;
        esac
    done
}

# Confirmation prompt
confirm_rollback() {
    if [[ "$SKIP_CONFIRMATION" == "true" ]] || [[ "$FORCE" == "true" ]] || [[ "$DRY_RUN" == "true" ]]; then
        return 0
    fi

    echo ""
    echo -e "${YELLOW}⚠️  WARNING: This will rollback all traffic from canary to stable deployment${NC}"
    echo ""
    echo "This action will:"
    echo "  1. Route 100% traffic to stable deployment"
    echo "  2. Scale down canary deployment to 0"
    echo "  3. Remove canary from load balancer"
    echo "  4. Clean up canary resources"
    echo ""
    read -p "Are you sure you want to continue? [yes/NO]: " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log "Rollback cancelled by user"
        exit 0
    fi
}

# Check prerequisites
check_prerequisites() {
    log "Checking rollback prerequisites..."

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

    # Check if stable deployment exists
    if ! kubectl get deployment redditharbor-agno -n "$NAMESPACE" &> /dev/null; then
        error "Stable deployment 'redditharbor-agno' not found - cannot rollback!"
    fi

    # Verify stable deployment is healthy
    STABLE_REPLICAS=$(kubectl get deployment redditharbor-agno -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
    STABLE_READY=$(kubectl get deployment redditharbor-agno -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')

    if [[ "$STABLE_READY" -ne "$STABLE_REPLICAS" ]]; then
        error "Stable deployment is not healthy (${STABLE_READY}/${STABLE_REPLICAS} ready)"
    fi

    log "Stable deployment is healthy with ${STABLE_READY}/${STABLE_REPLICAS} replicas ready"

    success "Prerequisites check passed"
}

# Get current traffic distribution
get_current_state() {
    log "Getting current deployment state..."

    # Check if canary exists
    if kubectl get deployment redditharbor-agno-canary -n "$NAMESPACE" &> /dev/null; then
        CANARY_EXISTS=true
        CANARY_REPLICAS=$(kubectl get deployment redditharbor-agno-canary -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
        CANARY_READY=$(kubectl get deployment redditharbor-agno-canary -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' || echo "0")
        log "Canary deployment found: ${CANARY_READY}/${CANARY_REPLICAS} replicas"
    else
        CANARY_EXISTS=false
        log "No canary deployment found"
    fi

    # Get current traffic distribution
    if kubectl get crd virtualservices.networking.istio.io &> /dev/null && \
       kubectl get virtualservice redditharbor-agno -n "$NAMESPACE" &> /dev/null; then
        ISTIO_ENABLED=true
        STABLE_WEIGHT=$(kubectl get virtualservice redditharbor-agno -n "$NAMESPACE" -o jsonpath='{.spec.http[1].route[0].weight}')
        CANARY_WEIGHT=$(kubectl get virtualservice redditharbor-agno -n "$NAMESPACE" -o jsonpath='{.spec.http[1].route[1].weight}' || echo "0")
        log "Current traffic distribution: Stable=${STABLE_WEIGHT:-100}%, Canary=${CANARY_WEIGHT:-0}%"
    else
        ISTIO_ENABLED=false
        log "Istio not enabled - using service-based routing"
    fi
}

# Backup resources before rollback
backup_resources() {
    if [[ "$BACKUP_RESOURCES" != "true" ]] || [[ "$DRY_RUN" == "true" ]]; then
        log "Skipping resource backup"
        return 0
    fi

    log "Backing up resources before rollback..."

    BACKUP_DIR="/var/log/redditharbor-rollbacks/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    # Backup VirtualService if it exists
    if [[ "$ISTIO_ENABLED" == "true" ]]; then
        kubectl get virtualservice redditharbor-agno -n "$NAMESPACE" -o yaml > "$BACKUP_DIR/virtualservice.yaml"
        log "VirtualService backed up to $BACKUP_DIR/virtualservice.yaml"
    fi

    # Backup canary deployment if it exists
    if [[ "$CANARY_EXISTS" == "true" ]]; then
        kubectl get deployment redditharbor-agno-canary -n "$NAMESPACE" -o yaml > "$BACKUP_DIR/canary-deployment.yaml"
        kubectl get service redditharbor-agno-canary -n "$NAMESPACE" -o yaml > "$BACKUP_DIR/canary-service.yaml"
        log "Canary resources backed up to $BACKUP_DIR/"
    fi

    # Save rollback context
    cat > "$BACKUP_DIR/rollback-context.json" << EOF
{
    "timestamp": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
    "namespace": "$NAMESPACE",
    "istio_enabled": $ISTIO_ENABLED,
    "canary_exists": $CANARY_EXISTS,
    "stable_traffic_weight": ${STABLE_WEIGHT:-100},
    "canary_traffic_weight": ${CANARY_WEIGHT:-0},
    "canary_replicas": ${CANARY_REPLICAS:-0},
    "canary_ready": ${CANARY_READY:-0},
    "triggered_by": "$(whoami)",
    "command": "$0 $*"
}
EOF

    success "Resources backed up to $BACKUP_DIR"
}

# Emergency traffic routing to stable
emergency_routing() {
    log "Performing emergency traffic routing to stable deployment..."

    if [[ "$ISTIO_ENABLED" == "true" ]]; then
        # Update VirtualService to route all traffic to stable
        cat > /tmp/emergency-vs.yaml << EOF
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
        subset: stable
      weight: 100
  - route:
    - destination:
        host: redditharbor-agno
        subset: stable
      weight: 100
EOF

        if [[ "$DRY_RUN" == "true" ]]; then
            log "[DRY RUN] Would update VirtualService to route 100% traffic to stable"
        else
            kubectl apply -f /tmp/emergency-vs.yaml
            log "VirtualService updated - all traffic now routed to stable"
        fi

    else
        # Service-based routing - ensure main service points to stable
        if [[ "$DRY_RUN" == "true" ]]; then
            log "[DRY RUN] Would patch main service to select stable pods"
        else
            kubectl patch service redditharbor-agno -n "$NAMESPACE" -p \
                '{"spec":{"selector":{"track":"stable"}}}'
            log "Main service patched - all traffic now routed to stable"
        fi
    fi

    success "Emergency routing completed"
}

# Scale down canary deployment
scale_down_canary() {
    if [[ "$CANARY_EXISTS" != "true" ]]; then
        log "No canary deployment to scale down"
        return 0
    fi

    log "Scaling down canary deployment..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY RUN] Would scale canary deployment to 0 replicas"
        return 0
    fi

    # Scale down to 0 immediately
    kubectl scale deployment redditharbor-agno-canary -n "$NAMESPACE" --replicas=0

    # Wait for scale down to complete
    log "Waiting for canary pods to terminate..."
    kubectl wait --for=delete pod \
        --selector="app=redditharbor-agno,track=canary" \
        --namespace="$NAMESPACE" \
        --timeout=60s || true

    success "Canary deployment scaled down"
}

# Clean up canary resources
cleanup_canary_resources() {
    if [[ "$CANARY_EXISTS" != "true" ]]; then
        log "No canary resources to clean up"
        return 0
    fi

    log "Waiting ${CLEANUP_DELAY} seconds before cleanup..."
    sleep "$CLEANUP_DELAY"

    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY RUN] Would clean up canary resources"
        return 0
    fi

    # Delete canary deployment
    kubectl delete deployment redditharbor-agno-canary -n "$NAMESPACE" --ignore-not-found=true

    # Delete canary service
    kubectl delete service redditharbor-agno-canary -n "$NAMESPACE" --ignore-not-found=true

    # Delete ServiceMonitor
    kubectl delete servicemonitor redditharbor-agno-canary -n "$NAMESPACE" --ignore-not-found=true

    # Remove canary from DestinationRule
    if [[ "$ISTIO_ENABLED" == "true" ]]; then
        if kubectl get destinationrule redditharbor-agno -n "$NAMESPACE" &> /dev/null; then
            kubectl patch destinationrule redditharbor-agno -n "$NAMESPACE" --type=json \
                --patch='[{"op": "remove", "path": "/spec/subsets/1"}]' || true
        fi
    fi

    success "Canary resources cleaned up"
}

# Verify rollback success
verify_rollback() {
    log "Verifying rollback success..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY RUN] Would verify rollback success"
        return 0
    fi

    # Verify all traffic goes to stable
    if [[ "$ISTIO_ENABLED" == "true" ]]; then
        STABLE_WEIGHT=$(kubectl get virtualservice redditharbor-agno -n "$NAMESPACE" -o jsonpath='{.spec.http[1].route[0].weight}')
        if [[ "$STABLE_WEIGHT" != "100" ]]; then
            error "Traffic not fully routed to stable (weight: ${STABLE_WEIGHT}%)"
        fi
    fi

    # Verify stable deployment is healthy
    STABLE_REPLICAS=$(kubectl get deployment redditharbor-agno -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
    STABLE_READY=$(kubectl get deployment redditharbor-agno -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')

    if [[ "$STABLE_READY" -ne "$STABLE_REPLICAS" ]]; then
        error "Stable deployment not healthy after rollback (${STABLE_READY}/${STABLE_REPLICAS})"
    fi

    # Verify canary is removed
    if kubectl get deployment redditharbor-agno-canary -n "$NAMESPACE" &> /dev/null; then
        warn "Canary deployment still exists - manual cleanup may be required"
    fi

    # Test service endpoint
    for i in {1..5}; do
        if curl -f -s http://redditharbor-agno."$NAMESPACE".svc.cluster.local/health > /dev/null; then
            success "Health check $i passed"
        else
            error "Health check $i failed - service not responding"
        fi
        sleep 2
    done

    success "Rollback verification successful"
}

# Create rollback event
create_rollback_event() {
    if [[ "$DRY_RUN" == "true" ]]; then
        return 0
    fi

    log "Creating rollback event..."

    # Create Kubernetes event
    kubectl create event \
        --namespace="$NAMESPACE" \
        --type=Warning \
        --reason="CanaryRollback" \
        --message="Emergency rollback of canary deployment triggered by $(whoami)" \
        redditharbor-agno || true

    # Log to system
    logger -t redditharbor-rollback "Emergency rollback completed in namespace $NAMESPACE by $(whoami)"

    # Send to monitoring system (if available)
    if command -v curl &> /dev/null && [[ -n "${MONITORING_WEBHOOK:-}" ]]; then
        curl -X POST "$MONITORING_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{
                \"event_type\": \"rollback\",
                \"namespace\": \"$NAMESPACE\",
                \"timestamp\": \"$(date -u +'%Y-%m-%dT%H:%M:%SZ')\",
                \"triggered_by\": \"$(whoami)\",
                \"canary_existed\": $CANARY_EXISTS,
                \"istio_enabled\": $ISTIO_ENABLED
            }" || true
    fi

    success "Rollback event created"
}

# Monitor after rollback
monitor_after_rollback() {
    if [[ "$KEEP_MONITORING" != "true" ]] || [[ "$DRY_RUN" == "true" ]]; then
        return 0
    fi

    log "Starting post-rollback monitoring (Ctrl+C to stop)..."
    log "Press Ctrl+C to stop monitoring"

    # Monitor for 5 minutes or until interrupted
    END_TIME=$(($(date +%s) + 300))

    while true; do
        CURRENT_TIME=$(date +%s)
        if [[ $CURRENT_TIME -gt $END_TIME ]]; then
            log "Monitoring period complete"
            break
        fi

        # Check stable deployment health
        STABLE_READY=$(kubectl get deployment redditharbor-agno -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')
        STABLE_REPLICAS=$(kubectl get deployment redditharbor-agno -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')

        # Check service health
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://redditharbor-agno."$NAMESPACE".svc.cluster.local/health)

        # Log status
        echo -e "\n[${BLUE}$(date +'%H:%M:%S')${NC}] Stable Deployment: ${STABLE_READY}/${STABLE_REPLICAS} | HTTP: ${HTTP_CODE}"

        # Alert on issues
        if [[ "$STABLE_READY" -ne "$STABLE_REPLICAS" ]]; then
            warn "Stable deployment health degraded: ${STABLE_READY}/${STABLE_REPLICAS}"
        fi

        if [[ "$HTTP_CODE" != "200" ]]; then
            warn "Service health check failed: HTTP $HTTP_CODE"
        fi

        sleep 10
    done
}

# Display rollback summary
show_summary() {
    log "=== Rollback Summary ==="
    echo "Namespace: $NAMESPACE"
    echo "Timestamp: $(date)"
    echo "Triggered by: $(whoami)"
    echo ""

    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}[DRY RUN MODE]${NC}"
        echo "The following actions would be performed:"
        echo ""
    fi

    echo "Before Rollback:"
    echo "  Canary Existed: $CANARY_EXISTS"
    echo "  Traffic to Stable: ${STABLE_WEIGHT:-100}%"
    echo "  Traffic to Canary: ${CANARY_WEIGHT:-0}%"
    if [[ "$CANARY_EXISTS" == "true" ]]; then
        echo "  Canary Replicas: ${CANARY_READY:-0}/${CANARY_REPLICAS:-0}"
    fi
    echo ""

    echo "After Rollback:"
    echo "  Traffic to Stable: 100%"
    echo "  Traffic to Canary: 0%"
    echo "  Canary Deployment: Removed"
    echo ""

    if [[ "$BACKUP_RESOURCES" == "true" ]] && [[ -n "${BACKUP_DIR:-}" ]]; then
        echo "Backup Location: $BACKUP_DIR"
        echo ""
    fi

    if [[ "$KEEP_MONITORING" == "true" ]] && [[ "$DRY_RUN" != "true" ]]; then
        echo "Post-rollback monitoring is enabled"
        echo ""
    fi

    echo "Next Steps:"
    if [[ "$DRY_RUN" != "true" ]]; then
        echo "1. Monitor system stability"
        echo "2. Check application logs: kubectl logs -n $NAMESPACE -l track=stable -f"
        echo "3. Review metrics in Grafana"
        echo "4. Document root cause analysis"
        if [[ -n "${BACKUP_DIR:-}" ]]; then
            echo "5. Restore canary if needed: kubectl apply -f $BACKUP_DIR/"
        fi
    fi
}

# Main execution
main() {
    emergency "EMERGENCY ROLLBACK INITIATED"
    log "Starting RedditHarbor Phase 5 Emergency Rollback..."

    # Parse arguments
    parse_args "$@"

    # Confirmation check (skip for emergency mode)
    if [[ "$FORCE" != "true" ]]; then
        confirm_rollback
    else
        log "FORCE MODE: Skipping confirmation"
    fi

    # Execute rollback sequence
    check_prerequisites
    get_current_state
    backup_resources
    emergency_routing
    scale_down_canary
    cleanup_canary_resources
    verify_rollback
    create_rollback_event
    show_summary

    # Start monitoring if enabled
    if [[ "$KEEP_MONITORING" == "true" ]] && [[ "$DRY_RUN" != "true" ]]; then
        monitor_after_rollback
    fi

    success "Emergency rollback completed successfully!"
}

# Execute main function with error handling
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Set up error handling
    trap 'error "Rollback script failed unexpectedly at line $LINENO"' ERR

    # Execute main function
    main "$@"
fi