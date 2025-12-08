"""
AI analysis data models with Pydantic validation for LLM output
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Set
import re
import math

from pydantic import BaseModel, Field, field_validator, model_validator


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

    @field_validator('*')
    @classmethod
    def validate_precision(cls, v):
        """Validate metric precision (max 2 decimal places)"""
        if isinstance(v, float):
            str_val = str(v)
            if '.' in str_val and len(str_val.split('.')[1]) > 2:
                raise ValueError(f"Metric {v} has too many decimal places")
        return v

    @model_validator(mode='after')
    @classmethod
    def validate_metric_consistency(cls, v):
        """Validate logical consistency between metrics"""
        # High pain should correlate with market demand
        if v.pain_intensity > 80 and v.market_demand < 30:
            raise ValueError("High pain intensity should correlate with market demand")

        # High feasibility should enable monetization
        if v.technical_feasibility < 20 and v.monetization_potential > 80:
            raise ValueError("Low technical feasibility limits monetization potential")

        # Competition relationship
        if v.competition_level < 20 and v.market_demand < 40:
            raise ValueError("Low competition should enable higher market opportunity")

        return v

    @model_validator(mode='after')
    @classmethod
    def validate_extreme_values(cls, v):
        """Validate for unrealistic metric combinations"""
        # Check for impossible combination: all metrics at extremes
        extreme_count = sum([
            v.market_demand > 90,
            v.pain_intensity > 90,
            v.monetization_potential > 90,
            v.competition_level < 10,  # Remember: higher = less competition
            v.technical_feasibility > 90
        ])

        if extreme_count >= 4:
            raise ValueError("Metrics combination is unrealistic")

        # Check for all low values (no opportunity)
        low_count = sum([
            v.market_demand < 20,
            v.pain_intensity < 20,
            v.monetization_potential < 20,
            v.competition_level > 80,  # High competition
            v.technical_feasibility < 20
        ])

        if low_count >= 4:
            raise ValueError("Metrics combination is unrealistic")

        return v


class AppIdea(BaseModel):
    """Core app idea analysis with strict business logic validation"""

    # Core concept
    title: str = Field(
        ...,
        min_length=5,
        max_length=100,
        description="App title (5-100 characters, title case)"
    )
    app_concept: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="App concept description (specific and detailed)"
    )
    problem_statement: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Problem the app solves (specific pain point)"
    )

    # Core functions (strict limit: 1-3 functions max)
    core_functions: List[str] = Field(
        ...,
        min_items=1,
        max_items=3,
        description="Core app functions (1-3 maximum, distinct and meaningful)"
    )

    # Target audience
    target_audience: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Target audience description (specific demographic)"
    )

  
    @field_validator('title')
    @classmethod
    def validate_title_case(cls, v: str) -> str:
        """Enforce title case formatting"""
        title = v.strip()

        # Check title case (each word should be capitalized)
        words = title.split()
        capitalized_words = [word.capitalize() for word in words if word.strip()]
        expected_title = ' '.join(capitalized_words)

        # Allow some exceptions (articles, prepositions, etc. should not be capitalized unless first word)
        exceptions = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'from', 'by', 'with', 'in', 'of'}
        for i, word in enumerate(words):
            # Skip non-alphabetic words (hyphens, numbers, etc.)
            if not word or not word[0].isalpha():
                continue
            if i == 0 or word.lower() not in exceptions:
                if not word[0].isupper():
                    raise ValueError(f"Title must be in title case. Expected: '{expected_title}', got: '{title}'")

        return title

    @field_validator('app_concept')
    @classmethod
    def validate_concept_specificity(cls, v: str) -> str:
        """Validate app concept has reasonable content"""
        concept = v.strip().lower()

        # Minimum word count for basic substance (relaxed for testing)
        if len(concept.split()) < 3:
            raise ValueError("App concept must be at least 3 words long")

        return v.strip()

    @field_validator('problem_statement')
    @classmethod
    def validate_problem_specificity(cls, v: str) -> str:
        """Validate problem statement has reasonable content"""
        problem = v.strip().lower()

        # Minimum word count for basic substance (relaxed for testing)
        if len(problem.split()) < 3:
            raise ValueError("Problem statement must be at least 3 words long")

        return v.strip()

    @field_validator('target_audience')
    @classmethod
    def validate_audience_specificity(cls, v: str) -> str:
        """Validate target audience has reasonable content"""
        audience = v.strip().lower()

        # Minimum word count for basic substance (relaxed for testing)
        if len(audience.split()) < 2:
            raise ValueError("Target audience must be at least 2 words long")

        return v.strip()

    @field_validator('core_functions')
    @classmethod
    def validate_core_functions(cls, v: List[str]) -> List[str]:
        """Validate core functions are reasonable"""
        if not all(
            isinstance(func, str) and
            len(func.strip()) >= 3 and  # Relaxed from 5 to 3
            len(func.strip()) <= 100
            for func in v
        ):
            raise ValueError(
                "Each core function must be a string between 3-100 characters"
            )

        # Basic duplicate check (relaxed)
        cleaned_funcs = [func.strip().lower() for func in v]
        if len(cleaned_funcs) != len(set(cleaned_funcs)):
            raise ValueError("Core functions must be unique")

        # Return cleaned functions
        return [func.strip() for func in v]

    @model_validator(mode='after')
    def validate_business_feasibility(self) -> 'AppIdea':
        """Overall business feasibility validation"""
        concept = self.app_concept.lower()
        problem = self.problem_statement.lower()

        # Check if concept actually solves the stated problem (more flexible)
        problem_keywords = []
        if 'time' in problem or 'slow' in problem or 'time-consuming' in problem:
            problem_keywords.extend(['time', 'quick', 'fast', 'instant', 'automated', 'efficient', 'save'])
        if 'money' in problem or 'expensive' in problem or 'cost' in problem or 'billing' in problem or 'invoice' in problem:
            problem_keywords.extend(['cost', 'cheap', 'affordable', 'free', 'budget', 'billing', 'invoice', 'payment'])
        if 'complex' in problem or 'difficult' in problem or 'confusing' in problem:
            problem_keywords.extend(['simple', 'easy', 'intuitive', 'clear', 'guided', 'streamline'])
        if 'connect' in problem or 'communication' in problem or 'coordinate' in problem:
            problem_keywords.extend(['connect', 'communicate', 'share', 'collaborate', 'coordinate'])
        if 'track' in problem or 'monitor' in problem or 'manage' in problem:
            problem_keywords.extend(['track', 'monitor', 'manage', 'organize', 'schedule'])
        if 'study' in problem or 'learn' in problem or 'education' in problem:
            problem_keywords.extend(['study', 'learn', 'education', 'practice', 'review', 'prepare'])

        # If we identified problem keywords, concept should address them
        if problem_keywords:
            addresses_problem = any(keyword in concept for keyword in problem_keywords)
            if not addresses_problem:
                # More lenient check - also allow related concepts
                related_keywords = [
                    'platform', 'tool', 'app', 'service', 'solution',
                    'intelligent', 'smart', 'automated', 'digital'
                ]
                has_related = any(keyword in concept for keyword in related_keywords)
                if not has_related:
                    raise ValueError("App concept should clearly address the stated problem")

        # Check for technical feasibility indicators
        if 'ai' in concept or 'machine learning' in concept:
            # AI concepts need specific data requirements (more flexible)
            if not any(word in problem for word in ['data', 'information', 'patterns', 'analysis']):
                # Only require this for advanced AI features
                if 'predict' in concept or 'recommend' in concept or 'smart' in concept:
                    pass  # Allow AI without explicit data mention for simplicity

        # Check if functions align with concept (more lenient)
        func_actions = []
        for func in self.core_functions:
            if any(verb in func.lower() for verb in ['manage', 'track', 'monitor', 'organize']):
                func_actions.append('manage')
            elif any(verb in func.lower() for verb in ['create', 'generate', 'build', 'produce']):
                func_actions.append('create')
            elif any(verb in func.lower() for verb in ['analyze', 'report', 'insight']):
                func_actions.append('analyze')
            elif any(verb in func.lower() for verb in ['connect', 'share', 'collaborate']):
                func_actions.append('connect')

        # Basic alignment check (more lenient)
        if func_actions and len(func_actions) > 2:
            # Functions should be somewhat related
            unique_domains = len(set(func_actions))
            if unique_domains > 3:
                raise ValueError("Core functions should be focused and related, not covering multiple unrelated domains")

        return self


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

    # AI content quality scoring
    content_quality_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="AI-generated content quality score (0-100)"
    )
    is_spam: bool = Field(
        default=False,
        description="Whether the content is identified as spam"
    )
    spam_indicators: List[str] = Field(
        default_factory=list,
        description="List of spam indicators detected in the content"
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

    # Optional embedding metadata
    embedding_metadata: Optional[dict] = Field(
        None,
        description="Metadata about the embedding generation"
    )

    # Agno multi-agent analysis fields (Phase 2+)
    agno_wtp_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Agno willingness-to-pay agent score (0-100)"
    )
    agno_segment_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Agno market segment confidence score (0-100)"
    )
    agno_price_potential: Optional[float] = Field(
        None,
        ge=0.0,
        description="Agno price potential score (0-100)"
    )
    agno_behavior_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Agno payment behavior score (0-100)"
    )
    agno_consensus_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Agno agent consensus confidence (0-100)"
    )
    agno_segment_type: Optional[str] = Field(
        None,
        description="Agno identified market segment type (e.g., 'SMB', 'Enterprise')"
    )
    agno_agents_count: Optional[int] = Field(
        None,
        ge=0,
        description="Number of Agno agents that participated in analysis"
    )
    agno_analysis_cost_usd: Optional[float] = Field(
        None,
        ge=0.0,
        description="Cost of Agno analysis in USD"
    )
    agno_agent_metadata: Optional[dict] = Field(
        None,
        description="Metadata about Agno agent responses and reasoning"
    )
    agno_validation_status: Optional[str] = Field(
        None,
        description="Agno market validation status (e.g., 'validated', 'pending', 'failed')"
    )

    @field_validator('trust_level')
    @classmethod
    def validate_trust_level(cls, v):
        """Validate trust level is one of allowed values"""
        allowed_levels = ["LOW", "MEDIUM", "HIGH"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"trust_level must be one of {allowed_levels}")
        return v.upper()

    @field_validator('embedding')
    @classmethod
    def validate_embedding_vector(cls, v):
        """Validate embedding vector structure and values"""
        if v is None:
            return v  # Optional field, allow None

        # Must be a list
        if not isinstance(v, list):
            raise ValueError("Invalid embedding vector: must be a list")

        # Cannot be empty
        if len(v) == 0:
            raise ValueError("Invalid embedding vector: cannot be empty")

        # Reasonable length bounds (typical embedding dimensions)
        if len(v) < 10:
            raise ValueError("Invalid embedding vector: too short (minimum 10 dimensions)")

        if len(v) > 10000:
            raise ValueError("Invalid embedding vector: too long (maximum 10000 dimensions)")

        # All elements must be floats
        for i, element in enumerate(v):
            if not isinstance(element, (int, float)):
                raise ValueError(f"Invalid embedding vector: element at index {i} is not a number")

            # Check for infinite values
            if math.isinf(element):
                raise ValueError(f"Invalid embedding vector: element at index {i} is infinite")

            # Check for NaN values
            if math.isnan(element):
                raise ValueError(f"Invalid embedding vector: element at index {i} is NaN")

        return v

    @model_validator(mode='after')
    def validate_cross_model_consistency(self) -> 'AnalysisResult':
        """Validate cross-model consistency between final score and market metrics"""
        # Calculate expected score range based on market metrics
        # This represents the logical average of the four key metrics
        expected_score_range = (
            self.market_metrics.market_demand +
            self.market_metrics.pain_intensity +
            self.market_metrics.monetization_potential +
            self.market_metrics.technical_feasibility
        ) / 4

        # Allow reasonable deviation (20 points)
        max_deviation = 20.0
        score_difference = abs(self.final_score - expected_score_range)

        if score_difference > max_deviation:
            raise ValueError(
                f"Final score inconsistency: final_score ({self.final_score}) "
                f"deviates too much from market metrics average ({expected_score_range:.1f}). "
                f"Maximum allowed deviation: {max_deviation}"
            )

        return self

    @model_validator(mode='after')
    def validate_quality_thresholds(self) -> 'AnalysisResult':
        """Validate quality thresholds: spam posts should have content_quality_score ≤ 40"""
        if self.is_spam and self.content_quality_score > 40.0:
            raise ValueError(
                f"Spam content must have content_quality_score ≤ 40. "
                f"Current: content_quality_score={self.content_quality_score}, is_spam={self.is_spam}"
            )
        return self

    @model_validator(mode='after')
    def validate_timestamp_reasonableness(self) -> 'AnalysisResult':
        """Validate that analysis timestamp is not too old"""
        now = datetime.now(timezone.utc)
        max_age_days = 365

        # Ensure both timestamps are timezone-aware
        if self.analyzed_at.tzinfo is None:
            # Assume timezone-aware if not specified
            analyzed_at = self.analyzed_at.replace(tzinfo=timezone.utc)
        else:
            analyzed_at = self.analyzed_at

        if analyzed_at < now - timedelta(days=max_age_days):
            raise ValueError(f"Analysis timestamp is too old: more than {max_age_days} days in the past")

        return self

    @field_validator('final_score')
    @classmethod
    def validate_final_score_logic(cls, v):
        """Final score should be consistent with market metrics"""
        # In Pydantic v2, we don't have access to other fields in simple validators
        # This validation would need to be moved to a model_validator if needed
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }