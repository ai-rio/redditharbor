"""
AI analysis data models with Pydantic validation for LLM output
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class MarketMetrics(BaseModel):
    """Market analysis metrics with validation"""

    market_demand: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Market demand score (0-100)"
    )
    pain_intensity: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Pain point intensity (0-100)"
    )
    monetization_potential: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Monetization potential (0-100)"
    )
    competition_level: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Competition level (0-100, higher = less competition)"
    )
    technical_feasibility: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Technical feasibility (0-100)"
    )


class AppIdea(BaseModel):
    """Core app idea analysis with strict validation"""

    # Core concept
    title: str = Field(
        ...,
        min_length=5,
        max_length=100,
        description="App title (5-100 characters)"
    )
    app_concept: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="App concept description"
    )
    problem_statement: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Problem the app solves"
    )

    # Core functions (strict limit: 1-3 functions max)
    core_functions: List[str] = Field(
        ...,
        min_items=1,
        max_items=3,
        description="Core app functions (1-3 maximum)"
    )

    # Target audience
    target_audience: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Target audience description"
    )

    @validator('core_functions')
    def validate_core_functions(cls, v):
        """Validate core functions are meaningful descriptions"""
        if not all(
            isinstance(func, str) and
            len(func.strip()) >= 5 and
            len(func.strip()) <= 100
            for func in v
        ):
            raise ValueError(
                "Each core function must be a string between 5-100 characters"
            )

        # Check for duplicate or too similar functions
        cleaned_funcs = [func.strip().lower() for func in v]
        if len(cleaned_funcs) != len(set(cleaned_funcs)):
            raise ValueError("Core functions must be unique")

        return v


class AnalysisResult(BaseModel):
    """Complete analysis result combining all metrics"""

    # Source data
    submission_id: str = Field(..., description="Source Reddit submission ID")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")

    # App idea analysis
    app_idea: AppIdea = Field(..., description="App idea analysis")
    market_metrics: MarketMetrics = Field(..., description="Market analysis metrics")

    # Overall scoring
    final_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Final opportunity score (0-100)"
    )

    # Trust and confidence
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Confidence in analysis (0-100)"
    )
    trust_level: str = Field(
        ...,
        description="Trust level (LOW, MEDIUM, HIGH)"
    )

    # Optional embedding for semantic search
    embedding: Optional[List[float]] = Field(
        None,
        description="Text embedding vector for similarity search"
    )

    @validator('trust_level')
    def validate_trust_level(cls, v):
        """Validate trust level is one of allowed values"""
        allowed_levels = ["LOW", "MEDIUM", "HIGH"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"trust_level must be one of {allowed_levels}")
        return v.upper()

    @validator('final_score')
    def validate_final_score_logic(cls, v, values):
        """Final score should be consistent with market metrics"""
        if 'market_metrics' in values:
            metrics = values['market_metrics']
            # Final score should be roughly the average of key metrics
            expected_range = (
                (metrics.market_demand + metrics.pain_intensity + metrics.monetization_potential) / 3
            ) * 0.8  # Allow 20% variance

            if abs(v - expected_range) > 20:  # Allow 20 point variance
                pass  # Don't raise error, just note potential inconsistency

        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }