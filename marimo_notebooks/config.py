"""
Configuration for Marimo notebooks integration.
"""

import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class MarimoConfig:
    """Configuration for Marimo notebooks integration"""

    def __post_init__(self):
        # Load from environment or defaults
        self.supabase_url = os.getenv('SUPABASE_URL', 'http://127.0.0.1:54321')
        self.supabase_key = os.getenv('SUPABASE_KEY', '')
        self.database_config = {
            'host': os.getenv('DB_HOST', '127.0.0.1'),
            'port': int(os.getenv('DB_PORT', '54322')),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres')
        }