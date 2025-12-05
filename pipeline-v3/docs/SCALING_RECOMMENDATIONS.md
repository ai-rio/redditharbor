# RedditHarbor Agno System: Production Scaling Recommendations

## Executive Summary

This document provides detailed scaling recommendations for the RedditHarbor Agno multi-agent system to achieve **1000 submissions/minute throughput** with **99.9% uptime**. These recommendations address the critical gaps identified in the production readiness assessment.

## 1. Database Scaling Architecture

### 1.1 Connection Pooling Implementation

```python
# config/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
import logging

logger = logging.getLogger(__name__)

def create_production_db_engine(database_url: str):
    """
    Create production-ready database engine with connection pooling
    """
    engine = create_engine(
        database_url,
        # Connection pool configuration
        poolclass=QueuePool,
        pool_size=20,  # Base connections
        max_overflow=30,  # Additional connections under load
        pool_timeout=30,  # Wait time for connection
        pool_recycle=3600,  # Recycle connections every hour
        pool_pre_ping=True,  # Validate connections

        # Query optimization
        pool_reset_on_return='commit',
        echo=False,  # Disable SQL logging in production

        # Performance tuning
        connect_args={
            "application_name": "redditharbor-agno",
            "connect_timeout": 10,
            "command_timeout": 30,
            "options": "-c statement_timeout=30000"  # 30 second query timeout
        }
    )

    logger.info(f"Created DB engine with pool_size=20, max_overflow=30")
    return engine

# Database health check
async def check_db_health(engine):
    """Check database connectivity and performance"""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            return result.fetchone()[0] == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
```

### 1.2 Database Index Optimization

```sql
-- Production index optimizations
-- Run these during maintenance window

-- 1. Vector similarity index (pgvector)
CREATE INDEX CONCURRENTLY idx_opportunities_embedding_cosine
ON opportunities
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 2. Composite index for scoring queries
CREATE INDEX CONCURRENTLY idx_opportunities_score_composite
ON opportunities (final_score DESC, trust_level, analyzed_at DESC)
WHERE final_score > 50;

-- 3. Subreddit time-based index
CREATE INDEX CONCURRENTLY idx_opportunities_subreddit_time
ON opportunities (subreddit, reddit_created_at DESC, final_score DESC);

-- 4. Deduplication index
CREATE INDEX CONCURRENTLY idx_opportunities_content_hash
ON opportunities (md5(reddit_title || reddit_content))
WHERE is_duplicate = false;

-- 5. Partitioning for time-based data
CREATE TABLE opportunities_partitioned (
    LIKE opportunities INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- Monthly partitions
CREATE TABLE opportunities_2024_01 PARTITION OF opportunities_partitioned
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### 1.3 Read Replica Configuration

```python
# config/database_replicas.py
class DatabaseRouter:
    """
    Route read queries to replicas, write queries to primary
    """

    def __init__(self, primary_engine, replica_engines):
        self.primary = primary_engine
        self.replicas = replica_engines
        self.replica_index = 0

    def get_read_connection(self):
        """Get connection from replica pool with failover"""
        for i in range(len(self.replicas)):
            try:
                replica = self.replicas[self.replica_index]
                if check_db_health(replica):
                    return replica.connect()
            except Exception:
                logger.warning(f"Replica {self.replica_index} failed, trying next")
                self.replica_index = (self.replica_index + 1) % len(self.replicas)

        # Fallback to primary if all replicas fail
        logger.warning("All replicas failed, using primary for reads")
        return self.primary.connect()

    def get_write_connection(self):
        """Always use primary for writes"""
        return self.primary.connect()

# Usage in application
router = DatabaseRouter(primary_engine, replica_engines)

# For read operations
with router.get_read_connection() as conn:
    opportunities = conn.execute("SELECT * FROM opportunities LIMIT 100")

# For write operations
with router.get_write_connection() as conn:
    conn.execute("INSERT INTO opportunities ...")
```

## 2. API Rate Limiting and Resilience

### 2.1 Distributed Rate Limiter

```python
# infrastructure/rate_limiter.py
import redis
import time
from typing import Optional
import asyncio
from dataclasses import dataclass

@dataclass
class RateLimitConfig:
    requests_per_window: int
    window_seconds: int
    burst_capacity: int = None

class DistributedRateLimiter:
    """
    Redis-based distributed rate limiter for horizontal scaling
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.configs = {
            "openrouter": RateLimitConfig(60, 60, 10),  # 60 RPM, burst 10
            "cohere": RateLimitConfig(1000, 60, 100),  # 1000 RPM, burst 100
            "analysis_total": RateLimitConfig(1000, 60, 50)  # Total system limit
        }

    async def acquire(self, key: str, config_name: str) -> bool:
        """
        Acquire rate limit slot using sliding window algorithm

        Returns:
            bool: True if request allowed, False if rate limited
        """
        config = self.configs.get(config_name)
        if not config:
            raise ValueError(f"Unknown rate limit config: {config_name}")

        now = time.time()
        window_start = now - config.window_seconds

        # Use Redis pipeline for atomic operations
        pipe = self.redis.pipeline()

        # Remove expired entries
        pipe.zremrangebyscore(key, 0, window_start)

        # Count current requests
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(now): now})

        # Set expiry
        pipe.expire(key, config.window_seconds)

        results = pipe.execute()
        current_count = results[1]

        # Check burst capacity first, then sustained rate
        if config.burst_capacity and current_count < config.burst_capacity:
            return True
        elif current_count < config.requests_per_window:
            return True

        # Remove the request we added if over limit
        self.redis.zrem(key, str(now))
        return False

    async def wait_for_slot(self, key: str, config_name: str, max_wait: float = 60.0) -> bool:
        """
        Wait for available rate limit slot

        Returns:
            bool: True if slot acquired, False if timeout
        """
        start_time = time.time()

        while time.time() - start_time < max_wait:
            if await self.acquire(key, config_name):
                return True
            await asyncio.sleep(0.1)  # Poll every 100ms

        return False

# Usage in API clients
class ResilientAPIClient:
    def __init__(self, rate_limiter: DistributedRateLimiter):
        self.rate_limiter = rate_limiter
        self.circuit_breaker = CircuitBreaker()

    async def call_api(self, endpoint: str, data: dict):
        # Check circuit breaker first
        if self.circuit_breaker.is_open():
            raise CircuitBreakerOpenError("Service temporarily unavailable")

        # Acquire rate limit
        api_key = f"api:{endpoint}"
        if not await self.rate_limiter.acquire(api_key, "openrouter"):
            raise RateLimitError("Rate limit exceeded")

        try:
            # Make API call
            response = await self._make_request(endpoint, data)
            self.circuit_breaker.record_success()
            return response
        except Exception as e:
            self.circuit_breaker.record_failure()
            raise
```

### 2.2 Circuit Breaker Implementation

```python
# infrastructure/circuit_breaker.py
import time
import logging
from enum import Enum
from typing import Callable, Any
import asyncio

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """
    Circuit breaker pattern implementation for fault tolerance
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        """
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise CircuitBreakerOpenError("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except self.expected_exception as e:
            await self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return time.time() - self.last_failure_time >= self.timeout

    async def _on_success(self):
        """Handle successful operation"""
        async with self._lock:
            self.failure_count = 0
            self.state = CircuitState.CLOSED

    async def _on_failure(self):
        """Handle failed operation"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker opened after {self.failure_count} failures"
                )

class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass

class RateLimitError(Exception):
    """Raised when rate limit is exceeded"""
    pass

# Decorator for easy usage
def with_circuit_breaker(
    failure_threshold: int = 5,
    timeout: int = 60,
    expected_exception: type = Exception
):
    def decorator(func):
        breaker = CircuitBreaker(failure_threshold, timeout, expected_exception)

        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)

        return wrapper
    return decorator
```

### 2.3 API Client with Retry Logic

```python
# infrastructure/resilient_client.py
import asyncio
import random
from typing import TypeVar, Callable, Any
import backoff

T = TypeVar('T')

class ResilientAPIClient:
    """
    API client with exponential backoff retry and jitter
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

        self.session = None
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=60
        )

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3,
        jitter=backoff.full_jitter,
        max_time=60
    )
    async def request(
        self,
        method: str,
        endpoint: str,
        json_data: dict = None,
        params: dict = None
    ) -> dict:
        """
        Make HTTP request with retry and circuit breaker
        """
        async with self.circuit_breaker.call(
            self._make_request,
            method,
            endpoint,
            json_data,
            params
        ) as response:
            return await response.json()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: dict = None,
        params: dict = None
    ):
        """Internal request method"""
        async with self.session.request(
            method,
            endpoint,
            json=json_data,
            params=params
        ) as response:
            response.raise_for_status()
            return response
```

## 3. Horizontal Scaling Architecture

### 3.1 Kubernetes Deployment Configuration

```yaml
# k8s/agno-analyzer-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agno-analyzer
  labels:
    app: agno-analyzer
spec:
  replicas: 5  # Start with 5, can auto-scale
  selector:
    matchLabels:
      app: agno-analyzer
  template:
    metadata:
      labels:
        app: agno-analyzer
    spec:
      containers:
      - name: agno-analyzer
        image: redditharbor/agno-analyzer:latest
        ports:
        - containerPort: 8000

        # Resource limits for cost control
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"

        # Environment variables
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: redditharbor-secrets
              key: database-url
        - name: REDIS_URL
          value: "redis://redis-cluster:6379"
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: redditharbor-secrets
              key: openrouter-api-key
        - name: WORKER_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.uid

        # Liveness and readiness probes
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

        # Graceful termination
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15"]

      # Termination grace period
      terminationGracePeriodSeconds: 30

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agno-analyzer-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agno-analyzer
  minReplicas: 3
  maxReplicas: 20
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
  - type: Pods
    pods:
      metric:
        name: submissions_per_minute
      target:
        type: AverageValue
        averageValue: "200"  # Target 200 submissions/min per pod
```

### 3.2 Service Mesh with Istio

```yaml
# k8s/istio-gateway.yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: redditharbor-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - api.redditharbor.com
  - port:
      number: 443
      name: https
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: redditharbor-cert
    hosts:
    - api.redditharbor.com

---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: redditharbor-vs
spec:
  hosts:
  - api.redditharbor.com
  gateways:
  - redditharbor-gateway
  http:
  - match:
    - uri:
        prefix: "/v1/analyze"
    route:
    - destination:
        host: agno-analyzer
        port:
          number: 8000
      weight: 100
    # Retry configuration
    retries:
      attempts: 3
      perTryTimeout: 30s
      retryOn: 5xx,gateway-error,connect-failure,refused-stream
    # Timeouts
    timeout: 120s
    # Fault injection for testing
    fault:
      delay:
        percentage:
          value: 0.1
        fixedDelay: 5s

---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: agno-analyzer-dr
spec:
  host: agno-analyzer
  trafficPolicy:
    # Connection pool settings
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 50
        maxRequestsPerConnection: 10
    # Load balancing
    loadBalancer:
      simple: LEAST_CONN
    # Outlier detection
    outlierDetection:
      consecutiveErrors: 3
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
    # TLS
    tls:
      mode: ISTIO_MUTUAL
```

### 3.3 Message Queue for High Throughput

```python
# infrastructure/message_queue.py
import asyncio
import json
import logging
from typing import Callable, Dict, Any
import aio_pika
from aio_pika import ExchangeType, Message

logger = logging.getLogger(__name__)

class MessageQueue:
    """
    RabbitMQ-based message queue for high-throughput processing
    """

    def __init__(self, url: str):
        self.url = url
        self.connection = None
        self.channel = None
        self.exchanges = {}
        self.queues = {}

    async def connect(self):
        """Establish connection to RabbitMQ"""
        self.connection = await aio_pika.connect_robust(
            self.url,
            heartbeat=60,
            client_properties={
                "connection_name": "redditharbor-agno"
            }
        )
        self.channel = await self.connection.channel()

        # QoS settings
        await self.channel.set_qos(prefetch_count=10)

        logger.info("Connected to message queue")

    async def declare_exchange(self, name: str, exchange_type: ExchangeType = ExchangeType.DIRECT):
        """Declare exchange"""
        exchange = await self.channel.declare_exchange(
            name,
            type=exchange_type,
            durable=True
        )
        self.exchanges[name] = exchange
        return exchange

    async def declare_queue(
        self,
        name: str,
        exchange_name: str,
        routing_key: str,
        durable: bool = True,
        arguments: dict = None
    ):
        """Declare queue and bind to exchange"""
        queue = await self.channel.declare_queue(
            name,
            durable=durable,
            arguments=arguments or {
                "x-max-length": 100000,  # Limit queue size
                "x-message-ttl": 3600000  # 1 hour TTL
            }
        )

        if exchange_name in self.exchanges:
            await queue.bind(self.exchanges[exchange_name], routing_key)

        self.queues[name] = queue
        return queue

    async def publish(self, exchange_name: str, routing_key: str, message: Dict[str, Any]):
        """Publish message to exchange"""
        exchange = self.exchanges.get(exchange_name)
        if not exchange:
            raise ValueError(f"Exchange {exchange_name} not declared")

        await exchange.publish(
            Message(
                json.dumps(message).encode(),
                content_type="application/json",
                delivery_mode=2,  # Persistent
                priority=1
            ),
            routing_key
        )

    async def consume(
        self,
        queue_name: str,
        callback: Callable[[Dict[str, Any]], None],
        prefetch_count: int = 10
    ):
        """Consume messages from queue"""
        queue = self.queues.get(queue_name)
        if not queue:
            raise ValueError(f"Queue {queue_name} not declared")

        await self.channel.set_qos(prefetch_count=prefetch_count)

        async def wrapper(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    data = json.loads(message.body.decode())
                    await callback(data)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Message will be re-queued if not acknowledged

        await queue.consume(wrapper)
        logger.info(f"Started consuming from queue: {queue_name}")

# Worker implementation
class AnalysisWorker:
    """
    Worker for processing analysis requests from queue
    """

    def __init__(self, worker_id: str, analyzer: AgnoOpportunityAnalyzer):
        self.worker_id = worker_id
        self.analyzer = analyzer
        self.processed_count = 0
        self.error_count = 0

    async def process_message(self, message: Dict[str, Any]):
        """Process single analysis request"""
        try:
            # Extract submission data
            submission_data = message.get("submission")
            if not submission_data:
                raise ValueError("No submission data in message")

            # Create RedditSubmission object
            submission = RedditSubmission(**submission_data)

            # Run analysis
            result = await self.analyzer.analyze_submission(submission)

            # Store result in database
            await self.store_result(result)

            self.processed_count += 1

            # Log progress
            if self.processed_count % 100 == 0:
                logger.info(
                    f"Worker {self.worker_id}: Processed {self.processed_count} submissions"
                )

        except Exception as e:
            self.error_count += 1
            logger.error(f"Worker {self.worker_id} error: {e}")
            raise

    async def store_result(self, result: AnalysisResult):
        """Store analysis result in database"""
        # Implementation depends on your ORM/database layer
        pass

# Main worker application
async def run_worker():
    """Main worker loop"""
    # Initialize message queue
    mq = MessageQueue("amqp://guest:guest@localhost:5672/")
    await mq.connect()

    # Declare exchanges and queues
    await mq.declare_exchange("analysis", ExchangeType.DIRECT)
    await mq.declare_queue(
        "analysis.pending",
        "analysis",
        "analyze",
        arguments={
            "x-dead-letter-exchange": "analysis.dlx",
            "x-dead-letter-routing-key": "analyze.failed"
        }
    )

    # Create analyzer
    analyzer = await AgnoOpportunityAnalyzer.create()

    # Create and run worker
    worker = AnalysisWorker(f"worker-{uuid.uuid4()}", analyzer)

    # Start consuming
    await mq.consume("analysis.pending", worker.process_message)

    logger.info("Worker started, waiting for messages...")

    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down worker...")
```

## 4. Caching Strategy

### 4.1 Multi-Level Caching Implementation

```python
# infrastructure/cache.py
import redis
import json
import pickle
import hashlib
from typing import Any, Optional, Union, Callable
from functools import wraps
import asyncio
from datetime import timedelta

class CacheManager:
    """
    Multi-level caching with Redis backend
    """

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=False)
        self.local_cache = {}  # Simple in-memory cache
        self.local_cache_ttl = {}
        self.local_cache_max = 1000

    async def get(self, key: str, level: str = "redis") -> Optional[Any]:
        """Get value from cache"""
        if level == "local":
            return self._get_local(key)
        elif level == "redis":
            return await self._get_redis(key)
        elif level == "both":
            # Try local first, then redis
            value = self._get_local(key)
            if value is not None:
                return value
            value = await self._get_redis(key)
            if value is not None:
                self._set_local(key, value, ttl=300)  # Cache in local for 5 min
            return value

    def _get_local(self, key: str) -> Optional[Any]:
        """Get from local memory cache"""
        if key in self.local_cache:
            if key in self.local_cache_ttl:
                if time.time() > self.local_cache_ttl[key]:
                    del self.local_cache[key]
                    del self.local_cache_ttl[key]
                    return None
            return self.local_cache[key]
        return None

    async def _get_redis(self, key: str) -> Optional[Any]:
        """Get from Redis cache"""
        try:
            data = await self.redis.get(key)
            if data:
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Union[int, timedelta] = 3600,
        level: str = "both"
    ):
        """Set value in cache"""
        if level in ["local", "both"]:
            self._set_local(key, value, ttl)
        if level in ["redis", "both"]:
            await self._set_redis(key, value, ttl)

    def _set_local(self, key: str, value: Any, ttl: Union[int, timedelta]):
        """Set in local memory cache"""
        # Simple LRU eviction
        if len(self.local_cache) >= self.local_cache_max:
            # Remove oldest entry
            oldest_key = min(self.local_cache_ttl.keys(),
                           key=lambda k: self.local_cache_ttl[k])
            del self.local_cache[oldest_key]
            del self.local_cache_ttl[oldest_key]

        self.local_cache[key] = value
        if isinstance(ttl, timedelta):
            ttl = ttl.total_seconds()
        self.local_cache_ttl[key] = time.time() + ttl

    async def _set_redis(self, key: str, value: Any, ttl: Union[int, timedelta]):
        """Set in Redis cache"""
        try:
            data = pickle.dumps(value)
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            await self.redis.setex(key, ttl, data)
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    async def delete(self, key: str, level: str = "both"):
        """Delete key from cache"""
        if level in ["local", "both"]:
            self.local_cache.pop(key, None)
            self.local_cache_ttl.pop(key, None)
        if level in ["redis", "both"]:
            await self.redis.delete(key)

    async def clear_pattern(self, pattern: str, level: str = "redis"):
        """Clear keys matching pattern"""
        if level == "redis":
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)

# Cache decorators
def cache_result(
    ttl: int = 3600,
    key_prefix: str = "",
    level: str = "both",
    serialize_key: bool = True
):
    """
    Decorator to cache function results
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}"

            if serialize_key:
                # Create stable hash of arguments
                key_data = {
                    "args": args,
                    "kwargs": sorted(kwargs.items())
                }
                key_hash = hashlib.md5(
                    json.dumps(key_data, sort_keys=True, default=str).encode()
                ).hexdigest()
                cache_key += f":{key_hash}"
            else:
                cache_key += f":{str(args)}:{str(kwargs)}"

            # Try cache first
            result = await cache_manager.get(cache_key, level=level)
            if result is not None:
                return result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await cache_manager.set(cache_key, result, ttl=ttl, level=level)

            return result

        return wrapper
    return decorator

# Usage examples
@cache_result(ttl=1800, key_prefix="analysis")  # 30 minutes cache
async def get_opportunity_analysis(submission_id: str):
    """Cache analysis results"""
    # Implementation
    pass

@cache_result(ttl=3600, key_prefix="embedding")
async def get_text_embedding(text: str):
    """Cache text embeddings"""
    # Implementation
    pass

@cache_result(ttl=7200, key_prefix="market_research", level="redis")
async def get_market_research(query: str):
    """Cache market research results only in Redis"""
    # Implementation
    pass
```

### 4.2 Cache Invalidation Strategy

```python
# infrastructure/cache_invalidation.py
import asyncio
from typing import Dict, List, Set
import logging

logger = logging.getLogger(__name__)

class CacheInvalidationManager:
    """
    Manage cache invalidation based on data changes
    """

    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.invalidation_rules = {}

    def register_rule(self, pattern: str, keys: List[str]):
        """Register cache invalidation rule"""
        self.invalidation_rules[pattern] = keys

    async def invalidate_on_submission_update(self, submission_id: str):
        """Invalidate caches when submission is updated"""
        patterns = [
            f"analysis:*:{submission_id}*",
            f"embedding:*:{submission_id}*",
            f"market_research:*:{submission_id}*"
        ]

        for pattern in patterns:
            await self.cache_manager.clear_pattern(pattern)

    async def invalidate_on_opportunity_create(self, opportunity_data: Dict):
        """Invalidate caches when new opportunity is created"""
        # Invalidate similar opportunities cache
        subreddit = opportunity_data.get("subreddit")
        if subreddit:
            patterns = [
                f"opportunities:subreddit:{subreddit}:*",
                f"opportunities:recent:*",
                f"opportunities:high_score:*"
            ]

            for pattern in patterns:
                await self.cache_manager.clear_pattern(pattern)

    async def invalidate_on_model_update(self, model_name: str):
        """Invalidate caches when ML model is updated"""
        patterns = [
            f"{model_name}:*",
            f"analysis:*",  # All analyses use models
            f"similarity:*"  # Similarity searches
        ]

        for pattern in patterns:
            await self.cache_manager.clear_pattern(pattern)

# Event-driven invalidation
class EventListener:
    """
    Listen to database events and invalidate cache
    """

    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.invalidation_manager = CacheInvalidationManager(cache_manager)

    async def listen_to_db_changes(self):
        """Listen to PostgreSQL logical replication"""
        # Implementation using pgoutput or similar
        pass

    async def on_table_change(self, table: str, operation: str, data: Dict):
        """Handle database table changes"""
        if table == "opportunities":
            if operation in ["INSERT", "UPDATE"]:
                await self.invalidation_manager.invalidate_on_opportunity_create(data)
            elif operation == "DELETE":
                submission_id = data.get("submission_id")
                if submission_id:
                    await self.invalidation_manager.invalidate_on_submission_update(submission_id)
```

## 5. Performance Optimization

### 5.1 Batch Processing Optimization

```python
# optimization/batch_processor.py
import asyncio
from typing import List, Any, Callable
import time
from dataclasses import dataclass

@dataclass
class BatchConfig:
    batch_size: int = 50
    max_wait_time: float = 1.0  # seconds
    max_concurrent_batches: int = 10

class BatchProcessor:
    """
    Optimized batch processing for embeddings and API calls
    """

    def __init__(self, config: BatchConfig):
        self.config = config
        self.pending_items = []
        self.batch_semaphore = asyncio.Semaphore(config.max_concurrent_batches)
        self.last_batch_time = time.time()

    async def add_item(self, item: Any, process_func: Callable[[List[Any]], Any]):
        """
        Add item to batch for processing
        """
        self.pending_items.append((item, process_func))

        # Check if we should process the batch
        should_process = (
            len(self.pending_items) >= self.config.batch_size or
            time.time() - self.last_batch_time >= self.config.max_wait_time
        )

        if should_process:
            await self._process_batch()

    async def _process_batch(self):
        """Process current batch of items"""
        if not self.pending_items:
            return

        # Extract batch
        batch = self.pending_items[:]
        self.pending_items = []
        self.last_batch_time = time.time()

        # Acquire semaphore for concurrent batch limit
        async with self.batch_semaphore:
            # Group by process function
            groups = {}
            for item, func in batch:
                if func not in groups:
                    groups[func] = []
                groups[func].append(item)

            # Process each group
            tasks = []
            for func, items in groups.items():
                task = asyncio.create_task(self._process_group(func, items))
                tasks.append(task)

            # Wait for all groups to complete
            await asyncio.gather(*tasks)

    async def _process_group(self, func: Callable, items: List[Any]):
        """Process a group of items with the same function"""
        try:
            # Process batch
            results = await func(items)

            # If function returns results, store them
            if results is not None:
                # Implementation depends on your needs
                pass
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            # Optionally retry individually
            for item in items:
                try:
                    await func([item])
                except Exception as e2:
                    logger.error(f"Individual item retry failed: {e2}")

    async def flush(self):
        """Process any remaining items"""
        if self.pending_items:
            await self._process_batch()

# Usage example for embedding generation
class EmbeddingGenerator:
    def __init__(self, embedding_provider):
        self.provider = embedding_provider
        self.batch_processor = BatchProcessor(
            BatchConfig(
                batch_size=100,  # Cohere supports up to 96
                max_wait_time=0.5,
                max_concurrent_batches=5
            )
        )

    async def generate_embedding(self, text: str, metadata: dict = None):
        """Generate embedding with batching"""
        # Create a future for the result
        result_future = asyncio.Future()

        # Define batch processing function
        async def process_batch(texts: List[str]):
            # Generate embeddings in batch
            embeddings = []
            for i, text in enumerate(texts):
                embedding, _ = await self.provider.generate_embedding(text)
                embeddings.append(embedding)

            # Resolve futures
            for i, embedding in enumerate(embeddings):
                if hasattr(texts[i], 'future'):
                    texts[i].future.set_result(embedding)

        # Attach future to text object
        text_obj = type('TextObj', (), {'text': text, 'future': result_future})()

        # Add to batch processor
        await self.batch_processor.add_item(text_obj, process_batch)

        # Return result
        return await result_future
```

### 5.2 Connection Pool Management

```python
# optimization/pool_manager.py
import asyncio
import time
from typing import Dict, List, Optional
import logging
import httpx
import asyncpg

logger = logging.getLogger(__name__)

class ConnectionPoolManager:
    """
    Advanced connection pool management with health checks
    """

    def __init__(self):
        self.pools = {}
        self.health_check_interval = 30  # seconds
        self.health_check_task = None

    async def create_http_pool(
        self,
        name: str,
        base_url: str,
        pool_size: int = 10,
        timeout: float = 30.0
    ):
        """Create HTTP connection pool"""
        limits = httpx.Limits(
            max_keepalive_connections=pool_size,
            max_connections=pool_size * 2,
            keepalive_expiry=30.0
        )

        pool = httpx.AsyncClient(
            base_url=base_url,
            limits=limits,
            timeout=httpx.Timeout(timeout),
            http2=True  # Enable HTTP/2 for better performance
        )

        self.pools[name] = {
            'type': 'http',
            'pool': pool,
            'created_at': time.time(),
            'last_used': time.time()
        }

        logger.info(f"Created HTTP pool {name} with size {pool_size}")
        return pool

    async def create_db_pool(
        self,
        name: str,
        dsn: str,
        min_size: int = 10,
        max_size: int = 20
    ):
        """Create database connection pool"""
        pool = await asyncpg.create_pool(
            dsn,
            min_size=min_size,
            max_size=max_size,
            command_timeout=60,
            server_settings={
                'application_name': 'redditharbor-agno',
                'jit': 'off'  # Disable JIT for simpler queries
            }
        )

        self.pools[name] = {
            'type': 'db',
            'pool': pool,
            'created_at': time.time(),
            'last_used': time.time()
        }

        logger.info(f"Created DB pool {name} with min={min_size}, max={max_size}")
        return pool

    async def get_pool(self, name: str):
        """Get pool by name and update last used time"""
        if name in self.pools:
            self.pools[name]['last_used'] = time.time()
            return self.pools[name]['pool']
        return None

    async def close_all(self):
        """Close all connection pools"""
        for pool_info in self.pools.values():
            if pool_info['type'] == 'http':
                await pool_info['pool'].aclose()
            elif pool_info['type'] == 'db':
                await pool_info['pool'].close()

        self.pools.clear()

        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass

    async def start_health_checks(self):
        """Start periodic health checks"""
        self.health_check_task = asyncio.create_task(self._health_check_loop())

    async def _health_check_loop(self):
        """Periodic health check loop"""
        while True:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(5)

    async def _perform_health_checks(self):
        """Perform health checks on all pools"""
        current_time = time.time()

        for name, pool_info in self.pools.items():
            # Check if pool is stale (not used for 5 minutes)
            if current_time - pool_info['last_used'] > 300:
                logger.info(f"Pool {name} is stale, consider closing")
                continue

            # Perform health check based on type
            if pool_info['type'] == 'http':
                await self._check_http_pool(name, pool_info['pool'])
            elif pool_info['type'] == 'db':
                await self._check_db_pool(name, pool_info['pool'])

    async def _check_http_pool(self, name: str, pool: httpx.AsyncClient):
        """Check HTTP pool health"""
        try:
            # Simple health check
            response = await pool.get("/health")
            if response.status_code == 200:
                logger.debug(f"HTTP pool {name} healthy")
            else:
                logger.warning(f"HTTP pool {name} unhealthy: status {response.status_code}")
        except Exception as e:
            logger.error(f"HTTP pool {name} health check failed: {e}")

    async def _check_db_pool(self, name: str, pool: asyncpg.Pool):
        """Check DB pool health"""
        try:
            async with pool.acquire() as conn:
                await conn.execute("SELECT 1")
            logger.debug(f"DB pool {name} healthy")
        except Exception as e:
            logger.error(f"DB pool {name} health check failed: {e}")

# Global pool manager
pool_manager = ConnectionPoolManager()

# Usage in application
async def init_pools():
    """Initialize all connection pools"""
    await pool_manager.create_http_pool(
        "openrouter",
        "https://openrouter.ai/api/v1",
        pool_size=50
    )

    await pool_manager.create_db_pool(
        "postgres",
        "postgresql://user:pass@host/db",
        min_size=20,
        max_size=50
    )

    await pool_manager.start_health_checks()

async def cleanup_pools():
    """Clean up all connection pools"""
    await pool_manager.close_all()
```

## 6. Monitoring and Observability

### 6.1 Metrics Collection

```python
# monitoring/metrics.py
import time
import asyncio
from typing import Dict, Any
from collections import defaultdict, deque
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class MetricValue:
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)

class MetricsCollector:
    """
    In-memory metrics collection with Prometheus-like functionality
    """

    def __init__(self, retention_period: int = 3600):
        self.retention_period = retention_period
        self.counters = defaultdict(float)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(lambda: defaultdict(deque))
        self.lock = asyncio.Lock()

        # Start cleanup task
        asyncio.create_task(self._cleanup_old_metrics())

    async def increment_counter(self, name: str, value: float = 1.0, tags: Dict[str, str] = None):
        """Increment counter metric"""
        async with self.lock:
            key = self._make_key(name, tags)
            self.counters[key] += value

    async def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set gauge metric"""
        async with self.lock:
            key = self._make_key(name, tags)
            self.gauges[key] = value

    async def observe_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Observe histogram metric"""
        async with self.lock:
            key = self._make_key(name, tags)
            now = time.time()
            self.histograms[key]["values"].append(MetricValue(value, now))

            # Keep only recent values
            cutoff = now - self.retention_period
            while (self.histograms[key]["values"] and
                   self.histograms[key]["values"][0].timestamp < cutoff):
                self.histograms[key]["values"].popleft()

    def _make_key(self, name: str, tags: Dict[str, str] = None) -> str:
        """Create metric key from name and tags"""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{tag_str}}}"

    async def _cleanup_old_metrics(self):
        """Periodic cleanup of old metrics"""
        while True:
            try:
                now = time.time()
                cutoff = now - self.retention_period

                async with self.lock:
                    # Clean histogram values
                    for key in list(self.histograms.keys()):
                        values = self.histograms[key]["values"]
                        while values and values[0].timestamp < cutoff:
                            values.popleft()

                await asyncio.sleep(60)  # Clean every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics cleanup error: {e}")
                await asyncio.sleep(60)

    async def get_stats(self) -> Dict[str, Any]:
        """Get current metrics statistics"""
        async with self.lock:
            stats = {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {}
            }

            # Calculate histogram stats
            for key, data in self.histograms.items():
                values = [v.value for v in data["values"]]
                if values:
                    stats["histograms"][key] = {
                        "count": len(values),
                        "sum": sum(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "p50": self._percentile(values, 0.5),
                        "p95": self._percentile(values, 0.95),
                        "p99": self._percentile(values, 0.99)
                    }

            return stats

    def _percentile(self, values: list, p: float) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * p)
        return sorted_values[min(index, len(sorted_values) - 1)]

# Global metrics instance
metrics = MetricsCollector()

# Decorators for automatic metric collection
def monitor_execution_time(metric_name: str, tags: Dict[str, str] = None):
    """Decorator to monitor execution time"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                await metrics.increment_counter(
                    f"{metric_name}_success_total",
                    tags=tags
                )
                return result
            except Exception as e:
                await metrics.increment_counter(
                    f"{metric_name}_error_total",
                    tags={"error": type(e).__name__, **(tags or {})}
                )
                raise
            finally:
                duration = time.time() - start_time
                await metrics.observe_histogram(
                    f"{metric_name}_duration_seconds",
                    duration,
                    tags=tags
                )
        return wrapper
    return decorator

# Usage example
@monitor_execution_time("analyze_submission", {"service": "agno"})
async def analyze_submission(submission):
    """Analyze submission with metrics"""
    # Implementation
    pass
```

### 6.2 Alerting System

```python
# monitoring/alerting.py
import asyncio
import smtplib
from email.mime.text import MimeText
from typing import Dict, List, Callable, Any
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class AlertRule:
    name: str
    metric_name: str
    condition: str
    threshold: float
    severity: AlertSeverity
    duration: int = 300  # seconds
    message_template: str = None

class AlertManager:
    """
    Alerting system with multiple channels
    """

    def __init__(self):
        self.rules = {}
        self.active_alerts = {}
        self.channels = {
            "email": self._send_email,
            "slack": self._send_slack,
            "webhook": self._send_webhook
        }
        self.alert_history = []

    def add_rule(self, rule: AlertRule):
        """Add alert rule"""
        self.rules[rule.name] = rule

    async def check_alerts(self, metrics_data: Dict[str, Any]):
        """Check all alert rules against metrics"""
        for rule_name, rule in self.rules.items():
            try:
                await self._check_rule(rule, metrics_data)
            except Exception as e:
                logger.error(f"Error checking rule {rule_name}: {e}")

    async def _check_rule(self, rule: AlertRule, metrics_data: Dict[str, Any]):
        """Check individual alert rule"""
        # Get metric value
        metric_value = self._get_metric_value(rule.metric_name, metrics_data)
        if metric_value is None:
            return

        # Evaluate condition
        if self._evaluate_condition(rule.condition, metric_value, rule.threshold):
            # Alert condition met
            alert_key = f"{rule.name}:{rule.metric_name}"

            if alert_key not in self.active_alerts:
                # New alert
                self.active_alerts[alert_key] = {
                    "rule": rule,
                    "start_time": asyncio.get_event_loop().time()
                }

                # Send alert if not in cooldown
                await self._send_alert(rule, metric_value)

            else:
                # Check if alert should be re-fired
                alert = self.active_alerts[alert_key]
                if asyncio.get_event_loop().time() - alert["start_time"] > rule.duration:
                    await self._send_alert(rule, metric_value)

        else:
            # Condition not met, clear alert if active
            alert_key = f"{rule.name}:{rule.metric_name}"
            if alert_key in self.active_alerts:
                del self.active_alerts[alert_key]
                await self._send_resolved_alert(rule, metric_value)

    def _get_metric_value(self, metric_name: str, metrics_data: Dict[str, Any]) -> float:
        """Extract metric value from metrics data"""
        parts = metric_name.split(".")
        value = metrics_data

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None

        return float(value) if isinstance(value, (int, float)) else None

    def _evaluate_condition(self, condition: str, value: float, threshold: float) -> bool:
        """Evaluate alert condition"""
        if condition == "gt":
            return value > threshold
        elif condition == "lt":
            return value < threshold
        elif condition == "eq":
            return value == threshold
        elif condition == "gte":
            return value >= threshold
        elif condition == "lte":
            return value <= threshold
        else:
            return False

    async def _send_alert(self, rule: AlertRule, value: float):
        """Send alert notification"""
        message = self._format_alert_message(rule, value, active=True)

        # Send to configured channels
        for channel_name, channel_func in self.channels.items():
            try:
                await channel_func(
                    subject=f"RedditHarbor Alert: {rule.name}",
                    message=message,
                    severity=rule.severity
                )
            except Exception as e:
                logger.error(f"Failed to send alert to {channel_name}: {e}")

        # Add to history
        self.alert_history.append({
            "rule": rule.name,
            "severity": rule.severity.value,
            "message": message,
            "timestamp": asyncio.get_event_loop().time(),
            "resolved": False
        })

        logger.warning(f"Alert triggered: {rule.name} - {message}")

    async def _send_resolved_alert(self, rule: AlertRule, value: float):
        """Send resolved alert notification"""
        message = self._format_alert_message(rule, value, active=False)

        # Send to channels (only for critical alerts)
        if rule.severity == AlertSeverity.CRITICAL:
            for channel_name, channel_func in self.channels.items():
                try:
                    await channel_func(
                        subject=f"RedditHarbor Resolved: {rule.name}",
                        message=message,
                        severity=AlertSeverity.INFO
                    )
                except Exception as e:
                    logger.error(f"Failed to send resolved alert to {channel_name}: {e}")

        # Add to history
        self.alert_history.append({
            "rule": rule.name,
            "severity": rule.severity.value,
            "message": message,
            "timestamp": asyncio.get_event_loop().time(),
            "resolved": True
        })

        logger.info(f"Alert resolved: {rule.name} - {message}")

    def _format_alert_message(self, rule: AlertRule, value: float, active: bool) -> str:
        """Format alert message"""
        status = "ACTIVE" if active else "RESOLVED"

        if rule.message_template:
            return rule.message_template.format(
                status=status,
                value=value,
                threshold=rule.threshold
            )

        return (
            f"Alert {status}: {rule.name}\n"
            f"Metric: {rule.metric_name}\n"
            f"Current value: {value}\n"
            f"Threshold: {rule.threshold}\n"
            f"Condition: {rule.condition}"
        )

    async def _send_email(self, subject: str, message: str, severity: AlertSeverity):
        """Send email alert"""
        # Implementation depends on your email service
        # Example using SMTP
        msg = MimeText(message)
        msg["Subject"] = subject
        msg["From"] = "alerts@redditharbor.com"
        msg["To"] = "team@redditharbor.com"

        # SMTP implementation here
        pass

    async def _send_slack(self, subject: str, message: str, severity: AlertSeverity):
        """Send Slack alert"""
        # Implementation using Slack webhook
        webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

        payload = {
            "text": f"*{subject}*\n{message}",
            "color": severity.value
        }

        # Send to Slack
        pass

    async def _send_webhook(self, subject: str, message: str, severity: AlertSeverity):
        """Send webhook alert"""
        # Implementation for custom webhook
        pass

# Define alert rules
def create_standard_alert_rules() -> List[AlertRule]:
    """Create standard set of alert rules"""
    return [
        AlertRule(
            name="high_error_rate",
            metric_name="counters.analyze_submission_error_total",
            condition="gt",
            threshold=10,  # More than 10 errors
            severity=AlertSeverity.WARNING,
            message_template="High error rate detected: {value} errors in the last minute"
        ),
        AlertRule(
            name="slow_analysis",
            metric_name="histograms.analyze_submission_duration_seconds.p95",
            condition="gt",
            threshold=5.0,  # p95 > 5 seconds
            severity=AlertSeverity.WARNING,
            message_template="Analysis latency high: p95 = {value}s"
        ),
        AlertRule(
            name="low_throughput",
            metric_name="gauges.submissions_per_minute",
            condition="lt",
            threshold=100,  # Less than 100/min
            severity=AlertSeverity.CRITICAL,
            duration=600,  # 10 minutes
            message_template="Throughput too low: {value} submissions/min"
        ),
        AlertRule(
            name="high_db_connections",
            metric_name="gauges.db_connections_active",
            condition="gt",
            threshold=45,  # More than 45 connections (out of 50)
            severity=AlertSeverity.CRITICAL,
            message_template="Database connections high: {value}/50"
        ),
        AlertRule(
            name="api_rate_limit",
            metric_name="counters.api_rate_limit_total",
            condition="gt",
            threshold=0,  # Any rate limit hits
            severity=AlertSeverity.WARNING,
            message_template="API rate limit hit: {value} times"
        )
    ]

# Global alert manager
alert_manager = AlertManager()

# Initialize standard rules
for rule in create_standard_alert_rules():
    alert_manager.add_rule(rule)
```

## 7. Implementation Timeline

### Phase 1: Database Optimization (Week 1-2)
- [ ] Implement connection pooling
- [ ] Add production indexes
- [ ] Configure read replicas
- [ ] Implement query optimization

### Phase 2: API Resilience (Week 3-4)
- [ ] Implement distributed rate limiting
- [ ] Add circuit breaker pattern
- [ ] Implement retry logic with backoff
- [ ] Add API health checks

### Phase 3: Scalability Infrastructure (Week 5-6)
- [ ] Containerize application
- [ ] Set up Kubernetes cluster
- [ ] Implement auto-scaling
- [ ] Add load balancing

### Phase 4: Performance Optimization (Week 7-8)
- [ ] Implement batching for API calls
- [ ] Add multi-level caching
- [ ] Optimize embedding generation
- [ ] Tune database queries

### Phase 5: Monitoring and Operations (Week 9-10)
- [ ] Implement metrics collection
- [ ] Set up alerting system
- [ ] Add distributed tracing
- [ ] Create dashboards

## 8. Success Metrics

The system will be considered production-ready when it achieves:

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Throughput | 1000 submissions/min | Metrics dashboard |
| Latency (p95) | <500ms | APM tracing |
| Error Rate | <0.1% | Error tracking |
| Availability | 99.9% uptime | SLA monitoring |
| Cost per Analysis | <$0.003 | Cost tracking |
| Auto-scaling | 0-2000 submissions/min | Load testing |
| Recovery Time | <30 seconds | Chaos testing |

---

*Document Version: 1.0*
*Last Updated: December 5, 2024*
*Next Review: December 19, 2024*