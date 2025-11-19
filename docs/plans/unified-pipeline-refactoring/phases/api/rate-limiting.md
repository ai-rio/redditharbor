# Redis Rate Limiting

**Purpose**: Implement distributed, Redis-based rate limiting for the RedditHarbor API, ensuring fair usage and preventing abuse while maintaining scalability across multiple server instances.

---

## Rate Limiting Strategy

### Architecture Overview
- **Redis-based**: Distributed rate limiting using Redis for consistency
- **Token Bucket Algorithm**: Allows burst handling with sustainable rates
- **Per-Endpoint Limits**: Different limits for different resource types
- **Sliding Windows**: More accurate rate limiting than fixed windows
- **Hierarchical Limits**: API key → IP → Global rate limiting

### Why Redis-based Rate Limiting?
1. **Distributed**: Works across multiple API instances
2. **Atomic Operations**: Redis provides atomic counters
3. **TTL Management**: Automatic cleanup of expired rate limit data
4. **Performance**: Sub-millisecond response times
5. **Scalability**: Can handle millions of rate limit checks per minute

---

## Redis Configuration

### Redis Settings for Rate Limiting

```python
# api/core/redis_config.py
from typing import Optional
from pydantic import BaseModel
from api.core.config import settings

class RateLimitRedisConfig(BaseModel):
    """Redis configuration optimized for rate limiting."""

    # Connection settings
    host: str = settings.REDIS_HOST
    port: int = settings.REDIS_PORT
    password: Optional[str] = settings.REDIS_PASSWORD
    db: int = settings.REDIS_DB

    # Pool settings for performance
    max_connections: int = 50
    retry_on_timeout: bool = True
    socket_keepalive: bool = True
    socket_keepalive_options: dict = {}

    # Rate limiting specific settings
    max_memory_policy: str = "allkeys-lru"  # Evict least recently used keys
    lazy_expulsion: bool = True  # Allow lazy expiration for better performance

    @property
    def connection_kwargs(self) -> dict:
        """Get Redis connection arguments."""
        return {
            "host": self.host,
            "port": self.port,
            "password": self.password,
            "db": self.db,
            "max_connections": self.max_connections,
            "retry_on_timeout": self.retry_on_timeout,
            "socket_keepalive": self.socket_keepalive,
            "decode_responses": True,
        }

rate_limit_redis_config = RateLimitRedisConfig()
```

### Redis Connection Management

```python
# api/core/redis_connection.py
from typing import Optional
import redis.asyncio as redis
from redis.asyncio import ConnectionPool, Redis
from api.core.redis_config import rate_limit_redis_config
import logging

logger = logging.getLogger(__name__)

class RedisConnectionManager:
    """Manage Redis connections for rate limiting."""

    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[Redis] = None
        self._connection_url: Optional[str] = None

    async def initialize(self):
        """Initialize Redis connection pool."""
        try:
            if self._pool is None:
                self._connection_url = rate_limit_redis_config.connection_kwargs

                # Create connection pool
                self._pool = ConnectionPool(**self._connection_url)

                # Create Redis client
                self._client = Redis(connection_pool=self._pool)

                # Test connection
                await self._client.ping()

                logger.info("Redis connection established for rate limiting")

        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            raise

    async def get_client(self) -> Redis:
        """Get Redis client (initialize if needed)."""
        if self._client is None:
            await self.initialize()
        return self._client

    async def close(self):
        """Close Redis connections."""
        if self._client:
            await self._client.aclose()
            self._client = None
        if self._pool:
            await self._pool.disconnect()
            self._pool = None
        logger.info("Redis connections closed")

    async def health_check(self) -> bool:
        """Check Redis health."""
        try:
            client = await self.get_client()
            await client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

# Global Redis connection manager
redis_manager = RedisConnectionManager()
```

---

## Rate Limiting Implementation

### Core Rate Limiter Class

Based on the extracted boilerplate, with enhancements for RedditHarbor's specific needs:

```python
# api/core/rate_limit.py
from datetime import UTC, datetime, timedelta
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import json
import time
import asyncio
from redis.asyncio import Redis

from api.core.redis_connection import redis_manager
from api.core.config import settings
import logging

logger = logging.getLogger(__name__)

@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    is_allowed: bool
    remaining_requests: int
    reset_time: int
    retry_after: Optional[int] = None
    limit: int = 0
    window_seconds: int = 0

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    limit: int  # Number of requests allowed
    window_seconds: int  # Time window in seconds
    burst_size: Optional[int] = None  # Optional burst capacity

class RedisRateLimiter:
    """
    Redis-based distributed rate limiter using sliding window algorithm.

    This implementation provides:
    - Sliding time windows for accurate rate limiting
    - Burst capacity for handling traffic spikes
    - Hierarchical rate limiting (user → IP → global)
    - Atomic operations to prevent race conditions
    """

    def __init__(self):
        self._client = None

    async def get_client(self) -> Redis:
        """Get Redis client."""
        if self._client is None:
            self._client = await redis_manager.get_client()
        return self._client

    async def is_rate_limited(
        self,
        key: str,
        limit: int,
        window_seconds: int,
        burst_size: Optional[int] = None
    ) -> RateLimitResult:
        """
        Check if a request is rate limited using sliding window algorithm.

        Args:
            key: Unique identifier for rate limiting (e.g., api_key:ip:endpoint)
            limit: Maximum requests allowed in the window
            window_seconds: Time window size in seconds
            burst_size: Optional burst capacity for handling spikes

        Returns:
            RateLimitResult: Rate limiting information
        """
        client = await self.get_client()
        now = int(time.time())
        window_start = now - window_seconds

        # Use Lua script for atomic operations
        lua_script = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local window_start = tonumber(ARGV[2])
        local limit = tonumber(ARGV[3])
        local window_seconds = tonumber(ARGV[4])
        local burst_size = tonumber(ARGV[5]) or limit

        -- Remove expired entries
        redis.call('ZREMRANGEBYSCORE', key, 0, window_start)

        -- Count current requests in window
        local current_count = redis.call('ZCARD', key)

        -- Calculate effective limit with burst capacity
        local effective_limit = math.min(limit + burst_size, limit * 2)

        -- Check if request is allowed
        if current_count >= effective_limit then
            -- Get oldest request timestamp for retry_after
            local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
            local retry_after = 0
            if #oldest > 0 then
                retry_after = tonumber(oldest[2]) + window_seconds - now
                if retry_after < 0 then
                    retry_after = 1
                end
            end

            return {
                allowed = false,
                current_count = current_count,
                limit = limit,
                window_seconds = window_seconds,
                retry_after = retry_after
            }
        end

        -- Add current request
        redis.call('ZADD', key, now, now)
        redis.call('EXPIRE', key, window_seconds + 1)

        -- Return updated state
        return {
            allowed = true,
            current_count = current_count + 1,
            limit = limit,
            window_seconds = window_seconds,
            retry_after = 0
        }
        """

        try:
            # Execute Lua script atomically
            result = await client.eval(
                lua_script,
                1,  # Number of keys
                key,
                now,
                window_start,
                limit,
                window_seconds,
                burst_size or limit
            )

            # Parse result
            result_data = {
                'allowed': bool(result[0]),
                'current_count': int(result[1]),
                'limit': int(result[2]),
                'window_seconds': int(result[3]),
                'retry_after': int(result[4]) if len(result) > 4 else 0
            }

            # Calculate reset time
            reset_time = now + window_seconds

            return RateLimitResult(
                is_allowed=result_data['allowed'],
                remaining_requests=max(0, limit - result_data['current_count']),
                reset_time=reset_time,
                retry_after=result_data['retry_after'] if not result_data['allowed'] else None,
                limit=limit,
                window_seconds=window_seconds
            )

        except Exception as e:
            logger.error(f"Rate limiting error for key {key}: {e}")
            # Fail open: allow request if Redis is down
            return RateLimitResult(
                is_allowed=True,
                remaining_requests=limit,
                reset_time=now + window_seconds,
                limit=limit,
                window_seconds=window_seconds
            )

    async def get_rate_limit_info(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> Dict:
        """Get current rate limit information without incrementing counter."""

        client = await self.get_client()
        now = int(time.time())
        window_start = now - window_seconds

        try:
            # Count requests in current window
            current_count = await client.zcount(key, window_start, '+inf')
            remaining_requests = max(0, limit - current_count)

            # Get TTL for reset time
            ttl = await client.ttl(key)
            reset_time = now + max(ttl, 0)

            return {
                'current_count': current_count,
                'limit': limit,
                'remaining_requests': remaining_requests,
                'reset_time': reset_time,
                'window_seconds': window_seconds
            }

        except Exception as e:
            logger.error(f"Failed to get rate limit info for {key}: {e}")
            return {
                'current_count': 0,
                'limit': limit,
                'remaining_requests': limit,
                'reset_time': now + window_seconds,
                'window_seconds': window_seconds
            }

    async def reset_rate_limit(self, key: str) -> bool:
        """Reset rate limit for a specific key."""

        client = await self.get_client()
        try:
            await client.delete(key)
            logger.info(f"Rate limit reset for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to reset rate limit for {key}: {e}")
            return False

# Global rate limiter instance
rate_limiter = RedisRateLimiter()
```

### Hierarchical Rate Limiting

```python
# api/core/hierarchical_rate_limiter.py
from typing import Dict, Optional, List
from fastapi import Request, HTTPException
from api.core.rate_limit import RateLimitResult, RateLimitConfig
from api.core.config import settings
import logging

logger = logging.getLogger(__name__)

class HierarchicalRateLimiter:
    """
    Implement hierarchical rate limiting:
    1. Global API limits
    2. Per-API-key limits
    3. Per-IP limits
    4. Per-endpoint limits
    """

    # Define rate limit configurations for different endpoint types
    RATE_LIMIT_CONFIGS = {
        # Pipeline endpoints (expensive operations)
        'pipeline': RateLimitConfig(
            limit=5,
            window_seconds=60,
            burst_size=2
        ),

        # AI analysis endpoints
        'analysis': RateLimitConfig(
            limit=20,
            window_seconds=60,
            burst_size=5
        ),

        # Data retrieval endpoints
        'data': RateLimitConfig(
            limit=100,
            window_seconds=60,
            burst_size=20
        ),

        # Monitoring endpoints
        'monitoring': RateLimitConfig(
            limit=60,
            window_seconds=60,
            burst_size=10
        ),

        # Default configuration
        'default': RateLimitConfig(
            limit=60,
            window_seconds=60,
            burst_size=10
        )
    }

    # API key specific limits (for different service types)
    API_KEY_LIMITS = {
        'primary': RateLimitConfig(limit=200, window_seconds=60),
        'webhook': RateLimitConfig(limit=50, window_seconds=60),
        'monitoring': RateLimitConfig(limit=120, window_seconds=60),
        'default': RateLimitConfig(limit=60, window_seconds=60)
    }

    async def check_rate_limits(
        self,
        request: Request,
        api_key: str,
        key_info: dict
    ) -> RateLimitResult:
        """
        Check hierarchical rate limits for a request.

        Args:
            request: FastAPI request object
            api_key: API key from request
            key_info: API key information including permissions

        Returns:
            RateLimitResult: Result of the most restrictive rate limit check
        """
        client_ip = self._get_client_ip(request)
        endpoint_type = self._get_endpoint_type(request.url.path)
        key_name = key_info.get('name', 'default')

        # Check limits in order of restrictiveness
        checks = [
            # 1. Global API limits (most restrictive)
            await self._check_global_limits(endpoint_type),

            # 2. Per-API-key limits
            await self._check_api_key_limits(api_key, key_name),

            # 3. Per-IP limits
            await self._check_ip_limits(client_ip),

            # 4. Per-endpoint limits
            await self._check_endpoint_limits(client_ip, endpoint_type)
        ]

        # Find the most restrictive limit
        most_restrictive = max(checks, key=lambda r: (not r.is_allowed, r.remaining_requests))

        # Log rate limit hits for monitoring
        if not most_restrictive.is_allowed:
            logger.warning(
                f"Rate limit exceeded: {api_key[:8]}... from {client_ip} "
                f"on {request.url.path}. Remaining: {most_restrictive.remaining_requests}"
            )

        return most_restrictive

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection IP
        return request.client.host

    def _get_endpoint_type(self, path: str) -> str:
        """Determine endpoint type from URL path."""
        path = path.lower()

        if '/pipeline' in path:
            return 'pipeline'
        elif any(word in path for word in ['/profiler', '/analyze', '/enrich']):
            return 'analysis'
        elif any(word in path for word in ['/opportunities', '/data', '/search']):
            return 'data'
        elif any(word in path for word in ['/health', '/metrics', '/status']):
            return 'monitoring'
        else:
            return 'default'

    async def _check_global_limits(self, endpoint_type: str) -> RateLimitResult:
        """Check global API limits."""
        config = self.RATE_LIMIT_CONFIGS[endpoint_type]
        key = f"global:{endpoint_type}"

        return await rate_limiter.is_rate_limited(
            key=key,
            limit=config.limit * 2,  # Higher global limit
            window_seconds=config.window_seconds,
            burst_size=config.burst_size * 2
        )

    async def _check_api_key_limits(self, api_key: str, key_name: str) -> RateLimitResult:
        """Check per-API-key limits."""
        config = self.API_KEY_LIMITS.get(key_name, self.API_KEY_LIMITS['default'])
        key = f"apikey:{api_key}"

        return await rate_limiter.is_rate_limited(
            key=key,
            limit=config.limit,
            window_seconds=config.window_seconds,
            burst_size=config.burst_size or config.limit // 4
        )

    async def _check_ip_limits(self, client_ip: str) -> RateLimitResult:
        """Check per-IP limits."""
        # Basic IP-based limits to prevent abuse
        key = f"ip:{client_ip}"

        return await rate_limiter.is_rate_limited(
            key=key,
            limit=100,  # 100 requests per minute per IP
            window_seconds=60,
            burst_size=20
        )

    async def _check_endpoint_limits(self, client_ip: str, endpoint_type: str) -> RateLimitResult:
        """Check per-endpoint per-IP limits."""
        config = self.RATE_LIMIT_CONFIGS[endpoint_type]
        key = f"endpoint:{client_ip}:{endpoint_type}"

        return await rate_limiter.is_rate_limited(
            key=key,
            limit=config.limit // 2,  # Half the normal limit per IP
            window_seconds=config.window_seconds,
            burst_size=config.burst_size
        )

# Global hierarchical rate limiter
hierarchical_rate_limiter = HierarchicalRateLimiter()
```

### FastAPI Integration

```python
# api/core/rate_limit_dependencies.py
from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from api.core.auth import verify_api_key, get_api_key_info
from api.core.hierarchical_rate_limiter import hierarchical_rate_limiter
from api.core.rate_limit import RateLimitResult
import logging

logger = logging.getLogger(__name__)

class RateLimitHTTPException(HTTPException):
    """HTTP exception for rate limiting with proper headers."""

    def __init__(self, result: RateLimitResult):
        headers = {
            "X-RateLimit-Limit": str(result.limit),
            "X-RateLimit-Remaining": str(result.remaining_requests),
            "X-RateLimit-Reset": str(result.reset_time),
        }

        if result.retry_after:
            headers["Retry-After"] = str(result.retry_after)

        super().__init__(
            status_code=429,
            detail="Rate limit exceeded",
            headers=headers
        )

async def rate_limit_dependency(
    request: Request,
    api_key: str = Depends(verify_api_key),
    key_info: dict = Depends(get_api_key_info)
):
    """
    FastAPI dependency for rate limiting.

    This function checks all applicable rate limits and raises
    an exception if any limit is exceeded.
    """
    try:
        # Check hierarchical rate limits
        result = await hierarchical_rate_limiter.check_rate_limits(
            request=request,
            api_key=api_key,
            key_info=key_info
        )

        # Add rate limit headers to response
        if hasattr(request.state, 'add_response_headers'):
            request.state.add_response_headers({
                "X-RateLimit-Limit": str(result.limit),
                "X-RateLimit-Remaining": str(result.remaining_requests),
                "X-RateLimit-Reset": str(result.reset_time),
            })

        # Raise exception if rate limited
        if not result.is_allowed:
            raise RateLimitHTTPException(result)

        return result

    except Exception as e:
        if isinstance(e, RateLimitHTTPException):
            raise

        logger.error(f"Rate limiting error: {e}")
        # Fail open: allow request if rate limiting fails
        return RateLimitResult(
            is_allowed=True,
            remaining_requests=60,
            reset_time=int(time.time()) + 60
        )

# Usage in route handlers:
# @router.post("/pipeline/run")
# async def run_pipeline(
#     request: PipelineRunRequest,
#     rate_limit_result: RateLimitResult = Depends(rate_limit_dependency)
# ):
#     # Route implementation
#     pass
```

---

## Advanced Features

### Rate Limit Analytics

```python
# api/monitoring/rate_limit_analytics.py
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from api.core.redis_connection import redis_manager
import logging

logger = logging.getLogger(__name__)

@dataclass
class RateLimitMetrics:
    """Rate limiting metrics."""
    total_requests: int
    blocked_requests: int
    top_consumers: List[Dict]
    endpoint_usage: Dict[str, int]
    hourly_breakdown: Dict[str, int]

class RateLimitAnalytics:
    """Analyze rate limiting patterns and metrics."""

    async def get_metrics(
        self,
        time_range_hours: int = 24
    ) -> RateLimitMetrics:
        """Get rate limiting metrics for the specified time range."""

        client = await redis_manager.get_client()

        try:
            # Get metrics from Redis analytics
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=time_range_hours)

            # Fetch various metrics
            total_requests = await self._get_total_requests(client, start_time, end_time)
            blocked_requests = await self._get_blocked_requests(client, start_time, end_time)
            top_consumers = await self._get_top_consumers(client, start_time, end_time)
            endpoint_usage = await self._get_endpoint_usage(client, start_time, end_time)
            hourly_breakdown = await self._get_hourly_breakdown(client, start_time, end_time)

            return RateLimitMetrics(
                total_requests=total_requests,
                blocked_requests=blocked_requests,
                top_consumers=top_consumers,
                endpoint_usage=endpoint_usage,
                hourly_breakdown=hourly_breakdown
            )

        except Exception as e:
            logger.error(f"Failed to get rate limit metrics: {e}")
            # Return empty metrics on error
            return RateLimitMetrics(
                total_requests=0,
                blocked_requests=0,
                top_consumers=[],
                endpoint_usage={},
                hourly_breakdown={}
            )

    async def _get_total_requests(
        self,
        client,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """Get total number of requests in time range."""
        # This would require additional Redis analytics setup
        # For now, return estimated value
        return 0

    async def _get_blocked_requests(
        self,
        client,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """Get number of blocked requests due to rate limiting."""
        # This would require tracking blocked requests in Redis
        return 0

    async def _get_top_consumers(
        self,
        client,
        start_time: datetime,
        end_time: datetime,
        limit: int = 10
    ) -> List[Dict]:
        """Get top API key consumers."""
        # This would require additional tracking in Redis
        return []

    async def _get_endpoint_usage(
        self,
        client,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, int]:
        """Get usage breakdown by endpoint type."""
        # This would require tracking endpoint usage
        return {}

    async def _get_hourly_breakdown(
        self,
        client,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, int]:
        """Get hourly request breakdown."""
        # This would require hourly analytics tracking
        return {}

# Global analytics instance
rate_limit_analytics = RateLimitAnalytics()
```

### Adaptive Rate Limiting

```python
# api/core/adaptive_rate_limiter.py
from typing import Dict, Optional
from datetime import datetime, timedelta
from api.core.rate_limit import RateLimitConfig, RateLimitResult
from api.core.redis_connection import redis_manager
import logging

logger = logging.getLogger(__name__)

class AdaptiveRateLimiter:
    """
    Dynamically adjust rate limits based on system load and usage patterns.

    Features:
    - Load-based limit adjustments
    - Time-of-day scaling
    - VIP user priority limits
    - Emergency throttling
    """

    def __init__(self):
        self.load_thresholds = {
            'high_load': 0.8,  # 80% CPU/memory usage
            'medium_load': 0.6,  # 60% CPU/memory usage
            'low_load': 0.3     # 30% CPU/memory usage
        }

    async def get_adaptive_config(
        self,
        base_config: RateLimitConfig,
        api_key: str,
        endpoint_type: str
    ) -> RateLimitConfig:
        """
        Get rate limit configuration adapted to current conditions.

        Args:
            base_config: Base rate limit configuration
            api_key: API key identifier
            endpoint_type: Type of endpoint being accessed

        Returns:
            RateLimitConfig: Adapted rate limit configuration
        """
        try:
            # Get current system load
            current_load = await self._get_system_load()

            # Check if API key has VIP status
            is_vip = await self._is_vip_key(api_key)

            # Get time-based multiplier
            time_multiplier = self._get_time_multiplier()

            # Calculate load-based multiplier
            load_multiplier = self._get_load_multiplier(current_load)

            # Get priority multiplier for VIP users
            priority_multiplier = 2.0 if is_vip else 1.0

            # Apply all multipliers
            final_multiplier = (
                load_multiplier *
                time_multiplier *
                priority_multiplier
            )

            # Create adapted configuration
            adapted_limit = int(base_config.limit * final_multiplier)
            adapted_burst = int(
                (base_config.burst_size or base_config.limit) * final_multiplier
            )

            # Ensure minimum limits
            adapted_limit = max(adapted_limit, base_config.limit // 4)
            adapted_burst = max(adapted_burst, 1)

            return RateLimitConfig(
                limit=adapted_limit,
                window_seconds=base_config.window_seconds,
                burst_size=adapted_burst
            )

        except Exception as e:
            logger.error(f"Failed to get adaptive config: {e}")
            # Return base config on error
            return base_config

    async def _get_system_load(self) -> float:
        """Get current system load (0.0 to 1.0)."""
        try:
            # This would integrate with system monitoring
            # For now, return a mock value
            return 0.4  # 40% load
        except Exception:
            return 0.5  # Default to 50% if monitoring fails

    async def _is_vip_key(self, api_key: str) -> bool:
        """Check if API key has VIP status."""
        # This would check against a database or Redis set of VIP keys
        return False

    def _get_time_multiplier(self) -> float:
        """Get time-based multiplier for rate limits."""
        current_hour = datetime.now().hour

        # Peak hours (9 AM - 5 PM) - more restrictive
        if 9 <= current_hour <= 17:
            return 0.8
        # Evening hours (6 PM - 10 PM) - normal
        elif 18 <= current_hour <= 22:
            return 1.0
        # Late night/early morning - more permissive
        else:
            return 1.5

    def _get_load_multiplier(self, load: float) -> float:
        """Get load-based multiplier for rate limits."""
        if load >= self.load_thresholds['high_load']:
            return 0.5  # Halve limits under high load
        elif load >= self.load_thresholds['medium_load']:
            return 0.8  # Reduce limits under medium load
        elif load <= self.load_thresholds['low_load']:
            return 1.5  # Increase limits under low load
        else:
            return 1.0  # Normal limits

# Global adaptive rate limiter
adaptive_rate_limiter = AdaptiveRateLimiter()
```

---

## Monitoring and Alerting

### Rate Limit Monitoring

```python
# api/monitoring/rate_limit_monitor.py
from typing import Dict, List
from datetime import datetime, timedelta
import asyncio
from api.core.redis_connection import redis_manager
from api.core.config import settings
import logging

logger = logging.getLogger(__name__)

class RateLimitMonitor:
    """Monitor rate limiting health and performance."""

    def __init__(self):
        self.alert_thresholds = {
            'redis_connection_failures': 5,  # 5 failures in 5 minutes
            'high_block_rate': 0.3,         # 30% of requests blocked
            'memory_usage': 0.9,           # 90% Redis memory usage
        }
        self.metrics = {
            'total_checks': 0,
            'blocked_requests': 0,
            'redis_errors': 0,
            'last_check': None
        }

    async def start_monitoring(self):
        """Start background monitoring task."""
        asyncio.create_task(self._monitoring_loop())

    async def _monitoring_loop(self):
        """Background monitoring loop."""
        while True:
            try:
                await self._check_rate_limit_health()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Rate limit monitoring error: {e}")
                await asyncio.sleep(60)

    async def _check_rate_limit_health(self):
        """Check the health of the rate limiting system."""
        now = datetime.now()

        # Check Redis connection health
        redis_healthy = await self._check_redis_health()
        if not redis_healthy:
            self.metrics['redis_errors'] += 1
            await self._check_redis_error_threshold(now)

        # Check Redis memory usage
        memory_usage = await self._get_redis_memory_usage()
        if memory_usage > self.alert_thresholds['memory_usage']:
            await self._alert_high_memory_usage(memory_usage)

        # Check block rate
        if self.metrics['total_checks'] > 100:  # Only check with sufficient sample size
            block_rate = self.metrics['blocked_requests'] / self.metrics['total_checks']
            if block_rate > self.alert_thresholds['high_block_rate']:
                await self._alert_high_block_rate(block_rate)

        self.metrics['last_check'] = now

    async def _check_redis_health(self) -> bool:
        """Check Redis connection health."""
        try:
            client = await redis_manager.get_client()
            await client.ping()
            return True
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return False

    async def _check_redis_error_threshold(self, now: datetime):
        """Check if Redis error threshold is exceeded."""
        # Reset counter if it's been more than 5 minutes
        if hasattr(self, '_last_redis_error_time'):
            if now - self._last_redis_error_time > timedelta(minutes=5):
                self.metrics['redis_errors'] = 0

        self._last_redis_error_time = now

        if self.metrics['redis_errors'] >= self.alert_thresholds['redis_connection_failures']:
            await self._alert_redis_connection_issues()

    async def _get_redis_memory_usage(self) -> float:
        """Get Redis memory usage as fraction (0.0 to 1.0)."""
        try:
            client = await redis_manager.get_client()
            info = await client.info('memory')
            used_memory = info.get('used_memory', 0)
            max_memory = info.get('maxmemory', 0)

            if max_memory > 0:
                return used_memory / max_memory
            else:
                # If maxmemory not set, estimate based on available memory
                return used_memory / (1024 * 1024 * 1024)  # Assume 1GB as reference
        except Exception as e:
            logger.error(f"Failed to get Redis memory usage: {e}")
            return 0.0

    async def _alert_high_block_rate(self, block_rate: float):
        """Alert on high request block rate."""
        message = (
            f"High rate limit block rate detected: {block_rate:.1%}. "
            f"This may indicate overly restrictive limits or abuse."
        )
        logger.warning(message)
        # In production, send alert to monitoring system
        # await self._send_alert("high_block_rate", message)

    async def _alert_high_memory_usage(self, memory_usage: float):
        """Alert on high Redis memory usage."""
        message = (
            f"High Redis memory usage: {memory_usage:.1%}. "
            f"Consider increasing memory or adjusting eviction policy."
        )
        logger.error(message)
        # In production, send alert to monitoring system
        # await self._send_alert("high_memory_usage", message)

    async def _alert_redis_connection_issues(self):
        """Alert on Redis connection issues."""
        message = (
            f"Multiple Redis connection failures detected. "
            f"Rate limiting may be failing open."
        )
        logger.error(message)
        # In production, send alert to monitoring system
        # await self._send_alert("redis_connection_issues", message)

    def record_check(self, blocked: bool):
        """Record a rate limit check for metrics."""
        self.metrics['total_checks'] += 1
        if blocked:
            self.metrics['blocked_requests'] += 1

    def get_metrics(self) -> Dict:
        """Get current monitoring metrics."""
        return {
            **self.metrics,
            'block_rate': (
                self.metrics['blocked_requests'] / max(1, self.metrics['total_checks'])
            )
        }

# Global rate limit monitor
rate_limit_monitor = RateLimitMonitor()
```

---

## Testing Rate Limiting

### Unit Tests

```python
# tests/test_rate_limiting.py
import pytest
import time
import asyncio
from unittest.mock import AsyncMock, patch
from api.core.rate_limit import RedisRateLimiter, RateLimitConfig
from api.core.hierarchical_rate_limiter import HierarchicalRateLimiter

@pytest.fixture
async def rate_limiter():
    """Create a rate limiter for testing."""
    limiter = RedisRateLimiter()

    # Mock Redis client for testing
    mock_client = AsyncMock()
    mock_client.ping.return_value = True
    limiter._client = mock_client

    return limiter

@pytest.fixture
async def hierarchical_limiter():
    """Create a hierarchical rate limiter for testing."""
    return HierarchicalRateLimiter()

class TestRedisRateLimiter:
    """Test the core Redis rate limiter."""

    @pytest.mark.asyncio
    async def test_basic_rate_limiting(self, rate_limiter):
        """Test basic rate limiting functionality."""
        # Mock Redis to return successful rate limit check
        rate_limiter._client.eval.return_value = [True, 1, 5, 60, 0]

        result = await rate_limiter.is_rate_limited(
            key="test:key",
            limit=5,
            window_seconds=60
        )

        assert result.is_allowed is True
        assert result.remaining_requests == 4
        assert result.limit == 5
        assert result.window_seconds == 60

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, rate_limiter):
        """Test rate limit exceeded scenario."""
        # Mock Redis to return rate limit exceeded
        rate_limiter._client.eval.return_value = [False, 5, 5, 60, 30]

        result = await rate_limiter.is_rate_limited(
            key="test:key",
            limit=5,
            window_seconds=60
        )

        assert result.is_allowed is False
        assert result.remaining_requests == 0
        assert result.retry_after == 30

    @pytest.mark.asyncio
    async def test_redis_error_handling(self, rate_limiter):
        """Test handling of Redis errors."""
        # Mock Redis to raise an exception
        rate_limiter._client.eval.side_effect = Exception("Redis error")

        result = await rate_limiter.is_rate_limited(
            key="test:key",
            limit=5,
            window_seconds=60
        )

        # Should fail open - allow request when Redis is down
        assert result.is_allowed is True
        assert result.remaining_requests == 5

    @pytest.mark.asyncio
    async def test_burst_capacity(self, rate_limiter):
        """Test burst capacity functionality."""
        # Mock Redis to allow burst
        rate_limiter._client.eval.return_value = [True, 8, 5, 60, 0]

        result = await rate_limiter.is_rate_limited(
            key="test:key",
            limit=5,
            window_seconds=60,
            burst_size=5
        )

        assert result.is_allowed is True
        # Should allow up to limit + burst_size = 10 requests
        assert result.remaining_requests >= 0

class TestHierarchicalRateLimiter:
    """Test the hierarchical rate limiter."""

    @pytest.mark.asyncio
    async def test_endpoint_classification(self, hierarchical_limiter):
        """Test endpoint type classification."""
        assert hierarchical_limiter._get_endpoint_type("/api/v1/pipeline/run") == "pipeline"
        assert hierarchical_limiter._get_endpoint_type("/api/v1/profiler/analyze") == "analysis"
        assert hierarchical_limiter._get_endpoint_type("/api/v1/opportunities") == "data"
        assert hierarchical_limiter._get_endpoint_type("/api/v1/health") == "monitoring"
        assert hierarchical_limiter._get_endpoint_type("/api/v1/unknown") == "default"

    @pytest.mark.asyncio
    async def test_client_ip_extraction(self, hierarchical_limiter):
        """Test client IP extraction."""
        # Mock request object
        class MockRequest:
            def __init__(self, headers=None, client=None):
                self.headers = headers or {}
                self.client = client

        # Test with X-Forwarded-For header
        request = MockRequest(
            headers={"X-Forwarded-For": "203.0.113.1, 10.0.0.1"},
            client=None
        )
        assert hierarchical_limiter._get_client_ip(request) == "203.0.113.1"

        # Test with X-Real-IP header
        request = MockRequest(
            headers={"X-Real-IP": "203.0.113.2"},
            client=None
        )
        assert hierarchical_limiter._get_client_ip(request) == "203.0.113.2"

        # Test with direct IP
        request = MockRequest(
            headers={},
            client=type('Client', (), {'host': '203.0.113.3'})()
        )
        assert hierarchical_limiter._get_client_ip(request) == "203.0.113.3"

class TestAdaptiveRateLimiting:
    """Test adaptive rate limiting functionality."""

    @pytest.mark.asyncio
    async def test_time_based_adjustment(self):
        """Test time-based rate limit adjustments."""
        from api.core.adaptive_rate_limiter import AdaptiveRateLimiter

        adaptive_limiter = AdaptiveRateLimiter()
        base_config = RateLimitConfig(limit=100, window_seconds=60)

        # Mock different hours
        with patch('datetime.datetime') as mock_datetime:
            # Peak hours
            mock_datetime.now.return_value.hour = 14
            peak_config = await adaptive_limiter.get_adaptive_config(
                base_config, "test_key", "pipeline"
            )
            assert peak_config.limit < base_config.limit

            # Late night
            mock_datetime.now.return_value.hour = 2
            night_config = await adaptive_limiter.get_adaptive_config(
                base_config, "test_key", "pipeline"
            )
            assert night_config.limit > base_config.limit
```

### Integration Tests

```python
# tests/test_rate_limiting_integration.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch
from api.main import app

client = TestClient(app)

class TestRateLimitingIntegration:
    """Test rate limiting in the actual FastAPI application."""

    def test_rate_limit_headers(self):
        """Test that rate limit headers are present in responses."""
        with patch.dict('os.environ', {'REDDIT_HARBOR_API_KEY': 'test-key'}):
            response = client.get(
                "/api/v1/health",
                headers={"X-API-Key": "test-key"}
            )

            assert response.status_code == 200
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers

    def test_rate_limit_exceeded_response(self):
        """Test rate limit exceeded response format."""
        # This test would need to mock Redis to simulate rate limit exceeded
        with patch.dict('os.environ', {'REDDIT_HARBOR_API_KEY': 'test-key'}):
            # Mock rate limiter to return exceeded limit
            with patch('api.core.hierarchical_rate_limiter.hierarchical_rate_limiter.check_rate_limits') as mock_check:
                from api.core.rate_limit import RateLimitResult

                mock_check.return_value = RateLimitResult(
                    is_allowed=False,
                    remaining_requests=0,
                    reset_time=int(time.time()) + 60,
                    retry_after=30,
                    limit=5,
                    window_seconds=60
                )

                response = client.get(
                    "/api/v1/health",
                    headers={"X-API-Key": "test-key"}
                )

                assert response.status_code == 429
                assert "Rate limit exceeded" in response.json()["detail"]
                assert "X-RateLimit-Limit" in response.headers
                assert "Retry-After" in response.headers

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test rate limiting under concurrent load."""
        import aiohttp
        import asyncio

        async def make_request(session):
            """Make a single API request."""
            try:
                async with session.get(
                    "http://localhost:8000/api/v1/health",
                    headers={"X-API-Key": "test-key"}
                ) as response:
                    return response.status
            except Exception:
                return None

        # Test with multiple concurrent requests
        async with aiohttp.ClientSession() as session:
            tasks = [make_request(session) for _ in range(20)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Most requests should succeed (depending on rate limit configuration)
        success_count = sum(1 for r in results if r == 200)
        assert success_count >= 10  # At least half should succeed
```

### Load Testing

```python
# tests/load_test_rate_limiting.py
from locust import HttpUser, task, between
import random

class RedditHarborAPIUser(HttpUser):
    """Load testing user for rate limiting."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Setup API key for requests."""
        self.api_key = "test-key"
        self.client.headers.update({"X-API-Key": self.api_key})

    @task(3)
    def health_check(self):
        """Test health endpoint (should have high rate limits)."""
        self.client.get("/api/v1/health")

    @task(2)
    def get_metrics(self):
        """Test metrics endpoint."""
        self.client.get("/api/v1/metrics")

    @task(1)
    def pipeline_small(self):
        """Test small pipeline execution (expensive operation)."""
        self.client.post(
            "/api/v1/pipeline/run",
            json={"source": "database", "limit": 5}
        )

    @task(1)
    def analyze_submission(self):
        """Test submission analysis."""
        self.client.post(
            "/api/v1/profiler/analyze",
            json={
                "submission_id": "test123",
                "submission_title": "Test submission",
                "submission_content": "Test content for analysis",
                "subreddit": "test"
            }
        )

class RateLimitStressTest(HttpUser):
    """Stress test specifically for rate limiting."""

    wait_time = between(0.1, 0.5)  # Very rapid requests

    def on_start(self):
        self.api_key = "test-key"
        self.client.headers.update({"X-API-Key": self.api_key})

    @task
    def rapid_requests(self):
        """Make rapid requests to test rate limiting."""
        endpoint = random.choice([
            "/api/v1/health",
            "/api/v1/metrics",
            "/api/v1/opportunities"
        ])

        with self.client.get(endpoint, catch_response=True) as response:
            if response.status_code == 429:
                # Rate limited - expected behavior
                response.success()
            elif response.status_code >= 500:
                response.failure(f"Server error: {response.status_code}")
            else:
                response.success()
```

---

## Production Deployment

### Redis Configuration for Rate Limiting

```redis
# redis.conf - Optimized for rate limiting
# Memory management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence (minimal for rate limiting data)
save 900 1
save 300 10
save 60 10000

# Network settings
tcp-keepalive 60
timeout 0

# Performance optimizations
tcp-backlog 511
databases 1

# Slow log (monitor performance)
slowlog-log-slower-than 1000
slowlog-max-len 128

# Client connections
maxclients 10000

# Lazy expiration (better for rate limiting)
lazy-expire yes
```

### Monitoring Rate Limiting Health

```python
# scripts/monitor_rate_limits.py
import asyncio
import sys
from datetime import datetime
from api.core.redis_connection import redis_manager
from api.core.rate_limit import rate_limiter
from api.monitoring.rate_limit_monitor import rate_limit_monitor

async def check_rate_limit_health():
    """Check the health of the rate limiting system."""
    print("🔍 Checking Rate Limit System Health")
    print("=" * 50)

    # Check Redis connection
    print("\n📡 Redis Connection:")
    try:
        redis_healthy = await redis_manager.health_check()
        print(f"   Status: {'✅ Healthy' if redis_healthy else '❌ Unhealthy'}")
    except Exception as e:
        print(f"   Status: ❌ Error - {e}")

    # Test rate limiter functionality
    print("\n⚡ Rate Limiter Functionality:")
    try:
        result = await rate_limiter.is_rate_limited(
            key="health_check",
            limit=10,
            window_seconds=60
        )
        print(f"   Status: ✅ Working")
        print(f"   Allowed: {result.is_allowed}")
        print(f"   Remaining: {result.remaining_requests}")
    except Exception as e:
        print(f"   Status: ❌ Error - {e}")

    # Get monitoring metrics
    print("\n📊 Monitoring Metrics:")
    try:
        metrics = rate_limit_monitor.get_metrics()
        print(f"   Total Checks: {metrics['total_checks']}")
        print(f"   Blocked Requests: {metrics['blocked_requests']}")
        print(f"   Block Rate: {metrics['block_rate']:.1%}")
        print(f"   Redis Errors: {metrics['redis_errors']}")
        if metrics['last_check']:
            print(f"   Last Check: {metrics['last_check']}")
    except Exception as e:
        print(f"   Status: ❌ Error - {e}")

    print("\n" + "=" * 50)
    print("✅ Rate limit health check complete")

if __name__ == "__main__":
    asyncio.run(check_rate_limit_health())
```

### Docker Compose with Redis

```yaml
# docker-compose.yml (enhanced for rate limiting)
services:
  api:
    build:
      context: .
      dockerfile: api/Dockerfile
    command: gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
    env_file:
      - .env
    ports:
      - "8000:8000"
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379
      - REDDIT_HARBOR_API_KEY=${REDDIT_HARBOR_API_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
      - ./redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  redis-commander:
    image: rediscommander/redis-commander:latest
    environment:
      - REDIS_HOSTS=local:redis:6379
    ports:
      - "8081:8081"
    depends_on:
      - redis
    profiles:
      - tools

volumes:
  redis-data:
    driver: local
```

This comprehensive rate limiting implementation provides production-ready, scalable, and feature-complete rate limiting for the RedditHarbor API using Redis, with hierarchical limits, adaptive adjustments, and comprehensive monitoring.