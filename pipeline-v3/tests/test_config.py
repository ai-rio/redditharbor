"""
Tests for configuration management
"""

import pytest
import os
from unittest.mock import patch

from config.settings import Settings, get_settings


class TestSettings:
    """Test Settings validation and loading"""

    def test_default_values(self):
        """Test default configuration values"""
        settings = Settings(
            reddit_client_id="test_id",
            reddit_client_secret="test_secret",
            openai_api_key="test_key"
        )

        assert settings.reddit_user_agent == "RedditHarbor Pipeline v3/1.0"
        assert settings.model_name == "gpt-4o-mini"
        assert settings.default_subreddits == ["productivity", "tools"]
        assert settings.default_limit == 10
        assert settings.batch_size == 5
        assert settings.embedding_dimension == 384
        assert settings.similarity_threshold == 0.8
        assert settings.log_level == "INFO"

    def test_validate_log_level(self):
        """Test log level validation"""
        settings = Settings(
            reddit_client_id="test",
            reddit_client_secret="test",
            openai_api_key="test",
            log_level="debug"  # Should be converted to uppercase
        )
        assert settings.log_level == "DEBUG"

        with pytest.raises(ValueError, match="log_level must be one of"):
            Settings(
                reddit_client_id="test",
                reddit_client_secret="test",
                openai_api_key="test",
                log_level="INVALID"
            )

    def test_parse_subreddits_string(self):
        """Test subreddit parsing from string"""
        settings = Settings(
            reddit_client_id="test",
            reddit_client_secret="test",
            openai_api_key="test",
            default_subreddits="productivity, tools, , freelance"  # Note empty string
        )
        assert settings.default_subreddits == ["productivity", "tools", "freelance"]

    def test_parse_subreddits_list(self):
        """Test subreddit parsing from list"""
        settings = Settings(
            reddit_client_id="test",
            reddit_client_secret="test",
            openai_api_key="test",
            default_subreddits=["productivity", "tools", "freelance"]
        )
        assert settings.default_subreddits == ["productivity", "tools", "freelance"]

    def test_validate_temperature_range(self):
        """Test temperature validation"""
        # Valid temperature
        settings = Settings(
            reddit_client_id="test",
            reddit_client_secret="test",
            openai_api_key="test",
            temperature=0.7
        )
        assert settings.temperature == 0.7

        # Invalid temperatures
        with pytest.raises(ValueError):
            Settings(
                reddit_client_id="test",
                reddit_client_secret="test",
                openai_api_key="test",
                temperature=-0.1  # Too low
            )

        with pytest.raises(ValueError):
            Settings(
                reddit_client_id="test",
                reddit_client_secret="test",
                openai_api_key="test",
                temperature=2.1  # Too high
            )

    def test_validate_score_ranges(self):
        """Test score and threshold validations"""
        settings = Settings(
            reddit_client_id="test",
            reddit_client_secret="test",
            openai_api_key="test"
        )

        # Test valid ranges
        assert 1 <= settings.default_limit <= 1000
        assert 1 <= settings.batch_size <= 50
        assert 0.0 <= settings.similarity_threshold <= 1.0

    def test_project_root_path(self):
        """Test project root path property"""
        settings = Settings(
            reddit_client_id="test",
            reddit_client_secret="test",
            openai_api_key="test"
        )
        assert settings.project_root.exists()
        assert (settings.project_root / "config").exists()

    def test_log_path_property(self):
        """Test log path property"""
        settings = Settings(
            reddit_client_id="test",
            reddit_client_secret="test",
            openai_api_key="test",
            log_file="test.log"
        )
        log_path = settings.log_path
        assert log_path.name == "test.log"
        assert "logs" in str(log_path)


class TestSettingsSingleton:
    """Test settings singleton pattern"""

    def test_get_settings_singleton(self):
        """Test that get_settings returns the same instance"""
        # Clear any existing instance
        import config.settings
        config.settings._settings = None

        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_reload_settings(self):
        """Test settings reload functionality"""
        import config.settings

        # Set initial instance
        config.settings._settings = Settings(
            reddit_client_id="old_id",
            reddit_client_secret="old_secret",
            openai_api_key="old_key"
        )

        old_settings = get_settings()
        assert old_settings.reddit_client_id == "old_id"

        # Reload with new environment
        with patch.dict(os.environ, {
            'REDDIT_CLIENT_ID': 'new_id',
            'REDDIT_CLIENT_SECRET': 'new_secret',
            'OPENAI_API_KEY': 'new_key'
        }):
            new_settings = reload_settings()
            assert new_settings.reddit_client_id == "new_id"

        # Verify singleton was updated
        current_settings = get_settings()
        assert current_settings.reddit_client_id == "new_id"