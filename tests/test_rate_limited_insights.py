#!/usr/bin/env python3
"""
Test rate-limited insight generation (only 2 opportunities)
This will test if we can avoid 429 errors with proper rate limiting
"""

import os
import sys
import time
import random
import requests
import json
from pathlib import Path

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from supabase import create_client
from dotenv import load_dotenv

load_dotenv(project_root / '.env.local')

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GLM_API_KEY = os.getenv("GLM_API_KEY")

print("=" * 80)
print("RATE-LIMITED TEST (2 opportunities)")
print("=" * 80)
print(f"\nRate limiting configuration:")
print(f"  - 10 second delay between requests")
print(f"  - Z.AI GLM API")
print(f"  - Testing with 2 opportunities only")
print()

if not SUPABASE_KEY or not GLM_API_KEY:
    print("❌ Missing required API keys in .env.local")
    sys.exit(1)

# Initialize Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch top 2 opportunities
print("Fetching top 2 opportunities...")
response = supabase.table("opportunity_analysis").select("*").order(
    "final_score", desc=True
).limit(2).execute()

if not response.data:
    print("❌ No opportunities found")
    sys.exit(1)

print(f"✅ Found {len(response.data)} opportunities\n")

# Fetch submissions
submission_ids = [opp['submission_id'] for opp in response.data]
sub_response = supabase.table("submissions").select("id, title, content").in_(
    "id", submission_ids
).execute()
submissions_map = {s['id']: s for s in sub_response.data}

# Process with rate limiting
for idx, opp in enumerate(response.data, 1):
    title = opp.get('title', 'N/A')
    print(f"\n{'='*80}")
    print(f"OPPORTUNITY {idx}/2")
    print(f"{'='*80}")
    print(f"Title: {title[:70]}...")
    print(f"Score: {opp.get('final_score', 'N/A')}")

    submission = submissions_map.get(opp['submission_id'], {})
    content = submission.get('content', '')

    print(f"\n⏱️  Waiting 10 seconds before API call...")
    time.sleep(10)

    try:
        # Prepare prompt
        prompt = f"""Generate a concise app opportunity description.

TITLE: {title}
CONTENT: {content[:800]}

Generate JSON with: app_concept, core_functions (array), growth_justification.
JSON only, no explanation."""

        # Make API request
        url = "https://api.z.ai/api/paas/v4/chat/completions"
        headers = {
            "Authorization": f"Bearer {GLM_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "glm-4.6",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 400,
            "temperature": 0.7
        }

        print(f"📡 Making API request to Z.AI GLM...")
        start = time.time()
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        elapsed = time.time() - start

        print(f"⏱️  Response time: {elapsed:.2f}s")
        print(f"📊 Status code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and result['choices']:
                content = result['choices'][0]['message']['content']
                print(f"✅ SUCCESS! Received response:")
                print(f"   {content[:200]}...")

                # Try to parse JSON
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    insight = json.loads(json_match.group())
                    print(f"\n📝 Parsed insight:")
                    print(f"   App: {insight.get('app_concept')}")
                    print(f"   Functions: {insight.get('core_functions', [])}")

                    # Update database
                    update_data = {
                        'app_concept': insight.get('app_concept'),
                        'core_functions': insight.get('core_functions'),
                        'growth_justification': insight.get('growth_justification')
                    }

                    supabase.table("opportunity_analysis").update(update_data).eq(
                        'opportunity_id', opp['opportunity_id']
                    ).execute()

                    print(f"💾 Database updated!")
                else:
                    print("⚠️  Could not parse JSON from response")
            else:
                print("⚠️  Unexpected response structure")
        elif response.status_code == 429:
            print(f"❌ 429 RATE LIMITED!")
            print(f"   Headers: {dict(response.headers)}")
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"   Response: {response.text[:300]}")

    except Exception as e:
        print(f"❌ Exception: {e}")

print(f"\n{'='*80}")
print("TEST COMPLETE")
print(f"{'='*80}")
print("\n✅ Rate limiting test finished")
print("If both requests succeeded, the rate limit configuration works!")
