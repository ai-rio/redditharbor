#!/usr/bin/env python3
"""
Performance benchmark for RedditHarbor Agno analyzer
Tests both sequential and parallel execution
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List

sys.path.append('.')

from models.reddit import RedditSubmission
from transform.agno_analyzer import AgnoOpportunityAnalyzer
from transform.embedding_factory import EmbeddingFactory


class PerformanceBenchmark:
    """Benchmark suite for Agno analyzer performance"""

    def __init__(self):
        self.results = {}

    def create_test_submissions(self, count: int = 10) -> list[RedditSubmission]:
        """Create test submissions for benchmarking"""
        submissions = []

        test_data = [
            {
                "title": "AI Tool for Code Review",
                "text": "Looking for an automated code review tool that can analyze code quality and suggest improvements for our development team",
                "subreddit": "programming",
                "author": f"dev_user_{i}"
            }
            for i in range(count)
        ]

        for i, data in enumerate(test_data):
            submission = RedditSubmission(
                id=f"benchmark_{i}",
                title=data["title"],
                text=data["text"],
                author=data["author"],
                subreddit=data["subreddit"],
                created_at=datetime.utcnow().isoformat()
            )
            submissions.append(submission)

        return submissions

    async def benchmark_sequential_execution(self, analyzer, submissions: list[RedditSubmission]):
        """Benchmark sequential agent execution"""
        print("\n=== Sequential Execution Benchmark ===")
        start_time = time.time()

        results = []
        for submission in submissions:
            result = analyzer.analyze_submission(submission)
            results.append(result)

        end_time = time.time()
        duration = end_time - start_time

        avg_time = duration / len(submissions)
        throughput = len(submissions) / duration

        print(f"Total time: {duration:.2f}s")
        print(f"Average per submission: {avg_time:.2f}s")
        print(f"Throughput: {throughput:.2f} submissions/sec")

        return {
            'total_time': duration,
            'avg_time': avg_time,
            'throughput': throughput,
            'results': results
        }

    async def benchmark_parallel_execution(self, analyzer, submissions: list[RedditSubmission]):
        """Benchmark parallel agent execution"""
        print("\n=== Parallel Execution Benchmark ===")

        # Use batch analysis for parallel processing
        start_time = time.time()
        results = await analyzer.analyze_batch_async(submissions, batch_size=5)
        end_time = time.time()

        duration = end_time - start_time
        avg_time = duration / len(submissions)
        throughput = len(submissions) / duration

        print(f"Total time: {duration:.2f}s")
        print(f"Average per submission: {avg_time:.2f}s")
        print(f"Throughput: {throughput:.2f} submissions/sec")

        return {
            'total_time': duration,
            'avg_time': avg_time,
            'throughput': throughput,
            'results': results
        }

    async def benchmark_embedding_providers(self, submissions: list[RedditSubmission]):
        """Benchmark different embedding providers"""
        print("\n=== Embedding Provider Benchmark ===")

        providers = ['fake', 'local']  # Start with free providers
        results = {}

        for provider in providers:
            print(f"\nTesting {provider} provider...")
            try:
                # Create analyzer with specific embedding provider
                analyzer = AgnoOpportunityAnalyzer(
                    model="anthropic/claude-haiku-4.5",
                    enable_embeddings=True,
                    embedding_provider=provider
                )

                start_time = time.time()
                test_text = "This is a test for embedding generation performance"
                embedding, metadata = analyzer.embedding_strategy.generate_embedding(test_text)
                end_time = time.time()

                duration = end_time - start_time

                results[provider] = {
                    'duration': duration,
                    'dimensions': len(embedding),
                    'metadata': metadata
                }

                print(f"  Duration: {duration:.3f}s")
                print(f"  Dimensions: {len(embedding)}")
                print(f"  Provider: {metadata.get('provider', 'unknown')}")

            except Exception as e:
                print(f"  Error: {e}")
                results[provider] = {'error': str(e)}

        return results

    async def benchmark_batch_embeddings(self, analyzer, texts: list[str]):
        """Benchmark batch embedding processing"""
        print("\n=== Batch Embedding Benchmark ===")

        provider = analyzer.embedding_strategy.primary_provider

        if not hasattr(provider, 'embed_batch'):
            print("Provider does not support batch processing")
            return None

        # Single embedding test
        single_start = time.time()
        for text in texts:
            embedding, _ = provider.embed(text)
        single_end = time.time()
        single_duration = single_end - single_start

        # Batch embedding test
        batch_start = time.time()
        embeddings = provider.embed_batch(texts)
        batch_end = time.time()
        batch_duration = batch_end - batch_start

        print(f"Single embeddings: {single_duration:.3f}s ({len(texts)} requests)")
        print(f"Batch embeddings: {batch_duration:.3f}s (1 request)")
        print(f"Improvement: {(single_duration/batch_duration):.1f}x faster")

        return {
            'single_duration': single_duration,
            'batch_duration': batch_duration,
            'improvement': single_duration / batch_duration
        }

    async def run_full_benchmark(self, submission_count: int = 10):
        """Run complete benchmark suite"""
        print("=" * 60)
        print("REDDITHARBOR AGNO PERFORMANCE BENCHMARK")
        print("=" * 60)

        # Create test data
        submissions = self.create_test_submissions(submission_count)
        print(f"Created {len(submissions)} test submissions")

        # Initialize analyzer
        analyzer = AgnoOpportunityAnalyzer(
            model="anthropic/claude-haiku-4.5",
            enable_embeddings=True,
            embedding_provider="fake"  # Use fake for consistent benchmarking
        )

        # Run benchmarks
        results = {}

        # 1. Sequential vs Parallel
        if hasattr(analyzer, 'analyze_batch_async'):
            sequential = await self.benchmark_sequential_execution(analyzer, submissions[:5])
            parallel = await self.benchmark_parallel_execution(analyzer, submissions[:5])

            results['execution_comparison'] = {
                'sequential': sequential,
                'parallel': parallel,
                'improvement': sequential['throughput'] / parallel['throughput']
            }

            print(f"\n🚀 Parallel execution improvement: {results['execution_comparison']['improvement']:.1f}x")

        # 2. Embedding providers
        embedding_results = await self.benchmark_embedding_providers(submissions[:3])
        results['embedding_providers'] = embedding_results

        # 3. Batch embeddings
        test_texts = [sub.text for sub in submissions[:10]]
        batch_results = await self.benchmark_batch_embeddings(analyzer, test_texts)
        if batch_results:
            results['batch_embeddings'] = batch_results

        # 4. Memory usage estimate
        print("\n=== Memory Usage Analysis ===")
        if analyzer.enable_embeddings and analyzer.embedding_strategy:
            sample_embedding, _ = analyzer.embedding_strategy.generate_embedding("Test")
            embedding_size = len(sample_embedding) * 4  # 4 bytes per float32

            print(f"Single embedding size: {embedding_size:,} bytes")
            print(f"Memory per 1K submissions: {embedding_size * 1000 / 1024 / 1024:.1f} MB")
            print(f"Memory per 100K submissions: {embedding_size * 100000 / 1024 / 1024:.1f} MB")

            results['memory_analysis'] = {
                'single_embedding_bytes': embedding_size,
                'per_1k_mb': embedding_size * 1000 / 1024 / 1024,
                'per_100k_mb': embedding_size * 100000 / 1024 / 1024
            }

        # 5. Production scaling estimate
        print("\n=== Production Scaling Estimates ===")
        if 'execution_comparison' in results:
            parallel_throughput = results['execution_comparison']['parallel']['throughput']

            # Calculate requirements for 1K submissions/minute
            target_throughput = 1000 / 60  # 16.67 submissions/sec
            workers_needed = target_throughput / parallel_throughput

            print(f"Target throughput: 1,000 submissions/minute ({target_throughput:.1f}/sec)")
            print(f"Single worker throughput: {parallel_throughput:.1f}/sec")
            print(f"Workers needed: {workers_needed:.0f}")

            results['scaling_estimate'] = {
                'target_throughput': target_throughput,
                'single_worker_throughput': parallel_throughput,
                'workers_needed': workers_needed
            }

        # Save results
        self.results = results
        self._save_results()

        print("\n" + "=" * 60)
        print("BENCHMARK COMPLETE")
        print("=" * 60)

        return results

    def _save_results(self):
        """Save benchmark results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_results_{timestamp}.json"

        # Prepare results for JSON serialization
        json_results = {}
        for key, value in self.results.items():
            if isinstance(value, dict):
                json_results[key] = value
            else:
                json_results[key] = str(value)

        # Add timestamp and summary
        json_results['benchmark_timestamp'] = timestamp
        json_results['python_version'] = sys.version

        with open(filename, 'w') as f:
            json.dump(json_results, f, indent=2)

        print(f"\nResults saved to: {filename}")


async def main():
    """Run benchmark suite"""
    import argparse

    # Parse command line args
    parser = argparse.ArgumentParser(description='Benchmark Agno analyzer performance')
    parser.add_argument('count', nargs='?', type=int, default=10,
                        help='Number of submissions to test (1-50, default: 10)')
    parser.add_argument('--with-agentops', action='store_true',
                        help='Enable AgentOps tracking for performance monitoring')
    args = parser.parse_args()

    # Validate count
    count = max(1, min(50, args.count))

    benchmark = PerformanceBenchmark()

    print(f"Running benchmark with {count} submissions...")
    if args.with_agentops:
        print("Note: AgentOps tracking enabled")
    else:
        print("Note: Using fake embeddings for consistent performance measurement")

    # Run the benchmark
    results = await benchmark.run_full_benchmark(count, enable_agentops=args.with_agentops)

    # Print summary
    print("\n📊 BENCHMARK SUMMARY:")
    if 'execution_comparison' in results:
        improvement = results['execution_comparison']['improvement']
        print(f"  • Parallel execution: {improvement:.1f}x faster")
    if 'batch_embeddings' in results:
        batch_improvement = results['batch_embeddings']['improvement']
        print(f"  • Batch embeddings: {batch_improvement:.1f}x faster")
    if 'scaling_estimate' in results:
        workers = results['scaling_estimate']['workers_needed']
        print(f"  • Workers needed for 1K/min: {workers:.0f}")
    if args.with_agentops:
        print("  • AgentOps tracking: Enabled")


if __name__ == "__main__":
    # Check for required packages
    try:
        import sentence_transformers
    except ImportError:
        print("⚠️  sentence-transformers not installed. Local embeddings will be skipped.")
        print("   Install with: pip install sentence-transformers torch")

    # Run benchmark
    asyncio.run(main())
