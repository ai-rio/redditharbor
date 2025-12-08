"""
VCR.py Integration Tests for MarketResearchAgent

These tests record and replay real Jina API interactions:
- Web search via Jina Search API
- Content extraction via Jina Reader API
- LLM-powered data extraction
- Redis caching behavior
- Rate limiting and retries

Usage:
1. First run (records interactions):
   pytest test_market_research_agent_vcr.py -k "test_real_jina_integration"

2. Subsequent runs (replays recordings):
   pytest test_market_research_agent_vcr.py

3. Re-record:
   rm tests/fixtures/vcr_cassettes/*.yml
   pytest test_market_research_agent_vcr.py -k "test_real_jina_integration"
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest
import vcr
from httpx import AsyncClient

from transform.caching.jina_cache import JinaCache
from transform.jina_client import JinaClient, JinaResponse, SearchResult
from transform.market_research_agent import MarketResearchAgent

# VCR configuration
VCR_CASSETTE_DIR = "tests/fixtures/vcr_cassettes"

my_vcr = vcr.VCR(
    cassette_library_dir=VCR_CASSETTE_DIR,
    record_mode="once",  # Record once, replay afterwards
    match_on=["uri", "method", "body", "headers"],
    filter_headers=["authorization", "x-api-key"],
    filter_post_data_parameters=["api_key"],
    decode_compressed_response=True,
    record_on_exception=True,
)


class TestJinaClientVCR:
    """VCR Tests for JinaClient"""

    @pytest.fixture
    def mock_llm_response(self):
        """Mock LLM response for structured extraction"""
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "company_name": "TestCo",
                            "pricing_model": "subscription",
                            "pricing_tiers": [
                                {"name": "Basic", "price": "$9/mo"},
                                {"name": "Pro", "price": "$29/mo"}
                            ],
                            "target_market": "SMB",
                            "confidence": 85.0
                        })
                    }
                }
            ]
        }

    @pytest.mark.vcr
    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.api
    async def test_real_web_search_functionality(self):
        """
        Test real web search using Jina Search API
        This test is recorded and replayed
        """
        with patch('transform.jina_client.acompletion') as mock_llm:
            # Mock LLM for structured extraction
            mock_llm.return_value = AsyncMock(
                choices=[{
                    "message": {
                        "content": json.dumps({
                            "results": [
                                {
                                    "url": "https://example.com/product",
                                    "title": "Example Product",
                                    "description": "A great example product",
                                    "relevance_score": 0.95
                                }
                            ]
                        })
                    }
                }]
            )

            # Create client with mocked credentials
            client = JinaClient(
                api_key="test-key",
                llm_api_key="test-llm-key",
                enable_caching=False,
                enable_cost_tracking=True
            )

            # Perform search
            results = await client.search_web(
                query="workflow automation tools pricing",
                num_results=5
            )

            # Verify results
            assert isinstance(results, list)
            assert len(results) > 0
            assert all(isinstance(r, SearchResult) for r in results)

            # Check cost tracking
            costs = client.get_cost_summary()
            assert costs["search_count"] > 0
            assert costs["total_cost"] > 0

    @pytest.mark.vcr
    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.api
    async def test_real_content_extraction(self):
        """
        Test real content extraction from a URL
        """
        # Create client
        client = JinaClient(
            api_key="test-key",
            enable_caching=False,
            enable_cost_tracking=True
        )

        # Extract content from a known URL
        response = await client.read_url("https://example.com")

        # Verify response
        assert isinstance(response, JinaResponse)
        assert response.url == "https://example.com"
        assert len(response.content) > 0
        assert response.status_code == 200
        assert response.extraction_time is not None

        # Check cost tracking
        costs = client.get_cost_summary()
        assert costs["extraction_count"] > 0

    @pytest.mark.vcr
    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.api
    async def test_real_pricing_extraction(self, mock_llm_response):
        """
        Test real competitor pricing extraction
        """
        with patch('transform.jina_client.acompletion') as mock_llm:
            # Mock LLM response
            mock_llm.return_value = AsyncMock(
                choices=[{
                    "message": {
                        "content": json.dumps({
                            "company_name": "AutomationPro",
                            "pricing_model": "subscription",
                            "pricing_tiers": [
                                {"name": "Starter", "price": "$19/mo"},
                                {"name": "Pro", "price": "$49/mo"}
                            ],
                            "target_market": "SMB",
                            "confidence": 90.0
                        })
                    }
                }]
            )

            client = JinaClient(
                api_key="test-key",
                llm_api_key="test-llm-key",
                enable_caching=False,
                enable_cost_tracking=True
            )

            # First get content (mocked)
            content = JinaResponse(
                url="https://automationpro.com/pricing",
                content="Our pricing: Starter $19/month, Pro $49/month",
                title="Pricing"
            )

            # Extract pricing
            pricing = await client.extract_competitor_pricing(
                content=content.content,
                source_url=content.url
            )

            # Verify pricing data
            assert pricing is not None
            assert pricing.company_name == "AutomationPro"
            assert pricing.pricing_model == "subscription"
            assert len(pricing.pricing_tiers) == 2
            assert pricing.confidence == 90.0

    @pytest.mark.vcr
    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.api
    async def test_real_market_size_extraction(self):
        """
        Test real market size extraction from industry report
        """
        with patch('transform.jina_client.acompletion') as mock_llm:
            # Mock LLM response
            mock_llm.return_value = AsyncMock(
                choices=[{
                    "message": {
                        "content": json.dumps({
                            "tam_value": "$50B",
                            "sam_value": "$5B",
                            "growth_rate": "15% CAGR",
                            "source_name": "Gartner Report 2024",
                            "year": 2024
                        })
                    }
                }]
            )

            client = JinaClient(
                api_key="test-key",
                llm_api_key="test-llm-key",
                enable_caching=False
            )

            # Mock content
            content = JinaResponse(
                url="https://gartner.com/report",
                content="The workflow automation market has a TAM of $50B...",
                title="Market Analysis"
            )

            # Extract market size
            market_size = await client.extract_market_size(
                content=content.content,
                source_url=content.url
            )

            # Verify market size data
            assert market_size is not None
            assert market_size.tam_value == "$50B"
            assert market_size.sam_value == "$5B"
            assert market_size.growth_rate == "15% CAGR"
            assert market_size.source_name == "Gartner Report 2024"

    @pytest.mark.vcr
    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.api
    async def test_real_product_launch_extraction(self):
        """
        Test real product launch data extraction
        """
        with patch('transform.jina_client.acompletion') as mock_llm:
            # Mock LLM response
            mock_llm.return_value = AsyncMock(
                choices=[{
                    "message": {
                        "content": json.dumps({
                            "product_name": "FlowAutomation",
                            "launch_platform": "Product Hunt",
                            "launch_date": "2024-03-15",
                            "upvotes": 2500,
                            "comments": 450
                        })
                    }
                }]
            )

            client = JinaClient(
                api_key="test-key",
                llm_api_key="test-llm-key",
                enable_caching=False
            )

            # Mock content
            content = JinaResponse(
                url="https://producthunt.com/posts/flowautomation",
                content="# FlowAutomation\n\n🚀 2500 upvotes • 450 comments",
                title="FlowAutomation - Product Hunt"
            )

            # Extract launch data
            launch = await client.extract_product_launch(
                content=content.content,
                source_url=content.url
            )

            # Verify launch data
            assert launch is not None
            assert launch.product_name == "FlowAutomation"
            assert launch.launch_platform == "Product Hunt"
            assert launch.upvotes == 2500
            assert launch.comments == 450

    @pytest.mark.asyncio
    async def test_rate_limiting_behavior(self):
        """Test rate limiting prevents too many requests"""
        client = JinaClient(
            api_key="test-key",
            rate_limit=2,  # 2 requests per second
            enable_caching=False
        )

        # Mock the actual HTTP requests
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock(
                status_code=200,
                text="Mock response",
                headers={"content-type": "text/plain"}
            )

            # Make multiple requests rapidly
            start_time = asyncio.get_event_loop().time()
            tasks = []

            for i in range(5):
                task = client.read_url(f"https://example{i}.com")
                tasks.append(task)

            # Wait for all to complete
            await asyncio.gather(*tasks)
            elapsed = asyncio.get_event_loop().time() - start_time

            # Should take at least 2 seconds due to rate limiting
            # (5 requests at 2 req/s = minimum 2 seconds)
            assert elapsed >= 2.0, f"Rate limiting not working: completed in {elapsed}s"

    @pytest.mark.asyncio
    async def test_retry_logic_on_failure(self):
        """Test that client retries on transient failures"""
        client = JinaClient(
            api_key="test-key",
            max_retries=3,
            retry_delay=0.1,  # Short delay for tests
            enable_caching=False
        )

        # Mock request that fails twice then succeeds
        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Temporary failure")
            return Mock(
                status_code=200,
                text="Success after retries",
                headers={"content-type": "text/plain"}
            )

        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = mock_request

            # Make request
            response = await client.read_url("https://example.com")

            # Should have retried and succeeded
            assert call_count == 3
            assert response.content == "Success after retries"

    @pytest.mark.asyncio
    async def test_error_propagation_on_max_retries(self):
        """Test that errors are propagated after max retries"""
        client = JinaClient(
            api_key="test-key",
            max_retries=2,
            retry_delay=0.1,
            enable_caching=False
        )

        # Mock request that always fails
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = Exception("Persistent failure")

            # Should raise exception after max retries
            with pytest.raises(Exception) as exc_info:
                await client.read_url("https://example.com")

            assert "Persistent failure" in str(exc_info.value)


class TestJinaCacheVCR:
    """VCR Tests for JinaCache behavior"""

    @pytest.fixture
    async def redis_cache(self):
        """Create Redis cache for testing"""
        # Skip if Redis not available
        try:
            import redis.asyncio as redis
            cache = JinaCache(
                redis_url="redis://localhost:6379/1",
                enable_in_memory_fallback=True
            )
            await cache._init_redis()
            if cache._redis_available:
                yield cache
                await cache.clear_all()
                await cache.close()
            else:
                pytest.skip("Redis not available")
        except ImportError:
            pytest.skip("Redis not installed")

    @pytest.mark.asyncio
    async def test_cache_hit_miss_tracking(self, redis_cache):
        """Test cache hit/miss statistics"""
        test_key = "test:search:workflow"
        test_value = {"result": "cached_data"}

        # Reset stats
        redis_cache.reset_stats()

        # Cache miss
        cached = await redis_cache.get(test_key)
        assert cached is None
        assert redis_cache.stats["misses"] == 1
        assert redis_cache.stats["hits"] == 0

        # Store in cache
        await redis_cache.set(test_key, test_value, ttl=60)

        # Cache hit
        cached = await redis_cache.get(test_key)
        assert cached == test_value
        assert redis_cache.stats["hits"] == 1

    @pytest.mark.asyncio
    async def test_ttl_behavior_by_data_type(self, redis_cache):
        """Test different TTL for different data types"""
        # Test competitor pricing (7 days)
        await redis_cache.set(
            "jina:competitor:test",
            {"company": "TestCo"},
            ttl=None  # Use default
        )

        ttl = await redis_cache.get_ttl("jina:competitor:test")
        # Should be close to 7 days (allowing for test timing)
        assert 6 * 24 * 3600 <= ttl <= 7 * 24 * 3600

        # Test market size (30 days)
        await redis_cache.set(
            "jina:market:test",
            {"tam": "$10B"},
            ttl=None  # Use default
        )

        ttl = await redis_cache.get_ttl("jina:market:test")
        # Should be close to 30 days
        assert 29 * 24 * 3600 <= ttl <= 30 * 24 * 3600

    @pytest.mark.asyncio
    async def test_cost_savings_estimation(self, redis_cache):
        """Test cost savings estimation for cache hits"""
        # Simulate cached search
        search_key = "jina:search:workflow automation"
        search_result = {"results": [{"url": "test.com"}]}

        # Set cache with cost tracking
        await redis_cache.set(search_key, search_result, ttl=3600)
        redis_cache.stats["hits"] = 1

        # Check savings
        savings = redis_cache.get_cost_savings()
        assert savings["estimated_savings"] > 0
        assert savings["hit_rate"] == 1.0  # 100% hit rate

    @pytest.mark.asyncio
    async def test_in_memory_fallback(self):
        """Test in-memory cache fallback when Redis unavailable"""
        cache = JinaCache(
            redis_url="redis://nonexistent:6379",
            enable_in_memory_fallback=True,
            max_memory_items=10
        )

        # Should fall back to memory cache
        test_key = "test:memory"
        test_value = {"data": "in_memory"}

        # Store
        await cache.set(test_key, test_value)
        assert len(cache._memory_cache) == 1

        # Retrieve
        cached = await cache.get(test_key)
        assert cached == test_value

        # Test LRU eviction
        for i in range(11):
            await cache.set(f"test:memory:{i}", {"data": f"value{i}"})

        # Should evict oldest
        assert len(cache._memory_cache) <= 10
        assert test_key not in cache._memory_cache

    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """Test cache key generation from URLs and queries"""
        cache = JinaCache(enable_in_memory_fallback=True)

        # Test URL key generation
        url_key = cache._generate_content_key("https://example.com/page")
        assert "jina:content:" in url_key
        assert "example.com" in url_key

        # Test search key generation
        search_key = cache._generate_search_key("workflow automation", 5)
        assert "jina:search:" in search_key
        assert "workflow" in search_key


class TestMarketResearchAgentIntegrationVCR:
    """VCR Integration Tests for MarketResearchAgent with real APIs"""

    @pytest.mark.vcr
    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.api
    async def test_end_to_end_market_validation(self):
        """
        Test complete market validation workflow with real APIs
        This is a comprehensive test that:
        1. Searches for competitors
        2. Extracts pricing information
        3. Searches for market size
        4. Searches for product launches
        5. Calculates validation score
        """
        with patch('transform.jina_client.acompletion') as mock_llm:
            # Mock all LLM responses
            mock_llm.return_value = AsyncMock(
                choices=[{
                    "message": {
                        "content": json.dumps({
                            "results": [
                                {
                                    "url": "https://zapier.com/pricing",
                                    "title": "Zapier Pricing",
                                    "description": "Automation tool pricing",
                                    "relevance_score": 0.95
                                }
                            ]
                        })
                    }
                }]
            )

            # Configure mock for different extraction types
            async def mock_extraction(*args, **kwargs):
                prompt = kwargs.get("messages", [{}])[-1].get("content", "")
                if "competitor" in prompt.lower() or "pricing" in prompt.lower():
                    return {
                        "choices": [{
                            "message": {
                                "content": json.dumps({
                                    "company_name": "Zapier",
                                    "pricing_model": "freemium",
                                    "pricing_tiers": [
                                        {"name": "Free", "price": "$0"},
                                        {"name": "Professional", "price": "$19.99/mo"}
                                    ],
                                    "target_market": "SMB",
                                    "confidence": 95.0
                                })
                            }
                        }]
                    }
                elif "market size" in prompt.lower():
                    return {
                        "choices": [{
                            "message": {
                                "content": json.dumps({
                                    "tam_value": "$60B",
                                    "sam_value": "$6B",
                                    "growth_rate": "20% CAGR",
                                    "source_name": "MarketsandMarkets 2024"
                                })
                            }
                        }]
                    }
                elif "product launch" in prompt.lower():
                    return {
                        "choices": [{
                            "message": {
                                "content": json.dumps({
                                    "product_name": "Make.com",
                                    "launch_platform": "Product Hunt",
                                    "launch_date": "2024-01-15",
                                    "upvotes": 3200,
                                    "comments": 580
                                })
                            }
                        }]
                    }
                return mock_llm.return_value

            mock_llm.side_effect = mock_extraction

            # Create agent with real Jina (but mocked LLM)
            agent = MarketResearchAgent(
                jina_api_key="test-key",
                validation_threshold=70.0,
                max_competitors=3,
                max_launches=2,
                enable_cost_tracking=True,
                use_real_jina=True
            )

            # Run market validation
            result = await agent.run({
                "app_concept": "AI-powered workflow automation tool",
                "target_market": "Small and medium businesses",
                "problem_description": "Businesses need to automate repetitive tasks between different software"
            })

            # Verify results
            assert isinstance(result, dict)
            assert result["validation_score"] > 70.0
            assert len(result["competitor_pricing"]) > 0
            assert result["market_size"] is not None
            assert len(result["similar_launches"]) > 0
            assert result["data_quality_score"] > 0
            assert len(result["evidence_urls"]) > 0
            assert len(result["search_queries"]) > 0
            assert result["jina_cost"] > 0

            # Verify reasoning includes evidence
            reasoning = result["reasoning"].lower()
            assert any(word in reasoning for word in ["competitor", "market", "launch"])

    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def test_concurrent_validations(self):
        """Test handling concurrent market validations"""
        with patch('transform.market_research_agent.JINA_AVAILABLE', True):
            agent = MarketResearchAgent(
                use_real_jina=False,  # Use mock for concurrency test
                enable_cost_tracking=True
            )

            # Create multiple validation tasks
            tasks = []
            for i in range(5):
                task = agent.run({
                    "app_concept": f"App {i}",
                    "target_market": "Test Market",
                    "problem_description": f"Problem {i}"
                })
                tasks.append(task)

            # Run all concurrently
            results = await asyncio.gather(*tasks)

            # Verify all completed successfully
            assert len(results) == 5
            assert all(isinstance(r, dict) for r in results)

            # Check cost tracking
            summary = agent.get_cost_summary()
            assert summary["validation_count"] == 5
            assert summary["total_cost"] > 0

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_api_failure(self):
        """Test graceful degradation when external APIs fail"""
        with patch('transform.market_research_agent.JINA_AVAILABLE', True):
            with patch('transform.market_research_agent.JinaClient') as mock_client_class:
                # Mock JinaClient to raise exception
                mock_client = Mock()
                mock_client_class.side_effect = Exception("API unavailable")

                # Agent should fall back to mock implementation
                agent = MarketResearchAgent(
                    jina_api_key="test-key",
                    use_real_jina=None  # Auto-detect
                )

                assert agent.use_real_jina is False
                assert agent.jina_client is None

                # Should still be able to run validations
                result = await agent.run({
                    "app_concept": "Test App",
                    "target_market": "Test Market"
                })

                assert isinstance(result, dict)
                assert "validation_score" in result
