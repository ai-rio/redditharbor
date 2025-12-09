"""
Optimized embedding providers with async support and connection pooling
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import aiohttp
import numpy as np

logger = logging.getLogger(__name__)


class BaseEmbeddingProvider(ABC):
    """Base class for embedding providers with async support"""

    def __init__(self, model: str, dimensions: int, api_key: str | None = None):
        self.model = model
        self.dimensions = dimensions
        self.api_key = api_key
        self.session = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self._initialize_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._close_session()

    async def _initialize_session(self):
        """Initialize HTTP session with connection pooling"""
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=100,  # Total connection pool size
                limit_per_host=20,  # Connections per host
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            timeout = aiohttp.ClientTimeout(total=30, connect=5)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )

    async def _close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

    @abstractmethod
    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for single text"""
        pass

    @abstractmethod
    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for batch of texts"""
        pass

    def generate_embedding_sync(self, text: str) -> tuple[list[float], dict[str, Any]]:
        """Synchronous wrapper for backward compatibility"""
        # Run async method in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.generate_embedding(text))
            metadata = {
                'provider': self.__class__.__name__,
                'model': self.model,
                'dimensions': len(result),
                'generated_at': datetime.now().isoformat()
            }
            return result, metadata
        finally:
            loop.close()


class CohereEmbeddingProvider(BaseEmbeddingProvider):
    """
    Cohere AI embedding provider with optimized async batching

    Supports up to 96 texts per batch for optimal throughput
    """

    def __init__(
        self,
        model: str = "embed-english-v3.0",
        dimensions: int = 1024,
        api_key: str | None = None,
        base_url: str = "https://api.cohere.ai/v1"
    ):
        super().__init__(model, dimensions, api_key)
        self.base_url = base_url
        self.max_batch_size = 96  # Cohere's maximum batch size
        self.rate_limit_delay = 0.1  # 100ms between batches

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for single text"""
        embeddings = await self.generate_embeddings_batch([text])
        return embeddings[0]

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for batch of texts"""
        if not self.session:
            await self._initialize_session()

        if not texts:
            return []

        # Split into chunks if exceeding max batch size
        all_embeddings = []
        for i in range(0, len(texts), self.max_batch_size):
            batch = texts[i:i + self.max_batch_size]
            batch_embeddings = await self._generate_batch_request(batch)
            all_embeddings.extend(batch_embeddings)

            # Rate limiting between batches
            if i + self.max_batch_size < len(texts):
                await asyncio.sleep(self.rate_limit_delay)

        return all_embeddings

    async def _generate_batch_request(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a single batch"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Client-Name": "RedditHarbor/1.0"
        }

        payload = {
            "model": self.model,
            "texts": texts,
            "input_type": "search_document"
        }

        try:
            async with self.session.post(
                f"{self.base_url}/embed",
                json=payload,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return [embedding for embedding in data["embeddings"]]
                else:
                    error_text = await response.text()
                    logger.error(f"Cohere API error: {response.status} - {error_text}")
                    # Return zero embeddings on error
                    return [[0.0] * self.dimensions for _ in texts]

        except TimeoutError:
            logger.error("Cohere API timeout")
            return [[0.0] * self.dimensions for _ in texts]

        except Exception as e:
            logger.error(f"Cohere API error: {e}")
            return [[0.0] * self.dimensions for _ in texts]

    def get_provider_info(self) -> dict[str, Any]:
        """Get provider information"""
        return {
            "provider": "Cohere",
            "model": self.model,
            "dimensions": self.dimensions,
            "max_batch_size": self.max_batch_size,
            "features": ["async_support", "batch_processing", "connection_pooling"],
            "cost_per_m_tokens": 0.10,
            "rate_limit": "100-500 calls/minute"
        }


class OpenRouterEmbeddingProvider(BaseEmbeddingProvider):
    """
    OpenRouter embedding provider with async support

    Note: OpenRouter doesn't directly support embeddings,
    this routes to OpenAI through OpenRouter's proxy
    """

    def __init__(
        self,
        model: str = "openai/text-embedding-3-small",
        dimensions: int = 1536,
        api_key: str | None = None,
        base_url: str = "https://openrouter.ai/api/v1"
    ):
        super().__init__(model, dimensions, api_key)
        self.base_url = base_url

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for single text"""
        if not self.session:
            await self._initialize_session()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://redditharbor.ai",
            "X-Title": "RedditHarbor"
        }

        payload = {
            "model": self.model,
            "input": text,
            "encoding_format": "float"
        }

        try:
            async with self.session.post(
                f"{self.base_url}/embeddings",
                json=payload,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["data"][0]["embedding"]
                else:
                    error_text = await response.text()
                    logger.error(f"OpenRouter API error: {response.status} - {error_text}")
                    return [0.0] * self.dimensions

        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            return [0.0] * self.dimensions

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for batch (processes individually)"""
        if not texts:
            return []

        # OpenRouter doesn't support batch embeddings, process individually
        tasks = [self.generate_embedding(text) for text in texts]
        return await asyncio.gather(*tasks)

    def get_provider_info(self) -> dict[str, Any]:
        """Get provider information"""
        return {
            "provider": "OpenRouter",
            "model": self.model,
            "dimensions": self.dimensions,
            "max_batch_size": 1,  # No batch support
            "features": ["async_support"],
            "note": "OpenRouter proxies to OpenAI for embeddings"
        }


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    OpenAI embedding provider with async support and batching
    """

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536,
        api_key: str | None = None,
        base_url: str = "https://api.openai.com/v1"
    ):
        super().__init__(model, dimensions, api_key)
        self.base_url = base_url
        self.max_batch_size = 2048  # OpenAI's limit

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for single text"""
        embeddings = await self.generate_embeddings_batch([text])
        return embeddings[0]

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for batch of texts"""
        if not self.session:
            await self._initialize_session()

        if not texts:
            return []

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "input": texts,
            "encoding_format": "float"
        }

        # Apply dimensions if specified and supported
        if self.dimensions != 1536 and "3-" in self.model:
            payload["dimensions"] = self.dimensions

        try:
            async with self.session.post(
                f"{self.base_url}/embeddings",
                json=payload,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    # Sort by index to maintain order
                    sorted_data = sorted(data["data"], key=lambda x: x["index"])
                    return [item["embedding"] for item in sorted_data]
                else:
                    error_text = await response.text()
                    logger.error(f"OpenAI API error: {response.status} - {error_text}")
                    return [[0.0] * self.dimensions for _ in texts]

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return [[0.0] * self.dimensions for _ in texts]

    def get_provider_info(self) -> dict[str, Any]:
        """Get provider information"""
        return {
            "provider": "OpenAI",
            "model": self.model,
            "dimensions": self.dimensions,
            "max_batch_size": self.max_batch_size,
            "features": ["async_support", "batch_processing", "connection_pooling"],
            "cost_per_m_tokens": 0.02
        }


class FakeEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic fake embedding provider for testing
    """

    def __init__(
        self,
        model: str = "fake-embeddings",
        dimensions: int = 1536,
        value_range: tuple[float, float] = (-1.0, 1.0)
    ):
        super().__init__(model, dimensions, None)
        self.value_range = value_range
        np.random.seed(42)  # For reproducible embeddings

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate deterministic embedding for text"""
        # Create hash-based embedding for consistency
        hash_val = hash(text) % (2 ** 32)
        np.random.seed(hash_val)
        embedding = np.random.uniform(
            self.value_range[0],
            self.value_range[1],
            self.dimensions
        ).tolist()
        return embedding

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for batch"""
        return [await self.generate_embedding(text) for text in texts]

    def get_provider_info(self) -> dict[str, Any]:
        """Get provider information"""
        return {
            "provider": "Fake",
            "model": self.model,
            "dimensions": self.dimensions,
            "features": ["deterministic", "cost_free", "offline"],
            "use_case": "Testing and development"
        }


class AdaptiveEmbeddingProvider:
    """
    Adaptive embedding provider that automatically selects best provider
    based on throughput, cost, and reliability metrics
    """

    def __init__(self, providers: list[BaseEmbeddingProvider]):
        self.providers = providers
        self.current_provider_index = 0
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_latency": 0.0,
            "provider_stats": [{} for _ in providers]
        }

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings with adaptive provider selection"""
        if not texts:
            return []

        # Try current provider first
        provider = self.providers[self.current_provider_index]
        start_time = datetime.now()

        try:
            embeddings = await provider.generate_embeddings_batch(texts)
            latency = (datetime.now() - start_time).total_seconds()

            # Update metrics
            self.metrics["total_requests"] += 1
            self.metrics["successful_requests"] += 1
            self.metrics["total_latency"] += latency

            # Update provider stats
            stats = self.metrics["provider_stats"][self.current_provider_index]
            stats["requests"] = stats.get("requests", 0) + 1
            stats["successes"] = stats.get("successes", 0) + 1
            stats["avg_latency"] = (
                (stats.get("avg_latency", 0) * (stats.get("requests", 0) - 1) + latency) /
                stats.get("requests", 1)
            )

            return embeddings

        except Exception as e:
            logger.error(f"Provider {self.current_provider_index} failed: {e}")

            # Update failure metrics
            self.metrics["total_requests"] += 1
            self.metrics["failed_requests"] += 1

            stats = self.metrics["provider_stats"][self.current_provider_index]
            stats["requests"] = stats.get("requests", 0) + 1
            stats["failures"] = stats.get("failures", 0) + 1

            # Try fallback providers
            for i, fallback_provider in enumerate(self.providers):
                if i == self.current_provider_index:
                    continue  # Skip the one that failed

                try:
                    logger.info(f"Falling back to provider {i}")
                    embeddings = await fallback_provider.generate_embeddings_batch(texts)

                    # Update current provider
                    self.current_provider_index = i
                    logger.info(f"Switched to provider {i} as primary")

                    return embeddings

                except Exception as fallback_error:
                    logger.error(f"Fallback provider {i} also failed: {fallback_error}")

            # All providers failed
            logger.error("All embedding providers failed")
            return [[0.0] * provider.dimensions for _ in texts]

    def get_metrics(self) -> dict[str, Any]:
        """Get comprehensive metrics"""
        return {
            **self.metrics,
            "success_rate": (
                self.metrics["successful_requests"] / self.metrics["total_requests"]
                if self.metrics["total_requests"] > 0 else 0
            ),
            "average_latency": (
                self.metrics["total_latency"] / self.metrics["successful_requests"]
                if self.metrics["successful_requests"] > 0 else 0
            ),
            "current_provider": self.current_provider_index
        }

    async def health_check(self) -> dict[int, bool]:
        """Check health of all providers"""
        results = {}
        test_text = "Health check test"

        for i, provider in enumerate(self.providers):
            try:
                embedding = await provider.generate_embedding(test_text)
                results[i] = len(embedding) > 0
            except:
                results[i] = False

        return results
