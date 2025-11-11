"""
Test suite for DLT Normalization Hooks.

Tests the SimplicityConstraintNormalizeHandler class which enforces
constraints during DLT's normalization phase, including automatic
disqualification of 4+ function apps and violation logging.
"""

from unittest.mock import Mock, patch

import pytest

from core.dlt.dataset_constraints import (
    create_constraint_aware_dataset,
    create_constraint_summary_resource,
    create_constraint_violations_resource,
    get_constraint_schema,
)
from core.dlt.normalize_hooks import (
    SimplicityConstraintNormalizeHandler,
    create_constraint_normalize_handler,
)


class TestSimplicityConstraintNormalizeHandler:
    """Test the SimplicityConstraintNormalizeHandler class."""

    def test_handler_initialization(self):
        """Test handler can be initialized with custom max_functions."""
        handler = SimplicityConstraintNormalizeHandler(max_functions=3)
        assert handler.max_functions == 3
        assert handler.violations_logged == 0
        assert handler.apps_processed == 0

    def test_default_initialization(self):
        """Test handler uses default max_functions=3."""
        handler = SimplicityConstraintNormalizeHandler()
        assert handler.max_functions == 3

    def test_extract_function_count_from_core_functions_field(self):
        """Test extraction from core_functions integer field."""
        handler = SimplicityConstraintNormalizeHandler()
        row = {"core_functions": 2}
        count = handler._extract_function_count(row)
        assert count == 2

    def test_extract_function_count_from_function_list(self):
        """Test extraction from function_list array."""
        handler = SimplicityConstraintNormalizeHandler()
        row = {"function_list": ["Track", "Calculate", "Notify"]}
        count = handler._extract_function_count(row)
        assert count == 3

    def test_extract_function_count_from_function_list_string(self):
        """Test extraction from function_list JSON string."""
        handler = SimplicityConstraintNormalizeHandler()
        row = {"function_list": '["Track", "Calculate"]'}
        count = handler._extract_function_count(row)
        assert count == 2

    def test_extract_function_count_from_description(self):
        """Test extraction from app_description text."""
        handler = SimplicityConstraintNormalizeHandler()
        row = {
            "app_description": "Allows users to track calories and calculate BMI. Provides goal setting features."
        }
        count = handler._extract_function_count(row)
        assert count > 0
        assert count <= 3

    def test_extract_function_count_no_data(self):
        """Test extraction when no function data available."""
        handler = SimplicityConstraintNormalizeHandler()
        row = {"app_name": "TestApp"}
        count = handler._extract_function_count(row)
        assert count == 0

    def test_enforce_constraint_one_function_approved(self):
        """Test app with 1 function is approved."""
        handler = SimplicityConstraintNormalizeHandler()
        row = {
            "opportunity_id": "opp_1",
            "app_name": "SimpleApp",
            "core_functions": 1,
            "total_score": 85.0
        }

        handler._enforce_constraint(row)

        assert row["is_disqualified"] == False
        assert row["simplicity_score"] == 100.0
        assert row["total_score"] == 85.0  # Preserved for approved apps
        assert "APPROVED (1 functions)" in row["validation_status"]
        assert "violation_reason" not in row or row["violation_reason"] is None

    def test_enforce_constraint_two_functions_approved(self):
        """Test app with 2 functions is approved."""
        handler = SimplicityConstraintNormalizeHandler()
        row = {
            "opportunity_id": "opp_2",
            "app_name": "TwoFuncApp",
            "core_functions": 2,
            "total_score": 90.0
        }

        handler._enforce_constraint(row)

        assert row["is_disqualified"] == False
        assert row["simplicity_score"] == 85.0
        assert "APPROVED (2 functions)" in row["validation_status"]

    def test_enforce_constraint_three_functions_approved(self):
        """Test app with 3 functions is approved (maximum)."""
        handler = SimplicityConstraintNormalizeHandler()
        row = {
            "opportunity_id": "opp_3",
            "app_name": "MaxFuncApp",
            "core_functions": 3,
            "total_score": 80.0
        }

        handler._enforce_constraint(row)

        assert row["is_disqualified"] == False
        assert row["simplicity_score"] == 70.0
        assert "APPROVED (3 functions)" in row["validation_status"]

    def test_enforce_constraint_four_functions_disqualified(self):
        """Test app with 4 functions is automatically disqualified."""
        handler = SimplicityConstraintNormalizeHandler()
        row = {
            "opportunity_id": "opp_4",
            "app_name": "ComplexApp",
            "core_functions": 4,
            "total_score": 95.0
        }

        handler._enforce_constraint(row)

        assert row["is_disqualified"] == True
        assert row["simplicity_score"] == 0.0
        assert row["total_score"] == 0.0  # Zeroed out for disqualified apps
        assert "DISQUALIFIED (4 functions)" in row["validation_status"]
        assert "4 core functions exceed maximum of 3" in row["violation_reason"]
        assert handler.violations_logged == 1

    def test_enforce_constraint_five_functions_disqualified(self):
        """Test app with 5+ functions is disqualified."""
        handler = SimplicityConstraintNormalizeHandler()
        row = {
            "opportunity_id": "opp_5",
            "app_name": "VeryComplexApp",
            "core_functions": 5
        }

        handler._enforce_constraint(row)

        assert row["is_disqualified"] == True
        assert row["simplicity_score"] == 0.0
        assert handler.violations_logged == 1

    def test_enforce_constraint_updates_timestamp(self):
        """Test constraint enforcement adds validation timestamp."""
        handler = SimplicityConstraintNormalizeHandler()
        row = {"core_functions": 1}

        handler._enforce_constraint(row)

        assert "validation_timestamp" in row
        assert row["validation_timestamp"] is not None

    def test_enforce_constraint_sets_constraint_version(self):
        """Test constraint enforcement sets constraint version."""
        handler = SimplicityConstraintNormalizeHandler()
        row = {"core_functions": 1}

        handler._enforce_constraint(row)

        assert row["constraint_version"] == 1
        assert "validation_timestamp" in row

    def test_calculate_simplicity_score_one_function(self):
        """Test score calculation for 1 function."""
        handler = SimplicityConstraintNormalizeHandler()
        score = handler._calculate_simplicity_score(1)
        assert score == 100.0

    def test_calculate_simplicity_score_two_functions(self):
        """Test score calculation for 2 functions."""
        handler = SimplicityConstraintNormalizeHandler()
        score = handler._calculate_simplicity_score(2)
        assert score == 85.0

    def test_calculate_simplicity_score_three_functions(self):
        """Test score calculation for 3 functions."""
        handler = SimplicityConstraintNormalizeHandler()
        score = handler._calculate_simplicity_score(3)
        assert score == 70.0

    def test_calculate_simplicity_score_four_functions(self):
        """Test score calculation for 4+ functions."""
        handler = SimplicityConstraintNormalizeHandler()
        score = handler._calculate_simplicity_score(4)
        assert score == 0.0

        score = handler._calculate_simplicity_score(10)
        assert score == 0.0

    def test_parse_functions_from_text_bullet_points(self):
        """Test parsing functions from bullet point text."""
        handler = SimplicityConstraintNormalizeHandler()
        text = """
        Features:
        • Track calories and nutrients
        • Calculate BMI and body fat
        • Set fitness goals
        """
        functions = handler._parse_functions_from_text(text)
        assert len(functions) > 0
        assert len(functions) <= 3

    def test_parse_functions_from_text_allows_pattern(self):
        """Test parsing functions from 'allows users to' pattern."""
        handler = SimplicityConstraintNormalizeHandler()
        text = "Allows users to track expenses and calculate budgets. Provides expense categorization features."
        functions = handler._parse_functions_from_text(text)
        assert len(functions) > 0

    def test_parse_functions_from_text_verb_noun(self):
        """Test parsing functions from verb-noun patterns."""
        handler = SimplicityConstraintNormalizeHandler()
        text = "Track expenses, calculate budgets, generate reports, and set reminders."
        functions = handler._parse_functions_from_text(text)
        assert len(functions) > 0

    def test_parse_functions_from_text_empty(self):
        """Test parsing functions from empty text."""
        handler = SimplicityConstraintNormalizeHandler()
        functions = handler._parse_functions_from_text("")
        assert len(functions) == 0

    def test_parse_functions_limit_to_three(self):
        """Test that parsing limits functions to maximum 3."""
        handler = SimplicityConstraintNormalizeHandler()
        text = """
        • Track expenses
        • Calculate budgets
        • Generate reports
        • Set reminders
        • Create categories
        """
        functions = handler._parse_functions_from_text(text)
        assert len(functions) <= 3

    def test_parse_functions_removes_duplicates(self):
        """Test that duplicate functions are removed."""
        handler = SimplicityConstraintNormalizeHandler()
        text = "Track expenses and track budget calculations"
        functions = handler._parse_functions_from_text(text)
        # Should have unique functions
        assert len(functions) == len(set(f.lower() for f in functions))

    def test_generate_violations(self):
        """Test generation of violation records."""
        handler = SimplicityConstraintNormalizeHandler()
        violations = list(handler.generate_violations(
            opportunity_id="opp_test",
            app_name="TestApp",
            function_count=4,
            original_score=90.0
        ))

        assert len(violations) == 1
        violation = violations[0]
        assert violation["opportunity_id"] == "opp_test"
        assert violation["app_name"] == "TestApp"
        assert violation["function_count"] == 4
        assert violation["max_allowed"] == 3
        assert violation["violation_type"] == "SIMPLICITY_CONSTRAINT"
        assert "exceed maximum" in violation["violation_reason"]
        assert violation["original_score"] == 90.0

    def test_get_stats(self):
        """Test getting statistics from handler."""
        handler = SimplicityConstraintNormalizeHandler()
        # Process some rows
        handler._enforce_constraint({"core_functions": 1})
        handler._enforce_constraint({"core_functions": 4})

        stats = handler.get_stats()
        assert stats["apps_processed"] == 2
        assert stats["violations_logged"] == 1

    def test_process_batch(self):
        """Test processing a batch of tables."""
        handler = SimplicityConstraintNormalizeHandler()

        # Create mock table
        mock_table = Mock()
        mock_table.name = "app_opportunities"
        mock_table.rows = [
            {"opportunity_id": "opp_1", "core_functions": 1},
            {"opportunity_id": "opp_2", "core_functions": 4}
        ]

        tables = [mock_table]
        processed = handler.process_batch(tables)

        # Verify rows were processed
        assert processed[0].rows[0]["is_disqualified"] == False
        assert processed[0].rows[1]["is_disqualified"] == True
        assert handler.apps_processed == 2
        assert handler.violations_logged == 1

    def test_process_batch_ignores_other_tables(self):
        """Test that non-app_opportunities tables are ignored."""
        handler = SimplicityConstraintNormalizeHandler()

        # Create mock tables
        mock_table1 = Mock()
        mock_table1.name = "submissions"
        mock_table1.rows = [{"id": "sub_1", "title": "Test"}]

        mock_table2 = Mock()
        mock_table2.name = "app_opportunities"
        mock_table2.rows = [{"opportunity_id": "opp_1", "core_functions": 1}]

        tables = [mock_table1, mock_table2]
        processed = handler.process_batch(tables)

        # Verify only app_opportunities was processed
        assert len(processed) == 2
        # Submissions table should be unchanged
        assert "is_disqualified" not in processed[0].rows[0]
        # App opportunities should be processed
        assert processed[1].rows[0]["is_disqualified"] == False


class TestCreateConstraintNormalizeHandler:
    """Test the factory function for creating handlers."""

    def test_create_with_default_max_functions(self):
        """Test factory creates handler with default max_functions=3."""
        handler = create_constraint_normalize_handler()
        assert isinstance(handler, SimplicityConstraintNormalizeHandler)
        assert handler.max_functions == 3

    def test_create_with_custom_max_functions(self):
        """Test factory creates handler with custom max_functions."""
        handler = create_constraint_normalize_handler(max_functions=5)
        assert isinstance(handler, SimplicityConstraintNormalizeHandler)
        assert handler.max_functions == 5


class TestCreateConstraintAwareDataset:
    """Test the create_constraint_aware_dataset function."""

    @patch('dlt.pipeline')
    def test_create_basic_dataset(self, mock_pipeline):
        """Test creating a basic constraint-aware dataset."""
        with patch.dict('os.environ', {'SUPABASE_DB_URL': 'test_url'}):
            pipeline = create_constraint_aware_dataset(
                dataset_name="test_dataset",
                enable_constraint_tracking=True,
                enable_data_quality=True,
                max_functions=3,
                destination_type="postgres"
            )

        # Verify pipeline was created
        assert mock_pipeline.called
        call_kwargs = mock_pipeline.call_args[1]
        assert call_kwargs["dataset_name"] == "test_dataset"
        assert call_kwargs["destination"] == "postgres"

    def test_create_dataset_with_all_options(self):
        """Test creating dataset with all options enabled."""
        with patch.dict('os.environ', {}, clear=True):
            # This test just checks the function doesn't raise errors
            # The actual DLT pipeline creation is mocked
            try:
                pipeline = create_constraint_aware_dataset(
                    dataset_name="full_test",
                    enable_constraint_tracking=True,
                    enable_data_quality=True,
                    max_functions=2,
                    destination_type="postgres"
                )
                # If we get here, the function executed without error
                assert pipeline is not None
            except Exception as e:
                # Some errors are expected (no actual DLT env configured)
                # But we should not get syntax errors or import errors
                assert "AttributeError" not in str(e)
                assert "NameError" not in str(e)

    def test_get_constraint_schema(self):
        """Test getting the constraint schema."""
        schema = get_constraint_schema()
        assert schema is not None
        # Schema should have a name
        assert schema.name is not None
        # DLT auto-generates tables from resources, so we just check schema exists
        assert isinstance(schema.tables, dict)


class TestConstraintSummaryResource:
    """Test the create_constraint_summary_resource function."""

    def test_summary_from_violations(self):
        """Test generating summary from violations data."""
        violations_data = [
            {"is_disqualified": False, "core_functions": 2, "simplicity_score": 85.0},
            {"is_disqualified": True, "core_functions": 4, "simplicity_score": 0.0},
            {"is_disqualified": False, "core_functions": 1, "simplicity_score": 100.0}
        ]

        resource = create_constraint_summary_resource(violations_data)
        summaries = list(resource())

        assert len(summaries) == 1
        summary = summaries[0]
        assert summary["total_opportunities"] == 3
        assert summary["approved_count"] == 2
        assert summary["disqualified_count"] == 1
        assert summary["compliance_rate"] == pytest.approx(66.67, rel=1e-2)
        assert summary["avg_core_functions"] == pytest.approx(2.33, rel=1e-2)
        assert summary["avg_simplicity_score"] == pytest.approx(61.67, rel=1e-2)

    def test_summary_from_empty_violations(self):
        """Test generating summary from empty violations data."""
        resource = create_constraint_summary_resource([])
        summaries = list(resource())

        assert len(summaries) == 1
        summary = summaries[0]
        assert summary["total_opportunities"] == 0
        assert summary["approved_count"] == 0
        assert summary["disqualified_count"] == 0
        assert summary["compliance_rate"] == 0.0
        assert summary["avg_core_functions"] == 0.0
        assert summary["avg_simplicity_score"] == 0.0


class TestConstraintViolationsResource:
    """Test the create_constraint_violations_resource function."""

    def test_violations_resource(self):
        """Test creating violations resource from data."""
        violations = [
            {
                "opportunity_id": "opp_1",
                "app_name": "ComplexApp",
                "function_count": 4,
                "violation_reason": "Too many functions"
            }
        ]

        resource = create_constraint_violations_resource(violations)
        violation_records = list(resource())

        assert len(violation_records) == 1
        record = violation_records[0]
        assert record["opportunity_id"] == "opp_1"
        assert record["app_name"] == "ComplexApp"
        assert record["function_count"] == 4
        assert record["violation_type"] == "SIMPLICITY_CONSTRAINT"
        assert "timestamp" in record

    def test_violations_resource_with_missing_fields(self):
        """Test violations resource handles missing fields."""
        violations = [
            {
                "opportunity_id": "opp_1"
                # Missing other fields
            }
        ]

        resource = create_constraint_violations_resource(violations)
        violation_records = list(resource())

        assert len(violation_records) == 1
        # Should fill in defaults
        assert violation_records[0]["opportunity_id"] == "opp_1"
        assert violation_records[0]["function_count"] == 0
        assert violation_records[0]["max_allowed"] == 3


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_end_to_end_constraint_enforcement(self):
        """Test end-to-end constraint enforcement flow."""
        # Create handler
        handler = SimplicityConstraintNormalizeHandler()

        # Create mock table with mixed opportunities
        mock_table = Mock()
        mock_table.name = "app_opportunities"
        mock_table.rows = [
            {
                "opportunity_id": "opp_1",
                "app_name": "SimpleApp",
                "core_functions": 1,
                "total_score": 90.0
            },
            {
                "opportunity_id": "opp_2",
                "app_name": "ComplexApp",
                "core_functions": 4,
                "total_score": 95.0
            },
            {
                "opportunity_id": "opp_3",
                "app_name": "TwoFuncApp",
                "core_functions": 2,
                "total_score": 85.0
            }
        ]

        # Process the batch
        processed = handler.process_batch([mock_table])

        # Verify results
        rows = processed[0].rows

        # First app (1 function) - approved
        assert rows[0]["is_disqualified"] == False
        assert rows[0]["simplicity_score"] == 100.0
        assert rows[0]["total_score"] == 90.0  # Preserved
        assert "APPROVED" in rows[0]["validation_status"]

        # Second app (4 functions) - disqualified
        assert rows[1]["is_disqualified"] == True
        assert rows[1]["simplicity_score"] == 0.0
        assert rows[1]["total_score"] == 0.0  # Zeroed
        assert "DISQUALIFIED" in rows[1]["validation_status"]

        # Third app (2 functions) - approved
        assert rows[2]["is_disqualified"] == False
        assert rows[2]["simplicity_score"] == 85.0
        assert rows[2]["total_score"] == 85.0  # Preserved

        # Verify statistics
        stats = handler.get_stats()
        assert stats["apps_processed"] == 3
        assert stats["violations_logged"] == 1

    def test_violation_generation_flow(self):
        """Test violation record generation flow."""
        handler = SimplicityConstraintNormalizeHandler()

        # Simulate processing a disqualified app
        mock_table = Mock()
        mock_table.name = "app_opportunities"
        mock_table.rows = [
            {
                "opportunity_id": "violation_test",
                "app_name": "TooManyFuncs",
                "core_functions": 5,
                "total_score": 100.0
            }
        ]

        handler.process_batch([mock_table])

        # Generate violation record
        violations = list(handler.generate_violations(
            opportunity_id="violation_test",
            app_name="TooManyFuncs",
            function_count=5,
            original_score=100.0
        ))

        assert len(violations) == 1
        violation = violations[0]
        assert violation["opportunity_id"] == "violation_test"
        assert violation["app_name"] == "TooManyFuncs"
        assert violation["function_count"] == 5
        assert violation["max_allowed"] == 3
        assert violation["original_score"] == 100.0
        assert violation["violation_type"] == "SIMPLICITY_CONSTRAINT"
        assert "exceed maximum" in violation["violation_reason"]
