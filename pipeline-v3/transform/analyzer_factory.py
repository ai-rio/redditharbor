"""
Factory pattern for analyzer creation with dependency injection and configuration management
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

from config import get_settings
from .analyzer import SimpleOpportunityAnalyzer, OpportunityAnalyzer
from .embedding_strategies import EmbeddingStrategy, FakeEmbeddingProvider, OpenAIEmbeddingProvider

logger = logging.getLogger(__name__)


class AnalyzerFactory(ABC):
    """Abstract base class for analyzer factories"""

    @abstractmethod
    def create_analyzer(self, config: Optional[Dict[str, Any]] = None):
        """Create an analyzer instance based on configuration"""
        pass


class TestModeAnalyzerFactory(AnalyzerFactory):
    """Factory for creating test mode analyzers with fake embeddings"""

    def __init__(self, embedding_dimensions: int = 384, value_range: tuple[float, float] = (-1.0, 1.0)):
        """
        Initialize test mode factory

        Args:
            embedding_dimensions: Dimensions for fake embedding vectors
            value_range: Min/max range for embedding values
        """
        self.embedding_dimensions = embedding_dimensions
        self.value_range = value_range

    def create_analyzer(self, config: Optional[Dict[str, Any]] = None) -> SimpleOpportunityAnalyzer:
        """
        Create a test mode analyzer with fake embeddings

        Args:
            config: Optional configuration overrides

        Returns:
            Configured SimpleOpportunityAnalyzer instance
        """
        # Override config with factory defaults
        if config is None:
            config = {}

        dimensions = config.get('embedding_dimensions', self.embedding_dimensions)
        value_range = config.get('value_range', self.value_range)

        # Create fake embedding provider
        fake_provider = FakeEmbeddingProvider(
            dimensions=dimensions,
            value_range=value_range
        )

        # Create embedding strategy
        embedding_strategy = EmbeddingStrategy(fake_provider)

        # Create analyzer with strategy
        analyzer = SimpleOpportunityAnalyzer(embedding_strategy)

        logger.info(f"Created test mode analyzer with {dimensions}-dimensional embeddings")
        return analyzer


class ProductionAnalyzerFactory(AnalyzerFactory):
    """Factory for creating production analyzers with real LLM and embedding services"""

    def __init__(self, settings=None):
        """
        Initialize production factory

        Args:
            settings: Application settings (will use get_settings() if None)
        """
        self.settings = settings or get_settings()

    def create_analyzer(self, config: Optional[Dict[str, Any]] = None) -> OpportunityAnalyzer:
        """
        Create a production analyzer with LLM and embedding services

        Args:
            config: Optional configuration overrides

        Returns:
            Configured OpportunityAnalyzer instance
        """
        # Override settings with config if provided
        if config:
            # Apply config overrides to settings
            for key, value in config.items():
                if hasattr(self.settings, key):
                    setattr(self.settings, key, value)

        try:
            # Create production analyzer
            analyzer = OpportunityAnalyzer()

            # Optionally enhance with OpenAI embeddings if configured
            if hasattr(self.settings, 'enable_openai_embeddings') and self.settings.enable_openai_embeddings:
                try:
                    openai_provider = OpenAIEmbeddingProvider(
                        model=getattr(self.settings, 'openai_embedding_model', 'text-embedding-3-small'),
                        dimensions=getattr(self.settings, 'openai_embedding_dimensions', 1536)
                    )

                    # Create fallback fake provider
                    fake_provider = FakeEmbeddingProvider()
                    embedding_strategy = EmbeddingStrategy(openai_provider, fake_provider)

                    # Replace analyzer's embedding strategy (need to modify analyzer)
                    analyzer.embedding_strategy = embedding_strategy

                    logger.info("Created production analyzer with OpenAI embeddings + fake fallback")

                except Exception as e:
                    logger.warning(f"Failed to initialize OpenAI embeddings, using fake only: {e}")
            else:
                logger.info("Created production analyzer with LLM only")

            return analyzer

        except Exception as e:
            logger.error(f"Failed to create production analyzer: {e}")
            raise RuntimeError(f"Production analyzer creation failed: {e}")


class HybridAnalyzerFactory(AnalyzerFactory):
    """Factory for creating hybrid analyzers with configurable providers"""

    def __init__(self, settings=None):
        """
        Initialize hybrid factory

        Args:
            settings: Application settings
        """
        self.settings = settings or get_settings()

    def create_analyzer(self, config: Optional[Dict[str, Any]] = None) -> SimpleOpportunityAnalyzer:
        """
        Create a hybrid analyzer with configurable embedding strategy

        Args:
            config: Configuration specifying providers and settings

        Returns:
            Configured analyzer instance
        """
        config = config or {}

        # Determine embedding provider from config
        embedding_config = config.get('embedding', {})
        provider_type = embedding_config.get('provider', 'fake')

        if provider_type == 'openai':
            try:
                primary_provider = OpenAIEmbeddingProvider(
                    model=embedding_config.get('model', 'text-embedding-3-small'),
                    dimensions=embedding_config.get('dimensions', 1536)
                )
            except Exception as e:
                logger.warning(f"OpenAI provider failed, falling back to fake: {e}")
                primary_provider = FakeEmbeddingProvider(
                    dimensions=embedding_config.get('dimensions', 384)
                )
        else:
            # Default to fake provider
            primary_provider = FakeEmbeddingProvider(
                dimensions=embedding_config.get('dimensions', 384),
                value_range=embedding_config.get('value_range', (-1.0, 1.0))
            )

        # Create fallback provider if specified
        fallback_config = embedding_config.get('fallback', {})
        if fallback_config.get('enabled', False):
            fallback_provider = FakeEmbeddingProvider(
                dimensions=fallback_config.get('dimensions', 384)
            )
        else:
            fallback_provider = None

        # Create embedding strategy
        embedding_strategy = EmbeddingStrategy(primary_provider, fallback_provider)

        # Create analyzer
        analyzer = SimpleOpportunityAnalyzer(embedding_strategy)

        logger.info(f"Created hybrid analyzer with {provider_type} primary provider")
        return analyzer


class AnalyzerFactoryProvider:
    """
    Provider for analyzer factories with environment-based factory selection
    """

    def __init__(self, settings=None):
        """
        Initialize factory provider

        Args:
            settings: Application settings
        """
        self.settings = settings or get_settings()
        self._factories = {
            'test': TestModeAnalyzerFactory(),
            'production': ProductionAnalyzerFactory(self.settings),
            'hybrid': HybridAnalyzerFactory(self.settings)
        }

    def get_factory(self, factory_type: str = None) -> AnalyzerFactory:
        """
        Get analyzer factory based on type or auto-detect from settings

        Args:
            factory_type: Type of factory ('test', 'production', 'hybrid', or None for auto-detect)

        Returns:
            AnalyzerFactory instance
        """
        if factory_type is None:
            # Auto-detect from settings
            factory_type = 'production' if not getattr(self.settings, 'test_mode', False) else 'test'

        if factory_type not in self._factories:
            raise ValueError(f"Unknown factory type: {factory_type}. Available: {list(self._factories.keys())}")

        factory = self._factories[factory_type]
        logger.info(f"Selected {factory_type} analyzer factory")
        return factory

    def create_analyzer(self, factory_type: str = None, config: Optional[Dict[str, Any]] = None):
        """
        Create analyzer using factory of specified type

        Args:
            factory_type: Type of factory to use
            config: Configuration for the analyzer

        Returns:
            Analyzer instance
        """
        factory = self.get_factory(factory_type)
        return factory.create_analyzer(config)

    def register_factory(self, factory_type: str, factory: AnalyzerFactory):
        """
        Register a custom factory

        Args:
            factory_type: Type identifier for the factory
            factory: AnalyzerFactory instance
        """
        self._factories[factory_type] = factory
        logger.info(f"Registered custom factory: {factory_type}")

    def list_available_factories(self) -> list[str]:
        """Get list of available factory types"""
        return list(self._factories.keys())


# Global factory provider instance
_analyzer_factory_provider = None


def get_analyzer_factory_provider(settings=None) -> AnalyzerFactoryProvider:
    """
    Get the global analyzer factory provider instance

    Args:
        settings: Application settings (only used on first call)

    Returns:
        AnalyzerFactoryProvider instance
    """
    global _analyzer_factory_provider
    if _analyzer_factory_provider is None:
        _analyzer_factory_provider = AnalyzerFactoryProvider(settings)
    return _analyzer_factory_provider


def create_analyzer(factory_type: str = None, config: Optional[Dict[str, Any]] = None, settings=None):
    """
    Convenience function to create an analyzer

    Args:
        factory_type: Type of factory to use
        config: Configuration for the analyzer
        settings: Application settings

    Returns:
        Analyzer instance
    """
    provider = get_analyzer_factory_provider(settings)
    return provider.create_analyzer(factory_type, config)