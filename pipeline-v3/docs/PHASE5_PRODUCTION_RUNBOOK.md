# Phase 5: Production Deployment Runbook

**Last Updated**: December 5, 2024
**Version**: 1.0
**Status**: Ready for Production Deployment

---

## Executive Summary

This runbook provides step-by-step instructions for deploying the RedditHarbor Agno multi-agent opportunity analyzer to production with Cohere embeddings integration.

**Key Metrics Achieved:**
- ✅ Embedding Integration: Cohere (embed-english-v3.0) successfully integrated
- ✅ A/B Testing: Comprehensive comparison framework ready
- ⚠️ Performance: Sequential execution limits throughput to ~8 submissions/minute
- ⚠️ Scaling: Requires parallelization for 1000 submissions/minute target

---

## 1. Pre-Deployment Checklist

### 1.1 Environment Verification
```bash
# Check Python version (3.11+ required)
python --version

# Verify UV is installed
uv --version

# Check required packages are installed
uv pip list | grep -E "(cohere|openrouter|agentops)"

# Validate environment variables
cat .env.local | grep -E "(COHERE_|OPENROUTER_|AGNO_|EMBEDDING_)"
```

### 1.2 Infrastructure Requirements
- **Minimum**: 4 CPU cores, 8GB RAM
- **Recommended**: 16 CPU cores, 32GB RAM
- **Storage**: 100GB SSD for logs and cache
- **Network**: 1Gbps for API calls

### 1.3 External Dependencies
```bash
# Test Cohere API connectivity
curl -X POST "https://api.cohere.ai/v1/embed" \
     -H "Authorization: Bearer $COHERE_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"texts": ["test"], "model": "embed-english-v3.0", "input_type": "search_document"}'

# Test OpenRouter API
curl -X POST "https://openrouter.ai/api/v1/chat/completions" \
     -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model": "anthropic/claude-haiku", "messages": [{"role": "user", "content": "test"}]}'

# Test Supabase connection
psql $DATABASE_URL -c "SELECT COUNT(*) FROM opportunities;"
```

---

## 2. Deployment Steps

### 2.1 Application Deployment

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Run unit tests
pytest tests/transform/test_agno_analyzer.py -v

# 3. Run integration tests
python scripts/phase5_ab_comparison.py --dry-run

# 4. Start application (development mode)
python main.py --config production

# 5. Verify health endpoint
curl http://localhost:8000/health
```

### 2.2 Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install UV
RUN pip install uv

# Copy dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Copy application
COPY . .

# Set environment
ENV PYTHONPATH=/app
ENV AGNO_ANALYZER_ENABLED=true
ENV EMBEDDING_PROVIDER=cohere

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  reddit-harbor:
    build: .
    ports:
      - "8000:8000"
    environment:
      - COHERE_API_KEY=${COHERE_API_KEY}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - AGNO_ANALYZER_ENABLED=true
      - EMBEDDING_PROVIDER=cohere
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 2.3 Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: reddit-harbor-agno
  labels:
    app: reddit-harbor-agno
spec:
  replicas: 10
  selector:
    matchLabels:
      app: reddit-harbor-agno
  template:
    metadata:
      labels:
        app: reddit-harbor-agno
    spec:
      containers:
      - name: app
        image: reddit-harbor:latest
        ports:
        - containerPort: 8000
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
        - name: EMBEDDING_PROVIDER
          value: "cohere"
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

## 3. Monitoring and Observability

### 3.1 Health Checks

```python
# main.py
from fastapi import FastAPI
from prometheus_client import Counter, Histogram, Gauge

app = FastAPI()

# Metrics
REQUEST_COUNT = Counter('reddit_harbor_requests_total', 'Total requests')
REQUEST_LATENCY = Histogram('reddit_harbor_request_duration_seconds', 'Request latency')
ACTIVE_ANALYSES = Gauge('reddit_harbor_active_analyses', 'Active analysis processes')

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "embedding_provider": os.getenv("EMBEDDING_PROVIDER", "fake"),
        "agno_enabled": os.getenv("AGNO_ANALYZER_ENABLED", "false") == "true"
    }
```

### 3.2 Prometheus Monitoring

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'reddit-harbor'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

### 3.3 Logging Configuration

```python
# logging_config.py
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": "/app/logs/reddit_harbor.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    },
    "loggers": {
        "": {
            "level": "INFO",
            "handlers": ["console", "file"]
        }
    }
}
```

---

## 4. Scaling and Performance

### 4.1 Horizontal Scaling

```yaml
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: reddit-harbor-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: reddit-harbor-agno
  minReplicas: 5
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 4.2 Performance Tuning

```python
# optimisations.py
import asyncio
from concurrent.futures import ThreadPoolExecutor

class OptimizedAgnoAnalyzer:
    """Optimized Agno analyzer with parallel execution"""

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.semaphore = asyncio.Semaphore(20)  # Limit concurrent API calls

    async def analyze_submission_parallel(self, submission):
        """Analyze submission with parallel agent execution"""
        tasks = []

        # Run agents in parallel
        tasks.append(self._run_agent_async(wtp_agent, submission))
        tasks.append(self._run_agent_async(segment_agent, submission))
        tasks.append(self._run_agent_async(price_agent, submission))
        tasks.append(self._run_agent_async(behavior_agent, submission))

        # Wait for all agents
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        return self._synthesize_results(results)

    async def _run_agent_async(self, agent, submission):
        """Run agent with semaphore control"""
        async with self.semaphore:
            return await agent.analyze(submission)
```

---

## 5. Troubleshooting Guide

### 5.1 Common Issues

#### Issue: High Latency (>10s)
**Symptoms:**
- P99 latency exceeding 10 seconds
- API timeouts
- User complaints

**Solutions:**
```bash
# Check agent execution times
grep -n "Agent.*completed" logs/reddit_harbor.log | tail -20

# Monitor memory usage
docker stats reddit-harbor-agno

# Check for blocking operations
python -m py-spy top --pid $(pgrep -f "python main.py")
```

#### Issue: Cohere API Rate Limits
**Symptoms:**
- HTTP 429 errors
- Analysis failures
- Reduced throughput

**Solutions:**
```python
# Add rate limiting and retry logic
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def call_cohere_with_retry(self, texts):
    """Call Cohere API with retry logic"""
    return await self.cohere_client.embed(texts=texts)
```

#### Issue: Memory Leaks
**Symptoms:**
- Increasing memory usage
- OOM kills
- Slow performance over time

**Solutions:**
```python
# Monitor memory usage
import psutil
import gc

def monitor_memory():
    process = psutil.Process()
    while True:
        memory_mb = process.memory_info().rss / 1024 / 1024
        if memory_mb > 3000:  # 3GB threshold
            gc.collect()  # Force garbage collection
        time.sleep(60)
```

### 5.2 Emergency Procedures

#### Emergency Rollback
```bash
# 1. Switch to fake embeddings
kubectl set env deployment/reddit-harbor-agno EMBEDDING_PROVIDER=fake

# 2. Disable Agno analyzer
kubectl set env deployment/reddit-harbor-agno AGNO_ANALYZER_ENABLED=false

# 3. Scale down
kubectl scale deployment reddit-harbor-agno --replicas=1
```

#### Emergency Scaling
```bash
# Scale up during traffic spikes
kubectl scale deployment reddit-harbor-agno --replicas=50

# Add more nodes if needed
kubectl autoscale deployment reddit-harbor-agno --min=10 --max=100 --cpu-percent=70
```

---

## 6. Maintenance Operations

### 6.1 Daily Checks

```bash
#!/bin/bash
# daily_health_check.sh

echo "=== RedditHarbor Daily Health Check ==="
echo "$(date):"

# Check service status
kubectl get pods -l app=reddit-harbor-agno

# Check error rates
ERROR_RATE=$(kubectl logs -l app=reddit-harbor-agno --since=24h | grep -c "ERROR")
echo "Error count (24h): $ERROR_RATE"

# Check latency
kubectl logs -l app=reddit-harbor-agno --since=1h | grep "latency" | tail -5

# Check API quotas
curl -s "https://api.cohere.ai/v1/rate-limits" -H "Authorization: Bearer $COHERE_API_KEY"

# Check database connections
psql $DATABASE_URL -c "SELECT count(*) FROM opportunities WHERE created_at > now() - interval '24 hours';"
```

### 6.2 Weekly Tasks

```bash
# weekly_maintenance.sh

echo "=== Weekly Maintenance ==="

# Rotate logs
kubectl exec -it deployment/reddit-harbor-agno -- logrotate /etc/logrotate.d/reddit_harbor

# Update packages
uv sync --upgrade

# Performance test
python scripts/phase5_load_test.py --duration 5 --rpm 500

# Database maintenance
psql $DATABASE_URL -c "VACUUM ANALYZE opportunities;"
psql $DATABASE_URL -c "REINDEX INDEX CONCURRENTLY opportunities_embeddings_idx;"
```

---

## 7. Security Considerations

### 7.1 API Key Management

```yaml
# Kubernetes secrets
apiVersion: v1
kind: Secret
metadata:
  name: reddit-harbor-secrets
type: Opaque
data:
  COHERE_API_KEY: <base64-encoded-key>
  OPENROUTER_API_KEY: <base64-encoded-key>
  DATABASE_URL: <base64-encoded-url>
```

### 7.2 Network Security

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: reddit-harbor-network-policy
spec:
  podSelector:
    matchLabels:
      app: reddit-harbor-agno
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: database
    - ports:
    - protocol: TCP
      port: 5432
  - to:
    - ipBlock:
        - cidr: 0.0.0.0/0
        - ports:
        - protocol: TCP
          port: 443  # HTTPS
```

---

## 8. Disaster Recovery

### 8.1 Backup Strategy

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
pg_dump $DATABASE_URL > "backups/reddit_harbor_${DATE}.sql"

# Configuration backup
kubectl get secret reddit-harbor-secrets -o yaml > "backups/secrets_${DATE}.yaml"
kubectl get configmap reddit-harbor-config -o yaml > "backups/config_${DATE}.yaml"

# Upload to S3
aws s3 sync backups/ s3://reddit-harbor-backups/
```

### 8.2 Recovery Procedure

```bash
# restore.sh
DATE="20241205_120000"

# Restore database
psql $DATABASE_URL < "backups/reddit_harbor_${DATE}.sql"

# Restore configuration
kubectl apply -f "backups/secrets_${DATE}.yaml"
kubectl apply -f "backups/config_${DATE}.yaml"

# Restart services
kubectl rollout restart deployment/reddit-harbor-agno
```

---

## 9. Contact and Support

### 9.1 Escalation Contacts
- **Primary Ops**: ops@reddit.harbor.com
- **Engineering**: engineering@reddit.harbor.com
- **On-call**: +1-555-REDDIT-1

### 9.2 Documentation Links
- [Architecture Guide](../docs/agno-integration/README.md)
- [API Documentation](../docs/api/)
- [Monitoring Dashboard](https://grafana.reddit.harbor.com)

---

*This runbook is maintained by the RedditHarbor engineering team. Please report any issues or suggestions to engineering@reddit.harbor.com.*