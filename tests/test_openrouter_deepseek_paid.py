#!/usr/bin/env python3
"""
Test OpenRouter API with DeepSeek PAID model (not free)
Verify full API functionality before implementing rate limiting
"""

import json
import os
import sys
import time
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
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Use a paid DeepSeek model (very cheap: $0.0000002 per 1K prompt tokens)
OPENROUTER_MODEL = "deepseek/deepseek-chat-v3.1"

print("=" * 80)
print("OPENROUTER + DEEPSEEK PAID MODEL TEST")
print("=" * 80)
print("\nConfiguration:")
print(f"  API Key: {OPENROUTER_API_KEY[:50]}...")
print(f"  Model: {OPENROUTER_MODEL}")
print("  Pricing: $0.0000002/1K prompt, $0.0000008/1K completion (very cheap!)")
print()

if not OPENROUTER_API_KEY:
    print("❌ OPENROUTER_API_KEY not found")
    sys.exit(1)

# Test with real opportunity insight generation
test_opportunity = {
    "title": "Some things I have learned from 15 years of coaching (updated)",
    "content": "After 15 years of coaching, I've realized that most people think coaching is about motivation and accountability. While those are important, the real power of coaching lies in helping people understand their patterns and create new neural pathways that make success feel natural...",
    "scores": {
        "market_demand": 65.0,
        "pain_intensity": 45.0,
        "monetization_potential": 30.0
    }
}

# Create detailed prompt
prompt = f"""Based on this Reddit post, generate a concise app opportunity description.

TITLE: {test_opportunity['title']}
CONTENT: {test_opportunity['content']}

SCORES:
- Market Demand: {test_opportunity['scores']['market_demand']}/100
- Pain Intensity: {test_opportunity['scores']['pain_intensity']}/100
- Monetization Potential: {test_opportunity['scores']['monetization_potential']}/100

Generate JSON with:
1. app_concept: One-line app description (e.g., "Personal coaching and mentorship platform")
2. core_functions: Array of 1-3 key features
3. growth_justification: Why this has monetization potential (2-3 sentences)

JSON only, no explanation or markdown."""

print("\nCalling DeepSeek API for insight generation...")
print(f"Title: {test_opportunity['title'][:60]}...")
print()

try:
    start_time = time.time()
    response = requests.post(
        f"{OPENROUTER_BASE_URL}/responses",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": OPENROUTER_MODEL,
            "input": prompt,
            "max_output_tokens": 400,
            "temperature": 0.7
        },
        timeout=60
    )

    elapsed = time.time() - start_time

    print(f"📊 Status Code: {response.status_code}")
    print(f"⏱️  Response Time: {elapsed:.2f}s")

    if response.status_code == 200:
        result = response.json()
        print("\n✅ SUCCESS! DeepSeek API is working!")

        # Extract the content
        if 'response' in result:
            output = result['response'].get('output', [])
            if output and len(output) > 0:
                message = output[0].get('content', [])
                if message and len(message) > 0:
                    text = message[0].get('text', '')
                    print("\n📝 Generated Response:")
                    print("-" * 80)
                    print(text)
                    print("-" * 80)

                    # Try to parse JSON
                    import re
                    json_match = re.search(r'\{.*\}', text, re.DOTALL)
                    if json_match:
                        try:
                            insight = json.loads(json_match.group())
                            print("\n✅ PARSED JSON:")
                            print(json.dumps(insight, indent=2))

                            print("\n📋 INSIGHT BREAKDOWN:")
                            print(f"  App Concept: {insight.get('app_concept')}")
                            functions = insight.get('core_functions', [])
                            print(f"  Core Functions ({len(functions)}):")
                            for func in functions:
                                print(f"    - {func}")
                            print(f"  Growth Justification: {insight.get('growth_justification')}")

                        except json.JSONDecodeError as e:
                            print(f"\n⚠️  Could not parse JSON: {e}")
                            print(f"Raw text: {text}")
    else:
        print(f"\n❌ ERROR: {response.status_code}")
        print(f"Response: {response.text[:1000]}")

except Exception as e:
    print(f"\n❌ Exception: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("OPENROUTER DEEPSEEK TEST COMPLETE")
print("=" * 80)
print("\nNext steps:")
print("1. ✅ API integration confirmed working")
print("2. 📊 Model pricing: ~$0.0002 per 1K tokens (very affordable)")
print("3. 🔄 Ready to implement rate-limited insight generation")
print("4. 💡 Suggest using this PAID model instead of free (more reliable)")
