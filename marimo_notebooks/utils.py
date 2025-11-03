"""
Utility functions for Marimo notebooks integration.
"""

import pandas as pd
import sqlalchemy
from .config import MarimoConfig


class DatabaseConnector:
    """Database connector for Marimo notebooks"""

    def __init__(self):
        self.config = MarimoConfig()
        self.connection_url = self._build_connection_url()
        self.engine = self._create_engine()

    def _build_connection_url(self):
        """Build database connection URL from config"""
        db_config = self.config.database_config
        return f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"

    def _create_engine(self):
        """Create SQLAlchemy engine"""
        return sqlalchemy.create_engine(self.connection_url)

    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute SQL query and return DataFrame"""
        try:
            return pd.read_sql(query, self.engine)
        except Exception as e:
            # Return error information as DataFrame for graceful error handling
            return pd.DataFrame([{"error": str(e), "query": query}])