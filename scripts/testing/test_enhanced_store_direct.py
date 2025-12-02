#!/usr/bin/env python3
"""
Direct Test of EnhancedHybridStore

This script directly tests the EnhancedHybridStore to verify it can write data
to enrichment tables. This bypasses the pipeline to isolate the storage issue.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from config.settings import SUPABASE_URL, SUPABASE_KEY

# Load environment variables
load_dotenv(project_root / '.env.local', override=True)
load_dotenv(project_root / '.env', override=False)

from supabase import create_client
from core.storage.enhanced_hybrid_store import EnhancedHybridStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_enhanced_store():
    """Test EnhancedHybridStore with sample data."""

    # Supabase configuration from environment variables (loaded in config/settings)
    if not SUPABASE_URL:
        raise ValueError("SUPABASE_URL environment variable is required")
    if not SUPABASE_KEY:
        raise ValueError("SUPABASE_KEY environment variable is required")

    try:
        # Initialize Supabase client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✓ Supabase client initialized")

        # Initialize EnhancedHybridStore
        enhanced_store = EnhancedHybridStore(supabase_client=supabase_client)
        logger.info("✓ EnhancedHybridStore initialized")

        # Create sample enriched submission data
        sample_submission = {
            "submission_id": "e7763e41-d7bf-4bf1-a004-decff9f0c5",
            "title": "Need feedback on timezone scheduling tool",
            "content": "I've been working on a timezone scheduling tool for remote teams...",
            "problem_description": "Remote teams struggle with timezone coordination when scheduling meetings across different time zones, leading to confusion and missed opportunities.",
            "app_concept": "AI-powered timezone scheduling tool that automatically finds optimal meeting times",
            "core_functions": "Automatic timezone detection, meeting scheduling, calendar integration, availability tracking",
            "subreddit": "remotework",

            # Opportunity scoring data
            "final_score": 85.5,
            "dimension_scores": {
                "market_demand": 0.8,
                "pain_intensity": 0.9,
                "competition_level": 0.6,
                "technical_feasibility": 0.8,
                "monetization_potential": 0.7
            },
            "priority": "high",
            "confidence": 0.85,
            "evidence_based": True,
            "core_functions": [
                "Timezone synchronization",
                "Calendar integration",
                "Meeting optimization"
            ],

            # Monetization data
            "willingness_to_pay_score": 75.0,
            "customer_segment": "B2B",
            "price_sensitivity_score": 60.0,
            "revenue_potential_score": 80.0,
            "mentioned_price_points": ["$10/month", "$100/year"],
            "existing_payment_behavior": "Currently using free tools",
            "urgency_level": "medium",
            "sentiment_toward_payment": "positive",
            "payment_friction_indicators": [],
            "llm_monetization_score": 70.0,
            "reasoning": "Teams actively need coordination tools",

            # Market validation data
            "market_validation_score": 85.0,
            "market_data_quality_score": 90.0,
            "market_validation_reasoning": "Several competing tools exist, validating market need",
            "market_competitors_found": [
                {"company_name": "Calendly", "features": ["Scheduling", "Timezone support"]},
                {"company_name": "World Time Buddy", "features": ["Timezone conversion", "Meeting planning"]}
            ],
            "market_size_tam": 50000000.0,
            "market_similar_launches": 15,
            "validation_reasoning": "Market validation shows strong demand"
        }

        logger.info("✓ Sample submission data created")

        # Test the enhanced store
        logger.info("🧪 Testing EnhancedHybridStore.store()...")

        result = enhanced_store.store([sample_submission])

        if result:
            logger.info("✅ EnhancedHybridStore.store() returned True")
        else:
            logger.error("❌ EnhancedHybridStore.store() returned False")
            return False

        # Get statistics
        stats = enhanced_store.get_enhanced_statistics()
        logger.info(f"📊 Enhanced Statistics: {json.dumps(stats, indent=2, default=str)}")

        # Test direct table queries
        logger.info("🔍 Testing direct table queries...")

        # Check app_opportunities
        response = supabase_client.table("app_opportunities").select("*").eq("submission_id", sample_submission["submission_id"]).execute()
        logger.info(f"✓ app_opportunities records: {len(response.data) if response.data else 0}")

        # Check opportunity_scores
        response = supabase_client.table("opportunity_scores").select("*").eq("opportunity_id", sample_submission["submission_id"]).execute()
        logger.info(f"✓ opportunity_scores records: {len(response.data) if response.data else 0}")

        # Check monetization_patterns
        response = supabase_client.table("monetization_patterns").select("*").eq("opportunity_id", sample_submission["submission_id"]).execute()
        logger.info(f"✓ monetization_patterns records: {len(response.data) if response.data else 0}")

        # Check market_validations
        response = supabase_client.table("market_validations").select("*").eq("opportunity_id", sample_submission["submission_id"]).execute()
        logger.info(f"✓ market_validations records: {len(response.data) if response.data else 0}")

        # Check competitive_landscape
        response = supabase_client.table("competitive_landscape").select("*").eq("opportunity_id", sample_submission["submission_id"]).execute()
        logger.info(f"✓ competitive_landscape records: {len(response.data) if response.data else 0}")

        logger.info("🎉 EnhancedHybridStore test completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ EnhancedHybridStore test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_store()
    sys.exit(0 if success else 1)