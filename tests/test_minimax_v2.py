#!/usr/bin/env python3
"""
Test MiniMax API with correct format
Based on MiniMax API documentation
"""

import os
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
print("TESTING MINIMAX API (Corrected Format)")
print("=" * 80)

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
MINIMAX_GROUP_ID = os.getenv("MINIMAX_GROUP_ID")

print(f"API Key: {MINIMAX_API_KEY[:50]}...")
print(f"Group ID: {MINIMAX_GROUP_ID}")

# Try different endpoints
endpoints = [
    "https://api.minimax.chat/v1/text/chatcompletion_pro",
    "https://api.minimax.chat/v1/text/chatcompletion",
    "https://api.minimax.chat/v1/text/chatcompletion_v2",
]

# Alternative: Use Bearer token directly
test_prompt = "Generate a simple app concept for fitness tracking. Return JSON only."

for endpoint in endpoints:
    print(f"\n{'='*80}")
    print(f"Testing endpoint: {endpoint}")
    print('='*80)

    try:
        # Method 1: Authorization header
        headers = {
            "Authorization": f"Bearer {MINIMAX_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "abab6.5s-chat",
            "messages": [
                {
                    "role": "user",
                    "content": test_prompt
                }
            ],
            "use_standard_sse": False
        }

        print("Method 1: Bearer Authorization")
        response = requests.post(endpoint, headers=headers, json=data, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")

        # Method 2: X-API-Key header
        headers2 = {
            "X-API-Key": MINIMAX_API_KEY,
            "Content-Type": "application/json"
        }

        print("\nMethod 2: X-API-Key Header")
        response2 = requests.post(endpoint, headers=headers2, json=data, timeout=30)
        print(f"Status: {response2.status_code}")
        print(f"Response: {response2.text[:500]}")

        # Method 3: Query parameter
        url_with_key = f"{endpoint}?Authorization=Bearer {MINIMAX_API_KEY}"
        headers3 = {"Content-Type": "application/json"}

        print("\nMethod 3: Query Parameter")
        response3 = requests.post(url_with_key, headers=headers3, json=data, timeout=30)
        print(f"Status: {response3.status_code}")
        print(f"Response: {response3.text[:500]}")

        if response.status_code == 200 and "invalid" not in response.text.lower():
            print(f"\n✅ SUCCESS with endpoint: {endpoint}")
            break

    except Exception as e:
        print(f"❌ Exception: {e}")

print("\n" + "=" * 80)
