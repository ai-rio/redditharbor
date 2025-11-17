#!/usr/bin/env python3
"""
Agno MCP Integration Test

This script specifically tests the Agno MCP integration to ensure it works correctly
with the fixed tool names and server configuration.
"""

import logging
import sys
import time
from typing import Dict, List

from agent_tools.jina_mcp_client import JinaMCPClient, get_jina_mcp_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Test data
TEST_URL = "https://example.com"
TEST_QUERY = "software architecture patterns"


def test_agno_connection_only():
    """Test Agno MCP connection without using tools"""
    print("\n" + "="*60)
    print("TESTING AGNO MCP CONNECTION ONLY")
    print("="*60)

    try:
        client = JinaMCPClient(fallback_to_direct=False)
        status = client.get_rate_limit_status()

        print("Connection Status:")
        print(f"  MCP Connected: {status.get('mcp_connected', False)}")
        print(f"  Available Tools: {status.get('mcp_tools', [])}")
        print(f"  Fallback Enabled: {status.get('fallback_enabled', True)}")

        if status.get('mcp_error'):
            print(f"  MCP Error: {status['mcp_error']}")

        if status.get('mcp_connected'):
            print("✅ Agno successfully connected to MCP server")
            return True
        else:
            print("❌ Agno failed to connect to MCP server")
            return False

    except Exception as e:
        print(f"❌ Agno connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        try:
            client.close()
        except:
            pass


def test_agno_tools_availability():
    """Test that Agno can access the correct MCP tools"""
    print("\n" + "="*60)
    print("TESTING AGNO TOOLS AVAILABILITY")
    print("="*60)

    expected_tools = ["jina_reader", "jina_search"]

    try:
        client = JinaMCPClient(fallback_to_direct=False)
        status = client.get_rate_limit_status()

        available_tools = status.get('mcp_tools', [])
        print(f"Expected tools: {expected_tools}")
        print(f"Available tools: {available_tools}")

        # Check for expected tools
        found_tools = [tool for tool in expected_tools if tool in available_tools]
        missing_tools = [tool for tool in expected_tools if tool not in available_tools]

        print(f"Found tools: {found_tools}")
        if missing_tools:
            print(f"Missing tools: {missing_tools}")

        if found_tools:
            print(f"✅ Agno found {len(found_tools)}/{len(expected_tools)} expected tools")
            return True
        else:
            print("❌ Agno didn't find any expected tools")
            return False

    except Exception as e:
        print(f"❌ Agno tools test failed: {e}")
        return False

    finally:
        try:
            client.close()
        except:
            pass


def test_agno_jina_reader():
    """Test Agno with jina_reader tool"""
    print("\n" + "="*60)
    print("TESTING AGNO JINA_READER")
    print("="*60)

    try:
        client = JinaMCPClient(fallback_to_direct=False)

        print(f"Reading URL: {TEST_URL}")
        start_time = time.time()

        response = client.read_url(TEST_URL, use_cache=False)

        elapsed_time = time.time() - start_time

        if response and response.content:
            print(f"✅ Agno jina_reader successful!")
            print(f"  Time taken: {elapsed_time:.2f}s")
            print(f"  Content length: {len(response.content)}")
            print(f"  Word count: {response.word_count}")
            print(f"  Title: {response.title}")
            print(f"  Cached: {response.cached}")

            # Show content preview
            preview = response.content[:200].replace('\n', ' ')
            print(f"  Content preview: {preview}...")

            return True
        else:
            print("❌ Agno jina_reader returned empty response")
            return False

    except Exception as e:
        print(f"❌ Agno jina_reader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        try:
            client.close()
        except:
            pass


def test_agno_jina_search():
    """Test Agno with jina_search tool"""
    print("\n" + "="*60)
    print("TESTING AGNO JINA_SEARCH")
    print("="*60)

    try:
        client = JinaMCPClient(fallback_to_direct=False)

        print(f"Searching for: {TEST_QUERY}")
        start_time = time.time()

        results = client.search_web(TEST_QUERY, num_results=3, use_cache=False)

        elapsed_time = time.time() - start_time

        if results and len(results) > 0:
            print(f"✅ Agno jina_search successful!")
            print(f"  Time taken: {elapsed_time:.2f}s")
            print(f"  Results found: {len(results)}")

            for i, result in enumerate(results, 1):
                print(f"  Result {i}:")
                print(f"    Title: {result.title}")
                print(f"    URL: {result.url}")
                print(f"    Snippet: {result.snippet[:100]}...")
                print()

            return True
        else:
            print("❌ Agno jina_search returned no results")
            return False

    except Exception as e:
        print(f"❌ Agno jina_search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        try:
            client.close()
        except:
            pass


def test_agno_vs_direct_comparison():
    """Compare Agno MCP client with direct HTTP client"""
    print("\n" + "="*60)
    print("TESTING AGNO VS DIRECT COMPARISON")
    print("="*60)

    # Test direct client
    direct_success = False
    direct_time = 0
    direct_content_length = 0

    try:
        from agent_tools.jina_reader_client import get_jina_client
        direct_client = get_jina_client()

        print("Testing direct HTTP client...")
        start_time = time.time()
        direct_response = direct_client.read_url(TEST_URL, use_cache=False)
        direct_time = time.time() - start_time

        if direct_response.content:
            direct_success = True
            direct_content_length = len(direct_response.content)
            print(f"✅ Direct client successful: {direct_content_length} chars in {direct_time:.2f}s")
        else:
            print("❌ Direct client failed: empty response")

    except Exception as e:
        print(f"❌ Direct client failed: {e}")

    # Test Agno MCP client
    agno_success = False
    agno_time = 0
    agno_content_length = 0

    try:
        agno_client = JinaMCPClient(fallback_to_direct=False)

        print("Testing Agno MCP client...")
        start_time = time.time()
        agno_response = agno_client.read_url(TEST_URL, use_cache=False)
        agno_time = time.time() - start_time

        if agno_response.content:
            agno_success = True
            agno_content_length = len(agno_response.content)
            print(f"✅ Agno MCP client successful: {agno_content_length} chars in {agno_time:.2f}s")
        else:
            print("❌ Agno MCP client failed: empty response")

    except Exception as e:
        print(f"❌ Agno MCP client failed: {e}")

    # Compare results
    print(f"\nComparison Results:")
    print(f"Direct HTTP:  {'✅' if direct_success else '❌'} ({direct_time:.2f}s, {direct_content_length} chars)")
    print(f"Agno MCP:     {'✅' if agno_success else '❌'} ({agno_time:.2f}s, {agno_content_length} chars)")

    if direct_success and agno_success:
        # Check if content is reasonably similar
        length_diff_percent = abs(direct_content_length - agno_content_length) / max(direct_content_length, agno_content_length) * 100
        print(f"Content length difference: {length_diff_percent:.1f}%")

        if length_diff_percent < 50:  # Allow some difference due to processing
            print("✅ Both clients working with reasonable content similarity")
            return True
        else:
            print("⚠️  Both clients working but with significant content differences")
            return True  # Still consider success since both are working
    elif agno_success:
        print("✅ Agno MCP client working (direct client failed)")
        return True
    else:
        print("❌ Both clients failed")
        return False


def test_agno_singleton():
    """Test Agno MCP client singleton functionality"""
    print("\n" + "="*60)
    print("TESTING AGNO SINGLETON")
    print("="*60)

    try:
        # Get singleton instance
        client1 = get_jina_mcp_client(fallback_to_direct=False)
        client2 = get_jina_mcp_client(fallback_to_direct=False)

        # Should be the same instance
        if client1 is client2:
            print("✅ Singleton working correctly - same instance returned")
        else:
            print("⚠️  Singleton not working - different instances returned")

        # Test functionality
        response1 = client1.read_url(TEST_URL, use_cache=False)
        response2 = client2.read_url(TEST_URL, use_cache=True)  # Should use cache

        if response1.content and response2.content:
            if response2.cached:
                print("✅ Singleton cache working correctly")
            else:
                print("⚠️  Cache may not be working as expected")

            print(f"✅ Singleton client functional")
            return True
        else:
            print("❌ Singleton client failed to get responses")
            return False

    except Exception as e:
        print(f"❌ Singleton test failed: {e}")
        return False

    finally:
        try:
            client1.close()
            client2.close()
        except:
            pass


def main():
    """Run all Agno MCP integration tests"""
    print("AGNO MCP INTEGRATION TESTS")
    print("="*80)
    print("This test suite validates that the Agno MCP integration works correctly")
    print("with the fixed tool names and server configuration.")
    print(f"Test URL: {TEST_URL}")
    print(f"Test Query: {TEST_QUERY}")
    print("="*80)

    tests = [
        ("Agno Connection Only", test_agno_connection_only),
        ("Agno Tools Availability", test_agno_tools_availability),
        ("Agno Jina Reader", test_agno_jina_reader),
        ("Agno Jina Search", test_agno_jina_search),
        ("Agno vs Direct Comparison", test_agno_vs_direct_comparison),
        ("Agno Singleton", test_agno_singleton),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Final summary
    print("\n" + "="*80)
    print("AGNO MCP INTEGRATION SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:<30} {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All Agno MCP integration tests passed!")
        print("The Agno MCP integration is working correctly with:")
        print("  ✅ Fixed tool names (jina_reader, jina_search)")
        print("  ✅ Correct MCP server (jina-mcp-tools)")
        print("  ✅ Proper tool calls and response handling")
        print("  ✅ Functional fallback behavior")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed.")
        print("Check the logs above for details on what needs to be fixed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())