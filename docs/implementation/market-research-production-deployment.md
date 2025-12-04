# MarketResearchAgent Production Deployment Guide

**Phase 3.7 Production Readiness Documentation**

This guide provides comprehensive instructions for deploying the MarketResearchAgent with Jina integration to production environments, including monitoring, security, and operational procedures.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Security Configuration](#security-configuration)
5. [Monitoring & Observability](#monitoring--observability)
6. [Deployment Architecture](#deployment-architecture)
7. [Deployment Procedures](#deployment-procedures)
8. [Health Checks & Monitoring](#health-checks--monitoring)
9. [Cost Management](#cost-management)
10. [Security & Compliance](#security--compliance)
11. [Troubleshooting](#troubleshooting)
12. [Maintenance & Operations](#maintenance--operations)

---

## Overview

The MarketResearchAgent production deployment includes:

- **Scalable Architecture**: Multi-instance deployment with load balancing
- **Comprehensive Monitoring**: Prometheus metrics, Grafana dashboards, and health checks
- **Resilience Patterns**: Circuit breakers, retry policies, and dead letter queues
- **Security Hardening**: API key rotation, PII anonymization, and audit logging
- **Cost Management**: Budget tracking, usage limits, and cost optimization
- **Operational Excellence**: Automated deployments, rollback procedures, and incident response

### Key Components

1. **MarketResearchAgent**: Core market research functionality
2. **JinaClient**: Web content extraction and search
3. **Monitoring Stack**: Prometheus, Grafana, and custom health checks
4. **Caching Layer**: Redis for performance and cost optimization
5. **Resilience Layer**: Circuit breakers and error handling
6. **Security Layer**: Authentication, authorization, and PII protection

---

## Prerequisites

### Infrastructure Requirements

**Minimum Production Setup:**
- CPU: 4 vCPU cores
- Memory: 8GB RAM
- Storage: 100GB SSD
- Network: 1Gbps connectivity

**Recommended Production Setup:**
- CPU: 8 vCPU cores
- Memory: 16GB RAM
- Storage: 500GB SSD
- Network: 10Gbps connectivity
- High availability: Multi-zone deployment

### Software Dependencies

**Required Services:**
- Python 3.9+
- Redis 6.0+ (for caching)
- PostgreSQL 13+ (for metrics storage)
- Prometheus 2.30+ (for metrics collection)
- Grafana 8.0+ (for visualization)

**Optional Services:**
- Kubernetes 1.20+ (for orchestration)
- Nginx/HAProxy (for load balancing)
- AlertManager (for alert routing)
- Jaeger/Zipkin (for distributed tracing)

### External API Keys

**Required API Access:**
- Jina Reader API key
- LLM API key (OpenAI/Anthropic/other)
- Supabase credentials (for data storage)
- Reddit API credentials (for enhanced research)

---

## Environment Setup

### 1. Production Environment Variables

Create a `.env.production` file with the following configuration:

```bash
# Copy the template and fill in your values
cp .env.production.template .env.production
```

**Critical Security Settings:**
```bash
# API Keys (NEVER commit actual keys)
JINA_API_KEY=your_jina_api_key_here
JINA_LLM_API_KEY=your_llm_api_key_here
ENCRYPTION_KEY=your_32_byte_encryption_key_here

# Security
API_KEY_ROTATION_DAYS=90
ENABLE_PII_ANONYMIZATION=true
SECURITY_HEADERS_ENABLED=true
```

### 2. Database Setup

**Redis Configuration:**
```bash
# Redis for caching
REDIS_HOST=your-redis-host
REDIS_PORT=6379
REDIS_PASSWORD=secure_redis_password
REDIS_SSL=true
REDIS_CONNECTION_POOL_SIZE=20
```

**PostgreSQL Setup (for metrics storage):**
```sql
CREATE DATABASE redditharbor_metrics;
CREATE USER redditharbor WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE redditharbor_metrics TO redditharbor;
```

### 3. Application Configuration

**Performance Settings:**
```bash
# Worker configuration
WORKER_COUNT=4
WORKER_MAX_TASKS_PER_CHILD=1000
WORKER_TIMEOUT_SECONDS=300

# Connection settings
JINA_TIMEOUT_SECONDS=30
JINA_MAX_RETRIES=3
JINA_RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

---

## Security Configuration

### 1. API Key Management

**Rotation Procedure:**
1. Generate new API keys
2. Update environment variables
3. Deploy updated configuration
4. Monitor for service degradation
5. Deactivate old keys after 24 hours

**Key Storage:**
- Use AWS Secrets Manager, Azure Key Vault, or HashiCorp Vault
- Implement automatic key rotation
- Monitor key usage and expiration
- Maintain audit logs of key access

### 2. Network Security

**Firewall Configuration:**
```bash
# Required ports
22    # SSH (admin access only)
80    # HTTP (redirect to HTTPS)
443   # HTTPS (primary access)
8080  # Health checks (internal only)
9090  # Prometheus (internal only)
3001  # Grafana (internal only)
```

**TLS Configuration:**
- Use TLS 1.2+ only
- Implement certificate auto-renewal
- Use strong cipher suites
- Enable HSTS headers

### 3. PII Anonymization

**Configuration:**
```bash
ENABLE_PII_ANONYMIZATION=true
PII_DETECTION_MODEL=en_core_web_lg
PII_ANONYMIZATION_METHOD=mask
```

**Implementation:**
- All web content processed through spaCy NER
- Personal information automatically masked
- Audit trails maintained for compliance
- Data retention policies enforced

---

## Monitoring & Observability

### 1. Metrics Collection

**Prometheus Configuration:**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'market-research-agent'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-host:9121']
```

**Key Metrics:**
- `market_research_requests_total`: Total requests processed
- `market_research_response_time_seconds`: Request latency
- `market_research_cost_total_usd`: Cost tracking
- `market_research_validation_score`: Validation quality
- `market_research_errors_total`: Error counts

### 2. Grafana Dashboards

**Essential Dashboards:**

1. **Market Research Overview**
   - Request rate and success rate
   - Response time percentiles
   - Cost tracking and budget usage
   - Validation score distribution

2. **Infrastructure Health**
   - CPU, memory, and disk usage
   - Redis performance metrics
   - Database connection pool
   - Network latency

3. **Error Analysis**
   - Error rate by type
   - Circuit breaker status
   - Failed request analysis
   - Dead letter queue metrics

### 3. Alerting Configuration

**AlertManager Rules:**
```yaml
# alerts.yml
groups:
  - name: market-research-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(market_research_errors_total[5m]) > 0.05
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate in Market Research Agent"

      - alert: BudgetExceeded
        expr: market_research_daily_budget_remaining_usd < 0
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "Daily budget exceeded"

      - alert: CircuitBreakerOpen
        expr: market_research_circuit_breaker_state{state="OPEN"} == 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Circuit breaker is OPEN"
```

**Notification Channels:**
- Slack: #ops-alerts and #dev-alerts
- Email: ops-team@company.com
- PagerDuty: Critical alerts only
- SMS: Emergency contacts

---

## Deployment Architecture

### 1. High-Level Architecture

```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    │    (HTTPS)      │
                    └─────────┬───────┘
                              │
                    ┌─────────┴───────┐
                    │  Application    │
                    │    Instances    │
                    │  (3+ replicas)  │
                    └─────────┬───────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
    ┌─────────┴─────┐ ┌───────┴───────┐ ┌─────┴─────┐
    │   Redis       │ │ PostgreSQL    │ │  External  │
    │   Cache       │ │   Metrics     │ │   APIs     │
    └───────────────┘ └───────────────┘ └─────────────┘
```

### 2. Container Deployment

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run application
CMD ["python", "-m", "transform.market_research_health", "--host", "0.0.0.0", "--port", "8080"]
```

**Docker Compose:**
```yaml
version: '3.8'

services:
  market-research-agent:
    build: .
    replicas: 3
    environment:
      - REDIS_HOST=redis
      - DATABASE_URL=postgresql://user:pass@postgres:5432/redditharbor
    depends_on:
      - redis
      - postgres
    ports:
      - "8080:8080"
    volumes:
      - ./logs:/app/logs

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=redditharbor_metrics
      - POSTGRES_USER=redditharbor
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning

volumes:
  redis_data:
  postgres_data:
  prometheus_data:
  grafana_data:
```

### 3. Kubernetes Deployment

**Deployment YAML:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: market-research-agent
  labels:
    app: market-research-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: market-research-agent
  template:
    metadata:
      labels:
        app: market-research-agent
    spec:
      containers:
      - name: market-research-agent
        image: your-registry/market-research-agent:latest
        ports:
        - containerPort: 8080
        env:
        - name: REDIS_HOST
          value: "redis-service"
        - name: JINA_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: jina-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: market-research-agent-service
spec:
  selector:
    app: market-research-agent
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP
```

---

## Deployment Procedures

### 1. Pre-Deployment Checklist

**Code Quality:**
- [ ] All tests passing (>95% coverage)
- [ ] Code review completed
- [ ] Security scan passed
- [ ] Performance tests completed
- [ ] Documentation updated

**Infrastructure:**
- [ ] Environment variables configured
- [ ] API keys rotated and tested
- [ ] Database migrations applied
- [ ] Monitoring dashboards updated
- [ ] Alert thresholds configured

**Security:**
- [ ] Secrets management configured
- [ ] TLS certificates renewed
- [ ] Firewall rules updated
- [ ] Access controls verified
- [ ] Audit logging enabled

### 2. Deployment Steps

**Blue-Green Deployment:**
```bash
# 1. Deploy to green environment
kubectl apply -f deployment-green.yaml

# 2. Wait for green pods to be ready
kubectl rollout status deployment/market-research-agent-green

# 3. Run smoke tests
python scripts/smoke_tests.py --environment=green

# 4. Switch traffic to green
kubectl patch service market-research-agent -p '{"spec":{"selector":{"version":"green"}}}'

# 5. Monitor for issues
kubectl logs -f deployment/market-research-agent-green

# 6. Clean up blue environment
kubectl delete deployment market-research-agent-blue
```

**Rollback Procedure:**
```bash
# Quick rollback - switch traffic back
kubectl patch service market-research-agent -p '{"spec":{"selector":{"version":"blue"}}}'

# Full rollback - redeploy previous version
kubectl apply -f deployment-blue.yaml
kubectl rollout undo deployment/market-research-agent
```

### 3. Post-Deployment Validation

**Health Checks:**
```bash
# Check service health
curl https://api.example.com/health

# Check metrics availability
curl https://api.example.com/metrics

# Check circuit breaker status
curl https://api.example.com/health/detailed
```

**Performance Validation:**
```bash
# Load test
python scripts/load_test.py --concurrency=50 --duration=300s

# Cost validation
python scripts/cost_validation.py --budget=500

# Quality validation
python scripts/quality_test.py --sample-size=100
```

---

## Health Checks & Monitoring

### 1. Health Check Endpoints

**Liveness Probe (`/health/live`):**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-04T10:30:00Z",
  "service": "MarketResearchAgent",
  "version": "3.7.0"
}
```

**Readiness Probe (`/health/ready`):**
```json
{
  "ready": true,
  "timestamp": "2024-12-04T10:30:00Z",
  "checks": [
    {
      "name": "market_research_agent",
      "healthy": true,
      "message": "MarketResearchAgent functional",
      "response_time_ms": 245.5
    },
    {
      "name": "circuit_breaker_jina_api",
      "healthy": true,
      "message": "State: CLOSED"
    }
  ]
}
```

**Comprehensive Health (`/health/detailed`):**
```json
{
  "healthy": true,
  "timestamp": "2024-12-04T10:30:00Z",
  "total_response_time_ms": 1250.3,
  "checks": [...],
  "budget": {
    "daily_limit_usd": 500.0,
    "daily_usage_usd": 127.45,
    "usage_percent": 25.5
  },
  "performance": {
    "requests_total": 1250,
    "avg_response_time_ms": 845.2,
    "p95_response_time_ms": 2150.0,
    "p99_response_time_ms": 4800.0
  }
}
```

### 2. Monitoring Setup

**Prometheus Metrics Collection:**
```bash
# Start Prometheus
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

**Grafana Dashboard:**
```bash
# Start Grafana
docker run -d \
  --name grafana \
  -p 3001:3000 \
  -e "GF_SECURITY_ADMIN_PASSWORD=admin" \
  -v grafana-storage:/var/lib/grafana \
  grafana/grafana
```

### 3. Alert Thresholds

**Performance Alerts:**
- Response time P95 > 5 seconds
- Error rate > 5%
- Queue size > 1000 requests

**Budget Alerts:**
- Daily cost > 80% of budget
- Cost per validation > $0.10
- Unusual cost spikes > 200%

**Infrastructure Alerts:**
- CPU usage > 80%
- Memory usage > 85%
- Disk usage > 90%
- Redis memory > 70%

---

## Cost Management

### 1. Budget Configuration

**Daily Budget Limits:**
```bash
# Set daily budget
MONTHLY_JINA_BUDGET_USD=500.0
DAILY_COST_REPORT_ENABLED=true
COST_ALERT_THRESHOLD_PERCENT=80
```

**Usage Limits:**
```bash
# Request limits
MAX_DAILY_REQUESTS=1000
MAX_REQUESTS_PER_MINUTE=60
MAX_COST_PER_REQUEST_USD=0.01
```

### 2. Cost Optimization Strategies

**Caching Strategy:**
- Cache Jina API responses for 24 hours
- Implement intelligent cache warming
- Use Redis for distributed caching
- Monitor cache hit rates (>80% target)

**Request Optimization:**
- Batch multiple queries when possible
- Use intelligent request deduplication
- Implement request prioritization
- Optimize LLM prompt sizes

**API Usage:**
- Monitor API token usage
- Use cost-effective LLM models
- Implement request throttling
- Track cost per operation type

### 3. Cost Monitoring

**Daily Cost Report:**
```python
# Generate daily cost report
async def generate_cost_report():
    monitor = get_monitor()
    report = await monitor.get_daily_report()

    print(f"Daily Usage: ${report['budget']['used_usd']:.2f}")
    print(f"Budget Remaining: ${report['budget']['remaining_usd']:.2f}")
    print(f"Usage Percent: {report['budget']['usage_percent']:.1f}%")
```

**Cost Alerts:**
- Daily budget threshold warnings
- Unusual spending patterns
- API cost per request alerts
- Monthly budget projections

---

## Security & Compliance

### 1. Data Protection

**PII Anonymization:**
```python
# Configuration
ENABLE_PII_ANONYMIZATION=true
PII_DETECTION_MODEL=en_core_web_lg
PII_ANONYMIZATION_METHOD=mask

# Implementation
# All web content automatically processed for PII
# Personal information masked before storage
# Audit trails maintained for compliance
```

**Data Retention:**
```bash
# Retention policies
DATA_RETENTION_DAYS=365
AUDIT_LOG_RETENTION_DAYS=1095
CACHE_RETENTION_DAYS=30
```

### 2. Access Control

**Authentication:**
- API key authentication for all endpoints
- Role-based access control (RBAC)
- JWT tokens for web interface
- Multi-factor authentication for admin access

**Authorization:**
- Principle of least privilege
- Service account isolation
- Network segmentation
- Audit log access control

### 3. Compliance Requirements

**SOC 2 Compliance:**
- Security controls documented
- Audit trails enabled
- Incident response procedures
- Regular security assessments

**GDPR Compliance:**
- Data minimization principles
- Right to erasure procedures
- Data processing agreements
- Privacy policy compliance

**HIPAA Compliance (if applicable):**
- PHI encryption at rest and in transit
- Business associate agreements
- Risk assessments
- Incident notification procedures

---

## Troubleshooting

### 1. Common Issues

**Circuit Breaker Open:**
```bash
# Check circuit breaker status
curl https://api.example.com/health/detailed

# Manually reset (emergency only)
curl -X POST https://api.example.com/admin/circuit-breaker/reset
```

**High Error Rate:**
```bash
# Check recent errors
kubectl logs deployment/market-research-agent --tail=100

# Check external API status
curl -I https://api.jina.ai/

# Check Redis connectivity
redis-cli -h redis-host ping
```

**Performance Degradation:**
```bash
# Check resource usage
kubectl top pods

# Check database connections
kubectl exec -it postgres -- psql -c "SELECT count(*) FROM pg_stat_activity;"

# Check cache hit rate
redis-cli info stats | grep keyspace
```

### 2. Debugging Tools

**Request Tracing:**
```python
# Enable request tracing
TRACE_REQUESTS=true
TRACE_SAMPLE_RATE=0.1  # 10% sampling
```

**Debug Endpoints:**
```bash
# Component health
curl https://api.example.com/health/detailed

# Performance metrics
curl https://api.example.com/metrics

# Configuration status
curl https://api.example.com/admin/config
```

### 3. Incident Response

**Severity Levels:**
- **P0 - Critical**: Service down, data loss, security breach
- **P1 - High**: Significant functionality loss, performance degradation
- **P2 - Medium**: Partial functionality loss, increased error rates
- **P3 - Low**: Minor issues, cosmetic problems

**Response Procedures:**
1. **Detection**: Automated alerts trigger
2. **Assessment**: On-call engineer evaluates impact
3. **Response**: Implement immediate fixes or workarounds
4. **Recovery**: Restore full functionality
5. **Post-mortem**: Document root cause and improvements

---

## Maintenance & Operations

### 1. Regular Maintenance Tasks

**Daily:**
- Review cost and usage reports
- Check error rates and performance metrics
- Verify backup completion
- Review security logs

**Weekly:**
- Update API keys (if needed)
- Review and rotate certificates
- Performance trend analysis
- Cache optimization review

**Monthly:**
- Security patch application
- Database maintenance
- Capacity planning review
- Cost optimization analysis

**Quarterly:**
- Disaster recovery testing
- Security assessment
- Architecture review
- Budget planning

### 2. Backup and Recovery

**Data Backup Strategy:**
```bash
# Daily database backup
pg_dump redditharbor_metrics > backup_$(date +%Y%m%d).sql

# Redis backup
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb backup/redis_$(date +%Y%m%d).rdb
```

**Recovery Procedures:**
1. **Application Recovery**: Restart services from containers
2. **Data Recovery**: Restore from latest backups
3. **Configuration Recovery**: Apply saved configurations
4. **Validation**: Run health checks and smoke tests

### 3. Scaling Procedures

**Horizontal Scaling:**
```bash
# Increase replicas
kubectl scale deployment market-research-agent --replicas=5

# Add worker nodes (Kubernetes)
kubectl scale nodepool production-nodes --count=10
```

**Vertical Scaling:**
```yaml
# Increase resource limits
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

---

## Conclusion

This production deployment guide provides a comprehensive framework for deploying and operating the MarketResearchAgent in production environments. Key takeaways:

1. **Security First**: Implement proper API key management, PII protection, and access controls
2. **Monitoring Essential**: Comprehensive monitoring with Prometheus, Grafana, and health checks
3. **Resilience Critical**: Circuit breakers, retry policies, and dead letter queues
4. **Cost Management**: Budget tracking, usage limits, and optimization strategies
5. **Operational Excellence**: Automated deployments, rollback procedures, and incident response

Following these guidelines ensures a reliable, secure, and cost-effective production deployment of the MarketResearchAgent.

For additional support or questions, refer to the team documentation or contact the DevOps team.