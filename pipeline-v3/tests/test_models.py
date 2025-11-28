"""
Tests for Pydantic data models
"""

import pytest
from datetime import datetime, UTC

from models.reddit import RedditSubmission
from models.analysis import AppIdea, MarketMetrics, AnalysisResult
from models.database import Opportunity


class TestRedditSubmission:
    """Test RedditSubmission model validation"""

    def test_valid_submission(self):
        """Test valid submission data"""
        submission = RedditSubmission(
            id="test123",
            title="Test Title",
            text="Test content",
            author="testuser",
            upvotes=100,
            score=100,
            comments_count=25,
            subreddit="test",
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/test/test123"
        )
        assert submission.id == "test123"
        assert submission.title == "Test Title"

    def test_invalid_permalink(self):
        """Test invalid permalink URL"""
        with pytest.raises(ValueError, match="permalink must be a valid Reddit URL"):
            RedditSubmission(
                id="test",
                title="Test",
                text="Content",
                author="user",
                upvotes=10,
                score=10,
                comments_count=5,
                subreddit="test",
                created_utc=datetime.now(UTC),
                permalink="invalid-url"
            )

    def test_future_timestamp(self):
        """Test future timestamp validation"""
        future_time = datetime.now(UTC).replace(year=2050)
        with pytest.raises(ValueError, match="created_utc cannot be in the future"):
            RedditSubmission(
                id="test",
                title="Test",
                text="Content",
                author="user",
                upvotes=10,
                score=10,
                comments_count=5,
                subreddit="test",
                created_utc=future_time,
                permalink="https://reddit.com/r/test/test123"
            )


class TestAppIdea:
    """Test AppIdea model validation"""

    def test_valid_app_idea(self):
        """Test valid app idea data"""
        idea = AppIdea(
            title="Productivity App",
            app_concept="A simple productivity tool for task management",
            problem_statement="People struggle with task organization",
            target_audience="Students and professionals",
            core_functions=["task tracking", "deadline reminders"]
        )
        assert len(idea.core_functions) == 2
        assert "task tracking" in idea.core_functions

    def test_too_many_functions(self):
        """Test validation fails with too many core functions"""
        with pytest.raises(ValueError, match="Core functions.*maximum.*3"):
            AppIdea(
                title="Complex App",
                app_concept="An app that does everything",
                problem_statement="Complex problems",
                target_audience="Everyone",
                core_functions=["func1", "func2", "func3", "func4", "func5"]
            )

    def test_duplicate_functions(self):
        """Test validation fails with duplicate functions"""
        with pytest.raises(ValueError, match="Core functions must be unique"):
            AppIdea(
                title="Duplicate App",
                app_concept="App with duplicate functions",
                problem_statement="Problem",
                target_audience="Users",
                core_functions=["task tracking", "Task Tracking", "TASK TRACKING"]
            )

    def test_invalid_function_length(self):
        """Test validation fails with invalid function length"""
        with pytest.raises(ValueError, match="Each core function must be.*5-100 characters"):
            AppIdea(
                title="Invalid App",
                app_concept="App with bad functions",
                problem_statement="Problem",
                target_audience="Users",
                core_functions=["hi", "this is a very long function description that exceeds the maximum allowed length and should fail validation"]
            )


class TestMarketMetrics:
    """Test MarketMetrics model validation"""

    def test_valid_metrics(self):
        """Test valid market metrics"""
        metrics = MarketMetrics(
            market_demand=75.0,
            pain_intensity=80.0,
            monetization_potential=70.0,
            competition_level=60.0,
            technical_feasibility=85.0
        )
        assert metrics.market_demand == 75.0
        assert all(0.0 <= value <= 100.0 for value in [
            metrics.market_demand, metrics.pain_intensity, metrics.monetization_potential,
            metrics.competition_level, metrics.technical_feasibility
        ])

    def test_invalid_scores(self):
        """Test validation fails with scores outside 0-100 range"""
        with pytest.raises(ValueError):
            MarketMetrics(
                market_demand=150.0,  # Invalid: > 100
                pain_intensity=80.0,
                monetization_potential=70.0,
                competition_level=60.0,
                technical_feasibility=85.0
            )

        with pytest.raises(ValueError):
            MarketMetrics(
                market_demand=75.0,
                pain_intensity=-10.0,  # Invalid: < 0
                monetization_potential=70.0,
                competition_level=60.0,
                technical_feasibility=85.0
            )


class TestAnalysisResult:
    """Test AnalysisResult model validation"""

    def test_valid_analysis(self):
        """Test valid analysis result"""
        idea = AppIdea(
            title="Test App",
            app_concept="A test application",
            problem_statement="A test problem",
            target_audience="Test users",
            core_functions=["test function"]
        )
        metrics = MarketMetrics(
            market_demand=70.0,
            pain_intensity=75.0,
            monetization_potential=80.0,
            competition_level=65.0,
            technical_feasibility=85.0
        )

        analysis = AnalysisResult(
            submission_id="test123",
            app_idea=idea,
            market_metrics=metrics,
            final_score=75.0,
            confidence_score=80.0,
            trust_level="HIGH"
        )
        assert analysis.final_score == 75.0
        assert analysis.trust_level == "HIGH"

    def test_invalid_trust_level(self):
        """Test validation fails with invalid trust level"""
        idea = AppIdea(
            title="Test App",
            app_concept="A test application",
            problem_statement="A test problem",
            target_audience="Test users",
            core_functions=["test function"]
        )
        metrics = MarketMetrics(
            market_demand=70.0,
            pain_intensity=75.0,
            monetization_potential=80.0,
            competition_level=65.0,
            technical_feasibility=85.0
        )

        with pytest.raises(ValueError, match="trust_level must be one of"):
            AnalysisResult(
                submission_id="test123",
                app_idea=idea,
                market_metrics=metrics,
                final_score=75.0,
                confidence_score=80.0,
                trust_level="INVALID"
            )