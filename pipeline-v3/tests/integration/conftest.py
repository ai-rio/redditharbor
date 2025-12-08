"""
Integration test configuration for pipeline v3
"""

import asyncio
import json
import os
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest

from tests.helpers.test_data_factory import (
    AgentResponseFactory,
    RedditSubmissionFactory,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_supabase_integration():
    """Mock Supabase client for integration tests"""
    with patch('scripts.core.batch_opportunity_scoring.supabase') as mock:
        # Setup common mock patterns
        mock.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(data=[])
        mock.rpc.return_value.execute.return_value = Mock(data=[{'success': True}])
        yield mock


@pytest.fixture
def mock_opportunity_agent():
    """Mock opportunity analyzer agent"""
    with patch('scripts.core.opp_agent.OpportunityAnalyzerAgent') as mock_class:
        agent = Mock()
        agent.analyze_opportunity.return_value = {
            'final_score': 75.0,
            'monetization_potential': 80.0,
            'problem_alignment': 85.0,
            'ai_enhanced': True,
            'analysis_timestamp': '2024-01-01T00:00:00Z'
        }
        mock_class.return_value = agent
        yield agent


@pytest.fixture
def mock_analyzer():
    """Mock Agno analyzer"""
    with patch('core.agents.monetization.agno_analyzer.MonetizationAgnoAnalyzer') as mock_class:
        analyzer = Mock()
        analyzer.analyze.return_value = Mock(
            willingness_to_pay_score=75.0,
            market_segment_score=80.0,
            price_sensitivity_score=60.0,
            revenue_potential_score=78.5,
            customer_segment="B2B",
            mentioned_price_points=["$500/month"],
            existing_payment_behavior="$200/month",
            urgency_level="High",
            sentiment_toward_payment="Positive",
            payment_friction_indicators=["none_detected"],
            llm_monetization_score=82.5,
            confidence=0.85,
            reasoning="Test analysis result",
            subreddit_multiplier=1.3
        )
        analyzer.analyze_stream = AsyncMock()
        mock_class.return_value = analyzer
        yield analyzer


@pytest.fixture
def test_batch_data():
    """Test batch data for integration testing"""
    return RedditSubmissionFactory.create_batch_submissions(6, {
        'high_wtp_b2b': 2,
        'low_wtp_b2c': 2,
        'mixed_segment': 2
    })


@pytest.fixture
def test_database_state():
    """Test database state for integration testing"""
    return {
        'business_concepts': [
            {
                'id': 1,
                'concept_name': 'CRM Solutions',
                'has_agno_analysis': True,
                'last_analyzed': '2024-01-01T00:00:00Z',
                'wtp_score_avg': 75.0,
                'analysis_count': 10
            },
            {
                'id': 2,
                'concept_name': 'Project Management',
                'has_agno_analysis': False,
                'last_analyzed': None,
                'wtp_score_avg': None,
                'analysis_count': 0
            }
        ],
        'opportunities_unified': [
            {
                'submission_id': 'sub_001',
                'business_concept_id': 1,
                'title': 'CRM needed for growing team',
                'text': 'We need a CRM as we scale from 10 to 50 employees',
                'subreddit': 'startups',
                'ai_enhanced_score': 75.0,
                'trust_score': 75,
                'num_comments': 15
            },
            {
                'submission_id': 'sub_002',
                'business_concept_id': 2,
                'title': 'Project management tool search',
                'text': 'Looking for tools to manage remote team projects',
                'subreddit': 'remoteWork',
                'ai_enhanced_score': 0.0,  # Not processed yet
                'trust_score': 60,
                'num_comments': 8
            }
        ]
    }


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing"""
    env_vars = {
        'MONETIZATION_LLM_ENABLED': 'true',
        'MONETIZATION_LLM_THRESHOLD': '50.0',
        'OPENROUTER_API_KEY': 'test_api_key',
        'AGENTOPS_API_KEY': 'test_agentops_key',
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test_supabase_key'
    }

    with patch.dict('os.environ', env_vars):
        yield


@pytest.fixture
def async_test_context():
    """Async test context for async test functions"""
    return {
        'loop': asyncio.get_event_loop(),
        'results': [],
        'errors': []
    }


@pytest.fixture
def integration_test_data():
    """Comprehensive integration test data"""
    return {
        'valid_submissions': RedditSubmissionFactory.create_batch_submissions(10),
        'agent_responses': {
            'wtp': AgentResponseFactory.create_wtp_variations(),
            'segment': AgentResponseFactory.create_segment_variations(),
            'price': AgentResponseFactory.create_price_variations(),
            'behavior': AgentResponseFactory.create_behavior_variations()
        },
        'consensus_scenarios': AgentResponseFactory.create_consensus_scenarios()
    }


@pytest.fixture
def mock_supabase_responses():
    """Mock Supabase responses for various scenarios"""
    def create_mock_response(data):
        mock = Mock()
        mock.data = data
        return mock

    return {
        'no_duplicates': create_mock_response([]),
        'duplicate_no_analysis': create_mock_response([{'business_concept_id': 2}]),
        'duplicate_with_analysis': create_mock_response([{'business_concept_id': 1}]),
        'business_concept_no_analysis': create_mock_response([{
            'id': 2,
            'has_agno_analysis': False
        }]),
        'business_concept_with_analysis': create_mock_response([{
            'id': 1,
            'has_agno_analysis': True
        }]),
        'primary_opportunity': create_mock_response([{
            'submission_id': 'primary_001',
            'llm_monetization_score': 85.5,
            'willingness_to_pay_score': 75.0,
            'customer_segment': 'B2B',
            'confidence': 0.85,
            'reasoning': 'Primary analysis result'
        }]),
        'no_primary': create_mock_response([]),
        'rpc_success': create_mock_response([{'update_agno_analysis_tracking': True}]),
        'rpc_error': create_mock_response([])
    }


@pytest.fixture
def test_scenario_config():
    """Test scenario configuration"""
    return {
        'batch_sizes': [1, 5, 10, 50],
        'concurrent_levels': [1, 5, 10],
        'error_scenarios': [
            'database_error',
            'agent_error',
            'timeout',
            'malformed_response'
        ],
        'performance_thresholds': {
            'min_throughput': 5.0,  # submissions per second
            'max_latency': 10.0,  # seconds
            'max_memory_mb': 100  # MB
        }
    }


@pytest.fixture
def integration_test_helpers():
    """Helper functions for integration tests"""
    class IntegrationTestHelpers:
        @staticmethod
        def setup_database_mocks(mock_supabase, scenario):
            """Setup database mocks for specific scenario"""
            if scenario == 'unique_submissions':
                mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = [
                    Mock(data=[]),  # No duplicates found
                    Mock(data=[{'has_agno_analysis': False}])  # Business concept without analysis
                ]
            elif scenario == 'duplicate_with_existing':
                mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = [
                    Mock(data=[{'business_concept_id': 1}]),  # Duplicate found
                    Mock(data=[{'has_agno_analysis': True}])  # Has existing analysis
                ]
            elif scenario == 'duplicate_needs_analysis':
                mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = [
                    Mock(data=[{'business_concept_id': 2}]),  # Duplicate found
                    Mock(data=[{'has_agno_analysis': False}])  # No existing analysis
                ]
            elif scenario == 'database_error':
                mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("Database connection failed")

        @staticmethod
        def verify_batch_results(results, expected_count, min_score=0):
            """Verify batch processing results"""
            assert len(results) == expected_count
            for result in results:
                assert result['processed'] is True
                assert result['submission_id'] is not None
                if 'analysis_result' in result:
                    assert result['analysis_result'] is not None
                    if 'final_score' in result['analysis_result']:
                        assert result['analysis_result']['final_score'] >= min_score

        @staticmethod
        def verify_agentops_calls(mock_agentops, expected_events):
            """Verify AgentOps events were recorded"""
            if hasattr(mock_agentops, 'events'):
                assert len(mock_agentops.events) >= len(expected_events)
                event_names = [e['event_name'] for e in mock_agentops.events]
                for expected_event in expected_events:
                    assert expected_event in event_names

        @staticmethod
        def create_performance_metrics():
            """Create performance metrics collector"""
            return {
                'start_time': None,
                'end_time': None,
                'processing_times': [],
                'memory_usage': [],
                'throughput': 0.0
            }

        @staticmethod
        def calculate_performance_metrics(metrics):
            """Calculate performance metrics"""
            if metrics['start_time'] and metrics['end_time']:
                duration = metrics['end_time'] - metrics['start_time']
                total_submissions = sum(len(batch) for batch in metrics['processing_times'])
                metrics['throughput'] = total_submissions / duration if duration > 0 else 0
                return metrics
            return None

    return IntegrationTestHelpers()
