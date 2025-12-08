"""
Test suite for LiteLLM integration with Pipeline v3
"""

import time
from unittest.mock import Mock, patch

import pytest

from models.cost_tracking import CostSummary, CostTracking, ModelCostConfig
from models.reddit import RedditSubmission
from transform.litellm_analyzer import LiteLLMAnalyzer


class TestLiteLLMAnalyzer:
    """Test LiteLLM analyzer functionality"""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        settings = Mock()
        settings.model_name = "openai/gpt-4o-mini"
        settings.max_tokens = 1000
        settings.temperature = 0.3
        settings.openai_api_key = "test_key"
        settings.openai_base_url = "https://openrouter.ai/api/v1"
        settings.is_openrouter_configured = True
        settings.batch_size = 5
        settings.get_openai_client_config.return_value = {
            "api_key": "test_key",
            "base_url": "https://openrouter.ai/api/v1"
        }
        return settings

    @pytest.fixture
    def test_submission(self):
        """Create test Reddit submission"""
        return RedditSubmission(
            id="test123",
            title="Looking for a better productivity app",
            text="I need a simple app to track my daily tasks and remind me of deadlines.",
            author="test_user",
            subreddit="productivity",
            upvotes=45,
            comments_count=12,
            created_utc="2024-01-01T12:00:00Z",
            permalink="/r/productivity/comments/test123/",
            url="https://reddit.com/r/productivity/comments/test123/"
        )

    def test_cost_tracking_model_creation(self):
        """Test cost tracking model creation and validation"""
        cost_data = CostTracking(
            model_used="openai/gpt-4o-mini",
            provider="openrouter",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            input_cost_usd=0.000015,
            output_cost_usd=0.000030,
            total_cost_usd=0.000045,
            latency_seconds=1.23,
            prompt_length_chars=500,
            model_pricing_per_m_tokens={"input": 0.15, "output": 0.60},
            request_success=True
        )

        assert cost_data.model_used == "openai/gpt-4o-mini"
        assert cost_data.total_cost_usd == 0.000045
        assert cost_data.request_success is True

    def test_cost_summary_model_creation(self):
        """Test cost summary model creation"""
        summary = CostSummary(
            total_cost_usd=0.001234,
            total_tokens=2500,
            analysis_count=5,
            avg_cost_per_analysis=0.000247,
            model_breakdown={
                "openai/gpt-4o-mini": {
                    "count": 3,
                    "cost": 0.000741,
                    "tokens": 1500
                }
            }
        )

        assert summary.total_cost_usd == 0.001234
        assert summary.analysis_count == 5
        assert "openai/gpt-4o-mini" in summary.model_breakdown

    def test_model_cost_config(self):
        """Test model cost configuration"""
        config = ModelCostConfig(
            model_name="openai/gpt-4o-mini",
            provider="openrouter",
            input_cost_per_million=0.15,
            output_cost_per_million=0.60,
            max_tokens=4000,
            supports_json_mode=True
        )

        assert config.model_name == "openai/gpt-4o-mini"
        assert config.input_cost_per_million == 0.15
        assert config.supports_json_mode is True

    @patch('transform.litellm_analyzer.litellm')
    @patch('transform.litellm_analyzer.get_settings')
    def test_litellm_analyzer_initialization(self, mock_get_settings, mock_litellm, mock_settings):
        """Test LiteLLM analyzer initialization"""
        mock_get_settings.return_value = mock_settings

        analyzer = LiteLLMAnalyzer()

        assert analyzer.settings == mock_settings
        assert analyzer.enable_cost_tracking is True
        mock_litellm.set_verbose.assert_called_once_with(False)

    @patch('transform.litellm_analyzer.litellm')
    @patch('transform.litellm_analyzer.get_settings')
    def test_extract_cost_data(self, mock_get_settings, mock_litellm, mock_settings):
        """Test cost data extraction from LiteLLM response"""
        mock_get_settings.return_value = mock_settings

        # Mock LiteLLM response
        mock_response = Mock()
        mock_usage = Mock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50
        mock_usage.total_tokens = 150
        mock_response.usage = mock_usage
        mock_response.model = "openai/gpt-4o-mini"

        analyzer = LiteLLMAnalyzer()
        start_time = time.time()

        # Mock the time difference
        with patch('time.time', return_value=start_time + 1.23):
            cost_data = analyzer._extract_cost_data(mock_response, "test prompt", start_time)

        assert cost_data.model_used == "openai/gpt-4o-mini"
        assert cost_data.prompt_tokens == 100
        assert cost_data.completion_tokens == 50
        assert cost_data.total_tokens == 150
        assert cost_data.latency_seconds == 1.23
        assert cost_data.total_cost_usd > 0

    @patch('transform.litellm_analyzer.litellm')
    @patch('transform.litellm_analyzer.get_settings')
    def test_calculate_model_costs(self, mock_get_settings, mock_litellm, mock_settings):
        """Test model cost calculation"""
        mock_get_settings.return_value = mock_settings

        analyzer = LiteLLMAnalyzer()

        # Test with known model
        costs = analyzer._calculate_model_costs("openai/gpt-4o-mini", 1000, 500)

        assert costs["input_cost_usd"] == 0.00015  # 1000 tokens * 0.15/1M
        assert costs["output_cost_usd"] == 0.00030  # 500 tokens * 0.60/1M
        assert costs["total_cost_usd"] == 0.00045

        # Test with unknown model (fallback)
        costs = analyzer._calculate_model_costs("unknown/model", 1000, 500)
        assert costs["input_cost_usd"] == 0.001  # fallback rate
        assert costs["output_cost_usd"] == 0.005  # fallback rate

    def test_generate_cost_summary_empty(self):
        """Test cost summary generation with no data"""
        analyzer = LiteLLMAnalyzer()
        summary = analyzer._generate_cost_summary([])

        assert summary.total_cost_usd == 0.0
        assert summary.total_tokens == 0
        assert summary.analysis_count == 0
        assert summary.avg_cost_per_analysis == 0.0
        assert summary.model_breakdown == {}

    def test_generate_cost_summary_with_data(self):
        """Test cost summary generation with data"""
        analyzer = LiteLLMAnalyzer()

        cost_data_list = [
            CostTracking(
                model_used="openai/gpt-4o-mini",
                provider="openrouter",
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                input_cost_usd=0.000015,
                output_cost_usd=0.000030,
                total_cost_usd=0.000045,
                latency_seconds=1.0,
                prompt_length_chars=200,
                model_pricing_per_m_tokens={"input": 0.15, "output": 0.60},
                request_success=True
            ),
            CostTracking(
                model_used="anthropic/claude-haiku",
                provider="openrouter",
                prompt_tokens=80,
                completion_tokens=40,
                total_tokens=120,
                input_cost_usd=0.000080,
                output_cost_usd=0.000200,
                total_cost_usd=0.000280,
                latency_seconds=0.8,
                prompt_length_chars=150,
                model_pricing_per_m_tokens={"input": 1.0, "output": 5.0},
                request_success=True
            )
        ]

        summary = analyzer._generate_cost_summary(cost_data_list)

        assert summary.total_cost_usd == 0.000325  # 0.000045 + 0.000280
        assert summary.total_tokens == 270  # 150 + 120
        assert summary.analysis_count == 2
        assert summary.avg_cost_per_analysis == 0.0001625  # 0.000325 / 2
        assert len(summary.model_breakdown) == 2
        assert "openai/gpt-4o-mini" in summary.model_breakdown
        assert "anthropic/claude-haiku" in summary.model_breakdown

    @patch('transform.litellm_analyzer.litellm')
    @patch('transform.litellm_analyzer.get_settings')
    def test_error_cost_tracking(self, mock_get_settings, mock_litellm, mock_settings, test_submission):
        """Test cost tracking for error cases"""
        mock_get_settings.return_value = mock_settings

        analyzer = LiteLLMAnalyzer()

        # Simulate error during analysis
        error_cost = analyzer._create_error_cost_data("Test error", test_submission, time.time() - 0.5)

        assert error_cost.model_used == mock_settings.model_name
        assert error_cost.provider == "openrouter"
        assert error_cost.request_success is False
        assert error_cost.error_message == "Test error"
        assert error_cost.total_cost_usd == 0.0
        assert error_cost.latency_seconds == 0.5

    def test_model_fallback_configuration(self):
        """Test model cost configuration fallback"""
        analyzer = LiteLLMAnalyzer()

        # Test with known model
        config = analyzer._get_model_cost_config("openai/gpt-4o-mini")
        assert config is not None
        assert config.model_name == "openai/gpt-4o-mini"
        assert config.input_cost_per_million == 0.15

        # Test with unknown model
        config = analyzer._get_model_cost_config("unknown/unknown-model")
        assert config is not None
        assert config.model_name == "unknown/unknown-model"
        assert config.input_cost_per_million == 1.0  # fallback rate

    @patch('transform.litellm_analyzer.litellm')
    @patch('transform.litellm_analyzer.get_settings')
    def test_analyzer_configuration(self, mock_get_settings, mock_litellm, mock_settings):
        """Test analyzer configuration and setup"""
        mock_get_settings.return_value = mock_settings

        analyzer = LiteLLMAnalyzer(enable_cost_tracking=False)

        assert analyzer.enable_cost_tracking is False
        assert analyzer.settings == mock_settings
        mock_litellm.set_verbose.assert_called_once_with(False)

    def test_token_usage_validation(self):
        """Test token usage validation in cost tracking"""
        with pytest.raises(ValueError):
            # Negative tokens should raise an error
            CostTracking(
                model_used="test/model",
                provider="test",
                prompt_tokens=-1,  # Invalid negative value
                completion_tokens=50,
                total_tokens=49,  # Should be 99 if calculated properly
                input_cost_usd=0.00001,
                output_cost_usd=0.00002,
                total_cost_usd=0.00003,
                latency_seconds=1.0,
                prompt_length_chars=100,
                model_pricing_per_m_tokens={"input": 0.15, "output": 0.60},
                request_success=True
            )


if __name__ == "__main__":
    pytest.main([__file__])
