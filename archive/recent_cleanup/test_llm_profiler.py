#!/usr/bin/env python3

from agent_tools.llm_profiler import LLMProfiler
import json

# Test with the example from the LLM profiler itself
profiler = LLMProfiler()

test_data = {
    "text": "I'm so frustrated with budgeting apps. They are all too expensive and none of them sync properly with my bank. I just want something simple that works and does not cost $15/month. Why is there no good solution for this?",
    "title": "Looking for a better budgeting app",
    "subreddit": "personalfinance",
    "score": 72.5
}

print('Testing with LLM profiler example data...')
profile = profiler.generate_app_profile(
    text=test_data["text"],
    title=test_data["title"],
    subreddit=test_data["subreddit"],
    score=test_data["score"]
)

print('\n=== LLM PROFILER RESPONSE ===')
print(json.dumps(profile, indent=2))
print('\nKey fields:')
print(f'app_name: {profile.get("app_name", "MISSING")}')
print(f'final_score: {profile.get("final_score", "MISSING")}')
print(f'app_concept: {profile.get("app_concept", "MISSING")}')
print(f'problem_description: {profile.get("problem_description", "MISSING")}')
print(f'core_functions: {profile.get("core_functions", "MISSING")}')