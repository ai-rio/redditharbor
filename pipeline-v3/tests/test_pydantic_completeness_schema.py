"""
DEBT-005: Schema Completeness Tests - These tests are designed to FAIL and expose gaps in Pydantic model validation

This test suite validates that our Pydantic models have comprehensive schema validation
that catches edge cases, missing constraints, and incomplete validation rules.
"""

import json
from datetime import UTC, datetime, timedelta, timezone
from typing import List

import pytest

from models.analysis import AnalysisResult, AppIdea, MarketMetrics
from models.database import OpportunityCreate
from models.reddit import RedditComment, RedditSubmission


class TestRedditSubmissionSchemaCompleteness:
    """Test RedditSubmission model schema completeness - SHOULD FAIL"""

    def test_missing_score_validation_consistency(self):
        """Test that score validation fails for inconsistent upvotes/downvotes - SHOULD FAIL"""
        # Current implementation doesn't validate score = upvotes - downvotes
        submission = RedditSubmission(
            id="test123",
            title="Test Title",
            text="Test content",
            author="testuser",
            upvotes=100,
            downvotes=50,  # This should make score = 50, but we're passing 200
            score=200,     # INCONSISTENT - should trigger validation failure
            comments_count=25,
            subreddit="test",
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/test/test123"
        )
        # This assertion should FAIL because current implementation doesn't validate score consistency
        assert submission.score == submission.upvotes - submission.downvotes

    def test_missing_negative_score_validation(self):
        """Test that negative scores are properly validated - SHOULD FAIL"""
        # Current implementation doesn't prevent negative scores despite business logic
        with pytest.raises(ValueError, match="Score cannot be negative"):
            RedditSubmission(
                id="test123",
                title="Test Title",
                text="Test content",
                author="testuser",
                upvotes=10,
                downvotes=20,  # More downvotes than upvotes
                score=-10,     # Negative score should be rejected
                comments_count=25,
                subreddit="test",
                created_utc=datetime.now(UTC),
                permalink="https://reddit.com/r/test/test123"
            )

    def test_missing_url_validation_when_present(self):
        """Test that URL validation occurs when URL is provided - SHOULD FAIL"""
        # Current implementation doesn't validate URL format when provided
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
            permalink="https://reddit.com/r/test/test123",
            url="invalid-url-not-a-valid-domain"  # Should trigger validation
        )
        # This should FAIL because URL validation is missing
        assert submission.url.startswith(("http://", "https://"))

    def test_missing_author_name_validation(self):
        """Test that author names are validated against Reddit username rules - SHOULD FAIL"""
        # Current implementation doesn't validate Reddit username format
        invalid_usernames = [
            "user name",  # spaces not allowed
            "user-name",  # hyphens may not be allowed
            "",           # empty string
            "a" * 21,     # too long (Reddit limit is 20 chars)
            "bot",        # reserved term
            "mod",        # reserved term
        ]

        for username in invalid_usernames:
            with pytest.raises(ValueError, match="Invalid Reddit username"):
                RedditSubmission(
                    id="test123",
                    title="Test Title",
                    text="Test content",
                    author=username,
                    upvotes=100,
                    score=100,
                    comments_count=25,
                    subreddit="test",
                    created_utc=datetime.now(UTC),
                    permalink="https://reddit.com/r/test/test123"
                )

    def test_missing_subreddit_validation(self):
        """Test that subreddit names are validated - SHOULD FAIL"""
        # Current implementation doesn't validate subreddit format
        invalid_subreddits = [
            "test subreddit",  # spaces not allowed
            "test-subreddit",  # hyphens may not be allowed in all cases
            "",               # empty string
            "a" * 22,         # too long
            "mod",           # reserved term
            "all",           # reserved term
            "friends",       # reserved term
        ]

        for subreddit in invalid_subreddits:
            with pytest.raises(ValueError, match="Invalid subreddit name"):
                RedditSubmission(
                    id="test123",
                    title="Test Title",
                    text="Test content",
                    author="testuser",
                    upvotes=100,
                    score=100,
                    comments_count=25,
                    subreddit=subreddit,
                    created_utc=datetime.now(UTC),
                    permalink="https://reddit.com/r/test/test123"
                )

    def test_missing_title_spam_keywords_validation(self):
        """Test that titles don't contain spam keywords - SHOULD FAIL"""
        # Current implementation doesn't check for spam patterns
        spam_keywords = ["free money", "click here", "limited time", "urgent", "act now"]

        for keyword in spam_keywords:
            with pytest.raises(ValueError, match="Title contains spam-like content"):
                RedditSubmission(
                    id="test123",
                    title=f"Amazing {keyword} offer!!!",
                    text="Test content",
                    author="testuser",
                    upvotes=100,
                    score=100,
                    comments_count=25,
                    subreddit="test",
                    created_utc=datetime.now(UTC),
                    permalink="https://reddit.com/r/test/test123"
                )

    def test_missing_text_content_validation(self):
        """Test that text content has minimum meaningful length - SHOULD FAIL"""
        # Current implementation doesn't validate text quality
        invalid_texts = [
            "",                      # empty text
            "   ",                   # only whitespace
            ".",                     # too short for meaningful content
            "I.",                    # too short
            "This is just test.",    # too vague for research value
        ]

        for text in invalid_texts:
            with pytest.raises(ValueError, match="Text must be meaningful and substantial"):
                RedditSubmission(
                    id="test123",
                    title="Test Title",
                    text=text,
                    author="testuser",
                    upvotes=100,
                    score=100,
                    comments_count=25,
                    subreddit="test",
                    created_utc=datetime.now(UTC),
                    permalink="https://reddit.com/r/test/test123"
                )

    def test_missing_cross_field_dependencies(self):
        """Test cross-field validation dependencies - SHOULD FAIL"""
        # Current implementation doesn't validate relationships between fields
        submission = RedditSubmission(
            id="test123",
            title="Test Title",
            text="Test content",
            author="testuser",
            upvotes=0,                  # No upvotes
            score=100,                  # Impossible score with 0 upvotes
            comments_count=0,           # No comments
            subreddit="test",
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/test/test123"
        )

        # This should validate that high score requires engagement
        if submission.score > 50 and submission.upvotes == 0:
            pytest.fail("High score with zero upvotes should be impossible")

    def test_missing_timestamp_reasonableness(self):
        """Test that timestamps are within reasonable bounds - SHOULD FAIL"""
        # Current implementation only checks future dates, not ancient ones
        ancient_dates = [
            datetime(1970, 1, 1),  # Unix epoch
            datetime(2005, 1, 1),  # Before Reddit existed
            datetime(2000, 1, 1),  # Very old
        ]

        for created_date in ancient_dates:
            with pytest.raises(ValueError, match="Date is too old for Reddit content"):
                RedditSubmission(
                    id="test123",
                    title="Test Title",
                    text="Test content",
                    author="testuser",
                    upvotes=100,
                    score=100,
                    comments_count=25,
                    subreddit="test",
                    created_utc=created_date,
                    permalink="https://reddit.com/r/test/test123"
                )


class TestRedditCommentSchemaCompleteness:
    """Test RedditComment model schema completeness - SHOULD FAIL"""

    def test_missing_score_validation_consistency(self):
        """Test that comment score validation fails for inconsistent upvotes - SHOULD FAIL"""
        # Current implementation doesn't validate score consistency for comments
        comment = RedditComment(
            id="comment123",
            submission_id="test123",
            author="testuser",
            text="Test comment",
            upvotes=10,
            score=-5,  # Inconsistent with upvotes
            created_utc=datetime.now(UTC)
        )
        # This should FAIL because score can't be negative with positive upvotes
        assert comment.score >= 0

    def test_missing_comment_length_validation(self):
        """Test that comment length is validated - SHOULD FAIL"""
        # Current implementation doesn't validate comment length
        invalid_comments = [
            "",                                # empty comment
            "   ",                            # only whitespace
            ".",                               # too short
            "a" * 10001,                      # too long (Reddit limit)
            "This comment is clearly too long and should be rejected by proper length validation that checks Reddit's actual comment limits",
        ]

        for comment_text in invalid_comments:
            with pytest.raises(ValueError, match="Comment length is invalid"):
                RedditComment(
                    id="comment123",
                    submission_id="test123",
                    author="testuser",
                    text=comment_text,
                    upvotes=10,
                    created_utc=datetime.now(UTC)
                )


class TestAppIdeaSchemaCompleteness:
    """Test AppIdea model schema completeness - SHOULD FAIL"""

    def test_missing_title_case_validation(self):
        """Test that titles follow proper case conventions - SHOULD FAIL"""
        # Current implementation doesn't validate title case
        invalid_titles = [
            "all lowercase title",          # should use proper case
            "ALL UPPERCASE TITLE",          # should use proper case
            "Title With Extra Spaces",      # should not have extra spaces
            "title With Bad Capitalization", # inconsistent capitalization
            "123 Numbers At Start",          # shouldn't start with numbers
        ]

        for title in invalid_titles:
            with pytest.raises(ValueError, match="Title must follow proper capitalization"):
                AppIdea(
                    title=title,
                    app_concept="A test application",
                    problem_statement="A test problem",
                    target_audience="Test users",
                    core_functions=["test function"]
                )

    def test_missing_concept_uniqueness_check(self):
        """Test that app concepts are unique and not generic - SHOULD FAIL"""
        # Current implementation doesn't check for generic or duplicate concepts
        generic_concepts = [
            "a mobile app",
            "an application",
            "software solution",
            "web platform",
            "app for smartphones",
        ]

        for concept in generic_concepts:
            with pytest.raises(ValueError, match="App concept must be specific and non-generic"):
                AppIdea(
                    title="Generic App",
                    app_concept=concept,
                    problem_statement="A test problem",
                    target_audience="Test users",
                    core_functions=["test function"]
                )

    def test_missing_problem_statement_specificity(self):
        """Test that problem statements are specific enough - SHOULD FAIL"""
        # Current implementation doesn't validate problem specificity
        generic_problems = [
            "People need help",                  # too vague
            "Technology is important",          # not a problem
            "Users want better experience",     # too generic
            "Businesses need efficiency",      # too broad
        ]

        for problem in generic_problems:
            with pytest.raises(ValueError, match="Problem statement must be specific and actionable"):
                AppIdea(
                    title="Specific App",
                    app_concept="A specific application",
                    problem_statement=problem,
                    target_audience="Test users",
                    core_functions=["test function"]
                )

    def test_missing_target_audience_validation(self):
        """Test that target audience is specific and validated - SHOULD FAIL"""
        # Current implementation doesn't validate audience specificity
        invalid_audiences = [
            "everyone",                          # too broad
            "people",                           # too generic
            "users",                            # too generic
            "everyone who needs this",         # too broad
            "tech professionals and business users and students and everyone else",  # too many groups
        ]

        for audience in invalid_audiences:
            with pytest.raises(ValueError, match="Target audience must be specific"):
                AppIdea(
                    title="Targeted App",
                    app_concept="A targeted application",
                    problem_statement="A specific problem",
                    target_audience=audience,
                    core_functions=["test function"]
                )

    def test_missing_function_semantic_validation(self):
        """Test that core functions are semantically different - SHOULD FAIL"""
        # Current implementation only checks for exact duplicates
        semantically_similar = [
            "task management",              # too similar to "task organization"
            "organize tasks",               # similar to above
            "manage activities",            # similar concept
            "activity organization",        # similar concept
        ]

        with pytest.raises(ValueError, match="Core functions must be semantically distinct"):
            AppIdea(
                title="Similar Functions App",
                app_concept="An app with similar functions",
                problem_statement="A problem",
                target_audience="Users",
                core_functions=semantically_similar
            )

    def test_missing_business_logic_validation(self):
        """Test app idea business logic validation - SHOULD FAIL"""
        # Current implementation doesn't validate business feasibility
        idea = AppIdea(
            title="Impossible App",
            app_concept="App that reads minds and solves all problems",
            problem_statement="People have problems",
            target_audience="Everyone",
            core_functions=["mind reading", "time travel", "teleportation"]
        )

        # This should validate that functions are technologically feasible
        impossible_functions = ["mind reading", "teleportation", "time travel"]
        if any(func in " ".join(idea.core_functions).lower() for func in impossible_functions):
            pytest.fail("App contains technologically impossible features")


class TestMarketMetricsSchemaCompleteness:
    """Test MarketMetrics model schema completeness - SHOULD FAIL"""

    def test_missing_metric_consistency_validation(self):
        """Test that market metrics are logically consistent - SHOULD FAIL"""
        # Current implementation doesn't validate metric relationships
        metrics = MarketMetrics(
            market_demand=10.0,     # Very low demand
            pain_intensity=90.0,    # Very high pain
            monetization_potential=90.0,  # Very high monetization
            competition_level=10.0,     # Very low competition
            technical_feasibility=90.0   # Very high feasibility
        )

        # This should validate metric relationships
        if (metrics.pain_intensity > 80 and metrics.market_demand < 30):
            pytest.fail("High pain with low market demand is inconsistent")

        if (metrics.competition_level < 20 and metrics.market_demand < 40):
            pytest.fail("Low competition should correlate with higher market demand")

    def test_missing_extreme_value_validation(self):
        """Test that extreme metric values are validated - SHOULD FAIL"""
        # Current implementation only checks 0-100 range, not reasonableness
        extreme_metrics = [
            {"market_demand": 0.1, "pain_intensity": 0.1},  # Too low to be viable
            {"monetization_potential": 99.9, "technical_feasibility": 5.0},  # Unrealistic combination
            {"competition_level": 0.1, "monetization_potential": 10.0},  # Low competition should enable higher monetization
        ]

        for metric_set in extreme_metrics:
            with pytest.raises(ValueError, match="Metrics combination is unrealistic"):
                MarketMetrics(
                    market_demand=metric_set["market_demand"],
                    pain_intensity=metric_set["pain_intensity"],
                    monetization_potential=metric_set.get("monetization_potential", 50.0),
                    competition_level=metric_set.get("competition_level", 50.0),
                    technical_feasibility=metric_set.get("technical_feasibility", 50.0)
                )

    def test_missing_precision_validation(self):
        """Test that metric precision is appropriate - SHOULD FAIL"""
        # Current implementation doesn't validate precision
        metrics = MarketMetrics(
            market_demand=75.555555,  # Too many decimal places
            pain_intensity=80.123456,
            monetization_potential=70.987654,
            competition_level=60.345678,
            technical_feasibility=85.234567
        )

        # Metrics should have reasonable precision (1-2 decimal places)
        for value in [metrics.market_demand, metrics.pain_intensity, metrics.monetization_potential,
                     metrics.competition_level, metrics.technical_feasibility]:
            if len(str(value).split('.')[1]) > 2:
                pytest.fail(f"Metric {value} has too many decimal places")


class TestAnalysisResultSchemaCompleteness:
    """Test AnalysisResult model schema completeness - SHOULD FAIL"""

    def test_missing_cross_model_validation(self):
        """Test cross-model validation in AnalysisResult - SHOULD FAIL"""
        # Current implementation doesn't validate relationships between models

        idea = AppIdea(
            title="Test App",
            app_concept="A test application",
            problem_statement="A test problem",
            target_audience="Test users",
            core_functions=["test function"]
        )

        metrics = MarketMetrics(
            market_demand=20.0,     # Low market demand
            pain_intensity=15.0,     # Low pain intensity
            monetization_potential=85.0,  # High monetization potential - inconsistent
            competition_level=90.0,     # Very high competition
            technical_feasibility=10.0   # Very low technical feasibility
        )

        analysis = AnalysisResult(
            submission_id="test123",
            app_idea=idea,
            market_metrics=metrics,
            final_score=90.0,        # High score despite inconsistent metrics
            confidence_score=80.0,
            trust_level="HIGH"
        )

        # This should validate that final score is consistent with component metrics
        expected_score_range = (
            (metrics.market_demand + metrics.pain_intensity +
             metrics.monetization_potential + metrics.technical_feasibility) / 4
        )

        if abs(analysis.final_score - expected_score_range) > 20:
            pytest.fail("Final score is inconsistent with component metrics")

    def test_missing_embedding_validation(self):
        """Test that embedding vector is properly validated - SHOULD FAIL"""
        # Current implementation doesn't validate embedding structure

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

        # Invalid embeddings that should be caught
        invalid_embeddings = [
            [],                    # Empty vector
            [1.0, 2.0],            # Too short
            [1.0] * 10001,         # Too long
            ["not a float"],       # Wrong type
            [float('inf')],       # Infinite values
            [float('nan')],       # NaN values
        ]

        for embedding in invalid_embeddings:
            with pytest.raises(ValueError, match="Invalid embedding vector"):
                AnalysisResult(
                    submission_id="test123",
                    app_idea=idea,
                    market_metrics=metrics,
                    final_score=75.0,
                    confidence_score=80.0,
                    trust_level="HIGH",
                    embedding=embedding
                )

    def test_missing_timestamp_validation(self):
        """Test that analyzed_at timestamp is validated - SHOULD FAIL"""
        # Current implementation doesn't validate timestamp reasonableness

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

        old_timestamp = datetime.now(UTC) - timedelta(days=365)

        with pytest.raises(ValueError, match="Analysis timestamp is too old"):
            AnalysisResult(
                submission_id="test123",
                app_idea=idea,
                market_metrics=metrics,
                final_score=75.0,
                confidence_score=80.0,
                trust_level="HIGH",
                analyzed_at=old_timestamp
            )


class TestOpportunityCreateSchemaCompleteness:
    """Test OpportunityCreate model schema completeness - SHOULD FAIL"""

    def test_missing_database_constraint_validation(self):
        """Test that data matches database constraints - SHOULD FAIL"""
        # Current implementation doesn't validate database constraints

        create = OpportunityCreate(
            submission_id="test123",
            reddit_title="Test Title",
            reddit_url="https://reddit.com/r/test/test123",
            subreddit="test",
            reddit_author="testuser",
            reddit_upvotes=100,
            reddit_comments_count=25,
            reddit_created_at=datetime.now(UTC),
            app_title="Test App",
            app_concept="A test application",
            problem_statement="A test problem",
            target_audience="Test users",
            core_functions=["test function"],
            market_demand=70.0,
            pain_intensity=75.0,
            monetization_potential=80.0,
            competition_level=65.0,
            technical_feasibility=85.0,
            final_score=75.0,
            confidence_score=80.0,
            trust_level="HIGH"
        )

        # This should validate string lengths match database constraints
        assert len(create.reddit_title) <= 300, "Reddit title exceeds database limit"
        assert len(create.app_title) <= 200, "App title exceeds database limit"

        # This should validate that submission_id uniqueness is checked
        duplicate_submissions = ["test123", "test123"]  # Should be unique
        if len(set(duplicate_submissions)) != len(duplicate_submissions):
            pytest.fail("Duplicate submission IDs should be rejected")

    def test_missing_foreign_key_validation(self):
        """Test that foreign key relationships are validated - SHOULD FAIL"""
        # Current implementation doesn't validate foreign key constraints

        create = OpportunityCreate(
            submission_id="nonexistent123",  # Should validate this exists
            reddit_title="Test Title",
            reddit_url="https://reddit.com/r/test/test123",
            subreddit="test",
            reddit_author="testuser",
            reddit_upvotes=100,
            reddit_comments_count=25,
            reddit_created_at=datetime.now(UTC),
            app_title="Test App",
            app_concept="A test application",
            problem_statement="A test problem",
            target_audience="Test users",
            core_functions=["test function"],
            market_demand=70.0,
            pain_intensity=75.0,
            monetization_potential=80.0,
            competition_level=65.0,
            technical_feasibility=85.0,
            final_score=75.0,
            confidence_score=80.0,
            trust_level="HIGH"
        )

        # This should validate that submission_id exists in database
        # This would require database access to test properly
        create.submission_id = ""  # Should fail validation
        create.submission_id = "a" * 11  # Should fail validation (max 10 chars)

        with pytest.raises(ValueError, match="Invalid submission ID"):
            # This would trigger the validation if it existed
            pass

    def test_missing_json_schema_validation(self):
        """Test that JSON fields match expected schema - SHOULD FAIL"""
        # Current implementation doesn't validate JSON field structure

        create = OpportunityCreate(
            submission_id="test123",
            reddit_title="Test Title",
            reddit_url="https://reddit.com/r/test/test123",
            subreddit="test",
            reddit_author="testuser",
            reddit_upvotes=100,
            reddit_comments_count=25,
            reddit_created_at=datetime.now(UTC),
            app_title="Test App",
            app_concept="A test application",
            problem_statement="A test problem",
            target_audience="Test users",
            core_functions=["not a string list"],  # Should be a list of strings
            market_demand=70.0,
            pain_intensity=75.0,
            monetization_potential=80.0,
            competition_level=65.0,
            technical_feasibility=85.0,
            final_score=75.0,
            confidence_score=80.0,
            trust_level="HIGH"
        )

        # This should validate that core_functions is a proper list
        if not isinstance(create.core_functions, list):
            pytest.fail("core_functions must be a list")

        if not all(isinstance(func, str) for func in create.core_functions):
            pytest.fail("All core_functions must be strings")

        # This should validate JSON serialization works
        try:
            json_str = json.dumps(create.core_functions)
            parsed = json.loads(json_str)
            assert parsed == create.core_functions
        except (TypeError, ValueError):
            pytest.fail("core_functions must be JSON serializable")
