"""
SQLAlchemy database models with pgvector support
"""

from datetime import datetime
from typing import List, Optional

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


class OpportunityCreate:
    """
    Pydantic model for creating new opportunities
    Used to validate data before database insertion
    """

    def __init__(
        self,
        submission_id: str,
        reddit_title: str,
        reddit_url: str,
        subreddit: str,
        reddit_author: Optional[str],
        reddit_upvotes: int,
        reddit_comments_count: int,
        reddit_created_at: datetime,
        app_title: str,
        app_concept: str,
        problem_statement: str,
        target_audience: str,
        core_functions: List[str],
        market_demand: float,
        pain_intensity: float,
        monetization_potential: float,
        competition_level: float,
        technical_feasibility: float,
        final_score: float,
        confidence_score: float,
        trust_level: str,
        embedding: Optional[List[float]] = None,
    ):
        self.submission_id = submission_id
        self.reddit_title = reddit_title
        self.reddit_url = reddit_url
        self.subreddit = subreddit
        self.reddit_author = reddit_author
        self.reddit_upvotes = reddit_upvotes
        self.reddit_comments_count = reddit_comments_count
        self.reddit_created_at = reddit_created_at
        self.app_title = app_title
        self.app_concept = app_concept
        self.problem_statement = problem_statement
        self.target_audience = target_audience
        self.core_functions = core_functions
        self.market_demand = market_demand
        self.pain_intensity = pain_intensity
        self.monetization_potential = monetization_potential
        self.competition_level = competition_level
        self.technical_feasibility = technical_feasibility
        self.final_score = final_score
        self.confidence_score = confidence_score
        self.trust_level = trust_level
        self.embedding = embedding

    def to_db_model(self) -> Opportunity:
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