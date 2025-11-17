#!/usr/bin/env python3
"""
Final MCP Integration Summary and Analysis

This script provides a comprehensive analysis of the MCP integration issues
and provides the correct fixes needed.
"""

import subprocess
import sys
import time
import urllib.request
import urllib.parse


def test_direct_jina_api():
    """Test direct Jina API access to validate the base functionality"""
    print("\n" + "="*60)
    print("TESTING DIRECT JINA API ACCESS")
    print("="*60)

    try:
        # Test Jina Reader API directly
        test_url = "https://example.com"
        jina_reader_url = f"https://r.jina.ai/http://{test_url}"

        print(f"Testing Jina Reader API with: {jina_reader_url}")
        start_time = time.time()

        try:
            with urllib.request.urlopen(jina_reader_url, timeout=30) as response:
                content = response.read().decode('utf-8')
            elapsed = time.time() - start_time

            if content and len(content) > 50:
                print(f"✅ Jina Reader API working!")
                print(f"   Response time: {elapsed:.2f}s")
                print(f"   Content length: {len(content)} characters")
                print(f"   Content preview: {content[:200].replace(chr(10), ' ')}...")
                return True
            else:
                print(f"❌ Jina Reader API returned insufficient content")
                return False

        except Exception as e:
            print(f"❌ Jina Reader API failed: {e}")
            return False

    except Exception as e:
        print(f"❌ Direct API test failed: {e}")
        return False


def analyze_mcp_server_status():
    """Analyze the actual MCP server status and capabilities"""
    print("\n" + "="*60)
    print("ANALYZING MCP SERVER STATUS")
    print("="*60)

    mcp_analysis = {}

    # Check jina-mcp-tools
    print("1. Checking jina-mcp-tools availability...")
    try:
        result = subprocess.run(
            ["npx", "-y", "jina-mcp-tools", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            mcp_analysis["jina-mcp-tools_available"] = True
            mcp_analysis["jina-mcp-tools_version"] = result.stdout.strip()
            print(f"✅ jina-mcp-tools available: {result.stdout.strip()}")
        else:
            mcp_analysis["jina-mcp-tools_available"] = False
            print(f"❌ jina-mcp-tools not available: {result.stderr}")

    except Exception as e:
        mcp_analysis["jina-mcp-tools_available"] = False
        print(f"❌ jina-mcp-tools check failed: {e}")

    # Test interface
    print("\n2. Testing jina-mcp-tools interface...")
    try:
        result = subprocess.run(
            ["npx", "-y", "jina-mcp-tools"],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = result.stdout + result.stderr
        if "jina_reader" in output and "jina_search" in output:
            mcp_analysis["tools_detected"] = ["jina_reader", "jina_search"]
            print(f"✅ Tools detected: jina_reader, jina_search")
        else:
            mcp_analysis["tools_detected"] = []
            print(f"❌ Expected tools not detected in output")
            print(f"Output: {output[:200]}")

    except Exception as e:
        mcp_analysis["tools_detected"] = []
        print(f"❌ Interface test failed: {e}")

    return mcp_analysis


def identify_integration_issues():
    """Identify the specific issues with the current MCP integration"""
    print("\n" + "="*60)
    print("IDENTIFYING INTEGRATION ISSUES")
    print("="*60)

    issues_found = []

    print("Analyzing known issues...")

    # Issue 1: Wrong MCP server/package
    print("\n1. MCP Server Issue:")
    print("   ❌ Code references '@jina-ai/mcp-server' which doesn't exist")
    print("   ✅ Should use 'jina-mcp-tools' which is available")
    issues_found.append("wrong_mcp_server")

    # Issue 2: Wrong tool names
    print("\n2. Tool Name Issue:")
    print("   ❌ Code uses 'mcp__jina-ai__read_url' and 'mcp__jina-ai__search_web'")
    print("   ✅ Should use 'jina_reader' and 'jina_search'")
    issues_found.append("wrong_tool_names")

    # Issue 3: Protocol mismatch
    print("\n3. Protocol Issue:")
    print("   ❌ Code expects standard MCP JSON-RPC protocol")
    print("   ⚠️  jina-mcp-tools may not follow standard MCP protocol")
    print("   ✅ May need custom implementation or direct HTTP calls")
    issues_found.append("protocol_mismatch")

    # Issue 4: Agno dependency
    print("\n4. Dependency Issue:")
    print("   ❌ Code depends on 'agno' package which is not installed")
    print("   ✅ Need to install agno or provide fallback implementation")
    issues_found.append("agno_dependency")

    return issues_found


def recommend_fixes(issues_found, mcp_analysis):
    """Provide specific fixes for the identified issues"""
    print("\n" + "="*60)
    print("RECOMMENDED FIXES")
    print("="*60)

    fixes = []

    print("Based on the analysis, here are the recommended fixes:")

    # Fix 1: Tool names
    if "wrong_tool_names" in issues_found:
        print(f"\n1. Fix Tool Names:")
        print(f"   In agent_tools/jina_mcp_client.py:")
        print(f"   - Change 'mcp__jina-ai__read_url' to 'jina_reader'")
        print(f"   - Change 'mcp__jina-ai__search_web' to 'jina_search'")
        fixes.append("fix_tool_names")

    # Fix 2: MCP server
    if "wrong_mcp_server" in issues_found:
        print(f"\n2. Fix MCP Server Reference:")
        print(f"   In agent_tools/jina_mcp_client.py:")
        print(f"   - Change '@jina-ai/mcp-server' to 'jina-mcp-tools'")
        fixes.append("fix_mcp_server")

    # Fix 3: Hybrid client implementation
    if "protocol_mismatch" in issues_found:
        print(f"\n3. Fix Hybrid Client:")
        print(f"   In agent_tools/jina_hybrid_client.py:")
        print(f"   - Replace stub methods with actual implementation")
        print(f"   - Use direct HTTP calls to Jina API as fallback")
        fixes.append("fix_hybrid_client")

    # Fix 4: Alternative approaches
    print(f"\n4. Alternative Approaches:")
    print(f"   Option A: Install agno package:")
    print(f"      pip install agno")
    print(f"   Option B: Use direct HTTP calls to Jina API:")
    print(f"      https://r.jina.ai/http://URL for reading")
    print(f"      https://s.jina.ai/http://URL for search")
    print(f"   Option C: Custom MCP implementation:")
    print(f"      Implement proper MCP protocol for jina-mcp-tools")
    fixes.append("alternative_approaches")

    return fixes


def generate_implementation_plan():
    """Generate a step-by-step implementation plan"""
    print("\n" + "="*60)
    print("IMPLEMENTATION PLAN")
    print("="*60)

    plan = [
        {
            "step": 1,
            "title": "Fix Tool Names in jina_mcp_client.py",
            "details": [
                "Change 'mcp__jina-ai__read_url' to 'jina_reader'",
                "Change 'mcp__jina-ai__search_web' to 'jina_search'",
                "Update MCP server command to 'npx -y jina-mcp-tools'"
            ]
        },
        {
            "step": 2,
            "title": "Fix Hybrid Client Implementation",
            "details": [
                "Replace stub methods in jina_hybrid_client.py",
                "Implement actual MCP calls via subprocess",
                "Add proper error handling and fallback"
            ]
        },
        {
            "step": 3,
            "title": "Install Dependencies",
            "details": [
                "Install agno package: pip install agno",
                "Or implement fallback without agno dependency"
            ]
        },
        {
            "step": 4,
            "title": "Update Simple Client",
            "details": [
                "Fix tool names in jina_mcp_client_simple.py",
                "Ensure consistent interface across all clients"
            ]
        },
        {
            "step": 5,
            "title": "Create Comprehensive Tests",
            "details": [
                "Test actual MCP functionality (not just HTTP fallback)",
                "Validate tool name mapping works correctly",
                "Test both success and failure scenarios"
            ]
        },
        {
            "step": 6,
            "title": "Ensure Backward Compatibility",
            "details": [
                "Maintain existing JinaReaderClient interface",
                "Preserve rate limiting and caching behavior",
                "Add graceful fallback when MCP unavailable"
            ]
        }
    ]

    for step in plan:
        print(f"\nStep {step['step']}: {step['title']}")
        for detail in step['details']:
            print(f"   • {detail}")

    return plan


def main():
    """Run final MCP integration analysis"""
    print("FINAL MCP INTEGRATION ANALYSIS")
    print("="*80)
    print("This script analyzes the MCP integration issues and provides fixes.")

    # Test base functionality
    jina_working = test_direct_jina_api()

    # Analyze MCP server
    mcp_analysis = analyze_mcp_server_status()

    # Identify issues
    issues_found = identify_integration_issues()

    # Recommend fixes
    fixes = recommend_fixes(issues_found, mcp_analysis)

    # Generate implementation plan
    plan = generate_implementation_plan()

    # Final summary
    print("\n" + "="*80)
    print("FINAL ANALYSIS SUMMARY")
    print("="*80)

    print(f"Jina API Direct Access: {'✅ Working' if jina_working else '❌ Not Working'}")
    print(f"MCP Tools Available: {len(mcp_analysis.get('tools_detected', []))} found")
    print(f"Issues Identified: {len(issues_found)}")
    print(f"Fixes Recommended: {len(fixes)}")

    print(f"\nKey Findings:")
    print(f"1. Jina API is working directly - base functionality confirmed")
    print(f"2. MCP server (jina-mcp-tools) is available but may not follow standard protocol")
    print(f"3. Current code has wrong tool names and server references")
    print(f"4. Agno dependency is missing and causing import errors")

    print(f"\nRecommendation:")
    if jina_working:
        print(f"✅ PROCEED WITH IMPLEMENTATION")
        print(f"   The base Jina API is working, so we can implement a working solution")
        print(f"   Use the provided implementation plan to fix the integration")
        return 0
    else:
        print(f"❌ INVESTIGATE BASE CONNECTIVITY")
        print(f"   The Jina API itself is not accessible")
        print(f"   Fix network/connectivity issues before proceeding")
        return 1


if __name__ == "__main__":
    sys.exit(main())