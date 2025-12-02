"""
LLM-powered opportunity analysis using OpenRouter API with Instructor validation
"""

import logging
import os
from datetime import datetime
from typing import List

try:
    import instructor
    INSTRUCTOR_AVAILABLE = True
except ImportError:
    INSTRUCTOR_AVAILABLE = False
    instructor = None

# Conditional OpenAI import with fallback for testing
import sys

# Only import OpenAI if we're not in test environment or if explicitly enabled
if 'pytest' not in sys.modules and not os.environ.get('TEST_NO_OPENAI'):
    try:
        # Apply pydantic v2 compatibility patch before importing OpenAI
        import pydantic
        if hasattr(pydantic, 'v1') and hasattr(pydantic.v1, 'BaseModel'):
            # Pydantic v2+ - patch BaseModel to work with OpenAI
            pydantic.BaseModel = pydantic.v1.BaseModel

        from openai import OpenAI
        OPENAI_AVAILABLE = True
    except ImportError:
        OPENAI_AVAILABLE = False
        OpenAI = None
else:
    OPENAI_AVAILABLE = False
    OpenAI = None
    # Create a mock class for testing
    class MockOpenAI:
        pass
    OpenAI = MockOpenAI

from config import get_settings
from models.reddit import RedditSubmission
from models.analysis import AnalysisResult, AppIdea, MarketMetrics
from .embedding_strategies import EmbeddingStrategy, FakeEmbeddingProvider, OpenAIEmbeddingProvider

logger = logging.getLogger(__name__)


class SimpleOpportunityAnalyzer:
    """
    Simplified analyzer for testing embedding generation without LLM dependencies
    Uses embedding strategy pattern for pluggable embedding providers
    """

    def __init__(self, embedding_strategy: EmbeddingStrategy = None):
        """
        Initialize simple analyzer with embedding strategy

        Args:
            embedding_strategy: Strategy for embedding generation (defaults to fake provider)
        """
        self.settings = None

        # Initialize embedding strategy with default fake provider if none provided
        if embedding_strategy is None:
            fake_provider = FakeEmbeddingProvider(dimensions=384, value_range=(-1.0, 1.0))
            self.embedding_strategy = EmbeddingStrategy(fake_provider)
        else:
            self.embedding_strategy = embedding_strategy

    def analyze_submission(self, submission: RedditSubmission) -> AnalysisResult:
        """
        Analyze a single Reddit submission with embedding generation

        Args:
            submission: Reddit submission to analyze

        Returns:
            AnalysisResult with complete opportunity analysis and embedding
        """
        logger.info(f"Analyzing submission (fake): {submission.id} - {submission.title[:50]}...")

        # Generate fake analysis data with more substantial content
        app_idea = AppIdea(
            title=f"AI-Powered Productivity Solution for {submission.subreddit} Community",
            app_concept=f"A comprehensive application designed to address the specific needs and challenges faced by {submission.subreddit} community members, providing intelligent automation and workflow optimization",
            problem_statement=f"Users in the {submission.subreddit} community frequently struggle with managing their daily tasks and maintaining productivity in an increasingly digital world. The current solutions available in the market are often too generic and fail to address the specific pain points and workflows that are unique to this community's needs and preferences.",
            target_audience=f"Active members of the r/{submission.subreddit} community, including content creators, moderators, and engaged users who are looking for specialized tools to enhance their productivity and streamline their community participation activities.",
            core_functions=["intelligent task automation", "community workflow optimization", " personalized productivity analytics"]
        )

        market_metrics = MarketMetrics(
            market_demand=70.0,
            pain_intensity=75.0,
            monetization_potential=80.0,
            competition_level=65.0,
            technical_feasibility=85.0
        )

        # Generate embedding using the strategy pattern
        text_for_embedding = f"{submission.title} {submission.text} {submission.subreddit}"
        embedding_metadata = {
            'submission_id': submission.id,
            'source': 'reddit_submission_analysis'
        }

        embedding, embedding_metadata = self.embedding_strategy.generate_embedding(
            text_for_embedding,
            embedding_metadata
        )

        # Generate quality scoring based on content analysis
        content_quality_score, is_spam, spam_indicators = self._analyze_content_quality(submission)

        return AnalysisResult(
            submission_id=submission.id,
            analyzed_at=datetime.now(),
            app_idea=app_idea,
            market_metrics=market_metrics,
            final_score=75.0,
            confidence_score=80.0,
            trust_level="HIGH",
            content_quality_score=content_quality_score,
            is_spam=is_spam,
            spam_indicators=spam_indicators,
            embedding=embedding,
            embedding_metadata=embedding_metadata
        )

    def analyze_batch(self, submissions: List[RedditSubmission], batch_size: int = None) -> List[AnalysisResult]:
        """
        Analyze multiple submissions in batches

        Args:
            submissions: List of submissions to analyze
            batch_size: Size of each processing batch

        Returns:
            List of AnalysisResult objects
        """
        logger.info(f"Analyzing {len(submissions)} submissions (fake)")

        results = []
        for submission in submissions:
            try:
                analysis = self.analyze_submission(submission)
                results.append(analysis)
            except Exception as e:
                logger.error(f"Failed to analyze submission {submission.id}: {e}")
                continue

        logger.info(f"✓ Fake batch analysis complete: {len(results)} successful")
        return results

    
    def test_connection(self) -> bool:
        """Test connection using embedding strategy"""
        strategy_test = self.embedding_strategy.test_strategy()
        if strategy_test:
            logger.info("✓ Fake analyzer connection test successful")
        else:
            logger.warning("Fake analyzer connection test failed")
        return strategy_test

    def _analyze_content_quality(self, submission: RedditSubmission) -> tuple[float, bool, List[str]]:
        """
        Analyze content quality and detect spam indicators

        Args:
            submission: Reddit submission to analyze

        Returns:
            Tuple of (content_quality_score, is_spam, spam_indicators)
        """
        spam_indicators = []
        quality_score = 85.0  # Start with high quality score

        text = f"{submission.title} {submission.text}".lower()

        # Check for spam indicators
        if self._has_excessive_caps(submission.title):
            spam_indicators.append("excessive_caps")
            quality_score -= 15

        if self._has_repetitive_content(text):
            spam_indicators.append("repetitive_content")
            quality_score -= 20

        if self._has_suspicious_links(submission):
            spam_indicators.append("suspicious_links")
            quality_score -= 25

        if self._has_spam_keywords(text):
            spam_indicators.append("spam_keywords")
            quality_score -= 20

        # Check content length and substance
        if len(submission.text.strip()) < 50:
            spam_indicators.append("too_short")
            quality_score -= 10
        elif len(submission.text.strip()) > 5000:
            # Very long content might be spam
            spam_indicators.append("excessively_long")
            quality_score -= 15

        # Check for basic grammatical quality (simplified)
        if self._has_poor_grammar(submission.title):
            spam_indicators.append("poor_grammar")
            quality_score -= 10

        # Ensure score stays within bounds
        quality_score = max(0.0, min(100.0, quality_score))

        # Determine if this is spam
        is_spam = quality_score <= 40.0 or len(spam_indicators) >= 3

        return quality_score, is_spam, spam_indicators

    def _has_excessive_caps(self, title: str) -> bool:
        """Check if title has excessive capitalization"""
        if len(title) < 5:
            return False
        caps_count = sum(1 for c in title if c.isupper())
        caps_ratio = caps_count / len(title)
        return caps_ratio > 0.4  # More than 40% caps is excessive

    def _has_repetitive_content(self, text: str) -> bool:
        """Check for repetitive phrases or content"""
        words = text.split()
        if len(words) < 10:
            return False

        # Check for repeated words
        word_count = {}
        for word in words:
            if len(word) > 3:  # Ignore short words
                word_count[word] = word_count.get(word, 0) + 1

        # If any meaningful word appears more than 3 times, it's repetitive
        return any(count > 3 for count in word_count.values())

    def _has_suspicious_links(self, submission: RedditSubmission) -> bool:
        """Check for suspicious link patterns"""
        # This is a simplified check - in production, you'd use more sophisticated analysis
        text = f"{submission.title} {submission.text}".lower()
        suspicious_patterns = ['bit.ly', 'tinyurl.com', 'short.link', 't.co']
        return any(pattern in text for pattern in suspicious_patterns)

    def _has_spam_keywords(self, text: str) -> bool:
        """Check for common spam keywords"""
        spam_keywords = [
            'click here', 'buy now', 'free money', 'make money fast',
            'limited time', 'act now', 'urgent', 'winner', 'congratulations',
            'claim your', 'guaranteed', 'risk free', 'no cost'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in spam_keywords)

    def _has_poor_grammar(self, title: str) -> bool:
        """Simplified grammar check"""
        # Check for basic punctuation issues
        if title.count('!') > 1:
            return True
        if title.count('?') > 1:
            return True
        if not title[0].isupper() and not title[0].isdigit():
            return True
        return False

    def get_model_info(self) -> dict:
        """Get model info using embedding strategy"""
        strategy_info = self.embedding_strategy.get_strategy_info()
        return {
            "model": "fake-model",
            "provider": "Fake",
            "base_url": None,
            "max_tokens": 1000,
            "temperature": 0.7,
            "is_configured": True,
            "embedding_strategy": strategy_info
        }


class OpportunityAnalyzer(SimpleOpportunityAnalyzer):
    """
    LLM-powered analyzer using OpenRouter API with cost-optimized models
    """

    def __init__(self):
        """Initialize analyzer with OpenRouter client and Instructor"""
        self.settings = get_settings()

        if not INSTRUCTOR_AVAILABLE or not OPENAI_AVAILABLE:
            raise RuntimeError("instructor and openai packages are required for OpportunityAnalyzer")

        # Configure OpenAI client for OpenRouter
        openai_config = self.settings.get_openai_client_config()
        openai_client = OpenAI(**openai_config)

        # Initialize Instructor with OpenRouter client
        self.client = instructor.from_openai(openai_client)

        # System prompt for consistent analysis
        self.system_prompt = """
You are an expert product analyst and startup opportunity scout. Your task is to analyze Reddit discussions
and extract potential app opportunities that solve real user problems.

CRITICAL RULES:
1. Maximum 3 core functions per app - this is non-negotiable. Apps with 4+ functions fail.
2. Focus on SIMPLE solutions. Users prefer focused tools over complex platforms.
3. Each function must be independently valuable and clearly described.
4. Look for recurring pain points, workaround discussions, and "I wish" statements.
5. Validate market demand through the number of upvotes, comments, and engagement.
6. Score monetization potential based on willingness to pay indicators.

CONTENT QUALITY SCORING REQUIREMENTS:
7. Assign a content_quality_score (0-100) where:
   - 80-100: High quality, original content with clear value
   - 60-79: Good quality content with minor issues
   - 40-59: Moderate quality with several concerns
   - 0-39: Low quality, likely spam or irrelevant

8. Set is_spam = True and content_quality_score ≤ 40 for:
   - Excessive capitalization or punctuation
   - Repetitive phrases or content
   - Suspicious links or URL shorteners
   - Common spam keywords (click here, buy now, free money, etc.)
   - Very short content (< 50 chars) with no substance
   - Poor grammar or formatting

9. List specific spam_indicators when is_spam=True, such as:
   - ["excessive_caps", "repetitive_content", "suspicious_links", "spam_keywords", "too_short", "poor_grammar"]

Return your analysis as structured JSON following the exact schema provided.
"""

    def analyze_submission(self, submission: RedditSubmission) -> AnalysisResult:
        """
        Analyze a single Reddit submission for app opportunities

        Args:
            submission: Reddit submission to analyze

        Returns:
            AnalysisResult with complete opportunity analysis

        Raises:
            RuntimeError: If LLM analysis fails
        """
        logger.info(f"Analyzing submission: {submission.id} - {submission.title[:50]}...")

        # Prepare user prompt with submission data
        user_prompt = self._create_analysis_prompt(submission)

        try:
            # Use Instructor to get structured output from OpenRouter
            analysis = self.client.chat.completions.create(
                model=self.settings.model_name,
                max_tokens=self.settings.max_tokens,
                temperature=self.settings.temperature,
                response_model=AnalysisResult,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )

            # Add source metadata
            analysis.submission_id = submission.id

            logger.info(f"✓ Analysis complete: {analysis.app_idea.title} (score: {analysis.final_score:.1f})")
            return analysis

        except Exception as e:
            logger.error(f"LLM analysis failed for submission {submission.id}: {e}")
            raise RuntimeError(f"Failed to analyze submission {submission.id}: {e}")

    def analyze_batch(
        self,
        submissions: List[RedditSubmission],
        batch_size: int = None
    ) -> List[AnalysisResult]:
        """
        Analyze multiple submissions in batches for efficiency

        Args:
            submissions: List of submissions to analyze
            batch_size: Size of each processing batch (from settings if None)

        Returns:
            List of AnalysisResult objects

        Raises:
            RuntimeError: If batch analysis fails
        """
        logger.info(f"Analyzing {len(submissions)} submissions in batches")

        if batch_size is None:
            batch_size = self.settings.batch_size

        results = []
        errors = []

        for i in range(0, len(submissions), batch_size):
            batch = submissions[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(submissions) + batch_size - 1) // batch_size

            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} submissions) with {self.settings.model_name}")

            for j, submission in enumerate(batch):
                try:
                    analysis = self.analyze_submission(submission)
                    results.append(analysis)

                except Exception as e:
                    error_msg = f"Failed to analyze submission {submission.id}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue

        if not results and errors:
            raise RuntimeError(f"Failed to analyze any submissions. Errors: {errors}")

        logger.info(f"✓ Batch analysis complete: {len(results)} successful, {len(errors)} failed")

        if errors:
            logger.warning(f"Encountered {len(errors)} analysis errors")

        return results

    def _create_analysis_prompt(self, submission: RedditSubmission) -> str:
        """
        Create detailed analysis prompt from Reddit submission data

        Args:
            submission: Reddit submission to analyze

        Returns:
            Formatted prompt string for LLM
        """
        prompt = f"""
ANALYZE THIS REDDIT POST FOR APP OPPORTUNITIES:

**POST DETAILS:**
- Title: {submission.title}
- Subreddit: r/{submission.subreddit}
- Author: {submission.author}
- Upvotes: {submission.upvotes}
- Comments: {submission.comments_count}
- Posted: {submission.created_utc.strftime('%Y-%m-%d %H:%M UTC')}

**CONTENT:**
{submission.text[:2000]}...

**URL:** {submission.permalink}

ANALYSIS TASK:
1. Identify the core problem or pain point being discussed
2. Extract a specific app idea that solves this problem
3. Define 1-3 core functions MAXIMUM (this is critical - 4+ functions = automatic failure)
4. Assess market demand based on engagement and problem severity
5. Evaluate monetization potential and competition level
6. Provide confidence scoring and trust level

Remember: SIMPLER IS BETTER. Focus on focused, single-purpose apps.
"""

        return prompt

    def validate_analysis_quality(self, analysis: AnalysisResult) -> bool:
        """
        Validate the quality and consistency of an analysis result

        Args:
            analysis: AnalysisResult to validate

        Returns:
            True if analysis passes quality checks, False otherwise
        """
        try:
            # Check core functions count
            if len(analysis.app_idea.core_functions) > 3:
                logger.warning(f"Analysis rejected: too many core functions ({len(analysis.app_idea.core_functions)})")
                return False

            # Check score consistency
            if not (0.0 <= analysis.final_score <= 100.0):
                logger.warning(f"Analysis rejected: invalid final_score ({analysis.final_score})")
                return False

            # Check market metrics are within bounds
            metrics = analysis.market_metrics
            if not all(0.0 <= getattr(metrics, field) <= 100.0 for field in [
                'market_demand', 'pain_intensity', 'monetization_potential',
                'competition_level', 'technical_feasibility'
            ]):
                logger.warning("Analysis rejected: invalid market metrics")
                return False

            # Check trust level
            if analysis.trust_level not in ['LOW', 'MEDIUM', 'HIGH']:
                logger.warning(f"Analysis rejected: invalid trust_level ({analysis.trust_level})")
                return False

            return True

        except Exception as e:
            logger.error(f"Analysis validation failed: {e}")
            return False

    def test_connection(self) -> bool:
        """
        Test LLM API connection with OpenRouter using a simple request

        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Testing OpenRouter connection with model: {self.settings.model_name}")

            # Simple test request
            response = self.client.chat.completions.create(
                model=self.settings.model_name,
                max_tokens=10,
                temperature=0,
                response_model=AppIdea,
                messages=[
                    {"role": "user", "content": "Create a simple test app idea about productivity"}
                ]
            )

            logger.info("✓ OpenRouter API connection test successful")
            logger.info(f"✓ Using model: {self.settings.model_name}")
            return True

        except Exception as e:
            logger.error(f"OpenRouter API connection test failed: {e}")
            logger.error(f"Model: {self.settings.model_name}")
            logger.error(f"Base URL: {self.settings.openai_base_url}")
            return False

    def get_model_info(self) -> dict:
        """
        Get information about the current model configuration

        Returns:
            Dictionary with model information
        """
        return {
            "model": self.settings.model_name,
            "provider": "OpenRouter" if self.settings.is_openrouter_configured else "OpenAI",
            "base_url": self.settings.openai_base_url,
            "max_tokens": self.settings.max_tokens,
            "temperature": self.settings.temperature,
            "is_configured": bool(self.settings.openai_api_key)
        }