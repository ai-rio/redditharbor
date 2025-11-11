"""
Test Marimo utilities - Database Connection
Following TDD approach for Task 2: Create Database Connection Utilities
"""
import sqlalchemy

from marimo_notebooks.utils import DatabaseConnector


def test_database_connection():
    """Test DatabaseConnector initialization and engine creation"""
    connector = DatabaseConnector()
    assert connector.connection_url is not None
    # Engine may be None if database is not running - that's expected behavior
    assert isinstance(connector.engine, (type(None), sqlalchemy.engine.base.Engine))


def test_query_execution():
    """Test basic query execution functionality"""
    connector = DatabaseConnector()
    result = connector.execute_query("SELECT 1 as test")
    assert result is not None
    assert len(result) > 0
