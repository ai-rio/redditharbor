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
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

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

from agent_tools.opportunity_analyzer_agent import OpportunityAnalyzerAgent
from agent_tools.llm_profiler import LLMProfiler
from config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client

# DLT imports for pipeline-based loading
from core.dlt_collection import create_dlt_pipeline

# DLT constraint validator
from core.dlt.constraint_validator import app_opportunities_with_constraint

# DLT opportunity pipeline
from scripts.dlt_opportunity_pipeline import load_app_opportunities_with_constraint


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


def fetch_all_submissions(supabase_client: Any, batch_size: int = 1000) -> List[Dict[str, Any]]:
    """
    Fetch all submissions from the Supabase database in batches.

    Args:
        supabase_client: Initialized Supabase client
        batch_size: Number of submissions to fetch per batch (default 1000)

    Returns:
        List of all submission dictionaries

    Raises:
        Exception: If database query fails
    """
    try:
        print("Fetching all submissions from database...")

        all_submissions = []
        offset = 0

        while True:
            # Build query with pagination
            query = supabase_client.table("submissions").select(
                "id, submission_id, title, text, content, subreddit, upvotes, "
                "comments_count, sentiment_score, problem_keywords, solution_mentions, "
                "created_at"
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


def fetch_submissions(supabase_client: Any, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Fetch submissions from the Supabase database.

    Args:
        supabase_client: Initialized Supabase client
        limit: Optional limit on number of submissions to fetch

    Returns:
        List of submission dictionaries with all relevant fields

    Raises:
        Exception: If database query fails
    """
    try:
        if limit:
            # Use simple fetch for limited results
            print("Fetching limited submissions from database...")
            query = supabase_client.table("submissions").select(
                "id, submission_id, title, text, content, subreddit, upvotes, "
                "comments_count, sentiment_score, problem_keywords, solution_mentions, "
                "created_at"
            ).limit(limit)

            response = query.execute()

            if not response.data:
                print("Warning: No submissions found in database")
                return []

            print(f"Successfully fetched {len(response.data)} submissions")
            return response.data
        else:
            # Fetch all submissions in batches
            return fetch_all_submissions(supabase_client)

    except Exception as e:
        print(f"Error fetching submissions: {e}")
        raise


def format_submission_for_agent(submission: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a database submission record for the OpportunityAnalyzerAgent.

    Args:
        submission: Raw submission data from database

    Returns:
        Formatted submission data for agent analysis
    """
    # Combine title and text/content for full text analysis
    title = submission.get("title", "")
    text = submission.get("text", "") or submission.get("content", "")
    full_text = f"{title}\n\n{text}".strip()

    # Format engagement data - use actual column names
    engagement = {
        "upvotes": submission.get("upvotes", 0) or 0,
        "num_comments": submission.get("comments_count", 0) or 0,
    }

    # Extract comments from problem_keywords and solution_mentions if available
    comments = []
    problem_keywords = submission.get("problem_keywords")
    solution_mentions = submission.get("solution_mentions")

    if problem_keywords:
        comments.append(f"Problem identified: {problem_keywords}")
    if solution_mentions:
        comments.append(f"Solution discussed: {solution_mentions}")

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
    analysis: Dict[str, Any],
    sector: str
) -> Dict[str, Any]:
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

    # Extract core functions from analysis
    core_functions = analysis.get("core_functions", [])
    if isinstance(core_functions, list):
        function_count = len(core_functions)
        function_list = core_functions
    else:
        # Fallback for old format
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
    scored_opportunities: List[Dict[str, Any]]
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
            print(f"\n  Disqualified Opportunities:")
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
        print(f"  - Table: workflow_results")
        print(f"  - Write mode: merge (deduplication enabled)")
        print(f"  - Primary key: opportunity_id")
        print(f"  - Constraint validation: DLT-native (1-3 function rule)")
        print(f"  - Started at: {load_info.started_at}")
        print(f"{'='*80}\n")

        return True

    except Exception as e:
        print(f"\n✗ Error loading scores via DLT: {e}")
        print(f"  - Opportunities affected: {len(scored_opportunities)}")
        print(f"  - Recommendation: Check DLT configuration and Supabase connection")
        print(f"{'='*80}\n")
        return False


def store_ai_profiles_to_app_opportunities_via_dlt(
    scored_opportunities: List[Dict[str, Any]]
) -> int:
    """
    Store opportunities with AI profiles to app_opportunities table via DLT.
    Uses DLT merge disposition for automatic deduplication on submission_id.
    Only stores opportunities that have LLM-generated profiles.

    Args:
        scored_opportunities: List of scored opportunities (some with AI profiles)

    Returns:
        Number of AI profiles stored
    """
    from core.dlt_app_opportunities import load_app_opportunities

    # Transform to app_opportunities format
    ai_profiles = []
    for opp in scored_opportunities:
        # Only include if it has AI-generated fields
        if not opp.get("problem_description"):
            continue

        ai_profiles.append({
            "submission_id": opp.get("submission_id", ""),  # Use REAL Reddit ID, not opportunity_id
            "problem_description": opp.get("problem_description", ""),
            "app_concept": opp.get("app_concept", ""),
            "core_functions": opp.get("function_list", []),
            "value_proposition": opp.get("value_proposition", ""),
            "target_user": opp.get("target_user", ""),
            "monetization_model": opp.get("monetization_model", ""),
            "opportunity_score": float(opp.get("final_score", 0)),
            "title": opp.get("app_name", ""),
            "subreddit": opp.get("submission_id", "").split("_")[0] if "_" in opp.get("submission_id", "") else "",
            "reddit_score": int(opp.get("original_score", 0)),
            "status": "discovered"
        })

    if not ai_profiles:
        return 0

    # Load via DLT with automatic deduplication
    success = load_app_opportunities(ai_profiles)
    return len(ai_profiles) if success else 0


def process_batch(
    submissions: List[Dict[str, Any]],
    agent: OpportunityAnalyzerAgent,
    batch_number: int,
    llm_profiler: Optional[LLMProfiler] = None,
    high_score_threshold: float = 40.0
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
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

    for submission in submissions:
        try:
            # Format submission for agent
            formatted = format_submission_for_agent(submission)

            # Analyze opportunity (scoring only, no AI profiling yet)
            analysis = agent.analyze_opportunity(formatted)

            # Check if this is a high-scoring opportunity
            final_score = analysis.get("final_score", 0)
            if llm_profiler and final_score >= high_score_threshold:
                high_score_count += 1
                print(f"  🎯 High score ({final_score:.1f}) - generating AI profile...")

                # Generate real AI app profile
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

            # Map subreddit to sector
            sector = map_subreddit_to_sector(submission.get("subreddit", ""))
            analysis["sector"] = sector

            # Prepare for DLT storage
            submission_id = submission.get("id")
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

    if high_score_count > 0:
        print(f"\n  ✨ Generated {high_score_count} AI profiles for high-scoring opportunities")

    return analysis_results, scored_opportunities


def generate_summary_report(
    all_results: List[Dict[str, Any]],
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

    print(f"\nProcessing Statistics:")
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
        print(f"\nScore Distribution:")
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
        print(f"\nAverage Dimension Scores:")
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

        print(f"\nOpportunities by Sector:")
        for sector, count in sorted(sector_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {sector:25} {count:,} ({count/len(valid_results)*100:.1f}%)")

        # Top opportunities
        print(f"\nTop 10 Opportunities:")
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


def main():
    """
    Main execution function for batch opportunity scoring (DLT-powered).
    """
    print("\n" + "="*80)
    print("BATCH OPPORTUNITY SCORING - DLT-POWERED")
    print("="*80 + "\n")
    print("Features:")
    print("  ✓ DLT Pipeline: Enabled")
    print("  ✓ Incremental Loading: Automatic")
    print("  ✓ Constraint Validation: DLT-Native (1-3 Function Rule)")
    print("  ✓ Deduplication: Merge disposition")
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
            results, scored_opps = process_batch(batch, agent, batch_num, llm_profiler)
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
    print(f"Total opportunities to load: {len(all_scored_opportunities):,}")

    dlt_load_start = time.time()
    load_success = load_scores_to_supabase_via_dlt(all_scored_opportunities)
    dlt_load_time = time.time() - dlt_load_start

    # Also store AI profiles to app_opportunities table via DLT (with deduplication)
    print(f"\n📤 Storing AI-generated profiles to app_opportunities via DLT...")
    ai_stored_count = store_ai_profiles_to_app_opportunities_via_dlt(all_scored_opportunities)
    if ai_stored_count > 0:
        print(f"✓ Stored {ai_stored_count} AI-generated app profiles (deduplicated on submission_id)")
    else:
        print(f"  No AI profiles to store (score threshold not met)")

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
    print(f"Deduplication:         Enabled (merge disposition)")
    print(f"Primary key:           opportunity_id")
    print(f"Target table:          opportunity_scores")
    print(f"Constraint validation: DLT-Native (1-3 function rule)")
    print(f"{'='*80}\n")

    if load_success:
        print("✓ Batch opportunity scoring completed successfully!")
    else:
        print("⚠️  Batch opportunity scoring completed with warnings (DLT load failed)")


if __name__ == "__main__":
    main()
