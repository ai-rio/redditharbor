#!/usr/bin/env python3
"""
Batch Opportunity Scoring Script (DLT-Powered)
Processes all Reddit submissions in the database and scores them using the 5-dimensional methodology.

This script:
- Fetches all submissions from the Supabase database
- Maps subreddits to business sectors
- Scores opportunities using OpportunityAnalyzerAgent
- Stores results in opportunity_scores table via DLT pipeline (merge disposition)
- Provides progress tracking and summary statistics

Deduplication Integration for AI Analysis Components:
This module implements cost-saving deduplication logic for two expensive AI components:
1. Agno Monetization Analysis (multi-agent team, ~$0.10 per analysis)
2. AI App Profiling (EnhancedLLMProfiler, ~$0.005 per profile)

Key Deduplication Functions:
- should_run_agno_analysis(): Check if Agno should run or be skipped
- should_run_profiler_analysis(): Check if profiler should run or be skipped
- copy_agno_from_primary(): Copy Agno results from primary opportunity
- copy_profiler_from_primary(): Copy AI profile from primary opportunity
- update_concept_agno_stats(): Update concept metadata after Agno analysis
- update_concept_profiler_stats(): Update concept metadata after profiling

Expected ROI: 70% cost reduction ($3,528/year at 10K posts/month)
Data Quality: Consistent core_functions arrays, no semantic fragmentation

DLT Migration Benefits:
- Automatic deduplication (merge write disposition)
- Schema evolution support (automatic table updates)
- Production-ready deployment (Airflow integration)
- Consistent data loading pattern across all scripts

CRITICAL: Uses centralized score_calculator module for consistency.
"""

import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env.local
from dotenv import load_dotenv

load_dotenv(project_root / ".env.local")

# Import core functions serialization utilities
from core.utils.core_functions_serialization import standardize_core_functions
from core.dlt import PK_SUBMISSION_ID, PK_OPPORTUNITY_ID

try:
    from tqdm import tqdm
except ImportError:
    print("Warning: tqdm not installed. Installing for progress bars...")
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "tqdm"])
    from tqdm import tqdm

from core.agents.profiler import EnhancedLLMProfiler

# Hybrid strategy imports (Option A & B)
from core.agents.monetization.factory import get_monetization_analyzer
from core.agents.interactive import OpportunityAnalyzerAgent

# Market data validation (Phase 3: Data-Driven Validation)
from core.agents.market_validation import MarketDataValidator
from core.agents.market_validation.validator import ValidationEvidence
from config import SUPABASE_KEY, SUPABASE_URL

# DLT constraint validator
from core.dlt.constraint_validator import app_opportunities_with_constraint

# HTTP client configuration for connection pool management
from core.http_client_config import initialize_http_clients
from core.lead_extractor import LeadExtractor, convert_to_database_record

# Configure logging
logger = logging.getLogger(__name__)

# Hybrid Strategy Configuration
HYBRID_STRATEGY_CONFIG = {
    "option_a": {
        "enabled": os.getenv("MONETIZATION_LLM_ENABLED", "true").lower() == "true",
        "threshold": float(os.getenv("MONETIZATION_LLM_THRESHOLD", "60.0")),
        "model": os.getenv("MONETIZATION_LLM_MODEL", "openai/gpt-4o-mini"),
        "openrouter_key": os.getenv("OPENROUTER_API_KEY"),
    },
    "option_b": {
        "enabled": os.getenv("LEAD_EXTRACTION_ENABLED", "true").lower() == "true",
        "threshold": float(os.getenv("LEAD_EXTRACTION_THRESHOLD", "60.0")),
        "slack_webhook": os.getenv("SLACK_WEBHOOK_URL"),
    },
    "market_validation": {
        "enabled": os.getenv("MARKET_VALIDATION_ENABLED", "true").lower() == "true",
        "threshold": float(os.getenv("MARKET_VALIDATION_THRESHOLD", "60.0")),
        "jina_api_key": os.getenv("JINA_API_KEY", ""),
    },
}

# DLT imports for pipeline-based loading
# DLT opportunity pipeline
from supabase import create_client

# ============================================================================
# SUBREDDIT TO SECTOR MAPPING
# ============================================================================

SECTOR_MAPPING = {
    # Health & Fitness
    "fitness": "Health & Fitness",
    "loseit": "Health & Fitness",
    "bodyweightfitness": "Health & Fitness",
    "nutrition": "Health & Fitness",
    "healthyfood": "Health & Fitness",
    "yoga": "Health & Fitness",
    "running": "Health & Fitness",
    "weightlifting": "Health & Fitness",
    "xxfitness": "Health & Fitness",
    "progresspics": "Health & Fitness",
    "gainit": "Health & Fitness",
    "flexibility": "Health & Fitness",
    "naturalbodybuilding": "Health & Fitness",
    "eatcheapandhealthy": "Health & Fitness",
    "keto": "Health & Fitness",
    "cycling": "Health & Fitness",
    "meditation": "Health & Fitness",
    "mentalhealth": "Health & Fitness",
    "fitness30plus": "Health & Fitness",
    "homegym": "Health & Fitness",
    # Finance & Investing
    "personalfinance": "Finance & Investing",
    "financialindependence": "Finance & Investing",
    "investing": "Finance & Investing",
    "stocks": "Finance & Investing",
    "wallstreetbets": "Finance & Investing",
    "realestateinvesting": "Finance & Investing",
    "povertyfinance": "Finance & Investing",
    "frugal": "Finance & Investing",
    "fire": "Finance & Investing",
    "bogleheads": "Finance & Investing",
    "dividends": "Finance & Investing",
    "options": "Finance & Investing",
    "smallbusiness": "Finance & Investing",
    "cryptocurrency": "Finance & Investing",
    "tax": "Finance & Investing",
    "accounting": "Finance & Investing",
    "financialcareers": "Finance & Investing",
    # Education & Career
    "learnprogramming": "Education & Career",
    "cscareerquestions": "Education & Career",
    "careerguidance": "Education & Career",
    "resumes": "Education & Career",
    "jobs": "Education & Career",
    "studentloans": "Education & Career",
    "college": "Education & Career",
    "gradschool": "Education & Career",
    "teaching": "Education & Career",
    "entrepreneurs": "Education & Career",
    "startups": "Education & Career",
    # Travel & Experiences
    "travel": "Travel & Experiences",
    "solotravel": "Travel & Experiences",
    "digitalnomad": "Travel & Experiences",
    "backpacking": "Travel & Experiences",
    "roadtrip": "Travel & Experiences",
    "travel_hacks": "Travel & Experiences",
    "shoestring": "Travel & Experiences",
    "expats": "Travel & Experiences",
    "travelpartners": "Travel & Experiences",
    "budgettravel": "Travel & Experiences",
    "vagabond": "Travel & Experiences",
    # Real Estate
    "realestate": "Real Estate",
    "firsttimehomebuyer": "Real Estate",
    "homeimprovement": "Real Estate",
    "diy": "Real Estate",
    "homeowners": "Real Estate",
    "renters": "Real Estate",
    "mortgages": "Real Estate",
    "landlord": "Real Estate",
    "realestate_canada": "Real Estate",
    "housingmarkets": "Real Estate",
    # Technology & SaaS
    "saas": "Technology & SaaS",
    "indiehackers": "Technology & SaaS",
    "sidehustle": "Technology & SaaS",
    "juststart": "Technology & SaaS",
    "roastmystartup": "Technology & SaaS",
    "buildinpublic": "Technology & SaaS",
    "microsaas": "Technology & SaaS",
    "nocode": "Technology & SaaS",
    "webdev": "Technology & SaaS",
}


def map_subreddit_to_sector(subreddit: str) -> str:
    """
    Map a subreddit to its corresponding business sector.

    Args:
        subreddit: Name of the subreddit (case-insensitive)

    Returns:
        Sector name as string, defaults to "Technology & SaaS" if not found
    """
    if not subreddit:
        return "Technology & SaaS"

    subreddit_lower = subreddit.lower()
    return SECTOR_MAPPING.get(subreddit_lower, "Technology & SaaS")


def should_run_agno_analysis(
    submission: dict[str, Any], supabase: Any
) -> tuple[bool, str | None]:
    """
    Checks if Agno monetization analysis should run for a submission.
    Skips if it's a duplicate with existing Agno analysis.

    Args:
        submission: Submission data from app_opportunities table
        supabase: Initialized Supabase client

    Returns:
        Tuple of (should_run: bool, concept_id: str | None)
        - should_run: True if analysis should run, False if should skip/copy
        - concept_id: Business concept ID if duplicate found, None if unique
    """
    try:
        # Get submission_id for database lookup
        submission_id = submission.get("submission_id", submission.get("id"))
        if not submission_id:
            logger.warning(
                "Submission missing submission_id, defaulting to run Agno analysis"
            )
            return True, None

        # Check if submission has a business_concept_id (indicates it's a duplicate)
        # First try to get from opportunities_unified table
        try:
            response = (
                supabase.table("opportunities_unified")
                .select("business_concept_id")
                .eq("submission_id", submission_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                concept_id = response.data[0].get("business_concept_id")
                if concept_id:
                    # This is a duplicate opportunity, check if concept has Agno analysis
                    concept_response = (
                        supabase.table("business_concepts")
                        .select("has_agno_analysis")
                        .eq("id", concept_id)
                        .execute()
                    )

                    if concept_response.data and len(concept_response.data) > 0:
                        has_agno = concept_response.data[0].get(
                            "has_agno_analysis", False
                        )
                        logger.info(
                            f"Submission {submission_id} is duplicate of concept {concept_id}, has_agno_analysis={has_agno}"
                        )
                        return not has_agno, str(
                            concept_id
                        )  # Skip if has Agno, run if no Agno
                    else:
                        # Found concept but no concept data - assume no Agno
                        return True, str(concept_id)
        except Exception as db_error:
            logger.warning(
                f"Database error checking deduplication for {submission_id}: {db_error}"
            )
            # Default to running analysis if database check fails
            return True, None

        # If no business_concept_id found, this is a unique opportunity
        logger.debug(f"Submission {submission_id} is unique, should run Agno analysis")
        return True, None

    except Exception as e:
        logger.error(
            f"Error checking if should run Agno analysis for {submission.get('submission_id', 'unknown')}: {e}"
        )
        # Default to running analysis on errors
        return True, None


def copy_agno_from_primary(
    submission: dict[str, Any], concept_id: str, supabase: Any
) -> dict[str, Any]:
    """
    Copies Agno analysis results from primary opportunity for duplicate submissions.

    Args:
        submission: Current submission data (duplicate)
        concept_id: Business concept ID to find primary opportunity
        supabase: Initialized Supabase client

    Returns:
        Dictionary formatted for hybrid_results llm_analysis, or empty dict if copy fails
        Should contain all Agno analysis fields properly formatted
    """
    try:
        # Get the primary opportunity for this concept
        # Look for existing Agno analysis linked to this concept
        agno_response = (
            supabase.table("llm_monetization_analysis")
            .select("*")
            .eq("business_concept_id", concept_id)
            .eq("copied_from_primary", False)
            .execute()
        )

        # Handle test environment where Mock objects might be used
        if not hasattr(agno_response, "data") or agno_response.data is None:
            logger.warning(f"No Agno analysis response for concept {concept_id}")
            return {}

        # Handle both real data and Mock objects for testing
        try:
            # For real responses
            if isinstance(agno_response.data, (list, tuple)):
                data_list = agno_response.data
            else:
                # For Mock objects or other types
                data_list = (
                    list(agno_response.data)
                    if hasattr(agno_response.data, "__iter__")
                    else []
                )
        except (TypeError, AttributeError):
            # Handle Mock objects that don't support iteration
            logger.warning(
                f"Cannot iterate Agno analysis data for concept {concept_id}"
            )
            return {}

        if not data_list or len(data_list) == 0:
            # No primary Agno analysis found, try alternative lookup methods
            # Try to find by primary_opportunity_id
            concept_response = (
                supabase.table("business_concepts")
                .select("primary_opportunity_id")
                .eq("id", concept_id)
                .execute()
            )

            if (
                hasattr(concept_response, "data")
                and concept_response.data
                and len(concept_response.data) > 0
            ):
                primary_opp_id = concept_response.data[0].get("primary_opportunity_id")
                if primary_opp_id:
                    # Try to find Agno analysis for primary opportunity
                    agno_response = (
                        supabase.table("llm_monetization_analysis")
                        .select("*")
                        .eq("opportunity_id", primary_opp_id)
                        .execute()
                    )

                    if hasattr(agno_response, "data") and agno_response.data:
                        try:
                            if isinstance(agno_response.data, (list, tuple)):
                                data_list = agno_response.data
                            else:
                                data_list = (
                                    list(agno_response.data)
                                    if hasattr(agno_response.data, "__iter__")
                                    else []
                                )
                        except (TypeError, AttributeError):
                            data_list = []

            if not data_list or len(data_list) == 0:
                logger.warning(f"No Agno analysis found for concept {concept_id}")
                return {}

        # Get the primary Agno analysis (use the most recent if multiple)
        if len(data_list) == 1:
            primary_analysis = data_list[0]
        else:
            # Multiple analyses found, use the most recent
            try:
                primary_analysis = max(
                    data_list, key=lambda x: x.get("analyzed_at", "")
                )
            except (TypeError, AttributeError):
                # Fallback to first analysis if date comparison fails
                primary_analysis = data_list[0]

        # Create formatted llm_analysis dict for current submission
        submission_id = submission.get("submission_id", submission.get("id"))
        copied_analysis = {
            "opportunity_id": f"opp_{submission_id}",
            "submission_id": submission_id,
            "llm_monetization_score": primary_analysis.get("llm_monetization_score"),
            "keyword_monetization_score": primary_analysis.get(
                "keyword_monetization_score"
            ),
            "customer_segment": primary_analysis.get("customer_segment"),
            "willingness_to_pay_score": primary_analysis.get(
                "willingness_to_pay_score"
            ),
            "price_sensitivity_score": primary_analysis.get("price_sensitivity_score"),
            "revenue_potential_score": primary_analysis.get("revenue_potential_score"),
            "payment_sentiment": primary_analysis.get("payment_sentiment"),
            "urgency_level": primary_analysis.get("urgency_level"),
            "existing_payment_behavior": primary_analysis.get(
                "existing_payment_behavior"
            ),
            "mentioned_price_points": primary_analysis.get("mentioned_price_points"),
            "payment_friction_indicators": primary_analysis.get(
                "payment_friction_indicators"
            ),
            "confidence": primary_analysis.get("confidence"),
            "reasoning": primary_analysis.get("reasoning"),
            "subreddit_multiplier": primary_analysis.get("subreddit_multiplier"),
            "model_used": primary_analysis.get("model_used"),
            "score_delta": primary_analysis.get("score_delta"),
            # Add metadata indicating this is copied
            "copied_from_primary": True,
            "primary_opportunity_id": primary_analysis.get("opportunity_id"),
            "business_concept_id": concept_id,
            "copy_timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"Copied Agno analysis from primary for concept {concept_id} to submission {submission_id}"
        )
        return copied_analysis

    except Exception as e:
        logger.error(
            f"Error copying Agno analysis from primary for concept {concept_id}: {e}"
        )
        return {}


def update_concept_agno_stats(
    concept_id: str, agno_result: dict[str, Any], supabase: Any
) -> None:
    """
    Updates business concept with Agno analysis metadata.
    Tracks analysis count and running average for WTP scores.

    Args:
        concept_id: Business concept ID to update
        agno_result: Dictionary containing Agno analysis results
        supabase: Initialized Supabase client

    Returns:
        None (function logs errors but doesn't raise)
    """
    try:
        # Extract WTP score from Agno result
        wtp_score = agno_result.get("willingness_to_pay_score")
        if wtp_score is not None:
            wtp_score = float(wtp_score)

        # Call the database function to update Agno tracking
        response = supabase.rpc(
            "update_agno_analysis_tracking",
            {
                "p_concept_id": int(concept_id),
                "p_has_analysis": True,
                "p_wtp_score": wtp_score,
            },
        ).execute()

        if response.data and len(response.data) > 0:
            success = response.data[0].get("update_agno_analysis_tracking", False)
            if success:
                logger.info(
                    f"Updated Agno stats for concept {concept_id} (WTP: {wtp_score})"
                )
            else:
                logger.warning(f"Failed to update Agno stats for concept {concept_id}")
        else:
            logger.warning(
                f"No response from update_agno_analysis_tracking for concept {concept_id}"
            )

    except Exception as e:
        logger.error(f"Error updating concept Agno stats for {concept_id}: {e}")
        # Don't raise exception - this is non-critical functionality
        pass


def should_run_profiler_analysis(
    submission: dict[str, Any], supabase: Any
) -> tuple[bool, str | None]:
    """
    Checks if AI profiling should run for a submission.
    Skips if it's a duplicate with existing AI profile.
    Prevents semantic fragmentation of core_functions arrays.

    Args:
        submission: Submission data from app_opportunities table
        supabase: Initialized Supabase client

    Returns:
        Tuple of (should_run: bool, concept_id: str | None)
        - should_run: True if profiling should run, False if should skip/copy
        - concept_id: Business concept ID if duplicate found, None if unique
    """
    try:
        # Get submission_id for database lookup
        submission_id = submission.get("submission_id", submission.get("id"))
        if not submission_id:
            logger.warning(
                "Submission missing submission_id, defaulting to run profiler analysis"
            )
            return True, None

        # Check if submission has a business_concept_id (indicates it's a duplicate)
        # First try to get from opportunities_unified table
        try:
            response = (
                supabase.table("opportunities_unified")
                .select("business_concept_id")
                .eq("submission_id", submission_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                concept_id = response.data[0].get("business_concept_id")
                if concept_id:
                    # This is a duplicate opportunity, check if concept has AI profiling
                    concept_response = (
                        supabase.table("business_concepts")
                        .select("has_ai_profiling")
                        .eq("id", concept_id)
                        .execute()
                    )

                    if concept_response.data and len(concept_response.data) > 0:
                        has_profiler = concept_response.data[0].get(
                            "has_ai_profiling", False
                        )
                        logger.info(
                            f"Submission {submission_id} is duplicate of concept {concept_id}, has_ai_profiling={has_profiler}"
                        )
                        return not has_profiler, str(
                            concept_id
                        )  # Skip if has profiler, run if no profiler
                    else:
                        # Found concept but no concept data - assume no profiler
                        return True, str(concept_id)
        except Exception as db_error:
            logger.warning(
                f"Database error checking deduplication for {submission_id}: {db_error}"
            )
            # Default to running profiling if database check fails
            return True, None

        # If no business_concept_id found, this is a unique opportunity
        logger.debug(
            f"Submission {submission_id} is unique, should run profiler analysis"
        )
        return True, None

    except Exception as e:
        logger.error(
            f"Error checking if should run profiler analysis for {submission.get('submission_id', 'unknown')}: {e}"
        )
        # Default to running profiling on errors
        return True, None


def copy_profiler_from_primary(
    submission: dict[str, Any], concept_id: str, supabase: Any
) -> dict[str, Any]:
    """
    Copies AI profile (app_name, core_functions, etc.) from primary opportunity.
    Ensures consistent core_functions arrays across duplicate submissions.

    Args:
        submission: Current submission data (duplicate)
        concept_id: Business concept ID to find primary opportunity
        supabase: Initialized Supabase client

    Returns:
        Dictionary formatted for AI profile, or empty dict if copy fails
        Should contain all AI profile fields: app_name, core_functions, value_proposition, etc.
    """
    try:
        # Get the primary opportunity for this concept
        # Look for existing AI profile linked to this concept
        profile_response = (
            supabase.table("workflow_results")
            .select("*")
            .eq("business_concept_id", concept_id)
            .eq("copied_from_primary", False)
            .execute()
        )

        # Handle test environment where Mock objects might be used
        if not hasattr(profile_response, "data") or profile_response.data is None:
            logger.warning(f"No AI profile response for concept {concept_id}")
            return {}

        # Handle both real data and Mock objects for testing
        try:
            # For real responses
            if isinstance(profile_response.data, (list, tuple)):
                data_list = profile_response.data
            else:
                # For Mock objects or other types
                data_list = (
                    list(profile_response.data)
                    if hasattr(profile_response.data, "__iter__")
                    else []
                )
        except (TypeError, AttributeError):
            # Handle Mock objects that don't support iteration
            logger.warning(f"Cannot iterate AI profile data for concept {concept_id}")
            return {}

        if not data_list or len(data_list) == 0:
            # No primary AI profile found, try alternative lookup methods
            # Try to find by primary_opportunity_id
            concept_response = (
                supabase.table("business_concepts")
                .select("primary_opportunity_id")
                .eq("id", concept_id)
                .execute()
            )

            if (
                hasattr(concept_response, "data")
                and concept_response.data
                and len(concept_response.data) > 0
            ):
                primary_opp_id = concept_response.data[0].get("primary_opportunity_id")
                if primary_opp_id:
                    # Try to find AI profile for primary opportunity
                    profile_response = (
                        supabase.table("workflow_results")
                        .select("*")
                        .eq("opportunity_id", primary_opp_id)
                        .eq("copied_from_primary", False)
                        .execute()
                    )

                    if hasattr(profile_response, "data") and profile_response.data:
                        try:
                            if isinstance(profile_response.data, (list, tuple)):
                                data_list = profile_response.data
                            else:
                                data_list = (
                                    list(profile_response.data)
                                    if hasattr(profile_response.data, "__iter__")
                                    else []
                                )
                        except (TypeError, AttributeError):
                            data_list = []

            if not data_list or len(data_list) == 0:
                logger.warning(f"No AI profile found for concept {concept_id}")
                return {}

        # Get the primary AI profile (use the most recent if multiple)
        if len(data_list) == 1:
            primary_profile = data_list[0]
        else:
            # Multiple profiles found, use the most recent
            try:
                primary_profile = max(
                    data_list, key=lambda x: x.get("processed_at", "")
                )
            except (TypeError, AttributeError):
                # Fallback to first profile if date comparison fails
                primary_profile = data_list[0]

        # Create formatted AI profile dict for current submission
        submission_id = submission.get("submission_id", submission.get("id"))
        copied_profile = {
            "opportunity_id": f"opp_{submission_id}",
            "submission_id": submission_id,
            "app_name": primary_profile.get("app_name"),
            "core_functions": primary_profile.get("core_functions"),
            "value_proposition": primary_profile.get("value_proposition"),
            "problem_description": primary_profile.get("problem_description"),
            "app_concept": primary_profile.get("app_concept"),
            "target_user": primary_profile.get("target_user"),
            "monetization_model": primary_profile.get("monetization_model"),
            "final_score": primary_profile.get("final_score"),
            "market_demand": primary_profile.get("market_demand"),
            "pain_intensity": primary_profile.get("pain_intensity"),
            "monetization_potential": primary_profile.get("monetization_potential"),
            "market_gap": primary_profile.get("market_gap"),
            "technical_feasibility": primary_profile.get("technical_feasibility"),
            # Add metadata indicating this is copied
            "copied_from_primary": True,
            "primary_opportunity_id": primary_profile.get("opportunity_id"),
            "business_concept_id": concept_id,
            "copy_timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"Copied AI profile from primary for concept {concept_id} to submission {submission_id}"
        )
        return copied_profile

    except Exception as e:
        logger.error(
            f"Error copying AI profile from primary for concept {concept_id}: {e}"
        )
        return {}


def update_concept_profiler_stats(
    concept_id: str, ai_profile: dict[str, Any], supabase: Any
) -> None:
    """
    Updates business concept with AI profile metadata.
    Tracks profile generation count and timestamps.

    Args:
        concept_id: Business concept ID to update
        ai_profile: Dictionary containing AI profile results
        supabase: Initialized Supabase client

    Returns:
        None (function logs errors but doesn't raise)
    """
    try:
        # Extract final score from AI profile
        profiler_score = ai_profile.get("final_score")
        if profiler_score is not None:
            profiler_score = float(profiler_score)

        # Call the database function to update profiler tracking
        response = supabase.rpc(
            "update_profiler_analysis_tracking",
            {
                "p_concept_id": int(concept_id),
                "p_has_analysis": True,
                "p_profiler_score": profiler_score,
            },
        ).execute()

        if response.data and len(response.data) > 0:
            success = response.data[0].get("update_profiler_analysis_tracking", False)
            if success:
                logger.info(
                    f"Updated profiler stats for concept {concept_id} (Score: {profiler_score})"
                )
            else:
                logger.warning(
                    f"Failed to update profiler stats for concept {concept_id}"
                )
        else:
            logger.warning(
                f"No response from update_profiler_analysis_tracking for concept {concept_id}"
            )

    except Exception as e:
        logger.error(f"Error updating concept profiler stats for {concept_id}: {e}")
        # Don't raise exception - this is non-critical functionality
        pass


def fetch_all_submissions(
    supabase_client: Any, batch_size: int = 1000
) -> list[dict[str, Any]]:
    """
    Fetch all opportunities from app_opportunities table in batches.

    Args:
        supabase_client: Initialized Supabase client
        batch_size: Number of opportunities to fetch per batch (default 1000)

    Returns:
        List of all opportunity dictionaries

    Raises:
        Exception: If database query fails
    """
    try:
        print("Fetching all opportunities from app_opportunities...")

        all_submissions = []
        offset = 0

        while True:
            # Build query with pagination
            query = (
                supabase_client.table("app_opportunities")
                .select(
                    "submission_id, title, problem_description, subreddit, reddit_score, "
                    "num_comments, trust_score, trust_badge, activity_score"
                )
                .range(offset, offset + batch_size - 1)
            )

            response = query.execute()

            if not response.data:
                break  # No more submissions

            all_submissions.extend(response.data)
            print(
                f"Fetched {len(response.data)} submissions (total: {len(all_submissions)})"
            )

            # If we got fewer than batch_size, we've reached the end
            if len(response.data) < batch_size:
                break

            offset += batch_size

        print(f"Successfully fetched {len(all_submissions)} total submissions")

        # Content-based deduplication to remove cross-posted content
        print("🔍 Checking for content duplicates...")
        unique_submissions = []
        seen_titles = set()

        for submission in all_submissions:
            # Focus on title similarity for cross-post deduplication
            title = submission.get("title", "").strip().lower()

            # Remove common filler words and normalize
            title_words = set(title.split())

            # Remove common filler words that don't affect meaning
            filler_words = {
                "i",
                "the",
                "a",
                "an",
                "and",
                "or",
                "but",
                "in",
                "on",
                "at",
                "to",
                "for",
                "of",
                "with",
                "by",
                "is",
                "are",
                "was",
                "were",
                "be",
                "been",
                "have",
                "has",
                "had",
                "do",
                "does",
                "did",
                "will",
                "would",
                "could",
                "should",
                "may",
                "might",
                "can",
                "must",
                "shall",
            }

            # Create title signature from meaningful words only
            title_signature = tuple(sorted(title_words - filler_words))

            # Use only title signature for deduplication (cross-posts typically have identical titles)
            content_key = title_signature

            if content_key not in seen_titles:
                seen_titles.add(content_key)
                unique_submissions.append(submission)
            else:
                print(
                    f"  🔄 Removed duplicate: '{title[:50]}...' (r/{submission.get('subreddit')})"
                )

        if len(unique_submissions) < len(all_submissions):
            print(
                f"✅ Removed {len(all_submissions) - len(unique_submissions)} content duplicates"
            )
            print(
                f"📊 Unique submissions: {len(unique_submissions)} from {len(all_submissions)} total"
            )

        return unique_submissions

    except Exception as e:
        print(f"Error fetching submissions: {e}")
        raise


def fetch_submissions(
    supabase_client: Any, limit: int | None = None
) -> list[dict[str, Any]]:
    """
    Fetch opportunities from app_opportunities table for AI enrichment.

    Args:
        supabase_client: Initialized Supabase client
        limit: Optional limit on number of opportunities to fetch

    Returns:
        List of opportunity dictionaries with all relevant fields

    Raises:
        Exception: If database query fails
    """
    try:
        if limit:
            # Use simple fetch for limited results
            print("Fetching limited opportunities from app_opportunities...")
            query = (
                supabase_client.table("app_opportunities")
                .select(
                    "submission_id, title, problem_description, subreddit, reddit_score, "
                    "num_comments, trust_score, trust_badge, activity_score"
                )
                .limit(limit)
            )

            response = query.execute()

            if not response.data:
                print("Warning: No opportunities found in database")
                return []

            print(f"Successfully fetched {len(response.data)} opportunities")
            return response.data
        else:
            # Fetch all opportunities in batches
            return fetch_all_submissions(supabase_client)

    except Exception as e:
        print(f"Error fetching opportunities: {e}")
        raise


def format_submission_for_agent(submission: dict[str, Any]) -> dict[str, Any]:
    """
    Format an opportunity from app_opportunities for LLM profiler enrichment.

    Args:
        submission: Opportunity data from app_opportunities table

    Returns:
        Formatted opportunity data for AI profile generation
    """
    # Use existing problem_description or combine title for full text analysis
    title = submission.get("title", "")
    text = submission.get("problem_description", "")
    full_text = f"{title}\n\n{text}".strip() if text else title

    # Format engagement data using app_opportunities column names
    engagement = {
        "upvotes": submission.get("reddit_score", 0) or 0,
        "num_comments": submission.get("num_comments", 0) or 0,
    }

    # Include trust metadata for context
    comments = []
    trust_score = submission.get("trust_score")
    trust_badge = submission.get("trust_badge")

    if trust_score:
        comments.append(f"Trust Score: {trust_score}")
    if trust_badge:
        comments.append(f"Trust Badge: {trust_badge}")

    return {
        "id": submission.get("submission_id", submission.get("id", "unknown")),
        "title": title,
        "text": full_text,
        "subreddit": submission.get("subreddit", ""),
        "engagement": engagement,
        "comments": comments,
        "sentiment_score": submission.get("sentiment_score", 0.0),
        "db_id": submission.get("id"),  # Keep reference to database UUID
    }


def prepare_analysis_for_storage(
    submission_id: str,
    analysis: dict[str, Any],
    sector: str,
    trust_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Prepare opportunity analysis result for DLT pipeline storage.

    Args:
        submission_id: ID of the submission from the submissions table
        analysis: Analysis results from agent containing dimension scores
        sector: Mapped business sector

    Returns:
        Dictionary formatted for workflow_results table
    """
    # Generate opportunity_id from submission_id (unique identifier for merge)
    opportunity_id = f"opp_{submission_id}"

    # Extract dimension scores
    scores = analysis.get("dimension_scores", {})

    # Extract core functions from analysis (now always available)
    core_functions = analysis.get("core_functions", [])

    if isinstance(core_functions, list) and len(core_functions) > 0:
        function_count = len(core_functions)
        function_list = core_functions
    else:
        # Fallback for unexpected format
        function_count = core_functions if isinstance(core_functions, int) else 1
        function_list = [f"Core function {i + 1}" for i in range(function_count)]

    # Extract cost tracking data if available
    cost_data = analysis.get("cost_tracking", {})

    # Prepare data for workflow_results table
    analysis_data = {
        "opportunity_id": opportunity_id,  # For workflow_results deduplication
        "submission_id": submission_id,  # Original Reddit ID for app_opportunities deduplication
        "app_name": analysis.get(
            "app_name", analysis.get("title", "Unnamed Opportunity")
        )[:255],
        "function_count": function_count,
        "function_list": function_list,
        "original_score": float(analysis.get("final_score", 0)),
        "final_score": float(analysis.get("final_score", 0)),
        "status": "scored",
        "constraint_applied": True,
        "ai_insight": f"Market sector: {sector}. Subreddit: {analysis.get('subreddit', 'unknown')}",
        "subreddit": analysis.get("subreddit", ""),
        "processed_at": datetime.now().isoformat(),
        # Trust validation data (from app_opportunities)
        "trust_score": float(trust_data.get("trust_score", 0))
        if trust_data and trust_data.get("trust_score")
        else None,
        "trust_badge": trust_data.get("trust_badge", "")[:50]
        if trust_data and trust_data.get("trust_badge")
        else None,
        "activity_score": float(trust_data.get("activity_score", 0))
        if trust_data and trust_data.get("activity_score")
        else None,
        # Dimension scores
        "market_demand": float(scores.get("market_demand", 0)) if scores else None,
        "pain_intensity": float(scores.get("pain_intensity", 0)) if scores else None,
        "monetization_potential": float(scores.get("monetization_potential", 0))
        if scores
        else None,
        "market_gap": float(scores.get("market_gap", 0)) if scores else None,
        "technical_feasibility": float(scores.get("technical_feasibility", 0))
        if scores
        else None,
        # App profile fields (from LLM if available)
        "problem_description": analysis.get("problem_description", "")[:500],
        "app_concept": analysis.get("app_concept", "")[:500],
        "value_proposition": analysis.get("value_proposition", "")[:500],
        "target_user": analysis.get("target_user", "")[:255],
        "monetization_model": analysis.get("monetization_model", "")[:255],
        # Cost tracking data (from EnhancedLLMProfiler)
        "llm_model_used": cost_data.get("model_used"),
        "llm_provider": cost_data.get("provider", "openrouter"),
        "llm_prompt_tokens": cost_data.get("prompt_tokens", 0),
        "llm_completion_tokens": cost_data.get("completion_tokens", 0),
        "llm_total_tokens": cost_data.get("total_tokens", 0),
        "llm_input_cost_usd": cost_data.get("input_cost_usd", 0.0),
        "llm_output_cost_usd": cost_data.get("output_cost_usd", 0.0),
        "llm_total_cost_usd": cost_data.get("total_cost_usd", 0.0),
        "llm_latency_seconds": cost_data.get("latency_seconds", 0.0),
        "llm_timestamp": cost_data.get("timestamp"),
        "llm_pricing_info": cost_data.get("model_pricing_per_m_tokens", {}),
        "cost_tracking_enabled": bool(cost_data),
    }

    # Market validation evidence (from MarketDataValidator)
    market_evidence = analysis.get("market_validation_evidence")
    if market_evidence:
        analysis_data.update(
            {
                "market_validation_score": float(
                    market_evidence.get("validation_score", 0)
                ),
                "market_data_quality_score": float(
                    market_evidence.get("data_quality_score", 0)
                ),
                "market_validation_reasoning": market_evidence.get("reasoning", "")[
                    :1000
                ],
                "market_competitors_found": market_evidence.get(
                    "competitors_found", []
                ),
                "market_size_tam": market_evidence.get("tam_value"),
                "market_size_growth": market_evidence.get("growth_rate"),
                "market_similar_launches": market_evidence.get(
                    "similar_launches_count", 0
                ),
                "market_validation_cost_usd": float(
                    market_evidence.get("total_cost", 0)
                ),
                "market_validation_timestamp": market_evidence.get("timestamp"),
            }
        )

    return analysis_data


def load_scores_to_supabase_via_dlt(scored_opportunities: list[dict[str, Any]]) -> bool:
    """
    Load scored opportunities to Supabase using DLT pipeline with constraint validation.

    This function uses DLT's merge write disposition to automatically handle
    deduplication based on opportunity_id. If a score already exists, it will
    be updated with the new values. Includes DLT-native constraint validation
    for the 1-3 core function rule.

    Args:
        scored_opportunities: List of scored opportunity dictionaries

    Returns:
        True if successful, False otherwise
    """
    if not scored_opportunities:
        print("⚠️  No scored opportunities to load")
        return False

    # Phase 1: Pre-flight checks for function consistency
    print("\n🔍 Pre-flight checks (Phase 1)...")

    # Check: Every opportunity has function_list
    missing_functions = [
        o["opportunity_id"] for o in scored_opportunities if not o.get("function_list")
    ]
    if missing_functions:
        print(
            f"❌ ERROR: {len(missing_functions)} opportunities missing function_list:"
        )
        for opp_id in missing_functions[:5]:
            print(f"  - {opp_id}")
        raise ValueError(f"Cannot load: {len(missing_functions)} missing function_list")

    # Check: function_count matches function_list length
    mismatches = [
        o
        for o in scored_opportunities
        if len(o.get("function_list", [])) != o.get("function_count")
    ]
    if mismatches:
        print(f"⚠️  WARNING: {len(mismatches)} opportunities have count/list mismatch")
        for opp in mismatches[:3]:
            print(
                f"  - {opp['opportunity_id']}: count={opp.get('function_count')}, "
                f"actual={len(opp.get('function_list', []))}"
            )

    print(f"✓ Pre-flight checks passed ({len(scored_opportunities)} opportunities)")

    try:
        print(f"\n{'=' * 80}")
        print("LOADING SCORES TO SUPABASE VIA DLT PIPELINE")
        print(f"{'=' * 80}")
        print(f"Opportunities to load: {len(scored_opportunities)}")

        # Validate constraints before loading
        print("\n🔍 Validating constraints...")
        validated_opportunities = list(
            app_opportunities_with_constraint(scored_opportunities)
        )
        approved = [o for o in validated_opportunities if not o.get("is_disqualified")]
        disqualified = [o for o in validated_opportunities if o.get("is_disqualified")]

        print(f"  ✓ Approved: {len(approved)}")
        print(f"  ⚠️  Disqualified: {len(disqualified)}")
        print(
            f"  ✓ Compliance rate: {len(approved) / len(validated_opportunities) * 100:.1f}%"
        )

        if disqualified:
            print("\n  Disqualified Opportunities:")
            for opp in disqualified[:3]:  # Show first 3
                print(
                    f"    - {opp.get('app_name', 'Unknown')}: {opp.get('violation_reason', 'N/A')}"
                )
            if len(disqualified) > 3:
                print(f"    ... and {len(disqualified) - 3} more")

        # Use the DLT constraint validator resource which has the correct table_name
        # The resource decorator already specifies table_name="workflow_results"
        # Just pass the data to the resource
        print("\n📤 Loading to workflow_results table via DLT constraint validator...")

        # Load using the DLT pipeline
        from core.dlt_collection import create_dlt_pipeline

        pipeline = create_dlt_pipeline()

        # Use the constraint validator resource
        load_info = pipeline.run(
            app_opportunities_with_constraint(scored_opportunities),
            write_disposition="merge",
            primary_key=PK_OPPORTUNITY_ID,  # Deduplication key
        )

        print(
            f"\n✓ Successfully processed {len(validated_opportunities)} opportunities"
        )
        print(
            f"✓ Successfully loaded {len(approved)} approved opportunities to Supabase"
        )
        if disqualified:
            print(
                f"⚠️  Skipped {len(disqualified)} disqualified opportunities (4+ functions)"
            )
        print("  - Table: workflow_results")
        print("  - Write mode: merge (deduplication enabled)")
        print("  - Primary key: opportunity_id")
        print("  - Constraint validation: DLT-native (1-3 function rule)")
        print(f"  - Started at: {load_info.started_at}")
        print(f"{'=' * 80}\n")

        return True

    except Exception as e:
        print(f"\n✗ Error loading scores via DLT: {e}")
        print(f"  - Opportunities affected: {len(scored_opportunities)}")
        print("  - Recommendation: Check DLT configuration and Supabase connection")
        print(f"{'=' * 80}\n")
        return False


def store_ai_profiles_to_app_opportunities_via_dlt(
    scored_opportunities: list[dict[str, Any]],
) -> int:
    """
    Update app_opportunities table with AI-enriched profiles via DLT.
    Uses DLT merge disposition to update existing records with LLM-generated content.
    Preserves trust indicators (trust_score, trust_badge, activity_score) from original data.
    Only updates opportunities that have AI-generated fields.

    Args:
        scored_opportunities: List of scored opportunities (some with AI profiles)

    Returns:
        Number of AI profiles stored
    """
    import dlt

    from config import SUPABASE_KEY, SUPABASE_URL
    from core.dlt_collection import create_dlt_pipeline
    from supabase import create_client

    # Fetch current trust data from database to preserve it
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Filter to only opportunities with AI-generated fields
    ai_profiles = []
    for opp in scored_opportunities:
        # Only include if it has AI-generated fields and valid submission_id
        if not opp.get("problem_description") or not opp.get("submission_id"):
            continue

        # Fetch existing trust data for this submission_id
        submission_id = opp.get("submission_id")
        try:
            existing = (
                supabase.table("app_opportunities")
                .select(
                    "trust_score, trust_badge, activity_score, engagement_level, "
                    "trust_level, trend_velocity, problem_validity, discussion_quality, "
                    "ai_confidence_level, trust_validation_timestamp, trust_validation_method, "
                    "subreddit, reddit_score, num_comments, title"
                )
                .eq("submission_id", submission_id)
                .execute()
            )

            trust_data = existing.data[0] if existing.data else {}
        except Exception as e:
            print(f"⚠️  Could not fetch trust data for {submission_id}: {e}")
            trust_data = {}

        # Merge AI profile with preserved trust indicators
        ai_profile = {
            "submission_id": submission_id,
            "problem_description": opp.get("problem_description"),
            "app_concept": opp.get("app_concept"),
            "core_functions": standardize_core_functions(opp.get("function_list", [])),
            "value_proposition": opp.get("value_proposition"),
            "target_user": opp.get("target_user"),
            "monetization_model": opp.get("monetization_model"),
            "opportunity_score": float(opp.get("final_score", 0)),
            "title": trust_data.get("title", opp.get("app_name", "")),
            "status": "ai_enriched",
            # Preserve trust layer fields
            "trust_score": trust_data.get("trust_score"),
            "trust_badge": trust_data.get("trust_badge"),
            "activity_score": trust_data.get("activity_score"),
            "engagement_level": trust_data.get("engagement_level"),
            "trust_level": trust_data.get("trust_level"),
            "trend_velocity": trust_data.get("trend_velocity"),
            "problem_validity": trust_data.get("problem_validity"),
            "discussion_quality": trust_data.get("discussion_quality"),
            "ai_confidence_level": trust_data.get("ai_confidence_level"),
            "trust_validation_timestamp": trust_data.get("trust_validation_timestamp"),
            "trust_validation_method": trust_data.get("trust_validation_method"),
            # Preserve submission metadata
            "subreddit": trust_data.get("subreddit"),
            "reddit_score": trust_data.get("reddit_score"),
            "num_comments": trust_data.get("num_comments"),
        }
        ai_profiles.append(ai_profile)

    if not ai_profiles:
        print("⚠️  No AI profiles to store (no opportunities with AI-generated fields)")
        return 0

    # Create DLT resource for app_opportunities with merge disposition
    @dlt.resource(
        name="app_opportunities",
        write_disposition="merge",
        primary_key=PK_SUBMISSION_ID,
    )
    def ai_enriched_opportunities():
        yield ai_profiles

    # Load via DLT pipeline
    pipeline = create_dlt_pipeline()
    load_info = pipeline.run(ai_enriched_opportunities())

    print(
        f"✓ Updated {len(ai_profiles)} opportunities with AI profiles in app_opportunities"
    )
    return len(ai_profiles)


def perform_market_validation(opportunity_data: dict) -> ValidationEvidence | None:
    """
    Perform market data validation for high-scoring opportunities.

    This function validates monetization potential using real market data:
    - Competitor pricing analysis
    - Market size estimation
    - Similar product launches
    - Industry benchmarks

    Args:
        opportunity_data: Dictionary containing:
            - app_concept: Description of the app concept
            - target_market: B2B, B2C, etc.
            - problem_description: The problem being solved

    Returns:
        ValidationEvidence with market data and scores, or None on failure
    """
    # Check if market validation is enabled
    if not HYBRID_STRATEGY_CONFIG["market_validation"]["enabled"]:
        return None

    # Check if Jina API key is configured
    if not HYBRID_STRATEGY_CONFIG["market_validation"]["jina_api_key"]:
        logger = logging.getLogger(__name__)
        logger.warning("Market validation skipped: No JINA_API_KEY configured")
        return None

    # Extract required fields
    app_concept = opportunity_data.get("app_concept", "")
    target_market = opportunity_data.get("target_market", "B2C")
    problem_description = opportunity_data.get("problem_description", "")

    # Skip if missing critical data
    if not app_concept or not problem_description:
        return None

    try:
        # Initialize validator (lazy initialization)
        if not hasattr(perform_market_validation, "_validator"):
            perform_market_validation._validator = MarketDataValidator()

        # Perform validation
        evidence = perform_market_validation._validator.validate_opportunity(
            app_concept=app_concept,
            target_market=target_market,
            problem_description=problem_description,
        )

        return evidence

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Market validation failed: {e}")
        return None


def store_hybrid_results_to_database(
    all_results: list[dict[str, Any]],
) -> dict[str, int]:
    """
    Store hybrid strategy results (Option A & B) to their respective database tables.

    This function extracts LLM analysis and lead data from the analysis results
    and stores them in the appropriate hybrid strategy tables.

    Args:
        all_results: List of analysis results containing hybrid_results

    Returns:
        Dictionary with counts of stored records by type
    """
    llm_analyses = []
    customer_leads = []

    # Extract hybrid results from analysis
    for result in all_results:
        hybrid_results = result.get("hybrid_results", {})

        # Option A: LLM Monetization Analysis
        if "llm_analysis" in hybrid_results:
            llm_record = hybrid_results["llm_analysis"]
            llm_analyses.append(llm_record)

        # Option B: Customer Lead Extraction
        if "lead" in hybrid_results:
            lead_record = hybrid_results["lead"]
            customer_leads.append(lead_record)

    stored_counts = {"llm_analyses": 0, "customer_leads": 0}

    # Store Option A: LLM Monetization Analysis
    if llm_analyses:
        try:

            @dlt.resource(
                name="llm_monetization_analysis",
                write_disposition="merge",
                primary_key=PK_OPPORTUNITY_ID,
            )
            def llm_analysis_resource():
                yield from llm_analyses

            pipeline = create_dlt_pipeline()
            load_info = pipeline.run(llm_analysis_resource())
            stored_counts["llm_analyses"] = len(llm_analyses)
            print(f"✓ Stored {len(llm_analyses)} LLM monetization analyses")

        except Exception as e:
            print(f"⚠️  Failed to store LLM analyses: {e}")

    # Store Option B: Customer Leads
    if customer_leads:
        try:

            @dlt.resource(
                name="customer_leads",
                write_disposition="merge",
                primary_key=PK_OPPORTUNITY_ID,
            )
            def customer_leads_resource():
                yield from customer_leads

            pipeline = create_dlt_pipeline()
            load_info = pipeline.run(customer_leads_resource())
            stored_counts["customer_leads"] = len(customer_leads)
            print(f"✓ Stored {len(customer_leads)} customer leads")

            # Log hot leads summary
            hot_leads = [
                lead
                for lead in customer_leads
                if lead.get("urgency_level") in ["high", "critical"]
                and lead.get("lead_score", 0) >= 75
            ]
            if hot_leads:
                print(
                    f"🔥 HOT LEADS: {len(hot_leads)} high-priority leads ready for outreach!"
                )

        except Exception as e:
            print(f"⚠️  Failed to store customer leads: {e}")

    return stored_counts


def process_batch(
    submissions: list[dict[str, Any]],
    agent: OpportunityAnalyzerAgent,
    batch_number: int,
    llm_profiler: EnhancedLLMProfiler | None = None,
    ai_profile_threshold: float = 40.0,
    supabase: Any = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int, dict[str, Any]]:
    """
    Process a batch of submissions through the opportunity analyzer.

    This function scores submissions but does NOT store them directly.
    Instead, it returns scored opportunities for batch DLT loading.

    For high-scoring opportunities (>= threshold), generates real AI app profiles
    using Claude Haiku via OpenRouter.

    Args:
        submissions: List of submission dictionaries to process
        agent: Initialized OpportunityAnalyzerAgent
        batch_number: Current batch number for logging
        llm_profiler: Optional LLM profiler for high-score opportunities
        ai_profile_threshold: Score threshold for LLM profiling (default: 40.0)
        supabase: Optional Supabase client for deduplication checks

    Returns:
        Tuple of (analysis_results, scored_opportunities_for_dlt, ai_profiles_count, market_validation_stats)
        - analysis_results: List with full analysis metadata
        - scored_opportunities_for_dlt: List formatted for DLT pipeline
        - ai_profiles_count: Number of AI profiles generated in this batch
        - market_validation_stats: Dictionary with market validation metrics
    """
    analysis_results = []
    scored_opportunities = []
    high_score_count = 0
    total_submissions = len(submissions)

    # Market validation tracking
    market_validation_stats = {
        "validation_count": 0,
        "total_validation_score": 0.0,
        "total_data_quality_score": 0.0,
        "total_validation_cost": 0.0,
        "competitors_found": 0,
        "market_sizes_found": 0,
        "similar_launches_found": 0,
    }

    for submission in submissions:
        try:
            # Format submission for agent
            formatted = format_submission_for_agent(submission)

            # Analyze opportunity (scoring only, no AI profiling yet)
            analysis = agent.analyze_opportunity(formatted)

            # Check if this is a high-scoring opportunity
            final_score = analysis.get("final_score", 0)
            print(f"  📊 {formatted['title'][:60]}... Score: {final_score:.1f}")

            # HYBRID STRATEGY: Run Option A & B analysis on qualified opportunities
            if (
                final_score >= ai_profile_threshold
            ):  # Use AI profile threshold for consistency
                hybrid_results = {}

                # Option A: LLM Monetization Analysis (if enabled)
                if (
                    HYBRID_STRATEGY_CONFIG["option_a"]["enabled"]
                    and HYBRID_STRATEGY_CONFIG["option_a"]["openrouter_key"]
                ):
                    try:
                        # === DEDUPLICATION INTEGRATION POINT 1: AGNO MONETIZATION ANALYSIS ===
                        # Skip expensive Agno multi-agent analysis (~$0.10 per analysis) for duplicate business concepts
                        # Expected savings: $2.80 per 100 posts (70% reduction at 40% duplicate rate)
                        # This preserves investment in high-quality multi-agent analysis while eliminating redundant costs
                        should_run_agno = True
                        concept_id = None

                        if supabase:
                            should_run_agno, concept_id = should_run_agno_analysis(
                                submission, supabase
                            )

                        if should_run_agno:
                            # Fresh Agno analysis needed
                            if not hasattr(process_batch, "_llm_analyzer"):
                                process_batch._llm_analyzer = get_monetization_analyzer(
                                    model=HYBRID_STRATEGY_CONFIG["option_a"]["model"]
                                )

                            llm_result = process_batch._llm_analyzer.analyze(
                                text=formatted["text"],
                                subreddit=formatted["subreddit"],
                                keyword_monetization_score=analysis.get(
                                    "monetization_potential", 0
                                ),
                            )

                            # Update monetization score with LLM result
                            analysis["monetization_potential"] = (
                                llm_result.llm_monetization_score
                            )
                            analysis["customer_segment"] = llm_result.customer_segment
                            analysis["llm_analysis"] = {
                                "willingness_to_pay": llm_result.willingness_to_pay_score,
                                "payment_sentiment": llm_result.sentiment_toward_payment,
                                "price_points": llm_result.mentioned_price_points,
                                "urgency": llm_result.urgency_level,
                                "confidence": llm_result.confidence,
                            }

                            # Store LLM analysis record for database
                            hybrid_results["llm_analysis"] = {
                                "opportunity_id": f"opp_{submission.get('submission_id', submission.get('id'))}",
                                "submission_id": submission.get(
                                    "submission_id", submission.get("id")
                                ),
                                "llm_monetization_score": llm_result.llm_monetization_score,
                                "keyword_monetization_score": analysis.get(
                                    "monetization_potential", 0
                                ),
                                "customer_segment": llm_result.customer_segment,
                                "willingness_to_pay_score": llm_result.willingness_to_pay_score,
                                "price_sensitivity_score": llm_result.price_sensitivity_score,
                                "revenue_potential_score": llm_result.revenue_potential_score,
                                "payment_sentiment": llm_result.sentiment_toward_payment,
                                "urgency_level": llm_result.urgency_level,
                                "existing_payment_behavior": llm_result.existing_payment_behavior,
                                "mentioned_price_points": llm_result.mentioned_price_points,
                                "payment_friction_indicators": llm_result.payment_friction_indicators,
                                "confidence": llm_result.confidence,
                                "reasoning": llm_result.reasoning,
                                "subreddit_multiplier": llm_result.subreddit_multiplier,
                                "model_used": HYBRID_STRATEGY_CONFIG["option_a"][
                                    "model"
                                ],
                                "score_delta": llm_result.llm_monetization_score
                                - analysis.get("monetization_potential", 0),
                                "concept_id": concept_id,
                            }

                            print(
                                f"  ✅ Option A: LLM Score {llm_result.llm_monetization_score:.1f} (Δ{llm_result.llm_monetization_score - analysis.get('monetization_potential', 0):+.1f})"
                            )

                            # Update concept metadata with fresh Agno analysis
                            if supabase and concept_id:
                                agno_result = {
                                    "willingness_to_pay_score": llm_result.willingness_to_pay_score,
                                    "customer_segment": llm_result.customer_segment,
                                    "llm_monetization_score": llm_result.llm_monetization_score,
                                    "confidence": llm_result.confidence,
                                }
                                update_concept_agno_stats(
                                    concept_id, agno_result, supabase
                                )

                        else:
                            # Skip Agno analysis - copy from primary opportunity
                            if supabase and concept_id:
                                agno_copy_result = copy_agno_from_primary(
                                    submission, concept_id, supabase
                                )

                                if agno_copy_result:
                                    # Update analysis with copied Agno data
                                    analysis["monetization_potential"] = (
                                        agno_copy_result.get(
                                            "llm_monetization_score",
                                            analysis.get("monetization_potential", 0),
                                        )
                                    )
                                    analysis["customer_segment"] = agno_copy_result.get(
                                        "customer_segment"
                                    )
                                    analysis["llm_analysis"] = {
                                        "willingness_to_pay": agno_copy_result.get(
                                            "willingness_to_pay_score"
                                        ),
                                        "payment_sentiment": agno_copy_result.get(
                                            "payment_sentiment"
                                        ),
                                        "price_points": agno_copy_result.get(
                                            "mentioned_price_points"
                                        ),
                                        "urgency": agno_copy_result.get(
                                            "urgency_level"
                                        ),
                                        "confidence": agno_copy_result.get(
                                            "confidence"
                                        ),
                                    }

                                    # Store copied analysis for database
                                    hybrid_results["llm_analysis"] = {
                                        "opportunity_id": f"opp_{submission.get('submission_id', submission.get('id'))}",
                                        "submission_id": submission.get(
                                            "submission_id", submission.get("id")
                                        ),
                                        "llm_monetization_score": agno_copy_result.get(
                                            "llm_monetization_score"
                                        ),
                                        "keyword_monetization_score": analysis.get(
                                            "monetization_potential", 0
                                        ),
                                        "customer_segment": agno_copy_result.get(
                                            "customer_segment"
                                        ),
                                        "willingness_to_pay_score": agno_copy_result.get(
                                            "willingness_to_pay_score"
                                        ),
                                        "price_sensitivity_score": agno_copy_result.get(
                                            "price_sensitivity_score"
                                        ),
                                        "revenue_potential_score": agno_copy_result.get(
                                            "revenue_potential_score"
                                        ),
                                        "payment_sentiment": agno_copy_result.get(
                                            "payment_sentiment"
                                        ),
                                        "urgency_level": agno_copy_result.get(
                                            "urgency_level"
                                        ),
                                        "existing_payment_behavior": agno_copy_result.get(
                                            "existing_payment_behavior"
                                        ),
                                        "mentioned_price_points": agno_copy_result.get(
                                            "mentioned_price_points"
                                        ),
                                        "payment_friction_indicators": agno_copy_result.get(
                                            "payment_friction_indicators"
                                        ),
                                        "confidence": agno_copy_result.get(
                                            "confidence"
                                        ),
                                        "reasoning": agno_copy_result.get("reasoning"),
                                        "subreddit_multiplier": agno_copy_result.get(
                                            "subreddit_multiplier"
                                        ),
                                        "model_used": agno_copy_result.get(
                                            "model_used", "copied"
                                        ),
                                        "score_delta": agno_copy_result.get(
                                            "llm_monetization_score", 0
                                        )
                                        - analysis.get("monetization_potential", 0),
                                        "concept_id": concept_id,
                                        "copied_from_primary": True,
                                    }

                                    print(
                                        f"  🔄 Option A: Skipped analysis - copied from concept {concept_id} (WTP: {agno_copy_result.get('willingness_to_pay_score', 0)})"
                                    )
                                else:
                                    print(
                                        f"  ⚠️  Option A: Failed to copy Agno analysis from concept {concept_id}"
                                    )
                            else:
                                print(
                                    f"  ⚠️  Option A: Skipped analysis but no supabase/concept_id available"
                                )

                    except Exception as e:
                        print(f"  ⚠️  Option A LLM analysis failed: {e}")

                # Option B: Customer Lead Extraction (if enabled)
                if HYBRID_STRATEGY_CONFIG["option_b"]["enabled"]:
                    try:
                        if not hasattr(process_batch, "_lead_extractor"):
                            process_batch._lead_extractor = LeadExtractor()

                        # Convert submission to post format for lead extractor
                        post = {
                            "id": formatted["id"],
                            "author": formatted.get("author", "unknown"),
                            "title": formatted["title"],
                            "selftext": formatted["text"],
                            "subreddit": formatted["subreddit"],
                            "created_utc": formatted.get("created_utc"),
                        }

                        # Extract lead signals
                        lead = process_batch._lead_extractor.extract_from_reddit_post(
                            post=post, opportunity_score=final_score
                        )

                        # Convert to database record
                        lead_record = convert_to_database_record(lead)
                        lead_record["opportunity_id"] = (
                            f"opp_{submission.get('submission_id', submission.get('id'))}"
                        )

                        hybrid_results["lead"] = lead_record

                        print(
                            f"  👥 Option B: Lead Score {lead.lead_score}/100 ({lead.urgency_level} urgency)"
                        )

                        # Optional: Send Slack alert for hot leads
                        if (
                            lead.urgency_level in ["high", "critical"]
                            and lead.lead_score >= 75
                            and HYBRID_STRATEGY_CONFIG["option_b"]["slack_webhook"]
                        ):
                            try:
                                import requests

                                from core.lead_extractor import format_lead_for_slack

                                slack_msg = format_lead_for_slack(lead)
                                webhook_url = HYBRID_STRATEGY_CONFIG["option_b"][
                                    "slack_webhook"
                                ]

                                response = requests.post(
                                    webhook_url, json=slack_msg, timeout=10
                                )
                                if response.status_code == 200:
                                    print("  📱 Hot lead alert sent to Slack!")
                                else:
                                    print(
                                        f"  ⚠️  Slack notification failed: {response.status_code}"
                                    )
                            except Exception as slack_e:
                                print(f"  ⚠️  Slack notification error: {slack_e}")

                    except Exception as e:
                        print(f"  ⚠️  Option B lead extraction failed: {e}")

                # Store hybrid results in analysis for later processing
                if hybrid_results:
                    analysis["hybrid_results"] = hybrid_results
            if llm_profiler and final_score >= ai_profile_threshold:
                high_score_count += 1

                # === DEDUPLICATION INTEGRATION POINT 2: AI PROFILING ===
                # Skip AI app profiling for duplicates to prevent semantic fragmentation
                # Ensures consistent core_functions arrays across duplicate submissions
                # This maintains data quality by avoiding different LLM interpretations of the same concept
                # Cost savings: $0.02 per 100 posts (70% reduction in profiler calls)
                should_run_profiler, concept_id = should_run_profiler_analysis(submission, supabase)

                if should_run_profiler:
                    # Fresh AI profiling needed
                    print(f"  🎯 High score ({final_score:.1f}) - generating fresh AI profile...")

                    # Generate real AI app profile with cost tracking
                    try:
                        # Prepare Agno evidence if available from hybrid analysis
                        agno_evidence = None
                        if hybrid_results and "llm_analysis" in hybrid_results:
                            # Extract the Agno analysis data that was used for Option A
                            agno_evidence = {
                                "willingness_to_pay_score": hybrid_results[
                                    "llm_analysis"
                                ].get("willingness_to_pay_score", 50),
                                "customer_segment": hybrid_results["llm_analysis"].get(
                                    "customer_segment", "Unknown"
                                ),
                                "sentiment_toward_payment": hybrid_results[
                                    "llm_analysis"
                                ].get("payment_sentiment", "Neutral"),
                                "urgency_level": hybrid_results["llm_analysis"].get(
                                    "urgency_level", "Low"
                                ),
                                "mentioned_price_points": hybrid_results[
                                    "llm_analysis"
                                ].get("mentioned_price_points", []),
                                "existing_payment_behavior": hybrid_results[
                                    "llm_analysis"
                                ].get("existing_payment_behavior", "Not specified"),
                                "payment_friction_indicators": hybrid_results[
                                    "llm_analysis"
                                ].get("payment_friction_indicators", []),
                                "confidence": hybrid_results["llm_analysis"].get(
                                    "confidence", 0.7
                                ),
                            }
                        print(
                            f"  🧠 Evidence-based profiling: Using Agno analysis (WTP: {agno_evidence['willingness_to_pay_score']}/100, Segment: {agno_evidence['customer_segment']})"
                        )

                    # Use the enhanced evidence-based profiling method
                        if agno_evidence:
                            # Use dedicated evidence-based method
                            ai_profile = llm_profiler.generate_app_profile_with_evidence(
                                text=formatted["text"],
                                title=formatted["title"],
                                subreddit=formatted["subreddit"],
                                score=final_score,
                                agno_analysis=agno_evidence,
                            )
                            # Extract cost data from profile (embedded by evidence-based method)
                            cost_data = ai_profile.get("cost_tracking", {})
                            print("  ✅ Enhanced evidence-based profiling completed")
                        else:
                            # Fallback to standard method with cost tracking
                            ai_profile, cost_data = (
                                llm_profiler.generate_app_profile_with_costs(
                                    text=formatted["text"],
                                    title=formatted["title"],
                                    subreddit=formatted["subreddit"],
                                score=final_score,
                                agno_analysis=agno_evidence,
                            )
                        )
                        print("  🤖 Standard AI profiling (no evidence available)")

                        # Merge AI profile into analysis and store cost data
                        analysis.update(ai_profile)
                        analysis["cost_tracking"] = (
                            cost_data  # Ensure cost data is preserved
                        )

                        # Update concept profiler stats for fresh profiling
                        update_concept_profiler_stats(concept_id, ai_profile, supabase)

                        # Enhanced evidence validation logging
                        validation = None
                        alignment_score = 0
                        validation_status = "unknown"
                        discrepancies = []
                        warnings = []
                        confidence_metrics = {}
                        evidence_strength = "medium"
                        validation_icon = "🔴"  # Default icon

                        if agno_evidence and "evidence_validation" in ai_profile:
                            validation = ai_profile["evidence_validation"]
                            alignment_score = validation.get("alignment_score", 0)
                            validation_status = validation.get("overall_status", "unknown")
                            discrepancies = validation.get("discrepancies", [])
                            warnings = validation.get("warnings", [])
                            confidence_metrics = validation.get("confidence_metrics", {})
                            evidence_strength = validation.get(
                                "evidence_strength", "medium"
                            )

                            # Determine validation icon based on alignment
                            if alignment_score >= 80:
                                validation_icon = "🟢"
                            elif alignment_score >= 60:
                                validation_icon = "🟡"
                            else:
                                validation_icon = "🔴"

                            print(
                                f"  {validation_icon} Evidence Validation: {validation_status.replace('_', ' ').title()} ({alignment_score:.1f}% alignment)"
                            )
                            print(
                                f"     Evidence Strength: {evidence_strength.title()} (Confidence: {confidence_metrics.get('evidence_confidence', 0):.2f})"
                            )

                            # Show detailed validation results
                            validations = validation.get("validations", {})
                            if validations:
                                print("     Validation Details:")
                                for validation_name, validation_data in validations.items():
                                    if (
                                        isinstance(validation_data, dict)
                                        and "score" in validation_data
                                        ):
                                            score = (
                                                validation_data["score"] * 100
                                            )  # Convert to percentage
                                            status_icon = (
                                                "✅"
                                                if validation_data.get("aligned", False)
                                        else "❌"
                                    )
                                    print(
                                        f"       {status_icon} {validation_name.replace('_', ' ').title()}: {score:.0f}%"
                                    )

                        # Show discrepancies
                        if discrepancies:
                            print(
                                f"  ⚠️  Evidence Discrepancies: {len(discrepancies)} flagged"
                            )
                            for discrepancy in discrepancies[:2]:  # Show first 2
                                print(f"     - {discrepancy}")
                            if len(discrepancies) > 2:
                                print(
                                    f"     ... and {len(discrepancies) - 2} more discrepancies"
                                )

                        # Show warnings
                        if warnings:
                            print(f"  ⚡ Evidence Warnings: {len(warnings)} noted")
                            for warning in warnings[:1]:  # Show first warning
                                print(f"     - {warning}")
                            if len(warnings) > 1:
                                print(f"     ... and {len(warnings) - 1} more warnings")

                        # Log evidence summary if available
                        if "evidence_summary" in ai_profile:
                            evidence_summary = ai_profile["evidence_summary"]
                            print(
                                f"  📊 Evidence Summary: {evidence_summary.get('validation_score', 0):.1f}% validation score"
                            )

                    # Log cost information
                        cost_usd = cost_data.get("total_cost_usd", 0.0)
                        tokens = cost_data.get("total_tokens", 0)
                        evidence_indicator = "🧠" if agno_evidence else "🤖"
                        print(
                            f"  {evidence_indicator} AI Profile Cost: ${cost_usd:.6f} ({tokens} tokens)"
                        )

                        # PHASE 3: Market Data Validation (after AI profiling)
                        # Only perform if we have app_concept from AI profile
                        market_validation_threshold = HYBRID_STRATEGY_CONFIG[
                            "market_validation"
                        ]["threshold"]
                        if (
                            HYBRID_STRATEGY_CONFIG["market_validation"]["enabled"]
                            and final_score >= market_validation_threshold
                            and ai_profile.get("app_concept")
                        ):
                            print(
                                f"  📊 Performing market validation (score {final_score:.1f} >= threshold {market_validation_threshold})..."
                            )

                        # Prepare data for market validation
                        validation_input = {
                            "app_concept": ai_profile.get("app_concept", ""),
                            "target_market": ai_profile.get("target_user", "B2C"),
                            "problem_description": ai_profile.get(
                                "problem_description", formatted["text"][:500]
                            ),
                        }

                        market_evidence = perform_market_validation(validation_input)

                        if market_evidence:
                            # Store evidence in analysis for downstream processing
                            evidence_dict = {
                                "validation_score": market_evidence.validation_score,
                                "data_quality_score": market_evidence.data_quality_score,
                                "reasoning": market_evidence.reasoning,
                                "total_cost": market_evidence.total_cost,
                                "timestamp": market_evidence.timestamp.isoformat()
                                if market_evidence.timestamp
                                else None,
                                "competitors_found": [
                                    p.company_name
                                    for p in market_evidence.competitor_pricing
                                ],
                                "tam_value": market_evidence.market_size.tam_value
                                if market_evidence.market_size
                                else None,
                                "growth_rate": market_evidence.market_size.growth_rate
                                if market_evidence.market_size
                                else None,
                                "similar_launches_count": len(
                                    market_evidence.similar_launches
                                ),
                            }
                            analysis["market_validation_evidence"] = evidence_dict

                            # Update tracking stats
                            market_validation_stats["validation_count"] += 1
                            market_validation_stats["total_validation_score"] += (
                                market_evidence.validation_score
                            )
                            market_validation_stats["total_data_quality_score"] += (
                                market_evidence.data_quality_score
                            )
                            market_validation_stats["total_validation_cost"] += (
                                market_evidence.total_cost
                            )
                            market_validation_stats["competitors_found"] += len(
                                market_evidence.competitor_pricing
                            )
                            if market_evidence.market_size:
                                market_validation_stats["market_sizes_found"] += 1
                            market_validation_stats["similar_launches_found"] += len(
                                market_evidence.similar_launches
                            )

                            # Log validation results
                            print(
                                f"  📈 Market Validation: {market_evidence.validation_score:.1f}/100 (quality: {market_evidence.data_quality_score:.1f}/100)"
                            )
                            print(
                                f"     Competitors: {', '.join(evidence_dict['competitors_found'][:3]) if evidence_dict['competitors_found'] else 'None found'}"
                            )
                            if evidence_dict["tam_value"]:
                                print(
                                    f"     Market Size: {evidence_dict['tam_value']} ({evidence_dict.get('growth_rate', 'N/A')})"
                                )
                            print(
                                f"     Similar Launches: {evidence_dict['similar_launches_count']} found"
                            )
                            print(
                                f"     Validation Cost: ${market_evidence.total_cost:.6f}"
                            )
                        elif not HYBRID_STRATEGY_CONFIG["market_validation"]["enabled"]:
                            pass  # Silently skip if disabled
                        elif not HYBRID_STRATEGY_CONFIG["market_validation"][
                            "jina_api_key"
                        ]:
                            pass  # Already warned in perform_market_validation
                        else:
                            print(f"  ⚠️  Market validation skipped or failed")

                    except Exception as e:
                        print(f"  ⚠️  Fresh profiling failed: {e}")
                        # Continue with basic scoring without AI profile

                else:
                    # Skip AI profiling and copy from primary opportunity
                    print(f"  🔄 High score ({final_score:.1f}) - skipping AI profiling, copying from concept {concept_id}...")

                    # Copy AI profile from primary opportunity
                    copied_profile = copy_profiler_from_primary(submission, concept_id, supabase)

                    if copied_profile:
                        # Successfully copied profile
                        analysis.update(copied_profile)

                        # Ensure cost_tracking is set with copy metadata
                        analysis["cost_tracking"] = {
                            "total_cost_usd": 0.0,  # No cost for copied profiles
                            "total_tokens": 0,
                            "operation_type": "copied_from_primary",
                            "concept_id": concept_id,
                            "copied_at": datetime.now().isoformat()
                        }

                        print(f"  ✅ AI profile copied successfully from concept {concept_id}")
                    else:
                        # Copy failed, fallback to fresh profiling
                        print(f"  ⚠️  Failed to copy AI profile from concept {concept_id}, running fresh profiling as fallback...")

                        # Generate real AI app profile with cost tracking
                        try:
                            # Prepare Agno evidence if available from hybrid analysis
                            agno_evidence = None
                            if hybrid_results and "llm_analysis" in hybrid_results:
                                # Extract the Agno analysis data that was used for Option A
                                agno_evidence = {
                                    "willingness_to_pay_score": hybrid_results["llm_analysis"].get("willingness_to_pay_score", 50),
                                    "customer_segment": hybrid_results["llm_analysis"].get("customer_segment", "Unknown"),
                                    "sentiment_toward_payment": hybrid_results["llm_analysis"].get("payment_sentiment", "Neutral"),
                                    "urgency_level": hybrid_results["llm_analysis"].get("urgency_level", "Low"),
                                    "mentioned_price_points": hybrid_results["llm_analysis"].get("mentioned_price_points", []),
                                    "existing_payment_behavior": hybrid_results["llm_analysis"].get("existing_payment_behavior", "Not specified"),
                                    "payment_friction_indicators": hybrid_results["llm_analysis"].get("payment_friction_indicators", []),
                                    "confidence": hybrid_results["llm_analysis"].get("confidence", 0.7),
                                }
                                print(f"  🧠 Evidence-based profiling: Using Agno analysis (WTP: {agno_evidence['willingness_to_pay_score']}/100)")

                            # Use the enhanced evidence-based profiling method
                            if agno_evidence:
                                # Use dedicated evidence-based method
                                ai_profile = llm_profiler.generate_app_profile_with_evidence(
                                    text=formatted["text"],
                                    title=formatted["title"],
                                    subreddit=formatted["subreddit"],
                                    score=final_score,
                                    agno_analysis=agno_evidence,
                                )
                                # Extract cost data from profile (embedded by evidence-based method)
                                cost_data = ai_profile.get("cost_tracking", {})
                                print("  ✅ Enhanced evidence-based profiling completed (fallback)")
                            else:
                                # Fallback to standard method with cost tracking
                                ai_profile, cost_data = llm_profiler.generate_app_profile_with_costs(
                                    text=formatted["text"],
                                    title=formatted["title"],
                                    subreddit=formatted["subreddit"],
                                    score=final_score,
                                    agno_analysis=agno_evidence,
                                )
                                print("  🤖 Standard AI profiling (fallback - no evidence available)")

                            # Merge AI profile into analysis and store cost data
                            analysis.update(ai_profile)
                            analysis["cost_tracking"] = cost_data

                            # Update concept profiler stats for fallback profiling
                            update_concept_profiler_stats(concept_id, ai_profile, supabase)

                            # Log cost information for fallback
                            cost_usd = cost_data.get("total_cost_usd", 0.0)
                            tokens = cost_data.get("total_tokens", 0)
                            evidence_indicator = "🧠" if agno_evidence else "🤖"
                            print(f"  {evidence_indicator} Fallback AI Profile Cost: ${cost_usd:.6f} ({tokens} tokens)")

                        except Exception as fallback_e:
                            print(f"  ⚠️  Fallback AI profiling also failed: {fallback_e}")
                            # Continue with basic scoring without AI profile

            else:
                # Score too low for AI enrichment
                print(
                    f"  📊 Score {final_score:.1f} below AI threshold ({ai_profile_threshold}) - basic scoring only"
                )

            # Map subreddit to sector
            sector = map_subreddit_to_sector(submission.get("subreddit", ""))
            analysis["sector"] = sector

            # Prepare for DLT storage - use submission_id from app_opportunities
            submission_id = submission.get("submission_id", submission.get("id"))

            # Extract trust data from submission
            trust_data = {
                "trust_score": submission.get("trust_score"),
                "trust_badge": submission.get("trust_badge"),
                "activity_score": submission.get("activity_score"),
            }

            scored_opp = prepare_analysis_for_storage(
                submission_id, analysis, sector, trust_data
            )

            # Track for batch loading
            scored_opportunities.append(scored_opp)

            # Add metadata for reporting
            analysis["stored"] = False  # Will be updated after DLT load
            analysis["opportunity_id"] = f"opp_{submission_id}"
            analysis_results.append(analysis)

        except Exception as e:
            print(f"Error processing submission {submission.get('id', 'unknown')}: {e}")
            # Add error entry but continue processing
            analysis_results.append(
                {
                    "submission_id": submission.get("id", "unknown"),
                    "error": str(e),
                    "stored": False,
                    "final_score": 0,
                }
            )
            continue

    print("\n  📊 AI Enrichment Summary:")
    print(f"    - Total submissions: {total_submissions}")
    print(f"    - AI threshold: {ai_profile_threshold}")
    print(
        f"    - Qualified for AI: {high_score_count}/{total_submissions} ({(high_score_count / total_submissions * 100):.1f}%)"
    )

    if high_score_count > 0:
        print(f"    - ✅ Generated {high_score_count} AI profiles with LLM enrichment")
    else:
        print("    - ⚠️  WARNING: No AI profiles generated!")
        print(
            f"    - 🔍 ALL {total_submissions} opportunities scored below the {ai_profile_threshold} threshold"
        )
        print("    - 💡 Consider:")
        print(
            f"      - Lowering AI threshold: SCORE_THRESHOLD={max(20.0, ai_profile_threshold - 10.0)}"
        )
        print("      - Collecting higher-quality Reddit data")
        print("      - Improving opportunity scoring algorithm")
        print("      - Checking subreddit selection for better pain points")

        # Additional insights for low scores
        avg_score = sum(
            r.get("final_score", 0) for r in analysis_results if "final_score" in r
        ) / len(analysis_results)
        print(
            f"    - 📈 Average score: {avg_score:.1f} (threshold gap: {ai_profile_threshold - avg_score:.1f})"
        )

    # Market validation summary for this batch
    if market_validation_stats["validation_count"] > 0:
        print("\n  📊 Market Validation Summary (This Batch):")
        print(
            f"    - Validations performed: {market_validation_stats['validation_count']}"
        )
        avg_val_score = (
            market_validation_stats["total_validation_score"]
            / market_validation_stats["validation_count"]
        )
        avg_quality_score = (
            market_validation_stats["total_data_quality_score"]
            / market_validation_stats["validation_count"]
        )
        print(f"    - Avg validation score: {avg_val_score:.1f}/100")
        print(f"    - Avg data quality: {avg_quality_score:.1f}/100")
        print(
            f"    - Competitors found: {market_validation_stats['competitors_found']}"
        )
        print(
            f"    - Market sizes found: {market_validation_stats['market_sizes_found']}"
        )
        print(
            f"    - Similar launches: {market_validation_stats['similar_launches_found']}"
        )
        print(
            f"    - Total validation cost: ${market_validation_stats['total_validation_cost']:.6f}"
        )

    return (
        analysis_results,
        scored_opportunities,
        high_score_count,
        market_validation_stats,
    )


def generate_summary_report(
    all_results: list[dict[str, Any]], elapsed_time: float, total_submissions: int
) -> None:
    """
    Generate and print a comprehensive summary report.

    Args:
        all_results: List of all analysis results
        elapsed_time: Total processing time in seconds
        total_submissions: Total number of submissions processed
    """
    print("\n" + "=" * 80)
    print("BATCH OPPORTUNITY SCORING - SUMMARY REPORT")
    print("=" * 80)

    # Basic statistics
    successful = sum(1 for r in all_results if r.get("stored", False))
    failed = len(all_results) - successful

    print("\nProcessing Statistics:")
    print(f"  Total Submissions:     {total_submissions:,}")
    print(f"  Successfully Scored:   {successful:,}")
    print(f"  Failed:                {failed:,}")
    print(f"  Success Rate:          {(successful / total_submissions * 100):.1f}%")
    print(f"  Total Time:            {elapsed_time:.2f} seconds")
    print(f"  Average Time/Item:     {(elapsed_time / total_submissions):.3f} seconds")
    print(
        f"  Processing Rate:       {(total_submissions / elapsed_time):.1f} items/second"
    )

    # Score distribution
    valid_results = [r for r in all_results if r.get("stored", False)]

    if valid_results:
        print("\nScore Distribution:")
        high_priority = sum(1 for r in valid_results if r.get("final_score", 0) >= 85)
        med_high = sum(1 for r in valid_results if 70 <= r.get("final_score", 0) < 85)
        medium = sum(1 for r in valid_results if 55 <= r.get("final_score", 0) < 70)
        low = sum(1 for r in valid_results if 40 <= r.get("final_score", 0) < 55)
        not_recommended = sum(1 for r in valid_results if r.get("final_score", 0) < 40)

        print(
            f"  High Priority (85+):   {high_priority:,} ({high_priority / len(valid_results) * 100:.1f}%)"
        )
        print(
            f"  Med-High (70-84):      {med_high:,} ({med_high / len(valid_results) * 100:.1f}%)"
        )
        print(
            f"  Medium (55-69):        {medium:,} ({medium / len(valid_results) * 100:.1f}%)"
        )
        print(
            f"  Low (40-54):           {low:,} ({low / len(valid_results) * 100:.1f}%)"
        )
        print(
            f"  Not Recommended (<40): {not_recommended:,} ({not_recommended / len(valid_results) * 100:.1f}%)"
        )

        # Average scores by dimension
        print("\nAverage Dimension Scores:")
        avg_market = sum(
            r.get("dimension_scores", {}).get("market_demand", 0) for r in valid_results
        ) / len(valid_results)
        avg_pain = sum(
            r.get("dimension_scores", {}).get("pain_intensity", 0)
            for r in valid_results
        ) / len(valid_results)
        avg_monetization = sum(
            r.get("dimension_scores", {}).get("monetization_potential", 0)
            for r in valid_results
        ) / len(valid_results)
        avg_gap = sum(
            r.get("dimension_scores", {}).get("market_gap", 0) for r in valid_results
        ) / len(valid_results)
        avg_tech = sum(
            r.get("dimension_scores", {}).get("technical_feasibility", 0)
            for r in valid_results
        ) / len(valid_results)
        avg_final = sum(r.get("final_score", 0) for r in valid_results) / len(
            valid_results
        )

        print(f"  Market Demand:         {avg_market:.1f}/100")
        print(f"  Pain Intensity:        {avg_pain:.1f}/100")
        print(f"  Monetization:          {avg_monetization:.1f}/100")
        print(f"  Market Gap:            {avg_gap:.1f}/100")
        print(f"  Technical Feasibility: {avg_tech:.1f}/100")
        print(f"  Final Score:           {avg_final:.1f}/100")

        # Sector breakdown
        sector_counts = {}
        for r in valid_results:
            sector = r.get("sector", "Unknown")
            sector_counts[sector] = sector_counts.get(sector, 0) + 1

        print("\nOpportunities by Sector:")
        for sector, count in sorted(
            sector_counts.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {sector:25} {count:,} ({count / len(valid_results) * 100:.1f}%)")

        # Top opportunities
        print("\nTop 10 Opportunities:")
        top_opps = sorted(
            valid_results, key=lambda x: x.get("final_score", 0), reverse=True
        )[:10]
        for i, opp in enumerate(top_opps, 1):
            title = opp.get("title", "No title")[:60]
            score = opp.get("final_score", 0)
            sector = opp.get("sector", "Unknown")
            subreddit = opp.get("subreddit", "Unknown")
            print(f"  {i:2}. [{score:.1f}] r/{subreddit:20} {title}")

    print("\n" + "=" * 80)
    print("Report Complete!")
    print("=" * 80 + "\n")


def refresh_problem_metrics(supabase, submission_ids: list[str]) -> None:
    """
    Refresh problem metrics for the given submissions.

    This function is called after opportunities are loaded to calculate and store
    Reddit validation signals (comment count, trending score, intent signals, etc.)
    in the problem_metrics table.

    Args:
        supabase: Supabase client
        submission_ids: List of submission UUIDs to refresh metrics for
    """
    if not submission_ids:
        print("  No submissions to refresh metrics for")
        return

    print(f"\n📊 Refreshing problem metrics for {len(submission_ids)} submissions...")

    try:
        # Call the refresh_problem_metrics function for each submission
        # This function is defined in the problem_metrics migration
        for submission_id in submission_ids:
            try:
                # Execute the stored function to refresh metrics
                response = supabase.rpc(
                    "refresh_problem_metrics", {"p_problem_id": submission_id}
                ).execute()

            except Exception as e:
                # Log but don't fail - metrics are secondary to scoring
                print(
                    f"  ⚠️  Could not refresh metrics for {submission_id[:8]}...: {str(e)[:50]}"
                )
                continue

        print(f"✓ Problem metrics refreshed for {len(submission_ids)} submissions")

    except Exception as e:
        print(f"⚠️  Metrics refresh unavailable: {str(e)[:100]}")
        print("  (This is expected if problem_metrics table hasn't been created yet)")
        print(
            "  Run: psql -f supabase/migrations/20251110151231_add_problem_metrics_table.sql"
        )


def main():
    """
    Main execution function for batch opportunity scoring (DLT-powered).
    """
    # Initialize HTTP clients FIRST to prevent connection pool exhaustion
    initialize_http_clients()

    # Read score threshold from environment variable (default: 40.0)
    import os

    score_threshold = float(os.getenv("SCORE_THRESHOLD", "40.0"))

    # Track AI profile generation for final reporting
    ai_profiles_generated = 0

    print("\n" + "=" * 80)
    print("BATCH OPPORTUNITY SCORING - DLT-POWERED")
    print("=" * 80 + "\n")
    print("Features:")
    print("  ✓ DLT Pipeline: Enabled")
    print("  ✓ Incremental Loading: Automatic")
    print("  ✓ Constraint Validation: DLT-Native (1-3 Function Rule)")
    print("  ✓ Deduplication: Merge disposition")
    print(f"  ✓ AI Profile Threshold: {score_threshold}")

    # Market Validation Configuration
    market_val_enabled = HYBRID_STRATEGY_CONFIG["market_validation"]["enabled"]
    market_val_threshold = HYBRID_STRATEGY_CONFIG["market_validation"]["threshold"]
    jina_configured = bool(HYBRID_STRATEGY_CONFIG["market_validation"]["jina_api_key"])

    if market_val_enabled and jina_configured:
        print(f"  ✓ Market Validation: Enabled (threshold: {market_val_threshold})")
    elif market_val_enabled and not jina_configured:
        print(f"  ⚠️ Market Validation: Enabled but JINA_API_KEY not configured")
    else:
        print("  ✗ Market Validation: Disabled")
    print("")

    start_time = time.time()

    # Initialize clients
    print("Initializing connections...")
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        agent = OpportunityAnalyzerAgent()

        # Initialize LLM profiler for high-score opportunities
        llm_profiler = None
        try:
            llm_profiler = EnhancedLLMProfiler()
            print("✓ Connections initialized successfully")
            print("  - Supabase: Connected")
            print("  - OpportunityAnalyzerAgent: Ready")
            print("  - LLM Profiler: Ready (Claude Haiku via OpenRouter)")
            print("  - DLT Pipeline: Available")
        except Exception as e:
            print(f"⚠️  LLM Profiler unavailable ({e})")
            print("  - Continuing with scoring only (no AI profiles)")
            print("✓ Connections initialized successfully")
            print("  - Supabase: Connected")
            print("  - OpportunityAnalyzerAgent: Ready")
            print("  - DLT Pipeline: Available")
    except Exception as e:
        print(f"✗ Error initializing: {e}")
        return

    # Fetch submissions
    print("\nFetching submissions from database...")
    try:
        submissions = fetch_submissions(supabase)
        if not submissions:
            print("No submissions to process. Exiting.")
            return
        print(f"✓ Found {len(submissions):,} submissions to process")
    except Exception as e:
        print(f"✗ Error fetching submissions: {e}")
        return

    # Process in batches
    print(f"\n{'=' * 80}")
    print("PROCESSING SUBMISSIONS IN BATCHES")
    print(f"{'=' * 80}")
    all_results = []
    all_scored_opportunities = []
    batch_size = 100
    num_batches = (len(submissions) + batch_size - 1) // batch_size

    # Aggregate market validation statistics
    total_market_validation_stats = {
        "validation_count": 0,
        "total_validation_score": 0.0,
        "total_data_quality_score": 0.0,
        "total_validation_cost": 0.0,
        "competitors_found": 0,
        "market_sizes_found": 0,
        "similar_launches_found": 0,
    }

    print(f"Total batches: {num_batches}")
    print(f"Batch size: {batch_size} submissions")
    print("Starting processing with progress bar...\n")

    # Use tqdm for overall progress
    for i in tqdm(
        range(0, len(submissions), batch_size), desc="Processing batches", unit="batch"
    ):
        batch = submissions[i : i + batch_size]
        batch_num = (i // batch_size) + 1

        try:
            # Process batch (returns analysis results, scored opportunities, AI profile count, and market validation stats)
            results, scored_opps, ai_profiles_count, batch_market_stats = process_batch(
                batch, agent, batch_num, llm_profiler, score_threshold, supabase
            )
            all_results.extend(results)
            all_scored_opportunities.extend(scored_opps)
            ai_profiles_generated += ai_profiles_count

            # Aggregate market validation statistics
            for key in total_market_validation_stats:
                total_market_validation_stats[key] += batch_market_stats.get(key, 0)

        except Exception as e:
            print(f"\n✗ Error processing batch {batch_num}: {e}")
            print("   Continuing with next batch...\n")
            continue

    # Calculate processing time
    processing_time = time.time() - start_time

    # Generate cost summary if AI profiles were generated
    cost_summary = None
    if ai_profiles_generated > 0 and llm_profiler:
        cost_summary = llm_profiler.get_cost_summary(all_scored_opportunities)
        print("\n💰 AI ENRICHMENT COST SUMMARY")
        print(f"   Total Cost: ${cost_summary['total_cost_usd']:.6f}")
        print(f"   Total Tokens: {cost_summary['total_tokens']:,}")
        print(f"   Avg Cost per Profile: ${cost_summary['avg_cost_per_profile']:.6f}")

        # Log model breakdown
        for model, stats in cost_summary["model_breakdown"].items():
            print(
                f"   {model}: {stats['count']} profiles, ${stats['cost']:.6f}, {stats['tokens']} tokens"
            )

        # Evidence-based analysis metrics
        evidence_based_profiles = sum(
            1 for opp in all_scored_opportunities if opp.get("evidence_based", False)
        )
        if evidence_based_profiles > 0:
            print("\n🧠 EVIDENCE-BASED PROFILING METRICS")
            print(
                f"   Evidence-based profiles: {evidence_based_profiles}/{ai_profiles_generated} ({(evidence_based_profiles / ai_profiles_generated * 100):.1f}%)"
            )
            print(
                f"   Standard AI profiles: {ai_profiles_generated - evidence_based_profiles}"
            )

            # Calculate evidence validation metrics
            validation_scores = []
            discrepancy_count = 0
            for opp in all_scored_opportunities:
                if opp.get("evidence_validation"):
                    validation_scores.append(
                        opp["evidence_validation"].get("alignment_score", 0)
                    )
                    discrepancy_count += len(
                        opp["evidence_validation"].get("discrepancies", [])
                    )

            if validation_scores:
                avg_alignment = sum(validation_scores) / len(validation_scores)
                print(f"   Average evidence alignment: {avg_alignment:.1f}%")
                print(f"   Total evidence discrepancies: {discrepancy_count}")

                # Count alignment status categories
                alignment_categories = {}
                for opp in all_scored_opportunities:
                    if opp.get("evidence_validation"):
                        status = opp["evidence_validation"].get(
                            "overall_status", "unknown"
                        )
                        alignment_categories[status] = (
                            alignment_categories.get(status, 0) + 1
                        )

                if alignment_categories:
                    print("   Alignment distribution:")
                    for status, count in alignment_categories.items():
                        print(f"     - {status.replace('_', ' ').title()}: {count}")
        else:
            print("\n📊 AI PROFILING NOTE")
            print("   Standard AI profiling only (no Agno evidence integration)")
            print("   Enable MONETIZATION_LLM_ENABLED=true for evidence-based analysis")

    # Market Validation Summary (Phase 3)
    if total_market_validation_stats["validation_count"] > 0:
        print("\n📊 MARKET VALIDATION SUMMARY (Phase 3)")
        print(
            f"   Total Validations: {total_market_validation_stats['validation_count']}"
        )
        avg_val_score = (
            total_market_validation_stats["total_validation_score"]
            / total_market_validation_stats["validation_count"]
        )
        avg_quality = (
            total_market_validation_stats["total_data_quality_score"]
            / total_market_validation_stats["validation_count"]
        )
        print(f"   Avg Validation Score: {avg_val_score:.1f}/100")
        print(f"   Avg Data Quality: {avg_quality:.1f}/100")
        print(
            f"   Total Competitors Found: {total_market_validation_stats['competitors_found']}"
        )
        print(
            f"   Market Sizes Discovered: {total_market_validation_stats['market_sizes_found']}"
        )
        print(
            f"   Similar Product Launches: {total_market_validation_stats['similar_launches_found']}"
        )
        print(
            f"   Total Validation Cost: ${total_market_validation_stats['total_validation_cost']:.6f}"
        )

        # Calculate combined cost (AI profiling + market validation)
        if cost_summary:
            combined_cost = (
                cost_summary["total_cost_usd"]
                + total_market_validation_stats["total_validation_cost"]
            )
            print(f"\n   Combined Analysis Cost: ${combined_cost:.6f}")
            print(f"     - AI Profiling: ${cost_summary['total_cost_usd']:.6f}")
            print(
                f"     - Market Validation: ${total_market_validation_stats['total_validation_cost']:.6f}"
            )
    elif HYBRID_STRATEGY_CONFIG["market_validation"]["enabled"]:
        print("\n📊 MARKET VALIDATION NOTE")
        print(
            "   No market validations performed (opportunities below threshold or missing app_concept)"
        )
        if not HYBRID_STRATEGY_CONFIG["market_validation"]["jina_api_key"]:
            print(
                "   WARNING: JINA_API_KEY not configured - market validation disabled"
            )

    # Load all scored opportunities to Supabase via DLT (batch operation)
    print(f"\n{'=' * 80}")
    print("LOADING SCORED OPPORTUNITIES TO SUPABASE")
    print(f"{'=' * 80}")

    # Filter to only include opportunities with function_list (i.e., those with AI profiles)
    opportunities_with_functions = [
        opp
        for opp in all_scored_opportunities
        if opp.get("function_list") and len(opp.get("function_list", [])) > 0
    ]

    print(f"Total opportunities analyzed: {len(all_scored_opportunities):,}")
    print(
        f"Opportunities with AI profiles (function_list): {len(opportunities_with_functions):,}"
    )
    print(
        f"Filtered out (no AI profile): {len(all_scored_opportunities) - len(opportunities_with_functions):,}"
    )

    dlt_load_start = time.time()
    load_success = load_scores_to_supabase_via_dlt(opportunities_with_functions)
    dlt_load_time = time.time() - dlt_load_start

    # Also store AI profiles to app_opportunities table via DLT (with deduplication)
    print("\n📤 Storing AI-generated profiles to app_opportunities via DLT...")
    ai_stored_count = store_ai_profiles_to_app_opportunities_via_dlt(
        all_scored_opportunities
    )
    if ai_stored_count > 0:
        print(
            f"✓ Stored {ai_stored_count} AI-generated app profiles (deduplicated on submission_id)"
        )
    else:
        print("  No AI profiles to store (score threshold not met)")

    # HYBRID STRATEGY: Store Option A & B results to their respective tables
    print(f"\n{'=' * 60}")
    print("HYBRID STRATEGY - STORING OPTION A & B RESULTS")
    print(f"{'=' * 60}")

    hybrid_counts = store_hybrid_results_to_database(all_results)
    print("\n📊 Hybrid Strategy Summary:")
    print(f"   Option A (LLM Analysis): {hybrid_counts['llm_analyses']} records stored")
    print(
        f"   Option B (Customer Leads): {hybrid_counts['customer_leads']} records stored"
    )

    if hybrid_counts["llm_analyses"] > 0 or hybrid_counts["customer_leads"] > 0:
        print(
            f"   ✅ Hybrid strategy successfully enhanced {hybrid_counts['llm_analyses'] + hybrid_counts['customer_leads']} opportunities"
        )
    else:
        print("   ⚠️  No hybrid results stored (opportunities below 60-point threshold)")

    # Refresh problem metrics for credibility tracking
    submission_ids = [sub.get("id") for sub in submissions if sub.get("id")]
    refresh_problem_metrics(supabase, submission_ids)

    # Update stored status in results
    if load_success:
        for result in all_results:
            if "error" not in result:
                result["stored"] = True

    # Calculate total elapsed time
    elapsed_time = time.time() - start_time

    # Generate summary report
    print(f"\n{'=' * 80}")
    print("GENERATING SUMMARY REPORT")
    print(f"{'=' * 80}")
    generate_summary_report(all_results, elapsed_time, len(submissions))

    # Print DLT-specific metrics
    print(f"\n{'=' * 80}")
    print("DLT PIPELINE METRICS")
    print(f"{'=' * 80}")
    print(f"Processing time:       {processing_time:.2f}s")
    print(f"DLT load time:         {dlt_load_time:.2f}s")
    print(f"Total time:            {elapsed_time:.2f}s")
    print(f"Load success:          {'✓ Yes' if load_success else '✗ No'}")
    print("Deduplication:         Enabled (merge disposition)")
    print("Primary key:           opportunity_id")
    print("Target table:          opportunity_scores")
    print("Constraint validation: DLT-Native (1-3 function rule)")
    print(f"{'=' * 80}\n")

    if load_success:
        print("✓ Batch opportunity scoring completed successfully!")

        # AI Profile Generation Status
        if ai_profiles_generated == 0:
            print(f"\n{'=' * 80}")
            print("⚠️  AI PROFILE GENERATION WARNING")
            print(f"{'=' * 80}")
            print("No AI profiles were generated in this run.")
            print(f"🔍 Threshold: {score_threshold}")
            print(f"📊 Opportunities processed: {len(submissions)}")
            print(
                f"📈 Best score: {max(r.get('final_score', 0) for r in all_results):.1f}"
            )
            print("🎯 Recommended actions:")
            print(
                f"  • Run with lower threshold: SCORE_THRESHOLD={max(20.0, score_threshold - 15.0)}"
            )
            print("  • Collect data from higher-engagement subreddits")
            print("  • Target posts with stronger pain indicators")
            print("  • Consider current market conditions and trending topics")
            print(f"{'=' * 80}")
        else:
            print(f"\n✅ Generated {ai_profiles_generated} AI profiles successfully!")
    else:
        print("⚠️  Batch opportunity scoring completed with warnings (DLT load failed)")


if __name__ == "__main__":
    main()
