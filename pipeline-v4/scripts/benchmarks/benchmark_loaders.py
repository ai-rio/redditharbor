"""
Performance Benchmarking Suite for SQLModelLoader vs PostgresLoader
Task 3.4: Comprehensive performance comparison with multiple metrics
"""

import json
import logging
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import psutil

# Add pipeline-v4 to path (we're in pipeline-v4 directory)
sys.path.insert(0, str(Path(__file__).parent))

# Import from pipeline-v4 modules
from config.settings import get_settings
from database import get_engine
from load.postgres_loader import PostgresLoader
from load.sqlmodel_loader import SQLModelLoader
from models.analysis import Opportunity

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Suppress info logs during benchmarking
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BenchmarkResult:
    """Container for benchmark results"""

    def __init__(self, loader_name: str):
        self.loader_name = loader_name
        self.metrics = {
            'insert_single': [],
            'insert_batch': [],
            'duplicate_detection': [],
            'retrieval': [],
            'memory_usage': [],
            'connection_pool': {}
        }

    def add_metric(self, category: str, value: float):
        """Add a metric measurement"""
        if category in self.metrics and isinstance(self.metrics[category], list):
            self.metrics[category].append(value)

    def set_pool_metrics(self, size: int, checked_out: int):
        """Set connection pool metrics"""
        self.metrics['connection_pool'] = {
            'size': size,
            'checked_out': checked_out
        }

    def get_average(self, category: str) -> float:
        """Get average for a metric category"""
        values = self.metrics.get(category, [])
        if not values:
            return 0.0
        return sum(values) / len(values)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export"""
        return {
            'loader_name': self.loader_name,
            'averages': {
                'insert_single_ms': self.get_average('insert_single') * 1000,
                'insert_batch_ms': self.get_average('insert_batch') * 1000,
                'duplicate_detection_ms': self.get_average('duplicate_detection') * 1000,
                'retrieval_ms': self.get_average('retrieval') * 1000,
                'memory_mb': self.get_average('memory_usage'),
            },
            'connection_pool': self.metrics['connection_pool'],
            'raw_measurements': {
                k: v for k, v in self.metrics.items()
                if isinstance(v, list) and v
            }
        }


class LoaderBenchmark:
    """Comprehensive loader performance benchmark suite"""

    def __init__(self, data_volumes: list[int] = None):
        """
        Initialize benchmark suite

        Args:
            data_volumes: List of data volumes to test (default: [100, 1000, 10000])
        """
        self.data_volumes = data_volumes or [100, 1000, 10000]
        self.settings = get_settings()
        self.results = {}
        self.process = psutil.Process()

    def generate_test_opportunity(self, index: int) -> Opportunity:
        """Generate a test opportunity with realistic data"""
        return Opportunity(
            submission_id=f"bench_{index}_{int(time.time() * 1000000)}",
            subreddit="benchmarking",
            title=f"Benchmark Opportunity {index}",
            wtp_score=75.0 + (index % 25),
            confidence_score=80.0,
            trust_level="MEDIUM",
            analysis={
                "app_idea": {
                    "title": f"Benchmark App {index}",
                    "app_concept": "Performance testing application concept",
                    "problem_statement": "Testing database loader performance",
                    "core_functions": ["function1", "function2"],
                    "target_audience": "Performance engineers"
                },
                "pain_points": ["slow inserts", "memory usage"],
                "opportunity_summary": "Test opportunity for benchmarking",
                "content_quality_score": 85.0,
                "is_spam": False,
                "spam_indicators": []
            },
            metrics={
                "market_demand": 85.0,
                "pain_intensity": 75.0,
                "monetization_potential": 80.0,
                "technical_feasibility": 90.0,
                "competition_level": 70.0
            }
        )

    def clean_database(self):
        """Clean test data from database"""
        logger.info("Cleaning benchmark data from database...")

        # Use raw SQL for fast cleanup
        from sqlalchemy import text
        engine = get_engine()

        with engine.connect() as conn:
            result = conn.execute(
                text("DELETE FROM opportunities WHERE subreddit = 'benchmarking'")
            )
            conn.commit()
            logger.info(f"Deleted {result.rowcount} benchmark records")

    def measure_memory(self) -> float:
        """Get current memory usage in MB"""
        mem_info = self.process.memory_info()
        return mem_info.rss / (1024 * 1024)  # Convert to MB

    def get_pool_stats(self, loader) -> tuple[int, int]:
        """Get connection pool statistics"""
        try:
            if isinstance(loader, SQLModelLoader):
                engine = loader.engine
                pool = engine.pool
                return pool.size(), pool.checkedout()
            elif isinstance(loader, PostgresLoader):
                # psycopg2 pool doesn't expose size/checkedout easily
                # Return approximations based on pool configuration
                return 10, 0  # Default pool size from PostgresLoader
        except Exception as e:
            logger.warning(f"Could not get pool stats: {e}")
            return 0, 0

    def warm_up_loader(self, loader):
        """Warm up loader by performing sample operations"""
        logger.debug(f"Warming up {loader.__class__.__name__}...")

        # Create and save a few test records
        for i in range(5):
            opp = self.generate_test_opportunity(-1000 - i)  # Negative index for warmup
            try:
                loader.save_opportunity(opp)
            except:
                pass  # Ignore errors during warmup

        # Clean up warmup data
        from sqlalchemy import text
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(
                text("DELETE FROM opportunities WHERE submission_id LIKE 'bench_-1%'")
            )
            conn.commit()

    def benchmark_single_inserts(
        self,
        loader,
        result: BenchmarkResult,
        count: int,
        iterations: int = 3
    ):
        """Benchmark single insert performance"""
        logger.info(f"  Benchmarking single inserts ({count} records, {iterations} iterations)...")

        for iteration in range(iterations):
            # Clean before each iteration
            self.clean_database()

            start_time = time.perf_counter()
            mem_start = self.measure_memory()

            for i in range(count):
                opp = self.generate_test_opportunity(i)
                loader.save_opportunity(opp)

            elapsed = time.perf_counter() - start_time
            mem_used = self.measure_memory() - mem_start

            # Calculate ops/sec
            ops_per_sec = count / elapsed if elapsed > 0 else 0
            avg_time_per_op = elapsed / count if count > 0 else 0

            result.add_metric('insert_single', avg_time_per_op)
            result.add_metric('memory_usage', mem_used)

            logger.debug(
                f"    Iteration {iteration + 1}: {ops_per_sec:.2f} ops/sec, "
                f"{avg_time_per_op * 1000:.3f} ms/op, {mem_used:.2f} MB"
            )

    def benchmark_batch_inserts(
        self,
        loader,
        result: BenchmarkResult,
        count: int,
        batch_size: int = 100,
        iterations: int = 3
    ):
        """Benchmark batch insert performance (SQLModelLoader only)"""
        if not hasattr(loader, 'save_opportunities'):
            logger.info(f"  Skipping batch insert (not supported by {loader.__class__.__name__})")
            return

        logger.info(f"  Benchmarking batch inserts ({count} records, batch size {batch_size})...")

        for iteration in range(iterations):
            # Clean before each iteration
            self.clean_database()

            # Generate all opportunities
            opportunities = [self.generate_test_opportunity(i) for i in range(count)]

            start_time = time.perf_counter()
            mem_start = self.measure_memory()

            # Process in batches
            for i in range(0, len(opportunities), batch_size):
                batch = opportunities[i:i + batch_size]
                loader.save_opportunities(batch)

            elapsed = time.perf_counter() - start_time
            mem_used = self.measure_memory() - mem_start

            ops_per_sec = count / elapsed if elapsed > 0 else 0
            avg_time_per_op = elapsed / count if count > 0 else 0

            result.add_metric('insert_batch', avg_time_per_op)
            result.add_metric('memory_usage', mem_used)

            logger.debug(
                f"    Iteration {iteration + 1}: {ops_per_sec:.2f} ops/sec, "
                f"{avg_time_per_op * 1000:.3f} ms/op, {mem_used:.2f} MB"
            )

    def benchmark_duplicate_detection(
        self,
        loader,
        result: BenchmarkResult,
        count: int,
        iterations: int = 3
    ):
        """Benchmark duplicate detection speed"""
        logger.info(f"  Benchmarking duplicate detection ({count} attempts)...")

        for iteration in range(iterations):
            # Clean and insert initial data
            self.clean_database()
            opportunities = [self.generate_test_opportunity(i) for i in range(count)]

            # Insert initial batch
            for opp in opportunities:
                loader.save_opportunity(opp)

            # Now benchmark duplicate detection
            start_time = time.perf_counter()

            duplicates_detected = 0
            for opp in opportunities:
                saved = loader.save_opportunity(opp)
                if not saved:
                    duplicates_detected += 1

            elapsed = time.perf_counter() - start_time
            avg_time_per_check = elapsed / count if count > 0 else 0

            result.add_metric('duplicate_detection', avg_time_per_check)

            logger.debug(
                f"    Iteration {iteration + 1}: {duplicates_detected}/{count} detected, "
                f"{avg_time_per_check * 1000:.3f} ms/check"
            )

    def benchmark_retrieval(
        self,
        loader,
        result: BenchmarkResult,
        count: int,
        iterations: int = 3
    ):
        """Benchmark retrieval performance"""
        logger.info(f"  Benchmarking retrieval ({count} records)...")

        # Clean and insert test data once
        self.clean_database()
        opportunities = [self.generate_test_opportunity(i) for i in range(count)]

        for opp in opportunities:
            loader.save_opportunity(opp)

        # Benchmark retrieval
        for iteration in range(iterations):
            start_time = time.perf_counter()

            for opp in opportunities:
                retrieved = loader.get_opportunity(opp.submission_id)
                assert retrieved is not None, f"Failed to retrieve {opp.submission_id}"

            elapsed = time.perf_counter() - start_time
            avg_time_per_get = elapsed / count if count > 0 else 0

            result.add_metric('retrieval', avg_time_per_get)

            logger.debug(
                f"    Iteration {iteration + 1}: {avg_time_per_get * 1000:.3f} ms/get"
            )

    def benchmark_loader(self, loader_class, loader_name: str):
        """Run complete benchmark suite for a loader"""
        logger.info(f"\n{'=' * 70}")
        logger.info(f"Benchmarking: {loader_name}")
        logger.info(f"{'=' * 70}")

        result = BenchmarkResult(loader_name)

        # Initialize loader
        loader = loader_class()

        # Warm up
        self.warm_up_loader(loader)

        # Get pool stats
        pool_size, checked_out = self.get_pool_stats(loader)
        result.set_pool_metrics(pool_size, checked_out)

        # Run benchmarks for each data volume
        for volume in self.data_volumes:
            logger.info(f"\nData volume: {volume:,} records")

            # Adjust iteration count based on volume
            iterations = 3 if volume <= 1000 else 1

            # Single inserts
            self.benchmark_single_inserts(loader, result, volume, iterations)

            # Batch inserts (if supported)
            self.benchmark_batch_inserts(loader, result, volume, iterations=iterations)

            # Duplicate detection
            self.benchmark_duplicate_detection(loader, result, volume, iterations)

            # Retrieval
            self.benchmark_retrieval(loader, result, volume, iterations)

        # Clean up
        self.clean_database()
        loader.close()

        return result

    def run_benchmarks(self) -> dict[str, BenchmarkResult]:
        """Run benchmarks for both loaders"""
        logger.info("Starting loader performance benchmarks...")
        logger.info(f"Data volumes: {self.data_volumes}")

        # Benchmark PostgresLoader
        self.results['PostgresLoader'] = self.benchmark_loader(
            PostgresLoader,
            'PostgresLoader (psycopg2)'
        )

        # Benchmark SQLModelLoader
        self.results['SQLModelLoader'] = self.benchmark_loader(
            SQLModelLoader,
            'SQLModelLoader (SQLAlchemy)'
        )

        return self.results

    def compare_results(self) -> dict:
        """Generate comparison analysis"""
        logger.info("\n" + "=" * 70)
        logger.info("Performance Comparison")
        logger.info("=" * 70)

        postgres = self.results['PostgresLoader']
        sqlmodel = self.results['SQLModelLoader']

        comparison = {
            'timestamp': datetime.now(UTC).isoformat(),
            'data_volumes': self.data_volumes,
            'loaders': {
                'PostgresLoader': postgres.to_dict(),
                'SQLModelLoader': sqlmodel.to_dict()
            },
            'comparison': {}
        }

        # Calculate percentage differences
        metrics = ['insert_single', 'insert_batch', 'duplicate_detection', 'retrieval']

        for metric in metrics:
            pg_avg = postgres.get_average(metric)
            sm_avg = sqlmodel.get_average(metric)

            if pg_avg > 0:
                percent_diff = ((sm_avg - pg_avg) / pg_avg) * 100
                comparison['comparison'][metric] = {
                    'postgres_ms': pg_avg * 1000,
                    'sqlmodel_ms': sm_avg * 1000,
                    'difference_percent': percent_diff,
                    'faster': 'PostgresLoader' if percent_diff > 0 else 'SQLModelLoader'
                }

        # Memory comparison
        pg_mem = postgres.get_average('memory_usage')
        sm_mem = sqlmodel.get_average('memory_usage')
        if pg_mem > 0:
            mem_diff = ((sm_mem - pg_mem) / pg_mem) * 100
            comparison['comparison']['memory_usage'] = {
                'postgres_mb': pg_mem,
                'sqlmodel_mb': sm_mem,
                'difference_percent': mem_diff
            }

        return comparison

    def print_results(self, comparison: dict):
        """Print formatted results"""
        print("\n" + "=" * 80)
        print("LOADER PERFORMANCE BENCHMARK RESULTS")
        print("=" * 80)

        print("\nTest Configuration:")
        print(f"  Data Volumes: {comparison['data_volumes']}")
        print(f"  Timestamp: {comparison['timestamp']}")

        print("\n" + "-" * 80)
        print("Metric Comparison (Lower is Better for Time)")
        print("-" * 80)

        for metric, data in comparison['comparison'].items():
            if metric == 'memory_usage':
                print(f"\n{metric.replace('_', ' ').title()}:")
                print(f"  PostgresLoader:  {data['postgres_mb']:>8.2f} MB")
                print(f"  SQLModelLoader:  {data['sqlmodel_mb']:>8.2f} MB")
                print(f"  Difference:      {data['difference_percent']:>+7.2f}%")
            else:
                print(f"\n{metric.replace('_', ' ').title()}:")
                print(f"  PostgresLoader:  {data['postgres_ms']:>8.3f} ms")
                print(f"  SQLModelLoader:  {data['sqlmodel_ms']:>8.3f} ms")
                print(f"  Difference:      {data['difference_percent']:>+7.2f}%")
                print(f"  Faster:          {data['faster']}")

        # Overall assessment
        print("\n" + "=" * 80)
        print("PERFORMANCE GATE ASSESSMENT")
        print("=" * 80)

        # Check if SQLModel is within 10% for critical metrics
        critical_metrics = ['insert_single', 'duplicate_detection']
        max_diff = 0
        failing_metrics = []

        for metric in critical_metrics:
            if metric in comparison['comparison']:
                diff = comparison['comparison'][metric]['difference_percent']
                if abs(diff) > abs(max_diff):
                    max_diff = diff
                if diff > 10:  # SQLModel is slower by more than 10%
                    failing_metrics.append(f"{metric}: {diff:+.2f}%")

        if failing_metrics:
            print("\n❌ FAIL: SQLModelLoader exceeds 10% threshold")
            print("\nFailing Metrics:")
            for metric in failing_metrics:
                print(f"  - {metric}")
        else:
            print("\n✅ PASS: SQLModelLoader within 10% performance threshold")
            print(f"\nMaximum difference: {max_diff:+.2f}%")

        print("\n" + "=" * 80)

    def save_results(self, comparison: dict, output_dir: str = "."):
        """Save results to JSON file"""
        output_path = Path(output_dir) / "benchmark_results.json"

        with open(output_path, 'w') as f:
            json.dump(comparison, f, indent=2)

        logger.info(f"\nResults saved to: {output_path}")
        return output_path


def main():
    """Main benchmark execution"""
    # Configure data volumes for testing
    # Start with smaller volumes for faster testing, add larger volumes as needed
    data_volumes = [100, 1000, 10000]

    # Check if running in CI or want quick test
    if os.getenv('QUICK_BENCHMARK'):
        data_volumes = [100, 500]

    # Create benchmark suite
    benchmark = LoaderBenchmark(data_volumes=data_volumes)

    # Run benchmarks
    benchmark.run_benchmarks()

    # Compare and analyze
    comparison = benchmark.compare_results()

    # Print results
    benchmark.print_results(comparison)

    # Save results
    output_path = benchmark.save_results(comparison)

    print(f"\nBenchmark complete! Results saved to {output_path}")

    return comparison


if __name__ == "__main__":
    main()
