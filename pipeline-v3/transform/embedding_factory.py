"""
Embedding provider factory with support for multiple backends
"""

import logging
from datetime import datetime
from typing import Any

from .embedding_providers_new import (
    CohereEmbeddingProvider,
    GoogleVertexAIEmbeddingProvider,
    JinaAIEmbeddingProvider,
    VoyageAIEmbeddingProvider,
)
from .embedding_strategies import (
    EmbeddingStrategy,
    FakeEmbeddingProvider,
    OpenAIEmbeddingProvider,
    OpenRouterEmbeddingProvider,
)

logger = logging.getLogger(__name__)


class EmbeddingFactory:
    """
    Factory for creating embedding providers with fallback support

    Supported providers:
    - fake: Deterministic hash-based embeddings (free, for testing)
    - openrouter: OpenRouter LLM API (not currently supporting embeddings)
    - openai: Direct OpenAI API (production)
    - local: sentence-transformers (free, local inference)
    - cohere: Cohere AI embeddings (production, enterprise-ready)
    - voyage: Voyage AI embeddings (cost-effective, OpenAI-compatible)
    - jina: Jina AI embeddings (async support, automatic retry)
    - vertexai: Google Vertex AI embeddings (enterprise grade)
    """

    @staticmethod
    def create_provider(
        provider_type: str,
        model: str | None = None,
        dimensions: int | None = None,
        api_key: str | None = None,
        fallback_provider: str | None = None
    ) -> EmbeddingStrategy:
        """
        Create an embedding strategy with optional fallback

        Args:
            provider_type: Primary provider type (fake, openai, openrouter, local, cohere, voyage, jina, vertexai)
            model: Model name for the provider
            dimensions: Embedding dimensions (default varies by provider)
            api_key: API key for the provider (if needed)
            fallback_provider: Fallback provider type

        Returns:
            Configured EmbeddingStrategy
        """
        primary_provider = EmbeddingFactory._create_single_provider(
            provider_type, model, dimensions, api_key
        )

        fallback = None
        if fallback_provider:
            fallback = EmbeddingFactory._create_single_provider(
                fallback_provider, model, dimensions, api_key
            )

        return EmbeddingStrategy(primary_provider, fallback)

    @staticmethod
    def _create_single_provider(
        provider_type: str,
        model: str | None = None,
        dimensions: int | None = None,
        api_key: str | None = None
    ):
        """Create a single embedding provider"""

        if provider_type == "fake":
            return FakeEmbeddingProvider(
                dimensions=dimensions or 1536,
                value_range=(-1.0, 1.0)
            )

        elif provider_type == "openrouter":
            logger.warning(
                "OpenRouter does not support embeddings. "
                "Use 'openai' for embeddings via OpenAI API directly."
            )
            return OpenRouterEmbeddingProvider(
                model=model or "openai/text-embedding-3-small",
                dimensions=dimensions or 1536
            )

        elif provider_type == "openai":
            return OpenAIEmbeddingProvider(
                model=model or "text-embedding-3-small",
                dimensions=dimensions or 1536
            )

        elif provider_type == "local":
            return LocalEmbeddingProvider(
                model=model or "all-MiniLM-L6-v2",
                dimensions=dimensions or 384
            )

        elif provider_type == "cohere":
            return CohereEmbeddingProvider(
                model=model or "embed-english-v3.0",
                dimensions=dimensions or 1024,
                api_key=api_key
            )

        elif provider_type == "voyage":
            return VoyageAIEmbeddingProvider(
                model=model or "voyage-large-2",
                dimensions=dimensions or 1536,
                api_key=api_key
            )

        elif provider_type == "jina":
            return JinaAIEmbeddingProvider(
                model=model or "jina-embeddings-v3",
                dimensions=dimensions or 1024,
                api_key=api_key
            )

        elif provider_type == "vertexai":
            return GoogleVertexAIEmbeddingProvider(
                model=model or "textembedding-gecko@003",
                dimensions=dimensions or 768,
                project_id=api_key  # Using api_key to pass project_id for simplicity
            )

        else:
            raise ValueError(f"Unsupported embedding provider: {provider_type}")

    @staticmethod
    def get_provider_info() -> dict[str, Any]:
        """Get information about available providers"""
        return {
            "fake": {
                "description": "Deterministic hash-based embeddings",
                "cost": "Free",
                "dimensions": "Configurable (default: 1536)",
                "use_case": "Testing and development",
                "requires_api_key": False
            },
            "openai": {
                "description": "OpenAI text-embedding-3-small via direct API",
                "cost": "$0.00002 per 1K tokens",
                "dimensions": "1536",
                "use_case": "Production with high quality",
                "requires_api_key": True
            },
            "openrouter": {
                "description": "OpenRouter (LLM API only)",
                "cost": "Not applicable - no embeddings",
                "dimensions": "N/A",
                "use_case": "Not recommended for embeddings",
                "requires_api_key": True,
                "note": "OpenRouter focuses on LLMs, not embeddings"
            },
            "local": {
                "description": "sentence-transformers local inference",
                "cost": "Free (CPU/GPU usage)",
                "dimensions": "Model dependent (384 for MiniLM)",
                "use_case": "Cost optimization and offline use",
                "requires_api_key": False
            },
            "cohere": {
                "description": "Cohere AI embeddings with enterprise features",
                "cost": "$0.10 per 1M tokens",
                "dimensions": "1024",
                "use_case": "Production with enterprise reliability",
                "requires_api_key": True,
                "rate_limits": "100-500 calls/minute"
            },
            "voyage": {
                "description": "Voyage AI - cost-effective, OpenAI-compatible",
                "cost": "$0.12 per 1M tokens",
                "dimensions": "1536",
                "use_case": "Cost-optimized production",
                "requires_api_key": True,
                "batch_size": "256 texts per request",
                "migration_difficulty": "Low (OpenAI-compatible)"
            },
            "jina": {
                "description": "Jina AI embeddings with async support",
                "cost": "$0.03 per 1M tokens",
                "dimensions": "1024",
                "use_case": "High-performance with automatic retry",
                "requires_api_key": True,
                "features": ["async_support", "auto_rate_limit", "built_in_retry"],
                "batch_size": "256 texts per batch"
            },
            "vertexai": {
                "description": "Google Vertex AI enterprise embeddings",
                "cost": "$0.0001 per 1K characters",
                "dimensions": "768",
                "use_case": "Enterprise scale with Google infrastructure",
                "requires_api_key": True,
                "infrastructure": "Google Cloud Platform",
                "advantages": ["scalability", "reliability", "enterprise_support"]
            }
        }


class LocalEmbeddingProvider:
    """
    Local sentence-transformers embedding provider
    """

    def __init__(self, model: str = "all-MiniLM-L6-v2", dimensions: int = 384):
        self.model = model
        self.dimensions = dimensions
        self._model = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the sentence transformer model"""
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model)
            logger.info(f"✓ Loaded local embedding model: {self.model}")
        except ImportError:
            raise RuntimeError(
                "sentence-transformers package required. "
                "Install with: pip install sentence-transformers torch"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load model {self.model}: {e}")

    def generate_embedding(self, text: str, metadata=None):
        """Generate embedding using local model"""
        if not self._model:
            raise RuntimeError("Model not initialized")

        embedding = self._model.encode(text, convert_to_numpy=True)
        embedding_list = embedding.tolist()

        embedding_metadata = {
            'provider': 'local',
            'model': self.model,
            'dimensions': len(embedding_list),
            'generated_at': str(datetime.now()),
            'content_preview': text[:100] + '...' if len(text) > 100 else text,
            'content_length': len(text),
            'cost_estimate': 0.0  # Free
        }

        if metadata:
            embedding_metadata.update(metadata)

        return embedding_list, embedding_metadata

    def get_vector_dimensions(self) -> int:
        return self.dimensions

    def test_connection(self) -> bool:
        """Test model is loaded"""
        return self._model is not None

    def get_provider_info(self) -> dict[str, Any]:
        return {
            "provider": "local",
            "model": self.model,
            "dimensions": self.dimensions,
            "is_configured": self._model is not None,
            "capabilities": ["semantic", "local_inference", "cost_effective"],
            "cost_model": "Free (local CPU/GPU usage)",
            "advantages": ["free", "offline", "fast", "privacy_preserving"]
        }
