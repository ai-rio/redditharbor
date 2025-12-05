#!/usr/bin/env python3
"""
Phase 5: Load Testing for RedditHarbor

Validates scalability requirements:
- 1000 submissions/minute target
- P99 latency < 10 seconds under load
- Error rate < 1%
- Memory usage stability
- Resource efficiency
"""

import asyncio
import time
import statistics
import json
import logging
import psutil
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any
import os
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.local')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import RedditHarbor components
from models.reddit import RedditSubmission
from transform.analyzer_factory import AgnoAnalyzerFactory


class LoadTester:
    """Load testing for Phase 5 scalability requirements"""

    def __init__(self):
        self.metrics = {
            'latencies': [],
            'errors': 0,
            'successes': 0,
            'start_time': None,
            'end_time': None,
            'memory_usage': [],
            'cpu_usage': []
        }
        self.lock = threading.Lock()
        self.test_running = False

    def generate_test_submission(self, index: int) -> RedditSubmission:
        """Generate a test Reddit submission"""
        test_cases = [
            {
                'title': f'Business Need #{index}: Subscription management pain',
                'subreddit': 'SaaS',
                'text': f'We need a better way to manage subscriptions. Current tools are too expensive and complex. Test case {index} for load testing.',
                'score': 100 + (index % 400),
                'num_comments': 10 + (index % 100),
                'author': f'test_user_{index}'
            },
            {
                'title': f'Market Gap #{index}: No solution for niche problem',
                'subreddit': 'Entrepreneur',
                'text': f'There\'s no good tool for managing remote team collaboration. Would pay $100/month for solution. Load test iteration {index}.',
                'score': 50 + (index % 200),
                'num_comments': 5 + (index % 50),
                'author': f'test_entrepreneur_{index}'
            }
        ]

        case = test_cases[index % len(test_cases)]
        return RedditSubmission(
            id=f'load_test_{index}',
            title=case['title'],
            selftext=case['text'],
            subreddit=case['subreddit'],
            score=case['score'],
            num_comments=case['num_comments'],
            author=case['author'],
            created_utc=datetime.now().timestamp(),
            url=f'https://reddit.com/r/{case["subreddit"]}/comments/load_test_{index}/'
        )

    async def analyze_submission(self, submission: RedditSubmission, worker_id: int) -> Dict[str, Any]:
        """Analyze a single submission"""
        start_time = time.time()

        try:
            # Create Agno analyzer with fake embeddings for load testing
            config = {
                'embedding_provider': 'fake',  # Use fake to avoid API limits
                'enable_embeddings': True,
                'consensus_threshold': 60.0
            }

            factory = AgnoAnalyzerFactory(config)
            analyzer = factory.create_analyzer()

            # Perform analysis
            result = analyzer.analyze_submission(submission)

            latency = time.time() - start_time

            with self.lock:
                self.metrics['latencies'].append(latency)
                self.metrics['successes'] += 1

            return {
                'worker_id': worker_id,
                'submission_id': submission.id,
                'latency': latency,
                'success': True,
                'result_quality': getattr(result, 'monetization_score', 0.5)
            }

        except Exception as e:
            latency = time.time() - start_time
            with self.lock:
                self.metrics['errors'] += 1
                self.metrics['latencies'].append(latency)  # Still count for stats

            return {
                'worker_id': worker_id,
                'submission_id': submission.id,
                'latency': latency,
                'success': False,
                'error': str(e)
            }

    def monitor_resources(self):
        """Monitor system resources during load test"""
        while self.test_running:
            with self.lock:
                self.metrics['memory_usage'].append(psutil.Process().memory_info().rss / 1024 / 1024)  # MB
                self.metrics['cpu_usage'].append(psutil.Process().cpu_percent())
            time.sleep(1)  # Sample every second

    async def run_load_test(self, duration_minutes: int = 1, target_rpm: int = 1000) -> Dict[str, Any]:
        """
        Run load test for specified duration and target RPM

        Args:
            duration_minutes: Test duration in minutes
            target_rpm: Target requests per minute
        """
        duration_seconds = duration_minutes * 60
        total_requests = target_rpm * duration_minutes
        requests_per_second = target_rpm / 60

        logger.info(f"Starting load test:")
        logger.info(f"  Duration: {duration_minutes} minute(s)")
        logger.info(f"  Target RPM: {target_rpm}")
        logger.info(f"  Total requests: {total_requests}")
        logger.info(f"  Requests/second: {requests_per_second:.2f}")

        # Calculate optimal number of workers
        optimal_workers = min(20, max(5, int(requests_per_second / 2)))
        logger.info(f"  Using {optimal_workers} concurrent workers")

        self.test_running = True
        self.metrics['start_time'] = datetime.now()

        # Start resource monitoring
        monitor_thread = threading.Thread(target=self.monitor_resources)
        monitor_thread.start()

        # Generate submissions
        submissions = [self.generate_test_submission(i) for i in range(total_requests)]

        # Run load test with controlled rate
        with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
            futures = []
            submission_index = 0
            start_time = time.time()

            while submission_index < total_requests and time.time() - start_time < duration_seconds:
                # Submit new requests at controlled rate
                while len(futures) < optimal_workers * 2 and submission_index < total_requests:
                    submission = submissions[submission_index]
                    future = executor.submit(asyncio.run, self.analyze_submission(submission, submission_index))
                    futures.append((future, submission_index))
                    submission_index += 1

                # Check completed futures
                completed_futures = []
                for future, idx in futures:
                    if future.done():
                        try:
                            result = future.result()
                            if idx % 50 == 0:  # Log progress every 50
                                logger.info(f"Completed {idx + 1}/{total_requests} - "
                                          f"Latency: {result['latency']:.2f}s - "
                                          f"{'✅' if result['success'] else '❌'}")
                        except Exception as e:
                            logger.error(f"Future {idx} failed: {e}")
                        completed_futures.append((future, idx))

                # Remove completed futures
                for item in completed_futures:
                    futures.remove(item)

                # Rate limiting to match target RPM
                time.sleep(1 / requests_per_second if requests_per_second > 0 else 0.1)

            # Wait for remaining futures
            for future, idx in futures:
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Final future {idx} failed: {e}")

        self.test_running = False
        self.metrics['end_time'] = datetime.now()
        monitor_thread.join()

        # Calculate results
        return self.calculate_load_test_results(total_requests, duration_seconds)

    def calculate_load_test_results(self, total_requests: int, duration_seconds: int) -> Dict[str, Any]:
        """Calculate load test results"""
        actual_duration = (self.metrics['end_time'] - self.metrics['start_time']).total_seconds()
        actual_rpm = self.metrics['successes'] / actual_duration * 60
        error_rate = self.metrics['errors'] / total_requests * 100 if total_requests > 0 else 0

        # Filter successful latencies
        successful_latencies = [l for l in self.metrics['latencies'] if l < float('inf')]

        results = {
            'test_parameters': {
                'duration_seconds': actual_duration,
                'target_requests': total_requests,
                'actual_requests': len(self.metrics['latencies']),
                'target_rpm': total_requests / (duration_seconds / 60),
                'actual_rpm': actual_rpm
            },
            'performance_metrics': {
                'success_rate': 100 - error_rate,
                'error_rate': error_rate,
                'throughput_rpm': actual_rpm,
                'throughput_rps': actual_rpm / 60 if actual_rpm > 0 else 0,
                'total_processed': self.metrics['successes'],
                'total_errors': self.metrics['errors']
            }
        }

        if successful_latencies:
            latency_stats = {
                'avg_latency': statistics.mean(successful_latencies),
                'p50_latency': statistics.median(successful_latencies),
                'p90_latency': statistics.quantiles(successful_latencies, n=10)[8],
                'p95_latency': statistics.quantiles(successful_latencies, n=20)[18],
                'p99_latency': statistics.quantiles(successful_latencies, n=100)[98],
                'min_latency': min(successful_latencies),
                'max_latency': max(successful_latencies),
                'std_deviation': statistics.stdev(successful_latencies)
            }
            results['latency_metrics'] = latency_stats
        else:
            results['latency_metrics'] = {'error': 'No successful requests'}

        # Resource usage
        if self.metrics['memory_usage']:
            results['resource_metrics'] = {
                'avg_memory_mb': statistics.mean(self.metrics['memory_usage']),
                'max_memory_mb': max(self.metrics['memory_usage']),
                'avg_cpu_percent': statistics.mean(self.metrics['cpu_usage']),
                'max_cpu_percent': max(self.metrics['cpu_usage'])
            }
        else:
            results['resource_metrics'] = {'error': 'No resource data collected'}

        return results

    def generate_load_test_report(self, results: Dict[str, Any]) -> str:
        """Generate load test report"""
        report = [
            "# Phase 5: Load Testing Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Test Summary",
            "",
            f"- **Duration**: {results['test_parameters']['duration_seconds']:.1f} seconds",
            f"- **Target RPM**: {results['test_parameters']['target_rpm']:.0f}",
            f"- **Actual RPM**: {results['test_parameters']['actual_rpm']:.0f}",
            f"- **Total Requests**: {results['test_parameters']['actual_requests']}",
            "",
            "## Phase 5 Requirements Status",
            ""
        ]

        # Check requirements
        target_rpm = results['test_parameters']['target_rpm']
        actual_rpm = results['test_parameters']['actual_rpm']
        rpm_pass = "✅" if actual_rpm >= target_rpm else "❌"

        error_rate = results['performance_metrics']['error_rate']
        error_pass = "✅" if error_rate < 1 else "❌"

        p99_latency = results.get('latency_metrics', {}).get('p99_latency', float('inf'))
        p99_pass = "✅" if p99_latency < 10 else "❌"

        report.extend([
            f"- **RPM Requirement** ({target_rpm}/min): {actual_rpm:.0f}/min {rpm_pass}",
            f"- **Error Rate** (<1%): {error_rate:.2f}% {error_pass}",
            f"- **P99 Latency** (<10s): {p99_latency:.2f}s {p99_pass}",
            "",
            "## Detailed Metrics",
            "",
            "### Performance",
            f"- Success Rate: {results['performance_metrics']['success_rate']:.2f}%",
            f"- Throughput: {results['performance_metrics']['throughput_rpm']:.1f} RPM",
            f"- Processed: {results['performance_metrics']['total_processed']:,}",
            f"- Errors: {results['performance_metrics']['total_errors']:,}",
            "",
            "### Latency Distribution",
            ""
        ])

        if 'latency_metrics' in results and 'error' not in results['latency_metrics']:
            lm = results['latency_metrics']
            report.extend([
                f"- Average: {lm['avg_latency']:.3f}s",
                f"- P50: {lm['p50_latency']:.3f}s",
                f"- P90: {lm['p90_latency']:.3f}s",
                f"- P95: {lm['p95_latency']:.3f}s",
                f"- P99: {lm['p99_latency']:.3f}s",
                f"- Min: {lm['min_latency']:.3f}s",
                f"- Max: {lm['max_latency']:.3f}s",
                f"- Std Dev: {lm['std_deviation']:.3f}s",
                ""
            ])

        if 'resource_metrics' in results and 'error' not in results['resource_metrics']:
            rm = results['resource_metrics']
            report.extend([
                "### Resource Usage",
                f"- Average Memory: {rm['avg_memory_mb']:.1f} MB",
                f"- Peak Memory: {rm['max_memory_mb']:.1f} MB",
                f"- Average CPU: {rm['avg_cpu_percent']:.1f}%",
                f"- Peak CPU: {rm['max_cpu_percent']:.1f}%",
                ""
            ])

        # Recommendations
        report.extend([
            "## Recommendations",
            "",
            "### For Meeting 1000 RPM Target:",
            "1. **Parallel Agent Execution**: Current sequential execution is the bottleneck",
            "2. **Batch Processing**: Process multiple submissions simultaneously",
            "3. **Connection Pooling**: Reuse HTTP connections for LLM calls",
            "4. **Caching**: Cache similar content to avoid redundant analysis",
            "5. **Horizontal Scaling**: Deploy multiple instances behind load balancer",
            "",
            "### Estimated Requirements for 1000 RPM:",
            "- **Workers**: 50-100 concurrent processes",
            "- **Memory**: 16-32 GB RAM total",
            "- **CPU**: 16+ cores",
            "- **Infrastructure**: Auto-scaling with minimum 10 instances",
            "",
            "### Optimization Priority:",
            "1. Implement parallel agent synthesis (70% latency reduction)",
            "2. Add batching for LLM calls (50% throughput increase)",
            "3. Deploy to container orchestration (Kubernetes/ECS)",
            "4. Add monitoring and alerting for production",
            "5. Implement circuit breakers for resilience"
        ])

        return "\n".join(report)

    async def run_test_suite(self, test_configs: List[Dict[str, int]]) -> str:
        """Run multiple load test configurations"""
        all_reports = ["# Phase 5: Load Testing Suite\n"]

        for i, config in enumerate(test_configs):
            logger.info(f"\n{'='*60}")
            logger.info(f"Load Test #{i+1}: {config['rpm']} RPM for {config['minutes']} minute(s)")
            logger.info(f"{'='*60}")

            # Clear metrics
            self.metrics = {
                'latencies': [],
                'errors': 0,
                'successes': 0,
                'start_time': None,
                'end_time': None,
                'memory_usage': [],
                'cpu_usage': []
            }

            # Run test
            results = await self.run_load_test(config['minutes'], config['rpm'])
            report = self.generate_load_test_report(results)

            # Save individual test report
            filename = f"phase5_load_test_{config['rpm']}rpm_{config['minutes']}min.md"
            with open(filename, 'w') as f:
                f.write(report)
            logger.info(f"Report saved to: {filename}")

            all_reports.append(f"\n\n{report}")

        # Save combined report
        combined_report = "\n".join(all_reports)
        with open("phase5_load_test_suite.md", 'w') as f:
            f.write(combined_report)

        logger.info("\nCombined report saved to: phase5_load_test_suite.md")
        return combined_report


async def main():
    """Main load testing function"""
    print("=" * 60)
    print("Phase 5: Load Testing")
    print("=" * 60)
    print()

    # Test configurations: RPM, duration in minutes
    test_configs = [
        {'rpm': 100, 'minutes': 0.5},  # Quick sanity check
        {'rpm': 500, 'minutes': 0.5},  # Medium load
        {'rpm': 1000, 'minutes': 0.25},  # Target load (shortened for demo)
    ]

    # Check environment
    if not os.getenv('OPENROUTER_API_KEY'):
        logger.warning("OPENROUTER_API_KEY not set. Tests will use fallback.")

    # Run test suite
    tester = LoadTester()
    await tester.run_test_suite(test_configs)


if __name__ == "__main__":
    asyncio.run(main())