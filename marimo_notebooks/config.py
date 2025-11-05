"""
RedditHarbor Marimo Configuration

Configuration management for Marimo notebooks integration.
Follows RedditHarbor project patterns for environment variable handling.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class MarimoConfig:
    """
    Configuration for Marimo notebooks integration.

    Loads configuration from environment variables following RedditHarbor patterns.
    Falls back to defaults if environment variables are not set.
    """

    supabase_url: str
    supabase_key: str
    database_config: Dict[str, Any]

    def __init__(self) -> None:
        """
        Initialize configuration from environment variables or defaults.

        Uses the same pattern as config/settings.py for consistency.
        """
        # Import project settings to maintain consistency
        try:
            # Add project root to path to import config
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            from config.settings import SUPABASE_URL, SUPABASE_KEY, DB_CONFIG

            self.supabase_url = SUPABASE_URL
            self.supabase_key = SUPABASE_KEY
            self.db_config = DB_CONFIG

        except ImportError:
            # Fallback to environment variables and defaults
            self.supabase_url = os.getenv('SUPABASE_URL', 'http://127.0.0.1:54321')
            self.supabase_key = os.getenv('SUPABASE_KEY')
            self.db_config = {"user": "redditor", "submission": "submission", "comment": "comment"}

        # Database connection configuration for PostgreSQL
        self.database_config = {
            'host': os.getenv('DB_HOST', '127.0.0.1'),
            'port': int(os.getenv('DB_PORT', '54322')),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres')
        }

    def get_connection_url(self) -> str:
        """
        Get the database connection URL for SQLAlchemy.

        Returns:
            str: Formatted database connection URL
        """
        return (
            f"postgresql://{self.database_config['user']}:"
            f"{self.database_config['password']}@"
            f"{self.database_config['host']}:"
            f"{self.database_config['port']}/"
            f"{self.database_config['database']}"
        )

    def is_configured(self) -> bool:
        """
        Check if the configuration is properly set up.

        Returns:
            bool: True if configuration is valid, False otherwise
        """
        return (
            self.supabase_url is not None
            and self.supabase_key is not None
            and len(self.supabase_key) > 0
        )