"""
Unit tests for AgnoOpportunityAnalyzer debug mode functionality

These tests verify that the enable_debug parameter is properly stored
and used throughout the AgnoOpportunityAnalyzer implementation.

RED PHASE: This test should FAIL with the current implementation because:
- enable_debug is not stored as an instance variable
"""

import sys
from pathlib import Path

# Add pipeline-v3 to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pipeline-v3"))

import pytest
from transform.agno_analyzer import AgnoOpportunityAnalyzer


class TestAgnoDebugModeStorage:
    """Test that enable_debug parameter is properly stored as instance variable"""

    def test_enable_debug_stored_as_instance_variable_when_true(self):
        """
        Verify enable_debug=True is stored as self.enable_debug
        """
        analyzer = AgnoOpportunityAnalyzer(enable_debug=True)

        assert hasattr(analyzer, 'enable_debug'), "enable_debug should be stored as instance variable"
        assert analyzer.enable_debug is True, "enable_debug should be True when passed as True"

    def test_debug_mode_used_in_agent_initialization(self):
        """
        RED TEST: Verify that self.enable_debug is used (not self.enable_agentops)
        when setting debug_mode for agents

        This test SHOULD FAIL because:
        - Lines 466, 473, 480, 487, 495, 513 incorrectly use self.enable_agentops
        - They should use self.enable_debug instead
        """
        # Create analyzer with debug=True but agentops=False
        analyzer = AgnoOpportunityAnalyzer(enable_debug=True, enable_agentops=False)

        # Verify agents were initialized with debug_mode=True (from self.enable_debug)
        # This should FAIL because current code uses self.enable_agentops (False) not self.enable_debug (True)
        assert analyzer.wtp_agent.debug_mode is True, "WTP agent should have debug_mode=True from enable_debug"
        assert analyzer.segment_agent.debug_mode is True, "Segment agent should have debug_mode=True from enable_debug"
        assert analyzer.price_agent.debug_mode is True, "Price agent should have debug_mode=True from enable_debug"
        assert analyzer.behavior_agent.debug_mode is True, "Behavior agent should have debug_mode=True from enable_debug"
