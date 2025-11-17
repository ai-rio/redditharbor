#!/usr/bin/env python3
"""
Jina Reader Client for Data-Driven Market Validation

This client provides access to Jina AI's Reader API for:
- Reading and extracting content from URLs (r.jina.ai)
- Performing web searches with LLM-optimized results (s.jina.ai)

Features:
- Rate limiting (500 RPM for reading, 100 RPM for search)
- Automatic retry with exponential backoff
- Clean markdown output optimized for LLM consumption
- Response caching to minimize API calls
"""

import logging
import time
import urllib.parse
from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class RateLimiter:
    """Simple token bucket rate limiter"""

    max_requests_per_minute: int
    _request_times: list = field(default_factory=list)

    def wait_if_needed(self) -> None:
        """Wait if we've exceeded rate limit"""
        now = time.time()
        # Remove requests older than 60 seconds
        self._request_times = [t for t in self._request_times if now - t < 60]

        if len(self._request_times) >= self.max_requests_per_minute:
            # Calculate wait time
            oldest = min(self._request_times)
            wait_time = 60 - (now - oldest) + 0.1  # Add small buffer
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.2f}s")
                time.sleep(wait_time)
            # Clean up after waiting
            now = time.time()
            self._request_times = [t for t in self._request_times if now - t < 60]

        self._request_times.append(time.time())

    def get_remaining_requests(self) -> int:
        """Get number of requests remaining in current window"""
        now = time.time()
        self._request_times = [t for t in self._request_times if now - t < 60]
        return max(0, self.max_requests_per_minute - len(self._request_times))


@dataclass
class SearchResult:
    """A single search result from Jina"""

    title: str
    url: str
    snippet: str
    position: int


@dataclass
class JinaResponse:
    """Response from Jina Reader API"""

    content: str
    url: str
    title: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    cached: bool = False
    word_count: int = 0

    def __post_init__(self):
        if self.word_count == 0:
            self.word_count = len(self.content.split())


class JinaReaderClient:
    """
    Client for Jina AI Reader API to fetch web content.

    Provides:
    - URL reading with clean markdown extraction
    - Web search with structured results
    - Rate limiting to stay within free tier limits
    - Response caching to minimize API calls

    Free Tier Limits:
    - Reader (r.jina.ai): 500 requests per minute
    - Search (s.jina.ai): 100 requests per minute
    """

    def __init__(self):
        self.reader_base_url = settings.JINA_READER_BASE_URL
        self.search_base_url = settings.JINA_SEARCH_BASE_URL
        self.api_key = settings.JINA_API_KEY
        self.timeout = settings.JINA_REQUEST_TIMEOUT

        # Initialize rate limiters
        self.read_limiter = RateLimiter(
            max_requests_per_minute=settings.JINA_READ_RPM_LIMIT
        )
        self.search_limiter = RateLimiter(
            max_requests_per_minute=settings.JINA_SEARCH_RPM_LIMIT
        )

        # Simple in-memory cache
        self._cache: dict[str, JinaResponse] = {}
        self._cache_ttl = settings.MARKET_VALIDATION_CACHE_TTL

        # Initialize HTTP client with proper headers
        self.client = httpx.Client(
            timeout=httpx.Timeout(self.timeout),
            headers=self._build_headers(),
            follow_redirects=True,
        )

        logger.info(
            f"JinaReaderClient initialized: "
            f"read_limit={settings.JINA_READ_RPM_LIMIT}/min, "
            f"search_limit={settings.JINA_SEARCH_RPM_LIMIT}/min, "
            f"cache_ttl={self._cache_ttl}s"
        )

    def _build_headers(self) -> dict:
        """Build headers for Jina API requests"""
        headers = {
            "Accept": "text/plain",  # Request plain text/markdown response
            "User-Agent": "RedditHarbor/1.0 (Market Validation)",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    def _get_cache_key(self, url: str) -> str:
        """Generate cache key for a URL"""
        return f"read:{url}"

    def _is_cached(self, cache_key: str) -> bool:
        """Check if a response is in cache and not expired"""
        if cache_key not in self._cache:
            return False

        cached_response = self._cache[cache_key]
        age = (datetime.now(UTC) - cached_response.timestamp).total_seconds()
        return age < self._cache_ttl

    def read_url(self, url: str, use_cache: bool = True) -> JinaResponse:
        """
        Read and extract content from a URL using Jina Reader API.

        Args:
            url: The URL to read and extract content from
            use_cache: Whether to use cached response if available

        Returns:
            JinaResponse with extracted markdown content

        Raises:
            httpx.HTTPError: If the request fails after retries
        """
        cache_key = self._get_cache_key(url)

        # Check cache first
        if use_cache and self._is_cached(cache_key):
            cached = self._cache[cache_key]
            logger.debug(f"Cache hit for {url}")
            return JinaResponse(
                content=cached.content,
                url=cached.url,
                title=cached.title,
                timestamp=cached.timestamp,
                cached=True,
                word_count=cached.word_count,
            )

        # Wait for rate limit
        self.read_limiter.wait_if_needed()

        # Build the Jina Reader URL
        reader_url = f"{self.reader_base_url}{url}"

        logger.info(f"Reading URL via Jina: {url}")

        # Make request with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.get(reader_url)
                response.raise_for_status()

                content = response.text

                # Extract title from content if present (Jina usually includes it)
                title = self._extract_title_from_content(content)

                jina_response = JinaResponse(content=content, url=url, title=title)

                # Cache the response
                if use_cache:
                    self._cache[cache_key] = jina_response

                logger.info(
                    f"Successfully read {url} ({jina_response.word_count} words)"
                )
                return jina_response

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Rate limited by Jina - wait and retry
                    wait_time = 60 * (attempt + 1)
                    msg = f"Rate limited by Jina, waiting {wait_time}s"
                    logger.warning(f"{msg} (attempt {attempt + 1})")
                    time.sleep(wait_time)
                elif e.response.status_code >= 500:
                    # Server error - retry with backoff
                    wait_time = 2**attempt
                    status = e.response.status_code
                    logger.warning(f"Server error {status}, retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    raise
            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    logger.warning(f"Timeout reading {url}, retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    raise

        raise httpx.HTTPError(f"Failed to read {url} after {max_retries} attempts")

    def search_web(
        self, query: str, num_results: int = 5, use_cache: bool = True
    ) -> list[SearchResult]:
        """
        Search the web using Jina Search API.

        Args:
            query: The search query
            num_results: Number of results to return (max 10)
            use_cache: Whether to use cached results if available

        Returns:
            List of SearchResult objects

        Raises:
            httpx.HTTPError: If the request fails after retries
        """
        cache_key = f"search:{query}:{num_results}"

        # Check cache
        if use_cache and cache_key in self._cache:
            cached = self._cache[cache_key]
            age = (datetime.utcnow() - cached.timestamp).total_seconds()
            if age < self._cache_ttl:
                logger.debug(f"Cache hit for search: {query}")
                # Parse cached content back to SearchResult objects
                return self._parse_search_results(cached.content)

        # Wait for rate limit
        self.search_limiter.wait_if_needed()

        # Build search URL
        encoded_query = urllib.parse.quote(query)
        search_url = f"{self.search_base_url}?q={encoded_query}"

        logger.info(f"Searching via Jina: {query}")

        # Make request with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.get(search_url)
                response.raise_for_status()

                content = response.text

                # Cache the raw response
                if use_cache:
                    self._cache[cache_key] = JinaResponse(
                        content=content, url=search_url, title=f"Search: {query}"
                    )

                # Parse the results
                results = self._parse_search_results(content)

                # Limit to requested number
                results = results[:num_results]

                logger.info(f"Found {len(results)} results for '{query}'")
                return results

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    wait_time = 60 * (attempt + 1)
                    logger.warning(f"Rate limited, waiting {wait_time}s")
                    time.sleep(wait_time)
                elif e.response.status_code >= 500:
                    wait_time = 2**attempt
                    logger.warning(f"Server error, retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    raise
            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    logger.warning(f"Timeout, retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    raise

        raise httpx.HTTPError(
            f"Failed to search '{query}' after {max_retries} attempts"
        )

    def _extract_title_from_content(self, content: str) -> str | None:
        """
        Extract page title from Jina Reader response.

        Jina Reader can return titles in multiple formats:
        1. "Title: Page Title" at the start (newer format)
        2. "# Page Title" as markdown header (older format)

        Args:
            content: Raw content from Jina Reader API

        Returns:
            Extracted title string or None if not found
        """
        if not content:
            return None

        lines = content.split("\n")
        if not lines:
            return None

        # Strategy 1: Check for "Title: ..." format (newer Jina format)
        for _i, line in enumerate(lines[:10]):  # Check first 10 lines
            line = line.strip()
            if line.startswith("Title:"):
                title = line[6:].strip()
                if title:
                    logger.debug(f"Extracted title from 'Title:' format: {title[:50]}")
                    return title

        # Strategy 2: Check for markdown header "# Title"
        first_line = lines[0].strip()
        if first_line.startswith("# "):
            title = first_line[2:].strip()
            if title:
                logger.debug(f"Extracted title from markdown header: {title[:50]}")
                return title

        # Strategy 3: Check for any header in first few lines
        for line in lines[:5]:
            line = line.strip()
            if line.startswith("## "):
                title = line[3:].strip()
                if title:
                    logger.debug(f"Extracted title from H2 header: {title[:50]}")
                    return title
            elif line.startswith("### "):
                title = line[4:].strip()
                if title:
                    logger.debug(f"Extracted title from H3 header: {title[:50]}")
                    return title

        logger.debug("No title found in content")
        return None

    def _parse_search_results(self, content: str) -> list[SearchResult]:
        """
        Parse Jina search results from markdown content.

        Jina returns search results in this format:
        [1] Title: The best expense tracker apps
        [1] URL Source: https://example.com/article
        [1] Description: Short description text
        [1] Published Time: 2021-01-26T16:59:51+0000

        Full content follows...

        [2] Title: Next result...
        """
        import re

        results = []
        current_result = {}
        position = 0

        lines = content.strip().split("\n")

        for line in lines:
            line = line.strip()

            # Match [N] Title: pattern
            title_match = re.match(r"\[(\d+)\] Title: (.+)", line)
            if title_match:
                # Save previous result if exists
                if current_result.get("title"):
                    position += 1
                    results.append(
                        SearchResult(
                            title=current_result.get("title", ""),
                            url=current_result.get("url", ""),
                            snippet=current_result.get("snippet", ""),
                            position=position,
                        )
                    )
                # Start new result
                current_result = {
                    "title": title_match.group(2).strip(),
                    "url": "",
                    "snippet": "",
                }
                continue

            # Match [N] URL Source: pattern
            url_match = re.match(r"\[\d+\] URL Source: (.+)", line)
            if url_match and current_result:
                current_result["url"] = url_match.group(1).strip()
                continue

            # Match [N] Description: pattern
            desc_match = re.match(r"\[\d+\] Description: (.+)", line)
            if desc_match and current_result:
                current_result["snippet"] = desc_match.group(1).strip()
                continue

            # Fallback: Old format with # headers
            if line.startswith("# ") or line.startswith("## "):
                if current_result.get("title"):
                    position += 1
                    results.append(
                        SearchResult(
                            title=current_result.get("title", ""),
                            url=current_result.get("url", ""),
                            snippet=current_result.get("snippet", ""),
                            position=position,
                        )
                    )
                current_result = {
                    "title": line.lstrip("#").strip(),
                    "url": "",
                    "snippet": "",
                }

            # Look for URL in old format
            elif line.lower().startswith("url:"):
                if current_result:
                    current_result["url"] = line[4:].strip()
            elif line.startswith("http://") or line.startswith("https://"):
                if current_result and not current_result.get("url"):
                    current_result["url"] = line

        # Don't forget the last result
        if current_result.get("title"):
            position += 1
            results.append(
                SearchResult(
                    title=current_result.get("title", ""),
                    url=current_result.get("url", ""),
                    snippet=current_result.get("snippet", ""),
                    position=position,
                )
            )

        return results

    def get_rate_limit_status(self) -> dict:
        """Get current rate limit status"""
        return {
            "read_remaining": self.read_limiter.get_remaining_requests(),
            "read_max": settings.JINA_READ_RPM_LIMIT,
            "search_remaining": self.search_limiter.get_remaining_requests(),
            "search_max": settings.JINA_SEARCH_RPM_LIMIT,
            "cache_size": len(self._cache),
        }

    def clear_cache(self) -> int:
        """Clear all cached responses. Returns number of items cleared."""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {count} cached responses")
        return count

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def close(self):
        """Close the HTTP client"""
        self.client.close()


# Singleton instance for reuse
_client_instance: JinaReaderClient | None = None


def get_jina_client() -> JinaReaderClient:
    """Get or create the singleton JinaReaderClient instance"""
    global _client_instance
    if _client_instance is None:
        _client_instance = JinaReaderClient()
    return _client_instance


if __name__ == "__main__":
    # Simple test
    import sys

    logging.basicConfig(level=logging.INFO)

    print("Testing JinaReaderClient...")
    print("=" * 60)

    client = JinaReaderClient()

    # Test rate limit status
    status = client.get_rate_limit_status()
    print(f"Rate limit status: {status}")

    # Test reading a simple URL
    if len(sys.argv) > 1:
        url = sys.argv[1]
        print(f"\nReading URL: {url}")
        try:
            response = client.read_url(url)
            print(f"Title: {response.title}")
            print(f"Word count: {response.word_count}")
            print("Preview (first 500 chars):")
            print(response.content[:500])
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("\nNo URL provided. Usage: python jina_reader_client.py <url>")
        print("Example: python jina_reader_client.py https://example.com")

    print("\n" + "=" * 60)
    print("Test complete!")
