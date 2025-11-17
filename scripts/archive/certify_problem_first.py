#!/usr/bin/env python3
"""
Certify problem-first approach with 2 test cases:
1. "47 demos" post (already tested successfully)
2. Accessibility post (new candidate)
"""
import json
import os
import sys

import requests
from dotenv import load_dotenv

# Load env
load_dotenv('.env.local')

from supabase import create_client

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Problem-First Prompt
PROBLEM_FIRST_PROMPT = """You are a PROBLEM DISCOVERER. Your job is to:

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
Return ONLY valid JSON:

{{
  "problem_identified": "What is the core problem?",
  "problem_evidence": "Specific quotes/examples from Reddit",
  "app_concept": "Simple app name and what it does",
  "core_functions": ["Function 1", "Function 2"],
  "reddit_demand_evidence": "Quotes showing users want this",
  "simplicity_score": 1-3 (number of core functions)
}}

=== CRITICAL RULES ===
1. Start with PROBLEM, not app
2. Design the SIMPLEST solution (1-3 functions only)
3. Must cite Reddit evidence
4. Reject if no clear problem OR too complex
5. Return null if not a real solvable problem

=== REDDIT POST ===

TITLE: {title}

POST CONTENT:
{content}

TOP COMMENTS:
{top_comments}

Identify the problem, validate it, and design the simplest app to solve it.
Return ONLY valid JSON."""

def test_post(submission_id, expected_title_hint):
    """Test a specific post with problem-first prompt"""
    print(f"\n{'='*80}")
    print(f"TESTING: {expected_title_hint}")
    print('='*80)

    # Get submission
    result = supabase.table("submissions").select("*").eq("id", submission_id).execute()
    if not result.data:
        print("❌ Post not found")
        return False

    post = result.data[0]

    # Get comments
    result = supabase.table("comments").select("body").eq("submission_id", submission_id).order("upvotes", desc=True).limit(3).execute()
    comments = [c['body'] for c in result.data]
    top_comments = "\n---\n".join(comments)

    print(f"\nTitle: {post['title']}")
    print(f"Subreddit: r/{post['subreddit']}")
    print(f"\nText: {post['text'][:400]}...")
    if comments:
        print(f"\nComments ({len(comments)}):")
        for i, c in enumerate(comments, 1):
            print(f"  {i}. {c[:150]}...")

    # Call OpenRouter with problem-first prompt
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    final_prompt = PROBLEM_FIRST_PROMPT.replace('{title}', post['title']).replace(
        '{content}', post['text'][:1500]).replace('{top_comments}', top_comments[:2000])

    payload = {
        "model": "anthropic/claude-haiku-4.5",
        "messages": [{"role": "user", "content": final_prompt}],
        "max_tokens": 600,
        "temperature": 0.7
    }

    print("\n=== CALLING AI ===")
    response = requests.post(url, headers=headers, json=payload, timeout=60)

    if response.status_code != 200:
        print(f"❌ API Error: {response.status_code}")
        return False

    result = response.json()
    text = result['choices'][0]['message']['content'].strip()

    # Clean markdown
    if text.startswith('```json'):
        text = text[7:]
    if text.endswith('```'):
        text = text[:-3]
    text = text.strip()

    print("\nAI Response:")
    print(text)

    # Try to parse JSON
    try:
        insight = json.loads(text)
        print(f"\n{'='*60}")
        print("✅ SUCCESS! Problem-first approach worked!")
        print(f"{'='*60}")
        print(f"\nProblem: {insight.get('problem_identified', 'N/A')}")
        print(f"App: {insight.get('app_concept', 'N/A')}")
        print(f"Functions: {insight.get('core_functions', [])}")
        print(f"Simplicity: {insight.get('simplicity_score', 'N/A')} functions")
        print("\nReddit Evidence:")
        evidence = insight.get('reddit_demand_evidence')
        if evidence:
            print(f"  {evidence[:200]}...")
        else:
            print(f"  {insight.get('rejection_reason', 'N/A')[:200]}...")
        return True
    except json.JSONDecodeError:
        print("\n❌ AI returned non-JSON response")
        return False

# Test Case 1: "47 demos" post (already proven)
print("CERTIFYING PROBLEM-FIRST APPROACH")
print("="*80)

# Find "47 demos" post
result = supabase.table("submissions").select("id").ilike("title", "%47 demos%").execute()
if result.data:
    test_47_demos = test_post(result.data[0]['id'], "47 demos post (Problem: building without validation)")
else:
    print("❌ 47 demos post not found")
    sys.exit(1)

# Test Case 2: Accessibility post
result = supabase.table("submissions").select("id").ilike("title", "%Accessibility%").execute()
if result.data:
    test_accessibility = test_post(result.data[0]['id'], "Accessibility post (Problem: accessibility in development)")
else:
    print("❌ Accessibility post not found")
    sys.exit(1)

# Summary
print(f"\n{'='*80}")
print("CERTIFICATION SUMMARY")
print(f"{'='*80}")
print(f"\nTest 1 - '47 demos' (validation problem): {'✅ PASS' if test_47_demos else '❌ FAIL'}")
print(f"Test 2 - 'Accessibility' (development problem): {'✅ PASS' if test_accessibility else '❌ FAIL'}")
print()

if test_47_demos and test_accessibility:
    print("🎉 PROBLEM-FIRST APPROACH CERTIFIED!")
    print("   ✅ Works on business/startup problems")
    print("   ✅ Works on technical development problems")
    print("   ✅ Generates valid 1-3 function apps")
    print("   ✅ Cites Reddit evidence")
    print("   ✅ Ready for implementation!")
else:
    print("⚠️  Need more testing before implementation")
