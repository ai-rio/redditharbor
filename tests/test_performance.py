"""
Performance Benchmark Tests

Tests for the DLT performance benchmarking system and components.
"""

import pytest
import os
import sys
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add scripts to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

def test_performance_benchmark_script_exists():
    """Test that performance benchmark script exists and is importable"""
    script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'performance_benchmark.py')
    assert os.path.exists(script_path), "Performance benchmark script missing"

    # Test import works
    try:
        import performance_benchmark
        assert hasattr(performance_benchmark, 'PerformanceBenchmark')
        assert hasattr(performance_benchmark, 'run_benchmark')
        assert hasattr(performance_benchmark, 'main')
    except ImportError as e:
        pytest.fail(f"Failed to import performance benchmark: {e}")

def test_performance_report_exists():
    """Test that performance report file exists"""
    report_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'reports', 'dlt-performance-report.md')
    assert os.path.exists(report_path), "Performance report missing"

def test_performance_benchmark_class():
    """Test PerformanceBenchmark class functionality"""
    from performance_benchmark import PerformanceBenchmark, BenchmarkMetrics

    benchmark = PerformanceBenchmark()

    # Test initialization
    assert benchmark.results == {}
    assert benchmark.process is not None
    assert 'subreddit_activity' in benchmark.mock_data
    assert 'content_quality' in benchmark.mock_data

def test_benchmark_metrics_dataclass():
    """Test BenchmarkMetrics dataclass"""
    from performance_benchmark import BenchmarkMetrics

    # Test default values
    metrics = BenchmarkMetrics()
    assert metrics.api_calls == 0
    assert metrics.processing_time == 0.0
    assert metrics.memory_usage == 0.0
    assert metrics.items_collected == 0
    assert metrics.quality_score == 0.0
    assert metrics.active_subreddits == 0
    assert metrics.validation_time == 0.0

def test_timer_functionality():
    """Test timing and memory measurement functionality"""
    from performance_benchmark import PerformanceBenchmark
    import time

    benchmark = PerformanceBenchmark()

    # Test timer start/end
    benchmark.start_timer("test_operation")
    time.sleep(0.01)  # Small delay
    benchmark.end_timer("test_operation")

    assert "test_operation_duration" in benchmark.results
    assert benchmark.results["test_operation_duration"] > 0.005  # Should be at least 5ms
    assert "test_operation_memory_delta" in benchmark.results

def test_activity_level_assignment():
    """Test consistent activity level assignment"""
    from performance_benchmark import PerformanceBenchmark

    benchmark = PerformanceBenchmark()

    # Test activity level assignment is consistent
    activity1 = benchmark._get_subreddit_activity_level("test_subreddit_1")
    activity2 = benchmark._get_subreddit_activity_level("test_subreddit_1")  # Same name
    assert activity1 == activity2, "Activity level should be consistent for same subreddit"

    # Test different subreddits can have different activity levels
    activity3 = benchmark._get_subreddit_activity_level("different_subreddit")
    # This might be same or different, both are valid
    assert activity3 in ['high_activity', 'medium_activity', 'low_activity']

def test_activity_score_calculation():
    """Test activity score calculation algorithm"""
    from performance_benchmark import PerformanceBenchmark

    benchmark = PerformanceBenchmark()

    # Test with high activity metrics
    high_activity_data = {
        'avg_score': (100, 200),
        'subscribers': (100000, 500000)
    }

    score = benchmark._calculate_activity_score(
        comments=500,
        posts=100,
        activity_data=high_activity_data
    )

    assert isinstance(score, (int, float))
    assert score > 0
    assert score <= 200  # Should be reasonable bounds

def test_traditional_collection_simulation():
    """Test traditional collection simulation"""
    from performance_benchmark import PerformanceBenchmark

    benchmark = PerformanceBenchmark()
    test_subreddits = [f"test_sub_{i}" for i in range(5)]

    metrics = benchmark.simulate_traditional_collection(test_subreddits)

    # Validate metrics
    assert metrics.api_calls > 0
    assert metrics.processing_time > 0
    assert metrics.items_collected > 0
    assert metrics.quality_score > 0
    assert metrics.quality_score <= 1.0
    assert metrics.active_subreddits == len(test_subreddits)  # Traditional treats all as active

def test_dlt_collection_simulation():
    """Test DLT collection simulation"""
    from performance_benchmark import PerformanceBenchmark

    benchmark = PerformanceBenchmark()
    test_subreddits = [f"test_sub_{i}" for i in range(5)]

    metrics = benchmark.simulate_dlt_collection(test_subreddits)

    # Validate metrics
    assert metrics.api_calls > 0
    assert metrics.processing_time > 0
    assert metrics.validation_time > 0
    assert metrics.items_collected > 0
    assert metrics.quality_score > 0
    assert metrics.quality_score <= 1.0
    assert metrics.active_subreddits <= len(test_subreddits)  # DLT filters inactive

def test_improvement_calculations():
    """Test performance improvement calculations"""
    from performance_benchmark import PerformanceBenchmark, BenchmarkMetrics

    benchmark = PerformanceBenchmark()

    # Create test metrics
    traditional = BenchmarkMetrics(
        api_calls=1000,
        processing_time=100.0,
        memory_usage=50.0,
        items_collected=100,
        quality_score=0.5
    )

    dlt = BenchmarkMetrics(
        api_calls=400,  # 60% reduction
        processing_time=70.0,  # 30% improvement
        memory_usage=40.0,  # 20% improvement
        items_collected=80,  # Slightly fewer but higher quality
        quality_score=0.85  # 70% improvement
    )

    improvements = benchmark.calculate_improvements(traditional, dlt)

    # Validate calculations
    assert 'api_call_reduction' in improvements
    assert 'time_improvement' in improvements
    assert 'quality_improvement' in improvements
    assert 'memory_efficiency' in improvements
    assert 'efficiency_improvement' in improvements

    assert improvements['api_call_reduction'] == pytest.approx(60.0, rel=1e-1)
    assert improvements['time_improvement'] == pytest.approx(30.0, rel=1e-1)
    assert improvements['quality_improvement'] == pytest.approx(70.0, rel=1e-1)

def test_report_generation():
    """Test comprehensive report generation"""
    from performance_benchmark import PerformanceBenchmark, BenchmarkMetrics

    benchmark = PerformanceBenchmark()
    subreddit_count = 10

    # Create test metrics
    traditional = BenchmarkMetrics(
        api_calls=2400,
        processing_time=10.0,
        memory_usage=25.0,
        items_collected=240,
        quality_score=0.5,
        active_subreddits=10
    )

    dlt = BenchmarkMetrics(
        api_calls=960,
        processing_time=7.0,
        memory_usage=20.0,
        items_collected=192,
        quality_score=0.85,
        active_subreddits=6,
        validation_time=1.0
    )

    improvements = {
        'api_call_reduction': 60.0,
        'time_improvement': 30.0,
        'quality_improvement': 70.0,
        'memory_efficiency': 20.0,
        'efficiency_improvement': 60.0
    }

    report = benchmark.generate_report(traditional, dlt, subreddit_count, improvements)

    # Validate report structure
    assert 'test_date' in report
    assert 'test_configuration' in report
    assert 'traditional_metrics' in report
    assert 'dlt_metrics' in report
    assert 'improvements' in report
    assert 'executive_summary' in report

    # Validate specific values
    assert report['test_configuration']['subreddit_count'] == subreddit_count
    assert report['traditional_metrics']['api_calls'] == traditional.api_calls
    assert report['dlt_metrics']['api_calls'] == dlt.api_calls
    assert 'IMPLEMENT' in report['executive_summary']['dlt_recommendation']

def test_run_benchmark_function():
    """Test the main benchmark runner function"""
    from performance_benchmark import run_benchmark

    # Test with small subreddit count for faster testing
    report = run_benchmark(subreddit_count=5, save_report=False)

    # Validate report structure
    assert isinstance(report, dict)
    assert 'test_date' in report
    assert 'test_configuration' in report
    assert 'traditional_metrics' in report
    assert 'dlt_metrics' in report
    assert 'improvements' in report

    # Validate benchmark ran correctly
    assert report['test_configuration']['subreddit_count'] == 5
    assert report['traditional_metrics']['api_calls'] > 0
    assert report['dlt_metrics']['api_calls'] > 0

@patch('sys.argv', ['performance_benchmark.py', '--subreddits', '5'])
def test_main_function_small_scale():
    """Test main function with small scale parameters"""
    from performance_benchmark import main

    # Mock sys.argv for testing
    with patch('sys.argv', ['performance_benchmark.py', '--subreddits', '5']):
        try:
            report = main()
            assert isinstance(report, dict)
            assert report['test_configuration']['subreddit_count'] == 5
        except SystemExit as e:
            # main() might call sys.exit(), which is expected
            assert e.code == 0

@patch('sys.argv', ['performance_benchmark.py', '--small'])
def test_main_function_small_flag():
    """Test main function with --small flag"""
    from performance_benchmark import main

    with patch('sys.argv', ['performance_benchmark.py', '--small']):
        try:
            report = main()
            assert isinstance(report, dict)
            assert report['test_configuration']['subreddit_count'] == 10
        except SystemExit as e:
            assert e.code == 0

@patch('sys.argv', ['performance_benchmark.py', '--medium'])
def test_main_function_medium_flag():
    """Test main function with --medium flag"""
    from performance_benchmark import main

    with patch('sys.argv', ['performance_benchmark.py', '--medium']):
        try:
            report = main()
            assert isinstance(report, dict)
            assert report['test_configuration']['subreddit_count'] == 50
        except SystemExit as e:
            assert e.code == 0

def test_mock_data_structure():
    """Test mock data structure for realistic simulation"""
    from performance_benchmark import PerformanceBenchmark

    benchmark = PerformanceBenchmark()
    mock_data = benchmark.mock_data

    # Validate structure
    assert 'subreddit_activity' in mock_data
    assert 'content_quality' in mock_data

    # Validate activity levels
    activity_levels = ['high_activity', 'medium_activity', 'low_activity']
    for level in activity_levels:
        assert level in mock_data['subreddit_activity']
        activity_data = mock_data['subreddit_activity'][level]
        assert 'comments_per_day' in activity_data
        assert 'posts_per_day' in activity_data
        assert 'avg_score' in activity_data
        assert 'subscribers' in activity_data

    # Validate quality distributions
    for method in ['traditional', 'dlt_validated']:
        assert method in mock_data['content_quality']
        quality_dist = mock_data['content_quality'][method]
        assert 'high_quality' in quality_dist
        assert 'medium_quality' in quality_dist
        assert 'low_quality' in quality_dist

        # Validate probabilities sum to 1
        total = quality_dist['high_quality'] + quality_dist['medium_quality'] + quality_dist['low_quality']
        assert abs(total - 1.0) < 0.01  # Allow small floating point error

def test_activity_metrics_simulation():
    """Test activity metrics simulation functionality"""
    from performance_benchmark import PerformanceBenchmark

    benchmark = PerformanceBenchmark()

    # Test different activity levels
    for activity_level in ['high_activity', 'medium_activity', 'low_activity']:
        activity_data = benchmark.mock_data['subreddit_activity'][activity_level]
        comments, posts = benchmark._simulate_activity_metrics(activity_data)

        # Validate ranges
        min_comments, max_comments = activity_data['comments_per_day']
        min_posts, max_posts = activity_data['posts_per_day']

        assert min_comments <= comments <= max_comments
        assert min_posts <= posts <= max_posts

def test_report_file_creation():
    """Test that report files are created correctly"""
    from performance_benchmark import run_benchmark
    import tempfile
    import shutil

    # Create temporary directory for test
    temp_dir = tempfile.mkdtemp()
    original_reports_dir = "docs/reports"

    try:
        # Mock the reports directory to temp directory
        with patch('os.makedirs') as mock_makedirs:
            with patch('builtins.open', create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file

                # Run benchmark with save enabled
                report = run_benchmark(subreddit_count=3, save_report=True)

                # Verify makedirs was called
                mock_makedirs.assert_called_once_with(original_reports_dir, exist_ok=True)

                # Verify file was opened for writing
                mock_open.assert_called_once()

                # Verify json.dump was called (indirectly through file operations)
                assert isinstance(report, dict)

    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_performance_report_content():
    """Test that the generated performance report has expected content"""
    report_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'reports', 'dlt-performance-report.md')

    with open(report_path, 'r') as f:
        content = f.read()

    # Check for key sections
    assert "Executive Summary" in content
    assert "Performance Benchmark Methodology" in content
    assert "Detailed Performance Analysis" in content
    assert "Business Impact Assessment" in content
    assert "Production Deployment Recommendations" in content
    assert "Conclusion" in content

    # Check for key metrics and findings
    assert "API Call Reduction" in content
    assert "Data Quality Enhancement" in content
    assert "Processing Efficiency" in content
    assert "IMMEDIATE IMPLEMENTATION" in content

    # Check for specific numbers and percentages
    assert "40-60%" in content
    assert "42-85%" in content
    assert "22-35%" in content

if __name__ == "__main__":
    pytest.main([__file__, "-v"])