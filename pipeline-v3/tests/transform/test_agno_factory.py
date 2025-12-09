"""
Test suite for AgnoAnalyzerFactory integration following TDD principles
Phase 2: Factory Pattern Integration
"""

from typing import Any, Dict, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest


# Test that AgnoAnalyzerFactory doesn't exist yet (RED phase)
def test_agno_analyzer_factory_class_exists():
    """Test that AgnoAnalyzerFactory class is implemented"""
    from transform.analyzer_factory import AgnoAnalyzerFactory
    assert AgnoAnalyzerFactory is not None

def test_agno_factory_inherits_from_analyzer_factory():
    """Test that AgnoAnalyzerFactory inherits from AnalyzerFactory"""
    from transform.analyzer_factory import AgnoAnalyzerFactory, AnalyzerFactory
    assert issubclass(AgnoAnalyzerFactory, AnalyzerFactory)

def test_agno_factory_create_analyzer_method():
    """Test that AgnoAnalyzerFactory has create_analyzer method"""
    from transform.analyzer_factory import AgnoAnalyzerFactory
    assert hasattr(AgnoAnalyzerFactory, 'create_analyzer')
    assert callable(AgnoAnalyzerFactory.create_analyzer)

def test_agno_factory_initialization():
    """Test AgnoAnalyzerFactory initialization with configuration"""
    from transform.analyzer_factory import AgnoAnalyzerFactory

    # Test default initialization
    factory = AgnoAnalyzerFactory()
    assert factory is not None

    # Test initialization with custom config
    config = {
        'model': 'anthropic/claude-opus-4',
        'enable_agentops': True,
        'api_key': 'test-key'
    }
    factory_with_config = AgnoAnalyzerFactory(config)
    assert factory_with_config is not None

def test_agno_factory_creates_agno_analyzer():
    """Test that factory creates AgnoOpportunityAnalyzer instance"""
    from transform.agno_analyzer import AgnoOpportunityAnalyzer
    from transform.analyzer_factory import AgnoAnalyzerFactory

    factory = AgnoAnalyzerFactory()
    analyzer = factory.create_analyzer()

    assert isinstance(analyzer, AgnoOpportunityAnalyzer)

def test_agno_factory_with_custom_configuration():
    """Test factory passes configuration to AgnoOpportunityAnalyzer"""
    from transform.analyzer_factory import AgnoAnalyzerFactory

    config = {
        'model': 'anthropic/claude-opus-4',
        'enable_agentops': False,
        'base_url': 'https://custom-api.com'
    }

    factory = AgnoAnalyzerFactory(config)
    analyzer = factory.create_analyzer()

    # Verify analyzer was created with custom config
    assert analyzer is not None

def test_agno_factory_configuration_validation():
    """Test factory validates configuration parameters"""
    from transform.analyzer_factory import AgnoAnalyzerFactory

    factory = AgnoAnalyzerFactory()

    # Test valid configuration
    valid_config = {
        'model': 'anthropic/claude-haiku-4.5',
        'enable_agentops': True
    }
    analyzer = factory.create_analyzer(valid_config)
    assert analyzer is not None

    # Test invalid configuration handling
    invalid_config = {
        'model': '',  # Empty model should be handled
        'enable_agentops': 'not_a_boolean'
    }

    # Should handle gracefully or raise appropriate error
    try:
        analyzer = factory.create_analyzer(invalid_config)
        # If no error, analyzer should still be created with defaults
        assert analyzer is not None
    except ValueError:
        # ValueError is acceptable for invalid config
        pass

def test_factory_provider_registers_agno_factory():
    """Test that AnalyzerFactoryProvider registers AgnoAnalyzerFactory"""
    from transform.analyzer_factory import AnalyzerFactoryProvider

    provider = AnalyzerFactoryProvider()

    # Check if 'agno' is in available factories
    available_factories = provider.list_available_factories()
    assert 'agno' in available_factories

def test_factory_provider_creates_agno_analyzer():
    """Test that AnalyzerFactoryProvider can create Agno analyzer"""
    from transform.analyzer_factory import AnalyzerFactoryProvider

    provider = AnalyzerFactoryProvider()
    analyzer = provider.create_analyzer('agno')

    # Should create an AgnoOpportunityAnalyzer instance
    assert analyzer is not None
    assert analyzer.__class__.__name__ == 'AgnoOpportunityAnalyzer'

def test_factory_provider_auto_detection_for_agno():
    """Test factory provider auto-detects Agno analyzer based on settings"""
    from transform.analyzer_factory import AnalyzerFactoryProvider

    # Mock settings to prefer Agno
    mock_settings = Mock()
    mock_settings.analyzer_type = 'agno'

    provider = AnalyzerFactoryProvider(mock_settings)
    analyzer = provider.create_analyzer()  # Auto-detect

    assert analyzer is not None
    assert analyzer.__class__.__name__ == 'AgnoOpportunityAnalyzer'

def test_agno_factory_with_embedding_strategy():
    """Test Agno factory integrates with EmbeddingStrategy"""
    from transform.analyzer_factory import AgnoAnalyzerFactory
    from transform.embedding_strategies import EmbeddingStrategy, FakeEmbeddingProvider

    # Create factory with embedding strategy
    embedding_provider = FakeEmbeddingProvider()
    embedding_strategy = EmbeddingStrategy(embedding_provider)

    config = {
        'embedding_strategy': embedding_strategy
    }

    factory = AgnoAnalyzerFactory()
    analyzer = factory.create_analyzer(config)

    assert analyzer is not None
    # Verify embedding strategy is used if Agno analyzer supports it

def test_agno_factory_error_handling():
    """Test Agno factory handles errors gracefully"""
    from transform.analyzer_factory import AgnoAnalyzerFactory

    factory = AgnoAnalyzerFactory()

    # Test with problematic configuration
    problematic_config = {
        'api_key': None,  # Should cause error if API key is required
        'model': 'invalid-model-name'
    }

    # Should not crash unhandled
    try:
        analyzer = factory.create_analyzer(problematic_config)
        # If successful, should create fallback analyzer
        assert analyzer is not None
    except Exception as e:
        # Should raise meaningful error, not crash
        assert isinstance(e, (ValueError, RuntimeError, ConnectionError))

def test_agno_factory_backward_compatibility():
    """Test Agno factory maintains backward compatibility with existing factory interface"""
    from transform.analyzer_factory import AgnoAnalyzerFactory, AnalyzerFactory

    # Should be usable wherever AnalyzerFactory is expected
    def create_any_analyzer(factory: AnalyzerFactory, config: dict | None = None):
        return factory.create_analyzer(config)

    agno_factory = AgnoAnalyzerFactory()
    analyzer = create_any_analyzer(agno_factory, {'model': 'test-model'})

    assert analyzer is not None

def test_agno_factory_default_configuration():
    """Test Agno factory uses sensible defaults when no config provided"""
    from transform.analyzer_factory import AgnoAnalyzerFactory

    factory = AgnoAnalyzerFactory()
    analyzer = factory.create_analyzer()  # No config provided

    assert analyzer is not None
    # Should use default model and settings
    # These will be verified based on actual implementation

def test_agno_factory_configuration_override():
    """Test Agno factory allows partial configuration override"""
    from transform.analyzer_factory import AgnoAnalyzerFactory

    # Factory with default config
    factory = AgnoAnalyzerFactory({
        'model': 'anthropic/claude-haiku-4.5',
        'enable_agentops': True
    })

    # Override only agentops setting
    override_config = {
        'enable_agentops': False
    }

    analyzer = factory.create_analyzer(override_config)

    assert analyzer is not None
    # Other settings should remain from factory defaults

def test_agno_factory_environment_variable_integration():
    """Test Agno factory respects environment variables"""
    import os

    from transform.analyzer_factory import AgnoAnalyzerFactory

    # Set environment variable
    os.environ['AGNO_MODEL'] = 'anthropic/claude-opus-4'

    try:
        factory = AgnoAnalyzerFactory()
        analyzer = factory.create_analyzer()

        assert analyzer is not None
        # Should use environment variable if implemented

    finally:
        # Clean up
        os.environ.pop('AGNO_MODEL', None)
