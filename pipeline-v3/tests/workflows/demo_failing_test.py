#!/usr/bin/env python3
"""
Demo: Show failing test for set_session_state method
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from workflows.tracked_workflow import TrackedWorkflow

# This test demonstrates the missing set_session_state method
print("=== DEMO: Failing test for set_session_state ===")

workflow = TrackedWorkflow(name="demo_test")
print(f"✅ TrackedWorkflow created with session_id: {workflow.session_id}")
print(f"✅ Initial session_state: {workflow.session_state}")

# This should fail
try:
    workflow.set_session_state("running")
    print(f"✅ set_session_state worked! New state: {workflow.session_state}")
except AttributeError as e:
    print(f"❌ EXPECTED FAILURE: {e}")
    print("This test drives the need for set_session_state method")