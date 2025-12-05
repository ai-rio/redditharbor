# RedditHarbor Phase 5 Operations Guide

**Last Updated**: December 5, 2024
**Version**: 1.0
**Audience**: Operations Teams, SREs, DevOps Engineers

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Daily Operations](#daily-operations)
4. [Monitoring and Alerting](#monitoring-and-alerting)
5. [Deployment Management](#deployment-management)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance Procedures](#maintenance-procedures)
8. [Emergency Procedures](#emergency-procedures)
9. [Performance Optimization](#performance-optimization)
10. [Cost Management](#cost-management)

---

## Overview

RedditHarbor Phase 5 is a production-ready multi-agent system for Reddit opportunity analysis with the following key characteristics:

- **Target Throughput**: 1000 submissions/minute
- **Latency Target**: P99 < 10 seconds
- **Availability Target**: 99.9% uptime
- **Deployment Strategy**: Canary deployments with gradual traffic switching
- **Monitoring Stack**: AgentOps + Prometheus + Grafana
- **Cost Tracking**: Real-time LLM and embedding cost monitoring

---

## System Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer (HAProxy)                   │
└─────────────┬───────────────────────────────────────────────┘
              │
      ┌───────┼───────┐
      │       │       │
┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
│  Stable    │ │  Canary   │ │ Previous   │
│Deployment  │ │Deployment │ │ Deployment │
│ (Primary)  │ │ (Testing) │ │ (Backup)   │
└─────┬─────┘ └─────┬─────┘ └─────┬─────┘
      │             │             │
      └───────┬─────┴─────────────┘
              │
┌─────────────▼─────────────┐
│    RedditHarbor Services   │
│  ├─ Agno Analyzer (4x)    │
│  ├─ Embedding Service     │
│  └─ API Gateway           │
└─────────────┬─────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
┌───▼──┐ ┌───▼──┐ ┌───▼──┐
│Cohere│ │OpenR │ │AgentO│
│Embed │ │outer │ │ps    │
└───┬──┘ └───┬──┘ └───┬──┘
    │         │         │
    └─────────┼─────────┘
              │
      ┌───────▼───────┐
      │  PostgreSQL   │
      │ + pgvector    │
      └───────────────┘
```

### Key Services

- **Agno Analyzer**: Core multi-agent analysis engine
  - WTP Agent: Win-The-Platform analysis
  - Segment Agent: Market segment identification
  - Price Agent: Pricing strategy analysis
  - Behavior Agent: User behavior modeling

- **Embedding Service**: Text vectorization using Cohere embeddings
  - Batch processing (96 texts per request)
  - Local caching for similar embeddings
  - Fallback to OpenRouter if needed

- **API Gateway**: Request routing and load balancing
  - Rate limiting
  - Request validation
  - Response caching

### External Dependencies

| Service | Purpose | Rate Limit | Cost | Backup |
|---------|---------|------------|------|--------|
| Cohere | Embeddings | 500/minute | $0.10/M tokens | OpenRouter |
| OpenRouter | LLM API | 500/minute | $0.002/analysis | Multiple models |
| AgentOps | Monitoring | N/A | $50/month | Local tracking |

---

## Daily Operations

### Morning Checklist (06:00 UTC)

```bash
#!/bin/bash
# scripts/morning-checklist.sh

echo "=== RedditHarbor Phase 5 Daily Checklist ==="
echo "Date: $(date)"
echo "Operator: $(whoami)"

# 1. Check system overview
echo "1. System Overview"
./scripts/health-monitor.py --format json > /tmp/health-$(date +%Y%m%d).json

# 2. Review overnight performance
echo "2. Overnight Performance"
curl -s "http://prometheus:9090/api/v1/query_range?query=rate(reddit_harbor_submissions_total[5m])*60&start=$(date -d '12 hours ago' -u +%s)&end=$(date -u +%s)&step=300" | \
  jq '.data.result | length' > /tmp/overnight-samples.log

# 3. Check error rates
echo "3. Error Rate Summary"
ERROR_RATE=$(curl -s "http://prometheus:9090/api/v1/query?query=rate(reddit_harbor_errors_total[1h])/rate(reddit_harbor_submissions_total[1h])*100" | \
  jq -r '.data.result[0].value[1]')
echo "Error rate (last hour): ${ERROR_RATE}%"

# 4. Cost summary
echo "4. Cost Summary"
DAILY_COST=$(curl -s "http://prometheus:9090/api/v1/query?query=increase(agentops_cost_total[24h])" | \
  jq -r '.data.result[0].value[1]')
echo "Daily cost: $${DAILY_COST:-0}"

# 5. Check alerts
echo "5. Active Alerts"
kubectl get servicemonitor -n monitoring | grep reddit-harbor

# 6. Review logs
echo "6. Log Summary"
ERROR_COUNT=$(kubectl logs -n production -l app=redditharbor-agno --since=24h | grep ERROR | wc -l)
echo "Errors in last 24h: $ERROR_COUNT"

# 7. Resource utilization
echo "7. Resource Utilization"
kubectl top pods -n production -l app=redditharbor-agno | tail -5

echo "=== Morning Checklist Complete ==="
```

### Shift Handoff

Before each shift change, the on-call engineer should:

1. **Review Current Status**
   ```bash
   # Check overall health
   ./scripts/health-monitor.py

   # Review recent incidents
   kubectl get events -n production --sort-by='.lastTimestamp' | tail -10

   # Check active alerts
   curl -s "http://alertmanager:9093/api/v1/alerts" | jq '.[] | select(.state=="firing") | .labels.alertname'
   ```

2. **Update Runbook**
   - Document any manual interventions
   - Note performance anomalies
   - Record any configuration changes

3. **Communicate to Next Shift**
   - Use Slack channel `#ops-handoff`
   - Include key metrics and any ongoing issues
   - Reference any tickets or incidents

### Daily Reporting

Automated daily reports are sent at 00:00 UTC with:

- **Performance Metrics**
  - Total submissions processed
  - Average latency (P50, P95, P99)
  - Error rate and types
  - Throughput variations

- **Cost Analysis**
  - Daily spend by provider
  - Cost per analysis
  - Budget utilization
  - Cost optimization suggestions

- **Infrastructure Health**
  - Pod restart counts
  - Resource utilization
  - Database performance
  - External API status

---

## Monitoring and Alerting

### Monitoring Stack Components

1. **AgentOps**
   - Application-level monitoring
   - LLM cost tracking
   - Agent execution tracing
   - Performance analytics

2. **Prometheus**
   - System metrics collection
   - Custom application metrics
   - Alert rule evaluation
   - Long-term data storage

3. **Grafana**
   - Real-time dashboards
   - Historical data visualization
   - Alert management
   - Custom panels

### Key Metrics to Monitor

#### Application Metrics
```yaml
application_metrics:
  throughput:
    - reddit_harbor_submissions_total
    - reddit_harbor_submissions_per_second
    - reddit_harbor_active_analyses

  latency:
    - reddit_harbor_request_duration_seconds
    - reddit_harbor_agent_execution_time
    - reddit_harbor_embedding_generation_time

  errors:
    - reddit_harbor_errors_total
    - reddit_harbor_error_rate
    - reddit_harbor_timeout_rate

  business:
    - reddit_harbor_analysis_success_rate
    - reddit_harbor_opportunities_identified
    - reddit_harbor_quality_score_distribution
```

#### Infrastructure Metrics
```yaml
infrastructure_metrics:
  kubernetes:
    - kube_pod_status_phase
    - kube_deployment_status_replicas
    - kube_node_status_condition

  database:
    - pg_stat_activity_count
    - pg_stat_statements_mean_time
    - pg_database_size_bytes

  external_apis:
    - cohere_api_requests_total
    - cohere_api_request_duration_seconds
    - openrouter_api_requests_total
    - agentops_events_total
```

#### Cost Metrics
```yaml
cost_metrics:
  provider_costs:
    - agentops_cost_by_provider
    - agentops_cost_by_model
    - agentops_cost_per_operation

  budgets:
    - agentops_daily_budget_usage
    - agentops_hourly_budget_usage
    - agentops_cost_trend
```

### Alerting Rules

#### Critical Alerts (Page immediately)
```yaml
critical_alerts:
  service_down:
    - reddit_harbor_up == 0
    - kubenretes_pod_crash_looping
    - database_connection_failed

  performance_degraded:
    - p99_latency > 15s
    - error_rate > 10%
    - throughput < 200/min

  cost_overrun:
    - hourly_cost > $100
    - daily_cost > $1000
```

#### Warning Alerts (Email/Slack)
```yaml
warning_alerts:
  performance_warning:
    - p99_latency > 10s
    - error_rate > 5%
    - throughput < 500/min

  resource_usage:
    - cpu_usage > 80%
    - memory_usage > 85%
    - disk_usage > 90%

  api_warnings:
    - cohere_api_latency > 5s
    - openrouter_api_error_rate > 5%
```

### Dashboard URLs

- **Main Dashboard**: https://grafana.company.com/d/redditharbor-main
- **Performance Dashboard**: https://grafana.company.com/d/redditharbor-performance
- **Cost Dashboard**: https://grafana.company.com/d/redditharbor-costs
- **Infrastructure Dashboard**: https://grafana.company.com/d/redditharbor-infra

---

## Deployment Management

### Deployment Process

1. **Pre-deployment Checks**
   ```bash
   # Verify environment
   ./scripts/verify-deployment.sh -n staging

   # Run health checks
   ./scripts/health-monitor.py

   # Check costs are within budget
   curl -s "http://prometheus:9090/api/v1/query?query=increase(agentops_cost_total[1h])"
   ```

2. **Canary Deployment**
   ```bash
   # Deploy 10% canary
   ./scripts/deploy-canary.sh -p 10

   # Monitor for 30 minutes
   ./scripts/health-monitor.py --continuous --interval 60 &
   MONITOR_PID=$!
   sleep 1800
   kill $MONITOR_PID
   ```

3. **Gradual Traffic Increase**
   ```bash
   # Increase to 25%
   ./scripts/traffic-switch.sh split 25

   # Monitor and validate
   ./scripts/verify-deployment.sh

   # Continue to 50%, 75%, 100%
   ./scripts/traffic-switch.sh split 50
   ./scripts/traffic-switch.sh split 75
   ./scripts/traffic-switch.sh all-canary
   ```

4. **Promotion**
   ```bash
   # Promote canary to stable
   ./scripts/promote-canary.sh -n production

   # Clean up old version
   ./scripts/cleanup-old-deployment.sh --keep-last 2
   ```

### Rollback Procedures

#### Emergency Rollback
```bash
# Immediate rollback to stable
./scripts/rollback-canary.sh --force --skip-confirmation

# Or using traffic switching
./scripts/traffic-switch.sh all-stable
```

#### Gradual Rollback
```bash
# Reduce canary traffic gradually
./scripts/traffic-switch.sh split 50
./scripts/traffic-switch.sh split 25
./scripts/traffic-switch.sh split 10
./scripts/traffic-switch.sh all-stable

# Then remove canary
kubectl delete deployment redditharbor-agno-canary -n production
```

### Blue-Green Deployment Support

While we primarily use canary deployments, blue-green is supported:

```bash
# Deploy to green environment
./scripts/deploy-bluegreen.sh --target green

# Switch traffic
./scripts/switch-bluegreen.sh --target green

# Keep blue for rollback
./scripts/keep-blue-deployment.sh
```

---

## Troubleshooting

### Common Issues and Solutions

#### High Latency

**Symptoms**:
- P99 latency > 10 seconds
- User complaints about slow responses
- Timeout errors increasing

**Diagnosis**:
```bash
# Check agent execution times
kubectl logs -n production -l app=redditharbor-agno | grep "agent.*completed" | tail -20

# Check API provider latency
curl -s "http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95,rate(cohere_request_duration_seconds_bucket[5m]))"

# Check database query performance
psql $DATABASE_URL -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

**Solutions**:
1. **Scale up deployment**:
   ```bash
   kubectl scale deployment redditharbor-agno -n production --replicas=10
   ```

2. **Optimize batch sizes**:
   ```yaml
   # Reduce embedding batch size if API is slow
   embedding_batch_size: 48  # From 96
   ```

3. **Enable local caching**:
   ```yaml
   enable_embedding_cache: true
   cache_ttl: 3600
   ```

#### High Error Rate

**Symptoms**:
- Error rate > 5%
- Failed submissions increasing
- API provider errors

**Diagnosis**:
```bash
# Check error types
kubectl logs -n production -l app=redditharbor-agno | grep ERROR | sort | uniq -c

# Check API provider status
curl -s https://status.cohere.ai
curl -s https://status.openrouter.ai

# Check rate limits
curl -s -H "Authorization: Bearer $COHERE_API_KEY" https://api.cohere.ai/v1/rate-limits
```

**Solutions**:
1. **Implement circuit breaker**:
   ```yaml
   circuit_breaker:
     enabled: true
     failure_threshold: 5
     timeout: 60
   ```

2. **Add retry logic**:
   ```yaml
   retry_policy:
     max_attempts: 3
     backoff: exponential
     base_delay: 1
   ```

3. **Reduce concurrency**:
   ```yaml
   max_concurrent_submissions: 30  # From 50
   ```

#### Memory Leaks

**Symptoms**:
- Memory usage increasing over time
- OOMKilled events
- Slow performance over time

**Diagnosis**:
```bash
# Check memory usage
kubectl top pods -n production -l app=redditharbor-agno

# Check for OOM kills
kubectl describe pods -n production -l app=redditharbor-agno | grep OOMKilled

# Analyze memory patterns
python scripts/memory-analyzer.py --pod <pod-name>
```

**Solutions**:
1. **Reduce batch sizes**:
   ```yaml
   embedding_batch_size: 48
   agent_batch_size: 5
   ```

2. **Enable garbage collection**:
   ```python
   import gc
   gc.set_threshold(700, 10, 10)
   ```

3. **Add memory limits**:
   ```yaml
   resources:
     requests:
       memory: 8Gi
     limits:
       memory: 16Gi
   ```

#### Database Issues

**Symptoms**:
- Database connection errors
- Slow query performance
- Connection pool exhaustion

**Diagnosis**:
```bash
# Check connection count
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"

# Check slow queries
psql $DATABASE_URL -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check locks
psql $DATABASE_URL -c "SELECT * FROM pg_locks WHERE NOT granted;"
```

**Solutions**:
1. **Increase connection pool**:
   ```yaml
   database_pool:
     size: 20
     max_overflow: 30
   ```

2. **Add indexes**:
   ```sql
   CREATE INDEX CONCURRENTLY idx_opportunities_embedding_cosine
   ON opportunities USING pgvector (embedding vector_cosine_ops);
   ```

3. **Optimize queries**:
   ```sql
   EXPLAIN ANALYZE SELECT * FROM opportunities WHERE created_at > NOW() - INTERVAL '1 hour';
   ```

### Debugging Tools

#### Health Monitoring
```bash
# Continuous health monitoring
./scripts/health-monitor.py --continuous --alerts-file /var/log/health-alerts.log

# Detailed health check
curl -s http://redditharbor-agno.production.svc.cluster.local/health/detailed | jq .
```

#### Log Analysis
```bash
# Real-time logs
kubectl logs -n production -l app=redditharbor-agno -f

# Error logs only
kubectl logs -n production -l app=redditharbor-agno | grep ERROR

# Analyze patterns
kubectl logs -n production -l app=redditharbor-agno --since=1h | \
  grep -E "(ERROR|WARN)" | sort | uniq -c | sort -nr
```

#### Performance Profiling
```bash
# Generate flame graph
kubectl exec -it <pod-name> -- py-spy top --pid 1 --output profile.svg

# Memory profiling
kubectl exec -it <pod-name> -- py-spy top --pid 1 --memory
```

---

## Maintenance Procedures

### Weekly Maintenance

Every Sunday at 02:00 UTC:

```bash
#!/bin/bash
# scripts/weekly-maintenance.sh

echo "=== Weekly Maintenance ==="

# 1. Rotate logs
kubectl exec -n production deployment/redditharbor-agno -- logrotate /etc/logrotate.d/redditharbor

# 2. Update dependencies (staging first)
cd /home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3
uv pip list --outdated

# 3. Performance baseline
python scripts/phase5_performance_benchmark.py --duration 600 --target-rpm 800

# 4. Database maintenance
psql $DATABASE_URL -c "VACUUM ANALYZE opportunities;"
psql $DATABASE_URL -c "REINDEX DATABASE $PGDATABASE;"

# 5. Clean up old AgentOps sessions
python scripts/cleanup_old_sessions.py --days 7

# 6. Check disk usage
df -h | grep -E "/$|/var|/opt"

# 7. Update monitoring rules
kubectl apply -f monitoring/alert-rules.yaml

# 8. Backup configurations
kubectl get deployment redditharbor-agno -n production -o yaml > /backups/deployment-$(date +%Y%m%d).yaml

echo "=== Weekly Maintenance Complete ==="
```

### Monthly Maintenance

First of each month:

1. **Capacity Planning Review**
   - Review growth trends
   - Plan infrastructure scaling
   - Update resource limits

2. **Cost Optimization Review**
   - Analyze cost per analysis
   - Review provider pricing
   - Implement optimizations

3. **Security Updates**
   - Update base images
   - Patch dependencies
   - Review security scans

4. **Documentation Updates**
   - Update runbooks
   - Add new procedures
   - Review incident reports

### Quarterly Maintenance

End of each quarter:

1. **Architecture Review**
   - Evaluate current design
   - Plan improvements
   - Review tech debt

2. **Disaster Recovery Test**
   - Test backup/restore
   - Verify failover procedures
   - Update DR documentation

3. **Performance Tuning**
   - Optimize bottlenecks
   - Update baselines
   - Implement improvements

---

## Emergency Procedures

### Service Outage

When service is completely down:

1. **Immediate Actions**
   ```bash
   # Check all pods
   kubectl get pods -n production -o wide

   # Check recent deployments
   kubectl rollout history deployment/redditharbor-agno -n production

   # Check events
   kubectl get events -n production --sort-by='.lastTimestamp' | tail -20
   ```

2. **Quick Recovery**
   ```bash
   # Restart deployment
   kubectl rollout restart deployment/redditharbor-agno -n production

   # Or rollback to last known good
   kubectl rollout undo deployment/redditharbor-agno -n production

   # Verify recovery
   ./scripts/health-monitor.py
   ```

3. **Communication**
   - Post to Slack #incidents
   - Update status page
   - Notify stakeholders

### Database Emergency

When database is unavailable:

1. **Switch to read-only mode**
   ```bash
   kubectl set env deployment/redditharbor-agno -n production READ_ONLY=true
   ```

2. **Promote read replica** (if configured)
   ```bash
   kubectl patch configmap db-config -n production -p '{"data":{"DATABASE_URL":"<replica_url>"}}'
   kubectl rollout restart deployment/redditharbor-agno -n production
   ```

3. **Emergency restore**
   ```bash
   # Get latest backup
   LATEST_BACKUP=$(aws s3 ls s3://reddit-harbor-backups/database/ | tail -1 | awk '{print $3}')

   # Download and restore
   aws s3 cp s3://reddit-harbor-backups/database/$LATEST_BACKUP /tmp/
   psql $DATABASE_URL < /tmp/$LATEST_BACKUP
   ```

### Cost Spike Response

When costs exceed budget:

1. **Immediate Mitigation**
   ```bash
   # Reduce batch sizes
   kubectl set env deployment/redditharbor-agno -n production EMBEDDING_BATCH_SIZE=32
   kubectl set env deployment/redditharbor-agno -n production MAX_CONCURRENT_SUBMISSIONS=20
   ```

2. **Switch to Cheaper Models**
   ```bash
   kubectl set env deployment/redditharbor-agno -n production LLM_MODEL=openai/gpt-3.5-turbo
   ```

3. **Scale Down if Needed**
   ```bash
   kubectl scale deployment redditharbor-agno -n production --replicas=3
   ```

### Security Incident

If security breach is suspected:

1. **Isolate affected components**
   ```bash
   # Cut off external access
   kubectl set env deployment/redditharbor-agno -n production EXTERNAL_API_ENABLED=false
   ```

2. **Preserve evidence**
   ```bash
   # Export logs
   kubectl logs -n production -l app=redditharbor-agno --since=24h > /tmp/security-incident.log

   # Take database snapshot
   pg_dump $DATABASE_URL > /tmp/security-snapshot.sql
   ```

3. **Follow security playbook**
   - Contact security team
   - Document timeline
   - Notify stakeholders

---

## Performance Optimization

### Scaling Strategies

#### Horizontal Scaling
```yaml
# HPA Configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: redditharbor-agno-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: redditharbor-agno
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

#### Vertical Scaling
```yaml
# Resource Optimization
resources:
  requests:
    cpu: 4000m
    memory: 8Gi
  limits:
    cpu: 8000m
    memory: 16Gi
```

### Performance Tuning

#### Application Level
```python
# Optimize batch processing
BATCH_CONFIG = {
    "embedding_batch_size": 96,      # Max for Cohere
    "agent_batch_size": 5,           # Parallel agents
    "max_concurrent_submissions": 50, # Optimal throughput
    "gc_frequency": 100              # Periodic cleanup
}

# Enable caching
CACHE_CONFIG = {
    "enable_embedding_cache": True,
    "cache_ttl": 3600,
    "max_cache_size": 10000
}
```

#### Database Level
```sql
-- Optimize queries
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM opportunities
WHERE reddit_created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;

-- Add composite indexes
CREATE INDEX CONCURRENTLY idx_opportunities_composite_search
ON opportunities (final_score, trust_level, analyzed_at DESC);

-- Partition large tables
CREATE TABLE opportunities_y2024m12 PARTITION OF opportunities
FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');
```

#### Network Level
```yaml
# Connection pooling
database:
  pool_size: 20
  max_overflow: 30
  pool_timeout: 30
  pool_recycle: 3600

# HTTP client optimization
http_client:
  connection_pool_size: 20
  max_connections: 100
  keep_alive_timeout: 30
```

---

## Cost Management

### Cost Monitoring

#### Daily Cost Report
```python
# Generate daily cost report
def generate_cost_report():
    costs = {
        "cohere": get_cohere_costs(),
        "openrouter": get_openrouter_costs(),
        "infrastructure": get_infrastructure_costs()
    }

    total = sum(costs.values())
    budget = get_daily_budget()

    return {
        "total": total,
        "budget": budget,
        "remaining": budget - total,
        "breakdown": costs
    }
```

#### Cost Alerts
```yaml
alerts:
  hourly_budget_warning:
    condition: hourly_cost > 40
    action: reduce_batch_size

  daily_budget_warning:
    condition: daily_cost > 800
    action: switch_to_cheaper_model
```

### Optimization Strategies

#### Batch Optimization
```yaml
# Optimize API call batching
batching:
  cohere:
    optimal_size: 96      # Max supported
    min_size: 32         # Minimum for efficiency
    timeout: 5           # Wait time for batch fill

  embeddings:
    cache_similarity: 0.95  # Cache threshold
    deduplication: true
```

#### Model Selection
```python
# Cost-optimized model selection
def select_model(priority, complexity):
    if priority == "high":
        return "anthropic/claude-3-haiku"
    elif complexity > 0.8:
        return "anthropic/claude-haiku"
    else:
        return "openai/gpt-3.5-turbo"  # Cheaper option
```

#### Caching Strategy
```python
# Smart caching rules
CACHE_RULES = {
    "embeddings": {
        "ttl": 3600,           # 1 hour
        "similarity_threshold": 0.95,
        "max_size": 10000
    },
    "agent_responses": {
        "ttl": 1800,           # 30 minutes
        "deterministic_only": True,
        "max_size": 5000
    }
}
```

---

## Appendices

### Quick Reference Commands

```bash
# Health Check
./scripts/health-monitor.py

# Deploy
./scripts/deploy-canary.sh -p 10

# Switch Traffic
./scripts/traffic-switch.sh split 25

# Rollback
./scripts/rollback-canary.sh --force

# Verify
./scripts/verify-deployment.sh -v

# Monitor Costs
curl -s "http://prometheus:9090/api/v1/query?query=increase(agentops_cost_total[1h])"
```

### Contact Information

| Role | Contact | Hours |
|------|---------|-------|
| On-call Engineer | oncall@company.com | 24/7 |
| Engineering Lead | eng-lead@company.com | 9-5 UTC |
| Infrastructure Team | infra@company.com | 24/7 |
| Security Team | security@company.com | 24/7 |

### Useful Links

- **Main Dashboard**: https://grafana.company.com/d/redditharbor-main
- **Alert Manager**: https://alertmanager.company.com
- **Documentation**: https://docs.company.com/redditharbor
- **Runbook Repository**: https://github.company.com/redditharbor-runbooks

---

**Document Control**

- **Owner**: RedditHarbor Operations Team
- **Review Cycle**: Monthly
- **Last Review**: December 5, 2024
- **Next Review**: January 5, 2025

For questions or updates, please contact ops@company.com or create an issue in the runbook repository.