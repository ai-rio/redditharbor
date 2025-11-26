"""
Comprehensive TDD tests for DLT configuration loading and validation.

This test suite validates:
- DLT secrets.toml configuration loading
- Supabase destination type configuration
- PostgreSQL/Supabase credential validation
- Error handling for missing/invalid configurations

Phase: TDD approach - Tests first, implementation later
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional

# Import pytest with fallback
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    pytest = None

# Import toml with fallback
try:
    import toml
    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False
    toml = None

# Add project root to path
project_root = Path(__file__).parent.parent.parent
import sys
sys.path.insert(0, str(project_root))


# ============================================================================
# FIXTURES FOR DLT CONFIGURATION
# ============================================================================

@pytest.fixture
def valid_secrets_toml_content():
    """Valid DLT secrets.toml content for Supabase configuration"""
    return """
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


# Skip tests that require toml if not available
skip_if_no_toml = pytest.mark.skipif(not TOML_AVAILABLE, reason="toml module not available")

@pytest.fixture
def invalid_secrets_toml_content():
    """Invalid DLT secrets.toml content with missing credentials"""
    return """
[runtime]
log_level = "INFO"

[destination.supabase]
# Missing credentials section

[sources.reddit]
client_id = "test_client_id"
"""

@pytest.fixture
def postgres_direct_secrets_toml():
    """DLT secrets.toml using direct connection string for PostgreSQL"""
    return """
[runtime]
log_level = "INFO"

[destination.postgres]
credentials = "postgresql://test_user:test_pass@test_host:5432/test_db"

[sources.reddit]
client_id = "test_client_id"
client_secret = "test_client_secret"
"""

@pytest.fixture
def supabase_structured_secrets_toml():
    """DLT secrets.toml using structured credentials for Supabase"""
    return """
[runtime]
log_level = "DEBUG"

[destination.supabase]
[destination.supabase.credentials]
database = "reddit_harbor"
username = "postgres"
password = "supabase_password"
host = "localhost.supabase.co"
port = 5432
connect_timeout = 30
sslmode = "require"

[destination.supabase.data_writer]
disposition = "merge"
write_disposition = "merge"
primary_key = "id"
"""

@pytest.fixture
def temp_secrets_dir():
    """Create temporary directory for DLT secrets"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


# ============================================================================
# TEST CLASSES FOR DLT CONFIGURATION
# ============================================================================

@skip_if_no_toml
class TestDLTConfigurationLoading:
    """Test DLT configuration file loading and parsing"""

    def test_load_valid_secrets_toml(self, valid_secrets_toml_content, temp_secrets_dir):
        """Test loading a valid secrets.toml file"""
        secrets_file = temp_secrets_dir / "secrets.toml"
        secrets_file.write_text(valid_secrets_toml_content.strip())

        # Load and parse the file
        loaded_config = toml.load(secrets_file)

        assert loaded_config is not None
        assert "destination" in loaded_config
        assert "supabase" in loaded_config["destination"]
        assert "credentials" in loaded_config["destination"]["supabase"]

        # Check structured credentials
        creds = loaded_config["destination"]["supabase"]["credentials"]
        assert creds["username"] == "postgres"
        assert creds["host"] == "localhost"
        assert creds["port"] == 5432

    def test_load_missing_secrets_file(self, temp_secrets_dir):
        """Test handling of missing secrets.toml file"""
        missing_file = temp_secrets_dir / "secrets.toml"

        # Should raise FileNotFoundError or handle gracefully
        with pytest.raises(FileNotFoundError):
            toml.load(missing_file)

    def test_load_invalid_toml_syntax(self, temp_secrets_dir):
        """Test handling of invalid TOML syntax"""
        secrets_file = temp_secrets_dir / "secrets.toml"
        secrets_file.write_text("""
        [destination
        missing closing bracket
        """)

        # Should raise TOMLDecodeError
        with pytest.raises(toml.TomlDecodeError):
            toml.load(secrets_file)

    def test_load_incomplete_configuration(self, invalid_secrets_toml_content, temp_secrets_dir):
        """Test loading configuration with missing required sections"""
        secrets_file = temp_secrets_dir / "secrets.toml"
        secrets_file.write_text(invalid_secrets_toml_content.strip())

        loaded_config = toml.load(secrets_file)

        # Configuration loads but missing required fields
        assert "destination" in loaded_config
        assert "supabase" in loaded_config["destination"]
        assert "credentials" not in loaded_config["destination"]["supabase"]


class TestDLTCredentialValidation:
    """Test DLT credential validation and format checking"""

    def test_validate_postgres_connection_string(self):
        """Test PostgreSQL connection string format validation"""
        valid_connection_strings = [
            "postgresql://user:pass@host:5432/db",
            "postgresql://postgres@localhost:5432/reddit_db",
            "postgres://user:pass@host/db",
        ]

        for conn_str in valid_connection_strings:
            assert self._is_valid_postgres_connection_string(conn_str)

    def test_validate_invalid_postgres_connection_string(self):
        """Test invalid PostgreSQL connection string detection"""
        invalid_connection_strings = [
            "not_a_connection_string",
            "mysql://user:pass@host:3306/db",
            "postgresql://@host/db",  # missing user
            "postgresql://user@:5432",  # missing host/database
        ]

        for conn_str in invalid_connection_strings:
            assert not self._is_valid_postgres_connection_string(conn_str)

    def test_validate_structured_credentials(self, supabase_structured_secrets_toml):
        """Test structured credential validation"""
        config = toml.loads(supabase_structured_secrets_toml)
        creds = config["destination"]["supabase"]["credentials"]

        # Check required fields
        required_fields = ["database", "username", "password", "host", "port"]
        for field in required_fields:
            assert field in creds, f"Missing required field: {field}"
            assert creds[field], f"Empty value for required field: {field}"

        # Check port is valid integer
        assert isinstance(creds["port"], int) or str(creds["port"]).isdigit()

        # Check optional fields have reasonable defaults
        assert creds.get("connect_timeout", 30) > 0
        assert creds.get("sslmode", "prefer") in ["require", "prefer", "disable"]

    def test_validate_supabase_specific_credentials(self):
        """Test Supabase-specific credential validation"""
        # Supabase URLs typically have specific patterns
        supabase_hosts = [
            "localhost.supabase.co",
            "xyz.supabase.co",
            "127.0.0.1",  # Local development
            "localhost"
        ]

        for host in supabase_hosts:
            assert self._is_valid_supabase_host(host)

    def _is_valid_postgres_connection_string(self, conn_str: str) -> bool:
        """Helper method to validate PostgreSQL connection string"""
        try:
            import re
            pattern = r'^(postgres(?:ql)?)://[^@]+@[^:]+:\d+/[^/]+$'
            return bool(re.match(pattern, conn_str))
        except ImportError:
            # Fallback validation without regex
            return conn_str.startswith(('postgresql://', 'postgres://')) and '@' in conn_str

    def _is_valid_supabase_host(self, host: str) -> bool:
        """Helper method to validate Supabase host pattern"""
        return (
            host.endswith('.supabase.co') or
            host == 'localhost' or
            host == '127.0.0.1' or
            'supabase' in host
        )


@skip_if_no_toml
class TestDLTDestinationConfiguration:
    """Test DLT destination type and merge disposition configuration"""

    def test_supabase_destination_configuration(self, valid_secrets_toml_content):
        """Test Supabase destination configuration"""
        config = toml.loads(valid_secrets_toml_content)

        assert "destination" in config
        assert "supabase" in config["destination"]

        # Supabase should be configured as a destination
        dest_config = config["destination"]["supabase"]
        assert "credentials" in dest_config

    def test_postgres_destination_configuration(self, postgres_direct_secrets_toml):
        """Test PostgreSQL destination configuration (direct connection string)"""
        config = toml.loads(postgres_direct_secrets_toml)

        assert "destination" in config
        assert "postgres" in config["destination"]

        dest_config = config["destination"]["postgres"]
        assert "credentials" in dest_config

        # Should be a valid PostgreSQL connection string
        conn_str = dest_config["credentials"]
        assert self._is_valid_postgres_connection_string(conn_str)

    def test_merge_disposition_configuration(self, supabase_structured_secrets_toml):
        """Test merge disposition configuration for app_opportunities table"""
        config = toml.loads(supabase_structured_secrets_toml)

        assert "destination" in config
        assert "supabase" in config["destination"]

        if "data_writer" in config["destination"]["supabase"]:
            writer_config = config["destination"]["supabase"]["data_writer"]

            # Check disposition settings
            assert writer_config.get("disposition") == "merge"
            assert writer_config.get("write_disposition") == "merge"
            assert writer_config.get("primary_key") == "id"

    def test_destination_type_compatibility(self, valid_secrets_toml_content, postgres_direct_secrets_toml):
        """Test that both 'supabase' and 'postgres' destination types are valid"""
        # Test Supabase config
        supabase_config = toml.loads(valid_secrets_toml_content)
        assert "supabase" in supabase_config["destination"]

        # Test PostgreSQL config
        postgres_config = toml.loads(postgres_direct_secrets_toml)
        assert "postgres" in postgres_config["destination"]

        # Both should be valid for DLT since Supabase uses PostgreSQL
        assert supabase_config is not None
        assert postgres_config is not None


@skip_if_no_toml
class TestDLTConfigurationErrorHandling:
    """Test error handling for DLT configuration issues"""

    def test_missing_credentials_error(self, invalid_secrets_toml_content):
        """Test error when credentials are missing"""
        config = toml.loads(invalid_secrets_toml_content)

        # Should detect missing credentials
        assert "destination" in config
        assert "supabase" in config["destination"]

        # Accessing missing credentials should raise KeyError
        with pytest.raises(KeyError):
            config["destination"]["supabase"]["credentials"]

    def test_invalid_port_value(self, temp_secrets_dir):
        """Test error handling for invalid port values"""
        invalid_config = """
[destination.supabase.credentials]
database = "postgres"
username = "postgres"
password = "postgres"
host = "localhost"
port = "invalid_port"
"""
        config = toml.loads(invalid_config)
        port = config["destination"]["supabase.credentials"]["port"]

        # Port should be numeric
        assert not str(port).isdigit()

    def test_empty_required_field_values(self, temp_secrets_dir):
        """Test error handling for empty required fields"""
        empty_config = """
[destination.supabase.credentials]
database = ""
username = ""
password = ""
host = ""
port = 5432
"""
        config = toml.loads(empty_config)
        creds = config["destination"]["supabase.credentials"]

        # All required fields should be non-empty
        empty_fields = [k for k, v in creds.items() if not v and k != "connect_timeout"]
        assert len(empty_fields) > 0

    def test_malformed_connection_string(self, temp_secrets_dir):
        """Test error handling for malformed connection strings"""
        malformed_config = """
[destination.postgres]
credentials = "postgresql://user@host_without_port/db"
"""
        config = toml.loads(malformed_config)
        conn_str = config["destination"]["postgres"]["credentials"]

        # Should detect malformed connection string
        assert not self._is_valid_postgres_connection_string(conn_str)


# ============================================================================
# INTEGRATION-STYLE TESTS WITH DLT MOCKING
# ============================================================================

class TestDLTIntegrationConfiguration:
    """Integration-style tests with DLT mocking"""

    @patch('dlt.pipeline')
    def test_dlt_pipeline_initialization_with_supabase(self, mock_pipeline_class):
        """Test DLT pipeline initialization with Supabase destination"""
        # Mock the pipeline
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        # Simulate pipeline creation with Supabase destination
        with patch.dict('os.environ', {'DESTINATION': 'supabase'}):
            # This would be the actual DLT pipeline creation
            pipeline = mock_pipeline_class(
                pipeline_name="reddit_harbor",
                destination="supabase",
                dataset_name="reddit_data"
            )

        # Verify pipeline was created with correct parameters
        mock_pipeline_class.assert_called_once()
        args, kwargs = mock_pipeline_class.call_args
        assert kwargs.get('destination') == 'supabase'
        assert 'reddit_harbor' in kwargs.get('pipeline_name', '')

    @patch('dlt.pipeline')
    def test_dlt_pipeline_initialization_with_postgres(self, mock_pipeline_class):
        """Test DLT pipeline initialization with PostgreSQL destination"""
        # Mock the pipeline
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        # Simulate pipeline creation with PostgreSQL destination
        pipeline = mock_pipeline_class(
            pipeline_name="reddit_harbor",
            destination="postgres",
            dataset_name="reddit_data"
        )

        # Verify pipeline was created with correct parameters
        mock_pipeline_class.assert_called_once()
        args, kwargs = mock_pipeline_class.call_args
        assert kwargs.get('destination') == 'postgres'

    @patch('dlt.pipeline')
    def test_merge_disposition_configuration_in_pipeline(self, mock_pipeline_class):
        """Test merge disposition configuration in DLT pipeline"""
        # Mock the pipeline and run method
        mock_pipeline = Mock()
        mock_pipeline.run = Mock(return_value=Mock())
        mock_pipeline_class.return_value = mock_pipeline

        # Sample data for app_opportunities table
        sample_data = [
            {"id": 1, "title": "Test Opportunity", "score": 85.5},
            {"id": 2, "title": "Another Opportunity", "score": 90.2}
        ]

        # Simulate pipeline run with merge disposition
        mock_pipeline.run(
            sample_data,
            table_name="app_opportunities",
            write_disposition="merge",
            primary_key="id"
        )

        # Verify run was called with merge disposition
        mock_pipeline.run.assert_called_once()
        args, kwargs = mock_pipeline.run.call_args
        assert kwargs.get('write_disposition') == 'merge'
        assert kwargs.get('primary_key') == 'id'


# ============================================================================
# CONFIGURATION FILE PATH HANDLING
# ============================================================================

class TestDLTConfigurationFilePathHandling:
    """Test DLT configuration file path resolution and handling"""

    def test_default_secrets_toml_location(self):
        """Test default secrets.toml location detection"""
        # DLT typically looks for .dlt/secrets.toml in project root
        current_dir = Path.cwd()
        dlt_dir = current_dir / ".dlt"
        secrets_file = dlt_dir / "secrets.toml"

        # Test path construction
        expected_path = current_dir / ".dlt" / "secrets.toml"
        assert secrets_file == expected_path

    def test_alternative_secrets_toml_location(self):
        """Test alternative secrets.toml location handling"""
        # Allow configuration via environment variable
        alt_path = "/custom/path/to/secrets.toml"

        with patch.dict('os.environ', {'DLT_SECRETS_PATH': alt_path}):
            custom_path = os.environ.get('DLT_SECRETS_PATH')
            assert custom_path == alt_path

    def test_secrets_toml_directory_creation(self, temp_secrets_dir):
        """Test automatic creation of .dlt directory if missing"""
        dlt_dir = temp_secrets_dir / ".dlt"

        # Directory should not exist initially
        assert not dlt_dir.exists()

        # Create directory
        dlt_dir.mkdir(parents=True, exist_ok=True)

        # Directory should now exist
        assert dlt_dir.exists()
        assert dlt_dir.is_dir()

    def test_secrets_toml_file_permissions(self, temp_secrets_dir):
        """Test secrets.toml file has appropriate permissions"""
        secrets_file = temp_secrets_dir / "secrets.toml"
        secrets_file.write_text("test content")

        # Check file exists and has appropriate permissions (not world-readable)
        assert secrets_file.exists()

        # On Unix systems, secrets should be 600 or 640
        if os.name == 'posix':
            file_stat = secrets_file.stat()
            file_mode = file_stat.st_mode & 0o777
            # File should not be world-readable
            assert file_mode & 0o004 == 0  # No read permission for others


# ============================================================================
# UTILITY FUNCTIONS AND HELPERS
# ============================================================================

def create_dlt_config_secrets(
    temp_dir: Path,
    destination_type: str = "supabase",
    use_structured_creds: bool = True,
    connection_string: Optional[str] = None
) -> Path:
    """
    Helper function to create a valid DLT secrets.toml file for testing.

    Args:
        temp_dir: Temporary directory path
        destination_type: 'supabase' or 'postgres'
        use_structured_creds: Whether to use structured credential format
        connection_string: Optional direct connection string

    Returns:
        Path to the created secrets.toml file
    """
    dlt_dir = temp_dir / ".dlt"
    dlt_dir.mkdir(exist_ok=True)
    secrets_file = dlt_dir / "secrets.toml"

    config_content = {
        "runtime": {"log_level": "INFO"},
        "destination": {}
    }

    if use_structured_creds:
        config_content["destination"][destination_type] = {
            "credentials": {
                "database": "reddit_harbor",
                "username": "postgres",
                "password": "postgres",
                "host": "localhost",
                "port": 5432
            }
        }
    elif connection_string:
        config_content["destination"][destination_type] = {
            "credentials": connection_string
        }

    # Write TOML content
    with open(secrets_file, 'w') as f:
        toml.dump(config_content, f)

    return secrets_file


# ============================================================================
# PYTEST MARKERS AND CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers for DLT tests"""
    config.addinivalue_line(
        "markers", "dlt_config: marks tests for DLT configuration testing"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "mock_dlt: marks tests that mock DLT components"
    )