"""SQLAlchemy models matching actual database schema."""

from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class Submission(Base):
    """SQLAlchemy model for submissions table."""
    __tablename__ = 'submissions'

    id = Column(UUID(as_uuid=True), primary_key=True)
    reddit_id = Column(String(100))
    redditor_id = Column(UUID)
    subreddit_id = Column(UUID)
    title = Column(Text)
    content = Column(Text)
    url = Column(Text)
    score = Column(Integer)
    num_comments = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}