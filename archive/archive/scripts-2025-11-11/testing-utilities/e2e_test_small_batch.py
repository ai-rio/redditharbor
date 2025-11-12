#!/usr/bin/env python3
"""
E2E Test: Small Batch Opportunity Detection
Creates test Reddit submissions → Runs scoring → Verifies storage
"""

import os
import sys
import uuid
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent_tools.llm_profiler import LLMProfiler
from agent_tools.opportunity_analyzer_agent import OpportunityAnalyzerAgent
from supabase import create_client


def create_test_submissions(supabase):
    """Insert 3 test submissions with varying pain levels"""

    print("\n" + "="*80)
    print("STEP 1: Creating Test Submissions")
    print("="*80)

    # Generate UUIDs for test submissions
    uuid1 = str(uuid.uuid4())
    uuid2 = str(uuid.uuid4())
    uuid3 = str(uuid.uuid4())

    test_submissions = [
        {
            "id": uuid1,
            "title": "I'm desperate for a solution - existing tools are completely broken",
            "text": "I'm absolutely desperate here. I've tried 15 different project management tools and NONE of them work for our team. They're either $50/month per user (insane!), or they're missing critical features like time tracking and Gantt charts. My team is hemorrhaging productivity - we waste 10+ hours per week just managing our tasks across different tools. I've spent $3000+ this year on failed subscriptions. Someone PLEASE tell me there's a solution I'm missing. This is killing our business and I'm ready to pay good money for something that actually works. The market is completely broken - everything is either enterprise-level expensive or consumer-grade useless.",
            "content": "I'm absolutely desperate here. I've tried 15 different project management tools and NONE of them work for our team. They're either $50/month per user (insane!), or they're missing critical features like time tracking and Gantt charts. My team is hemorrhaging productivity - we waste 10+ hours per week just managing our tasks across different tools. I've spent $3000+ this year on failed subscriptions. Someone PLEASE tell me there's a solution I'm missing. This is killing our business and I'm ready to pay good money for something that actually works. The market is completely broken - everything is either enterprise-level expensive or consumer-grade useless.",
            "subreddit": "SaaS",
            "score": 1840,
            "num_comments": 342,
            "url": "https://reddit.com/r/SaaS/test1"
        },
        {
            "id": uuid2,
            "title": "Looking for meal planning help",
            "text": "Does anyone have a good meal planning system? I struggle with planning meals for the week and end up wasting food. Looking for app recommendations.",
            "content": "Does anyone have a good meal planning system? I struggle with planning meals for the week and end up wasting food. Looking for app recommendations.",
            "subreddit": "cooking",
            "score": 45,
            "num_comments": 12,
            "url": "https://reddit.com/r/cooking/test2"
        },
        {
            "id": uuid3,
            "title": "Nice weather today",
            "text": "Just wanted to share that it's a beautiful sunny day. Hope everyone is having a great weekend!",
            "content": "Just wanted to share that it's a beautiful sunny day. Hope everyone is having a great weekend!",
            "subreddit": "CasualConversation",
            "score": 12,
            "num_comments": 3,
            "url": "https://reddit.com/r/CasualConversation/test3"
        }
    ]

    # Insert submissions
    for sub in test_submissions:
        try:
            supabase.table("submissions").insert(sub).execute()
            print(f"  ✓ Created: {sub['title'][:60]}... (score: {sub['score']})")
        except Exception:
            print(f"  ⚠️  Skipped (may already exist): {sub['id']}")

    print("\n✓ Test submissions ready")
    return test_submissions, [uuid1, uuid2, uuid3]


def run_scoring(supabase, llm_profiler, test_uuids):
    """Run opportunity scoring on test submissions"""

    print("\n" + "="*80)
    print("STEP 2: Running Opportunity Analysis")
    print("="*80)

    agent = OpportunityAnalyzerAgent()

    # Fetch test submissions
    result = supabase.table('submissions').select('*').in_('id', test_uuids).execute()

    submissions = result.data
    print(f"Found {len(submissions)} test submissions to analyze\n")

    scored_opportunities = []

    for sub in submissions:
        # Format for analyzer
        formatted = {
            "id": sub.get("id"),
            "title": sub.get("title"),
            "text": sub.get("text", sub.get("content", "")),
            "subreddit": sub.get("subreddit"),
            "engagement": {
                "upvotes": sub.get("score", 0),
                "num_comments": sub.get("num_comments", 0)
            }
        }

        # Analyze
        analysis = agent.analyze_opportunity(formatted)
        final_score = analysis.get("final_score", 0)

        print(f"📊 {sub['title'][:50]}...")
        print(f"   Score: {final_score:.1f}/100")

        # Generate AI profile for high scores (using 30.0 threshold for testing)
        if llm_profiler and final_score >= 30.0:
            print("   🎯 Score >= 30! Generating AI profile...")
            try:
                ai_profile = llm_profiler.generate_app_profile(
                    text=formatted["text"],
                    title=formatted["title"],
                    subreddit=formatted["subreddit"],
                    score=final_score
                )

                # Merge AI profile into analysis
                analysis.update(ai_profile)
                print(f"   ✨ AI Profile: {ai_profile.get('app_concept', 'N/A')[:60]}...")
            except Exception as e:
                print(f"   ⚠️  AI profile failed: {e}")

        # Prepare for storage
        scored_opp = {
            "opportunity_id": sub.get("id"),
            "app_name": sub.get("title", "Unknown")[:255],
            "function_count": len(analysis.get("core_functions", [])),
            "function_list": analysis.get("core_functions", []),
            "original_score": sub.get("score", 0),
            "final_score": final_score,
            "status": "analyzed",
            "problem_description": analysis.get("problem_description", ""),
            "app_concept": analysis.get("app_concept", ""),
            "value_proposition": analysis.get("value_proposition", ""),
            "target_user": analysis.get("target_user", ""),
            "monetization_model": analysis.get("monetization_model", "")
        }

        scored_opportunities.append(scored_opp)
        print()

    return scored_opportunities


def store_opportunities(supabase, scored_opportunities):
    """Store opportunities using DLT with deduplication"""

    print("="*80)
    print("STEP 3: Storing Results via DLT")
    print("="*80)

    # Skip workflow_results (DLT-managed table) for this test
    print("\n📤 Skipping workflow_results (DLT-managed table)")

    # Store AI profiles to app_opportunities via DLT (with deduplication)
    print("\n📤 Storing AI profiles to app_opportunities via DLT...")

    # Transform to app_opportunities format
    ai_profiles = []
    for opp in scored_opportunities:
        if not opp.get("problem_description"):
            continue

        ai_profiles.append({
            "submission_id": opp.get("opportunity_id"),
            "problem_description": opp.get("problem_description"),
            "app_concept": opp.get("app_concept"),
            "core_functions": opp.get("function_list", []),
            "value_proposition": opp.get("value_proposition"),
            "target_user": opp.get("target_user"),
            "monetization_model": opp.get("monetization_model"),
            "opportunity_score": float(opp.get("final_score", 0)),
            "title": opp.get("app_name", ""),
            "subreddit": opp.get("opportunity_id", "").split("_")[0] if "_" in opp.get("opportunity_id", "") else "",
            "reddit_score": int(opp.get("original_score", 0)),
            "status": "discovered"
        })

    if ai_profiles:
        from core.dlt_app_opportunities import load_app_opportunities
        success = load_app_opportunities(ai_profiles)
        if success:
            print(f"\n✓ Stored {len(ai_profiles)} AI profiles (deduplicated on submission_id)")
        else:
            print("\n⚠️  Failed to store AI profiles via DLT")
    else:
        print("\n  No AI profiles to store (score threshold not met)")


def verify_results(supabase):
    """Verify data in both tables"""

    print("\n" + "="*80)
    print("STEP 4: Verification")
    print("="*80)

    # Check workflow_results
    wf_result = supabase.table('workflow_results').select('*').execute()
    print(f"\nworkflow_results: {len(wf_result.data)} rows")

    # Check app_opportunities
    app_result = supabase.table('app_opportunities').select('*').execute()
    print(f"app_opportunities: {len(app_result.data)} rows")

    # Check top_opportunities view
    top_result = supabase.table('top_opportunities').select('*').execute()
    print(f"top_opportunities view: {len(top_result.data)} rows (score > 40)")

    if top_result.data:
        print("\n🎯 High-Score Opportunities:")
        for opp in top_result.data:
            print(f"\n  Score: {opp.get('opportunity_score', 0):.1f}")
            print(f"  Problem: {opp.get('problem_description', 'N/A')[:80]}...")
            print(f"  App: {opp.get('app_concept', 'N/A')[:80]}...")


def main():
    print("\n" + "="*80)
    print("E2E TEST: Small Batch Opportunity Detection")
    print("="*80)

    # Initialize clients
    supabase = create_client(
        os.getenv('SUPABASE_URL', 'http://127.0.0.1:54321'),
        os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU')
    )

    try:
        llm_profiler = LLMProfiler()
        print("✓ LLM Profiler: Ready (Claude Haiku)")
    except Exception as e:
        print(f"⚠️  LLM Profiler unavailable: {e}")
        llm_profiler = None

    # Run E2E test
    test_subs, test_uuids = create_test_submissions(supabase)
    scored_opportunities = run_scoring(supabase, llm_profiler, test_uuids)
    store_opportunities(supabase, scored_opportunities)
    verify_results(supabase)

    print("\n" + "="*80)
    print("✅ E2E TEST COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Check Supabase Studio: http://127.0.0.1:54323")
    print("2. Query app_opportunities table")
    print("3. Run: marimo run marimo_notebooks/opportunity_dashboard_fixed.py")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
