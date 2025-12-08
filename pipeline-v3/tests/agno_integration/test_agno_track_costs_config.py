#!/usr/bin/env python3
"""
Test for AGNO_TRACK_COSTS configuration in settings.py

This test verifies that the AGNO_TRACK_COSTS configuration is available
in the settings, as required by the audit report.
"""

import pytest

from config.settings import Settings


class TestAgnoTrackCostsConfig:
    """Test that AGNO_TRACK_COSTS configuration is properly defined"""

    def test_agno_track_costs_default_value(self):
        """Test that AGNO_TRACK_COSTS has a default value"""
        settings = Settings.create_for_testing()
        assert hasattr(settings, 'agno_track_costs'), "agno_track_costs should be a settings attribute"
        assert isinstance(settings.agno_track_costs, bool), "agno_track_costs should be a boolean"
        assert settings.agno_track_costs is True, "agno_track_costs should default to True"


def run_test():
    """Run the test directly"""
    test_instance = TestAgnoTrackCostsConfig()

    print("Running test_agno_track_costs_default_value...")
    test_instance.test_agno_track_costs_default_value()
    print("✓ Passed")

    print("\nTest passed!")


if __name__ == "__main__":
    run_test()
