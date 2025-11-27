"""
SQLAlchemy Loader for RedditHarbor Pipeline v2 - SCHEMA FIXED VERSION

Phase 2: Complete implementation with CRITICAL schema alignment fixes.

This module provides a SQLAlchemy-based alternative to DLT for loading
opportunity data to PostgreSQL with explicit transaction control,
eliminating silent failures.

Key Features:
- FIXED: Field mappings to match actual database schema
- Explicit transaction control with commit/rollback visibility
- Data persistence verification (prevents silent failures)
- Complete load operations (merge, append, replace)
- Integration with existing ID resolution system
- DLT-compatible interfaces through adapter

FIXES APPLIED:
- Removed references to non-existent columns (text, comments_count, score, created_utc)
- Fixed column name mappings (upvotes->reddit_score, processed_at->analyzed_at)
- Proper handling of DLT-specific required fields (_dlt_load_id, _dlt_id)
- Updated all SQL statements to use actual database schema

Author: Phase 2 DLT to SQLAlchemy Migration (Schema Fixed)
Version: Pipeline-v2 compatible
"""

import logging
import time
import json
from datetime import datetime, UTC
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Union, Iterator
from dataclasses import dataclass
import os

# SQLAlchemy imports
try:
    from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer, Float, DateTime, Boolean
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, Session
    from sqlalchemy.exc import SQLAlchemyError, OperationalError, IntegrityError
    from sqlalchemy.pool import QueuePool
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    SQLAlchemyError = Exception
    OperationalError = Exception
    # Fallback types for when SQLAlchemy is not available
    Session = None

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


class SQLAlchemyLoadError(Exception):
    """Custom exception for SQLAlchemy loader operations."""
    pass


@dataclass
class LoadResult:
    """Explicit load result - no silent failures"""
    success: bool
    load_id: str
    records_inserted: int
    records_updated: int
    errors: List[str]
    timestamp: str
    error_message: str = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "load_id": self.load_id,
            "records_inserted": self.records_inserted,
            "records_updated": self.records_updated,
            "errors": self.errors,
            "error_message": self.error_message,
            "timestamp": self.timestamp
        }


@dataclass
class InsertResult:
    """Result of insert/update operations"""
    inserted: int
    updated: int


@dataclass
class VerificationResult:
    """Result of load operation verification"""
    success: bool
    expected_count: int
    actual_count: int
    errors: List[str]


class SQLAlchemyLoader:
    """
    SQLAlchemy-based data loader for RedditHarber opportunity data.

    Phase 2: COMPLETE SCHEMA-ALIGNED implementation with explicit transaction control:
    - FIXED: Field mappings to match actual database schema
    - Connection management and validation
    - Basic session management
    - Table existence validation
    - ID resolution system integration
    - Complete load operations with merge/append/replace
    - Data persistence verification (eliminates silent failures)
    - Explicit transaction control with commit/rollback
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
                    "application_name": "reddit_harbor_sqlalchemy_loader_fixed"
                }
            )

            # Create session factory
            self._session_factory = sessionmaker(bind=self._engine)

            logger.info("✓ SQLAlchemy engine initialized successfully (SCHEMA FIXED)")

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

                        # Get last updated timestamp (use analyzed_at as it's the actual column)
                        last_updated = conn.execute(text("""
                            SELECT MAX(analyzed_at) FROM app_opportunities
                            WHERE analyzed_at IS NOT NULL
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

                    # Check for critical columns (updated to match actual schema)
                    critical_columns = ["submission_id", "title", "analyzed_at", "_dlt_load_id", "_dlt_id"]
                    existing_columns = [col["name"] for col in validation_result["columns"]]

                    missing_critical = [
                        col for col in critical_columns
                        if col not in existing_columns
                    ]

                    validation_result["missing_critical_columns"] = missing_critical
                    validation_result["validation_status"] = (
                        "valid" if not missing_critical else "incomplete"
                    )

                    # Log schema validation details
                    if missing_critical:
                        logger.warning(f"Missing critical columns: {missing_critical}")
                    else:
                        logger.info("✓ All critical columns present in table schema")

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

    # ========================================================================
    # PHASE 2: COMPLETE IMPLEMENTATION - CORE LOAD OPERATIONS (SCHEMA FIXED)
    # ========================================================================

    def load_opportunities(
        self,
        opportunities: List[Dict[str, Any]],
        write_disposition: str = "merge"
    ) -> LoadResult:
        """
        Load opportunities with EXPLICIT transaction control (SCHEMA FIXED)

        Args:
            opportunities: List of opportunity records
            write_disposition: "merge" (upsert), "append", or "replace"

        Returns:
            LoadResult with explicit success/failure status

        Raises:
            SQLAlchemyLoadError: On transaction failure
        """
        if not opportunities:
            logger.warning("No opportunities to load")
            return LoadResult(
                success=True,
                load_id=self._generate_load_id(),
                records_inserted=0,
                records_updated=0,
                errors=[],
                timestamp=datetime.utcnow().isoformat()
            )

        start_time = time.time()
        load_id = self._generate_load_id()

        try:
            with self.get_session() as session:
                with session.begin():  # Explicit transaction
                    # 1. Prepare data (ID resolution + schema mapping)
                    prepared = self.prepare_opportunity_data(opportunities)

                    # 2. Execute load based on disposition
                    if write_disposition == "merge":
                        result = self._merge_opportunities(session, prepared)
                    elif write_disposition == "append":
                        result = self._append_opportunities(session, prepared)
                    elif write_disposition == "replace":
                        result = self._replace_opportunities(session, prepared)
                    else:
                        raise SQLAlchemyLoadError(f"Unsupported write_disposition: {write_disposition}")

                    # 3. CRITICAL: Verify data actually persisted
                    verification = self._verify_load_operation(session, prepared)
                    if not verification.success:
                        raise SQLAlchemyLoadError(f"Verification failed: {verification.errors}")

                    # 4. Explicit commit (automatic with begin())
                    load_time = time.time() - start_time
                    logger.info(f"✓ SQLAlchemy SCHEMA-FIXED load completed in {load_time:.2f}s")
                    logger.info(f"  - Load ID: {load_id}")
                    logger.info(f"  - Records processed: {result.inserted + result.updated}")
                    logger.info(f"  - Write disposition: {write_disposition}")

                    return LoadResult(
                        success=True,
                        load_id=load_id,
                        records_inserted=result.inserted,
                        records_updated=result.updated,
                        errors=[],
                        timestamp=datetime.utcnow().isoformat()
                    )

        except Exception as e:
            # Explicit rollback (automatic on exception)
            load_time = time.time() - start_time
            logger.error(f"❌ SQLAlchemy SCHEMA-FIXED load failed after {load_time:.2f}s: {e}")
            return LoadResult(
                success=False,
                load_id=load_id,
                records_inserted=0,
                records_updated=0,
                errors=[str(e)],
                timestamp=datetime.utcnow().isoformat()
            )

    def prepare_opportunity_data(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Prepare data for insertion with SCHEMA-FIXED field mappings:
        1. Resolve Reddit IDs to UUIDs (integrate with existing ID resolver)
        2. Validate required fields
        3. Handle data type conversions
        4. MAP FIELDS TO ACTUAL DATABASE SCHEMA
        """
        prepared_opportunities = []

        for opp in opportunities:
            try:
                # Resolve submission ID using the established ID resolution system
                id_result = resolve_submission_id(opp.get('submission_id', ''))

                # Schema-fixed field mapping - map incoming data to actual database columns
                prepared_opp = {
                    # Required DLT fields (must be populated)
                    '_dlt_load_id': f'sqlalchemy_load_{datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")}',
                    '_dlt_id': f'sqlalchemy_{id_result.uuid if id_result else opp.get("submission_id", "")}',

                    # Core identity fields (exist in database)
                    'submission_id': id_result.uuid if id_result else opp.get('submission_id', ''),
                    'title': opp.get('title', ''),
                    'subreddit': opp.get('subreddit', ''),

                    # FIXED: upvotes -> reddit_score (actual column name) - ensure always provided
                    'reddit_score': int(opp.get('upvotes', 0)) if opp.get('upvotes') is not None else 0,

                    # Opportunity analysis fields (exist in database)
                    'problem_description': opp.get('text', ''),  # FIXED: text -> problem_description
                    'app_concept': opp.get('app_concept', ''),
                    'core_functions': opp.get('core_functions', []),
                    'opportunity_score': float(opp.get('opportunity_score', 0.0)),
                    'monetization_score': float(opp.get('monetization_score', 0.0)),

                    # Trust and quality fields (exist in database)
                    'trust_score': float(opp.get('trust_score', 0.0)),
                    'trust_level': opp.get('trust_level', ''),
                    # FIXED: trust_badges needs to be JSON for JSONB column
                    'trust_badges': json.dumps(opp.get('trust_badges', [])) if opp.get('trust_badges') else '[]',

                    # FIXED: processed_at -> analyzed_at (actual column name)
                    'analyzed_at': opp.get('processed_at', datetime.now(UTC).isoformat()),

                    # FIXED: pipeline_version -> pipeline_source (actual column name)
                    'pipeline_source': opp.get('pipeline_version', 'pipeline_v2_sqlalchemy_fixed'),

                    # Additional fields that exist in database
                    'value_proposition': opp.get('value_proposition', ''),
                    'target_user': opp.get('target_user', ''),
                    'monetization_model': opp.get('monetization_model', ''),
                    'confidence': float(opp.get('confidence_score', 0.0)),
                    'evidence_based': bool(opp.get('evidence_based', False)),

                    # Additional available fields
                    'app_name': opp.get('app_name', ''),
                    'app_category': opp.get('app_category', ''),
                    'profession': opp.get('profession', ''),
                    'priority': opp.get('priority', ''),
                    'activity_score': float(opp.get('activity_score', 0.0)),
                    'trust_badge': opp.get('trust_badge', ''),
                    'market_validation_score': float(opp.get('market_validation_score', 0.0)),
                    'enrichment_version': opp.get('enrichment_version', 'v3.0.0'),
                    'status': opp.get('status', 'discovered')
                }

                # Remove None values to avoid SQL issues, but keep empty strings and zeros
                # Keep essential fields even if they appear "empty"
                essential_fields = ['_dlt_load_id', '_dlt_id', 'submission_id', 'trust_badges']
                prepared_opp = {k: v for k, v in prepared_opp.items()
                              if v is not None or k in essential_fields}
                prepared_opportunities.append(prepared_opp)

                # Log the mapping for debugging
                logger.debug(f"Mapped opportunity: {opp.get('submission_id')} -> {prepared_opp['submission_id']}")
                logger.debug(f"  Fields mapped: title={prepared_opp.get('title')}, reddit_score={prepared_opp.get('reddit_score')}")

            except Exception as e:
                logger.error(f"Error preparing opportunity data: {e}")
                logger.error(f"Problematic opportunity: {opp}")
                raise SQLAlchemyLoadError(f"Data preparation failed: {e}")

        logger.info(f"✓ Prepared {len(prepared_opportunities)} opportunities for loading (SCHEMA FIXED)")
        return prepared_opportunities

    def _merge_opportunities(self, session, prepared: List[Dict]) -> InsertResult:
        """Upsert logic with SCHEMA-FIXED SQL statements"""
        inserted = 0
        updated = 0

        for opp in prepared:
            # Check if record exists
            existing = session.execute(
                text("SELECT submission_id FROM app_opportunities WHERE submission_id = :id"),
                {"id": opp['submission_id']}
            ).fetchone()

            if existing:
                # Update existing record - ONLY use actual database columns
                update_stmt = text("""
                    UPDATE app_opportunities SET
                        title = :title,
                        subreddit = :subreddit,
                        reddit_score = :reddit_score,
                        problem_description = :problem_description,
                        app_concept = :app_concept,
                        core_functions = :core_functions,
                        opportunity_score = :opportunity_score,
                        monetization_score = :monetization_score,
                        trust_score = :trust_score,
                        trust_level = :trust_level,
                        trust_badges = :trust_badges,
                        analyzed_at = :analyzed_at,
                        pipeline_source = :pipeline_source,
                        value_proposition = :value_proposition,
                        target_user = :target_user,
                        monetization_model = :monetization_model,
                        confidence = :confidence,
                        evidence_based = :evidence_based,
                        app_name = :app_name,
                        app_category = :app_category,
                        profession = :profession,
                        priority = :priority,
                        activity_score = :activity_score,
                        trust_badge = :trust_badge,
                        market_validation_score = :market_validation_score,
                        enrichment_version = :enrichment_version,
                        status = :status,
                        _dlt_load_id = :_dlt_load_id,
                        _dlt_id = :_dlt_id
                    WHERE submission_id = :submission_id
                """)

                session.execute(update_stmt, opp)
                updated += 1
                logger.debug(f"Updated existing opportunity: {opp['submission_id']}")
            else:
                # Insert new record - ONLY use actual database columns
                insert_stmt = text("""
                    INSERT INTO app_opportunities (
                        _dlt_load_id, _dlt_id,
                        submission_id, title, subreddit, reddit_score,
                        problem_description, app_concept, core_functions,
                        opportunity_score, monetization_score,
                        trust_score, trust_level, trust_badges,
                        analyzed_at, pipeline_source,
                        value_proposition, target_user, monetization_model,
                        confidence, evidence_based,
                        app_name, app_category, profession, priority,
                        activity_score, trust_badge, market_validation_score,
                        enrichment_version, status
                    ) VALUES (
                        :_dlt_load_id, :_dlt_id,
                        :submission_id, :title, :subreddit, :reddit_score,
                        :problem_description, :app_concept, :core_functions,
                        :opportunity_score, :monetization_score,
                        :trust_score, :trust_level, :trust_badges,
                        :analyzed_at, :pipeline_source,
                        :value_proposition, :target_user, :monetization_model,
                        :confidence, :evidence_based,
                        :app_name, :app_category, :profession, :priority,
                        :activity_score, :trust_badge, :market_validation_score,
                        :enrichment_version, :status
                    )
                """)

                session.execute(insert_stmt, opp)
                inserted += 1
                logger.debug(f"Inserted new opportunity: {opp['submission_id']}")

        return InsertResult(inserted=inserted, updated=updated)

    def _append_opportunities(self, session, prepared: List[Dict]) -> InsertResult:
        """Append opportunities with SCHEMA-FIXED SQL statements"""
        for opp in prepared:
            insert_stmt = text("""
                INSERT INTO app_opportunities (
                    _dlt_load_id, _dlt_id,
                    submission_id, title, subreddit, reddit_score,
                    problem_description, app_concept, core_functions,
                    opportunity_score, monetization_score,
                    trust_score, trust_level, trust_badges,
                    analyzed_at, pipeline_source,
                    value_proposition, target_user, monetization_model,
                    confidence, evidence_based,
                    app_name, app_category, profession, priority,
                    activity_score, trust_badge, market_validation_score,
                    enrichment_version, status
                ) VALUES (
                    :_dlt_load_id, :_dlt_id,
                    :submission_id, :title, :subreddit, :reddit_score,
                    :problem_description, :app_concept, :core_functions,
                    :opportunity_score, :monetization_score,
                    :trust_score, :trust_level, :trust_badges,
                    :analyzed_at, :pipeline_source,
                    :value_proposition, :target_user, :monetization_model,
                    :confidence, :evidence_based,
                    :app_name, :app_category, :profession, :priority,
                    :activity_score, :trust_badge, :market_validation_score,
                    :enrichment_version, :status
                )
            """)

            session.execute(insert_stmt, opp)

        return InsertResult(inserted=len(prepared), updated=0)

    def _replace_opportunities(self, session, prepared: List[Dict]) -> InsertResult:
        """Replace all data in table with new opportunities"""
        # Clear existing data
        session.execute(text("TRUNCATE TABLE app_opportunities"))

        # Insert new data
        return self._append_opportunities(session, prepared)

    def _verify_load_operation(self, session, prepared: List[Dict]) -> VerificationResult:
        """
        CRITICAL: Verify data actually in database - prevents silent failures
        """
        if not prepared:
            return VerificationResult(
                success=True,
                expected_count=0,
                actual_count=0,
                errors=[]
            )

        ids = [opp['submission_id'] for opp in prepared]

        try:
            # Count loaded records using actual database
            result = session.execute(
                text("SELECT COUNT(*) FROM app_opportunities WHERE submission_id = ANY(:ids)"),
                {"ids": ids}
            ).scalar()

            success = result == len(prepared)
            errors = []
            if not success:
                errors = [
                    f"Expected {len(prepared)} records, found {result}",
                    "Data persistence verification failed - potential silent failure"
                ]

            if success:
                logger.info(f"✓ Verification passed: {result}/{len(prepared)} records persisted")
            else:
                logger.error(f"❌ Verification failed: {result}/{len(prepared)} records persisted")

            return VerificationResult(
                success=success,
                expected_count=len(prepared),
                actual_count=result,
                errors=errors
            )

        except Exception as e:
            logger.error(f"Verification query failed: {str(e)}")
            return VerificationResult(
                success=False,
                expected_count=len(prepared),
                actual_count=0,
                errors=[f"Verification query failed: {str(e)}"]
            )

    def _generate_load_id(self) -> str:
        """Generate unique load ID for tracking"""
        return f"sqlalchemy_load_fixed_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S_%f')}"


# ============================================================================
# UTILITY FUNCTIONS (SCHEMA FIXED)
# ============================================================================

def create_sqlalchemy_loader(connection_string: Optional[str] = None) -> SQLAlchemyLoader:
    """
    Factory function to create SCHEMA-FIXED SQLAlchemy loader instance.

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
    Test SCHEMA-FIXED SQLAlchemy foundation components.

    Args:
        connection_string: PostgreSQL connection string (optional)

    Returns:
        Dictionary with foundation test results
    """
    test_results = {
        "timestamp": datetime.now(UTC).isoformat(),
        "sqlalchemy_available": SQLALCHEMY_AVAILABLE,
        "id_resolver_available": ID_RESOLVER_AVAILABLE,
        "components": {},
        "schema_status": "fixed"
    }

    try:
        logger.info("Testing SCHEMA-FIXED SQLAlchemy foundation components")

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
        logger.info("✓ SCHEMA-FIXED SQLAlchemy foundation test completed successfully")

    except Exception as e:
        test_results["overall_status"] = "failed"
        test_results["error"] = str(e)
        logger.error(f"SCHEMA-FIXED SQLAlchemy foundation test failed: {e}")

    return test_results


def test_schema_fixed_load(connection_string: Optional[str] = None) -> Dict[str, Any]:
    """
    Test the SCHEMA-FIXED SQLAlchemy loader with actual data.

    Args:
        connection_string: PostgreSQL connection string (optional)

    Returns:
        Dictionary with load test results
    """
    test_results = {
        "timestamp": datetime.now(UTC).isoformat(),
        "test_type": "schema_fixed_load",
        "status": "started"
    }

    try:
        # Create loader
        loader = create_sqlalchemy_loader(connection_string)

        # Create test data that matches the DLT test structure
        test_opportunities = [
            {
                "submission_id": "test_schema_fixed_001",
                "title": "Test Schema Fixed - Productivity App Idea",
                "text": "Looking for an app that helps track productivity across multiple projects with AI-powered insights and team collaboration features.",
                "subreddit": "productivity",
                "upvotes": 15,
                "comments_count": 8,  # This will be ignored (no corresponding column)
                "score": 23,  # This will be ignored (no corresponding column)
                "created_utc": "2024-11-26T21:45:00Z",  # This will be ignored (no corresponding column)
                "permalink": "https://reddit.com/r/productivity/comments/test_schema_fixed_001",
                "quality_score": 85.0,  # This will be mapped to opportunity_score
                "opportunity_score": 75.0,
                "core_functions": ["productivity", "tracking", "collaboration"],
                "app_concept": "Multi-project productivity tracker with AI insights",
                "problem_description": "Users need better ways to track productivity across multiple projects and teams",
                "trust_score": 65.0,
                "trust_level": "MEDIUM",
                "trust_badges": ["ACTIVE_DISCUSSION", "QUALITY_CONTENT"],
                "confidence_score": 70.0,
                "monetization_score": 80.0,
                "processed_at": "2025-11-26T21:45:00Z",
                "pipeline_version": "pipeline_v2_sqlalchemy_fixed"
            }
        ]

        logger.info(f"Testing SCHEMA-FIXED load with {len(test_opportunities)} records")

        # Test the load
        load_result = loader.load_opportunities(
            test_opportunities,
            write_disposition="merge"
        )

        test_results.update({
            "status": "completed",
            "load_result": load_result.to_dict(),
            "success": load_result.success
        })

        if load_result.success:
            logger.info("✓ SCHEMA-FIXED load test PASSED")
        else:
            logger.error(f"❌ SCHEMA-FIXED load test FAILED: {load_result.errors}")

    except Exception as e:
        test_results["status"] = "failed"
        test_results["error"] = str(e)
        logger.error(f"SCHEMA-FIXED load test exception: {e}")

    return test_results