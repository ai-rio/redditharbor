#!/usr/bin/env python3
"""
Test 01: Single Submission Validation

This test validates that the unified OpportunityPipeline can successfully process
a single high-quality submission with ALL AI services enabled and populate all
expected enrichment fields.

Success Criteria:
- All 5 services execute successfully (Profiler, Opportunity, Monetization, Trust, Market Validation)
- All 30+ enrichment fields populated
- Processing time: 15-30 seconds
- Cost: $0.10-$0.20
- No unhandled exceptions
- Data stored in database correctly
- AgentOps session created (if enabled)
- LiteLLM costs tracked (if enabled)

Usage:
    python scripts/testing/integration/tests/test_01_single_submission.py
    python scripts/testing/integration/tests/test_01_single_submission.py --verbose
    python scripts/testing/integration/tests/test_01_single_submission.py --submission-id abc123
"""

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Set up paths - test utils first so they take precedence
test_utils_path = Path(__file__).parent.parent.resolve()
project_root = Path(__file__).parent.parent.parent.parent.parent.resolve()

# Add test utils to path FIRST so it takes precedence for config imports
sys.path.insert(0, str(test_utils_path))
sys.path.insert(1, str(project_root))

# Debug: Print path info
if '--verbose' in sys.argv:
    print(f"DEBUG: __file__ = {__file__}")
    print(f"DEBUG: project_root = {project_root}")
    print(f"DEBUG: test_utils_path = {test_utils_path}")
    print(f"DEBUG: sys.path[0] = {sys.path[0]}")
    print(f"DEBUG: sys.path[1] = {sys.path[1]}")
    print(f"DEBUG: main config exists = {(project_root / 'config').exists()}")
    print(f"DEBUG: test config exists = {(test_utils_path / 'config').exists()}")

from dotenv import load_dotenv
load_dotenv(project_root / ".env.local")

# Import test utilities FIRST (so we get the right config module)
from config import load_service_config, load_submissions_config, get_observability_config
if '--verbose' in sys.argv:
    print(f"DEBUG: Successfully imported test config functions")
from utils import (
    MetricsCollector,
    ServiceMetrics,
    SubmissionMetrics,
    calculate_field_coverage,
    generate_console_report,
    save_json_report,
    ObservabilityManager,
)

# Import pipeline components
from core.pipeline import OpportunityPipeline, PipelineConfig, DataSource

# Import main project settings (explicitly import from project root to avoid conflicts)
import importlib.util
spec = importlib.util.spec_from_file_location("main_config", project_root / "config" / "settings.py")
main_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_config)
SUPABASE_URL = main_config.SUPABASE_URL
SUPABASE_KEY = main_config.SUPABASE_KEY
from supabase import create_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_test_submission_id(args) -> str:
    """
    Get submission ID for testing.

    Args:
        args: Command line arguments

    Returns:
        Submission ID to test
    """
    if args.submission_id:
        return args.submission_id

    # Load from config
    submissions_config = load_submissions_config("submissions_single.json")
    submissions = submissions_config.get("submissions", [])

    if not submissions:
        raise ValueError("No submissions found in submissions_single.json")

    submission_id = submissions[0].get("submission_id")

    if submission_id == "REPLACE_WITH_ACTUAL_ID":
        # Need to query database
        logger.info("Querying database for high-quality submission...")
        client = create_client(SUPABASE_URL, SUPABASE_KEY)

        query_example = submissions_config.get("query_example", "")
        logger.info(f"Using query: {query_example}")

        # Execute query using direct table query instead of RPC
        # Parse the query to extract criteria
        where_conditions = []
        order_by = "reddit_score DESC"
        limit = 1

        # Extract conditions from the SQL query (simple parsing)
        if "reddit_score >= 40" in query_example:
            where_conditions.append("reddit_score.gte=40")
        if "LENGTH(selftext) >= 50" in query_example:
            where_conditions.append("selftext.notis.null")

        # Build the query
        query = client.table("submissions").select("submission_id, title, subreddit, reddit_score, num_comments, content")

        # Apply conditions
        for condition in where_conditions:
            key, value = condition.split(".", 1)
            if key == "reddit_score":
                query = query.gte("reddit_score", int(value.split("=")[1]))
            elif key == "selftext":
                query = query.not_("selftext", "is", None)

        result = query.order("reddit_score", desc=True).limit(1).execute()

        if not result.data or len(result.data) == 0:
            raise ValueError("No high-quality submissions found in database")

        submission_id = result.data[0]["submission_id"]
        logger.info(f"Selected submission: {submission_id}")

    return submission_id


def run_test(args) -> dict:
    """
    Run Test 01: Single Submission Validation.

    Args:
        args: Command line arguments

    Returns:
        Test results dictionary
    """
    print("\n" + "=" * 80)
    print("TEST 01: SINGLE SUBMISSION VALIDATION")
    print("=" * 80)
    print("\nGoal: Validate all AI services execute and populate enrichment fields")
    print("\nServices to test:")
    print("  1. ProfilerService (AI profiling via Claude Haiku)")
    print("  2. OpportunityService (5-dimensional scoring)")
    print("  3. MonetizationService (Agno multi-agent analysis)")
    print("  4. TrustService (6-dimensional trust validation)")
    print("  5. MarketValidationService (Real market data via Jina AI)")
    print("")

    # Initialize metrics collector
    metrics_collector = MetricsCollector("test_01_single_submission")

    # Load configurations
    service_config = load_service_config()
    observability_config = get_observability_config()

    # Initialize observability
    observability = ObservabilityManager("test_01_single_submission", observability_config)
    observability.initialize_agentops()
    observability.initialize_litellm()

    # Get submission ID
    try:
        submission_id = get_test_submission_id(args)
        print(f"Testing with submission: {submission_id}")
    except Exception as e:
        logger.error(f"Failed to get submission ID: {e}")
        print(f"\n✗ Failed to get test submission: {e}")
        print("\nPlease either:")
        print("  1. Update submissions_single.json with a real submission_id")
        print("  2. Use --submission-id <id> argument")
        print("  3. Ensure database has submissions matching criteria")
        return {"success": False, "error": str(e)}

    # Create pipeline configuration with ALL services enabled
    print("\nInitializing unified OpportunityPipeline...")
    print("  - Data Source: DATABASE")
    print("  - Limit: 1 submission")
    print("  - All Services: ENABLED")
    print("")

    try:
        # Create Supabase client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Create pipeline config with ALL services enabled
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=1,

            # Enable ALL services
            enable_profiler=True,
            enable_opportunity_scoring=True,
            enable_monetization=True,
            enable_trust=True,
            enable_market_validation=True,

            # Thresholds (set low to ensure all services run)
            ai_profile_threshold=0.0,
            monetization_threshold=0.0,
            market_validation_threshold=0.0,

            # Return data for analysis
            return_data=True,
            dry_run=False,

            # Supabase client
            supabase_client=supabase_client,

            # Source config - filter to specific submission
            source_config={
                "table_name": "submissions",
                "filter_column": "submission_id",
                "filter_value": submission_id,
            }
        )

        # Create pipeline
        pipeline = OpportunityPipeline(config)

        print("✓ Pipeline initialized successfully")
        print(f"  - Services loaded: {len(pipeline.services)}")
        print("")

    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}", exc_info=True)
        print(f"\n✗ Pipeline initialization failed: {e}")
        return {"success": False, "error": str(e)}

    # Run pipeline with timing
    print("Running pipeline...")
    print("-" * 80)

    start_time = time.time()

    try:
        result = pipeline.run()
        processing_time = time.time() - start_time

        print("-" * 80)
        print(f"\n✓ Pipeline completed in {processing_time:.2f}s")

    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        print(f"\n✗ Pipeline failed after {processing_time:.2f}s: {e}")
        observability.finalize()
        return {"success": False, "error": str(e)}

    # Analyze results
    print("\nAnalyzing results...")

    if not result.get("success", False):
        print(f"✗ Pipeline reported failure: {result.get('error', 'Unknown error')}")
        observability.finalize()
        return {"success": False, "error": result.get("error", "Pipeline reported failure")}

    # Get enriched submissions
    enriched_submissions = result.get("opportunities", result.get("data", []))

    if not enriched_submissions:
        print("✗ No enriched submissions returned")
        observability.finalize()
        return {"success": False, "error": "No enriched submissions returned"}

    enriched_submission = enriched_submissions[0]

    # Calculate field coverage
    field_coverage, populated_fields = calculate_field_coverage(enriched_submission)

    print(f"\n✓ Submission enriched successfully")
    print(f"  - Fields populated: {len(populated_fields)}/30+")
    print(f"  - Field coverage: {field_coverage:.1f}%")
    print("")

    # Track service execution (from pipeline stats)
    service_stats = result.get("stats", {})
    service_metrics_list = []
    total_cost = 0.0

    print("Service Execution Results:")
    print("-" * 80)

    for service_name in ["profiler", "opportunity", "monetization", "trust", "market_validation"]:
        # Check if service executed
        service_executed = service_name in pipeline.services

        if service_executed:
            # Get service stats from pipeline
            service = pipeline.services[service_name]
            service_stat = getattr(service, "stats", {})

            success = service_stat.get("analyzed", 0) > 0
            errors = service_stat.get("errors", 0)

            # Estimate cost based on service config
            service_cfg = service_config.get("services", {}).get(service_name, {})
            cost_cfg = service_cfg.get("cost", {})
            service_cost = cost_cfg.get("avg_per_call", 0.0) if success else 0.0

            total_cost += service_cost

            # Record in observability
            if service_cost > 0:
                observability.record_llm_call(
                    service_name=service_name,
                    model=service_cfg.get("config", {}).get("model", "unknown"),
                    cost=service_cost,
                    latency=0.0,  # TODO: Track actual latency
                    tokens=0,  # TODO: Track actual tokens
                    success=success,
                    error=None if success else f"{errors} errors"
                )

            # Create service metrics
            service_metric = ServiceMetrics(
                service_name=service_name,
                success=success,
                processing_time=0.0,  # TODO: Track per-service time
                cost=service_cost,
                error=None if success else f"{errors} errors"
            )
            service_metrics_list.append(service_metric)

            status = "✓ SUCCESS" if success else "✗ FAILED"
            print(f"{service_name:20s} {status:15s} Cost: ${service_cost:.4f}")
        else:
            print(f"{service_name:20s} ✗ NOT LOADED")

    print("-" * 80)
    print(f"Total Estimated Cost: ${total_cost:.4f}")
    print("")

    # Create submission metrics
    submission_metrics = SubmissionMetrics(
        submission_id=submission_id,
        status="success" if field_coverage >= 90 else "partial",
        total_time=processing_time,
        total_cost=total_cost,
        services_executed=len(service_metrics_list),
        services_succeeded=sum(1 for sm in service_metrics_list if sm.success),
        services_failed=sum(1 for sm in service_metrics_list if not sm.success),
        fields_populated=populated_fields,
        field_coverage=field_coverage,
        service_metrics=service_metrics_list,
    )

    # Record in metrics collector
    metrics_collector.record_submission(submission_metrics)

    # Generate final report
    test_metrics = metrics_collector.generate_report()

    # Print console report
    print(generate_console_report(test_metrics))

    # Save JSON report
    results_dir = Path(__file__).parent.parent / "results" / "test_01_single_submission"
    results_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    json_file = results_dir / f"run_{timestamp}.json"

    save_json_report(test_metrics, json_file)
    print(f"\n✓ Results saved to: {json_file}")

    # Finalize observability
    observability.finalize()

    # Determine overall success
    overall_success = (
        test_metrics.success_rate >= 100
        and test_metrics.avg_field_coverage >= 90
        and test_metrics.avg_cost_per_submission <= 0.20
    )

    return {
        "success": overall_success,
        "metrics": test_metrics.to_dict(),
        "report_path": str(json_file),
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test 01: Single Submission Validation")
    parser.add_argument(
        "--submission-id",
        type=str,
        help="Specific submission ID to test (optional, will query database if not provided)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run test
    try:
        result = run_test(args)

        if result["success"]:
            print("\n" + "=" * 80)
            print("✅ TEST 01 PASSED - Single submission validation successful")
            print("=" * 80)
            sys.exit(0)
        else:
            print("\n" + "=" * 80)
            print(f"❌ TEST 01 FAILED - {result.get('error', 'See report for details')}")
            print("=" * 80)
            sys.exit(1)

    except Exception as e:
        logger.error(f"Test failed with exception: {e}", exc_info=True)
        print("\n" + "=" * 80)
        print(f"❌ TEST 01 FAILED - Unexpected error: {e}")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
