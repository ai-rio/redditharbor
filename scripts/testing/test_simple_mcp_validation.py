#!/usr/bin/env python3
"""
Simple MCP Validation Test

This script tests the simple MCP client that doesn't depend on Agno.
It validates that MCP is actually being used instead of falling back to HTTP.
"""

import json
import logging
import subprocess
import sys
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agent_tools.jina_mcp_client_simple import JinaMCPClientSimple
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Test data
TEST_URL = "https://example.com"
TEST_QUERY = "software development best practices"


def test_mcp_server_direct():
    """Test direct interaction with MCP server"""
    print("\n" + "="*60)
    print("TESTING DIRECT MCP SERVER INTERACTION")
    print("="*60)

    try:
        # Test server version
        print("1. Checking MCP server availability...")
        result = subprocess.run(
            ["npx", "-y", "jina-mcp-tools", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            print(f"❌ MCP server not available: {result.stderr}")
            return False

        print(f"✅ MCP server available: {result.stdout.strip()}")

        # Test tools list
        print("2. Getting available tools...")
        mcp_request = {"method": "tools/list"}
        result = subprocess.run(
            ["npx", "-y", "jina-mcp-tools"],
            input=json.dumps(mcp_request),
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode != 0:
            print(f"❌ MCP tools list failed: {result.stderr}")
            return False

        response = json.loads(result.stdout)
        tools = [tool.get("name", "") for tool in response.get("result", {}).get("tools", [])]
        print(f"✅ Available MCP tools: {tools}")

        # Check for required tools
        required_tools = ["jina_reader", "jina_search"]
        found_tools = [tool for tool in required_tools if tool in tools]

        if found_tools:
            print(f"✅ Found required tools: {found_tools}")
            return True
        else:
            print(f"❌ Missing required tools. Required: {required_tools}, Found: {tools}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ MCP server interaction timed out")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse MCP response: {e}")
        return False
    except Exception as e:
        print(f"❌ Direct MCP test failed: {e}")
        return False


def test_mcp_direct_tool_call():
    """Test direct tool call to MCP server"""
    print("\n" + "="*60)
    print("TESTING DIRECT MCP TOOL CALL")
    print("="*60)

    try:
        # Call jina_reader directly
        print("Calling jina_reader tool directly...")
        mcp_request = {
            "method": "tools/call",
            "params": {
                "name": "jina_reader",
                "arguments": {
                    "url": TEST_URL
                }
            }
        }

        start_time = time.time()
        result = subprocess.run(
            ["npx", "-y", "jina-mcp-tools"],
            input=json.dumps(mcp_request),
            capture_output=True,
            text=True,
            timeout=30
        )
        elapsed = time.time() - start_time

        if result.returncode != 0:
            print(f"❌ Direct tool call failed: {result.stderr}")
            return False

        try:
            response = json.loads(result.stdout)

            # Extract content
            content = ""
            if "result" in response:
                if isinstance(response["result"], dict):
                    content = response["result"].get("content", "") or response["result"].get("text", "") or str(response["result"])
                else:
                    content = str(response["result"])
            else:
                content = result.stdout

            if content and len(content) > 50:
                print(f"✅ Direct MCP tool call successful!")
                print(f"   Time: {elapsed:.2f}s")
                print(f"   Content length: {len(content)}")
                print(f"   Content preview: {content[:100].replace(chr(10), ' ')}...")
                return True
            else:
                print(f"❌ Insufficient content: {len(content)} characters")
                return False

        except json.JSONDecodeError:
            # Check if we got raw text content
            if len(result.stdout.strip()) > 50:
                print(f"✅ Direct tool call successful (raw output)!")
                print(f"   Time: {elapsed:.2f}s")
                print(f"   Content length: {len(result.stdout)}")
                return True
            else:
                print(f"❌ Failed to parse and insufficient content")
                return False

    except subprocess.TimeoutExpired:
        print("❌ Direct tool call timed out")
        return False
    except Exception as e:
        print(f"❌ Direct tool call failed: {e}")
        return False


def test_simple_mcp_client_no_fallback():
    """Test Simple MCP client with fallback disabled"""
    print("\n" + "="*60)
    print("TESTING SIMPLE MCP CLIENT (NO FALLBACK)")
    print("="*60)

    try:
        # Create client with fallback disabled
        client = JinaMCPClientSimple(fallback_to_direct=False)

        # Check connection status
        status = client.get_rate_limit_status()
        print(f"Connection status:")
        print(f"  MCP Connected: {status.get('mcp_connected', False)}")
        print(f"  Available Tools: {status.get('mcp_tools', [])}")
        print(f"  Fallback Enabled: {status.get('fallback_enabled', True)}")

        if status.get('mcp_error'):
            print(f"  MCP Error: {status['mcp_error']}")

        if not status.get('mcp_connected'):
            print("❌ Simple MCP client failed to connect")
            return False

        # Test URL reading
        print(f"\nTesting URL reading: {TEST_URL}")
        start_time = time.time()
        response = client.read_url(TEST_URL, use_cache=False)
        elapsed = time.time() - start_time

        if response and response.content and len(response.content) > 50:
            print(f"✅ Simple MCP client URL reading successful!")
            print(f"   Time: {elapsed:.2f}s")
            print(f"   Content length: {len(response.content)}")
            print(f"   Word count: {response.word_count}")
            print(f"   Title: {response.title}")
            print(f"   Cached: {response.cached}")
            print(f"   Content preview: {response.content[:100].replace(chr(10), ' ')}...")
            return True
        else:
            print(f"❌ Simple MCP client URL reading failed: insufficient content")
            return False

    except Exception as e:
        print(f"❌ Simple MCP client test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        try:
            client.close()
        except:
            pass


def test_simple_mcp_client_search():
    """Test Simple MCP client search functionality"""
    print("\n" + "="*60)
    print("TESTING SIMPLE MCP CLIENT SEARCH")
    print("="*60)

    try:
        client = JinaMCPClientSimple(fallback_to_direct=False)

        # Check connection status
        status = client.get_rate_limit_status()
        if not status.get('mcp_connected'):
            print("❌ MCP client not connected for search test")
            return False

        # Test web search
        print(f"Testing web search: {TEST_QUERY}")
        start_time = time.time()
        results = client.search_web(TEST_QUERY, num_results=3, use_cache=False)
        elapsed = time.time() - start_time

        if results and len(results) > 0:
            print(f"✅ Simple MCP client search successful!")
            print(f"   Time: {elapsed:.2f}s")
            print(f"   Results found: {len(results)}")

            for i, result in enumerate(results, 1):
                print(f"   Result {i}:")
                print(f"     Title: {result.title}")
                print(f"     URL: {result.url}")
                print(f"     Snippet: {result.snippet[:100]}...")

            return True
        else:
            print(f"❌ Simple MCP client search failed: no results")
            return False

    except Exception as e:
        print(f"❌ Simple MCP client search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        try:
            client.close()
        except:
            pass


def test_caching_functionality():
    """Test that caching works with MCP client"""
    print("\n" + "="*60)
    print("TESTING CACHING FUNCTIONALITY")
    print("="*60)

    try:
        client = JinaMCPClientSimple(fallback_to_direct=False)

        # Clear cache
        cleared = client.clear_cache()
        print(f"Cache cleared: {cleared} items")

        # First call (should fetch from MCP)
        print("First call (should fetch from MCP)...")
        start_time = time.time()
        response1 = client.read_url(TEST_URL, use_cache=True)
        time1 = time.time() - start_time

        print(f"   Time: {time1:.2f}s, Cached: {response1.cached}")

        # Second call (should use cache)
        print("Second call (should use cache)...")
        start_time = time.time()
        response2 = client.read_url(TEST_URL, use_cache=True)
        time2 = time.time() - start_time

        print(f"   Time: {time2:.2f}s, Cached: {response2.cached}")

        # Verify cache is working
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

    finally:
        try:
            client.close()
        except:
            pass


def main():
    """Run all Simple MCP validation tests"""
    print("SIMPLE MCP VALIDATION TESTS")
    print("="*80)
    print("This test suite validates that MCP is actually being used")
    print("instead of falling back to HTTP requests.")
    print(f"Test URL: {TEST_URL}")
    print(f"Test Query: {TEST_QUERY}")
    print(f"Settings:")
    print(f"  Request timeout: {settings.JINA_REQUEST_TIMEOUT}s")
    print("="*80)

    tests = [
        ("Direct MCP Server", test_mcp_server_direct),
        ("Direct MCP Tool Call", test_mcp_direct_tool_call),
        ("Simple MCP Client (No Fallback)", test_simple_mcp_client_no_fallback),
        ("Simple MCP Client Search", test_simple_mcp_client_search),
        ("Caching Functionality", test_caching_functionality),
    ]

    results = []
    total_start_time = time.time()

    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"\n{test_name}: {status}")
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    total_time = time.time() - total_start_time

    # Final summary
    print("\n" + "="*80)
    print("SIMPLE MCP VALIDATION SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:<30} {status}")

    print(f"\nOverall: {passed}/{total} tests passed")
    print(f"Total time: {total_time:.2f}s")

    if passed == total:
        print("\n🎉 All Simple MCP validation tests passed!")
        print("✅ MCP server is responding correctly")
        print("✅ MCP tools are accessible and functional")
        print("✅ Simple MCP client is using MCP (not just falling back to HTTP)")
        print("✅ Caching is working properly")
        print("\n✅ THE MCP INTEGRATION IS WORKING CORRECTLY!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed.")
        print("Check the logs above for details on what needs to be fixed.")
        if passed == 0:
            print("\n❌ NO TESTS PASSED - MCP INTEGRATION IS NOT WORKING")
            print("The system is likely falling back to HTTP or failing completely.")
        return 1


if __name__ == "__main__":
    sys.exit(main())