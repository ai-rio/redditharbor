"""
Integration Tests for Trust Validation System

Tests the new trust validation system integration with existing pipelines:
- DLT Trust Pipeline compatibility
- Batch Opportunity Scoring integration
- Existing database operations
- End-to-end workflow validation

Run with: python -m pytest tests/test_trust_integration.py -v
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock, call
from typing import Dict, Any

from core.trust import (
    TrustValidationService,
    TrustRepositoryFactory,
    TrustValidationRequest,
    TrustIndicators,
    TrustLevel,
    TrustBadge,
    create_trust_service
)
from core.trust.repository import MultiTableTrustRepository

# Mock existing data structures that would come from pipelines
SAMPLE_SUBMISSION_DATA = {
    'submission_id': 't3_abc123',
    'title': 'Need help with task management apps',
    'text': 'I\'ve tried multiple task management apps but none work well for my workflow. Looking for recommendations.',
    'subreddit': 'productivity',
    'upvotes': 156,
    'comments_count': 42,
    'created_utc': 1700000000.0,
    'permalink': '/r/productivity/comments/abc123/need_help_with_task_management/'
}

SAMPLE_AI_ANALYSIS = {
    'problem_description': 'Users struggle with finding effective task management solutions that fit their personal workflow',
    'app_concept': 'AI-powered adaptive task manager that learns user preferences and optimizes task organization',
    'core_functions': ['Smart task scheduling', 'Priority optimization', 'Progress analytics'],
    'final_score': 78.5,
    'market_demand': 82.0,
    'pain_intensity': 75.0,
    'monetization_potential': 70.0,
    'market_gap': 65.0,
    'technical_feasibility': 80.0,
    'simplicity_score': 85.0
}

SAMPLE_TRUST_DATA = {
    'trust_score': 85.0,
    'trust_badge': 'GOLD',
    'trust_level': 'high',
    'activity_score': 75.0,
    'engagement_level': 'HIGH',
    'trend_velocity': 65.0,
    'problem_validity': 'VALID',
    'discussion_quality': 'GOOD',
    'ai_confidence_level': 'HIGH',
    'confidence_score': 80.0,
    'validation_timestamp': '2025-11-18T10:00:00Z',
    'validation_method': 'comprehensive_trust_layer'
}


class MockSupabaseClient:
    """Mock Supabase client for integration testing."""

    def __init__(self):
        self.tables = {}
        self.query_history = []

    def table(self, table_name: str):
        """Get table mock."""
        if table_name not in self.tables:
            self.tables[table_name] = MockTable(table_name, self.query_history)
        return self.tables[table_name]


class MockTable:
    """Mock table for Supabase operations."""

    def __init__(self, table_name: str, query_history: list):
        self.table_name = table_name
        self.query_history = query_history
        self.data = {}

    def select(self, *columns):
        """Mock select operation."""
        self.query_history.append({
            'table': self.table_name,
            'operation': 'select',
            'columns': columns
        })
        return self

    def eq(self, column: str, value):
        """Mock equality filter."""
        self.query_history.append({
            'table': self.table_name,
            'operation': 'filter',
            'column': column,
            'value': value
        })
        return self

    def in_(self, column: str, values: list):
        """Mock IN filter."""
        self.query_history.append({
            'table': self.table_name,
            'operation': 'in_filter',
            'column': column,
            'values': values
        })
        return self

    def execute(self):
        """Mock execute operation."""
        # Return mock data based on query
        if self.table_name == 'app_opportunities':
            # Mock existing trust indicators
            if 'submission_id' in [q.get('value', '') for q in self.query_history if q.get('operation') == 'filter']:
                submission_id = next(q['value'] for q in self.query_history if q.get('operation') == 'filter' and q.get('column') == 'submission_id')
                return MockExecuteResult([{
                    'submission_id': submission_id,
                    **SAMPLE_TRUST_DATA
                }])
        return MockExecuteResult([])

    def upsert(self, data: dict, on_conflict: str = None):
        """Mock upsert operation."""
        self.query_history.append({
            'table': self.table_name,
            'operation': 'upsert',
            'data': data,
            'on_conflict': on_conflict
        })
        return MockExecuteResult([data])

    def update(self, data: dict):
        """Mock update operation."""
        self.query_history.append({
            'table': self.table_name,
            'operation': 'update',
            'data': data
        })
        return MockExecuteResult([data])

    def delete(self):
        """Mock delete operation."""
        self.query_history.append({
            'table': self.table_name,
            'operation': 'delete'
        })
        return MockExecuteResult([])


class MockExecuteResult:
    """Mock execute result."""

    def __init__(self, data: list):
        self.data = data


class TestDLTTrustPipelineIntegration:
    """Test integration with DLT Trust Pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = MockSupabaseClient()
        self.repository = TrustRepositoryFactory.create_repository(self.mock_client)
        self.service = TrustValidationService(self.repository)

    @patch('core.trust.validation.calculate_activity_score')
    @patch('core.trust.validation.praw.Reddit')
    def test_dlt_trust_pipeline_workflow(self, mock_reddit, mock_calculate_activity):
        """Test complete DLT trust pipeline workflow."""
        # Mock Reddit API
        mock_calculate_activity.return_value = 40.0

        # Simulate DLT pipeline data processing
        submission_data = SAMPLE_SUBMISSION_DATA.copy()
        ai_analysis = SAMPLE_AI_ANALYSIS.copy()

        # Step 1: Trust validation (what would happen in dlt_trust_pipeline.py)
        trust_request = TrustValidationRequest(
            submission_id=submission_data['submission_id'],
            subreddit=submission_data['subreddit'],
            upvotes=submission_data['upvotes'],
            comments_count=submission_data['comments_count'],
            created_utc=submission_data['created_utc'],
            text=submission_data['text'],
            title=submission_data['title'],
            ai_analysis=ai_analysis
        )

        trust_result = self.service.validate_opportunity_trust(trust_request)

        assert trust_result.success is True
        indicators = trust_result.indicators

        # Step 2: Prepare data for DLT (what would happen before DLT load)
        dlt_profile = {
            'submission_id': submission_data['submission_id'],
            'title': submission_data['title'],
            'problem_description': ai_analysis['problem_description'],
            'app_concept': ai_analysis['app_concept'],
            'core_functions': ai_analysis['core_functions'],
            'opportunity_score': ai_analysis['final_score'],

            # Trust indicators from new system
            'trust_score': indicators.overall_trust_score,
            'trust_badge': indicators.trust_badges[0] if indicators.trust_badges else 'BASIC',
            'activity_score': indicators.subreddit_activity_score,
            'trust_level': indicators.trust_level.value,
            'engagement_level': indicators.engagement_level,
            'trend_velocity': indicators.trend_velocity,
            'problem_validity': indicators.problem_validity,
            'discussion_quality': indicators.discussion_quality,
            'ai_confidence_level': indicators.ai_confidence_level,
            'confidence_score': indicators.confidence_score,
            'validation_timestamp': indicators.validation_timestamp,
            'validation_method': indicators.validation_method,

            # Original Reddit data
            'subreddit': submission_data['subreddit'],
            'reddit_score': submission_data['upvotes'],
            'num_comments': submission_data['comments_count']
        }

        # Step 3: Save to database (what DLT would do)
        save_success = self.service.save_trust_indicators(
            submission_data['submission_id'],
            indicators
        )
        assert save_success is True

        # Verify data was prepared correctly for DLT
        assert 'trust_score' in dlt_profile
        assert 'trust_badge' in dlt_profile
        assert 'activity_score' in dlt_profile
        assert dlt_profile['trust_score'] >= 0.0
        assert dlt_profile['activity_score'] >= 0.0

    def test_existing_trust_data_compatibility(self):
        """Test compatibility with existing trust data in database."""
        # Simulate existing trust data in database
        existing_data = SAMPLE_TRUST_DATA.copy()
        existing_data['submission_id'] = SAMPLE_SUBMISSION_DATA['submission_id']

        # Mock repository to return existing data
        self.repository.data = {
            SAMPLE_SUBMISSION_DATA['submission_id']: TrustIndicators.from_dict(existing_data)
        }

        # Test retrieving existing trust indicators
        retrieved_indicators = self.service.get_trust_indicators(
            SAMPLE_SUBMISSION_DATA['submission_id']
        )

        assert retrieved_indicators is not None
        assert retrieved_indicators.trust_score == 85.0
        assert retrieved_indicators.trust_level == TrustLevel.HIGH

        # Test that existing data can be updated
        updates = {'trust_score': 90.0, 'confidence_score': 85.0}
        update_success = self.repository.update_trust_indicators(
            SAMPLE_SUBMISSION_DATA['submission_id'],
            updates
        )
        assert update_success is True


class TestBatchOpportunityScoringIntegration:
    """Test integration with Batch Opportunity Scoring."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = MockSupabaseClient()
        self.repository = TrustRepositoryFactory.create_repository(self.mock_client)
        self.service = TrustValidationService(self.repository)

    @patch('core.trust.validation.calculate_activity_score')
    @patch('core.trust.validation.praw.Reddit')
    def test_batch_scoring_with_trust_data(self, mock_reddit, mock_calculate_activity):
        """Test batch opportunity scoring with trust data integration."""
        # Mock Reddit API
        mock_calculate_activity.return_value = 40.0

        # Simulate batch of submissions from database
        submissions_batch = []
        ai_analyses = []

        for i in range(5):
            submission_data = SAMPLE_SUBMISSION_DATA.copy()
            submission_data['submission_id'] = f't3_abc{i:03d}'
            submission_data['upvotes'] = 100 + i * 20
            submission_data['comments_count'] = 20 + i * 5

            ai_analysis = SAMPLE_AI_ANALYSIS.copy()
            ai_analysis['final_score'] = 70.0 + i * 3

            submissions_batch.append(submission_data)
            ai_analyses.append(ai_analysis)

        # Create validation requests
        trust_requests = []
        for i, (submission, ai_analysis) in enumerate(zip(submissions_batch, ai_analyses)):
            request = TrustValidationRequest(
                submission_id=submission['submission_id'],
                subreddit=submission['subreddit'],
                upvotes=submission['upvotes'],
                comments_count=submission['comments_count'],
                created_utc=submission['created_utc'],
                text=submission['text'],
                title=submission['title'],
                ai_analysis=ai_analysis
            )
            trust_requests.append(request)

        # Perform batch trust validation
        batch_results = self.service.validate_batch_opportunities_trust(trust_requests)

        assert len(batch_results) == 5
        assert all(result.success for result in batch_results)

        # Test preparing data for workflow_results table
        workflow_data = []
        for i, (submission, ai_analysis, trust_result) in enumerate(
            zip(submissions_batch, ai_analyses, batch_results)
        ):
            indicators = trust_result.indicators

            workflow_record = {
                'opportunity_id': f"opp_{submission['submission_id']}",
                'submission_id': submission['submission_id'],
                'app_name': ai_analysis['app_concept'][:50],  # Truncate for DB
                'function_count': len(ai_analysis['core_functions']),
                'function_list': ai_analysis['core_functions'],
                'original_score': ai_analysis['final_score'],
                'final_score': ai_analysis['final_score'],

                # Trust data from new system
                'trust_score': indicators.overall_trust_score,
                'trust_badge': indicators.trust_badges[0] if indicators.trust_badges else 'BASIC',
                'activity_score': indicators.subreddit_activity_score,

                # Dimension scores from AI analysis
                'market_demand': ai_analysis.get('market_demand', 0),
                'pain_intensity': ai_analysis.get('pain_intensity', 0),
                'monetization_potential': ai_analysis.get('monetization_potential', 0),
                'market_gap': ai_analysis.get('market_gap', 0),
                'technical_feasibility': ai_analysis.get('technical_feasibility', 0),
                'simplicity_score': ai_analysis.get('simplicity_score', 0),

                # Metadata
                'status': 'scored',
                'processed_at': indicators.validation_timestamp
            }

            workflow_data.append(workflow_record)

        # Verify workflow data integrity
        for record in workflow_data:
            assert 'trust_score' in record
            assert 'trust_badge' in record
            assert 'activity_score' in record
            assert record['trust_score'] >= 0.0
            assert record['function_count'] == 3  # From sample data

    def test_trust_data_preservation_during_ai_update(self):
        """Test that trust data is preserved during AI enrichment."""
        # Simulate existing trust indicators
        existing_trust = TrustIndicators(
            trust_score=82.0,
            trust_level=TrustLevel.HIGH,
            trust_badges=[TrustBadge.SILVER, "Good Discussion"],
            activity_score=75.0,
            validation_timestamp="2025-11-17T15:00:00Z",
            validation_method="existing_system"
        )

        submission_id = SAMPLE_SUBMISSION_DATA['submission_id']
        self.repository.save_trust_indicators(submission_id, existing_trust)

        # Simulate AI scoring pipeline update (what batch_opportunity_scoring.py does)
        ai_update_data = {
            'problem_description': SAMPLE_AI_ANALYSIS['problem_description'],
            'app_concept': SAMPLE_AI_ANALYSIS['app_concept'],
            'core_functions': SAMPLE_AI_ANALYSIS['core_functions'],
            'opportunity_score': SAMPLE_AI_ANALYSIS['final_score'],
            'status': 'ai_enriched'
        }

        # Update with new AI data while preserving trust data
        updated_trust = TrustIndicators.from_dict({
            **existing_trust.to_dict(),
            **ai_update_data
        })

        update_success = self.repository.save_trust_indicators(submission_id, updated_trust)
        assert update_success is True

        # Verify trust data was preserved
        retrieved = self.service.get_trust_indicators(submission_id)
        assert retrieved is not None
        assert retrieved.trust_score == 82.0  # Preserved
        assert retrieved.trust_level == TrustLevel.HIGH  # Preserved
        assert retrieved.validation_timestamp == "2025-11-17T15:00:00Z"  # Preserved

        # Verify AI data was added
        # (Note: In real implementation, AI data would be in separate columns)


class TestMultiTableRepositoryIntegration:
    """Test multi-table repository integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = MockSupabaseClient()
        self.repository = MultiTableTrustRepository(self.mock_client)
        self.service = TrustValidationService(self.repository)

    def test_trust_data_from_multiple_sources(self):
        """Test retrieving trust data from multiple tables."""
        submission_id = SAMPLE_SUBMISSION_DATA['submission_id']

        # Mock different tables having different data
        # app_opportunities table has full trust data
        app_opportunities_data = {
            'submission_id': submission_id,
            **SAMPLE_TRUST_DATA
        }

        # submissions table has basic trust data
        submissions_data = {
            'submission_id': submission_id,
            'trust_score': 80.0,
            'trust_badge': 'SILVER'
        }

        # Configure mock to return appropriate data
        self.mock_client.tables['app_opportunities'].data = [app_opportunities_data]
        self.mock_client.tables['submissions'].data = [submissions_data]

        # Test that repository prioritizes app_opportunities table
        indicators = self.repository.get_trust_indicators(submission_id)

        assert indicators is not None
        assert indicators.trust_score == 85.0  # From app_opportunities (more complete)
        assert indicators.trust_level == TrustLevel.HIGH

        # Test existence check across tables
        exists = self.repository.exists_trust_indicators(submission_id)
        assert exists is True

    def test_batch_operations_with_multi_table_support(self):
        """Test batch operations with multi-table repository."""
        submission_ids = [f't3_abc{i:03d}' for i in range(3)]

        # Mock batch retrieval
        batch_data = []
        for i, submission_id in enumerate(submission_ids):
            data = SAMPLE_TRUST_DATA.copy()
            data['submission_id'] = submission_id
            data['trust_score'] = 80.0 + i * 5
            batch_data.append(data)

        self.mock_client.tables['app_opportunities'].data = batch_data

        # Perform batch retrieval
        results = self.repository.get_batch_trust_indicators(submission_ids)

        assert len(results) == 3
        for i, submission_id in enumerate(submission_ids):
            assert submission_id in results
            assert results[submission_id].trust_score == 80.0 + i * 5


class TestEndToEndWorkflow:
    """Test end-to-end workflow integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = MockSupabaseClient()
        self.repository = TrustRepositoryFactory.create_repository(self.mock_client)
        self.service = TrustValidationService(self.repository)

    @patch('core.trust.validation.calculate_activity_score')
    @patch('core.trust.validation.praw.Reddit')
    def test_complete_reddit_to_trusted_opportunity_workflow(self, mock_reddit, mock_calculate_activity):
        """Test complete workflow from Reddit data to trusted opportunity."""
        # Mock Reddit API
        mock_calculate_activity.return_value = 45.0

        # Step 1: Reddit data collection (simulated)
        reddit_post = SAMPLE_SUBMISSION_DATA.copy()

        # Step 2: AI opportunity analysis (simulated)
        ai_analysis = SAMPLE_AI_ANALYSIS.copy()

        # Step 3: Trust validation
        trust_request = TrustValidationRequest(
            submission_id=reddit_post['submission_id'],
            subreddit=reddit_post['subreddit'],
            upvotes=reddit_post['upvotes'],
            comments_count=reddit_post['comments_count'],
            created_utc=reddit_post['created_utc'],
            text=reddit_post['text'],
            title=reddit_post['title'],
            ai_analysis=ai_analysis
        )

        trust_result = self.service.validate_opportunity_trust(trust_request)
        assert trust_result.success is True

        # Step 4: Prepare for database storage (what pipelines do)
        app_opportunity_data = {
            'submission_id': reddit_post['submission_id'],
            'title': reddit_post['title'],
            'problem_description': ai_analysis['problem_description'],
            'app_concept': ai_analysis['app_concept'],
            'core_functions': ai_analysis['core_functions'],
            'opportunity_score': ai_analysis['final_score'],

            # Trust indicators (from new system)
            **trust_result.indicators.to_dict()
        }

        workflow_results_data = {
            'opportunity_id': f"opp_{reddit_post['submission_id']}",
            'submission_id': reddit_post['submission_id'],
            'app_name': ai_analysis['app_concept'][:50],
            'function_count': len(ai_analysis['core_functions']),
            'function_list': ai_analysis['core_functions'],

            # Scores
            'original_score': ai_analysis['final_score'],
            'final_score': ai_analysis['final_score'],

            # Trust data (key fields from new system)
            'trust_score': trust_result.indicators.overall_trust_score,
            'trust_badge': trust_result.indicators.trust_badges[0] if trust_result.indicators.trust_badges else 'BASIC',
            'activity_score': trust_result.indicators.subreddit_activity_score,

            # AI analysis dimensions
            'market_demand': ai_analysis.get('market_demand', 0),
            'pain_intensity': ai_analysis.get('pain_intensity', 0),
            'monetization_potential': ai_analysis.get('monetization_potential', 0),
            'market_gap': ai_analysis.get('market_gap', 0),
            'technical_feasibility': ai_analysis.get('technical_feasibility', 0),
            'simplicity_score': ai_analysis.get('simplicity_score', 0),

            'status': 'validated',
            'processed_at': trust_result.indicators.validation_timestamp
        }

        # Step 5: Validate data integrity
        assert app_opportunity_data['trust_score'] >= 0.0
        assert app_opportunity_data['activity_score'] >= 0.0
        assert workflow_results_data['trust_score'] == app_opportunity_data['trust_score']
        assert workflow_results_data['function_count'] == 3  # From sample data

        # Step 6: Save trust indicators (database operation simulation)
        save_success = self.service.save_trust_indicators(
            reddit_post['submission_id'],
            trust_result.indicators
        )
        assert save_success is True

        # Step 7: Verify retrieval
        retrieved_indicators = self.service.get_trust_indicators(reddit_post['submission_id'])
        assert retrieved_indicators is not None
        assert retrieved_indicators.trust_score == app_opportunity_data['trust_score']

    def test_system_performance_and_monitoring(self):
        """Test system performance and monitoring capabilities."""
        # Perform multiple validations
        requests = []
        for i in range(10):
            request = TrustValidationRequest(
                submission_id=f'test_{i}',
                subreddit='test',
                upvotes=50 + i * 5,
                comments_count=10 + i * 2,
                created_utc=time.time() - i * 3600,
                text=f'Test text {i}',
                ai_analysis={
                    'problem_description': f'Test problem {i}',
                    'app_concept': f'Test concept {i}',
                    'final_score': 60.0 + i * 2
                }
            )
            requests.append(request)

        # Batch validate
        start_time = time.time()
        results = self.service.validate_batch_opportunities_trust(requests)
        end_time = time.time()

        # Performance assertions
        processing_time = end_time - start_time
        assert processing_time < 5.0  # Should complete within 5 seconds
        assert len(results) == 10
        assert all(result.success for result in results)

        # Check service statistics
        stats = self.service.get_service_stats()
        assert stats['total_validations'] == 10
        assert stats['successful_validations'] == 10
        assert stats['success_rate'] == 1.0
        assert stats['average_processing_time_ms'] > 0

        # Check validation history
        history = self.service.get_validation_history()
        assert len(history) == 10

        # Verify audit trail
        for i, result in enumerate(results):
            assert result.source_submission_id == f'test_{i}'
            assert result.processing_time_ms > 0
            assert result.validation_version == '1.0'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])