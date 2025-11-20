"""Unified DLT (Data Load Tool) loading infrastructure.

This module provides a centralized DLT loader class that encapsulates all data loading
logic for RedditHarbor, replacing scattered DLT code in monolithic scripts.

Key Features:
- Unified interface for all DLT loading operations
- Automatic merge disposition handling (prevents duplicates)
- Statistics tracking (loaded, failed, skipped records)
- Error handling with detailed logging
- Support for batch and streaming loads
- Schema evolution support
- Connection pooling and reuse

Usage:
    from core.storage.dlt_loader import DLTLoader
    from core.dlt import PK_SUBMISSION_ID

    loader = DLTLoader()
    success = loader.load(
        data=opportunities,
        table_name="app_opportunities",
        primary_key=PK_SUBMISSION_ID,
        write_disposition="merge"
    )
"""

import logging
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

import dlt
from dlt.common.pipeline import LoadInfo

logger = logging.getLogger(__name__)


@dataclass
class LoadStatistics:
    """Statistics for DLT loading operations."""

    loaded: int = 0
    failed: int = 0
    skipped: int = 0
    total_attempted: int = 0
    errors: list[str] = field(default_factory=list)

    def add_success(self, count: int = 1) -> None:
        """Record successful load."""
        self.loaded += count
        self.total_attempted += count

    def add_failure(self, count: int = 1, error: str | None = None) -> None:
        """Record failed load."""
        self.failed += count
        self.total_attempted += count
        if error:
            self.errors.append(error)

    def add_skip(self, count: int = 1) -> None:
        """Record skipped records."""
        self.skipped += count

    def get_summary(self) -> dict[str, Any]:
        """Get statistics summary."""
        return {
            "loaded": self.loaded,
            "failed": self.failed,
            "skipped": self.skipped,
            "total_attempted": self.total_attempted,
            "success_rate": (
                self.loaded / self.total_attempted if self.total_attempted > 0 else 0.0
            ),
            "error_count": len(self.errors),
        }

    def reset(self) -> None:
        """Reset statistics."""
        self.loaded = 0
        self.failed = 0
        self.skipped = 0
        self.total_attempted = 0
        self.errors.clear()


class DLTLoader:
    """
    Unified DLT data loader for RedditHarbor.

    Encapsulates all DLT loading logic with consistent interface, error handling,
    and statistics tracking. Replaces scattered DLT code in monolithic scripts.

    Attributes:
        destination: DLT destination (default: "postgres")
        dataset_name: Dataset name (default: "public")
        connection_string: PostgreSQL connection string
        stats: Loading statistics tracker

    Examples:
        >>> # Simple load with merge disposition
        >>> loader = DLTLoader()
        >>> success = loader.load(
        ...     data=opportunities,
        ...     table_name="app_opportunities",
        ...     primary_key="submission_id",
        ...     write_disposition="merge"
        ... )

        >>> # Batch load with custom config
        >>> loader = DLTLoader(dataset_name="reddit_harbor")
        >>> success = loader.load_batch(
        ...     data=submissions,
        ...     table_name="submissions",
        ...     primary_key="submission_id",
        ...     batch_size=100
        ... )

        >>> # Get statistics
        >>> stats = loader.get_statistics()
        >>> print(f"Loaded: {stats['loaded']}, Failed: {stats['failed']}")
    """

    def __init__(
        self,
        destination: str = "postgres",
        dataset_name: str = "public",
        connection_string: str | None = None,
    ):
        """
        Initialize DLT loader.

        Args:
            destination: DLT destination type (default: "postgres")
            dataset_name: Target dataset name (default: "public")
            connection_string: PostgreSQL connection string
                (default: "postgresql://postgres:postgres@127.0.0.1:54322/postgres")
        """
        self.destination = destination
        self.dataset_name = dataset_name
        self.connection_string = (
            connection_string
            or "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
        )
        self.stats = LoadStatistics()
        self._pipeline_cache: dict[str, dlt.Pipeline] = {}

        logger.info(
            f"DLTLoader initialized: destination={destination}, dataset={dataset_name}"
        )

    def _get_or_create_pipeline(self, pipeline_name: str) -> dlt.Pipeline:
        """
        Get cached pipeline or create new one.

        Caches pipelines to avoid recreation overhead.

        Args:
            pipeline_name: Unique pipeline name

        Returns:
            dlt.Pipeline instance
        """
        if pipeline_name not in self._pipeline_cache:
            pipeline = dlt.pipeline(
                pipeline_name=pipeline_name,
                destination=dlt.destinations.postgres(self.connection_string),
                dataset_name=self.dataset_name,
            )
            self._pipeline_cache[pipeline_name] = pipeline
            logger.debug(f"Created new pipeline: {pipeline_name}")
        return self._pipeline_cache[pipeline_name]

    def _create_resource_with_columns(
        self,
        data: list[dict[str, Any]],
        table_name: str,
        columns: dict[str, dict[str, Any]],
        write_disposition: str,
        primary_key: str | None = None,
    ):
        """
        Create a DLT resource with explicit column type hints.

        This is essential for properly storing JSON fields in PostgreSQL as JSONB columns.
        Without explicit type hints, DLT may infer the wrong column types.

        Args:
            data: List of records to load
            table_name: Target table name
            columns: Column type hints dictionary
            write_disposition: Write disposition for the resource
            primary_key: Optional primary key field

        Returns:
            DLT resource function that can be passed to pipeline.run()
        """
        # Create a DLT resource with explicit column type hints
        @dlt.resource(
            name=table_name,
            write_disposition=write_disposition,
            primary_key=primary_key,
            columns=columns,
        )
        def typed_resource():
            """Generator that yields records with type hints."""
            for record in data:
                yield record

        return typed_resource

    def load(
        self,
        data: list[dict[str, Any]],
        table_name: str,
        write_disposition: str = "merge",
        primary_key: str | None = None,
        pipeline_name: str | None = None,
        columns: dict[str, dict[str, Any]] | None = None,
        **kwargs,
    ) -> bool:
        """
        Load data using DLT.

        Main loading method that handles data validation, pipeline creation,
        and error handling.

        Args:
            data: List of records to load
            table_name: Target table name
            write_disposition: "merge" (dedup), "replace" (truncate), or "append"
            primary_key: Primary key field for merge disposition
            pipeline_name: Optional custom pipeline name
            columns: Optional column type hints for DLT schema (e.g., {"field": {"data_type": "jsonb"}})
            **kwargs: Additional arguments passed to pipeline.run()

        Returns:
            bool: True if successful, False otherwise

        Raises:
            ValueError: If merge disposition used without primary_key
            ValueError: If data is empty

        Examples:
            >>> loader = DLTLoader()
            >>> # Merge load (prevents duplicates)
            >>> loader.load(
            ...     data=opportunities,
            ...     table_name="app_opportunities",
            ...     write_disposition="merge",
            ...     primary_key="submission_id"
            ... )

            >>> # Replace load (truncate and reload)
            >>> loader.load(
            ...     data=submissions,
            ...     table_name="submissions",
            ...     write_disposition="replace"
            ... )
        """
        # Validation
        if not data:
            logger.warning(f"No data to load for table '{table_name}'")
            return False

        if write_disposition == "merge" and not primary_key:
            raise ValueError("primary_key required for merge write disposition")

        # Prepare pipeline
        pipeline_name = pipeline_name or f"{table_name}_loader"
        record_count = len(data)

        logger.info(
            f"Loading {record_count} records to '{table_name}' "
            f"(disposition={write_disposition}, pk={primary_key})"
        )

        try:
            pipeline = self._get_or_create_pipeline(pipeline_name)

            # If columns are specified, create a resource with type hints
            if columns:
                resource = self._create_resource_with_columns(
                    data=data,
                    table_name=table_name,
                    columns=columns,
                    write_disposition=write_disposition,
                    primary_key=primary_key,
                )
                load_info: LoadInfo = pipeline.run(resource, **kwargs)
            else:
                # Run DLT pipeline without explicit column hints
                load_info: LoadInfo = pipeline.run(
                    data,
                    table_name=table_name,
                    write_disposition=write_disposition,
                    primary_key=primary_key,
                    **kwargs,
                )

            # Update statistics
            self.stats.add_success(record_count)

            logger.info(
                f" Loaded {record_count} records to '{table_name}' "
                f"(started: {load_info.started_at})"
            )
            logger.debug(f"Load info: {load_info}")

            return True

        except Exception as e:
            error_msg = f"DLT load error for '{table_name}': {e}"
            logger.error(error_msg, exc_info=True)
            self.stats.add_failure(record_count, error=error_msg)
            return False

    def load_with_resource(
        self,
        resource: Callable[..., Iterator[dict[str, Any]]],
        table_name: str,
        primary_key: str | None = None,
        pipeline_name: str | None = None,
        **kwargs,
    ) -> bool:
        """
        Load data using DLT resource (generator function).

        For advanced use cases where data is generated on-the-fly or
        streaming is required.

        Args:
            resource: DLT resource function (generator)
            table_name: Target table name
            primary_key: Primary key for merge disposition
            pipeline_name: Optional custom pipeline name
            **kwargs: Additional arguments passed to pipeline.run()

        Returns:
            bool: True if successful, False otherwise

        Examples:
            >>> @dlt.resource(name="opportunities", write_disposition="merge")
            >>> def opportunities_resource(data):
            ...     for record in data:
            ...         yield record
            >>>
            >>> loader = DLTLoader()
            >>> loader.load_with_resource(
            ...     resource=opportunities_resource(data),
            ...     table_name="app_opportunities",
            ...     primary_key="submission_id"
            ... )
        """
        pipeline_name = pipeline_name or f"{table_name}_resource_loader"

        logger.info(f"Loading resource to '{table_name}' (pk={primary_key})")

        try:
            pipeline = self._get_or_create_pipeline(pipeline_name)

            load_info: LoadInfo = pipeline.run(
                resource, primary_key=primary_key, **kwargs
            )

            # Note: Can't easily count records with resources
            self.stats.add_success(1)  # Track as one successful operation

            logger.info(f" Loaded resource to '{table_name}' (started: {load_info.started_at})")
            logger.debug(f"Load info: {load_info}")

            return True

        except Exception as e:
            error_msg = f"DLT resource load error for '{table_name}': {e}"
            logger.error(error_msg, exc_info=True)
            self.stats.add_failure(1, error=error_msg)
            return False

    def load_batch(
        self,
        data: list[dict[str, Any]],
        table_name: str,
        primary_key: str | None = None,
        batch_size: int = 100,
        write_disposition: str = "merge",
        **kwargs,
    ) -> dict[str, Any]:
        """
        Load data in batches for memory efficiency.

        Useful for large datasets that don't fit in memory.

        Args:
            data: List of records to load
            table_name: Target table name
            primary_key: Primary key for merge disposition
            batch_size: Records per batch (default: 100)
            write_disposition: "merge", "replace", or "append"
            **kwargs: Additional arguments passed to load()

        Returns:
            dict: Batch statistics with:
                - total_records: Total records processed
                - batches: Number of batches
                - successful_batches: Batches loaded successfully
                - failed_batches: Batches that failed
                - success_rate: Percentage of successful batches

        Examples:
            >>> loader = DLTLoader()
            >>> results = loader.load_batch(
            ...     data=large_dataset,
            ...     table_name="submissions",
            ...     primary_key="submission_id",
            ...     batch_size=50
            ... )
            >>> print(f"Loaded {results['total_records']} records in {results['batches']} batches")
        """
        if not data:
            logger.warning(f"No data to batch load for table '{table_name}'")
            return {
                "total_records": 0,
                "batches": 0,
                "successful_batches": 0,
                "failed_batches": 0,
                "success_rate": 0.0,
            }

        total_records = len(data)
        num_batches = (total_records + batch_size - 1) // batch_size
        successful_batches = 0
        failed_batches = 0

        logger.info(
            f"Batch loading {total_records} records to '{table_name}' "
            f"({num_batches} batches of {batch_size})"
        )

        for i in range(0, total_records, batch_size):
            batch = data[i : i + batch_size]
            batch_num = (i // batch_size) + 1

            logger.debug(f"Loading batch {batch_num}/{num_batches} ({len(batch)} records)")

            success = self.load(
                data=batch,
                table_name=table_name,
                write_disposition=write_disposition,
                primary_key=primary_key,
                pipeline_name=f"{table_name}_batch_{batch_num}",
                **kwargs,
            )

            if success:
                successful_batches += 1
            else:
                failed_batches += 1

        success_rate = successful_batches / num_batches if num_batches > 0 else 0.0

        logger.info(
            f" Batch loading complete: {successful_batches}/{num_batches} batches successful "
            f"({success_rate * 100:.1f}%)"
        )

        return {
            "total_records": total_records,
            "batches": num_batches,
            "successful_batches": successful_batches,
            "failed_batches": failed_batches,
            "success_rate": success_rate,
        }

    def get_statistics(self) -> dict[str, Any]:
        """
        Get loading statistics.

        Returns:
            dict: Statistics with loaded, failed, skipped counts and success rate

        Examples:
            >>> loader = DLTLoader()
            >>> # ... perform loads ...
            >>> stats = loader.get_statistics()
            >>> print(f"Success rate: {stats['success_rate'] * 100:.1f}%")
        """
        return self.stats.get_summary()

    def reset_statistics(self) -> None:
        """
        Reset loading statistics.

        Useful for resetting counters between batch operations.

        Examples:
            >>> loader = DLTLoader()
            >>> # ... perform loads ...
            >>> loader.reset_statistics()
            >>> # Start fresh batch
        """
        self.stats.reset()
        logger.debug("Statistics reset")

    def clear_pipeline_cache(self) -> None:
        """
        Clear cached pipelines.

        Forces recreation of pipelines on next use. Useful for testing
        or when changing configuration.

        Examples:
            >>> loader = DLTLoader()
            >>> # ... use loader ...
            >>> loader.clear_pipeline_cache()
            >>> # Next load will create fresh pipeline
        """
        self._pipeline_cache.clear()
        logger.debug("Pipeline cache cleared")
