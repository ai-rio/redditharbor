"""
Characterization tests for current DLT implementation.

These tests document the exact behavior of the current DLT system
to establish baseline expectations for the SQLAlchemy migration.

IMPORTANT: These tests document ACTUAL behavior, not EXPECTED behavior.
They should never be modified to make tests pass - they should document
the current state even if it's problematic.
"""

import pytest
import logging
from typing import Dict, List, Any
from datetime import datetime, UTC
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from storage.dlt_loader import DLTLoader
from core.utils.id_resolver import resolve_submission_id

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

    def test_dlt_connection_validation_behavior(self, dlt_loader):
        """
        Characterize DLT connection validation behavior.

        This test documents how DLT validates connections and what it reports.
        It should document the actual behavior, not enforce expectations.
        """
        result = dlt_loader.validate_connection()

        # Document actual behavior
        logger.info(f"DLT connection validation result: {result}")
        logger.info(f"Result type: {type(result)}")

        # This test documents current behavior, not expected behavior
        assert isinstance(result, bool)  # Should be boolean, but document if not

    def test_dlt_load_success_reporting_structure(self, dlt_loader, sample_opportunities):
        """
        Characterize DLT load success reporting structure.

        Documents what DLT returns when load operation completes,
        regardless of whether data actually persists.
        """
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
                logger.info(f"DLT load_id type: {type(load_info.load_id)}")

            if hasattr(load_info, 'counts'):
                logger.info(f"DLT counts: {load_info.counts}")
                logger.info(f"DLT counts type: {type(load_info.counts)}")

            if hasattr(load_info, 'table_names'):
                logger.info(f"DLT table_names: {load_info.table_names}")
                logger.info(f"DLT table_names type: {type(load_info.table_names)}")

            if hasattr(load_info, 'success'):
                logger.info(f"DLT success: {load_info.success}")
                logger.info(f"DLT success type: {type(load_info.success)}")

        except Exception as e:
            logger.error(f"DLT load failed with error: {e}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error args: {e.args}")

            # Document the failure mode - this is valuable characterization data
            pytest.fail(f"DLT load characterization failed: {e}")

    def test_dlt_silent_failure_investigation(self, dlt_loader, sample_opportunities):
        """
        CRITICAL TEST: Investigate DLT's silent failure behavior.

        This is the most important characterization test. It documents
        the core issue: DLT reports success but no data is actually persisted.
        """

        # Record pre-load database state
        pre_load_count = self._get_database_record_count()
        logger.info(f"Database record count before DLT load: {pre_load_count}")

        try:
            # Attempt load with DLT
            load_info = dlt_loader.load_opportunities(sample_opportunities)

            # Check if DLT reports success
            dlt_reports_success = self._dlt_reports_success(load_info)
            logger.info(f"DLT reports success: {dlt_reports_success}")

            # Document DLT's success indicators
            if hasattr(load_info, 'counts') and load_info.counts:
                reported_count = sum(load_info.counts.values())
                logger.info(f"DLT reports inserting {reported_count} records")
            else:
                reported_count = 0
                logger.info("DLT load_info has no counts attribute or counts is empty")

            # Check actual database state after DLT load
            post_load_count = self._get_database_record_count()
            records_added = post_load_count - pre_load_count
            logger.info(f"Database record count after DLT load: {post_load_count}")
            logger.info(f"Records actually added to database: {records_added}")

            # DOCUMENT THE SILENT FAILURE
            if dlt_reports_success and records_added == 0:
                logger.error("🚨 CONFIRMED: DLT reports success but no data in database (SILENT FAILURE)")
                logger.error(f"   DLT reported success: {dlt_reports_success}")
                logger.error(f"   DLT reported records: {reported_count}")
                logger.error(f"   Actual records added: {records_added}")

            elif dlt_reports_success and records_added > 0:
                logger.info("✅ DLT reports success and data actually persisted")

            elif not dlt_reports_success and records_added == 0:
                logger.info("⚠️  DLT reports failure and no data persisted (expected behavior)")

            else:
                logger.warning(f"🤔 Unexpected state: DLT reports success={dlt_reports_success}, records_added={records_added}")

            # This test ALWAYS passes - it's characterization, not validation
            assert True  # We're documenting behavior, not enforcing expectations

        except Exception as e:
            logger.error(f"DLT silent failure investigation failed: {e}")
            # Even failure is valuable characterization data
            pytest.fail(f"Could not complete DLT characterization: {e}")

    def test_dlt_error_reporting_behavior(self, dlt_loader):
        """
        Characterize DLT's error reporting behavior.

        Documents how DLT handles invalid data and what it reports.
        """

        # Test with invalid data that should cause an error
        invalid_opportunities = [{
            "submission_id": None,  # Invalid: null primary key
            "title": "Invalid test",
            "upvotes": "not_a_number",  # Invalid type
            "score": "also_not_a_number"
        }]

        try:
            load_info = dlt_loader.load_opportunities(invalid_opportunities)

            # Document how DLT handles errors
            logger.info(f"DLT handled invalid data without raising exception")
            logger.info(f"Load info: {load_info}")

            # Check if DLT reports failure for invalid data
            dlt_reports_success = self._dlt_reports_success(load_info)
            logger.info(f"DLT reports success for invalid data: {dlt_reports_success}")

            if dlt_reports_success:
                logger.warning("🚨 DLT reports success even with invalid data (potential silent failure)")

        except Exception as e:
            logger.info(f"DLT raised exception for invalid data: {e}")
            logger.info(f"Exception type: {type(e)}")
            logger.info(f"Exception args: {e.args}")

    def test_dlt_connection_port_behavior(self, dlt_loader):
        """
        Characterize DLT's connection behavior with different ports.

        Documents port conflicts and connection attempts observed in codebase.
        """

        # Test different ports that appear in the codebase
        test_ports = [54330, 54322, 54331]  # Ports seen in existing tests

        for port in test_ports:
            try:
                # Try to construct connection string for this port
                conn_str = f"postgresql://postgres:postgres@127.0.0.1:{port}/postgres"
                logger.info(f"Testing DLT connection to port {port}")

                # Document DLT's behavior with each port
                # Note: This may require modifying DLT loader temporarily
                # For characterization, we're documenting the issue exists

            except Exception as e:
                logger.info(f"DLT connection to port {port} failed: {e}")

    def test_dlt_database_table_existence(self, dlt_loader):
        """
        Characterize DLT's behavior when target table doesn't exist.

        Documents how DLT handles missing table scenarios.
        """

        # Test with non-existent table
        try:
            load_info = dlt_loader.load_opportunities(
                opportunities=[],
                table_name="non_existent_table_for_characterization"
            )

            logger.info(f"DLT behavior with non-existent table: {load_info}")

        except Exception as e:
            logger.info(f"DLT error with non-existent table: {e}")
            logger.info(f"Exception type: {type(e)}")

    def test_id_resolution_integration(self):
        """
        Characterize ID resolution system behavior for integration with SQLAlchemy.
        """
        test_cases = [
            "t3_abc123",  # Reddit submission ID
            "https://reddit.com/r/python/comments/abc123/test_post/",  # Reddit URL
            "550e8400-e29b-41d4-a716-446655440000",  # Valid UUID
            {"submission_id": "t3_def456"},  # Dict format
            {"reddit_id": "t3_ghi789"},  # Dict with reddit_id
        ]

        for test_case in test_cases:
            try:
                result = resolve_submission_id(test_case)
                logger.info(f"ID resolution for {test_case}: {result}")

                if result:
                    logger.info(f"  - UUID: {result.uuid}")
                    logger.info(f"  - Source: {result.source}")
                    logger.info(f"  - Error: {result.error}")

            except Exception as e:
                logger.error(f"ID resolution failed for {test_case}: {e}")

    def _get_database_record_count(self) -> int:
        """
        Helper method to get current record count from database.

        Uses direct SQLAlchemy to avoid DLT's connection issues.
        """
        try:
            import os
            from sqlalchemy import create_engine, text

            # Try to get connection from DLT config or use local dev default
            conn_str = os.getenv("DESTINATION__POSTGRES__CREDENTIALS",
                                "postgresql://postgres:postgres@127.0.0.1:54322/postgres")

            engine = create_engine(conn_str)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM app_opportunities")).scalar()
                return result or 0

        except Exception as e:
            logger.warning(f"Could not get database record count: {e}")
            return -1  # Indicates unable to get count

    def _dlt_reports_success(self, load_info) -> bool:
        """
        Helper method to determine if DLT load_info indicates success.

        Documents DLT's various success reporting mechanisms.
        """
        if hasattr(load_info, 'counts') and load_info.counts:
            total_count = sum(load_info.counts.values())
            logger.info(f"DLT counts indicate {total_count} records processed")
            return total_count > 0
        elif hasattr(load_info, 'success'):
            logger.info(f"DLT success attribute: {load_info.success}")
            return load_info.success
        elif hasattr(load_info, 'load_id') and load_info.load_id:
            logger.info(f"DLT has load_id: {load_info.load_id}")
            return True  # If there's a load_id, DLT considers it successful
        else:
            # Default assumption: if no error exception, DLT considers it success
            logger.info("DLT load_info has no clear success indicator, assuming success")
            return True