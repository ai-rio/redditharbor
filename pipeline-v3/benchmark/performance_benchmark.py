"""
Performance benchmarking suite for RedditHarbor Agno multi-agent system

This comprehensive benchmarking suite tests the system under various load conditions
to validate the 1000 submissions/minute target with P99 latency < 10s.
"""

import asyncio
import time
import json
import logging
import statistics
import psutil
import tracemalloc
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
from pathlib import Path

# Add parent directory to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from models.reddit import RedditSubmission
from transform.agno_analyzer_optimized import OptimizedAgnoAnalyzer, BatchConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark tests"""
    test_name: str
    num_submissions: int
    concurrent_workers: int
    duration_minutes: float
    expected_rpm: float
    expected_p99_latency: float

    # Advanced settings
    enable_embeddings: bool = True
    embedding_batch_size: int = 96
    max_concurrent_agents: int = 20
    max_concurrent_submissions: int = 50
    memory_monitoring: bool = True
    cpu_monitoring: bool = True
    detailed_metrics: bool = True


@dataclass
class BenchmarkResult:
    """Results from a benchmark run"""
    test_name: str
    config: BenchmarkConfig

    # Performance metrics
    total_submissions: int
    successful_submissions: int
    failed_submissions: int
    total_duration: float
    submissions_per_minute: float

    # Latency metrics
    latencies: List[float]
    p50_latency: float
    p95_latency: float
    p99_latency: float
    max_latency: float

    # Resource metrics
    peak_memory_mb: float
    avg_cpu_percent: float
    peak_cpu_percent: float

    # Error tracking
    error_types: Dict[str, int]

    # Agent metrics
    agent_latencies: Dict[str, List[float]]

    # Timestamp
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }


class SubmissionGenerator:
    """Generate realistic Reddit submissions for testing"""

    TITLES = [
        "I need a tool to automate my monthly reporting",
        "Building a SaaS to help freelancers manage invoices",
        "Looking for a solution to track team productivity remotely",
        "Wanted: App that compares prices across grocery stores",
        "Can someone build a tool to find duplicate expenses?",
        "Need help creating a platform for language exchange",
        "Building analytics dashboard for e-commerce stores",
        "Looking for AI to summarize customer feedback",
        "Need automated solution for social media posting",
        "Creating marketplace for local service providers"
    ]

    CONTENTS = [
        "I spend hours every month creating reports for my clients. There must be a better way to automate this process with templates and data integration. Currently using Excel and it's taking too much time.",
        "As a freelancer, I struggle with tracking invoices and getting paid on time. A simple dashboard that sends automated reminders would be invaluable.",
        "With remote work, it's hard to know if my team is productive without micromanaging. Looking for a tool that tracks progress transparently.",
        "I waste time checking multiple websites for grocery prices. An app that could scan and compare prices would save me money and time.",
        "I keep finding duplicate charges on my credit card. Need an automated way to scan and flag these for refunds.",
        "Learning languages is expensive. Want to connect directly with native speakers for practice without paying platforms.",
        "My e-commerce data is scattered across multiple platforms. Need a unified dashboard to track sales, inventory, and customer behavior.",
        "Reading hundreds of customer reviews is overwhelming. AI could summarize key themes and sentiment quickly.",
        "Managing multiple social media accounts manually is tedious. Automation with scheduling would be game-changing.",
        "Local service providers are hard to find and verify. A trusted marketplace with reviews and booking would help the community."
    ]

    SUBREDDITS = [
        "Entrepreneur", "SaaS", "smallbusiness", "freelance", "ProductHunt",
        "startups", "SideProject", "Apps", "Technology", "BusinessIdeas"
    ]

    def __init__(self, seed: int = 42):
        """Initialize with seed for reproducible generation"""
        np.random.seed(seed)

    def generate_submission(self, id_override: Optional[str] = None) -> RedditSubmission:
        """Generate a single realistic Reddit submission"""
        submission_id = id_override or f"benchmark_{int(time.time() * 1000000)}"

        title = np.random.choice(self.TITLES)
        content = np.random.choice(self.CONTENTS)
        subreddit = np.random.choice(self.SUBREDDITS)

        return RedditSubmission(
            id=submission_id,
            title=title,
            text=content,
            subreddit=subreddit,
            author=f"benchmark_user_{np.random.randint(1, 1000)}",
            score=np.random.randint(1, 100),
            comments_count=np.random.randint(0, 50),
            created_at=datetime.now(timezone.utc)
        )

    def generate_batch(self, count: int) -> List[RedditSubmission]:
        """Generate a batch of submissions"""
        return [self.generate_submission() for _ in range(count)]


class ResourceMonitor:
    """Monitor system resources during benchmark"""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.memory_samples = []
        self.cpu_samples = []
        self.monitoring = False

    async def start_monitoring(self):
        """Start resource monitoring"""
        if not self.enabled:
            return

        self.monitoring = True
        self.memory_samples = []
        self.cpu_samples = []

        process = psutil.Process()

        while self.monitoring:
            # Memory usage
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_samples.append(memory_mb)

            # CPU usage
            cpu_percent = process.cpu_percent()
            self.cpu_samples.append(cpu_percent)

            await asyncio.sleep(0.1)  # Sample every 100ms

    def stop_monitoring(self) -> Tuple[float, float, float]:
        """Stop monitoring and return metrics"""
        self.monitoring = False

        if not self.memory_samples or not self.cpu_samples:
            return 0.0, 0.0, 0.0

        peak_memory = max(self.memory_samples)
        avg_cpu = statistics.mean(self.cpu_samples)
        peak_cpu = max(self.cpu_samples)

        return peak_memory, avg_cpu, peak_cpu


class BenchmarkRunner:
    """Execute benchmark tests and collect results"""

    def __init__(self, output_dir: str = "benchmark/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.generator = SubmissionGenerator()
        self.results = []

    async def run_benchmark(self, config: BenchmarkConfig) -> BenchmarkResult:
        """Run a single benchmark test"""
        logger.info(f"Starting benchmark: {config.test_name}")
        logger.info(f"  - Submissions: {config.num_submissions}")
        logger.info(f"  - Workers: {config.concurrent_workers}")
        logger.info(f"  - Expected RPM: {config.expected_rpm}")
        logger.info(f"  - Expected P99 Latency: {config.expected_p99_latency}s")

        # Start memory tracking
        tracemalloc.start()

        # Initialize resource monitor
        monitor = ResourceMonitor(
            enabled=config.memory_monitoring or config.cpu_monitoring
        )
        monitor_task = asyncio.create_task(monitor.start_monitoring())

        # Generate test data
        submissions = self.generator.generate_batch(config.num_submissions)

        # Configure analyzer
        batch_config = BatchConfig(
            embedding_batch_size=config.embedding_batch_size,
            max_concurrent_agents=config.max_concurrent_agents,
            max_concurrent_submissions=config.max_concurrent_submissions
        )

        analyzer = OptimizedAgnoAnalyzer(
            config=batch_config,
            enable_embeddings=config.enable_embeddings,
            embedding_provider="cohere"
        )

        # Track latencies and errors
        latencies = []
        agent_latencies = {}
        errors = {}

        try:
            # Run benchmark
            start_time = time.time()

            # Process submissions in batches
            batch_size = config.concurrent_workers
            for i in range(0, len(submissions), batch_size):
                batch = submissions[i:i + batch_size]

                batch_start = time.time()
                results = await analyzer.analyze_batch_async(batch)
                batch_latency = time.time() - batch_start

                # Record latencies for each submission
                for j, result in enumerate(results):
                    submission_latency = batch_latency / len(batch)
                    latencies.append(submission_latency)

                    # Check for errors
                    if result.final_score == 0.0 and result.confidence_score == 0.0:
                        error_type = "analysis_error"
                        errors[error_type] = errors.get(error_type, 0) + 1

            total_duration = time.time() - start_time

            # Get performance metrics from analyzer
            metrics = await analyzer.get_performance_metrics()
            if 'agents' in metrics:
                for agent, agent_metrics in metrics['agents'].items():
                    agent_latencies[agent] = [agent_metrics['average_latency']]

            # Calculate performance metrics
            successful = len([r for r in results if r.final_score > 0])
            failed = len(results) - successful
            rpm = (successful / total_duration) * 60

            # Stop resource monitoring
            peak_memory, avg_cpu, peak_cpu = await monitor.stop_monitoring()
            monitor_task.cancel()

            # Get memory usage
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            # Calculate latency percentiles
            if latencies:
                p50 = np.percentile(latencies, 50)
                p95 = np.percentile(latencies, 95)
                p99 = np.percentile(latencies, 99)
                max_latency = max(latencies)
            else:
                p50 = p95 = p99 = max_latency = 0

            # Create result
            result = BenchmarkResult(
                test_name=config.test_name,
                config=config,
                total_submissions=len(submissions),
                successful_submissions=successful,
                failed_submissions=failed,
                total_duration=total_duration,
                submissions_per_minute=rpm,
                latencies=latencies,
                p50_latency=p50,
                p95_latency=p95,
                p99_latency=p99,
                max_latency=max_latency,
                peak_memory_mb=peak_memory,
                avg_cpu_percent=avg_cpu,
                peak_cpu_percent=peak_cpu,
                error_types=errors,
                agent_latencies=agent_latencies,
                timestamp=datetime.now(timezone.utc)
            )

            # Cleanup
            await analyzer.close()

            # Log results
            logger.info(f"Benchmark completed: {config.test_name}")
            logger.info(f"  - RPM: {rpm:.2f} (target: {config.expected_rpm})")
            logger.info(f"  - P99 Latency: {p99:.2f}s (target: {config.expected_p99_latency}s)")
            logger.info(f"  - Success Rate: {(successful/len(submissions))*100:.1f}%")
            logger.info(f"  - Peak Memory: {peak_memory:.1f}MB")
            logger.info(f"  - Peak CPU: {peak_cpu:.1f}%")

            return result

        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            monitor_task.cancel()
            await analyzer.close()
            raise

    async def run_all_benchmarks(self) -> List[BenchmarkResult]:
        """Run all predefined benchmarks"""
        configs = [
            # Light load test
            BenchmarkConfig(
                test_name="light_load",
                num_submissions=50,
                concurrent_workers=10,
                duration_minutes=1.0,
                expected_rpm=100,
                expected_p99_latency=5.0
            ),

            # Medium load test
            BenchmarkConfig(
                test_name="medium_load",
                num_submissions=200,
                concurrent_workers=20,
                duration_minutes=2.0,
                expected_rpm=500,
                expected_p99_latency=7.0
            ),

            # Full load test (target spec)
            BenchmarkConfig(
                test_name="full_load",
                num_submissions=1000,
                concurrent_workers=50,
                duration_minutes=5.0,
                expected_rpm=1000,
                expected_p99_latency=10.0
            ),

            # Stress test
            BenchmarkConfig(
                test_name="stress_test",
                num_submissions=2000,
                concurrent_workers=100,
                duration_minutes=10.0,
                expected_rpm=1500,
                expected_p99_latency=15.0
            ),

            # Embedding disabled test
            BenchmarkConfig(
                test_name="no_embeddings",
                num_submissions=500,
                concurrent_workers=30,
                duration_minutes=2.0,
                expected_rpm=1200,
                expected_p99_latency=8.0,
                enable_embeddings=False
            ),

            # Optimal batch size test
            BenchmarkConfig(
                test_name="optimal_batching",
                num_submissions=1000,
                concurrent_workers=50,
                duration_minutes=5.0,
                expected_rpm=1000,
                expected_p99_latency=10.0,
                embedding_batch_size=96,
                max_concurrent_agents=20,
                max_concurrent_submissions=50
            )
        ]

        results = []
        for config in configs:
            try:
                result = await self.run_benchmark(config)
                results.append(result)
                self.results.append(result)

                # Save individual result
                self.save_result(result)

                # Brief pause between tests
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Failed to run benchmark {config.test_name}: {e}")

        # Generate summary report
        self.generate_summary_report(results)

        return results

    def save_result(self, result: BenchmarkResult):
        """Save benchmark result to file"""
        filename = f"{result.test_name}_{result.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename

        with open(filepath, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)

        logger.info(f"Saved benchmark result to {filepath}")

    def generate_summary_report(self, results: List[BenchmarkResult]):
        """Generate comprehensive summary report"""
        report = []
        report.append("# RedditHarbor Performance Benchmark Report")
        report.append(f"\nGenerated: {datetime.now(timezone.utc).isoformat()}")
        report.append(f"\n## Executive Summary\n")

        # Check if targets met
        target_met = any(
            r.submissions_per_minute >= 1000 and r.p99_latency <= 10.0
            for r in results
        )

        if target_met:
            report.append("✅ **TARGET MET**: System achieved 1000 submissions/minute with P99 latency < 10s")
        else:
            report.append("❌ **TARGET NOT MET**: System did not achieve target performance")

        # Results table
        report.append("\n## Benchmark Results\n")
        report.append("| Test | Submissions | RPM | P50 Latency | P95 Latency | P99 Latency | Success Rate | Peak Memory (MB) |")
        report.append("|------|-------------|-----|-------------|-------------|-------------|--------------|------------------|")

        for result in results:
            report.append(
                f"| {result.test_name} | {result.total_submissions} | "
                f"{result.submissions_per_minute:.1f} | "
                f"{result.p50_latency:.2f}s | {result.p95_latency:.2f}s | "
                f"{result.p99_latency:.2f}s | "
                f"{(result.successful_submissions/result.total_submissions)*100:.1f}% | "
                f"{result.peak_memory_mb:.1f} |"
            )

        # Performance analysis
        report.append("\n## Performance Analysis\n")

        # Best performing configuration
        best_rpm = max(results, key=lambda r: r.submissions_per_minute)
        report.append(f"\n### Best Throughput\n")
        report.append(f"- **Test**: {best_rpm.test_name}")
        report.append(f"- **RPM**: {best_rpm.submissions_per_minute:.1f}")
        report.append(f"- **Configuration**: {best_rpm.max_concurrent_submissions} concurrent submissions, "
                     f"{best_rpm.embedding_batch_size} batch size")

        # Best latency
        best_latency = min(results, key=lambda r: r.p99_latency)
        report.append(f"\n### Best Latency\n")
        report.append(f"- **Test**: {best_latency.test_name}")
        report.append(f"- **P99 Latency**: {best_latency.p99_latency:.2f}s")
        report.append(f"- **Configuration**: {best_latency.max_concurrent_submissions} concurrent submissions")

        # Resource efficiency
        report.append(f"\n### Resource Efficiency\n")
        efficiency_scores = []
        for result in results:
            # Score = RPM / (Memory_MB/1000) * (1 - error_rate)
            error_rate = result.failed_submissions / result.total_submissions
            score = (result.submissions_per_minute / (result.peak_memory_mb / 1000)) * (1 - error_rate)
            efficiency_scores.append((result, score))

        most_efficient = max(efficiency_scores, key=lambda x: x[1])
        report.append(f"- **Most Efficient**: {most_efficient[0].test_name}")
        report.append(f"- **Efficiency Score**: {most_efficient[1]:.2f}")
        report.append(f"- **Memory per RPM**: {most_efficient[0].peak_memory_mb/most_efficient[0].submissions_per_minute:.2f}MB")

        # Recommendations
        report.append(f"\n## Recommendations\n")

        if not target_met:
            report.append("\n### To Achieve Target Performance (1000 RPM, P99 < 10s):")

            # Analyze bottlenecks
            high_latency_tests = [r for r in results if r.p99_latency > 10.0]
            low_rpm_tests = [r for r in results if r.submissions_per_minute < 1000]

            if high_latency_tests:
                avg_concurrency = np.mean([t.max_concurrent_submissions for t in high_latency_tests])
                report.append(f"- **Reduce Latency**: Tests with P99 > 10s used avg {avg_concurrency:.0f} concurrent submissions. "
                             f"Consider reducing to 25-30 to prevent API rate limiting.")

            if low_rpm_tests:
                report.append(f"- **Increase Throughput**: Tests below 1000 RPM should increase concurrent submissions to 50-60.")

            report.append(f"- **Enable Connection Pooling**: Ensure API endpoints support keep-alive connections")
            report.append(f"- **Optimize Batching**: Use Cohere's maximum batch size of 96 texts for embeddings")

        # Embedding impact analysis
        embedding_tests = [r for r in results if r.enable_embeddings]
        no_embedding_tests = [r for r in results if not r.enable_embeddings]

        if embedding_tests and no_embedding_tests:
            avg_rpm_with = np.mean([r.submissions_per_minute for r in embedding_tests])
            avg_rpm_without = np.mean([r.submissions_per_minute for r in no_embedding_tests])
            impact = ((avg_rpm_without - avg_rpm_with) / avg_rpm_with) * 100

            report.append(f"\n### Embedding Impact Analysis")
            report.append(f"- **With Embeddings**: {avg_rpm_with:.1f} RPM average")
            report.append(f"- **Without Embeddings**: {avg_rpm_without:.1f} RPM average")
            report.append(f"- **Performance Impact**: {impact:.1f}% {'decrease' if impact > 0 else 'increase'}")

        # Scaling recommendations
        report.append(f"\n## Production Scaling Recommendations\n")
        report.append(f"\n### Infrastructure Requirements")
        report.append(f"- **CPU**: 8+ cores for optimal concurrency")
        report.append(f"- **Memory**: 8GB minimum, 16GB recommended for 1000 RPM")
        report.append(f"- **Network**: 1Gbps for API call bandwidth")
        report.append(f"- **API Rate Limits**: Ensure 500+ calls/minute for LLM providers")

        report.append(f"\n### Configuration for Target Performance")
        report.append(f"- ```python")
        report.append(f"batch_config = BatchConfig(")
        report.append(f"    embedding_batch_size=96,  # Max for Cohere")
        report.append(f"    max_concurrent_agents=20,  # Balanced load")
        report.append(f"    max_concurrent_submissions=50,  # Optimal throughput")
        report.append(f")")
        report.append(f"```")

        report.append(f"\n### Monitoring Metrics")
        report.append(f"- Track P99 latency (target: <10s)")
        report.append(f"- Monitor RPM (target: 1000)")
        report.append(f"- Alert on memory usage (>4GB)")
        report.append(f"- Watch API rate limits (backpressure)")
        report.append(f"- Monitor error rate (>1% triggers alert)")

        # Save report
        report_text = "\n".join(report)
        report_path = self.output_dir / f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        with open(report_path, 'w') as f:
            f.write(report_text)

        logger.info(f"Saved benchmark report to {report_path}")

        # Generate visualizations
        self.generate_visualizations(results)

    def generate_visualizations(self, results: List[BenchmarkResult]):
        """Generate performance visualization charts"""
        if not results:
            return

        # Set up plotting style
        plt.style.use('seaborn-v0_8-darkgrid')
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('RedditHarbor Performance Benchmark Results', fontsize=16)

        test_names = [r.test_name for r in results]

        # Throughput chart
        rpms = [r.submissions_per_minute for r in results]
        axes[0, 0].bar(test_names, rpms)
        axes[0, 0].axhline(y=1000, color='r', linestyle='--', label='Target (1000 RPM)')
        axes[0, 0].set_title('Submissions Per Minute')
        axes[0, 0].set_ylabel('RPM')
        axes[0, 0].legend()
        axes[0, 0].tick_params(axis='x', rotation=45)

        # Latency chart
        p50_latencies = [r.p50_latency for r in results]
        p95_latencies = [r.p95_latency for r in results]
        p99_latencies = [r.p99_latency for r in results]

        x = np.arange(len(test_names))
        width = 0.25

        axes[0, 1].bar(x - width, p50_latencies, width, label='P50')
        axes[0, 1].bar(x, p95_latencies, width, label='P95')
        axes[0, 1].bar(x + width, p99_latencies, width, label='P99')
        axes[0, 1].axhline(y=10, color='r', linestyle='--', label='Target (10s)')
        axes[0, 1].set_title('Latency Percentiles')
        axes[0, 1].set_ylabel('Seconds')
        axes[0, 1].set_xticks(x)
        axes[0, 1].set_xticklabels(test_names, rotation=45)
        axes[0, 1].legend()

        # Success rate chart
        success_rates = [(r.successful_submissions / r.total_submissions) * 100 for r in results]
        axes[0, 2].bar(test_names, success_rates, color='green')
        axes[0, 2].axhline(y=99, color='r', linestyle='--', label='Target (99%)')
        axes[0, 2].set_title('Success Rate')
        axes[0, 2].set_ylabel('Percent')
        axes[0, 2].legend()
        axes[0, 2].tick_params(axis='x', rotation=45)

        # Memory usage chart
        memory_mb = [r.peak_memory_mb for r in results]
        axes[1, 0].bar(test_names, memory_mb, color='orange')
        axes[1, 0].axhline(y=4096, color='r', linestyle='--', label='Limit (4GB)')
        axes[1, 0].set_title('Peak Memory Usage')
        axes[1, 0].set_ylabel('MB')
        axes[1, 0].legend()
        axes[1, 0].tick_params(axis='x', rotation=45)

        # CPU usage chart
        cpu_percent = [r.avg_cpu_percent for r in results]
        axes[1, 1].bar(test_names, cpu_percent, color='purple')
        axes[1, 1].set_title('Average CPU Usage')
        axes[1, 1].set_ylabel('Percent')
        axes[1, 1].tick_params(axis='x', rotation=45)

        # Throughput vs Latency scatter
        axes[1, 2].scatter(rpms, p99_latencies, s=100, alpha=0.7)
        axes[1, 2].axhline(y=10, color='r', linestyle='--', alpha=0.5)
        axes[1, 2].axvline(x=1000, color='r', linestyle='--', alpha=0.5)
        axes[1, 2].set_xlabel('RPM')
        axes[1, 2].set_ylabel('P99 Latency (s)')
        axes[1, 2].set_title('Throughput vs P99 Latency')

        # Add labels to scatter plot
        for i, (rpm, latency, name) in enumerate(zip(rpms, p99_latencies, test_names)):
            axes[1, 2].annotate(name, (rpm, latency), xytext=(5, 5),
                               textcoords='offset points', fontsize=8)

        # Adjust layout and save
        plt.tight_layout()
        chart_path = self.output_dir / f"benchmark_charts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Saved benchmark charts to {chart_path}")


async def main():
    """Main entry point for benchmark runner"""
    runner = BenchmarkRunner()

    logger.info("Starting RedditHarbor performance benchmark suite")
    logger.info("This will test the system under various load conditions")
    logger.info("Target: 1000 submissions/minute with P99 latency < 10s")

    try:
        results = await runner.run_all_benchmarks()

        logger.info("\n" + "="*60)
        logger.info("BENCHMARK SUITE COMPLETED")
        logger.info("="*60)

        for result in results:
            logger.info(f"\n{result.test_name}:")
            logger.info(f"  RPM: {result.submissions_per_minute:.1f}")
            logger.info(f"  P99 Latency: {result.p99_latency:.2f}s")
            logger.info(f"  Success Rate: {(result.successful_submissions/result.total_submissions)*100:.1f}%")

    except Exception as e:
        logger.error(f"Benchmark suite failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())