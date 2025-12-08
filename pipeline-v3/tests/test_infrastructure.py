"""
Test infrastructure for Pipeline v3 tests with comprehensive mocking
"""

import os
import sys
from types import ModuleType
from unittest.mock import MagicMock, Mock


def install_all_mocks():
    """Install all necessary mock modules for testing"""

    # Mock pydantic_settings
    mock_pydantic_settings = ModuleType('pydantic_settings')
    mock_base_settings = Mock()
    mock_pydantic_settings.BaseSettings = mock_base_settings
    sys.modules['pydantic_settings'] = mock_pydantic_settings

    # Mock pydantic
    mock_pydantic = ModuleType('pydantic')
    mock_pydantic.Field = lambda default=None, alias=None, description=None: default
    mock_pydantic.field_validator = lambda field_name: lambda func: func
    sys.modules['pydantic'] = mock_pydantic

    # Mock prawcore
    mock_prawcore = ModuleType('prawcore')
    mock_prawcore.ResponseException = Exception
    mock_prawcore.NotFound = Exception
    mock_prawcore.Forbidden = Exception
    sys.modules['prawcore'] = mock_prawcore

    # Mock praw
    mock_praw = create_mock_praw_module()
    sys.modules['praw'] = mock_praw
    sys.modules['praw.exceptions'] = mock_praw.exceptions
    sys.modules['praw.models'] = mock_praw.models
    sys.modules['praw.core'] = mock_praw.core

    # Mock config
    mock_config = create_mock_config_module()
    sys.modules['config'] = mock_config

    # Mock models
    mock_models = create_mock_models_module()
    sys.modules['models'] = mock_models

    return {
        'pydantic_settings': mock_pydantic_settings,
        'pydantic': mock_pydantic,
        'praw': mock_praw,
        'prawcore': mock_prawcore,
        'config': mock_config,
        'models': mock_models
    }


class MockAuthor:
    """Mock Reddit author object"""
    def __init__(self, name="testuser"):
        self.name = name

    def __str__(self):
        return self.name


class MockSubmission:
    """Mock PRAW Submission object"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 'test123')
        self.title = kwargs.get('title', 'Test Submission')
        self.selftext = kwargs.get('selftext', 'Test content')
        self.author = kwargs.get('author', MockAuthor(kwargs.get('author_name', 'testuser')))
        self.ups = kwargs.get('ups', 100)
        self.score = kwargs.get('score', 100)
        self._downs = kwargs.get('downs', 0)
        self.num_comments = kwargs.get('num_comments', 25)
        self.created_utc = kwargs.get('created_utc', 1640995200)
        self.permalink = kwargs.get('permalink', '/r/test/test123')
        self.url = kwargs.get('url', 'https://example.com')
        self.is_self = kwargs.get('is_self', True)
        self.over_18 = kwargs.get('over_18', False)

        # Setup subreddit
        if 'subreddit' in kwargs:
            self.subreddit = kwargs['subreddit']
        else:
            self.subreddit = Mock()
            self.subreddit.display_name = Mock()
            self.subreddit.display_name.lower = Mock(return_value='test')

    @property
    def downs(self):
        """Compatibility property"""
        return getattr(self, '_downs', 0)

    @downs.setter
    def downs(self, value):
        self._downs = value


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

        self._hot_submissions = kwargs.get('hot_submissions', [])
        self._new_submissions = kwargs.get('new_submissions', [])
        self._top_submissions = kwargs.get('top_submissions', [])

    def hot(self, limit=None):
        return self._hot_submissions[:limit] if limit else self._hot_submissions

    def new(self, limit=None):
        return self._new_submissions[:limit] if limit else self._new_submissions

    def top(self, time_filter='week', limit=None):
        return self._top_submissions[:limit] if limit else self._top_submissions

    @property
    def over18(self):
        """Compatibility property"""
        return self.over_18


class MockReddit:
    """Mock PRAW Reddit object"""
    def __init__(self, **kwargs):
        self.client_id = kwargs.get('client_id', 'test_id')
        self.client_secret = kwargs.get('client_secret', 'test_secret')
        self.user_agent = kwargs.get('user_agent', 'test_agent')

        self.user = Mock()
        self.user.me = Mock(return_value=Mock(username='testuser'))

        self._subreddits = {}

    def subreddit(self, name):
        if name not in self._subreddits:
            self._subreddits[name] = MockSubreddit(display_name=name)
        return self._subreddits[name]


class MockSettings:
    """Mock Settings object"""
    def __init__(self):
        self.reddit_client_id = "test_client_id"
        self.reddit_client_secret = "test_client_secret"
        self.reddit_user_agent = "test_agent"
        self.reddit_username = "test_user"
        self.reddit_password = "test_pass"
        self.supabase_url = "https://test.supabase.co"
        self.supabase_key = "test_key"


class MockRedditSubmission:
    """Mock RedditSubmission model"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 'test123')
        self.title = kwargs.get('title', 'Test Submission')
        self.text = kwargs.get('text', 'Test content')
        self.author = kwargs.get('author', 'testuser')
        self.upvotes = kwargs.get('upvotes', 100)
        self.downvotes = kwargs.get('downvotes', 0)
        self.score = kwargs.get('score', 100)
        self.comments_count = kwargs.get('comments_count', 25)
        self.subreddit = kwargs.get('subreddit', 'test')
        self.created_utc = kwargs.get('created_utc', '2022-01-01T00:00:00+00:00')
        self.permalink = kwargs.get('permalink', 'https://reddit.com/r/test/test123')
        self.url = kwargs.get('url', 'https://example.com')
        self.is_self = kwargs.get('is_self', True)
        self.over_18 = kwargs.get('over_18', False)


def create_mock_praw_module():
    """Create a mock praw module"""
    praw_module = ModuleType('praw')

    praw_module.exceptions = ModuleType('praw.exceptions')
    praw_module.exceptions.ResponseException = Exception
    praw_module.exceptions.NotFound = Exception
    praw_module.exceptions.Forbidden = Exception
    praw_module.Reddit = MockReddit

    praw_module.models = ModuleType('praw.models')
    praw_module.models.Submission = MockSubmission

    praw_module.core = ModuleType('praw.core')
    praw_module.core.ResponseException = Exception
    praw_module.core.NotFound = Exception
    praw_module.core.Forbidden = Exception

    return praw_module


def create_mock_config_module():
    """Create a mock config module"""
    config_module = ModuleType('config')

    settings = MockSettings()
    config_module.get_settings = Mock(return_value=settings)
    config_module.settings = settings

    return config_module


def create_mock_models_module():
    """Create a mock models module"""
    models_module = ModuleType('models')
    models_module.RedditSubmission = MockRedditSubmission

    return models_module


def setup_test_environment():
    """Setup complete test environment with all mocks"""
    return install_all_mocks()


if __name__ == "__main__":
    # Test the infrastructure
    mocks = setup_test_environment()
    print("✅ All test mocks installed successfully")

    # Test imports
    from extract.reddit_client import RedditClient
    client = RedditClient()
    print(f"✅ RedditClient created: {client.settings is not None}")

    from models import RedditSubmission
    submission = RedditSubmission(id="test", title="Test")
    print(f"✅ RedditSubmission created: {submission.id} - {submission.title}")
