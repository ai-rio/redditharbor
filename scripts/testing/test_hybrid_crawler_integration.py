#!/usr/bin/env python3
"""
Test script for Enhanced Hybrid Crawler Integration

Tests the integration between Jina AI and Crawl4AI:
1. Basic functionality testing
2. Performance comparison
3. Token usage monitoring
4. Fallback behavior
5. Quality comparison
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from agent_tools.enhanced_hybrid_client import create_enhanced_hybrid_client
from config import settings


async def test_basic_functionality():
    """Test basic crawling functionality"""
    print("\n🧪 Testing Basic Functionality")
    print("=" * 50)

    # Create enhanced hybrid client
    client = create_enhanced_hybrid_client(
        enable_crawl4ai=True,
        token_threshold=80.0,
        performance_threshold=75.0
    )

    try:
        # Test URLs
        test_urls = [
            "https://example.com",  # Simple static site
            "https://httpbin.org/html",  # Test HTML content
            "https://jsonplaceholder.typicode.com",  # API documentation
        ]

        for url in test_urls:
            print(f"\n📡 Testing: {url}")

            start_time = time.time()
            result = await client.read_url(url)
            end_time = time.time()

            print(f"✅ Success: {bool(result.content)}")
            print(f"📄 Content length: {len(result.content)} chars")
            print(f"📝 Word count: {result.word_count}")
            print(f"⏱️  Response time: {end_time - start_time:.2f}s")
            print(f"📖 Title: {result.title or 'No title'}")

        # Test search functionality
        print(f"\n🔍 Testing search functionality")
        search_results = await client.search("python web scraping", max_results=3)
        print(f"📊 Search results: {len(search_results)} found")

        for i, result in enumerate(search_results, 1):
            print(f"  {i}. {result.title} - {result.url}")

    finally:
        await client.close()


async def test_performance_comparison():
    """Test performance comparison between crawlers"""
    print("\n⚡ Testing Performance Comparison")
    print("=" * 50)

    # Create client with quality comparison enabled
    client = create_enhanced_hybrid_client(
        enable_crawl4ai=True,
        performance_threshold=60.0,  # Lower threshold to trigger switching
        enable_quality_comparison=True
    )

    try:
        test_urls = [
            "https://www.python.org",
            "https://github.com",
            "https://stackoverflow.com"
        ]

        for url in test_urls:
            print(f"\n🔄 Testing performance: {url}")

            # Make multiple requests to test switching behavior
            for i in range(3):
                result = await client.read_url(url)
                print(f"  Request {i+1}: Success={bool(result.content)}, Words={result.word_count}")

                # Small delay between requests
                await asyncio.sleep(1)

        # Get performance stats
        stats = client.get_performance_stats()
        print(f"\n📊 Performance Statistics:")
        print(f"  Jina success rate: {stats['jina_performance']['success_rate']:.1f}%")
        print(f"  Crawl4AI success rate: {stats['crawl4ai_performance']['success_rate']:.1f}%")
        print(f"  Switches to Crawl4AI: {stats['switching_behavior']['switches_to_crawl4ai']}")
        print(f"  Token usage (daily): {stats['token_usage']['daily_percentage']:.1f}%")

    finally:
        await client.close()


async def test_fallback_behavior():
    """Test fallback behavior when primary crawler fails"""
    print("\n🔄 Testing Fallback Behavior")
    print("=" * 50)

    client = create_enhanced_hybrid_client(enable_crawl4ai=True)

    try:
        # Test with potentially problematic URLs
        test_urls = [
            "https://httpbin.org/status/500",  # Server error
            "https://nonexistent-domain-12345.com",  # DNS error
            "https://example.com/does-not-exist-404",  # 404 error
        ]

        for url in test_urls:
            print(f"\n🚨 Testing fallback: {url}")
            try:
                result = await client.read_url(url)
                print(f"  Result: Success={result.success}, Content length={len(result.content)}")
                if result.error_message:
                    print(f"  Error: {result.error_message}")
            except Exception as e:
                print(f"  Exception: {str(e)}")

    finally:
        await client.close()


async def test_token_monitoring():
    """Test token usage monitoring and automatic switching"""
    print("\n💰 Testing Token Usage Monitoring")
    print("=" * 50)

    # Create client with low token threshold to trigger switching
    client = create_enhanced_hybrid_client(
        enable_crawl4ai=True,
        token_threshold=1.0  # Very low threshold to force switching
    )

    try:
        # Make multiple requests to trigger token threshold
        test_url = "https://example.com"

        print(f"🔄 Making multiple requests to trigger token threshold...")

        for i in range(5):
            result = await client.read_url(test_url)
            print(f"  Request {i+1}: Success={bool(result.content)}, Words={result.word_count}")

            # Get current stats
            stats = client.get_performance_stats()
            if stats['token_usage']['near_limits']:
                print(f"  💡 Token usage near limits, switching to Crawl4AI")
                break

        final_stats = client.get_performance_stats()
        print(f"\n📊 Final Token Statistics:")
        print(f"  Daily usage: {final_stats['token_usage']['daily_percentage']:.1f}%")
        print(f"  Hourly usage: {final_stats['token_usage']['hourly_percentage']:.1f}%")
        print(f"  Near limits: {final_stats['token_usage']['near_limits']}")
        print(f"  Switches to Crawl4AI: {final_stats['switching_behavior']['switches_to_crawl4ai']}")

    finally:
        await client.close()


async def test_jina_only_mode():
    """Test Jina-only mode for comparison"""
    print("\n🎯 Testing Jina-Only Mode")
    print("=" * 50)

    # Create client without Crawl4AI
    client = create_enhanced_hybrid_client(enable_crawl4ai=False)

    try:
        test_urls = [
            "https://example.com",
            "https://www.python.org"
        ]

        for url in test_urls:
            print(f"\n📡 Testing Jina-only: {url}")

            start_time = time.time()
            result = await client.read_url(url)
            end_time = time.time()

            print(f"✅ Success: {bool(result.content)}")
            print(f"📄 Content length: {len(result.content)} chars")
            print(f"⏱️  Response time: {end_time - start_time:.2f}s")

        stats = client.get_performance_stats()
        print(f"\n📊 Jina-Only Statistics:")
        print(f"  Success rate: {stats['jina_performance']['success_rate']:.1f}%")
        print(f"  Total requests: {stats['jina_performance']['total_requests']}")
        print(f"  Crawler availability: {stats['crawler_availability']}")

    finally:
        await client.close()


async def main():
    """Run all integration tests"""
    print("🚀 Enhanced Hybrid Crawler Integration Tests")
    print("=" * 60)
    print(f"Configuration:")
    print(f"  - Crawl4AI enabled: {settings.HYBRID_CRAWLER_ENABLE_CRAWL4AI}")
    print(f"  - Jina fallback enabled: {settings.HYBRID_CRAWLER_ENABLE_JINA_FALLBACK}")
    print(f"  - Performance threshold: {settings.HYBRID_CRAWLER_PERFORMANCE_THRESHOLD}%")
    print(f"  - Quality comparison: {settings.HYBRID_CRAWLER_ENABLE_QUALITY_COMPARISON}")

    try:
        # Run tests
        await test_basic_functionality()
        await test_performance_comparison()
        await test_fallback_behavior()
        await test_token_monitoring()
        await test_jina_only_mode()

        print("\n✅ All integration tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)