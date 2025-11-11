"""
Test Suite for Centralized Score Calculator Module.

Tests the single source of truth for all score calculations across RedditHarbor:
- Simplicity score calculation (1-3 function constraint)
- Total weighted score calculation
- Constraint enforcement with audit trail
- Score validation helpers

These tests ensure DLT compliance and prevent ordering vulnerabilities.
"""

from datetime import datetime

import pytest

from core.dlt.score_calculator import (
    apply_constraint_to_score,
    calculate_simplicity_score,
    calculate_total_score,
    get_score_audit_summary,
    is_disqualified,
    recalculate_scores_after_validation,
    validate_score_range,
)


class TestCalculateSimplicityScore:
    """Test simplicity score calculation formula."""

    def test_one_function_100_points(self):
        """1 core function = 100 points (maximum simplicity)."""
        score = calculate_simplicity_score(1)
        assert score == 100.0
        assert isinstance(score, float)

    def test_two_functions_85_points(self):
        """2 core functions = 85 points."""
        score = calculate_simplicity_score(2)
        assert score == 85.0
        assert isinstance(score, float)

    def test_three_functions_70_points(self):
        """3 core functions = 70 points (minimum approved score)."""
        score = calculate_simplicity_score(3)
        assert score == 70.0
        assert isinstance(score, float)

    def test_four_functions_0_points_disqualified(self):
        """4+ core functions = 0 points (automatic disqualification)."""
        score = calculate_simplicity_score(4)
        assert score == 0.0

    def test_five_functions_0_points(self):
        """5 core functions = 0 points."""
        score = calculate_simplicity_score(5)
        assert score == 0.0

    def test_ten_functions_0_points(self):
        """10 core functions = 0 points."""
        score = calculate_simplicity_score(10)
        assert score == 0.0

    def test_zero_functions_0_points(self):
        """0 core functions = 0 points (no functions means no app)."""
        score = calculate_simplicity_score(0)
        assert score == 0.0

    def test_negative_function_count_raises_error(self):
        """Negative function count should raise ValueError."""
        with pytest.raises(ValueError, match="must be >= 0"):
            calculate_simplicity_score(-1)

    def test_non_integer_function_count_raises_error(self):
        """Non-integer function count should raise TypeError."""
        with pytest.raises(TypeError, match="must be int"):
            calculate_simplicity_score(2.5)

    def test_deterministic_scoring(self):
        """Verify scoring is deterministic (same input = same output)."""
        # Run 10 times, should always get same result
        results = [calculate_simplicity_score(2) for _ in range(10)]
        assert all(r == 85.0 for r in results)


class TestCalculateTotalScore:
    """Test weighted total score calculation."""

    def test_total_score_with_default_weights(self):
        """Calculate total score using default methodology weights."""
        opportunity = {
            "market_demand_score": 80,
            "pain_intensity_score": 85,
            "monetization_potential_score": 78,
            "market_gap_score": 72,
            "technical_feasibility_score": 95,
            "simplicity_score": 100
        }

        total = calculate_total_score(opportunity)

        # Manual calculation:
        # 80*0.20 + 85*0.25 + 78*0.20 + 72*0.10 + 95*0.05 + 100*0.20
        # = 16 + 21.25 + 15.6 + 7.2 + 4.75 + 20
        # = 84.8
        assert total == 84.8
        assert isinstance(total, float)

    def test_total_score_with_custom_weights(self):
        """Calculate total score with custom weights."""
        opportunity = {
            "market_demand_score": 80,
            "pain_intensity_score": 85,
            "monetization_potential_score": 78,
            "market_gap_score": 72,
            "technical_feasibility_score": 95,
            "simplicity_score": 100
        }

        custom_weights = {
            "market_demand_score": 0.30,
            "pain_intensity_score": 0.30,
            "monetization_potential_score": 0.10,
            "market_gap_score": 0.10,
            "technical_feasibility_score": 0.10,
            "simplicity_score": 0.10
        }

        total = calculate_total_score(opportunity, custom_weights)

        # Manual: 80*0.30 + 85*0.30 + 78*0.10 + 72*0.10 + 95*0.10 + 100*0.10
        # = 24 + 25.5 + 7.8 + 7.2 + 9.5 + 10
        # = 84.0
        assert total == 84.0

    def test_missing_dimension_raises_key_error(self):
        """Missing dimension should raise KeyError."""
        opportunity = {
            "market_demand_score": 80,
            # Missing other required dimensions
        }

        with pytest.raises(KeyError):
            calculate_total_score(opportunity)

    def test_weights_must_sum_to_one(self):
        """Weights that don't sum to 1.0 should raise ValueError."""
        opportunity = {
            "market_demand_score": 80,
            "pain_intensity_score": 85,
            "monetization_potential_score": 78,
            "market_gap_score": 72,
            "technical_feasibility_score": 95,
            "simplicity_score": 100
        }

        invalid_weights = {
            "market_demand_score": 0.50,  # These sum to 1.5
            "pain_intensity_score": 0.50,
            "monetization_potential_score": 0.20,
            "market_gap_score": 0.10,
            "technical_feasibility_score": 0.10,
            "simplicity_score": 0.10
        }

        with pytest.raises(ValueError, match="must sum to 1.0"):
            calculate_total_score(opportunity, invalid_weights)

    def test_score_rounded_to_two_decimals(self):
        """Total score should be rounded to 2 decimal places."""
        opportunity = {
            "market_demand_score": 77.777,
            "pain_intensity_score": 88.888,
            "monetization_potential_score": 66.666,
            "market_gap_score": 55.555,
            "technical_feasibility_score": 99.999,
            "simplicity_score": 100.0
        }

        total = calculate_total_score(opportunity)

        # Should be rounded to 2 decimals
        assert len(str(total).split('.')[-1]) <= 2

    def test_deterministic_scoring(self):
        """Verify total score calculation is deterministic."""
        opportunity = {
            "market_demand_score": 80,
            "pain_intensity_score": 85,
            "monetization_potential_score": 78,
            "market_gap_score": 72,
            "technical_feasibility_score": 95,
            "simplicity_score": 100
        }

        # Run 10 times, should always get same result
        results = [calculate_total_score(opportunity) for _ in range(10)]
        assert all(r == results[0] for r in results)


class TestApplyConstraintToScore:
    """Test constraint enforcement with audit trail."""

    def test_approved_one_function_app(self):
        """1 function app should be approved with simplicity_score=100."""
        opportunity = {
            "app_name": "SimpleApp",
            "total_score": 85.0
        }

        result = apply_constraint_to_score(opportunity, function_count=1)

        assert result["simplicity_score"] == 100.0
        assert result["total_score"] == 85.0  # Unchanged
        assert "_score_audit" not in result  # No audit for approved

    def test_approved_three_function_app(self):
        """3 function app should be approved with simplicity_score=70."""
        opportunity = {
            "app_name": "ThreeFuncApp",
            "total_score": 82.0
        }

        result = apply_constraint_to_score(opportunity, function_count=3)

        assert result["simplicity_score"] == 70.0
        assert result["total_score"] == 82.0  # Unchanged
        assert "_score_audit" not in result

    def test_disqualified_four_function_app(self):
        """4 function app should be disqualified with scores zeroed."""
        opportunity = {
            "app_name": "ComplexApp",
            "total_score": 90.0
        }

        result = apply_constraint_to_score(opportunity, function_count=4)

        # Scores should be zeroed
        assert result["total_score"] == 0.0
        assert result["simplicity_score"] == 0.0

        # Audit trail should be present
        assert "_score_audit" in result
        assert result["_score_audit"]["original_score"] == 90.0
        assert result["_score_audit"]["reason"] == "simplicity_constraint_violation"
        assert result["_score_audit"]["function_count"] == 4
        assert result["_score_audit"]["max_allowed_functions"] == 3

    def test_audit_trail_contains_timestamp(self):
        """Audit trail should contain ISO timestamp."""
        opportunity = {
            "app_name": "ComplexApp",
            "total_score": 90.0
        }

        result = apply_constraint_to_score(opportunity, function_count=5)

        assert "disqualified_at" in result["_score_audit"]
        # Verify it's a valid ISO timestamp
        timestamp_str = result["_score_audit"]["disqualified_at"]
        datetime.fromisoformat(timestamp_str)  # Should not raise

    def test_audit_trail_preserves_original_score(self):
        """Audit trail should preserve exact original score."""
        opportunity = {
            "app_name": "HighScoreApp",
            "total_score": 95.77
        }

        result = apply_constraint_to_score(opportunity, function_count=10)

        assert result["_score_audit"]["original_score"] == 95.77

    def test_zero_original_score_preserved(self):
        """Even a 0.0 original score should be preserved in audit."""
        opportunity = {
            "app_name": "ZeroScoreApp",
            "total_score": 0.0
        }

        result = apply_constraint_to_score(opportunity, function_count=4)

        assert result["_score_audit"]["original_score"] == 0.0

    def test_missing_total_score_defaults_to_zero(self):
        """Missing total_score should default to 0 in audit."""
        opportunity = {
            "app_name": "NoScoreApp"
        }

        result = apply_constraint_to_score(opportunity, function_count=4)

        assert result["_score_audit"]["original_score"] == 0.0

    def test_modifies_opportunity_in_place(self):
        """Function should modify the opportunity dict in place."""
        opportunity = {
            "app_name": "TestApp",
            "total_score": 85.0
        }

        original_id = id(opportunity)
        result = apply_constraint_to_score(opportunity, function_count=1)

        # Should be the same object
        assert id(result) == original_id


class TestRecalculateScoresAfterValidation:
    """Test score recalculation after constraint validation."""

    def test_recalculate_approved_opportunity(self):
        """Approved opportunity should get recalculated total score."""
        opportunity = {
            "market_demand_score": 80,
            "pain_intensity_score": 85,
            "monetization_potential_score": 78,
            "market_gap_score": 72,
            "technical_feasibility_score": 95,
            "simplicity_score": 100,
            "is_disqualified": False
        }

        result = recalculate_scores_after_validation(opportunity)

        # Should calculate total score
        assert "total_score" in result
        assert result["total_score"] == 84.8

    def test_disqualified_opportunity_stays_zero(self):
        """Disqualified opportunity should keep total_score = 0."""
        opportunity = {
            "market_demand_score": 80,
            "pain_intensity_score": 85,
            "monetization_potential_score": 78,
            "market_gap_score": 72,
            "technical_feasibility_score": 95,
            "simplicity_score": 0,
            "is_disqualified": True,
            "total_score": 0.0
        }

        result = recalculate_scores_after_validation(opportunity)

        # Should remain 0
        assert result["total_score"] == 0.0

    def test_disqualified_overrides_high_scores(self):
        """Even with high dimension scores, disqualified apps get 0."""
        opportunity = {
            "market_demand_score": 100,
            "pain_intensity_score": 100,
            "monetization_potential_score": 100,
            "market_gap_score": 100,
            "technical_feasibility_score": 100,
            "simplicity_score": 0,
            "is_disqualified": True
        }

        result = recalculate_scores_after_validation(opportunity)

        assert result["total_score"] == 0.0


class TestValidationHelpers:
    """Test validation helper functions."""

    def test_validate_score_range_valid(self):
        """Valid scores should return True."""
        assert validate_score_range(0.0) is True
        assert validate_score_range(50.0) is True
        assert validate_score_range(100.0) is True

    def test_validate_score_range_invalid(self):
        """Invalid scores should return False."""
        assert validate_score_range(-10.0) is False
        assert validate_score_range(150.0) is False

    def test_validate_score_range_custom_bounds(self):
        """Custom min/max should work correctly."""
        assert validate_score_range(50.0, min_val=0, max_val=50) is True
        assert validate_score_range(51.0, min_val=0, max_val=50) is False

    def test_get_score_audit_summary_present(self):
        """Should extract audit summary when present."""
        opportunity = {
            "_score_audit": {
                "original_score": 85.0,
                "reason": "violation"
            }
        }

        audit = get_score_audit_summary(opportunity)
        assert audit is not None
        assert audit["original_score"] == 85.0

    def test_get_score_audit_summary_missing(self):
        """Should return None when audit not present."""
        opportunity = {"app_name": "Test"}

        audit = get_score_audit_summary(opportunity)
        assert audit is None

    def test_is_disqualified_true(self):
        """Should return True for disqualified opportunities."""
        assert is_disqualified({"is_disqualified": True}) is True

    def test_is_disqualified_false(self):
        """Should return False for approved opportunities."""
        assert is_disqualified({"is_disqualified": False}) is False

    def test_is_disqualified_missing(self):
        """Should return False when field is missing."""
        assert is_disqualified({}) is False


class TestIntegrationScenarios:
    """Test end-to-end integration scenarios."""

    def test_correct_order_validation_before_calculation(self):
        """Verify correct order: validate first, then calculate."""
        # Step 1: Start with raw opportunity
        opportunity = {
            "app_name": "TestApp",
            "market_demand_score": 80,
            "pain_intensity_score": 85,
            "monetization_potential_score": 78,
            "market_gap_score": 72,
            "technical_feasibility_score": 95,
            "simplicity_score": 100
        }

        # Step 2: Apply constraint validation FIRST
        opportunity = apply_constraint_to_score(opportunity, function_count=1)

        # Step 3: Then calculate total score
        opportunity = recalculate_scores_after_validation(opportunity)

        # Verify correct result
        assert opportunity["simplicity_score"] == 100.0
        assert opportunity["total_score"] == 84.8
        assert not is_disqualified(opportunity)

    def test_wrong_order_catches_vulnerability(self):
        """Demonstrate the vulnerability when calculating before validating."""
        # WRONG ORDER (the bug we're fixing):
        opportunity = {
            "app_name": "ComplexApp",
            "market_demand_score": 80,
            "pain_intensity_score": 85,
            "monetization_potential_score": 78,
            "market_gap_score": 72,
            "technical_feasibility_score": 95,
            "simplicity_score": 100  # Not yet validated!
        }

        # If we calculate BEFORE validating (wrong order):
        wrong_total = calculate_total_score(opportunity)

        # This gives us a high score even though app has 4+ functions
        assert wrong_total == 84.8

        # Set the score in the opportunity (simulating old behavior)
        opportunity["total_score"] = wrong_total

        # NOW we validate (too late!)
        opportunity = apply_constraint_to_score(opportunity, function_count=4)

        # Audit trail shows we had calculated a score that should have been 0
        assert opportunity["_score_audit"]["original_score"] == 84.8
        assert opportunity["total_score"] == 0.0  # Correct, but damage done

        # This demonstrates why validation MUST happen BEFORE calculation

    def test_batch_processing_with_mixed_results(self):
        """Test batch processing with approved and disqualified apps."""
        opportunities = [
            {
                "app_name": "App1",
                "market_demand_score": 80,
                "pain_intensity_score": 85,
                "monetization_potential_score": 78,
                "market_gap_score": 72,
                "technical_feasibility_score": 95,
                "simplicity_score": 100
            },
            {
                "app_name": "App2",
                "market_demand_score": 90,
                "pain_intensity_score": 95,
                "monetization_potential_score": 88,
                "market_gap_score": 82,
                "technical_feasibility_score": 98,
                "simplicity_score": 85
            },
            {
                "app_name": "App3",
                "market_demand_score": 95,
                "pain_intensity_score": 90,
                "monetization_potential_score": 85,
                "market_gap_score": 80,
                "technical_feasibility_score": 92,
                "simplicity_score": 70
            }
        ]

        function_counts = [1, 2, 3]

        # Apply constraints in batch
        for opp, count in zip(opportunities, function_counts):
            apply_constraint_to_score(opp, count)
            recalculate_scores_after_validation(opp)

        # All should be approved
        assert all(not is_disqualified(opp) for opp in opportunities)
        assert all(opp["total_score"] > 0 for opp in opportunities)


class TestDLTCompliance:
    """Test DLT-specific compliance requirements."""

    def test_scores_are_serializable(self):
        """All scores should be JSON serializable (DLT requirement)."""
        import json

        opportunity = {
            "app_name": "TestApp",
            "market_demand_score": 80,
            "pain_intensity_score": 85,
            "monetization_potential_score": 78,
            "market_gap_score": 72,
            "technical_feasibility_score": 95,
            "simplicity_score": 100
        }

        apply_constraint_to_score(opportunity, function_count=4)

        # Should be JSON serializable
        json_str = json.dumps(opportunity)
        assert json_str is not None

    def test_no_floating_point_instability(self):
        """Scores should be stable across multiple calculations."""
        opportunity = {
            "market_demand_score": 77.77,
            "pain_intensity_score": 88.88,
            "monetization_potential_score": 66.66,
            "market_gap_score": 55.55,
            "technical_feasibility_score": 99.99,
            "simplicity_score": 100.0
        }

        # Calculate 100 times
        results = [calculate_total_score(opportunity.copy()) for _ in range(100)]

        # All should be exactly the same (no floating point drift)
        assert all(r == results[0] for r in results)

    def test_audit_trail_is_dict_serializable(self):
        """Audit trail should be dict-serializable for DLT."""
        opportunity = {
            "app_name": "ComplexApp",
            "total_score": 90.0
        }

        result = apply_constraint_to_score(opportunity, function_count=4)

        # Audit should be a dict
        assert isinstance(result["_score_audit"], dict)

        # All values should be serializable
        for key, value in result["_score_audit"].items():
            assert isinstance(value, (str, int, float, bool, type(None)))


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
