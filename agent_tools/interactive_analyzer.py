#!/usr/bin/env python3
"""
Interactive Opportunity Analyzer
Example script showing how to use the agent tools for opportunity analysis
"""

import sys
from pathlib import Path

import anyio

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from claude_agent_sdk import query

from agent_tools.opportunity_analyzer_agent import OpportunityAnalyzerAgent


async def interactive_analysis():
    """
    Interactive session for opportunity analysis using agent tools
    """
    print("=" * 60)
    print("🎯 RedditHarbor Opportunity Analysis Agent")
    print("=" * 60)
    print()
    print("This agent can help you:")
    print("  1. Analyze opportunities using 5-dimensional scoring")
    print("  2. Batch process multiple opportunities")
    print("  3. Track business metrics and KPIs")
    print("  4. Generate validation reports")
    print("  5. Run continuous analysis workflows")
    print()
    print("=" * 60)
    print()

    # Initialize the agent
    agent = OpportunityAnalyzerAgent()

    # Example 1: Analyze a single opportunity
    print("📊 EXAMPLE 1: Single Opportunity Analysis")
    print("-" * 60)

    example_opportunity = {
        "id": "opp_001",
        "title": "Need a better project management tool",
        "text": """I'm really frustrated with current project management tools.
        They're either too expensive for small teams or too complicated.
        I wish there was a simple, affordable solution that actually works.
        I would definitely pay for something that solves this.""",
        "subreddit": "startups",
        "engagement": {"upvotes": 156, "num_comments": 42},
        "comments": [
            "Totally agree, existing tools are overpriced",
            "Something simple is desperately needed",
            "I need this for my team"
        ]
    }

    result = agent.analyze_opportunity(example_opportunity)

    print(f"\nOpportunity: {result['title']}")
    print(f"Subreddit: {result['subreddit']}")
    print("\n📈 Dimension Scores:")
    print(f"  • Market Demand (20%): {result['dimension_scores']['market_demand']}")
    print(f"  • Pain Intensity (25%): {result['dimension_scores']['pain_intensity']}")
    print(f"  • Monetization Potential (30%): {result['dimension_scores']['monetization_potential']}")
    print(f"  • Market Gap (15%): {result['dimension_scores']['market_gap']}")
    print(f"  • Technical Feasibility (10%): {result['dimension_scores']['technical_feasibility']}")
    print(f"\n🎯 Final Score: {result['final_score']}")
    print(f"🏷️  Priority: {result['priority']}")
    print()

    # Example 2: Business Metrics Dashboard
    print("💼 EXAMPLE 2: Business Metrics Tracking")
    print("-" * 60)

    metrics = agent.track_business_metrics()

    print("\n📊 Current Quarter KPIs:")
    print(f"  • Opportunities Identified: {metrics['opportunities_identified']} (Target: {metrics['quarterly_target']})")
    print(f"  • Validation Success Rate: {metrics['validation_success_rate']*100:.1f}% (Target: {metrics['validation_target']*100:.1f}%)")
    print(f"  • High-Priority Count: {metrics['high_priority_count']} (Target: {metrics['high_priority_target']})")
    print(f"  • Cross-Platform Coverage: {metrics['cross_platform_coverage']*100:.1f}% (Target: {metrics['coverage_target']*100:.1f}%)")
    print(f"  • Revenue Potential: ${metrics['revenue_potential_monthly']:,}/mo (Target: ${metrics['revenue_target_monthly']:,}/mo)")
    print(f"  • Time to Market: {metrics['time_to_market_months']:.1f}mo (Target: {metrics['time_to_market_target']:.1f}mo)")
    print()

    # Example 3: Validation Framework
    print("✅ EXAMPLE 3: Validation Framework Tracking")
    print("-" * 60)

    validation = agent.generate_validation_report("opp_001")

    print("\nValidation Status:")
    print(f"  🔍 Cross-Platform: {validation['cross_platform']['status']}")
    print(f"  📊 Market Research: {validation['market_research']['status']}")
    print(f"  ⚙️  Technical Assessment: {validation['technical_feasibility']['status']}")
    print(f"  💰 User Validation: {validation['user_validation']['status']}")
    print()

    # Example 4: Batch Analysis
    print("🚀 EXAMPLE 4: Batch Analysis")
    print("-" * 60)

    batch_data = [
        {
            "id": "opp_002",
            "title": "Better meal planning app needed",
            "text": "Current meal planning apps are expensive and hard to use. Looking for alternatives.",
            "subreddit": "nutrition",
            "engagement": {"upvotes": 98, "num_comments": 31},
            "comments": ["They all suck", "Need something better"]
        },
        {
            "id": "opp_003",
            "title": "Freelancer payment issues",
            "text": "Getting paid as a freelancer is complicated. There must be a better way.",
            "subreddit": "freelance",
            "engagement": {"upvotes": 203, "num_comments": 67},
            "comments": ["This is a huge problem", "Would pay for a solution"]
        }
    ]

    batch_results = agent.batch_analyze_opportunities(batch_data)

    print(f"\nAnalyzed {len(batch_results)} opportunities:")
    for result in batch_results:
        if "error" not in result:
            print(f"  • {result['title'][:50]}... - Score: {result['final_score']} - {result['priority']}")
    print()

    # Example 5: Query Claude for insights
    print("🧠 EXAMPLE 5: AI-Powered Analysis with Claude")
    print("-" * 60)

    prompt = f"""
    Based on this opportunity analysis, provide strategic recommendations:

    Opportunity: {result['title']}
    Final Score: {result['final_score']}
    Priority: {result['priority']}

    Top scoring dimensions:
    1. {max(result['dimension_scores'], key=result['dimension_scores'].get)}: {max(result['dimension_scores'].values())}
    2. {sorted(result['dimension_scores'].items(), key=lambda x: x[1], reverse=True)[1][0]}: {sorted(result['dimension_scores'].values(), reverse=True)[1]}

    What should be the next steps for validation and development?
    """

    print("\n🤖 Asking Claude for strategic insights...")
    print("-" * 60)

    async for message in query(prompt=prompt):
        if hasattr(message, 'content'):
            for block in message.content:
                if hasattr(block, 'text'):
                    print(block.text)
                    print()

    print("=" * 60)
    print("✅ Analysis Complete!")
    print("=" * 60)
    print()
    print("To use these tools in your own code:")
    print("  1. Import: from agent_tools.opportunity_analyzer_agent import OpportunityAnalyzerAgent")
    print("  2. Initialize: agent = OpportunityAnalyzerAgent()")
    print("  3. Analyze: result = agent.analyze_opportunity(submission_data)")
    print("  4. Get metrics: metrics = agent.track_business_metrics()")
    print()
    print("For interactive use with Claude:")
    print("  • Use the custom @tool decorated methods")
    print("  • Call them directly in your conversations")
    print("  • They integrate seamlessly with marimo notebooks")
    print()


if __name__ == "__main__":
    anyio.run(interactive_analysis)
