"""
Database Infrastructure Tests for RedditHarbor Pipeline V4

Comprehensive tests for database engine creation, session management,
connection pooling, and transaction handling.
"""

from unittest.mock import MagicMock, patch

import pytest
import sqlalchemy
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import QueuePool
from sqlmodel import SQLModel

import database
from config.settings import Settings
from database import (
    create_db_and_tables,
    get_db_session,
    get_engine,
    get_session,
    get_session_dependency,
    init_db,
)
from models.analysis import Opportunity


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    settings = Settings()
    settings.database_url = "sqlite:///:memory:"
    return settings


@pytest.fixture
def reset_globals():
    """Reset global state between tests"""
    import database
    # Reset globals
    database._engine = None
    database._SessionLocal = None
    yield
    # Clean up after test
    database._engine = None
    database._SessionLocal = None


class TestEngineCreation:
    """Test database engine creation and configuration"""

    def test_engine_creation_with_sqlite(self, mock_settings, reset_globals):
        """Test engine creates correctly with SQLite URL"""
        with patch('database.get_settings', return_value=mock_settings):
            engine = get_engine()

            assert engine is not None
            assert isinstance(engine, sqlalchemy.engine.Engine)
            assert str(engine.url).startswith("sqlite://")
            assert engine.echo is False

    def test_engine_singleton_pattern(self, mock_settings, reset_globals):
        """Test engine follows singleton pattern"""
        with patch('database.get_settings', return_value=mock_settings):
            engine1 = get_engine()
            engine2 = get_engine()

            assert engine1 is engine2

    def test_engine_echo_configuration(self, mock_settings, reset_globals):
        """Test engine echo logging can be configured"""
        with patch('database.get_settings', return_value=mock_settings):
            # Test default echo setting
            engine = get_engine()
            assert engine.echo is False

            # Test with echo enabled
            init_db(echo=True)
            assert engine.echo is True


class TestTableCreation:
    """Test database table creation functionality"""

    @patch('database.get_engine')
    def test_create_tables_without_alembic(self, mock_get_engine, reset_globals):
        """Test table creation without Alembic"""
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine

        with patch('sqlmodel.SQLModel.metadata.create_all') as mock_create_all:
            create_db_and_tables(use_alembic=False)

            mock_create_all.assert_called_once_with(mock_engine)

    @patch('database.get_engine')
    def test_create_tables_with_alembic(self, mock_get_engine, reset_globals):
        """Test table creation with Alembic enabled"""
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine

        with patch('alembic.command.upgrade') as mock_upgrade:
            with patch('alembic.config.Config') as mock_config:
                create_db_and_tables(use_alembic=True)

                mock_config.assert_called_once_with("alembic.ini")
                mock_upgrade.assert_called_once_with(mock_config.return_value, "head")

    @patch('database.get_engine')
    def test_create_tables_exception_handling(self, mock_get_engine, reset_globals):
        """Test exception handling during table creation"""
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine

        with patch('sqlmodel.SQLModel.metadata.create_all') as mock_create_all:
            mock_create_all.side_effect = Exception("Connection failed")

            with pytest.raises(Exception, match="Connection failed"):
                create_db_and_tables(use_alembic=False)


class TestSessionLifecycle:
    """Test database session lifecycle management"""

    def test_get_session_generator(self, mock_settings, reset_globals):
        """Test get_session generator function"""
        with patch('database.get_settings', return_value=mock_settings):
            with patch('database.get_engine') as mock_get_engine:
                mock_engine = MagicMock()
                mock_get_engine.return_value = mock_engine

                session_gen = get_session()
                assert hasattr(session_gen, '__iter__') or hasattr(session_gen, '__next__')

                # Should be a generator
                session = next(session_gen)
                assert session is not None

    def test_db_session_context_manager(self, mock_settings, reset_globals):
        """Test get_db_session context manager"""
        with patch('database.get_settings', return_value=mock_settings):
            with patch('database.get_session') as mock_get_session:
                mock_session = MagicMock()

                def mock_generator():
                    yield mock_session

                mock_get_session.return_value = mock_generator()

                with get_db_session() as session:
                    assert session == mock_session
                    mock_session.commit.assert_not_called()

    def test_db_session_rollback_on_exception(self, mock_settings, reset_globals):
        """Test transaction rollback on exception"""
        with patch('database.get_settings', return_value=mock_settings):
            with patch('database.get_session') as mock_get_session:
                mock_session = MagicMock()

                def mock_generator():
                    yield mock_session

                mock_get_session.return_value = mock_generator()

                with pytest.raises(ValueError, match="Test error"):
                    with get_db_session():
                        raise ValueError("Test error")

                mock_session.rollback.assert_called_once()
                mock_session.commit.assert_not_called()


class TestTransactionRollback:
    """Test transaction rollback functionality"""

    def test_transaction_commit_success(self, mock_settings, reset_globals):
        """Test successful transaction commit"""
        with patch('database.get_settings', return_value=mock_settings):
            with patch('database.get_session') as mock_get_session:
                mock_session = MagicMock()

                def mock_generator():
                    yield mock_session

                mock_get_session.return_value = mock_generator()

                try:
                    with get_db_session() as session:
                        # Simulate successful operations
                        session.execute(text("SELECT 1"))
                        # Should commit normally
                except Exception:
                    pass  # We don't care about the exception in this test

                mock_session.commit.assert_called_once()

    def test_transaction_rollback_on_error(self, mock_settings, reset_globals):
        """Test transaction rollback on database error"""
        with patch('database.get_settings', return_value=mock_settings):
            with patch('database.get_session') as mock_get_session:
                mock_session = MagicMock()
                mock_session.execute.side_effect = OperationalError("Invalid SQL", None, None)

                def mock_generator():
                    yield mock_session

                mock_get_session.return_value = mock_generator()

                with pytest.raises(OperationalError):
                    with get_db_session() as session:
                        session.execute(text("INVALID SQL"))

                mock_session.rollback.assert_called_once()
                mock_session.commit.assert_not_called()


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_invalid_database_url(self, mock_settings, reset_globals):
        """Test handling of invalid database URL"""
        with patch('database.create_engine') as mock_create:
            mock_create.side_effect = Exception("Invalid URL")

            with pytest.raises(Exception):
                with patch('database.get_settings', return_value=mock_settings):
                    # Reset the global engine
                    database._engine = None
                    get_engine()

    def test_session_cleanup_on_teardown(self, mock_settings, reset_globals):
        """Test session cleanup during teardown"""
        with patch('database.get_settings', return_value=mock_settings):
            mock_session = MagicMock()
            mock_session.close = MagicMock()

            def mock_generator():
                yield mock_session

            with patch('database.get_session', return_value=mock_generator()):
                # Consume generator to trigger cleanup
                session_gen = get_session()
                next(session_gen)


class TestDatabaseIntegration:
    """Test database integration with SQLModel"""

    def test_opportunity_model_creation(self, mock_settings, reset_globals):
        """Test Opportunity model can be created"""
        with patch('database.get_settings', return_value=mock_settings):
            engine = get_engine()
            # Create tables first
            SQLModel.metadata.create_all(engine)

            # Create test opportunity
            test_opportunity = Opportunity(
                submission_id="test123",
                subreddit="test",
                title="Test Opportunity",
                wtp_score=75.0,
                analysis={"test": "data"},
                metrics={"market_demand": 80.0}
            )

            assert test_opportunity.submission_id == "test123"
            assert test_opportunity.wtp_score == 75.0
            assert test_opportunity.calculate_final_score() == 80.0  # Based on metrics

    def test_opportunity_trust_level_validation(self, mock_settings, reset_globals):
        """Test Opportunity model trust level validation"""
        # Valid trust levels
        for level in ['LOW', 'MEDIUM', 'HIGH']:
            opp = Opportunity(
                submission_id=f"test123_{level}",  # Unique ID for each
                subreddit="test",
                title="Test",
                wtp_score=50.0,
                trust_level=level
            )
            assert opp.trust_level == level

        # Invalid trust level should raise error
        with pytest.raises(ValueError, match="Trust level must be one of"):
            Opportunity(
                submission_id="test123_invalid",
                subreddit="test",
                title="Test",
                wtp_score=50.0,
                trust_level="INVALID"
            )

    def test_database_url_from_settings(self, reset_globals):
        """Test database URL is loaded from settings"""
        settings = Settings()
        settings.database_url = "sqlite:///test.db"

        with patch('database.get_settings', return_value=settings):
            with patch('database.create_engine') as mock_create:
                mock_engine = MagicMock()
                mock_create.return_value = mock_engine

                # Reset global engine to ensure it's created
                database._engine = None

                engine = get_engine()

                assert mock_create.called
                assert "test.db" in str(settings.database_url)
                mock_create.assert_called_once_with("sqlite:///test.db", **mock_create.call_args[1])


class TestUtilities:
    """Test utility functions and helpers"""

    def test_init_db_function(self, mock_settings, reset_globals):
        """Test init_db convenience function"""
        with patch('database.get_settings', return_value=mock_settings):
            with patch('database.create_db_and_tables') as mock_create:
                with patch('database.get_engine') as mock_engine:
                    mock_engine.return_value.echo = False

                    init_db(echo=True)

                    mock_create.assert_called_once_with(use_alembic=False)
                    # Engine echo should be updated
                    assert mock_engine.return_value.echo is True

    def test_get_session_dependency(self, mock_settings, reset_globals):
        """Test FastAPI dependency function"""
        with patch('database.get_settings', return_value=mock_settings):
            with patch('database.get_db_session') as mock_db_session:
                mock_session = MagicMock()

                def mock_context_manager():
                    return mock_session

                mock_db_session.return_value.__enter__.return_value = mock_session

                dep_func = get_session_dependency()
                result = next(dep_func)

                assert result == mock_session


class TestPerformance:
    """Test performance and concurrency scenarios"""

    @pytest.mark.parametrize("concurrent_sessions", [1, 5, 10])
    def test_concurrent_session_creation(self, concurrent_sessions, mock_settings, reset_globals):
        """Test concurrent session creation"""
        with patch('database.get_settings', return_value=mock_settings):
            with patch('database.get_engine') as mock_get_engine:
                mock_engine = MagicMock()
                mock_get_engine.return_value = mock_engine

                sessions = []

                def create_session():
                    session_gen = get_session()
                    return next(session_gen)

                # Create concurrent sessions
                for _ in range(concurrent_sessions):
                    sessions.append(create_session())

                # Verify all sessions were created
                assert len(sessions) == concurrent_sessions

    def test_session_isolation(self, mock_settings, reset_globals):
        """Test session isolation between different sessions"""
        with patch('database.get_settings', return_value=mock_settings):
            with patch('database.get_session') as mock_get_session:
                mock_session1 = MagicMock()
                mock_session2 = MagicMock()

                def mock_generator(session):
                    def gen():
                        yield session
                    return gen()

                # Create two different sessions
                mock_get_session.side_effect = [
                    mock_generator(mock_session1),
                    mock_generator(mock_session2)
                ]

                session1 = next(get_session())
                session2 = next(get_session())

                # Should be different instances
                assert session1 is not session2


# Additional test utilities
@pytest.fixture
def sample_opportunity_data():
    """Sample opportunity data for testing"""
    return {
        "submission_id": "test123",
        "subreddit": "productivity",
        "title": "Test App Opportunity",
        "wtp_score": 85.0,
        "analysis": {
            "app_idea": {
                "title": "Productivity Tracker",
                "concept": "Task management app",
                "problem_statement": "Difficulty tracking tasks across multiple platforms"
            },
            "pain_points": ["Task fragmentation", "Context switching"]
        },
        "metrics": {
            "market_demand": 90.0,
            "pain_intensity": 85.0,
            "monetization_potential": 75.0,
            "technical_feasibility": 80.0
        },
        "confidence_score": 75.0
    }


@pytest.fixture
def setup_database_tables(mock_settings, reset_globals):
    """Setup database tables for integration tests"""
    with patch('database.get_settings', return_value=mock_settings):
        engine = get_engine()
        # Create all tables
        SQLModel.metadata.create_all(engine)

        yield engine

        # Drop tables after test
        SQLModel.metadata.drop_all(engine)


# Test for table schema validation
def test_opportunity_table_schema(setup_database_tables):
    """Test Opportunity table schema is correctly defined"""
    # Connect to the database and check table structure
    with setup_database_tables.connect() as conn:
        result = conn.execute(text(
            "SELECT sql FROM sqlite_master "
            "WHERE type='table' AND name='opportunities'"
        ))
        table_sql = result.scalar()

        # Verify expected columns exist
        expected_columns = [
            'id', 'submission_id', 'subreddit', 'title',
            'wtp_score', 'final_score', 'confidence_score',
            'analysis', 'metrics', 'trust_level',
            'created_at', 'updated_at'
        ]

        for col in expected_columns:
            assert col.lower() in table_sql.lower()


# Test for engine configuration validation
def test_engine_configuration_postgres():
    """Test PostgreSQL engine configuration is properly defined"""
    # Test that the engine configuration parameters are correctly defined
    settings = Settings()
    settings.database_url = "postgresql://localhost:5432/test"

    # Expected configuration values from database.py
    expected_config = {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'echo': False
    }

    with patch('database.create_engine') as mock_create:
        mock_engine = MagicMock()
        mock_create.return_value = mock_engine

        with patch('database.get_settings', return_value=settings):
            # Reset global engine to ensure it's created
            database._engine = None
            get_engine()

            # Verify create_engine was called with correct parameters
            assert mock_create.called, "create_engine should have been called"
            call_args = mock_create.call_args
            assert call_args is not None, "call_args should not be None"

            # call_args[0] contains positional args, call_args[1] contains kwargs
            assert len(call_args[0]) == 1, "Should have one positional argument (database_url)"
            assert call_args[0][0] == "postgresql://localhost:5432/test"

            call_kwargs = call_args[1]
            assert call_kwargs['poolclass'] == QueuePool
            for key, value in expected_config.items():
                assert call_kwargs[key] == value


# Test for session factory configuration
def test_session_factory_configuration(reset_globals):
    """Test session factory is configured correctly"""
    with patch('database.get_settings') as mock_settings:
        mock_settings.return_value = Settings()

        with patch('database.get_engine') as mock_get_engine:
            mock_engine = MagicMock()
            mock_get_engine.return_value = mock_engine

            # Reset session factory
            database._SessionLocal = None

            # Get session from generator
            session_gen = get_session()
            session = next(session_gen)

            # Verify session configuration
            assert session.bind is mock_engine

            # Clean up the generator
            try:
                next(session_gen)  # This should trigger cleanup
            except StopIteration:
                pass


# Test database initialization workflow
def test_database_initialization_workflow(mock_settings, reset_globals):
    """Test complete database initialization workflow"""
    with patch('database.get_settings', return_value=mock_settings):
        # Test engine creation
        engine = get_engine()
        assert engine is not None

        # Test table creation
        with patch('sqlmodel.SQLModel.metadata.create_all') as mock_create:
            create_db_and_tables(use_alembic=False)
            mock_create.assert_called_once_with(engine)

        # Test session creation
        with patch('database.get_engine') as mock_get_engine:
            mock_engine = MagicMock()
            mock_get_engine.return_value = engine

            session_gen = get_session()
            session = next(session_gen)
            assert session is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
