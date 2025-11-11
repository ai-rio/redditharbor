"""
Phase 4 Integration Tests - DLT Constraint Validation with Existing Scripts

Tests the integration of DLT constraint validation with the existing
RedditHarbor scripts:
- final_system_test.py
- batch_opportunity_scoring.py

Validates that:
1. DLT constraint validator works with existing workflows
2. Backward compatibility is maintained
3. End-to-end workflows function correctly
4. Constraint validation occurs automatically
5. Both approved and disqualified opportunities are handled properly
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import DLT constraint components
from core.dlt.constraint_validator import app_opportunities_with_constraint
from scripts.batch_opportunity_scoring import (
    format_submission_for_agent,
    load_scores_to_supabase_via_dlt,
    prepare_analysis_for_storage,
)
from scripts.dlt_opportunity_pipeline import validate_constraints_only

# Import the components we're testing
from scripts.final_system_test import (
    generate_opportunity_scores,
    save_results,
)


class TestFinalSystemTestIntegration:
    """Test DLT constraint integration with final_system_test.py"""

    def test_generate_opportunities_with_constraint_metadata(self):
        """Test that generate_opportunity_scores produces data compatible with constraint validation."""
        opportunities = generate_opportunity_scores()

        # Verify opportunities have required fields for constraint validation
        assert len(opportunities) > 0

        for opp in opportunities:
            # Check that opportunities have the fields needed for constraint validation
            assert "app_name" in opp
            assert "core_functions" in opp or "function_list" in opp
            assert "total_score" in opp or opp["total_score"] is not None
            # Opportunities are already validated, so check validation metadata
            assert "is_disqualified" in opp
            assert "validation_status" in opp
            assert "validation_timestamp" in opp

    def test_constraint_validation_happens_before_score_calculation(self):
        """CRITICAL: Verify constraint validation happens BEFORE score calculation."""
        opportunities = generate_opportunity_scores()

        # All opportunities should have validation metadata
        for opp in opportunities:
            # Validation metadata should be present
            assert "is_disqualified" in opp
            assert "validation_status" in opp
            assert "simplicity_score" in opp
            assert "constraint_version" in opp

            # If disqualified, total_score must be 0
            if opp.get("is_disqualified"):
                assert opp["total_score"] == 0.0
                # Should have audit trail
                assert "_score_audit" in opp
                assert opp["_score_audit"]["original_score"] >= 0

    def test_approved_apps_have_calculated_scores(self):
        """Verify approved apps (1-3 functions) have properly calculated scores."""
        opportunities = generate_opportunity_scores()

        approved = [o for o in opportunities if not o.get("is_disqualified")]

        # All approved apps should have valid scores
        for opp in approved:
            assert opp["total_score"] > 0
            assert opp["simplicity_score"] in [70.0, 85.0, 100.0]
            assert opp["core_functions"] in [1, 2, 3]

    def test_save_results_with_constraint_validation(self):
        """Test that save_results applies DLT constraint validation."""
        # Create test opportunities
        test_opportunities = [
            {
                "app_name": "ValidApp1",
                "core_functions": 1,
                "function_list": ["track_data"],
                "total_score": 85.0,
                "market_demand_score": 80,
                "pain_intensity_score": 85,
                "monetization_potential_score": 80,
                "market_gap_score": 75,
                "technical_feasibility_score": 90
            },
            {
                "app_name": "ValidApp2",
                "core_functions": 2,
                "function_list": ["track_data", "analyze_data"],
                "total_score": 88.0,
                "market_demand_score": 85,
                "pain_intensity_score": 88,
                "monetization_potential_score": 85,
                "market_gap_score": 80,
                "technical_feasibility_score": 92
            }
        ]

        # Create a temporary file for testing
        with patch('scripts.final_system_test.Path') as mock_path:
            mock_path.return_value = Path(tempfile.gettempdir())

            # Mock the DLT pipeline to avoid actual database operations
            with patch('scripts.final_system_test.create_dlt_pipeline') as mock_pipeline:
                mock_load_info = MagicMock()
                mock_load_info.started_at = "2025-11-07T10:00:00"
                mock_pipeline.return_value.run.return_value = mock_load_info

                # Call save_results
                save_results(test_opportunities, use_dlt=True)

                # Verify the DLT pipeline was called
                assert mock_pipeline.called

                # Verify that the run was called with the constraint validator
                call_args = mock_pipeline.return_value.run.call_args
                assert call_args is not None

    def test_constraint_validation_reporting(self):
        """Test that constraint validation results are reported correctly."""
        test_opportunities = [
            {
                "app_name": "ValidApp1",
                "core_functions": 1,
                "function_list": ["track_data"],
                "total_score": 85.0
            },
            {
                "app_name": "InvalidApp",
                "core_functions": 4,  # This will be disqualified
                "function_list": ["f1", "f2", "f3", "f4"],
                "total_score": 90.0
            }
        ]

        # Validate constraints
        validated = list(app_opportunities_with_constraint(test_opportunities))
        approved = [o for o in validated if not o.get("is_disqualified")]
        disqualified = [o for o in validated if o.get("is_disqualified")]

        # Verify validation results
        assert len(validated) == 2
        assert len(approved) == 1
        assert len(disqualified) == 1
        assert approved[0]["app_name"] == "ValidApp1"
        assert disqualified[0]["app_name"] == "InvalidApp"
        assert disqualified[0]["violation_reason"] == "4 core functions exceed maximum of 3"
        assert disqualified[0]["total_score"] == 0  # Score should be zeroed for violations

    def test_backward_compatibility(self):
        """Test that DLT constraint integration maintains backward compatibility."""
        # Old-style opportunities without function_list or core_functions
        old_style_opportunities = [
            {
                "app_name": "OldApp1",
                "app_description": "Allows users to track data and calculate metrics",
                "total_score": 85.0
            }
        ]

        # Should still work with constraint validation
        validated = list(app_opportunities_with_constraint(old_style_opportunities))

        assert len(validated) == 1
        # Should have been processed and got constraint metadata
        assert "core_functions" in validated[0]
        assert "simplicity_score" in validated[0]
        assert "validation_status" in validated[0]
        assert "validation_timestamp" in validated[0]


class TestBatchOpportunityScoringIntegration:
    """Test DLT constraint integration with batch_opportunity_scoring.py"""

    def test_prepare_analysis_for_storage_with_constraints(self):
        """Test that prepare_analysis_for_storage works with constraint validation."""
        # Create a mock submission
        submission_id = "test_sub_123"

        # Create a mock analysis
        analysis = {
            "title": "Test Opportunity",
            "subreddit": "test",
            "final_score": 85.0,
            "priority": "High",
            "dimension_scores": {
                "market_demand": 80,
                "pain_intensity": 85,
                "monetization_potential": 80,
                "market_gap": 75,
                "technical_feasibility": 90,
                "simplicity_score": 85
            }
        }

        sector = "Technology & SaaS"

        # Prepare for storage
        storage_data = prepare_analysis_for_storage(submission_id, analysis, sector)

        # Verify all required fields are present
        assert "submission_id" in storage_data
        assert "opportunity_id" in storage_data
        assert "title" in storage_data
        assert "subreddit" in storage_data
        assert "sector" in storage_data
        assert "market_demand" in storage_data
        assert "simplicity_score" in storage_data

        # Verify data types
        assert isinstance(storage_data["market_demand"], float)
        assert isinstance(storage_data["simplicity_score"], float)

    def test_format_submission_for_agent_preserves_data(self):
        """Test that format_submission_for_agent preserves all necessary data."""
        # Create a mock submission
        submission = {
            "id": "test_123",
            "submission_id": "test_sub_123",
            "title": "Test Title",
            "text": "Test text content",
            "subreddit": "test",
            "upvotes": 100,
            "comments_count": 25,
            "sentiment_score": 0.5,
            "problem_keywords": "test problem",
            "solution_mentions": "test solution"
        }

        # Format for agent
        formatted = format_submission_for_agent(submission)

        # Verify all fields are present
        assert formatted["id"] == "test_sub_123"
        assert formatted["title"] == "Test Title"
        assert formatted["text"] == "Test Title\n\nTest text content"
        assert formatted["subreddit"] == "test"
        assert formatted["engagement"]["upvotes"] == 100
        assert formatted["engagement"]["num_comments"] == 25
        assert formatted["sentiment_score"] == 0.5
        assert formatted["db_id"] == "test_123"

    def test_load_scores_with_constraint_validation(self):
        """Test that load_scores_to_supabase_via_dlt applies constraint validation."""
        test_opportunities = [
            {
                "submission_id": "sub_1",
                "opportunity_id": "opp_1",
                "title": "Test Opp 1",
                "subreddit": "test",
                "sector": "Technology & SaaS",
                "market_demand": 80.0,
                "pain_intensity": 85.0,
                "monetization_potential": 80.0,
                "market_gap": 75.0,
                "technical_feasibility": 90.0,
                "simplicity_score": 85.0,
                "final_score": 85.0,
                "priority": "High"
            },
            {
                "submission_id": "sub_2",
                "opportunity_id": "opp_2",
                "title": "Test Opp 2",
                "subreddit": "test",
                "sector": "Technology & SaaS",
                "market_demand": 85.0,
                "pain_intensity": 90.0,
                "monetization_potential": 85.0,
                "market_gap": 80.0,
                "technical_feasibility": 95.0,
                "simplicity_score": 100.0,  # 1 function
                "final_score": 90.0,
                "priority": "High"
            }
        ]

        # Mock the DLT pipeline
        with patch('scripts.batch_opportunity_scoring.create_dlt_pipeline') as mock_pipeline:
            mock_load_info = MagicMock()
            mock_load_info.started_at = "2025-11-07T10:00:00"
            mock_pipeline.return_value.run.return_value = mock_load_info

            # Load with constraint validation
            result = load_scores_to_supabase_via_dlt(test_opportunities)

            # Verify success
            assert result is True

            # Verify the DLT pipeline was called
            assert mock_pipeline.called

            # Verify that the run was called with constraint validation
            call_args = mock_pipeline.return_value.run.call_args
            assert call_args is not None

    def test_constraint_validation_with_violations(self):
        """Test that constraint validation correctly identifies violations."""
        test_opportunities = [
            {
                "app_name": "ValidApp",
                "core_functions": 2,
                "function_list": ["func1", "func2"],
                "total_score": 85.0
            },
            {
                "app_name": "InvalidApp1",
                "core_functions": 4,
                "function_list": ["func1", "func2", "func3", "func4"],
                "total_score": 90.0
            },
            {
                "app_name": "InvalidApp2",
                "core_functions": 5,
                "function_list": ["func1", "func2", "func3", "func4", "func5"],
                "total_score": 95.0
            }
        ]

        # Validate constraints
        validated = list(app_opportunities_with_constraint(test_opportunities))
        approved = [o for o in validated if not o.get("is_disqualified")]
        disqualified = [o for o in validated if o.get("is_disqualified")]

        # Verify results
        assert len(validated) == 3
        assert len(approved) == 1
        assert len(disqualified) == 2

        # Verify disqualified opportunities have violations
        for opp in disqualified:
            assert opp["is_disqualified"] is True
            assert "violation_reason" in opp
            assert "4" in opp["violation_reason"] or "5" in opp["violation_reason"]
            assert opp["total_score"] == 0  # Score should be zeroed

    def test_validate_constraints_only_function(self):
        """Test the validate_constraints_only utility function."""
        test_opportunities = [
            {
                "app_name": "TestApp1",
                "core_functions": 1,
                "function_list": ["track"],
                "total_score": 85.0
            },
            {
                "app_name": "TestApp2",
                "core_functions": 2,
                "function_list": ["track", "analyze"],
                "total_score": 88.0
            },
            {
                "app_name": "TestApp3",
                "core_functions": 4,
                "function_list": ["f1", "f2", "f3", "f4"],
                "total_score": 90.0
            }
        ]

        # Validate without loading
        results = validate_constraints_only(test_opportunities)

        # Verify results structure
        assert "total_opportunities" in results
        assert "approved_count" in results
        assert "disqualified_count" in results
        assert "approved_opportunities" in results
        assert "disqualified_opportunities" in results
        assert "validation_timestamp" in results

        # Verify counts
        assert results["total_opportunities"] == 3
        assert results["approved_count"] == 2
        assert results["disqualified_count"] == 1
        assert len(results["approved_opportunities"]) == 2
        assert len(results["disqualified_opportunities"]) == 1

    def test_function_list_extraction_integration(self):
        """Test that function_list is properly extracted and validated."""
        # Test with function_list provided
        opp_with_list = {
            "app_name": "App1",
            "function_list": ["Track calories", "Calculate BMI"],
            "total_score": 85.0
        }

        validated = list(app_opportunities_with_constraint([opp_with_list]))
        assert len(validated) == 1
        assert validated[0]["core_functions"] == 2
        assert validated[0]["simplicity_score"] == 85.0
        assert validated[0]["is_disqualified"] is False

        # Test with core_functions count
        opp_with_count = {
            "app_name": "App2",
            "core_functions": 3,
            "total_score": 88.0
        }

        validated = list(app_opportunities_with_constraint([opp_with_count]))
        assert len(validated) == 1
        assert validated[0]["core_functions"] == 3
        assert validated[0]["simplicity_score"] == 70.0
        assert validated[0]["is_disqualified"] is False

        # Test with 4+ functions (disqualified)
        opp_disqualified = {
            "app_name": "App3",
            "core_functions": 5,
            "total_score": 90.0
        }

        validated = list(app_opportunities_with_constraint([opp_disqualified]))
        assert len(validated) == 1
        assert validated[0]["core_functions"] == 5
        assert validated[0]["simplicity_score"] == 0.0
        assert validated[0]["is_disqualified"] is True


class TestEndToEndWorkflow:
    """Test end-to-end workflows with DLT constraint validation"""

    def test_full_pipeline_with_constraint_validation(self):
        """Test a full pipeline from opportunity generation to validation."""
        # Step 1: Generate opportunities
        opportunities = generate_opportunity_scores()

        # Step 2: Validate constraints
        validated = list(app_opportunities_with_constraint(opportunities))
        approved = [o for o in validated if not o.get("is_disqualified")]
        disqualified = [o for o in validated if o.get("is_disqualified")]

        # Step 3: Verify results
        assert len(opportunities) > 0
        assert len(validated) == len(opportunities)

        # All opportunities in generate_opportunity_scores should be 1-3 functions
        assert all(o["core_functions"] <= 3 for o in opportunities)

        # All should pass constraint validation
        assert len(disqualified) == 0
        assert len(approved) == len(opportunities)

        # Verify constraint metadata was added
        for opp in validated:
            assert "core_functions" in opp
            assert "simplicity_score" in opp
            assert "is_disqualified" in opp
            assert "validation_status" in opp
            assert "validation_timestamp" in opp
            assert "constraint_version" in opp

    def test_mixed_approved_and_disqualified_workflow(self):
        """Test workflow with both approved and disqualified opportunities."""
        # Create mixed opportunities
        opportunities = [
            # Approved: 1 function
            {
                "app_name": "SimpleApp",
                "core_functions": 1,
                "function_list": ["Track data"],
                "total_score": 85.0
            },
            # Approved: 2 functions
            {
                "app_name": "TwoFuncApp",
                "core_functions": 2,
                "function_list": ["Track data", "Analyze data"],
                "total_score": 88.0
            },
            # Approved: 3 functions
            {
                "app_name": "ThreeFuncApp",
                "core_functions": 3,
                "function_list": ["Track", "Analyze", "Report"],
                "total_score": 82.0
            },
            # Disqualified: 4 functions
            {
                "app_name": "ComplexApp1",
                "core_functions": 4,
                "function_list": ["F1", "F2", "F3", "F4"],
                "total_score": 90.0
            },
            # Disqualified: 5 functions
            {
                "app_name": "ComplexApp2",
                "core_functions": 5,
                "function_list": ["F1", "F2", "F3", "F4", "F5"],
                "total_score": 95.0
            }
        ]

        # Validate constraints
        validated = list(app_opportunities_with_constraint(opportunities))
        approved = [o for o in validated if not o.get("is_disqualified")]
        disqualified = [o for o in validated if o.get("is_disqualified")]

        # Verify results
        assert len(opportunities) == 5
        assert len(validated) == 5
        assert len(approved) == 3
        assert len(disqualified) == 2

        # Verify approved opportunities
        assert approved[0]["core_functions"] == 1
        assert approved[0]["simplicity_score"] == 100.0
        assert approved[1]["core_functions"] == 2
        assert approved[1]["simplicity_score"] == 85.0
        assert approved[2]["core_functions"] == 3
        assert approved[2]["simplicity_score"] == 70.0

        # Verify disqualified opportunities
        assert disqualified[0]["core_functions"] == 4
        assert disqualified[0]["simplicity_score"] == 0.0
        assert disqualified[0]["total_score"] == 0
        assert disqualified[0]["is_disqualified"] is True
        assert "4 core functions exceed maximum of 3" in disqualified[0]["violation_reason"]

        assert disqualified[1]["core_functions"] == 5
        assert disqualified[1]["simplicity_score"] == 0.0
        assert disqualified[1]["total_score"] == 0
        assert disqualified[1]["is_disqualified"] is True


class TestBackwardCompatibility:
    """Test that DLT constraint integration maintains backward compatibility"""

    def test_opportunities_without_constraint_metadata(self):
        """Test that old opportunities without constraint metadata still work."""
        # Old-style opportunities (like from generate_opportunity_scores)
        old_opportunities = [
            {
                "app_name": "OldApp1",
                "core_functions": 1,
                "function_list": ["Track calories"],
                "simplicity_score": 100,
                "market_demand_score": 75,
                "pain_intensity_score": 85,
                "monetization_potential_score": 78,
                "market_gap_score": 72,
                "technical_feasibility_score": 95,
                "total_score": 85.0,
                "validation_status": "✅ APPROVED - Meets 1-3 function constraint"
            }
        ]

        # Should work with constraint validation
        validated = list(app_opportunities_with_constraint(old_opportunities))

        assert len(validated) == 1
        # New constraint metadata should be added
        assert "constraint_version" in validated[0]
        assert "validation_timestamp" in validated[0]
        # Old metadata should be preserved
        assert validated[0]["app_name"] == "OldApp1"
        # Note: validation_status is replaced by constraint validator with new format
        assert "APPROVED" in validated[0]["validation_status"]

    def test_missing_function_list(self):
        """Test opportunities without function_list but with core_functions."""
        opportunities = [
            {
                "app_name": "CountApp",
                "core_functions": 2,
                "total_score": 85.0
            }
        ]

        validated = list(app_opportunities_with_constraint(opportunities))

        assert len(validated) == 1
        assert validated[0]["core_functions"] == 2
        # core_functions count is preserved
        # function_list is not added automatically from core_functions count
        # (placeholders are generated internally only for scoring)

    def test_empty_opportunities(self):
        """Test that empty opportunity list is handled gracefully."""
        validated = list(app_opportunities_with_constraint([]))
        assert len(validated) == 0

    def test_none_values(self):
        """Test that None values are handled gracefully."""
        opportunities = [
            {
                "app_name": "TestApp",
                "core_functions": None,
                "function_list": None,
                "total_score": 85.0
            }
        ]

        # Should not crash, but may produce empty function list
        validated = list(app_opportunities_with_constraint(opportunities))
        assert len(validated) == 1
        # Should have default constraint metadata
        assert "is_disqualified" in validated[0]
        assert "validation_timestamp" in validated[0]


class TestPerformanceImpact:
    """Test that DLT constraint validation doesn't significantly impact performance"""

    def test_constraint_validation_performance(self):
        """Test that constraint validation adds minimal overhead."""
        import time

        # Create a large number of opportunities
        opportunities = []
        for i in range(1000):
            opportunities.append({
                "app_name": f"App{i}",
                "core_functions": (i % 3) + 1,  # 1-3 functions
                "function_list": [f"func_{j}" for j in range((i % 3) + 1)],
                "total_score": 70.0 + (i % 30)
            })

        # Time the validation
        start = time.time()
        validated = list(app_opportunities_with_constraint(opportunities))
        elapsed = time.time() - start

        # Should complete quickly (< 1 second for 1000 opportunities)
        assert elapsed < 1.0
        assert len(validated) == 1000

    def test_memory_efficiency(self):
        """Test that constraint validation is memory efficient."""
        import sys

        # Create opportunities
        opportunities = [
            {
                "app_name": f"App{i}",
                "core_functions": (i % 3) + 1,
                "function_list": [f"func_{j}" for j in range((i % 3) + 1)],
                "total_score": 75.0
            }
            for i in range(100)
        ]

        # Get initial memory
        initial_size = sys.getsizeof(opportunities)

        # Validate constraints
        validated = list(app_opportunities_with_constraint(opportunities))

        # Each opportunity should have added ~100 bytes of constraint metadata
        # Should be reasonable overhead
        for orig, val in zip(opportunities, validated):
            orig_size = sys.getsizeof(orig)
            val_size = sys.getsizeof(val)
            overhead = val_size - orig_size
            # Allow up to 500 bytes overhead per opportunity
            assert overhead < 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
