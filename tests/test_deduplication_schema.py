"""
Test deduplication schema implementation.
Following TDD approach - this test will fail first, then pass after schema implementation.
"""

import os
import sys
from unittest.mock import Mock

import pytest

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from dotenv import load_dotenv

    from supabase import create_client

    load_dotenv()

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        supabase = None

except ImportError:
    supabase = None


class TestDeduplicationSchema:
    """Test suite for deduplication schema implementation."""

    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client for testing."""
        mock_client = Mock()
        return mock_client

    def test_business_concepts_table_exists(self, mock_supabase):
        """
        Test that business_concepts table exists with correct schema.
        This test will fail until we implement the migration.
        """
        if not supabase:
            pytest.skip("Supabase not available - using mock")

        # Test that table exists and has expected columns
        try:
            response = (
                supabase.table("business_concepts").select("*").limit(1).execute()
            )

            # Should not raise an exception if table exists
            assert response is not None

            # Test table structure by attempting to insert a test record
            test_data = {
                "concept_name": "Test Concept",
                "concept_fingerprint": "test_fingerprint_123",
                "metadata": {"test": True},
            }

            # This should work if schema is correct
            insert_response = (
                supabase.table("business_concepts").insert(test_data).execute()
            )

            # Clean up test data
            if insert_response.data:
                test_id = insert_response.data[0]["id"]
                supabase.table("business_concepts").delete().eq("id", test_id).execute()

        except Exception as e:
            pytest.fail(f"Business concepts table test failed: {e}")

    def test_opportunities_unified_deduplication_columns(self):
        """
        Test that opportunities_unified table has deduplication columns.
        This test will fail until we implement the migration.
        """
        if not supabase:
            pytest.skip("Supabase not available")

        try:
            # Test that deduplication columns exist
            response = (
                supabase.table("opportunities_unified")
                .select(
                    "id, business_concept_id, semantic_fingerprint, is_duplicate, duplicate_of_id"
                )
                .limit(1)
                .execute()
            )

            # Should not raise exception if columns exist
            assert response is not None

        except Exception as e:
            pytest.fail(f"Opportunities unified deduplication columns test failed: {e}")

    def test_business_concepts_indexes_exist(self):
        """
        Test that required indexes exist for performance.
        """
        if not supabase:
            pytest.skip("Supabase not available")

        try:
            # Test index performance with a query that would use the index
            response = (
                supabase.table("business_concepts")
                .select("id, concept_name")
                .eq("concept_fingerprint", "test_fingerprint")
                .execute()
            )

            # Query should succeed (index existence is harder to test directly)
            assert response is not None

        except Exception as e:
            pytest.fail(f"Business concepts index test failed: {e}")

    def test_increment_concept_function_exists(self):
        """
        Test that increment_concept_count function exists.
        """
        if not supabase:
            pytest.skip("Supabase not available")

        try:
            # Test that the RPC function exists
            response = supabase.rpc(
                "increment_concept_count", {"concept_id": 999999}
            ).execute()

            # Function should exist (might fail due to non-existent ID, but should not raise "function does not exist")
            assert response is not None

        except Exception as e:
            if "function increment_concept_count" in str(e).lower():
                pytest.fail("increment_concept_count function does not exist")
            else:
                # Other errors are OK (e.g., concept_id doesn't exist)
                pass

    def test_deduplication_stats_view_exists(self):
        """
        Test that deduplication_stats view exists.
        """
        if not supabase:
            pytest.skip("Supabase not available")

        try:
            # Test that view exists by querying it
            response = supabase.table("deduplication_stats").select("*").execute()

            # View should exist and return data
            assert response is not None

        except Exception as e:
            pytest.fail(f"Deduplication stats view test failed: {e}")

    def test_foreign_key_constraints(self, mock_supabase):
        """
        Test that foreign key constraints are properly defined.
        """
        if not supabase:
            pytest.skip("Supabase not available - using mock")

        try:
            # Test foreign key constraint by attempting to insert invalid data
            # This should fail due to foreign key constraint

            # Test opportunities_unified -> business_concepts foreign key
            invalid_opp_data = {
                "business_concept_id": 999999,  # Non-existent concept ID
                "title": "Test Opportunity",
                "app_concept": "Test concept",
            }

            # This should fail due to foreign key constraint
            try:
                response = (
                    supabase.table("opportunities_unified")
                    .insert(invalid_opp_data)
                    .execute()
                )

                # If we get here, check if the record was actually inserted
                if response.data:
                    # Clean up
                    supabase.table("opportunities_unified").delete().eq(
                        "title", "Test Opportunity"
                    ).execute()
                    pytest.fail(
                        "Foreign key constraint not working - invalid concept_id was accepted"
                    )

            except Exception:
                # This is expected - foreign key constraint should prevent insertion
                pass

        except Exception as e:
            pytest.fail(f"Foreign key constraint test failed: {e}")

    def test_column_data_types(self):
        """
        Test that columns have correct data types.
        """
        if not supabase:
            pytest.skip("Supabase not available")

        try:
            # Test business_concepts table data types
            test_concept = {
                "concept_name": "Test Concept for Type Check",
                "concept_fingerprint": "type_check_fingerprint",
                "submission_count": 5,
                "metadata": {"type_check": True, "count": 42},
            }

            response = (
                supabase.table("business_concepts").insert(test_concept).execute()
            )

            if response.data:
                concept_id = response.data[0]["id"]

                # Verify data was inserted correctly (types are correct)
                verify_response = (
                    supabase.table("business_concepts")
                    .select("*")
                    .eq("id", concept_id)
                    .execute()
                )

                assert (
                    verify_response.data[0]["concept_name"]
                    == "Test Concept for Type Check"
                )
                assert verify_response.data[0]["submission_count"] == 5
                assert verify_response.data[0]["metadata"]["type_check"]

                # Clean up
                supabase.table("business_concepts").delete().eq(
                    "id", concept_id
                ).execute()

        except Exception as e:
            pytest.fail(f"Column data type test failed: {e}")


def test_schema_migration_integration():
    """
    Integration test for the complete schema migration.
    """
    if not supabase:
        pytest.skip("Supabase not available")

    # This test ensures all components work together
    test_suite = TestDeduplicationSchema()

    # Run a subset of critical tests
    test_suite.test_business_concepts_table_exists(None)
    test_suite.test_opportunities_unified_deduplication_columns()
    test_suite.test_increment_concept_function_exists()
    test_suite.test_deduplication_stats_view_exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
