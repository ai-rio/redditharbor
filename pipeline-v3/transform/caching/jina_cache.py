"""
Jina-specific caching implementation for market research data

This module provides Redis-based caching for Jina API responses with
configurable TTL values for different data types to optimize costs
and performance.
"""

import json
import hashlib
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import asyncio

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    import redis
    REDIS_AVAILABLE = False

from ..validation_evidence_pydantic import (
    CompetitorPricing,
    MarketSizeData,
    ProductLaunchData
)

logger = logging.getLogger(__name__)


class JinaCache:
    """
    Redis-based cache for Jina API responses with configurable TTL

    Features:
    - Separate TTL for different data types (competitor pricing, market size, etc.)
    - Cache hit rate tracking
    - Cost savings estimation
    - Fallback to in-memory cache if Redis unavailable
    - Async support for high-throughput operations
    """

    # Default TTL values (in seconds)
    DEFAULT_TTL = {
        "competitor_pricing": 7 * 24 * 60 * 60,  # 7 days
        "market_size": 30 * 24 * 60 * 60,        # 30 days
        "product_launch": 7 * 24 * 60 * 60,      # 7 days
        "web_search": 24 * 60 * 60,              # 24 hours
        "content_extraction": 7 * 24 * 60 * 60   # 7 days
    }

    # Cache key prefixes
    KEY_PREFIXES = {
        "competitor_pricing": "jina:competitor:",
        "market_size": "jina:market:",
        "product_launch": "jina:launch:",
        "web_search": "jina:search:",
        "content_extraction": "jina:content:"
    }

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        redis_db: int = 1,  # Use separate DB for Jina cache
        default_ttl: Optional[Dict[str, int]] = None,
        enable_in_memory_fallback: bool = True,
        max_memory_items: int = 1000
    ):
        """
        Initialize Jina cache with Redis connection

        Args:
            redis_url: Redis connection URL
            redis_db: Redis database number for Jina cache
            default_ttl: Custom TTL values for different data types
            enable_in_memory_fallback: Enable in-memory cache if Redis unavailable
            max_memory_items: Maximum items to store in in-memory cache
        """
        self.redis_url = redis_url
        self.redis_db = redis_db
        self.enable_in_memory_fallback = enable_in_memory_fallback
        self.max_memory_items = max_memory_items

        # Merge custom TTL with defaults
        self.ttl = self.DEFAULT_TTL.copy()
        if default_ttl:
            self.ttl.update(default_ttl)

        # Initialize Redis connection
        self._redis_client = None
        self._redis_available = False

        # In-memory fallback cache
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._memory_access_order: List[str] = []

        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "errors": 0,
            "fallback_hits": 0,
            "total_cost_saved": 0.0
        }

    async def initialize(self) -> None:
        """Initialize Redis connection and test connectivity"""
        try:
            if REDIS_AVAILABLE:
                # Parse URL to get connection details
                if self.redis_url.startswith("redis://"):
                    self._redis_client = redis.from_url(
                        f"{self.redis_url}/{self.redis_db}",
                        decode_responses=True
                    )
                else:
                    self._redis_client = redis.from_url(
                        self.redis_url,
                        decode_responses=True
                    )

                # Test connection
                await self._redis_client.ping()
                self._redis_available = True
                logger.info(f"Jina cache connected to Redis DB {self.redis_db}")
            else:
                logger.warning("Redis not available, using in-memory cache only")

        except Exception as e:
            logger.warning(f"Redis connection failed: {str(e)}. Using in-memory fallback")
            self._redis_available = False

    def _generate_cache_key(
        self,
        data_type: str,
        app_concept: str,
        target_market: str = "",
        additional_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate consistent cache key for market research queries

        Args:
            data_type: Type of data being cached
            app_concept: Application concept description
            target_market: Target market segment
            additional_params: Additional parameters for key generation

        Returns:
            Consistent cache key string
        """
        # Create base string for hashing
        key_data = {
            "app_concept": app_concept.lower().strip(),
            "target_market": target_market.lower().strip(),
            "type": data_type
        }

        if additional_params:
            # Sort keys for consistent hashing
            for k, v in sorted(additional_params.items()):
                key_data[k] = str(v).lower().strip()

        # Create hash
        key_string = json.dumps(key_data, sort_keys=True, separators=(',', ':'))
        hash_value = hashlib.sha256(key_string.encode()).hexdigest()[:16]

        # Combine with prefix
        prefix = self.KEY_PREFIXES.get(data_type, "jina:general:")
        return f"{prefix}{hash_value}"

    async def get(
        self,
        data_type: str,
        app_concept: str,
        target_market: str = "",
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached data for market research query

        Args:
            data_type: Type of data to retrieve
            app_concept: Application concept
            target_market: Target market
            additional_params: Additional query parameters

        Returns:
            Cached data or None if not found
        """
        cache_key = self._generate_cache_key(
            data_type, app_concept, target_market, additional_params
        )

        # Try Redis first
        if self._redis_available:
            try:
                cached_data = await self._redis_client.get(cache_key)
                if cached_data:
                    self.stats["hits"] += 1
                    logger.debug(f"Cache hit (Redis): {cache_key}")
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning(f"Redis get error: {str(e)}")
                self.stats["errors"] += 1

        # Fallback to memory cache
        if self.enable_in_memory_fallback and cache_key in self._memory_cache:
            # Check if cached item is still valid
            cached_item = self._memory_cache[cache_key]
            if not self._is_expired(cached_item):
                self.stats["fallback_hits"] += 1
                logger.debug(f"Cache hit (Memory): {cache_key}")
                return cached_item["data"]
            else:
                # Remove expired item
                self._remove_from_memory_cache(cache_key)

        self.stats["misses"] += 1
        logger.debug(f"Cache miss: {cache_key}")
        return None

    async def set(
        self,
        data_type: str,
        app_concept: str,
        data: Dict[str, Any],
        target_market: str = "",
        additional_params: Optional[Dict[str, Any]] = None,
        custom_ttl: Optional[int] = None
    ) -> None:
        """
        Cache market research data with appropriate TTL

        Args:
            data_type: Type of data being cached
            app_concept: Application concept
            data: Data to cache
            target_market: Target market
            additional_params: Additional query parameters
            custom_ttl: Custom TTL in seconds (overrides default)
        """
        cache_key = self._generate_cache_key(
            data_type, app_concept, target_market, additional_params
        )

        ttl = custom_ttl or self.ttl.get(data_type, self.DEFAULT_TTL["web_search"])
        serialized_data = json.dumps(data, default=str)

        # Store in Redis
        if self._redis_available:
            try:
                await self._redis_client.setex(cache_key, ttl, serialized_data)
                self.stats["sets"] += 1
                logger.debug(f"Cached to Redis: {cache_key} (TTL: {ttl}s)")
                return
            except Exception as e:
                logger.warning(f"Redis set error: {str(e)}")
                self.stats["errors"] += 1

        # Fallback to memory cache
        if self.enable_in_memory_fallback:
            self._add_to_memory_cache(cache_key, data, ttl)
            self.stats["sets"] += 1  # Count memory cache sets too
            logger.debug(f"Cached to Memory: {cache_key} (TTL: {ttl}s)")

    def _add_to_memory_cache(self, key: str, data: Dict[str, Any], ttl: int) -> None:
        """Add item to in-memory cache with LRU eviction"""
        # Remove oldest item if at capacity
        if len(self._memory_cache) >= self.max_memory_items:
            oldest_key = self._memory_access_order.pop(0)
            del self._memory_cache[oldest_key]

        # Add new item
        expire_time = datetime.now() + timedelta(seconds=ttl)
        self._memory_cache[key] = {
            "data": data,
            "expire_time": expire_time
        }

        # Update access order
        if key in self._memory_access_order:
            self._memory_access_order.remove(key)
        self._memory_access_order.append(key)

    def _remove_from_memory_cache(self, key: str) -> None:
        """Remove item from in-memory cache"""
        if key in self._memory_cache:
            del self._memory_cache[key]
        if key in self._memory_access_order:
            self._memory_access_order.remove(key)

    def _is_expired(self, cached_item: Dict[str, Any]) -> bool:
        """Check if cached item has expired"""
        return datetime.now() > cached_item["expire_time"]

    async def invalidate(
        self,
        data_type: Optional[str] = None,
        app_concept: Optional[str] = None,
        target_market: Optional[str] = None
    ) -> int:
        """
        Invalidate cache entries matching criteria

        Args:
            data_type: Specific data type to clear (None for all)
            app_concept: Specific app concept to clear (None for all)
            target_market: Specific market to clear (None for all)

        Returns:
            Number of keys invalidated
        """
        invalidated = 0

        # Clear Redis cache
        if self._redis_available:
            try:
                # Build pattern for keys to delete
                if data_type:
                    pattern = self.KEY_PREFIXES.get(data_type, "jina:*") + "*"
                else:
                    pattern = "jina:*"

                # Find and delete matching keys
                cursor = 0
                while True:
                    cursor, keys = await self._redis_client.scan(cursor, match=pattern, count=100)
                    if keys:
                        await self._redis_client.delete(*keys)
                        invalidated += len(keys)
                    if cursor == 0:
                        break

            except Exception as e:
                logger.warning(f"Redis invalidation error: {str(e)}")

        # Clear memory cache
        if self.enable_in_memory_fallback:
            keys_to_remove = []
            for key in self._memory_cache:
                # Check if key matches criteria
                if data_type and not key.startswith(self.KEY_PREFIXES.get(data_type, "")):
                    continue
                # Note: Can't easily filter by app_concept/target_market in memory cache
                keys_to_remove.append(key)

            for key in keys_to_remove:
                self._remove_from_memory_cache(key)

            invalidated += len(keys_to_remove)

        logger.info(f"Invalidated {invalidated} cache entries")
        return invalidated

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics

        Returns:
            Cache statistics dictionary
        """
        total_requests = self.stats["hits"] + self.stats["fallback_hits"] + self.stats["misses"]
        total_hits = self.stats["hits"] + self.stats["fallback_hits"]
        hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0

        stats = {
            "redis_available": self._redis_available,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests,
            "memory_cache_size": len(self._memory_cache),
            "memory_cache_max_size": self.max_memory_items,
            **self.stats
        }

        # Add Redis info if available
        if self._redis_available and self._redis_client:
            try:
                redis_info = await self._redis_client.info()
                stats["redis_memory_used"] = redis_info.get("used_memory_human", "N/A")
                stats["redis_connected_clients"] = redis_info.get("connected_clients", 0)
            except Exception as e:
                logger.warning(f"Failed to get Redis info: {str(e)}")

        return stats

    def estimate_cost_savings(
        self,
        search_cost_per_query: float = 0.0001,
        extraction_cost_per_url: float = 0.0002
    ) -> Dict[str, Any]:
        """
        Estimate cost savings from cache hits

        Args:
            search_cost_per_query: Cost per web search query
            extraction_cost_per_url: Cost per content extraction

        Returns:
            Cost savings estimate
        """
        # Rough estimate: each hit saves at least one API call
        estimated_savings = (
            self.stats["hits"] * search_cost_per_query +
            self.stats["fallback_hits"] * search_cost_per_query
        )

        return {
            "cache_hits": self.stats["hits"],
            "fallback_hits": self.stats["fallback_hits"],
            "estimated_cost_saved": round(estimated_savings, 6),
            "cost_per_search": search_cost_per_query,
            "cost_per_extraction": extraction_cost_per_url
        }

    async def close(self) -> None:
        """Close Redis connection"""
        if self._redis_client:
            await self._redis_client.close()
            logger.info("Jina cache connection closed")


# Global cache instance
_jina_cache: Optional[JinaCache] = None


async def get_jina_cache(
    redis_url: str = "redis://localhost:6379/0",
    redis_db: int = 1,
    **kwargs
) -> JinaCache:
    """
    Get or create global Jina cache instance

    Args:
        redis_url: Redis connection URL
        redis_db: Redis database number
        **kwargs: Additional cache configuration

    Returns:
        JinaCache instance
    """
    global _jina_cache

    if _jina_cache is None:
        _jina_cache = JinaCache(redis_url=redis_url, redis_db=redis_db, **kwargs)
        await _jina_cache.initialize()

    return _jina_cache


def generate_market_cache_key(app_concept: str, target_market: str) -> str:
    """
    Generate cache key for market research queries

    Args:
        app_concept: Application concept
        target_market: Target market

    Returns:
        Cache key string
    """
    combined = f"{app_concept.lower().strip()}|{target_market.lower().strip()}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]