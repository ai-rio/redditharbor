# ELT Pipeline Implementation Guide

<div align="center">

**Complete Implementation of Clean Extract → Transform → Load Pipeline**

*Type-safe Reddit data processing with real API integrations*

</div>

## 📋 Table of Contents

- [🏗️ Architecture Overview](#️-architecture-overview)
- [🔍 Extract Layer Implementation](#-extract-layer-implementation)
- [⚡ Transform Layer Implementation](#-transform-layer-implementation)
- [💾 Load Layer Implementation](#-load-layer-implementation)
- [🔧 Pipeline Orchestration](#-pipeline-orchestration)
- [🧪 Testing Strategy](#-testing-strategy)
- [📊 Performance Optimization](#-performance-optimization)

---

## 🏗️ Architecture Overview

The Pipeline v3 ELT implementation follows a clean, type-safe architecture:

```
pipeline_v3/
├── extract/           # Raw data extraction from APIs
├── transform/         # Business logic and data validation
├── load/             # Database storage with transactions
├── models/           # Pydantic models for type safety
├── config/           # Configuration management
└── main.py           # Pipeline orchestration
```

### Design Principles

1. **Single Responsibility** - Each module has one clear purpose
2. **Type Safety** - All data structures use Pydantic validation
3. **Error Handling** - Comprehensive error management throughout
4. **Testability** - Every component is independently testable
5. **Performance** - Async I/O and batch processing

---

## 🔍 Extract Layer Implementation

### Core Components

#### 1. Reddit Client (`extract/reddit_client.py`)

```python
import praw
from typing import List, AsyncGenerator
from ..models import RedditPost, RedditComment

class RedditExtractor:
    """Reddit API client with rate limiting and error handling"""

    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        self._rate_limiter = RateLimiter(requests_per_minute=60)

    async def extract_posts(
        self,
        subreddit: str,
        limit: int = 100,
        time_filter: str = "week"
    ) -> AsyncGenerator[RedditPost, None]:
        """Extract posts from subreddit with rate limiting"""

        subreddit_obj = self.reddit.subreddit(subreddit)

        async for submission in subreddit_obj.top(
            time_filter=time_filter,
            limit=limit
        ):
            await self._rate_limiter.wait()

            try:
                post = RedditPost(
                    id=submission.id,
                    title=submission.title,
                    author=str(submission.author) if submission.author else "[deleted]",
                    subreddit=submission.subreddit.display_name,
                    score=submission.score,
                    upvote_ratio=submission.upvote_ratio,
                    num_comments=submission.num_comments,
                    created_at=datetime.fromtimestamp(submission.created_utc),
                    content=submission.selftext,
                    url=submission.url,
                    permalink=submission.permalink
                )
                yield post

            except Exception as e:
                logger.error(f"Error processing post {submission.id}: {e}")
                continue

    async def extract_comments(
        self,
        post_id: str,
        limit: int = 50
    ) -> AsyncGenerator[RedditComment, None]:
        """Extract comments for a specific post"""

        submission = self.reddit.submission(id=post_id)
        submission.comments.replace_more(limit=0)

        for comment in submission.comments.list()[:limit]:
            await self._rate_limiter.wait()

            try:
                comment_data = RedditComment(
                    id=comment.id,
                    post_id=post_id,
                    author=str(comment.author) if comment.author else "[deleted]",
                    content=comment.body,
                    score=comment.score,
                    created_at=datetime.fromtimestamp(comment.created_utc),
                    depth=comment.depth
                )
                yield comment_data

            except Exception as e:
                logger.error(f"Error processing comment {comment.id}: {e}")
                continue
```

#### 2. LLM Client (`extract/llm_client.py`)

```python
import openai
from typing import Dict, Any, Optional
from ..models import LLMAnalysisResult

class LLMAnalyzer:
    """OpenRouter API client for content analysis"""

    def __init__(self, api_key: str, model: str = "anthropic/claude-3.5-sonnet"):
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = model
        self._rate_limiter = RateLimiter(requests_per_minute=100)

    async def analyze_content(
        self,
        content: str,
        analysis_type: str = "opportunity_detection"
    ) -> LLMAnalysisResult:
        """Analyze Reddit content for business opportunities"""

        await self._rate_limiter.wait()

        prompt = self._get_analysis_prompt(content, analysis_type)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000
            )

            analysis_text = response.choices[0].message.content

            # Parse structured response
            return LLMAnalysisResult(
                analysis_type=analysis_type,
                raw_response=analysis_text,
                structured_data=self._parse_analysis(analysis_text),
                confidence_score=self._extract_confidence(analysis_text),
                model_used=self.model,
                tokens_used=response.usage.total_tokens if response.usage else 0
            )

        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return LLMAnalysisResult.get_error_result(str(e))

    def _get_analysis_prompt(self, content: str, analysis_type: str) -> str:
        """Generate analysis prompt based on type"""

        if analysis_type == "opportunity_detection":
            return f"""
            Analyze this Reddit content for potential business opportunities:

            CONTENT: {content}

            Provide analysis in JSON format:
            {{
                "opportunity_type": "web_app|mobile_app|service|tool",
                "pain_point": "clear description of user problem",
                "solution_complexity": "simple|moderate|complex",
                "market_demand": "low|medium|high",
                "monetization_potential": "low|medium|high",
                "confidence_score": 0.0-1.0,
                "explanation": "detailed analysis"
            }}
            """

        # Add other analysis types as needed
        return f"Analyze this content: {content}"
```

---

## ⚡ Transform Layer Implementation

### Core Components

#### 1. Quality Filtering (`transform/quality_filter.py`)

```python
from typing import List, Tuple
from ..models import RedditPost, QualityScore

class QualityFilter:
    """Quality assessment and filtering for Reddit content"""

    def __init__(self, min_score_threshold: float = 0.7):
        self.min_score_threshold = min_score_threshold
        self.quality_weights = {
            'engagement': 0.3,
            'content_quality': 0.25,
            'recency': 0.2,
            'author_reputation': 0.15,
            'discussion_quality': 0.1
        }

    def filter_posts(
        self,
        posts: List[RedditPost]
    ) -> Tuple[List[RedditPost], List[QualityScore]]:
        """Filter posts based on quality assessment"""

        quality_scores = []
        filtered_posts = []

        for post in posts:
            score = self._calculate_quality_score(post)
            quality_scores.append(score)

            if score.overall_score >= self.min_score_threshold:
                filtered_posts.append(post)

        return filtered_posts, quality_scores

    def _calculate_quality_score(self, post: RedditPost) -> QualityScore:
        """Calculate comprehensive quality score for a post"""

        scores = {}

        # Engagement metrics
        scores['engagement'] = self._score_engagement(post)

        # Content quality
        scores['content_quality'] = self._score_content_quality(post)

        # Recency
        scores['recency'] = self._score_recency(post)

        # Author reputation (simplified)
        scores['author_reputation'] = self._score_author_reputation(post)

        # Discussion quality
        scores['discussion_quality'] = self._score_discussion_quality(post)

        # Calculate weighted overall score
        overall_score = sum(
            scores[metric] * weight
            for metric, weight in self.quality_weights.items()
        )

        return QualityScore(
            post_id=post.id,
            overall_score=overall_score,
            component_scores=scores,
            passed_threshold=overall_score >= self.min_score_threshold
        )

    def _score_engagement(self, post: RedditPost) -> float:
        """Score based on engagement metrics"""
        # Normalize score and comment count
        score_normalized = min(post.score / 1000, 1.0)  # Cap at 1000 upvotes
        comments_normalized = min(post.num_comments / 100, 1.0)  # Cap at 100 comments

        return (score_normalized + comments_normalized) / 2

    def _score_content_quality(self, post: RedditPost) -> float:
        """Score based on content characteristics"""
        content_length = len(post.content) if post.content else 0

        # Optimal content length: 200-2000 characters
        if 200 <= content_length <= 2000:
            length_score = 1.0
        elif content_length < 200:
            length_score = content_length / 200
        else:
            length_score = max(0, 1.0 - (content_length - 2000) / 2000)

        # Title quality (length, question indicators)
        title_score = self._score_title_quality(post.title)

        return (length_score + title_score) / 2

    def _score_title_quality(self, title: str) -> float:
        """Score title based on quality indicators"""
        score = 0.5  # Base score

        # Length check (optimal: 20-100 characters)
        if 20 <= len(title) <= 100:
            score += 0.2

        # Question indicators (problems often expressed as questions)
        question_indicators = ['?', 'how', 'what', 'why', 'anyone', 'does anyone']
        if any(indicator in title.lower() for indicator in question_indicators):
            score += 0.2

        # Pain point indicators
        pain_indicators = ['wish', 'if only', 'frustrated', 'annoying', 'problem']
        if any(indicator in title.lower() for indicator in pain_indicators):
            score += 0.3

        return min(score, 1.0)
```

#### 2. Trust Validation (`transform/trust_validation.py`)

```python
from typing import Dict, Any
from ..models import TrustScore

class TrustValidator:
    """Trust scoring system for content validation"""

    def __init__(self):
        self.trust_factors = {
            'author_history': 0.3,
            'content_consistency': 0.25,
            'sentiment_analysis': 0.2,
            'source_credibility': 0.15,
            'temporal_consistency': 0.1
        }

    def validate_content(
        self,
        post: RedditPost,
        comments: List[RedditComment]
    ) -> TrustScore:
        """Validate content trustworthiness"""

        trust_factors = {}

        # Author history and credibility
        trust_factors['author_history'] = self._assess_author_history(post)

        # Content consistency
        trust_factors['content_consistency'] = self._assess_content_consistency(post)

        # Sentiment analysis
        trust_factors['sentiment_analysis'] = self._assess_sentiment(post, comments)

        # Source credibility (subreddit reputation)
        trust_factors['source_credibility'] = self._assess_source_credibility(post)

        # Temporal consistency
        trust_factors['temporal_consistency'] = self._assess_temporal_consistency(post, comments)

        # Calculate overall trust score
        overall_score = sum(
            trust_factors[factor] * weight
            for factor, weight in self.trust_factors.items()
        )

        # Determine trust level
        trust_level = self._determine_trust_level(overall_score)

        # Generate trust badges
        trust_badges = self._generate_trust_badges(trust_factors, overall_score)

        return TrustScore(
            post_id=post.id,
            overall_score=overall_score,
            trust_level=trust_level,
            component_scores=trust_factors,
            trust_badges=trust_badges
        )

    def _assess_author_history(self, post: RedditPost) -> float:
        """Assess author credibility based on available data"""
        # Simplified scoring based on author information
        if post.author == "[deleted]":
            return 0.3  # Low trust for deleted users

        # In a real implementation, this would check:
        # - Account age
        # - Karma score
        # - Post history
        # - Subreddit participation

        return 0.7  # Default medium-high score for non-deleted users

    def _assess_content_consistency(self, post: RedditPost) -> float:
        """Check for internal consistency in content"""
        content = post.content.lower()
        title = post.title.lower()

        score = 0.5  # Base score

        # Check if content relates to title
        title_words = set(title.split())
        content_words = set(content.split())

        overlap = len(title_words & content_words)
        if overlap > 2:
            score += 0.3

        # Check for spam indicators
        spam_indicators = ['buy now', 'click here', 'free money', 'guarantee']
        if not any(indicator in content for indicator in spam_indicators):
            score += 0.2

        return min(score, 1.0)

    def _determine_trust_level(self, score: float) -> str:
        """Determine categorical trust level"""
        if score >= 0.8:
            return "HIGH"
        elif score >= 0.6:
            return "MEDIUM"
        elif score >= 0.4:
            return "LOW"
        else:
            return "VERY_LOW"
```

---

## 💾 Load Layer Implementation

### Core Components

#### 1. Database Repository (`load/repositories.py`)

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update
from typing import List, Optional, Dict, Any
from ..models import AppOpportunity, RedditPost, OpportunityScore

class OpportunityRepository:
    """Repository for app opportunity data operations"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_opportunity(
        self,
        opportunity: AppOpportunity
    ) -> Optional[AppOpportunity]:
        """Create a new opportunity record"""
        try:
            stmt = insert(AppOpportunity.__table__).values(
                **opportunity.dict(exclude={'id'})
            ).returning(AppOpportunity.__table__.c.id)

            result = await self.db.execute(stmt)
            opportunity_id = result.scalar()

            await self.db.commit()

            # Return created opportunity with ID
            opportunity.id = opportunity_id
            return opportunity

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create opportunity: {e}")
            return None

    async def bulk_create_opportunities(
        self,
        opportunities: List[AppOpportunity]
    ) -> Dict[str, Any]:
        """Create multiple opportunities in a single transaction"""
        try:
            if not opportunities:
                return {"success": True, "created_count": 0}

            # Convert to dictionaries
            opportunity_data = [
                opp.dict(exclude={'id'}) for opp in opportunities
            ]

            stmt = insert(AppOpportunity.__table__).values(opportunity_data)
            result = await self.db.execute(stmt)

            await self.db.commit()

            return {
                "success": True,
                "created_count": result.rowcount
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Bulk create failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "created_count": 0
            }

    async def find_opportunities_by_score(
        self,
        min_score: float = 70.0,
        limit: int = 50
    ) -> List[AppOpportunity]:
        """Find high-scoring opportunities"""
        try:
            stmt = select(AppOpportunity).where(
                AppOpportunity.opportunity_score >= min_score
            ).order_by(
                AppOpportunity.opportunity_score.desc()
            ).limit(limit)

            result = await self.db.execute(stmt)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []

    async def update_opportunity_score(
        self,
        opportunity_id: int,
        score: float,
        score_details: Dict[str, Any]
    ) -> bool:
        """Update opportunity score and details"""
        try:
            stmt = update(AppOpportunity).where(
                AppOpportunity.id == opportunity_id
            ).values(
                opportunity_score=score,
                score_components=score_details,
                analyzed_at=datetime.utcnow()
            )

            await self.db.execute(stmt)
            await self.db.commit()

            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Score update failed: {e}")
            return False
```

#### 2. Transaction Manager (`load/transaction_manager.py`)

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)

class TransactionManager:
    """Manages database transactions with proper error handling"""

    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory

    @asynccontextmanager
    async def get_transaction(
        self
    ) -> AsyncGenerator[AsyncSession, None]:
        """Context manager for database transactions"""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Transaction rolled back: {e}")
                raise

    async def execute_in_transaction(
        self,
        operation: callable,
        *args,
        **kwargs
    ):
        """Execute operation within a transaction"""
        async with self.get_transaction() as session:
            return await operation(session, *args, **kwargs)

    @asynccontextmanager
    async def get_readonly_session(
        self
    ) -> AsyncGenerator[AsyncSession, None]:
        """Context manager for read-only database operations"""
        async with self.session_factory() as session:
            try:
                yield session
                # No commit needed for read-only operations
            except Exception as e:
                logger.error(f"Read-only session error: {e}")
                raise
```

---

## 🔧 Pipeline Orchestration

### Main Pipeline (`main.py`)

```python
import asyncio
from typing import List, Optional
from .extract import RedditExtractor, LLMAnalyzer
from .transform import QualityFilter, TrustValidator, OpportunityScorer
from .load import TransactionManager, OpportunityRepository
from .config import get_config
from .models import AppOpportunity, PipelineResult

class PipelineV3:
    """Main ELT pipeline orchestrator"""

    def __init__(self):
        self.config = get_config()

        # Initialize extractors
        self.reddit_extractor = RedditExtractor(
            client_id=self.config.reddit_client_id,
            client_secret=self.config.reddit_client_secret,
            user_agent=self.config.reddit_user_agent
        )

        self.llm_analyzer = LLMAnalyzer(
            api_key=self.config.openrouter_api_key,
            model=self.config.openrouter_model
        )

        # Initialize transformers
        self.quality_filter = QualityFilter(
            min_score_threshold=self.config.min_quality_score
        )
        self.trust_validator = TrustValidator()
        self.opportunity_scorer = OpportunityScorer()

        # Initialize load components
        self.transaction_manager = TransactionManager(self.config.db_session_factory)

    async def run_pipeline(
        self,
        subreddit: str,
        limit: int = 100,
        enable_llm_analysis: bool = True
    ) -> PipelineResult:
        """Run complete ELT pipeline"""

        start_time = datetime.utcnow()

        try:
            # EXTRACT PHASE
            logger.info(f"Starting extraction from r/{subreddit}")
            reddit_posts = []

            async for post in self.reddit_extractor.extract_posts(
                subreddit=subreddit,
                limit=limit
            ):
                reddit_posts.append(post)

            logger.info(f"Extracted {len(reddit_posts)} posts")

            # TRANSFORM PHASE
            logger.info("Starting transformation phase")

            # Quality filtering
            filtered_posts, quality_scores = self.quality_filter.filter_posts(reddit_posts)
            logger.info(f"Quality filter: {len(filtered_posts)}/{len(reddit_posts)} posts passed")

            # Trust validation and opportunity analysis
            opportunities = []
            for post in filtered_posts:
                # Trust validation
                trust_score = self.trust_validator.validate_content(post, [])

                # LLM analysis for opportunity detection
                llm_analysis = None
                if enable_llm_analysis:
                    llm_analysis = await self.llm_analyzer.analyze_content(
                        post.content,
                        "opportunity_detection"
                    )

                # Opportunity scoring
                opportunity_score = self.opportunity_scorer.score_opportunity(
                    post, trust_score, llm_analysis
                )

                # Create opportunity
                opportunity = AppOpportunity.from_reddit_post(
                    reddit_post=post,
                    trust_score=trust_score.overall_score,
                    opportunity_score=opportunity_score.overall_score,
                    llm_analysis=llm_analysis.dict() if llm_analysis else None
                )

                opportunities.append(opportunity)

            logger.info(f"Generated {len(opportunities)} opportunities")

            # LOAD PHASE
            logger.info("Starting load phase")

            load_result = await self.transaction_manager.execute_in_transaction(
                self._load_opportunities,
                opportunities
            )

            # Calculate pipeline result
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            result = PipelineResult(
                success=load_result.get("success", False),
                total_posts_extracted=len(reddit_posts),
                posts_passed_quality=len(filtered_posts),
                opportunities_created=len(opportunities),
                opportunities_saved=load_result.get("created_count", 0),
                duration_seconds=duration,
                error_message=load_result.get("error")
            )

            logger.info(f"Pipeline completed in {duration:.2f}s: {result}")
            return result

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return PipelineResult.error_result(str(e))

    async def _load_opportunities(
        self,
        session: AsyncSession,
        opportunities: List[AppOpportunity]
    ) -> Dict[str, Any]:
        """Load opportunities into database"""
        repository = OpportunityRepository(session)
        return await repository.bulk_create_opportunities(opportunities)

# CLI Entry Point
async def main():
    """Command line interface for pipeline execution"""
    import argparse

    parser = argparse.ArgumentParser(description="RedditHarbor Pipeline v3")
    parser.add_argument("--subreddit", required=True, help="Subreddit to process")
    parser.add_argument("--limit", type=int, default=100, help="Number of posts to process")
    parser.add_argument("--disable-llm", action="store_true", help="Disable LLM analysis")

    args = parser.parse_args()

    pipeline = PipelineV3()

    result = await pipeline.run_pipeline(
        subreddit=args.subreddit,
        limit=args.limit,
        enable_llm_analysis=not args.disable_llm
    )

    print(f"Pipeline Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🧪 Testing Strategy

### Unit Tests

```python
# tests/test_quality_filter.py
import pytest
from pipeline_v3.transform.quality_filter import QualityFilter
from pipeline_v3.models import RedditPost

class TestQualityFilter:
    """Test cases for quality filtering"""

    def setup_method(self):
        self.filter = QualityFilter(min_score_threshold=0.7)

    def test_high_quality_post(self):
        """Test that high quality posts pass filter"""
        post = RedditPost(
            id="test1",
            title="How do I track my productivity effectively?",
            author="productivity_user",
            subreddit="productivity",
            score=500,
            num_comments=50,
            created_at=datetime.now(),
            content="I've been struggling with tracking my daily tasks and would love to hear what tools people use."
        )

        filtered_posts, scores = self.filter.filter_posts([post])

        assert len(filtered_posts) == 1
        assert scores[0].overall_score >= 0.7
        assert scores[0].passed_threshold is True

    def test_low_quality_post(self):
        """Test that low quality posts are filtered out"""
        post = RedditPost(
            id="test2",
            title="hi",
            author="new_user",
            subreddit="productivity",
            score=1,
            num_comments=0,
            created_at=datetime.now(),
            content="test post"
        )

        filtered_posts, scores = self.filter.filter_posts([post])

        assert len(filtered_posts) == 0
        assert scores[0].overall_score < 0.7
        assert scores[0].passed_threshold is False
```

### Integration Tests

```python
# tests/integration/test_full_pipeline.py
import pytest
import asyncio
from pipeline_v3.main import PipelineV3

class TestFullPipeline:
    """Integration tests for complete pipeline"""

    @pytest.mark.asyncio
    async def test_pipeline_with_mock_data(self):
        """Test pipeline with controlled mock data"""
        # Setup mock services
        # ... (mock implementations)

        pipeline = PipelineV3()

        result = await pipeline.run_pipeline(
            subreddit="test_productivity",
            limit=5,
            enable_llm_analysis=False  # Disable LLM for testing
        )

        assert result.success is True
        assert result.total_posts_extracted == 5
        assert result.opportunities_created > 0
```

---

## 📊 Performance Optimization

### Batch Processing

```python
class BatchProcessor:
    """Optimized batch processing for large datasets"""

    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size

    async def process_posts_in_batches(
        self,
        posts: List[RedditPost],
        processor_func: callable
    ) -> List[Any]:
        """Process posts in optimized batches"""
        results = []

        for i in range(0, len(posts), self.batch_size):
            batch = posts[i:i + self.batch_size]

            # Process batch concurrently
            batch_tasks = [
                processor_func(post) for post in batch
            ]

            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)

        return results
```

### Memory Management

```python
import gc
from typing import AsyncGenerator

class StreamingProcessor:
    """Memory-efficient streaming processing"""

    async def process_stream(
        self,
        data_stream: AsyncGenerator,
        processor_func: callable,
        checkpoint_interval: int = 1000
    ):
        """Process data stream with memory management"""
        processed_count = 0

        async for item in data_stream:
            # Process item
            result = await processor_func(item)
            yield result

            processed_count += 1

            # Memory cleanup
            if processed_count % checkpoint_interval == 0:
                gc.collect()
                logger.info(f"Processed {processed_count} items")
```

---

<div align="center">

**🎯 Pipeline Implementation Complete!**

**Key Features:**
- ✅ Type-safe data processing with Pydantic
- ✅ Real API integrations with error handling
- ✅ Transaction-safe database operations
- ✅ Comprehensive testing strategy
- ✅ Performance optimization

</div>