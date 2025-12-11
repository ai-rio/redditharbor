"""
AI analysis data models with SQLModel and Pydantic validation for LLM output
"""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Opportunity(SQLModel, table=True):
    """Single-table opportunity model with JSON storage"""

    __tablename__ = "opportunities"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Reddit data
    submission_id: str = Field(
        unique=True, index=True, description="Reddit submission ID"
    )
    subreddit: str = Field(index=True, description="Subreddit name")
    title: str = Field(description="Submission title")

    # Core scores
    wtp_score: float = Field(ge=0.0, le=100.0, description="Willingness-to-pay score")
    final_score: float = Field(
        default_factory=lambda: 0.0,
        ge=0.0,
        le=100.0,
        description="Final opportunity score",
    )
    confidence_score: float = Field(
        default_factory=lambda: 75.0, ge=0.0, le=100.0, description="Confidence score"
    )

    # JSON fields
    analysis: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    metrics: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    # Metadata
    trust_level: str = Field(default="MEDIUM", description="Trust level")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("trust_level")
    @classmethod
    def validate_trust_level(cls, v):
        valid_levels = ["LOW", "MEDIUM", "HIGH"]
        if v not in valid_levels:
            raise ValueError(f"Trust level must be one of {valid_levels}")
        return v

    def __init__(self, **data):
        """Initialize with automatic final score calculation"""
        # Calculate final_score if metrics provided but final_score not explicitly set
        if "final_score" not in data and "metrics" in data and data["metrics"]:
            weights = {
                "market_demand": 0.3,
                "pain_intensity": 0.25,
                "monetization_potential": 0.25,
                "technical_feasibility": 0.2,
            }

            score = 0.0
            total_weight = 0.0

            for metric, weight in weights.items():
                if metric in data["metrics"]:
                    score += data["metrics"][metric] * weight
                    total_weight += weight

            data["final_score"] = score / total_weight if total_weight > 0 else 0.0

        # Validate trust_level before passing to parent
        if "trust_level" in data:
            valid_levels = ["LOW", "MEDIUM", "HIGH"]
            if data["trust_level"] not in valid_levels:
                raise ValueError(f"Trust level must be one of {valid_levels}")

        super().__init__(**data)

    def calculate_final_score(self) -> float:
        """Calculate final score from metrics"""
        if not self.metrics:
            return 0.0

        # Weighted average of key metrics
        weights = {
            "market_demand": 0.3,
            "pain_intensity": 0.25,
            "monetization_potential": 0.25,
            "technical_feasibility": 0.2,
        }

        score = 0.0
        total_weight = 0.0

        for metric, weight in weights.items():
            if metric in self.metrics:
                score += self.metrics[metric] * weight
                total_weight += weight

        return score / total_weight if total_weight > 0 else 0.0

    def set_wtp_score(self, wtp: float):
        """Set WTP score and update final score"""
        self.wtp_score = min(100.0, max(0.0, wtp))
        self.final_score = self.calculate_final_score()

    @property
    def app_idea(self) -> dict[str, Any]:
        """Get app idea from analysis data"""
        return self.analysis.get("app_idea", {})

    @property
    def pain_points(self) -> list[str]:
        """Get pain points from analysis data"""
        return self.analysis.get("pain_points", [])

    @property
    def market_metrics(self) -> dict[str, Any]:
        """Get market metrics (alias for metrics)"""
        return self.metrics

    @property
    def spam_analysis(self) -> dict[str, Any]:
        """Get spam analysis from analysis data"""
        return self.analysis.get("spam_analysis", {})


class MarketMetrics(BaseModel):
    """Market analysis metrics with validation"""

    market_demand: float = Field(
        ..., ge=0.0, le=100.0, description="Market demand score (0-100)"
    )
    pain_intensity: float = Field(
        ..., ge=0.0, le=100.0, description="Pain point intensity (0-100)"
    )
    monetization_potential: float = Field(
        ..., ge=0.0, le=100.0, description="Monetization potential (0-100)"
    )
    technical_feasibility: float = Field(
        ..., ge=0.0, le=100.0, description="Technical feasibility (0-100)"
    )
    competition_level: float = Field(
        ..., ge=0.0, le=100.0, description="Competition level (0=high, 100=low)"
    )

    @field_validator(
        "market_demand",
        "pain_intensity",
        "monetization_potential",
        "technical_feasibility",
        "competition_level",
    )
    @classmethod
    def validate_scores(cls, v):
        """Ensure metric scores have reasonable precision"""
        if isinstance(v, float):
            str_val = str(v)
            if "." in str_val and len(str_val.split(".")[1]) > 2:
                raise ValueError(f"Metric {v} has too many decimal places")
        return v


class AppIdea(BaseModel):
    """Core app idea analysis with strict business logic validation"""

    # Core concept
    title: str = Field(
        ...,
        min_length=5,
        max_length=100,
        description="App title (5-100 characters, title case)",
    )
    app_concept: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="App concept description (specific and detailed)",
    )
    problem_statement: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Problem the app solves (specific pain point)",
    )

    # Core functions (strict limit: 1-3 functions max)
    core_functions: list[str] = Field(
        ...,
        min_items=1,
        max_items=3,
        description="Core app functions (1-3 maximum, distinct and meaningful)",
    )

    # Target audience
    target_audience: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Target audience description (specific demographic)",
    )


class AnalysisResult(BaseModel):
    """Complete analysis result combining all components"""

    # Reddit metadata
    submission_id: str = Field(..., description="Reddit submission ID")
    subreddit: str = Field(..., description="Subreddit name")
    title: str = Field(..., description="Submission title")

    # Core components
    app_idea: AppIdea = Field(..., description="Core app idea analysis")
    metrics: MarketMetrics = Field(..., description="Market metrics")
    pain_points: list[str] = Field(
        ...,
        min_items=1,
        max_items=5,
        description="Identified pain points (1-5 maximum)",
    )

    # Summary and scoring
    opportunity_summary: str = Field(
        ..., min_length=50, max_length=500, description="Opportunity summary"
    )
    final_score: float = Field(
        ..., ge=0.0, le=100.0, description="Final opportunity score"
    )
    confidence_score: float = Field(
        default=75.0, ge=0.0, le=100.0, description="Confidence score"
    )
    wtp_score: float = Field(
        ..., ge=0.0, le=100.0, description="Willingness-to-pay score"
    )
    trust_level: str = Field(default="MEDIUM", description="Trust level of analysis")

    # Additional analysis fields
    content_quality_score: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Content quality score"
    )
    is_spam: bool = Field(default=False, description="Whether the content is spam")
    spam_indicators: list[str] = Field(
        default_factory=list, description="Spam indicators"
    )
    analyzed_at: datetime | None = Field(default=None, description="Analysis timestamp")

    @field_validator("trust_level")
    @classmethod
    def validate_trust_level(cls, v):
        valid_levels = ["LOW", "MEDIUM", "HIGH"]
        if v not in valid_levels:
            raise ValueError(f"Trust level must be one of {valid_levels}")
        return v


# Simple test
if __name__ == "__main__":
    # Test model creation
    opp = Opportunity(
        submission_id="test123",
        subreddit="productivity",
        title="Test app",
        wtp_score=85.0,
        analysis={"app_idea": {"title": "Test App"}},
        metrics={"market_demand": 90.0},
    )
    print(f"✓ Created opportunity: {opp.title}")
    print(f"✓ Final score: {opp.calculate_final_score()}")
