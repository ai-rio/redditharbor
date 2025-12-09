"""
Configuration validation tests for environment variables
RED Phase: Tests for environment variable validation edge cases
"""

import os
import pytest
from unittest.mock import patch
from pydantic import ValidationError

from config.settings import Settings


class TestEnvironmentVariableValidation:
    """Test environment variable validation edge cases"""

    @patch.dict(os.environ, {}, clear=True)
    def test_invalid_string_for_numeric_fields(self):
        """Test invalid string values for numeric fields"""
        with pytest.raises(ValidationError) as exc_info:
            Settings.create_for_testing(
                reddit_client_id="test",
                reddit_client_secret="test",
                openai_api_key="test",
                agno_timeout="not_a_number"  # Should be int
            )
        assert "agno_timeout" in str(exc_info.value)

    @patch.dict(os.environ, {}, clear=True)
    def test_malformed_boolean_values(self):
        """Test malformed boolean string values"""
        # These should fail - invalid boolean representations
        invalid_booleans = ["maybe", "somewhat", "2", "-1", "enabled", "disabled"]
        for bool_val in invalid_booleans:
            with pytest.raises(ValidationError) as exc_info:
                Settings.create_for_testing(
                    reddit_client_id="test",
                    reddit_client_secret="test",
                    openai_api_key="test",
                    agentops_enabled=bool_val  # Invalid boolean string
                )
            assert "agentops_enabled" in str(exc_info.value)

    @patch.dict(os.environ, {}, clear=True)
    def test_negative_cost_values(self):
        """Test negative cost values should be rejected"""
        with pytest.raises(ValidationError) as exc_info:
            Settings.create_for_testing(
                reddit_client_id="test",
                reddit_client_secret="test",
                openai_api_key="test",
                agno_claude_cost_per_million_input_tokens=-5.0  # Negative cost
            )
        assert "agno_claude_cost_per_million_input_tokens" in str(exc_info.value)