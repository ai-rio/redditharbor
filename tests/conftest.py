"""Shared pytest fixtures for unified pipeline testing."""
import pytest
from typing import Any, Dict
from unittest.mock import MagicMock


@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing."""
    client = MagicMock()
    client.table.return_value.select.return_value.execute.return_value.data = []
    return client


@pytest.fixture
def sample_submission() -> Dict[str, Any]:
    """Sample Reddit submission for testing."""
    return {
        "submission_id": "test123",
        "title": "I need an app to track my fitness goals",
        "content": "I wish there was an app that could help me...",
        "subreddit": "fitness",
        "author": "test_user",
        "score": 42,
        "created_utc": 1700000000,
        "url": "https://reddit.com/r/fitness/test123",
    }


@pytest.fixture
def sample_business_concept() -> Dict[str, Any]:
    """Sample business concept for testing."""
    return {
        "id": 1,
        "primary_submission_id": "test123",
        "concept_text": "Fitness tracking app",
        "has_agno_analysis": False,
        "has_profiler_analysis": False,
        "submission_count": 1,
    }


@pytest.fixture
def mock_profiler():
    """Mock EnhancedLLMProfiler for testing."""
    profiler = MagicMock()
    profiler.generate_profile.return_value = {
        "app_name": "FitTrack Pro",
        "core_functions": ["Track workouts", "Set goals", "View progress"],
        "value_proposition": "Simple fitness tracking for busy people",
    }
    return profiler


@pytest.fixture
def mock_opportunity_analyzer():
    """Mock OpportunityAnalyzerAgent for testing."""
    analyzer = MagicMock()
    analyzer.analyze.return_value = {
        "final_score": 75.5,
        "market_demand": 80,
        "technical_feasibility": 70,
        "monetization_potential": 75,
        "competitive_advantage": 65,
        "user_pain_intensity": 85,
    }
    return analyzer
