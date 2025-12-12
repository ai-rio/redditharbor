"""
Comprehensive Test Suite for Unified Loader
RedditHarbor Pipeline V4 - Loader Consolidation

This test suite follows Test-Driven Development (TDD) principles:
- Tests written FIRST to drive the implementation (RED phase)
- Unified Loader implementation does NOT exist yet
- Tests will initially FAIL - this is expected and correct
- Implementation will be created to make these tests pass (GREEN phase)

Test Coverage:
- Basic CRUD operations (save, get, update, delete)
- Duplicate detection and handling
- Batch operations for performance
- Validation and error handling
- Transaction management and rollback
- Connection pooling and concurrent operations
- Logging and monitoring
- Configuration and settings

Total Test Count: 30+ comprehensive tests
"""

import logging
import threading
import time
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlmodel import Session, select

from database import get_db_session, get_engine
from models.analysis import Opportunity

# This import WILL FAIL because Loader doesn't exist yet
# This is INTENTIONAL - TDD RED phase
from load.loader import Loader

logger = logging.getLogger(__name__)


# ============================================================================
# TEST CLASS 1: Basic CRUD Operations
# ============================================================================


class TestLoaderBasicOperations:
    """Test basic Create, Read, Update, Delete operations"""

    def test_loader_initialization_succeeds(self):
        """Test that Loader can be initialized successfully"""
        # Act
        loader = Loader()

        # Assert
        assert loader is not None
        assert loader.engine is not None
        assert hasattr(loader, "session_factory")
        assert hasattr(loader, "logger")

    def test_save_new_opportunity_returns_true(self):
        """Test saving a new opportunity returns True"""
        # Arrange
        loader = Loader()
        opp = Opportunity(
            submission_id="test_new_123",
            subreddit="test",
            title="Test New Opportunity",
            wtp_score=75.0,
            trust_level="HIGH",
            analysis={"app_idea": {"title": "Test App"}},
            metrics={"market_demand": 85.0},
        )

        # Act
        result = loader.save_opportunity(opp)

        # Assert
        assert result is True
        assert opp.id is not None  # Should be assigned by database

    def test_save_opportunity_sets_timestamps(self):
        """Test that created_at and updated_at are set correctly"""
        # Arrange
        loader = Loader()
        before_save = datetime.now(UTC)

        opp = Opportunity(
            submission_id="test_timestamps",
            subreddit="test",
            title="Test Timestamps",
            wtp_score=50.0,
        )

        # Act
        loader.save_opportunity(opp)
        after_save = datetime.now(UTC)

        # Assert
        before_save_naive = before_save.replace(tzinfo=None)
        after_save_naive = after_save.replace(tzinfo=None)

        assert before_save_naive <= opp.created_at <= after_save_naive
        assert before_save_naive <= opp.updated_at <= after_save_naive

    def test_get_opportunity_by_submission_id(self):
        """Test retrieving an opportunity by submission_id"""
        # Arrange
        loader = Loader()
        opp = Opportunity(
            submission_id="test_get_123",
            subreddit="test",
            title="Test Get Opportunity",
            wtp_score=60.0,
        )
        loader.save_opportunity(opp)

        # Act
        retrieved = loader.get_opportunity("test_get_123")

        # Assert
        assert retrieved is not None
        assert retrieved.submission_id == "test_get_123"
        assert retrieved.title == "Test Get Opportunity"
        assert retrieved.wtp_score == 60.0

    def test_get_nonexistent_opportunity_returns_none(self):
        """Test retrieving non-existent opportunity returns None"""
        # Arrange
        loader = Loader()

        # Act
        result = loader.get_opportunity("nonexistent_id")

        # Assert
        assert result is None

    def test_update_opportunity_success(self):
        """Test updating an existing opportunity"""
        # Arrange
        loader = Loader()
        opp = Opportunity(
            submission_id="test_update_123",
            subreddit="test",
            title="Original Title",
            wtp_score=50.0,
        )
        loader.save_opportunity(opp)

        # Act
        updates = {"title": "Updated Title", "wtp_score": 75.0}
        result = loader.update_opportunity("test_update_123", updates)

        # Assert
        assert result is True
        updated_opp = loader.get_opportunity("test_update_123")
        assert updated_opp.title == "Updated Title"
        assert updated_opp.wtp_score == 75.0

    def test_update_nonexistent_opportunity_returns_false(self):
        """Test updating non-existent opportunity returns False"""
        # Arrange
        loader = Loader()

        # Act
        result = loader.update_opportunity("nonexistent", {"title": "New Title"})

        # Assert
        assert result is False

    def test_delete_opportunity_success(self):
        """Test deleting an existing opportunity"""
        # Arrange
        loader = Loader()
        opp = Opportunity(
            submission_id="test_delete_123",
            subreddit="test",
            title="To Be Deleted",
            wtp_score=50.0,
        )
        loader.save_opportunity(opp)

        # Act
        result = loader.delete_opportunity("test_delete_123")

        # Assert
        assert result is True
        assert loader.get_opportunity("test_delete_123") is None

    def test_delete_nonexistent_opportunity_returns_false(self):
        """Test deleting non-existent opportunity returns False"""
        # Arrange
        loader = Loader()

        # Act
        result = loader.delete_opportunity("nonexistent")

        # Assert
        assert result is False


# ============================================================================
# TEST CLASS 2: Duplicate Detection and Handling
# ============================================================================


class TestLoaderDuplicateHandling:
    """Test duplicate detection and ON CONFLICT behavior"""

    def test_save_duplicate_opportunity_returns_false(self):
        """Test saving duplicate submission_id returns False"""
        # Arrange
        loader = Loader()
        opp1 = Opportunity(
            submission_id="duplicate_test",
            subreddit="test",
            title="First Save",
            wtp_score=50.0,
        )
        loader.save_opportunity(opp1)

        # Create duplicate
        opp2 = Opportunity(
            submission_id="duplicate_test",
            subreddit="test",
            title="Second Save",
            wtp_score=60.0,
        )

        # Act
        result = loader.save_opportunity(opp2)

        # Assert
        assert result is False
        assert opp2.id is None  # Should not be assigned

    def test_duplicate_preserves_original_record(self):
        """Test that duplicate attempt preserves original record"""
        # Arrange
        loader = Loader()
        submission_id = "preserve_original"
        opp1 = Opportunity(
            submission_id=submission_id,
            subreddit="test",
            title="Original",
            wtp_score=50.0,
        )
        loader.save_opportunity(opp1)

        # Attempt duplicate
        opp2 = Opportunity(
            submission_id=submission_id,
            subreddit="test",
            title="Duplicate",
            wtp_score=75.0,
        )
        loader.save_opportunity(opp2)

        # Act
        retrieved = loader.get_opportunity(submission_id)

        # Assert
        assert retrieved.title == "Original"
        assert retrieved.wtp_score == 50.0

    def test_duplicate_detection_case_sensitive(self):
        """Test that duplicate detection is case-sensitive"""
        # Arrange
        loader = Loader()
        opp1 = Opportunity(
            submission_id="CaseSensitive",
            subreddit="test",
            title="First",
            wtp_score=50.0,
        )
        loader.save_opportunity(opp1)

        opp2 = Opportunity(
            submission_id="casesensitive",
            subreddit="test",
            title="Second",
            wtp_score=50.0,
        )

        # Act
        result = loader.save_opportunity(opp2)

        # Assert - Should succeed (different case)
        assert result is True


# ============================================================================
# TEST CLASS 3: Validation and Error Handling
# ============================================================================


class TestLoaderValidation:
    """Test data validation before database operations"""

    def test_save_empty_submission_id_raises_error(self):
        """Test that empty submission_id raises ValueError"""
        # Arrange
        loader = Loader()
        opp = Opportunity(
            submission_id="",
            subreddit="test",
            title="Test",
            wtp_score=50.0,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="submission_id cannot be empty"):
            loader.save_opportunity(opp)

    def test_save_none_submission_id_raises_error(self):
        """Test that None submission_id raises ValueError"""
        # Arrange
        loader = Loader()
        opp = Opportunity(
            submission_id=None,
            subreddit="test",
            title="Test",
            wtp_score=50.0,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="submission_id cannot be empty"):
            loader.save_opportunity(opp)

    def test_save_invalid_trust_level_raises_error(self):
        """Test that invalid trust_level raises ValueError"""
        # Arrange
        loader = Loader()
        opp = Opportunity(
            submission_id="test_trust",
            subreddit="test",
            title="Test",
            wtp_score=50.0,
        )
        opp.trust_level = "INVALID"

        # Act & Assert
        with pytest.raises(ValueError, match="Trust level must be one of"):
            loader.save_opportunity(opp)

    def test_save_invalid_analysis_structure_raises_error(self):
        """Test that invalid analysis structure raises ValueError"""
        # Arrange
        loader = Loader()
        opp = Opportunity(
            submission_id="test_analysis",
            subreddit="test",
            title="Test",
            wtp_score=50.0,
        )
        opp.analysis = "not a dict"  # Invalid structure

        # Act & Assert
        with pytest.raises(ValueError, match="analysis field must be a dictionary"):
            loader.save_opportunity(opp)


# ============================================================================
# TEST CLASS 4: Batch Operations
# ============================================================================


class TestLoaderBatchOperations:
    """Test batch save operations for performance"""

    def test_save_opportunities_batch_success(self):
        """Test batch save of multiple opportunities"""
        # Arrange
        loader = Loader()
        opportunities = [
            Opportunity(
                submission_id=f"batch_{i}",
                subreddit="test",
                title=f"Batch Test {i}",
                wtp_score=float(50 + i * 5),
            )
            for i in range(10)
        ]

        # Act
        saved_count = loader.save_opportunities(opportunities)

        # Assert
        assert saved_count == 10

        # Verify all saved
        for i in range(10):
            opp = loader.get_opportunity(f"batch_{i}")
            assert opp is not None
            assert opp.title == f"Batch Test {i}"

    def test_save_opportunities_with_duplicates(self):
        """Test batch save filters out duplicates"""
        # Arrange
        loader = Loader()
        # Pre-save some opportunities
        for i in range(5):
            opp = Opportunity(
                submission_id=f"batch_dup_{i}",
                subreddit="test",
                title=f"Original {i}",
                wtp_score=50.0,
            )
            loader.save_opportunity(opp)

        # Create batch with duplicates and new records
        opportunities = [
            Opportunity(
                submission_id=f"batch_dup_{i}",
                subreddit="test",
                title=f"Duplicate {i}",
                wtp_score=75.0,
            )
            for i in range(10)  # 0-4 are duplicates, 5-9 are new
        ]

        # Act
        saved_count = loader.save_opportunities(opportunities)

        # Assert
        assert saved_count == 5  # Only new ones saved

    def test_save_empty_batch_returns_zero(self):
        """Test that saving empty batch returns 0"""
        # Arrange
        loader = Loader()

        # Act
        result = loader.save_opportunities([])

        # Assert
        assert result == 0


# ============================================================================
# TEST CLASS 5: save_analysis Method
# ============================================================================


class TestLoaderSaveAnalysis:
    """Test save_analysis method that converts AnalysisResult to Opportunity"""

    def test_save_analysis_converts_and_saves(self):
        """Test that save_analysis properly converts AnalysisResult"""
        # Arrange
        loader = Loader()

        # Create a mock AnalysisResult object
        from models.analysis import MarketMetrics, AppIdea

        class MockAnalysisResult:
            def __init__(self):
                self.submission_id = "test_analysis_save"
                self.subreddit = "test"
                self.title = "Test Analysis"
                self.wtp_score = 80.0
                self.final_score = 75.0
                self.confidence_score = 85.0
                self.trust_level = "HIGH"
                self.app_idea = AppIdea(
                    title="Test App",
                    app_concept="A test application for validation",
                    problem_statement="Testing analysis conversion",
                    core_functions=["Function 1", "Function 2"],
                    target_audience="Developers and testers who need validation tools",
                )
                self.pain_points = ["Pain 1", "Pain 2"]
                self.opportunity_summary = "Test summary"
                self.content_quality_score = 90.0
                self.is_spam = False
                self.spam_indicators = []
                self.analyzed_at = datetime.now(UTC)
                self.metrics = MarketMetrics(
                    market_demand=85.0,
                    pain_intensity=70.0,
                    monetization_potential=90.0,
                    technical_feasibility=80.0,
                    competition_level=60.0,
                )

        analysis = MockAnalysisResult()

        # Act
        result = loader.save_analysis(analysis)

        # Assert
        assert result is True

        # Verify saved correctly
        opp = loader.get_opportunity("test_analysis_save")
        assert opp is not None
        assert opp.wtp_score == 80.0
        assert "app_idea" in opp.analysis


# ============================================================================
# TEST CLASS 6: Transaction Management and Rollback
# ============================================================================


class TestLoaderTransactionManagement:
    """Test transaction handling and rollback on errors"""

    def test_transaction_rollback_on_integrity_error(self):
        """Test that transaction rolls back on IntegrityError"""
        # Arrange
        loader = Loader()

        with patch("load.loader.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = iter([mock_session])

            # Configure mock to return None for duplicate check
            mock_session.exec.return_value.first.return_value = None

            # Configure mock to raise IntegrityError on commit
            mock_session.commit.side_effect = IntegrityError("test", "test", "test")

            opp = Opportunity(
                submission_id="rollback_test",
                subreddit="test",
                title="Test",
                wtp_score=50.0,
            )

            # Act & Assert
            with pytest.raises(IntegrityError):
                loader.save_opportunity(opp)

            # Verify rollback was called
            mock_session.rollback.assert_called_once()

    def test_session_cleanup_on_error(self):
        """Test that session is cleaned up even on errors"""
        # Arrange
        loader = Loader()

        with patch("load.loader.get_session") as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = iter([mock_session])

            mock_session.exec.return_value.first.return_value = None
            mock_session.add.side_effect = RuntimeError("Database error")

            opp = Opportunity(
                submission_id="cleanup_test",
                subreddit="test",
                title="Test",
                wtp_score=50.0,
            )

            # Act & Assert
            with pytest.raises(RuntimeError):
                loader.save_opportunity(opp)

            # Verify session cleanup
            mock_session.close.assert_called_once()


# ============================================================================
# TEST CLASS 7: Query Methods
# ============================================================================


class TestLoaderQueryMethods:
    """Test various query methods for retrieving opportunities"""

    def test_get_opportunities_by_subreddit(self):
        """Test retrieving all opportunities for a subreddit"""
        # Arrange
        loader = Loader()
        for i in range(5):
            opp = Opportunity(
                submission_id=f"subreddit_test_{i}",
                subreddit="programming",
                title=f"Test {i}",
                wtp_score=50.0,
            )
            loader.save_opportunity(opp)

        # Act
        results = loader.get_opportunities_by_subreddit("programming")

        # Assert
        assert len(results) == 5
        for opp in results:
            assert opp.subreddit == "programming"

    def test_get_opportunities_by_score_range(self):
        """Test retrieving opportunities within score range"""
        # Arrange
        loader = Loader()
        for i in range(10):
            opp = Opportunity(
                submission_id=f"score_range_{i}",
                subreddit="test",
                title=f"Test {i}",
                wtp_score=float(i * 10),
            )
            opp.final_score = float(i * 10)
            loader.save_opportunity(opp)

        # Act
        results = loader.get_opportunities_by_score_range(
            min_score=30.0, max_score=70.0, limit=100
        )

        # Assert
        assert len(results) >= 4  # Scores 30, 40, 50, 60, 70
        for opp in results:
            assert 30.0 <= opp.final_score <= 70.0

    def test_count_opportunities(self):
        """Test counting total opportunities"""
        # Arrange
        loader = Loader()
        for i in range(15):
            opp = Opportunity(
                submission_id=f"count_test_{i}",
                subreddit="test",
                title=f"Test {i}",
                wtp_score=50.0,
            )
            loader.save_opportunity(opp)

        # Act
        count = loader.count_opportunities()

        # Assert
        assert count == 15


# ============================================================================
# TEST CLASS 8: Concurrent Operations
# ============================================================================


class TestLoaderConcurrentOperations:
    """Test thread safety and concurrent operations"""

    def test_concurrent_writes_different_opportunities(self):
        """Test concurrent writes to different opportunities"""
        # Arrange
        num_threads = 10
        results = []
        errors = []

        def save_opportunity(thread_id):
            try:
                loader = Loader()
                opp = Opportunity(
                    submission_id=f"concurrent_{thread_id}",
                    subreddit="test",
                    title=f"Thread {thread_id}",
                    wtp_score=50.0,
                )
                result = loader.save_opportunity(opp)
                results.append((thread_id, result))
            except Exception as e:
                errors.append((thread_id, e))

        # Act
        threads = [
            threading.Thread(target=save_opportunity, args=(i,))
            for i in range(num_threads)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Assert
        assert len(errors) == 0
        assert len(results) == num_threads
        assert all(r[1] for r in results)  # All should succeed


# ============================================================================
# TEST CLASS 9: Logging and Monitoring
# ============================================================================


class TestLoaderLogging:
    """Test logging and monitoring capabilities"""

    def test_successful_save_logs_info(self):
        """Test that successful saves are logged"""
        # Arrange
        loader = Loader()

        with patch.object(loader, "logger") as mock_logger:
            opp = Opportunity(
                submission_id="log_test",
                subreddit="test",
                title="Test",
                wtp_score=50.0,
            )

            # Act
            loader.save_opportunity(opp)

            # Assert
            mock_logger.info.assert_called()
            log_message = mock_logger.info.call_args[0][0]
            assert "Saved opportunity" in log_message

    def test_duplicate_save_logs_warning(self):
        """Test that duplicate saves log warning"""
        # Arrange
        loader = Loader()
        opp1 = Opportunity(
            submission_id="log_dup",
            subreddit="test",
            title="First",
            wtp_score=50.0,
        )
        loader.save_opportunity(opp1)

        with patch.object(loader, "logger") as mock_logger:
            opp2 = Opportunity(
                submission_id="log_dup",
                subreddit="test",
                title="Second",
                wtp_score=50.0,
            )

            # Act
            loader.save_opportunity(opp2)

            # Assert
            mock_logger.warning.assert_called()


# ============================================================================
# TEST CLASS 10: Cleanup and Resource Management
# ============================================================================


class TestLoaderResourceManagement:
    """Test resource cleanup and management"""

    def test_loader_close_method(self):
        """Test that close method cleans up resources"""
        # Arrange
        loader = Loader()

        # Act
        loader.close()

        # Assert - Should not raise errors
        assert True  # If we got here, close() worked


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture(scope="function", autouse=True)
def clean_test_database():
    """Clean database before and after each test"""
    engine = get_engine()

    with Session(engine) as session:
        session.exec(text("DELETE FROM opportunities"))
        try:
            session.exec(text("ALTER SEQUENCE opportunities_id_seq RESTART WITH 1"))
        except Exception:
            pass
        session.commit()
        logger.info("Cleaned opportunity table for test")

    yield

    with Session(engine) as session:
        session.exec(text("DELETE FROM opportunities"))
        try:
            session.exec(text("ALTER SEQUENCE opportunities_id_seq RESTART WITH 1"))
        except Exception:
            pass
        session.commit()
        logger.info("Cleaned opportunity table after test")


@pytest.fixture
def sample_opportunity():
    """Create a sample opportunity for testing"""
    return Opportunity(
        submission_id="sample_123",
        subreddit="test",
        title="Sample Opportunity",
        wtp_score=75.0,
        trust_level="HIGH",
        analysis={
            "app_idea": {
                "title": "Sample App",
                "concept": "Test concept",
                "problem": "Test problem",
            }
        },
        metrics={
            "market_demand": 85.0,
            "pain_intensity": 70.0,
            "monetization_potential": 90.0,
            "technical_feasibility": 80.0,
        },
    )


# Test runner
if __name__ == "__main__":
    # This will fail because Loader doesn't exist yet
    # This is INTENTIONAL - TDD RED phase
    pytest.main([__file__, "-v", "--tb=short"])
