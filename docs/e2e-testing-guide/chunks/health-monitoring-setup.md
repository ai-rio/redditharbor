# Health Monitoring Setup

<div style="text-align: center; margin: 20px 0;">
  <h1 style="color: #FF6B35;">🏥 Health Monitoring Setup</h1>
  <p style="color: #004E89; font-size: 1.2em;">Real-time integration health monitoring dashboard configuration</p>
</div>

---

## 📋 Overview

This **Health Monitoring Setup** guide provides comprehensive configuration for RedditHarbor's real-time integration health monitoring system. The setup enables continuous monitoring of all 5 production integrations with automated alerting and performance benchmarking.

**What you'll configure:**
1. 📊 **Real-time Dashboard** - Live integration health monitoring
2. 🚨 **Automated Alerting** - Threshold-based notifications
3. 📈 **Performance Benchmarking** - Continuous performance tracking
4. 🔄 **Health Check Automation** - Scheduled validation routines
5. 📋 **Historical Analysis** - Trend monitoring and capacity planning

**Time Investment:** 15 minutes setup, then automated monitoring
**Monitoring Frequency:** Every 5 minutes (configurable)
**Success Threshold:** 100% coverage of all integration components

---

## 🚀 Quick Start Health Monitoring Setup

### **Step 1: Health Monitoring System Installation (3 minutes)**

```bash
# Verify health monitoring components are available
source .venv/bin/activate && python -c "
print('🏥 Health Monitoring System Check')
print('=' * 40)

# Check health monitoring script availability
import os
health_script = 'scripts/analysis/monitor_integration_health.py'
if os.path.exists(health_script):
    print('✅ Health Monitor Script: Available')
else:
    print('❌ Health Monitor Script: Missing')
    exit(1)

# Check required dependencies for monitoring
try:
    import asyncio
    import aiohttp
    import subprocess
    print('✅ Monitoring Dependencies: Available')
except ImportError as e:
    print(f'❌ Monitoring Dependencies: Missing {e}')
    print('Run: pip install aiohttp')
    exit(1)

# Check environment variables for all integrations
required_vars = ['AGENTOPS_API_KEY', 'OPENROUTER_API_KEY', 'JINA_API_KEY', 'DATABASE_URL']
configured_vars = [var for var in required_vars if os.getenv(var)]

print(f'✅ Environment Configuration: {len(configured_vars)}/{len(required_vars)} variables')
if len(configured_vars) < len(required_vars):
    missing = set(required_vars) - set(configured_vars)
    print(f'⚠️  Missing: {missing}')

print('\\n🎯 Health Monitoring System: Ready for setup')
"
```

### **Step 2: Real-time Health Dashboard Configuration (4 minutes)**

```bash
# Run comprehensive health check to establish baseline
source .venv/bin/activate && python scripts/analysis/monitor_integration_health.py

# Create a monitoring dashboard configuration file
cat > scripts/config/health_monitoring_config.json << 'EOF'
{
  "monitoring_settings": {
    "check_interval_seconds": 300,
    "alert_thresholds": {
      "response_time_warning_ms": 500,
      "response_time_critical_ms": 2000,
      "success_rate_warning": 90,
      "success_rate_critical": 75,
      "error_rate_warning": 10,
      "error_rate_critical": 25
    },
    "components": {
      "agno_multi_agent": {
        "enabled": true,
        "timeout_seconds": 75,
        "expected_performance": {
          "min_wtp_score": 0,
          "max_wtp_score": 100,
          "valid_segments": ["B2B", "B2C"]
        }
      },
      "agentops_observability": {
        "enabled": true,
        "timeout_seconds": 5,
        "expected_performance": {
          "max_latency_ms": 500,
          "dashboard_accessible": true
        }
      },
      "jina_mcp_hybrid": {
        "enabled": true,
        "timeout_seconds": 10,
        "expected_performance": {
          "success_rate_min": 80,
          "max_response_time_ms": 5000
        }
      },
      "supabase_database": {
        "enabled": true,
        "timeout_seconds": 5,
        "expected_performance": {
          "max_query_time_ms": 300,
          "min_table_count": 5
        }
      },
      "environment_config": {
        "enabled": true,
        "timeout_seconds": 2,
        "expected_performance": {
          "required_vars_count": 4,
          "supabase_running": true
        }
      }
    },
    "notifications": {
      "console_alerts": true,
      "file_logging": true,
      "dashboard_updates": true
    },
    "logging": {
      "log_directory": "logs/health_monitoring",
      "retention_days": 30,
      "log_level": "INFO"
    }
  }
}
EOF

echo "✅ Health monitoring configuration created"
echo "📊 Configuration file: scripts/config/health_monitoring_config.json"
```

### **Step 3: Automated Health Check Scheduling (3 minutes)**

```bash
# Create automated health monitoring script
cat > scripts/monitoring/automated_health_monitor.sh << 'EOF'
#!/bin/bash

# RedditHarbor Automated Health Monitor
# Runs comprehensive health checks and updates dashboard

echo "🏥 RedditHarbor Health Monitor - $(date)"
echo "=========================================="

# Navigate to project directory
cd "$(dirname "$0")/../.."

# Activate virtual environment
source .venv/bin/activate

# Run health check with JSON output for dashboard
HEALTH_OUTPUT=$(python scripts/analysis/monitor_integration_health.py --json 2>/dev/null)
EXIT_CODE=$?

# Log results
echo "Health Check Exit Code: $EXIT_CODE"
echo "Health Check Results: $HEALTH_OUTPUT"

# Create health status file for dashboard consumption
echo "$HEALTH_OUTPUT" > logs/latest_health_check.json

# Update dashboard if available
if [ -f "scripts/monitoring/update_dashboard.py" ]; then
    python scripts/monitoring/update_dashboard.py --health-data "$HEALTH_OUTPUT"
fi

# Send alerts if needed (simple console alert for now)
if [ $EXIT_CODE -ne 0 ]; then
    echo "🚨 HEALTH ALERT: Integration issues detected"
    echo "Check logs for detailed information"
fi

echo "Health monitoring completed at $(date)"
echo "=========================================="
EOF

chmod +x scripts/monitoring/automated_health_monitor.sh

# Create log directory structure
mkdir -p logs/health_monitoring
mkdir -p logs/health_monitoring/historical

echo "✅ Automated health monitor script created"
echo "📁 Log directories created"
echo "🔄 Scheduling: Run 'scripts/monitoring/automated_health_monitor.sh' every 5 minutes"
```

### **Step 4: Health Dashboard Visualization Setup (5 minutes)**

```bash
# Create a simple health dashboard
cat > scripts/monitoring/health_dashboard.py << 'EOF'
#!/usr/bin/env python3
"""
RedditHarbor Health Monitoring Dashboard
Real-time visualization of integration health status
"""

import json
import time
import os
from datetime import datetime, timedelta
from pathlib import Path

class HealthDashboard:
    def __init__(self):
        self.health_log_dir = Path("logs/health_monitoring")
        self.latest_health_file = Path("logs/latest_health_check.json")

    def load_latest_health_data(self):
        """Load the most recent health check data"""
        if self.latest_health_file.exists():
            try:
                with open(self.latest_health_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading health data: {e}")
                return None
        return None

    def display_health_dashboard(self):
        """Display real-time health dashboard"""
        os.system('clear')

        print("🏥 REDDITHARBOR INTEGRATION HEALTH DASHBOARD")
        print("=" * 60)
        print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        health_data = self.load_latest_health_data()

        if not health_data:
            print("❌ No health data available")
            print("Run: python scripts/analysis/monitor_integration_health.py")
            return

        # Display overall status
        overall_status = health_data.get('overall_status', 'unknown')
        healthy_count = health_data.get('healthy_components', 0)
        degraded_count = health_data.get('degraded_components', 0)
        unhealthy_count = health_data.get('unhealthy_components', 0)
        total_components = health_data.get('total_components', 0)

        status_color = {
            'healthy': '✅',
            'degraded': '⚠️',
            'unhealthy': '❌'
        }.get(overall_status, '❓')

        print(f"\n📊 OVERALL STATUS: {status_color} {overall_status.upper()}")
        print(f"   Healthy: {healthy_count} ✅")
        print(f"   Degraded: {degraded_count} ⚠️")
        print(f"   Unhealthy: {unhealthy_count} ❌")
        print(f"   Total: {total_components}")

        # Display component details
        health_checks = health_data.get('health_checks', [])
        if health_checks:
            print(f"\n🔍 COMPONENT DETAILS:")
            for check in health_checks:
                component = check.get('component', 'unknown')
                status = check.get('status', 'unknown')
                latency = check.get('latency_ms', 0)
                last_check = check.get('last_check', '')

                status_icon = {
                    'healthy': '✅',
                    'degraded': '⚠️',
                    'unhealthy': '❌'
                }.get(status, '❓')

                print(f"\n   {status_icon} {component.upper()}")
                print(f"      Status: {status}")
                print(f"      Latency: {latency:.1f}ms")
                print(f"      Last Check: {last_check}")

                # Show error if present
                error_msg = check.get('error_message')
                if error_msg:
                    print(f"      Error: {error_msg[:60]}...")

                # Show metrics if available
                metrics = check.get('metrics')
                if metrics:
                    print(f"      Metrics: {json.dumps(metrics, indent=8)}")

        # Display system metrics
        system_metrics = health_data.get('system_metrics', {})
        if system_metrics:
            print(f"\n📈 SYSTEM METRICS:")
            uptime = system_metrics.get('monitoring_uptime_seconds', 0)
            avg_latency = system_metrics.get('average_latency_ms', 0)
            total_checks = system_metrics.get('total_checks_run', 0)

            print(f"   Monitoring Uptime: {uptime/3600:.1f} hours")
            print(f"   Average Latency: {avg_latency:.1f}ms")
            print(f"   Total Checks Run: {total_checks}")

        # Display recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if overall_status == 'healthy':
            print("   ✅ All integrations healthy - system ready for production")
        elif overall_status == 'degraded':
            print("   ⚠️  Some integrations degraded - review warnings above")
        else:
            print("   ❌ Critical issues detected - immediate attention required")

        print(f"\n🔄 Next update in 30 seconds...")
        print(f"📊 Detailed logs: {self.health_log_dir}/")
        print(f"🎯 Manual check: python scripts/analysis/monitor_integration_health.py")

def main():
    """Run the health monitoring dashboard"""
    dashboard = HealthDashboard()

    try:
        while True:
            dashboard.display_health_dashboard()
            time.sleep(30)  # Update every 30 seconds
    except KeyboardInterrupt:
        print("\n\n🏥 Health monitoring dashboard stopped")
        print("✅ Monitoring session completed")

if __name__ == "__main__":
    main()
EOF

chmod +x scripts/monitoring/health_dashboard.py

echo "✅ Health monitoring dashboard created"
echo "🖥️  Start dashboard: python scripts/monitoring/health_dashboard.py"
echo "📊 Dashboard updates every 30 seconds automatically"
```

---

## 📊 Advanced Health Monitoring Configuration

### **Scenario 1: Custom Alert Thresholds**

```bash
# Configure custom alert thresholds for specific components
cat > scripts/config/custom_alert_thresholds.json << 'EOF'
{
  "custom_thresholds": {
    "agno_multi_agent": {
      "performance_thresholds": {
        "max_analysis_time_seconds": 60,
        "min_success_rate": 85,
        "max_wtp_score_variance": 20
      },
      "cost_alerts": {
        "max_cost_per_analysis": 0.0001,
        "daily_cost_budget": 0.01
      }
    },
    "agentops_observability": {
      "performance_thresholds": {
        "max_trace_creation_time_ms": 500,
        "max_dashboard_latency_ms": 1000,
        "min_event_recording_success": 99
      },
      "connectivity_alerts": {
        "max_consecutive_failures": 3,
        "dashboard_access_timeout": 5
      }
    },
    "jina_mcp_hybrid": {
      "performance_thresholds": {
        "max_url_reading_time_seconds": 5,
        "min_search_success_rate": 80,
        "max_api_response_time_ms": 3000
      },
      "rate_limit_alerts": {
        "warning_threshold_percent": 80,
        "critical_threshold_percent": 95
      }
    },
    "supabase_database": {
      "performance_thresholds": {
        "max_query_time_ms": 300,
        "max_connection_time_ms": 100,
        "min_table_access_success": 99.5
      },
      "storage_alerts": {
        "max_storage_usage_percent": 80,
        "min_available_connections": 5
      }
    }
  },
  "notification_settings": {
    "alert_cooldown_minutes": 15,
    "escalation_rules": {
      "critical_alerts": {
        "immediate_notification": true,
        "escalation_after_minutes": 5
      },
      "warning_alerts": {
        "immediate_notification": false,
        "escalation_after_minutes": 30
      }
    }
  }
}
EOF

echo "✅ Custom alert thresholds configured"
echo "📁 Configuration: scripts/config/custom_alert_thresholds.json"
```

### **Scenario 2: Historical Trend Monitoring**

```bash
# Create historical trend monitoring script
cat > scripts/monitoring/trend_monitor.py << 'EOF'
#!/usr/bin/env python3
"""
RedditHarbor Historical Trend Monitoring
Analyzes health check trends over time for capacity planning
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import statistics

class TrendMonitor:
    def __init__(self):
        self.health_log_dir = Path("logs/health_monitoring/historical")
        self.health_log_dir.mkdir(parents=True, exist_ok=True)

    def save_historical_data(self, health_data):
        """Save health data for historical analysis"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"health_check_{timestamp}.json"
        filepath = self.health_log_dir / filename

        # Add timestamp to data
        health_data['saved_at'] = timestamp
        health_data['unix_timestamp'] = datetime.now().timestamp()

        try:
            with open(filepath, 'w') as f:
                json.dump(health_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving historical data: {e}")
            return False

    def analyze_trends(self, days=7):
        """Analyze health trends over specified period"""
        cutoff_date = datetime.now() - timedelta(days=days)

        # Find historical files within period
        historical_data = []
        for file_path in self.health_log_dir.glob("health_check_*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                # Parse timestamp from filename
                timestamp_str = file_path.stem.replace('health_check_', '')
                file_datetime = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')

                if file_datetime >= cutoff_date:
                    historical_data.append({
                        'data': data,
                        'timestamp': file_datetime
                    })
            except Exception as e:
                continue

        if not historical_data:
            return None

        # Analyze component trends
        component_trends = {}

        for record in historical_data:
            health_checks = record['data'].get('health_checks', [])

            for check in health_checks:
                component = check.get('component', 'unknown')
                status = check.get('status', 'unknown')
                latency = check.get('latency_ms', 0)

                if component not in component_trends:
                    component_trends[component] = {
                        'statuses': [],
                        'latencies': [],
                        'errors': []
                    }

                component_trends[component]['statuses'].append(status)
                component_trends[component]['latencies'].append(latency)

                if check.get('error_message'):
                    component_trends[component]['errors'].append(check['error_message'])

        # Calculate trend metrics
        trend_analysis = {}
        for component, data in component_trends.items():
            statuses = data['statuses']
            latencies = data['latencies']
            errors = data['errors']

            # Status distribution
            healthy_count = statuses.count('healthy')
            degraded_count = statuses.count('degraded')
            unhealthy_count = statuses.count('unhealthy')
            total_checks = len(statuses)

            # Performance metrics
            if latencies:
                avg_latency = statistics.mean(latencies)
                min_latency = min(latencies)
                max_latency = max(latencies)
                latency_stability = statistics.stdev(latencies) if len(latencies) > 1 else 0
            else:
                avg_latency = min_latency = max_latency = latency_stability = 0

            trend_analysis[component] = {
                'total_checks': total_checks,
                'health_distribution': {
                    'healthy': healthy_count,
                    'degraded': degraded_count,
                    'unhealthy': unhealthy_count
                },
                'health_percentage': (healthy_count / total_checks) * 100 if total_checks > 0 else 0,
                'performance': {
                    'avg_latency_ms': avg_latency,
                    'min_latency_ms': min_latency,
                    'max_latency_ms': max_latency,
                    'latency_stability': latency_stability
                },
                'error_count': len(errors),
                'most_recent_status': statuses[-1] if statuses else 'unknown',
                'trend_direction': self._calculate_trend(statuses)
            }

        return {
            'analysis_period_days': days,
            'total_analyzed_checks': len(historical_data),
            'analysis_timestamp': datetime.now().isoformat(),
            'component_trends': trend_analysis
        }

    def _calculate_trend(self, statuses):
        """Simple trend calculation based on recent vs older status"""
        if len(statuses) < 4:
            return 'insufficient_data'

        recent = statuses[-2:]  # Last 2 checks
        older = statuses[-4:-2]  # Previous 2 checks

        recent_healthy = recent.count('healthy')
        older_healthy = older.count('healthy')

        if recent_healthy > older_healthy:
            return 'improving'
        elif recent_healthy < older_healthy:
            return 'degrading'
        else:
            return 'stable'

    def display_trend_report(self, days=7):
        """Display comprehensive trend analysis"""
        trend_data = self.analyze_trends(days)

        if not trend_data:
            print("❌ No historical data available for trend analysis")
            return

        print(f"📈 REDDITHARBOR HEALTH TREND ANALYSIS")
        print(f"Analysis Period: {days} days")
        print(f"Analyzed Checks: {trend_data['total_analyzed_checks']}")
        print("=" * 60)

        for component, data in trend_data['component_trends'].items():
            print(f"\n🔍 {component.upper()}")
            print(f"   Health Score: {data['health_percentage']:.1f}%")
            print(f"   Total Checks: {data['total_checks']}")
            print(f"   Status Distribution: ✅{data['health_distribution']['healthy']} "
                  f"⚠️{data['health_distribution']['degraded']} "
                  f"❌{data['health_distribution']['unhealthy']}")
            print(f"   Trend: {data['trend_direction']}")
            print(f"   Performance: {data['performance']['avg_latency_ms']:.1f}ms avg latency")
            print(f"   Errors: {data['error_count']}")

def main():
    """Run trend analysis"""
    monitor = TrendMonitor()

    # Save current health data (would be called from health check)
    # monitor.save_historical_data(current_health_data)

    # Display trend analysis
    monitor.display_trend_report(days=7)

if __name__ == "__main__":
    main()
EOF

chmod +x scripts/monitoring/trend_monitor.py

echo "✅ Historical trend monitoring configured"
echo "📈 Run analysis: python scripts/monitoring/trend_monitor.py"
```

### **Scenario 3: Automated Alerting System**

```bash
# Create automated alerting system
cat > scripts/monitoring/alert_system.py << 'EOF'
#!/usr/bin/env python3
"""
RedditHarbor Automated Alerting System
Sends notifications based on health monitoring thresholds
"""

import json
import smtplib
import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

class AlertSystem:
    def __init__(self):
        self.config_file = Path("scripts/config/health_monitoring_config.json")
        self.alert_log_file = Path("logs/health_monitoring/alerts.log")
        self.alert_log_file.parent.mkdir(parents=True, exist_ok=True)

    def load_config(self):
        """Load monitoring configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
        return {}

    def check_alert_conditions(self, health_data):
        """Check if alert conditions are met"""
        config = self.load_config()
        thresholds = config.get('monitoring_settings', {}).get('alert_thresholds', {})
        alerts = []

        # Check overall system health
        overall_status = health_data.get('overall_status', 'unknown')
        if overall_status == 'unhealthy':
            alerts.append({
                'severity': 'critical',
                'component': 'system',
                'message': 'Overall system health is unhealthy',
                'details': f"Unhealthy components: {health_data.get('unhealthy_components', 0)}"
            })
        elif overall_status == 'degraded':
            alerts.append({
                'severity': 'warning',
                'component': 'system',
                'message': 'System health is degraded',
                'details': f"Degraded components: {health_data.get('degraded_components', 0)}"
            })

        # Check individual component performance
        health_checks = health_data.get('health_checks', [])
        for check in health_checks:
            component = check.get('component', 'unknown')
            status = check.get('status', 'unknown')
            latency = check.get('latency_ms', 0)

            # Performance alerts
            if latency > thresholds.get('response_time_critical_ms', 2000):
                alerts.append({
                    'severity': 'critical',
                    'component': component,
                    'message': f'Critical latency detected: {latency:.1f}ms',
                    'details': f"Component {component} response time exceeds critical threshold"
                })
            elif latency > thresholds.get('response_time_warning_ms', 500):
                alerts.append({
                    'severity': 'warning',
                    'component': component,
                    'message': f'High latency detected: {latency:.1f}ms',
                    'details': f"Component {component} response time exceeds warning threshold"
                })

            # Status alerts
            if status == 'unhealthy':
                alerts.append({
                    'severity': 'critical',
                    'component': component,
                    'message': f'Component {component} is unhealthy',
                    'details': check.get('error_message', 'No details available')
                })
            elif status == 'degraded':
                alerts.append({
                    'severity': 'warning',
                    'component': component,
                    'message': f'Component {component} is degraded',
                    'details': check.get('error_message', 'Performance degraded')
                })

        return alerts

    def should_send_alert(self, alert):
        """Check if alert should be sent (rate limiting)"""
        # Simple rate limiting - don't send same alert within 15 minutes
        cooldown_minutes = 15
        cutoff_time = datetime.now() - timedelta(minutes=cooldown_minutes)

        if not self.alert_log_file.exists():
            return True

        try:
            with open(self.alert_log_file, 'r') as f:
                recent_alerts = []
                for line in f:
                    try:
                        alert_data = json.loads(line.strip())
                        alert_time = datetime.fromisoformat(alert_data.get('timestamp', ''))
                        if alert_time > cutoff_time:
                            recent_alerts.append(alert_data)
                    except:
                        continue

            # Check if similar alert was sent recently
            for recent_alert in recent_alerts:
                if (recent_alert.get('component') == alert['component'] and
                    recent_alert.get('severity') == alert['severity']):
                    return False

            return True
        except:
            return True

    def log_alert(self, alert):
        """Log alert for tracking and rate limiting"""
        alert_entry = {
            'timestamp': datetime.now().isoformat(),
            'severity': alert['severity'],
            'component': alert['component'],
            'message': alert['message'],
            'details': alert['details']
        }

        try:
            with open(self.alert_log_file, 'a') as f:
                f.write(json.dumps(alert_entry) + '\n')
        except Exception as e:
            print(f"Error logging alert: {e}")

    def send_console_alert(self, alert):
        """Send alert to console"""
        severity_icons = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️'
        }

        icon = severity_icons.get(alert['severity'], '📢')
        print(f"\n{icon} INTEGRATION HEALTH ALERT")
        print(f"Component: {alert['component']}")
        print(f"Severity: {alert['severity']}")
        print(f"Message: {alert['message']}")
        print(f"Details: {alert['details']}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 50)

    def process_health_data(self, health_data):
        """Process health data and send alerts if needed"""
        alerts = self.check_alert_conditions(health_data)

        if not alerts:
            print("✅ No alerts triggered - all systems healthy")
            return

        sent_alerts = 0
        for alert in alerts:
            if self.should_send_alert(alert):
                self.send_console_alert(alert)
                self.log_alert(alert)
                sent_alerts += 1
            else:
                print(f"🔕 Alert rate-limited: {alert['component']} - {alert['severity']}")

        if sent_alerts > 0:
            print(f"\n📊 Alert Summary: {sent_alerts} alerts sent")
        else:
            print(f"\n📊 Alert Summary: {len(alerts)} alerts detected, {sent_alerts} sent (rate limited)")

def main():
    """Process health data and send alerts"""
    import sys

    if len(sys.argv) > 1:
        # Load health data from file
        health_file = sys.argv[1]
        try:
            with open(health_file, 'r') as f:
                health_data = json.load(f)
        except Exception as e:
            print(f"Error loading health data: {e}")
            return
    else:
        print("Usage: python alert_system.py <health_data_file>")
        return

    # Process alerts
    alert_system = AlertSystem()
    alert_system.process_health_data(health_data)

if __name__ == "__main__":
    main()
EOF

chmod +x scripts/monitoring/alert_system.py

echo "✅ Automated alerting system configured"
echo "🚨 Alert processing: python scripts/monitoring/alert_system.py <health_data.json>"
```

---

## 📈 Health Monitoring Performance Analysis

### **Real-time Monitoring Dashboard Commands**

```bash
# Start real-time health monitoring dashboard
start_health_dashboard() {
    echo "🏥 Starting RedditHarbor Health Monitoring Dashboard"
    echo "=================================================="

    cd /home/carlos/projects/redditharbor
    source .venv/bin/activate

    # Create logs directory if it doesn't exist
    mkdir -p logs/health_monitoring

    # Run initial health check
    echo "Running initial health check..."
    python scripts/analysis/monitor_integration_health.py

    # Start dashboard
    echo "Starting real-time dashboard..."
    echo "Press Ctrl+C to stop monitoring"
    python scripts/monitoring/health_dashboard.py
}

# Usage: start_health_dashboard
```

### **Historical Performance Analysis**

```bash
# Analyze historical performance trends
analyze_health_trends() {
    echo "📈 RedditHarbor Health Trend Analysis"
    echo "===================================="

    cd /home/carlos/projects/redditharbor
    source .venv/bin/activate

    # Run trend analysis for different periods
    echo "Analyzing 7-day trends..."
    python scripts/monitoring/trend_monitor.py

    echo
    echo "📊 Performance Metrics Summary:"
    echo "- Component health percentages over time"
    echo "- Latency trends and stability analysis"
    echo "- Error pattern identification"
    echo "- Capacity planning recommendations"
}

# Usage: analyze_health_trends
```

### **Health Monitoring Status Check**

```bash
# Quick health monitoring status check
health_monitoring_status() {
    echo "🏥 RedditHarbor Health Monitoring Status"
    echo "======================================="

    echo "📁 Configuration Files:"
    [ -f "scripts/config/health_monitoring_config.json" ] && echo "   ✅ Main configuration" || echo "   ❌ Main configuration missing"
    [ -f "scripts/config/custom_alert_thresholds.json" ] && echo "   ✅ Custom thresholds" || echo "   ⚠️  Custom thresholds not configured"

    echo
    echo "🔧 Monitoring Scripts:"
    [ -f "scripts/analysis/monitor_integration_health.py" ] && echo "   ✅ Health monitor script" || echo "   ❌ Health monitor missing"
    [ -f "scripts/monitoring/health_dashboard.py" ] && echo "   ✅ Dashboard script" || echo "   ❌ Dashboard script missing"
    [ -f "scripts/monitoring/alert_system.py" ] && echo "   ✅ Alert system" || echo "   ❌ Alert system missing"
    [ -f "scripts/monitoring/trend_monitor.py" ] && echo "   ✅ Trend monitor" || echo "   ❌ Trend monitor missing"

    echo
    echo "📊 Log Files:"
    [ -f "logs/latest_health_check.json" ] && echo "   ✅ Latest health check" || echo "   ❌ No recent health checks"
    [ -d "logs/health_monitoring" ] && echo "   ✅ Health monitoring logs" || echo "   ❌ Log directory missing"

    echo
    echo "🔄 Automated Monitoring:"
    if pgrep -f "automated_health_monitor.sh" > /dev/null; then
        echo "   ✅ Automated monitoring running"
    else
        echo "   ⚠️  Automated monitoring not running"
        echo "      Start with: ./scripts/monitoring/automated_health_monitor.sh"
    fi

    echo
    echo "🎯 Quick Actions:"
    echo "   Run health check: python scripts/analysis/monitor_integration_health.py"
    echo "   Start dashboard: python scripts/monitoring/health_dashboard.py"
    echo "   View trends: python scripts/monitoring/trend_monitor.py"
}

# Usage: health_monitoring_status
```

---

## 🎯 Success Indicators

### **When Health Monitoring Setup is Successful:**

1. **✅ Real-time Dashboard**: Live health status updates every 30 seconds
2. **✅ Automated Monitoring**: Scheduled health checks every 5 minutes
3. **✅ Alert System**: Threshold-based notifications with rate limiting
4. **✅ Historical Analysis**: Trend monitoring and capacity planning
5. **✅ Performance Benchmarking**: Continuous performance tracking

### **Expected Monitoring Performance:**

| Metric | Target | Acceptable Range |
|--------|--------|------------------|
| **Dashboard Update Frequency** | 30s | 15-60s |
| **Health Check Interval** | 5min | 3-10min |
| **Alert Response Time** | <1min | 30s-5min |
| **Historical Data Retention** | 30 days | 7-90 days |
| **System Resource Usage** | <5% CPU | 2-10% CPU |

### **Troubleshooting Common Issues:**

#### **❌ Health Monitor Script Not Found**
```bash
# Verify script installation
ls -la scripts/analysis/monitor_integration_health.py

# If missing, reinstall dependencies
cd /home/carlos/projects/redditharbor
source .venv/bin/activate
python scripts/analysis/monitor_integration_health.py
```

#### **❌ Dashboard Not Updating**
```bash
# Check latest health data
ls -la logs/latest_health_check.json

# Run manual health check
python scripts/analysis/monitor_integration_health.py --json > logs/latest_health_check.json

# Restart dashboard
python scripts/monitoring/health_dashboard.py
```

#### **❌ Alerts Not Sending**
```bash
# Check alert configuration
cat scripts/config/health_monitoring_config.json | jq '.notifications'

# Test alert system manually
echo '{"overall_status":"unhealthy","health_checks":[]}' | python scripts/monitoring/alert_system.py /dev/stdin
```

---

## 📚 Additional Resources

### **Related Documentation:**
- **[Integration Validation Quickstart](./integration-validation-quickstart.md)** - Basic integration testing
- **[Observability Testing](./observability-testing.md)** - AgentOps dashboard setup
- **[Production Pipeline Testing](./production-pipeline-testing.md)** - End-to-end production testing
- **[Production Deployment Integration](./production-deployment-integration.md)** - Deployment monitoring

### **Quick Reference Commands:**
```bash
# Start monitoring dashboard
start_health_dashboard

# Check monitoring status
health_monitoring_status

# Analyze trends
analyze_health_trends

# Manual health check
python scripts/analysis/monitor_integration_health.py

# Process alerts
python scripts/monitoring/alert_system.py logs/latest_health_check.json
```

---

<div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 2px solid #F5F5F5;">
  <p style="color: #666; font-size: 0.9em;">
    Continue with <a href="./production-pipeline-testing.md" style="color: #004E89; font-weight: bold;">Production Pipeline Testing</a> to validate end-to-end production workflows! 🏭
  </p>
</div>