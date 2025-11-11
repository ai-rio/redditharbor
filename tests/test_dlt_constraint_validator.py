"""
Test suite for DLT Constraint Validator.

Tests the DLT-native simplicity constraint enforcement for app opportunities,
including 1-3 core function validation, automatic disqualification for 4+ functions,
and constraint metadata tracking.
"""

from unittest.mock import Mock, patch

import dlt
import pytest

from core.dlt.constraint_validator import (
    _calculate_simplicity_score,
    _extract_core_functions,
    _parse_functions_from_text,
    app_opportunities_with_constraint,
)


class TestCalculateSimplicityScore:
    """Test the simplicity score calculation formula."""

    def test_one_function_100_points(self):
        """1 core function = 100 points (maximum score)."""
        score = _calculate_simplicity_score(1)
        assert score == 100.0
        assert isinstance(score, float)

    def test_two_functions_85_points(self):
        """2 core functions = 85 points."""
        score = _calculate_simplicity_score(2)
        assert score == 85.0

    def test_three_functions_70_points(self):
        """3 core functions = 70 points (minimum approved score)."""
        score = _calculate_simplicity_score(3)
        assert score == 70.0

    def test_four_functions_0_points_disqualified(self):
        """4+ core functions = 0 points (automatic disqualification)."""
        score = _calculate_simplicity_score(4)
        assert score == 0.0

    def test_five_functions_0_points(self):
        """5 core functions = 0 points."""
        score = _calculate_simplicity_score(5)
        assert score == 0.0

    def test_ten_functions_0_points(self):
        """10 core functions = 0 points."""
        score = _calculate_simplicity_score(10)
        assert score == 0.0

    def test_zero_functions_0_points(self):
        """0 core functions = 0 points (no functions means no app)."""
        score = _calculate_simplicity_score(0)
        assert score == 0.0


class TestExtractCoreFunctions:
    """Test core function extraction from opportunity data."""

    def test_extract_from_function_list(self):
        """Extract functions from function_list field."""
        opportunity = {
            "function_list": ["Track calories", "Calculate BMI", "Set goals"]
        }
        functions = _extract_core_functions(opportunity)
        assert len(functions) == 3
        assert "Track calories" in functions

    def test_extract_from_core_functions_count(self):
        """Generate functions from core_functions count."""
        opportunity = {
            "core_functions": 2
        }
        functions = _extract_core_functions(opportunity)
        assert len(functions) == 2
        assert "function_1" in functions
        assert "function_2" in functions

    def test_extract_from_description(self):
        """Parse functions from app_description text."""
        opportunity = {
            "app_description": "Allows users to track calories and calculate BMI. Provides goal setting features."
        }
        functions = _extract_core_functions(opportunity)
        assert len(functions) > 0
        assert all(isinstance(f, str) for f in functions)

    def test_empty_opportunity(self):
        """Handle empty or missing opportunity data."""
        opportunity = {}
        functions = _extract_core_functions(opportunity)
        assert len(functions) == 0

    def test_invalid_core_functions_type(self):
        """Handle invalid core_functions field type."""
        opportunity = {
            "core_functions": "invalid"  # Should be int, not string
        }
        functions = _extract_core_functions(opportunity)
        assert len(functions) == 0


class TestParseFunctionsFromText:
    """Test NLP parsing of functions from description text."""

    def test_bullet_point_patterns(self):
        """Parse functions from bullet points."""
        text = """
        • Track calories consumed daily
        • Calculate body mass index
        • Set fitness goals
        """
        functions = _parse_functions_from_text(text)
        assert len(functions) > 0
        assert any("calories" in f.lower() for f in functions)

    def test_allows_users_to_patterns(self):
        """Parse functions from 'allows users to' patterns."""
        text = "Allows users to track calories and calculate BMI. Provides goal setting features."
        functions = _parse_functions_from_text(text)
        assert len(functions) > 0
        assert any("calories" in f.lower() for f in functions)

    def test_verb_noun_patterns(self):
        """Parse functions from verb-noun patterns."""
        text = "Track calories, calculate BMI, set goals, monitor progress"
        functions = _parse_functions_from_text(text)
        assert len(functions) > 0

    def test_empty_text(self):
        """Handle empty text."""
        functions = _parse_functions_from_text("")
        assert len(functions) == 0

    def test_duplicate_functions_removed(self):
        """Ensure duplicate functions are removed."""
        text = "Track calories Track calories calculate BMI calculate BMI"
        functions = _parse_functions_from_text(text)
        # Should not have duplicates
        assert len(functions) == len(set(f.lower() for f in functions))

    def test_maximum_3_functions(self):
        """Limit to maximum 3 functions."""
        text = "F1 F2 F3 F4 F5 F6 F7 F8 F9 F10"
        functions = _parse_functions_from_text(text)
        assert len(functions) <= 3

    def test_function_name_cleaning(self):
        """Test whitespace normalization and formatting."""
        text = "Track    calories    with   detailed   logging"
        functions = _parse_functions_from_text(text)
        assert len(functions) > 0
        # Check no extra whitespace
        for f in functions:
            assert "  " not in f


class TestDLTConstraintResource:
    """Test the DLT resource with constraint validation."""

    def test_one_function_app_passes(self):
        """1 function app passes constraint with 100 simplicity score."""
        opportunity = {
            "opportunity_id": "test_1",
            "app_name": "SimpleCalorieCounter",
            "function_list": ["Track calories"],
            "total_score": 85.0,
            "market_demand_score": 80.0,
            "pain_intensity_score": 85.0,
            "monetization_potential_score": 90.0,
            "market_gap_score": 75.0,
            "technical_feasibility_score": 80.0
        }

        result = list(app_opportunities_with_constraint([opportunity]))[0]

        assert result["core_functions"] == 1
        assert result["simplicity_score"] == 100.0
        assert result["is_disqualified"] == False
        assert result["constraint_version"] == 1
        assert "validation_timestamp" in result
        assert result["validation_status"] == "APPROVED (1 functions)"
        assert "violation_reason" not in result or result["violation_reason"] is None

    def test_two_function_app_passes(self):
        """2 function app passes constraint with 85 simplicity score."""
        opportunity = {
            "opportunity_id": "test_2",
            "app_name": "CalorieMacroTracker",
            "function_list": ["Track calories", "Track macros"],
            "total_score": 88.0
        }

        result = list(app_opportunities_with_constraint([opportunity]))[0]

        assert result["core_functions"] == 2
        assert result["simplicity_score"] == 85.0
        assert result["is_disqualified"] == False
        assert result["validation_status"] == "APPROVED (2 functions)"

    def test_three_function_app_passes(self):
        """3 function app passes constraint with 70 simplicity score."""
        opportunity = {
            "opportunity_id": "test_3",
            "app_name": "FullFitnessTracker",
            "function_list": ["Track calories", "Track macros", "Track water intake"],
            "total_score": 82.0
        }

        result = list(app_opportunities_with_constraint([opportunity]))[0]

        assert result["core_functions"] == 3
        assert result["simplicity_score"] == 70.0
        assert result["is_disqualified"] == False
        assert result["validation_status"] == "APPROVED (3 functions)"

    def test_four_function_app_disqualified(self):
        """4+ function app is automatically disqualified with 0 simplicity score."""
        opportunity = {
            "opportunity_id": "test_4",
            "app_name": "ComplexAllInOneApp",
            "function_list": ["F1", "F2", "F3", "F4"],
            "total_score": 90.0  # High score before constraint
        }

        result = list(app_opportunities_with_constraint([opportunity]))[0]

        assert result["core_functions"] == 4
        assert result["simplicity_score"] == 0.0
        assert result["is_disqualified"] == True
        assert result["total_score"] == 0.0  # Zeroed out
        assert "DISQUALIFIED" in result["validation_status"]
        assert "4" in result["validation_status"]
        assert result["violation_reason"] == "4 core functions exceed maximum of 3"

    def test_five_function_app_disqualified(self):
        """5 function app is automatically disqualified."""
        opportunity = {
            "opportunity_id": "test_5",
            "app_name": "SuperComplexApp",
            "function_list": ["F1", "F2", "F3", "F4", "F5"],
            "total_score": 95.0
        }

        result = list(app_opportunities_with_constraint([opportunity]))[0]

        assert result["core_functions"] == 5
        assert result["simplicity_score"] == 0.0
        assert result["is_disqualified"] == True
        assert result["total_score"] == 0.0
        assert result["violation_reason"] == "5 core functions exceed maximum of 3"

    def test_multiple_opportunities_validation(self):
        """Validate multiple opportunities with different function counts."""
        opportunities = [
            {
                "opportunity_id": "opp_1",
                "app_name": "SingleFunction",
                "function_list": ["Track calories"]
            },
            {
                "opportunity_id": "opp_2",
                "app_name": "DualFunction",
                "function_list": ["Track calories", "Calculate BMI"]
            },
            {
                "opportunity_id": "opp_3",
                "app_name": "ComplexApp",
                "function_list": ["F1", "F2", "F3", "F4", "F5"]
            }
        ]

        results = list(app_opportunities_with_constraint(opportunities))

        # First app (1 function) - approved
        assert results[0]["is_disqualified"] == False
        assert results[0]["simplicity_score"] == 100.0

        # Second app (2 functions) - approved
        assert results[1]["is_disqualified"] == False
        assert results[1]["simplicity_score"] == 85.0

        # Third app (5 functions) - disqualified
        assert results[2]["is_disqualified"] == True
        assert results[2]["simplicity_score"] == 0.0
        assert results[2]["total_score"] == 0.0

    def test_constraint_metadata_added(self):
        """Verify all constraint metadata fields are added."""
        opportunity = {
            "opportunity_id": "test_meta",
            "app_name": "TestApp",
            "function_list": ["Single function"]
        }

        result = list(app_opportunities_with_constraint([opportunity]))[0]

        # Check all required metadata fields
        assert "core_functions" in result
        assert "simplicity_score" in result
        assert "is_disqualified" in result
        assert "constraint_version" in result
        assert "validation_timestamp" in result
        assert "validation_status" in result

    def test_existing_fields_preserved(self):
        """Ensure existing opportunity fields are preserved."""
        opportunity = {
            "opportunity_id": "test_preserve",
            "app_name": "TestApp",
            "function_list": ["Track calories"],
            "market_demand_score": 80.0,
            "custom_field": "custom_value"
        }

        result = list(app_opportunities_with_constraint([opportunity]))[0]

        # Check existing fields are preserved
        assert result["opportunity_id"] == "test_preserve"
        assert result["app_name"] == "TestApp"
        assert result["market_demand_score"] == 80.0
        assert result["custom_field"] == "custom_value"

    def test_parsing_from_description_fallback(self):
        """Test function parsing when function_list is not available."""
        opportunity = {
            "opportunity_id": "test_parse",
            "app_name": "ParsedApp",
            "app_description": "Allows users to track calories, calculate BMI, and set fitness goals"
        }

        result = list(app_opportunities_with_constraint([opportunity]))[0]

        assert result["core_functions"] > 0
        assert result["is_disqualified"] == False
        assert "validation_status" in result


class TestDLTPipelineIntegration:
    """Test integration with DLT pipeline (mocked)."""

    @patch('dlt.pipeline')
    def test_dlt_pipeline_creation(self, mock_pipeline):
        """Test DLT pipeline is created with correct configuration."""
        from scripts.dlt_opportunity_pipeline import (
            load_app_opportunities_with_constraint,
        )

        # Mock pipeline instance
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.run.return_value = Mock(
            load_id="test_load_123",
            duration=500
        )
        mock_pipeline.return_value = mock_pipeline_instance

        opportunities = [
            {
                "opportunity_id": "test_1",
                "app_name": "TestApp",
                "function_list": ["Track calories"]
            }
        ]

        # Call the pipeline function
        load_info = load_app_opportunities_with_constraint(opportunities)

        # Verify pipeline was created with correct config
        mock_pipeline.assert_called_once()
        call_kwargs = mock_pipeline.call_args.kwargs
        assert call_kwargs["pipeline_name"] == "reddit_harbor_collection"
        assert call_kwargs["destination"] == "postgres"
        assert call_kwargs["dataset_name"] == "reddit_harbor"

        # Verify run was called with correct parameters
        mock_pipeline_instance.run.assert_called_once()
        run_call = mock_pipeline_instance.run.call_args
        assert run_call.kwargs["write_disposition"] == "merge"
        assert run_call.kwargs["primary_key"] == "opportunity_id"

    def test_validate_constraints_only(self):
        """Test validation without database loading."""
        from scripts.dlt_opportunity_pipeline import validate_constraints_only

        opportunities = [
            {
                "opportunity_id": "test_1",
                "app_name": "SimpleApp",
                "function_list": ["Track calories"]
            },
            {
                "opportunity_id": "test_2",
                "app_name": "ComplexApp",
                "function_list": ["F1", "F2", "F3", "F4", "F5"]
            }
        ]

        results = validate_constraints_only(opportunities)

        # Verify validation summary
        assert results["total_opportunities"] == 2
        assert results["approved_count"] == 1
        assert results["disqualified_count"] == 1
        assert len(results["approved_opportunities"]) == 1
        assert len(results["disqualified_opportunities"]) == 1
        assert "validation_timestamp" in results


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_opportunities_list(self):
        """Handle empty opportunities list."""
        results = list(app_opportunities_with_constraint([]))
        assert len(results) == 0

    def test_none_opportunities(self):
        """Handle None opportunities list - DLT wraps in ResourceExtractionError."""
        with pytest.raises(dlt.extract.exceptions.ResourceExtractionError):
            list(app_opportunities_with_constraint(None))

    def test_malformed_opportunity(self):
        """Handle malformed opportunity data."""
        opportunities = [
            None,  # None opportunity
            {
                "opportunity_id": "test_1",
                # Missing function_list and other fields
            }
        ]

        # Should not crash, just yield opportunities as-is with defaults
        results = list(app_opportunities_with_constraint([opportunities[1]]))
        assert len(results) == 1
        assert results[0]["core_functions"] == 0  # Default for missing

    def test_very_long_function_list(self):
        """Handle opportunity with very long function list."""
        opportunity = {
            "opportunity_id": "test_long",
            "app_name": "LongListApp",
            "function_list": [f"Function {i}" for i in range(20)]
        }

        result = list(app_opportunities_with_constraint([opportunity]))[0]

        assert result["core_functions"] == 20
        assert result["is_disqualified"] == True
        assert result["simplicity_score"] == 0.0

    def test_special_characters_in_functions(self):
        """Handle special characters in function names."""
        opportunity = {
            "opportunity_id": "test_special",
            "app_name": "SpecialCharApp",
            "function_list": ["Track calories (advanced)", "Calculate BMI (beta)"]
        }

        result = list(app_opportunities_with_constraint([opportunity]))[0]

        assert result["core_functions"] == 2
        assert result["is_disqualified"] == False

    def test_case_insensitive_function_names(self):
        """Test case handling in function names."""
        opportunity = {
            "opportunity_id": "test_case",
            "app_name": "CaseTest",
            "function_list": ["TRACK CALORIES", "calculate bmi", "Set Goals"]
        }

        result = list(app_opportunities_with_constraint([opportunity]))[0]

        assert result["core_functions"] == 3
        assert result["is_disqualified"] == False


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
