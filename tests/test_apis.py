#!/usr/bin/env python3
"""
Test API keys for MiniMax and Z.AI GLM
Validates rate limits and functionality
"""

import json
import os
import time
from pathlib import Path

import requests

# Load environment variables
project_root = Path(__file__).parent
env_file = project_root / '.env.local'

with open(env_file) as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, val = line.strip().split('=', 1)
            os.environ[key] = val

print("=" * 80)
print("API TESTING - MiniMax vs Z.AI GLM")
print("=" * 80)

# Test payload
test_payload = {
    "title": "Building a fitness app for busy professionals",
    "content": "I need a workout app that can give me quick 15-minute routines",
    "scores": {"market_demand": 75, "pain_intensity": 80}
}

# =============================================================================
# TEST 1: MiniMax API
# =============================================================================
print("\n1. TESTING MINIMAX API")
print("-" * 80)

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
MINIMAX_GROUP_ID = os.getenv("MINIMAX_GROUP_ID")

if not MINIMAX_API_KEY or not MINIMAX_GROUP_ID:
    print("❌ MiniMax credentials not found")
else:
    print(f"✅ API Key: {MINIMAX_API_KEY[:50]}...")
    print(f"✅ Group ID: {MINIMAX_GROUP_ID}")

    try:
        # MiniMax API call
        url = "https://api.minimax.chat/v1/text/chatcompletion_pro"

        headers = {
            "Authorization": f"Bearer {MINIMAX_API_KEY}",
            "Content-Type": "application/json"
        }

        prompt = f"""Generate a concise app opportunity description.

TITLE: {test_payload['title']}
CONTENT: {test_payload['content']}

Return JSON with: app_concept, core_functions (array), growth_justification"""

        data = {
            "model": "abab6.5s-chat",
            "stream": False,
            "use_standard_sse": False,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "reply_constraints": {
                "sender_type": "BOT",
                "sender_name": "MiniMax"
            }
        }

        print("Calling MiniMax API...")
        start_time = time.time()
        response = requests.post(url, headers=headers, json=data, timeout=30)
        elapsed = time.time() - start_time

        print(f"Response Time: {elapsed:.2f}s")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS - MiniMax API is working!")
            print(f"Response: {json.dumps(result, indent=2)[:500]}...")
        elif response.status_code == 429:
            print("❌ 429 ERROR - Rate Limited")
            print(f"Headers: {response.headers}")
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.text[:500]}")

    except Exception as e:
        print(f"❌ Exception: {e}")

# =============================================================================
# TEST 2: Z.AI GLM API
# =============================================================================
print("\n2. TESTING Z.AI GLM API")
print("-" * 80)

GLM_API_KEY = os.getenv("GLM_API_KEY")
GLM_BASE_URL = "https://api.z.ai/api/paas/v4/"
GLM_MODEL = "glm-4.6"

if not GLM_API_KEY:
    print("❌ GLM API Key not found")
else:
    print(f"✅ API Key: {GLM_API_KEY[:30]}...")
    print(f"✅ Model: {GLM_MODEL}")

    try:
        # Z.AI GLM API call
        url = f"{GLM_BASE_URL}chat/completions"

        headers = {
            "Authorization": f"Bearer {GLM_API_KEY}",
            "Content-Type": "application/json"
        }

        prompt = f"""Based on this Reddit post, generate a concise opportunity description.

TITLE: {test_payload['title']}
CONTENT: {test_payload['content']}

SCORES:
- Market Demand: {test_payload['scores']['market_demand']}/100
- Pain Intensity: {test_payload['scores']['pain_intensity']}/100

Generate JSON with:
1. app_concept: One-line app description
2. core_functions: Array of 1-3 key features
3. growth_justification: Why this has monetization potential (2-3 sentences)

JSON only, no explanation."""

        data = {
            "model": GLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 0.7
        }

        print("Calling Z.AI GLM API...")
        start_time = time.time()
        response = requests.post(url, headers=headers, json=data, timeout=30)
        elapsed = time.time() - start_time

        print(f"Response Time: {elapsed:.2f}s")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS - Z.AI GLM API is working!")
            print(f"Response: {json.dumps(result, indent=2)[:500]}...")
        elif response.status_code == 429:
            print("❌ 429 ERROR - Rate Limited")
            print(f"Headers: {dict(response.headers)}")
            if 'X-RateLimit-Remaining' in response.headers:
                print(f"Rate Limit Remaining: {response.headers['X-RateLimit-Remaining']}")
            if 'X-RateLimit-Reset' in response.headers:
                print(f"Rate Limit Reset: {response.headers['X-RateLimit-Reset']}")
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.text[:500]}")

    except Exception as e:
        print(f"❌ Exception: {e}")

# =============================================================================
# RATE LIMIT TEST
# =============================================================================
print("\n3. TESTING RATE LIMITS")
print("-" * 80)
print("Making 5 rapid requests to test rate limiting...")
print("(This will help us determine safe request intervals)")
print()

if GLM_API_KEY:
    url = f"{GLM_BASE_URL}chat/completions"
    headers = {
        "Authorization": f"Bearer {GLM_API_KEY}",
        "Content-Type": "application/json"
    }

    for i in range(5):
        start = time.time()
        data = {
            "model": GLM_MODEL,
            "messages": [{"role": "user", "content": f"Test request {i+1}"}],
            "max_tokens": 50
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            elapsed = time.time() - start
            status = "✅" if response.status_code == 200 else "❌"

            print(f"{status} Request {i+1}: {response.status_code} ({elapsed:.2f}s)")

            if response.status_code == 429:
                print(f"   ⚠️  Rate limited! Headers: {dict(response.headers)}")
                break

            # Small delay between requests
            time.sleep(0.5)

        except Exception as e:
            print(f"❌ Request {i+1} failed: {e}")
            break

print("\n" + "=" * 80)
print("API TESTING COMPLETE")
print("=" * 80)
