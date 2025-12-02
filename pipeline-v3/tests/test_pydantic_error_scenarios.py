"""
DEBT-005: Error Scenario Tests - These tests are designed to FAIL and expose error handling gaps

This test suite validates that our Pydantic models handle error scenarios gracefully,
including malformed data, serialization failures, and unexpected inputs.
"""

import pytest
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Union
import json
from decimal import Decimal

from models.reddit import RedditSubmission, RedditComment
from models.analysis import AppIdea, MarketMetrics, AnalysisResult
from models.database import OpportunityCreate


class TestRedditSubmissionErrorScenarios:
    """Test RedditSubmission model error scenario handling - SHOULD FAIL"""

    def test_malformed_reddit_data_structure(self):
        """Test malformed Reddit data structure handling - SHOULD FAIL"""
        # Current implementation may not handle malformed Reddit API responses

        malformed_data_cases = [
            {
                "id": None,  # Missing required field
                "title": "Test Title",
                "text": "Test content",
                "author": "testuser",
                "upvotes": 100,
                "score": 100,
                "comments_count": 25,
                "subreddit": "test",
                "created_utc": datetime.now(timezone.utc),
                "permalink": "https://reddit.com/r/test/test123"
            },
            {
                "id": "test123",
                "title": None,  # Missing required field
                "text": "Test content",
                "author": "testuser",
                "upvotes": 100,
                "score": 100,
                "comments_count": 25,
                "subreddit": "test",
                "created_utc": datetime.now(timezone.utc),
                "permalink": "https://reddit.com/r/test/test123"
            },
            {
                "id": "test123",
                "title": "Test Title",
                "text": "Test content",
                "author": "testuser",
                "upvotes": None,  # Missing required numeric field
                "score": 100,
                "comments_count": 25,
                "subreddit": "test",
                "created_utc": datetime.now(timezone.utc),
                "permalink": "https://reddit.com/r/test/test123"
            },
            {
                "id": "test123",
                "title": "Test Title",
                "text": "Test content",
                "author": "testuser",
                "upvotes": "not-a-number",  # Invalid type for numeric field
                "score": 100,
                "comments_count": 25,
                "subreddit": "test",
                "created_utc": datetime.now(timezone.utc),
                "permalink": "https://reddit.com/r/test/test123"
            },
            {
                "id": "test123",
                "title": "Test Title",
                "text": "Test content",
                "author": "testuser",
                "upvotes": 100,
                "score": 100,
                "comments_count": 25,
                "subreddit": "test",
                "created_utc": "not-a-datetime",  # Invalid datetime format
                "permalink": "https://reddit.com/r/test/test123"
            },
        ]

        for i, malformed_data in enumerate(malformed_data_cases):
            with pytest.raises((ValueError, TypeError), match=".*"):
                # These should fail with clear error messages
                RedditSubmission(**malformed_data)

    def test_reddit_api_response_simulation(self):
        """Test Reddit API response simulation with errors - SHOULD FAIL"""
        # Current implementation may not handle API response variations

        # Simulate Reddit API error responses
        api_error_responses = [
            {
                "error": "RATE_LIMIT_EXCEEDED",
                "message": "You are doing that too much. Try again later.",
                "retry_after": 900
            },
            {
                "error": "INVALID_TOKEN",
                "message": "Invalid OAuth token"
            },
            {
                "error": "SUBREDDIT_NOT_FOUND",
                "message": "no subreddit exists with that name"
            },
            {
                "error": "USER_NOT_FOUND",
                "message": "USER_NOT_FOUND"
            },
            {
                "error": "THREAD_LOCKED",
                "message": "thread is locked"
            },
        ]

        for error_response in api_error_responses:
            # This should fail because we can't create a submission from an error response
            with pytest.raises(ValueError, match=f"Reddit API error: {error_response['error']}"):
                # Attempt to create submission from error response (should fail)
                RedditSubmission(
                    id="error123",
                    title=error_response.get("message", "Error Response"),
                    text=f"API Error: {error_response['error']}",
                    author="system",
                    upvotes=0,
                    score=0,
                    comments_count=0,
                    subreddit="error",
                    created_utc=datetime.now(timezone.utc),
                    permalink="https://reddit.com/r/error/error123"
                )

    def test_database_constraint_violation(self):
        """Test database constraint violation handling - SHOULD FAIL"""
        # Current implementation may not handle database constraint violations

        # Simulate duplicate submission ID scenario
        duplicate_submissions = [
            {
                "id": "duplicate123",
                "title": "First submission",
                "text": "First content",
                "author": "user1",
                "upvotes": 100,
                "score": 100,
                "comments_count": 25,
                "subreddit": "test",
                "created_utc": datetime.now(timezone.utc),
                "permalink": "https://reddit.com/r/test/duplicate123"
            },
            {
                "id": "duplicate123",  # Same ID - should cause constraint violation
                "title": "Second submission",
                "text": "Second content",
                "author": "user2",
                "upvotes": 50,
                "score": 50,
                "comments_count": 10,
                "subreddit": "test",
                "created_utc": datetime.now(timezone.utc),
                "permalink": "https://reddit.com/r/test/duplicate123"
            }
        ]

        # Create first submission
        first_submission = RedditSubmission(**duplicate_submissions[0])

        # Try to create duplicate (should fail with constraint violation)
        with pytest.raises(ValueError, match="Duplicate submission ID"):
            RedditSubmission(**duplicate_submissions[1])

        # Test unique constraint simulation
        try:
            # This would normally be handled by the database layer
            # but our model should detect potential duplicates
            assert first_submission.id != duplicate_submissions[1]["id"], "Duplicate IDs should be rejected"
        except AssertionError:
            pytest.fail("Duplicate submission ID detection failed")

    def test_serialization_deserialization_errors(self):
        """Test serialization/deserialization error handling - SHOULD FAIL"""
        # Current implementation may not handle serialization errors

        # Create a valid submission
        submission = RedditSubmission(
            id="test123",
            title="Test Title",
            text="Test content",
            author="testuser",
            upvotes=100,
            score=100,
            comments_count=25,
            subreddit="test",
            created_utc=datetime.now(timezone.utc),
            permalink="https://reddit.com/r/test/test123"
        )

        # Test JSON serialization
        try:
            json_str = submission.model_dump_json()
            parsed_back = json.loads(json_str)
        except (json.JSONDecodeError, TypeError) as e:
            pytest.fail(f"JSON serialization failed: {e}")

        # Test invalid deserialization data
        invalid_json_data = [
            "",                           # Empty string
            "not-json",                   # Invalid JSON
            '{"invalid": "structure"}',   # Wrong structure
            '{"id": null}',               # Missing required fields
            '{"id": 123}',                # Wrong type
            '{"id": "test", "title": {}}', # Nested invalid structure
        ]

        for invalid_json in invalid_json_data:
            with pytest.raises((json.JSONDecodeError, ValueError, TypeError)):
                # Attempt to deserialize invalid JSON
                RedditSubmission.model_validate_json(invalid_json)

        # Test corrupted datetime handling
        corrupted_json = '{"id": "test123", "title": "Test", "text": "Content", "author": "user", "upvotes": 100, "score": 100, "comments_count": 25, "subreddit": "test", "created_utc": "corrupted-date", "permalink": "https://reddit.com/r/test/test123"}'

        with pytest.raises(ValueError, match="Invalid datetime format"):
            RedditSubmission.model_validate_json(corrupted_json)

    def test_memory_allocation_errors(self):
        """Test memory allocation error simulation - SHOULD FAIL"""
        # Current implementation may not handle memory allocation issues

        # Test extremely large string allocation
        try:
            # This should fail due to memory constraints
            extremely_large_title = "a" * (10**9)  # 1GB string - should fail
            submission = RedditSubmission(
                id="test123",
                title=extremely_large_title,
                text="Test content",
                author="testuser",
                upvotes=100,
                score=100,
                comments_count=25,
                subreddit="test",
                created_utc=datetime.now(timezone.utc),
                permalink="https://reddit.com/r/test/test123"
            )
        except MemoryError:
            pytest.fail("Memory allocation should be handled gracefully")
        except Exception as e:
            # This should fail with appropriate error handling
            assert "Memory" in str(e) or "Size" in str(e)

        # Test memory allocation in bulk operations
        try:
            # Create many large objects to test memory limits
            large_objects = []
            for i in range(10000):  # 10,000 large objects
                large_text = "a" * 10000  # 10KB per object = 100MB total
                submission = RedditSubmission(
                    id=f"large{i}",
                    title=f"Large Object {i}",
                    text=large_text,
                    author=f"user{i}",
                    upvotes=100,
                    score=100,
                    comments_count=25,
                    subreddit="test",
                    created_utc=datetime.now(timezone.utc),
                    permalink="https://reddit.com/r/test/large{i}"
                )
                large_objects.append(submission)

            # This should validate memory usage
            import sys
            total_memory = sum(sys.getsizeof(obj) for obj in large_objects)
            assert total_memory < 500 * 1024 * 1024, f"Memory usage {total_memory} exceeds 500MB limit"

        except MemoryError:
            pytest.fail("Bulk memory allocation should be handled gracefully")

    def test_type_conversion_errors(self):
        """Test type conversion error handling - SHOULD FAIL"""
        # Current implementation may not handle type conversion errors

        type_error_cases = [
            {
                "id": 123,  # Should be string, not int
                "title": "Test Title",
                "text": "Test content",
                "author": "testuser",
                "upvotes": 100,
                "score": 100,
                "comments_count": 25,
                "subreddit": "test",
                "created_utc": datetime.now(timezone.utc),
                "permalink": "https://reddit.com/r/test/test123"
            },
            {
                "id": "test123",
                "title": 456,  # Should be string, not int
                "text": "Test content",
                "author": "testuser",
                "upvotes": 100,
                "score": 100,
                "comments_count": 25,
                "subreddit": "test",
                "created_utc": datetime.now(timezone.utc),
                "permalink": "https://reddit.com/r/test/test123"
            },
            {
                "id": "test123",
                "title": "Test Title",
                "text": "Test content",
                "author": "testuser",
                "upvotes": "100",  # String instead of int
                "score": 100,
                "comments_count": 25,
                "subreddit": "test",
                "created_utc": datetime.now(timezone.utc),
                "permalink": "https://reddit.com/r/test/test123"
            },
            {
                "id": "test123",
                "title": "Test Title",
                "text": "Test content",
                "author": "testuser",
                "upvotes": 100,
                "score": "100",  # String instead of int
                "comments_count": 25,
                "subreddit": "test",
                "created_utc": datetime.now(timezone.utc),
                "permalink": "https://reddit.com/r/test/test123"
            },
        ]

        for i, type_error_case in enumerate(type_error_cases):
            with pytest.raises((TypeError, ValueError), match=".*"):
                RedditSubmission(**type_error_case)

        # Test numeric conversion edge cases
        numeric_edge_cases = [
            {"upvotes": "999999999999999999999999999999", "score": 100},  # Extremely large number
            {"upvotes": -999999999999999999999999999999, "score": 100},  # Extremely negative number
            {"upvotes": 100, "score": "999999999999999999999999999999"},  # Large score
            {"upvotes": 100, "score": "not-a-number"},  # Non-numeric score
        ]

        for edge_case in numeric_edge_cases:
            with pytest.raises((ValueError, TypeError), match=".*"):
                RedditSubmission(
                    id="test123",
                    title="Test Title",
                    text="Test content",
                    author="testuser",
                    upvotes=edge_case["upvotes"],
                    score=edge_case["score"],
                    comments_count=25,
                    subreddit="test",
                    created_utc=datetime.now(timezone.utc),
                    permalink="https://reddit.com/r/test/test123"
                )


class TestRedditCommentErrorScenarios:
    """Test RedditComment model error scenario handling - SHOULD FAIL"""

    def test_missing_parent_submission_error(self):
        """Test missing parent submission error handling - SHOULD FAIL"""
        # Current implementation may not validate parent submission existence

        # Simulate comment without parent submission
        orphan_comment = RedditComment(
            id="comment123",
            submission_id="nonexistent123",  # Should validate this exists
            author="testuser",
            text="Orphan comment",
            upvotes=10,
            created_utc=datetime.now(timezone.utc)
        )

        # This should validate parent submission existence
        # In a real system, this would check against the submissions database
        try:
            # Simulate database lookup for nonexistent submission
            assert "nonexistent123" != "real_submission_id", "Parent submission should exist"
        except AssertionError:
            pytest.fail("Orphan comment should be rejected")

    def test_comment_hierarchy_loop_error(self):
        """Test comment hierarchy loop error handling - SHOULD FAIL"""
        # Current implementation may not detect hierarchy loops

        # Simulate a comment hierarchy loop
        # comment1 -> comment2 -> comment3 -> comment1 (loop)
        loop_comments = [
            {
                "id": "comment1",
                "submission_id": "submission123",
                "author": "user1",
                "text": "First level comment",
                "upvotes": 10,
                "created_utc": datetime.now(timezone.utc)
            },
            {
                "id": "comment2",
                "submission_id": "comment1",  # Points to comment1
                "author": "user2",
                "text": "Second level comment",
                "upvotes": 8,
                "created_utc": datetime.now(timezone.utc)
            },
            {
                "id": "comment3",
                "submission_id": "comment2",  # Points to comment2
                "author": "user3",
                "text": "Third level comment (creates loop)",
                "upvotes": 5,
                "created_utc": datetime.now(timezone.utc)
            },
            {
                "id": "comment4",
                "submission_id": "comment3",  # Would complete the loop if pointing to comment1
                "author": "user4",
                "text": "Fourth level comment (would create loop)",
                "upvotes": 3,
                "created_utc": datetime.now(timezone.utc)
            }
        ]

        # Create comments
        created_comments = {}
        for comment_data in loop_comments:
            comment = RedditComment(**comment_data)
            created_comments[comment.id] = comment

        # Check for hierarchy loops (should fail if detected)
        def detect_loops(comment_id, visited=None, path=None):
            if visited is None:
                visited = set()
            if path is None:
                path = []

            if comment_id in visited:
                return True, path + [comment_id]  # Loop detected
            if comment_id in path:
                return True, path[path.index(comment_id):] + [comment_id]  # Loop detected

            visited.add(comment_id)
            path.append(comment_id)

            # Get submission_id (parent)
            comment = created_comments.get(comment_id)
            if comment and comment.submission_id in created_comments:
                loop, loop_path = detect_loops(comment.submission_id, visited, path)
                if loop:
                    return loop, loop_path

            visited.remove(comment_id)
            path.pop()
            return False, []

        # Check each comment for loops
        for comment_id in created_comments:
            has_loop, loop_path = detect_loops(comment_id)
            if has_loop:
                pytest.fail(f"Comment hierarchy loop detected: {' -> '.join(loop_path)}")

    def test_spam_comment_detection(self):
        """Test spam comment detection - SHOULD FAIL"""
        # Current implementation may not detect spam comments

        spam_indicators = [
            "Check out my website: spammy-site.com",  # URL spam
            "👉 http://spam-link.com",              # Emoji + spam
            "Free money! Click here!",              # Obvious scam
            "upvote if you agree",                  # Vote manipulation
            "I am a bot",                           # Bot declaration
            "This is an automated message",         # Automated content
            "+++",                                  # Gibberish
            "asdfghjkl",                           # Random characters
            "www.spam-site.com",                    # Bare domain
            "email@spam.com",                      # Email spam
        ]

        for spam_text in spam_indicators:
            with pytest.raises(ValueError, match="Spam comment detected"):
                RedditComment(
                    id="spam123",
                    submission_id="test123",
                    author="spammer",
                    text=spam_text,
                    upvotes=0,
                    created_utc=datetime.now(timezone.utc)
                )

    def test_comment_velocity_spam_detection(self):
        """Test comment velocity spam detection - SHOULD FAIL"""
        # Current implementation may not detect velocity-based spam

        # Simulate user posting many comments in short time
        rapid_comments = []
        base_time = datetime.now(timezone.utc)

        for i in range(100):  # 100 comments in rapid succession
            comment_time = base_time + timedelta(milliseconds=i * 50)  # Every 50ms
            comment = RedditComment(
                id=f"rapid_comment_{i}",
                submission_id="test123",
                author="rapid_poster",
                text=f"Rapid comment {i}",
                upvotes=0,
                created_utc=comment_time
            )
            rapid_comments.append(comment)

        # Check for velocity-based spam patterns
        time_differences = []
        for i in range(1, len(rapid_comments)):
            diff = (rapid_comments[i].created_utc - rapid_comments[i-1].created_utc).total_seconds()
            time_differences.append(diff)

        avg_interval = sum(time_differences) / len(time_differences)
        total_comments = len(rapid_comments)

        # Velocity-based spam detection rules
        if avg_interval < 1.0 and total_comments > 50:  # Very fast posting with many comments
            pytest.fail("Velocity-based spam detected: user posted too many comments too quickly")

    def test_comment_moderation_bypass(self):
        """Test comment moderation bypass detection - SHOULD FAIL"""
        # Current implementation may not detect moderation bypass attempts

        bypass_attempts = [
            {
                "text": "badword with spaces",      # Obfuscation with spaces
                "detection": "Space-separated bypass"
            },
            {
                "text": "bad.word",                 # Obfuscation with dots
                "detection": "Dot-separated bypass"
            },
            {
                "text": "b4dword",                  # Leetspeak
                "detection": "Leetspeak bypass"
            },
            {
                "text": "b a d w o r d",            # Character separation
                "detection": "Character separation bypass"
            },
            {
                "text": "bad-word",                 # Hyphen separation
                "detection": "Hyphen separation bypass"
            },
        ]

        for bypass_case in bypass_attempts:
            with pytest.raises(ValueError, match="Moderation bypass detected"):
                RedditComment(
                    id="bypass123",
                    submission_id="test123",
                    author="bypass_user",
                    text=bypass_case["text"],
                    upvotes=0,
                    created_utc=datetime.now(timezone.utc)
                )


class TestAppIdeaErrorScenarios:
    """Test AppIdea model error scenario handling - SHOULD FAIL"""

    def test_idea_rejection_scenarios(self):
        """Test idea rejection scenarios - SHOULD FAIL"""
        # Current implementation may not validate business logic for rejection

        rejection_cases = [
            {
                "title": "Spam App",
                "concept": "Make money fast!",
                "problem_statement": "People want money",
                "target_audience": "Everyone who wants money",
                "core_functions": ["make money", "get rich quick"],
                "rejection_reason": "Spam-like content detected"
            },
            {
                "title": "Illegal App",
                "concept": "App for illegal activities",
                "problem_statement": "Need illegal solutions",
                "target_audience": "Criminals",
                "core_functions": ["illegal_function_1", "illegal_function_2"],
                "rejection_reason": "Illegal content detected"
            },
            {
                "title": "Duplicate App",
                "concept": "Another generic social media app",
                "problem_statement": "People want to connect",
                "target_audience": "Everyone",
                "core_functions": ["post", "like", "share"],
                "rejection_reason": "Generic/duplicate concept detected"
            },
        ]

        for rejection_case in rejection_cases:
            with pytest.raises(ValueError, match=rejection_case["rejection_reason"]):
                AppIdea(
                    title=rejection_case["title"],
                    app_concept=rejection_case["concept"],
                    problem_statement=rejection_case["problem_statement"],
                    target_audience=rejection_case["target_audience"],
                    core_functions=rejection_case["core_functions"]
                )

    def test_invalid_app_categories(self):
        """Test invalid app category detection - SHOULD FAIL"""
        # Current implementation may not validate app categories

        invalid_categories = [
            {
                "title": "Harmful App",
                "concept": "App that encourages harmful behavior",
                "problem_statement": "People want to hurt others",
                "target_audience": "People who want to cause harm",
                "core_functions": ["harmful_function"],
                "category": "Harmful/Illegal"
            },
            {
                "title": "Scam App",
                "concept": "App designed to defraud users",
                "problem_statement": "People want to steal money",
                "target_audience": "Potential victims",
                "core_functions": ["scam_users", "steal_data"],
                "category": "Fraud/Scam"
            },
            {
                "title": "Misleading App",
                "concept": "App that promises what it can't deliver",
                "problem_statement": "People fall for false promises",
                "target_audience": "Gullible people",
                "core_functions": ["make_false_promises", "deliver_nothing"],
                "category": "Misleading/Deceptive"
            },
        ]

        for invalid_case in invalid_categories:
            with pytest.raises(ValueError, match=f"Invalid app category: {invalid_case['category']}"):
                AppIdea(
                    title=invalid_case["title"],
                    app_concept=invalid_case["concept"],
                    problem_statement=invalid_case["problem_statement"],
                    target_audience=invalid_case["target_audience"],
                    core_functions=invalid_case["core_functions"]
                )

    def test_business_model_validation_errors(self):
        """Test business model validation errors - SHOULD FAIL"""
        # Current implementation may not validate business models

        invalid_business_models = [
            {
                "title": "Free App with Premium Features",
                "concept": "App that requires subscription but offers no value",
                "problem_statement": "People want free stuff",
                "target_audience": "Everyone who wants free stuff",
                "core_functions": ["limited_functionality"],
                "monetization_issue": "No value justification for premium features"
            },
            {
                "title": "High-Cost App with Low Market",
                "concept": "Enterprise app for tiny market",
                "problem_statement": "Specific niche problem",
                "target_audience": "Very small audience",
                "core_functions": ["expensive_enterprise_function"],
                "monetization_issue": "High development cost for small market"
            },
            {
                "title": "App No One Will Pay For",
                "concept": "Nice-to-have but not essential",
                "problem_statement": "Minor convenience issue",
                "target_audience": "People with disposable income",
                "core_functions": ["convenience_feature"],
                "monetization_issue": "Not valuable enough to monetize"
            },
        ]

        for business_case in invalid_business_models:
            with pytest.raises(ValueError, match=business_case["monetization_issue"]):
                AppIdea(
                    title=business_case["title"],
                    app_concept=business_case["concept"],
                    problem_statement=business_case["problem_statement"],
                    target_audience=business_case["target_audience"],
                    core_functions=business_case["core_functions"]
                )

    def test_technical_feasibility_errors(self):
        """Test technical feasibility error handling - SHOULD FAIL"""
        # Current implementation may not validate technical feasibility

        impossible_requirements = [
            {
                "title": "Mind Reading App",
                "concept": "App that reads users' thoughts",
                "problem_statement": "People want others to read their minds",
                "target_audience": "Everyone",
                "core_functions": ["read_minds", "decode_thoughts"],
                "feasibility_issue": "Technologically impossible with current technology"
            },
            {
                "title": "Time Travel App",
                "concept": "App that allows users to travel through time",
                "problem_statement": "People want to change the past",
                "target_audience": "Everyone",
                "core_functions": ["travel_to_past", "travel_to_future"],
                "feasibility_issue": "Violates known laws of physics"
            },
            {
                "title": "Perfect AI App",
                "concept": "App with perfect AI requiring no training",
                "problem_statement": "People want perfect AI",
                "target_audience": "Everyone",
                "core_functions": ["perfect_ai", "infinite_intelligence"],
                "feasibility_issue": "Requires breakthrough AI research"
            },
        ]

        for impossible_case in impossible_requirements:
            with pytest.raises(ValueError, match=impossible_case["feasibility_issue"]):
                AppIdea(
                    title=impossible_case["title"],
                    app_concept=impossible_case["concept"],
                    problem_statement=impossible_case["problem_statement"],
                    target_audience=impossible_case["target_audience"],
                    core_functions=impossible_case["core_functions"]
                )


class TestMarketMetricsErrorScenarios:
    """Test MarketMetrics model error scenario handling - SHOULD FAIL"""

    def test_metric_validation_errors(self):
        """Test metric validation errors - SHOULD FAIL"""
        # Current implementation may not validate metric relationships

        invalid_metric_combinations = [
            {
                "market_demand": 0.0,      # No demand
                "pain_intensity": 0.0,      # No pain
                "monetization_potential": 100.0,  # High monetization - inconsistent
                "competition_level": 50.0,
                "technical_feasibility": 50.0,
                "error": "Inconsistent metrics: no demand but high monetization"
            },
            {
                "market_demand": 100.0,    # Max demand
                "pain_intensity": 10.0,     # Low pain - inconsistent
                "monetization_potential": 20.0,  # Low monetization - inconsistent
                "competition_level": 90.0,     # High competition
                "technical_feasibility": 10.0,  # Low feasibility
                "error": "Inconsistent metrics: high demand with low pain and monetization"
            },
            {
                "market_demand": 50.0,
                "pain_intensity": 50.0,
                "monetization_potential": 50.0,
                "competition_level": 0.0,      # No competition
                "technical_feasibility": 5.0,   # Low feasibility
                "error": "Inconsistent metrics: no competition with low feasibility"
            },
        ]

        for invalid_case in invalid_metric_combinations:
            with pytest.raises(ValueError, match=invalid_case["error"]):
                MarketMetrics(**invalid_case)

    def test_extreme_metric_value_errors(self):
        """Test extreme metric value errors - SHOULD FAIL"""
        # Current implementation may not handle extreme metric values

        extreme_value_cases = [
            {
                "market_demand": 999.9,     # Way over 100
                "pain_intensity": 999.9,
                "monetization_potential": 999.9,
                "competition_level": 999.9,
                "technical_feasibility": 999.9,
                "error": "Extreme values exceed reasonable bounds"
            },
            {
                "market_demand": -999.9,    # Way below 0
                "pain_intensity": -999.9,
                "monetization_potential": -999.9,
                "competition_level": -999.9,
                "technical_feasibility": -999.9,
                "error": "Negative values below minimum bounds"
            },
            {
                "market_demand": float('inf'),  # Infinite values
                "pain_intensity": float('inf'),
                "monetization_potential": float('inf'),
                "competition_level": float('inf'),
                "technical_feasibility": float('inf'),
                "error": "Infinite values not allowed"
            },
            {
                "market_demand": float('nan'),  # NaN values
                "pain_intensity": float('nan'),
                "monetization_potential": float('nan'),
                "competition_level": float('nan'),
                "technical_feasibility": float('nan'),
                "error": "NaN values not allowed"
            },
        ]

        for extreme_case in extreme_value_cases:
            with pytest.raises(ValueError, match=extreme_case["error"]):
                MarketMetrics(**extreme_case)

    def test_metric_consistency_errors(self):
        """Test metric consistency error handling - SHOULD FAIL"""
        # Current implementation may not validate metric consistency

        inconsistent_metrics = [
            {
                "market_demand": 90.0,      # High demand
                "pain_intensity": 10.0,      # Low pain - inconsistent
                "monetization_potential": 10.0,  # Low monetization - inconsistent
                "competition_level": 90.0,     # High competition - expected with high demand
                "technical_feasibility": 90.0,  # High feasibility
                "error": "High demand should correlate with high pain and monetization"
            },
            {
                "market_demand": 10.0,      # Low demand
                "pain_intensity": 90.0,      # High pain - inconsistent
                "monetization_potential": 90.0,  # High monetization - inconsistent
                "competition_level": 10.0,     # Low competition - expected with low demand
                "technical_feasibility": 90.0,  # High feasibility
                "error": "Low demand should correlate with low pain and monetization"
            },
            {
                "market_demand": 50.0,
                "pain_intensity": 50.0,
                "monetization_potential": 50.0,
                "competition_level": 90.0,     # Very high competition
                "technical_feasibility": 10.0,  # Very low feasibility
                "error": "Very high competition should correlate with higher feasibility"
            },
        ]

        for inconsistent_case in inconsistent_metrics:
            with pytest.raises(ValueError, match=inconsistent_case["error"]):
                MarketMetrics(**inconsistent_case)


class TestAnalysisResultErrorScenarios:
    """Test AnalysisResult model error scenario handling - SHOULD FAIL"""

    def test_cross_model_consistency_errors(self):
        """Test cross-model consistency error handling - SHOULD FAIL"""
        # Current implementation may not validate cross-model consistency

        inconsistent_analyses = [
            {
                "app_idea": {
                    "title": "Simple App",
                    "app_concept": "Very simple app idea",
                    "problem_statement": "Simple problem",
                    "target_audience": "General audience",
                    "core_functions": ["simple_function"]
                },
                "market_metrics": {
                    "market_demand": 10.0,      # Low demand
                    "pain_intensity": 10.0,      # Low pain
                    "monetization_potential": 90.0,  # High monetization - inconsistent
                    "competition_level": 90.0,     # High competition
                    "technical_feasibility": 10.0   # Low feasibility
                },
                "final_score": 90.0,        # High score - inconsistent
                "confidence_score": 90.0,    # High confidence - inconsistent
                "error": "Simple idea with low metrics cannot have high score"
            },
            {
                "app_idea": {
                    "title": "Complex App",
                    "app_concept": "Very complex app with advanced features",
                    "problem_statement": "Complex problem requiring advanced technology",
                    "target_audience": "Technical experts",
                    "core_functions": ["complex_function_1", "complex_function_2", "complex_function_3"]
                },
                "market_metrics": {
                    "market_demand": 90.0,      # High demand
                    "pain_intensity": 90.0,      # High pain
                    "monetization_potential": 90.0,  # High monetization
                    "competition_level": 10.0,     # Low competition
                    "technical_feasibility": 10.0   # Low feasibility - inconsistent
                },
                "final_score": 90.0,        # High score - inconsistent
                "confidence_score": 90.0,    # High confidence - inconsistent
                "error": "Complex idea with low feasibility cannot have high score"
            },
        ]

        for inconsistent_case in inconsistent_analyses:
            app_idea = AppIdea(**inconsistent_case["app_idea"])
            market_metrics = MarketMetrics(**inconsistent_case["market_metrics"])

            with pytest.raises(ValueError, match=inconsistent_case["error"]):
                AnalysisResult(
                    submission_id="test123",
                    app_idea=app_idea,
                    market_metrics=market_metrics,
                    final_score=inconsistent_case["final_score"],
                    confidence_score=inconsistent_case["confidence_score"],
                    trust_level="HIGH"
                )

    def test_embedding_vector_errors(self):
        """Test embedding vector error handling - SHOULD FAIL"""
        # Current implementation may not validate embedding vectors

        invalid_embedding_cases = [
            {
                "embedding": [],            # Empty vector
                "error": "Embedding vector cannot be empty"
            },
            {
                "embedding": [1.0, 2.0, "not-a-number"],  # Mixed types
                "error": "Embedding vector must contain only numbers"
            },
            {
                "embedding": [float('inf'), float('-inf')],  # Infinite values
                "error": "Embedding vector cannot contain infinite values"
            },
            {
                "embedding": [float('nan'), float('nan')],  # NaN values
                "error": "Embedding vector cannot contain NaN values"
            },
            {
                "embedding": [1.0] * 100000,  # Extremely large vector
                "error": "Embedding vector too large"
            },
            {
                "embedding": [1.0] * 3 + ["string"],  # String in vector
                "error": "Embedding vector must contain only numeric values"
            },
        ]

        for invalid_case in invalid_embedding_cases:
            app_idea = AppIdea(
                title="Test App",
                app_concept="A test application",
                problem_statement="A test problem",
                target_audience="Test users",
                core_functions=["test function"]
            )

            market_metrics = MarketMetrics(
                market_demand=70.0,
                pain_intensity=75.0,
                monetization_potential=80.0,
                competition_level=65.0,
                technical_feasibility=85.0
            )

            with pytest.raises(ValueError, match=invalid_case["error"]):
                AnalysisResult(
                    submission_id="test123",
                    app_idea=app_idea,
                    market_metrics=market_metrics,
                    final_score=75.0,
                    confidence_score=80.0,
                    trust_level="HIGH",
                    embedding=invalid_case["embedding"]
                )

    def test_score_calculation_errors(self):
        """Test score calculation error handling - SHOULD FAIL"""
        # Current implementation may not validate score calculations

        score_error_cases = [
            {
                "app_idea": {
                    "title": "High Complexity App",
                    "app_concept": "Complex app requiring advanced technology",
                    "problem_statement": "Complex problem",
                    "target_audience": "Technical audience",
                    "core_functions": ["advanced_function_1", "advanced_function_2", "advanced_function_3"]
                },
                "market_metrics": {
                    "market_demand": 30.0,      # Low demand
                    "pain_intensity": 30.0,      # Low pain
                    "monetization_potential": 30.0,  # Low monetization
                    "competition_level": 80.0,     # High competition
                    "technical_feasibility": 20.0   # Low feasibility
                },
                "final_score": 90.0,        # High score - inconsistent
                "confidence_score": 80.0,
                "error": "Low metrics cannot result in high final score"
            },
            {
                "app_idea": {
                    "title": "Simple App",
                    "app_concept": "Simple app idea",
                    "problem_statement": "Simple problem",
                    "target_audience": "General audience",
                    "core_functions": ["simple_function"]
                },
                "market_metrics": {
                    "market_demand": 90.0,      # High demand
                    "pain_intensity": 90.0,      # High pain
                    "monetization_potential": 90.0,  # High monetization
                    "competition_level": 10.0,     # Low competition
                    "technical_feasibility": 90.0   # High feasibility
                },
                "final_score": 20.0,        # Low score - inconsistent
                "confidence_score": 80.0,
                "error": "High metrics cannot result in low final score"
            },
            {
                "app_idea": {
                    "title": "Test App",
                    "app_concept": "A test application",
                    "problem_statement": "A test problem",
                    "target_audience": "Test users",
                    "core_functions": ["test function"]
                },
                "market_metrics": {
                    "market_demand": 70.0,
                    "pain_intensity": 75.0,
                    "monetization_potential": 80.0,
                    "competition_level": 65.0,
                    "technical_feasibility": 85.0
                },
                "final_score": 75.0,
                "confidence_score": 20.0,    # Low confidence - inconsistent
                "error": "High score with low confidence is inconsistent"
            },
        ]

        for score_case in score_error_cases:
            app_idea = AppIdea(**score_case["app_idea"])
            market_metrics = MarketMetrics(**score_case["market_metrics"])

            with pytest.raises(ValueError, match=score_case["error"]):
                AnalysisResult(
                    submission_id="test123",
                    app_idea=app_idea,
                    market_metrics=market_metrics,
                    final_score=score_case["final_score"],
                    confidence_score=score_case["confidence_score"],
                    trust_level="HIGH"
                )


class TestOpportunityCreateErrorScenarios:
    """Test OpportunityCreate model error scenario handling - SHOULD FAIL"""

    def test_database_constraint_violation_scenarios(self):
        """Test database constraint violation scenarios - SHOULD FAIL"""
        # Current implementation may not handle database constraint violations

        constraint_violation_cases = [
            {
                "submission_id": "",          # Empty required field
                "reddit_title": "Test Title",
                "reddit_url": "https://reddit.com/test/test123",
                "subreddit": "test",
                "reddit_author": "testuser",
                "reddit_upvotes": 100,
                "reddit_comments_count": 25,
                "reddit_created_at": datetime.now(timezone.utc),
                "app_title": "Test App Title",
                "app_concept": "Test concept",
                "problem_statement": "Test problem",
                "target_audience": "Test audience",
                "core_functions": ["test function"],
                "error": "Required field cannot be empty"
            },
            {
                "submission_id": "a" * 11,    # Too long (Reddit limit is 10 chars)
                "reddit_title": "Test Title",
                "reddit_url": "https://reddit.com/test/test123",
                "subreddit": "test",
                "reddit_author": "testuser",
                "reddit_upvotes": 100,
                "reddit_comments_count": 25,
                "reddit_created_at": datetime.now(timezone.utc),
                "app_title": "Test App Title",
                "app_concept": "Test concept",
                "problem_statement": "Test problem",
                "target_audience": "Test audience",
                "core_functions": ["test function"],
                "error": "Submission ID exceeds maximum length"
            },
            {
                "submission_id": "test123",
                "reddit_title": "a" * 301,    # Too long (Reddit limit is 300 chars)
                "reddit_url": "https://reddit.com/test/test123",
                "subreddit": "test",
                "reddit_author": "testuser",
                "reddit_upvotes": 100,
                "reddit_comments_count": 25,
                "reddit_created_at": datetime.now(timezone.utc),
                "app_title": "Test App Title",
                "app_concept": "Test concept",
                "problem_statement": "Test problem",
                "target_audience": "Test audience",
                "core_functions": ["test function"],
                "error": "Reddit title exceeds maximum length"
            },
            {
                "submission_id": "test123",
                "reddit_title": "Test Title",
                "reddit_url": "a" * 501,    # Too long (URL limit is 500 chars)
                "subreddit": "test",
                "reddit_author": "testuser",
                "reddit_upvotes": 100,
                "reddit_comments_count": 25,
                "reddit_created_at": datetime.now(timezone.utc),
                "app_title": "Test App Title",
                "app_concept": "Test concept",
                "problem_statement": "Test problem",
                "target_audience": "Test audience",
                "core_functions": ["test function"],
                "error": "Reddit URL exceeds maximum length"
            },
        ]

        for constraint_case in constraint_violation_cases:
            with pytest.raises(ValueError, match=constraint_case["error"]):
                OpportunityCreate(
                    submission_id=constraint_case["submission_id"],
                    reddit_title=constraint_case["reddit_title"],
                    reddit_url=constraint_case["reddit_url"],
                    subreddit=constraint_case["subreddit"],
                    reddit_author=constraint_case["reddit_author"],
                    reddit_upvotes=constraint_case["reddit_upvotes"],
                    reddit_comments_count=constraint_case["reddit_comments_count"],
                    reddit_created_at=constraint_case["reddit_created_at"],
                    app_title=constraint_case["app_title"],
                    app_concept=constraint_case["app_concept"],
                    problem_statement=constraint_case["problem_statement"],
                    target_audience=constraint_case["target_audience"],
                    core_functions=constraint_case["core_functions"],
                    market_demand=70.0,
                    pain_intensity=75.0,
                    monetization_potential=80.0,
                    competition_level=65.0,
                    technical_feasibility=85.0,
                    final_score=75.0,
                    confidence_score=80.0,
                    trust_level="HIGH"
                )

    def test_foreign_key_error_scenarios(self):
        """Test foreign key error scenarios - SHOULD FAIL"""
        # Current implementation may not validate foreign key constraints

        foreign_key_error_cases = [
            {
                "submission_id": "invalid_id!",  # Invalid format
                "reddit_title": "Test Title",
                "reddit_url": "https://reddit.com/test/test123",
                "subreddit": "test",
                "reddit_author": "testuser",
                "reddit_upvotes": 100,
                "reddit_comments_count": 25,
                "reddit_created_at": datetime.now(timezone.utc),
                "app_title": "Test App Title",
                "app_concept": "Test concept",
                "problem_statement": "Test problem",
                "target_audience": "Test audience",
                "core_functions": ["test function"],
                "error": "Invalid submission ID format"
            },
            {
                "submission_id": "123",  # Numeric ID (Reddit IDs are alphanumeric)
                "reddit_title": "Test Title",
                "reddit_url": "https://reddit.com/test/test123",
                "subreddit": "test",
                "reddit_author": "testuser",
                "reddit_upvotes": 100,
                "reddit_comments_count": 25,
                "reddit_created_at": datetime.now(timezone.utc),
                "app_title": "Test App Title",
                "app_concept": "Test concept",
                "problem_statement": "Test problem",
                "target_audience": "Test audience",
                "core_functions": ["test function"],
                "error": "Submission ID must be alphanumeric"
            },
            {
                "submission_id": "test123",
                "reddit_title": "Test Title",
                "reddit_url": "https://reddit.com/test/test123",
                "subreddit": "nonexistent_subreddit!",  # Invalid subreddit format
                "reddit_author": "testuser",
                "reddit_upvotes": 100,
                "reddit_comments_count": 25,
                "reddit_created_at": datetime.now(timezone.utc),
                "app_title": "Test App Title",
                "app_concept": "Test concept",
                "problem_statement": "Test problem",
                "target_audience": "Test audience",
                "core_functions": ["test function"],
                "error": "Invalid subreddit format"
            },
        ]

        for fk_case in foreign_key_error_cases:
            with pytest.raises(ValueError, match=fk_case["error"]):
                OpportunityCreate(
                    submission_id=fk_case["submission_id"],
                    reddit_title=fk_case["reddit_title"],
                    reddit_url=fk_case["reddit_url"],
                    subreddit=fk_case["subreddit"],
                    reddit_author=fk_case["reddit_author"],
                    reddit_upvotes=fk_case["reddit_upvotes"],
                    reddit_comments_count=fk_case["reddit_comments_count"],
                    reddit_created_at=fk_case["reddit_created_at"],
                    app_title=fk_case["app_title"],
                    app_concept=fk_case["app_concept"],
                    problem_statement=fk_case["problem_statement"],
                    target_audience=fk_case["target_audience"],
                    core_functions=fk_case["core_functions"],
                    market_demand=70.0,
                    pain_intensity=75.0,
                    monetization_potential=80.0,
                    competition_level=65.0,
                    technical_feasibility=85.0,
                    final_score=75.0,
                    confidence_score=80.0,
                    trust_level="HIGH"
                )

    def test_data_type_conversion_errors(self):
        """Test data type conversion error scenarios - SHOULD FAIL"""
        # Current implementation may not handle data type conversion errors

        type_conversion_error_cases = [
            {
                "submission_id": "test123",
                "reddit_title": 456,  # Should be string, not int
                "reddit_url": "https://reddit.com/test/test123",
                "subreddit": "test",
                "reddit_author": "testuser",
                "reddit_upvotes": "100",  # String instead of int
                "reddit_comments_count": "25",  # String instead of int
                "reddit_created_at": "not-a-datetime",  # Invalid datetime
                "app_title": "Test App Title",
                "app_concept": "Test concept",
                "problem_statement": "Test problem",
                "target_audience": "Test audience",
                "core_functions": ["test function"],
                "error": "Invalid data type for field"
            },
            {
                "submission_id": "test123",
                "reddit_title": "Test Title",
                "reddit_url": "https://reddit.com/test/test123",
                "subreddit": "test",
                "reddit_author": "testuser",
                "reddit_upvotes": -100,  # Negative upvotes
                "reddit_comments_count": 25,
                "reddit_created_at": datetime.now(timezone.utc),
                "app_title": "Test App Title",
                "app_concept": "Test concept",
                "problem_statement": "Test problem",
                "target_audience": "Test audience",
                "core_functions": ["test function"],
                "error": "Negative values not allowed for upvotes"
            },
            {
                "submission_id": "test123",
                "reddit_title": "Test Title",
                "reddit_url": "https://reddit.com/test/test123",
                "subreddit": "test",
                "reddit_author": "testuser",
                "reddit_upvotes": 100,
                "reddit_comments_count": -25,  # Negative comments count
                "reddit_created_at": datetime.now(timezone.utc),
                "app_title": "Test App Title",
                "app_concept": "Test concept",
                "problem_statement": "Test problem",
                "target_audience": "Test audience",
                "core_functions": ["test function"],
                "error": "Negative comments count not allowed"
            },
        ]

        for type_case in type_conversion_error_cases:
            with pytest.raises((TypeError, ValueError), match=type_case["error"]):
                OpportunityCreate(
                    submission_id=type_case["submission_id"],
                    reddit_title=type_case["reddit_title"],
                    reddit_url=type_case["reddit_url"],
                    subreddit=type_case["subreddit"],
                    reddit_author=type_case["reddit_author"],
                    reddit_upvotes=type_case["reddit_upvotes"],
                    reddit_comments_count=type_case["reddit_comments_count"],
                    reddit_created_at=type_case["reddit_created_at"],
                    app_title=type_case["app_title"],
                    app_concept=type_case["app_concept"],
                    problem_statement=type_case["problem_statement"],
                    target_audience=type_case["target_audience"],
                    core_functions=type_case["core_functions"],
                    market_demand=70.0,
                    pain_intensity=75.0,
                    monetization_potential=80.0,
                    competition_level=65.0,
                    technical_feasibility=85.0,
                    final_score=75.0,
                    confidence_score=80.0,
                    trust_level="HIGH"
                )

    def test_json_serialization_errors(self):
        """Test JSON serialization error scenarios - SHOULD FAIL"""
        # Current implementation may not handle JSON serialization errors

        json_serialization_error_cases = [
            {
                "submission_id": "test123",
                "reddit_title": "Test Title",
                "reddit_url": "https://reddit.com/test/test123",
                "subreddit": "test",
                "reddit_author": "testuser",
                "reddit_upvotes": 100,
                "reddit_comments_count": 25,
                "reddit_created_at": datetime.now(timezone.utc),
                "app_title": "Test App Title",
                "app_concept": "Test concept",
                "problem_statement": "Test problem",
                "target_audience": "Test audience",
                "core_functions": {"not": "a list"},  # Should be a list, not dict
                "error": "core_functions must be a list of strings"
            },
            {
                "submission_id": "test123",
                "reddit_title": "Test Title",
                "reddit_url": "https://reddit.com/test/test123",
                "subreddit": "test",
                "reddit_author": "testuser",
                "reddit_upvotes": 100,
                "reddit_comments_count": 25,
                "reddit_created_at": datetime.now(timezone.utc),
                "app_title": "Test App Title",
                "app_concept": "Test concept",
                "problem_statement": "Test problem",
                "target_audience": "Test audience",
                "core_functions": [123, 456],  # List of numbers, not strings
                "error": "core_functions must contain only strings"
            },
            {
                "submission_id": "test123",
                "reddit_title": "Test Title",
                "reddit_url": "https://reddit.com/test/test123",
                "subreddit": "test",
                "reddit_author": "testuser",
                "reddit_upvotes": 100,
                "reddit_comments_count": 25,
                "reddit_created_at": datetime.now(timezone.utc),
                "app_title": "Test App Title",
                "app_concept": "Test concept",
                "problem_statement": "Test problem",
                "target_audience": "Test audience",
                "core_functions": ["", ""],  # Empty strings
                "error": "core_functions cannot contain empty strings"
            },
        ]

        for json_case in json_serialization_error_cases:
            with pytest.raises(ValueError, match=json_case["error"]):
                OpportunityCreate(
                    submission_id=json_case["submission_id"],
                    reddit_title=json_case["reddit_title"],
                    reddit_url=json_case["reddit_url"],
                    subreddit=json_case["subreddit"],
                    reddit_author=json_case["reddit_author"],
                    reddit_upvotes=json_case["reddit_upvotes"],
                    reddit_comments_count=json_case["reddit_comments_count"],
                    reddit_created_at=json_case["reddit_created_at"],
                    app_title=json_case["app_title"],
                    app_concept=json_case["app_concept"],
                    problem_statement=json_case["problem_statement"],
                    target_audience=json_case["target_audience"],
                    core_functions=json_case["core_functions"],
                    market_demand=70.0,
                    pain_intensity=75.0,
                    monetization_potential=80.0,
                    competition_level=65.0,
                    technical_feasibility=85.0,
                    final_score=75.0,
                    confidence_score=80.0,
                    trust_level="HIGH"
                )

    def test_database_mapping_consistency_errors(self):
        """Test database mapping consistency error scenarios - SHOULD FAIL"""
        # Current implementation may not ensure database model consistency

        # Create a valid OpportunityCreate instance
        valid_create = OpportunityCreate(
            submission_id="test123",
            reddit_title="Test Title",
            reddit_url="https://reddit.com/test/test123",
            subreddit="test",
            reddit_author="testuser",
            reddit_upvotes=100,
            reddit_comments_count=25,
            reddit_created_at=datetime.now(timezone.utc),
            app_title="Test App Title",
            app_concept="Test concept",
            problem_statement="Test problem",
            target_audience="Test audience",
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

        # Test successful database model conversion
        try:
            db_model = valid_create.to_db_model()
            assert db_model is not None
            assert db_model.submission_id == valid_create.submission_id
            assert db_model.reddit_title == valid_create.reddit_title
            assert db_model.app_title == valid_create.app_title
        except Exception as e:
            pytest.fail(f"Database model conversion failed: {e}")

        # Test data truncation scenarios
        truncation_error_cases = [
            {
                "reddit_title": "a" * 301,  # Exceeds 300 char limit
                "error": "Reddit title exceeds database limit"
            },
            {
                "reddit_url": "a" * 501,  # Exceeds 500 char limit
                "error": "Reddit URL exceeds database limit"
            },
            {
                "app_title": "a" * 201,  # Exceeds 200 char limit
                "error": "App title exceeds database limit"
            },
        ]

        for truncation_case in truncation_error_cases:
            modified_create = OpportunityCreate(
                submission_id="test123",
                reddit_title=truncation_case["reddit_title"] if "reddit_title" in truncation_case else "Valid Title",
                reddit_url=truncation_case["reddit_url"] if "reddit_url" in truncation_case else "https://reddit.com/test/test123",
                subreddit="test",
                reddit_author="testuser",
                reddit_upvotes=100,
                reddit_comments_count=25,
                reddit_created_at=datetime.now(timezone.utc),
                app_title=truncation_case["app_title"] if "app_title" in truncation_case else "Valid App Title",
                app_concept="Test concept",
                problem_statement="Test problem",
                target_audience="Test audience",
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

            with pytest.raises(ValueError, match=truncation_case["error"]):
                # This should detect truncation and fail
                db_model = modified_create.to_db_model()
                # Check if any field was truncated
                for field_name, field_value in modified_create.__dict__.items():
                    if isinstance(field_value, str) and len(field_value) > 300:
                        assert len(getattr(db_model, field_name)) <= 300, f"Field {field_name} was not properly truncated"