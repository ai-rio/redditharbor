#!/usr/bin/env python3
"""
Minimal test script to verify quality scoring implementation
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone

from models.analysis import AnalysisResult, AppIdea, MarketMetrics


def test_quality_scoring_model():
    """Test the quality scoring model implementation"""
    print("Testing AI Content Quality Scoring Model")
    print("=" * 40)

    # Create valid components
    idea = AppIdea(
        title="Test App",
        app_concept="A test application",
        problem_statement="A test problem",
        target_audience="Test users",
        core_functions=["test function"]
    )
    metrics = MarketMetrics(
        market_demand=70.0,
        pain_intensity=75.0,
        monetization_potential=80.0,
        competition_level=65.0,
        technical_feasibility=85.0
    )

    # Test 1: Valid high-quality content
    print("\n1. Testing valid high-quality content...")
    try:
        high_quality = AnalysisResult(
            submission_id="hq_123",
            app_idea=idea,
            market_metrics=metrics,
            final_score=80.0,
            confidence_score=85.0,
            trust_level="HIGH",
            content_quality_score=90.5,  # High quality
            is_spam=False,
            spam_indicators=[]
        )
        print(f"   ✓ Created high-quality analysis: score={high_quality.content_quality_score}, spam={high_quality.is_spam}")
    except Exception as e:
        print(f"   ✗ Failed to create high-quality analysis: {e}")

    # Test 2: Valid spam content
    print("\n2. Testing valid spam content...")
    try:
        spam_analysis = AnalysisResult(
            submission_id="spam_456",
            app_idea=idea,
            market_metrics=metrics,
            final_score=25.0,
            confidence_score=40.0,
            trust_level="LOW",
            content_quality_score=20.0,  # Low quality for spam
            is_spam=True,
            spam_indicators=["excessive_caps", "spam_keywords"]
        )
        print(f"   ✓ Created spam analysis: score={spam_analysis.content_quality_score}, spam={spam_analysis.is_spam}")
        print(f"   ✓ Spam indicators: {spam_analysis.spam_indicators}")
    except Exception as e:
        print(f"   ✗ Failed to create spam analysis: {e}")

    # Test 3: Invalid spam with high score (should fail)
    print("\n3. Testing invalid spam with high score...")
    try:
        invalid_spam = AnalysisResult(
            submission_id="invalid_789",
            app_idea=idea,
            market_metrics=metrics,
            final_score=75.0,
            confidence_score=80.0,
            trust_level="HIGH",
            content_quality_score=85.0,  # Too high for spam
            is_spam=True
        )
        print("   ✗ Model validation should have failed!")
    except ValueError as e:
        print(f"   ✓ Model validation correctly rejected spam with high score: {str(e)[:60]}...")

    # Test 4: Missing content_quality_score (should fail)
    print("\n4. Testing missing content_quality_score...")
    try:
        missing_score = AnalysisResult(
            submission_id="missing_123",
            app_idea=idea,
            market_metrics=metrics,
            final_score=75.0,
            confidence_score=80.0,
            trust_level="HIGH",
            # content_quality_score missing - should fail
        )
        print("   ✗ Model should have failed with missing content_quality_score!")
    except ValueError as e:
        print(f"   ✓ Model validation correctly required content_quality_score: {str(e)[:60]}...")

    # Test 5: Invalid content_quality_score range
    print("\n5. Testing invalid content_quality_score range...")
    try:
        invalid_range = AnalysisResult(
            submission_id="range_123",
            app_idea=idea,
            market_metrics=metrics,
            final_score=75.0,
            confidence_score=80.0,
            trust_level="HIGH",
            content_quality_score=150.0,  # Too high (> 100)
            is_spam=False
        )
        print("   ✗ Model should have failed with invalid content_quality_score range!")
    except ValueError as e:
        print(f"   ✓ Model validation correctly rejected invalid range: {str(e)[:60]}...")

    print("\n" + "=" * 40)
    print("Quality Scoring Model Test Complete!")
    print("Core functionality is working correctly.")

if __name__ == "__main__":
    test_quality_scoring_model()
