"""
Mock PRAW module for testing RedditClient functionality without actual PRAW installation
"""

import sys
from unittest.mock import Mock, MagicMock
from types import ModuleType


class MockSubmission:
    """Mock PRAW Submission object"""
    def __init__(self, **kwargs):
        # Default attributes
        self.id = kwargs.get('id', 'test123')
        self.title = kwargs.get('title', 'Test Submission')
        self.selftext = kwargs.get('selftext', 'Test content')
        self.author = kwargs.get('author', Mock())
        self.ups = kwargs.get('ups', 100)
        self.score = kwargs.get('score', 100)
        self.downs = kwargs.get('downs', 0)
        self.num_comments = kwargs.get('num_comments', 25)
        self.created_utc = kwargs.get('created_utc', 1640995200)
        self.permalink = kwargs.get('permalink', '/r/test/test123')
        self.url = kwargs.get('url', 'https://example.com')
        self.is_self = kwargs.get('is_self', True)
        self.over_18 = kwargs.get('over_18', False)

        # Mock subreddit
        self.subreddit = kwargs.get('subreddit', Mock())
        if hasattr(self.subreddit, 'display_name') is False:
            self.subreddit.display_name = Mock()
            self.subreddit.display_name.lower = Mock(return_value='test')

        # Setup author string representation
        if hasattr(self.author, '__str__') is False:
            self.author.__str__ = lambda: kwargs.get('author_name', 'testuser')


class MockSubreddit:
    """Mock PRAW Subreddit object"""
    def __init__(self, **kwargs):
        self.display_name = kwargs.get('display_name', 'test')
        self.title = kwargs.get('title', 'Test Subreddit')
        self.public_description = kwargs.get('public_description', 'A test subreddit')
        self.subscribers = kwargs.get('subscribers', 1000)
        self.active_user_count = kwargs.get('active_user_count', 100)
        self.created_utc = kwargs.get('created_utc', 1640995200)
        self.over_18 = kwargs.get('over_18', False)
        self.restricted = kwargs.get('restricted', False)

        # Setup submission lists
        self._hot_submissions = kwargs.get('hot_submissions', [])
        self._new_submissions = kwargs.get('new_submissions', [])
        self._top_submissions = kwargs.get('top_submissions', [])

    def hot(self, limit=None):
        """Return hot submissions"""
        return self._hot_submissions[:limit] if limit else self._hot_submissions

    def new(self, limit=None):
        """Return new submissions"""
        return self._new_submissions[:limit] if limit else self._new_submissions

    def top(self, time_filter='week', limit=None):
        """Return top submissions"""
        return self._top_submissions[:limit] if limit else self._top_submissions


class MockReddit:
    """Mock PRAW Reddit object"""
    def __init__(self, **kwargs):
        self.client_id = kwargs.get('client_id', 'test_id')
        self.client_secret = kwargs.get('client_secret', 'test_secret')
        self.user_agent = kwargs.get('user_agent', 'test_agent')

        # Setup user mock
        self.user = Mock()
        self.user.me = Mock(return_value=Mock(username='testuser'))

        # Setup subreddit factory
        self._subreddits = {}

    def subreddit(self, name):
        """Get subreddit object"""
        if name not in self._subreddits:
            self._subreddits[name] = MockSubreddit(display_name=name)
        return self._subreddits[name]


def create_mock_praw_module():
    """Create a mock praw module"""
    praw_module = ModuleType('praw')

    # Add exceptions
    praw_module.exceptions = ModuleType('praw.exceptions')
    praw_module.exceptions.ResponseException = Exception
    praw_module.exceptions.NotFound = Exception
    praw_module.exceptions.Forbidden = Exception
    praw_module.Reddit = MockReddit

    # Add models
    praw_module.models = ModuleType('praw.models')
    praw_module.models.Submission = MockSubmission

    # Add core
    praw_module.core = ModuleType('praw.core')
    praw_module.core.ResponseException = Exception
    praw_module.core.NotFound = Exception
    praw_module.core.Forbidden = Exception

    return praw_module


def create_mock_prawcore_module():
    """Create a mock prawcore module"""
    prawcore_module = ModuleType('prawcore')

    # Add exceptions
    prawcore_module.ResponseException = Exception
    prawcore_module.NotFound = Exception
    prawcore_module.Forbidden = Exception

    return prawcore_module


def install_mock_praw():
    """Install mock praw module into sys.modules"""
    mock_praw = create_mock_praw_module()
    mock_prawcore = create_mock_prawcore_module()

    sys.modules['praw'] = mock_praw
    sys.modules['praw.exceptions'] = mock_praw.exceptions
    sys.modules['praw.models'] = mock_praw.models
    sys.modules['praw.core'] = mock_praw.core
    sys.modules['prawcore'] = mock_prawcore

    return mock_praw


if __name__ == "__main__":
    # Test the mock
    install_mock_praw()
    import praw

    # Test Reddit creation
    reddit = praw.Reddit(client_id='test', client_secret='test', user_agent='test')
    print(f"Created mock Reddit: {reddit.client_id}")

    # Test subreddit
    subreddit = reddit.subreddit('test')
    print(f"Created mock subreddit: {subreddit.display_name}")

    # Test submission
    submission = MockSubmission(id='abc123', title='Test')
    print(f"Created mock submission: {submission.id} - {submission.title}")