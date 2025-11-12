#!/usr/bin/env python3
"""
AI Profile Quality Investigation - Compare Good vs Bad AI Profiles
Shows the difference between specific LLM-generated profiles and generic template responses
"""

import pandas as pd
from pathlib import Path

def load_and_compare_profiles():
    """Load both datasets and compare quality"""

    print("🔍 AI PROFILE QUALITY INVESTIGATION")
    print("=" * 60)

    # Load good AI profiles (specific, detailed)
    try:
        good_profiles = pd.read_csv('db_dumps/ai_opportunities.csv')
        print(f"✅ Loaded {len(good_profiles)} detailed AI profiles from ai_opportunities.csv")
    except FileNotFoundError:
        print("❌ ai_opportunities.csv not found")
        return

    # Load bad AI profiles (generic template)
    try:
        bad_profiles = pd.read_csv('db_dumps/ai_profiles.csv')
        print(f"⚠️  Loaded {len(bad_profiles)} template profiles from ai_profiles.csv")
    except FileNotFoundError:
        print("❌ ai_profiles.csv not found")
        return

    print("\n" + "=" * 60)
    print("ANALYSIS: SPECIFIC vs GENERIC PROFILES")
    print("=" * 60)

    # Show examples of good profiles
    print("\n🎯 EXAMPLES OF HIGH-QUALITY SPECIFIC PROFILES:")
    print("-" * 50)

    for i, (_, profile) in enumerate(good_profiles.head(3).iterrows()):
        print(f"\n{i+1}. TITLE: {profile['app_name'][:60]}...")
        print(f"   SCORE: {profile['final_score']:.1f}")
        print(f"   PROBLEM: {profile['problem_description'][:80]}...")
        print(f"   SOLUTION: {profile['app_concept'][:80]}...")

        # Parse functions to show specificity
        try:
            import ast
            functions = ast.literal_eval(profile['function_list'])
            print(f"   FUNCTIONS ({len(functions)}):")
            for j, func in enumerate(functions[:2], 1):
                print(f"     {j}. {func[:40]}...")
        except:
            print(f"   FUNCTIONS: {profile['function_list'][:60]}...")

    # Show examples of bad profiles
    print("\n⚠️  EXAMPLES OF GENERIC TEMPLATE PROFILES:")
    print("-" * 50)

    for i, (_, profile) in enumerate(bad_profiles.head(3).iterrows()):
        print(f"\n{i+1}. TITLE: {profile['title'][:60]}...")
        print(f"   SCORE: {profile['opportunity_score']:.1f}")
        print(f"   PROBLEM: {profile['problem_description'][:80]}...")
        print(f"   SOLUTION: {profile['app_concept'][:80]}...")
        print(f"   FUNCTIONS: {profile['core_functions'][:60]}...")

    # Analysis of the pattern
    print("\n" + "=" * 60)
    print("PATTERN ANALYSIS:")
    print("=" * 60)

    # Check for generic patterns in bad profiles
    generic_patterns = [
        "Users struggle with",
        "and need better tools and solutions",
        "An app that helps users address",
        "User tracking",
        "Solution finder",
        "Community support",
        "Track progress and identify patterns",
        "Match users with relevant solutions",
        "Connect users with similar challenges"
    ]

    print("\n🔍 GENERIC PATTERN DETECTION:")
    for pattern in generic_patterns:
        bad_count = bad_profiles['problem_description'].str.contains(pattern, na=False).sum()
        good_count = good_profiles['problem_description'].str.contains(pattern, na=False).sum()

        print(f"   '{pattern[:30]}...':")
        print(f"     Generic profiles: {bad_count}/{len(bad_profiles)} ({bad_count/len(bad_profiles)*100:.1f}%)")
        print(f"     Specific profiles: {good_count}/{len(good_profiles)} ({good_count/len(good_profiles)*100:.1f}%)")

    # Score comparison
    print("\n📊 SCORE COMPARISON:")
    print(f"   Generic template profiles - Avg score: {bad_profiles['opportunity_score'].mean():.1f}")
    print(f"   Specific LLM profiles - Avg score: {good_profiles['final_score'].mean():.1f}")

    # Function count comparison
    print("\n🔧 FUNCTION COMPARISON:")
    generic_func_counts = bad_profiles['core_functions'].apply(lambda x: len(x.split(',')) if isinstance(x, str) else 0).value_counts().to_dict()
    specific_func_counts = good_profiles['function_count'].value_counts().to_dict()

    print(f"   Generic profiles - Function distribution: {generic_func_counts}")
    print(f"   Specific profiles - Function distribution: {specific_func_counts}")

    print("\n" + "=" * 60)
    print("ROOT CAUSE IDENTIFICATION:")
    print("=" * 60)
    print("""
🎯 KEY FINDING:
   The LLM profiler IS generating high-quality, specific app ideas with
   detailed functions and real problem analysis (see ai_opportunities.csv).

🔥 THE PROBLEM:
   Something in the data pipeline is OVERWRITING these good results with
   generic template responses, likely in the batch_opportunity_scoring.py
   script or in the database storage process.

📊 EVIDENCE:
   - ai_opportunities.csv: Contains specific, detailed AI profiles
   - ai_profiles.csv: Contains generic template responses
   - Both have similar titles but completely different content quality

🎯 NEXT STEPS:
   1. Identify where in the pipeline the good AI profiles get replaced
   2. Fix the data transformation that creates generic templates
   3. Ensure LLM-generated content is preserved throughout the pipeline
""")

if __name__ == "__main__":
    load_and_compare_profiles()