#!/usr/bin/env python3
"""
Find more test candidates for problem-first approach
"""
import os
from dotenv import load_dotenv
load_dotenv('.env.local')
import requests

headers = {
    'apikey': os.getenv('SUPABASE_KEY'),
    'Authorization': f"Bearer {os.getenv('SUPABASE_KEY')}"
}

print('FINDING TEST CANDIDATES FOR PROBLEM-FIRST APPROACH')
print('='*60)

# Get all opportunity analysis records
response = requests.get(
    f"{os.getenv('SUPABASE_URL')}/rest/v1/opportunity_analysis?select=submission_id,title,final_score,comment_count,monetization_potential",
    headers=headers
)

if response.status_code == 200:
    all_opps = response.json()

    # Filter for posts with comments and low scores (likely real problems)
    candidates = []
    for opp in all_opps:
        if opp['comment_count'] > 0 and opp['final_score'] < 20:
            # Get submission text to check for problems
            sub_response = requests.get(
                f"{os.getenv('SUPABASE_URL')}/rest/v1/submissions?select=id,title,text&id=eq.{opp['submission_id']}",
                headers=headers
            )

            if sub_response.status_code == 200:
                sub_data = sub_response.json()
                if sub_data:
                    sub = sub_data[0]
                    text = sub.get('text', '').lower()

                    # Look for problem language
                    problem_words = ['struggle', 'problem', 'hard', 'annoying', 'tired', 'waste', 'difficult', 'annoyed']
                    if any(word in text for word in problem_words):
                        candidates.append({
                            'submission_id': opp['submission_id'],
                            'title': sub['title'],
                            'text': sub.get('text', ''),
                            'score': opp['final_score'],
                            'comments': opp['comment_count'],
                            'monetization': opp['monetization_potential']
                        })

    print(f'\nFound {len(candidates)} candidate posts\n')

    # Sort by score (lowest first = most likely real problems)
    candidates.sort(key=lambda x: x['score'])

    # Show top 5 candidates
    for i, cand in enumerate(candidates[:5], 1):
        print(f"{i}. {cand['title'][:70]}...")
        print(f"   Score: {cand['score']:.1f} | Comments: {cand['comments']} | Monetization: {cand['monetization']:.1f}")
        print(f"   Text: {cand['text'][:200]}...")
        print(f"   ID: {cand['submission_id']}")
        print()

    if len(candidates) >= 2:
        print(f"\n✅ RECOMMENDED TEST POSTS:")
        print(f"   1. {candidates[0]['title'][:60]}...")
        print(f"   2. {candidates[1]['title'][:60]}...")
    else:
        print(f"\n⚠️  Not enough candidates found")
        print(f"   We already have '47 demos' post as a test case")
        print(f"   Let's test it with problem-first approach")
