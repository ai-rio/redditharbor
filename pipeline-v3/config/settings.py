"""
Configuration settings for Pipeline v3 using existing RedditHarbor infrastructure
"""

import os
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with validation and environment variable support"""

    # Reddit API Configuration (using existing env vars)
    reddit_client_id: str = Field(default="test_client_id", alias="REDDIT_PUBLIC", description="Reddit API client ID")
    reddit_client_secret: str = Field(default="test_client_secret", alias="REDDIT_SECRET", description="Reddit API client secret")
    reddit_user_agent: str = Field(
        default="RedditHarbor Pipeline v3/1.0",
        description="Reddit API user agent string"
    )

    def __init__(self, **kwargs):
        """Initialize with support for explicit values overriding environment variables"""
        # Extract special parameters
        _env_file = kwargs.pop('_env_file', '.env.local')

        # Normal initialization: allow environment variables
        super().__init__(_env_file=_env_file, **kwargs)

    @classmethod
    def create_for_testing(cls, **kwargs):
        """Create a Settings instance for testing, bypassing environment variables"""
        # Create instance with default values, then set explicit values
        instance = cls.__new__(cls)
        BaseSettings.__init__(instance, _env_file=None)  # Initialize without env vars

        # Set provided values
        for key, value in kwargs.items():
            setattr(instance, key, value)

        return instance

    # Database Configuration (using existing DATABASE_URL)
    database_url: str = Field(
        default="postgresql://postgres:postgres@127.0.0.1:54322/postgres",
        alias="DATABASE_URL",
        description="PostgreSQL database connection string"
    )

    # LLM Configuration (using OpenRouter instead of OpenAI)
    openai_api_key: str = Field(
        default="test_api_key",
        alias="OPENROUTER_API_KEY",
        description="OpenRouter API key (used as OpenAI compatible endpoint)"
    )
    openai_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL"
    )
    model_name: str = Field(
        default="openai/gpt-4o-mini",
        alias="OPENROUTER_MODEL",
        description="OpenRouter model to use for analysis"
    )
    max_tokens: int = Field(
        default=2000,
        description="Maximum tokens for LLM responses"
    )
    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="LLM temperature for creativity vs consistency"
    )

    # Pipeline Configuration
    default_subreddits: List[str] = Field(
        default=["productivity", "tools"],
        description="Default subreddits to fetch from"
    )
    default_limit: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="Default number of submissions to fetch"
    )
    batch_size: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Batch size for LLM processing"
    )

    # pgvector Configuration
    embedding_dimension: int = Field(
        default=384,
        description="Dimension for text embeddings (pgvector)"
    )
    similarity_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Similarity threshold for duplicate detection"
    )

    # Agno Multi-Agent Configuration
    agno_analyzer_enabled: bool = Field(
        default=True,
        alias="AGNO_ANALYZER_ENABLED",
        description="Enable Agno multi-agent analyzer"
    )
    agno_orchestration_mode: str = Field(
        default="sequential",
        alias="AGNO_ORCHESTRATION_MODE",
        description="Agent orchestration mode (sequential or parallel)"
    )
    agno_consensus_threshold: float = Field(
        default=60.0,
        alias="AGNO_CONSENSUS_THRESHOLD",
        ge=0.0,
        le=100.0,
        description="Minimum confidence threshold for multi-agent consensus"
    )
    agno_model: str = Field(
        default="anthropic/claude-haiku-4.5",
        alias="AGNO_MODEL",
        description="Default model for Agno agents"
    )
    agno_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="AGNO_BASE_URL",
        description="API base URL for Agno agents"
    )
    agno_enable_agentops: bool = Field(
        default=False,
        alias="AGNO_ENABLE_AGENTOPS",
        description="Enable AgentOps tracking for Agno agents"
    )

    # Jina API Configuration for Phase 3 Market Research
    jina_api_key: str = Field(
        default="",
        alias="JINA_API_KEY",
        description="Jina API key for web search and content extraction"
    )
    jina_redis_url: str = Field(
        default="redis://localhost:6379/0",
        alias="JINA_REDIS_URL",
        description="Redis URL for Jina response caching"
    )
    jina_redis_db: int = Field(
        default=1,
        alias="JINA_REDIS_DB",
        description="Redis database number for Jina cache"
    )
    jina_enable_cache: bool = Field(
        default=True,
        alias="JINA_ENABLE_CACHE",
        description="Enable Jina response caching"
    )
    jina_cache_ttl_competitor: int = Field(
        default=7 * 24 * 60 * 60,  # 7 days
        alias="JINA_CACHE_TTL_COMPETITOR",
        description="Cache TTL for competitor pricing data (seconds)"
    )
    jina_cache_ttl_market: int = Field(
        default=30 * 24 * 60 * 60,  # 30 days
        alias="JINA_CACHE_TTL_MARKET",
        description="Cache TTL for market size data (seconds)"
    )
    jina_cache_ttl_launch: int = Field(
        default=7 * 24 * 60 * 60,  # 7 days
        alias="JINA_CACHE_TTL_LAUNCH",
        description="Cache TTL for product launch data (seconds)"
    )
    jina_rate_limit: int = Field(
        default=10,
        alias="JINA_RATE_LIMIT",
        description="Jina API rate limit (requests per second)"
    )
    jina_timeout: float = Field(
        default=30.0,
        alias="JINA_TIMEOUT",
        description="Jina API request timeout (seconds)"
    )
    jina_max_retries: int = Field(
        default=3,
        alias="JINA_MAX_RETRIES",
        description="Maximum Jina API retry attempts"
    )
    jina_enable_cost_tracking: bool = Field(
        default=True,
        alias="JINA_ENABLE_COST_TRACKING",
        description="Enable Jina API cost tracking"
    )
    jina_search_cost_per_query: float = Field(
        default=0.0001,
        alias="JINA_SEARCH_COST_PER_QUERY",
        description="Cost per Jina search query (USD)"
    )
    jina_extraction_cost_per_url: float = Field(
        default=0.0002,
        alias="JINA_EXTRACTION_COST_PER_URL",
        description="Cost per Jina content extraction (USD)"
    )
    jina_llm_model: str = Field(
        default="anthropic/claude-haiku-4.5",
        alias="JINA_LLM_MODEL",
        description="LLM model for Jina data extraction"
    )
    jina_llm_api_key: str = Field(
        default="",
        alias="JINA_LLM_API_KEY",
        description="API key for LLM used in Jina extraction"
    )
    jina_llm_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="JINA_LLM_BASE_URL",
        description="Base URL for LLM API used in Jina extraction"
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    log_file: str = Field(
        default="pipeline_v3.log",
        description="Log file name"
    )

    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level is one of the allowed values"""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if isinstance(v, str) and v.upper() not in allowed_levels:
            raise ValueError(f"log_level must be one of {allowed_levels}")
        return v.upper() if isinstance(v, str) else v

    @field_validator("default_subreddits", mode="before")
    @classmethod
    def parse_subreddits(cls, v):
        """Parse subreddits from various input formats"""
        if isinstance(v, str):
            # Comma-separated string
            return [s.strip() for s in v.split(",") if s.strip()]
        elif isinstance(v, list):
            return v
        else:
            raise ValueError("default_subreddits must be a string or list")

    
    @property
    def project_root(self) -> Path:
        """Get the project root directory"""
        return Path(__file__).parent.parent.parent

    @property
    def log_path(self) -> Path:
        """Get the full path to the log file"""
        return self.project_root / "logs" / self.log_file

    @property
    def is_openrouter_configured(self) -> bool:
        """Check if OpenRouter is properly configured"""
        return (
            self.openai_api_key and
            "openrouter" in self.openai_base_url.lower()
        )

    def get_openai_client_config(self) -> dict:
        """Get OpenAI client configuration for OpenRouter"""
        if self.is_openrouter_configured:
            return {
                "api_key": self.openai_api_key,
                "base_url": self.openai_base_url,
                "default_headers": {
                    "HTTP-Referer": "https://github.com/redditharbor/redditharbor",
                    "X-Title": "RedditHarbor Pipeline v3"
                }
            }
        else:
            return {
                "api_key": self.openai_api_key
            }

    model_config = {
        "env_file": ".env.local",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow",  # Allow extra fields for testing
        "validate_assignment": True,
    }


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance, creating it if necessary"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings(_env_file: str | None = ".env.local") -> Settings:
    """Reload settings from environment variables"""
    global _settings
    _settings = Settings(_env_file=_env_file)
    return _settings