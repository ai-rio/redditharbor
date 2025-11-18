#!/usr/bin/env python3
"""
Migration Progress Monitor

Real-time monitoring and alerting for core table restructuring progress.
Provides comprehensive visibility into migration status, performance, and health.

Usage:
    uv run python3 scripts/monitoring/migration_progress_monitor.py
    uv run python3 scripts/monitoring/migration_progress_monitor.py --continuous
    uv run python3 scripts/monitoring/migration_progress_monitor.py --alerts-only
"""

import asyncio
import json
import logging
import smtplib
import sys
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import asyncpg
import psutil

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config.settings import get_database_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/migration_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MigrationProgressMonitor:
    """Real-time monitoring for core table restructuring."""

    def __init__(self, continuous: bool = False, alerts_only: bool = False):
        self.db_config = get_database_config()
        self.continuous = continuous
        self.alerts_only = alerts_only
        self.monitoring_start_time = datetime.now()
        self.alert_thresholds = {
            'query_time_warning': 2.0,  # seconds
            'query_time_critical': 5.0,  # seconds
            'memory_warning': 80,  # percentage
            'cpu_warning': 80,  # percentage
            'disk_warning': 85,  # percentage
            'connection_warning': 50,  # percentage of max connections
        }

        # Ensure logs directory exists
        Path("logs").mkdir(exist_ok=True)

        logger.info(f"Migration Progress Monitor initialized - Continuous: {continuous}, Alerts Only: {alerts_only}")

    async def get_db_connection(self) -> asyncpg.Connection:
        """Get database connection."""
        try:
            conn = await asyncpg.connect(
                host=self.db_config.host,
                port=self.db_config.port,
                user=self.db_config.user,
                password=self.db_config.password,
                database=self.db_config.database
            )
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def get_system_metrics(self) -> Dict:
        """Get system performance metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100

            # Network stats
            network = psutil.net_io_counters()

            return {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'status': 'warning' if cpu_percent > self.alert_thresholds['cpu_warning'] else 'normal'
                },
                'memory': {
                    'percent': memory_percent,
                    'used_gb': memory.used / (1024**3),
                    'total_gb': memory.total / (1024**3),
                    'status': 'warning' if memory_percent > self.alert_thresholds['memory_warning'] else 'normal'
                },
                'disk': {
                    'percent': disk_percent,
                    'used_gb': disk.used / (1024**3),
                    'total_gb': disk.total / (1024**3),
                    'status': 'warning' if disk_percent > self.alert_thresholds['disk_warning'] else 'normal'
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv
                }
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {'error': str(e)}

    async def get_database_metrics(self, conn: asyncpg.Connection) -> Dict:
        """Get database performance metrics."""
        try:
            # Connection info
            connection_query = """
                SELECT
                    count(*) as active_connections,
                    round(
                        100.0 * count(*) /
                        (SELECT setting::int FROM pg_settings WHERE name = 'max_connections')
                    , 2) as connection_percent
                FROM pg_stat_activity
                WHERE state = 'active';
            """

            conn_info = await conn.fetchrow(connection_query)

            # Table sizes
            table_sizes_query = """
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size_pretty,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables
                WHERE schemaname = 'public'
                  AND (
                      tablename LIKE '%unified%'
                      OR tablename LIKE '%assessments%'
                      OR tablename LIKE '%backup%'
                  )
                ORDER BY size_bytes DESC;
            """

            table_sizes = await conn.fetch(table_sizes_query)

            # Index usage
            index_usage_query = """
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
                  AND (
                      tablename LIKE '%unified%'
                      OR tablename LIKE '%assessments%'
                  )
                ORDER BY idx_scan DESC;
            """

            index_usage = await conn.fetch(index_usage_query)

            # Query performance (slow queries)
            slow_queries_query = """
                SELECT
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows
                FROM pg_stat_statements
                WHERE mean_time > 1000  -- queries taking more than 1 second on average
                ORDER BY mean_time DESC
                LIMIT 10;
            """

            slow_queries = await conn.fetch(slow_queries_query)

            # Lock information
            lock_info_query = """
                SELECT
                    pid,
                    state,
                    application_name,
                    backend_start,
                    query_start,
                    state_change,
                    wait_event_type,
                    wait_event
                FROM pg_stat_activity
                WHERE wait_event IS NOT NULL
                  AND state != 'idle'
                ORDER BY query_start;
            """

            lock_info = await conn.fetch(lock_info_query)

            return {
                'timestamp': datetime.now().isoformat(),
                'connections': {
                    'active_count': conn_info['active_connections'],
                    'percent_of_max': conn_info['connection_percent'],
                    'status': 'warning' if conn_info['connection_percent'] > self.alert_thresholds['connection_warning'] else 'normal'
                },
                'table_sizes': [dict(row) for row in table_sizes],
                'index_usage': [dict(row) for row in index_usage],
                'slow_queries': [dict(row) for row in slow_queries],
                'locks': [dict(row) for row in lock_info]
            }
        except Exception as e:
            logger.error(f"Failed to get database metrics: {e}")
            return {'error': str(e)}

    async def get_migration_status(self, conn: asyncpg.Connection) -> Dict:
        """Get current migration status and progress."""
        try:
            # Check unified tables exist and get their status
            table_status_query = """
                SELECT
                    'opportunities_unified' as table_name,
                    EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'opportunities_unified') as exists
                UNION ALL
                SELECT
                    'opportunity_assessments' as table_name,
                    EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'opportunity_assessments') as exists;
            """

            table_status = await conn.fetch(table_status_query)

            # Row counts and data freshness
            row_counts_query = """
                WITH unified_counts AS (
                    SELECT 'opportunities_unified' as table_name, COUNT(*) as row_count,
                           MIN(created_at) as earliest_record,
                           MAX(created_at) as latest_record
                    FROM opportunities_unified
                    UNION ALL
                    SELECT 'opportunity_assessments' as table_name, COUNT(*) as row_count,
                           MIN(created_at) as earliest_record,
                           MAX(created_at) as latest_record
                    FROM opportunity_assessments
                ),
                backup_counts AS (
                    SELECT 'opportunities_backup' as table_name, COUNT(*) as row_count
                    FROM opportunities_backup_20251118
                    UNION ALL
                    SELECT 'app_opportunities_backup' as table_name, COUNT(*) as row_count
                    FROM app_opportunities_backup_20251118
                    UNION ALL
                    SELECT 'workflow_results_backup' as table_name, COUNT(*) as row_count
                    FROM workflow_results_backup_20251118
                )
                SELECT * FROM unified_counts
                UNION ALL
                SELECT * FROM backup_counts;
            """

            row_counts = await conn.fetch(row_counts_query)

            # Data integrity checks
            integrity_checks_query = """
                SELECT
                    'trust_score_violations' as check_name,
                    COUNT(*) as violations
                FROM opportunities_unified
                WHERE trust_score < 0 OR trust_score > 100
                UNION ALL
                SELECT
                    'missing_core_data' as check_name,
                    COUNT(*) as violations
                FROM opportunities_unified
                WHERE title IS NULL OR submission_id IS NULL
                UNION ALL
                SELECT
                    'assessment_integrity' as check_name,
                    COUNT(*) as violations
                FROM opportunity_assessments oa
                WHERE oa.opportunity_id NOT IN (SELECT id FROM opportunities_unified);
            """

            integrity_checks = await conn.fetch(integrity_checks_query)

            # Recent activity
            recent_activity_query = """
                SELECT
                    'opportunities_unified' as table_name,
                    COUNT(*) as records_last_hour
                FROM opportunities_unified
                WHERE created_at > NOW() - INTERVAL '1 hour'
                UNION ALL
                SELECT
                    'opportunity_assessments' as table_name,
                    COUNT(*) as records_last_hour
                FROM opportunity_assessments
                WHERE created_at > NOW() - INTERVAL '1 hour';
            """

            recent_activity = await conn.fetch(recent_activity_query)

            total_violations = sum(check['violations'] for check in integrity_checks)

            return {
                'timestamp': datetime.now().isoformat(),
                'table_status': [dict(row) for row in table_status],
                'row_counts': [dict(row) for row in row_counts],
                'integrity_violations': total_violations,
                'integrity_checks': [dict(row) for row in integrity_checks],
                'recent_activity': [dict(row) for row in recent_activity],
                'migration_health': 'healthy' if total_violations == 0 else 'issues_detected'
            }
        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            return {'error': str(e)}

    async def monitor_query_performance(self, conn: asyncpg.Connection) -> Dict:
        """Monitor performance of key migration queries."""
        try:
            # Key queries to monitor
            test_queries = [
                {
                    'name': 'high_trust_opportunities',
                    'query': """
                        SELECT COUNT(*) FROM opportunities_unified
                        WHERE trust_score > 80
                        ORDER BY trust_score DESC
                        LIMIT 10;
                    """
                },
                {
                    'name': 'assessment_join',
                    'query': """
                        SELECT COUNT(*) FROM opportunities_unified ou
                        JOIN opportunity_assessments oa ON ou.id = oa.opportunity_id
                        WHERE oa.total_score > 70;
                    """
                },
                {
                    'name': 'data_integrity_check',
                    'query': """
                        SELECT COUNT(*) FROM opportunities_unified
                        WHERE title IS NULL OR submission_id IS NULL;
                    """
                }
            ]

            query_results = []

            for test_query in test_queries:
                start_time = time.time()
                try:
                    result = await conn.fetchval(test_query['query'])
                    execution_time = time.time() - start_time

                    status = 'normal'
                    if execution_time > self.alert_thresholds['query_time_critical']:
                        status = 'critical'
                    elif execution_time > self.alert_thresholds['query_time_warning']:
                        status = 'warning'

                    query_results.append({
                        'name': test_query['name'],
                        'execution_time': execution_time,
                        'result': result,
                        'status': status
                    })

                except Exception as e:
                    execution_time = time.time() - start_time
                    query_results.append({
                        'name': test_query['name'],
                        'execution_time': execution_time,
                        'error': str(e),
                        'status': 'error'
                    })

            return {
                'timestamp': datetime.now().isoformat(),
                'query_performance': query_results,
                'overall_status': 'normal' if all(q['status'] == 'normal' for q in query_results) else 'warning'
            }
        except Exception as e:
            logger.error(f"Failed to monitor query performance: {e}")
            return {'error': str(e)}

    def check_alert_conditions(self, metrics: Dict) -> List[Dict]:
        """Check for alert conditions in metrics."""
        alerts = []

        # System alerts
        if 'system' in metrics:
            system = metrics['system']

            if system.get('cpu', {}).get('status') == 'warning':
                alerts.append({
                    'type': 'system',
                    'severity': 'warning',
                    'message': f"High CPU usage: {system['cpu']['percent']}%",
                    'timestamp': system['timestamp']
                })

            if system.get('memory', {}).get('status') == 'warning':
                alerts.append({
                    'type': 'system',
                    'severity': 'warning',
                    'message': f"High memory usage: {system['memory']['percent']}%",
                    'timestamp': system['timestamp']
                })

            if system.get('disk', {}).get('status') == 'warning':
                alerts.append({
                    'type': 'system',
                    'severity': 'warning',
                    'message': f"High disk usage: {system['disk']['percent']}%",
                    'timestamp': system['timestamp']
                })

        # Database alerts
        if 'database' in metrics:
            db = metrics['database']

            if db.get('connections', {}).get('status') == 'warning':
                alerts.append({
                    'type': 'database',
                    'severity': 'warning',
                    'message': f"High database connection usage: {db['connections']['percent_of_max']}%",
                    'timestamp': db['timestamp']
                })

            if len(db.get('slow_queries', [])) > 0:
                alerts.append({
                    'type': 'database',
                    'severity': 'warning',
                    'message': f"{len(db['slow_queries'])} slow queries detected",
                    'timestamp': db['timestamp']
                })

        # Migration alerts
        if 'migration' in metrics:
            migration = metrics['migration']

            if migration.get('migration_health') != 'healthy':
                alerts.append({
                    'type': 'migration',
                    'severity': 'critical',
                    'message': f"Migration issues detected: {migration.get('integrity_violations', 0)} integrity violations",
                    'timestamp': migration['timestamp']
                })

        # Query performance alerts
        if 'query_performance' in metrics:
            qp = metrics['query_performance']

            if qp.get('overall_status') != 'normal':
                alerts.append({
                    'type': 'performance',
                    'severity': 'warning',
                    'message': "Query performance issues detected",
                    'timestamp': qp['timestamp']
                })

        return alerts

    async def send_email_alert(self, alert: Dict) -> bool:
        """Send email alert (placeholder - would require email configuration)."""
        try:
            # This is a placeholder - actual email configuration would be needed
            logger.warning(f"EMAIL ALERT: {alert['severity'].upper()} - {alert['message']}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False

    async def collect_metrics(self) -> Dict:
        """Collect all monitoring metrics."""
        conn = await self.get_db_connection()

        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'monitoring_duration': str(datetime.now() - self.monitoring_start_time)
            }

            if not self.alerts_only:
                # Collect all metrics
                metrics['system'] = self.get_system_metrics()
                metrics['database'] = await self.get_database_metrics(conn)
                metrics['migration'] = await self.get_migration_status(conn)
                metrics['query_performance'] = await self.monitor_query_performance(conn)
            else:
                # Only collect metrics needed for alerting
                metrics['system'] = self.get_system_metrics()
                metrics['migration'] = await self.get_migration_status(conn)

            # Check for alerts
            alerts = self.check_alert_conditions(metrics)
            metrics['alerts'] = alerts

            # Send alerts if any
            for alert in alerts:
                await self.send_email_alert(alert)
                logger.warning(f"ALERT: {alert['severity'].upper()} - {alert['message']}")

            return metrics

        finally:
            await conn.close()

    def save_metrics(self, metrics: Dict) -> str:
        """Save metrics to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/migration_metrics_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)

        return filename

    def print_metrics_summary(self, metrics: Dict) -> None:
        """Print metrics summary to console."""
        print("\n" + "="*80)
        print("MIGRATION PROGRESS MONITOR")
        print("="*80)
        print(f"Timestamp: {metrics['timestamp']}")
        print(f"Monitoring Duration: {metrics['monitoring_duration']}")

        # System metrics
        if 'system' in metrics:
            system = metrics['system']
            print(f"\nSYSTEM METRICS:")
            print(f"  CPU: {system['cpu']['percent']:.1f}% ({system['cpu']['status']})")
            print(f"  Memory: {system['memory']['percent']:.1f}% ({system['memory']['status']})")
            print(f"  Disk: {system['disk']['percent']:.1f}% ({system['disk']['status']})")

        # Migration status
        if 'migration' in metrics:
            migration = metrics['migration']
            print(f"\nMIGRATION STATUS:")
            print(f"  Health: {migration['migration_health']}")
            print(f"  Integrity Violations: {migration['integrity_violations']}")

            if 'row_counts' in migration:
                for count in migration['row_counts']:
                    print(f"  {count['table_name']}: {count['row_count']} records")

        # Database metrics
        if 'database' in metrics:
            db = metrics['database']
            print(f"\nDATABASE METRICS:")
            print(f"  Active Connections: {db['connections']['active_count']} ({db['connections']['percent_of_max']:.1f}%)")
            print(f"  Slow Queries: {len(db.get('slow_queries', []))}")
            print(f"  Active Locks: {len(db.get('locks', []))}")

        # Query performance
        if 'query_performance' in metrics:
            qp = metrics['query_performance']
            print(f"\nQUERY PERFORMANCE:")
            for query in qp['query_performance']:
                status_symbol = "✅" if query['status'] == 'normal' else "⚠️"
                print(f"  {status_symbol} {query['name']}: {query['execution_time']:.3f}s")

        # Alerts
        if metrics.get('alerts'):
            print(f"\n🚨 ALERTS ({len(metrics['alerts'])}):")
            for alert in metrics['alerts']:
                severity_symbol = "🔴" if alert['severity'] == 'critical' else "🟡"
                print(f"  {severity_symbol} {alert['type'].upper()}: {alert['message']}")

        print("="*80)

    async def run_continuous_monitoring(self, interval: int = 60) -> None:
        """Run continuous monitoring with specified interval."""
        logger.info(f"Starting continuous monitoring with {interval}s interval")

        try:
            while True:
                metrics = await self.collect_metrics()

                if not self.alerts_only:
                    self.print_metrics_summary(metrics)

                # Save metrics periodically (every 10 cycles)
                if int(time.time()) % (interval * 10) < interval:
                    filename = self.save_metrics(metrics)
                    logger.info(f"Metrics saved to {filename}")

                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Continuous monitoring stopped by user")
        except Exception as e:
            logger.error(f"Continuous monitoring error: {e}")
            raise

    async def run_single_check(self) -> None:
        """Run a single monitoring check."""
        metrics = await self.collect_metrics()
        self.print_metrics_summary(metrics)

        # Always save single check results
        filename = self.save_metrics(metrics)
        logger.info(f"Metrics saved to {filename}")


async def main():
    """Main function for monitoring."""
    import argparse

    parser = argparse.ArgumentParser(description="Migration Progress Monitor")
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuous monitoring'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Monitoring interval in seconds (default: 60)'
    )
    parser.add_argument(
        '--alerts-only',
        action='store_true',
        help='Only collect metrics needed for alerting'
    )
    parser.add_argument(
        '--save-to-file',
        action='store_true',
        help='Save metrics to file'
    )

    args = parser.parse_args()

    # Initialize monitor
    monitor = MigrationProgressMonitor(
        continuous=args.continuous,
        alerts_only=args.alerts_only
    )

    try:
        if args.continuous:
            await monitor.run_continuous_monitoring(args.interval)
        else:
            await monitor.run_single_check()

    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())