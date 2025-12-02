#!/usr/bin/env python3
"""
Simple Test for Enhanced Storage Fix

This is a simplified test that focuses on testing the EnhancedHybridStore
without complex configuration imports.

Created: 2025-11-22
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env.local")

# Import settings directly
import config.settings as settings
from supabase import create_client

def test_enhanced_store():
    """Test EnhancedHybridStore functionality."""
    print("Testing EnhancedHybridStore...")

    try:
        # Import the enhanced store
        from core.storage.enhanced_hybrid_store import EnhancedHybridStore
        print("✓ EnhancedHybridStore imported successfully")

        # Create test data
        test_data = [{
            "submission_id": "test_enhanced_123",
            "title": "Test submission for enhanced storage",
            "content": "This is a test to verify enhanced storage works",
            "subreddit": "test",

            # Opportunity data
            "final_score": 85.0,
            "dimension_scores": {
                "market_demand": 0.9,
                "pain_intensity": 0.8,
                "competition_level": 0.6,
                "technical_feasibility": 0.7,
                "monetization_potential": 0.8,
            },
            "priority": "high",
            "confidence": 0.85,
            "evidence_based": True,
            "core_functions": ["Function 1", "Function 2"],
            "problem_description": "Test problem description",
            "target_user": "Test users",

            # Profiler data
            "profession": "Software Engineer",
            "ai_profile": {"score": 85.0},
            "app_name": "TestApp",
            "app_category": "Productivity",
            "core_problems": ["Problem 1", "Problem 2"],

            # Monetization data
            "willingness_to_pay_score": 75.0,
            "customer_segment": "B2B",
            "price_sensitivity_score": 60.0,
            "revenue_potential_score": 80.0,
            "llm_monetization_score": 78.0,

            # Trust data
            "trust_level": "medium",
            "overall_trust_score": 75.0,
            "trust_badges": ["quality_discussion"],

            # Market validation data
            "market_validation_score": 70.0,
            "market_data_quality_score": 80.0,
            "validation_reasoning": "Test validation reasoning",
            "market_competitors_found": [
                {"company_name": "Competitor1", "pricing_model": "subscription"}
            ],
            "market_similar_launches": 5,
        }]

        # Create Supabase client and enhanced store
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        store = EnhancedHybridStore(supabase_client=client)

        print("✓ EnhancedHybridStore initialized successfully")

        # Test storing the data
        success = store.store(test_data)

        if success:
            print("✓ Data stored successfully")

            # Get statistics
            stats = store.get_enhanced_statistics()
            print(f"  - Loaded: {stats.get('loaded', 0)}")
            print(f"  - Failed: {stats.get('failed', 0)}")
            print(f"  - Enrichment tables: {stats.get('enrichment_tables_written', [])}")

            # Test table validation
            from utils.enhanced_metrics import validate_enrichment_tables_populated
            validation = validate_enrichment_tables_populated(client, "test_enhanced_123")

            print("\nTable validation results:")
            populated = 0
            for table, has_data in validation.items():
                status = "✓" if has_data else "✗"
                print(f"  {status} {table}")
                if has_data:
                    populated += 1

            coverage = (populated / len(validation)) * 100
            print(f"\nTable coverage: {populated}/{len(validation)} ({coverage:.1f}%)")

            return coverage >= 80

        else:
            print("❌ Data storage failed")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("Enhanced Storage Fix Test")
    print("=" * 50)

    success = test_enhanced_store()

    print("\n" + "=" * 50)
    if success:
        print("✅ ENHANCED STORAGE FIX TEST PASSED")
        print("Enrichment data is being persisted to specialized tables correctly")
        return 0
    else:
        print("❌ ENHANCED STORAGE FIX TEST FAILED")
        print("Enrichment data persistence needs more work")
        return 1

if __name__ == "__main__":
    sys.exit(main())