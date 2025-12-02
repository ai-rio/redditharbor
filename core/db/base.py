"""SQLAlchemy base configuration for RedditHarbor ORM.

This module provides the declarative base and common configuration
for all SQLAlchemy ORM models in RedditHarbor.

Components:
- Base: SQLAlchemy declarative base class for all models
- Common columns and functionality for database entities
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    String,
    Text,
    BigInteger,
    Integer,
    Float,
    Boolean,
    Column
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

# Create declarative base
Base = declarative_base()


class TimestampMixin:
    """Mixin class for timestamp functionality.

    Provides created_at and updated_at timestamp columns that are
    automatically managed for all models that inherit from this mixin.
    """

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when record was created"
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when record was last updated"
    )


class UUIDMixin:
    """Mixin class for UUID primary key functionality.

    Provides a UUID primary key column for models that use UUIDs
    as their primary identifier.
    """

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        comment="UUID primary key"
    )


class RedditIDMixin:
    """Mixin class for Reddit-specific ID fields.

    Provides Reddit-specific identifier fields that are common
    across Reddit data models (submissions, comments, redditors).
    """

    reddit_id = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Reddit's internal ID (e.g., t3_abc123 for submissions)"
    )

    reddit_full_id = Column(
        String(50),
        nullable=True,
        comment="Full Reddit ID with type prefix (e.g., t3_abc123)"
    )


class ScoringMixin:
    """Mixin class for scoring and metrics.

    Provides common scoring fields for Reddit content.
    """

    score = Column(
        BigInteger,
        nullable=True,
        default=0,
        comment="Reddit score (upvotes - downvotes)"
    )

    reddit_score = Column(
        BigInteger,
        nullable=True,
        default=0,
        comment="Original Reddit score from API"
    )

    upvotes = Column(
        BigInteger,
        nullable=True,
        default=0,
        comment="Number of upvotes"
    )

    downvotes = Column(
        BigInteger,
        nullable=True,
        default=0,
        comment="Number of downvotes"
    )

    num_comments = Column(
        BigInteger,
        nullable=True,
        default=0,
        comment="Number of comments"
    )


class TrustMixin:
    """Mixin class for trust scoring and validation.

    Provides trust-related fields for content validation and scoring.
    """

    trust_score = Column(
        Float,
        nullable=True,
        comment="Trust score (0.0-1.0) for content validation"
    )

    trust_level = Column(
        String(50),
        nullable=True,
        comment="Trust level classification (e.g., 'high', 'medium', 'low')"
    )


class DLTMetaMixin:
    """Mixin class for DLT pipeline metadata.

    Provides metadata fields for DLT (Data Load Tool) integration.
    """

    _dlt_id = Column(
        String(50),
        nullable=False,
        index=True,
        comment="DLT internal ID"
    )

    _dlt_load_id = Column(
        String(50),
        nullable=False,
        index=True,
        comment="DLT load batch ID"
    )