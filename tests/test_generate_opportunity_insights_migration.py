#!/usr/bin/env python3
"""
Unit tests for generate_opportunity_insights_openrouter.py DLT migration

Tests cover:
- OpenRouter API integration (mocked)
- Insight structure validation
- DLT pipeline integration (mocked)
- Data loading to opportunity_analysis table
- Deduplication (run twice, verify no duplicate insights)
- Error handling (API failures, batch load failures)
- Statistics reporting
- Batch optimization
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import functions from script
from scripts.generate_opportunity_insights_openrouter import (
    RateLimiter,
    generate_insight_with_openrouter,
    load_insights_to_supabase_via_dlt,
    validate_insight,
)


class TestOpenRouterIntegration:
    """Test OpenRouter API integration"""

    def test_rate_limiter_delay(self):
        """Test rate limiter enforces delay between requests"""
        import time

        rate_limiter = RateLimiter(min_delay=0.1, max_delay=0.2)

        start = time.time()
        rate_limiter.wait()
        first_call = time.time()

        rate_limiter.wait()
        second_call = time.time()

        # Second call should be delayed
        assert (second_call - first_call) >= 0.1

    @patch('scripts.generate_opportunity_insights_openrouter.requests.post')
    def test_generate_insight_with_valid_response(self, mock_post):
        """Test insight generation with valid OpenRouter response"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': '''```json
{
  "problem_identified": "Users struggle to track late payments",
  "problem_evidence": "Reddit users mention spreadsheet nightmares",
  "app_concept": "Late payment reminder tracker for freelancers",
  "core_functions": ["Track unpaid invoices", "Send automated reminders"],
  "reddit_demand_evidence": "r/freelance users discuss late payment struggles",
  "simplicity_score": 2
}
```'''
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        rate_limiter = RateLimiter(min_delay=0.01, max_delay=0.02)

        insight = generate_insight_with_openrouter(
            title="I forget to follow up on late payments",
            content="I use spreadsheets and it's a nightmare",
            scores={'market_demand': 60, 'pain_intensity': 70, 'monetization_potential': 50, 'simplicity_score': 60},
            rate_limiter=rate_limiter,
            top_comments=""
        )

        assert insight is not None
        assert 'app_concept' in insight
        assert 'core_functions' in insight
        assert isinstance(insight['core_functions'], list)

    @patch('scripts.generate_opportunity_insights_openrouter.requests.post')
    def test_generate_insight_with_api_error(self, mock_post):
        """Test insight generation handles API errors"""
        # Mock API error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        rate_limiter = RateLimiter(min_delay=0.01, max_delay=0.02)

        insight = generate_insight_with_openrouter(
            title="Test title",
            content="Test content",
            scores={'market_demand': 60, 'pain_intensity': 70, 'monetization_potential': 50, 'simplicity_score': 60},
            rate_limiter=rate_limiter,
            top_comments=""
        )

        # Should return None on error
        assert insight is None

    @patch('scripts.generate_opportunity_insights_openrouter.requests.post')
    def test_generate_insight_with_null_response(self, mock_post):
        """Test insight generation handles null (rejection) responses"""
        # Mock null response (AI rejection)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': 'null'
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        rate_limiter = RateLimiter(min_delay=0.01, max_delay=0.02)

        insight = generate_insight_with_openrouter(
            title="Generic post",
            content="Not a problem",
            scores={'market_demand': 60, 'pain_intensity': 70, 'monetization_potential': 50, 'simplicity_score': 60},
            rate_limiter=rate_limiter,
            top_comments=""
        )

        # Should return None for rejected opportunities
        assert insight is None


class TestInsightValidation:
    """Test insight structure validation"""

    def test_validate_valid_insight(self):
        """Test validation accepts valid insight"""
        insight = {
            'app_concept': 'Late payment reminder tracker for freelancers',
            'core_functions': ['Track unpaid invoices', 'Send automated reminders'],
            'growth_justification': 'Reddit users in r/freelance frequently discuss late payment struggles and mention willingness to pay $10-30/month for solutions'
        }

        is_valid, reason = validate_insight(insight, monetization_score=60)

        assert is_valid is True
        assert reason == "Valid"

    def test_validate_missing_app_concept(self):
        """Test validation rejects insight with missing app_concept"""
        insight = {
            'core_functions': ['Function 1', 'Function 2'],
            'growth_justification': 'Reddit evidence shows demand'
        }

        is_valid, reason = validate_insight(insight, monetization_score=60)

        assert is_valid is False
        assert 'app_concept' in reason

    def test_validate_too_many_functions(self):
        """Test validation rejects insight with too many functions"""
        insight = {
            'app_concept': 'Complex productivity platform with many features',
            'core_functions': ['Function 1', 'Function 2', 'Function 3', 'Function 4'],
            'growth_justification': 'Reddit users discuss productivity in r/productivity'
        }

        is_valid, reason = validate_insight(insight, monetization_score=60)

        assert is_valid is False
        assert 'exceed max of 3' in reason

    def test_validate_low_monetization_score(self):
        """Test validation rejects insight with low monetization score"""
        insight = {
            'app_concept': 'Simple task tracker for personal use',
            'core_functions': ['Track tasks'],
            'growth_justification': 'Reddit users mention task tracking needs'
        }

        is_valid, reason = validate_insight(insight, monetization_score=3)

        assert is_valid is False
        assert 'Monetization score too low' in reason

    def test_validate_missing_reddit_evidence(self):
        """Test validation rejects insight without Reddit evidence"""
        insight = {
            'app_concept': 'Generic productivity tool for everyone',
            'core_functions': ['Track productivity', 'Generate reports'],
            'growth_justification': 'General market analysis shows demand for productivity tools'
        }

        is_valid, reason = validate_insight(insight, monetization_score=60)

        assert is_valid is False
        assert 'Reddit evidence' in reason


class TestDLTPipelineIntegration:
    """Test DLT pipeline integration"""

    @patch('scripts.generate_opportunity_insights_openrouter.create_dlt_pipeline')
    def test_load_insights_success(self, mock_create_pipeline):
        """Test successful insight loading via DLT"""
        # Mock DLT pipeline
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_load_info.started_at = "2025-11-07T12:00:00"
        mock_pipeline.run.return_value = mock_load_info
        mock_create_pipeline.return_value = mock_pipeline

        insights = [
            {
                'opportunity_id': 'opp_test_123',
                'submission_id': 'test_123',
                'title': 'Test opportunity',
                'app_concept': 'Test app concept',
                'core_functions': ['Function 1'],
                'growth_justification': 'Reddit evidence',
                'market_demand': 60.0,
                'pain_intensity': 70.0,
                'monetization_potential': 50.0,
                'simplicity_score': 70.0,
                'final_score': 62.5,
            }
        ]

        success = load_insights_to_supabase_via_dlt(insights)

        assert success is True
        mock_pipeline.run.assert_called_once_with(
            insights,
            table_name="opportunity_analysis",
            write_disposition="merge",
            primary_key="opportunity_id"
        )

    @patch('scripts.generate_opportunity_insights_openrouter.create_dlt_pipeline')
    def test_load_insights_error_handling(self, mock_create_pipeline):
        """Test error handling in DLT loading"""
        # Mock DLT pipeline error
        mock_pipeline = MagicMock()
        mock_pipeline.run.side_effect = Exception("Database connection failed")
        mock_create_pipeline.return_value = mock_pipeline

        insights = [
            {
                'opportunity_id': 'opp_test_123',
                'submission_id': 'test_123',
                'title': 'Test opportunity',
                'app_concept': 'Test app concept',
                'core_functions': ['Function 1'],
                'growth_justification': 'Reddit evidence',
                'market_demand': 60.0,
                'pain_intensity': 70.0,
                'monetization_potential': 50.0,
                'simplicity_score': 70.0,
                'final_score': 62.5,
            }
        ]

        success = load_insights_to_supabase_via_dlt(insights)

        assert success is False

    def test_load_insights_empty_batch(self):
        """Test loading with empty insight batch"""
        insights = []

        success = load_insights_to_supabase_via_dlt(insights)

        assert success is False


class TestDeduplication:
    """Test deduplication via merge disposition"""

    @patch('scripts.generate_opportunity_insights_openrouter.create_dlt_pipeline')
    def test_duplicate_insights_merged(self, mock_create_pipeline):
        """Test that duplicate insights are merged, not duplicated"""
        # Mock DLT pipeline
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_load_info.started_at = "2025-11-07T12:00:00"
        mock_pipeline.run.return_value = mock_load_info
        mock_create_pipeline.return_value = mock_pipeline

        # Same opportunity_id (should merge, not duplicate)
        insights_batch_1 = [
            {
                'opportunity_id': 'opp_test_123',
                'submission_id': 'test_123',
                'title': 'Test opportunity',
                'app_concept': 'Test app concept v1',
                'core_functions': ['Function 1'],
                'growth_justification': 'Reddit evidence',
                'market_demand': 60.0,
                'pain_intensity': 70.0,
                'monetization_potential': 50.0,
                'simplicity_score': 70.0,
                'final_score': 62.5,
            }
        ]

        insights_batch_2 = [
            {
                'opportunity_id': 'opp_test_123',  # Same ID
                'submission_id': 'test_123',
                'title': 'Test opportunity',
                'app_concept': 'Test app concept v2 (updated)',
                'core_functions': ['Function 1', 'Function 2'],
                'growth_justification': 'Updated Reddit evidence',
                'market_demand': 65.0,
                'pain_intensity': 75.0,
                'monetization_potential': 55.0,
                'simplicity_score': 70.0,
                'final_score': 65.0,
            }
        ]

        # Load first batch
        success1 = load_insights_to_supabase_via_dlt(insights_batch_1)
        assert success1 is True

        # Load second batch (should merge, not create duplicate)
        success2 = load_insights_to_supabase_via_dlt(insights_batch_2)
        assert success2 is True

        # Verify merge disposition was used
        calls = mock_pipeline.run.call_args_list
        assert len(calls) == 2
        for call in calls:
            assert call[1]['write_disposition'] == 'merge'
            assert call[1]['primary_key'] == 'opportunity_id'


class TestBatchOptimization:
    """Test batch loading optimization"""

    @patch('scripts.generate_opportunity_insights_openrouter.create_dlt_pipeline')
    def test_batch_loading_accumulates_insights(self, mock_create_pipeline):
        """Test that insights are accumulated and loaded in a single batch"""
        # Mock DLT pipeline
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_load_info.started_at = "2025-11-07T12:00:00"
        mock_pipeline.run.return_value = mock_load_info
        mock_create_pipeline.return_value = mock_pipeline

        # Batch of 10 insights
        insights = [
            {
                'opportunity_id': f'opp_test_{i}',
                'submission_id': f'test_{i}',
                'title': f'Test opportunity {i}',
                'app_concept': f'Test app concept {i}',
                'core_functions': ['Function 1'],
                'growth_justification': 'Reddit evidence',
                'market_demand': 60.0,
                'pain_intensity': 70.0,
                'monetization_potential': 50.0,
                'simplicity_score': 70.0,
                'final_score': 62.5,
            }
            for i in range(10)
        ]

        success = load_insights_to_supabase_via_dlt(insights)

        assert success is True
        # Should be called ONCE with ALL insights (batch optimization)
        mock_pipeline.run.assert_called_once()
        call_args = mock_pipeline.run.call_args[0]
        assert len(call_args[0]) == 10  # All 10 insights in single batch


class TestStatisticsReporting:
    """Test statistics reporting"""

    @patch('scripts.generate_opportunity_insights_openrouter.create_dlt_pipeline')
    def test_statistics_captured(self, mock_create_pipeline, capsys):
        """Test that statistics are captured and reported"""
        # Mock DLT pipeline
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_load_info.started_at = "2025-11-07T12:00:00"
        mock_pipeline.run.return_value = mock_load_info
        mock_create_pipeline.return_value = mock_pipeline

        insights = [
            {
                'opportunity_id': 'opp_test_123',
                'submission_id': 'test_123',
                'title': 'Test opportunity',
                'app_concept': 'Test app concept',
                'core_functions': ['Function 1'],
                'growth_justification': 'Reddit evidence',
                'market_demand': 60.0,
                'pain_intensity': 70.0,
                'monetization_potential': 50.0,
                'simplicity_score': 70.0,
                'final_score': 62.5,
            }
        ]

        success = load_insights_to_supabase_via_dlt(insights)

        # Capture output
        captured = capsys.readouterr()

        assert success is True
        assert "LOADING INSIGHTS TO SUPABASE VIA DLT PIPELINE" in captured.out
        assert "Insights to load: 1" in captured.out
        assert "Successfully loaded 1 AI insights" in captured.out
        assert "Table: opportunity_analysis" in captured.out
        assert "Write mode: merge" in captured.out
        assert "Primary key: opportunity_id" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
