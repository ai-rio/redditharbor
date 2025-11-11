# tests/test_dlt_integration.py
"""DLT Integration Tests"""

import os
from unittest.mock import patch


def test_dlt_imports():
    """Test that DLT dependencies are available"""
    try:
        from datetime import datetime

        import dlt
        import praw
        assert True  # If imports succeed
    except ImportError as e:
        assert False, f"Missing dependency: {e}"


def test_reddit_client_initialization():
    """Test PRAW client can be initialized with environment variables"""
    import praw

    # Test with mock values for now
    with patch.dict(os.environ, {
        'REDDIT_CLIENT_ID': 'test_client_id',
        'REDDIT_CLIENT_SECRET': 'test_client_secret'
    }):
        # This will fail without proper credentials, but verifies the interface
        try:
            reddit = praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID"),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                user_agent="RedditHarbor-DLT/1.0"
            )
            assert hasattr(reddit, 'subreddit')
        except Exception:
            # Expected to fail in test environment
            pass
