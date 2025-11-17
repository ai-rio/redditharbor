#!/usr/bin/env python3
"""
Minimal test to check if dspy is causing the connection pool exhaustion.
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment
from dotenv import load_dotenv
load_dotenv(project_root / '.env.local')

print("Testing dspy/MonetizationLLMAnalyzer connection pool behavior...")
print("="*80)

# Import HTTP client config (triggers auto-init)
import core.http_client_config

# Import MonetizationLLMAnalyzer
from agent_tools.monetization_llm_analyzer import MonetizationLLMAnalyzer

print("\nInitializing MonetizationLLMAnalyzer...")
analyzer = MonetizationLLMAnalyzer()
print("✓ Analyzer initialized")

# Try making multiple sequential calls
print("\nMaking 10 sequential monetization analysis calls...")
test_opportunity = {
    "problem_description": "I need to track my expenses better",
    "app_concept": "Expense tracking app with AI categorization",
    "core_functions": ["Track expenses", "AI categorization", "Budget alerts"],
    "value_proposition": "Automatic expense tracking that saves time",
    "target_user": "Busy professionals who want to manage finances",
    "monetization_model": "Freemium with $9.99/month premium"
}

for i in range(10):
    try:
        print(f"  Call {i+1}...", end=" ", flush=True)
        result = analyzer.analyze(test_opportunity, subreddit="personalfinance")
        print(f"✓ Success (score: {result['monetization_score']:.1f})")
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        break

print("\n" + "="*80)
print("Test complete!")
