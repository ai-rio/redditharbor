#!/usr/bin/env python3
"""
Test script for Simplified MCP Jina Integration

This script tests the new simplified MCP-based Jina client and compares it with the original direct client.
"""

import logging
import sys
import time
from typing import Any

from agent_tools.jina_mcp_client_simple import JinaMCPClientSimple, get_jina_mcp_client_simple
from agent_tools.jina_reader_client import get_jina_client
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def test_mcp_connection():
    """Test basic MCP connection and tool availability"""
    print("\n" + "=" * 60)
    print("TESTING MCP CONNECTION")
    print("=" * 60)

    try:
        client = get_jina_mcp_client_simple(fallback_to_direct=False)  # MCP only
        status = client.get_rate_limit_status()

        print(f"MCP Connected: {status['mcp_connected']}")
        print(f"Available Tools: {status['mcp_tools']}")

        if status.get('mcp_error'):
            print(f"MCP Error: {status['mcp_error']}")

        if status['mcp_connected']:
            print("✅ MCP connection successful!")
            return True
        else:
            print("❌ MCP connection failed")
            return False

    except Exception as e:
        print(f"❌ Exception during MCP connection test: {e}")
        return False
    finally:
        try:
            client.close()
        except:
            pass


def test_url_reading():
    """Test URL reading functionality"""
    print("\n" + "=" * 60)
    print("TESTING URL READING")
    print("=" * 60)

    test_url = "https://example.com"

    # Test MCP client with fallback
    try:
        print(f"Testing MCP client with fallback for: {test_url}")
        start_time = time.time()

        mcp_client = get_jina_mcp_client_simple(fallback_to_direct=True)
        response = mcp_client.read_url(test_url)

        end_time = time.time()

        print(f"✅ MCP client success!")
        print(f"   Title: {response.title}")
        print(f"   Word count: {response.word_count}")
        print(f"   Content preview: {response.content[:200]}...")
        print(f"   Response time: {end_time - start_time:.2f}s")
        print(f"   Cached: {response.cached}")

        mcp_success = True
        mcp_time = end_time - start_time

    except Exception as e:
        print(f"❌ MCP client failed: {e}")
        mcp_success = False
        mcp_time = None

    # Test direct client for comparison
    try:
        print(f"\nTesting direct client for: {test_url}")
        start_time = time.time()

        direct_client = get_jina_client()
        response = direct_client.read_url(test_url)

        end_time = time.time()

        print(f"✅ Direct client success!")
        print(f"   Title: {response.title}")
        print(f"   Word count: {response.word_count}")
        print(f"   Content preview: {response.content[:200]}...")
        print(f"   Response time: {end_time - start_time:.2f}s")
        print(f"   Cached: {response.cached}")

        direct_success = True
        direct_time = end_time - start_time

    except Exception as e:
        print(f"❌ Direct client failed: {e}")
        direct_success = False
        direct_time = None

    # Summary
    print(f"\nURL READING SUMMARY:")
    print(f"   MCP Client:     {'✅' if mcp_success else '❌'}" + (f" ({mcp_time:.2f}s)" if mcp_time else ""))
    print(f"   Direct Client:  {'✅' if direct_success else '❌'}" + (f" ({direct_time:.2f}s)" if direct_time else ""))

    if mcp_success and direct_success and mcp_time and direct_time:
        speed_diff = ((direct_time - mcp_time) / direct_time) * 100
        print(f"   Speed diff:     {speed_diff:+.1f}% (MCP vs Direct)")

    return mcp_success or direct_success


def test_web_search():
    """Test web search functionality"""
    print("\n" + "=" * 60)
    print("TESTING WEB SEARCH")
    print("=" * 60)

    test_query = "expense tracking app pricing"

    # Test MCP client with fallback
    try:
        print(f"Testing MCP client with fallback for: {test_query}")
        start_time = time.time()

        mcp_client = get_jina_mcp_client_simple(fallback_to_direct=True)
        results = mcp_client.search_web(test_query, num_results=3)

        end_time = time.time()

        print(f"✅ MCP client success!")
        print(f"   Results found: {len(results)}")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.title}")
            print(f"      {result.url}")
            print(f"      {result.snippet[:100]}...")
        print(f"   Response time: {end_time - start_time:.2f}s")

        mcp_success = True
        mcp_time = end_time - start_time

    except Exception as e:
        print(f"❌ MCP client failed: {e}")
        mcp_success = False
        mcp_time = None

    # Test direct client for comparison
    try:
        print(f"\nTesting direct client for: {test_query}")
        start_time = time.time()

        direct_client = get_jina_client()
        results = direct_client.search_web(test_query, num_results=3)

        end_time = time.time()

        print(f"✅ Direct client success!")
        print(f"   Results found: {len(results)}")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.title}")
            print(f"      {result.url}")
            print(f"      {result.snippet[:100]}...")
        print(f"   Response time: {end_time - start_time:.2f}s")

        direct_success = True
        direct_time = end_time - start_time

    except Exception as e:
        print(f"❌ Direct client failed: {e}")
        direct_success = False
        direct_time = None

    # Summary
    print(f"\nWEB SEARCH SUMMARY:")
    print(f"   MCP Client:     {'✅' if mcp_success else '❌'}" + (f" ({mcp_time:.2f}s)" if mcp_time else ""))
    print(f"   Direct Client:  {'✅' if direct_success else '❌'}" + (f" ({direct_time:.2f}s)" if direct_time else ""))

    if mcp_success and direct_success and mcp_time and direct_time:
        speed_diff = ((direct_time - mcp_time) / direct_time) * 100
        print(f"   Speed diff:     {speed_diff:+.1f}% (MCP vs Direct)")

    return mcp_success or direct_success


def test_caching():
    """Test caching functionality"""
    print("\n" + "=" * 60)
    print("TESTING CACHING")
    print("=" * 60)

    test_url = "https://example.com"

    try:
        client = get_jina_mcp_client_simple()
        client.clear_cache()  # Start fresh

        print(f"First call (should fetch from API):")
        start_time = time.time()
        response1 = client.read_url(test_url)
        time1 = time.time() - start_time
        print(f"   Time: {time1:.2f}s, Cached: {response1.cached}")

        print(f"Second call (should use cache):")
        start_time = time.time()
        response2 = client.read_url(test_url)
        time2 = time.time() - start_time
        print(f"   Time: {time2:.2f}s, Cached: {response2.cached}")

        if response2.cached and time2 < time1:
            speedup = (time1 - time2) / time1 * 100
            print(f"✅ Caching working! {speedup:.1f}% speedup")
            return True
        else:
            print("❌ Caching not working as expected")
            return False

    except Exception as e:
        print(f"❌ Caching test failed: {e}")
        return False


def test_rate_limiting():
    """Test rate limiting functionality"""
    print("\n" + "=" * 60)
    print("TESTING RATE LIMITING")
    print("=" * 60)

    try:
        client = get_jina_mcp_client_simple()
        status = client.get_rate_limit_status()

        print(f"Rate limit status:")
        print(f"   Read remaining:  {status['read_remaining']}/{status['read_max']}")
        print(f"   Search remaining: {status['search_remaining']}/{status['search_max']}")
        print(f"   Cache size: {status['cache_size']}")

        # Test a few rapid calls to see if rate limiting works
        print(f"\nMaking 3 rapid search calls...")
        for i in range(3):
            start_time = time.time()
            try:
                results = client.search_web(f"test query {i}", num_results=1)
                end_time = time.time()
                print(f"   Call {i+1}: {len(results)} results in {end_time - start_time:.2f}s")
            except Exception as e:
                print(f"   Call {i+1}: Failed - {e}")

        print("✅ Rate limiting test completed")
        return True

    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")
        return False


def test_market_data_validator():
    """Test MarketDataValidator with MCP client"""
    print("\n" + "=" * 60)
    print("TESTING MARKET DATA VALIDATOR")
    print("=" * 60)

    try:
        from agent_tools.market_data_validator import MarketDataValidator

        validator = MarketDataValidator()  # Should use MCP client by default

        # Simple validation test
        app_concept = "expense tracking app"
        target_market = "B2C"
        problem = "People struggle to track expenses manually"

        print(f"Running market validation for: {app_concept}")
        start_time = time.time()

        evidence = validator.validate_opportunity(
            app_concept, target_market, problem, max_searches=2  # Limited for testing
        )

        end_time = time.time()

        print(f"✅ Market validation completed!")
        print(f"   Validation score: {evidence.validation_score:.1f}/100")
        print(f"   Data quality score: {evidence.data_quality_score:.1f}/100")
        print(f"   Competitors found: {len(evidence.competitor_pricing)}")
        print(f"   Similar launches: {len(evidence.similar_launches)}")
        print(f"   URLs fetched: {len(evidence.urls_fetched)}")
        print(f"   Total cost: ${evidence.total_cost:.4f}")
        print(f"   Response time: {end_time - start_time:.2f}s")

        # Get client status
        if hasattr(validator.jina_client, 'get_rate_limit_status'):
            status = validator.jina_client.get_rate_limit_status()
            print(f"   Client type: {'MCP' if status.get('mcp_connected') else 'Direct'}")
            if status.get('mcp_connected'):
                print(f"   MCP tools: {status['mcp_tools']}")

        return True

    except Exception as e:
        print(f"❌ Market data validator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("SIMPLIFIED MCP JINA INTEGRATION TESTS")
    print("=" * 60)
    print(f"Settings:")
    print(f"  Market validation enabled: {settings.MARKET_VALIDATION_ENABLED}")
    print(f"  Jina read RPM limit: {settings.JINA_READ_RPM_LIMIT}")
    print(f"  Jina search RPM limit: {settings.JINA_SEARCH_RPM_LIMIT}")
    print(f"  Request timeout: {settings.JINA_REQUEST_TIMEOUT}s")

    tests = [
        ("MCP Connection", test_mcp_connection),
        ("URL Reading", test_url_reading),
        ("Web Search", test_web_search),
        ("Caching", test_caching),
        ("Rate Limiting", test_rate_limiting),
        ("Market Data Validator", test_market_data_validator),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:<25} {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! MCP integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())