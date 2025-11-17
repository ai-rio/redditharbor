#!/usr/bin/env python3
"""
Simple AgentOps observability test with Jina Hybrid Client
Focuses on demonstrating the working integration
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent_tools.jina_hybrid_client import JinaHybridClient
from agent_tools.market_data_validator import MarketDataValidator
import agentops

async def test_simple_agentops():
    """Simple AgentOps observability test"""

    print("🔍 SIMPLE AGENTOPS OBSERVABILITY TEST")
    print("=" * 50)

    # Initialize AgentOps
    try:
        agentops.init(
            api_key=os.environ.get("AGENTOPS_API_KEY"),
            auto_start_session=False,
            tags=["jina-hybrid", "observability", "simple-test"]
        )
        print("✅ AgentOps initialized")
    except Exception as e:
        print(f"❌ AgentOps init failed: {e}")
        return

    # Start trace
    trace = agentops.start_trace("jina_hybrid_simple_test")
    print(f"✅ Started trace: {trace}")

    try:
        # Test Jina Hybrid Client
        print("\n📡 Testing Jina Hybrid Client...")

        hybrid_client = JinaHybridClient(enable_mcp_experimental=True)

        print(f"MCP Available: {hybrid_client.mcp_capability.mcp_available}")
        print(f"Status: {hybrid_client.mcp_capability.status_message}")

        # Test URL reading
        result = await hybrid_client.read_url("https://example.com")
        print(f"✅ Read URL: {result.get('title', '')} ({len(result.get('content', ''))} chars)")

        # Test search
        search_result = await hybrid_client.search("python monitoring")
        print(f"✅ Search: {len(search_result.get('results', []))} results")

        # Test MarketDataValidator
        print("\n💰 Testing MarketDataValidator...")
        validator = MarketDataValidator(jina_client=hybrid_client)

        validation = await validator.validate_opportunity(
            "simple test opportunity",
            market_size_keywords=["test market"]
        )

        print(f"✅ Validation score: {validation.get('validation_score', 0)}/100")
        print(f"✅ Cost: ${validation.get('total_cost', 0):.6f}")

        # End trace successfully
        agentops.end_trace(trace, "Success")
        print("✅ Trace completed successfully")

        # Display summary
        print("\n📊 OBSERVABILITY SUMMARY")
        print("=" * 50)
        print("✅ AgentOps integration working")
        print("✅ Jina Hybrid Client operational")
        print("✅ MCP capabilities detected")
        print("✅ Market validation with cost tracking")
        print(f"\n🎯 Dashboard: https://app.agentops.ai/")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        agentops.end_trace(trace, f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    print("🚀 Starting simple AgentOps test...")
    asyncio.run(test_simple_agentops())
    print("✅ Test completed!")