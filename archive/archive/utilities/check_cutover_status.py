#!/usr/bin/env python3
"""
Quick status check for DLT traffic cutover

Provides a snapshot of the current cutover status without running a full cycle.
"""

import json
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_status():
    """Check and display cutover status"""
    config_path = project_root / "config/traffic_cutover_config.json"
    log_path = project_root / "error_log/dlt_traffic_cuttover.log"

    print("=" * 80)
    print("DLT TRAFFIC CUTOVER STATUS")
    print("=" * 80)

    if not config_path.exists():
        print("\n⚠️  No cutover configuration found")
        print("   Run: python scripts/dlt_traffic_cuttover.py --phase 10% --action setup")
        return

    with open(config_path) as f:
        config = json.load(f)

    # Current status
    print(f"\n📊 Current Phase: {config.get('current_phase', 'Not configured')}")
    print(f"   DLT Enabled: {'✓' if config.get('dlt_enabled') else '✗'}")
    print(f"   Manual Enabled: {'✓' if config.get('manual_enabled') else '✗'}")

    # Last run
    if "last_run" in config:
        last_run = config["last_run"]
        timestamp = last_run.get("timestamp", "Unknown")
        print(f"\n⏱️  Last Run: {timestamp}")
        print(f"   DLT Collections: {last_run.get('dlt_count', 0)}")
        print(f"   Manual Collections: {last_run.get('manual_count', 0)}")
        print(f"   Errors: {last_run.get('error_count', 0)}")

    # Next actions
    print("\n" + "=" * 80)
    print("NEXT ACTIONS")
    print("=" * 80)

    phase = config.get("current_phase", "manual_only")

    if phase == "manual_only":
        print("\n1. Setup 10% cutover:")
        print("   python scripts/dlt_traffic_cuttover.py --phase 10% --action setup")
        print("\n2. Run collection cycle:")
        print("   python scripts/dlt_traffic_cuttover.py --phase 10% --action collect")
        print("\n3. Start monitoring:")
        print("   python scripts/dlt_traffic_cuttover.py --phase 10% --action monitor")

    elif phase == "10%":
        print("\n✓ 10% cutover is ACTIVE")
        print("\nMonitoring for 24 hours...")
        print("Check logs: tail -f error_log/dlt_traffic_cuttover.log")

    elif phase == "50%":
        print("\n⚠️  50% cutover is ACTIVE")
        print("\nMonitoring for 48 hours...")

    elif phase == "100%":
        print("\n🚨 100% DLT cutover is ACTIVE")
        print("\nAll traffic is now on DLT pipeline")

    # Logs
    if log_path.exists():
        print("\n" + "=" * 80)
        print("RECENT LOGS (last 10 lines)")
        print("=" * 80)
        with open(log_path) as f:
            lines = f.readlines()[-10:]
            for line in lines:
                print(line.rstrip())
    else:
        print("\n📝 No logs yet (log file will be created on first run)")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_status()
