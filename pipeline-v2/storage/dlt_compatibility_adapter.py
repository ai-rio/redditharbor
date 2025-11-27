"""
DLT Compatibility Adapter for RedditHarbor Pipeline v2

Provides DLT-like interface for SQLAlchemy loader to ensure backwards compatibility.
This allows existing code to work without modification while gaining the reliability
benefits of SQLAlchemy.
"""

import logging
from typing import Any, Dict, List, Optional
from types import SimpleNamespace

from .sqlalchemy_loader import SQLAlchemyLoader, LoadResult

logger = logging.getLogger(__name__)


class DLTCompatibilityAdapter:
    """
    Adapter that provides DLT-compatible interface for SQLAlchemy loader.

    This allows existing code to work without modification while gaining
    the reliability benefits of SQLAlchemy.
    """

    def __init__(self, sqlalchemy_loader: SQLAlchemyLoader, pipeline_name: str = "reddit_opportunity_pipeline_v2"):
        """
        Initialize DLT compatibility adapter.

        Args:
            sqlalchemy_loader: Underlying SQLAlchemy loader
            pipeline_name: Pipeline name for compatibility
        """
        self.loader = sqlalchemy_loader
        self.pipeline_name = pipeline_name
        self._last_load_info = None

    def run(
        self,
        data: List[Dict[str, Any]],
        table_name: str = "app_opportunities",
        write_disposition: str = "merge",
        primary_key: str = "submission_id"
    ) -> SimpleNamespace:
        """
        Run data loading with DLT-compatible interface.

        Args:
            data: Data to load
            table_name: Target table name
            write_disposition: Write disposition
            primary_key: Primary key column

        Returns:
            DLT-like LoadInfo object
        """
        try:
            result = self.loader.load_opportunities(
                opportunities=data,
                write_disposition=write_disposition
            )

            # Convert to DLT-like format
            load_info = SimpleNamespace(
                load_id=result.load_id,
                schema_name="public",
                table_names=[table_name],
                counts={table_name: result.records_inserted + result.records_updated},
                success=result.success,
                error_message=result.error_message
            )

            self._last_load_info = load_info
            return load_info

        except Exception as e:
            logger.error(f"DLT adapter load failed: {e}")
            # Return DLT-like failure object
            load_info = SimpleNamespace(
                load_id="failed",
                schema_name="public",
                table_names=[table_name],
                counts={table_name: 0},
                success=False,
                error_message=str(e)
            )

            self._last_load_info = load_info
            return load_info

    @property
    def last_trace(self) -> Optional[SimpleNamespace]:
        """Get information about the last run (DLT compatibility)."""
        if self._last_load_info:
            return SimpleNamespace(
                load_id=self._last_load_info.load_id,
                success=self._last_load_info.success,
                duration=0.0  # Not tracked in current implementation
            )
        return None

    def state(self) -> Dict[str, Any]:
        """Get pipeline state (DLT compatibility)."""
        return {
            "pipeline_name": self.pipeline_name,
            "destination": "postgresql",
            "dataset_name": "app_opportunities",
            "adapter": "sqlalchemy_compatibility"
        }


def create_dlt_compatible_loader(
    connection_string: str = None,
    pipeline_name: str = "reddit_opportunity_pipeline_v2",
    use_local_dev: bool = True
) -> DLTCompatibilityAdapter:
    """
    Create DLT-compatible loader using SQLAlchemy backend.

    Args:
        connection_string: PostgreSQL connection string
        pipeline_name: Pipeline name for compatibility
        use_local_dev: Use local development defaults

    Returns:
        DLT-compatible loader adapter
    """
    from .sqlalchemy_loader import create_sqlalchemy_loader

    sqlalchemy_loader = create_sqlalchemy_loader(
        connection_string=connection_string
    )

    return DLTCompatibilityAdapter(
        sqlalchemy_loader=sqlalchemy_loader,
        pipeline_name=pipeline_name
    )