"""
Enhanced PRAW mocking infrastructure for extract tests
This module provides properly configured mocks for PRAW Reddit API functionality
"""

import sys
from types import ModuleType
from unittest.mock import Mock, MagicMock, PropertyMock
from datetime import datetime, UTC


class MockAuthor:
    """Mock Reddit author object"""
    def __init__(self, name="testuser"):
        self.name = name

    def __str__(self):
        return self.name


class MockSubmission:
    """Mock PRAW Submission object with all required attributes"""
    def __init__(self, **kwargs):
        # Core attributes
        self.id = kwargs.get('id', 'test123')
        self.title = kwargs.get('title', 'Test Submission')
        self.selftext = kwargs.get('selftext', 'Test content')
        self.author = kwargs.get('author', MockAuthor(kwargs.get('author_name', 'testuser')))

        # Voting and engagement
        self.ups = kwargs.get('ups', 100)
        self.score = kwargs.get('score', 100)
        self.downs = kwargs.get('downs', 0)
        self.num_comments = kwargs.get('num_comments', 25)

        # Metadata
        self.created_utc = kwargs.get('created_utc', 1640995200)
        self.permalink = kwargs.get('permalink', '/r/test/test123')
        self.url = kwargs.get('url', 'https://example.com')
        self.is_self = kwargs.get('is_self', True)
        self.over_18 = kwargs.get('over_18', False)

        # Subreddit (setup with proper display_name)
        if 'subreddit' in kwargs:
            self.subreddit = kwargs['subreddit']
        else:
            self.subreddit = Mock()
            self.subreddit.display_name = kwargs.get('subreddit_name', 'test')


class MockSubreddit:
    """Mock PRAW Subreddit object with proper method implementations"""
    def __init__(self, **kwargs):
        self.display_name = kwargs.get('display_name', 'test')
        self.title = kwargs.get('title', 'Test Subreddit')
        self.public_description = kwargs.get('public_description', 'A test subreddit')
        self.subscribers = kwargs.get('subscribers', 1000)
        self.active_user_count = kwargs.get('active_user_count', 100)
        self.created_utc = kwargs.get('created_utc', 1640995200)
        self.over_18 = kwargs.get('over_18', False)
        self.restricted = kwargs.get('restricted', False)

        # Setup submission collections
        self._hot_submissions = kwargs.get('hot_submissions', [])
        self._new_submissions = kwargs.get('new_submissions', [])
        self._top_submissions = kwargs.get('top_submissions', [])

    def hot(self, limit=None):
        """Return hot submissions"""
        if limit:
            return self._hot_submissions[:limit]
        return iter(self._hot_submissions)

    def new(self, limit=None):
        """Return new submissions"""
        if limit:
            return self._new_submissions[:limit]
        return iter(self._new_submissions)

    def top(self, time_filter='week', limit=None):
        """Return top submissions"""
        if limit:
            return self._top_submissions[:limit]
        return iter(self._top_submissions)


class MockReddit:
    """Mock PRAW Reddit object with proper setup"""
    def __init__(self, **kwargs):
        self.client_id = kwargs.get('client_id', 'test_id')
        self.client_secret = kwargs.get('client_secret', 'test_secret')
        self.user_agent = kwargs.get('user_agent', 'test_agent')

        # Setup user mock
        self.user = Mock()
        self.user.me = Mock(return_value=MockAuthor('testuser'))

        # Setup subreddit storage and factory
        self._subreddits = {}

        # Setup subreddit as a method that can be mocked properly
        self.subreddit = Mock(side_effect=self._get_subreddit)

    def _get_subreddit(self, name):
        """Internal method to get or create subreddit object"""
        if name not in self._subreddits:
            self._subreddits[name] = MockSubreddit(display_name=name)
        return self._subreddits[name]


class MockSettings:
    """Mock settings object"""
    def __init__(self):
        self.reddit_client_id = "test_client_id"
        self.reddit_client_secret = "test_client_secret"
        self.reddit_user_agent = "test_agent"
        self.supabase_url = "https://test.supabase.co"
        self.supabase_key = "test_key"


def create_comprehensive_praw_mocks():
    """Create comprehensive PRAW module mocks"""

    # Create mock prawcore
    mock_prawcore = ModuleType('prawcore')
    mock_prawcore.ResponseException = Exception
    mock_prawcore.NotFound = Exception
    mock_prawcore.Forbidden = Exception

    # Create mock praw
    mock_praw = ModuleType('praw')

    # Setup praw.exceptions
    mock_praw.exceptions = ModuleType('praw.exceptions')
    mock_praw.exceptions.ResponseException = Exception
    mock_praw.exceptions.NotFound = Exception
    mock_praw.exceptions.Forbidden = Exception

    # Setup praw.models
    mock_praw.models = ModuleType('praw.models')
    mock_praw.models.Submission = MockSubmission

    # Setup praw.core
    mock_praw.core = ModuleType('praw.core')
    mock_praw.core.ResponseException = Exception
    mock_praw.core.NotFound = Exception
    mock_praw.core.Forbidden = Exception

    # Set Reddit class constructor
    mock_praw.Reddit = MockReddit

    # Install into sys.modules
    sys.modules['prawcore'] = mock_prawcore
    sys.modules['praw'] = mock_praw
    sys.modules['praw.exceptions'] = mock_praw.exceptions
    sys.modules['praw.models'] = mock_praw.models
    sys.modules['praw.core'] = mock_praw.core

    return {
        'prawcore': mock_prawcore,
        'praw': mock_praw,
        'praw.exceptions': mock_praw.exceptions,
        'praw.models': mock_praw.models,
        'praw.core': mock_praw.core
    }


def create_mock_config():
    """Create mock config module"""
    mock_config = ModuleType('config')
    settings = MockSettings()
    mock_config.get_settings = Mock(return_value=settings)
    return mock_config


def create_mock_models():
    """Create mock models module"""
    mock_models = ModuleType('models')

    # Create a mock RedditSubmission that validates like the real one but works with mocks
    class RedditSubmission:
        """Mock RedditSubmission with validation behavior similar to real Pydantic model"""
        def __init__(self, **kwargs):
            # Validate required fields like the real RedditSubmission
            if 'id' not in kwargs or not kwargs['id'] or len(str(kwargs['id'])) < 3:
                raise ValueError("Invalid submission data: validation error")

            if 'title' not in kwargs or not kwargs['title'] or len(str(kwargs['title']).strip()) == 0:
                raise ValueError("Invalid submission data: validation error")

            if 'author' not in kwargs or not kwargs['author']:
                kwargs['author'] = "[deleted]"  # Handle missing author

            # Validate permalink format
            permalink = kwargs.get('permalink', '')
            if permalink and not (permalink.startswith('https://reddit.com/') or permalink.startswith('/r/')):
                raise ValueError("Invalid submission data: validation error")

            # Store all the data
            self.id = kwargs.get('id', 'test123')
            self.title = kwargs.get('title', 'Test Submission')
            self.text = kwargs.get('text', kwargs.get('selftext', 'Test content'))
            self.author = kwargs.get('author', 'testuser')
            self.upvotes = kwargs.get('upvotes', 100)
            self.downvotes = kwargs.get('downvotes', 0)
            self.score = kwargs.get('score', 100)
            self.comments_count = kwargs.get('comments_count', 25)
            self.subreddit = kwargs.get('subreddit', 'test')
            self.created_utc = kwargs.get('created_utc', datetime.now(UTC))
            self.permalink = kwargs.get('permalink', 'https://reddit.com/r/test/test123')
            self.url = kwargs.get('url', 'https://example.com')
            self.is_self = kwargs.get('is_self', True)
            self.over_18 = kwargs.get('over_18', False)

    mock_models.RedditSubmission = RedditSubmission
    return mock_models


def cleanup_extract_test_environment(original_modules=None):
    """Clean up mock environment to restore real modules"""
    if original_modules:
        # Restore original modules if provided
        for module_name, module in original_modules.items():
            if module is not None:
                sys.modules[module_name] = module
            elif module_name in sys.modules:
                del sys.modules[module_name]
    else:
        # Force reload of critical modules by removing them from cache
        modules_to_clean = [
            'pydantic', 'pydantic_settings', 'config', 'models',
            'config.settings', 'praw', 'prawcore'
        ]
        for module_name in modules_to_clean:
            if module_name in sys.modules:
                del sys.modules[module_name]


def setup_extract_test_environment():
    """Setup complete mock environment for extract tests"""

    # Store original modules before mocking
    original_modules = {
        'pydantic': sys.modules.get('pydantic'),
        'pydantic_settings': sys.modules.get('pydantic_settings'),
        'config': sys.modules.get('config'),
        'models': sys.modules.get('models'),
        'praw': sys.modules.get('praw'),
        'prawcore': sys.modules.get('prawcore')
    }

    # Install all mocks
    praw_mocks = create_comprehensive_praw_mocks()
    mock_config = create_mock_config()
    mock_models = create_mock_models()

    # Mock pydantic and pydantic_settings
    mock_pydantic_settings = ModuleType('pydantic_settings')
    mock_pydantic_settings.BaseSettings = Mock
    sys.modules['pydantic_settings'] = mock_pydantic_settings

    mock_pydantic = ModuleType('pydantic')
    mock_pydantic.Field = lambda default=None, alias=None, description=None: default
    mock_pydantic.field_validator = lambda field_name: lambda func: func
    mock_pydantic.BaseModel = Mock
    # CRITICAL: Add missing AliasChoices and AliasPath to prevent import errors
    mock_pydantic.AliasChoices = lambda *args: args[0] if args else None
    mock_pydantic.AliasPath = lambda *args: args[0] if args else None
    sys.modules['pydantic'] = mock_pydantic

    # Install config and models
    sys.modules['config'] = mock_config
    sys.modules['models'] = mock_models

    return {
        'praw': praw_mocks['praw'],
        'prawcore': praw_mocks['prawcore'],
        'config': mock_config,
        'models': mock_models,
        'pydantic': mock_pydantic,
        'pydantic_settings': mock_pydantic_settings,
        'original_modules': original_modules
    }


def create_mock_reddit_with_subreddits(subreddit_configs):
    """
    Helper to create a MockReddit with pre-configured subreddits

    Args:
        subreddit_configs: Dict mapping subreddit names to MockSubreddit instances

    Returns:
        MockReddit instance
    """
    mock_reddit = MockReddit()
    mock_reddit._subreddits = subreddit_configs.copy()
    return mock_reddit


# Export main classes for use in tests
__all__ = [
    'MockAuthor',
    'MockSubmission',
    'MockSubreddit',
    'MockReddit',
    'MockSettings',
    'setup_extract_test_environment',
    'cleanup_extract_test_environment',
    'create_comprehensive_praw_mocks',
    'create_mock_reddit_with_subreddits'
]