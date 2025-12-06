#!/usr/bin/env python3
"""
Test script to verify real Agno agents are working
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from transform.agno_analyzer import AgnoOpportunityAnalyzer
from models.reddit import RedditSubmission
from config.settings import get_settings

def test_real_agents():
    """Test real Agno agents with a sample submission"""
    print("=" * 60)
    print("TESTING REAL AGNO AGENTS")
    print("=" * 60)

    # Check configuration
    settings = get_settings()
    print(f"API Key configured: {bool(settings.openai_api_key and settings.openai_api_key != 'test_api_key')}")
    print(f"Agno Model: {settings.agno_model}")
    print(f"Agno Base URL: {settings.agno_base_url}")
    print()

    # Create test submission
    test_submission = RedditSubmission(
        id="test123",
        title="Looking for a project management tool for my startup",
        text="We are a small team of 5 developers struggling with task management. We've tried Trello and Jira but they're too complex. Would pay $50/month for something simple. Our budget is $200/month total for tools.",
        subreddit="Entrepreneur",
        author="startup_founder",
        upvotes=15,
        downvotes=0,
        score=15,
        comments_count=8,
        created_utc=datetime.now(timezone.utc),
        permalink="https://reddit.com/r/Entrepreneur/comments/test123"
    )

    # Initialize analyzer with real agents
    print("Initializing Agno Opportunity Analyzer with real agents...")
    try:
        analyzer = AgnoOpportunityAnalyzer(
            enable_agentops=True,  # Enable debug mode for testing
            enable_embeddings=False  # Disable embeddings for now
        )
        print("✓ Analyzer initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize analyzer: {e}")
        return False

    # Run analysis
    print("\nRunning analysis on test submission...")
    try:
        result = analyzer.analyze_submission(test_submission)

        print("✓ Analysis completed successfully!")
        print(f"App Title: {result.app_idea.title}")
        print(f"Final Score: {result.final_score:.1f}")
        print(f"App Concept: {result.app_idea.app_concept[:200]}...")
        print(f"Market Demand: {result.market_metrics.market_demand:.1f}")
        print(f"Pain Intensity: {result.market_metrics.pain_intensity:.1f}")
        print(f"Monetization: {result.market_metrics.monetization_potential:.1f}")

        return True

    except Exception as e:
        print(f"✗ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_agent_imports():
    """Check that all agents can be imported"""
    print("\nChecking agent imports...")

    try:
        from transform.agno_agents import (
            WillingnessToPayAgent,
            MarketSegmentAgent,
            PricePointAgent,
            PaymentBehaviorAgent,
            MarketResearchAgent
        )
        print("✓ All agent imports successful")

        # Test creating agents with configuration
        print("\nTesting agent creation...")

        # Get configuration from settings
        settings = get_settings()

        wtp_agent = WillingnessToPayAgent(
            model=settings.agno_model,
            api_key=settings.openai_api_key,
            base_url=settings.agno_base_url,
            debug_mode=True
        )
        print(f"✓ WillingnessToPayAgent created: {wtp_agent.name}")

        segment_agent = MarketSegmentAgent(
            model=settings.agno_model,
            api_key=settings.openai_api_key,
            base_url=settings.agno_base_url,
            debug_mode=True
        )
        print(f"✓ MarketSegmentAgent created: {segment_agent.name}")

        price_agent = PricePointAgent(
            model=settings.agno_model,
            api_key=settings.openai_api_key,
            base_url=settings.agno_base_url,
            debug_mode=True
        )
        print(f"✓ PricePointAgent created: {price_agent.name}")

        behavior_agent = PaymentBehaviorAgent(
            model=settings.agno_model,
            api_key=settings.openai_api_key,
            base_url=settings.agno_base_url,
            debug_mode=True
        )
        print(f"✓ PaymentBehaviorAgent created: {behavior_agent.name}")

        market_agent = MarketResearchAgent(
            model=settings.agno_model,
            api_key=settings.openai_api_key,
            base_url=settings.agno_base_url,
            debug_mode=True
        )
        print(f"✓ MarketResearchAgent created: {market_agent.name}")

        return True

    except Exception as e:
        print(f"✗ Import or creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Real Agno Agent Implementation")
    print("=" * 50)

    # Check imports first
    if not check_agent_imports():
        sys.exit(1)

    # Test real agents
    if test_real_agents():
        print("\n✅ ALL TESTS PASSED - Real Agno agents are working!")
        sys.exit(0)
    else:
        print("\n❌ TESTS FAILED - Check configuration and logs")
        sys.exit(1)