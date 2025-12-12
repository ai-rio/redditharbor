"""
Tests for the Loader Factory Pattern implementation.

Tests ensure proper factory behavior, dependency injection, and error handling.
"""

from unittest.mock import patch

import pytest

from config.settings import Settings
from load.base import BaseLoader
from load.loader import OpportunityLoader
from load.loader_factory import get_loader
from models.analysis import Opportunity


class MockLoader(BaseLoader):
    """Mock loader for testing dependency injection"""

    def __init__(self, settings=None):
        self.settings = settings
        self.saved_opportunities = []

    def save_opportunity(self, opportunity: Opportunity) -> bool:
        self.saved_opportunities.append(opportunity)
        return True

    def save_analysis(self, analysis) -> bool:
        return True

    def close(self):
        pass


class TestBaseLoader:
    """Test the abstract base loader interface"""

    def test_base_loader_is_abstract(self):
        """Test that BaseLoader cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BaseLoader()


class TestLoaderFactory:
    """Test the loader factory functionality"""

    def test_get_loader_returns_opportunity_loader(self):
        """Test factory returns OpportunityLoader"""
        settings = Settings()
        loader = get_loader(settings)

        assert isinstance(loader, OpportunityLoader)
        assert loader.settings == settings

    def test_get_loader_uses_dependency_injection(self):
        """Test factory returns injected loader instance"""
        mock_loader = MockLoader()
        loader = get_loader(loader_override=mock_loader)

        assert loader is mock_loader
        assert isinstance(loader, MockLoader)

    def test_get_loader_uses_global_settings_when_none_provided(self):
        """Test factory uses global settings when none provided"""
        with patch('load.loader_factory.get_settings') as mock_get_settings:
            mock_settings = Settings()
            mock_get_settings.return_value = mock_settings

            loader = get_loader()

            mock_get_settings.assert_called_once()
            assert isinstance(loader, OpportunityLoader)

    @patch('load.loader.OpportunityLoader')
    def test_get_loader_handles_import_error(self, mock_loader_class):
        """Test factory handles import errors gracefully"""
        mock_loader_class.side_effect = ImportError("No module named 'sqlmodel'")

        with pytest.raises(RuntimeError, match="Loader module import failed"):
            get_loader(Settings())

    @patch('load.loader.OpportunityLoader')
    def test_get_loader_handles_initialization_error(self, mock_loader_class):
        """Test factory handles initialization errors gracefully"""
        mock_loader_class.side_effect = Exception("Database connection failed")

        with pytest.raises(RuntimeError, match="Loader initialization failed"):
            get_loader(Settings())


class TestFactoryIntegration:
    """Integration tests for factory pattern with OpportunityLoader"""

    def test_loader_implements_base_interface(self):
        """Test that OpportunityLoader properly implements BaseLoader interface"""
        loader = OpportunityLoader()
        assert isinstance(loader, BaseLoader)
        assert hasattr(loader, 'save_opportunity')
        assert hasattr(loader, 'save_analysis')
        assert hasattr(loader, 'close')

    def test_factory_creates_opportunity_loader(self):
        """Test factory creates OpportunityLoader instance"""
        settings = Settings()
        loader = get_loader(settings)
        assert isinstance(loader, OpportunityLoader)

    def test_factory_with_settings_uses_global_when_none(self):
        """Test factory behavior with different settings scenarios"""
        # Test with explicit settings
        explicit_settings = Settings()
        loader1 = get_loader(explicit_settings)
        assert isinstance(loader1, OpportunityLoader)

        # Test without settings (should use global)
        with patch('load.loader_factory.get_settings') as mock_get_settings:
            global_settings = Settings()
            mock_get_settings.return_value = global_settings

            loader2 = get_loader()
            assert isinstance(loader2, OpportunityLoader)
            mock_get_settings.assert_called_once()


if __name__ == "__main__":
    # Run basic smoke tests
    print("Running basic loader factory tests...")

    # Test that loader can be created
    loader = get_loader(Settings())
    print(f"✓ Created OpportunityLoader: {type(loader).__name__}")

    # Test dependency injection
    mock_loader = MockLoader()
    injected_loader = get_loader(loader_override=mock_loader)
    print(f"✓ Dependency injection works: {type(injected_loader).__name__}")

    print("\nAll basic tests passed!")
