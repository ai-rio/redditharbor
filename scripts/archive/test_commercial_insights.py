#!/usr/bin/env python3
"""Test AI insights on commercial subreddit data"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
import re

from redditharbor.login import supabase

from config.settings import SUPABASE_KEY, SUPABASE_URL


def clean_ai_response(text):
    """Clean and validate AI response"""
    if not text or len(text.strip()) < 50:
        return None

    # Remove markdown code blocks
    text = re.sub(r'```json\n?', '', text)
    text = re.sub(r'\n?```', '', text)

    # Try to parse as JSON
    try:
        data = json.loads(text)
        return data
    except:
        return None

def get_opportunity_data(submission_id):
    """Fetch opportunity data with comments from database"""
    client = supabase(url=SUPABASE_URL, private_key=SUPABASE_KEY)

    # Get submission
    result = client.table('submissions').select('*').eq('id', submission_id).execute()
    if not result.data:
        return None
    submission = result.data[0]

    # Get comments
    result = client.table('comments').select('body').eq('submission_id', submission_id).limit(10).execute()
    comments = result.data

    return {
        'submission': submission,
        'comments': comments
    }

def analyze_with_ai(data):
    """Analyze opportunity with OpenRouter"""
    submission = data['submission']
    comments = data['comments']

    # Build prompt
    prompt = f"""
You are analyzing a Reddit post for monetizable app opportunities.

Post Title: {submission['title']}
Post Text: {submission.get('text', 'N/A')}
Subreddit: {submission['subreddit']}

Top Comments:
"""

    for i, comment in enumerate(comments[:10], 1):
        prompt += f"{i}. {comment['body'][:300]}\n\n"

    prompt += """
Analyze this post for a monetizable app opportunity. Respond with ONLY valid JSON:

{
  "app_concept": "Brief app idea (max 20 words)",
  "core_functions": ["function 1", "function 2", "function 3"],
  "target_market": "Who would use this",
  "monetization_model": "How to make money",
  "reddit_evidence": "Quotes showing demand/pain points",
  "confidence": 0.0-1.0,
  "justification": "Why this is valid"
}

CRITICAL REQUIREMENTS:
- Must be an actual app (not a service, tool, or manual process)
- Maximum 3 core functions
- Must cite Reddit evidence
- No generic "productivity" or "automation" apps
"""

    # Call OpenRouter
    headers = {
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        'model': 'anthropic/claude-haiku-4.5',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 500
    }

    try:
        # Note: Using Supabase key as API key won't work - need actual OpenRouter key
        print("⚠️  Cannot test without OpenRouter API key")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# Test
if __name__ == "__main__":
    # Test post: "My client wants to buy exclusivity"
    submission_id = "d92f6e00-4961-4b94-a3f8-b40810deeab7"

    print("=" * 80)
    print("TESTING AI INSIGHTS ON COMMERCIAL POST")
    print("=" * 80)

    data = get_opportunity_data(submission_id)
    if data:
        print(f"\n✅ Found submission: {data['submission']['title'][:60]}...")
        print(f"✅ Found {len(data['comments'])} comments")

        # Show the data
        print(f"\nPost text: {data['submission'].get('text', 'N/A')[:200]}...")
        print("\nComment sample:")
        for i, comment in enumerate(data['comments'][:3], 1):
            print(f"  {i}. {comment['body'][:150]}...")
    else:
        print("❌ Submission not found")
