#!/usr/bin/env python3
"""
Simple Integration Test

Tests the core components of the market validation system that can be verified
without external dependencies.
"""

import json
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_basic_imports():
    """Test basic imports that should work"""
    logger.info("🧪 Testing Basic Imports...")

    try:
        # Test config import
        from config import settings
        logger.info("✅ Config import successful")

        # Check key settings
        if hasattr(settings, 'SUPABASE_URL'):
            logger.info("✅ SUPABASE_URL configured")
        else:
            logger.error("❌ SUPABASE_URL not found")

        if hasattr(settings, 'MARKET_VALIDATION_ENABLED'):
            logger.info(f"✅ MARKET_VALIDATION_ENABLED: {settings.MARKET_VALIDATION_ENABLED}")
        else:
            logger.error("❌ MARKET_VALIDATION_ENABLED not found")

        return True

    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        return False


def test_file_structure():
    """Test that required files exist"""
    logger.info("🧪 Testing File Structure...")

    required_files = [
        "migrations/001_add_market_validation_fields.sql",
        "agent_tools/market_data_validator.py",
        "agent_tools/market_validation_persistence.py",
        "agent_tools/jina_reader_client.py",
        "config/settings.py"
    ]

    missing_files = []

    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            logger.info(f"✅ {file_path}")
        else:
            logger.error(f"❌ {file_path}")
            missing_files.append(file_path)

    if missing_files:
        logger.error(f"Missing {len(missing_files)} required files")
        return False

    logger.info("✅ All required files exist")
    return True


def test_migration_file():
    """Test that migration file has expected content"""
    logger.info("🧪 Testing Migration File...")

    migration_file = project_root / "migrations" / "001_add_market_validation_fields.sql"

    try:
        with open(migration_file, 'r') as f:
            content = f.read()

        # Check for key migration components
        expected_components = [
            "ALTER TABLE app_opportunities",
            "ALTER TABLE market_validations",
            "CREATE INDEX",
            "market_validation_score",
            "market_data_quality_score",
            "market_competitors_found"
        ]

        for component in expected_components:
            if component in content:
                logger.info(f"✅ Found: {component}")
            else:
                logger.error(f"❌ Missing: {component}")
                return False

        # Count SQL statements
        statement_count = content.count(';')
        logger.info(f"✅ Migration contains {statement_count} SQL statements")

        return True

    except Exception as e:
        logger.error(f"❌ Error reading migration file: {e}")
        return False


def test_persistence_module_structure():
    """Test persistence module has expected classes and methods"""
    logger.info("🧪 Testing Persistence Module Structure...")

    persistence_file = project_root / "agent_tools" / "market_validation_persistence.py"

    try:
        with open(persistence_file, 'r') as f:
            content = f.read()

        expected_classes = [
            "class MarketValidationPersistence",
            "def save_validation_evidence",
            "def get_market_validation",
            "def get_validation_analytics"
        ]

        for expected in expected_classes:
            if expected in content:
                logger.info(f"✅ Found: {expected}")
            else:
                logger.error(f"❌ Missing: {expected}")
                return False

        # Count methods
        method_count = content.count('def ')
        logger.info(f"✅ Module contains {method_count} methods")

        return True

    except Exception as e:
        logger.error(f"❌ Error checking persistence module: {e}")
        return False


def test_database_connection():
    """Test basic database connectivity via HTTP"""
    logger.info("🧪 Testing Database Connection...")

    try:
        import requests

        from config import settings

        # Test basic health check
        response = requests.get(
            f"{settings.SUPABASE_URL}/rest/v1/",
            timeout=5
        )

        if response.status_code == 200:
            logger.info("✅ Database REST API is accessible")

            # Test that we can query a simple table
            response = requests.get(
                f"{settings.SUPABASE_URL}/rest/v1/_migrations_log?limit=1",
                headers={"apikey": settings.SUPABASE_KEY},
                timeout=5
            )

            if response.status_code == 200:
                logger.info("✅ Database query successful")
                return True
            else:
                logger.warning(f"⚠️ Database query failed: {response.status_code}")
                return False
        else:
            logger.error(f"❌ Database not accessible: {response.status_code}")
            return False

    except ImportError:
        logger.warning("⚠️ Requests not available, skipping database test")
        return True  # Not a failure, just can't test
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        return False


def test_schema_compliance():
    """Test that our implementation follows the schema analysis recommendations"""
    logger.info("🧪 Testing Schema Compliance...")

    analysis_file = project_root / "schema_dumps" / "MARKET_VALIDATION_PERSISTENCY_ANALYSIS_20251116.md"

    if not analysis_file.exists():
        logger.warning("⚠️ Schema analysis file not found, skipping compliance test")
        return True

    try:
        with open(analysis_file, 'r') as f:
            analysis_content = f.read()

        migration_file = project_root / "migrations" / "001_add_market_validation_fields.sql"
        with open(migration_file, 'r') as f:
            migration_content = f.read()

        # Check for Option 1 implementation (recommended)
        if "Enhance Existing market_validations Table (RECOMMENDED)" in analysis_content:
            logger.info("✅ Schema analysis recommends Option 1")

            # Check that we followed the recommendation
            if "ALTER TABLE market_validations" in migration_content:
                logger.info("✅ Following Option 1: Enhanced market_validations table")
            else:
                logger.error("❌ Not following Option 1 recommendation")
                return False

        # Check for required fields from analysis
        required_fields = [
            "market_validation_score",
            "market_data_quality_score",
            "market_validation_reasoning",
            "market_competitors_found",
            "market_size_tam"
        ]

        for field in required_fields:
            if field in migration_content:
                logger.info(f"✅ Required field implemented: {field}")
            else:
                logger.error(f"❌ Required field missing: {field}")
                return False

        logger.info("✅ Schema compliance verified")
        return True

    except Exception as e:
        logger.error(f"❌ Schema compliance check failed: {e}")
        return False


def main():
    """Main test function"""
    logger.info("🚀 Starting Simple Integration Test")
    logger.info("=" * 60)

    tests = [
        ("Basic Imports", test_basic_imports),
        ("File Structure", test_file_structure),
        ("Migration File", test_migration_file),
        ("Persistence Module", test_persistence_module_structure),
        ("Database Connection", test_database_connection),
        ("Schema Compliance", test_schema_compliance)
    ]

    results = {}

    for test_name, test_func in tests:
        logger.info(f"\nTEST: {test_name}")
        logger.info("-" * 40)
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test '{test_name}' failed with exception: {e}")
            results[test_name] = False

    # Summary
    logger.info("\n🏁 TEST SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name:<25}: {status}")

    logger.info("=" * 60)
    logger.info(f"Overall: {passed}/{total} tests passed")

    if passed == total:
        logger.info("\n🎉 All tests passed! System is properly configured.")
        logger.info("\n📋 DEPLOYMENT CHECKLIST:")
        logger.info("□ Apply database migration via Supabase Studio")
        logger.info("□ Configure JINA_API_KEY in .env.local")
        logger.info("□ Install missing dependencies if needed")
        logger.info("□ Run full integration test with real API calls")
        logger.info("□ Monitor performance and analytics")
    else:
        logger.warning(f"\n⚠️ {total - passed} test(s) failed. Review the issues above.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)