#!/usr/bin/env python3
"""
TDD Step 1: Write a test that fails for BaseAgent AgentOps integration
"""

def test_base_agent_initializes_agentops_tracker():
    """Test that BaseAgent initializes AgentOps tracker when enabled"""
    from unittest.mock import Mock, patch

    from transform.agno_agents import BaseAgent

    with patch('transform.agno_agents.get_tracker') as mock_tracker:
        mock_tracker_instance = Mock()
        mock_tracker.return_value = mock_tracker_instance

        # Create agent with AgentOps enabled
        agent = BaseAgent(
            model="anthropic/claude-haiku-4.5",
            api_key="test_key",
            base_url="https://openrouter.ai/api/v1",
            enable_agentops=True
        )

        # This should fail: agentops_tracker not initialized
        assert hasattr(agent, 'agentops_tracker'), "agentops_tracker should exist"
        assert agent.agentops_tracker == mock_tracker_instance, "agentops_tracker should be set correctly"

        # Should fail: session not started
        mock_tracker_instance.start_session.assert_called_once_with("base_session")

    print("Test passed - BaseAgent initializes AgentOps tracker correctly!")

if __name__ == "__main__":
    try:
        test_base_agent_initializes_agentops_tracker()
    except AssertionError as e:
        print(f"Test failed as expected: {e}")
    except Exception as e:
        print(f"Other error: {e}")
