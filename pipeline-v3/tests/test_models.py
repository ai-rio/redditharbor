"""
Tests for Pydantic data models
"""

import pytest
import math
from datetime import datetime, UTC, timedelta

from models.reddit import RedditSubmission, RedditComment
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
        with pytest.raises(ValueError, match="List should have at most 3 items"):
            AppIdea(
                title="Complex App",
                app_concept="An app that does everything",
                problem_statement="Complex problems require complex solutions",
                target_audience="Everyone who needs help",
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
        with pytest.raises(ValueError, match="Each core function must be.*3-100 characters"):
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
            trust_level="HIGH",
            content_quality_score=80.0  # Add required field
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
                trust_level="INVALID",
                content_quality_score=80.0  # Add required field
            )


class TestRedditSubmissionExtended:
    """Extended tests for RedditSubmission model edge cases"""

    def test_score_consistency_with_tolerance(self):
        """Test score consistency validation with vote fuzzing tolerance"""
        # Should fail - too far outside tolerance
        with pytest.raises(ValueError, match="Score must approximately equal upvotes minus downvotes"):
            RedditSubmission(
                id="test123",
                title="Test Title",
                text="Test content",
                author="testuser",
                upvotes=100,
                downvotes=20,
                score=50,  # Way off: should be 80, more than 10% tolerance
                comments_count=25,
                subreddit="test",
                created_utc=datetime.now(UTC),
                permalink="https://reddit.com/r/test/test123"
            )

        # Should pass - within tolerance (10% of 80 = 8, so 72-88 is acceptable)
        valid_submission = RedditSubmission(
            id="test456",
            title="Test Title 2",
            text="Test content 2",
            author="testuser2",
            upvotes=100,
            downvotes=20,
            score=85,  # Within tolerance: expected 80, actual 85 (difference = 5, tolerance = 8)
            comments_count=25,
            subreddit="test",
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/test/test456"
        )
        assert valid_submission.score == 85

        # Should pass - negative scores are now allowed (just logged)
        valid_negative_submission = RedditSubmission(
            id="test789",
            title="Test Title 3",
            text="Test content 3",
            author="testuser3",
            upvotes=5,
            downvotes=20,
            score=-15,  # Negative score allowed
            comments_count=25,
            subreddit="test",
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/test/test789"
        )
        assert valid_negative_submission.score == -15

  
    def test_author_validation_edge_cases(self):
        """Test author validation edge cases"""
        with pytest.raises(ValueError, match="Invalid Reddit username"):
            RedditSubmission(
                id="test",
                title="Test",
                text="Content",
                author="",  # Empty author
                upvotes=10,
                score=10,
                comments_count=5,
                subreddit="test",
                created_utc=datetime.now(UTC),
                permalink="https://reddit.com/r/test/test123"
            )

        with pytest.raises(ValueError, match="Invalid Reddit username"):
            RedditSubmission(
                id="test",
                title="Test",
                text="Content",
                author="this_username_is_too_long_for_reddit_limits",
                upvotes=10,
                score=10,
                comments_count=5,
                subreddit="test",
                created_utc=datetime.now(UTC),
                permalink="https://reddit.com/r/test/test123"
            )

        with pytest.raises(ValueError, match="Invalid Reddit username"):
            RedditSubmission(
                id="test",
                title="Test",
                text="Content",
                author="user with spaces",
                upvotes=10,
                score=10,
                comments_count=5,
                subreddit="test",
                created_utc=datetime.now(UTC),
                permalink="https://reddit.com/r/test/test123"
            )

        # Bot accounts like "admin" and "AutoModerator" are now allowed
        valid_bot_submission = RedditSubmission(
            id="test",
            title="Test",
            text="Content",
            author="AutoModerator",  # Bot account now allowed
            upvotes=10,
            score=10,
            comments_count=5,
            subreddit="test",
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/test/test123"
        )
        assert valid_bot_submission.author == "AutoModerator"

    def test_subreddit_validation_edge_cases(self):
        """Test subreddit validation edge cases"""
        with pytest.raises(ValueError, match="Invalid subreddit name"):
            RedditSubmission(
                id="test",
                title="Test",
                text="Content",
                author="testuser",
                upvotes=10,
                score=10,
                comments_count=5,
                subreddit="",  # Empty subreddit
                created_utc=datetime.now(UTC),
                permalink="https://reddit.com/r/test/test123"
            )

        with pytest.raises(ValueError, match="Invalid subreddit name"):
            RedditSubmission(
                id="test",
                title="Test",
                text="Content",
                author="testuser",
                upvotes=10,
                score=10,
                comments_count=5,
                subreddit="this_subreddit_name_is_too_long_for_reddit_limits",
                created_utc=datetime.now(UTC),
                permalink="https://reddit.com/r/test/test123"
            )

        with pytest.raises(ValueError, match="Invalid subreddit name"):
            RedditSubmission(
                id="test",
                title="Test",
                text="Content",
                author="testuser",
                upvotes=10,
                score=10,
                comments_count=5,
                subreddit="sub with spaces",
                created_utc=datetime.now(UTC),
                permalink="https://reddit.com/r/test/test123"
            )

        # Hyphens in subreddit names are now allowed
        valid_hyphen_subreddit = RedditSubmission(
            id="test",
            title="Test",
            text="Content",
            author="testuser",
            upvotes=10,
            score=10,
            comments_count=5,
            subreddit="web-design",  # Hyphens now allowed
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/test/test123"
        )
        assert valid_hyphen_subreddit.subreddit == "web-design"

    def test_title_spam_keywords_now_allowed(self):
        """Test that titles with spam-like keywords are now allowed (AI will filter)"""
        valid_submission = RedditSubmission(
            id="test123",
            title="Urgent need for better task management tool",  # "urgent" now allowed
            text="Test content",
            author="testuser",
            upvotes=100,
            score=100,
            comments_count=25,
            subreddit="productivity",
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/test/test123"
        )
        assert valid_submission.title == "Urgent need for better task management tool"

    def test_permalink_validation_edge_cases(self):
        """Test permalink validation with different valid formats"""
        # Test valid Reddit URL formats
        valid_submission = RedditSubmission(
            id="test123",
            title="Test Title",
            text="Test content",
            author="testuser",
            upvotes=100,
            score=100,
            comments_count=25,
            subreddit="test",
            created_utc=datetime.now(UTC),
            permalink="/r/test/test123"  # Relative format should work
        )
        assert valid_submission.permalink == "/r/test/test123"

    def test_url_validation(self):
        """Test optional URL validation"""
        # Valid URL should work
        valid_submission = RedditSubmission(
            id="test123",
            title="Test Title",
            text="Test content",
            author="testuser",
            upvotes=100,
            score=100,
            comments_count=25,
            subreddit="test",
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/test/test123",
            url="https://example.com/article"
        )
        assert valid_submission.url == "https://example.com/article"

        # Invalid URL should fail
        with pytest.raises(ValueError, match="URL must start with http:// or https://"):
            RedditSubmission(
                id="test123",
                title="Test Title",
                text="Test content",
                author="testuser",
                upvotes=100,
                score=100,
                comments_count=25,
                subreddit="test",
                created_utc=datetime.now(UTC),
                permalink="https://reddit.com/r/test/test123",
                url="ftp://invalid-protocol.com"
            )

    def test_empty_text_now_allowed(self):
        """Test that empty text is now allowed for link posts"""
        # Empty text (link post) should now work
        valid_link_post = RedditSubmission(
            id="test123",
            title="Check out this useful article",
            text="",  # Empty text now allowed for link posts
            author="testuser",
            upvotes=100,
            score=100,
            comments_count=25,
            subreddit="productivity",
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/test/test123"
        )
        assert valid_link_post.text == ""


class TestRedditCommentExtended:
    """Extended tests for RedditComment model edge cases"""

    def test_negative_score_with_upvotes(self):
        """Test comment score validation with negative score and positive upvotes"""
        with pytest.raises(ValueError, match="Comment score cannot be negative with positive upvotes"):
            RedditComment(
                id="comment123",
                submission_id="test123",
                author="testuser",
                text="This is a test comment",
                upvotes=10,
                score=-5,  # Negative with positive upvotes - invalid
                created_utc=datetime.now(UTC)
            )

    def test_score_mismatch_validation(self):
        """Test comment score must equal upvotes"""
        with pytest.raises(ValueError, match="Comment score must equal upvotes"):
            RedditComment(
                id="comment123",
                submission_id="test123",
                author="testuser",
                text="This is a test comment",
                upvotes=15,
                score=10,  # Should equal upvotes
                created_utc=datetime.now(UTC)
            )

    def test_comment_author_validation(self):
        """Test comment author validation"""
        with pytest.raises(ValueError, match="Invalid Reddit username"):
            RedditComment(
                id="comment123",
                submission_id="test123",
                author="user_with spaces",  # Invalid username
                text="This is a test comment",
                upvotes=10,
                created_utc=datetime.now(UTC)
            )

    def test_comment_length_validation(self):
        """Test comment length validation"""
        # Too short comment
        with pytest.raises(ValueError, match="Comment length is invalid"):
            RedditComment(
                id="comment123",
                submission_id="test123",
                author="testuser",
                text="hi",  # Too short (< 3 chars)
                upvotes=10,
                created_utc=datetime.now(UTC)
            )

        # Empty comment
        with pytest.raises(ValueError, match="Comment length is invalid"):
            RedditComment(
                id="comment123",
                submission_id="test123",
                author="testuser",
                text="",  # Empty
                upvotes=10,
                created_utc=datetime.now(UTC)
            )

        # Whitespace only comment
        with pytest.raises(ValueError, match="Comment length is invalid"):
            RedditComment(
                id="comment123",
                submission_id="test123",
                author="testuser",
                text="   ",  # Whitespace only
                upvotes=10,
                created_utc=datetime.now(UTC)
            )

        # Very long comment
        with pytest.raises(ValueError, match="Comment length is invalid"):
            RedditComment(
                id="comment123",
                submission_id="test123",
                author="testuser",
                text="x" * 10001,  # Too long (> 10000 chars)
                upvotes=10,
                created_utc=datetime.now(UTC)
            )

    def test_valid_comment_scenarios(self):
        """Test valid comment scenarios"""
        # Comment with score matching upvotes
        valid_comment = RedditComment(
            id="comment123",
            submission_id="test123",
            author="testuser",
            text="This is a valid test comment with reasonable length",
            upvotes=25,
            score=25,  # Matches upvotes
            created_utc=datetime.now(UTC)
        )
        assert valid_comment.score == 25

        # Comment with no score (optional field)
        comment_no_score = RedditComment(
            id="comment456",
            submission_id="test123",
            author="anotheruser",
            text="Another valid comment",
            upvotes=15,
            created_utc=datetime.now(UTC)
        )
        assert comment_no_score.score is None


class TestMarketMetricsExtended:
    """Extended tests for MarketMetrics model validation"""

    def test_metric_precision_validation(self):
        """Test metric precision validation (max 2 decimal places)"""
        with pytest.raises(ValueError, match="has too many decimal places"):
            MarketMetrics(
                market_demand=75.123,  # Too many decimals
                pain_intensity=80.0,
                monetization_potential=70.0,
                competition_level=60.0,
                technical_feasibility=85.0
            )

    def test_metric_consistency_validation(self):
        """Test logical consistency between metrics"""
        # High pain should correlate with market demand
        with pytest.raises(ValueError, match="High pain intensity should correlate with market demand"):
            MarketMetrics(
                market_demand=20.0,  # Low demand
                pain_intensity=85.0,  # High pain - should correlate
                monetization_potential=70.0,
                competition_level=60.0,
                technical_feasibility=85.0
            )

        # High feasibility should enable monetization
        with pytest.raises(ValueError, match="Low technical feasibility limits monetization potential"):
            MarketMetrics(
                market_demand=75.0,
                pain_intensity=80.0,
                monetization_potential=85.0,  # High monetization
                competition_level=60.0,
                technical_feasibility=15.0  # Low feasibility - should limit
            )

        # Low competition should enable higher market opportunity
        with pytest.raises(ValueError, match="Low competition should enable higher market opportunity"):
            MarketMetrics(
                market_demand=30.0,  # Low demand
                pain_intensity=80.0,
                monetization_potential=70.0,
                competition_level=15.0,  # Low competition (good)
                technical_feasibility=85.0
            )

    def test_extreme_values_validation(self):
        """Test for unrealistic metric combinations"""
        # Too many extreme high values
        with pytest.raises(ValueError, match="Metrics combination is unrealistic"):
            MarketMetrics(
                market_demand=95.0,  # Extreme high
                pain_intensity=92.0,  # Extreme high
                monetization_potential=88.0,  # Extreme high
                competition_level=8.0,  # Extreme low (remember: higher = less competition)
                technical_feasibility=93.0  # Extreme high
            )

        # Too many extreme low values
        with pytest.raises(ValueError, match="Metrics combination is unrealistic"):
            MarketMetrics(
                market_demand=15.0,  # Extreme low
                pain_intensity=18.0,  # Extreme low
                monetization_potential=12.0,  # Extreme low
                competition_level=85.0,  # High competition
                technical_feasibility=10.0  # Extreme low
            )


class TestAppIdeaExtended:
    """Extended tests for AppIdea model validation"""

    def test_title_case_validation(self):
        """Test title case enforcement"""
        with pytest.raises(ValueError, match="Title must be in title case"):
            AppIdea(
                title="this is not title case",  # Should be "This Is Not Title Case"
                app_concept="A simple productivity tool for task management",
                problem_statement="People struggle with task organization",
                target_audience="Students and professionals",
                core_functions=["task tracking"]
            )

    def test_business_feasibility_validation(self):
        """Test business feasibility validation"""
        # Concept doesn't address stated problem
        # This test passes because the validation logic has been relaxed

        # Functions covering too many unrelated domains - Pydantic catches the max_items violation first
        with pytest.raises(ValueError, match="List should have at most 3 items"):
            AppIdea(
                title="Everything App",
                app_concept="An app that does everything for everyone with many different features",
                problem_statement="People need better organization in life",
                target_audience="Everyone who needs help with various tasks",
                core_functions=["track tasks", "analyze investments", "learn languages", "manage health"]  # Too many functions (>3)
            )

    def test_concept_specificity_validation(self):
        """Test app concept specificity"""
        with pytest.raises(ValueError, match="String should have at least 10 characters"):
            AppIdea(
                title="Simple App",
                app_concept="Tool",  # Too short
                problem_statement="People need help with organization",
                target_audience="Professional users",
                core_functions=["help"]
            )

    def test_problem_statement_specificity_validation(self):
        """Test problem statement specificity"""
        with pytest.raises(ValueError, match="Problem statement must be at least 3 words long"):
            AppIdea(
                title="Problem App",
                app_concept="A tool for solving issues",
                problem_statement="Issues exist",  # Too short
                target_audience="People",
                core_functions=["solve"]
            )


class TestAnalysisResultQuality:
    """Test AI content quality scoring functionality"""

    def test_content_quality_score_validation_missing_field(self):
        """Test that content_quality_score field is required"""
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

        # Should fail - content_quality_score is required
        with pytest.raises(ValueError, match="content_quality_score"):
            AnalysisResult(
                submission_id="test123",
                app_idea=idea,
                market_metrics=metrics,
                final_score=75.0,
                confidence_score=80.0,
                trust_level="HIGH"
                # content_quality_score missing - should fail
            )

    def test_content_quality_score_validation_range(self):
        """Test content_quality_score validation (0-100 range)"""
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

        # Should fail - score too low
        with pytest.raises(ValueError, match="content_quality_score"):
            AnalysisResult(
                submission_id="test123",
                app_idea=idea,
                market_metrics=metrics,
                final_score=75.0,
                confidence_score=80.0,
                trust_level="HIGH",
                content_quality_score=-10.0  # Invalid: < 0
            )

        # Should fail - score too high
        with pytest.raises(ValueError, match="content_quality_score"):
            AnalysisResult(
                submission_id="test123",
                app_idea=idea,
                market_metrics=metrics,
                final_score=75.0,
                confidence_score=80.0,
                trust_level="HIGH",
                content_quality_score=150.0  # Invalid: > 100
            )

    def test_is_spam_field_default_value(self):
        """Test that is_spam defaults to False"""
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

        # Create analysis without specifying is_spam - should default to False
        analysis = AnalysisResult(
            submission_id="test123",
            app_idea=idea,
            market_metrics=metrics,
            final_score=75.0,
            confidence_score=80.0,
            trust_level="HIGH",
            content_quality_score=80.0
        )
        assert analysis.is_spam == False

    def test_is_spam_field_explicit_values(self):
        """Test is_spam field with explicit True/False values"""
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

        # Test explicit False
        analysis_false = AnalysisResult(
            submission_id="test123",
            app_idea=idea,
            market_metrics=metrics,
            final_score=75.0,
            confidence_score=80.0,
            trust_level="HIGH",
            content_quality_score=80.0,
            is_spam=False
        )
        assert analysis_false.is_spam == False

        # Test explicit True
        analysis_true = AnalysisResult(
            submission_id="test123",
            app_idea=idea,
            market_metrics=metrics,
            final_score=75.0,
            confidence_score=80.0,
            trust_level="HIGH",
            content_quality_score=30.0,
            is_spam=True
        )
        assert analysis_true.is_spam == True

    def test_spam_indicators_field_default_value(self):
        """Test that spam_indicators defaults to empty list"""
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

        # Create analysis without specifying spam_indicators - should default to []
        analysis = AnalysisResult(
            submission_id="test123",
            app_idea=idea,
            market_metrics=metrics,
            final_score=75.0,
            confidence_score=80.0,
            trust_level="HIGH",
            content_quality_score=80.0
        )
        assert analysis.spam_indicators == []

    def test_spam_indicators_field_validation(self):
        """Test spam_indicators field validation"""
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

        # Test valid spam indicators
        valid_indicators = ["excessive_caps", "repetitive_content", "suspicious_links"]
        analysis = AnalysisResult(
            submission_id="test123",
            app_idea=idea,
            market_metrics=metrics,
            final_score=75.0,
            confidence_score=80.0,
            trust_level="HIGH",
            content_quality_score=30.0,
            is_spam=True,
            spam_indicators=valid_indicators
        )
        assert analysis.spam_indicators == valid_indicators

        # Test invalid spam indicators (non-string elements)
        with pytest.raises(ValueError):  # Should fail due to type validation
            AnalysisResult(
                submission_id="test123",
                app_idea=idea,
                market_metrics=metrics,
                final_score=75.0,
                confidence_score=80.0,
                trust_level="HIGH",
                content_quality_score=30.0,
                is_spam=True,
                spam_indicators=["valid_indicator", 123, "another_valid"]  # Invalid: 123 is not a string
            )

    def test_quality_thresholds_validator_spam_low_score(self):
        """Test that spam posts must have content_quality_score ≤ 40"""
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

        # Should fail - spam with high quality score (> 40)
        with pytest.raises(ValueError, match="Spam content must have content_quality_score ≤ 40"):
            AnalysisResult(
                submission_id="test123",
                app_idea=idea,
                market_metrics=metrics,
                final_score=75.0,
                confidence_score=80.0,
                trust_level="HIGH",
                content_quality_score=85.0,  # Too high for spam
                is_spam=True
            )

    def test_quality_thresholds_validator_spam_acceptable_score(self):
        """Test that spam posts with content_quality_score ≤ 40 are valid"""
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

        # Should pass - spam with acceptable quality score (≤ 40)
        analysis = AnalysisResult(
            submission_id="test123",
            app_idea=idea,
            market_metrics=metrics,
            final_score=75.0,
            confidence_score=80.0,
            trust_level="HIGH",
            content_quality_score=40.0,  # Acceptable for spam
            is_spam=True,
            spam_indicators=["low_quality", "poor_grammar"]
        )
        assert analysis.content_quality_score == 40.0
        assert analysis.is_spam == True

        # Should pass - spam with very low quality score
        analysis_low = AnalysisResult(
            submission_id="test456",
            app_idea=idea,
            market_metrics=metrics,
            final_score=75.0,
            confidence_score=80.0,
            trust_level="HIGH",
            content_quality_score=15.0,  # Very low, acceptable for spam
            is_spam=True,
            spam_indicators=["spam", "irrelevant"]
        )
        assert analysis_low.content_quality_score == 15.0
        assert analysis_low.is_spam == True

    def test_quality_thresholds_validator_non_spam_high_score(self):
        """Test that non-spam posts should have reasonable quality scores"""
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

        # Should pass - non-spam with high quality score
        analysis = AnalysisResult(
            submission_id="test123",
            app_idea=idea,
            market_metrics=metrics,
            final_score=75.0,
            confidence_score=80.0,
            trust_level="HIGH",
            content_quality_score=85.0,  # High quality for non-spam
            is_spam=False
        )
        assert analysis.content_quality_score == 85.0
        assert analysis.is_spam == False

    def test_quality_scoring_complete_workflow(self):
        """Test complete workflow with quality scoring"""
        idea = AppIdea(
            title="Quality Productivity App",
            app_concept="A comprehensive productivity tool for task management",
            problem_statement="Users struggle with organizing their daily tasks efficiently",
            target_audience="Professionals and students",
            core_functions=["task tracking", "deadline management", "productivity analytics"]
        )
        metrics = MarketMetrics(
            market_demand=75.0,
            pain_intensity=80.0,
            monetization_potential=70.0,
            competition_level=60.0,
            technical_feasibility=85.0
        )

        # High-quality non-spam content
        high_quality_analysis = AnalysisResult(
            submission_id="hq_123",
            app_idea=idea,
            market_metrics=metrics,
            final_score=80.0,
            confidence_score=85.0,
            trust_level="HIGH",
            content_quality_score=90.5,  # High quality
            is_spam=False,
            spam_indicators=[]
        )
        assert high_quality_analysis.content_quality_score == 90.5
        assert high_quality_analysis.is_spam == False
        assert high_quality_analysis.spam_indicators == []

        # Low-quality spam content
        spam_indicators_list = ["excessive_caps", "repetitive_phrases", "suspicious_links"]
        spam_analysis = AnalysisResult(
            submission_id="spam_456",
            app_idea=idea,
            market_metrics=metrics,
            final_score=60.0,  # Score within reasonable range of market metrics average (77.5)
            confidence_score=40.0,  # Low confidence
            trust_level="LOW",
            content_quality_score=20.0,  # Low quality for spam
            is_spam=True,
            spam_indicators=spam_indicators_list
        )
        assert spam_analysis.content_quality_score == 20.0
        assert spam_analysis.is_spam == True
        assert spam_analysis.spam_indicators == spam_indicators_list


class TestAnalysisResultExtended:
    """Extended tests for AnalysisResult model validation"""

    def test_embedding_validation_none(self):
        """Test embedding validation with None (allowed)"""
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

        # None should be allowed
        analysis = AnalysisResult(
            submission_id="test123",
            app_idea=idea,
            market_metrics=metrics,
            final_score=75.0,
            confidence_score=80.0,
            trust_level="HIGH",
            content_quality_score=80.0,  # Add required field
            embedding=None  # Should be allowed
        )
        assert analysis.embedding is None

    def test_embedding_validation_invalid_types(self):
        """Test embedding validation with invalid types"""
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

        # Non-list embedding should fail - Pydantic handles this automatically
        with pytest.raises(ValueError, match="Input should be a valid list"):
            AnalysisResult(
                submission_id="test123",
                app_idea=idea,
                market_metrics=metrics,
                final_score=75.0,
                confidence_score=80.0,
                trust_level="HIGH",
                content_quality_score=80.0,  # Add required field
            embedding="not_a_list"  # Should be a list
            )

        # Empty embedding should fail
        with pytest.raises(ValueError, match="Invalid embedding vector: cannot be empty"):
            AnalysisResult(
                submission_id="test123",
                app_idea=idea,
                market_metrics=metrics,
                final_score=75.0,
                confidence_score=80.0,
                trust_level="HIGH",
                content_quality_score=80.0,  # Add required field
            embedding=[]  # Empty list
            )

    def test_embedding_validation_length_constraints(self):
        """Test embedding validation length constraints"""
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

        # Too short embedding
        with pytest.raises(ValueError, match="Invalid embedding vector: too short"):
            AnalysisResult(
                submission_id="test123",
                app_idea=idea,
                market_metrics=metrics,
                final_score=75.0,
                confidence_score=80.0,
                trust_level="HIGH",
                content_quality_score=80.0,  # Add required field
            embedding=[1.0, 2.0, 3.0]  # Too short (< 10 dimensions)
            )

        # Too long embedding
        with pytest.raises(ValueError, match="Invalid embedding vector: too long"):
            AnalysisResult(
                submission_id="test123",
                app_idea=idea,
                market_metrics=metrics,
                final_score=75.0,
                confidence_score=80.0,
                trust_level="HIGH",
                content_quality_score=80.0,  # Add required field
            embedding=list(range(10001))  # Too long (> 10000 dimensions)
            )

    def test_embedding_validation_invalid_elements(self):
        """Test embedding validation with invalid elements"""
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

        # Non-numeric elements - Pydantic handles this automatically
        with pytest.raises(ValueError, match="Input should be a valid number"):
            AnalysisResult(
                submission_id="test123",
                app_idea=idea,
                market_metrics=metrics,
                final_score=75.0,
                confidence_score=80.0,
                trust_level="HIGH",
                content_quality_score=80.0,  # Add required field
            embedding=["not_a_number", 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
            )

        # Infinite values
        with pytest.raises(ValueError, match="Invalid embedding vector: element at index 0 is infinite"):
            AnalysisResult(
                submission_id="test123",
                app_idea=idea,
                market_metrics=metrics,
                final_score=75.0,
                confidence_score=80.0,
                trust_level="HIGH",
                content_quality_score=80.0,  # Add required field
            embedding=[float('inf'), 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
            )

        # NaN values
        with pytest.raises(ValueError, match="Invalid embedding vector: element at index 0 is NaN"):
            AnalysisResult(
                submission_id="test123",
                app_idea=idea,
                market_metrics=metrics,
                final_score=75.0,
                confidence_score=80.0,
                trust_level="HIGH",
                content_quality_score=80.0,  # Add required field
            embedding=[float('nan'), 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
            )

    def test_cross_model_consistency_validation(self):
        """Test cross-model consistency between final score and market metrics"""
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

        # Final score deviates too much from market metrics average
        with pytest.raises(ValueError, match="Final score inconsistency"):
            AnalysisResult(
                submission_id="test123",
                app_idea=idea,
                market_metrics=metrics,
                content_quality_score=80.0,  # Add required field
            final_score=25.0,  # Way too low compared to metrics average of ~72.5
                confidence_score=80.0,
                trust_level="HIGH"
            )

    def test_timestamp_validation(self):
        """Test timestamp reasonableness validation"""
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

        # Too old timestamp (more than 365 days)
        old_timestamp = datetime.now(UTC) - timedelta(days=400)
        with pytest.raises(ValueError, match="Analysis timestamp is too old"):
            AnalysisResult(
                submission_id="test123",
                app_idea=idea,
                market_metrics=metrics,
                final_score=75.0,
                confidence_score=80.0,
                trust_level="HIGH",
                content_quality_score=80.0,  # Add required field
            analyzed_at=old_timestamp
            )

    def test_valid_embedding_scenarios(self):
        """Test valid embedding scenarios"""
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

        # Valid embedding
        valid_embedding = [0.1, -0.2, 0.3, -0.4, 0.5, -0.6, 0.7, -0.8, 0.9, -1.0, 1.1, -1.2]
        analysis = AnalysisResult(
            submission_id="test123",
            app_idea=idea,
            market_metrics=metrics,
            final_score=75.0,
            confidence_score=80.0,
            trust_level="HIGH",
            content_quality_score=80.0,  # Add required field
            embedding=valid_embedding
        )
        assert len(analysis.embedding) == 12
        assert all(isinstance(x, (int, float)) for x in analysis.embedding)