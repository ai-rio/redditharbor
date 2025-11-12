#!/usr/bin/env python3
"""
Simple test runner for performance benchmark components.
This script validates that the performance benchmarking system works correctly.
"""

import sys
import os
import traceback

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test that all required modules can be imported"""
    try:
        import performance_benchmark
        print("✅ performance_benchmark module imported successfully")

        # Test key classes and functions
        assert hasattr(performance_benchmark, 'PerformanceBenchmark')
        assert hasattr(performance_benchmark, 'BenchmarkMetrics')
        assert hasattr(performance_benchmark, 'run_benchmark')
        assert hasattr(performance_benchmark, 'main')
        print("✅ All required classes and functions are available")

        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        traceback.print_exc()
        return False

def test_benchmark_initialization():
    """Test PerformanceBenchmark class initialization"""
    try:
        from performance_benchmark import PerformanceBenchmark

        benchmark = PerformanceBenchmark()
        assert benchmark.results == {}
        assert benchmark.process is not None
        assert 'subreddit_activity' in benchmark.mock_data
        assert 'content_quality' in benchmark.mock_data
        print("✅ PerformanceBenchmark initialization successful")

        return True
    except Exception as e:
        print(f"❌ Benchmark initialization test failed: {e}")
        traceback.print_exc()
        return False

def test_benchmark_metrics():
    """Test BenchmarkMetrics dataclass"""
    try:
        from performance_benchmark import BenchmarkMetrics

        metrics = BenchmarkMetrics()
        assert metrics.api_calls == 0
        assert metrics.processing_time == 0.0
        assert metrics.memory_usage == 0.0
        assert metrics.items_collected == 0
        assert metrics.quality_score == 0.0
        assert metrics.active_subreddits == 0
        assert metrics.validation_time == 0.0
        print("✅ BenchmarkMetrics dataclass working correctly")

        return True
    except Exception as e:
        print(f"❌ BenchmarkMetrics test failed: {e}")
        traceback.print_exc()
        return False

def test_activity_level_assignment():
    """Test consistent activity level assignment"""
    try:
        from performance_benchmark import PerformanceBenchmark

        benchmark = PerformanceBenchmark()

        # Test consistency
        activity1 = benchmark._get_subreddit_activity_level("test_subreddit_1")
        activity2 = benchmark._get_subreddit_activity_level("test_subreddit_1")
        assert activity1 == activity2, "Activity level should be consistent"

        # Test valid activity levels
        activity3 = benchmark._get_subreddit_activity_level("different_subreddit")
        assert activity3 in ['high_activity', 'medium_activity', 'low_activity']
        print("✅ Activity level assignment working correctly")

        return True
    except Exception as e:
        print(f"❌ Activity level assignment test failed: {e}")
        traceback.print_exc()
        return False

def test_timer_functionality():
    """Test timing and memory measurement"""
    try:
        from performance_benchmark import PerformanceBenchmark
        import time

        benchmark = PerformanceBenchmark()

        benchmark.start_timer("test_operation")
        time.sleep(0.01)  # Small delay
        benchmark.end_timer("test_operation")

        assert "test_operation_duration" in benchmark.results
        assert benchmark.results["test_operation_duration"] > 0.005
        assert "test_operation_memory_delta" in benchmark.results
        print("✅ Timer functionality working correctly")

        return True
    except Exception as e:
        print(f"❌ Timer functionality test failed: {e}")
        traceback.print_exc()
        return False

def test_traditional_simulation():
    """Test traditional collection simulation"""
    try:
        from performance_benchmark import PerformanceBenchmark

        benchmark = PerformanceBenchmark()
        test_subreddits = [f"test_sub_{i}" for i in range(3)]

        metrics = benchmark.simulate_traditional_collection(test_subreddits)

        assert metrics.api_calls > 0
        assert metrics.processing_time > 0
        assert metrics.items_collected > 0
        assert metrics.quality_score > 0
        assert metrics.quality_score <= 1.0
        assert metrics.active_subreddits == len(test_subreddits)
        print(f"✅ Traditional simulation: {metrics.api_calls} calls, {metrics.items_collected} items")

        return True
    except Exception as e:
        print(f"❌ Traditional simulation test failed: {e}")
        traceback.print_exc()
        return False

def test_dlt_simulation():
    """Test DLT collection simulation"""
    try:
        from performance_benchmark import PerformanceBenchmark

        benchmark = PerformanceBenchmark()
        test_subreddits = [f"test_sub_{i}" for i in range(3)]

        metrics = benchmark.simulate_dlt_collection(test_subreddits)

        assert metrics.api_calls > 0
        assert metrics.processing_time > 0
        assert metrics.validation_time > 0
        assert metrics.items_collected > 0
        assert metrics.quality_score > 0
        assert metrics.quality_score <= 1.0
        assert metrics.active_subreddits <= len(test_subreddits)
        print(f"✅ DLT simulation: {metrics.api_calls} calls, {metrics.items_collected} items, {metrics.active_subreddits} active")

        return True
    except Exception as e:
        print(f"❌ DLT simulation test failed: {e}")
        traceback.print_exc()
        return False

def test_improvement_calculations():
    """Test performance improvement calculations"""
    try:
        from performance_benchmark import PerformanceBenchmark, BenchmarkMetrics

        benchmark = PerformanceBenchmark()

        traditional = BenchmarkMetrics(
            api_calls=1000,
            processing_time=100.0,
            items_collected=100,
            quality_score=0.5
        )

        dlt = BenchmarkMetrics(
            api_calls=400,
            processing_time=70.0,
            items_collected=80,
            quality_score=0.85
        )

        improvements = benchmark.calculate_improvements(traditional, dlt)

        assert 'api_call_reduction' in improvements
        assert 'time_improvement' in improvements
        assert 'quality_improvement' in improvements
        assert improvements['api_call_reduction'] == pytest.approx(60.0, rel=1e-1)
        print("✅ Improvement calculations working correctly")

        return True
    except Exception as e:
        print(f"❌ Improvement calculations test failed: {e}")
        traceback.print_exc()
        return False

def test_full_benchmark():
    """Test complete benchmark run"""
    try:
        from performance_benchmark import run_benchmark

        report = run_benchmark(subreddit_count=5, save_report=False)

        assert isinstance(report, dict)
        assert 'test_date' in report
        assert 'test_configuration' in report
        assert 'traditional_metrics' in report
        assert 'dlt_metrics' in report
        assert 'improvements' in report
        assert report['test_configuration']['subreddit_count'] == 5
        print("✅ Full benchmark run successful")

        # Print key results
        trad = report['traditional_metrics']
        dlt = report['dlt_metrics']
        print(f"   Traditional: {trad['api_calls']} calls, quality={trad['quality_score']:.2f}")
        print(f"   DLT: {dlt['api_calls']} calls, quality={dlt['quality_score']:.2f}")
        print(f"   API reduction: {report['improvements']['api_call_reduction']:.1f}%")
        print(f"   Quality improvement: {report['improvements']['quality_improvement']:.1f}%")

        return True
    except Exception as e:
        print(f"❌ Full benchmark test failed: {e}")
        traceback.print_exc()
        return False

def test_report_structure():
    """Test that performance report has expected structure"""
    try:
        report_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'reports', 'dlt-performance-report.md')

        with open(report_path, 'r') as f:
            content = f.read()

        required_sections = [
            "Executive Summary",
            "Performance Benchmark Methodology",
            "Detailed Performance Analysis",
            "Business Impact Assessment",
            "Production Deployment Recommendations",
            "Conclusion"
        ]

        for section in required_sections:
            assert section in content, f"Missing section: {section}"

        required_findings = [
            "API Call Reduction",
            "Data Quality Enhancement",
            "Processing Efficiency",
            "IMMEDIATE IMPLEMENTATION"
        ]

        for finding in required_findings:
            assert finding in content, f"Missing finding: {finding}"

        print("✅ Performance report structure validated")
        return True
    except Exception as e:
        print(f"❌ Report structure test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Running Performance Benchmark Tests")
    print("=" * 50)

    tests = [
        ("Module Imports", test_imports),
        ("Benchmark Initialization", test_benchmark_initialization),
        ("BenchmarkMetrics Dataclass", test_benchmark_metrics),
        ("Activity Level Assignment", test_activity_level_assignment),
        ("Timer Functionality", test_timer_functionality),
        ("Traditional Simulation", test_traditional_simulation),
        ("DLT Simulation", test_dlt_simulation),
        ("Improvement Calculations", test_improvement_calculations),
        ("Full Benchmark Run", test_full_benchmark),
        ("Report Structure", test_report_structure)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Performance benchmarking system is ready.")
        return True
    else:
        print("⚠️ Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)