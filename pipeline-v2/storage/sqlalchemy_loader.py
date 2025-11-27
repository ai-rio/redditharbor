"""
SQLAlchemy Loader for RedditHarbor Pipeline v2

Phase 1: Foundation implementation for DLT to SQLAlchemy migration.

This module provides a SQLAlchemy-based alternative to DLT for loading
opportunity data to PostgreSQL with explicit transaction control,
eliminating silent failures.

Key Features:
- Explicit transaction control with commit/rollback visibility
- Connection validation and error handling
- Integration with existing ID resolution system
- Foundation-only implementation (Phase 1)

Author: Phase 1 DLT to SQLAlchemy Migration
Version: Pipeline-v2 compatible
"""

import logging
import time
from datetime import datetime, UTC
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Union, Iterator
import os

# SQLAlchemy imports
try:
    from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer, Float, DateTime, Boolean
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, Session
    from sqlalchemy.exc import SQLAlchemyError, OperationalError
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    SQLAlchemyError = Exception
    OperationalError = Exception

# ID resolution system import
try:
    from core.utils.id_resolver import resolve_submission_id, ResolutionResult
    ID_RESOLVER_AVAILABLE = True
except ImportError:
    ID_RESOLVER_AVAILABLE = False
    ResolutionResult = None

logger = logging.getLogger(__name__)

# Constants
DEFAULT_TABLE_NAME = "app_opportunities"
DEFAULT_CONNECTION_STRING = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"


class SQLAlchemyLoaderError(Exception):
    """Custom exception for SQLAlchemy loader operations."""
    pass


class SQLAlchemyConnectionError(SQLAlchemyLoaderError):
    """Exception for connection issues."""
    pass


class SQLAlchemyTransactionError(SQLAlchemyLoaderError):
    """Exception for transaction issues."""
    pass


class SQLAlchemyLoader:
    """
    SQLAlchemy-based data loader for RedditHarber opportunity data.

    Phase 1: Foundation implementation focusing on:
    - Connection management and validation
    - Basic session management
    - Table existence validation
    - ID resolution system integration
    """

    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize SQLAlchemy loader with database connection.

        Args:
            connection_string: PostgreSQL connection string (optional, uses default if None)

        Raises:
            SQLAlchemyLoaderError: If SQLAlchemy is not available
            SQLAlchemyConnectionError: If connection configuration is invalid
        """
        if not SQLALCHEMY_AVAILABLE:
            raise SQLAlchemyLoaderError(
                "SQLAlchemy is not available. Install with: pip install sqlalchemy"
            )

        self.connection_string = connection_string or os.getenv(
            "DATABASE_URL",
            DEFAULT_CONNECTION_STRING
        )

        self._engine = None
        self._session_factory = None
        self._metadata = MetaData()

        # Initialize engine and session factory
        self._initialize_engine()

        # Validate connection after initialization
        if not self.validate_connection():
            raise SQLAlchemyConnectionError("Failed to establish database connection")

    def _initialize_engine(self) -> None:
        """
        Initialize SQLAlchemy engine with optimal settings for RedditHarbor.
        """
        try:
            logger.debug("Initializing SQLAlchemy engine")

            # Create engine with connection pooling and timeout settings
            self._engine = create_engine(
                self.connection_string,
                pool_pre_ping=True,  # Validate connections before use
                pool_recycle=3600,   # Recycle connections after 1 hour
                pool_size=5,         # Connection pool size
                max_overflow=10,     # Additional connections when pool is full
                echo=False,          # Set to True for SQL logging
                connect_args={
                    "connect_timeout": 30,  # Connection timeout
                    "application_name": "reddit_harbor_sqlalchemy_loader"
                }
            )

            # Create session factory
            self._session_factory = sessionmaker(bind=self._engine)

            logger.info("✓ SQLAlchemy engine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize SQLAlchemy engine: {e}")
            raise SQLAlchemyConnectionError(f"Engine initialization failed: {e}")

    def validate_connection(self) -> bool:
        """
        Validate database connection and basic functionality.

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            logger.debug("Validating SQLAlchemy connection")

            with self._engine.connect() as conn:
                # Test basic connectivity
                result = conn.execute(text("SELECT 1 as test")).fetchone()
                if result[0] != 1:
                    raise SQLAlchemyConnectionError("Basic query returned unexpected result")

                # Test database access
                db_version = conn.execute(text("SELECT version()")).scalar()
                logger.debug(f"Connected to PostgreSQL: {db_version}")

                logger.debug("✓ SQLAlchemy connection validation successful")
                return True

        except OperationalError as e:
            logger.error(f"✗ SQLAlchemy connection validation failed (operational): {e}")
            return False
        except Exception as e:
            logger.error(f"✗ SQLAlchemy connection validation failed: {e}")
            return False

    def get_load_statistics(self) -> Dict[str, Any]:
        """
        Get basic database statistics for monitoring and validation.

        Returns:
            Dictionary with database statistics
        """
        try:
            with self._engine.connect() as conn:
                # Basic table statistics
                stats = {
                    "connection_status": "connected",
                    "table_exists": False,
                    "record_count": 0,
                    "last_updated": None,
                    "database_size": 0,
                    "timestamp": datetime.now(UTC).isoformat()
                }

                # Check if app_opportunities table exists
                try:
                    result = conn.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_schema = 'public'
                            AND table_name = 'app_opportunities'
                        )
                    """)).scalar()

                    stats["table_exists"] = bool(result)

                    if stats["table_exists"]:
                        # Get record count
                        count_result = conn.execute(text("SELECT COUNT(*) FROM app_opportunities")).scalar()
                        stats["record_count"] = count_result or 0

                        # Get last updated timestamp
                        last_updated = conn.execute(text("""
                            SELECT MAX(processed_at) FROM app_opportunities
                            WHERE processed_at IS NOT NULL
                        """)).scalar()
                        stats["last_updated"] = last_updated.isoformat() if last_updated else None

                except Exception as e:
                    logger.warning(f"Could not gather table statistics: {e}")

                # Get database size
                try:
                    size_result = conn.execute(text("""
                        SELECT pg_size_pretty(pg_database_size(current_database()))
                    """)).scalar()
                    stats["database_size"] = size_result
                except Exception as e:
                    logger.warning(f"Could not get database size: {e}")

                return stats

        except Exception as e:
            logger.error(f"Error getting load statistics: {e}")
            return {
                "connection_status": "failed",
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat()
            }

    @contextmanager
    def get_session(self) -> Iterator[Session]:
        """
        Context manager for database sessions with automatic cleanup.

        Yields:
            SQLAlchemy session instance

        Usage:
            with loader.get_session() as session:
                # Use session for database operations
                session.execute(text("SELECT * FROM app_opportunities"))
                # Session is automatically closed and cleaned up
        """
        if not self._session_factory:
            raise SQLAlchemyLoaderError("Session factory not initialized")

        session = self._session_factory()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise SQLAlchemyTransactionError(f"Session operation failed: {e}")
        finally:
            session.close()

    def test_id_resolution_integration(self, test_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Test ID resolution system integration (Phase 1 validation).

        Args:
            test_data: Sample data for ID resolution testing

        Returns:
            Dictionary with ID resolution test results
        """
        if not ID_RESOLVER_AVAILABLE:
            return {
                "status": "skipped",
                "reason": "ID resolver not available",
                "timestamp": datetime.now(UTC).isoformat()
            }

        test_results = {
            "status": "completed",
            "total_tests": len(test_data),
            "successful_resolutions": 0,
            "failed_resolutions": 0,
            "results": [],
            "timestamp": datetime.now(UTC).isoformat()
        }

        logger.info(f"Testing ID resolution integration with {len(test_data)} records")

        for i, record in enumerate(test_data):
            try:
                # Test ID resolution
                result = resolve_submission_id(record.get("submission_id"))

                test_record = {
                    "index": i,
                    "input": record.get("submission_id"),
                    "resolved_uuid": result.uuid if result else None,
                    "resolution_source": result.source if result else None,
                    "error": result.error if result else "No resolution result"
                }

                if result and result.uuid:
                    test_results["successful_resolutions"] += 1
                    test_record["status"] = "success"
                else:
                    test_results["failed_resolutions"] += 1
                    test_record["status"] = "failed"

                test_results["results"].append(test_record)

            except Exception as e:
                test_results["failed_resolutions"] += 1
                test_results["results"].append({
                    "index": i,
                    "input": record.get("submission_id"),
                    "status": "error",
                    "error": str(e)
                })

        logger.info(f"ID resolution test completed: {test_results['successful_resolutions']}/{test_results['total_tests']} successful")
        return test_results

    def validate_target_table(self, table_name: str = DEFAULT_TABLE_NAME) -> Dict[str, Any]:
        """
        Validate that target table exists and has expected structure.

        Args:
            table_name: Name of the table to validate

        Returns:
            Dictionary with table validation results
        """
        try:
            with self._engine.connect() as conn:
                # Check if table exists
                table_exists = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = :table_name
                    )
                """), {"table_name": table_name}).scalar()

                validation_result = {
                    "table_name": table_name,
                    "exists": bool(table_exists),
                    "timestamp": datetime.now(UTC).isoformat()
                }

                if validation_result["exists"]:
                    # Get column information
                    columns_result = conn.execute(text("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                        AND table_name = :table_name
                        ORDER BY ordinal_position
                    """), {"table_name": table_name}).fetchall()

                    validation_result["columns"] = [
                        {
                            "name": col[0],
                            "type": col[1],
                            "nullable": col[2] == "YES",
                            "default": col[3]
                        }
                        for col in columns_result
                    ]

                    # Check for critical columns
                    critical_columns = ["submission_id", "title", "processed_at"]
                    existing_columns = [col["name"] for col in validation_result["columns"]]

                    missing_critical = [
                        col for col in critical_columns
                        if col not in existing_columns
                    ]

                    validation_result["missing_critical_columns"] = missing_critical
                    validation_result["validation_status"] = (
                        "valid" if not missing_critical else "incomplete"
                    )

                else:
                    validation_result["validation_status"] = "missing"

                return validation_result

        except Exception as e:
            return {
                "table_name": table_name,
                "exists": False,
                "validation_status": "error",
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat()
            }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_sqlalchemy_loader(connection_string: Optional[str] = None) -> SQLAlchemyLoader:
    """
    Factory function to create SQLAlchemy loader instance.

    Args:
        connection_string: PostgreSQL connection string (optional)

    Returns:
        Configured SQLAlchemy loader instance

    Raises:
        SQLAlchemyLoaderError: If SQLAlchemy is not available
    """
    if not SQLALCHEMY_AVAILABLE:
        raise SQLAlchemyLoaderError(
            "SQLAlchemy is not available. Install with: pip install sqlalchemy"
        )

    return SQLAlchemyLoader(connection_string=connection_string)


def test_sqlalchemy_foundation(connection_string: Optional[str] = None) -> Dict[str, Any]:
    """
    Test SQLAlchemy foundation components for Phase 1 validation.

    Args:
        connection_string: PostgreSQL connection string (optional)

    Returns:
        Dictionary with foundation test results
    """
    test_results = {
        "timestamp": datetime.now(UTC).isoformat(),
        "sqlalchemy_available": SQLALCHEMY_AVAILABLE,
        "id_resolver_available": ID_RESOLVER_AVAILABLE,
        "components": {}
    }

    try:
        # Test 1: Connection and validation
        loader = create_sqlalchemy_loader(connection_string)

        test_results["components"]["connection"] = {
            "status": "success",
            "connection_valid": loader.validate_connection(),
            "statistics": loader.get_load_statistics()
        }

        # Test 2: Table validation
        test_results["components"]["table_validation"] = {
            "status": "success",
            "validation": loader.validate_target_table()
        }

        # Test 3: ID resolution integration
        sample_data = [
            {"submission_id": "t3_test123"},
            {"submission_id": "https://reddit.com/r/test/comments/test123/title/"},
            {"submission_id": "550e8400-e29b-41d4-a716-446655440000"}
        ]
        test_results["components"]["id_resolution"] = loader.test_id_resolution_integration(sample_data)

        test_results["overall_status"] = "success"

    except Exception as e:
        test_results["overall_status"] = "failed"
        test_results["error"] = str(e)
        logger.error(f"SQLAlchemy foundation test failed: {e}")

    return test_results