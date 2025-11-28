"""
LLM-powered opportunity analysis using OpenRouter API with Instructor validation
"""

import logging
from typing import List

import instructor
from openai import OpenAI

from config import get_settings
from models import RedditSubmission, AnalysisResult, AppIdea, MarketMetrics

logger = logging.getLogger(__name__)


class OpportunityAnalyzer:
    """
    LLM-powered analyzer using OpenRouter API with cost-optimized models
    """

    def __init__(self):
        """Initialize analyzer with OpenRouter client and Instructor"""
        self.settings = get_settings()

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