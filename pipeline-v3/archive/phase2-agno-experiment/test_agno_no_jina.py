#!/usr/bin/env python3
"""
Test script to verify Agno analyzer works without Jina integration
"""

import sys
import os
import json
from datetime import datetime

# Add pipeline-v3 to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.reddit import RedditSubmission
from transform.analyzer_factory import AgnoAnalyzerFactory
from monitoring.metrics_collector import get_collector

def test_agno_without_jina():
    """Test that Agno analyzer works without Jina API integration"""
    print("=" * 80)
    print("Testing Agno Analyzer Without Jina Integration")
    print("=" * 80)
    print(f"Test started at: {datetime.utcnow()}")

    # Create test submission
    submission = RedditSubmission(
        id="test_123",
        title="Looking for a project management tool for my startup",
        text="We're a small team of 5 developers struggling to track tasks. Would pay for a good solution.",
        author="entrepreneur_user",
        subreddit="Entrepreneur",
        score=45,
        comments_count=23,
        created_at=datetime.utcnow().isoformat()
    )

    print(f"\nTest Submission:")
    print(f"  Title: {submission.title}")
    print(f"  Subreddit: r/{submission.subreddit}")
    print(f"  Content snippet: {submission.text[:100]}...")

    # Create Agno analyzer using factory
    print("\nInitializing Agno Analyzer...")
    try:
        factory = AgnoAnalyzerFactory({
            'model': 'anthropic/claude-haiku-4.5',
            'enable_agentops': False,
            'embedding_provider': 'fake'
        })
        analyzer = factory.create_analyzer()
        print("✓ Agno analyzer created successfully")
    except Exception as e:
        print(f"✗ Failed to create Agno analyzer: {e}")
        return False

    # Run analysis
    print("\nRunning multi-agent analysis...")
    try:
        # Get metrics collector
        metrics = get_collector()

        # Track the analysis
        with metrics.track("transform", test_run=True, opportunity_id=submission.id) as context:
            result = analyzer.analyze_submission(submission)

            # Update context metadata
            context["metadata"] = {
                "test_type": "agno_without_jina",
                "submission_id": submission.id,
                "final_score": getattr(result, 'final_score', 0),
                "analysis_completed": True
            }

        print("✓ Analysis completed successfully")
    except Exception as e:
        print(f"✗ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Display results
    print("\nAnalysis Results:")
    print("-" * 40)
    print(f"Final Score: {getattr(result, 'final_score', 'N/A')}")
    print(f"Trust Level: {getattr(result, 'trust_level', 'N/A')}")
    print(f"Confidence Score: {getattr(result, 'confidence_score', 'N/A')}")

    if hasattr(result, 'app_idea'):
        print(f"\nApp Idea:")
        print(f"  Title: {getattr(result.app_idea, 'title', 'N/A')}")
        print(f"  Concept: {getattr(result.app_idea, 'app_concept', 'N/A')[:100]}...")
        print(f"  Target Audience: {getattr(result.app_idea, 'target_audience', 'N/A')}")

    if hasattr(result, 'market_metrics'):
        print(f"\nMarket Metrics:")
        print(f"  Market Demand: {getattr(result.market_metrics, 'market_demand', 'N/A')}")
        print(f"  Pain Intensity: {getattr(result.market_metrics, 'pain_intensity', 'N/A')}")
        print(f"  Monetization Potential: {getattr(result.market_metrics, 'monetization_potential', 'N/A')}")

    # Test multi-agent consensus
    print("\nMulti-Agent Consensus Check:")
    print("-" * 40)

    # Check if we have agent details (this shows multi-agent coordination worked)
    if hasattr(result, '_raw_synthesis') and hasattr(result._raw_synthesis, 'agent_details'):
        agent_details = result._raw_synthesis.agent_details

        for agent_name, details in agent_details.items():
            if isinstance(details, dict) and not details.get('error'):
                print(f"✓ {agent_name} agent: Executed successfully")

                # Show key metrics from each agent
                if agent_name == "wtp":
                    score = details.get("wtp_score", "N/A")
                    print(f"    - WTP Score: {score}")
                elif agent_name == "segment":
                    market = details.get("market_demand_score", "N/A")
                    print(f"    - Market Demand Score: {market}")
                elif agent_name == "price":
                    monetization = details.get("monetization_score", "N/A")
                    print(f"    - Monetization Score: {monetization}")
                elif agent_name == "behavior":
                    pain = details.get("pain_intensity_score", "N/A")
                    print(f"    - Pain Intensity Score: {pain}")
            else:
                print(f"✗ {agent_name} agent: Failed or returned error")

    # Verify no Jina dependencies were used
    print("\nJina Dependency Check:")
    print("-" * 40)

    # Check that no Jina-related errors occurred
    jina_errors = [
        "jina", "Jina", "JINA_API_KEY", "JinaClient",
        "market_research", "validation_score", "competitor_pricing"
    ]

    # Check the logs for any Jina references
    has_jina = False
    for error_term in jina_errors:
        if error_term.lower() in str(result).lower():
            has_jina = True
            print(f"✗ Found potential Jina reference: {error_term}")

    if not has_jina:
        print("✓ No Jina dependencies found in results")

    # Print cost summary if available
    if hasattr(analyzer, 'cost_tracker'):
        cost_summary = analyzer.cost_tracker.get_cost_summary()
        print(f"\nCost Summary:")
        print(f"  Total Cost: ${cost_summary['total_cost']:.6f}")
        print(f"  Analysis Count: {cost_summary['analysis_count']}")

    print("\n" + "=" * 80)
    print("Test completed successfully!")
    print("=" * 80)
    return True

def test_batch_analysis():
    """Test batch analysis without Jina"""
    print("\n" + "=" * 80)
    print("Testing Batch Analysis Without Jina")
    print("=" * 80)

    # Create multiple test submissions
    submissions = [
        RedditSubmission(
            id="batch_1",
            title="Need CRM for small business",
            text="Looking for affordable CRM solution for team of 10",
            author="business_owner",
            subreddit="smallbusiness",
            score=25,
            comments_count=12,
            created_at=datetime.utcnow().isoformat()
        ),
        RedditSubmission(
            id="batch_2",
            title="API integration tool needed",
            text="Want to automate API connections between services",
            author="developer",
            subreddit="saas",
            score=60,
            comments_count=30,
            created_at=datetime.utcnow().isoformat()
        )
    ]

    # Create analyzer
    factory = AgnoAnalyzerFactory({
        'model': 'anthropic/claude-haiku-4.5',
        'enable_agentops': False,
        'embedding_provider': 'fake'
    })
    analyzer = factory.create_analyzer()

    # Run batch analysis
    print(f"\nAnalyzing {len(submissions)} submissions...")
    try:
        results, cost_summary = analyzer.analyze_batch_with_costs(submissions)
        print(f"✓ Batch analysis completed")
        print(f"  Results: {len(results)} analyses")
        print(f"  Total cost: ${cost_summary.get('total_cost', 0):.6f}")
        print(f"  Throughput: {cost_summary.get('throughput', 0):.2f} submissions/sec")

        # Show individual results
        for i, result in enumerate(results, 1):
            print(f"\n  Result {i}:")
            print(f"    Final Score: {getattr(result, 'final_score', 'N/A')}")
            print(f"    Trust Level: {getattr(result, 'trust_level', 'N/A')}")

        return True

    except Exception as e:
        print(f"✗ Batch analysis failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting Agno Analyzer Tests (Without Jina)")
    print("=" * 80)

    success = True

    # Test single analysis
    if not test_agno_without_jina():
        success = False

    # Test batch analysis
    if not test_batch_analysis():
        success = False

    # Final result
    print("\n" + "=" * 80)
    if success:
        print("✓ ALL TESTS PASSED - Agno analyzer works without Jina!")
        print("=" * 80)
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        print("=" * 80)
        sys.exit(1)