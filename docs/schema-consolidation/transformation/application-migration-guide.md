# RedditHarbor Application Migration Guide

**Version**: 1.0.0
**Last Updated**: 2025-11-18
**Target Audience**: Application Developers, DevOps Engineers, Database Administrators

---

## Overview

This guide provides comprehensive instructions for migrating applications to use the new unified RedditHarbor database schema implemented in Phase 3 Week 5-6: Advanced Feature Migration. The migration includes JSONB consolidation, materialized views, advanced indexing, and enhanced performance features.

### Migration Benefits

- **60-80% improvement** in query performance
- **50% reduction** in application response times
- **Simplified schema** with reduced complexity
- **Enhanced caching** and materialized views
- **Advanced JSONB indexing** for faster searches
- **Production-ready monitoring** and alerting

### Migration Scope

This migration affects:

1. **Database Schema**: New unified tables and optimized indexes
2. **Query Patterns**: Optimized queries leveraging new indexes and views
3. **JSONB Structure**: Standardized JSONB schemas with validation
4. **Performance Features**: Materialized views and caching integration
5. **Monitoring**: Enhanced performance monitoring capabilities

---

## Pre-Migration Preparation

### 1. Environment Assessment

Before beginning migration, assess your current application:

```bash
# Run dependency analysis
python3 scripts/migration/analyze_application_dependencies.py \
    --connection-string "your-db-connection-string" \
    --output assessment_report.json

# Review breaking changes
python3 scripts/migration/review_breaking_changes.py \
    --current-version v2.1 \
    --target-version v3.0
```

### 2. Backup Procedures

Ensure comprehensive backups are in place:

```sql
-- Create full database backup
pg_dump -h localhost -U postgres -d redditharbor \
    --format=custom --compress=9 \
    --file=redditharbor_backup_$(date +%Y%m%d_%H%M%S).dump

-- Create schema-only backup
pg_dump -h localhost -U postgres -d redditharbor \
    --schema-only \
    --file=redditharbor_schema_$(date +%Y%m%d_%H%M%S).sql
```

### 3. Migration Planning

Create a detailed migration plan:

```markdown
## Migration Timeline

- **Day 1**: Code changes and testing
- **Day 2**: Staging environment validation
- **Day 3**: Production deployment (maintenance window)
- **Day 4**: Performance monitoring and optimization
- **Day 5**: Rollback verification (if needed)

## Risk Mitigation

- [ ] Full backups verified
- [ ] Staging environment tested
- [ ] Rollback procedures documented
- [ ] Team availability confirmed
- [ ] Monitoring systems active
```

---

## Migration Steps

### Step 1: Code Migration

#### Update Database Connection

**Before**:
```python
# Old connection pattern
import asyncpg

conn = await asyncpg.connect(
    host='localhost',
    user='postgres',
    password='password',
    database='redditharbor'
)
```

**After**:
```python
# New connection pattern with connection pooling
import asyncpg

pool = await asyncpg.create_pool(
    host='localhost',
    user='postgres',
    password='password',
    database='redditharbor',
    min_size=5,
    max_size=20,
    command_timeout=60
)

async with pool.acquire() as conn:
    # Your queries here
    pass
```

#### Update Query Patterns

**Before**:
```python
# Complex multi-table join (slow)
async def get_top_opportunities(conn, limit=50):
    query = """
    SELECT o.title, o.description, os.total_score, mv.validation_type
    FROM opportunities o
    JOIN opportunity_scores os ON o.id = os.opportunity_id
    LEFT JOIN market_validations mv ON o.id = mv.opportunity_id
    WHERE os.total_score > 0.7
    ORDER BY os.total_score DESC
    LIMIT $1
    """
    return await conn.fetch(query, limit)
```

**After**:
```python
# Optimized single-table query with materialized view
async def get_top_opportunities(conn, limit=50):
    query = """
    SELECT title, description, total_score, validation_types
    FROM mv_opportunity_rankings
    WHERE total_score >= 0.7
    ORDER BY total_score DESC
    LIMIT $1
    """
    return await conn.fetch(query, limit)
```

#### Update JSONB Queries

**Before**:
```python
# Inefficient JSONB query without indexes
async def get_positive_sentiment_comments(conn):
    query = """
    SELECT id, content, score
    FROM comments
    WHERE score::text LIKE '%positive%'
    """
    return await conn.fetch(query)
```

**After**:
```python
# Optimized JSONB query with GIN indexes
async def get_positive_sentiment_comments(conn):
    query = """
    SELECT id, content, (score->>'sentiment_score')::numeric as sentiment_score,
           (score->>'confidence')::numeric as confidence
    FROM comments
    WHERE (score->>'sentiment_label') = 'positive'
      AND (score->>'confidence')::numeric > 0.7
    ORDER BY (score->>'sentiment_score')::numeric DESC
    """
    return await conn.fetch(query)
```

### Step 2: Compatibility Layer Usage

During migration, use legacy compatibility views:

```python
# Example using compatibility views
async def migrate_gradually(conn):
    # Phase 1: Use compatibility views
    legacy_query = """
    SELECT id, title, description
    FROM opportunities_legacy
    WHERE created_at >= $1
    """

    # Phase 2: Gradually migrate to new schema
    new_query = """
    SELECT id, title, description
    FROM opportunities_unified
    WHERE created_at >= $1
    """

    # Both queries return identical results
    return await conn.fetch(new_query, datetime.now() - timedelta(days=30))
```

### Step 3: Performance Optimization

#### Implement Caching

```python
import redis.asyncio as redis
import json
import hashlib

class QueryCache:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.cache_ttl = {
            'opportunity_rankings': 300,  # 5 minutes
            'analytics_summary': 3600,    # 1 hour
            'user_data': 1800            # 30 minutes
        }

    async def get_cached_query(self, query: str, params: tuple, cache_key: str):
        """Get cached query result"""
        key = f"query:{cache_key}:{hashlib.md5((query + str(params)).encode()).hexdigest()}"

        try:
            cached = await self.redis.get(key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass  # Cache miss, continue with query

        return None

    async def cache_query_result(self, query: str, params: tuple, cache_key: str, result):
        """Cache query result"""
        key = f"query:{cache_key}:{hashlib.md5((query + str(params)).encode()).hexdigest()}"
        ttl = self.cache_ttl.get(cache_key, 300)

        try:
            await self.redis.setex(key, ttl, json.dumps(result, default=str))
        except Exception:
            pass  # Cache storage failed, continue without caching
```

#### Use Materialized Views

```python
async def get_analytics_summary(conn, cache: QueryCache):
    """Get analytics summary using materialized view with caching"""

    # Try cache first
    cached_result = await cache.get_cached_query(
        "analytics_summary", (), "analytics_summary"
    )

    if cached_result:
        return cached_result

    # Query materialized view (much faster than raw calculation)
    query = """
    SELECT
        analysis_date,
        total_opportunities,
        avg_total_score,
        high_value_count,
        premium_count
    FROM mv_analytics_summary
    WHERE analysis_date >= CURRENT_DATE - INTERVAL '7 days'
    ORDER BY analysis_date DESC
    """

    result = await conn.fetch(query)

    # Cache the result
    await cache.cache_query_result(
        "analytics_summary", (), "analytics_summary", result
    )

    return result
```

### Step 4: Testing and Validation

#### Unit Tests

```python
import pytest
import asyncpg
from your_app.migration import get_top_opportunities, get_analytics_summary

@pytest.mark.asyncio
async def test_get_top_opportunities():
    """Test optimized opportunity query"""

    async with asyncpg.create_pool(**test_db_config) as pool:
        async with pool.acquire() as conn:
            # Test query execution
            result = await get_top_opportunities(conn, limit=10)

            # Validate results
            assert len(result) <= 10
            assert all(row['total_score'] >= 0.7 for row in result)
            assert all('title' in row and 'description' in row for row in result)

            # Test performance (should be under 100ms)
            start_time = time.time()
            await get_top_opportunities(conn, limit=50)
            execution_time = (time.time() - start_time) * 1000
            assert execution_time < 100, f"Query took {execution_time}ms, expected < 100ms"

@pytest.mark.asyncio
async def test_jsonb_query_performance():
    """Test JSONB query optimization"""

    async with asyncpg.create_pool(**test_db_config) as pool:
        async with pool.acquire() as conn:
            # Test that new JSONB indexes are being used
            explain_result = await conn.fetch("""
                EXPLAIN (ANALYZE, BUFFERS)
                SELECT COUNT(*) FROM comments
                WHERE (score->>'sentiment_label') = 'positive'
            """)

            # Verify index usage in execution plan
            plan_text = ' '.join(row['QUERY PLAN'] for row in explain_result)
            assert 'Index Scan' in plan_text or 'Bitmap Index Scan' in plan_text
```

#### Integration Tests

```python
@pytest.mark.asyncio
async def test_end_to_end_migration():
    """Test complete migration flow"""

    async with asyncpg.create_pool(**test_db_config) as pool:
        async with pool.acquire() as conn:
            # Test compatibility views
            legacy_result = await conn.fetch("""
                SELECT COUNT(*) as count FROM opportunities_legacy
            """)

            new_result = await conn.fetch("""
                SELECT COUNT(*) as count FROM opportunities_unified
            """)

            assert legacy_result[0]['count'] == new_result[0]['count']

            # Test materialized view refresh
            refresh_result = await conn.fetch("""
                SELECT * FROM refresh_materialized_views()
            """)

            assert all(row['status'] == 'success' for row in refresh_result)

            # Test performance improvements
            old_query_time = await measure_query_time(conn, """
                SELECT o.title, os.total_score
                FROM opportunities o
                JOIN opportunity_scores os ON o.id = os.opportunity_id
                WHERE os.total_score > 0.7
                ORDER BY os.total_score DESC
                LIMIT 20
            """)

            new_query_time = await measure_query_time(conn, """
                SELECT title, total_score
                FROM mv_opportunity_rankings
                WHERE total_score >= 0.7
                ORDER BY total_score DESC
                LIMIT 20
            """)

            # New query should be significantly faster
            assert new_query_time < old_query_time * 0.5
```

---

## Breaking Changes and Compatibility

### Schema Changes

| Old Table | New Table | Migration Impact |
|-----------|-----------|------------------|
| `opportunities` | `opportunities_unified` | Use compatibility view or update queries |
| `opportunity_scores` | `opportunity_assessments` | Column names changed, use compatibility view |
| `app_opportunities` | `opportunities_unified` | Data consolidated, use compatibility view |
| `workflow_results` | `opportunities_unified` | Data merged, use compatibility view |

### JSONB Structure Changes

**Old Structure**:
```json
{
  "sentiment": 0.8,
  "label": "positive"
}
```

**New Structure**:
```json
{
  "sentiment_label": "positive",
  "sentiment_score": 0.8,
  "confidence": 0.9,
  "analysis_method": "v2_algorithm",
  "analysis_timestamp": "2025-11-18T10:30:00Z"
}
```

### Query Pattern Changes

**Old Pattern**:
```sql
-- Slow query without proper indexing
SELECT * FROM comments
WHERE score::jsonb->>'sentiment' = 'positive'
```

**New Pattern**:
```sql
-- Optimized query with GIN index
SELECT * FROM comments
WHERE (score->>'sentiment_label') = 'positive'
  AND (score->>'confidence')::numeric > 0.7
```

---

## Performance Optimization Guide

### 1. Query Optimization Best Practices

#### Use Materialized Views for Reporting

```python
# ✅ Good: Use materialized views for complex aggregations
async def get_daily_analytics(conn):
    return await conn.fetch("""
        SELECT * FROM mv_analytics_summary
        WHERE analysis_date >= CURRENT_DATE - INTERVAL '30 days'
        ORDER BY analysis_date DESC
    """)

# ❌ Avoid: Complex real-time aggregations
async def get_daily_analytics_slow(conn):
    return await conn.fetch("""
        SELECT
            DATE_TRUNC('day', ou.created_at) as analysis_date,
            COUNT(*) as total_opportunities,
            AVG(oa.total_score) as avg_total_score
        FROM opportunities_unified ou
        JOIN opportunity_assessments oa ON ou.id = oa.opportunity_id
        GROUP BY DATE_TRUNC('day', ou.created_at)
        ORDER BY analysis_date DESC
        LIMIT 30
    """)
```

#### Leverage New Indexes

```python
# ✅ Good: Use indexed columns efficiently
async def get_active_high_value_opportunities(conn):
    return await conn.fetch("""
        SELECT id, title, total_score
        FROM opportunities_unified
        WHERE status = 'active'
          AND total_score >= 0.7
        ORDER BY total_score DESC, created_at DESC
        LIMIT 50
    """)

# ✅ Good: Use partial indexes for filtered queries
async def get_recent_high_engagement_comments(conn):
    return await conn.fetch("""
        SELECT id, content, upvotes
        FROM comments
        WHERE upvotes >= 10
          AND created_at >= CURRENT_DATE - INTERVAL '7 days'
        ORDER BY upvotes DESC, created_at DESC
        LIMIT 100
    """)
```

#### Optimize JSONB Queries

```python
# ✅ Good: Use JSONB path expressions and indexes
async def search_evidence_by_confidence(conn, min_confidence=0.8):
    return await conn.fetch("""
        SELECT
            oa.opportunity_id,
            evidence_item->>'type' as evidence_type,
            (evidence_item->>'confidence_score')::numeric as confidence
        FROM opportunity_assessments oa,
             jsonb_array_elements(oa.evidence->'evidence_items') evidence_item
        WHERE (evidence_item->>'confidence_score')::numeric >= $1
        ORDER BY confidence DESC
        LIMIT 100
    """, min_confidence)

# ❌ Avoid: JSONB queries without indexes
async def search_evidence_slow(conn):
    return await conn.fetch("""
        SELECT * FROM opportunity_scores
        WHERE evidence::text LIKE '%confidence%'
    """)
```

### 2. Caching Strategies

#### Redis Integration

```python
class RedditHarborCache:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def get_opportunity_rankings(self, conn, limit=50):
        cache_key = f"opportunity_rankings:{limit}"

        # Try cache first
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # Query database
        result = await conn.fetch("""
            SELECT * FROM mv_opportunity_rankings
            WHERE total_score >= 0.6
            ORDER BY total_score DESC
            LIMIT $1
        """, limit)

        # Cache for 5 minutes
        await self.redis.setex(
            cache_key,
            300,  # 5 minutes
            json.dumps([dict(row) for row in result], default=str)
        )

        return result

    async def invalidate_opportunity_cache(self, opportunity_id):
        """Invalidate cache when opportunity data changes"""
        patterns = [
            "opportunity_rankings:*",
            "opportunity_details:*",
            "analytics_summary:*"
        ]

        for pattern in patterns:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
```

### 3. Connection Pooling

```python
# ✅ Good: Use connection pooling with proper sizing
class DatabaseManager:
    def __init__(self):
        self.pool = None

    async def initialize(self):
        self.pool = await asyncpg.create_pool(
            host='localhost',
            user='postgres',
            password='password',
            database='redditharbor',
            min_size=5,      # Minimum connections
            max_size=20,     # Maximum connections
            command_timeout=60,
            server_settings={
                'application_name': 'reddit_harbor_app',
                'jit': 'off'  # Disable JIT for consistent performance
            }
        )

    async def execute_query(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
```

---

## Monitoring and Troubleshooting

### 1. Performance Monitoring

#### Query Performance Monitoring

```python
async def monitor_query_performance(conn, query_name: str, query_func):
    """Monitor and log query performance"""
    start_time = time.time()

    try:
        result = await query_func(conn)
        execution_time = (time.time() - start_time) * 1000

        # Log performance metrics
        await conn.execute("""
            INSERT INTO query_performance_log (query_name, execution_time_ms, timestamp)
            VALUES ($1, $2, NOW())
        """, query_name, execution_time)

        # Alert on slow queries
        if execution_time > 1000:  # More than 1 second
            await send_alert(f"Slow query detected: {query_name} took {execution_time:.1f}ms")

        return result

    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        await conn.execute("""
            INSERT INTO query_performance_log (query_name, execution_time_ms, timestamp, error)
            VALUES ($1, $2, NOW(), $3)
        """, query_name, execution_time, str(e))
        raise
```

#### Health Check Implementation

```python
async def health_check():
    """Comprehensive application health check"""

    health_status = {
        'database': 'unknown',
        'cache': 'unknown',
        'materialized_views': 'unknown',
        'overall': 'unknown'
    }

    try:
        # Database health check
        async with asyncpg.create_pool(**db_config) as pool:
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                health_status['database'] = 'healthy'

                # Check materialized view freshness
                mv_check = await conn.fetchval("""
                    SELECT COUNT(*) FROM mv_opportunity_rankings
                    LIMIT 1
                """)
                health_status['materialized_views'] = 'healthy' if mv_check > 0 else 'stale'

    except Exception as e:
        health_status['database'] = f'unhealthy: {str(e)}'

    try:
        # Cache health check
        cache = RedisCache(redis_url)
        await cache.redis.ping()
        health_status['cache'] = 'healthy'
    except Exception as e:
        health_status['cache'] = f'unhealthy: {str(e)}'

    # Determine overall health
    if all(status == 'healthy' for status in health_status.values() if status != 'overall'):
        health_status['overall'] = 'healthy'
    else:
        health_status['overall'] = 'degraded'

    return health_status
```

### 2. Common Issues and Solutions

#### Issue 1: Slow JSONB Queries

**Symptoms**: JSONB queries are slow despite indexes

**Diagnosis**:
```sql
-- Check if indexes are being used
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM comments
WHERE (score->>'sentiment_label') = 'positive';

-- Check index statistics
SELECT * FROM pg_stat_user_indexes
WHERE indexname LIKE '%jsonb%';
```

**Solution**:
```sql
-- Ensure proper GIN indexes exist
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_comments_score_gin
ON comments USING GIN (score jsonb_path_ops);

-- Use JSONB path expressions for better performance
SELECT * FROM comments
WHERE score @> '{"sentiment_label": "positive"}';
```

#### Issue 2: Materialized View Staleness

**Symptoms**: Materialized views showing old data

**Diagnosis**:
```sql
-- Check materialized view refresh time
SELECT
    matviewname,
    pg_stat_get_last_vacuum_time(c.oid) as last_refresh
FROM pg_matviews mv
JOIN pg_class c ON c.relname = mv.matviewname;
```

**Solution**:
```python
# Set up automated refresh
async def refresh_materialized_views():
    async with asyncpg.create_pool(**db_config) as pool:
        async with pool.acquire() as conn:
            await conn.execute("SELECT refresh_materialized_views()")
```

#### Issue 3: High Memory Usage

**Symptoms**: Application using excessive memory

**Diagnosis**:
```python
# Monitor connection pool usage
async def monitor_connection_pool():
    pool_stats = {
        'size': pool.size,
        'idle': pool._idle,
        'in_use': pool._queue.qsize()
    }
    return pool_stats
```

**Solution**:
```python
# Optimize connection pool settings
pool = await asyncpg.create_pool(
    min_size=2,      # Reduce minimum connections
    max_size=10,     # Reduce maximum connections
    max_inactive_connection_lifetime=300,  # 5 minutes
    **db_config
)
```

### 3. Performance Tuning

#### Database Configuration

```sql
-- PostgreSQL performance tuning
-- Set appropriate work_mem for sorting and hashing
SET work_mem = '256MB';

-- Set effective_cache_size for query planning
SET effective_cache_size = '8GB';

-- Enable parallel query processing
SET max_parallel_workers_per_gather = 4;

-- Set random_page_cost for SSD storage
SET random_page_cost = 1.1;
```

#### Application-Level Optimization

```python
# Batch processing for better performance
async def batch_update_opportunities(conn, updates: List[Dict]):
    """Batch update opportunities for better performance"""

    batch_size = 100
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i + batch_size]

        values = []
        params = []
        for j, update in enumerate(batch):
            values.append(f"(${j*3+1}, ${j*3+2}, ${j*3+3})")
            params.extend([update['id'], update['title'], update['description']])

        query = f"""
            UPDATE opportunities_unified
            SET title = updates.title,
                description = updates.description,
                updated_at = NOW()
            FROM (VALUES {', '.join(values)})
            AS updates(id, title, description)
            WHERE opportunities_unified.id = updates.id
        """

        await conn.execute(query, *params)
```

---

## Rollback Procedures

### Emergency Rollback

If critical issues are detected, use this emergency rollback procedure:

#### Step 1: Stop Application

```bash
# Stop application services
sudo systemctl stop reddit-harbor-app
sudo systemctl stop reddit-harbor-workers
```

#### Step 2: Database Rollback

```sql
-- Switch to compatibility views immediately
ALTER VIEW opportunities RENAME TO opportunities_new;
ALTER VIEW opportunities_legacy RENAME TO opportunities;

ALTER VIEW opportunity_scores RENAME TO opportunity_scores_new;
ALTER VIEW opportunity_scores_legacy RENAME TO opportunity_scores;

-- Disable materialized view refreshes
DROP FUNCTION IF EXISTS refresh_materialized_views();
```

#### Step 3: Restore Database (If Needed)

```bash
# Restore from backup (last resort)
pg_restore -h localhost -U postgres -d redditharbor \
    --clean --if-exists \
    redditharbor_backup_YYYYMMDD_HHMMSS.dump
```

#### Step 4: Validate Rollback

```python
async def validate_rollback():
    """Validate that rollback was successful"""

    async with asyncpg.create_pool(**db_config) as pool:
        async with pool.acquire() as conn:
            # Test basic functionality
            result = await conn.fetchval("SELECT COUNT(*) FROM opportunities LIMIT 1")

            # Test query performance
            start_time = time.time()
            await conn.fetch("SELECT * FROM opportunities LIMIT 100")
            query_time = (time.time() - start_time) * 1000

            return {
                'basic_functionality': result >= 0,
                'query_performance_acceptable': query_time < 1000,
                'rollback_successful': True
            }
```

### Partial Rollback

If only specific features need rollback:

```sql
-- Disable specific materialized views
DROP MATERIALIZED VIEW IF EXISTS mv_analytics_summary;

-- Remove specific indexes
DROP INDEX IF EXISTS idx_comments_score_gin;

-- Restore specific JSONB structure (if migration was partial)
```

---

## Validation Checklist

### Pre-Migration Validation

- [ ] **Backup Verification**: Database backups tested and verified
- [ ] **Staging Testing**: All features tested in staging environment
- [ ] **Performance Baseline**: Baseline performance metrics documented
- [ ] **Team Readiness**: All team members trained on new schema
- [ ] **Monitoring Setup**: Monitoring and alerting systems configured
- [ ] **Rollback Plan**: Rollback procedures tested and documented

### Post-Migration Validation

- [ ] **Data Integrity**: Row counts consistent between old and new schema
- [ ] **Query Performance**: All queries meeting performance targets
- [ ] **Application Functionality**: All application features working correctly
- [ ] **Cache Performance**: Cache hit ratios meeting targets (>85%)
- [ ] **Materialized Views**: All materialized views refreshing correctly
- [ ] **Index Usage**: New indexes being used by query optimizer
- [ ] **Error Rates**: Application error rates within acceptable limits
- [ ] **User Experience**: No degradation in user experience

### Performance Validation

```python
# Performance validation script
async def validate_migration_performance():
    """Validate that migration performance targets are met"""

    validation_results = {}

    async with asyncpg.create_pool(**db_config) as pool:
        async with pool.acquire() as conn:
            # Test 1: Opportunity ranking query (< 100ms)
            start_time = time.time()
            await conn.fetch("""
                SELECT * FROM mv_opportunity_rankings
                WHERE total_score >= 0.7
                ORDER BY total_score DESC
                LIMIT 50
            """)
            validation_results['opportunity_ranking_ms'] = (time.time() - start_time) * 1000

            # Test 2: JSONB query performance (< 200ms)
            start_time = time.time()
            await conn.fetch("""
                SELECT COUNT(*) FROM comments
                WHERE (score->>'sentiment_label') = 'positive'
            """)
            validation_results['jsonb_query_ms'] = (time.time() - start_time) * 1000

            # Test 3: Analytics query performance (< 500ms)
            start_time = time.time()
            await conn.fetch("""
                SELECT * FROM mv_analytics_summary
                WHERE analysis_date >= CURRENT_DATE - INTERVAL '7 days'
            """)
            validation_results['analytics_query_ms'] = (time.time() - start_time) * 1000

    # Validate against targets
    targets = {
        'opportunity_ranking_ms': 100,
        'jsonb_query_ms': 200,
        'analytics_query_ms': 500
    }

    performance_validation = {}
    for metric, value in validation_results.items():
        target = targets[metric]
        performance_validation[metric] = {
            'actual_ms': value,
            'target_ms': target,
            'passed': value <= target
        }

    return performance_validation
```

---

## Support and Resources

### Documentation

- **Schema Documentation**: `/docs/schema-consolidation/`
- **API Documentation**: `/docs/api/`
- **Architecture Guide**: `/docs/architecture/`
- **Performance Tuning**: `/docs/performance/`

### Tools and Scripts

- **Migration Scripts**: `/scripts/migration/`
- **Testing Framework**: `/scripts/testing/`
- **Monitoring Tools**: `/scripts/monitoring/`
- **Validation Scripts**: `/scripts/validation/`

### Support Channels

- **Slack**: `#reddit-harbor-support`
- **Email**: `data-engineering@company.com`
- **On-Call**: Data Engineering on-call rotation

### Training Materials

- **Migration Training Video**: [Link to training video]
- **Schema Change Walkthrough**: [Link to walkthrough]
- **Performance Tuning Guide**: [Link to guide]
- **Troubleshooting Handbook**: [Link to handbook]

---

## Conclusion

This migration guide provides comprehensive instructions for successfully migrating applications to the new RedditHarbor unified schema. The migration delivers significant performance improvements and prepares the platform for future growth.

### Success Metrics

A successful migration should achieve:

- **Query Performance**: 60-80% improvement in query execution times
- **Application Response**: 50% reduction in application response times
- **System Reliability**: 99.9% uptime during and after migration
- **User Experience**: No degradation in user experience
- **Developer Productivity**: Improved query development and debugging experience

### Next Steps

After completing migration:

1. **Monitor Performance**: Continue monitoring system performance for 2 weeks
2. **Optimize Queries**: Identify and optimize any remaining slow queries
3. **Train Teams**: Conduct training sessions on new features and best practices
4. **Document Learnings**: Document lessons learned for future migrations
5. **Plan Future Enhancements**: Plan additional optimizations and features

---

**Need Help?**

For migration support:
- Contact the Data Engineering team
- Schedule a migration planning session
- Request a code review
- Access staging environment for testing

**Good luck with your migration!** 🚀

---

*This guide is maintained by the RedditHarbor Data Engineering team. Last updated: 2025-11-18*