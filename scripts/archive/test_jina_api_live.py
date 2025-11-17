#!/usr/bin/env python3
"""
Live test for Jina Reader API with real API key.
This tests actual web content fetching and search capabilities.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment
from dotenv import load_dotenv

load_dotenv(project_root / ".env.local")

import logging

logging.basicConfig(level=logging.INFO)

from agent_tools.jina_reader_client import JinaReaderClient

print("=" * 70)
print("JINA READER API LIVE TEST")
print("=" * 70)

# Initialize client
client = JinaReaderClient()

# Check API key
from config import settings

print(f"\nAPI Key configured: {'Yes' if settings.JINA_API_KEY else 'No'}")
print(f"API Key prefix: {settings.JINA_API_KEY[:20]}..." if settings.JINA_API_KEY else "")

# Test 1: Rate limit status
print("\n1. RATE LIMIT STATUS")
print("-" * 40)
status = client.get_rate_limit_status()
for key, value in status.items():
    print(f"  {key}: {value}")

# Test 2: Read a simple URL
print("\n2. READ URL TEST")
print("-" * 40)
test_url = "https://stripe.com/pricing"
print(f"Reading: {test_url}")

try:
    response = client.read_url(test_url)
    print(f"  ✓ Success!")
    print(f"  Title: {response.title}")
    print(f"  Word count: {response.word_count}")
    print(f"  Cached: {response.cached}")
    print(f"\n  First 500 characters of content:")
    print("  " + "-" * 38)
    content_preview = response.content[:500].replace("\n", "\n  ")
    print(f"  {content_preview}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    import traceback

    traceback.print_exc()

# Test 3: Cache test (should be cached)
print("\n3. CACHE TEST (same URL)")
print("-" * 40)
try:
    response = client.read_url(test_url)
    print(f"  Cached: {response.cached}")
    if response.cached:
        print("  ✓ Cache working correctly!")
except Exception as e:
    print(f"  ✗ Failed: {e}")

# Test 4: Web search
print("\n4. WEB SEARCH TEST")
print("-" * 40)
search_query = "expense tracking app pricing SaaS"
print(f"Searching: '{search_query}'")

try:
    results = client.search_web(search_query, num_results=3)
    print(f"  ✓ Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n  Result {i}:")
        print(f"    Title: {result.title}")
        print(f"    URL: {result.url}")
        print(f"    Snippet: {result.snippet[:100]}...")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    import traceback

    traceback.print_exc()

# Test 5: Final rate limit status
print("\n5. FINAL RATE LIMIT STATUS")
print("-" * 40)
status = client.get_rate_limit_status()
for key, value in status.items():
    print(f"  {key}: {value}")

print("\n" + "=" * 70)
print("LIVE TEST COMPLETE!")
print("=" * 70)
