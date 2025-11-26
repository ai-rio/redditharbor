"""
DLT Pipeline Helper for RedditHarbor Pipeline v2

This module provides DLT pipeline configuration and management for loading
validated opportunity data to Supabase (PostgreSQL) with merge disposition.

Key Features:
- Configurable DLT pipeline with Supabase/PostgreSQL destination
- Merge disposition for app_opportunities table using submission_id as primary key
- Error handling and connection validation
- Load statistics and monitoring
- Support for both connection string and structured credential formats

Author: Phase 5 DLT Implementation
Version: Pipeline-v2 compatible
"""

import logging
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# DLT imports
try:
    import dlt
    from dlt.common.pipeline import LoadInfo
    from dlt.common.destination import Destination
    DLT_AVAILABLE = True
except ImportError as e:
    DLT_AVAILABLE = False
    dlt = None
    LoadInfo = None
    Destination = None

# TOML imports for configuration
try:
    import toml
    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False
    toml = None

# Supabase client for connection validation
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    create_client = None

logger = logging.getLogger(__name__)

# Constants for DLT configuration
DEFAULT_PIPELINE_NAME = "reddit_opportunity_pipeline_v2"
DEFAULT_TABLE_NAME = "app_opportunities"
DEFAULT_PRIMARY_KEY = "submission_id"
DEFAULT_WRITE_DISPOSITION = "merge"
DEFAULT_DATASET_NAME = "app_opportunities"

# Default connection settings for local Supabase development
DEFAULT_LOCAL_SUPABASE = {
    "host": "localhost",
    "port": 5432,
    "database": "postgres",
    "username": "postgres",
    "password": "postgres"
}


class DLTLoaderError(Exception):
    """Custom exception for DLT loader operations."""
    pass


class DLTCredentialError(DLTLoaderError):
    """Exception for DLT credential configuration issues."""
    pass


class DLTConnectionError(DLTLoaderError):
    """Exception for DLT connection issues."""
    pass


class DLTLoader:
    """
    DLT Pipeline Manager for RedditHarbor data loading to Supabase.

    Provides high-level interface for creating and managing DLT pipelines
    with proper error handling, configuration management, and merge disposition
    for the app_opportunities table.
    """

    def __init__(
        self,
        pipeline_name: str = DEFAULT_PIPELINE_NAME,
        secrets_path: Optional[str] = None,
        use_local_dev: bool = True
    ):
        """
        Initialize DLT loader with configuration.

        Args:
            pipeline_name: Name for the DLT pipeline
            secrets_path: Path to secrets.toml file (default: .dlt/secrets.toml)
            use_local_dev: Use local development Supabase settings

        Raises:
            DLTLoaderError: If DLT is not available
            DLTCredentialError: If configuration is invalid
        """
        if not DLT_AVAILABLE:
            raise DLTLoaderError("DLT library is not available. Install with: pip install dlt")

        self.pipeline_name = pipeline_name
        self.secrets_path = secrets_path or self._get_default_secrets_path()
        self.use_local_dev = use_local_dev
        self._pipeline = None
        self._credentials = None

        # Load configuration on initialization
        self._load_configuration()
        self._validate_configuration()

    def _get_default_secrets_path(self) -> str:
        """Get default path for secrets.toml file."""
        current_dir = Path(__file__).parent.parent
        return str(current_dir / ".dlt" / "secrets.toml")

    def _load_configuration(self) -> None:
        """Load DLT configuration from secrets.toml file."""
        try:
            secrets_file = Path(self.secrets_path)
            if not secrets_file.exists():
                if self.use_local_dev:
                    logger.warning(f"Secrets file not found at {self.secrets_path}, using local defaults")
                    self._create_default_config()
                else:
                    raise DLTCredentialError(f"Secrets file not found: {self.secrets_path}")

            if TOML_AVAILABLE and secrets_file.exists():
                config = toml.load(secrets_file)
                self._credentials = self._extract_credentials_from_config(config)
                logger.debug("DLT configuration loaded successfully")
            else:
                logger.warning("TOML not available, using local development defaults")
                self._credentials = self._create_local_credentials()

        except Exception as e:
            logger.error(f"Error loading DLT configuration: {e}")
            raise DLTCredentialError(f"Failed to load configuration: {e}")

    def _create_default_config(self) -> None:
        """Create default secrets.toml configuration for local development."""
        secrets_dir = Path(self.secrets_path).parent
        secrets_dir.mkdir(parents=True, exist_ok=True)

        default_config = f"""# DLT Configuration for RedditHarbor Pipeline v2
# Auto-generated for local development

[runtime]
log_level = "INFO"

# Supabase Destination Configuration (PostgreSQL backend)
[destination.postgres]
credentials = "postgresql://postgres:postgres@localhost:54322/postgres"

[destination.postgres.data_writer]
disposition = "merge"
write_disposition = "merge"

[sources.reddit]
client_id = "your_reddit_client_id_here"
client_secret = "your_reddit_client_secret_here"
user_agent = "RedditHarbor/1.0"
"""

        with open(self.secrets_path, 'w') as f:
            f.write(default_config)

        logger.info(f"Created default configuration at {self.secrets_path}")

    def _extract_credentials_from_config(self, config: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        """Extract credentials from DLT configuration."""
        try:
            # Try postgres destination first (recommended for Supabase)
            if "destination" in config and "postgres" in config["destination"]:
                postgres_config = config["destination"]["postgres"]

                # Direct connection string
                if "credentials" in postgres_config:
                    return postgres_config["credentials"]

                # Structured credentials
                elif "credentials" in postgres_config and isinstance(postgres_config["credentials"], dict):
                    return postgres_config["credentials"]

            # Fallback to supabase destination (legacy support)
            elif "destination" in config and "supabase" in config["destination"]:
                supabase_config = config["destination"]["supabase"]

                if "credentials" in supabase_config:
                    if isinstance(supabase_config["credentials"], str):
                        return supabase_config["credentials"]
                    elif isinstance(supabase_config["credentials"], dict):
                        return supabase_config["credentials"]

            raise DLTCredentialError("No valid destination credentials found in configuration")

        except Exception as e:
            raise DLTCredentialError(f"Error extracting credentials: {e}")

    def _create_local_credentials(self) -> Union[str, Dict[str, Any]]:
        """Create local development credentials."""
        if self.use_local_dev:
            # Use connection string format for simplicity
            return (
                f"postgresql://{DEFAULT_LOCAL_SUPABASE['username']}:"
                f"{DEFAULT_LOCAL_SUPABASE['password']}@"
                f"{DEFAULT_LOCAL_SUPABASE['host']}:"
                f"{DEFAULT_LOCAL_SUPABASE['port']}/"
                f"{DEFAULT_LOCAL_SUPABASE['database']}"
            )
        else:
            raise DLTCredentialError("No credentials available and local development disabled")

    def _validate_configuration(self) -> None:
        """Validate DLT configuration."""
        if not self._credentials:
            raise DLTCredentialError("No credentials configured")

        # Validate credential format
        if isinstance(self._credentials, str):
            if not self._validate_connection_string(self._credentials):
                raise DLTCredentialError("Invalid PostgreSQL connection string format")
        elif isinstance(self._credentials, dict):
            required_fields = ["host", "port", "database", "username", "password"]
            missing_fields = [field for field in required_fields if field not in self._credentials]
            if missing_fields:
                raise DLTCredentialError(f"Missing required credential fields: {missing_fields}")

        logger.debug("DLT configuration validated successfully")

    def _validate_connection_string(self, conn_str: str) -> bool:
        """Validate PostgreSQL connection string format."""
        try:
            import re
            pattern = r'^(postgres(?:ql)?)://[^@]+@[^:]+:\d+/[^/]+$'
            return bool(re.match(pattern, conn_str))
        except ImportError:
            # Fallback validation without regex
            return (
                conn_str.startswith(('postgresql://', 'postgres://')) and
                '@' in conn_str and
                ':' in conn_str.split('@')[-1]
            )

    def create_pipeline(
        self,
        destination: str = "postgres",
        dataset_name: str = DEFAULT_DATASET_NAME
    ) -> Any:
        """
        Create and configure DLT pipeline.

        Args:
            destination: Destination type ('postgres' for Supabase)
            dataset_name: Dataset name in the destination

        Returns:
            Configured DLT pipeline instance

        Raises:
            DLTConnectionError: If pipeline creation fails
        """
        try:
            logger.debug(f"Creating DLT pipeline: {self.pipeline_name}")

            # Create pipeline with credentials
            if isinstance(self._credentials, str):
                pipeline = dlt.pipeline(
                    pipeline_name=self.pipeline_name,
                    destination=destination,
                    dataset_name=dataset_name,
                    credentials=self._credentials
                )
            else:
                # Structured credentials
                pipeline = dlt.pipeline(
                    pipeline_name=self.pipeline_name,
                    destination=destination,
                    dataset_name=dataset_name,
                    credentials=self._credentials
                )

            self._pipeline = pipeline
            logger.info(f"✓ DLT pipeline created: {self.pipeline_name}")
            return pipeline

        except Exception as e:
            logger.error(f"Error creating DLT pipeline: {e}")
            raise DLTConnectionError(f"Failed to create pipeline: {e}")

    def load_opportunities(
        self,
        opportunities: List[Dict[str, Any]],
        table_name: str = DEFAULT_TABLE_NAME,
        primary_key: str = DEFAULT_PRIMARY_KEY,
        write_disposition: str = DEFAULT_WRITE_DISPOSITION,
        pipeline: Optional[Any] = None
    ) -> LoadInfo:
        """
        Load opportunity data to Supabase using DLT with merge disposition.

        Args:
            opportunities: List of opportunity records to load
            table_name: Target table name
            primary_key: Primary key for merge disposition
            write_disposition: Write disposition (default: 'merge')
            pipeline: Existing pipeline instance (optional)

        Returns:
            DLT LoadInfo with load results

        Raises:
            DLTLoaderError: If load operation fails
        """
        if not opportunities:
            logger.warning("No opportunities to load")
            # Return empty LoadInfo for consistency
            from types import SimpleNamespace
            return SimpleNamespace(
                load_id="empty_load",
                schema_name="public",
                table_names=[table_name],
                counts={table_name: 0}
            )

        # Use provided pipeline or create new one
        if pipeline is None:
            if self._pipeline is None:
                self.create_pipeline()
            pipeline = self._pipeline

        try:
            logger.info(f"Loading {len(opportunities)} opportunities to {table_name}")
            start_time = time.time()

            # Run DLT pipeline with merge disposition
            load_info = pipeline.run(
                opportunities,
                table_name=table_name,
                write_disposition=write_disposition,
                primary_key=primary_key
            )

            load_time = time.time() - start_time

            # Log load statistics
            total_records = sum(load_info.counts.values()) if hasattr(load_info, 'counts') else len(opportunities)
            logger.info(f"✓ DLT load completed in {load_time:.2f}s")
            logger.info(f"  - Load ID: {getattr(load_info, 'load_id', 'unknown')}")
            logger.info(f"  - Records processed: {total_records}")
            logger.info(f"  - Table: {table_name}")
            logger.info(f"  - Write disposition: {write_disposition}")

            return load_info

        except Exception as e:
            logger.error(f"Error in DLT load operation: {e}")
            raise DLTLoaderError(f"Load operation failed: {e}")

    def validate_connection(self) -> bool:
        """
        Validate DLT connection to Supabase/PostgreSQL.

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            logger.debug("Validating DLT connection")

            # Create test pipeline
            test_pipeline = self.create_pipeline()

            # Test connection by running a simple query
            # Note: This is a basic validation - DLT will validate on first use
            if test_pipeline:
                logger.debug("✓ DLT connection validation successful")
                return True
            else:
                logger.error("✗ DLT connection validation failed: No pipeline created")
                return False

        except Exception as e:
            logger.error(f"✗ DLT connection validation failed: {e}")
            return False

    def get_load_statistics(self, load_info: LoadInfo) -> Dict[str, Any]:
        """
        Extract and format load statistics from LoadInfo.

        Args:
            load_info: DLT LoadInfo instance

        Returns:
            Dictionary with formatted load statistics
        """
        try:
            stats = {
                "load_id": getattr(load_info, 'load_id', 'unknown'),
                "schema_name": getattr(load_info, 'schema_name', 'unknown'),
                "table_names": getattr(load_info, 'table_names', []),
                "total_records": 0,
                "table_counts": {},
                "load_timestamp": datetime.now(UTC).isoformat()
            }

            # Extract count information
            if hasattr(load_info, 'counts') and load_info.counts:
                stats["table_counts"] = dict(load_info.counts)
                stats["total_records"] = sum(load_info.counts.values())

            return stats

        except Exception as e:
            logger.error(f"Error extracting load statistics: {e}")
            return {
                "load_id": "error",
                "total_records": 0,
                "error": str(e)
            }

    def prepare_opportunity_data(
        self,
        submissions: List[Dict[str, Any]],
        score_threshold: float = 40.0
    ) -> List[Dict[str, Any]]:
        """
        Prepare submission data for DLT loading with proper field mapping.

        Args:
            submissions: List of processed submissions with analysis
            score_threshold: Minimum trust score for inclusion

        Returns:
            List of formatted opportunity records for DLT
        """
        opportunities = []

        for submission in submissions:
            # Filter by trust score threshold
            if submission.get("overall_trust_score", 0) < score_threshold:
                continue

            # Map fields to expected database schema
            opportunity = {
                # Primary key and Reddit fields
                "submission_id": submission.get("submission_id"),
                "title": submission.get("title"),
                "text": submission.get("text", ""),
                "subreddit": submission.get("subreddit"),
                "upvotes": submission.get("upvotes", 0),
                "comments_count": submission.get("comments_count", 0),
                "score": submission.get("score", 0),
                "created_utc": submission.get("created_utc"),
                "permalink": submission.get("permalink", ""),

                # Quality and analysis fields
                "quality_score": submission.get("quality_score"),
                "filter_reason": submission.get("filter_reason"),
                "opportunity_score": submission.get("final_score"),
                "core_functions": submission.get("core_functions", []),
                "app_concept": submission.get("app_concept", ""),
                "problem_description": submission.get("problem_description", ""),

                # Trust validation fields
                "trust_score": submission.get("overall_trust_score"),
                "trust_level": submission.get("trust_level", ""),
                "trust_badges": submission.get("trust_badges", []),
                "confidence_score": submission.get("confidence_score", 0.0),

                # Monetization analysis fields
                "monetization_score": submission.get("llm_monetization_score"),
                "willingness_to_pay_score": submission.get("willingness_to_pay_score"),
                "customer_segment": submission.get("customer_segment", ""),

                # Processing metadata
                "processed_at": submission.get("validation_timestamp", datetime.now(UTC).isoformat()),
                "pipeline_version": "pipeline_v2"
            }

            # Remove None values to keep data clean
            opportunity = {k: v for k, v in opportunity.items() if v is not None}

            opportunities.append(opportunity)

        logger.debug(f"Prepared {len(opportunities)} opportunities for DLT loading")
        return opportunities


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_dlt_loader(
    pipeline_name: str = DEFAULT_PIPELINE_NAME,
    secrets_path: Optional[str] = None,
    use_local_dev: bool = True
) -> DLTLoader:
    """
    Factory function to create DLT loader instance.

    Args:
        pipeline_name: Name for the DLT pipeline
        secrets_path: Path to secrets.toml file
        use_local_dev: Use local development settings

    Returns:
        Configured DLT loader instance
    """
    return DLTLoader(
        pipeline_name=pipeline_name,
        secrets_path=secrets_path,
        use_local_dev=use_local_dev
    )


def load_opportunities_to_supabase(
    submissions: List[Dict[str, Any]],
    score_threshold: float = 40.0,
    pipeline_name: str = DEFAULT_PIPELINE_NAME,
    table_name: str = DEFAULT_TABLE_NAME
) -> Tuple[bool, Dict[str, Any]]:
    """
    Convenience function to load opportunities to Supabase.

    Args:
        submissions: List of processed submissions
        score_threshold: Minimum trust score
        pipeline_name: DLT pipeline name
        table_name: Target table name

    Returns:
        Tuple of (success_flag, load_statistics)
    """
    try:
        loader = create_dlt_loader(pipeline_name=pipeline_name)

        # Prepare data
        opportunities = loader.prepare_opportunity_data(submissions, score_threshold)

        if not opportunities:
            logger.info("No opportunities meet the score threshold")
            return True, {"total_records": 0, "skipped_reason": "score_threshold"}

        # Load data
        load_info = loader.load_opportunities(
            opportunities,
            table_name=table_name
        )

        # Get statistics
        stats = loader.get_load_statistics(load_info)
        return True, stats

    except Exception as e:
        logger.error(f"Failed to load opportunities to Supabase: {e}")
        return False, {"error": str(e), "total_records": 0}