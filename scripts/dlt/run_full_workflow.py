#!/usr/bin/env python3
"""
Complete RedditHarbor Workflow Orchestrator
============================================

Executes the full pipeline:
1. Collect Reddit data from configured subreddits
2. Store in Supabase using DLT pipeline
3. Analyze and score opportunities using DLT constraints
4. Display console results with detailed analytics

This script runs all phases with progress tracking and comprehensive reporting.
"""

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment
from dotenv import load_dotenv

load_dotenv(project_root / '.env.local')

# Set up logging
log_dir = project_root / "error_log"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'workflow.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
    from tqdm import tqdm
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tqdm", "-q"])
    from tqdm import tqdm

# ============================================================================
# PHASE 1: DATABASE INITIALIZATION
# ============================================================================

def initialize_database():
    """Initialize Supabase connection and verify tables exist."""
    logger.info("=" * 80)
    logger.info("PHASE 1: Database Initialization")
    logger.info("=" * 80)

    from config import SUPABASE_KEY, SUPABASE_URL
    from supabase import create_client

    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Test connection
        result = supabase.table("submission").select("count", count="exact").execute()
        submission_count = result.count if hasattr(result, 'count') else 0

        logger.info("✓ Database connected successfully")
        logger.info(f"  Current submissions: {submission_count}")

        return supabase
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        raise

# ============================================================================
# PHASE 2: COLLECT DATA
# ============================================================================

def collect_reddit_data(supabase):
    """Collect fresh Reddit data using DLT pipeline."""
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 2: Collecting Reddit Data")
    logger.info("=" * 80)

    from core.dlt_collection import (
        PROBLEM_KEYWORDS,
        collect_problem_posts,
        create_dlt_pipeline,
        load_to_supabase,
    )

    # Target subreddits - opportunity-focused
    SUBREDDITS = [
        "personalfinance", "fitness", "loseit", "investing", "SaaS",
        "startups", "Entrepreneur", "learnprogramming", "ProductHunt",
        "apps", "nutrition", "mentalhealth", "travel", "digitalnomad"
    ]

    logger.info(f"Collecting from {len(SUBREDDITS)} subreddits...")
    logger.info(f"Problem keywords: {len(PROBLEM_KEYWORDS)} keywords")

    try:
        # Collect problem posts
        submissions = []
        for subreddit in SUBREDDITS:
            try:
                posts = collect_problem_posts(subreddit, limit=10)
                submissions.extend(posts)
                logger.info(f"  ✓ {subreddit}: {len(posts)} posts")
            except Exception as e:
                logger.warning(f"  ✗ {subreddit}: {str(e)[:50]}")
                continue

        logger.info(f"\nTotal submissions collected: {len(submissions)}")

        if submissions:
            # Load to Supabase via DLT
            logger.info("Loading data to Supabase via DLT...")
            pipeline = create_dlt_pipeline()
            load_to_supabase(supabase, submissions, pipeline)
            logger.info("✓ Data loaded successfully to Supabase")

        return submissions
    except Exception as e:
        logger.error(f"✗ Collection failed: {e}")
        return []

# ============================================================================
# PHASE 3: ANALYZE & SCORE
# ============================================================================

def analyze_and_score(supabase, submissions):
    """Analyze submissions and score them using DLT constraints."""
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 3: Analyzing & Scoring Opportunities")
    logger.info("=" * 80)

    from agent_tools.opportunity_analyzer_agent import OpportunityAnalyzerAgent
    from core.dlt.score_calculator import (
        apply_constraint_to_score,
        calculate_simplicity_score,
        calculate_total_score,
    )

    logger.info(f"Processing {len(submissions)} submissions...")

    # Initialize scoring agent
    agent = OpportunityAnalyzerAgent()

    scored_opportunities = []
    constraint_violations = []

    for sub in tqdm(submissions, desc="Scoring submissions"):
        try:
            # Analyze opportunity
            analysis = agent.analyze(sub)

            if analysis:
                # Extract function count for simplicity scoring
                function_list = analysis.get("function_list", [])
                function_count = len(function_list)

                # Calculate scores
                simplicity = calculate_simplicity_score(function_count)
                total = calculate_total_score(analysis)

                # Apply constraint (4+ functions = disqualified)
                final_score, constraint_applied = apply_constraint_to_score(
                    total, function_count,
                    original_data=analysis
                )

                opportunity = {
                    "opportunity_id": sub.get("id", f"opp_{int(time.time())}"),
                    "app_name": analysis.get("app_name", "Unknown"),
                    "description": analysis.get("description", ""),
                    "function_count": function_count,
                    "function_list": function_list,
                    "simplicity_score": simplicity,
                    "total_score": final_score,
                    "original_score": total,
                    "constraint_applied": constraint_applied,
                    "market_demand": analysis.get("market_demand_score", 0),
                    "pain_intensity": analysis.get("pain_intensity_score", 0),
                    "monetization": analysis.get("monetization_potential_score", 0),
                    "technical_feasibility": analysis.get("technical_feasibility_score", 0),
                    "market_gap": analysis.get("market_gap_score", 0),
                    "created_at": datetime.now().isoformat()
                }

                scored_opportunities.append(opportunity)

                if constraint_applied:
                    constraint_violations.append({
                        "opportunity_id": opportunity["opportunity_id"],
                        "app_name": opportunity["app_name"],
                        "reason": f"Function count: {function_count} (max: 3)",
                        "original_score": total,
                        "final_score": final_score
                    })

        except Exception as e:
            logger.warning(f"  Error scoring {sub.get('id', 'unknown')}: {str(e)[:50]}")
            continue

    logger.info(f"✓ Scored {len(scored_opportunities)} opportunities")
    if constraint_violations:
        logger.info(f"⚠ Found {len(constraint_violations)} constraint violations")

    return scored_opportunities, constraint_violations

# ============================================================================
# PHASE 4: DISPLAY RESULTS
# ============================================================================

def display_results(opportunities: list[dict[str, Any]], violations: list[dict[str, Any]]):
    """Display comprehensive analysis results in console."""
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 4: Analysis Results")
    logger.info("=" * 80)

    if not opportunities:
        logger.warning("No opportunities found to display")
        return

    # ========== SUMMARY STATISTICS ==========
    logger.info("\n📊 SUMMARY STATISTICS")
    logger.info("-" * 80)

    total = len(opportunities)
    approved = sum(1 for o in opportunities if o.get("constraint_applied") == False)
    disqualified = len(violations)
    compliance_rate = (approved / total * 100) if total > 0 else 0

    logger.info(f"Total Opportunities: {total}")
    logger.info(f"Approved: {approved} ({approved/total*100:.1f}%)")
    logger.info(f"Disqualified: {disqualified} ({disqualified/total*100:.1f}%)")
    logger.info(f"Compliance Rate: {compliance_rate:.1f}%")

    # ========== SCORING BREAKDOWN ==========
    logger.info("\n📈 SCORING BREAKDOWN")
    logger.info("-" * 80)

    score_ranges = {
        "100 (1 function)": 0,
        "85 (2 functions)": 0,
        "70 (3 functions)": 0,
        "0 (4+ functions)": 0
    }

    for opp in opportunities:
        score = opp.get("total_score", 0)
        if score == 100:
            score_ranges["100 (1 function)"] += 1
        elif score == 85:
            score_ranges["85 (2 functions)"] += 1
        elif score == 70:
            score_ranges["70 (3 functions)"] += 1
        elif score == 0:
            score_ranges["0 (4+ functions)"] += 1

    for range_name, count in score_ranges.items():
        pct = (count / total * 100) if total > 0 else 0
        logger.info(f"  {range_name}: {count} ({pct:.1f}%)")

    # ========== TOP OPPORTUNITIES ==========
    logger.info("\n🏆 TOP OPPORTUNITIES (by score)")
    logger.info("-" * 80)

    sorted_opps = sorted(opportunities, key=lambda x: x.get("total_score", 0), reverse=True)

    for i, opp in enumerate(sorted_opps[:10], 1):
        logger.info(f"\n{i}. {opp.get('app_name', 'Unknown')}")
        logger.info(f"   Score: {opp.get('total_score', 0):.1f}")
        logger.info(f"   Functions: {opp.get('function_count', 0)}")
        logger.info(f"   Description: {opp.get('description', 'N/A')[:60]}")
        logger.info(f"   Market Demand: {opp.get('market_demand', 0)}")
        logger.info(f"   Pain Intensity: {opp.get('pain_intensity', 0)}")
        logger.info(f"   Monetization: {opp.get('monetization', 0)}")

    # ========== CONSTRAINT VIOLATIONS ==========
    if violations:
        logger.info("\n⚠️  CONSTRAINT VIOLATIONS (4+ functions)")
        logger.info("-" * 80)

        for i, v in enumerate(violations[:5], 1):
            logger.info(f"\n{i}. {v.get('app_name', 'Unknown')}")
            logger.info(f"   Original Score: {v.get('original_score', 0):.1f}")
            logger.info(f"   Final Score: {v.get('final_score', 0):.1f}")
            logger.info(f"   Reason: {v.get('reason', 'N/A')}")

    # ========== DIMENSION ANALYSIS ==========
    logger.info("\n📐 DIMENSION ANALYSIS (Average Scores)")
    logger.info("-" * 80)

    avg_market = sum(o.get("market_demand", 0) for o in opportunities) / len(opportunities) if opportunities else 0
    avg_pain = sum(o.get("pain_intensity", 0) for o in opportunities) / len(opportunities) if opportunities else 0
    avg_monetization = sum(o.get("monetization", 0) for o in opportunities) / len(opportunities) if opportunities else 0
    avg_technical = sum(o.get("technical_feasibility", 0) for o in opportunities) / len(opportunities) if opportunities else 0
    avg_gap = sum(o.get("market_gap", 0) for o in opportunities) / len(opportunities) if opportunities else 0

    logger.info(f"Market Demand: {avg_market:.1f}")
    logger.info(f"Pain Intensity: {avg_pain:.1f}")
    logger.info(f"Monetization Potential: {avg_monetization:.1f}")
    logger.info(f"Technical Feasibility: {avg_technical:.1f}")
    logger.info(f"Market Gap: {avg_gap:.1f}")

    # ========== EXPORT RESULTS ==========
    logger.info("\n💾 EXPORTING RESULTS")
    logger.info("-" * 80)

    results_file = project_root / "generated" / "workflow_results.json"
    results_file.parent.mkdir(exist_ok=True)

    export_data = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": total,
            "approved": approved,
            "disqualified": disqualified,
            "compliance_rate": compliance_rate
        },
        "opportunities": opportunities,
        "violations": violations
    }

    with open(results_file, 'w') as f:
        json.dump(export_data, f, indent=2)

    logger.info(f"✓ Results exported to: {results_file}")

# ============================================================================
# MAIN WORKFLOW ORCHESTRATION
# ============================================================================

def main():
    """Execute complete workflow."""
    start_time = time.time()

    logger.info("\n")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 78 + "║")
    logger.info("║" + "RedditHarbor - Complete Workflow Execution".center(78) + "║")
    logger.info("║" + f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(78) + "║")
    logger.info("║" + " " * 78 + "║")
    logger.info("╚" + "=" * 78 + "╝")

    try:
        # Phase 1: Initialize
        supabase = initialize_database()

        # Phase 2: Collect
        submissions = collect_reddit_data(supabase)

        # Phase 3: Analyze & Score
        opportunities, violations = analyze_and_score(supabase, submissions)

        # Phase 4: Display Results
        display_results(opportunities, violations)

        # Final summary
        elapsed = time.time() - start_time
        logger.info("\n" + "=" * 80)
        logger.info("✅ WORKFLOW COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total execution time: {elapsed:.2f} seconds")
        logger.info(f"Results logged to: {log_dir / 'workflow.log'}")
        logger.info(f"Data exported to: {project_root / 'generated' / 'workflow_results.json'}")

    except Exception as e:
        logger.error("\n" + "=" * 80)
        logger.error("❌ WORKFLOW FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
