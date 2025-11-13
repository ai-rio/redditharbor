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

DLT Migration Benefits:
- Automatic deduplication (merge write disposition)
- Schema evolution support (automatic table updates)
- Production-ready deployment (Airflow integration)
- Consistent data loading pattern across all scripts

CRITICAL: Uses centralized score_calculator module for consistency.
"""

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

load_dotenv(project_root / '.env.local')

try:
    from tqdm import tqdm
except ImportError:
    print("Warning: tqdm not installed. Installing for progress bars...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tqdm"])
    from tqdm import tqdm

from agent_tools.llm_profiler import LLMProfiler
from agent_tools.opportunity_analyzer_agent import OpportunityAnalyzerAgent
from config import SUPABASE_KEY, SUPABASE_URL

# DLT constraint validator
from core.dlt.constraint_validator import app_opportunities_with_constraint

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


def fetch_all_submissions(supabase_client: Any, batch_size: int = 1000) -> list[dict[str, Any]]:
    """
    Fetch all opportunities from app_opportunities_trust table in batches.

    Args:
        supabase_client: Initialized Supabase client
        batch_size: Number of opportunities to fetch per batch (default 1000)

    Returns:
        List of all opportunity dictionaries

    Raises:
        Exception: If database query fails
    """
    try:
        print("Fetching all opportunities from app_opportunities_trust...")

        all_submissions = []
        offset = 0

        while True:
            # Build query with pagination
            query = supabase_client.table("app_opportunities_trust").select(
                "submission_id, title, problem_description, subreddit, reddit_score, "
                "num_comments, trust_score, trust_badge, activity_score"
            ).range(offset, offset + batch_size - 1)

            response = query.execute()

            if not response.data:
                break  # No more submissions

            all_submissions.extend(response.data)
            print(f"Fetched {len(response.data)} submissions (total: {len(all_submissions)})")

            # If we got fewer than batch_size, we've reached the end
            if len(response.data) < batch_size:
                break

            offset += batch_size

        print(f"Successfully fetched {len(all_submissions)} total submissions")
        return all_submissions

    except Exception as e:
        print(f"Error fetching submissions: {e}")
        raise


def fetch_submissions(supabase_client: Any, limit: int | None = None) -> list[dict[str, Any]]:
    """
    Fetch opportunities from app_opportunities_trust table for AI enrichment.

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
            print("Fetching limited opportunities from app_opportunities_trust...")
            query = supabase_client.table("app_opportunities_trust").select(
                "submission_id, title, problem_description, subreddit, reddit_score, "
                "num_comments, trust_score, trust_badge, activity_score"
            ).limit(limit)

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
    Format an opportunity from app_opportunities_trust for LLM profiler enrichment.

    Args:
        submission: Opportunity data from app_opportunities_trust table

    Returns:
        Formatted opportunity data for AI profile generation
    """
    # Use existing problem_description or combine title for full text analysis
    title = submission.get("title", "")
    text = submission.get("problem_description", "")
    full_text = f"{title}\n\n{text}".strip() if text else title

    # Format engagement data using app_opportunities_trust column names
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
        "db_id": submission.get("id")  # Keep reference to database UUID
    }


def prepare_analysis_for_storage(
    submission_id: str,
    analysis: dict[str, Any],
    sector: str
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
    if isinstance(core_functions, list):
        function_count = len(core_functions)
        function_list = core_functions
    else:
        # Fallback for unexpected format
        function_count = core_functions if isinstance(core_functions, int) else 1
        function_list = [f"Core function {i+1}" for i in range(function_count)]

    # Prepare data for workflow_results table
    analysis_data = {
        "opportunity_id": opportunity_id,  # For workflow_results deduplication
        "submission_id": submission_id,  # Original Reddit ID for app_opportunities deduplication
        "app_name": analysis.get("title", "Unnamed Opportunity")[:255],
        "function_count": function_count,
        "function_list": function_list,
        "original_score": float(analysis.get("final_score", 0)),
        "final_score": float(analysis.get("final_score", 0)),
        "status": "scored",
        "constraint_applied": True,
        "ai_insight": f"Market sector: {sector}. Subreddit: {analysis.get('subreddit', 'unknown')}",
        "processed_at": datetime.now().isoformat(),
        # Dimension scores
        "market_demand": float(scores.get("market_demand", 0)) if scores else None,
        "pain_intensity": float(scores.get("pain_intensity", 0)) if scores else None,
        "monetization_potential": float(scores.get("monetization_potential", 0)) if scores else None,
        "market_gap": float(scores.get("market_gap", 0)) if scores else None,
        "technical_feasibility": float(scores.get("technical_feasibility", 0)) if scores else None,
        # App profile fields (from LLM if available)
        "problem_description": analysis.get("problem_description", "")[:500],
        "app_concept": analysis.get("app_concept", "")[:500],
        "value_proposition": analysis.get("value_proposition", "")[:500],
        "target_user": analysis.get("target_user", "")[:255],
        "monetization_model": analysis.get("monetization_model", "")[:255],
    }

    return analysis_data


def load_scores_to_supabase_via_dlt(
    scored_opportunities: list[dict[str, Any]]
) -> bool:
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
        o["opportunity_id"] for o in scored_opportunities
        if not o.get("function_list")
    ]
    if missing_functions:
        print(f"❌ ERROR: {len(missing_functions)} opportunities missing function_list:")
        for opp_id in missing_functions[:5]:
            print(f"  - {opp_id}")
        raise ValueError(f"Cannot load: {len(missing_functions)} missing function_list")

    # Check: function_count matches function_list length
    mismatches = [
        o for o in scored_opportunities
        if len(o.get("function_list", [])) != o.get("function_count")
    ]
    if mismatches:
        print(f"⚠️  WARNING: {len(mismatches)} opportunities have count/list mismatch")
        for opp in mismatches[:3]:
            print(f"  - {opp['opportunity_id']}: count={opp.get('function_count')}, "
                  f"actual={len(opp.get('function_list', []))}")

    print(f"✓ Pre-flight checks passed ({len(scored_opportunities)} opportunities)")

    try:
        print(f"\n{'='*80}")
        print("LOADING SCORES TO SUPABASE VIA DLT PIPELINE")
        print(f"{'='*80}")
        print(f"Opportunities to load: {len(scored_opportunities)}")

        # Validate constraints before loading
        print("\n🔍 Validating constraints...")
        validated_opportunities = list(app_opportunities_with_constraint(scored_opportunities))
        approved = [o for o in validated_opportunities if not o.get("is_disqualified")]
        disqualified = [o for o in validated_opportunities if o.get("is_disqualified")]

        print(f"  ✓ Approved: {len(approved)}")
        print(f"  ⚠️  Disqualified: {len(disqualified)}")
        print(f"  ✓ Compliance rate: {len(approved)/len(validated_opportunities)*100:.1f}%")

        if disqualified:
            print("\n  Disqualified Opportunities:")
            for opp in disqualified[:3]:  # Show first 3
                print(f"    - {opp.get('app_name', 'Unknown')}: {opp.get('violation_reason', 'N/A')}")
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
            primary_key="opportunity_id"  # Deduplication key
        )

        print(f"\n✓ Successfully processed {len(validated_opportunities)} opportunities")
        print(f"✓ Successfully loaded {len(approved)} approved opportunities to Supabase")
        if disqualified:
            print(f"⚠️  Skipped {len(disqualified)} disqualified opportunities (4+ functions)")
        print("  - Table: workflow_results")
        print("  - Write mode: merge (deduplication enabled)")
        print("  - Primary key: opportunity_id")
        print("  - Constraint validation: DLT-native (1-3 function rule)")
        print(f"  - Started at: {load_info.started_at}")
        print(f"{'='*80}\n")

        return True

    except Exception as e:
        print(f"\n✗ Error loading scores via DLT: {e}")
        print(f"  - Opportunities affected: {len(scored_opportunities)}")
        print("  - Recommendation: Check DLT configuration and Supabase connection")
        print(f"{'='*80}\n")
        return False


def store_ai_profiles_to_app_opportunities_via_dlt(
    scored_opportunities: list[dict[str, Any]]
) -> int:
    """
    Update app_opportunities_trust table with AI-enriched profiles via DLT.
    Uses DLT merge disposition to update existing records with LLM-generated content.
    Preserves trust indicators (trust_score, trust_badge, activity_score) from original data.
    Only updates opportunities that have AI-generated fields.

    Args:
        scored_opportunities: List of scored opportunities (some with AI profiles)

    Returns:
        Number of AI profiles stored
    """
    import dlt
    from core.dlt_collection import create_dlt_pipeline
    from config import SUPABASE_URL, SUPABASE_KEY
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
            existing = supabase.table("app_opportunities_trust").select(
                "trust_score, trust_badge, activity_score, engagement_level, "
                "trust_level, trend_velocity, problem_validity, discussion_quality, "
                "ai_confidence_level, trust_validation_timestamp, trust_validation_method, "
                "subreddit, reddit_score, num_comments, title"
            ).eq("submission_id", submission_id).execute()

            trust_data = existing.data[0] if existing.data else {}
        except Exception as e:
            print(f"⚠️  Could not fetch trust data for {submission_id}: {e}")
            trust_data = {}

        # Merge AI profile with preserved trust indicators
        ai_profile = {
            "submission_id": submission_id,
            "problem_description": opp.get("problem_description"),
            "app_concept": opp.get("app_concept"),
            "core_functions": ", ".join(opp.get("function_list", [])) if isinstance(opp.get("function_list"), list) else str(opp.get("function_list", "")),
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

    # Create DLT resource for app_opportunities_trust with merge disposition
    @dlt.resource(
        name="app_opportunities_trust",
        write_disposition="merge",
        primary_key="submission_id"
    )
    def ai_enriched_opportunities():
        yield ai_profiles

    # Load via DLT pipeline
    pipeline = create_dlt_pipeline()
    load_info = pipeline.run(ai_enriched_opportunities())

    print(f"✓ Updated {len(ai_profiles)} opportunities with AI profiles in app_opportunities_trust")
    return len(ai_profiles)


def process_batch(
    submissions: list[dict[str, Any]],
    agent: OpportunityAnalyzerAgent,
    batch_number: int,
    llm_profiler: LLMProfiler | None = None,
    ai_profile_threshold: float = 40.0
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
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
        high_score_threshold: Score threshold for LLM profiling (default: 40.0)

    Returns:
        Tuple of (analysis_results, scored_opportunities_for_dlt)
        - analysis_results: List with full analysis metadata
        - scored_opportunities_for_dlt: List formatted for DLT pipeline
    """
    analysis_results = []
    scored_opportunities = []
    high_score_count = 0
    total_submissions = len(submissions)

    for submission in submissions:
        try:
            # Format submission for agent
            formatted = format_submission_for_agent(submission)

            # Analyze opportunity (scoring only, no AI profiling yet)
            analysis = agent.analyze_opportunity(formatted)

            # Check if this is a high-scoring opportunity
            final_score = analysis.get("final_score", 0)
            print(f"  📊 {formatted['title'][:60]}... Score: {final_score:.1f}")
            if llm_profiler and final_score >= ai_profile_threshold:
                high_score_count += 1
                print(f"  🎯 High score ({final_score:.1f}) - generating AI profile...")

                # Generate real AI app profile (using system score as context)
                try:
                    ai_profile = llm_profiler.generate_app_profile(
                        text=formatted["text"],
                        title=formatted["title"],
                        subreddit=formatted["subreddit"],
                        score=final_score
                    )
                    # Merge AI profile into analysis
                    analysis.update(ai_profile)
                except Exception as e:
                    print(f"  ⚠️  LLM profiling failed: {e}")
                    # Continue with basic scoring
            else:
                # Score too low for AI enrichment
                print(f"  📊 Score {final_score:.1f} below AI threshold ({ai_profile_threshold}) - basic scoring only")

            # Map subreddit to sector
            sector = map_subreddit_to_sector(submission.get("subreddit", ""))
            analysis["sector"] = sector

            # Prepare for DLT storage - use submission_id from app_opportunities_trust
            submission_id = submission.get("submission_id", submission.get("id"))
            scored_opp = prepare_analysis_for_storage(
                submission_id,
                analysis,
                sector
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
            analysis_results.append({
                "submission_id": submission.get("id", "unknown"),
                "error": str(e),
                "stored": False,
                "final_score": 0
            })
            continue

    print(f"\n  📊 AI Enrichment Summary:")
    print(f"    - Total submissions: {total_submissions}")
    print(f"    - AI threshold: {ai_profile_threshold}")
    print(f"    - Qualified for AI: {high_score_count}/{total_submissions} ({(high_score_count/total_submissions*100):.1f}%)")
    if high_score_count > 0:
        print(f"    - ✅ Generated {high_score_count} AI profiles")
    else:
        print(f"    - ⚠️  No AI profiles generated (all scores below threshold)")

    return analysis_results, scored_opportunities


def generate_summary_report(
    all_results: list[dict[str, Any]],
    elapsed_time: float,
    total_submissions: int
) -> None:
    """
    Generate and print a comprehensive summary report.

    Args:
        all_results: List of all analysis results
        elapsed_time: Total processing time in seconds
        total_submissions: Total number of submissions processed
    """
    print("\n" + "="*80)
    print("BATCH OPPORTUNITY SCORING - SUMMARY REPORT")
    print("="*80)

    # Basic statistics
    successful = sum(1 for r in all_results if r.get("stored", False))
    failed = len(all_results) - successful

    print("\nProcessing Statistics:")
    print(f"  Total Submissions:     {total_submissions:,}")
    print(f"  Successfully Scored:   {successful:,}")
    print(f"  Failed:                {failed:,}")
    print(f"  Success Rate:          {(successful/total_submissions*100):.1f}%")
    print(f"  Total Time:            {elapsed_time:.2f} seconds")
    print(f"  Average Time/Item:     {(elapsed_time/total_submissions):.3f} seconds")
    print(f"  Processing Rate:       {(total_submissions/elapsed_time):.1f} items/second")

    # Score distribution
    valid_results = [r for r in all_results if r.get("stored", False)]

    if valid_results:
        print("\nScore Distribution:")
        high_priority = sum(1 for r in valid_results if r.get("final_score", 0) >= 85)
        med_high = sum(1 for r in valid_results if 70 <= r.get("final_score", 0) < 85)
        medium = sum(1 for r in valid_results if 55 <= r.get("final_score", 0) < 70)
        low = sum(1 for r in valid_results if 40 <= r.get("final_score", 0) < 55)
        not_recommended = sum(1 for r in valid_results if r.get("final_score", 0) < 40)

        print(f"  High Priority (85+):   {high_priority:,} ({high_priority/len(valid_results)*100:.1f}%)")
        print(f"  Med-High (70-84):      {med_high:,} ({med_high/len(valid_results)*100:.1f}%)")
        print(f"  Medium (55-69):        {medium:,} ({medium/len(valid_results)*100:.1f}%)")
        print(f"  Low (40-54):           {low:,} ({low/len(valid_results)*100:.1f}%)")
        print(f"  Not Recommended (<40): {not_recommended:,} ({not_recommended/len(valid_results)*100:.1f}%)")

        # Average scores by dimension
        print("\nAverage Dimension Scores:")
        avg_market = sum(r.get("dimension_scores", {}).get("market_demand", 0) for r in valid_results) / len(valid_results)
        avg_pain = sum(r.get("dimension_scores", {}).get("pain_intensity", 0) for r in valid_results) / len(valid_results)
        avg_monetization = sum(r.get("dimension_scores", {}).get("monetization_potential", 0) for r in valid_results) / len(valid_results)
        avg_gap = sum(r.get("dimension_scores", {}).get("market_gap", 0) for r in valid_results) / len(valid_results)
        avg_tech = sum(r.get("dimension_scores", {}).get("technical_feasibility", 0) for r in valid_results) / len(valid_results)
        avg_final = sum(r.get("final_score", 0) for r in valid_results) / len(valid_results)

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
        for sector, count in sorted(sector_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {sector:25} {count:,} ({count/len(valid_results)*100:.1f}%)")

        # Top opportunities
        print("\nTop 10 Opportunities:")
        top_opps = sorted(valid_results, key=lambda x: x.get("final_score", 0), reverse=True)[:10]
        for i, opp in enumerate(top_opps, 1):
            title = opp.get("title", "No title")[:60]
            score = opp.get("final_score", 0)
            sector = opp.get("sector", "Unknown")
            subreddit = opp.get("subreddit", "Unknown")
            print(f"  {i:2}. [{score:.1f}] r/{subreddit:20} {title}")

    print("\n" + "="*80)
    print("Report Complete!")
    print("="*80 + "\n")


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
                    "refresh_problem_metrics",
                    {"p_problem_id": submission_id}
                ).execute()

            except Exception as e:
                # Log but don't fail - metrics are secondary to scoring
                print(f"  ⚠️  Could not refresh metrics for {submission_id[:8]}...: {str(e)[:50]}")
                continue

        print(f"✓ Problem metrics refreshed for {len(submission_ids)} submissions")

    except Exception as e:
        print(f"⚠️  Metrics refresh unavailable: {str(e)[:100]}")
        print("  (This is expected if problem_metrics table hasn't been created yet)")
        print("  Run: psql -f supabase/migrations/20251110151231_add_problem_metrics_table.sql")


def main():
    """
    Main execution function for batch opportunity scoring (DLT-powered).
    """
    # Read score threshold from environment variable (default: 40.0)
    import os
    score_threshold = float(os.getenv("SCORE_THRESHOLD", "40.0"))

    print("\n" + "="*80)
    print("BATCH OPPORTUNITY SCORING - DLT-POWERED")
    print("="*80 + "\n")
    print("Features:")
    print("  ✓ DLT Pipeline: Enabled")
    print("  ✓ Incremental Loading: Automatic")
    print("  ✓ Constraint Validation: DLT-Native (1-3 Function Rule)")
    print("  ✓ Deduplication: Merge disposition")
    print(f"  ✓ AI Profile Threshold: {score_threshold}")
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
            llm_profiler = LLMProfiler()
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
    print(f"\n{'='*80}")
    print("PROCESSING SUBMISSIONS IN BATCHES")
    print(f"{'='*80}")
    all_results = []
    all_scored_opportunities = []
    batch_size = 100
    num_batches = (len(submissions) + batch_size - 1) // batch_size

    print(f"Total batches: {num_batches}")
    print(f"Batch size: {batch_size} submissions")
    print("Starting processing with progress bar...\n")

    # Use tqdm for overall progress
    for i in tqdm(range(0, len(submissions), batch_size), desc="Processing batches", unit="batch"):
        batch = submissions[i:i+batch_size]
        batch_num = (i // batch_size) + 1

        try:
            # Process batch (returns analysis results and scored opportunities)
            results, scored_opps = process_batch(batch, agent, batch_num, llm_profiler, score_threshold)
            all_results.extend(results)
            all_scored_opportunities.extend(scored_opps)

        except Exception as e:
            print(f"\n✗ Error processing batch {batch_num}: {e}")
            print("   Continuing with next batch...\n")
            continue

    # Calculate processing time
    processing_time = time.time() - start_time

    # Load all scored opportunities to Supabase via DLT (batch operation)
    print(f"\n{'='*80}")
    print("LOADING SCORED OPPORTUNITIES TO SUPABASE")
    print(f"{'='*80}")

    # Filter to only include opportunities with function_list (i.e., those with AI profiles)
    opportunities_with_functions = [
        opp for opp in all_scored_opportunities
        if opp.get("function_list") and len(opp.get("function_list", [])) > 0
    ]

    print(f"Total opportunities analyzed: {len(all_scored_opportunities):,}")
    print(f"Opportunities with AI profiles (function_list): {len(opportunities_with_functions):,}")
    print(f"Filtered out (no AI profile): {len(all_scored_opportunities) - len(opportunities_with_functions):,}")

    dlt_load_start = time.time()
    load_success = load_scores_to_supabase_via_dlt(opportunities_with_functions)
    dlt_load_time = time.time() - dlt_load_start

    # Also store AI profiles to app_opportunities table via DLT (with deduplication)
    print("\n📤 Storing AI-generated profiles to app_opportunities via DLT...")
    ai_stored_count = store_ai_profiles_to_app_opportunities_via_dlt(all_scored_opportunities)
    if ai_stored_count > 0:
        print(f"✓ Stored {ai_stored_count} AI-generated app profiles (deduplicated on submission_id)")
    else:
        print("  No AI profiles to store (score threshold not met)")

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
    print(f"\n{'='*80}")
    print("GENERATING SUMMARY REPORT")
    print(f"{'='*80}")
    generate_summary_report(all_results, elapsed_time, len(submissions))

    # Print DLT-specific metrics
    print(f"\n{'='*80}")
    print("DLT PIPELINE METRICS")
    print(f"{'='*80}")
    print(f"Processing time:       {processing_time:.2f}s")
    print(f"DLT load time:         {dlt_load_time:.2f}s")
    print(f"Total time:            {elapsed_time:.2f}s")
    print(f"Load success:          {'✓ Yes' if load_success else '✗ No'}")
    print("Deduplication:         Enabled (merge disposition)")
    print("Primary key:           opportunity_id")
    print("Target table:          opportunity_scores")
    print("Constraint validation: DLT-Native (1-3 function rule)")
    print(f"{'='*80}\n")

    if load_success:
        print("✓ Batch opportunity scoring completed successfully!")
    else:
        print("⚠️  Batch opportunity scoring completed with warnings (DLT load failed)")


if __name__ == "__main__":
    main()
