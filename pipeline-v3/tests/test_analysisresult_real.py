#!/usr/bin/env python3
"""
Test AnalysisResult validation using valid AppIdea data
"""

import pytest
from datetime import datetime, timezone, timedelta
from models.analysis import AppIdea, MarketMetrics, AnalysisResult

def create_valid_app_idea():
    """Create a valid AppIdea for testing"""
    return AppIdea(
        title="Task Management Application",
        app_concept="A productivity tool that helps freelancers manage client projects and track billable hours using automated time tracking and invoicing features.",
        problem_statement="Freelancers struggle with manual time tracking, inconsistent invoicing, and difficulty managing multiple client projects simultaneously in their current workflow.",
        target_audience="Freelance professionals and independent consultants who work with multiple clients and bill by the hour.",
        core_functions=["Track billable hours automatically", "Generate professional invoices", "Manage client projects and deadlines"]
    )

def test_missing_cross_model_validation():
    """Test cross-model validation in AnalysisResult - SHOULD PASS"""
    # Using valid AppIdea and INCONSISTENT metrics (like the schema test)
    idea = create_valid_app_idea()

    # Use metrics that are individually valid but create inconsistency at AnalysisResult level
    # These metrics pass MarketMetrics validation but should fail AnalysisResult cross-validation
    inconsistent_metrics = MarketMetrics(
        market_demand=25.0,     # Low market demand
        pain_intensity=30.0,     # Low pain intensity
        monetization_potential=35.0,  # Low monetization potential
        competition_level=40.0,     # Low competition
        technical_feasibility=45.0   # Low technical feasibility
    )

    # This should fail - final score is too inconsistent with component metrics
    # Expected average: (25 + 30 + 35 + 45) / 4 = 33.75
    with pytest.raises(ValueError, match="Final score inconsistency"):
        AnalysisResult(
            submission_id="test456",
            app_idea=idea,
            market_metrics=inconsistent_metrics,
            final_score=90.0,        # Too high compared to metrics average of 33.75
            confidence_score=80.0,
            trust_level="HIGH"
        )

    # This should work - final score is consistent with component metrics
    analysis = AnalysisResult(
        submission_id="test123",
        app_idea=idea,
        market_metrics=inconsistent_metrics,
        final_score=35.0,        # Consistent with metrics average ~33.75
        confidence_score=80.0,
        trust_level="HIGH"
    )

def test_missing_embedding_validation():
    """Test that embedding vector is properly validated - SHOULD PASS"""
    idea = create_valid_app_idea()

    metrics = MarketMetrics(
        market_demand=70.0,
        pain_intensity=75.0,
        monetization_potential=80.0,
        competition_level=65.0,
        technical_feasibility=85.0
    )

    # Valid embedding should work
    valid_embedding = [0.1] * 384  # Typical embedding size
    analysis = AnalysisResult(
        submission_id="test123",
        app_idea=idea,
        market_metrics=metrics,
        final_score=75.0,
        confidence_score=80.0,
        trust_level="HIGH",
        embedding=valid_embedding
    )
    assert len(analysis.embedding) == 384

    # Test embeddings that should be caught by our validation
    # These should trigger our custom validation with "Invalid embedding vector" message
    invalid_embeddings = [
        [],                    # Empty vector - should trigger our validation
        [1.0, 2.0],            # Too short - should trigger our validation
        [1.0] * 10001,         # Too long - should trigger our validation
        [float('inf')],       # Infinite values - should trigger our validation
        [float('nan')],       # NaN values - should trigger our validation
    ]

    for embedding in invalid_embeddings:
        with pytest.raises(ValueError, match="Invalid embedding vector"):
            AnalysisResult(
                submission_id="test123",
                app_idea=idea,
                market_metrics=metrics,
                final_score=75.0,
                confidence_score=80.0,
                trust_level="HIGH",
                embedding=embedding
            )

    # Test type validation - Pydantic catches these first with ValidationError
    # We expect these to fail during type validation, not our custom validation
    type_invalid_embeddings = [
        ["not a float"],       # Wrong type - Pydantic catches this first
    ]

    for embedding in type_invalid_embeddings:
        with pytest.raises((ValueError, TypeError)):  # Accept either error type
            AnalysisResult(
                submission_id="test123",
                app_idea=idea,
                market_metrics=metrics,
                final_score=75.0,
                confidence_score=80.0,
                trust_level="HIGH",
                embedding=embedding
            )

def test_missing_timestamp_validation():
    """Test that analyzed_at timestamp is validated - SHOULD PASS"""
    idea = create_valid_app_idea()

    metrics = MarketMetrics(
        market_demand=70.0,
        pain_intensity=75.0,
        monetization_potential=80.0,
        competition_level=65.0,
        technical_feasibility=85.0
    )

    # Recent timestamp should work
    recent_timestamp = datetime.now(timezone.utc) - timedelta(days=1)
    analysis = AnalysisResult(
        submission_id="test123",
        app_idea=idea,
        market_metrics=metrics,
        final_score=75.0,
        confidence_score=80.0,
        trust_level="HIGH",
        analyzed_at=recent_timestamp
    )
    assert analysis.analyzed_at == recent_timestamp

    # Old timestamp should fail
    old_timestamp = datetime.now(timezone.utc) - timedelta(days=365)

    with pytest.raises(ValueError, match="Analysis timestamp is too old"):
        AnalysisResult(
            submission_id="test123",
            app_idea=idea,
            market_metrics=metrics,
            final_score=75.0,
            confidence_score=80.0,
            trust_level="HIGH",
            analyzed_at=old_timestamp
        )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])