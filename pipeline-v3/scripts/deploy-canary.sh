#!/bin/bash
# RedditHarbor Phase 5 Canary Deployment Script
# ============================================
#
# This script automates the canary deployment process for RedditHarbor Phase 5,
# including Docker image building, deployment creation, and traffic routing setup.

set -euo pipefail

# Configuration defaults
CANARY_PERCENT=${CANARY_PERCENT:-10}
NAMESPACE=${NAMESPACE:-production}
VERSION=${VERSION:-$(git rev-parse --short HEAD 2>/dev/null || echo "latest")}
IMAGE_REGISTRY=${IMAGE_REGISTRY:-"your-registry.com"}
IMAGE_NAME=${IMAGE_NAME:-"redditharbor/agno"}
DRY_RUN=${DRY_RUN:-false}
SKIP_BUILD=${SKIP_BUILD:-false}
SKIP_TESTS=${SKIP_TESTS:-false}
HEALTH_CHECK_TIMEOUT=${HEALTH_CHECK_TIMEOUT:-300}
AUTO_PROMOTE=${AUTO_PROMOTE:-false}
PROMOTE_DELAY=${PROMOTE_DELAY:-1800}  # 30 minutes

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
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
RedditHarbor Phase 5 Canary Deployment

Usage: $0 [OPTIONS]

OPTIONS:
    -p, --canary-percent PERCENT   Percentage of traffic for canary (default: 10)
    -n, --namespace NAMESPACE      Target namespace (default: production)
    -v, --version VERSION         Version to deploy (default: git commit hash)
    -r, --registry REGISTRY       Docker registry (default: your-registry.com)
    -i, --image IMAGE             Full image name (default: redditharbor/agno)
    --dry-run                     Show what would be done without executing
    --skip-build                  Skip Docker build step
    --skip-tests                  Skip pre-deployment tests
    --auto-promote                Automatically promote after delay
    --promote-delay SECONDS       Delay before auto-promotion (default: 1800)
    --health-timeout SECONDS      Health check timeout (default: 300)
    -h, --help                    Show this help message

EXAMPLES:
    # Basic canary deployment with 10% traffic
    $0

    # Deploy 20% canary to staging namespace
    $0 -p 20 -n staging

    # Deploy specific version with auto-promotion
    $0 -v v1.2.3 --auto-promote --promote-delay 3600

    # Dry run to see what would happen
    $0 --dry-run -p 30

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--canary-percent)
                CANARY_PERCENT="$2"
                shift 2
                ;;
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            -r|--registry)
                IMAGE_REGISTRY="$2"
                shift 2
                ;;
            -i|--image)
                IMAGE_NAME="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --auto-promote)
                AUTO_PROMOTE=true
                shift
                ;;
            --promote-delay)
                PROMOTE_DELAY="$2"
                shift 2
                ;;
            --health-timeout)
                HEALTH_CHECK_TIMEOUT="$2"
                shift 2
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

    # Validate arguments
    if [[ ! "$CANARY_PERCENT" =~ ^[0-9]+$ ]] || [[ "$CANARY_PERCENT" -lt 0 ]] || [[ "$CANARY_PERCENT" -gt 100 ]]; then
        error "Canary percentage must be between 0 and 100"
    fi

    # Construct full image path
    IMAGE_TAG="${IMAGE_REGISTRY}/${IMAGE_NAME}:${VERSION}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed"
    fi

    # Check if Docker is installed (if not skipping build)
    if [[ "$SKIP_BUILD" != "true" ]] && ! command -v docker &> /dev/null; then
        error "Docker is not installed"
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
        error "Stable deployment 'redditharbor-agno' not found in namespace '$NAMESPACE'"
    fi

    success "Prerequisites check passed"
}

# Run pre-deployment tests
run_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        log "Skipping pre-deployment tests"
        return 0
    fi

    log "Running pre-deployment tests..."

    # Run unit tests
    if ! python -m pytest tests/ -v; then
        error "Unit tests failed"
    fi

    # Run integration tests
    if ! python scripts/test_apis.py; then
        error "API integration tests failed"
    fi

    # Run performance test
    if ! python scripts/phase5_performance_benchmark.py --quick; then
        error "Performance tests failed"
    fi

    success "All tests passed"
}

# Build Docker image
build_image() {
    if [[ "$SKIP_BUILD" == "true" ]]; then
        log "Skipping Docker build"
        return 0
    fi

    log "Building Docker image: $IMAGE_TAG"

    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY RUN] Would build Docker image: $IMAGE_TAG"
        return 0
    fi

    # Build the image
    if ! docker build -t "$IMAGE_TAG" \
        --build-arg VERSION="$VERSION" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse HEAD 2>/dev/null || echo 'unknown')" \
        .; then
        error "Docker build failed"
    fi

    # Push the image
    log "Pushing Docker image to registry..."
    if ! docker push "$IMAGE_TAG"; then
        error "Docker push failed"
    fi

    success "Docker image built and pushed: $IMAGE_TAG"
}

# Create canary deployment manifest
create_canary_deployment() {
    log "Creating canary deployment manifest..."

    # Calculate number of replicas based on stable deployment
    STABLE_REPLICAS=$(kubectl get deployment redditharbor-agno -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
    CANARY_REPLICAS=1  # Start with 1 replica, can scale based on traffic

    cat > /tmp/canary-deployment.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redditharbor-agno-canary
  namespace: $NAMESPACE
  labels:
    app: redditharbor-agno
    track: canary
    version: $VERSION
spec:
  replicas: $CANARY_REPLICAS
  selector:
    matchLabels:
      app: redditharbor-agno
      track: canary
  template:
    metadata:
      labels:
        app: redditharbor-agno
        track: canary
        version: $VERSION
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: agno-analyzer
        image: $IMAGE_TAG
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
          protocol: TCP
        env:
        - name: COHERE_API_KEY
          valueFrom:
            secretKeyRef:
              name: reddit-harbor-secrets
              key: COHERE_API_KEY
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: reddit-harbor-secrets
              key: OPENROUTER_API_KEY
        - name: AGENTOPS_API_KEY
          valueFrom:
            secretKeyRef:
              name: reddit-harbor-secrets
              key: AGENTOPS_API_KEY
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: reddit-harbor-secrets
              key: DATABASE_URL
        - name: EMBEDDING_PROVIDER
          value: "cohere"
        - name: AGNO_ANALYZER_ENABLED
          value: "true"
        - name: MAX_CONCURRENT_SUBMISSIONS
          value: "50"
        - name: EMBEDDING_BATCH_SIZE
          value: "96"
        - name: LOG_LEVEL
          value: "INFO"
        - name: ENVIRONMENT
          value: "production"
        - name: AGENTOPS_PROJECT_NAME
          value: "reddit-harbor-phase5-canary"
        - name: VERSION
          value: "$VERSION"
        resources:
          requests:
            cpu: 4000m
            memory: 8Gi
          limits:
            cpu: 8000m
            memory: 16Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        startupProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 30

---
apiVersion: v1
kind: Service
metadata:
  name: redditharbor-agno-canary
  namespace: $NAMESPACE
  labels:
    app: redditharbor-agno
    track: canary
spec:
  selector:
    app: redditharbor-agno
    track: canary
  ports:
  - name: http
    port: 80
    targetPort: 8000
    protocol: TCP

---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: redditharbor-agno-canary
  namespace: $NAMESPACE
  labels:
    app: redditharbor-agno
    track: canary
spec:
  selector:
    matchLabels:
      app: redditharbor-agno
      track: canary
  endpoints:
  - port: http
    path: /metrics
    interval: 15s
    scrapeTimeout: 10s
EOF

    log "Canary deployment manifest created"
}

# Setup traffic routing (using Istio VirtualService)
setup_traffic_routing() {
    log "Setting up traffic routing for $CANARY_PERCENT% canary traffic..."

    # Check if Istio is available
    if ! kubectl get crd virtualservices.networking.istio.io &> /dev/null; then
        warn "Istio not found, using simple service-based routing"
        setup_simple_routing
        return 0
    fi

    cat > /tmp/canary-virtual-service.yaml << EOF
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
      weight: $((100 - CANARY_PERCENT))
    - destination:
        host: redditharbor-agno
        subset: canary
      weight: $CANARY_PERCENT

---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: redditharbor-agno
  namespace: $NAMESPACE
spec:
  host: redditharbor-agno
  subsets:
  - name: stable
    labels:
      track: stable
  - name: canary
    labels:
      track: canary
EOF

    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY RUN] Would apply Istio VirtualService and DestinationRule"
        cat /tmp/canary-virtual-service.yaml
        return 0
    fi

    kubectl apply -f /tmp/canary-virtual-service.yaml
    success "Istio traffic routing configured"
}

# Simple routing without Istio
setup_simple_routing() {
    log "Setting up simple service-based routing..."

    # For simple routing, we'll use a different service name
    cat > /tmp/canary-service.yaml << EOF
apiVersion: v1
kind: Service
metadata:
  name: redditharbor-agno-test
  namespace: $NAMESPACE
  labels:
    app: redditharbor-agno
    track: canary
spec:
  selector:
    app: redditharbor-agno
    track: canary
  ports:
  - name: http
    port: 80
    targetPort: 8000
    protocol: TCP
EOF

    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY RUN] Would create test service for canary traffic"
        return 0
    fi

    kubectl apply -f /tmp/canary-service.yaml
    warn "Manual traffic routing required: Use redditharbor-agno-test service for canary testing"
}

# Deploy canary
deploy_canary() {
    log "Deploying canary to namespace: $NAMESPACE"

    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY RUN] Would deploy canary with configuration:"
        cat /tmp/canary-deployment.yaml
        return 0
    fi

    # Apply the deployment
    if ! kubectl apply -f /tmp/canary-deployment.yaml; then
        error "Failed to apply canary deployment"
    fi

    success "Canary deployment applied"
}

# Wait for canary to be ready
wait_for_canary() {
    log "Waiting for canary deployment to be ready..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY RUN] Would wait for deployment to be ready (timeout: ${HEALTH_CHECK_TIMEOUT}s)"
        return 0
    fi

    # Wait for deployment rollout
    if ! kubectl rollout status deployment/redditharbor-agno-canary \
        --namespace="$NAMESPACE" \
        --timeout="${HEALTH_CHECK_TIMEOUT}s"; then
        error "Canary deployment failed to become ready within timeout"
    fi

    # Wait for pods to be ready
    if ! kubectl wait --for=condition=ready pod \
        --selector="app=redditharbor-agno,track=canary" \
        --namespace="$NAMESPACE" \
        --timeout="${HEALTH_CHECK_TIMEOUT}s"; then
        error "Canary pods failed to become ready within timeout"
    fi

    success "Canary deployment is ready"
}

# Run health checks
run_health_checks() {
    log "Running health checks on canary deployment..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY RUN] Would run comprehensive health checks"
        return 0
    fi

    # Get canary pod name
    CANARY_POD=$(kubectl get pods -n "$NAMESPACE" -l track=canary -o jsonpath='{.items[0].metadata.name}')

    # Check basic health endpoint
    for i in {1..10}; do
        if kubectl exec -n "$NAMESPACE" "$CANARY_POD" -- curl -f http://localhost:8000/health; then
            success "Health check $i passed"
            sleep 2
        else
            error "Health check $i failed"
        fi
    done

    # Check detailed health
    kubectl exec -n "$NAMESPACE" "$CANARY_POD" -- curl -f http://localhost:8000/health/detailed

    # Check metrics endpoint
    kubectl exec -n "$NAMESPACE" "$CANARY_POD" -- curl -f http://localhost:8000/metrics

    success "All health checks passed"
}

# Display deployment summary
show_summary() {
    log "=== Canary Deployment Summary ==="
    echo "Version: $VERSION"
    echo "Image: $IMAGE_TAG"
    echo "Namespace: $NAMESPACE"
    echo "Canary Traffic: $CANARY_PERCENT%"
    echo "Deployment Time: $(date)"
    echo ""

    if [[ "$DRY_RUN" != "true" ]]; then
        echo "Canary Pods:"
        kubectl get pods -n "$NAMESPACE" -l track=canary -o wide
        echo ""

        echo "Services:"
        kubectl get svc -n "$NAMESPACE" -l app=redditharbor-agno
        echo ""

        echo "Next Steps:"
        echo "1. Monitor canary performance:"
        echo "   kubectl logs -n $NAMESPACE -l track=canary -f"
        echo ""
        echo "2. Check metrics in Grafana:"
        echo "   https://grafana.company.com/d/canary-dashboard"
        echo ""
        echo "3. Test canary endpoint:"
        if kubectl get crd virtualservices.networking.istio.io &> /dev/null; then
            echo "   curl -H 'x-canary: true' http://redditharbor-agno.$NAMESPACE.svc.cluster.local/health"
        else
            echo "   curl http://redditharbor-agno-test.$NAMESPACE.svc.cluster.local/health"
        fi
        echo ""

        if [[ "$AUTO_PROMOTE" == "true" ]]; then
            echo "4. Auto-promotion scheduled in ${PROMOTE_DELAY} seconds"
            echo "   To cancel: kubectl delete deployment redditharbor-agno-canary -n $NAMESPACE"
        else
            echo "4. To promote to full deployment:"
            echo "   ./scripts/promote-canary.sh -n $NAMESPACE -v $VERSION"
            echo ""
            echo "5. To rollback:"
            echo "   ./scripts/rollback-canary.sh -n $NAMESPACE"
        fi
    fi
}

# Auto-promotion logic
auto_promote() {
    if [[ "$AUTO_PROMOTE" != "true" ]] || [[ "$DRY_RUN" == "true" ]]; then
        return 0
    fi

    log "Scheduling auto-promotion in ${PROMOTE_DELAY} seconds..."

    # Run promotion in background
    (
        sleep "$PROMOTE_DELAY"
        log "Auto-promoting canary deployment..."
        if ./scripts/promote-canary.sh -n "$NAMESPACE" -v "$VERSION" --force; then
            log "Canary successfully auto-promoted"
        else
            error "Auto-promotion failed"
        fi
    ) &

    PROMOTE_PID=$!
    echo $PROMOTE_PID > /tmp/canary-promote.pid
    log "Auto-promotion PID: $PROMOTE_PID"
}

# Cleanup function
cleanup() {
    if [[ -f /tmp/canary-promote.pid ]]; then
        PROMOTE_PID=$(cat /tmp/canary-promote.pid)
        if kill -0 "$PROMOTE_PID" 2>/dev/null; then
            log "Canceling auto-promotion..."
            kill "$PROMOTE_PID"
        fi
        rm -f /tmp/canary-promote.pid
    fi

    # Clean up temporary files
    rm -f /tmp/canary-deployment.yaml
    rm -f /tmp/canary-virtual-service.yaml
    rm -f /tmp/canary-service.yaml
}

# Main execution
main() {
    log "Starting RedditHarbor Phase 5 Canary Deployment..."

    # Set up cleanup trap
    trap cleanup EXIT

    # Parse arguments
    parse_args "$@"

    # Run checks and deployment
    check_prerequisites
    run_tests
    build_image
    create_canary_deployment
    setup_traffic_routing
    deploy_canary
    wait_for_canary
    run_health_checks
    show_summary
    auto_promote

    success "Canary deployment completed successfully!"
}

# Execute main function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi