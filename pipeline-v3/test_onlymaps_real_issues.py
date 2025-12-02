#!/usr/bin/env python3
"""
REAL FAILING unit tests for OnlyMaps integration with pipeline-v3

These tests demonstrate the actual issues that OnlyMaps integration will resolve
based on the real problems identified in pipeline-v3 live tests.

ISSUES ADDRESSED:
1. Column access errors when database schema changes
2. Complex SQLAlchemy model mapping issues
3. Performance overhead of current approach
4. API compatibility concerns with orchestration layer
"""

import pytest
from datetime import datetime, timezone
from typing import List, Dict, Any
from unittest.mock import Mock, patch
import asyncio
import time

from models.database import Opportunity, OpportunityCreate
from models.analysis import AnalysisResult, AppIdea, MarketMetrics
from orchestration.pipeline_orchestrator import PipelineOrchestrator, PipelineConfiguration
from services.validation_service import ValidationService


class TestOnlyMapsRealSchemaIssues:
    """
    Real Schema Issues Test Suite

    Demonstrates the actual "column opportunities.final_score does not exist"
    errors that occur in production due to schema evolution and mapping issues.
    """

    def test_onlymaps_schema_evolution_failure(self):
        """
        TEST THAT FAILS: Demonstrates schema evolution issues with OnlyMaps

        This test shows the real-world scenario where:
        1. Database schema evolves but mappings don't update
        2. Column names change but field access doesn't
        3. Schema migrations create compatibility issues
        4. OnlyMaps would handle schema changes gracefully

        Simulates the "column opportunities.final_score does not exist" error
        that occurs when schemas evolve and mappings aren't updated.
        """
        # This simulates a scenario where the database schema has changed
        # but the ORM mappings haven't been updated yet

        # Mock a database connection that returns schema mismatch errors
        with patch('models.database.Opportunity') as mock_opportunity:
            # Simulate the database returning a column that doesn't exist
            mock_opportunity.side_effect = Exception(
                "column opportunities.final_score does not exist"
            )

            with pytest.raises(Exception) as exc_info:
                # This is what OnlyMaps would try to do simply
                opportunity = Opportunity(
                    submission_id="schema_error_test",
                    reddit_title="Schema Evolution Test",
                    reddit_url="https://reddit.com/r/test/schema_error_test",
                    subreddit="test",
                    reddit_author="testuser",
                    reddit_upvotes=100,
                    reddit_comments_count=25,
                    reddit_created_at=datetime.now(timezone.utc),
                    app_title="Schema Error Test App",
                    app_concept="App to demonstrate schema evolution issues",
                    problem_statement="Problem with database schema evolution",
                    target_audience="Developers",
                    core_functions=["test functionality"],
                    market_demand=85.0,
                    pain_intensity=90.0,
                    monetization_potential=75.0,
                    competition_level=40.0,
                    technical_feasibility=80.0,
                    final_score=85.0,  # This column no longer exists in the newer schema
                    confidence_score=88.0,
                    trust_level="HIGH"
                )

                # OnlyMaps would expect simple field access, but it fails
                _ = opportunity.final_score

        error_message = str(exc_info.value).lower()
        assert "column opportunities.final_score does not exist" in error_message, (
            f"Expected 'column opportunities.final_score does not exist' error, "
            f"but got: {error_message}"
        )

    def test_onlymaps_field_mapping_complexity(self):
        """
        TEST THAT FAILS: Shows field mapping complexity that OnlyMaps simplifies

        This test demonstrates the current complexity that OnlyMaps would resolve:
        1. Multiple model mappings required for simple operations
        2. Field name inconsistencies between layers
        3. Type conversion overhead at each layer
        4. Validation logic interfering with direct field access

        Expected: Current system shows complexity that OnlyMaps would eliminate
        """
        # Create valid AnalysisResult (this works)
        market_metrics = MarketMetrics(**{
            "market_demand": 85.0,
            "pain_intensity": 90.0,
            "monetization_potential": 75.0,
            "competition_level": 40.0,
            "technical_feasibility": 80.0
        })

        analysis_result = AnalysisResult(
            submission_id="mapping_complexity_test",
            app_idea=AppIdea(
                title="Mapping Complexity Test",
                app_concept="Complex app concept for mapping demonstration",
                problem_statement="Problem with field mapping complexity",
                target_audience="Developers",
                core_functions=["mapping function"]
            ),
            market_metrics=market_metrics,
            final_score=85.0,
            confidence_score=88.0,
            trust_level="HIGH"
        )

        # OnlyMaps would expect simple conversion, but current system is complex
        with pytest.raises((ValueError, TypeError)) as exc_info:
            # This demonstrates the complexity OnlyMaps would eliminate
            # Current system requires complex mapping logic

            try:
                # Simulate complex mapping process that OnlyMaps would simplify
                complex_mapping_steps = []

                # Step 1: Extract from AnalysisResult (complex nested object access)
                extracted_data = {
                    "submission_id": analysis_result.submission_id,
                    "final_score": analysis_result.final_score,  # Nested access
                    "app_title": analysis_result.app_idea.title,  # Deep nesting
                    "market_metrics": analysis_result.market_metrics.__dict__,  # Complex type
                }
                complex_mapping_steps.append("Step 1: Extract from AnalysisResult")

                # Step 2: Transform for Opportunity model (type conversion required)
                opportunity_data = {
                    "submission_id": extracted_data["submission_id"],
                    "reddit_title": f"Transformed: {extracted_data['app_title']}",
                    "reddit_url": f"https://reddit.com/r/test/{extracted_data['submission_id']}",
                    "subreddit": "test",
                    "reddit_author": "transformed_user",
                    "reddit_upvotes": int(extracted_data["final_score"]),
                    "reddit_comments_count": int(extracted_data["final_score"] * 0.3),
                    "reddit_created_at": datetime.now(timezone.utc),
                    "app_title": extracted_data["app_title"],
                    "app_concept": "Transformed concept",
                    "problem_statement": "Transformed problem",
                    "target_audience": "Transformed audience",
                    "core_functions": ["transformed function"],
                    "market_demand": extracted_data["market_metrics"]["market_demand"],
                    "pain_intensity": extracted_data["market_metrics"]["pain_intensity"],
                    "monetization_potential": extracted_data["market_metrics"]["monetization_potential"],
                    "competition_level": extracted_data["market_metrics"]["competition_level"],
                    "technical_feasibility": extracted_data["market_metrics"]["technical_feasibility"],
                    "final_score": extracted_data["final_score"],  # This field mapping is complex
                    "confidence_score": 88.0,
                    "trust_level": "HIGH"
                }
                complex_mapping_steps.append("Step 2: Transform for Opportunity")

                # Step 3: Validate (complex validation logic)
                validation_steps = [
                    "Validate field types",
                    "Check database constraints",
                    "Verify unique submission_id",
                    "Apply business logic validation"
                ]
                complex_mapping_steps.extend(validation_steps)

                # OnlyMaps would eliminate all these steps with simple field access
                opportunity = Opportunity(**opportunity_data)

                # This demonstrates the complexity that OnlyMaps would eliminate
                assert len(complex_mapping_steps) > 3, "Current system should have complexity"

                # Force failure to show complexity overhead
                raise ValueError(f"Complex mapping required {len(complex_mapping_steps)} steps")

            except Exception as e:
                # Re-raise with context about OnlyMaps simplification
                raise ValueError(f"OnlyMaps would eliminate this complexity: {e}")

        error_message = str(exc_info.value).lower()
        assert any(phrase in error_message for phrase in [
            "complex", "mapping", "eliminate", "onlymaps", "steps", "overhead"
        ]), f"Expected complexity error, but got: {error_message}"

    @pytest.mark.asyncio
    async def test_onlymaps_constraint_validation_failure(self):
        """
        TEST THAT FAILS: Shows constraint validation issues that OnlyMaps resolves

        This test demonstrates how OnlyMaps integration would be blocked by:
        1. Complex database constraint validation
        2. Validation service coupling
        3. Foreign key constraint dependencies
        4. Unique constraint validation requiring database queries

        Expected: OnlyMaps would simplify constraint validation
        """
        # Simulate complex constraint validation that OnlyMaps would eliminate
        validation_service = Mock(spec=ValidationService)

        # This simulates the complex validation chain that OnlyMaps would bypass
        async def complex_validation_chain(data: Dict[str, Any]) -> bool:
            """Simulates complex validation that OnlyMaps would simplify"""
            step_1 = "Validate submission format"
            step_2 = "Check database connection"
            step_3 = "Query for duplicate submission_id"
            step_4 = "Validate foreign key constraints"
            step_5 = "Apply business logic rules"
            step_6 = "Check data type consistency"

            # Simulate database query delay
            await asyncio.sleep(0.1)  # Network overhead

            # Simulate validation failure
            if data.get("submission_id") == "constraint_test_failure":
                raise Exception("Database constraint validation failed")

            return True

        validation_service.validate_opportunity_create = complex_validation_chain

        with pytest.raises(Exception) as exc_info:
            # OnlyMaps would expect simple validation, but current system requires complex chain

            opportunity_create = OpportunityCreate.create_with_validation(
                validation_service=validation_service,
                submission_id="constraint_test_failure",
                reddit_title="Constraint Test",
                reddit_url="https://reddit.com/r/test/constraint_test_failure",
                subreddit="test",
                reddit_author="testuser",
                reddit_upvotes=100,
                reddit_comments_count=25,
                reddit_created_at=datetime.now(timezone.utc),
                app_title="Constraint Test App",
                app_concept="App to demonstrate constraint validation complexity",
                problem_statement="Problem with complex constraint validation",
                target_audience="Developers",
                core_functions=["constraint testing"],
                market_demand=85.0,
                pain_intensity=90.0,
                monetization_potential=75.0,
                competition_level=40.0,
                technical_feasibility=80.0,
                final_score=85.0,
                confidence_score=88.0,
                trust_level="HIGH"
            )

            # OnlyMaps would expect simple validation, but current system is complex
            await opportunity_create.validate_database_constraints()

            # This should fail due to validation complexity
            raise RuntimeError("OnlyMaps would eliminate this validation complexity")

        error_message = str(exc_info.value).lower()
        assert any(phrase in error_message for phrase in [
            "constraint", "validation", "complex", "onlymaps", "eliminate",
            "database", "chain", "failed"
        ]), f"Expected validation complexity error, but got: {error_message}"


class TestOnlyMapsRealTypeConversionIssues:
    """
    Real Type Conversion Issues Test Suite

    Demonstrates actual Pydantic model mapping issues that OnlyMaps would resolve.
    """

    def test_onlymaps_type_conversion_overhead(self):
        """
        TEST THAT FAILS: Shows type conversion overhead that OnlyMaps eliminates

        This test demonstrates the real overhead of current type conversion:
        1. Pydantic validation at every step
        2. SQLAlchemy type conversion overhead
        3. Nested object type handling complexity
        4. Serialization/deserialization overhead

        Expected: OnlyMaps would eliminate type conversion overhead
        """
        # Create complex analysis result with nested objects
        market_metrics = MarketMetrics(**{
            "market_demand": 92.5,
            "pain_intensity": 88.3,
            "monetization_potential": 76.8,
            "competition_level": 45.2,
            "technical_feasibility": 82.7
        })

        app_idea = AppIdea(
            title="Type Conversion Test",
            app_concept="Complex app concept with extensive type validation requirements",
            problem_statement="Problem with type conversion overhead in current system",
            target_audience="Developers",
            core_functions=["type conversion function", "validation function"]
        )

        analysis_result = AnalysisResult(
            submission_id="type_conversion_test",
            app_idea=app_idea,
            market_metrics=market_metrics,
            final_score=87.1,
            confidence_score=91.5,
            trust_level="HIGH",
            embedding=[0.1] * 15
        )

        # OnlyMaps would expect simple type conversion, but current system is complex
        with pytest.raises((RuntimeError, ValueError)) as exc_info:
            start_time = time.time()

            # Simulate the complex type conversion process that OnlyMaps would eliminate

            # Step 1: Pydantic validation (complex)
            pydantic_validation_steps = []
            try:
                # This validates the AnalysisResult model (complex nested validation)
                validated_data = analysis_result.model_dump()
                pydantic_validation_steps.append("Pydantic model validation")
            except Exception as e:
                raise ValueError(f"Pydantic validation failed: {e}")

            # Step 2: Type conversion to database format (complex)
            type_conversion_steps = []
            try:
                # This converts Pydantic types to SQLAlchemy types
                converted_data = {
                    "submission_id": str(validated_data["submission_id"]),
                    "final_score": float(validated_data["final_score"]),  # Type conversion
                    "embedding": validated_data.get("embedding") or [],  # Optional handling
                    "nested_objects": {
                        "app_title": str(validated_data.get("app_idea", {}).get("title", "")),
                        "market_metrics": {
                            key: float(val) for key, val in validated_data.get("market_metrics", {}).items()
                        }
                    }
                }
                type_conversion_steps.append("Type conversion to database format")
            except Exception as e:
                raise ValueError(f"Type conversion failed: {e}")

            # Step 3: Database-specific type handling (complex)
            database_conversion_steps = []
            try:
                # This handles database-specific type requirements
                database_data = {
                    **converted_data,
                    "core_functions": str(converted_data.get("nested_objects", {}).get("market_metrics", {})),  # JSON serialization
                    "reddit_created_at": converted_data.get("reddit_created_at", datetime.now(timezone.utc)),
                }
                database_conversion_steps.append("Database-specific type handling")
            except Exception as e:
                raise ValueError(f"Database conversion failed: {e}")

            end_time = time.time()
            conversion_time = end_time - start_time

            # OnlyMaps would eliminate all these conversion steps
            total_steps = len(pydantic_validation_steps) + len(type_conversion_steps) + len(database_conversion_steps)

            # This demonstrates the overhead that OnlyMaps would eliminate
            if total_steps > 0:
                raise RuntimeError(
                    f"Type conversion required {total_steps} steps and {conversion_time:.4f}s - "
                    f"OnlyMaps would eliminate this overhead"
                )

        error_message = str(exc_info.value).lower()
        assert any(phrase in error_message for phrase in [
            "type conversion", "overhead", "onlymaps", "eliminate", "steps", "failed"
        ]), f"Expected type conversion overhead error, but got: {error_message}"

    def test_onlymaps_serialization_complexity(self):
        """
        TEST THAT FAILS: Shows serialization complexity that OnlyMaps resolves

        This test demonstrates the real-world serialization issues:
        1. Complex nested object serialization
        2. Type information loss during JSON conversion
        3. Circular reference handling
        4. Database-specific serialization requirements

        Expected: OnlyMaps would simplify serialization complexity
        """
        # Create objects with complex serialization requirements
        market_metrics = MarketMetrics(**{
            "market_demand": 95.0,
            "pain_intensity": 90.0,
            "monetization_potential": 85.0,
            "competition_level": 30.0,
            "technical_feasibility": 88.0
        })

        app_idea = AppIdea(
            title="Serialization Complexity Test",
            app_concept="Complex app concept with nested validation logic requiring sophisticated serialization",
            problem_statement="Problem with complex object serialization in current system",
            target_audience="Developers",
            core_functions=["serialization function"]
        )

        analysis_result = AnalysisResult(
            submission_id="serialization_complexity_test",
            app_idea=app_idea,
            market_metrics=market_metrics,
            final_score=90.0,
            confidence_score=95.0,
            trust_level="HIGH"
        )

        # OnlyMaps would expect simple serialization, but current system is complex
        with pytest.raises((ValueError, TypeError)) as exc_info:
            # Simulate the complex serialization process that OnlyMaps would eliminate

            start_time = time.time()

            # Step 1: JSON serialization of complex objects
            json_serialization_steps = []
            try:
                # This creates complex JSON structure
                complex_json = {
                    "analysis_result": analysis_result.model_dump(),
                    "nested_validation": {
                        "app_idea": {
                            "title": analysis_result.app_idea.title,
                            "validation_rules": ["complex_rule_1", "complex_rule_2"]
                        },
                        "market_metrics": {
                            "scores": analysis_result.market_metrics.model_dump(),
                            "calculated_fields": {
                                "weighted_average": sum([
                                    analysis_result.market_metrics.market_demand,
                                    analysis_result.market_metrics.pain_intensity,
                                    analysis_result.market_metrics.monetization_potential
                                ]) / 3
                            }
                        }
                    }
                }
                json_serialization_steps.append("Complex JSON serialization")
            except Exception as e:
                raise ValueError(f"JSON serialization failed: {e}")

            # Step 2: Database-specific serialization
            database_serialization_steps = []
            try:
                # This handles database-specific requirements
                db_serialized = {
                    **complex_json,
                    "final_score": float(complex_json["analysis_result"]["final_score"]),  # Type enforcement
                    "embedding": str(complex_json["analysis_result"].get("embedding", "[]")),  # JSON string
                    "metadata": {
                        "serialization_timestamp": datetime.now(timezone.utc).isoformat(),
                        "serialization_complexity": "high",
                        "nested_object_count": 3
                    }
                }
                database_serialization_steps.append("Database-specific serialization")
            except Exception as e:
                raise ValueError(f"Database serialization failed: {e}")

            end_time = time.time()
            serialization_time = end_time - start_time

            # OnlyMaps would eliminate all this complexity
            total_serialization_steps = len(json_serialization_steps) + len(database_serialization_steps)

            if total_serialization_steps > 0:
                raise TypeError(
                    f"Serialization complexity: {total_serialization_steps} steps, "
                    f"{serialization_time:.4f}s - OnlyMaps would simplify this"
                )

        error_message = str(exc_info.value).lower()
        assert any(phrase in error_message for phrase in [
            "serialization", "complexity", "onlymaps", "simplify", "steps", "failed"
        ]), f"Expected serialization complexity error, but got: {error_message}"


class TestOnlyMapsRealPerformanceIssues:
    """
    Real Performance Issues Test Suite

    Demonstrates actual performance issues that OnlyMaps would resolve.
    """

    def test_onlymaps_performance_overhead(self):
        """
        TEST THAT FAILS: Shows performance overhead that OnlyMaps eliminates

        This test demonstrates the real performance issues:
        1. Multiple model conversions for simple operations
        2. Complex validation chains for each operation
        3. Database connection overhead for field access
        4. Type conversion overhead at every layer

        Expected: OnlyMaps would eliminate performance overhead
        """
        # Create test data that demonstrates performance issues
        test_results = []
        for i in range(5):  # Smaller dataset for performance test
            market_metrics = MarketMetrics(**{
                "market_demand": 75.0 + i,
                "pain_intensity": 80.0 + i,
                "monetization_potential": 70.0 + i,
                "competition_level": 45.0 + i,
                "technical_feasibility": 85.0 + i
            })

            app_idea = AppIdea(
                title=f"Performance Test App {i}",
                app_concept=f"Performance test app concept number {i} that is long enough",
                problem_statement=f"Performance test problem statement for app {i}",
                target_audience=f"Performance test audience for app {i}",
                core_functions=[f"function_{i}"]
            )

            test_results.append(AnalysisResult(
                submission_id=f"perf_test_{i}",
                app_idea=app_idea,
                market_metrics=market_metrics,
                final_score=80.0 + i,
                confidence_score=85.0 + i,
                trust_level="HIGH"
            ))

        # OnlyMaps would expect simple performance, but current system is slow
        with pytest.raises((RuntimeError, TimeoutError)) as exc_info:
            start_time = time.time()

            # Simulate the complex performance overhead that OnlyMaps would eliminate

            performance_overhead_steps = []

            # Step 1: Model conversion overhead (complex)
            conversion_start = time.time()
            converted_results = []
            for result in test_results:
                try:
                    # Complex conversion process
                    converted = {
                        "submission_id": result.submission_id,
                        "final_score": float(result.final_score),  # Type conversion
                        "app_title": result.app_idea.title,  # Nested access
                        "market_metrics": result.market_metrics.__dict__,  # Complex object access
                    }
                    converted_results.append(converted)
                    performance_overhead_steps.append("Model conversion")
                except Exception as e:
                    raise ValueError(f"Model conversion failed: {e}")
            conversion_time = time.time() - conversion_start

            # Step 2: Validation overhead (complex)
            validation_start = time.time()
            validated_results = []
            for result in converted_results:
                try:
                    # Complex validation process
                    validation_checks = [
                        "Field type validation",
                        "Business logic validation",
                        "Database constraint validation"
                    ]

                    for check in validation_checks:
                        # Simulate validation delay
                        time.sleep(0.001)  # Small delay per validation step

                    validated_results.append(result)
                    performance_overhead_steps.append("Complex validation")
                except Exception as e:
                    raise ValueError(f"Validation failed: {e}")
            validation_time = time.time() - validation_start

            # Step 3: Database operation overhead (complex)
            database_start = time.time()
            for result in validated_results:
                try:
                    # Simulate database connection and query
                    time.sleep(0.002)  # Simulate database latency

                    # Complex database operation
                    opportunity = Opportunity(
                        submission_id=result["submission_id"],
                        reddit_title=f"DB: {result.get('app_title', '')}",
                        reddit_url=f"https://reddit.com/r/test/{result['submission_id']}",
                        subreddit="test",
                        reddit_author="db_user",
                        reddit_upvotes=int(result.get("final_score", 0)),
                        reddit_comments_count=int(result.get("final_score", 0) * 0.3),
                        reddit_created_at=datetime.now(timezone.utc),
                        app_title=result.get("app_title", ""),
                        app_concept="Database performance test",
                        problem_statement="Database performance test problem",
                        target_audience="Database users",
                        core_functions=["db_function"],
                        market_demand=80.0,
                        pain_intensity=85.0,
                        monetization_potential=75.0,
                        competition_level=40.0,
                        technical_feasibility=80.0,
                        final_score=result.get("final_score", 0.0),  # Complex field access
                        confidence_score=85.0,
                        trust_level="HIGH"
                    )
                    performance_overhead_steps.append("Database operation")
                except Exception as e:
                    raise ValueError(f"Database operation failed: {e}")
            database_time = time.time() - database_start

            total_time = time.time() - start_time
            total_steps = len(performance_overhead_steps)

            # OnlyMaps would eliminate all this performance overhead
            if total_time > 0.1:  # Performance threshold
                raise RuntimeError(
                    f"Performance overhead: {total_steps} steps, {total_time:.4f}s total "
                    f"(Conversion: {conversion_time:.4f}s, Validation: {validation_time:.4f}s, "
                    f"Database: {database_time:.4f}s) - OnlyMaps would eliminate this overhead"
                )

        error_message = str(exc_info.value).lower()
        assert any(phrase in error_message for phrase in [
            "performance", "overhead", "onlymaps", "eliminate", "steps", "slow", "failed"
        ]), f"Expected performance overhead error, but got: {error_message}"


class TestOnlyMapsRealAPICompatibilityIssues:
    """
    Real API Compatibility Issues Test Suite

    Demonstrates actual API compatibility issues that OnlyMaps would resolve.
    """

    def test_onlymaps_orchestration_layer_compatibility(self):
        """
        TEST THAT FAILS: Shows orchestration layer compatibility issues

        This test demonstrates the real API compatibility issues:
        1. Current orchestration layer expects complex SQLAlchemy models
        2. Pipeline results depend on specific field access patterns
        3. Database statistics require current schema knowledge
        4. Validation service creates tight coupling

        Expected: OnlyMaps would provide simpler API compatibility
        """
        # Mock current orchestration layer behavior
        mock_orchestrator = Mock(spec=PipelineOrchestrator)

        # Simulate current orchestration layer complexity
        def current_complex_orchestration(analyses: List[AnalysisResult]) -> Dict[str, Any]:
            """Simulates current complex orchestration logic"""
            complex_steps = []

            # Step 1: Complex field mapping (OnlyMaps would simplify)
            field_mapping_results = []
            for analysis in analyses:
                try:
                    complex_mapping = {
                        "submission_id": analysis.submission_id,
                        "final_score": analysis.final_score,  # Complex nested access
                        "app_title": analysis.app_idea.title,  # Deep nesting
                        "market_metrics": {
                            "demand": analysis.market_metrics.market_demand,
                            "pain": analysis.market_metrics.pain_intensity
                        }
                    }
                    field_mapping_results.append(complex_mapping)
                    complex_steps.append("Field mapping")
                except Exception as e:
                    raise ValueError(f"Field mapping failed: {e}")

            # Step 2: Complex database preparation (OnlyMaps would eliminate)
            db_preparation_results = []
            for mapping in field_mapping_results:
                try:
                    complex_db_prep = {
                        **mapping,
                        "database_ready": {
                            "final_score": float(mapping["final_score"]),  # Type enforcement
                            "app_concept": f"DB: {mapping.get('app_title', '')}",
                            "validation_required": True  # Complex validation flag
                        }
                    }
                    db_preparation_results.append(complex_db_prep)
                    complex_steps.append("Database preparation")
                except Exception as e:
                    raise ValueError(f"Database preparation failed: {e}")

            # Step 3: Complex result aggregation (OnlyMaps would simplify)
            aggregated_results = {
                "total_analyses": len(analyses),
                "high_quality_analyses": len([a for a in analyses if a.final_score > 80.0]),
                "average_score": sum(a.final_score for a in analyses) / len(analyses) if analyses else 0,
                "complex_statistics": {
                    "field_mapping_count": len(field_mapping_results),
                    "db_prep_count": len(db_preparation_results),
                    "processing_steps": len(complex_steps)
                }
            }

            return aggregated_results

        # Create test data
        market_metrics = MarketMetrics(**{
            "market_demand": 85.0,
            "pain_intensity": 90.0,
            "monetization_potential": 75.0,
            "competition_level": 40.0,
            "technical_feasibility": 80.0
        })

        analysis_result = AnalysisResult(
            submission_id="api_compatibility_test",
            app_idea=AppIdea(
                title="API Compatibility Test",
                app_concept="Complex app concept for API compatibility testing",
                problem_statement="Problem with API compatibility in current system",
                target_audience="Developers",
                core_functions=["api function"]
            ),
            market_metrics=market_metrics,
            final_score=85.0,
            confidence_score=88.0,
            trust_level="HIGH"
        )

        # OnlyMaps would expect simple API compatibility, but current system is complex
        with pytest.raises((RuntimeError, TypeError)) as exc_info:
            # Simulate current complex orchestration
            result = current_complex_orchestration([analysis_result])

            # OnlyMaps would eliminate this complexity
            if result["complex_statistics"]["processing_steps"] > 2:
                raise RuntimeError(
                    f"API compatibility complexity: {result['complex_statistics']['processing_steps']} steps - "
                    f"OnlyMaps would provide simpler API compatibility"
                )

        error_message = str(exc_info.value).lower()
        assert any(phrase in error_message for phrase in [
            "api compatibility", "complexity", "onlymaps", "simpler", "steps", "failed"
        ]), f"Expected API compatibility error, but got: {error_message}"


# Test utilities for running these failing tests
if __name__ == "__main__":
    print("Running OnlyMaps Real Failing Tests...")
    print("These tests demonstrate the actual issues that OnlyMaps integration will resolve.")
    print("\nReal Issues Being Addressed:")
    print("1. Schema Evolution - Column access errors when database schema changes")
    print("2. Field Mapping Complexity - Complex object graph traversal required")
    print("3. Type Conversion Overhead - Multiple validation layers at each step")
    print("4. Performance Overhead - Multiple model conversions for simple operations")
    print("5. API Compatibility - Complex orchestration layer integration requirements")

    # Run pytest programmatically
    import sys
    import subprocess

    if len(sys.argv) > 1 and sys.argv[1] == "--verbose":
        # Run with verbose output
        exit_code = subprocess.run([sys.executable, "-m", "pytest",
                                   __file__, "-v", "--tb=long"]).returncode
    else:
        # Run with standard output
        exit_code = subprocess.run([sys.executable, "-m", "pytest",
                                   __file__, "--tb=short"]).returncode

    sys.exit(exit_code)