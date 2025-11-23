#!/usr/bin/env python3
"""
Test 02: Small Batch Validation for RedditHarbor Unified Pipeline

This test processes 5 submissions with varied quality levels to validate:
1. Consistent behavior across the batch
2. Cost-effective model performance
3. Field coverage across different submission types
4. Graceful degradation for low-quality submissions
5. Memory usage monitoring and cost tracking

Performance Optimizations:
- Cost-effective models using meta-llama/llama-3.1-8b-instruct:floor
- Reduced market validation search count (5 instead of 10)
- Sequential processing for better monitoring and error isolation
- Optional MonetizationService for cost control

Success Criteria:
- Process 5 submissions with varied quality levels
- 80%+ batch completion rate
- Average field coverage: 75%+
- Cost: $0.50-$1.00 total
- Time: 15 minutes max
- Memory usage under 1GB

Submission Types:
1. High Quality: Good engagement, sufficient text content
2. Medium Quality: Moderate engagement, decent text
3. Low Quality: Minimal engagement, limited text
4. Edge Case: Long text or processing challenges
5. Edge Case: Minimal data or validation scenarios

Usage:
    python test_02_small_batch.py
    python test_02_small_batch.py --verbose
    python test_02_small_batch.py --monetization
    python test_02_small_batch.py --update-config
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil

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
from config import (
    get_observability_config,
    load_service_config,
    load_submissions_config,
)

# Import database verifier for real-time SQLAlchemy validation
from utils.database_verifier import DatabaseVerifier

if '--verbose' in sys.argv:
    print("DEBUG: Successfully imported test config functions")
# Import main project settings (explicitly import from project root to avoid conflicts)
import importlib.util

from utils import (
    MetricsCollector,
    ObservabilityManager,
    ServiceMetrics,
    SubmissionMetrics,
    calculate_field_coverage,
    generate_console_report,
    save_json_report,
)

spec = importlib.util.spec_from_file_location("main_config", project_root / "config" / "settings.py")
main_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_config)
SUPABASE_URL = main_config.SUPABASE_URL
SUPABASE_KEY = main_config.SUPABASE_KEY

# Import the new timeout-configured client
import sys

sys.path.insert(0, str(project_root))
from core.clients import get_default_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cost-optimized timeout settings
HTTP_TIMEOUT = 15  # Slightly increased for batch processing
AGNO_TIMEOUT = 30  # Increased for batch reliability
MAX_RETRIES = 2
BATCH_MEMORY_LIMIT_MB = 1024  # 1GB memory limit for batch processing

class BatchMemoryMonitor:
    """Monitor memory usage during batch processing."""

    def __init__(self, limit_mb: int = BATCH_MEMORY_LIMIT_MB):
        self.limit_mb = limit_mb
        self.process = psutil.Process()
        self.start_memory = self.get_memory_mb()
        self.peak_memory = self.start_memory
        self.memory_samples = []

    def get_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024

    def sample(self) -> dict[str, float]:
        """Sample current memory usage."""
        current = self.get_memory_mb()
        self.peak_memory = max(self.peak_memory, current)
        self.memory_samples.append(current)
        return {
            "current": current,
            "peak": self.peak_memory,
            "limit": self.limit_mb,
            "usage_percent": (current / self.limit_mb) * 100
        }

    def is_within_limit(self) -> bool:
        """Check if memory usage is within limit."""
        return self.get_memory_mb() <= self.limit_mb

    def get_summary(self) -> dict[str, Any]:
        """Get memory usage summary."""
        return {
            "start_memory_mb": self.start_memory,
            "peak_memory_mb": self.peak_memory,
            "final_memory_mb": self.get_memory_mb(),
            "limit_mb": self.limit_mb,
            "samples_count": len(self.memory_samples),
            "average_memory_mb": sum(self.memory_samples) / len(self.memory_samples) if self.memory_samples else 0,
            "within_limit": self.is_within_limit()
        }

def apply_batch_optimizations(args) -> None:
    """Apply batch-specific optimizations."""

    # Set cost-effective model
    os.environ['OPENROUTER_MODEL'] = 'meta-llama/llama-3.1-8b-instruct:floor'

    # Reduce timeouts for batch processing
    os.environ['LITELLM_TIMEOUT'] = str(HTTP_TIMEOUT)
    os.environ['AGENTOPS_TIMEOUT'] = str(AGNO_TIMEOUT)
    os.environ['LITELLM_NUM_RETRIES'] = str(MAX_RETRIES)

    # Optimize for cost
    os.environ['LITELLM_DROP_PARAMS'] = 'true'
    os.environ['MARKET_VALIDATION_SEARCH_COUNT'] = '5'  # Reduced from 10

    if '--verbose' in sys.argv:
        print("Applied batch optimizations:")
        print("  - Model: meta-llama/llama-3.1-8b-instruct:floor")
        print(f"  - HTTP Timeout: {HTTP_TIMEOUT}s")
        print(f"  - Agno Timeout: {AGNO_TIMEOUT}s")
        print("  - Market Search Count: 5")
        print(f"  - Max Retries: {MAX_RETRIES}")

def update_small_batch_config() -> dict[str, Any]:
    """Update small batch configuration with actual submission IDs from database."""
    logger.info("Querying database for actual submission IDs...")

    try:
        client = get_default_client()

        # Query for varied submission quality levels
        query_results = []

        # High quality: Try to find submissions with good scores and text
        high_quality = client.table("submissions").select(
            "submission_id, title, subreddit, reddit_score, num_comments, content"
        ).eq("submission_id", "e7763e41-d7bf-4bf1-a004-decff9f0f0c5").execute()

        if high_quality.data:
            query_results.append({
                "quality_level": "high",
                "data": high_quality.data[0]
            })

        # Medium quality: Find test submissions with some content
        medium_quality = client.table("submissions").select(
            "submission_id, title, subreddit, reddit_score, num_comments, content"
        ).eq("submission_id", "high_quality").execute()

        if medium_quality.data:
            query_results.append({
                "quality_level": "medium",
                "data": medium_quality.data[0]
            })

        # Low quality: Submissions with minimal or no content
        low_quality_samples = ["real_test_prof_1", "real_test_prof_2", "real_test_prof_3"]

        for i, sample_id in enumerate(low_quality_samples[:3]):  # Take 3 for variety
            low_quality = client.table("submissions").select(
                "submission_id, title, subreddit, reddit_score, num_comments, content"
            ).eq("submission_id", sample_id).execute()

            if low_quality.data:
                query_results.append({
                    "quality_level": "low",
                    "data": low_quality.data[0]
                })

        # Load current config
        config_path = test_utils_path / "config" / "submissions_small_batch.json"
        with open(config_path) as f:
            config = json.load(f)

        # Update submission entries
        updated_submissions = []
        for i, (submission_entry, result) in enumerate(zip(config["submissions"], query_results)):
            data = result["data"]
            text_length = len(data.get("content", ""))

            updated_submission = {
                "submission_id": data["submission_id"],
                "title": data["title"],
                "subreddit": data["subreddit"],
                "reddit_score": data.get("reddit_score", 0),
                "num_comments": data.get("num_comments", 0),
                "text_length": text_length,
                "quality_level": result["quality_level"],
                "description": submission_entry["description"],
                "expected_services": submission_entry["expected_services"],
                "expected_field_coverage": submission_entry["expected_field_coverage"]
            }

            # Add special considerations for edge cases
            if "special_considerations" in submission_entry:
                updated_submission["special_considerations"] = submission_entry["special_considerations"]

            updated_submissions.append(updated_submission)

        # Update config
        config["submissions"] = updated_submissions
        config["last_updated"] = datetime.now().isoformat()
        config["database_query_timestamp"] = datetime.now().isoformat()

        # Save updated config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        logger.info(f"Updated config with {len(updated_submissions)} real submissions")
        return config

    except Exception as e:
        logger.error(f"Failed to update config with real submissions: {e}")
        # Return original config
        return load_submissions_config("submissions_small_batch.json")

def create_batch_pipeline_config(submission_ids: list[str], args, supabase_client) -> Any:
    """Create pipeline configuration for batch processing."""
    from core.pipeline import DataSource, OpportunityPipeline, PipelineConfig

    # Create pipeline config with cost-effective settings
    config = PipelineConfig(
        data_source=DataSource.DATABASE,
        limit=len(submission_ids),

        # Core services - always enabled
        enable_profiler=True,
        enable_opportunity_scoring=True,
        enable_trust=True,

        # Optional services based on arguments
        enable_monetization=args.monetization,
        enable_market_validation=True,

        # Thresholds - set low to ensure processing
        ai_profile_threshold=0.0,
        monetization_threshold=0.0 if args.monetization else 1.0,  # Disable if not requested
        market_validation_threshold=0.0,

        # Return data for analysis
        return_data=True,
        dry_run=False,

        # Supabase client
        supabase_client=supabase_client,

        # Source config - filter to specific submissions
        source_config={
            "table_name": "submissions",
            "filter_column": "submission_id",
            "filter_value": submission_ids,  # List of submission IDs
        },

        # Batch-specific optimizations
        enable_deduplication=False,  # Disable for testing
        monetization_strategy="agno" if args.monetization else "none",
        monetization_config={
            "timeout": AGNO_TIMEOUT,
            "max_retries": MAX_RETRIES,
        } if args.monetization else None,

        # Sequential processing for better monitoring
        parallel_processing=False,
    )

    return OpportunityPipeline(config)

def process_single_submission(pipeline, submission_config: dict[str, Any], memory_monitor: BatchMemoryMonitor, observability: ObservabilityManager, service_config: dict[str, Any], database_verifier: DatabaseVerifier) -> tuple[dict[str, Any], SubmissionMetrics]:
    """Process a single submission and return results with metrics."""
    submission_id = submission_config["submission_id"]
    quality_level = submission_config["quality_level"]

    logger.info(f"Processing submission: {submission_id} ({quality_level})")
    print(f"\n{'-' * 60}")
    print(f"Processing: {submission_id}")
    print(f"Quality Level: {quality_level}")
    print(f"Title: {submission_config['title']}")
    print(f"Text Length: {submission_config['text_length']}")
    print(f"{'-' * 60}")

    start_time = time.time()
    memory_sample_start = memory_monitor.sample()

    # Create individual pipeline for this submission
    individual_pipeline = create_batch_pipeline_config([submission_id], argparse.Namespace(monetization=False),
                                                     get_default_client())

    try:
        # Run the pipeline
        result = individual_pipeline.run()
        processing_time = time.time() - start_time

        if result.get("success", False):
            enriched_submissions = result.get("opportunities", result.get("data", []))
            if enriched_submissions:
                enriched_submission = enriched_submissions[0]

                # Calculate field coverage
                field_coverage, populated_fields = calculate_field_coverage(enriched_submission)

                # Get service execution stats
                service_metrics_list = []
                total_cost = 0.0

                for service_name in ["profiler", "opportunity", "monetization", "trust", "market_validation"]:
                    service_executed = service_name in individual_pipeline.services

                    if service_executed:
                        service = individual_pipeline.services[service_name]
                        service_stat = getattr(service, "stats", {})
                        success = service_stat.get("analyzed", 0) > 0
                        errors = service_stat.get("errors", 0)

                        # Estimate cost
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
                                latency=processing_time,
                                tokens=0,
                                success=success,
                                error=None if success else f"{errors} errors"
                            )

                        service_metric = ServiceMetrics(
                            service_name=service_name,
                            success=success,
                            processing_time=processing_time,
                            cost=service_cost,
                            error=None if success else f"{errors} errors"
                        )
                        service_metrics_list.append(service_metric)

                # Determine submission status
                expected_coverage = submission_config.get("expected_field_coverage", "70%")
                if expected_coverage.endswith('%'):
                    expected_coverage_value = float(expected_coverage[:-1])
                    coverage_met = field_coverage >= expected_coverage_value
                else:
                    coverage_met = field_coverage >= 75  # Default

                # Verify database storage using SQLAlchemy
                print(f"  🔍 Verifying database storage...")
                verification_result = database_verifier.verify_submission_storage(submission_id, result)

                # Update status based on verification results
                storage_success = verification_result.success
                verification_field_coverage = verification_result.field_coverage

                print(f"  ✓ Storage Verification: {verification_result.message}")
                if verification_result.missing_fields:
                    print(f"  ⚠️  Missing fields: {len(verification_result.missing_fields)}")

                status = "success" if (
                    coverage_met and
                    all(sm.success for sm in service_metrics_list) and
                    storage_success
                ) else "partial"

                submission_metrics = SubmissionMetrics(
                    submission_id=submission_id,
                    status=status,
                    total_time=processing_time,
                    total_cost=total_cost,
                    services_executed=len(service_metrics_list),
                    services_succeeded=sum(1 for sm in service_metrics_list if sm.success),
                    services_failed=sum(1 for sm in service_metrics_list if not sm.success),
                    fields_populated=populated_fields,
                    field_coverage=field_coverage,
                    service_metrics=service_metrics_list,
                )

                result_data = {
                    "success": True,
                    "submission_id": submission_id,
                    "quality_level": quality_level,
                    "processing_time": processing_time,
                    "field_coverage": field_coverage,
                    "populated_fields": len(populated_fields),
                    "total_cost": total_cost,
                    "services_executed": len(service_metrics_list),
                    "services_succeeded": sum(1 for sm in service_metrics_list if sm.success),
                    "memory_usage": memory_monitor.sample(),
                    "enriched_submission": enriched_submission,
                    # Database verification results
                    "storage_verification": {
                        "success": storage_success,
                        "field_coverage": verification_field_coverage,
                        "message": verification_result.message,
                        "table_status": verification_result.table_status,
                        "missing_fields": verification_result.missing_fields
                    }
                }

                print(f"✓ SUCCESS: {submission_id}")
                print(f"  - Processing Time: {processing_time:.2f}s")
                print(f"  - Field Coverage: {field_coverage:.1f}% ({len(populated_fields)} fields)")
                print(f"  - Cost: ${total_cost:.4f}")
                print(f"  - Services: {sum(1 for sm in service_metrics_list if sm.success)}/{len(service_metrics_list)}")
                print(f"  - Memory: {memory_sample_start['current']:.1f}MB")

                return result_data, submission_metrics
            else:
                raise Exception("No enriched submissions returned")
        else:
            raise Exception(f"Pipeline reported failure: {result.get('error', 'Unknown error')}")

    except Exception as e:
        processing_time = time.time() - start_time
        error_message = str(e)

        print(f"✗ FAILED: {submission_id}")
        print(f"  - Error: {error_message}")
        print(f"  - Processing Time: {processing_time:.2f}s")
        print(f"  - Memory: {memory_sample_start['current']:.1f}MB")

        result_data = {
            "success": False,
            "submission_id": submission_id,
            "quality_level": quality_level,
            "processing_time": processing_time,
            "field_coverage": 0.0,
            "populated_fields": 0,
            "total_cost": 0.0,
            "services_executed": 0,
            "services_succeeded": 0,
            "error": error_message,
            "memory_usage": memory_monitor.sample()
        }

        submission_metrics = SubmissionMetrics(
            submission_id=submission_id,
            status="failed",
            total_time=processing_time,
            total_cost=0.0,
            services_executed=0,
            services_succeeded=0,
            services_failed=0,
            fields_populated=[],
            field_coverage=0.0,
            service_metrics=[],
        )

        return result_data, submission_metrics

def run_small_batch_test(args) -> dict:
    """
    Run Test 02 small batch validation.

    Args:
        args: Command line arguments

    Returns:
        Test results dictionary
    """
    print("\n" + "=" * 80)
    print("TEST 02: SMALL BATCH VALIDATION")
    print("=" * 80)
    print("\nBatch Configuration:")
    print("  ✓ Cost-effective models: meta-llama/llama-3.1-8b-instruct:floor")
    print("  ✓ Reduced market validation search: 5 results")
    print("  ✓ Sequential processing for monitoring")
    print("  ✓ Memory usage tracking")
    print(f"  ✓ Monetization Service: {'ENABLED' if args.monetization else 'DISABLED'}")
    print("\nGoal: Validate consistent behavior across varied submission quality")
    print("\nProcessing:")
    print("  - 5 submissions with varied quality levels")
    print("  - High, Medium, Low, and Edge case submissions")
    print("  - Field coverage and cost tracking")
    print("  - Memory usage monitoring")
    print("")

    # Apply batch optimizations
    apply_batch_optimizations(args)

    # Initialize memory monitor
    memory_monitor = BatchMemoryMonitor()

    # Initialize metrics collector
    metrics_collector = MetricsCollector("test_02_small_batch")

    # Initialize database verifier for real-time validation
    database_verifier = DatabaseVerifier()
    print("✓ Database verifier initialized for real-time validation")

    # Load configurations
    service_config = load_service_config()
    observability_config = get_observability_config()

    # Initialize observability
    observability = ObservabilityManager("test_02_small_batch", observability_config)
    observability.initialize_agentops()
    observability.initialize_litellm()

    # Update configuration with real submissions if requested
    if args.update_config:
        print("Updating small batch configuration with real submissions...")
        try:
            batch_config = update_small_batch_config()
            print("✓ Configuration updated successfully")
        except Exception as e:
            print(f"⚠️  Failed to update config: {e}, using existing config")
            batch_config = load_submissions_config("submissions_small_batch.json")
    else:
        batch_config = load_submissions_config("submissions_small_batch.json")

    # Get submission configurations
    submission_configs = batch_config.get("submissions", [])

    if not submission_configs:
        print("✗ No submissions found in configuration")
        return {"success": False, "error": "No submissions found in configuration"}

    print(f"✓ Loaded {len(submission_configs)} submissions for processing")
    for i, sub_config in enumerate(submission_configs, 1):
        print(f"  {i}. {sub_config['submission_id']} ({sub_config['quality_level']}) - {sub_config['title']}")
    print("")

    # Process submissions sequentially
    batch_start_time = time.time()
    batch_results = []

    print("Starting batch processing...")
    print("-" * 80)

    for i, submission_config in enumerate(submission_configs, 1):
        print(f"\n[{i}/{len(submission_configs)}] Processing submission...")

        # Check memory before processing
        if not memory_monitor.is_within_limit():
            print(f"⚠️  WARNING: Memory limit exceeded ({memory_monitor.get_memory_mb():.1f}MB > {memory_monitor.limit_mb}MB)")
            if not args.continue_on_memory_warning:
                print("Stopping batch processing due to memory limit")
                break

        try:
            result_data, submission_metrics = process_single_submission(
                None,  # We'll create individual pipelines
                submission_config,
                memory_monitor,
                observability,
                service_config,
                database_verifier
            )

            batch_results.append(result_data)
            metrics_collector.record_submission(submission_metrics)

            # Brief pause between submissions for resource cleanup
            time.sleep(1)

        except Exception as e:
            logger.error(f"Failed to process submission {submission_config['submission_id']}: {e}")

            error_result = {
                "success": False,
                "submission_id": submission_config["submission_id"],
                "quality_level": submission_config["quality_level"],
                "processing_time": 0.0,
                "field_coverage": 0.0,
                "populated_fields": 0,
                "total_cost": 0.0,
                "error": str(e),
                "memory_usage": memory_monitor.sample(),
                # Storage verification (not available for failed submissions)
                "storage_verification": {
                    "success": False,
                    "field_coverage": 0.0,
                    "message": f"Pipeline failed: {str(e)}",
                    "table_status": {},
                    "missing_fields": []
                }
            }

            batch_results.append(error_result)

            # Stop processing if fail_fast is enabled
            if batch_config.get("batch_config", {}).get("fail_fast", False):
                print("Stopping batch processing due to fail_fast setting")
                break

    batch_processing_time = time.time() - batch_start_time
    print("-" * 80)
    print(f"\n✓ Batch processing completed in {batch_processing_time:.2f}s")

    # Analyze batch results
    print("\nAnalyzing batch results...")

    successful_submissions = [r for r in batch_results if r["success"]]
    failed_submissions = [r for r in batch_results if not r["success"]]

    success_rate = (len(successful_submissions) / len(batch_results)) * 100
    total_cost = sum(r["total_cost"] for r in batch_results)
    avg_field_coverage = sum(r["field_coverage"] for r in batch_results) / len(batch_results) if batch_results else 0

    print("\nBatch Summary:")
    print(f"  - Total Submissions: {len(batch_results)}")
    print(f"  - Successful: {len(successful_submissions)} ({success_rate:.1f}%)")
    print(f"  - Failed: {len(failed_submissions)}")
    print(f"  - Success Rate: {success_rate:.1f}%")
    print(f"  - Total Cost: ${total_cost:.4f}")
    print(f"  - Average Field Coverage: {avg_field_coverage:.1f}%")
    print(f"  - Processing Time: {batch_processing_time:.2f}s")

    # Quality level analysis
    print("\nQuality Level Analysis:")
    quality_groups = {}
    for result in batch_results:
        quality = result["quality_level"]
        if quality not in quality_groups:
            quality_groups[quality] = []
        quality_groups[quality].append(result)

    for quality, results in quality_groups.items():
        successful = [r for r in results if r["success"]]
        avg_coverage = sum(r["field_coverage"] for r in results) / len(results) if results else 0
        print(f"  - {quality.capitalize()}: {len(successful)}/{len(results)} successful, {avg_coverage:.1f}% avg coverage")

    # Memory usage summary
    memory_summary = memory_monitor.get_summary()
    print("\nMemory Usage Summary:")
    print(f"  - Start: {memory_summary['start_memory_mb']:.1f}MB")
    print(f"  - Peak: {memory_summary['peak_memory_mb']:.1f}MB")
    print(f"  - Final: {memory_summary['final_memory_mb']:.1f}MB")
    print(f"  - Limit: {memory_summary['limit_mb']}MB")

    # Storage verification summary
    print("\nDatabase Storage Verification Summary:")
    storage_successful = [r for r in batch_results if r.get("storage_verification", {}).get("success", False)]
    storage_failed = [r for r in batch_results if not r.get("storage_verification", {}).get("success", False)]
    storage_success_rate = (len(storage_successful) / len(batch_results)) * 100 if batch_results else 0

    # Calculate average verification field coverage
    verification_coverages = [r.get("storage_verification", {}).get("field_coverage", 0) for r in batch_results]
    avg_verification_coverage = sum(verification_coverages) / len(verification_coverages) if verification_coverages else 0

    # Table-specific success rates
    table_stats = {}
    for result in batch_results:
        table_status = result.get("storage_verification", {}).get("table_status", {})
        for table, success in table_status.items():
            if table not in table_stats:
                table_stats[table] = {"success": 0, "total": 0}
            table_stats[table]["total"] += 1
            if success:
                table_stats[table]["success"] += 1

    print(f"  - Storage Success Rate: {storage_success_rate:.1f}% ({len(storage_successful)}/{len(batch_results)})")
    print(f"  - Average Storage Coverage: {avg_verification_coverage:.1f}%")

    if table_stats:
        print("  - Table-Specific Success Rates:")
        for table, stats in table_stats.items():
            rate = (stats["success"] / stats["total"]) * 100
            print(f"    * {table}: {rate:.1f}% ({stats['success']}/{stats['total']})")

    if storage_failed:
        print("  - Storage Issues Detected:")
        for result in storage_failed:
            submission_id = result["submission_id"]
            message = result.get("storage_verification", {}).get("message", "Unknown error")
            print(f"    * {submission_id}: {message}")

    print(f"\nMemory Status: {'✓ WITHIN LIMIT' if memory_summary['within_limit'] else '✗ EXCEEDED LIMIT'}")

    # Check success criteria
    success_criteria = batch_config.get("success_criteria", {})
    criteria_met = []
    criteria_failed = []

    if success_rate >= success_criteria.get("completion_rate", 100):
        criteria_met.append(f"Completion Rate: {success_rate:.1f}% >= {success_criteria.get('completion_rate', 100)}%")
    else:
        criteria_failed.append(f"Completion Rate: {success_rate:.1f}% < {success_criteria.get('completion_rate', 100)}%")

    if avg_field_coverage >= success_criteria.get("avg_field_coverage", 75):
        criteria_met.append(f"Field Coverage: {avg_field_coverage:.1f}% >= {success_criteria.get('avg_field_coverage', 75)}%")
    else:
        criteria_failed.append(f"Field Coverage: {avg_field_coverage:.1f}% < {success_criteria.get('avg_field_coverage', 75)}%")

    if total_cost <= success_criteria.get("max_cost", 1.00):
        criteria_met.append(f"Cost: ${total_cost:.4f} <= ${success_criteria.get('max_cost', 1.00):.2f}")
    else:
        criteria_failed.append(f"Cost: ${total_cost:.4f} > ${success_criteria.get('max_cost', 1.00):.2f}")

    if batch_processing_time <= (success_criteria.get("max_time_minutes", 15) * 60):
        criteria_met.append(f"Time: {batch_processing_time:.2f}s <= {success_criteria.get('max_time_minutes', 15)}min")
    else:
        criteria_failed.append(f"Time: {batch_processing_time:.2f}s > {success_criteria.get('max_time_minutes', 15)}min")

    if memory_summary['within_limit']:
        criteria_met.append(f"Memory: {memory_summary['peak_memory_mb']:.1f}MB <= {memory_summary['limit_mb']}MB")
    else:
        criteria_failed.append(f"Memory: {memory_summary['peak_memory_mb']:.1f}MB > {memory_summary['limit_mb']}MB")

    print("\nSuccess Criteria:")
    for criteria in criteria_met:
        print(f"  ✓ {criteria}")
    for criteria in criteria_failed:
        print(f"  ✗ {criteria}")

    # Determine overall success
    overall_success = (
        success_rate >= success_criteria.get("completion_rate", 100) and
        avg_field_coverage >= success_criteria.get("avg_field_coverage", 75) and
        total_cost <= success_criteria.get("max_cost", 1.00) and
        batch_processing_time <= (success_criteria.get("max_time_minutes", 15) * 60) and
        memory_summary['within_limit']
    )

    # Generate comprehensive report
    test_metrics = metrics_collector.generate_report()
    test_metrics.batch_summary = {
        "total_submissions": len(batch_results),
        "successful_submissions": len(successful_submissions),
        "failed_submissions": len(failed_submissions),
        "success_rate": success_rate,
        "total_cost": total_cost,
        "avg_field_coverage": avg_field_coverage,
        "batch_processing_time": batch_processing_time,
        "memory_summary": memory_summary,
        "quality_analysis": {
            quality: {
                "count": len(results),
                "successful": len([r for r in results if r["success"]]),
                "avg_coverage": sum(r["field_coverage"] for r in results) / len(results) if results else 0
            }
            for quality, results in quality_groups.items()
        },
        "success_criteria": {
            "met": criteria_met,
            "failed": criteria_failed,
            "overall_success": overall_success
        },
        "batch_results": batch_results
    }

    # Print console report
    print("\n" + generate_console_report(test_metrics))

    # Save JSON report
    results_dir = Path(__file__).parent.parent / "results" / "test_02_small_batch"
    results_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    json_file = results_dir / f"run_{timestamp}.json"

    save_json_report(test_metrics, json_file)
    print(f"\n✓ Results saved to: {json_file}")

    # Finalize observability
    observability.finalize()

    # Clean up database verifier
    try:
        database_verifier.close()
        print("✓ Database verifier connections closed")
    except Exception as e:
        logger.warning(f"Error closing database verifier: {e}")

    return {
        "success": overall_success,
        "metrics": test_metrics.to_dict(),
        "report_path": str(json_file),
        "batch_summary": test_metrics.batch_summary
    }

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test 02: Small Batch Validation")
    parser.add_argument(
        "--monetization",
        action="store_true",
        help="Enable MonetizationService (increases cost)"
    )
    parser.add_argument(
        "--update-config",
        action="store_true",
        help="Update configuration with real submission IDs from database"
    )
    parser.add_argument(
        "--continue-on-memory-warning",
        action="store_true",
        help="Continue processing even if memory limit is exceeded"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run small batch test
    try:
        result = run_small_batch_test(args)

        if result["success"]:
            print("\n" + "=" * 80)
            print("✅ TEST 02 PASSED - All batch criteria achieved")
            print("=" * 80)
            sys.exit(0)
        else:
            print("\n" + "=" * 80)
            print("❌ TEST 02 FAILED - See report for details")
            print("=" * 80)
            sys.exit(1)

    except Exception as e:
        logger.error(f"Test failed with exception: {e}", exc_info=True)
        print("\n" + "=" * 80)
        print(f"❌ TEST 02 FAILED - Unexpected error: {e}")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
