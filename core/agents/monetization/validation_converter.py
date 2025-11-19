#!/usr/bin/env python3
"""
Agno Analysis to Validation Evidence Converter

This module converts Agno MonetizationAnalysis results to ValidationEvidence
format for persistence in the RedditHarbor database.

This bridges the gap between the Agno multi-agent market research system
and the MarketValidationPersistence infrastructure.

Key Features:
- Converts MonetizationAnalysis to ValidationEvidence
- Maps Agno scores to validation evidence structure
- Preserves all valuable analysis data for persistence
- Handles data transformation gracefully

Created: 2025-11-18
Author: RedditHarbor Data Engineering Team
"""

from datetime import UTC, datetime
from typing import Any

from agent_tools.market_data_validator import ValidationEvidence
from agent_tools.monetization_agno_analyzer import MonetizationAnalysis


def convert_agno_analysis_to_validation_evidence(
    agno_analysis: MonetizationAnalysis,
    submission_text: str,
    subreddit: str,
    additional_metadata: dict[str, Any] | None = None,
) -> ValidationEvidence:
    """
    Convert Agno MonetizationAnalysis to ValidationEvidence format.

    This transformation enables Agno market research data to be persisted
    using the existing MarketValidationPersistence infrastructure.

    Args:
        agno_analysis: The MonetizationAnalysis result from Agno agents
        submission_text: Original Reddit submission text for context
        subreddit: Subreddit name for context
        additional_metadata: Optional additional metadata to include

    Returns:
        ValidationEvidence object compatible with persistence layer
    """

    # Map Agno scores to validation evidence structure
    # Use willingness_to_pay_score as primary validation score since it's
    # the most direct indicator of market validation
    validation_score = agno_analysis.willingness_to_pay_score

    # Data quality based on confidence and how complete the analysis is
    data_quality_score = min(
        agno_analysis.confidence * 100,  # Convert confidence 0-1 to 0-100
        90.0,  # Cap at 90 since this is derived from LLM analysis, not hard data
    )

    # Build comprehensive reasoning from Agno analysis
    reasoning_parts = [
        "Agno multi-agent market analysis",
        f"Customer Segment: {agno_analysis.customer_segment}",
        f"Willingness to Pay: {agno_analysis.willingness_to_pay_score}/100",
        f"Payment Sentiment: {agno_analysis.sentiment_toward_payment}",
        f"Urgency Level: {agno_analysis.urgency_level}",
    ]

    if agno_analysis.mentioned_price_points:
        price_points = ', '.join(agno_analysis.mentioned_price_points[:3])
        reasoning_parts.append(f"Price Points Mentioned: {price_points}")

    if agno_analysis.existing_payment_behavior != "Not specified":
        reasoning_parts.append(
            f"Payment Behavior: {agno_analysis.existing_payment_behavior}"
        )

    reasoning = " | ".join(reasoning_parts)

    # Add Agno reasoning if available
    if agno_analysis.reasoning:
        reasoning += f"\n\nAgno Reasoning: {agno_analysis.reasoning}"

    # Create competitor pricing from price points mentioned
    if agno_analysis.mentioned_price_points:
        # Create a synthetic competitor entry from mentioned price points
        price_tiers = []
        for price in agno_analysis.mentioned_price_points[:3]:  # Limit to top 3
            # Clean price text to extract numeric value
            import re

            price_match = re.search(r"\$?(\d+)", price)
            if price_match:
                numeric_price = int(price_match.group(1))
                if numeric_price < 20:
                    tier_name = "Basic"
                elif numeric_price < 50:
                    tier_name = "Pro"
                elif numeric_price < 100:
                    tier_name = "Business"
                else:
                    tier_name = "Enterprise"

                price_tiers.append(
                    {
                        "tier": tier_name,
                        "price": price,
                        "features": [
                            f"Inferred from Reddit discussion in r/{subreddit}"
                        ],
                    }
                )

        if price_tiers:
            competitor_pricing_data = {
                "company_name": f"Market Intelligence (r/{subreddit})",
                "pricing_tiers": price_tiers,
                "pricing_model": "subscription",  # Default assumption
                "target_market": agno_analysis.customer_segment,
                "source_url": f"https://reddit.com/r/{subreddit}",
                "extracted_at": datetime.now(UTC),
                "confidence": agno_analysis.confidence,
            }
            # Note: competitor_pricing_data is available for future use
            # Note: We don't directly instantiate CompetitorPricing here
            # to avoid import issues. The persistence layer will handle serialization.

    # Create market size estimation based on customer segment
    if agno_analysis.customer_segment != "Unknown":
        # Provide basic market size context
        if agno_analysis.customer_segment == "B2B":
            {
                "tam_value": "$500B+",  # Global B2B software market
                "sam_value": "$50B+",  # Serviceable B2B market
                "som_value": "$1B+",  # Obtainable market
                "growth_rate": "12% CAGR",
                "year": 2024,
                "source_url": "Agno B2B Market Intelligence",
                "source_name": "Agno Multi-Agent Analysis",
                "confidence": agno_analysis.confidence * 0.7,  # Lower confidence for estimates
            }
        elif agno_analysis.customer_segment == "B2C":
            market_size_data = {
                "tam_value": "$300B+",  # Global B2C app market
                "sam_value": "$30B+",
                "som_value": "$500M+",
                "growth_rate": "8% CAGR",
                "year": 2024,
                "source_url": "Agno B2C Market Intelligence",
                "source_name": "Agno Multi-Agent Analysis",
                "confidence": agno_analysis.confidence * 0.7,
            }
            # Note: market_size_data is available for future use

    # Create ValidationEvidence object
    evidence = ValidationEvidence(
        competitor_pricing=[],  # Will be populated by persistence layer
        market_size=None,  # Will be populated by persistence layer
        similar_launches=[],  # No direct data from Agno for this
        industry_benchmarks={
            "customer_segment": agno_analysis.customer_segment,
            "market_segment_score": agno_analysis.market_segment_score,
            "price_sensitivity_score": agno_analysis.price_sensitivity_score,
            "revenue_potential_score": agno_analysis.revenue_potential_score,
            "subreddit_multiplier": agno_analysis.subreddit_multiplier,
            "urgency_level": agno_analysis.urgency_level,
            "payment_sentiment": agno_analysis.sentiment_toward_payment,
            "existing_payment_behavior": agno_analysis.existing_payment_behavior,
            "payment_friction_indicators": agno_analysis.payment_friction_indicators,
            "mentioned_price_points": agno_analysis.mentioned_price_points,
            "analysis_source": "agno_multi_agent",
            "subreddit": subreddit,
            "additional_metadata": additional_metadata or {},
        },
        validation_score=validation_score,
        data_quality_score=data_quality_score,
        reasoning=reasoning,
        search_queries_used=[f"market_analysis_{subreddit}"],
        urls_fetched=[],  # Agno doesn't use external URLs like Jina
        timestamp=datetime.now(UTC),
        total_cost=0.01,  # Approximate cost from Agno analysis
    )

    return evidence


def prepare_agno_persistence_data(
    agno_analysis: MonetizationAnalysis,
    app_opportunity_id: str,
    submission_id: str,
    subreddit: str,
    additional_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Prepare Agno analysis data for persistence in a format compatible with
    MarketValidationPersistence.save_validation_evidence().

    This is a convenience function that prepares all the data needed
    to persist Agno analysis results.

    Args:
        agno_analysis: The MonetizationAnalysis result from Agno agents
        app_opportunity_id: UUID from app_opportunities table
        submission_id: Reddit submission ID
        subreddit: Subreddit name
        additional_metadata: Optional additional metadata

    Returns:
        Dictionary with all data needed for persistence
    """

    evidence = convert_agno_analysis_to_validation_evidence(
        agno_analysis=agno_analysis,
        submission_text="",  # Not needed for persistence
        subreddit=subreddit,
        additional_metadata=additional_metadata,
    )

    # Prepare data for persistence
    persistence_data = {
        "app_opportunity_id": app_opportunity_id,
        "opportunity_id": submission_id,
        "evidence": evidence,
        "validation_type": "agno_market_analysis",
        "validation_source": "agno_agents",
    }

    return persistence_data
