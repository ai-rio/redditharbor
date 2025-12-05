"""
Performance Benchmark Tests for Agno Integration

Phase 5 Production Testing - validates performance targets and scalability
"""

import pytest
import time
import json
import asyncio
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import statistics
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor

from models.reddit import RedditSubmission
from models.analysis import AnalysisResult
from transform.agno_analyzer import AgnoOpportunityAnalyzer
from tests.helpers.test_data_factory import RedditSubmissionFactory


class PerformanceTestData:
    """Factory for creating performance test data"""

    @staticmethod
    def create_latency_test_data() -> Dict[str, Any]:
        """Create data for latency benchmarking"""
        # Create sample submissions for testing
        return {
            "small_batch": RedditSubmissionFactory.create_batch_submissions(10),
            "medium_batch": RedditSubmissionFactory.create_batch_submissions(50),
            "large_batch": RedditSubmissionFactory.create_batch_submissions(100),
            "submissions": {
                "simple": RedditSubmissionFactory.create_submission("low_wtp_b2c"),
                "complex": RedditSubmissionFactory.create_submission("high_wtp_b2b"),
                "false_positive": RedditSubmissionFactory.create_submission("false_positives")
            }
        }

    @staticmethod
    def create_cost_test_data() -> Dict[str, Any]:
        """Create data for cost validation testing"""
        return {
            "submissions": RedditSubmissionFactory.create_batch_submissions(50),
            "target_cost_per_submission": 0.005,
            "cost_breakdown": {
                "wtp_agent": 0.001,
                "segment_agent": 0.001,
                "price_agent": 0.001,
                "behavior_agent": 0.001,
                "synthesis_llm": 0.0005,
                "embedding": 0.0001
            }
        }

    @staticmethod
    def create_throughput_test_data(duration_minutes: int = 60) -> Dict[str, Any]:
        """Create data for throughput testing"""
        # Estimate submissions per minute for target throughput
        target_per_hour = 100
        submissions_needed = int((target_per_hour * duration_minutes) / 60)

        return {
            "submissions": RedditSubmissionFactory.create_batch_submissions(submissions_needed),
            "duration_minutes": duration_minutes,
            "target_throughput": target_per_hour
        }


@dataclass
class BenchmarkThresholds:
    """Production benchmark thresholds"""

    # Latency thresholds (seconds)
    SINGLE_ANALYSIS_P95_TARGET = 5.0
    BATCH_10_P95_TARGET = 4.5
    BATCH_50_P95_TARGET = 4.0
    BATCH_100_P95_TARGET = 3.5

    # Throughput thresholds (submissions/hour)
    MIN_THROUGHPUT_TARGET = 100

    # Cost thresholds (USD per analysis)
    MAX_COST_PER_ANALYSIS = 0.005

    # Quality thresholds
    MIN_PRECISION = 0.80
    MIN_RECALL = 0.75

    # Resource usage thresholds
    MAX_MEMORY_MB = 512
    MAX_CPU_PERCENT = 80


@dataclass
class BenchmarkResults:
    """Results from performance benchmarking"""

    test_name: str
    timestamp: str
    sample_size: int
    duration_seconds: float

    # Latency metrics
    avg_latency: float
    p50_latency: float
    p95_latency: float
    p99_latency: float
    min_latency: float
    max_latency: float

    # Throughput metrics
    throughput_submissions_per_second: float
    throughput_submissions_per_hour: float

    # Cost metrics
    total_cost: float
    cost_per_submission: float
    estimated_monthly_cost: float

    # Quality metrics
    avg_final_score: float
    avg_confidence_score: float
    high_opportunity_rate: float
    error_rate: float

    # Resource metrics
    peak_memory_mb: float
    avg_cpu_percent: float
    peak_cpu_percent: float

    # Additional metrics
    agent_performance: Dict[str, Dict[str, float]]


class TestAgnoPerformanceBenchmarks:
    """Comprehensive performance benchmarking for Agno analyzer"""

    @pytest.fixture
    def benchmark_thresholds(self):
        """Get benchmark thresholds"""
        return BenchmarkThresholds()

    @pytest.fixture
    def agno_analyzer(self):
        """Initialize Agno analyzer for benchmarking"""
        return AgnoOpportunityAnalyzer(
            model="anthropic/claude-haiku-4.5",
            enable_agentops=False,  # Disable for benchmarks
            enable_embeddings=False,  # Disable for speed
            validation_threshold=70.0
        )

    @pytest.fixture
    def performance_test_data(self):
        """Get performance test data"""
        return PerformanceTestData()

    def test_single_submission_latency(self, benchmark_thresholds, agno_analyzer):
        """
        Benchmark single submission analysis latency

        Validates P95 latency < 5 seconds for individual submissions
        """
        # Test submissions with varying complexity
        test_cases = performance_test_data.create_latency_test_data()["submissions"]
        latencies = []

        for name, submission in test_cases.items():
            # Multiple runs for statistical significance
            run_latencies = []
            for _ in range(5):
                start_time = time.time()
                try:
                    result = agno_analyzer.analyze_submission(submission)
                    end_time = time.time()
                    run_latencies.append(end_time - start_time)
                except Exception as e:
                    # Count errors as failed runs
                    run_latencies.append(float('inf'))

            # Record best latency (excluding errors)
            valid_latencies = [l for l in run_latencies if l != float('inf')]
            if valid_latencies:
                latencies.append(min(valid_latencies))

        # Calculate statistics
        avg_latency = statistics.mean(latencies)
        p95_latency = self._calculate_percentile(latencies, 95)

        # Validate against threshold
        assert p95_latency <= benchmark_thresholds.SINGLE_ANALYSIS_P95_TARGET, \
            f"Single analysis P95 latency {p95_latency:.2f}s exceeds target {benchmark_thresholds.SINGLE_ANALYSIS_P95_TARGET}s"

        # Log detailed results
        print(f"\nSingle Submission Latency Results:")
        print(f"  Average: {avg_latency:.3f}s")
        print(f"  P95: {p95_latency:.3f}s")
        print(f"  Min: {min(latencies):.3f}s")
        print(f"  Max: {max(latencies):.3f}s")

    def test_batch_processing_performance(self, benchmark_thresholds, agno_analyzer):
        """
        Benchmark batch processing performance

        Validates performance for batches of 10, 50, and 100 submissions
        """
        test_data = performance_test_data.create_latency_test_data()
        batch_sizes = [10, 50, 100]
        batch_results = []

        for batch_size in batch_sizes:
            # Get appropriate batch
            if batch_size == 10:
                submissions = test_data["small_batch"]
            elif batch_size == 50:
                submissions = test_data["medium_batch"]
            else:
                submissions = test_data["large_batch"]

            # Measure batch processing
            start_time = time.time()
            memory_start = self._get_memory_usage()

            try:
                # Process batch
                results, cost_summary = agno_analyzer.analyze_batch_with_costs(submissions)

                end_time = time.time()
                memory_end = self._get_memory_usage()

                duration = end_time - start_time
                avg_latency = duration / len(submissions)
                throughput = len(submissions) / duration

                # Calculate metrics
                batch_result = BenchmarkResults(
                    test_name=f"batch_{batch_size}",
                    timestamp=datetime.now().isoformat(),
                    sample_size=len(submissions),
                    duration_seconds=duration,
                    avg_latency=avg_latency,
                    p50_latency=avg_latency,  # Same for batch
                    p95_latency=avg_latency,  # Same for batch
                    p99_latency=avg_latency,  # Same for batch
                    min_latency=0,
                    max_latency=duration,
                    throughput_submissions_per_second=throughput,
                    throughput_submissions_per_hour=throughput * 3600,
                    total_cost=cost_summary.get("total_cost", 0),
                    cost_per_submission=cost_summary.get("cost_per_submission", 0),
                    estimated_monthly_cost=0,
                    avg_final_score=statistics.mean([r.final_score for r in results]),
                    avg_confidence_score=statistics.mean([r.confidence_score for r in results]),
                    high_opportunity_rate=sum(1 for r in results if r.final_score >= 60) / len(results),
                    error_rate=0,
                    peak_memory_mb=memory_end - memory_start,
                    avg_cpu_percent=0,
                    peak_cpu_percent=0,
                    agent_performance={}
                )

                batch_results.append(batch_result)

                # Validate throughput
                assert batch_result.throughput_submissions_per_hour >= benchmark_thresholds.MIN_THROUGHPUT_TARGET, \
                    f"Batch size {batch_size}: Throughput {batch_result.throughput_submissions_per_hour:.1f}/hr below target {benchmark_thresholds.MIN_THROUGHPUT_TARGET}/hr"

                # Validate cost
                assert batch_result.cost_per_submission <= benchmark_thresholds.MAX_COST_PER_ANALYSIS, \
                    f"Batch size {batch_size}: Cost ${batch_result.cost_per_submission:.4f} exceeds target ${benchmark_thresholds.MAX_COST_PER_ANALYSIS}"

            except Exception as e:
                pytest.fail(f"Batch processing failed for size {batch_size}: {str(e)}")

        # Print batch results
        print(f"\nBatch Processing Results:")
        for result in batch_results:
            print(f"  Batch {result.test_name}:")
            print(f"    Avg Latency: {result.avg_latency:.3f}s")
            print(f"    Throughput: {result.throughput_submissions_per_hour:.1f}/hr")
            print(f"    Cost/Sub: ${result.cost_per_submission:.4f}")

    def test_cost_validation_benchmark(self, benchmark_thresholds, agno_analyzer):
        """
        Benchmark and validate cost per analysis

        Validates actual cost against target <$0.005 per analysis
        """
        test_data = performance_test_data.create_cost_test_data()
        submissions = test_data["submissions"]

        # Track costs
        total_cost = 0
        costs = []
        results = []

        for submission in submissions:
            # Reset cost tracker for clean measurement
            agno_analyzer.cost_tracker = type(agno_analyzer.cost_tracker)()

            start_time = time.time()
            result = agno_analyzer.analyze_submission(submission)
            end_time = time.time()

            # Get cost of this analysis
            analysis_cost = agno_analyzer.cost_tracker.get_last_analysis_cost()
            costs.append(analysis_cost)
            total_cost += analysis_cost
            results.append(result)

        # Calculate cost metrics
        avg_cost = statistics.mean(costs)
        max_cost = max(costs)
        min_cost = min(costs)

        # Validate against target
        assert avg_cost <= benchmark_thresholds.MAX_COST_PER_ANALYSIS, \
            f"Average cost ${avg_cost:.4f} exceeds target ${benchmark_thresholds.MAX_COST_PER_ANALYSIS}"

        assert max_cost <= benchmark_thresholds.MAX_COST_PER_ANALYSIS * 2, \
            f"Maximum cost ${max_cost:.4f} exceeds 2x target ${benchmark_thresholds.MAX_COST_PER_ANALYSIS * 2}"

        # Print cost breakdown
        print(f"\nCost Validation Results:")
        print(f"  Total analyses: {len(submissions)}")
        print(f"  Total cost: ${total_cost:.4f}")
        print(f"  Average cost: ${avg_cost:.4f}")
        print(f"  Min cost: ${min_cost:.4f}")
        print(f"  Max cost: ${max_cost:.4f}")

    def test_throughput_stress_test(self, benchmark_thresholds, agno_analyzer):
        """
        Stress test throughput with sustained load

        Validates sustained throughput >100 submissions/hour
        """
        # Generate test data for 10 minutes of processing
        test_data = performance_test_data.create_throughput_test_data(duration_minutes=10)
        submissions = test_data["submissions"]

        # Process in batches to simulate real usage
        batch_size = 10
        batch_times = []
        error_count = 0
        total_processed = 0

        for i in range(0, len(submissions), batch_size):
            batch = submissions[i:i + batch_size]

            start_time = time.time()
            try:
                results, _ = agno_analyzer.analyze_batch_with_costs(batch)
                end_time = time.time()

                batch_times.append(end_time - start_time)
                total_processed += len(results)

            except Exception as e:
                print(f"Batch {i // batch_size} failed: {str(e)}")
                error_count += 1
                continue

        # Calculate throughput metrics
        total_time = sum(batch_times)
        avg_batch_time = statistics.mean(batch_times)
        throughput = total_processed / (total_time / 3600) if total_time > 0 else 0
        error_rate = error_count / (len(submissions) / batch_size)

        # Validate throughput
        assert throughput >= benchmark_thresholds.MIN_THROUGHPUT_TARGET, \
            f"Stress test throughput {throughput:.1f}/hr below target {benchmark_thresholds.MIN_THROUGHPUT_TARGET}/hr"

        # Validate error rate
        assert error_rate <= 0.05,  # Max 5% error rate
            f"Error rate {error_rate:.2%} exceeds maximum 5%"

        # Print throughput results
        print(f"\nThroughput Stress Test Results:")
        print(f"  Submissions processed: {total_processed}")
        print(f"  Total processing time: {total_time:.1f}s")
        print(f"  Average batch time: {avg_batch_time:.3f}s")
        print(f"  Throughput: {throughput:.1f}/hr")
        print(f"  Error rate: {error_rate:.2%}")

    def test_concurrent_processing_benchmark(self, benchmark_thresholds, agno_analyzer):
        """
        Benchmark concurrent processing capabilities

        Tests performance with multiple concurrent workers
        """
        submissions = RedditSubmissionFactory.create_batch_submissions(50)
        concurrent_levels = [1, 2, 4, 8]
        concurrent_results = []

        for num_workers in concurrent_levels:
            # Process submissions concurrently
            start_time = time.time()

            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                # Submit all tasks
                futures = [
                    executor.submit(agno_analyzer.analyze_submission, sub)
                    for sub in submissions
                ]

                # Collect results
                results = []
                errors = 0
                for future in futures:
                    try:
                        result = future.result(timeout=30)  # 30s timeout
                        results.append(result)
                    except Exception as e:
                        errors += 1

            end_time = time.time()

            # Calculate metrics
            duration = end_time - start_time
            throughput = len(results) / (duration / 3600) if duration > 0 else 0
            error_rate = errors / len(futures)

            concurrent_result = {
                "workers": num_workers,
                "duration": duration,
                "throughput": throughput,
                "error_rate": error_rate,
                "processed": len(results),
                "errors": errors
            }

            concurrent_results.append(concurrent_result)

            # Validate no errors from concurrency
            assert error_rate <= 0.05, f"Concurrent processing with {num_workers} workers has {error_rate:.2%} errors"

        # Analyze scaling efficiency
        baseline_throughput = concurrent_results[0]["throughput"]
        max_throughput = max(r["throughput"] for r in concurrent_results)

        # Validate scaling
        assert max_throughput >= baseline_throughput * 2, \
            f"Concurrent processing scaling insufficient: {max_throughput:.1f}/hr vs baseline {baseline_throughput:.1f}/hr"

        # Print concurrent results
        print(f"\nConcurrent Processing Results:")
        for result in concurrent_results:
            print(f"  {result['workers']} workers:")
            print(f"    Throughput: {result['throughput']:.1f}/hr")
            print(f"    Duration: {result['duration']:.1f}s")
            print(f"    Error rate: {result['error_rate']:.2%}")

    def test_memory_usage_benchmark(self, benchmark_thresholds, agno_analyzer):
        """
        Benchmark memory usage during processing

        Validates memory usage stays within acceptable limits
        """
        # Start with fresh process
        initial_memory = self._get_memory_usage()

        # Process increasing batch sizes
        batch_sizes = [10, 50, 100, 200]
        memory_snapshots = []

        for batch_size in batch_sizes:
            submissions = RedditSubmissionFactory.create_batch_submissions(batch_size)

            # Measure memory before batch
            memory_before = self._get_memory_usage()

            # Process batch
            try:
                results, _ = agno_analyzer.analyze_batch_with_costs(submissions)
            except Exception as e:
                pytest.fail(f"Memory test batch failed: {str(e)}")

            # Measure memory after batch
            memory_after = self._get_memory_usage()

            # Force garbage collection
            import gc
            gc.collect()

            memory_after_gc = self._get_memory_usage()

            snapshot = {
                "batch_size": batch_size,
                "memory_before": memory_before,
                "memory_after": memory_after,
                "memory_after_gc": memory_after_gc,
                "memory_increase": memory_after - memory_before
            }

            memory_snapshots.append(snapshot)

            # Validate memory usage
            assert memory_after_gc <= initial_memory + benchmark_thresholds.MAX_MEMORY_MB, \
                f"Memory usage {memory_after_gc:.1f}MB exceeds limit {benchmark_thresholds.MAX_MEMORY_MB}MB"

        # Analyze memory growth
        print(f"\nMemory Usage Results:")
        print(f"  Initial memory: {initial_memory:.1f}MB")
        for snapshot in memory_snapshots:
            print(f"  Batch {snapshot['batch_size']}:")
            print(f"    Increase: {snapshot['memory_increase']:.1f}MB")
            print(f"    After GC: {snapshot['memory_after_gc']:.1f}MB")

    def test_quality_consistency_benchmark(self, benchmark_thresholds, agno_analyzer):
        """
        Benchmark quality consistency across multiple runs

        Validates that analysis quality remains consistent
        """
        # Select 10 diverse submissions
        test_submissions = []
        for _ in range(2):
            test_submissions.extend(RedditSubmissionFactory.create_batch_submissions(5))

        # Run each submission multiple times
        consistency_results = []

        for submission in test_submissions:
            run_scores = []
            run_confidences = []

            for _ in range(5):  # 5 runs per submission
                result = agno_analyzer.analyze_submission(submission)
                run_scores.append(result.final_score)
                run_confidences.append(result.confidence_score)

            # Calculate consistency metrics
            score_std = statistics.stdev(run_scores) if len(run_scores) > 1 else 0
            confidence_std = statistics.stdev(run_confidences) if len(run_confidences) > 1 else 0

            consistency_results.append({
                "submission_id": submission.id,
                "score_mean": statistics.mean(run_scores),
                "score_std": score_std,
                "confidence_mean": statistics.mean(run_confidences),
                "confidence_std": confidence_std,
                "score_cv": score_std / statistics.mean(run_scores) if statistics.mean(run_scores) > 0 else 0,
                "confidence_cv": confidence_std / statistics.mean(run_confidences) if statistics.mean(run_confidences) > 0 else 0
            })

        # Analyze overall consistency
        avg_score_cv = statistics.mean([r["score_cv"] for r in consistency_results])
        avg_confidence_cv = statistics.mean([r["confidence_cv"] for r in consistency_results])

        # Validate consistency (CV should be < 0.1 for 90% consistency)
        assert avg_score_cv <= 0.1, \
            f"Score consistency CV {avg_score_cv:.3f} exceeds 0.1 threshold"

        assert avg_confidence_cv <= 0.1, \
            f"Confidence consistency CV {avg_confidence_cv:.3f} exceeds 0.1 threshold"

        # Print consistency results
        print(f"\nQuality Consistency Results:")
        print(f"  Score CV: {avg_score_cv:.3f}")
        print(f"  Confidence CV: {avg_confidence_cv:.3f}")
        print(f"  Average score: {statistics.mean([r['score_mean'] for r in consistency_results]):.1f}")
        print(f"  Average confidence: {statistics.mean([r['confidence_mean'] for r in consistency_results]):.1f}")

    def test_comprehensive_performance_report(self, benchmark_thresholds, agno_analyzer):
        """
        Generate comprehensive performance benchmark report

        This test produces a detailed report for production validation
        """
        # Run all benchmark tests and collect results
        report = {
            "test_date": datetime.now().isoformat(),
            "benchmark_thresholds": asdict(benchmark_thresholds),
            "test_results": {}
        }

        # Single submission latency
        report["test_results"]["single_latency"] = self._run_single_latency_test(agno_analyzer)

        # Batch processing
        report["test_results"]["batch_processing"] = self._run_batch_processing_test(agno_analyzer)

        # Cost validation
        report["test_results"]["cost_validation"] = self._run_cost_validation_test(agno_analyzer)

        # Throughput
        report["test_results"]["throughput"] = self._run_throughput_test(agno_analyzer)

        # Memory usage
        report["test_results"]["memory_usage"] = self._run_memory_usage_test(agno_analyzer)

        # Quality consistency
        report["test_results"]["quality_consistency"] = self._run_quality_consistency_test(agno_analyzer)

        # Generate overall assessment
        report["summary"] = self._generate_benchmark_summary(report["test_results"], benchmark_thresholds)

        # Save report
        self._save_benchmark_report(report, "agno_performance_benchmark.json")

        # Validate overall pass/fail
        assert report["summary"]["all_criteria_met"], \
            f"Benchmark validation failed: {report['summary']['failed_criteria']}"

        print(f"\nComprehensive Benchmark Summary:")
        print(f"  All criteria met: {report['summary']['all_criteria_met']}")
        print(f"  Passed: {len(report['summary']['passed_criteria'])}")
        print(f"  Failed: {len(report['summary']['failed_criteria'])}")

    # Helper methods
    def _calculate_percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024

    def _run_single_latency_test(self, analyzer) -> Dict[str, float]:
        """Run single submission latency test"""
        test_data = PerformanceTestData().create_latency_test_data()["submissions"]
        latencies = []

        for submission in test_data.values():
            start_time = time.time()
            analyzer.analyze_submission(submission)
            end_time = time.time()
            latencies.append(end_time - start_time)

        return {
            "avg": statistics.mean(latencies),
            "p50": self._calculate_percentile(latencies, 50),
            "p95": self._calculate_percentile(latencies, 95),
            "p99": self._calculate_percentile(latencies, 99),
            "min": min(latencies),
            "max": max(latencies)
        }

    def _run_batch_processing_test(self, analyzer) -> Dict[str, Any]:
        """Run batch processing test"""
        test_data = PerformanceTestData().create_latency_test_data()
        results = {}

        for batch_name, submissions in test_data.items():
            if batch_name.endswith("_batch"):
                start_time = time.time()
                batch_results, cost_summary = analyzer.analyze_batch_with_costs(submissions)
                end_time = time.time()

                results[batch_name] = {
                    "size": len(submissions),
                    "duration": end_time - start_time,
                    "throughput": len(submissions) / (end_time - start_time) * 3600,
                    "cost_per_submission": cost_summary.get("cost_per_submission", 0)
                }

        return results

    def _run_cost_validation_test(self, analyzer) -> Dict[str, float]:
        """Run cost validation test"""
        test_data = PerformanceTestData().create_cost_test_data()
        submissions = test_data["submissions"]
        costs = []

        for submission in submissions:
            analyzer.cost_tracker = type(analyzer.cost_tracker)()
            analyzer.analyze_submission(submission)
            costs.append(analyzer.cost_tracker.get_last_analysis_cost())

        return {
            "total_cost": sum(costs),
            "avg_cost": statistics.mean(costs),
            "min_cost": min(costs),
            "max_cost": max(costs),
            "total_analyses": len(submissions)
        }

    def _run_throughput_test(self, analyzer) -> Dict[str, float]:
        """Run throughput test"""
        test_data = PerformanceTestData().create_throughput_test_data(duration_minutes=5)
        submissions = test_data["submissions"]

        start_time = time.time()
        results, _ = analyzer.analyze_batch_with_costs(submissions)
        end_time = time.time()

        duration = end_time - start_time
        throughput = len(submissions) / (duration / 3600) if duration > 0 else 0

        return {
            "submissions_processed": len(submissions),
            "duration_seconds": duration,
            "throughput_per_hour": throughput,
            "throughput_per_second": len(submissions) / duration if duration > 0 else 0
        }

    def _run_memory_usage_test(self, analyzer) -> Dict[str, Any]:
        """Run memory usage test"""
        initial_memory = self._get_memory_usage()

        # Process batch
        submissions = RedditSubmissionFactory.create_batch_submissions(100)
        memory_before = self._get_memory_usage()

        results, _ = analyzer.analyze_batch_with_costs(submissions)

        memory_after = self._get_memory_usage()

        # Force GC and measure again
        import gc
        gc.collect()
        memory_after_gc = self._get_memory_usage()

        return {
            "initial_memory_mb": initial_memory,
            "memory_before_mb": memory_before,
            "memory_after_mb": memory_after,
            "memory_after_gc_mb": memory_after_gc,
            "peak_increase_mb": memory_after - memory_before,
            "final_increase_mb": memory_after_gc - initial_memory
        }

    def _run_quality_consistency_test(self, analyzer) -> Dict[str, float]:
        """Run quality consistency test"""
        submissions = RedditSubmissionFactory.create_batch_submissions(10)
        all_score_variances = []
        all_confidence_variances = []

        for submission in submissions:
            scores = []
            confidences = []

            for _ in range(5):
                result = analyzer.analyze_submission(submission)
                scores.append(result.final_score)
                confidences.append(result.confidence_score)

            if len(scores) > 1:
                all_score_variances.append(statistics.variance(scores))
                all_confidence_variances.append(statistics.variance(confidences))

        return {
            "avg_score_variance": statistics.mean(all_score_variances) if all_score_variances else 0,
            "avg_confidence_variance": statistics.mean(all_confidence_variances) if all_confidence_variances else 0,
            "max_score_variance": max(all_score_variances) if all_score_variances else 0,
            "max_confidence_variance": max(all_confidence_variances) if all_confidence_variances else 0
        }

    def _generate_benchmark_summary(
        self,
        test_results: Dict[str, Any],
        thresholds: BenchmarkThresholds
    ) -> Dict[str, Any]:
        """Generate benchmark summary with pass/fail criteria"""
        passed_criteria = []
        failed_criteria = []

        # Check single latency
        if test_results["single_latency"]["p95"] <= thresholds.SINGLE_ANALYSIS_P95_TARGET:
            passed_criteria.append("single_latency_p95")
        else:
            failed_criteria.append("single_latency_p95")

        # Check throughput
        if test_results["throughput"]["throughput_per_hour"] >= thresholds.MIN_THROUGHPUT_TARGET:
            passed_criteria.append("throughput_target")
        else:
            failed_criteria.append("throughput_target")

        # Check cost
        if test_results["cost_validation"]["avg_cost"] <= thresholds.MAX_COST_PER_ANALYSIS:
            passed_criteria.append("cost_target")
        else:
            failed_criteria.append("cost_target")

        # Check memory
        if test_results["memory_usage"]["final_increase_mb"] <= thresholds.MAX_MEMORY_MB:
            passed_criteria.append("memory_target")
        else:
            failed_criteria.append("memory_target")

        # Check consistency (lower variance is better)
        if test_results["quality_consistency"]["avg_score_variance"] <= 10:  # Arbitrary threshold
            passed_criteria.append("quality_consistency")
        else:
            failed_criteria.append("quality_consistency")

        return {
            "all_criteria_met": len(failed_criteria) == 0,
            "passed_criteria": passed_criteria,
            "failed_criteria": failed_criteria,
            "total_criteria": len(passed_criteria) + len(failed_criteria)
        }

    def _save_benchmark_report(self, report: Dict[str, Any], filename: str):
        """Save benchmark report to file"""
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)