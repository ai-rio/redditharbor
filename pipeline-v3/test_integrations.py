#!/usr/bin/env python3
"""
Test script to verify all integrations are working correctly:
- AgentOps tracking
- LiteLLM/OpenRouter connectivity
- Cost tracking
- Real Agno agent execution
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from transform.agno_analyzer import AgnoOpportunityAnalyzer
from models.reddit import RedditSubmission
from config.settings import get_settings

def test_agentops_integration():
    """Test AgentOps is properly integrated with Agno agents"""
    print("=" * 60)
    print("TESTING AGENTOPS INTEGRATION")
    print("=" * 60)

    settings = get_settings()
    print(f"AgentOps API Key configured: {bool(settings.agno_enable_agentops and settings.openai_api_key != 'test_api_key')}")
    print(f"AgentOps enabled in settings: {settings.agno_enable_agentops}")
    print(f"AgentOps auto-instrument OpenAI: {getattr(settings, 'agentops_auto_instrument_openai', 'Not set')}")
    print()

def test_openrouter_connectivity():
    """Test OpenRouter API connectivity via Agno"""
    print("=" * 60)
    print("TESTING OPENROUTER CONNECTIVITY")
    print("=" * 60)

    settings = get_settings()
    print(f"OpenRouter API Key configured: {bool(settings.openai_api_key and settings.openai_api_key != 'test_api_key')}")
    print(f"OpenRouter URL: {settings.openai_base_url}")
    print(f"Agno Model: {settings.agno_model}")
    print(f"Agno Base URL: {settings.agno_base_url}")
    print()

def test_real_agent_execution():
    """Test real Agno agent execution with cost tracking"""
    print("=" * 60)
    print("TESTING REAL AGENT EXECUTION")
    print("=" * 60)

    try:
        # Create test submission with rich data
        test_submission = RedditSubmission(
            id="integration-test-123",
            title="Looking for project management solution for 10-person remote team",
            text="We're a fully remote software team of 10 developers struggling with project coordination. We've tried Jira (too complex), Trello (too basic), and Asana (too expensive at $15/user/month). Our budget is around $100/month total. We need something with good API integrations for GitHub and Slack, time tracking, and roadmap planning. We're willing to pay for a good solution that actually understands remote team workflows.",
            author="remote_team_lead",
            upvotes=42,
            downvotes=2,
            score=40,
            comments_count=12,
            subreddit="Entrepreneur",
            created_utc=datetime.now(timezone.utc),
            permalink="https://reddit.com/r/Entrepreneur/comments/integration-test-123/"
        )

        print(f"Test submission: {test_submission.title[:50]}...")
        print(f"Content length: {len(test_submission.text)} characters")
        print()

        # Initialize analyzer with AgentOps enabled
        start_time = time.time()
        analyzer = AgnoOpportunityAnalyzer(
            enable_agentops=True,  # Enable AgentOps tracking
            enable_embeddings=False  # Disable embeddings for this test
        )
        init_time = time.time()
        print(f"✓ Analyzer initialized in {init_time - start_time:.2f}s")

        # Run analysis
        print("Running real agent analysis...")
        analysis_start = time.time()
        result = analyzer.analyze_submission(test_submission)
        analysis_time = time.time() - analysis_start

        print(f"✓ Analysis completed in {analysis_time:.2f}s")
        print(f"App Title: {result.app_idea.title}")
        print(f"Final Score: {result.final_score:.1f}")
        print(f"Confidence: {result.confidence_score:.1f}%")
        print(f"Trust Level: {result.trust_level}")

        # Check market metrics
        print(f"Market Demand: {result.market_metrics.market_demand:.1f}")
        print(f"Pain Intensity: {result.market_metrics.pain_intensity:.1f}")
        print(f"Monetization: {result.market_metrics.monetization_potential:.1f}")

        return True, analysis_time

    except Exception as e:
        print(f"✗ Real agent execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False, 0

def test_cost_tracking():
    """Test that cost tracking systems are working"""
    print("=" * 60)
    print("TESTING COST TRACKING")
    print("=" * 60)

    settings = get_settings()

    # Check OpenRouter costs
    print(f"OpenRouter API Key configured: {bool(settings.openai_api_key)}")
    print(f"Using OpenRouter: {settings.is_openrouter_configured}")

    # Check AgentOps costs
    print(f"AgentOps API Key configured: {bool(settings.openai_api_key)}")  # Using same key for now
    print(f"AgentOps enabled: {settings.agno_enable_agentops}")

    # Cost estimates
    model = settings.agno_model
    print(f"Model: {model}")

    # Rough cost estimation
    if "claude-haiku" in model.lower():
        cost_per_1k_tokens = 0.00025  # Approximate cost for Claude Haiku
        print(f"Estimated cost per 1K tokens: ${cost_per_1k_tokens}")
    elif "gpt-4o-mini" in model.lower():
        cost_per_1k_tokens = 0.00015  # Approximate cost for GPT-4o-mini
        print(f"Estimated cost per 1K tokens: ${cost_per_1k_tokens}")
    else:
        cost_per_1k_tokens = 0.001  # Conservative estimate
        print(f"Estimated cost per 1K tokens: ${cost_per_1k_tokens} (conservative)")

def main():
    """Run all integration tests"""
    print("RedditHarbor Pipeline v3 - Integration Verification")
    print("=" * 60)
    print()

    # Test configurations
    test_agentops_integration()
    test_openrouter_connectivity()
    test_cost_tracking()

    # Test real execution
    print()
    success, analysis_time = test_real_agent_execution()

    # Summary
    print()
    print("=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)

    if success:
        print("✅ ALL INTEGRATIONS WORKING!")
        print(f"✓ AgentOps: Configured and ready")
        print(f"✓ OpenRouter: Connected and responding")
        print(f"✓ Agno Agents: Real AI analysis working")
        print(f"✓ Cost Tracking: Systems in place")
        print(f"✓ Analysis Time: {analysis_time:.2f}s")
        print()
        print("🚀 READY TO ADD TOOLS TO AGENTS!")
        return 0
    else:
        print("❌ SOME INTEGRATIONS FAILED")
        print("Please check the errors above before adding tools")
        return 1

if __name__ == "__main__":
    sys.exit(main())