#!/usr/bin/env python3
"""
Hybrid Web Crawler: Crawl4AI + Jina AI Integration

Smart crawler that uses Crawl4AI as primary with Jina AI as fallback:
- Primary: Crawl4AI (no token limits, full browser control)
- Fallback: Jina AI (when Crawl4AI fails or rate limited)
- Performance comparison and automatic switching
- Content quality assessment for optimal results
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from agent_tools.jina_reader_client import JinaReaderClient, JinaResponse
from config import settings

logger = logging.getLogger(__name__)


class CrawlerType(Enum):
    """Available crawler types"""
    CRAWL4AI = "crawl4ai"
    JINA_AI = "jina_ai"


@dataclass
class CrawlResult:
    """Unified result from any crawler"""
    content: str
    url: str
    title: Optional[str] = None
    crawler_used: CrawlerType = CrawlerType.CRAWL4AI
    success: bool = True
    error_message: Optional[str] = None
    response_time: float = 0.0
    word_count: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    quality_score: float = 0.0  # 0-1, based on content length, structure, etc.

    def __post_init__(self):
        if self.word_count == 0:
            self.word_count = len(self.content.split())
        # Simple quality scoring based on content characteristics
        if self.quality_score == 0 and self.success:
            self.quality_score = min(1.0, self.word_count / 1000)  # More words = higher quality


@dataclass
class CrawlerPerformance:
    """Track performance metrics for each crawler"""
    crawler_type: CrawlerType
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    average_quality_score: float = 0.0
    last_used: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        """Success rate as percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100


class HybridWebCrawler:
    """
    Intelligent hybrid crawler that combines Crawl4AI and Jina AI

    Strategy:
    1. Try Crawl4AI first (no token limits, full control)
    2. Fall back to Jina AI if Crawl4AI fails
    3. Track performance and adapt strategy based on success rates
    4. Use Jina AI for comparison/quality validation
    """

    def __init__(
        self,
        enable_crawl4ai: bool = True,
        enable_jina_fallback: bool = True,
        performance_threshold: float = 80.0,  # Switch crawler if success rate below this
        enable_quality_comparison: bool = False  # Compare results from both crawlers
    ):
        self.enable_crawl4ai = enable_crawl4ai
        self.enable_jina_fallback = enable_jina_fallback
        self.performance_threshold = performance_threshold
        self.enable_quality_comparison = enable_quality_comparison

        # Performance tracking
        self.performance = {
            CrawlerType.CRAWL4AI: CrawlerPerformance(crawler_type=CrawlerType.CRAWL4AI),
            CrawlerType.JINA_AI: CrawlerPerformance(crawler_type=CrawlerType.JINA_AI)
        }

        # Initialize clients
        self.jina_client: Optional[JinaReaderClient] = None
        self.crawl4ai_available = False

        # Setup clients
        self._setup_clients()

        # Crawl4AI session management
        self._crawl4ai_session = None

        logger.info(
            f"HybridWebCrawler initialized: "
            f"crawl4ai={enable_crawl4ai}, "
            f"jina_fallback={enable_jina_fallback}, "
            f"quality_comparison={enable_quality_comparison}"
        )

    def _setup_clients(self) -> None:
        """Setup crawler clients with availability checks"""
        # Setup Jina client (always available as fallback)
        if self.enable_jina_fallback:
            try:
                self.jina_client = JinaReaderClient()
                logger.info("Jina AI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Jina client: {e}")
                self.enable_jina_fallback = False

        # Check Crawl4AI availability
        if self.enable_crawl4ai:
            try:
                import crawl4ai
                self.crawl4ai_available = True
                logger.info("Crawl4AI is available")
            except ImportError:
                logger.warning("Crawl4AI not installed, will use Jina AI only")
                self.crawl4ai_available = False
                self.enable_crawl4ai = False

    async def crawl_url(
        self,
        url: str,
        prefer_crawler: Optional[CrawlerType] = None,
        use_fallback: bool = True,
        timeout: int = 30
    ) -> CrawlResult:
        """
        Crawl a URL using the optimal crawler with intelligent fallback

        Args:
            url: URL to crawl
            prefer_crawler: Force use of specific crawler
            use_fallback: Enable fallback to secondary crawler
            timeout: Request timeout in seconds

        Returns:
            CrawlResult with content and metadata
        """
        start_time = time.time()

        # Determine crawler order
        if prefer_crawler:
            crawler_order = [prefer_crawler]
            if use_fallback:
                other_crawler = (CrawlerType.JINA_AI if prefer_crawler == CrawlerType.CRAWL4AI
                               else CrawlerType.CRAWL4AI)
                if (other_crawler == CrawlerType.CRAWL4AI and self.enable_crawl4ai) or \
                   (other_crawler == CrawlerType.JINA_AI and self.enable_jina_fallback):
                    crawler_order.append(other_crawler)
        else:
            # Intelligent ordering based on performance
            crawler_order = self._get_optimal_crawler_order()

        # Try crawlers in order
        last_error = None
        for crawler_type in crawler_order:
            try:
                result = await self._crawl_with_specific_crawler(
                    url, crawler_type, timeout
                )

                if result.success:
                    # Update performance metrics
                    self._update_performance(crawler_type, result, time.time() - start_time)

                    # Quality comparison if enabled
                    if self.enable_quality_comparison and len(crawler_order) > 1:
                        await self._compare_quality(url, result, crawler_order)

                    return result
                else:
                    last_error = result.error_message

            except Exception as e:
                last_error = str(e)
                logger.warning(f"{crawler_type.value} failed for {url}: {e}")

                # Update failure metrics
                perf = self.performance[crawler_type]
                perf.total_requests += 1
                perf.failed_requests += 1

        # All crawlers failed
        return CrawlResult(
            content="",
            url=url,
            success=False,
            error_message=last_error or "All crawlers failed",
            response_time=time.time() - start_time
        )

    def _get_optimal_crawler_order(self) -> List[CrawlerType]:
        """Get crawler order based on performance and availability"""
        order = []

        # Prefer Crawl4AI if available and performing well
        if self.enable_crawl4ai and self.crawl4ai_available:
            crawl4ai_perf = self.performance[CrawlerType.CRAWL4AI]
            if crawl4ai_perf.total_requests == 0 or crawl4ai_perf.success_rate >= self.performance_threshold:
                order.append(CrawlerType.CRAWL4AI)

        # Add Jina as fallback or primary
        if self.enable_jina_fallback:
            jina_perf = self.performance[CrawlerType.JINA_AI]
            if jina_perf.total_requests == 0 or jina_perf.success_rate >= self.performance_threshold:
                if not order or order[0] != CrawlerType.JINA_AI:
                    order.append(CrawlerType.JINA_AI)

        # Add remaining available crawlers as backup
        for crawler_type in [CrawlerType.CRAWL4AI, CrawlerType.JINA_AI]:
            if crawler_type not in order:
                if (crawler_type == CrawlerType.CRAWL4AI and self.enable_crawl4ai and self.crawl4ai_available) or \
                   (crawler_type == CrawlerType.JINA_AI and self.enable_jina_fallback):
                    order.append(crawler_type)

        return order or [CrawlerType.JINA_AI]  # Default fallback

    async def _crawl_with_specific_crawler(
        self, url: str, crawler_type: CrawlerType, timeout: int
    ) -> CrawlResult:
        """Crawl URL using specific crawler"""
        if crawler_type == CrawlerType.CRAWL4AI:
            return await self._crawl_with_crawl4ai(url, timeout)
        elif crawler_type == CrawlerType.JINA_AI:
            return await self._crawl_with_jina(url, timeout)
        else:
            raise ValueError(f"Unsupported crawler type: {crawler_type}")

    async def _crawl_with_crawl4ai(self, url: str, timeout: int) -> CrawlResult:
        """Crawl URL using Crawl4AI"""
        try:
            from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

            # Lazy initialization of browser session
            if self._crawl4ai_session is None:
                browser_config = BrowserConfig(
                    headless=True,
                    viewport_width=1920,
                    viewport_height=1080,
                    user_agent="Mozilla/5.0 (compatible; RedditHarbor/1.0; +https://redditharbor.com)"
                )
                self._crawl4ai_session = AsyncWebCrawler(config=browser_config)
                await self._crawl4ai_session.start()

            # Configure crawl
            crawler_config = CrawlerRunConfig(
                page_timeout=timeout * 1000,  # Convert to milliseconds
                remove_overlay_elements=True,
                wait_for=None,  # Don't wait for specific elements
            )

            # Perform crawl
            result = await self._crawl4ai_session.arun(url, config=crawler_config)

            if result.success:
                return CrawlResult(
                    content=result.markdown or result.cleaned_html or "",
                    url=url,
                    title=result.metadata.get("title") if result.metadata else None,
                    crawler_used=CrawlerType.CRAWL4AI,
                    success=True,
                    word_count=len(result.markdown.split()) if result.markdown else 0
                )
            else:
                return CrawlResult(
                    content="",
                    url=url,
                    crawler_used=CrawlerType.CRAWL4AI,
                    success=False,
                    error_message="Crawl4AI failed to extract content"
                )

        except Exception as e:
            return CrawlResult(
                content="",
                url=url,
                crawler_used=CrawlerType.CRAWL4AI,
                success=False,
                error_message=f"Crawl4AI error: {str(e)}"
            )

    async def _crawl_with_jina(self, url: str, timeout: int) -> CrawlResult:
        """Crawl URL using Jina AI"""
        if not self.jina_client:
            return CrawlResult(
                content="",
                url=url,
                crawler_used=CrawlerType.JINA_AI,
                success=False,
                error_message="Jina client not initialized"
            )

        try:
            # Use existing Jina client
            jina_result = await asyncio.get_event_loop().run_in_executor(
                None, self.jina_client.read_url, url
            )

            return CrawlResult(
                content=jina_result.content,
                url=url,
                title=jina_result.title,
                crawler_used=CrawlerType.JINA_AI,
                success=jina_result.content != "",
                word_count=jina_result.word_count
            )

        except Exception as e:
            return CrawlResult(
                content="",
                url=url,
                crawler_used=CrawlerType.JINA_AI,
                success=False,
                error_message=f"Jina AI error: {str(e)}"
            )

    async def _compare_quality(
        self, url: str, primary_result: CrawlResult, crawler_order: List[CrawlerType]
    ) -> None:
        """Compare results from different crawlers for quality assessment"""
        if len(crawler_order) < 2:
            return

        # Get result from secondary crawler for comparison
        secondary_crawler = crawler_order[1]
        try:
            comparison_result = await self._crawl_with_specific_crawler(
                url, secondary_crawler, 30
            )

            if comparison_result.success:
                # Simple quality comparison
                primary_quality = primary_result.quality_score
                secondary_quality = comparison_result.quality_score

                logger.info(
                    f"Quality comparison for {url}: "
                    f"{primary_result.crawler_used.value} ({primary_quality:.2f}) vs "
                    f"{comparison_result.crawler_used.value} ({secondary_quality:.2f})"
                )

                # Update quality scores based on comparison
                if secondary_quality > primary_quality:
                    logger.info(f"Secondary crawler {secondary_crawler.value} provided better quality")

        except Exception as e:
            logger.warning(f"Quality comparison failed for {url}: {e}")

    def _update_performance(
        self, crawler_type: CrawlerType, result: CrawlResult, response_time: float
    ) -> None:
        """Update performance metrics for crawler"""
        perf = self.performance[crawler_type]
        perf.total_requests += 1
        perf.last_used = datetime.now(UTC)

        if result.success:
            perf.successful_requests += 1

            # Update rolling averages
            total_successful = perf.successful_requests
            perf.average_response_time = (
                (perf.average_response_time * (total_successful - 1) + response_time) / total_successful
            )
            perf.average_quality_score = (
                (perf.average_quality_score * (total_successful - 1) + result.quality_score) / total_successful
            )
        else:
            perf.failed_requests += 1

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        return {
            crawler_type.value: {
                "total_requests": perf.total_requests,
                "success_rate": perf.success_rate,
                "average_response_time": perf.average_response_time,
                "average_quality_score": perf.average_quality_score,
                "last_used": perf.last_used.isoformat() if perf.last_used else None
            }
            for crawler_type, perf in self.performance.items()
        }

    async def close(self) -> None:
        """Cleanup resources"""
        if self._crawl4ai_session:
            await self._crawl4ai_session.close()
            self._crawl4ai_session = None

        logger.info("HybridWebCrawler closed")