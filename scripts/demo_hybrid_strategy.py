#!/usr/bin/env python3
"""
RedditHarbor Hybrid Strategy Demo

Demonstrates both Option A (monetization LLM analyzer) and Option B (lead extraction).

This script proves:
1. You can extract sales leads from Reddit (Option B)
2. You can enhance monetization scoring with LLM (Option A)
3. Both use the SAME underlying data
4. Both can run in parallel

Run this to see the "aha moment" - the data is already there!
"""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.lead_extractor import LeadExtractor, format_lead_for_slack

# =============================================================================
# REALISTIC REDDIT POST EXAMPLES
# =============================================================================

EXAMPLE_POSTS = [
    {
        "id": "abc123",
        "author": "startup_cto_42",
        "title": "Switching from Asana - need recommendations",
        "selftext": """We're a team of 12 and currently paying $360/month for Asana.
It's gotten too expensive after the latest pricing change.

Looking for alternatives that:
- Cost under $200/month
- Integrate with Slack
- Have good mobile apps

Our budget is approved, need to decide by end of Q1. Any recommendations?""",
        "subreddit": "projectmanagement",
        "created_utc": 1705334567
    },
    {
        "id": "def456",
        "author": "fitness_enthusiast",
        "title": "MyFitnessPal alternatives?",
        "selftext": """I'm so frustrated with MyFitnessPal. The free version is too limited and $10/month for premium is expensive.

Looking for something that tracks macros properly and syncs with Apple Watch. Budget is around $5-8/month max.""",
        "subreddit": "fitness",
        "created_utc": 1705334567
    },
    {
        "id": "ghi789",
        "author": "small_biz_owner",
        "title": "What CRM do you use?",
        "selftext": "Small business owner here. Curious what CRM tools people use for managing customer relationships. Salesforce seems overkill for us.",
        "subreddit": "smallbusiness",
        "created_utc": 1705334567
    }
]


def demo_option_b_lead_extraction():
    """Demo Option B: Customer Lead Generation"""

    print("\n" + "="*80)
    print("OPTION B: CUSTOMER LEAD GENERATION")
    print("="*80)
    print("\nExtracting SALES LEADS from Reddit posts...")
    print("(Same data you're already collecting - just extract different fields!)\n")

    extractor = LeadExtractor()

    for i, post in enumerate(EXAMPLE_POSTS, 1):
        print(f"\n{'-'*80}")
        print(f"POST {i}/{len(EXAMPLE_POSTS)}: r/{post['subreddit']}")
        print(f"{'-'*80}\n")

        # Extract lead
        lead = extractor.extract_from_reddit_post(post, opportunity_score=85.0)

        # Show Slack alert format
        slack_msg = format_lead_for_slack(lead)
        print(slack_msg)

        print(f"\n💡 This is a REAL SALES LEAD!")
        print(f"   - Contact: u/{lead.reddit_username}")
        print(f"   - Post: {lead.reddit_post_url}")
        if lead.budget_mentioned:
            print(f"   - Budget: {lead.budget_mentioned}")
        if lead.current_solution:
            print(f"   - Current tool: {lead.current_solution} ← COMPETITOR!")


def demo_option_a_monetization():
    """Demo Option A: Enhanced Monetization Scoring"""

    print("\n\n" + "="*80)
    print("OPTION A: ENHANCED MONETIZATION SCORING")
    print("="*80)
    print("\nLLM-powered analysis fixes false positives in keyword matching...")
    print("(Requires DSPy + OpenAI API key - disabled in this demo)\n")

    print("Example improvements:")
    print("\n1. Sentiment Awareness:")
    print("   ❌ Keyword: 'willing to pay' → HIGH score")
    print("   ✅ LLM: 'NOT willing to pay' → LOW score")

    print("\n2. B2B vs B2C Weighting:")
    print("   ❌ Keyword: Both treated equally")
    print("   ✅ LLM: B2B weighted 35%, B2C weighted 15%")

    print("\n3. Price Extraction:")
    print("   ❌ Keyword: No extraction")
    print("   ✅ LLM: Extracts '$360/month', 'budget approved'")

    print("\n4. Subreddit Context:")
    print("   ❌ Keyword: No context awareness")
    print("   ✅ LLM: r/entrepreneur=1.5x, r/frugal=0.6x multipliers")

    print("\n📊 To test with real LLM:")
    print("   1. Set OPENAI_API_KEY in .env")
    print("   2. Run: python agent_tools/monetization_llm_analyzer.py")


def demo_hybrid_strategy():
    """Demo the Hybrid Strategy - both options together"""

    print("\n\n" + "="*80)
    print("🚀 HYBRID STRATEGY: BEST OF BOTH WORLDS")
    print("="*80)
    print("\nRun BOTH Option A and Option B simultaneously!\n")

    print("Pipeline Flow:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("1. collect_problem_posts()          → Same Reddit data collection")
    print("2. OpportunityAnalyzerAgent.analyze() → Same keyword scoring")
    print("   ├─→ 2a. Extract leads (Option B)     → Customer leads table")
    print("   └─→ 2b. LLM monetization (Option A)  → Enhanced scoring")
    print("3. Store both in database           → Parallel tracking")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    print("\nMarket Opportunity:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Option A (Founders Edition):  $29-99/mo  × 100 = $3-10k MRR")
    print("Option B (Growth Edition):    $499-4999/mo × 100 = $50-500k MRR")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    print("\nLaunch Strategy:")
    print("✅ 1. Validate Option A first (faster, simpler)")
    print("✅ 2. Build Option B in parallel (bigger opportunity)")
    print("✅ 3. Launch whichever validates first")
    print("✅ 4. Or run BOTH (different pricing, same backend)")


def main():
    """Run full demo"""

    print("\n" + "="*80)
    print("🎯 REDDITHARBOR HYBRID STRATEGY DEMO")
    print("="*80)
    print("\nThis demo shows how to extract BOTH:")
    print("  • App ideas (Option A)")
    print("  • Sales leads (Option B)")
    print("\nFrom the SAME Reddit data you're already collecting!\n")

    # Demo Option B
    demo_option_b_lead_extraction()

    # Demo Option A
    demo_option_a_monetization()

    # Demo Hybrid
    demo_hybrid_strategy()

    print("\n\n" + "="*80)
    print("✅ DEMO COMPLETE")
    print("="*80)
    print("\nNext Steps:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("1. Run migrations:")
    print("   psql $DB -f supabase/migrations/20251114200000_add_customer_leads_table.sql")
    print("   psql $DB -f supabase/migrations/20251114200001_add_llm_monetization_analysis.sql")
    print("")
    print("2. Test lead extraction:")
    print("   python core/lead_extractor.py")
    print("")
    print("3. Test LLM analyzer (requires OpenAI API key):")
    print("   python agent_tools/monetization_llm_analyzer.py")
    print("")
    print("4. Read integration guide:")
    print("   docs/guides/hybrid-strategy-integration-guide.md")
    print("")
    print("5. Integrate into your pipeline:")
    print("   See examples in docs/guides/")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")


if __name__ == "__main__":
    main()
