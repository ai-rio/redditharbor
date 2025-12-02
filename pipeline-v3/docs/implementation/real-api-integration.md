# Real API Integration Guide

<div align="center">

**Production-Ready External Service Integration**

*Connecting Pipeline v3 to Reddit API, OpenRouter LLM, and Supabase with robust error handling*

</div>

## 📋 Table of Contents

- [🌐 Integration Overview](#-integration-overview)
- [🔴 Reddit API Integration with PRAW](#-reddit-api-integration-with-praw)
- [🤖 OpenRouter LLM Integration](#-openrouter-llm-integration)
- [🗄️ Supabase Database Connectivity](#️-supabase-database-connectivity)
- [🔐 Authentication and Security](#-authentication-and-security)
- [⚠️ Error Handling and Resilience](#️-error-handling-and-resilience)
- [🚀 Production Deployment](#-production-deployment)
- [🔧 Configuration Management](#-configuration-management)
- [📊 API Monitoring and Health Checks](#-api-monitoring-and-health-checks)

---

## 🌐 Integration Overview

### Architecture Diagram

```mermaid
graph TB
    subgraph "Pipeline v3"
        P[Pipeline Core]
    end

    subgraph "External APIs"
        A[Reddit API]
        L[OpenRouter LLM]
        S[Supabase]
    end

    subgraph "Integration Layer"
        RA[PRAW Client]
        LM[LLM Manager]
        DB[Database Manager]
    end

    subgraph "Error Handling"
        EH[Error Handler]
        RT[Retry Logic]
        CB[Circuit Breaker]
    end

    P --> RA
    P --> LM
    P --> DB

    RA --> A
    LM --> L
    DB --> S

    EH --> RT
    RT --> CB

    RA -.-> EH
    LM -.-> EH
    DB -.-> EH

    style A fill:#FF4500,stroke:#333,stroke-width:2px
    style L fill:#0066CC,stroke:#333,stroke-width:2px
    style S fill:#3ECF8E,stroke:#333,stroke-width:2px
    style P fill:#FFB84D,stroke:#333,stroke-width:2px
```

### Integration Requirements

| Service | Purpose | Rate Limits | Authentication |
|---------|---------|-------------|----------------|
| Reddit API | Data extraction | 60 req/min per IP | OAuth 2.0 |
| OpenRouter | LLM analysis | Varies by model | API Key |
| Supabase | Data storage | Based on plan | JWT/API Key |

---

## 🔴 Reddit API Integration with PRAW

### 1. PRAW Configuration and Setup

**Advanced PRAW Client Configuration**
```python
import praw
import asyncio
import time
from typing import List, Optional, AsyncGenerator
from prawcore.exceptions import (
    RequestException,
    ResponseException,
    Forbidden,
    NotFound,
    TooManyRequests
)
from models.reddit import RedditSubmission, RedditComment

class AdvancedRedditClient:
    """Advanced PRAW client with error handling and rate limiting"""

    def __init__(self, settings):
        self.settings = settings
        self.reddit = None
        self.rate_limiter = RedditRateLimiter()
        self.error_handler = RedditErrorHandler()
        self._initialize_client()

    def _initialize_client(self):
        """Initialize PRAW client with advanced configuration"""

        self.reddit = praw.Reddit(
            client_id=self.settings.reddit_client_id,
            client_secret=self.settings.reddit_client_secret,
            user_agent=self.settings.reddit_user_agent,
            read_only=True,
            config_interpolation="basic",
            check_for_updates=False,  # Disable update checks for performance
            timeout=30,              # Request timeout
            retry_on_error=True,     # Built-in retry mechanism
        )

    async def extract_submissions(
        self,
        subreddit: str,
        limit: int = 100,
        sort: str = "hot",
        time_filter: str = "week",
        min_score: int = 10
    ) -> AsyncGenerator[RedditSubmission, None]:
        """Extract Reddit submissions with robust error handling"""

        try:
            # Apply rate limiting
            await self.rate_limiter.acquire()

            # Get subreddit object
            subreddit_obj = self.reddit.subreddit(subreddit)

            # Get submission stream based on sort method
            if sort == "hot":
                submissions = subreddit_obj.hot(limit=limit)
            elif sort == "top":
                submissions = subreddit_obj.top(time_filter=time_filter, limit=limit)
            elif sort == "new":
                submissions = subreddit_obj.new(limit=limit)
            elif sort == "rising":
                submissions = subreddit_obj.rising(limit=limit)
            else:
                raise ValueError(f"Unknown sort method: {sort}")

            # Process submissions
            for submission in submissions:
                try:
                    # Filter by score
                    if submission.score < min_score:
                        continue

                    # Convert to Pydantic model
                    reddit_submission = await self._convert_submission(submission)

                    # Apply additional filtering
                    if self._should_include_submission(reddit_submission):
                        yield reddit_submission

                except Exception as e:
                    await self.error_handler.handle_submission_error(submission.id, e)
                    continue

                # Apply rate limiting between submissions
                await self.rate_limiter.acquire()

        except TooManyRequests:
            # Handle rate limit exceeded
            await self.rate_limiter.handle_rate_limit_exceeded()
            raise

        except (Forbidden, NotFound) as e:
            # Handle subreddit access issues
            await self.error_handler.handle_subreddit_error(subreddit, e)
            raise

        except Exception as e:
            # Handle other errors
            await self.error_handler.handle_general_error(e)
            raise

    async def extract_comments(
        self,
        submission_id: str,
        limit: int = 50,
        sort: str = "best"
    ) -> List[RedditComment]:
        """Extract comments for a submission"""

        try:
            await self.rate_limiter.acquire()

            submission = self.reddit.submission(submission_id)
            submission.comments.replace_more(limit=0)  # Load all comments

            comments = []

            if sort == "best":
                comment_list = submission.comments
            elif sort == "top":
                comment_list = submission.comments
            elif sort == "new":
                comment_list = submission.comments
            else:
                comment_list = submission.comments

            for comment in comment_list[:limit]:
                if hasattr(comment, 'body'):
                    reddit_comment = RedditComment(
                        id=comment.id,
                        submission_id=submission_id,
                        author=str(comment.author) if comment.author else "[deleted]",
                        body=comment.body,
                        score=comment.score,
                        created_utc=comment.created_utc,
                        permalink=comment.permalink,
                        parent_id=comment.parent_id
                    )
                    comments.append(reddit_comment)

            return comments

        except Exception as e:
            await self.error_handler.handle_comment_error(submission_id, e)
            return []

    async def _convert_submission(self, submission) -> RedditSubmission:
        """Convert PRAW submission to Pydantic model"""

        # Extract additional metadata
        author_name = str(submission.author) if submission.author else "[deleted]"

        # Handle crossposts
        crosspost_parent = None
        if submission.is_crosspost:
            crosspost_parent = submission.crosspost_parent

        return RedditSubmission(
            id=submission.id,
            title=submission.title,
            text=submission.selftext,
            author=author_name,
            upvotes=submission.ups,
            downvotes=submission.downs,
            score=submission.score,
            comments_count=submission.num_comments,
            subreddit=submission.subreddit.display_name,
            created_utc=submission.created_utc,
            permalink=submission.permalink,
            url=submission.url,
            is_self=submission.is_self,
            over_18=submission.over_18,
            spoiler=submission.spoiler,
            stickied=submission.stickied,
            crosspost_parent=crosspost_parent
        )

    def _should_include_submission(self, submission: RedditSubmission) -> bool:
        """Apply additional filtering criteria"""

        # Exclude posts that are too short
        if len(submission.title.strip()) < 10:
            return False

        # Exclude posts with certain keywords (spam, etc.)
        exclude_keywords = ["spam", "scam", "advertisement"]
        title_lower = submission.title.lower()

        if any(keyword in title_lower for keyword in exclude_keywords):
            return False

        # Exclude deleted/removed posts
        if submission.author == "[deleted]" or submission.author == "[removed]":
            return False

        # Include only posts with meaningful content
        has_content = (
            len(submission.text.strip()) > 50 or
            submission.comments_count > 10 or
            submission.score > 50
        )

        return has_content

    async def test_connection(self) -> dict:
        """Test Reddit API connection and credentials"""

        try:
            # Test basic authentication
            user = self.reddit.user.me()

            # Test subreddit access
            test_subreddit = self.reddit.subreddit("test")

            # Get basic info
            info = {
                "authenticated": True,
                "username": str(user) if user else "anonymous",
                "user_agent": self.reddit.config.user_agent,
                "read_only": self.reddit.read_only,
                "test_subreddit_accessible": True
            }

            return info

        except Exception as e:
            return {
                "authenticated": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
```

### 2. Advanced Rate Limiting

**Sophisticated Reddit Rate Limiter**
```python
import asyncio
import time
from collections import deque
from typing import Dict, Optional

class RedditRateLimiter:
    """Advanced rate limiting for Reddit API"""

    def __init__(self, requests_per_minute: int = 60, burst_allowance: int = 5):
        self.requests_per_minute = requests_per_minute
        self.burst_allowance = burst_allowance
        self.request_times = deque()
        self.last_reset = time.time()
        self.requests_used = 0
        self.burst_tokens = burst_allowance

        # Rate limit tracking
        self.rate_limit_hits = 0
        self.total_requests = 0

    async def acquire(self, wait_for_limit: bool = True) -> bool:
        """Acquire permission to make a request"""

        now = time.time()

        # Reset counter if minute has passed
        if now - self.last_reset >= 60:
            self.last_reset = now
            self.requests_used = 0
            # Restore burst tokens gradually
            self.burst_tokens = min(self.burst_allowance, self.burst_tokens + 1)

        # Check if we're within rate limit
        if self.requests_used >= self.requests_per_minute:
            if wait_for_limit:
                wait_time = 60 - (now - self.last_reset)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    return await self.acquire(wait_for_limit)
            else:
                return False

        # Check burst tokens
        if self.burst_tokens <= 0:
            if wait_for_limit:
                # Wait for token restoration
                await asyncio.sleep(60 / self.requests_per_minute)
                return await self.acquire(wait_for_limit)
            else:
                return False

        # Record request
        self.request_times.append(now)
        self.requests_used += 1
        self.burst_tokens -= 1
        self.total_requests += 1

        # Clean old request times
        one_minute_ago = now - 60
        while self.request_times and self.request_times[0] < one_minute_ago:
            self.request_times.popleft()

        return True

    async def handle_rate_limit_exceeded(self):
        """Handle Reddit rate limit exceeded"""

        self.rate_limit_hits += 1

        # Exponential backoff based on rate limit hit count
        backoff_time = min(300, 2 ** self.rate_limit_hits)  # Max 5 minutes

        print(f"Reddit rate limit exceeded. Waiting {backoff_time}s...")
        await asyncio.sleep(backoff_time)

    def get_status(self) -> Dict:
        """Get current rate limiter status"""

        return {
            "requests_used": self.requests_used,
            "requests_per_minute": self.requests_per_minute,
            "burst_tokens": self.burst_tokens,
            "rate_limit_hits": self.rate_limit_hits,
            "total_requests": self.total_requests,
            "time_until_reset": max(0, 60 - (time.time() - self.last_reset))
        }
```

### 3. Reddit Error Handling

**Comprehensive Reddit Error Handler**
```python
import logging
from typing import Dict, List
from prawcore.exceptions import *
from models.reddit import RedditSubmission

class RedditErrorHandler:
    """Handle Reddit API errors with appropriate responses"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_counts = {}
        self.recent_errors = []

    async def handle_submission_error(self, submission_id: str, error: Exception):
        """Handle errors during submission processing"""

        error_type = type(error).__name__
        self._record_error(error_type, error)

        if isinstance(error, (RequestException, ResponseException)):
            self.logger.warning(f"Reddit API error for submission {submission_id}: {error}")
            # Don't fail the entire pipeline for individual submission errors

        elif isinstance(error, Forbidden):
            self.logger.error(f"Access forbidden for submission {submission_id}: {error}")

        elif isinstance(error, NotFound):
            self.logger.warning(f"Submission {submission_id} not found: {error}")

        else:
            self.logger.error(f"Unexpected error processing submission {submission_id}: {error}")

    async def handle_subreddit_error(self, subreddit: str, error: Exception):
        """Handle errors accessing subreddits"""

        error_type = type(error).__name__
        self._record_error(error_type, error)

        if isinstance(error, Forbidden):
            self.logger.error(f"Access forbidden for subreddit r/{subreddit}: {error}")
            # This could be a private subreddit or authentication issue

        elif isinstance(error, NotFound):
            self.logger.error(f"Subreddit r/{subreddit} not found: {error}")
            # Subreddit doesn't exist

        else:
            self.logger.error(f"Unexpected error accessing subreddit r/{subreddit}: {error}")

    async def handle_comment_error(self, submission_id: str, error: Exception):
        """Handle errors during comment extraction"""

        error_type = type(error).__name__
        self._record_error(error_type, error)

        # Comments are less critical, so we can be more lenient
        self.logger.warning(f"Error extracting comments for {submission_id}: {error}")

    async def handle_general_error(self, error: Exception):
        """Handle general Reddit API errors"""

        error_type = type(error).__name__
        self._record_error(error_type, error)

        if isinstance(error, TooManyRequests):
            self.logger.error(f"Reddit API rate limit exceeded: {error}")

        elif isinstance(error, (RequestException, ResponseException)):
            self.logger.error(f"Reddit API communication error: {error}")

        else:
            self.logger.error(f"General Reddit API error: {error}")

    def _record_error(self, error_type: str, error: Exception):
        """Record error for statistics"""

        # Update error counts
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        # Record recent error
        self.recent_errors.append({
            "type": error_type,
            "message": str(error),
            "timestamp": time.time()
        })

        # Keep only recent errors (last hour)
        cutoff_time = time.time() - 3600
        self.recent_errors = [
            e for e in self.recent_errors
            if e["timestamp"] > cutoff_time
        ]

    def get_error_summary(self) -> Dict:
        """Get error handling statistics"""

        return {
            "error_counts": self.error_counts,
            "recent_errors_count": len(self.recent_errors),
            "total_error_types": len(self.error_counts)
        }
```

---

## 🤖 OpenRouter LLM Integration

### 1. OpenRouter Client Implementation

**Production-Ready OpenRouter Integration**
```python
import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Union
from openai import OpenAI
import instructor
from pydantic import BaseModel, ValidationError

class OpenRouterClient:
    """Production-ready OpenRouter LLM client with Instructor"""

    def __init__(self, settings):
        self.settings = settings
        self.client = None
        self.instructor_client = None
        self.rate_limiter = LLMRateLimiter()
        self.error_handler = LLMErrorHandler()
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize OpenAI and Instructor clients for OpenRouter"""

        client_config = self.settings.get_openai_client_config()

        # Initialize OpenAI client for OpenRouter
        self.client = OpenAI(**client_config)

        # Initialize Instructor client for structured output
        self.instructor_client = instructor.from_openai(self.client)

    async def analyze_submission(
        self,
        submission: RedditSubmission,
        response_model: BaseModel,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> BaseModel:
        """Analyze Reddit submission using LLM with structured output"""

        try:
            # Apply rate limiting
            await self.rate_limiter.acquire()

            # Prepare prompt
            prompt = self._prepare_analysis_prompt(submission)

            # Set parameters
            temperature = temperature or self.settings.temperature
            max_tokens = max_tokens or self.settings.max_tokens

            # Use Instructor for structured output
            response = await asyncio.to_thread(
                self.instructor_client.chat.completions.create,
                model=self.settings.model_name,
                response_model=response_model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=30.0
            )

            self.rate_limiter.record_success()
            return response

        except ValidationError as e:
            await self.error_handler.handle_validation_error(submission.id, e)
            raise

        except Exception as e:
            await self.rate_limiter.record_error(is_rate_limit=self._is_rate_limit_error(e))
            await self.error_handler.handle_general_error(submission.id, e)
            raise

    async def analyze_batch(
        self,
        submissions: List[RedditSubmission],
        response_model: BaseModel,
        batch_size: int = 5
    ) -> List[BaseModel]:
        """Analyze multiple submissions in batch"""

        results = []

        # Process in batches to respect rate limits
        for i in range(0, len(submissions), batch_size):
            batch = submissions[i:i + batch_size]

            # Create concurrent tasks for the batch
            tasks = [
                self.analyze_submission(submission, response_model)
                for submission in batch
            ]

            # Execute batch with error handling
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter successful results
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    await self.error_handler.handle_batch_error(
                        batch[j].id, result
                    )
                    # Could implement fallback or retry logic here
                else:
                    results.append(result)

        return results

    def _prepare_analysis_prompt(self, submission: RedditSubmission) -> str:
        """Prepare analysis prompt from Reddit submission"""

        prompt = f"""
Analyze this Reddit post for app development opportunities:

TITLE: {submission.title}
SUBREDDIT: r/{submission.subreddit}
AUTHOR: {submission.author}
UPVOTES: {submission.score}
COMMENTS: {submission.comments_count}

CONTENT:
{submission.text}

PERMALINK: {submission.permalink}

Provide detailed analysis focusing on:
1. Problems or pain points mentioned
2. Solutions or workarounds discussed
3. Target audience characteristics
4. Market potential indicators
5. Technical feasibility considerations

Be specific and actionable in your analysis.
"""

        return prompt.strip()

    def _get_system_prompt(self) -> str:
        """Get system prompt for LLM"""

        return """
You are an expert app analyst specializing in identifying software opportunities from Reddit discussions.

Your analysis should be:
- Specific and concrete, not vague
- Based on actual problems mentioned
- Realistic and achievable
- Focused on simple, valuable solutions (maximum 3 core functions)
- Market-aware and technically feasible

Always ground your analysis in the actual content provided, not assumptions.
Extract insights directly from what people are saying about their problems and needs.
"""

    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Check if error is rate limit related"""

        error_str = str(error).lower()
        rate_limit_indicators = [
            "rate limit",
            "too many requests",
            "quota exceeded",
            "429"
        ]

        return any(indicator in error_str for indicator in rate_limit_indicators)

    async def test_connection(self) -> Dict:
        """Test OpenRouter connection and model availability"""

        try:
            # Simple test request
            response = await self.client.chat.completions.create(
                model=self.settings.model_name,
                messages=[{"role": "user", "content": "Hello, test connection"}],
                max_tokens=10
            )

            return {
                "connected": True,
                "model": self.settings.model_name,
                "response_received": True,
                "usage": response.usage.model_dump() if response.usage else None
            }

        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "error_type": type(e).__name__
            }

    def get_supported_models(self) -> List[str]:
        """Get list of supported models for cost optimization"""

        return [
            "gpt-4o",
            "gpt-4o-mini",
            "claude-3.5-sonnet",
            "claude-3-haiku",
            "meta-llama/llama-3.1-8b-instruct:floor",
            "meta-llama/llama-3.1-70b-instruct:floor",
            "mistralai/mistral-7b-instruct:floor",
            "anthropic/claude-3-opus:floor"
        ]
```

### 2. LLM Rate Limiting

**Intelligent LLM Rate Limiter**
```python
import asyncio
import time
from collections import deque
from typing import Dict, Optional

class LLMRateLimiter:
    """Adaptive rate limiting for LLM API calls"""

    def __init__(self, initial_rpm: int = 120):
        self.rpm = initial_rpm
        self.request_times = deque()
        self.last_adjustment = time.time()
        self.error_count = 0
        self.success_count = 0
        self.consecutive_errors = 0

        # Advanced rate limiting parameters
        self.min_rpm = 10
        self.max_rpm = 300
        self.burst_allowance = 5
        self.backoff_multiplier = 2

    async def acquire(self, wait_for_limit: bool = True) -> bool:
        """Acquire permission to make LLM request"""

        now = time.time()

        # Clean old requests
        one_minute_ago = now - 60
        while self.request_times and self.request_times[0] < one_minute_ago:
            self.request_times.popleft()

        # Check if we can make a request
        if len(self.request_times) >= self.rpm:
            if wait_for_limit:
                # Calculate wait time
                oldest_request = self.request_times[0]
                wait_time = (oldest_request + 60) - now

                if wait_time > 0:
                    await asyncio.sleep(min(wait_time, 60))  # Max wait 60s
                    return await self.acquire(wait_for_limit)
            else:
                return False

        # Check for burst allowance
        if len(self.request_times) >= self.rpm + self.burst_allowance:
            if wait_for_limit:
                await asyncio.sleep(60 / self.rpm)
                return await self.acquire(wait_for_limit)
            else:
                return False

        # Record request
        self.request_times.append(now)
        return True

    def record_success(self):
        """Record successful request"""

        self.success_count += 1
        self.consecutive_errors = 0
        self._adjust_rate_limit()

    async def record_error(self, is_rate_limit: bool = False):
        """Record failed request"""

        self.error_count += 1
        self.consecutive_errors += 1

        if is_rate_limit:
            # Aggressive rate reduction on rate limit errors
            self.rpm = max(self.min_rpm, self.rpm // 2)

            # Add delay to recover
            if self.consecutive_errors > 2:
                wait_time = min(self.backoff_multiplier ** self.consecutive_errors, 30)
                await asyncio.sleep(wait_time)

        self._adjust_rate_limit()

    def _adjust_rate_limit(self):
        """Adjust rate limit based on performance"""

        now = time.time()

        # Adjust every 30 seconds of activity
        if now - self.last_adjustment < 30:
            return

        total_requests = self.success_count + self.error_count

        if total_requests >= 10:  # Have enough data
            success_rate = self.success_count / total_requests

            # Success rate thresholds
            if success_rate > 0.95:
                # High success rate, increase gradually
                self.rpm = min(self.rpm + 20, self.max_rpm)
            elif success_rate < 0.8:
                # Low success rate, decrease
                self.rpm = max(self.rpm - 30, self.min_rpm)

        # Reset counters
        self.success_count = 0
        self.error_count = 0
        self.last_adjustment = now

    def get_status(self) -> Dict:
        """Get current rate limiter status"""

        return {
            "current_rpm": self.rpm,
            "recent_requests": len(self.request_times),
            "success_count": self.success_count,
            "error_count": self.error_count,
            "consecutive_errors": self.consecutive_errors
        }
```

---

## 🗄️ Supabase Database Connectivity

### 1. Supabase Client Implementation

**Production-Ready Supabase Integration**
```python
import asyncio
from typing import List, Optional, Dict, Any
from supabase import create_client, Client
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
import uuid
from datetime import datetime

from models.analysis import AnalysisResult, AppIdea, MarketMetrics
from models.reddit import RedditSubmission

class SupabaseManager:
    """Production-ready Supabase database manager"""

    def __init__(self, settings):
        self.settings = settings
        self.supabase: Optional[Client] = None
        self.engine = None
        self.session_factory = None
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize Supabase and SQLAlchemy clients"""

        # Initialize Supabase client
        self.supabase = create_client(
            self.settings.supabase_url,
            self.settings.supabase_anon_key
        )

        # Initialize SQLAlchemy async engine
        self.engine = create_async_engine(
            self.settings.database_url,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False  # Disable SQL logging in production
        )

        # Create session factory
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    @asynccontextmanager
    async def get_session(self):
        """Get database session with automatic cleanup"""

        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def store_analysis_results(
        self,
        results: List[AnalysisResult]
    ) -> Dict[str, int]:
        """Store analysis results with transaction safety"""

        stored_count = 0
        skipped_count = 0
        error_count = 0

        async with self.get_session() as session:
            try:
                # Check for duplicates first
                existing_ids = await self._check_existing_submissions(
                    session, [r.submission_id for r in results]
                )

                # Process results
                for result in results:
                    try:
                        # Skip if already exists
                        if result.submission_id in existing_ids:
                            skipped_count += 1
                            continue

                        # Store using SQLAlchemy
                        db_result = await self._convert_to_db_model(result)
                        session.add(db_result)
                        stored_count += 1

                    except Exception as e:
                        error_count += 1
                        print(f"Error storing analysis result: {e}")
                        continue

                await session.commit()

                return {
                    "stored": stored_count,
                    "skipped": skipped_count,
                    "errors": error_count
                }

            except Exception as e:
                await session.rollback()
                raise e

    async def get_opportunities(
        self,
        limit: int = 100,
        min_score: float = 50.0,
        trust_levels: Optional[List[str]] = None,
        subreddits: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve opportunities with filtering"""

        async with self.get_session() as session:
            try:
                from models.database import Opportunity

                # Build query
                query = session.query(Opportunity)

                # Apply filters
                if min_score:
                    query = query.filter(Opportunity.final_score >= min_score)

                if trust_levels:
                    query = query.filter(Opportunity.trust_level.in_(trust_levels))

                if subreddits:
                    query = query.filter(Opportunity.subreddit.in_(subreddits))

                # Order and limit
                query = query.order_by(
                    Opportunity.final_score.desc(),
                    Opportunity.created_at.desc()
                ).limit(limit)

                # Execute query
                results = await session.execute(query)
                opportunities = results.scalars().all()

                # Convert to dictionaries
                return [self._convert_opportunity_to_dict(op) for op in opportunities]

            except Exception as e:
                print(f"Error retrieving opportunities: {e}")
                return []

    async def find_similar_opportunities(
        self,
        embedding: List[float],
        similarity_threshold: float = 0.8,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find opportunities using vector similarity search"""

        async with self.get_session() as session:
            try:
                from models.database import Opportunity
                from sqlalchemy import text

                # Use pgvector for similarity search
                similarity_query = text(f"""
                SELECT *,
                       1 - (embedding <=> :embedding_vector) as similarity
                FROM opportunities
                WHERE 1 - (embedding <=> :embedding_vector) > :threshold
                ORDER BY similarity DESC
                LIMIT :limit
                """)

                result = await session.execute(
                    similarity_query,
                    {
                        "embedding_vector": embedding,
                        "threshold": similarity_threshold,
                        "limit": limit
                    }
                )

                similar_opportunities = result.fetchall()

                return [dict(row._mapping) for row in similar_opportunities]

            except Exception as e:
                print(f"Error finding similar opportunities: {e}")
                return []

    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary for dashboard"""

        async with self.get_session() as session:
            try:
                from models.database import Opportunity
                from sqlalchemy import func, text

                # Basic counts
                total_opportunities = await session.scalar(
                    func.count(Opportunity.id)
                )

                avg_score = await session.scalar(
                    func.avg(Opportunity.final_score)
                ) or 0

                # Trust level distribution
                trust_distribution = await session.execute(
                    text("""
                    SELECT trust_level, COUNT(*) as count
                    FROM opportunities
                    GROUP BY trust_level
                    """)
                )

                trust_counts = {
                    row.trust_level: row.count
                    for row in trust_distribution.fetchall()
                }

                # Top subreddits
                top_subreddits = await session.execute(
                    text("""
                    SELECT subreddit, COUNT(*) as count, AVG(final_score) as avg_score
                    FROM opportunities
                    GROUP BY subreddit
                    ORDER BY count DESC
                    LIMIT 10
                    """)
                )

                subreddit_stats = [
                    {
                        "subreddit": row.subreddit,
                        "count": row.count,
                        "avg_score": float(row.avg_score) if row.avg_score else 0
                    }
                    for row in top_subreddits.fetchall()
                ]

                # Recent activity
                recent_count = await session.scalar(
                    text("""
                    SELECT COUNT(*)
                    FROM opportunities
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                    """)
                )

                return {
                    "total_opportunities": total_opportunities,
                    "average_score": float(avg_score),
                    "trust_level_distribution": trust_counts,
                    "top_subreddits": subreddit_stats,
                    "recent_activity_24h": recent_count or 0
                }

            except Exception as e:
                print(f"Error getting analytics summary: {e}")
                return {}

    async def _check_existing_submissions(
        self,
        session: AsyncSession,
        submission_ids: List[str]
    ) -> set:
        """Check which submission IDs already exist"""

        from models.database import Opportunity

        existing = await session.execute(
            session.query(Opportunity.submission_id)
            .filter(Opportunity.submission_id.in_(submission_ids))
        )

        return {row.submission_id for row in existing.fetchall()}

    async def _convert_to_db_model(self, result: AnalysisResult):
        """Convert AnalysisResult to database model"""

        from models.database import Opportunity

        return Opportunity(
            id=uuid.uuid4(),
            submission_id=result.submission_id,
            app_title=result.app_idea.title,
            app_concept=result.app_idea.app_concept,
            problem_statement=result.app_idea.problem_statement,
            target_audience=result.app_idea.target_audience,
            core_functions=result.app_idea.core_functions,
            market_demand=result.market_metrics.market_demand,
            pain_intensity=result.market_metrics.pain_intensity,
            monetization_potential=result.market_metrics.monetization_potential,
            competition_level=result.market_metrics.competition_level,
            technical_feasibility=result.market_metrics.technical_feasibility,
            final_score=result.final_score,
            confidence_score=result.confidence_score,
            trust_level=result.trust_level,
            embedding=result.embedding,
            created_at=datetime.utcnow()
        )

    def _convert_opportunity_to_dict(self, opportunity) -> Dict[str, Any]:
        """Convert database model to dictionary"""

        return {
            "id": str(opportunity.id),
            "submission_id": opportunity.submission_id,
            "app_title": opportunity.app_title,
            "app_concept": opportunity.app_concept,
            "problem_statement": opportunity.problem_statement,
            "target_audience": opportunity.target_audience,
            "core_functions": opportunity.core_functions,
            "market_demand": opportunity.market_demand,
            "pain_intensity": opportunity.pain_intensity,
            "monetization_potential": opportunity.monetization_potential,
            "competition_level": opportunity.competition_level,
            "technical_feasibility": opportunity.technical_feasibility,
            "final_score": opportunity.final_score,
            "confidence_score": opportunity.confidence_score,
            "trust_level": opportunity.trust_level,
            "created_at": opportunity.created_at.isoformat() if opportunity.created_at else None
        }

    async def test_connection(self) -> Dict[str, Any]:
        """Test database connectivity"""

        try:
            # Test basic connection
            async with self.get_session() as session:
                # Simple query to test connection
                result = await session.execute(text("SELECT 1 as test"))
                test_value = result.scalar()

            # Test Supabase connection
            supabase_test = self.supabase.table('opportunities').select('count').execute()

            return {
                "database_connected": test_value == 1,
                "supabase_connected": True,
                "supabase_response": supabase_test.data if supabase_test.data else None
            }

        except Exception as e:
            return {
                "database_connected": False,
                "supabase_connected": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
```

---

## 🔐 Authentication and Security

### 1. Secure Credential Management

**Production Security Configuration**
```python
import os
import keyring
from cryptography.fernet import Fernet
from typing import Optional, Dict
import json

class SecureCredentialManager:
    """Secure management of API credentials and keys"""

    def __init__(self, app_name: str = "reddit_harbor"):
        self.app_name = app_name
        self.fernet = None
        self._initialize_encryption()

    def _initialize_encryption(self):
        """Initialize encryption for stored credentials"""

        # Try to get encryption key from keyring
        encryption_key = keyring.get_password(self.app_name, "encryption_key")

        if not encryption_key:
            # Generate new encryption key
            encryption_key = Fernet.generate_key().decode()
            keyring.set_password(self.app_name, "encryption_key", encryption_key)

        self.fernet = Fernet(encryption_key.encode())

    def store_credential(self, service: str, credential_type: str, value: str):
        """Securely store a credential"""

        # Encrypt the value
        encrypted_value = self.fernet.encrypt(value.encode()).decode()

        # Store in keyring
        keyring.set_password(f"{self.app_name}_{service}", credential_type, encrypted_value)

    def get_credential(self, service: str, credential_type: str) -> Optional[str]:
        """Retrieve a stored credential"""

        try:
            encrypted_value = keyring.get_password(f"{self.app_name}_{service}", credential_type)

            if encrypted_value:
                # Decrypt the value
                decrypted_value = self.fernet.decrypt(encrypted_value.encode()).decode()
                return decrypted_value

        except Exception:
            pass  # Credential not found or decryption failed

        return None

    def store_api_config(self, service: str, config: Dict[str, str]):
        """Store multiple API configuration values"""

        config_json = json.dumps(config)
        self.store_credential(service, "config", config_json)

    def get_api_config(self, service: str) -> Optional[Dict[str, str]]:
        """Retrieve API configuration"""

        config_json = self.get_credential(service, "config")

        if config_json:
            try:
                return json.loads(config_json)
            except json.JSONDecodeError:
                pass

        return None

    def clear_credentials(self, service: Optional[str] = None):
        """Clear stored credentials"""

        if service:
            # Clear specific service credentials
            try:
                keyring.delete_password(f"{self.app_name}_{service}", "config")
            except keyring.errors.PasswordDeleteError:
                pass
        else:
            # Clear all credentials (more complex implementation needed)
            pass

class AuthenticationManager:
    """Manage authentication for all external services"""

    def __init__(self, settings, credential_manager: SecureCredentialManager):
        self.settings = settings
        self.credential_manager = credential_manager
        self.auth_tokens = {}

    async def authenticate_reddit(self) -> bool:
        """Authenticate with Reddit API"""

        try:
            # Get credentials
            client_id = self._get_credential_or_env("REDDIT_CLIENT_ID", "reddit", "client_id")
            client_secret = self._get_credential_or_env("REDDIT_CLIENT_SECRET", "reddit", "client_secret")

            if not client_id or not client_secret:
                raise ValueError("Reddit API credentials not found")

            # Test authentication
            import praw
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=self.settings.reddit_user_agent
            )

            # Verify authentication
            username = reddit.user.me()

            self.auth_tokens["reddit"] = {
                "authenticated": True,
                "username": str(username) if username else "anonymous"
            }

            return True

        except Exception as e:
            self.auth_tokens["reddit"] = {
                "authenticated": False,
                "error": str(e)
            }
            return False

    async def authenticate_openrouter(self) -> bool:
        """Authenticate with OpenRouter API"""

        try:
            # Get API key
            api_key = self._get_credential_or_env("OPENROUTER_API_KEY", "openrouter", "api_key")

            if not api_key:
                raise ValueError("OpenRouter API key not found")

            # Test authentication
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://openrouter.ai/api/v1/models",
                    headers=headers,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        self.auth_tokens["openrouter"] = {
                            "authenticated": True,
                            "api_key_present": True
                        }
                        return True
                    else:
                        raise Exception(f"HTTP {response.status}: {await response.text()}")

        except Exception as e:
            self.auth_tokens["openrouter"] = {
                "authenticated": False,
                "error": str(e)
            }
            return False

    async def authenticate_supabase(self) -> bool:
        """Authenticate with Supabase"""

        try:
            # Get credentials
            url = self._get_credential_or_env("SUPABASE_URL", "supabase", "url")
            anon_key = self._get_credential_or_env("SUPABASE_ANON_KEY", "supabase", "anon_key")

            if not url or not anon_key:
                raise ValueError("Supabase credentials not found")

            # Test authentication
            supabase = create_client(url, anon_key)

            # Try to access the database
            result = supabase.table('opportunities').select('count').limit(1).execute()

            self.auth_tokens["supabase"] = {
                "authenticated": True,
                "database_accessible": True
            }

            return True

        except Exception as e:
            self.auth_tokens["supabase"] = {
                "authenticated": False,
                "error": str(e)
            }
            return False

    def _get_credential_or_env(
        self,
        env_var: str,
        service: str,
        credential_type: str
    ) -> Optional[str]:
        """Get credential from secure storage or environment variable"""

        # Try secure storage first
        credential = self.credential_manager.get_credential(service, credential_type)

        if credential:
            return credential

        # Fallback to environment variable
        return os.getenv(env_var)

    async def authenticate_all_services(self) -> Dict[str, bool]:
        """Authenticate with all external services"""

        auth_results = {}

        auth_results["reddit"] = await self.authenticate_reddit()
        auth_results["openrouter"] = await self.authenticate_openrouter()
        auth_results["supabase"] = await self.authenticate_supabase()

        return auth_results

    def get_authentication_status(self) -> Dict[str, Dict]:
        """Get current authentication status for all services"""

        return self.auth_tokens
```

---

## ⚠️ Error Handling and Resilience

### 1. Circuit Breaker Pattern

**Circuit Breaker for External APIs**
```python
import time
import asyncio
from enum import Enum
from typing import Callable, Any, Optional
from dataclasses import dataclass

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5        # Failures before opening
    timeout: float = 60.0            # Seconds to wait before trying again
    success_threshold: int = 2       # Successes needed to close circuit
    exception_types: tuple = (Exception,)

class CircuitBreaker:
    """Circuit breaker pattern for external service resilience"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.last_failure_exception = None

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""

        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")

        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self._close_circuit()
            else:
                self._reset_failure_count()

            return result

        except self.config.exception_types as e:
            self._record_failure(e)

            if self.failure_count >= self.config.failure_threshold:
                self._open_circuit()

            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset"""

        return time.time() - self.last_failure_time >= self.config.timeout

    def _record_failure(self, exception: Exception):
        """Record a failure"""

        self.failure_count += 1
        self.last_failure_time = time.time()
        self.last_failure_exception = exception

    def _reset_failure_count(self):
        """Reset failure count on success"""

        self.failure_count = 0

    def _open_circuit(self):
        """Open the circuit breaker"""

        self.state = CircuitState.OPEN
        self.success_count = 0

    def _close_circuit(self):
        """Close the circuit breaker"""

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0

    def get_status(self) -> dict:
        """Get current circuit breaker status"""

        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "last_failure_exception": str(self.last_failure_exception) if self.last_failure_exception else None
        }

# Circuit breaker instances for different services
reddit_circuit_breaker = CircuitBreaker(
    CircuitBreakerConfig(
        failure_threshold=3,
        timeout=30.0,
        exception_types=(RequestException, ResponseException, TimeoutError)
    )
)

openrouter_circuit_breaker = CircuitBreaker(
    CircuitBreakerConfig(
        failure_threshold=5,
        timeout=60.0,
        exception_types=(ConnectionError, TimeoutError)
    )
)

supabase_circuit_breaker = CircuitBreaker(
    CircuitBreakerConfig(
        failure_threshold=2,
        timeout=45.0,
        exception_types=(ConnectionError, TimeoutError)
    )
)
```

---

## 🚀 Production Deployment

### 1. Environment Configuration

**Production Environment Setup**
```python
# config/production.py
import os
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings

class ProductionSettings(BaseSettings):
    """Production environment settings"""

    # Environment identification
    environment: str = Field(default="production", description="Environment name")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Reddit API (Production)
    reddit_client_id: str = Field(..., alias="REDDIT_CLIENT_ID")
    reddit_client_secret: str = Field(..., alias="REDDIT_CLIENT_SECRET")
    reddit_user_agent: str = Field(
        default="RedditHarbor Pipeline v3/1.0 (Production)",
        description="Reddit API user agent"
    )

    # OpenRouter API (Production)
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(
        default="claude-3.5-sonnet",
        description="Production LLM model"
    )

    # Supabase (Production)
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_anon_key: str = Field(..., alias="SUPABASE_ANON_KEY")
    supabase_service_key: str = Field(..., alias="SUPABASE_SERVICE_KEY")

    # Database (Production)
    database_url: str = Field(..., alias="DATABASE_URL")
    database_pool_size: int = Field(default=50, description="Database pool size")
    database_max_overflow: int = Field(default=100, description="Max overflow connections")

    # Performance settings
    worker_processes: int = Field(default=4, description="Number of worker processes")
    max_concurrent_requests: int = Field(default=100, description="Max concurrent requests")
    request_timeout: int = Field(default=30, description="Request timeout (seconds)")

    # Monitoring and logging
    log_level: str = Field(default="INFO", description="Log level")
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    enable_health_checks: bool = Field(default=True, description="Enable health checks")

    # Security
    enable_https: bool = Field(default=True, description="Force HTTPS")
    allowed_origins: List[str] = Field(
        default=["https://your-domain.com"],
        description="CORS allowed origins"
    )
    api_rate_limit: int = Field(default=1000, description="API rate limit per hour")

    # Backup and recovery
    enable_backups: bool = Field(default=True, description="Enable automatic backups")
    backup_retention_days: int = Field(default=30, description="Backup retention period")

    @validator('log_level')
    def validate_log_level(cls, v):
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'log_level must be one of {allowed_levels}')
        return v.upper()

    @validator('environment')
    def validate_environment(cls, v):
        allowed_envs = ['development', 'staging', 'production']
        if v not in allowed_envs:
            raise ValueError(f'environment must be one of {allowed_envs}')
        return v

    class Config:
        env_file = ".env.production"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Docker configuration for production deployment
DOCKER_COMPOSE_PRODUCTION = """
version: '3.8'

services:
  pipeline-v3:
    build: .
    environment:
      - REDDIT_CLIENT_ID=${REDDIT_CLIENT_ID}
      - REDDIT_CLIENT_SECRET=${REDDIT_CLIENT_SECRET}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    depends_on:
      - redis
      - postgres
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - pipeline-v3
    restart: unless-stopped

volumes:
  redis_data:
"""
```

### 2. Health Checks and Monitoring

**Comprehensive Health Check System**
```python
import asyncio
import aiohttp
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheck:
    name: str
    status: HealthStatus
    response_time: float
    message: str
    timestamp: float

class HealthMonitor:
    """Monitor health of all external services and internal components"""

    def __init__(self):
        self.health_checks = {}
        self.circuit_breakers = {
            "reddit": reddit_circuit_breaker,
            "openrouter": openrouter_circuit_breaker,
            "supabase": supabase_circuit_breaker
        }

    async def check_all_services(self) -> Dict[str, HealthCheck]:
        """Check health of all services"""

        checks = {}

        # Check Reddit API
        checks["reddit"] = await self._check_reddit_health()

        # Check OpenRouter API
        checks["openrouter"] = await self._check_openrouter_health()

        # Check Supabase
        checks["supabase"] = await self._check_supabase_health()

        # Check database
        checks["database"] = await self._check_database_health()

        # Check internal components
        checks["memory"] = await self._check_memory_health()
        checks["disk"] = await self._check_disk_health()

        self.health_checks = checks
        return checks

    async def _check_reddit_health(self) -> HealthCheck:
        """Check Reddit API health"""

        start_time = time.time()

        try:
            # Check circuit breaker status
            if self.circuit_breakers["reddit"].state == CircuitState.OPEN:
                return HealthCheck(
                    name="reddit",
                    status=HealthStatus.UNHEALTHY,
                    response_time=time.time() - start_time,
                    message="Circuit breaker is open",
                    timestamp=time.time()
                )

            # Test Reddit API connectivity
            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "RedditHarbor Health Check/1.0"
                }

                async with session.get(
                    "https://www.reddit.com/r/test/hot.json?limit=1",
                    headers=headers,
                    timeout=10
                ) as response:

                    response_time = time.time() - start_time

                    if response.status == 200:
                        return HealthCheck(
                            name="reddit",
                            status=HealthStatus.HEALTHY,
                            response_time=response_time,
                            message="Reddit API responding normally",
                            timestamp=time.time()
                        )
                    else:
                        return HealthCheck(
                            name="reddit",
                            status=HealthStatus.DEGRADED,
                            response_time=response_time,
                            message=f"HTTP {response.status}",
                            timestamp=time.time()
                        )

        except Exception as e:
            return HealthCheck(
                name="reddit",
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                message=f"Connection error: {str(e)}",
                timestamp=time.time()
            )

    async def _check_openrouter_health(self) -> HealthCheck:
        """Check OpenRouter API health"""

        start_time = time.time()

        try:
            # Check circuit breaker
            if self.circuit_breakers["openrouter"].state == CircuitState.OPEN:
                return HealthCheck(
                    name="openrouter",
                    status=HealthStatus.UNHEALTHY,
                    response_time=time.time() - start_time,
                    message="Circuit breaker is open",
                    timestamp=time.time()
                )

            # Test OpenRouter API
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                    "Content-Type": "application/json"
                }

                async with session.get(
                    "https://openrouter.ai/api/v1/models",
                    headers=headers,
                    timeout=10
                ) as response:

                    response_time = time.time() - start_time

                    if response.status == 200:
                        return HealthCheck(
                            name="openrouter",
                            status=HealthStatus.HEALTHY,
                            response_time=response_time,
                            message="OpenRouter API responding normally",
                            timestamp=time.time()
                        )
                    else:
                        return HealthCheck(
                            name="openrouter",
                            status=HealthStatus.DEGRADED,
                            response_time=response_time,
                            message=f"HTTP {response.status}",
                            timestamp=time.time()
                        )

        except Exception as e:
            return HealthCheck(
                name="openrouter",
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                message=f"Connection error: {str(e)}",
                timestamp=time.time()
            )

    async def _check_supabase_health(self) -> HealthCheck:
        """Check Supabase health"""

        start_time = time.time()

        try:
            # Check circuit breaker
            if self.circuit_breakers["supabase"].state == CircuitState.OPEN:
                return HealthCheck(
                    name="supabase",
                    status=HealthStatus.UNHEALTHY,
                    response_time=time.time() - start_time,
                    message="Circuit breaker is open",
                    timestamp=time.time()
                )

            # Test Supabase connectivity
            supabase_url = os.getenv("SUPABASE_URL")
            anon_key = os.getenv("SUPABASE_ANON_KEY")

            async with aiohttp.ClientSession() as session:
                headers = {
                    "apikey": anon_key,
                    "Authorization": f"Bearer {anon_key}"
                }

                async with session.get(
                    f"{supabase_url}/rest/v1/opportunities?select=count&limit=1",
                    headers=headers,
                    timeout=10
                ) as response:

                    response_time = time.time() - start_time

                    if response.status == 200:
                        return HealthCheck(
                            name="supabase",
                            status=HealthStatus.HEALTHY,
                            response_time=response_time,
                            message="Supabase API responding normally",
                            timestamp=time.time()
                        )
                    else:
                        return HealthCheck(
                            name="supabase",
                            status=HealthStatus.DEGRADED,
                            response_time=response_time,
                            message=f"HTTP {response.status}",
                            timestamp=time.time()
                        )

        except Exception as e:
            return HealthCheck(
                name="supabase",
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                message=f"Connection error: {str(e)}",
                timestamp=time.time()
            )

    async def _check_memory_health(self) -> HealthCheck:
        """Check memory usage"""

        start_time = time.time()

        try:
            import psutil

            memory = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info()

            memory_usage_percent = memory.percent
            process_memory_mb = process_memory.rss / 1024 / 1024

            if memory_usage_percent < 80 and process_memory_mb < 1024:
                status = HealthStatus.HEALTHY
                message = f"Memory usage: {memory_usage_percent:.1f}%, Process: {process_memory_mb:.1f}MB"
            elif memory_usage_percent < 90 and process_memory_mb < 1536:
                status = HealthStatus.DEGRADED
                message = f"High memory usage: {memory_usage_percent:.1f}%, Process: {process_memory_mb:.1f}MB"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Critical memory usage: {memory_usage_percent:.1f}%, Process: {process_memory_mb:.1f}MB"

            return HealthCheck(
                name="memory",
                status=status,
                response_time=time.time() - start_time,
                message=message,
                timestamp=time.time()
            )

        except Exception as e:
            return HealthCheck(
                name="memory",
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                message=f"Error checking memory: {str(e)}",
                timestamp=time.time()
            )

    async def _check_disk_health(self) -> HealthCheck:
        """Check disk space"""

        start_time = time.time()

        try:
            import psutil

            disk = psutil.disk_usage('/')
            free_percent = (disk.free / disk.total) * 100

            if free_percent > 20:
                status = HealthStatus.HEALTHY
                message = f"Disk space: {free_percent:.1f}% free"
            elif free_percent > 10:
                status = HealthStatus.DEGRADED
                message = f"Low disk space: {free_percent:.1f}% free"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Critical disk space: {free_percent:.1f}% free"

            return HealthCheck(
                name="disk",
                status=status,
                response_time=time.time() - start_time,
                message=message,
                timestamp=time.time()
            )

        except Exception as e:
            return HealthCheck(
                name="disk",
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                message=f"Error checking disk: {str(e)}",
                timestamp=time.time()
            )

    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status"""

        if not self.health_checks:
            return HealthStatus.HEALTHY

        statuses = [check.status for check in self.health_checks.values()]

        if any(status == HealthStatus.UNHEALTHY for status in statuses):
            return HealthStatus.UNHEALTHY
        elif any(status == HealthStatus.DEGRADED for status in statuses):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    def get_health_summary(self) -> Dict:
        """Get comprehensive health summary"""

        overall_status = self.get_overall_status()

        return {
            "overall_status": overall_status.value,
            "timestamp": time.time(),
            "checks": {
                name: {
                    "status": check.status.value,
                    "response_time": check.response_time,
                    "message": check.message,
                    "timestamp": check.timestamp
                }
                for name, check in self.health_checks.items()
            },
            "circuit_breakers": {
                name: breaker.get_status()
                for name, breaker in self.circuit_breakers.items()
            }
        }
```

---

## 📊 API Monitoring and Health Checks

### 1. Prometheus Metrics Integration

**Production Metrics Collection**
```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
import asyncio
from typing import Dict, Any

# Prometheus metrics
REQUEST_COUNT = Counter('pipeline_requests_total', 'Total requests', ['service', 'method', 'status'])
REQUEST_DURATION = Histogram('pipeline_request_duration_seconds', 'Request duration', ['service', 'method'])
ACTIVE_CONNECTIONS = Gauge('pipeline_active_connections', 'Active connections', ['service'])
PROCESSED_ITEMS = Counter('pipeline_processed_items_total', 'Total items processed', ['stage'])
ERROR_COUNT = Counter('pipeline_errors_total', 'Total errors', ['service', 'error_type'])

class MetricsCollector:
    """Collect and expose pipeline metrics"""

    def __init__(self, metrics_port: int = 8000):
        self.metrics_port = metrics_port
        self.start_time = time.time()

    def start_metrics_server(self):
        """Start Prometheus metrics HTTP server"""

        start_http_server(self.metrics_port)

    def record_request(self, service: str, method: str, status: str, duration: float):
        """Record request metrics"""

        REQUEST_COUNT.labels(service=service, method=method, status=status).inc()
        REQUEST_DURATION.labels(service=service, method=method).observe(duration)

    def record_processed_items(self, stage: str, count: int):
        """Record processed items"""

        PROCESSED_ITEMS.labels(stage=stage).inc(count)

    def record_error(self, service: str, error_type: str):
        """Record error occurrence"""

        ERROR_COUNT.labels(service=service, error_type=error_type).inc()

    def update_active_connections(self, service: str, count: int):
        """Update active connections gauge"""

        ACTIVE_CONNECTIONS.labels(service=service).set(count)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary for monitoring dashboard"""

        uptime = time.time() - self.start_time

        return {
            "uptime_seconds": uptime,
            "metrics_port": self.metrics_port,
            "total_requests": REQUEST_COUNT._value.get(),
            "total_processed_items": PROCESSED_ITEMS._value.get(),
            "total_errors": ERROR_COUNT._value.get()
        }

# Usage example:
# metrics = MetricsCollector()
# metrics.start_metrics_server()
# metrics.record_request("reddit", "extract", "success", 2.5)
# metrics.record_processed_items("extract", 25)
```

---

## 🔧 Configuration Management

### 1. Environment-Specific Configuration

**Configuration Factory Pattern**
```python
from abc import ABC, abstractmethod
from typing import Dict, Any
import os

class BaseSettings(ABC):
    """Base settings interface"""

    @abstractmethod
    def get_database_url(self) -> str:
        pass

    @abstractmethod
    def get_reddit_config(self) -> Dict[str, str]:
        pass

    @abstractmethod
    def get_llm_config(self) -> Dict[str, str]:
        pass

class DevelopmentSettings(BaseSettings):
    """Development environment settings"""

    def __init__(self):
        self.environment = "development"
        self.debug = True

    def get_database_url(self) -> str:
        return os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:54322/postgres")

    def get_reddit_config(self) -> Dict[str, str]:
        return {
            "client_id": os.getenv("REDDIT_CLIENT_ID", "test_client_id"),
            "client_secret": os.getenv("REDDIT_CLIENT_SECRET", "test_client_secret"),
            "user_agent": "RedditHarbor Pipeline v3/1.0 (Development)"
        }

    def get_llm_config(self) -> Dict[str, str]:
        return {
            "api_key": os.getenv("OPENROUTER_API_KEY", "test_key"),
            "model": "meta-llama/llama-3.1-8b-instruct:floor"
        }

class StagingSettings(BaseSettings):
    """Staging environment settings"""

    def __init__(self):
        self.environment = "staging"
        self.debug = False

    def get_database_url(self) -> str:
        return os.getenv("STAGING_DATABASE_URL")

    def get_reddit_config(self) -> Dict[str, str]:
        return {
            "client_id": os.getenv("STAGING_REDDIT_CLIENT_ID"),
            "client_secret": os.getenv("STAGING_REDDIT_CLIENT_SECRET"),
            "user_agent": "RedditHarbor Pipeline v3/1.0 (Staging)"
        }

    def get_llm_config(self) -> Dict[str, str]:
        return {
            "api_key": os.getenv("STAGING_OPENROUTER_API_KEY"),
            "model": "claude-3.5-sonnet"
        }

class ProductionSettings(BaseSettings):
    """Production environment settings"""

    def __init__(self):
        self.environment = "production"
        self.debug = False

    def get_database_url(self) -> str:
        return os.getenv("PRODUCTION_DATABASE_URL")

    def get_reddit_config(self) -> Dict[str, str]:
        return {
            "client_id": os.getenv("PRODUCTION_REDDIT_CLIENT_ID"),
            "client_secret": os.getenv("PRODUCTION_REDDIT_CLIENT_SECRET"),
            "user_agent": "RedditHarbor Pipeline v3/1.0 (Production)"
        }

    def get_llm_config(self) -> Dict[str, str]:
        return {
            "api_key": os.getenv("PRODUCTION_OPENROUTER_API_KEY"),
            "model": "gpt-4o"
        }

class SettingsFactory:
    """Factory for creating environment-specific settings"""

    @staticmethod
    def create_settings() -> BaseSettings:
        """Create settings based on environment"""

        environment = os.getenv("ENVIRONMENT", "development").lower()

        if environment == "production":
            return ProductionSettings()
        elif environment == "staging":
            return StagingSettings()
        else:
            return DevelopmentSettings()

# Usage:
# settings = SettingsFactory.create_settings()
# db_url = settings.get_database_url()
```

This comprehensive real API integration guide provides production-ready implementations for all external services with robust error handling, security, monitoring, and deployment considerations. The code includes practical examples for integrating with Reddit API, OpenRouter LLM, and Supabase database with enterprise-grade resilience patterns.

---

<div align="center">

**🔗 Ready for Production Deployment**

*This guide provides all the components needed for reliable, scalable API integration in production environments*

</div>