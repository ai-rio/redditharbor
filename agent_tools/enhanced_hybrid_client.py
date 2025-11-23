#!/usr/bin/env python3
"""
Enhanced Hybrid Client: Jina AI + Crawl4AI Integration

Extends the existing JinaHybridClient with intelligent Crawl4AI integration:
- Smart switching based on token usage and performance
- Jina AI as primary, Crawl4AI as fallback when tokens are limited
- Automatic performance optimization
- Token usage monitoring and proactive switching
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from agent_tools.crawl_result_normalizer import (
    CrawlResultNormalizer,
    NormalizedCrawlResult,
)
from agent_tools.hybrid_crawler import CrawlerType, HybridWebCrawler
from agent_tools.jina_hybrid_client import JinaHybridClient
from config import settings

logger = logging.getLogger(__name__)


@dataclass
class TokenUsageStats:
    """Track Jina AI token usage for intelligent switching"""
    daily_usage: int = 0
    daily_limit: int = 0
    hourly_usage: int = 0
    hourly_limit: int = 0
    last_reset_hour: int = 0
    last_reset_day: int = 0

    @property
    def daily_usage_percentage(self) -> float:
        """Percentage of daily token usage"""
        if self.daily_limit == 0:
            return 0.0
        return (self.daily_usage / self.daily_limit) * 100

    @property
    def hourly_usage_percentage(self) -> float:
        """Percentage of hourly token usage"""
        if self.hourly_limit == 0:
            return 0.0
        return (self.hourly_usage / self.hourly_limit) * 100

    def should_use_crawl4ai_fallback(self) -> bool:
        """Determine if we should switch to Crawl4AI due to token limits"""
        return (
            self.daily_usage_percentage > 80 or  # 80% of daily limit
            self.hourly_usage_percentage > 85     # 85% of hourly limit
        )


class EnhancedHybridClient:
    """
    Enhanced hybrid client that combines Jina AI with Crawl4AI intelligently

    Strategy:
    1. Use Jina AI as primary crawler (faster, simpler for most sites)
    2. Monitor token usage and performance metrics
    3. Switch to Crawl4AI when:
       - Jina token usage near limits
       - Jina performance drops below threshold
       - Crawl4AI provides better quality results
    4. Maintain compatibility with existing JinaHybridClient interface
    """

    def __init__(
        self,
        enable_crawl4ai_fallback: bool = True,
        token_threshold_percentage: float = 80.0,
        performance_threshold: float = 75.0,
        enable_quality_comparison: bool = False
    ):
        """
        Initialize enhanced hybrid client

        Args:
            enable_crawl4ai_fallback: Enable Crawl4AI as fallback
            token_threshold_percentage: Switch to Crawl4AI at this token usage percentage
            performance_threshold: Switch crawlers if performance below this percentage
            enable_quality_comparison: Compare results quality between crawlers
        """
        # Initialize existing Jina hybrid client
        self.jina_client = JinaHybridClient(enable_mcp_experimental=False)

        # Initialize Crawl4AI hybrid crawler
        self.crawl4ai_client = None
        if enable_crawl4ai_fallback and settings.HYBRID_CRAWLER_ENABLED:
            try:
                self.crawl4ai_client = HybridWebCrawler(
                    enable_crawl4ai=settings.HYBRID_CRAWLER_ENABLE_CRAWL4AI,
                    enable_jina_fallback=False,  # Don't use Jina as fallback here
                    performance_threshold=performance_threshold,
                    enable_quality_comparison=enable_quality_comparison
                )
                logger.info("Enhanced Hybrid Client: Crawl4AI fallback enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize Crawl4AI fallback: {e}")
                enable_crawl4ai_fallback = False

        # Configuration
        self.enable_crawl4ai_fallback = enable_crawl4ai_fallback
        self.token_threshold = token_threshold_percentage
        self.performance_threshold = performance_threshold
        self.enable_quality_comparison = enable_quality_comparison

        # Token usage tracking
        self.token_stats = TokenUsageStats(
            daily_limit=1000000,  # Estimated daily token limit
            hourly_limit=50000    # Estimated hourly token limit
        )

        # Performance tracking
        self.performance_stats = {
            "jina_success": 0,
            "jina_total": 0,
            "crawl4ai_success": 0,
            "crawl4ai_total": 0,
            "switches_to_crawl4ai": 0,
            "switches_to_jina": 0
        }

        # Result normalization
        self.normalizer = CrawlResultNormalizer(strict_mode=False)

        logger.info(
            f"EnhancedHybridClient initialized: "
            f"crawl4ai_fallback={enable_crawl4ai_fallback}, "
            f"token_threshold={token_threshold_percentage}%, "
            f"performance_threshold={performance_threshold}%"
        )

    async def read_url(self, url: str, prefer_jina: bool = True, normalize: bool = True) -> NormalizedCrawlResult:
        """
        Read URL content using intelligent crawler selection

        Args:
            url: URL to read
            prefer_jina: Whether to prefer Jina AI (default: True)
            normalize: Whether to normalize the result (default: True)

        Returns:
            NormalizedCrawlResult with consistent format across crawlers
        """
        # Update token usage stats
        self._update_token_usage()

        # Determine crawler strategy
        use_jina = prefer_jina and not self._should_use_crawl4ai()

        raw_result = None
        source_crawler = None

        if use_jina:
            try:
                # Use Jina AI
                raw_result = await self._read_with_jina(url)
                source_crawler = "jina_ai"
                self.performance_stats["jina_total"] += 1
                if raw_result.content:
                    self.performance_stats["jina_success"] += 1

                # Check if we should try Crawl4AI for comparison
                if (self.enable_quality_comparison and
                    self.crawl4ai_client and
                    self._should_compare_quality()):
                    await self._compare_results(url, raw_result, None)

            except Exception as e:
                logger.warning(f"Jina AI failed for {url}: {e}")
                self.performance_stats["jina_total"] += 1

                # Fall back to Crawl4AI if available
                if self.enable_crawl4ai_fallback and self.crawl4ai_client:
                    logger.info(f"Falling back to Crawl4AI for {url}")
                    raw_result = await self._read_with_crawl4ai(url)
                    source_crawler = "crawl4ai"
                    self.performance_stats["crawl4ai_total"] += 1
                    if raw_result.content:
                        self.performance_stats["crawl4ai_success"] += 1
                else:
                    raise

        elif self.enable_crawl4ai_fallback and self.crawl4ai_client:
            # Use Crawl4AI
            try:
                raw_result = await self._read_with_crawl4ai(url)
                source_crawler = "crawl4ai"
                self.performance_stats["crawl4ai_total"] += 1
                if raw_result.content:
                    self.performance_stats["crawl4ai_success"] += 1

            except Exception as e:
                logger.warning(f"Crawl4AI failed for {url}: {e}")
                self.performance_stats["crawl4ai_total"] += 1

                # Fall back to Jina AI
                logger.info(f"Falling back to Jina AI for {url}")
                raw_result = await self._read_with_jina(url)
                source_crawler = "jina_ai"

        else:
            # No Crawl4AI available, use Jina only
            raw_result = await self._read_with_jina(url)
            source_crawler = "jina_ai"

        # Apply normalization if requested
        if normalize and raw_result:
            normalized_result = self.normalizer.normalize_result(raw_result, source_crawler, url)

            # Add crawler switching info to processing notes
            if (use_jina and source_crawler == "crawl4ai"):
                normalized_result.processing_notes.append("Switched from Jina AI to Crawl4AI (fallback)")
            elif (not use_jina and source_crawler == "jina_ai"):
                normalized_result.processing_notes.append("Switched from Crawl4AI to Jina AI (fallback)")

            return normalized_result
        else:
            # Return raw result if normalization disabled
            return raw_result

    async def search(self, query: str, max_results: int = 10) -> list[Any]:
        """
        Perform web search using Jina AI (Crawl4AI doesn't have search capabilities)

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of search results
        """
        # For search, we still use Jina AI as Crawl4AI doesn't have search API
        return await self._search_with_jina(query, max_results)

    def _should_use_crawl4ai(self) -> bool:
        """Determine if we should use Crawl4AI based on current conditions"""
        if not self.enable_crawl4ai_fallback or not self.crawl4ai_client:
            return False

        # Check token usage
        if settings.HYBRID_CRAWLER_MONITOR_TOKEN_USAGE:
            if self.token_stats.should_use_crawl4ai_fallback():
                logger.info(f"Switching to Crawl4AI due to token usage: {self.token_stats.daily_usage_percentage:.1f}%")
                self.performance_stats["switches_to_crawl4ai"] += 1
                return True

        # Check Jina performance
        jina_success_rate = self._get_jina_success_rate()
        if jina_success_rate < self.performance_threshold:
            logger.info(f"Switching to Crawl4AI due to Jina performance: {jina_success_rate:.1f}%")
            self.performance_stats["switches_to_crawl4ai"] += 1
            return True

        return False

    def _get_jina_success_rate(self) -> float:
        """Get Jina AI success rate percentage"""
        if self.performance_stats["jina_total"] == 0:
            return 100.0  # Assume perfect if no requests yet
        return (self.performance_stats["jina_success"] / self.performance_stats["jina_total"]) * 100

    def _should_compare_quality(self) -> bool:
        """Determine if we should compare quality between crawlers"""
        return (
            self.enable_quality_comparison and
            self.performance_stats["jina_total"] > 10 and  # Have enough data
            self.crawl4ai_client
        )

    async def _read_with_jina(self, url: str) -> Any:
        """Read URL using Jina AI"""
        # Use existing Jina hybrid client
        from agent_tools.jina_reader_client import JinaResponse

        try:
            # Get result from Jina client (synchronous)
            jina_result = self.jina_client._primary_client.read_url(url)

            # Convert to compatible format
            return JinaResponse(
                content=jina_result.content,
                url=jina_result.url,
                title=jina_result.title,
                word_count=jina_result.word_count
            )

        except Exception as e:
            logger.error(f"Jina AI read failed for {url}: {e}")
            raise

    async def _read_with_crawl4ai(self, url: str) -> Any:
        """Read URL using Crawl4AI"""
        try:
            result = await self.crawl4ai_client.crawl_url(
                url,
                prefer_crawler=CrawlerType.CRAWL4AI,
                use_fallback=False  # Don't fall back to Jina from here
            )

            # Convert to JinaResponse-compatible format
            from agent_tools.jina_reader_client import JinaResponse

            return JinaResponse(
                content=result.content,
                url=result.url,
                title=result.title,
                word_count=result.word_count,
                timestamp=result.timestamp
            )

        except Exception as e:
            logger.error(f"Crawl4AI read failed for {url}: {e}")
            raise

    async def _search_with_jina(self, query: str, max_results: int) -> list[Any]:
        """Search using Jina AI"""
        try:
            return self.jina_client._primary_client.search(query, max_results=max_results)
        except Exception as e:
            logger.error(f"Jina AI search failed for '{query}': {e}")
            return []

    async def _compare_results(self, url: str, jina_result: Any, crawl4ai_result: Any | None) -> None:
        """Compare results quality between crawlers"""
        if not self.crawl4ai_client:
            return

        try:
            # Get Crawl4AI result for comparison
            crawl4ai_crawl = await self.crawl4ai_client.crawl_url(url)

            if crawl4ai_crawl.success:
                jina_quality = min(1.0, len(jina_result.content.split()) / 1000)
                crawl4ai_quality = crawl4ai_crawl.quality_score

                logger.info(
                    f"Quality comparison for {url}: "
                    f"Jina={jina_quality:.2f}, Crawl4AI={crawl4ai_quality:.2f}"
                )

                # Update strategy if Crawl4AI consistently better
                if crawl4ai_quality > jina_quality * 1.2:  # 20% better
                    logger.info("Crawl4AI showing significantly better quality")

        except Exception as e:
            logger.warning(f"Quality comparison failed for {url}: {e}")

    def _update_token_usage(self) -> None:
        """Update token usage statistics"""
        now = datetime.now(UTC)

        # Reset hourly counter if needed
        if now.hour != self.token_stats.last_reset_hour:
            self.token_stats.hourly_usage = 0
            self.token_stats.last_reset_hour = now.hour

        # Reset daily counter if needed
        if now.day != self.token_stats.last_reset_day:
            self.token_stats.daily_usage = 0
            self.token_stats.last_reset_day = now.day

        # Estimate token usage based on requests
        # Rough estimate: 1 token per character for content processing
        estimated_tokens = self.performance_stats["jina_total"] * 1000  # Rough estimate
        self.token_stats.daily_usage = estimated_tokens
        self.token_stats.hourly_usage = estimated_tokens % self.token_stats.hourly_limit

    def get_performance_stats(self) -> dict[str, Any]:
        """Get comprehensive performance statistics"""
        jina_rate = self._get_jina_success_rate()
        crawl4ai_rate = 0.0
        if self.performance_stats["crawl4ai_total"] > 0:
            crawl4ai_rate = (self.performance_stats["crawl4ai_success"] /
                           self.performance_stats["crawl4ai_total"]) * 100

        return {
            "jina_performance": {
                "success_rate": jina_rate,
                "total_requests": self.performance_stats["jina_total"],
                "successful_requests": self.performance_stats["jina_success"]
            },
            "crawl4ai_performance": {
                "success_rate": crawl4ai_rate,
                "total_requests": self.performance_stats["crawl4ai_total"],
                "successful_requests": self.performance_stats["crawl4ai_success"]
            },
            "switching_behavior": {
                "switches_to_crawl4ai": self.performance_stats["switches_to_crawl4ai"],
                "switches_to_jina": self.performance_stats["switches_to_jina"]
            },
            "token_usage": {
                "daily_usage": self.token_stats.daily_usage,
                "daily_percentage": self.token_stats.daily_usage_percentage,
                "hourly_usage": self.token_stats.hourly_usage,
                "hourly_percentage": self.token_stats.hourly_usage_percentage,
                "near_limits": self.token_stats.should_use_crawl4ai_fallback()
            },
            "crawler_availability": {
                "jina_available": True,
                "crawl4ai_available": self.enable_crawl4ai_fallback and self.crawl4ai_client is not None
            },
            "normalization": self.normalizer.get_normalization_stats()
        }

    async def close(self) -> None:
        """Cleanup resources"""
        if self.crawl4ai_client:
            await self.crawl4ai_client.close()

        logger.info("Enhanced Hybrid Client closed")


# Factory function for easy instantiation
def create_enhanced_hybrid_client(
    enable_crawl4ai: bool | None = None,
    token_threshold: float | None = None,
    performance_threshold: float | None = None
) -> EnhancedHybridClient:
    """
    Factory function to create enhanced hybrid client with settings from config

    Args:
        enable_crawl4ai: Override HYBRID_CRAWLER_ENABLED setting
        token_threshold: Override token threshold percentage
        performance_threshold: Override performance threshold

    Returns:
        EnhancedHybridClient instance
    """
    return EnhancedHybridClient(
        enable_crawl4ai_fallback=enable_crawl4ai if enable_crawl4ai is not None else settings.HYBRID_CRAWLER_ENABLE_CRAWL4AI,
        token_threshold_percentage=token_threshold if token_threshold is not None else settings.HYBRID_CRAWLER_JINA_TOKEN_THRESHOLD / 10000,
        performance_threshold=performance_threshold if performance_threshold is not None else settings.HYBRID_CRAWLER_PERFORMANCE_THRESHOLD,
        enable_quality_comparison=settings.HYBRID_CRAWLER_ENABLE_QUALITY_COMPARISON
    )
