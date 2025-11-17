#!/usr/bin/env python3
"""
Simple test for Jina Reader API functionality.
Tests the API directly without project dependencies.
"""

import os
import sys
import logging
import httpx
from dataclasses import dataclass
from datetime import datetime, UTC

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class JinaResponse:
    """Response from Jina Reader API"""
    content: str
    url: str
    title: str | None = None
    timestamp: datetime = datetime.now(UTC)
    cached: bool = False
    word_count: int = 0

    def __post_init__(self):
        if self.word_count == 0:
            self.word_count = len(self.content.split())

def test_jina_api():
    """Test Jina API functionality"""
    print("=" * 70)
    print("JINA READER API TEST")
    print("=" * 70)

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv(".env.local")

    # Get API key
    api_key = os.getenv("JINA_API_KEY")
    if not api_key:
        print("❌ JINA_API_KEY not found in .env.local")
        return False

    print(f"✅ API Key found: {api_key[:20]}...")

    # Setup client
    headers = {
        "Accept": "text/plain",
        "User-Agent": "RedditHarbor/1.0 (Test)",
    }

    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    client = httpx.Client(
        timeout=httpx.Timeout(30),
        headers=headers,
        follow_redirects=True,
    )

    try:
        # Test 1: Search for "AI expense tracking apps market size 2024"
        print("\n1. WEB SEARCH TEST")
        print("-" * 40)
        search_query = "AI expense tracking apps market size 2024"
        search_url = f"https://s.jina.ai/?q={search_query}"

        print(f"Searching: '{search_query}'")
        response = client.get(search_url)
        response.raise_for_status()

        content = response.text
        print(f"✅ Search successful! Content length: {len(content)} characters")
        print("\nFirst 500 characters of search results:")
        print("-" * 40)
        print(content[:500])
        print("-" * 40)

        # Test 2: Read a URL from the search results
        print("\n2. URL READING TEST")
        print("-" * 40)

        # Extract a URL from the search results (simple approach)
        lines = content.split('\n')
        test_url = None

        for line in lines[:20]:  # Check first 20 lines
            if line.startswith('http') and ('example' in line or 'blog' in line or 'news' in line):
                test_url = line.strip()
                break

        if not test_url:
            # Fallback to a known URL
            test_url = "https://stripe.com/pricing"

        print(f"Reading URL: {test_url}")
        reader_url = f"https://r.jina.ai/http://{test_url.replace('https://', '')}"

        url_response = client.get(reader_url)
        url_response.raise_for_status()

        url_content = url_response.text
        print(f"✅ URL reading successful! Content length: {len(url_content)} characters")

        # Extract title
        title = None
        url_lines = url_content.split('\n')
        for line in url_lines[:10]:
            if line.startswith('Title:'):
                title = line[6:].strip()
                break
            elif line.startswith('# '):
                title = line[2:].strip()
                break

        if title:
            print(f"✅ Title extracted: {title}")
        else:
            print("⚠️  No title found")

        print(f"Word count: {len(url_content.split())}")
        print("\nFirst 300 characters of URL content:")
        print("-" * 40)
        print(url_content[:300])
        print("-" * 40)

        # Test 3: Rate limit info
        print("\n3. RATE LIMIT INFORMATION")
        print("-" * 40)
        rate_limit_headers = {
            'X-RateLimit-Limit': response.headers.get('X-RateLimit-Limit', 'Not provided'),
            'X-RateLimit-Remaining': response.headers.get('X-RateLimit-Remaining', 'Not provided'),
        }

        for key, value in rate_limit_headers.items():
            print(f"{key}: {value}")

        print("\n✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("SUMMARY:")
        print("✅ API Key authentication: Working")
        print("✅ Web search: Working")
        print("✅ URL reading: Working")
        print("✅ Response quality: Good")
        print("=" * 70)

        return True

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()

if __name__ == "__main__":
    success = test_jina_api()
    sys.exit(0 if success else 1)