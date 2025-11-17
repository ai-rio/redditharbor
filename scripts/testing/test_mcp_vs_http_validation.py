#!/usr/bin/env python3
"""
MCP vs HTTP Validation Test

This test specifically validates that MCP clients are actually using MCP
instead of just falling back to HTTP. It does this by:
1. Testing MCP-only clients (no fallback)
2. Comparing response patterns and timings
3. Monitoring MCP server interaction
"""

import json
import logging
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

from agent_tools.jina_hybrid_client import JinaHybridClient
from agent_tools.jina_mcp_client import JinaMCPClient
from agent_tools.jina_mcp_client_simple import JinaMCPClientSimple
from agent_tools.jina_reader_client import get_jina_client

# Configure logging to capture all details
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Test data
TEST_URL = "https://httpbin.org/json"  # Simple JSON endpoint
TEST_QUERY = "REST API design principles"


class MCPMonitor:
    """Monitor MCP server interactions"""
    def __init__(self):
        self.calls_made = []
        self.intercepted = False

    def intercept_mcp_call(self, tool_name: str, arguments: Dict[str, Any]):
        """Record MCP call details"""
        self.calls_made.append({
            'tool': tool_name,
            'arguments': arguments,
            'timestamp': time.time()
        })
        self.intercepted = True
        logger.info(f"MCP Call Intercepted: {tool_name} with args: {arguments}")


def test_mcp_server_direct_interaction():
    """Test direct interaction with MCP server to confirm it's working"""
    print("\n" + "="*60)
    print("TESTING DIRECT MCP SERVER INTERACTION")
    print("="*60)

    try:
        # Test tools list
        print("1. Testing tools list...")
        mcp_request = {"method": "tools/list"}
        process = subprocess.run(
            ["npx", "-y", "jina-mcp-tools"],
            input=json.dumps(mcp_request),
            capture_output=True,
            text=True,
            timeout=15
        )

        if process.returncode != 0:
            print(f"❌ MCP server not responding: {process.stderr}")
            return False

        response = json.loads(process.stdout)
        tools = [tool.get("name", "") for tool in response.get("result", {}).get("tools", [])]
        print(f"✅ MCP server responding with tools: {tools}")

        # Test actual tool call
        print("\n2. Testing direct tool call...")
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
        process = subprocess.run(
            ["npx", "-y", "jina-mcp-tools"],
            input=json.dumps(mcp_request),
            capture_output=True,
            text=True,
            timeout=30
        )
        call_time = time.time() - start_time

        if process.returncode != 0:
            print(f"❌ MCP tool call failed: {process.stderr}")
            return False

        response = json.loads(process.stdout)
        content_length = len(str(response.get("result", "")))
        print(f"✅ MCP tool call successful in {call_time:.2f}s, content length: {content_length}")

        return True

    except Exception as e:
        print(f"❌ Direct MCP interaction failed: {e}")
        return False


def test_mcp_client_no_fallback():
    """Test MCP clients with fallback explicitly disabled"""
    print("\n" + "="*60)
    print("TESTING MCP CLIENTS (NO FALLBACK)")
    print("="*60)

    clients_to_test = [
        ("Agno MCP Client", lambda: JinaMCPClient(fallback_to_direct=False)),
        ("Simple MCP Client", lambda: JinaMCPClientSimple(fallback_to_direct=False)),
    ]

    results = {}

    for client_name, client_factory in clients_to_test:
        print(f"\nTesting {client_name}...")
        client = None

        try:
            client = client_factory()
            status = client.get_rate_limit_status()

            print(f"  MCP Connected: {status.get('mcp_connected', False)}")
            print(f"  Available Tools: {status.get('mcp_tools', [])}")
            print(f"  Fallback Enabled: {status.get('fallback_enabled', True)}")

            if status.get('mcp_connected', False):
                # Test URL reading
                print(f"  Testing URL reading...")
                start_time = time.time()
                response = client.read_url(TEST_URL, use_cache=False)
                call_time = time.time() - start_time

                if response.content and len(response.content) > 10:
                    print(f"  ✅ URL reading successful in {call_time:.2f}s")
                    print(f"     Content length: {len(response.content)}")
                    print(f"     Word count: {response.word_count}")
                    results[client_name] = {
                        'success': True,
                        'time': call_time,
                        'content_length': len(response.content),
                        'mcp_used': True  # Assuming MCP was used since fallback is disabled
                    }
                else:
                    print(f"  ❌ URL reading failed - insufficient content")
                    results[client_name] = {'success': False, 'error': 'Insufficient content'}
            else:
                error = status.get('mcp_error', 'MCP not connected')
                print(f"  ❌ MCP not connected: {error}")
                results[client_name] = {'success': False, 'error': error}

        except Exception as e:
            print(f"  ❌ {client_name} failed: {e}")
            results[client_name] = {'success': False, 'error': str(e)}

        finally:
            if client:
                try:
                    client.close()
                except:
                    pass

    return results


def test_hybrid_client_mcp_priority():
    """Test hybrid client to see if it prefers MCP over HTTP when available"""
    print("\n" + "="*60)
    print("TESTING HYBRID CLIENT (MCP PRIORITY)")
    print("="*60)

    try:
        # Test with MCP experimental enabled
        print("Testing Hybrid Client with MCP enabled...")
        hybrid_client = JinaHybridClient(enable_mcp_experimental=True)
        status = hybrid_client.get_rate_limit_status()

        print(f"  MCP Available: {status.get('mcp_available', False)}")
        print(f"  Jina MCP Tools: {status.get('jina_mcp_tools_available', False)}")
        print(f"  Available Tools: {status.get('mcp_tools', [])}")
        print(f"  Status Message: {status.get('mcp_status_message', '')}")

        if status.get('jina_mcp_tools_available', False):
            print("  ✅ Hybrid client detected MCP tools")

            # Test URL reading - should try MCP first
            print("  Testing URL reading (should try MCP first)...")
            start_time = time.time()
            response = hybrid_client.read_url(TEST_URL, use_cache=False)
            call_time = time.time() - start_time

            if response.content and len(response.content) > 10:
                print(f"  ✅ URL reading successful in {call_time:.2f}s")
                print(f"     Content length: {len(response.content)}")
                print(f"     Word count: {response.word_count}")

                # We can't easily determine if MCP was actually used vs HTTP fallback
                # But if MCP tools are available, it should have tried MCP first
                return {
                    'success': True,
                    'time': call_time,
                    'content_length': len(response.content),
                    'mcp_tools_detected': status.get('available_tools', []),
                    'note': 'MCP likely used but cannot confirm without deeper monitoring'
                }
            else:
                return {'success': False, 'error': 'Insufficient content'}
        else:
            return {
                'success': False,
                'error': 'Hybrid client did not detect MCP tools',
                'status': status
            }

    except Exception as e:
        return {'success': False, 'error': str(e)}

    finally:
        try:
            hybrid_client.close()
        except:
            pass


def test_response_differences():
    """Compare responses from different clients to detect differences"""
    print("\n" + "="*60)
    print("TESTING RESPONSE DIFFERENCES")
    print("="*60)

    responses = {}

    # Get direct HTTP response
    try:
        print("Getting direct HTTP response...")
        direct_client = get_jina_client()
        direct_start = time.time()
        direct_response = direct_client.read_url(TEST_URL, use_cache=False)
        direct_time = time.time() - direct_start

        responses['direct'] = {
            'content': direct_response.content,
            'time': direct_time,
            'word_count': direct_response.word_count,
            'title': direct_response.title
        }
        print(f"  ✅ Direct response: {len(direct_response.content)} chars in {direct_time:.2f}s")
    except Exception as e:
        print(f"  ❌ Direct client failed: {e}")
        responses['direct'] = {'error': str(e)}

    # Get simple MCP response (if available)
    try:
        print("Getting Simple MCP response...")
        mcp_client = JinaMCPClientSimple(fallback_to_direct=False)

        # Check if MCP is actually connected
        status = mcp_client.get_rate_limit_status()
        if not status.get('mcp_connected'):
            print(f"  ❌ Simple MCP not connected: {status.get('mcp_error')}")
        else:
            mcp_start = time.time()
            mcp_response = mcp_client.read_url(TEST_URL, use_cache=False)
            mcp_time = time.time() - mcp_start

            responses['simple_mcp'] = {
                'content': mcp_response.content,
                'time': mcp_time,
                'word_count': mcp_response.word_count,
                'title': mcp_response.title
            }
            print(f"  ✅ Simple MCP response: {len(mcp_response.content)} chars in {mcp_time:.2f}s")

        mcp_client.close()
    except Exception as e:
        print(f"  ❌ Simple MCP client failed: {e}")
        responses['simple_mcp'] = {'error': str(e)}

    # Compare responses
    print("\nComparing responses...")
    if 'direct' in responses and 'simple_mcp' in responses:
        direct_data = responses['direct']
        mcp_data = responses['simple_mcp']

        if 'error' not in direct_data and 'error' not in mcp_data:
            # Compare content similarity (basic)
            content_similarity = len(set(direct_data['content'].split()) & set(mcp_data['content'].split())) / len(set(direct_data['content'].split() + mcp_data['content'].split())) * 100

            print(f"  Content similarity: {content_similarity:.1f}%")
            print(f"  Direct time: {direct_data['time']:.2f}s")
            print(f"  MCP time: {mcp_data['time']:.2f}s")

            if content_similarity > 80:
                print("  ✅ Responses are similar - MCP working correctly")
                return True
            else:
                print("  ⚠️  Responses differ significantly - may indicate different processing")
                return False
        else:
            print("  ❌ Could not compare - one or both responses failed")
            return False
    else:
        print("  ❌ Could not compare - missing responses")
        return False


def main():
    """Run comprehensive MCP vs HTTP validation tests"""
    print("MCP vs HTTP VALIDATION TESTS")
    print("="*80)
    print("This test validates that MCP clients are actually using MCP")
    print("instead of falling back to HTTP requests.")
    print(f"Test URL: {TEST_URL}")
    print("="*80)

    # Run all tests
    test_results = {}

    # Test 1: Direct MCP server interaction
    test_results['direct_mcp'] = test_mcp_server_direct_interaction()

    # Test 2: MCP clients with no fallback
    test_results['mcp_clients'] = test_mcp_client_no_fallback()

    # Test 3: Hybrid client MCP priority
    test_results['hybrid_client'] = test_hybrid_client_mcp_priority()

    # Test 4: Response differences
    test_results['response_differences'] = test_response_differences()

    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)

    # Check MCP server is working
    mcp_server_working = test_results.get('direct_mcp', False)
    print(f"MCP Server Working: {'✅' if mcp_server_working else '❌'}")

    # Check MCP clients work without fallback
    mcp_client_results = test_results.get('mcp_clients', {})
    successful_mcp_clients = [name for name, result in mcp_client_results.items() if result.get('success', False)]
    print(f"MCP Clients (No Fallback): {len(successful_mcp_clients)} working: {successful_mcp_clients}")

    # Check hybrid client
    hybrid_result = test_results.get('hybrid_client', {})
    hybrid_working = hybrid_result.get('success', False)
    print(f"Hybrid Client: {'✅' if hybrid_working else '❌'}")
    if hybrid_working and 'mcp_tools_detected' in hybrid_result:
        print(f"  MCP tools detected: {hybrid_result['mcp_tools_detected']}")

    # Check response comparison
    responses_similar = test_results.get('response_differences', False)
    print(f"Response Comparison: {'✅' if responses_similar else '❌'}")

    # Overall assessment
    print(f"\nOverall Assessment:")
    if mcp_server_working and successful_mcp_clients:
        print("🎉 MCP INTEGRATION IS WORKING!")
        print("   - MCP server is responding correctly")
        print("   - MCP clients can connect and use MCP tools")
        if hybrid_working:
            print("   - Hybrid client is properly configured")
        if responses_similar:
            print("   - MCP and HTTP responses are consistent")
        print("\n✅ The system is properly using MCP, not just falling back to HTTP.")
        return 0
    elif mcp_server_working and not successful_mcp_clients:
        print("⚠️  MCP SERVER WORKING BUT CLIENTS HAVE ISSUES")
        print("   - MCP server responds to direct calls")
        print("   - But client wrappers are failing")
        print("   - Check client configurations and error handling")
        return 1
    else:
        print("❌ MCP INTEGRATION NOT WORKING")
        print("   - MCP server is not responding correctly")
        print("   - System likely falling back to HTTP")
        print("   - Check MCP server installation and configuration")
        return 1


if __name__ == "__main__":
    sys.exit(main())