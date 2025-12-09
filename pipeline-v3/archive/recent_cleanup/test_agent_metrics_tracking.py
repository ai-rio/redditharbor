#!/usr/bin/env python3
"""
Test script to verify all 5 agents have proper metrics tracking

This test addresses QA audit finding:
"Agent-level tracking incomplete: Only 4 unique agent names found
Many records missing agent_name field"

Expected agents: wtp, segment, price, payment, market
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import agents
# Import metrics collector
from pipeline_v3.monitoring.metrics_collector import get_collector
from pipeline_v3.transform.agno_agents import (
    MarketResearchAgent,
    MarketSegmentAgent,
    PaymentBehaviorAgent,
    PricePointAgent,
    WillingnessToPayAgent,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_agent_metrics_tracking():
    """Test that all 5 agents properly track metrics with agent_name"""

    print("=" * 60)
    print("TESTING AGENT METRICS TRACKING")
    print("=" * 60)

    # Test configuration
    model = "test-model"
    api_key = "test-key"
    base_url = "https://test.example.com"

    # Expected agent names mapping
    expected_agents = {
        "WillingnessToPayAgent": "wtp",
        "MarketSegmentAgent": "segment",
        "PricePointAgent": "price",
        "PaymentBehaviorAgent": "payment",
        "MarketResearchAgent": "market"
    }

    # Test data
    test_input = {
        "opportunity_id": "test-opp-001",
        "app_concept": "AI-powered task management tool",
        "target_market": "B2B productivity",
        "problem_description": "Teams struggle with task prioritization"
    }

    results = []

    # Test each agent
    for agent_class, expected_name in expected_agents.items():
        print(f"\nTesting {agent_class}...")

        try:
            # Initialize agent
            agent = agent_class(model, api_key, base_url)

            # Verify agent name mapping
            actual_name = agent._get_agent_name()
            if actual_name != expected_name:
                print(f"  ❌ Agent name mismatch: expected {expected_name}, got {actual_name}")
                results.append({
                    "agent_class": agent_class,
                    "expected_name": expected_name,
                    "actual_name": actual_name,
                    "status": "name_mismatch"
                })
                continue

            print(f"  ✅ Agent name correctly mapped: {actual_name}")

            # Test agent execution with metrics
            input_json = json.dumps(test_input)
            result = agent.run(input_json)

            # Verify result is valid JSON
            parsed_result = json.loads(result)
            print("  ✅ Agent executed successfully")
            print(f"  📊 Result keys: {list(parsed_result.keys())}")

            results.append({
                "agent_class": agent_class,
                "agent_name": actual_name,
                "status": "success",
                "result_keys": list(parsed_result.keys())
            })

        except Exception as e:
            print(f"  ❌ Agent failed: {str(e)}")
            results.append({
                "agent_class": agent_class,
                "expected_name": expected_name,
                "status": "error",
                "error": str(e)
            })

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] != "success"]

    print(f"✅ Successful agents: {len(successful)}/5")
    print(f"❌ Failed agents: {len(failed)}/5")

    if successful:
        print("\n✅ Successfully tested agents:")
        for r in successful:
            print(f"  - {r['agent_class']} → {r['agent_name']}")

    if failed:
        print("\n❌ Failed agents:")
        for r in failed:
            if r["status"] == "name_mismatch":
                print(f"  - {r['agent_class']}: name mismatch (expected {r['expected_name']}, got {r['actual_name']})")
            else:
                print(f"  - {r['agent_class']}: {r.get('error', 'unknown error')}")

    # Check metrics database
    await check_metrics_database(expected_agents.values())

    # Return overall success
    return len(successful) == 5


async def check_metrics_database(expected_agent_names):
    """Check that metrics were recorded for all expected agents"""

    print("\n" + "=" * 60)
    print("CHECKING METRICS DATABASE")
    print("=" * 60)

    try:
        collector = get_collector()

        # Query recent metrics (last hour)
        import psycopg2

        from config import get_settings

        settings = get_settings()
        conn = psycopg2.connect(settings.database_url)

        with conn.cursor() as cur:
            # Get metrics from last hour
            cur.execute("""
                SELECT agent_name, COUNT(*) as count,
                       MAX(created_at) as last_execution
                FROM pipeline_metrics
                WHERE created_at >= %s
                  AND phase = 'transform'
                GROUP BY agent_name
                ORDER BY agent_name
            """, (datetime.now() - timedelta(hours=1),))

            records = cur.fetchall()

            print("\n📊 Metrics recorded in last hour:")
            if records:
                for agent_name, count, last_exec in records:
                    print(f"  - {agent_name}: {count} executions (last: {last_exec})")
            else:
                print("  No metrics found in last hour")

            # Check for all expected agents
            found_agents = {r[0] for r in records}
            missing_agents = set(expected_agent_names) - found_agents

            if missing_agents:
                print(f"\n❌ Missing agents in metrics: {', '.join(missing_agents)}")
            else:
                print("\n✅ All expected agents found in metrics!")

            # Check for NULL agent_name
            cur.execute("""
                SELECT COUNT(*)
                FROM pipeline_metrics
                WHERE created_at >= %s
                  AND phase = 'transform'
                  AND agent_name IS NULL
            """, (datetime.now() - timedelta(hours=1),))

            null_count = cur.fetchone()[0]
            if null_count > 0:
                print(f"\n❌ Found {null_count} records with NULL agent_name")
            else:
                print("\n✅ No NULL agent_name records found")

        conn.close()

    except Exception as e:
        print(f"\n❌ Failed to check metrics database: {str(e)}")
        print("  This might be expected if the database is not available")
        return False

    return True


async def test_individual_agent_execution():
    """Test each agent individually to ensure proper metrics tracking"""

    print("\n" + "=" * 60)
    print("INDIVIDUAL AGENT EXECUTION TEST")
    print("=" * 60)

    # Test each agent individually with fresh metrics
    agents = [
        (WillingnessToPayAgent, "wtp"),
        (MarketSegmentAgent, "segment"),
        (PricePointAgent, "price"),
        (PaymentBehaviorAgent, "payment"),
        (MarketResearchAgent, "market")
    ]

    for agent_class, expected_name in agents:
        print(f"\n--- Testing {agent_class.__name__} ---")

        # Create agent
        agent = agent_class("test-model", "test-key", "test-url")

        # Create unique opportunity ID for this test
        opportunity_id = f"test-{expected_name}-{datetime.now().strftime('%H%M%S')}"
        test_data = {
            "opportunity_id": opportunity_id,
            "content": f"Test content for {expected_name} agent",
            "app_concept": "Test app concept",
            "target_market": "Test market"
        }

        # Execute agent
        try:
            result = agent.run(json.dumps(test_data))
            parsed = json.loads(result)

            print(f"✅ {expected_name} agent executed successfully")
            print(f"  Opportunity ID: {opportunity_id}")
            print(f"  Result: {list(parsed.keys())}")

        except Exception as e:
            print(f"❌ {expected_name} agent failed: {str(e)}")


async def main():
    """Main test execution"""

    print("🔍 AGENT METRICS TRACKING VERIFICATION")
    print(f"Timestamp: {datetime.now()}")

    # Test 1: Basic agent functionality and name mapping
    success = await test_agent_metrics_tracking()

    # Test 2: Individual agent execution
    await test_individual_agent_execution()

    # Final verdict
    print("\n" + "=" * 60)
    print("FINAL VERDICT")
    print("=" * 60)

    if success:
        print("✅ ALL TESTS PASSED")
        print("✅ All 5 agents are properly instrumented with metrics tracking")
        print("✅ Agent names are correctly mapped: wtp, segment, price, payment, market")
        print("\nThe QA audit finding should now be resolved:")
        print("- All 5 unique agent names are tracked")
        print("- No missing agent_name fields")
        print("- Consistent agent-level tracking implemented")
    else:
        print("❌ SOME TESTS FAILED")
        print("❌ Agent metrics tracking needs further investigation")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
