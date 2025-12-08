#!/usr/bin/env python3
"""
Test P2 OpportunityCreate database constraint validation using legacy compatibility mode
"""

from datetime import UTC, datetime, timezone

import pytest

from models.database import OpportunityCreate
from services.validation_service import TestDatabaseValidator, ValidationService


@pytest.fixture
def legacy_test_validator():
    """Create legacy test validator for backward compatibility"""
    return TestDatabaseValidator()


@pytest.fixture
def legacy_validation_service(legacy_test_validator):
    """Create validation service for legacy testing"""
    return ValidationService(legacy_test_validator)


def test_p2_database_constraint_validation(legacy_validation_service, legacy_test_validator):
    """Test P2 database constraint validation - duplicate submission ID should be rejected"""

    # Reset validation state for clean test
    legacy_test_validator.clear_state()

    # First OpportunityCreate should succeed - using factory method with validation service
    create1 = OpportunityCreate.create_with_validation(
        validation_service=legacy_validation_service,
        submission_id="test123",
        reddit_title="Test Title",
        reddit_url="https://reddit.com/r/test/test123",
        subreddit="test",
        reddit_author="testuser",
        reddit_upvotes=100,
        reddit_comments_count=25,
        reddit_created_at=datetime.now(UTC),
        app_title="Test App",
        app_concept="A test application for validation testing",
        problem_statement="A test problem for validation testing",
        target_audience="Test users",
        core_functions=["test function"],
        market_demand=70.0,
        pain_intensity=75.0,
        monetization_potential=80.0,
        competition_level=65.0,
        technical_feasibility=85.0,
        final_score=75.0,
        confidence_score=80.0,
        trust_level="HIGH"
    )

    # Manually track this submission ID to simulate database persistence
    legacy_test_validator.add_used_submission_id("test123")

    print(f"✓ First OpportunityCreate succeeded: {create1.submission_id}")

    # Second OpportunityCreate with same ID should fail during database validation
    create2 = OpportunityCreate.create_with_validation(
        validation_service=legacy_validation_service,
        submission_id="test123",  # Same ID should trigger validation error
        reddit_title="Another Test Title",
        reddit_url="https://reddit.com/r/test/another123",
        subreddit="test",
        reddit_author="testuser2",
        reddit_upvotes=150,
        reddit_comments_count=35,
        reddit_created_at=datetime.now(UTC),
        app_title="Another Test App",
        app_concept="Another test application for validation testing",
        problem_statement="Another test problem for validation testing",
        target_audience="Another test users",
        core_functions=["another test function"],
        market_demand=65.0,
        pain_intensity=70.0,
        monetization_potential=75.0,
        competition_level=60.0,
        technical_feasibility=80.0,
        final_score=70.0,
        confidence_score=75.0,
        trust_level="MEDIUM"
    )

    # Database validation is now async, so we test it separately
    import asyncio
    with pytest.raises(ValueError, match="Duplicate submission ID"):
        asyncio.run(create2.validate_database_constraints())

    print("✓ Duplicate submission ID correctly rejected")


def test_p2_foreign_key_validation(legacy_validation_service):
    """Test P2 foreign key validation - invalid submission ID should be rejected"""

    # OpportunityCreate with "nonexistent123" should fail during async validation
    create = OpportunityCreate.create_with_validation(
        validation_service=legacy_validation_service,
        submission_id="nonexistent123",  # This should trigger our validation
        reddit_title="Test Title",
        reddit_url="https://reddit.com/r/test/test123",
        subreddit="test",
        reddit_author="testuser",
        reddit_upvotes=100,
        reddit_comments_count=25,
        reddit_created_at=datetime.now(UTC),
        app_title="Test App",
        app_concept="A test application for validation testing",
        problem_statement="A test problem for validation testing",
        target_audience="Test users",
        core_functions=["test function"],
        market_demand=70.0,
        pain_intensity=75.0,
        monetization_potential=80.0,
        competition_level=65.0,
        technical_feasibility=85.0,
        final_score=75.0,
        confidence_score=80.0,
        trust_level="HIGH"
    )

    # Database validation is now async, so we test it separately
    import asyncio
    with pytest.raises(ValueError, match="Invalid submission ID"):
        asyncio.run(create.validate_database_constraints())

    print("✓ Invalid submission ID correctly rejected")


def test_p2_validation_success(legacy_validation_service):
    """Test that valid OpportunityCreate instances work correctly"""

    # This should succeed - no special IDs
    create = OpportunityCreate.create_with_validation(
        validation_service=legacy_validation_service,
        submission_id="valid123",  # This should work fine
        reddit_title="Test Title",
        reddit_url="https://reddit.com/r/test/test123",
        subreddit="test",
        reddit_author="testuser",
        reddit_upvotes=100,
        reddit_comments_count=25,
        reddit_created_at=datetime.now(UTC),
        app_title="Test App",
        app_concept="A test application for validation testing",
        problem_statement="A test problem for validation testing",
        target_audience="Test users",
        core_functions=["test function"],
        market_demand=70.0,
        pain_intensity=75.0,
        monetization_potential=80.0,
        competition_level=65.0,
        technical_feasibility=85.0,
        final_score=75.0,
        confidence_score=80.0,
        trust_level="HIGH"
    )

    # Should pass database validation
    import asyncio
    asyncio.run(create.validate_database_constraints())

    print(f"✓ Valid OpportunityCreate succeeded: {create.submission_id}")


def test_backward_compatibility_without_validation_service():
    """Test that OpportunityCreate still works without validation service for legacy code"""

    # This should work without validation service (skip database validation)
    create = OpportunityCreate(
        submission_id="legacy123",
        reddit_title="Test Title",
        reddit_url="https://reddit.com/r/test/test123",
        subreddit="test",
        reddit_author="testuser",
        reddit_upvotes=100,
        reddit_comments_count=25,
        reddit_created_at=datetime.now(UTC),
        app_title="Test App",
        app_concept="A test application for validation testing",
        problem_statement="A test problem for validation testing",
        target_audience="Test users",
        core_functions=["test function"],
        market_demand=70.0,
        pain_intensity=75.0,
        monetization_potential=80.0,
        competition_level=65.0,
        technical_feasibility=85.0,
        final_score=75.0,
        confidence_score=80.0,
        trust_level="HIGH"
    )

    assert create._validation_service is None
    print(f"✓ Legacy OpportunityCreate succeeded without validation service: {create.submission_id}")

if __name__ == "__main__":
    print("=== Testing P2 OpportunityCreate Validation ===")

    print("\n1. Testing successful valid creation...")
    test_p2_validation_success()

    print("\n2. Testing duplicate submission ID rejection...")
    test_p2_database_constraint_validation()

    print("\n3. Testing invalid submission ID rejection...")
    test_p2_foreign_key_validation()

    print("\n✅ All P2 validation tests passed!")
