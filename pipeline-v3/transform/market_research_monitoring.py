"""
MarketResearchAgent Monitoring and Observability Module

Production-grade monitoring, metrics collection, and observability for
Jina Market Research Integration Phase 3.7
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

# Prometheus metrics (with fallback)
try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# Redis for distributed monitoring (with fallback)
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class MarketResearchMetrics:
    """Metrics data structure for market research operations"""
    timestamp: datetime
    operation_type: str
    app_concept_id: str | None = None
    target_market: str | None = None

    # Performance metrics
    response_time_ms: float = 0.0
    jina_api_time_ms: float = 0.0
    cache_hit: bool = False

    # Cost metrics
    total_cost_usd: float = 0.0
    jina_cost_usd: float = 0.0
    llm_cost_usd: float = 0.0

    # Quality metrics
    validation_score: float = 0.0
    data_quality_score: float = 0.0
    competitors_found: int = 0
    market_size_found: bool = False
    launches_found: int = 0

    # Error metrics
    error_type: str | None = None
    error_message: str | None = None
    retry_count: int = 0
    circuit_breaker_triggered: bool = False

    # Usage metrics
    queries_executed: int = 0
    urls_fetched: int = 0
    tokens_used: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class PrometheusMetricsCollector:
    """Prometheus metrics collection for market research operations"""

    def __init__(self):
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus not available, metrics collection disabled")
            return

        # Counters
        self.request_counter = Counter(
            'market_research_requests_total',
            'Total market research requests',
            ['operation_type', 'status']
        )

        self.cost_counter = Counter(
            'market_research_cost_total_usd',
            'Total cost in USD for market research',
            ['cost_type']
        )

        self.error_counter = Counter(
            'market_research_errors_total',
            'Total errors in market research',
            ['error_type', 'operation_type']
        )

        self.cache_counter = Counter(
            'market_research_cache_hits_total',
            'Cache hits in market research',
            ['cache_type', 'hit']
        )

        # Histograms
        self.response_time_histogram = Histogram(
            'market_research_response_time_seconds',
            'Response time for market research operations',
            ['operation_type'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        )

        self.validation_score_histogram = Histogram(
            'market_research_validation_score',
            'Validation scores from market research',
            buckets=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        )

        # Gauges
        self.active_requests_gauge = Gauge(
            'market_research_active_requests',
            'Currently active market research requests'
        )

        self.daily_budget_gauge = Gauge(
            'market_research_daily_budget_remaining_usd',
            'Remaining daily budget for market research in USD'
        )

        self.queue_size_gauge = Gauge(
            'market_research_queue_size',
            'Current size of market research request queue'
        )

    def record_request(self, metrics: MarketResearchMetrics, status: str = 'success'):
        """Record a market research request"""
        if not PROMETHEUS_AVAILABLE:
            return

        # Update counters
        self.request_counter.labels(
            operation_type=metrics.operation_type,
            status=status
        ).inc()

        # Update cost counters
        if metrics.total_cost_usd > 0:
            self.cost_counter.labels(cost_type='total').inc(metrics.total_cost_usd)
        if metrics.jina_cost_usd > 0:
            self.cost_counter.labels(cost_type='jina').inc(metrics.jina_cost_usd)
        if metrics.llm_cost_usd > 0:
            self.cost_counter.labels(cost_type='llm').inc(metrics.llm_cost_usd)

        # Update error counter if applicable
        if metrics.error_type:
            self.error_counter.labels(
                error_type=metrics.error_type,
                operation_type=metrics.operation_type
            ).inc()

        # Update cache counter
        self.cache_counter.labels(
            cache_type='jina',
            hit='true' if metrics.cache_hit else 'false'
        ).inc()

        # Update histograms
        self.response_time_histogram.labels(
            operation_type=metrics.operation_type
        ).observe(metrics.response_time_ms / 1000.0)

        self.validation_score_histogram.observe(metrics.validation_score)

    def increment_active_requests(self):
        """Increment active requests gauge"""
        if PROMETHEUS_AVAILABLE:
            self.active_requests_gauge.inc()

    def decrement_active_requests(self):
        """Decrement active requests gauge"""
        if PROMETHEUS_AVAILABLE:
            self.active_requests_gauge.dec()

    def set_daily_budget_remaining(self, amount_usd: float):
        """Set remaining daily budget"""
        if PROMETHEUS_AVAILABLE:
            self.daily_budget_gauge.set(amount_usd)

    def set_queue_size(self, size: int):
        """Set queue size"""
        if PROMETHEUS_AVAILABLE:
            self.queue_size_gauge.set(size)

    def get_metrics(self) -> str:
        """Get Prometheus metrics in text format"""
        if PROMETHEUS_AVAILABLE:
            return generate_latest()
        return ""


class RedisMetricsStore:
    """Redis-based distributed metrics storage"""

    def __init__(self, redis_url: str | None = None):
        self.redis_client = None
        self.enabled = REDIS_AVAILABLE

        if self.enabled:
            try:
                settings = get_settings()
                redis_url = redis_url or getattr(settings, 'redis_url', 'redis://localhost:6379')
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                logger.info("Redis metrics store initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Redis metrics store: {e}")
                self.enabled = False

    async def store_metrics(self, metrics: MarketResearchMetrics) -> bool:
        """Store metrics in Redis"""
        if not self.enabled or not self.redis_client:
            return False

        try:
            # Store in multiple data structures for different query patterns

            # 1. Time-series data with expiration
            time_series_key = f"market_research:metrics:{metrics.timestamp.timestamp()}"
            await self.redis_client.setex(
                time_series_key,
                timedelta(days=7),  # Keep for 7 days
                json.dumps(metrics.to_dict())
            )

            # 2. Daily aggregation
            date_key = f"market_research:daily:{metrics.timestamp.date()}"
            await self.redis_client.hincrby(
                date_key,
                'total_requests',
                1
            )
            await self.redis_client.hincrbyfloat(
                date_key,
                'total_cost_usd',
                metrics.total_cost_usd
            )
            await self.redis_client.expire(date_key, timedelta(days=30))

            # 3. Error tracking
            if metrics.error_type:
                error_key = f"market_research:errors:{metrics.error_type}"
                await self.redis_client.hincrby(error_key, 'count', 1)
                await self.redis_client.expire(error_key, timedelta(days=7))

            # 4. Performance percentiles
            perf_key = f"market_research:performance:{metrics.operation_type}"
            await self.redis_client.lpush(
                perf_key,
                metrics.response_time_ms
            )
            # Keep only last 1000 measurements
            await self.redis_client.ltrim(perf_key, 0, 999)
            await self.redis_client.expire(perf_key, timedelta(days=1))

            return True

        except Exception as e:
            logger.error(f"Failed to store metrics in Redis: {e}")
            return False

    async def get_daily_stats(self, date: datetime | None = None) -> dict[str, Any]:
        """Get daily statistics"""
        if not self.enabled or not self.redis_client:
            return {}

        try:
            if date is None:
                date = datetime.now().date()

            date_key = f"market_research:daily:{date}"
            stats = await self.redis_client.hgetall(date_key)

            return {
                'date': str(date),
                'total_requests': int(stats.get('total_requests', 0)),
                'total_cost_usd': float(stats.get('total_cost_usd', 0.0))
            }

        except Exception as e:
            logger.error(f"Failed to get daily stats from Redis: {e}")
            return {}

    async def get_performance_percentiles(
        self,
        operation_type: str,
        percentiles: list[float] = None
    ) -> dict[str, float]:
        """Get performance percentiles for an operation type"""
        if not self.enabled or not self.redis_client:
            return {}

        if percentiles is None:
            percentiles = [50, 75, 90, 95, 99]

        try:
            perf_key = f"market_research:performance:{operation_type}"
            response_times = await self.redis_client.lrange(perf_key, 0, -1)

            if not response_times:
                return {}

            # Convert to float and sort
            times = sorted(float(rt) for rt in response_times)

            result = {}
            for p in percentiles:
                index = int((p / 100) * len(times))
                if index >= len(times):
                    index = len(times) - 1
                result[f'p{p}'] = times[index]

            return result

        except Exception as e:
            logger.error(f"Failed to get performance percentiles from Redis: {e}")
            return {}

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()


class CircuitBreaker:
    """Circuit breaker for resilient API calls"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        # State
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.half_open_calls = 0

        # Metrics
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0

    def can_execute(self) -> bool:
        """Check if execution is allowed"""
        self.total_calls += 1

        if self.state == 'CLOSED':
            return True
        elif self.state == 'OPEN':
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = 'HALF_OPEN'
                self.half_open_calls = 0
                logger.info("Circuit breaker transitioning to HALF_OPEN")
                return True
            return False
        elif self.state == 'HALF_OPEN':
            if self.half_open_calls >= self.half_open_max_calls:
                return False
            return True

        return False

    def record_success(self):
        """Record a successful call"""
        self.successful_calls += 1

        if self.state == 'HALF_OPEN':
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self.state = 'CLOSED'
                self.failure_count = 0
                logger.info("Circuit breaker transitioning to CLOSED")
        elif self.state == 'CLOSED':
            self.failure_count = 0

    def record_failure(self):
        """Record a failed call"""
        self.failed_calls += 1
        self.last_failure_time = time.time()
        self.failure_count += 1

        if self.state == 'HALF_OPEN' or self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            logger.warning(
                f"Circuit breaker transitioning to OPEN "
                f"(failures: {self.failure_count}/{self.failure_threshold})"
            )

    def get_stats(self) -> dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            'state': self.state,
            'failure_count': self.failure_count,
            'failure_threshold': self.failure_threshold,
            'total_calls': self.total_calls,
            'successful_calls': self.successful_calls,
            'failed_calls': self.failed_calls,
            'success_rate': (
                self.successful_calls / self.total_calls * 100
                if self.total_calls > 0 else 0
            )
        }


class MarketResearchMonitor:
    """
    Comprehensive monitoring for MarketResearchAgent

    Features:
    - Real-time metrics collection
    - Prometheus integration
    - Redis distributed storage
    - Circuit breaker patterns
    - Cost tracking and budget management
    - Performance monitoring
    - Error tracking and alerting
    """

    def __init__(
        self,
        enable_prometheus: bool = True,
        enable_redis: bool = True,
        redis_url: str | None = None,
        daily_budget_usd: float = 500.0
    ):
        self.enable_prometheus = enable_prometheus and PROMETHEUS_AVAILABLE
        self.enable_redis = enable_redis and REDIS_AVAILABLE

        # Initialize components
        self.prometheus = PrometheusMetricsCollector() if self.enable_prometheus else None
        self.redis_store = RedisMetricsStore(redis_url) if self.enable_redis else None

        # Circuit breakers for external services
        self.circuit_breakers = {
            'jina_api': CircuitBreaker(),
            'llm_api': CircuitBreaker(),
            'redis_cache': CircuitBreaker()
        }

        # Budget tracking
        self.daily_budget_usd = daily_budget_usd
        self.daily_cost_usd = 0.0
        self.last_budget_reset = datetime.now().date()

        # Performance tracking
        self.response_times = deque(maxlen=1000)
        self.error_counts = defaultdict(int)
        self.operation_counts = defaultdict(int)

        # Alerts
        self.alert_thresholds = {
            'error_rate_percent': 5.0,
            'response_time_p95_ms': 5000,
            'budget_usage_percent': 80.0,
            'circuit_breaker_open': True
        }

        logger.info(
            f"MarketResearchMonitor initialized - "
            f"Prometheus: {self.enable_prometheus}, Redis: {self.enable_redis}"
        )

    def with_monitoring(
        self,
        operation_type: str,
        track_cost: bool = True,
        track_performance: bool = True
    ):
        """
        Decorator for monitoring function execution

        Args:
            operation_type: Type of operation being monitored
            track_cost: Whether to track cost metrics
            track_performance: Whether to track performance metrics
        """
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not asyncio.iscoroutinefunction(func):
                    return func(*args, **kwargs)

                return await self._monitor_execution(
                    func, operation_type, args, kwargs, track_cost, track_performance
                )

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return self._monitor_execution_sync(
                    func, operation_type, args, kwargs, track_cost, track_performance
                )

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator

    async def _monitor_execution(
        self,
        func: Callable,
        operation_type: str,
        args: tuple,
        kwargs: dict[str, Any],
        track_cost: bool,
        track_performance: bool
    ):
        """Monitor async function execution"""
        start_time = time.time()
        metrics = MarketResearchMetrics(
            timestamp=datetime.now(),
            operation_type=operation_type
        )

        # Increment active requests
        if self.prometheus:
            self.prometheus.increment_active_requests()

        try:
            # Extract relevant info from arguments if available
            if args and hasattr(args[0], '__dict__'):
                # Check if it's a MarketResearchAgent instance
                if hasattr(args[0], 'validation_threshold'):
                    # Extract market research parameters
                    if 'app_concept' in kwargs:
                        metrics.app_concept_id = kwargs['app_concept'][:50]  # Truncate for ID
                    if 'target_market' in kwargs:
                        metrics.target_market = kwargs['target_market']

            # Execute function
            result = await func(*args, **kwargs)

            # Calculate metrics
            if track_performance:
                metrics.response_time_ms = (time.time() - start_time) * 1000
                self.response_times.append(metrics.response_time_ms)

                # Extract validation score if available
                if isinstance(result, dict):
                    metrics.validation_score = result.get('validation_score', 0.0)
                    metrics.data_quality_score = result.get('data_quality_score', 0.0)
                    metrics.competitors_found = len(result.get('competitor_pricing', []))
                    metrics.market_size_found = bool(result.get('market_size'))
                    metrics.launches_found = len(result.get('similar_launches', []))

                    # Cost tracking
                    if track_cost:
                        metrics.jina_cost_usd = result.get('jina_cost', 0.0)
                        metrics.total_cost_usd = metrics.jina_cost_usd

                        # Update daily budget
                        self._update_daily_budget(metrics.total_cost_usd)

            # Record metrics
            await self._record_metrics(metrics, 'success')

            return result

        except Exception as e:
            # Record error metrics
            metrics.response_time_ms = (time.time() - start_time) * 1000
            metrics.error_type = type(e).__name__
            metrics.error_message = str(e)

            await self._record_metrics(metrics, 'error')

            # Re-raise exception
            raise

        finally:
            # Decrement active requests
            if self.prometheus:
                self.prometheus.decrement_active_requests()

    def _monitor_execution_sync(
        self,
        func: Callable,
        operation_type: str,
        args: tuple,
        kwargs: dict[str, Any],
        track_cost: bool,
        track_performance: bool
    ):
        """Monitor sync function execution"""
        start_time = time.time()

        try:
            result = func(*args, **kwargs)

            # Create metrics for sync functions
            metrics = MarketResearchMetrics(
                timestamp=datetime.now(),
                operation_type=operation_type,
                response_time_ms=(time.time() - start_time) * 1000
            )

            # Schedule async recording without blocking
            asyncio.create_task(self._record_metrics(metrics, 'success'))

            return result

        except Exception as e:
            metrics = MarketResearchMetrics(
                timestamp=datetime.now(),
                operation_type=operation_type,
                response_time_ms=(time.time() - start_time) * 1000,
                error_type=type(e).__name__,
                error_message=str(e)
            )

            asyncio.create_task(self._record_metrics(metrics, 'error'))
            raise

    async def _record_metrics(self, metrics: MarketResearchMetrics, status: str):
        """Record metrics to all configured stores"""
        try:
            # Update local counters
            self.operation_counts[metrics.operation_type] += 1
            if metrics.error_type:
                self.error_counts[metrics.error_type] += 1

            # Record to Prometheus
            if self.prometheus:
                self.prometheus.record_request(metrics, status)

            # Store in Redis
            if self.redis_store:
                await self.redis_store.store_metrics(metrics)

            # Check alerts
            await self._check_alerts(metrics)

        except Exception as e:
            logger.error(f"Failed to record metrics: {e}")

    def _update_daily_budget(self, cost_usd: float):
        """Update daily budget tracking"""
        today = datetime.now().date()

        # Reset budget tracking if it's a new day
        if today != self.last_budget_reset:
            self.daily_cost_usd = 0.0
            self.last_budget_reset = today
            logger.info("Daily budget tracking reset")

        self.daily_cost_usd += cost_usd

        # Update Prometheus gauge
        if self.prometheus:
            remaining = max(0, self.daily_budget_usd - self.daily_cost_usd)
            self.prometheus.set_daily_budget_remaining(remaining)

    async def _check_alerts(self, metrics: MarketResearchMetrics):
        """Check if any alerts should be triggered"""
        alerts = []

        # Error rate alert
        total_ops = sum(self.operation_counts.values())
        if total_ops > 0:
            error_rate = (sum(self.error_counts.values()) / total_ops) * 100
            if error_rate > self.alert_thresholds['error_rate_percent']:
                alerts.append({
                    'type': 'error_rate',
                    'message': f"Error rate {error_rate:.1f}% exceeds threshold "
                              f"{self.alert_thresholds['error_rate_percent']}%",
                    'severity': 'warning'
                })

        # Response time alert
        if len(self.response_times) > 20:
            sorted_times = sorted(self.response_times)
            p95_index = int(0.95 * len(sorted_times))
            p95_time = sorted_times[p95_index]

            if p95_time > self.alert_thresholds['response_time_p95_ms']:
                alerts.append({
                    'type': 'response_time',
                    'message': f"P95 response time {p95_time:.0f}ms exceeds threshold "
                              f"{self.alert_thresholds['response_time_p95_ms']}ms",
                    'severity': 'warning'
                })

        # Budget usage alert
        if self.daily_budget_usd > 0:
            budget_usage = (self.daily_cost_usd / self.daily_budget_usd) * 100
            if budget_usage > self.alert_thresholds['budget_usage_percent']:
                alerts.append({
                    'type': 'budget_usage',
                    'message': f"Daily budget usage {budget_usage:.1f}% exceeds threshold "
                              f"{self.alert_thresholds['budget_usage_percent']}%",
                    'severity': 'critical'
                })

        # Circuit breaker alerts
        for name, breaker in self.circuit_breakers.items():
            if breaker.state == 'OPEN':
                alerts.append({
                    'type': 'circuit_breaker',
                    'message': f"Circuit breaker {name} is OPEN",
                    'severity': 'critical'
                })

        # Send alerts (implementation depends on notification system)
        for alert in alerts:
            await self._send_alert(alert)

    async def _send_alert(self, alert: dict[str, Any]):
        """Send alert notification"""
        try:
            logger.warning(
                f"ALERT - {alert['type'].upper()}: {alert['message']}"
            )

            # Here you would integrate with actual alerting systems:
            # - Slack webhook
            # - PagerDuty
            # - Email notifications
            # - SMS alerts

        except Exception as e:
            logger.error(f"Failed to send alert: {e}")

    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get circuit breaker for a service"""
        return self.circuit_breakers.get(service_name, CircuitBreaker())

    async def get_health_status(self) -> dict[str, Any]:
        """Get comprehensive health status"""
        status = {
            'healthy': True,
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }

        # Check Redis
        if self.enable_redis and self.redis_store:
            try:
                await self.redis_store.redis_client.ping()
                status['components']['redis'] = {'healthy': True}
            except Exception as e:
                status['components']['redis'] = {
                    'healthy': False,
                    'error': str(e)
                }
                status['healthy'] = False

        # Check circuit breakers
        for name, breaker in self.circuit_breakers.items():
            status['components'][f'circuit_breaker_{name}'] = {
                'healthy': breaker.state != 'OPEN',
                'state': breaker.state,
                'stats': breaker.get_stats()
            }

        # Budget status
        budget_usage = (self.daily_cost_usd / self.daily_budget_usd) * 100 if self.daily_budget_usd > 0 else 0
        status['budget'] = {
            'daily_limit_usd': self.daily_budget_usd,
            'daily_usage_usd': self.daily_cost_usd,
            'usage_percent': budget_usage
        }

        # Performance summary
        if len(self.response_times) > 0:
            sorted_times = sorted(self.response_times)
            status['performance'] = {
                'requests_total': len(self.response_times),
                'avg_response_time_ms': sum(self.response_times) / len(self.response_times),
                'p95_response_time_ms': sorted_times[int(0.95 * len(sorted_times))],
                'p99_response_time_ms': sorted_times[int(0.99 * len(sorted_times))]
            }

        # Error summary
        total_errors = sum(self.error_counts.values())
        status['errors'] = {
            'total_errors': total_errors,
            'error_types': dict(self.error_counts)
        }

        return status

    async def get_daily_report(self) -> dict[str, Any]:
        """Generate daily performance report"""
        report = {
            'date': datetime.now().date().isoformat(),
            'generated_at': datetime.now().isoformat()
        }

        # Get Redis daily stats
        if self.redis_store:
            report['redis_stats'] = await self.redis_store.get_daily_stats()

        # Performance percentiles by operation
        if self.redis_store:
            report['performance_percentiles'] = {}
            for operation_type in self.operation_counts.keys():
                percentiles = await self.redis_store.get_performance_percentiles(operation_type)
                if percentiles:
                    report['performance_percentiles'][operation_type] = percentiles

        # Circuit breaker stats
        report['circuit_breakers'] = {}
        for name, breaker in self.circuit_breakers.items():
            report['circuit_breakers'][name] = breaker.get_stats()

        # Budget report
        report['budget'] = {
            'limit_usd': self.daily_budget_usd,
            'used_usd': self.daily_cost_usd,
            'remaining_usd': max(0, self.daily_budget_usd - self.daily_cost_usd)
        }

        # Operation summary
        report['operations'] = dict(self.operation_counts)

        return report

    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics"""
        if self.prometheus:
            return self.prometheus.get_metrics()
        return ""

    async def close(self):
        """Close monitoring resources"""
        if self.redis_store:
            await self.redis_store.close()
        logger.info("MarketResearchMonitor closed")


# Global monitor instance
_monitor: MarketResearchMonitor | None = None


def get_monitor() -> MarketResearchMonitor:
    """Get or create global monitor instance"""
    global _monitor
    if _monitor is None:
        settings = get_settings()
        _monitor = MarketResearchMonitor(
            enable_prometheus=getattr(settings, 'prometheus_enabled', False),
            enable_redis=getattr(settings, 'redis_enabled', False),
            redis_url=getattr(settings, 'redis_url', None),
            daily_budget_usd=getattr(settings, 'daily_jina_budget_usd', 500.0)
        )
    return _monitor


async def close_monitor():
    """Close global monitor instance"""
    global _monitor
    if _monitor:
        await _monitor.close()
        _monitor = None
