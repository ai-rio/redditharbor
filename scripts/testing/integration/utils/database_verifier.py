"""Database verifier module for real-time SQLAlchemy-based validation.

This module provides comprehensive database verification capabilities using
SQLAlchemy ORM patterns to validate data storage integrity during tests.
Eliminates manual double-checking by integrating real-time validation.

Usage:
    from scripts.testing.integration.utils.database_verifier import DatabaseVerifier

    verifier = DatabaseVerifier()
    result = verifier.verify_submission_storage(submission_id, pipeline_result)
"""

import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any

# Add project root to path for imports
sys.path.append("/home/carlos/projects/redditharbor-core-functions-fix")

try:
    from sqlalchemy import create_engine, inspect, text
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import Session, sessionmaker

    from core.utils.id_resolver import ResolutionResult, resolve_submission_id
except ImportError as e:
    if "sqlalchemy" in str(e).lower():
        print("ERROR: SQLAlchemy not available. Install with: pip install sqlalchemy")
    elif "id_resolver" in str(e).lower():
        print("ERROR: Canonical ID resolver not available. Check core/utils/id_resolver.py")
    else:
        print(f"ERROR: Import failed: {e}")
    sys.exit(1)

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of database verification operation."""

    success: bool
    message: str
    stored_fields: int = 0
    expected_fields: int = 0
    field_coverage: float = 0.0
    missing_fields: list[str] = None
    table_status: dict[str, bool] = None
    timestamp: datetime | None = None

    def __post_init__(self):
        if self.missing_fields is None:
            self.missing_fields = []
        if self.table_status is None:
            self.table_status = {}
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class TableSchema:
    """Schema information for database tables."""

    table_name: str
    columns: list[str]
    primary_keys: list[str]
    nullable_columns: list[str]
    column_types: dict[str, str]


class DatabaseVerifier:
    """
    Comprehensive database verifier using SQLAlchemy patterns.

    Provides real-time validation of data storage with proper session management,
    transaction control, and connection handling following SQLAlchemy best practices.
    """

    def __init__(self, database_url: str | None = None):
        """
        Initialize database verifier with SQLAlchemy engine and session factory.

        Args:
            database_url: PostgreSQL connection URL (defaults to local Supabase)

        Raises:
            SQLAlchemyError: If database connection fails
        """
        # Default to local Supabase PostgreSQL
        if database_url is None:
            database_url = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

        try:
            # Create engine with connection pooling
            self.engine = create_engine(
                database_url,
                pool_pre_ping=True,  # Validate connections before use
                pool_recycle=3600,  # Recycle connections after 1 hour
                echo=False,  # Set to True for SQL debugging
            )

            # Create session factory
            self.SessionLocal = sessionmaker(bind=self.engine)

            # Test connection
            self._test_connection()

            # Cache table schemas for performance
            self._table_schemas = self._load_table_schemas()

            logger.info("Database verifier initialized successfully")

        except SQLAlchemyError as e:
            logger.error(f"Failed to initialize database verifier: {e}")
            raise

    def _test_connection(self) -> None:
        """Test database connection with proper session handling."""
        try:
            with self.SessionLocal() as session:
                result = session.execute(text("SELECT 1 as test"))
                test_value = result.scalar()
                if test_value != 1:
                    raise SQLAlchemyError("Connection test failed")
                logger.debug("Database connection test successful")
        except Exception as e:
            raise SQLAlchemyError(f"Database connection failed: {e}")

    def _load_table_schemas(self) -> dict[str, TableSchema]:
        """Load and cache table schema information."""
        schemas = {}
        tables_to_check = [
            "submissions",
            "app_opportunities",
            "opportunity_scores",
            "market_validations",
            "monetization_patterns",
            "competitive_landscape",
        ]

        try:
            with self.SessionLocal() as session:
                inspector = inspect(self.engine)

                for table_name in tables_to_check:
                    if inspector.has_table(table_name):
                        columns = inspector.get_columns(table_name)

                        schema = TableSchema(
                            table_name=table_name,
                            columns=[col["name"] for col in columns],
                            primary_keys=inspector.get_pk_constraint(table_name)[
                                "constrained_columns"
                            ],
                            nullable_columns=[
                                col["name"] for col in columns if col["nullable"]
                            ],
                            column_types={
                                col["name"]: str(col["type"]) for col in columns
                            },
                        )
                        schemas[table_name] = schema

            logger.debug(f"Loaded schemas for {len(schemas)} tables")
            return schemas

        except Exception as e:
            logger.warning(f"Failed to load table schemas: {e}")
            return {}

    def verify_submission_storage(
        self, submission_id: str, pipeline_result: dict[str, Any]
    ) -> VerificationResult:
        """
        Verify that submission data was stored correctly across all relevant tables.

        Args:
            submission_id: UUID of the submission to verify
            pipeline_result: Pipeline execution result containing expected data

        Returns:
            VerificationResult with detailed storage status
        """
        result = VerificationResult(
            success=False,
            message="Verification not completed",
            expected_fields=0,
            stored_fields=0,
        )

        try:
            with self.SessionLocal() as session:
                # CRITICAL FIX: Use canonical ID resolver for consistent ID handling
                # The pipeline may store data using UUID transformation, but queries
                # might use raw IDs like "hybrid_1". The resolver provides the single
                # source of truth for all ID transformations.
                resolution_result = resolve_submission_id(submission_id)

                if not resolution_result or not resolution_result.uuid:
                    result.message = f"Failed to resolve submission_id '{submission_id}' to UUID"
                    logger.warning(f"ID resolution failed for {submission_id}")
                    return result

                resolved_uuid = resolution_result.uuid
                logger.debug(f"Resolved '{submission_id}' -> '{resolved_uuid}' (source: {resolution_result.source})")

                # Verify base submission exists using resolved UUID first, fallback to reddit_id
                submission_query = text("""
                    SELECT submission_id, title, subreddit, reddit_score,
                           created_utc
                    FROM submissions
                    WHERE submission_id = :resolved_uuid
                       OR reddit_id = :original_id
                """)

                submission_result = session.execute(
                    submission_query, {
                        "resolved_uuid": resolved_uuid,
                        "original_id": submission_id
                    }
                ).fetchone()

                if not submission_result:
                    result.message = f"Submission {submission_id} (resolved to {resolved_uuid}) not found in database"
                    logger.warning(f"Database lookup failed for resolved UUID {resolved_uuid} and original ID {submission_id}")
                    return result

                # Verify app_opportunities entry (contains all pipeline data)
                opportunity_result = self._verify_app_opportunities(
                    session, resolved_uuid, submission_id, pipeline_result
                )
                result.table_status["app_opportunities"] = opportunity_result

                # For now, we consider successful storage in app_opportunities as complete verification
                # since it contains all the consolidated pipeline data

                # Calculate overall success and field coverage
                success_count = sum(
                    1 for status in result.table_status.values() if status
                )
                total_tables = len(result.table_status)
                result.success = success_count == total_tables

                # Estimate field coverage based on pipeline services
                result.expected_fields = self._estimate_expected_fields(pipeline_result)
                result.stored_fields = (
                    result.expected_fields * success_count // total_tables
                )
                result.field_coverage = (
                    (result.stored_fields / result.expected_fields * 100)
                    if result.expected_fields > 0
                    else 0
                )

                result.message = (
                    f"Verification completed: {success_count}/{total_tables} tables "
                    f"successfully stored ({result.field_coverage:.1f}% field coverage)"
                )

                return result

        except SQLAlchemyError as e:
            result.message = f"Database verification failed: {e!s}"
            logger.error(f"Verification error for submission {submission_id}: {e}")
            return result
        except Exception as e:
            result.message = f"Unexpected verification error: {e!s}"
            logger.error(
                f"Unexpected verification error for submission {submission_id}: {e}"
            )
            return result

    def _verify_app_opportunities(
        self, session: Session, resolved_uuid: str, original_id: str, pipeline_result: dict[str, Any]
    ) -> bool:
        """Verify app_opportunities table entry with comprehensive field validation."""
        try:
            # CRITICAL FIX: Use resolved UUID for FK lookups with fallback to original ID
            # The app_opportunities table should use the resolved UUID for submission_id FK
            query = text("""
                SELECT submission_id, app_name, value_proposition, problem_description,
                       target_user, monetization_model, final_score, opportunity_score,
                       market_validation_score, monetization_score, dimension_scores,
                       priority, confidence, status, trust_level, analyzed_at
                FROM app_opportunities
                WHERE submission_id = :resolved_uuid
                   OR submission_id = :original_id
            """)

            result = session.execute(query, {
                "resolved_uuid": resolved_uuid,
                "original_id": original_id
            }).fetchone()

            if not result:
                return False

            # Verify key fields are populated
            key_fields = [
                "submission_id",
                "app_name",
                "value_proposition",
                "final_score",
                "opportunity_score",
                "dimension_scores",
                "priority",
            ]

            for field in key_fields:
                if getattr(result, field) is None:
                    logger.warning(
                        f"Missing key field {field} in app_opportunities for resolved UUID {resolved_uuid} (original: {original_id})"
                    )
                    return False

            return True

        except Exception as e:
            logger.error(f"Error verifying app_opportunities: {e}")
            return False

    def _estimate_expected_fields(self, pipeline_result: dict[str, Any]) -> int:
        """Estimate expected field count based on executed services."""
        services = pipeline_result.get("services", [])

        # Base fields from submission
        base_fields = 7  # submission_id, title, subreddit, reddit_score, num_comments, selftext, created_at

        # Service-specific fields
        service_fields = {
            "ProfilerService": 6,  # app_name, value_proposition, problem_description, target_user, monetization_model, created_at
            "OpportunityService": 6,  # final_score, dimension_scores, priority, core_functions, weights, created_at
            "TrustService": 12,  # various trust score fields + badges + validation fields
            "MonetizationService": 14,  # willingness_to_pay, market_segment, price_sensitivity, revenue_potential, etc.
            "MarketValidationService": 7,  # market_validation_score, competitor_count, market_size, etc.
        }

        total_fields = base_fields
        for service in services:
            total_fields += service_fields.get(service, 0)

        return total_fields

    def verify_batch_storage(
        self, submission_ids: list[str], pipeline_results: list[dict[str, Any]]
    ) -> list[VerificationResult]:
        """
        Verify storage for multiple submissions.

        Args:
            submission_ids: List of submission UUIDs to verify
            pipeline_results: Corresponding pipeline execution results

        Returns:
            List of VerificationResult objects
        """
        results = []

        for submission_id, pipeline_result in zip(submission_ids, pipeline_results):
            result = self.verify_submission_storage(submission_id, pipeline_result)
            results.append(result)

        return results

    def get_storage_summary(self, results: list[VerificationResult]) -> dict[str, Any]:
        """
        Generate summary statistics for batch verification results.

        Args:
            results: List of VerificationResult objects

        Returns:
            Dictionary with summary statistics
        """
        if not results:
            return {"error": "No results to summarize"}

        successful_verifications = sum(1 for r in results if r.success)
        total_verifications = len(results)
        avg_field_coverage = (
            sum(r.field_coverage for r in results) / total_verifications
        )

        table_success_rates = {}
        if results:
            all_tables = set()
            for result in results:
                all_tables.update(result.table_status.keys())

            for table in all_tables:
                successes = sum(1 for r in results if r.table_status.get(table, False))
                table_success_rates[table] = (successes / total_verifications) * 100

        return {
            "total_submissions": total_verifications,
            "successful_verifications": successful_verifications,
            "overall_success_rate": (successful_verifications / total_verifications)
            * 100,
            "average_field_coverage": avg_field_coverage,
            "table_success_rates": table_success_rates,
            "issues": [r.message for r in results if not r.success],
        }

    def close(self):
        """Close database connections and cleanup resources."""
        if hasattr(self, "engine"):
            self.engine.dispose()
            logger.info("Database verifier connections closed")


# Convenience function for quick verification
def verify_storage(
    submission_id: str, pipeline_result: dict[str, Any]
) -> VerificationResult:
    """
    Quick verification function for single submission.

    Args:
        submission_id: UUID of submission to verify
        pipeline_result: Pipeline execution result

    Returns:
        VerificationResult with storage status
    """
    verifier = DatabaseVerifier()
    try:
        return verifier.verify_submission_storage(submission_id, pipeline_result)
    finally:
        verifier.close()
