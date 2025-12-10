"""
Tests for the Loader Factory Pattern implementation.

Tests ensure proper factory behavior, loader selection, and error handling.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Optional

from load.loader_factory import (
    BaseLoader,
    get_loader,
    LoaderType,
    create_loader_by_type
)
from load.postgres_loader import PostgresLoader
from load.sqlmodel_loader import SQLModelLoader
from models.analysis import Opportunity
from config.settings import Settings


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

    def test_get_loader_returns_postgres_by_default(self):
        """Test factory returns PostgresLoader when use_sqlmodel_loader is False"""
        # Create settings with SQLModel disabled
        settings = Settings(use_sqlmodel_loader=False)

        # Get loader from factory
        loader = get_loader(settings)

        # Verify correct type
        assert isinstance(loader, PostgresLoader)
        assert loader.settings == settings

    def test_get_loader_returns_sqlmodel_when_enabled(self):
        """Test factory returns SQLModelLoader when use_sqlmodel_loader is True"""
        # Create settings with SQLModel enabled
        settings = Settings(use_sqlmodel_loader=True)

        # Get loader from factory
        loader = get_loader(settings)

        # Verify correct type
        assert isinstance(loader, SQLModelLoader)
        assert loader.settings == settings

    def test_get_loader_uses_dependency_injection(self):
        """Test factory returns injected loader instance"""
        # Create mock loader
        mock_loader = MockLoader()

        # Get loader with dependency injection
        loader = get_loader(loader_override=mock_loader)

        # Verify the mock loader is returned
        assert loader is mock_loader
        assert isinstance(loader, MockLoader)

    def test_get_loader_uses_global_settings_when_none_provided(self):
        """Test factory uses global settings when none provided"""
        # Mock the global settings
        with patch('load.loader_factory.get_settings') as mock_get_settings:
            mock_settings = Settings(use_sqlmodel_loader=False)
            mock_get_settings.return_value = mock_settings

            # Get loader without providing settings
            loader = get_loader()

            # Verify global settings were used
            mock_get_settings.assert_called_once()
            assert isinstance(loader, PostgresLoader)

    @patch('load.postgres_loader.PostgresLoader')
    def test_get_loader_handles_import_error(self, mock_postgres_class):
        """Test factory handles import errors gracefully"""
        # Make PostgresLoader raise ImportError
        mock_postgres_class.side_effect = ImportError("No module named 'psycopg2'")

        # Factory should raise RuntimeError
        with pytest.raises(RuntimeError, match="Loader module import failed"):
            get_loader(Settings(use_sqlmodel_loader=False))

    @patch('load.postgres_loader.PostgresLoader')
    def test_get_loader_handles_initialization_error(self, mock_postgres_class):
        """Test factory handles initialization errors gracefully"""
        # Make PostgresLoader raise exception during init
        mock_postgres_class.side_effect = Exception("Database connection failed")

        # Factory should raise RuntimeError
        with pytest.raises(RuntimeError, match="Loader initialization failed"):
            get_loader(Settings(use_sqlmodel_loader=False))


class TestLoaderType:
    """Test the LoaderType enumeration utility"""

    def test_all_types(self):
        """Test all_types returns expected values"""
        types = LoaderType.all_types()
        assert LoaderType.POSTGRES in types
        assert LoaderType.SQLMODEL in types
        assert len(types) == 2

    def test_is_valid_with_valid_types(self):
        """Test is_valid returns True for valid types"""
        assert LoaderType.is_valid(LoaderType.POSTGRES) is True
        assert LoaderType.is_valid(LoaderType.SQLMODEL) is True
        assert LoaderType.is_valid("postgres") is True
        assert LoaderType.is_valid("sqlmodel") is True

    def test_is_valid_with_invalid_types(self):
        """Test is_valid returns False for invalid types"""
        assert LoaderType.is_valid("invalid") is False
        assert LoaderType.is_valid("mongodb") is False
        assert LoaderType.is_valid("") is False
        assert LoaderType.is_valid(None) is False


class TestCreateLoaderByType:
    """Test the create_loader_by_type function"""

    def test_create_postgres_loader_by_type(self):
        """Test creating PostgresLoader by type string"""
        settings = Settings()

        loader = create_loader_by_type(LoaderType.POSTGRES, settings)

        assert isinstance(loader, PostgresLoader)
        assert loader.settings == settings

    def test_create_sqlmodel_loader_by_type(self):
        """Test creating SQLModelLoader by type string"""
        settings = Settings()

        loader = create_loader_by_type(LoaderType.SQLMODEL, settings)

        assert isinstance(loader, SQLModelLoader)
        assert loader.settings == settings

    def test_create_loader_by_type_invalid_type(self):
        """Test error handling for invalid loader type"""
        with pytest.raises(ValueError, match="Invalid loader type"):
            create_loader_by_type("invalid_type")

    def test_create_loader_by_type_uses_global_settings(self):
        """Test create_loader_by_type uses global settings when none provided"""
        with patch('load.loader_factory.get_settings') as mock_get_settings:
            mock_settings = Settings()
            mock_get_settings.return_value = mock_settings

            loader = create_loader_by_type(LoaderType.POSTGRES)

            mock_get_settings.assert_called_once()
            assert isinstance(loader, PostgresLoader)

    @patch('load.sqlmodel_loader.SQLModelLoader')
    def test_create_loader_by_type_handles_import_error(self, mock_sqlmodel_class):
        """Test create_loader_by_type handles import errors"""
        mock_sqlmodel_class.side_effect = ImportError("SQLModel not available")

        with pytest.raises(RuntimeError, match="Loader module import failed"):
            create_loader_by_type(LoaderType.SQLMODEL)


class TestFactoryIntegration:
    """Integration tests for factory pattern with actual loaders"""

    def test_both_loaders_implement_base_interface(self):
        """Test that both loaders properly implement BaseLoader interface"""
        # Test PostgresLoader
        postgres_loader = PostgresLoader()
        assert isinstance(postgres_loader, BaseLoader)
        assert hasattr(postgres_loader, 'save_opportunity')
        assert hasattr(postgres_loader, 'save_analysis')
        assert hasattr(postgres_loader, 'close')

        # Test SQLModelLoader
        sqlmodel_loader = SQLModelLoader()
        assert isinstance(sqlmodel_loader, BaseLoader)
        assert hasattr(sqlmodel_loader, 'save_opportunity')
        assert hasattr(sqlmodel_loader, 'save_analysis')
        assert hasattr(sqlmodel_loader, 'close')

    def test_factory_switches_loaders_based_on_setting(self):
        """Test factory correctly switches loaders based on settings"""
        # Test with Postgres
        postgres_settings = Settings(use_sqlmodel_loader=False)
        postgres_loader = get_loader(postgres_settings)
        assert isinstance(postgres_loader, PostgresLoader)
        assert not isinstance(postgres_loader, SQLModelLoader)

        # Test with SQLModel
        sqlmodel_settings = Settings(use_sqlmodel_loader=True)
        sqlmodel_loader = get_loader(sqlmodel_settings)
        assert isinstance(sqlmodel_loader, SQLModelLoader)
        assert not isinstance(sqlmodel_loader, PostgresLoader)

    def test_factory_with_settings_uses_global_when_none(self):
        """Test factory behavior with different settings scenarios"""
        # Test with explicit settings
        explicit_settings = Settings(use_sqlmodel_loader=True)
        loader1 = get_loader(explicit_settings)
        assert isinstance(loader1, SQLModelLoader)

        # Test without settings (should use global)
        with patch('load.loader_factory.get_settings') as mock_get_settings:
            global_settings = Settings(use_sqlmodel_loader=False)
            mock_get_settings.return_value = global_settings

            loader2 = get_loader()
            assert isinstance(loader2, PostgresLoader)
            mock_get_settings.assert_called_once()


if __name__ == "__main__":
    # Run basic smoke tests
    print("Running basic loader factory tests...")

    # Test that both loaders can be created
    postgres_loader = get_loader(Settings(use_sqlmodel_loader=False))
    print(f"✓ Created PostgresLoader: {type(postgres_loader).__name__}")

    sqlmodel_loader = get_loader(Settings(use_sqlmodel_loader=True))
    print(f"✓ Created SQLModelLoader: {type(sqlmodel_loader).__name__}")

    # Test dependency injection
    mock_loader = MockLoader()
    injected_loader = get_loader(loader_override=mock_loader)
    print(f"✓ Dependency injection works: {type(injected_loader).__name__}")

    # Test LoaderType utilities
    print(f"✓ Available loader types: {LoaderType.all_types()}")
    print(f"✓ 'postgres' is valid: {LoaderType.is_valid('postgres')}")
    print(f"✓ 'invalid' is valid: {LoaderType.is_valid('invalid')}")

    # Test create by type
    by_type_loader = create_loader_by_type(LoaderType.POSTGRES)
    print(f"✓ Created loader by type: {type(by_type_loader).__name__}")

    print("\nAll basic tests passed!")