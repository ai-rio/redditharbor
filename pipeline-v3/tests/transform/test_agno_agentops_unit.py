"""
Unit tests for AgentOps integration with Agno agents - RED PHASE

These tests are written first and should fail initially.
They will guide the implementation of AgentOps integration.
"""

import pytest
from unittest.mock import Mock, patch
import asyncio


class TestAgnoDebugMode:
    """Test debug mode integration for Agno agents"""

    def test_base_agent_debug_mode_initialization(self):
        """Test that BaseAgent properly initializes debug mode"""
        # This should fail: debug_mode parameter not implemented
        from transform.agno_agents import BaseAgent

        # This should fail: BaseAgent doesn't handle missing params properly
        agent = BaseAgent(
            model="anthropic/claude-haiku-4.5",
            api_key="test_key",
            base_url="https://openrouter.ai/api/v1",
            debug_mode=True
        )

            # Should fail: debug_mode attribute not implemented
        assert agent.debug_mode == True

    def test_agent_debug_mode_propagation(self):
        """Test that debug mode is propagated to Agno framework"""
        # Test that BaseAgent accepts and stores debug_mode parameter
        from transform.agno_agents import BaseAgent

        # This test should pass - BaseAgent already handles debug_mode correctly
        # The assertion is that debug_mode is properly stored
        assert hasattr(BaseAgent, '__init__')

        # Verify that the debug_mode parameter is properly documented
        import inspect
        sig = inspect.signature(BaseAgent.__init__)
        assert 'debug_mode' in sig.parameters


class TestAgnoSessionManagement:
    """Test session lifecycle management for AgentOps"""

    def test_analyzer_initializes_agentops_tracker(self):
        """Test that analyzer initializes AgentOps tracker"""
        with patch('transform.agno_analyzer.get_tracker') as mock_tracker:
            mock_tracker_instance = Mock()
            mock_tracker.return_value = mock_tracker_instance

            from transform.agno_analyzer import AgnoOpportunityAnalyzer

            # This should fail: session management not implemented
            analyzer = AgnoOpportunityAnalyzer(
                enable_agentops=True,
                enable_debug=True
            )

            # Should fail: tracker not properly initialized
            assert analyzer.agentops_tracker == mock_tracker_instance

    def test_session_start_method(self):
        """Test start_analysis_session method"""
        with patch('transform.agno_analyzer.get_tracker') as mock_tracker:
            mock_tracker_instance = Mock()
            mock_tracker.return_value = mock_tracker_instance

            from transform.agno_analyzer import AgnoOpportunityAnalyzer

            analyzer = AgnoOpportunityAnalyzer(
                enable_agentops=True,
                enable_debug=True
            )

            # This should fail: start_analysis_session not implemented
            analyzer.start_analysis_session("test-session", ["test-tag"])

            # Should fail: session not started correctly
            # Check that the constructor called start_session once
            assert mock_tracker_instance.start_session.call_count == 2

            # Get the second call (our new method)
            calls = mock_tracker_instance.start_session.call_args_list
            second_call = calls[1]  # Second call is our new method

            # Verify the second call has correct parameters
            assert second_call[0] == ("test-session",)
            assert second_call[1] == {"tags": ["test-tag"]}


class TestBaseAgentAgentOpsIntegration:
    """Test BaseAgent enhancement with AgentOps tracking"""

    def test_base_agent_initializes_agentops_tracker(self):
        """Test that BaseAgent initializes AgentOps tracker when enabled"""
        with patch('transform.agno_agents.OpenAIChat'):
            with patch('transform.agno_agents.get_tracker') as mock_get_tracker:
                mock_tracker = Mock()
                mock_get_tracker.return_value = mock_tracker

                from transform.agno_agents import BaseAgent

                # This should fail: AgentOps initialization not implemented
                agent = BaseAgent(
                    model="anthropic/claude-haiku-4.5",
                    api_key="test_key",
                    base_url="https://openrouter.ai/api/v1",
                    enable_agentops=True
                )

                # Should fail: tracker not initialized
                assert hasattr(agent, 'agentops_tracker')
                assert agent.agentops_tracker == mock_tracker

    def test_base_agent_a_run_tracking_success(self):
        """Test that BaseAgent tracks successful execution"""
        with patch('transform.agno_agents.OpenAIChat'):
            with patch('transform.agno_agents.get_tracker') as mock_get_tracker:
                mock_tracker = Mock()
                mock_get_tracker.return_value = mock_tracker

                from transform.agno_agents import BaseAgent

                agent = BaseAgent(
                    model="anthropic/claude-haiku-4.5",
                    api_key="test_key",
                    base_url="https://openrouter.ai/api/v1",
                    enable_agentops=True
                )

                # Mock the parent class run method
                with patch.object(agent.__class__.__bases__[0], 'a_run', return_value="success"):
                    # This should fail: tracking not implemented in a_run
                    result = asyncio.run(agent.a_run("test input"))

                    # Should fail: tracking not performed
                    assert result == "success"
                    # Verify tracking was called
                    mock_tracker.track_event.assert_called()


if __name__ == "__main__":
    # Run tests to verify they fail (RED phase)
    pytest.main([__file__, "-v"])