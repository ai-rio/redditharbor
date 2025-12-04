"""
Edge case tests for AgnoOpportunityAnalyzer
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

from tests.helpers.test_data_factory import RedditSubmissionFactory
from tests.helpers.mock_agno_agents import MockAgnoTeam, MockWTPAgent
from tests.helpers.assertion_helpers import AgnoAnalysisAssertions
from tests.performance.conftest import PerformanceTestHelpers


class TestAgnoAnalyzerEdgeCases:
    """Edge case tests for Agno analyzer"""

    def test_empty_text_handling(self, mock_agno_team_performance):
        """Test handling of empty/None text submissions"""
        edge_cases = [
            {'submission_id': 'empty_001', 'text': '', 'subreddit': 'startups'},
            {'submission_id': 'none_001', 'text': None, 'subreddit': 'startups'},
            {'submission_id': 'whitespace_001', 'text': '   \n\t  ', 'subreddit': 'startups'}
        ]

        for case in edge_cases:
            with pytest.raises(Exception):  # Should raise exception for invalid input
                result = mock_agno_team_performance.analyze_opportunity(
                    text=case['text'],
                    subreddit=case['subreddit']
                )

    def test_extremely_long_text_handling(self, mock_agno_team_performance):
        """Test handling of extremely long submissions"""
        # Create submission with very long text
        long_text = ' '.join(['This is a test sentence.'] * 10000)  # ~700KB of text

        submission = {
            'submission_id': 'long_001',
            'text': long_text,
            'subreddit': 'startups'
        }

        # Should handle long text without crashing
        result = mock_agno_team_performance.analyze_opportunity(
            text=submission['text'],
            subreddit=submission['subreddit']
        )

        # Result should still be valid
        AgnoAnalysisAssertions.assert_analysis_completeness(result)
        assert result.reasoning is not None

    def test_unicode_special_characters(self, mock_agno_team_performance):
        """Test handling of unicode and special characters"""
        unicode_cases = [
            {
                'submission_id': 'unicode_001',
                'text': '需要CRM系统🚀 as we scale from 10 to 50 employees 📈 💰',
                'subreddit': 'startups'
            },
            {
                'submission_id': 'emoji_001',
                'text': 'CRM needed!!! $$$ &*&^%$#@! <> " 😊 👨‍💼 💼',
                'subreddit': 'startups'
            },
            {
                'submission_id': 'nonlatin_001',
                'text': 'CRM system needed for 國際 expansion and ประเทศ development',
                'subreddit': 'startups'
            }
        ]

        for case in unicode_cases:
            result = mock_agno_team_performance.analyze_opportunity(
                text=case['text'],
                subreddit=case['subreddit']
            )

            AgnoAnalysisAssertions.assert_analysis_completeness(result)
            # Should handle unicode gracefully without character encoding issues
            assert isinstance(result.reasoning, str)

    def test_invalid_subreddit_names(self, mock_agno_team_performance):
        """Test handling of invalid subreddit names"""
        invalid_subreddits = [
            None,
            '',
            'not_a_subreddit',
            '123invalid',
            'subreddit_with_underscores',
            'ALL_CAPS_SUBREDDIT',
            'subreddit-with-dashes'
        ]

        text = "Need CRM for growing team"

        for subreddit in invalid_subreddits:
            # Should handle invalid subreddit gracefully
            result = mock_agno_team_performance.analyze_opportunity(
                text=text,
                subreddit=subreddit or 'startups'  # Use default if None
            )

            AgnoAnalysisAssertions.assert_analysis_completeness(result)
            # Subreddit multiplier should default to reasonable value
            assert result.subreddit_multiplier >= 0.5

    def test_malformed_agent_responses(self, mock_agno_team_performance):
        """Test handling of malformed agent responses"""
        # Mock the team to return malformed responses
        with patch.object(mock_agno_team_performance, '_call_agent') as mock_call:
            # Return malformed JSON responses
            mock_call.return_value = MalformedResponseMock()

            text = "Need CRM for growing team"

            # Should handle malformed responses gracefully
            result = mock_agno_team_performance.analyze_opportunity(
                text=text,
                subreddit='startups'
            )

            # Should return fallback analysis
            AgnoAnalysisAssertions.assert_analysis_completeness(result)
            assert result.willingness_to_pay_score > 0

    def test_timeout_scenarios(self, mock_agno_team_performance):
        """Test timeout handling"""
        with patch('time.sleep') as mock_sleep:
            # Mock timeout
            mock_sleep.side_effect = TimeoutError("Request timed out")

            text = "Need CRM for growing team"

            # Should handle timeouts gracefully
            with pytest.raises(TimeoutError):
                mock_agno_team_performance.analyze_opportunity(
                    text=text,
                    subreddit='startups'
                )

    def test_memory_exhaustion_scenarios(self, mock_agno_team_performance):
        """Test memory exhaustion scenarios"""
        # Create very large batch that might cause memory issues
        large_batch = RedditSubmissionFactory.create_batch_submissions(1000)

        # Should handle large batches without crashing
        results = mock_agno_team_performance.analyze_opportunity_batch(
            submissions=large_batch,
            batch_size=100
        )

        # Should process most submissions successfully
        success_rate = len(results) / len(large_batch)
        assert success_rate > 0.8, f"Success rate {success_rate} too low for large batch"

        # Validate results
        for result in results:
            AgnoAnalysisAssertions.assert_analysis_completeness(result)

    def test_concurrent_access_scenarios(self, mock_agno_team_performance):
        """Test concurrent access scenarios"""
        import threading
        import time

        results = []
        errors = []
        lock = threading.Lock()

        def worker(submission):
            try:
                result = mock_agno_team_performance.analyze_opportunity(
                    text=submission['text'],
                    subreddit=submission['subreddit']
                )
                with lock:
                    results.append(result)
            except Exception as e:
                with lock:
                    errors.append(str(e))

        # Create multiple worker threads
        submissions = RedditSubmissionFactory.create_batch_submissions(20)
        threads = []

        for submission in submissions:
            thread = threading.Thread(target=worker, args=(submission,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout

        # Should handle concurrent access without issues
        assert len(results) > 0, "No results from concurrent processing"
        assert len(errors) < len(submissions) * 0.1, f"Too many errors: {len(errors)}"

        # Validate results
        for result in results:
            AgnoAnalysisAssertions.assert_analysis_completeness(result)

    def test_agent_failure_scenarios(self, mock_agno_team_performance):
        """Test individual agent failure scenarios"""
        with patch.object(mock_agno_team_performance, '_call_agent') as mock_call:
            # Mock different agent failures
            def mock_agent_failure(agent_name, *args, **kwargs):
                if agent_name == 'wtp':
                    raise Exception("WTP agent failed")
                elif agent_name == 'segment':
                    return {
                        'customer_segment': 'B2B',
                        'confidence': 0.7,
                        'reasoning': 'Segment analysis succeeded'
                    }
                elif agent_name == 'price':
                    return {
                        'mentioned_price_points': ['$500/month'],
                        'price_sensitivity_score': 60,
                        'reasoning': 'Price analysis succeeded'
                    }
                elif agent_name == 'behavior':
                    return {
                        'payment_friction_indicators': ['none_detected'],
                        'existing_payment_behavior': '$200/month',
                        'reasoning': 'Behavior analysis succeeded'
                    }

            mock_call.side_effect = lambda agent_name, *args, **kwargs: mock_agent_failure(agent_name, *args, **kwargs)

            text = "Need CRM for growing team"

            # Should handle individual agent failures gracefully
            result = mock_agno_team_performance.analyze_opportunity(
                text=text,
                subreddit='startups'
            )

            # Should still return reasonable analysis
            AgnoAnalysisAssertions.assert_analysis_completeness(result)
            assert result.willingness_to_pay_score > 0  # Should have fallback

    def test_rate_limit_scenarios(self, mock_agno_team_performance):
        """Test rate limiting scenarios"""
        call_count = 0

        with patch('time.sleep') as mock_sleep:
            def mock_rate_limited_call(*args, **kwargs):
                nonlocal call_count
                call_count += 1

                # Simulate rate limiting every 5 calls
                if call_count % 5 == 0:
                    mock_sleep.return_value = None
                    raise Exception("Rate limit exceeded")

                return Mock(
                    willingness_to_pay_score=75,
                    customer_segment='B2B',
                    confidence=0.8,
                    reasoning='Analysis successful'
                )

            with patch.object(mock_agno_team_performance, '_call_agent') as mock_call:
                mock_call.side_effect = mock_rate_limited_call

                submissions = RedditSubmissionFactory.create_batch_submissions(15)

                # Should handle rate limiting
                results = []
                errors = []

                for submission in submissions:
                    try:
                        result = mock_agno_team_performance.analyze_opportunity(
                            text=submission['text'],
                            subreddit=submission['subreddit']
                        )
                        results.append(result)
                    except Exception as e:
                        errors.append(str(e))

                # Should handle rate limiting without complete failure
                assert len(results) > 0, "No successful results after rate limiting"
                success_rate = len(results) / len(submissions)
                assert success_rate > 0.6, f"Success rate {success_rate} too low after rate limiting"

    def test_database_connection_scenarios(self, mock_supabase_integration):
        """Test database connection failure scenarios"""
        with patch('scripts.core.batch_opportunity_scoring.supabase') as mock_supabase:
            # Simulate database connection failure
            mock_supabase.side_effect = Exception("Database connection failed")

            # Should handle database failures gracefully
            from scripts.core.batch_opportunity_scoring import should_run_agno_analysis

            submission = RedditSubmissionFactory.create_single_submission('high_wtp_b2b')

            with pytest.raises(Exception) as exc_info:
                should_run, concept_id = should_run_agno_analysis(
                    submission, mock_supabase
                )

            assert "Database connection failed" in str(exc_info.value)

    def test_api_key_scenarios(self, mock_agno_team_performance):
        """Test API key scenarios"""
        # Test with None API key
        analyzer_without_key = MockAgnoTeam(
            enable_cost_tracking=False,
            enable_agentops=False,
            mock_responses=True
        )

        result = analyzer_without_key.analyze_opportunity(
            text="Need CRM",
            subreddit="startups"
        )

        AgnoAnalysisAssertions.assert_analysis_completeness(result)

        # Test with invalid API key format
        analyzer_invalid_key = MockAgnoTeam(
            api_key="invalid-key",
            enable_cost_tracking=False,
            enable_agentops=False,
            mock_responses=True
        )

        result = analyzer_invalid_key.analyze_opportunity(
            text="Need CRM",
            subreddit="startups"
        )

        AgnoAnalysisAssertions.assert_analysis_completeness(result)

    def test_network_scenarios(self, mock_agno_team_performance):
        """Test network-related edge cases"""
        with patch('requests.request') as mock_request:
            # Simulate various network errors
            def mock_network_error(*args, **kwargs):
                import random
                error_type = random.choice([
                    ConnectionError("Connection reset"),
                    TimeoutError("Request timeout"),
                    Exception("Network unreachable")
                ])
                raise error_type

            mock_request.side_effect = mock_network_error

            # Should handle network errors gracefully
            with pytest.raises(Exception):
                mock_agno_team_performance.analyze_opportunity(
                    text="Need CRM",
                    subreddit="startups"
                )

    def test_data_validation_scenarios(self, mock_agno_team_performance):
        """Test input data validation scenarios"""
        # Test with invalid data types
        invalid_inputs = [
            {'text': 123, 'subreddit': 'startups'},  # text as number
            {'text': 'Need CRM', 'subreddit': 123},  # subreddit as number
            {'text': [], 'subreddit': 'startups'},  # text as list
            {'text': {}, 'subreddit': 'startups'},  # text as dict
            {'text': 'Need CRM', 'subreddit': []},   # subreddit as list
        ]

        for invalid_input in invalid_inputs:
            with pytest.raises(Exception):
                mock_agno_team_performance.analyze_opportunity(
                    text=invalid_input['text'],
                    subreddit=invalid_input['subreddit']
                )

    def test_consensus_calculation_edge_cases(self, mock_agno_team_performance):
        """Test consensus calculation edge cases"""
        # Mock team to return extreme variations
        with patch.object(mock_agno_team_performance, '_call_agent') as mock_call:
            def mock_extreme_responses(*args, **kwargs):
                # Return highly varied responses to test consensus
                import random
                return {
                    'willingness_to_pay_score': random.choice([10, 90]),
                    'customer_segment': random.choice(['B2B', 'B2C', 'Mixed']),
                    'confidence': random.choice([0.1, 0.9]),
                    'reasoning': 'Mock analysis'
                }

            mock_call.side_effect = mock_extreme_responses

            # Multiple submissions to test consistency
            submissions = RedditSubmissionFactory.create_batch_submissions(5)

            results = []
            for submission in submissions:
                result = mock_agno_team_performance.analyze_opportunity(
                    text=submission['text'],
                    subreddit=submission['subreddit']
                )
                results.append(result)

            # Should handle extreme variations gracefully
            for result in results:
                AgnoAnalysisAssertions.assert_analysis_completeness(result)
                # Scores should still be in valid range despite variations
                assert 0 <= result.willingness_to_pay_score <= 100

    def test_cost_tracking_edge_cases(self, mock_agno_team_performance):
        """Test cost tracking edge cases"""
        # Enable cost tracking
        analyzer = MockAgnoTeam(
            enable_cost_tracking=True,
            enable_agentops=False,
            mock_responses=True
        )

        # Process many submissions to test cost accumulation
        submissions = RedditSubmissionFactory.create_batch_submissions(50)

        results = []
        for submission in submissions:
            result = analyzer.analyze_opportunity(
                text=submission['text'],
                subreddit=submission['subreddit']
            )
            results.append(result)

        # Should track costs without issues
        assert hasattr(analyzer, 'total_cost')
        assert analyzer.total_cost >= 0

        # Should still return valid results
        for result in results:
            AgnoAnalysisAssertions.assert_analysis_completeness(result)


class MalformedResponseMock:
    """Mock class to simulate malformed agent responses"""
    def __init__(self):
        pass

    def __str__(self):
        return "malformed response"

    def json(self):
        # This will raise JSONDecodeError
        return "invalid json"