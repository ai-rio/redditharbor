#!/usr/bin/env python3
"""
MCP-based Jina Client for Data-Driven Market Validation

This client provides access to Jina AI's Reader and Search API through Agno MCP integration:
- Reading and extracting content from URLs via mcp__jina-ai__read_url
- Performing web searches via mcp__jina-ai__search_web
- Maintains compatibility with the original JinaReaderClient interface

Features:
- MCP server integration with stdio transport
- Rate limiting preservation (500 RPM for reading, 100 RPM for search)
- Response caching to minimize MCP calls
- Fallback to direct HTTP if MCP unavailable
- Comprehensive error handling and logging
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from agno.tools.mcp import MCPTools

from agent_tools.jina_reader_client import (
    JinaResponse,
    RateLimiter,
    SearchResult,
    get_jina_client,
)
from config import settings

logger = logging.getLogger(__name__)


@dataclass
class MCPConnectionStatus:
    """Status of MCP connection and available tools"""

    is_connected: bool = False
    available_tools: list[str] = field(default_factory=list)
    connection_error: str | None = None
    last_connection_attempt: datetime = field(default_factory=lambda: datetime.now(UTC))

    def has_tool(self, tool_name: str) -> bool:
        """Check if a specific tool is available"""
        return tool_name in self.available_tools


class JinaMCPClient:
    """
    MCP-based client for Jina AI Reader and Search APIs.

    This client uses Agno MCPTools to connect to Jina MCP server and provides
    the same interface as JinaReaderClient for backward compatibility.

    Primary tools used:
    - mcp__jina-ai__read_url: Read and extract content from URLs
    - mcp__jina-ai__search_web: Search the web with LLM-optimized results

    Fallback behavior:
    - If MCP server is unavailable, falls back to direct HTTP client
    - Maintains rate limiting and caching from original implementation
    """

    def __init__(self, fallback_to_direct: bool = True):
        """
        Initialize the MCP-based Jina client.

        Args:
            fallback_to_direct: Whether to fall back to direct HTTP client if MCP fails
        """
        self.fallback_to_direct = fallback_to_direct
        self.timeout = settings.JINA_REQUEST_TIMEOUT

        # Rate limiters (same as original client)
        self.read_limiter = RateLimiter(
            max_requests_per_minute=settings.JINA_READ_RPM_LIMIT
        )
        self.search_limiter = RateLimiter(
            max_requests_per_minute=settings.JINA_SEARCH_RPM_LIMIT
        )

        # In-memory cache (same as original client)
        self._cache: dict[str, JinaResponse] = {}
        self._cache_ttl = settings.MARKET_VALIDATION_CACHE_TTL

        # MCP connection status
        self.mcp_status = MCPConnectionStatus()

        # MCP tools instance
        self._mcp_tools: MCPTools | None = None

        # Fallback client
        self._fallback_client = get_jina_client() if fallback_to_direct else None

        # Initialize MCP connection
        self._initialize_mcp_connection()

        logger.info(
            f"JinaMCPClient initialized: "
            f"mcp_connected={self.mcp_status.is_connected}, "
            f"tools_found={len(self.mcp_status.available_tools)}, "
            f"fallback_enabled={fallback_to_direct}"
        )

    def _initialize_mcp_connection(self) -> None:
        """Initialize connection to Jina MCP server"""
        try:
            # Initialize MCP tools for Jina AI server
            self._mcp_tools = MCPTools(
                command="npx -y jina-mcp-tools",
                transport="stdio",
                timeout_seconds=self.timeout,
                env={},  # Empty environment dict, defaults will be merged
            )

            # Try to get available tools
            available_tools = []
            if hasattr(self._mcp_tools, 'tools'):
                available_tools = list(self._mcp_tools.tools.keys())

            # Check for required Jina tools (actual tool names from jina-mcp-tools)
            required_tools = [
                "jina_reader",
                "jina_search"
            ]

            found_tools = [tool for tool in required_tools if tool in available_tools]

            if found_tools:
                self.mcp_status.is_connected = True
                self.mcp_status.available_tools = found_tools
                logger.info(f"Connected to Jina MCP server with tools: {found_tools}")
            else:
                self.mcp_status.connection_error = f"Required tools not found. Available: {available_tools}"
                logger.warning(self.mcp_status.connection_error)

        except Exception as e:
            self.mcp_status.connection_error = str(e)
            logger.error(f"Failed to connect to Jina MCP server: {e}")

            # Clean up failed MCP tools instance
            self._mcp_tools = None

    def _get_cache_key(self, url: str, operation: str = "read") -> str:
        """Generate cache key for a URL and operation"""
        return f"{operation}:{url}"

    def _is_cached(self, cache_key: str) -> bool:
        """Check if a response is in cache and not expired"""
        if cache_key not in self._cache:
            return False

        cached_response = self._cache[cache_key]
        age = (datetime.now(UTC) - cached_response.timestamp).total_seconds()
        return age < self._cache_ttl

    def _call_mcp_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call an MCP tool with error handling.

        Args:
            tool_name: Name of the MCP tool to call
            **kwargs: Arguments to pass to the tool

        Returns:
            Tool response or None if call fails
        """
        if not self.mcp_status.is_connected or not self._mcp_tools:
            logger.error(f"MCP not connected, cannot call {tool_name}")
            return None

        if not self.mcp_status.has_tool(tool_name):
            logger.error(f"Tool {tool_name} not available in MCP server")
            return None

        try:
            # Call the MCP tool
            if hasattr(self._mcp_tools, tool_name):
                tool_func = getattr(self._mcp_tools, tool_name)
                result = tool_func(**kwargs)
                return result
            else:
                logger.error(f"Tool {tool_name} not found in MCP tools instance")
                return None

        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            return None

    def _mcp_read_url(self, url: str) -> JinaResponse | None:
        """
        Read URL using MCP tool.

        Args:
            url: URL to read

        Returns:
            JinaResponse or None if failed
        """
        try:
            # Call MCP tool with correct tool name
            result = self._call_mcp_tool("jina_reader", url=url)

            if not result:
                return None

            # Parse MCP result to JinaResponse format
            # MCP tool should return content similar to original API
            content = str(result) if result else ""

            # Extract title from content (reuse original logic)
            title = self._extract_title_from_content(content)

            return JinaResponse(
                content=content,
                url=url,
                title=title,
                cached=False,
                word_count=len(content.split())
            )

        except Exception as e:
            logger.error(f"Error reading URL via MCP: {e}")
            return None

    def _mcp_search_web(self, query: str, num_results: int = 5) -> list[SearchResult] | None:
        """
        Search web using MCP tool.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of SearchResult objects or None if failed
        """
        try:
            # Call MCP tool with correct tool name and parameters
            result = self._call_mcp_tool("jina_search", query=query, num_results=num_results)

            if not result:
                return None

            # Parse MCP result to SearchResult format
            # MCP tool should return results similar to original API
            content = str(result) if result else ""

            # Parse search results (reuse original logic)
            return self._parse_search_results(content)

        except Exception as e:
            logger.error(f"Error searching via MCP: {e}")
            return None

    def _extract_title_from_content(self, content: str) -> str | None:
        """
        Extract page title from Jina Reader response.

        Reuses the same logic as the original JinaReaderClient.
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

        Reuses the same parsing logic as the original JinaReaderClient.
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

    def read_url(self, url: str, use_cache: bool = True) -> JinaResponse:
        """
        Read and extract content from a URL using MCP or fallback client.

        Args:
            url: The URL to read and extract content from
            use_cache: Whether to use cached response if available

        Returns:
            JinaResponse with extracted markdown content

        Raises:
            Exception: If both MCP and fallback client fail
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

        logger.info(f"Reading URL via MCP: {url}")

        # Try MCP first
        if self.mcp_status.is_connected:
            try:
                response = self._mcp_read_url(url)
                if response:
                    # Cache the response
                    if use_cache:
                        self._cache[cache_key] = response

                    logger.info(f"Successfully read {url} via MCP ({response.word_count} words)")
                    return response
            except Exception as e:
                logger.warning(f"MCP read failed for {url}: {e}")

        # Fallback to direct client if enabled
        if self._fallback_client:
            logger.info(f"Falling back to direct client for {url}")
            try:
                response = self._fallback_client.read_url(url, use_cache=False)  # Don't double-cache
                if use_cache:
                    self._cache[cache_key] = response
                return response
            except Exception as e:
                logger.error(f"Fallback client also failed for {url}: {e}")

        raise Exception(f"Failed to read {url} via both MCP and fallback client")

    def search_web(
        self, query: str, num_results: int = 5, use_cache: bool = True
    ) -> list[SearchResult]:
        """
        Search the web using MCP or fallback client.

        Args:
            query: The search query
            num_results: Number of results to return (max 10)
            use_cache: Whether to use cached results if available

        Returns:
            List of SearchResult objects

        Raises:
            Exception: If both MCP and fallback client fail
        """
        cache_key = f"search:{query}:{num_results}"

        # Check cache
        if use_cache and cache_key in self._cache:
            cached = self._cache[cache_key]
            age = (datetime.now(UTC) - cached.timestamp).total_seconds()
            if age < self._cache_ttl:
                logger.debug(f"Cache hit for search: {query}")
                # Parse cached content back to SearchResult objects
                return self._parse_search_results(cached.content)

        # Wait for rate limit
        self.search_limiter.wait_if_needed()

        logger.info(f"Searching via MCP: {query}")

        # Try MCP first
        if self.mcp_status.is_connected:
            try:
                results = self._mcp_search_web(query, num_results)
                if results is not None:
                    # Limit to requested number
                    results = results[:num_results]

                    # Cache the raw response (serialize results back to content)
                    if use_cache:
                        # Create a simple content representation for caching
                        cached_content = f"Search results for '{query}':\n"
                        for i, result in enumerate(results, 1):
                            cached_content += f"[{i}] Title: {result.title}\n"
                            cached_content += f"[{i}] URL Source: {result.url}\n"
                            cached_content += f"[{i}] Description: {result.snippet}\n\n"

                        self._cache[cache_key] = JinaResponse(
                            content=cached_content,
                            url=f"search:{query}",
                            title=f"Search: {query}"
                        )

                    logger.info(f"Found {len(results)} results via MCP for '{query}'")
                    return results
            except Exception as e:
                logger.warning(f"MCP search failed for '{query}': {e}")

        # Fallback to direct client if enabled
        if self._fallback_client:
            logger.info(f"Falling back to direct client for search: {query}")
            try:
                results = self._fallback_client.search_web(query, num_results, use_cache=False)
                if use_cache and results:
                    # Cache the results
                    cached_content = f"Search results for '{query}':\n"
                    for i, result in enumerate(results, 1):
                        cached_content += f"[{i}] Title: {result.title}\n"
                        cached_content += f"[{i}] URL Source: {result.url}\n"
                        cached_content += f"[{i}] Description: {result.snippet}\n\n"

                    self._cache[cache_key] = JinaResponse(
                        content=cached_content,
                        url=f"search:{query}",
                        title=f"Search: {query}"
                    )
                return results
            except Exception as e:
                logger.error(f"Fallback client also failed for search '{query}': {e}")

        raise Exception(f"Failed to search '{query}' via both MCP and fallback client")

    def get_rate_limit_status(self) -> dict:
        """Get current rate limit status"""
        status = {
            "mcp_connected": self.mcp_status.is_connected,
            "mcp_tools": self.mcp_status.available_tools,
            "read_remaining": self.read_limiter.get_remaining_requests(),
            "read_max": settings.JINA_READ_RPM_LIMIT,
            "search_remaining": self.search_limiter.get_remaining_requests(),
            "search_max": settings.JINA_SEARCH_RPM_LIMIT,
            "cache_size": len(self._cache),
            "fallback_enabled": self.fallback_to_direct,
        }

        if self.mcp_status.connection_error:
            status["mcp_error"] = self.mcp_status.connection_error

        return status

    def clear_cache(self) -> int:
        """Clear all cached responses. Returns number of items cleared."""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {count} cached responses")
        return count

    def reconnect_mcp(self) -> bool:
        """Attempt to reconnect to MCP server"""
        logger.info("Attempting to reconnect to MCP server...")
        self.mcp_status = MCPConnectionStatus()  # Reset status
        self._mcp_tools = None  # Clear existing tools

        try:
            self._initialize_mcp_connection()
            return self.mcp_status.is_connected
        except Exception as e:
            logger.error(f"Failed to reconnect to MCP server: {e}")
            return False

    def close(self):
        """Close the MCP client and fallback client"""
        if self._mcp_tools:
            try:
                # MCP tools might need cleanup
                if hasattr(self._mcp_tools, 'close'):
                    self._mcp_tools.close()
            except Exception as e:
                logger.error(f"Error closing MCP tools: {e}")
            finally:
                self._mcp_tools = None

        if self._fallback_client:
            try:
                self._fallback_client.close()
            except Exception as e:
                logger.error(f"Error closing fallback client: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Singleton instance for reuse
_mcp_client_instance: JinaMCPClient | None = None


def get_jina_mcp_client(fallback_to_direct: bool = True) -> JinaMCPClient:
    """Get or create the singleton JinaMCPClient instance"""
    global _mcp_client_instance
    if _mcp_client_instance is None:
        _mcp_client_instance = JinaMCPClient(fallback_to_direct=fallback_to_direct)
    return _mcp_client_instance


if __name__ == "__main__":
    # Simple test
    import sys

    logging.basicConfig(level=logging.INFO)

    print("Testing JinaMCPClient...")
    print("=" * 60)

    client = JinaMCPClient()

    # Test connection status
    status = client.get_rate_limit_status()
    print(f"MCP Connection Status: {status}")

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
        print("\nNo URL provided. Usage: python jina_mcp_client.py <url>")
        print("Example: python jina_mcp_client.py https://example.com")

    # Test search
    if len(sys.argv) > 2:
        query = sys.argv[2]
        print(f"\nSearching: {query}")
        try:
            results = client.search_web(query)
            print(f"Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.title}")
                print(f"   {result.url}")
                print(f"   {result.snippet[:100]}...")
                print()
        except Exception as e:
            print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("Test complete!")
    client.close()
