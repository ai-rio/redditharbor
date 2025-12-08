#!/usr/bin/env python3
"""
Test TC-002: Basic Method Existence for BaseAgent a_run() method

This test is designed to fail initially since the a_run method
doesn't exist yet. This follows the TDD approach.
"""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from agno.models.openai import OpenAIChat

# Import the actual implementation
from transform.agno_agents import BaseAgent


class TestBaseAgentARunTC002:
    """Test class for TC-002: BaseAgent a_run Method Existence"""

    def test_a_run_method_exists(self):
        """TC-002: Verify that a_run method exists in BaseAgent"""
        # Arrange
        model = OpenAIChat(
            id="test-model",
            api_key="test-key",
            base_url="https://api.test.com"
        )

        # Create a minimal BaseAgent instance
        agent = BaseAgent(
            model="test-model",
            api_key="test-key",
            base_url="https://api.test.com",
            enable_agentops=False
        )

        # Act & Assert
        assert hasattr(agent, 'a_run'), "a_run method should exist in BaseAgent"


def run_test():
    """Run the test directly"""
    test_instance = TestBaseAgentARunTC002()
    try:
        test_instance.test_a_run_method_exists()
        print("✅ TC-002 PASSED: a_run method exists")
        return True
    except AssertionError as e:
        print(f"❌ TC-002 FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ TC-002 ERROR: {e}")
        return False


if __name__ == "__main__":
    # Run test directly for debugging
    success = run_test()
    exit(0 if success else 1)
