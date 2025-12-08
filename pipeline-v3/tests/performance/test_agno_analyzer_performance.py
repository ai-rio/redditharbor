"""
Performance tests for AgnoOpportunityAnalyzer
"""

import asyncio
import time
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest

from tests.helpers.assertion_helpers import AgnoAnalysisAssertions
from tests.helpers.mock_agno_agents import MockAgnoTeam
from tests.helpers.test_data_factory import RedditSubmissionFactory
from tests.performance.conftest import PerformanceMetrics, PerformanceTestHelpers


class TestAgnoAnalyzerPerformance:
    """Performance tests for Agno analyzer"""

    def test_single_submission_performance(self, performance_monitor, mock_agno_team_performance):
        """Test performance on single submission analysis"""
        submission = RedditSubmissionFactory.create_single_submission('high_wtp_b2b')

        # Measure performance
        start_time = time.time()
        start_memory = performance_monitor.process.return_value.memory_info.return_value.rss / 1024 / 1024

        result = mock_agno_team_performance.analyze_opportunity(
            text=submission['text'],
            subreddit=submission['subreddit']
        )

        end_time = time.time()
        end_memory = performance_monitor.process.return_value.memory_info.return_value.rss / 1024 / 1024

        # Calculate metrics
        execution_time = end_time - start_time
        memory_usage = end_memory - start_memory

        # Assert performance thresholds
        assert execution_time <= 1.0, f"Single submission took {execution_time}s, expected < 1s"
        assert memory_usage < 50, f"Memory usage {memory_usage}MB too high"

        # Validate result
        AgnoAnalysisAssertions.assert_analysis_completeness(result)

    def test_batch_processing_performance(self, batch_sizes, performance_monitor, mock_agno_team_performance):
        """Test batch processing performance with varying batch sizes"""
        performance_results = []

        for batch_size in batch_sizes:
            submissions = RedditSubmissionFactory.create_batch_submissions(batch_size)

            start_time = time.time()
            start_memory = performance_monitor.process.return_value.memory_info.return_value.rss / 1024 / 1024

            results = mock_agno_team_performance.analyze_opportunity_batch(
                submissions=submissions,
                batch_size=batch_size
            )

            end_time = time.time()
            end_memory = performance_monitor.process.return_value.memory_info.return_value.rss / 1024 / 1024

            metrics = PerformanceMetrics(
                start_time=start_time,
                end_time=end_time,
                cpu_percent=performance_monitor.cpu_percent.return_value,
                memory_mb=end_memory - start_memory,
                execution_time=end_time - start_time,
                throughput=batch_size / (end_time - start_time),
                success_count=len(results),
                error_count=0,
                peak_memory_mb=end_memory,
                context_switches=150
            )

            performance_results.append(metrics)

            # Validate all results
            for result in results:
                AgnoAnalysisAssertions.assert_analysis_completeness(result)

        # Analyze scaling performance
        for i in range(1, len(performance_results)):
            prev_throughput = performance_results[i-1].throughput
            current_throughput = performance_results[i].throughput

            # Throughput should generally scale with batch size
            assert current_throughput >= prev_throughput * 0.8, (
                f"Throughput decreased from {prev_throughput} to {current_throughput} "
                f"when increasing batch size"
            )

    @pytest.mark.asyncio
    async def test_async_batch_performance(self, batch_sizes, performance_monitor, mock_agno_team_performance):
        """Test async batch processing performance"""
        async def analyze_async(submission):
            return await mock_agno_team_performance.analyze_opportunity_async(
                text=submission['text'],
                subreddit=submission['subreddit']
            )

        for batch_size in batch_sizes[:3]:  # Test smaller batches for async
            submissions = RedditSubmissionFactory.create_batch_submissions(batch_size)

            start_time = time.time()
            start_memory = performance_monitor.process.return_value.memory_info.return_value.rss / 1024 / 1024

            # Process concurrently
            tasks = [analyze_async(sub) for sub in submissions]
            results = await asyncio.gather(*tasks)

            end_time = time.time()
            end_memory = performance_monitor.process.return_value.memory_info.return_value.rss / 1024 / 1024

            metrics = PerformanceMetrics(
                start_time=start_time,
                end_time=end_time,
                cpu_percent=performance_monitor.cpu_percent.return_value,
                memory_mb=end_memory - start_memory,
                execution_time=end_time - start_time,
                throughput=batch_size / (end_time - start_time),
                success_count=len(results),
                error_count=0,
                peak_memory_mb=end_memory,
                context_switches=100
            )

            # Validate results
            for result in results:
                AgnoAnalysisAssertions.assert_analysis_completeness(result)

            # Async should be faster than sequential for larger batches
            if batch_size > 1:
                assert metrics.throughput > 2.0, f"Async throughput {metrics.throughput} too low"

    def test_concurrent_processing_performance(self, concurrent_levels, batch_sizes,
                                             performance_monitor, mock_agno_team_performance,
                                             performance_test_helpers):
        """Test performance under concurrent processing"""

        # Use moderate batch size for concurrent testing
        batch_size = 10
        submissions = RedditSubmissionFactory.create_batch_submissions(batch_size * 5)  # 5 batches

        thresholds = {
            'max_execution_time': 10.0,
            'min_throughput': 5.0
        }

        performance_results = []

        for concurrent_level in concurrent_levels[:3]:  # Test first 3 concurrency levels
            # Split submissions for concurrent processing
            batch_sublists = [submissions[i::concurrent_level] for i in range(concurrent_level)]
            batch_sublists = [batch for batch in batch_sublists if batch]  # Remove empty batches

            def process_batch(batch):
                return mock_agno_team_performance.analyze_opportunity_batch(
                    submissions=batch,
                    batch_size=len(batch)
                )

            # Measure performance
            metrics_data = performance_test_helpers.measure_concurrent_performance(
                process_batch, batch_size, concurrent_level, batch_sublists[0]
            )

            metrics = PerformanceMetrics(
                start_time=time.time() - metrics_data['execution_time'],
                end_time=time.time(),
                cpu_percent=performance_monitor.cpu_percent.return_value,
                memory_mb=50.0,  # Mock memory
                execution_time=metrics_data['execution_time'],
                throughput=metrics_data['throughput'],
                success_count=metrics_data['total_processed'],
                error_count=0,
                peak_memory_mb=100.0,
                context_switches=200
            )

            performance_results.append(metrics)
            performance_test_helpers.assert_performance_metrics(metrics, thresholds)

        # Analyze scaling behavior
        for i in range(1, len(performance_results)):
            prev_throughput = performance_results[i-1].throughput
            current_throughput = performance_results[i].throughput
            concurrent_ratio = concurrent_levels[i] / concurrent_levels[i-1]

            # Throughput should improve with more concurrency
            expected_throughput = prev_throughput * concurrent_ratio * 0.5  # Account for overhead
            assert current_throughput >= expected_throughput, (
                f"Concurrent throughput didn't scale: {prev_throughput} -> {current_throughput} "
                f"(expected ~{expected_throughput})"
            )

    def test_load_testing_performance(self, performance_monitor, mock_agno_team_performance,
                                     performance_test_helpers):
        """Test performance under load conditions"""

        # Test with different load scenarios
        load_scenarios = [
            {'name': 'light_load', 'count': 10, 'expected_throughput': 5.0},
            {'name': 'medium_load', 'count': 50, 'expected_throughput': 10.0},
            {'name': 'heavy_load', 'count': 100, 'expected_throughput': 15.0}
        ]

        performance_results = []

        for scenario in load_scenarios:
            submissions = performance_test_helpers.generate_load_test_submissions(
                scenario['count'], 'normal'
            )

            def process_load(submission):
                return mock_agno_team_performance.analyze_opportunity(
                    text=submission['text'],
                    subreddit=submission['subreddit']
                )

            # Measure performance
            throughput_data = performance_test_helpers.measure_throughput(
                map, process_load, submissions
            )

            metrics = PerformanceMetrics(
                start_time=time.time() - throughput_data['execution_time'],
                end_time=time.time(),
                cpu_percent=performance_monitor.cpu_percent.return_value,
                memory_mb=75.0,
                execution_time=throughput_data['execution_time'],
                throughput=throughput_data['throughput'],
                success_count=throughput_data['total_processed'],
                error_count=0,
                peak_memory_mb=150.0,
                context_switches=300
            )

            performance_results.append(metrics)

            # Validate throughput meets expectations
            assert metrics.throughput >= scenario['expected_throughput'] * 0.7, (
                f"{scenario['name']} throughput {metrics.throughput} below expected "
                f"{scenario['expected_throughput']} * 0.7"
            )

            # Validate all results
            for result in throughput_data['results']:
                AgnoAnalysisAssertions.assert_analysis_completeness(result)

    def test_memory_usage_scaling(self, batch_sizes, performance_monitor, mock_agno_team_performance):
        """Test memory usage scaling with batch size"""

        memory_usage = []

        for batch_size in batch_sizes:
            submissions = RedditSubmissionFactory.create_batch_submissions(batch_size)

            start_memory = performance_monitor.process.return_value.memory_info.return_value.rss / 1024 / 1024

            # Process batch
            results = mock_agno_team_performance.analyze_opportunity_batch(
                submissions=submissions,
                batch_size=batch_size
            )

            end_memory = performance_monitor.process.return_value.memory_info.return_value.rss / 1024 / 1024

            memory_increase = end_memory - start_memory
            memory_usage.append(memory_increase)

            # Memory should scale reasonably with batch size
            if batch_size > 1:
                # Memory increase per submission should be bounded
                memory_per_submission = memory_increase / batch_size
                assert memory_per_submission < 10, (
                    f"Memory per submission {memory_per_submission}MB too high for batch size {batch_size}"
                )

        # Memory should not grow exponentially
        for i in range(1, len(memory_usage)):
            ratio = memory_usage[i] / memory_usage[i-1]
            batch_ratio = batch_sizes[i] / batch_sizes[i-1]
            assert ratio <= batch_ratio * 1.5, (
                f"Memory growth ratio {ratio} exceeds batch size ratio {batch_ratio} by too much"
            )

    def test_edge_case_performance(self, edge_case_submissions, performance_monitor,
                                 mock_agno_team_performance):
        """Test performance with edge cases"""

        start_time = time.time()
        start_memory = performance_monitor.process.return_value.memory_info.return_value.rss / 1024 / 1024

        results = []
        errors = []

        for submission in edge_case_submissions:
            try:
                result = mock_agno_team_performance.analyze_opportunity(
                    text=submission['text'],
                    subreddit=submission['subreddit']
                )
                results.append(result)
            except Exception as e:
                errors.append(str(e))

        end_time = time.time()
        end_memory = performance_monitor.process.return_value.memory_info.return_value.rss / 1024 / 1024

        # Calculate metrics
        execution_time = end_time - start_time
        throughput = len(results) / execution_time if execution_time > 0 else 0

        # Edge cases shouldn't cause excessive slowness
        assert execution_time <= 5.0, f"Edge cases took {execution_time}s, expected < 5s"
        assert throughput >= 0.5, f"Edge case throughput {throughput} too low"

        # Most edge cases should be handled gracefully
        error_rate = len(errors) / len(edge_case_submissions)
        assert error_rate <= 0.2, f"Error rate {error_rate * 100}% too high for edge cases"

        # Validate successful results
        for result in results:
            AgnoAnalysisAssertions.assert_analysis_completeness(result)

    def test_rate_limit_performance(self, rate_limit_scenarios, performance_monitor,
                                  mock_agno_team_performance):
        """Test performance under rate limiting"""

        base_submissions = RedditSubmissionFactory.create_batch_submissions(20)

        for scenario in rate_limit_scenarios:
            with patch('time.sleep') as mock_sleep:
                # Mock the delay
                mock_sleep.side_effect = lambda x: time.sleep(x * 0.1)  # Accelerated for testing

                start_time = time.time()

                # Process with mocked rate limiting
                results = []
                for submission in base_submissions:
                    try:
                        result = mock_agno_team_performance.analyze_opportunity(
                            text=submission['text'],
                            subreddit=submission['subreddit']
                        )
                        results.append(result)
                    except:
                        pass

                end_time = time.time()

                execution_time = end_time - start_time
                expected_min_time = len(base_submissions) * scenario['delay'] * 0.1  # Accelerated

                # Should account for rate limiting
                assert execution_time >= expected_min_time * 0.5, (
                    f"Execution time {execution_time}s doesn't account for rate limiting "
                    f"(expected ~{expected_min_time}s)"
                )

    def test_performance_report_generation(self, performance_monitor, mock_agno_team_performance):
        """Test comprehensive performance report generation"""

        # Generate multiple test runs
        metrics_list = []

        for i in range(5):
            submissions = RedditSubmissionFactory.create_batch_submissions(10)

            start_time = time.time()
            start_memory = performance_monitor.process.return_value.memory_info.return_value.rss / 1024 / 1024

            results = mock_agno_team_performance.analyze_opportunity_batch(
                submissions=submissions,
                batch_size=10
            )

            end_time = time.time()
            end_memory = performance_monitor.process.return_value.memory_info.return_value.rss / 1024 / 1024

            from tests.performance.conftest import PerformanceMetrics
            metrics = PerformanceMetrics(
                start_time=start_time,
                end_time=end_time,
                cpu_percent=20 + i * 5,  # Vary CPU for realistic data
                memory_mb=50,
                execution_time=end_time - start_time,
                throughput=len(results) / (end_time - start_time),
                success_count=len(results),
                error_count=0,
                peak_memory_mb=end_memory,
                context_switches=100 + i * 20
            )
            metrics_list.append(metrics)

        # Generate report
        helpers = PerformanceTestHelpers()
        report = helpers.create_performance_report(metrics_list)

        # Validate report structure
        assert 'summary' in report
        assert 'execution_time' in report
        assert 'throughput' in report
        assert 'memory_usage' in report
        assert 'cpu_usage' in report

        # Validate summary statistics
        assert report['summary']['total_tests'] == 5
        assert report['summary']['success_rate'] == 100.0

        # Validate percentile calculations
        for metric in ['execution_time', 'throughput', 'memory_usage', 'cpu_usage']:
            assert 'p50' in report[metric]
            assert 'p90' in report[metric]
            assert 'p95' in report[metric]
            assert 'p99' in report[metric]
            assert report[metric]['p50'] <= report[metric]['p90'] <= report[metric]['p95'] <= report[metric]['p99']
