"""
Pipeline V4 Configuration
Centralized settings with environment variable support
"""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with validation"""

    # ===== Reddit API =====
    reddit_client_id: str = Field(alias="REDDIT_PUBLIC")
    reddit_client_secret: str = Field(alias="REDDIT_SECRET")
    reddit_user_agent: str = Field(
        default="RedditHarbor Pipeline v4/1.0"
    )

    # ===== Database =====
    database_url: str = Field(
        default="postgresql://postgres:postgres@127.0.0.1:54331/postgres",
        alias="DATABASE_URL"
    )

    # ===== LLM Configuration =====
    llm_api_key: str = Field(alias="OPENROUTER_API_KEY")
    llm_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="LLM_BASE_URL"
    )
    llm_model: str = Field(
        default="openai/gpt-4o-mini",
        alias="LLM_MODEL"
    )
    llm_max_tokens: int = Field(default=2000)
    llm_temperature: float = Field(default=0.3, ge=0.0, le=2.0)

    # ===== Pipeline Configuration =====
    default_subreddits: list[str] = Field(
        default=["productivity", "tools"]
    )
    default_limit: int = Field(default=10, ge=1, le=1000)
    batch_size: int = Field(default=5, ge=1, le=50)

    # ===== Deduplication =====
    enable_deduplication: bool = Field(default=True)
    checkpoint_interval: int = Field(default=25)

    # ===== SQLModel Migration =====
    use_sqlmodel_loader: bool = Field(
        default=False,
        description="Enable SQLModel-based database loader (Phase 3 migration)",
        alias="USE_SQLMODEL_LOADER"
    )

    # ===== Logging =====
    log_level: str = Field(default="INFO")

    model_config = {
        "env_file": ".env.local",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Global singleton
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings