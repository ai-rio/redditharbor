"""
LLM-based opportunity analyzer using LiteLLM
Supports OpenAI, Anthropic, OpenRouter, and other providers
"""

import json
import logging

import litellm

from config.settings import get_settings
from models.analysis import AnalysisResult
from models.reddit import RedditSubmission

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

For each submission, provide a complete analysis matching the AnalysisResult schema:
- app_idea: title, app_concept, problem_statement, core_functions (1-3), target_audience
- metrics: market_demand, pain_intensity, monetization_potential, competition_level (0-100, higher=less competition), technical_feasibility
- pain_points: list of identified pain points (1-5 items)
- opportunity_summary: Brief opportunity summary (50-500 chars)
- final_score: Overall opportunity score (0-100)
- wtp_score: Willingness-to-pay score (0-100)
- confidence_score: Analysis confidence level (0-100)
- trust_level: LOW/MEDIUM/HIGH
- content_quality_score: AI content quality (0-100)
- is_spam: boolean
- spam_indicators: list of spam indicators if any

Ensure all scores are between 0-100 and the response is valid JSON."""

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
CONTENT: {submission.selftext[:1000] if hasattr(submission, 'selftext') else submission.text[:1000]}
ENGAGEMENT: {submission.score} upvotes, {submission.num_comments if hasattr(submission, 'num_comments') else submission.comments_count} comments
AUTHOR: {submission.author}
URL: {submission.permalink}

Provide a complete JSON analysis with this structure:
{{
    "app_idea": {{
        "title": "App Title (Title Case)",
        "app_concept": "Detailed app concept description (10-500 chars)",
        "problem_statement": "Specific problem this solves (10-1000 chars)",
        "core_functions": ["feature1", "feature2", "feature3"],
        "target_audience": "Specific target audience description (10-500 chars)"
    }},
    "metrics": {{
        "market_demand": <0-100>,
        "pain_intensity": <0-100>,
        "monetization_potential": <0-100>,
        "competition_level": <0-100>,  // Higher = less competition
        "technical_feasibility": <0-100>
    }},
    "pain_points": ["pain point 1", "pain point 2", "pain point 3"],
    "opportunity_summary": "Brief summary of the opportunity (50-500 chars)",
    "final_score": <0-100>,
    "wtp_score": <0-100>,
    "confidence_score": <0-100>,
    "trust_level": "LOW|MEDIUM|HIGH",
    "content_quality_score": <0-100>,
    "is_spam": false,
    "spam_indicators": []
}}"""
