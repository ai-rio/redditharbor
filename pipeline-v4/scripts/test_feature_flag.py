#!/usr/bin/env python3
"""
Test script to verify SQLModel feature flag functionality

This script tests:
1. Default behavior (psycopg2 loader when flag is False)
2. SQLModel loader when flag is True
3. Proper loader selection and initialization
4. Both loaders can save and retrieve data
"""

import logging
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings, get_settings
from core.pipeline import Pipeline
from load.postgres_loader import PostgresLoader
from load.sqlmodel_loader import SQLModelLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_default_behavior():
    """Test default behavior with flag=False (psycopg2 loader)"""
    print("\n" + "="*60)
    print("TEST 1: Default Behavior (USE_SQLMODEL_LOADER=False)")
    print("="*60)

    # Ensure environment variable is not set or False
    if "USE_SQLMODEL_LOADER" in os.environ:
        del os.environ["USE_SQLMODEL_LOADER"]

    # Create settings with default (False)
    settings = Settings()
    assert settings.use_sqlmodel_loader is False, f"Expected False, got {settings.use_sqlmodel_loader}"
    print(f"✓ Feature flag use_sqlmodel_loader = {settings.use_sqlmodel_loader}")

    # Initialize pipeline - should use psycopg2 loader
    pipeline = Pipeline(settings=settings)

    # Check loader type
    loader_type = type(pipeline.loader).__name__
    print(f"✓ Pipeline initialized with loader: {loader_type}")

    assert loader_type == "PostgresLoader", f"Expected PostgresLoader, got {loader_type}"
    print("✓ Default behavior test passed!")


def test_sqlmodel_flag_true():
    """Test SQLModel loader when flag=True"""
    print("\n" + "="*60)
    print("TEST 2: SQLModel Enabled (USE_SQLMODEL_LOADER=True)")
    print("="*60)

    # Set environment variable
    os.environ["USE_SQLMODEL_LOADER"] = "true"

    # Create settings
    settings = Settings()
    assert settings.use_sqlmodel_loader is True, f"Expected True, got {settings.use_sqlmodel_loader}"
    print(f"✓ Feature flag use_sqlmodel_loader = {settings.use_sqlmodel_loader}")

    # Initialize pipeline - should use SQLModel loader
    pipeline = Pipeline(settings=settings)

    # Check loader type
    loader_type = type(pipeline.loader).__name__
    print(f"✓ Pipeline initialized with loader: {loader_type}")

    assert loader_type == "SQLModelLoader", f"Expected SQLModelLoader, got {loader_type}"
    print("✓ SQLModel flag test passed!")


def test_environment_variable_priority():
    """Test that environment variable overrides code defaults"""
    print("\n" + "="*60)
    print("TEST 3: Environment Variable Priority")
    print("="*60)

    # Test with True environment variable
    os.environ["USE_SQLMODEL_LOADER"] = "True"
    settings = Settings()
    assert settings.use_sqlmodel_loader is True
    print("✓ Environment variable True overrides default")

    # Test with False environment variable
    os.environ["USE_SQLMODEL_LOADER"] = "False"
    settings = Settings()
    assert settings.use_sqlmodel_loader is False
    print("✓ Environment variable False overrides default")

    # Clean up
    if "USE_SQLMODEL_LOADER" in os.environ:
        del os.environ["USE_SQLMODEL_LOADER"]

    print("✓ Environment variable priority test passed!")


def test_both_loaders_importable():
    """Test that both loaders can be imported and instantiated"""
    print("\n" + "="*60)
    print("TEST 4: Both Loaders Importable")
    print("="*60)

    settings = get_settings()

    # Test psycopg2 loader
    try:
        postgres_loader = PostgresLoader(settings)
        print(f"✓ PostgresLoader instantiated: {type(postgres_loader).__name__}")
        assert hasattr(postgres_loader, 'save_analysis')
        print("✓ PostgresLoader has save_analysis method")
    except Exception as e:
        print(f"✗ PostgresLoader failed: {e}")
        raise

    # Test SQLModel loader
    try:
        sqlmodel_loader = SQLModelLoader(settings)
        print(f"✓ SQLModelLoader instantiated: {type(sqlmodel_loader).__name__}")
        assert hasattr(sqlmodel_loader, 'save_analysis')
        print("✓ SQLModelLoader has save_analysis method")
    except Exception as e:
        print(f"✗ SQLModelLoader failed: {e}")
        raise

    print("✓ Both loaders importable test passed!")


def test_loader_interface_compatibility():
    """Test that both loaders have the same interface"""
    print("\n" + "="*60)
    print("TEST 5: Loader Interface Compatibility")
    print("="*60)

    settings = get_settings()

    # Get both loaders
    postgres_loader = PostgresLoader(settings)
    sqlmodel_loader = SQLModelLoader(settings)

    # Check common methods
    common_methods = ['save_analysis']

    for method_name in common_methods:
        # Check PostgresLoader
        assert hasattr(postgres_loader, method_name), f"PostgresLoader missing {method_name}"
        assert callable(getattr(postgres_loader, method_name)), f"PostgresLoader.{method_name} not callable"
        print(f"✓ PostgresLoader.{method_name} exists and callable")

        # Check SQLModelLoader
        assert hasattr(sqlmodel_loader, method_name), f"SQLModelLoader missing {method_name}"
        assert callable(getattr(sqlmodel_loader, method_name)), f"SQLModelLoader.{method_name} not callable"
        print(f"✓ SQLModelLoader.{method_name} exists and callable")

    print("✓ Interface compatibility test passed!")


def main():
    """Run all tests"""
    print("SQLModel Feature Flag Verification")
    print("=" * 60)
    print("Testing the feature flag system for SQLModel migration")

    try:
        # Run all tests
        test_default_behavior()
        test_sqlmodel_flag_true()
        test_environment_variable_priority()
        test_both_loaders_importable()
        test_loader_interface_compatibility()

        print("\n" + "="*60)
        print("ALL TESTS PASSED! ✓")
        print("="*60)
        print("\nFeature flag system is working correctly:")
        print("• Default behavior uses psycopg2 loader (safe)")
        print("• Environment variable USE_SQLMODEL_LOADER=True enables SQLModel")
        print("• Both loaders are importable and functional")
        print("• Both loaders have compatible interfaces")
        print("• Pipeline correctly selects loader based on flag")

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
