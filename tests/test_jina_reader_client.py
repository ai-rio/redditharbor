#!/usr/bin/env python3
"""
Unit tests for JinaReaderClient and MarketDataValidator

Tests:
- Rate limiter functionality
- Cache behavior
- URL reading (mocked)
- Search result parsing
- Market data extraction
"""

import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent_tools.jina_reader_client import (
    JinaReaderClient,
    JinaResponse,
    RateLimiter,
    SearchResult,
    get_jina_client,
)
from agent_tools.market_data_validator import (
    CompetitorPricing,
    MarketDataValidator,
    MarketSizeData,
    ProductLaunchData,
    ValidationEvidence,
)


class TestRateLimiter:
    """Tests for the RateLimiter class"""

    def test_initial_state(self):
        """Test that rate limiter starts with full capacity"""
        limiter = RateLimiter(max_requests_per_minute=10)
        assert limiter.get_remaining_requests() == 10

    def test_request_tracking(self):
        """Test that requests are tracked correctly"""
        limiter = RateLimiter(max_requests_per_minute=5)

        # Make 3 requests
        for _ in range(3):
            limiter.wait_if_needed()

        assert limiter.get_remaining_requests() == 2

    def test_rate_limit_window(self):
        """Test that requests expire after 60 seconds"""
        limiter = RateLimiter(max_requests_per_minute=2)

        # Make 2 requests
        limiter.wait_if_needed()
        limiter.wait_if_needed()

        # Should be at limit
        assert limiter.get_remaining_requests() == 0

        # Manually expire old requests
        limiter._request_times = [time.time() - 61]

        # Should have capacity again
        assert limiter.get_remaining_requests() == 2

    def test_remaining_requests_accuracy(self):
        """Test accurate remaining request count"""
        limiter = RateLimiter(max_requests_per_minute=100)

        for i in range(10):
            limiter.wait_if_needed()

        assert limiter.get_remaining_requests() == 90


class TestJinaResponse:
    """Tests for JinaResponse dataclass"""

    def test_word_count_calculation(self):
        """Test automatic word count calculation"""
        response = JinaResponse(
            content="This is a test with exactly eight words here",
            url="https://example.com",
        )
        assert response.word_count == 9

    def test_cached_flag(self):
        """Test cached flag is set correctly"""
        response = JinaResponse(content="test", url="https://example.com", cached=True)
        assert response.cached is True

    def test_timestamp_auto_set(self):
        """Test timestamp is automatically set"""
        response = JinaResponse(content="test", url="https://example.com")
        assert isinstance(response.timestamp, datetime)


class TestSearchResult:
    """Tests for SearchResult dataclass"""

    def test_search_result_creation(self):
        """Test SearchResult can be created"""
        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="This is a test snippet",
            position=1,
        )
        assert result.title == "Test Title"
        assert result.position == 1


class TestJinaReaderClient:
    """Tests for JinaReaderClient"""

    @pytest.fixture
    def client(self):
        """Create a JinaReaderClient instance"""
        return JinaReaderClient()

    def test_initialization(self, client):
        """Test client initializes correctly"""
        assert client.reader_base_url == "https://r.jina.ai/"
        assert client.search_base_url == "https://s.jina.ai/"
        assert client.timeout > 0
        assert isinstance(client.read_limiter, RateLimiter)
        assert isinstance(client.search_limiter, RateLimiter)

    def test_rate_limit_status(self, client):
        """Test rate limit status returns correct structure"""
        status = client.get_rate_limit_status()
        assert "read_remaining" in status
        assert "read_max" in status
        assert "search_remaining" in status
        assert "search_max" in status
        assert "cache_size" in status

    def test_cache_key_generation(self, client):
        """Test cache key is generated correctly"""
        url = "https://example.com/page"
        key = client._get_cache_key(url)
        assert key == f"read:{url}"

    def test_cache_check_empty(self, client):
        """Test cache check returns False when empty"""
        assert client._is_cached("read:https://example.com") is False

    def test_cache_check_expired(self, client):
        """Test cache check returns False for expired entries"""
        cache_key = "read:https://example.com"
        # Add an expired entry (timestamp > TTL)
        old_time = datetime.now(UTC) - timedelta(seconds=client._cache_ttl + 100)
        client._cache[cache_key] = JinaResponse(
            content="old", url="https://example.com", timestamp=old_time
        )
        assert client._is_cached(cache_key) is False

    def test_cache_check_valid(self, client):
        """Test cache check returns True for valid entries"""
        cache_key = "read:https://example.com"
        client._cache[cache_key] = JinaResponse(
            content="test", url="https://example.com"
        )
        assert client._is_cached(cache_key) is True

    def test_clear_cache(self, client):
        """Test cache clearing"""
        client._cache["key1"] = JinaResponse(content="1", url="url1")
        client._cache["key2"] = JinaResponse(content="2", url="url2")

        count = client.clear_cache()
        assert count == 2
        assert len(client._cache) == 0

    def test_parse_search_results_basic(self, client):
        """Test parsing basic search results in Jina format"""
        content = """[1] Title: Test Result 1
[1] URL Source: https://example.com/1
[1] Description: This is the first result snippet.

Some extra content here...

[2] Title: Test Result 2
[2] URL Source: https://example.com/2
[2] Description: This is the second result snippet."""

        results = client._parse_search_results(content)

        assert len(results) == 2
        assert results[0].title == "Test Result 1"
        assert results[0].url == "https://example.com/1"
        assert "first result" in results[0].snippet
        assert results[0].position == 1

        assert results[1].title == "Test Result 2"
        assert results[1].position == 2

    def test_parse_search_results_with_url_prefix(self, client):
        """Test parsing search results with old URL: prefix format"""
        content = """# Result With Prefix
URL: https://example.com/page
Some snippet text here."""

        results = client._parse_search_results(content)

        assert len(results) == 1
        assert results[0].url == "https://example.com/page"

    def test_parse_search_results_jina_format(self, client):
        """Test parsing actual Jina search response format"""
        content = """[1] Title: Spend Management Software
[1] URL Source: https://www.expensify.com/
[1] Description: Expensify simplifies expense tracking.
[1] Published Time: 2024-01-01T00:00:00+0000

Expensify's spend management software...

[2] Title: Top SaaS Tools
[2] URL Source: https://example.com/saas-tools
[2] Description: Overview of SaaS spend management tools."""

        results = client._parse_search_results(content)

        assert len(results) == 2
        assert results[0].title == "Spend Management Software"
        assert results[0].url == "https://www.expensify.com/"
        assert "simplifies" in results[0].snippet
        assert results[1].title == "Top SaaS Tools"

    def test_context_manager(self, client):
        """Test client works as context manager"""
        with client:
            status = client.get_rate_limit_status()
            assert status is not None

    def test_singleton_pattern(self):
        """Test get_jina_client returns singleton"""
        client1 = get_jina_client()
        client2 = get_jina_client()
        assert client1 is client2

    @patch("agent_tools.jina_reader_client.httpx.Client")
    def test_read_url_uses_cache(self, mock_httpx):
        """Test that cached responses are returned without API call"""
        client = JinaReaderClient()

        # Pre-populate cache
        cache_key = client._get_cache_key("https://example.com")
        client._cache[cache_key] = JinaResponse(
            content="cached content", url="https://example.com", title="Cached Title"
        )

        # Read URL - should use cache
        response = client.read_url("https://example.com", use_cache=True)

        assert response.cached is True
        assert response.content == "cached content"
        # HTTP client should not have been called for reading
        # (only initialized during __init__)

    def test_build_headers_without_api_key(self, client):
        """Test headers are built correctly without API key"""
        # Save original key
        original_key = client.api_key
        client.api_key = ""

        headers = client._build_headers()

        assert "Accept" in headers
        assert "User-Agent" in headers
        assert "Authorization" not in headers

        # Restore
        client.api_key = original_key

    def test_build_headers_with_api_key(self, client):
        """Test headers include authorization when API key is set"""
        client.api_key = "test_key_123"
        headers = client._build_headers()

        assert headers["Authorization"] == "Bearer test_key_123"


class TestMarketDataValidator:
    """Tests for MarketDataValidator"""

    @pytest.fixture
    def mock_jina_client(self):
        """Create a mock JinaReaderClient"""
        mock = Mock(spec=JinaReaderClient)
        mock.search_web = Mock(return_value=[])
        mock.read_url = Mock(
            return_value=JinaResponse(content="Test content", url="https://example.com")
        )
        return mock

    @pytest.fixture
    def validator(self, mock_jina_client):
        """Create a MarketDataValidator with mock client"""
        return MarketDataValidator(jina_client=mock_jina_client)

    def test_initialization(self, validator):
        """Test validator initializes correctly"""
        assert validator.llm_model is not None
        assert validator.total_tokens == 0
        assert validator.total_cost == 0.0

    def test_calculate_validation_score_empty(self):
        """Test validation score with no evidence"""
        evidence = ValidationEvidence()
        validator = MarketDataValidator.__new__(MarketDataValidator)
        score = validator._calculate_validation_score(evidence)
        assert score == 0.0

    def test_calculate_validation_score_with_competitors(self):
        """Test validation score with competitor data"""
        evidence = ValidationEvidence(
            competitor_pricing=[
                CompetitorPricing(
                    company_name="Competitor 1",
                    pricing_tiers=[],
                    pricing_model="subscription",
                    target_market="B2C",
                    source_url="https://example.com",
                    confidence=0.8,
                )
            ]
        )
        validator = MarketDataValidator.__new__(MarketDataValidator)
        score = validator._calculate_validation_score(evidence)
        # 15 points * 0.8 confidence = 12
        assert score >= 10.0

    def test_calculate_validation_score_with_market_size(self):
        """Test validation score with market size data"""
        evidence = ValidationEvidence(
            market_size=MarketSizeData(
                tam_value="$10 billion", growth_rate="15% CAGR", confidence=0.9
            )
        )
        validator = MarketDataValidator.__new__(MarketDataValidator)
        score = validator._calculate_validation_score(evidence)
        # 30 * 0.9 = 27
        assert score >= 25.0

    def test_calculate_data_quality_score_empty(self):
        """Test data quality score with no evidence"""
        evidence = ValidationEvidence()
        validator = MarketDataValidator.__new__(MarketDataValidator)
        score = validator._calculate_data_quality_score(evidence)
        assert score == 0.0

    def test_calculate_data_quality_score_full(self):
        """Test data quality score with complete evidence"""
        evidence = ValidationEvidence(
            competitor_pricing=[
                CompetitorPricing("C1", [], "sub", "B2C", "url1", confidence=0.8),
                CompetitorPricing("C2", [], "sub", "B2C", "url2", confidence=0.8),
                CompetitorPricing("C3", [], "sub", "B2C", "url3", confidence=0.8),
            ],
            market_size=MarketSizeData(
                tam_value="$10B", growth_rate="15% CAGR", confidence=0.9
            ),
            similar_launches=[ProductLaunchData("P1", "PH")],
            industry_benchmarks={"key": "value"},
        )
        validator = MarketDataValidator.__new__(MarketDataValidator)
        score = validator._calculate_data_quality_score(evidence)
        # 25 (competitors) + 10 (>=3) + 25 (market) + 10 (tam+growth) + 20 (launches) + 10 (benchmarks)
        assert score == 100.0

    def test_extract_market_keywords(self):
        """Test market keyword extraction"""
        validator = MarketDataValidator.__new__(MarketDataValidator)

        # Test expense tracking
        keywords = validator._extract_market_keywords("expense tracking app")
        assert "personal finance" in keywords.lower()

        # Test fitness app
        keywords = validator._extract_market_keywords("fitness workout tracker")
        assert "fitness" in keywords.lower()

        # Test project management
        keywords = validator._extract_market_keywords("task management tool")
        assert "project management" in keywords.lower()

    def test_generate_reasoning_no_data(self):
        """Test reasoning generation with no data"""
        evidence = ValidationEvidence()
        validator = MarketDataValidator.__new__(MarketDataValidator)
        reasoning = validator._generate_reasoning(evidence, "test app")

        assert "No competitor" in reasoning
        assert "No market size" in reasoning
        assert "WEAK" in reasoning

    def test_generate_reasoning_with_data(self):
        """Test reasoning generation with data"""
        evidence = ValidationEvidence(
            competitor_pricing=[
                CompetitorPricing(
                    "Acme Corp", [], "subscription", "B2C", "url", confidence=0.9
                )
            ],
            market_size=MarketSizeData(
                tam_value="$50 billion", growth_rate="20% CAGR", confidence=0.8
            ),
            similar_launches=[ProductLaunchData("Product1", "Product Hunt")],
            validation_score=75.0,
        )
        validator = MarketDataValidator.__new__(MarketDataValidator)
        reasoning = validator._generate_reasoning(evidence, "test app")

        assert "Acme Corp" in reasoning
        assert "$50 billion" in reasoning
        assert "Product Hunt" in reasoning
        assert "STRONG" in reasoning

    def test_get_industry_benchmarks_b2b(self):
        """Test B2B industry benchmarks"""
        validator = MarketDataValidator.__new__(MarketDataValidator)
        benchmarks = validator._get_industry_benchmarks("SaaS tool", "B2B")

        assert "avg_contract_value" in benchmarks
        assert "sales_cycle" in benchmarks
        assert "subscription" in str(benchmarks)

    def test_get_industry_benchmarks_b2c(self):
        """Test B2C industry benchmarks"""
        validator = MarketDataValidator.__new__(MarketDataValidator)
        benchmarks = validator._get_industry_benchmarks("consumer app", "B2C")

        assert "avg_arpu" in benchmarks
        assert "retention_benchmark" in benchmarks
        assert "freemium" in str(benchmarks)


class TestValidationEvidence:
    """Tests for ValidationEvidence dataclass"""

    def test_default_initialization(self):
        """Test ValidationEvidence has correct defaults"""
        evidence = ValidationEvidence()

        assert evidence.competitor_pricing == []
        assert evidence.market_size is None
        assert evidence.similar_launches == []
        assert evidence.industry_benchmarks == {}
        assert evidence.validation_score == 0.0
        assert evidence.data_quality_score == 0.0
        assert evidence.reasoning == ""
        assert isinstance(evidence.timestamp, datetime)
        assert evidence.total_cost == 0.0


class TestCompetitorPricing:
    """Tests for CompetitorPricing dataclass"""

    def test_creation(self):
        """Test CompetitorPricing can be created"""
        pricing = CompetitorPricing(
            company_name="Acme Corp",
            pricing_tiers=[
                {"tier": "Basic", "price": "$9.99/mo", "features": ["Feature 1"]}
            ],
            pricing_model="subscription",
            target_market="B2C",
            source_url="https://acme.com/pricing",
            confidence=0.85,
        )

        assert pricing.company_name == "Acme Corp"
        assert len(pricing.pricing_tiers) == 1
        assert pricing.pricing_model == "subscription"
        assert pricing.confidence == 0.85


class TestMarketSizeData:
    """Tests for MarketSizeData dataclass"""

    def test_creation_with_all_fields(self):
        """Test MarketSizeData with all fields"""
        data = MarketSizeData(
            tam_value="$100 billion",
            sam_value="$20 billion",
            som_value="$2 billion",
            growth_rate="25% CAGR",
            year=2024,
            source_url="https://report.com",
            source_name="Grand View Research",
            confidence=0.95,
        )

        assert data.tam_value == "$100 billion"
        assert data.sam_value == "$20 billion"
        assert data.som_value == "$2 billion"
        assert data.growth_rate == "25% CAGR"
        assert data.confidence == 0.95

    def test_creation_with_minimal_fields(self):
        """Test MarketSizeData with minimal fields"""
        data = MarketSizeData()

        assert data.tam_value is None
        assert data.sam_value is None
        assert data.year == 2024
        assert data.confidence == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
