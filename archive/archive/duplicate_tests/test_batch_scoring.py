#!/usr/bin/env python3
"""
Test script for batch_opportunity_scoring.py
Validates core functions without processing all 6,127 submissions
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import directly without going through scripts package
import importlib.util

spec = importlib.util.spec_from_file_location(
    "batch_opportunity_scoring",
    project_root / "scripts" / "batch_opportunity_scoring.py"
)
batch_scoring = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch_scoring)

map_subreddit_to_sector = batch_scoring.map_subreddit_to_sector
format_submission_for_agent = batch_scoring.format_submission_for_agent
SECTOR_MAPPING = batch_scoring.SECTOR_MAPPING
from agent_tools.opportunity_analyzer_agent import OpportunityAnalyzerAgent
from config import SUPABASE_KEY, SUPABASE_URL
from supabase import create_client


def test_sector_mapping():
    """Test subreddit to sector mapping"""
    print("Testing sector mapping...")

    test_cases = [
        ("fitness", "Health & Fitness"),
        ("personalfinance", "Finance & Investing"),
        ("learnprogramming", "Education & Career"),
        ("travel", "Travel & Experiences"),
        ("realestate", "Real Estate"),
        ("saas", "Technology & SaaS"),
        ("unknownsubreddit", "Technology & SaaS"),  # Default
    ]

    for subreddit, expected in test_cases:
        result = map_subreddit_to_sector(subreddit)
        status = "PASS" if result == expected else "FAIL"
        print(f"  [{status}] {subreddit} -> {result}")

    print(f"Total sectors defined: {len(set(SECTOR_MAPPING.values()))}")
    print(f"Total subreddits mapped: {len(SECTOR_MAPPING)}\n")


def test_submission_formatting():
    """Test submission formatting for agent"""
    print("Testing submission formatting...")

    sample_submission = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "submission_id": "abc123",
        "title": "Looking for a better budgeting app",
        "text": "I'm frustrated with current options. They're too expensive.",
        "subreddit": "personalfinance",
        "upvotes": 245,
        "comments_count": 87,
        "sentiment_score": -0.35,
        "problem_keywords": "frustrated, expensive",
        "solution_mentions": "budgeting app"
    }

    formatted = format_submission_for_agent(sample_submission)

    assert "id" in formatted, "Missing id field"
    assert "title" in formatted, "Missing title field"
    assert "text" in formatted, "Missing text field"
    assert "subreddit" in formatted, "Missing subreddit field"
    assert "engagement" in formatted, "Missing engagement field"
    assert "comments" in formatted, "Missing comments field"
    assert formatted["engagement"]["upvotes"] == 245, "Incorrect upvotes"
    assert formatted["engagement"]["num_comments"] == 87, "Incorrect comments count"

    print(f"  [PASS] Formatted submission ID: {formatted['id']}")
    print(f"  [PASS] Text length: {len(formatted['text'])} chars")
    print(f"  [PASS] Engagement: {formatted['engagement']}")
    print(f"  [PASS] Comments extracted: {len(formatted['comments'])}\n")


def test_agent_analysis():
    """Test OpportunityAnalyzerAgent with sample data"""
    print("Testing OpportunityAnalyzerAgent...")

    agent = OpportunityAnalyzerAgent()

    sample_data = {
        "id": "test_001",
        "title": "Need better expense tracking tool",
        "text": "I'm desperate for a simple app to track my expenses. Current options are too complicated and expensive. I would pay for something that actually works.",
        "subreddit": "personalfinance",
        "engagement": {"upvotes": 150, "num_comments": 45},
        "comments": [
            "I hate my current expense tracker",
            "Why is there nothing simple available?"
        ]
    }

    result = agent.analyze_opportunity(sample_data)

    assert "dimension_scores" in result, "Missing dimension scores"
    assert "final_score" in result, "Missing final score"
    assert "priority" in result, "Missing priority"

    print("  [PASS] Analysis completed")
    print(f"  Final Score: {result['final_score']}")
    print(f"  Priority: {result['priority']}")
    print("  Dimension Scores:")
    for dim, score in result["dimension_scores"].items():
        print(f"    - {dim}: {score}")
    print()


def test_database_connection():
    """Test connection to Supabase and fetch a sample submission"""
    print("Testing database connection...")

    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Try to fetch one submission
        response = supabase.table("submissions").select("*").limit(1).execute()

        if response.data and len(response.data) > 0:
            print("  [PASS] Connected to database")
            print(f"  [PASS] Sample submission fetched: {response.data[0].get('submission_id')}")

            # Check if required fields exist
            sample = response.data[0]
            required_fields = ["id", "submission_id", "title", "subreddit"]
            for field in required_fields:
                if field in sample:
                    print(f"  [PASS] Field '{field}' exists")
                else:
                    print(f"  [WARN] Field '{field}' missing")
        else:
            print("  [WARN] No submissions found in database")

        # Check if opportunities table exists
        try:
            opp_response = supabase.table("opportunities").select("id").limit(1).execute()
            print("  [PASS] Opportunities table accessible")
        except Exception as e:
            print(f"  [WARN] Opportunities table issue: {e}")

        # Check if opportunity_scores table exists
        try:
            score_response = supabase.table("opportunity_scores").select("id").limit(1).execute()
            print("  [PASS] Opportunity_scores table accessible")
        except Exception as e:
            print(f"  [WARN] Opportunity_scores table issue: {e}")

        print()

    except Exception as e:
        print(f"  [FAIL] Database connection error: {e}\n")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("BATCH OPPORTUNITY SCORING - TEST SUITE")
    print("="*80 + "\n")

    try:
        test_sector_mapping()
        test_submission_formatting()
        test_agent_analysis()
        test_database_connection()

        print("="*80)
        print("All tests completed!")
        print("="*80 + "\n")

        print("Ready to run full batch scoring:")
        print("  python3 scripts/batch_opportunity_scoring.py")
        print("\nOr with UV:")
        print("  uv run python3 scripts/batch_opportunity_scoring.py\n")

    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
