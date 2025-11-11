"""
RedditHarbor Marimo Utilities

Database connection utilities for Marimo notebooks integration.
Provides robust database connectivity with proper error handling and logging.
"""

import logging

import pandas as pd
import sqlalchemy
from sqlalchemy.exc import SQLAlchemyError

from .config import MarimoConfig

# Set up logging following RedditHarbor patterns
logger = logging.getLogger(__name__)


class DatabaseConnector:
    """
    Database connector for Marimo notebooks.

    Provides a robust interface for connecting to RedditHarbor database
    and executing queries with proper error handling and fallback mechanisms.
    """

    def __init__(self) -> None:
        """
        Initialize the database connector.

        Creates configuration, builds connection URL, and creates SQLAlchemy engine.
        Gracefully handles connection failures.
        """
        self.config = MarimoConfig()
        self.connection_url = self.config.get_connection_url()
        self.engine = self._create_engine()

    def _create_engine(self) -> sqlalchemy.Engine | None:
        """
        Create SQLAlchemy engine with error handling.

        Returns:
            Optional[sqlalchemy.Engine]: Database engine or None if connection fails
        """
        try:
            engine = sqlalchemy.create_engine(
                self.connection_url,
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=3600,   # Recycle connections after 1 hour
            )
            # Test the connection
            with engine.connect() as conn:
                conn.execute(sqlalchemy.text("SELECT 1"))

            logger.info("✅ Database engine created successfully")
            return engine

        except SQLAlchemyError as e:
            logger.error(f"❌ Failed to create database engine: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error creating database engine: {e}")
            return None

    def execute_query(self, query: str) -> pd.DataFrame:
        """
        Execute SQL query and return results as DataFrame.

        Args:
            query: SQL query string to execute

        Returns:
            pd.DataFrame: Query results or error information as DataFrame
        """
        if self.engine is None:
            logger.warning("⚠️ Database engine not available, returning error DataFrame")
            return pd.DataFrame([{
                "error": "Database connection not available",
                "query": query,
                "connection_url": self.connection_url
            }])

        try:
            logger.info(f"🔍 Executing query: {query[:100]}...")
            result_df = pd.read_sql(query, self.engine)
            logger.info(f"✅ Query executed successfully, returned {len(result_df)} rows")
            return result_df

        except SQLAlchemyError as e:
            error_msg = f"Database query failed: {e}"
            logger.error(f"❌ {error_msg}")
            return pd.DataFrame([{
                "error": error_msg,
                "query": query,
                "connection_url": self.connection_url
            }])

        except Exception as e:
            error_msg = f"Unexpected error executing query: {e}"
            logger.error(f"❌ {error_msg}")
            return pd.DataFrame([{
                "error": error_msg,
                "query": query,
                "connection_url": self.connection_url
            }])

    def test_connection(self) -> bool:
        """
        Test database connectivity.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        if self.engine is None:
            logger.warning("⚠️ Database engine is None")
            return False

        try:
            with self.engine.connect() as conn:
                result = conn.execute(sqlalchemy.text("SELECT 1"))
                logger.info("✅ Database connection test successful")
                return True
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False

    def get_table_info(self, table_name: str) -> pd.DataFrame:
        """
        Get information about a specific table.

        Args:
            table_name: Name of the table to inspect

        Returns:
            pd.DataFrame: Table schema information or error
        """
        query = f"""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position
        """
        return self.execute_query(query)

    def get_available_tables(self) -> pd.DataFrame:
        """
        Get list of available tables in the database.

        Returns:
            pd.DataFrame: List of tables or error
        """
        query = """
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
        """
        return self.execute_query(query)
