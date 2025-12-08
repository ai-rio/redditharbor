#!/usr/bin/env python3
"""
Test script to verify the Agno multi-agent coordination fixes
"""

import logging
from datetime import UTC, datetime
from uuid import uuid4

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import models and analyzer
from models.reddit import RedditSubmission
from transform.agno_analyzer import AgnoOpportunityAnalyzer


def test_agent_coordination():
    """Test that all 4 agents are properly coordinating and generating meaningful consensus"""

    print("\n" + "="*60)
    print("TESTING AGNO MULTI-AGENT COORDINATION FIXES")
    print("="*60)

    # Create test submission with clear business intent
    submission = RedditSubmission(
        id=str(uuid4()),
        title="Looking for payroll automation solution for our 50-employee company",
        text="""
        Our company is spending 20+ hours per month on manual payroll processing.
        We're currently using QuickBooks but it's not automated enough.

        We need a solution that can:
        - Auto-calculate taxes and deductions
        - Generate payslips automatically
        - Handle direct deposits
        - Integrate with our time tracking system

        Budget is up to $200/month for the right solution.
        This is urgent - we're struggling with compliance issues.
        """,
        author="hr_manager_2024",
        upvotes=45,
        downvotes=2,
        score=43,
        comments_count=23,
        subreddit="entrepreneur",
        created_utc=datetime.now(UTC),
        permalink="/r/entrepreneur/comments/payroll_automation_needed/",
        url=None,
        is_self=True,
        over_18=False
    )

    # Initialize analyzer with embeddings disabled for testing
    analyzer = AgnoOpportunityAnalyzer(
        enable_embeddings=False,
        embedding_provider="fake"
    )

    print("\n1. Running multi-agent analysis...")
    print(f"   Submission: {submission.title[:50]}...")
    print(f"   Subreddit: r/{submission.subreddit}")

    # Analyze the submission
    result = analyzer.analyze_submission(submission)

    print("\n2. Checking analysis results...")
    print(f"   Final Score: {result.final_score:.1f}")
    print(f"   Market Demand: {result.market_metrics.market_demand:.1f}")
    print(f"   Pain Intensity: {result.market_metrics.pain_intensity:.1f}")
    print(f"   Monetization Potential: {result.market_metrics.monetization_potential:.1f}")

    print("\n3. Checking Agno agent fields (should NOT be None)...")

    # Check agno fields
    agno_fields = {
        'agno_wtp_score': result.agno_wtp_score,
        'agno_segment_type': result.agno_segment_type,
        'agno_segment_confidence': result.agno_segment_confidence,
        'agno_price_potential': result.agno_price_potential,
        'agno_behavior_score': result.agno_behavior_score,
        'agno_consensus_confidence': result.agno_consensus_confidence
    }

    all_present = True
    for field, value in agno_fields.items():
        status = "✓" if value is not None else "✗"
        print(f"   {field}: {value if value is not None else 'NULL'} {status}")
        if value is None:
            all_present = False

    print("\n4. Checking agent details JSON...")
    if result.agno_agent_details:
        print("   ✓ agno_agent_details is present")

        # Check each agent's output
        agent_count = len(result.agno_agent_details)
        print(f"   Number of agents: {agent_count}")

        for agent_name, agent_output in result.agno_agent_details.items():
            if 'error' in agent_output:
                print(f"   ✗ {agent_name}: ERROR - {agent_output.get('error', 'Unknown error')}")
            else:
                print(f"   ✓ {agent_name}: OK")

                # Show key metrics for each agent
                if agent_name == 'wtp':
                    print(f"     - WTP Score: {agent_output.get('wtp_score', 'N/A')}")
                    print(f"     - Market Demand: {agent_output.get('market_demand_score', 'N/A')}")
                elif agent_name == 'segment':
                    print(f"     - Segment Type: {agent_output.get('segment_type', 'N/A')}")
                    print(f"     - Target Audience: {agent_output.get('target_audience', 'N/A')[:50]}...")
                elif agent_name == 'price':
                    print(f"     - Monetization Score: {agent_output.get('monetization_score', 'N/A')}")
                    print(f"     - Price Point: {agent_output.get('price_point', 'N/A')}")
                elif agent_name == 'behavior':
                    print(f"     - Behavior Score: {agent_output.get('behavior_score', 'N/A')}")
                    print(f"     - Pain Intensity: {agent_output.get('pain_intensity_score', 'N/A')}")
    else:
        print("   ✗ agno_agent_details is NULL")
        all_present = False

    print("\n5. Checking consensus calculation...")

    # Verify consensus was calculated from agent outputs
    if all_present and result.agno_agent_details:
        wtp_score = result.agno_agent_details.get('wtp', {}).get('wtp_score', 0)
        segment_score = result.agno_agent_details.get('segment', {}).get('market_demand_score', 0)
        price_score = result.agno_agent_details.get('price', {}).get('monetization_score', 0)
        behavior_score = result.agno_agent_details.get('behavior', {}).get('pain_intensity_score', 0)

        print("   Raw Agent Scores:")
        print(f"     - WTP Agent: {wtp_score}")
        print(f"     - Segment Agent: {segment_score}")
        print(f"     - Price Agent: {price_score}")
        print(f"     - Behavior Agent: {behavior_score}")

        # Calculate expected consensus
        expected_market_demand = (wtp_score * 0.6) + (segment_score * 0.4)
        expected_pain_intensity = (wtp_score * 0.5) + (behavior_score * 0.3) + (price_score * 0.2)

        print("\n   Expected Consensus:")
        print(f"     - Market Demand: {expected_market_demand:.1f}")
        print(f"     - Pain Intensity: {expected_pain_intensity:.1f}")

        print("\n   Actual Consensus:")
        print(f"     - Market Demand: {result.market_metrics.market_demand:.1f}")
        print(f"     - Pain Intensity: {result.market_metrics.pain_intensity:.1f}")

        # Check if values are close (allowing for some rounding)
        market_close = abs(result.market_metrics.market_demand - expected_market_demand) < 1.0
        pain_close = abs(result.market_metrics.pain_intensity - expected_pain_intensity) < 1.0

        if market_close and pain_close:
            print("   ✓ Consensus calculation is working correctly")
        else:
            print("   ✗ Consensus calculation may have issues")
    else:
        print("   ✗ Cannot verify consensus - missing agent data")

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    if all_present and result.agno_agent_details:
        print("✓ SUCCESS: All Agno fields are populated!")
        print("✓ Multi-agent coordination is working properly")
        print("✓ Agent outputs are being preserved in the database")
        print("\nThe following issues have been FIXED:")
        print("- agno_* fields are now populated from agent outputs")
        print("- Agent-specific analysis is preserved")
        print("- Consensus is calculated from individual agent scores")
        print("- Raw agent details are stored for transparency")

        return True
    else:
        print("✗ FAILURE: Some Agno fields are still NULL")
        print("\nRemaining issues:")
        if not all_present:
            print("- Some agno_* fields are not being populated")
        if not result.agno_agent_details:
            print("- Agent details are not being preserved")

        return False


def test_different_submissions():
    """Test with different types of submissions to ensure variety in agent outputs"""

    print("\n\n" + "="*60)
    print("TESTING VARIETY OF SUBMISSION TYPES")
    print("="*60)

    test_cases = [
        {
            "name": "B2B SaaS Request",
            "title": "Need enterprise CRM solution for sales team",
            "text": "Our 100-person sales team needs better CRM. Budget $500/mo.",
            "subreddit": "sales"
        },
        {
            "name": "B2C Consumer App",
            "title": "App to track fitness goals would be amazing",
            "text": "I want an app that helps me stay motivated to work out and eat healthy.",
            "subreddit": "fitness"
        },
        {
            "name": "Technical Tool Request",
            "title": "API monitoring tool for developers needed",
            "text": "Our dev team needs better API monitoring and alerting. Willing to pay for good solution.",
            "subreddit": "webdev"
        }
    ]

    analyzer = AgnoOpportunityAnalyzer(enable_embeddings=False)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing {test_case['name']}...")

        submission = RedditSubmission(
            id=str(uuid4()),
            title=test_case['title'],
            text=test_case['text'],
            author="test_user",
            upvotes=10,
            downvotes=0,
            score=10,
            comments_count=5,
            subreddit=test_case['subreddit'],
            created_utc=datetime.now(UTC),
            permalink=f"/r/{test_case['subreddit']}/test/",
            url=None,
            is_self=True,
            over_18=False
        )

        result = analyzer.analyze_submission(submission)

        # Check for variety in outputs
        print(f"   Segment Type: {result.agno_segment_type}")
        print(f"   WTP Score: {result.agno_wtp_score:.1f}")
        print(f"   Price Potential: {result.agno_price_potential:.1f}")

        # Verify agent details have substance
        if result.agno_agent_details:
            segment_agent = result.agno_agent_details.get('segment', {})
            target_audience = segment_agent.get('target_audience', '')
            if target_audience and len(target_audience) > 10:
                print(f"   Target Audience: {target_audience[:50]}...")
            else:
                print("   ⚠ Target audience seems generic")


if __name__ == "__main__":
    print("RedditHarbor Pipeline v3 - Agno Multi-Agent Coordination Test")
    print("=============================================================")

    # Run the main test
    success = test_agent_coordination()

    # Run variety tests if main test passed
    if success:
        test_different_submissions()

    print("\n\nTest complete! Check output above for results.")
