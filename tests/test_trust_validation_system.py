"""
Comprehensive Test Suite for Trust Validation System

Tests the new decoupled trust validation system including:
- Service layer functionality
- Repository pattern implementation
- Data model validation and serialization
- Backward compatibility
- Error handling and edge cases

Run with: python -m pytest tests/test_trust_validation_system.py -v
"""

import pytest
import time
from datetime import datetime, UTC
from unittest.mock import Mock, patch, MagicMock

from core.trust import (
    TrustValidationService,
    TrustRepositoryFactory,
    TrustIndicators,
    TrustValidationRequest,
    TrustValidationResult,
    TrustScoreWeights,
    TrustBadgeConfig,
    TrustLevel,
    TrustBadge,
    TrustTables,
    TrustColumns,
    create_trust_service,
    validate_trust_compatibility
)
from core.trust.repository import (
    TrustRepositoryInterface,
    SupabaseTrustRepository,
    MultiTableTrustRepository
)


class TestTrustIndicators:
    """Test TrustIndicators data model."""

    def test_trust_indicators_creation(self):
        """Test creating trust indicators with valid data."""
        indicators = TrustIndicators(
            trust_score=85.5,
            trust_level=TrustLevel.HIGH,
            trust_badges=[TrustBadge.GOLD, TrustBadge.HIGH_ENGAGEMENT],
            activity_score=75.0,
            confidence_score=80.0
        )

        assert indicators.trust_score == 85.5
        assert indicators.trust_level == TrustLevel.HIGH
        assert indicators.trust_badges == [TrustBadge.GOLD, TrustBadge.HIGH_ENGAGEMENT]
        assert indicators.activity_score == 75.0
        assert indicators.confidence_score == 80.0

    def test_trust_indicators_validation(self):
        """Test trust indicators validation."""
        # Valid trust score
        indicators = TrustIndicators(trust_score=50.0)
        assert indicators.trust_score == 50.0

        # Invalid trust score should raise ValueError
        with pytest.raises(ValueError, match="Trust score must be between 0-100"):
            TrustIndicators(trust_score=150.0)

        with pytest.raises(ValueError, match="Trust score must be between 0-100"):
            TrustIndicators(trust_score=-10.0)

    def test_trust_indicators_serialization(self):
        """Test trust indicators serialization."""
        indicators = TrustIndicators(
            trust_score=75.0,
            trust_level=TrustLevel.MEDIUM,
            trust_badges=[TrustBadge.SILVER],
            validation_timestamp="2025-11-18T10:00:00Z"
        )

        data = indicators.to_dict()

        assert data["trust_score"] == 75.0
        assert data["trust_level"] == "medium"
        assert data["trust_badges"] == [TrustBadge.SILVER]
        assert data["validation_timestamp"] == "2025-11-18T10:00:00Z"

    def test_trust_indicators_deserialization(self):
        """Test trust indicators deserialization."""
        data = {
            "trust_score": 80.0,
            "trust_level": "high",
            "trust_badges": ["GOLD", "SILVER"],
            "activity_score": 70.0,
            "validation_timestamp": "2025-11-18T10:00:00Z"
        }

        indicators = TrustIndicators.from_dict(data)

        assert indicators.trust_score == 80.0
        assert indicators.trust_level == TrustLevel.HIGH
        assert indicators.trust_badges == ["GOLD", "SILVER"]
        assert indicators.activity_score == 70.0


class TestTrustValidationRequest:
    """Test TrustValidationRequest data model."""

    def test_request_creation(self):
        """Test creating a valid trust validation request."""
        request = TrustValidationRequest(
            submission_id="abc123",
            subreddit="productivity",
            upvotes=150,
            comments_count=25,
            created_utc=1700000000,
            text="I need help with task management..."
        )

        assert request.submission_id == "abc123"
        assert request.subreddit == "productivity"
        assert request.upvotes == 150
        assert request.comments_count == 25
        assert request.created_utc == 1700000000

    def test_request_validation(self):
        """Test request validation."""
        # Valid request
        request = TrustValidationRequest(
            submission_id="abc123",
            subreddit="test",
            upvotes=10,
            comments_count=5,
            created_utc="1700000000"
        )
        assert request.submission_id == "abc123"

        # Missing required fields
        with pytest.raises(ValueError, match="submission_id is required"):
            TrustValidationRequest(
                submission_id="",
                subreddit="test",
                upvotes=10,
                comments_count=5,
                created_utc="1700000000"
            )

        # Negative values
        with pytest.raises(ValueError, match="upvotes cannot be negative"):
            TrustValidationRequest(
                submission_id="abc123",
                subreddit="test",
                upvotes=-10,
                comments_count=5,
                created_utc="1700000000"
            )

    def test_request_serialization(self):
        """Test request serialization."""
        ai_analysis = {
            "problem_description": "Users need better task management",
            "app_concept": "Smart task manager with AI",
            "final_score": 75.0
        }

        request = TrustValidationRequest(
            submission_id="abc123",
            subreddit="productivity",
            upvotes=150,
            comments_count=25,
            created_utc=1700000000,
            ai_analysis=ai_analysis,
            activity_threshold=30.0
        )

        data = request.to_dict()
        assert data["submission_id"] == "abc123"
        assert data["ai_analysis"] == ai_analysis
        assert data["activity_threshold"] == 30.0


class TestTrustScoreWeights:
    """Test TrustScoreWeights configuration."""

    def test_default_weights(self):
        """Test default weight configuration."""
        weights = TrustScoreWeights()

        total = sum([
            weights.subreddit_activity,
            weights.post_engagement,
            weights.trend_velocity,
            weights.problem_validity,
            weights.discussion_quality,
            weights.ai_confidence
        ])

        assert abs(total - 1.0) < 0.01  # Allow floating point tolerance

    def test_weight_validation(self):
        """Test weight validation."""
        # Valid weights
        weights = TrustScoreWeights(
            subreddit_activity=0.30,
            post_engagement=0.20,
            trend_velocity=0.15,
            problem_validity=0.15,
            discussion_quality=0.15,
            ai_confidence=0.05
        )
        assert weights.subreddit_activity == 0.30

        # Invalid total weight
        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            TrustScoreWeights(
                subreddit_activity=0.5,
                post_engagement=0.5,  # This makes total > 1.0
                trend_velocity=0.15,
                problem_validity=0.15,
                discussion_quality=0.15,
                ai_confidence=0.10
            )

        # Invalid individual weight
        with pytest.raises(ValueError, match="Each weight must be between"):
            TrustScoreWeights(
                subreddit_activity=0.10,  # Too low
                post_engagement=0.20,
                trend_velocity=0.15,
                problem_validity=0.15,
                discussion_quality=0.15,
                ai_confidence=0.10
            )

    def test_weight_serialization(self):
        """Test weight serialization."""
        weights = TrustScoreWeights(
            subreddit_activity=0.25,
            ai_confidence=0.10
        )

        data = weights.to_dict()
        assert data["subreddit_activity"] == 0.25
        assert data["ai_confidence"] == 0.10

    def test_weight_deserialization(self):
        """Test weight deserialization."""
        data = {
            "subreddit_activity": 0.30,
            "ai_confidence": 0.15
        }

        weights = TrustScoreWeights.from_dict(data)
        assert weights.subreddit_activity == 0.30
        assert weights.ai_confidence == 0.15
        # Other weights should use defaults
        assert weights.post_engagement == 0.20


class MockTrustRepository(TrustRepositoryInterface):
    """Mock repository for testing."""

    def __init__(self):
        self.data = {}
        self.save_calls = []
        self.get_calls = []

    def get_trust_indicators(self, submission_id: str) -> TrustIndicators | None:
        self.get_calls.append(submission_id)
        return self.data.get(submission_id)

    def save_trust_indicators(self, submission_id: str, indicators: TrustIndicators) -> bool:
        self.save_calls.append((submission_id, indicators))
        self.data[submission_id] = indicators
        return True

    def update_trust_indicators(self, submission_id: str, updates: dict) -> bool:
        if submission_id in self.data:
            indicators = self.data[submission_id]
            for key, value in updates.items():
                if hasattr(indicators, key):
                    setattr(indicators, key, value)
            return True
        return False

    def get_batch_trust_indicators(self, submission_ids: list) -> dict:
        return {sid: self.data.get(sid) for sid in submission_ids if sid in self.data}

    def delete_trust_indicators(self, submission_id: str) -> bool:
        if submission_id in self.data:
            del self.data[submission_id]
            return True
        return False

    def exists_trust_indicators(self, submission_id: str) -> bool:
        return submission_id in self.data


class TestTrustRepository:
    """Test trust repository implementation."""

    def test_repository_interface(self):
        """Test that repository implements interface correctly."""
        repo = MockTrustRepository()

        # Test save and get
        indicators = TrustIndicators(trust_score=80.0)
        assert repo.save_trust_indicators("test123", indicators) is True
        assert repo.save_calls == [("test123", indicators)]

        retrieved = repo.get_trust_indicators("test123")
        assert retrieved is not None
        assert retrieved.trust_score == 80.0
        assert repo.get_calls == ["test123"]

        # Test exists
        assert repo.exists_trust_indicators("test123") is True
        assert repo.exists_trust_indicators("nonexistent") is False

        # Test update
        updates = {"trust_score": 90.0}
        assert repo.update_trust_indicators("test123", updates) is True
        updated = repo.get_trust_indicators("test123")
        assert updated.trust_score == 90.0

        # Test batch get
        batch_result = repo.get_batch_trust_indicators(["test123", "nonexistent"])
        assert "test123" in batch_result
        assert "nonexistent" not in batch_result

        # Test delete
        assert repo.delete_trust_indicators("test123") is True
        assert repo.exists_trust_indicators("test123") is False


class TestTrustValidationService:
    """Test trust validation service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.repository = MockTrustRepository()
        self.service = TrustValidationService(self.repository)

    def test_service_initialization(self):
        """Test service initialization."""
        service = TrustValidationService(self.repository)
        assert service.repository == self.repository
        assert service.activity_threshold == 25.0
        assert len(service.validation_history) == 0

    def test_service_custom_configuration(self):
        """Test service with custom configuration."""
        weights = TrustScoreWeights(subreddit_activity=0.30)
        badge_config = TrustBadgeConfig()
        service = TrustValidationService(
            repository=self.repository,
            weights=weights,
            badge_config=badge_config,
            activity_threshold=30.0
        )

        assert service.activity_threshold == 30.0
        assert service.weights.subreddit_activity == 0.30

    @patch('core.trust.validation.calculate_activity_score')
    @patch('core.trust.validation.praw.Reddit')
    def test_validate_opportunity_trust_success(self, mock_reddit, mock_calculate_activity):
        """Test successful trust validation."""
        # Mock Reddit API
        mock_calculate_activity.return_value = 40.0  # Will be normalized to 80.0

        # Create test request
        request = TrustValidationRequest(
            submission_id="test123",
            subreddit="productivity",
            upvotes=100,
            comments_count=20,
            created_utc=time.time() - 3600,  # 1 hour ago
            text="I need help with productivity and task management",
            title="Productivity tools recommendation",
            ai_analysis={
                "problem_description": "Users struggle with productivity and task management",
                "app_concept": "AI-powered productivity assistant with smart scheduling",
                "core_functions": ["Task scheduling", "Priority management", "Progress tracking"],
                "final_score": 75.0
            }
        )

        # Validate trust
        result = self.service.validate_opportunity_trust(request)

        # Verify result
        assert result.success is True
        assert result.source_submission_id == "test123"
        assert result.processing_time_ms is not None and result.processing_time_ms > 0
        assert result.validation_version == "1.0"

        # Verify indicators
        indicators = result.indicators
        assert indicators.trust_score >= 0.0
        assert indicators.trust_level in TrustLevel
        assert isinstance(indicators.trust_badges, list)
        assert indicators.confidence_score >= 0.0

        # Verify validation was saved
        assert "test123" in self.repository.data

        # Verify history
        assert len(self.service.validation_history) == 1
        assert self.service.validation_history[0] == result

    def test_validate_opportunity_trust_with_ai_analysis_missing(self):
        """Test trust validation without AI analysis."""
        request = TrustValidationRequest(
            submission_id="test123",
            subreddit="productivity",
            upvotes=10,
            comments_count=5,
            created_utc=time.time() - 86400,  # 1 day ago
            text="Simple text without AI analysis"
            # No ai_analysis provided
        )

        result = self.service.validate_opportunity_trust(request)

        assert result.success is True
        indicators = result.indicators
        # Should have low scores due to missing AI analysis
        assert indicators.problem_validity_score == 0.0
        assert indicators.quality_constraints_met is False

    def test_validate_opportunity_trust_error_handling(self):
        """Test trust validation error handling."""
        # Create invalid request that will cause errors
        request = TrustValidationRequest(
            submission_id="test123",
            subreddit="invalid_subreddit_that_will_fail",
            upvotes=10,
            comments_count=5,
            created_utc="invalid_timestamp",
            text="Test text"
        )

        result = self.service.validate_opportunity_trust(request)

        # Should still succeed but with minimal trust indicators
        assert result.success is True
        indicators = result.indicators
        assert indicators.trust_score <= 10.0  # Minimal score on error
        assert indicators.trust_level == TrustLevel.LOW
        assert "basic_validation" in indicators.trust_badges

    def test_validate_batch_opportunities(self):
        """Test batch trust validation."""
        requests = [
            TrustValidationRequest(
                submission_id=f"test{i}",
                subreddit="productivity",
                upvotes=50 + i * 10,
                comments_count=5 + i * 2,
                created_utc=time.time() - 3600 * i,
                text=f"Test text {i}",
                ai_analysis={
                    "problem_description": f"Problem {i}",
                    "app_concept": f"Concept {i}",
                    "final_score": 60.0 + i * 5
                }
            )
            for i in range(3)
        ]

        results = self.service.validate_batch_opportunities_trust(requests)

        assert len(results) == 3
        assert all(result.success for result in results)
        assert all(result.source_submission_id.startswith("test") for result in results)

    def test_save_and_get_trust_indicators(self):
        """Test saving and retrieving trust indicators."""
        indicators = TrustIndicators(
            trust_score=85.0,
            trust_level=TrustLevel.HIGH,
            trust_badges=[TrustBadge.GOLD]
        )

        # Save indicators
        assert self.service.save_trust_indicators("test123", indicators) is True

        # Retrieve indicators
        retrieved = self.service.get_trust_indicators("test123")
        assert retrieved is not None
        assert retrieved.trust_score == 85.0
        assert retrieved.trust_level == TrustLevel.HIGH

    def test_get_nonexistent_trust_indicators(self):
        """Test retrieving non-existent trust indicators."""
        result = self.service.get_trust_indicators("nonexistent")
        assert result is None

    def test_get_service_stats(self):
        """Test getting service statistics."""
        # Initially should have no validations
        stats = self.service.get_service_stats()
        assert stats["total_validations"] == 0
        assert stats["successful_validations"] == 0
        assert stats["success_rate"] == 0.0

        # Perform validation
        request = TrustValidationRequest(
            submission_id="test123",
            subreddit="test",
            upvotes=10,
            comments_count=5,
            created_utc=time.time()
        )

        result = self.service.validate_opportunity_trust(request)

        # Check updated stats
        stats = self.service.get_service_stats()
        assert stats["total_validations"] == 1
        assert stats["successful_validations"] == 1
        assert stats["success_rate"] == 1.0
        assert stats["average_processing_time_ms"] > 0

    def test_get_validation_history(self):
        """Test getting validation history."""
        # Initially empty
        history = self.service.get_validation_history()
        assert len(history) == 0

        # Perform validation
        request = TrustValidationRequest(
            submission_id="test123",
            subreddit="test",
            upvotes=10,
            comments_count=5,
            created_utc=time.time()
        )

        self.service.validate_opportunity_trust(request)

        # Should have one entry in history
        history = self.service.get_validation_history()
        assert len(history) == 1
        assert history[0].source_submission_id == "test123"

        # Test limit
        self.service.validate_opportunity_trust(request)
        history = self.service.get_validation_history(limit=1)
        assert len(history) == 1

    def test_clear_validation_history(self):
        """Test clearing validation history."""
        # Perform validation
        request = TrustValidationRequest(
            submission_id="test123",
            subreddit="test",
            upvotes=10,
            comments_count=5,
            created_utc=time.time()
        )

        self.service.validate_opportunity_trust(request)
        assert len(self.service.validation_history) == 1

        # Clear history
        self.service.clear_validation_history()
        assert len(self.service.validation_history) == 0


class TestTrustValidationIntegration:
    """Integration tests for trust validation system."""

    def test_backward_compatibility_layer(self):
        """Test that old trust_layer.py still works."""
        # This test ensures the compatibility layer works
        with patch('core.trust_layer.create_client') as mock_create_client:
            mock_client = Mock()
            mock_create_client.return_value = mock_client

            # Import should work
            from core.trust_layer import TrustLayerValidator, TrustIndicators as OldTrustIndicators

            # Create validator
            validator = TrustLayerValidator(activity_threshold=30.0)
            assert validator.activity_threshold == 30.0

            # Test validation (should work through compatibility layer)
            submission_data = {
                'submission_id': 'test123',
                'subreddit': 'productivity',
                'upvotes': 100,
                'comments_count': 20,
                'created_utc': 1700000000,
                'text': 'Test text'
            }

            ai_analysis = {
                'problem_description': 'Test problem',
                'app_concept': 'Test concept',
                'final_score': 75.0
            }

            indicators = validator.validate_opportunity_trust(submission_data, ai_analysis)
            assert isinstance(indicators, OldTrustIndicators)
            assert hasattr(indicators, 'overall_trust_score')
            assert hasattr(indicators, 'trust_level')

    def test_trust_system_compatibility_validation(self):
        """Test trust system compatibility validation function."""
        compatibility = validate_trust_compatibility()

        assert compatibility["compatible"] is True
        assert "version" in compatibility
        assert "tests_passed" in compatibility
        assert len(compatibility["tests_passed"]) > 0
        assert len(compatibility["errors"]) == 0

    def test_factory_functions(self):
        """Test trust service factory functions."""
        mock_client = Mock()

        service = create_trust_service(mock_client)
        assert isinstance(service, TrustValidationService)

        # Test with custom configuration
        custom_weights = TrustScoreWeights(subreddit_activity=0.30)
        service = create_trust_service(
            mock_client,
            weights=custom_weights,
            activity_threshold=35.0
        )
        assert service.weights.subreddit_activity == 0.30
        assert service.activity_threshold == 35.0


class TestErrorHandling:
    """Test error handling and edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.repository = MockTrustRepository()
        self.service = TrustValidationService(self.repository)

    def test_repository_error_handling(self):
        """Test handling of repository errors."""
        # Create repository that raises errors
        class ErrorRepository(TrustRepositoryInterface):
            def get_trust_indicators(self, submission_id: str):
                raise Exception("Database error")

            def save_trust_indicators(self, submission_id: str, indicators):
                raise Exception("Save failed")

            def update_trust_indicators(self, submission_id: str, updates):
                raise Exception("Update failed")

            def get_batch_trust_indicators(self, submission_ids: list):
                raise Exception("Batch get failed")

            def delete_trust_indicators(self, submission_id: str):
                raise Exception("Delete failed")

            def exists_trust_indicators(self, submission_id: str):
                raise Exception("Exists check failed")

        error_repo = ErrorRepository()
        service = TrustValidationService(error_repo)

        # Test that service handles repository errors gracefully
        request = TrustValidationRequest(
            submission_id="test123",
            subreddit="test",
            upvotes=10,
            comments_count=5,
            created_utc=time.time()
        )

        result = service.validate_opportunity_trust(request)
        assert result.success is True  # Should still succeed with minimal indicators

    def test_invalid_request_data(self):
        """Test handling of invalid request data."""
        # Test with negative values (should be handled gracefully)
        request = TrustValidationRequest(
            submission_id="test123",
            subreddit="test",
            upvotes=-10,  # Invalid, but constructor should handle it
            comments_count=0,
            created_utc=time.time()
        )

        # This should have been caught by request validation
        with pytest.raises(ValueError):
            TrustValidationRequest(
                submission_id="test123",
                subreddit="test",
                upvotes=-10,
                comments_count=0,
                created_utc=time.time()
            )

    def test_extreme_values(self):
        """Test handling of extreme values."""
        request = TrustValidationRequest(
            submission_id="test123",
            subreddit="test",
            upvotes=1000000,  # Very high upvotes
            comments_count=100000,  # Very high comments
            created_utc=time.time() - 31536000,  # Very old post (1 year)
            text="A" * 10000,  # Very long text
            ai_analysis={
                "problem_description": "B" * 1000,
                "app_concept": "C" * 1000,
                "final_score": 150.0  # Invalid high score
            }
        )

        result = self.service.validate_opportunity_trust(request)
        assert result.success is True
        indicators = result.indicators

        # Should handle extreme values gracefully
        assert 0.0 <= indicators.trust_score <= 100.0
        assert 0.0 <= indicators.post_engagement_score <= 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])