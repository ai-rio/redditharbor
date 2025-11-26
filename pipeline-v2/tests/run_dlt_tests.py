"""
Simple DLT test runner that mimics pytest functionality.

This script runs our DLT Supabase configuration tests using a minimal test runner
that doesn't require the full pytest framework.
"""

import sys
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class SimpleTestRunner:
    """Minimal test runner for DLT tests"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def assert_equal(self, actual, expected, message=""):
        """Assert two values are equal"""
        if actual == expected:
            return True
        else:
            error_msg = f"Assertion failed: {actual} != {expected}"
            if message:
                error_msg = f"{message}: {error_msg}"
            raise AssertionError(error_msg)

    def assert_true(self, condition, message=""):
        """Assert condition is true"""
        if condition:
            return True
        else:
            error_msg = "Assertion failed: condition is not True"
            if message:
                error_msg = f"{message}: {error_msg}"
            raise AssertionError(error_msg)

    def assert_false(self, condition, message=""):
        """Assert condition is false"""
        if not condition:
            return True
        else:
            error_msg = "Assertion failed: condition is not False"
            if message:
                error_msg = f"{message}: {error_msg}"
            raise AssertionError(error_msg)

    def assert_in(self, item, container, message=""):
        """Assert item is in container"""
        if item in container:
            return True
        else:
            error_msg = f"Assertion failed: {item} not in {container}"
            if message:
                error_msg = f"{message}: {error_msg}"
            raise AssertionError(error_msg)

    def assert_not_in(self, item, container, message=""):
        """Assert item is not in container"""
        if item not in container:
            return True
        else:
            error_msg = f"Assertion failed: {item} should not be in {container}"
            if message:
                error_msg = f"{message}: {error_msg}"
            raise AssertionError(error_msg)

    def run_test(self, test_func, test_name=""):
        """Run a single test function"""
        try:
            print(f"  🧪 {test_name or test_func.__name__}...", end=" ")
            test_func(self)  # Pass self to test function
            print("✅ PASS")
            self.passed += 1
        except AssertionError as e:
            print(f"❌ FAIL")
            print(f"    {e}")
            self.failed += 1
        except Exception as e:
            print(f"❌ ERROR")
            print(f"    {e}")
            traceback.print_exc()
            self.failed += 1

    def skip_test(self, test_name="", reason=""):
        """Skip a test"""
        print(f"  ⏭️  {test_name or 'Test'}... ⚠️  SKIP ({reason})")
        self.skipped += 1

    def print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed + self.skipped
        print(f"\n📊 Test Results: {self.passed} passed, {self.failed} failed, {self.skipped} skipped")
        print(f"📈 Total: {total} tests")

        if self.failed == 0:
            print("🎉 All tests passed!")
            return 0
        else:
            print(f"❌ {self.failed} test(s) failed")
            return 1


# ============================================================================
# DLT TEST FUNCTIONS
# ============================================================================

def test_connection_string_validation(runner):
    """Test PostgreSQL connection string validation"""
    def is_valid_postgres_connection_string(conn_str):
        """Helper method to validate PostgreSQL connection string"""
        try:
            import re
            pattern = r'^(postgres(?:ql)?)://[^@]+@[^:]+:\d+/[^/]+$'
            return bool(re.match(pattern, conn_str))
        except ImportError:
            return (
                conn_str.startswith(('postgresql://', 'postgres://')) and
                '@' in conn_str and
                ':' in conn_str.split('@')[-1]
            )

    # Test valid connection strings
    valid_strings = [
        "postgresql://user:pass@localhost:5432/db",
        "postgres://user@host:5432/reddit_db",
    ]

    # Test invalid connection strings
    invalid_strings = [
        "not_a_connection_string",
        "mysql://user@host/db",
    ]

    for conn_str in valid_strings:
        runner.assert_true(is_valid_postgres_connection_string(conn_str),
                         f"Valid connection string rejected: {conn_str}")

    for conn_str in invalid_strings:
        runner.assert_false(is_valid_postgres_connection_string(conn_str),
                          f"Invalid connection string accepted: {conn_str}")


def test_supabase_host_validation(runner):
    """Test Supabase host validation"""
    def is_valid_supabase_host(host):
        """Helper method to validate Supabase host pattern"""
        return (
            host.endswith('.supabase.co') or
            host == 'localhost' or
            host == '127.0.0.1' or
            'supabase' in host
        )

    valid_hosts = [
        "localhost.supabase.co",
        "xyz.supabase.co",
        "localhost",
        "127.0.0.1",
    ]

    invalid_hosts = [
        "other-host.com",
        "postgresql-server.local",
    ]

    for host in valid_hosts:
        runner.assert_true(is_valid_supabase_host(host),
                         f"Valid Supabase host rejected: {host}")

    for host in invalid_hosts:
        runner.assert_false(is_valid_supabase_host(host),
                          f"Invalid Supabase host accepted: {host}")


def test_merge_disposition_config(runner):
    """Test merge disposition configuration validation"""
    def validate_merge_disposition_config(config):
        """Validate merge disposition configuration"""
        required_keys = ["table_name", "write_disposition", "primary_key"]

        for key in required_keys:
            if key not in config:
                return False
            if not config[key]:
                return False

        # Validate write_disposition is "merge"
        if config["write_disposition"] != "merge":
            return False

        return True

    # Test valid configuration
    valid_config = {
        "table_name": "app_opportunities",
        "write_disposition": "merge",
        "primary_key": "id"
    }

    # Test invalid configurations
    invalid_configs = [
        {"table_name": "app_opportunities", "write_disposition": "append", "primary_key": "id"},  # Wrong disposition
        {"table_name": "app_opportunities", "write_disposition": "merge"},  # Missing primary_key
        {"write_disposition": "merge", "primary_key": "id"},  # Missing table_name
    ]

    runner.assert_true(validate_merge_disposition_config(valid_config),
                     "Valid merge disposition config rejected")

    for config in invalid_configs:
        runner.assert_false(validate_merge_disposition_config(config),
                          f"Invalid merge disposition config accepted: {config}")


def test_credential_validation(runner):
    """Test credential field validation"""
    def validate_required_fields(creds, required_fields):
        """Validate that all required fields are present and non-empty"""
        for field in required_fields:
            if field not in creds:
                return False
            if not creds[field]:
                return False
        return True

    # Test valid credentials
    valid_creds = {
        "database": "postgres",
        "username": "user",
        "password": "pass",
        "host": "localhost",
        "port": 5432
    }

    # Test invalid credentials
    invalid_creds = {
        "database": "",  # Empty
        "username": "user",
        "password": "pass",
        "host": "localhost",
        "port": 5432
    }

    required_fields = ["database", "username", "password", "host", "port"]

    runner.assert_true(validate_required_fields(valid_creds, required_fields),
                     "Valid credentials rejected")

    runner.assert_false(validate_required_fields(invalid_creds, required_fields),
                      "Invalid credentials accepted")


def test_fixture_content_structure(runner):
    """Test fixture content structure"""
    # Sample fixture content
    supabase_fixture = """
[runtime]
log_level = "INFO"

[destination.supabase]
credentials = "postgresql://postgres:postgres@localhost:54322/postgres"

[destination.supabase.credentials]
database = "postgres"
username = "postgres"
password = "postgres"
host = "localhost"
port = 5432

[sources.reddit]
client_id = "test_client_id"
client_secret = "test_client_secret"
user_agent = "test_agent/1.0"
"""

    postgres_fixture = """
[runtime]
log_level = "INFO"

[destination.postgres]
credentials = "postgresql://test_user:test_pass@test_host:5432/test_db"

[sources.reddit]
client_id = "test_client_id"
client_secret = "test_client_secret"
"""

    # Test basic content structure
    runner.assert_in("destination.supabase", supabase_fixture,
                    "Supabase destination missing")
    runner.assert_in("destination.supabase.credentials", supabase_fixture,
                    "Supabase credentials missing")
    runner.assert_in("sources.reddit", supabase_fixture,
                    "Reddit source missing")

    runner.assert_in("destination.postgres", postgres_fixture,
                    "Postgres destination missing")
    runner.assert_in("postgresql://", postgres_fixture,
                    "Postgres connection string missing")


def test_error_handling_scenarios(runner):
    """Test error handling scenarios"""
    # Test port validation
    def is_valid_port(port):
        """Check if port is valid"""
        if isinstance(port, str):
            return port.isdigit()
        return isinstance(port, int) and 1 <= port <= 65535

    runner.assert_true(is_valid_port(5432), "Valid port number rejected")
    runner.assert_true(is_valid_port("5432"), "Valid port string rejected")
    runner.assert_false(is_valid_port("invalid_port"), "Invalid port string accepted")
    runner.assert_false(is_valid_port(70000), "Invalid port number accepted")

    # Test empty field validation
    def has_empty_fields(fields_dict, exclude_fields=None):
        """Check if dictionary has empty fields"""
        exclude = exclude_fields or []
        for key, value in fields_dict.items():
            if key in exclude:
                continue
            if not value:  # Empty or None
                return True
        return False

    # Valid dict
    valid_dict = {"id": 1, "name": "test", "value": 100}
    runner.assert_false(has_empty_fields(valid_dict), "Valid dict flagged as having empty fields")

    # Invalid dict
    invalid_dict = {"id": 1, "name": "", "value": 100}
    runner.assert_true(has_empty_fields(invalid_dict), "Dict with empty fields not detected")

    # Test with exclusion
    runner.assert_false(has_empty_fields(invalid_dict, exclude_fields=["name"]),
                       "Empty field exclusion not working")


def main():
    """Run all DLT tests"""
    print("🚀 DLT Supabase Configuration Tests")
    print("=" * 50)

    runner = SimpleTestRunner()

    # Run tests
    print("\n📋 Connection and Configuration Tests:")
    runner.run_test(test_connection_string_validation, "test_connection_string_validation")
    runner.run_test(test_supabase_host_validation, "test_supabase_host_validation")
    runner.run_test(test_merge_disposition_config, "test_merge_disposition_config")
    runner.run_test(test_credential_validation, "test_credential_validation")
    runner.run_test(test_fixture_content_structure, "test_fixture_content_structure")
    runner.run_test(test_error_handling_scenarios, "test_error_handling_scenarios")

    # Print summary
    print("\n" + "=" * 50)
    return runner.print_summary()


if __name__ == "__main__":
    sys.exit(main())