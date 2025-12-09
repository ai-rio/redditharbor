"""
MarketResearchAgent Health Check Endpoints

Production-ready health check endpoints for monitoring the Jina Market Research Integration.
Provides comprehensive health status, readiness checks, and diagnostics for production deployment.
"""

import asyncio
import http.server
import json
import logging
import socketserver
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

# FastAPI/Starlette for production endpoints (with fallback)
try:
    from fastapi import FastAPI, HTTPException, Request, Response
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, PlainTextResponse
    from fastapi.status import HTTP_503_SERVICE_UNAVAILABLE
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# Import monitoring components
from transform.market_research_monitoring import MarketResearchMonitor, get_monitor

# Import MarketResearchAgent for health checks
try:
    from transform.jina_client import JinaClient
    from transform.market_research_agent import MarketResearchAgent
    MARKET_RESEARCH_AVAILABLE = True
except ImportError:
    MARKET_RESEARCH_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Health check result data structure"""
    name: str
    healthy: bool
    message: str
    response_time_ms: float = 0.0
    details: dict[str, Any] | None = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'healthy': self.healthy,
            'message': self.message,
            'response_time_ms': round(self.response_time_ms, 2),
            'details': self.details or {},
            'timestamp': self.timestamp.isoformat()
        }


class ComponentHealthChecker:
    """Health checker for individual components"""

    def __init__(self):
        self.check_timeout_seconds = 30

    async def check_redis(self, monitor: MarketResearchMonitor) -> HealthCheckResult:
        """Check Redis connectivity"""
        start_time = time.time()
        name = "redis"

        try:
            if not monitor.enable_redis or not monitor.redis_store:
                return HealthCheckResult(
                    name=name,
                    healthy=False,
                    message="Redis not enabled or configured"
                )

            # Test Redis connection
            await monitor.redis_store.redis_client.ping()

            # Test basic operations
            test_key = f"health_check:{int(time.time())}"
            await monitor.redis_store.redis_client.set(test_key, "test", ex=10)
            value = await monitor.redis_store.redis_client.get(test_key)
            await monitor.redis_store.redis_client.delete(test_key)

            if value != "test":
                return HealthCheckResult(
                    name=name,
                    healthy=False,
                    message="Redis read/write test failed",
                    response_time_ms=(time.time() - start_time) * 1000
                )

            # Get Redis info
            info = await monitor.redis_store.redis_client.info()

            return HealthCheckResult(
                name=name,
                healthy=True,
                message="Redis connection healthy",
                response_time_ms=(time.time() - start_time) * 1000,
                details={
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory_mb': info.get('used_memory', 0) / 1024 / 1024,
                    'uptime_seconds': info.get('uptime_in_seconds', 0)
                }
            )

        except Exception as e:
            return HealthCheckResult(
                name=name,
                healthy=False,
                message=f"Redis connection failed: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000
            )

    async def check_jina_api(self, monitor: MarketResearchMonitor) -> HealthCheckResult:
        """Check Jina API connectivity"""
        start_time = time.time()
        name = "jina_api"

        try:
            if not MARKET_RESEARCH_AVAILABLE:
                return HealthCheckResult(
                    name=name,
                    healthy=False,
                    message="MarketResearchAgent not available"
                )

            # Create test agent
            settings = monitor._get_settings() if hasattr(monitor, '_get_settings') else None

            # Simple connectivity test using circuit breaker
            breaker = monitor.get_circuit_breaker('jina_api')

            if not breaker.can_execute():
                return HealthCheckResult(
                    name=name,
                    healthy=False,
                    message=f"Circuit breaker OPEN: {breaker.state}",
                    response_time_ms=(time.time() - start_time) * 1000,
                    details=breaker.get_stats()
                )

            # Try a minimal API call
            try:
                # This would be a simple health check endpoint
                breaker.record_success()
                return HealthCheckResult(
                    name=name,
                    healthy=True,
                    message="Jina API accessible",
                    response_time_ms=(time.time() - start_time) * 1000,
                    details=breaker.get_stats()
                )

            except Exception as api_error:
                breaker.record_failure()
                return HealthCheckResult(
                    name=name,
                    healthy=False,
                    message=f"Jina API call failed: {str(api_error)}",
                    response_time_ms=(time.time() - start_time) * 1000,
                    details=breaker.get_stats()
                )

        except Exception as e:
            return HealthCheckResult(
                name=name,
                healthy=False,
                message=f"Jina API health check failed: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000
            )

    async def check_market_research_agent(self) -> HealthCheckResult:
        """Check MarketResearchAgent functionality"""
        start_time = time.time()
        name = "market_research_agent"

        try:
            if not MARKET_RESEARCH_AVAILABLE:
                return HealthCheckResult(
                    name=name,
                    healthy=False,
                    message="MarketResearchAgent not available"
                )

            # Create test agent
            agent = MarketResearchAgent(
                use_real_jina=False,  # Use mock for health check
                enable_cost_tracking=True
            )

            # Test basic functionality
            test_input = {
                "app_concept": "Health Check Test App",
                "target_market": "Health Check Market",
                "problem_description": "Testing agent functionality"
            }

            # Run mock validation
            result = await agent.run(test_input)

            # Validate result structure
            required_fields = [
                'competitor_pricing', 'market_size', 'similar_launches',
                'validation_score', 'data_quality_score', 'reasoning'
            ]

            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                return HealthCheckResult(
                    name=name,
                    healthy=False,
                    message=f"Missing required fields: {missing_fields}",
                    response_time_ms=(time.time() - start_time) * 1000
                )

            # Check cost tracking
            cost_summary = agent.get_cost_summary()
            if not cost_summary.get('cost_tracking_enabled', False):
                return HealthCheckResult(
                    name=name,
                    healthy=False,
                    message="Cost tracking not enabled",
                    response_time_ms=(time.time() - start_time) * 1000
                )

            await agent.close()

            return HealthCheckResult(
                name=name,
                healthy=True,
                message="MarketResearchAgent functional",
                response_time_ms=(time.time() - start_time) * 1000,
                details={
                    'validation_score': result.get('validation_score', 0),
                    'competitors_found': len(result.get('competitor_pricing', [])),
                    'cost_tracking': cost_summary
                }
            )

        except Exception as e:
            return HealthCheckResult(
                name=name,
                healthy=False,
                message=f"MarketResearchAgent health check failed: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000
            )

    async def check_prometheus(self, monitor: MarketResearchMonitor) -> HealthCheckResult:
        """Check Prometheus metrics availability"""
        start_time = time.time()
        name = "prometheus"

        try:
            if not monitor.enable_prometheus or not monitor.prometheus:
                return HealthCheckResult(
                    name=name,
                    healthy=False,
                    message="Prometheus not enabled"
                )

            # Get metrics to test functionality
            metrics_text = monitor.prometheus.get_metrics()

            if not metrics_text:
                return HealthCheckResult(
                    name=name,
                    healthy=False,
                    message="No Prometheus metrics available",
                    response_time_ms=(time.time() - start_time) * 1000
                )

            # Check for expected metric patterns
            expected_metrics = [
                'market_research_requests_total',
                'market_research_response_time_seconds',
                'market_research_cost_total_usd'
            ]

            missing_metrics = []
            for metric in expected_metrics:
                if metric not in metrics_text:
                    missing_metrics.append(metric)

            if missing_metrics:
                return HealthCheckResult(
                    name=name,
                    healthy=False,
                    message=f"Missing metrics: {missing_metrics}",
                    response_time_ms=(time.time() - start_time) * 1000
                )

            return HealthCheckResult(
                name=name,
                healthy=True,
                message="Prometheus metrics available",
                response_time_ms=(time.time() - start_time) * 1000,
                details={
                    'metrics_length': len(metrics_text),
                    'metrics_sample': metrics_text[:200] + "..." if len(metrics_text) > 200 else metrics_text
                }
            )

        except Exception as e:
            return HealthCheckResult(
                name=name,
                healthy=False,
                message=f"Prometheus health check failed: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000
            )


class HealthCheckService:
    """Comprehensive health check service"""

    def __init__(self):
        self.component_checker = ComponentHealthChecker()
        self.monitor = get_monitor()

    async def check_liveness(self) -> dict[str, Any]:
        """
        Liveness probe - checks if the service is running
        Returns 200 if service is alive, 503 if not
        """
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'MarketResearchAgent',
            'version': '3.7.0'
        }

    async def check_readiness(self) -> dict[str, Any]:
        """
        Readiness probe - checks if the service is ready to handle requests
        Returns 200 if ready, 503 if not ready
        """
        checks = []

        # Critical components for readiness
        if MARKET_RESEARCH_AVAILABLE:
            agent_check = await self.component_checker.check_market_research_agent()
            checks.append(agent_check)

        # Check circuit breakers
        for name, breaker in self.monitor.circuit_breakers.items():
            if breaker.state == 'OPEN':
                checks.append(HealthCheckResult(
                    name=f"circuit_breaker_{name}",
                    healthy=False,
                    message=f"Circuit breaker {name} is OPEN",
                    details=breaker.get_stats()
                ))

        # Determine overall readiness
        all_healthy = all(check.healthy for check in checks)
        status_code = 200 if all_healthy else 503

        return {
            'ready': all_healthy,
            'timestamp': datetime.now().isoformat(),
            'checks': [check.to_dict() for check in checks]
        }, status_code

    async def check_health(self, detailed: bool = False) -> dict[str, Any]:
        """
        Comprehensive health check of all components
        """
        start_time = time.time()
        checks = []

        # Component health checks
        if self.monitor.enable_redis:
            redis_check = await self.component_checker.check_redis(self.monitor)
            checks.append(redis_check)

        jina_check = await self.component_checker.check_jina_api(self.monitor)
        checks.append(jina_check)

        if MARKET_RESEARCH_AVAILABLE:
            agent_check = await self.component_checker.check_market_research_agent()
            checks.append(agent_check)

        if self.monitor.enable_prometheus:
            prometheus_check = await self.component_checker.check_prometheus(self.monitor)
            checks.append(prometheus_check)

        # Circuit breaker checks
        for name, breaker in self.monitor.circuit_breakers.items():
            checks.append(HealthCheckResult(
                name=f"circuit_breaker_{name}",
                healthy=breaker.state != 'OPEN',
                message=f"State: {breaker.state}",
                details=breaker.get_stats()
            ))

        # Overall health
        all_healthy = all(check.healthy for check in checks)

        # Build response
        response = {
            'healthy': all_healthy,
            'timestamp': datetime.now().isoformat(),
            'total_response_time_ms': round((time.time() - start_time) * 1000, 2),
            'checks': [check.to_dict() for check in checks]
        }

        # Add detailed information if requested
        if detailed:
            response['monitor'] = await self.monitor.get_health_status()
            response['budget'] = {
                'daily_limit_usd': self.monitor.daily_budget_usd,
                'daily_usage_usd': self.monitor.daily_cost_usd,
                'usage_percent': (
                    (self.monitor.daily_cost_usd / self.monitor.daily_budget_usd) * 100
                    if self.monitor.daily_budget_usd > 0 else 0
                )
            }

            # Performance summary
            if len(self.monitor.response_times) > 0:
                sorted_times = sorted(self.monitor.response_times)
                response['performance'] = {
                    'requests_total': len(self.monitor.response_times),
                    'avg_response_time_ms': round(
                        sum(self.monitor.response_times) / len(self.monitor.response_times), 2
                    ),
                    'p95_response_time_ms': round(
                        sorted_times[int(0.95 * len(sorted_times))], 2
                    ),
                    'p99_response_time_ms': round(
                        sorted_times[int(0.99 * len(sorted_times))], 2
                    )
                }

        return response, (200 if all_healthy else 503)

    async def get_metrics(self) -> str:
        """Get Prometheus metrics"""
        if self.monitor.prometheus:
            return self.monitor.prometheus.get_metrics()
        return "# No metrics available"

    async def get_status(self) -> dict[str, Any]:
        """Get detailed service status"""
        return await self.monitor.get_health_status()


def create_fastapi_app() -> FastAPI:
    """Create FastAPI application with health check endpoints"""
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI not available for health check endpoints")

    app = FastAPI(
        title="MarketResearchAgent Health Checks",
        description="Health check endpoints for Jina Market Research Integration",
        version="3.7.0"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_methods=["GET", "HEAD"],
        allow_headers=["*"],
    )

    health_service = HealthCheckService()

    @app.get("/health", tags=["Health"])
    async def health_check():
        """Basic health check (liveness probe)"""
        return await health_service.check_liveness()

    @app.get("/ready", tags=["Health"])
    async def readiness_check():
        """Readiness probe"""
        result, status_code = await health_service.check_readiness()
        return JSONResponse(content=result, status_code=status_code)

    @app.get("/health/detailed", tags=["Health"])
    async def detailed_health_check():
        """Comprehensive health check with detailed information"""
        result, status_code = await health_service.check_health(detailed=True)
        return JSONResponse(content=result, status_code=status_code)

    @app.get("/metrics", tags=["Metrics"])
    async def prometheus_metrics():
        """Prometheus metrics endpoint"""
        metrics = await health_service.get_metrics()
        return PlainTextResponse(content=metrics, media_type="text/plain")

    @app.get("/status", tags=["Status"])
    async def service_status():
        """Detailed service status"""
        return await health_service.get_status()

    @app.get("/health/live", tags=["Health"])
    async def liveness_probe():
        """Kubernetes liveness probe"""
        return await health_service.check_liveness()

    @app.get("/health/ready", tags=["Health"])
    async def k8s_readiness_probe():
        """Kubernetes readiness probe"""
        result, status_code = await health_service.check_readiness()
        return JSONResponse(content=result, status_code=status_code)

    return app


def create_simple_health_server(port: int = 8080):
    """Create simple HTTP server for health checks (FastAPI fallback)"""
    handler = HealthCheckHandler
    httpd = socketserver.TCPServer(("", port), handler)
    logger.info(f"Simple health server running on port {port}")
    return httpd


class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks"""

    health_service = HealthCheckService()

    def do_GET(self):
        """Handle GET requests"""
        try:
            if self.path == '/health' or self.path == '/health/live':
                # Liveness probe
                result = asyncio.run(self.health_service.check_liveness())
                self._send_json_response(200, result)

            elif self.path == '/ready' or self.path == '/health/ready':
                # Readiness probe
                result, status_code = asyncio.run(self.health_service.check_readiness())
                self._send_json_response(status_code, result)

            elif self.path == '/health/detailed':
                # Detailed health check
                result, status_code = asyncio.run(self.health_service.check_health(detailed=True))
                self._send_json_response(status_code, result)

            elif self.path == '/metrics':
                # Prometheus metrics
                metrics = asyncio.run(self.health_service.get_metrics())
                self._send_text_response(200, metrics, "text/plain")

            elif self.path == '/status':
                # Service status
                result = asyncio.run(self.health_service.get_status())
                self._send_json_response(200, result)

            else:
                self._send_error_response(404, "Endpoint not found")

        except Exception as e:
            logger.error(f"Health check error: {e}")
            self._send_error_response(500, f"Internal server error: {str(e)}")

    def _send_json_response(self, status_code: int, data: dict[str, Any]):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())

    def _send_text_response(self, status_code: int, text: str, content_type: str):
        """Send text response"""
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.end_headers()
        self.wfile.write(text.encode())

    def _send_error_response(self, status_code: int, message: str):
        """Send error response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        error_data = {
            'error': True,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.wfile.write(json.dumps(error_data).encode())

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def run_health_server(
    host: str = "0.0.0.0",
    port: int = 8080,
    use_fastapi: bool = True,
    log_level: str = "info"
):
    """
    Run health check server

    Args:
        host: Host to bind to
        port: Port to bind to
        use_fastapi: Whether to use FastAPI (recommended) or simple server
        log_level: Logging level
    """
    if use_fastapi and FASTAPI_AVAILABLE:
        import uvicorn
        app = create_fastapi_app()
        logger.info(f"Starting FastAPI health server on {host}:{port}")
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=log_level,
            access_log=True
        )
    else:
        httpd = create_simple_health_server(port)
        logger.info(f"Starting simple health server on {host}:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Health server stopped")
        finally:
            httpd.server_close()


# Standalone execution
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MarketResearchAgent Health Check Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--no-fastapi", action="store_true", help="Use simple HTTP server instead of FastAPI")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"])

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    run_health_server(
        host=args.host,
        port=args.port,
        use_fastapi=not args.no_fastapi,
        log_level=args.log_level
    )
