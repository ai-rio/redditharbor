"""
Pipeline V4 Database Module
SQLModel database configuration and session management for RedditHarbor
"""

import logging
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlmodel import Session, SQLModel

from config.settings import get_settings

# Configure logger
logger = logging.getLogger(__name__)

# Global engine singleton
_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def get_engine() -> Engine:
    """
    Get or create the database engine singleton.
    Configured with connection pooling for PostgreSQL.

    Returns:
        Engine: SQLAlchemy engine instance
    """
    global _engine

    if _engine is None:
        settings = get_settings()

        # Engine configuration optimized for PostgreSQL
        engine_kwargs = {
            "poolclass": QueuePool,
            "pool_size": 10,          # Default pool size
            "max_overflow": 20,       # Additional connections beyond pool_size
            "pool_timeout": 30,       # Seconds to wait before giving up
            "pool_recycle": 3600,     # Recycle connections after 1 hour
            "pool_pre_ping": True,    # Validate connections before use
            "echo": False,            # Set to True for SQL logging
        }

        # Create engine
        _engine = create_engine(
            settings.database_url,
            **engine_kwargs
        )

        logger.info("Created database engine for PostgreSQL")

    return _engine


def create_db_and_tables(use_alembic: bool = False) -> None:
    """
    Create database tables from SQLModel metadata.

    Args:
        use_alembic: If True, use Alembic migrations instead of direct creation.
                    Recommended for production environments.
    """
    engine = get_engine()

    if use_alembic:
        logger.info("Using Alembic for database migrations - run 'alembic upgrade head'")
        # Note: In production, use 'alembic upgrade head' instead
        import alembic.config
        alembic_cfg = alembic.config.Config("alembic.ini")
        alembic.command.upgrade(alembic_cfg, "head")
    else:
        try:
            # Create all tables from SQLModel metadata
            SQLModel.metadata.create_all(engine)
            logger.info("Successfully created database tables")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise


def get_session() -> Generator[Session, None, None]:
    """
    Generator function that yields a database session.
    Proper session lifecycle management with automatic cleanup.

    Yields:
        Session: SQLAlchemy session instance

    Example:
        with next(get_session()) as session:
            # Use session here
            pass
    """
    global _SessionLocal

    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            class_=Session
        )

    session = _SessionLocal()

    try:
        yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    Provides automatic transaction handling.

    Yields:
        Session: SQLAlchemy session instance

    Example:
        with get_db_session() as session:
            # Use session here
            # Transaction automatically committed/rolled back
            pass
    """
    session = next(get_session())

    try:
        yield session
        session.commit()
        logger.debug("Database transaction committed")
    except Exception as e:
        session.rollback()
        logger.error(f"Database transaction rolled back: {e}")
        raise
    finally:
        session.close()


def init_db(echo: bool = False, use_alembic: bool = False) -> None:
    """
    Initialize the database with tables and optional echo logging.

    Args:
        echo: Enable SQL query logging
        use_alembic: Use Alembic migrations instead of direct creation
    """
    # Update engine echo setting if needed
    if echo:
        engine = get_engine()
        if engine.echo != echo:
            engine.echo = echo
            logger.info("Enabled SQL query logging")

    # Create tables
    create_db_and_tables(use_alembic=use_alembic)
    logger.info("Database initialization complete")


def get_session_dependency() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI or similar frameworks.
    Returns a database session with proper lifecycle management.

    This is designed to be used with dependency injection systems.

    Yields:
        Session: Database session instance
    """
    with get_db_session() as session:
        yield session


# Engine property for backward compatibility
engine = get_engine

# Session factory for backward compatibility
SessionLocal = lambda: next(get_session())


if __name__ == "__main__":
    # Test database configuration
    logging.basicConfig(level=logging.INFO)

    print("Testing database configuration...")

    # Test engine creation
    try:
        db_engine = get_engine()
        print(f"✓ Engine created: {type(db_engine).__name__}")
        print(f"  URL: {db_engine.url}")
        print(f"  Pool size: {db_engine.pool.size()}")
        print(f"  Checked out: {db_engine.pool.checkedout()}")
    except Exception as e:
        print(f"✗ Engine creation failed: {e}")
        exit(1)

    # Test session creation
    try:
        with next(get_session()) as session:
            print(f"✓ Session created: {type(session).__name__}")
            # Test a simple query
            from sqlalchemy import text
            result = session.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"  PostgreSQL version: {version[:50]}...")
    except Exception as e:
        print(f"✗ Session test failed: {e}")
        exit(1)

    print("\n✓ Database configuration is working correctly!")
    print("\nTo create tables, run:")
    print("  from database import create_db_and_tables")
    print("  create_db_and_tables()")
    print("\nOr use the convenience function:")
    print("  from database import init_db")
    print("  init_db(echo=True)  # Enable SQL logging")
