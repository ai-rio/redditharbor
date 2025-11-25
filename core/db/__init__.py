"""RedditHarbor Database ORM Module.

This module provides SQLAlchemy ORM models and database session management
for RedditHarbor data storage and retrieval.

Components:
- Base: SQLAlchemy declarative base for all models
- Session: Database session management with connection pooling
- Models: ORM models for submissions, redditors, comments, etc.

Usage:
    from core.db import get_db_session, Submission
    with get_db_session() as session:
        submissions = session.query(Submission).limit(10).all()
"""

from .base import Base
from .session import get_db_session, engine, SessionLocal
from .models import Submission

__all__ = [
    'Base',
    'get_db_session',
    'engine',
    'SessionLocal',
    'Submission'
]