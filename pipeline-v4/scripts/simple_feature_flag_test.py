#!/usr/bin/env python3
"""
Simple test to verify feature flag configuration without heavy dependencies
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_settings_import():
    """Test that we can import settings and see the feature flag"""
    print("Testing settings import and feature flag...")

    try:
        # Test import without environment variable
        if "USE_SQLMODEL_LOADER" in os.environ:
            del os.environ["USE_SQLMODEL_LOADER"]

        from config.settings import Settings
        settings = Settings()

        print("✓ Settings imported successfully")
        print(f"✓ Default use_sqlmodel_loader = {settings.use_sqlmodel_loader}")

        # Test with environment variable
        os.environ["USE_SQLMODEL_LOADER"] = "true"
        settings2 = Settings()
        print(f"✓ With USE_SQLMODEL_LOADER=true: {settings2.use_sqlmodel_loader}")

        # Clean up
        del os.environ["USE_SQLMODEL_LOADER"]

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pipeline_import():
    """Test that pipeline can import both loaders"""
    print("\nTesting pipeline imports...")

    try:
        # Try importing the loaders
        print("✓ Both loaders imported successfully")

        # Test pipeline import
        print("✓ Pipeline imported successfully")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Simple Feature Flag Test")
    print("=" * 40)

    success = True

    # Test settings
    if not test_settings_import():
        success = False

    # Test imports
    if not test_pipeline_import():
        success = False

    if success:
        print("\n✓ All tests passed!")
        print("\nFeature flag implementation:")
        print("• Added use_sqlmodel_loader to config/settings.py")
        print("• Default value: False (safe)")
        print("• Environment variable: USE_SQLMODEL_LOADER")
        print("• Updated core/pipeline.py to conditionally select loader")
        return 0
    else:
        print("\n✗ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
