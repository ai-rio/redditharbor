"""
Factory pattern for analyzer creation with dependency injection and configuration management
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
import os

# Configure logger
logger = logging.getLogger(__name__)

try:
    from config import get_settings
except ImportError:
    # Mock settings for TDD when get_settings is not available
    class MockSettings:
        def __init__(self):
            self.test_mode = False
            self.enable_openai_embeddings = False
            self.openai_embedding_model = 'text-embedding-3-small'
            self.openai_embedding_dimensions = 1536
            self.agno_model = None
            self.agno_base_url = None
            self.agno_enable_agentops = None

    def get_settings():
        return MockSettings()

# Conditional imports with fallbacks
try:
    from .analyzer import SimpleOpportunityAnalyzer, OpportunityAnalyzer
except ImportError:
    # Mock analyzers for TDD
    class SimpleOpportunityAnalyzer:
        def __init__(self, embedding_strategy=None):
            self.embedding_strategy = embedding_strategy

    class OpportunityAnalyzer:
        pass

try:
    from .embedding_strategies import EmbeddingStrategy, FakeEmbeddingProvider, OpenAIEmbeddingProvider
except ImportError:
    # Mock embedding strategies for TDD
    class EmbeddingStrategy:
        def __init__(self, primary_provider=None, fallback_provider=None):
            self.primary_provider = primary_provider
            self.fallback_provider = fallback_provider

    class FakeEmbeddingProvider:
        def __init__(self, dimensions=384, value_range=(-1.0, 1.0)):
            self.dimensions = dimensions
            self.value_range = value_range

    class OpenAIEmbeddingProvider:
        def __init__(self, model='text-embedding-3-small', dimensions=1536):
            self.model = model
            self.dimensions = dimensions

# Conditional import for Agno analyzer to handle dependency issues
try:
    from .agno_analyzer import AgnoOpportunityAnalyzer
    AGNO_AVAILABLE = True
except ImportError as e:
    AGNO_AVAILABLE = False
    logger.warning(f"Agno analyzer not available: {e}")

    # Create a mock class for TDD and development when dependencies are missing
    class AgnoOpportunityAnalyzer:
        """
        Mock AgnoOpportunityAnalyzer for TDD and development when dependencies are missing

        This mock implementation allows the factory pattern to work even when the full
        Agno analyzer dependencies (SQLAlchemy, models, etc.) are not available.
        """

        def __init__(self, model: str = "anthropic/claude-haiku-4.5",
                     base_url: str = "https://openrouter.ai/api/v1",
                     enable_agentops: bool = False):
            """
            Initialize mock AgnoOpportunityAnalyzer

            Args:
                model: Model name for LLM agents
                base_url: Base URL for API endpoints
                enable_agentops: Whether to enable AgentOps tracking
            """
            self.model = model
            self.base_url = base_url
            self.enable_agentops = enable_agentops
            logger.info(f"Mock AgnoOpportunityAnalyzer created with model={model}")

        def analyze_submission(self, submission):
            """Mock analyze_submission method"""
            return {"mock_result": True, "model": self.model}

        def analyze_batch_with_costs(self, submissions):
            """Mock analyze_batch_with_costs method"""
            return [], {"mock_cost": 0.0}


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


class AgnoAnalyzerFactory(AnalyzerFactory):
    """
    Factory for creating Agno-based multi-agent analyzers

    This factory provides a clean interface for creating AgnoOpportunityAnalyzer
    instances with configurable settings. It supports:

    - Configuration precedence (runtime > factory > settings > environment > defaults)
    - Environment variable integration
    - Type validation and error handling
    - Mock fallback when dependencies are unavailable

    Environment Variables:
        AGNO_MODEL: Default model name (e.g., 'anthropic/claude-haiku-4.5')
        AGNO_BASE_URL: Default API base URL (e.g., 'https://openrouter.ai/api/v1')
        AGNO_ENABLE_AGENTOPS: Enable AgentOps tracking ('true'/'false')

    Configuration Example:
        factory = AgnoAnalyzerFactory({
            'model': 'anthropic/claude-opus-4',
            'enable_agentops': True
        })
        analyzer = factory.create_analyzer()
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Agno analyzer factory

        Args:
            config: Default configuration for Agno analyzers
        """
        self.default_config = config or {}
        self.settings = get_settings()

    def create_analyzer(self, config: Optional[Dict[str, Any]] = None) -> AgnoOpportunityAnalyzer:
        """
        Create an Agno-based multi-agent analyzer

        Args:
            config: Optional configuration overrides

        Returns:
            Configured AgnoOpportunityAnalyzer instance
        """
        # Merge configurations with precedence: runtime > factory defaults
        merged_config = self.default_config.copy()
        if config:
            merged_config.update(config)

        # Validate configuration before resolution (to catch type errors)
        self._validate_config_pre_resolution(merged_config)

        # Resolve configuration with precedence: runtime > factory > settings > environment > defaults
        resolved_config = self._resolve_configuration(merged_config)

        # Final validation of resolved configuration
        self._validate_config(resolved_config)

        # Create Agno analyzer
        analyzer = AgnoOpportunityAnalyzer(
            model=resolved_config['model'],
            base_url=resolved_config['base_url'],
            enable_agentops=resolved_config['enable_agentops']
        )

        logger.info(f"Created Agno analyzer with model={resolved_config['model']}, agentops={resolved_config['enable_agentops']}")
        return analyzer

    def _resolve_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve configuration with proper precedence order

        Args:
            config: Merged configuration dictionary

        Returns:
            Resolved configuration with all values determined
        """
        # Configuration precedence: runtime > factory defaults > settings > environment > defaults
        return {
            'model': self._resolve_config_value(
                config.get('model'),
                'agno_model',
                'AGNO_MODEL',
                'anthropic/claude-haiku-4.5'
            ),
            'base_url': self._resolve_config_value(
                config.get('base_url'),
                'agno_base_url',
                'AGNO_BASE_URL',
                'https://openrouter.ai/api/v1'
            ),
            'enable_agentops': self._resolve_boolean_config_value(
                config.get('enable_agentops'),
                'agno_enable_agentops',
                'AGNO_ENABLE_AGENTOPS',
                False
            )
        }

    def _resolve_config_value(self, config_value: Any, settings_attr: str, env_var: str, default: Any) -> Any:
        """
        Resolve a single configuration value with proper precedence

        Args:
            config_value: Value from runtime configuration
            settings_attr: Attribute name in settings
            env_var: Environment variable name
            default: Default value if all else fails

        Returns:
            Resolved configuration value
        """
        # Explicit None checks to avoid treating empty strings as falsy
        if config_value is not None:
            return config_value

        settings_value = getattr(self.settings, settings_attr, None)
        if settings_value is not None:
            return settings_value

        env_value = os.environ.get(env_var)
        if env_value is not None:
            return env_value

        return default

    def _resolve_boolean_config_value(self, config_value: Any, settings_attr: str, env_var: str, default: bool) -> bool:
        """
        Resolve a boolean configuration value with proper precedence and type conversion

        Args:
            config_value: Value from runtime configuration
            settings_attr: Attribute name in settings
            env_var: Environment variable name
            default: Default boolean value

        Returns:
            Resolved boolean configuration value
        """
        # Explicit None checks to avoid treating empty strings as falsy
        if config_value is not None:
            return bool(config_value)

        settings_value = getattr(self.settings, settings_attr, None)
        if settings_value is not None:
            return bool(settings_value)

        env_value = os.environ.get(env_var)
        if env_value is not None:
            return env_value.lower() == 'true'

        return default

    def _validate_config_pre_resolution(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration parameters before resolution (to catch type errors early)

        Args:
            config: Configuration dictionary to validate

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate model - empty string should be caught here
        model = config.get('model')
        if model == '':
            raise ValueError("Invalid model configuration: empty string. Model must be a non-empty string.")

        # Validate enable_agentops type
        enable_agentops = config.get('enable_agentops')
        if enable_agentops is not None and not isinstance(enable_agentops, bool):
            # Check if it's a string that can be converted to boolean
            if isinstance(enable_agentops, str):
                if enable_agentops.lower() not in ['true', 'false']:
                    raise ValueError(f"Invalid enable_agentops configuration: {enable_agentops}. Must be boolean or 'true'/'false'.")
            else:
                raise ValueError(f"Invalid enable_agentops configuration: {enable_agentops}. Must be boolean.")

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate resolved configuration parameters

        Args:
            config: Resolved configuration dictionary to validate

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate model
        model = config.get('model', '')
        if not model or not isinstance(model, str):
            raise ValueError(f"Invalid model configuration: {model}. Model must be a non-empty string.")

        # Validate enable_agentops is boolean (should be after resolution)
        enable_agentops = config.get('enable_agentops')
        if not isinstance(enable_agentops, bool):
            raise ValueError(f"Invalid enable_agentops configuration: {enable_agentops}. Must be boolean.")


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
            'hybrid': HybridAnalyzerFactory(self.settings),
            'agno': AgnoAnalyzerFactory()
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
            # Auto-detect from settings - check for analyzer_type first, then test_mode fallback
            factory_type = getattr(self.settings, 'analyzer_type', None)
            if factory_type is None:
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


def get_analyzer(analyzer_type: str = "agno", config: Optional[Dict[str, Any]] = None, settings=None):
    """
    Get an analyzer instance by type with Agno as default

    Args:
        analyzer_type: Type of analyzer ('test', 'production', 'hybrid', 'agno')
        config: Configuration for the analyzer
        settings: Application settings

    Returns:
        Analyzer instance
    """
    provider = get_analyzer_factory_provider(settings)
    return provider.create_analyzer(analyzer_type, config)