"""
Jina API client for Phase 3 Market Research Integration

This module provides a comprehensive Jina API client with:
- Web search via Jina Search API
- Content extraction via Jina Reader API
- LLM-powered data extraction
- Redis caching with configurable TTL
- Cost tracking and rate limiting
- Error handling and retries
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from urllib.parse import quote

import httpx
from litellm import acompletion

from .caching.jina_cache import JinaCache, get_jina_cache
from .validation_evidence_pydantic import (
    CompetitorPricing,
    MarketSizeData,
    ProductLaunchData,
)

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Individual search result from Jina Search API"""
    url: str
    title: str
    description: str
    relevance_score: float | None = None


@dataclass
class JinaResponse:
    """Response from Jina Reader API"""
    url: str
    content: str
    title: str | None = None
    status_code: int = 200
    extraction_time: float | None = None


@dataclass
class CostTracking:
    """Cost tracking for Jina API usage"""
    search_cost: float = 0.0
    extraction_cost: float = 0.0
    llm_cost: float = 0.0
    total_cost: float = 0.0
    search_count: int = 0
    extraction_count: int = 0
    llm_count: int = 0


class JinaClientConfig:
    """Configuration for Jina client"""

    # API endpoints
    JINA_SEARCH_API = "https://s.jina.ai/http://"
    JINA_READER_API = "https://r.jina.ai/http://"

    # Default costs (USD)
    DEFAULT_SEARCH_COST = 0.0001  # per query (5 results)
    DEFAULT_EXTRACTION_COST = 0.0002  # per URL
    DEFAULT_LLM_COST = 0.00025  # per 1K tokens (approximate)

    # Rate limiting
    DEFAULT_RATE_LIMIT = 10  # requests per second
    DEFAULT_BURST_LIMIT = 20  # max burst requests

    # Retry configuration
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1.0  # seconds
    DEFAULT_RETRY_BACKOFF = 2.0

    # Request timeout
    DEFAULT_TIMEOUT = 30.0  # seconds


class JinaClient:
    """
    Comprehensive Jina API client with caching and cost tracking

    Features:
    - Web search with result ranking
    - Content extraction from URLs
    - LLM-powered structured data extraction
    - Redis caching with configurable TTL
    - Rate limiting and automatic retries
    - Comprehensive cost tracking
    - AgentOps integration support
    """

    def __init__(
        self,
        api_key: str | None = None,
        cache: JinaCache | None = None,
        llm_model: str = "anthropic/claude-haiku-4.5",
        llm_api_key: str | None = None,
        llm_base_url: str = "https://openrouter.ai/api/v1",
        enable_caching: bool = True,
        enable_cost_tracking: bool = True,
        cache_ttl: dict[str, int] | None = None,
        rate_limit: int | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        enable_agentops: bool = False
    ):
        """
        Initialize Jina client

        Args:
            api_key: Jina API key (if required)
            cache: JinaCache instance (will create if None)
            llm_model: LLM model for data extraction
            llm_api_key: API key for LLM service
            llm_base_url: Base URL for LLM API
            enable_caching: Enable response caching
            enable_cost_tracking: Enable cost tracking
            cache_ttl: Custom TTL values for cache
            rate_limit: Rate limit (requests per second)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            enable_agentops: Enable AgentOps tracking
        """
        self.api_key = api_key
        self.llm_model = llm_model
        self.llm_api_key = llm_api_key
        self.llm_base_url = llm_base_url
        self.enable_caching = enable_caching
        self.enable_cost_tracking = enable_cost_tracking
        self.enable_agentops = enable_agentops
        self.cache_ttl = cache_ttl

        # Configuration
        self.rate_limit = rate_limit or JinaClientConfig.DEFAULT_RATE_LIMIT
        self.timeout = timeout or JinaClientConfig.DEFAULT_TIMEOUT
        self.max_retries = max_retries or JinaClientConfig.DEFAULT_MAX_RETRIES
        self.retry_delay = JinaClientConfig.DEFAULT_RETRY_DELAY
        self.retry_backoff = JinaClientConfig.DEFAULT_RETRY_BACKOFF

        # Initialize cache
        self.cache = cache
        if enable_caching and not self.cache:
            asyncio.create_task(self._initialize_cache())

        # Initialize HTTP client
        self.http_client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20
            )
        )

        # Rate limiting
        self.last_request_time = 0.0
        self.request_times: list[float] = []

        # Cost tracking
        self.cost_tracking = CostTracking()

        logger.info(f"Jina client initialized (caching: {enable_caching}, cost tracking: {enable_cost_tracking})")

    async def _initialize_cache(self) -> None:
        """Initialize cache asynchronously"""
        try:
            self.cache = await get_jina_cache(default_ttl=self.cache_ttl)
            logger.info("Jina cache initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize cache: {str(e)}")
            self.enable_caching = False

    async def search_web(
        self,
        query: str,
        num_results: int = 5,
        use_cache: bool | None = None
    ) -> list[SearchResult]:
        """
        Search the web using Jina Search API

        Args:
            query: Search query
            num_results: Number of results to return (max 10)
            use_cache: Override default caching behavior

        Returns:
            List of search results

        Raises:
            Exception: If search fails after retries
        """
        use_cache = use_cache if use_cache is not None else self.enable_caching

        # Check cache first
        if use_cache and self.cache:
            cached_results = await self.cache.get(
                data_type="web_search",
                app_concept=query,
                additional_params={"num_results": num_results}
            )
            if cached_results:
                logger.debug(f"Search cache hit for query: {query}")
                return [SearchResult(**r) for r in cached_results]

        # Apply rate limiting
        await self._apply_rate_limit()

        # Prepare request
        encoded_query = quote(query)
        search_url = f"{JinaClientConfig.JINA_SEARCH_API}{encoded_query}"

        # Execute with retries
        results = None
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                response = await self.http_client.get(search_url)
                response.raise_for_status()

                # Parse response
                data = response.json()
                results = self._parse_search_results(data, num_results)

                # Cache results
                if use_cache and self.cache and results:
                    await self.cache.set(
                        data_type="web_search",
                        app_concept=query,
                        data=[asdict(r) for r in results],
                        additional_params={"num_results": num_results}
                    )

                # Track cost
                if self.enable_cost_tracking:
                    self.cost_tracking.search_cost += JinaClientConfig.DEFAULT_SEARCH_COST
                    self.cost_tracking.search_count += 1
                    self.cost_tracking.total_cost += JinaClientConfig.DEFAULT_SEARCH_COST

                logger.debug(f"Search successful: {len(results)} results for query: {query}")
                break

            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = self.retry_delay * (self.retry_backoff ** attempt)
                    logger.warning(f"Search attempt {attempt + 1} failed: {str(e)}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Search failed after {self.max_retries + 1} attempts: {str(e)}")

        if results is None:
            raise Exception(f"Search failed: {str(last_error)}")

        return results

    async def read_url(
        self,
        url: str,
        use_cache: bool | None = None
    ) -> JinaResponse:
        """
        Extract content from URL using Jina Reader API

        Args:
            url: URL to extract content from
            use_cache: Override default caching behavior

        Returns:
            Extracted content as JinaResponse

        Raises:
            Exception: If extraction fails after retries
        """
        use_cache = use_cache if use_cache is not None else self.enable_caching

        # Check cache first
        if use_cache and self.cache:
            cached_content = await self.cache.get(
                data_type="content_extraction",
                app_concept=url
            )
            if cached_content:
                logger.debug(f"Content cache hit for URL: {url}")
                return JinaResponse(**cached_content)

        # Apply rate limiting
        await self._apply_rate_limit()

        # Prepare request
        encoded_url = quote(url, safe='')
        reader_url = f"{JinaClientConfig.JINA_READER_API}{encoded_url}"

        # Execute with retries
        content = None
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                response = await self.http_client.get(reader_url)
                extraction_time = time.time() - start_time

                response.raise_for_status()

                # Parse response
                data = response.json()
                content = JinaResponse(
                    url=url,
                    content=data.get("content", ""),
                    title=data.get("title"),
                    status_code=response.status_code,
                    extraction_time=extraction_time
                )

                # Cache content
                if use_cache and self.cache:
                    await self.cache.set(
                        data_type="content_extraction",
                        app_concept=url,
                        data=asdict(content)
                    )

                # Track cost
                if self.enable_cost_tracking:
                    self.cost_tracking.extraction_cost += JinaClientConfig.DEFAULT_EXTRACTION_COST
                    self.cost_tracking.extraction_count += 1
                    self.cost_tracking.total_cost += JinaClientConfig.DEFAULT_EXTRACTION_COST

                logger.debug(f"Content extraction successful: {len(content.content)} chars from {url}")
                break

            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = self.retry_delay * (self.retry_backoff ** attempt)
                    logger.warning(f"Content extraction attempt {attempt + 1} failed: {str(e)}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Content extraction failed after {self.max_retries + 1} attempts: {str(e)}")

        if content is None:
            raise Exception(f"Content extraction failed: {str(last_error)}")

        return content

    async def extract_competitor_pricing(
        self,
        content: str,
        source_url: str,
        use_cache: bool | None = None
    ) -> CompetitorPricing | None:
        """
        Extract competitor pricing information from web content

        Args:
            content: Web content to analyze
            source_url: Source URL for attribution
            use_cache: Override default caching behavior

        Returns:
            Extracted competitor pricing or None if extraction fails
        """
        use_cache = use_cache if use_cache is not None else self.enable_caching

        # Generate cache key based on content hash
        content_hash = str(hash(content))[:16]

        # Check cache first
        if use_cache and self.cache:
            cached_pricing = await self.cache.get(
                data_type="competitor_pricing",
                app_concept=content_hash,
                additional_params={"source": source_url}
            )
            if cached_pricing:
                logger.debug(f"Pricing cache hit for content: {content_hash}")
                return CompetitorPricing(**cached_pricing)

        # Prepare LLM prompt for extraction
        prompt = self._build_pricing_extraction_prompt(content, source_url)

        try:
            # Call LLM for extraction
            response = await acompletion(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting pricing information from web pages. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                api_key=self.llm_api_key,
                base_url=self.llm_base_url,
                temperature=0.1,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )

            # Parse response
            pricing_data = json.loads(response.choices[0].message.content)
            pricing = CompetitorPricing(
                company_name=pricing_data.get("company_name", "Unknown"),
                pricing_model=pricing_data.get("pricing_model", "unknown"),
                pricing_tiers=pricing_data.get("pricing_tiers", []),
                target_market=pricing_data.get("target_market", "B2C"),
                source_url=source_url,
                confidence=pricing_data.get("confidence", 70.0)
            )

            # Cache result
            if use_cache and self.cache:
                await self.cache.set(
                    data_type="competitor_pricing",
                    app_concept=content_hash,
                    data=asdict(pricing),
                    additional_params={"source": source_url}
                )

            # Track cost
            if self.enable_cost_tracking:
                tokens_used = response.usage.total_tokens if response.usage else 1000
                llm_cost = (tokens_used / 1000) * JinaClientConfig.DEFAULT_LLM_COST
                self.cost_tracking.llm_cost += llm_cost
                self.cost_tracking.llm_count += 1
                self.cost_tracking.total_cost += llm_cost

            logger.debug(f"Pricing extraction successful: {pricing.company_name}")
            return pricing

        except Exception as e:
            logger.error(f"Pricing extraction failed: {str(e)}")
            return None

    async def extract_market_size(
        self,
        content: str,
        source_url: str,
        use_cache: bool | None = None
    ) -> MarketSizeData | None:
        """
        Extract market size information from web content

        Args:
            content: Web content to analyze
            source_url: Source URL for attribution
            use_cache: Override default caching behavior

        Returns:
            Extracted market size data or None if extraction fails
        """
        use_cache = use_cache if use_cache is not None else self.enable_caching

        # Generate cache key
        content_hash = str(hash(content))[:16]

        # Check cache first
        if use_cache and self.cache:
            cached_market = await self.cache.get(
                data_type="market_size",
                app_concept=content_hash,
                additional_params={"source": source_url}
            )
            if cached_market:
                logger.debug(f"Market size cache hit for content: {content_hash}")
                return MarketSizeData(**cached_market)

        # Prepare LLM prompt
        prompt = self._build_market_size_extraction_prompt(content, source_url)

        try:
            # Call LLM for extraction
            response = await acompletion(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting market size information from reports. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                api_key=self.llm_api_key,
                base_url=self.llm_base_url,
                temperature=0.1,
                max_tokens=800,
                response_format={"type": "json_object"}
            )

            # Parse response
            market_data = json.loads(response.choices[0].message.content)
            market = MarketSizeData(
                tam_value=market_data.get("tam_value", ""),
                sam_value=market_data.get("sam_value", ""),
                growth_rate=market_data.get("growth_rate", ""),
                source_name=market_data.get("source_name", "Unknown"),
                source_url=source_url,
                year=market_data.get("year", datetime.now().year)
            )

            # Cache result
            if use_cache and self.cache:
                await self.cache.set(
                    data_type="market_size",
                    app_concept=content_hash,
                    data=asdict(market),
                    additional_params={"source": source_url}
                )

            # Track cost
            if self.enable_cost_tracking:
                tokens_used = response.usage.total_tokens if response.usage else 800
                llm_cost = (tokens_used / 1000) * JinaClientConfig.DEFAULT_LLM_COST
                self.cost_tracking.llm_cost += llm_cost
                self.cost_tracking.total_cost += llm_cost

            logger.debug(f"Market size extraction successful: TAM {market.tam_value}")
            return market

        except Exception as e:
            logger.error(f"Market size extraction failed: {str(e)}")
            return None

    async def extract_product_launch(
        self,
        content: str,
        source_url: str,
        use_cache: bool | None = None
    ) -> ProductLaunchData | None:
        """
        Extract product launch information from web content

        Args:
            content: Web content to analyze
            source_url: Source URL for attribution
            use_cache: Override default caching behavior

        Returns:
            Extracted product launch data or None if extraction fails
        """
        use_cache = use_cache if use_cache is not None else self.enable_caching

        # Generate cache key
        content_hash = str(hash(content))[:16]

        # Check cache first
        if use_cache and self.cache:
            cached_launch = await self.cache.get(
                data_type="product_launch",
                app_concept=content_hash,
                additional_params={"source": source_url}
            )
            if cached_launch:
                logger.debug(f"Product launch cache hit for content: {content_hash}")
                return ProductLaunchData(**cached_launch)

        # Prepare LLM prompt
        prompt = self._build_launch_extraction_prompt(content, source_url)

        try:
            # Call LLM for extraction
            response = await acompletion(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting product launch data from platforms like Product Hunt. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                api_key=self.llm_api_key,
                base_url=self.llm_base_url,
                temperature=0.1,
                max_tokens=600,
                response_format={"type": "json_object"}
            )

            # Parse response
            launch_data = json.loads(response.choices[0].message.content)
            launch = ProductLaunchData(
                product_name=launch_data.get("product_name", "Unknown"),
                launch_platform=launch_data.get("launch_platform", "Unknown"),
                launch_date=launch_data.get("launch_date", ""),
                upvotes=launch_data.get("upvotes", 0),
                comments=launch_data.get("comments", 0),
                source_url=source_url
            )

            # Cache result
            if use_cache and self.cache:
                await self.cache.set(
                    data_type="product_launch",
                    app_concept=content_hash,
                    data=asdict(launch),
                    additional_params={"source": source_url}
                )

            # Track cost
            if self.enable_cost_tracking:
                tokens_used = response.usage.total_tokens if response.usage else 600
                llm_cost = (tokens_used / 1000) * JinaClientConfig.DEFAULT_LLM_COST
                self.cost_tracking.llm_cost += llm_cost
                self.cost_tracking.total_cost += llm_cost

            logger.debug(f"Product launch extraction successful: {launch.product_name}")
            return launch

        except Exception as e:
            logger.error(f"Product launch extraction failed: {str(e)}")
            return None

    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting to requests"""
        current_time = time.time()

        # Remove old request times (older than 1 second)
        self.request_times = [t for t in self.request_times if current_time - t < 1.0]

        # Check if we're at the rate limit
        if len(self.request_times) >= self.rate_limit:
            # Sleep until we can make a request
            sleep_time = 1.0 - (current_time - self.request_times[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        # Record this request
        self.request_times.append(current_time)

    def _parse_search_results(self, data: dict[str, Any], num_results: int) -> list[SearchResult]:
        """Parse search results from Jina Search API response"""
        results = []

        if "data" in data and isinstance(data["data"], list):
            for item in data["data"][:num_results]:
                result = SearchResult(
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    relevance_score=item.get("score")
                )
                results.append(result)

        return results

    def _build_pricing_extraction_prompt(self, content: str, source_url: str) -> str:
        """Build prompt for pricing extraction"""
        return f"""
Extract pricing information from the following web content.
Focus on finding:
- Company name
- Pricing model (subscription, freemium, one-time, etc.)
- Pricing tiers with prices
- Target market (B2B, B2C, enterprise)
- Confidence level (0-100)

Source: {source_url}

Content:
{content[:2000]}...

Respond with JSON in this exact format:
{{
    "company_name": "string",
    "pricing_model": "string",
    "pricing_tiers": [
        {{"name": "string", "price": "string", "features": ["string"]}}
    ],
    "target_market": "string",
    "confidence": 85.0
}}
"""

    def _build_market_size_extraction_prompt(self, content: str, source_url: str) -> str:
        """Build prompt for market size extraction"""
        return f"""
Extract market size information from the following report content.
Focus on finding:
- TAM (Total Addressable Market) value
- SAM (Serviceable Addressable Market) value
- Market growth rate (CAGR)
- Report source name
- Year of data

Source: {source_url}

Content:
{content[:2000]}...

Respond with JSON in this exact format:
{{
    "tam_value": "$X billion",
    "sam_value": "$Y billion",
    "growth_rate": "Z% CAGR",
    "source_name": "string",
    "year": 2024
}}
"""

    def _build_launch_extraction_prompt(self, content: str, source_url: str) -> str:
        """Build prompt for product launch extraction"""
        return f"""
Extract product launch information from the following content.
Focus on finding:
- Product name
- Launch platform (Product Hunt, Hacker News, etc.)
- Launch date
- Number of upvotes/engagement
- Number of comments

Source: {source_url}

Content:
{content[:1500]}...

Respond with JSON in this exact format:
{{
    "product_name": "string",
    "launch_platform": "string",
    "launch_date": "YYYY-MM-DD",
    "upvotes": 0,
    "comments": 0
}}
"""

    def get_cost_summary(self) -> dict[str, Any]:
        """
        Get comprehensive cost summary

        Returns:
            Cost summary with breakdowns
        """
        return {
            "total_cost": round(self.cost_tracking.total_cost, 6),
            "search_cost": round(self.cost_tracking.search_cost, 6),
            "extraction_cost": round(self.cost_tracking.extraction_cost, 6),
            "llm_cost": round(self.cost_tracking.llm_cost, 6),
            "search_queries": self.cost_tracking.search_count,
            "urls_extracted": self.cost_tracking.extraction_count,
            "llm_calls": self.cost_tracking.llm_count,
            "average_cost_per_search": (
                self.cost_tracking.search_cost / self.cost_tracking.search_count
                if self.cost_tracking.search_count > 0 else 0
            ),
            "average_cost_per_extraction": (
                self.cost_tracking.extraction_cost / self.cost_tracking.extraction_count
                if self.cost_tracking.extraction_count > 0 else 0
            ),
            "average_cost_per_llm_call": (
                self.cost_tracking.llm_cost / self.cost_tracking.llm_count
                if self.cost_tracking.llm_count > 0 else 0
            )
        }

    async def close(self) -> None:
        """Close HTTP client and cache connections"""
        await self.http_client.aclose()
        if self.cache:
            await self.cache.close()
        logger.info("Jina client closed")
