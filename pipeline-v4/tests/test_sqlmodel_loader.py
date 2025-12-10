"""
Test-Driven Development Tests for SQLModel Loader
RedditHarbor Pipeline V4 - Phase 2, Task 2.2

These tests are written following TDD methodology:
- Tests are written FIRST (RED phase)
- SQLModelLoader implementation does NOT exist yet
- All tests MUST fail initially
- Implementation will be in Task 2.3 (GREEN phase)

Test Count Target: Minimum 17 tests covering all requirements
"""

import pytest
import threading
import time
from datetime import datetime, UTC
from typing import List, Optional
from unittest.mock import Mock, patch, MagicMock

# SQLModel and database imports
from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.pool import QueuePool

# Project imports
from models.analysis import Opportunity, MarketMetrics, AppIdea
from database import get_db_session, get_engine, get_session

# This import WILL FAIL because SQLModelLoader doesn't exist yet
# This is INTENTIONAL - TDD RED phase
from load.sqlmodel_loader import SQLModelLoader


class TestSQLModelLoaderBasicFunctionality:
    """Test basic SQLModelLoader functionality"""

    def test_save_new_opportunity_returns_true(self):
        """Test saving a new opportunity returns True"""
        # Arrange
        loader = SQLModelLoader()
        opp = Opportunity(
            submission_id="test_123",
            subreddit="test",
            title="Test Opportunity",
            wtp_score=75.0,
            trust_level="HIGH",
            analysis={"app_idea": {"title": "Test App"}},
            metrics={"market_demand": 85.0}
        )

        # Act
        result = loader.save_opportunity(opp)

        # Assert
        assert result is True
        assert opp.id is not None  # Should be assigned by database

    def test_save_opportunity_without_id_raises_error(self):
        """Test that saving without submission_id raises validation error"""
        # Arrange
        loader = SQLModelLoader()
        opp = Opportunity(
            # Missing submission_id
            subreddit="test",
            title="Test",
            wtp_score=50.0
        )

        # Act & Assert
        with pytest.raises(ValueError, match="submission_id is required"):
            loader.save_opportunity(opp)

    def test_save_opportunity_with_invalid_trust_level_raises_error(self):
        """Test that invalid trust level raises validation error"""
        # Arrange
        loader = SQLModelLoader()
        opp = Opportunity(
            submission_id="test_456",
            subreddit="test",
            title="Test",
            wtp_score=50.0,
            trust_level="INVALID"  # Invalid trust level
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Trust level must be one of"):
            loader.save_opportunity(opp)

    def test_save_opportunity_calculates_final_score_automatically(self):
        """Test that final_score is calculated from metrics when not provided"""
        # Arrange
        loader = SQLModelLoader()
        opp = Opportunity(
            submission_id="test_789",
            subreddit="test",
            title="Test",
            wtp_score=50.0,
            metrics={
                "market_demand": 80.0,
                "pain_intensity": 70.0,
                "monetization_potential": 90.0,
                "technical_feasibility": 60.0
            }
        )

        # Act
        loader.save_opportunity(opp)

        # Assert - Final score should be weighted average
        expected_final = (80.0 * 0.3 + 70.0 * 0.25 + 90.0 * 0.25 + 60.0 * 0.2)
        assert opp.final_score == expected_final

    def test_save_opportunity_updates_timestamps(self):
        """Test that created_at and updated_at are set correctly"""
        # Arrange
        loader = SQLModelLoader()
        before_save = datetime.now(UTC)

        opp = Opportunity(
            submission_id="test_timestamps",
            subreddit="test",
            title="Test",
            wtp_score=50.0
        )

        # Act
        loader.save_opportunity(opp)
        after_save = datetime.now(UTC)

        # Assert
        assert before_save <= opp.created_at <= after_save
        assert before_save <= opp.updated_at <= after_save


class TestSQLModelLoaderDuplicateHandling:
    """Test duplicate detection and ON CONFLICT handling"""

    def test_save_duplicate_opportunity_returns_false(self):
        """Test saving same submission_id returns False (duplicate detection)"""
        # Arrange
        loader = SQLModelLoader()
        opp1 = Opportunity(
            submission_id="duplicate_test",
            subreddit="test",
            title="First Save",
            wtp_score=50.0
        )

        # Save first opportunity
        result1 = loader.save_opportunity(opp1)
        assert result1 is True

        # Try to save duplicate
        opp2 = Opportunity(
            submission_id="duplicate_test",  # Same ID
            subreddit="test",
            title="Second Save",
            wtp_score=60.0
        )

        # Act
        result2 = loader.save_opportunity(opp2)

        # Assert
        assert result2 is False
        assert opp2.id is None  # Should not be assigned

    def test_duplicate_detection_is_case_sensitive(self):
        """Test that duplicate detection is case sensitive for submission_id"""
        # Arrange
        loader = SQLModelLoader()
        opp1 = Opportunity(
            submission_id="CaseSensitive",
            subreddit="test",
            title="First",
            wtp_score=50.0
        )
        loader.save_opportunity(opp1)

        opp2 = Opportunity(
            submission_id="casesensitive",  # Different case
            subreddit="test",
            title="Second",
            wtp_score=50.0
        )

        # Act
        result = loader.save_opportunity(opp2)

        # Assert - Should succeed (different case)
        assert result is True

    def test_only_one_record_exists_after_duplicate_attempt(self):
        """Test that only one record exists after duplicate save attempt"""
        # Arrange
        loader = SQLModelLoader()
        submission_id = "single_record_test"

        # Save first
        opp1 = Opportunity(
            submission_id=submission_id,
            subreddit="test",
            title="First",
            wtp_score=50.0
        )
        loader.save_opportunity(opp1)

        # Attempt duplicate
        opp2 = Opportunity(
            submission_id=submission_id,
            subreddit="test",
            title="Second",
            wtp_score=60.0
        )
        loader.save_opportunity(opp2)

        # Act - Verify only one record exists
        with get_db_session() as session:
            statement = select(Opportunity).where(
                Opportunity.submission_id == submission_id
            )
            results = session.exec(statement).all()

        # Assert
        assert len(results) == 1
        assert results[0].title == "First"  # Original record preserved

    def test_duplicate_different_subreddit_allowed(self):
        """Test that same submission_id in different subreddit is still duplicate"""
        # Arrange
        loader = SQLModelLoader()
        opp1 = Opportunity(
            submission_id="cross_subreddit",
            subreddit="programming",
            title="In Programming",
            wtp_score=50.0
        )
        loader.save_opportunity(opp1)

        opp2 = Opportunity(
            submission_id="cross_subreddit",  # Same ID
            subreddit="productivity",  # Different subreddit
            title="In Productivity",
            wtp_score=50.0
        )

        # Act
        result = loader.save_opportunity(opp2)

        # Assert - Still a duplicate (same submission_id)
        assert result is False

    def test_null_submission_id_not_allowed(self):
        """Test that null/empty submission_id raises error"""
        # Arrange
        loader = SQLModelLoader()

        # Test None
        opp_none = Opportunity(
            submission_id=None,
            subreddit="test",
            title="Test",
            wtp_score=50.0
        )

        # Test empty string
        opp_empty = Opportunity(
            submission_id="",
            subreddit="test",
            title="Test",
            wtp_score=50.0
        )

        # Act & Assert
        with pytest.raises(ValueError, match="submission_id cannot be empty"):
            loader.save_opportunity(opp_none)

        with pytest.raises(ValueError, match="submission_id cannot be empty"):
            loader.save_opportunity(opp_empty)


class TestSQLModelLoaderTransactionHandling:
    """Test transaction rollback on errors"""

    def test_transaction_rollback_on_database_error(self):
        """Test that transaction rolls back on database error"""
        # Arrange
        loader = SQLModelLoader()

        # Mock database to raise error during commit
        with patch.object(loader, '_get_session') as mock_session_func:
            mock_session = MagicMock()
            mock_session_func.return_value.__enter__.return_value = mock_session

            # Configure mock to raise error on commit
            mock_session.commit.side_effect = IntegrityError(
                "mock", "mock", "mock"
            )

            opp = Opportunity(
                submission_id="rollback_test",
                subreddit="test",
                title="Should Roll Back",
                wtp_score=50.0
            )

            # Act & Assert
            with pytest.raises(IntegrityError):
                loader.save_opportunity(opp)

            # Verify rollback was called
            mock_session.rollback.assert_called_once()

    def test_partial_save_not_possible_on_error(self):
        """Test that partial data is not saved when error occurs mid-operation"""
        # Arrange
        loader = SQLModelLoader()

        # Create a valid opportunity first
        opp1 = Opportunity(
            submission_id="partial_save_1",
            subreddit="test",
            title="First Record",
            wtp_score=50.0
        )
        result1 = loader.save_opportunity(opp1)
        assert result1 is True

        # Now simulate an error during second save
        with patch('sqlmodel.Session') as MockSession:
            mock_session = MagicMock()
            MockSession.return_value = mock_session

            # Configure to add but fail on commit
            mock_session.commit.side_effect = OperationalError(
                "mock", "mock", "mock"
            )

            opp2 = Opportunity(
                submission_id="partial_save_2",
                subreddit="test",
                title="Should Not Save",
                wtp_score=50.0
            )

            # Act
            with pytest.raises(OperationalError):
                loader.save_opportunity(opp2)

        # Assert - Verify only first record exists
        with get_db_session() as session:
            results = session.exec(select(Opportunity)).all()
            submission_ids = [r.submission_id for r in results]

        assert "partial_save_1" in submission_ids
        assert "partial_save_2" not in submission_ids

    def test_session_cleanup_on_error(self):
        """Test that session is properly cleaned up even on errors"""
        # Arrange
        loader = SQLModelLoader()

        with patch.object(loader, '_get_session') as mock_session_func:
            mock_session = MagicMock()
            mock_session_func.return_value.__enter__.return_value = mock_session

            # Configure to raise error
            mock_session.add.side_effect = RuntimeError("Database error")

            opp = Opportunity(
                submission_id="cleanup_test",
                subreddit="test",
                title="Test",
                wtp_score=50.0
            )

            # Act & Assert
            with pytest.raises(RuntimeError):
                loader.save_opportunity(opp)

            # Verify cleanup methods were called
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()

    def test_connection_error_handling(self):
        """Test graceful handling of connection errors"""
        # Arrange
        loader = SQLModelLoader()

        with patch('database.get_engine') as mock_engine:
            mock_engine.side_effect = OperationalError(
                "connection failed", "mock", "mock"
            )

            opp = Opportunity(
                submission_id="connection_error_test",
                subreddit="test",
                title="Test",
                wtp_score=50.0
            )

            # Act & Assert
            with pytest.raises(OperationalError):
                loader.save_opportunity(opp)

    def test_sqlalchemy_error_propagation(self):
        """Test that SQLAlchemy errors are properly propagated"""
        # Arrange
        loader = SQLModelLoader()

        with patch.object(loader, '_get_session') as mock_session_func:
            mock_session = MagicMock()
            mock_session_func.return_value.__enter__.return_value = mock_session

            # Configure to raise generic SQLAlchemyError
            mock_session.add.side_effect = SQLAlchemyError("Generic DB error")

            opp = Opportunity(
                submission_id="sqlalchemy_error_test",
                subreddit="test",
                title="Test",
                wtp_score=50.0
            )

            # Act & Assert
            with pytest.raises(SQLAlchemyError):
                loader.save_opportunity(opp)


class TestSQLModelLoaderBatchOperations:
    """Test batch operations performance and behavior"""

    def test_save_multiple_opportunities_success(self):
        """Test saving multiple opportunities in batch succeeds"""
        # Arrange
        loader = SQLModelLoader()
        opportunities = []

        for i in range(5):
            opp = Opportunity(
                submission_id=f"batch_test_{i}",
                subreddit="test",
                title=f"Batch Test {i}",
                wtp_score=float(50 + i * 10)
            )
            opportunities.append(opp)

        # Act
        results = []
        for opp in opportunities:
            result = loader.save_opportunity(opp)
            results.append(result)

        # Assert
        assert all(results)  # All should return True
        assert len(results) == 5

        # Verify all saved
        with get_db_session() as session:
            saved = session.exec(
                select(Opportunity).where(
                    Opportunity.submission_id.like("batch_test_%")
                )
            ).all()
        assert len(saved) == 5

    def test_batch_operation_all_or_none_behavior(self):
        """Test that batch operations have all or none behavior"""
        # This test will be implemented in Task 2.3 when we add batch_save method
        # For now, we test individual save operations
        pass

    def test_performance_with_many_records(self):
        """Test performance when saving many records"""
        # Arrange
        loader = SQLModelLoader()
        start_time = time.time()

        # Act - Save 100 opportunities
        for i in range(100):
            opp = Opportunity(
                submission_id=f"perf_test_{i}",
                subreddit="test",
                title=f"Performance Test {i}",
                wtp_score=50.0
            )
            loader.save_opportunity(opp)

        elapsed = time.time() - start_time

        # Assert - Should complete in reasonable time (< 5 seconds)
        assert elapsed < 5.0, f"Too slow: {elapsed:.2f} seconds"


class TestSQLModelLoaderConnectionPooling:
    """Test connection pool handling and exhaustion"""

    def test_connection_pool_exhaustion_handling(self):
        """Test graceful handling of connection pool exhaustion"""
        # Arrange
        loader = SQLModelLoader()

        # Mock pool to raise exhaustion error
        with patch('database.get_engine') as mock_engine:
            mock_engine_instance = MagicMock()
            mock_engine.return_value = mock_engine_instance

            # Configure pool to raise timeout
            mock_engine_instance.connect.side_effect = OperationalError(
                "pool timeout", "mock", "mock"
            )

            opp = Opportunity(
                submission_id="pool_exhaustion_test",
                subreddit="test",
                title="Test",
                wtp_score=50.0
            )

            # Act & Assert
            with pytest.raises(OperationalError, match="pool timeout"):
                loader.save_opportunity(opp)

    def test_connection_retry_on_timeout(self):
        """Test connection retry behavior on timeout"""
        # This will be tested in Task 2.3 implementation
        # For now, verify error is raised
        loader = SQLModelLoader()

        opp = Opportunity(
            submission_id="retry_test",
            subreddit="test",
            title="Test",
            wtp_score=50.0
        )

        # Mock to simulate timeout then success
        with patch.object(loader, '_get_session') as mock_session:
            call_count = 0

            def side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise OperationalError("timeout", "mock", "mock")
                return MagicMock()

            mock_session.side_effect = side_effect

            # Act
            result = loader.save_opportunity(opp)

            # Assert - Should succeed after retry
            assert result is True
            assert call_count == 2  # Called twice (fail + retry)

    def test_multiple_connections_from_pool(self):
        """Test that multiple connections can be obtained from pool"""
        # Arrange
        loaders = [SQLModelLoader() for _ in range(3)]
        opportunities = [
            Opportunity(
                submission_id=f"multi_conn_{i}",
                subreddit="test",
                title=f"Multi Connection Test {i}",
                wtp_score=50.0
            )
            for i in range(3)
        ]

        # Act - Save concurrently
        results = []
        for loader, opp in zip(loaders, opportunities):
            result = loader.save_opportunity(opp)
            results.append(result)

        # Assert
        assert all(results)

        # Verify all saved
        with get_db_session() as session:
            saved = session.exec(
                select(Opportunity).where(
                    Opportunity.submission_id.like("multi_conn_%")
                )
            ).all()
        assert len(saved) == 3


class TestSQLModelLoaderConcurrentWrites:
    """Test thread safety and concurrent write operations"""

    def test_concurrent_writes_same_opportunity(self):
        """Test concurrent writes to same submission_id"""
        # Arrange
        submission_id = "concurrent_same"
        results = []
        errors = []

        def save_opportunity(thread_id):
            try:
                loader = SQLModelLoader()
                opp = Opportunity(
                    submission_id=submission_id,
                    subreddit="test",
                    title=f"Thread {thread_id}",
                    wtp_score=50.0 + thread_id
                )
                result = loader.save_opportunity(opp)
                results.append((thread_id, result))
            except Exception as e:
                errors.append((thread_id, e))

        # Act - Create 5 threads trying to save same submission
        threads = []
        for i in range(5):
            thread = threading.Thread(target=save_opportunity, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all to complete
        for thread in threads:
            thread.join()

        # Assert
        assert len(errors) == 0, f"Unexpected errors: {errors}"
        assert len(results) == 5

        # Only one should succeed (return True)
        successful = [r for r in results if r[1] is True]
        failed = [r for r in results if r[1] is False]

        assert len(successful) == 1
        assert len(failed) == 4

        # Verify only one record in database
        with get_db_session() as session:
            records = session.exec(
                select(Opportunity).where(
                    Opportunity.submission_id == submission_id
                )
            ).all()
        assert len(records) == 1

    def test_concurrent_writes_different_opportunities(self):
        """Test concurrent writes to different opportunities"""
        # Arrange
        num_threads = 10
        results = []
        errors = []

        def save_opportunity(thread_id):
            try:
                loader = SQLModelLoader()
                opp = Opportunity(
                    submission_id=f"concurrent_diff_{thread_id}",
                    subreddit="test",
                    title=f"Thread {thread_id}",
                    wtp_score=50.0
                )
                result = loader.save_opportunity(opp)
                results.append((thread_id, result))
            except Exception as e:
                errors.append((thread_id, e))

        # Act - Create threads saving different opportunities
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=save_opportunity, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Assert
        assert len(errors) == 0, f"Unexpected errors: {errors}"
        assert len(results) == num_threads

        # All should succeed
        successful = [r for r in results if r[1] is True]
        assert len(successful) == num_threads

        # Verify all records saved
        with get_db_session() as session:
            records = session.exec(
                select(Opportunity).where(
                    Opportunity.submission_id.like("concurrent_diff_%")
                )
            ).all()
        assert len(records) == num_threads

    def test_thread_safety_with_shared_loader(self):
        """Test thread safety when sharing loader instance"""
        # Arrange
        shared_loader = SQLModelLoader()
        results = []

        def save_with_shared_loader(thread_id):
            opp = Opportunity(
                submission_id=f"shared_loader_{thread_id}",
                subreddit="test",
                title=f"Shared Loader {thread_id}",
                wtp_score=50.0
            )
            result = shared_loader.save_opportunity(opp)
            results.append(result)

        # Act
        threads = []
        for i in range(5):
            thread = threading.Thread(target=save_with_shared_loader, args=(i,))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Assert
        assert all(results)
        assert len(results) == 5


class TestSQLModelLoaderLoggingAndMonitoring:
    """Test logging and monitoring capabilities"""

    def test_successful_save_logs_info(self):
        """Test that successful saves are logged"""
        # Arrange
        loader = SQLModelLoader()

        with patch('logging.getLogger') as mock_logger:
            logger_instance = MagicMock()
            mock_logger.return_value = logger_instance

            opp = Opportunity(
                submission_id="log_test_success",
                subreddit="test",
                title="Test",
                wtp_score=50.0
            )

            # Act
            loader.save_opportunity(opp)

            # Assert
            logger_instance.info.assert_called()
            log_message = logger_instance.info.call_args[0][0]
            assert "Saved opportunity" in log_message
            assert "log_test_success" in log_message

    def test_duplicate_save_logs_warning(self):
        """Test that duplicate saves log warning"""
        # Arrange
        loader = SQLModelLoader()

        # Save first time
        opp1 = Opportunity(
            submission_id="log_test_duplicate",
            subreddit="test",
            title="First",
            wtp_score=50.0
        )
        loader.save_opportunity(opp1)

        # Try to save duplicate
        with patch('logging.getLogger') as mock_logger:
            logger_instance = MagicMock()
            mock_logger.return_value = logger_instance

            opp2 = Opportunity(
                submission_id="log_test_duplicate",
                subreddit="test",
                title="Second",
                wtp_score=50.0
            )

            # Act
            result = loader.save_opportunity(opp2)

            # Assert
            assert result is False
            logger_instance.warning.assert_called()
            log_message = logger_instance.warning.call_args[0][0]
            assert "Duplicate" in log_message
            assert "log_test_duplicate" in log_message

    def test_error_logs_with_context(self):
        """Test that errors are logged with proper context"""
        # Arrange
        loader = SQLModelLoader()

        with patch.object(loader, '_get_session') as mock_session_func:
            mock_session = MagicMock()
            mock_session_func.return_value.__enter__.return_value = mock_session
            mock_session.add.side_effect = RuntimeError("Test error")

            with patch('logging.getLogger') as mock_logger:
                logger_instance = MagicMock()
                mock_logger.return_value = logger_instance

                opp = Opportunity(
                    submission_id="log_test_error",
                    subreddit="test",
                    title="Test",
                    wtp_score=50.0
                )

                # Act
                with pytest.raises(RuntimeError):
                    loader.save_opportunity(opp)

                # Assert
                logger_instance.error.assert_called()
                log_message = logger_instance.error.call_args[0][0]
                assert "Error saving opportunity" in log_message
                assert "log_test_error" in log_message


class TestSQLModelLoaderConfiguration:
    """Test loader configuration and settings"""

    def test_loader_uses_database_config(self):
        """Test that loader uses database configuration from settings"""
        # Arrange
        loader = SQLModelLoader()

        # Assert
        assert loader.engine is not None
        assert hasattr(loader, 'session_factory')

    def test_custom_configuration_support(self):
        """Test that loader accepts custom configuration"""
        # This will be tested in Task 2.3 when we add config support
        # For now, verify default initialization
        loader = SQLModelLoader()
        assert loader is not None

    def test_environment_specific_settings(self):
        """Test that loader adapts to different environments"""
        # This will be tested in Task 2.3 with environment detection
        pass


# Fixtures for test setup
@pytest.fixture
def test_database():
    """Create test database tables"""
    # Create in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    # Patch the database module to use test engine
    with patch('database.get_engine', return_value=engine):
        yield engine

    # Cleanup
    SQLModel.metadata.drop_all(engine)


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
                "problem": "Test problem"
            }
        },
        metrics={
            "market_demand": 85.0,
            "pain_intensity": 70.0,
            "monetization_potential": 90.0,
            "technical_feasibility": 80.0
        }
    )


# Test runner configuration
if __name__ == "__main__":
    # This will fail because SQLModelLoader doesn't exist yet
    # This is INTENTIONAL - TDD RED phase
    pytest.main([__file__, "-v", "--tb=short"])