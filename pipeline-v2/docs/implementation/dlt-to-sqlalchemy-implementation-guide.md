# DLT to SQLAlchemy Migration - Technical Implementation Guide

## Overview

This guide provides detailed technical specifications for migrating RedditHarbor's data loading layer from DLT to SQLAlchemy, addressing critical silent failure issues and implementing robust transaction management.

## Migration Architecture

### Current State Analysis

**DLT Implementation Issues:**
```python
# Current problematic pattern in pipeline-v2/storage/dlt_loader.py
class DLTLoader:
    def load_opportunities(self, opportunities, **kwargs):
        load_info = pipeline.run(opportunities, **kwargs)
        # Returns success but may have rolled back silently
        return load_info
```

**Target SQLAlchemy Implementation:**
```python
# Proposed replacement pattern
class SQLAlchemyLoader:
    def load_opportunities(self, opportunities, **kwargs):
        with Session(self.engine) as session:
            transaction = session.begin()
            try:
                records = self._prepare_data(opportunities)
                session.add_all(records)
                session.flush()  # Execute but don't commit yet
                count = session.execute(text("SELECT COUNT(*) FROM app_opportunities WHERE submission_id IN :ids"),
                                      {"ids": [r.submission_id for r in records]}).scalar()
                assert count == len(records), f"Insertion verification failed: expected {len(records)}, got {count}"
                transaction.commit()
                return LoadResult(success=True, records_inserted=len(records))
            except Exception as e:
                transaction.rollback()
                logger.error(f"SQLAlchemy load failed: {e}")
                raise LoadError(f"Failed to load opportunities: {e}")
```

## Phase 1: Foundation Implementation

### 1.1 SQLAlchemy Loader Core

**File: `pipeline-v2/storage/sqlalchemy_loader.py`**
```python
"""
SQLAlchemy-based data loader for RedditHarbor Pipeline v2

Replaces DLT to provide explicit transaction control and eliminate silent failures.
"""

import logging
import time
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

# SQLAlchemy imports
from sqlalchemy import create_engine, text, select, update, insert
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.pool import QueuePool

# Project imports
from core.utils.id_resolver import resolve_submission_id, ResolutionResult

logger = logging.getLogger(__name__)

class SQLAlchemyLoadError(Exception):
    """Custom exception for SQLAlchemy loader operations."""
    pass

class LoadResult:
    """Structured result for load operations."""
    def __init__(self, success: bool, records_inserted: int = 0, records_updated: int = 0,
                 load_id: str = None, error_message: str = None):
        self.success = success
        self.records_inserted = records_inserted
        self.records_updated = records_updated
        self.load_id = load_id or f"load_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        self.error_message = error_message
        self.load_timestamp = datetime.now(UTC).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "load_id": self.load_id,
            "success": self.success,
            "records_inserted": self.records_inserted,
            "records_updated": self.records_updated,
            "load_timestamp": self.load_timestamp,
            "error_message": self.error_message
        }

class SQLAlchemyLoader:
    """
    PostgreSQL loader using SQLAlchemy with explicit transaction control.

    Provides reliable data loading with immediate success/failure feedback,
    eliminating the silent failure issues experienced with DLT.
    """

    def __init__(
        self,
        connection_string: str,
        pool_size: int = 10,
        max_overflow: int = 20,
        echo: bool = False,
        isolation_level: str = "READ_COMMITTED"
    ):
        """
        Initialize SQLAlchemy loader with database connection.

        Args:
            connection_string: PostgreSQL connection string
            pool_size: Base connection pool size
            max_overflow: Maximum additional connections
            echo: Enable SQLAlchemy query logging
            isolation_level: Transaction isolation level
        """
        self.connection_string = connection_string
        self.engine = None
        self.session_factory = None

        self._create_engine(pool_size, max_overflow, echo, isolation_level)
        self._validate_connection()

    def _create_engine(self, pool_size: int, max_overflow: int, echo: bool, isolation_level: str):
        """Create SQLAlchemy engine with optimized settings."""
        try:
            self.engine = create_engine(
                self.connection_string,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=True,  # Validate connections before use
                pool_recycle=3600,   # Recycle connections after 1 hour
                echo=echo,
                isolation_level=isolation_level,
                connect_args={
                    "application_name": "redditharbor_pipeline_v2",
                    "connect_timeout": 30,
                    "command_timeout": 300
                }
            )

            self.session_factory = sessionmaker(bind=self.engine)
            logger.info("✓ SQLAlchemy engine created successfully")

        except Exception as e:
            logger.error(f"Failed to create SQLAlchemy engine: {e}")
            raise SQLAlchemyLoadError(f"Engine creation failed: {e}")

    def _validate_connection(self):
        """Validate database connection and table existence."""
        try:
            with self.engine.connect() as conn:
                # Test basic connectivity
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                logger.info(f"✓ Database connection validated: {version.split(',')[0]}")

                # Verify target table exists
                table_check = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'app_opportunities'
                    )
                """)).scalar()

                if not table_check:
                    raise SQLAlchemyLoadError("Target table 'app_opportunities' does not exist")

                logger.info("✓ Target table validated")

        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            raise SQLAlchemyLoadError(f"Connection validation failed: {e}")

    @contextmanager
    def get_session(self):
        """Context manager for database sessions with automatic cleanup."""
        session = self.session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def prepare_opportunity_data(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prepare opportunity data for SQLAlchemy insertion.

        Args:
            opportunities: Raw opportunity data from processing pipeline

        Returns:
            List of prepared opportunity records with resolved IDs
        """
        prepared_opportunities = []

        for opp in opportunities:
            try:
                # Resolve submission ID using the established ID resolution system
                id_result = resolve_submission_id(opp.get('submission_id', ''))

                # Ensure created_utc is properly formatted
                created_utc = opp.get('created_utc')
                if isinstance(created_utc, (int, float)):
                    created_utc = datetime.fromtimestamp(created_utc, UTC).isoformat()
                elif created_utc and not isinstance(created_utc, str):
                    created_utc = str(created_utc)

                # Map fields to database schema
                prepared_opp = {
                    'submission_id': id_result.uuid,  # Use resolved UUID
                    'title': opp.get('title', ''),
                    'text': opp.get('text', ''),
                    'subreddit': opp.get('subreddit', ''),
                    'upvotes': int(opp.get('upvotes', 0)),
                    'comments_count': int(opp.get('comments_count', 0)),
                    'score': float(opp.get('score', 0.0)),
                    'created_utc': created_utc,
                    'permalink': opp.get('permalink', ''),
                    'quality_score': float(opp.get('quality_score', 0.0)),
                    'trust_score': float(opp.get('trust_score', 0.0)),
                    'opportunity_score': float(opp.get('opportunity_score', 0.0)),
                    'confidence_score': float(opp.get('confidence_score', 0.0)),
                    'monetization_score': float(opp.get('monetization_score', 0.0)),
                    'willingness_to_pay_score': float(opp.get('willingness_to_pay_score', 0.0)),
                    'customer_segment': opp.get('customer_segment', ''),
                    'core_functions': opp.get('core_functions', []),
                    'app_concept': opp.get('app_concept', ''),
                    'problem_description': opp.get('problem_description', ''),
                    'trust_level': opp.get('trust_level', ''),
                    'trust_badges': opp.get('trust_badges', []),
                    'processed_at': opp.get('processed_at', datetime.now(UTC).isoformat()),
                    'pipeline_version': opp.get('pipeline_version', 'pipeline_v2_sqlalchemy')
                }

                # Remove None values
                prepared_opp = {k: v for k, v in prepared_opp.items() if v is not None}
                prepared_opportunities.append(prepared_opp)

            except Exception as e:
                logger.error(f"Error preparing opportunity data: {e}")
                logger.error(f"Problematic opportunity: {opp}")
                raise SQLAlchemyLoadError(f"Data preparation failed: {e}")

        logger.info(f"Prepared {len(prepared_opportunities)} opportunities for loading")
        return prepared_opportunities

    def load_opportunities(
        self,
        opportunities: List[Dict[str, Any]],
        table_name: str = "app_opportunities",
        write_disposition: str = "merge",
        primary_key: str = "submission_id"
    ) -> LoadResult:
        """
        Load opportunity data to PostgreSQL with explicit transaction control.

        Args:
            opportunities: List of opportunity records to load
            table_name: Target table name
            write_disposition: Write disposition ('append', 'replace', 'merge')
            primary_key: Primary key column for merge operations

        Returns:
            LoadResult with detailed success/failure information
        """
        if not opportunities:
            logger.warning("No opportunities to load")
            return LoadResult(success=True, records_inserted=0, records_updated=0)

        start_time = time.time()
        load_id = f"sqlalchemy_load_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"

        try:
            # Prepare data
            prepared_opportunities = self.prepare_opportunity_data(opportunities)

            with self.get_session() as session:
                with session.begin():
                    if write_disposition == "merge":
                        result = self._merge_opportunities(session, prepared_opportunities, primary_key)
                    elif write_disposition == "append":
                        result = self._append_opportunities(session, prepared_opportunities)
                    elif write_disposition == "replace":
                        result = self._replace_opportunities(session, prepared_opportunities, table_name)
                    else:
                        raise SQLAlchemyLoadError(f"Unsupported write_disposition: {write_disposition}")

                    # Verify operation success
                    verification_count = self._verify_load_operation(session, prepared_opportunities, primary_key)
                    if verification_count != len(prepared_opportunities):
                        raise SQLAlchemyLoadError(
                            f"Load verification failed: expected {len(prepared_opportunities)} records, found {verification_count}"
                        )

                    # Transaction commits automatically on success

                load_time = time.time() - start_time
                logger.info(f"✓ SQLAlchemy load completed in {load_time:.2f}s")
                logger.info(f"  - Load ID: {load_id}")
                logger.info(f"  - Records processed: {result['inserted'] + result['updated']}")
                logger.info(f"  - Table: {table_name}")
                logger.info(f"  - Write disposition: {write_disposition}")

                return LoadResult(
                    success=True,
                    records_inserted=result['inserted'],
                    records_updated=result['updated'],
                    load_id=load_id
                )

        except Exception as e:
            load_time = time.time() - start_time
            logger.error(f"❌ SQLAlchemy load failed after {load_time:.2f}s: {e}")
            return LoadResult(
                success=False,
                load_id=load_id,
                error_message=str(e)
            )

    def _merge_opportunities(self, session: Session, opportunities: List[Dict], primary_key: str) -> Dict[str, int]:
        """Merge opportunities using upsert logic."""
        inserted = 0
        updated = 0

        for opp in opportunities:
            # Check if record exists
            existing = session.execute(
                text(f"SELECT {primary_key} FROM app_opportunities WHERE {primary_key} = :id"),
                {"id": opp[primary_key]}
            ).fetchone()

            if existing:
                # Update existing record
                update_stmt = text("""
                    UPDATE app_opportunities SET
                        title = :title,
                        text = :text,
                        subreddit = :subreddit,
                        upvotes = :upvotes,
                        comments_count = :comments_count,
                        score = :score,
                        created_utc = :created_utc,
                        permalink = :permalink,
                        quality_score = :quality_score,
                        trust_score = :trust_score,
                        opportunity_score = :opportunity_score,
                        confidence_score = :confidence_score,
                        monetization_score = :monetization_score,
                        willingness_to_pay_score = :willingness_to_pay_score,
                        customer_segment = :customer_segment,
                        core_functions = :core_functions,
                        app_concept = :app_concept,
                        problem_description = :problem_description,
                        trust_level = :trust_level,
                        trust_badges = :trust_badges,
                        processed_at = :processed_at,
                        pipeline_version = :pipeline_version
                    WHERE submission_id = :submission_id
                """)

                session.execute(update_stmt, opp)
                updated += 1
            else:
                # Insert new record
                insert_stmt = text("""
                    INSERT INTO app_opportunities (
                        submission_id, title, text, subreddit, upvotes, comments_count, score,
                        created_utc, permalink, quality_score, trust_score, opportunity_score,
                        confidence_score, monetization_score, willingness_to_pay_score,
                        customer_segment, core_functions, app_concept, problem_description,
                        trust_level, trust_badges, processed_at, pipeline_version
                    ) VALUES (
                        :submission_id, :title, :text, :subreddit, :upvotes, :comments_count, :score,
                        :created_utc, :permalink, :quality_score, :trust_score, :opportunity_score,
                        :confidence_score, :monetization_score, :willingness_to_pay_score,
                        :customer_segment, :core_functions, :app_concept, :problem_description,
                        :trust_level, :trust_badges, :processed_at, :pipeline_version
                    )
                """)

                session.execute(insert_stmt, opp)
                inserted += 1

        return {"inserted": inserted, "updated": updated}

    def _append_opportunities(self, session: Session, opportunities: List[Dict]) -> Dict[str, int]:
        """Append opportunities (insert only)."""
        for opp in opportunities:
            insert_stmt = text("""
                INSERT INTO app_opportunities (
                    submission_id, title, text, subreddit, upvotes, comments_count, score,
                    created_utc, permalink, quality_score, trust_score, opportunity_score,
                    confidence_score, monetization_score, willingness_to_pay_score,
                    customer_segment, core_functions, app_concept, problem_description,
                    trust_level, trust_badges, processed_at, pipeline_version
                ) VALUES (
                    :submission_id, :title, :text, :subreddit, :upvotes, :comments_count, :score,
                    :created_utc, :permalink, :quality_score, :trust_score, :opportunity_score,
                    :confidence_score, :monetization_score, :willingness_to_pay_score,
                    :customer_segment, :core_functions, :app_concept, :problem_description,
                    :trust_level, :trust_badges, :processed_at, :pipeline_version
                )
            """)

            session.execute(insert_stmt, opp)

        return {"inserted": len(opportunities), "updated": 0}

    def _replace_opportunities(self, session: Session, opportunities: List[Dict], table_name: str) -> Dict[str, int]:
        """Replace all data in table with new opportunities."""
        # Clear existing data
        session.execute(text(f"TRUNCATE TABLE {table_name}"))

        # Insert new data
        return self._append_opportunities(session, opportunities)

    def _verify_load_operation(self, session: Session, opportunities: List[Dict], primary_key: str) -> int:
        """Verify that all records were successfully loaded."""
        ids = [opp[primary_key] for opp in opportunities]

        if not ids:
            return 0

        # Count loaded records
        result = session.execute(
            text(f"SELECT COUNT(*) FROM app_opportunities WHERE {primary_key} = ANY(:ids)"),
            {"ids": ids}
        ).scalar()

        return result

    def validate_connection(self) -> bool:
        """Validate database connection and table structure."""
        try:
            with self.engine.connect() as conn:
                # Test query
                result = conn.execute(text("SELECT 1")).scalar()
                return result == 1
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            return False

    def get_load_statistics(self) -> Dict[str, Any]:
        """Get statistics about recent load operations."""
        try:
            with self.engine.connect() as conn:
                # Get table statistics
                result = conn.execute(text("""
                    SELECT
                        COUNT(*) as total_records,
                        COUNT(DISTINCT subreddit) as unique_subreddits,
                        MAX(created_utc) as latest_record,
                        MIN(created_utc) as earliest_record
                    FROM app_opportunities
                """)).fetchone()

                return {
                    "total_records": result.total_records,
                    "unique_subreddits": result.unique_subreddits,
                    "latest_record": result.latest_record,
                    "earliest_record": result.earliest_record,
                    "connection_status": "connected"
                }

        except Exception as e:
            logger.error(f"Failed to get load statistics: {e}")
            return {
                "total_records": 0,
                "connection_status": "error",
                "error": str(e)
            }

# Factory function for backwards compatibility
def create_sqlalchemy_loader(
    connection_string: str = None,
    use_local_dev: bool = True
) -> SQLAlchemyLoader:
    """
    Factory function to create SQLAlchemy loader instance.

    Args:
        connection_string: PostgreSQL connection string
        use_local_dev: Use local development defaults

    Returns:
        Configured SQLAlchemy loader instance
    """
    if connection_string is None:
        if use_local_dev:
            connection_string = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
        else:
            # Try to get from environment or DLT config
            import os
            connection_string = os.getenv("DESTINATION__POSTGRES__CREDENTIALS")
            if not connection_string:
                raise SQLAlchemyLoadError("No connection string provided and local dev disabled")

    return SQLAlchemyLoader(connection_string)
```

### 1.2 DLT Compatibility Adapter

**File: `pipeline-v2/storage/dlt_compatibility_adapter.py`**
```python
"""
DLT Compatibility Adapter for RedditHarbor Pipeline v2

Provides DLT-like interface for SQLAlchemy loader to ensure backwards compatibility.
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
                table_name=table_name,
                write_disposition=write_disposition,
                primary_key=primary_key
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

# Factory function for seamless replacement
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
    sqlalchemy_loader = create_sqlalchemy_loader(
        connection_string=connection_string,
        use_local_dev=use_local_dev
    )

    return DLTCompatibilityAdapter(
        sqlalchemy_loader=sqlalchemy_loader,
        pipeline_name=pipeline_name
    )
```

## Phase 2: Testing Implementation

### 2.1 Characterization Tests

**File: `pipeline-v2/tests/test_dlt_characterization.py`**
```python
"""
Characterization tests for current DLT implementation.

These tests document the exact behavior of the current DLT system
to establish baseline expectations for the SQLAlchemy migration.
"""

import pytest
import logging
from typing import Dict, List, Any
from datetime import datetime, UTC

from storage.dlt_loader import DLTLoader

logger = logging.getLogger(__name__)

class TestDLTCharacterization:
    """Characterize current DLT behavior before migration."""

    @pytest.fixture
    def dlt_loader(self):
        """Create DLT loader instance for testing."""
        try:
            return DLTLoader(
                pipeline_name="characterization_test",
                use_local_dev=True
            )
        except Exception as e:
            pytest.skip(f"DLT not available: {e}")

    @pytest.fixture
    def sample_opportunities(self):
        """Sample opportunity data for testing."""
        return [{
            "submission_id": "char_test_001",
            "title": "Characterization Test Opportunity",
            "text": "This is a test opportunity for DLT characterization.",
            "subreddit": "test",
            "upvotes": 100,
            "comments_count": 25,
            "score": 125.0,
            "created_utc": datetime.now(UTC).isoformat(),
            "quality_score": 85.0,
            "trust_score": 80.0,
            "opportunity_score": 75.0,
            "confidence_score": 70.0,
            "monetization_score": 65.0,
            "willingness_to_pay_score": 60.0,
            "customer_segment": "Test Segment",
            "core_functions": ["test", "characterization"],
            "app_concept": "Test Concept",
            "problem_description": "Test problem",
            "trust_level": "HIGH",
            "trust_badges": ["TEST_BADGE"],
            "processed_at": datetime.now(UTC).isoformat(),
            "pipeline_version": "char_test"
        }]

    def test_dlt_connection_validation(self, dlt_loader):
        """Characterize DLT connection validation behavior."""
        result = dlt_loader.validate_connection()

        # Document actual behavior
        logger.info(f"DLT connection validation result: {result}")

        # This test documents current behavior, not expected behavior
        assert isinstance(result, bool)

    def test_dlt_load_success_behavior(self, dlt_loader, sample_opportunities):
        """Characterize DLT load success reporting."""
        try:
            load_info = dlt_loader.load_opportunities(
                opportunities=sample_opportunities,
                table_name="app_opportunities",
                write_disposition="merge",
                primary_key="submission_id"
            )

            # Document DLT's load info structure
            logger.info(f"DLT load_info type: {type(load_info)}")
            logger.info(f"DLT load_info attributes: {dir(load_info)}")

            # Check for common DLT attributes
            if hasattr(load_info, 'load_id'):
                logger.info(f"DLT load_id: {load_info.load_id}")
            if hasattr(load_info, 'counts'):
                logger.info(f"DLT counts: {load_info.counts}")
            if hasattr(load_info, 'table_names'):
                logger.info(f"DLT table_names: {load_info.table_names}")

        except Exception as e:
            logger.error(f"DLT load failed with error: {e}")
            logger.error(f"Error type: {type(e)}")

            # Document the failure mode
            pytest.fail(f"DLT load characterization failed: {e}")

    def test_dlt_silent_failure_investigation(self, dlt_loader, sample_opportunities):
        """Investigate DLT's silent failure behavior."""

        # Record pre-load database state
        pre_load_count = self._get_database_record_count()

        try:
            # Attempt load
            load_info = dlt_loader.load_opportunities(sample_opportunities)

            # Check if DLT reports success
            dlt_reports_success = self._dlt_reports_success(load_info)
            logger.info(f"DLT reports success: {dlt_reports_success}")

            # Check actual database state
            post_load_count = self._get_database_record_count()
            records_added = post_load_count - pre_load_count
            logger.info(f"Records actually added to database: {records_added}")

            # Document the discrepancy
            if dlt_reports_success and records_added == 0:
                logger.error("⚠️  CONFIRMED: DLT reports success but no data in database (silent failure)")

            # This test documents the silent failure issue
            assert True  # Always pass - this is characterization, not validation

        except Exception as e:
            logger.error(f"DLT silent failure investigation failed: {e}")

    def test_dlt_error_reporting(self, dlt_loader):
        """Characterize DLT's error reporting behavior."""

        # Test with invalid data that should cause an error
        invalid_opportunities = [{
            "submission_id": None,  # Invalid: null primary key
            "title": "Invalid test"
        }]

        try:
            load_info = dlt_loader.load_opportunities(invalid_opportunities)

            # Document how DLT handles errors
            logger.info(f"DLT handled invalid data without exception")
            logger.info(f"Load info: {load_info}")

        except Exception as e:
            logger.info(f"DLT raised exception for invalid data: {e}")
            logger.info(f"Exception type: {type(e)}")

    def _get_database_record_count(self) -> int:
        """Get current record count from database."""
        try:
            import os
            from sqlalchemy import create_engine, text

            # Try to get connection from DLT config
            conn_str = os.getenv("DESTINATION__POSTGRES__CREDENTIALS",
                                "postgresql://postgres:postgres@127.0.0.1:54322/postgres")

            engine = create_engine(conn_str)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM app_opportunities")).scalar()
                return result or 0

        except Exception as e:
            logger.warning(f"Could not get database record count: {e}")
            return -1

    def _dlt_reports_success(self, load_info) -> bool:
        """Check if DLT load_info indicates success."""
        if hasattr(load_info, 'counts') and load_info.counts:
            return sum(load_info.counts.values()) > 0
        elif hasattr(load_info, 'success'):
            return load_info.success
        else:
            # Default assumption: if no error exception, DLT considers it success
            return True
```

### 2.2 SQLAlchemy Implementation Tests

**File: `pipeline-v2/tests/test_sqlalchemy_loader.py`**
```python
"""
Comprehensive tests for SQLAlchemy loader implementation.

These tests verify that the SQLAlchemy replacement provides
explicit transaction control and eliminates silent failures.
"""

import pytest
import logging
from typing import Dict, List, Any
from datetime import datetime, UTC

from storage.sqlalchemy_loader import SQLAlchemyLoader, LoadResult, create_sqlalchemy_loader

logger = logging.getLogger(__name__)

class TestSQLAlchemyLoader:
    """Test SQLAlchemy loader implementation."""

    @pytest.fixture
    def sqlalchemy_loader(self):
        """Create SQLAlchemy loader for testing."""
        connection_string = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
        try:
            loader = SQLAlchemyLoader(connection_string, echo=False)
            return loader
        except Exception as e:
            pytest.skip(f"SQLAlchemy connection failed: {e}")

    @pytest.fixture
    def sample_opportunities(self):
        """Sample opportunity data for testing."""
        return [{
            "submission_id": "sqlalchemy_test_001",
            "title": "SQLAlchemy Test Opportunity",
            "text": "This is a test opportunity for SQLAlchemy loader validation.",
            "subreddit": "test",
            "upvotes": 100,
            "comments_count": 25,
            "score": 125.0,
            "created_utc": datetime.now(UTC).isoformat(),
            "quality_score": 85.0,
            "trust_score": 80.0,
            "opportunity_score": 75.0,
            "confidence_score": 70.0,
            "monetization_score": 65.0,
            "willingness_to_pay_score": 60.0,
            "customer_segment": "Test Segment",
            "core_functions": ["test", "sqlalchemy"],
            "app_concept": "SQLAlchemy Test Concept",
            "problem_description": "SQLAlchemy test problem",
            "trust_level": "HIGH",
            "trust_badges": ["SQLALCHEMY_TEST_BADGE"],
            "processed_at": datetime.now(UTC).isoformat(),
            "pipeline_version": "sqlalchemy_test"
        }]

    def test_connection_validation(self, sqlalchemy_loader):
        """Test explicit connection validation."""
        result = sqlalchemy_loader.validate_connection()

        assert result is True, "Connection validation should return True for working connection"

        # Test statistics to ensure connection is working
        stats = sqlalchemy_loader.get_load_statistics()
        assert stats["connection_status"] == "connected"
        assert "total_records" in stats

    def test_explicit_success_behavior(self, sqlalchemy_loader, sample_opportunities):
        """Test that SQLAlchemy provides explicit success/failure feedback."""

        # Get pre-load state
        pre_load_stats = sqlalchemy_loader.get_load_statistics()
        pre_count = pre_load_stats["total_records"]

        # Load data
        load_result = sqlalchemy_loader.load_opportunities(
            opportunities=sample_opportunities,
            table_name="app_opportunities",
            write_disposition="merge"
        )

        # Verify explicit success reporting
        assert isinstance(load_result, LoadResult)
        assert load_result.success is True
        assert load_result.records_inserted > 0
        assert load_result.error_message is None
        assert load_result.load_id is not None

        # Verify actual data persistence
        post_load_stats = sqlalchemy_loader.get_load_statistics()
        post_count = post_load_stats["total_records"]

        assert post_count == pre_count + load_result.records_inserted, \
            f"Database should have {load_result.records_inserted} more records"

        logger.info(f"✓ SQLAlchemy explicit success validation passed")
        logger.info(f"  - Records inserted: {load_result.records_inserted}")
        logger.info(f"  - Database count change: {post_count - pre_count}")

    def test_explicit_failure_behavior(self, sqlalchemy_loader):
        """Test that SQLAlchemy provides explicit failure feedback."""

        # Create invalid opportunity data that should cause failure
        invalid_opportunities = [{
            "submission_id": "sqlalchemy_invalid_test",
            "upvotes": "invalid_number",  # This should cause a type error
            "score": "not_a_float"
        }]

        # Attempt load - should fail explicitly
        load_result = sqlalchemy_loader.load_opportunities(
            opportunities=invalid_opportunities,
            table_name="app_opportunities"
        )

        # Verify explicit failure reporting
        assert isinstance(load_result, LoadResult)
        assert load_result.success is False
        assert load_result.records_inserted == 0
        assert load_result.error_message is not None
        assert len(load_result.error_message) > 0

        logger.info(f"✓ SQLAlchemy explicit failure validation passed")
        logger.info(f"  - Error message: {load_result.error_message}")

    def test_transaction_rollback_behavior(self, sqlalchemy_loader):
        """Test that failed transactions are properly rolled back."""

        # Get initial record count
        initial_count = sqlalchemy_loader.get_load_statistics()["total_records"]

        # Create data where first record is valid but second is invalid
        mixed_validity_opportunities = [
            {
                "submission_id": "rollback_test_valid",
                "title": "Valid Record",
                "subreddit": "test",
                "upvotes": 100,
                "score": 100.0,
                "created_utc": datetime.now(UTC).isoformat()
            },
            {
                "submission_id": "rollback_test_invalid",
                "title": "Invalid Record",
                "subreddit": "test",
                "upvotes": "invalid",  # This should cause rollback
                "score": "not_a_float"
            }
        ]

        # Attempt load - should fail and rollback
        load_result = sqlalchemy_loader.load_opportunities(
            opportunities=mixed_validity_opportunities,
            table_name="app_opportunities"
        )

        # Verify load failed
        assert load_result.success is False
        assert load_result.error_message is not None

        # Verify rollback - no records should be added
        final_count = sqlalchemy_loader.get_load_statistics()["total_records"]
        assert final_count == initial_count, \
            "No records should be added when transaction rolls back"

        # Verify valid record was not persisted
        with sqlalchemy_loader.get_session() as session:
            result = session.execute(
                text("SELECT COUNT(*) FROM app_opportunities WHERE submission_id = 'rollback_test_valid'")
            ).scalar()
            assert result == 0, "Valid record should not be persisted after rollback"

        logger.info(f"✓ SQLAlchemy transaction rollback validation passed")
        logger.info(f"  - Initial count: {initial_count}")
        logger.info(f"  - Final count: {final_count}")
        logger.info(f"  - Records added: 0 (correct rollback)")

    def test_merge_disposition_behavior(self, sqlalchemy_loader, sample_opportunities):
        """Test merge write disposition behavior."""

        # First load - should insert
        first_load = sqlalchemy_loader.load_opportunities(
            opportunities=sample_opportunities,
            write_disposition="merge"
        )

        assert first_load.success is True
        assert first_load.records_inserted == len(sample_opportunities)
        assert first_load.records_updated == 0

        # Second load with same IDs - should update
        updated_opportunities = [
            {**opp, "upvotes": 999, "title": "Updated Title"}
            for opp in sample_opportunities
        ]

        second_load = sqlalchemy_loader.load_opportunities(
            opportunities=updated_opportunities,
            write_disposition="merge"
        )

        assert second_load.success is True
        assert second_load.records_inserted == 0
        assert second_load.records_updated == len(sample_opportunities)

        # Verify updates were applied
        with sqlalchemy_loader.get_session() as session:
            result = session.execute(
                text("SELECT upvotes, title FROM app_opportunities WHERE submission_id = :id"),
                {"id": sample_opportunities[0]["submission_id"]}
            ).fetchone()

            assert result.upvotes == 999
            assert result.title == "Updated Title"

        logger.info(f"✓ SQLAlchemy merge disposition validation passed")

    def test_id_resolution_integration(self, sqlalchemy_loader):
        """Test integration with ID resolution system."""

        # Test with raw Reddit ID
        reddit_id_opportunities = [{
            "submission_id": "abc123xyz",  # Raw Reddit ID
            "title": "Reddit ID Test",
            "subreddit": "test",
            "upvotes": 50,
            "score": 75.0,
            "created_utc": datetime.now(UTC).isoformat()
        }]

        load_result = sqlalchemy_loader.load_opportunities(
            opportunities=reddit_id_opportunities,
            write_disposition="merge"
        )

        assert load_result.success is True

        # Verify ID was resolved to UUID format
        with sqlalchemy_loader.get_session() as session:
            result = session.execute(
                text("SELECT submission_id FROM app_opportunities WHERE title = 'Reddit ID Test'")
            ).fetchone()

            assert result is not None

            # Should be a UUID, not the raw Reddit ID
            stored_id = result.submission_id
            assert stored_id != "abc123xyz"
            assert len(stored_id) == 36  # UUID length
            assert stored_id.count('-') == 4  # UUID format

        logger.info(f"✓ SQLAlchemy ID resolution integration validation passed")

    def test_load_statistics_accuracy(self, sqlalchemy_loader, sample_opportunities):
        """Test that load statistics are accurate."""

        # Get initial statistics
        initial_stats = sqlalchemy_loader.get_load_statistics()
        initial_count = initial_stats["total_records"]

        # Load data
        load_result = sqlalchemy_loader.load_opportunities(
            opportunities=sample_opportunities,
            write_disposition="append"
        )

        # Get updated statistics
        updated_stats = sqlalchemy_loader.get_load_statistics()
        updated_count = updated_stats["total_records"]

        # Verify statistics accuracy
        assert updated_count == initial_count + load_result.records_inserted
        assert updated_stats["connection_status"] == "connected"
        assert "unique_subreddits" in updated_stats

        logger.info(f"✓ SQLAlchemy load statistics validation passed")
        logger.info(f"  - Initial records: {initial_count}")
        logger.info(f"  - Loaded records: {load_result.records_inserted}")
        logger.info(f"  - Final records: {updated_count}")
        logger.info(f"  - Count matches: {updated_count == initial_count + load_result.records_inserted}")
```

## Phase 3: Migration Validation

### 3.1 Parallel Testing Framework

**File: `pipeline-v2/tests/test_migration_parallel.py`**
```python
"""
Parallel testing framework for DLT to SQLAlchemy migration.

Runs both DLT and SQLAlchemy implementations side-by-side to validate
data consistency and identify any discrepancies.
"""

import pytest
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime, UTC

from storage.dlt_loader import DLTLoader
from storage.sqlalchemy_loader import SQLAlchemyLoader

logger = logging.getLogger(__name__)

class TestMigrationParallel:
    """Parallel testing of DLT and SQLAlchemy implementations."""

    @pytest.fixture
    def dlt_loader(self):
        """Create DLT loader instance."""
        try:
            return DLTLoader(
                pipeline_name="parallel_test_dlt",
                use_local_dev=True
            )
        except Exception as e:
            pytest.skip(f"DLT not available for parallel testing: {e}")

    @pytest.fixture
    def sqlalchemy_loader(self):
        """Create SQLAlchemy loader instance."""
        connection_string = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
        try:
            return SQLAlchemyLoader(connection_string, echo=False)
        except Exception as e:
            pytest.skip(f"SQLAlchemy not available for parallel testing: {e}")

    @pytest.fixture
    def unique_test_data(self):
        """Generate unique test data for parallel comparison."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
        unique_id = f"parallel_test_{timestamp}"

        return [{
            "submission_id": unique_id,
            "title": f"Parallel Test Opportunity {timestamp}",
            "text": f"This is a parallel test opportunity created at {timestamp}.",
            "subreddit": "test",
            "upvotes": 100,
            "comments_count": 25,
            "score": 125.0,
            "created_utc": datetime.now(UTC).isoformat(),
            "quality_score": 85.0,
            "trust_score": 80.0,
            "opportunity_score": 75.0,
            "confidence_score": 70.0,
            "monetization_score": 65.0,
            "willingness_to_pay_score": 60.0,
            "customer_segment": "Parallel Test Segment",
            "core_functions": ["test", "parallel"],
            "app_concept": "Parallel Test Concept",
            "problem_description": "Parallel test problem",
            "trust_level": "HIGH",
            "trust_badges": ["PARALLEL_TEST_BADGE"],
            "processed_at": datetime.now(UTC).isoformat(),
            "pipeline_version": "parallel_test"
        }]

    def test_parallel_data_consistency(self, dlt_loader, sqlalchemy_loader, unique_test_data):
        """Test that both implementations handle the same data consistently."""

        # Get initial database state
        initial_stats = sqlalchemy_loader.get_load_statistics()
        initial_count = initial_stats["total_records"]

        logger.info(f"Starting parallel test with {len(unique_test_data)} records")
        logger.info(f"Initial database record count: {initial_count}")

        # Load with SQLAlchemy
        sqlalchemy_result = sqlalchemy_loader.load_opportunities(
            opportunities=unique_test_data,
            table_name="app_opportunities",
            write_disposition="merge"
        )

        logger.info(f"SQLAlchemy result: {sqlalchemy_result.to_dict()}")

        # Load with DLT (using different submission_id to avoid conflicts)
        dlt_test_data = [
            {**record, "submission_id": f"dlt_{record['submission_id']}", "title": f"DLT {record['title']}"}
            for record in unique_test_data
        ]

        try:
            dlt_load_info = dlt_loader.load_opportunities(
                opportunities=dlt_test_data,
                table_name="app_opportunities",
                write_disposition="merge"
            )

            logger.info(f"DLT load completed")
            logger.info(f"DLT load_info type: {type(dlt_load_info)}")
            logger.info(f"DLT load_info attributes: {dir(dlt_load_info)}")

            # Document DLT behavior
            dlt_reports_success = self._check_dlt_success(dlt_load_info)
            logger.info(f"DLT reports success: {dlt_reports_success}")

        except Exception as e:
            logger.error(f"DLT load failed: {e}")
            logger.error(f"Error type: {type(e)}")
            dlt_reports_success = False

        # Check actual database state
        final_stats = sqlalchemy_loader.get_load_statistics()
        final_count = final_stats["total_records"]
        records_added = final_count - initial_count

        logger.info(f"Final database record count: {final_count}")
        logger.info(f"Records actually added: {records_added}")
        logger.info(f"SQLAlchemy reported inserted: {sqlalchemy_result.records_inserted}")

        # Validate SQLAlchemy consistency
        assert sqlalchemy_result.success is True
        assert sqlalchemy_result.records_inserted == len(unique_test_data)
        assert records_added >= sqlalchemy_result.records_inserted, \
            f"Database should have at least {sqlalchemy_result.records_inserted} new records"

        # Document DLT vs SQLAlchemy behavior
        self._document_parallel_results(
            dlt_success=dlt_reports_success,
            sqlalchemy_success=sqlalchemy_result.success,
            records_added=records_added,
            sqlalchemy_reported=sqlalchemy_result.records_inserted
        )

        # Verify SQLAlchemy-loaded data is correctly stored
        with sqlalchemy_loader.get_session() as session:
            result = session.execute(
                text("SELECT COUNT(*) FROM app_opportunities WHERE submission_id = :id"),
                {"id": unique_test_data[0]["submission_id"]}
            ).scalar()

            assert result == 1, "SQLAlchemy-loaded record should be present"

        logger.info(f"✓ Parallel consistency test completed")

    def test_error_handling_comparison(self, dlt_loader, sqlalchemy_loader):
        """Compare error handling between implementations."""

        # Create invalid data that should cause errors
        invalid_data = [{
            "submission_id": None,  # Invalid primary key
            "title": "Invalid Test",
            "upvotes": "not_a_number"  # Invalid data type
        }]

        # Test SQLAlchemy error handling
        sqlalchemy_result = sqlalchemy_loader.load_opportunities(
            opportunities=invalid_data,
            table_name="app_opportunities"
        )

        # Test DLT error handling
        try:
            dlt_load_info = dlt_loader.load_opportunities(
                opportunities=invalid_data,
                table_name="app_opportunities"
            )
            dlt_reports_success = self._check_dlt_success(dlt_load_info)
            dlt_error_message = None
        except Exception as e:
            dlt_reports_success = False
            dlt_error_message = str(e)

        # Document error handling differences
        logger.info(f"SQLAlchemy error handling:")
        logger.info(f"  - Success: {sqlalchemy_result.success}")
        logger.info(f"  - Error message: {sqlalchemy_result.error_message}")
        logger.info(f"  - Records inserted: {sqlalchemy_result.records_inserted}")

        logger.info(f"DLT error handling:")
        logger.info(f"  - Success: {dlt_reports_success}")
        logger.info(f"  - Error message: {dlt_error_message}")

        # Validate SQLAlchemy provides explicit error feedback
        assert sqlalchemy_result.success is False
        assert sqlalchemy_result.error_message is not None
        assert sqlalchemy_result.records_inserted == 0

        logger.info(f"✓ Error handling comparison completed")

    def test_performance_comparison(self, dlt_loader, sqlalchemy_loader):
        """Compare performance characteristics."""

        # Create larger dataset for performance testing
        performance_data = []
        for i in range(100):  # 100 records
            performance_data.append({
                "submission_id": f"perf_test_{i}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
                "title": f"Performance Test Record {i}",
                "subreddit": "performance_test",
                "upvotes": i * 10,
                "score": float(i * 15),
                "created_utc": datetime.now(UTC).isoformat(),
                "quality_score": 80.0 + (i % 20),
                "trust_score": 75.0 + (i % 25)
            })

        # Test SQLAlchemy performance
        import time
        sqlalchemy_start = time.time()

        sqlalchemy_result = sqlalchemy_loader.load_opportunities(
            opportunities=performance_data,
            write_disposition="append"
        )

        sqlalchemy_time = time.time() - sqlalchemy_start

        # Test DLT performance
        dlt_performance_data = [
            {**record, "submission_id": f"dlt_{record['submission_id']}"}
            for record in performance_data
        ]

        dlt_start = time.time()

        try:
            dlt_load_info = dlt_loader.load_opportunities(
                opportunities=dlt_performance_data,
                write_disposition="append"
            )
            dlt_time = time.time() - dlt_start
            dlt_reports_success = self._check_dlt_success(dlt_load_info)
        except Exception as e:
            dlt_time = time.time() - dlt_start
            dlt_reports_success = False
            logger.error(f"DLT performance test failed: {e}")

        # Document performance comparison
        logger.info(f"Performance comparison for {len(performance_data)} records:")
        logger.info(f"SQLAlchemy:")
        logger.info(f"  - Time: {sqlalchemy_time:.2f}s")
        logger.info(f"  - Success: {sqlalchemy_result.success}")
        logger.info(f"  - Records/sec: {len(performance_data) / sqlalchemy_time:.1f}")

        logger.info(f"DLT:")
        logger.info(f"  - Time: {dlt_time:.2f}s")
        logger.info(f"  - Success: {dlt_reports_success}")
        if dlt_reports_success:
            logger.info(f"  - Records/sec: {len(performance_data) / dlt_time:.1f}")

        # Validate SQLAlchemy performance is reasonable
        assert sqlalchemy_result.success is True
        assert sqlalchemy_time < 30.0, "SQLAlchemy should complete within 30 seconds"
        assert len(performance_data) / sqlalchemy_time > 10, "Should process at least 10 records/sec"

        logger.info(f"✓ Performance comparison completed")

    def _check_dlt_success(self, load_info) -> bool:
        """Check if DLT load_info indicates success."""
        if hasattr(load_info, 'counts') and load_info.counts:
            return sum(load_info.counts.values()) > 0
        elif hasattr(load_info, 'success'):
            return load_info.success
        else:
            # Default assumption
            return True

    def _document_parallel_results(self, dlt_success: bool, sqlalchemy_success: bool,
                                 records_added: int, sqlalchemy_reported: int):
        """Document parallel test results for analysis."""
        result_summary = {
            "timestamp": datetime.now(UTC).isoformat(),
            "dlt_reports_success": dlt_success,
            "sqlalchemy_success": sqlalchemy_success,
            "database_records_added": records_added,
            "sqlalchemy_reports_inserted": sqlalchemy_reported,
            "consistency_check": records_added >= sqlalchemy_reported,
            "silent_failure_detected": dlt_success and records_added < sqlalchemy_reported
        }

        logger.info(f"PARALLEL TEST SUMMARY: {result_summary}")

        # If silent failure detected, document it clearly
        if result_summary["silent_failure_detected"]:
            logger.error("🚨 SILENT FAILURE CONFIRMED:")
            logger.error(f"   DLT reports success: {dlt_success}")
            logger.error(f"   SQLAlchemy actually inserted: {sqlalchemy_reported}")
            logger.error(f"   Database actually contains: {records_added}")
```

This comprehensive implementation guide provides:

1. **Core SQLAlchemy Implementation** - Full replacement for DLT with explicit transaction control
2. **DLT Compatibility Adapter** - Backwards-compatible interface to minimize code changes
3. **Characterization Tests** - Document current DLT behavior for comparison
4. **Comprehensive Test Suite** - Validate all aspects of the SQLAlchemy implementation
5. **Parallel Testing Framework** - Direct comparison between DLT and SQLAlchemy

The implementation addresses the critical silent failure issue by providing:
- Explicit commit/rollback transactions
- Immediate success/failure feedback
- No silent data loss
- Comprehensive error reporting
- Performance visibility

The TDD approach ensures that migration is safe and validated at every step.