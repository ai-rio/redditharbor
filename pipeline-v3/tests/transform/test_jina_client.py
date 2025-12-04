"""
Test suite for Jina client architecture and caching

This test suite validates the Jina client implementation for Phase 3 Market Research Integration.
Tests include:
- Jina client initialization
- Web search functionality
- Content extraction
- LLM-powered data extraction
- Redis caching
- Cost tracking
- Rate limiting
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

# Import test configuration
from config.settings import Settings, get_settings

# Import Jina components
try:
    from transform.jina_client import (
        JinaClient,
        SearchResult,
        JinaResponse,
        CostTracking,
        JinaClientConfig
    )
    from transform.caching.jina_cache import JinaCache, get_jina_cache
    from transform.validation_evidence_pydantic import (
        CompetitorPricing,
        MarketSizeData,
        ProductLaunchData
    )
    JINA_AVAILABLE = True
except ImportError:
    JINA_AVAILABLE = False

from transform.market_research_agent import MarketResearchAgent


@pytest.mark.skipif(not JINA_AVAILABLE, reason="Jina client not available")
class TestJinaClient:
    """Test Jina client functionality"""

    @pytest.fixture
    async def jina_client(self):
        """Create Jina client for testing"""
        client = JinaClient(
            api_key="test_key",
            llm_model="test-model",
            llm_api_key="test_llm_key",
            enable_caching=False,  # Disable caching for unit tests
            enable_cost_tracking=True,
            rate_limit=5,  # Lower for tests
            timeout=10.0
        )
        yield client
        await client.close()

    @pytest.mark.asyncio
    async def test_jina_client_initialization(self, jina_client):
        """Test Jina client initialization"""
        assert jina_client.api_key == "test_key"
        assert jina_client.llm_model == "test-model"
        assert jina_client.enable_caching is False
        assert jina_client.enable_cost_tracking is True
        assert jina_client.rate_limit == 5
        assert isinstance(jina_client.cost_tracking, CostTracking)

    @pytest.mark.asyncio
    async def test_web_search_mock(self, jina_client):
        """Test web search with mock response"""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {
                    "url": "https://example.com",
                    "title": "Example Page",
                    "description": "Test description",
                    "score": 0.9
                }
            ]
        }

        # Patch HTTP client
        with patch.object(jina_client.http_client, 'get', return_value=mock_response):
            results = await jina_client.search_web("test query", num_results=1)

        assert len(results) == 1
        assert results[0].url == "https://example.com"
        assert results[0].title == "Example Page"
        assert results[0].description == "Test description"
        assert results[0].relevance_score == 0.9

        # Check cost tracking
        assert jina_client.cost_tracking.search_count == 1
        assert jina_client.cost_tracking.search_cost == JinaClientConfig.DEFAULT_SEARCH_COST

    @pytest.mark.asyncio
    async def test_content_extraction_mock(self, jina_client):
        """Test content extraction with mock response"""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": "Test content",
            "title": "Test Title"
        }

        # Patch HTTP client
        with patch.object(jina_client.http_client, 'get', return_value=mock_response):
            content = await jina_client.read_url("https://example.com")

        assert content.url == "https://example.com"
        assert content.content == "Test content"
        assert content.title == "Test Title"
        assert content.status_code == 200

        # Check cost tracking
        assert jina_client.cost_tracking.extraction_count == 1
        assert jina_client.cost_tracking.extraction_cost == JinaClientConfig.DEFAULT_EXTRACTION_COST

    @pytest.mark.asyncio
    async def test_pricing_extraction_mock(self, jina_client):
        """Test competitor pricing extraction with mock LLM"""
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='''{
                "company_name": "TestCompany",
                "pricing_model": "subscription",
                "pricing_tiers": [
                    {"name": "Basic", "price": "$10/mo"}
                ],
                "target_market": "B2B",
                "confidence": 85.0
            }'''))
        ]

        # Patch LLM completion
        with patch('transform.jina_client.acompletion', return_value=mock_response):
            pricing = await jina_client.extract_competitor_pricing(
                content="Test content with pricing info",
                source_url="https://example.com/pricing"
            )

        assert pricing is not None
        assert pricing.company_name == "TestCompany"
        assert pricing.pricing_model == "subscription"
        assert len(pricing.pricing_tiers) == 1
        assert pricing.pricing_tiers[0]["name"] == "Basic"
        assert pricing.target_market == "B2B"
        assert pricing.confidence == 85.0

    @pytest.mark.asyncio
    async def test_cost_summary(self, jina_client):
        """Test cost summary functionality"""
        # Simulate some API calls
        jina_client.cost_tracking.search_count = 10
        jina_client.cost_tracking.search_cost = 0.001
        jina_client.cost_tracking.extraction_count = 20
        jina_client.cost_tracking.extraction_cost = 0.004
        jina_client.cost_tracking.llm_count = 5
        jina_client.cost_tracking.llm_cost = 0.00125
        jina_client.cost_tracking.total_cost = 0.00625

        summary = jina_client.get_cost_summary()

        assert summary["total_cost"] == 0.00625
        assert summary["search_cost"] == 0.001
        assert summary["extraction_cost"] == 0.004
        assert summary["llm_cost"] == 0.00125
        assert summary["search_queries"] == 10
        assert summary["urls_extracted"] == 20
        assert summary["llm_calls"] == 5
        assert summary["average_cost_per_search"] == 0.0001
        assert summary["average_cost_per_extraction"] == 0.0002


@pytest.mark.skipif(not JINA_AVAILABLE, reason="Jina cache not available")
class TestJinaCache:
    """Test Jina caching functionality"""

    @pytest.fixture
    async def jina_cache(self):
        """Create Jina cache for testing"""
        # Use in-memory cache only for testing
        cache = JinaCache(
            redis_url="memory://",
            enable_in_memory_fallback=True,
            max_memory_items=100
        )
        yield cache
        await cache.close()

    @pytest.mark.asyncio
    async def test_cache_key_generation(self, jina_cache):
        """Test cache key generation"""
        key1 = jina_cache._generate_cache_key(
            "competitor_pricing",
            "Project Management Tool",
            "B2B"
        )
        key2 = jina_cache._generate_cache_key(
            "competitor_pricing",
            "Project Management Tool",
            "B2B"
        )
        key3 = jina_cache._generate_cache_key(
            "competitor_pricing",
            "Different Tool",
            "B2B"
        )

        assert key1 == key2  # Same inputs should generate same key
        assert key1 != key3  # Different inputs should generate different key
        assert key1.startswith("jina:competitor:")  # Should have correct prefix

    @pytest.mark.asyncio
    async def test_cache_set_get(self, jina_cache):
        """Test cache set and get operations"""
        test_data = {
            "company_name": "TestCompany",
            "pricing": {"tier": "$10/mo"}
        }

        # Set data
        await jina_cache.set(
            data_type="competitor_pricing",
            app_concept="Test App",
            data=test_data
        )

        # Get data
        cached_data = await jina_cache.get(
            data_type="competitor_pricing",
            app_concept="Test App"
        )

        assert cached_data == test_data

        # Test miss
        miss_data = await jina_cache.get(
            data_type="competitor_pricing",
            app_concept="Nonexistent App"
        )
        assert miss_data is None

    @pytest.mark.asyncio
    async def test_cache_stats(self, jina_cache):
        """Test cache statistics"""
        # Set some data
        await jina_cache.set(
            data_type="web_search",
            app_concept="Test",
            data={"results": []}
        )

        # Get data (hit)
        await jina_cache.get(
            data_type="web_search",
            app_concept="Test"
        )

        # Get nonexistent data (miss)
        await jina_cache.get(
            data_type="web_search",
            app_concept="Missing"
        )

        stats = await jina_cache.get_stats()
        # Memory cache uses fallback_hits since Redis isn't available in tests
        assert stats["fallback_hits"] == 1
        assert stats["misses"] == 1
        assert stats["sets"] == 1
        assert stats["hit_rate_percent"] == 50.0


@pytest.mark.skipif(not JINA_AVAILABLE, reason="Market research agent not available")
class TestMarketResearchAgent:
    """Test MarketResearchAgent with Jina integration"""

    @pytest.fixture
    def test_settings(self):
        """Create test settings"""
        return Settings.create_for_testing(
            jina_api_key="test_jina_key",
            jina_enable_cache=True,
            jina_enable_cost_tracking=True
        )

    @pytest.mark.asyncio
    async def test_agent_initialization_with_jina(self, test_settings):
        """Test agent initialization with Jina client"""
        with patch('transform.market_research_agent.get_settings', return_value=test_settings):
            agent = MarketResearchAgent(
                jina_api_key="test_jina_key",
                use_real_jina=True
            )

        assert agent.use_real_jina is True
        assert agent.jina_client is not None
        assert agent.jina_client.api_key == "test_jina_key"

        await agent.close()

    @pytest.mark.asyncio
    async def test_agent_fallback_to_mock(self):
        """Test agent falls back to mock when Jina not available"""
        agent = MarketResearchAgent(
            jina_api_key=None,  # No API key
            use_real_jina=True  # Force real mode
        )

        assert agent.use_real_jina is False
        assert agent.jina_client is None

        await agent.close()

    @pytest.mark.asyncio
    async def test_should_validate_opportunity(self):
        """Test opportunity validation logic"""
        agent = MarketResearchAgent(validation_threshold=70.0)

        # Test above threshold
        assert agent.should_validate_opportunity(75.0) is True

        # Test below threshold
        assert agent.should_validate_opportunity(65.0) is False

        # Test at threshold
        assert agent.should_validate_opportunity(70.0) is True

        await agent.close()

    @pytest.mark.asyncio
    async def test_mock_market_validation(self):
        """Test mock market validation (without real Jina)"""
        agent = MarketResearchAgent(use_real_jina=False)

        input_data = {
            "app_concept": "Project Management Tool",
            "target_market": "B2B",
            "problem_description": "Teams struggle with project coordination"
        }

        result = await agent.run(input_data)

        # Check result structure
        assert "competitor_pricing" in result
        assert "market_size" in result
        assert "similar_launches" in result
        assert "validation_score" in result
        assert "data_quality_score" in result
        assert "reasoning" in result
        assert "evidence_urls" in result
        assert "search_queries" in result
        assert "jina_cost" in result

        # Check mock data exists
        assert len(result["competitor_pricing"]) > 0
        assert result["market_size"] is not None
        assert len(result["similar_launches"]) > 0
        assert result["validation_score"] > 0

        await agent.close()


@pytest.mark.skipif(not JINA_AVAILABLE, reason="Jina integration not available")
class TestJinaIntegration:
    """Integration tests for Jina client with caching"""

    @pytest.mark.asyncio
    async def test_end_to_end_market_research_mock(self):
        """Test end-to-end market research flow with mocked Jina APIs"""
        # Create agent with mock Jina (provide API key to enable real mode)
        agent = MarketResearchAgent(
            jina_api_key="test_api_key",  # Enable real mode
            use_real_jina=True,
            validation_threshold=70.0,
            max_competitors=3,
            max_launches=2
        )

        # Mock all Jina API calls
        with patch.object(agent.jina_client, 'search_web') as mock_search, \
             patch.object(agent.jina_client, 'read_url') as mock_read, \
             patch.object(agent.jina_client, 'extract_competitor_pricing') as mock_pricing, \
             patch.object(agent.jina_client, 'extract_market_size') as mock_market, \
             patch.object(agent.jina_client, 'extract_product_launch') as mock_launch, \
             patch.object(agent.jina_client, 'get_cost_summary') as mock_cost_summary:

            # Mock search results
            mock_search.return_value = [
                SearchResult(url="https://competitor1.com", title="Competitor 1", description=""),
                SearchResult(url="https://competitor2.com", title="Competitor 2", description="")
            ]

            # Mock content extraction
            mock_read.return_value = JinaResponse(
                url="https://competitor1.com",
                content="Pricing: $10/month Basic, $25/month Pro"
            )

            # Mock data extraction (return dictionaries for compatibility)
            mock_pricing.return_value = {
                "company_name": "Competitor 1",
                "pricing_model": "subscription",
                "pricing_tiers": [{"name": "Basic", "price": "$10/mo"}],
                "target_market": "B2B",
                "source_url": "https://competitor1.com",
                "confidence": 85.0
            }

            mock_market.return_value = {
                "tam_value": "$10B",
                "sam_value": "$1B",
                "growth_rate": "15% CAGR",
                "source_name": "Market Report 2024",
                "source_url": "https://marketreport.com",
                "year": 2024
            }

            mock_launch.return_value = {
                "product_name": "Similar App",
                "launch_platform": "Product Hunt",
                "launch_date": "2024-01-15",
                "upvotes": 500,
                "comments": 100,
                "source_url": "https://producthunt.com"
            }

            # Mock cost summary to return realistic costs
            mock_cost_summary.return_value = {
                "total_cost": 0.0009,
                "extraction_count": 2,
                "extraction_cost": 0.0006,
                "search_count": 1,
                "search_cost": 0.0003,
                "validation_count": 1
            }

            # Run market research
            input_data = {
                "app_concept": "Project Management Tool",
                "target_market": "B2B",
                "problem_description": "Teams need better coordination"
            }

            result = await agent.run(input_data)

            # Verify results
            assert result["validation_score"] > 0
            assert len(result["competitor_pricing"]) == 2
            assert result["market_size"] is not None
            assert len(result["similar_launches"]) == 2

            # Verify cost tracking
            cost_summary = agent.get_cost_summary()
            assert cost_summary["total_cost"] > 0

        await agent.close()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])