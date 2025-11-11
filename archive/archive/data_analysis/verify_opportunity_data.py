#!/usr/bin/env python3
"""
Data Verification Script for Monetizable Opportunity Research

This script verifies the data collection status against the methodology requirements
defined in docs/monetizable_app_research_methodology.md
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime

from config import SUPABASE_KEY, SUPABASE_URL
from supabase import create_client

# Market segments from methodology
METHODOLOGY_SUBREDDITS = {
    "Health & Fitness": [
        "fitness", "bodyweightfitness", "nutrition", "loseit", "gainit", "keto",
        "running", "cycling", "yoga", "meditation", "mentalhealth",
        "personaltraining", "homegym", "fitness30plus"
    ],
    "Finance & Investing": [
        "personalfinance", "investing", "stocks", "Bogleheads", "financialindependence",
        "CryptoCurrency", "cryptocurrencymemes", "Bitcoin", "ethfinance",
        "FinancialCareers", "tax", "Accounting", "RealEstateInvesting"
    ],
    "Education & Career": [
        "learnprogramming", "cscareerquestions", "IWantToLearn",
        "selfimprovement", "getdisciplined", "productivity", "study",
        "careerguidance", "resumes", "jobs", "interviews"
    ],
    "Travel & Experiences": [
        "travel", "solotravel", "backpacking", "digitalnomad",
        "TravelHacks", "flights", "airbnb", "cruise", "roadtrips",
        "AskTourism", "TravelTips", "Shoestring"
    ],
    "Real Estate": [
        "RealEstate", "realtors", "FirstTimeHomeBuyer", "HomeImprovement",
        "landlord", "Renting", "PropertyManagement", "Homeowners",
        "RealEstateTech", "houseflipper", "zillowgonewild"
    ],
    "Technology & SaaS Productivity": [
        "SaaS", "startups", "Entrepreneur", "SideProject",
        "antiwork", "workreform", "productivity", "selfhosted",
        "apphookup", "iosapps", "androidapps", "software"
    ]
}


def verify_data_collection():
    """Verify data collection status against methodology requirements"""

    print("=" * 80)
    print("RedditHarbor Data Collection Verification Report")
    print("=" * 80)
    print()

    # Connect to Supabase
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return

    print()
    print("-" * 80)
    print("OVERALL DATA SUMMARY")
    print("-" * 80)

    # Get overall statistics
    try:
        # Total submissions
        result = supabase.table("submission").select("*", count="exact").execute()
        total_submissions = result.count
        print(f"Total Submissions: {total_submissions:,}")

        # Total comments
        result = supabase.table("comment").select("*", count="exact").execute()
        total_comments = result.count
        print(f"Total Comments: {total_comments:,}")

        # Get subreddit breakdown
        result = supabase.rpc("get_submission_counts_by_subreddit").execute()
        if result.data:
            subreddit_data = result.data
        else:
            # Fallback: get unique subreddits manually
            result = supabase.table("submission").select("subreddit").execute()
            subreddits = set(row["subreddit"] for row in result.data if row.get("subreddit"))
            print(f"Unique Subreddits: {len(subreddits)}")
            subreddit_data = []
            for sub in subreddits:
                count = supabase.table("submission").select("*", count="exact").eq("subreddit", sub).execute().count
                subreddit_data.append({"subreddit": sub, "count": count})

    except Exception as e:
        print(f"❌ Error fetching summary: {e}")
        subreddit_data = []

    print()
    print("-" * 80)
    print("DATA COLLECTION BY MARKET SEGMENT")
    print("-" * 80)

    # Check coverage for each market segment
    collected_subreddits = {item["subreddit"].lower() for item in subreddit_data if "subreddit" in item}

    total_required = 0
    total_collected = 0
    segment_results = []

    for segment, required_subs in METHODOLOGY_SUBREDDITS.items():
        total_required += len(required_subs)

        # Check which subreddits have data
        required_lower = [sub.lower() for sub in required_subs]
        collected = [sub for sub in required_lower if sub in collected_subreddits]
        total_collected += len(collected)

        coverage = (len(collected) / len(required_subs)) * 100 if required_subs else 0

        segment_results.append({
            "segment": segment,
            "required": len(required_subs),
            "collected": len(collected),
            "coverage": coverage,
            "missing": [sub for sub in required_lower if sub not in collected_subreddits]
        })

        print(f"\n{segment}:")
        print(f"  Required: {len(required_subs)} subreddits")
        print(f"  Collected: {len(collected)} subreddits ({coverage:.1f}% coverage)")

        if collected:
            print(f"  ✅ Have data: {', '.join(collected[:5])}" + (" ..." if len(collected) > 5 else ""))

        if len(collected) < len(required_subs):
            missing_count = len(required_subs) - len(collected)
            sample_missing = segment_results[-1]["missing"][:3]
            print(f"  ❌ Missing: {missing_count} subreddits (e.g., {', '.join(sample_missing)})")

    print()
    print("-" * 80)
    print("COVERAGE SUMMARY")
    print("-" * 80)
    print(f"Overall Coverage: {total_collected}/{total_required} subreddits ({(total_collected/total_required)*100:.1f}%)")

    # Data quality metrics
    print()
    print("-" * 80)
    print("DATA QUALITY METRICS")
    print("-" * 80)

    # Check date ranges
    try:
        result = supabase.table("submission").select("created_at").order("created_at").limit(1).execute()
        earliest = result.data[0]["created_at"] if result.data else "N/A"

        result = supabase.table("submission").select("created_at").order("created_at", desc=True).limit(1).execute()
        latest = result.data[0]["created_at"] if result.data else "N/A"

        print(f"Date Range: {earliest} to {latest}")

        # Calculate if we have recent data (last 90 days as per methodology)
        if latest != "N/A":
            latest_dt = datetime.fromisoformat(latest.replace("Z", "+00:00"))
            days_ago = (datetime.now().astimezone() - latest_dt).days
            print(f"Latest Data: {days_ago} days ago")

            if days_ago <= 3:
                print("  ✅ Data is current (within 3 days)")
            elif days_ago <= 30:
                print("  ⚠️  Data is recent but not current (within 30 days)")
            else:
                print("  ❌ Data is stale (over 30 days old)")
    except Exception as e:
        print(f"❌ Error checking date ranges: {e}")

    # Check for pain indicators and monetization signals
    print()
    print("-" * 80)
    print("OPPORTUNITY DETECTION READINESS")
    print("-" * 80)

    pain_keywords = ["frustrated", "annoying", "terrible", "problem", "issue"]
    monetization_keywords = ["willing to pay", "subscription", "premium", "price", "cost"]

    try:
        # Sample check for pain indicators
        sample_posts = supabase.table("submission").select("title, text").limit(100).execute()

        pain_count = 0
        monetization_count = 0

        for post in sample_posts.data:
            text = (post.get("title", "") + " " + (post.get("text", "") or "")).lower()
            if any(keyword in text for keyword in pain_keywords):
                pain_count += 1
            if any(keyword in text for keyword in monetization_keywords):
                monetization_count += 1

        print("Sample Analysis (100 posts):")
        print(f"  Pain Indicators: {pain_count}% of sample posts")
        print(f"  Monetization Signals: {monetization_count}% of sample posts")

        if pain_count >= 10:
            print("  ✅ Sufficient pain indicators detected")
        else:
            print("  ⚠️  Low pain indicators - may need more data")

    except Exception as e:
        print(f"❌ Error checking opportunity signals: {e}")

    print()
    print("-" * 80)
    print("RECOMMENDATIONS")
    print("-" * 80)

    recommendations = []

    if total_collected < total_required * 0.3:
        recommendations.append("🔴 CRITICAL: Less than 30% of required subreddits have data. Run comprehensive data collection.")
    elif total_collected < total_required * 0.7:
        recommendations.append(f"🟡 WARNING: Only {(total_collected/total_required)*100:.0f}% coverage. Expand data collection to missing segments.")
    else:
        recommendations.append(f"🟢 GOOD: {(total_collected/total_required)*100:.0f}% coverage achieved. Focus on data quality and freshness.")

    if total_comments == 0:
        recommendations.append("🔴 CRITICAL: No comment data collected. Comments are essential for opportunity analysis.")

    # Check segments with no coverage
    zero_coverage = [r for r in segment_results if r["collected"] == 0]
    if zero_coverage:
        recommendations.append(f"🔴 Missing entire segments: {', '.join([r['segment'] for r in zero_coverage])}")

    for rec in recommendations:
        print(f"  {rec}")

    print()
    print("=" * 80)
    print("Report Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 80)

    return {
        "total_submissions": total_submissions,
        "total_comments": total_comments,
        "coverage_pct": (total_collected/total_required)*100,
        "segment_results": segment_results,
        "recommendations": recommendations
    }


if __name__ == "__main__":
    verify_data_collection()
