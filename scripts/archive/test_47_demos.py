#!/usr/bin/env python3
"""
Test AI on the "47 demos" post specifically
"""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import functions directly from the file
import importlib.util

from supabase import create_client

spec = importlib.util.spec_from_file_location("gen_insights", "scripts/generate_opportunity_insights_openrouter.py")
gen_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen_mod)

generate_insight_with_openrouter = gen_mod.generate_insight_with_openrouter
RateLimiter = gen_mod.RateLimiter
validate_insight = gen_mod.validate_insight

# Load env
load_dotenv(project_root / '.env.local')
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Get the "47 demos" post
print("=" * 80)
print("TESTING AI ON '47 DEMOS' POST")
print("=" * 80)

result = supabase.table("submissions").select("*").ilike("title", "%47 demos%").execute()
if not result.data:
    print("❌ '47 demos' post not found")
    sys.exit(1)

post = result.data[0]
sub_id = post['id']

print(f"\nTitle: {post['title']}")
print(f"Subreddit: r/{post['subreddit']}")
print(f"Text: {post['text'][:400]}...")

# Get comments
result = supabase.table("comments").select("body").eq("submission_id", sub_id).order("upvotes", desc=True).limit(3).execute()
comments = [c['body'] for c in result.data]
top_comments = "\n---\n".join(comments)

print(f"\nComments ({len(comments)}):")
for i, c in enumerate(comments, 1):
    print(f"  {i}. {c[:150]}...")

# Get opportunity scores
result = supabase.table("opportunity_analysis").select("*").eq("submission_id", sub_id).execute()
opp = result.data[0] if result.data else {}

print("\n=== OPPORTUNITY SCORES ===")
print(f"Final Score: {opp.get('final_score', 0):.1f}")
print(f"Market Demand: {opp.get('market_demand', 0):.1f}")
print(f"Pain Intensity: {opp.get('pain_intensity', 0):.1f}")
print(f"Monetization: {opp.get('monetization_potential', 0):.1f}")
print(f"Simplicity: {opp.get('simplicity_score', 0):.1f}")

# Generate AI insight
print("\n=== GENERATING AI INSIGHT ===")
scores = {
    'market_demand': opp.get('market_demand', 0),
    'pain_intensity': opp.get('pain_intensity', 0),
    'monetization_potential': opp.get('monetization_potential', 0),
    'simplicity_score': opp.get('simplicity_score', 0)
}

rate_limiter = RateLimiter(min_delay=0, max_delay=0)
insight = generate_insight_with_openrouter(
    post['title'],
    post['text'],
    scores,
    rate_limiter,
    top_comments
)

if insight:
    print("\n✅ AI RESPONSE:")
    print(json.dumps(insight, indent=2))

    # Validate
    is_valid, reason = validate_insight(insight, scores['monetization_potential'])
    if is_valid:
        print(f"\n✅ VALIDATION PASSED: {reason}")
    else:
        print(f"\n❌ VALIDATION FAILED: {reason}")
else:
    print("\n❌ AI rejected/null response")
    print("The AI sees this as not having a clear app opportunity.")
    print("\nThis suggests the prompt is still too strict or app-focused.")
    print("We need a problem-first approach!")
