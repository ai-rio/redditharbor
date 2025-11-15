#!/usr/bin/env python3
"""
Test the EXACT execution path of the batch script to find the hang
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path - EXACT like batch script
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables - EXACT like batch script
from dotenv import load_dotenv
load_dotenv(project_root / '.env.local')

print("=" * 60)
print("TESTING EXACT BATCH SCRIPT EXECUTION PATH")
print("=" * 60)

print("1. Importing tqdm...")
try:
    from tqdm import tqdm
    print("   ✓ tqdm imported")
except ImportError as e:
    print(f"   ✗ tqdm failed: {e}")

print("2. Importing core modules...")
try:
    from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler
    from agent_tools.opportunity_analyzer_agent import OpportunityAnalyzerAgent
    from config import SUPABASE_KEY, SUPABASE_URL
    print("   ✓ Core modules imported")
except Exception as e:
    print(f"   ✗ Core modules failed: {e}")

print("3. Importing hybrid strategy modules...")
try:
    from agent_tools.monetization_llm_analyzer import MonetizationLLMAnalyzer
    from core.lead_extractor import LeadExtractor, convert_to_database_record
    print("   ✓ Hybrid strategy modules imported")
except Exception as e:
    print(f"   ✗ Hybrid strategy modules failed: {e}")

print("4. Importing DLT constraint validator...")
try:
    from core.dlt.constraint_validator import app_opportunities_with_constraint
    print("   ✓ DLT constraint validator imported")
except Exception as e:
    print(f"   ✗ DLT constraint validator failed: {e}")

print("5. Setting up HYBRID_STRATEGY_CONFIG...")
try:
    HYBRID_STRATEGY_CONFIG = {
        "option_a": {
            "enabled": os.getenv("MONETIZATION_LLM_ENABLED", "true").lower() == "true",
            "threshold": float(os.getenv("MONETIZATION_LLM_THRESHOLD", "60.0")),
            "model": os.getenv("MONETIZATION_LLM_MODEL", "openai/gpt-4o-mini"),
            "openrouter_key": os.getenv("OPENROUTER_API_KEY"),
        },
        "option_b": {
            "enabled": os.getenv("LEAD_EXTRACTION_ENABLED", "true").lower() == "true",
            "threshold": float(os.getenv("LEAD_EXTRACTION_THRESHOLD", "60.0")),
            "slack_webhook": os.getenv("SLACK_WEBHOOK_URL"),
        }
    }
    print("   ✓ HYBRID_STRATEGY_CONFIG created")
except Exception as e:
    print(f"   ✗ HYBRID_STRATEGY_CONFIG failed: {e}")

print("6. Testing database connection...")
try:
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = supabase.table('app_opportunities_trust').select('*').limit(46).execute()
    submissions = response.data
    print(f"   ✓ Database connected, got {len(submissions)} submissions")
except Exception as e:
    print(f"   ✗ Database connection failed: {e}")

print("7. Testing agent initialization...")
try:
    agent = OpportunityAnalyzerAgent()
    profiler = EnhancedLLMProfiler()
    print("   ✓ Agents initialized")
except Exception as e:
    print(f"   ✗ Agent initialization failed: {e}")

print("8. Testing tqdm loop creation...")
try:
    batch_size = 100
    print(f"   About to create tqdm loop with {len(submissions)} submissions...")

    # This is the EXACT line that hangs in the batch script
    for i in tqdm(range(0, len(submissions), batch_size), desc="Processing batches", unit="batch"):
        print(f"   ✓ TQDM loop created, iteration {i}")
        break  # Just test first iteration

except Exception as e:
    print(f"   ✗ TQDM loop failed: {e}")
    import traceback
    traceback.print_exc()

print("9. Testing format_submission_for_agent...")
try:
    sys.path.append(str(project_root / 'scripts' / 'core'))
    from batch_opportunity_scoring import format_submission_for_agent

    submission = submissions[0]
    formatted = format_submission_for_agent(submission)
    print(f"   ✓ format_submission_for_agent works: {formatted.get('title', 'No title')[:50]}...")
except Exception as e:
    print(f"   ✗ format_submission_for_agent failed: {e}")

print("10. Testing process_batch import...")
try:
    from batch_opportunity_scoring import process_batch
    print("   ✓ process_batch imported")
except Exception as e:
    print(f"   ✗ process_batch import failed: {e}")

print("11. Testing actual process_batch call...")
try:
    batch = submissions[:1]  # Just 1 submission
    print(f"   About to call process_batch with 1 submission...")

    results, scored_opps, ai_profiles_count = process_batch(
        batch, agent, 1, profiler, 30.0
    )

    print(f"   ✓ process_batch completed: {len(results)} results")
except Exception as e:
    print(f"   ✗ process_batch failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("EXACT EXECUTION TEST COMPLETE")
print("=" * 60)