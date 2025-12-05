"""
Real-time performance monitoring dashboard for RedditHarbor Agno system

Provides live monitoring of:
- Throughput (RPM)
- Latency distributions (P50, P95, P99)
- Agent performance
- Resource utilization (CPU, Memory)
- Error rates and types
- API call patterns
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging
from collections import defaultdict, deque

import psutil
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PerformanceSnapshot:
    """Snapshot of performance metrics at a point in time"""
    timestamp: datetime
    throughput_rpm: float
    p50_latency: float
    p95_latency: float
    p99_latency: float
    error_rate: float
    cpu_percent: float
    memory_mb: float
    active_connections: int
    queue_depth: int


@dataclass
class AlertThresholds:
    """Thresholds for performance alerts"""
    min_rpm: float = 800  # Alert if RPM falls below
    max_p99_latency: float = 12.0  # Alert if P99 exceeds
    max_error_rate: float = 0.02  # Alert if error rate exceeds 2%
    max_cpu_percent: float = 90.0  # Alert if CPU exceeds
    max_memory_mb: float = 8192  # Alert if memory exceeds 8GB
    max_queue_depth: int = 1000  # Alert if queue depth exceeds


class PerformanceMonitor:
    """Real-time performance monitoring system"""

    def __init__(
        self,
        window_size_minutes: int = 10,
        snapshot_interval_seconds: int = 5,
        alert_thresholds: Optional[AlertThresholds] = None
    ):
        self.window_size_minutes = window_size_minutes
        self.snapshot_interval = snapshot_interval_seconds
        self.alert_thresholds = alert_thresholds or AlertThresholds()

        # Data storage
        self.snapshots = deque(maxlen=window_size_minutes * 60 // snapshot_interval_seconds)
        self.latencies = deque(maxlen=10000)
        self.errors = defaultdict(deque)
        self.agent_metrics = defaultdict(lambda: deque(maxlen=1000))
        self.api_calls = defaultdict(int)

        # Current metrics
        self.current_rpm = 0.0
        self.active_connections = 0
        self.queue_depth = 0

        # Monitoring state
        self.monitoring = False
        self.last_alerts = {}
        self.alert_cooldown_seconds = 60

        # Process for system metrics
        self.process = psutil.Process()

    async def start_monitoring(self):
        """Start performance monitoring"""
        if self.monitoring:
            return

        self.monitoring = True
        logger.info("Starting performance monitoring")

        # Run monitoring loop
        asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        logger.info("Stopping performance monitoring")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Collect metrics
                snapshot = await self._collect_snapshot()
                self.snapshots.append(snapshot)

                # Check alerts
                await self._check_alerts(snapshot)

                # Wait for next interval
                await asyncio.sleep(self.snapshot_interval)

            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(self.snapshot_interval)

    async def _collect_snapshot(self) -> PerformanceSnapshot:
        """Collect current performance snapshot"""
        # Calculate throughput from recent submissions
        if self.snapshots:
            recent_snapshots = [s for s in self.snapshots
                              if s.timestamp > datetime.now() - timedelta(minutes=1)]
            if recent_snapshots:
                self.current_rpm = np.mean([s.throughput_rpm for s in recent_snapshots])

        # Calculate latency percentiles
        if self.latencies:
            latencies_array = np.array(list(self.latencies))
            p50 = np.percentile(latencies_array, 50)
            p95 = np.percentile(latencies_array, 95)
            p99 = np.percentile(latencies_array, 99)
        else:
            p50 = p95 = p99 = 0.0

        # Calculate error rate
        total_errors = sum(len(queue) for queue in self.errors.values())
        total_requests = len(self.latencies) + total_errors
        error_rate = total_errors / total_requests if total_requests > 0 else 0.0

        # Get system metrics
        cpu_percent = self.process.cpu_percent()
        memory_mb = self.process.memory_info().rss / 1024 / 1024

        return PerformanceSnapshot(
            timestamp=datetime.now(),
            throughput_rpm=self.current_rpm,
            p50_latency=p50,
            p95_latency=p95,
            p99_latency=p99,
            error_rate=error_rate,
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            active_connections=self.active_connections,
            queue_depth=self.queue_depth
        )

    async def _check_alerts(self, snapshot: PerformanceSnapshot):
        """Check for alert conditions"""
        now = datetime.now()
        alerts = []

        # Check RPM threshold
        if snapshot.throughput_rpm < self.alert_thresholds.min_rpm:
            alert_key = "low_throughput"
            if self._should_alert(alert_key, now):
                alerts.append({
                    "type": "WARNING",
                    "metric": "RPM",
                    "value": snapshot.throughput_rpm,
                    "threshold": self.alert_thresholds.min_rpm,
                    "message": f"Low throughput: {snapshot.throughput_rpm:.1f} RPM (target: >{self.alert_thresholds.min_rpm})"
                })

        # Check latency threshold
        if snapshot.p99_latency > self.alert_thresholds.max_p99_latency:
            alert_key = "high_latency"
            if self._should_alert(alert_key, now):
                alerts.append({
                    "type": "WARNING",
                    "metric": "P99_LATENCY",
                    "value": snapshot.p99_latency,
                    "threshold": self.alert_thresholds.max_p99_latency,
                    "message": f"High P99 latency: {snapshot.p99_latency:.2f}s (target: <{self.alert_thresholds.max_p99_latency}s)"
                })

        # Check error rate threshold
        if snapshot.error_rate > self.alert_thresholds.max_error_rate:
            alert_key = "high_error_rate"
            if self._should_alert(alert_key, now):
                alerts.append({
                    "type": "CRITICAL",
                    "metric": "ERROR_RATE",
                    "value": snapshot.error_rate * 100,
                    "threshold": self.alert_thresholds.max_error_rate * 100,
                    "message": f"High error rate: {snapshot.error_rate*100:.1f}% (target: <{self.alert_thresholds.max_error_rate*100:.1f}%)"
                })

        # Check CPU threshold
        if snapshot.cpu_percent > self.alert_thresholds.max_cpu_percent:
            alert_key = "high_cpu"
            if self._should_alert(alert_key, now):
                alerts.append({
                    "type": "WARNING",
                    "metric": "CPU",
                    "value": snapshot.cpu_percent,
                    "threshold": self.alert_thresholds.max_cpu_percent,
                    "message": f"High CPU usage: {snapshot.cpu_percent:.1f}% (target: <{self.alert_thresholds.max_cpu_percent}%)"
                })

        # Check memory threshold
        if snapshot.memory_mb > self.alert_thresholds.max_memory_mb:
            alert_key = "high_memory"
            if self._should_alert(alert_key, now):
                alerts.append({
                    "type": "WARNING",
                    "metric": "MEMORY",
                    "value": snapshot.memory_mb,
                    "threshold": self.alert_thresholds.max_memory_mb,
                    "message": f"High memory usage: {snapshot.memory_mb:.1f}MB (target: <{self.alert_thresholds.max_memory_mb}MB)"
                })

        # Check queue depth threshold
        if snapshot.queue_depth > self.alert_thresholds.max_queue_depth:
            alert_key = "high_queue_depth"
            if self._should_alert(alert_key, now):
                alerts.append({
                    "type": "CRITICAL",
                    "metric": "QUEUE_DEPTH",
                    "value": snapshot.queue_depth,
                    "threshold": self.alert_thresholds.max_queue_depth,
                    "message": f"High queue depth: {snapshot.queue_depth} (target: <{self.alert_thresholds.max_queue_depth})"
                })

        # Log alerts
        for alert in alerts:
            logger.warning(f"PERFORMANCE ALERT: {alert['message']}")
            await self._handle_alert(alert)

    def _should_alert(self, alert_key: str, now: datetime) -> bool:
        """Check if alert should be sent (cooldown logic)"""
        last_alert = self.last_alerts.get(alert_key)
        if not last_alert:
            self.last_alerts[alert_key] = now
            return True

        time_since_last = (now - last_alert).total_seconds()
        if time_since_last >= self.alert_cooldown_seconds:
            self.last_alerts[alert_key] = now
            return True

        return False

    async def _handle_alert(self, alert: Dict[str, Any]):
        """Handle performance alert"""
        # Could integrate with:
        # - Slack notifications
        # - PagerDuty
        # - Email alerts
        # - Custom webhook endpoints
        pass

    def record_submission(self, latency: float, success: bool):
        """Record submission metrics"""
        self.latencies.append(latency)
        if not success:
            self.errors["submission_error"].append(datetime.now())

    def record_agent_latency(self, agent_name: str, latency: float):
        """Record agent latency"""
        self.agent_metrics[agent_name].append({
            "timestamp": datetime.now(),
            "latency": latency
        })

    def record_api_call(self, api_name: str):
        """Record API call"""
        self.api_calls[api_name] += 1

    def update_connections(self, active: int, queue_depth: int = 0):
        """Update connection metrics"""
        self.active_connections = active
        self.queue_depth = queue_depth

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        if not self.snapshots:
            return {"status": "no_data"}

        latest = self.snapshots[-1]

        # Calculate trends
        if len(self.snapshots) >= 2:
            previous = self.snapshots[-2]
            rpm_trend = latest.throughput_rpm - previous.throughput_rpm
            latency_trend = latest.p99_latency - previous.p99_latency
        else:
            rpm_trend = latency_trend = 0.0

        return {
            "status": "active",
            "current": asdict(latest),
            "trends": {
                "rpm_trend": rpm_trend,
                "latency_trend": latency_trend
            },
            "summary": {
                "total_submissions": len(self.latencies),
                "total_errors": sum(len(queue) for queue in self.errors.values()),
                "agents": {
                    name: {
                        "count": len(metrics),
                        "avg_latency": np.mean([m["latency"] for m in metrics]) if metrics else 0.0
                    }
                    for name, metrics in self.agent_metrics.items()
                },
                "api_calls": dict(self.api_calls)
            }
        }


class DashboardReporter:
    """Generate dashboard reports and visualizations"""

    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor

    async def generate_html_dashboard(self) -> str:
        """Generate HTML dashboard"""
        metrics = self.monitor.get_current_metrics()

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>RedditHarbor Performance Dashboard</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .dashboard {{ max-width: 1400px; margin: 0 auto; }}
                .metric-card {{ background: white; padding: 20px; margin: 10px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .metric-value {{ font-size: 2em; font-weight: bold; color: #333; }}
                .metric-label {{ color: #666; font-size: 0.9em; }}
                .status-good {{ color: #4CAF50; }}
                .status-warning {{ color: #FF9800; }}
                .status-critical {{ color: #F44336; }}
                .chart-container {{ height: 300px; margin: 20px 0; }}
                .alert {{ background: #ffebee; padding: 10px; margin: 10px 0; border-radius: 4px; border-left: 4px solid #F44336; }}
                .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .refresh {{ position: fixed; top: 20px; right: 20px; background: #2196F3; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }}
            </style>
        </head>
        <body>
            <button class="refresh" onclick="location.reload()">Refresh</button>
            <div class="dashboard">
                <div class="header">
                    <h1>RedditHarbor Performance Dashboard</h1>
                    <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>

                <div class="grid">
                    <div class="metric-card">
                        <div class="metric-label">Throughput (RPM)</div>
                        <div class="metric-value {self._get_status_class(metrics.get('current', {}).get('throughput_rpm', 0), 800, float('inf'))}">
                            {metrics.get('current', {}).get('throughput_rpm', 0):.1f}
                        </div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-label">P99 Latency (s)</div>
                        <div class="metric-value {self._get_status_class(metrics.get('current', {}).get('p99_latency', 0), 0, 12)}">
                            {metrics.get('current', {}).get('p99_latency', 0):.2f}
                        </div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-label">Error Rate (%)</div>
                        <div class="metric-value {self._get_status_class(metrics.get('current', {}).get('error_rate', 0) * 100, 0, 2)}">
                            {metrics.get('current', {}).get('error_rate', 0) * 100:.2f}
                        </div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-label">CPU Usage (%)</div>
                        <div class="metric-value {self._get_status_class(metrics.get('current', {}).get('cpu_percent', 0), 0, 90)}">
                            {metrics.get('current', {}).get('cpu_percent', 0):.1f}
                        </div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-label">Memory Usage (MB)</div>
                        <div class="metric-value {self._get_status_class(metrics.get('current', {}).get('memory_mb', 0), 0, 8192)}">
                            {metrics.get('current', {}).get('memory_mb', 0):.1f}
                        </div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-label">Queue Depth</div>
                        <div class="metric-value {self._get_status_class(metrics.get('current', {}).get('queue_depth', 0), 0, 1000)}">
                            {metrics.get('current', {}).get('queue_depth', 0)}
                        </div>
                    </div>
                </div>

                <div class="metric-card">
                    <h3>Agent Performance</h3>
                    <div class="grid">
        """

        # Add agent metrics
        for agent_name, agent_data in metrics.get('summary', {}).get('agents', {}).items():
            html += f"""
                        <div style="padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                            <div style="font-weight: bold;">{agent_name}</div>
                            <div>Calls: {agent_data['count']}</div>
                            <div>Avg Latency: {agent_data['avg_latency']:.2f}s</div>
                        </div>
            """

        html += """
                    </div>
                </div>

                <div class="metric-card">
                    <h3>Recent Snapshots</h3>
                    <div class="chart-container">
                        <canvas id="performanceChart"></canvas>
                    </div>
                </div>

                <script>
                    // Performance chart
                    const ctx = document.getElementById('performanceChart').getContext('2d');
                    const performanceChart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: [],
                            datasets: [{
                                label: 'RPM',
                                data: [],
                                borderColor: '#2196F3',
                                yAxisID: 'y',
                                tension: 0.4
                            }, {
                                label: 'P99 Latency (s)',
                                data: [],
                                borderColor: '#FF9800',
                                yAxisID: 'y1',
                                tension: 0.4
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            interaction: {
                                mode: 'index',
                                intersect: false,
                            },
                            scales: {
                                y: {
                                    type: 'linear',
                                    display: true,
                                    position: 'left',
                                    title: { display: true, text: 'RPM' }
                                },
                                y1: {
                                    type: 'linear',
                                    display: true,
                                    position: 'right',
                                    title: { display: true, text: 'Latency (s)' },
                                    grid: { drawOnChartArea: false }
                                }
                            }
                        }
                    });

                    // Auto-refresh every 5 seconds
                    setTimeout(() => location.reload(), 5000);
                </script>
            </div>
        </body>
        </html>
        """

        return html

    def _get_status_class(self, value: float, min_target: float, max_target: float) -> str:
        """Get CSS class based on value status"""
        if min_target <= value <= max_target:
            return "status-good"
        elif value < min_target * 0.8 or value > max_target * 1.2:
            return "status-critical"
        else:
            return "status-warning"

    async def generate_json_report(self) -> Dict[str, Any]:
        """Generate JSON performance report"""
        metrics = self.monitor.get_current_metrics()

        return {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy" if self._is_healthy(metrics) else "degraded",
            "metrics": metrics,
            "targets": {
                "rpm_target": 1000,
                "p99_latency_target": 10.0,
                "error_rate_target": 0.01
            },
            "alerts": self._get_active_alerts(metrics)
        }

    def _is_healthy(self, metrics: Dict[str, Any]) -> bool:
        """Check if system is healthy"""
        current = metrics.get('current', {})
        return (
            current.get('throughput_rpm', 0) >= 800 and
            current.get('p99_latency', 0) <= 12.0 and
            current.get('error_rate', 0) <= 0.02
        )

    def _get_active_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get list of active alerts"""
        alerts = []
        current = metrics.get('current', {})

        if current.get('throughput_rpm', 0) < 800:
            alerts.append({
                "type": "low_throughput",
                "severity": "warning",
                "message": f"Throughput below target: {current.get('throughput_rpm', 0):.1f} RPM"
            })

        if current.get('p99_latency', 0) > 12.0:
            alerts.append({
                "type": "high_latency",
                "severity": "warning",
                "message": f"P99 latency above target: {current.get('p99_latency', 0):.2f}s"
            })

        if current.get('error_rate', 0) > 0.02:
            alerts.append({
                "type": "high_error_rate",
                "severity": "critical",
                "message": f"Error rate above target: {current.get('error_rate', 0)*100:.1f}%"
            })

        return alerts


# Example usage
async def main():
    """Run performance monitoring dashboard"""
    monitor = PerformanceMonitor()
    reporter = DashboardReporter(monitor)

    # Start monitoring
    await monitor.start_monitoring()

    # Simulate some activity
    for i in range(100):
        # Record submission
        latency = np.random.normal(5, 2)  # 5s average latency
        success = np.random.random() > 0.01  # 99% success rate
        monitor.record_submission(latency, success)

        # Record agent metrics
        for agent in ["WTP Analyst", "Market Segment", "Price Point", "Payment Behavior"]:
            agent_latency = np.random.normal(2, 0.5)
            monitor.record_agent_latency(agent, agent_latency)

        # Update connections
        monitor.update_connections(
            active=np.random.randint(10, 50),
            queue_depth=np.random.randint(0, 100)
        )

        await asyncio.sleep(0.1)

    # Generate dashboard
    html = await reporter.generate_html_dashboard()
    with open("/tmp/dashboard.html", "w") as f:
        f.write(html)

    # Generate JSON report
    report = await reporter.generate_json_report()
    with open("/tmp/performance_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("Dashboard generated at /tmp/dashboard.html")
    print("Report generated at /tmp/performance_report.json")

    await monitor.stop_monitoring()


if __name__ == "__main__":
    asyncio.run(main())