#!/usr/bin/env python3
"""
Test to verify the AGNO_TRACK_COSTS configuration requirement based on audit report
"""

import sys
from pathlib import Path


def test_audit_report_requirement():
    """
    Test based on audit report requirement:
    "AGNO_TRACK_COSTS=true not found in settings"
    """
    # Read the settings file
    settings_path = Path(__file__).parent / "config" / "settings.py"
    settings_content = settings_path.read_text()

    # Check if AGNO_TRACK_COSTS is defined
    if 'agno_track_costs' not in settings_content:
        print("FAIL: agno_track_costs configuration not found in settings.py")
        print("Audit report requirement: 'AGNO_TRACK_COSTS=true not found in settings'")
        return False

    # Check if it's properly configured with the AGNO_TRACK_COSTS alias
    if 'AGNO_TRACK_COSTS' not in settings_content:
        print("FAIL: AGNO_TRACK_COSTS alias not found in settings.py")
        return False

    print("PASS: agno_track_costs configuration found in settings.py")
    return True

if __name__ == "__main__":
    success = test_audit_report_requirement()
    sys.exit(0 if success else 1)
