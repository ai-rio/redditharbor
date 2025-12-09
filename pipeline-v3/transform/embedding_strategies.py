"""
Embedding generation strategies with pluggable providers
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Abstract base class for embedding generation providers"""

    @abstractmethod
    def generate_embedding(self, text: str, metadata: dict[str, Any] | None = None) -> tuple[list[float], dict[str, Any]]:
        """
        Generate embedding vector for given text

        Args:
            text: Text to generate embedding for
            metadata: Optional metadata to include in embedding metadata

        Returns:
            Tuple of (embedding_vector, embedding_metadata)
        """
        pass

    @abstractmethod
    def get_vector_dimensions(self) -> int:
        """Get the dimensions of the embedding vectors"""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test connection to the embedding service"""
        pass

    @abstractmethod
    def get_provider_info(self) -> dict[str, Any]:
        """Get provider information"""
        pass


class FakeEmbeddingProvider(EmbeddingProvider):
    """
    Fake embedding provider for testing and development
    Uses deterministic hash-based embedding generation
    """

    def __init__(self, dimensions: int = 384, value_range: tuple[float, float] = (-1.0, 1.0)):
        """
        Initialize fake embedding provider

        Args:
            dimensions: Number of dimensions for embedding vectors
            value_range: Min/max range for embedding values
        """
        self.dimensions = dimensions
        self.min_value, self.max_value = value_range
        self.provider_name = f"fake-embedding-v{dimensions}"

    def generate_embedding(self, text: str, metadata: dict[str, Any] | None = None) -> tuple[list[float], dict[str, Any]]:
        """
        Generate deterministic embedding using hash-based approach

        Args:
            text: Text to generate embedding for
            metadata: Optional metadata to include

        Returns:
            Tuple of (embedding_vector, embedding_metadata)
        """
        import hashlib

        # Create content hash for consistency
        content_hash = hashlib.md5(text.encode()).hexdigest()

        # Generate deterministic embedding vector
        embedding = self._hash_to_vector(content_hash)

        # Create comprehensive metadata
        embedding_metadata = {
            'provider': 'fake',
            'model': self.provider_name,
            'dimensions': self.dimensions,
            'value_range': (self.min_value, self.max_value),
            'generated_at': datetime.now().isoformat(),
            'content_hash': content_hash,
            'method': 'hash-based-deterministic',
            'content_preview': text[:100] + '...' if len(text) > 100 else text,
            'content_length': len(text)
        }

        # Merge additional metadata if provided
        if metadata:
            embedding_metadata.update(metadata)

        return embedding, embedding_metadata

    def _hash_to_vector(self, content_hash: str) -> list[float]:
        """
        Convert hash to deterministic embedding vector

        Args:
            content_hash: MD5 hash string

        Returns:
            List of float values representing embedding
        """
        embedding = []

        for i in range(self.dimensions):
            # Create deterministic seed based on position and hash
            hash_segment = content_hash[i % len(content_hash):min(i % len(content_hash) + 2, len(content_hash))]
            seed = int(hash_segment or '00', 16) + i

            # Generate value within specified range
            normalized_value = (seed % 1000) / 1000.0  # 0.0 to 1.0
            scaled_value = self.min_value + normalized_value * (self.max_value - self.min_value)

            embedding.append(scaled_value)

        return embedding

    def get_vector_dimensions(self) -> int:
        return self.dimensions

    def test_connection(self) -> bool:
        logger.info("✓ Fake embedding provider test successful")
        return True

    def get_provider_info(self) -> dict[str, Any]:
        return {
            "provider": "fake",
            "model": self.provider_name,
            "dimensions": self.dimensions,
            "value_range": (self.min_value, self.max_value),
            "is_configured": True,
            "capabilities": ["deterministic", "hash_based", "no_external_dependencies"]
        }


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """
    OpenAI-based embedding provider for production use
    """

    def __init__(self, model: str = "text-embedding-3-small", dimensions: int = 1536):
        """
        Initialize OpenAI embedding provider

        Args:
            model: OpenAI embedding model name
            dimensions: Embedding dimensions (will be validated against model capabilities)
        """
        self.model = model
        self.dimensions = dimensions
        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI

            from config import get_settings

            settings = get_settings()
            # Use the dedicated embedding configuration
            embedding_config = settings.get_openai_embedding_config()
            self._client = OpenAI(**embedding_config)

        except ImportError:
            raise RuntimeError("openai package is required for OpenAIEmbeddingProvider")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OpenAI client: {e}")

    def generate_embedding(self, text: str, metadata: dict[str, Any] | None = None) -> tuple[list[float], dict[str, Any]]:
        """
        Generate embedding using OpenAI API

        Args:
            text: Text to generate embedding for
            metadata: Optional metadata to include

        Returns:
            Tuple of (embedding_vector, embedding_metadata)
        """
        if not self._client:
            raise RuntimeError("OpenAI client not initialized")

        try:
            response = self._client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=self.dimensions if self.dimensions <= 1536 else None
            )

            embedding = response.data[0].embedding

            embedding_metadata = {
                'provider': 'openai',
                'model': self.model,
                'dimensions': len(embedding),
                'generated_at': datetime.now().isoformat(),
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                'content_preview': text[:100] + '...' if len(text) > 100 else text,
                'content_length': len(text)
            }

            # Merge additional metadata if provided
            if metadata:
                embedding_metadata.update(metadata)

            return embedding, embedding_metadata

        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {e}")
            raise RuntimeError(f"Failed to generate embedding: {e}")

    def get_vector_dimensions(self) -> int:
        return self.dimensions

    def test_connection(self) -> bool:
        """Test OpenAI API connection"""
        if not self._client:
            return False

        try:
            test_response = self._client.embeddings.create(
                model=self.model,
                input="test"
            )
            logger.info("✓ OpenAI embedding provider test successful")
            return True
        except Exception as e:
            logger.error(f"OpenAI embedding provider test failed: {e}")
            return False

    def get_provider_info(self) -> dict[str, Any]:
        return {
            "provider": "openai",
            "model": self.model,
            "dimensions": self.dimensions,
            "is_configured": bool(self._client),
            "capabilities": ["semantic", "context_aware", "production_ready"]
        }


class EmbeddingStrategy:
    """
    Strategy pattern implementation for embedding generation
    Manages provider selection and fallback handling
    """

    def __init__(self, provider: EmbeddingProvider, fallback_provider: EmbeddingProvider | None = None):
        """
        Initialize embedding strategy

        Args:
            provider: Primary embedding provider
            fallback_provider: Optional fallback provider if primary fails
        """
        self.primary_provider = provider
        self.fallback_provider = fallback_provider

    def generate_embedding(self, text: str, metadata: dict[str, Any] | None = None) -> tuple[list[float], dict[str, Any]]:
        """
        Generate embedding using primary provider with fallback

        Args:
            text: Text to generate embedding for
            metadata: Optional metadata to include

        Returns:
            Tuple of (embedding_vector, embedding_metadata)
        """
        try:
            # Try primary provider first
            embedding, metadata_result = self.primary_provider.generate_embedding(text, metadata)
            metadata_result['provider_used'] = 'primary'
            return embedding, metadata_result

        except Exception as e:
            logger.warning(f"Primary embedding provider failed: {e}")

            if self.fallback_provider:
                try:
                    logger.info("Attempting fallback embedding provider")
                    embedding, metadata_result = self.fallback_provider.generate_embedding(text, metadata)
                    metadata_result['provider_used'] = 'fallback'
                    return embedding, metadata_result

                except Exception as fallback_error:
                    logger.error(f"Fallback embedding provider also failed: {fallback_error}")

            raise RuntimeError(f"All embedding providers failed for text: {text[:50]}...")

    def get_strategy_info(self) -> dict[str, Any]:
        """Get information about current embedding strategy"""
        return {
            "primary_provider": self.primary_provider.get_provider_info(),
            "fallback_provider": self.fallback_provider.get_provider_info() if self.fallback_provider else None,
            "vector_dimensions": self.primary_provider.get_vector_dimensions()
        }

    def test_strategy(self) -> bool:
        """Test the complete embedding strategy"""
        primary_ok = self.primary_provider.test_connection()
        fallback_ok = self.fallback_provider.test_connection() if self.fallback_provider else True

        return primary_ok or fallback_ok
