#!/usr/bin/env python3
"""
Dashboard Health Monitor
Periodically checks dashboard status and reports issues
"""

import sys
import time
from datetime import datetime
from pathlib import Path

import requests

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_dashboard_health():
    """Check dashboard accessibility and basic functionality"""
    base_url = "http://localhost:5000"
    health_status = {
        "timestamp": datetime.now().isoformat(),
        "dashboard_accessible": False,
        "api_responding": False,
        "response_time_ms": None,
        "status_code": None,
        "error": None
    }

    try:
        # Check main dashboard
        start_time = time.time()
        response = requests.get(base_url, timeout=5)
        response_time = (time.time() - start_time) * 1000

        health_status.update({
            "dashboard_accessible": True,
            "response_time_ms": round(response_time, 2),
            "status_code": response.status_code
        })

        # Check API endpoint
        try:
            api_response = requests.get(f"{base_url}/api/stats", timeout=5)
            health_status["api_responding"] = api_response.status_code == 200
        except Exception as e:
            health_status["api_responding"] = False
            health_status["error"] = str(e)

    except Exception as e:
        health_status["error"] = str(e)

    return health_status

def main():
    """Run dashboard health monitoring"""
    print("=" * 60)
    print("🏥 Dashboard Health Monitor")
    print("=" * 60)
    print("Monitoring: http://localhost:5000")
    print("Press Ctrl+C to stop monitoring")
    print("=" * 60)

    try:
        while True:
            health = check_dashboard_health()

            # Status line
            if health["dashboard_accessible"] and health["api_responding"]:
                status_icon = "✅"
                status_text = "HEALTHY"
            else:
                status_icon = "❌"
                status_text = "ISSUE DETECTED"

            print(f"{status_icon} {health['timestamp'][:19]} - {status_text} | "
                  f"Response: {health['response_time_ms'] or 'N/A'}ms | "
                  f"API: {'OK' if health['api_responding'] else 'FAIL'}")

            # Show error if any
            if health.get("error"):
                print(f"   ⚠️  Error: {health['error']}")

            time.sleep(30)  # Check every 30 seconds

    except KeyboardInterrupt:
        print("\n⏹️  Health monitoring stopped")
        print("Dashboard remains running at: http://localhost:5000")

if __name__ == "__main__":
    main()
