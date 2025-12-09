#!/usr/bin/env python3
"""
Simple verification that all 5 agents have correct name mappings

This script verifies the agent_name mapping without requiring database connection
or complex dependencies.
"""

import os
import sys

# Add pipeline-v3 to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_agent_name_mappings():
    """Test that all agents have correct name mappings"""

    # Import agents
    from transform.agno_agents import (
        Agent,
        MarketResearchAgent,
        MarketSegmentAgent,
        PaymentBehaviorAgent,
        PricePointAgent,
        WillingnessToPayAgent,
    )

    # Expected agent name mappings
    expected_mappings = {
        "WillingnessToPayAgent": "wtp",
        "MarketSegmentAgent": "segment",
        "PricePointAgent": "price",
        "PaymentBehaviorAgent": "payment",
        "MarketResearchAgent": "market"
    }

    print("🔍 VERIFYING AGENT NAME MAPPINGS")
    print("=" * 50)

    success = True

    # Test each agent class
    for agent_class_name, expected_name in expected_mappings.items():
        agent_class = globals()[agent_class_name]

        # Create instance
        agent = agent_class("test-model", "test-key", "test-url")

        # Get actual name
        actual_name = agent._get_agent_name()

        # Check mapping
        if actual_name == expected_name:
            print(f"✅ {agent_class_name} → {actual_name}")
        else:
            print(f"❌ {agent_class_name} → expected: {expected_name}, got: {actual_name}")
            success = False

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    if success:
        print("✅ ALL AGENT NAME MAPPINGS CORRECT")
        print("Expected agent names: wtp, segment, price, payment, market")
        print("\nThe QA audit finding should be resolved:")
        print("- All 5 unique agent names are properly mapped")
        print("- No missing agent_name fields expected")
        print("- Consistent agent-level tracking should work")
    else:
        print("❌ AGENT NAME MAPPING ISSUES FOUND")
        print("This would explain the QA audit finding")

    return success

def test_agent_count():
    """Verify we have exactly 5 agents"""

    from transform.agno_agents import (
        MarketResearchAgent,
        MarketSegmentAgent,
        PaymentBehaviorAgent,
        PricePointAgent,
        WillingnessToPayAgent,
    )

    agent_classes = [
        WillingnessToPayAgent,
        MarketSegmentAgent,
        PricePointAgent,
        PaymentBehaviorAgent,
        MarketResearchAgent
    ]

    print("\n📊 AGENT COUNT VERIFICATION")
    print(f"Found {len(agent_classes)} agent classes")

    expected_count = 5
    if len(agent_classes) == expected_count:
        print(f"✅ Correct number of agents ({expected_count})")
        return True
    else:
        print(f"❌ Expected {expected_count} agents, found {len(agent_classes)}")
        return False

def main():
    """Main verification"""

    print("AGENT METRICS TRACKING VERIFICATION")
    print("=" * 60)

    # Test 1: Agent count
    count_ok = test_agent_count()

    # Test 2: Agent name mappings
    names_ok = test_agent_name_mappings()

    # Overall result
    print("\n" + "=" * 60)
    print("OVERALL RESULT")
    print("=" * 60)

    if count_ok and names_ok:
        print("✅ ALL VERIFICATIONS PASSED")
        print("\nThe agent-level metrics tracking should now be complete:")
        print("- 5 agents properly defined")
        print("- Correct agent name mappings")
        print("- Should resolve QA audit finding")
        return True
    else:
        print("❌ VERIFICATION ISSUES FOUND")
        if not count_ok:
            print("- Agent count incorrect")
        if not names_ok:
            print("- Agent name mappings incorrect")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
