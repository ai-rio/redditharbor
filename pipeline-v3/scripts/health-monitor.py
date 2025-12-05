#!/usr/bin/env python3
"""
RedditHarbor Phase 5 Health Monitor
====================================

Comprehensive health monitoring script for RedditHarbor Phase 5 production deployment.
Monitors application health, external APIs, database connectivity, and system resources.
"""

import asyncio
import aiohttp
import asyncpg
import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class Severity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthCheck:
    """Individual health check result"""
    name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    duration_ms: float
    details: Optional[Dict] = None


@dataclass
class HealthReport:
    """Comprehensive health report"""
    overall_status: HealthStatus
    timestamp: datetime
    checks: List[HealthCheck]
    environment: str
    version: str
    node_name: str


class HealthMonitor:
    """Main health monitoring class"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._load_config()
        self.session: Optional[aiohttp.ClientSession] = None
        self.db_pool: Optional[asyncpg.Pool] = None
        self.start_time = datetime.now()
        self.check_history: List[HealthReport] = []

    def _load_config(self) -> Dict:
        """Load configuration from environment and defaults"""
        return {
            "database_url": os.getenv("DATABASE_URL"),
            "cohere_api_key": os.getenv("COHERE_API_KEY"),
            "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
            "agentops_api_key": os.getenv("AGENTOPS_API_KEY"),
            "environment": os.getenv("ENVIRONMENT", "production"),
            "version": os.getenv("APP_VERSION", "unknown"),
            "node_name": os.getenv("NODE_NAME", os.uname().nodename),
            "health_endpoint": os.getenv("HEALTH_ENDPOINT", "http://localhost:8000/health"),
            "metrics_endpoint": os.getenv("METRICS_ENDPOINT", "http://localhost:8000/metrics"),
            "detailed_endpoint": os.getenv("DETAILED_ENDPOINT", "http://localhost:8000/health/detailed"),
            "timeout": int(os.getenv("HEALTH_TIMEOUT", "30")),
            "thresholds": {
                "cpu_warning": float(os.getenv("CPU_WARNING_THRESHOLD", "80")),
                "cpu_critical": float(os.getenv("CPU_CRITICAL_THRESHOLD", "90")),
                "memory_warning": float(os.getenv("MEMORY_WARNING_THRESHOLD", "80")),
                "memory_critical": float(os.getenv("MEMORY_CRITICAL_THRESHOLD", "90")),
                "disk_warning": float(os.getenv("DISK_WARNING_THRESHOLD", "85")),
                "disk_critical": float(os.getenv("DISK_CRITICAL_THRESHOLD", "95")),
                "latency_warning": float(os.getenv("LATENCY_WARNING_THRESHOLD", "5000")),
                "latency_critical": float(os.getenv("LATENCY_CRITICAL_THRESHOLD", "10000")),
                "error_rate_warning": float(os.getenv("ERROR_RATE_WARNING", "0.02")),
                "error_rate_critical": float(os.getenv("ERROR_RATE_CRITICAL", "0.05"))
            }
        }

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config["timeout"])
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        if self.db_pool:
            await self.db_pool.close()

    async def check_application_health(self) -> HealthCheck:
        """Check application health endpoint"""
        start_time = time.time()
        name = "application_health"

        try:
            async with self.session.get(self.config["health_endpoint"]) as response:
                duration_ms = (time.time() - start_time) * 1000

                if response.status == 200:
                    data = await response.json()
                    return HealthCheck(
                        name=name,
                        status=HealthStatus.HEALTHY,
                        message="Application is healthy",
                        timestamp=datetime.now(),
                        duration_ms=duration_ms,
                        details=data
                    )
                else:
                    return HealthCheck(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Health check failed with HTTP {response.status}",
                        timestamp=datetime.now(),
                        duration_ms=duration_ms
                    )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check error: {str(e)}",
                timestamp=datetime.now(),
                duration_ms=duration_ms
            )

    async def check_detailed_health(self) -> HealthCheck:
        """Check detailed application health"""
        start_time = time.time()
        name = "detailed_health"

        try:
            async with self.session.get(self.config["detailed_endpoint"]) as response:
                duration_ms = (time.time() - start_time) * 1000

                if response.status == 200:
                    data = await response.json()
                    overall_status = data.get("status", "unknown")
                    issues = data.get("issues", [])

                    if overall_status == "healthy":
                        status = HealthStatus.HEALTHY
                        message = "All components healthy"
                    elif overall_status == "degraded":
                        status = HealthStatus.DEGRADED
                        message = f"Degraded: {', '.join(issues)}"
                    else:
                        status = HealthStatus.UNHEALTHY
                        message = f"Unhealthy: {', '.join(issues)}"

                    return HealthCheck(
                        name=name,
                        status=status,
                        message=message,
                        timestamp=datetime.now(),
                        duration_ms=duration_ms,
                        details=data
                    )
                else:
                    return HealthCheck(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Detailed health check failed: HTTP {response.status}",
                        timestamp=datetime.now(),
                        duration_ms=duration_ms
                    )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Detailed health check error: {str(e)}",
                timestamp=datetime.now(),
                duration_ms=duration_ms
            )

    async def check_database_health(self) -> HealthCheck:
        """Check database connectivity and performance"""
        start_time = time.time()
        name = "database_health"

        try:
            # Connect to database
            conn = await asyncpg.connect(self.config["database_url"])
            connect_time = (time.time() - start_time) * 1000

            # Test basic query
            query_start = time.time()
            result = await conn.fetchval("SELECT 1")
            query_time = (time.time() - query_start) * 1000

            # Get connection stats
            stats = await conn.fetchrow("""
                SELECT
                    count(*) as active_connections,
                    count(*) FILTER (WHERE state = 'active') as active_queries,
                    max(now() - state_change) as longest_idle
                FROM pg_stat_activity
                WHERE datname = current_database()
            """)

            await conn.close()

            # Check thresholds
            total_time = (time.time() - start_time) * 1000
            if connect_time > 1000 or query_time > 1000:
                status = HealthStatus.DEGRADED
                message = f"Database slow: connect={connect_time:.0f}ms, query={query_time:.0f}ms"
            else:
                status = HealthStatus.HEALTHY
                message = "Database is healthy"

            return HealthCheck(
                name=name,
                status=status,
                message=message,
                timestamp=datetime.now(),
                duration_ms=total_time,
                details={
                    "connect_time_ms": connect_time,
                    "query_time_ms": query_time,
                    "active_connections": stats["active_connections"],
                    "active_queries": stats["active_queries"],
                    "longest_idle_seconds": stats["longest_idle"].total_seconds()
                }
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Database health check failed: {str(e)}",
                timestamp=datetime.now(),
                duration_ms=duration_ms
            )

    async def check_external_apis(self) -> List[HealthCheck]:
        """Check external API health"""
        checks = []

        # Check Cohere API
        if self.config["cohere_api_key"]:
            checks.append(await self._check_cohere_api())
        else:
            checks.append(HealthCheck(
                name="cohere_api",
                status=HealthStatus.DEGRADED,
                message="Cohere API key not configured",
                timestamp=datetime.now(),
                duration_ms=0
            ))

        # Check OpenRouter API
        if self.config["openrouter_api_key"]:
            checks.append(await self._check_openrouter_api())
        else:
            checks.append(HealthCheck(
                name="openrouter_api",
                status=HealthStatus.DEGRADED,
                message="OpenRouter API key not configured",
                timestamp=datetime.now(),
                duration_ms=0
            ))

        # Check AgentOps API
        if self.config["agentops_api_key"]:
            checks.append(await self._check_agentops_api())
        else:
            checks.append(HealthCheck(
                name="agentops_api",
                status=HealthStatus.DEGRADED,
                message="AgentOps API key not configured",
                timestamp=datetime.now(),
                duration_ms=0
            ))

        return checks

    async def _check_cohere_api(self) -> HealthCheck:
        """Check Cohere API health"""
        start_time = time.time()
        name = "cohere_api"

        try:
            headers = {"Authorization": f"Bearer {self.config['cohere_api_key']}"}
            data = {
                "texts": ["health check"],
                "model": "embed-english-v3.0",
                "input_type": "search_document"
            }

            async with self.session.post(
                "https://api.cohere.ai/v1/embed",
                headers=headers,
                json=data
            ) as response:
                duration_ms = (time.time() - start_time) * 1000

                if response.status == 200:
                    rate_limit = response.headers.get("X-RateLimit-Remaining", "unknown")
                    return HealthCheck(
                        name=name,
                        status=HealthStatus.HEALTHY,
                        message=f"Cohere API healthy",
                        timestamp=datetime.now(),
                        duration_ms=duration_ms,
                        details={"rate_limit_remaining": rate_limit}
                    )
                elif response.status == 429:
                    return HealthCheck(
                        name=name,
                        status=HealthStatus.DEGRADED,
                        message="Cohere API rate limited",
                        timestamp=datetime.now(),
                        duration_ms=duration_ms
                    )
                else:
                    return HealthCheck(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Cohere API error: HTTP {response.status}",
                        timestamp=datetime.now(),
                        duration_ms=duration_ms
                    )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Cohere API check failed: {str(e)}",
                timestamp=datetime.now(),
                duration_ms=duration_ms
            )

    async def _check_openrouter_api(self) -> HealthCheck:
        """Check OpenRouter API health"""
        start_time = time.time()
        name = "openrouter_api"

        try:
            headers = {
                "Authorization": f"Bearer {self.config['openrouter_api_key']}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "anthropic/claude-haiku",
                "messages": [{"role": "user", "content": "hi"}]
            }

            async with self.session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data
            ) as response:
                duration_ms = (time.time() - start_time) * 1000

                if response.status == 200:
                    return HealthCheck(
                        name=name,
                        status=HealthStatus.HEALTHY,
                        message="OpenRouter API healthy",
                        timestamp=datetime.now(),
                        duration_ms=duration_ms
                    )
                else:
                    return HealthCheck(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"OpenRouter API error: HTTP {response.status}",
                        timestamp=datetime.now(),
                        duration_ms=duration_ms
                    )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"OpenRouter API check failed: {str(e)}",
                timestamp=datetime.now(),
                duration_ms=duration_ms
            )

    async def _check_agentops_api(self) -> HealthCheck:
        """Check AgentOps API health"""
        start_time = time.time()
        name = "agentops_api"

        try:
            headers = {
                "X-Agentops-Api-Key": self.config['agentops_api_key'],
                "Content-Type": "application/json"
            }
            data = {"type": "ping"}

            async with self.session.post(
                "https://api.agentops.ai/v2/server",
                headers=headers,
                json=data
            ) as response:
                duration_ms = (time.time() - start_time) * 1000

                if response.status == 200:
                    return HealthCheck(
                        name=name,
                        status=HealthStatus.HEALTHY,
                        message="AgentOps API healthy",
                        timestamp=datetime.now(),
                        duration_ms=duration_ms
                    )
                else:
                    return HealthCheck(
                        name=name,
                        status=HealthStatus.DEGRADED,
                        message=f"AgentOps API unavailable (HTTP {response.status}) - will use local tracking",
                        timestamp=datetime.now(),
                        duration_ms=duration_ms
                    )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheck(
                name=name,
                status=HealthStatus.DEGRADED,
                message=f"AgentOps API check failed: {str(e)} - will use local tracking",
                timestamp=datetime.now(),
                duration_ms=duration_ms
            )

    async def check_system_resources(self) -> List[HealthCheck]:
        """Check system resource usage"""
        checks = []

        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_threshold = self.config["thresholds"]
        if cpu_percent > cpu_threshold["cpu_critical"]:
            status = HealthStatus.UNHEALTHY
            message = f"Critical CPU usage: {cpu_percent:.1f}%"
        elif cpu_percent > cpu_threshold["cpu_warning"]:
            status = HealthStatus.DEGRADED
            message = f"High CPU usage: {cpu_percent:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"CPU usage normal: {cpu_percent:.1f}%"

        checks.append(HealthCheck(
            name="cpu_usage",
            status=status,
            message=message,
            timestamp=datetime.now(),
            duration_ms=0,
            details={"cpu_percent": cpu_percent}
        ))

        # Memory usage
        memory = psutil.virtual_memory()
        if memory.percent > cpu_threshold["memory_critical"]:
            status = HealthStatus.UNHEALTHY
            message = f"Critical memory usage: {memory.percent:.1f}%"
        elif memory.percent > cpu_threshold["memory_warning"]:
            status = HealthStatus.DEGRADED
            message = f"High memory usage: {memory.percent:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"Memory usage normal: {memory.percent:.1f}%"

        checks.append(HealthCheck(
            name="memory_usage",
            status=status,
            message=message,
            timestamp=datetime.now(),
            duration_ms=0,
            details={
                "memory_percent": memory.percent,
                "memory_used_gb": memory.used / (1024**3),
                "memory_total_gb": memory.total / (1024**3)
            }
        ))

        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        if disk_percent > cpu_threshold["disk_critical"]:
            status = HealthStatus.UNHEALTHY
            message = f"Critical disk usage: {disk_percent:.1f}%"
        elif disk_percent > cpu_threshold["disk_warning"]:
            status = HealthStatus.DEGRADED
            message = f"High disk usage: {disk_percent:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"Disk usage normal: {disk_percent:.1f}%"

        checks.append(HealthCheck(
            name="disk_usage",
            status=status,
            message=message,
            timestamp=datetime.now(),
            duration_ms=0,
            details={
                "disk_percent": disk_percent,
                "disk_used_gb": disk.used / (1024**3),
                "disk_total_gb": disk.total / (1024**3)
            }
        ))

        # Load average (Linux only)
        if hasattr(os, 'getloadavg'):
            load1, load5, load15 = os.getloadavg()
            cpu_count = psutil.cpu_count()
            load_percent = (load1 / cpu_count) * 100

            if load_percent > cpu_threshold["cpu_critical"]:
                status = HealthStatus.UNHEALTHY
                message = f"Critical load average: {load1:.2f}"
            elif load_percent > cpu_threshold["cpu_warning"]:
                status = HealthStatus.DEGRADED
                message = f"High load average: {load1:.2f}"
            else:
                status = HealthStatus.HEALTHY
                message = f"Load average normal: {load1:.2f}"

            checks.append(HealthCheck(
                name="load_average",
                status=status,
                message=message,
                timestamp=datetime.now(),
                duration_ms=0,
                details={
                    "load_1m": load1,
                    "load_5m": load5,
                    "load_15m": load15,
                    "cpu_count": cpu_count
                }
            ))

        return checks

    async def check_application_metrics(self) -> HealthCheck:
        """Check application metrics from Prometheus endpoint"""
        start_time = time.time()
        name = "application_metrics"

        try:
            async with self.session.get(self.config["metrics_endpoint"]) as response:
                if response.status == 200:
                    metrics_text = await response.text()
                    duration_ms = (time.time() - start_time) * 1000

                    # Parse some key metrics
                    metrics = self._parse_metrics(metrics_text)

                    # Check error rate
                    error_rate = metrics.get("error_rate", 0)
                    if error_rate > self.config["thresholds"]["error_rate_critical"]:
                        status = HealthStatus.UNHEALTHY
                        message = f"Critical error rate: {error_rate:.2%}"
                    elif error_rate > self.config["thresholds"]["error_rate_warning"]:
                        status = HealthStatus.DEGRADED
                        message = f"High error rate: {error_rate:.2%}"
                    else:
                        status = HealthStatus.HEALTHY
                        message = f"Error rate normal: {error_rate:.2%}"

                    return HealthCheck(
                        name=name,
                        status=status,
                        message=message,
                        timestamp=datetime.now(),
                        duration_ms=duration_ms,
                        details=metrics
                    )
                else:
                    return HealthCheck(
                        name=name,
                        status=HealthStatus.DEGRADED,
                        message=f"Metrics endpoint unavailable: HTTP {response.status}",
                        timestamp=datetime.now(),
                        duration_ms=(time.time() - start_time) * 1000
                    )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheck(
                name=name,
                status=HealthStatus.DEGRADED,
                message=f"Metrics check failed: {str(e)}",
                timestamp=datetime.now(),
                duration_ms=duration_ms
            )

    def _parse_metrics(self, metrics_text: str) -> Dict[str, float]:
        """Parse key metrics from Prometheus text format"""
        metrics = {}

        # Parse error rate
        # This is a simplified example - in practice, you'd want more robust parsing
        for line in metrics_text.split('\n'):
            if 'reddit_harbor_errors_total' in line and line.startswith('reddit_harbor_errors_total'):
                # Extract value from metric line
                parts = line.split(' ')
                if len(parts) >= 2:
                    try:
                        metrics['errors_total'] = float(parts[1])
                    except ValueError:
                        pass

            if 'reddit_harbor_submissions_total' in line and line.startswith('reddit_harbor_submissions_total'):
                parts = line.split(' ')
                if len(parts) >= 2:
                    try:
                        metrics['submissions_total'] = float(parts[1])
                    except ValueError:
                        pass

        # Calculate error rate if we have both metrics
        if 'errors_total' in metrics and 'submissions_total' in metrics:
            if metrics['submissions_total'] > 0:
                metrics['error_rate'] = metrics['errors_total'] / metrics['submissions_total']
            else:
                metrics['error_rate'] = 0

        return metrics

    async def run_health_checks(self) -> HealthReport:
        """Run all health checks and generate report"""
        logger.info("Starting comprehensive health checks...")

        # Run all checks concurrently
        app_health = asyncio.create_task(self.check_application_health())
        detailed_health = asyncio.create_task(self.check_detailed_health())
        db_health = asyncio.create_task(self.check_database_health())
        api_health = asyncio.create_task(self.check_external_apis())
        resource_health = asyncio.create_task(self.check_system_resources())
        metrics_health = asyncio.create_task(self.check_application_metrics())

        # Wait for all checks
        checks = [await app_health, await detailed_health, await db_health]
        checks.extend(await api_health)
        checks.extend(await resource_health)
        checks.append(await metrics_health)

        # Determine overall status
        if any(c.status == HealthStatus.UNHEALTHY for c in checks):
            overall_status = HealthStatus.UNHEALTHY
        elif any(c.status == HealthStatus.DEGRADED for c in checks):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        # Create report
        report = HealthReport(
            overall_status=overall_status,
            timestamp=datetime.now(),
            checks=checks,
            environment=self.config["environment"],
            version=self.config["version"],
            node_name=self.config["node_name"]
        )

        # Store in history
        self.check_history.append(report)
        if len(self.check_history) > 100:  # Keep last 100 reports
            self.check_history.pop(0)

        logger.info(f"Health checks completed: {overall_status.value}")
        return report

    def print_report(self, report: HealthReport, output_format: str = "table"):
        """Print health report in specified format"""
        if output_format == "json":
            print(json.dumps(self._serialize_report(report), indent=2))
        else:
            self._print_table_report(report)

    def _serialize_report(self, report: HealthReport) -> Dict:
        """Serialize report to JSON-serializable dict"""
        return {
            "overall_status": report.overall_status.value,
            "timestamp": report.timestamp.isoformat(),
            "environment": report.environment,
            "version": report.version,
            "node_name": report.node_name,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "checks": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "message": c.message,
                    "timestamp": c.timestamp.isoformat(),
                    "duration_ms": c.duration_ms,
                    "details": c.details
                }
                for c in report.checks
            ]
        }

    def _print_table_report(self, report: HealthReport):
        """Print health report in table format"""
        # Header
        print(f"\n{'='*80}")
        print(f"RedditHarbor Phase 5 Health Report")
        print(f"{'='*80}")
        print(f"Timestamp:    {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Environment:  {report.environment}")
        print(f"Version:      {report.version}")
        print(f"Node:         {report.node_name}")
        print(f"Uptime:       {(datetime.now() - self.start_time).total_seconds():.0f}s")
        print(f"Overall:      {report.overall_status.value.upper()}")
        print(f"\n{'Health Checks':80}")
        print(f"{'-'*80}")

        # Format status with colors
        for check in report.checks:
            status_symbol = {
                HealthStatus.HEALTHY: "✅",
                HealthStatus.DEGRADED: "⚠️",
                HealthStatus.UNHEALTHY: "❌",
                HealthStatus.UNKNOWN: "❓"
            }.get(check.status, "❓")

            print(f"{status_symbol} {check.name:25} {check.status.value:12} ({check.duration_ms:6.0f}ms) {check.message}")

            # Print details if available
            if check.details:
                for key, value in check.details.items():
                    print(f"   • {key}: {value}")

        print(f"\n{'='*80}")

    async def run_continuous_monitoring(self, interval: int = 60, alert_file: Optional[str] = None):
        """Run continuous monitoring with optional alert file"""
        logger.info(f"Starting continuous monitoring (interval: {interval}s)")

        try:
            while True:
                report = await self.run_health_checks()

                # Check for alerts
                alerts = self._generate_alerts(report)
                if alerts:
                    await self._handle_alerts(alerts, alert_file)

                # Print summary
                if report.overall_status != HealthStatus.HEALTHY:
                    logger.warning(f"Health check result: {report.overall_status.value}")
                else:
                    logger.info("Health check passed")

                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            raise

    def _generate_alerts(self, report: HealthReport) -> List[Dict]:
        """Generate alerts from health report"""
        alerts = []

        for check in report.checks:
            if check.status == HealthStatus.CRITICAL:
                alerts.append({
                    "severity": "critical",
                    "check": check.name,
                    "message": check.message,
                    "timestamp": check.timestamp
                })
            elif check.status == HealthStatus.UNHEALTHY:
                alerts.append({
                    "severity": "error",
                    "check": check.name,
                    "message": check.message,
                    "timestamp": check.timestamp
                })
            elif check.status == HealthStatus.DEGRADED:
                alerts.append({
                    "severity": "warning",
                    "check": check.name,
                    "message": check.message,
                    "timestamp": check.timestamp
                })

        return alerts

    async def _handle_alerts(self, alerts: List[Dict], alert_file: Optional[str]):
        """Handle generated alerts"""
        for alert in alerts:
            # Log alert
            level = {
                "critical": logging.CRITICAL,
                "error": logging.ERROR,
                "warning": logging.WARNING
            }.get(alert["severity"], logging.INFO)

            logger.log(level, f"ALERT [{alert['severity'].upper()}] {alert['check']}: {alert['message']}")

            # Write to alert file if specified
            if alert_file:
                alert_entry = {
                    "timestamp": alert["timestamp"].isoformat(),
                    "severity": alert["severity"],
                    "check": alert["check"],
                    "message": alert["message"],
                    "environment": self.config["environment"],
                    "node": self.config["node_name"]
                }

                try:
                    with open(alert_file, "a") as f:
                        f.write(json.dumps(alert_entry) + "\n")
                except Exception as e:
                    logger.error(f"Failed to write alert to file: {e}")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="RedditHarbor Phase 5 Health Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run single health check
  python health_monitor.py

  # Run with JSON output
  python health_monitor.py --format json

  # Continuous monitoring
  python health_monitor.py --continuous --interval 30

  # Continuous monitoring with alerts file
  python health_monitor.py --continuous --alerts-file /var/log/health-alerts.log

  # Custom configuration
  python health_monitor.py --health-endpoint http://service:8000/health
        """
    )

    parser.add_argument(
        "--health-endpoint",
        default=os.getenv("HEALTH_ENDPOINT", "http://localhost:8000/health"),
        help="Health check endpoint URL"
    )
    parser.add_argument(
        "--detailed-endpoint",
        default=os.getenv("DETAILED_ENDPOINT", "http://localhost:8000/health/detailed"),
        help="Detailed health check endpoint URL"
    )
    parser.add_argument(
        "--metrics-endpoint",
        default=os.getenv("METRICS_ENDPOINT", "http://localhost:8000/metrics"),
        help="Metrics endpoint URL"
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuous monitoring"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Monitoring interval in seconds (for continuous mode)"
    )
    parser.add_argument(
        "--alerts-file",
        help="File to write alerts to"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.getenv("HEALTH_TIMEOUT", "30")),
        help="Request timeout in seconds"
    )

    args = parser.parse_args()

    # Create monitor with configuration
    config = {
        "health_endpoint": args.health_endpoint,
        "detailed_endpoint": args.detailed_endpoint,
        "metrics_endpoint": args.metrics_endpoint,
        "timeout": args.timeout
    }

    async with HealthMonitor(config) as monitor:
        if args.continuous:
            await monitor.run_continuous_monitoring(
                interval=args.interval,
                alert_file=args.alerts_file
            )
        else:
            report = await monitor.run_health_checks()
            monitor.print_report(report, args.format)

            # Exit with appropriate code based on health status
            if report.overall_status == HealthStatus.UNHEALTHY:
                sys.exit(2)
            elif report.overall_status == HealthStatus.DEGRADED:
                sys.exit(1)
            else:
                sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())