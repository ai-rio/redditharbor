"""
LiteLLM-powered opportunity analysis with comprehensive cost tracking
"""

import logging
import os
import time
from datetime import datetime
from typing import Any, Optional

try:
    import instructor
    INSTRUCTOR_AVAILABLE = True
except ImportError:
    INSTRUCTOR_AVAILABLE = False
    instructor = None

import litellm

# Conditional imports for compatibility
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

from models.analysis import AnalysisResult, AppIdea, MarketMetrics
from models.cost_tracking import CostSummary, CostTracking, ModelCostConfig
from models.reddit import RedditSubmission

try:
    from .embedding_strategies import (
        EmbeddingStrategy,
        FakeEmbeddingProvider,
        OpenAIEmbeddingProvider,
    )
    from .simplicity_processor import SimplicityProcessor
except ImportError:
    # Fallback for direct import
    try:
        from transform.embedding_strategies import (
            EmbeddingStrategy,
            FakeEmbeddingProvider,
            OpenAIEmbeddingProvider,
        )
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

# AgentOps integration
try:
    from monitoring import (
        AgentOpsConfig,
        AgentOpsTracker,
        get_tracker,
        llm_call,
        tool,
        trace,
    )
    AGENTOPS_AVAILABLE = True
except ImportError:
    AGENTOPS_AVAILABLE = False
    # Mock AgentOps for backward compatibility
    class MockAgentOpsTracker:
        def __init__(self, *args, **kwargs):
            pass
        def start_session(self, *args, **kwargs):
            return None
        def end_session(self, *args, **kwargs):
            return None
        def track_llm_call(self, *args, **kwargs):
            return False
        def track_cost_summary(self, *args, **kwargs):
            return False
        def track_operation_result(self, *args, **kwargs):
            return False
        def track_error(self, *args, **kwargs):
            return False
        def get_session_summary(self):
            return None

    def trace(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    def tool(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    def llm_call(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    def get_tracker():
        return MockAgentOpsTracker()

    AgentOpsTracker = MockAgentOpsTracker
    AgentOpsConfig = None

logger = logging.getLogger(__name__)


class LiteLLMAnalyzer:
    """
    LiteLLM-powered analyzer with comprehensive cost tracking, AgentOps integration, and unified API access
    """

    def __init__(self,
                 model_name: str = "anthropic/claude-haiku-4.5",
                 enable_cost_tracking: bool = True,
                 enable_agentops_tracking: bool = True,
                 agentops_config: Optional[AgentOpsConfig] = None):
        """
        Initialize LiteLLM analyzer with cost tracking and AgentOps integration

        Args:
            model_name: Model identifier (e.g., "anthropic/claude-haiku-4.5")
            enable_cost_tracking: Whether to enable internal cost tracking
            enable_agentops_tracking: Whether to enable AgentOps monitoring
            agentops_config: Custom AgentOps configuration (defaults to environment)
        """
        self.settings = get_settings() if SETTINGS_AVAILABLE else MockSettings()
        self.model_name = model_name or self.settings.model_name
        self.enable_cost_tracking = enable_cost_tracking
        self.enable_agentops_tracking = enable_agentops_tracking and AGENTOPS_AVAILABLE
        self.simplicity_processor = SimplicityProcessor()

        # Initialize AgentOps tracker if enabled
        if self.enable_agentops_tracking:
            try:
                if agentops_config:
                    self.agentops_tracker = AgentOpsTracker(agentops_config)
                else:
                    self.agentops_tracker = get_tracker()

                logger.info(f"AgentOps tracking enabled for model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize AgentOps tracker: {e}")
                self.enable_agentops_tracking = False
                self.agentops_tracker = None
        else:
            self.agentops_tracker = None

        # Session tracking
        self._session_id = None
        self._analysis_count = 0

        # Configure LiteLLM for OpenRouter
        litellm.api_base = "https://openrouter.ai/api/v1"
        litellm.set_verbose = False

    def start_analysis_session(self, session_name: str | None = None,
                              tags: list[str] | None = None) -> str | None:
        """
        Start a new analysis session with AgentOps tracking

        Args:
            session_name: Name for the analysis session
            tags: Additional tags for the session

        Returns:
            Session ID if successful, None otherwise
        """
        if not self.enable_agentops_tracking:
            logger.debug("AgentOps tracking disabled, skipping session start")
            return None

        session_name = session_name or f"litellm_analysis_{self.model_name}"
        tags = tags or [self.model_name, "pipeline-v3", "analysis"]

        try:
            self._session_id = self.agentops_tracker.start_session(session_name, tags)
            self._analysis_count = 0
            logger.info(f"Started AgentOps analysis session: {self._session_id}")
            return self._session_id
        except Exception as e:
            logger.error(f"Failed to start AgentOps session: {e}")
            return None

    def end_analysis_session(self, status: str = "success") -> dict[str, Any] | None:
        """
        End current analysis session and return summary

        Args:
            status: Session completion status

        Returns:
            Session summary if available, None otherwise
        """
        if not self.enable_agentops_tracking or not self._session_id:
            return None

        try:
            metadata = {
                "model": self.model_name,
                "analysis_count": self._analysis_count,
                "analyzer_type": "LiteLLMAnalyzer"
            }

            summary = self.agentops_tracker.end_session(status, metadata)
            self._session_id = None
            logger.info(f"Ended AgentOps analysis session with status: {status}")
            return summary
        except Exception as e:
            logger.error(f"Failed to end AgentOps session: {e}")
            return None

    def get_session_summary(self) -> dict[str, Any] | None:
        """Get current session summary"""
        if not self.enable_agentops_tracking:
            return None

        try:
            return self.agentops_tracker.get_session_summary()
        except Exception as e:
            logger.error(f"Failed to get session summary: {e}")
            return None

        # Model cost configurations (per 1M tokens)
        self.model_costs = {
            "anthropic/claude-haiku-4.5": ModelCostConfig(
                model_name="anthropic/claude-haiku-4.5",
                provider="openrouter",
                input_cost_per_million=1.0,
                output_cost_per_million=5.0,
                max_tokens=200000,
                supports_json_mode=True
            ),
            "anthropic/claude-3.5-sonnet": ModelCostConfig(
                model_name="anthropic/claude-3.5-sonnet",
                provider="openrouter",
                input_cost_per_million=3.0,
                output_cost_per_million=15.0,
                max_tokens=200000,
                supports_json_mode=True
            ),
            "openai/gpt-4o-mini": ModelCostConfig(
                model_name="openai/gpt-4o-mini",
                provider="openrouter",
                input_cost_per_million=0.15,
                output_cost_per_million=0.60,
                max_tokens=128000,
                supports_json_mode=True
            ),
            "meta-llama/llama-3.1-8b-instruct:floor": ModelCostConfig(
                model_name="meta-llama/llama-3.1-8b-instruct:floor",
                provider="openrouter",
                input_cost_per_million=0.10,
                output_cost_per_million=0.10,
                max_tokens=128000,
                supports_json_mode=True
            ),
        }

        # Initialize embedding strategy with fallback
        try:
            fake_provider = FakeEmbeddingProvider(dimensions=384, value_range=(-1.0, 1.0))
            self.embedding_strategy = EmbeddingStrategy(fake_provider)
        except Exception:
            # Create minimal mock strategy for testing
            class MockEmbeddingStrategy:
                def generate_embedding(self, text, metadata=None):
                    return [0.0] * 384, metadata
            self.embedding_strategy = MockEmbeddingStrategy()

        # Initialize Instructor client with LiteLLM
        self.client = None
        if INSTRUCTOR_AVAILABLE:
            try:
                # Use OpenAI client wrapper for LiteLLM
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
                logger.warning(f"Failed to initialize Instructor client: {e}")
                self.client = None

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
        Analyze a single Reddit submission (backward compatible method)

        Args:
            submission: Reddit submission to analyze

        Returns:
            AnalysisResult with complete opportunity analysis
        """
        analysis, _ = self.analyze_submission_with_costs(submission)
        return analysis

    @trace(name="analyze_submission", track_args=False, track_result=True)
    @llm_call(model_name="auto", track_cost=True, track_tokens=True)
    def analyze_submission_with_costs(self, submission: RedditSubmission) -> tuple[AnalysisResult, CostTracking]:
        """
        Analyze a single Reddit submission with detailed cost tracking and AgentOps monitoring

        Args:
            submission: Reddit submission to analyze

        Returns:
            Tuple of (AnalysisResult, CostTracking)
        """
        logger.info(f"Analyzing submission with LiteLLM: {submission.id} - {submission.title[:50]}...")

        self._analysis_count += 1
        start_time = time.time()
        user_prompt = self._create_analysis_prompt(submission)

        # Track analysis start if AgentOps is available
        if self.enable_agentops_tracking and self.agentops_tracker:
            self.agentops_tracker.track_operation_result(
                "submission_analysis_start",
                success=True,
                metadata={
                    "submission_id": submission.id,
                    "model": self.model_name,
                    "prompt_length": len(user_prompt),
                    "subreddit": submission.subreddit
                }
            )

        try:
            if self.client:
                # Use Instructor for structured output
                analysis = self.client.chat.completions.create(
                    model=f"openrouter/{self.model_name}",
                    max_tokens=self.settings.max_tokens,
                    temperature=self.settings.temperature,
                    response_model=AnalysisResult,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )
            else:
                # Fallback to LiteLLM without structured output
                response = litellm.completion(
                    model=f"openrouter/{self.model_name}",
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=self.settings.max_tokens,
                    temperature=self.settings.temperature
                )
                # Parse structured response manually (simplified for fallback)
                import json
                analysis_data = json.loads(response.choices[0].message.content)
                analysis = AnalysisResult(**analysis_data)

            # Calculate latency
            latency = time.time() - start_time

            # Add source metadata
            analysis.submission_id = submission.id

            # Apply simplicity processor to adjust scoring and functions
            analysis = self.simplicity_processor.process_analysis(analysis)

            # Generate embedding
            embedding_metadata = {
                'submission_id': submission.id,
                'source': 'reddit_submission_analysis'
            }
            text_for_embedding = f"{submission.title} {submission.text} {submission.subreddit}"
            embedding, embedding_metadata = self.embedding_strategy.generate_embedding(
                text_for_embedding,
                embedding_metadata
            )

            # Set embedding
            analysis.embedding = embedding
            analysis.embedding_metadata = embedding_metadata

            # Create cost tracking data
            if self.enable_cost_tracking:
                cost_data = self._create_cost_tracking_from_analysis(
                    analysis, latency, len(user_prompt), success=True
                )
            else:
                cost_data = self._create_zero_cost_tracking(latency)

            # Track successful analysis with AgentOps
            if self.enable_agentops_tracking and self.agentops_tracker:
                try:
                    # Track the LLM call specifically
                    self.agentops_tracker.track_llm_call(
                        model=self.model_name,
                        tokens=cost_data.total_tokens,
                        cost=cost_data.total_cost_usd,
                        latency=cost_data.latency_seconds,
                        success=True,
                        metadata={
                            "submission_id": submission.id,
                            "analysis_type": "reddit_opportunity",
                            "final_score": analysis.final_score,
                            "app_title": analysis.app_idea.title
                        }
                    )

                    # Track analysis completion
                    self.agentops_tracker.track_operation_result(
                        "submission_analysis_complete",
                        success=True,
                        metadata={
                            "submission_id": submission.id,
                            "model": self.model_name,
                            "cost_usd": cost_data.total_cost_usd,
                            "final_score": analysis.final_score,
                            "content_quality_score": analysis.content_quality_score,
                            "is_spam": analysis.is_spam
                        }
                    )
                except Exception as track_error:
                    logger.warning(f"Failed to track with AgentOps: {track_error}")

            logger.info(f"✓ LiteLLM analysis complete: {analysis.app_idea.title} (score: {analysis.final_score:.1f})")
            return analysis, cost_data

        except Exception as e:
            logger.error(f"LiteLLM analysis failed for submission {submission.id}: {e}")

            # Track error with AgentOps
            if self.enable_agentops_tracking and self.agentops_tracker:
                try:
                    self.agentops_tracker.track_error(
                        error_type=type(e).__name__,
                        error_message=str(e),
                        metadata={
                            "submission_id": submission.id,
                            "model": self.model_name,
                            "analysis_type": "reddit_opportunity",
                            "prompt_length": len(user_prompt),
                            "latency": time.time() - start_time
                        }
                    )
                except Exception as track_error:
                    logger.warning(f"Failed to track error with AgentOps: {track_error}")

            # Return error analysis with cost tracking
            error_analysis = self._create_error_analysis(submission, str(e))
            cost_data = self._create_error_cost_tracking(time.time() - start_time, len(user_prompt), str(e))

            return error_analysis, cost_data

    def analyze_batch(self, submissions: list[RedditSubmission], batch_size: int = None) -> list[AnalysisResult]:
        """
        Analyze multiple submissions in batches (backward compatible)

        Args:
            submissions: List of submissions to analyze
            batch_size: Size of each processing batch

        Returns:
            List of AnalysisResult objects
        """
        results, _ = self.analyze_batch_with_costs(submissions, batch_size)
        return results

    @trace(name="analyze_batch", track_args=False, track_result=True)
    def analyze_batch_with_costs(
        self,
        submissions: list[RedditSubmission],
        batch_size: int = None
    ) -> tuple[list[AnalysisResult], CostSummary]:
        """
        Analyze multiple submissions in batches with cost summary

        Args:
            submissions: List of submissions to analyze
            batch_size: Size of each processing batch

        Returns:
            Tuple of (List[AnalysisResult], CostSummary)
        """
        logger.info(f"Analyzing {len(submissions)} submissions in batches with LiteLLM")

        if batch_size is None:
            batch_size = self.settings.batch_size if hasattr(self.settings, 'batch_size') else 5

        results = []
        cost_data_list = []
        errors = []

        for i in range(0, len(submissions), batch_size):
            batch = submissions[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(submissions) + batch_size - 1) // batch_size

            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} submissions) with {self.model_name}")

            for submission in batch:
                try:
                    analysis, cost_data = self.analyze_submission_with_costs(submission)
                    results.append(analysis)
                    cost_data_list.append(cost_data)

                except Exception as e:
                    error_msg = f"Failed to analyze submission {submission.id}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue

        if not results and errors:
            raise RuntimeError(f"Failed to analyze any submissions. Errors: {errors}")

        # Generate cost summary
        cost_summary = self.calculate_cost_summary(cost_data_list)

        logger.info(f"✓ LiteLLM batch analysis complete: {len(results)} successful, {len(errors)} failed")

        if errors:
            logger.warning(f"Encountered {len(errors)} analysis errors")

        return results, cost_summary

    def calculate_cost_summary(self, cost_data_list: list[CostTracking]) -> CostSummary:
        """
        Calculate cost summary from a list of cost tracking data

        Args:
            cost_data_list: List of CostTracking objects

        Returns:
            CostSummary with aggregated data
        """
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
                model_breakdown[model] = {
                    "count": 0,
                    "cost": 0.0,
                    "tokens": 0,
                    "avg_cost": 0.0
                }

            model_breakdown[model]["count"] += 1
            model_breakdown[model]["cost"] += cost.total_cost_usd
            model_breakdown[model]["tokens"] += cost.total_tokens

        # Calculate averages for each model
        for model_data in model_breakdown.values():
            if model_data["count"] > 0:
                model_data["avg_cost"] = model_data["cost"] / model_data["count"]

        cost_summary = CostSummary(
            total_cost_usd=round(total_cost, 6),
            total_tokens=total_tokens,
            analysis_count=analysis_count,
            avg_cost_per_analysis=round(total_cost / analysis_count, 6) if analysis_count > 0 else 0.0,
            model_breakdown=model_breakdown,
            timestamp=datetime.utcnow()
        )

        # Track cost summary with AgentOps
        if self.enable_agentops_tracking and self.agentops_tracker:
            try:
                self.agentops_tracker.track_cost_summary(cost_summary)
            except Exception as track_error:
                logger.warning(f"Failed to track cost summary with AgentOps: {track_error}")

        return cost_summary

    def test_connection(self) -> bool:
        """
        Test LiteLLM API connection

        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Testing LiteLLM connection with model: {self.model_name}")

            response = litellm.completion(
                model=f"openrouter/{self.model_name}",
                messages=[
                    {"role": "user", "content": "Create a simple test app idea about productivity"}
                ],
                max_tokens=100,
                temperature=0
            )

            logger.info("✓ LiteLLM API connection test successful")
            logger.info(f"✓ Using model: {self.model_name}")
            return True

        except Exception as e:
            logger.error(f"LiteLLM API connection test failed: {e}")
            return False

    def get_model_info(self) -> dict:
        """
        Get information about the current model configuration

        Returns:
            Dictionary with model information
        """
        model_config = self.model_costs.get(self.model_name)

        return {
            "model": self.model_name,
            "provider": model_config.provider if model_config else "unknown",
            "base_url": "https://openrouter.ai/api/v1",
            "max_tokens": self.settings.max_tokens if hasattr(self.settings, 'max_tokens') else 1000,
            "temperature": self.settings.temperature if hasattr(self.settings, 'temperature') else 0.3,
            "is_configured": bool(self.settings.openai_api_key) if hasattr(self.settings, 'openai_api_key') else False,
            "cost_tracking_enabled": self.enable_cost_tracking,
            "model_costs": {
                "input_cost_per_million": model_config.input_cost_per_million if model_config else 0,
                "output_cost_per_million": model_config.output_cost_per_million if model_config else 0
            }
        }

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

    def _create_cost_tracking_from_analysis(
        self,
        analysis: AnalysisResult,
        latency: float,
        prompt_length: int,
        success: bool = True
    ) -> CostTracking:
        """
        Create cost tracking data from analysis result

        Args:
            analysis: Analysis result
            latency: Request latency in seconds
            prompt_length: Length of prompt in characters
            success: Whether request was successful

        Returns:
            CostTracking object
        """
        model_config = self.model_costs.get(self.model_name)

        # Estimate token counts (in real implementation, these would come from the API response)
        # For now, we'll estimate based on text length
        estimated_prompt_tokens = max(100, prompt_length // 4)  # Rough estimate: 1 token per 4 chars
        estimated_completion_tokens = 300  # Estimate for structured output
        estimated_total_tokens = estimated_prompt_tokens + estimated_completion_tokens

        if model_config:
            input_cost = (estimated_prompt_tokens / 1_000_000) * model_config.input_cost_per_million
            output_cost = (estimated_completion_tokens / 1_000_000) * model_config.output_cost_per_million
            total_cost = input_cost + output_cost
            pricing = {
                "input": model_config.input_cost_per_million,
                "output": model_config.output_cost_per_million
            }
        else:
            # Default pricing
            input_cost = estimated_prompt_tokens * 0.000001  # $1 per 1M tokens
            output_cost = estimated_completion_tokens * 0.000005  # $5 per 1M tokens
            total_cost = input_cost + output_cost
            pricing = {"input": 1.0, "output": 5.0}

        return CostTracking(
            model_used=self.model_name,
            provider=model_config.provider if model_config else "openrouter",
            prompt_tokens=estimated_prompt_tokens,
            completion_tokens=estimated_completion_tokens,
            total_tokens=estimated_total_tokens,
            input_cost_usd=round(input_cost, 6),
            output_cost_usd=round(output_cost, 6),
            total_cost_usd=round(total_cost, 6),
            latency_seconds=round(latency, 3),
            prompt_length_chars=prompt_length,
            model_pricing_per_m_tokens=pricing,
            request_success=success
        )

    def _create_zero_cost_tracking(self, latency: float) -> CostTracking:
        """Create zero cost tracking for cases where cost tracking is disabled"""
        return CostTracking(
            model_used=self.model_name,
            provider="openrouter",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            input_cost_usd=0.0,
            output_cost_usd=0.0,
            total_cost_usd=0.0,
            latency_seconds=round(latency, 3),
            prompt_length_chars=0,
            model_pricing_per_m_tokens={"input": 0.0, "output": 0.0},
            request_success=True
        )

    def _create_error_analysis(self, submission: RedditSubmission, error_message: str) -> AnalysisResult:
        """Create a fallback analysis when LLM fails"""
        from datetime import datetime

        return AnalysisResult(
            submission_id=submission.id,
            analyzed_at=datetime.now(),
            app_idea=AppIdea(
                title=f"Analysis Failed - {submission.subreddit.title()}",
                app_concept=f"Unable to analyze due to error: {error_message[:100]}...",
                problem_statement="Analysis failed - manual review required",
                core_functions=["Manual analysis needed"],
                target_audience="Unknown - analysis failed"
            ),
            market_metrics=MarketMetrics(
                market_demand=50.0,
                pain_intensity=10.0,
                monetization_potential=15.0,
                competition_level=80.0,
                technical_feasibility=10.0
            ),
            final_score=21.25,
            confidence_score=0.0,
            trust_level="LOW",
            content_quality_score=0.0,
            is_spam=False,
            spam_indicators=[],
            embedding=None,
            embedding_metadata=None
        )

    def _create_error_cost_tracking(
        self,
        latency: float,
        prompt_length: int,
        error_message: str
    ) -> CostTracking:
        """Create cost tracking for failed requests"""
        return CostTracking(
            model_used=self.model_name,
            provider="openrouter",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            input_cost_usd=0.0,
            output_cost_usd=0.0,
            total_cost_usd=0.0,
            latency_seconds=round(latency, 3),
            prompt_length_chars=prompt_length,
            model_pricing_per_m_tokens={"input": 0.0, "output": 0.0},
            request_success=False,
            error_message=error_message
        )
