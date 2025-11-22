#!/usr/bin/env python3
"""
Enhanced Metrics Collection for Complete Enrichment Data Validation

This module provides enhanced field coverage calculation that checks for
expected enrichment fields across multiple database tables, not just the
main enriched submission dictionary.

Key Features:
- Checks field coverage across app_opportunities AND specialized enrichment tables
- Queries specialized tables directly for complete field validation
- Provides accurate 90%+ field coverage calculation
- Supports the test validation requirements

Problem Solved:
- Original field coverage only checked main dictionary, missing specialized table data
- Test failed because it looked for fields in wrong locations
- Now queries opportunity_scores, market_validations, monetization_patterns, competitive_landscape

Created: 2025-11-22
Author: RedditHarbor Data Engineering Team
"""

import logging
from typing import Any, Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Complete expected enrichment fields with their source locations
EXPECTED_ENRICHMENT_FIELDS = {
    # From app_opportunities table (main enriched data)
    "opportunity_score": "app_opportunities",
    "final_score": "app_opportunities",
    "dimension_scores": "app_opportunities",
    "priority": "app_opportunities",
    "core_functions": "app_opportunities",
    "problem_description": "app_opportunities",
    "target_user": "app_opportunities",

    # Profiler fields from app_opportunities
    "profession": "app_opportunities",
    "ai_profile": "app_opportunities",
    "evidence_based": "app_opportunities",
    "confidence": "app_opportunities",
    "app_name": "app_opportunities",
    "app_category": "app_opportunities",
    "core_problems": "app_opportunities",

    # Monetization fields from app_opportunities + monetization_patterns
    "monetization_score": "app_opportunities",
    "monetization_methods": "app_opportunities",  # Could be derived
    "willingness_to_pay_score": "monetization_patterns",
    "customer_segment": "monetization_patterns",
    "price_sensitivity_score": "monetization_patterns",
    "revenue_potential_score": "monetization_patterns",

    # Trust fields from app_opportunities
    "trust_level": "app_opportunities",
    "overall_trust_score": "app_opportunities",
    "trust_badges": "app_opportunities",
    "activity_validation_score": "app_opportunities",  # Could be derived
    "problem_authenticity_score": "app_opportunities",  # Could be derived
    "solution_readiness_score": "app_opportunities",  # Could be derived

    # Market validation fields from market_validations table
    "market_validation_score": "market_validations",
    "market_data_quality": "market_validations",
    "competitor_count": "market_validations",
    "market_size_estimate": "market_validations",
    "similar_launches_count": "market_validations",
    "validation_reasoning": "market_validations",
}


def calculate_enhanced_field_coverage(
    enriched_submission: Dict[str, Any],
    supabase_client,
    submission_id: str
) -> Tuple[float, List[str]]:
    """
    Calculate comprehensive field coverage across all enrichment tables.

    Checks for expected fields not just in the main submission dictionary,
    but also queries the specialized enrichment tables directly.

    Args:
        enriched_submission: Main enriched submission dictionary
        supabase_client: Supabase client for database queries
        submission_id: Submission ID to query specialized tables

    Returns:
        Tuple of (coverage_percentage, list_of_populated_fields)
    """
    populated_fields = []
    total_fields = len(EXPECTED_ENRICHMENT_FIELDS)

    if total_fields == 0:
        return 0.0, []

    logger.info(f"Calculating enhanced field coverage for {submission_id}")
    logger.info(f"Total expected fields: {total_fields}")

    # Step 1: Check fields in main enriched submission (app_opportunities data)
    for field_name, source_table in EXPECTED_ENRICHMENT_FIELDS.items():
        if source_table == "app_opportunities":
            # Check in main submission dictionary
            value = enriched_submission.get(field_name)
            if _is_field_populated(value):
                populated_fields.append(field_name)
                logger.debug(f"✓ Found {field_name} in main submission")

    # Step 2: Query specialized enrichment tables if supabase_client available
    if supabase_client:
        try:
            # Get opportunity_id from the opportunities table (not app_opportunities)
            # The opportunities table links submissions to enrichment data via opportunity_id
            opportunity_data = supabase_client.table("opportunities")\
                .select("id").eq("submission_id", submission_id).execute()

            opportunity_id = None
            if opportunity_data.data and len(opportunity_data.data) > 0:
                opportunity_id = opportunity_data.data[0]["id"]
                logger.info(f"Found opportunity_id: {opportunity_id}")
            else:
                logger.warning(f"No opportunity_id found in opportunities table for submission {submission_id}")

            if opportunity_id:
                # Check monetization_patterns table
                monetization_data = supabase_client.table("monetization_patterns")\
                    .select("*").eq("opportunity_id", opportunity_id).execute()

                if monetization_data.data and len(monetization_data.data) > 0:
                    record = monetization_data.data[0]
                    for field_name, source_table in EXPECTED_ENRICHMENT_FIELDS.items():
                        if source_table == "monetization_patterns" and field_name not in populated_fields:
                            if _is_field_populated(record.get(field_name)):
                                populated_fields.append(field_name)
                                logger.debug(f"✓ Found {field_name} in monetization_patterns")

                # Check market_validations table
                market_data = supabase_client.table("market_validations")\
                    .select("*").eq("opportunity_id", opportunity_id).execute()

                if market_data.data and len(market_data.data) > 0:
                    record = market_data.data[0]
                    for field_name, source_table in EXPECTED_ENRICHMENT_FIELDS.items():
                        if source_table == "market_validations" and field_name not in populated_fields:
                            if _is_field_populated(record.get(field_name)):
                                populated_fields.append(field_name)
                                logger.debug(f"✓ Found {field_name} in market_validations")

                # Check competitive_landscape table for competitor count
                competitive_data = supabase_client.table("competitive_landscape")\
                    .select("count").eq("opportunity_id", opportunity_id).execute()

                competitor_count = len(competitive_data.data) if competitive_data.data else 0
                if competitor_count > 0 and "competitor_count" not in populated_fields:
                    populated_fields.append("competitor_count")
                    logger.debug(f"✓ Found competitor_count ({competitor_count}) in competitive_landscape")

        except Exception as e:
            logger.error(f"Error querying specialized tables: {e}")

    # Calculate coverage percentage
    coverage = (len(populated_fields) / total_fields) * 100

    logger.info(f"Field coverage calculation complete:")
    logger.info(f"  Populated fields: {len(populated_fields)}/{total_fields}")
    logger.info(f"  Coverage: {coverage:.1f}%")

    if coverage < 90:
        logger.warning(f"Field coverage below target: {coverage:.1f}% < 90%")
        missing_fields = set(EXPECTED_ENRICHMENT_FIELDS.keys()) - set(populated_fields)
        logger.warning(f"Missing fields: {missing_fields}")

    return coverage, populated_fields


def _is_field_populated(value: Any) -> bool:
    """
    Check if a field value is considered populated.

    Args:
        value: Field value to check

    Returns:
        bool: True if field is populated (not None, not empty string, not empty list)
    """
    if value is None:
        return False
    if value == "":
        return False
    if isinstance(value, (list, dict)) and len(value) == 0:
        return False
    return True


def generate_enhanced_coverage_report(
    enriched_submissions: List[Dict[str, Any]],
    supabase_client,
    submission_ids: List[str]
) -> Dict[str, Any]:
    """
    Generate comprehensive field coverage report for multiple submissions.

    Args:
        enriched_submissions: List of enriched submission dictionaries
        supabase_client: Supabase client for database queries
        submission_ids: List of submission IDs to analyze

    Returns:
        dict: Comprehensive coverage report
    """
    total_submissions = len(enriched_submissions)
    if total_submissions == 0:
        return {
            "total_submissions": 0,
            "avg_coverage": 0.0,
            "submissions_meeting_target": 0,
            "field_coverage_by_submission": {},
            "overall_field_popularity": {}
        }

    coverage_results = []
    field_popularity = {field: 0 for field in EXPECTED_ENRICHMENT_FIELDS.keys()}

    for i, enriched_submission in enumerate(enriched_submissions):
        submission_id = submission_ids[i] if i < len(submission_ids) else "unknown"

        coverage, populated_fields = calculate_enhanced_field_coverage(
            enriched_submission, supabase_client, submission_id
        )

        coverage_results.append({
            "submission_id": submission_id,
            "coverage": coverage,
            "populated_fields": populated_fields,
            "meets_target": coverage >= 90
        })

        # Track field popularity
        for field in populated_fields:
            if field in field_popularity:
                field_popularity[field] += 1

    # Calculate aggregates
    avg_coverage = sum(r["coverage"] for r in coverage_results) / total_submissions
    submissions_meeting_target = sum(1 for r in coverage_results if r["meets_target"])

    # Calculate field popularity percentages
    field_popularity_pct = {
        field: (count / total_submissions * 100)
        for field, count in field_popularity.items()
    }

    return {
        "total_submissions": total_submissions,
        "avg_coverage": avg_coverage,
        "submissions_meeting_target": submissions_meeting_target,
        "target_success_rate": (submissions_meeting_target / total_submissions * 100),
        "field_coverage_by_submission": {
            r["submission_id"]: {
                "coverage": r["coverage"],
                "populated_fields": r["populated_fields"],
                "meets_target": r["meets_target"]
            }
            for r in coverage_results
        },
        "overall_field_popularity": field_popularity_pct,
        "least_popular_fields": sorted(
            field_popularity_pct.items(),
            key=lambda x: x[1]
        )[:10]  # Top 10 least populated fields
    }


def validate_enrichment_tables_populated(
    supabase_client,
    submission_id: str
) -> Dict[str, bool]:
    """
    Validate that all expected enrichment tables have data for a submission.

    Args:
        supabase_client: Supabase client for database queries
        submission_id: Submission ID to validate

    Returns:
        dict: Table validation results
    """
    results = {
        "app_opportunities": False,
        "opportunity_scores": False,
        "monetization_patterns": False,
        "market_validations": False,
        "competitive_landscape": False,
    }

    try:
        # Check app_opportunities (doesn't have id column, check for submission_id existence)
        app_data = supabase_client.table("app_opportunities")\
            .select("submission_id").eq("submission_id", submission_id).execute()
        results["app_opportunities"] = bool(app_data.data and len(app_data.data) > 0)

        # Get opportunity_id from the opportunities table for checking enrichment tables
        opp_data = supabase_client.table("opportunities")\
            .select("id").eq("submission_id", submission_id).execute()

        if opp_data.data and len(opp_data.data) > 0:
            opportunity_id = opp_data.data[0]["id"]

            # Check specialized tables
            tables_to_check = [
                "opportunity_scores",
                "monetization_patterns",
                "market_validations",
                "competitive_landscape"
            ]

            for table in tables_to_check:
                try:
                    data = supabase_client.table(table)\
                        .select("count").eq("opportunity_id", opportunity_id).execute()
                    results[table] = bool(data.data and len(data.data) > 0)
                except Exception as e:
                    logger.warning(f"Could not check table {table}: {e}")
                    results[table] = False

    except Exception as e:
        logger.error(f"Error validating enrichment tables: {e}")

    return results