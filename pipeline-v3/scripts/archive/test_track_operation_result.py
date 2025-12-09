#!/usr/bin/env python3
"""
Test track_operation_result method implementation
"""

import sys
from pathlib import Path

# Add current directory to path so we can import
sys.path.insert(0, str(Path(__file__).parent))

def test_track_operation_result():
    """Test that track_operation_result method works"""
    try:
        from tests.test_agentops_integration import MockAgentOpsTracker

        tracker = MockAgentOpsTracker()

        # This should work now
        tracker.track_operation_result("test_op", True)

        print("✅ SUCCESS: track_operation_result method works!")
        return True

    except AttributeError as e:
        print(f"❌ FAILURE: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_track_operation_result()
    exit(0 if success else 1)
