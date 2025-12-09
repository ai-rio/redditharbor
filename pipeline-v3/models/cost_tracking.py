"""
Cost tracking models for LiteLLM integration
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ModelCostConfig(BaseModel):
    """Cost configuration for different models"""

    model_name: str = Field(..., description="Model identifier")
    provider: str = Field(..., description="Provider name (openrouter, openai, etc.)")
    input_cost_per_million: float = Field(..., ge=0, description="Input token cost per 1M tokens")
    output_cost_per_million: float = Field(..., ge=0, description="Output token cost per 1M tokens")
    max_tokens: int | None = Field(None, description="Maximum tokens for model")
    supports_json_mode: bool = Field(default=True, description="Whether model supports JSON mode")


class CostTracking(BaseModel):
    """Detailed cost tracking for a single LLM call"""

    model_used: str = Field(..., description="Model name used for the call")
    provider: str = Field(..., description="Provider used")
    prompt_tokens: int = Field(..., ge=0, description="Number of input tokens")
    completion_tokens: int = Field(..., ge=0, description="Number of output tokens")
    total_tokens: int = Field(..., ge=0, description="Total tokens used")
    input_cost_usd: float = Field(..., ge=0, description="Input token cost in USD")
    output_cost_usd: float = Field(..., ge=0, description="Output token cost in USD")
    total_cost_usd: float = Field(..., ge=0, description="Total cost in USD")
    latency_seconds: float = Field(..., ge=0, description="Request latency in seconds")
    prompt_length_chars: int = Field(..., ge=0, description="Prompt length in characters")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Request timestamp")
    model_pricing_per_m_tokens: dict[str, float] = Field(..., description="Model pricing info")
    request_success: bool = Field(..., description="Whether the request succeeded")
    error_message: str | None = Field(None, description="Error message if request failed")


class CostSummary(BaseModel):
    """Cost summary for multiple analyses"""

    total_cost_usd: float = Field(..., ge=0, description="Total cost across all analyses")
    total_tokens: int = Field(..., ge=0, description="Total tokens across all analyses")
    analysis_count: int = Field(..., ge=0, description="Number of analyses")
    avg_cost_per_analysis: float = Field(..., ge=0, description="Average cost per analysis")
    model_breakdown: dict[str, dict[str, Any]] = Field(..., description="Usage breakdown by model")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Summary timestamp")
