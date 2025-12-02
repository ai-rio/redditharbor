#!/usr/bin/env python3
"""
Hybrid Jina Client with MCP Integration Support

This client provides the best of both worlds:
- Primary: Direct HTTP client for maximum reliability and performance
- Secondary: MCP-aware architecture ready for future integration
- Full compatibility with existing JinaReaderClient interface
- Enhanced logging and monitoring for MCP readiness

Features:
- Production-ready direct HTTP client with Jina AI API
- MCP tool detection and capability checking
- Graceful fallback to HTTP client for all operations
- Comprehensive error handling and performance monitoring
- Ready for future MCP server integration when available
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

from agent_tools.jina_reader_client import (
    JinaResponse,
    RateLimiter,
    SearchResult,
)
from config import settings

logger = logging.getLogger(__name__)


@dataclass
class MCPCapability:
    """MCP server capability and status information"""

    mcp_available: bool = False
    jina_mcp_tools_available: bool = False
    mcp_server_version: str | None = None
    available_tools: list[str] = field(default_factory=list)
    last_check: datetime = field(default_factory=lambda: datetime.now(UTC))
    connection_method: str = "stdio"  # stdio, sse, etc.
    status_message: str = "Not checked"


class JinaHybridClient:
    """
    Hybrid Jina AI client that prioritizes reliability while being MCP-ready.

    This client implements a pragmatic approach:
    1. Uses proven direct HTTP client for all operations
    2. Detects and reports MCP capabilities for future integration
    3. Maintains full compatibility with existing JinaReaderClient interface
    4. Provides enhanced monitoring and fallback capabilities

    Design Philosophy:
    - Production reliability over experimental features
    - Gradual migration path to MCP when servers are stable
    - Zero breaking changes to existing code
    - Enhanced observability and debugging
    """

    def __init__(self, enable_mcp_experimental: bool = False):
        """
        Initialize the hybrid Jina client.

        Args:
            enable_mcp_experimental: Whether to attempt experimental MCP integration
        """
        self.enable_mcp_experimental = enable_mcp_experimental

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

        # MCP capability tracking
        self.mcp_capability = MCPCapability()

        # Primary client: Direct HTTP for reliability (create new instance to avoid singleton issues)
        from agent_tools.jina_reader_client import JinaReaderClient
        self._primary_client = JinaReaderClient()  # Create fresh instance

        # Check MCP capabilities if enabled
        if enable_mcp_experimental:
            self._check_mcp_capabilities()

        logger.info(
            f"JinaHybridClient initialized: "
            f"primary_client=direct_http, "
            f"mcp_experimental={enable_mcp_experimental}, "
            f"mcp_available={self.mcp_capability.mcp_available}"
        )

    def _check_mcp_capabilities(self) -> None:
        """Check if Jina MCP tools are available and their capabilities"""
        try:
            import json
            import subprocess

            logger.info("Checking Jina MCP server capabilities...")

            # Check if npx and jina-mcp-tools are available
            result = subprocess.run(
                ["npx", "-y", "jina-mcp-tools", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                self.mcp_capability.mcp_available = True
                self.mcp_capability.jina_mcp_tools_available = True
                self.mcp_capability.status_message = "Jina MCP tools available"

                # Extract version if available
                version_output = result.stdout.strip()
                if version_output:
                    self.mcp_capability.mcp_server_version = version_output

                # Try to get tool list by testing actual MCP communication
                try:
                    # Test MCP tools list request
                    mcp_request = {"method": "tools/list"}
                    tools_result = subprocess.run(
                        ["npx", "-y", "jina-mcp-tools"],
                        input=json.dumps(mcp_request),
                        capture_output=True,
                        text=True,
                        timeout=10
                    )

                    if tools_result.returncode == 0:
                        try:
                            response = json.loads(tools_result.stdout)
                            if "result" in response and "tools" in response["result"]:
                                tools = [tool.get("name", "") for tool in response["result"]["tools"]]
                                jina_tools = [tool for tool in tools if tool in ["jina_reader", "jina_search"]]

                                if jina_tools:
                                    self.mcp_capability.available_tools = jina_tools
                                    self.mcp_capability.status_message = f"Jina MCP tools detected: {jina_tools}"
                                else:
                                    self.mcp_capability.status_message = "Jina MCP server connected but no jina tools found"
                            else:
                                self.mcp_capability.status_message = "Unexpected MCP response format"
                        except json.JSONDecodeError:
                            # If JSON parsing fails, check if tools are mentioned in stdout
                            if "jina_reader" in tools_result.stdout and "jina_search" in tools_result.stdout:
                                self.mcp_capability.available_tools = ["jina_reader", "jina_search"]
                                self.mcp_capability.status_message = "Jina MCP tools detected via output parsing"
                            else:
                                self.mcp_capability.status_message = "Could not parse MCP tools list"
                        else:
                            self.mcp_capability.status_message = f" MCP tools command failed: {tools_result.stderr}"
                    else:
                        self.mcp_capability.status_message = "MCP tools command failed"

                except Exception as e:
                    logger.debug(f"Could not get tool list from MCP server: {e}")

            else:
                self.mcp_capability.status_message = f"MCP server returned error: {result.stderr}"

        except subprocess.TimeoutExpired:
            self.mcp_capability.status_message = "MCP server check timed out"
        except FileNotFoundError:
            self.mcp_capability.status_message = "npx not available for MCP integration"
        except Exception as e:
            self.mcp_capability.status_message = f"MCP capability check failed: {e}"

        self.mcp_capability.last_check = datetime.now(UTC)

        logger.info(f"MCP capability check completed: {self.mcp_capability.status_message}")

    def _get_cache_key(self, url: str, operation: str = "read") -> str:
        """Generate cache key for a URL and operation"""
        return f"hybrid:{operation}:{url}"

    def _is_cached(self, cache_key: str) -> bool:
        """Check if a response is in cache and not expired"""
        if cache_key not in self._cache:
            return False

        cached_response = self._cache[cache_key]
        age = (datetime.now(UTC) - cached_response.timestamp).total_seconds()
        return age < self._cache_ttl

    def _experimental_mcp_read_url(self, url: str) -> JinaResponse | None:
        """
        Experimental MCP URL reading using subprocess calls.

        This method attempts to use MCP when enabled, but falls back to HTTP
        if MCP is not available or fails.

        Args:
            url: URL to read

        Returns:
            JinaResponse or None if failed
        """
        if not self.enable_mcp_experimental or not self.mcp_capability.jina_mcp_tools_available:
            return None

        if "jina_reader" not in self.mcp_capability.available_tools:
            logger.debug("jina_reader tool not available in MCP capabilities")
            return None

        try:
            import json
            import subprocess

            logger.debug(f"Attempting MCP read via jina_reader for {url}")

            # Call jina_reader tool via MCP
            mcp_request = {
                "method": "tools/call",
                "params": {
                    "name": "jina_reader",
                    "arguments": {
                        "url": url
                    }
                }
            }

            result = subprocess.run(
                ["npx", "-y", "jina-mcp-tools"],
                input=json.dumps(mcp_request),
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                logger.warning(f"MCP process failed for {url}: {result.stderr}")
                return None

            # Parse MCP response
            try:
                response = json.loads(result.stdout)
                content = ""

                # Extract content from MCP response format
                if "result" in response:
                    if isinstance(response["result"], dict):
                        if "content" in response["result"]:
                            content = response["result"]["content"]
                        elif "text" in response["result"]:
                            content = response["result"]["text"]
                        else:
                            content = str(response["result"])
                    else:
                        content = str(response["result"])
                else:
                    content = result.stdout

                if content:
                    # Extract title from content (reuse original logic)
                    title = self._extract_title_from_content(content)

                    return JinaResponse(
                        content=content,
                        url=url,
                        title=title,
                        cached=False,
                        word_count=len(content.split())
                    )
                else:
                    logger.warning(f"No content received from MCP for {url}")
                    return None

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse MCP response for {url}: {e}")
                # Fallback: treat raw output as content
                if result.stdout.strip():
                    title = self._extract_title_from_content(result.stdout)
                    return JinaResponse(
                        content=result.stdout,
                        url=url,
                        title=title,
                        cached=False,
                        word_count=len(result.stdout.split())
                    )
                return None

        except subprocess.TimeoutExpired:
            logger.warning(f"MCP read timed out for {url}")
            return None
        except Exception as e:
            logger.warning(f"Experimental MCP read failed for {url}: {e}")
            return None

    def _experimental_mcp_search_web(self, query: str, num_results: int = 5) -> list[SearchResult] | None:
        """
        Experimental MCP web search using subprocess calls.

        This method attempts to use MCP when enabled, but falls back to HTTP
        if MCP is not available or fails.

        Args:
            query: Search query
            num_results: Number of results

        Returns:
            List of SearchResult objects or None if failed
        """
        if not self.enable_mcp_experimental or not self.mcp_capability.jina_mcp_tools_available:
            return None

        if "jina_search" not in self.mcp_capability.available_tools:
            logger.debug("jina_search tool not available in MCP capabilities")
            return None

        try:
            import json
            import subprocess

            logger.debug(f"Attempting MCP search via jina_search for '{query}'")

            # Call jina_search tool via MCP
            mcp_request = {
                "method": "tools/call",
                "params": {
                    "name": "jina_search",
                    "arguments": {
                        "query": query,
                        "num_results": num_results
                    }
                }
            }

            result = subprocess.run(
                ["npx", "-y", "jina-mcp-tools"],
                input=json.dumps(mcp_request),
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                logger.warning(f"MCP search process failed for '{query}': {result.stderr}")
                return None

            # Parse MCP response
            try:
                response = json.loads(result.stdout)
                content = ""

                # Extract content from MCP response format
                if "result" in response:
                    if isinstance(response["result"], dict):
                        if "content" in response["result"]:
                            content = response["result"]["content"]
                        elif "results" in response["result"]:
                            # Format structured results for parsing
                            results_data = response["result"]["results"]
                            formatted_results = []
                            for i, item in enumerate(results_data, 1):
                                title = item.get("title", "")
                                url = item.get("url", "")
                                snippet = item.get("snippet", "")
                                formatted_results.append(f"[{i}] Title: {title}")
                                formatted_results.append(f"[{i}] URL Source: {url}")
                                formatted_results.append(f"[{i}] Description: {snippet}")
                            content = "\n".join(formatted_results)
                        else:
                            content = str(response["result"])
                    else:
                        content = str(response["result"])
                else:
                    content = result.stdout

                if content:
                    # Parse search results (reuse original logic)
                    return self._parse_search_results(content)
                else:
                    logger.warning(f"No content received from MCP search for '{query}'")
                    return None

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse MCP search response for '{query}': {e}")
                # Fallback: treat raw output as content
                if result.stdout.strip():
                    return self._parse_search_results(result.stdout)
                return None

        except subprocess.TimeoutExpired:
            logger.warning(f"MCP search timed out for '{query}'")
            return None
        except Exception as e:
            logger.warning(f"Experimental MCP search failed for '{query}': {e}")
            return None

    def read_url(self, url: str, use_cache: bool = True) -> JinaResponse:
        """
        Read and extract content from a URL using primary direct HTTP client
        with experimental MCP fallback if enabled.

        Args:
            url: The URL to read and extract content from
            use_cache: Whether to use cached response if available

        Returns:
            JinaResponse with extracted markdown content

        Raises:
            Exception: If all methods fail
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

        logger.info(f"Reading URL via hybrid client: {url}")

        # Try experimental MCP first if enabled
        if self.enable_mcp_experimental:
            mcp_response = self._experimental_mcp_read_url(url)
            if mcp_response:
                if use_cache:
                    self._cache[cache_key] = mcp_response
                logger.info(f"Successfully read {url} via experimental MCP ({mcp_response.word_count} words)")
                return mcp_response

        # Primary method: Direct HTTP client
        try:
            response = self._primary_client.read_url(url, use_cache=False)

            if use_cache:
                self._cache[cache_key] = response

            logger.info(f"Successfully read {url} via direct HTTP ({response.word_count} words)")
            return response

        except Exception as e:
            logger.error(f"Direct HTTP client failed for {url}: {e}")
            raise Exception(f"Failed to read {url}: {e}")

    def search_web(
        self, query: str, num_results: int = 5, use_cache: bool = True
    ) -> list[SearchResult]:
        """
        Search the web using primary direct HTTP client with experimental MCP fallback.

        Args:
            query: The search query
            num_results: Number of results to return (max 10)
            use_cache: Whether to use cached results if available

        Returns:
            List of SearchResult objects

        Raises:
            Exception: If all methods fail
        """
        cache_key = f"hybrid:search:{query}:{num_results}"

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

        logger.info(f"Searching via hybrid client: {query}")

        # Try experimental MCP first if enabled
        if self.enable_mcp_experimental:
            mcp_results = self._experimental_mcp_search_web(query, num_results)
            if mcp_results is not None:
                # Limit to requested number
                mcp_results = mcp_results[:num_results]

                # Cache the results
                if use_cache and mcp_results:
                    cached_content = f"Search results for '{query}':\n"
                    for i, result in enumerate(mcp_results, 1):
                        cached_content += f"[{i}] Title: {result.title}\n"
                        cached_content += f"[{i}] URL Source: {result.url}\n"
                        cached_content += f"[{i}] Description: {result.snippet}\n\n"

                    self._cache[cache_key] = JinaResponse(
                        content=cached_content,
                        url=f"search:{query}",
                        title=f"Search: {query}"
                    )

                logger.info(f"Found {len(mcp_results)} results via experimental MCP for '{query}'")
                return mcp_results

        # Primary method: Direct HTTP client
        try:
            results = self._primary_client.search_web(query, num_results, use_cache=False)

            # Cache the results
            if use_cache and results:
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

            logger.info(f"Found {len(results)} results via direct HTTP for '{query}'")
            return results

        except Exception as e:
            logger.error(f"Direct HTTP client failed for search '{query}': {e}")
            raise Exception(f"Failed to search '{query}': {e}")

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

    def get_rate_limit_status(self) -> dict:
        """Get current rate limit status including MCP capabilities"""
        status = {
            # Rate limiting info
            "read_remaining": self.read_limiter.get_remaining_requests(),
            "read_max": settings.JINA_READ_RPM_LIMIT,
            "search_remaining": self.search_limiter.get_remaining_requests(),
            "search_max": settings.JINA_SEARCH_RPM_LIMIT,
            "cache_size": len(self._cache),

            # MCP capabilities
            "mcp_available": self.mcp_capability.mcp_available,
            "mcp_experimental_enabled": self.enable_mcp_experimental,
            "mcp_tools_available": self.mcp_capability.jina_mcp_tools_available,
            "mcp_tools": self.mcp_capability.available_tools,
            "mcp_server_version": self.mcp_capability.mcp_server_version,
            "mcp_status_message": self.mcp_capability.status_message,
            "mcp_last_check": self.mcp_capability.last_check.isoformat(),

            # Client info
            "primary_client": "direct_http",
            "client_type": "hybrid",
        }

        return status

    def clear_cache(self) -> int:
        """Clear all cached responses. Returns number of items cleared."""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {count} cached responses")
        return count

    def refresh_mcp_capabilities(self) -> None:
        """Refresh MCP capability detection"""
        logger.info("Refreshing MCP capabilities...")
        self._check_mcp_capabilities()

    def close(self):
        """Close the client and clean up resources"""
        try:
            self._primary_client.close()
        except Exception as e:
            logger.error(f"Error closing primary client: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def get_jina_hybrid_client(enable_mcp_experimental: bool = False) -> JinaHybridClient:
    """Create a new JinaHybridClient instance"""
    return JinaHybridClient(enable_mcp_experimental=enable_mcp_experimental)


if __name__ == "__main__":
    # Simple test
    import sys

    logging.basicConfig(level=logging.INFO)

    print("Testing JinaHybridClient...")
    print("=" * 60)

    client = JinaHybridClient(enable_mcp_experimental=True)

    # Test connection status
    status = client.get_rate_limit_status()
    print("Client Status:")
    for key, value in status.items():
        print(f"   {key}: {value}")

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
        print("\nNo URL provided. Usage: python jina_hybrid_client.py <url>")
        print("Example: python jina_hybrid_client.py https://example.com")

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
