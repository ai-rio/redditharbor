"""
LLM-powered opportunity analysis using LiteLLM with comprehensive cost tracking
"""

import logging
import os
from datetime import datetime
from typing import List, Optional, Tuple

try:
    import instructor
    INSTRUCTOR_AVAILABLE = True
except ImportError:
    INSTRUCTOR_AVAILABLE = False
    instructor = None

try:
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    litellm = None

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

try:
    from config import get_settings
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False

    # Mock settings for testing
    class MockSettings:
        def __init__(self):
            self.model_name = "anthropic/claude-haiku-4.5"
            self.max_tokens = 1000
            self.temperature = 0.3
            self.openai_api_key = os.getenv("OPENROUTER_API_KEY")
            self.openai_base_url = "https://openrouter.ai/api/v1"
            self.is_openrouter_configured = True
            self.batch_size = 5

        def get_openai_client_config(self):
            return {
                "api_key": self.openai_api_key,
                "base_url": self.openai_base_url
            }

    def get_settings():
        return MockSettings()
from models.reddit import RedditSubmission
from models.analysis import AnalysisResult, AppIdea, MarketMetrics
from models.cost_tracking import CostTracking, CostSummary

try:
    from .embedding_strategies import EmbeddingStrategy, FakeEmbeddingProvider, OpenAIEmbeddingProvider
    from .simplicity_processor import SimplicityProcessor
except ImportError:
    # Fallback for direct import
    try:
        from transform.embedding_strategies import EmbeddingStrategy, FakeEmbeddingProvider, OpenAIEmbeddingProvider
        from transform.simplicity_processor import SimplicityProcessor
    except ImportError:
        # Mock implementations for testing
        class FakeEmbeddingProvider:
            def __init__(self, dimensions=384, value_range=(-1.0, 1.0)):
                self.dimensions = dimensions
                self.value_range = value_range

        class EmbeddingStrategy:
            def __init__(self, provider):
                self.provider = provider

        class SimplicityProcessor:
            def process_analysis(self, analysis):
                return analysis

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
        # Format subreddit name properly for title case
        subreddit_formatted = submission.subreddit.title() if submission.subreddit else "General"
        app_idea = AppIdea(
            title=f"AI-Powered Productivity Solution for {subreddit_formatted} Community",
            app_concept=f"A comprehensive application designed to address the specific needs and challenges faced by {submission.subreddit} community members, providing intelligent automation and workflow optimization",
            problem_statement=f"Users in the {submission.subreddit} community frequently struggle with managing their daily tasks and maintaining productivity in an increasingly digital world. The current solutions available in the market are often too generic and fail to address the specific pain points and workflows that are unique to this community's needs and preferences.",
            target_audience=f"Active members of the r/{submission.subreddit} community, including content creators, moderators, and engaged users who are looking for specialized tools to enhance their productivity and streamline their community participation activities.",
            core_functions=["intelligent task automation", "community workflow optimization", "personalized productivity analytics"]
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
    LLM-powered analyzer using LiteLLM for unified API access with comprehensive cost tracking
    """

    def __init__(self, use_litellm: bool = True, enable_cost_tracking: bool = True):
        """
        Initialize analyzer with LiteLLM support and optional cost tracking

        Args:
            use_litellm: Whether to use LiteLLM (recommended) or direct OpenAI client
            enable_cost_tracking: Whether to enable comprehensive cost tracking
        """
        self.settings = get_settings() if SETTINGS_AVAILABLE else MockSettings()
        self.use_litellm = use_litellm and LITELLM_AVAILABLE
        self.enable_cost_tracking = enable_cost_tracking

        # Initialize simplicity processor for score-driven function adjustment
        self.simplicity_processor = SimplicityProcessor()

        # Model cost configurations for cost tracking
        self.model_costs = {
            "anthropic/claude-haiku-4.5": {"input_cost": 1.0, "output_cost": 5.0},
            "anthropic/claude-3.5-sonnet": {"input_cost": 3.0, "output_cost": 15.0},
            "openai/gpt-4o-mini": {"input_cost": 0.15, "output_cost": 0.60},
        }

        # Configure LiteLLM if available and enabled
        if self.use_litellm:
            litellm.api_base = "https://openrouter.ai/api/v1"
            litellm.set_verbose = False
            self._init_litellm_client()
        else:
            # Fallback to direct OpenAI client
            self._init_openai_client()

    def _init_litellm_client(self):
        """Initialize LiteLLM client"""
        self.client = None
        if INSTRUCTOR_AVAILABLE:
            try:
                import openai
                openai_client = openai.OpenAI(
                    api_key=self.settings.openai_api_key,
                    base_url=self.settings.openai_base_url
                )
                self.client = instructor.from_openai(
                    openai_client,
                    mode=instructor.Mode.JSON
                )
            except Exception as e:
                logger.warning(f"Failed to initialize LiteLLM Instructor client: {e}")
                self.client = None

    def _init_openai_client(self):
        """Initialize direct OpenAI client (legacy mode)"""
        if not INSTRUCTOR_AVAILABLE or not OPENAI_AVAILABLE:
            raise RuntimeError("instructor and openai packages are required for OpportunityAnalyzer in legacy mode")

        # Configure OpenAI client for OpenRouter
        openai_config = self.settings.get_openai_client_config()
        openai_client = OpenAI(**openai_config)

        # Initialize Instructor with OpenRouter client using JSON mode for compatibility
        self.client = instructor.from_openai(
            openai_client,
            mode=instructor.Mode.JSON
        )

        # System prompt for consistent analysis
        self.system_prompt = """
You are an expert product analyst and startup opportunity scout. Your task is to analyze Reddit discussions
and extract potential app opportunities that solve real user problems.

CRITICAL RULES:
1. Maximum 3 core functions per app - this is non-negotiable. Apps with 4+ functions fail.
2. Identify the core functions that solve the problem based ONLY on the problem domain.
3. Each function must be independently valuable and clearly described.
4. Look for recurring pain points, workaround discussions, and "I wish" statements.
5. Validate market demand through the number of upvotes, comments, and engagement.
6. Score monetization potential based on willingness to pay indicators.

FUNCTION GENERATION:
Generate core functions based on the problem domain, not simplicity preferences:
- If the problem requires 1 core function, provide 1
- If the problem requires 2 complementary functions, provide 2
- If the problem requires 3 related functions, provide 3
- Do NOT artificially limit or expand functions to reach a target count

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
        logger.info(f"Analyzing submission ({'LiteLLM' if self.use_litellm else 'Direct'}): {submission.id} - {submission.title[:50]}...")

        # Prepare user prompt with submission data
        user_prompt = self._create_analysis_prompt(submission)

        try:
            if self.use_litellm and LITELLM_AVAILABLE:
                # Use LiteLLM for unified API access
                analysis = self._analyze_with_litellm(user_prompt)
            else:
                # Use direct OpenAI client (legacy)
                analysis = self._analyze_with_openai(user_prompt)

            # Add source metadata
            analysis.submission_id = submission.id

            # Apply simplicity processor to adjust scoring and functions
            analysis = self.simplicity_processor.process_analysis(analysis)

            # Generate embedding using parent's embedding strategy
            if hasattr(self, 'embedding_strategy'):
                text_for_embedding = f"{submission.title} {submission.text} {submission.subreddit}"
                embedding_metadata = {
                    'submission_id': submission.id,
                    'source': 'reddit_submission_analysis'
                }
                embedding, embedding_metadata = self.embedding_strategy.generate_embedding(
                    text_for_embedding,
                    embedding_metadata
                )
                analysis.embedding = embedding
                analysis.embedding_metadata = embedding_metadata

            logger.info(f"✓ Analysis complete: {analysis.app_idea.title} (score: {analysis.final_score:.1f})")
            return analysis

        except Exception as e:
            logger.error(f"LLM analysis failed for submission {submission.id}: {e}")
            raise RuntimeError(f"Failed to analyze submission {submission.id}: {e}")

    def analyze_submission_with_costs(self, submission: RedditSubmission) -> Tuple[AnalysisResult, Optional[CostTracking]]:
        """
        Analyze a single Reddit submission with cost tracking (if enabled)

        Args:
            submission: Reddit submission to analyze

        Returns:
            Tuple of (AnalysisResult, CostTracking) - CostTracking is None if disabled
        """
        import time
        start_time = time.time()

        analysis = self.analyze_submission(submission)

        # Create cost tracking if enabled
        cost_data = None
        if self.enable_cost_tracking:
            cost_data = self._create_cost_tracking(
                latency=time.time() - start_time,
                prompt_length=len(self._create_analysis_prompt(submission)),
                success=True
            )

        return analysis, cost_data

    def analyze_batch_with_costs(
        self,
        submissions: List[RedditSubmission],
        batch_size: int = None
    ) -> Tuple[List[AnalysisResult], Optional[CostSummary]]:
        """
        Analyze multiple submissions in batches with cost summary

        Args:
            submissions: List of submissions to analyze
            batch_size: Size of each processing batch

        Returns:
            Tuple of (List[AnalysisResult], CostSummary) - CostSummary is None if disabled
        """
        results = []
        cost_data_list = []

        for submission in submissions:
            try:
                analysis, cost_data = self.analyze_submission_with_costs(submission)
                results.append(analysis)
                if cost_data:
                    cost_data_list.append(cost_data)
            except Exception as e:
                logger.error(f"Failed to analyze submission {submission.id}: {e}")
                continue

        # Generate cost summary if enabled
        cost_summary = None
        if self.enable_cost_tracking and cost_data_list:
            cost_summary = self._calculate_cost_summary(cost_data_list)

        return results, cost_summary

    def _analyze_with_litellm(self, user_prompt: str) -> AnalysisResult:
        """Analyze using LiteLLM"""
        if self.client:
            # Use Instructor with LiteLLM backend
            return self.client.chat.completions.create(
                model=f"openrouter/{self.settings.model_name}",
                max_tokens=self.settings.max_tokens,
                temperature=self.settings.temperature,
                response_model=AnalysisResult,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
        else:
            # Fallback to direct LiteLLM call
            response = litellm.completion(
                model=f"openrouter/{self.settings.model_name}",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.settings.max_tokens,
                temperature=self.settings.temperature
            )
            # Parse response (simplified for fallback)
            import json
            analysis_data = json.loads(response.choices[0].message.content)
            return AnalysisResult(**analysis_data)

    def _analyze_with_openai(self, user_prompt: str) -> AnalysisResult:
        """Analyze using direct OpenAI client (legacy)"""
        return self.client.chat.completions.create(
            model=self.settings.model_name,
            max_tokens=self.settings.max_tokens,
            temperature=self.settings.temperature,
            response_model=AnalysisResult,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

    def _create_cost_tracking(self, latency: float, prompt_length: int, success: bool) -> CostTracking:
        """Create cost tracking data"""
        model_config = self.model_costs.get(self.settings.model_name, {"input_cost": 1.0, "output_cost": 5.0})

        # Estimate token counts
        estimated_prompt_tokens = max(100, prompt_length // 4)
        estimated_completion_tokens = 400  # Estimate for structured output
        estimated_total_tokens = estimated_prompt_tokens + estimated_completion_tokens

        input_cost = (estimated_prompt_tokens / 1_000_000) * model_config["input_cost"]
        output_cost = (estimated_completion_tokens / 1_000_000) * model_config["output_cost"]
        total_cost = input_cost + output_cost

        return CostTracking(
            model_used=self.settings.model_name,
            provider="openrouter",
            prompt_tokens=estimated_prompt_tokens,
            completion_tokens=estimated_completion_tokens,
            total_tokens=estimated_total_tokens,
            input_cost_usd=round(input_cost, 6),
            output_cost_usd=round(output_cost, 6),
            total_cost_usd=round(total_cost, 6),
            latency_seconds=round(latency, 3),
            prompt_length_chars=prompt_length,
            model_pricing_per_m_tokens=model_config,
            request_success=success
        )

    def _calculate_cost_summary(self, cost_data_list: List[CostTracking]) -> CostSummary:
        """Calculate cost summary from list of cost tracking data"""
        if not cost_data_list:
            return CostSummary(
                total_cost_usd=0.0,
                total_tokens=0,
                analysis_count=0,
                avg_cost_per_analysis=0.0,
                model_breakdown={},
                timestamp=datetime.utcnow()
            )

        total_cost = sum(cost.total_cost_usd for cost in cost_data_list)
        total_tokens = sum(cost.total_tokens for cost in cost_data_list)
        analysis_count = len(cost_data_list)

        # Model breakdown
        model_breakdown = {}
        for cost in cost_data_list:
            model = cost.model_used
            if model not in model_breakdown:
                model_breakdown[model] = {"count": 0, "cost": 0.0, "tokens": 0}
            model_breakdown[model]["count"] += 1
            model_breakdown[model]["cost"] += cost.total_cost_usd
            model_breakdown[model]["tokens"] += cost.total_tokens

        return CostSummary(
            total_cost_usd=round(total_cost, 6),
            total_tokens=total_tokens,
            analysis_count=analysis_count,
            avg_cost_per_analysis=round(total_cost / analysis_count, 6) if analysis_count > 0 else 0.0,
            model_breakdown=model_breakdown,
            timestamp=datetime.utcnow()
        )

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

            # Simple test request with sufficient tokens for JSON response
            response = self.client.chat.completions.create(
                model=self.settings.model_name,
                max_tokens=500,  # Increased to allow full JSON response
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
        model_config = self.model_costs.get(self.settings.model_name, {"input_cost": 1.0, "output_cost": 5.0})

        return {
            "model": self.settings.model_name,
            "provider": "OpenRouter",
            "base_url": self.settings.openai_base_url,
            "max_tokens": self.settings.max_tokens,
            "temperature": self.settings.temperature,
            "is_configured": bool(self.settings.openai_api_key),
            "use_litellm": self.use_litellm,
            "cost_tracking_enabled": self.enable_cost_tracking,
            "model_costs": {
                "input_cost_per_million": model_config["input_cost"],
                "output_cost_per_million": model_config["output_cost"]
            },
            "litellm_available": LITELLM_AVAILABLE,
            "instructor_available": INSTRUCTOR_AVAILABLE
        }