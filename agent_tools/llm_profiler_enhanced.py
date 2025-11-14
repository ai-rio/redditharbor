#!/usr/bin/env python3
"""
Enhanced LLM-Powered App Profile Generator with Cost Tracking
Uses LiteLLM for unified API and comprehensive cost/token tracking
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import litellm
from json_repair import repair_json

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import project settings
import config.settings as settings


class EnhancedLLMProfiler:
    """AI-powered app profile generation with comprehensive cost tracking"""

    def __init__(self):
        # Configure LiteLLM with OpenRouter
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-haiku-4.5")

        # Model cost configuration (per 1M tokens)
        self.model_costs = {
            "anthropic/claude-haiku-4.5": {
                "input_cost": 1.0,    # $1.00 per 1M input tokens
                "output_cost": 5.0    # $5.00 per 1M output tokens
            },
            "anthropic/claude-3.5-sonnet": {
                "input_cost": 3.0,    # $3.00 per 1M input tokens
                "output_cost": 15.0   # $15.00 per 1M output tokens
            },
            "openai/gpt-4o-mini": {
                "input_cost": 0.15,   # $0.15 per 1M input tokens
                "output_cost": 0.60   # $0.60 per 1M output tokens
            }
        }

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")

        # Configure LiteLLM settings
        litellm.api_base = "https://openrouter.ai/api/v1"
        litellm.set_verbose = False  # Set to True for debugging

        # List of generic app names to avoid (same as original)
        self.generic_names = {
            'taskflow', 'smartflow', 'protool', 'workflow', 'taskmaster', 'smartapp',
            'taskapp', 'flowapp', 'workapp', 'proapp', 'smarttask', 'taskpro',
            'flowpro', 'workpro', 'efficiencyapp', 'productivityapp', 'taskmanager'
        }

    def generate_app_profile_with_costs(
        self,
        text: str,
        title: str,
        subreddit: str,
        score: float
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Generate complete app profile with detailed cost tracking.

        Returns:
            Tuple of (profile_data, cost_tracking_data)
        """
        prompt = self._build_prompt(text, title, subreddit, score)

        # Track start time for latency measurement
        start_time = time.time()

        try:
            # Use LiteLLM for unified API call
            response = litellm.completion(
                model=f"openrouter/{self.model}",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800,
                timeout=30
            )

            # Calculate latency
            latency = time.time() - start_time

            # Parse profile
            profile = self._parse_response(response.choices[0].message.content, title, text)

            # Extract cost and usage data
            cost_data = self._extract_cost_data(response, latency, prompt)

            # Add cost tracking to profile
            profile["cost_tracking"] = cost_data

            return profile, cost_data

        except Exception as e:
            # Return error profile with minimal cost tracking
            error_cost_data = {
                "model_used": self.model,
                "error": str(e),
                "latency_seconds": time.time() - start_time,
                "cost_usd": 0.0,
                "tokens": 0,
                "timestamp": datetime.utcnow().isoformat()
            }

            error_profile = {
                "error": str(e),
                "problem_description": f"Error analyzing: {str(e)[:100]}",
                "app_concept": "Analysis failed - manual review required",
                "core_functions": ["Manual analysis needed"],
                "value_proposition": "Unable to generate value proposition",
                "target_user": "Unknown",
                "monetization_model": "Requires manual analysis",
                "cost_tracking": error_cost_data
            }

            return error_profile, error_cost_data

    def _extract_cost_data(self, response, latency: float, prompt: str) -> Dict[str, Any]:
        """Extract comprehensive cost and usage data from LiteLLM response"""

        # Get token usage from response
        usage = response.usage

        # Calculate costs using model-specific pricing
        model_pricing = self.model_costs.get(self.model, {
            "input_cost": 1.0,  # Default fallback
            "output_cost": 5.0
        })

        input_cost = (usage.prompt_tokens / 1_000_000) * model_pricing["input_cost"]
        output_cost = (usage.completion_tokens / 1_000_000) * model_pricing["output_cost"]
        total_cost = input_cost + output_cost

        # Get model info from response
        model_used = response.model.replace("openrouter/", "")  # Remove prefix

        return {
            "model_used": model_used,
            "provider": "openrouter",
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "input_cost_usd": round(input_cost, 6),
            "output_cost_usd": round(output_cost, 6),
            "total_cost_usd": round(total_cost, 6),
            "latency_seconds": round(latency, 3),
            "prompt_length_chars": len(prompt),
            "timestamp": datetime.utcnow().isoformat(),
            "model_pricing_per_m_tokens": {
                "input": model_pricing["input_cost"],
                "output": model_pricing["output_cost"]
            }
        }

    def generate_app_profile(
        self,
        text: str,
        title: str,
        subreddit: str,
        score: float
    ) -> dict[str, Any]:
        """
        Backward compatibility method - returns only profile data.
        Cost data is embedded in profile["cost_tracking"]
        """
        profile, _ = self.generate_app_profile_with_costs(text, title, subreddit, score)
        return profile

    def _build_prompt(self, text: str, title: str, subreddit: str, score: float) -> str:
        """Build structured prompt for LLM (same as original)"""
        return f"""You are an expert product analyst. Analyze this Reddit post and generate a complete app profile.

**Post Details:**
- Title: {title}
- Subreddit: r/{subreddit}
- Opportunity Score: {score}/100 (high potential)

**Post Content:**
{text[:1000]}

Generate a JSON response with exactly these fields:

1. **app_name** (1-3 words): UNIQUE, problem-specific name that directly reflects the core solution. Use descriptive naming patterns like: [Problem] + [Solution Type] or [Action] + [Benefit]. Examples: "TimeLens", "AutomateFlow", "FocusTrack", "PriorityGrid", "WorkflowSync". AVOID generic names like "TaskFlow", "SmartApp", "ProTool" that could apply to any problem.

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
- **APP NAME MUST BE UNIQUE AND PROBLEM-SPECIFIC**: The name should immediately tell users what problem it solves. Generic names like "TaskFlow", "SmartFlow", "ProTool" are unacceptable. Use descriptive combinations like: TimeFocus, WorkflowWizard, PriorityMaster, AutomationHub, ScheduleSync.

**Function Count Guidelines:**

START WITH 1 FUNCTION - only add more if absolutely necessary.

**DECISION FRAMEWORK:**
1. Count the number of DISTINCT user actions needed to solve the problem
2. If related actions can be combined into one workflow → 1 function
3. If actions require completely different interfaces/inputs → consider 2 functions
4. Only use 3 functions if there are truly independent problem domains

**CONCRETE EXAMPLES:**

1-Function Apps (PREFERRED - aim for this):
- Problem: "I forget to water my plants" → Function: "Send watering reminders based on plant type"
- Problem: "I can't track my daily calories" → Function: "Log food and show calorie total"
- Problem: "I lose track of parking spot" → Function: "Save and retrieve parking location"
- Problem: "I overspend on subscriptions" → Function: "Track recurring charges and show monthly total"

2-Function Apps (only if problem has TWO distinct needs):
- Problem: "I forget bills AND want to see spending patterns" → Functions: "1) Send bill reminders, 2) Visualize spending trends"
- Problem: "I can't find recipes for ingredients I have" → Functions: "1) Scan/input ingredients, 2) Match to recipes"

3-Function Apps (RARE - only for genuinely complex problems):
- Problem: "Roommates argue about chores, don't know who did what, and dispute fairness" → Functions: "1) Assign chores, 2) Track completion, 3) Calculate equity scores"

**CRITICAL RULES:**
- If you're tempted to add a 2nd function, ask: "Could this be a feature of the 1st function instead?"
- If you're considering 3 functions, ask: "Are we solving ONE problem or multiple separate problems?"
- Default to 1 function unless you can clearly justify why 2+ are essential
- Helper features, settings, or view options DO NOT count as separate functions

Return ONLY valid JSON, no markdown, no explanation."""

    def _parse_response(self, response: str, title: str, text: str) -> dict[str, Any]:
        """Parse LLM response into structured profile (same as original)"""
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
            # Use json_repair to fix malformed JSON from LLMs
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

            # Validate and improve app name uniqueness
            profile = self._validate_and_improve_app_name(profile, title, text)

            return profile

        except json.JSONDecodeError as e:
            # Try to repair malformed JSON using json_repair
            try:
                repaired_json = repair_json(response)
                profile = json.loads(repaired_json)
            except Exception:
                raise Exception(f"Failed to parse LLM response as JSON: {e}")
        except ValueError as e:
            raise Exception(f"Invalid profile structure: {e}")

    def _validate_and_improve_app_name(self, profile: dict[str, Any], title: str, text: str) -> dict[str, Any]:
        """Validate app name for uniqueness and problem specificity (same as original)"""
        app_name = profile.get("app_name", "").lower().replace(" ", "")

        # Check if it's a generic name
        if app_name in self.generic_names or len(app_name) < 4:
            # Generate a descriptive name based on the problem
            problem_keywords = self._extract_problem_keywords(title, text)
            solution_type = self._identify_solution_type(profile.get("app_concept", ""))

            # Create unique name
            if problem_keywords and solution_type:
                new_name = f"{problem_keywords[0]}{solution_type}"
            elif problem_keywords:
                new_name = f"{problem_keywords[0]}Hub"
            else:
                new_name = "SmartFlow"

            profile["app_name"] = new_name
            print(f"  🔄 Improved generic app name to: {new_name}")

        return profile

    def _extract_problem_keywords(self, title: str, text: str) -> list[str]:
        """Extract meaningful keywords related to the problem domain (same as original)"""
        problem_words = []

        # Common problem domains and their keywords
        domain_keywords = {
            'time': ['time', 'schedule', 'deadline', 'punctual', 'hours'],
            'task': ['task', 'todo', 'project', 'work', 'activity'],
            'focus': ['focus', 'concentrate', 'distraction', 'attention'],
            'automate': ['automation', 'repetitive', 'manual', 'workflow'],
            'priority': ['priority', 'urgent', 'important', 'ranking'],
            'track': ['track', 'monitor', 'measure', 'progress'],
            'organize': ['organize', 'manage', 'coordinate', 'structure']
        }

        combined_text = (title + " " + text[:200]).lower()

        for domain, keywords in domain_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                problem_words.append(domain.capitalize())

        return problem_words[:2]  # Return top 2 relevant domains

    def _identify_solution_type(self, app_concept: str) -> str:
        """Identify the type of solution based on the app concept (same as original)"""
        concept_lower = app_concept.lower()

        if any(word in concept_lower for word in ['track', 'monitor', 'measure']):
            return 'Track'
        elif any(word in concept_lower for word in ['automate', 'automatic', 'workflow']):
            return 'Flow'
        elif any(word in concept_lower for word in ['organize', 'manage', 'structure']):
            return 'Hub'
        elif any(word in concept_lower for word in ['focus', 'concentrate', 'priority']):
            return 'Focus'
        elif any(word in concept_lower for word in ['time', 'schedule', 'plan']):
            return 'Sync'
        else:
            return 'Pro'

    def get_cost_summary(self, profiles: list[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate cost summary for multiple profiles"""
        if not profiles:
            return {"total_cost": 0.0, "total_tokens": 0, "profile_count": 0}

        total_cost = 0.0
        total_tokens = 0
        model_usage = {}

        for profile in profiles:
            if "cost_tracking" in profile:
                cost_data = profile["cost_tracking"]
                total_cost += cost_data.get("total_cost_usd", 0.0)
                total_tokens += cost_data.get("total_tokens", 0)

                model = cost_data.get("model_used", "unknown")
                if model not in model_usage:
                    model_usage[model] = {"count": 0, "cost": 0.0, "tokens": 0}
                model_usage[model]["count"] += 1
                model_usage[model]["cost"] += cost_data.get("total_cost_usd", 0.0)
                model_usage[model]["tokens"] += cost_data.get("total_tokens", 0)

        return {
            "total_cost_usd": round(total_cost, 6),
            "total_tokens": total_tokens,
            "profile_count": len(profiles),
            "avg_cost_per_profile": round(total_cost / len(profiles), 6) if profiles else 0.0,
            "model_breakdown": model_usage,
            "timestamp": datetime.utcnow().isoformat()
        }


# Example usage
if __name__ == "__main__":
    profiler = EnhancedLLMProfiler()

    test_data = {
        "text": "I'm so frustrated with budgeting apps. They're all too expensive and none of them sync properly with my bank. I just want something simple that works and doesn't cost $15/month. Why is there no good solution for this?",
        "title": "Looking for a better budgeting app",
        "subreddit": "personalfinance",
        "score": 72.5
    }

    print("Generating app profile with cost tracking...")
    profile, cost_data = profiler.generate_app_profile_with_costs(
        text=test_data["text"],
        title=test_data["title"],
        subreddit=test_data["subreddit"],
        score=test_data["score"]
    )

    print("\n=== APP PROFILE ===")
    print(json.dumps(profile, indent=2))

    print("\n=== COST TRACKING ===")
    print(json.dumps(cost_data, indent=2))