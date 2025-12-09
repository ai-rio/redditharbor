#!/usr/bin/env python3
"""
Single test for Agno cost tracking configuration - TDD RED phase

This is the first test in the TDD cycle. It tests the most basic requirement:
that agno_track_costs configuration exists in settings.py.

Following strict TDD methodology:
1. Write ONE failing test (RED phase)
2. Run it to confirm it fails
3. Write minimal implementation to make it pass (GREEN phase)
4. Refactor if needed (REFACTOR phase)
"""

import pytest

from config.settings import Settings


class TestAgnoCostConfiguration:
    """Test Agno cost tracking configuration - one test at a time"""

    def test_agno_track_costs_exists_and_default(self):
        """Test that agno_track_costs exists and has correct default

        This is the first test in the TDD cycle for P1.3.
        It tests the most basic requirement: the agno_track_costs setting exists.
        """
        settings = Settings.create_for_testing()

        # Test attribute exists
        assert hasattr(settings, 'agno_track_costs'), "agno_track_costs should be a settings attribute"

        # Test type is boolean
        assert isinstance(settings.agno_track_costs, bool), "agno_track_costs should be a boolean"

        # Test default value is True (cost tracking enabled by default)
        assert settings.agno_track_costs is True, "agno_track_costs should default to True"

    def test_agno_debug_mode_exists_and_default(self):
        """Test that agno_debug_mode exists and has correct default"""
        settings = Settings.create_for_testing()

        # Test attribute exists
        assert hasattr(settings, 'agno_debug_mode'), "agno_debug_mode should be a settings attribute"

        # Test type is boolean
        assert isinstance(settings.agno_debug_mode, bool), "agno_debug_mode should be a boolean"

        # Test default value is False (debug mode disabled by default)
        assert settings.agno_debug_mode is False, "agno_debug_mode should default to False"

    def test_agentops_api_key_exists_and_default(self):
        """Test that agentops_api_key exists and has correct default"""
        settings = Settings.create_for_testing()

        # Test attribute exists
        assert hasattr(settings, 'agentops_api_key'), "agentops_api_key should be a settings attribute"

        # Test type is string
        assert isinstance(settings.agentops_api_key, str), "agentops_api_key should be a string"

        # Test default value is empty string
        assert settings.agentops_api_key == "", "agentops_api_key should default to empty string"

    def test_agentops_enabled_exists_and_default(self):
        """Test that agentops_enabled exists and has correct default"""
        settings = Settings.create_for_testing()

        # Test attribute exists
        assert hasattr(settings, 'agentops_enabled'), "agentops_enabled should be a settings attribute"

        # Test type is boolean
        assert isinstance(settings.agentops_enabled, bool), "agentops_enabled should be a boolean"

        # Test default value is False (disabled by default)
        assert settings.agentops_enabled is False, "agentops_enabled should default to False"


def run_single_test():
    """Run the single test to confirm it fails (RED phase)"""
    test_instance = TestAgnoCostConfiguration()

    print("Running single test: test_agno_track_costs_exists_and_default...")
    try:
        test_instance.test_agno_track_costs_exists_and_default()
        print("✓ Test passed - but it should have failed in RED phase!")
        return True
    except AssertionError as e:
        print(f"✗ Test failed as expected: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = run_single_test()
    if not success:
        print("\nTest failed correctly - now implement minimal code in GREEN phase")
    else:
        print("\nTest passed unexpectedly - check if implementation already exists")