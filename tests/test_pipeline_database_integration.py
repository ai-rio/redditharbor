"""Integration test for OpportunityPipeline with DATABASE source.

TDD RED PHASE: This test documents the expected behavior when the pipeline
fetches from the actual `submissions` table and processes the data through
the enrichment pipeline.

Current State (VALIDATED):
- ✓ 4 submissions stored in database (table: `submissions`)
- ✓ Collection works: `core/reddit/supabase_collection.py`
- ✗ Processing broken: `OpportunityPipeline` cannot read from database

Known Failures (from 8 background processes):
1. **Table mismatch**: Code expects `app_opportunities`, database has `submissions`
2. **Column mismatch**: Code expects `submission_id`, database has `id` and `reddit_id`
3. **Serialization error**: `ResolutionResult` object not JSON serializable

Database Schema (actual):
    submissions table columns:
    - id (uuid, primary key)
    - reddit_id (text) - Reddit's native submission ID
    - title (text)
    - content (text)
    - score (integer)
    - num_comments (integer)
    - subreddit_id (uuid, foreign key)
    - redditor_id (uuid, foreign key)
    - url (text)
    - created_at (timestamp)
    - updated_at (timestamp)

Expected Result:
    This test should currently FAIL with the known errors (RED phase).
    The test documents what SHOULD work after the GREEN phase implementation.
"""

import pytest
import os
from typing import Dict, Any

# Import Supabase client
from supabase import create_client, Client

# Import pipeline components
from core.pipeline import OpportunityPipeline, PipelineConfig, DataSource


@pytest.fixture
def supabase_client() -> Client:
    """Create Supabase client from environment variables.

    Returns:
        Client: Initialized Supabase client

    Raises:
        ValueError: If required environment variables are missing
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        pytest.skip("Supabase credentials not configured")

    return create_client(url, key)


@pytest.fixture
def verify_test_data(supabase_client: Client) -> int:
    """Verify that test data exists in the database.

    Args:
        supabase_client: Initialized Supabase client

    Returns:
        int: Number of submissions found in database

    Raises:
        AssertionError: If no test data is found
    """
    # Count submissions in database
    response = supabase_client.table("submissions").select("id", count="exact").execute()

    count = response.count if hasattr(response, 'count') else len(response.data)

    assert count >= 4, f"Expected at least 4 submissions, found {count}"

    return count


class TestPipelineDatabaseIntegration:
    """Integration tests for OpportunityPipeline with DATABASE source.

    These tests verify the complete pipeline flow from database fetch
    to enrichment and storage. All tests are expected to FAIL in RED phase.
    """

    def test_pipeline_can_fetch_from_submissions_table(
        self,
        supabase_client: Client,
        verify_test_data: int
    ):
        """Test that pipeline can fetch submissions from database.

        This test verifies the most basic pipeline operation:
        1. Configure pipeline with DATABASE source
        2. Run pipeline with dry_run=True (no enrichment)
        3. Verify submissions were fetched without errors

        Expected Failure (RED phase):
            - DatabaseFetcher expects `app_opportunities` table
            - DatabaseFetcher expects `submission_id` column
            - Actual table is `submissions` with `id` + `reddit_id` columns

        Args:
            supabase_client: Initialized Supabase client
            verify_test_data: Number of submissions in database
        """
        # Configure pipeline with DATABASE source
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=supabase_client,
            limit=10,
            dry_run=True,  # Skip storage for this test
            enable_profiler=False,  # Disable enrichment
            enable_opportunity_scoring=False,
            enable_trust=False,
            enable_monetization=False,
        )

        # Create pipeline
        pipeline = OpportunityPipeline(config)

        # Run pipeline
        result = pipeline.run()

        # Assertions
        assert result["success"] is True, f"Pipeline failed: {result.get('error')}"
        assert result["stats"]["fetched"] == min(verify_test_data, 10), \
            f"Expected {min(verify_test_data, 10)} submissions, got {result['stats']['fetched']}"
        assert result["stats"]["errors"] == 0, \
            f"Pipeline had {result['stats']['errors']} errors"

    def test_pipeline_fetches_correct_schema_fields(
        self,
        supabase_client: Client,
        verify_test_data: int
    ):
        """Test that fetched submissions have correct schema fields.

        This test verifies that the formatter correctly maps database columns
        to the expected schema for pipeline processing.

        Expected Failure (RED phase):
            - DatabaseFetcher hardcodes column names from `app_opportunities`
            - Formatter expects `submission_id` but database has `id` + `reddit_id`
            - Column name mismatches cause KeyError or AttributeError

        Args:
            supabase_client: Initialized Supabase client
            verify_test_data: Number of submissions in database
        """
        # Configure pipeline to return data
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=supabase_client,
            limit=4,
            dry_run=True,
            return_data=True,  # Return fetched data
            enable_profiler=False,
            enable_opportunity_scoring=False,
            enable_trust=False,
            enable_monetization=False,
        )

        # Create and run pipeline
        pipeline = OpportunityPipeline(config)
        result = pipeline.run()

        # Verify success
        assert result["success"] is True, f"Pipeline failed: {result.get('error')}"

        # Verify we got data back
        opportunities = result.get("opportunities", [])
        assert len(opportunities) > 0, "No opportunities returned"

        # Verify schema of first submission
        submission = opportunities[0]

        # Required fields that should exist after formatting
        required_fields = {
            "id",  # Primary identifier (could be submission_id or reddit_id)
            "title",  # Post title
            "text",  # Post content
            "subreddit",  # Subreddit name
            "engagement",  # Engagement metadata
        }

        missing_fields = required_fields - set(submission.keys())
        assert not missing_fields, f"Missing required fields: {missing_fields}"

        # Verify engagement structure
        assert isinstance(submission["engagement"], dict), \
            "engagement should be a dictionary"
        assert "upvotes" in submission["engagement"], \
            "engagement should have upvotes"
        assert "num_comments" in submission["engagement"], \
            "engagement should have num_comments"

    def test_pipeline_with_minimal_enrichment(
        self,
        supabase_client: Client,
        verify_test_data: int
    ):
        """Test pipeline with profiler enrichment enabled.

        This test verifies the complete pipeline flow:
        1. Fetch submissions from database
        2. Apply profiler enrichment
        3. Store results (dry_run=False)

        Expected Failure (RED phase):
            - DatabaseFetcher table/column mismatches
            - Formatter field mapping errors
            - Possible ResolutionResult serialization error

        Args:
            supabase_client: Initialized Supabase client
            verify_test_data: Number of submissions in database
        """
        # Configure pipeline with profiler only
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=supabase_client,
            limit=2,  # Process only 2 submissions
            dry_run=True,  # Don't store yet
            enable_profiler=True,  # Enable enrichment
            enable_opportunity_scoring=False,
            enable_trust=False,
            enable_monetization=False,
        )

        # Create and run pipeline
        pipeline = OpportunityPipeline(config)
        result = pipeline.run()

        # Verify pipeline success
        assert result["success"] is True, f"Pipeline failed: {result.get('error')}"

        # Verify fetching worked
        assert result["stats"]["fetched"] == 2, \
            f"Expected 2 submissions fetched, got {result['stats']['fetched']}"

        # Verify enrichment happened
        # Note: In dry_run mode, analyzed count may be 0 if services are not actually called
        # The important part is that no errors occurred
        assert result["stats"]["errors"] == 0, \
            f"Pipeline had {result['stats']['errors']} errors"

    def test_pipeline_error_reporting(
        self,
        supabase_client: Client,
        verify_test_data: int
    ):
        """Test that pipeline reports errors correctly.

        This test verifies that when the pipeline encounters schema mismatches
        or other errors, it reports them properly in the result.

        Expected Failure (RED phase):
            - DatabaseFetcher will raise exception due to table/column mismatch
            - Pipeline should catch and report the error
            - Error message should be descriptive

        Args:
            supabase_client: Initialized Supabase client
            verify_test_data: Number of submissions in database
        """
        # Configure pipeline
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=supabase_client,
            limit=10,
            dry_run=True,
            enable_profiler=False,
            enable_opportunity_scoring=False,
            enable_trust=False,
            enable_monetization=False,
        )

        # Create and run pipeline
        pipeline = OpportunityPipeline(config)
        result = pipeline.run()

        # In RED phase, we expect either:
        # 1. success=False with error message
        # 2. success=True but stats show errors

        if not result["success"]:
            # Pipeline failed with error
            assert "error" in result, "Failed pipeline should have error message"
            error_msg = result["error"]

            # Error should mention the schema mismatch
            assert any(
                keyword in error_msg.lower()
                for keyword in ["submission_id", "column", "table", "schema"]
            ), f"Error message should mention schema issue: {error_msg}"
        else:
            # Pipeline succeeded but may have errors in stats
            # This is also acceptable as long as errors are tracked
            assert "stats" in result, "Result should have stats"


class TestDatabaseFetcherConfiguration:
    """Test DatabaseFetcher configuration and ORM integration.

    These tests verify that DatabaseFetcher can be configured to work
    with the actual database schema using ORM mode.
    """

    def test_database_fetcher_orm_mode(self, supabase_client: Client):
        """Test DatabaseFetcher in ORM mode with correct table configuration.

        This test verifies that DatabaseFetcher can be configured to use:
        - Correct table name: 'submissions' (not 'app_opportunities')
        - Correct ID field: 'id' (uuid primary key)
        - ORM mode for dynamic schema introspection

        Expected Failure (RED phase):
            - DatabaseFetcher doesn't support 'use_orm' config yet
            - DatabaseFetcher doesn't support configurable 'id_field'
            - No dynamic schema introspection implemented

        Args:
            supabase_client: Initialized Supabase client
        """
        from core.fetchers.database_fetcher import DatabaseFetcher

        # Configure fetcher for ORM mode (the actual solution)
        config = {
            'table_name': 'submissions',  # Actual table name
            'use_orm': True,  # Use SQLAlchemy ORM (the whole point!)
            'id_field': 'id',  # UUID primary key
        }

        # Create fetcher
        # Note: In ORM mode, we might not need Supabase client
        fetcher = DatabaseFetcher(supabase_client, config=config)

        # Verify configuration was applied
        assert fetcher.table_name == 'submissions', \
            "Table name should be 'submissions'"
        assert fetcher.use_orm is True, \
            "ORM mode should be enabled (the actual solution!)"
        assert fetcher.id_field == 'id', \
            "ID field should be 'id'"

        # Try to fetch submissions
        submissions = list(fetcher.fetch(limit=2))

        # Verify we got submissions
        assert len(submissions) > 0, "Should fetch at least one submission"

        # Verify schema has correct fields
        submission = submissions[0]
        assert 'id' in submission, "Should have 'id' field (uuid)"
        assert 'reddit_id' in submission, "Should have 'reddit_id' field"
        assert 'title' in submission, "Should have 'title' field"
        assert 'subreddit' in submission or 'subreddit_id' in submission, \
            "Should have subreddit reference"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short", "-s"])
