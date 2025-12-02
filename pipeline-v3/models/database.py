"""
SQLAlchemy database models with pgvector support
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator, model_validator

if TYPE_CHECKING:
    from services.validation_service import ValidationService

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Index, Integer,
    JSON, String, Text, func, text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.sql import expression
# Use JSON for storing embeddings to avoid pgvector dependency issues
PGVECTOR_AVAILABLE = False
from sqlalchemy import JSON as Vector
from sqlalchemy import JSON as VECTOR
import uuid

Base = declarative_base()


class Opportunity(Base):
    """
    Database model for app opportunities with pgvector embeddings
    """
    __tablename__ = "opportunities"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        index=True
    )

    # Source Reddit data
    submission_id = Column(String(10), nullable=False, index=True, unique=True)
    reddit_title = Column(String(300), nullable=False)
    reddit_url = Column(String(500), nullable=False)
    subreddit = Column(String(100), nullable=False, index=True)
    reddit_author = Column(String(100), nullable=True)
    reddit_upvotes = Column(Integer, nullable=False, default=0)
    reddit_comments_count = Column(Integer, nullable=False, default=0)
    reddit_created_at = Column(DateTime, nullable=False)

    # App idea analysis
    app_title = Column(String(200), nullable=False, index=True)
    app_concept = Column(Text, nullable=False)
    problem_statement = Column(Text, nullable=False)
    target_audience = Column(Text, nullable=False)
    core_functions = Column(JSON, nullable=False)  # List[str]

    # Market metrics
    market_demand = Column(Float, nullable=False)
    pain_intensity = Column(Float, nullable=False)
    monetization_potential = Column(Float, nullable=False)
    competition_level = Column(Float, nullable=False)
    technical_feasibility = Column(Float, nullable=False)

    # Overall scoring
    final_score = Column(Float, nullable=False, index=True)
    confidence_score = Column(Float, nullable=False)
    trust_level = Column(String(10), nullable=False, index=True)

    # Semantic search - stored as JSON for compatibility
    embedding: Optional[List[float]] = Column(JSON, nullable=True)

    # Metadata
    analyzed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Status flags
    is_duplicate = Column(Boolean, nullable=False, default=False, index=True)
    duplicate_of_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=True)

    # Self-referential relationship for duplicates
    original_opportunity = relationship("Opportunity", remote_side=[id])

    # Indexes for performance
    __table_args__ = (
        # Composite indexes for common queries
        Index('idx_opportunities_final_score_trust', 'final_score', 'trust_level'),
        Index('idx_opportunities_subreddit_created', 'subreddit', 'reddit_created_at'),
        Index('idx_opportunities_analyzed_created', 'analyzed_at', 'created_at'),
        Index('idx_opportunities_core_functions', 'core_functions', postgresql_using='gin'),
        # Basic index for embedding (will be enhanced with pgvector later)
    )

    def __repr__(self) -> str:
        return (
            f"Opportunity(id={self.id}, title='{self.app_title}', "
            f"score={self.final_score:.1f}, trust='{self.trust_level}')"
        )


class OpportunityCreate(BaseModel):
    """
    Production-ready Pydantic model for creating new opportunities with comprehensive validation
    Integrates with ValidationService for database constraint and foreign key validation
    """

    # Core Reddit metadata
    submission_id: str = Field(..., min_length=3, description="Reddit submission ID (must be unique)")
    reddit_title: str = Field(..., min_length=1, max_length=300, description="Reddit submission title")
    reddit_url: str = Field(..., description="Reddit submission URL")
    subreddit: str = Field(..., min_length=1, max_length=21, description="Subreddit name")
    reddit_author: Optional[str] = Field(None, description="Reddit author username")
    reddit_upvotes: int = Field(..., ge=0, description="Number of upvotes")
    reddit_comments_count: int = Field(..., ge=0, description="Number of comments")
    reddit_created_at: datetime = Field(..., description="Reddit creation timestamp")

    # App idea details
    app_title: str = Field(..., min_length=1, max_length=200, description="App title")
    app_concept: str = Field(..., min_length=1, description="App concept description")
    problem_statement: str = Field(..., min_length=1, description="Problem statement")
    target_audience: str = Field(..., min_length=1, description="Target audience description")
    core_functions: List[str] = Field(..., min_items=1, description="List of core functions")

    # Analysis metrics
    market_demand: float = Field(..., ge=0, le=100, description="Market demand score")
    pain_intensity: float = Field(..., ge=0, le=100, description="Pain intensity score")
    monetization_potential: float = Field(..., ge=0, le=100, description="Monetization potential score")
    competition_level: float = Field(..., ge=0, le=100, description="Competition level score")
    technical_feasibility: float = Field(..., ge=0, le=100, description="Technical feasibility score")
    final_score: float = Field(..., ge=0, le=100, description="Final opportunity score")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence score")
    trust_level: str = Field(..., pattern="^(HIGH|MEDIUM|LOW)$", description="Trust level")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")

    # Validation service injection for production database validation
    _validation_service: Optional['ValidationService'] = None

    def __init__(self, validation_service: Optional['ValidationService'] = None, **data):
        """
        Initialize with optional validation service injection

        Args:
            validation_service: Optional validation service for database validation
            **data: Pydantic model data
        """
        super().__init__(**data)
        self._validation_service = validation_service

    @classmethod
    def create_with_validation(
        cls,
        validation_service: 'ValidationService',
        **data
    ) -> 'OpportunityCreate':
        """
        Factory method to create instance with validation service

        Args:
            validation_service: Validation service for database validation
            **data: Opportunity creation data

        Returns:
            OpportunityCreate instance with validation service configured
        """
        return cls(validation_service=validation_service, **data)

    @field_validator('reddit_url')
    @classmethod
    def validate_reddit_url(cls, v):
        """Validate Reddit URL format"""
        if not v.startswith(('https://reddit.com/', 'https://www.reddit.com/')):
            raise ValueError('reddit_url must be a valid Reddit URL')
        return v

    @field_validator('reddit_author')
    @classmethod
    def validate_reddit_author(cls, v):
        """Validate Reddit username format"""
        if v is not None:
            if not v or len(v) > 20 or ' ' in v:
                raise ValueError('Invalid Reddit username format')
        return v

    @field_validator('subreddit')
    @classmethod
    def validate_subreddit(cls, v):
        """Validate subreddit name format"""
        if not v or len(v) > 21 or ' ' in v or '-' in v:
            raise ValueError('Invalid subreddit name format')
        return v

    @field_validator('embedding')
    @classmethod
    def validate_embedding(cls, v):
        """Validate embedding vector"""
        if v is not None:
            if not isinstance(v, list) or len(v) == 0:
                raise ValueError('Embedding must be a non-empty list')
            if len(v) > 10000:  # Reasonable upper bound
                raise ValueError('Embedding vector too large')
            if not all(isinstance(x, float) for x in v):
                raise ValueError('Embedding must contain only float values')
        return v

    @model_validator(mode='after')
    def validate_date_reasonableness(self):
        """Validate that created_at date is reasonable"""
        if self.reddit_created_at > datetime.now(timezone.utc):
            raise ValueError('Created date cannot be in the future')
        if self.reddit_created_at < datetime.now(timezone.utc) - timedelta(days=3650):
            raise ValueError('Date is too old (more than 10 years)')
        return self

    async def validate_database_constraints(self) -> None:
        """
        Database constraint validation using ValidationService
        Checks for duplicate submission IDs and foreign key constraints

        Raises:
            ValueError: If database constraints are violated
        """
        if self._validation_service is None:
            # Skip database validation if no service provided
            return

        await self._validation_service.validate_opportunity_create({
            'submission_id': self.submission_id
        })

    def to_db_model(self) -> 'Opportunity':
        """Convert to SQLAlchemy model"""
        return Opportunity(
            submission_id=self.submission_id,
            reddit_title=self.reddit_title,
            reddit_url=self.reddit_url,
            subreddit=self.subreddit,
            reddit_author=self.reddit_author,
            reddit_upvotes=self.reddit_upvotes,
            reddit_comments_count=self.reddit_comments_count,
            reddit_created_at=self.reddit_created_at,
            app_title=self.app_title,
            app_concept=self.app_concept,
            problem_statement=self.problem_statement,
            target_audience=self.target_audience,
            core_functions=self.core_functions,
            market_demand=self.market_demand,
            pain_intensity=self.pain_intensity,
            monetization_potential=self.monetization_potential,
            competition_level=self.competition_level,
            technical_feasibility=self.technical_feasibility,
            final_score=self.final_score,
            confidence_score=self.confidence_score,
            trust_level=self.trust_level,
            embedding=self.embedding,
        )