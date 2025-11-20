#!/usr/bin/env python3
"""
Enhanced LLM-Powered App Profile Generator with Cost Tracking
Uses LiteLLM for unified API and comprehensive cost/token tracking
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import litellm
from json_repair import repair_json

# AgentOps for manual instrumentation
try:
    import agentops
    from agentops import tool, trace
    AGENTOPS_AVAILABLE = True
except ImportError:
    AGENTOPS_AVAILABLE = False

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import project settings and HTTP client configuration
import config.settings as settings

# Import triggers auto-configuration of HTTP clients
import core.http_client_config  # noqa: F401


class EnhancedLLMProfiler:
    """AI-powered app profile generation with comprehensive cost tracking"""

    def __init__(self):
        # Use centralized configuration
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.OPENROUTER_MODEL

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

        # Configure LiteLLM settings with managed HTTP client
        litellm.api_base = "https://openrouter.ai/api/v1"
        litellm.set_verbose = False  # Set to True for debugging

        # HTTP client is configured globally via core.http_client_config
        # No need to set it per-instance

        # List of generic app names to avoid (same as original)
        self.generic_names = {
            'taskflow', 'smartflow', 'protool', 'workflow', 'taskmaster', 'smartapp',
            'taskapp', 'flowapp', 'workapp', 'proapp', 'smarttask', 'taskpro',
            'flowpro', 'workpro', 'efficiencyapp', 'productivityapp', 'taskmanager'
        }

    @trace(name="ai_profile_generation")
    def generate_app_profile_with_costs(
        self,
        text: str,
        title: str,
        subreddit: str,
        score: float,
        agno_analysis: dict[str, Any] | None = None
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        Generate complete app profile with detailed cost tracking.

        Args:
            text: Reddit post text content
            title: Reddit post title
            subreddit: Subreddit name
            score: Opportunity score (0-100)
            agno_analysis: Optional Agno monetization analysis evidence

        Returns:
            Tuple of (profile_data, cost_tracking_data)
        """
        prompt = self._build_prompt(text, title, subreddit, score, agno_analysis)

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

            # Validate evidence alignment if Agno analysis provided
            evidence_validation = None
            if agno_analysis:
                evidence_validation = self._validate_evidence_alignment(profile, agno_analysis)
                profile["evidence_validation"] = evidence_validation

            # Extract cost and usage data
            cost_data = self._extract_cost_data(response, latency, prompt)

            # Add cost tracking to profile
            profile["cost_tracking"] = cost_data

            # Add evidence metadata
            if agno_analysis:
                profile["evidence_based"] = True
                profile["agno_evidence"] = {
                    "willingness_to_pay_score": agno_analysis.get("willingness_to_pay_score", 0),
                    "customer_segment": agno_analysis.get("customer_segment", "Unknown"),
                    "payment_sentiment": agno_analysis.get("sentiment_toward_payment", "Neutral"),
                    "urgency_level": agno_analysis.get("urgency_level", "Low"),
                    "price_points": agno_analysis.get("mentioned_price_points", []),
                    "confidence": agno_analysis.get("confidence", 0)
                }
            else:
                profile["evidence_based"] = False

            # Generate ai_profile field containing comprehensive analysis
            profile["ai_profile"] = {
                "analysis_summary": {
                    "app_name": profile.get("app_name", "Unknown"),
                    "app_category": profile.get("app_category", "Unknown"),
                    "target_profession": profile.get("profession", "Unknown"),
                    "core_problem_solved": profile.get("problem_description", "Unknown"),
                    "unique_value_prop": profile.get("value_proposition", "Unknown"),
                    "primary_target_user": profile.get("target_user", "Unknown"),
                    "monetization_approach": profile.get("monetization_model", "Unknown"),
                },
                "technical_feasibility": {
                    "estimated_complexity": "Medium" if len(profile.get("core_functions", [])) > 1 else "Low",
                    "core_function_count": len(profile.get("core_functions", [])),
                    "functions": profile.get("core_functions", []),
                    "target_problems": profile.get("core_problems", []),
                },
                "market_analysis": {
                    "target_market_segment": profile.get("profession", "Unknown"),
                    "app_category": profile.get("app_category", "Unknown"),
                    "evidence_based": profile.get("evidence_based", False),
                    "opportunity_score": score,  # Input opportunity score
                },
                "generation_metadata": {
                    "model_used": self.model,
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "evidence_available": bool(agno_analysis),
                    "cost_tracking": cost_data
                }
            }

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
                "app_category": "Unknown",
                "profession": "Unknown",
                "core_problems": ["Manual analysis required"],
                "ai_profile": {
                    "analysis_summary": {"error": str(e)},
                    "technical_feasibility": {"error": "Analysis failed"},
                    "market_analysis": {"error": "Analysis failed"},
                    "generation_metadata": {"error": str(e)}
                },
                "cost_tracking": error_cost_data
            }

            return error_profile, error_cost_data

    def _extract_cost_data(self, response, latency: float, prompt: str) -> dict[str, Any]:
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
        score: float,
        agno_analysis: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Backward compatibility method - returns only profile data.
        Cost data is embedded in profile["cost_tracking"]

        Args:
            text: Reddit post text content
            title: Reddit post title
            subreddit: Subreddit name
            score: Opportunity score (0-100)
            agno_analysis: Optional Agno monetization analysis evidence
        """
        profile, _ = self.generate_app_profile_with_costs(text, title, subreddit, score, agno_analysis)
        return profile

    def generate_app_profile_with_evidence(
        self,
        text: str,
        title: str,
        subreddit: str,
        score: float,
        agno_analysis: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Generate evidence-based AI profile using Agno analysis results.

        This method provides a dedicated interface for evidence-based profiling,
        ensuring that Agno analysis results are properly integrated into the AI profile.

        Args:
            text: Reddit post text content
            title: Reddit post title
            subreddit: Subreddit name
            score: Opportunity score (0-100)
            agno_analysis: Agno monetization analysis results with evidence

        Returns:
            Complete profile data with evidence validation and alignment scoring
        """
        if not agno_analysis:
            # Fallback to standard profiling if no evidence provided
            print("  ⚠️  No Agno evidence provided - using standard profiling")
            return self.generate_app_profile(text, title, subreddit, score)

        # Generate profile with evidence integration
        profile, cost_data = self.generate_app_profile_with_costs(
            text=text,
            title=title,
            subreddit=subreddit,
            score=score,
            agno_analysis=agno_analysis
        )

        # Ensure evidence validation is prominently featured
        if "evidence_validation" not in profile:
            # Generate validation if missing
            validation = self._validate_evidence_alignment(profile, agno_analysis)
            profile["evidence_validation"] = validation

        # Add evidence summary metrics
        profile["evidence_summary"] = {
            "evidence_based": True,
            "agno_confidence": agno_analysis.get("confidence", 0),
            "evidence_sources": [
                "willingness_to_pay",
                "customer_segment",
                "payment_sentiment",
                "urgency_level",
                "price_points",
                "payment_behavior"
            ],
            "validation_score": profile["evidence_validation"].get("alignment_score", 0),
            "validation_status": profile["evidence_validation"].get("overall_status", "unknown")
        }

        return profile

    def _build_prompt(self, text: str, title: str, subreddit: str, score: float, agno_analysis: dict[str, Any] | None = None) -> str:
        """Build structured prompt for LLM with optional evidence integration"""

        # Base prompt structure
        base_prompt = f"""You are an expert product analyst. Analyze this Reddit post and generate a complete app profile.

**Post Details:**
- Title: {title}
- Subreddit: r/{subreddit}
- Opportunity Score: {score}/100 (high potential)

**Post Content:**
{text[:1000]}"""

        # Add evidence section if Agno analysis provided
        if agno_analysis:
            evidence_section = f"""

**EVIDENCE-BASED ANALYSIS DATA:**
The following monetization analysis has been extracted from the same Reddit post.
USE THIS EVIDENCE to inform your app profile generation:

• **Willingness to Pay Score:** {agno_analysis.get('willingness_to_pay_score', 'N/A')}/100
• **Customer Segment:** {agno_analysis.get('customer_segment', 'Unknown')}
• **Payment Sentiment:** {agno_analysis.get('sentiment_toward_payment', 'Neutral')}
• **Urgency Level:** {agno_analysis.get('urgency_level', 'Low')}
• **Price Points Mentioned:** {', '.join(agno_analysis.get('mentioned_price_points', ['None']))}
• **Existing Payment Behavior:** {agno_analysis.get('existing_payment_behavior', 'Not specified')}
• **Payment Friction Indicators:** {', '.join(agno_analysis.get('payment_friction_indicators', ['None']))}
• **Evidence Confidence:** {agno_analysis.get('confidence', 'N/A')}

**EVIDENCE-BASED REQUIREMENTS:**
1. **ALIGNMENT REQUIRED:** Your app profile MUST align with the evidence above
2. **Market Segment Match:** Target user should match the identified customer segment ({agno_analysis.get('customer_segment', 'Unknown')})
3. **Monetization Consistency:** Pricing model must be consistent with willingness to pay score ({agno_analysis.get('willingness_to_pay_score', 'N/A')}/100) and payment sentiment ({agno_analysis.get('sentiment_toward_payment', 'Neutral')})
4. **Price Point Integration:** If specific price points are mentioned ({', '.join(agno_analysis.get('mentioned_price_points', ['None']))}), reference them in your monetization model
5. **Urgency Consideration:** Consider the urgency level ({agno_analysis.get('urgency_level', 'Low')}) in your value proposition
6. **Friction Awareness:** Address payment friction indicators ({', '.join(agno_analysis.get('payment_friction_indicators', ['None']))}) if present

**EVIDENCE VALIDATION:**
Your app profile will be validated for alignment with this evidence. Ensure:
- Target user matches the identified segment
- Monetization model aligns with payment sentiment and willingness to pay
- Price considerations reflect mentioned price points
- Value proposition addresses the urgency level

"""
            full_prompt = base_prompt + evidence_section
        else:
            # Add note about evidence availability
            full_prompt = base_prompt + """

**Note:** No monetization evidence analysis available. Generate app profile based on text analysis alone.

"""

        # Add the standard prompt instructions for both cases
        standard_instructions = """
Generate a JSON response with exactly these fields:

1. **app_name** (1-3 words): UNIQUE, problem-specific name that directly reflects the core solution. Use descriptive naming patterns like: [Problem] + [Solution Type] or [Action] + [Benefit]. Examples: "TimeLens", "AutomateFlow", "FocusTrack", "PriorityGrid", "WorkflowSync". AVOID generic names like "TaskFlow", "SmartApp", "ProTool" that could apply to any problem.

2. **problem_description** (1-2 sentences): The core problem or pain point expressed
3. **app_concept** (2-3 sentences): Specific app idea that solves this problem
4. **core_functions** (array of 1-3 strings): Focused functions with CLEAR BOUNDARIES that solve specific, non-overlapping aspects of the problem. Each function should have: (1) Specific problem it solves, (2) Clear scope boundaries, (3) One measurable outcome. Functions should work together logically (analyze -> build -> monitor) with no overlap.
5. **value_proposition** (1-2 sentences): Why users need this, what benefit they get
6. **target_user** (1 sentence): Primary user persona
7. **monetization_model** (1 sentence): Recommended revenue model with pricing

8. **app_category** (1 word): Choose ONE category from: Productivity, Finance, Health, Education, Communication, Entertainment, Business, Social, Travel, Shopping, Utilities, Development, Design, Marketing, Analytics, Security, Lifestyle, Food, Sports, News, Weather, Navigation, Photography, Music, Video, Gaming, Books, Reference, Medical, Fitness

9. **profession** (1-2 words): Primary profession or job role that would use this app. Examples: "Software Developer", "Marketing Manager", "Freelancer", "Small Business Owner", "Student", "Teacher", "Healthcare Worker", "Sales Representative", "Project Manager", "Designer", "Consultant", "Entrepreneur", "Financial Analyst", "HR Manager"

10. **core_problems** (array of 1-3 strings): Specific problems this app solves for the target profession. Each problem should be actionable and measurable. Examples: ["Time tracking across multiple projects", "Invoice management and payment reminders", "Client communication and collaboration"]

**Critical Rules:**
- Be SPECIFIC. No generic functions like "Core function 1" or "User management"
- Extract REAL problems from the text, do not invent them
- App concept must directly solve the stated problem
- Functions must be actionable and implementable
- Keep all fields concise
- **APP NAME MUST BE UNIQUE AND PROBLEM-SPECIFIC**: The name should immediately tell users what problem it solves. Generic names like "TaskFlow", "SmartFlow", "ProTool" are unacceptable. Use descriptive combinations like: TimeFocus, WorkflowWizard, PriorityMaster, AutomationHub, ScheduleSync.

**Function Count Guidelines:**

Determine the optimal number of core functions (1-3) based on the problem's actual complexity and user workflow requirements.

**DECISION FRAMEWORK:**

1. **Identify Distinct User Workflows**
   - Each workflow should have a clear trigger, input, process, and outcome
   - Workflows are distinct if they serve different user goals or require different contexts

2. **Apply the Separation Test**
   - Could these workflows run independently without each other?
   - Do they require different data inputs or user interfaces?
   - Would a user benefit from one without needing the others?

3. **Apply the Combination Test**
   - Do these workflows need to happen in sequence?
   - Do they share the same data and context?
   - Would splitting them create unnecessary complexity for users?

**DECISION CRITERIA:**

**Choose 1 Function When:**
- The problem has a single, focused user goal
- Related actions naturally flow in one continuous workflow
- All features serve the same primary outcome

**Choose 2 Functions When:**
- The problem involves two distinct user goals or workflows
- Functions serve complementary but separable purposes
- Each function could independently provide value

**Choose 3 Functions When:**
- The problem spans multiple independent domains
- Each function addresses a different aspect of the problem
- Functions work together as an ecosystem but remain self-contained

**CONCRETE EXAMPLES:**

**1-Function Apps (~60% of problems):**
- Problem: "I forget to water my plants" → Function: "Send watering reminders based on plant type"
- Problem: "I can't track my daily calories" → Function: "Log food and show calorie total"
- Problem: "I lose track of parking spot" → Function: "Save and retrieve parking location"

**2-Function Apps (~30% of problems):**
- Problem: "I forget bills AND want to see spending patterns" → Functions: "1) Send bill reminders, 2) Visualize spending trends"
- Problem: "I can't find recipes for ingredients I have" → Functions: "1) Scan/input ingredients, 2) Match to recipes"
- Problem: "I want to save money but don't know where I overspend" → Functions: "1) Categorize transactions, 2) Generate savings recommendations"

**3-Function Apps (~10% of problems):**
- Problem: "Roommates argue about chores, don't know who did what, and dispute fairness" → Functions: "1) Assign chores, 2) Track completion, 3) Calculate equity scores"
- Problem: "Remote teams struggle with timezone coordination, availability tracking, and meeting scheduling" → Functions: "1) Display team timezones, 2) Sync availability calendars, 3) Suggest optimal meeting times"

**VALIDATION CHECKLIST:**

Before finalizing your function count, ask:
- ✓ Does each function solve a specific, non-overlapping problem?
- ✓ Can I clearly explain when a user would use each function separately?
- ✓ Would combining functions create confusion or reduce clarity?
- ✓ Would separating functions make the app unnecessarily complex?

**CRITICAL RULES:**
- Each function must have clear boundaries and a specific problem it solves
- Functions should have one measurable outcome
- Helper features, settings, or view options DO NOT count as separate functions
- The number should reflect the problem's natural structure, not arbitrary limits

Return ONLY valid JSON, no markdown, no explanation."""

        return full_prompt + standard_instructions

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
                "monetization_model",
                "app_category",
                "profession",
                "core_problems"
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

    @tool(name="evidence_alignment_validation")
    def _validate_evidence_alignment(self, profile: dict[str, Any], agno_analysis: dict[str, Any]) -> dict[str, Any]:
        """
        Comprehensive validation that the AI profile aligns with Agno evidence.

        Returns validation results with detailed alignment scoring and discrepancy detection.
        """
        validation_results = {
            "alignment_score": 0.0,
            "validations": {},
            "discrepancies": [],
            "warnings": [],
            "overall_status": "pending",
            "evidence_strength": "medium"
        }

        # Extract key evidence from Agno analysis
        wtp_score = agno_analysis.get("willingness_to_pay_score", 50)
        customer_segment = agno_analysis.get("customer_segment", "Unknown")
        payment_sentiment = agno_analysis.get("sentiment_toward_payment", "Neutral")
        urgency_level = agno_analysis.get("urgency_level", "Low")
        price_points = agno_analysis.get("mentioned_price_points", [])
        confidence = agno_analysis.get("confidence", 0.7)

        # Determine evidence strength based on confidence
        if confidence >= 0.8:
            validation_results["evidence_strength"] = "high"
        elif confidence >= 0.6:
            validation_results["evidence_strength"] = "medium"
        else:
            validation_results["evidence_strength"] = "low"

        validation_score = 0.0
        weighted_checks = 0

        # 1. Customer Segment Alignment (Weight: 1.0)
        weight = 1.0
        weighted_checks += weight
        target_user = profile.get("target_user", "").lower()
        segment_aligned = False
        segment_score = 0.0

        if customer_segment == "B2B":
            b2b_keywords = ["business", "team", "company", "organization", "professional", "enterprise", "startup", "small business"]
            if any(word in target_user for word in b2b_keywords):
                segment_aligned = True
                segment_score = 1.0
        elif customer_segment == "B2C":
            b2c_keywords = ["individual", "personal", "user", "consumer", "person", "student", "family"]
            if any(word in target_user for word in b2c_keywords):
                segment_aligned = True
                segment_score = 1.0
        elif customer_segment == "Mixed":
            mixed_keywords = ["user", "customer", "client", "people", "organization"]
            if any(word in target_user for word in mixed_keywords):
                segment_aligned = True
                segment_score = 0.8  # Slightly lower for mixed segments
        else:
            # Unknown segment - give partial credit
            segment_score = 0.5
            segment_aligned = True

        validation_score += segment_score * weight

        validation_results["validations"]["customer_segment_alignment"] = {
            "evidence": customer_segment,
            "profile_target": target_user,
            "aligned": segment_aligned,
            "score": segment_score,
            "weight": weight
        }

        if not segment_aligned and customer_segment != "Unknown":
            validation_results["discrepancies"].append(
                f"Customer segment mismatch: Evidence suggests {customer_segment}, profile targets '{target_user}'"
            )

        # 2. Monetization Model Alignment with WTP (Weight: 1.5)
        weight = 1.5
        weighted_checks += weight
        monetization_model = profile.get("monetization_model", "").lower()
        payment_aligned = False
        payment_score = 0.0

        if wtp_score >= 75:  # High willingness to pay
            high_wtp_keywords = ["subscription", "premium", "paid", "pro", "enterprise", "business plan"]
            if any(word in monetization_model for word in high_wtp_keywords):
                payment_aligned = True
                payment_score = 1.0
        elif wtp_score >= 50:  # Medium willingness to pay
            medium_wtp_keywords = ["freemium", "trial", "tiered", "basic", "plus", "standard"]
            if any(word in monetization_model for word in medium_wtp_keywords):
                payment_aligned = True
                payment_score = 0.8
        else:  # Low willingness to pay
            low_wtp_keywords = ["free", "ad-supported", "basic", "community", "open source"]
            if any(word in monetization_model for word in low_wtp_keywords):
                payment_aligned = True
                payment_score = 1.0

        validation_score += payment_score * weight

        validation_results["validations"]["monetization_alignment"] = {
            "wtp_score": wtp_score,
            "monetization_model": monetization_model,
            "aligned": payment_aligned,
            "score": payment_score,
            "weight": weight,
            "wtp_category": "high" if wtp_score >= 75 else "medium" if wtp_score >= 50 else "low"
        }

        if not payment_aligned:
            validation_results["discrepancies"].append(
                f"Monetization model may not match willingness to pay (WTP: {wtp_score}/100, Model: '{monetization_model}')"
            )

        # 3. Payment Sentiment Alignment (Weight: 1.0)
        weight = 1.0
        weighted_checks += weight
        sentiment_aligned = True
        sentiment_score = 0.8  # Default to good alignment

        if payment_sentiment == "Negative":
            if "free" not in monetization_model and "basic" not in monetization_model:
                sentiment_aligned = False
                sentiment_score = 0.2
                validation_results["discrepancies"].append(
                    "Negative payment sentiment detected but profile doesn't emphasize free/accessible pricing"
                )
        elif payment_sentiment == "Positive":
            if monetization_model.count("free") > 1 and "premium" not in monetization_model:
                sentiment_aligned = False
                sentiment_score = 0.3
                validation_results["warnings"].append(
                    "Positive payment sentiment but profile suggests free-only model (might miss revenue opportunity)"
                )

        validation_score += sentiment_score * weight

        validation_results["validations"]["payment_sentiment_alignment"] = {
            "evidence_sentiment": payment_sentiment,
            "monetization_model": monetization_model,
            "aligned": sentiment_aligned,
            "score": sentiment_score,
            "weight": weight
        }

        # 4. Urgency Consideration (Weight: 0.8)
        weight = 0.8
        weighted_checks += weight
        value_prop = profile.get("value_proposition", "").lower()
        urgency_considered = False
        urgency_score = 0.6  # Default score

        if urgency_level in ["Critical", "High"]:
            urgency_keywords = ["immediate", "quickly", "fast", "urgent", "now", "asap", "instant", "real-time"]
            if any(word in value_prop for word in urgency_keywords):
                urgency_considered = True
                urgency_score = 1.0
            else:
                validation_results["warnings"].append(
                    f"High urgency detected ({urgency_level}) but value proposition doesn't emphasize speed"
                )
        elif urgency_level == "Medium":
            medium_urgency_keywords = ["save", "improve", "better", "efficient", "streamline", "optimize"]
            if any(word in value_prop for word in medium_urgency_keywords):
                urgency_considered = True
                urgency_score = 0.9
        else:  # Low urgency - no penalty
            urgency_score = 0.8
            urgency_considered = True

        validation_score += urgency_score * weight

        validation_results["validations"]["urgency_consideration"] = {
            "evidence_urgency": urgency_level,
            "value_proposition": value_prop[:100] + "..." if len(value_prop) > 100 else value_prop,
            "considered": urgency_considered,
            "score": urgency_score,
            "weight": weight
        }

        # 5. Price Point Integration (Weight: 1.2)
        weight = 1.2
        weighted_checks += weight
        price_integration = True
        price_score = 1.0

        if price_points:
            # Check if profile mentions pricing that aligns with mentioned points
            profile_mentioned_pricing = any(
                price_point.lower() in monetization_model or
                price_point.lower() in value_prop
                for price_point in price_points
            )

            if not profile_mentioned_pricing:
                price_integration = False
                price_score = 0.4
                validation_results["discrepancies"].append(
                    f"Price points mentioned in evidence ({', '.join(price_points)}) but not reflected in profile"
                )
            else:
                # Bonus points for explicit price integration
                price_score = 1.0

        validation_score += price_score * weight

        validation_results["validations"]["price_point_integration"] = {
            "evidence_price_points": price_points,
            "profile_mentions_pricing": price_integration,
            "integrated": price_integration,
            "score": price_score,
            "weight": weight
        }

        # Calculate overall alignment score (weighted)
        validation_results["alignment_score"] = (validation_score / weighted_checks) * 100 if weighted_checks > 0 else 0

        # Apply confidence-based adjustment
        if validation_results["evidence_strength"] == "low":
            validation_results["alignment_score"] *= 0.9  # Reduce score for low-confidence evidence

        # Determine overall status with more granular levels
        alignment_score = validation_results["alignment_score"]
        if alignment_score >= 90:
            validation_results["overall_status"] = "excellent_alignment"
        elif alignment_score >= 80:
            validation_results["overall_status"] = "strong_alignment"
        elif alignment_score >= 70:
            validation_results["overall_status"] = "good_alignment"
        elif alignment_score >= 50:
            validation_results["overall_status"] = "partial_alignment"
        elif alignment_score >= 30:
            validation_results["overall_status"] = "weak_alignment"
        else:
            validation_results["overall_status"] = "poor_alignment"

        # Add confidence metrics
        validation_results["confidence_metrics"] = {
            "evidence_confidence": confidence,
            "evidence_strength": validation_results["evidence_strength"],
            "validation_weight": weighted_checks,
            "discrepancy_count": len(validation_results["discrepancies"]),
            "warning_count": len(validation_results["warnings"])
        }

        return validation_results

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

    def get_cost_summary(self, profiles: list[dict[str, Any]]) -> dict[str, Any]:
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
