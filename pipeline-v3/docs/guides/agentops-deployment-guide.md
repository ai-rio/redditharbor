# AgentOps-Agno Integration Deployment Guide

<span style="color:#FF6B35;">●</span> RedditHarbor Pipeline v3
<span style="color:#004E89;">●</span> Production-Ready Configuration
<span style="color:#F7B801;">●</span> DevOps Best Practices

---

## Table of Contents

1. [Overview](#overview)
2. [Production Deployment](#production-deployment)
3. [Development Environment](#development-environment)
4. [CI/CD Integration](#cicd-integration)
5. [Troubleshooting](#troubleshooting)
6. [Performance Optimization](#performance-optimization)
7. [Security Considerations](#security-considerations)
8. [Monitoring and Alerting](#monitoring-and-alerting)

---

## Overview

The AgentOps-Agno integration provides comprehensive observability and cost tracking for the RedditHarbor Pipeline v3. This guide covers deploying and configuring the integration in both development and production environments.

### Key Components

- **AgentOpsTracker**: Core tracking functionality with local fallback
- **AgentOpsProductionManager**: Production-grade monitoring with alerting
- **TrackedWorkflow**: Workflow orchestration with built-in tracking
- **CostTracker**: Real-time cost monitoring and budget management

### Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   TrackedWorkflow │────►│ AgentOpsTracker  │────►│   AgentOps API   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         └──────────────►│ Local Fallback  │◄─────────────┘
                        └─────────────────┘
```

---

## Production Deployment

### Prerequisites

1. **AgentOps Account**
   - Sign up at [https://agentops.ai](https://agentops.ai)
   - Generate API key from dashboard
   - Create a project for pipeline monitoring

2. **Infrastructure Requirements**
   - Kubernetes cluster (recommended) or VM with at least 2 CPU, 4GB RAM
   - Persistent storage for logs (`/var/log/agentops`)
   - Network access to `api.agentops.ai`

3. **Dependencies**
   ```bash
   # Install AgentOps SDK
   pip install agentops
   ```

### Environment Configuration

Create a production environment file:

```bash
# /etc/environment/pipeline-v3-production.env

# ===== AgentOps Configuration =====
export AGENTOPS_API_KEY="prod_key_here"
export AGENTOPS_PROJECT_NAME="reddit-harbor-production"
export AGENTOPS_ENABLED=true
export AGENTOPS_AUTO_START=true
export AGENTOPS_TAGS="production,pipeline-v3,reddit-analysis"
export AGENTOPS_INSTRUMENT_LLM=true

# Cost Tracking Configuration
export COST_TRACKING_ENABLED=true
export COST_BUDGET_LIMIT=1000.0
export COST_ALERT_THRESHOLD=500.0
export AGENTOPS_DAILY_BUDGET=1000.0
export AGENTOPS_HOURLY_BUDGET=50.0
export AGENTOPS_COST_TRACKING=true

# Performance Configuration
export AGENTOPS_PERFORMANCE_TRACKING=true
export AGENTOPS_LATENCY_WARNING=5000
export AGENTOPS_LATENCY_CRITICAL=10000

# Session Configuration
export AGENTOPS_SESSION_DURATION=3600
export AGENTOPS_BATCH_SIZE=10
export AGENTOPS_FLUSH_INTERVAL=1
export AGENTOPS_MAX_RETRIES=3
export AGENTOPS_RETRY_DELAY=1

# Fallback Configuration
export AGENTOPS_LOCAL_FALLBACK=true
export AGENTOPS_LOCAL_PATH="/var/log/agentops"

# ===== Agno Configuration =====
export AGNO_DEBUG_MODE=false
export AGNO_ENABLE_AGENTOPS=true
export AGNO_MODEL="openrouter/meta-llama/llama-3.1-8b-instruct"
export AGNO_ORCHESTRATION_MODE="sequential"
export AGNO_CONSENSUS_THRESHOLD=60.0
export AGNO_TRACK_COSTS=true
```

### Docker/Container Configuration

#### Dockerfile

```dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create log directory
RUN mkdir -p /var/log/agentops && \
    chmod 755 /var/log/agentops

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV AGENTOPS_LOCAL_PATH=/var/log/agentops

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import monitoring.agentops_tracker; print('OK')" || exit 1

# Run the application
CMD ["python", "main.py"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  pipeline-v3:
    build: .
    container_name: reddit-harbor-pipeline
    restart: unless-stopped
    environment:
      # AgentOps Configuration
      - AGENTOPS_API_KEY=${AGENTOPS_API_KEY}
      - AGENTOPS_PROJECT_NAME=reddit-harbor-production
      - AGENTOPS_ENABLED=true
      - AGENTOPS_TAGS=production,pipeline-v3

      # Cost Configuration
      - AGENTOPS_DAILY_BUDGET=1000.0
      - AGENTOPS_HOURLY_BUDGET=50.0
      - AGENTOPS_COST_TRACKING=true

      # Performance Configuration
      - AGENTOPS_PERFORMANCE_TRACKING=true
      - AGENTOPS_LATENCY_WARNING=5000
      - AGENTOPS_LATENCY_CRITICAL=10000

      # Fallback Configuration
      - AGENTOPS_LOCAL_FALLBACK=true
      - AGENTOPS_LOCAL_PATH=/var/log/agentops

      # Agno Configuration
      - AGNO_ENABLE_AGENTOPS=true
      - AGNO_DEBUG_MODE=false

    volumes:
      - ./logs:/var/log/agentops
      - ./config:/app/config:ro

    ports:
      - "8080:8080"  # Health check endpoint

    networks:
      - pipeline-network

    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: reddit_harbor
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - pipeline-network

  redis:
    image: redis:7-alpine
    networks:
      - pipeline-network

volumes:
  postgres_data:

networks:
  pipeline-network:
    driver: bridge
```

### Kubernetes Deployment

#### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: pipeline-v3-config
  namespace: reddit-harbor
data:
  AGENTOPS_PROJECT_NAME: "reddit-harbor-production"
  AGENTOPS_ENABLED: "true"
  AGENTOPS_TAGS: "production,pipeline-v3,k8s"
  AGENTOPS_DAILY_BUDGET: "1000.0"
  AGENTOPS_HOURLY_BUDGET: "50.0"
  AGENTOPS_COST_TRACKING: "true"
  AGENTOPS_PERFORMANCE_TRACKING: "true"
  AGENTOPS_LATENCY_WARNING: "5000"
  AGENTOPS_LATENCY_CRITICAL: "10000"
  AGENTOPS_LOCAL_FALLBACK: "true"
  AGENTOPS_LOCAL_PATH: "/var/log/agentops"
  AGNO_ENABLE_AGENTOPS: "true"
  AGNO_DEBUG_MODE: "false"
```

#### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: pipeline-v3-secrets
  namespace: reddit-harbor
type: Opaque
data:
  AGENTOPS_API_KEY: <base64-encoded-key>
  REDDIT_PUBLIC: <base64-encoded-key>
  REDDIT_SECRET: <base64-encoded-key>
  OPENROUTER_API_KEY: <base64-encoded-key>
```

#### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pipeline-v3
  namespace: reddit-harbor
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pipeline-v3
  template:
    metadata:
      labels:
        app: pipeline-v3
    spec:
      containers:
      - name: pipeline-v3
        image: reddit-harbor/pipeline-v3:latest
        ports:
        - containerPort: 8080
        envFrom:
        - configMapRef:
            name: pipeline-v3-config
        - secretRef:
            name: pipeline-v3-secrets
        volumeMounts:
        - name: log-volume
          mountPath: /var/log/agentops
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: log-volume
        persistentVolumeClaim:
          claimName: agentops-logs-pvc
```

### Production Monitoring Setup

#### 1. AgentOps Dashboard Configuration

```python
# monitoring/setup_agentops_dashboard.py
import agentops
from monitoring.agentops_production_config import create_production_manager

async def setup_production_monitoring():
    """Set up production monitoring with AgentOps"""

    # Create production manager
    manager = create_production_manager()

    # Start monitoring session
    session_id = await manager.start_session(
        session_name="production-session",
        metadata={
            "environment": "production",
            "version": "v3.0.0",
            "deployment": "kubernetes"
        }
    )

    # Configure custom alerts
    await manager.configure_alerts({
        "cost_thresholds": {
            "hourly": 40.0,  # Alert at 80% of $50 budget
            "daily": 800.0   # Alert at 80% of $1000 budget
        },
        "performance_thresholds": {
            "latency_p95": 8000,  # ms
            "error_rate": 0.05     # 5%
        }
    })

    return manager, session_id

if __name__ == "__main__":
    import asyncio
    manager, session_id = asyncio.run(setup_production_monitoring())
    print(f"Production monitoring started: {session_id}")
```

#### 2. Custom Metrics Collection

```python
# monitoring/custom_metrics.py
from monitoring.agentops_tracker import get_tracker
from monitoring.cost_tracker import CostTracker
import asyncio

class ProductionMetrics:
    """Custom metrics for production monitoring"""

    def __init__(self):
        self.tracker = get_tracker()
        self.cost_tracker = CostTracker()

    async def track_pipeline_execution(self,
                                     pipeline_name: str,
                                     submissions_processed: int,
                                     total_cost: float,
                                     execution_time: float):
        """Track complete pipeline execution"""

        # Track with AgentOps
        await self.tracker.track_event("pipeline_execution", {
            "pipeline_name": pipeline_name,
            "submissions_processed": submissions_processed,
            "total_cost": total_cost,
            "execution_time_seconds": execution_time,
            "cost_per_submission": total_cost / submissions_processed if submissions_processed > 0 else 0,
            "submissions_per_minute": submissions_processed / (execution_time / 60) if execution_time > 0 else 0
        })

        # Track cost
        self.cost_tracker.track_cost(total_cost, f"pipeline_{pipeline_name}")
```

---

## Development Environment

### Local Setup

#### 1. Environment Configuration

Create `.env.local` for development:

```bash
# Development Configuration (lower thresholds for testing)
export AGENTOPS_API_KEY="dev_key_here"
export AGENTOPS_PROJECT_NAME="reddit-harbor-development"
export AGENTOPS_ENABLED=true
export AGENTOPS_TAGS="development,pipeline-v3"
export AGENTOPS_DAILY_BUDGET=10.0
export AGENTOPS_HOURLY_BUDGET=1.0
export AGENTOPS_LATENCY_WARNING=2000
export AGENTOPS_LATENCY_CRITICAL=5000

# Development-specific
export AGNO_DEBUG_MODE=true
export LOG_LEVEL=DEBUG
```

#### 2. Mock Configuration

```python
# monitoring/mock_tracker.py
"""Mock AgentOps tracker for development without API key"""

class MockAgentOpsTracker:
    """Mock tracker for development/testing"""

    def __init__(self):
        self.sessions = {}
        self.events = []
        print("🔧 Using Mock AgentOps Tracker (Development Mode)")

    def start_session(self, session_name: str, tags: list = None):
        session_id = f"mock_{session_name}_{int(time.time())}"
        self.sessions[session_id] = {
            "name": session_name,
            "start_time": datetime.now(),
            "tags": tags or []
        }
        print(f"📊 Mock session started: {session_id}")
        return session_id

    def track_event(self, event_name: str, data: dict):
        event = {
            "name": event_name,
            "data": data,
            "timestamp": datetime.now()
        }
        self.events.append(event)
        print(f"📈 Mock event tracked: {event_name}")
        return True

    def end_session(self, session_id: str, status: str = "success"):
        if session_id in self.sessions:
            self.sessions[session_id]["end_time"] = datetime.now()
            self.sessions[session_id]["status"] = status
            print(f"✅ Mock session ended: {session_id} ({status})")
        return {"status": status}
```

#### 3. Local Testing Script

```python
# scripts/test_agentops_integration.py
#!/usr/bin/env python3
"""Test AgentOps integration in development"""

import asyncio
import os
from monitoring.agentops_tracker import get_tracker, AgentOpsConfig

async def test_integration():
    """Test AgentOps integration"""

    # Create test configuration
    config = AgentOpsConfig(
        api_key=os.getenv("AGENTOPS_API_KEY", "test_key"),
        project_name="reddit-harbor-test",
        enabled=True,
        fallback_to_local_tracking=True
    )

    # Get tracker
    tracker = get_tracker()

    # Start test session
    session_id = tracker.start_session(
        session_name="test-integration",
        tags=["test", "development"]
    )
    print(f"Started session: {session_id}")

    # Test tracking
    tracker.track_llm_call(
        model="gpt-4o-mini",
        tokens=100,
        cost=0.001,
        latency=1.5,
        success=True
    )

    tracker.track_latency(
        operation_name="test_operation",
        latency=0.5
    )

    tracker.track_error(
        error_type="test_error",
        error_message="This is a test error"
    )

    # End session
    summary = tracker.end_session("success")
    print(f"Session summary: {summary}")

    return summary

if __name__ == "__main__":
    summary = asyncio.run(test_integration())
```

---

## CI/CD Integration

### GitHub Actions Configuration

```yaml
# .github/workflows/deploy-with-agentops.yml
name: Deploy Pipeline v3 with AgentOps

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  AGENTOPS_PROJECT_NAME: "reddit-harbor-ci-cd"
  AGENTOPS_TAGS: "ci-cd,pipeline-v3"

jobs:
  test-with-agentops:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Configure AgentOps for Testing
      run: |
        echo "AGENTOPS_API_KEY=${{ secrets.AGENTOPS_TEST_KEY }}" >> $GITHUB_ENV
        echo "AGENTOPS_ENABLED=true" >> $GITHUB_ENV
        echo "AGENTOPS_PROJECT_NAME=reddit-harbor-tests" >> $GITHUB_ENV
        echo "AGENTOPS_TAGS=ci-cd,github-actions" >> $GITHUB_ENV

    - name: Run tests with AgentOps tracking
      run: |
        python scripts/run_tests_with_agentops.py

    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  deploy-production:
    needs: test-with-agentops
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v3

    - name: Deploy to production
      run: |
        # Deployment script here
        echo "Deploying to production..."

    - name: Configure production AgentOps
      env:
        AGENTOPS_API_KEY: ${{ secrets.AGENTOPS_PROD_KEY }}
      run: |
        python scripts/setup_production_monitoring.py

    - name: Run smoke tests
      run: |
        python scripts/smoke_test.py
```

### Automated Testing with AgentOps

```python
# scripts/run_tests_with_agentops.py
#!/usr/bin/env python3
"""Run tests with AgentOps tracking"""

import asyncio
import pytest
from monitoring.agentops_tracker import get_tracker

async def main():
    """Run tests with AgentOps tracking"""

    # Initialize tracker
    tracker = get_tracker()

    # Start CI/CD session
    session_id = tracker.start_session(
        session_name="ci-cd-test-run",
        tags=["ci-cd", "testing", "github-actions"]
    )

    try:
        # Run pytest with coverage
        exit_code = pytest.main([
            "--cov=.",
            "--cov-report=xml",
            "--cov-report=html",
            "tests/"
        ])

        # Track test results
        tracker.track_event("test_results", {
            "exit_code": exit_code,
            "total_tests": pytest.total_tests,
            "passed": pytest.passed,
            "failed": pytest.failed,
            "skipped": pytest.skipped
        })

        return exit_code

    except Exception as e:
        tracker.track_error("ci_cd_error", str(e))
        return 1

    finally:
        # End session
        tracker.end_session("success" if exit_code == 0 else "failed")

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
```

### Deployment Pipeline Script

```python
# scripts/deploy_with_monitoring.py
#!/usr/bin/env python3
"""Deploy pipeline with AgentOps monitoring"""

import os
import subprocess
import asyncio
from monitoring.agentops_tracker import get_tracker

async def deploy():
    """Deploy with monitoring"""

    tracker = get_tracker()

    # Start deployment session
    session_id = tracker.start_session(
        session_name="deployment",
        tags=["deployment", "production"]
    )

    deployment_steps = [
        ("build_image", "docker build -t reddit-harbor/pipeline-v3 ."),
        ("push_image", "docker push reddit-harbor/pipeline-v3:latest"),
        ("update_k8s", "kubectl apply -f k8s/"),
        ("verify_deployment", "kubectl rollout status deployment/pipeline-v3")
    ]

    success = True

    for step_name, command in deployment_steps:
        start_time = time.time()

        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=300
            )

            duration = time.time() - start_time

            # Track step
            tracker.track_event("deployment_step", {
                "step": step_name,
                "command": command,
                "success": result.returncode == 0,
                "duration_seconds": duration,
                "stdout": result.stdout[-500:],  # Last 500 chars
                "stderr": result.stderr[-500:]
            })

            if result.returncode != 0:
                success = False
                break

        except subprocess.TimeoutExpired:
            tracker.track_error("deployment_timeout", f"Step {step_name} timed out")
            success = False
            break

    # End session
    status = "success" if success else "failed"
    tracker.end_session(status)

    return 0 if success else 1

if __name__ == "__main__":
    import sys
    import time
    exit_code = asyncio.run(deploy())
    sys.exit(exit_code)
```

---

## Troubleshooting

### Common Deployment Issues

#### 1. AgentOps Initialization Failures

```bash
# Error: Failed to initialize AgentOps
# Solution: Check API key and network connectivity

# Test API key
curl -H "Authorization: Bearer $AGENTOPS_API_KEY" \
     https://api.agentops.io/v1/verify

# Check network
ping api.agentops.io
```

#### 2. Session Management Issues

```python
# Debug session management
from monitoring.agentops_tracker import get_tracker

tracker = get_tracker()
print(f"AgentOps available: {tracker.agentops_available}")
print(f"Current session: {tracker.current_local_session}")
print(f"Local sessions: {list(tracker.local_sessions.keys())}")
```

#### 3. Cost Tracking Discrepancies

```python
# Debug cost tracking
from monitoring.cost_tracker import CostTracker

cost_tracker = CostTracker()
print(f"Total cost: ${cost_tracker.get_total_cost():.6f}")

# Check recent costs
if hasattr(tracker, 'get_recent_costs'):
    recent = tracker.get_recent_costs(limit=10)
    for cost in recent:
        print(f"{cost['timestamp']}: ${cost['amount']:.6f} ({cost['category']})")
```

### Debug Mode Configuration

```python
# monitoring/debug_config.py
"""Debug configuration for AgentOps"""

import logging
from monitoring.agentops_tracker import AgentOpsConfig, AgentOpsTracker

# Enable debug logging
logging.getLogger('agentops').setLevel(logging.DEBUG)
logging.getLogger('monitoring').setLevel(logging.DEBUG)

# Debug configuration
DEBUG_CONFIG = AgentOpsConfig(
    api_key=os.getenv("AGENTOPS_API_KEY"),
    project_name="reddit-harbor-debug",
    enabled=True,
    auto_start_session=True,
    session_tags=["debug", "troubleshooting"],
    instrument_llm_calls=True,
    max_retries=5,
    retry_delay=2.0,
    fallback_to_local_tracking=True
)

# Create debug tracker
debug_tracker = AgentOpsTracker(DEBUG_CONFIG)

# Enable verbose logging
debug_tracker.logger.setLevel(logging.DEBUG)
```

### Production Debugging Script

```python
# scripts/debug_production_issues.py
#!/usr/bin/env python3
"""Debug production issues with AgentOps"""

import asyncio
import json
import os
from datetime import datetime, timedelta

async def debug_production():
    """Debug production issues"""

    # Check environment
    print("=== Environment Check ===")
    required_vars = [
        "AGENTOPS_API_KEY",
        "AGENTOPS_PROJECT_NAME",
        "AGENTOPS_ENABLED",
        "AGENTOPS_DAILY_BUDGET",
        "AGENTOPS_HOURLY_BUDGET"
    ]

    for var in required_vars:
        value = os.getenv(var, "NOT SET")
        print(f"{var}: {'***' if 'KEY' in var else value}")

    # Check AgentOps connectivity
    print("\n=== AgentOps Connectivity ===")
    tracker = get_tracker()
    print(f"AgentOps available: {tracker.agentops_available}")
    print(f"Fallback enabled: {tracker.local_tracking_enabled}")

    # Test tracking
    print("\n=== Tracking Test ===")
    test_session = tracker.start_session("debug-test")
    print(f"Test session: {test_session}")

    success = tracker.track_llm_call(
        model="test-model",
        tokens=10,
        cost=0.00001,
        latency=0.1,
        success=True
    )
    print(f"Tracking test: {'✅' if success else '❌'}")

    summary = tracker.end_session("success")
    print(f"Session summary: {json.dumps(summary, indent=2)}")

    # Check local storage
    print("\n=== Local Storage Check ===")
    local_path = os.getenv("AGENTOPS_LOCAL_PATH", "/var/log/agentops")
    if os.path.exists(local_path):
        files = os.listdir(local_path)
        print(f"Local files: {files}")

        # Check recent logs
        for file in files[:5]:
            file_path = os.path.join(local_path, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                print(f"  {file}: {size} bytes, modified {mtime}")
    else:
        print(f"Local path not found: {local_path}")

if __name__ == "__main__":
    asyncio.run(debug_production())
```

### Error Resolution Guide

| Error | Cause | Solution |
|-------|--------|----------|
| `AgentOpsNotInitialized` | Missing API key or failed init | Check `AGENTOPS_API_KEY` environment variable |
| `SessionTimeoutError` | Session exceeded max duration | Increase `AGENTOPS_SESSION_DURATION` or implement session refresh |
| `CostBudgetExceeded` | Daily/hourly budget exceeded | Increase budget or optimize LLM usage |
| `TrackingRateLimited` | Too many tracking events | Increase `AGENTOPS_BATCH_SIZE` or reduce tracking frequency |
| `LocalStorageError` | Cannot write to local path | Check permissions on `AGENTOPS_LOCAL_PATH` |

---

## Performance Optimization

### Batching Configuration

```python
# monitoring/optimized_tracker.py
"""Optimized AgentOps tracker for high-performance scenarios"""

class OptimizedAgentOpsTracker(AgentOpsTracker):
    """Optimized tracker with performance enhancements"""

    def __init__(self, config: AgentOpsConfig):
        super().__init__(config)

        # Optimized batching
        self._batch_size = 50  # Increased from 10
        self._batch_timeout = 0.5  # Reduced from 1.0

        # Async queue for non-blocking tracking
        self._tracking_queue = asyncio.Queue(maxsize=1000)
        self._processing_task = None

    async def start_async_processing(self):
        """Start background task for processing events"""
        if not self._processing_task:
            self._processing_task = asyncio.create_task(
                self._process_events_background()
            )

    async def _process_events_background(self):
        """Process events in background without blocking"""
        while True:
            try:
                # Wait for events or timeout
                events = []
                try:
                    # Wait for first event
                    event = await asyncio.wait_for(
                        self._tracking_queue.get(),
                        timeout=self._batch_timeout
                    )
                    events.append(event)

                    # Get additional events immediately
                    while len(events) < self._batch_size:
                        try:
                            event = self._tracking_queue.get_nowait()
                            events.append(event)
                        except asyncio.QueueEmpty:
                            break

                except asyncio.TimeoutError:
                    # Process even if no events (timeout)
                    continue

                # Process batch
                await self._process_batch(events)

            except Exception as e:
                logger.error(f"Error processing events: {e}")
                await asyncio.sleep(1)

    async def track_event_async(self, event_name: str, data: dict):
        """Non-blocking event tracking"""
        try:
            await self._tracking_queue.put((event_name, data))
            return True
        except asyncio.QueueFull:
            logger.warning("Tracking queue full, dropping event")
            return False
```

### Caching Strategy

```python
# monitoring/cached_tracker.py
"""AgentOps tracker with intelligent caching"""

from functools import lru_cache
from datetime import datetime, timedelta
import hashlib

class CachedAgentOpsTracker(AgentOpsTracker):
    """Tracker with caching for duplicate events"""

    def __init__(self, config: AgentOpsConfig):
        super().__init__(config)
        self._event_cache = {}
        self._cache_ttl = 60  # seconds

    @lru_cache(maxsize=1000)
    def _get_event_hash(self, event_name: str, data_hash: str) -> str:
        """Generate hash for event deduplication"""
        return hashlib.md5(f"{event_name}{data_hash}".encode()).hexdigest()

    def track_event_cached(self, event_name: str, data: dict) -> bool:
        """Track event with caching to avoid duplicates"""

        # Generate hash
        data_str = json.dumps(data, sort_keys=True)
        event_hash = self._get_event_hash(event_name, data_str)

        # Check cache
        now = datetime.now()
        if event_hash in self._event_cache:
            cached_time = self._event_cache[event_hash]
            if now - cached_time < timedelta(seconds=self._cache_ttl):
                logger.debug(f"Skipping duplicate event: {event_name}")
                return True

        # Track event
        success = self.track_event(event_name, data)

        # Update cache
        if success:
            self._event_cache[event_hash] = now

            # Clean old entries
            cutoff = now - timedelta(seconds=self._cache_ttl * 10)
            self._event_cache = {
                h: t for h, t in self._event_cache.items()
                if t > cutoff
            }

        return success
```

### Resource Allocation

```yaml
# k8s/optimized-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pipeline-v3-optimized
spec:
  template:
    spec:
      containers:
      - name: pipeline-v3
        resources:
          # Base resources for AgentOps tracking
          requests:
            memory: "1Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "4000m"
        env:
        # Optimize for performance
        - name: AGENTOPS_BATCH_SIZE
          value: "50"
        - name: AGENTOPS_FLUSH_INTERVAL
          value: "0.5"
        - name: PYTHONUNBUFFERED
          value: "1"
        - name: UV_THREADPOOL_SIZE
          value: "4"
```

---

## Security Considerations

### API Key Management

#### 1. Kubernetes Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: agentops-secrets
  namespace: reddit-harbor
  annotations:
    kubernetes.io/secret-description: "AgentOps API keys and secrets"
type: Opaque
data:
  # Base64 encoded values
  api-key: <base64-encoded-agentops-api-key>
  project-name: cmVkZGl0LWhhcmJvci1wcm9kdWN0aW9u  # reddit-harbor-production
```

#### 2. AWS Secrets Manager

```python
# security/secrets_manager.py
"""Secure secret management for AgentOps"""

import boto3
import json
from botocore.exceptions import ClientError

class SecretManager:
    """Manage secrets securely"""

    def __init__(self, region_name: str = "us-east-1"):
        self.client = boto3.client('secretsmanager', region_name=region_name)

    def get_agentops_config(self) -> dict:
        """Get AgentOps configuration from Secrets Manager"""
        try:
            response = self.client.get_secret_value(
                SecretId="reddit-harbor/agentops-config"
            )
            secret = json.loads(response['SecretString'])
            return {
                'api_key': secret['api_key'],
                'project_name': secret['project_name'],
                'daily_budget': float(secret.get('daily_budget', '1000.0')),
                'hourly_budget': float(secret.get('hourly_budget', '50.0'))
            }
        except ClientError as e:
            logger.error(f"Failed to get AgentOps config: {e}")
            raise

# Usage in production
secret_manager = SecretManager()
config = secret_manager.get_agentops_config()
```

### Data Privacy

#### 1. PII Filtering

```python
# security/pii_filter.py
"""Filter PII before sending to AgentOps"""

import re
from typing import Dict, Any

class PIIFilter:
    """Filter personally identifiable information"""

    # PII patterns
    PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b\d{3}-\d{3}-\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    }

    def filter_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter PII from dictionary"""
        filtered = {}

        for key, value in data.items():
            if isinstance(value, str):
                filtered[key] = self.filter_text(value)
            elif isinstance(value, dict):
                filtered[key] = self.filter_dict(value)
            elif isinstance(value, list):
                filtered[key] = [
                    self.filter_text(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                filtered[key] = value

        return filtered

    def filter_text(self, text: str) -> str:
        """Filter PII from text"""
        for pattern_name, pattern in self.PATTERNS.items():
            text = re.sub(pattern, f'[REDACTED_{pattern_name.upper()}]', text)
        return text

# Integration with AgentOps
pii_filter = PIIFilter()

def track_with_pii_filter(tracker, event_name: str, data: dict):
    """Track event with PII filtering"""
    filtered_data = pii_filter.filter_dict(data)
    return tracker.track_event(event_name, filtered_data)
```

#### 2. Data Encryption

```python
# security/encryption.py
"""Encrypt sensitive tracking data"""

from cryptography.fernet import Fernet
import os
import base64

class DataEncryption:
    """Encrypt sensitive data before tracking"""

    def __init__(self):
        # Get encryption key from environment or generate
        key = os.getenv('AGENTOPS_ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key()
            print(f"Generated encryption key: {key.decode()}")
        self.cipher = Fernet(key)

    def encrypt(self, data: str) -> str:
        """Encrypt data"""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

    def encrypt_sensitive_fields(self, data: dict) -> dict:
        """Encrypt sensitive fields in data"""
        sensitive_fields = ['api_key', 'token', 'secret', 'password']

        for key, value in data.items():
            if any(field in key.lower() for field in sensitive_fields):
                if isinstance(value, str):
                    data[key] = self.encrypt(value)

        return data
```

### Access Control

#### 1. RBAC Configuration

```yaml
# k8s/rbac.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: reddit-harbor
  name: agentops-operator
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list"]
  resourceNames: ["agentops-secrets"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: agentops-binding
  namespace: reddit-harbor
subjects:
- kind: ServiceAccount
  name: pipeline-v3
  namespace: reddit-harbor
roleRef:
  kind: Role
  name: agentops-operator
  apiGroup: rbac.authorization.k8s.io
```

#### 2. Network Policies

```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: agentops-network-policy
  namespace: reddit-harbor
spec:
  podSelector:
    matchLabels:
      app: pipeline-v3
  egress:
  - to:
    - ipBlock:
        cidr: 35.227.118.175/32  # AgentOps API
    ports:
    - protocol: TCP
      port: 443
  - to: []
    ports:
    - protocol: TCP
      port: 53  # DNS
    - protocol: UDP
      port: 53  # DNS
```

---

## Monitoring and Alerting

### Custom Dashboards

#### 1. Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "RedditHarbor Pipeline - AgentOps Monitoring",
    "panels": [
      {
        "title": "Daily Cost Tracking",
        "type": "stat",
        "targets": [
          {
            "expr": "agentops_daily_cost_total",
            "legendFormat": "Daily Cost ($)"
          }
        ]
      },
      {
        "title": "LLM Call Latency",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(agentops_llm_latency_seconds_bucket[5m]))",
            "legendFormat": "P95 Latency (s)"
          },
          {
            "expr": "histogram_quantile(0.50, rate(agentops_llm_latency_seconds_bucket[5m]))",
            "legendFormat": "P50 Latency (s)"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "rate(agentops_errors_total[5m]) / rate(agentops_operations_total[5m])",
            "legendFormat": "Error Rate"
          }
        ]
      },
      {
        "title": "Token Usage by Model",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum by (model) (agentops_tokens_total)",
            "legendFormat": "{{model}}"
          }
        ]
      }
    ]
  }
}
```

#### 2. Prometheus Metrics Exporter

```python
# monitoring/prometheus_exporter.py
"""Export AgentOps metrics to Prometheus"""

from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Define metrics
REQUEST_COUNT = Counter(
    'agentops_requests_total',
    'Total number of AgentOps requests',
    ['status', 'endpoint']
)

REQUEST_LATENCY = Histogram(
    'agentops_request_latency_seconds',
    'AgentOps request latency',
    ['endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

COST_TRACKER = Gauge(
    'agentops_daily_cost_total',
    'Total daily cost in USD',
    ['project']
)

TOKEN_USAGE = Counter(
    'agentops_tokens_total',
    'Total tokens used',
    ['model', 'type']  # type: prompt, completion
)

ERROR_COUNT = Counter(
    'agentops_errors_total',
    'Total number of errors',
    ['error_type', 'severity']
)

class PrometheusExporter:
    """Export AgentOps metrics to Prometheus"""

    def __init__(self, port: int = 8000):
        self.port = port
        start_http_server(port)
        print(f"Prometheus exporter started on port {port}")

    def track_request(self, endpoint: str, status: str, latency: float):
        """Track a request"""
        REQUEST_COUNT.labels(status=status, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(latency)

    def update_cost(self, project: str, cost: float):
        """Update cost metric"""
        COST_TRACKER.labels(project=project).set(cost)

    def track_tokens(self, model: str, prompt_tokens: int, completion_tokens: int):
        """Track token usage"""
        TOKEN_USAGE.labels(model=model, type='prompt').inc(prompt_tokens)
        TOKEN_USAGE.labels(model=model, type='completion').inc(completion_tokens)

    def track_error(self, error_type: str, severity: str):
        """Track an error"""
        ERROR_COUNT.labels(error_type=error_type, severity=severity).inc()
```

### Alert Rules

#### 1. Prometheus Alert Rules

```yaml
# alerts/agentops-alerts.yaml
groups:
- name: agentops.rules
  rules:
  - alert: AgentOpsHighCostRate
    expr: rate(agentops_daily_cost_total[1h]) > 5.0
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High cost rate detected"
      description: "Cost rate is ${{ $value | humanize }}/hour"

  - alert: AgentOpsHighLatency
    expr: histogram_quantile(0.95, rate(agentops_request_latency_seconds_bucket[5m])) > 5.0
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High P95 latency"
      description: "P95 latency is {{ $value }}s"

  - alert: AgentOpsHighErrorRate
    expr: rate(agentops_errors_total[5m]) / rate(agentops_requests_total[5m]) > 0.1
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "High error rate"
      description: "Error rate is {{ $value | humanizePercentage }}"

  - alert: AgentOpsDailyBudgetExceeded
    expr: agentops_daily_cost_total > 1000
    for: 0m
    labels:
      severity: critical
    annotations:
      summary: "Daily budget exceeded"
      description: "Daily cost ${{ $value }} exceeds budget of $1000"
```

#### 2. PagerDuty Integration

```python
# monitoring/pagerduty_integration.py
"""Integrate AgentOps alerts with PagerDuty"""

import requests
import json

class PagerDutyIntegration:
    """Send critical alerts to PagerDuty"""

    def __init__(self, integration_key: str):
        self.integration_key = integration_key
        self.api_url = "https://events.pagerduty.com/v2/enqueue"

    def trigger_alert(self,
                     summary: str,
                     severity: str,
                     source: str = "agentops",
                     details: dict = None):
        """Trigger PagerDuty alert"""

        payload = {
            "routing_key": self.integration_key,
            "event_action": "trigger",
            "payload": {
                "summary": summary,
                "severity": severity,
                "source": source,
                "timestamp": "2023-12-09T07:00:00.000Z",
                "custom_details": details or {}
            }
        }

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 202:
                print(f"PagerDuty alert triggered: {summary}")
            else:
                print(f"Failed to trigger PagerDuty alert: {response.text}")

        except Exception as e:
            print(f"Error triggering PagerDuty alert: {e}")

# Integration with AgentOps production manager
async def setup_pagerduty_alerts(manager):
    """Set up PagerDuty alerts for critical events"""

    pagerduty = PagerDutyIntegration(
        integration_key=os.getenv("PAGERDUTY_INTEGRATION_KEY")
    )

    # Override alert method to send to PagerDuty
    original_send_alert = manager._send_alert

    async def send_alert_with_pagerduty(alert_type, message, severity, metadata=None):
        # Send original alert
        await original_send_alert(alert_type, message, severity, metadata)

        # Send to PagerDuty for critical alerts
        if severity == "critical":
            pagerduty.trigger_alert(
                summary=message,
                severity="critical",
                source="agentops",
                details=metadata
            )

    manager._send_alert = send_alert_with_pagerduty
```

### Health Checks

```python
# monitoring/health_check.py
"""Health check for AgentOps integration"""

from fastapi import FastAPI, HTTPException
from monitoring.agentops_tracker import get_tracker
from monitoring.agentops_production_config import create_production_manager
import asyncio

app = FastAPI()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agentops": "connected"}

@app.get("/health/agentops")
async def agentops_health():
    """Detailed AgentOps health check"""

    tracker = get_tracker()

    health = {
        "agentops_available": tracker.agentops_available,
        "local_tracking_enabled": tracker.local_tracking_enabled,
        "active_session": tracker.current_local_session is not None,
        "total_sessions": len(tracker.local_sessions),
        "recent_errors": 0
    }

    # Check recent errors
    if tracker.current_local_session:
        session_metrics = tracker.local_sessions.get(tracker.current_local_session)
        if session_metrics:
            health["recent_errors"] = len(session_metrics.errors)

    # Determine status
    if not tracker.agentops_available and not tracker.local_tracking_enabled:
        raise HTTPException(status_code=503, detail="AgentOps unavailable and local tracking disabled")

    if health["recent_errors"] > 10:
        raise HTTPException(status_code=500, detail="High error rate detected")

    return health

@app.get("/metrics/cost")
async def cost_metrics():
    """Get current cost metrics"""

    manager = create_production_manager()
    summary = manager.get_metrics_summary()

    return {
        "current_hourly_cost": summary["costs"]["current_hourly"],
        "current_daily_cost": summary["costs"]["current_daily"],
        "hourly_budget": summary["costs"]["hourly_budget"],
        "daily_budget": summary["costs"]["daily_budget"],
        "hourly_budget_remaining": summary["costs"]["hourly_budget_remaining"],
        "daily_budget_remaining": summary["costs"]["daily_budget_remaining"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

---

## Conclusion

This comprehensive deployment guide provides everything needed to successfully deploy and operate the AgentOps-Agno integration in production. Key takeaways:

1. **Start with development configuration** to understand the tracking behavior
2. **Implement proper security** including API key management and PII filtering
3. **Set up monitoring and alerting** to track costs and performance
4. **Use fallback mechanisms** to ensure reliability even if AgentOps is unavailable
5. **Optimize for performance** with batching and caching strategies

For additional support, refer to:
- [AgentOps Documentation](https://docs.agentops.ai)
- [RedditHarbor Architecture Guide](../architecture/)
- [Performance Optimization Guide](./performance-optimization.md)

Remember to regularly review and update your configuration as your usage patterns evolve.