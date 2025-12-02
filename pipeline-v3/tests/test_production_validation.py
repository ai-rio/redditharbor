#!/usr/bin/env python3
"""
Production validation tests for OpportunityCreate with ValidationService integration
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from models.database import OpportunityCreate
from services.validation_service import ValidationService, TestDatabaseValidator


class TestProductionValidation:
    """Test the new production-ready validation system"""

    @pytest.fixture
    def test_validator(self):
        """Create test database validator for testing"""
        return TestDatabaseValidator()

    @pytest.fixture
    def validation_service(self, test_validator):
        """Create validation service with test validator"""
        return ValidationService(test_validator)

    def test_opportunity_create_with_validation_service(self, validation_service):
        """Test creating OpportunityCreate with validation service injection"""
        opportunity = OpportunityCreate.create_with_validation(
            validation_service=validation_service,
            submission_id="test123",
            reddit_title="Test Title",
            reddit_url="https://reddit.com/r/test/test123",
            subreddit="test",
            reddit_author="testuser",
            reddit_upvotes=100,
            reddit_comments_count=25,
            reddit_created_at=datetime.now(timezone.utc),
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

        assert opportunity._validation_service is validation_service
        assert opportunity.submission_id == "test123"

    @pytest.mark.asyncio
    async def test_successful_database_validation(self, validation_service):
        """Test successful database validation with valid data"""
        opportunity = OpportunityCreate.create_with_validation(
            validation_service=validation_service,
            submission_id="valid123",
            reddit_title="Test Title",
            reddit_url="https://reddit.com/r/test/test123",
            subreddit="test",
            reddit_author="testuser",
            reddit_upvotes=100,
            reddit_comments_count=25,
            reddit_created_at=datetime.now(timezone.utc),
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

        # Should not raise any exceptions
        await opportunity.validate_database_constraints()

    @pytest.mark.asyncio
    async def test_duplicate_submission_id_rejection(self, validation_service, test_validator):
        """Test that duplicate submission IDs are rejected"""
        # Manually add a submission ID to simulate it already exists
        test_validator.add_used_submission_id("duplicate123")

        opportunity = OpportunityCreate.create_with_validation(
            validation_service=validation_service,
            submission_id="duplicate123",  # This should trigger duplicate validation error
            reddit_title="Test Title",
            reddit_url="https://reddit.com/r/test/test123",
            subreddit="test",
            reddit_author="testuser",
            reddit_upvotes=100,
            reddit_comments_count=25,
            reddit_created_at=datetime.now(timezone.utc),
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

        with pytest.raises(ValueError, match="Duplicate submission ID"):
            await opportunity.validate_database_constraints()

    @pytest.mark.asyncio
    async def test_invalid_submission_id_rejection(self, validation_service):
        """Test that invalid submission IDs are rejected"""
        opportunity = OpportunityCreate.create_with_validation(
            validation_service=validation_service,
            submission_id="nonexistent123",  # This should trigger foreign key validation error
            reddit_title="Test Title",
            reddit_url="https://reddit.com/r/test/test123",
            subreddit="test",
            reddit_author="testuser",
            reddit_upvotes=100,
            reddit_comments_count=25,
            reddit_created_at=datetime.now(timezone.utc),
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

        with pytest.raises(ValueError, match="Invalid submission ID"):
            await opportunity.validate_database_constraints()

    def test_opportunity_create_without_validation_service(self):
        """Test that OpportunityCreate works without validation service"""
        opportunity = OpportunityCreate(
            submission_id="no_validation123",
            reddit_title="Test Title",
            reddit_url="https://reddit.com/r/test/test123",
            subreddit="test",
            reddit_author="testuser",
            reddit_upvotes=100,
            reddit_comments_count=25,
            reddit_created_at=datetime.now(timezone.utc),
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

        assert opportunity._validation_service is None

        # Should not raise any exceptions - database validation is skipped
        # Note: In a real async context, this would be await opportunity.validate_database_constraints()
        # but for testing without validation service, it just returns None

    @pytest.mark.asyncio
    async def test_database_validation_skip_without_service(self):
        """Test that database validation is skipped when no service is provided"""
        opportunity = OpportunityCreate(
            submission_id="any_id_123",
            reddit_title="Test Title",
            reddit_url="https://reddit.com/r/test/test123",
            subreddit="test",
            reddit_author="testuser",
            reddit_upvotes=100,
            reddit_comments_count=25,
            reddit_created_at=datetime.now(timezone.utc),
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

        # Should not raise any exceptions
        await opportunity.validate_database_constraints()

    def test_to_db_model_conversion(self):
        """Test conversion to SQLAlchemy model still works"""
        opportunity = OpportunityCreate(
            submission_id="test123",
            reddit_title="Test Title",
            reddit_url="https://reddit.com/r/test/test123",
            subreddit="test",
            reddit_author="testuser",
            reddit_upvotes=100,
            reddit_comments_count=25,
            reddit_created_at=datetime.now(timezone.utc),
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

        db_model = opportunity.to_db_model()
        assert db_model.submission_id == "test123"
        assert db_model.reddit_title == "Test Title"
        assert db_model.app_title == "Test App"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])