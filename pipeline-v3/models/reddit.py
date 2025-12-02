"""
Reddit data models using Pydantic for validation
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class RedditSubmission(BaseModel):
    """Reddit submission data model with validation"""

    # Core Reddit data
    id: str = Field(..., min_length=3, description="Reddit submission ID")
    title: str = Field(..., min_length=1, max_length=300, description="Submission title")
    text: str = Field(default="", description="Submission text content")
    author: str = Field(..., description="Author username")

    # Engagement metrics
    upvotes: int = Field(..., ge=0, description="Number of upvotes")
    downvotes: int = Field(default=0, ge=0, description="Number of downvotes")
    score: int = Field(..., description="Reddit score (upvotes - downvotes)")
    comments_count: int = Field(..., ge=0, description="Number of comments")

    # Metadata
    subreddit: str = Field(..., description="Subreddit name")
    created_utc: datetime = Field(..., description="Creation timestamp")
    permalink: str = Field(..., description="Reddit permalink URL")

    # Optional fields
    url: Optional[str] = Field(None, description="External URL if any")
    is_self: bool = Field(default=True, description="Whether it's a self post")
    over_18: bool = Field(default=False, description="NSFW flag")

    @field_validator('permalink')
    @classmethod
    def validate_permalink(cls, v):
        """Validate permalink format"""
        if not v.startswith('https://reddit.com/') and not v.startswith('/r/'):
            raise ValueError("permalink must be a valid Reddit URL")
        return v

    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        """Validate URL format when provided"""
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    # Note: Author validation moved to model_validator below to avoid ValidationError wrapper

    @field_validator('created_utc')
    @classmethod
    def validate_timestamp(cls, v):
        """Ensure timestamp is in the past"""
        if v > datetime.now(timezone.utc):
            raise ValueError("created_utc cannot be in the future")
        return v

    @model_validator(mode='after')
    @classmethod
    def validate_score_consistency(cls, v):
        """Validate score consistency with upvotes and downvotes allowing for Reddit vote fuzzing"""
        expected_score = v.upvotes - v.downvotes

        # Allow small variance due to Reddit vote fuzzing (±10%)
        tolerance = max(1, int(expected_score * 0.1))

        if abs(v.score - expected_score) > tolerance:
            raise ValueError(f"Score must approximately equal upvotes minus downvotes within {tolerance} tolerance")
        return v

    @model_validator(mode='after')
    @classmethod
    def validate_negative_score(cls, v):
        """Allow negative scores but warn about them"""
        # Negative scores are possible on Reddit, just log for monitoring
        if v.score < 0:
            import logging
            logging.debug(f"Submission {v.id} has negative score: {v.score}")
        return v

    @model_validator(mode='after')
    @classmethod
    def validate_author_format(cls, v):
        """Validate Reddit username format"""
        author = v.author

        # Check for empty string
        if not author or author.strip() == '':
            raise ValueError("Invalid Reddit username")

        # Check length (Reddit limit is 20 characters)
        if len(author) > 20:
            raise ValueError("Invalid Reddit username")

        # Check for spaces
        if ' ' in author:
            raise ValueError("Invalid Reddit username")

        # Reserved terms check removed to allow bot accounts like AutoModerator
        return v

    @model_validator(mode='after')
    @classmethod
    def validate_subreddit_format(cls, v):
        """Validate subreddit name format"""
        subreddit = v.subreddit
        reserved_terms = ['mod', 'all', 'friends']

        # Check for empty string or whitespace-only
        if not subreddit or subreddit.strip() == '':
            raise ValueError("Invalid subreddit name")

        # Check length (Reddit limit is 21 characters for subreddits)
        if len(subreddit) > 21:
            raise ValueError("Invalid subreddit name")

        # Check for spaces only (allow hyphens for real subreddits)
        if ' ' in subreddit:
            raise ValueError("Invalid subreddit name")

        # Check for reserved terms
        if subreddit.lower() in reserved_terms:
            raise ValueError("Invalid subreddit name")

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
    text: str = Field(..., description="Comment text")
    upvotes: int = Field(..., ge=0, description="Number of upvotes")
    score: Optional[int] = Field(None, description="Comment score (should equal upvotes)")
    created_utc: datetime = Field(..., description="Creation timestamp")

    @field_validator('created_utc')
    @classmethod
    def validate_timestamp(cls, v):
        """Ensure timestamp is in the past"""
        if v > datetime.now(timezone.utc):
            raise ValueError("created_utc cannot be in the future")
        return v

    @model_validator(mode='after')
    @classmethod
    def validate_score_consistency(cls, v):
        """Validate score matches upvotes for comments and prevents negative scores"""
        if v.score is not None:
            # Check if score is negative with positive upvotes (impossible)
            if v.score < 0 and v.upvotes > 0:
                raise ValueError("Comment score cannot be negative with positive upvotes")
            # Check if score matches upvotes (Reddit comment behavior)
            if v.score != v.upvotes:
                raise ValueError(f"Comment score must equal upvotes ({v.upvotes})")
        return v

    @model_validator(mode='after')
    @classmethod
    def validate_author_format(cls, v):
        """Validate Reddit username format (reuse from RedditSubmission)"""
        author = v.author

        # Check for empty string
        if not author or author.strip() == '':
            raise ValueError("Invalid Reddit username")

        # Check length (Reddit limit is 20 characters)
        if len(author) > 20:
            raise ValueError("Invalid Reddit username")

        # Check for spaces
        if ' ' in author:
            raise ValueError("Invalid Reddit username")

        # Reserved terms check removed to allow bot accounts like AutoModerator
        return v

    @model_validator(mode='after')
    @classmethod
    def validate_comment_length(cls, v):
        """Validate Reddit comment length limits"""
        text = v.text
        # Check for empty or whitespace-only
        if not text or text.strip() == '':
            raise ValueError("Comment length is invalid")
        # Check for too short (less than 3 characters to be meaningful)
        if len(text.strip()) < 3:
            raise ValueError("Comment length is invalid")
        # Check for too long
        if len(text) > 10000:
            raise ValueError("Comment length is invalid")
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }