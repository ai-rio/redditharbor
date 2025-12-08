"""
Performance and load testing for pipeline components
"""

import random
import statistics
import time
from datetime import UTC, datetime, timezone
from typing import List
from unittest.mock import Mock, patch

import pytest

from models.analysis import AnalysisResult, AppIdea, MarketMetrics
from models.reddit import RedditSubmission
from orchestration.pipeline_orchestrator import (
    PipelineConfiguration,
    PipelineOrchestrator,
    PipelineResults,
)


class TestPipelinePerformance:
    """Performance tests for pipeline components"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock PipelineOrchestrator for performance testing"""
        mock_reddit_client = Mock()
        mock_analyzer = Mock()
        mock_analyzer_factory = Mock(return_value=mock_analyzer)
        mock_database_loader = Mock()
        mock_validator = Mock()
        mock_staging_layer = Mock()
        mock_settings = Mock()
        mock_settings.default_subreddits = ["test"]
        mock_settings.batch_size = 50

        orchestrator = PipelineOrchestrator(
            reddit_client=mock_reddit_client,
            analyzer_factory=mock_analyzer_factory,
            database_loader=mock_database_loader,
            validator=mock_validator,
            staging_layer=mock_staging_layer,
            settings=mock_settings
        )

        # Mock successful connections
        mock_reddit_client.test_connection.return_value = True
        mock_analyzer.test_connection.return_value = True
        mock_database_loader.test_connection.return_value = True

        return orchestrator, mock_reddit_client, mock_analyzer, mock_database_loader, mock_validator

    @pytest.fixture
    def large_submission_dataset(self) -> list[RedditSubmission]:
        """Generate a large dataset of Reddit submissions for testing"""
        submissions = []
        for i in range(1000):
            submission = RedditSubmission(
                id=f"perf_test_{i:04d}",
                title=f"Performance Test Submission {i}",
                text=f"This is test content for performance testing with submission number {i}. " * 10,
                author=f"user_{i % 100}",  # Some repeated authors
                upvotes=random.randint(1, 1000),
                score=random.randint(1, 1000),
                comments_count=random.randint(0, 500),
                subreddit=random.choice(["productivity", "technology", "business", "design"]),
                created_utc=datetime.now(UTC),
                permalink=f"https://reddit.com/r/test/perf_test_{i:04d}"
            )
            submissions.append(submission)
        return submissions

    @pytest.fixture
    def large_analysis_dataset(self) -> list[AnalysisResult]:
        """Generate a large dataset of analysis results for testing"""
        analyses = []
        quality_levels = [
            ("spam", True, 15.0, 25.0, "LOW", ["clickbait", "spam"]),
            ("low_quality", False, 35.0, 45.0, "MEDIUM", []),
            ("medium_quality", False, 65.0, 70.0, "MEDIUM", []),
            ("high_quality", False, 85.0, 90.0, "HIGH", [])
        ]

        for i in range(2000):
            level_name, is_spam, base_score, quality_score, trust_level, spam_indicators = random.choice(quality_levels)

            # Add some variation to scores
            score_variation = random.uniform(-10, 10)
            final_score = max(0, min(100, base_score + score_variation))
            quality_variation = random.uniform(-5, 5)
            final_quality_score = max(0, min(100, quality_score + quality_variation))

            analysis = AnalysisResult.model_construct(
                submission_id=f"perf_analysis_{i:04d}",
                analyzed_at=datetime.now(UTC),
                app_idea=AppIdea.model_construct(
                    title=f"Performance Test App {i} ({level_name})",
                    app_concept=f"Test application for performance testing number {i}",
                    problem_statement=f"Test problem statement for performance testing with index {i}",
                    core_functions=["Function 1", "Function 2"][:random.randint(1, 3)],
                    target_audience=f"Test users for performance test {i}"
                ),
                market_metrics=MarketMetrics.model_construct(
                    market_demand=final_score,
                    pain_intensity=final_score + random.uniform(-5, 5),
                    monetization_potential=final_score + random.uniform(-5, 5),
                    competition_level=max(0, min(100, 100 - final_score + random.uniform(-10, 10))),
                    technical_feasibility=final_score + random.uniform(-5, 5)
                ),
                final_score=final_score,
                content_quality_score=final_quality_score,
                is_spam=is_spam,
                spam_indicators=spam_indicators if is_spam else [],
                confidence_score=final_score + random.uniform(-5, 5),
                trust_level=trust_level
            )
            analyses.append(analysis)
        return analyses

    def test_filtering_performance_large_dataset(self, mock_orchestrator, large_analysis_dataset):
        """Test quality filtering performance with large dataset"""
        orchestrator, _, _, _, _ = mock_orchestrator

        config = PipelineConfiguration(
            min_score=50.0,
            min_confidence=50.0
        )

        # Measure filtering performance
        start_time = time.time()
        result = orchestrator._filter_by_quality(large_analysis_dataset, config)
        end_time = time.time()

        filtering_time = end_time - start_time
        analyses_per_second = len(large_analysis_dataset) / filtering_time

        # Performance assertions
        assert filtering_time < 10.0, f"Filtering {len(large_analysis_dataset)} analyses took too long: {filtering_time:.2f}s"
        assert analyses_per_second > 200, f"Filtering rate too slow: {analyses_per_second:.1f} analyses/second"

        # Verify correctness
        assert result['statistics']['total_input'] == len(large_analysis_dataset)
        assert len(result['filtered_analyses']) < len(large_analysis_dataset)  # Some should be filtered

        # Verify spam filtering
        spam_count = result['statistics']['spam_filtered']
        assert spam_count > 0, "Should have filtered some spam analyses"

        print(f"Filtered {len(large_analysis_dataset)} analyses in {filtering_time:.3f}s ({analyses_per_second:.1f} analyses/sec)")

    def test_filtering_performance_with_varying_dataset_sizes(self, mock_orchestrator):
        """Test filtering performance scaling with different dataset sizes"""
        orchestrator, _, _, _, _ = mock_orchestrator

        dataset_sizes = [100, 500, 1000, 2000, 5000]
        performance_results = []

        for size in dataset_sizes:
            # Generate dataset of specified size
            analyses = []
            for i in range(size):
                analysis = AnalysisResult.model_construct(
                    submission_id=f"perf_test_{size}_{i}",
                    analyzed_at=datetime.now(UTC),
                    app_idea=AppIdea.model_construct(
                        title=f"Test App {i}",
                        app_concept="Test concept",
                        problem_statement="Test problem",
                        core_functions=["Function"],
                        target_audience="Users"
                    ),
                    market_metrics=MarketMetrics.model_construct(
                        market_demand=50.0, pain_intensity=50.0, monetization_potential=50.0,
                        competition_level=50.0, technical_feasibility=50.0
                    ),
                    final_score=random.uniform(20, 90),
                    content_quality_score=random.uniform(10, 95),
                    is_spam=random.choice([True, False]),
                    spam_indicators=["spam"] if random.random() < 0.2 else [],
                    confidence_score=random.uniform(20, 90),
                    trust_level=random.choice(["LOW", "MEDIUM", "HIGH"])
                )
                analyses.append(analysis)

            config = PipelineConfiguration(min_score=50.0, min_confidence=50.0)

            # Measure performance
            start_time = time.time()
            result = orchestrator._filter_by_quality(analyses, config)
            end_time = time.time()

            filtering_time = end_time - start_time
            analyses_per_second = len(analyses) / filtering_time

            performance_results.append({
                'size': size,
                'time': filtering_time,
                'rate': analyses_per_second
            })

            print(f"Size: {size:5d}, Time: {filtering_time:6.3f}s, Rate: {analyses_per_second:7.1f} analyses/sec")

        # Verify performance scales reasonably
        for i in range(1, len(performance_results)):
            prev_result = performance_results[i-1]
            curr_result = performance_results[i]

            # Performance shouldn't degrade too much (allow for 3x time increase for 5x data increase)
            size_ratio = curr_result['size'] / prev_result['size']
            time_ratio = curr_result['time'] / prev_result['time']

            assert time_ratio < size_ratio * 1.5, f"Performance degradation too high: size {size_ratio}x, time {time_ratio}x"

    def test_memory_usage_during_filtering(self, mock_orchestrator, large_analysis_dataset):
        """Test memory usage during large dataset filtering"""
        import os

        import psutil

        orchestrator, _, _, _, _ = mock_orchestrator

        config = PipelineConfiguration(min_score=50.0, min_confidence=50.0)

        # Measure memory before filtering
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # Perform filtering
        result = orchestrator._filter_by_quality(large_analysis_dataset, config)

        # Measure memory after filtering
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before

        # Memory usage should be reasonable (less than 500MB for 2000 analyses)
        assert memory_used < 500, f"Memory usage too high: {memory_used:.1f}MB"

        print(f"Memory used for filtering {len(large_analysis_dataset)} analyses: {memory_used:.1f}MB")

    def test_concurrent_filtering_simulation(self, mock_orchestrator, large_analysis_dataset):
        """Simulate concurrent filtering scenarios"""
        orchestrator, _, _, _, _ = mock_orchestrator

        config = PipelineConfiguration(min_score=50.0, min_confidence=50.0)

        # Split dataset into chunks to simulate concurrent processing
        chunk_size = 500
        chunks = [large_analysis_dataset[i:i + chunk_size] for i in range(0, len(large_analysis_dataset), chunk_size)]

        all_results = []
        total_time = 0

        for chunk in chunks:
            start_time = time.time()
            result = orchestrator._filter_by_quality(chunk, config)
            end_time = time.time()

            chunk_time = end_time - start_time
            total_time += chunk_time
            all_results.extend(result['filtered_analyses'])

        # Verify all chunks were processed
        total_processed = sum(chunk['statistics']['total_input'] for chunk in chunks)
        assert total_processed == len(large_analysis_dataset)

        # Performance should still be reasonable
        avg_time_per_chunk = total_time / len(chunks)
        assert avg_time_per_chunk < 2.0, f"Average chunk processing time too high: {avg_time_per_chunk:.2f}s"

        print(f"Processed {len(chunks)} chunks in {total_time:.2f}s (avg: {avg_time_per_chunk:.2f}s per chunk)")

    def test_pipeline_end_to_end_performance(self, mock_orchestrator, large_submission_dataset):
        """Test end-to-end pipeline performance with large dataset"""
        orchestrator, mock_reddit_client, mock_analyzer, mock_database_loader, mock_validator = mock_orchestrator

        # Generate corresponding analyses
        analyses = []
        for submission in large_submission_dataset:
            analysis = AnalysisResult.model_construct(
                submission_id=submission.id,
                analyzed_at=datetime.now(UTC),
                app_idea=AppIdea.model_construct(
                    title=f"App for {submission.id}",
                    app_concept="Test concept",
                    problem_statement="Test problem",
                    core_functions=["Function"],
                    target_audience="Users"
                ),
                market_metrics=MarketMetrics.model_construct(
                    market_demand=60.0, pain_intensity=65.0, monetization_potential=70.0,
                    competition_level=45.0, technical_feasibility=75.0
                ),
                final_score=random.uniform(40, 90),
                content_quality_score=random.uniform(30, 95),
                is_spam=random.random() < 0.1,
                spam_indicators=["spam"] if random.random() < 0.1 else [],
                confidence_score=random.uniform(40, 90),
                trust_level=random.choice(["LOW", "MEDIUM", "HIGH"])
            )
            analyses.append(analysis)

        # Configure mocks
        mock_reddit_client.fetch_submissions.return_value = large_submission_dataset
        mock_analyzer.analyze_batch.return_value = analyses
        mock_database_loader.create_tables.return_value = None
        mock_database_loader.store_analyses.return_value = {"stored": len(analyses), "skipped": 0, "errors": 0}
        mock_database_loader.get_statistics.return_value = {
            "total_opportunities": len(analyses),
            "average_score": 65.0,
            "high_score_percentage": 70.0
        }
        mock_validator.get_quality_summary.return_value = {
            "validation_rate": 80.0,
            "high_score_rate": 75.0,
            "avg_final_score": 65.0,
            "trust_distribution": {"HIGH": len(analyses) // 2, "MEDIUM": len(analyses) // 3, "LOW": len(analyses) // 6}
        }

        # Mock staging layer
        orchestrator.staging_layer.store_submissions.return_value = ["batch_1", "batch_2", "batch_3"]
        orchestrator.staging_layer.get_batch.side_effect = [
            large_submission_dataset[:333],
            large_submission_dataset[333:666],
            large_submission_dataset[666:]
        ]
        orchestrator.staging_layer.get_statistics.return_value = {
            "processed_submissions": len(large_submission_dataset),
            "deduplication_rate": 5.0
        }

        config = PipelineConfiguration(
            subreddits=["test"],
            limit=len(large_submission_dataset),
            min_score=50.0,
            min_confidence=50.0,
            test_mode=True,
            dry_run=False,
            enable_staging=True
        )

        # Measure end-to-end performance
        start_time = time.time()
        results = orchestrator.execute_pipeline(config)
        end_time = time.time()

        total_time = end_time - start_time
        submissions_per_second = results.submissions_extracted / total_time
        analyses_per_second = results.analyses_generated / total_time

        # Performance assertions
        assert total_time < 30.0, f"End-to-end pipeline took too long: {total_time:.2f}s"
        assert submissions_per_second > 30, f"Submission processing rate too slow: {submissions_per_second:.1f} submissions/sec"
        assert analyses_per_second > 30, f"Analysis processing rate too slow: {analyses_per_second:.1f} analyses/sec"

        # Verify correctness
        assert results.submissions_extracted == len(large_submission_dataset)
        assert results.analyses_generated == len(analyses)
        assert results.high_quality_analyses > 0
        assert results.analyses_stored > 0

        print("End-to-end performance:")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Submissions: {results.submissions_extracted} ({submissions_per_second:.1f} submissions/sec)")
        print(f"  Analyses: {results.analyses_generated} ({analyses_per_second:.1f} analyses/sec)")
        print(f"  Quality filtered: {results.high_quality_analyses} ({results.high_quality_analyses/results.analyses_generated*100:.1f}% pass rate)")

    def test_database_storage_performance(self, mock_orchestrator, large_analysis_dataset):
        """Test database storage performance with large dataset"""
        orchestrator, _, _, mock_database_loader, _ = mock_orchestrator

        # Mock database storage to measure performance
        storage_times = []

        def mock_store_analyses(analyses, submissions):
            start_time = time.time()
            # Simulate database storage work
            time.sleep(0.001 * len(analyses))  # 1ms per analysis
            end_time = time.time()
            storage_times.append(end_time - start_time)
            return {"stored": len(analyses), "skipped": 0, "errors": 0}

        mock_database_loader.store_analyses.side_effect = mock_store_analyses

        # Test storage in batches
        batch_size = 100
        for i in range(0, len(large_analysis_dataset), batch_size):
            batch = large_analysis_dataset[i:i + batch_size]
            corresponding_submissions = [RedditSubmission(
                id=analysis.submission_id,
                title="Test",
                text="Test",
                author="user",
                upvotes=1,
                score=1,
                comments_count=0,
                subreddit="test",
                created_utc=datetime.now(UTC),
                permalink="https://reddit.com/r/test/test"
            ) for analysis in batch]

            stats, storage_time = orchestrator._store_analyses(
                batch, corresponding_submissions, PipelineConfiguration()
            )

        # Performance analysis
        avg_storage_time = statistics.mean(storage_times)
        total_storage_time = sum(storage_times)
        total_analyses = len(large_analysis_dataset)
        analyses_per_second = total_analyses / total_storage_time

        assert avg_storage_time < 1.0, f"Average batch storage time too high: {avg_storage_time:.3f}s"
        assert analyses_per_second > 100, f"Storage rate too slow: {analyses_per_second:.1f} analyses/sec"

        print("Database storage performance:")
        print(f"  Total analyses: {total_analyses}")
        print(f"  Total time: {total_storage_time:.2f}s")
        print(f"  Average batch time: {avg_storage_time:.3f}s")
        print(f"  Storage rate: {analyses_per_second:.1f} analyses/sec")

    def test_quality_filtering_statistics_accuracy(self, mock_orchestrator, large_analysis_dataset):
        """Test that filtering statistics are accurate for large datasets"""
        orchestrator, _, _, _, _ = mock_orchestrator

        config = PipelineConfiguration(min_score=50.0, min_confidence=50.0)

        result = orchestrator._filter_by_quality(large_analysis_dataset, config)
        stats = result['statistics']

        # Verify statistics accuracy
        actual_input = len(large_analysis_dataset)
        actual_output = len(result['filtered_analyses'])
        actual_filtered = actual_input - actual_output

        assert stats['total_input'] == actual_input
        assert stats['final_count'] == actual_output
        assert stats['total_filtered'] == actual_filtered

        # Verify filtering breakdown
        breakdown_total = (
            stats['spam_filtered'] +
            stats['low_quality_filtered'] +
            stats['below_min_score_filtered'] +
            stats['below_min_confidence_filtered']
        )
        assert breakdown_total == actual_filtered

        # Verify percentages
        if stats['total_input'] > 0:
            pass_rate_percentage = stats['filtering_percentages']['pass_rate_percentage']
            expected_pass_rate = (actual_output / actual_input) * 100
            assert abs(pass_rate_percentage - expected_pass_rate) < 0.1, "Pass rate percentage incorrect"

        print("Statistics accuracy check:")
        print(f"  Input: {actual_input}")
        print(f"  Output: {actual_output}")
        print(f"  Pass rate: {pass_rate_percentage:.1f}%")
        print(f"  Spam filtered: {stats['spam_filtered']}")
        print(f"  Low quality filtered: {stats['low_quality_filtered']}")
        print(f"  Below score filtered: {stats['below_min_score_filtered']}")
        print(f"  Below confidence filtered: {stats['below_min_confidence_filtered']}")

    def test_pipeline_performance_with_stress_conditions(self, mock_orchestrator):
        """Test pipeline performance under stress conditions"""
        orchestrator, mock_reddit_client, mock_analyzer, mock_database_loader, mock_validator = mock_orchestrator

        # Create a challenging dataset
        stress_analyses = []
        for i in range(5000):
            # Create analyses with edge cases and varied quality
            if i % 10 == 0:
                # 10% spam
                analysis = AnalysisResult.model_construct(
                    submission_id=f"stress_spam_{i}",
                    analyzed_at=datetime.now(UTC),
                    app_idea=AppIdea.model_construct(
                        title=f"SPAM!!! GET RICH {i}",
                        app_concept="AMAZING OPPORTUNITY" * 20,
                        problem_statement="URGENT!!!" * 15,
                        core_functions=["Quick money", "No work", "Instant results"],
                        target_audience="EVERYONE!!!"
                    ),
                    market_metrics=MarketMetrics.model_construct(
                        market_demand=100.0, pain_intensity=100.0, monetization_potential=100.0,
                        competition_level=0.0, technical_feasibility=100.0
                    ),
                    final_score=100.0,
                    content_quality_score=5.0,
                    is_spam=True,
                    spam_indicators=["spam", "clickbait", "all caps", "exaggerated"],
                    confidence_score=20.0,
                    trust_level="LOW"
                )
            elif i % 5 == 0:
                # 20% very low quality
                analysis = AnalysisResult.model_construct(
                    submission_id=f"stress_low_{i}",
                    analyzed_at=datetime.now(UTC),
                    app_idea=AppIdea.model_construct(
                        title=f"App {i}",
                        app_concept="Concept",
                        problem_statement="Problem",
                        core_functions=["Function"],
                        target_audience="Users"
                    ),
                    market_metrics=MarketMetrics.model_construct(
                        market_demand=10.0, pain_intensity=5.0, monetization_potential=5.0,
                        competition_level=95.0, technical_feasibility=10.0
                    ),
                    final_score=5.0,
                    content_quality_score=20.0,
                    is_spam=False,
                    spam_indicators=[],
                    confidence_score=10.0,
                    trust_level="LOW"
                )
            else:
                # 70% normal/medium quality
                analysis = AnalysisResult.model_construct(
                    submission_id=f"stress_normal_{i}",
                    analyzed_at=datetime.now(UTC),
                    app_idea=AppIdea.model_construct(
                        title=f"Quality App {i}",
                        app_concept="Reasonable application concept with decent detail",
                        problem_statement="Real problem statement with adequate detail and explanation",
                        core_functions=["Core function 1", "Core function 2"],
                        target_audience="Specific target audience with clear description"
                    ),
                    market_metrics=MarketMetrics.model_construct(
                        market_demand=60.0 + random.uniform(-20, 20),
                        pain_intensity=65.0 + random.uniform(-20, 20),
                        monetization_potential=55.0 + random.uniform(-20, 20),
                        competition_level=45.0 + random.uniform(-20, 20),
                        technical_feasibility=70.0 + random.uniform(-20, 20)
                    ),
                    final_score=60.0 + random.uniform(-30, 30),
                    content_quality_score=65.0 + random.uniform(-30, 30),
                    is_spam=False,
                    spam_indicators=[],
                    confidence_score=65.0 + random.uniform(-30, 30),
                    trust_level=random.choice(["LOW", "MEDIUM", "HIGH"])
                )
            stress_analyses.append(analysis)

        config = PipelineConfiguration(min_score=40.0, min_confidence=40.0)

        # Measure performance under stress
        start_time = time.time()
        result = orchestrator._filter_by_quality(stress_analyses, config)
        end_time = time.time()

        stress_time = end_time - start_time
        analyses_per_second = len(stress_analyses) / stress_time

        # Should still perform reasonably under stress
        assert stress_time < 30.0, f"Stress test took too long: {stress_time:.2f}s"
        assert analyses_per_second > 150, f"Stress test rate too slow: {analyses_per_second:.1f} analyses/sec"

        # Should correctly filter out spam and low quality
        assert result['statistics']['spam_filtered'] > 400  # ~10% of 5000
        assert result['statistics']['low_quality_filtered'] > 800  # ~20% of 5000

        print("Stress test results:")
        print(f"  Total analyses: {len(stress_analyses)}")
        print(f"  Processing time: {stress_time:.2f}s")
        print(f"  Processing rate: {analyses_per_second:.1f} analyses/sec")
        print(f"  Spam filtered: {result['statistics']['spam_filtered']}")
        print(f"  Low quality filtered: {result['statistics']['low_quality_filtered']}")
        print(f"  Final count: {result['statistics']['final_count']} ({result['statistics']['final_count']/len(stress_analyses)*100:.1f}% pass rate)")


class TestPipelineLoadTesting:
    """Load testing for pipeline components"""

    def test_memory_leak_detection(self):
        """Test for memory leaks during repeated operations"""
        import gc
        import os

        import psutil

        # Create orchestrator
        mock_orchestrator = PipelineOrchestrator()

        # Generate test data
        analyses = []
        for i in range(100):
            analysis = AnalysisResult.model_construct(
                submission_id=f"memory_test_{i}",
                analyzed_at=datetime.now(UTC),
                app_idea=AppIdea.model_construct(
                    title=f"Memory Test App {i}",
                    app_concept="Test concept for memory testing",
                    problem_statement="Test problem for memory testing",
                    core_functions=["Function"],
                    target_audience="Test users"
                ),
                market_metrics=MarketMetrics.model_construct(
                    market_demand=50.0, pain_intensity=50.0, monetization_potential=50.0,
                    competition_level=50.0, technical_feasibility=50.0
                ),
                final_score=50.0,
                content_quality_score=50.0,
                is_spam=False,
                spam_indicators=[],
                confidence_score=50.0,
                trust_level="MEDIUM"
            )
            analyses.append(analysis)

        config = PipelineConfiguration(min_score=30.0, min_confidence=30.0)

        process = psutil.Process(os.getpid())
        memory_measurements = []

        # Run filtering multiple times and measure memory
        for iteration in range(50):
            gc.collect()  # Force garbage collection
            memory_before = process.memory_info().rss / 1024 / 1024  # MB

            result = mock_orchestrator._filter_by_quality(analyses, config)

            gc.collect()
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_measurements.append(memory_after)

            if iteration % 10 == 0:
                print(f"Iteration {iteration}: Memory = {memory_after:.1f}MB")

        # Check for memory leaks
        initial_memory = memory_measurements[0]
        final_memory = memory_measurements[-1]
        memory_growth = final_memory - initial_memory

        # Memory growth should be minimal (less than 50MB over 50 iterations)
        assert memory_growth < 50, f"Potential memory leak detected: {memory_growth:.1f}MB growth over 50 iterations"

        print("Memory leak test:")
        print(f"  Initial memory: {initial_memory:.1f}MB")
        print(f"  Final memory: {final_memory:.1f}MB")
        print(f"  Memory growth: {memory_growth:.1f}MB")
        print(f"  Average memory: {statistics.mean(memory_measurements):.1f}MB")
        print(f"  Memory variation: {statistics.stdev(memory_measurements):.1f}MB")

    def test_concurrent_simulation_load(self):
        """Simulate concurrent load on pipeline components"""
        import queue
        import threading

        # Create orchestrator
        mock_orchestrator = PipelineOrchestrator()

        # Create work queue
        work_queue = queue.Queue()
        results_queue = queue.Queue()

        # Generate work items
        for batch_id in range(20):
            batch_analyses = []
            for i in range(100):
                analysis = AnalysisResult.model_construct(
                    submission_id=f"concurrent_test_{batch_id}_{i}",
                    analyzed_at=datetime.now(UTC),
                    app_idea=AppIdea.model_construct(
                        title=f"Concurrent Test App {batch_id}_{i}",
                        app_concept="Test concept for concurrent testing",
                        problem_statement="Test problem for concurrent testing",
                        core_functions=["Function"],
                        target_audience="Test users"
                    ),
                    market_metrics=MarketMetrics.model_construct(
                        market_demand=50.0, pain_intensity=50.0, monetization_potential=50.0,
                        competition_level=50.0, technical_feasibility=50.0
                    ),
                    final_score=50.0 + random.uniform(-20, 20),
                    content_quality_score=50.0 + random.uniform(-20, 20),
                    is_spam=random.random() < 0.1,
                    spam_indicators=["spam"] if random.random() < 0.1 else [],
                    confidence_score=50.0 + random.uniform(-20, 20),
                    trust_level=random.choice(["LOW", "MEDIUM", "HIGH"])
                )
                batch_analyses.append(analysis)
            work_queue.put((batch_id, batch_analyses))

        # Worker function
        def worker():
            while True:
                try:
                    batch_id, analyses = work_queue.get_nowait()
                except queue.Empty:
                    break

                config = PipelineConfiguration(min_score=40.0, min_confidence=40.0)
                start_time = time.time()
                result = mock_orchestrator._filter_by_quality(analyses, config)
                end_time = time.time()

                results_queue.put({
                    'batch_id': batch_id,
                    'processing_time': end_time - start_time,
                    'input_count': len(analyses),
                    'output_count': len(result['filtered_analyses'])
                })

        # Start worker threads
        num_workers = 4
        threads = []
        for _ in range(num_workers):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # Wait for all workers to complete
        for thread in threads:
            thread.join()

        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        # Analyze concurrent performance
        total_analyses = sum(r['input_count'] for r in results)
        total_time = max(r['processing_time'] for r in results)  # Wall clock time
        total_filtered = sum(r['output_count'] for r in results)
        avg_processing_time = statistics.mean(r['processing_time'] for r in results)

        print("Concurrent load test results:")
        print(f"  Workers: {num_workers}")
        print(f"  Batches processed: {len(results)}")
        print(f"  Total analyses: {total_analyses}")
        print(f"  Total filtered: {total_filtered}")
        print(f"  Wall clock time: {total_time:.3f}s")
        print(f"  Average batch time: {avg_processing_time:.3f}s")
        print(f"  Overall throughput: {total_analyses/total_time:.1f} analyses/sec")

        # Performance assertions
        assert len(results) == 20, "Not all batches were processed"
        assert total_analyses == 2000, "Incorrect number of analyses processed"
        assert total_time < 5.0, "Concurrent processing took too long"
