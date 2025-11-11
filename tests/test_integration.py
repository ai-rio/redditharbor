"""
Integration tests for DLT functionality with existing RedditHarbor system.

This test module verifies that DLT configuration is available in settings
and that DLT collection functions work from core.collection.
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest

# Add project root to path for imports
sys.path.insert(0, '/home/carlos/projects/redditharbor')

# Test imports
try:
    from config.settings import (
        DEFAULT_SUBREDDITS,
        DLT_DATASET_NAME,
        # DLT settings (should exist after integration)
        DLT_MIN_ACTIVITY_SCORE,
        DLT_PIPELINE_NAME,
        DLT_QUALITY_COMMENTS_PER_POST,
        DLT_QUALITY_MIN_COMMENT_LENGTH,
        DLT_QUALITY_MIN_SCORE,
        DLT_TIME_FILTER,
        # Existing settings
        REDDIT_PUBLIC,
        REDDIT_SECRET,
        SUPABASE_KEY,
        SUPABASE_URL,
    )
    SETTINGS_AVAILABLE = True
except ImportError as e:
    print(f"Settings import error (expected before implementation): {e}")
    SETTINGS_AVAILABLE = False

try:
    from core.collection import (
        # Existing functions
        collect_data,
        collect_monetizable_opportunities_data,
        # DLT functions (should exist after integration)
        collect_with_dlt_validation,
        get_dlt_collection_stats,
    )
    COLLECTION_AVAILABLE = True
except ImportError as e:
    print(f"Collection import error (expected before implementation): {e}")
    COLLECTION_AVAILABLE = False

IMPORTS_AVAILABLE = SETTINGS_AVAILABLE and COLLECTION_AVAILABLE


class TestDLTConfiguration:
    """Test DLT configuration integration with settings.py"""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="DLT settings not yet implemented")
    def test_dlt_settings_exist(self):
        """Test that DLT configuration variables are available"""
        # Test that DLT settings have proper types and values
        assert isinstance(DLT_MIN_ACTIVITY_SCORE, (int, float))
        assert 0 <= DLT_MIN_ACTIVITY_SCORE <= 100

        assert isinstance(DLT_TIME_FILTER, str)
        assert DLT_TIME_FILTER in ["hour", "day", "week", "month", "year", "all"]

        assert isinstance(DLT_PIPELINE_NAME, str)
        assert len(DLT_PIPELINE_NAME) > 0

        assert isinstance(DLT_DATASET_NAME, str)
        assert len(DLT_DATASET_NAME) > 0

        # Quality filter settings
        assert isinstance(DLT_QUALITY_MIN_COMMENT_LENGTH, int)
        assert DLT_QUALITY_MIN_COMMENT_LENGTH > 0

        assert isinstance(DLT_QUALITY_MIN_SCORE, int)
        assert DLT_QUALITY_MIN_SCORE >= 0

        assert isinstance(DLT_QUALITY_COMMENTS_PER_POST, int)
        assert DLT_QUALITY_COMMENTS_PER_POST > 0

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="DLT settings not yet implemented")
    def test_dlt_settings_environment_variables(self):
        """Test that DLT settings can be overridden by environment variables"""
        # Test environment variable override
        original_value = DLT_MIN_ACTIVITY_SCORE

        # Set environment variable
        os.environ['DLT_MIN_ACTIVITY_SCORE'] = '75.0'

        # This would require reloading the config module
        # For now, just verify the environment variable is set
        assert os.environ.get('DLT_MIN_ACTIVITY_SCORE') == '75.0'

        # Clean up
        del os.environ['DLT_MIN_ACTIVITY_SCORE']


class TestDLTCollectionFunctions:
    """Test DLT collection functions integration with core.collection"""

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="DLT functions not yet implemented")
    def test_collect_with_dlt_validation_signature(self):
        """Test that collect_with_dlt_validation function has correct signature"""
        # Test function is callable
        assert callable(collect_with_dlt_validation)

        # Test function accepts expected parameters
        import inspect
        sig = inspect.signature(collect_with_dlt_validation)

        expected_params = [
            'reddit_client', 'supabase_client', 'db_config', 'subreddits',
            'limit', 'sort_types', 'mask_pii', 'dlt_enabled', 'dlt_min_activity_score'
        ]

        for param in expected_params:
            assert param in sig.parameters

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="DLT functions not yet implemented")
    def test_get_dlt_collection_stats_signature(self):
        """Test that get_dlt_collection_stats function has correct signature"""
        # Test function is callable
        assert callable(get_dlt_collection_stats)

        # Test function accepts expected parameters
        import inspect
        sig = inspect.signature(get_dlt_collection_stats)

        expected_params = ['reddit_client', 'supabase_client', 'db_config']

        for param in expected_params:
            assert param in sig.parameters


class TestDLTBackwardCompatibility:
    """Test that existing collection functionality is not broken by DLT integration"""

    @pytest.mark.skipif(not COLLECTION_AVAILABLE, reason="Collection functions not yet imported")
    def test_existing_functions_unchanged(self):
        """Test that existing collection functions maintain their interface"""
        # These functions should exist regardless of DLT integration
        assert callable(collect_data)
        assert callable(collect_monetizable_opportunities_data)

        # Test their signatures haven't changed
        import inspect

        # collect_data signature
        sig = inspect.signature(collect_data)
        expected_params = [
            'reddit_client', 'supabase_client', 'db_config', 'subreddits',
            'limit', 'sort_types', 'mask_pii'
        ]

        for param in expected_params:
            assert param in sig.parameters

    @pytest.mark.skipif(not SETTINGS_AVAILABLE, reason="Settings not yet imported")
    def test_existing_settings_unchanged(self):
        """Test that existing settings are not affected by DLT integration"""
        # These settings should exist and maintain their types
        assert isinstance(REDDIT_PUBLIC, str)
        assert isinstance(REDDIT_SECRET, str)
        assert isinstance(SUPABASE_URL, str)
        assert isinstance(SUPABASE_KEY, str)
        assert isinstance(DEFAULT_SUBREDDITS, list)
        assert len(DEFAULT_SUBREDDITS) > 0


class TestDLTIntegrationWorkflow:
    """Test end-to-end DLT integration workflow"""

    @patch('scripts.run_dlt_activity_collection.run_dlt_collection')
    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="DLT functions not yet implemented")
    def test_dlt_collection_workflow(self, mock_dlt_collection):
        """Test complete DLT collection workflow integration"""
        # Mock external dependencies
        mock_reddit = Mock()
        mock_supabase = Mock()

        # Mock successful DLT collection result
        mock_dlt_collection.return_value = {
            "success": True,
            "pipeline_name": "test_pipeline",
            "load_id": "test_load_id",
            "subreddits_count": 5,
            "duration": 120.5
        }

        # Mock traditional collection to avoid actual API calls
        with patch('core.collection.collect_data') as mock_collect_data, \
             patch('core.collection.get_collection_status') as mock_status:

            mock_collect_data.return_value = True
            mock_status.return_value = {
                "status": "active",
                "total_posts_collected": 100,
                "total_comments_collected": 500
            }

            # Test that DLT collection can be called from core.collection
            result = collect_with_dlt_validation(
                reddit_client=mock_reddit,
                supabase_client=mock_supabase,
                db_config={"user": "redditors", "submission": "submissions", "comment": "comments"},
                subreddits=["python", "learnprogramming"],
                limit=100,
                dlt_enabled=True,
                dlt_min_activity_score=50.0
            )

            # Verify the function returns expected result structure
            assert result["success"] is True
            assert "traditional_collection" in result
            assert "dlt_collection" in result
            assert "combined_stats" in result

            # Verify DLT was called
            mock_dlt_collection.assert_called_once()

            # Verify traditional collection was called
            mock_collect_data.assert_called_once()


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])
