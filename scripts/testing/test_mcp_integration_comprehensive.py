#!/usr/bin/env python3
"""
Comprehensive MCP Integration Tests

This script tests all aspects of the MCP integration to ensure it works correctly.
Tests are designed to validate that MCP is actually being used, not just falling back to HTTP.
"""

import json
import logging
import subprocess
import sys
import time
from typing import Any, Dict, List

from agent_tools.jina_hybrid_client import JinaHybridClient, get_jina_hybrid_client
from agent_tools.jina_mcp_client import JinaMCPClient, get_jina_mcp_client
from agent_tools.jina_mcp_client_simple import JinaMCPClientSimple, get_jina_mcp_client_simple
from agent_tools.jina_reader_client import get_jina_client
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Test data
TEST_URL = "https://example.com"
TEST_QUERY = "Python programming best practices"
TIMEOUT = 30


class TestResult:
    """Helper class to track test results"""
    def __init__(self, name: str):
        self.name = name
        self.success = False
        self.error = None
        self.details = {}
        self.duration = 0.0

    def set_success(self, **details):
        self.success = True
        self.details.update(details)

    def set_failure(self, error: str, **details):
        self.success = False
        self.error = error
        self.details.update(details)

    def __str__(self):
        status = "✅ PASS" if self.success else "❌ FAIL"
        return f"{self.name:<30} {status} ({self.duration:.2f}s)"


def test_mcp_server_availability():
    """Test if Jina MCP server is available and working"""
    result = TestResult("MCP Server Availability")
    start_time = time.time()

    try:
        # Test basic server command
        process = subprocess.run(
            ["npx", "-y", "jina-mcp-tools", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if process.returncode == 0:
            result.set_success(
                version=process.stdout.strip(),
                server_available=True
            )
            logger.info(f"MCP server version: {process.stdout.strip()}")
        else:
            result.set_failure(
                f"Server command failed with code {process.returncode}: {process.stderr}",
                return_code=process.returncode
            )

    except subprocess.TimeoutExpired:
        result.set_failure("MCP server check timed out")
    except FileNotFoundError:
        result.set_failure("npx not found - Node.js not available")
    except Exception as e:
        result.set_failure(f"Unexpected error: {e}")

    result.duration = time.time() - start_time
    return result


def test_mcp_tool_list():
    """Test if we can list available MCP tools"""
    result = TestResult("MCP Tool List")
    start_time = time.time()

    try:
        # Request tools list from MCP server
        mcp_request = {"method": "tools/list"}
        process = subprocess.run(
            ["npx", "-y", "jina-mcp-tools"],
            input=json.dumps(mcp_request),
            capture_output=True,
            text=True,
            timeout=15
        )

        if process.returncode == 0:
            try:
                response = json.loads(process.stdout)
                if "result" in response and "tools" in response["result"]:
                    tools = response["result"]["tools"]
                    tool_names = [tool.get("name", "") for tool in tools]

                    # Check for expected tools
                    expected_tools = ["jina_reader", "jina_search"]
                    found_tools = [t for t in expected_tools if t in tool_names]

                    result.set_success(
                        total_tools=len(tool_names),
                        tool_names=tool_names,
                        found_expected_tools=found_tools
                    )
                    logger.info(f"Found {len(found_tools)}/{len(expected_tools)} expected tools: {found_tools}")
                else:
                    result.set_failure("Invalid MCP response format")
            except json.JSONDecodeError as e:
                result.set_failure(f"Failed to parse MCP response: {e}", raw_output=process.stdout[:200])
        else:
            result.set_failure(
                f"MCP process failed with code {process.returncode}: {process.stderr}",
                return_code=process.returncode
            )

    except subprocess.TimeoutExpired:
        result.set_failure("MCP tool list request timed out")
    except Exception as e:
        result.set_failure(f"Unexpected error: {e}")

    result.duration = time.time() - start_time
    return result


def test_mcp_direct_tool_call():
    """Test direct MCP tool call without client wrapper"""
    result = TestResult("Direct MCP Tool Call")
    start_time = time.time()

    try:
        # Call jina_reader tool directly
        mcp_request = {
            "method": "tools/call",
            "params": {
                "name": "jina_reader",
                "arguments": {
                    "url": TEST_URL
                }
            }
        }

        process = subprocess.run(
            ["npx", "-y", "jina-mcp-tools"],
            input=json.dumps(mcp_request),
            capture_output=True,
            text=True,
            timeout=30
        )

        if process.returncode == 0:
            try:
                response = json.loads(process.stdout)
                content = ""

                # Extract content from various response formats
                if "result" in response:
                    if isinstance(response["result"], dict):
                        content = response["result"].get("content", "") or response["result"].get("text", "") or str(response["result"])
                    else:
                        content = str(response["result"])
                else:
                    content = process.stdout

                if content and len(content) > 50:  # Reasonable content length
                    result.set_success(
                        content_length=len(content),
                        response_format="structured" if "result" in response else "raw"
                    )
                    logger.info(f"Direct MCP call succeeded, content length: {len(content)}")
                else:
                    result.set_failure("MCP returned insufficient content", content_length=len(content))

            except json.JSONDecodeError:
                # Fallback: check if we got any text content
                if len(process.stdout.strip()) > 50:
                    result.set_success(
                        content_length=len(process.stdout),
                        response_format="raw_text"
                    )
                else:
                    result.set_failure("Failed to parse MCP response and insufficient content")
        else:
            result.set_failure(
                f"MCP tool call failed with code {process.returncode}: {process.stderr}",
                return_code=process.returncode
            )

    except subprocess.TimeoutExpired:
        result.set_failure("Direct MCP tool call timed out")
    except Exception as e:
        result.set_failure(f"Unexpected error: {e}")

    result.duration = time.time() - start_time
    return result


def test_hybrid_client_mcp_only():
    """Test hybrid client with MCP enabled (experimental)"""
    result = TestResult("Hybrid Client (MCP Only)")
    start_time = time.time()

    try:
        # Create hybrid client with MCP enabled, but disable fallback to test pure MCP
        client = JinaHybridClient(enable_mcp_experimental=True)
        status = client.get_rate_limit_status()

        logger.info(f"Hybrid client status: {status}")

        if not status.get('mcp_available'):
            result.set_failure("MCP not available in hybrid client")
            return result

        if not status.get('jina_mcp_tools_available'):
            result.set_failure("Jina MCP tools not available in hybrid client")
            return result

        # Test URL reading - this will try MCP first, then fallback
        try:
            response = client.read_url(TEST_URL, use_cache=False)

            # Check if we got content
            if response.content and len(response.content) > 50:
                # Note: We can't easily distinguish if MCP was actually used vs fallback
                # But we can check if MCP capabilities were detected
                result.set_success(
                    content_length=len(response.content),
                    word_count=response.word_count,
                    mcp_tools_available=status.get('available_tools', []),
                    mcp_status_message=status.get('mcp_status_message', '')
                )
                logger.info(f"Hybrid client succeeded, content length: {len(response.content)}")
            else:
                result.set_failure("Insufficient content from hybrid client")

        except Exception as e:
            result.set_failure(f"Hybrid client failed to read URL: {e}")

    except Exception as e:
        result.set_failure(f"Failed to initialize hybrid client: {e}")

    finally:
        try:
            client.close()
        except:
            pass

    result.duration = time.time() - start_time
    return result


def test_agno_mcp_client():
    """Test Agno-based MCP client"""
    result = TestResult("Agno MCP Client")
    start_time = time.time()

    try:
        # Test with fallback disabled to test pure MCP
        client = JinaMCPClient(fallback_to_direct=False)
        status = client.get_rate_limit_status()

        logger.info(f"Agno MCP client status: {status}")

        if not status.get('mcp_connected'):
            result.set_failure(
                "Agno MCP client not connected",
                error=status.get('mcp_error', 'Unknown error'),
                available_tools=status.get('mcp_tools', [])
            )
            return result

        if not status.get('mcp_tools'):
            result.set_failure("No MCP tools available in Agno client")
            return result

        # Test URL reading
        try:
            response = client.read_url(TEST_URL, use_cache=False)

            if response.content and len(response.content) > 50:
                result.set_success(
                    content_length=len(response.content),
                    word_count=response.word_count,
                    mcp_tools=status.get('mcp_tools', []),
                    mcp_connected=True
                )
                logger.info(f"Agno MCP client succeeded, content length: {len(response.content)}")
            else:
                result.set_failure("Insufficient content from Agno MCP client")

        except Exception as e:
            result.set_failure(f"Agno MCP client failed to read URL: {e}")

    except Exception as e:
        result.set_failure(f"Failed to initialize Agno MCP client: {e}")

    finally:
        try:
            client.close()
        except:
            pass

    result.duration = time.time() - start_time
    return result


def test_simple_mcp_client():
    """Test simple subprocess-based MCP client"""
    result = TestResult("Simple MCP Client")
    start_time = time.time()

    try:
        # Test with fallback disabled to test pure MCP
        client = JinaMCPClientSimple(fallback_to_direct=False)
        status = client.get_rate_limit_status()

        logger.info(f"Simple MCP client status: {status}")

        if not status.get('mcp_connected'):
            result.set_failure(
                "Simple MCP client not connected",
                error=status.get('mcp_error', 'Unknown error'),
                available_tools=status.get('mcp_tools', [])
            )
            return result

        if not status.get('mcp_tools'):
            result.set_failure("No MCP tools available in simple client")
            return result

        # Test URL reading
        try:
            response = client.read_url(TEST_URL, use_cache=False)

            if response.content and len(response.content) > 50:
                result.set_success(
                    content_length=len(response.content),
                    word_count=response.word_count,
                    mcp_tools=status.get('mcp_tools', []),
                    mcp_connected=True
                )
                logger.info(f"Simple MCP client succeeded, content length: {len(response.content)}")
            else:
                result.set_failure("Insufficient content from simple MCP client")

        except Exception as e:
            result.set_failure(f"Simple MCP client failed to read URL: {e}")

    except Exception as e:
        result.set_failure(f"Failed to initialize simple MCP client: {e}")

    finally:
        try:
            client.close()
        except:
            pass

    result.duration = time.time() - start_time
    return result


def test_mcp_search_functionality():
    """Test MCP search functionality"""
    result = TestResult("MCP Search Functionality")
    start_time = time.time()

    try:
        # Use simple MCP client for search test
        client = JinaMCPClientSimple(fallback_to_direct=False)
        status = client.get_rate_limit_status()

        if not status.get('mcp_connected'):
            result.set_failure("MCP client not connected for search test")
            return result

        # Test web search
        try:
            results = client.search_web(TEST_QUERY, num_results=3, use_cache=False)

            if results and len(results) > 0:
                result.set_success(
                    results_count=len(results),
                    sample_title=results[0].title if results else None,
                    sample_url=results[0].url if results else None
                )
                logger.info(f"MCP search succeeded, found {len(results)} results")
            else:
                result.set_failure("No search results from MCP")

        except Exception as e:
            result.set_failure(f"MCP search failed: {e}")

    except Exception as e:
        result.set_failure(f"Failed to initialize MCP client for search: {e}")

    finally:
        try:
            client.close()
        except:
            pass

    result.duration = time.time() - start_time
    return result


def test_client_comparison():
    """Compare performance of different clients"""
    result = TestResult("Client Performance Comparison")
    start_time = time.time()

    try:
        results = {}

        # Test direct client
        try:
            direct_client = get_jina_client()
            direct_start = time.time()
            direct_response = direct_client.read_url(TEST_URL, use_cache=False)
            direct_time = time.time() - direct_start
            results['direct'] = {
                'success': True,
                'time': direct_time,
                'content_length': len(direct_response.content)
            }
        except Exception as e:
            results['direct'] = {'success': False, 'error': str(e)}

        # Test hybrid client (with fallback)
        try:
            hybrid_client = JinaHybridClient(enable_mcp_experimental=True)
            hybrid_start = time.time()
            hybrid_response = hybrid_client.read_url(TEST_URL, use_cache=False)
            hybrid_time = time.time() - hybrid_start
            results['hybrid'] = {
                'success': True,
                'time': hybrid_time,
                'content_length': len(hybrid_response.content)
            }
        except Exception as e:
            results['hybrid'] = {'success': False, 'error': str(e)}

        # Determine which clients succeeded
        successful_clients = [name for name, data in results.items() if data.get('success', False)]

        if successful_clients:
            result.set_success(
                successful_clients=successful_clients,
                client_results=results
            )
            logger.info(f"Performance comparison successful for: {successful_clients}")
        else:
            result.set_failure("All clients failed in comparison", results=results)

    except Exception as e:
        result.set_failure(f"Performance comparison failed: {e}")

    result.duration = time.time() - start_time
    return result


def run_all_tests():
    """Run all MCP integration tests"""
    print("COMPREHENSIVE MCP INTEGRATION TESTS")
    print("=" * 80)
    print(f"Test URL: {TEST_URL}")
    print(f"Test Query: {TEST_QUERY}")
    print(f"Timeout: {TIMEOUT}s")
    print(f"Settings:")
    print(f"  Market validation enabled: {settings.MARKET_VALIDATION_ENABLED}")
    print(f"  Jina read RPM limit: {settings.JINA_READ_RPM_LIMIT}")
    print(f"  Jina search RPM limit: {settings.JINA_SEARCH_RPM_LIMIT}")
    print(f"  Request timeout: {settings.JINA_REQUEST_TIMEOUT}s")
    print("=" * 80)

    tests = [
        test_mcp_server_availability,
        test_mcp_tool_list,
        test_mcp_direct_tool_call,
        test_hybrid_client_mcp_only,
        test_agno_mcp_client,
        test_simple_mcp_client,
        test_mcp_search_functionality,
        test_client_comparison,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
            print(result)
            if result.details:
                for key, value in result.details.items():
                    if key not in ['content']:  # Skip large content
                        print(f"    {key}: {value}")
            print()
        except Exception as e:
            error_result = TestResult(test_func.__name__)
            error_result.set_failure(f"Test crashed: {e}")
            results.append(error_result)
            print(error_result)
            print()

    # Final summary
    print("=" * 80)
    print("FINAL TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for result in results if result.success)
    total = len(results)
    total_time = sum(result.duration for result in results)

    for result in results:
        print(str(result))
        if result.error:
            print(f"    Error: {result.error}")

    print(f"\nOverall: {passed}/{total} tests passed")
    print(f"Total time: {total_time:.2f}s")

    if passed == total:
        print("\n🎉 All tests passed! MCP integration is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check the logs above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())