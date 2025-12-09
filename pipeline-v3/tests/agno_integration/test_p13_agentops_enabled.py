#!/usr/bin/env python3
"""
TDD test for agentops_enabled field - P1.3 configuration

Following strict TDD methodology:
1. Write ONE failing test (RED phase)
2. Run it to confirm it fails
3. Write minimal implementation to make it pass (GREEN phase)
4. Refactor if needed (REFACTOR phase)

This is the first test for completing P1.3 configuration.
"""

import sys
from pathlib import Path

# Add parent directory to path to import from pipeline-v3/config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from config.settings import Settings


class TestP13AgentOpsEnabled:
    """Test agentops_enabled field following TDD methodology - one test at a time"""

    def test_agentops_enabled_field_exists_and_default(self):
        """Test that agentops_enabled field exists with correct default

        This test ensures the agentops_enabled field is present to allow
        independent control over AgentOps integration, separate from AGNO_ENABLE_AGENTOPS.

        This is the RED phase - the test should fail because the field doesn't exist yet.
        """
        settings = Settings.create_for_testing()

        # Test attribute exists
        assert hasattr(settings, 'agentops_enabled'), "agentops_enabled should be a settings attribute"

        # Test type is boolean
        assert isinstance(settings.agentops_enabled, bool), "agentops_enabled should be a boolean"

        # Test default value is False (AgentOps disabled by default)
        assert settings.agentops_enabled is False, "agentops_enabled should default to False"


def run_red_phase_test():
    """Run the single test to confirm it fails (RED phase)"""
    test_instance = TestP13AgentOpsEnabled()

    print("=== TDD RED PHASE: Testing agentops_enabled field ===\n")
    print("Running test: test_agentops_enabled_field_exists_and_default...")

    try:
        test_instance.test_agentops_enabled_field_exists_and_default()
        print("✓ Test passed - Unexpected! This test should fail in RED phase")
        return False
    except (AssertionError, AttributeError) as e:
        print(f"✗ Test failed as expected: {type(e).__name__}")
        print(f"  Error: {e}")
        return True
    except Exception as e:
        print(f"✗ Unexpected error: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    success = run_red_phase_test()

    if success:
        print("\n🔴 RED phase successful - Test failed correctly")
        print("📝 Next: Add agentops_enabled field to settings.py (GREEN phase)")
    else:
        print("\n⚠️  Test passed unexpectedly - Check if implementation already exists")