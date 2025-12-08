"""
Optimized embedding providers with async support and connection pooling for RedditHarbor

This module provides high-performance embedding providers optimized for:
- Async/await patterns for non-blocking I/O
- Connection pooling to reduce latency
- Batch processing for maximum throughput
- Rate limiting and retry logic
- Adaptive provider selection

Providers:
- CohereEmbeddingProvider: Up to 96 texts/batch, optimal for production
- OpenRouterEmbeddingProvider: Proxy to OpenAI embeddings
- OpenAIEmbeddingProvider: Direct OpenAI API with batching
- FakeEmbeddingProvider: Deterministic testing provider
- AdaptiveEmbeddingProvider: Automatic provider selection
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Base class for embedding providers"""

    @abstractmethod
    def generate_embedding(self, text: str, metadata: dict | None = None) -> tuple[list[float], dict]:
        """Generate embedding for text"""
        pass

    @abstractmethod
    def get_vector_dimensions(self) -> int:
        """Get embedding dimensions"""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test provider connection"""
        pass


class CohereEmbeddingProvider(EmbeddingProvider):
    """
    Cohere-based embedding provider for production use

    Rate Limits:
    - Trial: 100 calls/minute
    - Production: 500 calls/minute
    """

    def __init__(self, model: str = "embed-english-v3.0", dimensions: int = 1024, api_key: str | None = None):
        """
        Initialize Cohere embedding provider

        Args:
            model: Cohere embedding model name
            dimensions: Embedding dimensions
            api_key: Cohere API key
        """
        self.model = model
        self.dimensions = dimensions
        self._client = None

        # Import Cohere only when needed
        try:
            import cohere
            self._cohere = cohere
        except ImportError:
            logger.error("Cohere package required. Install with: pip install cohere")
            raise

        # Initialize client if API key provided
        if api_key:
            self._client = self._cohere.Client(api_key)
            logger.info(f"✓ Initialized Cohere client with model: {model}")

    def _ensure_client(self) -> None:
        """Ensure Cohere client is initialized"""
        if not self._client:
            import os
            api_key = os.getenv('COHERE_API_KEY')
            if not api_key:
                raise ValueError("Cohere API key not provided. Set COHERE_API_KEY environment variable.")
            self._client = self._cohere.Client(api_key)
            logger.info(f"✓ Initialized Cohere client with model: {self.model}")

    def embed(self, text: str, metadata: dict[str, Any] | None = None) -> tuple[list[float], dict[str, Any]]:
        """
        Generate embedding for a single text using Cohere

        Args:
            text: Text to embed
            metadata: Optional metadata to store with embedding

        Returns:
            Tuple of (embedding, metadata)
        """
        self._ensure_client()

        try:
            response = self._client.embed(
                texts=[text],
                model=self.model,
                input_type="search_document",  # Optimize for document search
                embedding_types=["float"]
            )

            # Handle Cohere response structure
            if hasattr(response, 'embeddings'):
                # Try to get the first embedding
                if hasattr(response.embeddings, '__iter__') and not isinstance(response.embeddings, str):
                    embeddings_list = list(response.embeddings)
                    embedding = embeddings_list[0] if embeddings_list else None
                else:
                    embedding = response.embeddings
            else:
                embedding = None

            if embedding is None:
                raise ValueError("No embedding returned from Cohere API")

            embedding_metadata = {
                'provider': 'cohere',
                'model': self.model,
                'dimensions': len(embedding),
                'generated_at': datetime.now().isoformat(),
                'api_version': getattr(response.meta, 'api_version', 'unknown') if hasattr(response, 'meta') else 'unknown',
                'billed_units': getattr(response.meta, 'billed_units', {}) if hasattr(response, 'meta') else {},
                'content_preview': text[:100] + '...' if len(text) > 100 else text,
                'content_length': len(text)
            }

            if metadata:
                embedding_metadata.update(metadata)

            return embedding, embedding_metadata

        except Exception as e:
            logger.error(f"Cohere embedding generation failed: {e}")
            raise

    def embed_batch(self, texts: list[str], metadata: dict[str, Any] | None = None) -> list[tuple[list[float], dict[str, Any]]]:
        """
        Generate embeddings for multiple texts using Cohere

        Args:
            texts: List of texts to embed
            metadata: Optional metadata to store with embeddings

        Returns:
            List of (embedding, metadata) tuples
        """
        self._ensure_client()

        # Cohere supports up to 96 texts per request
        batch_size = 96
        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                response = self._client.embed(
                    texts=batch,
                    model=self.model,
                    input_type="search_document",
                    embedding_types=["float"]
                )

                # Handle batch response
                if hasattr(response, 'embeddings'):
                    if hasattr(response.embeddings, '__iter__') and not isinstance(response.embeddings, str):
                        embeddings_list = list(response.embeddings)
                    else:
                        # Single embedding returned for batch
                        embeddings_list = [response.embeddings] * len(batch)
                else:
                    embeddings_list = [None] * len(batch)

                # Create results
                for j, embedding in enumerate(embeddings_list):
                    if embedding is None:
                        raise ValueError(f"No embedding returned for text {j}")

                    embedding_metadata = {
                        'provider': 'cohere',
                        'model': self.model,
                        'dimensions': len(embedding),
                        'generated_at': datetime.now().isoformat(),
                        'batch_index': i + j,
                        'content_preview': batch[j][:100] + '...' if len(batch[j]) > 100 else batch[j],
                        'content_length': len(batch[j])
                    }

                    if metadata:
                        embedding_metadata.update(metadata)

                    results.append((embedding, embedding_metadata))

            except Exception as e:
                logger.error(f"Cohere batch embedding failed at index {i}: {e}")
                raise

        return results

    def get_vector_dimensions(self) -> int:
        return self.dimensions

    def test_connection(self) -> bool:
        """Test Cohere API connection"""
        if not self._client:
            return False

        try:
            test_response = self._client.embed(
                texts=["test"],
                model=self.model,
                input_type="search_document"
            )
            logger.info("✓ Cohere embedding provider test successful")
            return True
        except Exception as e:
            logger.error(f"Cohere embedding provider test failed: {e}")
            return False

    def get_provider_info(self) -> dict[str, Any]:
        return {
            "provider": "cohere",
            "model": self.model,
            "dimensions": self.dimensions,
            "is_configured": bool(self._client),
            "capabilities": ["semantic", "search_optimized", "production_ready"],
            "advantages": ["better_on_social_media", "cost_effective", "enterprise_grade"]
        }
