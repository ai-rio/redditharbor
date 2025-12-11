# SQLModel Loader Design Document

**Author:** Backend System Architect
**Date:** 2025-12-10
**Phase:** 2, Task 2.1
**Status:** Design Complete

---

## Executive Summary

This document outlines the design for `SQLModelLoader`, a SQLModel-based database loader that will replace the existing `PostgresLoader` in Pipeline V4. The design ensures backward compatibility while leveraging SQLModel's ORM capabilities for better maintainability and type safety.

## Key Requirements

1. **Drop-in Replacement**: Same public API as `PostgresLoader`
2. **SQLModel Integration**: Use Session-based operations
3. **Transaction Safety**: Proper rollback and commit handling
4. **Performance**: Within 10% of psycopg2 loader
5. **Error Handling**: Graceful degradation with detailed logging

---

## Architecture Overview

### Current State (PostgresLoader)
```
PostgresLoader
├── psycopg2 connection pool
├── Raw SQL with parameter binding
├── Manual transaction management
└── ON CONFLICT DO NOTHING for duplicates
```

### Target State (SQLModelLoader)
```
SQLModelLoader
├── SQLModel Session from database.py
├── ORM-based operations
├── Context-managed transactions
└── Duplicate detection via SELECT query
```

---

## Class Design

### SQLModelLoader Class Structure

```python
from typing import Optional, List
from sqlmodel import Session, select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging

from models.analysis import Opportunity
from database import get_db_session
from config.settings import get_settings

logger = logging.getLogger(__name__)

class SQLModelLoader:
    """
    SQLModel-based database loader for Opportunity records.

    Provides the same interface as PostgresLoader while using SQLModel
    ORM for type safety and maintainability.
    """

    def __init__(self, settings=None):
        """Initialize the loader with database session management."""
        self.settings = settings or get_settings()
        logger.info("✓ SQLModel Loader initialized")

    def save_opportunity(self, opportunity: Opportunity) -> bool:
        """
        Save an opportunity to the database.

        Args:
            opportunity: Opportunity instance to save

        Returns:
            bool: True if saved, False if duplicate skipped

        Raises:
            RuntimeError: If database operation fails
        """
        pass  # Implementation below

    def save_opportunities(self, opportunities: List[Opportunity]) -> int:
        """
        Save multiple opportunities in a single transaction.

        Args:
            opportunities: List of opportunities to save

        Returns:
            int: Number of records actually saved (excludes duplicates)

        Raises:
            RuntimeError: If database operation fails
        """
        pass  # Implementation below

    def get_opportunity(self, submission_id: str) -> Optional[Opportunity]:
        """
        Retrieve an opportunity by submission_id.

        Args:
            submission_id: Reddit submission ID

        Returns:
            Optional[Opportunity]: Found record or None
        """
        pass  # Implementation below

    def get_opportunities_by_subreddit(self, subreddit: str) -> List[Opportunity]:
        """
        Get all opportunities for a specific subreddit.

        Args:
            subreddit: Subreddit name

        Returns:
            List[Opportunity]: List of opportunities
        """
        pass  # Implementation below

    def close(self):
        """Close any resources (placeholder for consistency)."""
        logger.info("SQLModel Loader closed")
```

---

## Implementation Details

### 1. Session Management Strategy

We'll use the context manager approach from `database.py`:

```python
def save_opportunity(self, opportunity: Opportunity) -> bool:
    """Save a single opportunity with duplicate detection."""

    try:
        with get_db_session() as session:
            # Check for duplicate
            existing = session.exec(
                select(Opportunity)
                .where(Opportunity.submission_id == opportunity.submission_id)
            ).first()

            if existing:
                logger.info(f"⊘ Skipped duplicate {opportunity.submission_id}")
                return False

            # Save new record
            session.add(opportunity)
            session.flush()  # Get ID without committing
            session.refresh(opportunity)  # Update instance with DB values

            logger.info(f"✓ Saved opportunity {opportunity.submission_id}")
            return True

    except SQLAlchemyError as e:
        logger.error(f"Database error saving {opportunity.submission_id}: {e}")
        raise RuntimeError(f"Failed to save opportunity: {e}")
```

**Why this approach:**
- `get_db_session()` handles commit/rollback automatically
- Context manager ensures session cleanup
- Session is created per operation (good for connection pool)
- Exception handling is centralized

### 2. Duplicate Detection Strategy

Instead of SQL's `ON CONFLICT`, we'll use a SELECT query:

```python
# Check for duplicate before insert
existing = session.exec(
    select(Opportunity)
    .where(Opportunity.submission_id == opportunity.submission_id)
).first()

if existing:
    return False  # Skip duplicate
```

**Performance considerations:**
- Query uses the indexed `submission_id` column
- Single query before insert (no race condition at isolation level READ_COMMITTED)
- Could use `INSERT ... ON CONFLICT` with raw SQL if needed

### 3. Batch Operations

For improved performance, we'll support batch saves:

```python
def save_opportunities(self, opportunities: List[Opportunity]) -> int:
    """Save multiple opportunities efficiently."""

    if not opportunities:
        return 0

    saved_count = 0

    try:
        with get_db_session() as session:
            # Check all submission_ids at once
            submission_ids = [opp.submission_id for opp in opportunities]
            existing_map = {
                record.submission_id: record
                for record in session.exec(
                    select(Opportunity)
                    .where(Opportunity.submission_id.in_(submission_ids))
                ).all()
            }

            # Filter out duplicates
            new_opportunities = [
                opp for opp in opportunities
                if opp.submission_id not in existing_map
            ]

            if new_opportunities:
                session.add_all(new_opportunities)
                session.flush()  # Get IDs

                for opp in new_opportunities:
                    session.refresh(opp)
                    logger.debug(f"Saved opportunity {opp.submission_id}")

                saved_count = len(new_opportunities)
                logger.info(f"✓ Batch saved {saved_count}/{len(opportunities)} opportunities")
            else:
                logger.info("All opportunities were duplicates, none saved")

            return saved_count

    except SQLAlchemyError as e:
        logger.error(f"Batch save failed: {e}")
        raise RuntimeError(f"Failed to save opportunities: {e}")
```

### 4. Error Handling Approach

We'll implement a comprehensive error handling strategy:

```python
class SQLModelLoader:
    # ... previous code ...

    def _handle_database_error(self, error: SQLAlchemyError, operation: str) -> None:
        """Centralized error handling with specific error types."""

        if isinstance(error, IntegrityError):
            if "unique" in str(error).lower():
                # This shouldn't happen with our duplicate check, but handle gracefully
                logger.warning(f"Integrity error in {operation}: {error}")
            else:
                logger.error(f"Integrity constraint violation in {operation}: {error}")

        elif isinstance(error, OperationalError):
            if "connection" in str(error).lower():
                logger.error(f"Database connection error in {operation}: {error}")
            else:
                logger.error(f"Database operation error in {operation}: {error}")

        else:
            logger.error(f"Unexpected database error in {operation}: {type(error).__name__}: {error}")
```

### 5. Transaction Boundaries

We'll use the context manager from `database.py`:

```python
# database.py context manager handles:
with get_db_session() as session:
    # Auto-begin transaction
    try:
        # Operations here
        session.commit()  # Auto-commit at exit
    except Exception:
        session.rollback()  # Auto-rollback on error
        raise
    finally:
        session.close()  # Auto-close
```

**Key benefits:**
- Automatic transaction management
- No forgotten commits or rollbacks
- Clean separation of concerns
- Session lifecycle managed externally

---

## Data Model Alignment

### Current Issue
The `PostgresLoader` expects nested structure:
```python
analysis.app_idea.title  # AttributeError!
```

### Opportunity Model Structure
```python
class Opportunity(SQLModel, table=True):
    submission_id: str
    title: str
    analysis: Dict[str, Any] = {"app_idea": {"title": "..."}}
    metrics: Dict[str, Any] = {"market_demand": 90.0}
```

### Solution
The `SQLModelLoader` will properly handle the model structure:

```python
def _prepare_opportunity_from_analysis(self, analysis_result) -> Opportunity:
    """Create Opportunity instance from analysis result."""

    return Opportunity(
        submission_id=analysis_result.submission_id,
        subreddit=analysis_result.subreddit,
        title=analysis_result.title,
        wtp_score=analysis_result.wtp_score,

        # Properly structure analysis data
        analysis={
            "app_idea": {
                "title": analysis_result.app_idea.title,
                "app_concept": analysis_result.app_idea.app_concept,
                "problem_statement": analysis_result.app_idea.problem_statement,
                "core_functions": analysis_result.app_idea.core_functions,
                "target_audience": analysis_result.app_idea.target_audience,
            },
            "spam_analysis": analysis_result.spam_analysis,
            "pain_points": analysis_result.pain_points,
        },

        # Properly structure metrics
        metrics={
            "market_demand": analysis_result.market_metrics.market_demand,
            "pain_intensity": analysis_result.market_metrics.pain_intensity,
            "monetization_potential": analysis_result.market_metrics.monetization_potential,
            "competition_level": analysis_result.market_metrics.competition_level,
            "technical_feasibility": analysis_result.market_metrics.technical_feasibility,
        },

        trust_level=analysis_result.trust_level,
        updated_at=datetime.now(UTC)
    )
```

---

## Performance Optimizations

### 1. Connection Pool Utilization
- Leverage existing pool configuration from `database.py`
- Default: pool_size=10, max_overflow=20
- Consider increasing for high-throughput scenarios

### 2. Bulk Operations
```python
# Instead of N separate inserts
for opp in opportunities:
    session.add(opp)  # N database round-trips

# Use bulk operations
session.add_all(opportunities)  # 1 database round-trip
session.flush()  # 1 database round-trip for IDs
```

### 3. Query Optimization
```python
# Use indexed columns efficiently
session.exec(
    select(Opportunity)
    .where(Opportunity.submission_id.in_(ids))  # Uses index
    .where(Opportunity.final_score > 50)  # Consider adding index
)

# Only select needed columns for queries
session.exec(
    select(Opportunity.submission_id, Opportunity.final_score)
    .where(Opportunity.subreddit == subreddit)
)
```

### 4. Session Reuse
- Consider session-per-request pattern for web contexts
- For batch processing, use single session with periodic commits

---

## Logging Strategy

### Log Levels and Messages

```python
# INFO level - Key operations
logger.info(f"✓ Saved opportunity {opp.submission_id}")
logger.info(f"⊘ Skipped duplicate {opp.submission_id}")
logger.info(f"✓ Batch saved {count}/{total} opportunities")

# DEBUG level - Detailed operations
logger.debug(f"Checking for duplicate: {submission_id}")
logger.debug(f"Session state: {session.dirty}, {session.new}")

# WARNING level - Expected issues
logger.warning(f"Opportunity missing required field: {field}")
logger.warning(f"Connection pool nearing capacity: {pool.checkedout()}/{pool.size()}")

# ERROR level - Exceptions and failures
logger.error(f"Database error: {error}")
logger.error(f"Failed to save opportunity {submission_id}: {error}")
```

### Structured Logging Format
```python
# Include context for better debugging
logger.info(
    "Operation completed",
    extra={
        "operation": "save_opportunity",
        "submission_id": opp.submission_id,
        "duration_ms": duration,
        "is_duplicate": False
    }
)
```

---

## Migration Strategy

### Phase 1: Parallel Implementation
1. Create `SQLModelLoader` alongside `PostgresLoader`
2. Add feature flag in settings: `use_sqlmodel_loader: bool = False`
3. Create factory pattern for loader selection

### Phase 2: Feature Flag Testing
```python
# config/settings.py
use_sqlmodel_loader: bool = Field(
    default=False,
    alias="USE_SQLMODEL_LOADER"
)

# load/loader_factory.py
def get_loader(settings: Settings) -> BaseLoader:
    """Factory function to select loader based on feature flag."""
    if settings.use_sqlmodel_loader:
        logger.info("Using SQLModelLoader")
        return SQLModelLoader(settings)
    else:
        logger.info("Using PostgresLoader")
        return PostgresLoader(settings)
```

### Phase 3: Gradual Migration
1. Run both loaders in parallel with comparison
2. Monitor for data differences
3. Gradually increase traffic to SQLModelLoader
4. Deprecate and remove PostgresLoader

---

## Testing Strategy

### Unit Tests
```python
# test_sqlmodel_loader.py
def test_save_new_opportunity():
    """Test saving a new opportunity."""
    loader = SQLModelLoader()
    opp = create_test_opportunity()

    result = loader.save_opportunity(opp)

    assert result is True
    assert opp.id is not None  # Should be set by database

def test_skip_duplicate_opportunity():
    """Test duplicate detection."""
    loader = SQLModelLoader()
    opp = create_test_opportunity()

    # First save
    assert loader.save_opportunity(opp) is True

    # Second save - should skip
    assert loader.save_opportunity(opp) is False

def test_transaction_rollback():
    """Test rollback on error."""
    loader = SQLModelLoader()

    # Create invalid opportunity
    opp = Opportunity()  # Missing required fields

    with pytest.raises(RuntimeError):
        loader.save_opportunity(opp)

    # Verify nothing was saved
    assert loader.get_opportunity(opp.submission_id) is None
```

### Integration Tests
```python
def test_loader_compatibility():
    """Test both loaders produce identical results."""
    data = create_test_dataset()

    # Save with PostgresLoader
    pg_loader = PostgresLoader()
    pg_results = [pg_loader.save_opportunity(opp) for opp in data]

    # Save with SQLModelLoader
    sm_loader = SQLModelLoader()
    sm_results = [sm_loader.save_opportunity(opp) for opp in data]

    # Compare results
    assert pg_results == sm_results

    # Verify database state is identical
    pg_data = get_all_opportunities()
    sm_data = get_all_opportunities()
    assert_data_identical(pg_data, sm_data)
```

### Performance Tests
```python
def test_performance_benchmark():
    """Benchmark loader performance."""
    data = create_large_dataset(1000)

    # Test PostgresLoader
    start = time.time()
    for opp in data:
        pg_loader.save_opportunity(opp)
    pg_time = time.time() - start

    # Test SQLModelLoader
    start = time.time()
    for opp in data:
        sm_loader.save_opportunity(opp)
    sm_time = time.time() - start

    # Verify within 10%
    assert sm_time <= pg_time * 1.1
```

---

## Design Questions Answered

### 1. How will duplicate detection work with SQLModel?
- Use `SELECT` query before `INSERT`
- Leverage indexed `submission_id` column
- Single query per operation for efficiency

### 2. Should we use sessions directly or context managers?
- Use context managers from `database.py`
- Provides automatic transaction management
- Cleaner code with proper resource cleanup

### 3. How to handle connection pooling errors?
- Leverage SQLAlchemy's built-in connection pool
- Configure timeouts and retry logic
- Log pool utilization metrics

### 4. What performance optimizations can be made?
- Bulk operations with `add_all()`
- Batch duplicate checking with `IN` clauses
- Proper indexing on queried columns
- Consider session-per-request pattern

### 5. How to ensure transaction safety?
- Use context manager for automatic commit/rollback
- Exception handling preserves transaction integrity
- Proper isolation levels to prevent race conditions

---

## Implementation Checklist

- [ ] Create `SQLModelLoader` class with all required methods
- [ ] Implement duplicate detection logic
- [ ] Add comprehensive error handling
- [ ] Create data preparation helpers for model alignment
- [ ] Add logging at appropriate levels
- [ ] Write unit tests for all methods
- [ ] Create integration tests with PostgresLoader comparison
- [ ] Add performance benchmarks
- [ ] Implement feature flag system
- [ ] Create loader factory pattern
- [ ] Update documentation

---

## Risks and Mitigations

### Risk 1: Performance Regression
- **Mitigation:** Bulk operations, connection pool tuning, benchmarking

### Risk 2: Data Model Misalignment
- **Mitigation:** Data preparation helpers, comprehensive testing

### Risk 3: Connection Pool Exhaustion
- **Mitigation:** Pool monitoring, proper session lifecycle management

### Risk 4: Race Conditions in Duplicate Detection
- **Mitigation:** Proper transaction isolation, database constraints

### Risk 5: Memory Usage with Large Datasets
- **Mitigation:** Batch processing, session lifecycle management

---

## Conclusion

The `SQLModelLoader` design provides a clean, type-safe replacement for the existing `PostgresLoader` while maintaining full backward compatibility. The design leverages SQLModel's ORM capabilities, provides robust error handling, and includes performance optimizations to ensure production readiness.

The modular approach with context managers, factory patterns, and feature flags ensures a smooth migration path with zero downtime and the ability to rollback instantly if issues arise.

---

**Next Steps:**
1. Review and approve this design
2. Proceed with Task 2.2: Write SQLModel Loader Tests
3. Implement SQLModelLoader following this design
4. Run comprehensive testing and validation
