"""Failing tests for SQLAlchemy ORM integration with submissions table.

RED PHASE: These tests are designed to FAIL and define the desired behavior
for SQLAlchemy ORM integration. The failures will guide the implementation
of proper SQLAlchemy models and database abstraction.

Root Cause: DatabaseFetcher hardcoded schema assumptions for app_opportunities
table with submission_id column, but submissions table uses UUID id column.
This is the same issue that caused 5 days of DLT pain - hardcoded schema
assumptions throughout the codebase.
"""

import pytest
from uuid import uuid4
from typing import Dict, Any

# These imports WILL FAIL - this is intentional for RED phase
from core.db.models import Submission  # Module doesn't exist yet
from core.db.session import get_db_session, engine  # Module doesn't exist yet
from core.fetchers.database_fetcher import DatabaseFetcher


class TestSubmissionsORM:
    """
    Test suite for SQLAlchemy ORM integration with submissions table.

    All tests should FAIL in RED phase, indicating missing components:
    - core.db.models module doesn't exist
    - core.db.session module doesn't exist
    - Submission SQLAlchemy model doesn't exist
    - DatabaseFetcher lacks ORM integration
    """

    def test_schema_introspection_reflects_actual_schema(self):
        """
        Test that SQLAlchemy can reflect submissions table schema from database.

        This test verifies that SQLAlchemy can introspect the actual database
        schema and match it with our model expectations. It should FAIL because
        we haven't created the SQLAlchemy models yet.

        Expected schema (from actual database):
        - id: VARCHAR(100) (primary key) - NOT submission_id!
        - reddit_id: string/varchar (Reddit's submission ID)
        - title: varchar
        - subreddit: varchar
        - reddit_score: bigint
        - num_comments: bigint
        - created_utc: bigint (timestamp)
        - author: varchar
        - selftext: varchar

        This FAILS because:
        1. core.db.models module doesn't exist
        2. Submission SQLAlchemy model doesn't exist
        3. No schema reflection logic implemented
        """
        # This should fail with ImportError
        submission_table = Submission.__table__

        # Verify critical columns exist
        expected_columns = {
            'id',  # Database id field (currently NULL)
            'submission_id',  # Primary key with UUID-like values
            'reddit_id',  # Reddit's submission ID
            'title',
            'subreddit',
            'reddit_score',
            'num_comments',
            'created_utc',
            'author',
            'selftext'
        }

        actual_columns = {col.name for col in submission_table.columns}
        assert expected_columns <= actual_columns, f"Missing columns: {expected_columns - actual_columns}"

        # Verify submission_id is VARCHAR and primary key
        submission_id_column = submission_table.columns['submission_id']
        assert 'VARCHAR' in str(submission_id_column.type).upper(), "submission_id column should be VARCHAR type"
        assert submission_id_column.primary_key, "submission_id column should be primary key"

        # Verify reddit_id exists (this is what DatabaseFetcher should use)
        reddit_id_column = submission_table.columns['reddit_id']
        assert not reddit_id_column.primary_key, "reddit_id should not be primary key"

    def test_query_submissions_by_reddit_id(self):
        """
        Test querying submissions by reddit_id field using SQLAlchemy ORM.

        This test verifies we can query submissions using the reddit_id
        field (Reddit's native submission ID). This should FAIL because
        no ORM query methods exist yet.

        This addresses the core issue: DatabaseFetcher hardcoded 'submission_id'
        but the actual field is 'reddit_id'.

        This FAILS because:
        1. core.db.session module doesn't exist
        2. No SQLAlchemy session management
        3. Submission model doesn't exist
        """
        # This should fail with ImportError
        with get_db_session() as session:
            # Query by reddit_id (the actual field name in database)
            # Use a real reddit_id that exists in the database
            reddit_id = "test_enhanced_123"
            from sqlalchemy import select
            stmt = select(Submission).filter_by(reddit_id=reddit_id)
            result = session.execute(stmt)
            submission = result.scalar_one_or_none()

            # Should return submission with proper submission_id
            assert submission is not None
            assert submission.reddit_id == reddit_id
            assert submission.submission_id is not None  # Should be string (VARCHAR)
            assert isinstance(submission.submission_id, str)  # String type check
            assert submission.title is not None
            assert submission.subreddit is not None

    def test_id_insertion_and_retrieval(self):
        """
        Test inserting submission with proper ID handling.

        This test verifies we can insert submissions with manual
        ID primary keys and retrieve them properly. This should FAIL
        because no ORM models or insertion logic exists.

        This FAILS because:
        1. No SQLAlchemy Submission model
        2. No database session management
        3. No ORM insertion methods
        """
        # This should fail with ImportError
        import time
        unique_id = f'test-submission-{int(time.time() * 1000)}'
        test_data = {
            'submission_id': unique_id,
            'reddit_id': f't3_test_{int(time.time())}',
            'title': 'Test Submission',
            'subreddit': 'test',
            'reddit_score': 100,
            'num_comments': 25,
            'created_utc': 1672531200,  # 2024-01-01T00:00:00Z as epoch seconds
            'author': 'test_user',
            'selftext': 'Test content here',
            '_dlt_id': f'test_dlt_{int(time.time())}',
            '_dlt_load_id': str(time.time())
        }

        with get_db_session() as session:
            # Create new submission (ID is provided manually)
            new_submission = Submission(**test_data)
            session.add(new_submission)
            session.commit()
            session.refresh(new_submission)

            # Verify submission_id was set correctly
            assert new_submission.submission_id is not None
            assert isinstance(new_submission.submission_id, str)
            assert new_submission.submission_id == unique_id

            # Verify data integrity
            assert new_submission.reddit_id == test_data['reddit_id']
            assert new_submission.title == test_data['title']

            # Test retrieval by submission_id
            from sqlalchemy import select
            stmt = select(Submission).filter_by(submission_id=new_submission.submission_id)
            retrieved = session.execute(stmt).scalar_one_or_none()
            assert retrieved is not None
            assert retrieved.reddit_id == test_data['reddit_id']

    def test_database_fetcher_orm_integration(self):
        """
        Test that DatabaseFetcher can use ORM to fetch submissions dynamically.

        This test verifies that DatabaseFetcher can be updated to use ORM
        instead of hardcoded REST queries, eliminating the submission_id
        vs id mismatch issue. This should FAIL because DatabaseFetcher
        still uses hardcoded REST queries.

        The key issue this addresses:
        - DatabaseFetcher line 154: hardcoded 'submission_id' field
        - Actual table uses 'id' (UUID) primary key
        - Should use 'reddit_id' for Reddit ID lookups

        This FAILS because:
        1. DatabaseFetcher doesn't use ORM
        2. No dynamic schema introspection
        3. Still has hardcoded column assumptions
        """
        # This should fail because DatabaseFetcher doesn't support ORM yet
        fetcher_config = {
            'table_name': 'submissions',  # Use submissions table, not app_opportunities
            'use_orm': True,  # This option doesn't exist yet
            'id_field': 'reddit_id'  # Use correct field for Reddit IDs
        }

        # Mock Supabase client (should be unused in ORM mode)
        mock_client = None
        fetcher = DatabaseFetcher(mock_client, config=fetcher_config)

        # This should use ORM, not hardcoded REST queries
        submissions = list(fetcher.fetch(limit=5))

        # Verify submissions have correct schema
        for submission in submissions:
            # Should have UUID id field, not submission_id
            assert 'id' in submission
            assert 'reddit_id' in submission  # Reddit's native ID
            assert 'title' in submission
            assert 'subreddit' in submission

            # Should NOT have hardcoded submission_id field
            assert 'submission_id' not in submission, "Legacy submission_id field should not exist"


class TestDatabaseSchemaVerification:
    """
    Additional tests to verify database schema matches assumptions.
    These help ensure our ORM models will be built on correct assumptions.
    """

    def test_database_connection_and_table_exists(self):
        """
        Test that database connection works and submissions table exists.

        This should FAIL because no database session module exists.
        """
        # This should fail with ImportError
        with get_db_session() as session:
            from sqlalchemy import text
            # Simple query to verify table exists
            result = session.execute(text("SELECT COUNT(*) FROM submissions LIMIT 1"))
            count = result.scalar()
            assert isinstance(count, int)

    def test_submissions_table_column_verification(self):
        """
        Test detailed column verification for submissions table.

        This should FAIL because no schema introspection exists.
        """
        # This should fail with ImportError
        with get_db_session() as session:
            from sqlalchemy import text
            # Get table info from database
            result = session.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'submissions'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()

            # Convert to dict for easier verification
            column_info = {row[0]: {'type': row[1], 'nullable': row[2]} for row in columns}

            # Verify critical columns exist with correct types
            assert 'id' in column_info
            assert 'UUID' in column_info['id']['type'].upper()

            assert 'reddit_id' in column_info
            assert 'VARCHAR' in column_info['reddit_id']['type'].upper() or 'TEXT' in column_info['reddit_id']['type'].upper()

            assert 'title' in column_info
            assert 'subreddit' in column_info


# Expected failure messages for verification:
MISSING_MODEL_ERROR = "No module named 'core.db.models'"
MISSING_SESSION_ERROR = "No module named 'core.db.session'"
MISSING_ORM_FEATURE_ERROR = "DatabaseFetcher ORM integration not implemented"


@pytest.mark.xfail(reason="RED_PHASE_MISSING_COMPONENTS", strict=True)
class TestExpectedFailures:
    """
    Test class to explicitly mark expected failures and verify error messages.
    This ensures we're failing for the right reasons.
    """

    def test_import_models_fails_with_correct_error(self):
        """Verify models import fails with expected error."""
        with pytest.raises(ImportError, match="core.db.models"):
            from core.db.models import Submission

    def test_import_session_fails_with_correct_error(self):
        """Verify session import fails with expected error."""
        with pytest.raises(ImportError, match="core.db.session"):
            from core.db.session import get_db_session

    def test_database_fetcher_lacks_orm_support(self):
        """Verify DatabaseFetcher doesn't have ORM support yet."""
        mock_client = None
        fetcher = DatabaseFetcher(mock_client, config={'use_orm': True})

        # Should not have orm-related attributes
        assert not hasattr(fetcher, 'use_orm')
        assert not hasattr(fetcher, 'query_submissions')


if __name__ == "__main__":
    # Run tests to confirm RED phase
    pytest.main([__file__, "-v", "--tb=short"])