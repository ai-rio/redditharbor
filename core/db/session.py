"""Database session management for RedditHarbor.

This module provides SQLAlchemy session management with connection pooling,
transaction handling, and proper error handling for PostgreSQL connections.

Components:
- engine: SQLAlchemy engine configured for Supabase PostgreSQL
- SessionLocal: Session factory for database sessions
- get_db_session(): Context manager for database sessions

Usage:
    from core.db.session import get_db_session
    with get_db_session() as session:
        # Use session for database operations
        pass
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import psycopg2

from config.settings import get_database_config

# Configure logging
logger = logging.getLogger(__name__)

# Global engine and session factory
engine: Optional[Engine] = None
SessionLocal: Optional[sessionmaker] = None


def initialize_database() -> None:
    """Initialize database engine and session factory.

    Creates SQLAlchemy engine and session factory configured for
    Supabase PostgreSQL connection with proper pooling settings.
    """
    global engine, SessionLocal

    if engine is not None:
        return  # Already initialized

    try:
        # Get database configuration
        db_config = get_database_config()

        # Create connection string for PostgreSQL
        if 'dsn' in db_config:
            database_url = db_config['dsn']
        else:
            database_url = (
                f"postgresql://{db_config['user']}:{db_config['password']}@"
                f"{db_config['host']}:{db_config['port']}/{db_config['database']}"
            )

        # Create SQLAlchemy engine with optimized settings for Supabase
        engine = create_engine(
            database_url,
            pool_size=db_config.get('min_size', 2),
            max_overflow=db_config.get('max_size', 10) - db_config.get('min_size', 2),
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=False,  # Set to True for SQL debugging
        )

        # Create session factory
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )

        # Test database connection
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))

        logger.info("Database initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def get_engine() -> Engine:
    """Get database engine, initializing if necessary.

    Returns:
        Engine: SQLAlchemy engine instance

    Raises:
        RuntimeError: If database initialization fails
    """
    global engine
    if engine is None:
        initialize_database()
    if engine is None:
        raise RuntimeError("Failed to initialize database engine")
    return engine


def get_session_local() -> sessionmaker:
    """Get session factory, initializing if necessary.

    Returns:
        sessionmaker: SQLAlchemy session factory

    Raises:
        RuntimeError: If database initialization fails
    """
    global SessionLocal
    if SessionLocal is None:
        initialize_database()
    if SessionLocal is None:
        raise RuntimeError("Failed to initialize session factory")
    return SessionLocal


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions.

    Provides a database session with automatic transaction management,
    error handling, and connection cleanup.

    Yields:
        Session: SQLAlchemy session instance

    Example:
        with get_db_session() as session:
            user = session.query(User).filter_by(id=user_id).first()
            user.name = "New Name"
            session.commit()

    Note:
        - Automatically commits on success
        - Automatically rolls back on error
        - Automatically closes session
    """
    session_factory = get_session_local()
    session = session_factory()

    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def create_test_session() -> Session:
    """Create a database session for testing.

    Returns a session that can be used in test environments.
    Caller is responsible for closing the session.

    Returns:
        Session: SQLAlchemy session for testing

    Example:
        def test_something():
            session = create_test_session()
            try:
                # Test code here
                pass
            finally:
                session.close()
    """
    session_factory = get_session_local()
    return session_factory()


def check_database_connection() -> bool:
    """Check if database connection is working.

    Returns:
        bool: True if connection is working, False otherwise
    """
    try:
        eng = get_engine()
        with eng.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


def get_database_info() -> dict:
    """Get database connection information.

    Returns:
        dict: Database connection info and status
    """
    try:
        eng = get_engine()
        with eng.connect() as conn:
            from sqlalchemy import text
            # Get PostgreSQL version
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()

            # Get current database size (if available)
            try:
                result = conn.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()))"))
                size = result.scalar()
            except Exception:
                size = "Unknown"

            return {
                "status": "connected",
                "version": version,
                "size": size,
                "url": str(eng.url).replace(eng.url.password or "", "***") if eng.url.password else str(eng.url)
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# Initialize database on import
try:
    initialize_database()
except Exception as e:
    logger.warning(f"Database initialization deferred: {e}")