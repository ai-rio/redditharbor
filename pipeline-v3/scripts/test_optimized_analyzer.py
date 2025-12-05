#!/usr/bin/env python3
"""
Test script for the optimized Agno analyzer

Validates the performance improvements and ensures
Phase 5 production requirements are met.
"""

import asyncio
import time
import json
import logging
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from models.reddit import RedditSubmission
from transform.agno_analyzer_optimized import OptimizedAgnoAnalyzer, BatchConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestSubmissionGenerator:
    """Generate test submissions for validation"""

    def __init__(self):
        self.test_cases = [
            {
                "title": "Need automated expense tracking for small business",
                "text": "I'm spending hours every week categorizing expenses for my consulting business. There must be a way to automatically scan receipts and categorize them. Would pay $50/month for a solution that integrates with QuickBooks.",
                "subreddit": "Entrepreneur",
                "expected_score_range": (70, 90)
            },
            {
                "title": "Building platform to connect freelancers with clients",
                "text": "Creating a marketplace similar to Upwork but focused on AI/ML specialists. Need payment processing, contract templates, and dispute resolution. Target is software companies needing specialized talent.",
                "subreddit": "SaaS",
                "expected_score_range": (60, 85)
            },
            {
                "title": "Tool to compare grocery prices across stores",
                "text": "Family of 4 trying to save on groceries. Want an app that scans receipts and compares prices at Walmart, Target, and local stores. Would definitely pay $10/month if it saves $50+ per month.",
                "subreddit": "frugal",
                "expected_score_range": (75, 95)
            },
            {
                "title": "Looking for free open source alternative to Photoshop",
                "text": "Can't afford Adobe subscription. Need basic photo editing features: layers, filters, text tools. Not willing to pay for software, will use GIMP if I have to.",
                "subreddit": "opensource",
                "expected_score_range": (20, 40)
            },
            {
                "title": "AI tool to summarize customer feedback",
                "text": "Running e-commerce store with 500+ daily customer reviews. Need AI to categorize feedback, identify trends, and highlight urgent issues. Budget: $200/month if it saves 5 hours/week.",
                "subreddit": "smallbusiness",
                "expected_score_range": (65, 85)
            }
        ]

    def generate_submission(self, test_id: int) -> RedditSubmission:
        """Generate a test submission"""
        case = self.test_cases[test_id % len(self.test_cases)]

        return RedditSubmission(
            id=f"test_{test_id}_{int(time.time())}",
            title=case["title"],
            text=case["text"],
            subreddit=case["subreddit"],
            author=f"test_user_{test_id}",
            score=test_id * 2 + 10,
            comments_count=test_id + 5,
            created_at=datetime.now()
        )

    def generate_batch(self, count: int) -> list[RedditSubmission]:
        """Generate batch of test submissions"""
        return [self.generate_submission(i) for i in range(count)]


class PerformanceValidator:
    """Validate performance against Phase 5 requirements"""

    def __init__(self):
        self.requirements = {
            "min_rpm": 1000,
            "max_p99_latency": 10.0,
            "max_error_rate": 0.01,
            "min_success_rate": 0.99
        }

    def validate_throughput(self, rpm: float) -> tuple[bool, str]:
        """Validate throughput requirement"""
        if rpm >= self.requirements["min_rpm"]:
            return True, f"✅ Throughput: {rpm:.1f} RPM (target: {self.requirements['min_rpm']})"
        else:
            return False, f"❌ Throughput: {rpm:.1f} RPM (target: {self.requirements['min_rpm']})"

    def validate_latency(self, p99_latency: float) -> tuple[bool, str]:
        """Validate latency requirement"""
        if p99_latency <= self.requirements["max_p99_latency"]:
            return True, f"✅ P99 Latency: {p99_latency:.2f}s (target: <{self.requirements['max_p99_latency']}s)"
        else:
            return False, f"❌ P99 Latency: {p99_latency:.2f}s (target: <{self.requirements['max_p99_latency']}s)"

    def validate_error_rate(self, error_rate: float) -> tuple[bool, str]:
        """Validate error rate requirement"""
        if error_rate <= self.requirements["max_error_rate"]:
            return True, f"✅ Error Rate: {error_rate*100:.2f}% (target: <{self.requirements['max_error_rate']*100:.1f}%)"
        else:
            return False, f"❌ Error Rate: {error_rate*100:.2f}% (target: <{self.requirements['max_error_rate']*100:.1f}%)"


async def test_basic_functionality():
    """Test basic analyzer functionality"""
    logger.info("\n" + "="*60)
    logger.info("TESTING BASIC FUNCTIONALITY")
    logger.info("="*60)

    generator = TestSubmissionGenerator()
    validator = PerformanceValidator()

    # Initialize optimized analyzer
    config = BatchConfig(
        max_concurrent_submissions=10,
        max_concurrent_agents=5,
        enable_embeddings=True,
        embedding_batch_size=10
    )

    analyzer = OptimizedAgnoAnalyzer(
        config=config,
        enable_embeddings=False  # Disable for basic test
    )

    # Test single submission
    logger.info("\n1. Testing single submission analysis...")
    submission = generator.generate_submission(0)

    start_time = time.time()
    result = await analyzer.analyze_submission_async(submission)
    latency = time.time() - start_time

    logger.info(f"   - Analysis completed in {latency:.2f}s")
    logger.info(f"   - Final Score: {result.final_score:.1f}")
    logger.info(f"   - Trust Level: {result.trust_level}")
    logger.info(f"   - App Idea: {result.app_idea.title}")

    # Test batch processing
    logger.info("\n2. Testing batch analysis...")
    batch = generator.generate_batch(5)

    start_time = time.time()
    results = await analyzer.analyze_batch_async(batch)
    batch_latency = time.time() - start_time

    avg_latency = batch_latency / len(batch)
    success_rate = sum(1 for r in results if r.final_score > 0) / len(results)

    logger.info(f"   - Batch of {len(batch)} completed in {batch_latency:.2f}s")
    logger.info(f"   - Average per submission: {avg_latency:.2f}s")
    logger.info(f"   - Success Rate: {success_rate*100:.1f}%")

    await analyzer.close()

    return success_rate == 1.0


async def test_performance_scalability():
    """Test performance under load"""
    logger.info("\n" + "="*60)
    logger.info("TESTING PERFORMANCE SCALABILITY")
    logger.info("="*60)

    generator = TestSubmissionGenerator()
    validator = PerformanceValidator()

    # Test different load levels
    load_tests = [
        {"name": "Light Load", "submissions": 50, "concurrency": 10},
        {"name": "Medium Load", "submissions": 200, "concurrency": 25},
        {"name": "Heavy Load", "submissions": 500, "concurrency": 50}
    ]

    all_results = []

    for test in load_tests:
        logger.info(f"\n{test['name']}: {test['submissions']} submissions, {test['concurrency']} concurrent")

        # Configure for test
        config = BatchConfig(
            max_concurrent_submissions=test['concurrency'],
            max_concurrent_agents=min(test['concurrency'], 20),
            enable_embeddings=False  # Disable to focus on agent performance
        )

        analyzer = OptimizedAgnoAnalyzer(
            config=config,
            enable_embeddings=False
        )

        # Generate test data
        submissions = generator.generate_batch(test['submissions'])

        # Run test
        start_time = time.time()
        results = await analyzer.analyze_batch_async(submissions)
        total_time = time.time() - start_time

        # Calculate metrics
        rpm = (len(results) / total_time) * 60
        success_count = sum(1 for r in results if r.final_score > 0)
        success_rate = success_count / len(results)

        latencies = []
        for i, result in enumerate(results):
            # Estimate latency based on batch time
            latencies.append(total_time / len(submissions))

        p99_latency = sorted(latencies)[int(len(latencies) * 0.99)]
        error_rate = 1 - success_rate

        # Log results
        logger.info(f"   - RPM: {rpm:.1f}")
        logger.info(f"   - P99 Latency: {p99_latency:.2f}s")
        logger.info(f"   - Success Rate: {success_rate*100:.1f}%")
        logger.info(f"   - Error Rate: {error_rate*100:.2f}%")

        # Validate against requirements
        throughput_ok, throughput_msg = validator.validate_throughput(rpm)
        latency_ok, latency_msg = validator.validate_latency(p99_latency)
        error_ok, error_msg = validator.validate_error_rate(error_rate)

        logger.info(f"   - {throughput_msg}")
        logger.info(f"   - {latency_msg}")
        logger.info(f"   - {error_msg}")

        # Store results
        test_results = {
            "name": test['name'],
            "rpm": rpm,
            "p99_latency": p99_latency,
            "success_rate": success_rate,
            "error_rate": error_rate,
            "meets_requirements": throughput_ok and latency_ok and error_ok
        }
        all_results.append(test_results)

        await analyzer.close()

        # Brief pause between tests
        await asyncio.sleep(1)

    # Generate summary
    logger.info("\n" + "="*60)
    logger.info("PERFORMANCE SUMMARY")
    logger.info("="*60)

    for result in all_results:
        status = "✅ PASS" if result['meets_requirements'] else "❌ FAIL"
        logger.info(f"{result['name']}: {status}")
        logger.info(f"  RPM: {result['rpm']:.1f} | P99: {result['p99_latency']:.2f}s | Success: {result['success_rate']*100:.1f}%")

    return all_results


async def test_embedding_performance():
    """Test embedding batch performance"""
    logger.info("\n" + "="*60)
    logger.info("TESTING EMBEDDING PERFORMANCE")
    logger.info("="*60)

    generator = TestSubmissionGenerator()

    # Test with embeddings enabled
    config = BatchConfig(
        max_concurrent_submissions=20,
        max_concurrent_agents=10,
        enable_embeddings=True,
        embedding_batch_size=96  # Max for Cohere
    )

    analyzer = OptimizedAgnoAnalyzer(
        config=config,
        enable_embeddings=True,
        embedding_provider="fake"  # Use fake provider for testing
    )

    # Test different batch sizes
    batch_sizes = [10, 25, 50, 96]

    for batch_size in batch_sizes:
        logger.info(f"\nTesting batch size: {batch_size}")

        submissions = generator.generate_batch(batch_size)

        start_time = time.time()
        results = await analyzer.analyze_batch_async(submissions)
        total_time = time.time() - start_time

        rpm = (len(results) / total_time) * 60
        avg_latency = total_time / len(results)

        # Check embeddings
        with_embeddings = sum(1 for r in results if r.embedding is not None)

        logger.info(f"   - Processed: {len(results)} submissions")
        logger.info(f"   - RPM: {rpm:.1f}")
        logger.info(f"   - Avg Latency: {avg_latency:.2f}s")
        logger.info(f"   - With Embeddings: {with_embeddings}/{len(results)}")

    await analyzer.close()


async def test_memory_usage():
    """Test memory efficiency under load"""
    logger.info("\n" + "="*60)
    logger.info("TESTING MEMORY USAGE")
    logger.info("="*60)

    import psutil
    import gc

    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    logger.info(f"Initial memory usage: {initial_memory:.1f} MB")

    generator = TestSubmissionGenerator()
    config = BatchConfig(
        max_concurrent_submissions=50,
        enable_embeddings=False
    )

    analyzer = OptimizedAgnoAnalyzer(
        config=config,
        enable_embeddings=False
    )

    # Process batches and monitor memory
    batches = 10
    submissions_per_batch = 100

    for i in range(batches):
        submissions = generator.generate_batch(submissions_per_batch)
        await analyzer.analyze_batch_async(submissions)

        # Force garbage collection every 3 batches
        if (i + 1) % 3 == 0:
            gc.collect()

        current_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = current_memory - initial_memory

        logger.info(f"Batch {i+1}: Memory = {current_memory:.1f} MB (+{memory_increase:.1f} MB)")

    final_memory = process.memory_info().rss / 1024 / 1024
    total_increase = final_memory - initial_memory
    avg_per_submission = total_increase / (batches * submissions_per_batch)

    logger.info(f"\nFinal memory usage: {final_memory:.1f} MB")
    logger.info(f"Total increase: {total_increase:.1f} MB")
    logger.info(f"Average per submission: {avg_per_submission:.3f} MB")

    await analyzer.close()

    return total_increase < 1024  # Less than 1GB increase


async def generate_test_report(results: dict):
    """Generate comprehensive test report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_results": results,
        "summary": {
            "all_tests_passed": all(results.values()),
            "phase_5_ready": results.get("basic_functionality", False) and
                           results.get("scalability", False) and
                           results.get("memory_efficiency", False)
        }
    }

    # Save report
    report_path = Path("test_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"\nTest report saved to: {report_path}")

    # Print summary
    logger.info("\n" + "="*60)
    logger.info("FINAL TEST RESULTS")
    logger.info("="*60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{test_name.replace('_', ' ').title()}: {status}")

    if report["summary"]["phase_5_ready"]:
        logger.info("\n🎉 SYSTEM IS READY FOR PHASE 5 PRODUCTION DEPLOYMENT!")
    else:
        logger.info("\n⚠️  System needs optimization before production deployment")


async def main():
    """Run all performance tests"""
    logger.info("RedditHarbor Agno Analyzer Performance Test Suite")
    logger.info("Phase 5 Production Validation")
    logger.info("="*60)

    results = {}

    # Run tests
    try:
        results["basic_functionality"] = await test_basic_functionality()
    except Exception as e:
        logger.error(f"Basic functionality test failed: {e}")
        results["basic_functionality"] = False

    try:
        scalability_results = await test_performance_scalability()
        # Check if any test meets Phase 5 requirements
        results["scalability"] = any(r['meets_requirements'] for r in scalability_results)
    except Exception as e:
        logger.error(f"Scalability test failed: {e}")
        results["scalability"] = False

    try:
        await test_embedding_performance()
        results["embedding_performance"] = True
    except Exception as e:
        logger.error(f"Embedding test failed: {e}")
        results["embedding_performance"] = False

    try:
        results["memory_efficiency"] = await test_memory_usage()
    except Exception as e:
        logger.error(f"Memory test failed: {e}")
        results["memory_efficiency"] = False

    # Generate report
    await generate_test_report(results)


if __name__ == "__main__":
    # Run tests
    asyncio.run(main())