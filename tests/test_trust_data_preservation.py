"""Test trust data preservation in Phase 2 deduplication integration.

This test suite validates that trust scores and badges are preserved
when AI enrichment updates are made, preventing trust data loss.
"""

from unittest.mock import MagicMock, patch

import pytest

from core.storage.hybrid_store import HybridStore


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client."""
    client = MagicMock()
    return client


@pytest.fixture
def hybrid_store_with_client(mock_supabase):
    """Create HybridStore with mocked Supabase client."""
    return HybridStore(supabase_client=mock_supabase)


@pytest.fixture
def hybrid_store_without_client():
    """Create HybridStore without Supabase client."""
    return HybridStore(supabase_client=None)


@pytest.fixture
def sample_trust_data():
    """Sample trust data from database."""
    return {
        "sub_001": {
            "trust_score": 85.5,
            "trust_badge": "verified",
            "activity_score": 72.3,
            "trust_level": "high",
            "trust_badges": {"quality": True, "verified_user": True},
        },
        "sub_002": {
            "trust_score": 45.2,
            "trust_badge": "new",
            "activity_score": 30.1,
            "trust_level": "medium",
            "trust_badges": {"quality": False, "verified_user": False},
        },
    }


@pytest.fixture
def sample_submissions():
    """Sample submissions for testing."""
    return [
        {
            "submission_id": "sub_001",
            "problem_description": "Users struggle with task management",
            "app_concept": "AI-powered task organizer",
            "opportunity_score": 75.0,
            "title": "Need help with productivity",
            "author": "user1",
        },
        {
            "submission_id": "sub_002",
            "problem_description": "Teams waste time in meetings",
            "app_concept": "Smart meeting scheduler",
            "opportunity_score": 82.0,
            "title": "Too many useless meetings",
            "author": "user2",
        },
    ]


class TestFetchExistingTrustData:
    """Test batch fetching of existing trust data."""

    def test_fetch_with_existing_data(
        self, hybrid_store_with_client, sample_trust_data
    ):
        """Test fetching trust data for submissions with existing data."""
        # Mock database response
        mock_response = MagicMock()
        mock_response.data = [
            {
                "submission_id": "sub_001",
                "trust_score": 85.5,
                "trust_badge": "verified",
                "activity_score": 72.3,
                "trust_level": "high",
                "trust_badges": {"quality": True, "verified_user": True},
            },
            {
                "submission_id": "sub_002",
                "trust_score": 45.2,
                "trust_badge": "new",
                "activity_score": 30.1,
                "trust_level": "medium",
                "trust_badges": {"quality": False, "verified_user": False},
            },
        ]

        hybrid_store_with_client.supabase_client.table.return_value.select.return_value.in_.return_value.execute.return_value = mock_response

        # Fetch trust data
        trust_data = hybrid_store_with_client._fetch_existing_trust_data(
            ["sub_001", "sub_002"]
        )

        # Verify results
        assert len(trust_data) == 2
        assert trust_data["sub_001"]["trust_score"] == 85.5
        assert trust_data["sub_001"]["trust_badge"] == "verified"
        assert trust_data["sub_001"]["activity_score"] == 72.3
        assert trust_data["sub_002"]["trust_score"] == 45.2

    def test_fetch_with_no_existing_data(self, hybrid_store_with_client):
        """Test fetching trust data when no data exists."""
        # Mock empty database response
        mock_response = MagicMock()
        mock_response.data = []

        hybrid_store_with_client.supabase_client.table.return_value.select.return_value.in_.return_value.execute.return_value = mock_response

        # Fetch trust data
        trust_data = hybrid_store_with_client._fetch_existing_trust_data(["sub_001"])

        # Should return empty dict
        assert trust_data == {}

    def test_fetch_without_supabase_client(self, hybrid_store_without_client):
        """Test fetch gracefully handles missing Supabase client."""
        trust_data = hybrid_store_without_client._fetch_existing_trust_data(["sub_001"])

        # Should return empty dict without crashing
        assert trust_data == {}

    def test_fetch_with_empty_submission_list(self, hybrid_store_with_client):
        """Test fetch with empty submission ID list."""
        trust_data = hybrid_store_with_client._fetch_existing_trust_data([])

        # Should return empty dict
        assert trust_data == {}

    def test_fetch_with_database_error(self, hybrid_store_with_client):
        """Test fetch handles database errors gracefully."""
        # Mock database error
        hybrid_store_with_client.supabase_client.table.return_value.select.return_value.in_.return_value.execute.side_effect = Exception(
            "Database connection failed"
        )

        # Fetch should not crash
        trust_data = hybrid_store_with_client._fetch_existing_trust_data(["sub_001"])

        # Should return empty dict on error
        assert trust_data == {}

    def test_fetch_with_partial_data(self, hybrid_store_with_client):
        """Test fetch with only some submissions having trust data."""
        # Mock response with partial data
        mock_response = MagicMock()
        mock_response.data = [
            {
                "submission_id": "sub_001",
                "trust_score": 85.5,
                "trust_badge": "verified",
                "activity_score": None,  # Missing field
                "trust_level": "high",
                "trust_badges": None,  # Missing field
            }
        ]

        hybrid_store_with_client.supabase_client.table.return_value.select.return_value.in_.return_value.execute.return_value = mock_response

        # Fetch trust data
        trust_data = hybrid_store_with_client._fetch_existing_trust_data(
            ["sub_001", "sub_002"]
        )

        # Verify partial data
        assert len(trust_data) == 1
        assert trust_data["sub_001"]["trust_score"] == 85.5
        assert trust_data["sub_001"]["activity_score"] is None
        assert "sub_002" not in trust_data


class TestTrustDataPreservation:
    """Test trust data preservation during storage."""

    @patch.object(HybridStore, "_fetch_existing_trust_data")
    def test_preserve_trust_on_ai_update(
        self, mock_fetch, hybrid_store_with_client, sample_submissions
    ):
        """Test that trust data is preserved when AI fields are updated."""
        # Mock existing trust data
        mock_fetch.return_value = {
            "sub_001": {
                "trust_score": 85.5,
                "trust_badge": "verified",
                "activity_score": 72.3,
                "trust_level": "high",
                "trust_badges": {"quality": True},
            }
        }

        # Mock DLTLoader
        mock_loader = MagicMock()
        mock_loader.load.return_value = True
        hybrid_store_with_client.loader = mock_loader

        # Store submissions (AI update without trust data)
        hybrid_store_with_client.store(sample_submissions)

        # Verify that loader was called
        assert mock_loader.load.called

        # Get the opportunity data that was passed to loader
        call_args = mock_loader.load.call_args_list
        opportunities = None
        for call in call_args:
            if call[1].get("table_name") == "app_opportunities":
                opportunities = call[1]["data"]
                break

        # Verify trust data was preserved
        assert opportunities is not None
        sub_001_data = [o for o in opportunities if o["submission_id"] == "sub_001"][0]
        assert sub_001_data["trust_score"] == 85.5
        assert sub_001_data["trust_badge"] == "verified"
        assert sub_001_data["activity_score"] == 72.3
        assert sub_001_data["trust_level"] == "high"

    @patch.object(HybridStore, "_fetch_existing_trust_data")
    def test_new_trust_overrides_existing(
        self, mock_fetch, hybrid_store_with_client, sample_submissions
    ):
        """Test that new trust data overrides existing when provided."""
        # Mock existing trust data
        mock_fetch.return_value = {
            "sub_001": {
                "trust_score": 85.5,
                "trust_badge": "verified",
                "activity_score": 72.3,
                "trust_level": "high",
                "trust_badges": {"quality": True},
            }
        }

        # Mock DLTLoader
        mock_loader = MagicMock()
        mock_loader.load.return_value = True
        hybrid_store_with_client.loader = mock_loader

        # Add NEW trust data to submission (should override)
        sample_submissions[0]["trust_score"] = 95.0
        sample_submissions[0]["trust_badge"] = "premium"

        # Store submissions
        hybrid_store_with_client.store(sample_submissions)

        # Get the opportunity data
        call_args = mock_loader.load.call_args_list
        opportunities = None
        for call in call_args:
            if call[1].get("table_name") == "app_opportunities":
                opportunities = call[1]["data"]
                break

        # Verify NEW trust data was used (not old)
        sub_001_data = [o for o in opportunities if o["submission_id"] == "sub_001"][0]
        assert sub_001_data["trust_score"] == 95.0
        assert sub_001_data["trust_badge"] == "premium"

    @patch.object(HybridStore, "_fetch_existing_trust_data")
    def test_no_trust_preservation_without_client(
        self, mock_fetch, hybrid_store_without_client, sample_submissions
    ):
        """Test that store works without client (no trust preservation)."""
        # Mock fetch should return empty dict
        mock_fetch.return_value = {}

        # Mock DLTLoader
        mock_loader = MagicMock()
        mock_loader.load.return_value = True
        hybrid_store_without_client.loader = mock_loader

        # Store should still work
        result = hybrid_store_without_client.store(sample_submissions)

        # Should succeed even without trust preservation
        assert result is True
        assert mock_loader.load.called

    @patch.object(HybridStore, "_fetch_existing_trust_data")
    def test_partial_trust_fields_preserved(
        self, mock_fetch, hybrid_store_with_client, sample_submissions
    ):
        """Test preservation of partial trust fields."""
        # Mock existing trust data with only some fields
        mock_fetch.return_value = {
            "sub_001": {
                "trust_score": 85.5,
                "trust_badge": None,  # Missing
                "activity_score": 72.3,
                "trust_level": None,  # Missing
                "trust_badges": {"quality": True},
            }
        }

        # Mock DLTLoader
        mock_loader = MagicMock()
        mock_loader.load.return_value = True
        hybrid_store_with_client.loader = mock_loader

        # Store submissions
        hybrid_store_with_client.store(sample_submissions)

        # Get the opportunity data
        call_args = mock_loader.load.call_args_list
        opportunities = None
        for call in call_args:
            if call[1].get("table_name") == "app_opportunities":
                opportunities = call[1]["data"]
                break

        # Verify partial preservation
        sub_001_data = [o for o in opportunities if o["submission_id"] == "sub_001"][0]
        assert sub_001_data["trust_score"] == 85.5  # Preserved
        assert sub_001_data["trust_badge"] is None  # Was None
        assert sub_001_data["activity_score"] == 72.3  # Preserved


class TestTrustDataIntegration:
    """Integration tests for trust data preservation."""

    @patch.object(HybridStore, "_fetch_existing_trust_data")
    def test_full_pipeline_with_trust_preservation(
        self, mock_fetch, hybrid_store_with_client
    ):
        """Test complete pipeline with trust preservation."""
        # Mock existing trust data
        mock_fetch.return_value = {
            "sub_001": {
                "trust_score": 85.5,
                "trust_badge": "verified",
                "activity_score": 72.3,
                "trust_level": "high",
                "trust_badges": {"quality": True, "verified_user": True},
            }
        }

        # Mock DLTLoader
        mock_loader = MagicMock()
        mock_loader.load.return_value = True
        hybrid_store_with_client.loader = mock_loader

        # Create submission with AI enrichment but no trust data
        submissions = [
            {
                "submission_id": "sub_001",
                "problem_description": "Users need better productivity tools",
                "app_concept": "AI task manager",
                "opportunity_score": 75.0,
                "ai_profile": {"segment": "B2B", "urgency": "high"},
                # NO trust fields provided
            }
        ]

        # Store submissions
        result = hybrid_store_with_client.store(submissions)

        # Verify success
        assert result is True

        # Verify fetch was called
        mock_fetch.assert_called_once()

        # Verify trust data was preserved in storage
        call_args = mock_loader.load.call_args_list
        opportunities = None
        for call in call_args:
            if call[1].get("table_name") == "app_opportunities":
                opportunities = call[1]["data"]
                break

        assert opportunities is not None
        assert len(opportunities) == 1
        assert opportunities[0]["trust_score"] == 85.5
        assert opportunities[0]["trust_badge"] == "verified"
        assert opportunities[0]["activity_score"] == 72.3
        assert opportunities[0]["trust_level"] == "high"

    def test_statistics_tracking_with_trust_preservation(
        self, hybrid_store_with_client
    ):
        """Test that statistics tracking works with trust preservation."""
        # Mock DLTLoader
        mock_loader = MagicMock()
        mock_loader.load.return_value = True
        hybrid_store_with_client.loader = mock_loader

        # Mock fetch
        with patch.object(
            hybrid_store_with_client, "_fetch_existing_trust_data"
        ) as mock_fetch:
            mock_fetch.return_value = {}

            submissions = [
                {
                    "submission_id": "sub_001",
                    "problem_description": "Test",
                    "app_concept": "Test app",
                }
            ]

            # Store
            hybrid_store_with_client.store(submissions)

            # Check statistics
            stats = hybrid_store_with_client.get_statistics()
            assert stats["loaded"] == 1
            assert stats["total_attempted"] == 1


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @patch.object(HybridStore, "_fetch_existing_trust_data")
    def test_empty_trust_data_dict(
        self, mock_fetch, hybrid_store_with_client, sample_submissions
    ):
        """Test handling of empty trust data dict."""
        mock_fetch.return_value = {}

        # Mock DLTLoader
        mock_loader = MagicMock()
        mock_loader.load.return_value = True
        hybrid_store_with_client.loader = mock_loader

        # Should not crash
        result = hybrid_store_with_client.store(sample_submissions)
        assert result is True

    def test_store_with_no_submissions(self, hybrid_store_with_client):
        """Test store with empty submission list."""
        result = hybrid_store_with_client.store([])
        assert result is False

    @patch.object(HybridStore, "_fetch_existing_trust_data")
    def test_mixed_submission_ids(self, mock_fetch, hybrid_store_with_client):
        """Test handling of mixed submission_id and reddit_id."""
        mock_fetch.return_value = {
            "sub_001": {"trust_score": 85.5},
            "sub_002": {"trust_score": 75.0},
        }

        # Mock DLTLoader
        mock_loader = MagicMock()
        mock_loader.load.return_value = True
        hybrid_store_with_client.loader = mock_loader

        # Mixed submissions
        submissions = [
            {
                "submission_id": "sub_001",
                "problem_description": "Test 1",
                "app_concept": "App 1",
            },
            {
                "reddit_id": "sub_002",  # Uses reddit_id instead
                "problem_description": "Test 2",
                "app_concept": "App 2",
            },
        ]

        result = hybrid_store_with_client.store(submissions)
        assert result is True
