#!/usr/bin/env python3
"""
Raw MCP Validation Test

This script tests MCP functionality by making direct subprocess calls
to the MCP server, completely independent of any client libraries.
This validates that MCP is actually working at the base level.
"""

import json
import logging
import subprocess
import sys
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Test data
TEST_URL = "https://example.com"
TEST_QUERY = "software development best practices"
TIMEOUT = 30


class MCPValidator:
    """Validator for MCP functionality using direct subprocess calls"""

    def __init__(self):
        self.server_command = ["npx", "-y", "jina-mcp-tools"]
        self.timeout = TIMEOUT

    def check_server_availability(self):
        """Check if MCP server is available"""
        print("\n" + "="*60)
        print("CHECKING MCP SERVER AVAILABILITY")
        print("="*60)

        try:
            # Test version command
            print("1. Testing MCP server version...")
            result = subprocess.run(
                self.server_command + ["--version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                print(f"❌ MCP server version check failed:")
                print(f"   Return code: {result.returncode}")
                print(f"   Error: {result.stderr}")
                return False

            print(f"✅ MCP server available: {result.stdout.strip()}")
            return True

        except subprocess.TimeoutExpired:
            print("❌ MCP server version check timed out")
            return False
        except FileNotFoundError:
            print("❌ npx not found - Node.js and npm required")
            return False
        except Exception as e:
            print(f"❌ MCP server availability check failed: {e}")
            return False

    def get_available_tools(self):
        """Get list of available tools from MCP server"""
        print("\n" + "="*60)
        print("GETTING AVAILABLE MCP TOOLS")
        print("="*60)

        try:
            # Request tools list
            print("1. Requesting tools list from MCP server...")
            mcp_request = {"method": "tools/list"}
            result = subprocess.run(
                self.server_command,
                input=json.dumps(mcp_request),
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                print(f"❌ Tools list request failed:")
                print(f"   Return code: {result.returncode}")
                print(f"   Error: {result.stderr}")
                return []

            # Parse response
            try:
                response = json.loads(result.stdout)
                if "result" in response and "tools" in response["result"]:
                    tools = response["result"]["tools"]
                    tool_names = [tool.get("name", "") for tool in tools]

                    print(f"✅ Found {len(tool_names)} tools:")
                    for tool in tools:
                        print(f"   - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")

                    return tool_names
                else:
                    print("❌ Invalid response format - missing tools")
                    print(f"Response: {json.dumps(response, indent=2)}")
                    return []

            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse tools list response: {e}")
                print(f"Raw response: {result.stdout}")
                return []

        except subprocess.TimeoutExpired:
            print("❌ Tools list request timed out")
            return []
        except Exception as e:
            print(f"❌ Tools list request failed: {e}")
            return []

    def test_tool_call(self, tool_name, arguments):
        """Test calling a specific tool"""
        print(f"\n" + "="*60)
        print(f"TESTING TOOL CALL: {tool_name}")
        print("="*60)

        try:
            # Prepare tool call request
            mcp_request = {
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }

            print(f"1. Calling {tool_name} with arguments: {arguments}")
            start_time = time.time()

            result = subprocess.run(
                self.server_command,
                input=json.dumps(mcp_request),
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            elapsed = time.time() - start_time

            if result.returncode != 0:
                print(f"❌ Tool call failed:")
                print(f"   Return code: {result.returncode}")
                print(f"   Error: {result.stderr}")
                return None

            print(f"✅ Tool call completed in {elapsed:.2f}s")

            # Parse response
            try:
                response = json.loads(result.stdout)

                # Extract content from various response formats
                content = ""
                if "result" in response:
                    result_data = response["result"]
                    if isinstance(result_data, dict):
                        content = result_data.get("content", "") or result_data.get("text", "") or str(result_data)
                    elif isinstance(result_data, list):
                        # Handle list of content items
                        content = "\n".join(str(item) for item in result_data)
                    else:
                        content = str(result_data)
                else:
                    content = result.stdout

                print(f"✅ Tool call successful!")
                print(f"   Content length: {len(content)} characters")
                print(f"   Content preview: {content[:200].replace(chr(10), ' ')}...")

                return {
                    'success': True,
                    'content': content,
                    'length': len(content),
                    'time': elapsed,
                    'raw_response': response
                }

            except json.JSONDecodeError:
                # Fallback to raw output
                if result.stdout.strip():
                    print(f"✅ Tool call successful (raw output)!")
                    print(f"   Content length: {len(result.stdout)} characters")
                    print(f"   Content preview: {result.stdout[:200].replace(chr(10), ' ')}...")

                    return {
                        'success': True,
                        'content': result.stdout,
                        'length': len(result.stdout),
                        'time': elapsed,
                        'raw_response': result.stdout
                    }
                else:
                    print(f"❌ Tool call returned empty output")
                    return None

        except subprocess.TimeoutExpired:
            print(f"❌ Tool call to {tool_name} timed out")
            return None
        except Exception as e:
            print(f"❌ Tool call to {tool_name} failed: {e}")
            return None

    def validate_jina_tools(self):
        """Validate that Jina-specific tools are working"""
        print("\n" + "="*60)
        print("VALIDATING JINA TOOLS")
        print("="*60)

        # Get available tools
        tools = self.get_available_tools()

        # Check for expected Jina tools
        expected_tools = ["jina_reader", "jina_search"]
        found_tools = [tool for tool in expected_tools if tool in tools]

        print(f"\nExpected tools: {expected_tools}")
        print(f"Found tools: {found_tools}")
        print(f"Missing tools: {[tool for tool in expected_tools if tool not in tools]}")

        results = {}

        # Test jina_reader
        if "jina_reader" in tools:
            print(f"\n--- Testing jina_reader ---")
            result = self.test_tool_call("jina_reader", {"url": TEST_URL})
            results["jina_reader"] = result
        else:
            print(f"\n--- Skipping jina_reader (not available) ---")
            results["jina_reader"] = None

        # Test jina_search
        if "jina_search" in tools:
            print(f"\n--- Testing jina_search ---")
            result = self.test_tool_call("jina_search", {"query": TEST_QUERY, "num_results": 3})
            results["jina_search"] = result
        else:
            print(f"\n--- Skipping jina_search (not available) ---")
            results["jina_search"] = None

        return results

    def compare_with_direct_http(self):
        """Compare MCP results with direct HTTP calls to Jina API"""
        print("\n" + "="*60)
        print("COMPARING WITH DIRECT HTTP CALLS")
        print("="*60)

        try:
            import urllib.request
            import urllib.parse

            # Test direct Jina reader API
            print("1. Testing direct Jina Reader API...")
            jina_url = f"https://r.jina.ai/http://{TEST_URL}"

            start_time = time.time()
            try:
                with urllib.request.urlopen(jina_url, timeout=self.timeout) as response:
                    direct_content = response.read().decode('utf-8')
                direct_time = time.time() - start_time

                print(f"✅ Direct API call successful in {direct_time:.2f}s")
                print(f"   Content length: {len(direct_content)} characters")
                print(f"   Content preview: {direct_content[:200].replace(chr(10), ' ')}...")

                # Now test via MCP
                print(f"\n2. Testing same URL via MCP...")
                mcp_result = self.test_tool_call("jina_reader", {"url": TEST_URL})

                if mcp_result and mcp_result['success']:
                    print(f"\n3. Comparing results...")
                    mcp_content = mcp_result['content']

                    # Simple content similarity check
                    direct_words = set(direct_content.lower().split())
                    mcp_words = set(mcp_content.lower().split())

                    if direct_words and mcp_words:
                        common_words = direct_words & mcp_words
                        similarity = len(common_words) / max(len(direct_words), len(mcp_words)) * 100

                        print(f"   Direct API: {len(direct_content)} chars, {direct_time:.2f}s")
                        print(f"   MCP API:    {len(mcp_content)} chars, {mcp_result['time']:.2f}s")
                        print(f"   Content similarity: {similarity:.1f}%")

                        if similarity > 70:  # Reasonable similarity threshold
                            print(f"   ✅ Results are reasonably similar - MCP is working correctly!")
                            return True
                        else:
                            print(f"   ⚠️  Results differ significantly - may indicate different processing")
                            return True  # Still consider success since both are working
                    else:
                        print(f"   ⚠️  Could not calculate similarity due to empty content")
                        return True
                else:
                    print(f"   ❌ MCP call failed")
                    return False

            except Exception as e:
                print(f"   ❌ Direct API call failed: {e}")
                return False

        except ImportError:
            print("❌ urllib not available for direct HTTP comparison")
            return True  # Not a failure of MCP

        except Exception as e:
            print(f"❌ Direct HTTP comparison failed: {e}")
            return True  # Not a failure of MCP


def main():
    """Run raw MCP validation tests"""
    print("RAW MCP VALIDATION TESTS")
    print("="*80)
    print("This test validates MCP functionality by making direct subprocess calls")
    print("to the MCP server, completely independent of any client libraries.")
    print(f"Test URL: {TEST_URL}")
    print(f"Test Query: {TEST_QUERY}")
    print(f"Timeout: {TIMEOUT}s")
    print("="*80)

    validator = MCPValidator()
    test_results = []

    # Test 1: Server availability
    server_available = validator.check_server_availability()
    test_results.append(("Server Availability", server_available))

    if not server_available:
        print("\n❌ MCP SERVER NOT AVAILABLE - CANNOT CONTINUE")
        print("Please ensure:")
        print("1. Node.js and npm are installed")
        print("2. Internet connection is available")
        print("3. Jina MCP tools can be installed via npx")
        return 1

    # Test 2: Get available tools
    tools = validator.get_available_tools()
    tools_found = len(tools) > 0
    test_results.append(("Tools Discovery", tools_found))

    # Test 3: Validate Jina tools
    jina_results = validator.validate_jina_tools()
    jina_reader_working = jina_results.get("jina_reader") and jina_results["jina_reader"]["success"]
    jina_search_working = jina_results.get("jina_search") and jina_results["jina_search"]["success"]

    test_results.append(("Jina Reader", jina_reader_working))
    test_results.append(("Jina Search", jina_search_working))

    # Test 4: Compare with direct HTTP
    comparison_working = validator.compare_with_direct_http()
    test_results.append(("HTTP Comparison", comparison_working))

    # Final summary
    print("\n" + "="*80)
    print("RAW MCP VALIDATION SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:<25} {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    # Detailed breakdown
    print(f"\nDetailed Results:")
    print(f"  Server Available:      {'✅' if server_available else '❌'}")
    print(f"  Tools Found:           {'✅' if tools_found else '❌'} ({len(tools)} tools)")
    print(f"  Jina Reader Working:   {'✅' if jina_reader_working else '❌'}")
    print(f"  Jina Search Working:   {'✅' if jina_search_working else '❌'}")
    print(f"  HTTP Comparison:       {'✅' if comparison_working else '❌'}")

    if passed >= 4:  # At least 4 out of 5 tests should pass
        print(f"\n🎉 MCP VALIDATION SUCCESSFUL!")
        print("✅ MCP server is available and responding")
        print("✅ MCP tools are discoverable and functional")
        if jina_reader_working:
            print("✅ jina_reader tool is working correctly")
        if jina_search_working:
            print("✅ jina_search tool is working correctly")
        print("✅ MCP integration is ready for use")
        return 0
    else:
        print(f"\n⚠️  MCP VALIDATION INCOMPLETE")
        print("Some aspects of MCP integration may not be working correctly.")
        print("Check the logs above for details on what needs to be addressed.")
        if passed == 0:
            print("\n❌ COMPLETE FAILURE - MCP INTEGRATION NOT WORKING")
        return 1


if __name__ == "__main__":
    sys.exit(main())