"""
Simple validation script for DLT Supabase configuration tests.

This script validates that the test files can be imported and basic functionality
works without requiring the full pytest framework.
"""

import sys
import tempfile
from pathlib import Path

# Try to import toml, but handle missing dependency gracefully
try:
    import toml
    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False
    print("⚠️  toml module not available, some validations will be skipped")

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def validate_test_imports():
    """Test that test files can be imported without errors"""
    print("🧪 Validating DLT test imports...")

    try:
        # Try to import the test modules
        import test_dlt_configuration
        import test_dlt_supabase_connection

        # Check if toml is available in the test modules
        config_has_toml = hasattr(test_dlt_configuration, 'TOML_AVAILABLE') and test_dlt_configuration.TOML_AVAILABLE

        print(f"✅ All test modules imported successfully (toml available: {config_has_toml})")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def validate_toml_parsing():
    """Test TOML parsing functionality used in tests"""
    if not TOML_AVAILABLE:
        print("⚠️  TOML parsing skipped (toml module not available)")
        return True

    print("🧪 Validating TOML parsing...")

    try:
        # Test valid TOML content
        valid_toml = """
[destination.supabase]
credentials = "postgresql://user:pass@host:5432/db"

[destination.supabase.credentials]
database = "test_db"
username = "user"
password = "pass"
host = "localhost"
port = 5432
"""

        config = toml.loads(valid_toml)
        assert "destination" in config
        assert "supabase" in config["destination"]
        print("✅ TOML parsing works correctly")
        return True

    except Exception as e:
        print(f"❌ TOML parsing failed: {e}")
        return False


def validate_connection_string_validation():
    """Test PostgreSQL connection string validation logic"""
    print("🧪 Validating connection string validation...")

    def is_valid_postgres_connection_string(conn_str: str) -> bool:
        """Helper method to validate PostgreSQL connection string"""
        try:
            import re
            pattern = r'^(postgres(?:ql)?)://[^@]+@[^:]+:\d+/[^/]+$'
            return bool(re.match(pattern, conn_str))
        except ImportError:
            # Fallback validation without regex
            return (
                conn_str.startswith(('postgresql://', 'postgres://')) and
                '@' in conn_str
            )

    # Test valid connection strings
    valid_strings = [
        "postgresql://user:pass@host:5432/db",
        "postgres://user@localhost:5432/reddit_db",
    ]

    # Test invalid connection strings
    invalid_strings = [
        "not_a_connection_string",
        "mysql://user@host/db",
    ]

    try:
        for conn_str in valid_strings:
            if not is_valid_postgres_connection_string(conn_str):
                print(f"❌ Valid connection string rejected: {conn_str}")
                return False

        for conn_str in invalid_strings:
            if is_valid_postgres_connection_string(conn_str):
                print(f"❌ Invalid connection string accepted: {conn_str}")
                return False

        print("✅ Connection string validation works correctly")
        return True

    except Exception as e:
        print(f"❌ Connection string validation failed: {e}")
        return False


def validate_file_structure():
    """Test that required files exist and have correct structure"""
    print("🧪 Validating file structure...")

    required_files = [
        "test_dlt_configuration.py",
        "test_dlt_supabase_connection.py",
    ]

    try:
        for filename in required_files:
            file_path = Path(__file__).parent / filename
            if not file_path.exists():
                print(f"❌ Missing required file: {filename}")
                return False

            # Check file is not empty
            if file_path.stat().st_size == 0:
                print(f"❌ Empty file: {filename}")
                return False

        print("✅ All required files exist and are non-empty")
        return True

    except Exception as e:
        print(f"❌ File structure validation failed: {e}")
        return False


def validate_test_fixtures():
    """Test that test fixtures are properly defined"""
    print("🧪 Validating test fixtures...")

    try:
        # Import test modules to check fixtures
        from test_dlt_configuration import (
            valid_secrets_toml_content,
            invalid_secrets_toml_content,
            postgres_direct_secrets_toml,
            supabase_structured_secrets_toml,
            TOML_AVAILABLE
        )

        # Test that fixtures return valid content
        fixtures_to_test = [
            valid_secrets_toml_content(),
            postgres_direct_secrets_toml(),
            supabase_structured_secrets_toml()
        ]

        for fixture_content in fixtures_to_test:
            if not isinstance(fixture_content, str):
                print(f"❌ Fixture content is not a string")
                return False

            # Validate basic structure if TOML is available
            if TOML_AVAILABLE and toml:
                config = toml.loads(fixture_content)
                assert isinstance(config, dict)
                assert "destination" in config

        print("✅ Test fixtures are properly defined")
        return True

    except Exception as e:
        print(f"❌ Test fixture validation failed: {e}")
        return False


def main():
    """Run all validation checks"""
    print("🚀 DLT Supabase Configuration Test Validation")
    print("=" * 50)

    validations = [
        ("File Structure", validate_file_structure),
        ("TOML Parsing", validate_toml_parsing),
        ("Connection String Validation", validate_connection_string_validation),
        ("Test Imports", validate_test_imports),
        ("Test Fixtures", validate_test_fixtures),
    ]

    results = []
    for name, validation_func in validations:
        print(f"\n📋 {name}:")
        result = validation_func()
        results.append((name, result))

    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY:")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {name}")

    print(f"\n📈 Overall: {passed}/{total} validations passed")

    if passed == total:
        print("🎉 All validations passed! Tests are ready for implementation.")
        return 0
    else:
        print("⚠️  Some validations failed. Please review the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())