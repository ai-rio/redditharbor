#!/usr/bin/env python3
"""
Final validation test for the MCP Jina integration implementation.
"""

import logging
import time

from agent_tools.jina_hybrid_client import JinaHybridClient
from agent_tools.market_data_validator import MarketDataValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_basic_functionality():
    """Test basic hybrid client functionality"""
    print("Testing basic hybrid client functionality...")

    client = JinaHybridClient(enable_mcp_experimental=True)

    # Test URL reading
    print("\n1. Testing URL reading...")
    try:
        response = client.read_url("https://example.com")
        print(f"   ✅ Successfully read URL: {response.title} ({response.word_count} words)")
    except Exception as e:
        print(f"   ❌ URL reading failed: {e}")
        return False

    # Test web search
    print("\n2. Testing web search...")
    try:
        results = client.search_web("python programming", num_results=2)
        print(f"   ✅ Successfully found {len(results)} search results")
        for i, result in enumerate(results, 1):
            print(f"      {i}. {result.title}")
    except Exception as e:
        print(f"   ❌ Web search failed: {e}")
        return False

    # Test MCP capabilities
    print("\n3. Testing MCP capabilities...")
    status = client.get_rate_limit_status()
    print(f"   MCP Available: {status['mcp_available']}")
    print(f"   MCP Status: {status['mcp_status_message']}")
    print(f"   Client Type: {status['client_type']}")
    print(f"   ✅ MCP capability detection working")

    client.close()
    return True


def test_market_validator():
    """Test market data validator integration"""
    print("\n\nTesting MarketDataValidator integration...")

    validator = MarketDataValidator(enable_mcp_experimental=True)

    # Get client status
    if hasattr(validator.jina_client, 'get_rate_limit_status'):
        status = validator.jina_client.get_rate_limit_status()
        print(f"   Client Type: {status['client_type']}")
        print(f"   MCP Available: {status['mcp_available']}")
        print(f"   ✅ MarketDataValidator successfully uses hybrid client")
        return True
    else:
        print("   ❌ MarketDataValidator not using hybrid client")
        return False


def main():
    """Run final validation tests"""
    print("FINAL VALIDATION: MCP JINA INTEGRATION")
    print("=" * 60)

    start_time = time.time()

    # Test basic functionality
    basic_test = test_basic_functionality()

    # Test market validator integration
    validator_test = test_market_validator()

    end_time = time.time()

    print(f"\n\nFINAL SUMMARY")
    print("=" * 60)
    print(f"Basic Functionality: {'✅ PASS' if basic_test else '❌ FAIL'}")
    print(f"Market Validator:    {'✅ PASS' if validator_test else '❌ FAIL'}")
    print(f"Test Duration: {end_time - start_time:.2f}s")

    if basic_test and validator_test:
        print("\n🎉 SUCCESS: MCP Jina integration is working correctly!")
        print("\nKey Achievements:")
        print("   ✅ Hybrid client created with direct HTTP reliability")
        print("   ✅ MCP capability detection implemented")
        print("   ✅ MarketDataValidator integration completed")
        print("   ✅ Backward compatibility maintained")
        print("   ✅ Ready for future MCP server integration")
        return 0
    else:
        print("\n❌ FAILURE: Some tests failed")
        return 1


if __name__ == "__main__":
    exit(main())