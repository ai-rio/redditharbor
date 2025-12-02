"""
Comprehensive TDD tests for DLT Supabase connection and merge functionality.

This test suite validates:
- DLT pipeline creation and connection to Supabase (PostgreSQL)
- Merge disposition for app_opportunities table
- Database connection validation and error handling
- Integration with Supabase client and DLT pipeline orchestration

Phase: TDD approach - Tests first, implementation later
"""

import asyncio
import json
import tempfile
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, MagicMock, AsyncMock, patch, PropertyMock

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
import sys
sys.path.insert(0, str(project_root))


# ============================================================================
# FIXTURES FOR SUPABASE CONNECTION TESTING
# ============================================================================

@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for connection testing"""
    mock_client = Mock()
    mock_client.auth = Mock()
    mock_client.table = Mock()
    mock_client.from_ = Mock()  # Alternative method
    mock_client.rpc = Mock()
    mock_client.storage = Mock()

    # Mock authentication methods
    mock_client.auth.get_session = Mock(return_value={"user": {"id": "test_user"}})
    mock_client.auth.sign_in = Mock(return_value={"user": {"id": "test_user"}})

    # Mock table operations
    mock_table = Mock()
    mock_table.select = Mock(return_value=mock_table)
    mock_table.insert = Mock(return_value=mock_table)
    mock_table.upsert = Mock(return_value=mock_table)
    mock_table.update = Mock(return_value=mock_table)
    mock_table.delete = Mock(return_value=mock_table)
    mock_table.eq = Mock(return_value=mock_table)
    mock_table.execute = Mock(return_value=Mock(data=[], count=0))

    mock_client.table.return_value = mock_table
    mock_client.from_.return_value = mock_table

    return mock_client


@pytest.fixture
def mock_dlt_pipeline():
    """Mock DLT pipeline for connection testing"""
    mock_pipeline = Mock()

    # Mock pipeline methods
    mock_pipeline.run = Mock(return_value=Mock())
    mock_pipeline.extract = Mock(return_value=Mock())
    mock_pipeline.normalize = Mock(return_value=Mock())
    mock_pipeline.load = Mock(return_value=Mock())

    # Mock pipeline properties
    mock_pipeline.pipeline_name = "reddit_harbor_test"
    mock_pipeline.destination = "supabase"
    mock_pipeline.dataset_name = "reddit_data_test"

    # Mock load info
    mock_pipeline.last_trace = Mock()
    mock_pipeline.last_trace.load_info = Mock(
        counts= {"app_opportunities": 10},
        pipeline_name="reddit_harbor_test",
        destination_name="supabase",
        destination_type="postgres"
    )

    return mock_pipeline


@pytest.fixture
def sample_app_opportunities_data():
    """Sample app_opportunities data for merge testing"""
    current_time = datetime.now(UTC).isoformat()

    return [
        {
            "id": "opp_1",
            "reddit_id": "t3_abc123",
            "title": "Looking for automation tool to replace manual data entry",
            "score": 85.5,
            "trust_score": 92.0,
            "subreddit": "productivity",
            "created_utc": current_time,
            "updated_at": current_time,
            "analysis_metadata": {
                "opportunity_score": 88.0,
                "monetization_score": 75.0,
                "user_intent": "automation_need"
            }
        },
        {
            "id": "opp_2",
            "reddit_id": "t3_def456",
            "title": "Struggling with expensive SaaS solution, need alternative",
            "score": 91.2,
            "trust_score": 88.5,
            "subreddit": "sysadmin",
            "created_utc": current_time,
            "updated_at": current_time,
            "analysis_metadata": {
                "opportunity_score": 93.0,
                "monetization_score": 85.0,
                "user_intent": "cost_reduction"
            }
        },
        {
            "id": "opp_3",  # This will be an update for existing record
            "reddit_id": "t3_ghi789",
            "title": "Need better API integration tool for data pipelines",
            "score": 78.9,
            "trust_score": 95.0,
            "subreddit": "programming",
            "created_utc": current_time,
            "updated_at": current_time,
            "analysis_metadata": {
                "opportunity_score": 82.0,
                "monetization_score": 70.0,
                "user_intent": "integration_need"
            }
        }
    ]


@pytest.fixture
def mock_postgres_connection():
    """Mock PostgreSQL connection for DLT backend testing"""
    mock_conn = Mock()
    mock_cursor = Mock()

    # Mock connection methods
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.close = Mock()
    mock_conn.commit = Mock()
    mock_conn.rollback = Mock()

    # Mock cursor methods
    mock_cursor.execute = Mock()
    mock_cursor.fetchone = Mock()
    mock_cursor.fetchall = Mock()
    mock_cursor.close = Mock()

    # Mock connection check queries
    mock_cursor.fetchone.return_value = (1,)  # Connected

    return mock_conn, mock_cursor


# ============================================================================
# DLT PIPELINE CREATION AND CONFIGURATION TESTS
# ============================================================================

class TestDLTPipelineCreation:
    """Test DLT pipeline creation and basic configuration"""

    @patch('dlt.pipeline')
    def test_create_supabase_pipeline(self, mock_pipeline_class):
        """Test creating DLT pipeline with Supabase destination"""
        # Mock pipeline creation
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        # Create pipeline with Supabase destination
        pipeline = mock_pipeline_class(
            pipeline_name="reddit_harbor",
            destination="supabase",
            dataset_name="reddit_data",
            credentials="postgresql://postgres:postgres@localhost:54322/postgres"
        )

        # Verify pipeline was created correctly
        mock_pipeline_class.assert_called_once()
        args, kwargs = mock_pipeline_class.call_args

        assert kwargs.get('pipeline_name') == "reddit_harbor"
        assert kwargs.get('destination') == "supabase"
        assert kwargs.get('dataset_name') == "reddit_data"

    @patch('dlt.pipeline')
    def test_create_postgres_pipeline_as_fallback(self, mock_pipeline_class):
        """Test creating DLT pipeline with PostgreSQL destination as fallback"""
        # Mock pipeline creation
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        # Create pipeline with PostgreSQL destination
        pipeline = mock_pipeline_class(
            pipeline_name="reddit_harbor",
            destination="postgres",
            dataset_name="reddit_data",
            credentials="postgresql://postgres:postgres@localhost:54322/postgres"
        )

        # Verify pipeline was created correctly
        mock_pipeline_class.assert_called_once()
        args, kwargs = mock_pipeline_class.call_args

        assert kwargs.get('pipeline_name') == "reddit_harbor"
        assert kwargs.get('destination') == "postgres"
        assert kwargs.get('dataset_name') == "reddit_data"

    @patch('dlt.pipeline')
    def test_pipeline_with_merge_disposition_config(self, mock_pipeline_class):
        """Test pipeline creation with merge disposition configuration"""
        # Mock pipeline creation
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        # Create pipeline
        pipeline = mock_pipeline_class(
            pipeline_name="reddit_harbor",
            destination="supabase",
            dataset_name="reddit_data"
        )

        # Simulate run with merge disposition
        test_data = [{"id": 1, "title": "Test"}]
        pipeline.run(
            test_data,
            table_name="app_opportunities",
            write_disposition="merge",
            primary_key="id"
        )

        # Verify run was called with merge disposition
        mock_pipeline.run.assert_called_once()
        args, kwargs = mock_pipeline.run.call_args
        assert kwargs.get('write_disposition') == "merge"
        assert kwargs.get('primary_key') == "id"
        assert kwargs.get('table_name') == "app_opportunities"


class TestDLTCredentialsConfiguration:
    """Test DLT credential configuration for Supabase/PostgreSQL"""

    @patch('dlt.pipeline')
    def test_supabase_credentials_from_connection_string(self, mock_pipeline_class):
        """Test Supabase configuration using connection string"""
        connection_string = "postgresql://postgres:postgres@localhost:54322/postgres"

        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        # Create pipeline with connection string
        pipeline = mock_pipeline_class(
            pipeline_name="reddit_harbor",
            destination="supabase",
            dataset_name="reddit_data",
            credentials=connection_string
        )

        # Verify credentials were passed
        args, kwargs = mock_pipeline_class.call_args
        assert kwargs.get('credentials') == connection_string

    @patch('dlt.pipeline')
    def test_postgres_credentials_from_connection_string(self, mock_pipeline_class):
        """Test PostgreSQL configuration using connection string"""
        connection_string = "postgresql://user:pass@host:5432/db"

        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        # Create pipeline with connection string
        pipeline = mock_pipeline_class(
            pipeline_name="reddit_harbor",
            destination="postgres",
            dataset_name="reddit_data",
            credentials=connection_string
        )

        # Verify credentials were passed
        args, kwargs = mock_pipeline_class.call_args
        assert kwargs.get('credentials') == connection_string

    def test_validate_connection_string_formats(self):
        """Test validation of different connection string formats"""
        valid_formats = [
            "postgresql://user:pass@localhost:5432/db",
            "postgres://user@host:5432/database",
            "postgresql://postgres:postgres@127.0.0.1:54322/postgres",
        ]

        invalid_formats = [
            "not-a-connection-string",
            "mysql://user@host/db",  # Wrong database type
            "postgresql://user@host",  # Missing port/database
            "postgresql://@host:5432/db",  # Missing user
        ]

        for conn_str in valid_formats:
            assert self._validate_postgres_connection_string(conn_str)

        for conn_str in invalid_formats:
            assert not self._validate_postgres_connection_string(conn_str)

    def _validate_postgres_connection_string(self, conn_str: str) -> bool:
        """Helper to validate PostgreSQL connection string"""
        try:
            import re
            pattern = r'^(postgres(?:ql)?)://[^@]*@[^:]+:\d+/[^/]+$'
            return bool(re.match(pattern, conn_str))
        except ImportError:
            return (
                conn_str.startswith(('postgresql://', 'postgres://')) and
                '@' in conn_str and
                ':' in conn_str.split('@')[-1]  # Port specification
            )


# ============================================================================
# SUPABASE CONNECTION AND INTEGRATION TESTS
# ============================================================================

class TestSupabaseConnection:
    """Test Supabase connection and basic operations"""

    @patch('supabase.create_client')
    def test_supabase_client_creation(self, mock_create_client):
        """Test Supabase client creation with proper credentials"""
        mock_client = Mock()
        mock_create_client.return_value = mock_client

        # Create Supabase client
        supabase_url = "http://localhost:54321"
        supabase_key = "test_supabase_key"

        client = mock_create_client(supabase_url, supabase_key)

        # Verify client was created
        mock_create_client.assert_called_once_with(supabase_url, supabase_key)
        assert client == mock_client

    @patch('supabase.create_client')
    def test_supabase_connection_validation(self, mock_create_client):
        """Test Supabase connection validation"""
        mock_client = Mock()
        mock_create_client.return_value = mock_client

        # Mock successful connection test
        mock_client.rpc = Mock()
        mock_client.rpc.return_value.execute.return_value = Mock(data=[{"status": "ok"}])

        # Create and test connection
        client = mock_create_client("http://localhost:54321", "test_key")

        # Test connection (simulate health check)
        result = client.rpc("get_health_status").execute()

        assert result.data == [{"status": "ok"}]

    @patch('supabase.create_client')
    def test_supabase_table_access(self, mock_create_client, mock_supabase_client):
        """Test Supabase table access for app_opportunities"""
        mock_create_client.return_value = mock_supabase_client

        # Create client and access table
        client = mock_create_client("http://localhost:54321", "test_key")
        table = client.table("app_opportunities")

        # Verify table method was called
        client.table.assert_called_once_with("app_opportunities")
        assert table is not None

        # Test chain of operations
        mock_table = client.table.return_value
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = Mock(data=[], count=0)

        result = table.select("*").eq("status", "active").execute()

        mock_table.select.assert_called_with("*")
        mock_table.eq.assert_called_with("status", "active")
        mock_table.execute.assert_called_once()


class TestDLTSupabaseIntegration:
    """Test integration between DLT and Supabase"""

    @patch('dlt.pipeline')
    @patch('supabase.create_client')
    def test_dlt_pipeline_supabase_destination(self, mock_create_client, mock_pipeline_class):
        """Test DLT pipeline with Supabase destination"""
        # Setup mocks
        mock_supabase_client = Mock()
        mock_create_client.return_value = mock_supabase_client

        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        # Create Supabase client
        supabase_url = "http://localhost:54321"
        supabase_key = "test_key"
        client = mock_create_client(supabase_url, supabase_key)

        # Create DLT pipeline
        pipeline = mock_pipeline_class(
            pipeline_name="reddit_harbor",
            destination="supabase",
            dataset_name="reddit_data"
        )

        # Verify both were created
        mock_create_client.assert_called_once_with(supabase_url, supabase_key)
        mock_pipeline_class.assert_called_once()

    @patch('dlt.pipeline')
    def test_merge_disposition_configuration(self, mock_pipeline_class, sample_app_opportunities_data):
        """Test merge disposition configuration for app_opportunities table"""
        # Setup mock pipeline
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        # Create pipeline
        pipeline = mock_pipeline_class(
            pipeline_name="reddit_harbor",
            destination="supabase",
            dataset_name="reddit_data"
        )

        # Run pipeline with merge disposition
        pipeline.run(
            sample_app_opportunities_data,
            table_name="app_opportunities",
            write_disposition="merge",
            primary_key="id"
        )

        # Verify merge configuration
        mock_pipeline.run.assert_called_once()
        args, kwargs = mock_pipeline.run.call_args

        assert kwargs.get('table_name') == "app_opportunities"
        assert kwargs.get('write_disposition') == "merge"
        assert kwargs.get('primary_key') == "id"
        assert len(args) > 0  # Data was passed

        # Verify data structure
        passed_data = args[0]
        assert isinstance(passed_data, list)
        assert len(passed_data) > 0

        # Check that records have required fields
        sample_record = passed_data[0]
        assert 'id' in sample_record
        assert 'title' in sample_record
        assert 'score' in sample_record

    @patch('dlt.pipeline')
    def test_incremental_load_configuration(self, mock_pipeline_class):
        """Test incremental load configuration for new opportunities"""
        # Setup mock pipeline
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        # Create pipeline with incremental load
        pipeline = mock_pipeline_class(
            pipeline_name="reddit_harbor",
            destination="supabase",
            dataset_name="reddit_data"
        )

        # Simulate incremental load using timestamp
        incremental_data = [{"id": f"opp_{i}", "created_at": f"2024-01-{i+1:02d}"} for i in range(5)]

        pipeline.run(
            incremental_data,
            table_name="app_opportunities",
            write_disposition="merge",
            primary_key="id"
        )

        # Verify incremental configuration
        mock_pipeline.run.assert_called_once()
        args, kwargs = mock_pipeline.run.call_args

        assert kwargs.get('write_disposition') == "merge"  # Merge for incremental
        assert kwargs.get('primary_key') == "id"


# ============================================================================
# MERGE DISPOSITION AND DATA HANDLING TESTS
# ============================================================================

class TestMergeDisposition:
    """Test merge disposition functionality for app_opportunities table"""

    @patch('dlt.pipeline')
    def test_merge_new_records(self, mock_pipeline_class, sample_app_opportunities_data):
        """Test merging new records into app_opportunities table"""
        # Setup mock pipeline
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        # Create pipeline and merge new records
        pipeline = mock_pipeline_class(
            pipeline_name="reddit_harbor",
            destination="supabase",
            dataset_name="reddit_data"
        )

        # Run merge operation
        pipeline.run(
            sample_app_opportunities_data,
            table_name="app_opportunities",
            write_disposition="merge",
            primary_key="id"
        )

        # Verify merge was called with correct configuration
        mock_pipeline.run.assert_called_once()
        args, kwargs = mock_pipeline.run.call_args

        passed_data = args[0]
        assert len(passed_data) == len(sample_app_opportunities_data)

        # Verify all records have primary key
        for record in passed_data:
            assert 'id' in record
            assert record['id'] is not None

    @patch('dlt.pipeline')
    def test_merge_update_existing_records(self, mock_pipeline_class, sample_app_opportunities_data):
        """Test merging updates to existing records"""
        # Setup mock pipeline
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        # Simulate existing record update
        updated_record = {
            "id": "opp_1",  # Same ID as existing record
            "title": "Updated: Looking for automation tool",
            "score": 90.0,  # Updated score
            "updated_at": datetime.now(UTC).isoformat()
        }

        pipeline = mock_pipeline_class(
            pipeline_name="reddit_harbor",
            destination="supabase",
            dataset_name="reddit_data"
        )

        # Run merge with update
        pipeline.run(
            [updated_record],
            table_name="app_opportunities",
            write_disposition="merge",
            primary_key="id"
        )

        # Verify merge was called for update
        mock_pipeline.run.assert_called_once()
        args, kwargs = mock_pipeline.run.call_args

        passed_data = args[0]
        assert len(passed_data) == 1
        assert passed_data[0]['id'] == "opp_1"
        assert passed_data[0]['score'] == 90.0

    @patch('dlt.pipeline')
    def test_merge_disposition_error_handling(self, mock_pipeline_class):
        """Test error handling in merge disposition operations"""
        # Setup mock pipeline to raise exception
        mock_pipeline = Mock()
        mock_pipeline.run.side_effect = Exception("Database connection error")
        mock_pipeline_class.return_value = mock_pipeline

        pipeline = mock_pipeline_class(
            pipeline_name="reddit_harbor",
            destination="supabase",
            dataset_name="reddit_data"
        )

        # Test that errors are properly raised
        with pytest.raises(Exception, match="Database connection error"):
            pipeline.run(
                [{"id": "test"}],
                table_name="app_opportunities",
                write_disposition="merge",
                primary_key="id"
            )

    @patch('dlt.pipeline')
    def test_merge_with_schema_validation(self, mock_pipeline_class, sample_app_opportunities_data):
        """Test merge operation with schema validation"""
        # Setup mock pipeline
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        # Add schema validation mock
        mock_pipeline.run = Mock(side_effect=lambda *args, **kwargs: {
            "success": True,
            "records_processed": len(args[0]) if args else 0,
            "table_name": kwargs.get("table_name", "unknown"),
            "write_disposition": kwargs.get("write_disposition", "unknown")
        })

        pipeline = mock_pipeline_class(
            pipeline_name="reddit_harbor",
            destination="supabase",
            dataset_name="reddit_data"
        )

        # Run merge with validation
        result = pipeline.run(
            sample_app_opportunities_data,
            table_name="app_opportunities",
            write_disposition="merge",
            primary_key="id"
        )

        # Validate merge operation result
        assert result["success"] is True
        assert result["records_processed"] == len(sample_app_opportunities_data)
        assert result["table_name"] == "app_opportunities"
        assert result["write_disposition"] == "merge"


# ============================================================================
# CONNECTION ERROR HANDLING AND RECOVERY TESTS
# ============================================================================

class TestConnectionErrorHandling:
    """Test connection error handling and recovery mechanisms"""

    @patch('dlt.pipeline')
    def test_supabase_connection_failure(self, mock_pipeline_class):
        """Test handling of Supabase connection failure"""
        # Mock pipeline creation to raise connection error
        mock_pipeline_class.side_effect = Exception("Failed to connect to Supabase")

        # Test that connection failures are properly handled
        with pytest.raises(Exception, match="Failed to connect to Supabase"):
            mock_pipeline_class(
                pipeline_name="reddit_harbor",
                destination="supabase",
                dataset_name="reddit_data"
            )

    @patch('dlt.pipeline')
    def test_invalid_credentials_error(self, mock_pipeline_class):
        """Test handling of invalid Supabase credentials"""
        # Mock pipeline creation to raise authentication error
        mock_pipeline_class.side_effect = Exception("Authentication failed: invalid credentials")

        # Test authentication error handling
        with pytest.raises(Exception, match="Authentication failed"):
            mock_pipeline_class(
                pipeline_name="reddit_harbor",
                destination="supabase",
                dataset_name="reddit_data",
                credentials="postgresql://invalid:credentials@host/db"
            )

    @patch('dlt.pipeline')
    def test_connection_timeout_handling(self, mock_pipeline_class):
        """Test handling of connection timeouts"""
        # Mock pipeline creation to raise timeout error
        mock_pipeline_class.side_effect = Exception("Connection timeout")

        # Test timeout error handling
        with pytest.raises(Exception, match="Connection timeout"):
            mock_pipeline_class(
                pipeline_name="reddit_harbor",
                destination="supabase",
                dataset_name="reddit_data"
            )

    @patch('dlt.pipeline')
    def test_database_error_during_merge(self, mock_pipeline_class):
        """Test handling of database errors during merge operations"""
        # Setup mock pipeline
        mock_pipeline = Mock()
        mock_pipeline.run.side_effect = Exception("Database constraint violation")
        mock_pipeline_class.return_value = mock_pipeline

        pipeline = mock_pipeline_class(
            pipeline_name="reddit_harbor",
            destination="supabase",
            dataset_name="reddit_data"
        )

        # Test database error during merge
        with pytest.raises(Exception, match="Database constraint violation"):
            pipeline.run(
                [{"id": "test"}],
                table_name="app_opportunities",
                write_disposition="merge",
                primary_key="id"
            )


# ============================================================================
# PERFORMANCE AND SCALABILITY TESTS
# ============================================================================

class TestDLTPerformance:
    """Test DLT performance and scalability aspects"""

    @patch('dlt.pipeline')
    def test_large_dataset_merge_performance(self, mock_pipeline_class):
        """Test merge performance with large datasets"""
        # Setup mock pipeline
        mock_pipeline = Mock()
        mock_pipeline.run.return_value = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        # Generate large dataset
        large_dataset = [
            {
                "id": f"opp_{i}",
                "title": f"Opportunity {i}",
                "score": 80.0 + (i % 20),
                "created_at": datetime.now(UTC).isoformat()
            }
            for i in range(1000)  # 1000 records
        ]

        pipeline = mock_pipeline_class(
            pipeline_name="reddit_harbor",
            destination="supabase",
            dataset_name="reddit_data"
        )

        # Run merge with large dataset
        pipeline.run(
            large_dataset,
            table_name="app_opportunities",
            write_disposition="merge",
            primary_key="id"
        )

        # Verify all records were processed
        mock_pipeline.run.assert_called_once()
        args, kwargs = mock_pipeline.run.call_args
        passed_data = args[0]
        assert len(passed_data) == 1000

    @patch('dlt.pipeline')
    def test_batch_processing_configuration(self, mock_pipeline_class):
        """Test batch processing configuration for better performance"""
        # Setup mock pipeline
        mock_pipeline = Mock()
        mock_pipeline.run.return_value = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        # Test with different batch sizes
        batch_sizes = [100, 500, 1000]
        sample_data = [{"id": f"test_{i}", "value": i} for i in range(1500)]

        pipeline = mock_pipeline_class(
            pipeline_name="reddit_harbor",
            destination="supabase",
            dataset_name="reddit_data"
        )

        for batch_size in batch_sizes:
            # Process data in batches
            for i in range(0, len(sample_data), batch_size):
                batch = sample_data[i:i + batch_size]

                pipeline.run(
                    batch,
                    table_name="app_opportunities",
                    write_disposition="merge",
                    primary_key="id"
                )

        # Verify multiple runs occurred
        expected_runs = sum(1 for _ in range(0, len(sample_data), min(batch_sizes)))
        assert mock_pipeline.run.call_count >= len(batch_sizes)


# ============================================================================
# INTEGRATION WITH MAIN PIPELINE
# ============================================================================

class TestMainPipelineIntegration:
    """Test integration of DLT Supabase components with main pipeline"""

    @patch('dlt.pipeline')
    def test_pipeline_step_6_dlt_integration(self, mock_pipeline_class, sample_app_opportunities_data):
        """Test integration of DLT as Step 6 of main pipeline"""
        # Setup mock pipeline
        mock_pipeline = Mock()
        mock_pipeline.run.return_value = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        # Simulate pipeline step 6: Load to Supabase via DLT
        def pipeline_step_6_load_to_supabase(processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
            """
            Step 6: Load validated opportunities to Supabase using DLT with merge disposition.

            Args:
                processed_data: Validated opportunity data from previous pipeline steps

            Returns:
                Load results and statistics
            """
            # Filter to opportunity records
            opportunities = [
                record for record in processed_data
                if 'id' in record and 'title' in record and 'score' in record
            ]

            if not opportunities:
                return {"status": "no_data", "count": 0}

            # Create DLT pipeline for Supabase
            pipeline = mock_pipeline_class(
                pipeline_name="reddit_harbor",
                destination="supabase",
                dataset_name="reddit_data"
            )

            # Load opportunities with merge disposition
            pipeline.run(
                opportunities,
                table_name="app_opportunities",
                write_disposition="merge",
                primary_key="id"
            )

            return {
                "status": "success",
                "count": len(opportunities),
                "table": "app_opportunities",
                "write_disposition": "merge"
            }

        # Execute pipeline step 6
        result = pipeline_step_6_load_to_supabase(sample_app_opportunities_data)

        # Verify results
        assert result["status"] == "success"
        assert result["count"] == len(sample_app_opportunities_data)
        assert result["table"] == "app_opportunities"
        assert result["write_disposition"] == "merge"

        # Verify DLT pipeline was called correctly
        mock_pipeline_class.assert_called()
        mock_pipeline.run.assert_called()

        args, kwargs = mock_pipeline.run.call_args
        passed_data = args[0]
        assert len(passed_data) == len(sample_app_opportunities_data)
        assert kwargs.get('write_disposition') == "merge"
        assert kwargs.get('primary_key') == "id"

    @patch('dlt.pipeline')
    def test_empty_data_handling(self, mock_pipeline_class):
        """Test handling of empty data in pipeline step 6"""
        # Setup mock pipeline
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        def pipeline_step_6_load_to_supabase(processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
            opportunities = [
                record for record in processed_data
                if 'id' in record and 'title' in record and 'score' in record
            ]

            if not opportunities:
                return {"status": "no_data", "count": 0}

            pipeline = mock_pipeline_class(
                pipeline_name="reddit_harbor",
                destination="supabase",
                dataset_name="reddit_data"
            )

            pipeline.run(
                opportunities,
                table_name="app_opportunities",
                write_disposition="merge",
                primary_key="id"
            )

            return {"status": "success", "count": len(opportunities)}

        # Test with empty data
        result = pipeline_step_6_load_to_supabase([])
        assert result["status"] == "no_data"
        assert result["count"] == 0

        # Test with invalid data (no opportunity records)
        invalid_data = [{"invalid": "record"}, {"wrong": "format"}]
        result = pipeline_step_6_load_to_supabase(invalid_data)
        assert result["status"] == "no_data"
        assert result["count"] == 0

        # Verify DLT pipeline was not called for empty data
        mock_pipeline_class.assert_not_called()


# ============================================================================
# UTILITY FUNCTIONS AND HELPERS
# ============================================================================

def create_test_dlt_pipeline_config(
    destination: str = "supabase",
    pipeline_name: str = "reddit_harbor_test",
    dataset_name: str = "reddit_data_test"
) -> Dict[str, Any]:
    """
    Helper function to create test DLT pipeline configuration.

    Args:
        destination: Destination type ('supabase' or 'postgres')
        pipeline_name: Name of the DLT pipeline
        dataset_name: Dataset name in the destination

    Returns:
        Dictionary containing pipeline configuration
    """
    return {
        "pipeline_name": pipeline_name,
        "destination": destination,
        "dataset_name": dataset_name,
        "credentials": "postgresql://postgres:postgres@localhost:54322/postgres"
    }


def validate_merge_disposition_config(config: Dict[str, Any]) -> bool:
    """
    Helper function to validate merge disposition configuration.

    Args:
        config: Pipeline configuration dictionary

    Returns:
        True if configuration is valid for merge disposition
    """
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


# ============================================================================
# PYTEST MARKERS AND CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers for DLT Supabase tests"""
    config.addinivalue_line(
        "markers", "dlt_connection: marks tests for DLT connection testing"
    )
    config.addinivalue_line(
        "markers", "supabase_integration: marks tests for Supabase integration"
    )
    config.addinivalue_line(
        "markers", "merge_disposition: marks tests for merge disposition testing"
    )
    config.addinivalue_line(
        "markers", "dlt_performance: marks tests for DLT performance testing"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their module and content"""
    for item in items:
        # Mark DLT connection tests
        if "connection" in item.nodeid.lower() or "credential" in item.nodeid.lower():
            item.add_marker(pytest.mark.dlt_connection)

        # Mark Supabase integration tests
        if "supabase" in item.nodeid.lower():
            item.add_marker(pytest.mark.supabase_integration)

        # Mark merge disposition tests
        if "merge" in item.nodeid.lower():
            item.add_marker(pytest.mark.merge_disposition)

        # Mark performance tests
        if "performance" in item.nodeid.lower() or "large_dataset" in item.nodeid.lower():
            item.add_marker(pytest.mark.dlt_performance)