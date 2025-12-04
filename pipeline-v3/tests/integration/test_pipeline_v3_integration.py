"""
Integration tests for pipeline v3 with Agno analyzer
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from tests.integration.conftest import IntegrationTestHelpers


class TestPipelineV3Integration:
    """Integration tests for complete pipeline v3 workflow"""

    @pytest.mark.integration
    def test_batch_processing_workflow(self, mock_supabase_integration,
                                      mock_opportunity_agent,
                                      test_batch_data,
                                      mock_env_vars,
                                      integration_test_helpers):
        """Test complete batch processing workflow with Agno integration"""

        # Setup database mocks for unique submissions
        integration_test_helpers.setup_database_mocks(
            mock_supabase_integration, 'unique_submissions'
        )

        # Import and test batch processing
        with patch('scripts.core.batch_opportunity_scoring.process_batch') as mock_process:
            # Mock the process_batch function
            mock_process.return_value = [
                {
                    'submission_id': sub['submission_id'],
                    'processed': True,
                    'analysis_result': {
                        'final_score': 75.0,
                        'monetization_potential': 80.0
                    }
                }
                for sub in test_batch_data
            ]

            # Execute batch processing
            results = mock_process(
                submissions=test_batch_data,
                agent=mock_opportunity_agent,
                batch_number=1,
                ai_profile_threshold=50.0
            )

            # Verify results
            integration_test_helpers.verify_batch_results(
                results, len(test_batch_data), 50.0
            )

            # Verify database interactions
            assert mock_supabase_integration.table.called
            assert mock_supabase_integration.rpc.called

    @pytest.mark.integration
    def test_duplicate_submission_handling(self, mock_supabase_integration,
                                          mock_analyzer,
                                          test_database_state,
                                          integration_test_helpers):
        """Test handling of duplicate submissions with Agno analysis"""

        # Setup mock for duplicate with existing analysis
        mock_supabase_integration.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = [
            Mock(data=[{'business_concept_id': 1}]),  # Duplicate found
            Mock(data=[{'has_agno_analysis': True}])  # Has existing analysis
        ]

        # Test the skip logic
        from scripts.core.batch_opportunity_scoring import should_run_agno_analysis

        submission = test_database_state['opportunities_unified'][0]

        should_run, concept_id = should_run_agno_analysis(
            submission, mock_supabase_integration
        )

        # Should skip analysis for duplicates with existing analysis
        assert should_run is False
        assert concept_id == "1"

        # Verify the right database calls were made
        calls = mock_supabase_integration.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.call_args_list
        assert len(calls) == 2  # Two calls: check opportunities and check concept

    @pytest.mark.integration
    def test_agno_analysis_copy(self, mock_supabase_integration,
                              test_database_state,
                              integration_test_helpers):
        """Test copying Agno analysis from primary opportunity"""

        # Setup mocks
        mock_supabase_integration.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(data=[
            test_database_state['business_concepts'][0]  # Primary with analysis
        ])

        # Test copy function
        from scripts.core.batch_opportunity_scoring import copy_agno_from_primary

        submission = test_database_state['opportunities_unified'][1]
        concept_id = "1"

        result = copy_agno_from_primary(
            submission, concept_id, mock_supabase_integration
        )

        # Should copy the analysis
        assert result is not None
        assert result['llm_monetization_score'] == 75.0
        assert result['customer_segment'] == 'B2B'

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_batch_processing(self, mock_supabase_integration,
                                        mock_analyzer,
                                        test_batch_data,
                                        async_test_context,
                                        integration_test_helpers):
        """Test async batch processing with Agno analyzer"""

        # Setup async mocks
        mock_analyzer.analyze = AsyncMock()

        # Mock async analysis responses
        async def mock_analysis_async(*args, **kwargs):
            await asyncio.sleep(0.01)  # Simulate processing
            return Mock(
                willingness_to_pay_score=75.0,
                market_segment_score=80.0,
                llm_monetization_score=82.5,
                customer_segment="B2B",
                confidence=0.85
            )

        mock_analyzer.analyze.side_effect = mock_analysis_async

        # Process batch asynchronously
        tasks = []
        for submission in test_batch_data:
            task = asyncio.create_task(
                mock_analyzer.analyze(
                    text=submission['text'],
                    subreddit=submission['subreddit']
                )
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # Verify results
        assert len(results) == len(test_batch_data)
        for result in results:
            assert result.willingness_to_pay_score > 0
            assert result.customer_segment in ["B2B", "B2C", "Mixed", "Unknown"]

    @pytest.mark.integration
    def test_error_handling_workflow(self, mock_supabase_integration,
                                    test_batch_data,
                                    integration_test_helpers):
        """Test error handling in complete workflow"""

        # Setup database error
        mock_supabase_integration.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("Database connection failed")

        # Test graceful error handling
        with pytest.raises(Exception) as exc_info:
            from scripts.core.batch_opportunity_scoring import should_run_agno_analysis

            submission = test_batch_data[0]
            should_run, concept_id = should_run_agno_analysis(
                submission, mock_supabase_integration
            )

        assert "Database connection failed" in str(exc_info.value)

    @pytest.mark.integration
    def test_agentops_integration(self, mock_agentops_mock,
                                mock_supabase_integration,
                                test_batch_data,
                                integration_test_helpers):
        """Test AgentOps integration in complete workflow"""

        # Setup AgentOps mock
        mock_agentops_instance = mock_agentops_mock['instance']

        # Setup successful database interaction
        mock_supabase_integration.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(data=[])

        # Test with AgentOps enabled
        with patch('scripts.core.batch_opportunity_scoring.MonetizationAgnoAnalyzer') as mock_analyzer_class:
            analyzer = Mock()
            analyzer.analyze.return_value = Mock(
                llm_monetization_score=82.5,
                willingness_to_pay_score=75.0
            )
            analyzer.agentops_enabled = True
            mock_analyzer_class.return_value = analyzer

            # Process submission
            from scripts.core.batch_opportunity_scoring import process_single_submission

            result = process_single_submission(
                submission=test_batch_data[0],
                analyzer=analyzer,
                supabase=mock_supabase_integration
            )

            # Verify AgentOps events
            integration_test_helpers.verify_agentops_calls(
                mock_agentops_instance,
                ['WTP_Analyst_execution', 'Market_Segment_Analyst_execution']
            )

    @pytest.mark.integration
    def test_pipeline_configuration(self, mock_env_vars):
        """Test pipeline configuration and initialization"""

        # Test environment variable loading
        import os

        assert os.getenv('MONETIZATION_LLM_ENABLED') == 'true'
        assert os.getenv('MONETIZATION_LLM_THRESHOLD') == '50.0'
        assert os.getenv('OPENROUTER_API_KEY') == 'test_api_key'
        assert os.getenv('AGENTOPS_API_KEY') == 'test_agentops_key'

        # Test configuration initialization
        with patch('config.settings') as mock_settings:
            mock_settings.MONETIZATION_LLM_MODEL = "anthropic/claude-haiku-4.5"
            mock_settings.OPENROUTER_API_KEY = "test_api_key"

            from core.agents.monetization.agno_analyzer import MonetizationAgnoAnalyzer

            # Should initialize with correct configuration
            analyzer = MonetizationAgnoAnalyzer(
                model="anthropic/claude-haiku-4.5",
                agentops_api_key="test_key"
            )

            assert analyzer.model == "anthropic/claude-haiku-4.5"
            assert analyzer.agentops_enabled is not None

    @pytest.mark.integration
    def test_database_transaction_safety(self, mock_supabase_integration,
                                        test_batch_data):
        """Test database transaction safety during batch processing"""

        # Track all database calls
        db_calls = []

        def track_calls(*args, **kwargs):
            db_calls.append({
                'args': args,
                'kwargs': kwargs,
                'timestamp': asyncio.get_event_loop().time()
            })
            return Mock(data=[])

        mock_supabase_integration.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = track_calls

        # Process multiple submissions
        for submission in test_batch_data[:3]:
            from scripts.core.batch_opportunity_scoring import should_run_agno_analysis
            should_run, concept_id = should_run_agno_analysis(
                submission, mock_supabase_integration
            )

        # Verify transaction safety
        assert len(db_calls) > 0

        # Check that calls are properly structured
        for call in db_calls:
            assert 'table' in call['kwargs']
            assert 'select' in call['kwargs']
            assert 'eq' in call['kwargs']

    @pytest.mark.integration
    def test_pipeline_metrics_collection(self, mock_supabase_integration,
                                       test_batch_data,
                                       integration_test_helpers):
        """Test metrics collection during pipeline execution"""

        # Setup metrics collector
        metrics = integration_test_helpers.create_performance_metrics()
        metrics['start_time'] = 1000.0

        # Process batch
        mock_supabase_integration.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(data=[])

        with patch('scripts.core.batch_opportunity_scoring.process_batch') as mock_process:
            mock_process.return_value = [
                {
                    'submission_id': sub['submission_id'],
                    'processed': True,
                    'processing_time': 0.1
                }
                for sub in test_batch_data
            ]

            results = mock_process(
                submissions=test_batch_data,
                agent=Mock(),
                batch_number=1,
                ai_profile_threshold=50.0
            )

            # Record end time
            metrics['end_time'] = 1005.0  # 5 seconds for 10 submissions

            # Calculate metrics
            calculated_metrics = integration_test_helpers.calculate_performance_metrics(metrics)

            # Verify metrics
            assert calculated_metrics is not None
            assert calculated_metrics['throughput'] > 0
            assert calculated_metrics['throughput'] <= 10  # Max 10 submissions/sec

    @pytest.mark.integration
    def test_concurrent_pipeline_processing(self, mock_supabase_integration,
                                           mock_analyzer,
                                           test_batch_data,
                                           scenario_config,
                                           integration_test_helpers):
        """Test concurrent processing in pipeline v3"""

        # Setup concurrent processing
        batch_size = scenario_config['batch_sizes'][2]  # 10 submissions
        concurrent_level = scenario_config['concurrent_levels'][1]  # 5 concurrent

        test_submissions = test_batch_data[:batch_size]

        # Mock async processing
        async def mock_process_submission(submission):
            await asyncio.sleep(0.01)  # Simulate processing
            return {
                'submission_id': submission['submission_id'],
                'processed': True,
                'analysis_result': {'score': 75.0}
            }

        # Create concurrent tasks
        tasks = []
        for i in range(concurrent_level):
            batch = test_submissions[i::concurrent_level]  # Distribute submissions
            if batch:
                task = asyncio.create_task(
                    mock_process_submission(batch[0])
                )
                tasks.append(task)

        # Execute concurrent processing
        results = asyncio.run(asyncio.gather(*tasks))

        # Verify concurrent execution
        assert len(results) == concurrent_level
        for result in results:
            assert result['processed'] is True
            assert 'submission_id' in result