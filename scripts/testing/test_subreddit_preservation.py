#!/usr/bin/env python3
"""
Test Subreddit Field Preservation

Tests that subreddit field is properly preserved from original submission
to app_opportunities table along with AI-generated app metadata.
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

def test_subreddit_preservation():
    """Test that subreddit is preserved alongside app_name."""

    # Supabase configuration
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

        # Create submission data with both subreddit and AI-generated fields
        submission_with_subreddit = {
            "submission_id": "test_subreddit_preservation_123",
            "title": "Need feedback on project management tool",
            "content": "I've been working on a project management tool for remote teams...",
            "problem_description": "Remote teams struggle with project coordination and task tracking across different time zones.",
            "subreddit": "remotework",  # IMPORTANT: This must be preserved

            # AI-generated app metadata (simulating ProfilerService output)
            "app_name": "ProjectSync",
            "app_category": "Productivity",
            "core_functions": [
                "Task management",
                "Team collaboration",
                "Progress tracking"
            ],

            # Opportunity scoring data
            "final_score": 78.5,
            "dimension_scores": {
                "market_demand": 0.7,
                "pain_intensity": 0.8,
                "competition_level": 0.7,
                "technical_feasibility": 0.9,
                "monetization_potential": 0.6
            },
            "priority": "medium",
            "confidence": 0.8,
            "evidence_based": True,
        }

        logger.info("✓ Created submission with subreddit and AI metadata")

        # Test the enhanced store
        logger.info("🧪 Testing subreddit preservation...")

        result = enhanced_store.store([submission_with_subreddit])

        if result:
            logger.info("✅ EnhancedHybridStore.store() returned True")
        else:
            logger.error("❌ EnhancedHybridStore.store() returned False")
            return False

        # Verify the results directly from database
        logger.info("🔍 Verifying subreddit preservation in database...")

        # Get the UUID that was generated for our test submission
        import uuid
        namespace = uuid.uuid5(uuid.NAMESPACE_DNS, 'redditharbor-pipeline')
        expected_uuid = str(uuid.uuid5(namespace, "test_subreddit_preservation_123"))

        logger.info(f"Expected UUID for test submission: {expected_uuid}")

        # Query app_opportunities table
        response = supabase_client.table("app_opportunities").select("*").eq("submission_id", expected_uuid).execute()

        if response.data and len(response.data) > 0:
            record = response.data[0]
            logger.info("✅ Found record in app_opportunities table")
            logger.info(f"  • app_name: {record.get('app_name')}")
            logger.info(f"  • subreddit: {record.get('subreddit')}")
            logger.info(f"  • app_category: {record.get('app_category')}")

            # Verify subreddit is preserved
            if record.get('subreddit') == 'remotework':
                logger.info("🎉 SUCCESS: Subreddit field properly preserved!")
                return True
            else:
                logger.error(f"❌ FAILED: Expected subreddit='remotework', got '{record.get('subreddit')}'")
                return False
        else:
            logger.error("❌ FAILED: No record found in app_opportunities table")
            return False

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_subreddit_preservation()
    sys.exit(0 if success else 1)