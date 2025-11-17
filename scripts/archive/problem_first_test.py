#!/usr/bin/env python3
"""
Test problem-first AI approach on "47 demos" post
"""
import json
import os

import requests
from dotenv import load_dotenv

# Load env
load_dotenv('.env.local')

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

{
  "problem_identified": "What is the core problem?",
  "problem_evidence": "Specific quotes/examples from Reddit",
  "app_concept": "Simple app name and what it does",
  "core_functions": ["Function 1", "Function 2"],
  "reddit_demand_evidence": "Quotes showing users want this",
  "simplicity_score": 1-3 (number of core functions)
}

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
{content}

TOP COMMENTS:
{top_comments}

Identify the problem, validate it, and design the simplest app to solve it.
Return ONLY valid JSON."""

# Get the "47 demos" post
from supabase import create_client

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

result = supabase.table("submissions").select("*").ilike("title", "%47 demos%").execute()
post = result.data[0]
sub_id = post['id']

# Get comments
result = supabase.table("comments").select("body").eq("submission_id", sub_id).order("upvotes", desc=True).limit(3).execute()
comments = [c['body'] for c in result.data]
top_comments = "\n---\n".join(comments)

print("=" * 80)
print("PROBLEM-FIRST AI APPROACH TEST")
print("=" * 80)
print(f"\nTitle: {post['title']}")
print(f"\nPost: {post['text'][:400]}...")
print("\nComments:")
for i, c in enumerate(comments, 1):
    print(f"  {i}. {c[:150]}...")

# Call OpenRouter with problem-first prompt
url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
    "Content-Type": "application/json"
}

# Build the prompt with .format() using double braces to escape
final_prompt = PROBLEM_FIRST_PROMPT.replace('{title}', post['title']).replace(
    '{content}', post['text'][:1500]).replace('{top_comments}', top_comments[:2000])

payload = {
    "model": "anthropic/claude-haiku-4.5",
    "messages": [
        {
            "role": "user",
            "content": final_prompt
        }
    ],
    "max_tokens": 600,
    "temperature": 0.7
}

print("\n=== CALLING AI WITH PROBLEM-FIRST PROMPT ===")
response = requests.post(url, headers=headers, json=payload, timeout=60)

if response.status_code == 200:
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
        print("\n✅ SUCCESS! Problem-first approach worked!")
        print(f"\nProblem: {insight.get('problem_identified', 'N/A')}")
        print(f"App: {insight.get('app_concept', 'N/A')}")
        print(f"Functions: {insight.get('core_functions', [])}")
        print(f"Simplicity: {insight.get('simplicity_score', 'N/A')} functions")
    except json.JSONDecodeError:
        print("\n❌ AI returned non-JSON response")
        print(f"Raw: {text}")
else:
    print(f"\n❌ API Error: {response.status_code}")
    print(response.text[:200])
