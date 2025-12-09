"""
DEBT-005: Edge Case Handling Tests - These tests are designed to FAIL and expose edge case gaps

This test suite validates that our Pydantic models handle boundary conditions,
extreme values, and unusual scenarios that could cause failures in production.
"""

import json
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import List

import pytest

from models.analysis import AnalysisResult, AppIdea, MarketMetrics
from models.database import OpportunityCreate
from models.reddit import RedditComment, RedditSubmission


class TestRedditSubmissionEdgeCases:
    """Test RedditSubmission model edge case handling - SHOULD FAIL"""

    def test_maximum_length_boundary_values(self):
        """Test maximum length boundary values - SHOULD FAIL"""
        # Current implementation may not handle edge cases properly

        # Test exact maximum length for title (Reddit limit: 300 characters)
        max_length_title = "a" * 300
        submission = RedditSubmission(
            id="test123",
            title=max_length_title,
            text="a" * 1000,  # Should handle long text
            author="testuser",
            upvotes=100,
            score=100,
            comments_count=25,
            subreddit="test",
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/test/test123"
        )

        # This should validate exact maximum length handling
        assert len(submission.title) == 300

        # Test one character over limit (should fail)
        with pytest.raises(ValueError, match="Title exceeds maximum length"):
            RedditSubmission(
                id="test123",
                title="a" * 301,  # One character over limit
                text="a" * 1000,
                author="testuser",
                upvotes=100,
                score=100,
                comments_count=25,
                subreddit="test",
                created_utc=datetime.now(UTC),
                permalink="https://reddit.com/r/test/test123"
            )

    def test_unicode_and_special_characters(self):
        """Test Unicode and special character handling - SHOULD FAIL"""
        # Current implementation may not handle Unicode properly

        unicode_test_cases = [
            # Emojis and symbols
            "🚀 Amazing app idea with emojis! 🚀",
            "Title with £€¥ currency symbols",
            "Title with chinese characters: 应用程序",
            "Title with arabic: تطبيق",
            "Title with russian: приложение",
            "Title with mixed: 🎯 App für alle Benutzer 🎯",
            # Special characters
            "Title with quotes: 'test' \"double\" `backticks`",
            "Title with brackets: (parentheses) [square] {braces}",
            "Title with punctuation: test... test!!! test???",
            "Title with math: 2² 3³ ½ ¾ ∞ π",
            "Title with whitespace: \t\n\r\f\v test \t\n\r\f\v",
        ]

        for title in unicode_test_cases:
            submission = RedditSubmission(
                id="test123",
                title=title,
                text="Test content with special chars: 🚀£€¥",
                author="testuser",
                upvotes=100,
                score=100,
                comments_count=25,
                subreddit="test",
                created_utc=datetime.now(UTC),
                permalink="https://reddit.com/r/test/test123"
            )

            # This should validate Unicode handling
            assert submission.title == title
            assert "🚀" in submission.title or "£€¥" in submission.title

    def test_extreme_numeric_values(self):
        """Test extreme numeric value handling - SHOULD FAIL"""
        # Current implementation may not handle extreme values

        # Test maximum Reddit values
        max_submission = RedditSubmission(
            id="test123",
            title="Max engagement post",
            text="High engagement content",
            author="testuser",
            upvotes=2147483647,  # Max int32 value
            downvotes=0,
            score=2147483647,  # Max int32 value
            comments_count=2147483647,  # Max int32 value
            subreddit="test",
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/test/test123"
        )

        # This should validate extreme value handling
        assert max_submission.upvotes == 2147483647
        assert max_submission.comments_count == 2147483647

        # Test negative values (should fail)
        with pytest.raises(ValueError, match="Negative values not allowed"):
            RedditSubmission(
                id="test123",
                title="Test",
                text="Content",
                author="user",
                upvotes=-1,  # Negative upvotes should fail
                score=10,
                comments_count=5,
                subreddit="test",
                created_utc=datetime.now(UTC),
                permalink="https://reddit.com/r/test/test123"
            )

    def test_null_and_empty_string_handling(self):
        """Test null and empty string handling - SHOULD FAIL"""
        # Current implementation may not handle empty strings properly

        # Test empty strings for required fields
        empty_string_cases = [
            {"id": "", "field": "ID"},
            {"title": "", "field": "Title"},
            {"text": "", "field": "Text"},
            {"author": "", "field": "Author"},
            {"subreddit": "", "field": "Subreddit"},
        ]

        for case in empty_string_cases:
            with pytest.raises(ValueError, match=f"{case['field']} cannot be empty"):
                RedditSubmission(
                    id=case["id"],
                    title="test" if case["field"] != "Title" else "",
                    text="test" if case["field"] != "Text" else "",
                    author="test" if case["field"] != "Author" else "",
                    upvotes=100,
                    score=100,
                    comments_count=25,
                    subreddit="test" if case["field"] != "Subreddit" else "",
                    created_utc=datetime.now(UTC),
                    permalink="https://reddit.com/r/test/test123"
                )

    def test_whitespace_only_strings(self):
        """Test whitespace-only string handling - SHOULD FAIL"""
        # Current implementation may not catch whitespace-only strings

        whitespace_cases = [
            "     ",
            "\t",
            "\n",
            "\r\n",
            " \t \n \r ",
            "\u2003",  # Em space
            "\u00A0",  # Non-breaking space
        ]

        for whitespace_text in whitespace_cases:
            with pytest.raises(ValueError, match="Cannot contain only whitespace"):
                RedditSubmission(
                    id="test123",
                    title=whitespace_text,
                    text="valid content",
                    author="testuser",
                    upvotes=100,
                    score=100,
                    comments_count=25,
                    subreddit="test",
                    created_utc=datetime.now(UTC),
                    permalink="https://reddit.com/r/test/test123"
                )

    def test_timestamp_boundary_values(self):
        """Test timestamp boundary values - SHOULD FAIL"""
        # Current implementation may not handle extreme timestamps

        # Test Unix epoch (1970-01-01)
        epoch_time = datetime(1970, 1, 1, tzinfo=UTC)
        submission = RedditSubmission(
            id="test123",
            title="Old post",
            text="Historical content",
            author="testuser",
            upvotes=10,
            score=10,
            comments_count=5,
            subreddit="test",
            created_utc=epoch_time,
            permalink="https://reddit.com/r/test/test123"
        )

        # This should handle epoch time
        assert submission.created_utc == epoch_time

        # Test very recent timestamp (future boundary)
        very_recent = datetime.now(UTC) + timedelta(microseconds=1)
        with pytest.raises(ValueError, match="cannot be in the future"):
            RedditSubmission(
                id="test123",
                title="Test",
                text="Content",
                author="user",
                upvotes=10,
                score=10,
                comments_count=5,
                subreddit="test",
                created_utc=very_recent,
                permalink="https://reddit.com/r/test/test123"
            )

    def test_url_parsing_edge_cases(self):
        """Test URL parsing edge cases - SHOULD FAIL"""
        # Current implementation may not handle complex URLs

        complex_url_cases = [
            "https://www.reddit.com/r/technology/comments/123/example_title/",
            "https://reddit.com/r/programming/comments/456/code_review/",
            "https://www.reddit.com/r/science/comments/789/research_findings/",
            "https://reddit.com/r/futurology/comments/1011/future_tech/",
            "https://www.reddit.com/r/explainlikeimfive/comments/1122/simple_concept/",
            "/r/technology/comments/123/example_title/",  # Short URL
            "https://reddit.com/r/test/comments/test123/post_title/",  # Alphanumeric ID
        ]

        for url in complex_url_cases:
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
                permalink=url
            )

            # This should validate complex URL handling
            assert url.startswith(("https://reddit.com/", "/r/"))

        # Test invalid URL formats
        invalid_urls = [
            "http://reddit.com/r/test/test123",  # Should be https
            "https://bad-domain.com/r/test/test123",  # Wrong domain
            "not-a-url",  # Plain text
            "https://reddit.com/test/test123",  # Missing /r/
            "https://reddit.com/r//test123",  # Empty subreddit
        ]

        for invalid_url in invalid_urls:
            with pytest.raises(ValueError, match="must be a valid Reddit URL"):
                RedditSubmission(
                    id="test123",
                    title="Test",
                    text="Content",
                    author="user",
                    upvotes=10,
                    score=10,
                    comments_count=5,
                    subreddit="test",
                    created_utc=datetime.now(UTC),
                    permalink=invalid_url
                )

    def test_memory_efficiency_with_large_data(self):
        """Test memory efficiency with large data - SHOULD FAIL"""
        # Current implementation may not handle large text efficiently

        # Test very large text content
        large_text = "a" * 1000000  # 1MB of text
        submission = RedditSubmission(
            id="test123",
            title="Large content post",
            text=large_text,
            author="testuser",
            upvotes=100,
            score=100,
            comments_count=25,
            subreddit="test",
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/test/test123"
        )

        # This should validate large text handling
        assert len(submission.text) == 1000000

        # Test memory efficiency (should not consume excessive memory)
        import sys
        submission_memory = sys.getsizeof(submission)
        assert submission_memory < 10 * 1024 * 1024, "Submission object should use less than 10MB"

    def test_concurrent_access_simulation(self):
        """Test concurrent access simulation - SHOULD FAIL"""
        # Current implementation may not handle concurrent validation

        import threading
        import time

        results = []
        errors = []

        def create_submission(thread_id):
            try:
                submission = RedditSubmission(
                    id=f"test{thread_id}",
                    title=f"Thread {thread_id} content",
                    text=f"Content from thread {thread_id}",
                    author=f"user{thread_id}",
                    upvotes=100 + thread_id,
                    score=100 + thread_id,
                    comments_count=25 + thread_id,
                    subreddit="test",
                    created_utc=datetime.now(UTC),
                    permalink="https://reddit.com/r/test/test123"
                )
                results.append(submission)
            except Exception as e:
                errors.append(e)

        # Create multiple threads simulating concurrent access
        threads = []
        for i in range(100):  # 100 concurrent requests
            thread = threading.Thread(target=create_submission, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # This should validate concurrent access handling
        assert len(errors) == 0, f"Concurrent access caused {len(errors)} errors"
        assert len(results) == 100, f"Expected 100 submissions, got {len(results)}"


class TestRedditCommentEdgeCases:
    """Test RedditComment model edge case handling - SHOULD FAIL"""

    def test_comment_hierarchy_depth_limits(self):
        """Test comment hierarchy depth limits - SHOULD FAIL"""
        # Current implementation doesn't track comment depth

        # Simulate deep comment hierarchy
        depth_submissions = []
        current_parent_id = "submission123"

        for depth in range(1, 11):  # Create comments at different depths
            comment = RedditComment(
                id=f"comment_{depth}",
                submission_id=current_parent_id,
                author=f"user_{depth}",
                text=f"Comment at depth {depth}",
                upvotes=max(1, 10 - depth),  # Decreasing engagement with depth
                created_utc=datetime.now(UTC) - timedelta(minutes=depth)
            )
            depth_submissions.append(comment)
            current_parent_id = f"comment_{depth}"

        # This should validate depth-based validation
        # Deep comments should have different validation rules
        for i, comment in enumerate(depth_submissions):
            if i >= 5:  # Depth 5+
                # Deep comments should be shorter and more conversational
                assert len(comment.text) <= 100, f"Deep comment at depth {i} should be concise"

    def test_comment_velocity_limits(self):
        """Test comment velocity limits - SHOULD FAIL"""
        # Current implementation doesn't track comment velocity

        # Simulate extremely fast comment posting
        submission_time = datetime.now(UTC)
        fast_comments = []

        for i in range(100):  # 100 comments in rapid succession
            comment_time = submission_time + timedelta(milliseconds=i * 10)  # Every 10ms
            comment = RedditComment(
                id=f"fast_comment_{i}",
                submission_id="test123",
                author=f"fast_user_{i}",
                text=f"Ultra fast comment {i}",
                upvotes=1,
                created_utc=comment_time
            )
            fast_comments.append(comment)

        # This should validate velocity-based validation
        # Check for spam patterns in velocity
        time_differences = []
        for i in range(1, len(fast_comments)):
            diff = (fast_comments[i].created_utc - fast_comments[i-1].created_utc).total_seconds()
            time_differences.append(diff)

        avg_time_diff = sum(time_differences) / len(time_differences)
        if avg_time_diff < 0.1:  # Less than 100ms between comments
            pytest.fail("Comment velocity indicates potential spam activity")

    def test_extreme_comment_lengths(self):
        """Test extreme comment length handling - SHOULD FAIL"""
        # Current implementation may not handle extreme comment lengths

        # Test very long comments (Reddit limit: 10,000 characters)
        max_length_comment = "a" * 10000
        comment = RedditComment(
            id="comment123",
            submission_id="test123",
            author="testuser",
            text=max_length_comment,
            upvotes=100,
            created_utc=datetime.now(UTC)
        )

        # This should validate maximum length handling
        assert len(comment.text) == 10000

        # Test comment that exceeds limit (should fail)
        with pytest.raises(ValueError, match="Comment exceeds maximum length"):
            RedditComment(
                id="comment123",
                submission_id="test123",
                author="testuser",
                text="a" * 10001,  # One character over limit
                upvotes=100,
                created_utc=datetime.now(UTC)
            )

    def test_comment_score_anomalies(self):
        """Test comment score anomalies - SHOULD FAIL"""
        # Current implementation may not detect score anomalies

        # Test anomalous score patterns
        anomaly_cases = [
            {"upvotes": 1000, "score": -100},  # Impossible negative score with positive upvotes
            {"upvotes": 0, "score": 50},       # Impossible positive score with zero upvotes
            {"upvotes": -50, "score": 100},     # Impossible positive score with negative upvotes
            {"upvotes": 100, "score": 200},     # Score exceeds upvotes (impossible)
        ]

        for case in anomaly_cases:
            with pytest.raises(ValueError, match="Score anomaly detected"):
                RedditComment(
                    id="comment123",
                    submission_id="test123",
                    author="testuser",
                    text="Test comment",
                    upvotes=case["upvotes"],
                    score=case["score"],
                    created_utc=datetime.now(UTC)
                )

    def test_comment_automated_detection(self):
        """Test comment automated content detection - SHOULD FAIL"""
        # Current implementation doesn't detect automated/bot comments

        bot_indicators = [
            "I am a bot",  # Obvious bot
            "This is an automated response",  # Automated content
            "Bot: ",  # Bot prefix
            "[automated]",  # Automated tag
            "Auto-generated content",  # Auto-generated
            "This comment was posted by a bot",  # Bot declaration
        ]

        for bot_text in bot_indicators:
            with pytest.raises(ValueError, match="Automated content detected"):
                RedditComment(
                    id="comment123",
                    submission_id="test123",
                    author="bot_user",
                    text=bot_text,
                    upvotes=0,
                    created_utc=datetime.now(UTC)
                )


class TestAppIdeaEdgeCases:
    """Test AppIdea model edge case handling - SHOULD FAIL"""

    def test_maximum_item_limits(self):
        """Test maximum item limits - SHOULD FAIL"""
        # Current implementation may not handle extreme limits

        # Test maximum core functions (should be 3)
        max_functions = ["func1", "func2", "func3"]
        idea = AppIdea(
            title="Max Functions App",
            app_concept="App with maximum allowed functions",
            problem_statement="A complex problem requiring multiple solutions",
            target_audience="Complex users",
            core_functions=max_functions
        )

        # This should validate maximum item handling
        assert len(idea.core_functions) == 3

        # Test one over limit (should fail)
        with pytest.raises(ValueError, match="List should have at most 3 items"):
            AppIdea(
                title="Too Many Functions",
                app_concept="App with too many functions",
                problem_statement="A problem",
                target_audience="Users",
                core_functions=["func1", "func2", "func3", "func4"]  # 4 functions
            )

    def test_string_boundary_lengths(self):
        """Test string boundary length handling - SHOULD FAIL"""
        # Current implementation may not handle exact boundary lengths

        # Test exact minimum and maximum lengths
        boundary_cases = [
            {"title": "a" * 5, "field": "title", "min": 5},  # Minimum title length
            {"title": "a" * 100, "field": "title", "max": 100},  # Maximum title length
            {"concept": "a" * 10, "field": "concept", "min": 10},  # Minimum concept length
            {"concept": "a" * 500, "field": "concept", "max": 500},  # Maximum concept length
            {"problem": "a" * 10, "field": "problem", "min": 10},  # Minimum problem length
            {"problem": "a" * 1000, "field": "problem", "max": 1000},  # Maximum problem length
            {"audience": "a" * 10, "field": "audience", "min": 10},  # Minimum audience length
            {"audience": "a" * 500, "field": "audience", "max": 500},  # Maximum audience length
        ]

        for case in boundary_cases:
            idea = AppIdea(
                title=case["title"] if case["field"] == "title" else "Valid Title",
                app_concept=case["concept"] if case["field"] == "concept" else "Valid concept",
                problem_statement=case["problem"] if case["field"] == "problem" else "Valid problem",
                target_audience=case["audience"] if case["field"] == "audience" else "Valid audience",
                core_functions=["valid function"]
            )

            # This should validate boundary length handling
            if "min" in case:
                assert len(getattr(idea, case["field"])) >= case["min"]
            if "max" in case:
                assert len(getattr(idea, case["field"])) <= case["max"]

        # Test one character below minimum (should fail)
        with pytest.raises(ValueError, match="String should have at least 5 characters"):
            AppIdea(
                title="a",  # Too short (4 characters below minimum)
                app_concept="Valid concept",
                problem_statement="Valid problem",
                target_audience="Valid audience",
                core_functions=["valid function"]
            )

    def test_string_whitespace_normalization(self):
        """Test string whitespace normalization - SHOULD FAIL"""
        # Current implementation may not normalize whitespace

        whitespace_cases = [
            {"title": "  Multiple  Spaces  ", "expected": "Multiple Spaces"},
            {"title": "\tTabbed\tTitle\t", "expected": "Tabbed Title"},
            {"title": "\nNewline\nTitle\n", "expected": "Newline Title"},
            {"title": " \r\nMixed \r\n Whitespace \r\n ", "expected": "Mixed Whitespace"},
        ]

        for case in whitespace_cases:
            with pytest.raises(ValueError, match="Title contains excessive whitespace"):
                AppIdea(
                    title=case["title"],
                    app_concept="Valid concept",
                    problem_statement="Valid problem",
                    target_audience="Valid audience",
                    core_functions=["valid function"]
                )

    def test_special_character_handling(self):
        """Test special character handling - SHOULD FAIL"""
        # Current implementation may not handle special characters properly

        special_char_cases = [
            {"title": "Title with @#$%", "field": "title"},
            {"concept": "Concept with !@#$%^&*()", "field": "concept"},
            {"problem": "Problem with <>[]{}|", "field": "problem"},
            {"audience": "Audience with ~`-_=+[]{}|\\;:'\",./<>?", "field": "audience"},
            {"functions": ["func with @#$%", "func with !@#"], "field": "functions"},
        ]

        for case in special_char_cases:
            kwargs = {
                "title": "Valid Title",
                "app_concept": "Valid concept",
                "problem_statement": "Valid problem",
                "target_audience": "Valid audience",
                "core_functions": ["valid function"]
            }

            # Update with special characters
            if case["field"] == "functions":
                kwargs["core_functions"] = case["functions"]
            else:
                kwargs[case["field"]] = case[case["field"]]

            idea = AppIdea(**kwargs)

            # This should validate special character handling
            if case["field"] == "functions":
                for func in idea.core_functions:
                    assert any(char in func for char in "@#$%!") or pytest.fail("Special characters not properly handled")

    def test_function_semantic_similarity_detection(self):
        """Test function semantic similarity detection - SHOULD FAIL"""
        # Current implementation only checks exact duplicates

        semantically_similar_functions = [
            ["task management", "task organization"],  # Similar meanings
            ["activity tracking", "activity monitoring"],  # Similar meanings
            ["data analysis", "data processing"],  # Similar domain
            ["user interface", "ui design"],  # Similar domain (abbreviated)
            ["content management", "cms"],  # Similar domain (abbreviated)
        ]

        for similar_funcs in semantically_similar_functions:
            with pytest.raises(ValueError, match="Semantically similar functions detected"):
                AppIdea(
                    title="Similar Functions App",
                    app_concept="App with similar functions",
                    problem_statement="A problem",
                    target_audience="Users",
                    core_functions=similar_funcs
                )

    def test_json_serialization_edge_cases(self):
        """Test JSON serialization edge cases - SHOULD FAIL"""
        # Current implementation may not handle complex JSON serialization

        # Test Unicode characters in JSON
        unicode_idea = AppIdea(
            title="🚀 App with Unicode",
            app_concept="App with 🎯 emojis and special chars £€¥",
            problem_statement="Problem with 🌍 worldwide appeal 🚀",
            target_audience="👥 users worldwide",
            core_functions=["🎯 targeting", "📊 analytics"]
        )

        # Test JSON serialization
        try:
            import json
            serialized = unicode_idea.model_dump_json()
            deserialized = json.loads(serialized)
            assert deserialized["title"] == unicode_idea.title
        except (UnicodeEncodeError, json.JSONDecodeError):
            pytest.fail("Unicode characters not properly handled in JSON serialization")

        # Test circular reference detection (should fail)
        # This would require more complex model structure to test properly


class TestMarketMetricsEdgeCases:
    """Test MarketMetrics model edge case handling - SHOULD FAIL"""

    def test_floating_point_precision(self):
        """Test floating point precision handling - SHOULD FAIL"""
        # Current implementation may not handle floating point precision properly

        # Test very precise values
        precise_metrics = MarketMetrics(
            market_demand=75.123456789,
            pain_intensity=80.987654321,
            monetization_potential=70.555555555,
            competition_level=60.111111111,
            technical_feasibility=85.999999999
        )

        # This should validate precision handling
        assert precise_metrics.market_demand == 75.123456789

        # Test NaN and infinity handling
        invalid_values = [
            {"market_demand": float('nan')},
            {"pain_intensity": float('inf')},
            {"monetization_potential": float('-inf')},
            {"competition_level": float('nan')},
            {"technical_feasibility": float('inf')},
        ]

        for invalid_case in invalid_values:
            with pytest.raises(ValueError, match="Invalid numeric value"):
                kwargs = {
                    "market_demand": 70.0,
                    "pain_intensity": 70.0,
                    "monetization_potential": 70.0,
                    "competition_level": 70.0,
                    "technical_feasibility": 70.0
                }
                kwargs.update(invalid_case)
                MarketMetrics(**kwargs)

    def test_boundary_value_ranges(self):
        """Test boundary value range handling - SHOULD FAIL"""
        # Current implementation may not handle exact boundary values properly

        # Test exact boundary values
        boundary_values = [
            {"value": 0.0, "field": "minimum"},
            {"value": 100.0, "field": "maximum"},
            {"value": 0.000001, "field": "near_zero"},
            {"value": 99.999999, "field": "near_max"},
        ]

        for boundary in boundary_values:
            metrics = MarketMetrics(
                market_demand=boundary["value"],
                pain_intensity=50.0,
                monetization_potential=50.0,
                competition_level=50.0,
                technical_feasibility=50.0
            )

            # This should validate boundary value handling
            if boundary["field"] == "minimum":
                assert metrics.market_demand == 0.0
            elif boundary["field"] == "maximum":
                assert metrics.market_demand == 100.0

        # Test values just outside boundaries (should fail)
        with pytest.raises(ValueError, match="ensure this value is greater than or equal to 0"):
            MarketMetrics(
                market_demand=-0.000001,  # Just below minimum
                pain_intensity=50.0,
                monetization_potential=50.0,
                competition_level=50.0,
                technical_feasibility=50.0
            )

        with pytest.raises(ValueError, match="ensure this value is less than or equal to 100"):
            MarketMetrics(
                market_demand=100.000001,  # Just above maximum
                pain_intensity=50.0,
                monetization_potential=50.0,
                competition_level=50.0,
                technical_feasibility=50.0
            )

    def test_metric_consistency_at_boundaries(self):
        """Test metric consistency at boundaries - SHOULD FAIL"""
        # Current implementation may not validate metric consistency at boundaries

        # Test extreme but consistent metric combinations
        extreme_cases = [
            {
                "market_demand": 0.0,     # No demand
                "pain_intensity": 0.0,     # No pain
                "monetization_potential": 0.0,  # No monetization
                "competition_level": 100.0,     # Max competition
                "technical_feasibility": 0.0,   # No feasibility
            },
            {
                "market_demand": 100.0,    # Max demand
                "pain_intensity": 100.0,    # Max pain
                "monetization_potential": 100.0,  # Max monetization
                "competition_level": 0.0,      # No competition
                "technical_feasibility": 100.0,  # Max feasibility
            },
        ]

        for case in extreme_cases:
            metrics = MarketMetrics(**case)

            # This should validate extreme consistency
            if case["market_demand"] == 0.0:
                # Zero demand should correlate with other metrics
                assert metrics.monetization_potential <= 20.0, "Zero demand should have low monetization"

        # Test inconsistent extreme combinations (should fail)
        with pytest.raises(ValueError, match="Inconsistent extreme metrics"):
            MarketMetrics(
                market_demand=0.0,     # No demand
                pain_intensity=100.0,   # Max pain - inconsistent
                monetization_potential=100.0,  # Max monetization - inconsistent
                competition_level=50.0,
                technical_feasibility=50.0
            )


class TestAnalysisResultEdgeCases:
    """Test AnalysisResult model edge case handling - SHOULD FAIL"""

    def test_embedding_vector_edge_cases(self):
        """Test embedding vector edge cases - SHOULD FAIL"""
        # Current implementation may not handle embedding edge cases

        # Test edge cases for embedding vectors
        embedding_edge_cases = [
            {"embedding": [], "description": "Empty vector"},
            {"embedding": [1.0], "description": "Single dimension"},
            {"embedding": [1.0] * 512, "description": "Standard size"},
            {"embedding": [1.0] * 1536, "description": "Large size"},
            {"embedding": [0.0, 0.0, 0.0], "description": "Zero vector"},
            {"embedding": [1.0, -1.0, 1.0, -1.0], "description": "Mixed signs"},
            {"embedding": [float('inf'), float('-inf')], "description": "Infinite values"},
            {"embedding": [float('nan'), float('nan')], "description": "NaN values"},
        ]

        for case in embedding_edge_cases:
            if "inf" in case["description"] or "nan" in case["description"]:
                with pytest.raises(ValueError, match="Invalid embedding values"):
                    # These should fail due to invalid values
                    pass
            else:
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

                # This should validate embedding handling
                analysis = AnalysisResult(
                    submission_id="test123",
                    app_idea=idea,
                    market_metrics=metrics,
                    final_score=75.0,
                    content_quality_score=78.0,
                    is_spam=False,
                    spam_indicators=[],
                    confidence_score=80.0,
                    trust_level="HIGH",
                    embedding=case["embedding"]
                )

                # Validate embedding properties
                if case["embedding"]:
                    assert all(isinstance(x, (int, float)) for x in analysis.embedding)
                    assert not any(x for x in analysis.embedding if str(x) in ['inf', '-inf', 'nan'])

    def test_timestamp_boundary_handling(self):
        """Test timestamp boundary handling - SHOULD FAIL"""
        # Current implementation may not handle timestamp boundaries

        # Test various timestamp scenarios
        timestamp_cases = [
            {"time": datetime(1970, 1, 1, tzinfo=UTC), "description": "Unix epoch"},
            {"time": datetime(2038, 1, 1, tzinfo=UTC), "description": "Y2K38 issue"},
            {"time": datetime.now(UTC) - timedelta(days=1), "description": "Yesterday"},
            {"time": datetime.now(UTC), "description": "Current"},
        ]

        for case in timestamp_cases:
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

            # This should validate timestamp handling
            analysis = AnalysisResult(
                submission_id="test123",
                app_idea=idea,
                market_metrics=metrics,
                final_score=75.0,
                content_quality_score=78.0,
                is_spam=False,
                spam_indicators=[],
                confidence_score=80.0,
                trust_level="HIGH",
                analyzed_at=case["time"]
            )

            # Validate timestamp properties
            assert analysis.analyzed_at.tzinfo is not None, "Timestamp must have timezone info"
            assert analysis.analyzed_at <= datetime.now(UTC), "Analysis timestamp cannot be in the future"

    def test_model_deep_copy_and_isolation(self):
        """Test model deep copy and isolation - SHOULD FAIL"""
        # Current implementation may not ensure model isolation

        # Create original analysis
        original_idea = AppIdea(
            title="Original App",
            app_concept="Original application",
            problem_statement="Original problem",
            target_audience="Original users",
            core_functions=["original function"]
        )

        original_metrics = MarketMetrics(
            market_demand=70.0,
            pain_intensity=75.0,
            monetization_potential=80.0,
            competition_level=65.0,
            technical_feasibility=85.0
        )

        original_analysis = AnalysisResult(
            submission_id="test123",
            app_idea=original_idea,
            market_metrics=original_metrics,
            final_score=75.0,
            content_quality_score=78.0,
            is_spam=False,
            spam_indicators=[],
            confidence_score=80.0,
            trust_level="HIGH"
        )

        # Test that modifications to original don't affect copies
        try:
            import copy
            analysis_copy = copy.deepcopy(original_analysis)

            # Modify the copy
            analysis_copy.final_score = 90.0
            analysis_copy.trust_level = "LOW"

            # Original should be unchanged
            assert original_analysis.final_score == 75.0, "Original analysis should not be modified"
            assert original_analysis.trust_level == "HIGH", "Original trust level should not be changed"

            # This should validate deep copy handling
            assert analysis_copy.final_score == 90.0, "Copy should have modified score"
            assert analysis_copy.trust_level == "LOW", "Copy should have modified trust level"

        except Exception as e:
            pytest.fail(f"Deep copy failed: {e}")

    def test_large_scale_data_processing(self):
        """Test large scale data processing - SHOULD FAIL"""
        # Current implementation may not handle large-scale data processing

        import time
        start_time = time.time()

        # Process many analysis results
        analyses = []
        for i in range(1000):  # Process 1000 analyses
            idea = AppIdea(
                title=f"App {i}",
                app_concept=f"Application {i}",
                problem_statement=f"Problem {i}",
                target_audience=f"Users {i}",
                core_functions=[f"function {i}"]
            )

            metrics = MarketMetrics(
                market_demand=70.0 + (i % 30),  # Varying values
                pain_intensity=75.0 + (i % 25),
                monetization_potential=80.0 + (i % 20),
                competition_level=65.0 + (i % 15),
                technical_feasibility=85.0 + (i % 10)
            )

            analysis = AnalysisResult(
                submission_id=f"test{i}",
                app_idea=idea,
                market_metrics=metrics,
                final_score=75.0 + (i % 25),
                confidence_score=80.0 + (i % 20),
                trust_level=["LOW", "MEDIUM", "HIGH"][i % 3]
            )
            analyses.append(analysis)

        processing_time = time.time() - start_time

        # This should validate performance with large data
        assert len(analyses) == 1000, f"Should have processed 1000 analyses, got {len(analyses)}"
        assert processing_time < 10.0, f"Processing 1000 analyses took {processing_time:.2f}s, should be < 10s"

        # Verify all analyses are valid
        for i, analysis in enumerate(analyses):
            assert analysis.submission_id == f"test{i}", f"Analysis {i} has wrong submission_id"
            assert analysis.final_score >= 0.0, f"Analysis {i} has negative score"
            assert analysis.final_score <= 100.0, f"Analysis {i} has score over 100"

    def test_concurrent_model_creation(self):
        """Test concurrent model creation - SHOULD FAIL"""
        # Current implementation may not handle concurrent model creation

        import threading
        import time
        from queue import Queue

        results = Queue()
        errors = Queue()

        def create_analysis(thread_id):
            try:
                idea = AppIdea(
                    title=f"Thread {thread_id} App",
                    app_concept=f"Application for thread {thread_id}",
                    problem_statement=f"Problem solved by thread {thread_id}",
                    target_audience=f"Users of thread {thread_id}",
                    core_functions=[f"function {thread_id}"]
                )

                metrics = MarketMetrics(
                    market_demand=70.0 + (thread_id % 30),
                    pain_intensity=75.0 + (thread_id % 25),
                    monetization_potential=80.0 + (thread_id % 20),
                    competition_level=65.0 + (thread_id % 15),
                    technical_feasibility=85.0 + (thread_id % 10)
                )

                analysis = AnalysisResult(
                    submission_id=f"thread{thread_id}",
                    app_idea=idea,
                    market_metrics=metrics,
                    final_score=75.0 + (thread_id % 25),
                    confidence_score=80.0 + (thread_id % 20),
                    trust_level=["LOW", "MEDIUM", "HIGH"][thread_id % 3]
                )

                results.put(analysis)
            except Exception as e:
                errors.put(e)

        # Create multiple threads
        threads = []
        for i in range(50):  # 50 concurrent threads
            thread = threading.Thread(target=create_analysis, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # This should validate concurrent model creation
        assert errors.empty(), f"Concurrent creation caused {errors.qsize()} errors"
        assert results.qsize() == 50, f"Expected 50 analyses, got {results.qsize()}"


class TestOpportunityCreateEdgeCases:
    """Test OpportunityCreate model edge case handling - SHOULD FAIL"""

    def test_database_constraint_validation(self):
        """Test database constraint validation - SHOULD FAIL"""
        # Current implementation may not validate database constraints

        # Test string length constraints that match database
        boundary_cases = [
            {"reddit_title": "a" * 300, "field": "reddit_title", "max": 300},  # Max title
            {"reddit_url": "a" * 500, "field": "reddit_url", "max": 500},      # Max URL
            {"subreddit": "a" * 100, "field": "subreddit", "max": 100},      # Max subreddit
            {"app_title": "a" * 200, "field": "app_title", "max": 200},      # Max app title
        ]

        for case in boundary_cases:
            create = OpportunityCreate(
                submission_id="test123",
                reddit_title=case["reddit_title"] if case["field"] == "reddit_title" else "Valid Title",
                reddit_url=case["reddit_url"] if case["field"] == "reddit_url" else "https://reddit.com/test/test123",
                subreddit=case["subreddit"] if case["field"] == "subreddit" else "test",
                reddit_author="testuser",
                reddit_upvotes=100,
                reddit_comments_count=25,
                reddit_created_at=datetime.now(UTC),
                app_title=case["app_title"] if case["field"] == "app_title" else "Valid App Title",
                app_concept="Valid concept",
                problem_statement="Valid problem",
                target_audience="Valid audience",
                core_functions=["valid function"],
                market_demand=70.0,
                pain_intensity=75.0,
                monetization_potential=80.0,
                competition_level=65.0,
                technical_feasibility=85.0,
                final_score=75.0,
                confidence_score=80.0,
                trust_level="HIGH"
            )

            # This should validate database constraint handling
            if "max" in case:
                assert len(getattr(create, case["field"])) <= case["max"]

        # Test submission ID validation (should be unique and format-constrained)
        with pytest.raises(ValueError, match="Invalid submission ID format"):
            OpportunityCreate(
                submission_id="",  # Empty submission ID
                reddit_title="Valid Title",
                reddit_url="https://reddit.com/test/test123",
                subreddit="test",
                reddit_author="testuser",
                reddit_upvotes=100,
                reddit_comments_count=25,
                reddit_created_at=datetime.now(UTC),
                app_title="Valid App Title",
                app_concept="Valid concept",
                problem_statement="Valid problem",
                target_audience="Valid audience",
                core_functions=["valid function"],
                market_demand=70.0,
                pain_intensity=75.0,
                monetization_potential=80.0,
                competition_level=65.0,
                technical_feasibility=85.0,
                final_score=75.0,
                confidence_score=80.0,
                trust_level="HIGH"
            )

    def test_json_field_validation(self):
        """Test JSON field validation - SHOULD FAIL"""
        # Current implementation may not validate JSON fields properly

        # Test JSON field serialization and validation
        valid_json_cases = [
            {"core_functions": ["func1", "func2", "func3"]},
            {"core_functions": ["long function name that should still be valid", "short"]},
            {"core_functions": ["func with unicode 🚀", "func with symbols @#$%"]},
        ]

        for case in valid_json_cases:
            create = OpportunityCreate(
                submission_id="test123",
                reddit_title="Valid Title",
                reddit_url="https://reddit.com/test/test123",
                subreddit="test",
                reddit_author="testuser",
                reddit_upvotes=100,
                reddit_comments_count=25,
                reddit_created_at=datetime.now(UTC),
                app_title="Valid App Title",
                app_concept="Valid concept",
                problem_statement="Valid problem",
                target_audience="Valid audience",
                core_functions=case["core_functions"],
                market_demand=70.0,
                pain_intensity=75.0,
                monetization_potential=80.0,
                competition_level=65.0,
                technical_feasibility=85.0,
                final_score=75.0,
                confidence_score=80.0,
                trust_level="HIGH"
            )

            # This should validate JSON field handling
            json_str = json.dumps(create.core_functions)
            parsed_back = json.loads(json_str)
            assert parsed_back == create.core_functions

        # Test invalid JSON cases (should fail)
        invalid_json_cases = [
            {"core_functions": "not a list"},  # Should be a list
            {"core_functions": [1, 2, 3]},      # Should be strings
            {"core_functions": [None]},         # Should not contain None
            {"core_functions": [""]},          # Should not contain empty strings
        ]

        for case in invalid_json_cases:
            with pytest.raises(ValueError, match="Invalid JSON field"):
                OpportunityCreate(
                    submission_id="test123",
                    reddit_title="Valid Title",
                    reddit_url="https://reddit.com/test/test123",
                    subreddit="test",
                    reddit_author="testuser",
                    reddit_upvotes=100,
                    reddit_comments_count=25,
                    reddit_created_at=datetime.now(UTC),
                    app_title="Valid App Title",
                    app_concept="Valid concept",
                    problem_statement="Valid problem",
                    target_audience="Valid audience",
                    core_functions=case["core_functions"],
                    market_demand=70.0,
                    pain_intensity=75.0,
                    monetization_potential=80.0,
                    competition_level=65.0,
                    technical_feasibility=85.0,
                    final_score=75.0,
                    confidence_score=80.0,
                    trust_level="HIGH"
                )

    def test_foreign_key_validation(self):
        """Test foreign key validation - SHOULD FAIL"""
        # Current implementation may not validate foreign key constraints

        # Test submission_id format validation (should match Reddit ID format)
        invalid_submission_ids = [
            "",           # Empty
            "a" * 11,     # Too long (Reddit IDs are 6-10 chars)
            "short",      # Too short
            "INVALID",    # Non-alphanumeric
            "123-456",    # Contains hyphens
            None,         # Null value
        ]

        for invalid_id in invalid_submission_ids:
            with pytest.raises(ValueError, match="Invalid submission ID format"):
                OpportunityCreate(
                    submission_id=invalid_id,
                    reddit_title="Valid Title",
                    reddit_url="https://reddit.com/test/test123",
                    subreddit="test",
                    reddit_author="testuser",
                    reddit_upvotes=100,
                    reddit_comments_count=25,
                    reddit_created_at=datetime.now(UTC),
                    app_title="Valid App Title",
                    app_concept="Valid concept",
                    problem_statement="Valid problem",
                    target_audience="Valid audience",
                    core_functions=["valid function"],
                    market_demand=70.0,
                    pain_intensity=75.0,
                    monetization_potential=80.0,
                    competition_level=65.0,
                    technical_feasibility=85.0,
                    final_score=75.0,
                    confidence_score=80.0,
                    trust_level="HIGH"
                )

        # Test valid submission ID format
        valid_submission_ids = [
            "abc123",
            "test456",
            "submission7",
            "id89",
            "abcdefghij",  # 10 chars (max)
        ]

        for valid_id in valid_submission_ids:
            create = OpportunityCreate(
                submission_id=valid_id,
                reddit_title="Valid Title",
                reddit_url="https://reddit.com/test/test123",
                subreddit="test",
                reddit_author="testuser",
                reddit_upvotes=100,
                reddit_comments_count=25,
                reddit_created_at=datetime.now(UTC),
                app_title="Valid App Title",
                app_concept="Valid concept",
                problem_statement="Valid problem",
                target_audience="Valid audience",
                core_functions=["valid function"],
                market_demand=70.0,
                pain_intensity=75.0,
                monetization_potential=80.0,
                competition_level=65.0,
                technical_feasibility=85.0,
                final_score=75.0,
                confidence_score=80.0,
                trust_level="HIGH"
            )

            # This should validate submission ID format
            assert len(valid_id) >= 6 and len(valid_id) <= 10
            assert valid_id.isalnum()

    def test_datetime_boundary_values(self):
        """Test datetime boundary values - SHOULD FAIL"""
        # Current implementation may not handle datetime boundaries

        # Test various datetime scenarios
        datetime_cases = [
            {"created_at": datetime(1970, 1, 1, tzinfo=UTC), "description": "Unix epoch"},
            {"created_at": datetime(2030, 1, 1, tzinfo=UTC), "description": "Future but reasonable"},
            {"created_at": datetime.now(UTC) - timedelta(days=365), "description": "One year old"},
        ]

        for case in datetime_cases:
            create = OpportunityCreate(
                submission_id="test123",
                reddit_title="Valid Title",
                reddit_url="https://reddit.com/test/test123",
                subreddit="test",
                reddit_author="testuser",
                reddit_upvotes=100,
                reddit_comments_count=25,
                reddit_created_at=case["created_at"],
                app_title="Valid App Title",
                app_concept="Valid concept",
                problem_statement="Valid problem",
                target_audience="Valid audience",
                core_functions=["valid function"],
                market_demand=70.0,
                pain_intensity=75.0,
                monetization_potential=80.0,
                competition_level=65.0,
                technical_feasibility=85.0,
                final_score=75.0,
                confidence_score=80.0,
                trust_level="HIGH"
            )

            # This should validate datetime handling
            assert create.reddit_created_at.tzinfo is not None, "DateTime must have timezone info"
            assert create.reddit_created_at <= datetime.now(UTC), "Created date cannot be in the future"

            # Test very old dates (should fail validation)
            very_old_date = datetime(2005, 1, 1, tzinfo=UTC)  # Before Reddit really existed
            with pytest.raises(ValueError, match="Date is too old"):
                OpportunityCreate(
                    submission_id="test123",
                    reddit_title="Valid Title",
                    reddit_url="https://reddit.com/test/test123",
                    subreddit="test",
                    reddit_author="testuser",
                    reddit_upvotes=100,
                    reddit_comments_count=25,
                    reddit_created_at=very_old_date,
                    app_title="Valid App Title",
                    app_concept="Valid concept",
                    problem_statement="Valid problem",
                    target_audience="Valid audience",
                    core_functions=["valid function"],
                    market_demand=70.0,
                    pain_intensity=75.0,
                    monetization_potential=80.0,
                    competition_level=65.0,
                    technical_feasibility=85.0,
                    final_score=75.0,
                    confidence_score=80.0,
                    trust_level="HIGH"
                )

    def test_database_field_mapping_consistency(self):
        """Test database field mapping consistency - SHOULD FAIL"""
        # Current implementation may not ensure consistency between model and database

        # Create an instance and verify field consistency
        create = OpportunityCreate(
            submission_id="test123",
            reddit_title="Test Title for Database Validation",
            reddit_url="https://reddit.com/test/test123",
            subreddit="test",
            reddit_author="testuser",
            reddit_upvotes=100,
            reddit_comments_count=25,
            reddit_created_at=datetime.now(UTC),
            app_title="Test App Title",
            app_concept="Test app concept for database validation",
            problem_statement="Test problem statement for database validation",
            target_audience="Test target audience for database validation",
            core_functions=["test function 1", "test function 2", "test function 3"],
            market_demand=70.0,
            pain_intensity=75.0,
            monetization_potential=80.0,
            competition_level=65.0,
            technical_feasibility=85.0,
            final_score=75.0,
            confidence_score=80.0,
            trust_level="HIGH"
        )

        # This should validate database field mapping
        # Convert to database model and check consistency
        db_model = create.to_db_model()

        assert db_model.submission_id == create.submission_id
        assert db_model.reddit_title == create.reddit_title
        assert db_model.reddit_url == create.reddit_url
        assert db_model.subreddit == create.subreddit
        assert db_model.reddit_upvotes == create.reddit_upvotes
        assert db_model.reddit_comments_count == create.reddit_comments_count
        assert db_model.reddit_created_at == create.reddit_created_at
        assert db_model.app_title == create.app_title
        assert db_model.app_concept == create.app_concept
        assert db_model.problem_statement == create.problem_statement
        assert db_model.target_audience == create.target_audience
        assert db_model.core_functions == create.core_functions
        assert db_model.market_demand == create.market_demand
        assert db_model.pain_intensity == create.pain_intensity
        assert db_model.monetization_potential == create.monetization_potential
        assert db_model.competition_level == create.competition_level
        assert db_model.technical_feasibility == create.technical_feasibility
        assert db_model.final_score == create.final_score
        assert db_model.confidence_score == create.confidence_score
        assert db_model.trust_level == create.trust_level

        # Test for data truncation (should not occur)
        assert len(db_model.reddit_title) == len(create.reddit_title)
        assert len(db_model.app_title) == len(create.app_title)
