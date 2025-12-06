#!/usr/bin/env python3
"""
Minimal test to check exact database storage error
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from models.analysis import AnalysisResult, AppIdea, MarketMetrics
from models.reddit import RedditSubmission
from load.onlymaps_database import OnlyMapsDatabaseLoader

def test_minimal_storage():
    """Test storing a minimal valid analysis result"""
    print("=" * 60)
    print("MINIMAL DATABASE STORAGE TEST")
    print("=" * 60)

    # Create a minimal valid analysis result
    result = AnalysisResult(
        submission_id="minimal-test-2024",
        analyzed_at=datetime.now(timezone.utc),
        app_idea=AppIdea(
            title="Test App",
            app_concept="A test application for testing purposes",
            problem_statement="Test problem statement with enough words to meet validation requirements",
            target_audience="Test users for validation",
            core_functions=["Function 1", "Function 2"]
        ),
        market_metrics=MarketMetrics(
            market_demand=70.0,
            pain_intensity=60.0,
            monetization_potential=80.0,
            competition_level=50.0,
            technical_feasibility=90.0
        ),
        final_score=75.0,
        confidence_score=80.0,
        trust_level="HIGH",  # This should be valid
        content_quality_score=85.0,
        is_spam=False
    )

    print(f"Created test result with trust_level: {result.trust_level}")

    # Try to store it
    loader = OnlyMapsDatabaseLoader()

    try:
        loader.store_analyses([result])
        print("✅ Storage successful!")
        return True
    except Exception as e:
        print(f"❌ Storage failed: {e}")
        print(f"Error type: {type(e).__name__}")

        # If it's a database error, show the details
        if "value too long" in str(e).lower():
            print("\nField length issue detected. Checking field lengths...")

            # Check each field's length
            fields = {
                'trust_level': result.trust_level,
                'submission_id': result.submission_id,
                'app_title': result.app_idea.title,
                'app_concept': result.app_idea.app_concept[:100] + "..." if len(result.app_idea.app_concept) > 100 else result.app_idea.app_concept,
            }

            for field, value in fields.items():
                length = len(str(value)) if value else 0
                print(f"  {field}: '{value}' (length: {length})")

        return False

if __name__ == "__main__":
    if test_minimal_storage():
        print("\n✅ MINIMAL STORAGE TEST PASSED!")
        sys.exit(0)
    else:
        print("\n❌ MINIMAL STORAGE TEST FAILED!")
        sys.exit(1)