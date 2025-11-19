#!/usr/bin/env python3
"""
DLT Cost Tracking Integration
Enhanced DLT pipeline with comprehensive cost tracking for LLM operations
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import dlt

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import SUPABASE_KEY, SUPABASE_URL
from core.dlt import PK_OPPORTUNITY_ID


@dlt.resource(
    name="workflow_results_with_costs",
    write_disposition="merge",
    primary_key=PK_OPPORTUNITY_ID
)
def workflow_results_with_cost_tracking(opportunities: list[dict[str, Any]]):
    """
    DLT resource for loading workflow results with cost tracking.

    This resource enhances the standard workflow_results data with comprehensive
    cost tracking information from LLM operations.
    """
    enhanced_opportunities = []

    for opp in opportunities:
        enhanced_opp = opp.copy()

        # Extract cost tracking data if available
        cost_data = opp.get('cost_tracking', {})

        # Map cost data to database columns
        enhanced_opp.update({
            'llm_model_used': cost_data.get('model_used'),
            'llm_provider': cost_data.get('provider', 'openrouter'),
            'llm_prompt_tokens': cost_data.get('prompt_tokens', 0),
            'llm_completion_tokens': cost_data.get('completion_tokens', 0),
            'llm_total_tokens': cost_data.get('total_tokens', 0),
            'llm_input_cost_usd': cost_data.get('input_cost_usd', 0.0),
            'llm_output_cost_usd': cost_data.get('output_cost_usd', 0.0),
            'llm_total_cost_usd': cost_data.get('total_cost_usd', 0.0),
            'llm_latency_seconds': cost_data.get('latency_seconds', 0.0),
            'llm_timestamp': cost_data.get('timestamp'),
            'llm_pricing_info': cost_data.get('model_pricing_per_m_tokens', {}),
            'cost_tracking_enabled': bool(cost_data)
        })

        enhanced_opportunities.append(enhanced_opp)

    yield enhanced_opportunities


@dlt.source
def cost_tracking_source():
    """
    DLT source with cost tracking capabilities.
    """
    return {
        "workflow_results": workflow_results_with_cost_tracking,
    }


def create_cost_tracking_pipeline() -> dlt.Pipeline:
    """
    Create a DLT pipeline with cost tracking enabled.

    Returns:
        Configured DLT pipeline instance
    """
    pipeline = dlt.pipeline(
        pipeline_name="reddit_harbor_cost_tracking",
        destination="postgres",
        dataset_name="reddit_harbor",
        credentials={
            "host": SUPABASE_URL.replace("https://", "").replace("/rest/v1/", ""),
            "port": 54322,
            "user": "postgres",
            "password": SUPABASE_KEY,
            "database": "postgres"
        }
    )

    return pipeline


def load_opportunities_with_costs(
    opportunities: list[dict[str, Any]],
    pipeline: dlt.Pipeline | None = None
) -> dict[str, Any]:
    """
    Load opportunities with cost tracking to Supabase.

    Args:
        opportunities: List of opportunity dictionaries with cost tracking data
        pipeline: Optional existing DLT pipeline

    Returns:
        Load information from DLT
    """
    if pipeline is None:
        pipeline = create_cost_tracking_pipeline()

    # Load with cost tracking
    load_info = pipeline.run(
        cost_tracking_source().workflow_results_with_costs(opportunities),
        write_disposition="merge",
        primary_key=PK_OPPORTUNITY_ID
    )

    return load_info


def validate_cost_data(opportunities: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Validate cost tracking data in opportunities.

    Args:
        opportunities: List of opportunity dictionaries

    Returns:
        Validation results
    """
    validation_results = {
        'total_opportunities': len(opportunities),
        'with_cost_data': 0,
        'without_cost_data': 0,
        'invalid_cost_data': 0,
        'total_cost_usd': 0.0,
        'total_tokens': 0,
        'errors': []
    }

    for opp in opportunities:
        cost_data = opp.get('cost_tracking', {})

        if cost_data:
            validation_results['with_cost_data'] += 1

            # Validate cost data structure
            required_fields = [
                'model_used', 'total_tokens', 'total_cost_usd', 'timestamp'
            ]

            missing_fields = [field for field in required_fields if field not in cost_data]
            if missing_fields:
                validation_results['invalid_cost_data'] += 1
                validation_results['errors'].append(
                    f"Opportunity {opp.get('opportunity_id', 'unknown')} missing cost fields: {missing_fields}"
                )
                continue

            # Aggregate totals
            total_cost = cost_data.get('total_cost_usd', 0.0)
            total_tokens = cost_data.get('total_tokens', 0)

            if not isinstance(total_cost, (int, float)) or total_cost < 0:
                validation_results['errors'].append(
                    f"Invalid cost value for opportunity {opp.get('opportunity_id', 'unknown')}: {total_cost}"
                )
                continue

            if not isinstance(total_tokens, int) or total_tokens < 0:
                validation_results['errors'].append(
                    f"Invalid token count for opportunity {opp.get('opportunity_id', 'unknown')}: {total_tokens}"
                )
                continue

            validation_results['total_cost_usd'] += total_cost
            validation_results['total_tokens'] += total_tokens
        else:
            validation_results['without_cost_data'] += 1

    return validation_results


def generate_cost_report(
    opportunities: list[dict[str, Any]],
    title: str = "Cost Tracking Report"
) -> dict[str, Any]:
    """
    Generate comprehensive cost tracking report.

    Args:
        opportunities: List of opportunity dictionaries with cost data
        title: Report title

    Returns:
        Cost tracking report
    """
    validation = validate_cost_data(opportunities)

    # Model breakdown
    model_usage = {}
    for opp in opportunities:
        cost_data = opp.get('cost_tracking', {})
        if cost_data:
            model = cost_data.get('model_used', 'unknown')
            if model not in model_usage:
                model_usage[model] = {
                    'count': 0,
                    'total_cost': 0.0,
                    'total_tokens': 0,
                    'avg_latency': 0.0,
                    'latency_sum': 0.0
                }

            model_usage[model]['count'] += 1
            model_usage[model]['total_cost'] += cost_data.get('total_cost_usd', 0.0)
            model_usage[model]['total_tokens'] += cost_data.get('total_tokens', 0)
            model_usage[model]['latency_sum'] += cost_data.get('latency_seconds', 0.0)

    # Calculate averages
    for model, stats in model_usage.items():
        if stats['count'] > 0:
            stats['avg_cost_per_profile'] = stats['total_cost'] / stats['count']
            stats['avg_tokens_per_profile'] = stats['total_tokens'] / stats['count']
            stats['avg_latency'] = stats['latency_sum'] / stats['count']
            stats['cost_per_1k_tokens'] = (stats['total_cost'] / stats['total_tokens']) * 1000 if stats['total_tokens'] > 0 else 0.0

    # Generate report
    report = {
        'title': title,
        'generated_at': datetime.utcnow().isoformat(),
        'summary': {
            'total_opportunities': validation['total_opportunities'],
            'with_cost_data': validation['with_cost_data'],
            'cost_tracking_coverage': (validation['with_cost_data'] / validation['total_opportunities']) * 100 if validation['total_opportunities'] > 0 else 0,
            'total_cost_usd': round(validation['total_cost_usd'], 6),
            'total_tokens': validation['total_tokens'],
            'avg_cost_per_profile': round(validation['total_cost_usd'] / validation['with_cost_data'], 6) if validation['with_cost_data'] > 0 else 0,
            'validation_errors': len(validation['errors'])
        },
        'model_breakdown': model_usage,
        'validation_errors': validation['errors'][:10]  # Limit to first 10 errors
    }

    return report


# Example usage and testing
if __name__ == "__main__":
    # Test data with cost tracking
    test_opportunities = [
        {
            "opportunity_id": "test_1",
            "app_name": "TestApp",
            "function_count": 2,
            "final_score": 75.0,
            "status": "scored",
            "cost_tracking": {
                "model_used": "claude-haiku-4.5",
                "provider": "openrouter",
                "prompt_tokens": 850,
                "completion_tokens": 350,
                "total_tokens": 1200,
                "input_cost_usd": 0.00085,
                "output_cost_usd": 0.00175,
                "total_cost_usd": 0.0026,
                "latency_seconds": 1.234,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    ]

    # Validate and generate report
    validation = validate_cost_data(test_opportunities)
    report = generate_cost_report(test_opportunities, "Test Cost Report")

    print("Validation Results:")
    for key, value in validation.items():
        print(f"  {key}: {value}")

    print("\nCost Report:")
    print(f"  Total Cost: ${report['summary']['total_cost_usd']:.6f}")
    print(f"  Coverage: {report['summary']['cost_tracking_coverage']:.1f}%")
    print(f"  Avg Cost per Profile: ${report['summary']['avg_cost_per_profile']:.6f}")
