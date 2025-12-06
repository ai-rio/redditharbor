#!/usr/bin/env python3
"""
Simple test to verify Agno analyzer imports and initialization without Jina
"""

import sys
import os

# Add pipeline-v3 to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules import without Jina"""
    print("Testing imports...")

    try:
        # Test core imports
        from transform.agno_analyzer import AgnoOpportunityAnalyzer
        print("✓ AgnoOpportunityAnalyzer imported successfully")

        from transform.agno_agents import (
            WillingnessToPayAgent,
            MarketSegmentAgent,
            PricePointAgent,
            PaymentBehaviorAgent
        )
        print("✓ All core agents imported successfully")

        from transform.analyzer_factory import AgnoAnalyzerFactory
        print("✓ AgnoAnalyzerFactory imported successfully")

        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_agent_initialization():
    """Test that agents can be initialized without Jina dependencies"""
    print("\nTesting agent initialization...")

    try:
        from transform.agno_agents import (
            WillingnessToPayAgent,
            MarketSegmentAgent,
            PricePointAgent,
            PaymentBehaviorAgent
        )

        model = "test-model"
        api_key = "test-key"
        base_url = "https://test.com"

        # Initialize each agent
        wtp_agent = WillingnessToPayAgent(model, api_key, base_url)
        print("✓ WillingnessToPayAgent initialized")

        segment_agent = MarketSegmentAgent(model, api_key, base_url)
        print("✓ MarketSegmentAgent initialized")

        price_agent = PricePointAgent(model, api_key, base_url)
        print("✓ PricePointAgent initialized")

        behavior_agent = PaymentBehaviorAgent(model, api_key, base_url)
        print("✓ PaymentBehaviorAgent initialized")

        return True
    except Exception as e:
        print(f"✗ Agent initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agno_analyzer_initialization():
    """Test that Agno analyzer can be created without Jina"""
    print("\nTesting Agno analyzer initialization...")

    try:
        from transform.agno_analyzer import AgnoOpportunityAnalyzer

        # Create analyzer with minimal configuration
        analyzer = AgnoOpportunityAnalyzer(
            model="anthropic/claude-haiku-4.5",
            base_url="https://openrouter.ai/api/v1",
            enable_agentops=False,
            embedding_provider="fake"
        )
        print("✓ AgnoOpportunityAnalyzer created without Jina")

        # Check that no Jina client was initialized
        if hasattr(analyzer, 'market_research_agent'):
            print("✗ WARNING: market_research_agent still present")
            return False
        else:
            print("✓ No market research agent (Jina dependency removed)")

        # Check team has only 4 agents
        if len(analyzer.team.agents) == 4:
            print("✓ Team has exactly 4 core agents")
        else:
            print(f"✗ Team has {len(analyzer.team.agents)} agents (expected 4)")
            return False

        return True
    except Exception as e:
        print(f"✗ Agno analyzer initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_factory_creation():
    """Test that factory can create analyzer without Jina"""
    print("\nTesting factory-based creation...")

    try:
        from transform.analyzer_factory import AgnoAnalyzerFactory

        # Create factory
        factory = AgnoAnalyzerFactory({
            'model': 'anthropic/claude-haiku-4.5',
            'enable_agentops': False,
            'embedding_provider': 'fake'
        })
        print("✓ AgnoAnalyzerFactory created")

        # Create analyzer through factory
        analyzer = factory.create_analyzer()
        print("✓ Analyzer created through factory")

        # Verify no Jina dependencies
        if not hasattr(analyzer, 'jina_client') and not hasattr(analyzer, 'market_research_agent'):
            print("✓ No Jina dependencies in factory-created analyzer")
        else:
            print("✗ WARNING: Found Jina dependencies")
            return False

        return True
    except Exception as e:
        print(f"✗ Factory creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mock_team():
    """Test that MockTeam works with 4 agents"""
    print("\nTesting MockTeam with 4 agents...")

    try:
        from transform.agno_analyzer import MockTeam
        from transform.agno_agents import (
            WillingnessToPayAgent,
            MarketSegmentAgent,
            PricePointAgent,
            PaymentBehaviorAgent
        )

        # Create agents
        agents = [
            WillingnessToPayAgent("model", "key", "url"),
            MarketSegmentAgent("model", "key", "url"),
            PricePointAgent("model", "key", "url"),
            PaymentBehaviorAgent("model", "key", "url")
        ]

        # Create team
        team = MockTeam(agents)
        print("✓ MockTeam created with 4 agents")

        # Test agent map
        expected_agents = ["WTP Analyst", "Market Segment", "Price Point", "Payment Behavior"]
        for agent_name in expected_agents:
            if team.has_agent(agent_name):
                print(f"✓ {agent_name} agent found in team")
            else:
                print(f"✗ {agent_name} agent missing from team")
                return False

        # Test that Market Research is not in team
        if team.has_agent("Market Research"):
            print("✗ Market Research agent should not be in team")
            return False
        else:
            print("✓ Market Research agent correctly excluded")

        return True
    except Exception as e:
        print(f"✗ MockTeam test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Agno Analyzer Jina-Free Tests")
    print("=" * 50)

    success = True

    # Run all tests
    tests = [
        test_imports,
        test_agent_initialization,
        test_agno_analyzer_initialization,
        test_factory_creation,
        test_mock_team
    ]

    for test in tests:
        if not test():
            success = False

    # Final result
    print("\n" + "=" * 50)
    if success:
        print("✓ ALL TESTS PASSED")
        print("Agno analyzer successfully works without Jina!")
    else:
        print("✗ SOME TESTS FAILED")
        print("=" * 50)
        sys.exit(1)