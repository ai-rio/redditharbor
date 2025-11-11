"""
Test suite for DLT CLI Commands.

Tests the Click-based CLI for DLT-native constraint management,
including command parsing, configuration loading, error handling,
and integration with Phase 1 & 2 components.
"""

import json
import os
import tempfile
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

# Import the CLI commands
from dlt_cli import cli


class TestCLI:
    """Test the main CLI interface."""

    def test_cli_help(self):
        """Test that CLI displays help correctly."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "DLT-Native Simplicity Constraint Management CLI" in result.output
        assert "validate-constraints" in result.output
        assert "show-constraint-schema" in result.output
        assert "run-pipeline" in result.output

    def test_cli_version(self):
        """Test that CLI displays version correctly."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "DLT Constraint CLI" in result.output
        assert "1.0.0" in result.output


class TestValidateConstraintsCommand:
    """Test the validate-constraints command."""

    def test_validate_constraints_with_valid_data(self):
        """Test validating opportunities with 1-3 functions (all pass)."""
        runner = CliRunner()

        # Create test data with valid opportunities
        opportunities = [
            {
                "app_name": "SimpleApp1",
                "app_description": "An app with one core function",
                "function_list": ["track_data"]
            },
            {
                "app_name": "SimpleApp2",
                "app_description": "An app with two functions",
                "function_list": ["track_data", "analyze_data"]
            },
            {
                "app_name": "SimpleApp3",
                "app_description": "An app with three functions",
                "function_list": ["track_data", "analyze_data", "report_data"]
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(opportunities, f)
            temp_file = f.name

        try:
            result = runner.invoke(cli, ["validate-constraints", "--file", temp_file])
            assert result.exit_code == 0
            assert "VALIDATION SUMMARY" in result.output
            assert "Total opportunities: 3" in result.output
            assert "Approved: 3" in result.output
            assert "Disqualified: 0" in result.output
            assert "Compliance rate: 100.0%" in result.output
        finally:
            os.unlink(temp_file)

    def test_validate_constraints_with_violations(self):
        """Test validating opportunities with 4+ functions (some fail)."""
        runner = CliRunner()

        # Create test data with violations
        opportunities = [
            {
                "app_name": "ValidApp1",
                "function_list": ["track_data", "analyze_data"]
            },
            {
                "app_name": "InvalidApp1",
                "function_list": ["func1", "func2", "func3", "func4"]
            },
            {
                "app_name": "InvalidApp2",
                "function_list": ["func1", "func2", "func3", "func4", "func5"]
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(opportunities, f)
            temp_file = f.name

        try:
            result = runner.invoke(cli, ["validate-constraints", "--file", temp_file])
            assert result.exit_code == 0
            assert "VALIDATION SUMMARY" in result.output
            assert "Total opportunities: 3" in result.output
            assert "Approved: 1" in result.output
            assert "Disqualified: 2" in result.output
            assert "VIOLATIONS DETECTED" in result.output
            assert "InvalidApp1" in result.output
            assert "InvalidApp2" in result.output
        finally:
            os.unlink(temp_file)

    def test_validate_constraints_with_output_file(self):
        """Test validating with output file specified."""
        runner = CliRunner()

        opportunities = [
            {
                "app_name": "TestApp",
                "function_list": ["func1", "func2", "func3", "func4"]
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(opportunities, f)
            temp_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            result = runner.invoke(cli, [
                "validate-constraints",
                "--file", temp_file,
                "--output", output_file
            ])
            assert result.exit_code == 0
            assert f"Validated opportunities saved to: {output_file}" in result.output

            # Verify output file was created and contains validated data
            with open(output_file) as f:
                validated = json.load(f)
                assert len(validated) == 1
                assert validated[0]["app_name"] == "TestApp"
                assert validated[0]["is_disqualified"] == True
                assert validated[0]["core_functions"] == 4
        finally:
            os.unlink(temp_file)
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_validate_constraints_custom_max_functions(self):
        """Test validating with custom max functions setting."""
        runner = CliRunner()

        opportunities = [
            {
                "app_name": "TestApp",
                "function_list": ["func1", "func2", "func3"]
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(opportunities, f)
            temp_file = f.name

        try:
            # With max_functions=5, this should pass
            result = runner.invoke(cli, [
                "validate-constraints",
                "--file", temp_file,
                "--max-functions", "5"
            ])
            assert result.exit_code == 0
            assert "Approved: 1" in result.output
            assert "Disqualified: 0" in result.output
        finally:
            os.unlink(temp_file)

    def test_validate_constraints_with_fail_on_violation(self):
        """Test that --fail-on-violation exits with error code."""
        runner = CliRunner()

        opportunities = [
            {
                "app_name": "InvalidApp",
                "function_list": ["func1", "func2", "func3", "func4"]
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(opportunities, f)
            temp_file = f.name

        try:
            result = runner.invoke(cli, [
                "validate-constraints",
                "--file", temp_file,
                "--fail-on-violation"
            ])
            assert result.exit_code == 1
            assert "Violations found!" in result.output
        finally:
            os.unlink(temp_file)

    def test_validate_constraints_file_not_found(self):
        """Test error handling for non-existent file."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "validate-constraints",
            "--file", "/nonexistent/file.json"
        ])
        # Click uses exit code 2 for command-line errors
        assert result.exit_code == 2
        # Click provides a default error message
        assert "does not exist" in result.output

    def test_validate_constraints_invalid_json(self):
        """Test error handling for invalid JSON."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json ")
            temp_file = f.name

        try:
            result = runner.invoke(cli, [
                "validate-constraints",
                "--file", temp_file
            ])
            assert result.exit_code == 1
            assert "Error: Invalid JSON" in result.output
        finally:
            os.unlink(temp_file)

    def test_validate_constraints_not_list(self):
        """Test error handling when data is not a list."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"not": "a list"}, f)
            temp_file = f.name

        try:
            result = runner.invoke(cli, [
                "validate-constraints",
                "--file", temp_file
            ])
            assert result.exit_code == 1
            assert "Data must be a list of opportunities" in result.output
        finally:
            os.unlink(temp_file)

    def test_validate_constraints_verbose(self):
        """Test verbose output flag."""
        runner = CliRunner()

        opportunities = [
            {"app_name": "TestApp", "function_list": ["func1"]}
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(opportunities, f)
            temp_file = f.name

        try:
            result = runner.invoke(cli, [
                "--verbose",
                "validate-constraints",
                "--file", temp_file
            ])
            assert result.exit_code == 0
            # Verbose mode should show loading messages
            assert "Loaded" in result.output
        finally:
            os.unlink(temp_file)


class TestShowConstraintSchemaCommand:
    """Test the show-constraint-schema command."""

    def test_show_schema_table_format(self):
        """Test showing schema in table format."""
        runner = CliRunner()
        result = runner.invoke(cli, ["show-constraint-schema", "--format", "table"])
        assert result.exit_code == 0
        assert "DLT CONSTRAINT-AWARE SCHEMA" in result.output
        assert "app_opportunities" in result.output
        assert "constraint_violations" in result.output
        assert "core_functions" in result.output
        assert "simplicity_score" in result.output
        assert "is_disqualified" in result.output

    def test_show_schema_json_format(self):
        """Test showing schema in JSON format."""
        runner = CliRunner()
        result = runner.invoke(cli, ["show-constraint-schema", "--format", "json"])
        assert result.exit_code == 0

        # Parse JSON output
        schema_data = json.loads(result.output)
        assert "schema_name" in schema_data
        assert "tables" in schema_data
        assert "constraint_rules" in schema_data
        assert schema_data["schema_name"] == "reddit_harbor"

    def test_show_schema_output_to_file(self):
        """Test saving schema to file."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            result = runner.invoke(cli, [
                "show-constraint-schema",
                "--format", "json",
                "--output", output_file
            ])
            assert result.exit_code == 0
            assert f"Schema saved to: {output_file}" in result.output

            # Verify file was created
            with open(output_file) as f:
                schema_data = json.load(f)
                assert "schema_name" in schema_data
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)


class TestRunPipelineCommand:
    """Test the run-pipeline command."""

    @patch("dlt_cli.create_test_dataset")
    def test_run_pipeline_with_test_data(self, mock_create_dataset):
        """Test running pipeline with test data."""
        runner = CliRunner()

        # Create mock pipeline
        mock_pipeline = Mock()
        mock_pipeline.pipeline_name = "test_pipeline"
        mock_pipeline.run.return_value = Mock(asdict=lambda: {"load_id": "test_load_123"})
        # Add schema attribute for the check
        mock_schema = Mock()
        mock_pipeline.schema = mock_schema
        mock_create_dataset.return_value = mock_pipeline

        opportunities = [
            {
                "app_name": "TestApp",
                "app_description": "A test app",
                "function_list": ["func1", "func2"]
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(opportunities, f)
            temp_file = f.name

        try:
            result = runner.invoke(cli, [
                "run-pipeline",
                "--source", temp_file,
                "--destination", "postgres",
                "--dataset-name", "test_dataset",
                "--test"
            ])
            assert result.exit_code == 0
            assert "PIPELINE COMPLETED" in result.output
            assert "test_pipeline" in result.output
            assert "test_dataset" in result.output
            assert mock_pipeline.run.called
        finally:
            os.unlink(temp_file)

    @patch("dlt_cli.create_production_dataset")
    def test_run_pipeline_production_mode(self, mock_create_dataset):
        """Test running pipeline in production mode."""
        runner = CliRunner()

        mock_pipeline = Mock()
        mock_pipeline.pipeline_name = "prod_pipeline"
        mock_pipeline.run.return_value = Mock(asdict=lambda: {"load_id": "prod_load_456"})
        # Add schema attribute
        mock_schema = Mock()
        mock_pipeline.schema = mock_schema
        mock_create_dataset.return_value = mock_pipeline

        opportunities = [
            {
                "app_name": "ProdApp",
                "function_list": ["func1"]
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(opportunities, f)
            temp_file = f.name

        try:
            result = runner.invoke(cli, [
                "run-pipeline",
                "--source", temp_file,
                "--production"
            ])
            assert result.exit_code == 0
            assert "PIPELINE COMPLETED" in result.output
        finally:
            os.unlink(temp_file)

    def test_run_pipeline_file_not_found(self):
        """Test error handling for non-existent source file."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "run-pipeline",
            "--source", "/nonexistent/file.json"
        ])
        # Click uses exit code 2 for command-line errors
        assert result.exit_code == 2
        # Click provides a default error message
        assert "does not exist" in result.output


class TestTestConstraintCommand:
    """Test the test-constraint command."""

    def test_test_constraint_default_options(self):
        """Test constraint test with default options."""
        runner = CliRunner()
        result = runner.invoke(cli, ["test-constraint"])
        assert result.exit_code == 0
        assert "CONSTRAINT TEST RESULTS" in result.output
        assert "Total opportunities tested: 5" in result.output
        assert "Approved:" in result.output
        assert "Disqualified:" in result.output
        assert "Individual Results:" in result.output

    def test_test_constraint_custom_sample_size(self):
        """Test constraint test with custom sample size."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "test-constraint",
            "--sample-size", "10"
        ])
        assert result.exit_code == 0
        assert "Total opportunities tested: 10" in result.output

    def test_test_constraint_with_output(self):
        """Test constraint test with output file."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            result = runner.invoke(cli, [
                "test-constraint",
                "--output", output_file
            ])
            assert result.exit_code == 0
            assert f"Test results saved to: {output_file}" in result.output

            # Verify file was created and contains valid data
            with open(output_file) as f:
                test_data = json.load(f)
                assert len(test_data) == 5
                assert "app_name" in test_data[0]
                assert "is_disqualified" in test_data[0]
                assert "validation_status" in test_data[0]
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)


class TestCheckDatabaseCommand:
    """Test the check-database command."""

    @patch("dlt_cli.create_constraint_aware_dataset")
    def test_check_database_postgres(self, mock_create_dataset):
        """Test checking PostgreSQL database connectivity."""
        runner = CliRunner()

        mock_pipeline = Mock()
        mock_pipeline.pipeline_name = "test_pipeline"
        mock_create_dataset.return_value = mock_pipeline

        result = runner.invoke(cli, [
            "check-database",
            "--destination", "postgres",
            "--dataset-name", "test_dataset"
        ])
        assert result.exit_code == 0
        assert "DATABASE CHECK RESULTS" in result.output
        assert "Database type: postgres" in result.output
        assert "Dataset name: test_dataset" in result.output
        assert "✓ Database accessible" in result.output
        assert "app_opportunities" in result.output
        assert "constraint_violations" in result.output
        assert "core_functions" in result.output

    @patch("dlt_cli.dlt.pipeline")
    def test_check_database_with_error(self, mock_pipeline):
        """Test error handling for database check."""
        runner = CliRunner()

        # Simulate database connection error
        mock_pipeline.side_effect = Exception("Connection failed")

        result = runner.invoke(cli, ["check-database"])
        assert result.exit_code == 1
        assert "Error: Cannot connect to database" in result.output


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def test_full_workflow_validate_and_test(self):
        """Test full workflow: validate constraints then test."""
        runner = CliRunner()

        # Create test data
        opportunities = [
            {
                "app_name": "ValidApp1",
                "function_list": ["track"]
            },
            {
                "app_name": "ValidApp2",
                "function_list": ["track", "analyze"]
            },
            {
                "app_name": "InvalidApp1",
                "function_list": ["f1", "f2", "f3", "f4"]
            },
            {
                "app_name": "InvalidApp2",
                "function_list": ["f1", "f2", "f3", "f4", "f5"]
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(opportunities, f)
            temp_file = f.name

        try:
            # Step 1: Validate constraints
            result = runner.invoke(cli, [
                "validate-constraints",
                "--file", temp_file
            ])
            assert result.exit_code == 0
            assert "Approved: 2" in result.output
            assert "Disqualified: 2" in result.output
            assert "Compliance rate: 50.0%" in result.output

            # Step 2: Test constraint
            result = runner.invoke(cli, ["test-constraint"])
            assert result.exit_code == 0
            assert "CONSTRAINT TEST RESULTS" in result.output
        finally:
            os.unlink(temp_file)

    @patch("dlt_cli.create_constraint_aware_dataset")
    def test_schema_validation_workflow(self, mock_create_dataset):
        """Test workflow for checking schema and validating data."""
        runner = CliRunner()

        # Mock the dataset creation to avoid schema issues
        mock_pipeline = Mock()
        mock_pipeline.pipeline_name = "test_pipeline"
        mock_create_dataset.return_value = mock_pipeline

        # Step 1: Check database schema
        result = runner.invoke(cli, ["check-database"])
        assert result.exit_code == 0
        assert "DATABASE CHECK RESULTS" in result.output

        # Step 2: Show constraint schema
        result = runner.invoke(cli, ["show-constraint-schema"])
        assert result.exit_code == 0
        assert "DLT CONSTRAINT-AWARE SCHEMA" in result.output
        assert "core_functions" in result.output

    def test_verbose_output(self):
        """Test that verbose output provides additional information."""
        runner = CliRunner()

        # Test verbose mode for show-constraint-schema
        result = runner.invoke(cli, ["--verbose", "show-constraint-schema"])
        assert result.exit_code == 0

        # Test verbose mode for test-constraint
        result = runner.invoke(cli, ["--verbose", "test-constraint"])
        assert result.exit_code == 0


class TestCLIErrorHandling:
    """Test error handling in CLI commands."""

    def test_invalid_command(self):
        """Test error for invalid command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["invalid-command"])
        assert result.exit_code != 0

    def test_missing_required_option(self):
        """Test error for missing required option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["validate-constraints"])
        assert result.exit_code != 0
        assert "Error" in result.output or "Usage" in result.output

    def test_empty_file(self):
        """Test handling of empty JSON file."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([], f)
            temp_file = f.name

        try:
            result = runner.invoke(cli, [
                "validate-constraints",
                "--file", temp_file
            ])
            assert result.exit_code == 0
            assert "Total opportunities: 0" in result.output
            # Should show N/A for compliance rate
            assert "Compliance rate:" in result.output
        finally:
            os.unlink(temp_file)


class TestCLIHelpAndDocumentation:
    """Test that CLI help and documentation are clear."""

    def test_validate_constraints_help(self):
        """Test validate-constraints command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["validate-constraints", "--help"])
        assert result.exit_code == 0
        assert "Validate app opportunities" in result.output
        assert "--file" in result.output
        assert "--output" in result.output
        assert "--max-functions" in result.output
        assert "Example:" in result.output

    def test_show_constraint_schema_help(self):
        """Test show-constraint-schema command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["show-constraint-schema", "--help"])
        assert result.exit_code == 0
        assert "Display DLT schema" in result.output
        assert "--format" in result.output
        assert "table" in result.output
        assert "json" in result.output

    def test_run_pipeline_help(self):
        """Test run-pipeline command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["run-pipeline", "--help"])
        assert result.exit_code == 0
        assert "Run a full DLT pipeline" in result.output
        assert "--source" in result.output
        assert "--destination" in result.output
        assert "postgres" in result.output
        assert "--production" in result.output

    def test_main_group_help(self):
        """Test main CLI group help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "validate-constraints" in result.output
        assert "show-constraint-schema" in result.output
        assert "run-pipeline" in result.output
        assert "test-constraint" in result.output
        assert "check-database" in result.output


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
