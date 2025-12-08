"""
Performance test configuration for AgnoOpportunityAnalyzer
"""

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import psutil
import pytest

from tests.helpers.assertion_helpers import AgnoAnalysisAssertions
from tests.helpers.mock_agno_agents import MockAgnoTeam
from tests.helpers.test_data_factory import RedditSubmissionFactory


@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    start_time: float
    end_time: float
    cpu_percent: float
    memory_mb: float
    execution_time: float
    throughput: float
    success_count: int
    error_count: int


class PerformanceTestHelpers:
    """Helper functions for performance testing"""

    @staticmethod
    def start_performance_monitoring(duration_seconds: int = 10):
        """Start performance monitoring in background thread"""
        metrics = {
            'cpu_samples': [],
            'memory_samples': [],
            'timestamps': []
        }

        def monitor():
            start_time = time.time()
            while time.time() - start_time < duration_seconds:
                cpu = psutil.cpu_percent(interval=0.1)
                memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

                metrics['cpu_samples'].append(cpu)
                metrics['memory_samples'].append(memory)
                metrics['timestamps'].append(time.time())
                time.sleep(0.5)

        thread = threading.Thread(target=monitor)
        thread.start()

        return metrics, thread

    @staticmethod
    def measure_throughput(test_func, *args, **kwargs):
        """Measure throughput of test function"""
        start_time = time.time()
        results = []

        for result in test_func(*args, **kwargs):
            results.append(result)

        end_time = time.time()
        execution_time = end_time - start_time
        throughput = len(results) / execution_time if execution_time > 0 else 0

        return {
            'results': results,
            'execution_time': execution_time,
            'throughput': throughput,
            'total_processed': len(results)
        }


@pytest.fixture(scope="session")
def performance_test_loop():
    """Run tests in a loop for performance testing"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def performance_monitor():
    """Monitor performance during test execution"""
    def start_monitoring():
        return PerformanceMetrics(
            start_time=time.time(),
            end_time=0,
            cpu_percent=0,
            memory_mb=0,
            execution_time=0,
            throughput=0,
            success_count=0,
            error_count=0
        )
    return start_monitoring


@pytest.fixture
def batch_sizes():
    """Different batch sizes for testing"""
    return [1, 10, 50, 100]


@pytest.fixture
def concurrent_levels():
    """Different concurrency levels"""
    return [1, 2, 4, 8]


@pytest.fixture
def large_test_dataset():
    """Large dataset for performance testing"""
    return {
        'submissions': RedditSubmissionFactory.create_batch_submissions(1000),
        'expected_performance': {
            'min_throughput': 10,  # submissions per second
            'max_memory_mb': 100,
            'max_cpu_percent': 80
        }
    }


@pytest.fixture
def edge_case_submissions():
    """Submissions that test edge cases"""
    return [
        RedditSubmissionFactory.create_empty_submission(),
        RedditSubmissionFactory.create_max_length_submission(),
        RedditSubmissionFactory.create_special_chars_submission(),
        RedditSubmissionFactory.create_unicode_submission(),
        RedditSubmissionFactory.create_json_payload_submission()
    ]


@pytest.fixture
def rate_limit_scenarios():
    """Different rate limiting scenarios"""
    return [
        {'requests_per_second': 1, 'duration': 10},
        {'requests_per_second': 10, 'duration': 10},
        {'requests_per_second': 100, 'duration': 10}
    ]


@pytest.fixture
def mock_agno_team_performance():
    """Mock Agno team optimized for performance testing"""
    return MockAgnoTeam()


@pytest.fixture
def performance_test_helpers():
    """Helper functions for performance testing"""
    return PerformanceTestHelpers()
