"""
Reddit data models using Pydantic for validation
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class RedditSubmission(BaseModel):
    """Reddit submission data model with validation"""

    # Core Reddit data
    id: str = Field(..., min_length=3, description="Reddit submission ID")
    title: str = Field(..., min_length=1, max_length=300, description="Submission title")
    text: str = Field(..., description="Submission text content")
    author: str = Field(..., description="Author username")

    # Engagement metrics
    upvotes: int = Field(..., ge=0, description="Number of upvotes")
    downvotes: int = Field(default=0, ge=0, description="Number of downvotes")
    score: int = Field(..., description="Reddit score (upvotes - downvotes)")
    comments_count: int = Field(..., ge=0, description="Number of comments")

    # Metadata
    subreddit: str = Field(..., min_length=1, description="Subreddit name")
    created_utc: datetime = Field(..., description="Creation timestamp")
    permalink: str = Field(..., description="Reddit permalink URL")

    # Optional fields
    url: Optional[str] = Field(None, description="External URL if any")
    is_self: bool = Field(default=True, description="Whether it's a self post")
    over_18: bool = Field(default=False, description="NSFW flag")

    @validator('permalink')
    def validate_permalink(cls, v):
        """Validate permalink format"""
        if not v.startswith('https://reddit.com/') and not v.startswith('/r/'):
            raise ValueError("permalink must be a valid Reddit URL")
        return v

    @validator('created_utc')
    def validate_timestamp(cls, v):
        """Ensure timestamp is in the past"""
        if v > datetime.utcnow():
            raise ValueError("created_utc cannot be in the future")
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RedditComment(BaseModel):
    """Reddit comment data model"""

    id: str = Field(..., min_length=3, description="Comment ID")
    submission_id: str = Field(..., description="Parent submission ID")
    author: str = Field(..., description="Author username")
    text: str = Field(..., min_length=1, description="Comment text")
    upvotes: int = Field(..., ge=0, description="Number of upvotes")
    created_utc: datetime = Field(..., description="Creation timestamp")

    @validator('created_utc')
    def validate_timestamp(cls, v):
        """Ensure timestamp is in the past"""
        if v > datetime.utcnow():
            raise ValueError("created_utc cannot be in the future")
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }