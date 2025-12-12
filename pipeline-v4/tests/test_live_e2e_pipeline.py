"""
Live End-to-End Pipeline Integration Test

COMPLETE PIPELINE TEST: Real Reddit API → Real LLM → Real Database
NO MOCKS, NO FIXTURES - Tests actual production pipeline

This test:
1. Fetches real submissions from Reddit API
2. Analyzes with real OpenRouter LLM
3. Saves to real PostgreSQL database
4. Verifies duplicate detection
5. Validates database integrity

Requirements:
- REDDIT_PUBLIC and REDDIT_SECRET in .env.local
- OPENROUTER_API_KEY in .env.local
- PostgreSQL database running (see DATABASE_URL)
"""

import logging
import os
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlmodel import Session, select

from config.settings import get_settings
from core.pipeline import Pipeline
from core.staging import StagingLayer
from database import get_db_session, get_engine
from extract.reddit_client import RedditClient
from load.loader import Loader
from models.analysis import Opportunity
from transform.analyzer import OpportunityAnalyzer

# Configure logging for test output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class TestLiveE2EPipeline:
    """Live E2E integration tests for complete pipeline"""

    @classmethod
    def setup_class(cls):
        """Setup test class with credential checks"""
        cls.settings = get_settings()
        cls.test_subreddit = "productivity"
        cls.test_limit = 3

        # Store credentials for skip checks
        cls.has_reddit_creds = bool(
            cls.settings.reddit_client_id and
            cls.settings.reddit_client_secret
        )
        cls.has_llm_creds = bool(cls.settings.llm_api_key)
        cls.has_db_url = bool(cls.settings.database_url)

        logger.info("=" * 60)
        logger.info("LIVE E2E PIPELINE TEST SETUP")
        logger.info("=" * 60)
        logger.info(f"Test Subreddit: r/{cls.test_subreddit}")
        logger.info(f"Test Limit: {cls.test_limit} submissions")
        logger.info(f"Reddit Credentials: {'✓' if cls.has_reddit_creds else '✗'}")
        logger.info(f"LLM Credentials: {'✓' if cls.has_llm_creds else '✗'}")
        logger.info(f"Database URL: {'✓' if cls.has_db_url else '✗'}")
        logger.info("=" * 60)

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for each test method"""
        # Clear staging state before each test
        staging_dir = Path("pipeline_staging")
        if staging_dir.exists():
            state_file = staging_dir / "processed.json"
            if state_file.exists():
                state_file.unlink()
                logger.info("✓ Cleared staging state")

        yield

        # Cleanup after test (optional)
        # Note: We intentionally keep data in DB for verification

    def test_live_pipeline_complete(self):
        """
        LIVE E2E TEST: Complete pipeline from Reddit to Database

        Tests:
        1. Real Reddit API call (fetch 3 submissions)
        2. Real LLM analysis (OpenRouter)
        3. Real database storage (PostgreSQL)
        4. Verification of stored data
        """
        # Skip if credentials are placeholders
        if (
            self.settings.llm_api_key == "your_openrouter_api_key_here" or
            "your_" in self.settings.reddit_client_id.lower() or
            "your_" in self.settings.reddit_client_secret.lower()
        ):
            pytest.skip("Credentials contain placeholder values - update .env.local with real credentials")

        logger.info("\n" + "=" * 60)
        logger.info("TEST: LIVE PIPELINE COMPLETE")
        logger.info("=" * 60)

        start_time = time.time()

        # Initialize pipeline with real components
        pipeline = Pipeline(settings=self.settings)

        try:
            # STAGE 1: Extract from Real Reddit API
            logger.info(f"\n[STAGE 1] Extracting from r/{self.test_subreddit}...")
            extract_start = time.time()

            submissions = pipeline.reddit.fetch_submissions(
                subreddits=[self.test_subreddit],
                limit=self.test_limit,
                sort_by="hot"
            )

            extract_time = time.time() - extract_start

            assert len(submissions) > 0, "No submissions fetched from Reddit"
            assert len(submissions) <= self.test_limit, f"Too many submissions: {len(submissions)}"

            logger.info(f"✓ Fetched {len(submissions)} real submissions from Reddit")
            logger.info(f"  Time: {extract_time:.2f}s")

            # Log submission details
            for i, sub in enumerate(submissions, 1):
                logger.info(f"  [{i}] {sub.id}: {sub.title[:60]}...")

            # STAGE 2: Transform with Real LLM
            logger.info(f"\n[STAGE 2] Analyzing with OpenRouter LLM...")
            transform_start = time.time()

            analyses = []
            for i, submission in enumerate(submissions, 1):
                logger.info(f"  Analyzing submission {i}/{len(submissions)}: {submission.id}")

                analysis = pipeline.analyzer.analyze(submission)
                analyses.append(analysis)

                logger.info(
                    f"    ✓ WTP={analysis.wtp_score:.1f}, "
                    f"Score={analysis.final_score:.1f}, "
                    f"Confidence={analysis.confidence_score:.1f}"
                )

            transform_time = time.time() - transform_start

            assert len(analyses) == len(submissions), "Analysis count mismatch"
            assert all(a.final_score >= 0.0 for a in analyses), "Invalid scores detected"

            logger.info(f"✓ Analyzed {len(analyses)} submissions with LLM")
            logger.info(f"  Time: {transform_time:.2f}s")
            logger.info(f"  Avg per submission: {transform_time / len(analyses):.2f}s")

            # STAGE 3: Load to Real Database
            logger.info(f"\n[STAGE 3] Loading to PostgreSQL database...")
            load_start = time.time()

            saved_count = 0
            for i, analysis in enumerate(analyses, 1):
                logger.info(f"  Saving analysis {i}/{len(analyses)}: {analysis.submission_id}")

                if pipeline.loader.save_analysis(analysis):
                    saved_count += 1
                    logger.info(f"    ✓ Saved to database")
                else:
                    logger.info(f"    ⊘ Skipped (duplicate)")

            load_time = time.time() - load_start

            assert saved_count > 0, "No analyses were saved to database"

            logger.info(f"✓ Saved {saved_count}/{len(analyses)} analyses to database")
            logger.info(f"  Time: {load_time:.2f}s")

            # VERIFICATION: Query database to verify storage
            logger.info(f"\n[VERIFICATION] Querying database...")

            with get_db_session() as session:
                for analysis in analyses:
                    opportunity = session.exec(
                        select(Opportunity).where(
                            Opportunity.submission_id == analysis.submission_id
                        )
                    ).first()

                    assert opportunity is not None, f"Opportunity {analysis.submission_id} not found in DB"
                    assert opportunity.wtp_score == analysis.wtp_score, "WTP score mismatch"
                    assert opportunity.final_score == analysis.final_score, "Final score mismatch"
                    assert opportunity.subreddit == analysis.subreddit, "Subreddit mismatch"
                    assert opportunity.analysis is not None, "Analysis JSON is None"
                    assert opportunity.metrics is not None, "Metrics JSON is None"

                    logger.info(
                        f"  ✓ Verified {opportunity.submission_id}: "
                        f"ID={opportunity.id}, Score={opportunity.final_score:.1f}"
                    )

            # SUMMARY
            total_time = time.time() - start_time

            logger.info("\n" + "=" * 60)
            logger.info("LIVE E2E PIPELINE TEST RESULTS")
            logger.info("=" * 60)
            logger.info(f"✓ Stage 1 (Extract): {len(submissions)} submissions ({extract_time:.2f}s)")
            logger.info(f"✓ Stage 2 (Transform): {len(analyses)} analyses ({transform_time:.2f}s)")
            logger.info(f"✓ Stage 3 (Load): {saved_count} saved ({load_time:.2f}s)")
            logger.info(f"✓ Total Pipeline Time: {total_time:.2f}s")
            logger.info(f"✓ Database Integrity: VERIFIED")
            logger.info("=" * 60)

            # Final assertions
            assert len(submissions) == len(analyses), "Processing mismatch"
            assert saved_count <= len(analyses), "Saved count exceeds analyses"
            assert total_time < 300, f"Pipeline too slow: {total_time:.2f}s"  # 5 min max

        finally:
            # Cleanup
            pipeline.loader.close()

    def test_live_duplicate_detection(self):
        """
        LIVE TEST: Duplicate Detection

        Tests:
        1. Run pipeline twice on same subreddit
        2. Verify second run detects duplicates
        3. Confirm no new inserts on second run
        """
        # Skip if credentials are placeholders
        if (
            self.settings.llm_api_key == "your_openrouter_api_key_here" or
            "your_" in self.settings.reddit_client_id.lower()
        ):
            pytest.skip("Credentials contain placeholder values - update .env.local with real credentials")

        logger.info("\n" + "=" * 60)
        logger.info("TEST: LIVE DUPLICATE DETECTION")
        logger.info("=" * 60)

        # First run
        logger.info("\n[RUN 1] First pipeline execution...")
        pipeline1 = Pipeline(settings=self.settings)

        try:
            results1 = pipeline1.run(
                subreddits=[self.test_subreddit],
                limit=self.test_limit
            )

            first_saved = results1.analyses_saved
            logger.info(f"✓ Run 1: Saved {first_saved} analyses")

            assert first_saved > 0, "First run saved no analyses"

            # Second run (same subreddit)
            logger.info("\n[RUN 2] Second pipeline execution (expect duplicates)...")
            pipeline2 = Pipeline(settings=self.settings)

            results2 = pipeline2.run(
                subreddits=[self.test_subreddit],
                limit=self.test_limit
            )

            second_saved = results2.analyses_saved
            second_skipped = results2.analyses_skipped

            logger.info(f"✓ Run 2: Saved {second_saved}, Skipped {second_skipped}")

            # Verify duplicate detection
            assert second_skipped > 0, "No duplicates detected on second run"
            assert second_saved < first_saved, "Second run saved as many as first"

            logger.info("\n" + "=" * 60)
            logger.info("DUPLICATE DETECTION RESULTS")
            logger.info("=" * 60)
            logger.info(f"✓ First Run: {first_saved} saved")
            logger.info(f"✓ Second Run: {second_saved} saved, {second_skipped} skipped")
            logger.info(f"✓ Duplicate Detection: WORKING")
            logger.info("=" * 60)

        finally:
            pipeline1.loader.close()
            if 'pipeline2' in locals():
                pipeline2.loader.close()

    def test_live_database_integrity(self):
        """
        LIVE TEST: Database Integrity

        Tests:
        1. Query all opportunities from test subreddit
        2. Verify data structure integrity
        3. Check constraints (scores, timestamps, unique IDs)
        """
        logger.info("\n" + "=" * 60)
        logger.info("TEST: LIVE DATABASE INTEGRITY")
        logger.info("=" * 60)

        loader = Loader(settings=self.settings)

        try:
            # Query opportunities
            opportunities = loader.get_opportunities_by_subreddit(self.test_subreddit)

            logger.info(f"✓ Found {len(opportunities)} opportunities in database")

            if len(opportunities) == 0:
                logger.warning("No opportunities found - run test_live_pipeline_complete first")
                pytest.skip("No opportunities in database")

            # Verify data integrity
            submission_ids = set()

            for i, opp in enumerate(opportunities, 1):
                # Check required fields
                assert opp.id is not None, f"Opportunity {i} has no ID"
                assert opp.submission_id, f"Opportunity {i} has no submission_id"
                assert opp.subreddit == self.test_subreddit, f"Subreddit mismatch: {opp.subreddit}"
                assert opp.title, f"Opportunity {i} has no title"

                # Check scores
                assert 0.0 <= opp.wtp_score <= 100.0, f"Invalid WTP score: {opp.wtp_score}"
                assert 0.0 <= opp.final_score <= 100.0, f"Invalid final score: {opp.final_score}"
                assert 0.0 <= opp.confidence_score <= 100.0, f"Invalid confidence score: {opp.confidence_score}"

                # Check trust level
                assert opp.trust_level in ["LOW", "MEDIUM", "HIGH"], f"Invalid trust level: {opp.trust_level}"

                # Check JSON fields
                assert isinstance(opp.analysis, dict), "Analysis is not a dict"
                assert isinstance(opp.metrics, dict), "Metrics is not a dict"

                # Check timestamps
                assert opp.created_at is not None, "No created_at timestamp"
                assert opp.updated_at is not None, "No updated_at timestamp"
                assert opp.created_at <= opp.updated_at, "Timestamp ordering violation"

                # Check uniqueness
                assert opp.submission_id not in submission_ids, f"Duplicate submission_id: {opp.submission_id}"
                submission_ids.add(opp.submission_id)

                logger.info(
                    f"  [{i}] {opp.submission_id}: "
                    f"Score={opp.final_score:.1f}, "
                    f"WTP={opp.wtp_score:.1f}, "
                    f"Trust={opp.trust_level}"
                )

            logger.info("\n" + "=" * 60)
            logger.info("DATABASE INTEGRITY RESULTS")
            logger.info("=" * 60)
            logger.info(f"✓ Opportunities Checked: {len(opportunities)}")
            logger.info(f"✓ Unique submission_ids: {len(submission_ids)}")
            logger.info(f"✓ All scores valid: 0.0-100.0 range")
            logger.info(f"✓ All timestamps valid")
            logger.info(f"✓ All JSON fields valid")
            logger.info(f"✓ Database Integrity: VERIFIED")
            logger.info("=" * 60)

        finally:
            loader.close()

    def test_live_reddit_connection(self):
        """
        LIVE TEST: Reddit API Connection

        Tests:
        1. Reddit API authentication
        2. Subreddit accessibility
        3. Data fetch capability
        """
        logger.info("\n" + "=" * 60)
        logger.info("TEST: LIVE REDDIT CONNECTION")
        logger.info("=" * 60)

        client = RedditClient()

        # Test authentication
        logger.info("\n[TEST] Reddit API authentication...")
        is_connected = client.test_connection()
        assert is_connected, "Reddit API authentication failed"
        logger.info("✓ Reddit API authenticated")

        # Test subreddit access
        logger.info(f"\n[TEST] Accessing r/{self.test_subreddit}...")
        subreddit_info = client.get_subreddit_info(self.test_subreddit)

        assert subreddit_info is not None, "Failed to get subreddit info"
        assert subreddit_info["name"] == self.test_subreddit, "Subreddit name mismatch"

        logger.info(f"✓ Subreddit: r/{subreddit_info['name']}")
        logger.info(f"  Title: {subreddit_info['title']}")
        logger.info(f"  Subscribers: {subreddit_info.get('subscribers', 'N/A')}")

        # Test data fetch
        logger.info(f"\n[TEST] Fetching submissions...")
        submissions = client.fetch_submissions(
            subreddits=[self.test_subreddit],
            limit=2,
            sort_by="hot"
        )

        assert len(submissions) > 0, "No submissions fetched"
        assert all(s.subreddit == self.test_subreddit for s in submissions), "Subreddit mismatch"

        logger.info(f"✓ Fetched {len(submissions)} submissions")
        for i, sub in enumerate(submissions, 1):
            logger.info(f"  [{i}] {sub.id}: {sub.title[:50]}...")

        logger.info("\n" + "=" * 60)
        logger.info("REDDIT CONNECTION RESULTS")
        logger.info("=" * 60)
        logger.info(f"✓ Authentication: VERIFIED")
        logger.info(f"✓ Subreddit Access: VERIFIED")
        logger.info(f"✓ Data Fetch: VERIFIED")
        logger.info("=" * 60)

    def test_cleanup_old_opportunities(self):
        """
        UTILITY TEST: Cleanup old test opportunities

        Optional cleanup for test data (commented out by default)
        """
        logger.info("\n" + "=" * 60)
        logger.info("UTILITY: CLEANUP OLD OPPORTUNITIES")
        logger.info("=" * 60)

        # Uncomment to enable cleanup
        # loader = Loader(settings=self.settings)
        #
        # try:
        #     opportunities = loader.get_opportunities_by_subreddit(self.test_subreddit)
        #
        #     logger.info(f"Found {len(opportunities)} opportunities for cleanup")
        #
        #     for opp in opportunities:
        #         loader.delete_opportunity(opp.submission_id)
        #         logger.info(f"  ✓ Deleted {opp.submission_id}")
        #
        #     logger.info(f"✓ Cleaned up {len(opportunities)} opportunities")
        #
        # finally:
        #     loader.close()

        logger.info("Cleanup disabled (uncomment to enable)")
        logger.info("=" * 60)


# Manual test runner for direct execution
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n" + "=" * 60)
    print("LIVE E2E PIPELINE TEST SUITE")
    print("=" * 60)
    print("\nRunning tests with pytest...\n")

    # Run with pytest
    pytest.main([
        __file__,
        "-v",
        "-s",
        "--tb=short",
        "-k", "test_live"
    ])
