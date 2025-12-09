"""
LLM-based opportunity analyzer using LiteLLM
Supports OpenAI, Anthropic, OpenRouter, and other providers
"""

import logging
import json
from typing import Any
import litellm
from models.reddit import RedditSubmission
from models.analysis import AnalysisResult
from config.settings import get_settings

logger = logging.getLogger(__name__)


class OpportunityAnalyzer:
    """
    Single LLM analyzer with structured output
    Uses LiteLLM for provider flexibility
    """

    def __init__(self, settings=None):
        """Initialize analyzer with settings"""
        self.settings = settings or get_settings()

        # Configure LiteLLM
        litellm.api_key = self.settings.llm_api_key
        litellm.api_base = self.settings.llm_base_url

        # System prompt for opportunity analysis
        self.system_prompt = """You are an expert product opportunity analyst.
Analyze Reddit submissions to identify SaaS product opportunities.

For each submission, provide:
1. WTP Score (0-100): Willingness-to-pay based on pain severity
2. Final Score (0-100): Overall opportunity score
3. Confidence Score (0-100): Analysis confidence level
4. Core Functions: 3-5 key features the product should have
5. Pricing Strategy: Initial pricing recommendation
6. Target Segment: Primary user persona
7. Pain Points: Key problems mentioned
8. Trust Level: LOW/MEDIUM/HIGH based on post quality

Return valid JSON matching the AnalysisResult schema."""

    def analyze(self, submission: RedditSubmission) -> AnalysisResult:
        """
        Analyze a Reddit submission for product opportunities

        Args:
            submission: Reddit submission to analyze

        Returns:
            Structured analysis result

        Raises:
            RuntimeError: If LLM call fails
        """
        try:
            # Build analysis prompt
            prompt = self._build_prompt(submission)

            # Call LLM with structured output
            response = litellm.completion(
                model=self.settings.llm_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.settings.llm_temperature,
                max_tokens=self.settings.llm_max_tokens,
                response_format={"type": "json_object"}  # Force JSON
            )

            # Parse response
            content = response.choices[0].message.content
            result_data = json.loads(content)

            # Add metadata
            result_data["submission_id"] = submission.id
            result_data["subreddit"] = submission.subreddit
            result_data["title"] = submission.title

            # Validate with Pydantic
            return AnalysisResult(**result_data)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from LLM: {e}")
            raise RuntimeError(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Analysis failed for {submission.id}: {e}")
            raise RuntimeError(f"Analysis failed: {e}")

    def _build_prompt(self, submission: RedditSubmission) -> str:
        """Build analysis prompt from submission"""
        return f"""Analyze this Reddit post for SaaS product opportunities:

SUBREDDIT: r/{submission.subreddit}
TITLE: {submission.title}
CONTENT: {submission.selftext[:1000]}
ENGAGEMENT: {submission.score} upvotes, {submission.num_comments} comments

Provide a JSON analysis matching this structure:
{{
    "wtp_score": <0-100>,
    "final_score": <0-100>,
    "confidence_score": <0-100>,
    "core_functions": ["feature1", "feature2", ...],
    "pricing_strategy": {{"tier": "...", "price": "..."}},
    "target_segment": "description",
    "pain_points": ["pain1", "pain2", ...],
    "trust_level": "LOW|MEDIUM|HIGH"
}}"""