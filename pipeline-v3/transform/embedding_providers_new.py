"""
New embedding provider implementations for RedditHarbor
Supports Cohere, Voyage AI, Jina AI, and Google Vertex AI
"""

import logging
import time
from datetime import datetime
from typing import Any

from .embedding_strategies import EmbeddingProvider

logger = logging.getLogger(__name__)


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
        self._initialize_client(api_key)

        # Rate limiting
        self.rate_limiter = RateLimitHandler(requests_per_minute=450)  # Conservative
        self.retry_handler = RetryHandler(max_retries=3, backoff_factor=2)

    def _initialize_client(self, api_key: str | None):
        """Initialize Cohere client"""
        try:
            import cohere
            if not api_key:
                from config.settings import get_settings
                settings = get_settings()
                api_key = getattr(settings, 'cohere_api_key', None)

            if not api_key:
                raise ValueError("Cohere API key required")

            self._client = cohere.Client(api_key=api_key)
            logger.info(f"✓ Initialized Cohere client with model: {self.model}")

        except ImportError:
            raise RuntimeError("cohere package required. Install with: pip install cohere")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Cohere client: {e}")

    def generate_embedding(self, text: str, metadata: dict[str, Any] | None = None) -> tuple[list[float], dict[str, Any]]:
        """
        Generate embedding using Cohere API

        Args:
            text: Text to generate embedding for
            metadata: Optional metadata to include

        Returns:
            Tuple of (embedding_vector, embedding_metadata)
        """
        if not self._client:
            raise RuntimeError("Cohere client not initialized")

        # Rate limiting
        self.rate_limiter.wait_if_needed()

        # Retry with backoff
        return self.retry_handler.execute_with_retry(
            lambda: self._do_generate_embedding(text, metadata)
        )

    def _do_generate_embedding(self, text: str, metadata: dict[str, Any] | None):
        """Actual embedding generation"""
        try:
            response = self._client.embed(
                texts=[text],
                model=self.model,
                input_type="search_document",  # Optimize for document search
                embedding_types=["float"]
            )

            embedding = response.embeddings[0]

            embedding_metadata = {
                'provider': 'cohere',
                'model': self.model,
                'dimensions': len(embedding),
                'generated_at': datetime.now().isoformat(),
                'api_version': getattr(response.meta, 'api_version', 'unknown'),
                'billed_units': getattr(response.meta, 'billed_units', {}),
                'content_preview': text[:100] + '...' if len(text) > 100 else text,
                'content_length': len(text)
            }

            if metadata:
                embedding_metadata.update(metadata)

            return embedding, embedding_metadata

        except Exception as e:
            logger.error(f"Cohere embedding generation failed: {e}")
            raise

    def get_vector_dimensions(self) -> int:
        return self.dimensions

    def test_connection(self) -> bool:
        """Test Cohere API connection"""
        if not self._client:
            return False

        try:
            test_response = self._client.embed(
                texts=["test"],
                model=self.model
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
            "rate_limits": {
                "trial": "100 calls/minute",
                "production": "500 calls/minute"
            }
        }


class VoyageAIEmbeddingProvider(EmbeddingProvider):
    """
    Voyage AI-based embedding provider for cost-effective production use
    OpenAI-compatible API with competitive pricing
    """

    def __init__(self, model: str = "voyage-large-2", dimensions: int = 1536, api_key: str | None = None):
        """
        Initialize Voyage AI embedding provider

        Args:
            model: Voyage AI model name
            dimensions: Embedding dimensions
            api_key: Voyage AI API key
        """
        self.model = model
        self.dimensions = dimensions
        self._client = None
        self._initialize_client(api_key)

        # Rate limiting (conservative estimate)
        self.rate_limiter = RateLimitHandler(requests_per_minute=900)
        self.retry_handler = RetryHandler(max_retries=3, backoff_factor=2)

    def _initialize_client(self, api_key: str | None):
        """Initialize Voyage AI client"""
        try:
            import voyageai
            if not api_key:
                from config.settings import get_settings
                settings = get_settings()
                api_key = getattr(settings, 'voyage_api_key', None)

            if not api_key:
                raise ValueError("Voyage AI API key required")

            self._client = voyageai.Client(api_key=api_key)
            logger.info(f"✓ Initialized Voyage AI client with model: {self.model}")

        except ImportError:
            raise RuntimeError("voyageai package required. Install with: pip install voyageai")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Voyage AI client: {e}")

    def generate_embedding(self, text: str, metadata: dict[str, Any] | None = None) -> tuple[list[float], dict[str, Any]]:
        """
        Generate embedding using Voyage AI API

        Args:
            text: Text to generate embedding for
            metadata: Optional metadata to include

        Returns:
            Tuple of (embedding_vector, embedding_metadata)
        """
        if not self._client:
            raise RuntimeError("Voyage AI client not initialized")

        self.rate_limiter.wait_if_needed()

        return self.retry_handler.execute_with_retry(
            lambda: self._do_generate_embedding(text, metadata)
        )

    def _do_generate_embedding(self, text: str, metadata: dict[str, Any] | None):
        """Actual embedding generation"""
        try:
            result = self._client.embed(
                [text],  # Voyage AI expects list
                model=self.model,
                input_type="document"  # For document embeddings
            )

            embedding = result.embeddings[0]

            embedding_metadata = {
                'provider': 'voyage',
                'model': self.model,
                'dimensions': len(embedding),
                'generated_at': datetime.now().isoformat(),
                'total_tokens': result.total_tokens,
                'content_preview': text[:100] + '...' if len(text) > 100 else text,
                'content_length': len(text)
            }

            if metadata:
                embedding_metadata.update(metadata)

            return embedding, embedding_metadata

        except Exception as e:
            logger.error(f"Voyage AI embedding generation failed: {e}")
            raise

    def get_vector_dimensions(self) -> int:
        return self.dimensions

    def test_connection(self) -> bool:
        """Test Voyage AI API connection"""
        if not self._client:
            return False

        try:
            test_response = self._client.embed(
                ["test"],
                model=self.model
            )
            logger.info("✓ Voyage AI embedding provider test successful")
            return True
        except Exception as e:
            logger.error(f"Voyage AI embedding provider test failed: {e}")
            return False

    def get_provider_info(self) -> dict[str, Any]:
        return {
            "provider": "voyage",
            "model": self.model,
            "dimensions": self.dimensions,
            "is_configured": bool(self._client),
            "capabilities": ["semantic", "openai_compatible", "cost_effective"],
            "batch_size": 256,  # Max texts per request
            "advantages": ["cost_effective", "high_performance", "simple_migration"]
        }


class JinaAIEmbeddingProvider(EmbeddingProvider):
    """
    Jina AI-based embedding provider with async support
    """

    def __init__(self, model: str = "jina-embeddings-v3", dimensions: int = 1024, api_key: str | None = None):
        """
        Initialize Jina AI embedding provider

        Args:
            model: Jina AI model name
            dimensions: Embedding dimensions
            api_key: Jina AI API key
        """
        self.model = model
        self.dimensions = dimensions
        self._client = None
        self._initialize_client(api_key)

        # Jina AI has built-in rate limiting, but we'll be conservative
        self.rate_limiter = RateLimitHandler(requests_per_minute=1000)
        self.retry_handler = RetryHandler(max_retries=3, backoff_factor=2)

    def _initialize_client(self, api_key: str | None):
        """Initialize Jina AI client"""
        try:
            from jina_client import Client
            if not api_key:
                from config.settings import get_settings
                settings = get_settings()
                api_key = getattr(settings, 'jina_api_key', None)

            if not api_key:
                raise ValueError("Jina AI API key required")

            self._client = Client(api_key=api_key)
            logger.info(f"✓ Initialized Jina AI client with model: {self.model}")

        except ImportError:
            raise RuntimeError("jina-client package required. Install with: pip install jina-client")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Jina AI client: {e}")

    def generate_embedding(self, text: str, metadata: dict[str, Any] | None = None) -> tuple[list[float], dict[str, Any]]:
        """
        Generate embedding using Jina AI API

        Args:
            text: Text to generate embedding for
            metadata: Optional metadata to include

        Returns:
            Tuple of (embedding_vector, embedding_metadata)
        """
        if not self._client:
            raise RuntimeError("Jina AI client not initialized")

        self.rate_limiter.wait_if_needed()

        return self.retry_handler.execute_with_retry(
            lambda: self._do_generate_embedding(text, metadata)
        )

    def _do_generate_embedding(self, text: str, metadata: dict[str, Any] | None):
        """Actual embedding generation"""
        try:
            result = self._client.embed(
                input=[text],
                model=self.model,
                task="text-matching"  # Optimize for semantic similarity
            )

            embedding = result.data[0].embedding

            embedding_metadata = {
                'provider': 'jina',
                'model': self.model,
                'dimensions': len(embedding),
                'generated_at': datetime.now().isoformat(),
                'usage': result.usage,
                'model_version': result.model,
                'content_preview': text[:100] + '...' if len(text) > 100 else text,
                'content_length': len(text)
            }

            if metadata:
                embedding_metadata.update(metadata)

            return embedding, embedding_metadata

        except Exception as e:
            logger.error(f"Jina AI embedding generation failed: {e}")
            raise

    def get_vector_dimensions(self) -> int:
        return self.dimensions

    def test_connection(self) -> bool:
        """Test Jina AI API connection"""
        if not self._client:
            return False

        try:
            test_response = self._client.embed(
                input=["test"],
                model=self.model
            )
            logger.info("✓ Jina AI embedding provider test successful")
            return True
        except Exception as e:
            logger.error(f"Jina AI embedding provider test failed: {e}")
            return False

    def get_provider_info(self) -> dict[str, Any]:
        return {
            "provider": "jina",
            "model": self.model,
            "dimensions": self.dimensions,
            "is_configured": bool(self._client),
            "capabilities": ["semantic", "async_support", "automatic_retry"],
            "batch_size": 256,  # Max texts per batch
            "features": ["auto_rate_limit", "built_in_retry", "async_operations"]
        }


class GoogleVertexAIEmbeddingProvider(EmbeddingProvider):
    """
    Google Vertex AI embedding provider for enterprise use
    """

    def __init__(self, model: str = "textembedding-gecko@003", dimensions: int = 768, project_id: str | None = None, location: str = "us-central1"):
        """
        Initialize Google Vertex AI embedding provider

        Args:
            model: Vertex AI model name
            dimensions: Embedding dimensions
            project_id: Google Cloud project ID
            location: Google Cloud region
        """
        self.model = model
        self.dimensions = dimensions
        self.project_id = project_id
        self.location = location
        self._client = None
        self._initialize_client()

        # Vertex AI has generous limits but we'll be conservative
        self.rate_limiter = RateLimitHandler(requests_per_minute=900)
        self.retry_handler = RetryHandler(max_retries=3, backoff_factor=2)

    def _initialize_client(self):
        """Initialize Vertex AI client"""
        try:
            from vertexai.init import init as vertexai_init
            from vertexai.language_models import TextEmbeddingModel

            # Initialize Vertex AI
            if self.project_id:
                vertexai_init(project=self.project_id, location=self.location)
            else:
                # Use default credentials
                vertexai_init(location=self.location)

            self._model = TextEmbeddingModel.from_pretrained(self.model)
            logger.info(f"✓ Initialized Vertex AI with model: {self.model}")

        except ImportError:
            raise RuntimeError("vertexai package required. Install with: pip install google-cloud-aiplatform")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Vertex AI: {e}")

    def generate_embedding(self, text: str, metadata: dict[str, Any] | None = None) -> tuple[list[float], dict[str, Any]]:
        """
        Generate embedding using Vertex AI API

        Args:
            text: Text to generate embedding for
            metadata: Optional metadata to include

        Returns:
            Tuple of (embedding_vector, embedding_metadata)
        """
        if not self._model:
            raise RuntimeError("Vertex AI model not initialized")

        self.rate_limiter.wait_if_needed()

        return self.retry_handler.execute_with_retry(
            lambda: self._do_generate_embedding(text, metadata)
        )

    def _do_generate_embedding(self, text: str, metadata: dict[str, Any] | None):
        """Actual embedding generation"""
        try:
            embeddings = self._model.get_embeddings([text])
            embedding = embeddings[0].values

            embedding_metadata = {
                'provider': 'vertexai',
                'model': self.model,
                'dimensions': len(embedding),
                'generated_at': datetime.now().isoformat(),
                'project_id': self.project_id,
                'location': self.location,
                'content_preview': text[:100] + '...' if len(text) > 100 else text,
                'content_length': len(text)
            }

            if metadata:
                embedding_metadata.update(metadata)

            return embedding, embedding_metadata

        except Exception as e:
            logger.error(f"Vertex AI embedding generation failed: {e}")
            raise

    def get_vector_dimensions(self) -> int:
        return self.dimensions

    def test_connection(self) -> bool:
        """Test Vertex AI API connection"""
        if not self._model:
            return False

        try:
            test_embeddings = self._model.get_embeddings(["test"])
            logger.info("✓ Vertex AI embedding provider test successful")
            return True
        except Exception as e:
            logger.error(f"Vertex AI embedding provider test failed: {e}")
            return False

    def get_provider_info(self) -> dict[str, Any]:
        return {
            "provider": "vertexai",
            "model": self.model,
            "dimensions": self.dimensions,
            "is_configured": bool(self._model),
            "capabilities": ["semantic", "enterprise_grade", "scalable"],
            "infrastructure": "google_cloud",
            "advantages": ["high_reliability", "scalable", "enterprise_support"]
        }


# Utility classes for rate limiting and retries

class RateLimitHandler:
    """Generic rate limit handler for embedding providers"""

    def __init__(self, requests_per_minute: int, burst_capacity: int = 5):
        self.requests_per_minute = requests_per_minute
        self.burst_capacity = burst_capacity
        self.request_times = []
        self._lock = None  # In production, use threading.Lock()

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()
        minute_ago = now - 60

        # Remove old requests
        self.request_times = [t for t in self.request_times if t > minute_ago]

        if len(self.request_times) >= self.requests_per_minute:
            # Calculate sleep time
            oldest_request = min(self.request_times)
            sleep_time = 60 - (now - oldest_request)

            if sleep_time > 0:
                logger.warning(f"Rate limit approaching, sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)

        self.request_times.append(now)


class RetryHandler:
    """Handles retry logic with exponential backoff"""

    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def execute_with_retry(self, func):
        """Execute function with retry logic"""
        for attempt in range(self.max_retries + 1):
            try:
                return func()
            except Exception as e:
                if attempt == self.max_retries:
                    raise

                wait_time = self.backoff_factor ** attempt
                logger.warning(
                    f"Embedding attempt {attempt + 1} failed, retrying in {wait_time}s: {e}"
                )
                time.sleep(wait_time)
