#!/usr/bin/env python3
"""
Test OpenRouter API with DeepSeek free model
Verify authentication and API functionality
"""

import json
import os
import sys
from pathlib import Path

import requests

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
load_dotenv(project_root / '.env.local')

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3.1:free")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

print("=" * 80)
print("OPENROUTER + DEEPSEEK API TEST")
print("=" * 80)
print("\nConfiguration:")
print(f"  API Key: {OPENROUTER_API_KEY[:50]}...")
print(f"  Model: {OPENROUTER_MODEL}")
print(f"  Base URL: {OPENROUTER_BASE_URL}")
print()

if not OPENROUTER_API_KEY:
    print("❌ OPENROUTER_API_KEY not found in .env.local")
    sys.exit(1)

# Test 1: Check API key and credits
print("\n1. CHECKING API KEY STATUS")
print("-" * 80)

try:
    response = requests.get(
        f"{OPENROUTER_BASE_URL}/key",
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
        timeout=10
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("✅ API Key is valid!")
        print("\nKey Details:")
        print(f"  Label: {data.get('data', {}).get('label', 'N/A')}")
        print(f"  Limit: {data.get('data', {}).get('limit', 'N/A')}")
        print(f"  Remaining: {data.get('data', {}).get('limit_remaining', 'N/A')}")
        print(f"  Usage (all time): {data.get('data', {}).get('usage', 'N/A')}")
        print(f"  Usage (daily): {data.get('data', {}).get('usage_daily', 'N/A')}")
        print(f"  Is Free Tier: {data.get('data', {}).get('is_free_tier', 'N/A')}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        sys.exit(1)

except Exception as e:
    print(f"❌ Exception: {e}")
    sys.exit(1)

# Test 2: List available models (check if DeepSeek is available)
print("\n2. CHECKING AVAILABLE MODELS")
print("-" * 80)

try:
    response = requests.get(
        f"{OPENROUTER_BASE_URL}/models",
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
        timeout=10
    )

    if response.status_code == 200:
        models = response.json()
        deepseek_models = [m for m in models.get('data', []) if 'deepseek' in m.get('id', '').lower()]

        print(f"✅ Found {len(models.get('data', []))} total models")
        print(f"✅ Found {len(deepseek_models)} DeepSeek models")

        print("\nDeepSeek Models Available:")
        for model in deepseek_models[:10]:  # Show first 10
            print(f"  - {model.get('id')} ({model.get('name', 'N/A')})")
            print(f"    Pricing: ${model.get('pricing', {}).get('prompt', 'N/A')}/1K prompt, ${model.get('pricing', {}).get('completion', 'N/A')}/1K completion")
            print(f"    Context: {model.get('context_length', 'N/A')} tokens")
            print()

        # Check if our target model is available
        target_model = OPENROUTER_MODEL
        found = any(m.get('id') == target_model for m in deepseek_models)
        if found:
            print(f"✅ Target model '{target_model}' is available")
        else:
            print(f"⚠️  Target model '{target_model}' not found in list")
            print("Available DeepSeek models listed above")

    else:
        print(f"❌ Error: {response.status_code}")

except Exception as e:
    print(f"❌ Exception: {e}")

# Test 3: Make a test API call to DeepSeek
print("\n3. TESTING DEEPSEEK API CALL")
print("-" * 80)

test_prompt = """Generate a concise app opportunity description for a fitness tracking app.

Return JSON only with:
{
  "app_concept": "One-line app description",
  "core_functions": ["function1", "function2", "function3"],
  "growth_justification": "Why this has monetization potential"
}"""

try:
    print(f"Calling DeepSeek model: {OPENROUTER_MODEL}")
    print(f"Prompt: {test_prompt[:100]}...")

    response = requests.post(
        f"{OPENROUTER_BASE_URL}/responses",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": OPENROUTER_MODEL,
            "input": test_prompt,
            "max_output_tokens": 500,
            "temperature": 0.7
        },
        timeout=60
    )

    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Time: {response.elapsed.total_seconds():.2f}s")

    if response.status_code == 200:
        result = response.json()
        print("\n✅ SUCCESS! DeepSeek API is working!")
        print("\nResponse structure:")
        print(json.dumps(result, indent=2)[:1000])

        # Try to extract the content
        if 'response' in result:
            output = result['response'].get('output', [])
            if output and len(output) > 0:
                message = output[0].get('content', [])
                if message and len(message) > 0:
                    text = message[0].get('text', '')
                    print("\n📝 Generated Text:")
                    print(text[:500])

                    # Try to parse JSON
                    import re
                    json_match = re.search(r'\{.*\}', text, re.DOTALL)
                    if json_match:
                        try:
                            insight = json.loads(json_match.group())
                            print("\n✅ Parsed JSON:")
                            print(json.dumps(insight, indent=2))
                        except:
                            print("\n⚠️  Could not parse JSON from response")
    else:
        print(f"\n❌ ERROR: {response.status_code}")
        print(f"Response: {response.text[:1000]}")

except Exception as e:
    print(f"\n❌ Exception: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("OPENROUTER TEST COMPLETE")
print("=" * 80)
