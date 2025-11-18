#!/usr/bin/env python3
"""
RedditHarbor Advanced Feature Migration Monitoring System
Real-time monitoring and alerting for Phase 5 advanced feature migration.

Author: Data Engineering Team
Date: 2025-11-18
Version: 1.0.0
"""

import asyncio
import asyncpg
import psutil
import time
import json
import sys
import logging
import smtplib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from dataclasses import dataclass
import aiofiles

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config.settings import get_database_config

@dataclass
class PerformanceMetrics:
    """Real-time performance metrics"""
    timestamp: datetime
    query_time_ms: float
    cpu_usage_percent: float
    memory_usage_mb: float
    active_connections: int
    cache_hit_ratio: float
    slow_queries_count: int
    materialized_view_refresh_time_ms: float

@dataclass
class HealthCheck:
    """System health check results"""
    component: str
    status: str  # 'healthy', 'warning', 'critical'
    message: str
    timestamp: datetime
    metrics: Dict[str, Any]

@dataclass
class Alert:
    """Alert data structure"""
    alert_id: str
    severity: str  # 'info', 'warning', 'error', 'critical'
    component: str
    message: str
    timestamp: datetime
    metrics: Dict[str, Any]
    acknowledged: bool = False

class AdvancedMigrationMonitor:
    """
    Advanced monitoring system for RedditHarbor Phase 5 migration
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.db_config = get_database_config()

        # Monitoring thresholds
        self.thresholds = {
            'query_time_ms': 200.0,
            'cpu_usage_percent': 80.0,
            'memory_usage_percent': 85.0,
            'active_connections': 100,
            'cache_hit_ratio': 0.7,
            'slow_queries_count': 10,
            'mv_refresh_time_ms': 60000.0,  # 60 seconds
            'disk_usage_percent': 90.0
        }

        # Alerting configuration
        self.alert_config = {
            'email_enabled': config.get('email_alerts', {}).get('enabled', False),
            'email_recipients': config.get('email_alerts', {}).get('recipients', []),
            'slack_webhook': config.get('slack_webhook'),
            'alert_cooldown_minutes': 15
        }

        # Initialize monitoring state
        self.metrics_history = []
        self.health_checks = {}
        self.active_alerts = {}
        self.alert_history = []
        self.last_alert_times = {}

    async def start_monitoring(self, duration_minutes: Optional[int] = None) -> None:
        """Start continuous monitoring"""

        self.logger.info("Starting advanced migration monitoring")

        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes) if duration_minutes else None

        try:
            async with asyncpg.create_pool(**self.db_config) as db_pool:
                async with db_pool.acquire() as conn:

                    while True:
                        # Check if monitoring duration exceeded
                        if end_time and datetime.now() >= end_time:
                            self.logger.info(f"Monitoring duration of {duration_minutes} minutes completed")
                            break

                        try:
                            # Collect metrics
                            metrics = await self._collect_performance_metrics(conn)

                            # Run health checks
                            health_checks = await self._run_health_checks(conn)

                            # Analyze metrics and check for alerts
                            await self._analyze_metrics_and_alerts(metrics, health_checks)

                            # Store metrics and health checks
                            self.metrics_history.append(metrics)
                            self.health_checks.update({
                                check.component: check for check in health_checks
                            })

                            # Cleanup old metrics (keep last 24 hours)
                            self._cleanup_old_metrics()

                        except Exception as e:
                            self.logger.error(f"Monitoring cycle error: {e}")
                            await self._send_alert(Alert(
                                alert_id=f"monitoring_error_{int(time.time())}",
                                severity='error',
                                component='monitoring_system',
                                message=f"Monitoring system error: {str(e)}",
                                timestamp=datetime.now(),
                                metrics={'error': str(e)}
                            ))

                        # Wait for next monitoring cycle
                        await asyncio.sleep(30)  # Monitor every 30 seconds

        except Exception as e:
            self.logger.error(f"Monitoring system failed: {e}")
            raise

    async def _collect_performance_metrics(self, conn: asyncpg.Connection) -> PerformanceMetrics:
        """Collect comprehensive performance metrics"""

        timestamp = datetime.now()

        try:
            # Database query performance metrics
            query_time = await self._measure_avg_query_time(conn)

            # System resource metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_usage_mb = memory.used / 1024 / 1024

            # Database connection metrics
            active_connections = await self._get_active_connections(conn)

            # Cache hit ratio (if available)
            cache_hit_ratio = await self._get_cache_hit_ratio(conn)

            # Slow queries count
            slow_queries_count = await self._get_slow_queries_count(conn)

            # Materialized view refresh time
            mv_refresh_time = await self._get_materialized_view_refresh_time(conn)

            return PerformanceMetrics(
                timestamp=timestamp,
                query_time_ms=query_time,
                cpu_usage_percent=cpu_usage,
                memory_usage_mb=memory_usage_mb,
                active_connections=active_connections,
                cache_hit_ratio=cache_hit_ratio,
                slow_queries_count=slow_queries_count,
                materialized_view_refresh_time_ms=mv_refresh_time
            )

        except Exception as e:
            self.logger.error(f"Metrics collection failed: {e}")
            # Return default metrics on error
            return PerformanceMetrics(
                timestamp=timestamp,
                query_time_ms=0.0,
                cpu_usage_percent=0.0,
                memory_usage_mb=0.0,
                active_connections=0,
                cache_hit_ratio=0.0,
                slow_queries_count=0,
                materialized_view_refresh_time_ms=0.0
            )

    async def _measure_avg_query_time(self, conn: asyncpg.Connection) -> float:
        """Measure average query execution time"""

        test_queries = [
            "SELECT COUNT(*) FROM opportunities_unified LIMIT 1",
            "SELECT COUNT(*) FROM opportunity_assessments LIMIT 1",
            "SELECT COUNT(*) FROM mv_opportunity_rankings LIMIT 1"
        ]

        total_time = 0.0
        successful_queries = 0

        for query in test_queries:
            try:
                start_time = time.time()
                await conn.fetch(query)
                execution_time = (time.time() - start_time) * 1000  # Convert to ms
                total_time += execution_time
                successful_queries += 1
            except Exception as e:
                self.logger.warning(f"Test query failed: {query}, error: {e}")

        return total_time / successful_queries if successful_queries > 0 else 0.0

    async def _get_active_connections(self, conn: asyncpg.Connection) -> int:
        """Get current number of active database connections"""

        try:
            result = await conn.fetchval("""
                SELECT COUNT(*) FROM pg_stat_activity
                WHERE state = 'active'
            """)
            return result
        except Exception:
            return 0

    async def _get_cache_hit_ratio(self, conn: asyncpg.Connection) -> float:
        """Get database cache hit ratio"""

        try:
            result = await conn.fetchrow("""
                SELECT
                    blks_hit,
                    blks_read
                FROM pg_stat_database
                WHERE datname = current_database()
            """)

            if result and result['blks_read'] > 0:
                return result['blks_hit'] / (result['blks_hit'] + result['blks_read'])
            return 0.0
        except Exception:
            return 0.0

    async def _get_slow_queries_count(self, conn: asyncpg.Connection) -> int:
        """Get count of slow queries from pg_stat_statements"""

        try:
            # Check if pg_stat_statements is available
            extension_exists = await conn.fetchval("""
                SELECT COUNT(*) FROM pg_extension
                WHERE extname = 'pg_stat_statements'
            """) > 0

            if not extension_exists:
                return 0

            result = await conn.fetchval("""
                SELECT COUNT(*) FROM pg_stat_statements
                WHERE mean_exec_time > 1000  -- Queries taking > 1 second
            """)
            return result
        except Exception:
            return 0

    async def _get_materialized_view_refresh_time(self, conn: asyncpg.Connection) -> float:
        """Get materialized view refresh performance"""

        try:
            # Try to refresh a small materialized view to measure performance
            start_time = time.time()
            await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_opportunity_rankings")
            refresh_time = (time.time() - start_time) * 1000  # Convert to ms
            return refresh_time
        except Exception:
            return 0.0

    async def _run_health_checks(self, conn: asyncpg.Connection) -> List[HealthCheck]:
        """Run comprehensive health checks"""

        health_checks = []

        # Database connectivity check
        db_health = await self._check_database_health(conn)
        health_checks.append(db_health)

        # Materialized views health check
        mv_health = await self._check_materialized_views_health(conn)
        health_checks.append(mv_health)

        # Index health check
        index_health = await self._check_index_health(conn)
        health_checks.append(index_health)

        # JSONB performance health check
        jsonb_health = await self._check_jsonb_performance(conn)
        health_checks.append(jsonb_health)

        # System resource health check
        system_health = await self._check_system_resources()
        health_checks.append(system_health)

        return health_checks

    async def _check_database_health(self, conn: asyncpg.Connection) -> HealthCheck:
        """Check database connectivity and basic operations"""

        try:
            # Test basic database operations
            test_result = await conn.fetchval("SELECT 1 as test")

            if test_result == 1:
                return HealthCheck(
                    component='database',
                    status='healthy',
                    message='Database connectivity and basic operations working',
                    timestamp=datetime.now(),
                    metrics={'test_query_success': True}
                )
            else:
                return HealthCheck(
                    component='database',
                    status='critical',
                    message='Database test query returned unexpected result',
                    timestamp=datetime.now(),
                    metrics={'test_query_result': test_result}
                )
        except Exception as e:
            return HealthCheck(
                component='database',
                status='critical',
                message=f'Database health check failed: {str(e)}',
                timestamp=datetime.now(),
                metrics={'error': str(e)}
            )

    async def _check_materialized_views_health(self, conn: asyncpg.Connection) -> HealthCheck:
        """Check materialized views health and freshness"""

        try:
            # Check if materialized views exist and have data
            mv_count = await conn.fetchval("""
                SELECT COUNT(*) FROM pg_matviews
                WHERE schemaname = 'public'
            """)

            # Check data freshness
            mv_freshness = await conn.fetch("""
                SELECT
                    matviewname,
                    EXTRACT(EPOCH FROM (NOW() - last_refresh_time)) as age_seconds
                FROM (
                    SELECT
                        matviewname,
                        pg_stat_get_last_vacuum_time(c.oid) as last_refresh_time
                    FROM pg_matviews mv
                    JOIN pg_class c ON c.relname = mv.matviewname
                    WHERE mv.schemaname = 'public'
                ) fresh_data
            """)

            status = 'healthy'
            message = f'{mv_count} materialized views found'

            if mv_count == 0:
                status = 'critical'
                message = 'No materialized views found'
            elif mv_freshness and any(row['age_seconds'] > 3600 for row in mv_freshness):
                status = 'warning'
                message = 'Some materialized views may be stale'

            return HealthCheck(
                component='materialized_views',
                status=status,
                message=message,
                timestamp=datetime.now(),
                metrics={
                    'mv_count': mv_count,
                    'freshness_data': mv_freshness
                }
            )
        except Exception as e:
            return HealthCheck(
                component='materialized_views',
                status='critical',
                message=f'Materialized views health check failed: {str(e)}',
                timestamp=datetime.now(),
                metrics={'error': str(e)}
            )

    async def _check_index_health(self, conn: asyncpg.Connection) -> HealthCheck:
        """Check index usage and health"""

        try:
            # Get index usage statistics
            index_stats = await conn.fetch("""
                SELECT
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch,
                    schemaname,
                    tablename
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
            """)

            total_indexes = len(index_stats)
            used_indexes = len([idx for idx in index_stats if idx['idx_scan'] > 0])
            unused_indexes = total_indexes - used_indexes

            # Check for bloat or corruption (simplified)
            bloat_check = await conn.fetchval("""
                SELECT COUNT(*) FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relkind = 'i'
                AND n.nspname = 'public'
                AND c.reltuples > 0
                AND c.relpages / GREATEST(c.reltuples, 1) > 10  -- High pages to tuples ratio
            """)

            status = 'healthy'
            message = f'{used_indexes}/{total_indexes} indexes are being used'

            if unused_indexes > total_indexes * 0.3:  # More than 30% unused
                status = 'warning'
                message += f' ({unused_indexes} indexes unused)'
            elif bloat_check > 0:
                status = 'warning'
                message += ' (some indexes may need maintenance)'

            return HealthCheck(
                component='indexes',
                status=status,
                message=message,
                timestamp=datetime.now(),
                metrics={
                    'total_indexes': total_indexes,
                    'used_indexes': used_indexes,
                    'unused_indexes': unused_indexes,
                    'potentially_bloated_indexes': bloat_check
                }
            )
        except Exception as e:
            return HealthCheck(
                component='indexes',
                status='critical',
                message=f'Index health check failed: {str(e)}',
                timestamp=datetime.now(),
                metrics={'error': str(e)}
            )

    async def _check_jsonb_performance(self, conn: asyncpg.Connection) -> HealthCheck:
        """Check JSONB query performance"""

        try:
            # Test JSONB query performance
            jsonb_queries = [
                """
                SELECT COUNT(*) FROM comments
                WHERE (score->>'sentiment_label') = 'positive'
                """,
                """
                SELECT COUNT(*) FROM opportunity_scores
                WHERE (evidence->>'confidence_score')::numeric > 0.8
                """
            ]

            query_times = []
            for query in jsonb_queries:
                start_time = time.time()
                try:
                    await conn.fetch(query)
                    execution_time = (time.time() - start_time) * 1000
                    query_times.append(execution_time)
                except Exception:
                    query_times.append(float('inf'))

            avg_query_time = sum(t for t in query_times if t != float('inf')) / len([t for t in query_times if t != float('inf')])

            status = 'healthy'
            message = f'JSONB queries averaging {avg_query_time:.1f}ms'

            if avg_query_time > 500:  # More than 500ms average
                status = 'warning'
                message += ' (performance may be degraded)'
            elif avg_query_time > 2000:  # More than 2 seconds average
                status = 'critical'
                message += ' (severe performance issue)'

            return HealthCheck(
                component='jsonb_performance',
                status=status,
                message=message,
                timestamp=datetime.now(),
                metrics={
                    'average_query_time_ms': avg_query_time,
                    'query_times': query_times
                }
            )
        except Exception as e:
            return HealthCheck(
                component='jsonb_performance',
                status='critical',
                message=f'JSONB performance check failed: {str(e)}',
                timestamp=datetime.now(),
                metrics={'error': str(e)}
            )

    async def _check_system_resources(self) -> HealthCheck:
        """Check system resource usage"""

        try:
            # CPU and memory
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            status = 'healthy'
            messages = []

            if cpu_usage > 90:
                status = 'critical'
                messages.append(f'High CPU usage: {cpu_usage:.1f}%')
            elif cpu_usage > 80:
                status = 'warning'
                messages.append(f'Elevated CPU usage: {cpu_usage:.1f}%')

            if memory.percent > 90:
                status = 'critical'
                messages.append(f'High memory usage: {memory.percent:.1f}%')
            elif memory.percent > 80:
                if status != 'critical':
                    status = 'warning'
                messages.append(f'Elevated memory usage: {memory.percent:.1f}%')

            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > 90:
                status = 'critical'
                messages.append(f'High disk usage: {disk_percent:.1f}%')
            elif disk_percent > 85:
                if status != 'critical':
                    status = 'warning'
                messages.append(f'Elevated disk usage: {disk_percent:.1f}%')

            message = '; '.join(messages) if messages else 'System resources within normal limits'

            return HealthCheck(
                component='system_resources',
                status=status,
                message=message,
                timestamp=datetime.now(),
                metrics={
                    'cpu_usage_percent': cpu_usage,
                    'memory_usage_percent': memory.percent,
                    'disk_usage_percent': disk_percent,
                    'memory_available_gb': memory.available / 1024 / 1024 / 1024
                }
            )
        except Exception as e:
            return HealthCheck(
                component='system_resources',
                status='critical',
                message=f'System resource check failed: {str(e)}',
                timestamp=datetime.now(),
                metrics={'error': str(e)}
            )

    async def _analyze_metrics_and_alerts(self, metrics: PerformanceMetrics, health_checks: List[HealthCheck]) -> None:
        """Analyze metrics and generate alerts"""

        # Check performance metric thresholds
        await self._check_performance_thresholds(metrics)

        # Check health check status
        await self._check_health_alerts(health_checks)

        # Check for metric trends
        await self._check_metric_trends()

    async def _check_performance_thresholds(self, metrics: PerformanceMetrics) -> None:
        """Check performance metrics against thresholds"""

        alerts_to_send = []

        # Query time threshold
        if metrics.query_time_ms > self.thresholds['query_time_ms']:
            alerts_to_send.append(Alert(
                alert_id=f"slow_queries_{int(time.time())}",
                severity='warning' if metrics.query_time_ms < self.thresholds['query_time_ms'] * 2 else 'critical',
                component='query_performance',
                message=f"Slow query performance detected: {metrics.query_time_ms:.1f}ms average",
                timestamp=datetime.now(),
                metrics={'query_time_ms': metrics.query_time_ms}
            ))

        # CPU usage threshold
        if metrics.cpu_usage_percent > self.thresholds['cpu_usage_percent']:
            alerts_to_send.append(Alert(
                alert_id=f"high_cpu_{int(time.time())}",
                severity='warning' if metrics.cpu_usage_percent < 95 else 'critical',
                component='system_resources',
                message=f"High CPU usage: {metrics.cpu_usage_percent:.1f}%",
                timestamp=datetime.now(),
                metrics={'cpu_usage_percent': metrics.cpu_usage_percent}
            ))

        # Memory usage threshold
        memory_usage_percent = (metrics.memory_usage_mb * 1024 * 1024) / psutil.virtual_memory().total * 100
        if memory_usage_percent > self.thresholds['memory_usage_percent']:
            alerts_to_send.append(Alert(
                alert_id=f"high_memory_{int(time.time())}",
                severity='warning' if memory_usage_percent < 95 else 'critical',
                component='system_resources',
                message=f"High memory usage: {memory_usage_percent:.1f}%",
                timestamp=datetime.now(),
                metrics={'memory_usage_percent': memory_usage_percent}
            ))

        # Active connections threshold
        if metrics.active_connections > self.thresholds['active_connections']:
            alerts_to_send.append(Alert(
                alert_id=f"high_connections_{int(time.time())}",
                severity='warning',
                component='database',
                message=f"High database connections: {metrics.active_connections}",
                timestamp=datetime.now(),
                metrics={'active_connections': metrics.active_connections}
            ))

        # Cache hit ratio threshold
        if metrics.cache_hit_ratio < self.thresholds['cache_hit_ratio']:
            alerts_to_send.append(Alert(
                alert_id=f"low_cache_hit_ratio_{int(time.time())}",
                severity='warning',
                component='database_performance',
                message=f"Low cache hit ratio: {metrics.cache_hit_ratio:.2f}",
                timestamp=datetime.now(),
                metrics={'cache_hit_ratio': metrics.cache_hit_ratio}
            ))

        # Materialized view refresh time threshold
        if metrics.materialized_view_refresh_time_ms > self.thresholds['mv_refresh_time_ms']:
            alerts_to_send.append(Alert(
                alert_id=f"slow_mv_refresh_{int(time.time())}",
                severity='warning' if metrics.materialized_view_refresh_time_ms < self.thresholds['mv_refresh_time_ms'] * 2 else 'critical',
                component='materialized_views',
                message=f"Slow materialized view refresh: {metrics.materialized_view_refresh_time_ms:.1f}ms",
                timestamp=datetime.now(),
                metrics={'mv_refresh_time_ms': metrics.materialized_view_refresh_time_ms}
            ))

        # Send alerts
        for alert in alerts_to_send:
            await self._send_alert(alert)

    async def _check_health_alerts(self, health_checks: List[HealthCheck]) -> None:
        """Check health checks for alert conditions"""

        for check in health_checks:
            if check.status in ['warning', 'critical']:
                alert = Alert(
                    alert_id=f"health_{check.component}_{int(time.time())}",
                    severity='warning' if check.status == 'warning' else 'critical',
                    component=check.component,
                    message=f"Health check {check.status}: {check.message}",
                    timestamp=check.timestamp,
                    metrics=check.metrics
                )
                await self._send_alert(alert)

    async def _check_metric_trends(self) -> None:
        """Check for concerning metric trends"""

        if len(self.metrics_history) < 10:  # Need at least 10 data points for trend analysis
            return

        recent_metrics = self.metrics_history[-10:]

        # Check for steadily increasing query times
        query_times = [m.query_time_ms for m in recent_metrics]
        if len(query_times) >= 5:
            recent_avg = sum(query_times[-5:]) / 5
            older_avg = sum(query_times[:5]) / 5

            if recent_avg > older_avg * 1.5:  # 50% increase
                await self._send_alert(Alert(
                    alert_id=f"query_performance_degradation_{int(time.time())}",
                    severity='warning',
                    component='performance_trend',
                    message=f"Query performance degradation detected: {recent_avg:.1f}ms vs {older_avg:.1f}ms",
                    timestamp=datetime.now(),
                    metrics={'recent_avg_ms': recent_avg, 'older_avg_ms': older_avg}
                ))

    async def _send_alert(self, alert: Alert) -> None:
        """Send alert through configured channels"""

        # Check alert cooldown
        alert_key = f"{alert.component}_{alert.severity}"
        current_time = datetime.now()

        if (alert_key in self.last_alert_times and
            (current_time - self.last_alert_times[alert_key]).total_seconds() < self.alert_config['alert_cooldown_minutes'] * 60):
            return  # Skip due to cooldown

        self.last_alert_times[alert_key] = current_time

        # Store alert
        self.active_alerts[alert.alert_id] = alert
        self.alert_history.append(alert)

        # Send email alerts if enabled
        if self.alert_config['email_enabled'] and self.alert_config['email_recipients']:
            await self._send_email_alert(alert)

        # Send Slack alerts if configured
        if self.alert_config['slack_webhook']:
            await self._send_slack_alert(alert)

        # Log alert
        log_level = {
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL
        }.get(alert.severity, logging.WARNING)

        self.logger.log(log_level, f"ALERT: {alert.component} - {alert.message}")

    async def _send_email_alert(self, alert: Alert) -> None:
        """Send email alert"""

        try:
            # This would integrate with your email service
            # For now, we'll just log the email that would be sent
            email_body = f"""
            RedditHarbor Migration Alert

            Component: {alert.component}
            Severity: {alert.severity}
            Time: {alert.timestamp.isoformat()}
            Message: {alert.message}

            Metrics:
            {json.dumps(alert.metrics, indent=2, default=str)}
            """

            self.logger.info(f"EMAIL ALERT (would send to {self.alert_config['email_recipients']}): {email_body}")

        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")

    async def _send_slack_alert(self, alert: Alert) -> None:
        """Send Slack alert"""

        try:
            # This would integrate with Slack webhook
            # For now, we'll just log the Slack message that would be sent
            slack_message = {
                "text": f"RedditHarbor Migration Alert: {alert.component}",
                "attachments": [
                    {
                        "color": self._get_slack_color(alert.severity),
                        "fields": [
                            {"title": "Severity", "value": alert.severity, "short": True},
                            {"title": "Component", "value": alert.component, "short": True},
                            {"title": "Message", "value": alert.message, "short": False},
                            {"title": "Time", "value": alert.timestamp.isoformat(), "short": True}
                        ]
                    }
                ]
            }

            self.logger.info(f"SLACK ALERT (would send to webhook): {json.dumps(slack_message)}")

        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {e}")

    def _get_slack_color(self, severity: str) -> str:
        """Get Slack color for alert severity"""
        return {
            'info': '#36a64f',      # green
            'warning': '#ff9500',   # orange
            'error': '#ff0000',     # red
            'critical': '#8b0000'   # dark red
        }.get(severity, '#ff9500')

    def _cleanup_old_metrics(self) -> None:
        """Clean up old metrics to prevent memory issues"""

        cutoff_time = datetime.now() - timedelta(hours=24)
        self.metrics_history = [
            m for m in self.metrics_history
            if m.timestamp > cutoff_time
        ]

        # Also cleanup old alerts (keep last 1000)
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]

    def generate_monitoring_report(self) -> str:
        """Generate comprehensive monitoring report"""

        report_lines = [
            "# RedditHarbor Advanced Migration Monitoring Report",
            f"**Generated**: {datetime.now().isoformat()}",
            "",
            "## System Overview",
            ""
        ]

        # Current status summary
        healthy_components = len([h for h in self.health_checks.values() if h.status == 'healthy'])
        warning_components = len([h for h in self.health_checks.values() if h.status == 'warning'])
        critical_components = len([h for h in self.health_checks.values() if h.status == 'critical'])

        report_lines.extend([
            f"**Healthy Components**: {healthy_components} ✅",
            f"**Warning Components**: {warning_components} ⚠️",
            f"**Critical Components**: {critical_components} ❌",
            f"**Active Alerts**: {len(self.active_alerts)}",
            f"**Total Alerts (24h)**: {len([a for a in self.alert_history if (datetime.now() - a.timestamp).total_seconds() < 86400])}",
            ""
        ])

        # Recent metrics
        if self.metrics_history:
            latest_metrics = self.metrics_history[-1]
            report_lines.extend([
                "## Latest Metrics",
                f"**Query Time**: {latest_metrics.query_time_ms:.1f}ms",
                f"**CPU Usage**: {latest_metrics.cpu_usage_percent:.1f}%",
                f"**Memory Usage**: {latest_metrics.memory_usage_mb:.1f}MB",
                f"**Active Connections**: {latest_metrics.active_connections}",
                f"**Cache Hit Ratio**: {latest_metrics.cache_hit_ratio:.2f}",
                f"**Slow Queries**: {latest_metrics.slow_queries_count}",
                f"**MV Refresh Time**: {latest_metrics.materialized_view_refresh_time_ms:.1f}ms",
                ""
            ])

        # Health check details
        report_lines.extend(["## Component Health", ""])
        for component, health_check in self.health_checks.items():
            status_emoji = "✅" if health_check.status == "healthy" else "⚠️" if health_check.status == "warning" else "❌"
            report_lines.extend([
                f"### {component.replace('_', ' ').title()} {status_emoji}",
                f"**Status**: {health_check.status.upper()}",
                f"**Message**: {health_check.message}",
                f"**Last Checked**: {health_check.timestamp.isoformat()}",
                ""
            ])

        # Recent alerts
        recent_alerts = [a for a in self.alert_history if (datetime.now() - a.timestamp).total_seconds() < 3600]  # Last hour
        if recent_alerts:
            report_lines.extend(["## Recent Alerts (Last Hour)", ""])
            for alert in recent_alerts[-10:]:  # Show last 10
                severity_emoji = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🚨"}.get(alert.severity, "⚠️")
                report_lines.extend([
                    f"{severity_emoji} **{alert.component}** ({alert.severity.upper()})",
                    f"   {alert.message}",
                    f"   *{alert.timestamp.strftime('%H:%M:%S')}*",
                    ""
                ])

        # Performance trends
        if len(self.metrics_history) >= 10:
            report_lines.extend(["## Performance Trends", ""])

            # Calculate trends
            recent_avg_query_time = sum(m.query_time_ms for m in self.metrics_history[-5:]) / 5
            older_avg_query_time = sum(m.query_time_ms for m in self.metrics_history[-10:-5]) / 5

            trend = "↑" if recent_avg_query_time > older_avg_query_time else "↓" if recent_avg_query_time < older_avg_query_time else "→"
            report_lines.extend([
                f"**Query Performance Trend**: {trend} {recent_avg_query_time:.1f}ms (avg over last 5 checks)",
                ""
            ])

        report_lines.extend([
            "---",
            f"**Report generated by RedditHarbor Advanced Migration Monitoring System**",
            f"**Version**: 1.0.0"
        ])

        return "\n".join(report_lines)

    async def save_monitoring_data(self, output_dir: str) -> None:
        """Save monitoring data to files"""

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save metrics history
        metrics_file = output_path / f"metrics_history_{timestamp}.json"
        metrics_data = [asdict(m) for m in self.metrics_history]

        async with aiofiles.open(metrics_file, 'w') as f:
            await f.write(json.dumps(metrics_data, indent=2, default=str))

        # Save health checks
        health_file = output_path / f"health_checks_{timestamp}.json"
        health_data = {k: asdict(v) for k, v in self.health_checks.items()}

        async with aiofiles.open(health_file, 'w') as f:
            await f.write(json.dumps(health_data, indent=2, default=str))

        # Save alerts
        alerts_file = output_path / f"alerts_{timestamp}.json"
        alerts_data = [asdict(a) for a in self.alert_history]

        async with aiofiles.open(alerts_file, 'w') as f:
            await f.write(json.dumps(alerts_data, indent=2, default=str))

        # Save monitoring report
        report_file = output_path / f"monitoring_report_{timestamp}.md"
        report = self.generate_monitoring_report()

        async with aiofiles.open(report_file, 'w') as f:
            await f.write(report)

        self.logger.info(f"Monitoring data saved to {output_path}")


async def main():
    """Main entry point for the monitoring system"""

    parser = argparse.ArgumentParser(
        description="RedditHarbor Advanced Migration Monitoring"
    )
    parser.add_argument(
        '--duration-minutes',
        type=int,
        help='Monitoring duration in minutes (default: continuous)'
    )
    parser.add_argument(
        '--output-dir',
        default='./monitoring_output',
        help='Directory to save monitoring data'
    )
    parser.add_argument(
        '--config-file',
        help='Path to monitoring configuration file'
    )

    args = parser.parse_args()

    # Load configuration
    config = {}
    if args.config_file:
        try:
            async with aiofiles.open(args.config_file, 'r') as f:
                config_content = await f.read()
                config = json.loads(config_content)
        except Exception as e:
            print(f"Failed to load config file: {e}")
            return 1

    # Initialize monitoring system
    monitor = AdvancedMigrationMonitor(config)

    print("🔍 Starting RedditHarbor Advanced Migration Monitoring")
    print("=" * 60)

    if args.duration_minutes:
        print(f"Monitoring duration: {args.duration_minutes} minutes")
    else:
        print("Continuous monitoring (Ctrl+C to stop)")

    try:
        # Start monitoring
        await monitor.start_monitoring(args.duration_minutes)

    except KeyboardInterrupt:
        print("\n⏹️ Monitoring stopped by user")

    except Exception as e:
        print(f"\n❌ Monitoring failed: {e}")
        return 1

    finally:
        # Save monitoring data
        print(f"\n💾 Saving monitoring data to {args.output_dir}")
        await monitor.save_monitoring_data(args.output_dir)

        # Generate final report
        report = monitor.generate_monitoring_report()
        print("\n" + report)

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)