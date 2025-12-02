#!/usr/bin/env python3
"""
Simple DLT Test - Just check if we can import the module structure
"""

import sys
import logging
from pathlib import Path

# Add pipeline-v2 to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that we can import the DLT module structure"""
    logger.info("Testing DLT module import structure...")

    try:
        # Test basic import
        from storage import dlt_loader
        logger.info("✓ storage.dlt_loader imported successfully")

        # Test specific classes
        from storage.dlt_loader import DLTLoader
        logger.info("✓ DLTLoader class imported successfully")

        # Test factory function
        from storage.dlt_loader import create_dlt_loader
        logger.info("✓ create_dlt_loader function imported successfully")

        return True

    except ImportError as e:
        logger.error(f"✗ Import failed: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        return False

def test_dlt_availability():
    """Test if DLT library is available"""
    logger.info("Testing DLT library availability...")

    try:
        import dlt
        version = getattr(dlt, '__version__', 'unknown')
        logger.info(f"✓ DLT library available (version: {version})")
        return True
    except ImportError as e:
        logger.error(f"✗ DLT library not available: {e}")
        logger.info("  DLT 1.18.2 should be installed for this test")
        return False

def main():
    """Main test function"""
    logger.info("=" * 50)
    logger.info("Simple DLT Module Test")
    logger.info("=" * 50)

    # Test 1: Import structure
    import_ok = test_imports()

    # Test 2: DLT availability
    dlt_ok = test_dlt_availability()

    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("TEST SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Module Import: {'✅ PASS' if import_ok else '❌ FAIL'}")
    logger.info(f"DLT Library: {'✅ PASS' if dlt_ok else '❌ FAIL'}")

    if import_ok and dlt_ok:
        logger.info("\n🎉 Both tests passed! DLT infrastructure is ready.")
        return True
    else:
        logger.info("\n⚠️  Some tests failed. Check the errors above.")
        if not dlt_ok:
            logger.info("💡 To install DLT: pip install 'dlt[postgres]'")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)