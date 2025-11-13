#!/usr/bin/env python3
"""
LLM-Powered App Profile Generator
Uses Claude Haiku via OpenRouter for real AI analysis
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class LLMProfiler:
    """Real AI-powered app profile generation using Claude Haiku via OpenRouter"""

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-haiku-4.5")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")

    def generate_app_profile(
        self,
        text: str,
        title: str,
        subreddit: str,
        score: float
    ) -> dict[str, Any]:
        """
        Generate complete app profile using Claude Haiku.

        Args:
            text: Reddit submission text
            title: Reddit submission title
            subreddit: Source subreddit
            score: Opportunity score (for context)

        Returns:
            Dict with app profile fields or error info
        """
        prompt = self._build_prompt(text, title, subreddit, score)

        try:
            response = self._call_llm(prompt)
            profile = self._parse_response(response)
            return profile

        except Exception as e:
            return {
                "error": str(e),
                "problem_description": f"Error analyzing: {str(e)[:100]}",
                "app_concept": "Analysis failed - manual review required",
                "core_functions": ["Manual analysis needed"],
                "value_proposition": "Unable to generate value proposition",
                "target_user": "Unknown",
                "monetization_model": "Requires manual analysis"
            }

    def _build_prompt(self, text: str, title: str, subreddit: str, score: float) -> str:
        """Build structured prompt for LLM"""
        return f"""You are an expert product analyst. Analyze this Reddit post and generate a complete app profile.

**Post Details:**
- Title: {title}
- Subreddit: r/{subreddit}
- Opportunity Score: {score}/100 (high potential)

**Post Content:**
{text[:1000]}

Generate a JSON response with exactly these fields:

1. **app_name** (1-3 words): Short, catchy name for the app
2. **problem_description** (1-2 sentences): The core problem or pain point expressed
3. **app_concept** (2-3 sentences): Specific app idea that solves this problem
4. **core_functions** (array of 1-3 strings): Focused functions with CLEAR BOUNDARIES that solve specific, non-overlapping aspects of the problem. Each function should have: (1) Specific problem it solves, (2) Clear scope boundaries, (3) One measurable outcome. Functions should work together logically (analyze → build → monitor) with no overlap.
5. **value_proposition** (1-2 sentences): Why users need this, what benefit they get
6. **target_user** (1 sentence): Primary user persona
7. **monetization_model** (1 sentence): Recommended revenue model with pricing

**Critical Rules:**
- Be SPECIFIC. No generic functions like "Core function 1" or "User management"
- Extract REAL problems from the text, don't invent them
- App concept must directly solve the stated problem
- Functions must be actionable and implementable
- Keep all fields concise

**Function Count Guidelines:**
- Choose the MINIMUM number of functions (1-3) that genuinely solve the core problem
- Simple problems (single pain point) → 1 function is ideal
- Moderate problems (related pain points) → 2 functions may be needed
- Complex problems (multiple distinct needs) → 3 functions might be required
- Do NOT artificially inflate or deflate function count - match it to problem complexity
- Quality over quantity: fewer focused functions beat more scattered ones

Return ONLY valid JSON, no markdown, no explanation."""

    def _call_llm(self, prompt: str, max_retries: int = 3) -> str:
        """Call OpenRouter API with retry logic"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/redditharbor",
            "X-Title": "RedditHarbor App Profiler"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,  # Lower temp for consistent output
            "max_tokens": 800,   # Enough for profile, not wasteful
        }

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return content

            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise Exception(f"API call failed after {max_retries} retries: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff

        raise Exception("Unexpected error in API call")

    def _parse_response(self, response: str) -> dict[str, Any]:
        """Parse LLM response into structured profile"""
        # Clean up markdown code blocks if present
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        try:
            profile = json.loads(response)

            # Validate required fields
            required = [
                "app_name",
                "problem_description",
                "app_concept",
                "core_functions",
                "value_proposition",
                "target_user",
                "monetization_model"
            ]

            for field in required:
                if field not in profile:
                    raise ValueError(f"Missing required field: {field}")

            # Validate core_functions is a list
            if not isinstance(profile["core_functions"], list):
                profile["core_functions"] = [str(profile["core_functions"])]

            # Ensure 1-3 functions
            if len(profile["core_functions"]) == 0:
                profile["core_functions"] = ["Function definition needed"]
            elif len(profile["core_functions"]) > 3:
                profile["core_functions"] = profile["core_functions"][:3]

            return profile

        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse LLM response as JSON: {e}")
        except ValueError as e:
            raise Exception(f"Invalid profile structure: {e}")


# Example usage
if __name__ == "__main__":
    profiler = LLMProfiler()

    test_data = {
        "text": "I'm so frustrated with budgeting apps. They're all too expensive and none of them sync properly with my bank. I just want something simple that works and doesn't cost $15/month. Why is there no good solution for this?",
        "title": "Looking for a better budgeting app",
        "subreddit": "personalfinance",
        "score": 72.5
    }

    print("Generating app profile...")
    profile = profiler.generate_app_profile(
        text=test_data["text"],
        title=test_data["title"],
        subreddit=test_data["subreddit"],
        score=test_data["score"]
    )

    print("\n=== APP PROFILE ===")
    print(json.dumps(profile, indent=2))
