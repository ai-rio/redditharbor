#!/usr/bin/env python3
"""
Unit Tests for Cost Tracking Functionality
"""

import pytest
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.cost_tracking_error_handler import (
    CostTrackingErrorHandler,
    CostValidationError,
    CostDataCorruptionError,
    CostThresholdExceededError,
    validate_and_handle_costs
)
from core.dlt_cost_tracking import (
    validate_cost_data,
    generate_cost_report,
    workflow_results_with_cost_tracking
)


class TestCostTrackingErrorHandler:
    """Test cases for CostTrackingErrorHandler"""

    def test_validate_cost_data_valid(self):
        """Test validation of valid cost data"""
        handler = CostTrackingErrorHandler()

        valid_cost_data = {
            'model_used': 'claude-haiku-4.5',
            'provider': 'openrouter',
            'prompt_tokens': 850,
            'completion_tokens': 350,
            'total_tokens': 1200,
            'input_cost_usd': 0.00085,
            'output_cost_usd': 0.00175,
            'total_cost_usd': 0.0026,
            'latency_seconds': 1.234,
            'timestamp': datetime.utcnow().isoformat()
        }

        is_valid, errors = handler.validate_cost_data(valid_cost_data)
        assert is_valid, f"Valid cost data should pass validation, but got errors: {errors}"
        assert len(errors) == 0

    def test_validate_cost_data_missing_fields(self):
        """Test validation fails with missing required fields"""
        handler = CostTrackingErrorHandler()

        incomplete_data = {
            'model_used': 'claude-haiku-4.5',
            'total_cost_usd': 0.0026
        }

        is_valid, errors = handler.validate_cost_data(incomplete_data)
        assert not is_valid, "Incomplete data should fail validation"
        assert len(errors) > 0
        assert any("Missing required field" in error for error in errors)

    def test_validate_cost_data_token_mismatch(self):
        """Test validation fails with token count mismatch"""
        handler = CostTrackingErrorHandler()

        mismatched_data = {
            'model_used': 'claude-haiku-4.5',
            'provider': 'openrouter',
            'prompt_tokens': 850,
            'completion_tokens': 350,
            'total_tokens': 1500,  # Should be 1200
            'input_cost_usd': 0.00085,
            'output_cost_usd': 0.00175,
            'total_cost_usd': 0.0026,
            'latency_seconds': 1.234,
            'timestamp': datetime.utcnow().isoformat()
        }

        is_valid, errors = handler.validate_cost_data(mismatched_data)
        assert not is_valid, "Data with token mismatch should fail validation"
        assert any("Token count mismatch" in error for error in errors)

    def test_validate_cost_data_negative_values(self):
        """Test validation fails with negative values"""
        handler = CostTrackingErrorHandler()

        negative_data = {
            'model_used': 'claude-haiku-4.5',
            'provider': 'openrouter',
            'prompt_tokens': -100,  # Negative tokens
            'completion_tokens': 350,
            'total_tokens': 250,
            'input_cost_usd': 0.00085,
            'output_cost_usd': 0.00175,
            'total_cost_usd': 0.0026,
            'latency_seconds': 1.234,
            'timestamp': datetime.utcnow().isoformat()
        }

        is_valid, errors = handler.validate_cost_data(negative_data)
        assert not is_valid, "Data with negative values should fail validation"
        assert any("cannot be negative" in error for error in errors)

    def test_validate_batch_costs_within_threshold(self):
        """Test batch validation within cost threshold"""
        handler = CostTrackingErrorHandler(cost_threshold_usd=1.0)

        opportunities = [
            {
                'opportunity_id': 'test_1',
                'cost_tracking': {
                    'total_cost_usd': 0.002,
                    'total_tokens': 1000,
                    'model_used': 'claude-haiku-4.5',
                    'provider': 'openrouter',
                    'prompt_tokens': 700,
                    'completion_tokens': 300,
                    'input_cost_usd': 0.0007,
                    'output_cost_usd': 0.0013,
                    'latency_seconds': 1.0,
                    'timestamp': datetime.utcnow().isoformat()
                }
            },
            {
                'opportunity_id': 'test_2',
                'cost_tracking': {
                    'total_cost_usd': 0.003,
                    'total_tokens': 1500,
                    'model_used': 'claude-haiku-4.5',
                    'provider': 'openrouter',
                    'prompt_tokens': 1000,
                    'completion_tokens': 500,
                    'input_cost_usd': 0.0010,
                    'output_cost_usd': 0.0020,
                    'latency_seconds': 1.5,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
        ]

        is_valid, summary = handler.validate_batch_costs(opportunities)
        assert is_valid, "Batch within threshold should be valid"
        assert summary['total_cost_usd'] == 0.005
        assert summary['valid_opportunities'] == 2
        assert not summary['exceeds_threshold']

    def test_validate_batch_costs_exceeds_threshold(self):
        """Test batch validation exceeds cost threshold"""
        handler = CostTrackingErrorHandler(cost_threshold_usd=0.001)

        expensive_opportunity = {
            'opportunity_id': 'expensive_test',
            'cost_tracking': {
                'total_cost_usd': 0.005,  # Exceeds threshold
                'total_tokens': 2000,
                'model_used': 'claude-haiku-4.5',
                'provider': 'openrouter',
                'prompt_tokens': 1400,
                'completion_tokens': 600,
                'input_cost_usd': 0.0014,
                'output_cost_usd': 0.0036,
                'latency_seconds': 2.0,
                'timestamp': datetime.utcnow().isoformat()
            }
        }

        is_valid, summary = handler.validate_batch_costs([expensive_opportunity])
        assert not is_valid, "Batch exceeding threshold should be invalid"
        assert summary['exceeds_threshold']
        assert any("exceeds threshold" in error for error in summary['validation_errors'])

    def test_sanitize_cost_data(self):
        """Test cost data sanitization"""
        handler = CostTrackingErrorHandler()

        dirty_data = {
            'model_used': 'claude-haiku-4.5',
            'provider': 'openrouter',
            'prompt_tokens': '850',  # String instead of int
            'completion_tokens': 350.0,  # Float instead of int
            'total_tokens': 1000,  # Wrong total
            'input_cost_usd': '0.00085',  # String instead of float
            'output_cost_usd': 0.00175,
            'total_cost_usd': 0.003,  # Wrong total
            'latency_seconds': '1.234'  # String instead of float
        }

        sanitized = handler.sanitize_cost_data(dirty_data)

        # Check that numeric fields are properly typed
        assert isinstance(sanitized['prompt_tokens'], int)
        assert isinstance(sanitized['completion_tokens'], int)
        assert isinstance(sanitized['total_tokens'], int)
        assert isinstance(sanitized['input_cost_usd'], float)
        assert isinstance(sanitized['output_cost_usd'], float)
        assert isinstance(sanitized['total_cost_usd'], float)
        assert isinstance(sanitized['latency_seconds'], float)

        # Check that totals are recalculated correctly
        assert sanitized['total_tokens'] == sanitized['prompt_tokens'] + sanitized['completion_tokens']
        assert abs(sanitized['total_cost_usd'] - (sanitized['input_cost_usd'] + sanitized['output_cost_usd'])) < 0.000001

    def test_handle_validation_error_recovery(self):
        """Test recovery from validation errors"""
        handler = CostTrackingErrorHandler()

        opportunities_with_invalid_data = [
            {
                'opportunity_id': 'invalid_1',
                'cost_tracking': {
                    'model_used': 'claude-haiku-4.5',
                    'total_cost_usd': -0.001,  # Negative cost
                    'total_tokens': 1000
                }
            }
        ]

        should_retry, recovered = handler._handle_validation_error(opportunities_with_invalid_data)

        assert should_retry, "Should attempt recovery from validation error"
        assert len(recovered) == 1
        # Cost data should be removed or sanitized
        assert 'cost_tracking' not in recovered[0] or recovered[0]['cost_tracking']['total_cost_usd'] >= 0


class TestDLTCostTracking:
    """Test cases for DLT cost tracking functionality"""

    def test_validate_cost_data_function(self):
        """Test the standalone cost data validation function"""
        valid_cost_data = {
            'model_used': 'claude-haiku-4.5',
            'total_tokens': 1200,
            'total_cost_usd': 0.0026,
            'timestamp': datetime.utcnow().isoformat()
        }

        validation = validate_cost_data([valid_cost_data])

        assert validation['total_opportunities'] == 1
        assert validation['with_cost_data'] == 1
        assert validation['without_cost_data'] == 0
        assert validation['invalid_cost_data'] == 0
        assert validation['total_cost_usd'] == 0.0026
        assert validation['total_tokens'] == 1200
        assert len(validation['errors']) == 0

    def test_generate_cost_report(self):
        """Test cost report generation"""
        opportunities = [
            {
                'opportunity_id': 'test_1',
                'cost_tracking': {
                    'model_used': 'claude-haiku-4.5',
                    'total_cost_usd': 0.002,
                    'total_tokens': 1000,
                    'latency_seconds': 1.0
                }
            },
            {
                'opportunity_id': 'test_2',
                'cost_tracking': {
                    'model_used': 'gpt-4o-mini',
                    'total_cost_usd': 0.001,
                    'total_tokens': 800,
                    'latency_seconds': 0.8
                }
            },
            {
                'opportunity_id': 'test_3',
                # No cost data
            }
        ]

        report = generate_cost_report(opportunities, "Test Report")

        assert report['title'] == "Test Report"
        assert report['summary']['total_opportunities'] == 3
        assert report['summary']['with_cost_data'] == 2
        assert report['summary']['cost_tracking_coverage'] == 2/3 * 100
        assert report['summary']['total_cost_usd'] == 0.003
        assert report['summary']['total_tokens'] == 1800
        assert len(report['model_breakdown']) == 2

        # Check model breakdown
        assert 'claude-haiku-4.5' in report['model_breakdown']
        assert 'gpt-4o-mini' in report['model_breakdown']
        assert report['model_breakdown']['claude-haiku-4.5']['count'] == 1
        assert report['model_breakdown']['gpt-4o-mini']['count'] == 1

    def test_workflow_results_with_cost_tracking_resource(self):
        """Test the DLT resource for workflow results with cost tracking"""
        opportunities = [
            {
                'opportunity_id': 'test_1',
                'app_name': 'TestApp',
                'function_count': 2,
                'final_score': 75.0,
                'status': 'scored',
                'cost_tracking': {
                    'model_used': 'claude-haiku-4.5',
                    'provider': 'openrouter',
                    'prompt_tokens': 850,
                    'completion_tokens': 350,
                    'total_tokens': 1200,
                    'input_cost_usd': 0.00085,
                    'output_cost_usd': 0.00175,
                    'total_cost_usd': 0.0026,
                    'latency_seconds': 1.234,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
        ]

        # Test the resource function
        resource_results = list(workflow_results_with_cost_tracking(opportunities))

        assert len(resource_results) == 1
        enhanced_opp = resource_results[0]

        # Check that cost tracking fields are properly mapped
        assert enhanced_opp['llm_model_used'] == 'claude-haiku-4.5'
        assert enhanced_opp['llm_provider'] == 'openrouter'
        assert enhanced_opp['llm_total_tokens'] == 1200
        assert enhanced_opp['llm_total_cost_usd'] == 0.0026
        assert enhanced_opp['cost_tracking_enabled'] is True

    def test_workflow_results_without_cost_tracking(self):
        """Test handling of opportunities without cost tracking data"""
        opportunities = [
            {
                'opportunity_id': 'no_cost_1',
                'app_name': 'NoCostApp',
                'function_count': 1,
                'final_score': 60.0,
                'status': 'scored'
                # No cost_tracking field
            }
        ]

        resource_results = list(workflow_results_with_cost_tracking(opportunities))

        assert len(resource_results) == 1
        enhanced_opp = resource_results[0]

        # Check that cost tracking fields are set to defaults
        assert enhanced_opp['llm_model_used'] is None
        assert enhanced_opp['llm_provider'] == 'openrouter'
        assert enhanced_opp['llm_total_tokens'] == 0
        assert enhanced_opp['llm_total_cost_usd'] == 0.0
        assert enhanced_opp['cost_tracking_enabled'] is False


class TestIntegration:
    """Integration tests for cost tracking"""

    def test_validate_and_handle_costs_success(self):
        """Test successful validation and handling of costs"""
        opportunities = [
            {
                'opportunity_id': 'integration_test',
                'cost_tracking': {
                    'model_used': 'claude-haiku-4.5',
                    'provider': 'openrouter',
                    'prompt_tokens': 500,
                    'completion_tokens': 300,
                    'total_tokens': 800,
                    'input_cost_usd': 0.0005,
                    'output_cost_usd': 0.0015,
                    'total_cost_usd': 0.002,
                    'latency_seconds': 1.0,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
        ]

        success, processed_opps, summary = validate_and_handle_costs(opportunities, max_cost_usd=0.01)

        assert success, "Validation should succeed for valid data"
        assert len(processed_opps) == 1
        assert summary['total_cost_usd'] == 0.002

    def test_validate_and_handle_costs_with_recovery(self):
        """Test cost validation with error recovery"""
        opportunities = [
            {
                'opportunity_id': 'recovery_test',
                'cost_tracking': {
                    'model_used': 'claude-haiku-4.5',
                    'total_cost_usd': -0.001,  # Invalid negative cost
                    'total_tokens': 1000
                    # Missing other required fields
                }
            }
        ]

        success, processed_opps, summary = validate_and_handle_costs(opportunities, max_cost_usd=0.01)

        # Should succeed after recovery (cost data removed)
        assert success, "Should recover from validation errors"
        assert len(processed_opps) == 1
        # Cost data should be removed during recovery
        assert 'cost_tracking' not in processed_opps[0]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])