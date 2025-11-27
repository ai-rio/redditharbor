# SQLAlchemy Implementation

## Overview

This document provides the complete SQLAlchemy implementation that replaces DLT with explicit transaction control and eliminates silent failures. The implementation is extracted from the technical review and implementation guide, organized for practical TDD execution.

## Core Implementation Files

### 1. SQLAlchemy Loader (`pipeline-v2/storage/sqlalchemy_loader.py`)

This is the main replacement for DLT that provides explicit transaction control and eliminates silent failures.

```python
"""
SQLAlchemy-based data loader for RedditHarbor Pipeline v2

Replaces DLT to provide explicit transaction control and eliminate silent failures.
Key improvements:
- Explicit transaction commit/rollback
- Immediate success/failure feedback
- No silent data loss
- Integration with existing ID resolution system
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
    """Structured result for load operations with explicit success/failure."""
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
            echo: Enable SQLAlchemy query logging (set True for debugging)
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
        Prepare opportunity data for SQLAlchemy insertion with ID resolution.

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

                # Remove None values to avoid SQL issues
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

        This method eliminates silent failures by:
        1. Preparing data with ID resolution
        2. Using explicit transactions with commit/rollback
        3. Verifying data persistence before reporting success
        4. Providing immediate error feedback

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
            # Prepare data with ID resolution
            prepared_opportunities = self.prepare_opportunity_data(opportunities)

            # Explicit transaction control
            with self.get_session() as session:
                with session.begin():  # Automatic rollback on exception
                    if write_disposition == "merge":
                        result = self._merge_opportunities(session, prepared_opportunities, primary_key)
                    elif write_disposition == "append":
                        result = self._append_opportunities(session, prepared_opportunities)
                    elif write_disposition == "replace":
                        result = self._replace_opportunities(session, prepared_opportunities, table_name)
                    else:
                        raise SQLAlchemyLoadError(f"Unsupported write_disposition: {write_disposition}")

                    # CRITICAL: Verify operation success before commit
                    verification_count = self._verify_load_operation(session, prepared_opportunities, primary_key)
                    if verification_count != len(prepared_opportunities):
                        raise SQLAlchemyLoadError(
                            f"Load verification failed: expected {len(prepared_opportunities)} records, found {verification_count}"
                        )

                    # Transaction commits automatically on success
                    # Rolls back automatically if exception is raised

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
        """Merge opportunities using upsert logic with explicit handling."""
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
        """
        Verify that all records were successfully loaded.

        This is the critical step that eliminates silent failures - we verify
        data was actually persisted before reporting success.
        """
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

# Factory function for easy instantiation
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

### 2. DLT Compatibility Adapter (`pipeline-v2/storage/dlt_compatibility_adapter.py`)

This adapter provides backwards compatibility while gaining SQLAlchemy reliability.

```python
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
    from .sqlalchemy_loader import create_sqlalchemy_loader

    sqlalchemy_loader = create_sqlalchemy_loader(
        connection_string=connection_string,
        use_local_dev=use_local_dev
    )

    return DLTCompatibilityAdapter(
        sqlalchemy_loader=sqlalchemy_loader,
        pipeline_name=pipeline_name
    )
```

## Key Improvements Over DLT

### 1. Explicit Transaction Control

```python
# DLT (problematic):
load_info = pipeline.run(opportunities, write_disposition="merge")
# May report success but no actual commit

# SQLAlchemy (explicit):
with session.begin():  # Explicit transaction
    # Prepare and insert data
    session.add_all(records)
    # Automatic commit on success, rollback on exception
```

### 2. Immediate Success/Failure Feedback

```python
# DLT result (ambiguous):
load_info = pipeline.run(opportunities)
# Success not clearly defined

# SQLAlchemy result (explicit):
result = loader.load_opportunities(opportunities)
assert result.success == True  # Clear success indicator
assert result.records_inserted > 0  # Actual records confirmed
assert result.error_message is None  # No errors
```

### 3. Data Persistence Verification

```python
def _verify_load_operation(self, session: Session, opportunities: List[Dict]) -> int:
    """Critical verification step that eliminates silent failures"""
    ids = [opp[primary_key] for opp in opportunities]
    result = session.execute(
        text(f"SELECT COUNT(*) FROM app_opportunities WHERE {primary_key} = ANY(:ids)"),
        {"ids": ids}
    ).scalar()
    return result  # Actual count of persisted records
```

### 4. ID Resolution Integration

```python
def prepare_opportunity_data(self, opportunities: List[Dict]) -> List[Dict]:
    """Prepare data with ID resolution"""
    for opp in opportunities:
        # Resolve submission ID using existing system
        id_result = resolve_submission_id(opp.get('submission_id', ''))
        prepared_opp['submission_id'] = id_result.uuid  # Use resolved UUID
```

## Implementation Steps

### Step 1: Create Files
```bash
# Create storage directory if it doesn't exist
mkdir -p pipeline-v2/storage

# Create implementation files
touch pipeline-v2/storage/sqlalchemy_loader.py
touch pipeline-v2/storage/dlt_compatibility_adapter.py
touch pipeline-v2/storage/__init__.py
```

### Step 2: Test Connection
```python
# Test basic SQLAlchemy connection
from storage.sqlalchemy_loader import create_sqlalchemy_loader

try:
    loader = create_sqlalchemy_loader()
    print("✓ Connection valid:", loader.validate_connection())
    print("✓ Statistics:", loader.get_load_statistics())
except Exception as e:
    print("❌ Connection failed:", e)
```

### Step 3: Test Basic Load
```python
# Test basic load operation
from storage.sqlalchemy_loader import create_sqlalchemy_loader

loader = create_sqlalchemy_loader()
test_data = [{
    "submission_id": "sqlalchemy_test_001",
    "title": "Test Load",
    "subreddit": "test",
    "upvotes": 100,
    "score": 100.0,
    "created_utc": datetime.now(UTC).isoformat()
}]

result = loader.load_opportunities(test_data)
print("Load result:", result.to_dict())
```

### Step 4: Test Compatibility Adapter
```python
# Test DLT compatibility
from storage.dlt_compatibility_adapter import create_dlt_compatible_loader

loader = create_dlt_compatible_loader()
load_info = loader.run(test_data)
print("DLT-compatible result:", load_info)
```

## TDD Test Implementation

See the complete test suite in [`04-validation-testing.md`](04-validation-testing.md) for comprehensive tests covering:

1. **Explicit Success/Failure Tests** - Validate clear success/failure indicators
2. **Transaction Control Tests** - Verify rollback behavior
3. **Data Integrity Tests** - Confirm data persistence
4. **Performance Tests** - Ensure acceptable performance

## Integration with Existing Code

### Minimal Code Changes

Existing code using DLT can be updated with minimal changes:

```python
# Before (DLT):
from storage.dlt_loader import DLTLoader
loader = DLTLoader(pipeline_name="my_pipeline")
load_info = loader.run(opportunities, write_disposition="merge")

# After (SQLAlchemy compatible):
from storage.dlt_compatibility_adapter import create_dlt_compatible_loader
loader = create_dlt_compatible_loader(pipeline_name="my_pipeline")
load_info = loader.run(opportunities, write_disposition="merge")
```

### Gradual Migration

1. **Phase 1**: Deploy SQLAlchemy alongside DLT
2. **Phase 2**: Test both systems in parallel
3. **Phase 3**: Switch default to SQLAlchemy
4. **Phase 4**: Remove DLT code (after validation)

This implementation provides a robust, tested replacement for DLT that eliminates silent failures while maintaining full backwards compatibility.