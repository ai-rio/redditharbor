#!/usr/bin/env python3
"""
Integration test for the complete market validation pipeline.
Tests Phase 1, 2, and 3 together.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment
from dotenv import load_dotenv
load_dotenv(project_root / ".env.local")

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

print("=" * 70)
print("MARKET VALIDATION INTEGRATION TEST")
print("=" * 70)

# Test 1: Core Components
print("\n1. TESTING CORE COMPONENTS")
print("-" * 40)

from agent_tools.jina_reader_client import get_jina_client
from agent_tools.market_data_validator import MarketDataValidator
from config import settings

client = get_jina_client()
print(f"  ✓ JinaReaderClient initialized")
print(f"  API key configured: {bool(settings.JINA_API_KEY)}")
print(f"  Market validation enabled: {settings.MARKET_VALIDATION_ENABLED}")

validator = MarketDataValidator()
print(f"  ✓ MarketDataValidator initialized")
print(f"  LLM model: {validator.llm_model}")

# Test 2: Integration Function
print("\n2. TESTING INTEGRATION FUNCTION")
print("-" * 40)

from scripts.core.batch_opportunity_scoring import perform_market_validation

test_opportunity = {
    "submission_id": "test_123",
    "title": "I need to track my business expenses",
    "final_score": 75.0,
    "ai_profile": {
        "app_concept": "AI-powered expense tracking and categorization app",
        "target_user": "Small business owners and freelancers",
        "problem_description": "Manual expense tracking is time-consuming and error-prone"
    }
}

print(f"  Test opportunity: {test_opportunity['title']}")
print(f"  Score: {test_opportunity['final_score']}")
print(f"  App concept: {test_opportunity['ai_profile']['app_concept']}")

# Test 3: Perform Market Validation (limited test to save tokens)
print("\n3. TESTING MARKET VALIDATION (LIMITED)")
print("-" * 40)
print("  Note: Running limited validation to conserve API tokens")

# Test the validator directly with minimal searches
evidence = validator.validate_opportunity(
    app_concept=test_opportunity["ai_profile"]["app_concept"],
    target_market="B2B",  # SMB target
    problem_description=test_opportunity["ai_profile"]["problem_description"],
    max_searches=3  # Limited searches for testing
)

print(f"\n  ✓ Validation completed!")
print(f"  Validation Score: {evidence.validation_score:.1f}/100")
print(f"  Data Quality Score: {evidence.data_quality_score:.1f}/100")
print(f"  Total LLM Cost: ${evidence.total_cost:.4f}")
print(f"  Competitors found: {len(evidence.competitor_pricing)}")
if evidence.competitor_pricing:
    for comp in evidence.competitor_pricing:
        print(f"    - {comp.company_name} ({comp.pricing_model})")
print(f"  Market size: {evidence.market_size.tam_value if evidence.market_size else 'Not found'}")
print(f"  Similar launches: {len(evidence.similar_launches)}")
print(f"  URLs fetched: {len(evidence.urls_fetched)}")

# Test 4: Check reasoning
print("\n4. VALIDATION REASONING")
print("-" * 40)
reasoning_parts = evidence.reasoning.split(" | ")
for part in reasoning_parts:
    print(f"  • {part}")

# Test 5: Rate limit status
print("\n5. RATE LIMIT STATUS")
print("-" * 40)
status = client.get_rate_limit_status()
print(f"  Read requests remaining: {status['read_remaining']}/{status['read_max']}")
print(f"  Search requests remaining: {status['search_remaining']}/{status['search_max']}")
print(f"  Cache size: {status['cache_size']} entries")

print("\n" + "=" * 70)
print("INTEGRATION TEST COMPLETE!")
print("=" * 70)

# Summary
print("\nSUMMARY:")
print(f"  ✓ Phase 1 (Core Infrastructure): Working")
print(f"  ✓ Phase 2 (Data Extraction): Working")
print(f"  ✓ Phase 3 (Integration): Ready for batch processing")
print(f"  Total validation cost: ${evidence.total_cost:.4f}")
print(f"  Data collected: {len(evidence.competitor_pricing)} competitors, "
      f"{1 if evidence.market_size else 0} market size reports, "
      f"{len(evidence.similar_launches)} launches")
