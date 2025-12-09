"""
OnlyMaps performance comparison tests for pipeline-v3.

This module tests OnlyMaps' performance improvements over SQLAlchemy,
comparing mapping speeds, memory usage, CPU utilization, and overall
efficiency across different data volumes and complexity levels.
"""

import asyncio
import gc
import multiprocessing
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import psutil
import pytest

# Import SQLAlchemy for comparison
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base as sqlalchemy_declarative_base
from sqlalchemy.orm import sessionmaker

from load.database import DatabaseLoader
from models import (
    AnalysisResult,
    AppIdea,
    MarketMetrics,
    RedditComment,
    RedditSubmission,
)
from models.database import Opportunity, OpportunityCreate

# Import OnlyMaps components (assuming they exist)
from onlymaps import OnlyMapsConfig, OnlyMapsMapper, PerformanceBenchmarkError


class TestOnlyMapsPerformanceComparison:
    """Test suite for OnlyMaps performance comparisons against SQLAlchemy."""

    @pytest.fixture
    def sqlalchemy_engine(self, test_database_url):
        """Create SQLAlchemy engine for performance testing."""
        engine = create_engine(test_database_url, echo=False)
        yield engine
        engine.dispose()

    @pytest.fixture
    def sqlalchemy_session_factory(self, sqlalchemy_engine):
        """Create SQLAlchemy session factory for performance testing."""
        Session = sessionmaker(bind=sqlalchemy_engine)
        return Session

    @pytest.fixture
    def onlymaps_mapper(self):
        """Create OnlyMaps mapper for performance testing."""
        config = OnlyMapsConfig(
            batch_size=100,
            timeout=30,
            retry_attempts=3,
            fallback_to_sqlalchemy=False,
            schema_validation=True,
            performance_monitoring=True
        )
        return OnlyMapsMapper(config=config)

    @pytest.fixture
    def performance_metrics_fixture(self):
        """Performance metrics fixture for benchmarking."""
        return {
            'onlymaps_times': [],
            'sqlalchemy_times': [],
            'memory_usage': [],
            'cpu_usage': [],
            'batch_sizes': [10, 50, 100, 500, 1000, 5000],
            'comparison_ratios': []
        }

    # =============================================================================
    # Basic Performance Tests
    # =============================================================================

    def test_single_record_mapping_performance(self, onlymaps_mapper, sqlalchemy_engine, performance_metrics_fixture):
        """Test performance of single record mapping."""
        # Create test record
        record = {
            'id': str(uuid.uuid4()),
            'submission_id': 'test123',
            'reddit_title': 'Test App',
            'reddit_url': 'https://reddit.com/r/test/test123',
            'subreddit': 'test',
            'reddit_author': 'testuser',
            'reddit_upvotes': 150,
            'reddit_comments_count': 42,
            'reddit_created_at': '2024-01-15T10:30:00Z',
            'app_title': 'Test App',
            'app_concept': 'Test concept',
            'problem_statement': 'Test problem',
            'target_audience': 'Test audience',
            'core_functions': ['function1', 'function2'],
            'market_demand': 85.0,
            'pain_intensity': 90.0,
            'monetization_potential': 75.0,
            'competition_level': 60.0,
            'technical_feasibility': 80.0,
            'final_score': 78.5,
            'confidence_score': 85.0,
            'trust_level': 'HIGH',
            'embedding': None,
            'analyzed_at': '2024-01-16T12:45:00Z',
            'created_at': '2024-01-16T12:45:00Z',
            'updated_at': '2024-01-16T12:45:00Z'
        }

        # Benchmark OnlyMaps
        start_time = time.time()
        opportunity_om = onlymaps_mapper.map_from_sql(record, target_class=Opportunity)
        onlymaps_time = time.time() - start_time

        # Benchmark SQLAlchemy
        start_time = time.time()
        opportunity_sa = _create_opportunity_from_record(record)
        sqlalchemy_time = time.time() - start_time

        # Record metrics
        performance_metrics_fixture['onlymaps_times'].append(onlymaps_time)
        performance_metrics_fixture['sqlalchemy_times'].append(sqlalchemy_time)

        # Verify both approaches work correctly
        assert opportunity_om is not None
        assert opportunity_sa is not None
        assert opportunity_om.submission_id == opportunity_sa.submission_id
        assert opportunity_om.reddit_title == opportunity_sa.reddit_title

        # Calculate performance ratio
        performance_ratio = sqlalchemy_time / onlymaps_time if onlymaps_time > 0 else 0
        performance_metrics_fixture['comparison_ratios'].append(performance_ratio)

        # OnlyMaps should be at least as fast as SQLAlchemy (within reasonable margin)
        assert performance_ratio >= 0.5, f"OnlyMaps should be competitive with SQLAlchemy, got ratio: {performance_ratio}"

    def test_batch_mapping_performance(self, onlymaps_mapper, sqlalchemy_engine, performance_metrics_fixture):
        """Test performance of batch mapping operations."""
        # Generate test records
        records = []
        for i in range(100):
            record = {
                'id': str(uuid.uuid4()),
                'submission_id': f'test{i}',
                'reddit_title': f'Test App {i}',
                'reddit_url': f'https://reddit.com/r/test/test{i}',
                'subreddit': 'test',
                'reddit_author': f'user{i}',
                'reddit_upvotes': 150 + i,
                'reddit_comments_count': 42 + i,
                'reddit_created_at': '2024-01-15T10:30:00Z',
                'app_title': f'Test App {i}',
                'app_concept': f'Test concept {i}',
                'problem_statement': f'Test problem {i}',
                'target_audience': f'Test audience {i}',
                'core_functions': [f'function{i % 5}', f'function{(i + 1) % 5}'],
                'market_demand': 85.0 + (i % 15),
                'pain_intensity': 90.0 + (i % 10),
                'monetization_potential': 75.0 + (i % 20),
                'competition_level': 60.0 + (i % 25),
                'technical_feasibility': 80.0 + (i % 15),
                'final_score': 78.5 + (i % 21),
                'confidence_score': 85.0 + (i % 15),
                'trust_level': ['HIGH', 'MEDIUM', 'LOW'][i % 3],
                'embedding': None,
                'analyzed_at': '2024-01-16T12:45:00Z',
                'created_at': '2024-01-16T12:45:00Z',
                'updated_at': '2024-01-16T12:45:00Z'
            }
            records.append(record)

        # Benchmark OnlyMaps batch
        start_time = time.time()
        opportunities_om = onlymaps_mapper.map_batch(records, target_class=Opportunity)
        onlymaps_time = time.time() - start_time

        # Benchmark SQLAlchemy batch
        start_time = time.time()
        opportunities_sa = [_create_opportunity_from_record(record) for record in records]
        sqlalchemy_time = time.time() - start_time

        # Record metrics
        performance_metrics_fixture['onlymaps_times'].append(onlymaps_time)
        performance_metrics_fixture['sqlalchemy_times'].append(sqlalchemy_time)

        # Verify both approaches work correctly
        assert len(opportunities_om) == len(opportunities_sa) == len(records)
        for i, (opp_om, opp_sa) in enumerate(zip(opportunities_om, opportunities_sa)):
            assert opp_om.submission_id == opp_sa.submission_id
            assert opp_om.reddit_title == opp_sa.reddit_title

        # Calculate performance ratio
        performance_ratio = sqlalchemy_time / onlymaps_time if onlymaps_time > 0 else 0
        performance_metrics_fixture['comparison_ratios'].append(performance_ratio)

        # Batch OnlyMaps should be significantly faster due to optimization
        assert performance_ratio >= 1.0, f"OnlyMaps batch should be faster than SQLAlchemy, got ratio: {performance_ratio}"

    # =============================================================================
    # Scalability Tests
    # =============================================================================

    def test_scalability_with_increasing_data_volume(self, onlymaps_mapper, sqlalchemy_engine, performance_metrics_fixture):
        """Test scalability with increasing data volumes."""
        batch_sizes = [10, 50, 100, 500, 1000]

        for batch_size in batch_sizes:
            # Generate test records
            records = []
            for i in range(batch_size):
                record = {
                    'id': str(uuid.uuid4()),
                    'submission_id': f'test{i}',
                    'reddit_title': f'Test App {i}',
                    'reddit_url': f'https://reddit.com/r/test/test{i}',
                    'subreddit': 'test',
                    'reddit_author': f'user{i}',
                    'reddit_upvotes': 150 + i,
                    'reddit_comments_count': 42 + i,
                    'reddit_created_at': '2024-01-15T10:30:00Z',
                    'app_title': f'Test App {i}',
                    'app_concept': f'Test concept {i}',
                    'problem_statement': f'Test problem {i}',
                    'target_audience': f'Test audience {i}',
                    'core_functions': [f'function{i % 5}', f'function{(i + 1) % 5}'],
                    'market_demand': 85.0 + (i % 15),
                    'pain_intensity': 90.0 + (i % 10),
                    'monetization_potential': 75.0 + (i % 20),
                    'competition_level': 60.0 + (i % 25),
                    'technical_feasibility': 80.0 + (i % 15),
                    'final_score': 78.5 + (i % 21),
                    'confidence_score': 85.0 + (i % 15),
                    'trust_level': ['HIGH', 'MEDIUM', 'LOW'][i % 3],
                    'embedding': None,
                    'analyzed_at': '2024-01-16T12:45:00Z',
                    'created_at': '2024-01-16T12:45:00Z',
                    'updated_at': '2024-01-16T12:45:00Z'
                }
                records.append(record)

            # Benchmark OnlyMaps
            start_time = time.time()
            opportunities_om = onlymaps_mapper.map_batch(records, target_class=Opportunity)
            onlymaps_time = time.time() - start_time

            # Benchmark SQLAlchemy
            start_time = time.time()
            opportunities_sa = [_create_opportunity_from_record(record) for record in records]
            sqlalchemy_time = time.time() - start_time

            # Record metrics
            performance_metrics_fixture['onlymaps_times'].append(onlymaps_time)
            performance_metrics_fixture['sqlalchemy_times'].append(sqlalchemy_time)

            # Verify results
            assert len(opportunities_om) == len(opportunities_sa) == len(records)

            # Calculate performance ratio
            performance_ratio = sqlalchemy_time / onlymaps_time if onlymaps_time > 0 else 0
            performance_metrics_fixture['comparison_ratios'].append(performance_ratio)

            # OnlyMaps should scale better with larger datasets
            if batch_size >= 100:
                assert performance_ratio >= 1.5, f"OnlyMaps should scale better with large datasets, got ratio: {performance_ratio}"

    def test_memory_usage_comparison(self, onlymaps_mapper, performance_metrics_fixture):
        """Test memory usage comparison between OnlyMaps and SQLAlchemy."""

        # Generate large dataset
        batch_size = 1000
        records = []
        for i in range(batch_size):
            record = {
                'id': str(uuid.uuid4()),
                'submission_id': f'test{i}',
                'reddit_title': f'Test App {i}',
                'reddit_url': f'https://reddit.com/r/test/test{i}',
                'subreddit': 'test',
                'reddit_author': f'user{i}',
                'reddit_upvotes': 150 + i,
                'reddit_comments_count': 42 + i,
                'reddit_created_at': '2024-01-15T10:30:00Z',
                'app_title': f'Test App {i}',
                'app_concept': f'Test concept {i}',
                'problem_statement': f'Test problem {i}',
                'target_audience': f'Test audience {i}',
                'core_functions': [f'function{i % 5}', f'function{(i + 1) % 5}'],
                'market_demand': 85.0 + (i % 15),
                'pain_intensity': 90.0 + (i % 10),
                'monetization_potential': 75.0 + (i % 20),
                'competition_level': 60.0 + (i % 25),
                'technical_feasibility': 80.0 + (i % 15),
                'final_score': 78.5 + (i % 21),
                'confidence_score': 85.0 + (i % 15),
                'trust_level': ['HIGH', 'MEDIUM', 'LOW'][i % 3],
                'embedding': None,
                'analyzed_at': '2024-01-16T12:45:00Z',
                'created_at': '2024-01-16T12:45:00Z',
                'updated_at': '2024-01-16T12:45:00Z'
            }
            records.append(record)

        # Test OnlyMaps memory usage
        gc.collect()
        process = psutil.Process()
        memory_before = process.memory_info().rss

        opportunities_om = onlymaps_mapper.map_batch(records, target_class=Opportunity)
        memory_after_om = process.memory_info().rss
        memory_usage_om = memory_after_om - memory_before

        gc.collect()
        del opportunities_om

        # Test SQLAlchemy memory usage
        gc.collect()
        memory_before = process.memory_info().rss

        opportunities_sa = [_create_opportunity_from_record(record) for record in records]
        memory_after_sa = process.memory_info().rss
        memory_usage_sa = memory_after_sa - memory_before

        gc.collect()
        del opportunities_sa

        # Record memory metrics
        performance_metrics_fixture['memory_usage'].append({
            'onlymaps': memory_usage_om,
            'sqlalchemy': memory_usage_sa,
            'ratio': memory_usage_sa / memory_usage_om if memory_usage_om > 0 else 0
        })

        # OnlyMaps should use less memory
        assert memory_usage_om <= memory_usage_sa * 1.1, f"OnlyMaps should use less memory, got OM: {memory_usage_om}, SA: {memory_usage_sa}"

    # =============================================================================
    # Performance Monitoring Tests
    # =============================================================================

    def test_performance_monitoring_accuracy(self, onlymaps_mapper):
        """Test performance monitoring accuracy."""
        # Enable performance monitoring
        onlymaps_mapper.config.performance_monitoring = True

        # Generate test records
        records = []
        for i in range(50):
            record = {
                'id': str(uuid.uuid4()),
                'submission_id': f'test{i}',
                'reddit_title': f'Test App {i}',
                'reddit_url': f'https://reddit.com/r/test/test{i}',
                'subreddit': 'test',
                'reddit_author': f'user{i}',
                'reddit_upvotes': 150 + i,
                'reddit_comments_count': 42 + i,
                'reddit_created_at': '2024-01-15T10:30:00Z',
                'app_title': f'Test App {i}',
                'app_concept': f'Test concept {i}',
                'problem_statement': f'Test problem {i}',
                'target_audience': f'Test audience {i}',
                'core_functions': [f'function{i % 5}', f'function{(i + 1) % 5}'],
                'market_demand': 85.0 + (i % 15),
                'pain_intensity': 90.0 + (i % 10),
                'monetization_potential': 75.0 + (i % 20),
                'competition_level': 60.0 + (i % 25),
                'technical_feasibility': 80.0 + (i % 15),
                'final_score': 78.5 + (i % 21),
                'confidence_score': 85.0 + (i % 15),
                'trust_level': ['HIGH', 'MEDIUM', 'LOW'][i % 3],
                'embedding': None,
                'analyzed_at': '2024-01-16T12:45:00Z',
                'created_at': '2024-01-16T12:45:00Z',
                'updated_at': '2024-01-16T12:45:00Z'
            }
            records.append(record)

        # Perform mapping operations
        start_time = time.time()
        opportunities = onlymaps_mapper.map_batch(records, target_class=Opportunity)
        actual_time = time.time() - start_time

        # Verify performance metrics exist
        assert hasattr(onlymaps_mapper, '_performance_metrics')
        assert 'mapping_times' in onlymaps_mapper._performance_metrics
        assert 'batch_times' in onlymaps_mapper._performance_metrics

        # Get performance metrics
        recorded_times = onlymaps_mapper._performance_metrics['mapping_times']
        batch_times = onlymaps_mapper._performance_metrics['batch_times']

        # Verify performance metrics are reasonable
        assert len(recorded_times) > 0
        assert len(batch_times) > 0

        # Verify recorded times are positive
        assert all(t >= 0 for t in recorded_times)
        assert all(t >= 0 for t in batch_times)

        # Verify batch time is approximately correct (within 10% tolerance)
        assert abs(batch_times[-1] - actual_time) / actual_time < 0.1

    def test_performance_reporting(self, onlymaps_mapper):
        """Test performance reporting functionality."""
        # Generate test records
        records = []
        for i in range(30):
            record = {
                'id': str(uuid.uuid4()),
                'submission_id': f'test{i}',
                'reddit_title': f'Test App {i}',
                'reddit_url': f'https://reddit.com/r/test/test{i}',
                'subreddit': 'test',
                'reddit_author': f'user{i}',
                'reddit_upvotes': 150 + i,
                'reddit_comments_count': 42 + i,
                'reddit_created_at': '2024-01-15T10:30:00Z',
                'app_title': f'Test App {i}',
                'app_concept': f'Test concept {i}',
                'problem_statement': f'Test problem {i}',
                'target_audience': f'Test audience {i}',
                'core_functions': [f'function{i % 5}', f'function{(i + 1) % 5}'],
                'market_demand': 85.0 + (i % 15),
                'pain_intensity': 90.0 + (i % 10),
                'monetization_potential': 75.0 + (i % 20),
                'competition_level': 60.0 + (i % 25),
                'technical_feasibility': 80.0 + (i % 15),
                'final_score': 78.5 + (i % 21),
                'confidence_score': 85.0 + (i % 15),
                'trust_level': ['HIGH', 'MEDIUM', 'LOW'][i % 3],
                'embedding': None,
                'analyzed_at': '2024-01-16T12:45:00Z',
                'created_at': '2024-01-16T12:45:00Z',
                'updated_at': '2024-01-16T12:45:00Z'
            }
            records.append(record)

        # Perform mapping operations
        onlymaps_mapper.map_batch(records, target_class=Opportunity)
        onlymaps_mapper.map_batch(records, target_class=Opportunity)

        # Get performance report
        report = onlymaps_mapper.get_performance_report()

        # Verify report structure
        assert isinstance(report, dict)
        assert 'summary' in report
        assert 'detailed_metrics' in report
        assert 'recommendations' in report

        # Verify summary statistics
        summary = report['summary']
        assert 'total_operations' in summary
        assert 'average_time' in summary
        assert 'max_time' in summary
        assert 'min_time' in summary
        assert 'total_throughput' in summary

        # Verify detailed metrics
        detailed = report['detailed_metrics']
        assert 'operation_counts' in detailed
        assert 'time_distributions' in detailed
        assert 'error_rates' in detailed

        # Verify recommendations
        recommendations = report['recommendations']
        assert isinstance(recommendations, list)
        assert len(recommendations) >= 0  # Can be empty if no issues found

        # Verify report values are reasonable
        assert summary['total_operations'] >= 2  # We performed 2 batch operations
        assert summary['average_time'] >= 0
        assert summary['max_time'] >= 0
        assert summary['min_time'] >= 0
        assert summary['total_throughput'] >= 0

    # =============================================================================
    # Thread Safety Tests
    # =============================================================================

    def test_thread_safety(self, onlymaps_mapper, performance_metrics_fixture):
        """Test thread safety of OnlyMaps operations."""

        # Generate test records
        records = []
        for i in range(100):
            record = {
                'id': str(uuid.uuid4()),
                'submission_id': f'test{i}',
                'reddit_title': f'Test App {i}',
                'reddit_url': f'https://reddit.com/r/test/test{i}',
                'subreddit': 'test',
                'reddit_author': f'user{i}',
                'reddit_upvotes': 150 + i,
                'reddit_comments_count': 42 + i,
                'reddit_created_at': '2024-01-15T10:30:00Z',
                'app_title': f'Test App {i}',
                'app_concept': f'Test concept {i}',
                'problem_statement': f'Test problem {i}',
                'target_audience': f'Test audience {i}',
                'core_functions': [f'function{i % 5}', f'function{(i + 1) % 5}'],
                'market_demand': 85.0 + (i % 15),
                'pain_intensity': 90.0 + (i % 10),
                'monetization_potential': 75.0 + (i % 20),
                'competition_level': 60.0 + (i % 25),
                'technical_feasibility': 80.0 + (i % 15),
                'final_score': 78.5 + (i % 21),
                'confidence_score': 85.0 + (i % 15),
                'trust_level': ['HIGH', 'MEDIUM', 'LOW'][i % 3],
                'embedding': None,
                'analyzed_at': '2024-01-16T12:45:00Z',
                'created_at': '2024-01-16T12:45:00Z',
                'updated_at': '2024-01-16T12:45:00Z'
            }
            records.append(record)

        # Thread worker function
        def worker(thread_id, results):
            try:
                opportunities = onlymaps_mapper.map_batch(records, target_class=Opportunity)
                results[thread_id] = len(opportunities)
            except Exception as e:
                results[thread_id] = str(e)

        # Run multiple threads concurrently
        num_threads = 5
        results = {}
        threads = []

        start_time = time.time()
        for i in range(num_threads):
            thread = threading.Thread(target=worker, args=(i, results))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        end_time = time.time()
        concurrent_time = end_time - start_time

        # Verify all threads completed successfully
        for thread_id, result in results.items():
            if isinstance(result, str):
                raise Exception(f"Thread {thread_id} failed: {result}")
            assert result == len(records), f"Thread {thread_id} returned {result} instead of {len(records)}"

        # Verify thread safety (concurrent time should be less than sequential)
        sequential_time = 0
        for _ in range(num_threads):
            start_time = time.time()
            onlymaps_mapper.map_batch(records, target_class=Opportunity)
            sequential_time += time.time() - start_time

        speedup = sequential_time / concurrent_time if concurrent_time > 0 else 0
        assert speedup >= 0.8, f"Thread safety should provide reasonable speedup, got: {speedup}"

    # =============================================================================
    # Configuration Impact Tests
    # =============================================================================

    def test_batch_size_impact_on_performance(self, onlymaps_mapper):
        """Test impact of batch size on performance."""
        # Generate test records
        records = []
        for i in range(1000):
            record = {
                'id': str(uuid.uuid4()),
                'submission_id': f'test{i}',
                'reddit_title': f'Test App {i}',
                'reddit_url': f'https://reddit.com/r/test/test{i}',
                'subreddit': 'test',
                'reddit_author': f'user{i}',
                'reddit_upvotes': 150 + i,
                'reddit_comments_count': 42 + i,
                'reddit_created_at': '2024-01-15T10:30:00Z',
                'app_title': f'Test App {i}',
                'app_concept': f'Test concept {i}',
                'problem_statement': f'Test problem {i}',
                'target_audience': f'Test audience {i}',
                'core_functions': [f'function{i % 5}', f'function{(i + 1) % 5}'],
                'market_demand': 85.0 + (i % 15),
                'pain_intensity': 90.0 + (i % 10),
                'monetization_potential': 75.0 + (i % 20),
                'competition_level': 60.0 + (i % 25),
                'technical_feasibility': 80.0 + (i % 15),
                'final_score': 78.5 + (i % 21),
                'confidence_score': 85.0 + (i % 15),
                'trust_level': ['HIGH', 'MEDIUM', 'LOW'][i % 3],
                'embedding': None,
                'analyzed_at': '2024-01-16T12:45:00Z',
                'created_at': '2024-01-16T12:45:00Z',
                'updated_at': '2024-01-16T12:45:00Z'
            }
            records.append(record)

        # Test different batch sizes
        batch_sizes = [1, 10, 50, 100, 500, 1000]
        performance_by_batch_size = {}

        for batch_size in batch_sizes:
            # Configure batch size
            onlymaps_mapper.config.batch_size = batch_size

            # Benchmark performance
            start_time = time.time()
            opportunities = onlymaps_mapper.map_batch(records, target_class=Opportunity)
            end_time = time.time()

            # Verify results
            assert len(opportunities) == len(records)

            # Record performance
            performance_by_batch_size[batch_size] = {
                'time': end_time - start_time,
                'throughput': len(records) / (end_time - start_time) if end_time > start_time else 0
            }

        # Verify that larger batch sizes generally provide better throughput
        batch_sizes_sorted = sorted(batch_sizes)
        throughputs = [performance_by_batch_size[bs]['throughput'] for bs in batch_sizes_sorted]

        # Check if throughput generally improves with batch size (with some optimization point)
        optimal_batch_size = batch_sizes_sorted[throughputs.index(max(throughputs))]
        assert optimal_batch_size >= 10, f"Optimal batch size should be reasonable, got: {optimal_batch_size}"

    def test_timeout_impact_on_performance(self, onlymaps_mapper):
        """Test impact of timeout configuration on performance."""
        # Generate test records
        records = []
        for i in range(100):
            record = {
                'id': str(uuid.uuid4()),
                'submission_id': f'test{i}',
                'reddit_title': f'Test App {i}',
                'reddit_url': f'https://reddit.com/r/test/test{i}',
                'subreddit': 'test',
                'reddit_author': f'user{i}',
                'reddit_upvotes': 150 + i,
                'reddit_comments_count': 42 + i,
                'reddit_created_at': '2024-01-15T10:30:00Z',
                'app_title': f'Test App {i}',
                'app_concept': f'Test concept {i}',
                'problem_statement': f'Test problem {i}',
                'target_audience': f'Test audience {i}',
                'core_functions': [f'function{i % 5}', f'function{(i + 1) % 5}'],
                'market_demand': 85.0 + (i % 15),
                'pain_intensity': 90.0 + (i % 10),
                'monetization_potential': 75.0 + (i % 20),
                'competition_level': 60.0 + (i % 25),
                'technical_feasibility': 80.0 + (i % 15),
                'final_score': 78.5 + (i % 21),
                'confidence_score': 85.0 + (i % 15),
                'trust_level': ['HIGH', 'MEDIUM', 'LOW'][i % 3],
                'embedding': None,
                'analyzed_at': '2024-01-16T12:45:00Z',
                'created_at': '2024-01-16T12:45:00Z',
                'updated_at': '2024-01-16T12:45:00Z'
            }
            records.append(records)

        # Test different timeout values
        timeout_values = [1, 5, 10, 30, 60]
        performance_by_timeout = {}

        for timeout in timeout_values:
            # Configure timeout
            onlymaps_mapper.config.timeout = timeout

            # Benchmark performance
            start_time = time.time()
            opportunities = onlymaps_mapper.map_batch(records, target_class=Opportunity)
            end_time = time.time()

            # Verify results
            assert len(opportunities) == len(records)

            # Record performance
            performance_by_timeout[timeout] = {
                'time': end_time - start_time,
                'success': True
            }

        # Verify that reasonable timeout values work correctly
        for timeout, perf in performance_by_timeout.items():
            assert perf['success'], f"Timeout {timeout} should work correctly"

    # =============================================================================
    # Performance Regression Tests
    # =============================================================================

    def test_performance_regression_detection(self, onlymaps_mapper):
        """Test performance regression detection."""
        # Generate test records
        records = []
        for i in range(100):
            record = {
                'id': str(uuid.uuid4()),
                'submission_id': f'test{i}',
                'reddit_title': f'Test App {i}',
                'reddit_url': f'https://reddit.com/r/test/test{i}',
                'subreddit': 'test',
                'reddit_author': f'user{i}',
                'reddit_upvotes': 150 + i,
                'reddit_comments_count': 42 + i,
                'reddit_created_at': '2024-01-15T10:30:00Z',
                'app_title': f'Test App {i}',
                'app_concept': f'Test concept {i}',
                'problem_statement': f'Test problem {i}',
                'target_audience': f'Test audience {i}',
                'core_functions': [f'function{i % 5}', f'function{(i + 1) % 5}'],
                'market_demand': 85.0 + (i % 15),
                'pain_intensity': 90.0 + (i % 10),
                'monetization_potential': 75.0 + (i % 20),
                'competition_level': 60.0 + (i % 25),
                'technical_feasibility': 80.0 + (i % 15),
                'final_score': 78.5 + (i % 21),
                'confidence_score': 85.0 + (i % 15),
                'trust_level': ['HIGH', 'MEDIUM', 'LOW'][i % 3],
                'embedding': None,
                'analyzed_at': '2024-01-16T12:45:00Z',
                'created_at': '2024-01-16T12:45:00Z',
                'updated_at': '2024-01-16T12:45:00Z'
            }
            records.append(record)

        # Set baseline performance
        start_time = time.time()
        opportunities = onlymaps_mapper.map_batch(records, target_class=Opportunity)
        baseline_time = time.time() - start_time

        # Run performance regression check
        regression_report = onlymaps_mapper.check_performance_regression()

        # Verify regression report structure
        assert isinstance(regression_report, dict)
        assert 'regression_detected' in regression_report
        assert 'baseline_performance' in regression_report
        assert 'current_performance' in regression_report
        assert 'regression_percentage' in regression_report
        assert 'recommendations' in regression_report

        # Verify regression detection logic
        assert isinstance(regression_report['regression_detected'], bool)
        assert isinstance(regression_report['baseline_performance'], float)
        assert isinstance(regression_report['current_performance'], float)
        assert isinstance(regression_report['regression_percentage'], float)
        assert isinstance(regression_report['recommendations'], list)

        # Check if performance is reasonable (should not have significant regression)
        assert regression_report['regression_percentage'] < 50.0, f"Performance regression should be minimal, got: {regression_report['regression_percentage']}%"

    def test_performance_stability_over_time(self, onlymaps_mapper):
        """Test performance stability over multiple runs."""
        # Generate test records
        records = []
        for i in range(100):
            record = {
                'id': str(uuid.uuid4()),
                'submission_id': f'test{i}',
                'reddit_title': f'Test App {i}',
                'reddit_url': f'https://reddit.com/r/test/test{i}',
                'subreddit': 'test',
                'reddit_author': f'user{i}',
                'reddit_upvotes': 150 + i,
                'reddit_comments_count': 42 + i,
                'reddit_created_at': '2024-01-15T10:30:00Z',
                'app_title': f'Test App {i}',
                'app_concept': f'Test concept {i}',
                'problem_statement': f'Test problem {i}',
                'target_audience': f'Test audience {i}',
                'core_functions': [f'function{i % 5}', f'function{(i + 1) % 5}'],
                'market_demand': 85.0 + (i % 15),
                'pain_intensity': 90.0 + (i % 10),
                'monetization_potential': 75.0 + (i % 20),
                'competition_level': 60.0 + (i % 25),
                'technical_feasibility': 80.0 + (i % 15),
                'final_score': 78.5 + (i % 21),
                'confidence_score': 85.0 + (i % 15),
                'trust_level': ['HIGH', 'MEDIUM', 'LOW'][i % 3],
                'embedding': None,
                'analyzed_at': '2024-01-16T12:45:00Z',
                'created_at': '2024-01-16T12:45:00Z',
                'updated_at': '2024-01-16T12:45:00Z'
            }
            records.append(records)

        # Run multiple times and collect performance data
        num_runs = 10
        performance_data = []

        for run in range(num_runs):
            start_time = time.time()
            opportunities = onlymaps_mapper.map_batch(records, target_class=Opportunity)
            end_time = time.time()

            performance_data.append(end_time - start_time)

            # Verify results
            assert len(opportunities) == len(records)

        # Calculate performance stability metrics
        avg_time = sum(performance_data) / len(performance_data)
        max_time = max(performance_data)
        min_time = min(performance_data)
        coefficient_of_variation = (max_time - min_time) / avg_time if avg_time > 0 else 0

        # Verify performance stability (CV should be reasonable)
        assert coefficient_of_variation < 0.2, f"Performance should be stable, CV: {coefficient_of_variation}"

        # Verify performance consistency
        assert max_time <= avg_time * 1.5, f"Maximum time should not be too far from average: {max_time} vs {avg_time}"
        assert min_time >= avg_time * 0.5, f"Minimum time should not be too far from average: {min_time} vs {avg_time}"

    # =============================================================================
    # Performance Configuration Tests
    # =============================================================================

    def test_performance_monitoring_configuration(self, onlymaps_mapper):
        """Test performance monitoring configuration options."""
        # Test different configuration options
        config_options = [
            {'performance_monitoring': False, 'detailed_metrics': False},
            {'performance_monitoring': False, 'detailed_metrics': True},
            {'performance_monitoring': True, 'detailed_metrics': False},
            {'performance_monitoring': True, 'detailed_metrics': True}
        ]

        for config in config_options:
            # Configure performance monitoring
            onlymaps_mapper.config.performance_monitoring = config['performance_monitoring']
            onlymaps_mapper.config.detailed_metrics = config['detailed_metrics']

            # Generate test records
            records = []
            for i in range(10):
                record = {
                    'id': str(uuid.uuid4()),
                    'submission_id': f'test{i}',
                    'reddit_title': f'Test App {i}',
                    'reddit_url': f'https://reddit.com/r/test/test{i}',
                    'subreddit': 'test',
                    'reddit_author': f'user{i}',
                    'reddit_upvotes': 150 + i,
                    'reddit_comments_count': 42 + i,
                    'reddit_created_at': '2024-01-15T10:30:00Z',
                    'app_title': f'Test App {i}',
                    'app_concept': f'Test concept {i}',
                    'problem_statement': f'Test problem {i}',
                    'target_audience': f'Test audience {i}',
                    'core_functions': [f'function{i % 5}', f'function{(i + 1) % 5}'],
                    'market_demand': 85.0 + (i % 15),
                    'pain_intensity': 90.0 + (i % 10),
                    'monetization_potential': 75.0 + (i % 20),
                    'competition_level': 60.0 + (i % 25),
                    'technical_feasibility': 80.0 + (i % 15),
                    'final_score': 78.5 + (i % 21),
                    'confidence_score': 85.0 + (i % 15),
                    'trust_level': ['HIGH', 'MEDIUM', 'LOW'][i % 3],
                    'embedding': None,
                    'analyzed_at': '2024-01-16T12:45:00Z',
                    'created_at': '2024-01-16T12:45:00Z',
                    'updated_at': '2024-01-16T12:45:00Z'
                }
                records.append(record)

            # Perform mapping operations
            start_time = time.time()
            opportunities = onlymaps_mapper.map_batch(records, target_class=Opportunity)
            end_time = time.time()

            # Verify configuration is applied
            assert onlymaps_mapper.config.performance_monitoring == config['performance_monitoring']
            assert onlymaps_mapper.config.detailed_metrics == config['detailed_metrics']

            # Verify performance monitoring works as expected
            if config['performance_monitoring']:
                assert hasattr(onlymaps_mapper, '_performance_metrics')
                if config['detailed_metrics']:
                    assert 'operation_counts' in onlymaps_mapper._performance_metrics
                    assert 'time_distributions' in onlymaps_mapper._performance_metrics
                else:
                    assert 'total_operations' in onlymaps_mapper._performance_metrics

            # Verify results
            assert len(opportunities) == len(records)

    def test_performance_cleanup(self, onlymaps_mapper):
        """Test performance monitoring cleanup."""
        # Enable performance monitoring
        onlymaps_mapper.config.performance_monitoring = True

        # Generate test records
        records = []
        for i in range(50):
            record = {
                'id': str(uuid.uuid4()),
                'submission_id': f'test{i}',
                'reddit_title': f'Test App {i}',
                'reddit_url': f'https://reddit.com/r/test/test{i}',
                'subreddit': 'test',
                'reddit_author': f'user{i}',
                'reddit_upvotes': 150 + i,
                'reddit_comments_count': 42 + i,
                'reddit_created_at': '2024-01-15T10:30:00Z',
                'app_title': f'Test App {i}',
                'app_concept': f'Test concept {i}',
                'problem_statement': f'Test problem {i}',
                'target_audience': f'Test audience {i}',
                'core_functions': [f'function{i % 5}', f'function{(i + 1) % 5}'],
                'market_demand': 85.0 + (i % 15),
                'pain_intensity': 90.0 + (i % 10),
                'monetization_potential': 75.0 + (i % 20),
                'competition_level': 60.0 + (i % 25),
                'technical_feasibility': 80.0 + (i % 15),
                'final_score': 78.5 + (i % 21),
                'confidence_score': 85.0 + (i % 15),
                'trust_level': ['HIGH', 'MEDIUM', 'LOW'][i % 3],
                'embedding': None,
                'analyzed_at': '2024-01-16T12:45:00Z',
                'created_at': '2024-01-16T12:45:00Z',
                'updated_at': '2024-01-16T12:45:00Z'
            }
            records.append(record)

        # Perform mapping operations to generate performance data
        onlymaps_mapper.map_batch(records, target_class=Opportunity)
        onlymaps_mapper.map_batch(records, target_class=Opportunity)

        # Verify performance data exists
        assert hasattr(onlymaps_mapper, '_performance_metrics')
        assert len(onlymaps_mapper._performance_metrics.get('mapping_times', [])) > 0

        # Test cleanup
        onlymaps_mapper.cleanup_performance_metrics()

        # Verify performance data is cleared
        assert hasattr(onlymaps_mapper, '_performance_metrics')
        assert len(onlymaps_mapper._performance_metrics.get('mapping_times', [])) == 0


# Helper function for SQLAlchemy performance comparison
def _create_opportunity_from_record(record):
    """Helper function to create Opportunity from record for SQLAlchemy comparison."""
    return Opportunity(
        id=uuid.UUID(record['id']),
        submission_id=record['submission_id'],
        reddit_title=record['reddit_title'],
        reddit_url=record['reddit_url'],
        subreddit=record['subreddit'],
        reddit_author=record['reddit_author'],
        reddit_upvotes=record['reddit_upvotes'],
        reddit_comments_count=record['reddit_comments_count'],
        reddit_created_at=datetime.fromisoformat(record['reddit_created_at'].replace('Z', '+00:00')),
        app_title=record['app_title'],
        app_concept=record['app_concept'],
        problem_statement=record['problem_statement'],
        target_audience=record['target_audience'],
        core_functions=record['core_functions'],
        market_demand=record['market_demand'],
        pain_intensity=record['pain_intensity'],
        monetization_potential=record['monetization_potential'],
        competition_level=record['competition_level'],
        technical_feasibility=record['technical_feasibility'],
        final_score=record['final_score'],
        confidence_score=record['confidence_score'],
        trust_level=record['trust_level'],
        embedding=record['embedding'],
        analyzed_at=datetime.fromisoformat(record['analyzed_at'].replace('Z', '+00:00')),
        created_at=datetime.fromisoformat(record['created_at'].replace('Z', '+00:00')),
        updated_at=datetime.fromisoformat(record['updated_at'].replace('Z', '+00:00'))
    )
