"""
AgentOps configuration validation tests
RED Phase: Tests for AgentOps configuration edge cases
"""

import os
import pytest
from unittest.mock import patch
from pydantic import ValidationError

from config.settings import Settings


class TestAgentOpsConfigValidation:
    """Test AgentOps configuration edge cases"""

    @patch.dict(os.environ, {}, clear=True)
    def test_agentops_empty_api_key(self):
        """Test empty AgentOps API key should be rejected when enabled"""
        with pytest.raises(ValidationError) as exc_info:
            Settings.create_for_testing(
                reddit_client_id="test",
                reddit_client_secret="test",
                openai_api_key="test",
                agentops_api_key="",  # Empty API key
                agentops_enabled=True  # But AgentOps is enabled
            )
        assert "agentops_api_key" in str(exc_info.value)