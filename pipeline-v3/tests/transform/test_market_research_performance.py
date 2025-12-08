"""
Performance Tests for MarketResearchAgent

These tests benchmark:
- Market validation performance
- Caching effectiveness
- Cost tracking accuracy
- Concurrent request handling
- Memory usage profiling
- Response time distributions
"""

import asyncio
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import psutil
import pytest

from transform.caching.jina_cache import JinaCache
from transform.jina_client import JinaClient
from transform.market_research_agent import MarketResearchAgent


@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    total_time: float
    avg_time_per_request: float
    min_time: float
    max_time: float
    p50: float  # 50th percentile
    p95: float  # 95th percentile
    p99: float  # 99th percentile
    requests_per_second: float
    memory_usage_mb: float
    cost_efficiency: float  # validations per dollar


class TestMarketResearchPerformance:
    """Performance testing for MarketResearchAgent"""

    @pytest.fixture
    def agent(self):
        """Create agent for performance testing"""
        with patch('transform.market_research_agent.JINA_AVAILABLE', True):
            with patch('transform.market_research_agent.JinaClient'):
                with patch('transform.market_research_agent.get_jina_cache'):
                    return MarketResearchAgent(
                        validation_threshold=70.0,
                        max_competitors=5,
                        max_launches=3,
                        enable_cost_tracking=True,
                        use_real_jina=False  # Use mock for performance tests
                    )

    @pytest.fixture
    def cache(self):
        """Create cache for performance testing"""
        return JinaCache(
            redis_url="redis://localhost:6379/2",
            enable_in_memory_fallback=True,
            max_memory_items=1000
        )

    def measure_performance(self, func, *args, **kwargs) -> tuple[Any, PerformanceMetrics]:
        """Measure performance metrics for a function"""
        # Measure memory before
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB

        # Run the function with timing
        times = []
        results = []

        if kwargs.get('iterations', 1) > 1:
            for _ in range(kwargs['iterations']):
                start = time.perf_counter()
                result = func(*args)
                end = time.perf_counter()
                times.append(end - start)
                results.append(result)
        else:
            start = time.perf_counter()
            result = func(*args)
            end = time.perf_counter()
            times = [end - start]
            results = [result]

        # Measure memory after
        mem_after = process.memory_info().rss / 1024 / 1024  # MB

        # Calculate metrics
        times_array = np.array(times)
        metrics = PerformanceMetrics(
            total_time=sum(times),
            avg_time_per_request=np.mean(times_array),
            min_time=np.min(times_array),
            max_time=np.max(times_array),
            p50=np.percentile(times_array, 50),
            p95=np.percentile(times_array, 95),
            p99=np.percentile(times_array, 99),
            requests_per_second=len(times) / sum(times) if sum(times) > 0 else 0,
            memory_usage_mb=mem_after - mem_before,
            cost_efficiency=0  # Will be calculated later
        )

        return results[0] if len(results) == 1 else results, metrics

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_market_validation_performance(self, agent):
        """Benchmark market validation performance"""
        # Prepare test data
        test_cases = [
            {
                "app_concept": f"Workflow automation tool {i}",
                "target_market": "Small businesses",
                "problem_description": "Need to automate repetitive tasks"
            }
            for i in range(100)
        ]

        # Benchmark single validation
        single_result, single_metrics = self.measure_performance(
            agent.run, test_cases[0]
        )

        # Report single validation metrics
        print("\nSingle Validation Performance:")
        print(f"  Time: {single_metrics.avg_time_per_request:.3f}s")
        print(f"  Memory: {single_metrics.memory_usage_mb:.2f}MB")
        print(f"  Cost: ${agent.get_cost_summary()['total_cost']:.6f}")

        # Benchmark batch validation (sequential)
        start_batch = time.perf_counter()
        for test_case in test_cases[:10]:  # Run 10 for batch test
            await agent.run(test_case)
        batch_time = time.perf_counter() - start_batch

        # Calculate cost efficiency
        summary = agent.get_cost_summary()
        cost_efficiency = summary["validation_count"] / summary["total_cost"] if summary["total_cost"] > 0 else 0

        # Assertions
        assert single_metrics.avg_time_per_request < 1.0, "Single validation should be under 1 second"
        assert batch_time / 10 < 2.0, "Average batch time should be under 2 seconds"
        assert single_metrics.memory_usage_mb < 50, "Memory usage should be reasonable"
        assert cost_efficiency > 100, "Should achieve good cost efficiency"

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_concurrent_validation_performance(self, agent):
        """Benchmark concurrent market validations"""
        # Prepare test data
        test_cases = [
            {
                "app_concept": f"Concurrent test app {i}",
                "target_market": "Test Market",
                "problem_description": f"Test problem {i}"
            }
            for i in range(20)
        ]

        # Test different concurrency levels
        concurrency_levels = [1, 2, 5, 10]
        results = {}

        for concurrency in concurrency_levels:
            # Reset agent
            agent.reset_cost_tracking()

            # Create batches
            batches = [test_cases[i:i+concurrency] for i in range(0, len(test_cases), concurrency)]

            # Run validations concurrently
            start_time = time.perf_counter()
            all_results = []

            for batch in batches:
                tasks = [agent.run(test_case) for test_case in batch]
                batch_results = await asyncio.gather(*tasks)
                all_results.extend(batch_results)

            total_time = time.perf_counter() - start_time
            valid_results = len([r for r in all_results if r.get("validation_score", 0) > 0])

            results[concurrency] = {
                "time": total_time,
                "validations_per_second": valid_results / total_time,
                "total_cost": agent.get_cost_summary()["total_cost"],
                "valid_results": valid_results
            }

            print(f"\nConcurrency Level {concurrency}:")
            print(f"  Time: {total_time:.3f}s")
            print(f"  Validations/sec: {valid_results / total_time:.2f}")
            print(f"  Cost: ${agent.get_cost_summary()['total_cost']:.6f}")

        # Assertions
        assert results[5]["validations_per_second"] > results[1]["validations_per_second"] * 2, \
            "Higher concurrency should improve throughput"
        assert all(r["valid_results"] >= len(test_cases) * 0.9 for r in results.values()), \
            "Should maintain high success rate at all concurrency levels"

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_cache_performance(self, cache):
        """Benchmark caching performance"""
        # Test data
        test_data = [
            {"key": f"test:search:query{i}", "value": {"result": f"data{i}"}}
            for i in range(1000)
        ]

        # Benchmark cache writes
        write_times = []
        for item in test_data:
            start = time.perf_counter()
            await cache.set(item["key"], item["value"], ttl=3600)
            write_times.append(time.perf_counter() - start)

        # Benchmark cache reads (hits)
        read_times_hit = []
        for item in test_data:
            start = time.perf_counter()
            result = await cache.get(item["key"])
            read_times_hit.append(time.perf_counter() - start)
            assert result == item["value"]

        # Benchmark cache reads (misses)
        miss_times = []
        for i in range(100):
            start = time.perf_counter()
            result = await cache.get(f"nonexistent:{i}")
            miss_times.append(time.perf_counter() - start)
            assert result is None

        # Calculate metrics
        write_avg = np.mean(write_times)
        read_hit_avg = np.mean(read_times_hit)
        miss_avg = np.mean(miss_times)

        print("\nCache Performance:")
        print(f"  Write: {write_avg*1000:.3f}ms avg")
        print(f"  Read (hit): {read_hit_avg*1000:.3f}ms avg")
        print(f"  Read (miss): {miss_avg*1000:.3f}ms avg")
        print(f"  Hit rate: {cache.stats['hits'] / (cache.stats['hits'] + cache.stats['misses']) * 100:.1f}%")

        # Assertions
        assert write_avg < 0.01, "Cache writes should be under 10ms"
        assert read_hit_avg < 0.005, "Cache hits should be under 5ms"
        assert miss_avg < 0.005, "Cache misses should be under 5ms"
        assert cache.stats["hits"] > 900, "Should have high hit rate"

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_cost_tracking_performance(self, agent):
        """Test cost tracking doesn't significantly impact performance"""
        # Test with cost tracking enabled
        agent.enable_cost_tracking = True
        agent.reset_cost_tracking()

        start_time = time.perf_counter()
        for i in range(100):
            await agent.run({
                "app_concept": f"Cost test app {i}",
                "target_market": "Test Market"
            })
        time_with_tracking = time.perf_counter() - start_time

        summary_with = agent.get_cost_summary()

        # Test without cost tracking
        agent.enable_cost_tracking = False
        start_time = time.perf_counter()
        for i in range(100):
            await agent.run({
                "app_concept": f"Cost test app {i}",
                "target_market": "Test Market"
            })
        time_without_tracking = time.perf_counter() - start_time

        # Calculate overhead
        overhead = (time_with_tracking - time_without_tracking) / time_without_tracking * 100

        print("\nCost Tracking Overhead:")
        print(f"  With tracking: {time_with_tracking:.3f}s")
        print(f"  Without tracking: {time_without_tracking:.3f}s")
        print(f"  Overhead: {overhead:.1f}%")
        print(f"  Total cost tracked: ${summary_with['total_cost']:.6f}")

        # Assertions
        assert overhead < 10, "Cost tracking overhead should be under 10%"
        assert summary_with["validation_count"] == 100, "Should track all validations"
        assert summary_with["average_cost_per_validation"] > 0, "Should calculate average cost"

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_memory_efficiency(self, agent):
        """Test memory efficiency over many validations"""
        # Reset and measure baseline memory
        process = psutil.Process(os.getpid())
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run many validations
        memory_samples = [baseline_memory]

        for i in range(0, 1000, 100):
            # Run 100 validations
            for j in range(100):
                await agent.run({
                    "app_concept": f"Memory test app {i+j}",
                    "target_market": "Test Market",
                    "problem_description": "Test problem for memory efficiency"
                })

            # Measure memory
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)

            # Force garbage collection
            import gc
            gc.collect()

        # Analyze memory growth
        memory_growth = memory_samples[-1] - baseline_memory
        memory_per_validation = memory_growth / 1000

        print("\nMemory Efficiency:")
        print(f"  Baseline: {baseline_memory:.2f}MB")
        print(f"  Final: {memory_samples[-1]:.2f}MB")
        print(f"  Growth: {memory_growth:.2f}MB")
        print(f"  Per validation: {memory_per_validation*1024:.2f}KB")

        # Assertions
        assert memory_growth < 100, "Memory growth should be under 100MB for 1000 validations"
        assert memory_per_validation < 0.1, "Memory per validation should be under 100KB"

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_validation_score_calculation_performance(self, agent):
        """Benchmark validation score calculation"""
        # Create test evidence data
        competitor_data = [
            {
                "company_name": f"Competitor{i}",
                "pricing_model": "subscription",
                "confidence": 80.0 + i % 20
            }
            for i in range(100)
        ]

        market_data = {
            "tam_value": "$10B",
            "growth_rate": "15% CAGR",
            "source_name": "Test Source"
        }

        launch_data = [
            {
                "product_name": f"Product{i}",
                "upvotes": 100 + i * 10,
                "comments": 50 + i * 5
            }
            for i in range(50)
        ]

        # Benchmark score calculation
        iterations = 10000
        times = []

        for _ in range(iterations):
            start = time.perf_counter()
            agent._calculate_validation_score(
                competitor_pricing=competitor_data,
                market_size=market_data,
                similar_launches=launch_data
            )
            times.append(time.perf_counter() - start)

        # Calculate metrics
        times_array = np.array(times)
        avg_time = np.mean(times_array)
        p99_time = np.percentile(times_array, 99)

        print("\nScore Calculation Performance:")
        print(f"  Average: {avg_time*1000:.3f}ms")
        print(f"  P99: {p99_time*1000:.3f}ms")
        print(f"  Total for {iterations}: {sum(times):.3f}s")

        # Assertions
        assert avg_time < 0.001, "Score calculation should be under 1ms"
        assert p99_time < 0.005, "P99 score calculation should be under 5ms"

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_reasoning_generation_performance(self, agent):
        """Benchmark reasoning generation"""
        # Test data
        competitor_pricing = [
            {
                "company_name": f"Competitor{i}",
                "confidence": 80.0,
                "pricing_model": "subscription"
            }
            for i in range(20)
        ]

        market_size = {
            "tam_value": "$50B",
            "growth_rate": "20% CAGR",
            "source_name": "Gartner"
        }

        similar_launches = [
            {
                "product_name": f"Product{i}",
                "upvotes": 1000,
                "comments": 200
            }
            for i in range(10)
        ]

        # Benchmark reasoning generation
        iterations = 1000
        reasoning_lengths = []
        times = []

        for i in range(iterations):
            score = 50 + (i % 50)  # Vary scores

            start = time.perf_counter()
            reasoning = agent._generate_reasoning(
                competitor_pricing=competitor_pricing,
                market_size=market_size,
                similar_launches=similar_launches,
                validation_score=score
            )
            times.append(time.perf_counter() - start)
            reasoning_lengths.append(len(reasoning))

        # Calculate metrics
        avg_time = np.mean(times)
        avg_length = np.mean(reasoning_lengths)

        print("\nReasoning Generation Performance:")
        print(f"  Average time: {avg_time*1000:.3f}ms")
        print(f"  Average length: {avg_length:.0f} chars")
        print(f"  Chars per ms: {avg_length/(avg_time*1000):.0f}")

        # Assertions
        assert avg_time < 0.01, "Reasoning generation should be under 10ms"
        assert avg_length > 100, "Reasoning should have reasonable length"

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_data_conversion_performance(self, agent):
        """Benchmark data format conversion"""
        # Create mock evidence
        mock_evidence = Mock()
        mock_evidence.competitor_pricing = [
            Mock(
                company_name=f"Comp{i}",
                pricing_model="subscription",
                pricing_tiers=[{"name": "Pro", "price": "$29/mo"}],
                target_market="SMB",
                source_url=f"https://comp{i}.com",
                confidence=85.0
            )
            for i in range(50)
        ]
        mock_evidence.market_size = Mock(
            tam_value="$10B",
            sam_value="$1B",
            growth_rate="15% CAGR",
            source_name="Test Report"
        )
        mock_evidence.similar_launches = [
            Mock(
                product_name=f"Product{i}",
                launch_platform="Product Hunt",
                upvotes=500 + i * 10,
                comments=100 + i * 2,
                source_url=f"https://ph.com/p{i}"
            )
            for i in range(20)
        ]
        mock_evidence.validation_score = 75.0
        mock_evidence.data_quality_score = 80.0
        mock_evidence.reasoning = "Test reasoning"
        mock_evidence.urls_fetched = [f"https://example{i}.com" for i in range(70)]
        mock_evidence.search_queries_used = [f"query {i}" for i in range(30)]
        mock_evidence.total_cost = 0.01

        # Benchmark conversion
        iterations = 1000
        times = []

        for _ in range(iterations):
            start = time.perf_counter()
            result = agent._convert_evidence_to_dict(mock_evidence)
            times.append(time.perf_counter() - start)

            # Verify result
            assert len(result["competitor_pricing"]) == 50
            assert len(result["similar_launches"]) == 20
            assert len(result["evidence_urls"]) == 70
            assert len(result["search_queries"]) == 30

        # Calculate metrics
        avg_time = np.mean(times)

        print("\nData Conversion Performance:")
        print(f"  Average time: {avg_time*1000:.3f}ms")
        print(f"  Items processed: {50 + 20 + 70 + 30}")  # Total items converted

        # Assertions
        assert avg_time < 0.005, "Data conversion should be under 5ms"


class TestJinaClientPerformance:
    """Performance testing for JinaClient"""

    @pytest.fixture
    def client(self):
        """Create client for performance testing"""
        return JinaClient(
            api_key="test-key",
            enable_caching=True,
            enable_cost_tracking=True,
            rate_limit=100  # High limit for performance tests
        )

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_http_request_performance(self, client):
        """Benchmark HTTP request performance"""
        # Mock HTTP responses
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock(
                status_code=200,
                text="Test content",
                headers={"content-type": "text/plain"}
            )

            # Benchmark search requests
            urls = [f"https://example{i}.com" for i in range(100)]
            times = []

            for url in urls:
                start = time.perf_counter()
                await client.read_url(url)
                times.append(time.perf_counter() - start)

            # Calculate metrics
            avg_time = np.mean(times)
            requests_per_second = len(urls) / sum(times)

            print("\nHTTP Request Performance:")
            print(f"  Average time: {avg_time*1000:.3f}ms")
            print(f"  Requests/sec: {requests_per_second:.0f}")

            # Assertions
            assert avg_time < 0.1, "HTTP requests should be under 100ms"
            assert requests_per_second > 100, "Should achieve high throughput"

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_concurrent_http_performance(self, client):
        """Test concurrent HTTP request performance"""
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock(
                status_code=200,
                text="Test content",
                headers={"content-type": "text/plain"}
            )

            # Test different concurrency levels
            concurrency_levels = [10, 50, 100]
            results = {}

            for concurrency in concurrency_levels:
                urls = [f"https://example{i}.com" for i in range(concurrency)]

                start_time = time.perf_counter()
                tasks = [client.read_url(url) for url in urls]
                await asyncio.gather(*tasks)
                total_time = time.perf_counter() - start_time

                rps = concurrency / total_time
                results[concurrency] = {
                    "time": total_time,
                    "rps": rps
                }

                print(f"\nConcurrent Requests ({concurrency}):")
                print(f"  Time: {total_time:.3f}s")
                print(f"  Throughput: {rps:.0f} req/s")

            # Assertions
            assert results[50]["rps"] > results[10]["rps"] * 2, \
                "Higher concurrency should improve throughput"


class TestCachePerformance:
    """Detailed cache performance testing"""

    @pytest.fixture
    async def cache(self):
        """Create cache with Redis for testing"""
        try:
            cache = JinaCache(
                redis_url="redis://localhost:6379/3",
                enable_in_memory_fallback=True
            )
            await cache._init_redis()
            if cache._redis_available:
                # Clear cache before tests
                await cache.clear_all()
                yield cache
                await cache.close()
            else:
                pytest.skip("Redis not available")
        except Exception:
            pytest.skip("Redis not available")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_cache_scalability(self, cache):
        """Test cache performance with large datasets"""
        # Test different data sizes
        data_sizes = [100, 1000, 10000, 50000]
        results = {}

        for size in data_sizes:
            # Generate test data
            test_data = [
                {
                    "key": f"jina:test:{i}",
                    "value": {"data": "x" * 100, "index": i}  # 100 bytes each
                }
                for i in range(size)
            ]

            # Benchmark writes
            start_write = time.perf_counter()
            for item in test_data:
                await cache.set(item["key"], item["value"])
            write_time = time.perf_counter() - start_write

            # Benchmark reads
            start_read = time.perf_counter()
            for item in test_data:
                result = await cache.get(item["key"])
                assert result is not None
            read_time = time.perf_counter() - start_read

            # Calculate metrics
            write_rps = size / write_time
            read_rps = size / read_time

            results[size] = {
                "write_rps": write_rps,
                "read_rps": read_rps,
                "write_time": write_time,
                "read_time": read_time
            }

            print(f"\nCache Size: {size} items")
            print(f"  Write: {write_rps:.0f} ops/s ({write_time:.3f}s)")
            print(f"  Read: {read_rps:.0f} ops/s ({read_time:.3f}s)")

            # Clean up for next test
            await cache.clear_all()

        # Check performance degradation
        assert results[50000]["write_rps"] > 1000, "Should maintain >1000 write ops/s even at 50k items"
        assert results[50000]["read_rps"] > 5000, "Should maintain >5000 read ops/s even at 50k items"
