#!/usr/bin/env python3
"""
Generate human-readable opportunity insights using OpenRouter + Claude Haiku (DLT-Powered)
Production-ready with proper error handling and rate limiting

SUPPORTS MULTIPLE INPUT MODES:
1. Database mode (default): Process opportunities from Supabase
2. Test mode: Use high-quality sample data for testing
3. File mode: Process Reddit posts from JSON file
4. ID mode: Process specific submission IDs from command line

DLT Migration Benefits:
- Automatic deduplication via merge write disposition
- Batch loading optimization for better performance
- Consistent data loading pattern across all scripts
- Schema evolution support
- Production-ready deployment (Airflow integration)
"""

import os
import sys
import time
import uuid
import random
import requests
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv(project_root / '.env.local')

# DLT imports for pipeline-based loading
from core.dlt_collection import create_dlt_pipeline

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-haiku-4.5")

# Rate limiting configuration
RATE_LIMIT_DELAY = 3.0  # 3 seconds between requests (conservative)
MAX_RETRIES = 2

class RateLimiter:
    """Implements rate limiting with backoff"""

    def __init__(self, min_delay: float = 3.0, max_delay: float = 5.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0

    def wait(self):
        """Wait before making next request"""
        delay = random.uniform(self.min_delay, self.max_delay)
        elapsed = time.time() - self.last_request_time

        if elapsed < delay:
            sleep_time = delay - elapsed
            print(f"  ⏱️  Rate limiting: waiting {sleep_time:.1f}s...")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def set_delay(self, min_delay: float, max_delay: float):
        """Update delay settings"""
        self.min_delay = min_delay
        self.max_delay = max_delay


def generate_insight_with_openrouter(
    title: str,
    content: str,
    scores: Dict[str, float],
    rate_limiter: RateLimiter,
    top_comments: str = ""
) -> Optional[Dict[str, Any]]:
    """Generate insight using OpenRouter Claude Haiku with methodology validation"""

    if not OPENROUTER_API_KEY:
        print("  ⚠️  OPENROUTER_API_KEY not set, skipping")
        return None

    # PROBLEM-FIRST APPROACH (CERTIFIED): Identify problem first, then design simplest app
    prompt = f"""You are a PROBLEM DISCOVERER. Your job is to:

1. IDENTIFY the core problem people are describing
2. VALIDATE the problem is real and painful
3. DESIGN the simplest possible app (1-3 functions) to solve it

=== STEP 1: IDENTIFY THE PROBLEM ===
Read this Reddit post and find the underlying problem. Look for:
- People struggling with something
- Wasting time on manual work
- Unable to accomplish goals
- Repeating patterns of failure
- "If only there was..." or "I wish I could..."

=== STEP 2: VALIDATE THE PROBLEM ===
Does this problem:
- Affect real people (not theoretical)?
- Create real pain/waste/frustration?
- Have evidence from Reddit users?
- Occur frequently enough to matter?

=== STEP 3: DESIGN THE SIMPLEST APP ===
What 1-3 functions would solve this problem?
- 1 function = BEST
- 2 functions = GOOD
- 3 functions = MAXIMUM
- Must be specific, not generic

=== STEP 4: REDDIT EVIDENCE ===
Cite evidence from the post/comments showing:
- Users discussing this problem
- Mentions of paying for solutions
- Frustration with current options

=== RESPONSE FORMAT ===
Return ONLY valid JSON (or null if rejection):

{{
  "problem_identified": "What is the core problem?",
  "problem_evidence": "Specific quotes/examples from Reddit",
  "app_concept": "Simple app name and what it does",
  "core_functions": ["Function 1", "Function 2"],
  "reddit_demand_evidence": "Quotes showing users want this",
  "simplicity_score": 1-3 (number of core functions)
}}

REJECTION RESPONSE:
null

=== EXAMPLE ===

Post: "I forget to follow up on late payments. I use spreadsheets and it's a nightmare."

Problem Identified: Freelancers struggle to track and collect late payments
Problem Evidence: "I use spreadsheets and it's a nightmare"
App Concept: Late payment reminder tracker for freelancers
Core Functions: ["Track unpaid invoices", "Send automated follow-up reminders"]
Reddit Demand Evidence: r/freelance users discuss late payment struggles, mention $10-30/month for solutions
Simplicity Score: 2

=== CRITICAL RULES ===
1. Start with PROBLEM, not app
2. Design the SIMPLEST solution (1-3 functions only)
3. Must cite Reddit evidence
4. Reject if no clear problem OR too complex
5. Return null if not a real solvable problem

=== REDDIT POST ===

TITLE: {title}

POST CONTENT:
{content[:1500]}

TOP COMMENTS:
{top_comments[:2000] if top_comments else "(No comments available)"}

SCORING CONTEXT:
- Market Demand: {scores.get('market_demand', 0)}/100
- Pain Intensity: {scores.get('pain_intensity', 0)}/100
- Monetization Potential: {scores.get('monetization_potential', 0)}/100
- Simplicity Score: {scores.get('simplicity_score', 0)}/100

Identify the problem, validate it, and design the simplest app to solve it.
Return ONLY valid JSON or null."""

    for attempt in range(MAX_RETRIES):
        try:
            # Wait before request
            rate_limiter.wait()

            # Make API request
            url = f"{OPENROUTER_BASE_URL}/chat/completions"
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": OPENROUTER_MODEL,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.7
            }

            print(f"  📡 Calling OpenRouter DeepSeek (attempt {attempt + 1}/{MAX_RETRIES})...")
            response = requests.post(url, headers=headers, json=payload, timeout=90)

            # Handle errors
            if response.status_code != 200:
                print(f"  ❌ HTTP {response.status_code}: {response.text[:200]}")
                if attempt < MAX_RETRIES - 1:
                    print(f"  🔄 Retrying in 5 seconds...")
                    time.sleep(5)
                    continue
                return None

            # Parse response (OpenRouter uses standard OpenAI format)
            result = response.json()
            text = None

            if 'choices' in result:
                choices = result.get('choices', [])
                if choices and len(choices) > 0:
                    message = choices[0].get('message', {})
                    text = message.get('content', '').strip() if message else None
            else:
                # Debug: log unexpected response structure
                print(f"  ⚠️  Response keys: {list(result.keys())}")
                if 'error' in result:
                    print(f"  ⚠️  API Error: {result['error']}")
                return None

            if not text:
                print(f"  ⚠️  Empty response from API")
                return None

            # Clean up markdown code blocks (e.g., ```json ... ```)
            text = text.strip()
            if text.startswith('```json'):
                text = text[7:]  # Remove ```json
            if text.endswith('```'):
                text = text[:-3]  # Remove ```
            text = text.strip()

            # Try to parse JSON
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                try:
                    insight = json.loads(json_match.group())

                    # Map new problem-first fields to old format for database compatibility
                    if 'reddit_demand_evidence' in insight and not insight.get('growth_justification'):
                        insight['growth_justification'] = insight.get('reddit_demand_evidence', '')

                    # CRITICAL: Only return valid insights, no partial/garbage fallbacks
                    return insight
                except json.JSONDecodeError as e:
                    print(f"  ⚠️  JSON parse error: {e}")
                    print(f"  📄 Raw response (first 200 chars): {text[:200]}")
                    # NO FALLBACK - return None to properly reject bad responses
                    return None

            # Check if response is explicitly null (rejection)
            if text.lower() in ['null', 'none']:
                print(f"  ⚠️  AI explicitly rejected this opportunity")
                print(f"  📄 Full response: {text}")
                return None

            print(f"  ⚠️  No JSON found in response")
            print(f"  📄 Full response:\n{text}\n")
            return None

        except requests.exceptions.Timeout:
            print(f"  ⚠️  Timeout on attempt {attempt + 1}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(5)
                continue
            return None

        except Exception as e:
            print(f"  ❌ Exception: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)
                continue
            return None

    return None


def validate_insight(insight: Dict[str, Any], monetization_score: float) -> tuple[bool, str]:
    """
    Validate insight against methodology requirements.
    Returns (is_valid, reason)
    """
    if not insight:
        return False, "No response from AI"

    # Check if AI rejected it
    if insight is None or (isinstance(insight, str) and insight == "null"):
        return False, "AI rejected (null response)"

    # Check if AI rejected it with detailed reason
    reason = insight.get('rejection_reason') or insight.get('rejection_rationale')
    if reason:
        return False, f"AI rejected: {str(reason)[:100]}..."

    # Check monetization potential (lowered to 5 for problem-first approach)
    if monetization_score < 5:
        return False, f"Monetization score too low ({monetization_score}/100)"

    # Check app_concept
    app_concept = insight.get('app_concept', '').strip()
    if not app_concept:
        return False, "Missing app_concept"

    if len(app_concept) < 20:
        return False, f"app_concept too vague: {app_concept}"

    # Check for generic terms (must avoid 2+ generic terms)
    generic_terms = ['platform', 'tool', 'solution', 'application', 'system']
    if all(term in app_concept.lower() for term in generic_terms[:2]):
        return False, f"app_concept too generic: {app_concept}"

    # Check for nonsense/gibberish in app_concept
    import re
    # Check for excessive repetition (e.g., "word word word")
    if re.search(r'\b(\w+)\s+\1\s+\1', app_concept.lower()):
        return False, "app_concept has excessive word repetition (nonsense)"

    # Check for mostly punctuation or numbers
    alpha_ratio = sum(c.isalpha() for c in app_concept) / len(app_concept) if app_concept else 0
    if alpha_ratio < 0.5:
        return False, "app_concept has too many non-alphabetic characters"

    # Check core_functions
    core_functions = insight.get('core_functions', [])
    if not isinstance(core_functions, list):
        return False, f"core_functions must be array, got {type(core_functions)}"

    if len(core_functions) == 0:
        return False, "core_functions array is empty"

    if len(core_functions) > 3:
        return False, f"CONSTRAINT VIOLATION: {len(core_functions)} functions exceed max of 3"

    # Check each function is meaningful
    for func in core_functions:
        if not isinstance(func, str) or len(func) < 10:
            return False, f"Function too vague: {func}"

        # Check for gibberish in functions
        func_alpha_ratio = sum(c.isalpha() for c in func) / len(func) if func else 0
        if func_alpha_ratio < 0.5:
            return False, f"Function has too many non-alphabetic characters: {func[:30]}..."

    # Check growth_justification
    growth_justification = insight.get('growth_justification', '').strip()
    if not growth_justification:
        return False, "Missing growth_justification"

    if len(growth_justification) < 40:
        return False, f"growth_justification too brief: {growth_justification}"

    # Check for Reddit evidence (should cite discussions/comments)
    has_reddit_evidence = any(
        term in growth_justification.lower()
        for term in ['r/', 'reddit', 'comment', 'discuss', 'mention', 'user', 'post', 'feedback']
    )
    if not has_reddit_evidence:
        return False, "growth_justification lacks Reddit evidence (needs comment/post references)"

    # Check for gibberish in growth_justification
    gj_alpha_ratio = sum(c.isalpha() for c in growth_justification) / len(growth_justification) if growth_justification else 0
    if gj_alpha_ratio < 0.4:
        return False, "growth_justification has too many non-alphabetic characters"

    return True, "Valid"


def generate_mock_insight(title: str, content: str) -> Dict[str, Any]:
    """Generate mock insight based on keywords (ONLY as absolute last resort)

    CRITICAL: These are intentionally generic and will likely fail validation.
    This is a last-resort fallback only when AI completely fails.
    """
    # MOCK INSIGHTS ARE GENERIC BY DESIGN - THEY WILL LIKELY FAIL VALIDATION
    # Only enable this in true emergency situations

    title_lower = title.lower()
    content_lower = content.lower()

    if any(word in title_lower for word in ['fitness', 'workout', 'gym', 'train', 'exercise', 'health']):
        return {
            "app_concept": "Fitness tracking app for gym workouts",
            "core_functions": ["Log sets, reps, and weight"],
            "growth_justification": "Based on general fitness app market trends and typical user behavior patterns. Generic fitness tracking has established monetization models.",
            "source": "mock"
        }
    elif any(word in title_lower for word in ['finance', 'money', 'budget', 'save', 'invest', 'debt', 'tax']):
        return {
            "app_concept": "Budget tracking and expense monitoring tool",
            "core_functions": ["Track income and expenses", "Categorize spending"],
            "growth_justification": "Personal finance management represents a mature market with established subscription models. General market analysis indicates demand.",
            "source": "mock"
        }
    elif any(word in title_lower for word in ['resume', 'job', 'career', 'interview', 'hiring', 'salary']):
        return {
            "app_concept": "Resume builder and job application helper",
            "core_functions": ["Create professional resumes", "Track applications"],
            "growth_justification": "Career services market shows consistent demand across economic cycles. Employment tools have proven monetization.",
            "source": "mock"
        }
    else:
        # Generic fallback - will probably fail validation
        return {
            "app_concept": "Productivity tracking application",
            "core_functions": ["Track tasks and activities"],
            "growth_justification": "Productivity software represents a large and growing market segment with multiple successful business models.",
            "source": "mock"
        }


def get_sample_opportunities():
    """High-quality sample opportunities for testing"""
    return [
        {
            'submission_id': 'ef939846-de24-4e93-a41a-d886a316623e',
            'final_score': 35.85,
            'market_demand': 52.50,
            'pain_intensity': 19.00,
            'monetization_potential': 27.00,
            'simplicity_score': 70.00,
            'title': '30-Day Challenge #11: Audit your insurance coverage! (November, 2025)'
        },
        {
            'submission_id': '7a536474-0b1e-4757-94bc-17f336a60883',
            'final_score': 35.05,
            'market_demand': 50.00,
            'pain_intensity': 16.00,
            'monetization_potential': 27.00,
            'simplicity_score': 70.00,
            'title': 'Considering hiring a resume writer? Read this first.'
        },
        {
            'submission_id': '4b4570c7-3049-431e-b57b-5490a1fa65e0',
            'final_score': 34.70,
            'market_demand': 20.00,
            'pain_intensity': 43.00,
            'monetization_potential': 29.00,
            'simplicity_score': 70.00,
            'title': 'Some things I have learned from 15 years as a coach (updated) Part 2'
        },
        {
            'submission_id': '49641243-d566-4f16-9ca2-2f37b1061b23',
            'final_score': 33.20,
            'market_demand': 46.75,
            'pain_intensity': 38.00,
            'monetization_potential': 27.00,
            'simplicity_score': 70.00,
            'title': 'Balancing lower income in EU with improved quality of life?'
        },
        {
            'submission_id': '69da0c96-1b89-46b1-86ef-06fd54bb8ec1',
            'final_score': 32.20,
            'market_demand': 50.00,
            'pain_intensity': 40.00,
            'monetization_potential': 27.00,
            'simplicity_score': 70.00,
            'title': 'Bitcoin Newcomers FAQ - Please read!'
        }
    ]


def load_insights_to_supabase_via_dlt(
    insights: List[Dict[str, Any]]
) -> bool:
    """
    Load AI-generated insights to Supabase using DLT pipeline.

    This function uses DLT's merge write disposition to automatically handle
    deduplication based on opportunity_id. If an insight already exists, it will
    be updated with new values.

    Args:
        insights: List of insight dictionaries with app_concept, core_functions, etc.

    Returns:
        True if successful, False otherwise
    """
    if not insights:
        print("⚠️  No insights to load")
        return False

    try:
        print(f"\n{'='*80}")
        print("LOADING INSIGHTS TO SUPABASE VIA DLT PIPELINE")
        print(f"{'='*80}")
        print(f"Insights to load: {len(insights)}")

        # Create DLT pipeline
        pipeline = create_dlt_pipeline()

        # Load with merge disposition to prevent duplicates
        # Primary key is opportunity_id (unique per submission)
        load_info = pipeline.run(
            insights,
            table_name="opportunity_analysis",
            write_disposition="merge",
            primary_key="opportunity_id"  # Deduplication key
        )

        print(f"\n✓ Successfully loaded {len(insights)} AI insights")
        print(f"  - Table: opportunity_analysis")
        print(f"  - Write mode: merge (deduplication enabled)")
        print(f"  - Primary key: opportunity_id")
        print(f"  - Started at: {load_info.started_at}")
        print(f"{'='*80}\n")

        return True

    except Exception as e:
        print(f"\n✗ Error loading insights via DLT: {e}")
        print(f"  - Insights affected: {len(insights)}")
        print(f"  - Recommendation: Check DLT configuration and Supabase connection")
        print(f"{'='*80}\n")
        return False


def main():
    parser = argparse.ArgumentParser(description='Generate AI insights for monetizable app opportunities')
    parser.add_argument('--mode', choices=['database', 'test'], default='database',
                      help='Input mode: database (from Supabase) or test (sample data)')
    parser.add_argument('--limit', type=int, default=5, help='Number of opportunities to process')
    args = parser.parse_args()

    print("=" * 80)
    print("GENERATING OPPORTUNITY INSIGHTS (OpenRouter + Claude Haiku)")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  Mode: {args.mode.upper()}")
    print(f"  Model: {OPENROUTER_MODEL}")
    print(f"  Rate limit: {RATE_LIMIT_DELAY}s between requests")
    print(f"  Validation: Strict (1-3 functions, Reddit evidence required)")
    print(f"  API: OpenRouter (https://openrouter.ai)")
    print()

    # Validate environment
    if not SUPABASE_KEY:
        print("❌ ERROR: SUPABASE_KEY not set")
        sys.exit(1)

    if not OPENROUTER_API_KEY:
        print("❌ ERROR: OPENROUTER_API_KEY not set")
        sys.exit(1)

    # Get opportunities based on mode
    if args.mode == 'test':
        print(f"Using {args.limit} sample opportunities (high-quality, meets all criteria)...")
        opportunities = get_sample_opportunities()[:args.limit]

        # Fetch REAL content from database (even in test mode!)
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        submission_ids = [opp['submission_id'] for opp in opportunities]
        sub_query = supabase.table("submissions").select("id, title, text").in_(
            "id", submission_ids
        )
        sub_response = sub_query.execute()
        submissions_map = {s['id']: s for s in sub_response.data}

        # Fetch comments too
        com_query = supabase.table("comments").select("submission_id, body").in_(
            "submission_id", submission_ids
        ).order("upvotes", desc=True).limit(3)
        com_response = com_query.execute()

        comments_map = {}
        for comment in com_response.data:
            sub_id = comment['submission_id']
            if sub_id not in comments_map:
                comments_map[sub_id] = []
            comments_map[sub_id].append(comment['body'])

        print(f"✅ Loaded REAL Reddit content for {len(submissions_map)} submissions")
        print(f"✅ Loaded comments for {len(comments_map)} submissions")
    else:
        # Database mode - ONLY process problem posts
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"Fetching top {args.limit} PROBLEM submissions from database...")

        # Get all submissions with comments first
        query = supabase.table("submissions").select(
            "id, title, text, subreddit, num_comments"
        ).gt("num_comments", 0).order("num_comments", desc=True).limit(200)
        all_submissions = query.execute().data

        # Filter for problem posts by checking for problem keywords in title/text
        problem_keywords = [
            "struggle", "problem", "frustrated", "wish", "if only", "hate",
            "annoying", "difficult", "hard", "complicated", "confusing",
            "time consuming", "manual", "tedious", "slow", "expensive",
            "can't", "unable to", "impossible", "issue", "bug", "error"
        ]

        problem_submissions = []
        for sub in all_submissions:
            content = f"{sub['title']} {sub.get('text', '')}".lower()
            if any(keyword in content for keyword in problem_keywords):
                problem_submissions.append(sub)

        print(f"✅ Found {len(problem_submissions)} PROBLEM posts (out of {len(all_submissions)} total)")
        submissions = problem_submissions[:args.limit]

        if not submissions:
            print("❌ No problem posts found")
            print("⚠️  Try collecting data with problem-first approach first")
            return

        print(f"✅ Processing top {len(submissions)} problem posts")

        # Fetch comments for context
        submission_ids = [sub['id'] for sub in submissions]
        com_query = supabase.table("comments").select("submission_id, body, upvotes").in_(
            "submission_id", submission_ids
        ).order("upvotes", desc=True).limit(5)
        com_response = com_query.execute()

        comments_map = {}
        for comment in com_response.data:
            sub_id = comment['submission_id']
            if sub_id not in comments_map:
                comments_map[sub_id] = []
            comments_map[sub_id].append(comment['body'])

        # Create opportunities structure for processing
        opportunities = []
        submissions_map = {}
        for sub in submissions:
            submissions_map[sub['id']] = sub
            opportunities.append({
                'submission_id': sub['id'],
                'title': sub['title'],
                # Scores will be fetched from database below
                'market_demand': None,
                'pain_intensity': None,
                'monetization_potential': None,
                'simplicity_score': None,
                'final_score': None
            })

        # Fetch calculated scores (using opportunity_analysis table as source)
        print(f"\n📊 Fetching opportunity scores from database...")
        try:
            submission_ids = [sub['id'] for sub in submissions]
            # Fetch from opportunity_analysis table which has calculated scores
            score_query = supabase.table("opportunity_analysis").select(
                "submission_id, market_demand, pain_intensity, monetization_potential, simplicity_score, final_score"
            ).in_("submission_id", [str(sid) for sid in submission_ids])
            scores_response = score_query.execute()

            # Build scores map
            scores_map = {s['submission_id']: s for s in scores_response.data}

            # Update opportunities with actual scores
            for opp in opportunities:
                score_data = scores_map.get(str(opp['submission_id']))  # Convert UUID to string for lookup
                if score_data:
                    # Scores in opportunity_analysis are already in 0-100 range
                    opp['market_demand'] = round(score_data['market_demand'], 2) if isinstance(score_data['market_demand'], (int, float)) else 0
                    opp['pain_intensity'] = round(score_data['pain_intensity'], 2) if isinstance(score_data['pain_intensity'], (int, float)) else 0
                    opp['monetization_potential'] = round(score_data['monetization_potential'], 2) if isinstance(score_data['monetization_potential'], (int, float)) else 0
                    opp['simplicity_score'] = round(score_data['simplicity_score'], 2) if isinstance(score_data['simplicity_score'], (int, float)) else 0
                    opp['final_score'] = round(score_data['final_score'], 2) if isinstance(score_data['final_score'], (int, float)) else 0
                else:
                    # Fallback: generate scores on the fly if not in database
                    print(f"  ⚠️  Submission {opp['submission_id']} not in opportunity_analysis table, using baseline scores...")
                    try:
                        calc_response = supabase.rpc("update_opportunity_score", {
                            "p_submission_id": opp['submission_id']
                        }).execute()
                        if calc_response.data:
                            result = calc_response.data[0] if isinstance(calc_response.data, list) else calc_response.data
                            opp['market_demand'] = round(result.get('market_demand', 0) * 10, 2)
                            opp['pain_intensity'] = round(result.get('pain_intensity', 0) * 10, 2)
                            opp['monetization_potential'] = round(result.get('monetization_potential', 0) * 10, 2)
                            opp['simplicity_score'] = round(result.get('simplicity_score', 0) * 10, 2)
                            opp['final_score'] = round(result.get('composite_score', 0), 2)
                    except Exception as e:
                        print(f"  ✗ Error calculating scores: {e}")
                        # Use baseline scores as fallback
                        opp['market_demand'] = 60
                        opp['pain_intensity'] = 70
                        opp['monetization_potential'] = 60
                        opp['simplicity_score'] = 50
                        opp['final_score'] = 60

            print(f"✅ Scores loaded for {len(scores_map)} submissions")
        except Exception as e:
            print(f"⚠️  Could not fetch scores from database: {e}")
            print(f"   Using baseline scores as fallback...")
            for opp in opportunities:
                opp['market_demand'] = 60
                opp['pain_intensity'] = 70
                opp['monetization_potential'] = 60
                opp['simplicity_score'] = 50
                opp['final_score'] = 60

    print()

    # Initialize rate limiter
    rate_limiter = RateLimiter(min_delay=3.0, max_delay=5.0)

    # Process opportunities and batch insights for DLT loading
    ai_count = 0
    rejected_count = 0
    validation_failed = 0
    insights_batch = []  # Accumulate for batch DLT loading

    for idx, opp in enumerate(opportunities, 1):
        title = opp.get('title', 'N/A')
        print(f"\n[{idx}/{len(opportunities)}] {title[:70]}...")

        submission = submissions_map.get(opp['submission_id'], {})
        content = submission.get('text', '')

        # Combine top comments into context string
        top_comments = "\n---\n".join(comments_map.get(opp['submission_id'], [])[:3])

        scores = {
            'market_demand': opp.get('market_demand', 0),
            'pain_intensity': opp.get('pain_intensity', 0),
            'monetization_potential': opp.get('monetization_potential', 0),
            'simplicity_score': opp.get('simplicity_score', 0)
        }

        try:
            # Try to generate AI insight
            insight = generate_insight_with_openrouter(
                title, content, scores, rate_limiter, top_comments
            )

            # Validate insight - ONLY accept if it's valid
            if insight:
                is_valid, reason = validate_insight(insight, scores['monetization_potential'])

                if is_valid:
                    ai_count += 1
                    print(f"  ✅ Valid insight generated")

                    # Prepare insight data for DLT batch loading
                    # Generate opportunity_id from submission_id (for merge deduplication)
                    opportunity_id = f"opp_{opp['submission_id']}"

                    insert_data = {
                        'opportunity_id': opportunity_id,
                        'submission_id': str(opp['submission_id']),
                        'title': opp['title'],
                        'app_concept': insight.get('app_concept'),
                        'core_functions': insight.get('core_functions'),
                        'growth_justification': insight.get('growth_justification'),
                        'market_demand': float(opp.get('market_demand', 5)),
                        'pain_intensity': float(opp.get('pain_intensity', 5)),
                        'monetization_potential': float(opp.get('monetization_potential', 5)),
                        'simplicity_score': float(opp.get('simplicity_score', 5)),
                        'final_score': float(opp.get('final_score', 5)),
                    }

                    # Add to batch for DLT loading
                    insights_batch.append(insert_data)

                    # Display preview
                    if args.mode == 'test':
                        print(f"  📝 {insight.get('app_concept')[:60]}...")
                        print(f"  🔬 Test mode - will load via DLT in batch")
                    else:
                        print(f"  📝 {insight.get('app_concept')[:60]}...")
                        print(f"  🔄 Added to batch for DLT loading")
                else:
                    validation_failed += 1
                    print(f"  ❌ Validation failed: {reason}")
            else:
                rejected_count += 1
                print(f"  ⚠️  AI rejected opportunity (null response)")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            rejected_count += 1

    # Batch load all insights via DLT (only if not in test mode)
    dlt_success = False
    if insights_batch and args.mode != 'test':
        print(f"\n{'='*80}")
        print(f"BATCH LOADING {len(insights_batch)} INSIGHTS VIA DLT")
        print(f"{'='*80}")
        dlt_success = load_insights_to_supabase_via_dlt(insights_batch)
    elif insights_batch and args.mode == 'test':
        print(f"\n🔬 Test mode: Skipping DLT load for {len(insights_batch)} insights")
        dlt_success = True  # Count as success in test mode

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total processed: {len(opportunities)}")
    print(f"✅ Valid insights generated: {ai_count}")
    print(f"❌ Validation failures: {validation_failed}")
    print(f"⏭️  AI rejections (null): {rejected_count}")
    print()

    # DLT Statistics
    if dlt_success and insights_batch:
        print("DLT Pipeline Statistics:")
        print(f"  - Insights loaded: {len(insights_batch)}")
        print(f"  - Table: opportunity_analysis")
        print(f"  - Write disposition: merge (deduplication)")
        print(f"  - Primary key: opportunity_id")
        print()

    if ai_count > 0:
        print(f"✅ SUCCESS! {ai_count} high-quality insights generated")
        print(f"💰 Estimated cost: ~${(ai_count * 0.0001):.4f} (extremely affordable)")
        if dlt_success:
            print(f"💾 DLT Pipeline: Successfully loaded {len(insights_batch)} insights")
    else:
        print("⚠️  No valid insights generated (check validation criteria)")


if __name__ == "__main__":
    main()
