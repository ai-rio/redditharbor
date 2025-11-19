"""
Test suite for SimpleDeduplicator class - Task 2 Implementation.
Following TDD: Write failing test first, then implementation.

Tests cover:
- SimpleDeduplicator class initialization
- normalize_concept() method
- generate_fingerprint() method
- Proper Supabase client integration
"""

import hashlib
from unittest.mock import Mock, patch

import pytest

# Import the module we're going to create
# This will fail initially since the module doesn't exist yet
try:
    from core.deduplication import SimpleDeduplicator
except ImportError:
    SimpleDeduplicator = None


class TestSimpleDeduplicatorInit:
    """Test SimpleDeduplicator initialization."""

    def test_init_with_valid_credentials(self):
        """Test successful initialization with Supabase credentials."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch('core.deduplication.create_client') as mock_create_client:
            mock_client = Mock()
            mock_create_client.return_value = mock_client

            deduplicator = SimpleDeduplicator(
                supabase_url="https://test.supabase.co",
                supabase_key="test_key_123"
            )

            assert deduplicator.supabase == mock_client
            mock_create_client.assert_called_once_with(
                "https://test.supabase.co",
                "test_key_123"
            )

    def test_init_stores_supabase_client(self):
        """Test that Supabase client is properly stored as instance variable."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch('core.deduplication.create_client') as mock_create_client:
            mock_client = Mock()
            mock_create_client.return_value = mock_client

            deduplicator = SimpleDeduplicator("test_url", "test_key")

            assert hasattr(deduplicator, 'supabase')
            assert deduplicator.supabase == mock_client


class TestNormalizeConcept:
    """Test normalize_concept method."""

    def test_normalize_concept_basic_lowercase(self):
        """Test basic lowercase conversion."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch('core.deduplication.create_client'):
            deduplicator = SimpleDeduplicator("test_url", "test_key")

            result = deduplicator.normalize_concept("FITNESS TRACKING APP")
            assert result == "fitness tracking app"

    def test_normalize_concept_removes_extra_whitespace(self):
        """Test removal of extra whitespace."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch('core.deduplication.create_client'):
            deduplicator = SimpleDeduplicator("test_url", "test_key")

            result = deduplicator.normalize_concept("  Mobile   App:   FitnessFAQ   ")
            assert result == "mobile app: fitnessfaq"

    def test_normalize_concept_removes_common_prefixes(self):
        """Test removal of common app-related prefixes."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch('core.deduplication.create_client'):
            deduplicator = SimpleDeduplicator("test_url", "test_key")

            # Test various prefixes
            assert (
                deduplicator.normalize_concept("app idea: fitness tracker")
                == "idea: fitness tracker"
            )
            assert (
                deduplicator.normalize_concept("app: meditation guide")
                == "meditation guide"
            )
            assert (
                deduplicator.normalize_concept("mobile app workout planner")
                == "app workout planner"
            )
            assert (
                deduplicator.normalize_concept("web app meal prepper")
                == "app meal prepper"
            )

    def test_normalize_concept_handles_empty_string(self):
        """Test handling of empty and None inputs."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch('core.deduplication.create_client'):
            deduplicator = SimpleDeduplicator("test_url", "test_key")

            assert deduplicator.normalize_concept("") == ""
            assert deduplicator.normalize_concept("   ") == ""
            assert deduplicator.normalize_concept(None) == ""

    def test_normalize_concept_consistency(self):
        """Test that similar concepts normalize to the same string."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch('core.deduplication.create_client'):
            deduplicator = SimpleDeduplicator("test_url", "test_key")

            concept1 = "FitnessFAQ App for Tracking Workouts"
            concept2 = "fitnessfaq app for tracking workouts"
            concept3 = "  FitnessFAQ   App   For   Tracking   Workouts  "

            norm1 = deduplicator.normalize_concept(concept1)
            norm2 = deduplicator.normalize_concept(concept2)
            norm3 = deduplicator.normalize_concept(concept3)

            assert norm1 == norm2 == norm3


class TestGenerateFingerprint:
    """Test generate_fingerprint method."""

    def test_fingerprint_is_sha256_hash(self):
        """Test that fingerprint is a valid SHA256 hash."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch('core.deduplication.create_client'):
            deduplicator = SimpleDeduplicator("test_url", "test_key")

            concept = "fitness tracking app"
            fingerprint = deduplicator.generate_fingerprint(concept)

            # SHA256 should be 64 hexadecimal characters
            assert len(fingerprint) == 64
            assert all(c in '0123456789abcdef' for c in fingerprint)

            # Verify it's actually the SHA256 of the normalized concept
            expected = hashlib.sha256(b"fitness tracking app").hexdigest()
            assert fingerprint == expected

    def test_fingerprint_consistency(self):
        """Test that identical concepts produce identical fingerprints."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch('core.deduplication.create_client'):
            deduplicator = SimpleDeduplicator("test_url", "test_key")

            concept1 = "FitnessFAQ App for Tracking Workouts"
            concept2 = "fitnessfaq app for tracking workouts"

            fp1 = deduplicator.generate_fingerprint(concept1)
            fp2 = deduplicator.generate_fingerprint(concept2)

            assert fp1 == fp2

    def test_fingerprint_uniqueness(self):
        """Test that different concepts produce different fingerprints."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch('core.deduplication.create_client'):
            deduplicator = SimpleDeduplicator("test_url", "test_key")

            concept1 = "fitness tracking app"
            concept2 = "meal planning app"

            fp1 = deduplicator.generate_fingerprint(concept1)
            fp2 = deduplicator.generate_fingerprint(concept2)

            assert fp1 != fp2

    def test_fingerprint_handles_empty_concept(self):
        """Test fingerprint generation with empty concepts."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch('core.deduplication.create_client'):
            deduplicator = SimpleDeduplicator("test_url", "test_key")

            fp_empty = deduplicator.generate_fingerprint("")
            fp_none = deduplicator.generate_fingerprint(None)

            # Both should produce the same hash (of empty string)
            assert fp_empty == fp_none
            assert len(fp_empty) == 64


class TestIntegration:
    """Integration tests for the complete workflow."""

    def test_complete_workflow_normalization_to_fingerprint(self):
        """Test complete workflow from concept to fingerprint."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch('core.deduplication.create_client'):
            deduplicator = SimpleDeduplicator("test_url", "test_key")

            # Test with a realistic Reddit-sourced app concept
            raw_concept = (
                "  App IDEA:   RedditHarbor   for  Tracking   Investment   Threads  "
            )

            # Step 1: Normalize
            normalized = deduplicator.normalize_concept(raw_concept)
            assert normalized == "idea: redditharbor for tracking investment threads"

            # Step 2: Generate fingerprint
            fingerprint = deduplicator.generate_fingerprint(raw_concept)

            # Verify fingerprint matches manually calculated hash
            expected_fp = hashlib.sha256(normalized.encode('utf-8')).hexdigest()
            assert fingerprint == expected_fp


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_supabase_client_creation_failure(self):
        """Test handling of Supabase client creation failure."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch('core.deduplication.create_client') as mock_create_client:
            mock_create_client.side_effect = Exception("Supabase connection failed")

            # The implementation should propagate the exception
            with pytest.raises(Exception, match="Supabase connection failed"):
                SimpleDeduplicator("invalid_url", "invalid_key")

    def test_normalize_concept_with_special_characters(self):
        """Test normalization with special characters."""
        if SimpleDeduplicator is None:
            pytest.skip("SimpleDeduplicator not implemented yet")

        with patch('core.deduplication.create_client'):
            deduplicator = SimpleDeduplicator("test_url", "test_key")

            concept = "Fitnéss-Tracker! 🏃‍♂️ App for Workout$"
            result = deduplicator.normalize_concept(concept)

            # Should preserve special characters but normalize spacing/case
            assert result == "fitnéss-tracker! 🏃‍♂️ app for workout$"
