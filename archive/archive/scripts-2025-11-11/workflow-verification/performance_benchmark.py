#!/usr/bin/env python3
"""
DLT Performance Benchmark Script

Compare performance of traditional collection vs DLT activity validation.
Measures API calls, data quality, processing time, and memory usage.
"""

import time
import sys
import os
import logging
import psutil
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class BenchmarkMetrics:
    """Data class for benchmark metrics"""
    api_calls: int = 0
    processing_time: float = 0.0
    memory_usage: float = 0.0
    items_collected: int = 0
    quality_score: float = 0.0
    active_subreddits: int = 0
    validation_time: float = 0.0

class PerformanceBenchmark:
    """Comprehensive benchmark class for comparing collection methods"""

    def __init__(self):
        self.results = {}
        self.process = psutil.Process()
        self.mock_data = self._generate_mock_data()

    def _generate_mock_data(self) -> Dict[str, Any]:
        """Generate realistic mock data for benchmarking"""
        return {
            'subreddit_activity': {
                # Highly active subreddits (30%)
                'high_activity': {
                    'comments_per_day': (100, 500),
                    'posts_per_day': (20, 100),
                    'avg_score': (50, 200),
                    'subscribers': (50000, 500000)
                },
                # Moderately active (40%)
                'medium_activity': {
                    'comments_per_day': (20, 100),
                    'posts_per_day': (5, 20),
                    'avg_score': (10, 50),
                    'subscribers': (10000, 50000)
                },
                # Low activity (30%)
                'low_activity': {
                    'comments_per_day': (1, 20),
                    'posts_per_day': (1, 5),
                    'avg_score': (1, 10),
                    'subscribers': (1000, 10000)
                }
            },
            'content_quality': {
                # Traditional collection quality distribution
                'traditional': {
                    'high_quality': 0.3,  # 30% high quality
                    'medium_quality': 0.4,  # 40% medium quality
                    'low_quality': 0.3   # 30% low quality
                },
                # DLT validated quality distribution
                'dlt_validated': {
                    'high_quality': 0.7,  # 70% high quality (due to activity validation)
                    'medium_quality': 0.25,  # 25% medium quality
                    'low_quality': 0.05   # 5% low quality
                }
            }
        }

    def start_timer(self, operation_name: str):
        """Start timing an operation"""
        self.results[f"{operation_name}_start_time"] = time.time()
        self.results[f"{operation_name}_start_memory"] = self.process.memory_info().rss / 1024 / 1024  # MB

    def end_timer(self, operation_name: str):
        """End timing an operation"""
        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        start_time = self.results.get(f"{operation_name}_start_time", 0)
        start_memory = self.results.get(f"{operation_name}_start_memory", 0)

        self.results[f"{operation_name}_duration"] = end_time - start_time
        self.results[f"{operation_name}_memory_delta"] = end_memory - start_memory

    def record_metric(self, metric_name: str, value: Any):
        """Record a performance metric"""
        self.results[metric_name] = value

    def _get_subreddit_activity_level(self, subreddit_name: str) -> str:
        """Determine activity level for a subreddit (for consistent simulation)"""
        # Use hash for consistent activity level assignment
        hash_val = hash(subreddit_name) % 100
        if hash_val < 30:
            return 'high_activity'
        elif hash_val < 70:
            return 'medium_activity'
        else:
            return 'low_activity'

    def simulate_traditional_collection(self, subreddits: List[str]) -> BenchmarkMetrics:
        """Simulate traditional collection performance"""
        logger.info(f"🔍 Simulating traditional collection for {len(subreddits)} subreddits...")

        metrics = BenchmarkMetrics()
        self.start_timer("traditional_collection")

        total_api_calls = 0
        items_collected = 0
        quality_scores = []

        for subreddit in subreddits:
            # Traditional collection makes same API calls regardless of activity
            # Posts: 50 per sort type × 3 sort types = 150 API calls
            # Comments: 15 per post × 150 posts = 2,250 API calls
            api_calls_per_subreddit = 2,400
            total_api_calls += api_calls_per_subreddit

            # Collect items regardless of activity level
            # Traditional approach doesn't validate activity first
            posts_collected = 150  # Fixed number per subreddit
            comments_per_post = 15

            items_collected += posts_collected
            items_collected += posts_collected * comments_per_post

            # Simulate content quality based on traditional distribution
            quality_dist = self.mock_data['content_quality']['traditional']
            for _ in range(posts_collected):
                rand = random.random()
                if rand < quality_dist['high_quality']:
                    quality_scores.append(0.8)
                elif rand < quality_dist['high_quality'] + quality_dist['medium_quality']:
                    quality_scores.append(0.5)
                else:
                    quality_scores.append(0.2)

            # Simulate processing delay
            time.sleep(0.001)  # Small delay to simulate API latency

        metrics.api_calls = total_api_calls
        metrics.items_collected = items_collected
        metrics.quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        metrics.active_subreddits = len(subreddits)  # Traditional treats all as active

        self.end_timer("traditional_collection")
        metrics.processing_time = self.results["traditional_collection_duration"]
        metrics.memory_usage = max(0, self.results.get("traditional_collection_memory_delta", 0))

        logger.info(f"✅ Traditional simulation complete:")
        logger.info(f"  API calls: {total_api_calls:,}")
        logger.info(f"  Items collected: {items_collected:,}")
        logger.info(f"  Quality score: {metrics.quality_score:.2f}")

        return metrics

    def simulate_dlt_collection(self, subreddits: List[str]) -> BenchmarkMetrics:
        """Simulate DLT activity validation performance"""
        logger.info(f"🚀 Simulating DLT collection for {len(subreddits)} subreddits...")

        metrics = BenchmarkMetrics()

        # Start overall timer
        self.start_timer("dlt_collection")

        # Stage 1: Activity validation
        self.start_timer("activity_validation")
        active_subreddits = []
        validation_api_calls = 0

        for subreddit in subreddits:
            # Activity validation uses lighter API calls
            # Recent comments: 20, Top posts: 10 = 30 API calls per subreddit
            validation_calls = 30
            validation_api_calls += validation_calls

            # Determine activity level
            activity_level = self._get_subreddit_activity_level(subreddit)
            activity_data = self.mock_data['subreddit_activity'][activity_level]

            # Calculate activity score based on simulated metrics
            comments, posts = self._simulate_activity_metrics(activity_data)
            activity_score = self._calculate_activity_score(comments, posts, activity_data)

            # Apply activity threshold (25 is the configured minimum)
            if activity_score >= 25:
                active_subreddits.append(subreddit)

            # Small delay for validation processing
            time.sleep(0.0005)

        self.end_timer("activity_validation")
        metrics.validation_time = self.results["activity_validation_duration"]
        metrics.active_subreddits = len(active_subreddits)

        # Stage 2: Collection from active subreddits only
        self.start_timer("dlt_data_collection")
        collection_api_calls = 0
        items_collected = 0
        quality_scores = []

        for subreddit in active_subreddits:
            # Full collection but only for active subreddits
            # Same API call pattern as traditional but for fewer subreddits
            api_calls_per_subreddit = 2,400
            collection_api_calls += api_calls_per_subreddit

            # Active subreddits yield more and higher quality content
            activity_level = self._get_subreddit_activity_level(subreddit)
            if activity_level == 'high_activity':
                posts_collected = 150
                comments_per_post = 20
            elif activity_level == 'medium_activity':
                posts_collected = 100
                comments_per_post = 15
            else:  # low_activity (but passed threshold)
                posts_collected = 50
                comments_per_post = 10

            items_collected += posts_collected
            items_collected += posts_collected * comments_per_post

            # Higher quality content from active subreddits
            quality_dist = self.mock_data['content_quality']['dlt_validated']
            for _ in range(posts_collected):
                rand = random.random()
                if rand < quality_dist['high_quality']:
                    quality_scores.append(0.9)
                elif rand < quality_dist['high_quality'] + quality_dist['medium_quality']:
                    quality_scores.append(0.6)
                else:
                    quality_scores.append(0.3)

            # Processing delay
            time.sleep(0.001)

        self.end_timer("dlt_data_collection")

        # Calculate total metrics
        total_api_calls = validation_api_calls + collection_api_calls
        metrics.api_calls = total_api_calls
        metrics.items_collected = items_collected
        metrics.quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        self.end_timer("dlt_collection")
        metrics.processing_time = self.results["dlt_collection_duration"]
        metrics.memory_usage = max(0, self.results.get("dlt_collection_memory_delta", 0))

        logger.info(f"✅ DLT simulation complete:")
        logger.info(f"  Active subreddits: {len(active_subreddits)}/{len(subreddits)}")
        logger.info(f"  Total API calls: {total_api_calls:,}")
        logger.info(f"  Items collected: {items_collected:,}")
        logger.info(f"  Quality score: {metrics.quality_score:.2f}")

        return metrics

    def _simulate_activity_metrics(self, activity_data: Dict[str, tuple]) -> tuple:
        """Simulate activity metrics for a subreddit"""
        comments_range = activity_data['comments_per_day']
        posts_range = activity_data['posts_per_day']

        comments = random.randint(*comments_range)
        posts = random.randint(*posts_range)

        return comments, posts

    def _calculate_activity_score(self, comments: int, posts: int, activity_data: Dict[str, tuple]) -> float:
        """Calculate activity score based on metrics (same algorithm as DLT system)"""
        # Factor 1: Recent comments (40% weight)
        comment_score = min(comments * 0.4, 100)

        # Factor 2: Post engagement (30% weight) - simulate with avg score
        avg_score = random.randint(*activity_data['avg_score'])
        engagement_score = min(posts * avg_score * 0.3, 100)

        # Factor 3: Subscriber base (20% weight)
        subscribers = random.randint(*activity_data['subscribers'])
        subscriber_score = min(subscribers / 1000, 100) * 0.2

        # Factor 4: Active users (10% weight) - estimate as 5% of subscribers
        active_users = int(subscribers * 0.05)
        active_user_score = min(active_users / 100, 50) * 0.1

        total_score = comment_score + engagement_score + subscriber_score + active_user_score
        return int(total_score)

    def calculate_improvements(self, traditional: BenchmarkMetrics, dlt: BenchmarkMetrics) -> Dict[str, float]:
        """Calculate performance improvements between methods"""
        improvements = {}

        # API call reduction
        if traditional.api_calls > 0:
            api_improvement = ((traditional.api_calls - dlt.api_calls) / traditional.api_calls) * 100
            improvements['api_call_reduction'] = api_improvement

        # Processing time improvement
        if traditional.processing_time > 0:
            time_improvement = ((traditional.processing_time - dlt.processing_time) / traditional.processing_time) * 100
            improvements['time_improvement'] = time_improvement

        # Quality improvement
        if traditional.quality_score > 0:
            quality_improvement = ((dlt.quality_score - traditional.quality_score) / traditional.quality_score) * 100
            improvements['quality_improvement'] = quality_improvement

        # Memory efficiency improvement
        if traditional.memory_usage > 0:
            memory_improvement = ((traditional.memory_usage - dlt.memory_usage) / traditional.memory_usage) * 100
            improvements['memory_efficiency'] = memory_improvement

        # Items per API call efficiency
        traditional_efficiency = traditional.items_collected / max(traditional.api_calls, 1)
        dlt_efficiency = dlt.items_collected / max(dlt.api_calls, 1)

        if traditional_efficiency > 0:
            efficiency_improvement = ((dlt_efficiency - traditional_efficiency) / traditional_efficiency) * 100
            improvements['efficiency_improvement'] = efficiency_improvement

        return improvements

    def generate_report(self, traditional: BenchmarkMetrics, dlt: BenchmarkMetrics,
                       subreddit_count: int, improvements: Dict[str, float]) -> Dict[str, Any]:
        """Generate comprehensive performance benchmark report"""
        logger.info("📊 Generating performance report...")

        report = {
            "test_date": datetime.utcnow().isoformat(),
            "test_configuration": {
                "subreddit_count": subreddit_count,
                "simulation_type": "mock",
                "dlt_config": {
                    "min_activity_score": 25,
                    "time_filter": "week"
                }
            },
            "traditional_metrics": {
                "api_calls": traditional.api_calls,
                "processing_time_seconds": round(traditional.processing_time, 2),
                "memory_usage_mb": round(traditional.memory_usage, 2),
                "items_collected": traditional.items_collected,
                "quality_score": round(traditional.quality_score, 3),
                "active_subreddits": traditional.active_subreddits,
                "efficiency_items_per_api_call": round(traditional.items_collected / max(traditional.api_calls, 1), 3)
            },
            "dlt_metrics": {
                "api_calls": dlt.api_calls,
                "processing_time_seconds": round(dlt.processing_time, 2),
                "memory_usage_mb": round(dlt.memory_usage, 2),
                "items_collected": dlt.items_collected,
                "quality_score": round(dlt.quality_score, 3),
                "active_subreddits": dlt.active_subreddits,
                "validation_time_seconds": round(dlt.validation_time, 2),
                "efficiency_items_per_api_call": round(dlt.items_collected / max(dlt.api_calls, 1), 3)
            },
            "improvements": {
                k: round(v, 1) for k, v in improvements.items()
            },
            "executive_summary": {
                "api_call_reduction": f"{improvements.get('api_call_reduction', 0):.1f}%",
                "quality_improvement": f"{improvements.get('quality_improvement', 0):.1f}%",
                "efficiency_gain": f"{improvements.get('efficiency_improvement', 0):.1f}%",
                "dlt_recommendation": "IMPLEMENT" if improvements.get('quality_improvement', 0) > 20 and improvements.get('api_call_reduction', 0) > 20 else "EVALUATE"
            }
        }

        return report

def run_benchmark(subreddit_count: int = 50, save_report: bool = True) -> Dict[str, Any]:
    """Run performance benchmark with specified parameters"""
    logger.info(f"🚀 Starting performance benchmark with {subreddit_count} subreddits")

    # Generate test subreddit list
    test_subreddits = [f"test_subreddit_{i}" for i in range(subreddit_count)]

    benchmark = PerformanceBenchmark()

    # Run traditional collection simulation
    logger.info("=== Traditional Collection Simulation ===")
    traditional_metrics = benchmark.simulate_traditional_collection(test_subreddits)

    # Run DLT collection simulation
    logger.info("\n=== DLT Activity Validation Simulation ===")
    dlt_metrics = benchmark.simulate_dlt_collection(test_subreddits)

    # Calculate improvements
    improvements = benchmark.calculate_improvements(traditional_metrics, dlt_metrics)

    # Generate comprehensive report
    report = benchmark.generate_report(traditional_metrics, dlt_metrics, subreddit_count, improvements)

    # Print results summary
    print("\n" + "=" * 80)
    print("📊 PERFORMANCE BENCHMARK RESULTS")
    print("=" * 80)

    trad = report["traditional_metrics"]
    dlt = report["dlt_metrics"]
    exec_summary = report["executive_summary"]

    print(f"\n🔍 TRADITIONAL COLLECTION:")
    print(f"  API Calls: {trad['api_calls']:,}")
    print(f"  Processing Time: {trad['processing_time_seconds']}s")
    print(f"  Memory Usage: {trad['memory_usage_mb']} MB")
    print(f"  Items Collected: {trad['items_collected']:,}")
    print(f"  Quality Score: {trad['quality_score']}")
    print(f"  Efficiency: {trad['efficiency_items_per_api_call']} items/API call")

    print(f"\n🚀 DLT ACTIVITY VALIDATION:")
    print(f"  API Calls: {dlt['api_calls']:,}")
    print(f"  Processing Time: {dlt['processing_time_seconds']}s")
    print(f"  Memory Usage: {dlt['memory_usage_mb']} MB")
    print(f"  Items Collected: {dlt['items_collected']:,}")
    print(f"  Quality Score: {dlt['quality_score']}")
    print(f"  Active Subreddits: {dlt['active_subreddits']}/{subreddit_count}")
    print(f"  Validation Time: {dlt['validation_time_seconds']}s")
    print(f"  Efficiency: {dlt['efficiency_items_per_api_call']} items/API call")

    print(f"\n🎯 IMPROVEMENTS:")
    print(f"  API Call Reduction: {exec_summary['api_call_reduction']}")
    print(f"  Quality Improvement: {exec_summary['quality_improvement']}")
    print(f"  Efficiency Gain: {exec_summary['efficiency_gain']}")
    print(f"  Recommendation: {exec_summary['dlt_recommendation']}")

    # Save detailed report
    if save_report:
        report_dir = "docs/reports"
        os.makedirs(report_dir, exist_ok=True)
        report_file = f"{report_dir}/dlt-performance-report-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.json"

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"📄 Detailed report saved to: {report_file}")

    return report

def main():
    """Main function with command line arguments"""
    import argparse

    parser = argparse.ArgumentParser(description="DLT Performance Benchmark for RedditHarbor")
    parser.add_argument("--subreddits", type=int, default=50,
                       help="Number of subreddits to simulate (default: 50)")
    parser.add_argument("--small", action="store_true",
                       help="Run small scale benchmark (10 subreddits)")
    parser.add_argument("--medium", action="store_true",
                       help="Run medium scale benchmark (50 subreddits)")
    parser.add_argument("--large", action="store_true",
                       help="Run large scale benchmark (200 subreddits)")
    parser.add_argument("--no-save", action="store_true",
                       help="Don't save report to file")

    args = parser.parse_args()

    # Determine subreddit count
    if args.small:
        subreddit_count = 10
        logger.info("Running SMALL scale benchmark (10 subreddits)")
    elif args.medium:
        subreddit_count = 50
        logger.info("Running MEDIUM scale benchmark (50 subreddits)")
    elif args.large:
        subreddit_count = 200
        logger.info("Running LARGE scale benchmark (200 subreddits)")
    else:
        subreddit_count = args.subreddits
        logger.info(f"Running CUSTOM scale benchmark ({subreddit_count} subreddits)")

    # Run benchmark
    save_report = not args.no_save
    report = run_benchmark(subreddit_count, save_report)

    return report

if __name__ == "__main__":
    try:
        report = main()
        logger.info("✅ Performance benchmark completed successfully")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Benchmark failed: {e}")
        sys.exit(1)