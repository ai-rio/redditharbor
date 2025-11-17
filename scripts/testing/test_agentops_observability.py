#!/usr/bin/env python3
"""
Test AgentOps observability with Jina MCP integration
Demonstrates real-time cost tracking and performance monitoring
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

async def test_agentops_observability():
    """Test AgentOps observability with MCP integration"""

    print("🔍 AGENTOPS OBSERVABILITY TEST WITH JINA MCP INTEGRATION")
    print("=" * 70)

    # Initialize AgentOps with detailed tracking
    try:
        agentops.init(
            api_key=os.environ.get("AGENTOPS_API_KEY"),
            auto_start_session=False,
            tags=["jina-mcp-integration", "hybrid-client", "observability-test"],
            instrument_llm_calls=False  # Manual tracking for better control
        )
        print("✅ AgentOps initialized successfully")
    except Exception as e:
        print(f"❌ AgentOps initialization failed: {e}")
        return

    # Start a detailed trace
    trace = agentops.start_trace(
        "jina_mcp_observability_test",
        tags=["hybrid-client", "market-validation", "cost-tracking"]
    )
    print(f"✅ Started AgentOps trace: {trace}")

    try:
        # Test 1: Hybrid Client with AgentOps tracking
        print("\n📊 TEST 1: HYBRID CLIENT PERFORMANCE TRACKING")
        print("-" * 50)

        hybrid_client = JinaHybridClient(
            enable_mcp_experimental=True
        )

        # Record tool usage events
        agentops.Event("jina_hybrid_client_initialized", {
            "mcp_available": hybrid_client.mcp_available,
            "client_type": hybrid_client.client_type,
            "mcp_status": hybrid_client.mcp_status
        })

        # Test URL reading with performance tracking
        print("Testing URL reading with AgentOps tracking...")
        start_time = asyncio.get_event_loop().time()

        result = await hybrid_client.read_url("https://example.com")

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time

        # Record detailed metrics
        agentops.Event("jina_url_read_completed", {
            "url": "https://example.com",
            "word_count": len(result.get('content', '').split()),
            "title": result.get('title', ''),
            "response_time_seconds": duration,
            "client_type": hybrid_client.client_type,
            "cached": result.get('cached', False),
            "estimated_cost": 0.0001  # Jina API cost estimation
        })

        print(f"✅ URL read completed: {result.get('title', '')} ({duration:.2f}s)")

        # Test web search
        print("Testing web search with AgentOps tracking...")
        start_time = asyncio.get_event_loop().time()

        search_result = await hybrid_client.search("AI agent monitoring tools")

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time

        # Record search metrics
        agentops.Event("jina_web_search_completed", {
            "query": "AI agent monitoring tools",
            "results_count": len(search_result.get('results', [])),
            "response_time_seconds": duration,
            "client_type": hybrid_client.client_type,
            "cached": search_result.get('cached', False),
            "estimated_cost": 0.0005  # Search cost estimation
        })

        print(f"✅ Web search completed: {len(search_result.get('results', []))} results ({duration:.2f}s)")

        # Test 2: Market Data Validator with comprehensive tracking
        print("\n💰 TEST 2: MARKET DATA VALIDATOR COST TRACKING")
        print("-" * 50)

        validator = MarketDataValidator(
            jina_client=hybrid_client,
            model="anthropic/claude-haiku-4.5"
        )

        # Record validator initialization
        agentops.Event("market_data_validator_initialized", {
            "model": validator.model,
            "jina_client_type": type(hybrid_client).__name__,
            "mcp_enabled": hybrid_client.mcp_available
        })

        print("Running market validation with detailed cost tracking...")

        # Track the expensive validation process
        validation_start = asyncio.get_event_loop().time()

        validation_result = await validator.validate_opportunity(
            "expense tracking app for freelancers",
            competitors=["mint.intuit.com", "nerdwallet.com"],
            market_size_keywords=["personal finance software", "freelance tools"]
        )

        validation_end = asyncio.get_event_loop().time()
        validation_duration = validation_end - validation_start

        # Record comprehensive validation metrics
        agentops.Event("market_validation_completed", {
            "opportunity": "expense tracking app for freelancers",
            "validation_score": validation_result.get('validation_score', 0),
            "data_quality_score": validation_result.get('data_quality_score', 0),
            "competitors_analyzed": len(validation_result.get('competitor_analysis', [])),
            "market_data_points": len(validation_result.get('market_size_data', [])),
            "total_cost_estimate": validation_result.get('total_cost', 0),
            "total_duration_seconds": validation_duration,
            "urls_fetched": validation_result.get('urls_fetched', 0),
            "llm_calls_count": validation_result.get('llm_calls', 0),
            "client_type": hybrid_client.client_type
        })

        print(f"✅ Market validation completed:")
        print(f"   Score: {validation_result.get('validation_score', 0)}/100")
        print(f"   Cost: ${validation_result.get('total_cost', 0):.6f}")
        print(f"   Duration: {validation_duration:.2f}s")
        print(f"   URLs fetched: {validation_result.get('urls_fetched', 0)}")

        # Test 3: MCP capability observability
        print("\n🔧 TEST 3: MCP CAPABILITY OBSERVABILITY")
        print("-" * 50)

        # Detailed MCP status reporting
        mcp_status = {
            "mcp_available": hybrid_client.mcp_available,
            "mcp_experimental": hybrid_client.mcp_experimental,
            "mcp_status": hybrid_client.mcp_status,
            "client_type": hybrid_client.client_type,
            "primary_client": hybrid_client.primary_client,
            "mcp_tools": getattr(hybrid_client, 'mcp_tools', [])
        }

        agentops.Event("mcp_capability_assessment", mcp_status)

        print(f"MCP Status: {mcp_status}")

        # Test 4: Cost analysis and breakdown
        print("\n📈 TEST 4: COST ANALYSIS AND BREAKDOWN")
        print("-" * 50)

        # Simulate cost breakdown for different operations
        cost_breakdown = {
            "jina_api_calls": {
                "url_reads": 1,
                "searches": 1,
                "estimated_cost": 0.0006,
                "currency": "USD"
            },
            "llm_analysis": {
                "monetization_analysis": 1,
                "competitor_analysis": validation_result.get('llm_calls', 0),
                "estimated_tokens": 5000,
                "estimated_cost": validation_result.get('total_cost', 0),
                "currency": "USD"
            },
            "total_estimated_cost": validation_result.get('total_cost', 0) + 0.0006
        }

        agentops.Event("cost_breakdown_analysis", cost_breakdown)

        print(f"💰 Cost Breakdown:")
        print(f"   Jina API calls: ${cost_breakdown['jina_api_calls']['estimated_cost']:.6f}")
        print(f"   LLM analysis: ${cost_breakdown['llm_analysis']['estimated_cost']:.6f}")
        print(f"   Total estimated: ${cost_breakdown['total_estimated_cost']:.6f}")

        # End trace successfully
        agentops.end_trace(trace, "Success")
        print(f"✅ AgentOps trace completed successfully")

        # Display summary
        print("\n📊 OBSERVABILITY SUMMARY")
        print("=" * 70)
        print("✅ AgentOps Events Recorded:")
        print("   • jina_hybrid_client_initialized")
        print("   • jina_url_read_completed")
        print("   • jina_web_search_completed")
        print("   • market_data_validator_initialized")
        print("   • market_validation_completed")
        print("   • mcp_capability_assessment")
        print("   • cost_breakdown_analysis")
        print(f"\n🎯 View detailed dashboard at: https://app.agentops.ai/")
        print(f"📈 Trace will be available with: {len(cost_breakdown)} detailed events")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        # End trace with error
        agentops.end_trace(trace, f"Error: {str(e)}")
        raise

    finally:
        # Clean up
        if 'hybrid_client' in locals():
            await hybrid_client.close()

if __name__ == "__main__":
    print("🚀 Starting AgentOps observability test with Jina MCP integration...")
    asyncio.run(test_agentops_observability())
    print("✅ Observability test completed!")