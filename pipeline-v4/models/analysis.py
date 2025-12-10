"""
AI analysis data models with SQLModel and Pydantic validation for LLM output
"""

import math
from datetime import UTC, datetime
from typing import Optional, List, Dict, Any

from pydantic import field_validator, model_validator
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON


class Opportunity(SQLModel, table=True):
    """Single-table opportunity model with JSON storage"""
    
    __tablename__ = "opportunities"
    
    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Reddit data
    submission_id: str = Field(unique=True, index=True, description="Reddit submission ID")
    subreddit: str = Field(index=True, description="Subreddit name")
    title: str = Field(description="Submission title")
    
    # Core scores
    wtp_score: float = Field(ge=0.0, le=100.0, description="Willingness-to-pay score")
    final_score: float = Field(ge=0.0, le=100.0, description="Final opportunity score")
    confidence_score: float = Field(ge=0.0, le=100.0, description="Confidence score")
    
    # JSON fields
    analysis: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    metrics: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Metadata
    trust_level: str = Field(default="MEDIUM", description="Trust level")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    @field_validator('trust_level')
    @classmethod
    def validate_trust_level(cls, v):
        valid_levels = ['LOW', 'MEDIUM', 'HIGH']
        if v not in valid_levels:
            raise ValueError(f"Trust level must be one of {valid_levels}")
        return v
    
    def calculate_final_score(self) -> float:
        """Calculate final score from metrics"""
        if not self.metrics:
            return 0.0
        
        # Weighted average of key metrics
        weights = {
            'market_demand': 0.3,
            'pain_intensity': 0.25,
            'monetization_potential': 0.25,
            'technical_feasibility': 0.2
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
    def app_idea(self) -> Dict[str, Any]:
        """Get app idea from analysis data"""
        return self.analysis.get('app_idea', {})
    
    @property
    def pain_points(self) -> List[str]:
        """Get pain points from analysis data"""
        return self.analysis.get('pain_points', [])
    
    @property
    def market_metrics(self) -> Dict[str, Any]:
        """Get market metrics (alias for metrics)"""
        return self.metrics
    
    @property
    def spam_analysis(self) -> Dict[str, Any]:
        """Get spam analysis from analysis data"""
        return self.analysis.get('spam_analysis', {})


# Simple test
if __name__ == "__main__":
    # Test model creation
    opp = Opportunity(
        submission_id="test123",
        subreddit="productivity",
        title="Test app",
        wtp_score=85.0,
        analysis={"app_idea": {"title": "Test App"}},
        metrics={"market_demand": 90.0}
    )
    print(f"✓ Created opportunity: {opp.title}")
    print(f"✓ Final score: {opp.calculate_final_score()}")
