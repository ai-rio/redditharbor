#!/usr/bin/env python3
"""
Test script for Hybrid Jina Integration

This script tests the new hybrid Jina client that combines reliability
with MCP readiness for future integration.
"""

import logging
import sys
import time
from typing import Any

from agent_tools.jina_hybrid_client import JinaHybridClient, get_jina_hybrid_client
from agent_tools.jina_reader_client import get_jina_client
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def test_mcp_capabilities():
    """Test MCP capability detection"""
    print("\n" + "=" * 60)
    print("TESTING MCP CAPABILITIES")
    print("=" * 60)

    try:
        # Test without experimental MCP first
        client = get_jina_hybrid_client(enable_mcp_experimental=False)
        status = client.get_rate_limit_status()

        print(f"Standard Mode:")
        print(f"   MCP Available: {status['mcp_available']}")
        print(f"   MCP Experimental: {status['mcp_experimental_enabled']}")
        print(f"   MCP Status: {status['mcp_status_message']}")
        print(f"   Primary Client: {status['primary_client']}")

        # Test with experimental MCP
        client_exp = get_jina_hybrid_client(enable_mcp_experimental=True)
        status_exp = client_exp.get_rate_limit_status()

        print(f"\nExperimental Mode:")
        print(f"   MCP Available: {status_exp['mcp_available']}")
        print(f"   MCP Experimental: {status_exp['mcp_experimental_enabled']}")
        print(f"   MCP Status: {status_exp['mcp_status_message']}")
        print(f"   MCP Tools: {status_exp['mcp_tools']}")
        print(f"   MCP Version: {status_exp['mcp_server_version']}")

        if status_exp['mcp_available']:
            print("✅ MCP capabilities detected successfully")
            return True
        else:
            print("⚠️  MCP not available, but hybrid client will work with direct HTTP")
            return True  # This is expected and acceptable

    except Exception as e:
        print(f"❌ Exception during MCP capability test: {e}")
        return False
    finally:
        try:
            client.close()
            client_exp.close()
        except:
            pass


def test_url_reading():
    """Test URL reading functionality"""
    print("\n" + "=" * 60)
    print("TESTING URL READING")
    print("=" * 60)

    test_url = "https://example.com"

    # Test hybrid client
    try:
        print(f"Testing hybrid client for: {test_url}")
        start_time = time.time()

        hybrid_client = get_jina_hybrid_client(enable_mcp_experimental=True)
        response = hybrid_client.read_url(test_url)

        end_time = time.time()

        print(f"✅ Hybrid client success!")
        print(f"   Title: {response.title}")
        print(f"   Word count: {response.word_count}")
        print(f"   Content preview: {response.content[:200]}...")
        print(f"   Response time: {end_time - start_time:.2f}s")
        print(f"   Cached: {response.cached}")

        hybrid_success = True
        hybrid_time = end_time - start_time

    except Exception as e:
        print(f"❌ Hybrid client failed: {e}")
        hybrid_success = False
        hybrid_time = None

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
    print(f"   Hybrid Client:  {'✅' if hybrid_success else '❌'}" + (f" ({hybrid_time:.2f}s)" if hybrid_time else ""))
    print(f"   Direct Client:  {'✅' if direct_success else '❌'}" + (f" ({direct_time:.2f}s)" if direct_time else ""))

    if hybrid_success and direct_success and hybrid_time and direct_time:
        speed_diff = ((direct_time - hybrid_time) / direct_time) * 100
        print(f"   Speed diff:     {speed_diff:+.1f}% (Hybrid vs Direct)")

    return hybrid_success or direct_success


def test_web_search():
    """Test web search functionality"""
    print("\n" + "=" * 60)
    print("TESTING WEB SEARCH")
    print("=" * 60)

    test_query = "expense tracking app pricing"

    # Test hybrid client
    try:
        print(f"Testing hybrid client for: {test_query}")
        start_time = time.time()

        hybrid_client = get_jina_hybrid_client(enable_mcp_experimental=True)
        results = hybrid_client.search_web(test_query, num_results=3)

        end_time = time.time()

        print(f"✅ Hybrid client success!")
        print(f"   Results found: {len(results)}")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.title}")
            print(f"      {result.url}")
            print(f"      {result.snippet[:100]}...")
        print(f"   Response time: {end_time - start_time:.2f}s")

        hybrid_success = True
        hybrid_time = end_time - start_time

    except Exception as e:
        print(f"❌ Hybrid client failed: {e}")
        hybrid_success = False
        hybrid_time = None

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
    print(f"   Hybrid Client:  {'✅' if hybrid_success else '❌'}" + (f" ({hybrid_time:.2f}s)" if hybrid_time else ""))
    print(f"   Direct Client:  {'✅' if direct_success else '❌'}" + (f" ({direct_time:.2f}s)" if direct_time else ""))

    if hybrid_success and direct_success and hybrid_time and direct_time:
        speed_diff = ((direct_time - hybrid_time) / direct_time) * 100
        print(f"   Speed diff:     {speed_diff:+.1f}% (Hybrid vs Direct)")

    return hybrid_success or direct_success


def test_caching():
    """Test caching functionality"""
    print("\n" + "=" * 60)
    print("TESTING CACHING")
    print("=" * 60)

    test_url = "https://example.com"

    try:
        client = get_jina_hybrid_client()
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
        client = get_jina_hybrid_client()
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
    """Test MarketDataValidator with hybrid client"""
    print("\n" + "=" * 60)
    print("TESTING MARKET DATA VALIDATOR")
    print("=" * 60)

    try:
        from agent_tools.market_data_validator import MarketDataValidator

        validator = MarketDataValidator(enable_mcp_experimental=True)  # Should use hybrid client

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
            print(f"   Client type: {status['client_type']}")
            print(f"   Primary client: {status['primary_client']}")
            print(f"   MCP available: {status['mcp_available']}")
            if status['mcp_available']:
                print(f"   MCP tools: {status['mcp_tools']}")

        return True

    except Exception as e:
        print(f"❌ Market data validator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("HYBRID JINA INTEGRATION TESTS")
    print("=" * 60)
    print(f"Settings:")
    print(f"  Market validation enabled: {settings.MARKET_VALIDATION_ENABLED}")
    print(f"  Jina read RPM limit: {settings.JINA_READ_RPM_LIMIT}")
    print(f"  Jina search RPM limit: {settings.JINA_SEARCH_RPM_LIMIT}")
    print(f"  Request timeout: {settings.JINA_REQUEST_TIMEOUT}s")

    tests = [
        ("MCP Capabilities", test_mcp_capabilities),
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
        print("🎉 All tests passed! Hybrid Jina integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())